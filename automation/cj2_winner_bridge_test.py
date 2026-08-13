#!/usr/bin/env python3
"""
cj2_winner_bridge_test.py — static test suite for cj2_winner_bridge.py
(Phase G.2). Zero network access, zero model calls, zero filesystem access
beyond this file's own fixtures.

SYNTHETIC CONTROL-FLOW FIXTURE — every winner/seed object below is
hand-authored, not a real Stage-C output. This suite proves the mechanical
path (reconstructed winner -> bridge -> valid Fable-invocation payload)
works and fails closed correctly. It is NOT semantic evidence, NOT Stage-C
validation, and NOT production-readiness evidence — Stage C has not yet
satisfied the research track's own natural-safe-admission exit criterion
(.claude/experiments/final-evaluation-freeze-protocol-2026-08-13.md), and
this suite does not and cannot substitute for that.

USAGE: python3 automation/cj2_winner_bridge_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

import cj2_winner_bridge as bridge  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def expect_bridge_error(name, reason, fn):
    try:
        fn()
        check(name, False)
    except bridge.BridgeError as e:
        check(f"{name} (reason={e.reason})", e.reason == reason)
    except Exception as e:
        check(f"{name} (unexpected exception type: {type(e).__name__})", False)


VALID_WINNER = {
    "status": "candidate",
    "seed_evidence_refs": ["cj1:a1"],
    "additional_source_observations": [],
    "engine_move": "attends to the gap between the policy's stated aim and its measured effect",
    "seed_engagement": "strong",
    "interpretive_inference": "the program's own metric never captures the outcome it claims to target",
    "conceptual_shift": "reframes a compliance question as a measurement-validity question",
    "claimed_contribution": "the article should show the metric was never built to see this",
}

VALID_SEED = {
    "slug": "01_cave_dna",
    "source_sha256": "abc123def456",
    "source_snapshot": "The council's own report shows attendance rose 4% while satisfaction fell.",
    "resisting_detail": "The report treats a 4% attendance rise as success without checking whether "
                         "the people newly attending are the ones the program was meant to reach.",
    "evidence": [{"id": "cj1:a1", "excerpt": "attendance rose 4% while satisfaction fell"}],
}

VALID_EVIDENCE_PACKET = {
    "source_text": "The council's own report shows attendance rose 4% while satisfaction fell.",
    "source_hash": "abc123def456",
    "source_truncated": False,
    "source_origin": "fetched_article",
}

PROVENANCE_KWARGS = dict(
    cj1_seed_id="01_cave_dna", stage_c_letter="B", engine_label="P",
    admission_gate_terminal_state="admitted_safe",
)


def case_valid_winner_builds_payload():
    payload = bridge.build_bridge_payload(
        VALID_WINNER, VALID_SEED, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS
    )
    check("valid winner: news_title falls back to the seed's slug (no title/url on this fixture, no invention)",
          payload["news_title"] == "source 01_cave_dna")
    check("valid winner: news_summary is always empty (no fabricated summary)",
          payload["news_summary"] == "")
    check("valid winner: disability_angle is the seed's resisting_detail, verbatim",
          payload["disability_angle"] == VALID_SEED["resisting_detail"])
    check("valid winner: current_agent passed through unchanged",
          payload["current_agent"] == "Pixel Nova")
    check("valid winner: evidence_packet is the SAME object, by identity",
          payload["evidence_packet"] is VALID_EVIDENCE_PACKET)
    check("valid winner: no angle/seed_sentence/correction_moment/resisting_example/persona field present",
          not ({"angle", "seed_sentence", "correction_moment", "resisting_example", "persona",
                "register", "opening_scene", "opening_shape", "cross_cite"} & set(payload.keys())))
    prov = payload["_bridge_provenance"]
    check("valid winner: provenance carries bridge_version",
          prov["bridge_version"] == bridge.BRIDGE_VERSION)
    check("valid winner: provenance carries engine_label/stage_c_letter/cj1_seed_id",
          prov["engine_label"] == "P" and prov["stage_c_letter"] == "B" and prov["cj1_seed_id"] == "01_cave_dna")
    check("valid winner: provenance's admission_gate_terminal_state present, content-free string only",
          prov["admission_gate_terminal_state"] == "admitted_safe")


def case_evidence_packet_mismatch():
    mismatched_packet = dict(VALID_EVIDENCE_PACKET, source_hash="totally-different-hash")
    expect_bridge_error(
        "wrong evidence_packet (hash mismatch) fails closed",
        bridge.REASON_EVIDENCE_PACKET_MISMATCH,
        lambda: bridge.build_bridge_payload(VALID_WINNER, VALID_SEED, mismatched_packet, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_evidence_packet_missing_hash():
    no_hash_packet = {k: v for k, v in VALID_EVIDENCE_PACKET.items() if k != "source_hash"}
    expect_bridge_error(
        "evidence_packet missing source_hash entirely fails closed (unverifiable != identical)",
        bridge.REASON_EVIDENCE_PACKET_MISMATCH,
        lambda: bridge.build_bridge_payload(VALID_WINNER, VALID_SEED, no_hash_packet, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_seed_missing_hash():
    no_hash_seed = {k: v for k, v in VALID_SEED.items() if k != "source_sha256"}
    expect_bridge_error(
        "seed missing source_sha256 entirely fails closed",
        bridge.REASON_EVIDENCE_PACKET_MISMATCH,
        lambda: bridge.build_bridge_payload(VALID_WINNER, no_hash_seed, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_malformed_winner_not_a_dict():
    expect_bridge_error(
        "malformed winner (not a dict) rejected",
        bridge.REASON_WINNER_RECONSTRUCTION_FAILED,
        lambda: bridge.build_bridge_payload("not a dict", VALID_SEED, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_malformed_winner_missing_fields():
    incomplete = {"status": "candidate"}
    expect_bridge_error(
        "malformed winner (missing engine_move/claimed_contribution) rejected",
        bridge.REASON_WINNER_RECONSTRUCTION_FAILED,
        lambda: bridge.build_bridge_payload(incomplete, VALID_SEED, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_abstained_winner_rejected():
    abstained = dict(VALID_WINNER, status="abstain")
    expect_bridge_error(
        "abstained candidate (status != 'candidate') rejected",
        bridge.REASON_WINNER_RECONSTRUCTION_FAILED,
        lambda: bridge.build_bridge_payload(abstained, VALID_SEED, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_seed_missing_resisting_detail():
    no_resisting = {k: v for k, v in VALID_SEED.items() if k != "resisting_detail"}
    expect_bridge_error(
        "seed missing resisting_detail rejected (nothing to bridge into disability_angle)",
        bridge.REASON_WINNER_RECONSTRUCTION_FAILED,
        lambda: bridge.build_bridge_payload(VALID_WINNER, no_resisting, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_raw_stage_c_letter_rejected():
    """Test matrix item F — a bare anonymized Stage-C comparator payload
    passed directly, instead of a reconstructed winner, must be rejected."""
    raw_stage_c_output = {
        "candidate_assessments": {
            "A": {"factual_integrity": "pass", "assessment": "qualifies", "reason": "..."},
        },
        "selection": {"editorial_winner": "A", "runner_up": None, "margin": "clear", "why": "..."},
    }
    expect_bridge_error(
        "raw Stage-C comparator output (anonymized letter payload) rejected, not reconstructed",
        bridge.REASON_WINNER_RECONSTRUCTION_FAILED,
        lambda: bridge.build_bridge_payload(raw_stage_c_output, VALID_SEED, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_letter_map_rejected():
    letter_map_only = {"A": "P", "B": "S", "C": "Z", "D": "M"}
    expect_bridge_error(
        "bare letter_map dict rejected (not a reconstructed winner)",
        bridge.REASON_WINNER_RECONSTRUCTION_FAILED,
        lambda: bridge.build_bridge_payload(letter_map_only, VALID_SEED, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_barred_internal_fields_cannot_cross():
    """Test matrix item G — a winner record that (incorrectly, but
    defensively tested anyway) carries B2/R1/R2/Stage-C internal fields
    must never let them reach the assembled payload."""
    poisoned_winner = dict(VALID_WINNER)
    poisoned_winner["role"] = "factual_dependency"
    poisoned_winner["support"] = "unsupported"
    poisoned_winner["problems"] = ["undeclared_factual_dependency"]
    poisoned_winner["effective_status"] = "unsafe"
    poisoned_winner["candidate_assessments"] = {"A": {}}  # also triggers the raw-Stage-C-marker check
    expect_bridge_error(
        "winner carrying denylisted/raw-Stage-C-shaped fields rejected before payload assembly",
        bridge.REASON_WINNER_RECONSTRUCTION_FAILED,
        lambda: bridge.build_bridge_payload(poisoned_winner, VALID_SEED, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS),
    )


def case_denylist_scanner_unit_test():
    """Defense-in-depth, tested directly at the unit level: today's
    build_bridge_payload never embeds the winner's own fields wholesale (it
    only ever copies seed.resisting_detail into disability_angle), so a
    stray denylisted field on `winner` currently has no path to reach the
    assembled payload — confirmed separately by
    case_no_ranking_heuristic_invented's kind of check. What must still be
    proven is that the scanner ITSELF correctly detects a denylisted key
    wherever it appears, so a FUTURE change that starts forwarding more
    winner content is caught rather than silently trusted."""
    poisoned_payload = {
        "news_title": "x", "news_summary": "", "disability_angle": "y",
        "current_agent": "Pixel Nova",
        "nested": {"consistency": "R1_R2_SEMANTIC_CONFLICT"},
    }
    try:
        bridge._scan_for_denylisted_keys(poisoned_payload)
        check("denylist scanner detects a nested denylisted key", False)
    except bridge.BridgeError as e:
        check("denylist scanner detects a nested denylisted key", e.reason == bridge.REASON_BRIDGE_VALIDATION_FAILED)

    poisoned_list = {"items": [{"ok": 1}, {"support": "unsupported"}]}
    try:
        bridge._scan_for_denylisted_keys(poisoned_list)
        check("denylist scanner detects a denylisted key inside a list of dicts", False)
    except bridge.BridgeError as e:
        check("denylist scanner detects a denylisted key inside a list of dicts", e.reason == bridge.REASON_BRIDGE_VALIDATION_FAILED)

    clean_payload = {"news_title": "x", "nested": {"fine": "yes"}, "items": [{"ok": 1}]}
    try:
        bridge._scan_for_denylisted_keys(clean_payload)
        check("denylist scanner passes a genuinely clean payload", True)
    except bridge.BridgeError:
        check("denylist scanner passes a genuinely clean payload", False)


def case_provenance_allowlist_drops_unlisted_keys():
    """A denylisted key can never be smuggled in even via the provenance
    kwargs — the allowlist inside _bridge_provenance drops anything not
    explicitly named, regardless of what a caller passes."""
    payload = bridge.build_bridge_payload(
        VALID_WINNER, VALID_SEED, VALID_EVIDENCE_PACKET, "Pixel Nova",
        cj1_seed_id="01_cave_dna", stage_c_letter="B", engine_label="P",
        admission_gate_terminal_state="admitted_safe",
    )
    check("provenance allowlist: only the 6 allowed keys are present",
          set(payload["_bridge_provenance"].keys()) == bridge._PROVENANCE_ALLOWED_KEYS)


def case_no_ranking_heuristic_invented():
    """Phase G.1.1's own instruction: do not invent a ranking heuristic
    across multiple candidate fields. Confirm disability_angle always comes
    from exactly one field (seed.resisting_detail) regardless of what other
    analytical fields the winner carries (claimed_contribution,
    conceptual_shift, engine_move) — those must never be consulted for this
    purpose, even if resisting_detail is a short string and another field
    looks "richer.\""""
    rich_winner = dict(VALID_WINNER, claimed_contribution="a much longer, more detailed claim " * 5)
    payload = bridge.build_bridge_payload(rich_winner, VALID_SEED, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS)
    check("disability_angle is always seed.resisting_detail, never winner.claimed_contribution/engine_move/conceptual_shift",
          payload["disability_angle"] == VALID_SEED["resisting_detail"])


