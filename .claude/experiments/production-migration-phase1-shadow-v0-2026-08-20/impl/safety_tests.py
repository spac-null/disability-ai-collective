#!/usr/bin/env python3
"""
safety_tests.py -- deterministic safety tests for shadow V0.

Isolation, fail-closed behaviour and stage separation only. No literary quality tests.
No network, no model calls, no production state.

USAGE:  python3 safety_tests.py      (exit 0 = all pass)
"""
import copy
import io
import os
import pathlib
import sys
import tempfile
import contextlib

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from shadow_v0 import contracts as C            # noqa: E402
from shadow_v0.runner import run, ShadowDisabled, current_mode, MODE_REPLAY, MODE_LIVE_SHADOW  # noqa: E402
from shadow_v0.fixtures import Test2Fixture, Form13Fixture  # noqa: E402

PKG = HERE / "shadow_v0"
FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s %s" % (name, detail))
        FAILURES.append(name)


def _tmp_run(fixture, mode=MODE_REPLAY):
    with tempfile.TemporaryDirectory() as d:
        return run(fixture, pathlib.Path(d), mode=mode), pathlib.Path(d)


# ---------------------------------------------------------------- isolation
def test_default_off():
    os.environ.pop("SHADOW_V0_MODE", None)
    check("shadow mode defaults to OFF", current_mode() == "OFF", current_mode())
    try:
        with tempfile.TemporaryDirectory() as d:
            run(Test2Fixture(), pathlib.Path(d))
        check("run() refuses when OFF", False, "it ran")
    except ShadowDisabled:
        check("run() refuses when OFF", True)


def test_live_shadow_not_executable():
    try:
        with tempfile.TemporaryDirectory() as d:
            run(Test2Fixture(), pathlib.Path(d), mode=MODE_LIVE_SHADOW)
        check("LIVE_SHADOW refuses to execute", False, "it ran")
    except NotImplementedError:
        check("LIVE_SHADOW refuses to execute", True)


def _code_tokens(path):
    """Every identifier and non-docstring string literal in a module. Comments and
    docstrings are excluded on purpose: this test must assert what the code DOES,
    not what its prose says. (An earlier version failed on the word '_posts'
    appearing inside runner.py's own safety docstring.)"""
    import ast
    tree = ast.parse(path.read_text())
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
               and isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            out.append(node.value)
        elif isinstance(node, ast.Name):
            out.append(node.id)
        elif isinstance(node, ast.Attribute):
            out.append(node.attr)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            out.append(getattr(node, "module", "") or "")
            out.extend(a.name for a in node.names)
    return "\n".join(out)


def test_no_db_or_publication_code():
    src = "\n".join(_code_tokens(p) for p in sorted(PKG.glob("*.py")))
    for banned, label in [("sqlite3", "no sqlite3 in executable code"),
                          ("_posts", "no _posts path in executable code"),
                          ("_drafts", "no _drafts path in executable code"),
                          ("subprocess", "no subprocess in executable code"),
                          ("requests", "no network client in executable code"),
                          ("urllib", "no urllib in executable code"),
                          ("socket", "no socket in executable code")]:
        check(label, banned not in src, "found %r" % banned)


def test_writes_confined_to_run_root():
    repo = pathlib.Path(__file__).resolve().parents[5]
    before = {p: p.stat().st_mtime for p in list((repo / "_posts").glob("*.md"))[:5]}
    result, tmp = _tmp_run(Test2Fixture())
    # tmp is gone after the context manager; re-run to inspect written files
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        run(Test2Fixture(), d, mode=MODE_REPLAY)
        written = sorted(p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file())
        check("writes only under the run root", all(w.startswith("test2-") for w in written),
              str(written[:3]))
        check("source snapshot persisted as a file",
              any(w.endswith("source-snapshot.txt") for w in written))
        check("manifest persisted", any(w.endswith("MANIFEST.json") for w in written))
    after = {p: p.stat().st_mtime for p in before}
    check("no _posts file touched", before == after)


# ---------------------------------------------------------------- persistence
def test_source_text_persisted_not_just_hash():
    payload = Test2Fixture().source_snapshot()
    check("SOURCE_SNAPSHOT carries source_text", bool(payload.get("source_text")))
    check("SOURCE_SNAPSHOT carries provenance origin", bool(payload["provenance"].get("origin")))
    check("SOURCE_SNAPSHOT hash matches its own text",
          C.sha256_text(payload["source_text"]) == payload["source_sha256"])
    check("frozen Test-2 source hash preserved exactly",
          payload["source_sha256"] == "be381bbc157f967ea11c46817616d91567394dbfb5801b08898ca1fa46466c6c")


# ---------------------------------------------------------------- fail-closed
def test_hash_mismatch_fails_closed():
    p = Test2Fixture().source_snapshot()
    p = copy.deepcopy(p)
    p["source_sha256"] = "0" * 64
    art = C.Artifact(stage=C.SOURCE_SNAPSHOT, created_at="X", payload=p)
    try:
        C.validate(art); check("source hash mismatch fails closed", False, "accepted")
    except C.ContractViolation:
        check("source hash mismatch fails closed", True)


def test_lineage_break_fails_closed():
    src = C.Artifact(C.SOURCE_SNAPSHOT, "X", Test2Fixture().source_snapshot())
    child = C.Artifact(C.DISCOVERY, "X", Test2Fixture().discovery(),
                       input_hashes={"source": "0" * 64})
    try:
        C.verify_lineage(child, {"source": src}); check("lineage break fails closed", False, "accepted")
    except C.ContractViolation:
        check("lineage break fails closed", True)


