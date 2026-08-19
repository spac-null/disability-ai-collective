#!/usr/bin/env python3
"""
render_audit_prompt_form1_3.py — renders the UNCHANGED grounding-audit
prompt (orchestrator.sofa_discovery_shadow.build_shadow_grounding_audit_prompt,
the same function FORM-1/1.1/1.2 used) for the FORM-1.3 article, so it can
be executed through the local Claude subscription instead of OpenRouter.

The auditor PROMPT is byte-identical in construction to prior iterations.
The auditor MODEL is not: prior runs used the production review/audit model
chain via CLIProxy. That difference is recorded, and the automated verdict
is treated as evidence, not authority -- independent adjudication against
the frozen source is done on top, exactly as for FORM-1.1 and FORM-1.2.
"""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path("/Users/stargatesgx/code/disability-collective-ai")
sys.path.insert(0, str(REPO / "automation"))
OUT_DIR = REPO / ".claude/experiments/sofa-real-ab-1-2026-08-18/iterations/FORM-1.3"
CASE_DIR = REPO / ".claude/experiments/sofa-real-ab-1-2026-08-18/case"

from orchestrator.sofa_discovery_shadow import (
    build_shadow_grounding_audit_prompt, run_deterministic_prescan,
)

source_text = (CASE_DIR / "source-snapshot.txt").read_text(encoding="utf-8")
article_text = (OUT_DIR / "form1-3-article.md").read_text(encoding="utf-8")

# Same minimal stand-in packet the B.3/FORM-1.1/FORM-1.2 audit adapters used.
packet_for_audit = {"hidden_mechanism": {"value": ""}, "known_gaps": []}

flags = run_deterministic_prescan(article_text, source_text)
system, user = build_shadow_grounding_audit_prompt(
    source_text, packet_for_audit, article_text, flags)

rendered = "=== SYSTEM ===\n" + system + "\n\n=== USER ===\n" + user
(OUT_DIR / "form1-3-audit-prompt.txt").write_text(rendered, encoding="utf-8")
(OUT_DIR / "form1-3-audit-system.txt").write_text(system, encoding="utf-8")
(OUT_DIR / "form1-3-audit-user.txt").write_text(user, encoding="utf-8")
(OUT_DIR / "form1-3-audit-prescan.json").write_text(
    json.dumps(flags, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "ok": True,
    "audit_prompt_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
    "deterministic_flags": len(flags),
    "prompt_chars": len(rendered),
}, indent=2))
