#!/usr/bin/env python3
"""cripminds-calibration-runner — polls lab.cripminds.com for claimable
calibration jobs and executes exactly the workflow version named by each
job. Runs as a persistent systemd service on Trident (see ./README.md);
never requires an interactive Claude session or open shell.

Design invariants (do not relax without updating
../../.claude/reader-lab-v0-design-2026-08-12.md's calibration-orchestrator
section):
  - This script makes NO research-policy decisions of its own. The
    disposition/agreement/reference-strength rules below are a direct
    transcription of ../workflows/analyze-human-round-v1.md — if that
    file's rules ever change, this script's implementation must be
    updated to match, not the other way around.
  - The only model call anywhere in this file (cliproxy_chat, used only
    for the optional per-item `notes` field) never influences
    disposition/agreement_state/reference_strength/machine_comparison —
    those four fields are fully computed before the model is ever
    called, and the model's output cannot overwrite them.
  - This script never publishes a Reader Lab round, never creates or
    revokes a reviewer invitation, and never invents a source/candidate
    pair outside the explicit eligible_candidates the server sent it.
  - Uses only the Python standard library (urllib), matching the
    existing convention in automation/*.py and llm.py on this same host
    — no new dependency for a service this small.
"""

import json
import os
import sys
import time
import hashlib
import urllib.error
import urllib.request

BASE_URL = os.environ.get("CALIBRATION_BASE_URL", "https://lab.cripminds.com")
RUNNER_TOKEN = os.environ.get("CALIBRATION_RUNNER_TOKEN", "")
RUNNER_ID = os.environ.get("CALIBRATION_RUNNER_ID", "trident-1")
CLIPROXY_URL = os.environ.get("CLIPROXY_URL", "http://127.0.0.1:8317/v1")
CLIPROXY_MODEL = os.environ.get("CLIPROXY_MODEL", "openrouter/claude-sonnet-4.6")
POLL_INTERVAL_SECONDS = int(os.environ.get("CALIBRATION_POLL_INTERVAL", "30"))
BANNED_NOTE_WORDS = ("ground truth", "winner", "correct", "consensus")


# ---------------------------------------------------------------------
# canonical JSON — MUST match src/publish.js's sortedStringify exactly:
# recursively sorted object keys, no separators, non-ASCII preserved
# literally (not \uXXXX-escaped). This is what makes the result_hash
# this script computes verifiable by the Worker's own re-computation in
# calibrationJobs.js, across two different languages' default
# JSON serializers, which otherwise do not agree byte-for-byte.
# ---------------------------------------------------------------------

def canonical_json(value):
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(v) for v in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value.keys())
        return "{" + ",".join(
            json.dumps(k, ensure_ascii=False) + ":" + canonical_json(value[k]) for k in keys
        ) + "}"
    return json.dumps(value, ensure_ascii=False)


