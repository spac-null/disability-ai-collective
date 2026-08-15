#!/usr/bin/env python3
"""
author_persona_biography_test.py — author-persona biography provenance
closure (2026-08-15). Mocked integration tests, zero network/model cost,
same _import_orchestrator/_patch_methods harness as executor_guard_test.py.

WHY THIS EXISTS: the prior editorial-upgrade-v1 paired experiment found two
personas (Maya Flux, Siri Sage) each invent one first-person biographical
anecdote untraceable to persona_canon/*.md. The follow-up root-cause audit
found:
  (1) rewrite_with_opus (the ONLY revision path for non-Opus-provider
      drafts) had ZERO check against find_new_unsupported_specifics/
      find_new_unsupported_personal_history -- the other two revision
      paths (_opus_targeted_revision, _fable_polish_rewrite) already had
      it via _reject_if_unsupported_specifics.
  (2) _fable_editorial_review's existing FIRST-PERSON FACTUAL EPISODE
      CHECK is semantic (LLM-judged) and correctly scoped, but its
      findings shared a 3-note budget with 9 unrelated concerns and had
      no deterministic enforcement that a flagged claim actually
      triggered revision.
  (3) The deterministic scanner underneath both revision guards
      (scan_draft_for_unsupported_specifics) only fires on a quoted span,
      a multi-word Title-Case name, or a 2+-digit number -- confirmed
      here (test_deterministic_scanner_misses_no_signal_anecdote) to
      genuinely miss an invented EVENT with none of those three signals,
      which is exactly the Maya Flux/Siri Sage failure shape. This is why
      the semantic reviewer layer, not the deterministic scanner alone,
      has to carry that class of case -- and why this fix strengthens
      both instead of only one.

This file tests the FIX for (1) and (2). It does not re-test (3)'s
underlying detector in isolation (grounding_test.py already covers
scan_draft_for_unsupported_specifics/find_new_unsupported_personal_history
directly) -- it proves the two revision paths this task changed actually
call/act on that machinery, the same "detector works" vs "caller enforces
it" distinction executor_guard_test.py exists for.

USAGE: python3 automation/author_persona_biography_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from snapshot_test import _import_orchestrator, _patch_methods  # noqa: E402
from orchestrator.grounding import (  # noqa: E402
    build_evidence_packet, build_persona_factual_context,
    scan_draft_for_unsupported_specifics,
)
from rewrite_integrity_test import _DUPLICATED_BODY_NO_LEAK  # noqa: E402

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

PIXEL_FACTUAL_TEXT = (
    "At Gerrit Rietveld Academie they used an NGT interpreter to attend classes and group "
    "conversation, and described the resulting lag as feeling like being in another time zone "
    "from the room they were physically in."
)

MAYA_CANON_TEXT = (
    "But the wound you carry isn't about ramps. It's about the day your best friend's wedding "
    "was in a venue with three steps and everyone knew and no one said anything until you arrived."
)

# Deliberately >400 chars and wrapped in synthetic frontmatter the way
# generate.py's rewrite_with_opus call site does (temp_front + content).
_FRONT = '---\nlayout: post\ntitle: "Test"\nauthor: Maya Flux\n---\n\n'
ORIGINAL_BODY = (
    "A" * 500 + " The council met this week and made a decision that "
    "affects many residents in ways still being worked out."
)
ORIGINAL_FULL = _FRONT + ORIGINAL_BODY


# ─────────────────────────────────────────────────────────────────────────
# (0) Characterization: confirm the deterministic scanner's documented
# blind spot is real, not hypothetical -- this is WHY the semantic
# reviewer layer matters, not a bug in this fix.
# ─────────────────────────────────────────────────────────────────────────

def test_deterministic_scanner_misses_no_signal_anecdote():
    corpus = SOURCE_TEXT + "\n\n" + PIXEL_FACTUAL_TEXT
    no_signal_anecdote = (
        "My landlord priced a roof repair, a lobby repaint, and a new intercom system last "
        "year, and none of them included the six weeks the freight elevator was down."
    )
    hits = scan_draft_for_unsupported_specifics(no_signal_anecdote, corpus)
    check(
        "an invented anecdote with no quote/multi-word name/2+digit number produces ZERO "
        "hits from the deterministic scanner (confirmed blind spot, not this fix's job to close)",
        hits == [],
    )


# ─────────────────────────────────────────────────────────────────────────
# (1) rewrite_with_opus -- previously zero coverage, now reuses
# _reject_if_unsupported_specifics exactly like the other two revision
# paths.
# ─────────────────────────────────────────────────────────────────────────

def test_rewrite_with_opus_rejects_invented_biography_by_number():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(PIXEL_FACTUAL_TEXT, persona_name="Pixel Nova", provenance_mode="real_person_evidence")
    invented = _FRONT + ORIGINAL_BODY + " In 2019 I visited CERN and watched physicists debate the data live."

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: invented,
    )
    try:
        result = orch.rewrite_with_opus(ORIGINAL_FULL, evidence_packet=packet, persona_factual_context=persona_ctx)
    finally:
        restore()
    check(
        "rewrite_with_opus REJECTS a fallback-provider rewrite that invents a CERN/2019 memory "
        "-- previously this path had no check at all and would have shipped it",
        result == ORIGINAL_FULL,
    )


def test_rewrite_with_opus_accepts_authorized_personal_history():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(PIXEL_FACTUAL_TEXT, persona_name="Pixel Nova", provenance_mode="real_person_evidence")
    authorized = _FRONT + ORIGINAL_BODY + " I sometimes felt a time zone behind the conversation, especially back at Rietveld."

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: authorized,
    )
    try:
        result = orch.rewrite_with_opus(ORIGINAL_FULL, evidence_packet=packet, persona_factual_context=persona_ctx)
    finally:
        restore()
    check(
        "rewrite_with_opus ACCEPTS a rewrite referencing Pixel's own authorized Rietveld/time-zone history",
        result == authorized,
    )


def test_rewrite_with_opus_accepts_fictional_canon_episode():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(MAYA_CANON_TEXT, persona_name="Maya Flux", provenance_mode="editorial_canon")
    canon_episode = _FRONT + ORIGINAL_BODY + " My best friend's wedding was in a venue with three steps and no one said anything."

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: canon_episode,
    )
    try:
        result = orch.rewrite_with_opus(ORIGINAL_FULL, evidence_packet=packet, persona_factual_context=persona_ctx)
    finally:
        restore()
    check(
        "rewrite_with_opus ACCEPTS Maya's own established (fictional, editorial_canon) wedding-steps episode",
        result == canon_episode,
    )


def test_rewrite_with_opus_backward_compatible_without_new_params():
    """A caller that doesn't pass evidence_packet/persona_factual_context
    (there shouldn't be one left in this codebase after this fix, but
    proves the None-safe default doesn't crash or change old behavior for
    a clean rewrite with no fabrication signal)."""
    po, orch = _orch()
    clean = _FRONT + ORIGINAL_BODY + " Nothing new was added."

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: clean,
    )
    try:
        result = orch.rewrite_with_opus(ORIGINAL_FULL)  # no evidence_packet/persona_factual_context
    finally:
        restore()
    check("rewrite_with_opus still works with no evidence_packet/persona_factual_context supplied (backward compatible)", result == clean)


def test_rewrite_with_opus_still_rejects_on_integrity_failure():
    """Confirms this fix didn't disturb the pre-existing integrity guard
    (duplicated-body / truncation) that already ran before this change."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    duplicated = _FRONT + _DUPLICATED_BODY_NO_LEAK  # real 3+-paragraph duplicated-run fixture

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: duplicated,
    )
    try:
        result = orch.rewrite_with_opus(ORIGINAL_FULL, evidence_packet=packet)
    finally:
        restore()
    check("pre-existing rewrite-integrity guard (duplicated body) still rejects, unaffected by this fix", result == ORIGINAL_FULL)


