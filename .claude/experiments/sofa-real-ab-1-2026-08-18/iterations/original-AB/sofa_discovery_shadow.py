"""
sofa_discovery_shadow.py — Sofa Architecture V1 Shadow Slice 1 (+ Slice 1.1
epistemic-boundary fix and post-writer grounding audit).

SHADOW ONLY. Nothing in this module is imported by generate.py, llm.py,
gate.py, review.py, publish.py, or production_orchestrator.py, and nothing
here is called by the live 09:00 pipeline. See .claude/experiments/
sofa-shadow-slice-1-results-2026-08-18.md and sofa-shadow-slice-1-1-results-
2026-08-18.md for what was actually run with this module and what was
explicitly skipped for lack of clean local test material.

WHAT THIS IMPLEMENTS: the smallest slice of Architecture B (.claude/
experiments/sofa-architecture-v1-proposal-2026-08-18.md) — a post-commission
Discovery step that takes an EXISTING, ALREADY-VALIDATED Fable Layer 1
commission (source_decision == "commission") and produces a small,
explicitly-epistemically-typed Discovery Packet, plus a writer-context
projection that a generic (non-persona) prose writer can consume, PLUS
(Slice 1.1) a post-writer grounding audit — because Slice 1 found that a
grounded packet does not guarantee a grounded article.

EPISTEMIC CORRECTION (per the task that created this module — do not lose
this on future edits): `hidden_mechanism` is NOT source fact. It is
VALIDATED EDITORIAL INTERPRETATION, already semantically-entailment-checked
against the source anchor by `_verify_commission_mechanism_support` in
llm.py before this module ever sees it. This module never re-labels it as
fact, never asks the writer to treat it as a fact "the article must not
contradict," and never regenerates it — it is inherited, verbatim, from the
commission brief. Evidence and interpretation stay structurally separate
here exactly the way grounding.py already keeps evidence_candidate and
interpretation separate: two fields, never merged into one.

SLICE 1.1 CORRECTION (do not lose this either): Slice 1's supporting_evidence
/ carrying_material items wrapped {kind, source_excerpt, note} inside ONE
EVIDENCE envelope — which let editorial interpretation ("the written rule
that does the actual work of hiding the units") hide inside a field typed
as if it were pure source fact. Fixed: each item now carries source_excerpt
(EVIDENCE, substring-checked) and editorial_note (EDITORIAL_GUIDANCE or
EDITORIAL_INTERPRETATION, chosen by the caller, never EVIDENCE) as two
separate typed sub-fields. known_gaps items are now typed GROUNDING_BOUNDARY
(a hard boundary statement, neither fact nor interpretation) instead of
EVIDENCE. Slice 1.1 also found that a grounded Discovery Packet does NOT
guarantee a grounded finished article — the SYNTH-1 shadow article
introduced unsupported causal/motive/certainty claims ("its hold cannot
legally outlast forty-five days", "Nobody... was lying") that no packet-
level check could have caught, because they are properties of the WRITER'S
OUTPUT, not the packet. `run_shadow_grounding_audit` below audits the
article text itself, after the fact, against the source and packet.

WHAT THIS MODULE DOES NOT DO (all deliberate, all matching the task's
explicit boundaries):
  - does not call, patch, wire, or import Story Rejection V1.1, gate.py,
    review.py, or the live writer prompt in generate.py
  - does not regenerate hidden_mechanism / source_anchor_examined /
    why_disability_knowledge_changes_subject — those are read-only inputs
  - does not run competitive multi-lens discovery (Architecture C) — one
    lens, one mechanism, inherited from one existing commission
  - does not enable CJ-2
  - does not touch source selection (news_fetcher.py) or Story Rejection
  - does not weaken validate_brief / build_evidence_packet in any way —
    it calls the real ones, unmodified, and fails closed if a grounding
    claim can't be verified against the real source text
  - does not automatically rewrite an article the grounding audit flags —
    Slice 1.1 is diagnosis only, per its own explicit instruction

Pure functions only where possible (no `self`, testable without
instantiating ProductionOrchestrator), matching grounding.py's and
config.py's existing convention. The functions that need to call a model
(`run_shadow_discovery`, `run_shadow_writer`, `run_shadow_grounding_audit`)
take an injected `llm_call(system_prompt, user_prompt) -> str` callable
rather than reaching for a network client directly, so tests can supply a
deterministic stub and the real CLIProxy/OpenRouter call can be wired in
later without touching this module's logic.
"""
from __future__ import annotations

import json as _json
from datetime import datetime as _dt

from .grounding import build_evidence_packet as _build_evidence_packet  # re-export, unmodified
from .grounding import scan_free_prose_field as _scan_free_prose_field  # reused, not duplicated

SCHEMA_VERSION = "sofa-shadow-1"

# --------------------------------------------------------------------------- #
# Epistemic types — every field in a Discovery Packet must be one of these.
# "At minimum EVIDENCE / EDITORIAL_INTERPRETATION / EDITORIAL_GUIDANCE" per
# the task; EDITORIAL_METADATA is added for fields that are neither a
# factual claim, an interpretive claim, nor guidance about how to write —
# just bookkeeping about who/what produced the discovery (lens name,
# byline). Keeping it separate stops "which persona noticed this" from
# being mistaken for either a fact or a writing instruction.
# --------------------------------------------------------------------------- #
EVIDENCE = "EVIDENCE"
EDITORIAL_INTERPRETATION = "EDITORIAL_INTERPRETATION"
EDITORIAL_GUIDANCE = "EDITORIAL_GUIDANCE"
EDITORIAL_METADATA = "EDITORIAL_METADATA"
# Added in Shadow Slice 1.1: a statement of what the supplied evidence does
# NOT authorize the article to claim. Neither a fact (it asserts an absence,
# not a presence) nor ordinary interpretation/guidance about how to write —
# a hard editorial boundary. known_gaps items are the only field typed this
# way. See sofa-shadow-slice-1-1-results-2026-08-18.md §2.
GROUNDING_BOUNDARY = "GROUNDING_BOUNDARY"

VALID_EPISTEMIC_TYPES = frozenset(
    {EVIDENCE, EDITORIAL_INTERPRETATION, EDITORIAL_GUIDANCE, EDITORIAL_METADATA, GROUNDING_BOUNDARY}
)

# 0B (Real Article Test 1): the explicit, honest default for discovery_lens
# when nothing in this non-competitive slice's data actually records which
# lens produced the winning mechanism. Never silently replaced with the
# byline persona's name.
DISCOVERY_LENS_UNATTRIBUTED = "all_lenses_unattributed"

# The two types an editorial_note on a supporting_evidence/carrying_material
# item may carry. Never EVIDENCE (a note is never itself a source fact, even
# when it describes one) and never GROUNDING_BOUNDARY (that type is reserved
# for known_gaps) — see Shadow Slice 1.1 Problem 1.
_MATERIAL_NOTE_TYPES = frozenset({EDITORIAL_GUIDANCE, EDITORIAL_INTERPRETATION})

# Carrying/supporting-material item kinds. Illustrative, not closed — matches
# canonical Sofa §7's own "do not require any particular type" instruction.
# Kept here only so the schema validator can sanity-check the field exists
# and is a non-empty string, not to enforce a closed taxonomy.
_MATERIAL_KIND_HINT = (
    "sequence", "document", "physical_action", "person_action", "measurement",
    "object", "contradiction", "quote", "unresolved_absence",
)

