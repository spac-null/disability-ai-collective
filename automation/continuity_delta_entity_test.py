#!/usr/bin/env python3
"""
continuity_delta_entity_test.py -- an edit that MOVES a name has not ADDED it.

THE RUN THIS COST. production-20260916T070723Z-5a4e7891 ("Four Students at the Front,
Holding Sheet Music") was held at SAFETY on:

    CONTINUITY_ADDED_MATERIAL: ["editing added entities: ['Cem']"]

Cem Behar is the author the whole article is about. He is named in the Writer draft, in
the continuity text and in the final prose, and 28 Ledger facts carry his name. Nothing
was added. The delta compared both texts in PROSE mode, which drops a capitalised token
that opens a sentence -- right for "is this a name?", wrong for "was this name already
here?" -- and the polish had moved him off the front of his sentence:

    draft: "Cem Behar gives notations in the book as examples..."          -> {Behar}
    final: "Notation, by contrast, Cem Behar calls a vague suggestion..."  -> {Behar, Cem}

So the reference side no longer skips, exactly as story.factual_surface_audit already
treats its approved surface. The `after` side keeps prose mode, so an ordinary word
opening a rewritten sentence is still not read as a name.

This is a DETECTION FIX, not a relaxation: an entity absent from the draft in any
position is still reported, and numbers, sensory surface and relation growth are
untouched. The 15 and 19 September holds both stand, and are pinned here.

No model calls, no network, no evidence root.

Run (from repo root):
  python3 automation/continuity_delta_entity_test.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from new_engine_v1 import continuity as CE                       # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


# The real 16 September sentences, verbatim.
SEP16_DRAFT = ("Cem Behar gives notations in the book as examples of the different "
               "versions that arose over time in a work transmitted by meşk.")
SEP16_FINAL = ("Notation, by contrast, Cem Behar calls a vague suggestion, a lifeless "
               "object serving to sketch the general frame of the musical reality.")


def test_sep16_moved_name_is_not_added():
    errs = CE.validate_semantic_delta(SEP16_DRAFT, SEP16_FINAL)
    ent = [e for e in errs if "added entities" in e]
    check("16 Sep: a name moved off the sentence start is not reported as added",
          not ent, ent)


def test_sep16_name_is_present_in_both_texts():
    """The premise of the fix, stated independently of the delta code."""
    check("16 Sep: the draft really does name Cem", "Cem" in SEP16_DRAFT)
    check("16 Sep: the final really does name Cem", "Cem" in SEP16_FINAL)


def test_a_genuinely_new_entity_is_still_reported():
    errs = CE.validate_semantic_delta(
        "The book was published in Istanbul.",
        "The book was published in Istanbul by Yapi Kredi.")
    check("a name absent from the draft is still reported",
          any("added entities" in e for e in errs), errs)


def test_new_entity_at_a_sentence_start_is_still_reported():
    """The `after` side keeps prose mode, but a NEW name is caught wherever it sits:
    here it opens the second sentence, and the draft never contained it."""
    errs = CE.validate_semantic_delta(
        "The recording was made in winter.",
        "The recording was made in winter. Yapi Kredi published the book that year.")
    check("a new name opening a sentence is still caught",
          any("added entities" in e for e in errs), errs)


def test_numbers_and_sensory_are_untouched():
    n = CE.validate_semantic_delta("It lasted a while.", "It lasted 90 seconds.")
    check("an added number is still reported", any("added numbers" in e for e in n), n)
    # The 19 September shape: editing added sensory: ['hard'].
    s = CE.validate_semantic_delta("The admissions were unsuccessful.",
                                   "The admissions were unsuccessful and the bed was hard.")
    check("19 Sep shape: an added sensory word is still reported",
          any("added sensory" in e for e in s), s)


def test_relation_growth_is_untouched():
    """15 Sep was held on an added CAUSAL relation, 19 Sep on an added NEGATION relation.
    Neither is an entity question and neither may be affected by this fix."""
    c = CE.validate_semantic_delta("She left the ward. The report was filed.",
                                   "She left the ward because the report was filed.")
    check("15 Sep shape: an added CAUSAL relation still holds the run",
          any("CAUSE" in e or "relation" in e for e in c), c)
    n = CE.validate_semantic_delta("The coroner said the admissions helped.",
                                   "The coroner said the admissions did not help.")
    check("19 Sep shape: an added NEGATION relation still holds the run",
          any("relation" in e for e in n), n)


def test_moved_name_still_blocks_when_something_else_changed():
    """The fix must not launder an edit: moving a name is forgiven, the number that
    travelled with it is not."""
    errs = CE.validate_semantic_delta(
        "Cem Behar gives notations in the book.",
        "Notation, Cem Behar calls a suggestion, in all 12 examples.")
    check("a moved name plus an added number still holds",
          any("added numbers" in e for e in errs), errs)


def main():
    for fn in [test_sep16_moved_name_is_not_added,
               test_sep16_name_is_present_in_both_texts,
               test_a_genuinely_new_entity_is_still_reported,
               test_new_entity_at_a_sentence_start_is_still_reported,
               test_numbers_and_sensory_are_untouched,
               test_relation_growth_is_untouched,
               test_moved_name_still_blocks_when_something_else_changed]:
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL CONTINUITY DELTA ENTITY TESTS PASSED")


if __name__ == "__main__":
    main()
