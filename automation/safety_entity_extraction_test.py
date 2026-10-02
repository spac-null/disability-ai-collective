#!/usr/bin/env python3
"""safety_entity_extraction_test.py -- the two generic Safety entity-extraction defects
found by production-20260913T083824Z-f83f4b8a, and the guarantee that neither fix
weakened the screen.

That run committed to a story (Research PASS, Ledger PASS 133 facts, Worth PASS,
Architecture/Writer/Continuity/Prose Finish/Claim Mapper/Package all PASS) and was then
held at SAFETY on:

    NEW_UNSUPPORTED_FACTS ... entities=['Behind', 'Modern', 'Museum']

All three were false positives, from two independent and entirely generic defects:

  1. A SENTENCE CAN END INSIDE A QUOTATION MARK. The splitter's lookbehind required the
     character immediately before the whitespace to be `.!?`. In `... happy "future
     families." Behind the text is ...` the stop is followed by a closing quote, so no
     split happened, the rest of the article stayed in one 3,973-character segment, and
     an ordinary preposition opening the next sentence was scored as a name.

  2. THE LEDGER WAS NOT PART OF "APPROVED". The screen compared prose against the packet
     alone. The packet is the condensed subset given to the Writer; the frozen Ledger is
     what doctrine names as the source of factual permission. "San Francisco Museum of
     Modern Art" appears verbatim in three Ledger facts and nowhere in the packet render,
     so "Museum" and "Modern" blocked as inventions.

Neither fix is an allowlist. No token, publisher, institution or article is named in
either. The last two tests here are the ones that matter: a genuinely invented name and
a genuinely invented figure must still block.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import story as ST

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        FAILURES.append(name)
        print("  FAIL %s  %s" % (name, detail))


_LENS = {"verdict": ST.STRONG_INTERPRETIVE_LENS,
         "lens_claim": "A purchase is an event a means test can see.",
         "lens_evidence_ids": ["F01"]}


def _packet(*lines):
    """A real packet, built by the production builder rather than hand-shaped, so the
    approved surface under test is the one production actually renders."""
    facts = {"F%02d" % i: t for i, t in enumerate(lines, 1)}
    arch = {
        "article_type": ST.SHORT_NARRATIVE,
        "story_spine": "A drawing hung where it was bought.",
        "opening_object_or_event": "A drawing on a wall.",
        "reader_initial_state": "That a drawing was bought.",
        "beats": [{"beat_id": "B1", "happens": "the purchase",
                   "concrete_carrier": "the drawing", "facts_allowed": list(facts),
                   "concept_introduced": "", "why_reader_wants_next": "",
                   "must_not_say_yet": ""}],
        "turn": "The purchase is visible to something else.",
        "crip_turn": "A means test can see it.",
        "ending_move": "Return to the drawing.",
        "use_facts": list(facts),
        "use_quotes": [],
        "definitions": {},
        "prohibitions": ["Never use the first person."],
        "cut_evidence": [],
    }
    return ST.build_packet(arch, _LENS, facts)


def _ledger(*spans):
    return {"F%02d" % i: {"proposition": s, "support_span": s}
            for i, s in enumerate(spans, 1)}


# ── defect 1: a sentence ending inside a quotation mark ──────────────────────
def test_sentence_initial_after_a_closing_quote_is_not_an_entity():
    print("\n1. A capital opening a sentence after a closing quote is grammar, not a name")
    pk = _packet("The mural refers to a future city and to happy families.",
                 "The development stands nearby.")
    art = ('# T\n\nThe mural refers to a future city occupied by happy "future '
           'families." Behind the text is the development.\n')
    r = ST.factual_surface_audit(art, pk)
    check("'Behind' is no longer scored as an entity",
          "Behind" not in r["unapproved_entities"], r["unapproved_entities"])

    # Every closer that appears in ordinary prose, not just the straight double quote.
    for closer in ('"', "'", "”", "’", "»", ")", "]"):
        seg = 'He said it was over%s%s Afterwards nothing changed.' % (".", closer)
        ents = ST._entities(seg)
        check("  closer %r does not strand the next sentence" % closer,
              "Afterwards" not in ents, sorted(ents))

    # And a stop with no closer behaves exactly as it did before.
    check("a plain stop still splits",
          "Afterwards" not in ST._entities("It was over. Afterwards nothing changed."))
    check("the sentence-initial exemption is still position-based, not match-order",
          "Georgetown" in ST._entities("a visit to Georgetown."),
          sorted(ST._entities("a visit to Georgetown.")))


def test_the_sentence_initial_tradeoff_is_now_uniform():
    """WHAT THE FIX COSTS, pinned so nobody rediscovers it as a surprise.

    This screen has always exempted the first word of a sentence -- that is the whole
    point of `skip_sentence_initial`, and it means a name placed in that position is
    invisible to it, preposition or proper noun alike. The docstring accepts that
    tradeoff, and the module's own comment records where the cover comes from: the
    relation-level checks "remain the Grounder's and the Fact Check's".

    Before the fix, a name opening a sentence after a quoted stop was caught -- but only
    because the split FAILED and the name landed mid-segment by accident. The fix does
    not weaken a deliberate guarantee; it removes an accidental one and makes the
    exemption uniform. A name is exempt in that position after a quoted stop exactly as
    it already was after a bare stop, and nowhere else.
    """
    print("\n1b. The sentence-initial exemption is now uniform, and that is deliberate")
    quoted = ST._entities('She called it "finished." Hokusai disagreed that morning.')
    bare = ST._entities('She called it finished. Hokusai disagreed that morning.')
    check("after a quoted stop behaves exactly as after a bare stop",
          ("Hokusai" in quoted) == ("Hokusai" in bare), (sorted(quoted), sorted(bare)))
    check("and in both the opening word is exempt, by design",
          "Hokusai" not in quoted and "Hokusai" not in bare)
    check("the SAME name is still seen wherever else it appears",
          "Hokusai" in ST._entities('She called it "finished." The dealer told Hokusai '
                                    'the next morning.'))


# ── defect 2: the Ledger is part of the approved material ────────────────────
def test_a_multi_word_name_the_ledger_grants_does_not_fragment():
    print("\n2. A multi-word proper noun the Ledger grants is not split into inventions")
    pk = _packet("SFMOMA bought the drawing.", "It hung in San Francisco.")
    led = _ledger("Photographs are courtesy of the San Francisco Museum of Modern Art.")
    art = "# T\n\nIt hung at the San Francisco Museum of Modern Art that year.\n"

    before = ST.factual_surface_audit(art, pk)
    check("without the Ledger the fragments still look unapproved (the old behaviour)",
          {"Museum", "Modern"} <= set(before["unapproved_entities"]),
          before["unapproved_entities"])

    after = ST.factual_surface_audit(art, pk, led)
    check("with the Ledger they are licensed",
          not ({"Museum", "Modern"} & set(after["unapproved_entities"])),
          after["unapproved_entities"])
    check("and the surface is clean", after["hard_ok"], after)


def test_the_ledger_also_licenses_figures_and_vocabulary_it_grants():
    print("\n2b. The same applies to every channel, not only entities")
    pk = _packet("The museum bought work.")
    led = _ledger("SFMOMA acquired more than 100 pieces.",
                  "The gallery wall was painted pink.")
    art = "# T\n\nIt acquired more than 100 pieces for the pink wall.\n"
    r = ST.factual_surface_audit(art, pk, led)
    check("a figure the Ledger grants does not block", "100" not in r["unapproved_numbers"],
          r["unapproved_numbers"])
    check("a sensory word the Ledger grants does not block",
          "pink" not in r["unapproved_sensory"], r["unapproved_sensory"])


def test_omitting_the_ledger_reproduces_the_old_behaviour_exactly():
    print("\n2c. The parameter is additive -- existing callers are unchanged")
    pk = _packet("SFMOMA bought the drawing.")
    art = "# T\n\nIt hung at the Rijksmuseum.\n"
    check("packet-only call still works and still blocks",
          ST.factual_surface_audit(art, pk)
          == ST.factual_surface_audit(art, pk, None))
    check("and it blocks the invention",
          "Rijksmuseum" in ST.factual_surface_audit(art, pk)["unapproved_entities"])


# ── the screen must still catch real inventions ──────────────────────────────
def test_a_genuinely_new_entity_still_holds():
    print("\n3. A name in neither the packet nor the Ledger still HOLDS")
    pk = _packet("SFMOMA bought the drawing.")
    led = _ledger("Photographs are courtesy of the San Francisco Museum of Modern Art.")

    art = "# T\n\nIt hung at the Guggenheim in Bilbao that spring.\n"
    r = ST.factual_surface_audit(art, pk, led)
    check("the invented institution blocks", "Guggenheim" in r["unapproved_entities"],
          r["unapproved_entities"])
    check("the invented place blocks", "Bilbao" in r["unapproved_entities"],
          r["unapproved_entities"])
    check("hard_ok is False", r["hard_ok"] is False)

    # And in a sentence that follows a quoted stop -- the position defect 1 changed --
    # an invention anywhere but the opening word still blocks.
    art2 = '# T\n\nThe curator called it "finished." Staff at the Guggenheim disagreed.\n'
    r2 = ST.factual_surface_audit(art2, pk, led)
    check("an invention in a sentence following a quoted stop still blocks",
          "Guggenheim" in r2["unapproved_entities"], r2["unapproved_entities"])


def test_a_genuinely_new_number_still_holds():
    print("\n3b. A figure in neither still HOLDS")
    pk = _packet("SFMOMA bought the drawing.")
    led = _ledger("SFMOMA acquired more than 100 pieces.")
    r = ST.factual_surface_audit("# T\n\nIt paid 4.2 million for them.\n", pk, led)
    check("the invented figure blocks", "4.2" in r["unapproved_numbers"],
          r["unapproved_numbers"])
    check("hard_ok is False", r["hard_ok"] is False)


def test_a_partial_phrase_match_is_not_a_licence():
    """The Ledger licenses what it contains. It must not license a name merely adjacent
    to one it contains."""
    print("\n3c. Licensing is by content, not by proximity")
    pk = _packet("The museum bought work.")
    led = _ledger("Courtesy of the San Francisco Museum of Modern Art.")
    r = ST.factual_surface_audit(
        "# T\n\nIt hung at the San Diego Museum of Contemporary Art.\n", pk, led)
    check("'Diego' is not licensed by 'San Francisco'",
          "Diego" in r["unapproved_entities"], r["unapproved_entities"])
    check("'Contemporary' is not licensed by 'Modern'",
          "Contemporary" in r["unapproved_entities"], r["unapproved_entities"])


# ── the number tokeniser: a figure wearing a unit suffix ─────────────────────
#
# `\b\d[\d,.]*\b` cannot end between "0" and "m", and finds no shorter match, so "A$90m"
# yielded NO token while "A$90 million" yielded "90". Measured on
# production-20260905T210605Z-2d62633a: the packet said "A$90m", the prose said "A$90
# million", and `90` blocked -- the only number ever to block a run in the retained record.
# The mild half is that false positive. The half that matters is that an invented "A$250m"
# was never looked at, because the screen saw no figure there at all.


def test_the_number_tokeniser_itself_is_unchanged():
    """THE GUARD ON THE WHOLE DESIGN. The unit reading lives in factual_surface_audit, not
    in `_numbers`, because `_numbers` feeds CUT watch-term selection at
    composition.py:2535 -- which pushes its results first, longest first, into a CAPPED
    list. An adversary showed that extra tokens displace later candidates: with a cut fact
    carrying six suffixed figures the identifier `abc123` fell off and a hard CUT_LEAKAGE
    finding became a pass. If this test ever fails, every caller of `_numbers` has moved."""
    print("\n4. `_numbers` is untouched -- every other caller is unaffected")
    for text, want in (("A$90m", set()), ("5km", set()), ("1990s", set()),
                       ("A$90 million", {"90"}), ("in 2018, it closed", {"2018"}),
                       ("179.8 million", {"179.8"}), ("100,000 people", {"100,000"})):
        check("  _numbers(%-18s) == %s" % (repr(text), want or "nothing"),
              ST._numbers(text) == want, ST._numbers(text))


def test_a_figure_with_a_unit_suffix_is_visible_to_the_screen():
    print("\n4b. The audit reads a figure wearing a unit suffix")
    check("precondition: the spelled-out form was always seen",
          ST._numbers("A$90 million") == {"90"}, ST._numbers("A$90 million"))
    check("the suffixed form yields a token", ST._figures_with_units("A$90m") == {"90m"},
          ST._figures_with_units("A$90m"))
    for text, want in (("5km", "5km"), ("20kg", "20kg"), ("3bn", "3bn")):
        check("  %-7s yields %s" % (text, want), want in ST._figures_with_units(text),
              ST._figures_with_units(text))
    check("case is folded, so A$90M and A$90m are one figure",
          ST._figures_with_units("A$90M") == ST._figures_with_units("A$90m"),
          (ST._figures_with_units("A$90M"), ST._figures_with_units("A$90m")))


def test_a_suffixed_figure_does_not_license_the_bare_numeral():
    """THE REASON THE TOKEN IS "90m" AND NOT "90". An adversary constructed the case:
    with the bare numeral, an approved "A$90m" would license a prose "90 deaths", which
    blocks today. Leaving the bare-numeral tokens untouched makes that structurally
    impossible -- the approved side gains nothing that can cover a bare numeral."""
    print("\n4c. A figure in dollars does not license the same numeral in deaths")
    pk = _packet("The deal covers A$90m.")
    r = ST.factual_surface_audit("# T\n\nThe fire killed 90 people that night.\n", pk)
    check("90 is still unapproved", "90" in r["unapproved_numbers"],
          r["unapproved_numbers"])
    check("hard_ok is False", r["hard_ok"] is False)


def test_a_grammatical_suffix_is_not_a_unit():
    """"107th" and "1990s" must not become tokens: an ordinal in prose would then flag
    against an approved plain figure. Measured -- "107th" was the one and only tightening
    this change produced across the record before grammatical suffixes were excluded.
    Their behaviour is deliberately UNCHANGED, which here means still invisible."""
    print("\n4d. Ordinals and plurals are grammar, not units")
    for text in ("107th", "19th", "1990s", "2nd", "3rds", "5s"):
        check("  %-7s yields no unit token" % text,
              ST._figures_with_units(text) == set(), ST._figures_with_units(text))


def test_separators_are_untouched():
    """The trailing boundary used to force a backtrack off a swallowed separator. With it
    gone the greedy class keeps them, so they are stripped explicitly -- and these are the
    cases that would break if the stripping were wrong."""
    print("\n4e. Separators inside and after a figure")
    check("a trailing comma is not part of the figure",
          ST._numbers("in 2018, the scheme closed") == {"2018"},
          ST._numbers("in 2018, the scheme closed"))
    check("a decimal point is", "179.8" in ST._numbers("179.8 million"),
          ST._numbers("179.8 million"))
    check("a thousands separator is", "100,000" in ST._numbers("100,000 people"),
          ST._numbers("100,000 people"))
    check("a full stop ending a sentence is not",
          ST._numbers("It cost 90.") == {"90"}, ST._numbers("It cost 90."))


def test_the_two_notations_still_disagree_and_that_is_on_purpose():
    """WHAT THIS CHANGE DELIBERATELY LEAVES BROKEN, pinned so nobody reads it as an
    oversight. production-20260905T210605Z-2d62633a: packet "A$90m", prose "A$90
    million", `90` blocked -- the only number ever to block a run in the record, and a
    genuine false positive. Closing it requires the two notations to produce the SAME
    token, and that is exactly the loosening test_a_suffixed_figure_does_not_license_the
    _bare_numeral exists to prevent. The trade is the owner's; this test fails the day
    someone makes it quietly."""
    print("\n4f. The false positive is still here, deliberately")
    pk = _packet("The deal covers up to A$75 million of Tamboran's A$90m share.")
    r = ST.factual_surface_audit(
        "# T\n\nIt covers up to A$75 million of the A$90 million share.\n", pk)
    check("90 is still unapproved -- the known false positive",
          "90" in r["unapproved_numbers"], r["unapproved_numbers"])


def test_an_invented_suffixed_figure_blocks():
    """THE HALF THAT MATTERS. This case passed the screen before the change: the prose
    carried a figure the approved material never granted, and the tokeniser saw no figure
    there at all."""
    print("\n4g. An invented figure in suffixed notation is caught")
    pk = _packet("The deal covers up to A$75 million.")
    r = ST.factual_surface_audit("# T\n\nThe deal covers A$250m instead.\n", pk)
    check("the invented figure blocks", "250m" in r["unapproved_numbers"],
          r["unapproved_numbers"])
    check("hard_ok is False", r["hard_ok"] is False)


def test_the_same_suffixed_figure_on_both_sides_is_clean():
    """The approved side must read units too, or the fix would only ever ADD flags: a
    packet saying "A$90m" and prose saying "A$90m" would disagree with itself."""
    print("\n4h. The same suffixed figure on both sides is licensed")
    pk = _packet("The deal covers A$90m over three years.")
    r = ST.factual_surface_audit("# T\n\nThe deal covers A$90m over three years.\n", pk)
    check("90m is not unapproved", "90m" not in r["unapproved_numbers"],
          r["unapproved_numbers"])
    check("and the surface is clean", r["hard_ok"], r["unapproved_numbers"])


def test_a_notation_difference_is_not_a_new_figure():
    """THE RULE THAT KEEPS THIS FROM HOLDING GOOD ARTICLES. An adversary rated this the
    most likely shape of all: the article says "50 kilometres", the dek says "50km", and
    a screen that flags every unmatched unit token blocks the package for a notation
    difference. The numeral is the figure; the suffix is how it is written. So a suffixed
    figure is refused only when its NUMERAL is unlicensed too."""
    print("\n4i. An abbreviation of a licensed figure is not an invention")
    pk = _packet("The route runs 50 kilometres inland from the coast.")
    r = ST.factual_surface_audit("# T\n\nThe route runs 50km inland.\n", pk)
    check("50km is not unapproved", "50km" not in r["unapproved_numbers"],
          r["unapproved_numbers"])
    check("and the surface is clean", r["hard_ok"], r["unapproved_numbers"])
    # and the catch survives it: an invented figure has no licensed numeral behind it
    pk2 = _packet("The deal covers up to A$75 million.")
    r2 = ST.factual_surface_audit("# T\n\nThe deal covers A$250m instead.\n", pk2)
    check("an invented suffixed figure still blocks",
          "250m" in r2["unapproved_numbers"], r2["unapproved_numbers"])


def main():
    for t in (test_the_number_tokeniser_itself_is_unchanged,
              test_a_notation_difference_is_not_a_new_figure,
              test_the_same_suffixed_figure_on_both_sides_is_clean,
              test_a_figure_with_a_unit_suffix_is_visible_to_the_screen,
              test_a_suffixed_figure_does_not_license_the_bare_numeral,
              test_a_grammatical_suffix_is_not_a_unit,
              test_separators_are_untouched,
              test_the_two_notations_still_disagree_and_that_is_on_purpose,
              test_an_invented_suffixed_figure_blocks,
              test_sentence_initial_after_a_closing_quote_is_not_an_entity,
              test_the_sentence_initial_tradeoff_is_now_uniform,
              test_a_multi_word_name_the_ledger_grants_does_not_fragment,
              test_the_ledger_also_licenses_figures_and_vocabulary_it_grants,
              test_omitting_the_ledger_reproduces_the_old_behaviour_exactly,
              test_a_genuinely_new_entity_still_holds,
              test_a_genuinely_new_number_still_holds,
              test_a_partial_phrase_match_is_not_a_licence):
        t()
    print()
    if FAILURES:
        print("%d failure(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("All Safety entity-extraction tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
