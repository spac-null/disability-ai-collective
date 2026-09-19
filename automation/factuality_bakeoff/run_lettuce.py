"""Score the Crip Minds gold set with LettuceDetect (span localizer).

LettuceDetect is a RAG hallucination detector over (context, question, answer). Crip
Minds claims are not question-answer pairs, so ONE fixed, claim-neutral question is used
for every case and declared here; it is never varied per case or per label.

It is evaluated on its own terms (§16), not forced into a support probability:
  EXAMPLE level - did it flag any span in the claim?
  SPAN level    - does a flagged span overlap the gold unsupported span?
  TYPE          - what the taxonomy head called it.
  FALSE SPANS   - spans flagged on claims whose gold label is supported.
"""
import json
import os
import resource
import time

B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
GOLD = B + "/gold/CRIP_MINDS_GOLD.json"
QUESTION = "What do the supplied sources establish about this subject?"

CONDITIONS = [
    "context_SOURCE_CITED_BASIS",
    "context_SOURCE_COMPLETE",
    "context_LEDGER_CITED_BASIS",
    "context_LEDGER_COMPLETE",
]
SUPPORTED_LABELS = {"SUPPORTED_DIRECT", "SUPPORTED_RELATION",
                    "UNDER_CITED_BUT_SUPPORTED", "INTERPRETATION_SUPPORTED_PREMISES"}


def overlap(a0, a1, b0, b1):
    return max(0, min(a1, b1) - max(a0, b0))


def main():
    from lettucedetect.models.inference import HallucinationDetector

    t0 = time.time()
    detector = HallucinationDetector(
        method="transformer",
        model_path="KRLabsOrg/lettucedect-v2-mmbert-base",
        taxonomy_head="KRLabsOrg/lettucedect-v2-taxonomy-head",
    )
    load_s = time.time() - t0

    # wiring check from the project README's own example shape
    smoke = detector.predict(
        context=["France is a country in Europe. The capital of France is Paris. "
                 "The population of France is 67 million."],
        question="What is the capital of France? What is the population of France?",
        answer="The capital of France is Paris. The population of France is 69 million.",
        output_format="spans")
    smoke_flagged = [s.get("text") for s in smoke]
    smoke_ok = any("69" in (s or "") for s in smoke_flagged)
    print("SMOKE spans:", json.dumps(smoke, default=str)[:400], "ok=", smoke_ok, flush=True)

    gold = json.load(open(GOLD))
    results, latencies = [], []

    for case in gold["cases"]:
        claim = case["claim_text"]
        gold_span = case.get("unsupported_span")
        gs = None
        if gold_span:
            i = claim.find(gold_span)
            if i >= 0:
                gs = (i, i + len(gold_span))

        rec = {"case_id": case["case_id"], "gold_label": case["gold_label"],
               "failure_type": case["failure_type"], "article_key": case["article_key"],
               "gold_unsupported_span": gold_span, "gold_span_offsets": gs,
               "is_supported_gold": case["gold_label"] in SUPPORTED_LABELS,
               "conditions": {}}

        for cond in CONDITIONS:
            ctx = case.get(cond)
            if not ctx:
                continue
            t = time.time()
            spans = detector.predict(context=[ctx], question=QUESTION,
                                     answer=claim, output_format="spans")
            dt = time.time() - t
            latencies.append(dt)

            norm = []
            for s in spans or []:
                norm.append({
                    "start": s.get("start"), "end": s.get("end"),
                    "text": s.get("text"),
                    "confidence": s.get("confidence"),
                    "category": s.get("category") or s.get("label"),
                    "subcategory": s.get("subcategory"),
                })
            hit = False
            best_ov = 0
            if gs:
                for s in norm:
                    if s["start"] is None:
                        continue
                    ov = overlap(s["start"], s["end"], gs[0], gs[1])
                    best_ov = max(best_ov, ov)
                hit = best_ov > 0

            rec["conditions"][cond] = {
                "n_spans": len(norm), "spans": norm,
                "example_flagged": bool(norm),
                "span_overlaps_gold": hit,
                "best_overlap_chars": best_ov,
                "latency_s": round(dt, 3),
                "context_chars": len(ctx),
            }
        results.append(rec)
        c = rec["conditions"].get("context_SOURCE_COMPLETE") or {}
        print(rec["case_id"], rec["gold_label"][:28],
              "spans=", c.get("n_spans"), "overlap=", c.get("span_overlaps_gold"),
              [s["text"] for s in (c.get("spans") or [])][:2], flush=True)

    latencies.sort()

    def pct(p):
        return round(latencies[min(len(latencies) - 1, int(p * len(latencies)))], 3) if latencies else None

    vram = None
    try:
        import torch
        if torch.cuda.is_available():
            vram = round(torch.cuda.max_memory_allocated() / 1e9, 2)
    except Exception:
        pass

    out = {
        "system": "lettucedetect",
        "model": "KRLabsOrg/lettucedect-v2-mmbert-base",
        "taxonomy_head": "KRLabsOrg/lettucedect-v2-taxonomy-head",
        "fixed_question": QUESTION,
        "smoke_test": {"spans": smoke_flagged, "passed": bool(smoke_ok),
                       "expectation": "flags the wrong population figure (69 million)"},
        "operational": {
            "model_load_s": round(load_s, 2), "n_scorings": len(latencies),
            "mean_latency_s": round(sum(latencies) / len(latencies), 3) if latencies else None,
            "p50_latency_s": pct(0.5), "p95_latency_s": pct(0.95),
            "peak_ram_gb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2),
            "peak_vram_gb": vram,
        },
        "results": results,
    }
    with open(B + "/systems/LETTUCEDETECT_GOLD.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote LETTUCEDETECT_GOLD.json")
    print(json.dumps(out["operational"], indent=1))


if __name__ == "__main__":
    main()
