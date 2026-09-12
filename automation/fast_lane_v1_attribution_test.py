#!/usr/bin/env python3
"""Targeted regressions for ATTRIBUTION_AND_STATUS_MUST_SURVIVE, built from the real
immigration-run defect: attributed/disputed material upgraded to settled fact, and an
invented before/after relation between two separately-dated facts. No provider, no
network."""
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
    "F47": {"entities": ["Nikolas De Bremaeker"], "claim_type": "ATTRIBUTION",
           "proposition": "attorney says she was forced to sign", "support_span": "",
           "scope": "WORLD"},
    "F41": {"entities": ["Department of Homeland Security"], "claim_type": "ATTRIBUTION",
           "proposition": "DHS says she chose removal on March 5",
           "support_span": "", "scope": "WORLD"},
    "F54": {"entities": ["Nikolas De Bremaeker"], "claim_type": "ATTRIBUTION",
           "proposition": "attorney says ICE pressured her to sign",
           "support_span": "", "scope": "WORLD"},
    "F45": {"entities": [], "claim_type": "POSITIVE_FACT",
           "proposition": "the family was deported", "support_span": "",
           "scope": "WORLD"},
    "F46": {"entities": [], "claim_type": "POSITIVE_FACT",
           "proposition": "Swalwell's staff returned hearing devices",
           "support_span": "", "scope": "WORLD"},
}
ALLOWED = set(LEDGER)
FACT_STATUS = {
    "F47": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Nikolas De Bremaeker",
           "temporal_permission": "NONE"},
    "F41": {"claim_status": FL.DISPUTED, "attribution_to":
           "Department of Homeland Security", "temporal_permission": "NONE"},
    "F54": {"claim_status": FL.DISPUTED, "attribution_to": "Nikolas De Bremaeker",
           "temporal_permission": "NONE"},
    "F45": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "temporal_permission": "NONE"},
    "F46": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "temporal_permission": "NONE"},
}


def test_a_attributed_fact_self_reported_established_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "A", "fact_ids": ["F47"], "claim_status": "ESTABLISHED"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("A: attorney-attributed fact self-reported ESTABLISHED fails",
          len(errs) == 1 and "stronger than the packet's declared status" in errs[0],
          errs)


def test_b_attributed_fact_preserved_as_attributed_passes():
    errs = FL.validate_claim_map(
        [{"sentence_id": "B", "fact_ids": ["F47"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Nikolas De Bremaeker"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("B: same fact preserved as ATTRIBUTED/attorney passes", errs == [], errs)


def test_c_disputed_dated_fact_upgraded_to_established_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "C", "fact_ids": ["F41"], "claim_status": "ESTABLISHED",
          "qualifiers": "March 5"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("C: DHS's disputed dated account upgraded to ESTABLISHED "
          "('document dated March 5') fails -- metadata cannot license it",
          len(errs) == 1 and "stronger than the packet's declared status" in errs[0],
          errs)


def test_d_invented_before_after_between_separately_dated_facts_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "D", "fact_ids": ["F45", "F46"], "claim_status": "ESTABLISHED",
          "temporal_relation": "BEFORE"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("D: BEFORE/AFTER invented between two separately-established, "
          "separately-dated facts with no temporal_permission fails",
          len(errs) == 1 and "not licensed" in errs[0], errs)


def test_e_disputed_account_preserved_passes():
    errs = FL.validate_claim_map(
        [{"sentence_id": "E1", "fact_ids": ["F41"], "claim_status": "DISPUTED",
          "attribution_to": "Department of Homeland Security"},
         {"sentence_id": "E2", "fact_ids": ["F54"], "claim_status": "DISPUTED",
          "attribution_to": "Nikolas De Bremaeker"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("E: DHS vs attorney both preserved as DISPUTED, separately attributed, "
          "passes", errs == [], errs)


def main() -> None:
    for test in (test_a_attributed_fact_self_reported_established_fails,
                 test_b_attributed_fact_preserved_as_attributed_passes,
                 test_c_disputed_dated_fact_upgraded_to_established_fails,
                 test_d_invented_before_after_between_separately_dated_facts_fails,
                 test_e_disputed_account_preserved_passes):
        print("\n" + test.__name__)
        test()
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("\nALL PASS")


if __name__ == "__main__":
    main()
