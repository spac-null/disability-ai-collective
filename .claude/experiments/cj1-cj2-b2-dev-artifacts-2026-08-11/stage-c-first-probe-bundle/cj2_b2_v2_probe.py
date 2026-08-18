#!/usr/bin/env python3
"""
cj2_b2_v2_probe.py — EXPERIMENT-ONLY, uncommitted. Implements B2 v2 —
EXPLICIT PROPOSITION CONTRACT (R1 -> R2), per the frozen design in
.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md's
"## B2 v2 — REVISION 2" section. This is the SMALLEST isolated
experimental harness for that design: R1 schema/validator/call
construction, R2 schema/validator, the deterministic R1/R2 consistency
layer (Correction 5's exhaustive 3x2 table plus the uncertain row),
semantic-conflict handling (R1_R2_SEMANTIC_CONFLICT, fail-closed only in
the R1=true/R2=interpretive_only direction), and the existing
support/declaration/effective-verdict machinery reused unmodified from
cj2_b2_probe_v1_4_1.py wherever the design says KEEP.

Does NOT modify cj2_b2_probe.py, cj2_b2_probe_v1_2/1_3/1_4_1.py, any
frozen Stage A/C prompt, any capsule, or CJ-1. Does NOT touch production
code or production wiring.

Per explicit instruction: this file's main() is prepared but NOT
executed against a real model in this pass. No API calls have been made
with this harness. Static/deterministic correctness is exercised
separately by cj2_b2_v2_static_tests.py, which contains zero network
calls.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from cj1_v3_anchor_resolver import resolve_anchor  # noqa: E402
from cj2_b2_probe_v1_4_1 import _call as _call_raw  # noqa: E402  (reused unmodified, see Correction 4)

REFERENCE_SEED_DIR = HERE / ".probe_fixtures" / "cj2-reference-probe-1"
REFERENCE_RESULTS_DIR = REFERENCE_SEED_DIR / "results"
FRESH_BATCH_DIR = HERE / ".probe_fixtures" / "cj2-fresh-batch-1"
FRESH_RESULTS_DIR = FRESH_BATCH_DIR / "results"
FRESH_MAPPING_PATH = FRESH_BATCH_DIR / "human-review-hidden-mapping-v1.json"

V2_DIR = HERE / ".probe_fixtures" / "cj2-b2-v2"
R1_PROMPT_FILE = V2_DIR / "frozen_prompts" / "cj2-stage-b2-v2-r1.txt"
R2_PROMPT_FILE = V2_DIR / "frozen_prompts" / "cj2-stage-b2-v2-r2.txt"

R1_SYSTEM = R1_PROMPT_FILE.read_text()
R2_SYSTEM = R2_PROMPT_FILE.read_text()

# Identical to every prior B2 call — Correction 4: same model for R1/R2 on
# the first structural test, no independence claimed.
MODEL = "openrouter/claude-sonnet-4.6"
TEMPERATURE = 0.0
MAX_TOKENS = 5000
TIMEOUT = 120

REFERENCE_SLUGS = ["01_cave_dna", "05_dutch_painting_soldier", "07_ai_cheating_exam"]
ENGINE_LABELS = ["P", "S", "Z", "M"]

SEMANTIC_PROBLEMS = {
    "modality_hardening", "causality_hardening", "mechanism_invention",
    "necessity_dependency_hardening", "motivation_invention",
    "population_relation_hardening", "other",
}
ALL_PROBLEMS = SEMANTIC_PROBLEMS | {"undeclared_factual_dependency"}
ALL_ROLES = {"interpretive_only", "factual_dependency", "boundary_ambiguous"}
ALL_SUPPORT = {"not_required", "supported", "unsupported", "uncertain"}
ALL_DECLARATION = {"not_applicable", "declared", "undeclared", "uncertain"}
ALL_IMPORTANCE = {"load_bearing", "supporting", "incidental"}
ALL_EMPIRICAL_DEPENDENCY = {"true", "false", "uncertain"}
ALL_R1_AGREEMENT = {"consistent", "override"}


def _call(system_prompt: str, user_prompt: str) -> dict:
    """Thin wrapper around cj2_b2_probe_v1_4_1._call so R1/R2 use the
    identical request shape/model/temperature as every prior B2 call
    (Correction 4), without re-typing the urllib/JSON-extraction logic."""
    return _call_raw(system_prompt, user_prompt)


# ---------------------------------------------------------------------------
# Shared candidate-field helpers (unchanged from cj2_b2_probe_v1_4_1.py)
# ---------------------------------------------------------------------------

def expected_fields(candidate: dict) -> list:
    fields = []
    obs = candidate.get("additional_source_observations") or []
    for i in range(len(obs)):
        fields.append(f"additional_source_observations[{i}].observation")
    fields.append("engine_move")
    fields.append("seed_engagement")
    fields.append("interpretive_inference")
    if candidate.get("conceptual_shift") is not None:
        fields.append("conceptual_shift")
    fields.append("claimed_contribution")
    return fields


def declared_evidence_set(candidate: dict) -> set:
    ids = set(candidate.get("seed_evidence_refs") or [])
    for o in (candidate.get("additional_source_observations") or []):
        if isinstance(o, dict) and o.get("id"):
            ids.add(o["id"])
    return ids


# ---------------------------------------------------------------------------
# R1 — evidence-blind proposition analysis: input construction
# ---------------------------------------------------------------------------

def build_r1_user(candidate: dict) -> str:
    """Evidence-blind by construction: no source_snapshot, no canonical
    evidence, no seed_evidence_refs, no obs:N excerpt text — only each
    field's own prose (Correction 3)."""
    obs = candidate.get("additional_source_observations") or []
    lines = ["FIELD INSTANCES TO ANALYZE\n",
             "Produce exactly one field_audits entry for each source_field listed "
             "below -- no more, no fewer. Use these exact identifiers.\n"]
    for i, o in enumerate(obs):
        lines.append(f'source_field: additional_source_observations[{i}].observation\n'
                      f'text: "{o["observation"]}"\n')
    lines.append(f'source_field: engine_move\ntext: "{candidate.get("engine_move")}"\n')
    lines.append(f'source_field: seed_engagement\ntext: "{candidate.get("seed_engagement")}"\n')
    lines.append(f'source_field: interpretive_inference\ntext: "{candidate.get("interpretive_inference")}"\n')
    if candidate.get("conceptual_shift") is not None:
        lines.append(f'source_field: conceptual_shift\ntext: "{candidate.get("conceptual_shift")}"\n')
    lines.append(f'source_field: claimed_contribution\ntext: "{candidate.get("claimed_contribution")}"\n')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# R1 — field coverage + proposition-contract structural validation
