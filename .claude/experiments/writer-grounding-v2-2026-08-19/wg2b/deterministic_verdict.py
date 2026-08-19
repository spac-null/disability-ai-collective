#!/usr/bin/env python3
"""WG-2B — smallest deterministic re-verdict rule set, tested (not installed).
Operates ONLY on proposition text + source-anchor metadata from the frozen
WG-1B enumeration. No gold ids anywhere. No large blocklists."""
import json,re,sys
from pathlib import Path
W=Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v2-2026-08-19")
SRC=(W/"inputs/source-snapshot.txt").read_text(encoding="utf-8")
SRCN=re.sub(r"[’']","'",SRC.lower())

def insrc(s):
    return re.sub(r"[’']","'",s.lower()) in SRCN

# --- signals -------------------------------------------------------------
TEMPORAL = re.compile(r"\b(an hour|a minute|half an hour|that afternoon|an afternoon|the afternoon|"
                      r"on the day|in (january|february|march|april|may|june|july|august|september|"
                      r"october|november|december)|\d+\s*(minutes?|hours?|days?|weeks?|months?|years?)\s*(ago|earlier|later))\b", re.I)
MENTAL   = re.compile(r"\b(did not know|didn't know|had no way of|unaware|not in their possession|"
                      r"brought (nothing|anything)|knew|believed|felt|expected|anticipat\w*)\b", re.I)
PROPER   = re.compile(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+)\b")
QUANT    = re.compile(r"\b(most|some|many|much|several|plenty|a lot)\b", re.I)
COMPAR   = re.compile(r"\b(harder|easier|more|less|greater|stronger|the (harder|easier) one|"
                      r"presses|\w+er than)\b", re.I)
CAUSAL   = re.compile(r"\b(because|since|which means|so that|as a result)\b", re.I)
MARKER   = re.compile(r"\b(perhaps|it seems|seems|on (this|that|one) reading|read one way|arguably|"
                      r"may|might|the article|this piece|one could|appears to)\b", re.I)

def rules(p):
    txt = p.get("PROPOSITION","") or p.get("EXACT_SPAN","")
    span= p.get("EXACT_SPAN","") or txt
    anchor = (p.get("SOURCE_ANCHOR_RETURNED") or "").strip()
    hits=[]
    # R1 unsupported concrete temporal expression
    for m in TEMPORAL.finditer(span):
        if not insrc(m.group()): hits.append(("R1_TEMPORAL",m.group()))
    # R2 mental/knowledge state not licensed by an anchor
    if MENTAL.search(span) and not anchor: hits.append(("R2_MENTAL_STATE","no anchor"))
    # R3 proper noun absent from source
    for m in PROPER.finditer(span):
        if not insrc(m.group()): hits.append(("R3_PROPER_NOUN",m.group()))
    # R4 qualifier dropped: anchor carries a quantifier the proposition lacks
    if anchor and QUANT.search(anchor) and not QUANT.search(span):
        hits.append(("R4_QUALIFIER_DROPPED",QUANT.search(anchor).group()))
    return hits

def marker_rule(p):
    """R5 — the VISIBLE-MARKER hypothesis, tested separately (task section 7)."""
    span = p.get("EXACT_SPAN","") or p.get("PROPOSITION","")
    anchor=(p.get("SOURCE_ANCHOR_RETURNED") or "").strip()
    if (COMPAR.search(span) or CAUSAL.search(span)) and not MARKER.search(span) and not anchor:
        return [("R5_UNMARKED_COMPARATIVE_CAUSAL","")]
    return []

out={}
for tag in ["form1-3","r2","r3"]:
    props=json.load(open(W/f"wg2a/{tag}-propositions.json"))
    res=[]
    for p in props:
        core=rules(p); mk=marker_rule(p)
        res.append({"ID":p["ID"],"EXACT_SPAN":p["EXACT_SPAN"],"PRIOR":p["PRIOR_VERDICT"],
                    "ANCHOR":bool((p.get("SOURCE_ANCHOR_RETURNED") or "").strip()),
                    "core_hits":core,"marker_hits":mk,
                    "VERDICT_CORE":"UNSUPPORTED" if core else p["PRIOR_VERDICT"],
                    "VERDICT_CORE_PLUS_MARKER":"UNSUPPORTED" if (core or mk) else p["PRIOR_VERDICT"]})
    out[tag]=res
    (W/f"wg2b/{tag}-deterministic.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
    c=sum(1 for r in res if r["core_hits"]); m=sum(1 for r in res if r["marker_hits"] and not r["core_hits"])
    print(f"{tag}: {len(res)} props | core-rule flags {c} | marker-only additional flags {m}")
