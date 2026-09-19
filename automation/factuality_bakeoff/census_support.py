"""Census: how much mechanically verifiable DIRECT_SOURCE material exists.

For every frozen fact in every retained run, test whether its recorded support_span
appears verbatim in the normalized text of the sources it cites. A verbatim hit makes
the fact's proposition a DIRECT_SOURCE candidate: the source text itself resolves it.
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm_evidence as E

RUNS = sorted(glob.glob("/srv/data/cripminds-new-engine-v1/*/"))

stats = collections.Counter()
per_subject = collections.defaultdict(lambda: collections.Counter())
rows = []

for run_dir in RUNS:
    if not os.path.exists(os.path.join(run_dir, "FINAL_EVIDENCE_MANIFEST.json")):
        continue
    run = E.load_run(run_dir)
    if not run["sources"] or not run["facts"]:
        stats["run_missing_sources_or_facts"] += 1
        continue
    stats["runs_usable"] += 1
    subj = (run["subject"] or run["run_id"])[:70]

    for fid, fact in run["facts"].items():
        span = fact.get("support_span")
        prop = fact.get("proposition")
        if not span or not prop:
            stats["fact_missing_span_or_prop"] += 1
            continue
        span_n = E.normalize(span)[0]
        cited = fact.get("evidence_ids") or []
        cited_ctx, cited_ids = E.source_text_for(run, cited, complete=False)
        all_ctx, _ = E.source_text_for(run, None, complete=True)

        in_cited = span_n in cited_ctx
        in_all = span_n in all_ctx
        if in_cited:
            kind = "VERBATIM_IN_CITED"
        elif in_all:
            kind = "VERBATIM_ONLY_IN_OTHER_SOURCE"
        else:
            kind = "SPAN_NOT_FOUND"
        stats[kind] += 1
        per_subject[subj][kind] += 1
        rows.append({
            "run_id": run["run_id"], "subject": subj, "fact_id": fid, "kind": kind,
            "cited_ids": cited_ids, "claim_kind": fact.get("claim_kind"),
            "claim_type": fact.get("claim_type"),
            "prop_len": len(prop), "span_len": len(span),
        })

print("## totals")
for k, v in stats.most_common():
    print("  %-34s %d" % (k, v))

subj_with_verbatim = [s for s, c in per_subject.items() if c["VERBATIM_IN_CITED"] > 0]
print("\ndistinct subjects with >=1 verbatim-in-cited fact:", len(subj_with_verbatim))

ck = collections.Counter((r["claim_kind"], r["kind"]) for r in rows)
print("\n## claim_kind x verification (top 20)")
for k, v in ck.most_common(20):
    print("  ", k, v)

out = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff/gold/SUPPORT_CENSUS.json"
with open(out, "w") as fh:
    json.dump({"stats": dict(stats), "rows": rows}, fh, indent=1)
print("\nwrote", out, len(rows), "rows")
