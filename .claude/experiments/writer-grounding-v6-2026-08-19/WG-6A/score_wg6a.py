#!/usr/bin/env python3
"""WG-6A scorer. Gold->parent mapping copied VERBATIM from WG-4's score_wg4.py
(itself verbatim from WG-3) so it cannot be retuned after seeing arbitration."""
import json, collections
from pathlib import Path

W = Path(__file__).resolve().parent
I = W / "inputs"
TAGS = {"FORM-1.3": "form1-3", "FORM-1.3-R2": "r2", "FORM-1.3-R3": "r3"}

def norm(s):
    return ' '.join((s or '').lower().replace('’', "'").replace('—', '-').replace('–', '-').split())

gold = json.loads((I / "gold-ledger-V2.1-FROZEN.json").read_text())
findings = {f["id"]: (art, f) for art, a in gold["articles"].items() for f in a["unsupported_findings"]}
ex = {t: {p["ID"]: p for p in (lambda d: d["propositions"] if isinstance(d, dict) else d)(
      json.loads((I / f"{t}-extract-raw.json").read_text()))} for t in TAGS.values()}

# ---- VERBATIM mapping rule -------------------------------------------------
gmap = {}
for gid, (art, f) in findings.items():
    tag = TAGS[art]; gs = norm(f["span"]); gw = set(gs.split()); c = []
    for pid, p in ex[tag].items():
        ps = norm(p.get("EXACT_SPAN", ""))
        if ps and (ps in gs or gs in ps or len(gw & set(ps.split())) >= max(3, int(.4 * len(gw)))):
            c.append(pid)
    gmap[gid] = (tag, c)

arb = json.loads((W / "ARBITRATION.json").read_text())["arbitrated"]
by_parent = collections.defaultdict(list)
for a in arb:
    by_parent[(a["tag"], a["parent"])].append(a)

claimed = {(t, p) for gid, (t, c) in gmap.items() for p in c}
uns = [a for a in arb if a["arbitrated_verdict"] == "UNSUPPORTED"]

print("=" * 74); print("WG-6A MODULAR ARBITRATION vs GOLD V2.1")
tp, fn = [], []
for gid, (tag, cands) in sorted(gmap.items()):
    hits = [a for p in cands for a in by_parent[(tag, p)] if a["arbitrated_verdict"] == "UNSUPPORTED"]
    (tp if hits else fn).append(gid)
    print(f"  {'FOUND ' if hits else 'MISSED'} {gid} [{tag}] parents={cands}")
    for a in hits:
        print(f"      {a['commitment_id']} [{a['commitment_type']}] owner={a['owner']} "
              f"class={a['class']} proof={a['wg4b_proof_type']}")
        print(f"      -> {a['proposition'][:100]}")

fps = [a for a in uns if (a["tag"], a["parent"]) not in claimed]
print(f"\n  TP {len(tp)}   FN {len(fn)} {fn}   FP {len(fps)}")
for a in fps:
    print(f"    FP [{a['tag']}/{a['parent']}] {a['commitment_id']} owner={a['owner']} span=\"{a['parent_span']}\"")
recall = len(tp) / 8
precision = len(tp) / max(1, len(tp) + len(fps))
print(f"  recall {recall:.3f}   precision {precision:.3f}")

# ---- named controls -------------------------------------------------------
print("\n" + "=" * 74); print("NAMED CONTROLS")
controls = {}
for label, tag, pid, must in (("G13-04", "form1-3", "P22", "UNSUPPORTED"),
                              ("GR2-02", "r2", "P21", "UNSUPPORTED"),
                              ("R3-control", "r3", "P29", "SUPPORTED")):
    recs = by_parent[(tag, pid)]
    v = [r["arbitrated_verdict"] for r in recs]
    ok = must in v and (must == "UNSUPPORTED" or "UNSUPPORTED" not in v)
    controls[label] = {"tag": tag, "parent": pid, "required": must, "verdicts": v,
                       "owner": [r["owner"] for r in recs], "class": [r["class"] for r in recs],
                       "proof_type": [r["wg4b_proof_type"] for r in recs],
                       "scope": [r["wg4b_scope"] for r in recs], "pass": ok}
    print(f"  {label:11s} [{tag}/{pid}] required={must:12s} got={v} owner={controls[label]['owner']} "
          f"proof={controls[label]['proof_type']}  {'PASS' if ok else 'FAIL'}")
    if controls[label]["scope"][0]:
        print(f"      scope: {str(controls[label]['scope'][0])[:150]}")

# ---- interpretation integrity --------------------------------------------
print("\n" + "=" * 74); print("INTERPRETATION / UNCERTAIN INTEGRITY")
flipped_interp = [a for a in arb if a["wg4a_status"] == "INTERPRETATION"
                  and a["arbitrated_verdict"] == "UNSUPPORTED"]
print(f"  WG-4A INTERPRETATION commitments flipped to UNSUPPORTED by arbitration: {len(flipped_interp)}")
for a in flipped_interp:
    isgold = [g for g, (t, c) in gmap.items() if t == a["tag"] and a["parent"] in c]
    print(f"    {a['tag']}/{a['parent']} {a['commitment_id']} gold={isgold or 'NONE -> FALSE POSITIVE'}")
    print(f'        span: "{a["parent_span"]}"')

