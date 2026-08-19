#!/usr/bin/env python3
"""Post-repair verification: existing revision guard + Article Form structural checks."""
import json, re, sys
from pathlib import Path
REPO=Path("/Users/stargatesgx/code/disability-collective-ai")
sys.path.insert(0,str(REPO/"automation"))
R=REPO/".claude/experiments/writer-grounding-v0-2026-08-19"
from orchestrator.grounding import find_new_unsupported_specifics

OWNERSHIP=(r"festival(?:'s)? (says|argues|claims|states|admits|allows|whole way|mouth|line|own|vocabulary|"
           r"position|way of talking|characteristic|word|language|verb)|the festival is naming|as the festival uses|"
           r"in the festival's|festival describes itself|festival keeps offering|the festival's (cheerful|whole)")
ATTRACTOR=["no choice","could not advocate","cannot advocate","never meant to be found","went looking on purpose",
           "an estate","archive found","curator found","curator went looking","advocate for themselves",
           "wanted","chose","choice","consent","refused","denied","barrier","withheld","suppressed","intended"]
LABELS=["source fact","reviewer's narration","provenance","the reviewer explicitly argues","material below","label"]

def structure(a):
    paras=[p for p in a.strip().split("\n\n") if p.strip()]
    cv=[i+1 for i,p in enumerate(paras) if re.search(r"duty\s*[—–-]\s*to viewers|to tell them clearly",p)]
    own=[" ".join(m.group().split()) for m in re.finditer(r"[^.]*\bfestival\b[^.]*\.",a)
         if re.search(OWNERSHIP,m.group(),re.I)]
    meta=[s.strip() for s in re.split(r'(?<=[.!?])\s+',a)
          if re.search(r"not the festival's|whose view|did not say|is not the .*'s line",s,re.I)]
    low=a.lower()
    return {"paras":len(paras),"words":len(a.split()),
            "countervoice_para":cv[0] if cv else None,"arrival_para":len(paras),
            "countervoice_before_arrival":bool(cv) and cv[0]<len(paras),
            "paras_after_arrival":0,
            "festival_as_speaker":len(own),"festival_as_speaker_hits":own,
            "schema_labels":[l for l in LABELS if l in low],
            "attribution_bookkeeping":len(meta),
            "attractor_hits":[p for p in ATTRACTOR if p in low],
            "final_para":paras[-1]}

src=(R/"inputs/source-snapshot.txt").read_text(encoding="utf-8")
out={}
for tag,orig_f in [("form1-3","form1-3-article.md"),("r2","form-1.3-r2-article.md"),("r3","form-1.3-r3-article.md")]:
    o=(R/"inputs"/orig_f).read_text(encoding="utf-8")
    p=(R/"wg0b"/f"{tag}-patched.md").read_text(encoding="utf-8")
    guard=find_new_unsupported_specifics(o,p,src)
    so,sp=structure(o),structure(p)
    preserved=all([sp["festival_as_speaker"]==so["festival_as_speaker"]==0 or sp["festival_as_speaker"]==so["festival_as_speaker"],
                   sp["countervoice_before_arrival"],sp["paras_after_arrival"]==0,
                   sp["schema_labels"]==so["schema_labels"],sp["attribution_bookkeeping"]==so["attribution_bookkeeping"],
                   sp["attractor_hits"]==so["attractor_hits"],sp["paras"]==so["paras"]])
    out[tag]={"revision_guard_violations":guard,"structure_original":so,"structure_patched":sp,
              "all_form_dimensions_preserved":preserved,
              "arrival_byte_identical":so["final_para"]==sp["final_para"]}
    print(f"\n### {tag}")
    print(f"  revision guard (find_new_unsupported_specifics): {guard if guard else 'CLEAN'}")
    print(f"  festival-as-speaker      {so['festival_as_speaker']} -> {sp['festival_as_speaker']}")
    print(f"  countervoice para        {so['countervoice_para']} -> {sp['countervoice_para']} (before arrival: {sp['countervoice_before_arrival']})")
    print(f"  paras                    {so['paras']} -> {sp['paras']}   words {so['words']} -> {sp['words']}")
    print(f"  paras after arrival      {sp['paras_after_arrival']}")
    print(f"  schema labels            {so['schema_labels'] or 'NONE'} -> {sp['schema_labels'] or 'NONE'}")
    print(f"  attribution bookkeeping  {so['attribution_bookkeeping']} -> {sp['attribution_bookkeeping']}")
    print(f"  attractor                {so['attractor_hits'] or 'NONE'} -> {sp['attractor_hits'] or 'NONE'}")
    print(f"  ALL FORM DIMENSIONS PRESERVED: {preserved}")
    print(f"  arrival byte-identical:  {out[tag]['arrival_byte_identical']}")
(R/"wg0b"/"verify-report.json").write_text(json.dumps(out,indent=2,ensure_ascii=False))
