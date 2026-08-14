#!/usr/bin/env python3
"""
gate_rule_completeness_test.py — static test suite for
GateMixin._missing_rule_ids (A-M reconciliation, item I, 2026-08-14).

Proves a rule that never receives a recognized [FAIL|PASS|N/A] verdict
anywhere in a gate LLM response can never be silently indistinguishable
from that rule having passed — the exact "invisible rule" failure mode the
reconciliation confirmed live in _parse_rule_verdicts. Zero network,
zero model calls.

USAGE: python3 automation/gate_rule_completeness_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.gate import GateMixin  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


ALL_17_PASS = "\n".join(f"[PASS] R{i}" for i in range(1, 18))


def case_all_expected_rules_present_all_pass():
    missing = GateMixin._missing_rule_ids(ALL_17_PASS)
    check("all 17 rules present, all PASS -> zero missing", missing == frozenset())


def case_one_explicit_fail():
    raw = ALL_17_PASS.replace("[PASS] R5", '[FAIL] R5 — "vague we, no referent"')
    missing = GateMixin._missing_rule_ids(raw)
    check("one explicit FAIL among 17 present -> zero missing", missing == frozenset())
    violations = GateMixin._parse_rule_verdicts(raw)
    check("the one FAIL is still correctly parsed as a violation", len(violations) == 1 and "R5" in violations[0])


def case_one_rule_absent_entirely():
    lines = [f"[PASS] R{i}" for i in range(1, 18) if i != 9]  # R9 never mentioned at all
    raw = "\n".join(lines)
    missing = GateMixin._missing_rule_ids(raw)
    check("R9 never mentioned -> missing == {R9}", missing == frozenset({"R9"}))
    violations = GateMixin._parse_rule_verdicts(raw)
    check("critical: _parse_rule_verdicts alone shows ZERO violations for this response "
          "(this is exactly the silent-pass bug -- missing rules must be caught separately)",
          violations == [])


def case_last_rules_truncated():
    # Simulates a response cut off mid-list -- R14/R15/R16/R17 never appear.
    lines = [f"[PASS] R{i}" for i in range(1, 14)]
    raw = "\n".join(lines)
    missing = GateMixin._missing_rule_ids(raw)
    check("truncated tail (R14-R17 never appear) -> missing == {R14,R15,R16,R17}",
          missing == frozenset({"R14", "R15", "R16", "R17"}))


def case_malformed_rule_block():
    lines = [f"[PASS] R{i}" for i in range(1, 18)]
    lines[7] = "R8 is fine, no violation found"  # malformed: no [PASS|FAIL|N/A] prefix at all
    raw = "\n".join(lines)
    missing = GateMixin._missing_rule_ids(raw)
    check("malformed line for R8 (no recognized verdict prefix) -> counted as missing",
          missing == frozenset({"R8"}))


def case_duplicate_rule_last_wins():
    raw = ALL_17_PASS + '\n[FAIL] R5 — "second mention overrides"'
    missing = GateMixin._missing_rule_ids(raw)
    check("duplicate rule mention -> still zero missing (dedup by rule id)", missing == frozenset())
    violations = GateMixin._parse_rule_verdicts(raw)
    check("duplicate: last verdict per rule id wins -> R5 counted as FAIL",
          len(violations) == 1 and "R5" in violations[0])


def case_unknown_extra_rule_ignored():
    raw = ALL_17_PASS + "\n[FAIL] R99 — not a real rule, should be ignored for completeness"
    missing = GateMixin._missing_rule_ids(raw)
    check("unknown extra rule id (R99) does not affect completeness of the real 17",
          missing == frozenset())


def case_case_and_spacing_variation():
    # _parse_rule_verdicts's own regex requires the exact "[FAIL|PASS|N/A]" casing and
    # "R\d+" format, but tolerates arbitrary trailing whitespace/content after the id.
    lines = [f"[PASS]   R{i}   extra trailing commentary here" for i in range(1, 18)]
    raw = "\n".join(lines)
    missing = GateMixin._missing_rule_ids(raw)
    check("extra whitespace/trailing text around a valid verdict line still parses -> zero missing",
          missing == frozenset())


def case_zero_parsed_rules():
    raw = "The article looks fine overall, no notes."
    missing = GateMixin._missing_rule_ids(raw)
    check("completely unparseable response -> ALL 17 rules missing",
          missing == GateMixin._EXPECTED_GATE_RULE_IDS)
    violations = GateMixin._parse_rule_verdicts(raw)
    check("critical: _parse_rule_verdicts alone shows ZERO violations for a totally garbled "
          "response too (would read as a clean pass without the completeness check)",
          violations == [])


def case_none_input():
    missing = GateMixin._missing_rule_ids(None)
    check("raw=None -> ALL 17 rules missing (same as empty string, no crash)",
          missing == GateMixin._EXPECTED_GATE_RULE_IDS)


def case_missing_never_yields_clean_pass():
    """The single most important assertion: for every one of the scenarios
    above where _parse_rule_verdicts alone returns zero violations (which
    the OLD code would have read as a clean pass), _missing_rule_ids
    independently flags the gap. A caller that checks BOTH can never reach
    a state of "zero violations reported" while an expected rule went
    unevaluated."""
    scenarios = [
        "\n".join(f"[PASS] R{i}" for i in range(1, 18) if i != 9),  # one absent
        "\n".join(f"[PASS] R{i}" for i in range(1, 14)),             # truncated tail
        "The article looks fine overall, no notes.",                # fully garbled
    ]
    for raw in scenarios:
        violations = GateMixin._parse_rule_verdicts(raw)
        missing = GateMixin._missing_rule_ids(raw)
        check(f"scenario with violations=={violations!r}: missing is non-empty when violations is empty",
              not (violations == [] and missing == frozenset()))


if __name__ == "__main__":
    case_all_expected_rules_present_all_pass()
    case_one_explicit_fail()
    case_one_rule_absent_entirely()
    case_last_rules_truncated()
    case_malformed_rule_block()
    case_duplicate_rule_last_wins()
    case_unknown_extra_rule_ignored()
    case_case_and_spacing_variation()
    case_zero_parsed_rules()
    case_none_input()
    case_missing_never_yields_clean_pass()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
