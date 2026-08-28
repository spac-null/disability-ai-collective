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
    check("doctrine gives a concrete deletion test for echo paragraphs",
          "delete it" in d and "makes the same point in different words" in d)
    check("doctrine forbids a preview of the arrival", "preview of it" in d)
    check("doctrine forbids a reprise after the arrival", "reprise" in d)
    check("doctrine bans stacked conceptual nouns and metaphors",
          "conceptual nouns and metaphors" in d)


def test_form_forbids_restatement_movements():
    f = S.FORM_SYSTEM
    check("form: no movement exists to restate the arrival",
          "No movement exists to restate the arrival" in f)
    check("form: names the jobs a route has to do",
          "establish the concrete subject" in f and "show how it works" in f
          and "mark what the source does and does not establish" in f)
    check("form: the jobs are NOT imposed as a template",
          "NOT a template" in f and "form follows material" in f)
    check("form: still says there is no house structure",
          "no house structure" in f)
    check("form: target_words is the smallest completing range",
          "smallest range in which this argument actually completes" in f)


def test_interpretation_may_not_widen_into_a_general_claim():
    """A reading of a design must not silently become an empirical claim about the
    world. The 27 Aug regression article said the booklet sequences composition then
    detail (grounded) and then that sight runs that same sequence too fast to notice
    (a claim about everyone, which the source cannot support)."""
    n = S._NO_FABRICATION
    check("boundary separates a reading from a finding about the world",
          "is not a finding about how the world works" in n)
    check("boundary names the widening failure mode",
          "widen" in n and "general truth" in n)
    check("boundary enumerates the domains it covers",
          all(w in n for w in ("cognition", "perception", "behaviour",
                               "institutions", "outcomes")))
    check("boundary gives the three permitted dispositions",
          "the source must support it" in n and "mark it as a reading" in n
          and "it must go" in n)
    for site in (S.WRITER_SYSTEM, S.build_writer_input(
            {"motion": "m", "route": ["r"], "arrival": "a", "burden": "b",
             "target_words": [650, 800]},
            {"source_anchor_quote": "q", "what_becomes_knowable": "k",
             "grounding_boundaries": "g"},
            "source text", "0" * 64, "Maya Flux")["prompt_text"]):
        check("rule reaches the writer", "is not a finding about how the world works" in site)


def test_writer_may_come_in_short():
    wi = S.build_writer_input(
        {"motion": "m", "route": ["r"], "arrival": "a", "burden": "b",
         "target_words": [750, 950]},
        {"source_anchor_quote": "q", "what_becomes_knowable": "k",
         "grounding_boundaries": "g"},
        "source text", "0" * 64, "Maya Flux")
    p = wi["prompt_text"]
    check("under the range is stated to be a good outcome",
          "coming in under the range is a good outcome" in p)
    check("a shorter finished article is preferred to a longer repeating one",
          "beats a longer one that restates itself" in p)


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



def test_opening_states_why_this_is_worth_reading():
    """Owner reader review, 28 Aug: the article opened on a correct concrete
    description and still gave no reason to keep reading until paragraph three. The
    doctrine had the job buried inside the concrete-before-abstract rule; it is now
    its own instruction, with the three jobs named and no template attached."""
    d = S.PROSE_DOCTRINE
    check("opening names the concrete subject", "names the concrete subject" in d)
    check("opening says what is unusual about it",
          "what is unusual or particular about it" in d)
    check("opening says why the article is looking at it",
          "why this article is looking at it" in d)
    check("the jobs have a stated budget, not a pattern",
          "first two to four sentences" in d and "no set pattern" in d)
    check("reader must not wait until paragraph three or four",
          "third or fourth paragraph" in d)


def test_doctrine_attacks_sentence_density():
    """The dense sentences that still passed carried two or three abstractions each.
    The rule now names the construction to prefer and the one to break up."""
    d = S.PROSE_DOCTRINE
    check("one claim to a sentence", "One claim to a sentence" in d)
    check("concrete noun + active verb is the default build",
          "concrete noun and an active verb" in d)
    check("two ideas that both matter become two sentences",
          "write two sentences" in d)
    check("long multi-clause sentences are actively questioned",
          "Distrust any long sentence" in d)
    check("abstract nouns are replaced by the thing itself",
          "replaced by the thing itself" in d)
    check("no explanatory clause after the point is understood",
          "already understood" in d)
    check("no crude universal sentence-length limit is imposed",
          "words per sentence" not in d and "maximum of" not in d)


