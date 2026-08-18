#!/usr/bin/env python3
import json, glob
from collections import Counter
from pathlib import Path

REPO = Path("/Users/stargatesgx/code/disability-collective-ai")

def load_set(path_glob, key_fn):
    out = {}
    for f in glob.glob(str(REPO / path_glob)):
        if 'all_results' in f:
            continue
        d = json.load(open(f))
        out[key_fn(d)] = d
    return out

dev_v12 = load_set('automation/.probe_fixtures/cj2-reference-probe-1/b2_v1_2/*_b2.json', lambda d: f"{d['slug']}/{d['engine_label']}")
dev_v13 = load_set('automation/.probe_fixtures/cj2-reference-probe-1/b2_v1_3/*_b2.json', lambda d: f"{d['slug']}/{d['engine_label']}")
fb_v12 = load_set('automation/.probe_fixtures/cj2-fresh-batch-1/b2_v1_2/H*_b2.json', lambda d: d['h_id'])
fb_v13 = load_set('automation/.probe_fixtures/cj2-fresh-batch-1/b2_v1_3/H*_b2.json', lambda d: d['h_id'])

all_v12 = {**{f"DEV:{k}": v for k, v in dev_v12.items()}, **{f"FB:{k}": v for k, v in fb_v12.items()}}
all_v13 = {**{f"DEV:{k}": v for k, v in dev_v13.items()}, **{f"FB:{k}": v for k, v in fb_v13.items()}}

def role_counts(results):
    c = Counter()
    total = 0
    for d in results.values():
        if d['b2_run_status'] != 'valid':
            continue
        for claim in d['b2_result']['claims']:
            c[claim['role']] += 1
            total += 1
    return c, total

def pct(n, t):
    return round(100 * n / t, 2) if t else 0.0

def aggregate_block(v12, v13):
    c12, t12 = role_counts(v12)
    c13, t13 = role_counts(v13)
    return {
        "v1_2": {"total_claims": t12, "interpretive_only": c12['interpretive_only'],
                 "factual_dependency": c12['factual_dependency'], "boundary_ambiguous": c12['boundary_ambiguous'],
                 "interpretive_only_pct": pct(c12['interpretive_only'], t12),
                 "factual_dependency_pct": pct(c12['factual_dependency'], t12),
                 "boundary_ambiguous_pct": pct(c12['boundary_ambiguous'], t12)},
        "v1_3": {"total_claims": t13, "interpretive_only": c13['interpretive_only'],
                 "factual_dependency": c13['factual_dependency'], "boundary_ambiguous": c13['boundary_ambiguous'],
                 "interpretive_only_pct": pct(c13['interpretive_only'], t13),
                 "factual_dependency_pct": pct(c13['factual_dependency'], t13),
                 "boundary_ambiguous_pct": pct(c13['boundary_ambiguous'], t13)},
        "interpretive_only_pp_drop": round(pct(c12['interpretive_only'], t12) - pct(c13['interpretive_only'], t13), 2),
        "factual_dependency_pp_rise": round(pct(c13['factual_dependency'], t13) - pct(c12['factual_dependency'], t12), 2),
    }

agg_dev = aggregate_block(dev_v12, dev_v13)
agg_fb = aggregate_block(fb_v12, fb_v13)
agg_combined = aggregate_block(all_v12, all_v13)

# Criterion 3a: aggregate cap, evaluated on COMBINED 30-candidate corpus
crit3a_pass = abs(agg_combined["interpretive_only_pp_drop"]) <= 15 and abs(agg_combined["factual_dependency_pp_rise"]) <= 15

# Criterion 3b: flip-rate cap (exact source_field+claim-text match; lower bound)
total_interp_v12 = 0
flipped = 0
flip_details = []
for key in all_v12:
    d12 = all_v12[key]
    d13 = all_v13.get(key)
    if d12['b2_run_status'] != 'valid':
        continue
    v13_by_field_text = {}
    if d13 and d13['b2_run_status'] == 'valid':
        for c in d13['b2_result']['claims']:
            v13_by_field_text[(c['source_field'], c['claim'].strip())] = c
    for c12 in d12['b2_result']['claims']:
        if c12['role'] != 'interpretive_only':
            continue
        total_interp_v12 += 1
        match = v13_by_field_text.get((c12['source_field'], c12['claim'].strip()))
        if match and match['role'] in ('factual_dependency', 'boundary_ambiguous'):
            flipped += 1
            flip_details.append({"key": key, "source_field": c12['source_field'],
                                  "claim": c12['claim'], "v1_3_role": match['role']})

flip_rate = pct(flipped, total_interp_v12)
crit3b_pass = flip_rate <= 20.0

# Candidate-level verdict comparison
candidate_rows = []
for key in sorted(all_v12, key=lambda k: (k.split(':')[0], k.split(':')[1])):
    d12 = all_v12[key]
    d13 = all_v13.get(key)
    row = {
        "key": key,
        "v1_2_verdict": d12['effective_verdict'],
        "v1_3_verdict": d13['effective_verdict'] if d13 else None,
        "v1_3_run_status": d13['b2_run_status'] if d13 else None,
        "changed": d12['effective_verdict'] != (d13['effective_verdict'] if d13 else None),
    }
    candidate_rows.append(row)

