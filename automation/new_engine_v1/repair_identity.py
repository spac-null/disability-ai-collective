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

# ── the three states. Every one of them HOLDs. ───────────────────────────────
#
# There is no residual-versus-introduced distinction here, and an earlier draft of this
# file was wrong to attempt one. It separated them by whether the repaired text carried a
# number or proper noun the article had not contained -- which claims semantic
# proposition identity from a lexical token class, and is false in both directions.
# "the water is suitable for irrigation" becoming "the water is safe to drink" introduces
# an entirely new factual claim and adds neither a number nor a name; and a target
# reworded with a new figure has not necessarily become a different proposition.
#
# From an article diff alone, three things are provable and no more: the repair touched
# this unsupported text, it did not touch it, or we cannot establish which.
REPAIR_AFFECTED = "REPAIR_AFFECTED_UNSUPPORTED"
RECLASSIFIED = "RECLASSIFIED_UNSUPPORTED"
UNRESOLVED = "UNRESOLVED_REPAIR_IDENTITY"
STATES = (REPAIR_AFFECTED, RECLASSIFIED, UNRESOLVED)

_SENT_END = re.compile(r"(?<=[.!?])\s+")


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


def _normalise_with_map(text: str) -> tuple:
    """Whitespace-collapsed text plus, for every character in it, the offset it came
    from. The map is what makes the fallback safe: a match is mapped back to the exact
    original range it was found at, never re-derived from word anchors that could land
    on a different occurrence."""
    out, idx, prev_space = [], [], False
    for i, ch in enumerate(text):
        if ch.isspace():
            if prev_space or not out:
                continue
            out.append(" ")
            idx.append(i)
            prev_space = True
        else:
            out.append(ch)
            idx.append(i)
            prev_space = False
    return "".join(out), idx


def locate(quote: str, text: str) -> dict:
    """Where a finding's quote sits in the article. Exact, and unique or nothing.

    A quote that appears more than once cannot be attributed to one occurrence, and
    choosing one to get a tidier category is exactly the guess this module exists to
    refuse.

    The fallback exists because a grounder may re-wrap a quote it copied verbatim. It
    matches the COMPLETE normalised quote against the COMPLETE normalised article,
    requires exactly one occurrence, and maps that one range back through the index map.
    No fuzzy matching, no partial anchors, no similarity.
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
    flat_t, imap = _normalise_with_map(text)
    flat_q = " ".join(q.split())
    if not flat_q:
        return {"ok": False, "reason": "finding carries no quote"}
    n2 = flat_t.count(flat_q)
    if n2 == 1:
        s0 = flat_t.index(flat_q)
        e0 = s0 + len(flat_q)
        return {"ok": True, "start": imap[s0], "end": imap[e0 - 1] + 1,
                "basis": "whitespace_normalised"}
    if n2 > 1:
        return {"ok": False,
                "reason": "quote occurs %d times after re-wrapping; no unique span" % n2}
    return {"ok": False, "reason": "quote is not present in the repaired article"}


def _overlaps(a: tuple, spans: list) -> bool:
    return any(a[0] < e and s < a[1] for (s, e) in spans)


def classify_finding(quote: str, before: str, after: str, spans: dict) -> dict:
    """One pass-2 TRUE_UNSUPPORTED finding -> exactly one provable repair state."""
    if not spans.get("ok"):
        return {"state": UNRESOLVED, "why": spans.get("reason", "changed spans unknown")}
    loc = locate(quote, after)
    if not loc["ok"]:
        return {"state": UNRESOLVED, "why": loc["reason"]}
    span = (loc["start"], loc["end"])
    if _overlaps(span, spans["inserted"]) or _overlaps(span, spans["sentences"]):
        # The repair touched this text. Whether the unsupported content is the old
        # target still unsupported, the target reworded, or a proposition the repair
        # created is NOT decidable from a diff, and this state deliberately does not
        # say. It holds either way.
        return {"state": REPAIR_AFFECTED,
                "why": "overlaps text the repair changed", "span": span,
                "basis": loc["basis"]}
    if quote_unchanged(quote, before, after, span):
        return {"state": RECLASSIFIED,
                "why": "wholly in article text that existed before the repair and was "
                       "not changed by it", "span": span, "basis": loc["basis"]}
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

    Three counts, each of them something the article diff actually establishes. The
    pre-#58 `residual` and `introduced` keys are deliberately NOT carried forward: they
    named a distinction this layer cannot prove, and the only thing that ever read them
    was this engine's own decision layer and one of its tests.
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
            "span_basis": r.get("basis", ""),
            # Recorded because it is a fact about pass 1, not because it decides
            # anything: attribution comes from the article, never from a classification.
            "was_pass1_unsupported": (f.get("quote") in target_quotes),
        })
    counts = {s: sum(1 for r in records if r["state"] == s) for s in STATES}
    return {
        "repair_affected_unsupported": counts[REPAIR_AFFECTED],
        "reclassified_unsupported": counts[RECLASSIFIED],
        "unresolved_repair_identity": counts[UNRESOLVED],
        "unrelated_edits": 0 if spans.get("ok") else 1,
        "changed_spans_ok": bool(spans.get("ok")),
        "changed_spans_reason": spans.get("reason", ""),
        "inserted_spans": [list(s) for s in spans.get("inserted", [])],
        "findings": records,
    }
