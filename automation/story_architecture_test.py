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
        "reader_initial_state": "That a room was made of salt.",
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
    # Two distinct branches, tested separately.
    # (a) a prohibition that DESCRIBES THE EVIDENCE STATE -- the shape the Writer copies.
    desc = arch(prohibitions=["The material does not matter to this story."])
    e_desc = ST.validate_packet(ST.build_packet(desc, LENS, FACTS))
    check("a prohibition describing the evidence state is refused",
          any("description of the evidence" in e for e in e_desc), e_desc)
    # (b) anything not phrased as an instruction at all.
    stmt = arch(prohibitions=["Colours are unsupported here."])
    e_stmt = ST.validate_packet(ST.build_packet(stmt, LENS, FACTS))
    check("a prohibition that is not an instruction is refused",
          any("instruction to the" in e for e in e_stmt), e_stmt)
    # (c) but an imperative may QUOTE the construction it forbids. An earlier version of
    # this screen rejected exactly this, which is a false positive: the sentence is a
    # constraint on the generator, not a description of the evidence.
    quoting = arch(prohibitions=["Do not claim anything was never tested or does not exist."])
    check("an imperative quoting a negative construction is accepted",
          ST.validate_packet(ST.build_packet(quoting, LENS, FACTS)) == [],
          ST.validate_packet(ST.build_packet(quoting, LENS, FACTS)))
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



# ── loop 3: the lens must be embodied, and the audits must reach the architect ──
def test_the_crip_turn_must_declare_what_it_rereads():
    """Four blind readers, two unrelated subjects, one shared criticism: the turn was
    'a late abstract aside', 'the only paragraph with nobody in it'. A first version of
    this check inferred embodiment from token overlap and passed both architectures they
    had criticised, matching on the word "named". So the relation is declared now."""
    a = arch()
    check("a turn with no declared antecedent is refused",
          any("crip_turn_rereads missing" in e
              for e in ST.validate_lens_embodiment(a, LENS)))
    a2 = arch(crip_turn_rereads="B9")
    check("a turn pointing at a non-existent beat is refused",
          any("not a beat" in e for e in ST.validate_lens_embodiment(a2, LENS)))
    a3 = arch(crip_turn_rereads="B2")
    check("a turn re-reading the FINAL beat is refused",
          any("reader has had time" in e for e in ST.validate_lens_embodiment(a3, LENS)))
    a4 = arch(crip_turn_rereads="B1",
              crip_turn="Anyone who is measured by the wrong instrument knows this.")
    errs = ST.validate_lens_embodiment(a4, LENS)
    check("a turn naming nothing from the beat it claims is refused",
          any("does not name anything from B1" in e for e in errs), errs)
    a5 = arch(crip_turn_rereads="B1",
              crip_turn="Read the salt walls again and they mean something else.")
    check("a turn that names the beat's own carrier is accepted",
          ST.validate_lens_embodiment(a5, LENS) == [],
          ST.validate_lens_embodiment(a5, LENS))
    check("a refused lens is exempt (there is no turn to embody)",
          ST.validate_lens_embodiment(arch(), {"verdict": ST.WRONG_PUBLICATION}) == [])


def test_the_factual_surface_audit_catches_additions_the_packet_never_granted():
    pk = ST.build_packet(arch(), LENS, FACTS)
    clean = "A room of salt brick, set partway into the ground, held fragrances."
    r = ST.factual_surface_audit(clean, pk)
    check("prose within the packet is hard-clean", r["hard_ok"], r)
    for label, text, channel in (
            ("an invented number", "The room was 12 metres across.", "unapproved_numbers"),
            ("an invented name", "It was funded by the Tuscany Boutique.", "unapproved_entities"),
            ("an invented colour", "The walls were pink and warm.", "unapproved_sensory"),
            ("an invented scene", "A teacher sat at a desk with a laptop.", "unapproved_scene")):
        r = ST.factual_surface_audit(text, pk)
        check("%s is caught in %s" % (label, channel), bool(r[channel]) and not r["hard_ok"],
              r[channel])
    # the false positives found while running the campaign, kept as regressions
    pos = ST.build_packet(arch(story_spine="Jia Curated's fifth edition, a Jakarta-based studio."),
                          LENS, FACTS)
    r = ST.factual_surface_audit("The show was Jia Curated, run by a Jakarta studio.", pos)
    check("a possessive in the packet still approves the bare name (Curated's -> Curated)",
          "Curated" not in r["unapproved_entities"], r["unapproved_entities"])
    check("a hyphenated compound still approves its parts (Jakarta-based -> Jakarta)",
          "Jakarta" not in r["unapproved_entities"], r["unapproved_entities"])
    check("an ordinary word is not treated as a scene prop",
          ST.factual_surface_audit("It has to go somewhere, and a room is a room.",
                                   pk)["unapproved_scene"] == [],
          ST.factual_surface_audit("It has to go somewhere.", pk)["unapproved_scene"])


