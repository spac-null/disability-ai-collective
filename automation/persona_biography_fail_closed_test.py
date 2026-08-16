#!/usr/bin/env python3
"""
persona_biography_fail_closed_test.py — author-persona biography DETECTED-BUT-
UNCORRECTED fail-closed closure (2026-08-16). Mocked integration tests, zero
network/model cost, same _import_orchestrator/_patch_methods harness as
author_persona_biography_test.py.

WHY THIS EXISTS: the CripMinds post-release five-article evaluation batch
(691c365) found the AP1/APE2 semantic detector (_fable_editorial_review's
unsupported_persona_claims field) working correctly 5/5 times, but the
correction step -- _fable_polish_rewrite / _opus_targeted_revision, run from
_run_persona_biography_editorial_pass -- only succeeded 3/5 times. Both
survivors:
  - Article 5 ("Nine Codecs and Not One of Them Is For Her"): a flagged
    invented elaboration on Siri Sage's real canon fact (her mother is an
    audiologist -- the "thirty years in Edinburgh... fitting-room" detail was
    not) shipped verbatim in the final draft.
  - Article 7 ("23,000 Jobs and the Question Nobody Asks"): a flagged invented
    elaboration on Maya Flux's real canon fact (father drove route 4735 for
    22 years -- "when his knees went" was not) shipped verbatim, WITH
    fact_check_status: verified in the frontmatter -- an entirely separate,
    unrelated fact-check pass found the article's OTHER claims fine and had
    no way to know a persona-biography claim was still unresolved.

Root cause, confirmed by reading the code (not assumed): both cases coincided
with `_run_persona_biography_editorial_pass` recording an `editorial_revision`
degradation (the rewrite pass returned content byte-identical to the
pre-revision draft). `_compute_should_block` (generate.py) already existed as
the promotion-blocking policy, but only `fable_brief` and `gate_llm` blocked
ALONE -- a lone `editorial_revision` only counted toward its "2+ distinct
stages" threshold. So a KNOWN, specifically-detected unsupported claim could
survive into a `fact_check_status: verified` final candidate whenever nothing
else also degraded in the same run.

Nothing previously re-checked that a "revise" verdict driven by a flagged
persona claim actually removed that claim's text -- this file tests the fix
that closes that gap: `LLMMixin._persona_claims_unresolved` (a deterministic
recheck of the flagged claim's quoted text against the post-revision content,
independent of whether _fable_polish_rewrite changed anything else) and
`_compute_should_block` now also blocking alone on the new
`persona_biography_unresolved` stage it appends.

This is NOT a new semantic detector -- every test below starts from a claim
_fable_editorial_review already flagged (mocked exactly the way
author_persona_biography_test.py mocks it). No phrase list, no biography
ontology, no change to detection itself.

USAGE: python3 automation/persona_biography_fail_closed_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import json as _json
import re
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


def _orch():
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    orch._degraded_stages = []  # real production_orchestrator.py.__init__ already does this;
    # set explicitly here so every test starts from a known-clean list regardless of
    # ProductionOrchestrator's own init order.
    return po, orch


def _sequenced(responses):
    """Returns a _call_editorial_model-shaped mock that returns `responses[i]`
    on the i-th call (clamped to the last entry past the end) -- review is
    always call 0, a polish-rewrite attempt is always call 1+, matching
    _run_persona_biography_editorial_pass's real, deterministic call order."""
    state = {"n": 0}

    def _mock(self, system, user, max_tokens=1200, timeout=60, prefer_opus=False):
        i = min(state["n"], len(responses) - 1)
        state["n"] += 1
        return responses[i]
    return _mock


SOURCE_TEXT = (
    "The council voted 6-3 on Tuesday. Jane Doe said \"this was a difficult "
    "trade-off\" during the meeting. The vote affected 400 residents."
)

