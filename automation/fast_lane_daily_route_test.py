#!/usr/bin/env python3
"""Focused, offline regressions for the scheduled Fast Lane route."""
from __future__ import annotations

import inspect
import io
import json
import os
import pathlib
import sys
import tempfile
import types
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import new_engine_production as NEP                     # noqa: E402
import publish_best as PB                               # noqa: E402
from new_engine_v1 import composition as CP             # noqa: E402
from orchestrator.social import SocialMixin             # noqa: E402
import story_architecture_composition_test as FIX        # noqa: E402

FAILURES = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label
          + ("" if ok else "  " + repr(detail)))
    if not ok:
        FAILURES.append(label)


def test_mode_and_final_prose_mapping():
    check("default scheduled compose mode is unchanged",
          CP.scheduled_compose_mode({}) == CP.COMPOSE_NORMAL)
    check("explicit scheduled compose mode selects Fast Lane",
          CP.scheduled_compose_mode({"CRIPMINDS_FAST_LANE_COMPOSE": "1"})
          == CP.COMPOSE_FAST_LANE)
    check("normal Writer doctrine is byte-for-byte unchanged",
          CP.COMPOSE_SYSTEMS[CP.COMPOSE_NORMAL] == CP.WRITER_SYSTEM)
    check("Fast Lane doctrine is additive and mode-only",
          CP.COMPOSE_SYSTEMS[CP.COMPOSE_FAST_LANE].startswith(CP.WRITER_SYSTEM)
          and CP.FAST_LANE_WRITER_DELTA not in CP.COMPOSE_SYSTEMS[CP.COMPOSE_NORMAL])

    run_src = inspect.getsource(CP.run_story_architecture_composition)
    check("canonical architect remains the architecture producer",
          "architect(" in run_src)
    write_src = inspect.getsource(CP.write_article)
    check("canonical writer_packet remains the Writer input",
          "writer_packet(" in write_src)
    combined = run_src + write_src
    check("scheduled composition has no article-specific packet dependency",
          all(x not in combined for x in
              ("fast_lane_v1", "build_synthetic_arch", "asl_packet", "TD Snap")))
    cm = run_src.index("claim_map_article(")
    pkg = run_src.index("pkg = make_package(final)", cm)
    safety = run_src.index("record(SAFETY", pkg)
    grounding = run_src.index("record(GROUNDING", safety)
    fact = run_src.index("record(FACT_CHECK", grounding)
    check("Claim Mapper precedes package and factual gates",
          cm < pkg < safety < grounding < fact)

    changed = FIX.DRAFT.replace("The room was built from Himalayan salt bricks",
                                "The room was constructed from Himalayan salt bricks")
    seen = []
    original_scripted = FIX.Scripted
    original_mapper = CP.claim_map_article

    class PolishingScripted(original_scripted):
        def complete(self, system, user, **kw):
            if "the last writer to touch a finished" in system.lower():
                self.calls.append({"system": system, "user": user})
                return FIX.Reply(changed)
            return super().complete(system, user, **kw)

    def mapper(_provider, article, _ledger, _allowed, _status=None):
        seen.append(article)
        return [], [], 0, {"provider": "test"}

    FIX.Scripted = PolishingScripted
    CP.claim_map_article = mapper
    try:
        fast_provider, fast = FIX.run(FIX.full_script(), compose_mode=CP.COMPOSE_FAST_LANE)
        default_provider, default = FIX.run(FIX.full_script())
    finally:
        FIX.Scripted = original_scripted
        CP.claim_map_article = original_mapper

    check("Fast Lane composition passes the offline canonical fixture",
          fast["status"] == CP.PASS, fast.get("failure_reason"))
    check("Claim Mapper receives Prose Finish output, not Writer output",
          seen == [changed], seen)
    check("mapped SHA is the final article SHA",
          fast["detail"][CP.WRITER].get("claim_map_article_sha256")
          == fast["article_sha256"])
    with tempfile.TemporaryDirectory() as d:
        CP.persist(d, fast)
        retained = json.loads((pathlib.Path(d) / "CLAIM_MAP.json").read_text())
        check("Claim Map artifact retains exact final-prose SHA",
              retained["article_sha256"] == fast["article_sha256"])
    check("default composition never invokes Claim Mapper",
          len(seen) == 1 and default["status"] == CP.PASS,
          {"seen": len(seen), "status": default["status"]})
    fast_writer = next(c["system"] for c in fast_provider.calls
                       if "writing one finished article" in c["system"])
    normal_writer = next(c["system"] for c in default_provider.calls
                         if "writing one finished article" in c["system"])
    check("Fast Lane Writer call contains the doctrine",
          "IMPLEMENTATION_DETAILS_REQUIRE_DIRECT_LICENSE" in fast_writer)
    check("default Writer call does not contain the doctrine",
          "IMPLEMENTATION_DETAILS_REQUIRE_DIRECT_LICENSE" not in normal_writer)


class _Logger:
    def debug(self, *a, **k): pass
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass
    def error(self, *a, **k): pass


class _Social(SocialMixin):
    def __init__(self, root):
        self.repo_root = root
        self.assets_dir = root / "assets"
        self.assets_dir.mkdir()
        self.logger = _Logger()

    def _social_hook(self, *a, **k):
        raise AssertionError("post-gate social copy was regenerated")

    def _bsky_hook(self, *a, **k):
        raise AssertionError("post-gate social copy was regenerated")


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return self.payload


