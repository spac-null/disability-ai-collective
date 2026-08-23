#!/usr/bin/env python3
"""
shadow_capture_test.py -- deterministic safety tests for the passive capture sidecar.

Isolation and fail-safety only. No network, no model call, no production state.
USAGE: python3 automation/shadow_capture_test.py   (exit 0 = all pass)
"""
import ast
import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import shadow_capture as SC  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


def _on(root):
    os.environ[SC.ENV_FLAG] = "1"
    os.environ[SC.ENV_ROOT] = str(root)


def _off():
    os.environ.pop(SC.ENV_FLAG, None)


def test_default_off():
    _off()
    check("capture disabled with no flag", SC.enabled() is False)
    with tempfile.TemporaryDirectory() as d:
        os.environ[SC.ENV_ROOT] = d
        SC.capture("evidence", "run-x", None, packet_source="hello")
        SC.seal("run-x", None)
        check("OFF writes nothing at all", list(pathlib.Path(d).rglob("*")) == [])


def test_flag_on_writes_only_capture_artifacts():
    with tempfile.TemporaryDirectory() as d:
        _on(d)
        SC.capture("evidence", "r1", None, raw_cached_source="RAW", returned_source="RET",
                   packet_source="PKT", evidence_packet={"source_hash": "abc"},
                   provenance={"source_url": "https://example.org/a"})
        SC.seal("r1", None)
        files = sorted(p.relative_to(d).as_posix() for p in pathlib.Path(d).rglob("*") if p.is_file())
        check("all writes are under the run id", all(f.startswith("r1/") for f in files), files)
        check("no leftover temp/partial files", not any(".part" in f for f in files), files)
        check("manifest is append-only jsonl", "r1/manifest.jsonl" in files)
        check("COMPLETE marker written by seal", "r1/COMPLETE" in files)


def test_source_representations_preserved():
    with tempfile.TemporaryDirectory() as d:
        _on(d)
        SC.capture("evidence", "r2", None, raw_cached_source="FULL EXTRACTION",
                   returned_source="SLICE", packet_source="PACKET",
                   evidence_packet={"source_text": "PACKET", "source_hash": "h"})
        r = pathlib.Path(d) / "r2"
        check("raw cached source preserved verbatim",
              (r / "source/raw_cached_source.txt").read_text() == "FULL EXTRACTION")
        check("returned slice preserved verbatim",
              (r / "source/returned_source.txt").read_text() == "SLICE")
        check("packet source preserved verbatim",
              (r / "source/packet_source.txt").read_text() == "PACKET")
        pkt = json.loads((r / "source/evidence_packet.json").read_text())
        check("evidence packet preserved", pkt["source_hash"] == "h")
        check("three source representations kept distinct",
              len({(r / "source/raw_cached_source.txt").read_text(),
                   (r / "source/returned_source.txt").read_text(),
                   (r / "source/packet_source.txt").read_text()}) == 3)


def test_writer_visible_evidence_and_raw_output():
    with tempfile.TemporaryDirectory() as d:
        _on(d)
        SC.capture("writer", "r3", None, writer_prompt="PROMPT WITH SOURCE MATERIAL",
                   raw_writer_output="RAW ARTICLE", provider="p", model="m")
        SC.capture("rewrite", "r3", None, pre_rewrite="RAW ARTICLE", post_rewrite="REWRITTEN ARTICLE")
        r = pathlib.Path(d) / "r3"
        check("writer-visible evidence (prompt) preserved",
              (r / "legacy/writer_prompt.txt").read_text() == "PROMPT WITH SOURCE MATERIAL")
        check("RAW writer output preserved",
              (r / "legacy/writer_output_raw.md").read_text() == "RAW ARTICLE")
        check("post-rewrite output preserved",
              (r / "legacy/post_rewrite.md").read_text() == "REWRITTEN ARTICLE")
        check("raw writer and rewritten output remain distinct",
              (r / "legacy/writer_output_raw.md").read_text()
              != (r / "legacy/post_rewrite.md").read_text())
        ev = [json.loads(l) for l in (r / "manifest.jsonl").read_text().splitlines()]
        rw = [e for e in ev if e["event"] == "rewrite"][0]
        check("manifest records that the rewrite changed content",
              rw["entries"]["rewrite_changed_content"] is True)


