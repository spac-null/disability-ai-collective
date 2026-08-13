"""
cj2_shadow.py — Phase G.2 CJ-2 shadow integration plumbing.

Adds an OFF-by-default, additive-only hook that lets a future CJ-2 winner
(supplied today only as a saved/synthetic fixture — no live CJ-1..Stage-C
orchestration exists yet, and none is invoked by this module) be bridged
into `cj2_winner_bridge`'s output shape and recorded, WITHOUT ever
influencing the live article this run actually publishes.

Mode is read from the CJ2_INTEGRATION_MODE environment variable:
  OFF    (default, unset) — this mixin's own entry point is not even called
         by generate.py; if it somehow were, it still no-ops immediately.
  SHADOW — attempts to load a configured winner fixture, bridges it if
         valid, and PERSISTS the outcome to automation/engagement.db's new
         cj2_shadow_runs table. Never touches fable_brief, agent_name, or
         any value the real pipeline uses. Never raises — mirrors
         generate.py's own `_persist_article_plan` try/except discipline
         exactly, since a shadow-path failure must never be indistinguishable
         from, or cause, a real production failure.

PRODUCTION_AUTHORITY mode does not exist in this module and is not
implemented anywhere in this pass — see
.claude/master-roadmap-2026-08-13.md's `## PHASE G.2` for why.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime

# Path-provenance states (Phase G / G.1 `## G.1.9`). Only LIVE_LEGACY_PATH
# and CJ2_SHADOW are ever emitted by this pass — the other two are defined
# here for forward documentation only, per instruction 6's own "only states
# genuinely reachable should be emitted."
PATH_LIVE_LEGACY = "LIVE_LEGACY_PATH"
PATH_CJ2_SHADOW = "CJ2_SHADOW"
PATH_CJ2_WINNER_DRAFT = "CJ2_WINNER_DRAFT"   # not reachable this pass
PATH_CJ2_PRODUCTION = "CJ2_PRODUCTION"       # not reachable this pass

REASON_NO_CJ2_WINNER = "NO_CJ2_WINNER"
REASON_CJ2_SHADOW_UNAVAILABLE = "CJ2_SHADOW_UNAVAILABLE"

_MODE_OFF = "OFF"
_MODE_SHADOW = "SHADOW"


def _current_integration_mode() -> str:
    return os.environ.get("CJ2_INTEGRATION_MODE", _MODE_OFF).strip().upper()


class CJ2ShadowMixin:
    def _cj2_shadow_attempt(self, agent_name, evidence_packet, slug=None):
        """Called (only when integration mode != OFF) right after the real
        fable_brief/degraded-stage block has already been finalized in
        generate.py. Purely a side effect: reads a configured winner
        fixture if one exists, bridges it, records the outcome. Return
        value is never used by the caller — nothing here can change what
        gets published. Never raises."""
        try:
            mode = _current_integration_mode()
            if mode == _MODE_OFF:
                return
            if mode != _MODE_SHADOW:
                # Any value other than OFF/SHADOW (typos, a future mode name
                # used prematurely) is treated as SHADOW_UNAVAILABLE rather
                # than silently doing nothing or silently doing something
                # stronger than intended.
                self._persist_cj2_shadow_run({
                    "slug": slug, "agent": agent_name, "path_provenance": PATH_CJ2_SHADOW,
                    "bridge_valid": False, "failure_reason": REASON_CJ2_SHADOW_UNAVAILABLE,
                    "winner_present": False, "bridge_version": None,
                    "engine_label": None, "stage_c_letter": None, "cj1_seed_id": None,
                })
                return

            fixture_path = os.environ.get("CJ2_SHADOW_WINNER_FIXTURE", "")
            if not fixture_path or not os.path.isfile(fixture_path):
                self._persist_cj2_shadow_run({
                    "slug": slug, "agent": agent_name, "path_provenance": PATH_CJ2_SHADOW,
                    "bridge_valid": False, "failure_reason": REASON_NO_CJ2_WINNER,
                    "winner_present": False, "bridge_version": None,
                    "engine_label": None, "stage_c_letter": None, "cj1_seed_id": None,
                })
                return

            import cj2_winner_bridge  # deferred/lazy import — see module docstring

            try:
                with open(fixture_path, "r", encoding="utf-8") as f:
                    fixture = json.load(f)
            except Exception as e:
                self._persist_cj2_shadow_run({
                    "slug": slug, "agent": agent_name, "path_provenance": PATH_CJ2_SHADOW,
                    "bridge_valid": False,
                    "failure_reason": cj2_winner_bridge.REASON_WINNER_RECONSTRUCTION_FAILED,
                    "winner_present": False, "bridge_version": cj2_winner_bridge.BRIDGE_VERSION,
                    "engine_label": None, "stage_c_letter": None, "cj1_seed_id": None,
                    "detail": f"fixture unreadable/invalid JSON: {e}",
                })
                return

            winner = fixture.get("winner")
            seed = fixture.get("seed")
            cj1_seed_id = fixture.get("cj1_seed_id")
            stage_c_letter = fixture.get("stage_c_letter")
            engine_label = fixture.get("engine_label")
            admission_gate_terminal_state = fixture.get("admission_gate_terminal_state")

            try:
                payload = cj2_winner_bridge.build_bridge_payload(
                    winner, seed, evidence_packet, agent_name,
                    cj1_seed_id=cj1_seed_id, stage_c_letter=stage_c_letter,
                    engine_label=engine_label,
                    admission_gate_terminal_state=admission_gate_terminal_state,
                )
            except cj2_winner_bridge.BridgeError as e:
                self._persist_cj2_shadow_run({
                    "slug": slug, "agent": agent_name, "path_provenance": PATH_CJ2_SHADOW,
                    "bridge_valid": False, "failure_reason": e.reason,
                    "winner_present": winner is not None,
                    "bridge_version": cj2_winner_bridge.BRIDGE_VERSION,
                    "engine_label": engine_label, "stage_c_letter": stage_c_letter,
                    "cj1_seed_id": cj1_seed_id, "detail": str(e),
                })
                return

            # Success — recorded, never consumed. `payload` is deliberately
            # discarded beyond this logging call: nothing downstream reads
            # it, no fable_brief field is touched, no publication decision
            # is affected. This is the entire SHADOW-mode contract.
            self._persist_cj2_shadow_run({
                "slug": slug, "agent": agent_name, "path_provenance": PATH_CJ2_SHADOW,
                "bridge_valid": True, "failure_reason": None,
                "winner_present": True, "bridge_version": payload["_bridge_provenance"]["bridge_version"],
                "engine_label": payload["_bridge_provenance"]["engine_label"],
                "stage_c_letter": payload["_bridge_provenance"]["stage_c_letter"],
                "cj1_seed_id": payload["_bridge_provenance"]["cj1_seed_id"],
            })
        except Exception as e:
            # Outer catch-all, mirrors generate.py's _persist_article_plan
            # discipline exactly: a shadow-path failure of ANY kind must
            # never propagate into the real production run.
            self.logger.warning("CJ-2 shadow attempt failed (non-fatal, production unaffected): %s", e)

    def _persist_cj2_shadow_run(self, record: dict) -> None:
        """Same automation/engagement.db file _persist_article_plan/
        _persist_review_signals already write to — a future join between
        "what was planned," "what published," "did readers engage," and
        "was a CJ-2 winner available" is one file, not a cross-database
        query. Never raises."""
        try:
            db_dir = self.repo_root / "automation"
            db_dir.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_dir / "engagement.db")
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cj2_shadow_runs (
                        id                              INTEGER PRIMARY KEY AUTOINCREMENT,
                        recorded_at                     TEXT NOT NULL,
                        slug                             TEXT,
                        agent                            TEXT,
                        integration_mode                TEXT NOT NULL,
                        path_provenance                  TEXT NOT NULL,
                        bridge_valid                     INTEGER NOT NULL,
                        failure_reason                   TEXT,
                        winner_present                   INTEGER NOT NULL,
                        bridge_version                   TEXT,
                        engine_label                     TEXT,
                        stage_c_letter                   TEXT,
                        cj1_seed_id                      TEXT,
                        detail                           TEXT
                    )
                """)
                conn.execute(
                    "INSERT INTO cj2_shadow_runs "
                    "(recorded_at, slug, agent, integration_mode, path_provenance, bridge_valid, "
                    " failure_reason, winner_present, bridge_version, engine_label, stage_c_letter, "
                    " cj1_seed_id, detail) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        record.get("slug"), record.get("agent"), _current_integration_mode(),
                        record.get("path_provenance"), 1 if record.get("bridge_valid") else 0,
                        record.get("failure_reason"), 1 if record.get("winner_present") else 0,
                        record.get("bridge_version"), record.get("engine_label"),
                        record.get("stage_c_letter"), record.get("cj1_seed_id"), record.get("detail"),
                    ),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            self.logger.warning("CJ-2 shadow-run persistence failed (non-fatal): %s", e)
