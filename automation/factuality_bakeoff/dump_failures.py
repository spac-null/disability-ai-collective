"""Dump the failure-side candidate material in full, for hand adjudication."""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm_evidence as E

print("#" * 30, "FACT_CHECK contradicted / advisory")
for g in sorted(glob.glob("/srv/data/cripminds-new-engine-v1/*/FACT_CHECK*.json")):
    d = json.load(open(g))
    run = os.path.basename(os.path.dirname(g))
    for key in ("contradicted", "blocking_contradictions", "soft_findings", "advisory"):
        for f in (d.get(key) or []):
            print("\n=== %s :: %s :: %s" % (run, os.path.basename(g), key))
            print(json.dumps(f, indent=1)[:1500])

print("\n\n", "#" * 30, "SPAN_NOT_FOUND facts")
cen = json.load(open("/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff/gold/SUPPORT_CENSUS.json"))
for r in cen["rows"]:
    if r["kind"] != "VERBATIM_IN_CITED":
        run = E.load_run("/srv/data/cripminds-new-engine-v1/" + r["run_id"])
        fact = run["facts"][r["fact_id"]]
        print("\n=== %s %s (%s)" % (r["run_id"], r["fact_id"], r["kind"]))
        print(" prop:", fact.get("proposition"))
        print(" span:", (fact.get("support_span") or "")[:300])
        print(" cited:", fact.get("evidence_ids"))