def test_hashes_recorded_and_mismatch_detectable():
    with tempfile.TemporaryDirectory() as d:
        _on(d)
        SC.capture("evidence", "r4", None, packet_source="CONTENT")
        r = pathlib.Path(d) / "r4"
        ev = [json.loads(l) for l in (r / "manifest.jsonl").read_text().splitlines()][0]
        rec = ev["entries"]["source/packet_source.txt"]
        actual = SC._sha256((r / "source/packet_source.txt").read_text())
        check("hash recorded for each artifact", rec["sha256"] == actual)
        (r / "source/packet_source.txt").write_text("TAMPERED")
        check("hash mismatch detectable after tampering",
              SC._sha256((r / "source/packet_source.txt").read_text()) != rec["sha256"])


def test_incomplete_bundle_detectable():
    with tempfile.TemporaryDirectory() as d:
        _on(d)
        SC.capture("evidence", "r5", None, packet_source="X")   # no seal
        check("bundle without COMPLETE is detectable as incomplete",
              not (pathlib.Path(d) / "r5" / "COMPLETE").exists())
        SC.seal("r5", None)
        check("sealed bundle is detectable as complete",
              (pathlib.Path(d) / "r5" / "COMPLETE").exists())


def test_no_secrets_persisted():
    with tempfile.TemporaryDirectory() as d:
        _on(d)
        SC.capture("evidence", "r6", None, packet_source="key material: OPENROUTER api_key=sk-abc123")
        r = pathlib.Path(d) / "r6"
        check("secret-bearing artifact refused, not written",
              not (r / "source/packet_source.txt").exists())
        ev = [json.loads(l) for l in (r / "manifest.jsonl").read_text().splitlines()][0]
        check("refusal recorded in manifest",
              ev["entries"]["source/packet_source.txt"]["status"] == "REFUSED_POSSIBLE_SECRET")
        blob = "\n".join(p.read_text(errors="ignore") for p in r.rglob("*") if p.is_file())
        check("no secret value anywhere in the bundle", "sk-abc123" not in blob)


def test_capture_failure_never_raises():
    class Boom:
        def get(self, *a, **k):
            raise RuntimeError("boom")

    with tempfile.TemporaryDirectory() as d:
        _on(d)
        # unserialisable payload + a bad root, both must be swallowed
        SC.capture("evidence", "r7", None, evidence_packet=Boom())
        os.environ[SC.ENV_ROOT] = "/proc/definitely/not/writable/xyz"
        SC.capture("evidence", "r8", None, packet_source="X")
        SC.seal("r8", None)
        check("capture failure is swallowed, never raised", True)
        os.environ[SC.ENV_ROOT] = d
    check("unknown event is a no-op", SC.capture("nope", "r9", None) is None)
    check("missing run_id is a no-op", SC.capture("evidence", None, None) is None)


def test_no_db_publication_or_network_in_capture_code():
    """Scan executable code only -- identifiers, imports, non-docstring literals."""
    tree = ast.parse((HERE / "shadow_capture.py").read_text())
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
    src = "\n".join(toks)
    for banned, label in [("sqlite3", "no sqlite3 in capture code"),
                          ("_posts", "no _posts write in capture code"),
                          ("_drafts", "no _drafts write in capture code"),
                          ("commit_to_git", "no publication call in capture code"),
                          ("subprocess", "no subprocess in capture code"),
                          ("requests", "no network client in capture code"),
                          ("urllib", "no urllib in capture code"),
                          ("socket", "no socket in capture code")]:
        check(label, banned not in src, "found %r" % banned)


BASELINE = "8af3622"   # frozen production baseline this patch must remain additive against