changed_rows = [r for r in candidate_rows if r["changed"]]

# Known 5 miss targets (exact text where possible)
targets = [
    {"key": "FB:H05", "source_field": "interpretive_inference",
     "v1_2_text": "Panels were socially obligated to keep ranking even after their genuine discriminatory capacity had run out."},
    {"key": "FB:H08", "source_field": "interpretive_inference",
     "v1_2_text": "The scale's resolution was treated as adjustable by the raters, when in fact resolution is a property of the underlying signal."},
    {"key": "FB:H09", "source_field": "interpretive_inference",
     "v1_2_text": "The sex-differentiated cutoff encodes an institutional assumption about the expected magnitude of female career interruptions -- specifically five years' worth."},
    {"key": "FB:H14", "source_field": "interpretive_inference",
     "v1_2_text": "In the 3,700+ already-funded projects, the word 'policy' is not decorative but load-bearing, marking the orientation of the work toward its intended use."},
    {"key": "FB:H17", "source_field": "interpretive_inference",
     "v1_2_text": "The differential cutoffs reveal that the system is measuring career stage adjusted for an assumed sex-linked career disruption pattern, such as childbearing."},
]

target_results = []
manual_verdicts = {
    "FB:H05": {"status": "CONFIRMED_FIXED", "note": "Same proposition, reworded by re-extraction ('even after ranking had become meaningless' vs original wording) -- now factual_dependency/unsupported."},
    "FB:H08": {"status": "STILL_MISSED", "note": "Exact same claim text, still interpretive_only. v1.3's new section did not catch this modality/certainty-hardening case."},
    "FB:H09": {"status": "CLAIM_FIXED_RUN_SCHEMA_INVALID", "note": "Exact target claim (c5) now correctly factual_dependency/unsupported/motivation_invention. BUT the overall run is schema_invalid due to an UNRELATED claim (c7) violating the unsupported-requires-semantic-problem invariant -- no computed verdict for this candidate this run."},
    "FB:H14": {"status": "CONFIRMED_FIXED", "note": "Exact claim text match -- now factual_dependency/unsupported."},
    "FB:H17": {"status": "STILL_MISSED", "note": "Same proposition (minor rewording of the parenthetical example), still interpretive_only."},
}
for t in targets:
    d13 = all_v13.get(t["key"])
    target_results.append({
        **t,
        "v1_3_run_status": d13['b2_run_status'] if d13 else None,
        "manual_adjudication": manual_verdicts[t["key"]],
    })

# H03 must-remain-caught check
h03_v12 = all_v12["FB:H03"]
h03_v13 = all_v13["FB:H03"]
h03_target_claims_still_flagged = []
for c in h03_v13['b2_result']['claims']:
    eff = h03_v13['per_claim_effective'].get(c['claim_id'], {})
    if eff.get('effective_status') == 'unsupported' and c['source_field'] == 'interpretive_inference':
        h03_target_claims_still_flagged.append(c['claim'])
criterion2_pass = h03_v13['effective_verdict'] == 'unsafe' and len(h03_target_claims_still_flagged) >= 1

# Individually-inspected new-unsafe/new-safe cases (criterion 4)
new_verdict_cases = [
    {
        "key": "DEV:05_dutch_painting_soldier/M",
        "change": "safe -> unsafe",
        "target": False,
        "inspection": "Two claims (c9, c13) assert the 'modesty' motivation for the alteration as settled fact. Source (cj1:a3-region) frames modesty as only ONE of THREE speculative possibilities ('researchers speculate'). This is the SAME speculative-motive-hardening pattern already found and adjudicated for De Hooch/P under v1.2 ('likely_human_annotation_defect' -- the source itself hedges). Assessment: genuine, well-grounded catch, consistent with a prior adjudication of the identical source pattern, not an overcorrection.",
    },
    {
        "key": "DEV:05_dutch_painting_soldier/Z",
        "change": "safe -> unsafe",
        "target": False,
        "inspection": "Two claims (c7, c14) assert that the woman/men drinking contrast IS 'de Hooch's moral signal' / that his moralism 'functioned through contrast and implication' as deliberate intent. Source establishes the visual fact (who drinks, who doesn't) but not the artist's own intent. Assessment: defensible under the new rule (artistic intent = a 'was designed to accomplish' claim), but closer to the anti-overcorrection boundary than H05/M's case -- attributing a 'moral signal' to a painting is closer to ordinary art-critical language than a clear world-claim. Flagged as the more debatable of the two new dev-set catches.",
    },
    {
        "key": "FB:H16",
        "change": "unsafe -> safe",
        "target": False,
        "inspection": "The disputed claim (c4) is IDENTICAL text in both runs. v1.2 cited only the '3,700 projects' excerpt (does_not_establish_claim). v1.3 additionally cited a second, genuinely more direct excerpt: '...applications that had been previously approved by peer reviewers and agency employees' -- which does state these specific policy-flagged applications were previously approved. Assessment: this is a genuine additional-evidence finding (the auditor located a better citation this run), not a role/support-standard change from the new v1.3 section, and the second citation is real and substantively supports the claim. Independently judged more correct than v1.2's miss of this citation, not a new B2 weakness.",
    },
]

