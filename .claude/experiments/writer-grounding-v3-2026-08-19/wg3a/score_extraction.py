#!/usr/bin/env python3
"""WG-3A scorer. Content-preservation, NOT sentence coverage.

Required factual commitments per gold finding are declared HERE, derived from the
Gold V2.1 'why' fields, and were written BEFORE any extraction output was read."""
import json, re, sys
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v3-2026-08-19")

ART = {"form1-3":"form1-3-article.md","r2":"form-1.3-r2-article.md","r3":"form-1.3-r3-article.md"}
GOLD_ART = {"FORM-1.3":"form1-3","FORM-1.3-R2":"r2","FORM-1.3-R3":"r3"}

# gold_id -> (tag, gold span, [ (commitment label, regex over ATOMIC_PROPOSITION+S/P/O) ])
COMMITMENTS = {
 "G13-01": ("form1-3","City Art Centre",
   [("names the venue 'City Art Centre'", r"city art centre")]),
 "G13-02": ("form1-3","it is happening to a person who did not know the work existed an hour ago",
   [("person did NOT know the work existed", r"(did ?n[o']t|never|no[t]? )\s*\w*\s*know|unaware|not know"),
    ("the interval 'an hour'", r"an hour|one hour|hour ago|hour earlier")]),
 "G13-04": ("form1-3","not because the review ranks them or gathers them into a group",
   [("negation preserved", r"\b(not|does ?n[o']t|no)\b"),
    ("the REVIEW is the actor", r"review|reviewer"),
    ("rank / group predicate", r"rank|group|gather|place[sd]? them|above")]),
 "GR2-01": ("r2","without the visitor having brought anything to the encounter except the willingness to walk in",
   [("negation / exclusivity ('nothing except')", r"\bnothing\b|\bnot\b|without|anything|only|except|sole"),
    ("what the visitor BROUGHT", r"brought|bring|brings"),
    ("willingness to walk in", r"willing|walk in")]),
 "GR2-02": ("r2","taken here not because the review places them above the rest but simply because they can be set beside each other",
   [("negation preserved", r"\b(not|does ?n[o']t|no)\b"),
    ("the REVIEW is the actor", r"review|reviewer"),
    ("rank/placement predicate", r"place[sd]?|rank|above the rest|above")]),
 "GR2-04": ("r2","Sadao Hasegawa's work, the review adds, stayed unpublished and unseen in his lifetime.",
   [("Hasegawa's work stayed unpublished/unseen", r"unpublished|unseen"),
    ("ABSOLUTE scope (no 'most' qualifier)", r"__ADJUDICATE__")]),
 "GR3-01": ("r3","the visitor arrives at a name that was not in their possession an hour earlier",
   [("visitor did NOT have the name", r"\bnot\b|did ?n[o']t|never|unknown|unfamiliar"),
    ("the interval 'an hour earlier'", r"an hour|one hour|hour earlier|hour ago")]),
 "GR3-03": ("r3","walking around Edinburgh in August",
   [("the month August", r"august")]),
}
UNCERTAIN = {
 "U-R2-01": ("r2","the festival's characteristic verb",
   [("verb attributed to the FESTIVAL (possessive)", r"festival")]),
 "U-R2-02": ("r2","What it does not describe, and cannot",
   [("negation preserved", r"\bnot\b|does ?n[o']t"),
    ("modal impossibility 'cannot'", r"cannot|can ?not|unable|impossible")]),
}

def norm(s): return ' '.join((s or '').lower().replace('’',"'").replace('—','-').replace('–','-').split())

def load(tag):
    p=W/"wg3a"/f"{tag}-extract-raw.json"
    d=json.loads(p.read_text(encoding="utf-8"))
    return d["propositions"] if isinstance(d,dict) else d

