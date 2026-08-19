#!/usr/bin/env python3
"""WG-6N N1 RE-SCORE. Runs the corrected router over BOTH frozen conditions.

  (A) original WG-6A condition  — pre-repair components, must not regress
  (B) WG-6B post-repair condition — must surface every suppressed WG-4B verdict

Gold->parent mapping is copied VERBATIM from WG-6A/score_wg6a.py (itself
verbatim from score_wg4.py / WG-3) so it cannot be retuned. No model calls.
"""
import json, collections
from pathlib import Path
from arbitrate_v2 import arbitrate, load_condition

W = Path(__file__).resolve().parent
V6 = W.parent
I = V6 / "WG-6A" / "inputs"
POST = V6 / "WG-6B" / "postaudit"
TAGS = {"FORM-1.3": "form1-3", "FORM-1.3-R2": "r2", "FORM-1.3-R3": "r3"}


def norm(s):
    return ' '.join((s or '').lower().replace('’', "'").replace('—', '-').replace('–', '-').split())


gold = json.loads((I / "gold-ledger-V2.1-FROZEN.json").read_text())
findings = {f["id"]: (art, f) for art, a in gold["articles"].items() for f in a["unsupported_findings"]}

# ---------------------------------------------------------------- condition A
arbA, diagA, exA = [], {}, {}
for tag in TAGS.values():
    A, B, E = load_condition(I, tag, f"wg4a-{tag}-decomp-raw.json",
                             f"wg4b-{tag}-negproof-raw.json", f"{tag}-extract-raw.json")
    exA[tag] = E
    u, d = arbitrate(tag, A, B, E)
    arbA += u
    diagA[tag] = d

# ---- VERBATIM mapping rule (unchanged) --------------------------------------
gmap = {}
for gid, (art, f) in findings.items():
    tag = TAGS[art]; gs = norm(f["span"]); gw = set(gs.split()); c = []
    for pid, p in exA[tag].items():
        ps = norm(p.get("EXACT_SPAN", ""))
        if ps and (ps in gs or gs in ps or len(gw & set(ps.split())) >= max(3, int(.4 * len(gw)))):
            c.append(pid)
    gmap[gid] = (tag, c)

by_parent = collections.defaultdict(list)
for a in arbA:
    by_parent[(a["tag"], a["parent"])].append(a)
claimed = {(t, p) for gid, (t, c) in gmap.items() for p in c}
unsA = [a for a in arbA if a["arbitrated_verdict"] == "UNSUPPORTED"]

print("=" * 76)
print("CONDITION A — ORIGINAL WG-6A CONDITION, CORRECTED ROUTER")
tp, fn = [], []
for gid, (tag, cands) in sorted(gmap.items()):
    hits = [a for p in cands for a in by_parent[(tag, p)] if a["arbitrated_verdict"] == "UNSUPPORTED"]
    (tp if hits else fn).append(gid)
    print(f"  {'FOUND ' if hits else 'MISSED'} {gid} [{tag}] parents={cands}")
    for a in hits:
        print(f"      {a['commitment_id']} [{a['commitment_type']}] owner={a['owner']} "
              f"path={a['routing_path']} proof={a['wg4b_proof_type']}")

fps = [a for a in unsA if (a["tag"], a["parent"]) not in claimed]
recall = len(tp) / 8
precision = len(tp) / max(1, len(tp) + len(fps))
print(f"\n  TP {len(tp)}  FN {len(fn)} {fn}  FP {len(fps)}   recall {recall:.3f}  precision {precision:.3f}")
for a in fps:
    print(f"    FP [{a['tag']}/{a['parent']}] {a['commitment_id']} owner={a['owner']} span=\"{a['parent_span']}\"")

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
                       "routing_path": [r["routing_path"] for r in recs], "pass": ok}
    print(f"  {label:11s} [{tag}/{pid}] required={must:12s} got={v} proof={controls[label]['proof_type']}"
          f"  {'PASS' if ok else 'FAIL'}")

unroutedA = sum(len(d["unrouted_negatives"]) for d in diagA.values())
disagA = sum(len(d["proof_vs_verdict_disagreements"]) for d in diagA.values())
synthA = [u for d in diagA.values() for u in d["synthesised_units"]]
forbA = sorted({f for d in diagA.values() for f in d["forbidden_fields_read"]})
print(f"  unrouted {unroutedA}  disagreements {disagA}  synthesised {len(synthA)}  forbidden_read {forbA}")

# ---- regression check against the frozen WG-6A record -----------------------
old = json.loads((V6 / "WG-6A" / "WG6A-SCORING.json").read_text())
oldset = {(a["tag"], a["parent"], a["commitment_id"]) for a in old["unsupported_commitments"]}
newset = {(a["tag"], a["parent"], a["commitment_id"]) for a in unsA}
regression = {
    "old_tp": old["tp"], "old_fp": old["fp"], "old_fn": old["fn"],
    "new_tp": len(tp), "new_fp": len(fps), "new_fn": len(fn),
    "matrix_identical": (old["tp"], old["fp"], old["fn"]) == (len(tp), len(fps), len(fn)),
    "unsupported_set_identical": oldset == newset,
    "appeared": sorted(newset - oldset), "disappeared": sorted(oldset - newset),
}
print(f"  vs frozen WG-6A: matrix_identical={regression['matrix_identical']} "
      f"unsupported_set_identical={regression['unsupported_set_identical']} "
      f"appeared={regression['appeared']} disappeared={regression['disappeared']}")

