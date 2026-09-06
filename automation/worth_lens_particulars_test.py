#!/usr/bin/env python3
"""worth_lens_particulars_test.py -- a lens must rest on a fact about THIS subject.

MEASURED, on two real ledgers this gate passed identically.

  WildSumaco   85 facts, 3 disability-bearing, lens cited 1  -> published
  Meta/neuro   84 facts, 2 disability-bearing, lens cited 2  -> Reader correctly rejected
                                                                it as wrong publication

Both returned STRONG_DIRECT_LENS, and Meta cited MORE disability evidence than the article
that shipped. So neither density (3.5% vs 2.4%) nor citation count separates them.

CORRECTED 2026-09-06. This file used to answer "what separates them" with: WildSumaco's
fact was a PARTICULAR (that station's own ADA record) and Meta's were DEFINITIONS. The
first half of that was wrong, and the correction came from the published article, not from
here. The WildSumaco record is a US directory's classification of the STATION; the building
is a 2025 pavilion in Ecuador; nothing in the ledger tied the two. Grounding objected on
five of seven runs, latterly to the ADJACENCY rather than any wording. The claim was
removed from the live piece.

So there are THREE cases, not two, and the third is the dangerous one because it looks
specific:

  PARTICULAR        "McGonigle says the house's flexibility means the clients can close
                    down three of the six blocks."  -- this house's own design decision,
                    in its architect's own account. An article can stand on it.
  GENERAL           "Cochlear implants restore hearing in people with profound hearing
                    loss and are a form of neuroprosthesis."  -- a textbook definition
                    that would appear in any article on the subject; a clause, not an
                    argument.
  NOT THIS SUBJECT  "The field station directory entry for WildSumaco Biological Station
                    records ADA accessibility as No."  -- specific, sourced, and about a
                    different entity under a foreign framework.

WHAT THIS FILE CAN AND CANNOT TEST, stated plainly so nobody reads more into a green run
than it earns. Which facts ARE particulars is the model's judgement, declared in
`lens_particulars`; the validator only checks that a declared particular is in the ledger
and among the lens's own evidence_ids. So this file tests two separable things:

  1. BEHAVIOUR -- the necessary-and-not-sufficient carrier rule, unchanged and not relaxed.
  2. PROMPT SURFACE -- statically, that the doctrine the gate is taught no longer holds the
     WildSumaco record up as the model particular and now names it as an error. Same
     technique contracts.LEGACY_PROMPT_MARKERS already uses.

The MECHANICAL half of the WildSumaco defence is not here and does not claim to be: it is
the ledger's jurisdiction rule (new_engine_v1/jurisdiction.py, jurisdiction_test.py), which
restricts a foreign-framework record to attribution about the record that states it.

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
    # the PARTICULAR -- this subject's own design decision, in its architect's own account
    "F91": fact("McGonigle says the house's flexibility means the clients can close down "
                "three of the six blocks."),
    "F92": fact("The bedrooms sit in separate volumes from the living areas."),
    # NOT THIS SUBJECT -- specific and sourced, about a different entity under a foreign
    # framework. Kept in the ledger deliberately: the failure being guarded against is a
    # lens RESTING on it, not the fact existing.
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

print("\ntest_a_TOLLYMORE_like_lens_with_one_particular_DOES_proceed")
# The requirement is NOT relaxed by the doctrine correction: a genuine subject-specific
# particular -- this house's own design decision, in its architect's own account -- still
# passes on its own.
try:
    res = run({"verdict": ST.STRONG_DIRECT_LENS,
               "lens_claim": "The house's flexibility is the ability to switch parts of "
                             "itself off, while the route to bed stays outside.",
               "changes_meaning_how": "flexible stops meaning the same thing for every body",
               "evidence_ids": ["F92", "F03", "F91"],
               "lens_particulars": ["F91"],
               "lens_carrier": "closing three of six blocks while the bedrooms stay in "
                               "separate volumes",
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

print("\ntest_the_taught_doctrine_no_longer_holds_up_the_WildSumaco_record")
# STATIC, on the prompt surface itself -- the same technique
# contracts.LEGACY_PROMPT_MARKERS uses. Which facts are particulars is a model judgement,
# so the only place this correction can live is in what the model is taught.
_doc = CP.WORTH_SYSTEM
_ada_at = _doc.find("records ADA accessibility as No")
check("the WildSumaco ADA record is still discussed", _ada_at > 0,
      "deleting it silently would lose the lesson")
_window_before = _doc[max(0, _ada_at - 400):_ada_at]
check("it is no longer introduced as the PARTICULAR",
      "PARTICULAR  'The field station directory entry" not in _doc,
      "the positive exemplar must be gone, not merely reworded")
check("it is introduced as NOT THIS SUBJECT", "NOT THIS SUBJECT" in _window_before,
      _window_before[-120:])
check("the prompt says why -- a different entity",
      "classification of the STATION" in _doc, "the wrong-entity half must be named")
check("the prompt says why -- a foreign framework",
      "framework of a country the building is not in" in _doc,
      "the foreign-framework half must be named")
check("the prompt generalises past this one case",
      "neighbouring, parent or broader entity" in _doc,
      "a rule about ADA alone would not transfer")
check("the prompt names the adjacency failure",
      "invites a third conclusion no source supports" in _doc,
      "both sentences can be accurate and the placement still wrong")

print("\ntest_the_positive_exemplar_is_a_real_subject_specific_particular")
check("a genuine particular is taught in its place",
      "close down three of the six blocks" in _doc)
check("...and is described as belonging to the subject",
      "this house's own design decision" in _doc)
check("the definition example is retained unchanged",
      "Cochlear implants restore hearing" in _doc and "GENERAL " in _doc)
check("all three cases are presented together",
      "Three real examples" in _doc)

print("\ntest_the_particular_requirement_is_not_weakened")
_src_gate = CP.WORTH_SYSTEM
check("a lens must still rest on >= 1 subject-specific fact",
      "A lens has to rest on at least one fact that is ABOUT THIS SUBJECT" in _src_gate)
check("a definition still cannot carry an article",
      "cannot carry an article, however true it is" in _src_gate)
check("refusing is still free",
      "cost nothing" in _src_gate)

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
               "lens_claim": "A house that can switch three of its six parts off has a "
                             "plan for shrinking, and none for the route between them.",
               "changes_meaning_how": "the design's own flexibility becomes the subject",
               "evidence_ids": ["F91", "F92"], "lens_particulars": ["F91"],
               "lens_carrier": "what the flexibility closes and what it leaves outside",
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
         "lens_claim": "The house can be made smaller by closing part of itself.",
         "changes_meaning_how": "the reader notices the arithmetic",
         "evidence_ids": ["F91", "F01"], "lens_particulars": ["F91"],
         "lens_carrier": "the three blocks that can be closed",
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
