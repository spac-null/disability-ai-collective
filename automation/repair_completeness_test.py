#!/usr/bin/env python3
"""
repair_completeness_test.py -- one factual repair must be complete for the findings it
accepts.

THE PRODUCTION RUN. production-20260907T173433Z-ab65bb22 (Lubetkin, Finsbury Health
Centre) reached GROUNDING with SAFETY passed, produced seven genuinely subtractive edits
with zero permission errors -- and was still held, on two claims the repair had just
been told about:

    TRUE_UNSUPPORTED  "The Grade I listing marks the building as of exceptional interest"
    TRUE_UNCERTAIN    "the painted lettering"

Neither was introduced by the repair and neither is a new claim. Both were SECOND
OCCURRENCES of a proposition the repair fixed elsewhere:

  "exceptional interest"  pre-repair 2 occurrences -> post-repair 1
      cut:       "...list entry number 1297993 - the highest of England's three
                  statutory protection grades, for buildings of exceptional interest."
      survived:  "The Grade I listing marks the building as of exceptional interest,
                  and the condition record describes the same building."

  "the painted lettering" survived inside a sentence the repair WAS editing, for a
      different reason -- it removed "the removed screen" from
      "Two stated aims, and between them the marble, the bronze, the concrete, the
       painted lettering, the removed screen and the substituted glass."
      and left the flagged phrase standing.

There is no second repair, so an occurrence the one pass does not reach is an occurrence
nobody reaches.

NOTHING MECHANICAL WAS BROKEN, and these tests prove that first: the applier already
accepts several edits sharing one finding_id and applies them all. The model was never
told the claim might appear twice. The fix is in the instruction; the tests below hold
both the mechanism and the instruction.

Offline: real sentences from the retained run, the real validator, no provider, no
network, no article regenerated.

USAGE: python3 automation/repair_completeness_test.py
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP                          # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:240]))
    if not ok:
        FAILURES.append(label)


# ── the real article's two occurrences, verbatim from the retained run ──────────────
S1 = ("On the National Heritage List for England it is listed at Grade I, list entry "
      "number 1297993 - the highest of England's three statutory protection grades, for "
      "buildings of exceptional interest.")
S2 = ("The Grade I listing marks the building as of exceptional interest, and the "
      "condition record describes the same building.")
S3 = ("Two stated aims, and between them the marble, the bronze, the concrete, the "
      "painted lettering, the removed screen and the substituted glass.")
UNRELATED = ("The waiting room is the main room of the building, given the width of the "
             "centre block.")
ARTICLE = " ".join([S1, UNRELATED, S2, S3]) + "\n"

LEDGER = {
    "F16": {"fact_id": "F16", "proposition": "The building is listed at Grade I on the "
            "National Heritage List for England, list entry number 1297993.",
            "support_span": "listed at Grade I, list entry number 1297993"},
    "F32": {"fact_id": "F32", "proposition": "The refurbishment record mentions marble, "
            "bronze, concrete, lettering and substituted glass.",
            "support_span": "marble, bronze, concrete, lettering, substituted glass"},
}
PACKET = {"article_type": "field_note", "story_spine": "a health centre",
          "opening": "a health centre", "reader_initial_state": "", "beats": [],
          "turn": "", "crip_turn": "", "lens": "", "ending_move": "",
          "facts": [], "quotes": [], "definitions": {}, "prohibitions": []}
FINDINGS = [
    {"id": "G1", "classification": "TRUE_UNSUPPORTED", "repairable": True,
     "quote": "for buildings of exceptional interest",
     "why": "the listing does not carry the 'exceptional interest' gloss"},
    {"id": "G2", "classification": "TRUE_UNCERTAIN", "repairable": True,
     "quote": "the painted lettering", "why": "no source says the lettering is painted"},
]


def _apply(edits):
    return CP.apply_grounding_repair(ARTICLE, edits, FINDINGS, LEDGER, PACKET)


# ── 1. the mechanism already supports completeness ──────────────────────────────────
def test_several_edits_may_share_one_finding_id():
    text, prov, errs = _apply([
        {"finding_id": "G1", "operation": "NARROW", "original": S1,
         "repaired": "On the National Heritage List for England it is listed at Grade I, "
                     "list entry number 1297993.",
         "fact_ids": ["F16"], "what_was_removed": "the exceptional-interest gloss"},
        {"finding_id": "G1", "operation": "NARROW", "original": S2,
         "repaired": "The condition record describes the same building.",
         "fact_ids": [], "what_was_removed": "the exceptional-interest gloss, again"},
    ])
    check("two edits citing ONE finding are both accepted", not errs, errs)
    check("both are recorded in provenance", len(prov) == 2, prov)
    check("the first occurrence is gone",
          "three statutory protection grades" not in text, text[:200])
    check("THE SECOND OCCURRENCE IS GONE TOO -- the production defect",
          "exceptional interest" not in text, text)
    check("unrelated prose is untouched", UNRELATED in text, text[:200])


def test_the_production_failure_reproduces_with_only_one_edit():
    """One edit, exactly as the run emitted it: the survivor survives."""
    text, _prov, errs = _apply([
        {"finding_id": "G1", "operation": "NARROW", "original": S1,
         "repaired": "On the National Heritage List for England it is listed at Grade I, "
                     "list entry number 1297993.",
         "fact_ids": ["F16"], "what_was_removed": "the exceptional-interest gloss"}])
    check("the single edit is accepted", not errs, errs)
    check("and the claim still stands elsewhere -- exactly what production saw",
          "exceptional interest" in text and S2 in text, text)


def test_editing_a_sentence_for_one_reason_can_still_leave_the_flagged_phrase():
    """The painted-lettering shape: the repair had the sentence and cut the wrong part."""
    text, _prov, errs = _apply([
        {"finding_id": "G2", "operation": "NARROW", "original": S3,
         "repaired": "Two stated aims, and between them the marble, the bronze, the "
                     "concrete, the painted lettering and the substituted glass.",
         "fact_ids": ["F32"], "what_was_removed": "the removed screen"}])
    check("the edit is accepted", not errs, errs)
    check("but the flagged phrase survives in the sentence it just rewrote",
          "the painted lettering" in text, text)
    # Done completely, the same single repair clears it.
    text2, _p2, errs2 = _apply([
        {"finding_id": "G2", "operation": "NARROW", "original": S3,
         "repaired": "Two stated aims, and between them the marble, the bronze, the "
                     "concrete and the substituted glass.",
         "fact_ids": ["F32"], "what_was_removed": "the removed screen and the painted "
                                                  "characterisation of the lettering"}])
    check("removing both in one edit is accepted", not errs2, errs2)
    check("and the flagged phrase is gone", "painted lettering" not in text2, text2)


# ── 2. completeness must not become a licence to add ────────────────────────────────
def test_a_second_edit_may_still_not_add():
    _t, _p, errs = _apply([
        {"finding_id": "G1", "operation": "NARROW", "original": S1,
         "repaired": "On the National Heritage List for England it is listed at Grade I, "
                     "list entry number 1297993.",
         "fact_ids": ["F16"], "what_was_removed": "the gloss"},
        {"finding_id": "G1", "operation": "NARROW", "original": S2,
         "repaired": "Every Grade I listing always marks a building this way.",
         "fact_ids": ["F16"], "what_was_removed": "nothing"},
    ])
    check("a second edit that generalises is still refused", bool(errs), errs)
    check("...named as ADDS rather than subtracts",
          any("ADDS rather than subtracts" in e for e in errs), errs)
    check("...and identified as edit 2, not edit 1",
          any("edit 2" in e for e in errs), errs)


def test_an_edit_for_no_finding_is_still_refused():
    _t, _p, errs = _apply([
        {"finding_id": "G9", "operation": "NARROW", "original": UNRELATED,
         "repaired": "The waiting room is a room.", "fact_ids": [],
         "what_was_removed": "x"}])
    check("an edit citing an unreported finding is refused", bool(errs), errs)
    check("unrelated sentences cannot be touched under cover of completeness",
          any("did not report" in e for e in errs), errs)


# ── 3. the instruction now requires it, and the budget is unchanged ─────────────────
def test_the_instruction_requires_completeness():
    p = CP.REPAIR_GROUNDING_SYSTEM
    check("the instruction states the rule", "ONE REPAIR, EVERY OCCURRENCE" in p)
    check("it tells the model to search the whole article",
          "You have the WHOLE ARTICLE above" in p)
    check("it authorises several edits per finding",
          "Two edits for one finding is normal and correct." in p)
    check("it names the real failure it comes from",
          "of a building 'of \nexceptional interest'".replace("\n", "") in p.replace("\n", " ")
          or "exceptional interest" in p)
    check("it states the no-second-repair consequence", "there is no second repair" in p)
    check("the schema allows a repeated finding_id",
          "Repeat the same finding_id on each" in CP.REPAIR_GROUNDING_SCHEMA)
    # And the whole prior contract survives.
    for phrase in ("EXCISING EDITOR, NOT A WRITER", "PREFER DELETION OVER REPLACEMENT",
                   "WEAKER THAN THE ORIGINAL, NEVER STRONGER", "GENERALIZATION"):
        check("prior contract kept: %s" % phrase[:38], phrase in p)


def test_budget_and_strictness_unchanged():
    check("still exactly one repair call",
          "Exactly one call. Subtractive, audited, and never repeated."
          in (CP.grounding_repair.__doc__ or ""))
    check("the operation enum is unchanged", len(CP.REPAIR_OPS) == 7, CP.REPAIR_OPS)
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    check("the relation guard is untouched",
          'x["relation"] == ST.TEMPORAL' in src
          and 'op in ("CORRECT_TIME", "CORRECT_DATE")' in src)
    check("findings_left_unanswered is still a set difference, so duplicates are safe",
          "- {str(e.get(\"finding_id\")) for e in prov}" in src)


# ── 4. grounding can still hold ─────────────────────────────────────────────────────
def test_grounding_can_still_hold_on_a_genuine_survivor():
    """Completeness does not mean everything gets cleared: an occurrence nobody edited
    still stands, and the recheck is what decides."""
    text, _p, errs = _apply([
        {"finding_id": "G1", "operation": "NARROW", "original": S1,
         "repaired": "On the National Heritage List for England it is listed at Grade I, "
                     "list entry number 1297993.",
         "fact_ids": ["F16"], "what_was_removed": "the gloss"}])
    check("a partial repair is still applied, not rejected", not errs, errs)
    check("and the unrepaired occurrence remains in the text for the recheck to find",
          "exceptional interest" in text)


def main():
    for fn in (test_several_edits_may_share_one_finding_id,
               test_the_production_failure_reproduces_with_only_one_edit,
               test_editing_a_sentence_for_one_reason_can_still_leave_the_flagged_phrase,
               test_a_second_edit_may_still_not_add,
               test_an_edit_for_no_finding_is_still_refused,
               test_the_instruction_requires_completeness,
               test_budget_and_strictness_unchanged,
               test_grounding_can_still_hold_on_a_genuine_survivor):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL REPAIR COMPLETENESS TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
