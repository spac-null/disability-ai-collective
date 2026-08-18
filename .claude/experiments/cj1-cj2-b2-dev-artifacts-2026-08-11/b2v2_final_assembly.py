#!/usr/bin/env python3
import json, hashlib

migration = json.load(open("/tmp/b2v2_migration_analysis.json"))
matrix = json.load(open("/tmp/b2v2_matrix_analysis.json"))

TARGET_SCORING = [
    {
        "candidate": "H08",
        "run_status": "valid",
        "target_claim_text": "The scale's resolution was treated as adjustable by the raters, when in fact resolution is a property of the underlying signal.",
        "expected_role": "factual_dependency", "expected_support": "unsupported",
        "verdict": "MISS",
        "failure_mode": "R1_PROPOSITION_NOT_EXTRACTED (new subtype, not previously named)",
        "reason": "The exact target sentence is verbatim-present in the raw candidate's `interpretive_inference` field (confirmed by direct substring search), embedded mid-paragraph. R1 decomposed that SAME field into propositions c7-c12, extracting the sentences immediately before and after it, but never produced a proposition corresponding to this specific sentence at all -- it is not merely misclassified, it was never decomposed into its own tracked claim_id. field_audits[interpretive_inference] still passes structural validation (claim_ids=[c7..c12], no_auditable_propositions=false) because OTHER propositions were extracted from that field -- the field-coverage check cannot detect a single omitted SENTENCE within a field that otherwise has claims. This is a structurally invisible omission: nothing in the schema or validator flags it. Distinct from and arguably more concerning than 'R1 says false/uncertain' (the target's own MISS condition), since there was no judgment to be wrong about -- the proposition simply never existed for R2 to audit."
    },
    {
        "candidate": "H09",
        "run_status": "schema_invalid",
        "target_claim_text": "The sex-differentiated cutoff encodes an institutional assumption about the expected magnitude of female career interruptions -- specifically five years' worth.",
        "verdict": "MISS",
        "failure_mode": "MAX_TOKENS truncation at R2 (transport/budget defect, not semantic)",
        "reason": "R1 correctly extracted and evidence-blind-classified the target claim (c8, empirical_dependency=true, near-verbatim surface_claim match). R2's response was cut off mid-generation at ~20,794 raw characters (~5,000-token ceiling) before completing its claims[] array; the harness's JSON-extraction fallback recovered a single trailing claim OBJECT (not the {\"claims\":[...]} wrapper), which correctly failed schema validation (\"claims missing or not a list\"). Disqualified per the target's own explicit rule: 'REPAIRED only if... both R1 and R2 run_status are valid for the WHOLE run... does_not_count_as_repaired_if: the run is schema_invalid at either stage, even if this specific claim looks correctly classified.' Applied exactly as written."
    },
    {
        "candidate": "H17",
        "run_status": "valid",
        "target_claim_text": "The differential cutoffs reveal that the system is measuring career stage adjusted for an assumed sex-linked career disruption pattern (e.g., childbearing).",
        "expected_role": "factual_dependency", "expected_support": "unsupported",
        "verdict": "FLAGGED_NOT_RESOLVED",
        "failure_mode": "R1 catches it (ed=true); R2 exempts it as interpretive_only citing the claim's own hedge; conflict layer catches the disagreement and prevents a false-safe (verdict=ambiguous, never safe) -- but the underlying semantic disagreement is not resolved.",
        "reason": "Matches c6+c7 in R1's decomposition, both empirical_dependency=true (correctly caught). R2 called BOTH interpretive_only, and its own 'why'/override_rationale text explicitly cites the claim's illustrative '(e.g., childbearing)' aside as the reason ('Childbearing is used as an illustrative instance... not a factual claim'; override_rationale: 'the concrete_restatement itself acknowledges this is offered as an example'). This is EXACTLY the target's own disqualifying condition: 'does_not_count_as_repaired_if: role stays interpretive_only for ANY reason citing the claim's own hedge/aside wording.' The deterministic Layer 1.5 correctly flagged both as R1_R2_SEMANTIC_CONFLICT -> effective_status=unresolved_semantic_conflict -> candidate verdict=ambiguous (this candidate flipped from v1.4.1's safe to v2's ambiguous specifically because of this conflict -- see conflict_effectiveness). The architecture prevented the exact false-safe this whole design was built to catch (this is literally the single target the R1/R2 split was designed around), but R2's hedge-driven exemption on the evidence-bearing pass persists unchanged from v1.3/v1.4.1 -- the split isolates the failure to R2 specifically (R1, evidence-blind, was NOT swayed by the hedge) rather than fixing it."
    },
    {
        "candidate": "H05",
        "run_status": "valid",
        "target_claim_text_v1_3": ["Panels were socially obligated to keep ranking even after ranking had become meaningless.", "Panels were not failing to rank; they were successfully performing ranking as a duty."],
        "expected_role": "factual_dependency", "expected_support": "unsupported",
        "verdict": "FLAGGED_NOT_RESOLVED",
        "failure_mode": "Same FLAGGED_NOT_RESOLVED pattern as H17 -- R1 catches both target claims, R2 downgrades both to interpretive_only, conflict layer intervenes.",
        "reason": "Matched via content to c13 ('...their willingness to keep ranking even after ranking had become meaningless') and c16 ('Panels were not failing to rank; they were successfully performing ranking as a duty' -- near-verbatim). Both: R1 empirical_dependency=true, R2 role=interpretive_only, consistency=R1_R2_SEMANTIC_CONFLICT, effective_status=unresolved_semantic_conflict. Neither resolves to factual_dependency/unsupported as the target requires ('does_not_count_as_protected_if: either target claim no longer resolves factual_dependency/unsupported') -- NOT REPAIRED by the strict rule. Notably the candidate's overall effective_verdict is still 'unsafe' (matches v1.4.1, unchanged), but that is driven by a DIFFERENT claim (c14, cleanly factual_dependency/unsupported/motivation_invention, consistency=consistent) -- the two specific protected targets themselves are not cleanly re-caught, they are caught in the conflict layer's holding pattern instead."
    },
    {
        "candidate": "H14",
        "run_status": "valid",
        "target_claim_text": ["In the 3,700+ already-funded projects, the word 'policy' is not decorative but load-bearing, marking the orientation of the work toward its intended use.", "If the word-removal criterion were applied consistently, it would retroactively delegitimize a large portion of the existing funded portfolio."],
        "expected_role": "factual_dependency", "expected_support": "unsupported",
        "verdict": "MISS",
        "failure_mode": "New pattern, not previously named: R1 and R2 AGREE on role (factual_dependency, no conflict) but R2 judges the SECOND claim 'supported' rather than the expected 'unsupported'.",
        "reason": "Claim 1 (c8) is an exact-text match, resolves factual_dependency/unsupported/problems=['other'] -- matches perfectly. Claim 2 (c9, 'If applied consistently... retroactively delegitimize...') resolves factual_dependency/SUPPORTED, declared, citing two auditor_evidence excerpts (the 3,700+ figure and the removal instruction) with the reasoning: 'The inference... follows directly from these facts without requiring additional empirical support.' This is R2 treating the claim as a valid DEDUCTION from two declared, source-supported premises rather than as an unstated assumption -- a defensible piece of reasoning on its own terms, but it does not match the target's expected_support=unsupported, so per 'does_not_count_as_protected_if: either target claim no longer resolves factual_dependency/unsupported' the target is NOT REPAIRED. This is neither a hedge-driven exemption nor a false-safe (the candidate's overall verdict is still correctly 'unsafe', matching v1.4.1) -- R2 simply reached a more permissive support judgment on a inference-chain claim than the frozen target anticipated. Scored MISS per the mechanical rule with this caveat stated plainly: this is not obviously a regression in the same sense as H08/H09/De Hooch-Z."
    },
    {
        "candidate": "H03",
        "run_status": "valid",
        "expected_candidate_level_effective_verdict": "unsafe",
        "verdict": "FLAGGED_NOT_RESOLVED",
        "failure_mode": "Candidate-level safety property (unsafe) fully held; 2 of 3 required claim-level catches held cleanly; 1 of 3 (target B) fell into R1_R2_SEMANTIC_CONFLICT rather than a clean catch.",
        "reason": "Target A (c6, 'Female researchers are more likely to have had career interruptions (e.g., childbearing)...') = factual_dependency/unsupported, consistency=consistent -- clean catch, hedge NOT used as exemption grounds (negative control holds). Target C (c10, 'The program now works adequately for women who fit the interruption pattern the correction assumes.') = factual_dependency/unsupported, consistency=consistent -- clean catch, 'assumes' hedge NOT used as exemption grounds (negative control holds). Target B (c7, 'The 40-year cutoff... is... an operational patch applied to a proxy...') = R1 empirical_dependency=true, R2 role=interpretive_only, consistency=R1_R2_SEMANTIC_CONFLICT -- NOT a clean catch (R2's own 'why' text frames it as 'an interpretive characterization... not asserting a specific empirical fact,' which is a defensible reading distinct from H17's explicit hedge-citation pattern -- this is NOT the same disqualifying hedge-exemption failure mode, it looks like a genuine boundary judgment, though the conflict layer still correctly refused to let it resolve to a clean 'safe'-compatible state). Candidate-level effective_verdict = 'unsafe', matching the target's primary requirement exactly. Per the target's own wording ('at least the same claim-level catches as v1.2/v1.3/v1.4.1 hold'), 1-of-3 not resolving cleanly means the strict claim-level bar is not fully met, even though the safety-relevant candidate-level outcome is intact. Scored FLAGGED_NOT_RESOLVED to reflect this mixed, partial result honestly rather than rounding it up to REPAIRED or down to MISS."
    },
    {
        "candidate": "05_dutch_painting_soldier/Z",
        "run_status": "schema_invalid",
        "target_claim_text": ["De Hooch's moralism functioned through contrast and implication: the woman drinking the pass-glass while the two men abstain is the moral signal.", "The contrast between the woman drinking and the men not drinking is the moral signal."],
        "verdict": "MISS",
        "failure_mode": "MAX_TOKENS truncation at R2 (identical mechanism to H09) -- transport/budget defect, not semantic.",
        "reason": "R1 correctly extracted both target claims (c12 and c18, both near-verbatim matches, both empirical_dependency=true). R2's response truncated at ~19,874 raw characters (~5,000-token ceiling); the same single-trailing-claim-object extraction artifact occurred, correctly failing schema validation. Disqualified per the target's own explicit rule ('does_not_count_as_protected_if: run_status is schema_invalid or call_failed at either stage'), applied exactly as written -- this is the second of the two v1.4.1 REGRESSION targets, and it remains unresolved this pass for an entirely infrastructural reason unrelated to the conceptual-reframing bypass it was meant to test."
    },
]

