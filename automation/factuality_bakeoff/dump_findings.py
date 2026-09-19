"""Dump classified grounding findings in full for one canonical run per article."""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm_evidence as E

BASE = "/srv/data/cripminds-new-engine-v1/"
CANON = sys.argv[1:] or [
    "fast-lane-v1-fresh-asl-whitehouse-20260912",
    "fast-lane-v1-fresh-immigration-20260912",
    "fast-lane-v1-replay-td-snap-20260912",
    "production-20260911T165715Z-17914595",
    "production-20260913T083824Z-f83f4b8a",
    "replay-ab-20260910T082513Z-30f2477",
    "production-20260909T080020Z-842559f7-continuation-2026-09-09T211900",
]

for run_id in CANON:
    rd = BASE + run_id
    run = E.load_run(rd)
    print("\n" + "#" * 78)
    print("## RUN", run_id)
    print("## subject:", (run["subject"] or "?")[:200])
    print("## sources:", {k: (v["publisher"], v["role"], v["raw_chars"]) for k, v in run["sources"].items()})
    print("## facts:", len(run["facts"]), "claim_map:", (run["claim_map"] or {}).get("file"))

    best = {}
    for g in sorted(glob.glob(rd + "/GROUNDING*.json")):
        b = os.path.basename(g)
        rank = 3 if "OWNER_REPAIRED_F2" in b else 2 if "OWNER_REPAIRED" in b else 1
        try:
            d = json.load(open(g))
        except Exception:
            continue
        for f in (d.get("findings") or []):
            if not isinstance(f, dict) or not f.get("classification"):
                continue
            key = f.get("quote", "")[:70]
            if key not in best or best[key][0] < rank:
                best[key] = (rank, b, f)
    for key, (rank, b, f) in best.items():
        print("\n  --- [%s] %s  (from %s)" % (f.get("classification"), f.get("id"), b))
        print("      QUOTE:", f.get("quote"))
        print("      WHY:", f.get("why"))
        if f.get("suggested_patch"):
            print("      PATCH:", str(f.get("suggested_patch"))[:300])