# (schema_invalid enumeration per Correction 1)
# ---------------------------------------------------------------------------

def validate_r1(r1_parsed: dict, expected: list) -> dict:
    violations = []
    if not isinstance(r1_parsed, dict):
        return {"valid": False, "violations": ["r1_parsed is not a dict"]}

    field_audits = r1_parsed.get("field_audits")
    propositions = r1_parsed.get("propositions")
    if not isinstance(field_audits, list):
        violations.append("field_audits missing or not a list")
        field_audits = []
    if not isinstance(propositions, list):
        violations.append("propositions missing or not a list")
        propositions = []

    # -- field coverage (unchanged mechanism from B2_MODEL_OUTPUT_V1) --
    seen_fields = []
    for i, fa in enumerate(field_audits):
        if not isinstance(fa, dict):
            violations.append(f"field_audits[{i}] is not an object")
            continue
        sf = fa.get("source_field")
        seen_fields.append(sf)
        if sf not in expected:
            violations.append(f"field_audits[{i}].source_field {sf!r} is not an expected field for this candidate")
        no_aud = fa.get("no_auditable_propositions")
        cids = fa.get("claim_ids")
        if not isinstance(cids, list):
            violations.append(f"field_audits[{i}] ({sf!r}) claim_ids missing or not a list")
            cids = []
        if no_aud is True and len(cids) != 0:
            violations.append(f"field_audits[{i}] ({sf!r}) no_auditable_propositions=true but claim_ids is non-empty")
        if no_aud is False and len(cids) == 0:
            violations.append(f"field_audits[{i}] ({sf!r}) no_auditable_propositions=false but claim_ids is empty")
        if no_aud not in (True, False):
            violations.append(f"field_audits[{i}] ({sf!r}) no_auditable_propositions is not a boolean")

    missing = [f for f in expected if f not in seen_fields]
    extra = [f for f in seen_fields if f not in expected]
    dupes = [f for f in set(seen_fields) if seen_fields.count(f) > 1]
    for f in missing:
        violations.append(f"missing field_audits entry for expected field {f!r}")
    for f in extra:
        violations.append(f"field_audits entry for unexpected field {f!r}")
    for f in dupes:
        violations.append(f"field_audits has duplicate entries for field {f!r}")

    # -- proposition-contract structural invariants (NEW to v2) --
    claim_ids_seen = []
    props_by_id = {}
    for i, p in enumerate(propositions):
        if not isinstance(p, dict) or "claim_id" not in p:
            violations.append(f"propositions[{i}] missing claim_id")
            continue
        cid = p["claim_id"]
        if cid in props_by_id:
            violations.append(f"duplicate claim_id {cid!r} in propositions[]")
        props_by_id[cid] = p
        claim_ids_seen.append(cid)

        for req in ("surface_claim", "source_field", "world_truth_question", "concrete_restatement"):
            v = p.get(req)
            if not isinstance(v, str) or not v.strip():
                violations.append(f"proposition {cid}: {req} missing or empty (REQUIRED, unconditionally, "
                                   f"per Correction 2 — no not_applicable value is legal for any claim)")
        ed = p.get("empirical_dependency")
        if ed not in ALL_EMPIRICAL_DEPENDENCY:
            violations.append(f"proposition {cid}: empirical_dependency {ed!r} not in "
                               f"{sorted(ALL_EMPIRICAL_DEPENDENCY)}")

    # -- cross-reference field_audits <-> propositions (unchanged mechanism) --
    referenced = {}
    for fa in field_audits:
        if not isinstance(fa, dict):
            continue
        for cid in (fa.get("claim_ids") or []):
            referenced.setdefault(cid, []).append(fa.get("source_field"))

    for cid, refs in referenced.items():
        if len(refs) > 1:
            violations.append(f"claim_id {cid!r} referenced by more than one field_audits entry: {refs}")
        if cid not in props_by_id:
            violations.append(f"field_audits references claim_id {cid!r} which does not appear in propositions[]")
        else:
            claim_sf = props_by_id[cid].get("source_field")
            fa_sf = refs[0]
            if claim_sf != fa_sf:
                violations.append(
                    f"proposition {cid!r}.source_field={claim_sf!r} does not match the field_audits entry "
                    f"that references it (source_field={fa_sf!r})")

    for cid in claim_ids_seen:
        if cid not in referenced:
            violations.append(f"claim_id {cid!r} in propositions[] is never referenced by any field_audits entry")

    return {"valid": len(violations) == 0, "violations": violations, "props_by_id": props_by_id,
            "claim_id_order": claim_ids_seen}


