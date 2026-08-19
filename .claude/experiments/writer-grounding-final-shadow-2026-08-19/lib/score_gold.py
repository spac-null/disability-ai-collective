#!/usr/bin/env python3
"""FINAL REPLAY GATE 1 — score the PRE-REPAIR detector against Gold V2.1.
Runs ONLY after the pre-phase outputs are frozen. Gold->parent mapping copied
VERBATIM from WG-6A/score_wg6a.py (itself verbatim from score_wg4.py / WG-3)."""
import json, collections
from pathlib import Path

R = Path(__file__).resolve().parent.parent
I = R / "inputs"
TAGS = {"FORM-1.3": "form1-3", "FORM-1.3-R2": "r2", "FORM-1.3-R3": "r3"}


def norm(s):
    return ' '.join((s or '').lower().replace('’', "'").replace('—', '-').replace('–', '-').split())


gold = json.loads((I / "gold-ledger-V2.1-FROZEN.json").read_text())
findings = {f["id"]: (art, f) for art, a in gold["articles"].items() for f in a["unsupported_findings"]}
ex = {t: {p["ID"]: p for p in (lambda d: d["propositions"] if isinstance(d, dict) else d)(
      json.loads((R / "pre" / f"{t}-extract-raw.json").read_text()))} for t in TAGS.values()}

gmap = {}
for gid, (art, f) in findings.items():
    tag = TAGS[art]; gs = norm(f["span"]); gw = set(gs.split()); c = []
    for pid, p in ex[tag].items():
        ps = norm(p.get("EXACT_SPAN", ""))
        if ps and (ps in gs or gs in ps or len(gw & set(ps.split())) >= max(3, int(.4 * len(gw)))):
            c.append(pid)
    gmap[gid] = (tag, c)

arb = json.loads((R / "score" / "pre-ARBITRATION.json").read_text())["arbitrated"]
by_parent = collections.defaultdict(list)
for a in arb:
    by_parent[(a["tag"], a["parent"])].append(a)
claimed = {(t, p) for gid, (t, c) in gmap.items() for p in c}
uns = [a for a in arb if a["arbitrated_verdict"] == "UNSUPPORTED"]

print("=" * 78); print("GATE 1 — PRE-REPAIR DETECTOR vs GOLD V2.1")
tp, fn = [], []
for gid, (tag, cands) in sorted(gmap.items()):
    hits = [a for p in cands for a in by_parent[(tag, p)] if a["arbitrated_verdict"] == "UNSUPPORTED"]
    (tp if hits else fn).append(gid)
    print(f"  {'FOUND ' if hits else 'MISSED'} {gid} [{tag}] parents={cands}")
    for a in hits:
        print(f"      {a['commitment_id']} [{a['commitment_type']}] owner={a['owner']} path={a['routing_path']}")
        print(f"      -> {str(a['proposition'])[:110]}")

fps = [a for a in uns if (a["tag"], a["parent"]) not in claimed]
recall = len(tp) / 8
precision = len(tp) / max(1, len(tp) + len(fps))
print(f"\n  TP {len(tp)}  FN {len(fn)} {fn}  FP {len(fps)}   recall {recall:.3f}  precision {precision:.3f}")
for a in fps:
    print(f"    FP [{a['tag']}/{a['parent']}] {a['commitment_id']} [{a['commitment_type']}] owner={a['owner']}")
    print(f"       span      : \"{a['parent_span']}\"")
    print(f"       commitment: {a['proposition']}")
    print(f"       reason    : {str(a.get('reason'))[:260]}")

controls = {}
for label, tag, pid, must in (("G13-04", "form1-3", "P22", "UNSUPPORTED"),
                              ("GR2-02", "r2", "P21", "UNSUPPORTED"),
                              ("R3-control", "r3", "P29", "SUPPORTED")):
    recs = by_parent[(tag, pid)]
    v = [r["arbitrated_verdict"] for r in recs]
    ok = must in v and (must == "UNSUPPORTED" or "UNSUPPORTED" not in v)
    controls[label] = {"tag": tag, "parent": pid, "required": must, "got": v,
                       "owner": [r["owner"] for r in recs],
                       "proof_type": [r["wg4b_proof_type"] for r in recs],
                       "spans": sorted({r["parent_span"] for r in recs}), "pass": ok}
    print(f"  {label:11s} [{tag}/{pid}] required={must:12s} got={v} proof={controls[label]['proof_type']}"
          f"  {'PASS' if ok else 'FAIL'}")
