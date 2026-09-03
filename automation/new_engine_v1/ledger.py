"""
ledger.py -- factual permissions come from evidence, and only from evidence.

WHY THIS EXISTS. Two demonstrated failures from the campaign, both structural:

1. THE "pink" INCIDENT. A colour was written into the Story Architect's own `turn` field
   by hand. The writer packet was then built FROM the architecture, so the packet
   contained "pink", and the post-writer audit compares prose to the packet -- which
   means it certified the fabrication as approved. A stage that can write prose into the
   packet can mint factual ground truth. That has to be impossible, not discouraged.

2. THE ROMAN CLOSING CLAIM. "the part that was not engineered" is a claim about the
   world: that no receiving-end tooling exists. Nothing in the evidence says so. It
   survived every screen because the screens looked for unapproved numbers, names,
   colours and scene props, and a negative claim is none of those. Grounding V2 had
   independently been flagging this same class -- negative-existence claims it cannot
   support because no evidence can support an absence.

So: the ledger is the ONLY origin of factual permission. Story stages select, order,
connect, interpret and time the reader's discovery. They never author a fact.

And silence is not evidence of absence. A negative proposition needs either explicit
evidence FOR the negative, or an honest bounded scope over an audited corpus.
"""
from __future__ import annotations

import re

# ── claim taxonomy ────────────────────────────────────────────────────────────
POSITIVE = "POSITIVE_FACT"
NEGATIVE_EXISTENCE = "NEGATIVE_EXISTENCE"   # no X exists / was never built
ABSENCE = "ABSENCE"                          # X does not contain / mention / describe Y
EXCLUSIVITY = "EXCLUSIVITY"                  # only / none but / nothing except
FIRST_LAST = "FIRST_LAST"                    # the first / the last / never before
COMPARATIVE_NEGATION = "COMPARATIVE_NEGATION"  # unlike A, B did not
ATTRIBUTION = "ATTRIBUTION"                  # X stated / said / aimed
INTERPRETATION = "INTERPRETATION"            # editorial reading, not a world claim

CLAIM_TYPES = (POSITIVE, NEGATIVE_EXISTENCE, ABSENCE, EXCLUSIVITY, FIRST_LAST,
               COMPARATIVE_NEGATION, ATTRIBUTION, INTERPRETATION)

# The types that assert something about the world being missing. These are the ones
# silence cannot license.
NEGATIVE_TYPES = (NEGATIVE_EXISTENCE, ABSENCE, EXCLUSIVITY, FIRST_LAST,
                  COMPARATIVE_NEGATION)

# Scope of a negative claim.
WORLD = "WORLD"                    # about reality: needs explicit negative evidence
AUDITED_CORPUS = "AUDITED_CORPUS"  # about a bounded, enumerated set we actually checked

_WS = re.compile(r"\s+")


def _n(s: str) -> str:
    return _WS.sub(" ", (s or "")).strip().lower()


# ── building the ledger from evidence ─────────────────────────────────────────
def make_fact(fact_id: str, proposition: str, claim_type: str, evidence_ids: list,
              support_span: str = "", entities: list | None = None,
              scope: str = WORLD, corpus_size: int = 0,
              prohibited_extensions: list | None = None) -> dict:
    return {"fact_id": fact_id, "proposition": proposition, "claim_type": claim_type,
            "evidence_ids": list(evidence_ids or []), "support_span": support_span,
            "entities": list(entities or []), "scope": scope,
            "corpus_size": corpus_size,
            "prohibited_extensions": list(prohibited_extensions or [])}


def validate_fact(fact: dict, evidence_text: str) -> list:
    """A factual permission is only a permission if the evidence carries it."""
    errs = []
    fid = fact.get("fact_id") or "<no id>"
    if not re.match(r"^F\d{2,}$", str(fid)):
        errs.append("%s: fact_id must look like F01" % fid)
    ct = fact.get("claim_type")
    if ct not in CLAIM_TYPES:
        return errs + ["%s: claim_type %r not in the taxonomy" % (fid, ct)]
    if not (fact.get("proposition") or "").strip():
        errs.append("%s: empty proposition" % fid)

    if ct == INTERPRETATION:
        # An interpretation is allowed to have no support span, but it must still be
        # anchored to the evidence it reads.
        if not fact.get("evidence_ids"):
            errs.append("%s: an interpretation must name the evidence it reads" % fid)
        return errs

    if not fact.get("evidence_ids"):
        errs.append("%s: no evidence_ids" % fid)

    span = _n(fact.get("support_span"))
    if not span:
        errs.append("%s: no support_span quoted from the evidence" % fid)
    elif span not in _n(evidence_text):
        errs.append("%s: support_span is not verbatim in the evidence: %r"
                    % (fid, fact.get("support_span")[:70]))

    # The rule silence cannot satisfy.
    if ct in NEGATIVE_TYPES:
        if fact.get("scope") == AUDITED_CORPUS:
            if not fact.get("corpus_size"):
                errs.append("%s: an AUDITED_CORPUS negative must state how many items "
                            "were audited" % fid)
            if not re.search(r"\b(none|no|neither|not one)\b.*\b(of|among)\b|"
                             r"\b(of|among)\b.*\b(none|no)\b",
                             _n(fact.get("proposition")), re.I):
                errs.append("%s: an AUDITED_CORPUS negative must be worded as a claim "
                            "about that set, not about the world" % fid)
        elif fact.get("scope") == WORLD:
            # explicit negative evidence required: the span itself must be negative
            if not re.search(r"\b(no|not|never|none|without|nothing|nobody|neither|"
                             r"lacks?|absent|unavailable|has yet to|failed to)\b",
                             _n(span)):
                errs.append("%s: a WORLD negative claim needs evidence that states the "
                            "negative; the span quoted is not negative, and silence is "
                            "not evidence of absence" % fid)
        else:
            errs.append("%s: negative claim with scope %r" % (fid, fact.get("scope")))
    return errs


def validate_ledger(ledger: dict, evidence_text: str) -> list:
    errs = []
    for fid, fact in sorted(ledger.items()):
        if fact.get("fact_id") != fid:
            errs.append("%s: fact_id disagrees with its key (%r)" % (fid, fact.get("fact_id")))
        errs += validate_fact(fact, evidence_text)
    return errs


def propositions(ledger: dict) -> dict:
    """fact_id -> readable proposition. This is the ONLY text a packet may carry."""
    return {fid: f["proposition"] for fid, f in ledger.items()}


def negative_ids(ledger: dict) -> set:
    return {fid for fid, f in ledger.items() if f.get("claim_type") in NEGATIVE_TYPES}


# ── the anti-laundering invariant ─────────────────────────────────────────────
def architect_may_not_mint(arch: dict, ledger: dict) -> list:
    """Story Architect may reference factual permissions. It may not create them.

    Every fact id the architecture uses must already exist in the ledger, and the
    architecture's own prose fields may not introduce a factual attribute that no ledger
    proposition carries. This is the check the "pink" incident needed and did not have.
    """
    errs = []
    known = set(ledger)
    used = set(arch.get("use_facts") or [])
    for b in (arch.get("beats") or []):
        used |= set(b.get("facts_allowed") or [])
    minted = sorted(used - known)
    if minted:
        errs.append("architecture references fact ids that are not in the ledger "
                    "(minted facts): %s" % minted)
    return errs
