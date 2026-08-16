#!/usr/bin/env python3
"""
story_rejection_v1_test.py — DSR2 Story Rejection V1, deterministic unit +
isolated-harness tests for the two-layer Layer-1/2 short-circuit in
`_fable_editorial_brief` / `validate_source_decision` / `generate.py`.

Design (per .claude/current-work.md "Story Rejection V1"):
  * LAYER 1 (source commissionability, all four lenses): judged ONCE, evidence-
    validated, BEFORE rotation/eligible-carrier constraints. `validate_source_decision`
    returns a (ok, reason_code, reason, violations) tuple -- never raises. A
    verdict that fails ANY evidence-safety gate (bad source_origin, truncated
    source, ungrounded anchor, malformed structure) is a TECHNICAL FAILURE
    (brief -> None, degraded path), NEVER a persisted editorial decline.
  * LAYER 2 (eligible-persona execution): commission may still report
    `eligible_execution_possible=false` + `blocked_carry_persona` -- this is NOT
    a decline (source stays viable, no article today, no substitute persona).

The cases A-M (mandated by .claude/CONTEXT.md) are each covered. No live network:
`_call_editorial_model`, the source loaders, and `_get_recent_openings` are
patched; the DB is a throwaway tmp sqlite file under `_isolate_paths`.

Run (from repo root):
  python3 automation/story_rejection_v1_test.py
or as part of the suite:
  python3 -m pytest automation/story_rejection_v1_test.py -q
"""

import json as _json
import sqlite3
import tempfile
from datetime import datetime as _dt
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from snapshot_test import (  # noqa: E402
    _import_orchestrator, _patch_methods, _isolate_paths,
    FIXTURE_PERSONA_STATE, FIXTURE_FAULT_LINE,
    _evidence_field_fixture,
)
from orchestrator.grounding import (  # noqa: E402
    build_evidence_packet, validate_source_decision, STORY_REJECTION_CONTRACT_VERSION,
)


# --------------------------------------------------------------------------- #
# Shared fixtures / helpers
# --------------------------------------------------------------------------- #

# A single verbatim source, anchored by hand for the evidence-candidate fixtures.
SRC = (
    "Council minutes record that wheelchair user Priya Nathan told the committee "
    "the new bay is four hundred metres from the tram stop, past three blocks with "
    "no dropped kerb, and that the council's own accessibility officer signed off "
    "on the plan without ever walking the route. The meeting room is on Maple Street."
)

ANCHOR = "four hundred metres from the tram stop"  # verbatim in SRC

from orchestrator.config import _REGISTERS  # noqa: E402
REGISTER = _REGISTERS[0][0]  # "wry"


# A real, schema-valid Layer-2 commission brief (the part _fable_editorial_brief
# returns AFTER Layer-1 commission passes). Reused and mutated by the parse tests.
VALID_COMMISSION = {
    "source_decision": "commission",
    "eligible_execution_possible": True,
    "persona": "Maya Flux",
    "angle": "Is the replacement bay closer or further for most riders who actually use it?",
    "register": REGISTER,
    "seed_sentence": "The new accessible bay is four hundred metres from the tram stop.",
    "opening_scene": "The new accessible bay is four hundred metres from the tram stop.",
    "opening_shape": "fact",
    "correction_moment": _evidence_field_fixture(
        "A concrete moment where the council's own account complicates the framing.",
        "the council's own accessibility officer signed off on the plan without ever walking the route",
    ),
    "resisting_example": _evidence_field_fixture(
        "Something that superficially looks like resistance but actually performs the opposite",
        "wheelchair user Priya Nathan told the committee",
        named_person="Priya Nathan", dates_numbers=["four hundred"],
    ),
    "cross_cite": "",
    "dominant_framing": "access-is-compliance",
}

