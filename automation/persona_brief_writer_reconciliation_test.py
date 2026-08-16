#!/usr/bin/env python3
"""
persona_brief_writer_reconciliation_test.py — Persona Brief <-> Writer
Reconciliation, targeted production routing fix (2026-08-16), triggered by
the CripMinds conceptual-architecture audit's CA2 finding.

WHY THIS EXISTS: the audit's evaluation-batch artifacts showed 5/5 fixtures
with a surviving Fable brief had `fable_brief["persona"] != final writer/
byline persona` -- and the real published "Reached by Boat or Plane"
(Fable plan = Maya Flux, final writer = Siri Sage) is a third confirmed
instance. Root cause, confirmed directly in code: `generate.py` used to let
Fable choose a persona (mechanism-aware), then run THAT choice back through
`_balance_agent` (a purely rotation-fairness, mechanism-BLIND check) a
SECOND time -- and if rotation objected, silently substitute a different
persona while every downstream field (angle, correction_moment,
resisting_example, cross_cite) stayed exactly as Fable wrote it for the
ORIGINAL persona. This is the direct, traceable cause of at least two real
unsupported-persona-biography fabrication incidents (the writer, lacking
the substitute persona's actual canon support for the inherited mechanism,
invented biography to bridge the gap).

THE FIX: rotation/fairness eligibility (`_rotation_eligible_agents`,
discovery.py) is now computed BEFORE Fable's mechanism-aware decision and
passed into `_fable_editorial_brief` as a hard constraint -- Fable must
choose persona + mechanism/angle TOGETHER from within that set.
`_fable_editorial_brief` itself enforces this (returns None, same
degradation path as any other schema violation, if the model names a
persona outside the eligible set). The post-brief rebalancing block in
`generate.py` that used to re-run `_balance_agent` on Fable's own choice is
DELETED outright -- there is no surviving code path where Fable names
persona A and a downstream check silently substitutes persona B while A's
mechanism/angle/evidence ships unchanged. `_balance_agent` itself is
UNCHANGED (byte-for-byte) and still used only for the crude keyword-seeded
guess that runs BEFORE any brief exists, and as the fallback persona when a
brief is unavailable/discarded -- exactly as before this fix.

Covers the task's regression cases A-G:
  A. Fable persona is eligible -> Fable choice survives unchanged
  B. seed Pixel, Fable chooses Maya (eligible), historical post-Fable
     balance would have chosen Siri -> NEW code must never produce
     writer=Siri + Maya-brief-content (the exact old failure shape)
  C. multiple personas eligible -> Fable may choose one -> final writer
     matches it
  D. only one persona rotation-eligible -> Fable constrained to it ->
     brief/mechanism and writer remain aligned
  E. Fable brief discarded -> existing fallback semantics preserved, no
     fake persona/brief consistency marker
  F. persisted article plan persona == actual writer persona
  G. persona-biography safety (AP1/APE2/PS1) still receives and blocks
     against the FINAL persona, exactly as before this fix

Zero network, zero real model calls, zero article generation. Reuses the
same _import_orchestrator/_patch_methods/_isolate_paths harness as
snapshot_test.py/lineage_persistence_test.py.

USAGE: python3 automation/persona_brief_writer_reconciliation_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import json as _json
import sys
import tempfile
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from snapshot_test import (  # noqa: E402
    _import_orchestrator, _patch_methods, _isolate_paths,
    FIXTURE_RECENT_POSTS, FIXTURE_PERSONA_STATE, FIXTURE_FAULT_LINE,
)
from orchestrator.grounding import build_evidence_packet  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


ALL_PERSONAS = ["Pixel Nova", "Siri Sage", "Maya Flux", "Zen Circuit"]


# ─────────────────────────────────────────────────────────────────────────
# (1) Unit-level: _fable_editorial_brief's own eligibility enforcement
# ─────────────────────────────────────────────────────────────────────────

def _brief_json(persona, register="wry"):
    return _json.dumps({
        "persona": persona, "angle": "Is the drift or the plan the real cost?",
        "register": register, "seed_sentence": "The building was finished on schedule.",
        "opening_scene": "The building was finished on schedule.",
        "opening_shape": "fact",
        "correction_moment": {"editorial_need": "", "evidence_candidate":
            {"status": "not_found", "source_excerpt": "", "named_person": "", "direct_quote": "", "dates_numbers": []},
            "interpretation": ""},
        "resisting_example": {"editorial_need": "", "evidence_candidate":
            {"status": "not_found", "source_excerpt": "", "named_person": "", "direct_quote": "", "dates_numbers": []},
            "interpretation": ""},
        "cross_cite": "",
    })


def _orch_for_unit_test():
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    return po, orch


def case_a_eligible_persona_survives_unchanged():
    po, orch = _orch_for_unit_test()
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, system, user, **k: _brief_json("Maya Flux"),
        _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
        _active_fault_lines=lambda self, text: [],
    )
    try:
        brief = orch._fable_editorial_brief(
            "story", "summary", "", "Pixel Nova", build_evidence_packet(None),
            eligible_agents=["Maya Flux", "Siri Sage", "Zen Circuit"],
        )
    finally:
        restore()
    check("A: Fable's persona choice (Maya Flux), already inside the eligible "
          "set, is returned unchanged", brief is not None and brief["persona"] == "Maya Flux")


def case_b_ineligible_persona_choice_is_rejected_not_substituted():
    # THE OLD FAILURE SHAPE: Fable (or a model ignoring instructions) names a
    # persona OUTSIDE the eligible set. The old code would have accepted this
    # unconditionally as fable_brief["persona"], then silently rerouted the
    # WRITER through _balance_agent afterward while keeping this exact
    # mechanism/angle. The new code must instead reject the whole brief --
    # never split "the mechanism as planned" from "who actually writes it".
    po, orch = _orch_for_unit_test()
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, system, user, **k: _brief_json("Pixel Nova"),
        _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
        _active_fault_lines=lambda self, text: [],
    )
    try:
        brief = orch._fable_editorial_brief(
            "story", "summary", "", "Pixel Nova", build_evidence_packet(None),
            eligible_agents=["Maya Flux", "Siri Sage", "Zen Circuit"],  # Pixel Nova NOT eligible
        )
    finally:
        restore()
    check("B: a persona named outside the eligible set is REJECTED (brief is "
          "None), never silently accepted with a mismatched writer assigned later",
          brief is None)


def case_c_multiple_eligible_fable_may_choose_any_of_them():
    po, orch = _orch_for_unit_test()
    for choice in ("Siri Sage", "Zen Circuit"):
        restore = _patch_methods(
            po.ProductionOrchestrator,
            _call_editorial_model=lambda self, system, user, **k: _brief_json(choice),
            _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
            _active_fault_lines=lambda self, text: [],
        )
        try:
            brief = orch._fable_editorial_brief(
                "story", "summary", "", "Maya Flux", build_evidence_packet(None),
                eligible_agents=["Siri Sage", "Zen Circuit"],
            )
        finally:
            restore()
        check(f"C: with 2 personas eligible, Fable choosing {choice!r} is accepted",
              brief is not None and brief["persona"] == choice)


def case_d_single_eligible_persona_constrains_fable():
    po, orch = _orch_for_unit_test()
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, system, user, **k: _brief_json("Zen Circuit"),
        _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
        _active_fault_lines=lambda self, text: [],
    )
    try:
        brief = orch._fable_editorial_brief(
            "story", "summary", "", "Maya Flux", build_evidence_packet(None),
            eligible_agents=["Zen Circuit"],
        )
    finally:
        restore()
    check("D: with exactly one persona eligible, Fable naming that same "
          "persona is accepted and the brief/mechanism stay aligned to it",
          brief is not None and brief["persona"] == "Zen Circuit")

    # And the negative: naming anyone else with a single-persona eligible set
    # must still be rejected, same as case B.
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, system, user, **k: _brief_json("Maya Flux"),
        _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
        _active_fault_lines=lambda self, text: [],
    )
    try:
        brief2 = orch._fable_editorial_brief(
            "story", "summary", "", "Maya Flux", build_evidence_packet(None),
            eligible_agents=["Zen Circuit"],
        )
    finally:
        restore()
    check("D: naming a persona other than the single eligible one is rejected",
          brief2 is None)


def case_unconstrained_default_preserves_prior_behavior():
    # eligible_agents omitted entirely (None) -- existing callers (frozen
    # probes, snapshot fixtures) that don't pass it must see UNCHANGED
    # behavior: any of the 4 personas is acceptable, matching pre-fix
    # `brief["persona"] in self.agents`.
    po, orch = _orch_for_unit_test()
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, system, user, **k: _brief_json("Siri Sage"),
        _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
        _active_fault_lines=lambda self, text: [],
    )
    try:
        brief = orch._fable_editorial_brief(
            "story", "summary", "", "Maya Flux", build_evidence_packet(None),
        )  # no eligible_agents kwarg at all
    finally:
        restore()
    check("unconstrained call (no eligible_agents passed) preserves prior "
          "any-of-4-personas behavior -- backward compatible for existing "
          "frozen-probe/snapshot callers",
          brief is not None and brief["persona"] == "Siri Sage")


# ─────────────────────────────────────────────────────────────────────────
# (2) Integration: full generate.py pipeline through to _persist_article_plan
# (reuses lineage_persistence_test.py's stop-at-persistence discipline)
# ─────────────────────────────────────────────────────────────────────────

SOURCE_TEXT = (
    "On 10 August 2026, the Iolair foundation opened a residency building on a "
    "remote island reached only by boat or plane. The architects said the brief "
    "required privacy for the resident artist and public access for exhibitions."
)

NEWS_SEED = {
    "id": 1, "url": "https://example.com/reconciliation-fixture",
    "title": "Remote island residency opens",
    "summary": "A foundation opened an artist residency reachable only by boat or plane.",
    "source_name": "test", "source_tier": 1, "pub_date": "2026-08-16", "fetched_date": "2026-08-16",
    "relevance_score": 0.8, "themes": ["architecture"],
    "disability_angle": "Remoteness sold as a gift assumes a body that experiences it as choice.",
    "used": 0, "used_date": None, "angle_checked": 1,
}

CLEAN_WRITER_DRAFT = (
    "TITLE: The Boat You Cannot Miss\n\n"
    "The residency opened on schedule. The architects were proud of the brief they solved.\n\n"
    "I have spent a long time thinking about what a route requires of a body, and this one "
    "requires more than the brochure photograph admits."
)


class _StopAfterPersist(BaseException):
    pass


def _brief_dict(persona, register="wry"):
    return {
        "persona": persona, "angle": "Is the remoteness a gift or a wall?",
        "register": register, "seed_sentence": "The building was finished on schedule.",
        "opening_scene": "The building was finished on schedule.", "opening_shape": "fact",
        "correction_moment": {"editorial_need": "", "evidence_candidate":
            {"status": "not_found", "source_excerpt": "", "named_person": "", "direct_quote": "", "dates_numbers": []},
            "interpretation": ""},
        "resisting_example": {"editorial_need": "", "evidence_candidate":
            {"status": "not_found", "source_excerpt": "", "named_person": "", "direct_quote": "", "dates_numbers": []},
            "interpretation": ""},
        "cross_cite": "", "grounding_status": "validated", "grounding_violations": [],
        "grounding_scope": "evidence_fields_only", "brief_schema_version": 3,
        "source_truncated": False, "source_origin": "fetched_article",
        "source_length_chars": len(SOURCE_TEXT), "source_original_length_chars": len(SOURCE_TEXT),
    }


def _stateful_call_editorial_model(fable_persona):
    def _call(self, system, user, *a, **k):
        if "state-keeper" in system:
            return None
        if "about to rewrite a draft" in system:
            return CLEAN_WRITER_DRAFT
        if "editorial director of Crip Minds" in system:
            return _json.dumps(_brief_dict(fable_persona))
        return '{"verdict": "publish_as_is", "notes": [], "unsupported_persona_claims": []}'
    return _call


def _run_pipeline(eligible_agents, fable_persona, seed_persona_via_balance_agent, spy_balance_agent_calls,
                   spy_persona_bio_calls=None):
    """Runs the REAL generate.py path (_run_production_automation_locked)
    with _rotation_eligible_agents and the Fable-brief model call mocked
    deterministically, stopping at _persist_article_plan (same discipline as
    lineage_persistence_test.py's _StopAfterPersist sentinel). Returns
    (persisted_agent_name, persisted_fable_brief).

    spy_persona_bio_calls (optional list): if provided, _run_persona_
    biography_editorial_pass is replaced with a spy that records the
    agent_name it was called with and passes content through unchanged --
    lets a caller (case G) prove the FINAL, post-fix persona is what
    actually reaches the persona-biography safety stage, without needing to
    re-verify PS1's own internal correctness (already covered by its own
    dedicated test suite, unmodified and unaffected by this fix)."""
    po = _import_orchestrator()
    captured = {}

    def capturing_persist(self, slug, agent_name, fable_brief):
        captured["agent_name"] = agent_name
        captured["fable_brief"] = dict(fable_brief) if fable_brief else fable_brief
        raise _StopAfterPersist()

    def spying_balance_agent(self, preferred):
        spy_balance_agent_calls.append(preferred)
        return seed_persona_via_balance_agent

    def spying_persona_bio_pass(self, content, agent_name, review_angle, register,
                                 evidence_packet, persona_factual_context, raw_draft_guard_hits):
        if spy_persona_bio_calls is not None:
            spy_persona_bio_calls.append(agent_name)
        return content, True, False

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = po.ProductionOrchestrator()
        _isolate_paths(orch, tmpdir)
        orch.posts_dir.mkdir(parents=True, exist_ok=True)
        orch.drafts_dir.mkdir(parents=True, exist_ok=True)
        orch.assets_dir.mkdir(parents=True, exist_ok=True)
        (orch.repo_root / "_reviews").mkdir(exist_ok=True)
        for filename, title, body_line in FIXTURE_RECENT_POSTS:
            (orch.posts_dir / filename).write_text(f"---\ntitle: {title}\n---\n\n{body_line}\n", encoding="utf-8")

        orch.force_run = True

        _replacements = dict(
            check_for_existing_article_today=lambda self: None,
            get_news_seed=lambda self: dict(NEWS_SEED),
            get_discovery_from_database=lambda self: None,
            _get_overused_themes=lambda self: [],
            _get_recent_references=lambda self, days=14: [],
            get_source_text=lambda self, url, max_chars=3000, fallback_text=None: SOURCE_TEXT[:max_chars],
            get_source_origin=lambda self, url: "fetched_article",
            get_pool_links=lambda self, keywords: [],
            _balance_agent=spying_balance_agent,
            _rotation_eligible_agents=lambda self: list(eligible_agents),
            _pick_register=lambda self: ("wary", "Watchful, precise."),
            _pick_length=lambda self: 1000,
            _pick_article_type=lambda self: ("essay", ""),
            _get_calendar_event_nudge=lambda self: "",
            _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
            _active_fault_lines=lambda self, text: [],
            call_llm_via_openclaw_session=lambda self, prompt, model_priority=None: (CLEAN_WRITER_DRAFT, "openrouter", "claude-opus-4.8"),
            _call_editorial_model=_stateful_call_editorial_model(fable_persona),
            _call_openai_compat_api=lambda self, *a, **k: CLEAN_WRITER_DRAFT,
            _persist_article_plan=capturing_persist,
        )
        if spy_persona_bio_calls is not None:
            _replacements["_run_persona_biography_editorial_pass"] = spying_persona_bio_pass
        restore = _patch_methods(po.ProductionOrchestrator, **_replacements)
        error = None
        try:
            orch._run_production_automation_locked()
            error = "pipeline completed without ever reaching _persist_article_plan"
        except _StopAfterPersist:
            pass
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        finally:
            restore()

    if error:
        raise AssertionError(f"harness failed to reach persistence cleanly: {error}")
    return captured["agent_name"], captured["fable_brief"]


def case_b_integration_old_bug_shape_now_impossible():
    # Reproduces the EXACT historical shape: crude keyword seed picks "Pixel
    # Nova" (simulated via _balance_agent's mocked return value), Fable
    # (mechanism-aware) chooses "Maya Flux" -- which IS in the rotation-
    # eligible set -- and a spy proves _balance_agent is NEVER called again
    # with Fable's own choice (the old code's second, silent-override call).
    # If the old bug still existed, this integration would show a byline of
    # whatever _balance_agent("Maya Flux") returned instead of "Maya Flux"
    # itself; here _balance_agent always returns "Pixel Nova" regardless of
    # input, so ANY second call with "Maya Flux" would leak through as a
    # byline of "Pixel Nova" attached to Maya Flux's brief content -- the
    # exact old failure shape -- which must NOT happen.
    calls = []
    agent_name, fable_brief = _run_pipeline(
        eligible_agents=["Maya Flux", "Siri Sage", "Zen Circuit"],
        fable_persona="Maya Flux",
        seed_persona_via_balance_agent="Pixel Nova",
        spy_balance_agent_calls=calls,
    )
    check("B: final agent_name is Maya Flux (Fable's own choice), not Pixel "
          "Nova (what a second _balance_agent call would have forced)",
          agent_name == "Maya Flux")
    check("B: persisted fable_brief[\"persona\"] matches the final writer -- "
          "no mismatched-brief-content-under-different-byline state exists",
          fable_brief["persona"] == "Maya Flux" == agent_name)
    check("B: _balance_agent was called exactly once, with the crude "
          "keyword seed's own preference (Pixel Nova, from themes=[\"architecture\"]) "
          "-- NEVER called a second time with Fable's own choice (Maya Flux)",
          calls == ["Pixel Nova"])


def case_c_integration_final_writer_matches_fables_eligible_choice():
    calls = []
    agent_name, fable_brief = _run_pipeline(
        eligible_agents=["Siri Sage", "Zen Circuit"],
        fable_persona="Zen Circuit",
        seed_persona_via_balance_agent="Siri Sage",
        spy_balance_agent_calls=calls,
    )
    check("C: with 2 eligible personas, Fable's in-set choice (Zen Circuit) "
          "becomes the final writer", agent_name == "Zen Circuit")
    check("C: persisted plan persona matches", fable_brief["persona"] == "Zen Circuit")


def case_d_integration_single_eligible_persona():
    calls = []
    agent_name, fable_brief = _run_pipeline(
        eligible_agents=["Maya Flux"],
        fable_persona="Maya Flux",
        seed_persona_via_balance_agent="Maya Flux",
        spy_balance_agent_calls=calls,
    )
    check("D: single rotation-eligible persona -> Fable constrained to it, "
          "writer and brief stay aligned to Maya Flux",
          agent_name == "Maya Flux" and fable_brief["persona"] == "Maya Flux")


def case_e_fable_brief_discarded_fallback_preserved():
    # Fable's model call returns a persona OUTSIDE the eligible set -- the
    # whole brief is discarded (existing fail-closed fallback semantics,
    # unchanged by this fix). agent_name must fall back to whatever
    # _balance_agent's initial keyword-seed call produced, and NO fake
    # brief/persona consistency marker should appear.
    calls = []
    agent_name, fable_brief = _run_pipeline(
        eligible_agents=["Maya Flux", "Siri Sage", "Zen Circuit"],
        fable_persona="Pixel Nova",  # outside eligible set -> discarded
        seed_persona_via_balance_agent="Zen Circuit",
        spy_balance_agent_calls=calls,
    )
    check("E: brief discarded (fable_persona was ineligible) -> persisted "
          "fable_brief is falsy, no fake consistency marker invented",
          not fable_brief)
    check("E: agent_name falls back to the pre-existing keyword+rotation "
          "seed (Zen Circuit), exactly as before this fix",
          agent_name == "Zen Circuit")


def case_f_plan_writer_invariant_holds_across_scenarios():
    # Explicit, standalone deterministic assertion of the Plan <-> Writer
    # invariant (task Section 7): for every successful Fable path,
    # fable_brief["persona"] == agent_name == (eventually) the persisted
    # plan persona. Checked across several distinct eligible-set/choice
    # combinations, not just incidentally inside cases B-D.
    scenarios = [
        (["Maya Flux", "Siri Sage", "Zen Circuit"], "Siri Sage", "Pixel Nova"),
        (["Pixel Nova", "Zen Circuit"], "Pixel Nova", "Zen Circuit"),
        (["Maya Flux"], "Maya Flux", "Maya Flux"),
    ]
    for eligible, fable_choice, seed in scenarios:
        calls = []
        agent_name, fable_brief = _run_pipeline(
            eligible_agents=eligible, fable_persona=fable_choice,
            seed_persona_via_balance_agent=seed, spy_balance_agent_calls=calls,
        )
        check(f"F: plan<->writer invariant holds for eligible={eligible}, "
              f"Fable chose {fable_choice!r} -- fable_brief[persona] == agent_name == {fable_choice!r}",
              fable_brief["persona"] == agent_name == fable_choice)


def case_g_persona_biography_safety_receives_final_persona():
    # Confirms the routing fix correctly wires the FINAL (post-fix) persona
    # into the persona-biography safety stage -- not the crude keyword seed,
    # not any stale pre-brief value. PS1/AP1/APE2's own internal correctness
    # (does it actually detect/block an unsupported claim) is exhaustively
    # covered by persona_biography_fail_closed_test.py/author_persona_
    # biography_test.py, unmodified and unaffected by this fix -- this test
    # only proves the WIRING between this fix and that stage remains
    # correct: the persona _run_persona_biography_editorial_pass receives is
    # exactly the one Fable's brief named (Maya Flux here), never the
    # initial keyword seed (Pixel Nova) it started from.
    bio_calls = []
    agent_name, fable_brief = _run_pipeline(
        eligible_agents=["Maya Flux", "Siri Sage", "Zen Circuit"],
        fable_persona="Maya Flux",
        seed_persona_via_balance_agent="Pixel Nova",
        spy_balance_agent_calls=[],
        spy_persona_bio_calls=bio_calls,
    )
    check("G: persona-biography editorial pass received the FINAL persona "
          f"(Maya Flux), not the initial seed (Pixel Nova) -- calls: {bio_calls!r}",
          bio_calls == ["Maya Flux"])
    check("G: final persona matches across agent_name/fable_brief/bio-pass-call",
          agent_name == fable_brief["persona"] == "Maya Flux" == bio_calls[0])


if __name__ == "__main__":
    case_a_eligible_persona_survives_unchanged()
    case_b_ineligible_persona_choice_is_rejected_not_substituted()
    case_c_multiple_eligible_fable_may_choose_any_of_them()
    case_d_single_eligible_persona_constrains_fable()
    case_unconstrained_default_preserves_prior_behavior()
    case_b_integration_old_bug_shape_now_impossible()
    case_c_integration_final_writer_matches_fables_eligible_choice()
    case_d_integration_single_eligible_persona()
    case_e_fable_brief_discarded_fallback_preserved()
    case_f_plan_writer_invariant_holds_across_scenarios()
    case_g_persona_biography_safety_receives_final_persona()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("All persona brief <-> writer reconciliation tests passed.")
        sys.exit(0)
