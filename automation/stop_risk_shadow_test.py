#!/usr/bin/env python3
"""
stop_risk_shadow_test.py — static test suite for
ReviewMixin._extract_stop_risk_shadow (A-M reconciliation, item J, 2026-08-14).

J was never built anywhere in this codebase before this pass -- confirmed
live: zero grep hits for stop_risk/drop-off/attrition anywhere in
automation/ (see .claude/original-blueprint-A-M-reconciliation-2026-08-13.md
section J). This adds a STOP_RISK line to the existing _engagement_read
call (zero extra model cost) and this suite proves the deterministic
parser that extracts it: valid scores 1-5, a missing/absent line, a
malformed line, and that this stays observation-only (never touches
is_clean or any blocking path).

Zero network, zero model calls.

USAGE: python3 automation/stop_risk_shadow_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import inspect
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.review import ReviewMixin  # noqa: E402
from orchestrator.generate import GenerateMixin  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def extract(text):
    return ReviewMixin._extract_stop_risk_shadow(text)


def case_low_risk_scored():
    r = extract("VERDICT: yes, all the way.\nHOOK: a real one.\nDRAG: none.\nSTOP_RISK: 1 — NONE")
    check("STOP_RISK: 1 — NONE parses to score=1, reason='NONE'", r["score"] == 1 and r["reason"] == "NONE")


def case_high_risk_with_reason():
    r = extract("VERDICT: stop around paragraph 3.\nHOOK: none really.\nDRAG: repeats itself.\n"
                 "STOP_RISK: 5 — repetitive middle, the same observation restated three times")
    check("STOP_RISK: 5 — <reason> parses score=5 and the reason text",
          r["score"] == 5 and r["reason"] == "repetitive middle, the same observation restated three times")


def case_all_valid_scores_1_through_5():
    for n in range(1, 6):
        r = extract(f"STOP_RISK: {n} — some reason")
        check(f"STOP_RISK: {n} parses to score={n}", r["score"] == n)


def case_dash_variants():
    for sep in ("—", "-", ":"):
        r = extract(f"STOP_RISK: 3 {sep} unclear purpose in the middle section")
        check(f"separator {sep!r} still parses correctly", r["score"] == 3)


def case_missing_stop_risk_line():
    r = extract("VERDICT: yes.\nHOOK: interesting.\nDRAG: a bit slow.")
    check("no STOP_RISK line at all -> score=None, not 0 (distinguishable from a real low score)",
          r["score"] is None)
    check("no STOP_RISK line -> reason=None", r["reason"] is None)


def case_none_or_empty_input():
    r = extract(None)
    check("engagement_read=None -> score=None, never raises", r["score"] is None)
    r = extract("")
    check("engagement_read='' -> score=None, never raises", r["score"] is None)
    r = extract("(no response)")
    check("engagement_read='(no response)' (the _engagement_read failure sentinel) -> score=None",
          r["score"] is None)


def case_out_of_range_score_not_matched():
    # The regex itself only matches [1-5]; a malformed "STOP_RISK: 7" should not
    # match at all (score stays None) rather than silently accepting an invalid value.
    r = extract("STOP_RISK: 7 — way too high, not a real scale value")
    check("STOP_RISK: 7 (out of the defined 1-5 range) -> does not match, score=None",
          r["score"] is None)
    r = extract("STOP_RISK: 0 — zero isn't a valid score either")
    check("STOP_RISK: 0 (out of range) -> does not match, score=None", r["score"] is None)


def case_reason_defaults_to_none_when_blank():
    r = extract("STOP_RISK: 2 —")
    check("STOP_RISK with no reason text after the separator -> reason=None, not empty string",
          r["score"] == 2 and r["reason"] is None)


def case_shadow_only_flag_always_true():
    r = extract("STOP_RISK: 4 — delayed payoff")
    check("shadow_only is always True", r["shadow_only"] is True)


def case_never_feeds_should_block():
    src = inspect.getsource(GenerateMixin._compute_should_block)
    check("_compute_should_block's source never references stop_risk "
          "(J cannot silently gain blocking/publication authority)",
          "stop_risk" not in src.lower())


if __name__ == "__main__":
    case_low_risk_scored()
    case_high_risk_with_reason()
    case_all_valid_scores_1_through_5()
    case_dash_variants()
    case_missing_stop_risk_line()
    case_none_or_empty_input()
    case_out_of_range_score_not_matched()
    case_reason_defaults_to_none_when_blank()
    case_shadow_only_flag_always_true()
    case_never_feeds_should_block()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
