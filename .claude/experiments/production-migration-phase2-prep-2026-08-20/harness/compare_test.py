#!/usr/bin/env python3
"""Deterministic tests for the live-vs-shadow comparison harness. No model call."""
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
# reuse the real capture module to build fixtures -- no hand-rolled bundle format
CAP = pathlib.Path("/Users/stargatesgx/code/disability-collective-ai-production-observability/automation")
sys.path.insert(0, str(CAP))

import os                     # noqa: E402
import shadow_capture as SC   # noqa: E402
from compare import compare, CaptureBundle, BundleError  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


SRC = "The council voted 6-3 on Tuesday. 'A difficult trade-off,' said Dana Ruiz."
RAW_WRITER = "RAW\n\nWhat the writer produced before any rewrite."
POST_REWRITE = "REWRITTEN\n\nWhat the rewriter produced. A second named person was added."


def build_bundle(root, run_id="r", *, sealed=True, blocked=False, source=SRC):
    os.environ[SC.ENV_FLAG] = "1"
    os.environ[SC.ENV_ROOT] = str(root)
    SC.capture("evidence", run_id, None, raw_cached_source=source, returned_source=source,
               packet_source=source,
               evidence_packet={"source_text": source, "source_hash": SC._sha256(source),
                                "evidence_packet_hash": "pkt-hash", "source_origin": "fetched_article",
                                "source_truncated": False, "source_length_chars": len(source)},
               provenance={"source_url": "https://example.org/a"})
    SC.capture("commission", run_id, None,
               fable_brief={"persona": "Maya Flux", "grounding_status": "validated",
                            "grounding_violations": []},
               commission_input={"news_title": "t"})
    SC.capture("writer", run_id, None, writer_prompt="YOU ARE MAYA FLUX. ... SOURCE MATERIAL",
               raw_writer_output=RAW_WRITER, provider="p", model="m")
    SC.capture("rewrite", run_id, None, pre_rewrite=RAW_WRITER, post_rewrite=POST_REWRITE)
    SC.capture("disposition", run_id, None, should_block=blocked, review_clean=not blocked,
               fact_check_status="blocked" if blocked else "verified",
               disposition="draft_blocked" if blocked else "draft", slug="s",
               degraded_stages=["fable_brief"] if blocked else [])
    if sealed:
        SC.seal(run_id, None)
    return pathlib.Path(root) / run_id


def build_shadow_run(root, source=SRC, decision="ACCEPT"):
    d = pathlib.Path(root) / "shadow"
    d.mkdir(parents=True, exist_ok=True)
    (d / "source-snapshot.txt").write_text(source)
    (d / "MANIFEST.json").write_text(json.dumps(
        {"schema_version": "shadow-v0.1", "decision": decision,
         "source_sha256": SC._sha256(source), "stage_hashes": {"SOURCE_SNAPSHOT": "x"}}))
    (d / "WRITER_OUTPUT.json").write_text(json.dumps(
        {"payload": {"article_text": "SHADOW ARTICLE\n\nTwo paragraphs here."}}))
    (d / "GROUNDING_FINDINGS.json").write_text(json.dumps(
        {"payload": {"findings": [{"classification": "TRUE_UNSUPPORTED"},
                                  {"classification": "LEGITIMATE_INTERPRETATION"}]}}))
    return d


def test_accepts_exact_hash_match():
    with tempfile.TemporaryDirectory() as t:
        b = build_bundle(t); s = build_shadow_run(t)
        r = compare(b, s)
        check("valid bundle validates", r["validation"]["status"] == "VALID", r["validation"])
        check("exact source hash match -> COMPARABLE", r["verdict"] == "COMPARABLE", r["verdict"])
        check("source equivalence proven by hash",
              r["source_equivalence"]["verdict"] == "EQUIVALENT")


def test_rejects_source_mismatch():
    with tempfile.TemporaryDirectory() as t:
        b = build_bundle(t); s = build_shadow_run(t, source="A DIFFERENT SOURCE ENTIRELY")
        r = compare(b, s)
        check("source mismatch -> REJECTED", r["verdict"] == "REJECTED_SOURCE_MISMATCH", r["verdict"])
        check("mismatch reason explains unsoundness", "identical evidence" in r["reason"])


def test_legacy_only_mode():
    with tempfile.TemporaryDirectory() as t:
        r = compare(build_bundle(t))
        check("no shadow supplied -> LEGACY_ONLY", r["verdict"] == "LEGACY_ONLY", r["verdict"])
        check("legacy outcome still reported", r["legacy_outcome"]["writer_raw_sha256"] is not None)


