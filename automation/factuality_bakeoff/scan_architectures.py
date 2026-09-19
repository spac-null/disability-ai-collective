"""Reproduce the audit's turn-relation complaints over retained architectures.

Used for two purposes: it shows what the current production checker does on real data,
and it surfaces under-cited-basis candidates for the project gold set.
"""
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cm_baseline as B  # noqa: E402
import cm_evidence as E  # noqa: E402

rows = []
stats = collections.Counter()

for arch_path in sorted(glob.glob("/srv/data/cripminds-new-engine-v1/*/ARCHITECTURE.json")):
    run_dir = os.path.dirname(arch_path)
    fem = os.path.join(run_dir, "FINAL_EVIDENCE_MANIFEST.json")
    if not os.path.exists(fem):
        continue
    try:
        arch = json.load(open(arch_path))
        facts = (json.load(open(fem)) or {}).get("facts") or {}
    except Exception:
        continue
    if not facts:
        continue
    stats["architectures_scanned"] += 1

    lens = arch.get("final_lens") or {}
    targets = [
        ("final_lens.lens_claim", lens.get("lens_claim"), lens.get("evidence_basis")),
        ("crip_turn", arch.get("crip_turn"), arch.get("use_facts")),
        ("turn", arch.get("turn"), arch.get("use_facts")),
    ]
    for field, text, basis in targets:
        if not text or not basis:
            continue
        res = B.both_conditions(text, basis, facts)
        stats["turns_checked"] += 1
        cited = res["CITED_BASIS"]
        comp = res["COMPLETE_FROZEN_EVIDENCE"]
        if cited["decision"] == "UNSUPPORTED":
            stats["refused_on_cited_basis"] += 1
            shape = ("UNDER_CITED_SHAPE" if comp["decision"] == "SUPPORTED"
                     else "REFUSED_EVEN_ON_COMPLETE_EVIDENCE")
            stats[shape] += 1
            rows.append({
                "run_id": os.path.basename(run_dir), "field": field,
                "text": text, "declared_basis": basis,
                "cited_errors": cited["errors"], "complete_decision": comp["decision"],
                "complete_errors": comp["errors"], "shape": shape,
            })

print("## stats")
for k, v in stats.most_common():
    print("   %-36s %d" % (k, v))

print("\n## complaints (%d)" % len(rows))
for r in rows:
    print("\n=== %s | %s | %s" % (r["run_id"][:44], r["field"], r["shape"]))
    print("   RELATIONS REFUSED:", [(e["relation"], e["carried_by"]) for e in r["cited_errors"]])
    print("   DECLARED BASIS:", r["declared_basis"])
    print("   TEXT:", (r["text"] or "")[:320])
    if r["complete_errors"]:
        print("   STILL REFUSED ON COMPLETE:", [(e["relation"], e["carried_by"]) for e in r["complete_errors"]])

out = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff/systems/BASELINE_ARCH_SCAN.json"
with open(out, "w") as fh:
    json.dump({"stats": dict(stats), "rows": rows, "question_answered": B.QUESTION}, fh, indent=1)
print("\nwrote", out)
