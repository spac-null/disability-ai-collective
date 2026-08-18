import json, re

SYS = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_3_system.txt", encoding="utf-8").read()
# v1.3 user template is byte-identical to v1.2's -- no schema/template change.
USR = open("/Users/stargatesgx/code/disability-collective-ai/automation/.probe_fixtures/cj2-reference-probe-1/frozen_prompts/cj2-stage-b2-v1.2.txt", encoding="utf-8").read()
# (USR above is actually the v1.2 SYSTEM prompt reused as a stand-in path; real USR check below
#  loads the real v1.1/v1.2 user template file instead.)
USR = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_2_user_template.txt", encoding="utf-8").read() \
    if False else None

# Load the actual frozen v1.1/v1.2 user template (byte-identical across v1.1->v1.2->v1.3)
import pathlib
USR_PATH = pathlib.Path("/Users/stargatesgx/code/disability-collective-ai/automation/.probe_fixtures/cj2-reference-probe-1/frozen_prompts")
# The user template itself isn't stored as a separate frozen file on disk in this repo's
# convention (only the system prompt is) -- reconstruct from the experiment doc's frozen
# v1.1 template text stored earlier in this job's tmp dir.
USR = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_1_user_template.txt", encoding="utf-8").read()

results = []

def check(name, cond):
    results.append((name, bool(cond)))

# ---- carry-forward: all v1.1/v1.2 checks, re-verified against v1.3 ----
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

persona_hits_sys = re.findall(r"\bpersona\b", SYS, re.IGNORECASE)
check("[carry] banned word-boundary 'persona' absent -- system", len(persona_hits_sys) == 0)

check("[carry] 'effective_verdict' only appears inside a do-NOT-include instruction -- system",
      "effective_verdict" not in SYS.replace("a verdict, effective_verdict, or run_status", ""))
check("[carry] 'run_status' only appears inside a do-NOT-include instruction -- system",
      "run_status" not in SYS.replace("a verdict, effective_verdict, or run_status", ""))
check("[carry] explicit instruction NOT to output verdict/effective_verdict/run_status present",
      "Do NOT include a verdict, effective_verdict, or run_status" in SYS)

# development-set fixture leakage (v1.1/v1.2 convention)
dev_fixture_terms = ["cave dna", "de hooch", "dutch painting", "soldier",
                      "ai cheating", "cheating exam", "carbonate", "reluctant to return"]
for term in dev_fixture_terms:
    check(f"[carry] no development-fixture wording -- '{term}' absent (system)", term.lower() not in SYS.lower())

# fresh-batch-1 fixture leakage (NEW convention for v1.3, since v1.3 was designed
# from the fresh-batch failures -- must not copy the fresh candidates verbatim)
freshbatch_terms = [
    "NSFC", "young scientists fund", "male applicants must be under 35",
    "socially obligated to keep ranking", "SNSF", "swiss national science foundation",
    "splitting hairs that might not have existed", "NIH", "3,700", "policymakers are not considered",
    "phosphine", "azine", "solar eclipse", "corona", "funders should look beyond",
]
for term in freshbatch_terms:
    check(f"[NEW v1.3] no fresh-batch-1 fixture wording -- '{term}' absent (system)", term.lower() not in SYS.lower())

check("[carry] resisting_detail explicitly labeled context-only in system prompt",
      "resisting detail" in SYS.lower() and "not evidence" in SYS.lower())
check("[carry] resisting_detail explicitly labeled context-only in user template",
      "CONTEXT ONLY" in USR and "resisting_detail" in USR)

check('[carry] "auditable proposition" != "factual" distinction stated',
      '"Auditable" does NOT mean "factual."' in SYS)
check("[carry] trigger-word non-determinism guidance present",
      "DO NOT CLASSIFY BY TRIGGER WORDS" in SYS)
check('[carry] hedge phrases explicitly do not immunize a claim',
      "HEDGES DO NOT IMMUNIZE A CLAIM" in SYS)

check("[carry] old unsafe worked example ('official safety rating') absent",
      "official safety rating" not in SYS and "always provisional" not in SYS)
check("[carry] bridge INTERPRETIVE_ONLY example present",
      "shift from treating safety as a settled state" in SYS)
check("[carry] bridge FACTUAL_DEPENDENCY example present",
      "Engineers believed collapse was imminent" in SYS)

check("[carry] supported requires >=1 supports_claim citation",
      "cite at least one exact excerpt from source_snapshot with relation \"supports_claim.\"" in SYS)
check("[carry] unsupported requires >=1 does_not_establish_claim citation",
      "cite at least one exact excerpt showing the closest real fact" in SYS and "does_not_establish_claim" in SYS)
check("[carry] field coverage instruction present",
      "FIELD COVERAGE -- REQUIRED FOR EVERY FIELD INSTANCE SUPPLIED" in SYS)
check("[carry] candidate seed_evidence_refs present in user template",
      "seed_evidence_refs" in USR and "CANDIDATE-DECLARED SEED EVIDENCE" in USR)
check("[carry] system prompt introduces CANDIDATE-DECLARED SEED EVIDENCE input",
      "CANDIDATE-DECLARED SEED EVIDENCE" in SYS)
