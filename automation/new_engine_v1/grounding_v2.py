"""
grounding_v2.py -- claim-focused grounding. SHADOW ONLY, OFF BY DEFAULT.

    article -> deterministic sentence backbone (claims.segment)
            -> narrow type + atomicity pass (claims.identify)
            -> deterministic evidence retrieval (evidence.PackIndex)
            -> focused source-relative classifier, one fixed claim at a time
            -> mechanically validated findings

WHAT THIS IS NOT
It is not the production grounder and it cannot become one by accident. It writes its
own artifact, it is never placed in the artifact map `decision.py` reads, it cannot set
GROUNDING_FINDINGS, cannot trigger repair, cannot reach the fact check or the safety
bridge, and cannot make a held article publishable. `runner.py` calls it only when
CRIPMINDS_GROUNDING_V2_SHADOW is explicitly enabled; unset means the production path is
byte-for-byte what it was.

WHY IT LOOKS LIKE THIS
Measured, on frozen inputs: the whole-article grounder flipped classifications on
identical bytes and lost claims between passes, at temperature 0 too. The same claims,
asked one at a time with only their own evidence, came back 5/5 UNSUPPORTED, 5/5
SUPPORTED and 5/5 TRUE_UNCERTAIN, with 20/20 structurally valid replies. The instability
lived in asking one call to find claims AND judge them.
"""
from __future__ import annotations

import json
import os

from . import claims as CL
from . import evidence as EV
from .provider import parse_json_object

SHADOW_ENV = "CRIPMINDS_GROUNDING_V2_SHADOW"
ARTIFACT = "GROUNDING_V2_SHADOW"

SUPPORTED = "SUPPORTED"
UNSUPPORTED = "UNSUPPORTED"
TRUE_UNCERTAIN = "TRUE_UNCERTAIN"
LEGITIMATE_INTERPRETATION = "LEGITIMATE_INTERPRETATION"
CLASSIFIER_ERROR = "SHADOW_CLASSIFIER_ERROR"
NOT_CLASSIFIED_RETRIEVAL = EV.INCOMPLETE
ENUM = (SUPPORTED, UNSUPPORTED, TRUE_UNCERTAIN, LEGITIMATE_INTERPRETATION)

MAX_CLAIMS_CLASSIFIED = 40       # bound on calls per article
CLASSIFIER_MAX_TOKENS = 700


def enabled() -> bool:
    """Explicit opt-in only. Anything but a clear yes is OFF."""
    return str(os.environ.get(SHADOW_ENV, "")).strip().lower() in ("1", "true", "on", "yes")


CLASSIFIER_SYSTEM = (
    "You classify ONE claim against the authorised evidence you are given, and nothing "
    "else. You do not look for other claims, you do not judge prose, and you do not use "
    "knowledge of the subject that is not in the excerpts.\n\n"
    "Exactly one classification:\n"
    "  SUPPORTED -- the COMPLETE factual content of the claim is established by the "
    "evidence.\n"
    "  UNSUPPORTED -- the complete claim contains factual content the evidence does not "
    "establish. Support for PART of the claim is fine; name what remains unsupported.\n"
    "  TRUE_UNCERTAIN -- the sources materially conflict, or leave a factual proposition "
    "genuinely unresolved.\n"
    "  LEGITIMATE_INTERPRETATION -- the claim is clearly framed as interpretation rather "
    "than empirical fact and invents no factual state.\n\n"
    "Rules, enforced mechanically after you answer:\n"
    "  SUPPORTED requires an empty unsupported_residue and at least one exact quote.\n"
    "  UNSUPPORTED requires unsupported_residue naming the exact factual residue.\n"
    "  TRUE_UNCERTAIN requires conflict_description and a quote from each conflicting "
    "side.\n"
    "  LEGITIMATE_INTERPRETATION requires the factual basis it rests on.\n"
    "Every quote must be copied CHARACTER-FOR-CHARACTER from the evidence. The fields "
    "carry the justification; do not write an essay."
)


def classifier_prompt(claim: str, rendered_evidence: str) -> str:
    return ('CLAIM:\n"%s"\n\nAUTHORISED EVIDENCE:\n%s\n\nReply with JSON only:\n'
            '{"classification": "SUPPORTED|UNSUPPORTED|TRUE_UNCERTAIN|LEGITIMATE_INTERPRETATION",\n'
            ' "supporting_source_ids": ["S1"],\n'
            ' "supporting_exact_quotes": ["verbatim span(s) from the evidence"],\n'
            ' "unsupported_residue": "the exact factual content not established, or empty",\n'
            ' "conflict_description": "what conflicts, or empty"}\n' % (claim, rendered_evidence))


def _norm(s):
    return " ".join((s or "").split()).lower()


def validate(reply: dict, ev: dict) -> list:
    """Deterministic structural validation. Never repairs, never reinterprets."""
    errs = []
    c = reply.get("classification")
    if c not in ENUM:
        return ["classification %r not in %s" % (c, ", ".join(ENUM))]
    known = {b["source_id"] for b in ev.get("blocks", [])}
    # Accumulated per source, not overwritten: a source contributes several blocks
    # (ranked sentence plus its context window), and keeping only the last one would
    # reject a quote that really is in the evidence.
    hay = {}
    for b in ev.get("blocks", []):
        hay[b["source_id"]] = hay.get(b["source_id"], "") + " \u2016 " + _norm(b["exact_span"])
    quotes = reply.get("supporting_exact_quotes") or []
    for sid in (reply.get("supporting_source_ids") or []):
        if sid not in known:
            errs.append("source id %s was not supplied as evidence" % sid)
    for q in quotes:
        if not any(_norm(q) and _norm(q) in h for h in hay.values()):
            errs.append("quote is not verbatim in the supplied evidence: %r" % str(q)[:60])
    residue = (reply.get("unsupported_residue") or "").strip()
    if c == SUPPORTED:
        if residue:
            errs.append("SUPPORTED with a non-empty unsupported_residue")
        if not quotes:
            errs.append("SUPPORTED without a supporting quote")
    if c == UNSUPPORTED and not residue:
        errs.append("UNSUPPORTED without an unsupported_residue")
    if c == TRUE_UNCERTAIN:
        if not (reply.get("conflict_description") or "").strip():
            errs.append("TRUE_UNCERTAIN without a conflict_description")
        sides = {sid for sid in known if any(_norm(q) in hay[sid] for q in quotes)}
        if len(known) > 1 and len(sides) < 2:
            errs.append("TRUE_UNCERTAIN without evidence from both conflicting sides")
    if c == LEGITIMATE_INTERPRETATION and not quotes:
        errs.append("LEGITIMATE_INTERPRETATION without a factual basis quote")
    return errs


