import json, re

SYS = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_4_system.txt", encoding="utf-8").read()
USR = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_1_user_template.txt", encoding="utf-8").read()
v13 = open("/Users/stargatesgx/code/disability-collective-ai/automation/.probe_fixtures/cj2-reference-probe-1/frozen_prompts/cj2-stage-b2-v1.3.txt").read()

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ---- carry-forward: banned terms / schema-unchanged checks ----
banned_literal = [
    "Pixel", "Siri Sage", "Zen Circuit", "Maya Flux",
    "Deafness", "blindness", "autism", "curb-cut", "curb cut", "ramp",
    "disability_angle", "current_agent", "removed_engine_test",
    "Candidate A", "Candidate B", "Candidate C", "Candidate D",
    "Engine P", "Engine S", "Engine Z", "Engine M",
    "Stage C", "Stage A", "friction_type", "open_question", "ostensible_category",
]
for term in banned_literal:
    check(f"[carry] banned term absent -- system: '{term}'", term not in SYS)

check("[carry] banned word-boundary 'persona' absent -- system", len(re.findall(r"\bpersona\b", SYS, re.IGNORECASE)) == 0)
check("[carry] 'effective_verdict' only inside do-NOT-include instruction",
      "effective_verdict" not in SYS.replace("a verdict, effective_verdict, or run_status", ""))
check("[carry] 'run_status' only inside do-NOT-include instruction",
      "run_status" not in SYS.replace("a verdict, effective_verdict, or run_status", ""))
check("[carry] explicit do-NOT-include instruction present",
      "Do NOT include a verdict, effective_verdict, or run_status" in SYS)

dev_fixture_terms = ["cave dna", "de hooch", "dutch painting", "soldier",
                      "ai cheating", "cheating exam", "carbonate", "reluctant to return", "moral signal"]
for term in dev_fixture_terms:
    check(f"[carry] no development-fixture wording -- '{term}' absent", term.lower() not in SYS.lower())

freshbatch_terms = [
    "NSFC", "young scientists fund", "male applicants must be under 35",
    "socially obligated to keep ranking", "SNSF", "swiss national science foundation",
    "splitting hairs that might not have existed", "NIH", "3,700", "policymakers are not considered",
    "phosphine", "azine", "solar eclipse", "corona", "funders should look beyond",
    "resolution is a property of the underlying signal", "specifically five years' worth",
    "such as childbearing", "e.g., childbearing", "childbearing", "grading scale", "pluses and minuses",
]
for term in freshbatch_terms:
    check(f"[NEW] no fresh-batch-1 fixture wording -- '{term}' absent", term.lower() not in SYS.lower())

check("[carry] resisting_detail context-only present (system)",
      "resisting detail" in SYS.lower() and "not evidence" in SYS.lower())
check("[carry] resisting_detail context-only present (user template)",
      "CONTEXT ONLY" in USR and "resisting_detail" in USR)
check('[carry] "auditable proposition" != "factual" distinction stated',
      '"Auditable" does NOT mean "factual."' in SYS)
check("[carry] trigger-word guidance present", "DO NOT CLASSIFY BY TRIGGER WORDS" in SYS)
check("[carry] hedges-do-not-immunize section still present (pre-existing, unchanged)",
      "HEDGES DO NOT IMMUNIZE A CLAIM" in SYS)
check("[carry] bridge INTERPRETIVE_ONLY example present",
      "shift from treating safety as a settled state" in SYS)
check("[carry] bridge FACTUAL_DEPENDENCY example present",
      "Engineers believed collapse was imminent" in SYS)
check("[carry] atomic claim decomposition present",
      "ATOMIC CLAIM DECOMPOSITION" in SYS and "Multiple claim objects may share the same source_field." in SYS)
check("[carry] copy discipline present",
      "COPY DISCIPLINE -- EACH CITATION MUST BE ONE SHORT, CONTIGUOUS, EXACT SUBSTRING" in SYS)
problems_enum = ["modality_hardening", "causality_hardening", "mechanism_invention",
                  "necessity_dependency_hardening", "motivation_invention",
                  "population_relation_hardening", "undeclared_factual_dependency", "other"]
check("[carry] complete problems enum unchanged (no schema change)", all(p in SYS for p in problems_enum))
check("[carry] no held-out claim", "held-out" not in SYS.lower())

for header in ["WHAT COUNTS AS AN AUDITABLE PROPOSITION", "THE THREE ROLES", "ATOMIC CLAIM DECOMPOSITION",
               "HEDGES DO NOT IMMUNIZE A CLAIM", "DO NOT CLASSIFY BY TRIGGER WORDS",
               "TWO SEPARATE QUESTIONS FOR EVERY FACTUAL_DEPENDENCY",
               "SUPPORT MEANS EQUAL-OR-GREATER FACTUAL STRENGTH", "DECLARATION LINEAGE",
               "FACTUAL AUTHORITY", "AUDITOR EVIDENCE", "COPY DISCIPLINE",
               "IMPORTANCE", "PROBLEMS -- ALLOWED VALUES", "FIELD INVARIANTS", "FIELD COVERAGE", "OUTPUT"]:
    check(f"[carry] section preserved: {header!r}", header in SYS)

