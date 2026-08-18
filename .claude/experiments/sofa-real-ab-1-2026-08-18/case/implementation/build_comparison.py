import json, hashlib, os

DEV_SLUGS = ["01_cave_dna", "05_dutch_painting_soldier", "07_ai_cheating_exam"]
ENGINES = ["P","S","Z","M"]

def load_dev(version):
    out = {}
    d = f"automation/.probe_fixtures/cj2-reference-probe-1/{version}"
    for s in DEV_SLUGS:
        for e in ENGINES:
            p = f"{d}/{s}_{e}_b2.json"
            if os.path.exists(p):
                out[f"DEV:{s}/{e}"] = json.load(open(p))
    return out

def load_fresh(version):
    out = {}
    d = f"automation/.probe_fixtures/cj2-fresh-batch-1/{version}"
    mapping = json.load(open("automation/.probe_fixtures/cj2-fresh-batch-1/human-review-hidden-mapping-v1.json"))["mapping"]
    for t in mapping:
        h = t["h_id"]
        p = f"{d}/{h}_b2.json"
        if os.path.exists(p):
            out[f"FB:{h}"] = json.load(open(p))
    return out

v12 = {**load_dev("b2_v1_2"), **load_fresh("b2_v1_2")}
v13 = {**load_dev("b2_v1_3"), **load_fresh("b2_v1_3")}
v141 = {**load_dev("b2_v1_4_1"), **load_fresh("b2_v1_4_1")}

# ---- run status summary ----
def run_status_summary(data):
    out = {}
    for k, rec in data.items():
        out[rec["b2_run_status"]] = out.get(rec["b2_run_status"], 0) + 1
    return out

run_status = {"v1_2": run_status_summary(v12), "v1_3": run_status_summary(v13), "v1_4_1": run_status_summary(v141)}

# ---- candidate-level verdict transitions v1.3 -> v1.4.1 ----
changed = []
for k in v141:
    old = v13.get(k, {}).get("effective_verdict")
    new = v141[k]["effective_verdict"]
    if old != new:
        changed.append({"key": k, "v1_3_verdict": old, "v1_3_run_status": v13.get(k,{}).get("b2_run_status"),
                         "v1_4_1_verdict": new, "v1_4_1_run_status": v141[k]["b2_run_status"]})

# ---- role distribution ----
def role_dist(data):
    roles = {"interpretive_only":0,"factual_dependency":0,"boundary_ambiguous":0}
    total = 0
    for k, rec in data.items():
        if rec["b2_run_status"] != "valid":
            continue
        for c in rec["b2_result"]["claims"]:
            roles[c["role"]] += 1
            total += 1
    return roles, total

rd12, t12 = role_dist(v12)
rd13, t13 = role_dist(v13)
rd141, t141 = role_dist(v141)

io12, fd12 = 100*rd12["interpretive_only"]/t12, 100*rd12["factual_dependency"]/t12
io13, fd13 = 100*rd13["interpretive_only"]/t13, 100*rd13["factual_dependency"]/t13
io141, fd141 = 100*rd141["interpretive_only"]/t141, 100*rd141["factual_dependency"]/t141

def norm(t):
    return " ".join(t.lower().split())[:200]

def claims_by_key(data):
    out = {}
    for k, rec in data.items():
        if rec["b2_run_status"] == "valid":
            out[k] = rec["b2_result"]["claims"]
    return out

c12, c141 = claims_by_key(v12), claims_by_key(v141)

v12_io = [(k, norm(c["claim"]), c["claim"]) for k, cs in c12.items() for c in cs if c["role"]=="interpretive_only"]
flip_fwd = [(k,t) for k,nt,t in v12_io if any(norm(cc["claim"])==nt and cc["role"] in ("factual_dependency","boundary_ambiguous") for cc in c141.get(k,[]))]

v12_fd = [(k, norm(c["claim"]), c["claim"]) for k, cs in c12.items() for c in cs if c["role"]=="factual_dependency"]
flip_rev = [(k,t) for k,nt,t in v12_fd if any(norm(cc["claim"])==nt and cc["role"]=="interpretive_only" for cc in c141.get(k,[]))]

