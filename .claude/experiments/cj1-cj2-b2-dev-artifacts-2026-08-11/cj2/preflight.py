#!/usr/bin/env python3
"""Static preflight for CJ-2 Stage A / Stage C v1 prompts.
No API calls. Pure text/JSON checks only."""
import json
import re

STAGE_A = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/stage_a_system.txt").read()
STAGE_C = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/stage_c_system.txt").read()

# Also the user-input templates (composed inline here, matching what was shown to the user)
STAGE_A_USER_TEMPLATE = """ENGINE CAPSULE

Instrument: {instrument}
Move: {move}
Strong contribution: {strong_contribution}
Failure mode to avoid: {failure_mode}

SEED FRICTION

Resisting detail: {resisting_detail}

Canonical evidence:
cj1:a1: "{excerpt_a1}"
cj1:a2: "{excerpt_a2}"

SOURCE SNAPSHOT

{source_snapshot}
"""

STAGE_C_USER_TEMPLATE = """SEED FRICTION

Resisting detail: {resisting_detail}

Canonical evidence:
cj1:a1: "{excerpt_a1}"
cj1:a2: "{excerpt_a2}"

SOURCE SNAPSHOT

{source_snapshot}

CANDIDATE A

Engine A capsule:
  Instrument: {instrument_A}
  Move: {move_A}
  Strong contribution: {strong_contribution_A}
  Failure mode to avoid: {failure_mode_A}

Candidate A reading:
  seed_evidence_refs: {refs_A}
  additional_source_observations: {observations_A}
  engine_move: "{engine_move_A}"
  seed_engagement: "{seed_engagement_A}"
  interpretive_inference: "{interpretive_inference_A}"
  conceptual_shift: "{conceptual_shift_A}"
  claimed_contribution: "{claimed_contribution_A}"
"""

ok = True

def check(label, condition):
    global ok
    status = "PASS" if condition else "FAIL"
    if not condition:
        ok = False
    print(f"[{status}] {label}")

# 1. Banned terms absent from BOTH model-facing prompts + templates
BANNED = [
    "Pixel", "Siri", "Zen", "Maya", "persona", "disability", "Deafness",
    "blindness", "autism", "accessibility", "disability_angle",
    "topic affinity", "hard rout", "publication balance", "balance_agent",
    "current_agent",
]
def word_present(term, text):
    # word-boundary match so "persona" doesn't false-positive on "personally"
    return re.search(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE) is not None

for surface_name, text in [
    ("Stage A system prompt", STAGE_A),
    ("Stage A user template", STAGE_A_USER_TEMPLATE),
    ("Stage C system prompt", STAGE_C),
    ("Stage C user template", STAGE_C_USER_TEMPLATE),
]:
    found = [b for b in BANNED if word_present(b, text)]
    check(f"banned terms absent -- {surface_name}", not found)
    if found:
        print(f"    found: {found}")

# 2. Excluded CJ-1 fields absent from model-facing inputs
EXCLUDED_FIELDS = ["friction_type", "open_question", "ostensible_category"]
for surface_name, text in [
    ("Stage A system prompt", STAGE_A),
    ("Stage A user template", STAGE_A_USER_TEMPLATE),
    ("Stage C system prompt", STAGE_C),
    ("Stage C user template", STAGE_C_USER_TEMPLATE),
]:
    found = [f for f in EXCLUDED_FIELDS if f in text]
    check(f"CJ-1 excluded fields absent -- {surface_name}", not found)
    if found:
        print(f"    found: {found}")

# 2b. TITLE excluded entirely (as a literal field/label, not just the
# word "title" which could appear harmlessly in prose elsewhere).
# CORRECTED: previous version of this check had an unconditional
# "or True", making it always pass regardless of content -- a harness
# bug, not a prompt defect (the templates themselves never contained a
# TITLE field). Fixed to a real literal check, and added the equivalent
# check for Stage C which was missing entirely.
check("literal TITLE field absent from Stage A user template", "TITLE" not in STAGE_A_USER_TEMPLATE.upper())
check("literal TITLE field absent from Stage C user template", "TITLE" not in STAGE_C_USER_TEMPLATE.upper())
check("no {title}-style placeholder in Stage A template", "{title}" not in STAGE_A_USER_TEMPLATE)
check("no {title}-style placeholder in Stage C template", "{title}" not in STAGE_C_USER_TEMPLATE)

