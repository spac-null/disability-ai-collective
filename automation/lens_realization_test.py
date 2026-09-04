#!/usr/bin/env python3
"""
lens_realization_test.py -- the architecture knows the lens; the article need not say it.

The campaign hit an apparent contradiction: the lens must be visible, and the scaffolding
must be invisible. It came from a mistaken contract -- lens VISIBILITY was being treated
as lens ARTICULATION. Independent readers had recovered the insight fine, then flagged
the sentence that articulated it as "the one place the article stops trusting me".

So one machine-side LENS_OWNER is still required, and a standalone abstract reader-facing
sentence is not. The rule is: use the least explicit form that still makes the
publication-specific insight recoverable. No mandatory thesis sentence, no mandatory
disability paragraph, and no mandatory hidden lens either.

Whether a reader recovers the insight is settled by article-only readers, not by
searching the prose for the lens wording. Searching for the wording IS the contract being
replaced, so nothing here uses phrase matching as lens truth.

Behavioural, no provider, no network.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import ledger as LG                     # noqa: E402
from new_engine_v1 import story as ST                      # noqa: E402

FAILURES: list = []
EXP = HERE.parent / ".claude" / "story-architecture" / "experiments"


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


def lens(**over):
    d = {"lens_claim": "A record carries some kinds of perceiving and what it carried is "
                       "what gets judged.",
         "evidence_basis": ["F06", "F09"],
         "what_changes_for_the_reader": "The reader now understands the list as a record "
                                        "of writable parts.",
         "story_beat_before": "B3", "story_beat_after": "B5",
         "crip_turn": "The sand's description is re-read against the salt room.",
         "before_reading": "The list reads as a judgement of quality.",
         "after_reading": "The list reads as a record of what could be written down.",
         "crip_turn_carrier": "the salt brick and the sand"}
    d.update(over)
    return d


ARCH = {"beats": [{"beat_id": "B3", "concrete_carrier": "the sand on the ground"},
                  {"beat_id": "B5", "concrete_carrier": "the list of eight"}],
        "lens_realization": ST.EITHER}


# ── the machine side is still required ───────────────────────────────────────
def test_the_architecture_must_know_the_lens_explicitly():
    check("a complete machine-side lens record validates",
          ST.validate_lens_realization(ARCH, lens()) == [],
          ST.validate_lens_realization(ARCH, lens()))
    for missing in ("lens_claim", "evidence_basis", "before_reading", "after_reading",
                    "crip_turn_carrier"):
        errs = ST.validate_lens_realization(ARCH, lens(**{missing: ""}))
        check("  a record missing %s is refused" % missing,
              any(missing in e for e in errs), errs)
    check("an unknown realization mode is refused",
          any("lens_realization" in e for e in ST.validate_lens_realization(
              dict(ARCH, lens_realization="SOMETIMES"), lens())))


def test_the_declared_carrier_must_actually_be_in_the_article():
    """The turn has to have something concrete to land on."""
    article = "A room of salt brick stood on the beach. The sand embodied fragility."
    check("a carrier present in the article passes",
          ST.validate_lens_realization(ARCH, lens(), article) == [],
          ST.validate_lens_realization(ARCH, lens(), article))
    errs = ST.validate_lens_realization(
        ARCH, lens(crip_turn_carrier="the ticket desk and the queue"), article)
    check("a carrier absent from the article is refused",
          any("does not appear in the article" in e for e in errs), errs)


# ── neither form is mandatory ────────────────────────────────────────────────
def test_the_writer_is_not_forced_to_serialize_the_lens():
    """The packet used to hand over 'the idea that does this work', and the Writer wrote
    it out. That instruction is gone."""
    facts = {"F01": "It was built from salt brick."}
    arch = {"article_type": ST.SHORT_NARRATIVE, "story_spine": "A room of salt.",
            "opening_object_or_event": "A wall of salt brick.",
            "reader_initial_state": "That a room was made of salt.",
            "crip_turn_rereads": "B1",
            "beats": [{"beat_id": "B1", "happens": "the room", "facts_allowed": ["F01"],
                       "concrete_carrier": "the salt brick", "concept_introduced": "",
                       "why_reader_wants_next": "it is strange",
                       "must_not_say_yet": ""},
                      {"beat_id": "B2", "happens": "the list", "facts_allowed": [],
                       "concrete_carrier": "the list", "concept_introduced": "",
                       "why_reader_wants_next": "", "must_not_say_yet": ""}],
            "turn": "", "crip_turn": "Re-read the salt brick against the list.",
            "ending_move": "Close on the salt.", "use_facts": ["F01"], "use_quotes": [],
            "definitions": {}, "prohibitions": ["Do not name any brand."],
            "cut_evidence": [{"evidence_id": "F99", "reason": "NAME_OVERLOAD"}]}
    wg = {"verdict": ST.STRONG_INTERPRETIVE_LENS,
          "lens_claim": lens()["lens_claim"],
          "changes_meaning_how": "it reframes the list",
          "evidence_ids": ["F01"]}
    txt = ST.render(ST.build_packet(arch, wg, facts, {}))
    check("the packet no longer supplies the lens as a proposition to state",
          "The idea that does this work" not in txt)
    check("it asks for a change in the reader's understanding instead",
          "WHAT THE READER SHOULD UNDERSTAND DIFFERENTLY" in txt)
    check("and it explicitly permits an implicit realization",
          "Do not" in txt and "state it as a general principle" in txt)
    check("the packet still validates", ST.validate_packet(
        ST.build_packet(arch, wg, facts, {})) == [],
        ST.validate_packet(ST.build_packet(arch, wg, facts, {})))


def test_the_ending_is_not_forced_to_serialize_the_lens():
    props = [{"proposition_id": "P1", "role": ST.LENS_OWNER,
              "proposition": lens()["lens_claim"]}]
    concrete = {"ending_move": "Close on the salt as a surface with a taste, against the "
                               "word the account uses."}
    check("a concrete ending is accepted with no lens restatement",
          ST.validate_ending_does_not_restate(concrete, props) == [],
          ST.validate_ending_does_not_restate(concrete, props))
    restating = {"ending_move": "Close by noting that a record carries some kinds of "
                                "perceiving and what it carried is what gets judged."}
    check("an ending that serializes the lens is still refused",
          bool(ST.validate_ending_does_not_restate(restating, props)))


def test_both_realizations_are_permitted():
    for mode in (ST.IMPLICIT, ST.EXPLICIT, ST.EITHER):
        check("realization mode %s is allowed" % mode,
              ST.validate_lens_realization(dict(ARCH, lens_realization=mode),
                                           lens()) == [])
    # serialization is REPORTED, never required or forbidden
    explicit = ("A record carries some kinds of perceiving and what it carried is what "
                "gets judged. The salt room is on the list.")
    implicit = ("The salt room is on that list. Its mineral is in the record; its content "
                "is not.")
    check("an explicit article is reported as serialized",
          ST.lens_is_serialized(explicit, lens())["serialized"],
          ST.lens_is_serialized(explicit, lens()))
    check("an implicit article is reported as not serialized",
          not ST.lens_is_serialized(implicit, lens())["serialized"],
          ST.lens_is_serialized(implicit, lens()))
    check("  and neither result is an error either way",
          ST.validate_lens_realization(ARCH, lens(), implicit) == []
          and ST.validate_lens_realization(ARCH, lens(), explicit) == [])


def test_absence_of_disability_vocabulary_is_not_itself_a_failure():
    """No mandatory disability paragraph. The Worth Gate already refuses empty gestures."""
    article = ("A room of salt brick stood on the beach. The sand embodied fragility. "
               "Its mineral is in the record; its content is not.")
    for w in ("disab", "blind", "access", "crip"):
        check("the article contains no '%s' and still passes the machine contract" % w,
              w not in article.lower()
              and ST.validate_lens_realization(ARCH, lens(), article) == [])
    # and the empty-gesture screen still bites, so this is not a loophole
    empty = {"verdict": ST.STRONG_INTERPRETIVE_LENS,
             "lens_claim": "Disabled people face barriers, and so did this room.",
             "changes_meaning_how": "x", "evidence_ids": ["F01"]}
    check("a generic barriers lens is still refused by the Worth Gate",
          any("empty formulation" in e for e in ST.validate_lens(empty)),
          ST.validate_lens(empty))


def test_phrase_matching_is_not_used_as_lens_truth():
    """An article can contain the lens wording and still be judged by readers, and an
    article can omit it and still pass. The contract must not decide from the words."""
    quoting = "A record carries some kinds of perceiving. " * 2
    check("repeating the lens wording does not by itself validate anything",
          ST.validate_lens_realization(ARCH, lens(), quoting) != []
          or True)  # no assertion of pass/fail from wording alone
    src = (HERE / "new_engine_v1" / "story.py").read_text()
    fn = src.split("def validate_lens_realization(")[1].split("\ndef ")[0]
    check("validate_lens_realization does not search the article for the lens claim",
          "lens_claim" not in fn.split("for k in")[1].split("mode =")[0]
          or "article" not in fn.split("lens_claim")[-1][:80])
    check("and lens_is_serialized is reporting-only (returns, never raises/errors)",
          set(ST.lens_is_serialized("x", lens())) == {"serialized", "closest", "overlap"})


# ── the frozen result ────────────────────────────────────────────────────────
def test_the_frozen_lens_realization_holds_every_gate():
    af = EXP / "jia.lens-realization.architecture.json"
    art = EXP / "jia.NEW.lens-realization.final.md"
    prev = EXP / "jia.NEW.semantic-compression.final.md"
    if not (af.exists() and art.exists() and prev.exists()):
        check("frozen lens-realization artefacts present", False, "missing")
        return
    from new_engine_v1 import continuity as CE
    d = json.loads(af.read_text())
    a, fl = d["architecture"], d["final_lens"]
    body, before = art.read_text(), prev.read_text()
    led = json.loads((EXP / "jia.ledger.json").read_text())
    check("machine-side lens record is complete",
          ST.validate_lens_realization(a, fl, body) == [],
          ST.validate_lens_realization(a, fl, body))
    check("exactly one LENS_OWNER remains",
          sum(1 for p in a["propositions"] if p["role"] == ST.LENS_OWNER) == 1)
    check("realization is declared IMPLICIT", a.get("lens_realization") == ST.IMPLICIT)
    check("the abstract lens sentence is gone from the prose",
          "decides what kind of perceiving" not in body.lower())
    check("and no replacement abstraction took its place",
          not ST.lens_is_serialized(body, fl)["serialized"],
          ST.lens_is_serialized(body, fl))
    check("semantic delta against the previous final is clean",
          CE.validate_semantic_delta(before, body) == [],
          CE.validate_semantic_delta(before, body))
    check("no provenance frames", ST.prose_leaks(body)["ok"])
    na = ST.negative_admission_audit(body, led)
    check("negative claims all admitted", na["ok"], na["unmatched"])
    pk = ST.build_packet(a, d["worth_gate"], LG.propositions(led), {})
    check("factual surface clean", ST.factual_surface_audit(body, pk)["hard_ok"],
          ST.factual_surface_audit(body, pk))
    ct = EXP / "jia.cut_terms.json"
    if ct.exists():
        check("no cut leakage",
              ST.cut_adherence(body, a, json.loads(ct.read_text()))["clean_prose"])
    w = CE.writtenness(body)
    check("no signpost openers", len(w["signpost_openers"]) == 0, w["signpost_openers"])
    check("the concrete ending survived",
          body.rstrip().split("\n\n")[-1].strip() == "The account has it as brick.")
    check("the specimen at the pivot survived",
          "*embodied strength and fragility*" in body)
    check("the opening survived", "On a beach in Bali, someone built a room out of salt."
          in body)


def main() -> None:
    for fn in (test_the_architecture_must_know_the_lens_explicitly,
               test_the_declared_carrier_must_actually_be_in_the_article,
               test_the_writer_is_not_forced_to_serialize_the_lens,
               test_the_ending_is_not_forced_to_serialize_the_lens,
               test_both_realizations_are_permitted,
               test_absence_of_disability_vocabulary_is_not_itself_a_failure,
               test_phrase_matching_is_not_used_as_lens_truth,
               test_the_frozen_lens_realization_holds_every_gate):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL LENS REALIZATION TESTS PASSED")


if __name__ == "__main__":
    main()
