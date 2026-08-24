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


# ── ONE bounded repair, for exactness only ────────────────────────────────────
REPAIR_SYSTEM = (
    "You are correcting ONE field. You are given a source text and a claimed quotation "
    "that is not an exact span of it. Return the exact span of the source that the "
    "claim was reaching for, copied character-for-character from the source.\n\n"
    "You may not paraphrase, shorten below one clause, merge two separate places, or "
    "invent wording. If no single exact span carries that meaning, say so."
)


def repair_prompt(source_text: str, bad_anchor: str) -> str:
    return (
        "SOURCE:\n<<<SOURCE\n%s\nSOURCE>>>\n\n"
        "CLAIMED QUOTATION (not exact):\n%s\n\n"
        "Reply with JSON only:\n"
        '{"exact_span": "the verbatim span copied from SOURCE, or empty string if none '
        'exists"}\n' % (source_text, bad_anchor)
    )


def repair_anchor(provider, discovery_payload: dict, source_text: str) -> tuple[bool, str]:
    """ONE constrained attempt. Changes only the designated anchor field.

    No retry loop, no wholesale Discovery regeneration. Returns (repaired, detail); the
    result is re-validated by check_anchor, so a repair that is still not exact fails.
    """
    from .provider import parse_json_object
    bad = str(discovery_payload.get(ANCHOR_FIELD, ""))
    try:
        c = provider.complete(REPAIR_SYSTEM, repair_prompt(source_text, bad),
                              max_tokens=600)
        span = str(parse_json_object(c.text).get("exact_span", "")).strip()
    except Exception as e:
        return False, "anchor repair attempt failed: %s" % str(e)[:160]
    if not span:
        return False, "repair returned no exact span"
    candidate = dict(discovery_payload)
    candidate[ANCHOR_FIELD] = span
    ok, code, detail = check_anchor(candidate, source_text)
    if not ok:
        return False, "repaired anchor still invalid (%s): %s" % (code, detail)
    discovery_payload[ANCHOR_FIELD] = span
    discovery_payload["source_anchor_repaired"] = True
    return True, "anchor repaired to an exact source span (%d chars)" % len(normalize(span))
