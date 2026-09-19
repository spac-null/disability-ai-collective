"""RAGTruth implicit_true sanity probe — compatibility check only, never a decider.

CONTAMINATION, stated first because it governs how these numbers may be read:
  * LettuceDetect's v2 model card documents training on RAGTruth.
  * MiniCheck's LLM-AggreFact benchmark incorporates RAGTruth converted to its format.
  * FactCG reports LLM-AggreFact results too.
So every system here may have seen this data. These numbers answer "does the
implementation behave sanely on RAGTruth's own distinctions", not "is it better".

THE DISTINCTION BEING PROBED
RAGTruth marks some annotated spans `implicit_true`: the information may be correct in
the world even though it is not established by the supplied context. Crip Minds must
never collapse that into "lie" or "factual error". The groups below are kept apart and
reported apart:

  SUPPORTED_BY_CONTEXT   sentence from a response with no annotated span
  IMPLICIT_TRUE          sentence whose annotated span(s) are ALL implicit_true
  UNSUPPORTED_BASELESS   annotated Baseless Info, not implicit_true
  CONTRADICTED           annotated Conflict, not implicit_true

A context-grounded checker is expected to score IMPLICIT_TRUE low, because it is not in
the context. The question worth asking is whether its scores separate IMPLICIT_TRUE from
CONTRADICTED at all — if they are indistinguishable, the checker cannot tell "absent" from
"false", and nothing downstream may treat its output as a truth claim.

Protocol: test split only; bounded sample per group with a fixed seed, drawn BEFORE any
scoring; published default threshold 0.5; no tuning; adapters unchanged.
"""
import argparse
import collections
import json
import os
import random
import re
import statistics
import time

B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
D = B + "/repos/RAGTruth/dataset"
GROUPS = ["SUPPORTED_BY_CONTEXT", "IMPLICIT_TRUE", "UNSUPPORTED_BASELESS", "CONTRADICTED"]


def sentences_with_offsets(text):
    out, idx = [], 0
    for part in re.split(r"(?<=[.!?])\s+", text or ""):
        if part.strip():
            start = text.find(part, idx)
            out.append((start, start + len(part), part.strip()))
            idx = start + len(part)
    return out


