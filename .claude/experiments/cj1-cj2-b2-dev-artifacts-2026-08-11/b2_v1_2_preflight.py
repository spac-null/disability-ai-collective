import json, re, sys

SYS = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_2_system.txt", encoding="utf-8").read()
USR = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_2_user_template.txt", encoding="utf-8").read()

results = []

def check(name, cond):
    results.append((name, bool(cond)))

# =====================================================================
# SECTION 1 -- all v1.1 checks, re-verified against v1.2 (must still pass)
# =====================================================================

banned_literal = [
    "Pixel", "Siri Sage", "Zen Circuit", "Maya Flux",
    "Deafness", "blindness", "autism", "curb-cut", "curb cut", "ramp",
    "disability_angle", "current_agent", "removed_engine_test",
    "Candidate A", "Candidate B", "Candidate C", "Candidate D",
    "Engine P", "Engine S", "Engine Z", "Engine M",
    "Stage C", "Stage A", "friction_type", "open_question", "ostensible_category",
]
for term in banned_literal:
    check(f"[v1.1] banned term absent -- system: '{term}'", term not in SYS)
    check(f"[v1.1] banned term absent -- user: '{term}'", term not in USR)

persona_hits_sys = re.findall(r"\bpersona\b", SYS, re.IGNORECASE)
persona_hits_usr = re.findall(r"\bpersona\b", USR, re.IGNORECASE)
check("[v1.1] banned word-boundary 'persona' absent -- system", len(persona_hits_sys) == 0)
check("[v1.1] banned word-boundary 'persona' absent -- user", len(persona_hits_usr) == 0)

check("[v1.1] 'effective_verdict' only appears inside a do-NOT-include instruction -- system",
      "effective_verdict" not in SYS.replace("a verdict, effective_verdict, or run_status", ""))
check("[v1.1] 'run_status' only appears inside a do-NOT-include instruction -- system",
      "run_status" not in SYS.replace("a verdict, effective_verdict, or run_status", ""))
check("[v1.1] 'effective_verdict' absent -- user", "effective_verdict" not in USR)
check("[v1.1] 'run_status' absent -- user", "run_status" not in USR)
check("[v1.1] explicit instruction NOT to output verdict/effective_verdict/run_status present",
      "Do NOT include a verdict, effective_verdict, or run_status" in SYS)
check("[v1.1] model-facing bare 'verdict' key absent from JSON examples",
      '"verdict"' not in SYS and '"verdict"' not in USR)

fixture_terms = ["cave dna", "de hooch", "dutch painting", "soldier",
                  "ai cheating", "cheating exam", "carbonate"]
for term in fixture_terms:
    check(f"[v1.1] no development-fixture content -- '{term}' absent (system)", term not in SYS.lower())
    check(f"[v1.1] no development-fixture content -- '{term}' absent (user)", term not in USR.lower())
# v1.2-specific development fixtures introduced by the review's own wording -- also must stay out
for term in ["07_ai_cheating_exam", "aversive or inaccessible", "reluctant to return"]:
    check(f"[v1.2] no development-fixture wording -- '{term}' absent (system)", term.lower() not in SYS.lower())

check("[v1.1] resisting_detail explicitly labeled context-only in system prompt",
      "resisting detail" in SYS.lower() and "not evidence" in SYS.lower())
check("[v1.1] resisting_detail explicitly labeled context-only in user template",
      "CONTEXT ONLY" in USR and "resisting_detail" in USR)

check('[v1.1] "auditable proposition" != "factual" distinction stated',
      '"Auditable" does NOT mean "factual."' in SYS)
check("[v1.1] trigger-word non-determinism guidance present",
      "DO NOT CLASSIFY BY TRIGGER WORDS" in SYS)

check('[v1.1] hedge phrases explicitly do not immunize a claim',
      "HEDGES DO NOT IMMUNIZE A CLAIM" in SYS and "do NOT by themselves make a proposition interpretive" in SYS)
for hedge in ["can be read as", "can be understood as", "suggests", "reveals"]:
    check(f"[v1.1] hedge phrase listed: '{hedge}'", hedge in SYS)

check("[v1.1] old unsafe worked example ('official safety rating') absent",
      "official safety rating" not in SYS and "always provisional" not in SYS)
check("[v1.1] bridge INTERPRETIVE_ONLY example present",
      "shift from treating safety as a settled state" in SYS)
check("[v1.1] bridge FACTUAL_DEPENDENCY example present",
      "Engineers believed collapse was imminent" in SYS)
check("[v1.1] sorting-algorithm example still removed",
      "sorting algorithm" not in SYS.lower())

check("[v1.1] supported requires >=1 supports_claim citation",
      "cite at least one exact excerpt from source_snapshot with relation \"supports_claim.\"" in SYS)
check("[v1.1] unsupported requires >=1 does_not_establish_claim citation",
      "cite at least one exact excerpt showing the closest real fact" in SYS and "does_not_establish_claim" in SYS)

