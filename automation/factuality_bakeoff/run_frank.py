"""External sanity check on FRANK (MIT, published validation/test split).

Protocol, fixed before any test scoring:
  * label: Factuality == 1.0 -> supported (1), otherwise unsupported (0).
  * claim unit: each summary sentence is scored against the article, and the summary's
    score is the MIN over its sentences -- a summary is factual only if every sentence is.
    This matches FRANK's own definition and MiniCheck's documented sentence-level use.
  * validation split: adapter debugging and ONE global threshold only.
  * test split: scored exactly once, at the published default 0.5 and at that one global
    threshold. No per-category and no per-dataset tuning.

Answers "does this implementation behave like a factuality system", not "should Crip
Minds deploy it" (§8).
"""
import argparse
import collections
import json
import os
import random
import time

import nltk

B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
FRANK = B + "/repos/frank/data"
FAMILIES = ["Semantic_Frame_Errors", "Discourse_Errors", "Content_Verifiability_Errors"]


def load_records(split):
    bench = json.load(open(FRANK + "/benchmark_data.json"))
    anns = {(a["hash"], a["model_name"]): a for a in json.load(open(FRANK + "/human_annotations.json"))}
    out = []
    for r in bench:
        a = anns.get((r["hash"], r["model_name"]))
        if not a or a.get("split") != split:
            continue
        fact = a.get("Factuality")
        if fact is None:
            continue
        sents = [s.strip() for s in nltk.sent_tokenize(r["summary"] or "") if s.strip()]
        if not sents or not (r.get("article") or "").strip():
            continue
        out.append({
            "hash": r["hash"], "model_name": r["model_name"],
            "article": r["article"], "sentences": sents,
            "label": 1 if float(fact) == 1.0 else 0,
            "families": {f: a.get(f) for f in FAMILIES},
        })
    return out


def metrics(pairs, thr):
    """pairs: list of (label, score). Positive class = supported."""
    tp = sum(1 for l, s in pairs if l == 1 and s >= thr)
    fn = sum(1 for l, s in pairs if l == 1 and s < thr)
    tn = sum(1 for l, s in pairs if l == 0 and s < thr)
    fp = sum(1 for l, s in pairs if l == 0 and s >= thr)
    rec = tp / (tp + fn) if tp + fn else None
    spec = tn / (tn + fp) if tn + fp else None
    prec = tp / (tp + fp) if tp + fp else None
    f1 = (2 * prec * rec / (prec + rec)) if (prec and rec) else None
    return {
        "n": len(pairs), "threshold": thr,
        "accuracy": round((tp + tn) / len(pairs), 4) if pairs else None,
        "balanced_accuracy": round((rec + spec) / 2, 4) if (rec is not None and spec is not None) else None,
        "precision": round(prec, 4) if prec else None,
        "recall": round(rec, 4) if rec else None,
        "f1": round(f1, 4) if f1 else None,
        # FALSE_SUPPORTED: unfactual summary scored as supported (permissive error)
        "FALSE_SUPPORTED": fp,
        # FALSE_UNSUPPORTED: factual summary scored as unsupported (mierenneuker error)
        "FALSE_UNSUPPORTED": fn,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True, choices=["factcg", "minicheck"])
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0, help="bounded sample per split (0=all)")
    ap.add_argument("--seed", type=int, default=20260919)
    args = ap.parse_args()

    if args.system == "factcg":
        from factcg import FactCGScore
        sc = FactCGScore(model_name="microsoft/deberta-v3-large",
                         batch_size=args.batch_size, verbose=False, use_hf_ckpt=True)

        def score(ctxs, claims):
            return sc.score(contexts=list(ctxs), claims=list(claims))
    else:
        from minicheck.minicheck import MiniCheck
        sc = MiniCheck(model_name="flan-t5-large", cache_dir=B + "/models/hf/hub")

        def score(ctxs, claims):
            _, raw, _, _ = sc.score(docs=list(ctxs), claims=list(claims))
            return list(raw)

    out = {"system": args.system, "protocol": __doc__, "splits": {}}

    for split in ("valid", "test"):
        recs = load_records(split)
        if args.limit and len(recs) > args.limit:
            random.Random(args.seed).shuffle(recs)
            recs = recs[:args.limit]
            out.setdefault("sampling", {})[split] = {
                "bounded_sample": args.limit, "seed": args.seed,
                "note": "bounded for runtime; sampled before any scoring, fixed seed"}
        flat_ctx, flat_cl, owner = [], [], []
        for i, r in enumerate(recs):
            for s in r["sentences"]:
                flat_ctx.append(r["article"])
                flat_cl.append(s)
                owner.append(i)

        t0 = time.time()
        scores = []
        for i in range(0, len(flat_ctx), args.batch_size):
            scores.extend(score(flat_ctx[i:i + args.batch_size], flat_cl[i:i + args.batch_size]))
            if i % (args.batch_size * 20) == 0:
                print("  %s %s %d/%d" % (args.system, split, i, len(flat_ctx)), flush=True)
        elapsed = time.time() - t0

        agg = collections.defaultdict(list)
        for o, s in zip(owner, scores):
            agg[o].append(float(s))
        pairs = [(recs[i]["label"], min(v)) for i, v in agg.items()]

        entry = {
            "n_records": len(recs), "n_sentence_scorings": len(flat_ctx),
            "elapsed_s": round(elapsed, 1),
            "mean_latency_per_sentence_s": round(elapsed / max(1, len(flat_ctx)), 4),
            "label_balance": {"supported": sum(1 for l, _ in pairs if l == 1),
                              "unsupported": sum(1 for l, _ in pairs if l == 0)},
            "at_default_0.5": metrics(pairs, 0.5),
        }

        if split == "valid":
            best, best_thr = None, 0.5
            for k in range(5, 100, 5):
                thr = k / 100.0
                m = metrics(pairs, thr)
                if m["balanced_accuracy"] and (best is None or m["balanced_accuracy"] > best):
                    best, best_thr = m["balanced_accuracy"], thr
            out["global_dev_threshold"] = best_thr
            entry["threshold_search"] = {"chosen": best_thr, "val_balanced_accuracy": best}
            print("  global dev threshold chosen on FRANK validation:", best_thr, flush=True)
        else:
            entry["at_global_dev_threshold"] = metrics(pairs, out.get("global_dev_threshold", 0.5))
            # category breakdown over unsupported records only
            fam = {}
            for f in FAMILIES:
                sub = [(recs[i]["label"], min(v)) for i, v in agg.items()
                       if recs[i]["label"] == 0 and recs[i]["families"].get(f) is not None
                       and float(recs[i]["families"][f]) < 1.0]
                if sub:
                    caught = sum(1 for _, s in sub if s < 0.5)
                    fam[f] = {"n_unsupported_with_this_family": len(sub),
                              "caught_at_0.5": caught,
                              "missed_at_0.5": len(sub) - caught}
            entry["by_error_family_default_threshold"] = fam

        out["splits"][split] = entry
        print(split, json.dumps(entry["at_default_0.5"]), flush=True)

    dest = B + "/external/FRANK_%s.json" % args.system.upper()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", dest)


if __name__ == "__main__":
    main()
