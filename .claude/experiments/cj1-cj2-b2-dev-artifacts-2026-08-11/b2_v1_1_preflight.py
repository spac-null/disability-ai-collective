import json, re, sys

SYS = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_1_system.txt", encoding="utf-8").read()
USR = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_1_user_template.txt", encoding="utf-8").read()

results = []

def check(name, cond):
    results.append((name, bool(cond)))

def norm(s):
    return re.sub(r"\s+", " ", s)

NSYS, NUSR = norm(SYS), norm(USR)

# ---- banned terms (word-boundary where needed) ----
banned_literal = [
    "Pixel", "Siri Sage", "Zen Circuit", "Maya Flux",
    "Deafness", "blindness", "autism", "curb-cut", "curb cut", "ramp",
    "disability_angle", "current_agent", "removed_engine_test",
    "Candidate A", "Candidate B", "Candidate C", "Candidate D",
    "Engine P", "Engine S", "Engine Z", "Engine M",
    "Stage C", "Stage A", "friction_type", "open_question", "ostensible_category",
]
for term in banned_literal:
    check(f"banned term absent -- system: '{term}'", term not in SYS)
    check(f"banned term absent -- user: '{term}'", term not in USR)

# 'persona' word-boundary (allow 'personally')
persona_hits_sys = re.findall(r"\bpersona\b", SYS, re.IGNORECASE)
persona_hits_usr = re.findall(r"\bpersona\b", USR, re.IGNORECASE)
check("banned word-boundary 'persona' absent -- system", len(persona_hits_sys) == 0)
check("banned word-boundary 'persona' absent -- user", len(persona_hits_usr) == 0)

# ---- verdict/run_status/effective_verdict ----
check("'effective_verdict' only appears inside a do-NOT-include instruction -- system",
      "effective_verdict" not in SYS.replace("a verdict, effective_verdict, or run_status", ""))
check("'run_status' only appears inside a do-NOT-include instruction -- system",
      "run_status" not in SYS.replace("a verdict, effective_verdict, or run_status", ""))
check("'effective_verdict' absent -- user", "effective_verdict" not in USR)
check("'run_status' absent -- user", "run_status" not in USR)
check("explicit instruction NOT to output verdict/effective_verdict/run_status present",
      "Do NOT include a verdict, effective_verdict, or run_status" in SYS)
check("model-facing bare 'verdict' key absent from JSON examples",
      '"verdict"' not in SYS and '"verdict"' not in USR)

# ---- no development-fixture content ----
fixture_terms = ["cave dna", "de hooch", "dutch painting", "soldier",
                  "ai cheating", "cheating exam", "carbonate"]
for term in fixture_terms:
    check(f"no development-fixture content -- '{term}' absent (system)", term not in SYS.lower())
    check(f"no development-fixture content -- '{term}' absent (user)", term not in USR.lower())

# ---- resisting_detail context-only ----
check("resisting_detail explicitly labeled context-only in system prompt",
      "resisting detail" in SYS.lower() and "not evidence" in SYS.lower())
check("resisting_detail explicitly labeled context-only in user template",
      "CONTEXT ONLY" in USR and "resisting_detail" in USR)

# ---- auditable != factual ----
check('"auditable proposition" != "factual" distinction stated',
      '"Auditable" does NOT mean "factual."' in SYS)

# ---- trigger-word guidance ----
check("trigger-word non-determinism guidance present",
      "DO NOT CLASSIFY BY TRIGGER WORDS" in SYS)

# ---- hedge guidance (NEW) ----
check('hedge phrases ("can be read as"/"suggests"/etc.) explicitly do not immunize a claim',
      "HEDGES DO NOT IMMUNIZE A CLAIM" in SYS and "do NOT by themselves make a proposition interpretive" in SYS)
for hedge in ["can be read as", "can be understood as", "suggests", "reveals"]:
    check(f"hedge phrase listed: '{hedge}'", hedge in SYS)

# ---- new worked example is safe (no unsupported world-fact leftover) ----
check("old unsafe worked example ('official safety rating') absent",
      "official safety rating" not in SYS and "always provisional" not in SYS)
check("new INTERPRETIVE_ONLY bridge example present",
      "shift from treating safety as a settled state" in SYS)
check("new FACTUAL_DEPENDENCY bridge example present",
      "Engineers believed collapse was imminent" in SYS)
check("sorting-algorithm example removed (no concrete-source-free example left)",
      "sorting algorithm" not in SYS.lower())

# ---- supported/unsupported evidence requirements ----
check("supported requires >=1 supports_claim citation",
      "cite at least one exact excerpt from source_snapshot with relation \"supports_claim.\"" in SYS)
check("unsupported requires >=1 does_not_establish_claim citation",
      "cite at least one exact excerpt showing the closest real fact" in SYS and "does_not_establish_claim" in SYS)