def test_hooks_are_additive_only():
    """The CAPTURE patch must add capture lines and delete none.

    Measured on capture lines specifically, not on generate.py's total line
    count. The original whole-file budget stopped being meaningful once
    generate.py legitimately carried a second, unrelated feature
    (SOURCE_ACQUISITION_RETRY_V1, 2026-08-23) -- a total-lines assertion would
    then fail for reasons that have nothing to do with observability, which is
    what this test exists to protect. The invariant itself is unchanged and is
    now checked directly: no line mentioning the capture sidecar is ever
    removed, and the hooks stay a small addition.
    """
    import subprocess  # test-only; not in the capture module
    out = subprocess.run(["git", "diff", "-U0", BASELINE, "--",
                          "automation/orchestrator/generate.py"],
                         cwd=str(HERE.parent), capture_output=True, text=True).stdout
    if not out.strip():
        check("generate.py diff vs baseline visible", False, "no diff vs %s" % BASELINE); return
    tokens = ("_shadow_capture", "_shadow_seal", "shadow_capture", "_capture_run_id")
    added = [l for l in out.splitlines()
             if l.startswith("+") and not l.startswith("+++") and any(t in l for t in tokens)]
    removed = [l for l in out.splitlines()
               if l.startswith("-") and not l.startswith("---") and any(t in l for t in tokens)]
    check("no capture line is deleted vs baseline", removed == [],
          "removed=%s" % removed[:3])
    check("capture hooks remain a small addition (<60 capture lines)",
          len(added) < 60, "added=%d capture lines" % len(added))
    check("the capture hooks are actually present", len(added) >= 5,
          "added=%d" % len(added))


def test_process_signals_propagate():
    """SystemExit / KeyboardInterrupt must NOT be swallowed by the sidecar."""
    import tempfile as _tf
    orig = SC._write
    for exc_type in (KeyboardInterrupt, SystemExit):
        def boom(*a, **k):
            raise exc_type()
        SC._write = boom
        try:
            with _tf.TemporaryDirectory() as d:
                _on(d)
                try:
                    SC.capture("evidence", "sig", None, packet_source="X")
                    check("%s propagates (not swallowed)" % exc_type.__name__, False, "swallowed")
                except exc_type:
                    check("%s propagates (not swallowed)" % exc_type.__name__, True)
        finally:
            SC._write = orig
    # and an ordinary error is still swallowed
    def boom_ordinary(*a, **k):
        raise RuntimeError("disk on fire")
    SC._write = boom_ordinary
    try:
        with _tf.TemporaryDirectory() as d:
            _on(d)
            SC.capture("evidence", "ord", None, packet_source="X")
            check("ordinary Exception still swallowed", True)
    except Exception as e:
        check("ordinary Exception still swallowed", False, e)
    finally:
        SC._write = orig



# ------------------------------------------------------------------ capture contract v0.1
# Regression tests for the exact failure that invalidated the 2026-08-21 run (bundle
# 20260821T070006Z-647ffe6d): the writer was Opus, so the non-Opus `rewrite` hook was
# correctly skipped, but _fable_polish_rewrite and the persona-biography editorial pass
# then changed the content with nothing observing them -- leaving the bundle with no
# representation of what actually shipped (5450 captured chars vs 6391 persisted).

_FM = "---\nlayout: post\ntitle: \"T\"\nauthor: \"Maya Flux\"\n---\n\n"


def _final_body_of(persisted):
    """The same frontmatter strip generate.py's final_output hook performs."""
    body = persisted
    if persisted and persisted.startswith("---"):
        end = persisted.find("\n---\n", 3)
        if end != -1:
            body = persisted[end + 5:].lstrip("\n")
    return body


