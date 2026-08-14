"""
rewrite_integrity.py — shared fail-closed guard against catastrophic rewrite
corruption. Added 2026-08-14, morning-stabilization follow-up (see
.claude/morning-stabilization-2026-08-14.md).

Root incident: `_posts/2026-03-31-the-floor-plan-of-disappearance.md` was
published, from its very first commit, with its own body duplicated --
paragraphs repeated almost verbatim, separated by a leaked line of model
self-commentary ("I need to stop and return the correct article. Let me
apply only the listed fixes precisely."). Traced to `rewrite_with_opus`'s
acceptance check (llm.py), `rewritten.count("---") >= 2 and len(rewritten)
> 400` -- trivially satisfied by the function's own synthetic frontmatter
wrapper alone, with zero check for duplicated or malformed content. Neither
of the two other rewrite/revision paths (`_opus_targeted_revision`,
`_fable_polish_rewrite`) check for this either -- their shared fabrication
guard (`_reject_if_unsupported_specifics`) only flags NEW unsupported
facts/quotes, and a verbatim repeat of the ORIGINAL introduces nothing new,
so it passes that guard untouched.

SCOPE, DELIBERATELY NARROW: this catches CATASTROPHIC rewrite corruption --
a substantial, multi-paragraph block of the response duplicating another
part of itself -- not ordinary rhetorical repetition, callbacks, refrains,
or two paragraphs discussing the same idea. This is NOT review.py's G
repetition-shadow check (`_check_repetition_shadow`), which is a much looser,
observation-only, single-paragraph-pair candidate detector for editorial
calibration. This module's job is narrower and its bar is much higher: it
exists to make a specific, already-happened failure mode structurally
impossible to repeat, not to judge writing quality.

DUPLICATION SIGNAL (evidence, automation/repetition_shadow_corpus_harvest.py
+ ad hoc probing during the forensic pass, both zero-network/local-only):
requiring a RUN of consecutive paragraphs, each matching a corresponding
paragraph at a FIXED offset elsewhere in the same text (same shape as
copy-pasting a multi-paragraph block), at Jaccard similarity >= 0.7 on
content words, gave a clean, wide margin against real data -- the floor-plan
article produces a run of 6 consecutive matches (similarity 0.91-1.0);
sweeping this exact detector across all 140 currently-published articles
(including the 4 with a real but unrelated duplicate-figcaption cosmetic
bug) produces ZERO other matches at min_run=3 -- confirmed even at the more
sensitive min_run=2. A single isolated high-similarity paragraph pair (the
figcaption-duplication shape, or an intentional refrain) never forms a
multi-paragraph consecutive run and is correctly ignored. `<figure>...
</figure>` blocks are stripped entirely before comparison (not just their
tags) specifically so two similar image captions can never contribute to
this signal, confirmed structurally, not just empirically.

LENGTH RATIO: computed and reported for observability (the historical
failure measured ~1.97x), but NOT used as an independent rejection trigger
-- there is no saved corpus of legitimate rewrite input/output pairs in this
repo to calibrate a safe threshold against (these are live API calls, never
logged with before/after content), and one real corruption data point is
not enough evidence to set a boundary that won't risk rejecting a
legitimately long rewrite. Per instruction, omitted as a rejection reason
until real paired data exists to calibrate it.

META-COMMENTARY LEAK: no separate phrase-based detector built. No existing
mechanism in this repo does this for prose (the `cj2_b2_probe*.py` family's
"preamble" extraction is JSON-preamble parsing for an unrelated B2/CJ-2
research context, not reusable here, and out of scope to touch regardless).
A phrase blacklist for "I need to stop"/"let me"/etc. would be exactly the
brittle, overfit-to-one-sentence detector the instructions warn against --
confirmed live: "let me tell you what they're missing" and similar rhetorical
address-to-the-reader phrasing appears in multiple genuinely good, already-
published articles. The duplication-run detector above already catches the
historical failure with a wide margin without needing to read the leaked
sentence at all, so a separate leak detector isn't needed for this failure
class.
"""
import re

REASON_DUPLICATED_BODY = "DUPLICATED_BODY"
REASON_MALFORMED_ARTICLE = "MALFORMED_ARTICLE"

# Same stopword purpose as review.py's _REPETITION_STOPWORDS -- kept as an
# independent copy rather than a cross-module import (this module must be
# importable from llm.py without pulling in review.py's own dependencies).
_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
    "is", "are", "was", "were", "with", "this", "that", "these", "those",
    "from", "by", "as", "it", "its", "not", "but", "how", "why", "what",
    "when", "who", "which", "be", "been", "being", "has", "have", "had",
    "will", "would", "could", "should", "can", "do", "does", "did", "no",
    "so", "than", "then", "there", "their", "they", "them", "he", "she",
    "his", "her", "you", "your", "i", "we", "our", "if", "into", "out",
    "up", "down", "about", "still", "just", "one", "also",
})


