#!/usr/bin/env python3
"""
gate_pre_commit_integration_test.py — proves _pre_commit_gate itself (not
just _missing_rule_ids in isolation) correctly treats a rule-check response
missing an expected rule as gate_llm_ok=False / a degraded stage, the exact
same way an outright exception already was — A-M reconciliation item I,
2026-08-14. Zero network, zero model calls (the LLM call is monkeypatched).

Also proves check_truncation=True (added to gate.py's own
_call_openai_compat_api call this pass) is now actually passed through, and
that a clean, complete response is unaffected by either change.

USAGE: python3 automation/gate_pre_commit_integration_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import logging
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


# A real Bregman-style article body, well-formed enough to pass readability/
# buried-clause/argument-word/sentence-length checks cleanly on its own, so
# any FAIL this suite observes is attributable only to the gate_llm path.
CLEAN_BODY = """---
title: Test article
---

The ramp outside the library gets used every day. Nobody asks who built it or why. A wheelchair user rolls up, gets in, and leaves. That is the whole story, and it is enough.

A city planner once told me the ramp cost more than the stairs it replaced. He said it like an apology. I did not need one. I needed the ramp.

Most access work never gets a ribbon-cutting. It gets used, or it does not. This one gets used.
""" * 3  # repeated to clear any short-article edge cases in the deterministic checks


class _FakeGate(GateMixin):
    """Minimal stand-in: GateMixin's own methods (_readability_score,
    _check_buried_clause_sentences, etc.) are all self-contained on this
    class already — only _call_openai_compat_api (normally supplied by
    LLMMixin in the real ProductionOrchestrator) needs a stub here."""

    def __init__(self, fake_llm_call):
        self.logger = logging.getLogger("gate_pre_commit_integration_test")
        self.logger.addHandler(logging.NullHandler())
        self._degraded_stages = []
        self._fake_llm_call = fake_llm_call
        self._captured_call_kwargs = None

    def _call_openai_compat_api(self, **kwargs):
        self._captured_call_kwargs = kwargs
        return self._fake_llm_call(**kwargs)


ALL_17_PASS = "\n".join(f"[PASS] R{i}" for i in range(1, 18))


def case_clean_complete_response_unaffected():
    gate = _FakeGate(lambda **kw: ALL_17_PASS)
    content, changed = gate._pre_commit_gate(CLEAN_BODY, article_file=None, article_type="essay")
    check("A. clean, complete response: gate does not rewrite (changed=False)", changed is False)
    check("A. clean, complete response: no degraded stage recorded", gate._degraded_stages == [])
    check("A. check_truncation=True is now actually passed to _call_openai_compat_api",
          gate._captured_call_kwargs.get("check_truncation") is True)


def case_one_rule_silently_missing_is_now_caught():
    """The exact bug the reconciliation found: a response that completes
    without raising, but simply never mentions one rule."""
    raw_missing_one = "\n".join(f"[PASS] R{i}" for i in range(1, 18) if i != 14)
    gate = _FakeGate(lambda **kw: raw_missing_one)
    content, changed = gate._pre_commit_gate(CLEAN_BODY, article_file=None, article_type="essay")
    check("B. one rule (R14) silently missing: recorded as a degraded stage (gate_llm)",
          gate._degraded_stages == ["gate_llm"])


def case_truncated_tail_is_now_caught():
    raw_truncated = "\n".join(f"[PASS] R{i}" for i in range(1, 12))  # R12-R17 never appear
    gate = _FakeGate(lambda **kw: raw_truncated)
    content, changed = gate._pre_commit_gate(CLEAN_BODY, article_file=None, article_type="essay")
    check("C. truncated tail (R12-R17 missing): recorded as a degraded stage (gate_llm)",
          gate._degraded_stages == ["gate_llm"])


def case_check_truncation_exception_still_handled_by_existing_path():
    """Proves the pre-existing exception path (llm.py's own
    check_truncation=True raising a ValueError on finish_reason='length')
    still works correctly now that gate.py actually opts into it — this is
    the SAME existing except-block behavior, just newly reachable via a
    real truncation signal instead of only via a network/auth failure."""
    def raises_truncation(**kw):
        raise ValueError("Response truncated by max_tokens (model=x, finish_reason='length', "
                          "completion_tokens=1010, reasoning_tokens=None)")
    gate = _FakeGate(raises_truncation)
    content, changed = gate._pre_commit_gate(CLEAN_BODY, article_file=None, article_type="essay")
    check("D. check_truncation's own ValueError: caught by existing except path, "
          "recorded as a degraded stage (gate_llm)",
          gate._degraded_stages == ["gate_llm"])
    check("D. gate does not crash the caller -- returns (content, False) same as a clean run",
          changed is False)


def case_totally_garbled_response_is_now_caught():
    gate = _FakeGate(lambda **kw: "Looks fine to me, no specific notes.")
    content, changed = gate._pre_commit_gate(CLEAN_BODY, article_file=None, article_type="essay")
    check("E. completely unparseable response: recorded as a degraded stage (gate_llm), "
          "not silently read as zero violations",
          gate._degraded_stages == ["gate_llm"])


def case_real_fail_still_works_normally():
    """Confirms the fix didn't break the ordinary, everyday FAIL path --
    real violations are still counted and still drive the existing >=3
    threshold/surgical-fix logic, independent of the completeness check."""
    raw_two_fails = ALL_17_PASS.replace("[PASS] R5", '[FAIL] R5 — "x"').replace("[PASS] R10", '[FAIL] R10 — "y"')
    gate = _FakeGate(lambda **kw: raw_two_fails)
    content, changed = gate._pre_commit_gate(CLEAN_BODY, article_file=None, article_type="essay")
    check("F. 2 explicit FAILs, all 17 rules present: NOT treated as degraded (complete, just has violations)",
          gate._degraded_stages == [])


if __name__ == "__main__":
    case_clean_complete_response_unaffected()
    case_one_rule_silently_missing_is_now_caught()
    case_truncated_tail_is_now_caught()
    case_check_truncation_exception_still_handled_by_existing_path()
    case_totally_garbled_response_is_now_caught()
    case_real_fail_still_works_normally()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