def test_the_architect_stage_is_audited_too():
    """The campaign reported "pink" as a Writer fabrication. It was not: it had been
    written into the architecture's own `turn` field, so the packet had already approved
    it. An audit whose ground truth is generated cannot see upstream of itself."""
    bad = arch(turn="A picture holds a pink wall and a low ceiling.")
    r = ST.architect_prose_audit(bad, FACTS)
    check("an attribute invented in the architect's prose is caught",
          "pink" in r["unapproved_sensory"] and not r["hard_ok"], r)
    ok = arch(turn="A picture holds the brick.")
    check("the same field without the invented attribute passes",
          ST.architect_prose_audit(ok, FACTS)["hard_ok"],
          ST.architect_prose_audit(ok, FACTS))
    check("a packet built from the bad architecture looks CLEAN to the later audit",
          ST.factual_surface_audit("A pink wall.",
                                   ST.build_packet(bad, LENS, FACTS))["hard_ok"],
          "this is the laundering the architect audit exists to stop")
    num = arch(turn="The room was 12 metres across and cost 40,000 dollars.")
    rn = ST.architect_prose_audit(num, FACTS)
    check("an invented NUMBER in the architect's prose is caught",
          rn["unapproved_numbers"] and not rn["hard_ok"], rn["unapproved_numbers"])
    ent = arch(turn="It was funded by the Tuscany Stone Boutique.")
    re_ = ST.architect_prose_audit(ent, FACTS)
    check("an invented NAME in the architect's prose is caught",
          re_["unapproved_entities"] and not re_["hard_ok"], re_["unapproved_entities"])
    scene = arch(beats=[dict(arch()["beats"][0],
                            concrete_carrier="a teacher at a desk with a laptop"),
                        arch()["beats"][1]])
    check("an invented scene in a beat carrier is caught",
          bool(ST.architect_prose_audit(scene, FACTS)["unapproved_scene"]),
          ST.architect_prose_audit(scene, FACTS)["unapproved_scene"])


def test_the_frozen_loop3_articles_are_clean_on_every_screen():
    import json as _json
    for case in ("jia", "roman"):
        af = EXP / ("%s.architecture.json" % case)
        art = EXP / ("%s.NEW.loop3.md" % case)
        if not (af.exists() and art.exists()):
            check("frozen loop3 %s present" % case, False, "missing")
            continue
        d = _json.loads(af.read_text())
        a, lens, facts = d["architecture"], d["lens"], d["facts"]
        body = art.read_text()
        pk = ST.build_packet(a, lens, facts, d.get("quotes") or {})
        check("%-6s architecture validates" % case,
              ST.validate_architecture(a, set(facts)) == [],
              ST.validate_architecture(a, set(facts)))
        check("%-6s lens is embodied" % case,
              ST.validate_lens_embodiment(a, lens) == [],
              ST.validate_lens_embodiment(a, lens))
        # These loop-3 artefacts are HISTORICAL: kept for comparison, and held to the
        # bar that existed when they were made. The later iteration added a SPATIAL_RISK
        # channel, and the loop-3 jia architecture trips it ("edible", "small", "sunk")
        # -- which is the correct result and is exactly why that channel was added. The
        # FINAL artefacts are held to the new bar in ledger_and_lens_test.py.
        hist = ST.architect_prose_audit(a, facts, d.get("quotes") or {})
        check("%-6s architect prose carries no invented number/name/colour" % case,
              not hist["unapproved_numbers"] and not hist["unapproved_entities"]
              and not hist["unapproved_sensory"],
              {k: v for k, v in hist.items() if k != "hard_ok"})
        check("%-6s packet validates" % case, ST.validate_packet(pk) == [],
              ST.validate_packet(pk))
        check("%-6s prose carries no provenance frame" % case,
              ST.prose_leaks(body)["ok"], ST.prose_leaks(body)["frames"])
        hfs = ST.factual_surface_audit(body, pk)
        check("%-6s prose carries no invented number/name/colour/scene" % case,
              not hfs["unapproved_numbers"] and not hfs["unapproved_entities"]
              and not hfs["unapproved_sensory"] and not hfs["unapproved_scene"], hfs)
        ct = EXP / ("%s.cut_terms.json" % case)
        if ct.exists():
            r = ST.cut_adherence(body, a, _json.loads(ct.read_text()))
            check("%-6s uses no cut evidence" % case, r["clean_prose"], r["violations"])


