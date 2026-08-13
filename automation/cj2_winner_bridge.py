#!/usr/bin/env python3
"""
cj2_winner_bridge.py — cj2_winner_bridge_v1, Phase G.2.

Deterministic, minimal transport from a reconstructed CJ-2 Stage-C winner to
the exact input shape `orchestrator/llm.py`'s `_fable_editorial_brief` already
accepts (news_title, news_summary, disability_angle, current_agent,
evidence_packet). Per Phase G.1.1 (`.claude/master-roadmap-2026-08-13.md`,
`## PHASE G.1.1`): `angle`, `seed_sentence`, `correction_moment`,
`resisting_example`, `persona`, `register`, `opening_scene`, `opening_shape`,
`cross_cite` are all Fable-OUTPUT fields, never inputs — this module does not
produce any of them, and never will under the v1 contract. Producing any of
them here would be exactly the concealed-editorial-decision failure Phase
G.1.1 exists to prevent.

This module performs ONLY:
  A. deterministic structural transport (evidence_packet passed by reference,
     current_agent passed through, provenance fields copied verbatim)
  B. deterministic formatting (news_title/news_summary fallback chains, no
     new facts introduced)
  DIRECT carry-over into one existing, already-permissive, already-unchecked
     input slot (disability_angle <- the winner's own resisting_detail,
     verbatim, no ranking heuristic — there is exactly one candidate field,
     per Phase G.1.1's own instruction not to invent a ranking heuristic that
     doesn't already exist in the CJ-2 design)

It performs NO semantic/editorial composition. If a future caller needs
something this module cannot produce without inventing content, that is a
contract mismatch (raise BridgeError, do not compose around it).

Zero model calls. Zero network access. Zero filesystem access beyond what a
caller explicitly hands in.
"""
from __future__ import annotations

BRIDGE_VERSION = "cj2_winner_bridge_v1"

# ---------------------------------------------------------------------------
# Structured failure reasons (Phase G.2 instruction 12) — bridge-level only.
# Orchestration-level reasons (NO_CJ2_WINNER, CJ2_SHADOW_UNAVAILABLE) live in
# orchestrator/cj2_shadow.py, which is the caller, not this module.
# ---------------------------------------------------------------------------
REASON_WINNER_RECONSTRUCTION_FAILED = "WINNER_RECONSTRUCTION_FAILED"
REASON_EVIDENCE_PACKET_MISMATCH = "EVIDENCE_PACKET_MISMATCH"
REASON_BRIDGE_VALIDATION_FAILED = "BRIDGE_VALIDATION_FAILED"


class BridgeError(Exception):
    """Raised for any structural failure. `.reason` is always one of the
    REASON_* constants above — callers should branch on `.reason`, not on
    the message text."""

    def __init__(self, reason: str, message: str):
        super().__init__(f"{reason}: {message}")
        self.reason = reason


# ---------------------------------------------------------------------------
# Denylist — instruction 11 + Phase G.1/G.1.1's own barred-field lists.
# Applied to the ENTIRE payload except `_bridge_provenance`, which has its
# own separate, explicit allowlist (stricter: only listed keys survive,
# everything else in that sub-dict is dropped, not merely flagged).
# ---------------------------------------------------------------------------
_DENYLISTED_KEYS = frozenset({
    # R1
    "role", "empirical_dependency", "world_truth_question", "concrete_restatement",
    # R2 / support / declaration
    "support", "declaration", "problems", "causality_hardening",
    "mechanism_invention", "modality_hardening",
    # consistency / conflict / B2 terminal state
    "consistency", "r1_r2_semantic_conflict", "effective_status", "effective_verdict",
    "per_claim",
    # admission gate (terminal_state/routing/enter_stage_c/repair_occurred) —
    # terminal_state is allowed ONLY inside _bridge_provenance's own allowlist
    "terminal_state", "routing", "enter_stage_c", "repair_occurred",
    # Stage C comparator / anonymization
    "candidate_assessments", "selection", "editorial_winner", "runner_up",
    "margin", "factual_integrity", "engine_dependence", "conceptual_movement",
    "distinctive_contribution", "assessment", "letter_map",
    # Reader Lab / calibration
    "dataset_purpose", "calibration_candidates", "reviewer_id",
    "machine_comparison", "role_alignment", "support_alignment",
    "overall_relation", "dataset_disposition", "disposition",
})