# ---------------------------------------------------------------------------
# R2 — full-evidence role/support/declaration audit: input construction
# ---------------------------------------------------------------------------

def build_r2_user(seed: dict, candidate: dict, r1_props_by_id: dict, claim_id_order: list) -> str:
    ev_lines = "\n".join(f'{e["id"]}: "{e["excerpt"]}"' for e in seed["evidence"])
    parts = [
        "SEED FRICTION (resisting_detail is CONTEXT ONLY -- not factual authority; "
        "it cannot establish or rescue a factual dependency)\n",
        f"Resisting detail: {seed['resisting_detail']}\n",
        f"Canonical evidence:\n{ev_lines}\n",
        "CANDIDATE-DECLARED SEED EVIDENCE\n",
        f"seed_evidence_refs: {json.dumps(candidate.get('seed_evidence_refs') or [])}\n",
        "SOURCE SNAPSHOT\n",
        seed["source_snapshot"],
    ]
    obs = candidate.get("additional_source_observations") or []
    if obs:
        obs_lines = ["\nDECLARED EVIDENCE\n"]
        for o in obs:
            obs_lines.append(f'{o["id"]} excerpt:\n"{o["excerpt"]}"\n')
        parts.append("\n".join(obs_lines))

    prop_lines = ["\nFIXED PROPOSITION SET (produced by a separate evidence-blind pass -- "
                  "audit EXACTLY these claim_ids, no more, no fewer; independently form your "
                  "own role judgment, do not treat empirical_dependency as authoritative)\n"]
    for cid in claim_id_order:
        p = r1_props_by_id[cid]
        prop_lines.append(
            f'claim_id: {cid}\n'
            f'  source_field: {p["source_field"]}\n'
            f'  surface_claim: "{p["surface_claim"]}"\n'
            f'  world_truth_question: {p["world_truth_question"]}\n'
            f'  concrete_restatement: "{p["concrete_restatement"]}"\n'
            f'  empirical_dependency (earlier pass, non-authoritative): {p["empirical_dependency"]}\n'
        )
    parts.append("\n".join(prop_lines))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# R2 — claim-set-identity + structural invariants (schema_invalid enumeration)
