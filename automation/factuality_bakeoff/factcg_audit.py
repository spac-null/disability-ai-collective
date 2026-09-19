"""Correct blast-radius audit for the FactCG claim-truncation defect.

The library does NOT tokenize (premise, claim) as a pair. `Inferencer.tokenize` renders
both into ONE string:

    "{premise}\\n\\nChoose your answer: based on the paragraph above can we conclude that
     \\"{claim}\\"?\\n\\nOPTIONS:\\n- Yes\\n- No\\nI think the answer is "

and then calls the tokenizer with truncation='only_first', max_length=2048. On a single
sequence that truncates the TAIL -- which is where the claim and the answer scaffold sit.
So whenever the rendered premise alone reaches the 2048-token window, the claim is cut
off and the score becomes claim-independent.

A chunk is counted as claim-truncating when the rendered template's token length exceeds
2048, i.e. when the claim cannot survive.
"""
import json

B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
LIMIT = 2048

from factcg.inference import Inferencer  # noqa: E402
from factcg.utils import INSTRUCTION_TEMPLATE  # noqa: E402

inf = Inferencer(model_name="microsoft/deberta-v3-large", batch_size=2,
                 verbose=False, use_hf_ckpt=True)
tok = inf.tokenizer
gold = json.load(open(B + "/gold/CRIP_MINDS_GOLD.json"))

CONDS = ["context_SOURCE_CITED_BASIS", "context_SOURCE_COMPLETE",
         "context_LEDGER_CITED_BASIS", "context_LEDGER_COMPLETE"]


def rendered_len(premise, claim):
    text = INSTRUCTION_TEMPLATE.format(text_a=premise, text_b=claim)
    return len(tok(text, add_special_tokens=True)["input_ids"])


audit, affected_cases = [], set()
for case in gold["cases"]:
    for cond in CONDS:
        ctx = case.get(cond)
        if not ctx:
            continue
        chunks = inf.chunking_src(ctx)
        bad = sum(1 for c in chunks if rendered_len(c, case["claim_text"]) > LIMIT)
        if bad:
            affected_cases.add(case["case_id"])
        audit.append({
            "case_id": case["case_id"], "condition": cond, "n_chunks": len(chunks),
            "n_claim_truncating_chunks": bad, "affected": bool(bad),
            "max_chunk_chars": max((len(c) for c in chunks), default=0),
        })

n_aff = sum(1 for a in audit if a["affected"])
summary = {
    "conditions_audited": len(audit),
    "conditions_with_claim_truncating_chunk": n_aff,
    "pct_conditions_affected": round(100.0 * n_aff / max(1, len(audit)), 1),
    "cases_affected": sorted(affected_cases),
    "n_cases_affected": len(affected_cases),
    "n_cases_total": len(gold["cases"]),
    "mechanism": "INSTRUCTION_TEMPLATE renders premise+claim into ONE string; "
                 "truncation='only_first' on a single sequence drops the tail, which is "
                 "the claim. Long premise -> claim removed -> claim-independent score -> "
                 "max-over-chunks makes the document score claim-independent.",
    "limit_tokens": LIMIT,
}
print(json.dumps(summary, indent=1))
with open(B + "/systems/FACTCG_DEFECT_AUDIT.json", "w") as fh:
    json.dump({"summary": summary, "audit": audit}, fh, indent=1)
print("wrote FACTCG_DEFECT_AUDIT.json")
