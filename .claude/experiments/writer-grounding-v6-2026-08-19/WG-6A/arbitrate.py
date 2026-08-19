#!/usr/bin/env python3
"""WG-6A MODULAR VERDICT ARBITRATION.

Composes the frozen WG-4A (commitment decomposition) and WG-4B (negative
meta-source proof) outputs through deterministic routing. No model calls.
Routing reads only declared component fields. Rules fixed in PRE-REGISTRATION.md.
"""
import json, collections
from pathlib import Path

W = Path(__file__).resolve().parent
I = W / "inputs"
TAGS = {"FORM-1.3": "form1-3", "FORM-1.3-R2": "r2", "FORM-1.3-R3": "r3"}

# ---- forbidden decision inputs: asserted never consulted -------------------
FORBIDDEN_FIELDS = {"EXTRACTION_ANCHOR_WAS_EMPTY"}
_reads = []
def field(d, k):
    """Guarded read so the audit trail proves which fields drove decisions."""
    assert k not in FORBIDDEN_FIELDS, f"forbidden decision input read: {k}"
    _reads.append(k)
    return d.get(k)

def load(p):
    return json.loads((I / p).read_text())

wg4a, wg4b, ex = {}, {}, {}
for tag in TAGS.values():
    d = load(f"wg4a-{tag}-decomp-raw.json")
    wg4a[tag] = {x["PARENT_CLAIM_ID"]: x for x in (d["propositions"] if isinstance(d, dict) else d)}
    d = load(f"wg4b-{tag}-negproof-raw.json")
    wg4b[tag] = {x["ID"]: x for x in (d["results"] if isinstance(d, dict) else d)}
    d = load(f"{tag}-extract-raw.json")
    ex[tag] = {p["ID"]: p for p in (d["propositions"] if isinstance(d, dict) else d)}

PROOF_TO_VERDICT = {"EXPLICIT": "SUPPORTED", "BOUNDED_ABSENCE": "SUPPORTED", "NONE": "UNSUPPORTED"}

arb = []          # one record per arbitrated commitment
disagreements = []
unrouted = []

for tag in TAGS.values():
    for pid, parent in wg4a[tag].items():
        b = wg4b[tag].get(pid, {})
        in_scope = field(b, "IN_SCOPE") == "YES"
        negative = field(b, "NEGATIVE") == "YES"
        is_neg_parent = in_scope and negative
        commitments = parent.get("COMMITMENTS", [])
        meta = [c for c in commitments if c.get("COMMITMENT_TYPE") == "SOURCE_META"]

        # pre-registered fallback for a negative parent with no SOURCE_META target
        fallback_single = is_neg_parent and not meta and len(commitments) == 1

        for c in commitments:
            ctype = c.get("COMMITMENT_TYPE")
            route_to_b = is_neg_parent and (ctype == "SOURCE_META" or fallback_single)

            if route_to_b:
                proof = field(b, "PROOF_TYPE")
                assert proof in PROOF_TO_VERDICT, f"ARBITRATION_ERROR {tag}/{pid} proof={proof!r}"
                verdict = PROOF_TO_VERDICT[proof]
                owner, cls = "WG-4B", "NEGATIVE_SOURCE"
                own_v = b.get("VERDICT")
                # WG-4B verdict strings for supported negatives may be SUPPORTED or
                # INTERPRETATION; only a SUPPORTED/UNSUPPORTED flip is a disagreement.
                if (own_v == "UNSUPPORTED") != (verdict == "UNSUPPORTED"):
                    disagreements.append({"tag": tag, "parent": pid, "commitment": c["COMMITMENT_ID"],
                                          "proof_type": proof, "proof_derived": verdict,
                                          "wg4b_verdict_field": own_v})
            else:
                verdict = c.get("SUPPORT_STATUS")
                owner, cls = "WG-4A", "ORDINARY"
                proof = None
                if is_neg_parent and not meta and len(commitments) > 1:
                    cls = "ARBITRATION_UNROUTED"
                    unrouted.append({"tag": tag, "parent": pid, "commitment": c["COMMITMENT_ID"],
                                     "commitments_in_parent": len(commitments)})

            arb.append({
                "tag": tag, "parent": pid, "commitment_id": c["COMMITMENT_ID"],
                "commitment_type": ctype, "proposition": c.get("PROPOSITION"),
                "parent_span": ex[tag].get(pid, {}).get("EXACT_SPAN"),
                "class": cls, "owner": owner,
                "wg4a_status": c.get("SUPPORT_STATUS"),
                "wg4b_proof_type": proof,
                "wg4b_scope": b.get("SCOPE") if route_to_b else None,
                "arbitrated_verdict": verdict,
                "flipped_by_arbitration": route_to_b and verdict != c.get("SUPPORT_STATUS"),
            })

out = {
    "method": "REUSE_RESCORE_NO_MODEL_CALLS",
    "parents": sum(len(v) for v in wg4a.values()),
    "commitments": len(arb),
    "routed_to_wg4b": sum(1 for a in arb if a["owner"] == "WG-4B"),
    "routed_to_wg4a": sum(1 for a in arb if a["owner"] == "WG-4A"),
    "arbitration_unrouted": unrouted,
    "proof_vs_verdict_disagreements": disagreements,
    "verdicts": dict(collections.Counter(a["arbitrated_verdict"] for a in arb)),
    "flips_vs_wg4a": [a for a in arb if a["flipped_by_arbitration"]],
    "forbidden_fields_read": sorted(set(_reads) & FORBIDDEN_FIELDS),
    "decision_fields_read": sorted(set(_reads)),
    "arbitrated": arb,
}
(W / "ARBITRATION.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))

print(f"parents {out['parents']}  commitments {out['commitments']}")
print(f"routed -> WG-4B {out['routed_to_wg4b']}   -> WG-4A {out['routed_to_wg4a']}")
print(f"arbitrated verdicts {out['verdicts']}")
print(f"unrouted negatives: {len(unrouted)}")
print(f"proof/verdict disagreements: {len(disagreements)}")
print(f"forbidden fields used in a decision: {out['forbidden_fields_read']}")
print(f"\nflips vs WG-4A standalone ({len(out['flips_vs_wg4a'])}):")
for a in out["flips_vs_wg4a"]:
    print(f"  {a['tag']}/{a['parent']} {a['commitment_id']} {a['wg4a_status']} -> {a['arbitrated_verdict']}"
          f"  [proof={a['wg4b_proof_type']}]")
    print(f"      span: {a['parent_span']}")
