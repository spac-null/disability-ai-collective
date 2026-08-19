#!/usr/bin/env python3
"""WG-5 integrated detector scoring vs GOLD V2.1. Gate: 8/8 before any repair."""
import json, collections
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v5-2026-08-19")
TAGS={"FORM-1.3":"form1-3","FORM-1.3-R2":"r2","FORM-1.3-R3":"r3"}
ART={"form1-3":"form1-3-article.md","r2":"form-1.3-r2-article.md","r3":"form-1.3-r3-article.md"}
def norm(s): return ' '.join((s or '').lower().replace('’',"'").replace('—','-').replace('–','-').split())

gold=json.loads((W/"inputs/gold-ledger-V2.1-FROZEN.json").read_text())
findings={f["id"]:(art,f) for art,a in gold["articles"].items() for f in a["unsupported_findings"]}
V={}; 
for t in TAGS.values():
    d=json.loads((W/"stage2-verdict"/f"{t}-raw.json").read_text())
    V[t]=d["propositions"] if isinstance(d,dict) else d

allc=[(t,p,c) for t in V for p in V[t] for c in p.get("COMMITMENTS",[])]
dist=collections.Counter(c.get("VERDICT") for _,_,c in allc)
unsup=[(t,p,c) for t,p,c in allc if c.get("VERDICT")=="UNSUPPORTED"]
uncert=[(t,p,c) for t,p,c in allc if c.get("VERDICT")=="UNCERTAIN"]

print("="*72); print("WG-5 INTEGRATED DETECTOR vs GOLD V2.1")
print(f"  parents {sum(len(V[t]) for t in V)}  commitments {len(allc)}")
print(f"  verdicts {dict(dist)}")

tp=[];fn=[]
matched=set()
for gid,(art,f) in findings.items():
    tag=TAGS[art]; gs=norm(f["span"]); gw=set(gs.split()); hit=[]
    for t,p,c in unsup:
        if t!=tag: continue
        for cand in (c.get("OFFENDING_SPAN",""), p.get("EXACT_SPAN","")):
            cs=norm(cand)
            if cs and (cs in gs or gs in cs or len(gw&set(cs.split()))>=max(2,int(.4*len(gw)))):
                hit.append((p["PARENT_CLAIM_ID"],c)); break
    if hit: tp.append((gid,tag,hit)); matched.update(id(c) for _,c in hit)
    else: fn.append((gid,tag,f["span"]))
fp=[(t,p,c) for t,p,c in unsup if id(c) not in matched]

print(f"\n  TP={len(tp)}  FP={len(fp)}  FN={len(fn)}")
print(f"  UNSUPPORTED RECALL    = {len(tp)}/8 = {len(tp)/8*100:.1f}%")
if len(tp)+len(fp): print(f"  UNSUPPORTED PRECISION = {len(tp)}/{len(tp)+len(fp)} = {len(tp)/(len(tp)+len(fp))*100:.1f}%")
print("\n  CAUGHT:")
for gid,tag,hit in tp:
    for pid,c in hit: print(f'    {gid} [{tag}/{pid}/{c["COMMITMENT_ID"]}] offending="{c.get("OFFENDING_SPAN","")[:70]}"')
if fn:
    print("  MISSED:")
    for gid,tag,span in fn: print(f'    {gid} [{tag}] "{span[:80]}"')
print(f"\n  FALSE POSITIVES ({len(fp)}):")
for t,p,c in fp:
    print(f'    [{t}/{p["PARENT_CLAIM_ID"]}/{c["COMMITMENT_ID"]}] type={c.get("COMMITMENT_TYPE")}/{c.get("CLAIM_OBJECT_TYPE")}')
    print(f'       offending="{c.get("OFFENDING_SPAN","")[:80]}"  parent_span="{p["EXACT_SPAN"][:70]}"')
    print(f'       reason: {c.get("REASON","")[:170]}')
print(f"\n  UNCERTAIN ({len(uncert)}) — HOLD/REPORT, never repaired:")
for t,p,c in uncert:
    print(f'    [{t}/{p["PARENT_CLAIM_ID"]}/{c["COMMITMENT_ID"]}] "{p["EXACT_SPAN"][:70]}"')
    print(f'       reason: {c.get("REASON","")[:150]}')

# interpretation-preservation: the three reclassified items must NOT be flagged
CHECK=[("G13-03","form1-3","the one that presses"),("GR2-03","r2","the harder one"),
       ("GR3-02","r3","harder to discharge"),("R3-control","r3","without commentary")]
print("\n  GOLD-V2.1 INTERPRETATION / CONTROL PRESERVATION:")
for label,t,needle in CHECK:
    got=[]
    for p in V[t]:
        for c in p.get("COMMITMENTS",[]):
            if needle.lower() in (p.get("EXACT_SPAN","")+" "+c.get("PROPOSITION","")).lower():
                got.append((p["PARENT_CLAIM_ID"],c.get("VERDICT")))
    ok=all(v!="UNSUPPORTED" for _,v in got)
    print(f'    {"OK  " if ok else "FAIL"} {label}: {got}')

gate=(len(tp)==8)
print("\n"+"="*72); print(f"  GATE 8/8: {'PASS — proceed to repair' if gate else 'FAIL — DO NOT PATCH'}")
json.dump({"parents":sum(len(V[t]) for t in V),"commitments":len(allc),"verdicts":dict(dist),
 "tp":len(tp),"fp":len(fp),"fn":len(fn),"recall":len(tp)/8,
 "precision":(len(tp)/(len(tp)+len(fp)) if len(tp)+len(fp) else None),
 "caught":[g for g,_,_ in tp],"missed":[g for g,_,_ in fn],
 "false_positives":[{"tag":t,"parent":p["PARENT_CLAIM_ID"],"commitment":c["COMMITMENT_ID"],
    "offending":c.get("OFFENDING_SPAN"),"reason":c.get("REASON")} for t,p,c in fp],
 "uncertain":[{"tag":t,"parent":p["PARENT_CLAIM_ID"],"span":p["EXACT_SPAN"],"reason":c.get("REASON")} for t,p,c in uncert],
 "gate_8_of_8":gate}, open(W/"DETECTOR-SCORING.json","w"), indent=2)
print("  Written DETECTOR-SCORING.json")
