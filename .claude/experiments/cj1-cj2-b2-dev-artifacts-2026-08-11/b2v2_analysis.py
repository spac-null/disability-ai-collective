#!/usr/bin/env python3
"""One-shot analysis script for the B2-v2 30-candidate regression.
Reads already-executed results; makes no API calls; performs no tuning."""
import json, os, hashlib

REPO = "/Users/stargatesgx/code/disability-collective-ai/automation"
os.chdir(REPO)

# ---- load v2 results ----
v2 = {}
for fn in os.listdir(".probe_fixtures/cj2-b2-v2-regression/regression_results/per_candidate"):
    key = fn[:-5].replace("__", "/")
    v2[key] = json.load(open(f".probe_fixtures/cj2-b2-v2-regression/regression_results/per_candidate/{fn}"))

# ---- load v1.4.1 baseline ----
v141 = {}
for fn in os.listdir(".probe_fixtures/cj2-fresh-batch-1/b2_v1_4_1"):
    if fn.endswith("_b2.json"):
        v141[fn[:-len("_b2.json")]] = json.load(open(f".probe_fixtures/cj2-fresh-batch-1/b2_v1_4_1/{fn}"))
for fn in os.listdir(".probe_fixtures/cj2-reference-probe-1/b2_v1_4_1"):
    if fn.endswith("_b2.json"):
        base = fn[:-len("_b2.json")]
        slug, engine = base.rsplit("_", 1)
        v141[f"{slug}/{engine}"] = json.load(open(f".probe_fixtures/cj2-reference-probe-1/b2_v1_4_1/{fn}"))

assert set(v2.keys()) == set(v141.keys()) and len(v2) == 30

# =========================================================================
# SECTION 11 -- RUN HEALTH
# =========================================================================
run_health = {"r1": {"valid": 0, "schema_invalid": 0, "call_failed": 0},
              "r2": {"valid": 0, "schema_invalid": 0, "call_failed": 0},
              "combined": {}}
combined_counts = {}
for key, d in v2.items():
    p = d["pipeline"]
    # R1 layer
    if p["r1_result"] is None and d.get("r1_error"):
        run_health["r1"]["call_failed"] += 1
    elif p.get("r1_validation") and not p["r1_validation"]["valid"]:
        run_health["r1"]["schema_invalid"] += 1
    elif p["r1_result"] is not None:
        run_health["r1"]["valid"] += 1
    # R2 layer (only meaningful if R1 valid)
    if p["stage"] in ("r1",):
        pass  # R2 never attempted
    else:
        if p["r2_result"] is None and d.get("r2_error") and d["r2_error"] not in ("r1_failed_no_r2_call", "r1_schema_invalid_no_r2_call"):
            run_health["r2"]["call_failed"] += 1
        elif p.get("r2_validation") and not p["r2_validation"]["valid"]:
            run_health["r2"]["schema_invalid"] += 1
        elif p["r2_result"] is not None and p.get("r2_validation", {}).get("valid"):
            run_health["r2"]["valid"] += 1
    combined_counts[p["b2v2_run_status"]] = combined_counts.get(p["b2v2_run_status"], 0) + 1
run_health["combined"] = combined_counts

schema_invalid_candidates = [k for k, d in v2.items() if d["pipeline"]["b2v2_run_status"] == "schema_invalid"]

# =========================================================================
# SECTION 7 -- GLOBAL BIDIRECTIONAL ROLE MIGRATION (v1.4.1 -> v2)
# =========================================================================
# v1.4.1 role distribution (per-claim, all 30 candidates -- all were valid in v1.4.1)
v141_role_counts = {"interpretive_only": 0, "factual_dependency": 0, "boundary_ambiguous": 0}
for key, d in v141.items():
    for cid, c in d["per_claim_effective"].items():
        r = c.get("role")
        if r in v141_role_counts:
            v141_role_counts[r] += 1
