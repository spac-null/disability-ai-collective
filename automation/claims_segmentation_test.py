#!/usr/bin/env python3
"""Regression for the abbreviation guard in the deterministic sentence backbone.

The guard sits at the whitespace AFTER the terminator, so each negative lookbehind
has to include the period it protects. Written without it, (?<!\bMr) tested the two
characters "r." and could never fire: Mr./Mrs./Dr./St./No. all split anyway, and the
guard was dead code rather than merely incomplete. An independent audit (2026-09-20)
surfaced it through "Gazzetta Ufficiale of 28 February 2026, n. 49.", which split
after "n." and hid the issue number from its own sentence.

These cases pin both halves: abbreviations must not split, and ordinary sentence
endings must still split. Offsets and hashes are checked because the whole backbone
contract is that a span is exactly where it says it is.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
for p in (str(HERE), str(HERE / "new_engine_v1")):
    if p not in sys.path:
        sys.path.insert(0, p)

from new_engine_v1 import claims as CM                              # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else " <- %r" % detail))
    if not ok:
        FAILURES.append(label)


def seg(text):
    return [s["exact_span"] for s in CM.segment(text)]


print("abbreviations must not end a sentence")
GU = ("Law 27 February 2026, n. 26, published in the Gazzetta Ufficiale of "
      "28 February 2026, n. 49. This is the Milleproroghe.")
parts = seg(GU)
check("'n. 49.' stays inside its own sentence",
      len(parts) == 2 and "n. 49." in parts[0], parts)
check("the sentence after it still splits",
      parts[-1] == "This is the Milleproroghe.", parts)
check("Dr.", seg("Dr. Smith arrived early. The room was full.") ==
      ["Dr. Smith arrived early.", "The room was full."])
check("Mr. / Mrs. / St.",
      seg("Mr. Jones and Mrs. Lee met at St. Anne's College. They talked.") ==
      ["Mr. Jones and Mrs. Lee met at St. Anne's College.", "They talked."])
check("No.", seg("See No. 4 below. It explains everything.") ==
      ["See No. 4 below.", "It explains everything."])

print("ordinary endings must still split")
check("plain sentences", seg("The show opened. Nobody came. It closed.") ==
      ["The show opened.", "Nobody came.", "It closed."])
check("question and exclamation",
      seg("Did it work? It did. Remarkable!") ==
      ["Did it work?", "It did.", "Remarkable!"])
check("sentence ending in a year",
      seg("It happened on 28 February 2026. Nobody noticed.") ==
      ["It happened on 28 February 2026.", "Nobody noticed."])
check("quoted opener still splits",
      seg('She left. "Nobody saw her go."') == ['She left.', '"Nobody saw her go."'])

print("numeric punctuation must not be merged or broken")
check("decimals", seg("The value was 3.5 per cent. That is high.") ==
      ["The value was 3.5 per cent.", "That is high."])
check("version numbers", seg("Version 2.1 shipped. Users noticed.") ==
      ["Version 2.1 shipped.", "Users noticed."])
check("a decimal alone does not create a boundary",
      len(seg("The figure of 3.5 was revised to 4.25 later.")) == 1)

print("offsets and hashes stay exact")
ART = ("Dr. Smith read No. 4. The Gazzetta Ufficiale of 28 February 2026, n. 49 "
       "carried it. Nobody noticed.")
sents = CM.segment(ART)
check("verify_backbone clean", CM.verify_backbone(ART, sents) == [],
      CM.verify_backbone(ART, sents))
check("every span sits at its own offsets",
      all(ART[s["start"]:s["end"]] == s["exact_span"] for s in sents))
check("ids are stable and ordered",
      [s["sentence_id"] for s in sents] ==
      ["S%03d" % i for i in range(1, len(sents) + 1)],
      [s["sentence_id"] for s in sents])

print()
if FAILURES:
    print("FAILED %d: %s" % (len(FAILURES), ", ".join(FAILURES)))
    sys.exit(1)
print("ALL SEGMENTATION TESTS PASSED")