# ---------------------------------------------------------------------------

def validate_r2(r2_parsed: dict, r1_claim_ids: list, declared_ids: set) -> dict:
    violations = []
    if not isinstance(r2_parsed, dict):
        return {"valid": False, "violations": ["r2_parsed is not a dict"]}
    claims = r2_parsed.get("claims")
    if not isinstance(claims, list):
        return {"valid": False, "violations": ["claims missing or not a list"]}

    r1_set = set(r1_claim_ids)
    seen_ids = []
    claims_by_id = {}
    for c in claims:
        if not isinstance(c, dict) or "claim_id" not in c:
            violations.append("a claims[] entry is missing claim_id")
            continue
        cid = c["claim_id"]
        if cid in claims_by_id:
            violations.append(f"duplicate claim_id {cid!r} in R2's claims[]")
        claims_by_id[cid] = c
        seen_ids.append(cid)

    r2_set = set(seen_ids)
    if r2_set != r1_set:
        missing = r1_set - r2_set
        extra = r2_set - r1_set
        if missing:
            violations.append(f"R2 omitted claim_id(s) R1 emitted: {sorted(missing)}")
        if extra:
            violations.append(f"R2 introduced claim_id(s) R1 never emitted: {sorted(extra)}")

    for cid, c in claims_by_id.items():
        role = c.get("role")
        support = c.get("support")
        declaration = c.get("declaration")
        declared_refs = c.get("declared_refs")
        problems = c.get("problems")
        auditor_evidence = c.get("auditor_evidence")
        why = c.get("why")
        r1_agreement = c.get("r1_agreement")
        override_rationale = c.get("override_rationale")

        if role not in ALL_ROLES:
            violations.append(f"claim {cid}: unknown role {role!r}")
            continue
        if not isinstance(declared_refs, list):
            violations.append(f"claim {cid}: declared_refs missing or not a list")
            declared_refs = []
        if not isinstance(problems, list):
            violations.append(f"claim {cid}: problems missing or not a list")
            problems = []
        if not isinstance(auditor_evidence, list):
            violations.append(f"claim {cid}: auditor_evidence missing or not a list")
            auditor_evidence = []
        if c.get("importance") not in ALL_IMPORTANCE:
            violations.append(f"claim {cid}: unknown importance {c.get('importance')!r}")
        for p in problems:
            if p not in ALL_PROBLEMS:
                violations.append(f"claim {cid}: unknown problems value {p!r}")

        if r1_agreement not in ALL_R1_AGREEMENT:
            violations.append(f"claim {cid}: r1_agreement {r1_agreement!r} not in {sorted(ALL_R1_AGREEMENT)}")
        elif r1_agreement == "override":
            if not isinstance(override_rationale, str) or not override_rationale.strip():
                violations.append(f"claim {cid}: r1_agreement=override requires a non-empty "
                                   f"override_rationale (Correction 1 — presence, not content, is checked)")
        elif r1_agreement == "consistent" and override_rationale not in (None, ""):
            violations.append(f"claim {cid}: r1_agreement=consistent but override_rationale is non-null "
                               f"— should be null when there is no disagreement")

        if role == "interpretive_only":
            if support != "not_required":
                violations.append(f"claim {cid}: interpretive_only requires support=not_required, got {support!r}")
            if declaration != "not_applicable":
                violations.append(f"claim {cid}: interpretive_only requires declaration=not_applicable, got {declaration!r}")
            if declared_refs != []:
                violations.append(f"claim {cid}: interpretive_only requires declared_refs=[], got {declared_refs!r}")

        elif role == "boundary_ambiguous":
            if support != "uncertain":
                violations.append(f"claim {cid}: boundary_ambiguous requires support=uncertain, got {support!r}")
            if declaration != "uncertain":
                violations.append(f"claim {cid}: boundary_ambiguous requires declaration=uncertain, got {declaration!r}")
            if declared_refs != []:
                violations.append(f"claim {cid}: boundary_ambiguous requires declared_refs=[], got {declared_refs!r}")

        elif role == "factual_dependency":
            if support not in {"supported", "unsupported", "uncertain"}:
                violations.append(f"claim {cid}: factual_dependency requires support in "
                                   f"supported|unsupported|uncertain, got {support!r}")
            if declaration not in {"declared", "undeclared"}:
                violations.append(f"claim {cid}: factual_dependency requires declaration in "
                                   f"declared|undeclared, got {declaration!r}")

            if declaration == "declared":
                if len(declared_refs) < 1:
                    violations.append(f"claim {cid}: declaration=declared requires non-empty declared_refs")
                else:
                    bad = [r for r in declared_refs if r not in declared_ids]
                    if bad:
                        violations.append(
                            f"claim {cid}: declared_refs {bad} not in this candidate's ACTUAL declared "
                            f"evidence set {sorted(declared_ids)}")
            elif declaration == "undeclared":
                if declared_refs != []:
                    violations.append(f"claim {cid}: declaration=undeclared requires declared_refs=[], "
                                       f"got {declared_refs!r}")

            if support == "supported":
                if not any(isinstance(e, dict) and e.get("relation") == "supports_claim" for e in auditor_evidence):
                    violations.append(f"claim {cid}: support=supported requires >=1 auditor_evidence "
                                       f"entry with relation=supports_claim")
            elif support == "unsupported":
                if not any(isinstance(e, dict) and e.get("relation") == "does_not_establish_claim" for e in auditor_evidence):
                    violations.append(f"claim {cid}: support=unsupported requires >=1 auditor_evidence "
                                       f"entry with relation=does_not_establish_claim")
                if not why:
                    violations.append(f"claim {cid}: support=unsupported requires non-empty why")
                if not (SEMANTIC_PROBLEMS & set(problems)):
                    violations.append(f"claim {cid}: support=unsupported requires >=1 semantic problem "
                                       f"value in problems, got {problems!r}")

            if declaration == "undeclared" and "undeclared_factual_dependency" not in problems:
                violations.append(f"claim {cid}: declaration=undeclared requires "
                                   f"'undeclared_factual_dependency' in problems, got {problems!r}")

    return {"valid": len(violations) == 0, "violations": violations, "claims_by_id": claims_by_id}


