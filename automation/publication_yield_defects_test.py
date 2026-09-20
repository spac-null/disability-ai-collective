#!/usr/bin/env python3
"""publication_yield_defects_test.py -- two measuring errors that cost publication days.

An audit of the last 20 terminal production attempts (2026-09-20) found zero publications
since the commissioning-day record begins, and two of the terminal holds were the
machinery mis-measuring correct work rather than the work being wrong:

  1. story_spine length counted `spine.split(".")`, so decimal points and dotted
     abbreviations read as sentence ends. production-20260920T074108Z-f1a93cd8 lost the
     day to a one-sentence spine containing 13.8% and 21.3%;
     production-20260905T212756Z-d1d8a8d5 hit the same check on "U.S. Senate".

  2. negative_admission_audit drew its candidate facts from `claim_type in
     NEGATIVE_TYPES`, so a Ledger fact whose PROPOSITION states the absence in so many
     words was invisible whenever the Ledger had typed it POSITIVE_FACT or ATTRIBUTION.
     Measured on production-20260919T070300Z-faa849c8 (F18, F60),
     production-20260910T073435Z-703b7b90 (F39) and
     production-20260910T175526Z-757004af (F23).

The assertions that matter here are the negative ones. A spine that really is three
sentences must still fail; a negation with nothing behind it must still hold; and an
ATTRIBUTION fact must not license prose that drops the attribution and asserts the
absence flatly. Without those this file would prove only that the gates got quieter.

Stdlib only, no provider, no network.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import story as ST

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


def arch(spine):
    """A structurally valid architecture whose only variable is the spine."""
    return {
        "article_type": ST.NARRATIVE_ARTICLE,
        "story_spine": spine,
        "opening_object_or_event": "a treadmill in a Devon exercise lab",
        "beats": [
            {"beat_id": "B1", "concrete_carrier": "the second test",
             "why_reader_wants_next": "the number falls", "facts_allowed": ["F1"]},
            {"beat_id": "B2", "concrete_carrier": "the recovery chart",
             "facts_allowed": ["F2"]},
        ],
    }


def spine_errors(spine):
    return [e for e in ST.validate_architecture(arch(spine), {"F1", "F2"})
            if "story_spine" in e]


# ── 1. A FULL STOP IS NOT ALWAYS A SENTENCE END ──────────────────────────────
def test_decimals_do_not_end_a_sentence():
    """The exact spine that cost 2026-09-20."""
    spine = ("A study of 22 ME/CFS patients recorded a 13.8% fall in VO2peak and a 21.3% "
             "fall in work at the ventilatory threshold on a second cardiopulmonary "
             "exercise test 24 hours later.")
    check("two decimals count as one sentence", ST.sentence_count(spine) == 1,
          "got %d" % ST.sentence_count(spine))
    check("the 2026-09-20 spine validates", spine_errors(spine) == [],
          str(spine_errors(spine)))


def test_abbreviations_do_not_end_a_sentence():
    """The same check on production-20260905T212756Z-d1d8a8d5."""
    spine = ("Angie Nixon's Northwest Jacksonville bookstore now also supplies food, "
             "health sessions, tutoring and music lessons while she runs for the U.S. "
             "Senate against Ashley Moody.")
    check("a dotted abbreviation counts as one sentence", ST.sentence_count(spine) == 1,
          "got %d" % ST.sentence_count(spine))
    check("the 2026-09-05 spine validates", spine_errors(spine) == [],
          str(spine_errors(spine)))
    for s, n in [("Payment resumed at 9 a.m. on the Monday.", 1),
                 ("The trust, i.e. the Royal Devon, had no pathway.", 1),
                 ("Dr. Shenton told the inquest doctors needed help.", 1)]:
        check("one sentence: %r" % s[:34], ST.sentence_count(s) == n,
              "got %d" % ST.sentence_count(s))


def test_a_spine_that_really_is_several_sentences_still_fails():
    """THE TOLERANCE IS UNCHANGED. split(".") > 3 admitted at most two full stops."""
    check("one sentence passes", spine_errors("The second test is the measurement.") == [])
    check("two sentences still pass (as before)",
          spine_errors("The second test is the measurement. The first is not.") == [])
    three = ("The second test is the measurement. The first is not. "
             "The gap between them is the disease.")
    check("three sentences still fail", spine_errors(three) != [], str(spine_errors(three)))
    four = ("One thing. Then another. Then a third. And a fourth.")
    check("four sentences still fail", spine_errors(four) != [])
    check("a three-sentence spine carrying decimals still fails",
          spine_errors("VO2peak fell 13.8%. Work fell 21.3%. The patients did not "
                       "recover.") != [])
    check("an empty spine is still missing",
          any("missing" in e for e in spine_errors("")), str(spine_errors("")))


# ── 2. THE NEGATION IS IN THE PROPOSITION, NOT IN THE TYPE LABEL ─────────────
F18 = {"fact_id": "F18", "claim_type": "POSITIVE_FACT",
       "proposition": "The admissions were unsuccessful in preventing Maeve from "
                      "suffering from malnutrition, which was a consequence of her ME, "
                      "for which there is no known cure."}
F60 = {"fact_id": "F60", "claim_type": "ATTRIBUTION",
       "proposition": "The coroner said in conclusion there is no known treatment of ME, "
                      "and that it was not possible for her to say if any treatment could "
                      "have halted the decline."}
F01 = {"fact_id": "F01", "claim_type": "POSITIVE_FACT",
       "proposition": "Maeve Boothby O'Neill was admitted to the Royal Devon and Exeter "
                      "Hospital three times in 2021."}

SENT_18 = ("The admissions were unsuccessful in preventing her from suffering "
           "malnutrition, which was a consequence of her ME, for which there is no known "
           "cure.")
SENT_60 = ("The coroner said in conclusion that there is no known treatment of ME, and "
           "that it was not possible for her to say if any treatment could have halted "
           "the decline.")


def test_a_positive_typed_fact_that_states_the_absence_licenses_it():
    """production-20260919T070300Z-faa849c8, F18. Same clause, 0.91 word overlap."""
    a = ST.negative_admission_audit(SENT_18, {"F18": F18, "F01": F01})
    check("the sentence is still seen as negative-shaped", a["negative_sentences"] == 1)
    check("F18 licenses it", a["ok"], str(a["unmatched"]))
    check("F18 is reported as a negation-carrying fact",
          a["negation_carrying_facts"] == ["F18"], str(a["negation_carrying_facts"]))
    check("it is not counted among the negative-TYPED facts",
          a["negative_facts_available"] == [], str(a["negative_facts_available"]))


def test_an_attribution_fact_licenses_an_attributed_sentence_only():
    """F60 grants what the coroner SAID. It does not grant the bare absence."""
    ok = ST.negative_admission_audit(SENT_60, {"F60": F60, "F01": F01})
    check("the attributed sentence is licensed", ok["ok"], str(ok["unmatched"]))
    stripped = ("In conclusion there is no known treatment of ME, and it was not possible "
                "to say if any treatment could have halted the decline.")
    bad = ST.negative_admission_audit(stripped, {"F60": F60, "F01": F01})
    check("dropping the attribution is NOT licensed", not bad["ok"])
    check("and it is reported as a citation problem, not an invention",
          [h["basis"] for h in bad["unmatched"]] == [ST.MISSING_CITED_BASIS],
          str([h.get("basis") for h in bad["unmatched"]]))


def test_a_negation_with_nothing_behind_it_still_holds():
    """The assertion that matters. A Ledger with no negation anywhere must still block."""
    sent = "There is no objective clinical biomarker for identifying the injury."
    a = ST.negative_admission_audit(sent, {"F01": F01})
    check("an unsupported negative still holds", not a["ok"])
    check("and is named NO_EVIDENCE_SUPPORT",
          [h["basis"] for h in a["unmatched"]] == [ST.NO_EVIDENCE_SUPPORT],
          str([h.get("basis") for h in a["unmatched"]]))
    check("an empty ledger blocks it too",
          not ST.negative_admission_audit(sent, {})["ok"])


def test_an_unrelated_negation_does_not_license_a_different_one():
    """A fact must carry THIS negation, not merely some negation."""
    unrelated = {"fact_id": "F99", "claim_type": "NEGATIVE_EXISTENCE",
                 "proposition": "There were no specialist hospices, wards or beds in "
                                "England for patients with severe myalgic "
                                "encephalomyelitis."}
    sent = "There is no objective clinical biomarker for identifying paediatric "\
           "concussion in injured children."
    a = ST.negative_admission_audit(sent, {"F99": unrelated})
    check("an unrelated negation does not license it", not a["ok"], str(a["unmatched"]))


def test_negative_typed_facts_still_work_exactly_as_before():
    """The original pool is untouched; this is an addition, not a replacement."""
    neg = {"fact_id": "F20", "claim_type": "NEGATIVE_EXISTENCE",
           "proposition": "The evidence made clear there were no specialist hospitals or "
                          "hospices, beds or wards in England for patients with severe "
                          "myalgic encephalomyelitis."}
    sent = ("There were no specialist hospitals or hospices, no beds and no wards in "
            "England for patients with severe myalgic encephalomyelitis.")
    a = ST.negative_admission_audit(sent, {"F20": neg})
    check("a NEGATIVE_EXISTENCE fact still licenses its sentence", a["ok"],
          str(a["unmatched"]))
    check("and is still reported in negative_facts_available",
          a["negative_facts_available"] == ["F20"])


# ── 3. PRODUCTION OWNS THE SUBSCRIPTION BETWEEN 08:45 AND 10:00 ──────────────
def test_the_production_window_guard():
    import datetime as _dt
    import production_window_guard as PW

    def at(h, m):
        return _dt.datetime(2026, 9, 21, h, m)

    check("08:44 is outside", not PW.in_production_window(at(8, 44)))
    check("08:45 is inside", PW.in_production_window(at(8, 45)))
    check("09:00 is inside", PW.in_production_window(at(9, 0)))
    check("09:59 is inside", PW.in_production_window(at(9, 59)))
    check("10:00 is outside", not PW.in_production_window(at(10, 0)))
    try:
        PW.assert_outside_production_window("a replay", at(9, 10))
        raised = False
    except PW.ProductionWindowBusy:
        raised = True
    check("an automated job inside the window is refused", raised)
    PW.assert_outside_production_window("a replay", at(11, 0))
    check("and is allowed outside it", True)
    os.environ[PW.OVERRIDE_ENV] = "1"
    try:
        PW.assert_outside_production_window("a replay", at(9, 10))
        check("the override is honoured", True)
    except PW.ProductionWindowBusy:
        check("the override is honoured", False)
    finally:
        del os.environ[PW.OVERRIDE_ENV]


def main():
    for fn in (test_decimals_do_not_end_a_sentence,
               test_abbreviations_do_not_end_a_sentence,
               test_a_spine_that_really_is_several_sentences_still_fails,
               test_a_positive_typed_fact_that_states_the_absence_licenses_it,
               test_an_attribution_fact_licenses_an_attributed_sentence_only,
               test_a_negation_with_nothing_behind_it_still_holds,
               test_an_unrelated_negation_does_not_license_a_different_one,
               test_negative_typed_facts_still_work_exactly_as_before,
               test_the_production_window_guard):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    print("%d checks" % CHECKS[0])
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL PUBLICATION YIELD DEFECT TESTS PASSED")


if __name__ == "__main__":
    main()
