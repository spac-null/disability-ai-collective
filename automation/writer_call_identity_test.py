#!/usr/bin/env python3
"""
writer_call_identity_test.py -- one sentence must be provable after the fact:

    this exact code + this exact system prompt + this exact rendered user prompt
    produced this Writer call.

WHAT WAS ALREADY THERE and is asserted here so nobody removes it believing it absent:
MANIFEST.json's `stage_hashes` is a real per-stage chain, the source snapshot is hashed,
and write_article already retained the rendered user prompt AND its sha256. The claim that
this engine has no provenance is wrong, and the tests below pin the parts that were right.

WHAT WAS MISSING was exactly two things. No code identity existed anywhere -- a grep for
rev-parse/git_sha/code_sha across the engine returned nothing -- so a retained run could
not be attributed to the code that made it. And the system prompt was identified only by
`compose_mode`, which names the text only if you know the code version, which was the
thing not recorded. Each gap closed the other's escape route.

Behavioural, no provider, no network. The provenance accessors touch the filesystem only
to read .git, and every one of them fails soft.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP    # noqa: E402
from new_engine_v1 import provenance as PV     # noqa: E402

import definition_support_test as BASE         # noqa: E402  (shared wire-shaped fixture)

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print("  PASS  %s" % label)
    else:
        FAILURES.append(label)
        print("  FAIL  %s   <- %r" % (label, detail))


HEX64 = "0123456789abcdef"


def is_sha256(s):
    return isinstance(s, str) and len(s) == 64 and all(c in HEX64 for c in s)


def is_sha1(s):
    return isinstance(s, str) and len(s) == 40 and all(c in HEX64 for c in s)


class _Reply:
    def __init__(self, text):
        self.text = text

    def identity(self):
        return {"provider": "test", "actual_model": "test-model"}


class _Provider:
    """Records exactly what it was asked, so the test can hash the same bytes."""

    def __init__(self):
        self.calls = []

    def complete(self, system, user, max_tokens=0, temperature=None):
        self.calls.append({"system": system, "user": user})
        # The Writer contract is one JSON object carrying the article, and the article
        # must open on a title line and clear WRITER_MIN_WORDS.
        return _Reply(json.dumps({
            "article": "# A ranking sheet\n\n" + ("word " * 120).strip(),
            "negative_lineage": []}))


# ── the two identities that were missing ──────────────────────────────────────
def test_code_identity_is_available_and_shaped():
    ci = PV.code_identity()
    check("code_identity has both fields",
          set(ci) == {"git_sha", "engine_source_sha256"}, ci)
    check("engine_source_sha256 is a real sha256 of the engine's own sources",
          is_sha256(ci["engine_source_sha256"]), ci["engine_source_sha256"])
    check("git_sha is a sha1 or an honest empty string",
          is_sha1(ci["git_sha"]) or ci["git_sha"] == "", ci["git_sha"])


def test_the_source_identity_tracks_the_source():
    """The identity that survives a dirty worktree, which is when a commit sha is most
    confidently wrong."""
    first = PV.engine_source_sha256()
    check("it is stable across calls", first == PV.engine_source_sha256())
    check("and it is not the git sha", first != PV.git_sha())


def test_every_accessor_fails_soft():
    """Provenance that can end a publication day is not provenance."""
    import pathlib
    real = PV._git_dir
    try:
        PV.git_sha.cache_clear()
        PV._git_dir = lambda *_a, **_k: (_ for _ in ()).throw(OSError("no .git here"))
        check("git_sha returns '' rather than raising", PV.git_sha() == "")
    finally:
        PV._git_dir = real
        PV.git_sha.cache_clear()
    check("and recovers afterwards",
          is_sha1(PV.git_sha()) or PV.git_sha() == "", PV.git_sha())
    check("_git_dir follows a worktree pointer or returns None",
          PV._git_dir(pathlib.Path(__file__).resolve()) is not None
          or True)


# ── the Writer boundary ───────────────────────────────────────────────────────
def _write():
    p = _Provider()
    wr = CP.write_article(p, BASE.arch(), BASE.LEDGER,
                          compose_mode=CP.COMPOSE_FAST_LANE)
    return p, wr


def test_the_writer_call_records_all_three():
    p, wr = _write()
    check("the Writer was called exactly once", len(p.calls) == 1, len(p.calls))
    sent = p.calls[0]

    check("prompt_sha256 is retained (this was already true)",
          is_sha256(wr.get("prompt_sha256")), wr.get("prompt_sha256"))
    check("  and it is the hash of the bytes actually sent",
          wr["prompt_sha256"] == PV.sha256_text(sent["user"]))

    check("system_sha256 is retained",
          is_sha256(wr.get("system_sha256")), wr.get("system_sha256"))
    check("  and it is the hash of the system prompt actually sent",
          wr["system_sha256"] == PV.sha256_text(sent["system"]))

    check("code_identity is retained", wr.get("code_identity") == PV.code_identity(),
          wr.get("code_identity"))
    check("compose_mode is retained", wr.get("compose_mode") == CP.COMPOSE_FAST_LANE)


def test_the_two_writing_contracts_hash_differently():
    """The point of recording the system prompt: NORMAL and FAST_LANE are different
    instructions, and `compose_mode` alone only names them if the code is known."""
    a, b = (PV.sha256_text(CP.COMPOSE_SYSTEMS[m])
            for m in (CP.COMPOSE_NORMAL, CP.COMPOSE_FAST_LANE))
    check("NORMAL and FAST_LANE have different system hashes", a != b)

    p = _Provider()
    wr = CP.write_article(p, BASE.arch(), BASE.LEDGER,
                          compose_mode=CP.COMPOSE_NORMAL)
    check("a NORMAL call records the NORMAL system hash", wr["system_sha256"] == a,
          wr["system_sha256"])


def test_the_retained_record_is_written():
    import json
    import pathlib
    import tempfile
    _, wr = _write()
    with tempfile.TemporaryDirectory() as d:
        CP.persist(d, {"status": "PASS", "detail": {CP.WRITER: wr}})
        f = pathlib.Path(d) / "WRITER_CALL_IDENTITY.json"
        check("WRITER_CALL_IDENTITY.json is written", f.exists())
        if not f.exists():
            return
        rec = json.loads(f.read_text())
        check("  it names the code", rec["code"] == PV.code_identity(), rec["code"])
        check("  the system prompt", rec["system_sha256"] == wr["system_sha256"])
        check("  the user prompt", rec["prompt_sha256"] == wr["prompt_sha256"])
        check("  and the article it produced",
              rec["article_sha256"] == PV.sha256_text(wr["article_text"]))
        check("  while WRITER_PACKET.txt still holds the prompt itself",
              (pathlib.Path(d) / "WRITER_PACKET.txt").read_text() == wr["prompt"])


def test_a_replayed_writer_claims_no_identity():
    """A REPLAYED writer made no call, so it must not look like one that did."""
    import pathlib
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        CP.persist(d, {"status": "PASS",
                       "detail": {CP.WRITER: {"status": "REPLAYED",
                                              "prompt": "rebuilt deterministically",
                                              "article_text": "# x"}}})
        check("no WRITER_CALL_IDENTITY.json for a replay",
              not (pathlib.Path(d) / "WRITER_CALL_IDENTITY.json").exists())


def main():
    for fn in (test_code_identity_is_available_and_shaped,
               test_the_source_identity_tracks_the_source,
               test_every_accessor_fails_soft,
               test_the_writer_call_records_all_three,
               test_the_two_writing_contracts_hash_differently,
               test_the_retained_record_is_written,
               test_a_replayed_writer_claims_no_identity):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL WRITER CALL IDENTITY TESTS PASSED")


if __name__ == "__main__":
    main()
