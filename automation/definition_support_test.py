#!/usr/bin/env python3
"""
definition_support_test.py -- a definition may not assert what a beat could not.

`definitions` was the one architect-generated field with no factual screen anywhere. It
is not in architect_prose_audit's field list, so its numbers and entities were never
compared to the approved facts. It is not among the three fields validate_turn_support
covers, so the relations it asserts were never licensed. And render() hands it to the
Writer under EXPLAIN AT FIRST USE, which is an instruction to state it.

Measured on 2026-09-23 against 2e96aa7: an architecture whose only change from a clean
control was

    {"servo": "a small motor from Hitachi that turns to a commanded angle in 45
              milliseconds and holds there under 12 kg of load"}

passed check_architecture with ZERO errors. The same brand and numbers in `story_spine`
or a beat's `happens` are caught. A definition was the way round every gate in the engine.

THE ACCEPTANCE SIDE MATTERS AS MUCH AS THE REFUSAL SIDE, and it is not hypothetical here:
the last test in this file runs the real held-out architecture -- the manual baseline that
produced the published article -- against the real frozen evidence manifest. A first
version of this check used an empty licensing set when no `definition_evidence` was
declared, and that version refused it. That is how the licensing set came to be the same
one the crip turn already gets.

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


# ── the measured counterexample ───────────────────────────────────────────────
def test_the_control_is_clean():
    check("the control architecture passes check_architecture whole",
          CP.check_architecture(arch(), LEDGER) == [],
          CP.check_architecture(arch(), LEDGER))


def test_an_unsupported_definition_is_refused():
    a = arch(definitions={
        "servo": "a small motor from Hitachi that turns to a commanded angle in 45 "
                 "milliseconds and holds there under 12 kg of load"})
    errs = support(a)
    check("the invented numbers are named",
          any("45" in e and "12" in e for e in errs), errs)
    check("the invented brand is named",
          any("Hitachi" in e for e in errs), errs)
    check("and check_architecture refuses the architecture",
          any("DEFINITION_SUPPORT" in e for e in CP.check_architecture(a, LEDGER)),
          CP.check_architecture(a, LEDGER))


def test_a_plain_words_gloss_needs_no_fact():
    """The legitimate and expected use. Nothing here is a glossary policy."""
    a = arch(definitions={
        "ranking sheet": "the list a council publishes to say which entries it rates",
        "catalogue": "the printed book an entry has to appear in to be seen"})
    check("a gloss with no number, name or relation is accepted", support(a) == [],
          support(a))


# ── the declared binding ──────────────────────────────────────────────────────
def test_declared_ids_must_be_real_used_and_uncut():
    a = arch(definitions={"servo": "a part fitted to a display case"},
             definition_evidence={"servo": ["F99"]})
    check("a fact id that is not in the ledger is refused",
          any("not in the ledger" in e for e in support(a)), support(a))

    a = arch(definitions={"servo": "a part fitted to a display case"},
             definition_evidence={"servo": ["F04"]})
    check("a fact the architecture CUT is refused",
          any("which the architecture CUT" in e for e in support(a)), support(a))

    a = arch(definitions={"servo": "a part fitted to a display case"},
             definition_evidence={"nothing here": ["F01"]})
    check("evidence declared for a term that is not defined is refused",
          any("not defined" in e for e in support(a)), support(a))


def test_a_declared_id_narrows_the_licence():
    """Naming ids is a NARROWING declaration: it must license the gloss by itself."""
    a = arch(definitions={"firm": "the local firm that printed the catalogue"},
             definition_evidence={"firm": ["F03"]})
    check("a gloss licensed by the fact it declares is accepted", support(a) == [],
          support(a))

    # F02 carries the entry count; F03, the declared id, does not. Under the use_facts
    # fallback this gloss would pass, because F02 is used. Declaring F03 narrows the
    # licence to F03 alone, and the gloss then fails on a fact F03 does not carry.
    a = arch(definitions={"firm": "the firm that printed the 10 photographed entries"},
             definition_evidence={"firm": ["F03"]})
    check("a gloss whose number the DECLARED fact does not carry is refused",
          any("do not carry" in e for e in support(a)), support(a))
    check("  and the message names the declared ids, not 'the used facts'",
          any("['F03']" in e for e in support(a)), support(a))
    check("  while the same gloss passes on the use_facts fallback",
          ST.validate_definition_support(
              arch(definitions={"firm": "the firm that printed the 10 photographed "
                                        "entries"}), dict(LEDGER, F02=_fact(
                                            "F02", "10 entries were photographed for "
                                                   "the catalogue."))) == [],
          "narrowing must be the strictly tighter option")


def test_an_empty_gloss_is_refused():
    check("an empty definition is refused",
          any("is empty" in e for e in support(arch(definitions={"servo": "  "}))))


def test_a_hold_needs_no_definitions_licence():
    a = arch(article_type=ST.HOLD_NO_STORY,
             definitions={"servo": "a motor from Hitachi rated at 12 kg"})
    check("a HOLD is exempt", support(a) == [], support(a))


# ── the acceptance control that shaped the design ─────────────────────────────
def test_the_held_out_real_architecture_is_still_accepted():
    """The manual baseline that produced the published article, against its own frozen
    evidence. If this ever goes red, the check has started refusing a proven plan."""
    d = (pathlib.Path(__file__).resolve().parents[1]
         / ".claude" / "story-architecture" / "held-out-real-article-1")
    af, mf = d / "ARCHITECTURE.json", d / "FINAL_EVIDENCE_MANIFEST.json"
    if not (af.exists() and mf.exists()):
        check("held-out real architecture present", False, "missing %s" % d)
        return
    a = json.loads(af.read_text())
    facts = json.loads(mf.read_text())["facts"]
    led = facts if isinstance(facts, dict) else {f["fact_id"]: f for f in facts}

    check("it declares definitions at all", bool(a.get("definitions")),
          a.get("definitions"))
    errs = ST.validate_definition_support(a, led)
    check("its definitions are accepted against its own frozen evidence", errs == [],
          errs)
    check("  and it declares no definition_evidence, so the fallback is what carried it",
          not a.get("definition_evidence"), a.get("definition_evidence"))


def main():
    for fn in (test_the_control_is_clean,
               test_an_unsupported_definition_is_refused,
               test_a_plain_words_gloss_needs_no_fact,
               test_declared_ids_must_be_real_used_and_uncut,
               test_a_declared_id_narrows_the_licence,
               test_an_empty_gloss_is_refused,
               test_a_hold_needs_no_definitions_licence,
               test_the_held_out_real_architecture_is_still_accepted):
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
