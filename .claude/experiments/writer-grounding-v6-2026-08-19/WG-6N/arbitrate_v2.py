#!/usr/bin/env python3
"""WG-6N CORRECTED MODULAR VERDICT ARBITRATION (router v2).

Closes WG6-N1. Routing authority for a negative meta-source claim is WG-4B's
own semantic classification (IN_SCOPE + NEGATIVE), never a WG-4A type label.

Difference from WG-6A/arbitrate.py is exactly one added path, P3: a negative
parent with no SOURCE_META carrier and != 1 commitment now emits a synthesised
WG-4B unit instead of dropping WG-4B's verdict on the floor. No commitment is
ever reassigned away from WG-4A by that path, so independent commitments
sharing the parent sentence keep their own verdicts.

Rules fixed in PRE-REGISTRATION.md before this ran. No model calls. No gold.
"""
import json

PROOF_TO_VERDICT = {"EXPLICIT": "SUPPORTED", "BOUNDED_ABSENCE": "SUPPORTED", "NONE": "UNSUPPORTED"}

# carried over verbatim from WG-6A: an empty extraction anchor may never decide
FORBIDDEN_FIELDS = {"EXTRACTION_ANCHOR_WAS_EMPTY"}


def load_condition(base, tag, wg4a_name, wg4b_name, extract_name):
    a = json.loads((base / wg4a_name).read_text())
    b = json.loads((base / wg4b_name).read_text())
    e = json.loads((base / extract_name).read_text())
    A = {x["PARENT_CLAIM_ID"]: x for x in (a["propositions"] if isinstance(a, dict) else a)}
    B = {x["ID"]: x for x in (b["results"] if isinstance(b, dict) else b)}
    E = {p["ID"]: p for p in (e["propositions"] if isinstance(e, dict) else e)}
    return A, B, E


def arbitrate(tag, A, B, E, reads=None):
    """Returns (units, diagnostics). Deterministic, field-driven only."""
    reads = reads if reads is not None else []

    def field(d, k):
        assert k not in FORBIDDEN_FIELDS, f"forbidden decision input read: {k}"
        reads.append(k)
        return d.get(k)

    units, disagreements, unrouted, synthesised = [], [], [], []

    for pid, parent in A.items():
        b = B.get(pid, {})
        is_neg = field(b, "IN_SCOPE") == "YES" and field(b, "NEGATIVE") == "YES"
        cs = parent.get("COMMITMENTS", [])
        meta = [c for c in cs if c.get("COMMITMENT_TYPE") == "SOURCE_META"]
        span = E.get(pid, {}).get("EXACT_SPAN")

        # ---- which path owns this parent's negative claim --------------------
        if is_neg and meta:
            path = "P1_SOURCE_META_CARRIER"
        elif is_neg and len(cs) == 1:
            path = "P2_SINGLE_COMMITMENT_CARRIER"
        elif is_neg:
            path = "P3_SYNTHESISED_CARRIER"      # NEW — closes WG6-N1
        else:
            path = "NOT_NEGATIVE"

        proof = field(b, "PROOF_TYPE") if is_neg else None
        if is_neg:
            assert proof in PROOF_TO_VERDICT, f"ARBITRATION_ERROR {tag}/{pid} proof={proof!r}"
            neg_verdict = PROOF_TO_VERDICT[proof]
            own_v = b.get("VERDICT")
            if (own_v == "UNSUPPORTED") != (neg_verdict == "UNSUPPORTED"):
                disagreements.append({"tag": tag, "parent": pid, "proof_type": proof,
                                      "proof_derived": neg_verdict, "wg4b_verdict_field": own_v})

        for c in cs:
            to_b = path in ("P1_SOURCE_META_CARRIER", "P2_SINGLE_COMMITMENT_CARRIER") and (
                c.get("COMMITMENT_TYPE") == "SOURCE_META" or path == "P2_SINGLE_COMMITMENT_CARRIER")
            if to_b:
                v, owner, cls, pt = neg_verdict, "WG-4B", "NEGATIVE_SOURCE", proof
            else:
                v, owner, cls, pt = c.get("SUPPORT_STATUS"), "WG-4A", "ORDINARY", None
            units.append({
                "tag": tag, "parent": pid, "commitment_id": c["COMMITMENT_ID"],
                "commitment_type": c.get("COMMITMENT_TYPE"), "proposition": c.get("PROPOSITION"),
                "parent_span": span, "class": cls, "owner": owner, "routing_path": path,
                "wg4a_status": c.get("SUPPORT_STATUS"), "wg4b_proof_type": pt,
                "wg4b_scope": b.get("SCOPE") if to_b else None,
                "arbitrated_verdict": v, "synthesised": False,
                "reason": c.get("REASON"),
                "flipped_by_arbitration": to_b and v != c.get("SUPPORT_STATUS"),
            })

        # ---- P3: WG-4B's verdict gets its own unit, nothing is displaced -----
        if path == "P3_SYNTHESISED_CARRIER":
            u = {
                "tag": tag, "parent": pid, "commitment_id": f"{pid}-NEG",
                "commitment_type": "NEGATIVE_SOURCE_CLAIM",
                "proposition": b.get("NEGATIVE_CLAIM"),
                "parent_span": span, "class": "NEGATIVE_SOURCE", "owner": "WG-4B",
                "routing_path": path, "wg4a_status": None, "wg4b_proof_type": proof,
                "wg4b_scope": b.get("SCOPE"), "arbitrated_verdict": neg_verdict,
                "synthesised": True, "reason": b.get("REASON"),
                "flipped_by_arbitration": False,
                "coexisting_wg4a_commitments": [
                    {"commitment_id": c["COMMITMENT_ID"], "type": c.get("COMMITMENT_TYPE"),
                     "kept_verdict": c.get("SUPPORT_STATUS")} for c in cs],
            }
            units.append(u)
            synthesised.append(u)

    diag = {
        "unrouted_negatives": unrouted,          # unreachable by construction
        "proof_vs_verdict_disagreements": disagreements,
        "synthesised_units": synthesised,
        "decision_fields_read": sorted(set(reads)),
        "forbidden_fields_read": sorted(set(reads) & FORBIDDEN_FIELDS),
    }
    return units, diag
