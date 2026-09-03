#!/usr/bin/env python3
"""
story_architecture_test.py -- the packet cannot carry the research apparatus.

The defect these tests exist for was measured on 3 September 2026, not guessed. The
Writer received 5,554-7,121 prompt words to produce ~650, and `evidence_gaps` /
`grounding_boundaries` reached it as CONTENT. It returned them as sentences:

  given:  "The source does not describe how any visitor actually perceived these spaces"
  became: "It does not report what any visitor experienced, and I am not claiming it does."

Grounding V2's shadow runs had been reporting the same sentences as UNSUPPORTED
negative-existence claims all along.

So the invariant under test is not "the prose avoids some words". It is that a
prohibition can only reach the generator as an imperative, and that a packet carrying
the auditing frame is REFUSED rather than tidied.

Behavioural, no provider, no network.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import story as ST                       # noqa: E402

FAILURES: list = []
EXP = HERE.parent / ".claude" / "story-architecture" / "experiments"


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


FACTS = {"F01": "The room was built from salt brick.",
         "F02": "It was set partway into the ground.",
         "F03": "Inside it held fragrances and drinks.",
         "F04": "A studio designed it as a contemplative space."}


def arch(**over) -> dict:
    a = {
        "article_type": ST.SHORT_NARRATIVE,
        "story_spine": "A room of salt was ranked through a medium that cannot carry it.",
        "opening_object_or_event": "A wall of salt brick on a beach.",
        "reader_initial_state": "That a small room was made of salt.",
        "beats": [
            {"beat_id": "B1", "happens": "the room and its material",
             "concrete_carrier": "the salt walls", "facts_allowed": ["F01", "F02"],
             "concept_introduced": "", "why_reader_wants_next": "it is a strange thing",
             "must_not_say_yet": "the ranking"},
            {"beat_id": "B2", "happens": "what was inside",
             "concrete_carrier": "smell and taste", "facts_allowed": ["F03"],
             "concept_introduced": "", "why_reader_wants_next": "",
             "must_not_say_yet": ""},
        ],
        "turn": "What survives is a photograph.",
        "crip_turn": "The ranking measured only what a camera holds.",
        "ending_move": "Return to the salt wall.",
        "use_facts": ["F01", "F02", "F03"],
        "use_quotes": [],
        "definitions": {},
        "prohibitions": ["Do not name any brand.", "Never use the first person."],
        "cut_evidence": [{"evidence_id": "F04", "reason": "BACKGROUND_NOT_NEEDED"}],
    }
    a.update(over)
    return a


LENS = {"verdict": ST.STRONG_INTERPRETIVE_LENS,
        "lens_claim": "A festival travels in the medium it is documented in, and that "
                      "medium decides which work can travel at all.",
        "changes_meaning_how": "It turns a design ranking into a ranking of "
                               "photographability.",
        "evidence_ids": ["F01", "F03"]}


# ── the enforced invariant ───────────────────────────────────────────────────
def test_a_packet_carrying_the_auditing_frame_is_refused():
    good = ST.build_packet(arch(), LENS, FACTS)
    check("a clean packet validates", ST.validate_packet(good) == [],
          ST.validate_packet(good))
    # every one of these is a real construction taken from the frozen failures
    for label, bad_spine in (
            ("'the source does not describe'",
             "The source does not describe the building's form."),
            ("'nothing in the source'",
             "Nothing in the source says the room was accessible."),
            ("'the evidence'", "The evidence establishes only the material."),
            ("'this reading'", "This reading rests on one clause."),
            ("a source-id marker", "S1 supports the salt claim."),
            ("a role-taxonomy word", "The ANCHOR gives the material."),
            ("'the brief'", "The brief takes its cue from movement.")):
        p = ST.build_packet(arch(story_spine=bad_spine), LENS, FACTS)
        errs = ST.validate_packet(p)
        check("%s is refused" % label,
              any("provenance frame" in e for e in errs), errs[:2])


def test_a_prohibition_phrased_as_a_description_is_refused():
    """The exact defect: a constraint that describes the evidence becomes a caveat."""
    bad = arch(prohibitions=[
        "The source does not establish that any visitor was blind.",
    ])
    p = ST.build_packet(bad, LENS, FACTS)
    errs = ST.validate_packet(p)
    check("a description-shaped prohibition is refused", bool(errs), errs)
    check("  and it is named as such",
          any("description of the evidence" in e or "provenance frame" in e
              for e in errs), errs[:2])
    # A description-shaped prohibition whose verb is NOT in the provenance-frame list,
    # so only the prohibition screen can catch it. Without this the screen is untested:
    # "does not establish" is already refused one layer earlier.
    sneaky = arch(prohibitions=["The pavilion count does not matter to this story."])
    errs2 = ST.validate_packet(ST.build_packet(sneaky, LENS, FACTS))
    check("a description-shaped prohibition the frame list misses is still refused",
          any("description of the evidence" in e for e in errs2), errs2)
    ok = arch(prohibitions=[
        "Do not say any visitor was blind or low-vision.",
    ])
    p2 = ST.build_packet(ok, LENS, FACTS)
    check("the same constraint as an imperative is accepted",
          ST.validate_packet(p2) == [], ST.validate_packet(p2))
    txt = ST.render(p2)
    check("  and it reaches the generator as an instruction",
          "Do not say any visitor was blind" in txt)


def test_the_packet_does_not_carry_the_research_apparatus():
    p = ST.build_packet(arch(), LENS, FACTS)
    txt = ST.render(p)
    check("no source bodies, roles, ids or provenance", ST.leaks(txt) == [], ST.leaks(txt))
    check("no scaffold names reach the prompt", ST.scaffold_leaks(txt) == [],
          ST.scaffold_leaks(txt))
    check("cut facts are absent from the packet",
          FACTS["F04"] not in txt)
    check("used facts are present", all(FACTS[f] in txt for f in ("F01", "F02", "F03")))
    check("the packet is far smaller than the baseline writer prompt (5,554-7,121 words)",
          len(txt.split()) < 1200, len(txt.split()))


# ── worth gate ──────────────────────────────────────────────────────────────
def test_an_empty_lens_cannot_pass_the_worth_gate():
    for label, claim in (
            ("generic barriers", "Disabled people face barriers, and so did this idea."),
            ("reminder framing", "This reminds us that difference is everywhere."),
            ("bare analogy", "Just as disabled readers are excluded, so was the theory."),
            ("metaphor claim", "The blocked river is a metaphor for disability."),
            ("we-are-all", "We are all disabled by systems we did not design.")):
        errs = ST.validate_lens({"verdict": ST.STRONG_INTERPRETIVE_LENS,
                                 "lens_claim": claim,
                                 "changes_meaning_how": "it reframes things",
                                 "evidence_ids": ["F01"]})
        check("%s is rejected" % label,
              any("empty formulation" in e for e in errs), errs)
    thin = ST.validate_lens({"verdict": ST.STRONG_DIRECT_LENS, "lens_claim": "Access.",
                             "changes_meaning_how": "x", "evidence_ids": ["F01"]})
    check("a lens too thin to do work is rejected",
          any("too thin" in e for e in thin), thin)
    nolens = ST.validate_lens({"verdict": ST.STRONG_DIRECT_LENS,
                               "lens_claim": "A" * 60, "changes_meaning_how": "",
                               "evidence_ids": []})
    check("a lens with no evidence is rejected",
          any("must cite evidence" in e for e in nolens), nolens)
    check("  and one that never says what it changes",
          any("changes about the story" in e for e in nolens), nolens)


def test_a_refusal_is_a_valid_outcome_and_needs_no_proof():
    for v in (ST.WRONG_PUBLICATION, ST.NO_PLAUSIBLE_LENS, ST.WEAK_ANALOGY):
        r = ST.validate_lens({"verdict": v, "lens_claim": "", "evidence_ids": []})
        check("%s validates without a claim" % v, r == [], r)
        check("  and is not publishable", v not in ST.LENS_PUBLISHABLE)
    p = ST.build_packet(arch(), {"verdict": ST.WRONG_PUBLICATION, "lens_claim": "x"},
                        FACTS)
    check("a refused lens contributes no lens text to the packet", p["lens"] == "",
          p["lens"])


# ── architecture honesty ────────────────────────────────────────────────────
def test_selection_that_discards_nothing_is_not_selection():
    errs = ST.validate_architecture(arch(cut_evidence=[]), set(FACTS))
    check("an empty cut list is refused", any("not selection" in e for e in errs), errs)
    both = ST.validate_architecture(
        arch(cut_evidence=[{"evidence_id": "F01", "reason": "NAME_OVERLOAD"}]),
        set(FACTS))
    check("evidence cannot be both used and cut",
          any("both used and cut" in e for e in both), both)
    badreason = ST.validate_architecture(
        arch(cut_evidence=[{"evidence_id": "F04", "reason": "BECAUSE_I_SAID_SO"}]),
        set(FACTS))
    check("cut reasons come from the declared set",
          any("not in the declared set" in e for e in badreason), badreason)


def test_an_architecture_cannot_invent_evidence_or_skip_a_carrier():
    ghost = ST.validate_architecture(arch(use_facts=["F01", "F99"]), set(FACTS))
    check("use_facts outside the frozen evidence are refused",
          any("not in evidence" in e for e in ghost), ghost)
    a = arch()
    a["beats"][0]["facts_allowed"] = ["F77"]
    check("a beat cannot allow a fact that does not exist",
          any("not in the frozen evidence" in e
              for e in ST.validate_architecture(a, set(FACTS))))
    b = arch()
    b["beats"][0]["concrete_carrier"] = ""
    check("a beat with no concrete carrier is refused",
          any("no concrete carrier" in e
              for e in ST.validate_architecture(b, set(FACTS))))
    c = arch(opening_object_or_event="")
    check("an abstract opening is refused",
          any("openings must be concrete" in e
              for e in ST.validate_architecture(c, set(FACTS))))
    d = arch(beats=[arch()["beats"][0]])
    check("one beat is not a path",
          any("not a path" in e for e in ST.validate_architecture(d, set(FACTS))))
    for hold in (ST.HOLD_NO_STORY, ST.HOLD_WRONG_PUBLICATION):
        check("%s needs no beats" % hold,
              ST.validate_architecture({"article_type": hold}, set()) == [])


def test_chronology_is_not_causation():
    cand = {"story_id": "S1", "carrier_type": "object", "evidence_ids": ["F01"],
            "causal_chain": [{"kind": ST.SUPPORTED_CAUSAL, "evidence_ids": []}]}
    check("a causal claim with no evidence is refused",
          any("chronology is not cause" in e for e in ST.validate_candidate(cand)),
          ST.validate_candidate(cand))
    ok = {"story_id": "S1", "carrier_type": "object", "evidence_ids": ["F01"],
          "causal_chain": [{"kind": ST.CHRONOLOGICAL_ADJACENCY, "evidence_ids": []}]}
    check("adjacency may be declared without causal evidence",
          ST.validate_candidate(ok) == [], ST.validate_candidate(ok))
    check("a story with no evidence is not a story",
          any("not a story" in e for e in ST.validate_candidate(
              {"story_id": "x", "carrier_type": "object", "evidence_ids": []})))


def test_narrative_yield_penalises_an_argument_with_no_carrier():
    concrete = ST.narrative_yield(
        {"carrier_type": "object", "opening_possibility": "a salt wall",
         "real_event_or_change": "the room was ranked", "tension": "the medium drops it",
         "reader_first_sees": "a room", "reader_later_discovers": "a ranking",
         "causal_chain": [{"kind": ST.SUPPORTED_CAUSAL, "evidence_ids": ["F01"]}],
         "evidence_ids": ["F01"], "central_subject": "a room made of salt"})
    essay = ST.narrative_yield(
        {"carrier_type": None, "opening_possibility": "", "real_event_or_change": "",
         "tension": "", "causal_chain": [], "evidence_ids": [],
         "central_subject": "This reveals how photography reframes design"})
    check("a concrete story outscores a conceptual one",
          concrete["score"] > essay["score"], (concrete["score"], essay["score"]))
    check("  and the components are reported for a human to argue with",
          set(concrete["components"]) >= {"carrier", "causal", "tension"})
    check("  the concept-only move is penalised explicitly",
          essay["components"]["concept_only_penalty"] < 0)


# ── post-writer: the cut list must be checked, not merely declared ──────────
def test_the_cut_check_reports_its_own_blind_spots():
    """Loop 1 of the campaign returned OK on an article containing a cut term, because
    the sentinel-length threshold silently dropped the term that would have caught it."""
    a = arch(cut_evidence=[{"evidence_id": "F04", "reason": "BACKGROUND_NOT_NEEDED"}])
    r = ST.cut_adherence("A studio designed it as a contemplative space.", a,
                         {"F04": ["contemplative"]})
    check("a cut term appearing in prose is a violation",
          not r["clean_prose"] and r["violations"][0]["term"] == "contemplative", r)
    short = ST.cut_adherence("nothing here", a, {"F04": ["Ong"]})
    check("a term too short to search is REPORTED, not dropped",
          short["skipped_too_short"] and not short["ok"], short)
    check("  and that alone stops the check claiming success", short["ok"] is False)
    unwatched = ST.cut_adherence("nothing here", a, {})
    check("a cut item with no watch terms is reported",
          unwatched["cut_without_watch_terms"] == ["F04"], unwatched)
    clean = ST.cut_adherence("A room of salt.", a, {"F04": ["contemplative"]})
    check("a genuinely clean article passes", clean["ok"], clean)


def test_prose_and_scaffold_screens_work_on_finished_articles():
    check("an auditing sentence is detected in prose",
          ST.prose_leaks("It does not describe the building's form.")["total"] > 0)
    check("a bare mention of a document is NOT flagged",
          ST.prose_leaks("The newspaper printed a correction the next morning.")["ok"],
          ST.prose_leaks("The newspaper printed a correction the next morning."))
    check("scaffold names in prose are caught",
          not ST.scaffold_adherence("In BEAT_2 the CRIP_TURN lands.")["ok"])
    check("ordinary prose has no scaffold hits",
          ST.scaffold_adherence("On a beach in Bali, someone built a room of salt.")["ok"])


# ── the frozen experiment is what it claims to be ───────────────────────────
def test_the_frozen_jia_experiment_holds_its_contract():
    f = EXP / "jia.architecture.json"
    if not f.exists():
        check("frozen jia experiment present", False, "missing")
        return
    d = json.loads(f.read_text())
    facts, a, lens = d["facts"], d["architecture"], d["lens"]
    check("its lens validates", ST.validate_lens(lens) == [], ST.validate_lens(lens))
    check("its architecture validates",
          ST.validate_architecture(a, set(facts)) == [],
          ST.validate_architecture(a, set(facts)))
    pk = ST.build_packet(a, lens, facts, d.get("quotes") or {})
    check("its packet validates", ST.validate_packet(pk) == [], ST.validate_packet(pk))
    check("its packet is under 1,000 words", len(ST.render(pk).split()) < 1000,
          len(ST.render(pk).split()))
    art = EXP / "jia.NEW.loop2.md"
    if art.exists():
        body = art.read_text()
        check("the final article has zero provenance frames",
              ST.prose_leaks(body)["ok"], ST.prose_leaks(body)["frames"])
        check("and no scaffold leakage", ST.scaffold_adherence(body)["ok"])
        ct = json.loads((EXP / "jia.cut_terms.json").read_text())
        r = ST.cut_adherence(body, a, ct)
        check("and uses no cut evidence", r["clean_prose"], r["violations"])


def main() -> None:
    for fn in (test_a_packet_carrying_the_auditing_frame_is_refused,
               test_a_prohibition_phrased_as_a_description_is_refused,
               test_the_packet_does_not_carry_the_research_apparatus,
               test_an_empty_lens_cannot_pass_the_worth_gate,
               test_a_refusal_is_a_valid_outcome_and_needs_no_proof,
               test_selection_that_discards_nothing_is_not_selection,
               test_an_architecture_cannot_invent_evidence_or_skip_a_carrier,
               test_chronology_is_not_causation,
               test_narrative_yield_penalises_an_argument_with_no_carrier,
               test_the_cut_check_reports_its_own_blind_spots,
               test_prose_and_scaffold_screens_work_on_finished_articles,
               test_the_frozen_jia_experiment_holds_its_contract):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL STORY ARCHITECTURE TESTS PASSED")


if __name__ == "__main__":
    main()
