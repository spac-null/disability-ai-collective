#!/usr/bin/env python3
"""
cj2_shadow_integration_test.py — proves the Phase G.2 CJ-2 shadow hook is
wired into the REAL generate.py path correctly, and — most importantly —
that it is behaviorally inert in OFF mode and never influences the real
published brief/prompt in SHADOW mode, zero network cost.

SYNTHETIC CONTROL-FLOW FIXTURE — the winner/seed fixtures used here are
hand-authored, not real Stage-C output. This proves mechanical wiring only:
NOT semantic evidence, NOT Stage-C validation, NOT production-readiness
evidence (see cj2_winner_bridge_test.py's own docstring for the same
caveat, which applies equally here).

Reuses the same _import_orchestrator/_patch_methods/_isolate_paths harness
as snapshot_test.py/writer_prompt_test.py, and the identical
capture-and-abort-via-BaseException-sentinel technique at the writer's LLM
call site, so the real, unmodified _run_production_automation_locked() runs
all the way through the CJ-2 shadow hook and stops immediately before any
network call, image generation, git operation, or gate/fact-check pass.

USAGE: python3 automation/cj2_shadow_integration_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import json
import os
import sqlite3
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


class _StopAtWriterCall(BaseException):
    """See writer_prompt_test.py's _StopAfterWriterPrompt docstring for why
    this MUST subclass BaseException, not Exception — identical reasoning,
    identical call site (call_llm_via_openclaw_session is wrapped in
    generate.py's own `except Exception` fallback path)."""


SOURCE_TEXT = (
    "The council's own report shows attendance rose 4% while satisfaction fell.\n\n"
    "Program staff described the rise as a sign of success. The report does not "
    "say whether the people newly attending are the ones the program was meant "
    "to reach."
)

NEWS_SEED = {
    "id": 1, "url": "https://example.com/probe-fixture",
    "title": "City program reports 4% attendance rise",
    "summary": "Officials called the rise a success story.",
    "source_name": "test", "source_tier": 1, "pub_date": "2026-08-13", "fetched_date": "2026-08-13",
    "relevance_score": 0.8, "themes": "civic",
    "disability_angle": "Whether the rise reaches the people the program targets is unmeasured.",
    "used": 0, "used_date": None, "angle_checked": 1,
}


def _real_evidence_packet():
    """The REAL evidence_packet build_evidence_packet(SOURCE_TEXT) produces
    — used to compute a fixture's matching source_sha256 so the "valid
    winner" scenario below exercises the true-match path, not a
    coincidence."""
    return build_evidence_packet(SOURCE_TEXT)


def _write_fixture(tmpdir, *, matching_hash: bool) -> str:
    packet = _real_evidence_packet()
    seed_hash = packet["source_hash"] if matching_hash else "deliberately-wrong-hash"
    fixture = {
        "winner": {
            "status": "candidate",
            "seed_evidence_refs": ["cj1:a1"],
            "additional_source_observations": [],
            "engine_move": "attends to the gap between a metric and what it claims to measure",
            "seed_engagement": "strong",
            "interpretive_inference": "the rise is treated as success without checking who it reaches",
            "conceptual_shift": "reframes a participation number as a targeting question",
            "claimed_contribution": "shows the metric cannot see the population it claims to serve",
        },
        "seed": {
            "slug": "shadow-integration-fixture",
            "source_sha256": seed_hash,
            "source_snapshot": SOURCE_TEXT,
            "resisting_detail": "The report treats a 4% attendance rise as success without checking "
                                 "whether the people newly attending are the ones the program targets.",
            "evidence": [{"id": "cj1:a1", "excerpt": "attendance rose 4% while satisfaction fell"}],
        },
        "cj1_seed_id": "shadow-integration-fixture",
        "stage_c_letter": "B",
        "engine_label": "P",
        "admission_gate_terminal_state": "admitted_safe",
    }
    path = os.path.join(tmpdir, "winner_fixture.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fixture, f)
    return path


def _canary_brief(persona_name="Pixel Nova", register_name="wry"):
    packet = build_evidence_packet(SOURCE_TEXT)
    return {
        "persona": persona_name, "angle": "What does the number not measure?",
        "register": register_name, "seed_sentence": "The number went up.",
        "opening_scene": "", "opening_shape": "fact", "cross_cite": "",
        "correction_moment": {
            "editorial_need": "n/a",
            "evidence_candidate": {"status": "not_found", "source_excerpt": "", "named_person": "",
                                    "direct_quote": "", "dates_numbers": []},
            "interpretation": "n/a",
        },
        "resisting_example": {
            "editorial_need": "n/a",
            "evidence_candidate": {"status": "not_found", "source_excerpt": "", "named_person": "",
                                    "direct_quote": "", "dates_numbers": []},
            "interpretation": "n/a",
        },
        "brief_schema_version": 2, "grounding_status": "validated",
        "grounding_scope": "evidence_fields_only", "grounding_violations": [],
        "source_hash": packet["source_hash"], "evidence_packet_hash": packet["evidence_packet_hash"],
        "evidence_schema_version": packet["evidence_schema_version"], "source_truncated": packet["source_truncated"],
    }


def _run_pipeline(tmpdir, env_overrides, *, fable_brief_value="default"):
    """Runs the REAL, unmodified _run_production_automation_locked() with
    only the same non-CJ2 mocks writer_prompt_test.py already established,
    stopping at the writer's LLM call. fable_brief_value: "default" (a
    working canary brief), or None (simulate a real Fable failure, to prove
    CJ2 shadow's own success/failure never gets confused with
    fable_brief's own _degraded_stages entry). Returns
    (captured_prompt_or_None, orch, error_or_None)."""
    po = _import_orchestrator()
    captured = {}

    def capturing_llm_call(self, prompt, model_priority=None):
        captured["prompt"] = prompt
        raise _StopAtWriterCall()

    def brief_fn(self, *a, **k):
        return _canary_brief() if fable_brief_value == "default" else fable_brief_value

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
        # SOURCE_ACQUISITION_RETRY_V1 (2026-08-23): selection now runs through
        # the acquisition gate, and these harnesses use a deliberately minimal
        # synthetic SOURCE_TEXT the gate would correctly call an unusable
        # extraction. These cases are not about acquisition, so stub the
        # selection layer directly -- acquisition has its own suite,
        # source_retry_test.py.
        get_news_seed=lambda self, exclude_ids=None: dict(NEWS_SEED),
        get_news_seed_with_usable_source=lambda self, max_attempts=None, exclude_ids=None: dict(NEWS_SEED),
        get_discovery_from_database=lambda self: None,
        _get_overused_themes=lambda self: [],
        _get_recent_references=lambda self, days=14: [],
        get_source_text=lambda self, url, max_chars=3000, fallback_text=None, underlying_url=None: SOURCE_TEXT[:max_chars],
        get_source_origin=lambda self, url: "fetched_article",
        get_pool_links=lambda self, keywords: [],
        _balance_agent=lambda self, preferred: "Pixel Nova",
        _pick_register=lambda self: ("wry", "Watchful, precise."),
        _pick_length=lambda self: 1000,
        _pick_article_type=lambda self: ("essay", ""),
        _get_calendar_event_nudge=lambda self: "",
        _fable_editorial_brief=brief_fn,
        _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
        _active_fault_lines=lambda self, text: [dict(FIXTURE_FAULT_LINE)],
        call_llm_via_openclaw_session=capturing_llm_call,
    )
    old_env = {k: os.environ.get(k) for k in env_overrides}
    for k, v in env_overrides.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    error = None
    try:
        try:
            orch._run_production_automation_locked()
            error = "pipeline completed without ever reaching call_llm_via_openclaw_session"
        except _StopAtWriterCall:
            pass
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
    finally:
        restore()
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return captured.get("prompt"), orch, error


def _shadow_rows(orch):
    db_path = orch.repo_root / "automation" / "engagement.db"
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    try:
        try:
            cur = conn.execute(
                "SELECT integration_mode, path_provenance, bridge_valid, failure_reason, "
                "winner_present, engine_label FROM cj2_shadow_runs"
            )
            return cur.fetchall()
        except sqlite3.OperationalError:
            return []  # table never created -- OFF mode, hook never entered
    finally:
        conn.close()


def case_off_mode_is_inert():
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt, orch, error = _run_pipeline(tmpdir, {"CJ2_INTEGRATION_MODE": None, "CJ2_SHADOW_WINNER_FIXTURE": None})
        check("A. OFF mode: pipeline reaches the writer call with no error", error is None)
        check("A. OFF mode: writer prompt captured (real pipeline actually ran)", bool(prompt))
        check("A. OFF mode: cj2_shadow_runs table not even created (_cj2_shadow_attempt never called)",
              _shadow_rows(orch) == [])
        check("A. OFF mode: no cj2_shadow entry in _degraded_stages", "cj2_shadow" not in getattr(orch, "_degraded_stages", []))
        return prompt


def case_shadow_mode_no_fixture():
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt, orch, error = _run_pipeline(tmpdir, {"CJ2_INTEGRATION_MODE": "SHADOW", "CJ2_SHADOW_WINNER_FIXTURE": None})
        check("D. SHADOW, no winner configured: pipeline still reaches writer call with no error", error is None)
        rows = _shadow_rows(orch)
        check("D. SHADOW, no winner: exactly one shadow row recorded", len(rows) == 1)
        if rows:
            mode, prov, valid, reason, present, engine = rows[0]
            check("D. SHADOW, no winner: integration_mode=SHADOW", mode == "SHADOW")
            check("D. SHADOW, no winner: path_provenance=CJ2_SHADOW", prov == "CJ2_SHADOW")
            check("D. SHADOW, no winner: bridge_valid=0", valid == 0)
            check("D. SHADOW, no winner: failure_reason=NO_CJ2_WINNER", reason == "NO_CJ2_WINNER")
            check("D. SHADOW, no winner: winner_present=0", present == 0)
        return prompt


def case_shadow_mode_valid_winner():
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = _write_fixture(tmpdir, matching_hash=True)
        prompt, orch, error = _run_pipeline(
            tmpdir, {"CJ2_INTEGRATION_MODE": "SHADOW", "CJ2_SHADOW_WINNER_FIXTURE": fixture_path}
        )
        check("B. SHADOW, valid winner + matching evidence_packet: pipeline reaches writer with no error", error is None)
        rows = _shadow_rows(orch)
        check("B. SHADOW, valid winner: exactly one shadow row recorded", len(rows) == 1)
        if rows:
            mode, prov, valid, reason, present, engine = rows[0]
            check("B. SHADOW, valid winner: bridge_valid=1", valid == 1)
            check("B. SHADOW, valid winner: failure_reason is NULL", reason is None)
            check("B. SHADOW, valid winner: winner_present=1", present == 1)
            check("B. SHADOW, valid winner: engine_label recorded as 'P'", engine == "P")
        return prompt


def case_shadow_mode_wrong_evidence_packet():
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = _write_fixture(tmpdir, matching_hash=False)
        prompt, orch, error = _run_pipeline(
            tmpdir, {"CJ2_INTEGRATION_MODE": "SHADOW", "CJ2_SHADOW_WINNER_FIXTURE": fixture_path}
        )
        check("C. SHADOW, winner from a DIFFERENT evidence_packet: pipeline still reaches writer with no error", error is None)
        rows = _shadow_rows(orch)
        check("C. wrong evidence_packet: exactly one shadow row recorded", len(rows) == 1)
        if rows:
            mode, prov, valid, reason, present, engine = rows[0]
            check("C. wrong evidence_packet: bridge_valid=0", valid == 0)
            check("C. wrong evidence_packet: failure_reason=EVIDENCE_PACKET_MISMATCH", reason == "EVIDENCE_PACKET_MISMATCH")
        return prompt


def case_malformed_fixture_does_not_crash_production():
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_path = os.path.join(tmpdir, "bad.json")
        with open(bad_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        prompt, orch, error = _run_pipeline(
            tmpdir, {"CJ2_INTEGRATION_MODE": "SHADOW", "CJ2_SHADOW_WINNER_FIXTURE": bad_path}
        )
        check("E. malformed fixture JSON: pipeline still reaches writer with no error (never raises)", error is None)
        rows = _shadow_rows(orch)
        check("E. malformed fixture JSON: exactly one shadow row recorded, reason=WINNER_RECONSTRUCTION_FAILED",
              len(rows) == 1 and rows[0][3] == "WINNER_RECONSTRUCTION_FAILED")


def case_fable_failure_does_not_get_confused_with_cj2_shadow():
    """Proves _degraded_stages only ever gets "fable_brief" appended by
    Fable's own real failure — never "cj2_shadow" or any CJ2-related tag —
    regardless of CJ2 integration mode or bridge outcome, satisfying
    instruction 7's "no CJ2 failure can break production" and this
    module's own comment in generate.py about never touching
    _degraded_stages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = _write_fixture(tmpdir, matching_hash=True)
        prompt, orch, error = _run_pipeline(
            tmpdir, {"CJ2_INTEGRATION_MODE": "SHADOW", "CJ2_SHADOW_WINNER_FIXTURE": fixture_path},
            fable_brief_value=None,  # simulate a real Fable failure
        )
        check("F. Fable failure + SHADOW success: pipeline still reaches writer with no error", error is None)
        check("F. Fable failure + SHADOW success: _degraded_stages contains exactly ['fable_brief']",
              getattr(orch, "_degraded_stages", None) == ["fable_brief"])
        rows = _shadow_rows(orch)
        check("F. Fable failure + SHADOW success: CJ2 bridge still succeeded independently (bridge_valid=1)",
              len(rows) == 1 and rows[0][2] == 1)


def case_off_mode_prompt_matches_shadow_success_prompt(off_prompt, shadow_success_prompt):
    """The single most important assertion in this suite: OFF mode and a
    SUCCESSFUL SHADOW bridge produce the IDENTICAL writer prompt. Nothing
    about a valid CJ-2 winner being available and successfully bridged
    changes one character of what actually gets written and published —
    this is the entire SHADOW-mode contract, proven end-to-end rather than
    argued from code reading alone."""
    check("G. OFF-mode prompt is byte-identical to a successful-SHADOW-mode prompt "
          "(CJ-2 winner availability changes nothing about the real article)",
          off_prompt is not None and off_prompt == shadow_success_prompt)


if __name__ == "__main__":
    off_prompt = case_off_mode_is_inert()
    case_shadow_mode_no_fixture()
    shadow_success_prompt = case_shadow_mode_valid_winner()
    case_shadow_mode_wrong_evidence_packet()
    case_malformed_fixture_does_not_crash_production()
    case_fable_failure_does_not_get_confused_with_cj2_shadow()
    case_off_mode_prompt_matches_shadow_success_prompt(off_prompt, shadow_success_prompt)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