# Fields the writer must NEVER see, even indirectly, because they are
# reasoning ADDRESSED TO THE COMMISSION GATE, not material for an article.
# This is the single most important exclusion list in this module — see
# `to_writer_context` below and canonical Sofa §2/§4/§10.
_INTERNAL_ONLY_COMMISSION_FIELDS = frozenset({
    "why_disability_knowledge_changes_subject",
    "eligible_execution_possible",
    "blocked_carry_persona",
    "dominant_framing",
    "why_disability_knowledge_does_not_change_subject",
    "reason",
})

# Persona-roleplay fields that must never reach the shadow writer prompt,
# under any KEY name, even if a caller accidentally attaches them to a
# commission_brief or writer_context dict. `to_writer_context` recursively
# inspects dictionary KEYS ONLY for these (see `_find_banned_keys` below) —
# NOT a substring scan of serialized values. `assert_no_persona_leakage`
# separately scans assembled prompt TEXT, but only for the distinctive
# boilerplate phrases below, never for these bare key-like words.
#
# REAL ARTICLE TEST 1 CORRECTION (0A): the original Slice 1/1.1 version of
# this module serialized the whole writer-context dict to JSON and did a
# plain substring search for these words. That produces false positives on
# ordinary prose: real source material or a real article can legitimately
# contain "the reason", "the artistic canon", "a wound", "her mood" — none
# of which are persona-roleplay leakage. The fix: for STRUCTURED DATA, only
# a literal dictionary KEY matching one of these names is a violation; the
# same words appearing inside a string VALUE (an excerpt, a note, an
# article sentence) are not inspected at all. For RAW PROMPT TEXT (already
# correct in Slice 1/1.1 and unchanged here), only the specific boilerplate
# PHRASES below are checked — never these bare words.
_PERSONA_ROLEPLAY_KEYS = frozenset({
    "prompt_block", "wound", "mood", "persona_state", "obsessions",
    "authorized_personal_history", "persona_canon", "canon",
})
_PERSONA_ROLEPLAY_PHRASES = (
    "WRITE LIKE THIS PERSON",
    "YOUR WOUND",
    "AUTHORIZED PERSONAL HISTORY",
    "You are a disabled person",
    "This article is written BY a disabled person",
    "You are the author",
)


