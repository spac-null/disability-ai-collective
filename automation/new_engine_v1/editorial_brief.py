"""Opt-in editorial focus for a free Writer shadow, inside a frozen Ledger.

The model chooses a question and a subset of already licensed propositions. It does
not write facts, change source roles, or establish that its question is true. The
output is a proposal for shadow composition, not publication clearance.
"""
from __future__ import annotations

from .provider import parse_json_object

SYSTEM = """You are commissioning one Crip Minds essay from a frozen research record.
Find one question that the particular evidence can actually investigate. Select only
the numbered propositions needed to let that question develop, including any fact
that limits, complicates or could change the first reading. If the record cannot
support a worthwhile essay, say HOLD and name the missing evidence. The supplied
question is editorial intent, not a factual finding. Do not add a fact, scene, person,
date, number or causal claim. Do not outline the article or prescribe its beats.
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
        lines.append("%s  %s" % (fid, str(fact.get("proposition") or "").strip()))
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
