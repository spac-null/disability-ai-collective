#!/usr/bin/env python3
"""worth_lens_particulars_test.py -- a lens must rest on a fact about THIS subject.

MEASURED, on two real ledgers this gate passed identically.

  WildSumaco   85 facts, 3 disability-bearing, lens cited 1  -> published
  Meta/neuro   84 facts, 2 disability-bearing, lens cited 2  -> Reader correctly rejected
                                                                it as wrong publication

Both returned STRONG_DIRECT_LENS, and Meta cited MORE disability evidence than the article
that shipped. So neither density (3.5% vs 2.4%) nor citation count separates them. What
separates them is what the cited facts ARE:

  PARTICULAR  "The field station directory entry for WildSumaco Biological Station records
              ADA accessibility as No."  -- that station's own record; an article can
              stand on it.
  GENERAL     "Cochlear implants restore hearing in people with profound hearing loss and
              are a form of neuroprosthesis."  -- a textbook definition that would appear
              in any article on the subject; it can be a clause, not an argument.

Meta cost nine model calls through Writer, Continuity, Safety, Grounding and Fact Check
before anything noticed. Refusing at Worth costs two.

Stdlib only, no network.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP
from new_engine_v1 import story as ST

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


class Reply:
    def __init__(self, text):
        self.text = text
    def identity(self):
        return {"provider": "scripted", "requested_model": "t", "actual_model": "t",
                "fallback_used": False}


class Scripted:
    model = "test"
    url = "http://127.0.0.1:0/v1"
    def __init__(self, reply):
        self.reply = reply
    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                 deadline=None):
        return Reply(json.dumps(self.reply))


def fact(prop):
    return {"proposition": prop, "support_span": prop, "claim_kind": "STATE",
            "entities": [], "evidence_ids": ["S1"]}


LEDGER = {
    "F01": fact("The pavilion was completed in 2025 at Pacto Sumaco, Ecuador."),
    "F02": fact("The upper level classroom and observatory have no locks."),
    "F03": fact("The floor is lifted clear of the natural ground."),
    # the PARTICULAR -- this subject's own record
    "F90": fact("The field station directory entry for WildSumaco Biological Station "
                "records ADA accessibility as 'No'."),
    # the GENERALS -- true of a whole category
    "F79": fact("Cochlear implants restore hearing in people with profound hearing loss "
                "and are a form of neuroprosthesis."),
    "F80": fact("Brain-machine interfaces are not yet widely used in practical "
                "applications, while holding potential for people with motor disabilities."),
}

CAND = {"story_id": "a-slug", "carrier_type": "object",
        "opening_possibility": "the lifted floor", "real_event_or_change": "it was built",
        "tension": "two registers of who may pass", "reader_first_sees": "a room",
        "reader_later_discovers": "a record",
        "causal_chain": [], "evidence_ids": ["F01", "F02", "F03"]}


def run(worth):
    return CP.worth_gate(Scripted({"worth_gate": worth, "story_candidate": CAND}),
                         LEDGER, "a subject")


print("test_a_META_like_lens_on_definitions_alone_does_NOT_proceed")
try:
    run({"verdict": ST.STRONG_DIRECT_LENS,
         "lens_claim": "Disability is materially in this ledger as neurotechnology's "
                       "origin and its unfinished case.",
         "changes_meaning_how": "the reader sees the field's debt",
         "evidence_ids": ["F79", "F80", "F01"],
         "lens_particulars": []})
    out = "PROCEEDED"
except CP.CompositionHold as e:
    out = "; ".join(e.reasons) if hasattr(e, "reasons") else str(e)
check("it is held, not passed", out != "PROCEEDED", out[:90])
check("the reason names the actual defect",
      "no particular about this subject" in out, out[:160])
check("...and says why a definition cannot carry it",
      "clause but not an article" in out, out[:200])

print("\ntest_a_WILDSUMACO_like_lens_with_one_particular_DOES_proceed")
try:
    res = run({"verdict": ST.STRONG_DIRECT_LENS,
               "lens_claim": "The ledger holds two registers of who may pass: the "
                             "architecture's own, and the directory's.",
               "changes_meaning_how": "openness and access stop being the same word",
               "evidence_ids": ["F02", "F03", "F90"],
               "lens_particulars": ["F90"],
               "lens_carrier": "two registers of who may pass: the lockless room and the "
                               "directory's access field",
               "can_carry_article": "YES"})
    ok, why = res.get("status") == CP.PASS, ""
except CP.CompositionHold as e:
    ok, why = False, "; ".join(getattr(e, "reasons", [str(e)]))
check("one particular is enough to proceed", ok, why[:160])
check("the lens survives intact", ok and res["verdict"] == ST.STRONG_DIRECT_LENS)

print("\ntest_ordinary_refusals_are_unchanged")
for verdict in (ST.WRONG_PUBLICATION, ST.WEAK_ANALOGY,
                ST.NO_PLAUSIBLE_LENS):
    try:
        run({"verdict": verdict, "lens_claim": "considered and it does not hold",
             "changes_meaning_how": "", "evidence_ids": [], "lens_particulars": []})
        out = "PROCEEDED"
    except CP.CompositionHold as e:
        out = "; ".join(getattr(e, "reasons", [str(e)]))
    check("%s still returns cleanly" % verdict,
          "not publishable here" in out, out[:120])
    check("%s is NOT reported as a particulars failure" % verdict,
          "no particular about this subject" not in out,
          "a refusal must keep its own reason")

print("\ntest_no_unrelated_behaviour_changed")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "new_engine_v1", "composition.py")).read()
check("the check lives in worth_gate, not a new stage",
      src.count("def worth_gate(") == 1 and "def viability_gate" not in src)
check("no new model call was added",
      src[src.index("def worth_gate("):src.index("def worth_gate(") + 2000].count("_ask(") == 1)
check("the verdict vocabulary is untouched", len(ST.LENS_VERDICTS) == 5)
check("publishable verdicts are untouched", ST.LENS_PUBLISHABLE ==
      (ST.STRONG_DIRECT_LENS, ST.STRONG_INTERPRETIVE_LENS))
check("an interpretive lens is still reachable -- the publication's central mode",
      "STRONG_INTERPRETIVE_LENS does NOT require the material to mention disability" in src)
check("particulars must be a subset of the lens's own evidence",
      "lens_particulars cites facts the lens does not rest on" in src)
check("a particular not in the ledger does not count",
      'particulars = [f for f in (lens.get("lens_particulars") or []) if f in ledger]' in src)

print("\ntest_an_interpretive_lens_can_still_pass_on_a_particular")
try:
    res = run({"verdict": ST.STRONG_INTERPRETIVE_LENS,
               "lens_claim": "The directory has a field for the body and the building has "
                             "none; each records a different kind of passage.",
               "changes_meaning_how": "the record becomes the subject",
               "evidence_ids": ["F90", "F03"], "lens_particulars": ["F90"],
               "lens_carrier": "the field the directory has and the building has not",
               "can_carry_article": "YES"})
    ok = res.get("status") == CP.PASS
except CP.CompositionHold as e:
    ok = False
check("an interpretive reading on a particular still proceeds", ok,
      "the gate must not become a requirement that articles be ABOUT disability")

print("\n" + "-" * 60)
if FAILURES:
    print("WORTH LENS PARTICULARS: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d WORTH LENS PARTICULARS TESTS PASSED" % CHECKS[0])


# ---------------------------------------------------------------------------
print("\ntest_a_particular_that_cannot_carry_the_article_is_NOT_enough")
# >= 1 particular is necessary, not sufficient. A fact that is genuinely about this
# subject but appears once and is dropped fails the same way a definition does, only
# later -- after the article has been written.
try:
    run({"verdict": ST.STRONG_DIRECT_LENS,
         "lens_claim": "The pavilion's own record carries an access field.",
         "changes_meaning_how": "the reader notices the field",
         "evidence_ids": ["F90", "F01"], "lens_particulars": ["F90"],
         "lens_carrier": "the ADA field in the directory entry",
         "can_carry_article": "NO"})
    out = "PROCEEDED"
except CP.CompositionHold as e:
    out = "; ".join(getattr(e, "reasons", [str(e)]))
check("can_carry_article NO holds the run", out != "PROCEEDED", out[:80])
check("the reason says it would be one incidental sentence",
      "one incidental sentence" in out, out[:200])
check("...and names the carrier it judged", "carrier:" in out, out[:200])

print("\ntest_a_lens_with_no_named_carrier_is_held")
try:
    run({"verdict": ST.STRONG_DIRECT_LENS,
         "lens_claim": "The directory has a field for the body and the building has none, "
                       "so each records a different kind of passage through the same place.",
         "changes_meaning_how": "the record becomes the subject rather than the setting",
         "evidence_ids": ["F90"],
         "lens_particulars": ["F90"], "lens_carrier": "", "can_carry_article": "YES"})
    out = "PROCEEDED"
except CP.CompositionHold as e:
    out = "; ".join(getattr(e, "reasons", [str(e)]))
check("a missing carrier holds the run", out != "PROCEEDED", out[:80])
check("the reason says no carrier was named", "names no carrier" in out, out[:160])

print("\ntest_particulars_must_belong_to_the_lens")
try:
    res = run({"verdict": ST.STRONG_DIRECT_LENS, "lens_claim": "a reading",
               "changes_meaning_how": "x", "evidence_ids": ["F02"],
               "lens_particulars": ["F90"],          # not among evidence_ids
               "lens_carrier": "the record", "can_carry_article": "YES"})
    out = "PROCEEDED"
except CP.CompositionHold as e:
    out = "; ".join(getattr(e, "reasons", [str(e)]))
check("a particular the lens does not rest on is rejected",
      "does not rest on" in out or out != "PROCEEDED", out[:160])

print("\n" + "=" * 60)
if FAILURES:
    print("CARRIER CHECKS FAILED")
    sys.exit(1)
print("CARRIER CHECKS: necessary-not-sufficient enforced")