def _find_banned_keys(obj, banned_keys, _path=""):
    """Recursively walk a nested dict/list structure and return a list of
    "path: key" strings for every dictionary KEY that matches one of
    `banned_keys` — never inspects string VALUES, so ordinary prose or
    source excerpts containing the same word as a banned key (e.g. a
    source sentence using "wound" or "canon") never trips this check. Only
    an actual key name is a violation."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{_path}.{k}" if _path else str(k)
            if k in banned_keys:
                hits.append(here)
            hits.extend(_find_banned_keys(v, banned_keys, here))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            hits.extend(_find_banned_keys(item, banned_keys, f"{_path}[{i}]"))
    return hits


class SofaShadowError(Exception):
    """Fail-closed error for this module. Raised, never swallowed, whenever
    a packet/commission/writer-context is malformed, ungrounded, or
    attempts to smuggle persona-roleplay material into the writer path.
    Mirrors the rest of this codebase's fail-closed convention (Story
    Rejection returns defer/None rather than guessing) — this module raises
    instead of returning None, because it has no "publish anyway" fallback
    to protect: a shadow packet that can't be trusted should not be usable
    by anything downstream, including a shadow writer."""


def _field(value, epistemic_type, note=None):
    """Wrap a value with its explicit epistemic type. This is the one
    representation every Discovery Packet field uses — a bare string or
    list is never allowed to sit in a packet without a declared type,
    because that is exactly how the current production writer prompt loses
    track of which of its ~26 variables are fact and which are interpretation
    (sofa-pipeline-audit-current-runtime-2026-08-18.md §3b/§4)."""
    if epistemic_type not in VALID_EPISTEMIC_TYPES:
        raise SofaShadowError(
            f"unknown epistemic_type {epistemic_type!r} — must be one of {sorted(VALID_EPISTEMIC_TYPES)}"
        )
    return {"value": value, "epistemic_type": epistemic_type, "note": note or ""}


# --------------------------------------------------------------------------- #
# Discovery Packet construction (pure — no network, no LLM call inside this
# function itself; generated fields are passed in already-produced, so this
# function is fully unit-testable with hand-built inputs)
# --------------------------------------------------------------------------- #

def build_discovery_packet(
    commission_brief: dict,
    evidence_packet: dict,
    *,
    disturbance: str,
    reader_contract: str,
    reader_contract_distinctness_reason: str,
    supporting_evidence: list,
    carrying_material: list,
    known_gaps: list,
    form_suggestion: str = "",
    discovery_lens: str = None,
) -> dict:
    """Build and validate a Discovery Packet from an EXISTING, ALREADY-
    COMMISSIONED Fable Layer 1 brief. Does not call Fable, does not
    re-decide commissionability, does not regenerate hidden_mechanism or
    source_anchor_examined — those are read straight off `commission_brief`
    and carried through unchanged, exactly the way the architecture proposal
    requires ("hidden_mechanism ... existing VALIDATED EDITORIAL DISCOVERY
    from Fable Layer 1. Do NOT regenerate it in this slice.").

    REAL ARTICLE TEST 1 CORRECTION (0B): Slice 1/1.1 set a single `lens`
    field to `commission_brief["persona"]` whenever no explicit lens was
    given — silently claiming the EXECUTION persona (Layer 2's byline
    choice) had DISCOVERED the mechanism, when in the current, non-
    competitive architecture Fable Layer 1 judges commissionability with
    ALL FOUR lens perspectives at once and never records which one (if
    any) actually produced the winning mechanism. That is an unearned
    attribution. Fixed: the packet now carries two separate metadata
    fields —
      `discovery_lens`  — which lens actually produced the mechanism.
                          Defaults to the literal string
                          "all_lenses_unattributed" unless a caller
                          explicitly passes a real, data-backed value (which
                          nothing in this non-competitive slice can supply
                          yet — that requires Architecture C's competitive
                          discovery, explicitly out of scope here).
      `byline_persona`  — the execution persona selected by Layer 2, i.e.
                          `commission_brief.get("persona")`. This is a
                          byline/execution fact, not a discovery claim.
    discovery_lens is never auto-copied from byline_persona; a dedicated
    test (`test_discovery_lens_never_equals_byline_persona_by_default`)
    guards this.

    Fails closed (raises SofaShadowError) if:
      - commission_brief.source_decision != "commission"
      - commission_brief is missing source_anchor_examined / hidden_mechanism
      - source_anchor_examined is not a literal substring of
        evidence_packet["source_text"] (grounding-preserving — this module
        re-checks it independently of validate_source_decision, which
        already ran earlier in the real pipeline; belt-and-suspenders,
        since this module must never trust an upstream claim it can verify
        itself)
      - any supporting_evidence / carrying_material item claims a
        source_excerpt that is not a literal substring of source_text
      - any supporting_evidence / carrying_material item's editorial_note
        is typed EVIDENCE, or its note_type is missing/invalid when the
        note is non-empty (Slice 1.1 fix — a note is never itself source
        fact, even when it describes one)
      - reader_contract is empty, or identical (case-insensitively) to
        hidden_mechanism — the cheap, non-brittle distinctness floor asked
        for in the task (no semantic-similarity gate yet, just "not the
        literal same sentence")
    """
    if not isinstance(commission_brief, dict):
        raise SofaShadowError("commission_brief must be a dict")
    if commission_brief.get("source_decision") != "commission":
        raise SofaShadowError(
            "Discovery Packet can only be built from a commissioned brief "
            f"(source_decision={commission_brief.get('source_decision')!r}); "
            "declined/deferred sources never reach Discovery in this architecture"
        )

    source_anchor = commission_brief.get("source_anchor_examined")
    hidden_mechanism = commission_brief.get("hidden_mechanism")
    if not source_anchor or not isinstance(source_anchor, str):
        raise SofaShadowError("commission_brief.source_anchor_examined missing or not a string")
    if not hidden_mechanism or not isinstance(hidden_mechanism, str):
        raise SofaShadowError("commission_brief.hidden_mechanism missing or not a string")

    source_text = (evidence_packet or {}).get("source_text") or ""
    if not source_text:
        raise SofaShadowError("evidence_packet has no source_text — cannot ground a Discovery Packet")
    if source_anchor not in source_text:
        raise SofaShadowError(
            "source_anchor_examined is not a literal substring of evidence_packet.source_text — "
            "refusing to build a packet on an anchor this module cannot itself verify"
        )

    if not disturbance or not isinstance(disturbance, str):
        raise SofaShadowError("disturbance is required and must be a non-empty string")
    if not reader_contract or not isinstance(reader_contract, str):
        raise SofaShadowError("reader_contract is required and must be a non-empty string")
    if reader_contract.strip().lower() == hidden_mechanism.strip().lower():
        raise SofaShadowError(
            "reader_contract is identical to hidden_mechanism — this is exactly the "
            "'restating the insight' failure canonical Sofa forbids; regenerate the "
            "reader contract as a distinct sentence about reader interest, not the mechanism again"
        )

    def _check_material_list(items, list_name):
        """Slice 1.1: each item now produces {kind, source_excerpt, editorial_note}
        with source_excerpt and editorial_note as SEPARATE typed envelopes —
        never one envelope covering the whole item, which is exactly what
        let an interpretive note hide inside an EVIDENCE-typed blob in
        Slice 1. Caller input shape per item: {kind, source_excerpt,
        note (optional), note_type (required iff note is non-empty; one of
        EDITORIAL_GUIDANCE/EDITORIAL_INTERPRETATION)}."""
        if not isinstance(items, list):
            raise SofaShadowError(f"{list_name} must be a list")
        checked = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise SofaShadowError(f"{list_name}[{i}] must be a dict")
            kind = item.get("kind")
            excerpt = item.get("source_excerpt", "")
            note = item.get("note", "") or ""
            note_type = item.get("note_type")
            if not kind or not isinstance(kind, str):
                raise SofaShadowError(f"{list_name}[{i}].kind missing or not a string")
            if excerpt:
                if not isinstance(excerpt, str):
                    raise SofaShadowError(f"{list_name}[{i}].source_excerpt must be a string")
                if excerpt not in source_text:
                    raise SofaShadowError(
                        f"{list_name}[{i}].source_excerpt is not a literal substring of "
                        "source_text — refusing to carry an ungrounded excerpt into the packet"
                    )
            elif kind != "unresolved_absence":
                raise SofaShadowError(
                    f"{list_name}[{i}] has no source_excerpt and kind != 'unresolved_absence' — "
                    "every carrying/supporting item must either quote real source text or "
                    "explicitly be the 'unresolved_absence' kind (a gap, not a fact)"
                )
            if note:
                if note_type not in _MATERIAL_NOTE_TYPES:
                    raise SofaShadowError(
                        f"{list_name}[{i}].note_type must be one of {sorted(_MATERIAL_NOTE_TYPES)} "
                        f"when a note is present (got {note_type!r}) — an editorial note about a "
                        "piece of evidence is never itself typed EVIDENCE"
                    )
            else:
                note_type = note_type if note_type in _MATERIAL_NOTE_TYPES else EDITORIAL_GUIDANCE
            checked.append({
                "kind": kind,
                "source_excerpt": _field(excerpt, EVIDENCE, note=f"{list_name}[{i}] verbatim excerpt"),
                "editorial_note": _field(note, note_type, note=f"{list_name}[{i}] editorial note"),
            })
        return checked

    def _check_known_gaps(gaps):
        """Slice 1.1: each gap is now its own GROUNDING_BOUNDARY-typed
        envelope, not a bare string inside one EVIDENCE-typed list field —
        a statement of what the evidence does NOT authorize is neither a
        fact nor an interpretation."""
        if not isinstance(gaps, list) or not all(isinstance(g, str) for g in gaps):
            raise SofaShadowError("known_gaps must be a list of strings")
        return [_field(g, GROUNDING_BOUNDARY, note="what the evidence does NOT authorize claiming")
                for g in gaps]

    packet = {
        "schema_version": SCHEMA_VERSION,
        "built_at": _dt.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "evidence_packet_hash": (evidence_packet or {}).get("evidence_packet_hash"),

        "source_anchor": _field(source_anchor, EVIDENCE,
                                 note="verbatim, from commission_brief.source_anchor_examined"),
        "disturbance": _field(disturbance, EDITORIAL_INTERPRETATION,
                               note="what in the evidence does not fit the ordinary explanation"),
        "hidden_mechanism": _field(hidden_mechanism, EDITORIAL_INTERPRETATION,
                                    note="INHERITED from Fable Layer 1, NOT regenerated in this slice; "
                                         "already semantic-entailment-checked upstream; this is "
                                         "validated interpretation, not source fact"),
        "discovery_lens": _field(
            discovery_lens if discovery_lens else DISCOVERY_LENS_UNATTRIBUTED,
            EDITORIAL_METADATA,
            note="which lens produced the mechanism — unattributed unless a competitive-discovery "
                 "step (Architecture C, not this slice) explicitly recorded it",
        ),
        "byline_persona": _field(
            commission_brief.get("persona"), EDITORIAL_METADATA,
            note="the execution persona selected by Fable Layer 2 — a byline/execution fact, "
                 "NOT a claim that this persona discovered the mechanism",
        ),
        "reader_contract": _field(reader_contract, EDITORIAL_GUIDANCE,
                                   note="why a general reader should care; distinct from the mechanism"),
        "reader_contract_distinctness_reason": _field(
            reader_contract_distinctness_reason or "", EDITORIAL_GUIDANCE,
            note="human/model-facing note on why this is not just the mechanism restated — "
                 "unvalidated by a similarity gate in this slice, inspected manually per the task",
        ),
        "supporting_evidence": _check_material_list(supporting_evidence, "supporting_evidence"),
        "carrying_material": _check_material_list(carrying_material, "carrying_material"),
        "known_gaps": _check_known_gaps(known_gaps),
        "form_suggestion": _field(form_suggestion or "", EDITORIAL_GUIDANCE,
                                   note="suggestion only; writer may override if material argues otherwise"),
    }
    ok, errors = validate_discovery_packet(packet)
    if not ok:
        raise SofaShadowError("built packet failed its own validation: " + "; ".join(errors))
    return packet


def validate_discovery_packet(packet: dict):
    """Deterministic, non-LLM schema check. Returns (ok, errors). Never
    raises — mirrors validate_source_decision's (ok, code, reason, violations)
    discipline of returning a verdict rather than throwing, so a caller that
    wants to inspect-and-report (rather than fail-closed immediately) can.

    Slice 1.1: supporting_evidence/carrying_material items are validated as
    {kind: str, source_excerpt: envelope[EVIDENCE], editorial_note:
    envelope[EDITORIAL_GUIDANCE|EDITORIAL_INTERPRETATION]} — a note typed
    EVIDENCE is a hard validation failure, not a warning. known_gaps items
    are validated as envelopes typed GROUNDING_BOUNDARY, not EVIDENCE."""
    errors = []
    if not isinstance(packet, dict):
        return False, ["packet is not a dict"]

    required = (
        "schema_version", "source_anchor", "disturbance", "hidden_mechanism",
        "discovery_lens", "byline_persona", "reader_contract", "reader_contract_distinctness_reason",
        "supporting_evidence", "carrying_material", "known_gaps", "form_suggestion",
    )
    for key in required:
        if key not in packet:
            errors.append(f"missing required field: {key}")

    def _is_envelope(v):
        return isinstance(v, dict) and "value" in v and "epistemic_type" in v

    for key, val in packet.items():
        if key in ("schema_version", "built_at", "evidence_packet_hash"):
            continue

        if key in ("supporting_evidence", "carrying_material"):
            if not isinstance(val, list):
                errors.append(f"{key} must be a list of {{kind, source_excerpt, editorial_note}} items")
                continue
            for i, item in enumerate(val):
                if not isinstance(item, dict):
                    errors.append(f"{key}[{i}] must be a dict")
                    continue
                if not isinstance(item.get("kind"), str) or not item["kind"]:
                    errors.append(f"{key}[{i}].kind missing or not a string")
                se = item.get("source_excerpt")
                if not _is_envelope(se):
                    errors.append(f"{key}[{i}].source_excerpt is not a typed envelope")
                elif se["epistemic_type"] != EVIDENCE:
                    errors.append(
                        f"{key}[{i}].source_excerpt.epistemic_type must be EVIDENCE, "
                        f"got {se['epistemic_type']!r}"
                    )
                en = item.get("editorial_note")
                if not _is_envelope(en):
                    errors.append(f"{key}[{i}].editorial_note is not a typed envelope")
                elif en["epistemic_type"] not in _MATERIAL_NOTE_TYPES:
                    errors.append(
                        f"{key}[{i}].editorial_note.epistemic_type must be one of "
                        f"{sorted(_MATERIAL_NOTE_TYPES)} (never EVIDENCE), got {en['epistemic_type']!r}"
                    )
            continue

        if key == "known_gaps":
            if not isinstance(val, list):
                errors.append("known_gaps must be a list of GROUNDING_BOUNDARY envelopes")
                continue
            for i, item in enumerate(val):
                if not _is_envelope(item):
                    errors.append(f"known_gaps[{i}] is not a typed envelope")
                elif item["epistemic_type"] != GROUNDING_BOUNDARY:
                    errors.append(
                        f"known_gaps[{i}].epistemic_type must be GROUNDING_BOUNDARY, "
                        f"got {item['epistemic_type']!r}"
                    )
            continue

        if not _is_envelope(val):
            errors.append(f"{key} is not a typed field envelope (needs value + epistemic_type)")
            continue
        if val["epistemic_type"] not in VALID_EPISTEMIC_TYPES:
            errors.append(f"{key}.epistemic_type invalid: {val['epistemic_type']!r}")

    return (len(errors) == 0), errors


# --------------------------------------------------------------------------- #
# Writer-context projection — this is the ONE function that decides what
# crosses the Discovery -> Writer boundary. Everything not explicitly
# listed here stays on the editorial side, per canonical Sofa §2/§4.
# --------------------------------------------------------------------------- #

def to_writer_context(packet: dict, source_text: str) -> dict:
    """Project a Discovery Packet down to exactly what the shadow writer is
    allowed to receive. Strips epistemic-type envelopes to plain values
    (the writer doesn't need the bookkeeping, it needs the content), and
    OMITS entirely:
      - why_disability_knowledge_changes_subject and the other
        internal-only commission fields (never even enter this packet —
        see build_discovery_packet, which never copies them)
      - reader_contract_distinctness_reason (an editorial self-check, not
        material for the article)
      - evidence_packet_hash / schema_version / built_at (provenance
        bookkeeping, not writer content)

    REAL ARTICLE TEST 1 CORRECTION (0C): `source_text` (the exact evidence-
    packet source text this commission/packet was built from) is now a
    REQUIRED argument, surfaced to the writer as `reference_source`. Slice
    1/1.1's writer only ever saw the ranked supporting_evidence/
    carrying_material excerpts — a real risk that Discovery becomes a
    LOSSY COMPRESSION layer, silently discarding grounded detail the
    ranking happened not to select. The writer context now states an
    explicit hierarchy (see build_shadow_writer_prompt): carrying_material
    is the likely narrative spine, supporting_evidence is mechanism-
    support, and reference_source is additional grounded detail available
    when useful — never a license to abandon the ranked spine just because
    a louder number appears elsewhere in the source, and every claim drawn
    from it remains subject to the same post-writer grounding audit.

    REAL ARTICLE TEST 1 CORRECTION (0A): the previous version of this
    function serialized the context to JSON and did a plain substring
    search for banned phrases/keys — which produces false positives on
    ordinary prose (a source excerpt or article sentence containing "the
    reason", "the artistic canon", "a wound", "her mood" is not leakage).
    Fixed: this now recursively inspects dictionary KEYS ONLY via
    `_find_banned_keys` — a banned word appearing inside a string VALUE is
    never flagged; only an actual key name is.
    """
    ok, errors = validate_discovery_packet(packet)
    if not ok:
        raise SofaShadowError("cannot build writer context from invalid packet: " + "; ".join(errors))
    if not source_text or not isinstance(source_text, str):
        raise SofaShadowError(
            "to_writer_context requires the real source_text as reference_source — "
            "refusing to build a writer context with no reference source at all"
        )

    def _material(items):
        # Slice 1.1: unwrap the two-envelope item shape to plain values for
        # the writer (it needs the content, not the epistemic bookkeeping),
        # while keeping source_excerpt and editorial_note as separate keys
        # so the writer prompt can label them distinctly (see
        # build_shadow_writer_prompt) instead of silently re-merging them.
        return [
            {
                "kind": item["kind"],
                "source_excerpt": item["source_excerpt"]["value"],
                "editorial_note": item["editorial_note"]["value"],
            }
            for item in items
        ]

    context = {
        "discovery_lens": packet["discovery_lens"]["value"],
        "byline_persona": packet["byline_persona"]["value"],
        "disturbance": packet["disturbance"]["value"],
        "hidden_mechanism": {
            "claim": packet["hidden_mechanism"]["value"],
            "epistemic_status": "This is validated EDITORIAL INTERPRETATION, not a quoted source "
                                 "fact. Treat it as the discovery the evidence should be allowed to "
                                 "make intelligible — not a slogan the article must state, open with, "
                                 "close with, or prove like a thesis.",
        },
        "source_anchor": packet["source_anchor"]["value"],
        "supporting_evidence": _material(packet["supporting_evidence"]),
        "carrying_material": _material(packet["carrying_material"]),
        "known_gaps": [g["value"] for g in packet["known_gaps"]],
        "reader_contract": packet["reader_contract"]["value"],
        "form_suggestion": packet["form_suggestion"]["value"],
        "reference_source": source_text,
    }

    banned_key_hits = (
        _find_banned_keys(context, _PERSONA_ROLEPLAY_KEYS)
        + _find_banned_keys(context, _INTERNAL_ONLY_COMMISSION_FIELDS)
    )
    if banned_key_hits:
        raise SofaShadowError(
            "writer context contains banned key(s) as actual dictionary keys "
            f"(not merely as words inside prose): {banned_key_hits}"
        )
    # Phrase check stays on the assembled string form deliberately — a
    # literal boilerplate phrase like "WRITE LIKE THIS PERSON" appearing
    # anywhere, even inside a value, is still a real leak (unlike a bare
    # word such as "wound"), because no legitimate source excerpt or
    # article sentence would ever contain that exact production phrase.
    blob = _json.dumps(context)
    for phrase in _PERSONA_ROLEPLAY_PHRASES:
        if phrase in blob:
            raise SofaShadowError(f"writer context contains a banned persona-roleplay phrase: {phrase!r}")

    return context


def assert_no_persona_leakage(text: str) -> None:
    """Second, independent defense — scans an assembled PROMPT STRING (not
    a structured context dict) for distinctive production-roleplay
    BOILERPLATE PHRASES only. Raises SofaShadowError on any hit. Call this
    on the final assembled writer prompt string before it is ever sent to
    a model.

    REAL ARTICLE TEST 1 CORRECTION (0A): the previous version of this
    function also substring-scanned raw text for bare, generic words like
    "wound"/"canon"/"mood" — which real source material or article prose
    can legitimately contain ("her mood," "the artistic canon," "a wound")
    with zero connection to persona roleplay. Raw prompt text has no
    dictionary keys to inspect, so the key-based fix used in
    `to_writer_context` doesn't apply here — the correct fix for free text
    is to check ONLY for the specific, multi-word boilerplate phrases that
    actually appear in the production persona-roleplay prompt (see
    _PERSONA_ROLEPLAY_PHRASES), never single common words."""
    if not isinstance(text, str):
        raise SofaShadowError("assert_no_persona_leakage expects a string")
    for phrase in _PERSONA_ROLEPLAY_PHRASES:
        if phrase in text:
            raise SofaShadowError(f"writer prompt contains a banned persona-roleplay phrase: {phrase!r}")


# --------------------------------------------------------------------------- #
# Discovery-step generation — the ONE new model call this slice adds.
# Generates disturbance / reader_contract / supporting_evidence /
# carrying_material / known_gaps / form_suggestion from an already-
# commissioned brief. Does NOT touch hidden_mechanism/source_anchor_examined
# (read-only inherited inputs) and does NOT run multiple lens candidates —
# that is Architecture C, explicitly out of scope for this slice.
# --------------------------------------------------------------------------- #

def build_shadow_discovery_prompt(commission_brief: dict, evidence_packet: dict):
    """Returns (system_prompt, user_prompt) for the single Discovery-step
    model call. Deliberately small: one inherited mechanism, one source
    text, six fields to produce. Does not ask the model to re-judge
    commissionability (already decided) or to generate a second candidate
    mechanism (Architecture C, not this slice)."""
    source_text = (evidence_packet or {}).get("source_text") or ""
    system = (
        "You are the Discovery step of an editorial pipeline, running AFTER a source has "
        "already been commissioned. You do not decide whether this story is worth telling — "
        "that decision is final. Your only job is to prepare material for a separate prose "
        "writer who has not seen this source yet.\n\n"
        "You will be given: the source text, the validated source_anchor (a verbatim quoted "
        "clause), and the validated hidden_mechanism (an editorial interpretation, already "
        "checked against the source — you may not change it, soften it, or restate it as your "
        "own new claim).\n\n"
        "Produce, in the source's own actual content only — never invent a name, quote, date, "
        "or number that is not literally present in the source text below:\n"
        "1. disturbance — one or two sentences describing what in the evidence does not fit the "
        "ordinary explanation. This is your editorial description, not a quote.\n"
        "2. reader_contract — why an intelligent general reader who does not already care about "
        "this subject should keep reading. This must NOT be hidden_mechanism restated in new "
        "words — it answers a different question (reader interest, not mechanism).\n"
        "3. reader_contract_distinctness_reason — one sentence on why your reader_contract is not "
        "just the mechanism again.\n"
        "4. supporting_evidence — a list of items, each {kind, source_excerpt, note, note_type}, "
        "where source_excerpt is a literal substring of the source text that helps PROVE the "
        "mechanism is real, note is a short editorial explanation of why this item matters, and "
        "note_type is exactly 'EDITORIAL_INTERPRETATION' if the note asserts what the excerpt means "
        "or reveals, or 'EDITORIAL_GUIDANCE' if the note is advice about using it in the article. "
        "The note itself is NEVER treated as source fact — only source_excerpt is.\n"
        "5. carrying_material — a list of items, each {kind, source_excerpt, note, note_type}, same "
        "rules as above, where source_excerpt is a literal substring of the source text that could "
        "CARRY a reader through the article narratively (a sequence of dated events, a document, a "
        "person doing something, a measurement, an object, a contradiction, a quote, or — if "
        "genuinely absent — kind='unresolved_absence' with an empty source_excerpt). Do not default "
        "to whichever single fact is loudest or largest; consider whether a sequence of smaller "
        "facts would let the reader watch something happen rather than be told a number. "
        "supporting_evidence and carrying_material may overlap or may not — do not force them apart "
        "artificially.\n"
        "6. known_gaps — a list of plain-language statements of what the evidence does NOT "
        "support, so the writer knows the hard boundary of what may be claimed.\n"
        "7. form_suggestion — optional, one phrase (e.g. 'essay', 'field_note-like present-tense "
        "scene', 'short provocation') suggested by the shape of the material, not chosen at "
        "random. The writer may ignore it.\n\n"
        "Reply with JSON only, no other text, using exactly these keys: disturbance, "
        "reader_contract, reader_contract_distinctness_reason, supporting_evidence, "
        "carrying_material, known_gaps, form_suggestion."
    )
    user = (
        f"SOURCE TEXT:\n---\n{source_text}\n---\n\n"
        f"VALIDATED source_anchor_examined (verbatim from the source, do not alter):\n"
        f"{commission_brief.get('source_anchor_examined')}\n\n"
        f"VALIDATED hidden_mechanism (editorial interpretation, already checked — inherit, do "
        f"not regenerate or restate as new):\n{commission_brief.get('hidden_mechanism')}\n"
    )
    return system, user


def run_shadow_discovery(commission_brief: dict, evidence_packet: dict, discovery_llm_call,
                          discovery_lens: str = None) -> dict:
    """Orchestrates ONE Discovery-step model call and builds a validated
    Discovery Packet from its output. `discovery_llm_call(system_prompt,
    user_prompt) -> str` is injected so tests can supply a deterministic
    stub and so no network call is hidden inside this function's own body.

    REAL ARTICLE TEST 1 CORRECTION (0D): renamed from the generic `llm_call`
    to `discovery_llm_call` — this slice now has three distinct model
    roles (discovery, writer, grounding audit) and each must be resolvable
    to (and recorded as) the specific production model it is standing in
    for, never silently sharing one generic callable that could hide a
    model-identity mismatch between roles.

    Fails closed (raises SofaShadowError) on: a non-commission brief
    (checked again here, in addition to build_discovery_packet, so the
    model is never even called against a declined/deferred source),
    unparseable model output, or any grounding violation caught by
    build_discovery_packet (fabricated excerpt, mechanism restated as the
    reader contract, etc.)."""
    if commission_brief.get("source_decision") != "commission":
        raise SofaShadowError(
            "run_shadow_discovery called on a non-commissioned brief — Discovery never runs "
            "on a decline/defer in this architecture"
        )
    system, user = build_shadow_discovery_prompt(commission_brief, evidence_packet)
    raw = discovery_llm_call(system, user)
    if not raw or not isinstance(raw, str):
        raise SofaShadowError("Discovery-step model call returned no usable text")
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        parsed = _json.loads(cleaned)
    except (ValueError, IndexError) as exc:
        raise SofaShadowError(f"Discovery-step model output was not valid JSON: {exc}") from exc

    return build_discovery_packet(
        commission_brief,
        evidence_packet,
        disturbance=parsed.get("disturbance", ""),
        reader_contract=parsed.get("reader_contract", ""),
        reader_contract_distinctness_reason=parsed.get("reader_contract_distinctness_reason", ""),
        supporting_evidence=parsed.get("supporting_evidence", []),
        carrying_material=parsed.get("carrying_material", []),
        known_gaps=parsed.get("known_gaps", []),
        form_suggestion=parsed.get("form_suggestion", ""),
        discovery_lens=discovery_lens,
    )


# --------------------------------------------------------------------------- #
# Shadow writer — the smallest house-prose prompt needed to test the
# hypothesis, per the task's explicit "do NOT copy the giant production
# writer prompt wholesale" instruction. No persona voice, no roleplay, no
# byline-as-character. Byline is metadata attached AFTER generation, not a
# character the model is asked to inhabit.
# --------------------------------------------------------------------------- #

def build_shadow_writer_prompt(writer_context: dict):
    """Returns (system_prompt, user_prompt) for the shadow writer. Built
    directly from canonical Sofa §4 and §10 — Lens≠Writer, house prose
    standard — not from generate.py's persona-voice writer prompt, which
    this function does not read, import, or reference.

    REAL ARTICLE TEST 1 CORRECTION (0C): the writer now also receives
    `reference_source` — the full source text the evidence packet was
    built from — with an explicit priority hierarchy: carrying_material is
    the editorial process's best guess at the narrative spine,
    supporting_evidence is what proves the mechanism, and reference_source
    is additional grounded detail available when the ranked material
    turns out to have omitted something useful. The writer is told not to
    abandon the ranked spine merely because a louder number appears
    elsewhere in the source — every claim, wherever it comes from, remains
    subject to the same post-writer grounding audit."""
    system = (
        "You are a prose writer for a disability-led publication. You are not a character and "
        "you have no biography — you are a writing function. You will be given what an editorial "
        "process has already discovered about a real, sourced story. Your job is to write one "
        "article of narrative nonfiction that lets the evidence make that discovery intelligible "
        "to a reader who does not already care about this subject.\n\n"
        "HOUSE STANDARD:\n"
        "- Make the thinking sophisticated. Make the reading easy. Easy does not mean short.\n"
        "- Write book-like narrative nonfiction: developed paragraphs, explicit referents, "
        "concrete verbs, one unfamiliar idea introduced at a time.\n"
        "- Facts, documents, actions, and sequences should carry the thinking — not repeated "
        "explanation of what they mean.\n"
        "- No staccato simplification. No academic or legal-report compression. No repeated "
        "paraphrasing of the same insight in new words.\n"
        "- No mandatory first person. No mandatory disability paragraph or disclosure. Write in "
        "first person only if the supplied material genuinely supports it — never as a default.\n"
        "- Never invent a scene, quote, person, motive, or specific detail beyond what is in the "
        "SUPPORTING EVIDENCE / CARRYING MATERIAL / REFERENCE SOURCE sections below. If you want a "
        "concrete detail, it must already be there.\n\n"
        "MATERIAL HIERARCHY (read this before writing):\n"
        "1. CARRYING MATERIAL is the editorial process's ranked judgment of what likely carries "
        "the reader through the article — treat it as the probable narrative spine.\n"
        "2. SUPPORTING EVIDENCE is what proves the hidden mechanism is real.\n"
        "3. REFERENCE SOURCE is the complete original source text, given so you can recover a "
        "useful grounded detail the ranking above may have omitted. It is a safety net, not a "
        "replacement for the ranked material above: do not abandon the carrying material's spine "
        "merely because a louder or bigger number happens to appear elsewhere in the reference "
        "source. Every factual detail you use, wherever it comes from, remains subject to a "
        "post-writer grounding audit — an editorial NOTE attached to any item is never itself a "
        "source fact, only the quoted excerpt is.\n\n"
        "ABOUT THE DISCOVERY YOU ARE GIVEN: the hidden_mechanism below is a validated EDITORIAL "
        "INTERPRETATION, not a source fact you are quoting. Treat it as the thing this article "
        "should make intelligible through evidence — not a slogan you must state verbatim, not a "
        "thesis you must open or close on, not a sentence to reproduce. You decide the opening, "
        "the sequence, when (if ever) the mechanism becomes explicit on the page, and the ending. "
        "The reader_contract is guidance about why a reader should care — it is a stance to earn "
        "on the page, not a sentence to place anywhere in particular.\n\n"
        "The form_suggestion, if present, is a suggestion only. If the material clearly wants a "
        "different shape, use that instead.\n\n"
        "Write the article now. Do not explain your reasoning. Do not output anything except the "
        "article itself, with a title on the first line."
    )
    user = (
        f"DISTURBANCE (editorial description of what doesn't fit): {writer_context['disturbance']}\n\n"
        f"HIDDEN MECHANISM (validated editorial interpretation — {writer_context['hidden_mechanism']['epistemic_status']}):\n"
        f"{writer_context['hidden_mechanism']['claim']}\n\n"
        f"READER CONTRACT (why a general reader should care — guidance, not a sentence to quote): "
        f"{writer_context['reader_contract']}\n\n"
        f"SOURCE ANCHOR (verbatim evidence the commission rests on): {writer_context['source_anchor']}\n\n"
        f"CARRYING MATERIAL (priority 1 — likely narrative spine; the [note] after each item is an "
        f"EDITORIAL comment about the excerpt, not itself a source fact):\n"
        + "\n".join(f"- [{it['kind']}] {it['source_excerpt'] or '(no excerpt — see note)'} "
                     f"— (editorial note) {it['editorial_note']}"
                     for it in writer_context["carrying_material"])
        + "\n\n"
        f"SUPPORTING EVIDENCE (priority 2 — proves the mechanism; same rule, the [note] is "
        f"editorial, not source fact):\n"
        + "\n".join(f"- [{it['kind']}] {it['source_excerpt'] or '(no excerpt — see note)'} "
                     f"— (editorial note) {it['editorial_note']}"
                     for it in writer_context["supporting_evidence"])
        + "\n\n"
        f"KNOWN GAPS (the evidence does NOT support these — do not claim them):\n"
        + "\n".join(f"- {g}" for g in writer_context["known_gaps"])
        + "\n\n"
        f"FORM SUGGESTION (optional, overridable): {writer_context['form_suggestion'] or '(none — choose the shape the material earns)'}\n\n"
        f"REFERENCE SOURCE (priority 3 — the complete original source text; use it to recover "
        f"grounded detail the ranking above may have omitted, not to override the ranked spine):\n"
        f"---\n{writer_context['reference_source']}\n---\n"
    )
    assert_no_persona_leakage(system + user)
    return system, user


def run_shadow_writer(writer_context: dict, writer_llm_call) -> str:
    """Builds the shadow writer prompt, runs the second of the three model
    calls this slice set adds (Discovery, Writer, then the Slice 1.1
    grounding audit below), and returns the raw article text.
    `writer_llm_call` is injected exactly like `discovery_llm_call` in
    run_shadow_discovery — renamed (0D) so the writer role's model
    identity is never confused with Discovery's or the audit's, and can be
    pinned to the exact same production writer model a Legacy comparison
    run uses. Raises SofaShadowError if the assembled prompt itself fails
    the persona-leakage scan (belt and suspenders: build_shadow_writer_prompt
    already asserts this before returning) or if the model returns nothing
    usable."""
    system, user = build_shadow_writer_prompt(writer_context)
    raw = writer_llm_call(system, user)
    if not raw or not isinstance(raw, str) or not raw.strip():
        raise SofaShadowError("shadow writer model call returned no usable text")
    return raw.strip()


# --------------------------------------------------------------------------- #
# ARTICLE GROUNDING AUDIT (Shadow Slice 1.1, Problem 2) — a grounded
# Discovery Packet does NOT guarantee a grounded finished article. Slice 1's
# SYNTH-1 shadow article introduced unsupported causal/motive/certainty
# claims ("its hold cannot legally outlast forty-five days", "Nobody...was
# lying", "did not appear by accident") that no packet-level substring check
# could ever catch, because they are properties of what the WRITER produced,
# not of the packet it was given. This section audits the ARTICLE TEXT
# itself, after generation, against the source and the packet.
#
# Two layers, deliberately not one:
#   1. A DETERMINISTIC pre-scan — reuses grounding.scan_free_prose_field
#      (imported above, not duplicated) against the full article text. This
#      catches invented quoted spans, invented proper-noun-shaped entities,
#      and invented multi-digit numbers not present in source_text. Cheap,
#      blunt, exactly as documented in grounding.py — a clean result here
#      means "no hit on these three patterns," never "this article contains
#      no unsupported claims."
#   2. A MODEL call, because the deterministic scan cannot and does not
#      claim to catch interpretive overreach with no quote/number/proper-
#      noun shape ("Nobody was lying", "did not appear by accident", "cannot
#      legally outlast forty-five days" — none of these trip a regex). This
#      is the class of failure the task identified as the actual gap.
#
# _fable_editorial_review (llm.py) was inspected first, per the task's
# instruction to prefer reusing existing Fable review logic. It was NOT
# reused: it is tightly coupled to persona identity (persona canon/wound/
# first-person-episode checking), enforces "first-person throughout" as a
# hard rule (canonical Sofa explicitly forbids mandatory first person), and
# produces open-ended revision NOTES rather than a per-claim SUPPORTED/
# UNSUPPORTED/UNCERTAIN verdict. Reusing it would either drag persona
# machinery into a module that must stay persona-free, or require stripping
# it down so far that little of substance would actually be reused. A small,
# new, narrowly-scoped auditor was built instead, per the task's own
# fallback instruction.
# --------------------------------------------------------------------------- #

AUDIT_SUPPORTED = "SUPPORTED"
AUDIT_UNSUPPORTED = "UNSUPPORTED"
AUDIT_UNCERTAIN = "UNCERTAIN"
_VALID_AUDIT_VERDICTS = frozenset({AUDIT_SUPPORTED, AUDIT_UNSUPPORTED, AUDIT_UNCERTAIN})


def run_deterministic_prescan(article_text: str, source_text: str):
    """Thin, undisguised wrapper around grounding.scan_free_prose_field —
    reused, not duplicated, per the task's explicit instruction to inspect
    existing primitives before writing a new one. Returns the same list of
    (reason_code, reason) tuples that function returns. Catches: invented
    quoted spans, invented proper-noun-shaped entities (candidate invented
    names), invented multi-digit numbers/dates. Does NOT catch unsupported
    causal/motive/certainty claims — see run_shadow_grounding_audit for that
    class."""
    return _scan_free_prose_field(article_text, source_text)


def build_shadow_grounding_audit_prompt(source_text: str, packet: dict, article_text: str,
                                         deterministic_flags=None):
    """Returns (system_prompt, user_prompt) for the post-writer grounding
    audit model call. Scoped narrowly to what the deterministic pre-scan
    cannot do: judging specific SENTENCES/CLAIMS in the article for
    unsupported causal claims, unsupported motives, unsupported certainty,
    and interpretation presented as if it were source fact."""
    known_gaps = [g["value"] for g in packet.get("known_gaps", [])] if packet else []
    system = (
        "You are a grounding auditor for a disability-led publication. You did not write this "
        "article and you do not get to fix it. Your only job is to identify SPECIFIC claims or "
        "sentences in the article below that are not actually supported by the source text or by "
        "the editorial discovery packet's own explicit fields, and classify each one.\n\n"
        "Look specifically for the failure classes that simple pattern-matching cannot catch:\n"
        "- an unsupported CAUSAL claim (the article asserts X caused Y, or explains WHY something "
        "happened, when the source only shows that it happened)\n"
        "- an unsupported MOTIVE claim (the article asserts what someone intended, knew, believed, "
        "or was NOT doing — e.g. 'nobody was lying' asserts a claim about intent/knowledge the "
        "source does not establish)\n"
        "- unsupported CERTAINTY or a legal/factual claim stated as settled when the source does "
        "not establish it (e.g. 'cannot legally' is a legal conclusion; the source showing a POLICY "
        "definition is not the same as the source establishing legal enforceability)\n"
        "- an interpretation from the discovery packet's hidden_mechanism/disturbance presented in "
        "the article AS IF it were an established source fact, rather than as the article's own "
        "argument\n"
        "- invented names, dates, numbers, or quotations (also flag these if you see them, even "
        "though a separate deterministic pass already checks for some of this)\n\n"
        "For each claim you flag, quote the exact sentence or clause from the article, and give a "
        "verdict: SUPPORTED (the source or packet actually establishes this), UNSUPPORTED (the "
        "source/packet does not establish this and the article states it as if settled), or "
        "UNCERTAIN (plausible but not verifiable from what you were given — explain what would be "
        "needed to resolve it). Do not flag ordinary narrative connective language ('then', 'a week "
        "later', 'as a result of that letter') that does not assert a new unsupported fact.\n\n"
        "Reply with JSON only: {\"claims\": [{\"claim\": \"...\", \"verdict\": \"SUPPORTED|"
        "UNSUPPORTED|UNCERTAIN\", \"reason\": \"...\"}, ...]}. An empty claims list means you found "
        "nothing to flag — do not pad the list with trivially-supported claims just to have entries."
    )
    user = (
        f"SOURCE TEXT:\n---\n{source_text}\n---\n\n"
        f"DISCOVERY PACKET'S hidden_mechanism (editorial interpretation, not source fact — the "
        f"article may explore this, but must not present it as something the source itself states):"
        f"\n{(packet.get('hidden_mechanism') or {}).get('value', '') if packet else ''}\n\n"
        f"DISCOVERY PACKET's known_gaps (things the article must NOT claim):\n"
        + "\n".join(f"- {g}" for g in known_gaps) + "\n\n"
        + (
            "DETERMINISTIC PRE-SCAN already flagged these candidates (blunt pattern-matching, not "
            "proof — judge each with real understanding, and add anything else you find):\n"
            + "; ".join(f"'{reason}'" for _code, reason in deterministic_flags) + "\n\n"
            if deterministic_flags else ""
        )
        + f"ARTICLE TEXT TO AUDIT:\n---\n{article_text}\n---\n"
    )
    return system, user


def run_shadow_grounding_audit(source_text: str, packet: dict, article_text: str, audit_llm_call) -> dict:
    """Orchestrates the full post-writer grounding audit: deterministic
    pre-scan + one model call, merged into a single result dict:

      {"deterministic_flags": [(reason_code, reason), ...],
       "claims": [{"claim": str, "verdict": SUPPORTED|UNSUPPORTED|UNCERTAIN, "reason": str}, ...]}

    `audit_llm_call` (0D — renamed from generic `llm_call`) should be
    pinned to the production model that plays the closest real role to
    this function: the review/audit model (production's
    `_fable_editorial_review` model chain), recorded exactly in the
    results artifact, never silently substituted for the discovery or
    writer model.

    Fails closed (raises SofaShadowError) on unparseable model output or a
    malformed claim entry (missing claim/verdict, or verdict not one of the
    three valid values) — an audit result this module cannot itself trust
    must not be used to certify an article as eligible for comparison."""
    deterministic_flags = run_deterministic_prescan(article_text, source_text)
    system, user = build_shadow_grounding_audit_prompt(source_text, packet, article_text, deterministic_flags)
    raw = audit_llm_call(system, user)
    if not raw or not isinstance(raw, str):
        raise SofaShadowError("grounding-audit model call returned no usable text")
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        parsed = _json.loads(cleaned)
    except (ValueError, IndexError) as exc:
        raise SofaShadowError(f"grounding-audit model output was not valid JSON: {exc}") from exc

    claims = parsed.get("claims", [])
    if not isinstance(claims, list):
        raise SofaShadowError("grounding-audit output 'claims' must be a list")
    checked_claims = []
    for i, c in enumerate(claims):
        if not isinstance(c, dict) or not c.get("claim") or c.get("verdict") not in _VALID_AUDIT_VERDICTS:
            raise SofaShadowError(
                f"grounding-audit claims[{i}] malformed — needs claim (non-empty) and verdict in "
                f"{sorted(_VALID_AUDIT_VERDICTS)}, got {c!r}"
            )
        checked_claims.append({
            "claim": c["claim"],
            "verdict": c["verdict"],
            "reason": c.get("reason", ""),
        })

    return {"deterministic_flags": deterministic_flags, "claims": checked_claims}


GROUNDING_STATUS_GROUNDED = "GROUNDED"
GROUNDING_STATUS_REVIEWABLE_WITH_UNCERTAINTY = "REVIEWABLE_WITH_UNCERTAINTY"
GROUNDING_STATUS_FAIL = "FAIL"


def grounding_audit_status(audit: dict):
    """REAL ARTICLE TEST 1 — uncertainty terminology correction: a binary
    PASS/FAIL collapses "no unsupported and no uncertain claims" and "no
    unsupported claims but a documented uncertain one" into the same
    label, which overstates how clean the second case actually is. Returns
    (status, reasons) where status is exactly one of:

      GROUNDED                     — no UNSUPPORTED and no UNCERTAIN claims.
      REVIEWABLE_WITH_UNCERTAINTY  — no UNSUPPORTED claims, but >=1
                                      documented UNCERTAIN claim (non-empty
                                      reason).
      FAIL                         — >=1 UNSUPPORTED claim, OR a malformed/
                                      undocumented-UNCERTAIN result (an
                                      UNCERTAIN claim with no reason is
                                      treated the same as UNSUPPORTED — an
                                      unexplained shrug is not a documented
                                      boundary).

    Both GROUNDED and REVIEWABLE_WITH_UNCERTAINTY may be shown for a shadow
    quality comparison — but a REVIEWABLE_WITH_UNCERTAINTY result must
    always visibly carry its uncertainty reasons alongside it, never be
    silently reported as equivalent to GROUNDED. Only GROUNDED should ever
    count as clean for any future PRODUCTION eligibility decision (not
    built in this slice)."""
    if not isinstance(audit, dict) or "claims" not in audit or not isinstance(audit.get("claims"), list):
        return GROUNDING_STATUS_FAIL, ["audit result is malformed — missing/invalid 'claims'"]

    unsupported_reasons = []
    uncertain_reasons = []
    for c in audit["claims"]:
        if not isinstance(c, dict) or c.get("verdict") not in _VALID_AUDIT_VERDICTS:
            return GROUNDING_STATUS_FAIL, [f"malformed claim entry: {c!r}"]
        if c["verdict"] == AUDIT_UNSUPPORTED:
            unsupported_reasons.append(f"UNSUPPORTED: {c['claim']!r} — {c.get('reason', '(no reason given)')}")
        elif c["verdict"] == AUDIT_UNCERTAIN:
            if (c.get("reason") or "").strip():
                uncertain_reasons.append(f"UNCERTAIN (documented): {c['claim']!r} — {c['reason']}")
            else:
                unsupported_reasons.append(
                    f"UNDOCUMENTED UNCERTAIN: {c['claim']!r} — no reason given, treated as a failure"
                )

    if unsupported_reasons:
        return GROUNDING_STATUS_FAIL, unsupported_reasons
    if uncertain_reasons:
        return GROUNDING_STATUS_REVIEWABLE_WITH_UNCERTAINTY, uncertain_reasons
    return GROUNDING_STATUS_GROUNDED, []


def grounding_audit_passes(audit: dict):
    """Retained for Slice 1.1 callers/tests. Returns (ok, reasons) derived
    from `grounding_audit_status`: ok is True for GROUNDED or
    REVIEWABLE_WITH_UNCERTAINTY, False for FAIL. Prefer
    `grounding_audit_status` directly in new code — it does not collapse
    the documented-uncertainty case into a bare boolean."""
    status, reasons = grounding_audit_status(audit)
    return (status != GROUNDING_STATUS_FAIL), reasons


def discovery_packet_eligible_for_comparison(packet: dict, audit: dict):
    """The task's §5 eligibility rule, kept as its own function so callers
    cannot accidentally conflate 'the packet's excerpts are grounded' with
    'the finished article is grounded' — these are two different checks,
    on two different objects (a packet's substrings vs. an article's
    claims), and this function is the only place that combines them.

    Eligible for Sofa quality comparison (SHOWING to a human reader) only
    if BOTH:
      A. the Discovery Packet validates (validate_discovery_packet), AND
      B. the post-writer grounding audit status is GROUNDED or
         REVIEWABLE_WITH_UNCERTAINTY (never FAIL).

    Returns (eligible, status, reasons) — `status` is one of
    grounding_audit_status's three values, always returned so a
    REVIEWABLE_WITH_UNCERTAINTY result is never silently reported as
    equivalent to GROUNDED even when eligible is True for both."""
    packet_ok, packet_errors = validate_discovery_packet(packet)
    audit_status, audit_reasons = grounding_audit_status(audit)
    reasons = [f"PACKET: {e}" for e in packet_errors] + [f"ARTICLE ({audit_status}): {r}" for r in audit_reasons]
    eligible = packet_ok and audit_status != GROUNDING_STATUS_FAIL
    return eligible, audit_status, reasons
