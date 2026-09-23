#!/usr/bin/env python3
"""
definition_support_test.py -- a definition may not assert what a beat could not, and it
may not borrow its licence from evidence sitting elsewhere in the plan.

`definitions` was the one architect-generated field with no factual screen anywhere. Not
in architect_prose_audit's field list, so its numbers and entities were never compared to
the approved facts. Not among validate_turn_support's three fields, so the relations it
asserts were never licensed. And render() hands it to the Writer under EXPLAIN AT FIRST
USE, which is an instruction to state it.

Measured on 2e96aa7: an architecture whose only change from a clean control was

    {"servo": "a small motor from Hitachi that turns to a commanded angle in 45
              milliseconds and holds there under 12 kg of load"}

passed check_architecture with ZERO errors.

THE FIRST FIX WAS TOO WEAK AND ITS OWN ACCEPTANCE CONTROL PROVED IT. It let an undeclared
definition inherit `use_facts`, reasoning that this gave a gloss the same licence the crip
turn gets. The held-out architecture's "block group: the smallest area the survey publishes
figures for" asserts a SUPERLATIVE nothing in its evidence states -- and it PASSED, because
some unrelated fact among the 26 used ones carried a superlative somewhere. A broad pool
does not license a specific sentence; it only makes the check look like it ran. The licence
is per-term and explicit now.

TWO CLASSES OF TEST BELOW, kept apart on purpose:

  CURRENT_CONTRACT        what any new architecture must satisfy.
  HISTORICAL_COMPATIBILITY  what a REPLAY of a stored pre-`definition_evidence`
                          architecture does, and what the held-out artefact does under
                          the current contract -- which is FAIL, diagnostically. Being
                          published once is not evidence and does not relax the contract.

Behavioural, no provider, no network.
"""
import copy
import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP   # noqa: E402
from new_engine_v1 import ledger as LG        # noqa: E402
from new_engine_v1 import story as ST         # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print("  PASS  %s" % label)
    else:
        FAILURES.append(label)
        print("  FAIL  %s   <- %r" % (label, detail))


def _fact(fid, prop):
    return {"fact_id": fid, "proposition": prop, "claim_type": LG.POSITIVE,
            "claim_kind": "OCCURRENCE", "evidence_ids": ["S0"], "support_span": prop,
            "entities": [], "scope": LG.WORLD, "corpus_size": 0,
            "prohibited_extensions": []}


LEDGER = {
    "F01": _fact("F01", "The council published a ranking sheet in March."),
    "F02": _fact("F02", "Ten entries were photographed for the catalogue."),
    "F03": _fact("F03", "The catalogue was printed by a local firm."),
    "F04": _fact("F04", "A servo from Hitachi was fitted to the display case."),
}


def arch(**over) -> dict:
    a = {
        "article_type": "NARRATIVE_ARTICLE",
        "story_spine": "The council published a ranking sheet and ten entries were "
                       "photographed.",
        "opening_object_or_event": "the ranking sheet",
        "reader_initial_state": "a ranking sheet exists",
        "lens_realization": "IMPLICIT",
        "crip_turn_rereads": "B1",
        "turn": "",
        "crip_turn": "The ranking sheet records what could be photographed.",
        "ending_move": "the catalogue closes",
        "beats": [
            {"beat_id": "B1", "happens": "The council published a ranking sheet in March.",
             "concrete_carrier": "the ranking sheet", "facts_allowed": ["F01"],
             "concept_introduced": "", "beat_function": "REVEAL",
             "why_reader_wants_next": "the sheet leads to the entries",
             "must_not_say_yet": "the catalogue"},
            {"beat_id": "B2", "happens": "Ten entries were photographed for the catalogue.",
             "concrete_carrier": "the entry photographs", "facts_allowed": ["F02", "F01"],
             "concept_introduced": "", "beat_function": "REVEAL",
             "why_reader_wants_next": "the photographs lead to the printing",
             "must_not_say_yet": "the printer"},
            {"beat_id": "B3", "happens": "The catalogue was printed by a local firm.",
             "concrete_carrier": "the ranking sheet", "facts_allowed": ["F03", "F01"],
             "concept_introduced": "", "beat_function": "REVEAL",
             "why_reader_wants_next": "", "must_not_say_yet": ""},
        ],
        "use_facts": ["F01", "F02", "F03"],
        "primary_carrier": "F01",
        "evidence_roles": {"F01": "LOAD_BEARING", "F02": "SUPPORTING",
                           "F03": "SUPPORTING"},
        "supports": {"F02": ["F01"], "F03": ["F01"]},
        "use_quotes": [],
        "definitions": {},
        "cut_evidence": [{"evidence_id": "F04", "reason": "REDUNDANT_PROOF"}],
        "prohibitions": ["Do not invent a witness."],
        "final_lens": {
            "lens_claim": "A ranking sheet records what could be photographed.",
            "evidence_basis": ["F01", "F02"],
            "what_changes_for_the_reader": "the reader now understands the sheet as a "
                                           "record of photographability",
            "story_beat_before": "B1",
            "crip_turn": "The ranking sheet records what could be photographed.",
            "story_beat_after": "B3",
            "before_reading": "a ranking of design",
            "after_reading": "a ranking of photographability",
            "crip_turn_carrier": "the ranking sheet",
        },
    }
    a.update(over)
    return copy.deepcopy(a)


