#!/usr/bin/env python3
"""WG-5 deterministic fail-closed patcher. WG-0B principles:
exact OLD_TEXT match, no ambiguity, no overlap, no change outside approved spans."""
import json, hashlib, sys
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v5-2026-08-19")
ART={"form1-3":"form1-3-article.md","r2":"form-1.3-r2-article.md","r3":"form-1.3-r3-article.md"}

def apply(tag):
    art=(W/"inputs"/ART[tag]).read_text(encoding="utf-8")
    patches=json.loads((W/"stage3-repair"/f"{tag}-patches.json").read_text(encoding="utf-8"))
    P=patches["patches"] if isinstance(patches,dict) else patches
    spans=[]
    for p in P:
        old=p["OLD_TEXT"]; n=art.count(old)
        if n==0: return {"tag":tag,"status":"FAIL_CLOSED","reason":f'OLD_TEXT not found: {old[:60]!r}'}
        if n>1:  return {"tag":tag,"status":"FAIL_CLOSED","reason":f'OLD_TEXT ambiguous ({n}x): {old[:60]!r}'}
        i=art.index(old); spans.append((i,i+len(old),p))
    spans.sort()
    for a,b in zip(spans,spans[1:]):
        if a[1]>b[0]: return {"tag":tag,"status":"FAIL_CLOSED","reason":"overlapping patches"}
    out=[];prev=0;applied=[]
    for s,e,p in spans:
        new="" if p.get("OPERATION","REPLACE").upper()=="DELETE" else p["NEW_TEXT"]
        out.append(art[prev:s]); out.append(new); prev=e
        applied.append({"PATCH_ID":p.get("PATCH_ID"),"op":p.get("OPERATION","REPLACE"),
                        "removed":len(art[s:e]),"added":len(new),"old":art[s:e],"new":new})
    out.append(art[prev:]); patched="".join(out)
    # assert every changed byte belongs to an approved span
    unchanged_before=art[:spans[0][0]] if spans else art
    ok=patched.startswith(unchanged_before) and patched.endswith(art[spans[-1][1]:] if spans else art)
    (W/"stage3-repair"/f"{tag}-patched.md").write_text(patched,encoding="utf-8")
    return {"tag":tag,"status":"APPLIED","patches":len(P),"applied":applied,
      "orig_sha256":hashlib.sha256(art.encode()).hexdigest(),
      "patched_sha256":hashlib.sha256(patched.encode()).hexdigest(),
      "chars_removed":sum(a["removed"] for a in applied),"chars_added":sum(a["added"] for a in applied),
      "word_delta":len(patched.split())-len(art.split()),
      "paragraph_delta":len([p for p in patched.split("\n\n") if p.strip()])-len([p for p in art.split("\n\n") if p.strip()]),
      "boundary_assert_ok":ok}

if __name__=="__main__":
    res=[apply(t) for t in ("form1-3","r2","r3")]
    (W/"stage3-repair"/"APPLICATION-REPORT.json").write_text(json.dumps(res,indent=2))
    for r in res: print(json.dumps({k:v for k,v in r.items() if k!="applied"},indent=1))
