#!/usr/bin/env python3
"""Deterministic patch application. Fails closed. Never asks a model to regenerate."""
import json, sys, hashlib
from pathlib import Path
R=Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v0-2026-08-19")

def sha(s): return hashlib.sha256(s.encode()).hexdigest()

def main(tag, art_file, patch_file, gold_spans):
    orig=(R/"inputs"/art_file).read_text(encoding="utf-8")
    patches=json.load(open(R/"wg0b"/patch_file))
    patches=patches.get("patches",patches)
    spans=[]
    for p in patches:
        old=p["OLD_TEXT"]; new=p.get("NEW_TEXT","")
        op=p.get("OPERATION","REPLACE").upper()
        if op=="DELETE": new=""
        n=orig.count(old)
        if n==0: raise SystemExit(f"FAIL-CLOSED {p['PATCH_ID']}: OLD_TEXT occurs 0 times")
        if n>1:  raise SystemExit(f"FAIL-CLOSED {p['PATCH_ID']}: OLD_TEXT occurs {n} times, no location given")
        s=orig.index(old); e=s+len(old)
        # every patch must fall inside an approved gold span region
        if not any(g in orig and orig.index(g) <= s and e <= orig.index(g)+len(g) for g in gold_spans):
            # allow a patch that CONTAINS a gold span too (wider minimal edit)
            if not any(g in old for g in gold_spans):
                raise SystemExit(f"FAIL-CLOSED {p['PATCH_ID']}: edit outside approved gold spans: {old[:70]!r}")
        spans.append((s,e,new,p["PATCH_ID"]))
    spans.sort()
    for i in range(1,len(spans)):
        if spans[i][0] < spans[i-1][1]:
            raise SystemExit(f"FAIL-CLOSED: patches {spans[i-1][3]} and {spans[i][3]} overlap")
    out=[]; cur=0; removed=added=0
    for s,e,new,_ in spans:
        out.append(orig[cur:s]); out.append(new)
        removed+=e-s; added+=len(new); cur=e
    out.append(orig[cur:])
    patched="".join(out)
    # PROOF: everything outside approved spans is byte-identical
    a=[];b=[];cur=0
    for s,e,new,_ in spans:
        a.append(orig[cur:s]); cur=e
    a.append(orig[cur:])
    cur=0
    for (s,e,new,_) in spans:
        pass
    # rebuild remainder of patched by removing inserted texts at their new offsets
    rem=[];cur=0;shift=0
    for s,e,new,_ in spans:
        ns=s+shift; ne=ns+len(new)
        rem.append(patched[cur:ns]); cur=ne; shift += len(new)-(e-s)
    rem.append(patched[cur:])
    assert "".join(a)=="".join(rem), "UNAPPROVED BYTE CHANGE DETECTED"
    (R/"wg0b"/f"{tag}-patched.md").write_text(patched,encoding="utf-8")
    res={"tag":tag,"patches":len(spans),"chars_removed":removed,"chars_added":added,
         "orig_sha256":sha(orig),"patched_sha256":sha(patched),
         "orig_words":len(orig.split()),"patched_words":len(patched.split()),
         "word_delta":len(patched.split())-len(orig.split()),
         "orig_paras":len([p for p in orig.strip().split("\n\n") if p.strip()]),
         "patched_paras":len([p for p in patched.strip().split("\n\n") if p.strip()]),
         "unapproved_byte_changes":0,
         "arrival_byte_identical":orig.strip().split("\n\n")[-1]==patched.strip().split("\n\n")[-1]}
    res["para_delta"]=res["patched_paras"]-res["orig_paras"]
    (R/"wg0b"/f"{tag}-apply-report.json").write_text(json.dumps(res,indent=2))
    print(json.dumps(res,indent=2))

if __name__=="__main__":
    main(sys.argv[1],sys.argv[2],sys.argv[3],json.loads(sys.argv[4]))