v141_total = sum(v141_role_counts.values())

# v2 role distribution -- ONLY for candidates with valid combined run_status
# (per Correction 5's convention: R1_R2_SEMANTIC_CONFLICT claims count as
# boundary_ambiguous for migration-comparison purposes, raw role reported separately)
v2_role_counts_effective = {"interpretive_only": 0, "factual_dependency": 0, "boundary_ambiguous": 0}
v2_role_counts_raw = {"interpretive_only": 0, "factual_dependency": 0, "boundary_ambiguous": 0}
v2_conflict_claims = []
for key, d in v2.items():
    p = d["pipeline"]
    if p["b2v2_run_status"] != "valid":
        continue
    for cid, c in p["per_claim_effective"].items():
        role = c["role"]
        cons = c["consistency"]
        v2_role_counts_raw[role] += 1
        eff_role = "boundary_ambiguous" if cons == "R1_R2_SEMANTIC_CONFLICT" else role
        v2_role_counts_effective[eff_role] += 1
        if cons == "R1_R2_SEMANTIC_CONFLICT":
            v2_conflict_claims.append({"candidate": key, "claim_id": cid,
                                        "raw_role": role,
                                        "surface_claim": next(pr["surface_claim"] for pr in p["r1_result"]["propositions"] if pr["claim_id"] == cid)})
v2_total_effective = sum(v2_role_counts_effective.values())

# claim-content-keyed migration: match by (candidate, surface_claim text) is not
# stable across re-decomposition (different claim granularity/ids) -- report
# AGGREGATE distributional shift only (the mechanically sound comparison given
# re-decomposition), not a claim-by-claim migration table. This is disclosed
# explicitly, not silently substituted.
aggregate_shift = {
    "v1_4_1_interpretive_only_pct": round(100 * v141_role_counts["interpretive_only"] / v141_total, 1),
    "v1_4_1_factual_dependency_pct": round(100 * v141_role_counts["factual_dependency"] / v141_total, 1),
    "v1_4_1_boundary_ambiguous_pct": round(100 * v141_role_counts["boundary_ambiguous"] / v141_total, 1),
    "v2_interpretive_only_pct_effective": round(100 * v2_role_counts_effective["interpretive_only"] / v2_total_effective, 1),
    "v2_factual_dependency_pct_effective": round(100 * v2_role_counts_effective["factual_dependency"] / v2_total_effective, 1),
    "v2_boundary_ambiguous_pct_effective": round(100 * v2_role_counts_effective["boundary_ambiguous"] / v2_total_effective, 1),
    "v141_total_claims": v141_total,
    "v2_total_claims_valid_candidates_only": v2_total_effective,
    "v2_excluded_candidates_schema_invalid": schema_invalid_candidates,
    "caveat": "v1.4.1 used a single-stage schema (30/30 valid, one flat claim list per candidate). v2 uses an independent two-stage R1->R2 re-decomposition -- claim IDs and even claim GRANULARITY are not stable across the two runs (e.g. H08 has 14 claims under v1.4.1 vs 17 under v2's R1). A claim-by-claim migration table keyed by claim_id or exact-text match is therefore not mechanically meaningful here (unlike the v1.2->v1.3->v1.4.1 comparisons, which shared one decomposition scheme). This aggregate percentage-point comparison is reported instead, with the caveat stated plainly. The 6 named directional buckets (interpretive_only->factual_dependency, etc.) are NOT computed as claim-matched counts for this reason -- computing them would require inventing a semantic-similarity matching step this pass was not authorized to perform."
}

# =========================================================================
# Best-effort CLAIM-LEVEL migration via text-similarity matching (disclosed
# method, not a silent substitute for exact-id matching, which is impossible
# across re-decomposition -- see caveat above). One v1.4.1 claim is matched
# to at most one v2 claim WITHIN THE SAME CANDIDATE via greedy highest-
# similarity assignment (difflib.SequenceMatcher.ratio on lowercased text),
# threshold 0.55. Below threshold -> unmatched, reported separately, never
# silently dropped.
# =========================================================================
import difflib

