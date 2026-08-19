#!/usr/bin/env python3
"""WG-6B post-repair verification. Re-runs the SAME deterministic modular
arbitration over the post-repair WG-4A/WG-4B outputs on the PATCHED articles,
then scores: gold unsupported remaining, NEW unsupported, uncertain touched."""
import json, collections
from pathlib import Path

W = Path(__file__).resolve().parent
B = W.parent
I = B.parent / "WG-6A" / "inputs"
TAGS = {"FORM-1.3": "form1-3", "FORM-1.3-R2": "r2", "FORM-1.3-R3": "r3"}
PROOF_TO_VERDICT = {"EXPLICIT": "SUPPORTED", "BOUNDED_ABSENCE": "SUPPORTED", "NONE": "UNSUPPORTED"}

def norm(s):
    return ' '.join((s or '').lower().replace('’', "'").replace('—', '-').replace('–', '-').split())

def arbitrate(tag):
    """IDENTICAL routing/arbitration rule as WG-6A."""
    a = json.loads((W / f"{tag}-wg4a-raw.json").read_text())
    b = json.loads((W / f"{tag}-wg4b-raw.json").read_text())
    A = {x["PARENT_CLAIM_ID"]: x for x in (a["propositions"] if isinstance(a, dict) else a)}
    Bm = {x["ID"]: x for x in (b["results"] if isinstance(b, dict) else b)}
    ex = json.loads((W / f"{tag}-extract-raw.json").read_text())
    E = {p["ID"]: p for p in (ex["propositions"] if isinstance(ex, dict) else ex)}
    out = []
    for pid, parent in A.items():
        nb = Bm.get(pid, {})
        is_neg = nb.get("IN_SCOPE") == "YES" and nb.get("NEGATIVE") == "YES"
        cs = parent.get("COMMITMENTS", [])
        meta = [c for c in cs if c.get("COMMITMENT_TYPE") == "SOURCE_META"]
        fallback = is_neg and not meta and len(cs) == 1
        for c in cs:
            to_b = is_neg and (c.get("COMMITMENT_TYPE") == "SOURCE_META" or fallback)
            if to_b:
                proof = nb.get("PROOF_TYPE")
                v = PROOF_TO_VERDICT.get(proof, "ARBITRATION_ERROR")
                owner, cls = "WG-4B", "NEGATIVE_SOURCE"
            else:
                v, owner, cls, proof = c.get("SUPPORT_STATUS"), "WG-4A", "ORDINARY", None
            out.append({"tag": tag, "parent": pid, "commitment_id": c["COMMITMENT_ID"],
                        "commitment_type": c.get("COMMITMENT_TYPE"), "proposition": c.get("PROPOSITION"),
                        "parent_span": E.get(pid, {}).get("EXACT_SPAN"), "owner": owner, "class": cls,
                        "wg4b_proof_type": proof, "wg4a_status": c.get("SUPPORT_STATUS"),
                        "arbitrated_verdict": v, "reason": c.get("REASON")})
    return out

arb = []
for tag in TAGS.values():
    missing = [f for f in (f"{tag}-wg4a-raw.json", f"{tag}-wg4b-raw.json") if not (W / f).exists()]
    if missing:
        print(f"MISSING for {tag}: {missing}"); raise SystemExit(1)
    arb += arbitrate(tag)

gold = json.loads((I / "gold-ledger-V2.1-FROZEN.json").read_text())
findings = {f["id"]: (art, f) for art, a in gold["articles"].items() for f in a["unsupported_findings"]}
uns = [a for a in arb if a["arbitrated_verdict"] == "UNSUPPORTED"]

print("=" * 74); print("WG-6B POST-REPAIR RE-AUDIT (identical modular instrument, patched articles)")
print(f"  parents {len({(a['tag'], a['parent']) for a in arb})}  commitments {len(arb)}")
print(f"  verdicts {dict(collections.Counter(a['arbitrated_verdict'] for a in arb))}")
print(f"\n  POST-REPAIR UNSUPPORTED: {len(uns)}")

# Does any surviving unsupported correspond to a gold finding (by span containment)?
gold_remaining, new_uns = [], []
for a in uns:
    ps = norm(a["parent_span"]); pw = set(ps.split())
    hit = None
    for gid, (art, f) in findings.items():
        if TAGS[art] != a["tag"]:
            continue
        gs = norm(f["span"]); gw = set(gs.split())
        if ps and (ps in gs or gs in ps or len(gw & pw) >= max(3, int(.4 * len(gw)))):
            hit = gid; break
    (gold_remaining if hit else new_uns).append({**a, "gold_id": hit})
    print(f'   [{a["tag"]}/{a["parent"]}] {a["commitment_id"]} [{a["commitment_type"]}] '
          f'owner={a["owner"]} gold={hit or "NEW"}')
    print(f'      span: "{a["parent_span"]}"')
    print(f'      commitment: {a["proposition"]}')
    print(f'      reason: {str(a["reason"])[:200]}')

by_art = collections.Counter(a["tag"] for a in uns)
print(f"\n  gold UNSUPPORTED findings still present : {len(gold_remaining)}")
print(f"  NEW unsupported (no gold counterpart)  : {len(new_uns)}")
print(f"  per-article post-repair unsupported    : {dict(by_art)}")

# uncertain items untouched by patches
rep = {r["tag"]: r for r in json.loads((B / "APPLICATION-REPORT.json").read_text())}
unc = gold["articles"]["FORM-1.3-R2"]["uncertain_findings"]
unc_touched = []
for u in unc:
    touched = any(u["span"] in a["old"] or a["old"] in u["span"] for a in rep["r2"]["applied"])
    unc_touched.append({"span": u["span"], "patched": touched})
    print(f'  gold UNCERTAIN "{u["span"]}" patched={touched}')

res = {"method": "post-repair re-audit, identical modular instrument, patched articles",
       "commitments": len(arb),
       "verdicts": dict(collections.Counter(a["arbitrated_verdict"] for a in arb)),
       "post_repair_unsupported_total": len(uns),
       "post_repair_unsupported_per_article": dict(by_art),
       "gold_unsupported_remaining": len(gold_remaining),
       "gold_unsupported_remaining_detail": gold_remaining,
       "new_unsupported": len(new_uns), "new_unsupported_detail": new_uns,
       "gold_uncertain_patched": [u for u in unc_touched if u["patched"]],
       "gold_uncertain_checks": unc_touched}
(W / "POSTAUDIT-SCORING.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
print("\nWritten POSTAUDIT-SCORING.json")
