#!/usr/bin/env python3
"""
lineage_persistence_test.py — proves evidence_lineage/persona_factual_lineage
are correctly constructed and PERSISTED through the real generate.py path,
zero network cost.

WHY THIS EXISTS: writer_prompt_test.py and executor_guard_test.py both stop
before or call individual executor functions directly -- neither exercises
generate.py's own evidence_lineage/persona_factual_lineage construction
(around _persist_article_plan) or proves the executor's lineage entry
actually gets stamped when the executor runs. Found live, 2026-08-11: an
early version of this exact harness had a packet-identity bug (its mocked
planner brief was validated against a SEPARATELY built evidence_packet,
not the one generate.py's own run actually threads through writer/reviewer/
executor) that accidentally simulated a mixed-provenance run -- and exposed
that generate.py had no invariant check for it at all. That gap is now
fixed in generate.py (a mismatched brief is discarded, fail-closed); this
test proves BOTH the fix and the correct case.

Reuses the same _import_orchestrator/_patch_methods/_isolate_paths harness
as snapshot_test.py/writer_prompt_test.py, but lets the pipeline run all
the way to _persist_article_plan (mocked with a capture-and-abort sentinel,
same discipline as writer_prompt_test.py's _StopAfterWriterPrompt) instead
of stopping at the writer call.

USAGE: python3 automation/lineage_persistence_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
import tempfile
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from snapshot_test import (  # noqa: E402
    _import_orchestrator, _patch_methods, _isolate_paths,
    FIXTURE_RECENT_POSTS, FIXTURE_PERSONA_STATE, FIXTURE_FAULT_LINE,
)
from orchestrator.grounding import build_evidence_packet, validate_brief  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


class _StopAfterPersist(BaseException):
    """MUST subclass BaseException, not Exception -- see writer_prompt_test.py's
    _StopAfterWriterPrompt docstring for why (generate.py wraps various call
    sites in their own `except Exception`, which would silently swallow an
    Exception-based sentinel and let the run continue past persistence)."""


SOURCE_TEXT = (
    "On 6 August 2026, wheelchair user Elena Rossi tested the temporary entrance. "
    '"I can enter independently now, but the sign still sends me toward the stairs," Rossi said. '
    "Museum staff said 12 temporary signs would be replaced before reopening."
)

NEWS_SEED = {
    "id": 1, "url": "https://example.com/probe-fixture",
    "title": "Museum reopens with temporary accessible entrance",
    "summary": "The museum installed a temporary ramp while permanent works continue.",
    "source_name": "test", "source_tier": 1, "pub_date": "2026-08-11", "fetched_date": "2026-08-11",
    "relevance_score": 0.8, "themes": "architecture",
    "disability_angle": "A wheelchair user found the new ramp usable but the signage confusing.",
    "used": 0, "used_date": None, "angle_checked": 1,
}

CLEAN_WRITER_DRAFT = (
    "TITLE: A Ramp That Works, A Sign That Doesn't\n\n"
    "The new entrance ramp at the museum went in. "
    "Wheelchair user Elena Rossi tested it on 6 August 2026. "
    '"I can enter independently now, but the sign still sends me toward the stairs," Rossi said. '
    "Museum staff said 12 temporary signs would be replaced before reopening.\n\n"
    "This is a familiar shape to me. At Gerrit Rietveld Academie I relied on an NGT "
    "interpreter to follow group conversation, and the lag it introduced -- a beat behind, "
    "always translating rather than hearing -- felt like being a time zone removed from a "
    "room I was physically standing in."
)

RAW_BRIEF_TEMPLATE = {
    "resisting_example": {
        "editorial_need": "the resident's own account of the barrier",
        "evidence_candidate": {
            "status": "found",
            "source_excerpt": (
                'On 6 August 2026, wheelchair user Elena Rossi tested the temporary entrance. '
                '"I can enter independently now, but the sign still sends me toward the stairs," Rossi said.'
            ),
            "named_person": "Elena Rossi",
            "direct_quote": "I can enter independently now, but the sign still sends me toward the stairs",
            "dates_numbers": ["6"],
        },
        "interpretation": "the physical fix outran the wayfinding fix",
    },
    "correction_moment": {
        "editorial_need": "", "evidence_candidate": {"status": "not_found", "source_excerpt": "", "named_person": "", "direct_quote": "", "dates_numbers": []},
        "interpretation": "",
    },
    "angle": "What does a ramp that works next to a sign that doesn't reveal about access as a single fixed point?",
    "cross_cite": "", "opening_scene": "", "seed_sentence": "",
    "opening_shape": "fact", "persona": "Pixel Nova", "register": "wary",
}

ACCEPTED_REVISION = CLEAN_WRITER_DRAFT.split("\n\n", 1)[1] + "\n\nWhether the fix holds will depend on someone actually testing the route."


def _stateful_call_editorial_model(self, system, user, *a, **k):
    # Dispatch by system-prompt content, not call order: _call_editorial_model
    # is ALSO called by _fable_update_state ("Step 3b-0: Fable post-publish
    # state update", generate.py) which -- despite its own docstring saying
    # "post-publish" -- actually runs BEFORE the reviewer in generate.py's
    # real order (a pre-existing doc/code drift, found while building this
    # harness; unrelated to Phase 1.6, logged in .claude/current-work.md,
    # not fixed here). Content-based dispatch is robust to that ordering.
    if "state-keeper" in system:
        return None  # _fable_update_state handles a None response gracefully
    if "about to rewrite a draft" in system:
        return ACCEPTED_REVISION  # _fable_polish_rewrite (the executor)
    return '{"verdict": "revise", "notes": ["tighten the ending"]}'  # _fable_editorial_review


def _run(brief_builder):
    """brief_builder(evidence_packet) -> validated brief dict. Called with
    the REAL evidence_packet object generate.py's own run constructs and
    threads to _fable_editorial_brief -- not a separately pre-built one.
    (The fix for this harness's own original bug: validating a mocked
    brief against build_evidence_packet(SOURCE_TEXT) built WITHOUT
    source_origin set produces a DIFFERENT evidence_packet_hash than the
    real run's packet, which sets source_origin="fetched_article" --
    same source_hash, different packet identity, exactly the divergence
    evidence_packet_hash exists to catch.)"""
    po = _import_orchestrator()
    captured = {}

    def capturing_persist(self, slug, agent_name, fable_brief):
        captured["fable_brief"] = dict(fable_brief) if fable_brief else fable_brief
        raise _StopAfterPersist()

    def mocked_fable_editorial_brief(self, news_title, news_summary, disability_angle, current_agent,
                                      evidence_packet=None, eligible_agents=None):
        return brief_builder(evidence_packet)

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = po.ProductionOrchestrator()
        _isolate_paths(orch, tmpdir)
        orch.posts_dir.mkdir(parents=True, exist_ok=True)
        orch.drafts_dir.mkdir(parents=True, exist_ok=True)
        orch.assets_dir.mkdir(parents=True, exist_ok=True)
        (orch.repo_root / "_reviews").mkdir(exist_ok=True)
        for filename, title, body_line in FIXTURE_RECENT_POSTS:
            (orch.posts_dir / filename).write_text(f"---\ntitle: {title}\n---\n\n{body_line}\n", encoding="utf-8")

        orch.override_agent = "Pixel Nova"
        orch.force_run = True

        restore = _patch_methods(
            po.ProductionOrchestrator,
            check_for_existing_article_today=lambda self: None,
            get_news_seed=lambda self: dict(NEWS_SEED),
            get_discovery_from_database=lambda self: None,
            _get_overused_themes=lambda self: [],
            _get_recent_references=lambda self, days=14: [],
            get_source_text=lambda self, url, max_chars=3000, fallback_text=None: SOURCE_TEXT[:max_chars],
            get_source_origin=lambda self, url: "fetched_article",
            get_pool_links=lambda self, keywords: [],
            _balance_agent=lambda self, preferred: "Pixel Nova",
            _pick_register=lambda self: ("wary", "Watchful, precise."),
            _pick_length=lambda self: 1000,
            _pick_article_type=lambda self: ("essay", ""),
            _get_calendar_event_nudge=lambda self: "",
            _fable_editorial_brief=mocked_fable_editorial_brief,
            _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
            _active_fault_lines=lambda self, text: [dict(FIXTURE_FAULT_LINE)],
            call_llm_via_openclaw_session=lambda self, prompt, model_priority=None: (CLEAN_WRITER_DRAFT, "openrouter", "claude-opus-4.8"),
            _call_editorial_model=_stateful_call_editorial_model,
            _call_openai_compat_api=lambda self, *a, **k: ACCEPTED_REVISION,
            _persist_article_plan=capturing_persist,
        )
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
    return captured["fable_brief"]


def test_matching_packet_lineage_persists_through_executor():
    """The correct case: planner brief validated against the SAME
    evidence_packet object the real run builds and threads everywhere --
    proves planner/writer/reviewer/executor all share one identity, and
    that the executor's lineage entries actually get persisted, not just
    constructed and discarded."""
    def matching_brief_builder(evidence_packet):
        validated, _log = validate_brief(dict(RAW_BRIEF_TEMPLATE), evidence_packet)
        return validated

    fable_brief = _run(matching_brief_builder)
    ev = fable_brief.get("evidence_lineage")
    pf = fable_brief.get("persona_factual_lineage")

    check("evidence_lineage is present on the persisted brief", ev is not None)
    check("persona_factual_lineage is present on the persisted brief", pf is not None)
    if not (ev and pf):
        return

    all_ev = [ev.get("planner"), ev.get("writer"), ev.get("reviewer"), ev.get("executor")]
    check("all 4 evidence_lineage stages (planner/writer/reviewer/executor) are non-None", all(e is not None for e in all_ev))

    source_hashes = {e["source_hash"] for e in all_ev if e}
    packet_hashes = {e["packet_hash"] for e in all_ev if e}
    check("planner/writer/reviewer/executor share exactly ONE source_hash", len(source_hashes) == 1)
    check("planner/writer/reviewer/executor share exactly ONE evidence_packet_hash", len(packet_hashes) == 1)

    pf_writer, pf_reviewer, pf_executor = pf.get("writer"), pf.get("reviewer"), pf.get("executor")
    check("persona_factual_lineage.executor is non-None (the executor ran)", pf_executor is not None)
    if pf_executor:
        context_hashes = {e["context_hash"] for e in (pf_writer, pf_reviewer, pf_executor) if e}
        check("writer/reviewer/executor share exactly ONE persona context_hash", len(context_hashes) == 1)
        check("persona_factual_lineage.executor.verification == 'declared_shared_context'", pf_executor.get("verification") == "declared_shared_context")
        check("persona_factual_lineage.executor.provenance_mode == 'real_person_evidence'", pf_executor.get("provenance_mode") == "real_person_evidence")
    if ev.get("executor"):
        check("evidence_lineage.executor.packet_verification == 'declared_shared_packet'", ev["executor"].get("packet_verification") == "declared_shared_packet")


def test_mismatched_packet_brief_is_discarded_fail_closed():
    """REGRESSION for the exact gap found live 2026-08-11: a planner brief
    stamped from a DIFFERENT evidence_packet than the one this run is
    actually using must be discarded entirely, not silently accepted with
    a mixed-provenance lineage persisted alongside writer/reviewer/
    executor's real one."""
    def mismatched_brief_builder(evidence_packet):
        wrong_packet = build_evidence_packet(SOURCE_TEXT)  # no source_origin -- deliberately different identity
        assert wrong_packet["evidence_packet_hash"] != evidence_packet["evidence_packet_hash"], (
            "harness bug: the 'mismatched' packet accidentally matches the real one -- "
            "can't test the invariant this way anymore"
        )
        validated, _log = validate_brief(dict(RAW_BRIEF_TEMPLATE), wrong_packet)
        return validated

    fable_brief = _run(mismatched_brief_builder)
    check(
        "generate.py discards a brief stamped from a mismatched evidence_packet (fable_brief is None)",
        fable_brief is None,
    )


if __name__ == "__main__":
    test_matching_packet_lineage_persists_through_executor()
    test_mismatched_packet_brief_is_discarded_fail_closed()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All lineage persistence tests passed.")