# ---------------------------------------------------------------- condition B
print("\n" + "=" * 76)
print("CONDITION B — WG-6B POST-REPAIR CONDITION, CORRECTED ROUTER")
arbB, diagB, exB = [], {}, {}
for tag in TAGS.values():
    A, B, E = load_condition(POST, tag, f"{tag}-wg4a-raw.json",
                             f"{tag}-wg4b-raw.json", f"{tag}-extract-raw.json")
    exB[tag] = E
    u, d = arbitrate(tag, A, B, E)
    arbB += u
    diagB[tag] = d

unsB = [a for a in arbB if a["arbitrated_verdict"] == "UNSUPPORTED"]
oldpost = json.loads((POST / "POSTAUDIT-SCORING.json").read_text())
old_supp = {(u["tag"], u["parent"]) for u in oldpost["arbitration_unrouted"]}
oldB = {(a["tag"], a["parent"], a["commitment_id"])
        for a in oldpost["new_unsupported_detail"] + oldpost["gold_unsupported_remaining_detail"]}
newB = {(a["tag"], a["parent"], a["commitment_id"]) for a in unsB}

unroutedB = sum(len(d["unrouted_negatives"]) for d in diagB.values())
synthB = [u for d in diagB.values() for u in d["synthesised_units"]]
print(f"  commitments {len(arbB)}  verdicts {dict(collections.Counter(a['arbitrated_verdict'] for a in arbB))}")
print(f"  unrouted {unroutedB}   synthesised WG-4B units {len(synthB)}")
for u in synthB:
    print(f"   SYNTHESISED [{u['tag']}/{u['parent']}] {u['commitment_id']} proof={u['wg4b_proof_type']} "
          f"-> {u['arbitrated_verdict']}")
    print(f"       span: \"{u['parent_span']}\"")
    print(f"       WG-4B negative claim: {u['proposition']}")
    for c in u["coexisting_wg4a_commitments"]:
        print(f"       kept with WG-4A: {c['commitment_id']} [{c['type']}] -> {c['kept_verdict']}")

print(f"\n  POST-REPAIR UNSUPPORTED under corrected router: {len(unsB)} (old router: {len(oldB)})")
for a in unsB:
    print(f"   [{a['tag']}/{a['parent']}] {a['commitment_id']} [{a['commitment_type']}] owner={a['owner']} "
          f"path={a['routing_path']}")
    print(f"       span: \"{a['parent_span']}\"")
    print(f"       commitment: {a['proposition']}")

recovered = sorted(newB - oldB)
print(f"\n  findings recovered by the fix (previously suppressed): {recovered}")
print(f"  findings lost by the fix (must be empty): {sorted(oldB - newB)}")

decision = ("A — ROUTING_GAP_CLOSED"
            if unroutedA == 0 and unroutedB == 0 and regression["matrix_identical"]
            and regression["unsupported_set_identical"] and not (oldB - newB)
            and all(c["pass"] for c in controls.values()) and not forbA
            else "B — ROUTING_STILL_INCOMPLETE")
print("\n" + "=" * 76); print(f"N1 DECISION: {decision}")

(W / "N1-RESCORE.json").write_text(json.dumps({
    "method": "REUSE_RESCORE_NO_MODEL_CALLS, corrected router v2",
    "router_change": "added P3 synthesised carrier; routing authority is WG-4B IN_SCOPE+NEGATIVE",
    "condition_A": {
        "tp": len(tp), "fp": len(fps), "fn": len(fn), "recall": recall, "precision": precision,
        "caught": sorted(tp), "missed": fn, "false_positives": fps,
        "controls": controls, "unrouted": unroutedA,
        "proof_vs_verdict_disagreements": disagA, "synthesised_units": len(synthA),
        "forbidden_fields_read": forbA,
        "regression_vs_frozen_WG6A": regression,
        "unsupported_commitments": [{k: a[k] for k in ("tag", "parent", "commitment_id",
            "commitment_type", "owner", "class", "routing_path", "wg4b_proof_type",
            "parent_span", "proposition")} for a in unsA],
    },
    "condition_B": {
        "commitments": len(arbB),
        "verdicts": dict(collections.Counter(a["arbitrated_verdict"] for a in arbB)),
        "unrouted": unroutedB,
        "synthesised_units": synthB,
        "post_repair_unsupported_total": len(unsB),
        "post_repair_unsupported": [{k: a[k] for k in ("tag", "parent", "commitment_id",
            "commitment_type", "owner", "class", "routing_path", "wg4b_proof_type",
            "parent_span", "proposition", "reason")} for a in unsB],
        "previously_suppressed_parents": sorted(old_supp),
        "recovered_by_fix": recovered,
        "lost_by_fix": sorted(oldB - newB),
    },
    "decision": decision,
}, indent=2, ensure_ascii=False))
print("Written N1-RESCORE.json")
