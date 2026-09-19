import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = "/srv/data/cripminds-new-engine-v1/"
for run in ["production-20260903T210946Z-4dd582f6", "production-20260903T212459Z-601f5d23"]:
    d = json.load(open(BASE + run + "/GROUNDING_V2_SHADOW.json"))
    print("\n" + "#" * 76)
    print("## RUN", run)
    for f in (d.get("findings") or []):
        r = f.get("result") or {}
        if r.get("classification") not in ("UNSUPPORTED", "LEGITIMATE_INTERPRETATION"):
            continue
        print("\n  --- %s  %s (derivation=%s)" % (r.get("classification"), f.get("atomic_id"), f.get("derivation")))
        print("      CLAIM:", f.get("atomic_claim"))
        print("      PARENT:", (f.get("parent_exact_span") or "")[:220])
        for k in ("why", "reason", "explanation", "note"):
            if r.get(k):
                print("      WHY:", str(r[k])[:600])