def support(a):
    return ST.validate_definition_support(a, LEDGER)


# ══ CURRENT_CONTRACT ══════════════════════════════════════════════════════════
def test_CURRENT_CONTRACT_no_definitions_is_unchanged():
    check("an architecture with no definitions passes whole",
          CP.check_architecture(arch(), LEDGER) == [],
          CP.check_architecture(arch(), LEDGER))
    check("and the validator returns nothing to say", support(arch()) == [])
    check("an empty definitions map is equally silent",
          support(arch(definitions={})) == [])


def test_CURRENT_CONTRACT_definition_with_valid_explicit_evidence_passes():
    a = arch(definitions={"ranking sheet": "the list a council publishes in March"},
             definition_evidence={"ranking sheet": ["F01"]})
    check("a gloss licensed by the fact it declares is accepted", support(a) == [],
          support(a))
    check("and check_architecture accepts the architecture whole",
          CP.check_architecture(a, LEDGER) == [], CP.check_architecture(a, LEDGER))


def test_CURRENT_CONTRACT_missing_declaration_is_refused():
    """The correction. A used definition must say what licenses it -- always, not only
    when the gloss looks risky."""
    a = arch(definitions={"ranking sheet": "the list a council publishes"})
    check("a definition with no definition_evidence at all is refused",
          any("declares no evidence" in e for e in support(a)), support(a))

    a = arch(definitions={"ranking sheet": "the list a council publishes"},
             definition_evidence={})
    check("an empty definition_evidence map is refused",
          any("declares no evidence" in e for e in support(a)), support(a))

    a = arch(definitions={"ranking sheet": "the list a council publishes",
                          "catalogue": "the printed book"},
             definition_evidence={"ranking sheet": ["F01"]})
    errs = support(a)
    check("declaring one term but not the other refuses only the undeclared one",
          any("'catalogue'" in e and "declares no evidence" in e for e in errs)
          and not any("'ranking sheet'" in e for e in errs), errs)

    a = arch(definitions={"ranking sheet": "the list a council publishes"},
             definition_evidence={"ranking sheet": []})
    check("an empty id list is refused",
          any("declares no evidence" in e for e in support(a)), support(a))

    a = arch(definitions={"ranking sheet": "the list a council publishes"},
             definition_evidence={"nothing here": ["F01"]})
    check("evidence declared for a term that is not defined is refused",
          any("not defined" in e for e in support(a)), support(a))


