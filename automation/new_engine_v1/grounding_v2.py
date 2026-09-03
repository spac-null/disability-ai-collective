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

import hashlib
import json
import os
import time

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

MAX_CLAIMS_CLASSIFIED = 40       # bound on claims classified per article
CLASSIFIER_MAX_TOKENS = 700       # per claim, when a batch carries one
DEADLINE_EXHAUSTED = "SHADOW_DEADLINE_EXHAUSTED"

# ── batched focused classification (2026-09-03) ───────────────────────────────
#
# One claim per call was 40 calls per article, measured at ~$0.85-1.10 and 65-85s, and
# that cost is the recorded blocker on ever running V2 as a production shadow. Batching
# groups ALREADY-IDENTIFIED claims into one request; it does not hand the model an
# article and ask which claims matter, which is the instability V2 exists to avoid.
#
# Each claim keeps its own evidence capsule and its own record. The model is asked for
# one structured result per supplied atomic_id and nothing else -- no discovery, no
# ranking, no omission, no combining, no global reasoning about the article. A result
# citing evidence supplied for a DIFFERENT claim in the same batch is a validation
# error, never repaired.
CLASSIFY_BATCH_SIZE = 4
MAX_CLASSIFY_BATCHES = 10        # ceil(MAX_CLAIMS_CLASSIFIED / CLASSIFY_BATCH_SIZE)

# ── the shadow's total wall clock ─────────────────────────────────────────────
# Taken before the first V2 call of any kind, identification included, and passed to
# every provider call as a shared deadline -- provider.complete already clamps each leg
# to min(timeout, remaining) and refuses a leg with nothing left, so the total cannot be
# outlived by an ordinary per-call timeout. Exhausting it is recorded, never a verdict.
# 120, not the 90 first proposed, and the difference is measured. A real 40-sentence
# article -- the frozen Langrug draft -- takes 105.4s end to end at batch 4: 5
# identification calls in 48.5s and 8 classification batches in 56.9s, 8.1s per call.
# 90s exhausted at 88.1s with 16 of 36 claims unclassified. 120s fits that article with
# ~14% headroom and is the ceiling this work may set without owner review.
#
# It does NOT fit the structural worst case: 18 calls at 8.1s is ~146s. A worst-case
# article will therefore exhaust the deadline, and that is recorded as
# SHADOW_DEADLINE_EXHAUSTED rather than hidden -- never a verdict, never a coverage
# claim, and never able to reach a production decision.
GROUNDING_V2_TOTAL_SECONDS = 120
# A classification call given less than this has no useful chance of returning a valid
# structured reply, and an invalid reply is a recorded error rather than a verdict --
# so not starting is both cheaper and more honest. Set from the measured per-call
# latency of the optimised path.
# Measured per-call: 7.1s for a classification batch, 9.7s for an identification batch.
# 10 sits just above the slower of the two, so a call is never started without a
# realistic chance of returning a valid structured reply -- and an invalid reply is a
# recorded error, not a verdict, which is why not starting is the honest choice.
MIN_CALL_SECONDS = 10


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


BATCH_SYSTEM = (
    "You classify each claim you are given against THAT CLAIM'S OWN authorised "
    "evidence, and nothing else. You do not look for other claims, you do not judge "
    "prose, you do not rank or omit or combine claims, you do not reason about any "
    "article as a whole, and you do not use knowledge of the subject that is not in "
    "the excerpts.\n\n"
    "Each claim is given its own CLAIM_ID and its own evidence. Evidence supplied for "
    "one claim is NOT evidence for another: citing a source id or a quote from a "
    "different claim's block is rejected mechanically.\n\n"
    "Return exactly one result for every CLAIM_ID supplied -- no more, no fewer, none "
    "repeated.\n\n"
    + CLASSIFIER_SYSTEM.split("Exactly one classification:")[1].join(
        ["Exactly one classification per claim:", ""]))


def batch_prompt(items: list) -> str:
    """items: [(claim_id, claim_text, rendered_evidence)]. Order is preserved and is
    the caller's deterministic claim order."""
    blocks = []
    for cid, claim, ev in items:
        blocks.append('CLAIM_ID: %s\nCLAIM:\n"%s"\n\nAUTHORISED EVIDENCE FOR %s:\n%s'
                      % (cid, claim, cid, ev))
    return ("\n\n" + "-" * 60 + "\n\n").join(blocks) + (
        '\n\nReply with JSON only:\n'
        '{"results": [\n'
        '  {"claim_id": "%s",\n'
        '   "classification": "SUPPORTED|UNSUPPORTED|TRUE_UNCERTAIN|'
        'LEGITIMATE_INTERPRETATION",\n'
        '   "supporting_source_ids": ["S1"],\n'
        '   "supporting_exact_quotes": ["verbatim span(s) from THIS claim\'s evidence"],\n'
        '   "unsupported_residue": "the exact factual content not established, or empty",\n'
        '   "conflict_description": "what conflicts, or empty"}\n'
        ']}\n' % (items[0][0] if items else "C01"))


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