print("  NOTE: control parent IDs are the WG-6 extraction's numbering. Under a fresh extraction the")
print("        same claim may carry a different ID; the span column is the authoritative check.")

# reclassified interpretations and uncertain items must not be repair targets
recl = []
for entry in gold["reclassified_to_interpretation_v2"]:
    tag = TAGS[entry["article"]]; gs = norm(entry["span"]); gw = set(gs.split())
    cands = [pid for pid, pp in ex[tag].items()
             if norm(pp.get("EXACT_SPAN", "")) and
             (norm(pp["EXACT_SPAN"]) in gs or gs in norm(pp["EXACT_SPAN"]) or
              len(gw & set(norm(pp["EXACT_SPAN"]).split())) >= max(3, int(.4 * len(gw))))]
    disjoint = [pid for pid in cands if (tag, pid) not in claimed]
    dv = [a["arbitrated_verdict"] for pid in disjoint for a in by_parent[(tag, pid)]]
    recl.append({"id": entry["id"], "tag": tag, "gold_disjoint_parents": disjoint,
                 "gold_disjoint_verdicts": dv, "pass": "UNSUPPORTED" not in dv})
    print(f"  reclassified {entry['id']} GOLD-DISJOINT parents={disjoint} verdicts={dv} "
          f"{'PASS' if 'UNSUPPORTED' not in dv else 'FAIL'}")

unc = []
for u in gold["articles"]["FORM-1.3-R2"]["uncertain_findings"]:
    gs = norm(u["span"]); gw = set(gs.split())
    cands = [pid for pid, p in ex["r2"].items()
             if norm(p.get("EXACT_SPAN", "")) and
             (norm(p["EXACT_SPAN"]) in gs or gs in norm(p["EXACT_SPAN"]) or
              len(gw & set(norm(p["EXACT_SPAN"]).split())) >= max(3, int(.4 * len(gw))))]
    v = [a["arbitrated_verdict"] for p in cands for a in by_parent[("r2", p)]]
    unc.append({"span": u["span"], "parents": cands, "verdicts": v, "pass": "UNSUPPORTED" not in v})
    print(f'  uncertain "{u["span"]}" parents={cands} verdicts={v} {"PASS" if "UNSUPPORTED" not in v else "FAIL"}')

gate1 = len(tp) == 8 and not fn
print("\n" + "=" * 78)
print(f"GATE 1 (TP=8, FN=0): {'PASS' if gate1 else 'FAIL'}")
if fps:
    print(f"  FP {len(fps)} > 0 -> independent adjudication REQUIRED before repair (pre-registered).")

(R / "score" / "GATE1-PRE-REPAIR-SCORING.json").write_text(json.dumps({
    "gate": "GATE 1 — pre-repair detector vs Gold V2.1",
    "mapping_rule": "verbatim from WG-6A/score_wg6a.py",
    "commitments": len(arb),
    "verdicts": dict(collections.Counter(a["arbitrated_verdict"] for a in arb)),
    "tp": len(tp), "fp": len(fps), "fn": len(fn), "recall": recall, "precision": precision,
    "caught": sorted(tp), "missed": fn,
    "gold_parent_map": {k: v for k, v in gmap.items()},
    "false_positives": fps, "controls": controls,
    "reclassified_interpretation_checks": recl, "uncertain_checks": unc,
    "unsupported_commitments": [{k: a[k] for k in ("tag", "parent", "commitment_id",
        "commitment_type", "owner", "class", "routing_path", "wg4b_proof_type",
        "parent_span", "proposition", "reason")} for a in uns],
    "gate1_pass": gate1,
}, indent=2, ensure_ascii=False))
print("Written score/GATE1-PRE-REPAIR-SCORING.json")
