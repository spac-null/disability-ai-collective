#!/usr/bin/env python3
"""Focused Reader materiality bridge regressions A--F; no model or network calls."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import publication_safety_bridge as BRIDGE  # noqa: E402
from new_engine_v1 import composition as CP  # noqa: E402
from new_engine_v1 import contracts as C  # noqa: E402


FAILURES = []
ARTICLE = "A complete retained article whose factual gates have independently passed."


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name
          + ("" if condition else "  " + str(detail)))
    if not condition:
        FAILURES.append(name)


def clean_fact_check(_article):
    finding = {"claim_id": "C01", "type": "STAT", "subject": "subject",
               "claim_text": "a checked claim", "verdict": "VERIFIED",
               "reason": "verified", "blocking": False}
    return {"contradicted": [], "advisory": [], "unverifiable_count": 0,
            "soft_contradicted_count": 0, "extraction_status": "ok",
            "extraction_error": None, "claims_extracted": 1,
            "fact_check_completed": True, "findings": [finding], "not_checked": []}


def out(reader_status):
    stages = {stage: CP.PASS for stage in CP.STAGES}
    stages[CP.READER] = reader_status
    return {
        "decision": "ACCEPT",
        "provider": {"composition_engine": CP.COMPOSITION_STORY_ARCHITECTURE},
        "composition": {"status": CP.PASS, "stages": stages,
                        "article_text": ARTICLE, "publication_ready": True,
                        "words": len(ARTICLE.split()), "subject": "subject",
                        "failure_stage": None},
        "artifacts": {},
    }


def artifacts(root, *, publication_status="PASS_WITH_MINOR_FINDINGS",
              classifications=None, article_sha=None):
    held = {
        "READABILITY": {"verdict": "HOLD", "note": "one awkward sentence",
                        "passages": ["A complete retained article"]},
        "MOMENTUM": {"verdict": "HOLD", "note": "one small repetition",
                     "passages": ["whose factual gates"]},
    }
    classification = classifications or {key: "MINOR" for key in held}
    (root / "READER_AUDIT.json").write_text(json.dumps({
        "status": "HOLD", "held": held,
    }), encoding="utf-8")
    (root / "PUBLICATION_DECISION.json").write_text(json.dumps({
        "article_sha256": article_sha or C.sha256_text(ARTICLE),
        "raw_reader_status": "HOLD",
        "reader_findings": {key: value["note"] for key, value in held.items()},
        "reader_materiality_classification": classification,
        "publication_status": publication_status,
    }), encoding="utf-8")


def evaluate(reader_status, root=None):
    return BRIDGE.evaluate(out(reader_status), fact_check_fn=clean_fact_check,
                           run_dir=root)


def main():
    # A. Raw PASS remains sufficient, with no decision artifact.
    a = evaluate(CP.PASS)
    check("A raw Reader PASS remains eligible", a.eligible)
    check("A route is recorded as raw", a.summary()["reader_raw_pass"]
          and not a.summary()["reader_materiality_adjudication"])

    # B. Raw HOLD cannot pass without the retained decision.
    with tempfile.TemporaryDirectory() as d:
        b = evaluate(CP.HOLD, pathlib.Path(d))
        check("B raw HOLD without decision blocks", not b.eligible)

    # C. Exact SHA + exhaustive MINOR classification authorizes Reader effectively.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); artifacts(root)
        c = evaluate(CP.HOLD, root)
        summary = c.summary()
        check("C valid minor adjudication is eligible", c.eligible, c.failures)
        check("C raw HOLD remains visible", not summary["reader_raw_pass"])
        check("C effective route is visible", summary["reader_materiality_adjudication"]
              and summary["reader_effective_pass"])
        check("C evidence retains 2 MINOR and 0 MATERIAL",
              summary["reader_materiality_evidence"]["minor_finding_count"] == 2
              and summary["reader_materiality_evidence"]["material_finding_count"] == 0)

    # D. Material editorial status cannot authorize a raw HOLD.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); artifacts(root, publication_status="HOLD_MATERIAL_EDITORIAL")
        check("D HOLD_MATERIAL_EDITORIAL blocks", not evaluate(CP.HOLD, root).eligible)

    # E. One MATERIAL classification blocks even under a minor publication label.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); artifacts(
            root, classifications={"READABILITY": "MINOR", "MOMENTUM": "MATERIAL"})
        check("E one MATERIAL Reader finding blocks", not evaluate(CP.HOLD, root).eligible)

    # F. Decisions are byte-bound to the current article.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); artifacts(root, article_sha="0" * 64)
        check("F article SHA mismatch blocks", not evaluate(CP.HOLD, root).eligible)

    if FAILURES:
        print("%d failure(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("All Reader materiality bridge tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