check("[carry] declared_refs restricted to candidate-declared cj1:aN / obs:N IDs",
      "Never populate declared_refs with a canonical anchor ID the candidate itself did not declare" in SYS)

problems_enum = ["modality_hardening", "causality_hardening", "mechanism_invention",
                  "necessity_dependency_hardening", "motivation_invention",
                  "population_relation_hardening", "undeclared_factual_dependency", "other"]
check("[carry] complete problems enum present, UNCHANGED (no schema change)",
      all(p in SYS for p in problems_enum))
check("[carry] atomic claim decomposition (mixed-content) instruction present",
      "ATOMIC CLAIM DECOMPOSITION" in SYS and "Multiple claim objects may share the same source_field." in SYS)
check("[carry] copy-discipline (short/contiguous auditor evidence) present",
      "COPY DISCIPLINE -- EACH CITATION MUST BE ONE SHORT, CONTIGUOUS, EXACT SUBSTRING" in SYS)

# ---- NEW v1.3 checks ----
check("[v1.3] new role-determination section header present",
      "ROLE MUST BE DETERMINED BY PROPOSITIONAL DEPENDENCY, NOT BY SUBJECT TYPE OR CONCEPTUAL STYLE" in SYS)
check("[v1.3] explicit subject-type-does-not-settle-role statement present",
      "never classified interpretive_only merely because its subject is an institution" in SYS)
check("[v1.3] 'what must actually be true in the world' test present",
      "what must actually be true in the world for this proposition to hold?" in SYS)
check("[v1.3] system-dependency verb list present (does/assumes/requires/causes/encodes/generalizes/designed/operationally depends)",
      all(w in SYS for w in ["assumes", "requires", "causes", "encodes", "generalizes across",
                              "designed to accomplish", "operationally depends"]))
check("[v1.3] CONCRETE RESTATEMENT TEST section present",
      "CONCRETE RESTATEMENT TEST" in SYS)
check("[v1.3] concrete-restatement-without-strengthening instruction present",
      "restate the proposition as the nearest concrete claim" in SYS and "without strengthening it" in SYS)

generic_patterns = [
    "The policy encodes an assumption that X.",
    "The system obligates actors to do X.",
    "The measurement contains no remaining signal.",
    "A feature is substantively characteristic across a population.",
]
for p in generic_patterns:
    check(f"[v1.3] generic pattern present: {p!r}", p in SYS)

check("[v1.3] anti-overcorrection section header present",
      "DO NOT OVERCORRECT -- A METAPHOR IS STILL A METAPHOR" in SYS)
check("[v1.3] 'declarative grammar alone does not make a claim factual' present",
      "Declarative grammar alone" in SYS and "does not by itself make a claim factual" in SYS)
check("[v1.3] anti-overcorrection does-not-expand-definition disclaimer present",
      "does not expand the definition of factual_dependency beyond what the THREE ROLES section above already says" in SYS)

# no enum/schema change: verify the OUTPUT JSON shape block is byte-identical in key structure to v1.2
v12 = open("/Users/stargatesgx/code/disability-collective-ai/automation/.probe_fixtures/cj2-reference-probe-1/frozen_prompts/cj2-stage-b2-v1.2.txt").read()
# crude structural check: same set of top-level section headers from v1.2 all still present in v1.3
for header in ["WHAT COUNTS AS AN AUDITABLE PROPOSITION", "THE THREE ROLES", "ATOMIC CLAIM DECOMPOSITION",
               "HEDGES DO NOT IMMUNIZE A CLAIM", "DO NOT CLASSIFY BY TRIGGER WORDS",
               "TWO SEPARATE QUESTIONS FOR EVERY FACTUAL_DEPENDENCY",
               "SUPPORT MEANS EQUAL-OR-GREATER FACTUAL STRENGTH", "DECLARATION LINEAGE",
               "FACTUAL AUTHORITY", "AUDITOR EVIDENCE", "COPY DISCIPLINE",
               "IMPORTANCE", "PROBLEMS -- ALLOWED VALUES", "FIELD INVARIANTS", "FIELD COVERAGE", "OUTPUT"]:
    check(f"[carry] v1.2 section preserved: {header!r}", header in v12 and header in SYS)

# JSON examples still parse, same 4 examples as v1.2 (no new/removed examples -- prompt-only means
# no schema-example changes either)
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
parsed_ok = 0
for idx, block in enumerate(json_blocks):
    try:
        obj = json.loads(block)
        parsed_ok += 1
        block_str = json.dumps(obj)
        check(f"[carry] JSON example #{idx} parses", True)
        check(f"[carry] JSON example #{idx} has no verdict/effective_verdict/run_status key",
              "verdict" not in block_str and "run_status" not in block_str)
    except Exception:
        check(f"[carry] JSON example #{idx} parses", False)
check(f"[carry] found 4 JSON example blocks (unchanged from v1.2, got {len(json_blocks)})", len(json_blocks) == 4)

check("[carry] prompt itself makes no claim about the development set being held-out",
      "held-out" not in SYS.lower())

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