def test_missing_stage_artifact_holds():
    result, _ = _tmp_run(Test2Fixture())
    A = dict(result["artifacts"])
    del A[C.WRITER_OUTPUT]
    from shadow_v0.decision import decide
    d, reasons = decide(A)
    check("missing required stage -> HOLD", d == "HOLD", d)
    check("missing stage reason names the gap", "lineage incomplete" in reasons[0])


def test_missing_required_field_fails_closed():
    p = Test2Fixture().article_form(); p = copy.deepcopy(p); p.pop("arrival")
    try:
        C.validate(C.Artifact(C.ARTICLE_FORM, "X", p))
        check("missing required field fails closed", False, "accepted")
    except C.ContractViolation:
        check("missing required field fails closed", True)


# ---------------------------------------------------------------- decision
def test_grounding_unresolved_holds():
    result, _ = _tmp_run(Form13Fixture())
    check("FORM-1.3 unresolved unsupported -> HOLD", result["decision"] == "HOLD", result["decision"])
    check("HOLD reason names the unresolved findings",
          "unresolved TRUE_UNSUPPORTED" in result["reasons"][0])


def test_uncertain_holds_by_default():
    from shadow_v0.decision import decide
    result, _ = _tmp_run(Test2Fixture())
    A = copy.deepcopy(result["artifacts"])
    A[C.GROUNDING_FINDINGS].payload["uncertain_adjudicated"] = False
    d, reasons = decide(A)
    check("unadjudicated TRUE_UNCERTAIN -> HOLD", d == "HOLD", d)


def test_provider_failure_holds():
    from shadow_v0.decision import decide
    result, _ = _tmp_run(Test2Fixture())
    A = copy.deepcopy(result["artifacts"])
    A[C.WRITER_OUTPUT].payload["provider_status"] = "failed"
    d, reasons = decide(A)
    check("provider failure -> HOLD (no template fallback)", d == "HOLD", d)
    check("provider-failure reason rejects legacy fallback", "fallback" in reasons[0])


def test_accept_path():
    result, _ = _tmp_run(Test2Fixture())
    check("Test 2 replays to ACCEPT", result["decision"] == "ACCEPT", result["decision"])


# ---------------------------------------------------------------- architecture
def test_no_legacy_prompt_surface():
    for fx in (Test2Fixture(), Form13Fixture()):
        text = fx.writer_input()["prompt_text"]
        hits = [m for m in C.LEGACY_PROMPT_MARKERS if m in text]
        check("no legacy prompt surface in %s writer input" % fx.name, not hits, str(hits[:3]))
    # and the contract actively rejects one
    p = copy.deepcopy(Test2Fixture().writer_input())
    p["prompt_text"] = "YOU ARE MAYA FLUX. " + p["prompt_text"]
    p["prompt_sha256"] = C.sha256_text(p["prompt_text"])
    try:
        C.validate(C.Artifact(C.WRITER_INPUT, "X", p))
        check("legacy marker in writer input fails closed", False, "accepted")
    except C.ContractViolation:
        check("legacy marker in writer input fails closed", True)


def test_form_and_grounding_are_separate_stages():
    result, _ = _tmp_run(Test2Fixture())
    A = result["artifacts"]
    check("ARTICLE_FORM and GROUNDING_FINDINGS are distinct artifacts",
          A[C.ARTICLE_FORM].content_hash() != A[C.GROUNDING_FINDINGS].content_hash())
    gf_inputs = set(A[C.GROUNDING_FINDINGS].input_hashes)
    check("Writer Grounding receives writer_output + source", gf_inputs == {"writer_output", "source"}, str(gf_inputs))
    check("Writer Grounding does NOT receive ARTICLE_FORM", "article_form" not in gf_inputs)
    af_inputs = set(A[C.ARTICLE_FORM].input_hashes)
    check("Article Form derives from discovery + source", af_inputs == {"discovery", "source"}, str(af_inputs))
    check("Discovery derives from source only", set(A[C.DISCOVERY].input_hashes) == {"source"})


def test_repair_is_patch_only():
    p = copy.deepcopy(Test2Fixture().grounding_repair()); p["mode"] = "rewrite"
    try:
        C.validate(C.Artifact(C.GROUNDING_REPAIR, "X", p))
        check("non-patch-only repair fails closed", False, "accepted")
    except C.ContractViolation:
        check("non-patch-only repair fails closed", True)


def test_determinism():
    a, _ = _tmp_run(Test2Fixture())
    b, _ = _tmp_run(Test2Fixture())
    same = all(a["artifacts"][s].content_hash() == b["artifacts"][s].content_hash()
               for s in a["artifacts"])
    check("replay is deterministic across runs", same)


def main():
    for fn in [test_default_off, test_live_shadow_not_executable, test_no_db_or_publication_code,
               test_writes_confined_to_run_root, test_source_text_persisted_not_just_hash,
               test_hash_mismatch_fails_closed, test_lineage_break_fails_closed,
               test_missing_stage_artifact_holds, test_missing_required_field_fails_closed,
               test_grounding_unresolved_holds, test_uncertain_holds_by_default,
               test_provider_failure_holds, test_accept_path, test_no_legacy_prompt_surface,
               test_form_and_grounding_are_separate_stages, test_repair_is_patch_only,
               test_determinism]:
        print("\n%s" % fn.__name__)
        fn()
    print("\n%s" % ("-" * 60))
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - %s" % f)
        sys.exit(1)
    print("ALL SAFETY TESTS PASSED")


if __name__ == "__main__":
    main()
