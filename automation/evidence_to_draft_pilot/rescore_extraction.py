#!/usr/bin/env python3
"""
rescore_extraction.py -- EXTRACTION_METRICS_V2.json (sections 5 and 6).

Re-scores the STORED extraction cells. No model call, no regeneration.

WHAT V1 GOT WRONG, and what v2 separates:

  v1 reported one number, `spans_present_in_document`, and let it stand in for
  "precision". It was a raw substring check against HTML-derived source text, so a model
  quoting displayed characters failed it. v2 reports RAW_EXACT_MATCH and
  DISPLAY_NORMALIZED_MATCH separately and never adds them into a precision claim.

  v1 also counted non-empty fields and called the results "attribution", "qualifiers",
  "event binding" and "translation fidelity". Those are ANNOTATION VOLUME. A non-empty
  `event` field is not a correct event binding, and a missing `translation` field is a
  contract-completion gap, not proof that no translation occurred -- Gemini repeatedly
  returns an English proposition over an Italian span, which is translation without the
  field. v2 renames every one of these to what it actually measures and adds the
  language-pair observation that separates the two readings.

  Section 6's A-F stay apart: output quantity, contract completeness, span
  recoverability, claim support, relevant coverage, relationship accuracy. Only A, B, C
  and part of F are machine-measurable here. CLAIM SUPPORT (D) and RELEVANT COVERAGE (E)
  are NOT computed: they need a reference list of the facts each passage actually
  establishes, which this pilot never built. They are reported as NOT_MEASURED rather
  than silently proxied by a count.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from evidence_to_draft_pilot import span_match_v2 as SM            # noqa: E402
from evidence_to_draft_pilot import source_reading as SR           # noqa: E402

ROOT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                    "evidence-to-draft-pilot")
OUT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                   "evidence-to-draft-pilot-audit-v2")

# Sources whose character is not article prose. Section 6 asks that navigation and
# bibliographic noise be separated from article-relevant information rather than counted
# as coverage. Classified by URL/title, recorded, never silently dropped.
NOISE_PATTERNS = (
    (r"arxiv\.org/list|arxiv\.org/abs/\?|/list/", "ARXIV_LISTING"),
    (r"amazon\.[a-z.]+/", "RETAIL_PRODUCT_PAGE"),
)


def source_character(src: dict) -> str:
    blob = "%s %s" % (src.get("url") or "", src.get("title") or "")
    for pat, label in NOISE_PATTERNS:
        if re.search(pat, blob, re.I):
            return label
    return "ARTICLE_PROSE"


def latin_ratio(s: str) -> float:
    letters = [c for c in (s or "") if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if ord(c) < 128) / len(letters)


def looks_italian(s: str) -> bool:
    w = set(re.findall(r"[a-zà-ù]{3,}", (s or "").lower()))
    return len(w & {"che", "della", "per", "non", "con", "una", "sono", "delle",
                    "nel", "alla", "degli", "anche"}) >= 2


def rescore(cell: dict, source_text: str) -> dict:
    props = cell.get("propositions") or []
    raw = norm = disc = none = 0
    ambiguous = 0
    per = []
    for i, p in enumerate(props):
        span = p.get("support_span") or ""
        r = SM.score_span(span, source_text) if span else {
            "verdict": SM.NO_MATCH, "transformations": [], "occurrences": 0,
            "ambiguous": False}
        if r["verdict"] == SM.RAW_EXACT_MATCH:
            raw += 1
        elif r["verdict"] == SM.DISPLAY_NORMALIZED_MATCH:
            norm += 1
        elif r["verdict"] == SM.DISCONTINUOUS_SUPPORT:
            disc += 1
        else:
            none += 1
        if r.get("ambiguous"):
            ambiguous += 1
        per.append({"index": i, "verdict": r["verdict"],
                    "transformations": r.get("transformations"),
                    "occurrences": r.get("occurrences"),
                    "span_preview": span[:110]})

    # Language pairing: what the proposition is written in vs what the span is in.
    en_prop_it_span = sum(
        1 for p in props
        if (p.get("support_span") and looks_italian(p["support_span"])
            and not looks_italian(p.get("proposition") or "")
            and latin_ratio(p.get("proposition") or "") > 0.9))

    n = len(props)
    return {
        # A. OUTPUT QUANTITY -- not coverage.
        "A_output_quantity": {"propositions": n},
        # B. CONTRACT COMPLETENESS -- fields supplied, NOT fields correct.
        "B_contract_completeness": {
            "attribution_field_present": sum(1 for p in props if p.get("attribution")),
            "qualifier_field_present": sum(1 for p in props if p.get("qualifier")),
            "event_field_present": sum(1 for p in props if p.get("event")),
            "date_field_present": sum(1 for p in props if p.get("date_time")),
            "place_field_present": sum(1 for p in props if p.get("place")),
            "translation_field_present": sum(1 for p in props if p.get("translation")),
            "not_established_field_present": sum(1 for p in props
                                                 if p.get("not_established")),
            "measures": "whether the requested field was supplied; NOT whether its "
                        "value is correct",
        },
        # C. SPAN RECOVERABILITY -- two verdicts, never summed into precision.
        "C_span_recoverability": {
            "raw_exact_match": raw,
            "display_normalized_match": norm,
            "discontinuous_support": disc,
            "no_match": none,
            "ambiguous_location": ambiguous,
            "locatable_total": raw + norm,
            "is_not_entailment": True,
            "per_proposition": per,
        },
        # D / E -- deliberately not computed.
        "D_claim_support": "NOT_MEASURED -- needs per-span entailment judgement",
        "E_relevant_coverage": "NOT_MEASURED -- needs a reference list of the facts "
                               "each passage establishes; this pilot never built one",
        # F. RELATIONSHIP ACCURACY -- only the observable part.
        "F_relationship_observables": {
            "english_proposition_over_italian_span": en_prop_it_span,
            "note": "an English proposition over an Italian span is translation WITHOUT "
                    "the separate field: a contract-completeness gap, not proof that no "
                    "translation occurred",
        },
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cells = ROOT / "ledger" / "cells"
    passages = {p["passage_id"]: p for p in
                json.loads((ROOT / "extraction" / "PASSAGES.json").read_text())}
    out = {"evaluation_version": 2,
           "scored_from": "stored extraction cells; no model call, no regeneration",
           "cases": [], "totals": {}}

    tot = {}
    for f in sorted(cells.glob("extract_*.json")):
        cell = json.loads(f.read_text())
        pid = cell.get("passage")
        if not pid or pid not in passages:
            continue
        model = "gemini" if "_gemini_" in f.name else "claude"
        sid, source_id = pid.split("::")
        subj = json.loads((ROOT / "subjects" / sid / "SUBJECT.json").read_text())
        src = next(s for s in subj["generation_inputs"]["sources"]
                   if s["source_id"] == source_id)
        delivered = (src.get("text") or "")[:SR.PER_SOURCE_CHARS]
        m = rescore(cell, delivered)
        row = {"model": model, "case": sid, "source_id": source_id,
               "source_character": source_character(src),
               "retained_source_chars": len(src.get("text") or ""),
               "delivered_to_extractor_chars": len(delivered),
               "v1_reported_spans_present":
                   (cell.get("score") or {}).get("spans_present_in_document"),
               "metrics": m}
        out["cases"].append(row)
        t = tot.setdefault(model, {"propositions": 0, "raw": 0, "norm": 0,
                                   "disc": 0, "none": 0, "v1": 0, "ambiguous": 0,
                                   "en_prop_it_span": 0})
        c = m["C_span_recoverability"]
        t["propositions"] += m["A_output_quantity"]["propositions"]
        t["raw"] += c["raw_exact_match"]
        t["norm"] += c["display_normalized_match"]
        t["disc"] += c["discontinuous_support"]
        t["none"] += c["no_match"]
        t["ambiguous"] += c["ambiguous_location"]
        t["v1"] += row["v1_reported_spans_present"] or 0
        t["en_prop_it_span"] += m["F_relationship_observables"][
            "english_proposition_over_italian_span"]
    out["totals"] = tot
    (OUT / "EXTRACTION_METRICS_V2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False))

    print("%-8s %6s %6s %6s %6s %6s %6s  %s"
          % ("model", "props", "v1", "raw", "norm", "disc", "none", "locatable"))
    for model, t in sorted(tot.items()):
        loc = t["raw"] + t["norm"]
        print("%-8s %6d %6d %6d %6d %6d %6d  %d/%d (%.1f%%)"
              % (model, t["propositions"], t["v1"], t["raw"], t["norm"], t["disc"],
                 t["none"], loc, t["propositions"],
                 100.0 * loc / max(1, t["propositions"])))
    print()
    for model, t in sorted(tot.items()):
        print("%-8s english proposition over italian span: %d | ambiguous locations: %d"
              % (model, t["en_prop_it_span"], t["ambiguous"]))
    print("\nwrote %s" % (OUT / "EXTRACTION_METRICS_V2.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