def test_v01_opus_path_polish_mutates_but_final_output_still_captured():
    """Writer=Opus, non-Opus rewrite skipped, polish DOES change content."""
    with tempfile.TemporaryDirectory() as d:
        _on(d)
        r = "v01a"
        raw_writer = "TITLE: T\n\nthe original opus draft body.\n"
        after_polish = "the polished body, materially different and longer.\n"
        persisted = _FM + after_polish

        SC.capture("writer", r, None, writer_prompt="P", raw_writer_output=raw_writer,
                   writer_meta={"model": "anthropic/claude-opus-4.8"})
        # the Opus branch: persona pass ran, polish executed, NO non-Opus rewrite
        SC.capture("persona_biography_pass", r, None, branch="opus",
                   pre_content=raw_writer, post_content=after_polish,
                   reviewer_ran=True, executor_ran=True)
        SC.capture("fable_polish", r, None, branch="opus",
                   pre_polish=raw_writer, post_polish=after_polish)
        SC.capture("final_output", r, None, final_body=_final_body_of(persisted),
                   persisted_article=persisted, persisted_path="/x/_drafts/a.md",
                   stages={"persona_biography_pass": True, "fable_polish": True,
                           "non_opus_rewrite": False})
        SC.capture("disposition", r, None, disposition="draft", slug="a")
        SC.seal(r)

        b = pathlib.Path(d) / r
        events = [json.loads(l)["event"] for l in open(b / "manifest.jsonl")]
        check("v0.1 opus path: final_output event captured", "final_output" in events)
        check("v0.1 opus path: non-Opus rewrite correctly absent", "rewrite" not in events)
        check("v0.1 opus path: fable_polish observable", "fable_polish" in events)
        check("v0.1 opus path: persona pass observable", "persona_biography_pass" in events)

        fo = (b / "final" / "final_output.md").read_text()
        check("FINAL_OUTPUT equals the final persisted article body",
              fo == _final_body_of(persisted), "got %r" % fo[:60])
        check("FINAL_OUTPUT is NOT the raw writer output (the v0 bug)", fo != raw_writer)
        check("persisted article captured verbatim",
              (b / "final" / "persisted_article.md").read_text() == persisted)

        meta = json.loads((b / "final" / "final_output_meta.json").read_text())
        check("final_output records which stages ran",
              meta["stages_ran"] == {"persona_biography_pass": True, "fable_polish": True,
                                     "non_opus_rewrite": False}, meta["stages_ran"])
        pol = json.loads((b / "legacy" / "fable_polish_opus.json").read_text())
        check("fable_polish records a real content change", pol["changed_content"] is True)
        check("sealed bundle carries the v0.1 capture contract",
              json.loads((b / "COMPLETE").read_text())["capture_contract"] == "phase2-capture-v0.1")


def test_v01_no_post_writer_transformation_still_has_final_output():
    """Nothing mutates after the writer -- final_output must STILL exist."""
    with tempfile.TemporaryDirectory() as d:
        _on(d)
        r = "v01b"
        body = "an untouched draft body.\n"
        persisted = _FM + body
        SC.capture("writer", r, None, raw_writer_output=body)
        SC.capture("final_output", r, None, final_body=_final_body_of(persisted),
                   persisted_article=persisted, persisted_path="/x/_drafts/b.md",
                   stages={"persona_biography_pass": False, "fable_polish": False,
                           "non_opus_rewrite": False})
        SC.capture("disposition", r, None, disposition="draft", slug="b")
        SC.seal(r)
        b = pathlib.Path(d) / r
        events = [json.loads(l)["event"] for l in open(b / "manifest.jsonl")]
        check("no-transformation run still captures final_output", "final_output" in events)
        check("no inapplicable transformation events are required",
              "fable_polish" not in events and "persona_biography_pass" not in events
              and "rewrite" not in events)
        check("FINAL_OUTPUT equals the body even when nothing mutated",
              (b / "final" / "final_output.md").read_text() == body)


def test_v01_missing_final_output_is_detectable():
    """A v0-shaped bundle (no final_output) must fail the contract check."""
    with tempfile.TemporaryDirectory() as d:
        _on(d)
        r = "v01c"
        SC.capture("evidence", r, None, packet_source="s")
        SC.capture("commission", r, None, commission_input={"x": 1})
        SC.capture("writer", r, None, raw_writer_output="w")
        SC.capture("disposition", r, None, disposition="draft", slug="c")
        SC.seal(r)
        b = pathlib.Path(d) / r
        events = set(json.loads(l)["event"] for l in open(b / "manifest.jsonl"))
        missing = [e for e in SC.REQUIRED_EVENTS if e not in events]
        check("v0-shaped bundle is detected as contract-incomplete", missing == ["final_output"],
              "missing=%s" % missing)
        check("COMPLETE marker alone does NOT imply contract completeness",
              (b / "COMPLETE").exists() and bool(missing))


