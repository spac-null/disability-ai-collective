#!/usr/bin/env python3
"""
repair_identity.py -- which pass-2 unsupported findings the repair actually caused.

WHY THIS EXISTS
The repair verifier used to say "the repair introduced this unsupported claim" whenever a
pass-2 TRUE_UNSUPPORTED quote was absent from the set of pass-1 TRUE_UNSUPPORTED quotes.
That is not what it measured. On production-20260903T135702Z-3ea6156a one sentence was
patched -- "some 33,000 litres" became "most of it" -- and two OTHER findings came back
unsupported on the second pass. Both sentences were byte-identical before and after, and
both sat outside the patched span. One of them had been LEGITIMATE_INTERPRETATION on pass
1 with a reason that, on pass 2, still ended "not unsupported after all". The article was
held for claims the repair had created, and the repair had created neither.

So the question is answered from the ARTICLE, not from the classifications: the repair is
a deterministic clause substitution and its changed regions are therefore computable. A
pass-2 finding either overlaps text the repair wrote, or it does not.

WHAT THIS DOES NOT DO
It does not make anything publishable. All four states below HOLD, including the one that
means "we could not tell". It does not read the classifier's prose, does not re-judge a
verdict, does not call a model, and does not soften the grounder. The only thing that
changes is which of four true statements the run makes about itself.
"""
from __future__ import annotations

import re

# ── the four states. Every one of them HOLDs. ────────────────────────────────
RESIDUAL = "RESIDUAL_UNSUPPORTED"
INTRODUCED = "INTRODUCED_UNSUPPORTED"
RECLASSIFIED = "RECLASSIFIED_UNSUPPORTED"
UNRESOLVED = "UNRESOLVED_REPAIR_IDENTITY"
STATES = (RESIDUAL, INTRODUCED, RECLASSIFIED, UNRESOLVED)

# A "new fact" for attribution purposes: a number, or a capitalised word that is not the
# first word of a sentence. Deterministic, and the same shape the grounding tests already
# use for new-number/new-quote guards. It never decides a VERDICT -- only whether text the
# repair wrote carries factual material the article did not previously contain.
_NUMBER = re.compile(r"\d[\d,.]*")
_PROPER = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b")
_SENT_END = re.compile(r"(?<=[.!?])\s+")


def _factual_tokens(text: str) -> set:
    return set(_NUMBER.findall(text or "")) | set(_PROPER.findall(text or ""))


def changed_spans(before: str, after: str, patches: list) -> dict:
    """Replay the deterministic patches and report what the repair wrote.

    Returns {"ok": bool, "inserted": [(start, end)], "sentences": [(start, end)],
             "reason": str} in AFTER-article coordinates.

    `inserted` is the text the repair itself wrote. `sentences` are the whole sentences
    those insertions land in, which is the granularity a deletion has to be judged at: a
    removal writes no characters of its own, and the sentence around it is still text the
    repair materially changed.

    ok=False when the replay does not reproduce `after` exactly. That is not a small
    discrepancy to work around -- it means the recorded patches are not what happened, and
    nothing downstream may be attributed.
    """
    text, inserted = before, []
    for p in (patches or []):
        removed = p.get("removed") or ""
        ins = p.get("inserted")
        if ins is None:
            return {"ok": False, "inserted": [], "sentences": [],
                    "reason": "patch %r has no inserted text" % p.get("finding_id")}
        if not removed:
            return {"ok": False, "inserted": [], "sentences": [],
                    "reason": "patch %r removed nothing; span is undefined"
                              % p.get("finding_id")}
        i = text.find(removed)
        if i < 0:
            return {"ok": False, "inserted": [], "sentences": [],
                    "reason": "patch %r: removed text is not in the article at replay"
                              % p.get("finding_id")}
        delta = len(ins) - len(removed)
        end_old = i + len(removed)
        # Shift spans recorded earlier that sit after this edit.
        inserted = [(s + delta if s >= end_old else s,
                     e + delta if e >= end_old else e) for (s, e) in inserted]
        inserted.append((i, i + len(ins)))
        text = text[:i] + ins + text[end_old:]
    if text != after:
        return {"ok": False, "inserted": [], "sentences": [],
                "reason": "replaying the recorded patches does not reproduce the "
                          "repaired article"}
    return {"ok": True, "inserted": _merge(inserted),
            "sentences": _merge([_sentence_bounds(after, s, e) for (s, e) in inserted]),
            "reason": ""}


def _merge(spans: list) -> list:
    out = []
    for s, e in sorted(spans):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return [tuple(x) for x in out]


def _sentence_bounds(text: str, start: int, end: int) -> tuple:
    """The sentence(s) a span sits in, by the same terminator rule elsewhere."""
    left = 0
    for m in _SENT_END.finditer(text):
        if m.end() <= start:
            left = m.end()
        else:
            break
    right = len(text)
    for m in _SENT_END.finditer(text):
        if m.start() >= end:
            right = m.start()
            break
    return (left, max(right, end))


