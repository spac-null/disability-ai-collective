"""
span_match_v2.py -- representation-aware span matching for the EXPERIMENTAL scorer.

WHY. Evaluation v1 scored a support span as "not found" whenever it was not a literal
substring of the retained source after `composition.normalize_span`. That normaliser
folds whitespace, quote and dash shape and lowercases -- but it does NOT decode HTML
character references. Several retained sources are HTML-derived and still carry
`&laquo;`, `&raquo;`, `&egrave;` and friends. A model that quotes what a reader SEES
(«, », è) therefore failed a check against text that stores what the markup SAYS.

Measured on `production-20260915T072045Z-40294a3a::S2`: 5 of 17 Gemini spans matched
under v1; all 17 match once the entities are decoded. Across the subtest, Gemini goes
from 41/54 to 53/54 and Claude is unchanged at 340/344 -- so v1's headline
"span precision gap" was largely an encoding artefact, not a factual difference.

WHAT THIS IS AND IS NOT. It answers ONE question: can this quoted span be located in
this source? That is SPAN RECOVERABILITY. It is not entailment, not citation accuracy,
not coverage, and not proof that the source establishes the proposition. Every result
carries `is_not_entailment`.

TWO VERDICTS ARE ALWAYS KEPT, never collapsed:
    RAW_EXACT_MATCH          byte-identical presence, no transformation at all
    DISPLAY_NORMALIZED_MATCH presence after the declared, listed transformations

WHAT THE NORMALISER MAY DO, exhaustively: decode HTML character references, apply
Unicode NFC, fold quote and dash shape, collapse whitespace, trim, and rejoin a word
broken across a line as 'hyphen + space'. Each application
is RECORDED on the result, so a reader can see which transformation earned the match.

WHAT IT MAY NEVER DO, asserted by the negative tests in the static suite: delete or
insert a word, reorder words, drop or add a negation, equate different numbers, equate
different entity names, or accept a paraphrase. A transformation that could change what
a sentence means is not a representation difference.

AMBIGUITY IS REPORTED, NOT RESOLVED. A span occurring more than once yields
`occurrences > 1` and every start offset, rather than a silently chosen location.
"""
from __future__ import annotations

import html
import re
import unicodedata

RAW_EXACT_MATCH = "RAW_EXACT_MATCH"
DISPLAY_NORMALIZED_MATCH = "DISPLAY_NORMALIZED_MATCH"
NO_MATCH = "NO_MATCH"

# Quote and dash shape only -- the same folding production already treats as safe.
_QUOTE_FOLD = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "—": "-", "–": "-", " ": " ",
}
_WS = re.compile(r"\s+")

# LINE-BREAK HYPHENATION LEFT BY THE EXTRACTOR. Several retained sources are PDF-derived
# and carry a hyphen followed by a space where the original had a word broken across a
# line: "self- constitutive", "self- disfigurement", "self- assessment",
# "first- personal". A model quoting what a READER sees writes "self-constitutive" and
# then fails a raw substring check against text that stores the break.
#
# Measured: this is the entire cause of Claude's 4 "missing" spans on 9381ae93::S3 --
# every one diverges at exactly such a hyphen.
#
# The rewrite only removes whitespace AFTER a hyphen that sits BETWEEN two word
# characters. It cannot join two separate words (there is no hyphen), cannot split one,
# and cannot alter a dash used as punctuation (spaced on both sides).
_HYPHEN_BREAK = re.compile(r"(?<=\w)-\s+(?=\w)")


def _dehyphenate(s: str) -> str:
    return _HYPHEN_BREAK.sub("-", s)


def _fold_shape(s: str) -> str:
    for a, b in _QUOTE_FOLD.items():
        s = s.replace(a, b)
    return s


def normalize_display(text: str, *, unescape=True, nfc=True, fold=True,
                      collapse_ws=True, dehyphenate=False) -> str:
    """The declared transformations, each individually switchable so a caller can
    report WHICH one earned a match rather than only that one did."""
    s = text or ""
    if unescape:
        s = html.unescape(s)
    if nfc:
        s = unicodedata.normalize("NFC", s)
    if fold:
        s = _fold_shape(s)
    if collapse_ws:
        s = _WS.sub(" ", s).strip()
    if dehyphenate:
        s = _dehyphenate(s)
    return s


def _occurrences(needle: str, haystack: str) -> list:
    if not needle:
        return []
    out, i = [], haystack.find(needle)
    while i != -1:
        out.append(i)
        i = haystack.find(needle, i + 1)
    return out