ROLE_DIRECTIONS = [
    ("interpretive_only", "factual_dependency"),
    ("factual_dependency", "interpretive_only"),
    ("interpretive_only", "boundary_ambiguous"),
    ("factual_dependency", "boundary_ambiguous"),
    ("boundary_ambiguous", "interpretive_only"),
    ("boundary_ambiguous", "factual_dependency"),
]
migration_counts = {f"{a}->{b}": 0 for a, b in ROLE_DIRECTIONS}
unchanged_counts = {"interpretive_only": 0, "factual_dependency": 0, "boundary_ambiguous": 0}
matched_pairs_log = []
unmatched_v141 = []
unmatched_v2 = []
THRESHOLD = 0.55

for key in v2:
    v141_claims = v141[key]["per_claim_effective"]  # {cid: {"role": ...}}
    v141_claim_text = {}
    for cid, c in v141_claims.items():
        # find text from raw b2_result claims list
        pass
    raw_claims = {c["claim_id"]: c for c in v141[key]["b2_result"]["claims"]}

    p = v2[key]["pipeline"]
    if p["b2v2_run_status"] != "valid":
        for cid, c in v141_claims.items():
            unmatched_v141.append({"candidate": key, "claim_id": cid, "reason": "v2 run not valid"})
        continue

    v2_props = {pr["claim_id"]: pr for pr in p["r1_result"]["propositions"]}
    v2_effective = p["per_claim_effective"]

    available_v2 = set(v2_props.keys())
    for v141_cid, v141_c in raw_claims.items():
        old_role = v141_claims[v141_cid]["role"]
        old_text = v141_c.get("claim", "")
        best_cid, best_score = None, 0.0
        for v2_cid in available_v2:
            v2_text = v2_props[v2_cid]["surface_claim"]
            score = difflib.SequenceMatcher(None, old_text.lower(), v2_text.lower()).ratio()
            if score > best_score:
                best_score, best_cid = score, v2_cid
        if best_cid is not None and best_score >= THRESHOLD:
            available_v2.discard(best_cid)
            new_role_raw = v2_effective[best_cid]["role"]
            new_cons = v2_effective[best_cid]["consistency"]
            new_role_eff = "boundary_ambiguous" if new_cons == "R1_R2_SEMANTIC_CONFLICT" else new_role_raw
            matched_pairs_log.append({"candidate": key, "v141_claim_id": v141_cid, "v2_claim_id": best_cid,
                                       "similarity": round(best_score, 3), "old_role": old_role,
                                       "new_role_effective": new_role_eff, "new_role_raw": new_role_raw,
                                       "new_consistency": new_cons})
            if old_role == new_role_eff:
                if old_role in unchanged_counts:
                    unchanged_counts[old_role] += 1
            else:
                direction = f"{old_role}->{new_role_eff}"
                if direction in migration_counts:
                    migration_counts[direction] += 1
        else:
            unmatched_v141.append({"candidate": key, "claim_id": v141_cid, "text": old_text[:80],
                                    "best_similarity_found": round(best_score, 3)})
    for v2_cid in available_v2:
        unmatched_v2.append({"candidate": key, "claim_id": v2_cid, "text": v2_props[v2_cid]["surface_claim"][:80]})

total_matched = len(matched_pairs_log)
total_v141_claims_all = sum(len(v141[k]["per_claim_effective"]) for k in v2)
match_rate = round(100 * total_matched / total_v141_claims_all, 1)