# Mirrors the real Article 5 finding exactly (see captured.json in the
# preserved evaluation artifacts): mother-as-audiologist IS canon; the
# duration/scene are invented.
SIRI_CANON_TEXT = (
    "Your mother spent her working life as an audiologist. That is canon. "
    "No further detail about her career -- duration, city, or clinical scene -- is authorized."
)
FLAGGED_QUOTE = (
    "my mother, who spent thirty years in Edinburgh as an audiologist, "
    "sitting across from people while she fitted their aids"
)
# Realistic prose, not repeated-letter padding -- a run of the same character
# used as filler in an earlier draft of these fixtures was itself getting
# picked up by the deterministic new-entity scanner as a "possible named
# entity" once a differently-capitalized word followed it in a revised
# version, which is a real property of that scanner worth not fighting in a
# test. Reused byte-identical across every fixture below except the one
# sentence each test is actually about, so nothing in the shared filler ever
# reads as "new" between original and revised.
_FILLER = (
    "This piece opens with several sentences of scene-setting context about "
    "the underlying story before turning to its actual argument, the way "
    "most pieces on this publication do, and closes with a similar amount of "
    "ordinary prose restating the stakes -- present here only to give these "
    "fixtures a realistic overall length for the length-ratio and integrity "
    "checks a real revision pass is checked against, not to carry any "
    "content of its own worth analyzing on its own terms."
)
BASE_DRAFT = _FILLER + " I keep thinking about " + FLAGGED_QUOTE + ". " + _FILLER

# Matches the REAL Fable output shape exactly (see the preserved Article 5
# captured.json): the model embeds the quoted claim plus trailing explanation
# in one string -- NOT the bare claim text alone -- which is what
# _extract_flagged_persona_quote's regex is built to pull the quote back out
# of.
FLAGGED_CLAIM_ENTRY = (
    f'"{FLAGGED_QUOTE}" — the mother-as-audiologist fact is canon, but the '
    "thirty-year duration and the fitting-room scene are new biographical "
    "specifics not in the supplied canon"
)

REVIEW_JSON_WITH_CLAIM = _json.dumps({
    "verdict": "publish_as_is",  # deliberately wrong -- code must force "revise" regardless
    "notes": [],
    "unsupported_persona_claims": [FLAGGED_CLAIM_ENTRY],
})
REVIEW_JSON_NO_CLAIM_BUT_CRAFT_NOTES = _json.dumps({
    "verdict": "revise",
    "notes": ["opening is weak", "ending needs work"],
    "unsupported_persona_claims": [],
})


# ─────────────────────────────────────────────────────────────────────────
# (1) Article-5-shaped regression fixture: known unsupported elaboration +
# revision failure -> blocked.
# ─────────────────────────────────────────────────────────────────────────

def test_article5_shaped_unresolved_claim_appends_new_stage_and_blocks():
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(SIRI_CANON_TEXT, persona_name="Siri Sage", provenance_mode="real_person_evidence")

    restore = _patch_methods(
        po.ProductionOrchestrator,
        # Call 0: review, flags FLAGGED_QUOTE. Call 1+: _fable_polish_rewrite's
        # own attempt returns None (total failure) every time it's asked.
        _call_editorial_model=_sequenced([REVIEW_JSON_WITH_CLAIM, None]),
        # _opus_targeted_revision's fallback call (a DIFFERENT method) also
        # fails, so the whole revision chain returns article_body unchanged --
        # exactly the observed Article 5/7 degradation shape.
        _call_openai_compat_api=lambda self, *a, **k: None,
    )
    try:
        content, reviewer_ran, executor_ran = orch._run_persona_biography_editorial_pass(
            BASE_DRAFT, "Siri Sage", "does the codec argument hold?", "wry",
            packet, persona_ctx, [],
        )
    finally:
        restore()

    check("content is unchanged (total revision failure, matches the real Article 5/7 shape)", content == BASE_DRAFT)
    check("reviewer_ran is True", reviewer_ran is True)
    check("executor_ran is True (a revision attempt was made)", executor_ran is True)
    check("'editorial_revision' recorded (pre-existing behavior, unchanged by this fix)", "editorial_revision" in orch._degraded_stages)
    check("NEW: 'persona_biography_unresolved' recorded", "persona_biography_unresolved" in orch._degraded_stages)
    check(
        "NEW: _compute_should_block now blocks this run "
        "(previously: {'editorial_revision'} alone did not block -- this is the actual Article 5 bug)",
        po.ProductionOrchestrator._compute_should_block(orch._degraded_stages) is True,
    )