def classify(provider, claim: str, ev: dict,
             deadline: float | None = None) -> dict:
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
                              max_tokens=CLASSIFIER_MAX_TOKENS, temperature=0,
                              deadline=deadline)
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


def classify_batch(provider, items: list, evidence_by_id: dict,
                   deadline: float | None = None) -> dict:
    """N already-identified claims, ONE call, N independent records.

    `items` is [(claim_id, claim_text, rendered_evidence)] in the caller's deterministic
    order; `evidence_by_id` maps claim_id -> that claim's evidence dict, and is what
    each result is validated against -- so a result may only cite the blocks supplied
    for its own claim.

    Returns {claim_id: result}. Two failure granularities, chosen deliberately:

      * the BATCH CONTRACT broken -- unparsable payload, missing / duplicate / unknown /
        extra claim_id, count mismatch -- makes every claim in the batch a classifier
        error. Nothing in the reply can be trusted to belong to the claim it names.
      * the contract intact but ONE record invalid under the existing per-claim rules --
        that claim alone is a classifier error, and the other valid records stand.

    No retry. A malformed batch is recorded as malformed; asking again would hide the
    instability this whole module exists to measure.
    """
    ids = [cid for cid, _, _ in items]
    def all_error(detail, errs=()):
        return {cid: {"classification": CLASSIFIER_ERROR,
                      "retrieval_status": (evidence_by_id.get(cid) or {}).get("status"),
                      "errors": list(errs) or [detail], "reply": {}, "detail": detail,
                      "batch_size": len(ids)} for cid in ids}
    try:
        c = provider.complete(BATCH_SYSTEM, batch_prompt(items),
                              max_tokens=CLASSIFIER_MAX_TOKENS * len(items),
                              temperature=0, deadline=deadline)
        payload = parse_json_object(c.text)
    except Exception as e:
        return all_error("%s: %s" % (type(e).__name__, str(e)[:140]))

    results = payload.get("results")
    if not isinstance(results, list):
        return all_error("reply carries no results list")
    got = [r.get("claim_id") for r in results if isinstance(r, dict)]
    if len(results) != len(ids):
        return all_error("batch returned %d results for %d claims"
                         % (len(results), len(ids)))
    if len(set(got)) != len(got):
        return all_error("batch repeated a claim_id: %s" % sorted(got))
    missing = [c_ for c_ in ids if c_ not in got]
    extra = [c_ for c_ in got if c_ not in ids]
    if missing or extra:
        return all_error("batch claim_ids do not match the request "
                         "(missing=%s extra=%s)" % (missing, extra))

    out = {}
    for r in results:
        cid = r.get("claim_id")
        ev = evidence_by_id.get(cid) or {}
        # Validated against THIS claim's evidence only -- the isolation is the point.
        errs = validate(r, ev)
        out[cid] = {
            "classification": r.get("classification") if not errs else CLASSIFIER_ERROR,
            "retrieval_status": ev.get("status"),
            "supporting_source_ids": r.get("supporting_source_ids") or [],
            "supporting_exact_quotes": r.get("supporting_exact_quotes") or [],
            "unsupported_residue": (r.get("unsupported_residue") or "").strip(),
            "conflict_description": (r.get("conflict_description") or "").strip(),
            "errors": errs, "provider": c.identity(), "reply": r,
            "batch_size": len(ids),
        }
    return out


def batches(claims: list, size: int = CLASSIFY_BATCH_SIZE) -> list:
    """Deterministic grouping in the caller's claim order. Every claim appears exactly
    once; nothing is ranked, dropped or reordered."""
    size = max(1, int(size))
    return [claims[i:i + size] for i in range(0, len(claims), size)]


def evidence_identity(pack: dict) -> str:
    """A deterministic hash of the exact evidence V2 indexed.

    Diagnostic only, and deliberately not the future pack_id architecture: it hashes
    the source ids and texts this run actually saw, so two shadow observations can be
    compared knowing whether they read the same evidence.
    """
    h = hashlib.sha256()
    for src in (pack or {}).get("sources", []) or []:
        h.update(("\x00%s\x00" % (src.get("source_id") or "")).encode())
        h.update((src.get("text") or "").encode())
    return h.hexdigest()


