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


# ── >20K boundary fixtures (S2A semantics-check follow-up) ─────────────────
#
# CORRECTED CLASSIFICATION: this is S2 (an evidence-based raised static cap),
# NOT S3. Audited directly: fetch_source_article's `text = self.
# _extract_paragraphs(html)` is the only place the full, unsliced extraction
# ever exists -- a local variable, never cached, never hashed, never
# returned. `return text[:max_chars]` means everything downstream (the
# per-run cache, evidence_packet.source_text, source_hash,
# evidence_packet_hash, what Fable/the writer receive) operates on the
# ALREADY-SLICED text only. There is no separate canonical full-source
# representation anywhere in this pipeline. The earlier report's "S3
# realized as S1-in-practice" framing was wrong and is corrected here.
#
# What these fixtures answer precisely (per the semantics-check instructions):
#   - what is stored canonically -> only the <=20000-char slice
#   - what is hashed -> only the <=20000-char slice (source_hash/
#     evidence_packet_hash)
#   - what reaches Fable / the writer -> the same <=20000-char slice, both
#     receive the identical evidence_packet.source_text
#   - can evidence after 20k disappear silently -> the MATERIAL still
#     disappears (real, not fixed by this pass) -- but no longer SILENTLY:
#     source_truncated=True plus the new source_original_length_chars (real
#     number, when discovery.py's fetch captured it) discloses exactly how
#     much and lets a consumer detect it deterministically
#   - does any metadata indicate truncation -> yes, both fields above,
#     already threaded through validate_brief's own stamping with zero
#     changes needed there

def _fixture_of_length(n, marker=None, marker_at=None):
    """Build an n-char synthetic source. If marker/marker_at given, inserts
    the marker text at that character offset (padding around it), so a
    fixture's critical content sits at a precise, verifiable position."""
    if marker is None:
        return "x" * n
    before = "a" * marker_at
    after = "b" * (n - marker_at - len(marker))
    return before + marker + after


def case_A_19999_chars_under_cap_not_truncated():
    text = _fixture_of_length(19999)
    packet = build_evidence_packet(text, source_max_chars=_SOURCE_TEXT_MAX_CHARS, source_origin="fixture",
                                    source_original_length_chars=19999)
    check("A. 19,999-char source (just under the 20000 cap): source_truncated=False",
          packet["source_truncated"] is False)
    check("A. source_text stored in full, nothing cut", len(packet["source_text"]) == 19999)
    check("A. source_original_length_chars matches source_length_chars -- confirms "
          "nothing was actually lost",
          packet["source_original_length_chars"] == packet["source_length_chars"] == 19999)


def case_B_exactly_20000_chars_boundary():
    text = _fixture_of_length(20000)
    packet = build_evidence_packet(text, source_max_chars=_SOURCE_TEXT_MAX_CHARS, source_origin="fixture",
                                    source_original_length_chars=20000)
    check("B. exactly 20,000 chars: the existing >= heuristic conservatively "
          "flags source_truncated=True even though nothing was actually cut "
          "(pre-existing characteristic of this heuristic, unchanged by this pass)",
          packet["source_truncated"] is True)
    check("B. THE FIX: source_original_length_chars == source_length_chars "
          "disambiguates this exact case -- a consumer can now tell 'flagged "
          "truncated but actually complete' apart from a real cut, which was "
          "impossible before this pass (the field was always None)",
          packet["source_original_length_chars"] == packet["source_length_chars"] == 20000)


def case_C_20001_chars_one_over_cap():
    po, orch = _orch()
    text = _fixture_of_length(20001, marker="CRITICAL_EVIDENCE_AT_END", marker_at=19976)
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _fetch_url_html=lambda self, url: "<html>fake</html>",
        _extract_paragraphs=lambda self, html: text,
    )
    try:
        fetched = orch.get_source_text("https://example.org/c-fixture")
        original_length = orch.get_source_original_length("https://example.org/c-fixture")
    finally:
        restore()
    check("C. 20,001-char source: sliced to exactly 20000 chars", len(fetched) == 20000)
    check("C. THE FIX: get_source_original_length reports the true original "
          "length (20001), one more than what's stored", original_length == 20001)
    packet = build_evidence_packet(fetched, source_max_chars=_SOURCE_TEXT_MAX_CHARS,
                                    source_origin="fetched_article", source_original_length_chars=original_length)
    check("C. evidence_packet discloses exactly 1 char was cut (original_length - "
          "stored_length)", packet["source_original_length_chars"] - packet["source_length_chars"] == 1)
    check("C. source_truncated=True, correctly", packet["source_truncated"] is True)


def case_D_40000_chars_critical_evidence_after_20000_lost():
    po, orch = _orch()
    # Critical evidence placed at char 25000 -- well past the 20000 cap.
    text = _fixture_of_length(40000, marker="CRITICAL_TESTIMONY_HERE", marker_at=25000)
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _fetch_url_html=lambda self, url: "<html>fake</html>",
        _extract_paragraphs=lambda self, html: text,
    )
    try:
        fetched = orch.get_source_text("https://example.org/d-fixture")
        original_length = orch.get_source_original_length("https://example.org/d-fixture")
    finally:
        restore()
    check("D. 40,000-char source with evidence at char 25000: the evidence "
          "IS still genuinely lost -- this pass discloses truncation, it "
          "does not eliminate it (that would require true S3, deferred)",
          "CRITICAL_TESTIMONY_HERE" not in fetched)
    check("D. but the loss is no longer silent: get_source_original_length "
          "reports the true 40000-char length", original_length == 40000)
    packet = build_evidence_packet(fetched, source_max_chars=_SOURCE_TEXT_MAX_CHARS,
                                    source_origin="fetched_article", source_original_length_chars=original_length)
    check("D. evidence_packet lets a consumer compute exactly how much was "
          "cut (40000 - 20000 = 20000 chars silently-no-longer -- disclosed)",
          packet["source_original_length_chars"] - packet["source_length_chars"] == 20000)
    check("D. Fable and the writer both receive evidence_packet.source_text -- "
          "same, single, already-capped text; there is no separate 'canonical "
          "full source' either of them could fall back to",
          "CRITICAL_TESTIMONY_HERE" not in packet["source_text"])


if __name__ == "__main__":
    case_fixture_shape_is_correct()
    case_old_cap_would_have_dropped_late_testimony()
    case_current_constants_are_raised()
    case_fetch_source_article_preserves_late_testimony_with_new_cap()
    case_get_source_text_default_matches_new_cap()
    case_evidence_packet_built_with_new_cap_preserves_testimony()
    case_genuinely_oversized_source_still_gets_a_ceiling()
    case_A_19999_chars_under_cap_not_truncated()
    case_B_exactly_20000_chars_boundary()
    case_C_20001_chars_one_over_cap()
    case_D_40000_chars_critical_evidence_after_20000_lost()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
