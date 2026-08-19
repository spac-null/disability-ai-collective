#!/usr/bin/env python3
"""WG-3B scorer. Scores the object-of-claim verdicts against GOLD V2.1 (frozen).
Gold->proposition mapping reuses the WG-3A candidate matching, so it is not
re-tuned after seeing verdicts."""
import json, collections
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v3-2026-08-19")
TAGS={"FORM-1.3":"form1-3","FORM-1.3-R2":"r2","FORM-1.3-R3":"r3"}

def norm(s): return ' '.join((s or '').lower().replace('’',"'").replace('—','-').replace('–','-').split())

gold=json.loads((W/"inputs/gold-ledger-V2.1-FROZEN.json").read_text())
findings={f["id"]:(art,f) for art,a in gold["articles"].items() for f in a["unsupported_findings"]}

ex={};vd={}
for tag in TAGS.values():
    e=json.loads((W/"wg3a"/f"{tag}-extract-raw.json").read_text())
    ex[tag]={p["ID"]:p for p in (e["propositions"] if isinstance(e,dict) else e)}
    v=json.loads((W/"wg3b"/f"{tag}-verdict-raw.json").read_text())
    vd[tag]={x["ID"]:x for x in (v["verdicts"] if isinstance(v,dict) else v)}

# gold -> candidate proposition ids (same rule as WG-3A scorer)
gmap={}
for gid,(art,f) in findings.items():
    tag=TAGS[art]; gs=norm(f["span"]); gw=set(gs.split()); cands=[]
    for pid,p in ex[tag].items():
        ps=norm(p.get("EXACT_SPAN",""))
        if not ps: continue
        if ps in gs or gs in ps or len(gw&set(ps.split()))>=max(3,int(.4*len(gw))): cands.append(pid)
    gmap[gid]=(tag,cands)

tp=[];fn=[]
for gid,(tag,cands) in gmap.items():
    hit=[c for c in cands if vd[tag].get(c,{}).get("VERDICT")=="UNSUPPORTED"]
    (tp if hit else fn).append((gid,tag,hit or cands))
claimed={c for gid,(tag,cands) in gmap.items() for c in cands}

fps=[]
for tag in TAGS.values():
    for pid,v in vd[tag].items():
        if v.get("VERDICT")=="UNSUPPORTED" and pid not in claimed:
            p=ex[tag][pid]
            fps.append({"tag":tag,"ID":pid,"TYPE":p.get("CLAIM_OBJECT_TYPE"),
              "EXACT_SPAN":p.get("EXACT_SPAN"),"ATOMIC":p.get("ATOMIC_PROPOSITION"),
              "ANCHOR":p.get("SOURCE_ANCHOR",""),"REASON":v.get("REASON","")})

TP,FN,FP=len(tp),len(fn),len(fps)
dist=collections.Counter(v["VERDICT"] for t in TAGS.values() for v in vd[t].values())
print("=== VERDICT DISTRIBUTION (236 propositions) ===")
print(" ",dict(dist),"total",sum(dist.values()))
print(f"\n=== SCORE vs GOLD V2.1 (8 UNSUPPORTED) ===")
print(f"  TP={TP}  FP={FP}  FN={FN}")
print(f"  UNSUPPORTED RECALL    = {TP}/{TP+FN} = {TP/(TP+FN)*100:.1f}%")
print(f"  UNSUPPORTED PRECISION = {TP}/{TP+FP} = {TP/(TP+FP)*100:.1f}%" if TP+FP else "  precision n/a")
print("\n  CAUGHT:", [g for g,_,_ in tp])
print("  MISSED:", [g for g,_,_ in fn])
for gid,tag,c in fn:
    for pid in c:
        v=vd[tag].get(pid,{});p=ex[tag][pid]
        print(f'    FN {gid} {tag}/{pid} verdict={v.get("VERDICT")} type={p.get("CLAIM_OBJECT_TYPE")}')
        print(f'       reason: {v.get("REASON","")[:200]}')
print(f"\n=== FALSE POSITIVES ({FP}) — adjudicate each against the frozen source ===")
for f in fps:
    print(f'  [{f["tag"]}/{f["ID"]}] {f["TYPE"]}  anchor={"EMPTY" if not f["ANCHOR"] else "present"}')
    print(f'     SPAN  : {f["EXACT_SPAN"][:120]}')
    print(f'     ATOMIC: {f["ATOMIC"][:120]}')
    print(f'     REASON: {f["REASON"][:220]}')

print("\n=== DISCRIMINATION CASES ===")
CASES=[("G13-04 must be UNSUPPORTED","form1-3","not because the review ranks them"),
       ("GR2-01 must be UNSUPPORTED","r2","brought anything to the encounter"),
       ("GR2-02 must be UNSUPPORTED","r2","not because the review places them above the rest"),
       ("R3 CONTROL must NOT be UNSUPPORTED","r3","sits there without commentary"),
       ("G13-03 must stay INTERPRETATION","form1-3","the second side is the one that presses"),
       ("GR2-03 must stay INTERPRETATION","r2","the second direction is the harder one"),
       ("GR3-02 must stay INTERPRETATION","r3","harder to discharge")]
for label,tag,needle in CASES:
    print(f'\n-- {label}')
    for pid,p in ex[tag].items():
        if needle.lower() in (p.get("EXACT_SPAN","")+" "+p.get("ATOMIC_PROPOSITION","")).lower():
            v=vd[tag].get(pid,{})
            print(f'   [{pid}] type={p.get("CLAIM_OBJECT_TYPE")} VERDICT={v.get("VERDICT")}')
            print(f'        anchor_present={v.get("ANCHOR_PRESENT")} anchor_supports={v.get("ANCHOR_SUPPORTS_PREDICATE")}')
            print(f'        extraction anchor: {(p.get("SOURCE_ANCHOR") or "(EMPTY)")[:100]}')
            print(f'        reason: {v.get("REASON","")[:260]}')

json.dump({"experiment":"WG-3B OBJECT-OF-CLAIM VERDICT","gold":"GOLD V2.1 FROZEN",
 "propositions":sum(dist.values()),"verdict_distribution":dict(dist),
 "tp":TP,"fp":FP,"fn":FN,"unsupported_recall":TP/(TP+FN),
 "unsupported_precision":(TP/(TP+FP) if TP+FP else None),
 "caught":[g for g,_,_ in tp],"missed":[g for g,_,_ in fn],
 "false_positives":fps,"gold_to_proposition_map":{k:v[1] for k,v in gmap.items()}},
 open(W/"wg3b"/"WG3B-SCORING.json","w"),indent=2)
print("\nWritten: wg3b/WG3B-SCORING.json")