def locate(quote: str, text: str) -> dict:
    """Where a finding's quote sits in the article. Exact, and unique or nothing.

    A quote that appears more than once cannot be attributed to one occurrence, and
    choosing one to get a tidier category is exactly the guess this module exists to
    refuse. Whitespace is normalised for the search only -- never to match a DIFFERENT
    string -- because a grounder may re-wrap a quote it copied verbatim.
    """
    q = (quote or "").strip()
    if not q:
        return {"ok": False, "reason": "finding carries no quote"}
    n = text.count(q)
    if n == 1:
        i = text.index(q)
        return {"ok": True, "start": i, "end": i + len(q), "basis": "exact"}
    if n > 1:
        return {"ok": False, "reason": "quote occurs %d times; no unique span" % n}
    # one collapsed-whitespace attempt, on the same characters
    flat_q = " ".join(q.split())
    flat_t = " ".join(text.split())
    n2 = flat_t.count(flat_q)
    if n2 == 1:
        # Map back conservatively: locate the first and last words in the real text.
        words = flat_q.split()
        if words:
            first, last = re.escape(words[0]), re.escape(words[-1])
            m = re.search(first + r"[\s\S]{0,%d}?" % (len(q) + 80) + last, text)
            if m:
                return {"ok": True, "start": m.start(), "end": m.end(),
                        "basis": "whitespace_normalised"}
        return {"ok": False, "reason": "quote matches only after re-wrapping and its "
                                       "span could not be mapped back"}
    if n2 > 1:
        return {"ok": False, "reason": "quote occurs %d times after re-wrapping" % n2}
    return {"ok": False, "reason": "quote is not present in the repaired article"}


def _overlaps(a: tuple, spans: list) -> bool:
    return any(a[0] < e and s < a[1] for (s, e) in spans)


def classify_finding(quote: str, before: str, after: str, spans: dict) -> dict:
    """One pass-2 TRUE_UNSUPPORTED finding → exactly one repair state."""
    if not spans.get("ok"):
        return {"state": UNRESOLVED, "why": spans.get("reason", "changed spans unknown")}
    loc = locate(quote, after)
    if not loc["ok"]:
        return {"state": UNRESOLVED, "why": loc["reason"]}
    span = (loc["start"], loc["end"])
    text = after[span[0]:span[1]]
    if _overlaps(span, spans["inserted"]):
        # The unsupported content sits in text the repair itself wrote. Whether that is
        # the target's proposition reworded or a fresh one is not decidable from the
        # characters -- but a factual token the article did not previously contain is.
        new_facts = sorted(_factual_tokens(text) - _factual_tokens(before))
        if new_facts:
            return {"state": INTRODUCED, "why": "in text the repair wrote, carrying "
                                                "factual material absent from the "
                                                "pre-repair article: %s"
                                                % ", ".join(new_facts[:4]),
                    "span": span, "new_factual_tokens": new_facts[:8]}
        return {"state": RESIDUAL, "why": "in the repair target's own rewritten span, "
                                          "still unsupported", "span": span}
    if _overlaps(span, spans["sentences"]):
        return {"state": INTRODUCED,
                "why": "in a sentence the repair materially changed", "span": span}
    if quote_unchanged(quote, before, after, span):
        return {"state": RECLASSIFIED,
                "why": "wholly in article text that existed before the repair and was "
                       "not changed by it", "span": span}
    return {"state": UNRESOLVED,
            "why": "outside every changed span, but the same text could not be found "
                   "unchanged in the pre-repair article"}


def quote_unchanged(quote: str, before: str, after: str, span: tuple) -> bool:
    """The span's own characters existed, unchanged, before the repair.

    Checked against the pre-repair article directly rather than against pass 1's finding
    list: a classification is not evidence about what the text was, and a quote whose
    boundary drifted by one word between passes -- "and the first useful one..." versus
    "the first useful one..." -- is the same unchanged sentence either way.
    """
    text = after[span[0]:span[1]]
    if text and text in before:
        return True
    flat = " ".join(text.split())
    return bool(flat) and flat in " ".join(before.split())


def account(before: str, after: str, patches: list, pass1: list, pass2: list) -> dict:
    """The repair verification record.

    `residual` keeps its name and its blocking power but now means only what it says:
    the repair target's own span, still unsupported. `introduced` likewise means text the
    repair actually wrote. Everything the old arithmetic mislabelled lands in
    `reclassified`, and anything that cannot be established lands in `unresolved`.
    All four hold.
    """
    spans = changed_spans(before, after, patches)
    target_quotes = {f.get("quote") for f in (pass1 or [])
                     if f.get("classification") == "TRUE_UNSUPPORTED"}
    records = []
    for f in (pass2 or []):
        if f.get("classification") != "TRUE_UNSUPPORTED":
            continue
        r = classify_finding(f.get("quote") or "", before, after, spans)
        records.append({
            "id": f.get("id"),
            "quote": f.get("quote"),
            "state": r["state"],
            "why": r["why"],
            "span": list(r.get("span") or []),
            "was_pass1_unsupported": (f.get("quote") in target_quotes),
            **({"new_factual_tokens": r["new_factual_tokens"]}
               if r.get("new_factual_tokens") else {}),
        })
    counts = {s: sum(1 for r in records if r["state"] == s) for s in STATES}
    return {
        "residual": counts[RESIDUAL],
        "introduced": counts[INTRODUCED],
        "reclassified": counts[RECLASSIFIED],
        "unresolved": counts[UNRESOLVED],
        "unrelated_edits": 0 if spans.get("ok") else 1,
        "changed_spans_ok": bool(spans.get("ok")),
        "changed_spans_reason": spans.get("reason", ""),
        "inserted_spans": [list(s) for s in spans.get("inserted", [])],
        "findings": records,
    }
