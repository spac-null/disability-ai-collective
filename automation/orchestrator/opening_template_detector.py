"""
opening_template_detector.py — deterministic cross-article opening-template
shadow signal (article-quality evidence pass, 2026-08-14, B/C from the A-M
reconciliation).

Distinct from review.py's `_check_repetition_shadow` (G): that check compares
paragraphs WITHIN one article to catch a body accidentally duplicating
itself. This module compares one article's OPENING against OTHER, separately
published articles' openings, to catch a different failure shape entirely:
the writer reaching for the same formulaic sentence across unrelated pieces
-- confirmed real and live in this publication's own history, not
hypothetical.

Confirmed historical instance (evidence pass corpus sweep, zero model calls):
a near-verbatim template -- "But I design [X]. And let me tell you what
they're missing" -- appears in 4 articles, all published within one week
(2026-03-08 to 2026-03-16). Three of the four (architects-are-designing-
buildings-for-the-wrong-sense, the-door-you-can-t-read-is-the-door-that-isn-t-
there, the-frequency-you-designed-out) share not just that one sentence but a
second template too ("[X] was designed by someone who thinks [Y] is [Z]" /
"The first thing you notice is...") and cluster tightly under this detector
(pairwise shared-shingle counts of 8, 7, 4). The fourth
(the-map-that-stops-at-the-door) uses the same rhetorical DEVICE with
different wording after "let me tell you" and does NOT cluster under this
literal-phrase detector -- a known, accepted miss (see module-level test
`case_map_that_stops_known_miss`), not a bug to chase: this detector targets
literal near-verbatim phrase reuse, not generic rhetorical-pattern
similarity, which is a much harder, much noisier problem.

Corpus-wide sweep (140 articles, this evidence pass) found two ADDITIONAL,
previously unknown 2-article template families this same method, unprompted:
"[I am] good at predicting how someone will feel" (2026-06-14 / 2026-06-18)
and "the first time I stood in front of" (2026-06-21 / 2026-06-22) -- both
pairs published days apart, same shape as the March cluster.

KNOWN FALSE-POSITIVE SHAPE, found live during calibration: two "swan-care"
articles (2026-06-04, 2026-06-19) share 5 shingles, but these are shared
FACTS about the same real legal case (a Health and Care Worker visa, a
specific costs figure), not a stylistic template -- a legitimate
`series_part`-style continuation (the later piece links directly to the
earlier one). This detector does not distinguish "same real facts, reused
legitimately" from "same phrasing, reused as a tic" -- flagged as a known
limitation, not fixed here (see instruction against "dozens of special
cases" for a single observed instance).

SHADOW ONLY. Never blocks. Never feeds _should_block. Reports a candidate
family, not a verdict -- exactly like G's own repetition-shadow discipline.
"""
import re

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
    "is", "are", "was", "were", "with", "this", "that", "these", "those",
    "from", "by", "as", "it", "its", "not", "but", "how", "why", "what",
    "when", "who", "which", "be", "been", "being", "has", "have", "had",
    "will", "would", "could", "should", "can", "do", "does", "did", "no",
    "so", "than", "then", "there", "their", "they", "them", "he", "she",
    "his", "her", "you", "your", "i", "we", "our", "if", "into", "out",
    "up", "down", "about", "still", "just", "one", "also", "me", "my",
})

# Calibrated against the corpus sweep documented above: >=3 shared 6-word
# shingles (each shingle must itself contain >=3 content words, filtering
# stopword-heavy false matches) separates the 3 confirmed template families
# (scores 8, 7, 5, 4, 4, 3 across their pairs) from the rest of the 140-
# article corpus (zero other pairs reach this bar) -- see
# opening_template_detector_test.py's corpus-derived fixtures for the exact
# numbers this threshold is drawn from.
DEFAULT_MAX_WORDS = 200
DEFAULT_SHINGLE_SIZE = 6
DEFAULT_MIN_CONTENT_WORDS_PER_SHINGLE = 3
DEFAULT_MIN_SHARED_SHINGLES = 3


def normalize_opening(text, max_words=DEFAULT_MAX_WORDS):
    """Strip frontmatter, figure/image blocks, markdown links (kept as link
    text), URLs, remaining HTML, and markdown emphasis/heading markers, then
    return the first `max_words` lowercase content tokens. 200 words is wide
    enough to contain the confirmed historical template's furthest-observed
    position (word ~161 in the-map-that-stops-at-the-door) with margin."""
    body = re.sub(r"^---\n.*?\n---\n", "", text or "", flags=re.DOTALL)
    body = re.sub(r"<figure[^>]*>.*?</figure>", "", body, flags=re.DOTALL)
    body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
    body = re.sub(r"https?://\S+", "", body)
    body = re.sub(r"<[^>]+>", "", body)
    body = re.sub(r"[*_#`]", "", body)
    words = re.findall(r"[a-z']+", body.lower())
    return tuple(words[:max_words])


def _shingles(words, k=DEFAULT_SHINGLE_SIZE, min_content_words=DEFAULT_MIN_CONTENT_WORDS_PER_SHINGLE):
    """k-word shingles (overlapping windows) over the token sequence, kept
    only when the shingle itself contains at least `min_content_words` non-
    stopword tokens -- filters shingles that are structurally identical
    common phrasing ("the first time i stood in") but rewards the ones that
    still carry real content, and (deliberately) makes a 3-content-word
    shingle like "the first time i stood in front of" count, since that IS
    one of the two newly-discovered real template families."""
    result = set()
    for i in range(len(words) - k + 1):
        shingle = words[i:i + k]
        content_count = sum(1 for w in shingle if w not in _STOPWORDS and len(w) > 2)
        if content_count >= min_content_words:
            result.add(shingle)
    return result


def shared_shingle_count(opening_a, opening_b, **kwargs):
    """opening_a/opening_b are already-normalized token tuples (see
    normalize_opening). Returns (count, shared_shingles_set). Never raises."""
    try:
        sa = _shingles(opening_a, **kwargs)
        sb = _shingles(opening_b, **kwargs)
        shared = sa & sb
        return len(shared), shared
    except Exception:
        return 0, set()


def find_template_match(this_opening, candidate_openings, min_shared_shingles=DEFAULT_MIN_SHARED_SHINGLES):
    """this_opening: normalized token tuple for the article being checked.
    candidate_openings: dict {slug: normalized token tuple} for the
    comparison set (e.g. a recent window of published articles). Returns the
    single BEST match (highest shared-shingle count) as
    {"matched_slug": str, "shared_count": int, "shared_phrases": [str, ...]}
    if it reaches min_shared_shingles, else None. Never raises -- a
    malformed candidate is just skipped, not a crash."""
    best = None
    for slug, opening in (candidate_openings or {}).items():
        try:
            count, shared = shared_shingle_count(this_opening, opening)
        except Exception:
            continue
        if count >= min_shared_shingles and (best is None or count > best["shared_count"]):
            best = {
                "matched_slug": slug,
                "shared_count": count,
                "shared_phrases": [" ".join(s) for s in sorted(shared)][:5],
            }
    return best