result = {
    "_metadata": {
        "purpose": "cj2-stage-b2-v1.4.1 regression run vs v1.2 (baseline) and v1.3 (immediate predecessor), same 30-candidate corpus (12 dev + 18 fresh-batch-1), same model/temperature/max_tokens/timeout/input-construction/validators/resolver/run_status/effective_verdict logic as every prior B2 run. Only intentional experimental variable: the v1.4.1 prompt delta (STEP 3 hedge-handling rewrite).",
        "prompt_version": "cj2-stage-b2-v1.4.1",
        "prompt_sha256": hashlib.sha256(open("automation/.probe_fixtures/cj2-reference-probe-1/frozen_prompts/cj2-stage-b2-v1.4.1.txt","rb").read()).hexdigest(),
        "acceptance_matrix_path": "automation/.probe_fixtures/cj2-b2-v1.4.1-regression/acceptance-matrix-v1.json",
        "acceptance_matrix_sha256": hashlib.sha256(open("automation/.probe_fixtures/cj2-b2-v1.4.1-regression/acceptance-matrix-v1.json","rb").read()).hexdigest(),
        "corpus_size": 30,
    },
    "run_status_summary": run_status,
    "candidate_verdict_transitions_v1_3_to_v1_4_1": changed,
    "role_distribution": {
        "v1_2": {"counts": rd12, "total": t12, "interpretive_only_pct": round(io12,1), "factual_dependency_pct": round(fd12,1)},
        "v1_3": {"counts": rd13, "total": t13, "interpretive_only_pct": round(io13,1), "factual_dependency_pct": round(fd13,1)},
        "v1_4_1": {"counts": rd141, "total": t141, "interpretive_only_pct": round(io141,1), "factual_dependency_pct": round(fd141,1)},
    },
    "aggregate_shift_v1_2_baseline_gate": {
        "interpretive_only_delta_pp": round(io141-io12,1),
        "factual_dependency_delta_pp": round(fd141-fd12,1),
        "cap": "interpretive_only DROP <=15pp AND factual_dependency RISE <=15pp",
        "gate_result": "PASS (movement is in the OPPOSITE direction from what this cap bounds -- interpretive_only ROSE, factual_dependency FELL -- so the letter of the cap is not triggered; this is diagnostically the mirror-image failure, not an absence of failure -- see reverse_flip_rate_diagnostic_only)",
    },
    "flip_rate_v1_2_baseline_gate": {
        "v1_2_interpretive_only_total": len(v12_io),
        "flipped_to_factual_or_boundary": len(flip_fwd),
        "flip_rate_pct": round(100*len(flip_fwd)/len(v12_io),2),
        "cap": "<=20%",
        "gate_result": "PASS",
        "flipped_claims": [{"key":k,"claim":t} for k,t in flip_fwd],
    },
    "reverse_flip_rate_diagnostic_only_not_a_gate": {
        "v1_2_factual_dependency_total": len(v12_fd),
        "flipped_to_interpretive_only": len(flip_rev),
        "flip_rate_pct": round(100*len(flip_rev)/len(v12_fd),2),
        "note": "NOT one of the two preregistered gates. Reported because it directly explains the target-level failures below: v1.4.1 shows a real, measurable migration of previously-factual claims back into interpretive_only, in the opposite direction from the overcorrection the frozen gates guard against. Exact-text match only -- a lower bound, since re-extraction rewords some claims.",
        "flipped_claims": [{"key":k,"claim":t} for k,t in flip_rev],
    },
}

json.dump(result, open("automation/.probe_fixtures/cj2-b2-v1.4.1-regression/b2-v1.4.1-regression-comparison.json","w"), indent=2, ensure_ascii=False)
print("written. keys:", list(result.keys()))
print()
print("run_status:", run_status)
print("candidate transitions v1.3->v1.4.1:", len(changed))
for c in changed:
    print(" ", c)
