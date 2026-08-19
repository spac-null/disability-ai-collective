#!/usr/bin/env python3
"""WG-6B post-repair re-audit, stage 1: faithful extraction over the PATCHED
articles. WG-3A design UNCHANGED — system prompt read verbatim from the frozen
WG-3A file, not retyped. Sentence splitter identical to WG-1B/WG-3A/WG-5."""
import hashlib, json, re
from pathlib import Path

W = Path(__file__).resolve().parent           # postaudit/
B = W.parent                                  # WG-6B
FROZEN = B.parent.parent / "writer-grounding-v5-2026-08-19" / "inputs" / "WG3A-EXTRACTION-SYSTEM-FROZEN.txt"
SRC = B.parent / "WG-6A" / "inputs" / "source-snapshot.txt"
SYSTEM = FROZEN.read_text(encoding="utf-8")

def split_sentences(article):
    out = []
    for para in [p for p in article.strip().split("\n\n") if p.strip()]:
        if len(out) == 0:
            out.append(para.strip()); continue
        for s in re.split(r'(?<=[.!?])\s+', para.strip()):
            if s.strip(): out.append(s.strip())
    return out

src = SRC.read_text(encoding="utf-8")
for tag in ("form1-3", "r2", "r3"):
    art = (B / f"{tag}-patched.md").read_text(encoding="utf-8")
    sents = split_sentences(art)
    numbered = "\n".join(f"[{i}] {s}" for i, s in enumerate(sents, 1))
    user = (f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
            f"ARTICLE, SPLIT INTO {len(sents)} NUMBERED SENTENCES. Enumerate every assertion in every "
            f"one of them, in order, sentence ids 1 to {len(sents)}:\n---\n{numbered}\n---\n")
    rendered = "=== SYSTEM ===\n" + SYSTEM + "\n\n=== USER ===\n" + user
    sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
    (W / f"{tag}-extract-system.txt").write_text(SYSTEM, encoding="utf-8")
    (W / f"{tag}-extract-user.txt").write_text(user, encoding="utf-8")
    (W / f"{tag}-extract-prompt.txt").write_text(rendered, encoding="utf-8")
    (W / f"{tag}-extract-meta.json").write_text(json.dumps({
        "stage": "WG-6B POST-REPAIR RE-AUDIT / FAITHFUL EXTRACTION",
        "component_version": "WG-3A, unchanged (system prompt read verbatim from frozen file)",
        "tag": tag, "sentences": len(sents), "system_sha256": sha(SYSTEM),
        "frozen_system_source": str(FROZEN.relative_to(FROZEN.parents[3])),
        "user_sha256": sha(user), "prompt_sha256": sha(rendered),
        "patched_article_sha256": hashlib.sha256(art.encode()).hexdigest(),
        "source_sha256": hashlib.sha256(src.encode()).hexdigest(),
        "model_identity": "claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
        "execution_mode": "LOCAL_CLAUDE_SUBSCRIPTION", "blind_to_gold": True,
        "phase": "PRESERVED_PRE_EXECUTION"}, indent=2))
    print(f'{tag}: {len(sents)} sentences  system_sha={sha(SYSTEM)[:16]}  prompt_sha={sha(rendered)[:16]}')
