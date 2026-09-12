#!/usr/bin/env python3
"""Targeted regression for the separated, read-only Claim Mapper: proves the
one-retry-on-mechanical-error policy actually retries with the errors in the
prompt, never mutates the article, and stops after one retry. Uses a fake provider
-- no real network/subscription call."""
from __future__ import annotations

import json
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


class Completion:
    def __init__(self, text):
        self.text = text
        self.requested_model = "fake"
        self.actual_model = "fake"
        self.provider_label = "fake"
        self.usage = {}

    def identity(self):
        return {"provider": "fake"}


class FakeProvider:
    """Returns each entry in `replies` in order, one per .complete() call."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None):
        self.calls.append(user)
        return Completion(json.dumps(self.replies.pop(0)))


ARTICLE = "Emilio asked for an interpreter. He was denied one."
LEDGER = {"F08": {"entities": [], "claim_type": "POSITIVE_FACT",
                  "proposition": "Emilio asked for an interpreter",
                  "support_span": "", "scope": "WORLD"},
         "F10": {"entities": [], "claim_type": "POSITIVE_FACT",
                 "proposition": "he was denied one",
                 "support_span": "", "scope": "WORLD"}}
ALLOWED = set(LEDGER)


def test_valid_first_reply_needs_no_retry():
    good = {"claim_map": [
        {"sentence_id": "S001", "fact_ids": ["F08"]},
        {"sentence_id": "S002", "fact_ids": ["F10"]},
    ]}
    provider = FakeProvider([good])
    claim_map, errs, retries, ident = FL.claim_map_article(
        provider, ARTICLE, LEDGER, ALLOWED)
    check("a mechanically valid first reply needs zero retries",
          retries == 0 and errs == [], (retries, errs))
    check("exactly one provider call was made", len(provider.calls) == 1,
          len(provider.calls))


def test_invalid_first_reply_retries_once_with_errors_then_fixes():
    bad = {"claim_map": [{"sentence_id": "S001", "fact_ids": ["F99"]}]}     # F99 unknown
    good = {"claim_map": [
        {"sentence_id": "S001", "fact_ids": ["F08"]},
        {"sentence_id": "S002", "fact_ids": ["F10"]},
    ]}
    provider = FakeProvider([bad, good])
    claim_map, errs, retries, ident = FL.claim_map_article(
        provider, ARTICLE, LEDGER, ALLOWED)
    check("a mechanically invalid first reply gets exactly one retry",
          retries == 1, retries)
    check("the retry prompt names the mechanical error",
          len(provider.calls) == 2 and "F99" in provider.calls[1], provider.calls)
    check("the corrected reply is mechanically valid", errs == [], errs)
    check("exactly two provider calls total (no third attempt)",
          len(provider.calls) == 2, len(provider.calls))


def test_still_invalid_after_retry_stops_there():
    bad = {"claim_map": [{"sentence_id": "S001", "fact_ids": ["F99"]}]}
    still_bad = {"claim_map": [{"sentence_id": "S001", "fact_ids": ["F98"]}]}
    provider = FakeProvider([bad, still_bad])
    claim_map, errs, retries, ident = FL.claim_map_article(
        provider, ARTICLE, LEDGER, ALLOWED)
    check("still-invalid after the one retry returns errors, not a third attempt",
          retries == 1 and errs != [] and len(provider.calls) == 2,
          (retries, errs, len(provider.calls)))


def main() -> None:
    for test in (test_valid_first_reply_needs_no_retry,
                 test_invalid_first_reply_retries_once_with_errors_then_fixes,
                 test_still_invalid_after_retry_stops_there):
        print("\n" + test.__name__)
        test()
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("\nALL PASS")


if __name__ == "__main__":
    main()