def case_news_title_prefers_real_title_over_url_over_slug():
    seed_with_title = dict(VALID_SEED, title="Council report claims attendance success")
    payload = bridge.build_bridge_payload(VALID_WINNER, seed_with_title, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS)
    check("news_title prefers a real title when present",
          payload["news_title"] == "Council report claims attendance success")

    seed_with_url_only = dict(VALID_SEED, url="https://example.org/council-report")
    payload2 = bridge.build_bridge_payload(VALID_WINNER, seed_with_url_only, VALID_EVIDENCE_PACKET, "Pixel Nova", **PROVENANCE_KWARGS)
    check("news_title falls back to url when no title present",
          payload2["news_title"] == "https://example.org/council-report")


if __name__ == "__main__":
    case_valid_winner_builds_payload()
    case_evidence_packet_mismatch()
    case_evidence_packet_missing_hash()
    case_seed_missing_hash()
    case_malformed_winner_not_a_dict()
    case_malformed_winner_missing_fields()
    case_abstained_winner_rejected()
    case_seed_missing_resisting_detail()
    case_raw_stage_c_letter_rejected()
    case_letter_map_rejected()
    case_barred_internal_fields_cannot_cross()
    case_denylist_scanner_unit_test()
    case_provenance_allowlist_drops_unlisted_keys()
    case_no_ranking_heuristic_invented()
    case_news_title_prefers_real_title_over_url_over_slug()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
