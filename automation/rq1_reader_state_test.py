#!/usr/bin/env python3
"""
rq1_reader_state_test.py -- tests for the RQ-1 EXPERIMENTAL reader-state contract.

Local to the experiment. Nothing here tests or constrains authoritative generation.
The contract's whole purpose is to be falsifiable, so most of these tests are attempts to
smuggle something past it.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rq1_reader_state as RS                                    # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print("  PASS  " + label)
    else:
        FAILURES.append(label)
        print("  FAIL  %s   <- %s" % (label, detail))


def test_none_is_first_class():
    """A plan may move with no reader question at all. This is the guard against Q&A."""
    plan = [{"section_id": "S1", "reader_knows_entering": [],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": "CONTINUES"},
            {"section_id": "S2", "reader_knows_entering": ["a room of salt bricks"],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": "CHANGES_SCALE"},
            {"section_id": "S3", "reader_knows_entering": ["a room of salt bricks"],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": ""}]
    facts = [["a room was built of salt bricks"], ["the festival ran five days"], ["the account named eight"]]
    check("a plan with no questions anywhere is valid",
          RS.validate_reader_state(plan, facts) == [],
          RS.validate_reader_state(plan, facts))
    check("  and its questionless share is reported as total",
          RS.questionless_share(plan) == 1.0)


def test_a_questionless_section_may_not_claim_to_answer():
    plan = [{"section_id": "S1", "reader_knows_entering": [],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": "ANSWERS"}]
    errs = RS.validate_reader_state(plan, [["a room was built of salt"]])
    check("no question + ANSWERS is rejected", len(errs) == 1 and "no active question" in errs[0], errs)


def test_an_open_question_may_not_be_left_unserved():
    plan = [{"section_id": "S1", "reader_knows_entering": [],
             "reader_now_wonders_leaving": "what was it for", "next_move_relation": "CONTINUES"}]
    errs = RS.validate_reader_state(plan, [["a room was built of salt"]])
    check("open question + CONTINUES is rejected, with DEFERS suggested",
          errs and "DEFERS" in errs[0], errs)
    plan[0]["next_move_relation"] = "DEFERS"
    check("  and DEFERS is accepted for a deliberate delay",
          RS.validate_reader_state(plan, [["a room was built of salt"]]) == [])


def test_reader_knows_cannot_contain_undelivered_material():
    """Section 8 of the brief: the architect may not credit the reader with its own knowledge."""
    plan = [{"section_id": "S1", "reader_knows_entering": [],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": "CONTINUES"},
            {"section_id": "S2",
             "reader_knows_entering": ["the published ranking placed it among the eight most interesting"],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": "CONTINUES"}]
    facts = [["The pavilion was constructed from Himalayan salt bricks."],
             ["The pavilion was partially embedded into the ground."]]
    errs = RS.validate_reader_state(plan, facts)
    check("future knowledge in reader_knows_entering is caught", len(errs) == 1, errs)
    check("  and the message says how much was unrecoverable",
          errs and "content words appear in any fact delivered" in errs[0], errs)


def test_knowledge_is_checked_against_facts_not_summaries():
    """The bug this test exists for: a terse section summary does not contain the words of
    the fact it delivers, so checking against summaries produced false violations."""
    plan = [{"section_id": "S1", "reader_knows_entering": [],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": "CONTINUES"},
            {"section_id": "S2",
             "reader_knows_entering": ["the festival ran from 13 to 17 August at Pengembak Beach in Sanur"],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": "CONTINUES"}]
    facts = [["The festival ran from 13 to 17 August at Pengembak Beach in Sanur, on Bali's eastern shoreline."],
             ["The pavilion was constructed from Himalayan salt bricks."]]
    check("knowledge delivered by a fact is recognised even when no summary repeats it",
          RS.validate_reader_state(plan, facts) == [],
          RS.validate_reader_state(plan, facts))


def test_first_section_enters_empty():
    plan = [{"section_id": "S1", "reader_knows_entering": ["something the reader was never told"],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": "CONTINUES"}]
    errs = RS.validate_reader_state(plan, [["a room was built of salt"]])
    check("the opening section cannot enter with prior knowledge",
          errs and "cannot enter with the reader already knowing" in errs[0], errs)


def test_relation_must_be_declared():
    plan = [{"section_id": "S1", "reader_knows_entering": [],
             "reader_now_wonders_leaving": "NONE", "next_move_relation": "BECAUSE_I_SAID_SO"}]
    errs = RS.validate_reader_state(plan, [["a room was built of salt"]])
    check("an undeclared relation is rejected", any("not in" in e for e in errs), errs)


def test_the_internal_question_must_never_reach_prose():
    """Sections 6 and 21. The experiment fails if better order arrives as more questions."""
    leaky = ("The room was built of salt. So what was it for? You might wonder whether anyone "
             "noticed. But first, go back to the sand. Which brings us to the account.")
    hits = RS.question_serialization(leaky)
    kinds = {h["kind"] for h in hits}
    check("rhetorical so-what is caught", "rhetorical so-what" in kinds, kinds)
    check("reader address is caught", "reader address" in kinds, kinds)
    check("outline signposts are caught", "outline signpost" in kinds, kinds)
    check("reader instruction is caught", "reader instruction" in kinds, kinds)
    clean = ("The room was built of salt bricks and set partway into the ground. Inside it held "
             "fragrances and botanical drinks. The account has a word for that surface, and the "
             "word is brick.")
    check("clean prose carrying the same information is not flagged",
          RS.question_serialization(clean) == [], RS.question_serialization(clean))
    check("  and it contains no question marks", RS.rhetorical_question_count(clean) == 0)


def test_the_module_is_not_wired_into_generation():
    """RQ-1 is an experiment. Nothing authoritative may import it."""
    root = pathlib.Path(__file__).resolve().parent
    importers = []
    for p in root.rglob("*.py"):
        if p.name.startswith("rq1_"):
            continue
        try:
            src = p.read_text()
        except Exception:
            continue
        if "rq1_reader_state" in src:
            importers.append(p.name)
    check("no non-experimental module imports the reader-state contract",
          importers == [], importers)


def main():
    for fn in (test_none_is_first_class,
               test_a_questionless_section_may_not_claim_to_answer,
               test_an_open_question_may_not_be_left_unserved,
               test_reader_knows_cannot_contain_undelivered_material,
               test_knowledge_is_checked_against_facts_not_summaries,
               test_first_section_enters_empty,
               test_relation_must_be_declared,
               test_the_internal_question_must_never_reach_prose,
               test_the_module_is_not_wired_into_generation):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL RQ-1 READER-STATE TESTS PASSED")


if __name__ == "__main__":
    main()
