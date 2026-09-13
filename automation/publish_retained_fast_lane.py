#!/usr/bin/env python3
"""
publish_retained_fast_lane.py -- resume publication for an already-completed,
retained Fast Lane V1 run.

Loads and cross-validates the artifacts a Fast Lane replay (asl_packet.py-style:
LEDGER + RESEARCH_PACK -> ARTICLE_PACKET -> ARCH -> WRITER_OUTPUT ->
CLAIM_MAP_VALIDATION -> SAFETY_AUDIT -> GROUNDING_AUDIT -> FACT_CHECK ->
READER_AUDIT) already wrote to disk. Reruns NOTHING: no Writer, Claim Mapper,
Safety, Grounding, Fact Check or Reader call happens here. Only reads, then --
if the existing publication-safety bridge grants eligibility -- hands the
result to the existing candidate persistence and publisher.

Fails closed: any missing artifact, any SHA mismatch, any unresolved MATERIAL
Reader finding, or any invalid Fact Check adjudication blocks publication with
a named, exact reason. General: takes no article- or run-specific assumption
beyond what each retained artifact itself states.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import new_engine_candidate as CAND                      # noqa: E402
import publication_safety_bridge as BRIDGE                # noqa: E402
from new_engine_v1 import composition as CP               # noqa: E402


class ResumeBlocked(Exception):
    """Raised with an exact, named reason. Never guessed past."""


def _load(run_dir: pathlib.Path, name: str) -> dict:
    p = run_dir / name
    if not p.is_file():
        raise ResumeBlocked("missing required artifact: %s" % name)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        raise ResumeBlocked("%s: unreadable/malformed (%s)" % (name, e))


def _validate_fact_check_adjudication(fact_check: dict, adjudication: dict,
                                      article_sha: str) -> tuple:
    if adjudication.get("article_sha256") != article_sha:
        return False, "adjudication article_sha256 does not match current article bytes"
    if adjudication.get("raw_fact_check_status") != CP.HOLD:
        return False, "adjudication raw_fact_check_status is not HOLD"
    if adjudication.get("effective_fact_check_status") != CP.PASS:
        return False, "adjudication effective_fact_check_status is not PASS"
    if not adjudication.get("all_blocking_findings_adjudicated"):
        return False, "adjudication does not claim all_blocking_findings_adjudicated"
    raw_blocking = {c.get("claim") for c in (fact_check.get("contradicted") or [])}
    adjudicated = {f.get("article_span") for f in (adjudication.get("findings") or [])
                  if f.get("adjudication") == "VERIFIED_PRIMARY_SOURCE"}
    missing = raw_blocking - adjudicated
    if missing:
        return False, "raw contradicted claim(s) not covered by adjudication: %s" % sorted(missing)
    if not raw_blocking:
        return False, "no raw contradicted claims to adjudicate -- HOLD status unexplained"
    return True, ("%d blocking contradiction(s) adjudicated VERIFIED_PRIMARY_SOURCE"
                 % len(raw_blocking))


def _validate_reader_decision(reader: dict, decision: dict, article_sha: str) -> tuple:
    if decision.get("article_sha256") != article_sha:
        return False, "decision article_sha256 does not match current article bytes"
    if decision.get("raw_reader_status") != CP.HOLD:
        return False, "decision raw_reader_status is not HOLD"
    if decision.get("publication_status") != "PASS_WITH_MINOR_FINDINGS":
        return False, "publication_status is not PASS_WITH_MINOR_FINDINGS"
    held = set(reader.get("held") or {})
    classified = decision.get("reader_materiality_classification") or {}
    if set(classified) != held:
        return False, "decision does not classify exactly the retained held dimensions"
    non_minor = {k: v for k, v in classified.items() if str(v).upper() != "MINOR"}
    if non_minor:
        return False, "non-MINOR Reader classification(s): %s" % non_minor
    if not held:
        return False, "no held dimensions to classify -- HOLD status unexplained"
    return True, "%d Reader HOLD dimension(s), all MINOR" % len(held)


def validate_retained_run(run_dir: pathlib.Path) -> dict:
    """Load and cross-validate every retained Fast Lane artifact needed to authorize
    publication. Returns a dict of validated facts on success; raises ResumeBlocked
    with an exact, named reason otherwise. Reruns no editorial stage."""
    article_path = run_dir / "article.md"
    if not article_path.is_file():
        raise ResumeBlocked("missing required artifact: article.md")
    article_text = article_path.read_text(encoding="utf-8")
    article_sha = hashlib.sha256(article_text.encode("utf-8")).hexdigest()

    writer_output = _load(run_dir, "WRITER_OUTPUT.json")
    if writer_output.get("article_text") != article_text:
        raise ResumeBlocked("article.md and WRITER_OUTPUT.json article_text diverge")

    claim_map = _load(run_dir, "CLAIM_MAP_VALIDATION.json")
    if claim_map.get("errors"):
        raise ResumeBlocked("CLAIM_MAP_VALIDATION.json has unresolved errors: %s"
                            % claim_map["errors"])

    safety = _load(run_dir, "SAFETY_AUDIT.json")
    if safety.get("status") != CP.PASS:
        raise ResumeBlocked("SAFETY_AUDIT.json status=%r, not PASS" % safety.get("status"))

    grounding = _load(run_dir, "GROUNDING_AUDIT.json")
    if grounding.get("status") != CP.PASS:
        raise ResumeBlocked("GROUNDING_AUDIT.json status=%r, not PASS"
                            % grounding.get("status"))

    fact_check = _load(run_dir, "FACT_CHECK.json")
    fc_status = fact_check.get("status")
    if fc_status == CP.PASS:
        fc_effective_pass, fc_note = True, "raw PASS"
    elif fc_status == CP.HOLD:
        adjudication = _load(run_dir, "FACT_CHECK_ADJUDICATION.json")
        fc_effective_pass, fc_note = _validate_fact_check_adjudication(
            fact_check, adjudication, article_sha)
        if not fc_effective_pass:
            raise ResumeBlocked("FACT_CHECK adjudication invalid: %s" % fc_note)
    else:
        raise ResumeBlocked("FACT_CHECK.json status=%r, not PASS or HOLD" % fc_status)

    reader = _load(run_dir, "READER_AUDIT.json")
    rd_status = reader.get("status")
    if rd_status == CP.PASS:
        rd_effective_pass, rd_note = True, "raw PASS"
    elif rd_status == CP.HOLD:
        decision = _load(run_dir, "PUBLICATION_DECISION.json")
        rd_effective_pass, rd_note = _validate_reader_decision(reader, decision, article_sha)
        if not rd_effective_pass:
            raise ResumeBlocked("PUBLICATION_DECISION invalid: %s" % rd_note)
    else:
        raise ResumeBlocked("READER_AUDIT.json status=%r, not PASS or HOLD" % rd_status)

    return {
        "article_text": article_text, "article_sha256": article_sha,
        "safety_status": safety.get("status"), "grounding_status": grounding.get("status"),
        "fact_check": fact_check, "fact_check_effective_pass": fc_effective_pass,
        "fact_check_note": fc_note,
        "reader": reader, "reader_effective_pass": rd_effective_pass,
        "reader_note": rd_note,
        "claim_map": claim_map,
        "ledger": _load(run_dir, "LEDGER.json"),
        "research_pack": _load(run_dir, "RESEARCH_PACK.json"),
    }


def _retained_fact_check_fn(fact_check: dict):
    """Reports the ALREADY-COMPUTED retained FACT_CHECK.json result, unfiltered, to the
    bridge's authoritative check. Makes no model or network call -- this is not a
    fact-check rerun, it is the same result the retained run already has, read back
    honestly (including any real, unadjudicated contradiction)."""
    def _fn(_article_text):
        return fact_check
    return _fn


def build_bridge_out(validated: dict) -> dict:
    """The MINIMAL composition-shaped dict the existing bridge needs. Every stage
    value comes directly from a retained artifact's own recorded status -- nothing is
    synthesized to make eligibility more likely than the retained record supports."""
    stages = {s: CP.PASS for s in CP.STAGES}
    stages[CP.SAFETY] = validated["safety_status"]
    stages[CP.GROUNDING] = validated["grounding_status"]
    stages[CP.FACT_CHECK] = validated["fact_check"].get("status")
    stages[CP.READER] = validated["reader"].get("status")
    return {
        "decision": "ACCEPT",
        "provider": {"composition_engine": CP.COMPOSITION_STORY_ARCHITECTURE},
        "composition": {
            "status": CP.PASS, "stages": stages,
            "article_text": validated["article_text"], "publication_ready": True,
            "words": len(validated["article_text"].split()),
            "subject": "", "failure_stage": None,
        },
        "artifacts": {},
    }


def _title_of(article_text: str) -> str:
    for line in article_text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return "Untitled"


def _slug(text: str) -> str:
    """Same pattern as new_engine_production._slug -- a readable, Jekyll-filename-safe
    slug derived from the title, not the raw run directory name."""
    return re.sub(r"[^a-z0-9]+", "-", (text or "candidate").lower()).strip("-")[:70]


def resume(run_dir: str, *, drafts_dir: pathlib.Path | None = None,
          publish: bool = False) -> dict:
    run_dir = pathlib.Path(run_dir)
    result = {"run_dir": str(run_dir)}
    try:
        validated = validate_retained_run(run_dir)
    except ResumeBlocked as e:
        result.update(status="BLOCKED", blocker=str(e))
        return result
    result["article_sha256"] = validated["article_sha256"]
    result["fact_check_note"] = validated["fact_check_note"]
    result["reader_note"] = validated["reader_note"]

    out = build_bridge_out(validated)
    bridge = BRIDGE.evaluate(
        out, fact_check_fn=_retained_fact_check_fn(validated["fact_check"]),
        run_dir=run_dir)
    result["bridge_eligible"] = bridge.eligible
    result["bridge_failures"] = [c["check"] for c in bridge.failures]
    result["bridge_summary"] = bridge.summary()
    if not bridge.eligible:
        result.update(status="BLOCKED",
                      blocker="bridge not eligible: %s" % ", ".join(result["bridge_failures"]))
        return result

    title = _title_of(validated["article_text"])
    result["title"] = title
    if not publish:
        result["status"] = "ELIGIBLE_NOT_PUBLISHED"
        return result

    drafts_dir = drafts_dir or (HERE.parent / "_drafts")
    stamp = BRIDGE.stamp_fields(bridge)
    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta = {
        "run": run_dir.name, "generated_at": generated_at, "decision": "ACCEPT",
        "source_url": "", "source_sha256": "",
        "discovery_hash": "", "article_form_hash": "",
        "grounding_status": validated["grounding_status"], "grounding_unsupported": 0,
        "provider_model": "",
    }
    import new_engine_candidate as CANDIDATE
    pack = validated.get("research_pack") or {}
    pack = pack.get("payload", pack)
    sources = CANDIDATE.public_sources(pack, validated.get("ledger"),
                                       validated.get("claim_map"))
    path = CAND.persist_candidate(
        drafts_dir=drafts_dir, slug=_slug(title), body=validated["article_text"],
        title=title, author="Maya Flux", engine_meta=meta, rehearsal=False,
        safety=stamp, package=None, sources=sources)
    result["candidate_path"] = str(path)
    candidate_body = path.read_text(encoding="utf-8").split("---\n", 2)[-1].strip("\n")
    if candidate_body != validated["article_text"].strip("\n"):
        result.update(status="BLOCKED",
                      blocker="candidate body diverged from frozen article text")
        return result

    import publish_best as PUB
    rc = PUB.publish_candidate(path)
    result["published"] = rc == 0
    result["status"] = "PUBLISHED" if rc == 0 else "PUBLISH_FAILED"
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--publish", action="store_true",
                   help="Actually persist the candidate and publish. Without this "
                        "flag the run is only validated and the bridge is only "
                        "evaluated (dry run).")
    args = ap.parse_args()
    print(json.dumps(resume(args.run_dir, publish=args.publish),
                     indent=2, sort_keys=True, default=str))
