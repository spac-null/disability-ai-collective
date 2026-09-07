#!/usr/bin/env python3
"""
safety_matcher_precision_test.py -- Safety blocks unsupported claims, not unrelated
substrings, ordinary title-cased vocabulary, or a publisher's name.

THREE PRODUCTION ARTICLES, ONE AFTERNOON (2026-09-07). Five of the six Safety blockers
raised across three real runs were string-matching artefacts with no factual defect
behind them:

  cut term "Historic" (from a headline)      fired on  "historically"
  cut term "Ability"  (a book category)      fired on  "disability"
  provenance role PRIMARY                    fired on  the publisher "Primary Information"
  title "One Room, Two Acoustics, Convertible in a Day"
                                             reported "Acoustics" and "Convertible"
                                             as unapproved named ENTITIES

The sixth was real and must stay: a homepage excerpt claiming "the only thing that
changes from frame to frame is the sheet of paper itself" where the ledger licenses
constant exposure and developing conditions and nothing licenses the exclusivity.

These tests hold both halves of that line. Offline: no provider, no network, no run.

USAGE: python3 automation/safety_matcher_precision_test.py
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP                          # noqa: E402
from new_engine_v1 import story as ST                                # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:220]))
    if not ok:
        FAILURES.append(label)


def cut_violations(prose, terms_by_id, reasons=None):
    reasons = reasons or {}
    arch = {"cut_evidence": [{"evidence_id": cid, "reason": reasons.get(cid, "REDUNDANT_PROOF")}
                             for cid in terms_by_id]}
    return CP.ST.cut_adherence(prose, arch, terms_by_id)["violations"]


# ── FIX 1: the literal CUT branch is token-wise ─────────────────────────────────────
def test_literal_cut_is_token_wise():
    # The two real production false positives.
    v = cut_violations("Witko said that historically, when the black box theatre was in "
                       "the space and a show was on, they would call all the staff.",
                       {"F57": ["Historic"]})
    check("cut term 'Historic' does NOT fire on 'historically'", v == [], v)

    v = cut_violations("The material comes from pop culture imagery, memes, "
                       "advertisements, disability signage, artworks and archives, and "
                       "she notes that disability laws are weakening.",
                       {"F48": ["Ability"]})
    check("cut term 'Ability' does NOT fire on 'disability'", v == [], v)

    # And the screen still screens.
    v = cut_violations("The historic theatre reopened in September.", {"F57": ["Historic"]})
    check("cut term 'Historic' DOES fire on the token 'historic'", len(v) == 1, v)
    check("...reported as a literal match", v and v[0]["match"] == "literal", v)

    v = cut_violations("One category is Ability, another is Airports.", {"F48": ["Ability"]})
    check("cut term 'Ability' DOES fire on the token 'Ability'", len(v) == 1, v)

    # Punctuation and sentence ends still close a token.
    for prose, why in (("The theatre is historic.", "full stop"),
                       ("It is 'historic', they said.", "quotes and comma"),
                       ("Historic, and expensive.", "sentence-initial"),
                       ("A historic-looking facade.", "hyphen")):
        v = cut_violations(prose, {"F57": ["Historic"]})
        check("still caught across a %s boundary" % why, len(v) == 1, (prose, v))

    # Longer unrelated words no longer fire in either direction.
    for prose, why in (("a scandal in the archive", "'scan' inside 'scandal'"),
                       ("the ability to see", "'Ability' as its own word IS caught"),
                       ("the disabilities register", "'Ability' inside 'disabilities'")):
        pass
    check("'scan' does not fire on 'scandal'",
          cut_violations("A scandal in the archive.", {"F1": ["scan"]}) == [],
          cut_violations("A scandal in the archive.", {"F1": ["scan"]}))
    check("'Ability' does not fire on 'disabilities' either",
          cut_violations("The disabilities register.", {"F48": ["Ability"]}) == [])


def test_inflection_branch_is_untouched():
    """The literal branch narrowing must not cost the screen its inflection coverage."""
    # NOTE: the branch's own comment offers "subsidy" against "subsidised" as an
    # example. It does not in fact match, at this commit or before it -- `_stem` yields
    # "subsidy" and "subsidis" -- so it is deliberately not asserted here. Recorded as an
    # observation about that comment, not fixed: narrowing the literal branch neither
    # caused nor worsened it.
    for term, prose in (("scan", "The scans were filed."),
                        ("simulating", "The model simulated the load."),
                        # Regular plurals the stemmer alone cannot pair up. These WERE
                        # caught by the old substring test and must still be.
                        ("plate", "The ten plates were made."),
                        ("theatre", "Two theatres reopened."),
                        ("city", "Three cities agreed."),
                        ("match", "The matches were struck.")):
        v = cut_violations(prose, {"F1": [term]})
        check("inflected match still caught: %r vs %r" % (term, prose),
              len(v) == 1 and v[0]["match"] == "inflected", v)
    check("and 'scandal' is still not an inflection of 'scan'",
          cut_violations("A scandal.", {"F1": ["scan"]}) == [])
    check("nor is 'platform' an inflection of 'plate'",
          cut_violations("The platform was raised.", {"F1": ["plate"]}) == [])
    check("nor 'historically' of 'Historic', by either route",
          cut_violations("Historically, the room was a theatre.",
                         {"F57": ["Historic"]}) == [])
    check("nor 'disability' of 'Ability', by either route",
          cut_violations("Disability signage.", {"F48": ["Ability"]}) == [])


def test_multi_word_cut_terms():
    v = cut_violations("The Cherry Lane Theatre reopened.", {"F1": ["cherry lane"]})
    check("a multi-word term matches a contiguous token sequence", len(v) == 1, v)
    v = cut_violations("A cherry tree on the lane.", {"F1": ["cherry lane"]})
    check("...and not two words that merely both occur", v == [], v)


# ── FIX 2: provenance frames are frames, not vocabulary ─────────────────────────────
def test_role_taxonomy_is_a_frame_not_a_word():
    clean = [
        ("available online now from the publisher, Primary Information, and in "
         "bookstores from September 15", "the publisher 'Primary Information'"),
        ("an independent bookshop, independently run", "ordinary 'independent'"),
        ("she won the Senate primary in March", "'Senate primary'"),
        ("tertiary education funding was cut", "ordinary 'tertiary'"),
        ("she anchors the evening news", "'anchors' as an ordinary verb"),
    ]
    for text, why in clean:
        check("NOT machine language: %s" % why, ST.leaks(text) == [], ST.leaks(text))

    caught = [
        ('"role": "ANCHOR"', "the serialised role label"),
        ("ANCHOR: the building opened in 1938", "a bare capitalised role label"),
        ("role: primary", "a lowercase labelled role"),
        ("role = independent", "an equals-form label"),
        ("[primary] the source says", "a bracketed role"),
        ("TERTIARY material was discarded", "another capitalised role token"),
    ]
    for text, why in caught:
        check("STILL machine language: %s" % why, ST.leaks(text) != [], text)


def test_other_provenance_frames_unchanged():
    for text in ("the research pack does not establish this",
                 "nothing in the source supports it",
                 "S12 records the figure",
                 "the sha256 of the snapshot",
                 "it does not describe the building's form"):
        check("unchanged frame still caught: %r" % text[:44], ST.leaks(text) != [])
    check("and ordinary prose is still clean",
          ST.leaks("The pavilion stands on six columns. Water passes beneath it.") == [])


# ── FIX 3: title case is typography, not entity evidence ────────────────────────────
def _pkg(title="", dek="", excerpt="", meta="", hook=""):
    return {"title": title, "dek": dek, "homepage_excerpt": excerpt,
            "meta_description": meta, "social_hook": hook}


def _audit(final_text, package, ledger, packet_facts=""):
    packet = {"article_type": "field_note", "story_spine": packet_facts or "a room",
              "opening": "a room", "reader_initial_state": "", "beats": [],
              "turn": "", "crip_turn": "", "lens": "", "ending_move": "",
              "facts": [], "quotes": [], "definitions": {}, "prohibitions": []}
    return CP.safety_audit(final_text, final_text, packet, {"cut_evidence": []},
                           ledger, {}, {}, {}, package=package)


LEDGER_THEATRE = {
    "F11": {"fact_id": "F11", "proposition": "The dual-purpose conversion required a "
            "giant screening rig outfitted with speakers that descends from the "
            "stage's upper canopy.", "support_span": "dual-purpose conversion"},
    "F15": {"fact_id": "F15", "proposition": "According to LSS, the conversion between "
            "the two modes can happen within a day if needed.",
            "support_span": "conversion between the two modes ... within a day"},
}
PROSE_THEATRE = ("The mainstage seats 179. For a screening the curtains are pulled "
                 "across the brick and the rig comes down; for plays the curtains stay "
                 "open. The acoustic conditions differ between the two modes, and the "
                 "theatre switches between them often.\n")


def test_title_cased_ordinary_vocabulary_is_not_an_entity():
    r = _audit(PROSE_THEATRE,
               _pkg(title="One Room, Two Acoustics, Convertible in a Day",
                    dek="A24's renovated mainstage has no single sound."),
               LEDGER_THEATRE)
    ents = r["audits"]["publication_package"]["factual_surface"]["unapproved_entities"]
    check("'Acoustics' is not a novel named entity", "Acoustics" not in ents, ents)
    check("'Convertible' is not a novel named entity", "Convertible" not in ents, ents)
    check("the package raises no PACKAGE_UNSUPPORTED_FACTS",
          not any("PACKAGE_UNSUPPORTED_FACTS" in b for b in r["blocking"]), r["blocking"])


def test_a_genuinely_novel_name_still_blocks():
    # (a) a name in the dek, which is sentence-cased -- untouched by the title rule
    r = _audit(PROSE_THEATRE,
               _pkg(title="One Room, Two Acoustics, Convertible in a Day",
                    dek="The work was paid for by the Rockefeller Foundation."),
               LEDGER_THEATRE)
    ents = r["audits"]["publication_package"]["factual_surface"]["unapproved_entities"]
    check("an invented name in the dek is still an entity",
          any("Rockefeller" in e for e in ents), ents)
    check("...and still blocks",
          any("PACKAGE_UNSUPPORTED_FACTS" in b for b in r["blocking"]), r["blocking"])

    # (b) a SHAPED name inside the title keeps its evidence.
    #     NOTE: a digit-bearing name like "A24" is invisible to `_entities` at any
    #     commit -- its token regex is [A-Z][A-Za-z'.-]{2,}, which excludes digits -- so
    #     it is not asserted here. Pre-existing, unrelated to this change, recorded.
    r = _audit(PROSE_THEATRE,
               _pkg(title="One Room, Two Acoustics, Convertible in NASA in a Day"),
               LEDGER_THEATRE)
    ents = r["audits"]["publication_package"]["factual_surface"]["unapproved_entities"]
    check("an all-caps acronym in the title is still an entity",
          any("NASA" in e for e in ents), ents)

    r = _audit(PROSE_THEATRE,
               _pkg(title="One Room, Two Acoustics, Convertible at MoMA in a Day"),
               LEDGER_THEATRE)
    ents = r["audits"]["publication_package"]["factual_surface"]["unapproved_entities"]
    check("an internal-capital name in the title is still an entity",
          any("MoMA" in e for e in ents), ents)


def test_the_helpers_themselves():
    check("a real title reads as title-cased",
          CP._is_title_cased("One Room, Two Acoustics, Convertible in a Day"))
    check("a dek does not",
          not CP._is_title_cased("A24's renovated Cherry Lane mainstage has no single "
                                 "sound, and the studio says the switch can happen "
                                 "within a day."))
    check("a sentence-cased line with one name does not",
          not CP._is_title_cased("The work was paid for by the Rockefeller Foundation."))
    for tok, want in (("A24", True), ("MoMA", True), ("U.S.", True), ("ASL", True),
                      ("Acoustics", False), ("Convertible", False),
                      ("Rockefeller", False)):
        check("shape signal %r -> %s" % (tok, want), CP._has_shape_signal(tok) is want)


def test_licence_is_morphology_and_ledger_aware():
    r = _audit(PROSE_THEATRE, _pkg(dek="Two acoustics, and a conversion in a day."),
               LEDGER_THEATRE)
    sf = r["audits"]["publication_package"]["factual_surface"]
    check("a lowercase morphological variant of article vocabulary is licensed",
          not sf["unapproved_entities"], sf["unapproved_entities"])


# ── THE REAL CATCH MUST SURVIVE ALL OF THE ABOVE ────────────────────────────────────
LEDGER_PORTER = {
    "F42": {"fact_id": "F42", "proposition": "The ten photo-etchings in Wrinkle register "
            "in grey tonalities the journey of a blank sheet of paper from a pristine "
            "state to its transformation into a wrinkled piece of waste.",
            "support_span": "registering in grey tonalities the journey of a blank sheet"},
    "F43": {"fact_id": "F43", "proposition": "To produce the sequential crumpling, Porter "
            "photographed each step of the action to create ten separate plates, keeping "
            "light exposure and developing conditions the same to guarantee a consistent "
            "effect.", "support_span": "making sure that the light exposure and "
            "developing conditions remained the same"},
}
PROSE_PORTER = ("Porter photographed each step of the action to make ten separate "
                "plates, keeping the light exposure and developing conditions the same. "
                "The plates follow one sheet of paper from a pristine state to waste.\n")


def test_the_porter_exclusivity_hold_is_preserved():
    bad = ("The ten photo-etchings in Liliana Porter's Wrinkle were made under identical "
           "light exposure and developing conditions, so the only thing that changes "
           "from frame to frame is the sheet of paper itself, on its way to becoming "
           "waste.")
    r = _audit(PROSE_PORTER, _pkg(excerpt=bad), LEDGER_PORTER)
    check("the exclusivity claim is STILL an unsupported negative",
          any("PACKAGE_UNSUPPORTED_NEGATIVES" in b for b in r["blocking"]), r["blocking"])
    check("...and the offending sentence is the one named",
          any("only thing that changes" in str(b) or "identical light exposur" in str(b)
              for b in r["blocking"]), r["blocking"])

    # The same idea WITHOUT the exclusivity is the phrasing the run's own social hook
    # used. It is not this test's job to bless it, only to show the gate is discriminating
    # between the two rather than firing on the subject matter.
    ok = ("Liliana Porter held light exposure and developing conditions identical across "
          "all ten plates of Wrinkle, so what the print sequence records is the paper's "
          "changing state.")
    r2 = _audit(PROSE_PORTER, _pkg(excerpt=ok), LEDGER_PORTER)
    check("the non-exclusive phrasing raises no unsupported negative",
          not any("PACKAGE_UNSUPPORTED_NEGATIVES" in b for b in r2["blocking"]),
          r2["blocking"])


def main():
    for fn in (test_literal_cut_is_token_wise,
               test_inflection_branch_is_untouched,
               test_multi_word_cut_terms,
               test_role_taxonomy_is_a_frame_not_a_word,
               test_other_provenance_frames_unchanged,
               test_title_cased_ordinary_vocabulary_is_not_an_entity,
               test_a_genuinely_novel_name_still_blocks,
               test_the_helpers_themselves,
               test_licence_is_morphology_and_ledger_aware,
               test_the_porter_exclusivity_hold_is_preserved):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL SAFETY MATCHER PRECISION TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
