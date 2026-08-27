#!/usr/bin/env python3
"""
title_coherence.py -- does a headline actually describe the article underneath it?

The failure this exists for, from a real natural run
(production-20260827T070010Z-fd846f06): the source was a Dezeen roundup headlined
"Gravity-powered mountain trike among projects from the University of Ljubljana".
Discovery selected a different project from that roundup -- a layered tactile exhibition
system -- and the article was written entirely about it. The writer emitted no headline,
so the candidate silently inherited the source's, and shipped an article about tactile
booklets under a headline about a mountain trike. Nothing in the pipeline noticed,
because nothing was comparing the two.

The check is deliberately generic: no article-specific vocabulary, no topic list, no
model call. A headline that describes its article shares vocabulary with it. A headline
carried over from a roundup names things the article never mentions. So: take the
headline's content words, and count how many appear nowhere in the body.

Inflection is handled by a shared-prefix match rather than a stemmer, so "galleries"
matches "gallery" and "exposed" matches "exposure" without a dependency.

This module reports. It does not gate publication, and it is not part of the
publication-safety bridge.
"""
from __future__ import annotations

import re

_WORD = re.compile(r"[a-z0-9']+")

# Ordinary English function words. Nothing here is specific to any article or subject.
_STOP = frozenset("""
a an the and or but of in on at to for from by with without as is are was were be been
being this that these those it its into over under about among between across after
before during than then so such can could may might will would shall should must not no
nor if when while where how what which who whom whose you your we our they their them us
he she his her him me my i one two three new more most less least own same other another
each every all any both few many much some just also only even still yet there here now
than via per up out off down through against upon within toward towards along around
""".split())

_MIN_LEN = 3          # shorter tokens carry no topical signal
_PREFIX = 5           # shared-prefix length that counts as the same word family


def content_words(text: str) -> list[str]:
    """Topical words, in order, with duplicates preserved."""
    return [w for w in _WORD.findall((text or "").lower())
            if w not in _STOP and len(w) >= _MIN_LEN]


def _present(word: str, body_words: set[str]) -> bool:
    if word in body_words:
        return True
    if len(word) < _PREFIX:
        return False
    pre = word[:_PREFIX]
    return any(b.startswith(pre) for b in body_words if len(b) >= _PREFIX)


def analyse(title: str, body: str) -> dict:
    """Which of the headline's topical words the article never mentions."""
    terms = content_words(title)
    body_words = set(content_words(body))
    stray = [w for w in terms if not _present(w, body_words)]
    total = len(terms)
    return {"terms": total, "stray": stray, "stray_count": len(stray),
            "stray_ratio": (len(stray) / total) if total else 0.0}


def is_coherent(title: str, body: str, *,
                max_stray_ratio: float = 0.34, max_stray: int = 2) -> bool:
    """True when the headline plausibly describes the body.

    Both bounds must be exceeded to call a headline incoherent. Up to two unmatched
    words are tolerated, because a real headline routinely carries a verb or a framing
    noun the body never repeats ("Reveals", "Nobody"); what marks an inherited headline
    is that the SUBJECT itself is missing -- three or more absent terms making up more
    than a third of the headline. A headline with no topical words cannot be judged and
    is not rejected here.
    """
    a = analyse(title, body)
    if a["terms"] == 0:
        return True
    return not (a["stray_count"] > max_stray and a["stray_ratio"] > max_stray_ratio)


def describe(title: str, body: str) -> str:
    """One-line reason, for logs."""
    a = analyse(title, body)
    return ("%d of %d headline terms appear nowhere in the article (%s)"
            % (a["stray_count"], a["terms"], ", ".join(a["stray"][:6]) or "none"))
