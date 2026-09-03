#!/usr/bin/env python3
"""
autopsy.py -- reader-facing diagnostics for a Crip Minds article.

Counts, not verdicts. Every number here is a symptom to look at, never a score to
optimise: the campaign brief is explicit that human reading stays primary and that
literal phrase blacklists are not architecture fixes. What these numbers are good for
is telling you WHERE to read.

Usage:  python3 autopsy.py <article.md> [...]
"""
from __future__ import annotations

import pathlib
import re
import sys

# Machine/provenance language: phrases that describe the RESEARCH rather than the story.
# Diagnostic only. "source" alone is not counted -- a newspaper's own source can be
# story material; it is the auditing constructions that signal a leak.
LEAK = [
    r"\bthe source\b", r"\baccording to the source\b", r"\bthe brief\b",
    r"\bthis reading\b", r"\bthe evidence\b", r"\bdoes not establish\b",
    r"\bdoes not say\b", r"\bdoes not tell us\b", r"\bdoes not report\b",
    r"\bdoes not describe\b", r"\bnothing in the source\b", r"\bthe material\b",
    r"\bon its own wording\b", r"\bI am not claiming\b", r"\bshould be marked as one\b",
]
# Essay-machinery verbs: the "argument visible instead of story movement" symptom.
ESSAY = [r"\bthis reveals\b", r"\bthis reframes\b", r"\bthis complicates\b",
         r"\bwhat becomes visible\b", r"\bthe point is\b", r"\bworth saying\b",
         r"\bthe thing to hold onto\b", r"\bfirst thing to name\b",
         r"\bthe limit is worth stating\b", r"\bheld to that limit\b"]
HEDGE = [r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bappears to\b", r"\bseems to\b",
         r"\bonly as far as\b", r"\bas far as\b", r"\bnot claiming\b", r"\bunclear\b"]

STOP = {"The","A","An","But","And","When","Where","That","This","These","Those","It",
        "In","On","At","For","From","With","By","As","If","Then","There","Here","What",
        "Why","How","Not","No","Nor","So","Yet","Read","Look","Take","Held","Inside",
        "Several","Both","Each","Its","His","Her","Their","One","Two","Three","After",
        "Before","Now","Still","Even","Because","Nothing","Whether","Do","Doing"}


def body(text: str) -> str:
    return text.split("---", 2)[2] if text.startswith("---") else text


def sentences(t: str) -> list:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t.strip()) if s.strip()]


def proper_nouns(t: str) -> set:
    # capitalised tokens not at a sentence start, minus a small function-word stop list
    out = set()
    for s in sentences(t):
        for tok in re.findall(r"\b[A-Z][A-Za-z'’&.-]+\b", s)[1:]:
            if tok not in STOP and len(tok) > 1:
                out.add(tok)
    return out


def hits(t: str, pats: list) -> list:
    found = []
    for p in pats:
        n = len(re.findall(p, t, re.I))
        if n:
            found.append((p.replace(r"\b", ""), n))
    return sorted(found, key=lambda x: -x[1])


def opening_type(t: str) -> str:
    first = " ".join(sentences(t)[:2]).lower()
    if re.search(r"\b(19|20)\d\d\b.*\b(ran|opened|took place|published)\b", first) \
       or re.search(r"^\s*the \w+ edition", first):
        return "press-release/date"
    if re.search(r"\b(the source|according to)\b", first):
        return "research statement"
    if re.search(r"\b(is called|is a|reminds us|shows that|argues)\b", first) \
       and not re.search(r"\b(built|walked|stood|carried|opened|measured|fell|paid)\b", first):
        return "abstract thesis"
    if re.search(r"\b(built|walked|stood|carried|opened|measured|fell|paid|crushed|"
                 r"hatches|travelled|sounded)\b", first):
        return "scene/event/object"
    return "other"


def report(p: pathlib.Path) -> dict:
    t = body(p.read_text())
    s = sentences(t)
    L = [len(x.split()) for x in s] or [0]
    pn = proper_nouns(t)
    d = {
        "case": p.stem[:52],
        "words": len(t.split()),
        "paras": len([x for x in t.split("\n\n") if x.strip()]),
        "sents": len(s),
        "median_sent": sorted(L)[len(L) // 2],
        "max_sent": max(L),
        "over30": sum(1 for x in L if x > 30),
        "proper_nouns": len(pn),
        "numbers": len(re.findall(r"\b\d[\d,.]*\b", t)),
        "leak": sum(n for _, n in hits(t, LEAK)),
        "leak_detail": hits(t, LEAK)[:6],
        "essay": sum(n for _, n in hits(t, ESSAY)),
        "hedge": sum(n for _, n in hits(t, HEDGE)),
        "opening": opening_type(t),
        "final_sent_words": L[-1],
        "pn_list": sorted(pn)[:12],
    }
    return d


def main() -> None:
    rows = [report(pathlib.Path(a)) for a in sys.argv[1:]]
    hdr = ("case", "words", "paras", "sents", "med", "max", ">30", "PN", "num",
           "LEAK", "essay", "hedge", "final")
    print("%-52s %5s %5s %5s %4s %4s %3s %4s %4s %5s %5s %5s %5s" % hdr)
    for r in rows:
        print("%-52s %5d %5d %5d %4d %4d %3d %4d %4d %5d %5d %5d %5d" % (
            r["case"], r["words"], r["paras"], r["sents"], r["median_sent"],
            r["max_sent"], r["over30"], r["proper_nouns"], r["numbers"],
            r["leak"], r["essay"], r["hedge"], r["final_sent_words"]))
    for r in rows:
        print("\n%s\n  opening: %s" % (r["case"], r["opening"]))
        print("  leak   : %s" % (r["leak_detail"] or "none"))
        print("  names  : %s" % ", ".join(r["pn_list"]))


if __name__ == "__main__":
    main()