def classify(provider, claim: str, ev: dict) -> dict:
    """One claim, one call. A retrieval that could not assemble evidence is NOT sent to
    the classifier and is NOT a verdict -- the claim is recorded as
    EVIDENCE_RETRIEVAL_INCOMPLETE, which is a coverage state, not a finding."""
    if ev.get("status") == EV.INCOMPLETE or not ev.get("blocks"):
        return {"classification": NOT_CLASSIFIED_RETRIEVAL,
                "retrieval_status": ev.get("status"), "errors": [],
                "detail": ev.get("reason", ""), "reply": {}}
    try:
        c = provider.complete(CLASSIFIER_SYSTEM,
                              classifier_prompt(claim, EV.render(ev)),
                              max_tokens=CLASSIFIER_MAX_TOKENS, temperature=0)
        reply = parse_json_object(c.text)
    except Exception as e:
        return {"classification": CLASSIFIER_ERROR, "retrieval_status": ev.get("status"),
                "errors": ["%s: %s" % (type(e).__name__, str(e)[:140])], "reply": {},
                "detail": ""}
    errs = validate(reply, ev)
    return {"classification": reply.get("classification") if not errs else CLASSIFIER_ERROR,
            "retrieval_status": ev.get("status"),
            "supporting_source_ids": reply.get("supporting_source_ids") or [],
            "supporting_exact_quotes": reply.get("supporting_exact_quotes") or [],
            "unsupported_residue": (reply.get("unsupported_residue") or "").strip(),
            "conflict_description": (reply.get("conflict_description") or "").strip(),
            "errors": errs, "provider": c.identity(), "reply": reply}


def run_shadow(provider, *, article_text: str, pack: dict) -> dict:
    """The whole shadow path. Returns a payload for GROUNDING_V2_SHADOW.json.

    It has no authority: the caller must persist it and nothing else. Every sentence is
    accounted for -- classified, routed as interpretation, or recorded as
    UNRESOLVED_BOUNDARY -- so a coverage gap is visible rather than invisible.
    """
    sentences = CL.segment(article_text)
    backbone_errors = CL.verify_backbone(article_text, sentences)
    ident = CL.identify(provider, article_text, sentences)
    index = EV.PackIndex(pack)

    findings, calls = [], ident["calls"]
    for claim in CL.claims_for_classification(ident["records"])[:MAX_CLAIMS_CLASSIFIED]:
        ev = index.retrieve(claim["atomic_claim"])
        result = classify(provider, claim["atomic_claim"], ev)
        if result["classification"] not in (NOT_CLASSIFIED_RETRIEVAL,):
            calls += 1
        findings.append({
            "atomic_id": claim["atomic_id"],
            "parent_sentence_id": claim["parent_sentence_id"],
            "parent_exact_span": claim["parent_exact_span"],
            "atomic_claim": claim["atomic_claim"],
            "derivation": claim["derivation"],
            "evidence": {"status": ev.get("status"), "top_score": ev.get("top_score"),
                         "reason": ev.get("reason", ""),
                         "blocks": [{"source_id": b["source_id"], "score": b["score"],
                                     "exact_span": b["exact_span"][:400]}
                                    for b in ev.get("blocks", [])]},
            "result": {k: v for k, v in result.items() if k != "reply"},
        })

    interp = CL.interpretation_candidates(ident["records"])
    unresolved = [r for r in ident["records"] if r["type"] == CL.UNRESOLVED]
    dist = {}
    for f in findings:
        dist[f["result"]["classification"]] = dist.get(f["result"]["classification"], 0) + 1
    return {
        "shadow": True,
        "authority": "NONE -- comparison artifact only; not read by decision.py, the "
                     "safety bridge, repair or the fact check",
        "article_sentences": sentences,
        "identification": {"records": ident["records"], "coverage": ident["coverage"]},
        "backbone_errors": backbone_errors,
        "findings": findings,
        "interpretation_candidates": interp,
        "unresolved_boundaries": [{"sentence_id": r["sentence_id"],
                                   "parent_exact_span": r["parent_exact_span"],
                                   "reason": r.get("unresolved_reason", "")}
                                  for r in unresolved],
        "metrics": {"sentences": len(sentences),
                    "records": len(ident["records"]),
                    "unresolved_boundaries": len(unresolved),
                    "empirical_claims": len(findings),
                    "interpretation_candidates": len(interp),
                    "classification_distribution": dist,
                    "invalid_classifier_responses":
                        sum(1 for f in findings
                            if f["result"]["classification"] == CLASSIFIER_ERROR),
                    "evidence_incomplete":
                        sum(1 for f in findings
                            if f["result"]["classification"] == NOT_CLASSIFIED_RETRIEVAL),
                    "model_calls": calls},
        "_provider": ident.get("_provider", []),
    }
