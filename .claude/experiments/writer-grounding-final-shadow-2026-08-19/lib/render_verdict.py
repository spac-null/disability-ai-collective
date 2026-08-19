#!/usr/bin/env python3
"""FINAL REPLAY stage 2 — WG-4A decomposition and WG-4B negative-source proof.

Both system prompts read VERBATIM from their frozen files. User-prompt shape
copied character-for-character from WG-6B/postaudit/render_verdict_prompts.py.
usage: render_verdict.py pre|post
"""
import hashlib, json, sys
from pathlib import Path

PHASE = sys.argv[1]
assert PHASE in ("pre", "post")
R = Path(__file__).resolve().parent.parent
I = R / "inputs"
OUT = R / PHASE
ORIG = {"form1-3": "form1-3-article.md", "r2": "form-1.3-r2-article.md", "r3": "form-1.3-r3-article.md"}
WG4A_SYSTEM = (I / "WG4A-DECOMP-SYSTEM-FROZEN.txt").read_text(encoding="utf-8")
WG4B_SYSTEM = (I / "WG4B-NEGPROOF-SYSTEM-FROZEN.txt").read_text(encoding="utf-8")
FIELDS = ("ID", "SENTENCE_ID", "EXACT_SPAN", "ATOMIC_PROPOSITION", "SUBJECT", "PREDICATE",
          "OBJECT_OR_COMPLEMENT", "CLAIM_OBJECT_TYPE", "SOURCE_ANCHOR")
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
src = (I / "source-snapshot.txt").read_text(encoding="utf-8")

for tag in ("form1-3", "r2", "r3"):
    ef = OUT / f"{tag}-extract-raw.json"
    if not ef.exists():
        print(f"{tag}: MISSING {ef.name} — skipped"); continue
    ex = json.loads(ef.read_text(encoding="utf-8"))
    P = ex["propositions"] if isinstance(ex, dict) else ex
    art = ((I / ORIG[tag]) if PHASE == "pre" else (R / "repair" / f"{tag}-patched.md")).read_text(encoding="utf-8")
    lines = "\n".join(json.dumps({k: p.get(k, "") for k in FIELDS}, ensure_ascii=False) for p in P)

    a_user = (f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
              f"{len(P)} FAITHFULLY EXTRACTED PROPOSITIONS. Decompose and verdict every one, in order.\n"
              f"EXACT_SPAN is the article's own words and is authoritative. ATOMIC_PROPOSITION is a\n"
              f"grammatical normalisation, an aid only. SOURCE_ANCHOR is what the extraction returned;\n"
              f"it may be empty, wrong, or too weak for the commitment it is attached to.\n---\n{lines}\n---\n")
    b_user = (f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
              f"{len(P)} FAITHFULLY EXTRACTED PROPOSITIONS. Decide IN_SCOPE for every one, in order, and\n"
              f"fully evaluate those in scope. CLAIM_OBJECT_TYPE is an earlier stage's hypothesis, not\n"
              f"authority — judge scope yourself from what each proposition commits to.\n"
              f"EXACT_SPAN is the article's own words and is authoritative. SOURCE_ANCHOR is what the\n"
              f"extraction returned; \"\" means it found none.\n---\n{lines}\n---\n")

    for name, system, user in (("wg4a", WG4A_SYSTEM, a_user), ("wg4b", WG4B_SYSTEM, b_user)):
        rendered = "=== SYSTEM ===\n" + system + "\n\n=== USER ===\n" + user
        (OUT / f"{tag}-{name}-system.txt").write_text(system, encoding="utf-8")
        (OUT / f"{tag}-{name}-user.txt").write_text(user, encoding="utf-8")
        (OUT / f"{tag}-{name}-prompt.txt").write_text(rendered, encoding="utf-8")
        (OUT / f"{tag}-{name}-meta.json").write_text(json.dumps({
            "stage": f"FINAL SHADOW REPLAY / {PHASE.upper()}-REPAIR / {name.upper()}",
            "component_version": f"{name.upper()} unchanged (system prompt read verbatim from frozen file)",
            "phase": PHASE, "tag": tag, "input_propositions": len(P),
            "system_sha256": sha(system), "user_sha256": sha(user), "prompt_sha256": sha(rendered),
            "article_sha256": hashlib.sha256(art.encode()).hexdigest(),
            "input_extraction_sha256": hashlib.sha256(ef.read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256(src.encode()).hexdigest(),
            "model_identity": "claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
            "execution_mode": "LOCAL_CLAUDE_SUBSCRIPTION", "blind_to_gold": True,
            "preserved": "PRE_EXECUTION"}, indent=2), encoding="utf-8")
    print(f"{PHASE}/{tag}: {len(P)} props  wg4a_sys={sha(WG4A_SYSTEM)[:16]}  wg4b_sys={sha(WG4B_SYSTEM)[:16]}")
