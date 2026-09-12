#!/usr/bin/env python3
"""Focused publish_retained_fast_lane regressions A-F; no model or network calls."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import publish_retained_fast_lane as PRF  # noqa: E402
from new_engine_v1 import composition as CP  # noqa: E402

FAILURES = []
ARTICLE = "# A Title\n\nA complete retained Fast Lane article body.\n"


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name
          + ("" if condition else "  " + str(detail)))
    if not condition:
        FAILURES.append(name)


def _base_artifacts(root: pathlib.Path, *, article=ARTICLE):
    (root / "article.md").write_text(article, encoding="utf-8")
    (root / "WRITER_OUTPUT.json").write_text(json.dumps(
        {"article_text": article}), encoding="utf-8")
    (root / "CLAIM_MAP_VALIDATION.json").write_text(json.dumps(
        {"errors": [], "claim_map": [], "retries": 0}), encoding="utf-8")
    (root / "SAFETY_AUDIT.json").write_text(json.dumps(
        {"status": "PASS"}), encoding="utf-8")
    (root / "GROUNDING_AUDIT.json").write_text(json.dumps(
        {"status": "PASS"}), encoding="utf-8")
    (root / "FACT_CHECK.json").write_text(json.dumps(
        {"status": "PASS", "contradicted": [], "advisory": [],
         "extraction_status": "ok", "extraction_error": None,
         "claims_extracted": 1, "fact_check_completed": True,
         "findings": [{"claim_id": "C01", "verdict": "VERIFIED"}],
         "not_checked": [], "max_claims": 16,
         "unverifiable_count": 0, "soft_contradicted_count": 0}),
        encoding="utf-8")
    (root / "READER_AUDIT.json").write_text(json.dumps(
        {"status": "PASS", "held": {}}), encoding="utf-8")


def sha_of(text):
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    # A. A valid, all-PASS retained run rehydrates and is bridge-eligible.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _base_artifacts(root)
        result = PRF.resume(str(root))
        check("A valid retained run rehydrates", result["status"] == "ELIGIBLE_NOT_PUBLISHED",
              result)
        check("A bridge eligible", result.get("bridge_eligible") is True)

    # B. SHA mismatch (WRITER_OUTPUT diverges from article.md) blocks.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _base_artifacts(root)
        (root / "WRITER_OUTPUT.json").write_text(json.dumps(
            {"article_text": "different bytes entirely"}), encoding="utf-8")
        result = PRF.resume(str(root))
        check("B SHA/body mismatch blocks", result["status"] == "BLOCKED", result)
        check("B names the right blocker", "diverge" in result.get("blocker", ""),
              result.get("blocker"))

    # C. Missing required artifact blocks.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _base_artifacts(root)
        (root / "GROUNDING_AUDIT.json").unlink()
        result = PRF.resume(str(root))
        check("C missing artifact blocks", result["status"] == "BLOCKED", result)
        check("C names the missing file", "GROUNDING_AUDIT.json" in result.get("blocker", ""),
              result.get("blocker"))

    # D. A MATERIAL Reader finding blocks even with a well-formed decision file.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _base_artifacts(root)
        held = {"READABILITY": {"verdict": "HOLD", "note": "x"}}
        (root / "READER_AUDIT.json").write_text(json.dumps(
            {"status": "HOLD", "held": held}), encoding="utf-8")
        (root / "PUBLICATION_DECISION.json").write_text(json.dumps({
            "article_sha256": sha_of(ARTICLE), "raw_reader_status": "HOLD",
            "publication_status": "PASS_WITH_MINOR_FINDINGS",
            "reader_materiality_classification": {"READABILITY": "MATERIAL"},
        }), encoding="utf-8")
        result = PRF.resume(str(root))
        check("D MATERIAL Reader finding blocks", result["status"] == "BLOCKED", result)

    # E. An invalid Fact Check adjudication (SHA mismatch) blocks.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _base_artifacts(root)
        (root / "FACT_CHECK.json").write_text(json.dumps(
            {"status": "HOLD", "contradicted": [{"claim": "X"}]}), encoding="utf-8")
        (root / "FACT_CHECK_ADJUDICATION.json").write_text(json.dumps({
            "article_sha256": "0" * 64, "raw_fact_check_status": "HOLD",
            "effective_fact_check_status": "PASS",
            "all_blocking_findings_adjudicated": True,
            "findings": [{"article_span": "X", "adjudication": "VERIFIED_PRIMARY_SOURCE"}],
        }), encoding="utf-8")
        result = PRF.resume(str(root))
        check("E invalid Fact Check adjudication blocks", result["status"] == "BLOCKED", result)
        check("E names SHA mismatch", "sha256" in result.get("blocker", ""),
              result.get("blocker"))

    # F. Candidate body diverging from the frozen article blocks even post-bridge.
    # Exercised via persist_candidate's own contract: publish_retained_fast_lane
    # re-reads the just-written draft body and compares it back to validated
    # article_text before ever calling the publisher.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _base_artifacts(root)
        import new_engine_candidate as CAND
        orig_persist = CAND.persist_candidate

        def _tampering_persist(*a, **kw):
            path = orig_persist(*a, **kw)
            path.write_text(path.read_text(encoding="utf-8") + "\ntampered extra line\n",
                            encoding="utf-8")
            return path

        CAND.persist_candidate = _tampering_persist
        try:
            with tempfile.TemporaryDirectory() as dd:
                result = PRF.resume(str(root), drafts_dir=pathlib.Path(dd), publish=True)
        finally:
            CAND.persist_candidate = orig_persist
        check("F candidate body divergence blocks", result["status"] == "BLOCKED", result)
        check("F names body divergence", "diverged" in result.get("blocker", ""),
              result.get("blocker"))

    if FAILURES:
        print("%d failure(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("All publish_retained_fast_lane tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