# ---------------------------------------------------------------------------
# Layer 1 — auditor-evidence provenance (unchanged mechanism, wraps, never mutates)
# ---------------------------------------------------------------------------

def validate_auditor_evidence(claims_by_id: dict, source_snapshot: str) -> dict:
    out = {}
    for cid, c in claims_by_id.items():
        entries = c.get("auditor_evidence") or []
        entry_results = []
        for e in entries:
            if not isinstance(e, dict):
                entry_results.append({"excerpt": None, "relation": None, "valid": False,
                                       "resolver_status": None, "violations": ["entry is not an object"]})
                continue
            excerpt = e.get("excerpt", "")
            if excerpt and excerpt in source_snapshot:
                entry_results.append({"excerpt": excerpt, "relation": e.get("relation"),
                                       "valid": True, "resolver_status": "exact_match", "violations": []})
                continue
            diag = resolve_anchor(excerpt or "", source_snapshot, title=None)
            valid = diag["status"] == "normalized_unique_match"
            v = [] if valid else [f"auditor_evidence excerpt not a real substring "
                                   f"(resolver diagnostic: {diag['status']}): {excerpt!r}"]
            entry_results.append({"excerpt": excerpt, "relation": e.get("relation"),
                                   "valid": valid, "resolver_status": diag["status"], "violations": v})
        out[cid] = {
            "valid": all(er["valid"] for er in entry_results) if entry_results else True,
            "entries": entry_results,
            "violations": [v for er in entry_results for v in er["violations"]],
        }
    return out


# ---------------------------------------------------------------------------
# Layer 1.5 (NEW) — R1/R2 semantic consistency, per Correction 5's exhaustive table
# ---------------------------------------------------------------------------

def compute_consistency(props_by_id: dict, claims_by_id: dict) -> dict:
    """Reads ONLY R1.empirical_dependency and R2.role — never r1_agreement,
    never override_rationale (Correction 1's closing paragraph, Correction 5).
    Returns {claim_id: "consistent"|"r1_r2_escalation"|"r1_uncertain_resolved"
    |"R1_R2_SEMANTIC_CONFLICT"}."""
    out = {}
    for cid, c in claims_by_id.items():
        p = props_by_id.get(cid)
        if p is None:
            # Should never happen if validate_r2's claim-id-set check already
            # passed — defensive, not a new code path this design relies on.
            out[cid] = "unknown_no_r1_proposition"
            continue
        ed = p["empirical_dependency"]
        role = c.get("role")

        if ed == "uncertain":
            out[cid] = "r1_uncertain_resolved"
        elif ed == "true" and role == "interpretive_only":
            out[cid] = "R1_R2_SEMANTIC_CONFLICT"
        elif ed == "true" and role in ("factual_dependency", "boundary_ambiguous"):
            out[cid] = "consistent"
        elif ed == "false" and role == "factual_dependency":
            out[cid] = "r1_r2_escalation"
        elif ed == "false" and role in ("interpretive_only", "boundary_ambiguous"):
            out[cid] = "consistent"
        else:
            out[cid] = "unknown_combination"
    return out


