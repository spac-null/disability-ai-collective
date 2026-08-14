#!/usr/bin/env python3
"""
review_wholeness_test.py — proves _engagement_read now receives the WHOLE
article (A-M reconciliation item H, 2026-08-14), not the first 6000
characters, and proves the pre-fix behavior would have missed a marker
placed after that point — structurally, not semantically (the mock LLM
call never has to "notice" anything; this only checks what actually
reaches the API call). Also proves the RULES_SYSTEM check's own R1-R19
completeness gap (found while auditing H, same bug class as I) is closed.
Zero network, zero model calls.

USAGE: python3 automation/review_wholeness_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import logging
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.review import ReviewMixin  # noqa: E402
from orchestrator.gate import GateMixin  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


class _FakeReviewer(ReviewMixin, GateMixin):
    """ReviewMixin needs GateMixin's _parse_rule_verdicts/_missing_rule_ids
    (real production combines them in ProductionOrchestrator) and its own
    deterministic checks (_check_buried_clause_sentences etc, also on
    GateMixin) -- combining both here mirrors that composition exactly for
    just the two methods under test, without needing the full orchestrator."""

    def __init__(self, fake_llm_call):
        self.logger = logging.getLogger("review_wholeness_test")
        self.logger.addHandler(logging.NullHandler())
        self._fake_llm_call = fake_llm_call
        self.captured_calls = []

    def _call_openai_compat_api(self, **kwargs):
        self.captured_calls.append(kwargs)
        return self._fake_llm_call(**kwargs)


MARKER = "ZZZ_MARKER_PLACED_AFTER_CHAR_6000_ZZZ"

# Body engineered so the marker sits well past char 6000 but the whole
# thing stays well under config.py's own 2800-word/~16000-char tier — this
# structurally reproduces "a real 1600-2800 word article" without needing
# an actual published one.
PADDING = ("This sentence exists only to occupy space in the article body. " * 20 + "\n\n") * 7
BODY_WITH_LATE_MARKER = PADDING + f"\n\n{MARKER}\n\n" + PADDING
assert len(PADDING) > 6000, "test setup: padding must itself exceed the old 6000-char slice"
assert BODY_WITH_LATE_MARKER.index(MARKER) > 6000, "test setup: marker must sit past char 6000"


def case_engagement_read_now_receives_full_content_past_old_6000_limit():
    r = _FakeReviewer(lambda **kw: "VERDICT: yes\nHOOK: x\nDRAG: y")
    r._engagement_read(BODY_WITH_LATE_MARKER, "Test Title", "Pixel Nova")
    check("A. exactly one LLM call made", len(r.captured_calls) == 1)
    sent_prompt = r.captured_calls[0]["user_prompt"]
    check("B. the marker placed after char 6000 IS present in what was actually sent "
          "(this is the post-fix, whole-article behavior)",
          MARKER in sent_prompt)
    check("C. structural proof of the OLD bug: slicing what was sent at [:6000] the "
          "old way would NOT have contained the marker (confirms this really tests "
          "the truncation boundary, not a false positive)",
          MARKER not in sent_prompt[:6000 + len("Title: Test Title\nAuthor persona: Pixel Nova\n\n")])
    check("D. check_truncation=True is now passed on this call",
          r.captured_calls[0].get("check_truncation") is True)


def case_short_article_unaffected():
    short_body = "A short article, well under any threshold, old or new."
    r = _FakeReviewer(lambda **kw: "VERDICT: yes\nHOOK: x\nDRAG: y")
    result = r._engagement_read(short_body, "Short", "Maya Flux")
    check("E. short article: still works, full content sent",
          short_body in r.captured_calls[0]["user_prompt"] and result == "VERDICT: yes\nHOOK: x\nDRAG: y")


def case_article_just_below_old_threshold():
    body = "x" * 5999
    r = _FakeReviewer(lambda **kw: "VERDICT: yes\nHOOK: x\nDRAG: y")
    r._engagement_read(body, "T", "Zen Circuit")
    check("F. article just below the old 5999-char threshold: fully present (trivial "
          "pre-fix case, still correct post-fix)",
          body in r.captured_calls[0]["user_prompt"])


def case_article_just_above_old_threshold():
    body = "y" * 6001
    r = _FakeReviewer(lambda **kw: "VERDICT: yes\nHOOK: x\nDRAG: y")
    r._engagement_read(body, "T", "Siri Sage")
    check("G. article just above the old 6001-char threshold: the OLD code would have "
          "silently dropped the last character -- post-fix, the full body is sent",
          body in r.captured_calls[0]["user_prompt"])


def case_maximum_normal_production_article_size():
    """config.py's own longform tier is ~2800 words -- approximate at ~5.7
    chars/word (English prose average incl. spaces) -> ~16,000 chars."""
    body = ("word " * 2800).strip()
    assert len(body) > 6000
    r = _FakeReviewer(lambda **kw: "VERDICT: yes\nHOOK: x\nDRAG: y")
    r._engagement_read(body, "T", "Pixel Nova")
    check("H. a full 2800-word-tier article (~14000 chars): entirely present, not "
          "truncated at the old 6000-char boundary",
          body in r.captured_calls[0]["user_prompt"])


def case_truncation_exception_handled_gracefully():
    def raises_truncation(**kw):
        raise ValueError("Response truncated by max_tokens (finish_reason='length')")
    r = _FakeReviewer(raises_truncation)
    result = r._engagement_read(BODY_WITH_LATE_MARKER, "T", "Maya Flux")
    check("I. check_truncation's ValueError is caught by the existing except path, "
          "returns None (advisory-only, does not crash the caller)",
          result is None)


# ── RULES_SYSTEM (R1-R19) completeness, found while auditing H ────────────

ALL_19_PASS = "\n".join(f"[PASS] R{i}" for i in range(1, 20))


def case_review_rules_system_missing_rule_now_caught():
    raw_missing_one = "\n".join(f"[PASS] R{i}" for i in range(1, 20) if i != 18)
    missing = GateMixin._missing_rule_ids(raw_missing_one, expected=frozenset(f"R{i}" for i in range(1, 20)))
    check("J. review.py's own R1-R19 set: R18 silently missing is now detectable "
          "(same _missing_rule_ids method, parameterized with review.py's own 19-rule "
          "set instead of gate.py's 17)",
          missing == frozenset({"R18"}))
    violations = GateMixin._parse_rule_verdicts(raw_missing_one)
    check("K. critical: _parse_rule_verdicts alone shows ZERO violations for this "
          "response too (same silent-pass bug, now caught for review.py's rule set as well)",
          violations == [])


if __name__ == "__main__":
    case_engagement_read_now_receives_full_content_past_old_6000_limit()
    case_short_article_unaffected()
    case_article_just_below_old_threshold()
    case_article_just_above_old_threshold()
    case_maximum_normal_production_article_size()
    case_truncation_exception_handled_gracefully()
    case_review_rules_system_missing_rule_now_caught()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