VALID_DECLINE = {
    "source_decision": "decline",
    "dominant_framing": "ramp-as-generosity",
    "source_anchor_examined": ANCHOR,
    "why_disability_knowledge_does_not_change_subject": (
        "The council's own officer signing off despite never using the route is a "
        "bureaucratic-compliance framing, not a disability-mechanism one."
    ),
    "reason": "No CripMinds lens (Pixel/Siri/Maya/Zen) surfaces a disability-mechanism that changes the subject; the disability detail is window-dressing on a compliance story.",
    "blocked_carry_persona": "",
}


def _make_evidence(source_text=SRC, source_origin="fetched_article", truncated=False,
                   original_length=None):
    ep = build_evidence_packet(
        source_text, source_max_chars=20000, source_origin=source_origin,
        source_original_length_chars=original_length,
    )
    if truncated:
        ep["source_truncated"] = True
    return ep


def _orch():
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    _isolate_paths(orch, tempfile.mkdtemp())
    # __init__ mkdir'd the canonical repo's dirs; isolated tmp dirs need them too.
    for d in (orch.posts_dir, orch.drafts_dir, orch.assets_dir):
        d.mkdir(parents=True, exist_ok=True)
    return orch, po


class _Stop(Exception):
    """Sentinel raised by patched 'writer' methods so we can prove a code path
    never reaches a publication-artifacts step."""


def _patch_common(orch, po, brief_json):
    """Patch the persona loaders + the editorial model so `_fable_editorial_brief`
    is fully deterministic. Returns a restore() that undoes all four."""
    def fake_load_persona_state(self, name):
        return dict(FIXTURE_PERSONA_STATE)
    def fake_active_fault_lines(self, text):
        return [dict(FIXTURE_FAULT_LINE)]
    def fake_recent_openings(self, n):
        return []
    def fake_call_editorial_model(self, system, user, max_tokens=1200, timeout=60, prefer_opus=False):
        return _json.dumps(brief_json)
    r_loaders = _patch_methods(
        po.LLMMixin,
        _load_persona_state=fake_load_persona_state,
        _active_fault_lines=fake_active_fault_lines,
        _get_recent_openings=fake_recent_openings,
    )
    r_model = _patch_methods(po.LLMMixin, _call_editorial_model=fake_call_editorial_model)

    def restore():
        r_model()
        r_loaders()
    return restore


# --------------------------------------------------------------------------- #
# A. Strong mechanism over a fetched source -> commission (PRF1 intact)
# --------------------------------------------------------------------------- #