def test_v01_default_off_covers_new_events():
    """Every new v0.1 entry point must remain a no-op with the flag unset."""
    with tempfile.TemporaryDirectory() as d:
        os.environ[SC.ENV_ROOT] = str(d)
        _off()
        for ev, kw in (("final_output", {"final_body": "x", "persisted_article": "y"}),
                       ("persona_biography_pass", {"branch": "opus", "pre_content": "a",
                                                   "post_content": "b"}),
                       ("fable_polish", {"branch": "opus", "pre_polish": "a", "post_polish": "b"})):
            SC.capture(ev, "off1", None, **kw)
        SC.seal("off1")
        check("new v0.1 events write nothing when capture is OFF",
              not any(pathlib.Path(d).rglob("*")), sorted(str(x) for x in pathlib.Path(d).rglob("*")))


def test_v01_final_output_hook_is_structurally_unconditional():
    """Source-level: the hook must not sit inside is_opus / rewrite / any branch.

    This is the test that would have caught the v0 bug before a live run: the `rewrite`
    hook is nested inside `if not is_opus:`, so it can never fire on the normal path.
    final_output must sit at the same block depth as the disposition capture, which is
    known-unconditional, and must come after the writer capture.
    """
    src = (HERE / "orchestrator" / "generate.py").read_text()
    lines = src.splitlines()

    def indent_of(needle):
        for i, l in enumerate(lines):
            if needle in l:
                return i, len(l) - len(l.lstrip())
        return None, None

    i_writer, _ = indent_of('_shadow_capture("writer"')
    i_final, ind_final = indent_of('_shadow_capture("final_output"')
    i_disp, ind_disp = indent_of('_shadow_capture("disposition"')
    i_rew, ind_rew = indent_of('_shadow_capture("rewrite"')

    check("final_output hook exists in generate.py", i_final is not None)
    check("final_output is at the same block depth as disposition (unconditional)",
          ind_final == ind_disp, "final=%s disposition=%s" % (ind_final, ind_disp))
    check("final_output is strictly deeper-nested than nothing above it, unlike rewrite",
          ind_rew is not None and ind_rew > ind_disp,
          "rewrite=%s disposition=%s" % (ind_rew, ind_disp))
    check("final_output comes after the writer capture", i_writer < i_final)
    check("final_output comes before the disposition capture", i_final < i_disp)

    # no enclosing `if` between the last unconditional statement depth and the hook
    enclosing = [l.strip() for l in lines[max(0, i_final - 40):i_final]
                 if l.strip().startswith(("if ", "elif ", "else:")) and
                 (len(l) - len(l.lstrip())) < ind_final]
    check("no shallower conditional encloses the final_output hook", enclosing == [],
          "enclosing=%s" % enclosing[:3])


def main():
    for fn in [test_default_off, test_flag_on_writes_only_capture_artifacts,
               test_source_representations_preserved, test_writer_visible_evidence_and_raw_output,
               test_hashes_recorded_and_mismatch_detectable, test_incomplete_bundle_detectable,
               test_no_secrets_persisted, test_capture_failure_never_raises,
               test_no_db_publication_or_network_in_capture_code, test_hooks_are_additive_only,
               test_process_signals_propagate,
               test_v01_opus_path_polish_mutates_but_final_output_still_captured,
               test_v01_no_post_writer_transformation_still_has_final_output,
               test_v01_missing_final_output_is_detectable,
               test_v01_default_off_covers_new_events,
               test_v01_final_output_hook_is_structurally_unconditional]:
        print("\n" + fn.__name__)
        fn()
    _off()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL CAPTURE SAFETY TESTS PASSED")


if __name__ == "__main__":
    main()