def result_hash(result):
    return hashlib.sha256(canonical_json(result).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------
# HTTP helpers — stdlib only, matching automation/*.py's own convention
# ---------------------------------------------------------------------

def _request(method, path, body=None, timeout=30):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else b"{}"
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-Calibration-Runner-Token": RUNNER_TOKEN,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return False, json.loads(e.read().decode("utf-8"))
        except Exception:
            return False, {"error": f"http_{e.code}"}
    except Exception as e:
        return False, {"error": str(e)}


def claim_job():
    return _request("POST", "/ops/calibration/jobs/claim", {"runner_id": RUNNER_ID})


def complete_job(job_id, result):
    return _request(
        "POST",
        f"/ops/calibration/jobs/{job_id}/complete",
        {"runner_id": RUNNER_ID, "result": result, "result_hash": result_hash(result)},
    )


def fail_job(job_id, error):
    return _request("POST", f"/ops/calibration/jobs/{job_id}/fail", {"runner_id": RUNNER_ID, "error": str(error)})


# ---------------------------------------------------------------------
# CLIProxyAPI — same route/convention as automation/cj2_b2_probe*.py on
# this same host (127.0.0.1:8317, OpenAI-compatible /chat/completions).
# Never raises for a normal failure — callers check `ok`.
# ---------------------------------------------------------------------

def cliproxy_chat(system, user, temperature=0.0, max_tokens=200, timeout=30):
    payload = {
        "model": CLIPROXY_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        f"{CLIPROXY_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return True, text
    except Exception as e:
        return False, f"cliproxy request failed: {e}"


# ---------------------------------------------------------------------
# analyze_human_round — deterministic core, matching
# ../workflows/analyze-human-round-v1.md section-for-section.
# ---------------------------------------------------------------------

NOTES_SYSTEM_PROMPT = (
    "You are describing what two independent readers noticed about a short "
    "passage and a sentence written from it — never judging who was right."
)

def _notes_prompt(source_snapshot, candidate_sentence, judgments):
    lines = []
    for j in judgments:
        conf = j.get("confidence") or "not stated"
        comment = j.get("comment") or "none"
        lines.append(f"{j['reviewer_id']}: chose '{j['selected_public_response']}' (confidence: {conf}). Comment: {comment}.")
    judgment_block = "\n".join(lines)
    return (
        f"SOURCE:\n{source_snapshot}\n\n"
        f"THE SENTENCE:\n{candidate_sentence}\n\n"
        f"READER JUDGMENTS:\n{judgment_block}\n\n"
        "In one or two plain sentences, describe what these judgments show about "
        "how the sentence was read. Do not say which reader was correct. Do not "
        "use the words \"ground truth,\" \"winner,\" \"correct,\" or \"consensus.\" "
        "If the judgments simply agree, say what they agree the sentence does. "
        "If they differ, say what specifically they differ about."
    )


def generate_notes(source_snapshot, candidate_sentence, judgments):
    ok, text = cliproxy_chat(NOTES_SYSTEM_PROMPT, _notes_prompt(source_snapshot, candidate_sentence, judgments))
    if not ok or not text or not text.strip():
        return None
    lowered = text.lower()
    if any(bad in lowered for bad in BANNED_NOTE_WORDS):
        return None
    return text.strip()


def _confidence_summary(judgments):
    stated = [j["confidence"] for j in judgments if j.get("confidence")]
    if not stated:
        return "none stated"
    counts = {}
    for c in stated:
        counts[c] = counts.get(c, 0) + 1
    return ", ".join(f"{n} {c}" for c, n in counts.items())


def analyze_item(item, research_context_item):
    judgments = item.get("judgments", [])
    n = len(judgments)
    distinct = {j["internal_normalized_response"] for j in judgments}

    if n == 0:
        agreement_state = "insufficient"
        reference_strength = "none"
        disposition = "insufficient_evidence"
    elif n == 1:
        agreement_state = "single_judgment"
        reference_strength = "single_provisional"
        flagged_needs_more = bool(research_context_item and research_context_item.get("needs_more_reviewers"))
        disposition = "needs_more_reviewers" if flagged_needs_more else "provisional_reference"
    elif len(distinct) == 1:
        agreement_state = "agreement"
        reference_strength = "strong_provisional"
        disposition = "strong_reference"
    else:
        agreement_state = "disagreement"
        reference_strength = "none"
        disposition = "contested"

    machine_label = (research_context_item or {}).get("machine_reference_label")
    if disposition != "strong_reference":
        machine_comparison = "not_applicable"
    elif machine_label is None:
        machine_comparison = "no_machine_reference"
    else:
        # Role comparison: source_established/unsupported_factual_dependency
        # both depend on a real-world fact (a "factual dependency" in B2's
        # own vocabulary); interpretive_only does not. An agreed
        # "uncertain" (both reviewers unsure) falls to human_role
        # "uncertain" below — itself a real, meaningful signal (the item
        # is genuinely ambiguous), just not one with a role to compare
        # against a machine label.
        if distinct <= {"source_established", "unsupported_factual_dependency"}:
            human_role = "factual_dependency"
        elif distinct == {"interpretive_only"}:
            human_role = "interpretive_only"
        else:
            human_role = "uncertain"
        if human_role == "uncertain" or machine_label == "boundary_ambiguous":
            machine_comparison = "no_machine_reference"
        elif human_role == machine_label:
            machine_comparison = "aligns"
        else:
            machine_comparison = "diverges"

    notes = None
    if judgments:
        notes = generate_notes(item["source_snapshot"], item["candidate_sentence"], judgments)

    return {
        "item_id": item["item_id"],
        "slot": item.get("slot"),
        "reviewer_judgments": [
            {
                "reviewer_id": j["reviewer_id"],
                "internal_normalized_response": j["internal_normalized_response"],
                "confidence": j.get("confidence"),
                "has_comment": bool(j.get("comment")),
            }
            for j in sorted(judgments, key=lambda j: j["reviewer_id"])
        ],
        "agreement_state": agreement_state,
        "confidence_summary": _confidence_summary(judgments),
        "comments_present": any(j.get("comment") for j in judgments),
        "reference_strength": reference_strength,
        "machine_comparison": machine_comparison,
        "disposition": disposition,
        "notes": notes,
    }


def run_analyze_human_round(job_input):
    export = job_input["research_export"]
    context = job_input.get("research_context") or {}
    per_item_context = (context or {}).get("per_item", {})

    items = [analyze_item(item, per_item_context.get(item["item_id"])) for item in export.get("items", [])]

    summary = {"strong_reference": 0, "provisional_reference": 0, "contested": 0, "needs_more_reviewers": 0, "insufficient_evidence": 0}
    for it in items:
        summary[it["disposition"]] = summary.get(it["disposition"], 0) + 1

    return {
        "analysis_version": "analyze-human-round-v1",
        "round_id": job_input["round_id"],
        "generated_at": export.get("generated_at"),
        "items": items,
        "round_summary": summary,
    }


# ---------------------------------------------------------------------
# prepare_next_round — deterministic in v1 (no model call): with an
# empty eligible pool there is nothing yet for a model to meaningfully
# rank. See ../workflows/prepare-next-round-v1.md.
# ---------------------------------------------------------------------

def run_prepare_next_round(job_input):
    round_id = job_input["round_id"]
    candidates = job_input.get("eligible_candidates") or []

    # Fail closed: held_out_evaluation material must never enter human
    # calibration, regardless of what the caller claims eligible_for_reader_lab
    # already filtered — this is a second, independent check.
    tainted = [c for c in candidates if c.get("dataset_purpose") == "held_out_evaluation"]
    if tainted:
        raise ValueError(f"held_out_evaluation material present in eligible_candidates: {[c['candidate_id'] for c in tainted]}")

    if not candidates:
        return {"status": "NEEDS_ELIGIBLE_CANDIDATES", "round_id": round_id, "reason": "eligible_candidates was empty"}

    analysis = job_input.get("analysis") or {}
    flagged_items = {
        it["item_id"] for it in analysis.get("items", []) if it.get("disposition") in ("contested", "needs_more_reviewers")
    }

    def priority(c):
        rationale = (c.get("internal_rationale") or "")
        return 0 if any(item_id in rationale for item_id in flagged_items) else 1

    ordered = sorted(candidates, key=lambda c: (priority(c), c.get("created_at") or ""))
    selected = ordered[:5]

    purposes = {c.get("dataset_purpose") for c in selected}
    dataset_purpose = purposes.pop() if len(purposes) == 1 else "development"

    reviewer_ids = job_input.get("active_reviewer_ids") or []

    items = []
    rationale_parts = []
    for i, c in enumerate(selected):
        items.append(
            {
                "slot": i + 1,
                "source_snapshot": c["source_snapshot"],
                "candidate_sentence": c["candidate_sentence"],
                "internal_note": c.get("internal_rationale"),
                "provenance": c.get("provenance"),
            }
        )
        rationale_parts.append(f"slot {i + 1}: candidate {c['candidate_id']}" + (" (targets a flagged item)" if priority(c) == 0 else ""))

    return {
        "status": "DRAFT_READY",
        "round_id": round_id,
        "draft": {
            "dataset_purpose": dataset_purpose,
            "reviewer_ids": reviewer_ids,
            "items": items,
            "selection_rationale": "; ".join(rationale_parts),
        },
    }


# ---------------------------------------------------------------------
# main loop
# ---------------------------------------------------------------------

JOB_HANDLERS = {
    "analyze_human_round": run_analyze_human_round,
    "prepare_next_round": run_prepare_next_round,
}


def process_one(job):
    job_id = job["job_id"]
    job_type = job["job_type"]
    handler = JOB_HANDLERS.get(job_type)
    if not handler:
        fail_job(job_id, f"unknown_job_type: {job_type}")
        return
    try:
        result = handler(job["input"])
    except Exception as e:
        fail_job(job_id, f"{job_type} raised: {e}")
        return
    ok, body = complete_job(job_id, result)
    if not ok:
        print(f"[{job_id}] complete_job failed: {body}", file=sys.stderr)


def main():
    if not RUNNER_TOKEN:
        print("CALIBRATION_RUNNER_TOKEN not set — refusing to start", file=sys.stderr)
        sys.exit(1)
    print(f"cripminds-calibration-runner starting: base={BASE_URL} runner_id={RUNNER_ID} poll={POLL_INTERVAL_SECONDS}s")
    while True:
        ok, body = claim_job()
        if ok and not body.get("no_job"):
            print(f"claimed job {body['job_id']} ({body['job_type']})")
            process_one(body)
            continue  # check for another job immediately after finishing one
        if not ok:
            print(f"claim failed: {body}", file=sys.stderr)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
