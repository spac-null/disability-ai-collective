#!/usr/bin/env python3
"""
grounding_repair_subtractive_test.py -- a factual repair subtracts, and the instruction
names every relation the machine check refuses.

THE PRODUCTION RUN. production-20260907T154937Z-8556915b reached Grounding -- the first
run to get past Safety after the matcher fix -- and was lost at the repair:

    edit 1 ADDS rather than subtracts -- relations=['EQUIVALENCE']
        (allowed only what the cited facts ['F27', 'F25'] carry)
    edit 2 ADDS rather than subtracts -- relations=['GENERALIZATION']
        (allowed only what the cited facts ['F18', 'F54'] carry)

The validator was right both times and is not touched here. What was wrong is that
`REPAIR_GROUNDING_SYSTEM` warned about four of the NINE relation classes
`apply_grounding_repair` measures. GENERALIZATION -- the one that failed on edit 2 -- was
not among them, and neither were NEGATION, ABSENCE or the superlative. An instruction
that lists a subset of what the check refuses teaches a different contract from the one
the model is graded on.

These tests hold two things: the validator still refuses both relations, and the
instruction still tells the model to delete rather than re-compose, and still names every
class the check reads.

Offline. No provider, no network, no run.

USAGE: python3 automation/grounding_repair_subtractive_test.py
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
                          "" if ok else "   <- " + str(detail)[:240]))
    if not ok:
        FAILURES.append(label)


LEDGER = {
    "F27": {"fact_id": "F27", "proposition": "The team reported a decoding accuracy of "
            "62 per cent on the held-out session.",
            "support_span": "decoding accuracy of 62 per cent on the held-out session"},
    "F25": {"fact_id": "F25", "proposition": "The interface was tested with one "
            "participant over four sessions.",
            "support_span": "one participant over four sessions"},
    "F18": {"fact_id": "F18", "proposition": "The authors describe a slow adaptation "
            "loop running beside the fast decoder.",
            "support_span": "a slow adaptation loop running beside the fast decoder"},
    "F54": {"fact_id": "F54", "proposition": "The paper is a preprint submitted in "
            "September 2026.", "support_span": "preprint submitted in September 2026"},
}
PACKET = {"article_type": "field_note", "story_spine": "a decoder and its slow loop",
          "opening": "a decoder", "reader_initial_state": "", "beats": [],
          "turn": "", "crip_turn": "", "lens": "", "ending_move": "",
          "facts": [], "quotes": [], "definitions": {}, "prohibitions": []}
ARTICLE = ("The team reported a decoding accuracy of 62 per cent on the held-out "
           "session. The authors describe a slow adaptation loop running beside the "
           "fast decoder.\n")
FINDINGS = [{"id": "G1", "classification": "TRUE_UNSUPPORTED", "repairable": True,
             "quote": "The team reported a decoding accuracy of 62 per cent on the "
                      "held-out session.", "why": "scope"},
            {"id": "G2", "classification": "TRUE_UNSUPPORTED", "repairable": True,
             "quote": "The authors describe a slow adaptation loop running beside the "
                      "fast decoder.", "why": "scope"}]


def _apply(edits):
    return CP.apply_grounding_repair(ARTICLE, edits, FINDINGS, LEDGER, PACKET)


# ── the validator still refuses both relation classes ───────────────────────────────
def test_an_added_equivalence_is_still_refused():
    _t, _p, errs = _apply([{
        "finding_id": "G1", "operation": "NARROW",
        "original": "The team reported a decoding accuracy of 62 per cent on the "
                    "held-out session.",
        "repaired": "The reported accuracy on the held-out session amounts to the same "
                    "as the accuracy over four sessions.",
        "fact_ids": ["F27", "F25"], "what_was_removed": "scope"}])
    check("an edit that introduces EQUIVALENCE is refused", bool(errs), errs)
    check("...named as ADDS rather than subtracts, with the relation",
          any("ADDS rather than subtracts" in e and "EQUIVALENCE" in e for e in errs),
          errs)


def test_an_added_generalization_is_still_refused():
    _t, _p, errs = _apply([{
        "finding_id": "G2", "operation": "NARROW",
        "original": "The authors describe a slow adaptation loop running beside the "
                    "fast decoder.",
        "repaired": "Every such interface runs a slow adaptation loop beside its fast "
                    "decoder.",
        "fact_ids": ["F18", "F54"], "what_was_removed": "scope"}])
    check("an edit that introduces GENERALIZATION is refused", bool(errs), errs)
    check("...named as ADDS rather than subtracts, with the relation",
          any("ADDS rather than subtracts" in e and "GENERALIZATION" in e for e in errs),
          errs)


def test_both_together_are_refused_as_two_edits():
    _t, _p, errs = _apply([
        {"finding_id": "G1", "operation": "NARROW",
         "original": "The team reported a decoding accuracy of 62 per cent on the "
                     "held-out session.",
         "repaired": "The held-out accuracy is equivalent to the four-session result.",
         "fact_ids": ["F27", "F25"], "what_was_removed": "scope"},
        {"finding_id": "G2", "operation": "NARROW",
         "original": "The authors describe a slow adaptation loop running beside the "
                     "fast decoder.",
         "repaired": "In general these systems always run a slow loop beside a fast "
                     "decoder.",
         "fact_ids": ["F18", "F54"], "what_was_removed": "scope"}])
    check("both edits are refused, as the production run recorded", len(errs) >= 2, errs)
    check("edit 1 is the equivalence", any("edit 1" in e and "EQUIVALENCE" in e
                                           for e in errs), errs)
    check("edit 2 is the generalisation", any("edit 2" in e and "GENERALIZATION" in e
                                              for e in errs), errs)


# ── and a genuinely subtractive edit still passes ───────────────────────────────────
def test_a_subtractive_edit_is_still_allowed():
    text, prov, errs = _apply([{
        "finding_id": "G1", "operation": "NARROW",
        "original": "The team reported a decoding accuracy of 62 per cent on the "
                    "held-out session.",
        "repaired": "The team reported a decoding accuracy on the held-out session.",
        "fact_ids": ["F27"], "what_was_removed": "the figure"}])
    check("cutting the unsupported figure is allowed", not errs, errs)
    check("...and the edit is applied", "62 per cent" not in text, text[:120])
    check("...and recorded with its licensing facts",
          prov and prov[0]["fact_ids"] == ["F27"], prov)

    text2, _p2, errs2 = _apply([{
        "finding_id": "G2", "operation": "DELETE",
        "original": "The authors describe a slow adaptation loop running beside the "
                    "fast decoder.",
        "repaired": "", "fact_ids": [], "what_was_removed": "the sentence"}])
    check("deleting the sentence outright is allowed", not errs2, errs2)
    check("...and it is gone", "slow adaptation loop" not in text2, text2[:120])


# ── the instruction matches the check ───────────────────────────────────────────────
def test_the_instruction_directs_toward_deletion_not_recomposition():
    p = CP.REPAIR_GROUNDING_SYSTEM
    for phrase, why in (
            ("EXCISING EDITOR, NOT A WRITER", "the whole contract"),
            ("PREFER DELETION OVER REPLACEMENT", "the ordering rule"),
            ("WEAKER THAN THE ORIGINAL, NEVER STRONGER", "the direction rule"),
            ("RELATIONS ARE FACTUAL CLAIMS", "connectives are claims"),
            ("DELETE IT", "deletion is always available")):
        check("the instruction still says: %s" % why, phrase in p, phrase)
    check("it still forbids re-writing the sentence around the problem",
          "Re-writing the sentence around the problem is the one move that is never "
          "available." in p)
    check("it still states the one-repair consequence",
          "there is no second repair" in p)


def test_the_instruction_names_every_relation_the_check_measures():
    p = CP.REPAIR_GROUNDING_SYSTEM
    measured = [name for name, _rx in ST.TURN_RELATION_SHAPES]
    check("the check measures nine relation classes", len(measured) == 9, measured)
    for name in measured:
        check("the instruction names %s" % name, name in p)
    # The class that actually cost the run gets its own explanation, because it is the
    # one that reads as caution while being an enlargement.
    check("generalisation is called out in its own right",
          "GENERALISING IS THE QUIETEST WAY TO BREAK THIS" in p)
    check("...with the retreat-to-the-general failure named concretely",
          "one study becoming 'such studies'" in p)


def test_the_permissions_and_budget_are_unchanged():
    check("the operations are the same seven",
          CP.REPAIR_OPS == ("NARROW", "REMOVE_EXCLUSIVITY", "CORRECT_TIME",
                            "CORRECT_DATE", "RESTORE_ATTRIBUTION",
                            "NARROW_CHARACTERISATION", "DELETE"), CP.REPAIR_OPS)
    check("the repair is still exactly one call, never repeated",
          "Exactly one call. Subtractive, audited, and never repeated."
          in (CP.grounding_repair.__doc__ or ""))
    check("TEMPORAL is still exempt only under the two time operations",
          'x["relation"] == ST.TEMPORAL' in
          (HERE / "new_engine_v1" / "composition.py").read_text()
          and 'op in ("CORRECT_TIME", "CORRECT_DATE")' in
          (HERE / "new_engine_v1" / "composition.py").read_text())


def main():
    for fn in (test_an_added_equivalence_is_still_refused,
               test_an_added_generalization_is_still_refused,
               test_both_together_are_refused_as_two_edits,
               test_a_subtractive_edit_is_still_allowed,
               test_the_instruction_directs_toward_deletion_not_recomposition,
               test_the_instruction_names_every_relation_the_check_measures,
               test_the_permissions_and_budget_are_unchanged):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL GROUNDING REPAIR SUBTRACTIVE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