def build(seed, per_group):
    src = {}
    with open(D + "/source_info.jsonl") as fh:
        for line in fh:
            s = json.loads(line)
            src[s["source_id"]] = s
    pool = collections.defaultdict(list)

    with open(D + "/response.jsonl") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("split") != "test" or r.get("quality") != "good":
                continue
            s = src.get(r["source_id"])
            if not s:
                continue
            context = (s.get("source_info") or "")
            if isinstance(context, (dict, list)):
                context = json.dumps(context)
            context = context.strip()
            if not context:
                continue
            resp = r.get("response") or ""
            sents = sentences_with_offsets(resp)
            labels = r.get("labels") or []

            if not labels:
                for _, _, sent in sents:
                    if len(sent.split()) >= 6:
                        pool["SUPPORTED_BY_CONTEXT"].append(
                            {"context": context, "claim": sent, "task": s.get("task_type"),
                             "source_id": r["source_id"], "model": r.get("model")})
                continue

            # attach every annotated span to the sentence containing it
            per_sent = collections.defaultdict(list)
            for lb in labels:
                st, en = lb.get("start"), lb.get("end")
                if st is None or en is None:
                    continue
                for i, (a, b, _) in enumerate(sents):
                    if st < b and en > a:
                        per_sent[i].append(lb)
                        break
            for i, lbs in per_sent.items():
                sent = sents[i][2]
                if len(sent.split()) < 6:
                    continue
                impl = [l for l in lbs if l.get("implicit_true") is True]
                conflict = [l for l in lbs
                            if "Conflict" in (l.get("label_type") or "")
                            and l.get("implicit_true") is not True]
                baseless = [l for l in lbs
                            if "Baseless" in (l.get("label_type") or "")
                            and l.get("implicit_true") is not True]
                if impl and not conflict and not baseless:
                    g = "IMPLICIT_TRUE"
                elif conflict:
                    g = "CONTRADICTED"
                elif baseless:
                    g = "UNSUPPORTED_BASELESS"
                else:
                    continue
                pool[g].append({"context": context, "claim": sent, "task": s.get("task_type"),
                                "source_id": r["source_id"], "model": r.get("model"),
                                "label_types": sorted({l.get("label_type") for l in lbs}),
                                "spans": [l.get("text") for l in lbs][:3]})

    rng = random.Random(seed)
    sample = {}
    for g in GROUPS:
        items = pool.get(g, [])
        rng.shuffle(items)
        sample[g] = items[:per_group]
    return sample, {g: len(pool.get(g, [])) for g in GROUPS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True, choices=["factcg", "minicheck", "lettuce"])
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--per-group", type=int, default=120)
    ap.add_argument("--seed", type=int, default=20260919)
    args = ap.parse_args()

    sample, pool_sizes = build(args.seed, args.per_group)
    print("pool sizes (test split):", pool_sizes, flush=True)
    print("sampled:", {g: len(v) for g, v in sample.items()}, flush=True)

    if args.system == "factcg":
        from factcg import FactCGScore
        sc = FactCGScore(model_name="microsoft/deberta-v3-large",
                         batch_size=args.batch_size, verbose=False, use_hf_ckpt=True)
        score = lambda c, m: sc.score(contexts=list(c), claims=list(m))  # noqa: E731
        kind = "prob"
    elif args.system == "minicheck":
        from minicheck.minicheck import MiniCheck
        sc = MiniCheck(model_name="flan-t5-large", cache_dir=B + "/models/hf/hub")

        def score(c, m):
            _, raw, _, _ = sc.score(docs=list(c), claims=list(m))
            return list(raw)
        kind = "prob"
    else:
        from lettucedetect.models.inference import HallucinationDetector
        det = HallucinationDetector(
            method="transformer",
            model_path="KRLabsOrg/lettucedect-v2-mmbert-base",
            taxonomy_head="KRLabsOrg/lettucedect-v2-taxonomy-head")
        QUESTION = "What do the supplied sources establish about this subject?"

        def score(c, m):
            out = []
            for ctx, claim in zip(c, m):
                spans = det.predict(context=[ctx], question=QUESTION, answer=claim,
                                    output_format="spans")
                out.append(len(spans or []))
            return out
        kind = "spans"

    results, per_group = {}, {}
    t0 = time.time()
    n_scored = 0
    for g in GROUPS:
        items = sample[g]
        if not items:
            continue
        vals = []
        for i in range(0, len(items), args.batch_size):
            chunk = items[i:i + args.batch_size]
            vals.extend(score([x["context"] for x in chunk], [x["claim"] for x in chunk]))
        n_scored += len(vals)
        vals = [float(v) for v in vals]
        if kind == "prob":
            judged_supported = sum(1 for v in vals if v >= 0.5)
            per_group[g] = {
                "n": len(vals),
                "mean_support_prob": round(statistics.mean(vals), 4),
                "median_support_prob": round(statistics.median(vals), 4),
                "judged_SUPPORTED_at_0.5": judged_supported,
                "pct_judged_SUPPORTED": round(100.0 * judged_supported / len(vals), 1),
            }
        else:
            flagged = sum(1 for v in vals if v > 0)
            per_group[g] = {
                "n": len(vals),
                "mean_spans_flagged": round(statistics.mean(vals), 3),
                "flagged_any_span": flagged,
                "pct_flagged": round(100.0 * flagged / len(vals), 1),
                "pct_judged_SUPPORTED": round(100.0 * (len(vals) - flagged) / len(vals), 1),
            }
        results[g] = vals
        print(g, json.dumps(per_group[g]), flush=True)

    elapsed = time.time() - t0
    sep = None
    if "IMPLICIT_TRUE" in per_group and "CONTRADICTED" in per_group:
        sep = round(per_group["IMPLICIT_TRUE"]["pct_judged_SUPPORTED"]
                    - per_group["CONTRADICTED"]["pct_judged_SUPPORTED"], 1)

    out = {
        "system": args.system,
        "protocol": __doc__,
        "split": "test",
        "sampling": {"per_group_cap": args.per_group, "seed": args.seed,
                     "drawn_before_scoring": True},
        "pool_sizes_test_split": pool_sizes,
        "threshold": "published default 0.5, unchanged" if kind == "prob"
                     else "any flagged span = unsupported, unchanged",
        "by_group": per_group,
        "implicit_true_minus_contradicted_pct_supported": sep,
        "reading": "A separation near zero means the system does not distinguish "
                   "'absent from the context but not known false' from 'contradicted by "
                   "the context'. Its output may therefore not be read as a claim about "
                   "truth in the world.",
        "contamination": "LettuceDetect documents RAGTruth training; MiniCheck and FactCG "
                         "report LLM-AggreFact, which incorporates RAGTruth. Compatibility "
                         "metric only.",
        "operational": {"elapsed_s": round(elapsed, 1), "n_scored": n_scored,
                        "mean_latency_s": round(elapsed / max(1, n_scored), 4)},
        "raw_scores": {g: [round(v, 5) for v in vs] for g, vs in results.items()},
    }
    os.makedirs(B + "/external", exist_ok=True)
    dest = B + "/external/RAGTRUTH_%s.json" % args.system.upper()
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)
    print("separation (implicit_true - contradicted, pct judged supported):", sep)
    print("wrote", dest)


if __name__ == "__main__":
    main()