# ─────────────────────────────────────────────────────────────────────────
# (2) Article-7-shaped regression fixture: known unsupported elaboration +
# revision failure + ordinary fact-check otherwise verifies -> STILL blocked.
# This is the essential case: fact_check_status is computed by a completely
# separate mechanism (review.py's validate_article) that never looks at
# _degraded_stages/_compute_should_block's output going the other way --
# proving _compute_should_block returns True from persona_biography_unresolved
# ALONE (no gate_llm, no fable_brief, no second stage of any kind) is the
# actual proof that a parallel "verified" conclusion elsewhere cannot
# override this, because generate.py's degraded-stages block (which is where
# _compute_should_block's result gets turned into fact_check_status: blocked
# in the frontmatter) runs BEFORE validate_article, and validate_article's
# own stamp is guarded by `if not re.search(r"^fact_check_status:", ...)` --
# confirmed by reading review.py directly (lines ~1027 and ~1041) -- so
# whichever stamp lands first wins and is never overwritten.
# ─────────────────────────────────────────────────────────────────────────

def test_article7_shaped_unresolved_claim_blocks_even_when_it_is_the_only_stage():
    po, orch = _orch()
    check(
        "persona_biography_unresolved blocks completely alone -- no gate_llm, no fable_brief, "
        "no second degraded stage of any kind (this is the exact Article 7 shape: "
        "pipeline_degraded was [editorial_revision] only, and fact_check_status still came "
        "out 'verified' under the OLD policy)",
        po.ProductionOrchestrator._compute_should_block(["persona_biography_unresolved"]) is True,
    )
    check(
        "for comparison: 'editorial_revision' alone (no persona claim involved) still does NOT "
        "block -- this fix did not make ordinary editorial_revision degradation blocking",
        po.ProductionOrchestrator._compute_should_block(["editorial_revision"]) is False,
    )


def test_article7_shaped_frontmatter_stamp_survives_a_later_verified_write_attempt():
    """Integration-level: exercises the REAL create_article_file (writes
    pipeline_degraded from self._degraded_stages) and the REAL guarded-write
    pattern review.py's validate_article uses for fact_check_status, in the
    order production actually runs them (generate.py's degraded-stages block,
    which stamps fact_check_status: blocked when _should_block is True, always
    runs before validate_article in _run_production_automation_locked --
    confirmed by reading generate.py directly: create_article_file at Step 6,
    the degraded-stages block immediately after, validate_article afterward
    at line ~1256). Proves the actual publication-eligibility field
    (publish_best.py's `fm.get("fact_check_status") == "blocked"` check) ends
    up blocked and STAYS blocked even when a later, unrelated fact-check pass
    would otherwise have called this article clean."""
    import tempfile
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    with tempfile.TemporaryDirectory(prefix="persona-fail-closed-test-") as tmpdir:
        orch.repo_root = Path(tmpdir)
        orch.drafts_dir = orch.repo_root / "_drafts"
        orch.posts_dir = orch.repo_root / "_posts"
        orch.assets_dir = orch.repo_root / "assets"
        orch.drafts_dir.mkdir(parents=True, exist_ok=True)
        orch.posts_dir.mkdir(parents=True, exist_ok=True)
        orch.assets_dir.mkdir(parents=True, exist_ok=True)

        # Simulates the outcome of _run_persona_biography_editorial_pass
        # already having found the unresolved claim (tested directly above).
        orch._degraded_stages = ["persona_biography_unresolved"]

        restore = _patch_methods(
            po.ProductionOrchestrator,
            _generate_card_excerpt=lambda self, *a, **k: "excerpt",
            _generate_keywords=lambda self, *a, **k: ["k1", "k2"],
        )
        try:
            metadata = {
                "title": "Nine Codecs and Not One of Them Is For Her",
                "date": "2026-08-12",
                "author": "Siri Sage",
                "filename": "2026-08-12-nine-codecs-test.md",
                "categories": ["spatial design"],
                "agent_perspective": "blind spatial navigator and acoustic design expert",
                "source_note": "",
                "model_used": "openrouter/claude-opus-4.8",
                "register": "wry",
                "article_type": "essay",
                "editorial_score": 6,
                "excerpt": "excerpt",
                "keywords": ["k1", "k2"],
            }
            article_file = orch.create_article_file(metadata, BASE_DRAFT, [], [])
        finally:
            restore()

        fm_text = article_file.read_text()
        check(
            "create_article_file (real, unmodified code) wrote pipeline_degraded including the new stage",
            "persona_biography_unresolved" in fm_text,
        )

        # Mirrors generate.py:~1208-1214 exactly (the degraded-stages block
        # that runs immediately after create_article_file, before
        # validate_article) -- pure glue with no decision logic of its own
        # beyond _compute_should_block's already-tested return value.
        should_block = po.ProductionOrchestrator._compute_should_block(orch._degraded_stages)
        check("_compute_should_block(['persona_biography_unresolved']) is True in this integration path too", should_block is True)
        if should_block and not re.search(r"^fact_check_status:", fm_text, re.MULTILINE):
            fm_text = re.sub(r"^---\n", "---\nfact_check_status: blocked\n", fm_text, count=1)
            article_file.write_text(fm_text)

        # Now simulate a LATER, completely independent fact-check pass
        # (review.py's validate_article, "else" branch, ~line 1041) that
        # found everything else in the article fine and tries to stamp
        # "verified" -- using its REAL guard pattern verbatim.
        later_fm_text = article_file.read_text()
        if not re.search(r"^fact_check_status:", later_fm_text, re.MULTILINE):
            later_fm_text = re.sub(r"^---\n", "---\nfact_check_status: verified\n", later_fm_text, count=1)
            article_file.write_text(later_fm_text)

        final_text = article_file.read_text()
        check(
            "the earlier 'blocked' stamp survives -- a later all-clear fact-check pass never "
            "overwrites it, because validate_article's own write is guarded on the field's absence "
            "(exactly the ordering that let Article 7 end up 'verified' under the OLD policy)",
            "fact_check_status: blocked" in final_text and "fact_check_status: verified" not in final_text,
        )

        # The actual publication-eligibility check, verbatim from publish_best.py:221.
        sys.path.insert(0, str(AUTOMATION_DIR))
        import publish_best
        fm = publish_best.parse_frontmatter(final_text)
        check(
            "publish_best.py's real eligibility check (fm.get('fact_check_status') == 'blocked') "
            "would SKIP this draft -- the article cannot reach publish eligibility",
            fm.get("fact_check_status") == "blocked",
        )


