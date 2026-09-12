#!/usr/bin/env python3
"""Targeted regression for the sentence-initial-after-title-stripping bug: a leading
blank line between a Markdown heading and the first paragraph must not defeat the
sentence-initial exemption. No provider, no network."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import story as ST  # noqa: E402

FAILURES = []


def check(label, ok, detail=""):
    print(("PASS" if ok else "FAIL") + "  " + label + ("" if ok else " <- %r" % detail))
    if not ok:
        FAILURES.append(label)


packet = {"story_spine": "x", "beats": [], "ending_move": "x", "opening": "",
         "reader_initial_state": "", "turn": "", "crip_turn": "", "lens": "",
         "facts": [], "primary_carrier": "", "evidence_roles": {}, "quotes": [],
         "definitions": {}, "prohibitions": [], "_cut_count": 0}

article1 = "# Title\n\nWhen something happened, it mattered."
r1 = ST.factual_surface_audit(article1, packet)
check("1: blank line between heading and body -- 'When' not flagged",
      "When" not in r1["unapproved_entities"], r1["unapproved_entities"])

article2 = "# Title\nWhen something happened, it mattered."
r2 = ST.factual_surface_audit(article2, packet)
check("2: no blank line either -- 'When' not flagged",
      "When" not in r2["unapproved_entities"], r2["unapproved_entities"])

article3 = "# Title\n\nSomething happened. Then Zanzibar intervened unexpectedly."
r3 = ST.factual_surface_audit(article3, packet)
check("3: a genuinely unsupported mid-sentence entity is still caught",
      "Zanzibar" in r3["unapproved_entities"], r3["unapproved_entities"])

if FAILURES:
    raise SystemExit("FAILED: " + ", ".join(FAILURES))
print("\nALL PASS")