# JSON examples still 4, parse, no verdict/run_status keys
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
for idx, block in enumerate(json_blocks):
    try:
        obj = json.loads(block)
        check(f"[carry] JSON example #{idx} parses", True)
        block_str = json.dumps(obj)
        check(f"[carry] JSON example #{idx} no verdict/run_status key",
              "verdict" not in block_str and "run_status" not in block_str)
    except Exception:
        check(f"[carry] JSON example #{idx} parses", False)
check(f"[carry] found 4 JSON example blocks (unchanged, got {len(json_blocks)})", len(json_blocks) == 4)

# ---- NEW v1.4 checks ----
check("[v1.4] MANDATORY ROLE-DECISION PROCEDURE header present",
      "MANDATORY ROLE-DECISION PROCEDURE -- FOLLOW IN ORDER, FOR EVERY CLAIM, BEFORE ASSIGNING ROLE" in SYS)
check("[v1.4] procedure stated as not optional", "This procedure is not optional and not a suggestion." in SYS)
check("[v1.4] STEP 1 header present", "STEP 1 -- WORLD-TRUTH TEST" in SYS)
check("[v1.4] STEP 2 header present", "STEP 2 -- MANDATORY CONCRETE RESTATEMENT" in SYS)
check("[v1.4] STEP 3 header present", "STEP 3 -- HEDGE HANDLING: HEDGING AFFECTS STRENGTH, NEVER ROLE" in SYS)
check("[v1.4] STEP 4 header present", "STEP 4 -- ROLE" in SYS)

check("[v1.4] subject list broadened to include individual people",
      "a person, an individual, an institution" in SYS)
check("[v1.4] individual-vs-institution equivalence explicitly stated",
      "exactly as capable of being a factual_dependency as a proposition about an institution's" in SYS)

check("[v1.4] step2 says perform test BEFORE assigning role, do not skip",
      "perform the CONCRETE RESTATEMENT TEST BEFORE assigning role" in SYS
      and "Do not skip this step" in SYS)
for p in ["The policy encodes an assumption that X.", "The system obligates actors to do X.",
          "The measurement contains no remaining signal.",
          "A feature is substantively characteristic across a population."]:
    check(f"[v1.4] generic pattern retained: {p!r}", p in SYS)

check("[v1.4] hedge word list present",
      all(w in SYS for w in ['"may,"', '"might,"', '"appears,"', '"suggests,"', '"assumed,"',
                              '"potentially,"', '"e.g.,"', '"likely"']))
check("[v1.4] hedge-affects-strength-not-role statement present",
      "Candidate hedging affects how strongly a proposition is being asserted" in SYS
      and "does NOT affect whether that proposition is the kind of thing that needs factual support" in SYS)
check("[v1.4] 'may encode an assumption' generic example present",
      '"The rule may encode an assumption that X"' in SYS)
check("[v1.4] exemplifying-aside handling present",
      "An exemplifying aside" in SYS and "does NOT, by itself, convert the claim it is attached to into pure interpretation" in SYS)

check("[v1.4] Step 4 interpretive_only-permitted-only-when statement present",
      "interpretive_only is permitted ONLY when the argumentative force of the claim does NOT depend on any additional empirical proposition being true" in SYS)
check("[v1.4] explicit precedence rule present",
      "ROLE CLASSIFICATION MUST NOT BE OVERRIDDEN BY RHETORICAL HEDGING." in SYS)
check("[v1.4] precedence rule gives correct order (identify proposition/strength first, THEN decide support)",
      "First identify the proposition and its actual expressed strength (Steps 1-3). Only then decide whether that proposition requires factual support (Step 4)." in SYS)

check("[v1.4] anti-overcorrection rule retained (kept, not removed)",
      "DO NOT OVERCORRECT -- A METAPHOR IS STILL A METAPHOR" in SYS
      and "Declarative grammar alone" in SYS)

# no candidate-specific H08/H17/H09/DeHooch-Z wording
check("[v1.4] no verbatim H08/H09/H17/DeHooch-Z fixture text (see freshbatch/dev checks above)", True)

# structural: no duplicate section headers (old "ROLE MUST BE DETERMINED..." / bare "CONCRETE RESTATEMENT TEST" removed, replaced by the new procedure)
check("[v1.4] old standalone 'ROLE MUST BE DETERMINED BY PROPOSITIONAL DEPENDENCY' header removed (superseded by the new procedure)",
      "ROLE MUST BE DETERMINED BY PROPOSITIONAL DEPENDENCY, NOT BY SUBJECT TYPE OR CONCEPTUAL STYLE" not in SYS)
check("[v1.4] old standalone 'CONCRETE RESTATEMENT TEST' bare header removed (now STEP 2 heading)",
      SYS.count("CONCRETE RESTATEMENT TEST") == 0 or "STEP 2 -- MANDATORY CONCRETE RESTATEMENT" in SYS)

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