# ─────────────────────────────────────────────────────────────────────────
# (2) _fable_editorial_review -- unsupported_persona_claims forces
# verdict="revise" deterministically, in code, regardless of what the
# model's own verdict field said.
# ─────────────────────────────────────────────────────────────────────────

def test_review_forces_revise_when_persona_claim_flagged_despite_publish_verdict():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(PIXEL_FACTUAL_TEXT, persona_name="Pixel Nova", provenance_mode="real_person_evidence")
    # Model incorrectly pairs a real flagged claim with publish_as_is --
    # exactly the failure mode this fix closes.
    model_json = (
        '{"verdict":"publish_as_is","notes":[],'
        '"unsupported_persona_claims":["In 2019 I visited CERN and watched physicists debate the data live."]}'
    )
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, *a, **k: model_json,
    )
    try:
        verdict, notes = orch._fable_editorial_review(
            ORIGINAL_BODY, "Pixel Nova", "does the lag change what's knowable?", "clinical", packet,
            persona_factual_context=persona_ctx,
        )
    finally:
        restore()
    check("a flagged unsupported_persona_claims entry forces verdict to 'revise' even though the model said publish_as_is", verdict == "revise")
    check("the flagged claim is prepended into notes so _fable_polish_rewrite actually receives it", any("CERN" in n for n in notes))