def test_doctrine_keeps_naming_the_object():
    """Repeated abstractions (sequence / encounter / reading order / variable) were
    the density's other half: the article stopped naming the booklet."""
    d = S.PROSE_DOCTRINE
    check("the object comes back with the argument", "bring the object back with it" in d)
    check("a conceptual noun may not stand in for it",
          "conceptual noun standing in for it" in d)
    check("drifting off the material is named as the failure",
          "drifted off the material" in d)


def test_qualification_stays_local_and_plain():
    """The evidence boundary must survive; the academic disclaimer paragraph should
    not. 28 Aug spent a six-sentence paragraph explaining what it was not claiming."""
    d = S.PROSE_DOCTRINE
    check("a limit is marked where the claim is made",
          "Mark a limit where the claim is made" in d)
    check("one plain statement, not a paragraph",
          "one plain statement" in d and "not worth a paragraph" in d)
    check("state the boundary, do not perform it", "do not perform it" in d)
    # The boundary itself is untouched: still binding, still reaching the writer.
    check("evidence boundary is still in force",
          "is not a finding about how the world works" in S._NO_FABRICATION)


def test_ending_stops_instead_of_reprising():
    """28 Aug stated its arrival in the penultimate paragraph and again as the last
    line. The doctrine said the arrival is stated once; nothing told the writer what
    to do INSTEAD of a closing paragraph."""
    d = S.PROSE_DOCTRINE
    check("when the point lands, the article is over", "the article is over" in d)
    check("the permitted alternative is genuinely new material",
          "add one genuinely new thing" in d)
    check("no closing paragraph written out of habit",
          "because articles are expected to have one" in d)
    check("never end by restating the arrival",
          "saying the arrival again in other words" in d)
    check("the original once-only rule is still there", "arrival is stated once" in d.lower()
          or "The arrival is stated once" in d)


def test_form_owns_the_vocabulary_the_writer_inherits():
    """Root cause of the abstract register: the writer is told to follow the form
    exactly, and the form arrived written in conceptual nouns."""
    f = S.FORM_SYSTEM
    check("form must be written in plain concrete language",
          "plain, concrete language" in f)
    check("form names what the writer inherits",
          "inherits your vocabulary" in f)
    check("the last movement IS the arrival", "the route IS the arrival" in f)
    check("no movement after the arrival", "Do not place a movement after it" in f)
    check("single-source honest default range is stated",
          "500 to 650 words" in f)
    check("a longer range still requires real material",
          "material you actually have" in f)


def test_writer_prompt_says_the_arrival_once():
    wi = S.build_writer_input(
        {"motion": "m", "route": ["establish", "develop", "arrive"], "arrival": "a",
         "burden": "b", "target_words": [500, 650]},
        {"source_anchor_quote": "q", "what_becomes_knowable": "k",
         "grounding_boundaries": "g"},
        "source text", "0" * 64, "Maya Flux")
    p = wi["prompt_text"]
    check("route-end and arrival are stated to be one act",
          "the same act, not two" in p)
    check("the writer is told to write it once and stop",
          "write it once, there, and stop" in p)
    check("the prompt still carries no legacy surface",
          not [m for m in C.LEGACY_PROMPT_MARKERS if m in p])


def main() -> None:
    for fn in (test_aug27_source_headline_is_rejected,
               test_a_title_about_the_actual_subject_is_accepted,
               test_check_is_generic_not_keyword_matched,
               test_writer_is_asked_for_a_headline,
               test_prompt_carries_no_legacy_surface,
               test_readability_doctrine_is_operational,
               test_form_forbids_restatement_movements,
               test_interpretation_may_not_widen_into_a_general_claim,
               test_writer_may_come_in_short,
               test_opening_states_why_this_is_worth_reading,
               test_doctrine_attacks_sentence_density,
               test_doctrine_keeps_naming_the_object,
               test_qualification_stays_local_and_plain,
               test_ending_stops_instead_of_reprising,
               test_form_owns_the_vocabulary_the_writer_inherits,
               test_writer_prompt_says_the_arrival_once,
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