def run_shadow(provider, *, article_text: str, pack: dict,
               batch_size: int = None, total_seconds: float = None,
               min_call_seconds: float = None) -> dict:
    """The whole shadow path. Returns a payload for GROUNDING_V2_SHADOW.json.

    It has no authority: the caller must persist it and nothing else. Every sentence is
    accounted for -- classified, routed as interpretation, or recorded as
    UNRESOLVED_BOUNDARY -- so a coverage gap is visible rather than invisible.

    The total wall clock starts HERE, before the first identification call, and is
    passed to every provider call. provider.complete clamps each leg to
    min(timeout, remaining) and refuses a leg with nothing left, so no ordinary per-call
    timeout can outlive the total.
    """
    size = CLASSIFY_BATCH_SIZE if batch_size is None else max(1, int(batch_size))
    min_call = MIN_CALL_SECONDS if min_call_seconds is None else min_call_seconds
    started = time.monotonic()
    deadline = started + (GROUNDING_V2_TOTAL_SECONDS if total_seconds is None
                          else total_seconds)

    sentences = CL.segment(article_text)
    backbone_errors = CL.verify_backbone(article_text, sentences)
    ident = CL.identify(provider, article_text, sentences, deadline=deadline)
    index = EV.PackIndex(pack)

    findings, calls, class_calls = [], ident["calls"], 0
    all_claims = CL.claims_for_classification(ident["records"])[:MAX_CLAIMS_CLASSIFIED]
    # Out of time is out of time whether or not there was anything left to classify.
    # An earlier draft only set this inside the batch loop, so a run whose budget was
    # gone before the loop began reported deadline_exhausted=False -- true of the loop,
    # false of the run.
    deadline_exhausted = (deadline - time.monotonic()) < min_call

    for group in batches(all_claims, size)[:MAX_CLASSIFY_BATCHES]:
        evs = {c["atomic_id"]: index.retrieve(c["atomic_claim"]) for c in group}
        # A retrieval that could not assemble evidence is NOT sent to the classifier and
        # is NOT a verdict -- unchanged from the one-at-a-time path.
        sendable = [c for c in group
                    if evs[c["atomic_id"]].get("status") != EV.INCOMPLETE
                    and evs[c["atomic_id"]].get("blocks")]
        results = {}
        for c in group:
            if c not in sendable:
                ev = evs[c["atomic_id"]]
                results[c["atomic_id"]] = {
                    "classification": NOT_CLASSIFIED_RETRIEVAL,
                    "retrieval_status": ev.get("status"), "errors": [],
                    "detail": ev.get("reason", ""), "reply": {}}
        if sendable:
            remaining = deadline - time.monotonic()
            if remaining < min_call:
                deadline_exhausted = True
                for c in sendable:
                    results[c["atomic_id"]] = {
                        "classification": DEADLINE_EXHAUSTED,
                        "retrieval_status": evs[c["atomic_id"]].get("status"),
                        "errors": [], "reply": {},
                        "detail": "%.1fs left, below the %.1fs a call needs"
                                  % (remaining, min_call)}
            else:
                items = [(c["atomic_id"], c["atomic_claim"],
                          EV.render(evs[c["atomic_id"]])) for c in sendable]
                results.update(classify_batch(
                    provider, items,
                    {c["atomic_id"]: evs[c["atomic_id"]] for c in sendable},
                    deadline=deadline))
                calls += 1
                class_calls += 1
        for claim in group:
            ev = evs[claim["atomic_id"]]
            result = results[claim["atomic_id"]]
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
                    "deadline_exhausted_claims":
                        sum(1 for f in findings
                            if f["result"]["classification"] == DEADLINE_EXHAUSTED),
                    "batch_size": size,
                    "identification_calls": ident["calls"],
                    "classification_calls": class_calls,
                    "model_calls": calls,
                    "claims_identified": len(all_claims),
                    "claims_classified":
                        sum(1 for f in findings if f["result"]["classification"]
                            in ENUM),
                    "deadline_exhausted": deadline_exhausted,
                    "total_seconds_bound": (GROUNDING_V2_TOTAL_SECONDS
                                            if total_seconds is None else total_seconds),
                    "elapsed_seconds": round(time.monotonic() - started, 2)},
        "evidence_identity": evidence_identity(pack),
        "_provider": ident.get("_provider", []),
    }
