"""Score the Crip Minds gold set with FactCG or MiniCheck.

Both expose the same shape: score(contexts, claims) -> support probability per pair, and
both chunk long documents internally with max/SummaC-style aggregation. We use those
documented paths unchanged; no threshold is fitted on Crip Minds labels.

Each run first reproduces the system's own README example as a wiring check. If that
check fails the adapter is wrong and the scores must not be trusted.
"""
import argparse
import json
import os
import resource
import sys
import time

B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
GOLD = B + "/gold/CRIP_MINDS_GOLD.json"

CONDITIONS = [
    "context_SOURCE_CITED_BASIS",
    "context_SOURCE_COMPLETE",
    "context_LEDGER_CITED_BASIS",
    "context_LEDGER_COMPLETE",
]


def peak_ram_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


def peak_vram_gb():
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.max_memory_allocated() / 1e9
    except Exception:
        pass
    return None


def load_factcg(batch_size):
    from factcg import FactCGScore
    scorer = FactCGScore(model_name="microsoft/deberta-v3-large",
                         batch_size=batch_size, verbose=False, use_hf_ckpt=True)

    def fn(contexts, claims):
        return scorer.score(contexts=contexts, claims=claims)

    smoke = [("sun raises from east", "sun raises from west"),
             ("sun raises from west", "sun raises from west")]
    return fn, smoke, {"expect": "first clearly below second (README: ~0.065 vs ~0.784)"}


def load_minicheck(batch_size):
    from minicheck.minicheck import MiniCheck
    # the pinned checkpoint lives in the experiment's HF hub cache
    scorer = MiniCheck(model_name="flan-t5-large", cache_dir=B + "/models/hf/hub")

    def fn(contexts, claims):
        _, raw_prob, _, _ = scorer.score(docs=list(contexts), claims=list(claims))
        return list(raw_prob)

    doc = ("A group of students gather in the school library to study for their upcoming "
           "final exams.")
    smoke = [(doc, "The students are preparing for an examination."),
             (doc, "The students are on vacation.")]
    return fn, smoke, {"expect": "first high, second low (README: ~0.98 vs ~0.007)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True, choices=["factcg", "minicheck"])
    ap.add_argument("--batch-size", type=int, default=8)
    args = ap.parse_args()

    gold = json.load(open(GOLD))
    loader = {"factcg": load_factcg, "minicheck": load_minicheck}[args.system]

    t0 = time.time()
    fn, smoke, smeta = loader(args.batch_size)
    load_s = time.time() - t0

    sm_ctx = [s[0] for s in smoke]
    sm_cl = [s[1] for s in smoke]
    sm_scores = fn(sm_ctx, sm_cl)
    smoke_ok = sm_scores[0] < sm_scores[1] if args.system == "factcg" else sm_scores[0] > sm_scores[1]
    print("SMOKE", args.system, sm_scores, "ok=", smoke_ok, smeta["expect"], flush=True)

    results = []
    latencies = []
    for case in gold["cases"]:
        rec = {"case_id": case["case_id"], "gold_label": case["gold_label"],
               "failure_type": case["failure_type"], "article_key": case["article_key"],
               "scores": {}}
        for cond in CONDITIONS:
            ctx = case.get(cond)
            if not ctx:
                continue
            t = time.time()
            score = fn([ctx], [case["claim_text"]])[0]
            dt = time.time() - t
            latencies.append(dt)
            rec["scores"][cond] = {"support_prob": float(score),
                                   "latency_s": round(dt, 3),
                                   "context_chars": len(ctx)}
        results.append(rec)
        print(rec["case_id"], {k: round(v["support_prob"], 4) for k, v in rec["scores"].items()}, flush=True)

    latencies.sort()

    def pct(p):
        if not latencies:
            return None
        return round(latencies[min(len(latencies) - 1, int(p * len(latencies)))], 3)

    out = {
        "system": args.system,
        "smoke_test": {"scores": [float(s) for s in sm_scores], "passed": bool(smoke_ok),
                       "expectation": smeta["expect"]},
        "operational": {
            "model_load_s": round(load_s, 2),
            "n_scorings": len(latencies),
            "mean_latency_s": round(sum(latencies) / len(latencies), 3) if latencies else None,
            "p50_latency_s": pct(0.5), "p95_latency_s": pct(0.95),
            "batch_size": args.batch_size,
            "peak_ram_gb": round(peak_ram_gb(), 2),
            "peak_vram_gb": round(peak_vram_gb(), 2) if peak_vram_gb() else None,
        },
        "threshold_policy": "default 0.5, published; no tuning on Crip Minds labels",
        "results": results,
    }
    dest = B + "/systems/%s_GOLD.json" % args.system.upper()
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", dest)
    print(json.dumps(out["operational"], indent=1))


if __name__ == "__main__":
    main()
