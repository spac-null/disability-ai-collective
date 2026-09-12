#!/usr/bin/env python3
"""Targeted regressions for DIRECT_QUOTE_REQUIRES_EXACT_PERMISSION, built from the
real immigration Fact Check finding (an ABC7 ellipsis-joined quote treated as one
verbatim sentence). No provider, no network."""
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
    # F55: the real shape -- a secondary source's own ellipsis, no independently
    # verified full quote, so the packet grants paraphrase only.
    "F55": {"entities": ["Nikolas De Bremaeker"], "claim_type": "ATTRIBUTION",
           "proposition": "De Bremaeker said ICE denied Joseph access to "
                          "assistive devices.",
           "support_span": "", "scope": "WORLD"},
    # F60: a fact WITH a verified, independently-confirmed exact quote.
    "F60": {"entities": ["Eric Swalwell"], "claim_type": "ATTRIBUTION",
           "proposition": "Swalwell made a statement about deporting a 6-year-old.",
           "support_span": "", "scope": "WORLD"},
    # F61: a second verified quote, used to build the "stitched fragments" case.
    "F61": {"entities": ["Eric Swalwell"], "claim_type": "ATTRIBUTION",
           "proposition": "Swalwell said the removal made the country darker.",
           "support_span": "", "scope": "WORLD"},
}
ALLOWED = set(LEDGER)
FACT_STATUS = {
    "F55": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Nikolas De Bremaeker",
           "quote_permission": "ATTRIBUTED_PARAPHRASE_ONLY"},
    "F60": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Eric Swalwell",
           "quote_permission": "DIRECT_VERBATIM",
           "quote_text": "if you're coming for a 6-year-old, you have to go "
                         "through us",
           "quote_attribution": "Eric Swalwell"},
    "F61": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Eric Swalwell",
           "quote_permission": "DIRECT_VERBATIM",
           "quote_text": "it makes the country darker",
           "quote_attribution": "Eric Swalwell"},
}


def test_a_ellipsis_joined_quote_used_as_verbatim_fails():
    errs = FL.validate_claim_map(
        [{"sentence_id": "A", "fact_ids": ["F55"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Nikolas De Bremaeker",
          "quote_permission_used": "DIRECT_VERBATIM",
          "quoted_text": "In a move that shocks the conscience ... ICE denied "
                         "Joseph the assistive devices he needs to live."}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("A: an ellipsis-joined quote used as DIRECT_VERBATIM with no permission "
          "fails", len(errs) == 1 and "none of" in errs[0], errs)


def test_b_accurate_attributed_paraphrase_passes():
    errs = FL.validate_claim_map(
        [{"sentence_id": "B", "fact_ids": ["F55"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Nikolas De Bremaeker",
          "quote_permission_used": "ATTRIBUTED_PARAPHRASE_ONLY"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("B: the same material as an accurate attributed paraphrase passes",
          errs == [], errs)


def test_c_exact_verified_quote_copied_exactly_passes():
    errs = FL.validate_claim_map(
        [{"sentence_id": "C", "fact_ids": ["F60"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Eric Swalwell",
          "quote_permission_used": "DIRECT_VERBATIM",
          "quoted_text": "if you're coming for a 6-year-old, you have to go "
                         "through us"}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("C: an exact, permitted verbatim quote copied exactly passes",
          errs == [], errs)


def test_d_two_quote_fragments_stitched_together_fails():
    stitched = ("if you're coming for a 6-year-old, you have to go through us "
               "... it makes the country darker")
    errs = FL.validate_claim_map(
        [{"sentence_id": "D", "fact_ids": ["F60", "F61"], "claim_status": "ATTRIBUTED",
          "attribution_to": "Eric Swalwell",
          "quote_permission_used": "DIRECT_VERBATIM", "quoted_text": stitched}],
        ALLOWED, LEDGER, FACT_STATUS)
    check("D: two exact quote fragments stitched into one new quoted sentence "
          "fails -- the stitched text matches neither fact's permitted quote_text",
          len(errs) == 1 and "does not exactly match" in errs[0], errs)


def main() -> None:
    for test in (test_a_ellipsis_joined_quote_used_as_verbatim_fails,
                 test_b_accurate_attributed_paraphrase_passes,
                 test_c_exact_verified_quote_copied_exactly_passes,
                 test_d_two_quote_fragments_stitched_together_fails):
        print("\n" + test.__name__)
        test()
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("\nALL PASS")


if __name__ == "__main__":
    main()
