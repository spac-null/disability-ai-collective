"""Metrics for the Crip Minds gold set: decisions, error directions, error table.

Decision rules, fixed in advance and never fitted on Crip Minds labels:
  FactCG / MiniCheck  support_prob >= 0.5 -> SUPPORTED   (published default threshold)
  LettuceDetect       any flagged span    -> UNSUPPORTED  (its own output contract)
  Baseline            validate_turn_support returns any error -> UNSUPPORTED

Gold label -> expectation under COMPLETE frozen evidence:
  SUPPORTED_DIRECT, SUPPORTED_RELATION, UNDER_CITED_BUT_SUPPORTED,
  INTERPRETATION_SUPPORTED_PREMISES        -> SUPPORTED
  UNSUPPORTED_RELATION, PERIPHERAL_UNSUPPORTED -> UNSUPPORTED

UNDER_CITED_BUT_SUPPORTED is reported separately under CITED_BASIS, where a refusal is
the contract-correct answer and not counted as an error.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cm_baseline as BL  # noqa: E402
import cm_evidence as E  # noqa: E402

B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
BASE = "/srv/data/cripminds-new-engine-v1/"

SUPPORTED_FAMILY = {"SUPPORTED_DIRECT", "SUPPORTED_RELATION",
                    "UNDER_CITED_BUT_SUPPORTED", "INTERPRETATION_SUPPORTED_PREMISES"}
UNSUPPORTED_FAMILY = {"UNSUPPORTED_RELATION", "PERIPHERAL_UNSUPPORTED"}

gold = json.load(open(B + "/gold/CRIP_MINDS_GOLD.json"))
cases = {c["case_id"]: c for c in gold["cases"]}


def load(path):
    p = B + "/systems/" + path
    return json.load(open(p)) if os.path.exists(p) else None


factcg = load("FACTCG_GOLD.json")
factcg_fix = load("FACTCG_GOLD_CHUNKFIX.json")
minicheck = load("MINICHECK_GOLD.json")
lettuce = load("LETTUCEDETECT_GOLD.json")


def prob_decisions(sysobj, cond):
    out = {}
    for r in sysobj["results"]:
        s = r["scores"].get(cond)
        if s:
            out[r["case_id"]] = ("SUPPORTED" if s["support_prob"] >= 0.5 else "UNSUPPORTED",
                                 round(s["support_prob"], 4))
    return out


def lettuce_decisions(cond):
    out = {}
    for r in lettuce["results"]:
        c = r["conditions"].get(cond)
        if c:
            out[r["case_id"]] = ("UNSUPPORTED" if c["example_flagged"] else "SUPPORTED",
                                 "%d spans" % c["n_spans"])
    return out


def baseline_decisions(cond):
    """Run the production checker on the same claims. LEDGER conditions only: the
    function takes fact ids, not raw prose, so a SOURCE condition has no honest mapping."""
    out = {}
    for cid, case in cases.items():
        facts_path = os.path.join(BASE + case["run_id"], "FINAL_EVIDENCE_MANIFEST.json")
        if not os.path.exists(facts_path):
            continue
        facts = (json.load(open(facts_path)) or {}).get("facts") or {}
        if not facts:
            continue
        if cond == "context_LEDGER_CITED_BASIS":
            ids = case.get("cited_fact_ids") or []
            if not ids:
                continue
        else:
            ids = list(facts.keys())
        res = BL.check(case["claim_text"], ids, facts)
        out[cid] = (res["decision"], "%d err" % res["n_errors"])
    return out


SYSTEMS = {}
for name, obj in [("FACTCG_as_documented", factcg), ("FACTCG_chunkfix", factcg_fix),
                  ("MINICHECK", minicheck)]:
    if obj:
        SYSTEMS[name] = {cond: prob_decisions(obj, cond)
                         for cond in ["context_SOURCE_CITED_BASIS", "context_SOURCE_COMPLETE",
                                      "context_LEDGER_CITED_BASIS", "context_LEDGER_COMPLETE"]}
if lettuce:
    SYSTEMS["LETTUCEDETECT"] = {cond: lettuce_decisions(cond)
                                for cond in ["context_SOURCE_CITED_BASIS", "context_SOURCE_COMPLETE",
                                             "context_LEDGER_CITED_BASIS", "context_LEDGER_COMPLETE"]}
SYSTEMS["BASELINE_validate_turn_support"] = {
    "context_LEDGER_CITED_BASIS": baseline_decisions("context_LEDGER_CITED_BASIS"),
    "context_LEDGER_COMPLETE": baseline_decisions("context_LEDGER_COMPLETE"),
}

report = {"decision_rules": __doc__, "systems": {}}
errors_table = []

for sysname, conds in SYSTEMS.items():
    entry = {}
    for cond, decisions in conds.items():
        if not decisions:
            continue
        by_class = collections.defaultdict(lambda: collections.Counter())
        by_type = collections.defaultdict(lambda: collections.Counter())
        tp = tn = fp = fn = 0
        for cid, (dec, detail) in sorted(decisions.items()):
            case = cases[cid]
            label = case["gold_label"]
            expect = "SUPPORTED" if label in SUPPORTED_FAMILY else "UNSUPPORTED"
            # under-cited: refusal on the cited basis is contract-correct, not an error
            exempt = (label == "UNDER_CITED_BUT_SUPPORTED" and cond.endswith("CITED_BASIS"))
            ok = (dec == expect)
            by_class[label]["n"] += 1
            by_class[label]["correct" if ok else "wrong"] += 1
            if exempt:
                by_class[label]["exempt_cited_basis_refusal"] += 1
            if not exempt:
                by_type[case["failure_type"]]["n"] += 1
                by_type[case["failure_type"]]["correct" if ok else "wrong"] += 1
                if expect == "SUPPORTED":
                    if ok:
                        tp += 1
                    else:
                        fn += 1
                        by_class[label]["FALSE_UNSUPPORTED"] += 1
                else:
                    if ok:
                        tn += 1
                    else:
                        fp += 1
                        by_class[label]["FALSE_SUPPORTED"] += 1
            if not ok and not exempt:
                errors_table.append({
                    "system": sysname, "condition": cond, "case_id": cid,
                    "article": case["article_key"], "run_id": case["run_id"],
                    "gold_label": label, "failure_type": case["failure_type"],
                    "claim": case["claim_text"][:220],
                    "evidence_summary": (case.get("gold_evidence") or "")[:220],
                    "raw": detail, "decision": dec,
                    "direction": "FALSE_UNSUPPORTED" if expect == "SUPPORTED" else "FALSE_SUPPORTED",
                })
        sens = tp / (tp + fn) if (tp + fn) else None
        spec = tn / (tn + fp) if (tn + fp) else None
        entry[cond] = {
            "n_scored": tp + tn + fp + fn,
            "supported_recall": round(sens, 3) if sens is not None else None,
            "unsupported_recall": round(spec, 3) if spec is not None else None,
            "balanced_accuracy": round((sens + spec) / 2, 3) if (sens is not None and spec is not None) else None,
            "FALSE_SUPPORTED": fp, "FALSE_UNSUPPORTED": fn,
            "by_class": {k: dict(v) for k, v in by_class.items()},
            "by_failure_type": {k: dict(v) for k, v in by_type.items()},
        }
    report["systems"][sysname] = entry

with open(B + "/analysis/METRICS.json", "w") as fh:
    json.dump(report, fh, indent=1)
with open(B + "/analysis/ERRORS.json", "w") as fh:
    json.dump(errors_table, fh, indent=1)

HEAD = "context_SOURCE_COMPLETE"
print("=" * 96)
print("HEADLINE - condition %s (complete frozen evidence, source prose)" % HEAD)
print("%-34s %6s %8s %8s %8s %8s" % ("system", "n", "supp_rec", "unsup_rec", "balAcc", "FS/FU"))
for s, e in report["systems"].items():
    d = e.get(HEAD)
    if not d:
        print("%-34s   (not applicable to this condition)" % s)
        continue
    print("%-34s %6d %8s %8s %8s %4d/%-4d" % (
        s, d["n_scored"], d["supported_recall"], d["unsupported_recall"],
        d["balanced_accuracy"], d["FALSE_SUPPORTED"], d["FALSE_UNSUPPORTED"]))

print()
print("LEDGER_COMPLETE (fact propositions) - includes the production baseline")
for s, e in report["systems"].items():
    d = e.get("context_LEDGER_COMPLETE")
    if d:
        print("%-34s n=%-3d balAcc=%-6s FS=%-3d FU=%-3d" % (
            s, d["n_scored"], d["balanced_accuracy"], d["FALSE_SUPPORTED"], d["FALSE_UNSUPPORTED"]))

print()
print("wrote METRICS.json and ERRORS.json ; total wrong decisions logged:", len(errors_table))