def _strip_figure_blocks(text):
    return re.sub(r"<figure[^>]*>.*?</figure>", "", text, flags=re.DOTALL)


def _normalize_paragraphs(text):
    """Strip frontmatter, figure/image blocks entirely (not just their tags --
    see module docstring on why this must happen before paragraph splitting,
    not after), markdown links (kept as link text), and any remaining HTML."""
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    body = _strip_figure_blocks(body)
    body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
    body = re.sub(r"<[^>]+>", "", body)
    return [p.strip() for p in body.split("\n\n") if p.strip()]


def _content_words(paragraph):
    words = re.findall(r"[a-z']+", paragraph.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def find_duplicated_block(text, sim_threshold=0.7, min_content_words=8,
                           min_run=3, min_offset=4):
    """Deterministic, zero-network. Looks for a RUN of >= min_run consecutive
    paragraph indices i, i+1, ... each matching a corresponding paragraph at
    the SAME fixed offset elsewhere in the text (i+offset, i+1+offset, ...)
    at Jaccard content-word similarity >= sim_threshold -- the signature of a
    genuine multi-paragraph block having been duplicated, not an isolated
    restated idea or a repeated figure caption (both structurally excluded:
    the former needs a matching offset+run, which coincidental restatement
    essentially never produces; the latter never reaches paragraph-comparison
    at all -- figure blocks are stripped before splitting).

    min_offset guards against ordinary short-range rhetorical repetition
    (a phrase or single paragraph echoed a few lines later) counting as
    duplication -- the historical failure's offset was 13-15 paragraphs.

    Returns the single longest run found (a list of (i, j, similarity)
    tuples) if any run reaches min_run, else None. Never raises."""
    try:
        paragraphs = _normalize_paragraphs(text or "")
        word_sets = [_content_words(p) for p in paragraphs]
        eligible = [len(ws) >= min_content_words for ws in word_sets]
        n = len(paragraphs)

        matches = {}
        for i in range(n):
            if not eligible[i]:
                continue
            for j in range(i + min_offset, n):
                if not eligible[j]:
                    continue
                similarity = _jaccard(word_sets[i], word_sets[j])
                if similarity >= sim_threshold:
                    matches[(i, j)] = round(similarity, 2)

        best = None
        for (i, j) in sorted(matches):
            run = [(i, j, matches[(i, j)])]
            k = 1
            while (i + k, j + k) in matches:
                run.append((i + k, j + k, matches[(i + k, j + k)]))
                k += 1
            if len(run) >= min_run and (best is None or len(run) > len(best)):
                best = run
        return best
    except Exception:
        # A crash in this analysis must never be indistinguishable from "no
        # duplication found" being silently swallowed elsewhere -- but it
        # also must never be allowed to propagate into a live rewrite call's
        # own exception handling and get misread as an API failure. Treat an
        # analysis failure as "could not confirm duplication," not as a
        # rejection -- the caller's other checks (length, frontmatter) still
        # apply independently.
        return None


def _has_valid_frontmatter_and_body(text, min_body_chars=200):
    """Minimal structural check: exactly the two things `rewrite_with_opus`'s
    old `count("---") >= 2` check was trying and failing to verify -- one
    real frontmatter block, and a non-trivial body after it. Same regex
    idiom already used elsewhere in this codebase (publish_best.py's
    parse_frontmatter, generate.py's own frontmatter-stripping logic) rather
    than a new parser."""
    if not text:
        return False, "empty response"
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return False, "no valid frontmatter block found"
    body = text[m.end():].strip()
    if len(body) < min_body_chars:
        return False, f"body too short after frontmatter ({len(body)} chars)"
    return True, None


def validate_rewrite_integrity(original, rewritten, require_frontmatter=False):
    """Shared fail-closed guard for all three rewrite/revision acceptance
    paths in llm.py. Checks `rewritten` for catastrophic corruption --
    duplicated body (see find_duplicated_block) and, when
    require_frontmatter=True (rewrite_with_opus only -- the other two
    functions operate on body text with no frontmatter), a malformed
    article shape.

    Returns {"ok": bool, "reasons": [...], "duplicated_run": [...] or None,
    "length_ratio": float or None}. `reasons` is empty iff ok is True.
    Never raises -- callers must still fall back to `original` on ok=False,
    same as every other failure path these functions already have; this
    guard only ever narrows what gets accepted, never widens it."""
    reasons = []

    duplicated_run = find_duplicated_block(rewritten)
    if duplicated_run:
        reasons.append(REASON_DUPLICATED_BODY)

    if require_frontmatter:
        valid, _why = _has_valid_frontmatter_and_body(rewritten)
        if not valid:
            reasons.append(REASON_MALFORMED_ARTICLE)

    length_ratio = None
    if original:
        length_ratio = round(len(rewritten or "") / len(original), 3)

    return {
        "ok": not reasons,
        "reasons": reasons,
        "duplicated_run": duplicated_run,
        "length_ratio": length_ratio,
    }
