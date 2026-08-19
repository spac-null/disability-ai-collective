#!/usr/bin/env python3
"""FINAL REPLAY stage 1 — WG-3A faithful extraction.

System prompt read VERBATIM from the frozen file. Sentence splitter copied
character-for-character from WG-6B/postaudit/render_extract_prompt.py, itself
identical to WG-1B/WG-3A/WG-5. usage: render_extract.py pre|post
"""
import hashlib, json, re, sys
from pathlib import Path

PHASE = sys.argv[1]
assert PHASE in ("pre", "post")
R = Path(__file__).resolve().parent.parent
I = R / "inputs"
OUT = R / PHASE
SYSTEM = (I / "WG3A-EXTRACTION-SYSTEM-FROZEN.txt").read_text(encoding="utf-8")
ORIG = {"form1-3": "form1-3-article.md", "r2": "form-1.3-r2-article.md", "r3": "form-1.3-r3-article.md"}


def article_path(tag):
    return (I / ORIG[tag]) if PHASE == "pre" else (R / "repair" / f"{tag}-patched.md")


def split_sentences(article):
    out = []
    for para in [p for p in article.strip().split("\n\n") if p.strip()]:
        if len(out) == 0:
            out.append(para.strip()); continue
        for s in re.split(r'(?<=[.!?])\s+', para.strip()):
            if s.strip(): out.append(s.strip())
    return out


sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
src = (I / "source-snapshot.txt").read_text(encoding="utf-8")

for tag in ("form1-3", "r2", "r3"):
    art = article_path(tag).read_text(encoding="utf-8")
    sents = split_sentences(art)
    numbered = "\n".join(f"[{i}] {s}" for i, s in enumerate(sents, 1))
    user = (f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
            f"ARTICLE, SPLIT INTO {len(sents)} NUMBERED SENTENCES. Enumerate every assertion in every "
            f"one of them, in order, sentence ids 1 to {len(sents)}:\n---\n{numbered}\n---\n")
    rendered = "=== SYSTEM ===\n" + SYSTEM + "\n\n=== USER ===\n" + user
    (OUT / f"{tag}-extract-system.txt").write_text(SYSTEM, encoding="utf-8")
    (OUT / f"{tag}-extract-user.txt").write_text(user, encoding="utf-8")
    (OUT / f"{tag}-extract-prompt.txt").write_text(rendered, encoding="utf-8")
    (OUT / f"{tag}-extract-meta.json").write_text(json.dumps({
        "stage": f"FINAL SHADOW REPLAY / {PHASE.upper()}-REPAIR / WG-3A FAITHFUL EXTRACTION",
        "component_version": "WG-3A, unchanged (system prompt read verbatim from frozen file)",
        "phase": PHASE, "tag": tag, "sentences": len(sents),
        "system_sha256": sha(SYSTEM), "user_sha256": sha(user), "prompt_sha256": sha(rendered),
        "article_sha256": hashlib.sha256(art.encode()).hexdigest(),
        "source_sha256": hashlib.sha256(src.encode()).hexdigest(),
        "model_identity": "claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
        "execution_mode": "LOCAL_CLAUDE_SUBSCRIPTION", "blind_to_gold": True,
        "preserved": "PRE_EXECUTION"}, indent=2), encoding="utf-8")
    print(f"{PHASE}/{tag}: {len(sents)} sentences  prompt_sha={sha(rendered)[:16]}  art_sha={hashlib.sha256(art.encode()).hexdigest()[:16]}")