def test_validated_social_identity():
    hook = "EXACT validated package hook — unchanged."
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        social = _Social(root)
        social._store_pending_social("exact", "Title", "Maya Flux", social_hook=hook)
        marker = json.loads((root / "_social" / "exact.json").read_text())
        check("validated package social_hook is persisted exactly",
              marker["social_hook"] == hook)

        article = root / "2026-09-13-exact.md"
        article.write_text("---\ntitle: Title\n---\n\nBody long enough to describe.")
        captured = {}
        old_env = os.environ.copy()
        old_open = urllib.request.urlopen

        def fake_open(req, **_kw):
            url = req.full_url
            if "createSession" in url:
                return _Response({"accessJwt": "token", "did": "did:test"})
            if "createRecord" in url:
                captured["bluesky"] = json.loads(req.data)["record"]["text"]
                return _Response({"uri": "at://post"})
            if "/api/v1/statuses" in url:
                captured["mastodon"] = urllib.parse.parse_qs(
                    req.data.decode())["status"][0]
                return _Response({"url": "https://mastodon/post"})
            if "api.tumblr.com" in url:
                captured["tumblr"] = urllib.parse.parse_qs(
                    req.data.decode())["description"][0]
                return _Response({"response": {"id": "1"}})
            raise AssertionError(url)

        os.environ.update({
            "BSKY_HANDLE": "h", "BSKY_APP_PASSWORD": "p",
            "MASTODON_ACCESS_TOKEN": "m", "MASTODON_INSTANCE": "https://m.example",
            "TUMBLR_CONSUMER_KEY": "ck", "TUMBLR_CONSUMER_SECRET": "cs",
            "TUMBLR_ACCESS_TOKEN": "at", "TUMBLR_ACCESS_TOKEN_SECRET": "ats",
            "TUMBLR_BLOG": "blog", "SITE_URL": "https://cripminds.com",
        })
        urllib.request.urlopen = fake_open
        try:
            social.post_to_bluesky("Title", "Body", article, validated_hook=hook)
            social.post_to_mastodon("Title", "Body", article, validated_hook=hook)
            social.post_to_tumblr("Title", "Body", article, validated_hook=hook)
        finally:
            urllib.request.urlopen = old_open
            os.environ.clear()
            os.environ.update(old_env)

        check("Bluesky receives the exact validated hook",
              captured.get("bluesky", "").startswith(hook + "\n\n"), captured)
        check("Mastodon receives the exact validated hook",
              captured.get("mastodon", "").startswith(hook + "\n\n"), captured)
        check("Tumblr receives the exact validated hook",
              captured.get("tumblr") == hook, captured)


def test_dutch_tail_is_non_critical_and_ordered():
    src = inspect.getsource(PB.publish_candidate)
    check("successful English commit precedes social and Dutch",
          src.index("_commit_and_push") < src.index("_fire_pending_social")
          < src.index("_publish_dutch_translation"))

    calls = []
    tp = types.ModuleType("translate_publication")
    tp.REPO = pathlib.Path("original-translation-repo")
    tp.english_bundle = lambda p: calls.append("english_bundle") or {"article": "English"}
    tp.translate_bundle = lambda *a, **k: calls.append("translate_bundle") or {"article": "Dutch"}
    tp.fidelity_check = lambda *a, **k: calls.append("fidelity_check") or {"verdict": "PASS"}
    tp.write_translation = lambda *a, **k: calls.append("write_translation") or pathlib.Path("nl.md")
    tp.link_english = lambda *a, **k: calls.append("link_english")
    cp = types.ModuleType("claude_cli_provider")
    cp.ClaudeCLIProvider = lambda: object()
    old_tp = sys.modules.get("translate_publication")
    old_cp = sys.modules.get("claude_cli_provider")
    old_commit = PB._commit_and_push
    sys.modules["translate_publication"] = tp
    sys.modules["claude_cli_provider"] = cp
    PB._commit_and_push = lambda *a, **k: calls.append("commit_translation")
    try:
        PB._publish_dutch_translation(pathlib.Path("english.md"))
        check("successful English publication invokes existing Dutch flow",
              calls == ["english_bundle", "translate_bundle", "fidelity_check",
                        "write_translation", "link_english", "commit_translation"], calls)
        tp.translate_bundle = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("quota"))
        english = pathlib.Path(tempfile.mkstemp()[1])
        english.write_text("published English")
        PB._publish_dutch_translation(english)
        check("Dutch failure leaves published English bytes intact",
              english.read_text() == "published English")
        english.unlink()
    finally:
        PB._commit_and_push = old_commit
        if old_tp is None: sys.modules.pop("translate_publication", None)
        else: sys.modules["translate_publication"] = old_tp
        if old_cp is None: sys.modules.pop("claude_cli_provider", None)
        else: sys.modules["claude_cli_provider"] = old_cp


def test_runtime_wiring():
    prod = inspect.getsource(NEP.run_scheduled)
    check("production bridge receives the exact current run directory",
          "run_dir=root / run" in prod)
    check("validated social is stored before publication",
          prod.index("_store_pending_social") < prod.index("publish_if_eligible"))


def main():
    test_mode_and_final_prose_mapping()
    test_validated_social_identity()
    test_dutch_tail_is_non_critical_and_ordered()
    test_runtime_wiring()
    if FAILURES:
        print("%d failure(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("All Fast Lane daily-route tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