# ---------------------------------------------------------------------------
# Layer 2 — effective_status / effective_verdict, ONE new branch inserted
# ahead of the existing role/support branch (Correction 1)
# ---------------------------------------------------------------------------

def compute_effective_v2(claims_by_id: dict, evidence_validation: dict, consistency: dict) -> dict:
    per_claim = {}
    any_unsafe = False
    any_ambiguous = False

    for cid, c in claims_by_id.items():
        role = c.get("role")
        support = c.get("support")
        declaration = c.get("declaration")
        ev = evidence_validation.get(cid, {"valid": True, "entries": []})
        cons = consistency.get(cid)

        if cons == "R1_R2_SEMANTIC_CONFLICT":
            effective_status = "unresolved_semantic_conflict"
        elif role in ("interpretive_only", "boundary_ambiguous"):
            effective_status = support
        elif role == "factual_dependency" and support == "uncertain":
            effective_status = "uncertain"
        elif role == "factual_dependency" and support in ("supported", "unsupported"):
            relevant_relation = "supports_claim" if support == "supported" else "does_not_establish_claim"
            relevant_valid = any(
                e.get("relation") == relevant_relation and e.get("valid")
                for e in ev.get("entries", [])
            )
            effective_status = support if relevant_valid else "audit_unresolved"
        else:
            effective_status = "unknown"

        per_claim[cid] = {
            "role": role, "support": support, "declaration": declaration,
            "consistency": cons, "effective_status": effective_status,
        }

        if cons == "R1_R2_SEMANTIC_CONFLICT":
            any_ambiguous = True
        elif role == "factual_dependency":
            if effective_status == "unsupported" or declaration == "undeclared":
                any_unsafe = True
            elif effective_status in ("uncertain", "audit_unresolved"):
                any_ambiguous = True
        elif role == "boundary_ambiguous":
            any_ambiguous = True

    if any_unsafe:
        verdict = "unsafe"
    elif any_ambiguous:
        verdict = "ambiguous"
    else:
        verdict = "safe"

    return {"per_claim": per_claim, "effective_verdict": verdict}


# ---------------------------------------------------------------------------
# Full candidate pipeline: Layer 0 (run_status) -> Layer 1 -> 1.5 -> 2
# ---------------------------------------------------------------------------

def run_candidate_pipeline_v2(seed: dict, candidate: dict, r1_call: dict, r2_call: dict) -> dict:
    # Layer 0a — R1 run status
    if r1_call.get("parsed") is None:
        r1_status = "call_failed" if r1_call.get("raw") is None else "schema_invalid"
    else:
        r1_status = None  # resolved below after structural validation

    if r1_status in ("call_failed", "schema_invalid"):
        return {
            "b2v2_run_status": r1_status,
            "stage": "r1",
            "r1_result": r1_call.get("parsed"),
            "r1_validation": None,
            "r2_result": None,
            "r2_validation": None,
            "auditor_evidence_validation": None,
            "consistency": None,
            "effective_verdict": "not_computed",
            "per_claim_effective": None,
            "raw_error": r1_call.get("error"),
        }

    r1_parsed = r1_call["parsed"]
    expected = expected_fields(candidate)
    r1_validation = validate_r1(r1_parsed, expected)
    if not r1_validation["valid"]:
        return {
            "b2v2_run_status": "schema_invalid",
            "stage": "r1",
            "r1_result": r1_parsed,
            "r1_validation": r1_validation,
            "r2_result": None,
            "r2_validation": None,
            "auditor_evidence_validation": None,
            "consistency": None,
            "effective_verdict": "not_computed",
            "per_claim_effective": None,
            "raw_error": None,
        }

    props_by_id = r1_validation["props_by_id"]
    claim_id_order = r1_validation["claim_id_order"]

    # Layer 0b — R2 run status
    if r2_call.get("parsed") is None:
        r2_status = "call_failed" if r2_call.get("raw") is None else "schema_invalid"
        return {
            "b2v2_run_status": r2_status,
            "stage": "r2",
            "r1_result": r1_parsed,
            "r1_validation": r1_validation,
            "r2_result": r2_call.get("parsed"),
            "r2_validation": None,
            "auditor_evidence_validation": None,
            "consistency": None,
            "effective_verdict": "not_computed",
            "per_claim_effective": None,
            "raw_error": r2_call.get("error"),
        }

    r2_parsed = r2_call["parsed"]
    declared_ids = declared_evidence_set(candidate)
    r2_validation = validate_r2(r2_parsed, claim_id_order, declared_ids)
    if not r2_validation["valid"]:
        return {
            "b2v2_run_status": "schema_invalid",
            "stage": "r2",
            "r1_result": r1_parsed,
            "r1_validation": r1_validation,
            "r2_result": r2_parsed,
            "r2_validation": r2_validation,
            "auditor_evidence_validation": None,
            "consistency": None,
            "effective_verdict": "not_computed",
            "per_claim_effective": None,
            "raw_error": None,
        }

    claims_by_id = r2_validation["claims_by_id"]
    ev_validation = validate_auditor_evidence(claims_by_id, seed["source_snapshot"])
    consistency = compute_consistency(props_by_id, claims_by_id)
    effective = compute_effective_v2(claims_by_id, ev_validation, consistency)

    return {
        "b2v2_run_status": "valid",
        "stage": "complete",
        "r1_result": r1_parsed,
        "r1_validation": r1_validation,
        "r2_result": r2_parsed,
        "r2_validation": r2_validation,
        "auditor_evidence_validation": ev_validation,
        "consistency": consistency,
        "effective_verdict": effective["effective_verdict"],
        "per_claim_effective": effective["per_claim"],
        "raw_error": None,
    }


