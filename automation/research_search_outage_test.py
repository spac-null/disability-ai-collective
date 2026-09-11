#!/usr/bin/env python3
"""research_search_outage_test.py -- a total search-provider outage fails closed.

`research()`'s own docstring already promises: "Raises ResearchError on a
provider/transport failure so the caller can fail closed; it never returns a pack it
could not actually build." The scoped-query loop did not keep that promise: a
ResearchError from every single query was caught, appended to a diagnostic `failures`
list, and swallowed -- leaving `candidates` empty exactly as it would be on an
ordinary thin day, so the sufficiency verdict downstream reported
HOLD_INSUFFICIENT_RESEARCH (an editorial "we looked and found too little" verdict) for
what was actually zero successful search calls.

A single failing query alongside a successful one is ordinary and must NOT escalate --
only a search path that never ran at all.

Stdlib only, no network.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import research as RS                              # noqa: E402
from new_engine_v1 import contracts as C                              # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + str(detail)) if detail else ""))
    if not cond:
        FAILURES.append(label)


_ANCHOR_TEXT = ("A museum opens a retrospective of an artist's fifty-year practice, "
                "drawn from a private archive.") * 3
ANCHOR = {"url": "https://example.org/anchor", "text": _ANCHOR_TEXT,
          "sha256": C.sha256_text(_ANCHOR_TEXT), "title": "Retrospective",
          "publisher": "example.org", "accessed_at": "2026-09-11T00:00:00Z",
          "fetch_status": "ok", "content_length": len(_ANCHOR_TEXT)}


class Prov:
    """Scripted scope reply naming two search queries; nothing else is called."""

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                deadline=None):
        body = {"subject": "the retrospective", "queries": ["q1", "q2"],
               "anchor_kind": "news_report", "anchor_subject_words": 120,
               "questions": [], "named_entities": ["Artist"]}

        class R:
            text = json.dumps(body)

            def identity(self_):
                return {"provider": "scripted"}
        return R()


def _run(search_fn):
    real_search, real_fetch = RS.search_urls, RS.fetch_source
    RS.search_urls = search_fn
    RS.fetch_source = lambda url, **k: {"url": url, "status": "http_404", "text": ""}
    try:
        return RS.research(Prov(), anchor=ANCHOR, now_iso="2026-09-11T00:00:00Z",
                           api_key="k")
    finally:
        RS.search_urls, RS.fetch_source = real_search, real_fetch


def test_every_query_failing_technically_raises_rather_than_returns_a_pack():
    def always_boom(q, **k):
        raise RS.ResearchError("search failed: 429 rate limited")

    raised = False
    try:
        _run(always_boom)
    except RS.ResearchError as e:
        raised = True
        check("the error names the total failure, not one query's wording",
              "every scoped search query failed technically" in str(e), str(e))
    check("a total search outage raises ResearchError rather than returning a pack",
          raised, "no exception was raised")


def test_one_failing_query_beside_a_successful_one_is_ordinary():
    calls = {"n": 0}

    def half_boom(q, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RS.ResearchError("search failed: transient 500")
        return ["https://example.org/found"]

    pack = None
    threw = False
    try:
        pack = _run(half_boom)
    except RS.ResearchError:
        threw = True
    check("one failing query beside a successful one does not raise",
          not threw and pack is not None, pack)


def main() -> int:
    for fn in (test_every_query_failing_technically_raises_rather_than_returns_a_pack,
               test_one_failing_query_beside_a_successful_one_is_ordinary):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL RESEARCH SEARCH-OUTAGE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
