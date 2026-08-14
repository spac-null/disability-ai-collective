#!/usr/bin/env python3
"""
should_block_policy_test.py — static test suite for
GenerateMixin._compute_should_block (A-M reconciliation, `## M`, 2026-08-14).

The reconciliation confirmed a genuine open policy gap: `_degraded_stages ==
["gate_llm"]` alone did not force `fact_check_status: blocked`, even though
gate_llm going dark means "mechanical rule violations are UNKNOWN, not zero"
per gate.py's own log lines -- the same authoritative-safety-net-loss class
fable_brief already blocks on its own for. This suite proves the corrected
policy: fable_brief alone blocks (unchanged), gate_llm alone now blocks (the
fix), any other single stage alone still does not block (unchanged), 2+ of
any kind still blocks (unchanged), and that CJ-2/shadow-only failures can
never reach this policy at all because they never append to
_degraded_stages in the first place (structural check, mirrors how
repetition_shadow_test.py verified its own shadow check can never enter
is_clean's computation).

Zero network, zero model calls, zero article generation.

USAGE: python3 automation/should_block_policy_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.generate import GenerateMixin  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def case_no_degraded_stages_never_blocks():
    check("empty degraded_stages -> does not block (successful run unchanged)",
          GenerateMixin._compute_should_block([]) is False)


def case_fable_brief_alone_blocks_unchanged():
    check("fable_brief alone -> blocks (pre-existing policy, unchanged by this fix)",
          GenerateMixin._compute_should_block(["fable_brief"]) is True)


def case_gate_llm_alone_now_blocks():
    check("gate_llm alone -> blocks (THE FIX -- this was False before 2026-08-14)",
          GenerateMixin._compute_should_block(["gate_llm"]) is True)


def case_other_single_stage_alone_still_does_not_block():
    check("editorial_revision alone -> does not block (only fable_brief/gate_llm are "
          "lone-blocking; a single non-authoritative-alone stage still needs a second "
          "failure to matter, unchanged by this fix)",
          GenerateMixin._compute_should_block(["editorial_revision"]) is False)


def case_unknown_future_stage_alone_does_not_block():
    check("a hypothetical future stage name alone -> does not block (forward "
          "compatibility -- only fable_brief/gate_llm are named lone-blockers, "
          "everything else needs the 2+ threshold)",
          GenerateMixin._compute_should_block(["some_future_stage"]) is False)


def case_two_distinct_stages_blocks_unchanged():
    check("editorial_revision + fable_brief -> blocks (2+ threshold, unchanged)",
          GenerateMixin._compute_should_block(["editorial_revision", "fable_brief"]) is True)
    check("editorial_revision + gate_llm -> blocks (2+ threshold, was already True "
          "before this fix and remains True)",
          GenerateMixin._compute_should_block(["editorial_revision", "gate_llm"]) is True)
    check("two non-authoritative-alone stages together -> blocks (2+ threshold)",
          GenerateMixin._compute_should_block(["editorial_revision", "some_future_stage"]) is True)


def case_duplicate_stage_names_dedup_correctly():
    check("gate_llm appended twice (e.g. once per retry) -> still blocks, not "
          "miscounted as 2+ distinct stages via set dedup",
          GenerateMixin._compute_should_block(["gate_llm", "gate_llm"]) is True)
    check("editorial_revision appended twice alone -> still does not block "
          "(dedup must not accidentally cross the 2+ threshold)",
          GenerateMixin._compute_should_block(["editorial_revision", "editorial_revision"]) is False)


def case_order_independent():
    check("stage order does not affect the result",
          GenerateMixin._compute_should_block(["gate_llm", "fable_brief"])
          == GenerateMixin._compute_should_block(["fable_brief", "gate_llm"]))


def case_shadow_only_failures_never_reach_this_policy():
    # Structural check, not a call-path check: CJ-2/shadow integration must never
    # append to _degraded_stages at all (it is non-authoritative), so this policy
    # never even sees it, regardless of what the policy function itself returns.
    cj2_shadow_src = (AUTOMATION_DIR / "orchestrator" / "cj2_shadow.py").read_text()
    check("cj2_shadow.py never appends to _degraded_stages (shadow failures are "
          "structurally invisible to the blocking policy, not merely non-blocking "
          "by a lucky classification)",
          "_degraded_stages" not in cj2_shadow_src)


if __name__ == "__main__":
    case_no_degraded_stages_never_blocks()
    case_fable_brief_alone_blocks_unchanged()
    case_gate_llm_alone_now_blocks()
    case_other_single_stage_alone_still_does_not_block()
    case_unknown_future_stage_alone_does_not_block()
    case_two_distinct_stages_blocks_unchanged()
    case_duplicate_stage_names_dedup_correctly()
    case_order_independent()
    case_shadow_only_failures_never_reach_this_policy()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
