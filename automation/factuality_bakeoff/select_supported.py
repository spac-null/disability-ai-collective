"""Propose SUPPORTED_DIRECT and SUPPORTED_RELATION candidates for hand adjudication.

Only runs that carry COMPLETE frozen source text are used, so that a later UNSUPPORTED
judgement on the same article could in principle be checked too. Candidates are spread
across distinct articles; final labels are assigned by hand, not by this script.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm_evidence as E

REL = {
    "CAUSE": r"\bbecause\b|\bcaused?\b|\bled to\b|\bdue to\b|\bproduces?\b",
    "TEMPORAL": r"\bbefore\b|\bafter\b|\buntil\b|\bsince\b|\bthen\b",
    "COMPARISON": r"\bmore\b|\bless\b|\bfewer\b|\bthan\b|\bunlike\b|\blarger\b|\bsmaller\b",
    "NEGATION": r"\bnot\b|\bno\b|\bwithout\b|\bcannot\b|\bnever\b",
    "ATTRIBUTION": r"\bsaid\b|\bsays\b|\bwrote\b|\baccording to\b|\bdescribes?\b|\bstates?\b|\btold\b",
    "SUPERLATIVE": r"\b(?:most|least|best|worst|largest|oldest|first)\b",
}
WORD = re.compile(r"[a-z0-9]+")
STOP = set("the a an of to in on at for from by with and or but as is are was were be "
           "been being this that these those it its his her their there".split())


def toks(s):
    return {w for w in WORD.findall(s.lower()) if w not in STOP and len(w) > 2}


want_rel = "--relation" in sys.argv
limit_per_article = 2
rows = []

for d in sorted(glob.glob("/srv/data/cripminds-new-engine-v1/*/")):
    if not os.path.exists(os.path.join(d, "FINAL_EVIDENCE_MANIFEST.json")):
        continue
    run = E.load_run(d)
    if not run["sources"] or not run["facts"]:
        continue
    complete, _ = E.source_text_for(run, None, complete=True)
    picked = 0
    for fid, fact in run["facts"].items():
        if picked >= limit_per_article:
            break
        prop, span = fact.get("proposition"), fact.get("support_span")
        if not prop or not span:
            continue
        span_n = E.normalize(span)[0]
        if span_n not in complete:
            continue
        # proposition must be judgeable from the span alone: high term coverage
        pt, st = toks(prop), toks(span_n)
        if not pt:
            continue
        cover = len(pt & st) / len(pt)
        if cover < 0.75:
            continue
        if len(prop) < 60 or len(prop) > 260:
            continue
        rel_hits = [k for k, p in REL.items()
                    if re.search(p, prop, re.I) and re.search(p, span_n, re.I)]
        if want_rel and not rel_hits:
            continue
        if not want_rel and rel_hits:
            continue
        rows.append((run["run_id"], (run["subject"] or "")[:60], fid,
                     fact.get("evidence_ids"), rel_hits, cover, prop, span_n[:260]))
        picked += 1

print("candidates:", len(rows), "distinct runs:", len({r[0] for r in rows}))
for r in rows[:60]:
    print("\n=== %s | %s | cited=%s | rel=%s | cover=%.2f" % (r[0][:46], r[2], r[3], r[4], r[5]))
    print("  SUBJ:", r[1])
    print("  PROP:", r[6])
    print("  SPAN:", r[7])