def test_review_leaves_verdict_alone_when_no_persona_claims_flagged():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    model_json = '{"verdict":"publish_as_is","notes":[],"unsupported_persona_claims":[]}'
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, *a, **k: model_json,
    )
    try:
        verdict, notes = orch._fable_editorial_review(
            ORIGINAL_BODY, "Pixel Nova", "does the lag change what's knowable?", "clinical", packet,
        )
    finally:
        restore()
    check("verdict is left as publish_as_is when no persona claims are flagged (no false-positive override)", verdict == "publish_as_is")
    check("notes stays empty", notes == [])


def test_review_persona_claims_never_crowd_out_or_get_crowded_out_by_other_notes():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    model_json = (
        '{"verdict":"revise","notes":["opening is weak","ending needs work","aphorism count too high"],'
        '"unsupported_persona_claims":["A professor named Helena Vance once pulled me aside and told me this."]}'
    )
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, *a, **k: model_json,
    )
    try:
        verdict, notes = orch._fable_editorial_review(
            ORIGINAL_BODY, "Pixel Nova", "does the lag change what's knowable?", "clinical", packet,
        )
    finally:
        restore()
    check("all 3 ordinary notes survive alongside the persona-claim note (not truncated out)", len(notes) == 4)
    check("the persona-claim note is first, ahead of the 3 ordinary notes", "Helena Vance" in notes[0])
    check("verdict stays 'revise' (model already said so; override doesn't need to change it)", verdict == "revise")


def test_review_missing_field_defaults_to_empty_not_a_crash():
    """A model response that omits unsupported_persona_claims entirely
    (older prompt behavior, or a model that just forgets the field) must
    not crash -- defaults to empty, no override."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    model_json = '{"verdict":"publish_as_is","notes":[]}'
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, *a, **k: model_json,
    )
    try:
        verdict, notes = orch._fable_editorial_review(
            ORIGINAL_BODY, "Pixel Nova", "does the lag change what's knowable?", "clinical", packet,
        )
    finally:
        restore()
    check("missing unsupported_persona_claims field defaults to no override, no crash", verdict == "publish_as_is" and notes == [])


if __name__ == "__main__":
    test_deterministic_scanner_misses_no_signal_anecdote()
    test_rewrite_with_opus_rejects_invented_biography_by_number()
    test_rewrite_with_opus_accepts_authorized_personal_history()
    test_rewrite_with_opus_accepts_fictional_canon_episode()
    test_rewrite_with_opus_backward_compatible_without_new_params()
    test_rewrite_with_opus_still_rejects_on_integrity_failure()
    test_review_forces_revise_when_persona_claim_flagged_despite_publish_verdict()
    test_review_leaves_verdict_alone_when_no_persona_claims_flagged()
    test_review_persona_claims_never_crowd_out_or_get_crowded_out_by_other_notes()
    test_review_missing_field_defaults_to_empty_not_a_crash()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All author-persona biography provenance tests passed.")