def main():
    report={"experiment":"WG-3A EXTRACTION FIDELITY","gold":"GOLD V2.1 FROZEN","findings":{},"uncertain":{},"structural":{}}
    props={}
    for tag,f in ART.items():
        art=(W/"inputs"/f).read_text(encoding="utf-8")
        P=load(tag); props[tag]=P
        ids=set(); bad=[]
        for pr in P:
            ids.add(pr.get("SENTENCE_ID"))
            sp=pr.get("EXACT_SPAN","")
            if sp and sp not in art: bad.append({"ID":pr.get("ID"),"span":sp[:90]})
        nsent=json.loads((W/"wg3a"/f"{tag}-extract-meta.json").read_text())["sentences"]
        report["structural"][tag]={"propositions":len(P),"sentence_ids_covered":len(ids),
          "sentences_expected":nsent,"coverage_complete":len(ids)==nsent,
          "missing_sentence_ids":sorted(set(range(1,nsent+1))-ids),
          "non_contiguous_spans":len(bad),"non_contiguous_examples":bad[:5],
          "claim_object_type_dist":{k:sum(1 for x in P if x.get("CLAIM_OBJECT_TYPE")==k) for k in
            ["SUBJECT_MATTER","HUMAN_STATE","SOURCE_OR_REVIEW","CONCRETE_WORLD_DETAIL","OTHER"]}}
    for label,table,bucket in (("finding",COMMITMENTS,"findings"),("uncertain",UNCERTAIN,"uncertain")):
        for gid,(tag,gspan,checks) in table.items():
            gs=norm(gspan); gw=set(gs.split())
            cands=[]
            for pr in props[tag]:
                ps=norm(pr.get("EXACT_SPAN",""))
                if not ps: continue
                ov=len(gw & set(ps.split()))
                if ps in gs or gs in ps or ov>=max(3,int(.4*len(gw))):
                    blob=norm(" | ".join([pr.get("ATOMIC_PROPOSITION",""),pr.get("SUBJECT",""),
                                          pr.get("PREDICATE",""),pr.get("OBJECT_OR_COMPLEMENT","")]))
                    cands.append({"ID":pr.get("ID"),"TYPE":pr.get("CLAIM_OBJECT_TYPE"),
                      "EXACT_SPAN":pr.get("EXACT_SPAN"),"ATOMIC":pr.get("ATOMIC_PROPOSITION"),
                      "SUBJ":pr.get("SUBJECT"),"PRED":pr.get("PREDICATE"),"OBJ":pr.get("OBJECT_OR_COMPLEMENT"),
                      "ANCHOR":pr.get("SOURCE_ANCHOR",""),"_blob":blob})
            res=[]
            for cl,rx in checks:
                if rx=="__ADJUDICATE__": res.append({"commitment":cl,"met":None,"note":"manual adjudication"}); continue
                hits=[c["ID"] for c in cands if re.search(rx,c["_blob"])]
                res.append({"commitment":cl,"met":bool(hits),"met_by":hits})
            for c in cands: c.pop("_blob")
            report[bucket][gid]={"tag":tag,"gold_span":gspan,"candidates":cands,"commitment_checks":res}
    (W/"wg3a"/"WG3A-SCORING-EVIDENCE.json").write_text(json.dumps(report,indent=2))
    print("=== STRUCTURAL ===")
    for t,s in report["structural"].items():
        print(f'  {t:9} props {s["propositions"]:3}  sentences {s["sentence_ids_covered"]}/{s["sentences_expected"]}'
              f'  complete={s["coverage_complete"]}  bad_spans={s["non_contiguous_spans"]}')
        print(f'            types {s["claim_object_type_dist"]}')
        if s["missing_sentence_ids"]: print(f'            MISSING {s["missing_sentence_ids"]}')
        if s["non_contiguous_examples"]: print(f'            BAD {s["non_contiguous_examples"]}')
    print("\n=== COMMITMENT CHECKS ===")
    for bucket in ("findings","uncertain"):
        for gid,d in report[bucket].items():
            met=[c for c in d["commitment_checks"] if c["met"] is True]
            tot=[c for c in d["commitment_checks"]]
            print(f'\n{gid} [{d["tag"]}] candidates={len(d["candidates"])}  commitments met {len(met)}/{len(tot)}')
            for c in d["commitment_checks"]:
                print(f'    {"OK " if c["met"] else ("?? " if c["met"] is None else "MISS")} {c["commitment"]}'
                      + (f'  <- {c.get("met_by")}' if c.get("met_by") else ""))
    print("\nEvidence written: wg3a/WG3A-SCORING-EVIDENCE.json")

main()
