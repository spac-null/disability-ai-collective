#!/usr/bin/env python3
"""WG-6B post-repair re-audit, stage 2: the SAME modular instrument.
WG-4A and WG-4B system prompts are read VERBATIM from the frozen WG-4 files —
never retyped — so the post-repair audit uses a byte-identical instrument.
Consumes the post-repair extraction over the PATCHED articles. Blind to gold."""
import hashlib, json
from pathlib import Path

W = Path(__file__).resolve().parent            # postaudit/
B = W.parent                                   # WG-6B
V4 = B.parent.parent / "writer-grounding-v4-2026-08-19"
SRC = B.parent / "WG-6A" / "inputs" / "source-snapshot.txt"

WG4A_SYSTEM = (V4 / "WG-4A" / "form1-3-decomp-system.txt").read_text(encoding="utf-8")
WG4B_SYSTEM = (V4 / "WG-4B" / "form1-3-negproof-system.txt").read_text(encoding="utf-8")
FIELDS = ("ID", "SENTENCE_ID", "EXACT_SPAN", "ATOMIC_PROPOSITION", "SUBJECT", "PREDICATE",
          "OBJECT_OR_COMPLEMENT", "CLAIM_OBJECT_TYPE", "SOURCE_ANCHOR")
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
src = SRC.read_text(encoding="utf-8")

for tag in ("form1-3", "r2", "r3"):
    ef = W / f"{tag}-extract-raw.json"
    if not ef.exists():
        print(f"{tag}: MISSING {ef.name} — skipped"); continue
    ex = json.loads(ef.read_text(encoding="utf-8"))
    P = ex["propositions"] if isinstance(ex, dict) else ex
    art = (B / f"{tag}-patched.md").read_text(encoding="utf-8")
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
        (W / f"{tag}-{name}-system.txt").write_text(system, encoding="utf-8")
        (W / f"{tag}-{name}-user.txt").write_text(user, encoding="utf-8")
        (W / f"{tag}-{name}-prompt.txt").write_text("=== SYSTEM ===\n" + system + "\n\n=== USER ===\n" + user,
                                                    encoding="utf-8")
        (W / f"{tag}-{name}-meta.json").write_text(json.dumps({
            "stage": f"WG-6B POST-REPAIR RE-AUDIT / {name.upper()}",
            "component_version": f"{name.upper()} unchanged (system prompt read verbatim from frozen WG-4 file)",
            "tag": tag, "input_propositions": len(P),
            "system_sha256": sha(system), "user_sha256": sha(user),
            "prompt_sha256": sha("=== SYSTEM ===\n" + system + "\n\n=== USER ===\n" + user),
            "patched_article_sha256": hashlib.sha256(art.encode()).hexdigest(),
            "input_extraction_sha256": hashlib.sha256(ef.read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256(src.encode()).hexdigest(),
            "model_identity": "claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
            "execution_mode": "LOCAL_CLAUDE_SUBSCRIPTION", "blind_to_gold": True,
            "phase": "PRESERVED_PRE_EXECUTION"}, indent=2))
    print(f"{tag}: {len(P)} props  wg4a_sys={sha(WG4A_SYSTEM)[:16]}  wg4b_sys={sha(WG4B_SYSTEM)[:16]}")
