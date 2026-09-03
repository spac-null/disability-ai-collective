"""
anchors.py -- the source anchor is SELECTED, never written.

Discovery used to be asked for `source_anchor_quote`: one clause "copied
CHARACTER-FOR-CHARACTER from the source above". It was then checked against the anchor
source and the run was held if the quote was not an exact span of it. Four production
runs on 3 September 2026 died there, and the forensics say the model was not failing to
copy:

    41c42b46  anchor verbatim in S1 -- and S1's own verified 167-char excerpt
    c5ec09c7  anchor verbatim in S1, inside the 3,000 chars rendered into the prompt
    58039ea9  anchor verbatim in S1, inside the rendered window
    cd623f10  anchor verbatim in S1, inside the rendered window

Four for four, the quote was an exact span of AUTHORISED material -- from the RESEARCH
PACK block rather than the ANCHOR SOURCE block. The prompt carries both and says "the
source above"; the validator accepts only the first. The model copied correctly out of
the wrong box, and the one repair call was then handed only the anchor source and asked
to find a span carrying a meaning that is not in it, so it returned nothing and the run
held. That is a scope mismatch between prompt and validator, not a paraphrase problem --
and one of the four sources was a 702-char gallery page with nothing quotable in it at
all, so quoting the pack was the only sane move available.

Widening the validator to accept any pack source was the wrong repair: `check_subject_scope`
locates Discovery's quote by OFFSET inside the anchor, which is what stops a roundup being
researched for one item and written about another (a live failure on 28 August 2026). The
anchor must keep coming from the anchor.

So the model no longer supplies the text. This module cuts the anchor source into bounded
exact spans, gives each an id, and Discovery returns an id. Production reads the text back
out of the mapping. A paraphrase cannot pass because there is nowhere to put one, and a
span from the wrong source cannot pass because it was never on the menu.
"""
from __future__ import annotations

import re

from .invariants import MIN_ANCHOR_CHARS, normalize

# Reported bounds, not implicit. The candidate list is a prompt payload, so it is capped
# on both axes: enough spans that Discovery has a real editorial choice, few enough that
# the block cannot crowd out the source it came from.
MAX_CANDIDATES = 40
MAX_CANDIDATE_BLOCK_CHARS = 6_000
MAX_SPAN_CHARS = 600            # a pair of long sentences; past this it is a passage

NO_ANCHOR = "NONE"              # Discovery's explicit "no span here supports a reading"

# Abbreviations that must not end a sentence. Without this "P.R." splits mid-phrase and
# the candidate list fills with fragments ("But the importance of good royal P.R.").
_ABBREV = (r"(?<!\bP\.R)(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bSt)(?<!\bJr)"
           r"(?<!\bSr)(?<!\bvs)(?<!\bNo)(?<!\bcf)(?<!\bal)(?<!\be\.g)(?<!\bi\.e)"
           r"(?<!\bU\.S)(?<!\bU\.K)")
_SPLIT = re.compile(_ABBREV + r"(?<=[.!?])[\"')\]]?\s+(?=[A-Z\"'(\[])")


def _sentences(text: str) -> list:
    return [p.strip() for p in _SPLIT.split(text) if p.strip()]


def candidates(source_text: str, subject_span: str = "") -> list:
    """Bounded exact spans of the ANCHOR source, each with a stable id.

    Every returned `exact_span` is a substring of `normalize(source_text)`, so
    `check_anchor` passes on any of them by construction -- the normalisation is the same
    one it compares with, and it collapses only whitespace, curly quotes and dashes.

    `subject_span`, when the pack recorded one, narrows the menu to the researched
    subject. That is deliberate: a candidate outside it would only be rejected later by
    `check_subject_scope`, so offering it invites a hold instead of preventing one.

    Sentences and adjacent sentence pairs, in source order. Pairs exist because an idea
    is often two sentences (a claim and the thing that qualifies it) and a single-sentence
    menu would force Discovery to under-quote.
    """
    text = normalize(source_text)
    if not text:
        return []
    span = normalize(subject_span)
    if span and span in text:
        text = span

    sents = _sentences(text)
    spans, seen = [], set()
    for i, s in enumerate(sents):
        for cand in (s, " ".join(sents[i:i + 2]) if i + 1 < len(sents) else None):
            if not cand:
                continue
            cand = cand.strip()
            if not (MIN_ANCHOR_CHARS <= len(cand) <= MAX_SPAN_CHARS):
                continue
            if cand in seen or cand not in text:   # `in text` is the honesty check
                continue
            seen.add(cand)
            spans.append(cand)

    out, used = [], 0
    for s in spans:
        if len(out) >= MAX_CANDIDATES or used + len(s) > MAX_CANDIDATE_BLOCK_CHARS:
            break
        out.append({"anchor_id": "A%03d" % (len(out) + 1), "exact_span": s})
        used += len(s)
    return out


def render(cands: list) -> str:
    if not cands:
        return ""
    lines = ["\nANCHOR CANDIDATES -- exact spans of the ANCHOR SOURCE above.",
             "  Choose the ONE span your reading rests on and return its id in "
             "`source_anchor_id`.",
             "  You are choosing, not quoting: the system supplies the text for the id "
             "you pick, so do not retype, trim or tidy it.",
             "  Spans from the RESEARCH PACK are NOT eligible -- the anchor must come "
             "from the anchor source.",
             '  If no span below can carry the reading, return "%s" and say why in '
             "`disturbance`." % NO_ANCHOR]
    for c in cands:
        lines.append('  %s  "%s"' % (c["anchor_id"], c["exact_span"]))
    return "\n".join(lines) + "\n"


def resolve(payload: dict, cands: list) -> tuple:
    """(ok, code, detail). Writes `source_anchor_quote` from the MAPPING, never the model.

    Fail closed on every ambiguity: a missing id, an unknown id, an explicit NONE, or an
    empty menu. Any `source_anchor_quote` the model volunteered is discarded before the
    id is read, so model prose can never survive into the authoritative field even if a
    future prompt change starts asking for both.
    """
    from .invariants import (ANCHOR_ID_MISSING, ANCHOR_ID_UNKNOWN, ANCHOR_FIELD,
                             NO_ANCHOR_CANDIDATES, NO_VALID_ANCHOR)
    payload.pop(ANCHOR_FIELD, None)                # model prose is not authoritative

    if not cands:
        return False, NO_ANCHOR_CANDIDATES, "the anchor source yielded no bounded span"

    raw = payload.get("source_anchor_id")
    if not isinstance(raw, str) or not raw.strip():
        return False, ANCHOR_ID_MISSING, "source_anchor_id absent or empty"
    chosen = raw.strip().strip('"\'').upper()

    if chosen == NO_ANCHOR:
        return (False, NO_VALID_ANCHOR,
                "Discovery reported no candidate span could carry the reading")

    hit = [c for c in cands if c["anchor_id"] == chosen]
    if len(hit) != 1:
        return (False, ANCHOR_ID_UNKNOWN,
                "source_anchor_id %r is not one of the %d supplied ids" % (chosen, len(cands)))

    payload["source_anchor_id"] = chosen
    payload[ANCHOR_FIELD] = hit[0]["exact_span"]
    payload["source_anchor_selected"] = True
    return True, "ok", "anchor %s selected from %d candidates (%d chars)" % (
        chosen, len(cands), len(hit[0]["exact_span"]))
