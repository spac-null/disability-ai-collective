#!/usr/bin/env python3
"""FINAL REPLAY — render the WG-6B repair prompts. Persisted BEFORE any model call.
System prompt read VERBATIM from inputs/WG6B-REPAIR-SYSTEM-FROZEN.txt (proven
byte-identical to the prompt WG-6B actually sent). User shape carried verbatim."""
import hashlib, json
from pathlib import Path

R = Path(__file__).resolve().parent.parent
I = R / "inputs"
OUT = R / "repair"
ART = {"form1-3": "form1-3-article.md", "r2": "form-1.3-r2-article.md", "r3": "form-1.3-r3-article.md"}
SYSTEM = (I / "WG6B-REPAIR-SYSTEM-FROZEN.txt").read_text(encoding="utf-8")
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()

findings = json.loads((OUT / "REPAIR-INPUTS.json").read_text())
src = (I / "source-snapshot.txt").read_text().strip()

for tag, fs in findings.items():
    body = (I / ART[tag]).read_text()
    lines = [f"SOURCE TEXT (the only evidence):\n---\n{src}\n---\n",
             f"ARTICLE (patch against this exact text):\n---\n{body.strip()}\n---\n",
             f"{len(fs)} AUDIT FINDINGS. Produce exactly one patch per finding, in this order:\n---"]
    for f in fs:
        lines.append(json.dumps({k: f[k] for k in (
            "FINDING_ID", "EXACT_OFFENDING_SPAN", "ATOMIC_UNSUPPORTED_COMMITMENT",
            "PARENT_SENTENCE", "SOURCE_ANCHOR", "PROOF_STATE", "FAILURE_CLASS")},
            ensure_ascii=False))
    lines.append("---")
    user = "\n".join(lines)
    rendered = f"=== SYSTEM ===\n{SYSTEM}\n\n=== USER ===\n{user}"
    (OUT / f"{tag}-system.txt").write_text(SYSTEM)
    (OUT / f"{tag}-user.txt").write_text(user)
    (OUT / f"{tag}-prompt.txt").write_text(rendered)
    (OUT / f"{tag}-repair-meta.json").write_text(json.dumps({
        "stage": "FINAL SHADOW REPLAY / WG-6B SEMANTIC-CLOSURE PATCH REPAIR",
        "tag": tag, "findings": len(fs),
        "system_sha256": sha(SYSTEM), "user_sha256": sha(user), "prompt_sha256": sha(rendered),
        "article_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "source_sha256": hashlib.sha256(src.encode()).hexdigest(),
        "gold_ids_or_verdicts_in_prompt": False,
        "model_identity": "claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
        "execution_mode": "LOCAL_CLAUDE_SUBSCRIPTION", "blind_to_gold": True,
        "preserved": "PRE_EXECUTION"}, indent=2))
    print(f"{tag}: {len(fs)} findings  prompt_sha={sha(rendered)[:16]}")