# ---------------------------------------------------------------------------
# Bidirectional migration-report support (Correction 5's "(a) within-run" +
# the doc's "(b) cross-version" tables). Pure functions over already-computed
# results — no fixture-specific matching hardcoded here, since no real v2
# run exists yet; a regression script supplies its own claim-content key.
# ---------------------------------------------------------------------------

def within_run_consistency_report(all_consistency: list) -> dict:
    """all_consistency: list of per-candidate `consistency` dicts (claim_id ->
    state). Returns counts/rates for the 4 states plus the self-report-mismatch
    diagnostic (R2 said 'consistent' but the deterministic layer disagreed)."""
    counts = {"consistent": 0, "r1_r2_escalation": 0, "r1_uncertain_resolved": 0,
              "R1_R2_SEMANTIC_CONFLICT": 0}
    total = 0
    for cmap in all_consistency:
        for state in cmap.values():
            if state in counts:
                counts[state] += 1
            total += 1
    rates = {k: (v / total if total else None) for k, v in counts.items()}
    return {"counts": counts, "rates": rates, "total_claims": total}


def self_report_mismatch_report(all_claims_by_id: list, all_consistency: list) -> dict:
    mismatches = []
    for claims_by_id, cmap in zip(all_claims_by_id, all_consistency):
        for cid, c in claims_by_id.items():
            if c.get("r1_agreement") == "consistent" and cmap.get(cid) == "R1_R2_SEMANTIC_CONFLICT":
                mismatches.append(cid)
    return {"count": len(mismatches), "claim_ids": mismatches}


ROLE_TRANSITION_DIRECTIONS = [
    ("interpretive_only", "factual_dependency"),
    ("factual_dependency", "interpretive_only"),
    ("interpretive_only", "boundary_ambiguous"),
    ("factual_dependency", "boundary_ambiguous"),
    ("boundary_ambiguous", "interpretive_only"),
    ("boundary_ambiguous", "factual_dependency"),
]

VERDICT_TRANSITION_DIRECTIONS = [
    ("safe", "unsafe"), ("unsafe", "safe"),
    ("safe", "ambiguous"), ("unsafe", "ambiguous"),
    ("ambiguous", "safe"), ("ambiguous", "unsafe"),
]


def effective_role_for_migration(role: str, consistency_state: str) -> str:
    """v2's EFFECTIVE role for cross-version comparison purposes: a claim
    under R1_R2_SEMANTIC_CONFLICT compares as boundary_ambiguous (the bucket
    it effectively resolves into), with the raw role still reported
    separately by the caller so the distinction is never lost."""
    if consistency_state == "R1_R2_SEMANTIC_CONFLICT":
        return "boundary_ambiguous"
    return role


