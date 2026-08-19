#!/usr/bin/env python3
"""Renders the UNCHANGED grounding-audit prompt for a replicate article.
Same build_shadow_grounding_audit_prompt used by FORM-1/1.1/1.2/1.3."""
import hashlib, json, sys
from pathlib import Path
REPO = Path("/Users/stargatesgx/code/disability-collective-ai")
sys.path.insert(0, str(REPO / "automation"))
ITER = REPO / ".claude/experiments/sofa-real-ab-1-2026-08-18/iterations"
CASE = REPO / ".claude/experiments/sofa-real-ab-1-2026-08-18/case"
from orchestrator.sofa_discovery_shadow import (
    build_shadow_grounding_audit_prompt, run_deterministic_prescan)

rep = sys.argv[1]; out = ITER / rep; low = rep.lower()
source_text = (CASE / "source-snapshot.txt").read_text(encoding="utf-8")
article_text = (out / f"{low}-article.md").read_text(encoding="utf-8")
flags = run_deterministic_prescan(article_text, source_text)
system, user = build_shadow_grounding_audit_prompt(
    source_text, {"hidden_mechanism": {"value": ""}, "known_gaps": []}, article_text, flags)
(out / f"{low}-audit-system.txt").write_text(system, encoding="utf-8")
(out / f"{low}-audit-user.txt").write_text(user, encoding="utf-8")
(out / f"{low}-audit-prompt.txt").write_text("=== SYSTEM ===\n"+system+"\n\n=== USER ===\n"+user, encoding="utf-8")
(out / f"{low}-audit-prescan.json").write_text(json.dumps(flags, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"ok": True, "replicate": rep, "deterministic_flags": flags}, indent=2))
