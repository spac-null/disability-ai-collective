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
from orchestrator.grounding import build_evidence_packet, build_persona_factual_context  # noqa: E402

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


# ─────────────────────────────────────────────────────────────────────────
# Executor persona-history guard (Phase 1.6 continuation, added same day as
# the writer/reviewer AUTHORIZED PERSONAL HISTORY boundary): the tests above
# only ever supplied evidence_packet, never persona_factual_context -- they
# prove the STORY-evidence guard works, but say nothing about the
# persona-history guard added alongside _reject_if_unsupported_specifics'
# second check. These tests supply persona_factual_context explicitly and
# exercise find_new_unsupported_personal_history through the real executor
# call, the same "detector works in isolation" vs "executor actually calls
# it and acts on rejection" distinction this whole module exists to prove.
# ─────────────────────────────────────────────────────────────────────────

SOURCE_TEXT_ROSSI = (
    'On 6 August 2026, wheelchair user Elena Rossi tested the temporary entrance. '
    '"I can enter independently now, but the sign still sends me toward the stairs," Rossi said.'
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


def test_opus_targeted_revision_rejects_invented_personal_memory():
    """The seam this session's re-audit found: find_new_unsupported_specifics
    only checks against evidence_packet's source_text, so an executor
    revision introducing a fabricated first-person biographical episode had
    nothing to catch it even when persona_factual_context existed elsewhere
    in the pipeline. "In 2019 I visited CERN" is absent from both the source
    and PIXEL_FACTUAL_TEXT -- must be rejected."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT_ROSSI)
    persona_ctx = build_persona_factual_context(PIXEL_FACTUAL_TEXT, persona_name="Pixel Nova", provenance_mode="real_person_evidence")
    invented_memory = ORIGINAL_ARTICLE + ' In 2019 I visited CERN and watched physicists debate the data live.'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: invented_memory,
    )
    try:
        result = orch._opus_targeted_revision(
            ORIGINAL_ARTICLE, ["add a personal example"], "Pixel Nova", packet,
            persona_factual_context=persona_ctx,
        )
    finally:
        restore()
    check(
        "executor request to 'add a personal example' does NOT invent a CERN/2019 memory "
        "-- original article returned unchanged",
        result == ORIGINAL_ARTICLE,
    )


def test_opus_targeted_revision_accepts_authorized_personal_history():
    """Using the persona's own AUTHORIZED PERSONAL HISTORY material (Rietveld/
    time-zone) must be accepted -- the guard's job is to stop invention, not
    to block a persona from ever mentioning their own real, supplied life."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT_ROSSI)
    persona_ctx = build_persona_factual_context(PIXEL_FACTUAL_TEXT, persona_name="Pixel Nova", provenance_mode="real_person_evidence")
    authorized_memory = ORIGINAL_ARTICLE + ' I sometimes felt a time zone behind the conversation, especially back at Rietveld.'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: authorized_memory,
    )
    try:
        result = orch._opus_targeted_revision(
            ORIGINAL_ARTICLE, ["add a personal example"], "Pixel Nova", packet,
            persona_factual_context=persona_ctx,
        )
    finally:
        restore()
    check(
        "referencing Pixel's own AUTHORIZED PERSONAL HISTORY (Rietveld/time-zone) is ACCEPTED",
        result == authorized_memory,
    )


def test_opus_targeted_revision_accepts_fictional_canon_episode():
    """A fictional persona's own editorial_canon material (Maya's established
    wedding-steps wound) is legitimate for HER to reference -- editorial_canon
    is a different, weaker-verification provenance class than
    real_person_evidence (documented, not silently treated as equal), but
    still authorizes the persona's own established episode, not an
    invented one."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT_ROSSI)
    persona_ctx = build_persona_factual_context(MAYA_CANON_TEXT, persona_name="Maya Flux", provenance_mode="editorial_canon")
    canon_episode = ORIGINAL_ARTICLE + " My best friend's wedding was in a venue with three steps and no one said anything."

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: canon_episode,
    )
    try:
        result = orch._opus_targeted_revision(
            ORIGINAL_ARTICLE, ["add a personal example"], "Maya Flux", packet,
            persona_factual_context=persona_ctx,
        )
    finally:
        restore()
    check(
        "a fictional persona's own editorial_canon episode (Maya's wedding-steps wound) is ACCEPTED",
        result == canon_episode,
    )


def test_opus_targeted_revision_rejects_invented_biography_by_name():
    """Same failure class as the CERN test, but via a fabricated named
    person rather than a fabricated number -- proves the guard catches both
    signal shapes scan_draft_for_unsupported_specifics checks."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT_ROSSI)
    persona_ctx = build_persona_factual_context(PIXEL_FACTUAL_TEXT, persona_name="Pixel Nova", provenance_mode="real_person_evidence")
    invented_person = ORIGINAL_ARTICLE + ' A professor named Helena Vance once pulled me aside after a lecture and told me this changes everything.'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: invented_person,
    )
    try:
        result = orch._opus_targeted_revision(
            ORIGINAL_ARTICLE, ["add a personal example"], "Pixel Nova", packet,
            persona_factual_context=persona_ctx,
        )
    finally:
        restore()
    check(
        "a new invented named person in a fabricated personal anecdote is REJECTED",
        result == ORIGINAL_ARTICLE,
    )