# ─────────────────────────────────────────────────────────────────────────
# (3) Control cases (section 7 of the task) -- prove this fix does NOT
# over-block.
# ─────────────────────────────────────────────────────────────────────────

def test_control_A_supported_canon_with_ordinary_degradation_not_blocked_by_persona_safety():
    """SUPPORTED_CANON claim + editorial revision degradation -> not blocked
    merely by persona safety. No unsupported_persona_claims are flagged at
    all here (the claim is authorized canon, so the reviewer correctly
    returns an empty list) -- an ordinary revise-for-craft-reasons verdict
    that then degrades must only ever produce the pre-existing
    'editorial_revision' stage, never the new one."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=_sequenced([REVIEW_JSON_NO_CLAIM_BUT_CRAFT_NOTES, None]),
        _call_openai_compat_api=lambda self, *a, **k: None,
    )
    try:
        content, _, _ = orch._run_persona_biography_editorial_pass(
            BASE_DRAFT, "Maya Flux", "angle", "systematic", packet, {}, [],
        )
    finally:
        restore()

    check("content unchanged (ordinary craft-note revision also degraded, unrelated to persona safety)", content == BASE_DRAFT)
    check("'editorial_revision' recorded (unchanged pre-existing behavior)", "editorial_revision" in orch._degraded_stages)
    check("'persona_biography_unresolved' is NOT recorded -- no persona claim was ever flagged", "persona_biography_unresolved" not in orch._degraded_stages)
    check("_compute_should_block does not block on ordinary editorial_revision alone", po.ProductionOrchestrator._compute_should_block(orch._degraded_stages) is False)


def test_control_B_non_biographical_first_person_not_blocked():
    """NON_BIOGRAPHICAL_FIRST_PERSON -> not blocked. Modeled the same way as
    control A: if _fable_editorial_review (unmodified by this fix) correctly
    judges a first-person sentence as non-biographical and returns an empty
    unsupported_persona_claims list, nothing here should ever fire -- this
    test proves the new recheck is inert on empty/irrelevant notes,
    independent of what the detector decided."""
    from orchestrator.llm import LLMMixin
    check(
        "_persona_claims_unresolved is False when notes contain no flagged persona-claim entries at all",
        LLMMixin._persona_claims_unresolved(["opening is weak", "ending needs work"], "any content, doesn't matter") is False,
    )
    check(
        "_persona_claims_unresolved is False on a completely empty notes list",
        LLMMixin._persona_claims_unresolved([], "any content") is False,
    )


def test_control_C_unsupported_claim_successfully_removed_no_unresolved_block():
    """UNSUPPORTED claim + successful safe revision -> no unresolved persona
    block. The rewrite genuinely drops the flagged sentence and nothing else
    in it resembles the quoted text."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(SIRI_CANON_TEXT, persona_name="Siri Sage", provenance_mode="real_person_evidence")
    safely_revised = (
        _FILLER + " I keep thinking about my mother's career as an audiologist, "
        "and what her patients' hearing devices were built to do versus what these "
        "headphones are built to do. " + _FILLER
    )
    check("sanity: the safe revision genuinely does not contain the flagged quote", FLAGGED_QUOTE not in safely_revised)

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=_sequenced([REVIEW_JSON_WITH_CLAIM, safely_revised]),
    )
    try:
        content, _, _ = orch._run_persona_biography_editorial_pass(
            BASE_DRAFT, "Siri Sage", "does the codec argument hold?", "wry", packet, persona_ctx, [],
        )
    finally:
        restore()

    check("content actually changed (the safe revision was accepted)", content != BASE_DRAFT)
    check("'editorial_revision' NOT recorded (content changed, not a no-op)", "editorial_revision" not in orch._degraded_stages)
    check("NEW check: 'persona_biography_unresolved' NOT recorded -- the flagged claim's text is genuinely gone", "persona_biography_unresolved" not in orch._degraded_stages)
    check("_compute_should_block does not block a successfully-resolved run", po.ProductionOrchestrator._compute_should_block(orch._degraded_stages) is False)


