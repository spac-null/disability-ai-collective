#!/usr/bin/env python3
"""
repetition_shadow_test.py — static test suite for ReviewMixin's
_check_repetition_shadow (A-M reconciliation item G, 2026-08-14, G SHADOW
V0). Zero network, zero model calls — proves the deterministic candidate
detector itself, not any semantic judgment about whether a flagged pair
is actually a flaw. This check has NO blocking authority; that is verified
separately (case_no_blocking_authority below) and directly in
orchestrator/review.py's own is_clean computation.

USAGE: python3 automation/repetition_shadow_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.review import ReviewMixin  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def case_clearly_repeated_paragraph_flagged():
    # Deliberately NOT the (0, last) pair -- that exact pair is the intro/
    # conclusion exemption tested separately in case_intro_conclusion_echo_exempted.
    # Four paragraphs here so the repeated pair (1, 3) sits safely in the middle.
    opening = "This piece begins somewhere else entirely, with a different scene."
    p1 = ("The council approved the new accessible parking policy after months of "
          "resident petitions and public hearings about transit access downtown.")
    unrelated = ("Weegee heard the body first, before the camera ever caught up to "
                 "what the room already knew about who was allowed to stand where.")
    p2 = ("After months of resident petitions and public hearings about transit "
          "access downtown, the council approved the new accessible parking policy.")
    content = f"{opening}\n\n{p1}\n\n{unrelated}\n\n{p2}"
    hits = ReviewMixin._check_repetition_shadow(content)
    check("A. two paragraphs sharing nearly all content words are flagged as a candidate",
          len(hits) >= 1 and any(set(h["paragraph_pair"]) == {1, 3} for h in hits))
    if hits:
        h = next(h for h in hits if set(h["paragraph_pair"]) == {1, 3})
        check("A. flagged pair carries similarity/shared_terms/reason/shadow_only fields",
              {"paragraph_pair", "similarity", "shared_terms", "reason", "shadow_only"} <= set(h.keys()))
        check("A. shadow_only is True", h["shadow_only"] is True)
        check("A. reason text explicitly says candidate-only, not a verdict",
              "candidate only" in h["reason"] or "not a verdict" in h["reason"])


def case_genuinely_distinct_paragraphs_not_flagged():
    p1 = "The council approved the new accessible parking policy after months of hearings."
    p2 = "Weegee heard the body first, before the camera caught up to what the room knew."
    p3 = "A diagnosis changes what a person is allowed to want from the rest of their life."
    content = f"{p1}\n\n{p2}\n\n{p3}"
    hits = ReviewMixin._check_repetition_shadow(content)
    check("B. three genuinely unrelated paragraphs produce zero candidates", hits == [])


def case_intro_conclusion_echo_exempted():
    intro = ("The ramp outside the library gets used every day by people the city never "
             "consulted about where it should go or how steep it should be.")
    middle = "A planner once told me the ramp cost more than the stairs it replaced."
    conclusion = ("The ramp outside the library gets used every day by people the city "
                  "never consulted about where it should go or how steep it should be.")
    content = f"{intro}\n\n{middle}\n\n{conclusion}"
    hits = ReviewMixin._check_repetition_shadow(content)
    check("C. identical intro/conclusion (paragraph 0 vs last) is explicitly NOT flagged "
          "(the one deterministic exception this check encodes on purpose)",
          not any(set(h["paragraph_pair"]) == {0, 2} for h in hits))


def case_short_paragraphs_ignored():
    p1 = "Yes."
    p2 = "Yes indeed."
    p3 = ("This is a genuinely substantial paragraph with plenty of real content words "
          "about disability access policy and municipal budgeting decisions this year.")
    content = f"{p1}\n\n{p2}\n\n{p3}"
    hits = ReviewMixin._check_repetition_shadow(content)
    check("D. paragraphs under the min_content_words floor never get compared at all",
          hits == [])


def case_no_blocking_authority():
    """Confirms, at the source level, that shadow_repetition_hits cannot be
    part of is_clean's computation -- a structural guarantee, not just an
    assertion about behavior at one call site."""
    import inspect
    from orchestrator import review as review_module
    src = inspect.getsource(review_module.ReviewMixin.validate_article)
    is_clean_line = next(line for line in src.splitlines() if "is_clean = (" in line)
    check("E. is_clean's own computation line does not reference shadow_repetition_hits",
          "shadow_repetition_hits" not in is_clean_line)
    check("E. shadow_repetition_hits IS computed somewhere in validate_article "
          "(the check actually runs, it's just never consulted for is_clean)",
          "shadow_repetition_hits = self._check_repetition_shadow(content)" in src)


def case_threshold_is_a_parameter_not_hardcoded_magic():
    """Confirms the uncalibrated threshold is an actual parameter (so a
    future calibration pass can adjust it without touching the detection
    logic itself), not buried as a magic number."""
    import inspect
    sig = inspect.signature(ReviewMixin._check_repetition_shadow)
    check("F. similarity_threshold is a real, named, adjustable parameter",
          "similarity_threshold" in sig.parameters)
    check("F. min_content_words is a real, named, adjustable parameter",
          "min_content_words" in sig.parameters)


def case_empty_and_single_paragraph_input():
    check("G. empty content -> no crash, empty result", ReviewMixin._check_repetition_shadow("") == [])
    check("H. single paragraph -> no crash, empty result (nothing to pair)",
          ReviewMixin._check_repetition_shadow("Just one paragraph here, nothing to compare against.") == [])


if __name__ == "__main__":
    case_clearly_repeated_paragraph_flagged()
    case_genuinely_distinct_paragraphs_not_flagged()
    case_intro_conclusion_echo_exempted()
    case_short_paragraphs_ignored()
    case_no_blocking_authority()
    case_threshold_is_a_parameter_not_hardcoded_magic()
    case_empty_and_single_paragraph_input()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
