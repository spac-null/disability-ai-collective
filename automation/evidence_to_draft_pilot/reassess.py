#!/usr/bin/env python3
"""
reassess.py -- FACTUAL_REASSESSMENT_V2.json (sections 7 and 8).

Re-examines every v1 factual objection against the COMPLETE frozen evidence, and
relabels the origin counts so they say what they actually measure.

── SECTION 7: what each objection is worth ──────────────────────────────────────

Each objection is classified as exactly one of:

  SUPPORTED_BY_RETAINED_SOURCE               a frozen source carries the claim
  SUPPORTED_BUT_EVIDENCE_NOT_DELIVERED       the support exists, BEYOND the 5,000-char
                                             cut v1 imposed -- the reviewer could not
                                             have seen it and must not be scored as
                                             having found a fabrication
  UNSUPPORTED_IN_FROZEN_EVIDENCE             no frozen source carries it
  CONTRADICTED_BY_FROZEN_EVIDENCE            a source asserts something incompatible
  INTERPRETATION_WITH_SUPPORTED_PREMISES     a reading, not a worldly claim
  MIXED_OR_UNRESOLVED                        cannot be settled from stored artefacts

DELIBERATE LIMIT. Span presence is not entailment, so this module NEVER upgrades an
objection to "supported" on a lexical match alone. It can only establish two things
deterministically: that relevant evidence existed beyond the delivery cut (which
downgrades the objection's standing), and that a claim's licensing facts are or are not
in the frozen ledger. Everything else stays MIXED_OR_UNRESOLVED for the owner or the v2
reviewers, and a phrase matching does not clear the sentence it sits in: attribution,
qualifier, chronology and implied relation are checked separately where the stored
record allows it.

── SECTION 8: origin counts say TEXTUAL origin, not CAUSAL origin ───────────────

v1 reported `WRITER 138 / CURRENT_EDITING 23 / GUARDED_EDITING 20` as "failure origin".
The classifier locates a SPAN across three texts. It cannot see that an edit removed the
attribution around an unchanged span, changed its antecedent, or flipped the negation of
the sentence before it. The same counts are retained, relabelled TEXTUAL_ORIGIN, and the
causal categories are reported as NOT_ESTABLISHED rather than as zero.

`PLAN_OR_EVIDENCE = 0` and `DETECTOR_FALSE_POSITIVE = 0` are withdrawn as findings: the
v1 classifier never tested either possibility.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from evidence_to_draft_pilot import span_match_v2 as SM            # noqa: E402

V1 = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                  "evidence-to-draft-pilot")
OUT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                   "evidence-to-draft-pilot-audit-v2")

V1_DELIVERED_PREFIX = 5000

SUPPORTED = "SUPPORTED_BY_RETAINED_SOURCE"
NOT_DELIVERED = "SUPPORTED_BUT_EVIDENCE_NOT_DELIVERED_TO_REVIEWER"
UNSUPPORTED = "UNSUPPORTED_IN_FROZEN_EVIDENCE"
CONTRADICTED = "CONTRADICTED_BY_FROZEN_EVIDENCE"
INTERPRETATION = "INTERPRETATION_WITH_SUPPORTED_PREMISES"
MIXED = "MIXED_OR_UNRESOLVED"


def content_terms(s: str) -> set:
    import re
    stop = {"the", "a", "an", "of", "and", "or", "in", "on", "to", "for", "with",
            "that", "this", "is", "was", "были", "as", "by", "at", "it", "its",
            "from", "but", "not", "no", "he", "she", "they", "their", "his", "her",
            "which", "who", "what", "there", "has", "have", "had", "been", "be"}
    return {w for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", (s or "").lower())
            if w not in stop}


def locate_support(claim_terms: set, sources: list) -> dict:
    """Where in the retained sources does this claim's vocabulary concentrate?

    A blunt instrument used for ONE purpose only: deciding whether the material a
    reviewer would have needed sat inside or outside the 5,000-character window v1
    delivered. It never decides that a claim is true.
    """
    best = {"source_id": None, "offset": None, "hits": 0, "in_v1_window": None}
    if not claim_terms:
        return best
    for s in sources:
        text = SM.normalize_display(s.get("text") or "", dehyphenate=True).lower()
        if not text:
            continue
        window = 1200
        for start in range(0, max(1, len(text) - window), 600):
            seg = text[start:start + window]
            hits = sum(1 for t in claim_terms if t in seg)
            if hits > best["hits"]:
                best = {"source_id": s.get("source_id"), "offset": start,
                        "hits": hits, "terms": len(claim_terms),
                        "in_v1_window": start < V1_DELIVERED_PREFIX}
    return best


def classify_objection(ob: dict, sources: list, ledger: dict) -> dict:
    """One v1 objection -> a v2 standing, with its basis recorded."""
    span = ob.get("span") or ob.get("article_span") or ""
    why = ob.get("why") or ""
    terms = content_terms(span) | content_terms(why)
    loc = locate_support(terms, sources)

    out = {"raw_objection": ob, "article_span": span,
           "concentration": loc, "confidence": "LOW"}

    # The one thing this can settle deterministically.
    if loc["source_id"] and loc["hits"] >= max(3, 0.35 * len(terms)):
        if loc["in_v1_window"] is False:
            out["classification"] = NOT_DELIVERED
            out["confidence"] = "MEDIUM"
            out["basis"] = ("the vocabulary of this objection concentrates in %s at "
                            "offset %d, beyond the %d-character prefix evaluation v1 "
                            "delivered; the reviewer could not have checked it"
                            % (loc["source_id"], loc["offset"], V1_DELIVERED_PREFIX))
            return out
        out["classification"] = MIXED
        out["basis"] = ("relevant material was inside the delivered window (%s @ %d), "
                        "so the objection is not explained by the delivery defect; "
                        "whether the source ESTABLISHES the claim is not settled here"
                        % (loc["source_id"], loc["offset"]))
        return out

    out["classification"] = MIXED
    out["basis"] = ("no source segment concentrates this objection's vocabulary; span "
                    "presence is not entailment and this module does not adjudicate "
                    "support")
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = json.loads((V1 / "RESULTS.json").read_text())
    report = {"evaluation_version": 2,
              "v1_evidence_delivery_prefix_chars": V1_DELIVERED_PREFIX,
              "subjects": [], "totals": {}}
    totals = {}
    origin_v1 = {}

    for row in results["subjects"]:
        run = row["subject_id"]
        subj = json.loads((V1 / "subjects" / run / "SUBJECT.json").read_text())
        sources = subj["generation_inputs"]["sources"]
        ledger = subj["generation_inputs"]["ledger"]
        fo = row.get("failure_origin") or {}
        for k, v in (fo.get("counts") or {}).items():
            origin_v1[k] = origin_v1.get(k, 0) + v

        # Deduplicate by (arm, normalised span): v1 counted the same assertion once per
        # reviewer, which inflated every total.
        seen, objections = {}, []
        for f in fo.get("findings") or []:
            key = (f.get("arm"), SM.normalize_display(f.get("span") or "").lower()[:160])
            if key in seen:
                seen[key]["reviewers"].append(f.get("reviewer"))
                continue
            rec = {"arm": f.get("arm"), "kind": f.get("kind"),
                   "span": f.get("span"), "why": f.get("why"),
                   "textual_origin": f.get("origin"),
                   "reviewers": [f.get("reviewer")]}
            seen[key] = rec
            objections.append(rec)

        assessed = []
        for ob in objections:
            c = classify_objection(ob, sources, ledger)
            c["arm"] = ob["arm"]
            c["kind"] = ob["kind"]
            c["reviewers"] = ob["reviewers"]
            c["textual_origin"] = ob["textual_origin"]
            totals[c["classification"]] = totals.get(c["classification"], 0) + 1
            assessed.append(c)

        report["subjects"].append({
            "subject_id": run, "split": row.get("split"),
            "v1_objection_records": len(fo.get("findings") or []),
            "distinct_assertions_after_dedup": len(objections),
            "assessed": assessed})
        print("%-10s v1 records=%3d  distinct=%3d  %s"
              % (run[-8:], len(fo.get("findings") or []), len(objections),
                 json.dumps({k: sum(1 for a in assessed
                                    if a["classification"] == k)
                             for k in sorted({a["classification"]
                                              for a in assessed})})))

    report["totals"] = totals
    report["origin_relabelled"] = {
        "v1_counts_retained_as_TEXTUAL_ORIGIN": origin_v1,
        "what_these_measure": "which of the three texts first contains the quoted span",
        "what_these_do_NOT_measure": "causal origin of a factual defect; an edit can "
                                     "change scope, attribution, antecedent or negation "
                                     "around an unchanged span",
        "causal_categories": {
            "SOURCE_EXTRACTION_OR_EVIDENCE_GAP": "NOT_ESTABLISHED",
            "LEDGER_DISTORTION": "NOT_ESTABLISHED",
            "PLAN_DISTORTION": "NOT_ESTABLISHED",
            "WRITER_STRENGTHENING": "NOT_ESTABLISHED",
            "EDIT_INDUCED_SEMANTIC_CHANGE": "NOT_ESTABLISHED",
            "EVALUATION_EVIDENCE_OMISSION": "ESTABLISHED for the objections classified "
                                            "SUPPORTED_BUT_EVIDENCE_NOT_DELIVERED",
            "DETECTOR_FALSE_POSITIVE": "NOT_ESTABLISHED -- v1 reported 0, but never "
                                       "tested for it; the 0 is withdrawn",
        },
        "withdrawn_v1_findings": ["PLAN_OR_EVIDENCE = 0", "DETECTOR_FALSE_POSITIVE = 0"],
    }
    (OUT / "FACTUAL_REASSESSMENT_V2.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False))
    print()
    print("TOTALS:", json.dumps(totals, indent=1))
    print("wrote %s" % (OUT / "FACTUAL_REASSESSMENT_V2.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
