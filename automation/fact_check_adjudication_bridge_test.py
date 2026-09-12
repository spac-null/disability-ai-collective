#!/usr/bin/env python3
"""Focused Fact Check adjudication bridge regressions A-H; no model or network calls."""
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
ARTICLE_SHA = C.sha256_text(ARTICLE)


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name
          + ("" if condition else "  " + str(detail)))
    if not condition:
        FAILURES.append(name)


def clean_reader():
    return {"status": CP.PASS, "held": {}}


def minor_reader_decision(root):
    held = {"READABILITY": {"verdict": "HOLD", "note": "one awkward sentence"}}
    (root / "READER_AUDIT.json").write_text(json.dumps({
        "status": "HOLD", "held": held}), encoding="utf-8")
    (root / "PUBLICATION_DECISION.json").write_text(json.dumps({
        "article_sha256": ARTICLE_SHA, "raw_reader_status": "HOLD",
        "publication_status": "PASS_WITH_MINOR_FINDINGS",
        "reader_findings": {"READABILITY": "one awkward sentence"},
        "reader_materiality_classification": {"READABILITY": "MINOR"},
    }), encoding="utf-8")
    return {"status": "HOLD", "held": held}


def fact_check_fn_factory(contradicted, findings=None, claims_extracted=None):
    def _fn(_article):
        return {"extraction_status": "ok",
               "claims_extracted": claims_extracted or (len(findings or []) or 1),
               "fact_check_completed": True,
               "findings": findings or [{"claim_id": "C01", "verdict": "VERIFIED"}],
               "not_checked": [], "contradicted": contradicted, "advisory": [],
               "unverifiable_count": 0, "soft_contradicted_count": 0, "max_claims": 16}
    return _fn


def out_for(fact_check_status, reader=None):
    stages = {s: CP.PASS for s in CP.STAGES}
    stages[CP.FACT_CHECK] = fact_check_status
    reader = reader or clean_reader()
    stages[CP.READER] = reader["status"]
    return {
        "decision": "ACCEPT",
        "provider": {"composition_engine": CP.COMPOSITION_STORY_ARCHITECTURE},
        "composition": {"status": CP.PASS, "stages": stages,
                        "article_text": ARTICLE, "publication_ready": True,
                        "words": len(ARTICLE.split()), "subject": "subject",
                        "failure_stage": None},
        "artifacts": {},
    }


def write_fact_check_json(root, contradicted, status="HOLD"):
    (root / "FACT_CHECK.json").write_text(json.dumps({
        "status": status, "contradicted": contradicted}), encoding="utf-8")


def valid_adjudication(claims, root, *, article_sha=None):
    findings = [{
        "finding_id": "C%02d" % (i + 1), "adjudication": "VERIFIED_PRIMARY_SOURCE",
        "document_identity": "Primary Order, Judge X", "document_url": "https://example.test/doc",
        "source_evidence_sha256": "a" * 64, "article_span": claim,
        "exact_primary_span_normalized": claim, "match_result": "EXACT_MATCH_MODULO_TYPOGRAPHY",
        "reason": "verified against primary document",
    } for i, claim in enumerate(claims)]
    (root / "FACT_CHECK_ADJUDICATION.json").write_text(json.dumps({
        "article_sha256": article_sha or ARTICLE_SHA,
        "raw_fact_check_status": "HOLD", "effective_fact_check_status": "PASS",
        "all_blocking_findings_adjudicated": len(findings) == len(claims),
        "findings": findings,
    }), encoding="utf-8")


