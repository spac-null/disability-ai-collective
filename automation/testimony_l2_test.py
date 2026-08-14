#!/usr/bin/env python3
"""
testimony_l2_test.py — static test suite for testimony_l2.py (A-M
reconciliation item L, 2026-08-14).

L2 SHADOW SCAFFOLD -- OFF by default. This suite proves the deterministic
testimony-needed heuristic, the companion-candidate eligibility checks, and
(critically) that OFF mode leaves evidence_packet and production behavior
completely unchanged. Covers every scenario instruction 9 named: primary
already has testimony, primary lacks it, candidate available, no candidate
available, low-quality/unverifiable candidate, duplicate of primary,
provenance kept separate, primary factual authority unchanged, feature OFF
unchanged.

Uses a real (throwaway, tempdir) sqlite file for the persistence path and a
minimal fake orchestrator object (repo_root + logger) rather than the full
ProductionOrchestrator, matching this repo's existing shadow-check test
convention (see cj2_shadow_integration_test.py). Zero network, zero model
calls, zero article generation.

USAGE: python3 automation/testimony_l2_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import json
import logging
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator import testimony_l2  # noqa: E402
from orchestrator.testimony_l2 import (  # noqa: E402
    TestimonyL2Mixin, _testimony_needed_heuristic, _check_companion_eligibility,
    REASON_TESTIMONY_ALREADY_PRESENT, REASON_NO_COMPANION_FIXTURE,
    REASON_DUPLICATE_OF_PRIMARY, REASON_UNVERIFIABLE_ATTRIBUTION,
    REASON_TOO_SHORT, REASON_MISSING_FIELDS, REASON_ATTACHED,
)
from orchestrator.grounding import build_evidence_packet  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


class _FakeOrch(TestimonyL2Mixin):
    def __init__(self, tmpdir):
        self.repo_root = Path(tmpdir)
        self.logger = logging.getLogger("testimony_l2_test")


def _read_l2_runs(tmpdir):
    conn = sqlite3.connect(Path(tmpdir) / "automation" / "engagement.db")
    try:
        rows = conn.execute(
            "SELECT mode, testimony_needed, needed_reason, companion_attached, "
            "outcome_reason, companion_url, companion_person FROM l2_testimony_runs "
            "ORDER BY id DESC LIMIT 1"
        ).fetchall()
        return rows[0] if rows else None
    finally:
        conn.close()


# ── _testimony_needed_heuristic ────────────────────────────────────────────

def case_primary_already_has_testimony():
    text = 'The audit found the ramp unused. "I stopped going after the second time they lost my chair," said Maria Csontos, a wheelchair user in the program.'
    needed, reason = _testimony_needed_heuristic(text)
    check("primary source with attributed first-person quote -> testimony NOT needed",
          needed is False and reason == REASON_TESTIMONY_ALREADY_PRESENT)


def case_primary_lacks_testimony():
    text = "The audit found 40% of ramps citywide were non-compliant with the 2019 code. Repairs are budgeted for next fiscal year."
    needed, reason = _testimony_needed_heuristic(text)
    check("primary source with no quotes at all -> testimony needed",
          needed is True and reason == "NO_FIRST_PERSON_TESTIMONY_DETECTED")


def case_third_person_quote_is_not_testimony():
    text = 'The council report stated: "Conditions at the facility were found to be substandard across every metric measured this quarter."'
    needed, reason = _testimony_needed_heuristic(text)
    check("attributed but third-person institutional quote (no first-person marker) -> "
          "still needed (not genuine lived-experience testimony)",
          needed is True)


def case_no_source_text():
    needed, reason = _testimony_needed_heuristic(None)
    check("no source_text at all -> needed (nothing to check)", needed is True)
    needed, reason = _testimony_needed_heuristic("")
    check("empty source_text -> needed", needed is True)


# ── _check_companion_eligibility ───────────────────────────────────────────

def _packet(source_text="Some primary factual reporting about the topic at length.", source_hash_override=None):
    p = build_evidence_packet(source_text, source_max_chars=5000, source_origin="fixture")
    if source_hash_override is not None:
        p["source_hash"] = source_hash_override
    return p


def case_eligible_candidate_attaches():
    packet = _packet()
    candidate = {"url": "https://example.org/interview", "person": "Jamie Alt",
                 "text": "I waited forty minutes for the lift and missed the appointment entirely, again."}
    eligible, reason = _check_companion_eligibility(candidate, packet)
    check("well-formed, non-duplicate, attributed candidate -> eligible", eligible is True and reason == REASON_ATTACHED)


def case_missing_fields_rejected():
    packet = _packet()
    for bad in [{}, {"url": "https://x"}, {"text": "some text here that is long enough to pass length"},
                {"url": "https://x", "text": ""}, "not a dict", None]:
        eligible, reason = _check_companion_eligibility(bad, packet)
        check(f"malformed candidate {bad!r} -> ineligible (MISSING_FIELDS)",
              eligible is False and reason == REASON_MISSING_FIELDS)


def case_unverifiable_attribution_rejected():
    packet = _packet()
    candidate = {"url": "https://example.org/x", "text": "This is a sufficiently long companion text with no named speaker at all."}
    eligible, reason = _check_companion_eligibility(candidate, packet)
    check("candidate missing 'person' field -> ineligible (UNVERIFIABLE_ATTRIBUTION)",
          eligible is False and reason == REASON_UNVERIFIABLE_ATTRIBUTION)


def case_too_short_rejected():
    packet = _packet()
    candidate = {"url": "https://example.org/x", "person": "A. Person", "text": "Too short."}
    eligible, reason = _check_companion_eligibility(candidate, packet)
    check("candidate text under the minimum length -> ineligible (TOO_SHORT)",
          eligible is False and reason == REASON_TOO_SHORT)


def case_duplicate_of_primary_rejected_by_hash():
    primary_text = "This exact sentence is the primary source's entire body of text for this test."
    packet = _packet(source_text=primary_text)
    candidate = {"url": "https://example.org/dup", "person": "Someone",
                 "text": primary_text}
    eligible, reason = _check_companion_eligibility(candidate, packet)
    check("candidate text identical to primary source_text -> ineligible (DUPLICATE_OF_PRIMARY, hash match)",
          eligible is False and reason == REASON_DUPLICATE_OF_PRIMARY)


def case_duplicate_of_primary_rejected_by_substring():
    primary_text = "A long primary article body with many sentences describing the situation in detail across several paragraphs of reporting."
    packet = _packet(source_text=primary_text)
    candidate = {"url": "https://example.org/dup2", "person": "Someone",
                 "text": "many sentences describing the situation in detail across several"}
    eligible, reason = _check_companion_eligibility(candidate, packet)
    check("candidate text is a substring of the primary source -> ineligible (DUPLICATE_OF_PRIMARY)",
          eligible is False and reason == REASON_DUPLICATE_OF_PRIMARY)


def case_primary_factual_authority_never_touched():
    packet = _packet()
    original_hash = packet["source_hash"]
    original_packet_hash = packet["evidence_packet_hash"]
    original_text = packet["source_text"]
    candidate = {"url": "https://example.org/y", "person": "Jamie Alt", "text": "I waited forty minutes for the lift and missed the appointment entirely."}
    _check_companion_eligibility(candidate, packet)
    check("eligibility check never mutates source_text/source_hash/evidence_packet_hash",
          packet["source_hash"] == original_hash
          and packet["evidence_packet_hash"] == original_packet_hash
          and packet["source_text"] == original_text)


# ── TestimonyL2Mixin._l2_testimony_attempt (full flow, OFF/SHADOW) ─────────

def case_off_mode_leaves_evidence_packet_completely_unchanged():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ.pop("L2_TESTIMONY_MODE", None)
        os.environ.pop("L2_COMPANION_FIXTURE", None)
        orch = _FakeOrch(tmpdir)
        packet = _packet(source_text="No testimony here at all, just facts and figures.")
        keys_before = sorted(packet.keys())
        orch._l2_testimony_attempt(packet)
        check("OFF mode (env var unset, the real default): evidence_packet key set is byte-identical",
              sorted(packet.keys()) == keys_before)
        check("OFF mode: no companion_source key was added at all",
              "companion_source" not in packet)
        db_path = Path(tmpdir) / "automation" / "engagement.db"
        check("OFF mode: no database file was even created (zero side effects)",
              not db_path.exists())


def case_shadow_testimony_not_needed_no_fixture_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["L2_TESTIMONY_MODE"] = "SHADOW"
        os.environ.pop("L2_COMPANION_FIXTURE", None)
        try:
            orch = _FakeOrch(tmpdir)
            packet = _packet(source_text='"I have used this ramp every day for a year and it has never once failed me," said Noor Haddad.')
            orch._l2_testimony_attempt(packet)
            check("SHADOW + primary already has testimony -> companion_source explicitly None",
                  packet.get("companion_source") is None)
            row = _read_l2_runs(tmpdir)
            check("SHADOW + testimony present: persisted testimony_needed=0",
                  row is not None and row[1] == 0)
        finally:
            os.environ.pop("L2_TESTIMONY_MODE", None)


def case_shadow_testimony_needed_no_fixture_configured():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["L2_TESTIMONY_MODE"] = "SHADOW"
        os.environ.pop("L2_COMPANION_FIXTURE", None)
        try:
            orch = _FakeOrch(tmpdir)
            packet = _packet(source_text="Pure statistics, zero quotes, nothing personal at all in this report.")
            orch._l2_testimony_attempt(packet)
            check("SHADOW + testimony needed + no fixture env var -> companion_source is None "
                  "(no candidate available)", packet.get("companion_source") is None)
            row = _read_l2_runs(tmpdir)
            check("SHADOW + no fixture configured: outcome_reason == NO_COMPANION_FIXTURE",
                  row is not None and row[4] == REASON_NO_COMPANION_FIXTURE)
        finally:
            os.environ.pop("L2_TESTIMONY_MODE", None)


def case_shadow_eligible_fixture_attaches_with_separate_provenance():
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "companion.json"
        fixture_path.write_text(json.dumps({
            "url": "https://example.org/testimony",
            "person": "Jamie Alt",
            "text": "I waited forty minutes for the lift and missed the appointment entirely, again, just like last month.",
            "quote": "I waited forty minutes for the lift and missed the appointment entirely.",
        }))
        os.environ["L2_TESTIMONY_MODE"] = "SHADOW"
        os.environ["L2_COMPANION_FIXTURE"] = str(fixture_path)
        try:
            orch = _FakeOrch(tmpdir)
            packet = _packet(source_text="Pure statistics, zero quotes, nothing personal at all in this report.")
            original_hash = packet["source_hash"]
            orch._l2_testimony_attempt(packet)
            companion = packet.get("companion_source")
            check("SHADOW + eligible fixture -> companion_source attached", companion is not None)
            check("companion_source carries its own separate role/provenance, distinct from primary",
                  companion is not None and companion.get("role") == "companion_testimony"
                  and companion.get("url") == "https://example.org/testimony")
            check("attaching a companion never changes the primary source_hash",
                  packet["source_hash"] == original_hash)
            row = _read_l2_runs(tmpdir)
            check("SHADOW + eligible fixture: persisted companion_attached=1, url/person recorded",
                  row is not None and row[3] == 1 and row[5] == "https://example.org/testimony"
                  and row[6] == "Jamie Alt")
        finally:
            os.environ.pop("L2_TESTIMONY_MODE", None)
            os.environ.pop("L2_COMPANION_FIXTURE", None)


def case_shadow_ineligible_fixture_not_attached():
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "companion_bad.json"
        fixture_path.write_text(json.dumps({"url": "https://example.org/x", "text": "too short"}))
        os.environ["L2_TESTIMONY_MODE"] = "SHADOW"
        os.environ["L2_COMPANION_FIXTURE"] = str(fixture_path)
        try:
            orch = _FakeOrch(tmpdir)
            packet = _packet(source_text="Pure statistics, zero quotes, nothing personal at all in this report.")
            orch._l2_testimony_attempt(packet)
            check("SHADOW + ineligible fixture (no person, too short) -> companion_source stays None",
                  packet.get("companion_source") is None)
        finally:
            os.environ.pop("L2_TESTIMONY_MODE", None)
            os.environ.pop("L2_COMPANION_FIXTURE", None)


def case_never_raises_on_garbage_fixture():
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "garbage.json"
        fixture_path.write_text("{not valid json::")
        os.environ["L2_TESTIMONY_MODE"] = "SHADOW"
        os.environ["L2_COMPANION_FIXTURE"] = str(fixture_path)
        try:
            orch = _FakeOrch(tmpdir)
            packet = _packet(source_text="Pure statistics, zero quotes, nothing personal at all in this report.")
            try:
                orch._l2_testimony_attempt(packet)
                raised = False
            except Exception:
                raised = True
            check("malformed JSON fixture never raises out of _l2_testimony_attempt", raised is False)
            check("malformed fixture: companion_source stays None", packet.get("companion_source") is None)
        finally:
            os.environ.pop("L2_TESTIMONY_MODE", None)
            os.environ.pop("L2_COMPANION_FIXTURE", None)


if __name__ == "__main__":
    case_primary_already_has_testimony()
    case_primary_lacks_testimony()
    case_third_person_quote_is_not_testimony()
    case_no_source_text()
    case_eligible_candidate_attaches()
    case_missing_fields_rejected()
    case_unverifiable_attribution_rejected()
    case_too_short_rejected()
    case_duplicate_of_primary_rejected_by_hash()
    case_duplicate_of_primary_rejected_by_substring()
    case_primary_factual_authority_never_touched()
    case_off_mode_leaves_evidence_packet_completely_unchanged()
    case_shadow_testimony_not_needed_no_fixture_read()
    case_shadow_testimony_needed_no_fixture_configured()
    case_shadow_eligible_fixture_attaches_with_separate_provenance()
    case_shadow_ineligible_fixture_not_attached()
    case_never_raises_on_garbage_fixture()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
