#!/usr/bin/env python3
"""WG-4 scorer. Scores WG-4A (commitment decomposition) and WG-4B (negative
meta-source proof) SEPARATELY against GOLD V2.1. Gold->parent mapping reuses the
WG-3 rule verbatim so it cannot be retuned after seeing output."""
import json, collections, sys
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v4-2026-08-19")
TAGS={"FORM-1.3":"form1-3","FORM-1.3-R2":"r2","FORM-1.3-R3":"r3"}
FACTUAL={"BASE_STATE","TEMPORAL_MODIFIER","QUANTIFIER","PROPER_NOUN","HUMAN_STATE","CAUSAL_RELATION","SOURCE_META"}

def norm(s): return ' '.join((s or '').lower().replace('’',"'").replace('—','-').replace('–','-').split())

gold=json.loads((W/"inputs/gold-ledger-V2.1-FROZEN.json").read_text())
findings={f["id"]:(art,f) for art,a in gold["articles"].items() for f in a["unsupported_findings"]}
ex={t:{p["ID"]:p for p in (lambda d:d["propositions"] if isinstance(d,dict) else d)(
      json.loads((W/"inputs"/f"{t}-extract-raw.json").read_text()))} for t in TAGS.values()}

gmap={}
for gid,(art,f) in findings.items():
    tag=TAGS[art]; gs=norm(f["span"]); gw=set(gs.split()); c=[]
    for pid,p in ex[tag].items():
        ps=norm(p.get("EXACT_SPAN",""))
        if ps and (ps in gs or gs in ps or len(gw&set(ps.split()))>=max(3,int(.4*len(gw)))): c.append(pid)
    gmap[gid]=(tag,c)

def wg4a():
    D={}
    for t in TAGS.values():
        d=json.loads((W/"WG-4A"/f"{t}-decomp-raw.json").read_text())
        D[t]={x["PARENT_CLAIM_ID"]:x for x in (d["propositions"] if isinstance(d,dict) else d)}
    ncom=sum(len(x.get("COMMITMENTS",[])) for t in D for x in D[t].values())
    npar=sum(len(D[t]) for t in D)
    cst=collections.Counter(c.get("SUPPORT_STATUS") for t in D for x in D[t].values() for c in x.get("COMMITMENTS",[]))
    past=collections.Counter(x.get("PARENT_AGGREGATE") for t in D for x in D[t].values())
    print("="*70); print("WG-4A COMMITMENT DECOMPOSITION")
    print(f"  parents {npar}  commitments {ncom}  (avg {ncom/npar:.2f}/parent)")
    print(f"  commitment status {dict(cst)}")
    print(f"  parent aggregate  {dict(past)}")
    isolated=[];notiso=[]
    print("\n  --- per gold finding: was the unsupported commitment ISOLATED and flagged? ---")
    for gid,(tag,cands) in gmap.items():
        hits=[]
        for pid in cands:
            for c in D[tag].get(pid,{}).get("COMMITMENTS",[]):
                if c.get("SUPPORT_STATUS")=="UNSUPPORTED": hits.append((pid,c))
        ok=bool(hits); (isolated if ok else notiso).append(gid)
        print(f'  {"ISOLATED" if ok else "ABSORBED "} {gid} [{tag}] parents={cands}')
        for pid,c in hits:
            print(f'       {c["COMMITMENT_ID"]} [{c["COMMITMENT_TYPE"]}] {c["PROPOSITION"][:95]}')
        if not ok:
            for pid in cands:
                for c in D[tag].get(pid,{}).get("COMMITMENTS",[]):
                    print(f'       (miss) {c.get("COMMITMENT_ID")} [{c.get("COMMITMENT_TYPE")}] {c.get("SUPPORT_STATUS")}: {c.get("PROPOSITION","")[:80]}')
    claimed={p for _,(t,c) in gmap.items() for p in c}
    fps=[]
    for t in D:
        for pid,x in D[t].items():
            if x.get("PARENT_AGGREGATE")=="UNSUPPORTED" and pid not in claimed:
                fps.append((t,pid,ex[t][pid].get("CLAIM_OBJECT_TYPE"),x))
    print(f'\n  ISOLATION SCORE: {len(isolated)}/8   absorbed: {notiso}')
    print(f'  PARENT-LEVEL FALSE POSITIVES: {len(fps)}')
    frag=[f for f in fps if f[2] in ("SUBJECT_MATTER","OTHER")]
    print(f'  of which on SUBJECT_MATTER/OTHER (false fragmentation of analysis): {len(frag)}')
    for t,pid,ty,x in fps:
        bad=[c for c in x["COMMITMENTS"] if c.get("SUPPORT_STATUS")=="UNSUPPORTED"]
        print(f'    [{t}/{pid}] wg3a_type={ty} span="{x["EXACT_SPAN"][:80]}"')
        for c in bad: print(f'        {c["COMMITMENT_ID"]} [{c["COMMITMENT_TYPE"]}] {c["PROPOSITION"][:90]}')
        for c in bad: print(f'        reason: {c.get("REASON","")[:150]}')
    print("\n  --- required interval tests ---")
    for gid in ("G13-02","GR3-01"):
        tag,cands=gmap[gid]
        for pid in cands:
            for c in D[tag].get(pid,{}).get("COMMITMENTS",[]):
                print(f'  {gid} {tag}/{pid} {c["COMMITMENT_ID"]} [{c["COMMITMENT_TYPE"]}] -> {c["SUPPORT_STATUS"]}')
                print(f'        {c["PROPOSITION"][:110]}')
    return {"parents":npar,"commitments":ncom,"isolated":len(isolated),"absorbed":notiso,
            "parent_false_positives":len(fps),"false_fragmentation":len(frag),
            "commitment_status":dict(cst),"parent_aggregate":dict(past)}