def test_story_source_quote_unaffected_by_persona_history_guard():
    """The persona-history guard must not interfere with the pre-existing
    story-evidence guard: a revision that preserves Rossi's real, sourced
    quote verbatim -- with persona_factual_context ALSO supplied -- must
    still be accepted, proving the two guards run independently and
    neither's corpus accidentally narrows the other's."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT_ROSSI)
    persona_ctx = build_persona_factual_context(PIXEL_FACTUAL_TEXT, persona_name="Pixel Nova", provenance_mode="real_person_evidence")
    preserved_quote = ORIGINAL_ARTICLE + ' Rossi said, "I can enter independently now, but the sign still sends me toward the stairs," reflecting on the encounter.'

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: preserved_quote,
    )
    try:
        result = orch._opus_targeted_revision(
            ORIGINAL_ARTICLE, ["tighten the ending"], "Pixel Nova", packet,
            persona_factual_context=persona_ctx,
        )
    finally:
        restore()
    check(
        "Rossi's real, sourced quote survives a revision unaffected by the new persona-history guard",
        result == preserved_quote,
    )


def test_fable_polish_rewrite_primary_path_rejects_invented_memory_and_captures_prompt():
    """Every persona-history test above exercises _opus_targeted_revision
    directly. Production's PRIMARY revision path is _fable_polish_rewrite,
    with _opus_targeted_revision only as its fallback -- the code threads
    persona_factual_context through Fable and then unchanged into that
    fallback, but nothing above proves the ACTUAL PROMPT Fable receives
    contains the persona-history material, not just that the eventual
    return value is safe. Captures the real (system, user) prompt sent to
    the Fable rewrite call and asserts on it directly, the same
    capture-the-actual-prompt discipline writer_prompt_test.py uses for the
    writer stage."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT_ROSSI)
    persona_ctx = build_persona_factual_context(PIXEL_FACTUAL_TEXT, persona_name="Pixel Nova", provenance_mode="real_person_evidence")
    invented_memory = ORIGINAL_ARTICLE + ' In 2019 I visited CERN and watched physicists debate the data live.'
    clean_fallback = ORIGINAL_ARTICLE + ' I sometimes felt a time zone behind the conversation, especially back at Rietveld.'

    captured = {}

    def capturing_fable_rewrite(self, system, user, *a, **k):
        captured["system"] = system
        captured["user"] = user
        return invented_memory

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=capturing_fable_rewrite,
        _call_openai_compat_api=lambda self, *a, **k: clean_fallback,
    )
    try:
        result = orch._fable_polish_rewrite(
            ORIGINAL_ARTICLE, ["add a personal example"], "Pixel Nova", "wary", packet,
            persona_factual_context=persona_ctx,
        )
    finally:
        restore()

    full_prompt = captured.get("system", "") + "\n" + captured.get("user", "")
    check("Fable executor prompt was actually captured", bool(full_prompt.strip()))
    check("captured Fable prompt contains PERSONA PERSONAL-HISTORY CONTRACT", "PERSONA PERSONAL-HISTORY CONTRACT" in full_prompt)
    check("captured Fable prompt contains the AUTHORIZED PERSONAL HISTORY heading", "AUTHORIZED PERSONAL HISTORY" in full_prompt)
    check(
        "captured Fable prompt contains Pixel's real Rietveld/time-zone factual material",
        "Rietveld" in full_prompt and "time zone" in full_prompt,
    )
    check(
        "captured Fable prompt contains the story SOURCE MATERIAL block (Rossi)",
        "SOURCE MATERIAL" in full_prompt and "Rossi" in full_prompt,
    )
    check("captured Fable prompt does NOT contain PENDING VERIFICATION", "PENDING VERIFICATION" not in full_prompt)
    check("captured Fable prompt does NOT contain the notary anecdote", "notary" not in full_prompt.lower())

    check(
        "primary Fable rewrite's invented CERN/2019 memory is rejected via the real production "
        "entry point -- Opus fallback's clean revision is what's actually returned",
        result == clean_fallback,
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
    test_opus_targeted_revision_rejects_invented_personal_memory()
    test_opus_targeted_revision_accepts_authorized_personal_history()
    test_opus_targeted_revision_accepts_fictional_canon_episode()
    test_opus_targeted_revision_rejects_invented_biography_by_name()
    test_story_source_quote_unaffected_by_persona_history_guard()
    test_fable_polish_rewrite_primary_path_rejects_invented_memory_and_captures_prompt()
    test_no_editorial_notes_short_circuits_before_any_call()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All executor post-revision guard integration tests passed.")
