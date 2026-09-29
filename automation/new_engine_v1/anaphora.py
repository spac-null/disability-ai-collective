"""Facts whose cited span points at source material no other fact extracted.

TELEMETRY, NOT A GATE. Deliberately. This detector was built from the case that produced
it -- production-20260928T070709Z-9b443d22, where the article's own subject was missing --
and a rule calibrated on its own sample has already been falsified once in this project.
It records what it finds and blocks nothing. Whether it should ever become authority is a
question for a held-out measurement, not for the run that discovered it.

WHAT IT LOOKS FOR

A support span that opens on a demonstrative is a fragment: "one of THESE sheets", "both
of THESE patterns", "the answers to SUCH questions". It is only a fact if something else
establishes what the demonstrative points at. When nothing does, the Ledger has kept the
statement ABOUT a thing and dropped the statement SAYING WHAT THE THING IS -- and no
existing gate notices, because they all ask whether the prose is carried by the Ledger and
none asks whether the Ledger covers the source.

The confirmed case:

    span         "Prinzhorn bildet eines dieser Blaetter in seinem Buch ab, allerdings
                  auf dem Kopf stehend, mit einer falschen Autorenzuweisung ..."
    preceding    "... sind die Briefe von Emma Hauck. Sie wiederholt in diesen so oft das
                  bittende 'Herzensschatzi komm' ... dass sich eine Grauschwaerzung der
                  Flaeche ergibt."   <- in the source, cited by nothing

Re-freezing the same pack under the same code recovered it, so this is an omission rather
than an incapacity.

MEASURED ACROSS THE CORPUS, 2026-09-29: 100 retained runs, 8,866 facts. 16 runs carried an
orphaned fact; 4 of those facts had been selected into an article. All four were the same
shape -- a fact about a SET whose members were never extracted.

THE TEST IS STRUCTURAL, AND A LEXICAL ONE DOES NOT WORK. Matching the demonstrative's head
noun against the other propositions fails on this corpus because spans are the source's
own language and propositions are English: the span says "Blaetter" where the fact that
would establish it says "letters". So the question is asked of the SOURCE -- locate the
span, look at the characters before it, and ask whether any other fact is drawn from them.
"""

from __future__ import annotations

import html
import re

# Backward-pointing demonstratives in the languages this corpus contains. Bare definite
# articles are excluded: German "das"/"die" are usually articles, and including them makes
# the signal worthless.
_DEMONSTRATIVE = r"""
    dieser|diese|dieses|diesen|diesem|
    jener|jene|jenes|jenen|jenem|
    solche[rnms]?|derartige[rnms]?|
    these|those|such
"""
# At the OPENING of the span only. A demonstrative in the middle usually has its
# antecedent inside the same span, which makes the span self-contained.
OPENS_ON = re.compile(
    r"^\W{0,3}(?:\w+\s+){0,4}?\b(?:%s)\b\s+(\w{3,})" % _DEMONSTRATIVE, re.I | re.X)

# How far back an antecedent may sit: about two sentences. Far enough to reach the line
# naming the thing, short enough that an unrelated fact a paragraph earlier does not count.
LOOKBACK_CHARS = 400


def source_texts(pack: dict) -> dict:
    """source_id -> text, accepting the retained envelope or the bare pack."""
    if pack and "sources" not in pack and isinstance(pack.get("payload"), dict):
        pack = pack["payload"]
    return {s.get("source_id"): (s.get("text") or "")
            for s in ((pack or {}).get("sources") or []) if s.get("source_id")}


def _facts(ledger: dict) -> dict:
    """Retained LEDGER.json is not uniformly a map of fact objects -- some runs carry
    scalar metadata beside the facts. Filtered by SHAPE, so a new metadata key added
    later does not break a corpus sweep."""
    return {k: v for k, v in (ledger or {}).items()
            if isinstance(v, dict) and (v.get("support_span") or v.get("proposition"))}


def _locate(span: str, sources: dict) -> tuple:
    for sid, text in sources.items():
        for candidate in (span, html.unescape(span)):
            if candidate and candidate in text:
                return sid, text.index(candidate)
        un = html.unescape(text)
        target = html.unescape(span)
        if target and target in un:
            return sid, un.index(target)
    return None, -1


def orphaned_spans(ledger: dict, pack: dict, selected=()) -> list:
    """Facts whose span opens on a demonstrative nothing else in the ledger establishes."""
    sources = source_texts(pack)
    facts = _facts(ledger)
    if not sources or not facts:
        return []

    placed = {}
    for fid, fact in facts.items():
        span = str(fact.get("support_span") or "")
        sid, off = _locate(span, sources)
        if sid is not None:
            placed[fid] = (sid, off, off + len(span))

    selected = set(selected or ())
    out = []
    for fid, fact in facts.items():
        span = str(fact.get("support_span") or "")
        m = OPENS_ON.search(html.unescape(span))
        if not m or fid not in placed:
            continue
        sid, start, _end = placed[fid]
        lo = max(0, start - LOOKBACK_CHARS)
        if any(o != fid and osid == sid and oend > lo and ostart < start
               for o, (osid, ostart, oend) in placed.items()):
            continue
        out.append({
            "fact_id": fid,
            "selected": fid in selected,
            "span_opens_on": m.group(0)[:70].strip(),
            # Sliced from the RAW text and unescaped after: offsets come from a find on
            # the stored bytes, and unescaping changes the string's length, so slicing an
            # unescaped copy with those offsets walks forward and prints part of the span
            # itself as the material before it.
            "uncited_before_it": html.unescape(sources[sid][lo:start]).strip()[-240:],
            "proposition": str(fact.get("proposition") or "")[:200],
        })
    return out