def wg4b():
    R={}
    for t in TAGS.values():
        d=json.loads((W/"WG-4B"/f"{t}-negproof-raw.json").read_text())
        R[t]={x["ID"]:x for x in (d["results"] if isinstance(d,dict) else d)}
    ins=[(t,i,x) for t in R for i,x in R[t].items() if x.get("IN_SCOPE")=="YES"]
    neg=[(t,i,x) for t,i,x in ins if x.get("NEGATIVE")=="YES"]
    vd=collections.Counter(x.get("VERDICT") for _,_,x in ins)
    pt=collections.Counter(x.get("PROOF_TYPE") for _,_,x in neg)
    print("="*70); print("WG-4B NEGATIVE META-SOURCE PROOF")
    print(f"  in scope {len(ins)} / 236   negative {len(neg)}")
    print(f"  verdicts (in scope) {dict(vd)}")
    print(f"  proof types (negative) {dict(pt)}")
    META_GOLD={"G13-04":("form1-3","P22"),"GR2-02":("r2","P21")}
    print("\n  --- critical cases ---")
    for gid,(t,pid) in META_GOLD.items():
        x=R[t].get(pid,{})
        print(f'  {gid} [{t}/{pid}] VERDICT={x.get("VERDICT")} (must be UNSUPPORTED)')
        print(f'      in_scope={x.get("IN_SCOPE")} negative={x.get("NEGATIVE")} proof={x.get("PROOF_TYPE")} anchor_empty={x.get("EXTRACTION_ANCHOR_WAS_EMPTY")}')
        print(f'      scope: {str(x.get("SCOPE"))[:150]}')
        print(f'      reason: {str(x.get("REASON"))[:230]}')
    x=R["r3"].get("P29",{})
    print(f'  R3 CONTROL [r3/P29] VERDICT={x.get("VERDICT")} (must NOT be UNSUPPORTED)')
    print(f'      negative={x.get("NEGATIVE")} proof={x.get("PROOF_TYPE")}')
    print(f'      scope: {str(x.get("SCOPE"))[:200]}')
    print(f'      why_complete: {str(x.get("WHY_SCOPE_IS_COMPLETE"))[:220]}')
    goldmeta={p for gid in ("G13-04","GR2-02") for p in [META_GOLD[gid][1]]}
    claimed={(TAGS[findings[g][0]],p) for g in findings for p in gmap[g][1]}
    fps=[(t,i,x) for t,i,x in ins if x.get("VERDICT")=="UNSUPPORTED" and (t,i) not in claimed]
    print(f'\n  FALSE POSITIVES (in-scope UNSUPPORTED not a gold finding): {len(fps)}')
    for t,i,x in fps:
        p=ex[t][i]
        print(f'    [{t}/{i}] neg={x.get("NEGATIVE")} proof={x.get("PROOF_TYPE")} span="{p["EXACT_SPAN"][:80]}"')
        print(f'        reason: {str(x.get("REASON"))[:180]}')
    return {"in_scope":len(ins),"negative":len(neg),"verdicts":dict(vd),"proof_types":dict(pt),
            "false_positives":len(fps),
            "G13-04":R["form1-3"].get("P22"),"GR2-02":R["r2"].get("P21"),"R3_control":R["r3"].get("P29")}

out={}
if "--a" in sys.argv or len(sys.argv)==1: out["WG-4A"]=wg4a()
if "--b" in sys.argv or len(sys.argv)==1: out["WG-4B"]=wg4b()
(W/"WG4-SCORING.json").write_text(json.dumps(out,indent=2,default=str))
print("\nWritten WG4-SCORING.json")
