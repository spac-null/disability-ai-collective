#!/usr/bin/env python3
"""Static preflight for CJ-2 Stage B2 v1 prompt. No API calls. Pure text/JSON checks."""
import json
import re

STAGE_B2 = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/stage_b2_system.txt").read()
STAGE_B2_TEMPLATE = open("/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/stage_b2_user_template.txt").read()

ok = True
def check(label, condition):
    global ok
    status = "PASS" if condition else "FAIL"
    if not condition:
        ok = False
    print(f"[{status}] {label}")

def word_present(term, text):
    return re.search(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE) is not None

BANNED = [
    "Pixel", "Siri", "Zen", "Maya", "persona", "disability", "Deafness",
    "blindness", "autism", "accessibility", "disability_angle",
    "topic affinity", "hard rout", "publication balance", "balance_agent",
    "current_agent", "removed_engine_test", "Candidate A", "Candidate B",
    "Engine P", "Engine S", "Engine Z", "Engine M", "Stage C",
]
for surface_name, text in [("Stage B2 system prompt", STAGE_B2), ("Stage B2 user template", STAGE_B2_TEMPLATE)]:
    found = [b for b in BANNED if word_present(b, text)]
    check(f"banned terms absent -- {surface_name}", not found)
    if found:
        print(f"    found: {found}")

# verdict/effective_verdict/run_status may appear ONLY inside the explicit
# "do NOT include" instruction, never as something the model is asked to
# produce. Check context, not bare absence (a bare-absence check would be
# a false positive here -- the terms legitimately appear once, telling the
# model not to output them).
for surface_name, text in [("Stage B2 system prompt", STAGE_B2), ("Stage B2 user template", STAGE_B2_TEMPLATE)]:
    for term in ["effective_verdict", "run_status"]:
        idx = text.find(term)
        if idx == -1:
            check(f"'{term}' absent (fine) -- {surface_name}", True)
            continue
        window = text[max(0, idx-80):idx]
        check(f"'{term}' only appears inside a do-NOT-include instruction -- {surface_name}",
              "not include" in window.lower() or "do not" in window.lower() or "Do NOT" in window)

check('explicit instruction NOT to output verdict/effective_verdict/run_status present', "Do NOT include a verdict" in STAGE_B2 or "do NOT include" in STAGE_B2.lower())

# Development-fixture content absent (cave/DNA, De Hooch/soldier/painting, AI exam/cheating specifics)
DEV_FIXTURE_TERMS = ["cave", "carbonate", "uranium", "hominin", "Sulawesi", "Homo sapiens",
                     "de Hooch", "Mauritshuis", "courtyard", "pass-glass", "soldier",
                     "take-home", "campus shooting", "midterm", "48.6", "96%"]
found = [t for t in DEV_FIXTURE_TERMS if t.lower() in STAGE_B2.lower()]
check("no development-fixture content in Stage B2 system prompt (bridge/algorithm examples used instead)", not found)
if found:
    print(f"    found: {found}")

# resisting_detail labeled context-only
check('resisting_detail explicitly labeled context-only in system prompt', "CONTEXT ONLY" in STAGE_B2 or "context to help you identify" in STAGE_B2)
check('resisting_detail explicitly labeled context-only in user template', "CONTEXT ONLY" in STAGE_B2_TEMPLATE)

# auditable proposition definition present, explicitly distinguished from "factual"
check('"auditable proposition" != "factual" distinction stated', "does NOT mean" in STAGE_B2 and "auditable" in STAGE_B2.lower())

# trigger-word guidance present
check('trigger-word non-determinism guidance present', "TRIGGER WORDS" in STAGE_B2.upper())

# evidence requirements for both directions present
check('supported requires >=1 supports_claim citation', "supports_claim" in STAGE_B2)
check('unsupported requires >=1 does_not_establish_claim citation', "does_not_establish_claim" in STAGE_B2)

# field coverage instruction present
check('field coverage (one entry per field instance) instruction present', "field_audits" in STAGE_B2 and "exactly one field_audits entry" in STAGE_B2)

# Extract and validate JSON examples parse
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

examples = []
for marker in ['{\n"field_audits"', '{\n"claim_id": "c2"']:
    idx = STAGE_B2.find(marker)
    check(f"example found for marker {marker[:20]!r}", idx != -1)
    if idx != -1:
        block = extract_balanced(STAGE_B2, idx)
        examples.append((marker, block))

for name, block in examples:
    try:
        json.loads(block)
        check(f"JSON parses -- {name}", True)
    except Exception as e:
        check(f"JSON parses -- {name}", False)
        print(f"    error: {e}")

# Confirm no verdict key inside the actual JSON example objects
for name, block in examples:
    try:
        parsed = json.loads(block)
        keys_str = json.dumps(parsed)
        check(f"no verdict/run_status key inside JSON example -- {name}", "verdict" not in keys_str and "run_status" not in keys_str)
    except Exception:
        pass

print()
print("OVERALL:", "PASS" if ok else "FAIL")
