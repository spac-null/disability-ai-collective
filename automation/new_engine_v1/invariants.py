"""
invariants.py -- engine-level contracts NEW_ENGINE_V1 enforces on top of the frozen
Phase-1 stage contracts.

WHY THIS IS SEPARATE FROM contracts.py
The 2026-08-24 acceptance run exposed a real gap: Discovery is asked for a
source-grounded verbatim anchor, but nothing proved the anchor actually occurs in the
snapshot, and one quoted span in that run was not verbatim.

The fix needs a designated anchor field. `contracts.py` is a VERBATIM port of the frozen
Phase-1 module, and making a new field REQUIRED there would (a) invalidate the frozen
accepted artifacts, which have no such field, and (b) break hash-comparability with the
frozen shadow runs. So the contract revision is recorded as follows:

  CONTRACT REVISION (2026-08-24, engine-scoped)
    * The DISCOVERY payload gains one field: `source_anchor_quote`.
    * It is ADDITIVE in contracts.py terms -- validate() neither requires nor rejects
      it, so every frozen artifact stays readable and its hash unchanged.
    * NEW_ENGINE_V1 requires it, and enforces the exactness invariant HERE, before
      Article Form and before the writer.

Scope, deliberately narrow: this validates ONE designated field against the snapshot.
It does not police quotations inside interpretive prose -- `disturbance` and
`what_becomes_knowable` are interpretation and may paraphrase. Writer Grounding is what
judges the article's own claims.
"""
from __future__ import annotations

import re
import unicodedata

ANCHOR_FIELD = "source_anchor_quote"

# Deterministic reasons. Callers must not invent new strings for these conditions.
ANCHOR_MISSING = "DISCOVERY_SOURCE_ANCHOR_MISSING"
ANCHOR_NOT_IN_SOURCE = "DISCOVERY_SOURCE_ANCHOR_NOT_IN_SOURCE"
ANCHOR_TOO_SHORT = "DISCOVERY_SOURCE_ANCHOR_TOO_SHORT"
SUBJECT_SCOPE_MISMATCH = "DISCOVERY_SUBJECT_OUTSIDE_RESEARCHED_SCOPE"
# Anchor SELECTION (2026-09-03, PR #61). The anchor is chosen by id from deterministic
# candidates, so the ways it can fail are now the ways a choice can fail -- each an
# explicit HOLD, never a fallback to model-written text.
ANCHOR_ID_MISSING = "DISCOVERY_SOURCE_ANCHOR_ID_MISSING"
ANCHOR_ID_UNKNOWN = "DISCOVERY_SOURCE_ANCHOR_ID_UNKNOWN"
NO_ANCHOR_CANDIDATES = "DISCOVERY_NO_ANCHOR_CANDIDATES"
NO_VALID_ANCHOR = "DISCOVERY_NO_VALID_SOURCE_ANCHOR"

# An anchor shorter than this is not a clause and cannot ground a mechanism; it would
# also make the containment test meaningless (any short string matches something).
MIN_ANCHOR_CHARS = 25

_QUOTES = {
    "“": '"', "”": '"', "„": '"', "‟": '"', "«": '"',
    "»": '"', "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "′": "'", "″": '"',
}
_DASHES = {"‐": "-", "‑": "-", "‒": "-", "–": "-",
           "—": "-", "―": "-", "−": "-"}


def normalize(text: str) -> str:
    """Collapse ONLY mechanically harmless differences.

    Unicode NFKC, curly quotes and dashes folded to ASCII, all whitespace runs collapsed
    to one space, trimmed. Nothing semantic: no case folding, no punctuation stripping,
    no stemming, no fuzzy matching. A paraphrase must still fail.
    """
    if not isinstance(text, str):
        return ""
    t = unicodedata.normalize("NFKC", text)
    for src, dst in list(_QUOTES.items()) + list(_DASHES.items()):
        t = t.replace(src, dst)
    return re.sub(r"\s+", " ", t).strip()


def check_anchor(discovery_payload: dict, source_text: str) -> tuple[bool, str, str]:
    """(ok, reason_code, detail). Fail-closed: anything unproven is invalid.

    The anchor may be wrapped in quote characters by the model; those are stripped
    before comparison, because the quoting is presentation, not content.
    """
    raw = discovery_payload.get(ANCHOR_FIELD)
    if not isinstance(raw, str) or not raw.strip():
        return False, ANCHOR_MISSING, "%s absent or empty" % ANCHOR_FIELD
    anchor = normalize(raw).strip('"\'')
    if len(anchor) < MIN_ANCHOR_CHARS:
        return (False, ANCHOR_TOO_SHORT,
                "anchor is %d chars, minimum %d" % (len(anchor), MIN_ANCHOR_CHARS))
    if anchor not in normalize(source_text):
        return (False, ANCHOR_NOT_IN_SOURCE,
                "anchor does not occur verbatim in the snapshot: %r" % anchor[:120])
    return True, "ok", "anchor verified verbatim in source (%d chars)" % len(anchor)


# The generative anchor repair that used to live here was removed by PR #61. It was
# handed only the anchor source and asked to find a span carrying a meaning that was in a
# DIFFERENT source, so it returned nothing and the run held anyway -- and keeping it would
# leave a model-written anchor one call away from authority. Selection replaces it.


def check_subject_scope(discovery_payload: dict, subject_span: str,
                        source_text: str) -> tuple[bool, str, str]:
    """(ok, reason_code, detail). Did Discovery write about the subject that was researched?

    The failure this closes is specific and was live on 28 August 2026: the anchor was a
    roundup covering seven unrelated projects, research scoped and searched for one of
    them, and Discovery then built its reading on a different one. Both stages were
    individually correct and the pack was provenance-valid; the article was simply
    grounded in material nobody had researched.

    The test is deterministic and uses the anchor invariant's own machinery: Discovery's
    verbatim `source_anchor_quote` must fall INSIDE the span of the anchor that the
    research pack was built for. No model call, no similarity score, no keyword overlap
    -- an offset comparison over the same normalised text `check_anchor` already
    validated the quote against.

    An empty or unverifiable subject span means the anchor was not partitioned into
    subjects (an ordinary single-subject article), and the check passes: it exists to
    stop a heterogeneous anchor being researched for A and written about B, not to
    narrow a source that only has one subject in it.
    """
    if not isinstance(subject_span, str) or not subject_span.strip():
        return True, "", "no subject span recorded; anchor is single-subject"
    src = normalize(source_text)
    span = normalize(subject_span)
    start = src.find(span)
    if start < 0:
        return True, "", "subject span is not a verbatim region of the anchor; not enforced"
    if len(span) >= len(src) - 1:
        return True, "", "subject span covers the whole anchor"
    anchor = normalize(discovery_payload.get(ANCHOR_FIELD) or "").strip('"\'')
    if not anchor:
        return False, ANCHOR_MISSING, "%s absent or empty" % ANCHOR_FIELD
    at = src.find(anchor)
    if at < 0:
        return False, ANCHOR_NOT_IN_SOURCE, "anchor is not a span of the source"
    end = start + len(span)
    if start <= at and at + len(anchor) <= end:
        return True, "", "anchor lies inside the researched subject (chars %d-%d)" % (start, end)
    return (False, SUBJECT_SCOPE_MISMATCH,
            "the research pack was built for the subject at chars %d-%d of the anchor, "
            "but Discovery grounded its reading at char %d -- outside it. Researching one "
            "item of a roundup and writing about another is the failure this blocks."
            % (start, end, at))