def test_CURRENT_CONTRACT_a_broad_pool_licenses_nothing():
    """The exact hole the first fix left. F04 carries 'Hitachi'; it is CUT, and even a
    USED neighbour would not license a gloss that does not declare it."""
    a = arch(definitions={
        "servo": "a small motor from Hitachi that turns to a commanded angle in 45 "
                 "milliseconds and holds there under 12 kg of load"},
        definition_evidence={"servo": ["F01"]})
    errs = support(a)
    check("the invented numbers are named against the DECLARED fact",
          any("45" in e and "12" in e and "['F01']" in e for e in errs), errs)
    check("the invented brand is named",
          any("Hitachi" in e for e in errs), errs)
    check("and check_architecture refuses the architecture",
          any("DEFINITION_SUPPORT" in e for e in CP.check_architecture(a, LEDGER)),
          CP.check_architecture(a, LEDGER))

    # The superlative case the held-out gloss is made of, on the current contract.
    a = arch(definitions={"block group": "the smallest area the survey publishes for"},
             definition_evidence={"block group": ["F01"]})
    check("a superlative no declared fact states is refused",
          any("SUPERLATIVE" in e for e in support(a)), support(a))


def test_CURRENT_CONTRACT_unusable_ids_are_refused():
    a = arch(definitions={"servo": "a part fitted to a display case"},
             definition_evidence={"servo": ["F99"]})
    check("a fact id that is not in the ledger is refused",
          any("not in the ledger" in e for e in support(a)), support(a))

    a = arch(definitions={"servo": "a part fitted to a display case"},
             definition_evidence={"servo": ["F04"]})
    check("a fact the architecture CUT is refused",
          any("which the architecture CUT" in e for e in support(a)), support(a))
    check("  and a CUT fact cannot license the gloss's surface either",
          not any("Hitachi" in e for e in support(a)), support(a))

    a = arch(definitions={"servo": "a part fitted to a display case"},
             definition_evidence={"servo": ["F01", "F99"]})
    check("one good id does not excuse an unresolvable one",
          any("F99" in e for e in support(a)), support(a))


def test_CURRENT_CONTRACT_an_empty_gloss_is_refused():
    check("an empty definition is refused",
          any("is empty" in e for e in support(
              arch(definitions={"servo": "  "},
                   definition_evidence={"servo": ["F01"]}))))


def test_CURRENT_CONTRACT_a_hold_needs_no_licence():
    a = arch(article_type=ST.HOLD_NO_STORY,
             definitions={"servo": "a motor from Hitachi rated at 12 kg"})
    check("a HOLD is exempt", support(a) == [], support(a))


def test_CURRENT_CONTRACT_architect_output_is_never_checked_as_legacy():
    """check_architecture defaults to the current contract, so a NEW architecture that
    omits the field is refused however it reached the gate."""
    a = arch(definitions={"ranking sheet": "the list a council publishes"})
    check("the default contract is CURRENT", CP.CONTRACT_CURRENT == "CURRENT")
    check("an undeclared definition is refused under the default",
          any("DEFINITION_SUPPORT" in e for e in CP.check_architecture(a, LEDGER)),
          CP.check_architecture(a, LEDGER))
    check("the schema demands one entry for every term",
          "REQUIRED: one entry for EVERY term" in CP.ARCHITECT_SCHEMA)


# ══ HISTORICAL_COMPATIBILITY ══════════════════════════════════════════════════
# Replay only. These assert what a REPLAY of a stored pre-`definition_evidence`
# architecture does. None of them is a statement about what new work may do.
def test_HISTORICAL_COMPATIBILITY_replay_accepts_a_pre_field_architecture():
    a = arch(definitions={"ranking sheet": "the list a council publishes"})
    check("the architecture is recognised as predating the field",
          ST.definitions_predate_evidence_binding(a))
    check("replay accepts it",
          ST.validate_definition_support(a, LEDGER, legacy_replay=True) == [],
          ST.validate_definition_support(a, LEDGER, legacy_replay=True))
    check("  and the SAME architecture is refused under the current contract",
          any("declares no evidence" in e for e in support(a)), support(a))
    check("check_architecture takes the path only when asked",
          any("DEFINITION_SUPPORT" in e for e in CP.check_architecture(a, LEDGER))
          and not any("DEFINITION_SUPPORT" in e for e in CP.check_architecture(
              a, LEDGER, contract=CP.CONTRACT_LEGACY_REPLAY)))