# 3. removed_engine_test absent from Stage C system prompt + Stage C user template
check("removed_engine_test absent from Stage C system prompt", "removed_engine_test" not in STAGE_C)
check("removed_engine_test absent from Stage C user template", "removed_engine_test" not in STAGE_C_USER_TEMPLATE)

# 4. abstain_reason present in Stage A abstain invariant + example
check("abstain_reason present in Stage A prompt", "abstain_reason" in STAGE_A)

# 5. runner_up invariants present in Stage C prompt (text-level check)
check("Stage C states runner_up must be qualifying-only", "runner_up must be the" in STAGE_C and "next-strongest QUALIFYING candidate" in STAGE_C)
check("Stage C states 0-qualify case", "no_distinctive_contribution" in STAGE_C and "NO candidate qualifies" in STAGE_C)
check("Stage C states 1-qualify case sets runner_up null", '"clear"' in STAGE_C and "exactly ONE candidate qualifies" in STAGE_C)

# 6. No literal "true | false" / "[] or [...]" / "pass|fail" style invalid-JSON constructs remain
INVALID_JSON_MARKERS = ["true | false", "] or [", "pass|fail", "pass | fail"]
for surface_name, text in [("Stage A", STAGE_A), ("Stage C", STAGE_C)]:
    found = [m for m in INVALID_JSON_MARKERS if m in text]
    check(f"no invalid-JSON-in-example markers -- {surface_name}", not found)
    if found:
        print(f"    found: {found}")

# 6b. No reversed "Do inflate" typo -- normalize whitespace/newlines first,
# since a soft line-wrap inside the prose is not a real defect.
_stage_c_flat = re.sub(r'\s+', ' ', STAGE_C)
check('no "Do inflate" typo in Stage C (must be "Do NOT inflate")', "Do inflate this" not in _stage_c_flat)
check('"Do NOT inflate" present in Stage C', "Do NOT inflate this" in _stage_c_flat)

# 7. Extract and validate every fenced/braced JSON example actually parses.
# We manually pull the known example blocks (there are 2 in Stage A, 1 in Stage C)
# by finding balanced-brace spans starting at each "{\n  \"status\"" / "{\n  \"candidate_assessments\"".

def extract_balanced(text, start_idx):
    depth = 0
    for i in range(start_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start_idx:i+1]
    return None

stage_a_examples = []
for marker in ['{\n  "status": "candidate"', '{\n  "status": "abstain"']:
    idx = STAGE_A.find(marker)
    check(f"Stage A example found for marker starting {marker[:20]!r}", idx != -1)
    if idx != -1:
        block = extract_balanced(STAGE_A, idx)
        stage_a_examples.append((marker, block))

stage_c_examples = []
idx = STAGE_C.find('{\n  "candidate_assessments"')
check("Stage C example found", idx != -1)
if idx != -1:
    block = extract_balanced(STAGE_C, idx)
    stage_c_examples.append(("candidate_assessments example", block))

for name, block in stage_a_examples + stage_c_examples:
    try:
        json.loads(block)
        check(f"JSON parses -- {name}", True)
    except Exception as e:
        check(f"JSON parses -- {name}", False)
        print(f"    error: {e}")
        print(f"    block: {block[:300]}")

# 8. Stage A byte-identical across P/S/Z/M calls: by construction, this script uses
# ONE STAGE_A string for all four capsules (only the user-message ENGINE CAPSULE
# block differs) -- verify no engine-specific token (P/S/Z/M as engine labels, or
# capsule content) is baked into the system prompt itself.
ENGINE_LEAK_MARKERS = ["Engine P", "Engine S", "Engine Z", "Engine M",
                       "mediation, timing, translation",  # Engine P instrument text
                       "actor and an environment",         # Engine S instrument text
                       "classification, measurement",       # Engine Z instrument text
                       "system promises in principle"]     # Engine M instrument text
found = [m for m in ENGINE_LEAK_MARKERS if m in STAGE_A]
check("no engine-specific capsule content baked into Stage A system prompt", not found)
if found:
    print(f"    found: {found}")

print()
print("OVERALL:", "PASS" if ok else "FAIL")
