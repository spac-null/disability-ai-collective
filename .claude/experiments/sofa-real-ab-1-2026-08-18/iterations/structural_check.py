#!/usr/bin/env python3
"""Deterministic structural checks, identical across FORM-1.3 / R2 / R3."""
import json, re, sys, difflib
from pathlib import Path
ITER = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/sofa-real-ab-1-2026-08-18/iterations")

DEST = ("The review uses discovery for the visitor's present encounter with previously "
        "unknown work, while some of the work discussed in the review had remained unshown "
        "during its maker's lifetime.")

OWNERSHIP = r"festival(?:'s)? (says|argues|claims|states|admits|allows|whole way|mouth|line|own|vocabulary|position|way of talking)|the festival is naming|as the festival uses|in the festival's|festival describes itself|festival keeps offering|the festival's (cheerful|whole)"
ATTRACTOR = ["no choice","could not advocate","cannot advocate","never meant to be found",
             "went looking on purpose","an estate","archive found","curator found",
             "curator went looking","advocate for themselves","wanted","chose","choice",
             "consent","refused","denied","barrier","withheld","suppressed","intended"]
LABELS = ["source fact","reviewer's narration","provenance","the reviewer explicitly argues",
          "material below","label"]

def analyse(path, tag):
    a = Path(path).read_text(encoding="utf-8").strip()
    paras = [p for p in a.split("\n\n") if p.strip()]
    low = a.lower()
    norm = lambda s: re.sub(r'\W+',' ',s.lower()).strip()
    cv = [i+1 for i,p in enumerate(paras) if re.search(r"duty\s*[—-]\s*to viewers|duty . to viewers|to tell them clearly", p)]
    own = [" ".join(m.group().split()) for m in re.finditer(r"[^.]*\bfestival\b[^.]*\.", a)
           if re.search(OWNERSHIP, m.group(), re.I)]
    meta = [s.strip() for s in re.split(r'(?<=[.!?])\s+', a)
            if re.search(r"not the festival's|whose view|did not say|is not the .*'s line", s, re.I)]
    sims = [round(difflib.SequenceMatcher(None, norm(p), norm(DEST)).ratio(), 2) for p in paras]
    best = max(range(len(paras)), key=lambda i: sims[i])
    print(f"\n########## {tag} ##########")
    print(f"paragraphs: {len(paras)} | words: {len(a.split())}")
    print(f"title: {paras[0].splitlines()[0][:80]}")
    print(f"countervoice para(s): {cv or 'NOT FOUND'}")
    print(f"destination-similarity by para: {sims}")
    print(f"most destination-like para: {best+1} (sim {sims[best]}) of {len(paras)}")
    print(f"paras after most-destination-like: {len(paras)-(best+1)}")
    print(f"countervoice before that para: {bool(cv) and cv[0] < best+1}")
    print(f"festival-as-speaker/owner phrases: {len(own)}")
    for o in own: print(f"   * {o[:150]}")
    print(f"schema label tokens: {[l for l in LABELS if l in low] or 'NONE'}")
    print(f"attribution-bookkeeping sentences: {len(meta)}")
    for m in meta: print(f"   * {m[:150]}")
    print(f"agency/consent attractor hits: {[p for p in ATTRACTOR if p in low] or 'NONE'}")
    print(f"FINAL PARA: {paras[-1][:400]}")

for tag, p in [("FORM-1.3","FORM-1.3/form1-3-article.md"),
               ("FORM-1.3-R2","FORM-1.3-R2/form-1.3-r2-article.md"),
               ("FORM-1.3-R3","FORM-1.3-R3/form-1.3-r3-article.md")]:
    fp = ITER / p
    if fp.exists(): analyse(fp, tag)
    else: print(f"\n########## {tag} ########## (not yet generated)")