def test_control_D_partial_revision_that_changes_other_things_but_leaves_claim_untouched_still_blocks():
    """Case C from the task's section 5: reviewer flags a claim, revision
    returns DIFFERENT text (so content != pre_revision_content, no
    'editorial_revision' stage), but the SAME flagged claim survives verbatim
    inside it -- exactly the gap a whole-content equality check alone would
    miss, and exactly why the recheck runs unconditionally rather than only
    when a no-op is detected."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(SIRI_CANON_TEXT, persona_name="Siri Sage", provenance_mode="real_person_evidence")
    # Same _FILLER as BASE_DRAFT (byte-identical) -- only the sentence right
    # after it differs, isolating that as the one real edit rather than also
    # handing the deterministic new-entity scanner a second, spurious
    # difference to react to.
    partially_revised = (
        _FILLER + " Here is a different opening sentence, changed as requested. "
        "I keep thinking about " + FLAGGED_QUOTE + ". " + _FILLER
    )
    check("sanity: the partial revision IS different text from the original draft", partially_revised != BASE_DRAFT)
    check("sanity: the partial revision still contains the flagged quote verbatim", FLAGGED_QUOTE in partially_revised)

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=_sequenced([REVIEW_JSON_WITH_CLAIM, partially_revised]),
    )
    try:
        content, _, _ = orch._run_persona_biography_editorial_pass(
            BASE_DRAFT, "Siri Sage", "does the codec argument hold?", "wry", packet, persona_ctx, [],
        )
    finally:
        restore()

    check("content did change (not a whole-content no-op)", content == partially_revised)
    check("'editorial_revision' NOT recorded (this was not a no-op)", "editorial_revision" not in orch._degraded_stages)
    check(
        "NEW: 'persona_biography_unresolved' IS recorded anyway -- caught independent of the "
        "no-op check, which alone would have missed this",
        "persona_biography_unresolved" in orch._degraded_stages,
    )
    check("_compute_should_block blocks this run", po.ProductionOrchestrator._compute_should_block(orch._degraded_stages) is True)


def test_control_E_revision_introducing_new_fabrication_gets_rejected_original_flagged_claim_still_caught():
    """UNSUPPORTED claim + revision introduces a DIFFERENT unsupported
    biography -> blocked by existing/new combined protections. The rewrite
    drops the ORIGINAL flagged sentence but invents a new one
    (quote/name/number-bearing, so grounding.find_new_unsupported_specifics /
    find_new_unsupported_personal_history -- already wired into
    _reject_if_unsupported_specifics, unmodified by this fix -- rejects it).
    _fable_polish_rewrite then falls back to _opus_targeted_revision, which
    also fails here, so the article ships on the ORIGINAL, unrevised content
    -- meaning the ORIGINAL flagged claim is still present and this fix's
    recheck still catches it. Demonstrates the two protections combine
    correctly rather than one silently undoing the other."""
    po, orch = _orch()
    packet = build_evidence_packet(SOURCE_TEXT)
    persona_ctx = build_persona_factual_context(SIRI_CANON_TEXT, persona_name="Siri Sage", provenance_mode="real_person_evidence")
    new_fabrication = (
        _FILLER + " In 2019 I visited CERN and watched physicists debate the data live, "
        "which is what made me first think about my family's relationship to precision "
        "instruments, long before headphones existed as a category worth writing about at all. "
        + _FILLER
    )
    check("sanity: the new fabrication genuinely drops the original flagged quote", FLAGGED_QUOTE not in new_fabrication)

    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=_sequenced([REVIEW_JSON_WITH_CLAIM, new_fabrication]),
        _call_openai_compat_api=lambda self, *a, **k: None,  # opus_targeted_revision fallback also fails
    )
    try:
        content, _, _ = orch._run_persona_biography_editorial_pass(
            BASE_DRAFT, "Siri Sage", "does the codec argument hold?", "wry", packet, persona_ctx, [],
        )
    finally:
        restore()

    check(
        "the existing (unmodified) post-revision guard rejected the new CERN/2019 fabrication "
        "-- content falls all the way back to the original, unrevised draft",
        content == BASE_DRAFT,
    )
    check("'editorial_revision' recorded (the whole chain ultimately produced a no-op)", "editorial_revision" in orch._degraded_stages)
    check(
        "NEW: 'persona_biography_unresolved' ALSO recorded -- the original flagged claim survived "
        "(never replaced, since the replacement attempt was correctly rejected)",
        "persona_biography_unresolved" in orch._degraded_stages,
    )
    check("_compute_should_block blocks this run", po.ProductionOrchestrator._compute_should_block(orch._degraded_stages) is True)


# ─────────────────────────────────────────────────────────────────────────
# (4) Direct unit tests of the two new helpers, isolated from the LLM-call
# plumbing above.
# ─────────────────────────────────────────────────────────────────────────

def test_extract_flagged_persona_quote_helper():
    from orchestrator.llm import LLMMixin
    note = f"REMOVE unsupported persona biography claim: \"{FLAGGED_QUOTE}\" — explanation text after the quote"
    check("extracts the quoted span correctly", LLMMixin._extract_flagged_persona_quote(note) == FLAGGED_QUOTE)
    check("returns None for a note without the expected prefix", LLMMixin._extract_flagged_persona_quote("some ordinary craft note") is None)
    check(
        "returns None (fail-closed signal) for a malformed flagged note with no quoted span at all",
        LLMMixin._extract_flagged_persona_quote("REMOVE unsupported persona biography claim: no quotes here") is None,
    )


def test_persona_claims_unresolved_treats_unextractable_quote_as_unresolved():
    """'successful remediation cannot be established' is itself a failure
    condition (section 3 of the task) -- a malformed flagged note (no
    quoted span to check) must never be silently treated as resolved."""
    from orchestrator.llm import LLMMixin
    malformed_note = "REMOVE unsupported persona biography claim: no quotes here at all"
    check(
        "a flagged note whose quote can't be extracted is treated as unresolved regardless of content",
        LLMMixin._persona_claims_unresolved([malformed_note], "literally anything, doesn't matter") is True,
    )


if __name__ == "__main__":
    test_article5_shaped_unresolved_claim_appends_new_stage_and_blocks()
    test_article7_shaped_unresolved_claim_blocks_even_when_it_is_the_only_stage()
    test_article7_shaped_frontmatter_stamp_survives_a_later_verified_write_attempt()
    test_control_A_supported_canon_with_ordinary_degradation_not_blocked_by_persona_safety()
    test_control_B_non_biographical_first_person_not_blocked()
    test_control_C_unsupported_claim_successfully_removed_no_unresolved_block()
    test_control_D_partial_revision_that_changes_other_things_but_leaves_claim_untouched_still_blocks()
    test_control_E_revision_introducing_new_fabrication_gets_rejected_original_flagged_claim_still_caught()
    test_extract_flagged_persona_quote_helper()
    test_persona_claims_unresolved_treats_unextractable_quote_as_unresolved()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All persona-biography fail-closed tests passed.")