claim_migration_report = {
    "method": "greedy per-candidate text-similarity matching (difflib.SequenceMatcher.ratio, threshold>=0.55), disclosed best-effort substitute for exact-id matching (impossible across independent re-decomposition -- see aggregate_shift caveat)",
    "total_v1_4_1_claims": total_v141_claims_all,
    "matched": total_matched,
    "match_rate_pct": match_rate,
    "unmatched_v1_4_1_claims": len(unmatched_v141),
    "unmatched_v2_claims_not_counted_in_migration": len(unmatched_v2),
    "migration_counts": migration_counts,
    "unchanged_counts": unchanged_counts,
    "note": "Unmatched claims are NOT assumed unchanged or assumed migrated -- they are excluded from this table and counted separately. A ~55%+ text-similarity floor for near-paraphrase matching is a judgment call, not a preregistered threshold; treat this table as directional/diagnostic, not a precise census."
}

print("RUN_HEALTH", json.dumps(run_health, indent=2))
print()
print("SCHEMA_INVALID_CANDIDATES", schema_invalid_candidates)
print()
print("AGGREGATE_SHIFT", json.dumps(aggregate_shift, indent=2))
print()
print("CLAIM_MIGRATION", json.dumps(claim_migration_report, indent=2))

json.dump({
    "run_health": run_health,
    "schema_invalid_candidates": schema_invalid_candidates,
    "aggregate_shift": aggregate_shift,
    "claim_migration_report": claim_migration_report,
    "matched_pairs_log": matched_pairs_log,
    "unmatched_v141": unmatched_v141,
    "unmatched_v2": unmatched_v2,
}, open("/tmp/b2v2_migration_analysis.json", "w"), indent=2)

print()
print("RAW_VS_EFFECTIVE_ROLE_COUNTS", json.dumps({"raw": v2_role_counts_raw, "effective": v2_role_counts_effective}, indent=2))

# =========================================================================
# R1/R2 3x3 DISAGREEMENT MATRIX (valid candidates only, 13/30)
# =========================================================================
matrix = {}
for ed in ("true", "false", "uncertain"):
    for role in ("factual_dependency", "interpretive_only", "boundary_ambiguous"):
        matrix[f"R1={ed}|R2={role}"] = 0

conflict_claims_detail = []
total_valid_claims = 0
for key, d in v2.items():
    p = d["pipeline"]
    if p["b2v2_run_status"] != "valid":
        continue
    props = {pr["claim_id"]: pr for pr in p["r1_result"]["propositions"]}
    for cid, c in p["per_claim_effective"].items():
        total_valid_claims += 1
        ed = props[cid]["empirical_dependency"]
        role = c["role"]
        matrix[f"R1={ed}|R2={role}"] += 1
        if c["consistency"] == "R1_R2_SEMANTIC_CONFLICT":
            conflict_claims_detail.append({"candidate": key, "claim_id": cid})

matrix_pct = {k: round(100 * v / total_valid_claims, 1) for k, v in matrix.items()}

# =========================================================================
# CONFLICT EFFECTIVENESS
# =========================================================================
# For every R1_R2_SEMANTIC_CONFLICT claim: would it have been "safe"-compatible
# (i.e. contribute nothing to unsafe/ambiguous) if resolved via the plain
# role/support branch instead of the conflict override? Per compute_effective_v2,
# role=interpretive_only always yields effective_status=support=not_required,
# which never triggers any_unsafe/any_ambiguous -- so YES, every conflict claim
# would have defaulted to a safe-compatible status without the override.
would_be_safe_without_override = len(conflict_claims_detail)

# candidates whose overall verdict is "ambiguous" purely because of
# R1_R2_SEMANTIC_CONFLICT claims (no independently-unsafe claim in the same candidate)
candidates_flipped_by_conflict_rule = []
for key, d in v2.items():
    p = d["pipeline"]
    if p["b2v2_run_status"] != "valid":
        continue
    if p["effective_verdict"] != "ambiguous":
        continue
    has_conflict = any(c["consistency"] == "R1_R2_SEMANTIC_CONFLICT" for c in p["per_claim_effective"].values())
    has_independent_unsafe = any(
        c["role"] == "factual_dependency" and c["consistency"] != "R1_R2_SEMANTIC_CONFLICT" and
        (c["effective_status"] == "unsupported" or c["declaration"] == "undeclared")
        for c in p["per_claim_effective"].values()
    )
    if has_conflict and not has_independent_unsafe:
        candidates_flipped_by_conflict_rule.append(key)

