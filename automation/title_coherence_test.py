#!/usr/bin/env python3
"""
title_coherence_test.py -- headline/article coherence, and the writer contract that
should have produced a headline in the first place.

Regression case is real: production-20260827T070010Z-fd846f06 inherited a Dezeen roundup
headline about a gravity-powered mountain trike onto an article written entirely about a
layered tactile exhibition system. No article-specific vocabulary is hard-coded here --
the fixtures are the real strings, but the check under test is generic.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import title_coherence as TC                                   # noqa: E402
from new_engine_v1 import contracts as C                       # noqa: E402
from new_engine_v1 import stages as S                          # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + detail))
    if not ok:
        FAILURES.append(label)


# The real 27 August case, trimmed to the paragraphs the check reads.
AUG27_BODY = """
Among the projects gathered from the University of Ljubljana's Academy of Fine Arts and
Design, one arrives dressed as a courtesy. Zoja Cepin's Multisensory Exhibition Experience
is described as a system that "makes artworks accessible beyond sight," developed through
interviews and testing with blind and partially sighted people.

Each booklet translates an artwork into three progressively detailed tactile layers,
allowing visitors to move from composition to key features at their own pace. The whole
comes first. Then the parts. Then the finer parts.

The standard gallery encounter assumes that meaning arrives all at once, at the display's
pace, through sight. The layered booklet refuses the all-at-once. It insists on a sequence
and hands the clock to the visitor, and in refusing it, the booklet names it. The
conventional encounter had a structure all along, but the speed of sight hid the assembly.
"""

AUG27_SOURCE_HEADLINE = ("Gravity-powered mountain trike among projects from the "
                         "University of Ljubljana")


def test_aug27_source_headline_is_rejected():
    a = TC.analyse(AUG27_SOURCE_HEADLINE, AUG27_BODY)
    check("27 Aug: source headline names terms the article never uses",
          a["stray_count"] >= 4, str(a))
    for term in ("gravity", "powered", "mountain", "trike"):
        check("27 Aug: %r flagged as stray" % term, term in a["stray"], str(a["stray"]))
    check("27 Aug: source headline is INCOHERENT for this body",
          TC.is_coherent(AUG27_SOURCE_HEADLINE, AUG27_BODY) is False)


def test_a_title_about_the_actual_subject_is_accepted():
    for good in ("The Tactile Booklet That Exposed What Galleries Assume",
                 "Three Tactile Layers, and the Gallery Assumption They Expose",
                 "What a Layered Booklet Reveals About the Pace of Looking"):
        check("coherent headline accepted: %r" % good[:40],
              TC.is_coherent(good, AUG27_BODY) is True,
              TC.describe(good, AUG27_BODY))


def test_check_is_generic_not_keyword_matched():
    """Same shape, unrelated subject: a roundup headline naming a different item."""
    body = ("The county replaced every bus shelter timetable with a screen. The screens "
            "show departures in a font too small to read from the bench, and go blank in "
            "direct sun. A printed timetable did neither.")
    check("unrelated roundup headline rejected",
          TC.is_coherent("Solar canopy wins prize among railway station designs", body)
          is False)
    check("headline about the actual subject accepted",
          TC.is_coherent("The Bus Shelter Screen That Goes Blank in Sunlight", body)
          is True)
    check("tolerates a couple of unmatched framing words",
          TC.is_coherent("The Bus Shelter Screen Nobody Anticipated", body) is True)
    check("empty/topic-free headline is not rejected here",
          TC.is_coherent("Of the and it", body) is True)
    check("inflection matches without a stemmer",
          TC.is_coherent("Screens, Timetables and Benches", body) is True)


# ── writer contract ───────────────────────────────────────────────────────────
def test_writer_is_asked_for_a_headline():
    wi = S.build_writer_input(
        {"motion": "m", "route": ["r"], "arrival": "a", "burden": "b",
         "target_words": [750, 950]},
        {"source_anchor_quote": "q", "what_becomes_knowable": "k",
         "grounding_boundaries": "g"},
        "source text", "0" * 64, "Maya Flux")
    p = wi["prompt_text"]
    check("writer is asked for a TITLE line", "TITLE: <headline>" in p)
    check("writer is told the source headline is not its headline",
          "provenance metadata, not yours" in p and "Do not copy it." in p)
    check("body-only instruction no longer forbids a title",
          "no title" not in p)
    check("word range is framed as an upper bound, not a quota",
          "never a quota" in p)


def test_prompt_carries_no_legacy_surface():
    """The contract validates WRITER_INPUT against 29 legacy markers -- one of which is
    a title-rule marker, so a headline instruction is exactly where this could regress."""
    wi = S.build_writer_input(
        {"motion": "m", "route": ["r"], "arrival": "a", "burden": "b",
         "target_words": [750, 950]},
        {"source_anchor_quote": "q", "what_becomes_knowable": "k",
         "grounding_boundaries": "g"},
        "source text", "0" * 64, "Maya Flux")
    hits = [m for m in C.LEGACY_PROMPT_MARKERS if m in wi["prompt_text"]]
    check("no legacy prompt marker present", hits == [], str(hits))
    C.validate(C.Artifact(stage=C.WRITER_INPUT, created_at="2026-08-27T00:00:00+00:00",
                          payload=wi))
    check("WRITER_INPUT still validates against the frozen contract", True)


def test_readability_doctrine_is_operational():
    d = S.PROSE_DOCTRINE
    for label, needle in (("concrete before abstract", "Concrete before abstract"),
                          ("say the point once", "Say the point once"),
                          ("restatement is not development", "is not development"),
                          ("one idea at a time", "one idea moving at a time"),
                          ("plain bridge to meaning", "plain sentence that does the explaining"),
                          ("no rereading", "need rereading"),
                          ("ordinary over specialist words", "ordinary word"),
                          ("metaphor kept selective", "used sparingly")):
        check("doctrine states: %s" % label, needle in d)
    check("doctrine keeps the no-end-summary rule", "do not summarise at the end" in d)


def test_title_is_split_off_the_body():
    t, b = S.split_title("TITLE: A Headline\n\nFirst paragraph of the article.")
    check("title parsed", t == "A Headline", repr(t))
    check("title removed from body", b == "First paragraph of the article.", repr(b))
    t2, b2 = S.split_title("No headline line here.\n\nSecond paragraph.")
    check("absent title tolerated", t2 == "")
    check("body returned unchanged when no title line",
          b2 == "No headline line here.\n\nSecond paragraph.")
    t3, b3 = S.split_title("  title :  Spaced And Lowercased  \n\nBody.")
    check("tolerant of spacing/case", t3 == "Spaced And Lowercased", repr(t3))
    check("body still clean", b3 == "Body.", repr(b3))


def main() -> None:
    for fn in (test_aug27_source_headline_is_rejected,
               test_a_title_about_the_actual_subject_is_accepted,
               test_check_is_generic_not_keyword_matched,
               test_writer_is_asked_for_a_headline,
               test_prompt_carries_no_legacy_surface,
               test_readability_doctrine_is_operational,
               test_title_is_split_off_the_body):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL TITLE-COHERENCE / READABILITY-CONTRACT TESTS PASSED")


if __name__ == "__main__":
    main()
