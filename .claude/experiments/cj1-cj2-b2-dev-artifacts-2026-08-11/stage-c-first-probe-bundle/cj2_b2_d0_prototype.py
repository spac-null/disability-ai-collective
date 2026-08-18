#!/usr/bin/env python3
"""
cj2_b2_d0_prototype.py — B2 NEXT-STRUCTURE PROTOTYPE — D0/R1/R2.
EXPERIMENT-ONLY. NO MODEL CALLS. Not v2.1. Does not modify, import, or
touch any frozen cj2-stage-b2-v2 artifact (cj2_b2_v2_probe.py, its frozen
prompts, or acceptance-matrix-v2-preregistered.json) and does not modify
production article generation.

Implements the deterministic, code-computed half of the D0/R1/R2 design
in `.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md`
`## B2 NEXT-STRUCTURE DESIGN — D0/R1/R2`, REVISED per the 2026-08-12
adversarial coverage audit (`## B2 NEXT-STRUCTURE PROTOTYPE — ADVERSARIAL
COVERAGE AUDIT`) and the follow-up decision to accept Option B (explicit
ID-based segment accounting) as deterministic bookkeeping, paired with a
SEPARATE semantic checker (C0, in `cj2_b2_c0_prototype.py`) for the
completeness question bookkeeping alone cannot answer:

  candidate fields -> D0 (schema/structure defined here; NO model call
                       this pass) -> deterministic segment-accounting
                       validator (THIS FILE) -> C0 semantic audit
                       (cj2_b2_c0_prototype.py, separate file) ->
                       fixed-claim handoff check -> effective status.

D0's SINGLE semantic responsibility: identify the propositions present
in candidate text. D0 must NOT decide empirical_dependency,
interpretive_only/factual_dependency role, support, declaration, or
safe/unsafe — none of that vocabulary appears below. It remains
evidence-blind: this module never reads a source_snapshot, only the
candidate's own generated fields.

D0 OUTPUT SCHEMA (versioned; bump D0_SCHEMA_VERSION on any change):

    {
      "claims": [
        {"claim_id": str, "source_field": str, "segment_ids": [str, ...],
         "exact_surface_span": str, "atomic_claim": str}, ...
      ],
      "non_propositional": [
        {"non_prop_id": str, "source_field": str, "segment_ids": [str, ...],
         "exact_surface_span": str,
         "reason_code": one of NON_PROPOSITIONAL_REASON_CODES,
         "reason_note": str}, ...
      ]
    }

REVISION (2026-08-12, this pass): `segment_ids` is now a REQUIRED field
on every claim/non_propositional record — explicit bookkeeping (Option
B), not inferred from span-overlap heuristics. `exact_surface_span` is
still required and still resolved via the same quote-fold algorithm
already validated for CJ-1 v3 anchors (`cj1_v3_anchor_resolver.
resolve_anchor`) — D0 is still not permitted to paraphrase away claim
identity. The two are cross-checked for CONSISTENCY (see
`validate_segment_id_consistency` below): a claim's declared
`segment_ids` must equal exactly the set of deterministic segments its
resolved span geometrically overlaps — no more, no fewer. This removes
the prior version's `MIN_OVERLAP_FRACTION` heuristic entirely (kept
below, commented, as a superseded historical marker, not used by any
current function) — coverage is now a plain, threshold-free set
membership check: every deterministic `segment_id` must appear in the
union of declared `segment_ids` across claims and non_propositional
records, or it is not covered. No fraction, no ambiguity about partial
overlap.

**CRITICAL, CORRECTED FRAMING FROM THE ADVERSARIAL AUDIT — READ BEFORE
TRUSTING THIS FILE'S OUTPUT AS "COMPLETE":** this segment-accounting
mechanism (Option B) is explicit, unambiguous, deterministic bookkeeping.
**It is NOT a semantic completeness check and must never be described,
documented, or relied on as one.** A claim whose `exact_surface_span`
covers an entire segment, and whose declared `segment_ids` correctly and
consistently names that segment, STILL mechanically satisfies this
file's coverage check even if its `atomic_claim` text represents only
one of two or three propositions actually asserted within that
segment's text — the adversarial audit (`automation/
cj2_b2_d0_adversarial_coverage_audit.py`) demonstrated this directly, in
6/6 generic cases, and confirmed it is not hypothetical (the real,
already-selected H17 sentence has exactly this shape). Detecting THAT
failure class is C0's job (`cj2_b2_c0_prototype.py`), not this file's.
Anything in this module's docstrings from the PRIOR pass that called
segment-level surface coverage "the coverage contract" or implied it
established proposition completeness has been superseded by this
correction.

SEGMENTATION DECISION (resolved, documented, not left open) — UNCHANGED
from the prior pass, not reopened by this revision:
  Smallest deterministic unit chosen: sentence-level, further split on
  semicolons into clause-level units. Colons are DELIBERATELY NOT a
  split point (would fragment single atomic claims more often than it
  would correctly separate two, per real H14 material). Semicolons
  reliably separate independent clauses in this material. Bullet/
  numbered list lines are treated as line-level units before sentence/
  clause splitting. Coordinating-conjunction splitting ("and", "but")
  inside an already-single sentence is explicitly NOT attempted — this
  is now KNOWN, not merely flagged, to be one concrete way a semantic
  omission can hide inside a single segment (per the adversarial audit)
  — solving it is explicitly NOT attempted by adding more punctuation
  split points (per instruction: that just relocates the same gap to
  whichever conjunction/em-dash a future fixture happens to use, as H17
  already demonstrates). NOT a full linguistic parser.

FAIL-CLOSED PRIORITY (most severe first): schema_invalid >
span_resolution_failed > segment_id_consistency_failed >
D0_COVERAGE_FAILURE > valid. `D0_COVERAGE_FAILURE` (this file's own
structural finding, previously named `coverage_incomplete` — renamed
this pass for an explicit, distinct diagnostic identity) and
`R1_R2_SEMANTIC_CONFLICT`/`unresolved_semantic_conflict` (defined in
cj2_b2_v2_probe.py, untouched by this module) are DIFFERENT failure
classes and must never be conflated in diagnostics: a coverage failure
means a proposition may never reach the factuality audit at all; a
semantic conflict means two stages disagreed about a proposition both
stages saw.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from cj1_v3_anchor_resolver import resolve_anchor  # noqa: E402 -- reused, not reinvented

D0_SCHEMA_VERSION = "d0-prototype-0.2"

NON_PROPOSITIONAL_REASON_CODES = [
    "heading_or_label",
    "citation_or_reference",
    "connective_only_fragment",
    "formatting_artifact",
    "purely_rhetorical_transition",
    "other",
]

# SUPERSEDED 2026-08-12 by ID-based segment accounting (Option B) --
# kept only as a historical marker of what this file used to compute
# coverage with. No current function reads this constant.
_SUPERSEDED_MIN_OVERLAP_FRACTION = 0.5

_BULLET_LINE_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
_SENT_BOUNDARY_RE = re.compile(r"(?<=[.!?])(?=\s+[A-Z0-9\"‘’“”]|\s*$)")
_SUBSTANTIVE_RE = re.compile(r"[A-Za-z]{2,}")


def _substantive(text: str) -> bool:
    """A segment is 'substantive' if it contains at least one real word
    -- filters out stray leftover punctuation/whitespace artifacts from
    splitting (e.g. a lone dash left over after a semicolon split)."""
    return bool(_SUBSTANTIVE_RE.search(text))


def _split_sentences(text: str) -> list[str]:
    parts = []
    last = 0
    for m in _SENT_BOUNDARY_RE.finditer(text):
        parts.append(text[last:m.start()])
        last = m.start()
    parts.append(text[last:])
    return parts


def segment_field(field_text: str) -> list[dict]:
    """Deterministic segmentation of one candidate field's raw text.

    Returns an ordered list of {"segment_id", "text", "start", "end"}.
    `start`/`end` are character offsets into `field_text`. Every
    returned `text` is an EXACT substring of `field_text` (segments are
    produced by splitting the field's own text, never by paraphrasing
    it) -- offsets are located via plain `str.find`, not the
    quote-folding resolver (that resolver exists for claim spans a
    MODEL retyped; a segment is never retyped, so exact match is
    guaranteed by construction).
    """
    segments: list[dict] = []
    seg_counter = 0
    search_from = 0

    lines = field_text.split("\n")
    line_units: list[str] = list(lines)

    cursor = 0
    for line in line_units:
        line_start = field_text.find(line, cursor)
        cursor = line_start + len(line)
        if not line.strip():
            continue
        # Bullet-marker lines are kept as one line-level unit before
        # sentence splitting (marker retained in the span so the span
        # remains an exact substring of field_text).
        is_bullet = bool(_BULLET_LINE_RE.match(line))
        sentence_units = [line] if is_bullet else _split_sentences(line)
        for sent in sentence_units:
            clauses = sent.split(";")
            # Re-attach the semicolon to the clause that precedes it so
            # each clause is still an exact substring when re-located,
            # and so no information (the semicolon itself) is silently
            # dropped from any clause's own span.
            rebuilt = []
            for i, c in enumerate(clauses):
                rebuilt.append(c + (";" if i < len(clauses) - 1 else ""))
            for piece in rebuilt:
                stripped = piece.strip()
                if not stripped or not _substantive(stripped):
                    continue
                start = field_text.find(stripped, search_from)
                if start == -1:
                    # Stripping can shift the match earlier than
                    # search_from in pathological whitespace cases;
                    # fall back to a field-wide search rather than
                    # silently dropping the segment.
                    start = field_text.find(stripped)
                end = start + len(stripped)
                seg_counter += 1
                segments.append({
                    "segment_id": f"seg{seg_counter}",
                    "text": stripped,
                    "start": start,
                    "end": end,
                })
                search_from = max(search_from, end)
    return segments


def segment_field_map(candidate_fields: dict) -> dict:
    """Convenience: {field_name: segment_field(text)} for every field.
    Computed once, reused by validators and by test/tooling callers that
    need the deterministic segment_ids for a field (e.g. to derive a
    claim's correct segment_ids from its resolved span)."""
    return {name: segment_field(text) for name, text in candidate_fields.items()}


def _resolve_span_offset(excerpt: str, field_text: str) -> dict:
    """Wraps resolve_anchor and, on a resolvable match, also returns the
    character offset of the RECOVERED original substring in field_text
    -- needed for the segment_ids consistency check, which resolve_anchor
    alone doesn't compute."""
    r = resolve_anchor(excerpt, field_text, title=None)
    if r["status"] in ("exact_match", "normalized_unique_match") and r["original_substring"] is not None:
        start = field_text.find(r["original_substring"])
        if start != -1:
            r["start"] = start
            r["end"] = start + len(r["original_substring"])
        else:
            # Should not happen given resolve_anchor's own contract, but
            # fail closed rather than silently trusting an unlocatable
            # offset.
            r["status"] = "no_match"
            r["start"] = None
            r["end"] = None
    else:
        r["start"] = None
        r["end"] = None
    return r


# Public alias -- cj2_b2_c0_prototype.py (and any other module) should
# import this name rather than the underscore-prefixed one; the
# underscore name is kept for backward-compatible internal call sites
# in this file only.
def resolve_span_offset(excerpt: str, field_text: str) -> dict:
    return _resolve_span_offset(excerpt, field_text)


def segment_ids_overlapping_span(segments: list[dict], start: int, end: int) -> list[str]:
    """Pure geometry: which of `segments`' character ranges intersect
    [start, end) at all (any nonzero overlap, no fraction/threshold).
    Used both by the consistency validator (to check D0's self-reported
    segment_ids against reality) and, as a convenience for tests/tooling
    that don't want to hand-compute segment_ids, by
    `auto_segment_ids_for_span` below."""
    return [
        seg["segment_id"] for seg in segments
        if min(end, seg["end"]) - max(start, seg["start"]) > 0
    ]


def auto_segment_ids_for_span(field_text: str, segments: list[dict], exact_surface_span: str) -> list[str]:
    """TEST/TOOLING CONVENIENCE ONLY -- not something a real D0 model
    call can use, since the model must self-report segment_ids as part
    of producing its claims (that self-report is exactly what
    `validate_segment_id_consistency` checks). Resolves a span the same
    way the real validator would, then returns the segment_ids it
    geometrically overlaps -- lets test fixtures avoid hand-computing
    offsets while still exercising the real resolution/geometry code
    paths."""
    r = _resolve_span_offset(exact_surface_span, field_text)
    if r["start"] is None:
        return []
    return segment_ids_overlapping_span(segments, r["start"], r["end"])


def validate_d0_schema(d0_output: dict, candidate_fields: dict) -> dict:
    """Structural-only validation -- no coverage judgment here. Returns
    {"valid": bool, "violations": [str, ...]}."""
    violations = []
    if not isinstance(d0_output, dict):
        return {"valid": False, "violations": ["d0_output is not a dict"]}

    claims = d0_output.get("claims")
    non_props = d0_output.get("non_propositional")
    if not isinstance(claims, list):
        violations.append("missing or non-list 'claims'")
        claims = []
    if not isinstance(non_props, list):
        violations.append("missing or non-list 'non_propositional'")
        non_props = []

    seen_claim_ids = set()
    for i, c in enumerate(claims):
        if not isinstance(c, dict):
            violations.append(f"claims[{i}] is not a dict")
            continue
        for key in ("claim_id", "source_field", "exact_surface_span", "atomic_claim"):
            if not isinstance(c.get(key), str) or not c.get(key).strip():
                violations.append(f"claims[{i}] missing/empty required field '{key}'")
        seg_ids = c.get("segment_ids")
        if not isinstance(seg_ids, list) or not seg_ids or not all(isinstance(s, str) and s.strip() for s in seg_ids):
            violations.append(f"claims[{i}] missing/empty/malformed required field 'segment_ids' (must be a non-empty list of strings)")
        cid = c.get("claim_id")
        if cid is not None:
            if cid in seen_claim_ids:
                violations.append(f"duplicate claim_id '{cid}'")
            seen_claim_ids.add(cid)
        sf = c.get("source_field")
        if sf is not None and sf not in candidate_fields:
            violations.append(f"claims[{i}] references unknown source_field '{sf}'")

    seen_np_ids = set()
    for i, n in enumerate(non_props):
        if not isinstance(n, dict):
            violations.append(f"non_propositional[{i}] is not a dict")
            continue
        for key in ("non_prop_id", "source_field", "exact_surface_span", "reason_code"):
            if not isinstance(n.get(key), str) or not n.get(key).strip():
                violations.append(f"non_propositional[{i}] missing/empty required field '{key}'")
        seg_ids = n.get("segment_ids")
        if not isinstance(seg_ids, list) or not seg_ids or not all(isinstance(s, str) and s.strip() for s in seg_ids):
            violations.append(f"non_propositional[{i}] missing/empty/malformed required field 'segment_ids' (must be a non-empty list of strings)")
        npid = n.get("non_prop_id")
        if npid is not None:
            if npid in seen_np_ids:
                violations.append(f"duplicate non_prop_id '{npid}'")
            seen_np_ids.add(npid)
        rc = n.get("reason_code")
        if rc is not None and rc not in NON_PROPOSITIONAL_REASON_CODES:
            violations.append(f"non_propositional[{i}] illegal reason_code '{rc}'")
        sf = n.get("source_field")
        if sf is not None and sf not in candidate_fields:
            violations.append(f"non_propositional[{i}] references unknown source_field '{sf}'")

    return {"valid": len(violations) == 0, "violations": violations}


def validate_span_resolution(d0_output: dict, candidate_fields: dict) -> dict:
    """Checks every claim/non_propositional exact_surface_span actually
    resolves against its source_field's raw text. Distinct from schema
    validation (a span can be well-formed as a string and still not
    exist in the field text -- that's this check's job, not
    validate_d0_schema's)."""
    failures = []
    resolutions = {"claims": [], "non_propositional": []}
    for c in d0_output.get("claims", []) or []:
        sf = c.get("source_field")
        field_text = candidate_fields.get(sf, "")
        r = _resolve_span_offset(c.get("exact_surface_span", ""), field_text)
        resolutions["claims"].append({"claim_id": c.get("claim_id"), **r})
        if r["status"] not in ("exact_match", "normalized_unique_match"):
            failures.append(f"claim '{c.get('claim_id')}' span resolution: {r['status']} ({r['detail']})")
    for n in d0_output.get("non_propositional", []) or []:
        sf = n.get("source_field")
        field_text = candidate_fields.get(sf, "")
        r = _resolve_span_offset(n.get("exact_surface_span", ""), field_text)
        resolutions["non_propositional"].append({"non_prop_id": n.get("non_prop_id"), **r})
        if r["status"] not in ("exact_match", "normalized_unique_match"):
            failures.append(f"non_propositional '{n.get('non_prop_id')}' span resolution: {r['status']} ({r['detail']})")
    return {"valid": len(failures) == 0, "violations": failures, "resolutions": resolutions}


def validate_segment_id_consistency(d0_output: dict, candidate_fields: dict, span_res: dict) -> dict:
    """THE bookkeeping-integrity check for Option B. A claim/non_prop's
    DECLARED `segment_ids` must equal EXACTLY (not a subset, not a
    superset) the set of segment_ids its RESOLVED exact_surface_span
    geometrically overlaps. Any mismatch means D0's own bookkeeping is
    internally inconsistent -- either fabricated (claiming a segment the
    span doesn't touch) or incomplete (a span visibly spans a segment
    it didn't declare) -- and is treated as a structural failure, not a
    coverage question. Requires `span_res` (from validate_span_resolution)
    to already have resolved offsets; records with unresolvable spans
    are skipped here (already reported by validate_span_resolution)."""
    violations = []
    segments_by_field = segment_field_map(candidate_fields)
    resolved_claims = {r["claim_id"]: r for r in span_res["resolutions"]["claims"] if r["start"] is not None}
    resolved_nonprop = {r["non_prop_id"]: r for r in span_res["resolutions"]["non_propositional"] if r["start"] is not None}

    for c in d0_output.get("claims", []) or []:
        cid = c.get("claim_id")
        sf = c.get("source_field")
        declared = set(c.get("segment_ids") or [])
        r = resolved_claims.get(cid)
        if r is None or sf not in segments_by_field:
            continue
        actual = set(segment_ids_overlapping_span(segments_by_field[sf], r["start"], r["end"]))
        if declared != actual:
            violations.append(
                f"claim '{cid}': declared segment_ids {sorted(declared)} != "
                f"actual geometric overlap {sorted(actual)} for its resolved span"
            )

    for n in d0_output.get("non_propositional", []) or []:
        npid = n.get("non_prop_id")
        sf = n.get("source_field")
        declared = set(n.get("segment_ids") or [])
        r = resolved_nonprop.get(npid)
        if r is None or sf not in segments_by_field:
            continue
        actual = set(segment_ids_overlapping_span(segments_by_field[sf], r["start"], r["end"]))
        if declared != actual:
            violations.append(
                f"non_propositional '{npid}': declared segment_ids {sorted(declared)} != "
                f"actual geometric overlap {sorted(actual)} for its resolved span"
            )

    return {"valid": len(violations) == 0, "violations": violations}


def compute_coverage(candidate_fields: dict, d0_output: dict) -> dict:
    """THE segment-accounting coverage check (Option B) -- plain,
    threshold-free set membership. Independently segments every field,
    then checks whether every deterministic segment_id is named by the
    UNION of declared `segment_ids` across all claims and
    non_propositional records for that field. Does NOT recompute overlap
    itself (that's `validate_segment_id_consistency`'s job, run
    separately and required to pass first) -- this function trusts
    DECLARED segment_ids precisely because consistency was already
    verified elsewhere in the pipeline.

    CORRECTED FRAMING (see module docstring): this establishes
    SEGMENT-LEVEL surface accounting only. It does NOT establish that
    the claims covering a segment semantically represent everything
    that segment asserts -- see C0 (cj2_b2_c0_prototype.py) for that
    separate, distinct check."""
    per_field = []
    total_uncovered = 0
    fields_with_zero_references = []

    claims_by_field = {}
    for c in d0_output.get("claims", []) or []:
        claims_by_field.setdefault(c.get("source_field"), []).append(c)
    nonprop_by_field = {}
    for n in d0_output.get("non_propositional", []) or []:
        nonprop_by_field.setdefault(n.get("source_field"), []).append(n)

    for field_name, field_text in candidate_fields.items():
        field_claims = claims_by_field.get(field_name, [])
        field_nonprop = nonprop_by_field.get(field_name, [])
        if not field_name.startswith("_") and not field_claims and not field_nonprop:
            fields_with_zero_references.append(field_name)

        segments = segment_field(field_text)
        covered_ids = set()
        for c in field_claims:
            covered_ids.update(c.get("segment_ids") or [])
        for n in field_nonprop:
            covered_ids.update(n.get("segment_ids") or [])

        seg_reports = []
        for seg in segments:
            covering_claim_ids = [c.get("claim_id") for c in field_claims if seg["segment_id"] in (c.get("segment_ids") or [])]
            covering_non_prop_ids = [n.get("non_prop_id") for n in field_nonprop if seg["segment_id"] in (n.get("segment_ids") or [])]
            covered = seg["segment_id"] in covered_ids
            if not covered:
                total_uncovered += 1
            seg_reports.append({
                **seg,
                "covered": covered,
                "covering_claim_ids": covering_claim_ids,
                "covering_non_prop_ids": covering_non_prop_ids,
            })

        per_field.append({
            "source_field": field_name,
            "segment_count": len(segments),
            "uncovered_segments": [s for s in seg_reports if not s["covered"]],
            "segments": seg_reports,
        })

    return {
        "per_field": per_field,
        "coverage_complete": total_uncovered == 0,
        "total_uncovered_segments": total_uncovered,
        "fields_with_zero_references": fields_with_zero_references,
    }


def non_propositional_rate_report(d0_output: dict) -> dict:
    """Diagnostic only -- reports RATES, never trusts a non_propositional
    marking as correct merely because a reason_code/reason_note is
    present. 'other' usage is reported separately and should be
    reviewed, per instruction to be conservative about it."""
    non_props = d0_output.get("non_propositional", []) or []
    claims = d0_output.get("claims", []) or []
    total_segments_marked = len(non_props)
    total_units = total_segments_marked + len(claims)
    by_reason = {code: 0 for code in NON_PROPOSITIONAL_REASON_CODES}
    for n in non_props:
        rc = n.get("reason_code")
        if rc in by_reason:
            by_reason[rc] += 1
    return {
        "non_propositional_count": total_segments_marked,
        "claim_count": len(claims),
        "non_propositional_rate_of_total_units": (
            total_segments_marked / total_units if total_units else 0.0
        ),
        "by_reason_code": by_reason,
        "other_reason_count": by_reason.get("other", 0),
        "note": "Rate only -- not a threshold, not an automatic trust signal. A high 'other' count deserves human review, per instruction; this function does not gate on it.",
    }


def compute_d0_effective_status(candidate_fields: dict, d0_output: dict) -> dict:
    """Fail-closed priority: schema_invalid > span_resolution_failed >
    segment_id_consistency_failed > D0_COVERAGE_FAILURE > valid.

    `D0_COVERAGE_FAILURE` (renamed this pass from `coverage_incomplete`
    for an explicit, distinct diagnostic identity) is THIS FILE's own
    structural finding -- `detected_by: "segment_accounting"`. It is
    kept structurally distinct from C0's semantic finding
    (`detected_by: "c0_semantic_audit"`, computed in
    cj2_b2_c0_prototype.py, layered on top of a `valid` result from this
    function) and from R1/R2's own `R1_R2_SEMANTIC_CONFLICT` /
    `unresolved_semantic_conflict` (cj2_b2_v2_probe.py, untouched here)
    -- never imported or reused as vocabulary in this function."""
    schema = validate_d0_schema(d0_output, candidate_fields)
    if not schema["valid"]:
        return {"status": "schema_invalid", "detail": schema["violations"]}

    span_res = validate_span_resolution(d0_output, candidate_fields)
    if not span_res["valid"]:
        return {"status": "span_resolution_failed", "detail": span_res["violations"]}

    consistency = validate_segment_id_consistency(d0_output, candidate_fields, span_res)
    if not consistency["valid"]:
        return {"status": "segment_id_consistency_failed", "detail": consistency["violations"]}

    coverage = compute_coverage(candidate_fields, d0_output)
    if not coverage["coverage_complete"]:
        detail = [
            f"{f['source_field']}: {len(f['uncovered_segments'])} uncovered segment(s) -- "
            + "; ".join(s["text"][:80] for s in f["uncovered_segments"])
            for f in coverage["per_field"] if f["uncovered_segments"]
        ]
        return {
            "status": "D0_COVERAGE_FAILURE",
            "detected_by": "segment_accounting",
            "detail": detail,
            "coverage": coverage,
        }

    return {"status": "valid", "detail": [], "coverage": coverage}


def validate_claim_set_unchanged(fixed_claim_ids, downstream_claim_ids, stage_name: str) -> dict:
    """Fixed-claim handoff check. Used for ALL THREE handoff points in
    the D0/C0/R1/R2 topology:
      - R1 receiving exactly D0's claim_id set (R1 cannot decompose,
        split, merge, or omit D0's claims)
      - R2 receiving exactly what R1 was handed (unchanged from v2's
        existing discipline -- R2 is keyed by claim_id only)
      - D0's claim_id set remaining unchanged after C0 runs (C0 has no
        mechanism to alter it -- see cj2_b2_c0_prototype.py's own schema,
        which has no `claims`/`revised_claims` key at all)
    A single generic function because the invariant is identical at
    every point: the downstream stage's claim_id set must equal the
    upstream fixed set, exactly -- no additions, no omissions."""
    fixed = set(fixed_claim_ids)
    downstream = set(downstream_claim_ids)
    missing = sorted(fixed - downstream)
    extra = sorted(downstream - fixed)
    return {
        "stage": stage_name,
        "valid": not missing and not extra,
        "missing_from_downstream": missing,
        "extra_in_downstream": extra,
    }
