#!/usr/bin/env python3
"""
cj1_v3_anchor_resolver.py — EXPERIMENT-ONLY, NO MODEL CALLS.

Deterministic second-pass provenance resolution for CJ-1 v3 anchors that
failed the strict exact-substring validator (cj1_v3_validator.py). Reads
ALREADY-PRODUCED Round 1 results
(automation/.probe_fixtures/cj1-v3/results/*_result.json) and does not
mutate them -- writes a separate resolution report per fixture instead.

Purpose: separate "the model invented evidence" from "the model located
real evidence but transcribed a normalizable character differently."
cj1_v3_validator.py's strict check (correct, per the frozen v3 contract)
cannot make that distinction by itself -- this resolver is the followup
diagnostic, not a replacement validator and not silent rescue: the strict
`invalid` verdict from Round 1 stands unchanged regardless of what this
finds.

ALGORITHM (exactly as specified, no more):
  1. Exact substring match against source_snapshot -> exact_match.
  2. If exact fails, normalize ONLY:
       U+2018 LEFT SINGLE QUOTATION MARK  -> ASCII '
       U+2019 RIGHT SINGLE QUOTATION MARK -> ASCII '
       U+201C LEFT DOUBLE QUOTATION MARK  -> ASCII "
       U+201D RIGHT DOUBLE QUOTATION MARK -> ASCII "
     applied to BOTH the candidate excerpt and the source_snapshot, for
     LOCATION purposes only.
  3. Accept only if there is EXACTLY ONE matching location in the
     normalized snapshot -> normalized_unique_match. Recover and report
     the ORIGINAL (non-normalized) source substring at that location --
     never the model's version -- since normalization here is a 1:1
     character substitution, original-string indices are identical to
     normalized-string indices.
  4. Zero matches -> no_match. If the excerpt (checked both raw and
     quote-normalized) is nonetheless an exact substring of the
     fixture's TITLE, relabel -> out_of_scope (it's real text, just
     outside source_snapshot's evidentiary scope).
  5. More than one normalized match -> ambiguous_match. NOT rescued.

Deliberately NOT implemented (per explicit instruction): fuzzy matching,
edit distance, semantic similarity, whitespace normalization, dash
rewriting, punctuation deletion, model-assisted repair. Only the 4
smart-quote code points above are folded, and only to find a unique
location -- the persisted result is always the untouched original text.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
FIXTURES_DIR = AUTOMATION_DIR / ".probe_fixtures" / "cj1-v3"
RESULTS_DIR = FIXTURES_DIR / "results"

_QUOTE_FOLD = {
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
}


def _fold_quotes(text: str) -> str:
    for src, dst in _QUOTE_FOLD.items():
        text = text.replace(src, dst)
    return text


def resolve_anchor(excerpt: str, source_snapshot: str, title: str | None = None) -> dict:
    """Returns {"status": ..., "original_substring": str|None, "detail": str}."""
    idx = source_snapshot.find(excerpt)
    if idx != -1:
        # Exact match already -- confirm uniqueness isn't relevant here;
        # strict validator already accepts this case, resolver agrees.
        return {
            "status": "exact_match",
            "original_substring": source_snapshot[idx:idx + len(excerpt)],
            "detail": "exact substring match against source_snapshot",
        }

    norm_excerpt = _fold_quotes(excerpt)
    norm_snapshot = _fold_quotes(source_snapshot)
    positions = []
    start = 0
    while True:
        i = norm_snapshot.find(norm_excerpt, start)
        if i == -1:
            break
        positions.append(i)
        start = i + 1

    if len(positions) == 1:
        i = positions[0]
        # 1:1 character substitution -> indices in norm_snapshot equal
        # indices in the original source_snapshot.
        original = source_snapshot[i:i + len(excerpt)]
        return {
            "status": "normalized_unique_match",
            "original_substring": original,
            "detail": (
                f"unique match after folding U+2018/U+2019/U+201C/U+201D "
                f"to ASCII quotes; original source text recovered, not "
                f"the model's normalized text"
            ),
        }
    elif len(positions) > 1:
        return {
            "status": "ambiguous_match",
            "original_substring": None,
            "detail": f"{len(positions)} candidate locations after quote-folding -- not resolved, not rescued",
        }

    # len(positions) == 0: not in source_snapshot even after quote-folding.
    if title:
        if excerpt in title or norm_excerpt in _fold_quotes(title):
            return {
                "status": "out_of_scope",
                "original_substring": excerpt,
                "detail": "verbatim (or quote-fold-verbatim) match found in TITLE, not in source_snapshot -- real text, outside the snapshot's evidentiary scope",
            }

    return {
        "status": "no_match",
        "original_substring": None,
        "detail": "no exact or quote-folded match in source_snapshot, and not found in title either",
    }


def resolve_result_file(result_path: Path) -> dict:
    result = json.loads(result_path.read_text())
    slug = result["slug"]
    title = result.get("title")

    fixture_path = FIXTURES_DIR / f"{slug}.json"
    fixture = json.loads(fixture_path.read_text())
    source_snapshot = fixture["source_snapshot"]

    v3_parsed = result["v3"].get("parsed")
    anchors = (v3_parsed or {}).get("source_anchors") or []

    resolutions = []
    for i, anchor in enumerate(anchors):
        excerpt = anchor.get("excerpt") if isinstance(anchor, dict) else None
        if not isinstance(excerpt, str):
            resolutions.append({"anchor_index": i, "status": "malformed", "original_substring": None, "detail": "anchor has no string excerpt"})
            continue
        r = resolve_anchor(excerpt, source_snapshot, title=title)
        r["anchor_index"] = i
        r["claimed_excerpt"] = excerpt
        resolutions.append(r)

    return {
        "slug": slug,
        "strict_validator_verdict": result.get("v3_validation"),
        "resolutions": resolutions,
    }


def main():
    if not RESULTS_DIR.exists():
        print(f"No results dir at {RESULTS_DIR} -- run cj1_v3_probe.py first.")
        return
    out_dir = FIXTURES_DIR / "resolver_reports"
    out_dir.mkdir(exist_ok=True)
    for result_path in sorted(RESULTS_DIR.glob("*_result.json")):
        report = resolve_result_file(result_path)
        out_path = out_dir / f"{report['slug']}_resolver_report.json"
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"[{report['slug']}] strict={report['strict_validator_verdict']['valid'] if report['strict_validator_verdict'] else 'N/A'}")
        for r in report["resolutions"]:
            print(f"    anchor[{r['anchor_index']}] -> {r['status']}: {r['detail']}")
        print(f"    -> {out_path}")


if __name__ == "__main__":
    main()
