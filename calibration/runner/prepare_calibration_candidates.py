#!/usr/bin/env python3
"""prepare-calibration-candidates-v1 — packages an already-frozen B2/CJ-2
research artifact into a candidate ingestion bundle and pushes it to
`POST /ops/calibration/candidates`. See
../workflows/prepare-calibration-candidates-v1.md for the full contract.

Design invariants (do not relax without updating that doc):
  - Never invents a candidate, a hash, a provenance string, or a
    dataset_purpose/eligible_for_reader_lab value. Every field this
    script ingests must already be explicit in the source file — a
    missing or ambiguous field excludes that record with a
    NEEDS_HUMAN_ACTION reason, never a guess.
  - held_out_evaluation material is rejected outright, on top of the
    two independent checks already downstream of this script
    (calibrationWorkflow.js, calibration_runner.py's
    run_prepare_next_round) and the third, server-side one
    (candidateIngestion.js) — this script's own check is belt-and-
    suspenders, never the only line of defense.
  - This script does not decide anything the Worker doesn't
    independently re-validate. Its own checks exist to fail fast with a
    clear local error message, not as the actual security boundary.
  - Uses only the Python standard library (urllib), matching
    calibration_runner.py's own convention.

Usage:
    CALIBRATION_RUNNER_TOKEN=... python3 prepare_calibration_candidates.py \\
        --input ../candidates/RL-2026-002-candidates.json \\
        --source-experiment-id cj2-fresh-batch-1 \\
        --source-experiment-id cj2-reference-probe-1 \\
        --rationale "RL-2026-002 support-boundary calibration round"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("CALIBRATION_BASE_URL", "https://lab.cripminds.com")
RUNNER_TOKEN = os.environ.get("CALIBRATION_RUNNER_TOKEN", "")
RUNNER_ID = os.environ.get("CALIBRATION_RUNNER_ID", "trident-1")

WORKFLOW_NAME = "prepare-calibration-candidates"
WORKFLOW_VERSION = "v1"

REQUIRED_RECORD_FIELDS = ("source_snapshot", "candidate_sentence", "provenance", "dataset_purpose")
ALLOWED_DATASET_PURPOSES = ("pilot", "development", "blind_calibration", "contested")
MACHINE_FIELDS = (
    "machine_role", "machine_support", "machine_problems", "machine_conflict_state",
    "machine_why", "researcher_side_family_criteria_met", "family_internal_only",
    "family_internal_only_note", "internal_ref",
)


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
            # See calibration_runner.py's own comment: Cloudflare's edge
            # blocks urllib's default User-Agent with a bare 403 before
            # this ever reaches the Worker. Baked in from the start here
            # rather than rediscovering that bug a second time.
            "User-Agent": "cripminds-calibration-runner/1.0",
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


def select_and_validate(records):
    """Deterministic only — no model call, no ranking, no invention.
    Every record must already explicitly state everything required; a
    record that doesn't is excluded with a NEEDS_HUMAN_ACTION reason,
    never guessed into shape."""
    candidates = []
    excluded = []

    for i, raw in enumerate(records):
        label = raw.get("provenance") or raw.get("internal_ref") or f"record[{i}]"
        missing = [f for f in REQUIRED_RECORD_FIELDS if not isinstance(raw.get(f), str) or not raw.get(f).strip()]
        if missing:
            excluded.append({"provenance": label, "reason": f"NEEDS_HUMAN_ACTION: missing {', '.join(missing)}"})
            continue

        if raw["dataset_purpose"] == "held_out_evaluation":
            excluded.append({"provenance": label, "reason": "held_out_evaluation material may never enter calibration_candidates"})
            continue
        if raw["dataset_purpose"] not in ALLOWED_DATASET_PURPOSES:
            excluded.append({"provenance": label, "reason": f"NEEDS_HUMAN_ACTION: unrecognized dataset_purpose '{raw['dataset_purpose']}'"})
            continue

        # Must be exactly True -- matches candidateIngestion.js's own
        # server-side rule exactly, so a local dry-run's exclusions
        # accurately predict what the server will accept. A record the
        # source artifact itself marks not-yet-eligible (or leaves
        # unaddressed) is never something this script decides to
        # override or smuggle through as inert.
        if raw.get("eligible_for_reader_lab") is not True:
            reason = (
                "eligible_for_reader_lab is false -- this pipeline only ingests already-decided-eligible material"
                if raw.get("eligible_for_reader_lab") is False
                else "NEEDS_HUMAN_ACTION: eligible_for_reader_lab must be explicitly true, never omitted or ambiguous"
            )
            excluded.append({"provenance": label, "reason": reason})
            continue

        machine_reference = {k: raw[k] for k in MACHINE_FIELDS if k in raw}

        candidates.append({
            "source_snapshot": raw["source_snapshot"],
            "candidate_sentence": raw["candidate_sentence"],
            "source_snapshot_id": raw.get("source_snapshot_id"),
            "candidate_claim_id": raw.get("candidate_claim_id"),
            "provenance": raw["provenance"],
            "dataset_purpose": raw["dataset_purpose"],
            "eligible_for_reader_lab": raw["eligible_for_reader_lab"],
            "internal_rationale": raw.get("machine_why") or raw.get("internal_ref"),
            "machine_reference_json": machine_reference or None,
        })

    return candidates, excluded


def build_bundle(records, source_experiment_ids, rationale):
    candidates, excluded = select_and_validate(records)
    return {
        "workflow_name": WORKFLOW_NAME,
        "workflow_version": WORKFLOW_VERSION,
        "source_experiment_ids": source_experiment_ids,
        "selection_rationale": rationale,
        "candidates": candidates,
        "excluded": excluded,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="path to a *-candidates.json file")
    parser.add_argument("--source-experiment-id", action="append", default=[], dest="source_experiment_ids")
    parser.add_argument("--rationale", default="")
    parser.add_argument("--dry-run", action="store_true", help="build and print the bundle, never POST it")
    args = parser.parse_args()

    if not RUNNER_TOKEN and not args.dry_run:
        print("CALIBRATION_RUNNER_TOKEN not set — refusing to submit (use --dry-run to build the bundle only)", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        records = json.load(f)
    if not isinstance(records, list):
        print(f"{args.input} must contain a JSON array of candidate records", file=sys.stderr)
        sys.exit(1)

    bundle = build_bundle(records, args.source_experiment_ids, args.rationale)
    print(f"selected {len(bundle['candidates'])} candidate(s), excluded {len(bundle['excluded'])}")
    for e in bundle["excluded"]:
        print(f"  excluded: {e['provenance']} -- {e['reason']}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(bundle, indent=2, ensure_ascii=False))
        return

    if not bundle["candidates"]:
        print("nothing eligible to submit -- not calling the ingestion endpoint", file=sys.stderr)
        sys.exit(0)

    ok, body = _request("POST", "/ops/calibration/candidates", {**bundle, "runner_id": RUNNER_ID})
    if not ok:
        print(f"ingestion request failed: {body}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(body, indent=2, ensure_ascii=False))
    if body.get("has_rejections"):
        print("one or more candidates were rejected by the server — see results[] above", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
