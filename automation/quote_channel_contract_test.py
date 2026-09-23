#!/usr/bin/env python3
"""
quote_channel_contract_test.py -- a required quotation may not vanish in silence.

TWO HALVES OF ONE CONTRADICTION, both live on 2e96aa7:

  PLANNING SIDE. ARCHITECT_SCHEMA asked for `use_quotes`. build_packet resolves those ids
  against a `quotes` mapping, and writer_packet() calls build_packet with THREE arguments
  -- so the mapping is always {}. Nothing in the engine produces one. `packet["quotes"]`
  was therefore always [], render()'s QUOTE EXACTLY block never fired, and an architecture
  that decided the article needed a quotation had that decision dropped between the plan
  and the prompt without any error anywhere.

  WRITING SIDE. The FAST_LANE contract told the Writer it may use quotation marks "ONLY
  when a fact below explicitly grants quote_permission: DIRECT_VERBATIM and gives its
  quote_text". No fact on this path carries either field, so the condition could never be
  met. The instruction resolved to "never quote" while appearing to describe a permission
  system -- in the one register the Writer is measured transcribing.

The fix is removal, not wiring: a ledger fact's support_span is verbatim source text, but
it is the span that SUPPORTS a proposition, not a record of someone speaking, and the
ledger has no speaker structure to attribute it to. Making quotations out of spans is a
new evidence contract, not a repair to this one.

Behavioural, no provider, no network.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP   # noqa: E402
from new_engine_v1 import story as ST         # noqa: E402

import definition_support_test as BASE        # noqa: E402  (shared wire-shaped fixture)

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print("  PASS  %s" % label)
    else:
        FAILURES.append(label)
        print("  FAIL  %s   <- %r" % (label, detail))


LEDGER = BASE.LEDGER
arch = BASE.arch


# ── the planning side ─────────────────────────────────────────────────────────
def test_a_required_quotation_is_refused_rather_than_dropped():
    a = arch(use_quotes=["Q01"])
    errs = CP.check_architecture(a, LEDGER)
    check("check_architecture refuses an architecture that requires a quote",
          any("QUOTE_CHANNEL" in e for e in errs), errs)
    check("  and says where it would have been lost",
          any("dropped between the plan and the prompt" in e for e in errs), errs)

    raised = ""
    try:
        CP.writer_packet(a, LEDGER)
    except CP.CompositionHold as e:
        raised = " ".join(e.reasons)
    check("writer_packet fails closed on the same architecture",
          "no quote channel" in raised, raised[:200])


def test_an_architecture_that_requires_no_quotation_is_untouched():
    check("an empty use_quotes is accepted", CP.quote_requirement_errors(arch()) == [],
          CP.quote_requirement_errors(arch()))
    check("a missing use_quotes is accepted",
          CP.quote_requirement_errors({"article_type": "NARRATIVE_ARTICLE"}) == [])
    check("whitespace-only ids do not count as a requirement",
          CP.quote_requirement_errors({"use_quotes": ["", "  "]}) == [])
    check("the control architecture still passes whole",
          CP.check_architecture(arch(), LEDGER) == [],
          CP.check_architecture(arch(), LEDGER))


def test_the_architect_is_no_longer_asked_for_quotes():
    check("ARCHITECT_SCHEMA no longer declares use_quotes",
          '"use_quotes"' not in CP.ARCHITECT_SCHEMA)


def test_the_packet_still_carries_no_quotes():
    """The condition that made the requirement unsatisfiable, pinned so that anyone
    wiring a real quote channel later has to change this test on purpose."""
    pk, prompt = CP.writer_packet(arch(), LEDGER)
    check("packet['quotes'] is empty", pk["quotes"] == [], pk["quotes"])
    check("and the rendered prompt has no QUOTE EXACTLY block",
          "QUOTE EXACTLY" not in prompt)


# ── the writing side ──────────────────────────────────────────────────────────
def test_the_fast_lane_contract_is_satisfiable():
    sys_prompt = CP.COMPOSE_SYSTEMS[CP.COMPOSE_FAST_LANE]
    check("the unsatisfiable quote_permission clause is gone",
          "quote_permission" not in sys_prompt)
    check("DIRECT_VERBATIM is no longer offered as a condition",
          "DIRECT_VERBATIM" not in sys_prompt)
    check("the Writer is still told not to quote freely",
          "DO_NOT_QUOTE" in sys_prompt)
    check("  and the prohibition is stated as a rule it can actually obey",
          "Do not put quotation marks around anyone's words" in sys_prompt)
    check("reconstruction from fragments is still forbidden",
          "reconstruct a quote from fragments" in sys_prompt)
    check("and paraphrase-inside-quotation-marks is still forbidden",
          "paraphrase inside quotation marks" in sys_prompt)


def test_the_normal_contract_is_unchanged_in_this_respect():
    normal = CP.COMPOSE_SYSTEMS[CP.COMPOSE_NORMAL]
    check("the NORMAL contract never referenced quote_permission either",
          "quote_permission" not in normal)


def main():
    for fn in (test_a_required_quotation_is_refused_rather_than_dropped,
               test_an_architecture_that_requires_no_quotation_is_untouched,
               test_the_architect_is_no_longer_asked_for_quotes,
               test_the_packet_still_carries_no_quotes,
               test_the_fast_lane_contract_is_satisfiable,
               test_the_normal_contract_is_unchanged_in_this_respect):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL QUOTE CHANNEL CONTRACT TESTS PASSED")


if __name__ == "__main__":
    main()