recl = {"G13-03": ("FORM-1.3", "It is a two-sided obligation"),
        "GR2-03": ("FORM-1.3-R2", "obligation running two ways"),
        "GR3-02": ("FORM-1.3-R3", "second obligation is harder")}
print("\n  owner-calibrated reclassified interpretations (must NOT be UNSUPPORTED):")
print("    NOTE: the verbatim mapping rule was designed for the SHORT gold unsupported")
print("    spans. Applied to these long, generic reclassified spans it over-matches and")
print("    pulls in parents belonging to OTHER gold findings. The authoritative column is")
print("    GOLD-DISJOINT: parents matched by this reclassified span and claimed by NO gold")
print("    unsupported finding. An UNSUPPORTED there would be a genuine violation.")
recl_out = []
for gid, entry in [(r["id"], r) for r in gold["reclassified_to_interpretation_v2"]]:
    tag = TAGS[entry["article"]]; gs = norm(entry["span"]); gw = set(gs.split())
    cands = [pid for pid, pp in ex[tag].items()
             if norm(pp.get("EXACT_SPAN", "")) and
             (norm(pp["EXACT_SPAN"]) in gs or gs in norm(pp["EXACT_SPAN"]) or
              len(gw & set(norm(pp["EXACT_SPAN"]).split())) >= max(3, int(.4 * len(gw))))]
    loose = [a["arbitrated_verdict"] for pid in cands for a in by_parent[(tag, pid)]]
    disjoint = [pid for pid in cands if (tag, pid) not in claimed]
    dv = [a["arbitrated_verdict"] for pid in disjoint for a in by_parent[(tag, pid)]]
    bleed = [(pid, g) for pid in cands if (tag, pid) in claimed
             for g in gmap if gmap[g][0] == tag and pid in gmap[g][1]]
    ok = "UNSUPPORTED" not in dv
    recl_out.append({"id": gid, "tag": tag, "loose_parents": cands, "loose_verdicts": loose,
                     "gold_disjoint_parents": disjoint, "gold_disjoint_verdicts": dv,
                     "overmatched_into_other_gold_findings": sorted({g for _, g in bleed}),
                     "pass": ok})
    print(f"    {gid} [{tag}] loose={loose}")
    print(f"        GOLD-DISJOINT parents={disjoint} verdicts={dv}  {'PASS' if ok else 'FAIL'}")
    if bleed:
        print(f"        over-matched into other gold findings: {sorted({g for _, g in bleed})}")

print("\n  gold UNCERTAIN items (must NOT be UNSUPPORTED -> cannot become repair targets):")
unc_out = []
for u in gold["articles"]["FORM-1.3-R2"]["uncertain_findings"]:
    gs = norm(u["span"]); gw = set(gs.split())
    cands = [pid for pid, p in ex["r2"].items()
             if norm(p.get("EXACT_SPAN", "")) and
             (norm(p["EXACT_SPAN"]) in gs or gs in norm(p["EXACT_SPAN"]) or
              len(gw & set(norm(p["EXACT_SPAN"]).split())) >= max(3, int(.4 * len(gw))))]
    v = [a["arbitrated_verdict"] for p in cands for a in by_parent[("r2", p)]]
    ok = "UNSUPPORTED" not in v
    unc_out.append({"span": u["span"], "parents": cands, "verdicts": v, "pass": ok})
    print(f'    "{u["span"]}" parents={cands} verdicts={v}  {"PASS" if ok else "FAIL"}')

decision = ("A — MODULAR_ARBITRATION_READY" if len(tp) == 8 and not fps and controls["R3-control"]["pass"]
            else "B — ARBITRATION_RECALL_REGRESSION" if fn
            else "C — ARBITRATION_PRECISION_GAP")
print("\n" + "=" * 74); print(f"DECISION: {decision}")

(W / "WG6A-SCORING.json").write_text(json.dumps({
    "method": "REUSE_RESCORE_NO_MODEL_CALLS",
    "mapping_rule": "verbatim from score_wg4.py / WG-3",
    "parents": 236, "commitments": len(arb),
    "arbitrated_verdicts": dict(collections.Counter(a["arbitrated_verdict"] for a in arb)),
    "tp": len(tp), "fp": len(fps), "fn": len(fn), "recall": recall, "precision": precision,
    "caught": sorted(tp), "missed": fn,
    "false_positives": fps,
    "controls": controls,
    "interpretation_flipped_to_unsupported": len(flipped_interp),
    "uncertain_checks": unc_out,
    "reclassified_interpretation_checks": recl_out,
    "unsupported_commitments": [{k: a[k] for k in ("tag", "parent", "commitment_id",
                                 "commitment_type", "owner", "class", "wg4b_proof_type",
                                 "parent_span", "proposition")} for a in uns],
    "decision": decision,
}, indent=2, ensure_ascii=False))
print("Written WG6A-SCORING.json")
