#!/usr/bin/env python3
"""
author_persona_biography_nonopus_closure_test.py — AP1 edge-case closure
(2026-08-15, follow-up to author_persona_biography_test.py / commit a73d71a).

THE EDGE CASE: a73d71a closed two gaps (rewrite_with_opus's own diff-based
guard; _fable_editorial_review's deterministic verdict override) but left a
third path open: a NON-Opus initial draft that ALREADY contains an
unsupported persona-biography claim, where rewrite_with_opus's Opus rewrite
PRESERVES that same claim rather than introducing a new one.

Why the existing (post-a73d71a) guards do not catch this:
  - rewrite_with_opus's guard (_reject_if_unsupported_specifics /
    find_new_unsupported_personal_history) is a DIFF between the original
    and revised text -- a claim present on BOTH sides cancels out; only
    claims NEW to the rewrite are flagged (see rewrite_with_opus's own
    docstring, and _reject_if_unsupported_specifics's).
  - _fable_editorial_review's FIRST-PERSON FACTUAL EPISODE CHECK, before
    this closure, ran ONLY when generate.py's is_opus was True (confirmed
    by direct code read of generate.py's Step 3b-i, prior to this fix) --
    a non-Opus original draft never reached it at all.
  - fact_check.py's live web fact-check does not fill the gap either:
    _extract_verifiable_claims' own QUOTE category is explicitly scoped to
    a claim "attributed to a specific named real person, OTHER THAN THE
    FIRST-PERSON NARRATOR" -- persona autobiography is out of scope there
    by design, confirmed by direct code read, not inferred from the name.
  - publish_best.py's promotion gate only skips drafts carrying
    `fact_check_status: blocked` in frontmatter (confirmed by direct code
    read: the only condition checked is `fm.get("fact_check_status") ==
    "blocked"`) -- it does NOT check the review sidecar's CLEAN/FLAGGED
    status, and review.py's own comment (validate_article, "Web fact-check
    — quotes, studies, stats, events") documents that advisory-only
    findings mark a review FLAGGED WITHOUT setting fact_check_status:
    blocked. So even if some other advisory check had flagged the claim,
    that alone would not have stopped promotion.

THE FIX (this closure, same day): generate.py's Step 3b-i previously ran
the Fable editorial review + polish/executor guard chain (llm.py's
_fable_editorial_review / _fable_polish_rewrite) only for is_opus == True.
Extracted into a new shared method, _run_persona_biography_editorial_pass
(llm.py), and now called from BOTH branches: once for Opus-original
content (unchanged behavior/timing), and once more for non-Opus content
AFTER rewrite_with_opus produces its final prose (new). No new detector --
same reviewer, same deterministic unsupported_persona_claims override, same
_fable_polish_rewrite/_opus_targeted_revision executor chain a73d71a already
hardened. First person is never banned: only a claim the semantic reviewer
itself judges as an untraceable biographical EVENT is ever touched.

Mocked integration tests, zero network/model cost, same
_import_orchestrator/_patch_methods harness as author_persona_biography_test.py.

USAGE: python3 automation/author_persona_biography_nonopus_closure_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from snapshot_test import _import_orchestrator, _patch_methods  # noqa: E402
from orchestrator.grounding import (  # noqa: E402
    build_evidence_packet, build_persona_factual_context,
)

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def _orch():
    po = _import_orchestrator()
    return po, po.ProductionOrchestrator()


SOURCE_TEXT = (
    "The council voted 6-3 on Tuesday. Jane Doe said \"this was a difficult "
    "trade-off\" during the meeting. The vote affected 400 residents."
)

# Maya Flux's only authorized canon episode (same fixture as
# author_persona_biography_test.py's MAYA_CANON_TEXT) -- a wedding, three
# steps, no childhood/parent/protest content anywhere in it.
MAYA_CANON_TEXT = (
    "But the wound you carry isn't about ramps. It's about the day your best friend's wedding "
    "was in a venue with three steps and everyone knew and no one said anything until you arrived."
)

_FRONT = '---\nlayout: post\ntitle: "Test"\nauthor: Maya Flux\n---\n\n'
BASE_BODY = (
    "A" * 500 + " The council met this week and made a decision that "
    "affects many residents in ways still being worked out."
)

# Unambiguous invented childhood/family biographical event, absent from
# MAYA_CANON_TEXT and SOURCE_TEXT entirely -- the task's own example shape.
UNSUPPORTED_CLAIM = (
    "When I was twelve, my mother took me to a protest downtown that changed "
    "how I have read every ramp and doorway since."
)

# A different wording of the SAME already-authorized wedding-steps fact --
# tests that a DIFFERENT WORDING of an authorized event is not treated as a
# new violation (this fix must not become a phrase-ban).
CANON_REWORDING = (
    "My best friend once got married in a place with three steps at the door, "
    "and everyone there already knew what that meant before I arrived."
)

# Present-tense opinion/attention in first person -- not a biographical
# event, must never be treated as one.
NON_BIOGRAPHICAL_FIRST_PERSON = (
    "I keep coming back to how casually the notice describes the stairs, "
    "as if a doorway were a detail instead of a decision."
)


def _make_editorial_model_sequence(*responses):
    """_call_editorial_model is used by BOTH _fable_editorial_review (JSON
    verdict) and _fable_polish_rewrite (plain rewritten text) -- this
    harness needs a stateful mock that returns a different canned response
    per call, in order, exactly like the real call sequence
    _run_persona_biography_editorial_pass makes."""
    calls = {"n": 0}

    def _mock(self, *a, **k):
        i = calls["n"]
        calls["n"] += 1
        return responses[min(i, len(responses) - 1)]
    return _mock


# ─────────────────────────────────────────────────────────────────────────
# (1) Characterize the gap: rewrite_with_opus ALONE (unchanged by this fix)
# preserves an unsupported claim that was already in the original draft --
# proving the diff-based guard's blind spot is real, not hypothetical, and
# that nothing before this fix's new call site would have caught it.
# ─────────────────────────────────────────────────────────────────────────

def test_rewrite_with_opus_alone_preserves_preexisting_unsupported_claim():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(MAYA_CANON_TEXT, persona_name="Maya Flux", provenance_mode="editorial_canon")
    non_opus_original = _FRONT + BASE_BODY + " " + UNSUPPORTED_CLAIM
    # Opus "rewrite" that keeps the exact same claim -- polishing prose,
    # not touching the biographical content, the realistic preserved-claim shape.
    rewritten_same_claim = non_opus_original

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: rewritten_same_claim,
    )
    try:
        result = orch.rewrite_with_opus(non_opus_original, evidence_packet=packet, persona_factual_context=persona_ctx)
    finally:
        restore()
    check(
        "GAP CONFIRMED: rewrite_with_opus's own guard does not strip an unsupported claim "
        "already present before the rewrite (diff-based guard only catches NEW claims)",
        UNSUPPORTED_CLAIM in result,
    )


# ─────────────────────────────────────────────────────────────────────────
# (2) THE FIX: the full non-Opus lifecycle as generate.py now actually
# wires it -- rewrite_with_opus, then _run_persona_biography_editorial_pass
# -- fails closed on the preserved claim before any downstream stage
# (fact_check.py, publish_best.py) ever sees it.
# ─────────────────────────────────────────────────────────────────────────

def test_full_nonopus_lifecycle_blocks_preserved_unsupported_claim():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(MAYA_CANON_TEXT, persona_name="Maya Flux", provenance_mode="editorial_canon")
    non_opus_original_full = _FRONT + BASE_BODY + " " + UNSUPPORTED_CLAIM

    # Step 1 (rewrite_with_opus): preserves the claim, same as the gap test above.
    restore1 = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: non_opus_original_full,
    )
    try:
        rewritten_full = orch.rewrite_with_opus(non_opus_original_full, evidence_packet=packet, persona_factual_context=persona_ctx)
    finally:
        restore1()
    # Strip synthetic frontmatter the same way generate.py's non-Opus branch does.
    fm_end = rewritten_full.find("\n---\n", 3)
    content_after_rewrite = rewritten_full[fm_end + 5:].lstrip("\n")
    check("setup: claim still present after rewrite_with_opus alone (same gap as test above)", UNSUPPORTED_CLAIM in content_after_rewrite)

    # Step 2 (the new call site): _run_persona_biography_editorial_pass.
    # Model is deliberately worst-cased: verdict says publish_as_is (the
    # reviewer's own verdict field can't be trusted alone, same reasoning
    # a73d71a already established) but correctly flags the claim in the
    # dedicated unsupported_persona_claims field -- code must force revise.
    review_json = (
        '{"verdict":"publish_as_is","notes":[],'
        f'"unsupported_persona_claims":["{UNSUPPORTED_CLAIM}"]}}'
    )
    # Same "A"*500 padding block as the input, UNCHANGED -- a real polish pass
    # rewrites the flagged sentence, not unrelated filler; keeping the padding
    # identical also avoids a test artifact where a differently-charactered
    # padding block gets misread by the deterministic guard as a "new named
    # entity" (confirmed while building this test -- an artifact of this test's
    # own fixture shape, not a pipeline behavior).
    fixed_content = (
        "A" * 500 + " The council met this week and made a decision that "
        "affects many residents in ways still being worked out. The piece stays "
        "with the vote and what it changes, without reaching for a childhood memory."
    )
    restore2 = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=_make_editorial_model_sequence(review_json, fixed_content),
    )
    try:
        final_content, reviewer_ran, executor_ran = orch._run_persona_biography_editorial_pass(
            content_after_rewrite, "Maya Flux", "what the vote actually changes", "warm",
            packet, persona_ctx, raw_draft_guard_hits=[],
        )
    finally:
        restore2()

    check("DOES THE PIPELINE FAIL CLOSED: reviewer ran on the non-Opus post-rewrite content", reviewer_ran is True)
    check("DOES THE PIPELINE FAIL CLOSED: executor (polish rewrite) ran because a persona claim was flagged", executor_ran is True)
    check(
        "DOES THE PIPELINE FAIL CLOSED: the preserved unsupported claim is GONE from the final content "
        "that would reach fact_check.py / publish_best.py",
        UNSUPPORTED_CLAIM not in final_content,
    )
    check("the final content is the repaired text, not silently deleted down to nothing", len(final_content) > 400)


# ─────────────────────────────────────────────────────────────────────────
# (3) Control cases -- the fix must not ban first person or invent a
# biography ontology; only a reviewer-confirmed unsupported EVENT is acted on.
# ─────────────────────────────────────────────────────────────────────────

def test_control_authorized_canon_event_survives():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(MAYA_CANON_TEXT, persona_name="Maya Flux", provenance_mode="editorial_canon")
    content = BASE_BODY + " " + CANON_REWORDING
    # Reviewer correctly finds nothing unsupported -- a different wording of
    # an already-authorized fact is not a new event.
    review_json = '{"verdict":"publish_as_is","notes":[],"unsupported_persona_claims":[]}'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=_make_editorial_model_sequence(review_json),
    )
    try:
        final_content, reviewer_ran, executor_ran = orch._run_persona_biography_editorial_pass(
            content, "Maya Flux", "what the vote actually changes", "warm",
            packet, persona_ctx, raw_draft_guard_hits=[],
        )
    finally:
        restore()
    check("CONTROL: an authorized canon event (reworded) survives unchanged", final_content == content)
    check("CONTROL: no executor call made when nothing is flagged", executor_ran is False)


def test_control_non_biographical_first_person_survives():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(MAYA_CANON_TEXT, persona_name="Maya Flux", provenance_mode="editorial_canon")
    content = BASE_BODY + " " + NON_BIOGRAPHICAL_FIRST_PERSON
    review_json = '{"verdict":"publish_as_is","notes":[],"unsupported_persona_claims":[]}'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=_make_editorial_model_sequence(review_json),
    )
    try:
        final_content, reviewer_ran, executor_ran = orch._run_persona_biography_editorial_pass(
            content, "Maya Flux", "what the vote actually changes", "warm",
            packet, persona_ctx, raw_draft_guard_hits=[],
        )
    finally:
        restore()
    check(
        "CONTROL: non-biographical first person (present-tense attention, no event) survives untouched -- "
        "this fix does not ban first person generally",
        final_content == content,
    )
    check("CONTROL: no executor call made for non-biographical first person", executor_ran is False)


def test_control_unsupported_event_introduced_only_by_rewrite_still_blocked():
    """Confirms a73d71a's ALREADY-ADDED rewrite_with_opus guard (not touched
    by this closure) still rejects a claim introduced BY the rewrite itself
    -- this fix is additive, not a replacement for that guard."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(MAYA_CANON_TEXT, persona_name="Maya Flux", provenance_mode="editorial_canon")
    # Signal-bearing (Title-Case name + a 4-digit year), same shape as
    # author_persona_biography_test.py's existing CERN/2019 case -- the
    # deterministic diff guard only fires on a quoted span, a multi-word
    # Title-Case name, or a 2+-digit number (documented blind spot,
    # confirmed separately by this closure's own gap-characterization test
    # above and by author_persona_biography_test.py's
    # test_deterministic_scanner_misses_no_signal_anecdote); a claim with
    # none of those three signals is a known, pre-existing, unrelated blind
    # spot, not what this control case is checking.
    clean_original = _FRONT + BASE_BODY + " The piece stays with the vote itself."
    rewrite_introduces_new_claim = (
        clean_original + " In 2019 I visited CERN and watched physicists debate the data live."
    )

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: rewrite_introduces_new_claim,
    )
    try:
        result = orch.rewrite_with_opus(clean_original, evidence_packet=packet, persona_factual_context=persona_ctx)
    finally:
        restore()
    check(
        "CONTROL: an unsupported event introduced ONLY by the rewrite is still rejected by the "
        "pre-existing (a73d71a) rewrite_with_opus guard -- unaffected by this closure",
        result == clean_original,
    )


if __name__ == "__main__":
    test_rewrite_with_opus_alone_preserves_preexisting_unsupported_claim()
    test_full_nonopus_lifecycle_blocks_preserved_unsupported_claim()
    test_control_authorized_canon_event_survives()
    test_control_non_biographical_first_person_survives()
    test_control_unsupported_event_introduced_only_by_rewrite_still_blocked()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All checks passed.")
    sys.exit(0)