def role_migration_table(baseline_roles: dict, v2_effective_roles: dict) -> dict:
    """baseline_roles / v2_effective_roles: {claim_content_key: role}. Caller
    supplies the content-matching key (claim text, not claim_id — ids are not
    stable across versions/re-decomposition, per the doc's existing
    convention). Returns counts for all 6 named directions, none bundled."""
    counts = {f"{a}->{b}": 0 for a, b in ROLE_TRANSITION_DIRECTIONS}
    for key, old_role in baseline_roles.items():
        new_role = v2_effective_roles.get(key)
        if new_role is None or new_role == old_role:
            continue
        direction = f"{old_role}->{new_role}"
        if direction in counts:
            counts[direction] += 1
    return counts


def verdict_migration_table(baseline_verdicts: dict, v2_verdicts: dict) -> dict:
    counts = {f"{a}->{b}": 0 for a, b in VERDICT_TRANSITION_DIRECTIONS}
    for key, old_v in baseline_verdicts.items():
        new_v = v2_verdicts.get(key)
        if new_v is None or new_v == old_v:
            continue
        direction = f"{old_v}->{new_v}"
        if direction in counts:
            counts[direction] += 1
    return counts


def identity_restatement_rate(props_by_id: dict) -> dict:
    """Diagnostic-only metric flagged as a NEW risk in the design doc
    (Correction 2's risk list) — fraction of propositions whose
    concrete_restatement is exactly or near-exactly equal to surface_claim.
    No threshold is chosen here; this is measurement infrastructure only."""
    total = len(props_by_id)
    identical = 0
    for p in props_by_id.values():
        a = (p.get("surface_claim") or "").strip().lower()
        b = (p.get("concrete_restatement") or "").strip().lower()
        if a == b:
            identical += 1
    return {"identical": identical, "total": total,
            "rate": (identical / total if total else None)}


# ---------------------------------------------------------------------------
# Main — NOT EXECUTED against a real model in this pass (per instruction).
# Prepared so a future explicitly-authorized run can invoke it unchanged.
# ---------------------------------------------------------------------------

def _load_fresh_targets():
    mapping = json.loads(FRESH_MAPPING_PATH.read_text())["mapping"]
    return mapping  # [{"h_id": "H01", "slug": "...", "engine_label": "P"}, ...]


def _iter_dev_candidates():
    for slug in REFERENCE_SLUGS:
        seed = json.loads((REFERENCE_SEED_DIR / f"{slug}_canonical_seed.json").read_text())
        stage_a = json.loads((REFERENCE_RESULTS_DIR / f"{slug}_stage_a.json").read_text())
        for label in ENGINE_LABELS:
            candidate = stage_a[label].get("parsed")
            if candidate is None or candidate.get("status") != "candidate":
                continue
            yield f"{slug}/{label}", seed, candidate


def _iter_fresh_candidates():
    for t in _load_fresh_targets():
        h_id, slug, label = t["h_id"], t["slug"], t["engine_label"]
        seed = json.loads((FRESH_BATCH_DIR / f"{slug}_canonical_seed.json").read_text())
        stage_a = json.loads((FRESH_RESULTS_DIR / f"{slug}_stage_a.json").read_text())
        candidate = stage_a[label]["parsed"]
        yield h_id, seed, candidate


def run_one_candidate(key: str, seed: dict, candidate: dict) -> dict:
    r1_user = build_r1_user(candidate)
    r1_call = _call(R1_SYSTEM, r1_user)

    r1_parsed = r1_call.get("parsed")
    if r1_parsed is None:
        return run_candidate_pipeline_v2(seed, candidate, r1_call, {"parsed": None, "raw": None, "error": "r1_failed_no_r2_call"})

    expected = expected_fields(candidate)
    r1_check = validate_r1(r1_parsed, expected)
    if not r1_check["valid"]:
        # R2 is never called against a structurally invalid R1 output —
        # there is no fixed claim set to audit against.
        return run_candidate_pipeline_v2(seed, candidate, r1_call, {"parsed": None, "raw": None, "error": "r1_schema_invalid_no_r2_call"})

    r2_user = build_r2_user(seed, candidate, r1_check["props_by_id"], r1_check["claim_id_order"])
    r2_call = _call(R2_SYSTEM, r2_user)
    return run_candidate_pipeline_v2(seed, candidate, r1_call, r2_call)


def main():
    raise SystemExit(
        "cj2_b2_v2_probe.py.main() is prepared but NOT authorized to run in this "
        "pass — B2 v2 has made zero API calls, per explicit instruction. Invoke "
        "run_one_candidate() directly, with explicit go-ahead, once that changes."
    )


if __name__ == "__main__":
    main()
