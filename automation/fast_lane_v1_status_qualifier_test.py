#!/usr/bin/env python3
"""Targeted regressions for claim-type-vs-evidence-status separation and required-
qualifier preservation, built from the real immigration Grounding findings. No
provider, no network."""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import fast_lane_v1 as FL                                 # noqa: E402
import immigration_packet_v2 as IP2                         # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                           "" if ok else " <- %r" % detail))
    if not ok:
        FAILURES.append(label)


# A real Métraux/Hands United statement, NEGATIVE_EXISTENCE claim_type -- the exact
# shape of the real F13/F16 defect.
LEDGER = {
    "F13": {"entities": [], "claim_type": "NEGATIVE_EXISTENCE",
           "proposition": "There is no public information on how often deaf people "
                          "are given interpreters.",
           "support_span": "", "scope": "WORLD"},
    "F16": {"entities": ["Venezuelan Sign Language", "Mexican Sign Language"],
           "claim_type": "NEGATIVE_EXISTENCE",
           "proposition": "Interpreters are taken at their word..., leading to poor-"
                          "quality interpreters because there is no certification "
                          "process.",
           "support_span": "", "scope": "WORLD"},
    "F01": {"entities": ["Mother Jones"], "claim_type": "ATTRIBUTION",
           "proposition": "Mother Jones reporting found that some of the more than "
                          "100 deaf immigrants deported had no interpreters, or "
                          "interpretation inadequate to their needs.",
           "support_span": "", "scope": "WORLD"},
}
ALLOWED = set(LEDGER)
FACT_STATUS = {
    "F13": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux",
           "temporal_permission": "NONE"},
    "F16": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux",
           "temporal_permission": "NONE",
           "required_qualifiers": ["sometimes"]},
    "F01": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux",
           "temporal_permission": "NONE",
           "required_qualifiers": ["no interpreters, or inadequate interpretation "
                                   "(disjunction)"]},
}


def test_a_negative_existence_claim_type_compiled_as_attributed_in_real_packet():
    real = IP2.FACT_STATUS
    check("A: real packet's F13 (NEGATIVE_EXISTENCE, Métraux's interview statement) "
          "is compiled as ATTRIBUTED, not ESTABLISHED",
          real["F13"]["claim_status"] == FL.ATTRIBUTED, real["F13"])
    check("A: real packet's F16 (NEGATIVE_EXISTENCE, Hands United via Métraux) is "
          "compiled as ATTRIBUTED, not ESTABLISHED",
          real["F16"]["claim_status"] == FL.ATTRIBUTED, real["F16"])


def test_b_same_statement_narrated_unattributed_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "B", "fact_ids": ["F13"], "claim_status": "ESTABLISHED",
          "attribution_to": None}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("B: F13 narrated as ESTABLISHED with no attribution fails",
          len(errs) == 1 and "stronger than the packet's declared status" in errs[0],
          errs)


def test_c_sometimes_dropped_to_unconditional_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "C", "fact_ids": ["F16"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Julia Métraux",
          "required_qualifiers_preserved": False}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("C: 'sometimes leads to poor-quality interpreters' reported as an "
          "unconditional claim (required_qualifiers_preserved=False) fails",
          len(errs) == 1 and "qualifier preservation" in errs[0], errs)


def test_d_disjunction_narrowed_to_one_branch_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "D", "fact_ids": ["F01"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Julia Métraux",
          "required_qualifiers_preserved": False}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("D: 'no interpreters, or inadequate service' narrowed to only "
          "'inadequate service' (required_qualifiers_preserved=False) fails",
          len(errs) == 1 and "qualifier preservation" in errs[0], errs)


def test_e_correctly_attributed_and_qualified_passes():
    errs = FL.validate_claim_map(
        [{"sentence_id": "E1", "fact_ids": ["F16"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Julia Métraux", "claim_shape": "QUALIFIED",
          "required_qualifiers_preserved": True},
         {"sentence_id": "E2", "fact_ids": ["F01"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Julia Métraux", "claim_shape": "DISJUNCTION",
          "required_qualifiers_preserved": True}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("E: correctly attributed AND qualifier-preserved versions pass",
          errs == [], errs)


def main() -> None:
    for test in (test_a_negative_existence_claim_type_compiled_as_attributed_in_real_packet,
                 test_b_same_statement_narrated_unattributed_fails,
                 test_c_sometimes_dropped_to_unconditional_fails,
                 test_d_disjunction_narrowed_to_one_branch_fails,
                 test_e_correctly_attributed_and_qualified_passes):
        print("\n" + test.__name__)
        test()
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("\nALL PASS")


if __name__ == "__main__":
    main()