# Explicit allowlist for `_bridge_provenance` — everything else in that
# sub-dict is dropped, not merely flagged, since it is the one place a raw
# admission-gate `terminal_state` string is legitimately allowed to travel
# (per Phase G's own note: that string is documented as containing "no claim
# content, no source text" — operational metadata only, never prompt text).
_PROVENANCE_ALLOWED_KEYS = frozenset({
    "bridge_version", "cj1_seed_id", "stage_c_letter", "engine_label",
    "admission_gate_terminal_state", "source_hash",
})

# Keys that, if present on the `winner` argument, indicate a caller passed
# raw Stage-C comparator output (or its letter_map) instead of a
# reconstructed Stage-A winner record — instruction 10 / test matrix item F.
_STAGE_C_RAW_MARKERS = frozenset({
    "candidate_assessments", "selection", "editorial_winner", "letter_map",
})

# Minimum shape a reconstructed Stage-A winner record must have to be
# considered structurally valid (per the exact schema recovered in Phase G /
# G.1: status, engine_move, claimed_contribution, etc.).
_REQUIRED_WINNER_KEYS = frozenset({"status", "engine_move", "claimed_contribution"})


def _scan_for_denylisted_keys(obj, _path="payload"):
    """Recursively walk obj (dicts/lists only — this payload has no other
    nested container types), raise BRIDGE_VALIDATION_FAILED on the first
    denylisted key found anywhere. Case-insensitive on key names."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str) and key.lower() in _DENYLISTED_KEYS:
                raise BridgeError(
                    REASON_BRIDGE_VALIDATION_FAILED,
                    f"denylisted internal field '{key}' present at {_path}.{key} — refusing to build payload",
                )
            _scan_for_denylisted_keys(value, f"{_path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _scan_for_denylisted_keys(item, f"{_path}[{i}]")


def _sanitize_provenance(raw_provenance: dict) -> dict:
    """Drop any key not in _PROVENANCE_ALLOWED_KEYS — allowlist, not
    denylist, for this one sub-dict specifically, since it's the sole
    intentional exception to "nothing internal crosses the bridge"."""
    return {k: v for k, v in raw_provenance.items() if k in _PROVENANCE_ALLOWED_KEYS}


def _reject_if_raw_stage_c_output(winner) -> None:
    if not isinstance(winner, dict):
        raise BridgeError(REASON_WINNER_RECONSTRUCTION_FAILED, "winner is not a dict")
    hit = _STAGE_C_RAW_MARKERS & set(winner.keys())
    if hit:
        raise BridgeError(
            REASON_WINNER_RECONSTRUCTION_FAILED,
            f"received raw Stage-C/anonymization output ({sorted(hit)}), not a reconstructed "
            f"Stage-A winner record — reconstruct via the letter_map lookup first",
        )


def _validate_winner_shape(winner: dict) -> None:
    missing = _REQUIRED_WINNER_KEYS - set(winner.keys())
    if missing:
        raise BridgeError(
            REASON_WINNER_RECONSTRUCTION_FAILED,
            f"reconstructed winner missing required field(s): {sorted(missing)}",
        )
    if winner.get("status") != "candidate":
        raise BridgeError(
            REASON_WINNER_RECONSTRUCTION_FAILED,
            f"reconstructed winner status is {winner.get('status')!r}, not 'candidate' — "
            f"an abstained record cannot be bridged",
        )


def _validate_seed_shape(seed: dict) -> None:
    if not isinstance(seed, dict):
        raise BridgeError(REASON_WINNER_RECONSTRUCTION_FAILED, "seed is not a dict")
    if not seed.get("resisting_detail"):
        raise BridgeError(
            REASON_WINNER_RECONSTRUCTION_FAILED,
            "seed has no resisting_detail — this is the only field this bridge version "
            "carries into disability_angle; without it there is nothing to bridge",
        )


def _check_evidence_packet_identity(seed: dict, evidence_packet: dict) -> None:
    """Hard invariant (Phase G.1.7 / G.1.1's EVIDENCE_PACKET INVARIANT): the
    bridge may only produce a valid payload when the seed's own recorded
    source hash matches the SAME canonical evidence_packet generate.py
    already built for this run. Absence of a verifiable hash on either side
    is treated as a mismatch, not silently passed — this is deliberately
    conservative: an unverifiable claim of identity is not identity."""
    seed_hash = seed.get("source_sha256")
    packet_hash = evidence_packet.get("source_hash") if isinstance(evidence_packet, dict) else None
    if not seed_hash or not packet_hash:
        raise BridgeError(
            REASON_EVIDENCE_PACKET_MISMATCH,
            "cannot verify source identity — seed.source_sha256 or "
            "evidence_packet.source_hash missing; refusing to trust an unverifiable match",
        )
    if seed_hash != packet_hash:
        raise BridgeError(
            REASON_EVIDENCE_PACKET_MISMATCH,
            "seed.source_sha256 does not match this run's evidence_packet.source_hash — "
            "the winner was computed against a different source fetch than the one "
            "generate.py is using for this run; refusing to establish a second "
            "provenance universe",
        )


def _deterministic_news_title(seed: dict) -> str:
    """DETERMINISTIC FORMAT — fallback chain, no new facts. Prefers a real
    title/url the seed's underlying source actually carries; falls back to
    the seed's own content-free slug identifier rather than inventing prose.
    Never reads winner-level analytical fields (engine_move,
    claimed_contribution, etc.) — those are candidate-specific judgments,
    not source metadata, and using them here would misrepresent them as if
    they were the news item itself."""
    return seed.get("title") or seed.get("url") or f"source {seed.get('slug', 'unknown')}"


def build_bridge_payload(
    winner: dict,
    seed: dict,
    evidence_packet: dict,
    current_agent: str,
    *,
    cj1_seed_id: str,
    stage_c_letter: str,
    engine_label: str,
    admission_gate_terminal_state: str,
) -> dict:
    """The one entry point. Returns a payload structurally suitable for the
    existing `_fable_editorial_brief(news_title, news_summary,
    disability_angle, current_agent, evidence_packet)` call — same 5
    arguments, nothing more. Raises BridgeError (see REASON_* constants) on
    any structural problem. Never returns a partially-valid payload."""
    _reject_if_raw_stage_c_output(winner)
    _validate_winner_shape(winner)
    _validate_seed_shape(seed)
    _check_evidence_packet_identity(seed, evidence_packet)

    payload = {
        "news_title": _deterministic_news_title(seed),
        # DETERMINISTIC, always empty: no clean single summary field exists
        # anywhere in the CJ-1/Stage-A/Stage-C schema (verified across Phase
        # G/G.1's own field-level schema map) — composing one from analytical
        # fields would be semantic composition, not formatting. Empty string
        # is an already-exercised, accepted value for this field in the live
        # pipeline itself (news_seed absent -> _ns_summary = "").
        "news_summary": "",
        # DIRECT — the one field Phase G.1.1 concluded carries real weight:
        # verbatim carry-over into an existing "inspiration only, never
        # validated as evidence" input slot, the same functional role the
        # live pipeline's own news_seed.disability_angle already plays.
        "disability_angle": seed["resisting_detail"],
        "current_agent": current_agent,
        # SAME OBJECT, by reference — never a copy, never rebuilt. This is
        # what makes the evidence_packet invariant meaningful downstream:
        # generate.py's own validate_brief() call will stamp/compare hashes
        # against this exact object.
        "evidence_packet": evidence_packet,
        "_bridge_provenance": _sanitize_provenance({
            "bridge_version": BRIDGE_VERSION,
            "cj1_seed_id": cj1_seed_id,
            "stage_c_letter": stage_c_letter,
            "engine_label": engine_label,
            "admission_gate_terminal_state": admission_gate_terminal_state,
            "source_hash": evidence_packet.get("source_hash") if isinstance(evidence_packet, dict) else None,
        }),
    }

    # Defense in depth — even though nothing above reads a denylisted field,
    # scan the assembled payload before returning it. A future edit to this
    # function that accidentally forwards a raw winner/seed sub-object wholesale
    # would be caught here rather than silently reaching Fable's prompt.
    _scan_for_denylisted_keys({k: v for k, v in payload.items() if k != "evidence_packet"})

    return payload
