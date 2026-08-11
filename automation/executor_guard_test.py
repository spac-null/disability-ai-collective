#!/usr/bin/env python3
"""
executor_guard_test.py — mocked integration tests proving _opus_targeted_revision
and _fable_polish_rewrite (automation/orchestrator/llm.py) actually ENFORCE
grounding.find_new_unsupported_specifics's verdict via
_reject_if_unsupported_specifics, not merely that the pure detector function
works in isolation (grounding_test.py already covers that).

WHY THIS EXISTS: the real safety boundary for the Phase 1.5B fabricated-quote
failure lives in the INTERACTION between an LLM call's output and the
deterministic guard that runs on it -- "the detector works" and "the executor
actually calls the detector and acts on a rejection" are different claims,
and only the second one is the thing that protects production. Found on
review before this phase's mocked baseline was recorded.

Uses the same _import_orchestrator/_patch_methods harness as snapshot_test.py
-- zero network, zero real cost. Patches _call_openai_compat_api and
_call_editorial_model directly to return CONTROLLED text (bypassing their own
real fallback-chain logic, which isn't what's under test here), then calls
the REAL executor methods and asserts on what they actually return.

USAGE: python3 automation/executor_guard_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from snapshot_test import _import_orchestrator, _patch_methods  # noqa: E402
from orchestrator.grounding import build_evidence_packet  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


SOURCE_TEXT = (
    "The council voted 6-3 on Tuesday. Jane Doe said \"this was a difficult "
    "trade-off\" during the meeting. The vote affected 400 residents."
)

# Long enough to clear both executors' minimum-length gates
# (_opus_targeted_revision: len(revised) > 400;
# _fable_polish_rewrite: len(revised) > max(400, len(article_body) * 0.6)).
ORIGINAL_ARTICLE = (
    "A" * 500 + " The council met this week and made a decision that "
    "affects many residents in ways still being worked out."
)


def _orch():
    po = _import_orchestrator()
    return po, po.ProductionOrchestrator()


def test_opus_targeted_revision_rejects_misattributed_quote():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    # The quote text IS real (in SOURCE_TEXT), but reattributed to a
    # fabricated speaker -- exactly the misattribution case task #20 added.
    fabricated = ORIGINAL_ARTICLE + ' Deborah Antwi said "this was a difficult trade-off" to reporters.'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: fabricated,
    )
    try:
        result = orch._opus_targeted_revision(ORIGINAL_ARTICLE, ["fix the opening"], "Maya Flux", packet)
    finally:
        restore()
    check(
        "Opus targeted revision with a real-quote-but-fabricated-speaker is REJECTED "
        "-- original article returned unchanged, not the fabrication",
        result == ORIGINAL_ARTICLE,
    )


def test_opus_targeted_revision_accepts_grounded_quote():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    grounded = ORIGINAL_ARTICLE + ' Jane Doe said "this was a difficult trade-off" to reporters.'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: grounded,
    )
    try:
        result = orch._opus_targeted_revision(ORIGINAL_ARTICLE, ["fix the opening"], "Maya Flux", packet)
    finally:
        restore()
    check(
        "Opus targeted revision with a genuinely source-backed quote+attribution is ACCEPTED",
        result == grounded,
    )


def test_fable_polish_rewrite_rejects_primary_then_falls_back():
    """Primary attempt (_call_editorial_model, prefer_opus=True internally --
    but that's an implementation detail this test doesn't need to know about,
    it just controls what the call returns) fabricates a quote and gets
    rejected; falls through to _opus_targeted_revision, whose OWN call
    (_call_openai_compat_api) returns a clean, source-grounded revision."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    fabrication = ORIGINAL_ARTICLE + ' Deborah Antwi said "this changes everything" at the hearing.'
    grounded_fallback = ORIGINAL_ARTICLE + ' Jane Doe said "this was a difficult trade-off" to reporters.'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, *a, **k: fabrication,
        _call_openai_compat_api=lambda self, *a, **k: grounded_fallback,
    )
    try:
        result = orch._fable_polish_rewrite(ORIGINAL_ARTICLE, ["fix the opening"], "Maya Flux", "wry", packet)
    finally:
        restore()
    check(
        "primary rewrite attempt fabricates a quote -> rejected -> Opus fallback's clean "
        "revision is what's actually returned",
        result == grounded_fallback,
    )


def test_fable_polish_rewrite_rejects_both_primary_and_fallback():
    """Recreates the exact Phase 1.5B failure SHAPE: the primary rewrite
    attempt invents a quote, gets rejected, falls back to
    _opus_targeted_revision -- which ALSO invents a (different) unsupported
    quote and gets rejected too. Final result must be the untouched original
    article, not either fabrication -- this is the case that proves the
    guard is a real backstop, not just a speed bump on the common path."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    fabrication_1 = ORIGINAL_ARTICLE + ' Deborah Antwi said "this changes everything" at the hearing.'
    fabrication_2 = ORIGINAL_ARTICLE + ' Marcus Reyes said "nobody expected this" to the press.'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, *a, **k: fabrication_1,
        _call_openai_compat_api=lambda self, *a, **k: fabrication_2,
    )
    try:
        result = orch._fable_polish_rewrite(ORIGINAL_ARTICLE, ["fix the opening"], "Maya Flux", "wry", packet)
    finally:
        restore()
    check(
        "both the primary rewrite AND its Opus fallback fabricate an unsupported quote "
        "-- final result is the untouched original article, not either fabrication",
        result == ORIGINAL_ARTICLE,
    )


def test_fable_polish_rewrite_accepts_grounded_primary_attempt():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    grounded = ORIGINAL_ARTICLE + ' Jane Doe said "this was a difficult trade-off" to reporters.'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, *a, **k: grounded,
    )
    try:
        result = orch._fable_polish_rewrite(ORIGINAL_ARTICLE, ["fix the opening"], "Maya Flux", "wry", packet)
    finally:
        restore()
    check(
        "primary rewrite attempt with a source-backed quote is accepted, no fallback needed",
        result == grounded,
    )


def test_no_editorial_notes_short_circuits_before_any_call():
    """Both executors return article_body unchanged, with no LLM call at
    all, when there are no editorial notes to apply -- not part of the
    guard's job, but worth confirming the guard doesn't somehow get
    exercised on a no-op path."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    called = []
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: called.append(1) or "should never be used",
        _call_editorial_model=lambda self, *a, **k: called.append(1) or "should never be used",
    )
    try:
        r1 = orch._opus_targeted_revision(ORIGINAL_ARTICLE, [], "Maya Flux", packet)
        r2 = orch._fable_polish_rewrite(ORIGINAL_ARTICLE, [], "Maya Flux", "wry", packet)
    finally:
        restore()
    check("no editorial notes -> _opus_targeted_revision returns original untouched, no call made", r1 == ORIGINAL_ARTICLE and not called)
    check("no editorial notes -> _fable_polish_rewrite returns original untouched, no call made", r2 == ORIGINAL_ARTICLE and not called)


if __name__ == "__main__":
    test_opus_targeted_revision_rejects_misattributed_quote()
    test_opus_targeted_revision_accepts_grounded_quote()
    test_fable_polish_rewrite_rejects_primary_then_falls_back()
    test_fable_polish_rewrite_rejects_both_primary_and_fallback()
    test_fable_polish_rewrite_accepts_grounded_primary_attempt()
    test_no_editorial_notes_short_circuits_before_any_call()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All executor post-revision guard integration tests passed.")