# ── a carrier may not mint a happening the ledger holds only as a rule ───────
# Measured on the held-out Justin Blinder run, 4 September 2026. Beat B6's carrier read
# "a block group with no published figure, and the brake that therefore does not move",
# and the article duly said the bike "coasted through the block group with no published
# figure". Every noun was approved. No source reports a ride through such a block group:
# the ledger holds only what the device DOES when it meets one. Novelty checks pass this
# -- nothing is new -- because the invention is in the recombination.
LEDGER = {
    "D1": {"claim_kind": ST.DISPOSITION,
           "proposition": "Where a block group's sample is too small, the ACS publishes "
                          "no estimate, and the device renders this as no reading."},
    "D2": {"claim_kind": ST.DISPOSITION,
           "proposition": "The servo pulls the existing front brake arm."},
    "O1": {"claim_kind": ST.OCCURRENCE,
           "proposition": "Riding near NYCHA complexes, the device released resistance."},
    "U1": {"proposition": "A fact whose claim_kind nobody declared."},
}


def _beat(carrier, facts):
    return {"beat_id": "B6", "happens": "what the measure does not hold",
            "concrete_carrier": carrier, "facts_allowed": facts,
            "concept_introduced": "", "why_reader_wants_next": "the cables",
            "must_not_say_yet": ""}


def _reject(carrier, facts):
    return ST.validate_carrier_occurrence({"beats": [_beat(carrier, facts)]}, LEDGER)


def test_a_carrier_cannot_mint_an_occurrence_from_a_disposition():
    bug = _reject("a block group with no published figure, and the brake that therefore "
                  "does not move", ["D1", "D2"])
    check("the exact held-out carrier is refused", len(bug) == 1, bug)
    if bug:
        check("  and is refused as an unsupported instance",
              bug[0]["code"] == "CARRIER_INSTANCE_NOT_SUPPORTED", bug[0])
        check("  and says which claim kinds it actually had",
              bug[0]["supporting_claim_kinds"] == {"D1": ST.DISPOSITION,
                                                   "D2": ST.DISPOSITION},
              bug[0]["supporting_claim_kinds"])
    # the repair the run actually shipped
    check("the repaired carrier names the thing and passes",
          _reject("a block group with no published figure", ["D1", "D2"]) == [], "")

    # MUTATIONS: each is the same beat with one thing changed.
    check("a finite verb alone is enough to refuse",
          len(_reject("the brake that does not move", ["D1"])) == 1)
    check("a consequence connective is enough to refuse",
          len(_reject("a block group, and therefore a slack cable", ["D1"])) == 1)
    check("a participle doing a verb's work is enough to refuse",
          len(_reject("the bike coasting through the block group", ["D1"])) == 1)
    check("an undeclared claim_kind is read as a disposition, not waved through",
          len(_reject("the brake that does not move", ["U1"])) == 1)
    check("no allowed facts at all cannot license an occurrence",
          len(_reject("the brake that does not move", [])) == 1)

    # AND THE OTHER DIRECTION: valid language must survive.
    check("an occurrence carrier backed by an OCCURRENCE fact passes",
          _reject("the bike speeding up alongside the complexes", ["O1"]) == [], "")
    check("an occurrence fact anywhere in the beat is enough",
          _reject("the bike speeding up alongside the complexes",
                  ["D1", "O1"]) == [], "")
    check("an explicitly conditional carrier stays available to dispositions",
          _reject("a block group where the survey publishes no figure, and the brake "
                  "that would not move", ["D1"]) == [], "")
    check("adjectival participles are not events",
          _reject("the published figure for the housing complexes", ["D1"]) == [], "")
    check("a plain noun phrase passes with nothing but dispositions",
          _reject("the card of scores and the servo arm on the brake cable",
                  ["D1", "D2"]) == [], "")


