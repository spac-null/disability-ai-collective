#!/usr/bin/env python3
"""
ledger_and_lens_test.py -- factual permissions come from evidence; stages cannot mint them.

Two demonstrated failures from the campaign are the reason this file exists.

THE "pink" INCIDENT. A colour was hand-written into the Story Architect's `turn` field.
The writer packet is built FROM the architecture, so the packet carried "pink", and the
post-writer audit compares prose to the packet -- so it certified the fabrication as
approved. A stage that writes prose into the packet can mint factual ground truth.

THE ROMAN ENDING. "the part that was not engineered" claims that no receiving-end tooling
exists. The frozen evidence contains no negative evidence at all about the receiving end
(archive 0, tool 0, storage 0, bandwidth 0). It passed every screen because the screens
looked for unapproved numbers, names, colours and props, and an absence is none of those.

So: silence is not evidence of absence, and no story stage authors a fact.

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

EVIDENCE = ("The Oaken Tiltroom was constructed from Himalayan salt bricks from Tuscany "
            "Stone Boutique, the pavilion was partially embedded into the ground. Inside, "
            "the pavilion featured fragrances, with the aim of engaging all senses. "
            "Here are eight of the most interesting.")


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


def fact(**kw):
    return LG.make_fact(**kw)


BASE = {"F01": fact(fact_id="F01", proposition="It was built from salt brick.",
                    claim_type=LG.POSITIVE, evidence_ids=["S0"],
                    support_span="constructed from Himalayan salt bricks",
                    prohibited_extensions=["colour", "how it was laid"]),
        "F02": fact(fact_id="F02", proposition="It was partially embedded in the ground.",
                    claim_type=LG.POSITIVE, evidence_ids=["S0"],
                    support_span="partially embedded into the ground",
                    prohibited_extensions=["floor level", "depth", "steps"])}


# ── the ledger is the only origin of factual permission ──────────────────────
def test_a_fact_needs_a_verbatim_span_in_the_evidence():
    check("a well-supported fact validates", LG.validate_ledger(BASE, EVIDENCE) == [],
          LG.validate_ledger(BASE, EVIDENCE))
    bad = fact(fact_id="F03", proposition="The walls were pink.",
               claim_type=LG.POSITIVE, evidence_ids=["S0"],
               support_span="the walls were pink")
    errs = LG.validate_fact(bad, EVIDENCE)
    check("a fact whose span is not in the evidence is refused",
          any("not verbatim in the evidence" in e for e in errs), errs)
    nospan = fact(fact_id="F04", proposition="It was cold inside.",
                  claim_type=LG.POSITIVE, evidence_ids=["S0"])
    check("a fact with no span at all is refused",
          any("no support_span" in e for e in LG.validate_fact(nospan, EVIDENCE)))
    noev = fact(fact_id="F05", proposition="It was built from salt brick.",
                claim_type=LG.POSITIVE, evidence_ids=[],
                support_span="constructed from Himalayan salt bricks")
    check("a fact with no evidence id is refused",
          any("no evidence_ids" in e for e in LG.validate_fact(noev, EVIDENCE)))
    check("an interpretation may have no span but must name its evidence",
          LG.validate_fact(fact(fact_id="F06", proposition="A selection is not a count.",
                                claim_type=LG.INTERPRETATION, evidence_ids=["S0"]),
                           EVIDENCE) == [])
    check("  an interpretation with no evidence at all is refused",
          any("must name the evidence" in e for e in LG.validate_fact(
              fact(fact_id="F07", proposition="A selection is not a count.",
                   claim_type=LG.INTERPRETATION, evidence_ids=[]), EVIDENCE)))


# ── silence is not evidence of absence ───────────────────────────────────────
def test_a_world_negative_needs_evidence_that_states_the_negative():
    """The Roman ending, reproduced as a unit test."""
    world = fact(fact_id="F10",
                 proposition="No tooling was engineered at the receiving end.",
                 claim_type=LG.NEGATIVE_EXISTENCE, evidence_ids=["S0"],
                 support_span="with the aim of engaging all senses",  # positive span
                 scope=LG.WORLD)
    errs = LG.validate_fact(world, EVIDENCE)
    check("a WORLD negative resting on a positive span is refused",
          any("silence is not evidence of absence" in e for e in errs), errs)
    for ct in (LG.ABSENCE, LG.EXCLUSIVITY, LG.FIRST_LAST, LG.COMPARATIVE_NEGATION):
        f = fact(fact_id="F11", proposition="Nothing of the kind was done.",
                 claim_type=ct, evidence_ids=["S0"],
                 support_span="Here are eight of the most interesting", scope=LG.WORLD)
        check("  %s is held to the same rule" % ct,
              any("silence is not evidence" in e for e in LG.validate_fact(f, EVIDENCE)))
    # an audited-corpus negative is admissible, but must state its size and its wording
    ok = fact(fact_id="F12",
              proposition="None of the eight descriptions reports what a visitor perceived.",
              claim_type=LG.ABSENCE, evidence_ids=["S0"],
              support_span="Here are eight of the most interesting",
              scope=LG.AUDITED_CORPUS, corpus_size=8)
    check("an AUDITED_CORPUS negative worded about that set validates",
          LG.validate_fact(ok, EVIDENCE) == [], LG.validate_fact(ok, EVIDENCE))
    nosize = dict(ok, corpus_size=0)
    check("  without a stated corpus size it is refused",
          any("how many items were audited" in e
              for e in LG.validate_fact(nosize, EVIDENCE)))
    worldish = dict(ok, proposition="Visitor perception was never recorded anywhere.")
    check("  worded as a claim about the world it is refused",
          any("not about the world" in e for e in LG.validate_fact(worldish, EVIDENCE)))


# ── stages cannot mint facts ─────────────────────────────────────────────────
def test_the_architect_cannot_mint_a_fact_id():
    arch = {"use_facts": ["F01", "F02"], "beats": [{"facts_allowed": ["F01"]}]}
    check("referencing existing facts is fine",
          LG.architect_may_not_mint(arch, BASE) == [])
    minted = {"use_facts": ["F01", "F99"], "beats": [{"facts_allowed": ["F77"]}]}
    errs = LG.architect_may_not_mint(minted, BASE)
    check("inventing fact ids is refused",
          any("minted facts" in e for e in errs), errs)
    check("  and both invented ids are named",
          "F77" in str(errs) and "F99" in str(errs), errs)


def test_the_architect_cannot_launder_an_attribute_through_its_own_prose():
    """The "pink" class, at each of the four attribute kinds section 5 requires."""
    props = LG.propositions(BASE)
    for label, field, value, channel in (
            ("colour", "turn", "A picture holds a pink wall.", "unapproved_sensory"),
            ("floor/spatial", "turn", "The upper floor sat above the sand.",
             "unapproved_spatial"),
            ("quantity", "turn", "The room was 12 metres across.", "unapproved_numbers"),
            ("scene", "crip_turn", "A teacher waited at a desk with a laptop.",
             "unapproved_scene")):
        a = {field: value, "beats": []}
        r = ST.architect_prose_audit(a, props)
        hit = r[channel]
        check("an unsupported %s in the architect's prose is caught" % label,
              bool(hit), r)
    ok = {"turn": "A picture holds the brick.", "beats": []}
    check("architect prose inside the ledger passes",
          ST.architect_prose_audit(ok, props)["hard_ok"],
          ST.architect_prose_audit(ok, props))


# ── the writer side ──────────────────────────────────────────────────────────
def test_a_writer_negative_claim_must_match_a_negative_fact():
    led = dict(BASE)
    led["F12"] = fact(fact_id="F12",
                      proposition="None of the eight descriptions reports what a visitor perceived.",
                      claim_type=LG.ABSENCE, evidence_ids=["S0"],
                      support_span="Here are eight of the most interesting",
                      scope=LG.AUDITED_CORPUS, corpus_size=8)
    covered = "Across all eight descriptions, none reports what any visitor perceived."
    r = ST.negative_admission_audit(covered, led)
    check("a negative sentence matching its fact is admitted", r["ok"], r["unmatched"])
    for label, sentence in (
            ("was not engineered", "It is the part that was not engineered."),
            ("there was no", "There was no way to open the file."),
            ("never existed", "Such a room had never existed before."),
            ("nothing in", "Nothing in the plan accounted for it."),
            ("none reports", "None reports what happened next."),
            ("not once", "What it was like: not once.")):
        r = ST.negative_admission_audit(sentence, led)
        check("an unsupported negative (%s) is caught" % label,
              not r["ok"] and r["negative_sentences"] >= 1, r)
    check("ordinary prose raises no negative flag",
          ST.negative_admission_audit("The walls were salt brick.", led)["ok"])


def test_intent_and_causal_assertions_are_surfaced():
    hits = ST.intent_causal_scan("They wanted to change the ranking. So that it would win.")
    check("intent and causal shapes are surfaced", len(hits) >= 1, hits)
    check("plain description is not", ST.intent_causal_scan("The walls were salt.") == [])


# ── the final lens contract ──────────────────────────────────────────────────
def _arch():
    return {"article_type": ST.SHORT_NARRATIVE,
            "beats": [{"beat_id": "B1", "concrete_carrier": "the salt walls"},
                      {"beat_id": "B2", "concrete_carrier": "the sand underfoot"},
                      {"beat_id": "B3", "concrete_carrier": "the list of eight"}]}


def _lens(**over):
    d = {"lens_claim": "The record keeps what materials meant and loses what they were like.",
         "evidence_basis": ["F01"],
         "what_changes_for_the_reader": "The reader now understands the ranking as a "
                                        "judgement about what transferred.",
         "story_beat_before": "B1", "crip_turn": "Go back to the salt walls.",
         "story_beat_after": "B3"}
    d.update(over)
    return d


def test_the_final_lens_must_sit_between_two_beats_and_change_understanding():
    check("a complete final lens validates",
          ST.validate_final_lens(_lens(), _arch(), BASE) == [],
          ST.validate_final_lens(_lens(), _arch(), BASE))
    check("an omitted crip turn is refused",
          any("missing crip_turn" in e
              for e in ST.validate_final_lens(_lens(crip_turn=""), _arch(), BASE)))
    check("a turn that re-reads a LATER beat than it lands on is refused",
          any("earlier and a later beat" in e for e in ST.validate_final_lens(
              _lens(story_beat_before="B3", story_beat_after="B1"), _arch(), BASE)))
    check("a turn naming nothing from the beat it re-reads is refused",
          any("names nothing from B1" in e for e in ST.validate_final_lens(
              _lens(crip_turn="Anyone measured wrongly knows this."), _arch(), BASE)))
    check("a lens citing an unknown fact is refused",
          any("unknown facts" in e for e in ST.validate_final_lens(
              _lens(evidence_basis=["F99"]), _arch(), BASE)))
    check("a lens that never says what changes for the reader is refused",
          any("change in understanding" in e for e in ST.validate_final_lens(
              _lens(what_changes_for_the_reader="it is better"), _arch(), BASE)))
    check("a beat id that does not exist is refused",
          any("is not a beat" in e for e in ST.validate_final_lens(
              _lens(story_beat_before="B9"), _arch(), BASE)))


def test_worth_gate_metadata_alone_is_not_a_lens():
    """A publishable Worth Gate verdict with no final lens must not pass."""
    for missing in ("crip_turn", "story_beat_before", "story_beat_after",
                    "what_changes_for_the_reader"):
        errs = ST.validate_final_lens(_lens(**{missing: ""}), _arch(), BASE)
        check("a final lens missing %s is refused" % missing, bool(errs), errs)
    check("and an entirely absent final lens is refused",
          bool(ST.validate_final_lens({}, _arch(), BASE)))


# ── the frozen final artefacts ───────────────────────────────────────────────
def test_the_frozen_jia_final_holds_every_contract():
    lf, af = EXP / "jia.ledger.json", EXP / "jia.final.architecture.json"
    art = EXP / "jia.NEW.final.md"
    if not (lf.exists() and af.exists() and art.exists()):
        check("frozen jia final artefacts present", False, "missing")
        return
    led = json.loads(lf.read_text())
    d = json.loads(af.read_text())
    a, wg, fl = d["architecture"], d["worth_gate"], d["final_lens"]
    props = LG.propositions(led)
    body = art.read_text()
    check("the ledger's every support span is verbatim in the frozen evidence",
          all("not verbatim" not in e for e in LG.validate_ledger(led, _jia_evidence())),
          [e for e in LG.validate_ledger(led, _jia_evidence()) if "verbatim" in e])
    check("no minted facts", LG.architect_may_not_mint(a, led) == [],
          LG.architect_may_not_mint(a, led))
    check("architect prose is inside the ledger",
          ST.architect_prose_audit(a, props)["hard_ok"],
          ST.architect_prose_audit(a, props))
    check("the final lens contract holds", ST.validate_final_lens(fl, a, led) == [],
          ST.validate_final_lens(fl, a, led))
    pk = ST.build_packet(a, wg, props, {})
    check("the packet validates", ST.validate_packet(pk) == [], ST.validate_packet(pk))
    check("the packet stays small", len(ST.render(pk).split()) < 1000,
          len(ST.render(pk).split()))
    check("zero provenance frames in the prose", ST.prose_leaks(body)["ok"],
          ST.prose_leaks(body)["frames"])
    check("factual surface clean", ST.factual_surface_audit(body, pk)["hard_ok"],
          ST.factual_surface_audit(body, pk))
    na = ST.negative_admission_audit(body, led)
    check("every negative claim is admitted by a negative fact", na["ok"], na["unmatched"])
    check("no intent or causal invention", ST.intent_causal_scan(body) == [],
          ST.intent_causal_scan(body))
    ct = EXP / "jia.cut_terms.json"
    if ct.exists():
        check("no cut evidence in the prose",
              ST.cut_adherence(body, a, json.loads(ct.read_text()))["clean_prose"])


def _jia_evidence() -> str:
    """The spans the ledger quotes, as one string. The full anchor body is deliberately
    not committed to this repo, so the test asserts span-shape rather than re-fetching
    third-party text."""
    lf = EXP / "jia.ledger.json"
    led = json.loads(lf.read_text())
    return " ".join(f.get("support_span", "") for f in led.values())


def test_roman_is_held_and_the_reason_is_recorded():
    wf = EXP / "roman.final.worthgate.json"
    if not wf.exists():
        check("roman worth-gate record present", False, "missing")
        return
    d = json.loads(wf.read_text())
    check("roman is HELD", d["decision"] == "HOLD", d["decision"])
    check("its verdict is not publishable",
          d["worth_gate"]["verdict"] not in ST.LENS_PUBLISHABLE,
          d["worth_gate"]["verdict"])
    check("the rejected negative fact is recorded with its reason",
          any("silence is not evidence of absence" in e
              for e in d["attempted_negative_fact_rejected_because"]),
          d["attempted_negative_fact_rejected_because"])
    check("no final roman article was generated",
          not (EXP / "roman.NEW.final.md").exists())


def main() -> None:
    for fn in (test_a_fact_needs_a_verbatim_span_in_the_evidence,
               test_a_world_negative_needs_evidence_that_states_the_negative,
               test_the_architect_cannot_mint_a_fact_id,
               test_the_architect_cannot_launder_an_attribute_through_its_own_prose,
               test_a_writer_negative_claim_must_match_a_negative_fact,
               test_intent_and_causal_assertions_are_surfaced,
               test_the_final_lens_must_sit_between_two_beats_and_change_understanding,
               test_worth_gate_metadata_alone_is_not_a_lens,
               test_the_frozen_jia_final_holds_every_contract,
               test_roman_is_held_and_the_reason_is_recorded):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL LEDGER AND LENS TESTS PASSED")


if __name__ == "__main__":
    main()
