#!/usr/bin/env python3
"""A claim the evidence can refuse, proposed before the evidence exists.

WHY THE ORDER MATTERS, measured rather than argued. Worth ran AFTER the ledger was
frozen and asked what reading could be found in the pile, so the lens could only
DESCRIBE the pile -- a report by construction. Three separately measured defects follow
from that one ordering:

    register   SOUNDS_LIKE_REPORT is the owner's most-pressed reaction, 7 of 10 sessions
    density    4.7 proper nouns per 100 words against 3.0 in this publication's own
               published articles, in 25% less space -- with no claim, every fact is
               equally admissible and nothing selects
    joins      one unlicensed join survived five independent controls in a single day,
               because the Writer was manufacturing tension the pipeline never supplied

Each assertion below refuses a shape that is NOT a hypothesis. None of them judges
whether a claim is true: that is what the run is for, and a refuted claim is a real
outcome and often the better story.

Run: python3 automation/hypothesis_first_test.py
"""

from __future__ import annotations

import inspect
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as C      # noqa: E402
from new_engine_v1 import hypothesis as H       # noqa: E402
import knowledge_first as KF                    # noqa: E402

SUBJECT = "The Prinzhorn collection's historical inventory book"
REAL = {"claim": "The inventory book recorded a person's diagnosis more completely than "
                 "it recorded their name",
        "refuted_if": "the list gives full surnames throughout",
        "matters_because": "it shows what the archive was built to hold"}

FAILED: list = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILED.append(name)


def main() -> int:
    check("a claim that could be false is accepted",
          H.validate(REAL, SUBJECT) == [], str(H.validate(REAL, SUBJECT)))

    for name, mutate in (
        ("a topic with no verb is not a claim",
         {"claim": "The inventory book of the Prinzhorn collection in Heidelberg"}),
        ("a question has no truth value to test",
         {"claim": "What did the inventory book actually record about people?"}),
        ("a claim with no stated way to be wrong",
         {"refuted_if": ""}),
        ("a claim that merely restates its subject",
         {"claim": "The historical inventory book of the Prinzhorn collection is an "
                   "inventory book"}),
        ("a true claim nobody is changed by", {"matters_because": ""}),
        ("a refutation that restates the claim",
         {"refuted_if": REAL["claim"]}),
        ("a claim too short to assert anything", {"claim": "It was recorded"}),
    ):
        errs = H.validate(dict(REAL, **mutate), SUBJECT)
        check("refused: " + name, errs != [], "accepted something that is not a claim")

    check("a non-object is refused rather than crashing",
          H.validate("a claim, as a string") != [])

    # ── how later stages receive it ───────────────────────────────────────────
    blk = H.block(REAL)
    check("the block labels it as UNPROVED", "NOT established" in blk,
          "the engine's posture is that nothing unproved may be asserted, and a "
          "hypothesis is unproved by definition")
    check("and says refusal is a real outcome", "refuse it" in blk)
    check("an empty hypothesis renders nothing", H.block({}) == "")
    check("so does a malformed one", H.block("not a dict") == "")

    # ── the wiring ────────────────────────────────────────────────────────────
    # THE CLAIM IS NOT INVENTED. An earlier version of this file asserted that
    # commissioning ASKS a model for a hypothesis. It should not: 48 approved instruments
    # each carry a MECHANISM -- the claim itself -- and 43 carry a DISCONFIRMING SHAPE
    # saying what would refute it, and both were being loaded and parsed past. The claim
    # was always the owner's; it was being thrown away and then asked for again.
    check("the schema does NOT ask a model to invent a claim",
          '"hypothesis"' not in KF.COMMISSION_SCHEMA,
          "the claim belongs to the instrument, not to a model")

    instruments = KF.load_questions()
    check("every approved instrument yields a claim",
          all(H.from_instrument(q) for q in instruments),
          "%d of %d" % (sum(1 for q in instruments if H.from_instrument(q)),
                        len(instruments)))
    one = H.from_instrument(instruments[0])
    check("the claim is the instrument's own MECHANISM",
          one["claim"] == instruments[0]["mechanism"])
    check("and its refutation the DISCONFIRMING SHAPE",
          one["refuted_if"] == instruments[0].get("disconfirming_shape", ""))
    check("and it records which instrument it came from",
          one["instrument"] == instruments[0]["id"])
    check("an instrument with no mechanism yields nothing",
          H.from_instrument({"id": "PRX-01"}) == {})

    # THE INSTRUMENT'S OTHER GUARDS REACH THE PROPOSER
    check("CARRIERS is loaded", all(q.get("carriers") for q in instruments))
    check("FALSE MOVE is loaded", all(q.get("false_move") for q in instruments))
    src = __import__("inspect").getsource(KF.propose_stories)
    check("the proposer is given what can carry the question", "carriers" in src)
    check("and the wrong version the owner named", "false_move" in src)

    src = inspect.getsource(C.worth_gate)
    check("Worth can be given the claim",
          "hypothesis" in inspect.signature(C.worth_gate).parameters)
    check("Worth renders it through the one function that labels it",
          "HYP.block" in src)

    # BACKWARD COMPATIBLE BY CONSTRUCTION. Every run before this, and any run whose
    # commission carries no claim, must send the prompt it sent before the parameter
    # existed -- an empty block is the empty string, so the join adds nothing.
    check("no claim means the Worth prompt is unchanged", H.block({}) == "",
          "an absent hypothesis must not alter a single byte of the old prompt")

    print("-" * 62)
    if FAILED:
        print("FAILED: %d" % len(FAILED))
        for f in FAILED:
            print("   - " + f)
        return 1
    print("all hypothesis-first checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