def match_span(span: str, source: str) -> dict:
    """Locate `span` in `source`. Returns the verdict, the transformations that were
    needed, occurrence count and offsets."""
    raw_hits = _occurrences(span or "", source or "")
    if raw_hits:
        return {"verdict": RAW_EXACT_MATCH, "transformations": [],
                "occurrences": len(raw_hits), "offsets": raw_hits[:8],
                "ambiguous": len(raw_hits) > 1, "is_not_entailment": True}

    # Which transformation actually earns it? Applied cumulatively, reported honestly.
    steps = [("html_unescape", dict(unescape=True, nfc=False, fold=False,
                                    collapse_ws=False)),
             ("nfc", dict(unescape=True, nfc=True, fold=False, collapse_ws=False)),
             ("quote_dash_fold", dict(unescape=True, nfc=True, fold=True,
                                      collapse_ws=False)),
             ("whitespace", dict(unescape=True, nfc=True, fold=True,
                                 collapse_ws=True)),
             ("line_break_hyphenation", dict(unescape=True, nfc=True, fold=True,
                                             collapse_ws=True, dehyphenate=True))]
    applied = []
    for name, kw in steps:
        applied.append(name)
        n = normalize_display(span, **kw)
        h = normalize_display(source, **kw)
        hits = _occurrences(n, h)
        if hits:
            return {"verdict": DISPLAY_NORMALIZED_MATCH,
                    "transformations": list(applied),
                    "occurrences": len(hits), "offsets": hits[:8],
                    "ambiguous": len(hits) > 1, "is_not_entailment": True}
    return {"verdict": NO_MATCH, "transformations": list(applied),
            "occurrences": 0, "offsets": [], "ambiguous": False,
            "is_not_entailment": True}


# ── DISCONTINUOUS SUPPORT ────────────────────────────────────────────────────
# A span that fails a contiguous check may still be present in the source as two pieces
# separated by intervening material -- a footnote, a page header, an inserted caption.
# That is a DIFFERENT finding from a fabricated quotation, and section 5 asks for the
# two to be classified apart. This detects it WITHOUT licensing it: the span is split at
# sentence-ish boundaries and each piece looked up on its own. A span whose pieces are
# all present, in order, is reported as DISCONTINUOUS_SUPPORT -- a quotation-fidelity
# problem, not evidence of invention.
DISCONTINUOUS_SUPPORT = "DISCONTINUOUS_SUPPORT"
_MIN_PIECE = 24


def _longest_prefix_present(needle: str, haystack: str) -> int:
    """Length of the longest prefix of `needle` that occurs in `haystack`."""
    lo, hi, best = 0, len(needle), 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if mid and needle[:mid] in haystack:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


def discontinuous_check(span: str, source: str, *, max_gap_chars: int = 600,
                        min_part: int = 20) -> dict:
    """Does the span appear as CONTIGUOUS PARTS separated by interposed source material?

    Anchored on the longest contiguous prefix rather than walked word by word. A word
    walk picks the first occurrence of a common word and then measures a gap to wherever
    that happened to land -- on the one real case here it reported a 1254-character gap
    for a block that is actually 287 characters long.

    THE MEASURED CASE, `9381ae93::S3`. The extracted source reads:

        "...have priority and importance because they concern" +
        "1 A.C. EWING, THE DEFINITION OF GOOD 133 (1947). 2 T.M. SCANLON, WHAT WE OWE
         TO EACH OTHER 160 (1998). 3 Id. at 158-60. brought to you by COREView metadata,
         citation and similar papers at core.ac.uk provided by PhilPapers [PDF PAGE 2] 2" +
        "what we owe to others."

    287 characters of footnote and page furniture dropped into the middle of a sentence
    by the PDF extractor. The sentence a reader sees is continuous; the stored text is
    not. That is an EXTRACTION ARTEFACT, and classifying it as a fabricated quotation
    would be wrong.

    STRICTNESS. Every part must be present, in order, each at least `min_part`
    characters, with each interposed gap under `max_gap_chars`. Passing means the
    quotation is not verbatim-contiguous in THIS extraction. It is not a licence to treat
    the span as exact, and it is not evidence that the source entails the proposition.
    """
    n_src = normalize_display(source, dehyphenate=True)
    rest = normalize_display(span, dehyphenate=True)
    if len(rest) < min_part * 2:
        return {"discontinuous": False, "reason": "span too short to test"}

    parts, gaps, cursor, guard = [], [], 0, 0
    while rest and guard < 12:
        guard += 1
        n = _longest_prefix_present(rest, n_src[cursor:])
        if n < min_part:
            return {"discontinuous": False, "parts_found": len(parts),
                    "unmatched_remainder": rest[:80]}
        at = n_src.index(rest[:n], cursor)
        if parts:
            gaps.append(at - cursor)
        parts.append({"text": rest[:n][:90], "at": at, "chars": n})
        cursor = at + n
        rest = rest[n:].strip()

    if not parts or rest:
        return {"discontinuous": False, "parts_found": len(parts),
                "unmatched_remainder": rest[:80]}
    if len(parts) < 2:
        return {"discontinuous": False, "reason": "contiguous"}
    worst = max(gaps) if gaps else 0
    if worst > max_gap_chars:
        return {"discontinuous": False, "parts_found": len(parts),
                "reason": "interposed gap of %d chars exceeds %d" % (worst,
                                                                    max_gap_chars)}
    return {"discontinuous": True, "parts": parts, "interposed_gaps": gaps,
            "largest_interposed_gap_chars": worst,
            "interposed_sample": n_src[parts[0]["at"] + parts[0]["chars"]:
                                       parts[1]["at"]][:240],
            "note": "every part present, in order, separated by interposed source "
                    "material; an extraction artefact / quotation-fidelity finding, "
                    "NOT a fabricated span and NOT evidence of entailment"}


def score_span(span: str, source: str) -> dict:
    r = match_span(span, source)
    if r["verdict"] == NO_MATCH:
        d = discontinuous_check(span, source)
        if d.get("discontinuous"):
            r = dict(r, verdict=DISCONTINUOUS_SUPPORT, discontinuous=d)
        else:
            r = dict(r, discontinuous=d)
    return r
