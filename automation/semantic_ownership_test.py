#!/usr/bin/env python3
"""
semantic_ownership_test.py -- one idea, one semantic owner.

The last defect in the Jia final was created upstream of the prose. The article stated a
single insight five times, climbing:

  "The account keeps what the sand was said to mean and loses what it was to stand on it."
  "That is the shape of the whole record."
  "It holds the meanings and drops the encounters."
  "A record decides what kind of perceiving it can carry."
  "Then whatever it carried becomes the thing anyone downstream can weigh."

Two independent readers found it without prompting and both said the same thing: the
paragraphing *is* the scaffolding, and the beats are countable. The Continuity Editor
could not fix it, because each restatement was a declared beat, and deleting a beat is a
semantic decision. So it is fixed here.

One finding is recorded in the tests themselves: word overlap is nearly useless for this
job. The two Jia abstractions share ZERO content words and an overlap test scores them
0.00. The load-bearing check is structural -- more than one ABSTRACT proposition means
the article explains itself twice, whatever words each uses.

Behavioural, no provider, no network.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import story as ST                      # noqa: E402
from new_engine_v1 import continuity as CE                 # noqa: E402

FAILURES: list = []
EXP = HERE.parent / ".claude" / "story-architecture" / "experiments"
CARRIERS = {"salt", "sand", "room", "walls", "brick", "water", "list", "account",
            "pavilion", "mineral"}


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


def P(pid, role, text, **kw):
    d = {"proposition_id": pid, "role": role, "proposition": text}
    d.update(kw)
    return d


EVID = P("P1", ST.EVIDENCE, "Across all eight descriptions, none reports what any "
                            "visitor perceived.", supported_by=["F09"])
OWNER = P("P3", ST.LENS_OWNER, "A record decides what kind of perceiving it can carry, "
                               "and what it carried is what anyone downstream can weigh.")


# ── the required mutations (campaign section 18) ─────────────────────────────
def test_two_beats_cannot_own_the_same_lens_proposition():
    """1: two LENS_OWNERs -> HOLD, compression required."""
    dup = [EVID, OWNER, P("P4", ST.LENS_OWNER, "It holds the meanings and drops the "
                                               "encounters.")]
    errs = ST.validate_propositions(dup)
    check("1 two LENS_OWNER propositions are refused",
          any("exactly one semantic owner" in e for e in errs), errs)
    check("  and both are named", "P3" in str(errs) and "P4" in str(errs), errs)


def test_a_second_abstraction_is_caught_even_with_no_shared_words():
    """8: the same lens duplicated under different wording.

    This is the finding that made the structural test necessary: these two say one thing
    and share nothing lexically.
    """
    a = "It holds the meanings and drops the encounters."
    b = "A record decides what kind of perceiving it can carry."
    check("word overlap scores the two Jia abstractions at ~0",
          ST.restates(a, b) < 0.2, ST.restates(a, b))
    dup = [EVID, P("P3", ST.LENS_OWNER, a), P("P4", ST.CONSEQUENCE, b, adds="nothing new")]
    r = ST.semantic_redundancy(dup, carriers=CARRIERS)
    check("8 but the structural check still catches the duplication",
          not r["ok"] and any(f["kind"] == "MULTIPLE_ABSTRACTIONS" for f in r["flagged"]),
          r)
    check("  and it reports how many abstractions there are", r["abstract_count"] == 2,
          r["abstract_count"])


def test_turn_and_crip_turn_may_collapse():
    """2: if both encode the same movement, they are one prose beat."""
    same = {"turn": "What a medium can hold becomes what is judged downstream.",
            "crip_turn": "A medium carries certain kinds of perceiving and those become "
                         "the judgeable ones."}
    r = ST.collapse_turn_and_crip_turn(same, [], carriers=CARRIERS)
    check("2 two abstractions of one movement are told to collapse", r["collapse"], r)
    check("  and the reason names the abstraction test", r["both_abstract"], r)
    distinct = {"turn": "The festival ended and the pavilions came down.",
                "crip_turn": "A record carries only some kinds of perceiving."}
    r2 = ST.collapse_turn_and_crip_turn(distinct, [], carriers=CARRIERS)
    check("  a concrete event plus an abstraction stays separate", not r2["collapse"], r2)


def test_the_ending_may_embody_but_not_explain():
    """3 and 4."""
    arch_bad = {"ending_move": "Close by restating that a record decides what kind of "
                               "perceiving it can carry."}
    errs = ST.validate_ending_does_not_restate(arch_bad, [EVID, OWNER])
    check("3 an ending restating the lens is refused",
          any("restates the lens" in e for e in errs), errs)
    for bad in ("Therefore the record is partial.",
                "In other words, the record is partial.",
                "What this shows is that records are partial."):
        check("  a summarising ending (%s) is refused" % bad.split()[0],
              bool(ST.validate_ending_does_not_restate({"ending_move": bad},
                                                       [EVID, OWNER])))
    good = {"ending_move": "Close on the salt as a surface with a taste, set against the "
                           "word the account uses for it."}
    check("4 a concrete callback ending is accepted",
          ST.validate_ending_does_not_restate(good, [EVID, OWNER]) == [],
          ST.validate_ending_does_not_restate(good, [EVID, OWNER]))
    check("  a missing ending is still refused",
          bool(ST.validate_ending_does_not_restate({}, [EVID, OWNER])))


def test_evidence_and_lens_may_share_a_topic():
    """5: same subject, different roles, both allowed."""
    props = [EVID, OWNER]
    check("5 evidence plus one lens owner validates",
          ST.validate_propositions(props) == [], ST.validate_propositions(props))
    r = ST.semantic_redundancy(props, carriers=CARRIERS)
    check("  and is not flagged as redundant", r["ok"], r["flagged"])
    # Worth stating plainly: these two DO share a topic and share almost no vocabulary,
    # which is exactly why the role contract rather than word overlap is the control.
    check("  and word overlap between them is near zero, as expected",
          ST.restates(EVID["proposition"], OWNER["proposition"]) < 0.2,
          ST.restates(EVID["proposition"], OWNER["proposition"]))


def test_a_consequence_must_add_something():
    """6: a real consequence is allowed; a paraphrase wearing the role is not."""
    real = P("P4", ST.CONSEQUENCE,
             "The salt room is on that list, described by the part of itself that could "
             "be written down.",
             adds="the outcome for this pavilion specifically", supported_by=["F11"])
    check("6 a consequence that states what is new validates",
          ST.validate_propositions([EVID, OWNER, real]) == [],
          ST.validate_propositions([EVID, OWNER, real]))
    lazy = P("P4", ST.CONSEQUENCE, "So the record is partial.")
    check("  a consequence that says nothing new is refused",
          any("paraphrase wearing a role" in e
              for e in ST.validate_propositions([EVID, OWNER, lazy])))
    cb = P("P5", ST.CALLBACK, "The account has it as brick.")
    check("  a callback with no named carrier is refused",
          any("must name the concrete carrier" in e
              for e in ST.validate_propositions([EVID, OWNER, cb])))


def test_removing_the_only_lens_owner_fails():
    """7."""
    errs = ST.validate_propositions([EVID])
    check("7 zero lens owners is refused",
          any("not zero" in e or "no LENS_OWNER" in e for e in errs), errs)


def test_schema_fields_cannot_force_redundant_prose():
    """9: an empty field creates no obligation."""
    a = {"turn": "", "crip_turn": "A record carries only some kinds of perceiving.",
         "ending_move": "Close on the salt."}
    r = ST.collapse_turn_and_crip_turn(a, [], carriers=CARRIERS)
    check("9 an empty turn creates no prose obligation",
          not r["collapse"] and "only one of the two" in r["reason"], r)
    check("  and the architecture is still valid with turn empty",
          "turn" not in str(ST.validate_ending_does_not_restate(a, [EVID, OWNER])))


def test_beats_may_shrink_while_story_order_holds():
    """10."""
    before = ("A room was built of salt. It held fragrances. The account lists eight. "
              "None reports a perception.")
    draft = CE.label_draft(before)
    edits = [{"id": "E001", "parents": ["D001", "D002"], "operation": CE.MERGE,
              "text": "A room was built of salt, and it held fragrances.",
              "paragraph_break": True},
             {"id": "E002", "parents": ["D003", "D004"], "operation": CE.MERGE,
              "text": "The account lists eight, and none reports a perception."}]
    check("10 four sentences become two with lineage intact",
          CE.validate_lineage(edits, draft) == [], CE.validate_lineage(edits, draft))
    out = CE.apply_edits(edits)
    check("  story order is preserved", out.index("salt") < out.index("eight"))
    check("  and no semantic delta", CE.validate_semantic_delta(before, out) == [],
          CE.validate_semantic_delta(before, out))
    check("  every input sentence is still accounted for",
          set().union(*[set(e["parents"]) for e in edits]) == set(draft))


# ── the frozen compressed result ─────────────────────────────────────────────
def test_the_frozen_compression_holds_every_gate():
    af = EXP / "jia.compressed.architecture.json"
    art = EXP / "jia.NEW.semantic-compression.final.md"
    prev = EXP / "jia.NEW.continuity.final.md"
    if not (af.exists() and art.exists() and prev.exists()):
        check("frozen compression artefacts present", False, "missing")
        return
    d = json.loads(af.read_text())
    a, props = d["architecture"], d["architecture"]["propositions"]
    body, before = art.read_text(), prev.read_text()
    check("exactly one LENS_OWNER",
          sum(1 for p in props if p["role"] == ST.LENS_OWNER) == 1)
    check("propositions validate", ST.validate_propositions(props) == [],
          ST.validate_propositions(props))
    r = ST.semantic_redundancy(props, carriers=CARRIERS)
    check("no semantic redundancy", r["ok"], r["flagged"])
    check("exactly one abstraction remains", r["abstract_count"] == 1, r["abstract_count"])
    check("the ending does not restate the lens",
          ST.validate_ending_does_not_restate(a, props) == [],
          ST.validate_ending_does_not_restate(a, props))
    check("turn was collapsed, not duplicated", not (a.get("turn") or "").strip())
    check("  and the collapse is recorded", a.get("turn_collapsed_into") == "crip_turn")
    check("no architect rhetoric", CE.validate_architect_is_semantic(a) == [],
          CE.validate_architect_is_semantic(a))
    check("semantic delta against the previous final is clean",
          CE.validate_semantic_delta(before, body) == [],
          CE.validate_semantic_delta(before, body))
    w0, w1 = CE.writtenness(before), CE.writtenness(body)
    check("signpost openers reached zero (was %d)" % len(w0["signpost_openers"]),
          len(w1["signpost_openers"]) == 0, w1["signpost_openers"])
    check("paragraphs reduced (%d -> %d)" % (w0["paragraphs"], w1["paragraphs"]),
          w1["paragraphs"] < w0["paragraphs"])
    check("the opening survived untouched",
          body.split("\n\n")[1].startswith("On a beach in Bali, someone built a room out "
                                           "of salt."))
    check("the quoted specimen survived",
          "*embodied strength and fragility*" in body)
    check("the closing line still stands alone",
          body.rstrip().split("\n\n")[-1].strip() == "The account has it as brick.")
    # the abstraction really is stated once
    low = body.lower()
    check("the lens is articulated exactly once",
          low.count("decides what kind of perceiving") == 1, low.count("perceiving"))
    check("and the earlier duplicate abstractions are gone",
          "holds the meanings and drops the encounters" not in low
          and "shape of the whole record" not in low)


def main() -> None:
    for fn in (test_two_beats_cannot_own_the_same_lens_proposition,
               test_a_second_abstraction_is_caught_even_with_no_shared_words,
               test_turn_and_crip_turn_may_collapse,
               test_the_ending_may_embody_but_not_explain,
               test_evidence_and_lens_may_share_a_topic,
               test_a_consequence_must_add_something,
               test_removing_the_only_lens_owner_fails,
               test_schema_fields_cannot_force_redundant_prose,
               test_beats_may_shrink_while_story_order_holds,
               test_the_frozen_compression_holds_every_gate):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL SEMANTIC OWNERSHIP TESTS PASSED")


if __name__ == "__main__":
    main()