def test_raw_writer_and_rewrite_distinct():
    with tempfile.TemporaryDirectory() as t:
        r = compare(build_bundle(t))
        lo = r["legacy_outcome"]
        check("raw writer output hash present", lo["writer_raw_sha256"] is not None)
        check("post-rewrite hash present", lo["post_rewrite_sha256"] is not None)
        check("raw writer and rewrite outputs are distinct",
              lo["writer_raw_sha256"] != lo["post_rewrite_sha256"])
        eff = r["legacy_rule_effects"]["rewrite_attributable"]
        check("rewrite effect attributable by construction", eff["changed"] is True)
        check("attribution basis stated", "nothing else executes between" in eff["basis"])


def test_blocked_run_remains_comparable():
    with tempfile.TemporaryDirectory() as t:
        b = build_bundle(t, blocked=True); s = build_shadow_run(t, decision="ACCEPT")
        r = compare(b, s)
        check("blocked legacy run is still COMPARABLE", r["verdict"] == "COMPARABLE", r["verdict"])
        check("legacy blocking observed", r["legacy_outcome"]["should_block"] is True)
        check("outcome pair recorded (legacy BLOCKED vs shadow ACCEPT)",
              r["outcome_pair"]["legacy"] == "BLOCKED" and r["outcome_pair"]["shadow"] == "ACCEPT")
        check("neither system assumed correct", "neither system is assumed" in r["outcome_pair"]["note"])


def test_incomplete_bundle_rejected():
    with tempfile.TemporaryDirectory() as t:
        r = compare(build_bundle(t, sealed=False))
        check("unsealed bundle -> CAPTURE_INVALID", r["verdict"] == "CAPTURE_INVALID", r["verdict"])
        check("next action is the next chronological run", "next chronological" in r["next_action"])


def test_tampered_bundle_rejected():
    with tempfile.TemporaryDirectory() as t:
        b = build_bundle(t)
        (b / "source/packet_source.txt").write_text("TAMPERED")
        r = compare(b)
        check("hash mismatch -> CAPTURE_INVALID", r["verdict"] == "CAPTURE_INVALID", r["verdict"])
        check("mismatch names the artifact",
              any("hash mismatch" in p for p in r["validation"]["problems"]))


def test_missing_bundle_fails_closed():
    try:
        CaptureBundle(pathlib.Path("/nonexistent/xyz")); check("missing bundle fails closed", False)
    except BundleError:
        check("missing bundle fails closed", True)
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t) / "empty"; d.mkdir()
        try:
            CaptureBundle(d); check("bundle without manifest fails closed", False)
        except BundleError:
            check("bundle without manifest fails closed", True)


def test_no_llm_judge():
    """Scans executable code only. An earlier version string-matched raw file text and
    failed on the word 'similarity' inside compare.py's own docstring saying it does NOT
    do similarity -- the test must assert what the code does, not what its prose says."""
    import ast
    tree = ast.parse(pathlib.Path(HERE / "compare.py").read_text())
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
               and isinstance(b[0].value.value, str):
                docs.add(id(b[0].value))
    toks = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
            toks.append(n.value)
        elif isinstance(n, ast.Name):
            toks.append(n.id)
        elif isinstance(n, ast.Attribute):
            toks.append(n.attr)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            toks.append(getattr(n, "module", "") or "")
            toks.extend(a.name for a in n.names)
    src = "\n".join(toks).lower()
    for banned in ("openai", "anthropic", "openrouter", "requests", "urllib", "socket", "subprocess"):
        check("harness contains no %s in executable code" % banned, banned not in src)
    for banned in ("difflib", "sequencematcher", "ratio"):
        check("no prose-similarity machinery (%s)" % banned, banned not in src)


def test_source_representations_reported():
    with tempfile.TemporaryDirectory() as t:
        r = compare(build_bundle(t))
        se = r["source_equivalence"]
        check("legacy packet source hash reported", se["legacy_packet_source_sha256"] is not None)
        check("evidence packet hash reported", se["legacy_evidence_packet_hash"] == "pkt-hash")
        check("raw-cached vs packet-source relationship reported",
              se["raw_cached_vs_packet_source_identical"] is True)
        check("grounding measurements kept separate, not merged",
              "not the same measurement" in r["grounding"]["note"])


def main():
    for fn in [test_accepts_exact_hash_match, test_rejects_source_mismatch, test_legacy_only_mode,
               test_raw_writer_and_rewrite_distinct, test_blocked_run_remains_comparable,
               test_incomplete_bundle_rejected, test_tampered_bundle_rejected,
               test_missing_bundle_fails_closed, test_no_llm_judge,
               test_source_representations_reported]:
        print("\n" + fn.__name__)
        fn()
    os.environ.pop(SC.ENV_FLAG, None)
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL COMPARISON HARNESS TESTS PASSED")


if __name__ == "__main__":
    main()
