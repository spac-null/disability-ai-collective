"""
human_detail_provenance.py — shadow-only detector for HUMAN-DETAIL PROVENANCE
CLAIMS with absent or unclear grounding (human-detail provenance audit,
2026-08-14, .claude/human-detail-provenance-and-source-completeness-
2026-08-14.md).

Confirmed incidents this closes the gap on, both found live during this
audit, neither caught by any existing mechanism:
- `_posts/2026-05-04-the-floor-plan-they-can-t-read.md` states "Their
  facilitators told me, in a February 2024 call, that..." -- the fetched
  primary source (a Conversation article, verified directly) contains zero
  quotes from any teacher/student/facilitator at all.
- `_posts/2026-05-20-sixty-four-dollars-an-hour-is-museum-language-for-we.md`
  attributes a direct quote to "one manager" at Tacoma Art Museum, "recorded
  in meeting notes I obtained through a public records request" -- the
  fetched primary source (a Hyperallergic article about Seattle Art Museum
  unionizing, verified directly) contains only a collective union-letter
  quote and a CEO quote, nothing about Tacoma, no public-records claim at
  all. This is the sharper of the two: a specific, elaborate, checkable-
  SOUNDING provenance claim attached to a quote that has no relationship to
  the actual fetched source.

SCOPE, DELIBERATELY NARROW (per audit instruction 10/12 -- do not become "no
sentence may exist outside the source"): this targets only claims where the
PERSONA CLAIMS PERSONAL, FIRSTHAND CONTACT with a source -- an interview, a
call, a conversation, a records request -- not citation of an independent,
named, dated third-party publication ("in a 2014 interview with Wired",
"told the Guardian"), which is a lower-risk, already-tolerated citation
pattern and explicitly excluded here. Background/contextual knowledge with
no personal-contact claim is untouched -- governed by existing fact_check
policy, not this module.

Testimony is functional, not a quota (constraint 2 of this pass): this
module does not judge whether an article NEEDS a personal-contact claim,
only whether one that's ALREADY THERE has any relationship to the fetched
evidence. An article with zero personal-contact claims triggers nothing
here, by design -- that is the expected, common, healthy case (confirmed
across this corpus: most articles carry no such claim at all).

SHADOW ONLY. Never blocks. Never feeds _should_block. A missing source_text
(no fetch, or a downgraded fallback_summary) makes every personal-contact
claim in the article BY CONSTRUCTION ungrounded -- reported as
NO_SOURCE_AVAILABLE, not silently skipped, since this is exactly the
Renzo Griffini / Saija Hollmén shape confirmed live in this audit (an
article with no source_url at all, carrying an elaborate claimed personal
interview).
"""
import re

REASON_GROUNDED_QUOTE = "GROUNDED_QUOTE"
REASON_UNGROUNDED_QUOTE = "UNGROUNDED_QUOTE"
REASON_UNVERIFIABLE_PARAPHRASE = "UNVERIFIABLE_PARAPHRASE"
REASON_NO_SOURCE_AVAILABLE = "NO_SOURCE_AVAILABLE"

# Claims the PERSONA had personal, firsthand contact with a source: an
# interview, a call, a conversation, a records request. Deliberately First-
# person ("me"/"I") -- this is what distinguishes "I personally obtained
# this" from a citation of someone else's reporting.
_PERSONAL_CONTACT_RE = re.compile(
    r"\b("
    r"told me|said to me|explained to me|described to me|recalled to me|"
    r"mentioned to me|admitted to me|confided in me|wrote to me|"
    r"i (?:spoke|talked|met) (?:to|with)|"
    r"(?:a|the|our) (?:phone )?call (?:with|to) me|"
    r"(?:records?|notes?|documents?) i obtained|"
    r"an interview i conducted|"
    r"in a call (?:with|to) me"
    r")\b",
    re.IGNORECASE,
)

