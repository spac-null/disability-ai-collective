#!/usr/bin/env python3
"""Targeted regressions for EVENT_CONTEXT_BINDING, built from the real immigration
Grounding finding (Swalwell's Monday Hayward quote implied to belong to the Friday
Los Angeles press conference). No provider, no network."""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import fast_lane_v1 as FL                                 # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                           "" if ok else " <- %r" % detail))
    if not ok:
        FAILURES.append(label)


LEDGER = {
    "F35": {"entities": ["Nikolas De Bremaeker", "Tony Thurmond"],
           "claim_type": "POSITIVE_FACT",
           "proposition": "De Bremaeker and Thurmond held a news conference in "
                          "Los Angeles.",
           "support_span": "", "scope": "WORLD"},
    "F36": {"entities": ["Tony Thurmond"], "claim_type": "ATTRIBUTION",
           "proposition": "Thurmond expressed outrage and reached out to "
                          "Swalwell's office.",
           "support_span": "", "scope": "WORLD"},
    "F38": {"entities": ["Eric Swalwell"], "claim_type": "ATTRIBUTION",
           "proposition": "Swalwell said 'if you're coming for a 6-year-old, you "
                          "have to go through us.'",
           "support_span": "", "scope": "WORLD"},
}
ALLOWED = set(LEDGER)
FACT_STATUS = {
    "F35": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "temporal_permission": "NONE", "event_id": "EVENT_A",
           "event_date": "Friday", "event_location": "Los Angeles"},
    "F36": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Tony Thurmond",
           "temporal_permission": "NONE", "event_id": "EVENT_A",
           "event_date": "Friday", "event_location": "Los Angeles"},
    "F38": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Eric Swalwell",
           "temporal_permission": "NONE", "event_id": "EVENT_B",
           "event_date": "Monday", "event_location": "Hayward"},
}


def test_a_mixed_events_under_one_event_label_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "A", "fact_ids": ["F35", "F38"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Eric Swalwell", "event_id": "EVENT_A"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("A: a fact from EVENT_A and a fact from EVENT_B both labeled EVENT_A "
          "fails", len(errs) == 1 and "belong to event(s)" in errs[0], errs)


def test_b_event_b_borrows_event_a_date_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "B", "fact_ids": ["F38"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Eric Swalwell", "event_id": "EVENT_B",
          "qualifiers": "Friday"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("B: EVENT_B's sentence borrowing EVENT_A's own date ('Friday') fails",
          len(errs) == 1 and "not this event's" in errs[0], errs)


def test_c_separate_events_with_explicit_transition_passes():
    errs = FL.validate_claim_map(
        [{"sentence_id": "C", "fact_ids": ["F38"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Eric Swalwell", "event_id": "EVENT_B",
          "qualifiers": "Monday", "event_transition": True,
          "context_anchor_fact_ids": ["F38"]}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("C: EVENT_B disambiguated with its own licensed date and an anchor "
          "drawn from its own cited facts passes", errs == [], errs)


def test_d_same_event_two_facts_passes_without_forced_transition():
    errs = FL.validate_claim_map(
        [{"sentence_id": "D", "fact_ids": ["F35", "F36"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Tony Thurmond", "event_id": "EVENT_A",
          "event_transition": False}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("D: two facts genuinely from the same event pass with no transition "
          "language forced", errs == [], errs)


def test_e_separate_events_do_not_license_temporal_relation():
    errs = FL.validate_claim_map(
        [{"sentence_id": "E", "fact_ids": ["F35", "F38"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Eric Swalwell", "temporal_relation": "AFTER"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("E: two separately-dated events do not license an unpermitted "
          "temporal_relation (reuses the existing temporal_permission check)",
          len(errs) == 1 and "not licensed" in errs[0], errs)


def main() -> None:
    for test in (test_a_mixed_events_under_one_event_label_fails,
                 test_b_event_b_borrows_event_a_date_fails,
                 test_c_separate_events_with_explicit_transition_passes,
                 test_d_same_event_two_facts_passes_without_forced_transition,
                 test_e_separate_events_do_not_license_temporal_relation):
        print("\n" + test.__name__)
        test()
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("\nALL PASS")


if __name__ == "__main__":
    main()
