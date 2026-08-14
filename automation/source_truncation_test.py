#!/usr/bin/env python3
"""
source_truncation_test.py — regression suite for the source-packet
truncation closure (human-detail provenance + source-truncation audit,
2026-08-14).

Reproduces, with a synthetic fixture (not a real network fetch), the
confirmed defect: fetch_source_article's old 3000-char default silently
dropped any testimony/evidence appearing after character 3000 of the
extracted article -- a position-blind, first-N-characters slice with no
quote-awareness. Proves the fix (discovery.py's _SOURCE_TEXT_CACHE_MAX_CHARS
and generate.py's _SOURCE_TEXT_MAX_CHARS, both raised 3000/6000 -> 20000)
actually preserves testimony that the old cap would have destroyed, using
the real fetch_source_article method with only the network call
(_fetch_url_html) and HTML extraction (_extract_paragraphs) mocked --
everything downstream of those two calls is the real, unmodified code path.

Zero network, zero model calls.

USAGE: python3 automation/source_truncation_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from snapshot_test import _import_orchestrator, _patch_methods  # noqa: E402
from orchestrator.discovery import _SOURCE_TEXT_CACHE_MAX_CHARS  # noqa: E402
from orchestrator.generate import _SOURCE_TEXT_MAX_CHARS  # noqa: E402
from orchestrator.grounding import build_evidence_packet  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def _orch():
    po = _import_orchestrator()
    return po, po.ProductionOrchestrator()


_TESTIMONY_BEFORE_3000 = '"This system has never once worked for me," said Jordan Ellis, a caseworker.'
_TESTIMONY_AFTER_3000 = '"Nobody told us the office was closing until the day it happened," said Priya Nair, a former client.'

# Padding chosen so _TESTIMONY_BEFORE_3000 sits comfortably before char 3000
# and _TESTIMONY_AFTER_3000 sits comfortably after it -- confirmed by the
# assertions in case_fixture_shape_is_correct below, not assumed.
_FILLER_BEFORE = "General background context about the policy area. " * 40
_FILLER_MIDDLE = "More general background context, unrelated to any testimony. " * 80
_LONG_ARTICLE = _FILLER_BEFORE + _TESTIMONY_BEFORE_3000 + _FILLER_MIDDLE + _TESTIMONY_AFTER_3000


def case_fixture_shape_is_correct():
    before_pos = _LONG_ARTICLE.index(_TESTIMONY_BEFORE_3000)
    after_pos = _LONG_ARTICLE.index(_TESTIMONY_AFTER_3000)
    check("fixture: testimony-before sits before char 3000", before_pos < 3000)
    check("fixture: testimony-after sits after char 3000", after_pos > 3000)
    check("fixture: testimony-after sits before the new 20000-char ceiling",
          after_pos + len(_TESTIMONY_AFTER_3000) < 20000)


def case_old_cap_would_have_dropped_late_testimony():
    # Reproduces the OLD defect directly and mechanically: a plain first-N-
    # chars slice at the old default (3000) on the exact same extracted text.
    old_slice = _LONG_ARTICLE[:3000]
    check("OLD 3000-char slice: contains the early testimony",
          _TESTIMONY_BEFORE_3000 in old_slice)
    check("OLD 3000-char slice: DROPS the late testimony -- the confirmed defect",
          _TESTIMONY_AFTER_3000 not in old_slice)


def case_current_constants_are_raised():
    check("discovery.py's canonical cache ceiling raised to 20000 (was 6000, "
          "originally 3000)", _SOURCE_TEXT_CACHE_MAX_CHARS == 20000)
    check("generate.py's evidence_packet ceiling raised in lockstep to 20000 "
          "(was 3000)", _SOURCE_TEXT_MAX_CHARS == 20000)


def case_fetch_source_article_preserves_late_testimony_with_new_cap():
    po, orch = _orch()
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _fetch_url_html=lambda self, url: "<html>fake</html>",
        _extract_paragraphs=lambda self, html: _LONG_ARTICLE,
    )
    try:
        result = orch.fetch_source_article("https://example.org/article", max_chars=_SOURCE_TEXT_CACHE_MAX_CHARS)
    finally:
        restore()
    check("fetch_source_article with the NEW cap: preserves the early testimony",
          _TESTIMONY_BEFORE_3000 in result)
    check("fetch_source_article with the NEW cap: preserves the LATE testimony -- "
          "the defect this pass closes", _TESTIMONY_AFTER_3000 in result)


def case_get_source_text_default_matches_new_cap():
    po, orch = _orch()
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _fetch_url_html=lambda self, url: "<html>fake</html>",
        _extract_paragraphs=lambda self, html: _LONG_ARTICLE,
    )
    try:
        # No max_chars override -- exercises the REAL default generate.py's
        # call sites rely on (self.get_source_text(url, fallback_text=...)).
        result = orch.get_source_text("https://example.org/article2")
    finally:
        restore()
    check("get_source_text's own DEFAULT (no override, matching real generate.py "
          "call sites) preserves the late testimony too",
          _TESTIMONY_AFTER_3000 in result)


def case_evidence_packet_built_with_new_cap_preserves_testimony():
    packet = build_evidence_packet(_LONG_ARTICLE, source_max_chars=_SOURCE_TEXT_MAX_CHARS, source_origin="fixture")
    check("evidence_packet.source_text (what Fable and the writer actually "
          "receive) contains the early testimony",
          _TESTIMONY_BEFORE_3000 in packet["source_text"])
    check("evidence_packet.source_text contains the LATE testimony -- confirms "
          "the fix reaches all the way to what Fable/the writer see",
          _TESTIMONY_AFTER_3000 in packet["source_text"])
    check("evidence_packet correctly reports source_truncated=False for an "
          "article well under the new 20000-char ceiling",
          packet["source_truncated"] is False)


def case_genuinely_oversized_source_still_gets_a_ceiling():
    # The new cap is generous, not infinite. build_evidence_packet itself
    # never slices (it only flags source_truncated based on length -- the
    # actual slicing happens earlier, in fetch_source_article); the ceiling
    # is enforced there, so exercise that real call path, not
    # build_evidence_packet in isolation.
    po, orch = _orch()
    oversized = "word " * 10000  # ~50,000 chars, comfortably over the 20000 ceiling
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _fetch_url_html=lambda self, url: "<html>fake</html>",
        _extract_paragraphs=lambda self, html: oversized,
    )
    try:
        fetched = orch.fetch_source_article("https://example.org/huge", max_chars=_SOURCE_TEXT_CACHE_MAX_CHARS)
    finally:
        restore()
    check("a genuinely oversized source is still truncated at the new ceiling "
          "by fetch_source_article, not passed through unbounded",
          len(fetched) <= _SOURCE_TEXT_CACHE_MAX_CHARS)

    packet = build_evidence_packet(fetched, source_max_chars=_SOURCE_TEXT_MAX_CHARS, source_origin="fixture")
    check("evidence_packet built from the already-sliced text correctly reports "
          "source_truncated=True (honest flag, not a re-slice)",
          packet["source_truncated"] is True)


if __name__ == "__main__":
    case_fixture_shape_is_correct()
    case_old_cap_would_have_dropped_late_testimony()
    case_current_constants_are_raised()
    case_fetch_source_article_preserves_late_testimony_with_new_cap()
    case_get_source_text_default_matches_new_cap()
    case_evidence_packet_built_with_new_cap_preserves_testimony()
    case_genuinely_oversized_source_still_gets_a_ceiling()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