def test_HISTORICAL_COMPATIBILITY_is_not_a_way_back_to_the_fallback():
    """The compatibility path applies ONLY where the field is absent altogether. An author
    who declared the field knew about it and is held to the current contract."""
    a = arch(definitions={"a": "gloss one", "b": "gloss two"},
             definition_evidence={"a": ["F01"]})
    check("a partially-declared architecture does not predate the field",
          not ST.definitions_predate_evidence_binding(a))
    check("and replay still refuses its undeclared term",
          any("'b'" in e and "declares no evidence" in e
              for e in ST.validate_definition_support(a, LEDGER, legacy_replay=True)),
          ST.validate_definition_support(a, LEDGER, legacy_replay=True))

    a = arch(definitions={"servo": "a motor from Hitachi rated at 12 kg"},
             definition_evidence={"servo": ["F01"]})
    check("replay does not excuse an unlicensed surface where evidence WAS declared",
          ST.validate_definition_support(a, LEDGER, legacy_replay=True) != [],
          ST.validate_definition_support(a, LEDGER, legacy_replay=True))


def test_HISTORICAL_COMPATIBILITY_the_held_out_artefact_is_a_diagnostic():
    """The manual baseline that produced the published article. It now FAILS the current
    contract, and that is the correct result: its "block group" gloss asserts a superlative
    its own frozen evidence never states. Kept as a diagnostic, not as an acceptance
    control -- having been published once is not evidence, and it must not be able to force
    the contract to accept an unsupported gloss."""
    d = (pathlib.Path(__file__).resolve().parents[1]
         / ".claude" / "story-architecture" / "held-out-real-article-1")
    af, mf = d / "ARCHITECTURE.json", d / "FINAL_EVIDENCE_MANIFEST.json"
    if not (af.exists() and mf.exists()):
        check("held-out real architecture present", False, "missing %s" % d)
        return
    a = json.loads(af.read_text())
    facts = json.loads(mf.read_text())["facts"]
    led = facts if isinstance(facts, dict) else {f["fact_id"]: f for f in facts}

    check("it predates the field", ST.definitions_predate_evidence_binding(a))
    cur = ST.validate_definition_support(a, led)
    check("under the CURRENT contract it is refused, for want of a declaration",
          all("declares no evidence" in e for e in cur) and len(cur) == 2, cur)
    check("a replay of it is accepted",
          ST.validate_definition_support(a, led, legacy_replay=True) == [])

    # The diagnostic proper: declaring the most plausible ids does not rescue the gloss,
    # because nothing in the frozen evidence states the superlative it asserts.
    plausible = dict(a, definition_evidence={
        "rent burden": ["F16", "F21"], "block group": ["F19"]})
    errs = ST.validate_definition_support(plausible, led)
    check("and declaring its own most plausible facts still refuses 'block group'",
          any("'block group'" in e and "SUPERLATIVE" in e for e in errs), errs)
    check("  while 'rent burden' is licensed by the facts it rests on",
          not any("'rent burden'" in e for e in errs), errs)


def main():
    for fn in (test_CURRENT_CONTRACT_no_definitions_is_unchanged,
               test_CURRENT_CONTRACT_definition_with_valid_explicit_evidence_passes,
               test_CURRENT_CONTRACT_missing_declaration_is_refused,
               test_CURRENT_CONTRACT_a_broad_pool_licenses_nothing,
               test_CURRENT_CONTRACT_unusable_ids_are_refused,
               test_CURRENT_CONTRACT_an_empty_gloss_is_refused,
               test_CURRENT_CONTRACT_a_hold_needs_no_licence,
               test_CURRENT_CONTRACT_architect_output_is_never_checked_as_legacy,
               test_HISTORICAL_COMPATIBILITY_replay_accepts_a_pre_field_architecture,
               test_HISTORICAL_COMPATIBILITY_is_not_a_way_back_to_the_fallback,
               test_HISTORICAL_COMPATIBILITY_the_held_out_artefact_is_a_diagnostic):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL DEFINITION SUPPORT TESTS PASSED")


if __name__ == "__main__":
    main()
