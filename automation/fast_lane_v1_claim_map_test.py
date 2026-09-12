#!/usr/bin/env python3
"""Targeted regressions for the corrected CLAIM_MAP entity_owner contract: optional,
nullable, exact-match-only against the cited fact(s)' canonical Ledger entities. No
provider, no network."""
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
    "F13": {"entities": [], "proposition": "no public info", "support_span": "",
           "scope": "WORLD"},
    "F16": {"entities": ["Venezuelan Sign Language", "Mexican Sign Language",
                        "United States"],
           "proposition": "no certification", "support_span": "", "scope": "WORLD"},
    "F99": {"entities": ["United States"], "proposition": "single entity fact",
           "support_span": "", "scope": "WORLD"},
}
ALLOWED = set(LEDGER)


def test_a_entityless_fact_null_owner_passes():
    errs = FL.validate_claim_map(
        [{"sentence_id": "A", "fact_ids": ["F13"], "entity_owner": None}],
        ALLOWED, LEDGER)
    check("A: entities=[] with entity_owner=null passes", errs == [], errs)


def test_b_single_entity_exact_match_passes():
    errs = FL.validate_claim_map(
        [{"sentence_id": "B", "fact_ids": ["F99"], "entity_owner": "United States"}],
        ALLOWED, LEDGER)
    check("B: entities=['United States'] with entity_owner='United States' passes",
          errs == [], errs)


def test_c_descriptive_phrase_not_silently_canonical():
    errs = FL.validate_claim_map(
        [{"sentence_id": "C", "fact_ids": ["F99"],
          "entity_owner": "United States interpreter certification"}],
        ALLOWED, LEDGER)
    check("C: a descriptive phrase for a single-entity fact is refused, not accepted",
          len(errs) == 1 and "not the cited fact's exact canonical entity" in errs[0],
          errs)


def test_d_multi_entity_null_owner_passes():
    errs = FL.validate_claim_map(
        [{"sentence_id": "D", "fact_ids": ["F16"], "entity_owner": None,
          "scope": "general"}],
        ALLOWED, LEDGER)
    check("D: multi-entity fact with entity_owner=null (and a non-single scope "
          "label) passes -- scope isn't checked when >1 fact would need to agree",
          errs == [], errs)


def test_e_wrong_single_entity_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "E", "fact_ids": ["F99"], "entity_owner": "Wrong Entity"}],
        ALLOWED, LEDGER)
    check("E: entity_owner='Wrong Entity' for a single-entity fact fails",
          len(errs) == 1, errs)


def main() -> None:
    for test in (test_a_entityless_fact_null_owner_passes,
                 test_b_single_entity_exact_match_passes,
                 test_c_descriptive_phrase_not_silently_canonical,
                 test_d_multi_entity_null_owner_passes,
                 test_e_wrong_single_entity_fails):
        print("\n" + test.__name__)
        test()
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("\nALL PASS")


if __name__ == "__main__":
    main()