# ---- field coverage ----
check("field coverage (one entry per field instance) instruction present",
      "FIELD COVERAGE -- REQUIRED FOR EVERY FIELD INSTANCE SUPPLIED" in SYS)

# ---- correction 1: declaration lineage ----
check("candidate seed_evidence_refs present in user template",
      "seed_evidence_refs" in USR and "CANDIDATE-DECLARED SEED EVIDENCE" in USR)
check("system prompt introduces CANDIDATE-DECLARED SEED EVIDENCE input",
      "CANDIDATE-DECLARED SEED EVIDENCE" in SYS)
check("support and declaration explicitly described as separate/independent questions",
      "TWO SEPARATE QUESTIONS FOR EVERY FACTUAL_DEPENDENCY" in SYS and "These are independent" in SYS)
check("declaration=declared requires non-empty declared_refs stated",
      'declaration="declared" requires declared_refs to contain at least one ID' in SYS)
check("declared_refs restricted to candidate-declared cj1:aN / obs:N IDs",
      "Never populate declared_refs with a canonical anchor ID the candidate itself did not declare" in SYS)
check("obs:N observation prose explicitly cannot establish itself merely because excerpt is real",
      "does NOT certify that the obs:N's own OBSERVATION PROSE" in SYS)
check("interpretive_only / boundary_ambiguous declared_refs=[] stated",
      'interpretive_only: support="not_required", declaration="not_applicable", declared_refs=[]' in SYS
      and 'boundary_ambiguous: support="uncertain", declaration="uncertain", declared_refs=[]' in SYS)

# ---- correction 3: importance / problems ----
check("importance definitions present (load_bearing/supporting/incidental)",
      "load_bearing: removing this proposition materially collapses" in SYS
      and "supporting: the proposition materially strengthens" in SYS
      and "incidental: the proposition is substantive" in SYS)
check("importance stated as diagnostic-only, never an exemption",
      "IMPORTANCE -- DIAGNOSTIC ONLY, NEVER AN EXEMPTION" in SYS
      and "never exempts an unsupported or undeclared factual claim" in SYS)
problems_enum = ["modality_hardening", "causality_hardening", "mechanism_invention",
                  "necessity_dependency_hardening", "motivation_invention",
                  "population_relation_hardening", "undeclared_factual_dependency", "other"]
check("complete problems enum present in system prompt",
      all(p in SYS for p in problems_enum))
check("unsupported -> >=1 semantic problem value required",
      'support="unsupported" requires problems to contain at least one of the semantic problem values' in SYS)
check("undeclared -> undeclared_factual_dependency required",
      'declaration="undeclared" requires problems to contain undeclared_factual_dependency' in SYS)
check("claim may carry multiple problems values stated",
      "may carry multiple problems values when more than one applies" in SYS)

# ---- correction 4: exact source_field identifiers ----
required_ids = [
    "additional_source_observations[0].observation",
    "engine_move",
    "seed_engagement",
    "interpretive_inference",
    "conceptual_shift",
    "claimed_contribution",
]
for fid in required_ids:
    check(f"exact source_field identifier '{fid}' present in user template",
          f"source_field: {fid}" in USR)
    check(f"exact source_field identifier '{fid}' present in system prompt (schema/example)",
          fid in SYS)
check("conceptual_shift block marked omit-if-null in user template",
      "omit this block and its field_audits entry entirely if conceptual_shift is null" in USR)
check("additional_source_observations repeat/omit instruction present in user template",
      "omit entirely if the candidate declared none" in USR)

# ---- JSON examples parse ----
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
            json_blocks.append(SYS[brace_start:i+1])
            brace_start = None

parsed_ok = 0
for idx, block in enumerate(json_blocks):
    try:
        obj = json.loads(block)
        parsed_ok += 1
        # no verdict/run_status leakage inside any parsed example
        block_str = json.dumps(obj)
        check(f"JSON example #{idx} parses", True)
        check(f"JSON example #{idx} has no verdict/effective_verdict/run_status key",
              "verdict" not in block_str and "run_status" not in block_str)
    except Exception as e:
        check(f"JSON example #{idx} parses", False)

check(f"found >=3 JSON example blocks in system prompt (got {len(json_blocks)})", len(json_blocks) >= 3)

# ---- engine-blindness / B2 remains engine-blind ----
check("system prompt states auditor does not know which engine produced the candidate",
      "You do NOT know which perceptual engine produced this candidate" in SYS)

# ---- methodology terminology (checked separately against the versioning note, not the prompt) ----
check("prompt itself makes no claim about the development set being held-out",
      "held-out" not in SYS.lower() and "held-out" not in USR.lower())

overall = all(v for _, v in results)

for name, ok in results:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")

print()
print("OVERALL:", "PASS" if overall else "FAIL")
if not overall:
    print("\nFAILED CHECKS:")
    for name, ok in results:
        if not ok:
            print(" -", name)