check("[v1.1] field coverage instruction present",
      "FIELD COVERAGE -- REQUIRED FOR EVERY FIELD INSTANCE SUPPLIED" in SYS)

check("[v1.1] candidate seed_evidence_refs present in user template",
      "seed_evidence_refs" in USR and "CANDIDATE-DECLARED SEED EVIDENCE" in USR)
check("[v1.1] system prompt introduces CANDIDATE-DECLARED SEED EVIDENCE input",
      "CANDIDATE-DECLARED SEED EVIDENCE" in SYS)
check("[v1.1] support and declaration explicitly described as separate/independent questions",
      "TWO SEPARATE QUESTIONS FOR EVERY FACTUAL_DEPENDENCY" in SYS and "These are independent" in SYS)
check("[v1.1] declaration=declared requires non-empty declared_refs stated",
      'declaration="declared" requires declared_refs to contain at least one ID' in SYS)
check("[v1.1] declared_refs restricted to candidate-declared cj1:aN / obs:N IDs",
      "Never populate declared_refs with a canonical anchor ID the candidate itself did not declare" in SYS)
check("[v1.1] obs:N observation prose explicitly cannot establish itself",
      "does NOT certify that the obs:N's own OBSERVATION PROSE" in SYS)
check("[v1.1] interpretive_only / boundary_ambiguous declared_refs=[] stated",
      'interpretive_only: support="not_required", declaration="not_applicable", declared_refs=[]' in SYS
      and 'boundary_ambiguous: support="uncertain", declaration="uncertain", declared_refs=[]' in SYS)

check("[v1.1] importance definitions present",
      "load_bearing: removing this proposition materially collapses" in SYS
      and "supporting: the proposition materially strengthens" in SYS
      and "incidental: the proposition is substantive" in SYS)
check("[v1.1] importance stated as diagnostic-only, never an exemption",
      "IMPORTANCE -- DIAGNOSTIC ONLY, NEVER AN EXEMPTION" in SYS
      and "never exempts an unsupported or undeclared factual claim" in SYS)
problems_enum = ["modality_hardening", "causality_hardening", "mechanism_invention",
                  "necessity_dependency_hardening", "motivation_invention",
                  "population_relation_hardening", "undeclared_factual_dependency", "other"]
check("[v1.1] complete problems enum present in system prompt (unchanged, no schema change)",
      all(p in SYS for p in problems_enum))
check("[v1.1] unsupported -> >=1 semantic problem value required",
      'support="unsupported" requires problems to contain at least one of the semantic problem values' in SYS)
check("[v1.1] undeclared -> undeclared_factual_dependency required",
      'declaration="undeclared" requires problems to contain undeclared_factual_dependency' in SYS)
check("[v1.1] claim may carry multiple problems values stated",
      "may carry multiple problems values when more than one applies" in SYS)

required_ids = [
    "additional_source_observations[0].observation",
    "engine_move", "seed_engagement", "interpretive_inference",
    "conceptual_shift", "claimed_contribution",
]
for fid in required_ids:
    check(f"[v1.1] exact source_field identifier '{fid}' present in user template",
          f"source_field: {fid}" in USR)
    check(f"[v1.1] exact source_field identifier '{fid}' present in system prompt", fid in SYS)
check("[v1.1] conceptual_shift block marked omit-if-null in user template",
      "omit this block and its field_audits entry entirely if conceptual_shift is null" in USR)
check("[v1.1] additional_source_observations repeat/omit instruction present in user template",
      "omit entirely if the candidate declared none" in USR)

check("[v1.1] system prompt states auditor does not know which engine produced the candidate",
      "You do NOT know which perceptual engine produced this candidate" in SYS)
check("[v1.1] prompt itself makes no claim about the development set being held-out",
      "held-out" not in SYS.lower() and "held-out" not in USR.lower())

# =====================================================================
# SECTION 2 -- NEW v1.2 checks (Corrections A-D)
# =====================================================================

check("[v1.2] atomic/mixed-proposition decomposition instruction present",
      "ATOMIC CLAIM DECOMPOSITION" in SYS
      and "split it into separate auditable propositions" in SYS)
check("[v1.2] interpretive wrapper explicitly does not shield embedded fact",
      "AN INTERPRETIVE WRAPPER DOES NOT SHIELD THE FACTS INSIDE IT" in SYS
      and "An interpretive wrapper does not convert the factual material inside it into interpretation." in SYS)
check("[v1.2] queue/customers generic decomposition example present",
      "training customers to accept delay" in SYS and "queue" in SYS.lower())
check("[v1.2] interface/two-populations generic decomposition example present",
      "produced two incompatible user populations" in SYS)

check("[v1.2] support explicitly requires equal-or-greater factual strength",
      "SUPPORT MEANS EQUAL-OR-GREATER FACTUAL STRENGTH" in SYS
      and "at the same or greater factual strength" in SYS)