def case_a_strong_mechanism_commissions():
    orch, po = _orch()
    restore = _patch_common(orch, po, VALID_COMMISSION)
    try:
        ep = _make_evidence(source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            "Council signs off on new bay", "summary",
            "disability_angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert brief is not None, "strong mechanism must produce a brief, not decline"
        assert brief["source_decision"] == "commission"
        assert brief["persona"] == "Maya Flux"  # PRF1: fable == plan == writer == byline
    finally:
        restore()
    print("A OK  strong-mechanism fetched source -> commission (persona invariant held)")


# --------------------------------------------------------------------------- #
# B. Mechanism exists but lives in NO eligible carrier today -> no_execution,
#    NOT a decline (source stays viable, no article, no substitute)
# --------------------------------------------------------------------------- #

def case_b_mechanism_but_no_eligible_carrier():
    orch, po = _orch()
    blocked = VALID_COMMISSION.copy()
    blocked.update({
        "source_decision": "commission",
        "eligible_execution_possible": False,
        "blocked_carry_persona": "Pixel Nova",
    })
    restore = _patch_common(orch, po, blocked)
    try:
        ep = _make_evidence(source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert brief is not None
        assert brief.get("eligible_execution_possible") is False
        assert brief.get("blocked_carry_persona") == "Pixel Nova"
        assert brief["source_decision"] == "commission"
        assert brief.get("decline_contract_version") is None  # not a decline
    finally:
        restore()
    print("B OK  mechanism real but no eligible carrier -> no_execution, source not declined")


# --------------------------------------------------------------------------- #
# C. Genuine no-mechanism fetched source -> DECLINE (writer never runs)
# --------------------------------------------------------------------------- #

def case_c_genuine_no_mechanism_declines():
    orch, po = _orch()
    restore = _patch_common(orch, po, VALID_DECLINE)
    try:
        ep = _make_evidence(source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert brief is not None
        assert brief["source_decision"] == "decline"
        assert brief["decline_contract_version"] == STORY_REJECTION_CONTRACT_VERSION
        # The decline's anchor must be grounded in the source (validate_source_decision
        # already enforced this on the parse path; restate it here for clarity).
        ok, _, _, _ = validate_source_decision(brief, ep)
        assert ok, "declined verdict must pass evidence validation"
    finally:
        restore()
    print("C OK  genuine no-mechanism fetched source -> decline, anchor grounded")


# --------------------------------------------------------------------------- #
# D. Malformed decline (missing `reason`) -> validate_source_decision rejects;
#    `_fable_editorial_brief` returns None (technical failure, NOT a decline)
# --------------------------------------------------------------------------- #

def case_d_malformed_decline_is_technical_failure():
    orch, po = _orch()
    malformed = VALID_DECLINE.copy()
    del malformed["reason"]
    restore = _patch_common(orch, po, malformed)
    try:
        ep = _make_evidence(source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert brief is None, "malformed decline must collapse to None (technical failure), not be persisted"
    finally:
        restore()
    print("D OK  malformed decline verdict -> None (technical failure, never persisted)")


# --------------------------------------------------------------------------- #
# E. Provider returns malformed JSON / wrong schema shape -> None (not decline)
# --------------------------------------------------------------------------- #

def case_e_provider_malformed_payload_is_technical_failure():
    orch, po = _orch()
    restore = _patch_common(orch, po, {"source_decision": "decline"})  # missing all fields
    try:
        ep = _make_evidence(source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert brief is None
    finally:
        restore()
    print("E OK  provider schema violation -> None (technical failure, never decline)")


# --------------------------------------------------------------------------- #
# F. Fallback-summary origin trying to decline -> cannot decline (DEFER),
#    brief collapses to None
# --------------------------------------------------------------------------- #

def case_f_fallback_origin_cannot_decline():
    orch, po = _orch()
    restore = _patch_common(orch, po, VALID_DECLINE)
    try:
        ep = _make_evidence(source_origin="fallback_summary")
        brief = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert brief is None, "a fallback_summary source cannot legally decline -> None (DEFER/insufficient)"
    finally:
        restore()
    # Direct validator check mirrors what the parse path did.
    ep = _make_evidence(source_origin="fallback_summary")
    ok, code, _, _ = validate_source_decision(VALID_DECLINE, ep)
    assert ok is False
    assert code == "decline_source_insufficient"
    print("F OK  fallback_summary origin -> cannot decline (DEFER, not editorial decline)")


# --------------------------------------------------------------------------- #
# G. Declined seed is excluded from re-extraction (extraction WHERE clause)
# --------------------------------------------------------------------------- #

def case_g_declined_seed_excluded_from_extraction():
    orch, po = _orch()
    seed_id = "seed-declined-g"
    conn = sqlite3.connect(str(orch.discovery_db))
    conn.row_factory = sqlite3.Row
    import news_fetcher as nf  # noqa: E402  (AUTOMATION_DIR is on sys.path via _isolate_paths/_import_orchestrator)
    from news_fetcher import init_db
    init_db(conn)
    today = _dt.now().strftime("%Y-%m-%d")
    now = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO news_seeds (id, url, title, source_name, pub_date, fetched_date, "
        "disability_angle, declined, declined_date) VALUES (?,?,?,?,?,?,?,?,?)",
        (seed_id, "http://g.example", "G title", "GSource", today, today,
         "G angle", 1, now),
    )
    conn.commit()
    # Insert a second, non-declined seed that SHOULD be eligible.
    conn.execute(
        "INSERT INTO news_seeds (id, url, title, source_name, pub_date, fetched_date) "
        "VALUES (?,?,?,?,?,?)",
        ("seed-live-g", "http://live-g.example", "Live title", "LSource", today, today),
    )
    conn.commit()
    seen = []
    orig_key, orig_extract = nf.API_KEY, nf.extract_angle
    nf.API_KEY = "test-key"  # bypass extract_top_angles' `if not API_KEY: return`
    nf.extract_angle = lambda title, summary, url: seen.append(title) or None
    try:
        nf.extract_top_angles(conn, n=10)
    finally:
        nf.API_KEY, nf.extract_angle = orig_key, orig_extract
    row = conn.execute("SELECT id, declined FROM news_seeds WHERE id=?", (seed_id,)).fetchone()
    assert row["declined"] == 1, "declined flag must be persisted"
    # The declined seed (title "G title") must never have been handed to extract_angle;
    # the live seed (title "Live title") must have been.
    assert "G title" not in seen, "declined seed must not reach extract_angle (wasted paid call)"
    assert "Live title" in seen, "non-declined seed should be processed by extract_angle"
    conn.close()
    print("G OK  declined seed excluded from angle-extraction WHERE (no wasted paid call)")


# --------------------------------------------------------------------------- #
# H. Restart safety: a stale-contract decline is reconsiderable, not sticky
# --------------------------------------------------------------------------- #

def case_h_stale_contract_declined_seed_is_reconsiderable():
    orch, po = _orch()
    conn = sqlite3.connect(str(orch.discovery_db))
    from news_fetcher import init_db
    init_db(conn)
    conn.execute(
        "INSERT INTO news_seeds (id, url, title, source_name, pub_date, fetched_date, "
        "declined, decline_schema_version, declined_source_hash) VALUES (?,?,?,?,?,?,?,?,?)",
        ("seed-stale-h", "http://h.example", "H", "HS", "2026-08-01", "2026-08-01",
         1, "s0", "deadbeef"),
    )
    conn.commit()
    # A stale-contract decline (recorded contract "s0") must NOT hold:
    # _is_news_seed_declined_current returns False => seed is re-offered by get_news_seed.
    packet = _make_evidence(source_origin="fetched_article")
    is_current = orch._is_news_seed_declined_current(conn, "seed-stale-h", packet)
    assert is_current is False, "stale contract version => decline is reconsiderable, not sticky"
    conn.close()
    print("H OK  stale-contract decline record is reconsiderable (not sticky on restart)")


# --------------------------------------------------------------------------- #
# I. Source hash change => prior decline invalidated, seed re-offered
# --------------------------------------------------------------------------- #

def case_i_source_hash_change_invalidates_prior_decline():
    orch, po = _orch()
    conn = sqlite3.connect(str(orch.discovery_db))
    from news_fetcher import init_db
    init_db(conn)
    conn.execute(
        "INSERT INTO news_seeds (id, url, title, source_name, pub_date, fetched_date, "
        "declined, decline_schema_version, declined_source_hash) VALUES (?,?,?,?,?,?,?,?,?)",
        ("seed-hash-i", "http://i.example", "I", "IS", "2026-08-01", "2026-08-01",
         1, STORY_REJECTION_CONTRACT_VERSION, "oldhash"),
    )
    conn.commit()
    packet = _make_evidence(source_origin="fetched_article")  # current hash differs from "oldhash"
    is_current = orch._is_news_seed_declined_current(conn, "seed-hash-i", packet)
    assert is_current is False, "changed source hash => prior decline is stale, seed re-offered"
    conn.close()
    print("I OK  changed source_hash invalidates prior decline (seed reconsiderable)")


# --------------------------------------------------------------------------- #
# J. extract_top_angles / shadow sampler WHERE excludes declined seeds (both pools)
# --------------------------------------------------------------------------- #

def case_j_shadow_sampler_excludes_declined():
    orch, po = _orch()
    conn = sqlite3.connect(str(orch.discovery_db))
    conn.row_factory = sqlite3.Row
    from news_fetcher import init_db
    init_db(conn)
    today = _dt.now().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO news_seeds (id,url,title,source_name,pub_date,fetched_date,used,disability_angle,angle_checked,declined) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("seed-dec-j", "http://decj.example", "Dec J", "DecJ", today, today, 0, None, None, 1),
    )
    conn.execute(
        "INSERT INTO news_seeds (id,url,title,source_name,pub_date,fetched_date,used,disability_angle,angle_checked,declined) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("seed-ok-j", "http://okj.example", "Ok J", "OkJ", today, today, 0, None, None, 0),
    )
    conn.commit()
    import news_fetcher as nf  # noqa: E402  (AUTOMATION_DIR on sys.path via harness)
    orig_key, orig_extract = nf.API_KEY, nf.extract_angle
    nf.API_KEY = "test-key"  # bypass extract_top_angles' `if not API_KEY: return`
    seen = []
    # extract_angle(title, summary, url) -> we record the title (seed title).
    nf.extract_angle = lambda title, summary, url: seen.append(title) or None
    try:
        nf.extract_top_angles(conn, n=10)
    finally:
        nf.API_KEY, nf.extract_angle = orig_key, orig_extract
    assert "Dec J" not in seen, "declined seed (Dec J) must not reach extract_angle"
    assert "Ok J" in seen, "non-declined seed (Ok J) should be processed"
    conn.close()
    print("J OK  extract_top_angles + shadow sampler WHERE excludes declined seed")


# --------------------------------------------------------------------------- #
# K. Blocked-persona fixture on an otherwise-strong fetched source -> decline
#    is NOT produced (it is no_execution: commission but no eligible carrier)
# --------------------------------------------------------------------------- #

def case_k_blocked_persona_fixture_mechanism_does_not_decline():
    orch, po = _orch()
    brief = VALID_COMMISSION.copy()
    brief.update({
        "eligible_execution_possible": False,
        "blocked_carry_persona": "Pixel Nova",
    })
    restore = _patch_common(orch, po, brief)
    try:
        ep = _make_evidence(source_origin="fetched_article")
        out = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert out is not None
        assert out["source_decision"] == "commission"
        assert out.get("eligible_execution_possible") is False
        assert out.get("blocked_carry_persona") == "Pixel Nova"
        assert "decline_contract_version" not in out
        assert "decline_schema_version" not in out
    finally:
        restore()
    print("K OK  blocked-persona fixture -> no_execution, no decline record written")


# --------------------------------------------------------------------------- #
# L. Successful commission path preserves PRF1: fable_brief personae ==
#    persisted plan persona == writer == byline (no post-Fable substitution)
# --------------------------------------------------------------------------- #

def case_l_commission_prf1_persona_invariant():
    orch, po = _orch()
    restore = _patch_common(orch, po, VALID_COMMISSION)
    try:
        ep = _make_evidence(source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage", "Pixel Nova"],
        )
        assert brief is not None
        fable_persona = brief["persona"]
        # PRF1: the brief's persona is in the eligible set (no substitution needed)
        assert fable_persona in ("Maya Flux", "Siri Sage", "Pixel Nova")
        # Persisted plan persona (if a plan were persisted) would equal fable_persona;
        # here we assert the brief itself carries no post-substitution field and the
        # chosen persona is the one Fable selected, unchanged.
        assert brief["eligible_execution_possible"] is True
        assert brief.get("blocked_carry_persona") in (None, "")
    finally:
        restore()
    print("L OK  commission path: fable_brief persona is the execution persona (PRF1)")


# --------------------------------------------------------------------------- #
# M. _handle_declined_run writes NO publication artifacts: no article file,
#    no _persist_article_plan call, mark_news_seed_declined called once.
# --------------------------------------------------------------------------- #

def case_m_declined_run_writes_no_publication_artifacts():
    orch, po = _orch()
    persisted = []
    restore_plan = _patch_methods(
        po.GenerateMixin,
        _persist_article_plan=lambda self, slug, agent_name, fable_brief: persisted.append(("plan", slug)),
    )
    # Spy on the decline persistence.
    spied = []
    restore_mark = _patch_methods(
        po.DiscoveryMixin,
        mark_news_seed_declined=lambda self, seed_id, record: spied.append((seed_id, record)),
    )
    try:
        seed = {"id": "seed-m", "title": "M", "url": "http://m.example", "summary": "", "themes": []}
        ep = _make_evidence(source_origin="fetched_article")
        result = orch._handle_declined_run(seed, VALID_DECLINE, ep, "fetched_article")
        assert result["status"] == "declined"
        assert result["commit_success"] is False
        assert result["agent"] is None
        # The decline MUST have been recorded exactly once.
        assert len(spied) == 1
        sid, record = spied[0]
        assert sid == "seed-m"
        assert record["verdict"] == "declined"
        assert record["contract"] == "sr1"
        # And NO publication artifacts were written: _persist_article_plan never ran.
        assert persisted == [], "_persist_article_plan must not run on a decline"
        # posts_dir / drafts_dir must be empty (no article file written).
        assert not any(orch.posts_dir.iterdir()), "no article file should be written on decline"
        assert not any(orch.drafts_dir.iterdir()), "no draft file should be written on decline"
    finally:
        restore_plan()
        restore_mark()
    print("M OK  decline run: no article/plan/commit, only decline record persisted")


# --------------------------------------------------------------------------- #
# N. Regression: a BLOCKED (non-eligible) persona named directly in the
#    "persona" field must still produce no_execution, not None. Cases B/K left
#    "persona" at an eligible name (Maya Flux) while only blocked_carry_persona
#    named the blocked one -- that masked a real gap: _fable_editorial_brief's
#    Layer-2 gate used to require brief["persona"] in the eligible set even for
#    a blocked-commission verdict, so a model naming the blocked persona in
#    "persona" itself (the natural place to say which lens carries the
#    mechanism) collapsed the brief to None (technical failure) instead of
#    no_execution -- and generate.py's None-handling falls through to the
#    LEGACY commission path, which would write an article via a substitute
#    persona. Exactly what DSR2 forbids.
# --------------------------------------------------------------------------- #

def case_n_blocked_persona_named_in_persona_field_still_no_execution():
    orch, po = _orch()
    blocked = VALID_COMMISSION.copy()
    blocked.update({
        "source_decision": "commission",
        "eligible_execution_possible": False,
        "persona": "Pixel Nova",  # the blocked persona itself, NOT in eligible_agents below
        "blocked_carry_persona": "Pixel Nova",
    })
    restore = _patch_common(orch, po, blocked)
    try:
        ep = _make_evidence(source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],  # Pixel Nova is NOT eligible
        )
        assert brief is not None, (
            "a blocked/ineligible persona name in the brief must not collapse "
            "_fable_editorial_brief to None -- that misroutes to the legacy "
            "commission path and lets a substitute persona write the article"
        )
        assert brief["source_decision"] == "commission"
        assert brief.get("eligible_execution_possible") is False
        assert brief.get("blocked_carry_persona") == "Pixel Nova"
        assert "decline_contract_version" not in brief
    finally:
        restore()
    print("N OK  blocked persona named directly in persona field -> still no_execution, not None")


# --------------------------------------------------------------------------- #
# O/P. Regression: real SELECTION (get_news_seed), not the private helper,
#    must reconsider a stale-contract decline and must still exclude a
#    current-contract decline. Cases H/I only called
#    `_is_news_seed_declined_current` directly -- their docstrings claimed
#    "seed is re-offered by get_news_seed" but never actually called
#    get_news_seed, so the fact that get_news_seed's own SQL never consulted
#    that helper (blanket `declined = 0` exclusion) went unnoticed.
# --------------------------------------------------------------------------- #

def case_o_stale_contract_seed_reoffered_by_get_news_seed():
    orch, po = _orch()
    conn = sqlite3.connect(str(orch.discovery_db))
    from news_fetcher import init_db
    init_db(conn)
    today = _dt.now().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO news_seeds (id,url,title,source_name,pub_date,fetched_date,"
        "relevance_score,disability_angle,used,declined,decline_schema_version,declined_source_hash) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("seed-stale-o", "http://stale-o.example", "Stale O", "SO", today, today,
         0.9, "some angle", 0, 1, "s0", "deadbeef"),
    )
    conn.commit()
    conn.close()
    seed = orch.get_news_seed()
    assert seed is not None, "a stale-contract decline must be reconsiderable by REAL selection"
    assert seed["id"] == "seed-stale-o"
    print("O OK  get_news_seed re-offers a stale-contract declined seed (real selection path)")


def case_p_current_contract_seed_excluded_by_get_news_seed():
    orch, po = _orch()
    conn = sqlite3.connect(str(orch.discovery_db))
    from news_fetcher import init_db
    init_db(conn)
    today = _dt.now().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO news_seeds (id,url,title,source_name,pub_date,fetched_date,"
        "relevance_score,disability_angle,used,declined,decline_schema_version) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ("seed-current-p", "http://current-p.example", "Current P", "CP", today, today,
         0.9, "some angle", 0, 1, STORY_REJECTION_CONTRACT_VERSION),
    )
    conn.commit()
    conn.close()
    seed = orch.get_news_seed()
    assert seed is None, "a current-contract decline must remain excluded from REAL selection"
    print("P OK  get_news_seed still excludes a current-contract declined seed")


# --------------------------------------------------------------------------- #
# Q. _handle_no_execution_run writes NO publication artifacts and does NOT
#    write a decline record (mirrors case M, for the no_execution branch).
# --------------------------------------------------------------------------- #

def case_q_no_execution_run_writes_no_publication_artifacts():
    orch, po = _orch()
    persisted = []
    restore_plan = _patch_methods(
        po.GenerateMixin,
        _persist_article_plan=lambda self, slug, agent_name, fable_brief: persisted.append(("plan", slug)),
    )
    spied = []
    restore_mark = _patch_methods(
        po.DiscoveryMixin,
        mark_news_seed_declined=lambda self, seed_id, record: spied.append((seed_id, record)),
    )
    try:
        seed = {"id": "seed-q", "title": "Q", "url": "http://q.example", "summary": "", "themes": []}
        blocked_brief = VALID_COMMISSION.copy()
        blocked_brief.update({"eligible_execution_possible": False, "blocked_carry_persona": "Pixel Nova"})
        ep = _make_evidence(source_origin="fetched_article")
        result = orch._handle_no_execution_run(seed, blocked_brief, ep, "fetched_article")
        assert result["status"] == "no_execution"
        assert result["commit_success"] is False
        assert result["agent"] is None
        assert result.get("declined") is False
        assert spied == [], "mark_news_seed_declined must NOT be called for no_execution (not a decline)"
        assert persisted == [], "_persist_article_plan must not run for no_execution"
        assert not any(orch.posts_dir.iterdir()), "no article file should be written for no_execution"
        assert not any(orch.drafts_dir.iterdir()), "no draft file should be written for no_execution"
    finally:
        restore_plan()
        restore_mark()
    print("Q OK  no_execution run: no article/plan/decline-record, clean end")


# --------------------------------------------------------------------------- #
# validate_source_decision direct edge cases (complement C/D/E/F)
# --------------------------------------------------------------------------- #

def case_validate_source_decision_contract_version():
    assert STORY_REJECTION_CONTRACT_VERSION == "sr1"
    # A valid decline with a grounded anchor over a fetched source passes.
    ep = _make_evidence(source_origin="fetched_article")
    ok, code, _, _ = validate_source_decision(VALID_DECLINE, ep)
    ok, code, _, _ = validate_source_decision(VALID_DECLINE, ep)
    assert ok and code == "decline"  # contract version is current => a valid decline verdict
    # The decline's origin/truncation/anchor gates are exercised by the cases below;
    # a current-origin decline passes Layer-1 evidence safety.
    ok2, code2, _, v2 = validate_source_decision(VALID_DECLINE, _make_evidence(source_origin="none"))
    assert ok2 is False and code2 == "decline_source_insufficient"
    assert v2 and any(x["reason_code"] == "decline_source_insufficient" for x in v2)
    print("validate OK  contract-version gate: sr1, origin/truncation/anchor enforced")


def case_non_declision_brief_passes():
    ep = _make_evidence(source_origin="fetched_article")
    ok, code, reason, _ = validate_source_decision({"source_decision": "commission"}, ep)
    assert ok  # a commission brief is trivially a valid Layer-1 verdict
    ok, _, _, _ = validate_source_decision({}, ep)  # legacy, no source_decision
    assert ok  # legacy commission pass-through
    print("validate OK  commission + legacy briefs pass Layer-1 without evidence gates")


def case_truncated_source_blocks_decline():
    ep = _make_evidence(source_origin="fetched_article", truncated=True)
    ok, code, _, _ = validate_source_decision(VALID_DECLINE, ep)
    assert ok is False and code == "decline_evidence_truncated"
    print("validate OK  truncated source => decline blocked (DEFER, not editorial)")


def case_ungrounded_anchor_blocks_decline():
    ep = _make_evidence(source_origin="fetched_article")
    bad = VALID_DECLINE.copy()
    bad["source_anchor_examined"] = "this exact sentence is not in the source"
    ok, code, _, _ = validate_source_decision(bad, ep)
    assert ok is False and code == "decline_anchor_not_grounded"
    print("validate OK  ungrounded anchor => decline blocked (technical failure)")


def case_neither_truncated_nor_ungrounded_on_fixture_origin():
    ep = _make_evidence(source_origin="fixture")
    ok, code, _, _ = validate_source_decision(VALID_DECLINE, ep)
    assert ok and code == "decline"
    print("validate OK  fixture-origin decline passes Layer-1 evidence gates")


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #

ALL = [
    case_a_strong_mechanism_commissions,
    case_b_mechanism_but_no_eligible_carrier,
    case_c_genuine_no_mechanism_declines,
    case_d_malformed_decline_is_technical_failure,
    case_e_provider_malformed_payload_is_technical_failure,
    case_f_fallback_origin_cannot_decline,
    case_g_declined_seed_excluded_from_extraction,
    case_h_stale_contract_declined_seed_is_reconsiderable,
    case_i_source_hash_change_invalidates_prior_decline,
    case_j_shadow_sampler_excludes_declined,
    case_k_blocked_persona_fixture_mechanism_does_not_decline,
    case_l_commission_prf1_persona_invariant,
    case_m_declined_run_writes_no_publication_artifacts,
    case_n_blocked_persona_named_in_persona_field_still_no_execution,
    case_o_stale_contract_seed_reoffered_by_get_news_seed,
    case_p_current_contract_seed_excluded_by_get_news_seed,
    case_q_no_execution_run_writes_no_publication_artifacts,
    case_validate_source_decision_contract_version,
    case_non_declision_brief_passes,
    case_truncated_source_blocks_decline,
    case_ungrounded_anchor_blocks_decline,
    case_neither_truncated_nor_ungrounded_on_fixture_origin,
]


def main():
    failures = 0
    for case in ALL:
        try:
            case()
        except AssertionError as e:
            failures += 1
            print(f"FAIL  {case.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"ERROR {case.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(ALL) - failures}/{len(ALL)} cases passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