def test_the_carrier_check_is_off_unless_a_ledger_is_supplied():
    a = arch()
    a["beats"][0]["concrete_carrier"] = "the salt walls that were built into the ground"
    check("without a ledger the architecture validates exactly as before",
          not any("CARRIER_INSTANCE" in e for e in ST.validate_architecture(a, set(FACTS))))
    withl = ST.validate_architecture(a, set(FACTS),
                                     {"F01": {"claim_kind": ST.DISPOSITION},
                                      "F02": {"claim_kind": ST.DISPOSITION}})
    check("with a ledger the same architecture is refused",
          any("CARRIER_INSTANCE_NOT_SUPPORTED" in e for e in withl), withl)
    check("  and the message names the carrier and the kinds it had",
          any("salt walls" in e and ST.DISPOSITION in e for e in withl), withl)


def test_inflection_does_not_defeat_a_cut_watch_term():
    a = arch(cut_evidence=[{"evidence_id": "F04", "reason": "BACKGROUND_NOT_NEEDED"}])
    # The watch term is written in one form and the prose reaches for another. The
    # literal test cannot see it; before this, the screen reported clean prose.
    hit = ST.cut_adherence("The studio had already designed two of them.", a,
                           {"F04": ["designs"]})
    check("an inflected form of a watch term is a violation",
          [v["term"] for v in hit["violations"]] == ["designs"], hit["violations"])
    check("  and is reported as inflected, so a reviewer can see why it fired",
          hit["violations"] and hit["violations"][0]["match"] == "inflected",
          hit["violations"])
    check("the reverse inflection is caught too",
          not ST.cut_adherence("Two scans of the fork.", a,
                               {"F04": ["scan"]})["clean_prose"])
    lit = ST.cut_adherence("A contemplative space.", a, {"F04": ["contemplative"]})
    check("a literal hit is still reported as literal",
          lit["violations"] and lit["violations"][0]["match"] == "literal",
          lit["violations"])
    # STATED LIMIT, not a fixed one: the pre-existing literal pass is a raw substring
    # test, so a longer unrelated word containing the term still fires. That predates
    # this patch and is unchanged by it. It over-reports a CUT rather than under-reports
    # one, which is the safe direction, and narrowing it is a separate change.
    check("a longer word merely containing the term still fires, literally, as before",
          [v["match"] for v in
           ST.cut_adherence("It caused a scandal.", a,
                            {"F04": ["scan"]})["violations"]] == ["literal"])
    check("  and the stem pass is not what fired there",
          [v["match"] for v in
           ST.cut_adherence("It left a footprint.", a,
                            {"F04": ["print"]})["violations"]] == ["literal"])
    # what the stem pass must NOT do: match a longer word by prefix. Only whole tokens.
    check("the stem pass does not match a longer token by prefix",
          ST.cut_adherence("A scanner was mentioned once.", a,
                           {"F04": ["scans"]})["clean_prose"],
          ST.cut_adherence("A scanner was mentioned once.", a,
                           {"F04": ["scans"]})["violations"])
    check("multi-word watch terms are matched literally and only literally",
          ST.cut_adherence("Other cites were mentioned.", a,
                           {"F04": ["other cities"]})["clean_prose"])
    check("an unrelated body is still clean",
          ST.cut_adherence("A room of salt.", a, {"F04": ["design"]})["clean_prose"])


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
               test_the_frozen_jia_experiment_holds_its_contract,
               test_the_crip_turn_must_declare_what_it_rereads,
               test_the_factual_surface_audit_catches_additions_the_packet_never_granted,
               test_the_architect_stage_is_audited_too,
               test_the_frozen_loop3_articles_are_clean_on_every_screen,
               test_a_carrier_cannot_mint_an_occurrence_from_a_disposition,
               test_the_carrier_check_is_off_unless_a_ledger_is_supplied,
               test_inflection_does_not_defeat_a_cut_watch_term):
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
