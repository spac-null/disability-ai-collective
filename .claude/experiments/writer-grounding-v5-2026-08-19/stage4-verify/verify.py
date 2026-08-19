#!/usr/bin/env python3
"""WG-5 stage 4 verification: Article Form (constants copied VERBATIM from the
frozen sofa-real-ab-1 structural_check.py), voice/person, preservation metrics."""
import json, re, difflib
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v5-2026-08-19")
ART={"form1-3":"form1-3-article.md","r2":"form-1.3-r2-article.md","r3":"form-1.3-r3-article.md"}

# ---- verbatim from frozen structural_check.py ----
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
# --------------------------------------------------

def form_check(text):
    a=text.strip(); paras=[p for p in a.split("\n\n") if p.strip()]; low=a.lower()
    norm=lambda s: re.sub(r'\W+',' ',s.lower()).strip()
    cv=[i+1 for i,p in enumerate(paras) if re.search(r"duty\s*[—-]\s*to viewers|duty . to viewers|to tell them clearly", p)]
    own=[" ".join(m.group().split()) for m in re.finditer(r"[^.]*\bfestival\b[^.]*\.", a)
         if re.search(OWNERSHIP, m.group(), re.I)]
    meta=[s.strip() for s in re.split(r'(?<=[.!?])\s+', a)
          if re.search(r"not the festival's|whose view|did not say|is not the .*'s line", s, re.I)]
    sims=[round(difflib.SequenceMatcher(None,norm(p),norm(DEST)).ratio(),2) for p in paras]
    best=max(range(len(paras)),key=lambda i:sims[i])
    return {"paragraphs":len(paras),"words":len(a.split()),
      "countervoice_paras":cv,"arrival_para":best+1,"paras_after_arrival":len(paras)-(best+1),
      "arrival_final":len(paras)-(best+1)==0,
      "countervoice_before_arrival":bool(cv) and cv[0]<best+1,
      "festival_as_speaker_failures":len(own),"festival_phrases":own,
      "schema_label_tokens":[l for l in LABELS if l in low],
      "attribution_bookkeeping_leakage":len(meta),"bookkeeping_sentences":meta,
      "agency_consent_attractor_hits":[p for p in ATTRACTOR if p in low],
      "destination_similarity":sims,"final_para":paras[-1][:300]}

VOICE=[r"\bI\b",r"\bwe\b",r"\bour\b",r"\bus\b",r"on this reading",r"on the reading offered",
       r"\bhere\b",r"it seems to me",r"arguably",r"perhaps",r"in my view"]
def voice_counts(text):
    return {p:len(re.findall(p,text,re.I if p not in (r"\bI\b",) else 0)) for p in VOICE}

out={}
for tag,af in ART.items():
    orig=(W/"inputs"/af).read_text(encoding="utf-8")
    pf=W/"stage3-repair"/f"{tag}-patched.md"
    if not pf.exists(): out[tag]={"status":"NO PATCHED FILE"}; continue
    pat=pf.read_text(encoding="utf-8")
    fo,fp=form_check(orig),form_check(pat)
    dims=["festival_as_speaker_failures","attribution_bookkeeping_leakage","arrival_final",
          "countervoice_before_arrival","paras_after_arrival","agency_consent_attractor_hits",
          "schema_label_tokens","arrival_para","paragraphs"]
    changed={d:{"before":fo[d],"after":fp[d]} for d in dims if fo[d]!=fp[d]}
    vo,vp=voice_counts(orig),voice_counts(pat)
    vdelta={k:{"before":vo[k],"after":vp[k]} for k in vo if vo[k]!=vp[k]}
    patches=json.loads((W/"stage3-repair"/f"{tag}-patches.json").read_text())
    P=patches["patches"] if isinstance(patches,dict) else patches
    newtext=" ".join(p.get("NEW_TEXT","") for p in P)
    intro=[k for k in VOICE if re.search(k,newtext,re.I if k not in (r"\bI\b",) else 0)]
    # arrival paragraph identity
    op=[x for x in orig.split("\n\n") if x.strip()]; pp=[x for x in pat.split("\n\n") if x.strip()]
    arr_i=fo["arrival_para"]-1
    arrival_identical = arr_i < len(pp) and op[arr_i]==pp[arr_i]
    out[tag]={"form_before":fo,"form_after":fp,"form_dimensions_changed":changed,
      "form_preserved":len(changed)==0,
      "voice_token_deltas":vdelta,"voice_tokens_in_patch_text":intro,
      "voice_regression":bool(intro) or bool(vdelta),
      "arrival_paragraph_patched":not arrival_identical,
      "arrival_bytes_identical":arrival_identical}
(W/"stage4-verify"/"FORM-VOICE-VERIFICATION.json").write_text(json.dumps(out,indent=2))
for t,d in out.items():
    if d.get("status"): print(t,d["status"]); continue
    print(f'== {t}: form_preserved={d["form_preserved"]} changed={list(d["form_dimensions_changed"])}')
    print(f'   arrival_final={d["form_after"]["arrival_final"]} paras_after_arrival={d["form_after"]["paras_after_arrival"]}'
          f' countervoice_before={d["form_after"]["countervoice_before_arrival"]}')
    print(f'   festival_as_speaker={d["form_after"]["festival_as_speaker_failures"]}'
          f' bookkeeping={d["form_after"]["attribution_bookkeeping_leakage"]}'
          f' attractor={d["form_after"]["agency_consent_attractor_hits"]}')
    print(f'   arrival_bytes_identical={d["arrival_bytes_identical"]}  voice_regression={d["voice_regression"]} {d["voice_tokens_in_patch_text"]}')
    if d["voice_token_deltas"]: print(f'   voice deltas: {d["voice_token_deltas"]}')