check("[v1.2] 'reasonable/plausible paraphrase' explicitly rejected as the support test",
      "NOT A PLAUSIBLE PARAPHRASE" in SYS
      and "is not \"is the candidate's wording a reasonable, plausible, natural, or sympathetic reading" in SYS
      and "regardless of how reasonable, sympathetic, or intuitively correct the stronger wording seems" in SYS)
check("[v1.2] new-concept-allowed vs stronger-world-fact-not-allowed rule stated",
      "A NEW CONCEPT" in SYS and "is always allowed without source support" in SYS
      and "A STRONGER WORLD-FACT is never allowed without source support" in SYS)

for pattern in ["MODALITY (including capability)", "CAUSALITY:", "NECESSITY/DEPENDENCY:",
                "MOTIVATION:", "CAPABILITY:", "POPULATION LINKAGE:",
                "TEMPORAL/GENERALIZATION SCOPE:"]:
    check(f"[v1.2] strengthening-pattern check present: '{pattern}'", pattern in SYS)
check("[v1.2] capability strengthening explicitly mapped to modality_hardening (no schema change)",
      "capability is a modal claim; there is no separate capability tag in the problems list" in SYS)
check("[v1.2] temporal/generalization scope explicitly mapped to 'other' by default",
      "-> other, unless the broadened claim also fits one of the six patterns above" in SYS)

check("[v1.2] multiple claim objects per source_field explicitly allowed (prose)",
      "Multiple claim objects may share the same source_field." in SYS)
check("[v1.2] field coverage section cross-references multi-claim decomposition",
      "A field_audits entry's claim_ids may contain more than one claim_id when atomic decomposition" in SYS)
check("[v1.2] do-not-compress-to-keep-count-low instruction present",
      "Do not compress two propositions into one claim merely to keep the count low" in SYS)

check("[v1.2] short/contiguous auditor-evidence requirement present",
      "COPY DISCIPLINE -- EACH CITATION MUST BE ONE SHORT, CONTIGUOUS, EXACT SUBSTRING" in SYS)
check("[v1.2] explicit ban on joining across a paragraph break",
      "joining two sentences across a paragraph break into one continuous string" in SYS)
check("[v1.2] explicit ban on removing a parenthetical from inside a quotation",
      "removing a parenthetical or aside from inside a quotation" in SYS)
check("[v1.2] explicit ban on splicing quote fragments across an attribution clause",
      "splicing two quoted fragments together across an intervening attribution clause" in SYS)
check("[v1.2] non-contiguous evidence -> multiple auditor_evidence entries required",
      "emit TWO separate auditor_evidence entries, one per passage" in SYS)

check("[v1.2] no resolver-expansion language anywhere in the prompt",
      "fuzzy" not in SYS.lower() and "whitespace-collapse repair" not in SYS.lower()
      and "resolver" not in SYS.lower())

# JSON examples parse, including the new atomic-decomposition example
json_blocks = []
brace_start = None
depth = 0
for i, ch in enumerate(SYS):
    if ch == "{":
        if depth == 0:
            brace_start = i
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0 and brace_start is not None:
            json_blocks.append(SYS[brace_start:i + 1])
            brace_start = None

parsed = []
for idx, block in enumerate(json_blocks):
    try:
        obj = json.loads(block)
        parsed.append(obj)
        check(f"[v1.1] JSON example #{idx} parses", True)
        block_str = json.dumps(obj)
        check(f"[v1.1] JSON example #{idx} has no verdict/effective_verdict/run_status key",
              "verdict" not in block_str and "run_status" not in block_str)
    except Exception:
        check(f"[v1.1] JSON example #{idx} parses", False)

check(f"[v1.1] found >=4 JSON example blocks in system prompt (got {len(json_blocks)})", len(json_blocks) >= 4)

decomposition_example = None
for obj in parsed:
    if isinstance(obj, dict) and "claims" in obj and len(obj.get("claims", [])) == 2:
        decomposition_example = obj
        break
check("[v1.2] a JSON example demonstrates two claims sharing the same source_field",
      decomposition_example is not None
      and len({c.get("source_field") for c in decomposition_example["claims"]}) == 1)
if decomposition_example:
    fa = decomposition_example.get("field_audits", [])
    check("[v1.2] that example's field_audits entry lists both claim_ids together",
          len(fa) == 1 and set(fa[0].get("claim_ids", [])) == {"c4", "c5"})
else:
    check("[v1.2] that example's field_audits entry lists both claim_ids together", False)

overall = all(v for _, v in results)

for name, ok in results:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")

print()
print("OVERALL:", "PASS" if overall else "FAIL", f"({sum(1 for _,v in results if v)}/{len(results)})")
if not overall:
    print("\nFAILED CHECKS:")
    for name, ok in results:
        if not ok:
            print(" -", name)
