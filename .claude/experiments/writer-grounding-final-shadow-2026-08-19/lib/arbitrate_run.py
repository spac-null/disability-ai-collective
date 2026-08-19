#!/usr/bin/env python3
"""FINAL REPLAY — run the CORRECTED router (WG-6N arbitrate_v2) over one phase.
usage: arbitrate_run.py pre|post   -> writes score/{phase}-ARBITRATION.json"""
import json, collections, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from arbitrate_v2 import arbitrate, load_condition

PHASE = sys.argv[1]
assert PHASE in ("pre", "post")
R = Path(__file__).resolve().parent.parent
D = R / PHASE

units, diag = [], {}
for tag in ("form1-3", "r2", "r3"):
    A, B, E = load_condition(D, tag, f"{tag}-wg4a-raw.json", f"{tag}-wg4b-raw.json",
                             f"{tag}-extract-raw.json")
    u, d = arbitrate(tag, A, B, E)
    units += u
    diag[tag] = d

unrouted = sum(len(d["unrouted_negatives"]) for d in diag.values())
synth = [u for d in diag.values() for u in d["synthesised_units"]]
disag = [x for d in diag.values() for x in d["proof_vs_verdict_disagreements"]]
forb = sorted({f for d in diag.values() for f in d["forbidden_fields_read"]})
out = {
    "phase": PHASE, "router": "WG-6N arbitrate_v2 (corrected, P3 synthesis)",
    "parents": len({(u["tag"], u["parent"]) for u in units}), "commitments": len(units),
    "routed_to_wg4b": sum(1 for u in units if u["owner"] == "WG-4B"),
    "routed_to_wg4a": sum(1 for u in units if u["owner"] == "WG-4A"),
    "verdicts": dict(collections.Counter(u["arbitrated_verdict"] for u in units)),
    "unrouted": unrouted, "synthesised_units": synth,
    "proof_vs_verdict_disagreements": disag, "forbidden_fields_read": forb,
    "arbitrated": units,
}
(R / "score" / f"{PHASE}-ARBITRATION.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(f"{PHASE}: parents {out['parents']} commitments {out['commitments']} verdicts {out['verdicts']}")
print(f"  -> WG-4B {out['routed_to_wg4b']}  -> WG-4A {out['routed_to_wg4a']}  unrouted {unrouted}"
      f"  synthesised {len(synth)}  disagreements {len(disag)}  forbidden {forb}")
for u in units:
    if u["arbitrated_verdict"] == "UNSUPPORTED":
        print(f"  UNSUPPORTED [{u['tag']}/{u['parent']}] {u['commitment_id']} [{u['commitment_type']}] "
              f"owner={u['owner']} path={u['routing_path']}")
        print(f"      span: \"{u['parent_span']}\"")
        print(f"      commitment: {u['proposition']}")