n_repaired = sum(1 for t in TARGET_SCORING if t["verdict"] == "REPAIRED")
n_flagged = sum(1 for t in TARGET_SCORING if t["verdict"] == "FLAGGED_NOT_RESOLVED")
n_miss = sum(1 for t in TARGET_SCORING if t["verdict"] == "MISS")

comparison = {
    "_metadata": {
        "purpose": "cj2-stage-b2-v2 (R1->R2 explicit proposition contract) 30-candidate development/regression run vs v1.4.1 (immediate predecessor, single-stage) baseline. Same 30-candidate corpus (12 dev + 18 fresh-batch-1), same model/temperature/timeout as every prior B2 run. R2's schema is substantially more verbose per claim than v1.4.1's (auditor_evidence + why + override_rationale + r1_agreement per claim vs. a flatter structure) -- MAX_TOKENS was carried forward UNCHANGED at 5000, which this run shows to be insufficient for the majority of the corpus.",
        "r1_prompt_sha256": "e29916bf906e3f23e3e6cea0044dae450046d07d9e48149b1e15ef6e476cf858",
        "r2_prompt_sha256": "496f6630ed4eddf057eecc0da77e72d3d821325ec3732d4e48b87c0e9513eefb",
        "harness_sha256": "ae8b2fbdf07eefab8d3fea4ce3684e3cae6364520560b547b3bf94deaa642d01",
        "regression_driver_sha256": "e30d05741821e30ee989eed5dfe4e54dbbfd2606d3e3dee95b6b47d7a1843292",
        "corpus_manifest_sha256": "c372d1cc3292a318b27cdd289630d20e430d600b559b79787c202d18f2cda9b4",
        "acceptance_matrix_sha256": "3d59792b128f5991ce7c8e2b75be23bfb45a1d794dce7a7c4ec56d41d5d593cc",
        "corpus_size": 30,
        "model": "openrouter/claude-sonnet-4.6", "temperature": 0.0, "max_tokens": 5000, "timeout": 120,
        "retry_policy": "none",
        "execution_location": "trident, via localhost CLIProxyAPI, isolated scratch (deleted after hash-verified copy-back)"
    },
    "run_status_summary": {
        "r1": {"valid": 30, "schema_invalid": 0, "call_failed": 0},
        "r2": {"valid": 13, "schema_invalid": 17, "call_failed": 0},
        "combined_b2v2_run_status": {"valid": 13, "schema_invalid": 17},
        "PRIMARY_FINDING": "17 of 30 candidates (56.7%) failed at R2 with an IDENTICAL failure signature: raw response length clustered at 19,771-21,388 characters (~5,000-token ceiling) and an identical schema violation ('claims missing or not a list', caused by the JSON extractor recovering only a single trailing claim object from truncated output). This is a single systemic MAX_TOKENS=5000 insufficiency for R2's per-claim-verbose schema, strongly correlated with R1's claim count (all candidates with <=16 claims succeeded; most with >=17 failed, with a mixed zone at 17-19 claims depending on per-claim verbosity) -- NOT 17 independent content-specific failures. Distinct from and dominant over any semantic finding below.",
        "schema_invalid_candidates": migration["schema_invalid_candidates"],
    },
    "target_scoring": TARGET_SCORING,
    "acceptance_status": {
        "targets_repaired": n_repaired, "targets_flagged_not_resolved": n_flagged, "targets_miss": n_miss,
        "targets_total": 7,
        "status": "FAIL",
        "descriptive_phrase": (
            "FAIL -- 0 of 7 preregistered targets achieve REPAIRED. 3 (H17, H05, H03) reach FLAGGED_NOT_RESOLVED: "
            "the R1/R2 architecture demonstrably prevents a false-safe on every one of these (verdict never resolves "
            "to safe on the strength of these specific claims), but the underlying semantic disagreement is not "
            "resolved and the target's exact expected state is not reached. 4 (H08, H09, H14, De Hooch/Z) are MISS, "
            "for THREE DIFFERENT reasons, not one: H09 and De Hooch/Z are disqualified purely by the systemic "
            "MAX_TOKENS truncation defect (R1 caught both correctly); H08 is a newly observed failure mode where R1 "
            "never extracted the target proposition from its own source field at all; H14 is R2 judging one target "
            "claim's inference chain 'supported' rather than the expected 'unsupported' (role correct, support "
            "verdict more permissive than expected, no hedge-exemption or false-safe involved)."
        )
    },
    "r1_vs_r2_special_diagnostics_all_7_targets": "See target_scoring[].reason for full per-target R1/R2/wrapper breakdown per the 5-category framework (A: both correct, B: R1 catches/R2 misses/wrapper saves, C: R1 misses/R2 catches, D: both miss, E: boundary/other). Category B (R1 catches, R2 misses, wrapper prevents false-safe): H17, H05, and H03's target B. Category D (both miss, in the sense that no clean catch occurs) for H08 by omission rather than misjudgment. H14 does not fit A-E cleanly -- a sixth pattern (both agree on role, disagree on support strength) not named in the original 5-category framework.",
    "global_bidirectional_role_migration": {
        "aggregate_percentage_shift": migration["aggregate_shift"],
        "claim_level_best_effort_migration": migration["claim_migration_report"],
        "raw_vs_effective_v2_role_counts": matrix["raw_vs_effective_role_counts"],
    },
    "r1_r2_disagreement_3x3_matrix": {
        "counts": matrix["r1_r2_matrix_counts"],
        "percentages_of_212_valid_claims": matrix["r1_r2_matrix_pct"],
        "total_valid_claims": matrix["total_valid_claims_for_matrix"],
        "headline": "88 of 212 valid claims (41.5%) are R1=empirically-true / R2=interpretive_only -- the safety-relevant conflict direction -- occurring at a far higher rate than an edge case. 99 (46.7%) are R1=true/R2=factual_dependency (agreement). 25 (11.8%) are R1=false/R2=interpretive_only (agreement, non-empirical). ZERO instances of R1=false/R2=factual_dependency (the 'conservative escalation' direction the design anticipated as a secondary risk never occurred, even once, in this run). ZERO instances of R1=uncertain (R1 never used that value in this run). ZERO raw R2 boundary_ambiguous role (all 'boundary_ambiguous' in the effective/aggregate tables above is the conflict-layer's own reclassification of R1_R2_SEMANTIC_CONFLICT claims, not the model choosing that role directly)."
    },
    "conflict_layer_effectiveness": matrix["conflict_effectiveness"],
    "candidate_verdict_transitions_v1_4_1_to_v2": {
        "migrations": matrix["verdict_migration"],
        "unchanged_counts": matrix["verdict_unchanged_counts"],
        "not_computed_count": len(matrix["verdict_not_computed"]),
        "not_computed_detail": matrix["verdict_not_computed"],
        "note": "Only 13/30 candidates have a computed v2 verdict; the other 17 are 'not_computed' (schema_invalid), not silently treated as unchanged or as any particular verdict."
    },
    "cost_and_complexity": {
        "total_calls": 60, "r1_calls": 30, "r2_calls": 30,
        "call_level_failures_transport": 0,
        "total_wall_clock_seconds": 3660.27,
        "vs_v1_4_1": "v1.4.1 made 30 total calls (single-stage). v2 makes up to 60 (2x call count) plus a materially more verbose R2 completion schema per call (auditor_evidence + why + override_rationale + r1_agreement per claim, vs. v1.4.1's flatter per-claim structure) -- actual compute/token cost is very likely more than 2x v1.4.1's, though exact token usage was not captured by this harness (only completion text was persisted, not the API response's usage object). Approximate: R2 completions averaged output right at or exceeding the 5,000-token MAX_TOKENS ceiling for the majority of the corpus.",
        "not_used_as_acceptance_criterion": True
    },
    "confirmations": {
        "no_post_result_tuning": True,
        "no_prompt_edits": True,
        "no_schema_edits": True,
        "no_threshold_edits": True,
        "no_selective_reruns": True,
        "no_reader_lab_data_used": True,
        "no_cross_publisher_material_used": True,
        "no_stage_c_run": True,
        "cj2_stage_b2_v1_4_1_unmodified": True,
    }
}

out_path = "/Users/stargatesgx/code/disability-collective-ai/automation/.probe_fixtures/cj2-b2-v2-regression/b2-v2-regression-comparison.json"
text = json.dumps(comparison, indent=2, sort_keys=False)
open(out_path, "w").write(text)
print("wrote", out_path)
print("sha256:", hashlib.sha256(text.encode()).hexdigest())
