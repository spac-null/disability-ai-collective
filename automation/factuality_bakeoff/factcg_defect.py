"""Quantify and work around a FactCG chunking defect, then re-score.

DEFECT (library, not adapter):
  `Inferencer.chunking_src(max_chunk_size=550)` measures NLTK word tokens but never
  splits a single "sentence" that already exceeds the budget -- the else-branch assigns
  `chunk = s["text"]` whatever its size. Real source text (PDF extractions, navigation
  furniture) contains segments with no sentence punctuation, so an oversized chunk is
  produced. The pair is then tokenized with truncation='only_first', max_length=2048; the
  premise alone consumes the whole window and the CLAIM IS TRUNCATED AWAY. That chunk
  returns a fixed, claim-independent probability, and because scoring aggregates with a
  max over chunks, the document's score becomes claim-independent.

  Observed: identical 0.8916546702 for the true claim, an unrelated gold claim, and a
  deliberately false control, on the same 39k-char context.

WORKAROUND (declared, not tuned): split any chunk that does not fit the model window into
token-bounded pieces, so every chunk leaves room for the claim. This changes only
chunking; the checkpoint, threshold and aggregation are untouched. Reported as a separate
variant so the as-documented numbers stay visible.
"""
import json
import sys

import nltk
from nltk.tokenize import sent_tokenize


def fits(tokenizer, premise, claim, limit):
    n = len(tokenizer(premise, claim)["input_ids"])
    return n <= limit


def claim_survives(tokenizer, premise, claim, limit):
    """True if the claim's tokens are still present after truncation='only_first'."""
    enc = tokenizer(premise, claim, truncation="only_first", max_length=limit)
    ids = enc["input_ids"]
    claim_ids = tokenizer(claim, add_special_tokens=False)["input_ids"]
    if not claim_ids:
        return True
    # the claim is the second segment; check its final tokens are present
    tail = claim_ids[-5:]
    return any(ids[i:i + len(tail)] == tail for i in range(len(ids) - len(tail) + 1))


def safe_chunker(tokenizer, limit=2048, reserve=160, max_chunk_size=550):
    """chunking_src replacement: same sentence packing, but oversized pieces are split."""

    def count(text):
        return len(nltk.word_tokenize(text))

    def hard_split(text):
        ids = tokenizer(text, add_special_tokens=False)["input_ids"]
        budget = limit - reserve
        out = []
        for i in range(0, len(ids), budget):
            out.append(tokenizer.decode(ids[i:i + budget], skip_special_tokens=True))
        return out

    def chunking_src(src, max_chunk_size=max_chunk_size):
        chunks, chunk, size = [], "", 0
        for s in sent_tokenize(src):
            n = count(s)
            if size + n <= max_chunk_size:
                chunk = (chunk + "\n" + s).strip("\n")
                size += n
            else:
                if chunk.strip():
                    chunks.append(chunk.strip("\n"))
                chunk, size = s, n
        if chunk.strip():
            chunks.append(chunk.strip("\n"))

        fixed = []
        for c in chunks:
            if len(tokenizer(c, add_special_tokens=False)["input_ids"]) > limit - reserve:
                fixed.extend(hard_split(c))
            else:
                fixed.append(c)
        return [c for c in fixed if c.strip()]

    return chunking_src


def main():
    B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
    gold = json.load(open(B + "/gold/CRIP_MINDS_GOLD.json"))

    from factcg.inference import Inferencer
    inf = Inferencer(model_name="microsoft/deberta-v3-large", batch_size=2,
                     verbose=False, use_hf_ckpt=True)
    tok = inf.tokenizer
    LIMIT = 2048

    # ---- 1. blast radius under the library's own chunker ----
    audit = []
    for case in gold["cases"]:
        for cond in ("context_SOURCE_CITED_BASIS", "context_SOURCE_COMPLETE",
                     "context_LEDGER_CITED_BASIS", "context_LEDGER_COMPLETE"):
            ctx = case.get(cond)
            if not ctx:
                continue
            chunks = inf.chunking_src(ctx)
            bad = [c for c in chunks
                   if not claim_survives(tok, c, case["claim_text"], LIMIT)]
            audit.append({"case_id": case["case_id"], "condition": cond,
                          "n_chunks": len(chunks), "n_claim_truncating_chunks": len(bad),
                          "affected": bool(bad)})
    n_aff = sum(1 for a in audit if a["affected"])
    print("conditions audited: %d | claim-truncating: %d (%.0f%%)"
          % (len(audit), n_aff, 100.0 * n_aff / max(1, len(audit))), flush=True)

    # ---- 2. re-score with the workaround chunker ----
    inf.chunking_src = safe_chunker(tok, limit=LIMIT)
    results = []
    for case in gold["cases"]:
        rec = {"case_id": case["case_id"], "gold_label": case["gold_label"],
               "failure_type": case["failure_type"], "article_key": case["article_key"],
               "scores": {}}
        for cond in ("context_SOURCE_CITED_BASIS", "context_SOURCE_COMPLETE",
                     "context_LEDGER_CITED_BASIS", "context_LEDGER_COMPLETE"):
            ctx = case.get(cond)
            if not ctx:
                continue
            vals, _ = inf.batch_inference([ctx], [case["claim_text"]])
            rec["scores"][cond] = {"support_prob": float(vals[0]),
                                   "context_chars": len(ctx)}
        results.append(rec)
        print(rec["case_id"], {k: round(v["support_prob"], 4)
                               for k, v in rec["scores"].items()}, flush=True)

    out = {
        "system": "factcg_chunkfix",
        "variant": "declared defect workaround: oversized chunks split to fit the 2048-token "
                   "window so the claim is never truncated. Checkpoint, threshold and "
                   "max-aggregation unchanged.",
        "defect": {
            "where": "factcg/inference.py chunking_src + truncation='only_first'",
            "effect": "claim truncated out of oversized chunks -> fixed claim-independent "
                      "score -> max aggregation makes the document score claim-independent",
            "evidence": "0.8916546702 identical for true claim, unrelated claim and false control",
            "conditions_audited": len(audit),
            "conditions_with_claim_truncating_chunk": n_aff,
        },
        "audit": audit,
        "results": results,
    }
    with open(B + "/systems/FACTCG_GOLD_CHUNKFIX.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote FACTCG_GOLD_CHUNKFIX.json")


if __name__ == "__main__":
    main()
