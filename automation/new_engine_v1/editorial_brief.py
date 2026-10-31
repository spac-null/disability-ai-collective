"""Opt-in editorial focus for a free Writer shadow, inside a frozen Ledger.

The model chooses a question and a subset of already licensed propositions. It does
not write facts, change source roles, or establish that its question is true. The
output is a proposal for shadow composition, not publication clearance.
"""
from __future__ import annotations

from .provider import parse_json_object

SYSTEM = """You are commissioning one fully reported Crip Minds long-form essay from
a frozen research record. Find one consequential question that the particular evidence
can actually answer through distinct concrete particulars, a credible complication
and enough development to sustain roughly 1,400–2,200 words without repetition.
Select only the numbered propositions needed for that question. If the central answer
depends on missing outcomes, participant accounts, cohort details or implementation,
say HOLD and name the reporting needed. Do not turn a gap in the record into the
essay's main revelation or shrink the question until it becomes a thin explainer.
Where the record offers a witnessed action, exchange, document or physical object that
lets a reader enter the problem, keep the best such propositions. A list of categories
and outcomes alone is not enough material for a reported essay. The Writer decides
where those details belong; do not prescribe an opening or ending.
The supplied question is editorial intent, not a factual finding. Source IDs show
which propositions share a source; several facts from one source are not several
independent reports. Do not add a fact, scene, person, date, number or causal claim.
Do not outline the article or prescribe its beats.
Reply with one JSON object: {"decision":"WRITE|HOLD", "question":"...",
"fact_ids":["F01"], "reason":"one or two sentences", "missing_evidence":"..."}.
For HOLD, leave question empty and fact_ids empty."""


class EditorialBriefError(ValueError):
    pass


def propose(provider, *, subject: str, question: str, ledger: dict) -> dict:
    if not ledger:
        raise EditorialBriefError("cannot select a brief from an empty Ledger")
    lines = ["SUBJECT: " + subject.strip(), "ORIGINAL QUESTION: " + question.strip(),
             "FROZEN PROPOSITIONS:"]
    for fid, fact in sorted(ledger.items()):
        sources = ",".join(str(x) for x in (fact.get("evidence_ids") or [])) or "unspecified"
        lines.append("%s  [%s] %s" % (
            fid, sources, str(fact.get("proposition") or "").strip()))
    user = "\n".join(lines)
    completion = provider.complete(SYSTEM, user, max_tokens=1800)
    obj = parse_json_object(completion.text)
    decision = str(obj.get("decision") or "").upper()
    if decision not in ("WRITE", "HOLD"):
        raise EditorialBriefError("editorial decision must be WRITE or HOLD")
    ids = obj.get("fact_ids")
    if not isinstance(ids, list) or any(not isinstance(fid, str) for fid in ids):
        raise EditorialBriefError("fact_ids must be a list of strings")
    if len(ids) != len(set(ids)) or set(ids) - set(ledger):
        raise EditorialBriefError("brief cites duplicate or unknown fact IDs")
    selected_question = str(obj.get("question") or "").strip()
    if decision == "WRITE" and (not selected_question or not ids):
        raise EditorialBriefError("WRITE requires a question and selected facts")
    if decision == "HOLD" and (selected_question or ids):
        raise EditorialBriefError("HOLD must not carry a writing brief")
    return {
        "decision": decision,
        "question": selected_question,
        "fact_ids": ids,
        "reason": str(obj.get("reason") or "").strip(),
        "missing_evidence": str(obj.get("missing_evidence") or "").strip(),
        "provider": completion.identity(),
        "system_prompt": SYSTEM,
        "user_prompt": user,
    }