report = {
    "_metadata": {
        "purpose": "cj2-stage-b2-v1.3 regression comparison against v1.2, run on the exact 30-candidate corpus (12 development + 18 fresh-batch-1), same call conditions/input construction/validators, only the v1.3 prompt delta as the experimental variable.",
        "model": "openrouter/claude-sonnet-4.6", "temperature": 0.0, "max_tokens": 5000,
        "v1_2_prompt_sha256_dev": "unchanged, original v1.2 run",
        "v1_3_prompt_sha256": "8a5b279e33ae2de801c6914e0143f28dc3afb0a1cbc7e157ac3e427e64bfe177",
        "v1_2_outputs_preserved": True,
        "tuning_performed": False,
    },
    "run_status_summary": dict(Counter(all_v13[k]['b2_run_status'] for k in all_v13)),
    "candidate_level_verdicts": candidate_rows,
    "changed_verdicts": changed_rows,
    "new_verdict_cases_individually_inspected": new_verdict_cases,
    "role_distribution": {"development_set_12": agg_dev, "fresh_batch_18": agg_fb, "combined_30": agg_combined},
    "flip_rate_analysis": {
        "total_v1_2_interpretive_only_claims": total_interp_v12,
        "flipped_to_factual_dependency_or_boundary_ambiguous": flipped,
        "flip_rate_pct": flip_rate,
        "flip_details": flip_details,
        "note": "Exact (source_field, claim text) match only -- a LOWER BOUND. Claims reworded by re-extraction (e.g. H05, H17's targets) are undercounted here.",
    },
    "acceptance_criteria": {
        "criterion_1_five_confirmed_misses": {
            "targets": target_results,
            "summary": {"confirmed_fixed": 2, "claim_fixed_run_schema_invalid": 1, "still_missed": 2},
            "result": "PARTIAL -- 2/5 confirmed fixed (H05, H14), 1/5 claim-level fixed but run schema_invalid (H09), 2/5 still missed (H08, H17)",
        },
        "criterion_2_h03_must_remain_caught": {
            "v1_3_verdict": h03_v13['effective_verdict'],
            "target_claims_still_flagged_unsupported": h03_target_claims_still_flagged,
            "result": "PASS" if criterion2_pass else "FAIL",
        },
        "criterion_3_role_migration": {
            "criterion_3a_aggregate_cap": {
                "interpretive_only_pp_drop_combined": agg_combined["interpretive_only_pp_drop"],
                "factual_dependency_pp_rise_combined": agg_combined["factual_dependency_pp_rise"],
                "cap_pp": 15,
                "result": "PASS" if crit3a_pass else "FAIL",
            },
            "criterion_3b_flip_rate_cap": {
                "flip_rate_pct": flip_rate, "cap_pct": 20.0,
                "result": "PASS" if crit3b_pass else "FAIL",
            },
            "result": "PASS" if (crit3a_pass and crit3b_pass) else "FAIL",
        },
        "criterion_4_new_unsafe_verdicts_individually_inspected": {
            "count": len([c for c in new_verdict_cases if c["change"] == "safe -> unsafe"]),
            "cases": [c for c in new_verdict_cases if c["change"] == "safe -> unsafe"],
            "result": "DONE -- each individually inspected and reported above, none assumed correct merely because v1.3 is stricter",
        },
        "criterion_5_no_further_tuning": {
            "result": "PASS -- no edits made to cj2-stage-b2-v1.3 after seeing these outputs; any further correction is v1.4, not made in this pass",
        },
    },
    "overall_regression_status": "PARTIAL PASS: role-migration criteria (3a, 3b) and H03-retention criterion (2) both PASS cleanly -- no blanket overcorrection. The primary miss-fix criterion (1) is a MIXED result: 2 of 5 confirmed fixed, 1 fixed at the claim level but blocked by an unrelated schema-compliance failure, 2 still missed. Two NEW, non-targeted unsafe findings appeared on the development set (one strong, one more debatable) plus one new safe finding on the fresh batch, all individually inspected. v1.3 is NOT a complete fix and is NOT tuned further in this pass, per instruction.",
}

out_dir = REPO / "automation" / ".probe_fixtures" / "cj2-b2-v1.3-regression"
out_dir.mkdir(parents=True, exist_ok=True)
json_path = out_dir / "b2-v1.3-regression-comparison.json"
json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
print(f"wrote {json_path}")

import hashlib
print("SHA256:", hashlib.sha256(json_path.read_bytes()).hexdigest())