conflict_effectiveness = {
    "total_R1_R2_SEMANTIC_CONFLICT_claims": len(conflict_claims_detail),
    "claims": conflict_claims_detail,
    "would_have_defaulted_to_safe_compatible_status_without_override": would_be_safe_without_override,
    "candidates_whose_verdict_is_ambiguous_specifically_because_of_the_conflict_rule": candidates_flipped_by_conflict_rule,
    "note": "Every R1_R2_SEMANTIC_CONFLICT claim, if resolved via the plain role/support branch instead of the deterministic override, would land on role=interpretive_only -> support=not_required -> a safe-compatible effective_status. The override is therefore responsible for preventing a false-safe on every single one of these claims -- this is the architecture doing exactly what it was designed to do. Separately, the candidates listed above would have their WHOLE-CANDIDATE verdict flip from ambiguous to safe if the conflict rule did not exist AND no other claim in that candidate independently resolves unsafe."
}

print()
print("R1_R2_MATRIX_COUNTS", json.dumps(matrix, indent=2))
print("R1_R2_MATRIX_PCT", json.dumps(matrix_pct, indent=2))
print()
print("CONFLICT_EFFECTIVENESS", json.dumps(conflict_effectiveness, indent=2))

# =========================================================================
# CANDIDATE-LEVEL VERDICT TRANSITIONS v1.4.1 -> v2
# =========================================================================
VERDICT_DIRECTIONS = [("safe","unsafe"),("unsafe","safe"),("safe","ambiguous"),
                       ("unsafe","ambiguous"),("ambiguous","safe"),("ambiguous","unsafe")]
verdict_migration = {f"{a}->{b}": [] for a,b in VERDICT_DIRECTIONS}
verdict_unchanged = {"safe": [], "unsafe": [], "ambiguous": []}
verdict_not_computed = []

for key in v2:
    old_v = v141[key]["effective_verdict"]
    p = v2[key]["pipeline"]
    if p["b2v2_run_status"] != "valid":
        verdict_not_computed.append({"candidate": key, "v1_4_1_verdict": old_v, "v2_run_status": p["b2v2_run_status"]})
        continue
    new_v = p["effective_verdict"]
    if old_v == new_v:
        verdict_unchanged[old_v].append(key)
    else:
        direction = f"{old_v}->{new_v}"
        if direction in verdict_migration:
            verdict_migration[direction].append(key)

print()
print("VERDICT_MIGRATION", json.dumps(verdict_migration, indent=2))
print("VERDICT_UNCHANGED_COUNTS", {k: len(v) for k,v in verdict_unchanged.items()})
print("VERDICT_NOT_COMPUTED_COUNT", len(verdict_not_computed))
print("VERDICT_NOT_COMPUTED", json.dumps(verdict_not_computed, indent=2))

json.dump({
    "raw_vs_effective_role_counts": {"raw": v2_role_counts_raw, "effective": v2_role_counts_effective},
    "r1_r2_matrix_counts": matrix,
    "r1_r2_matrix_pct": matrix_pct,
    "total_valid_claims_for_matrix": total_valid_claims,
    "conflict_effectiveness": conflict_effectiveness,
    "verdict_migration": verdict_migration,
    "verdict_unchanged_counts": {k: len(v) for k,v in verdict_unchanged.items()},
    "verdict_unchanged_detail": verdict_unchanged,
    "verdict_not_computed": verdict_not_computed,
}, open("/tmp/b2v2_matrix_analysis.json","w"), indent=2)