# Citation of an independent, dated, named third-party publication --
# explicitly excluded (lower risk, already-tolerated pattern; the persona is
# not claiming personal contact, only citing someone else's public record).
# Deliberately CASE-SENSITIVE (no re.IGNORECASE): the [A-Z] here is how this
# distinguishes "told The Guardian" (a named publication) from "told me"
# (a personal-contact claim) -- applying IGNORECASE would make [A-Z] match
# "me" too and silently defeat the whole distinction (found in testing).
_THIRD_PARTY_CITATION_RE = re.compile(
    r"\bin (?:a|an) \d{4} interview with [A-Z]|"
    r"\btold (?:the )?[A-Z][a-zA-Z']+(?: [A-Z][a-zA-Z']+)? (?:in|that|it)\b|"
    r"\bwrote in [A-Z]|"
    r"\bsaid (?:in|during) (?:a|an) \d{4}"
)

_QUOTED_SPAN_RE = re.compile(r'["“‘]([^"”’]{8,})["”’]')

# Context window around a PERSONAL_CONTACT_RE match, wide enough to comfortably
# contain a nearby quotation. NOT sentence-splitting: an earlier version split
# on sentence-ending punctuation first, which silently truncated any quote
# containing its own internal period ('"The system is beautiful. My clients
# cannot find anything."' split into two pieces, losing the closing quote
# mark and misreporting a grounded quote as unverifiable) -- found in testing,
# fixed by windowing over the raw text instead of pre-splitting it.
_CONTEXT_BEFORE_CHARS = 100
_CONTEXT_AFTER_CHARS = 300


def find_personal_contact_claims(article_text):
    """Deterministic harvest: text windows claiming the persona's own personal
    contact with a source, excluding windows that instead cite an
    independent third-party publication. Returns a list of context-window
    strings (deduplicated, order preserved). Never raises."""
    try:
        body = re.sub(r"^---\n.*?\n---\n", "", article_text or "", flags=re.DOTALL)
        body = re.sub(r"<figure[^>]*>.*?</figure>", "", body, flags=re.DOTALL)
        body = re.sub(r"<[^>]+>", "", body)
        candidates = []
        seen = set()
        for m in _PERSONAL_CONTACT_RE.finditer(body):
            window_start = max(0, m.start() - _CONTEXT_BEFORE_CHARS)
            window_end = min(len(body), m.end() + _CONTEXT_AFTER_CHARS)
            window = body[window_start:window_end].strip()
            if _THIRD_PARTY_CITATION_RE.search(window):
                continue
            if window and window not in seen:
                seen.add(window)
                candidates.append(window)
        return candidates
    except Exception:
        return []


def check_provenance(article_text, source_text):
    """For every personal-contact claim found in article_text, classify its
    grounding against source_text. Returns a list of
    {"claim": str, "reason": one of the REASON_* constants,
    "quoted_span": str or None}. Never raises -- an analysis failure
    degrades to an empty list (nothing flagged), never a crash, and never a
    false GROUNDED_QUOTE claim."""
    try:
        claims = find_personal_contact_claims(article_text)
        results = []
        for claim in claims:
            quote_match = _QUOTED_SPAN_RE.search(claim)
            quoted_span = quote_match.group(1).strip() if quote_match else None

            if not source_text:
                results.append({"claim": claim, "reason": REASON_NO_SOURCE_AVAILABLE, "quoted_span": quoted_span})
                continue

            if quoted_span:
                if quoted_span in source_text:
                    results.append({"claim": claim, "reason": REASON_GROUNDED_QUOTE, "quoted_span": quoted_span})
                else:
                    results.append({"claim": claim, "reason": REASON_UNGROUNDED_QUOTE, "quoted_span": quoted_span})
            else:
                # A paraphrased personal-contact claim with no quoted span is
                # structurally unverifiable by exact-match -- surfaced for
                # human attention, never silently passed as grounded.
                results.append({"claim": claim, "reason": REASON_UNVERIFIABLE_PARAPHRASE, "quoted_span": None})
        return results
    except Exception:
        return []
