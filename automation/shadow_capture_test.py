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
    """The generate.py patch must add lines and delete none, measured against the
    production baseline -- not against HEAD, which is empty once the patch is committed."""
    import subprocess  # test-only; not in the capture module
    out = subprocess.run(["git", "diff", "--numstat", BASELINE, "--", "automation/orchestrator/generate.py"],
                         cwd=str(HERE.parent), capture_output=True, text=True).stdout.strip()
    if not out:
        check("generate.py diff vs baseline visible", False, "no diff vs %s" % BASELINE); return
    added, deleted, _ = out.split(None, 2)
    check("generate.py patch deletes no lines vs baseline", deleted == "0", "deleted=%s" % deleted)
    check("generate.py patch is small (<80 added lines)", int(added) < 80, "added=%s" % added)


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


def main():
    for fn in [test_default_off, test_flag_on_writes_only_capture_artifacts,
               test_source_representations_preserved, test_writer_visible_evidence_and_raw_output,
               test_hashes_recorded_and_mismatch_detectable, test_incomplete_bundle_detectable,
               test_no_secrets_persisted, test_capture_failure_never_raises,
               test_no_db_publication_or_network_in_capture_code, test_hooks_are_additive_only,
               test_process_signals_propagate]:
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