def main():
    # A. Raw Fact Check PASS -- unchanged PASS path, no decision file needed.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        out = out_for(CP.PASS)
        b = BRIDGE.evaluate(out, fact_check_fn=fact_check_fn_factory([]), run_dir=root)
        check("A raw Fact Check PASS remains eligible", b.eligible, b.failures)
        s = b.summary()
        check("A route recorded as raw",
              s["fact_check_raw_pass"] and not s["fact_check_adjudication"])

    # B. Raw Fact Check HOLD with no adjudication file -- BLOCK.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        write_fact_check_json(root, [{"claim": "X"}])
        out = out_for(CP.HOLD)
        b = BRIDGE.evaluate(
            out, fact_check_fn=fact_check_fn_factory([{"claim": "X"}]), run_dir=root)
        check("B HOLD without adjudication blocks", not b.eligible)
        check("B names both failing checks",
              {"fact_check_pass", "world_relative_fact_check"} <= set(b.summary()["failures"]))

    # C. Raw HOLD + valid primary-source adjudication covering every blocker -- effective PASS.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        write_fact_check_json(root, [{"claim": "X"}, {"claim": "Y"}])
        valid_adjudication(["X", "Y"], root)
        out = out_for(CP.HOLD)
        b = BRIDGE.evaluate(
            out, fact_check_fn=fact_check_fn_factory([{"claim": "X"}, {"claim": "Y"}]),
            run_dir=root)
        check("C fully adjudicated HOLD is eligible", b.eligible, b.failures)
        s = b.summary()
        check("C effective route visible",
              s["fact_check_adjudication"] and s["fact_check_effective_pass"])
        check("C 2 adjudicated, 0 unadjudicated",
              s["fact_check_adjudication_evidence"]["adjudicated_finding_count"] == 2
              and s["fact_check_adjudication_evidence"]["unadjudicated_blocking_count"] == 0)

    # D. Adjudication covers only 1 of 2 blockers -- BLOCK.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        write_fact_check_json(root, [{"claim": "X"}, {"claim": "Y"}])
        valid_adjudication(["X"], root)  # only X covered
        out = out_for(CP.HOLD)
        b = BRIDGE.evaluate(
            out, fact_check_fn=fact_check_fn_factory([{"claim": "X"}, {"claim": "Y"}]),
            run_dir=root)
        check("D partial adjudication blocks", not b.eligible)

    # E. Article SHA mismatch in the adjudication file -- BLOCK.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        write_fact_check_json(root, [{"claim": "X"}])
        valid_adjudication(["X"], root, article_sha="0" * 64)
        out = out_for(CP.HOLD)
        b = BRIDGE.evaluate(
            out, fact_check_fn=fact_check_fn_factory([{"claim": "X"}]), run_dir=root)
        check("E SHA mismatch blocks", not b.eligible)

    # F. Unknown/unsupported adjudication type -- BLOCK.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        write_fact_check_json(root, [{"claim": "X"}])
        (root / "FACT_CHECK_ADJUDICATION.json").write_text(json.dumps({
            "article_sha256": ARTICLE_SHA, "raw_fact_check_status": "HOLD",
            "effective_fact_check_status": "PASS",
            "all_blocking_findings_adjudicated": True,
            "findings": [{"finding_id": "C01", "adjudication": "EDITORIAL_JUDGMENT_CALL",
                         "document_identity": "x", "document_url": "https://x",
                         "source_evidence_sha256": "a" * 64, "article_span": "X",
                         "exact_primary_span_normalized": "X", "match_result": "EXACT_MATCH",
                         "reason": "we decided it's fine"}],
        }), encoding="utf-8")
        out = out_for(CP.HOLD)
        b = BRIDGE.evaluate(
            out, fact_check_fn=fact_check_fn_factory([{"claim": "X"}]), run_dir=root)
        check("F unsupported adjudication type blocks", not b.eligible)

    # G. Valid adjudication for one contradiction, but another NON-adjudicated
    # world-relative contradiction remains (a claim FACT_CHECK.json never even
    # recorded, e.g. because fact_check_fn returned a different/updated list than
    # what's on disk) -- BLOCK.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        write_fact_check_json(root, [{"claim": "X"}])
        valid_adjudication(["X"], root)
        out = out_for(CP.HOLD)
        # world-relative fact_check_fn reports an EXTRA, unadjudicated contradiction
        b = BRIDGE.evaluate(
            out, fact_check_fn=fact_check_fn_factory([{"claim": "X"}, {"claim": "Z"}]),
            run_dir=root)
        check("G residual unadjudicated contradiction blocks", not b.eligible)
        s = b.summary()
        # Fail-closed on the whole set: one uncovered claim (Z) means NEITHER claim
        # counts as adjudicated for this check, not just the delta -- an otherwise-sound
        # decision file gets no partial credit. See _fact_check_adjudication_coverage.
        check("G world-relative side reports 0 adjudicated given a residual gap",
              s["world_relative_fact_check_adjudication"]["adjudicated_finding_count"] == 0,
              s["world_relative_fact_check_adjudication"])

    # H. Reader PASS_WITH_MINOR_FINDINGS + valid Fact Check adjudication -- bridge
    # eligible when all other requirements pass (both adjudication paths composing).
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        reader = minor_reader_decision(root)
        write_fact_check_json(root, [{"claim": "X"}])
        valid_adjudication(["X"], root)
        out = out_for(CP.HOLD, reader=reader)
        b = BRIDGE.evaluate(
            out, fact_check_fn=fact_check_fn_factory([{"claim": "X"}]), run_dir=root)
        check("H combined Reader+FactCheck adjudication is eligible", b.eligible, b.failures)

    if FAILURES:
        print("%d failure(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("All Fact Check adjudication bridge tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
