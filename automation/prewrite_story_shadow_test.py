#!/usr/bin/env python3
"""prewrite_story_shadow_test.py -- the shadow has no authority, and OFF means absent.

A shadow that can change a production decision is not a shadow. These checks are the
whole contract: nothing when the flag is unset, exactly one call when it is set, and a
malformed or failing reply costs the composition nothing.
"""
import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import prewrite_story_shadow as PSS   # noqa: E402

FAILED = []


def check(name, cond):
    print("  %s  %s" % ("PASS" if cond else "FAIL", name))
    if not cond:
        FAILED.append(name)


LEDGER = {
    "F01": {"proposition": "The facilitator holds the alphabet board up in the air."},
    "F02": {"proposition": "The facilitator decides whether a letter was selected."},
}
ARCH = {"story_spine": "A board is held up and someone else decides what was chosen.",
        "opening_object_or_event": "the alphabet board",
        "primary_carrier": "F02",
        "ending_move": "Lands on the two decisions.",
        "definitions": {"letterboarding": "spelling on a held board"},
        "beats": [{"beat_id": "B1", "beat_function": "REVEAL",
                   "concrete_carrier": "the board", "happens": "It is held up.",
                   "facts_allowed": ["F01"]}]}
WORTH = {"story_candidate": {"subject": "letterboarding"},
         "worth_gate": {"lens_claim": "who decides what was said"}}
PACK = {"subject": "letterboarding"}

GOOD = {
    "theme_statement": "who is allowed to have said something",
    "central_question": "who chose the letter",
    "concrete_entry": {"description": "the held board", "fact_ids": ["F01"]},
    "reader_promise": "how a message gets attributed",
    "discovery_arc": [{"beat_id": "B1", "before": "nothing", "after": "the board",
                       "move": "REVEALS", "fact_ids": ["F01"]}],
    "load_bearing_concepts": [{"concept": "letterboarding", "why_load_bearing": "the mechanism",
                               "plain_language_meaning": "spelling on a held board",
                               "evidence_fact_ids": ["F01"], "status": "READY"}],
    "grounding_readiness": [{"planned_element": "the two decisions",
                             "status": "EVIDENCE_BACKED", "fact_ids": ["F02"]}],
    "crip_minds_turn": "assistance can become authorship",
    "why_carrier_reveals_it": "the decision is visible at the board",
    "research_budget": {"load_bearing": ["F01"], "credibility_once": [],
                        "provenance_only": [], "cuttable": []},
    "landing": {"reader_at_start": "a drawing", "reader_at_end": "a decision",
                "changed_understanding": "who spoke", "lands": "YES"},
    "argument_readiness": "ARGUMENT_READY",
    "cut_before_writing": [],
    "risks": [],
}


class Calls:
    def __init__(self, reply):
        self.n, self.reply = 0, reply

    def __call__(self, system, user):
        self.n += 1
        if isinstance(self.reply, Exception):
            raise self.reply
        self.last_user = user
        return self.reply


print("OFF IS ABSENT")
os.environ.pop(PSS.ENV_FLAG, None)
check("enabled() is False when the flag is unset", PSS.enabled() is False)
c = Calls(GOOD)
with tempfile.TemporaryDirectory() as d:
    out = PSS.run(c, PACK, LEDGER, WORTH, ARCH, out_dir=d)
    check("run() returns None", out is None)
    check("zero calls are made", c.n == 0)
    check("no artifact is written", list(pathlib.Path(d).iterdir()) == [])
for v in ("0", "off", "false", "no", ""):
    os.environ[PSS.ENV_FLAG] = v
    check("flag %r is OFF" % v, PSS.enabled() is False)

print("\nON IS EXACTLY ONE CALL, AND ONLY A FILE")
os.environ[PSS.ENV_FLAG] = "1"
check("enabled() is True", PSS.enabled() is True)
c = Calls(GOOD)
with tempfile.TemporaryDirectory() as d:
    out = PSS.run(c, PACK, LEDGER, WORTH, ARCH, out_dir=d)
    check("exactly one call", c.n == 1)
    check("status OK", out.get("status") == "OK")
    check("authority is ZERO", out.get("authority") == "ZERO")
    check("records that no prose exists", out.get("article_not_written_yet") is True)
    f = pathlib.Path(d) / "PREWRITE_STORY_SHADOW.json"
    check("artifact persisted", f.exists())
    check("artifact is valid json", isinstance(json.loads(f.read_text()), dict))
    check("no verdict field of any kind",
          not any(k in out for k in ("pass", "hold", "verdict", "score",
                                     "publishable", "recommendation")))

print("\nTHE SHADOW SEES ONLY FROZEN PRE-WRITING MATERIAL")
check("the prompt carries the plan", "THE PLAN" in c.last_user)
check("the prompt carries the frozen facts", "FROZEN FACTS" in c.last_user)
# The probe is about OUTCOME leakage, not vocabulary: the schema legitimately uses the
# word "verdict" to forbid one. What must never reach the shadow is the article, or what
# a later gate said about it.
for leak in ("READER_AUDIT", "ACCESSIBLE_READING", "RESEARCH_LOAD", "MOMENTUM",
             "ARTICLE_FINAL", "one_line"):
    check("the prompt does not leak %r" % leak, leak not in c.last_user)
check("the prompt carries no prose surface",
      not any(k in c.last_user for k in ("WRITER_DRAFT", "CONTINUITY_FINAL")))

print("\nFAILURE IS NEVER BLOCKING")
c = Calls(RuntimeError("provider unavailable"))
with tempfile.TemporaryDirectory() as d:
    out = PSS.run(c, PACK, LEDGER, WORTH, ARCH, out_dir=d)
    check("a provider error returns an artifact, not an exception",
          isinstance(out, dict) and out.get("status") == "FAILED")
c = Calls({"theme_statement": "x"})          # malformed: missing nearly everything
with tempfile.TemporaryDirectory() as d:
    out = PSS.run(c, PACK, LEDGER, WORTH, ARCH, out_dir=d)
    check("a malformed reply is marked INVALID", out.get("status") == "INVALID")
    check("and its errors are recorded", bool(out.get("validation_errors")))

print("\nFACT IDS ARE CHECKED AGAINST THE FROZEN LEDGER")
bad = json.loads(json.dumps(GOOD))
bad["concrete_entry"]["fact_ids"] = ["F99"]
errs = PSS.validate(bad, LEDGER)
check("an invented fact id invalidates the artifact",
      any("F99" in e for e in errs))
bad2 = json.loads(json.dumps(GOOD))
bad2["discovery_arc"][0]["move"] = "IS_GREAT"
check("an undeclared move is refused",
      any("move" in e for e in PSS.validate(bad2, LEDGER)))
bad3 = json.loads(json.dumps(GOOD))
bad3["landing"]["lands"] = "PROBABLY"
check("an undeclared landing verdict is refused",
      any("lands" in e for e in PSS.validate(bad3, LEDGER)))
check("the good artifact validates clean", PSS.validate(GOOD, LEDGER) == [])

print("\nTHE SCHEMA CANNOT EXPRESS A GATE")
for forbidden in ("PASS", "HOLD", "score", "publishable"):
    check("schema offers no %r field" % forbidden,
          ('"%s"' % forbidden) not in PSS.SCHEMA)

os.environ.pop(PSS.ENV_FLAG, None)
print("\n" + "-" * 62)
if FAILED:
    print("FAILED: %d" % len(FAILED))
    for f in FAILED:
        print("   - %s" % f)
    sys.exit(1)
print("ALL PREWRITE STORY SHADOW TESTS PASSED")
