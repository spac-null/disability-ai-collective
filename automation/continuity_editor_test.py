#!/usr/bin/env python3
"""
continuity_editor_test.py -- linguistic freedom, zero factual freedom.

The owner read the ledger-bound Jia final and found the Story Architect still visible
through the prose. Two mechanisms were measured:

  TRANSCRIPTION -- the architect's own fields carried the staging, and the Writer copied
  it: crip_turn "Go back to the sand." -> "So go back to the sand." at 0.93 similarity;
  ending_move "Return to the salt walls..." -> the closing sentence at 0.90.

  SENTENCES ANNOUNCING THEIR STRUCTURAL JOB -- "The answer was mostly things you cannot
  look at.", "So go back to the sand.", "Read that list again and notice...". Each tells
  the reader what it is doing rather than telling them about the world.

What was NOT the cause, on two counts now:

  Beats becoming paragraphs one for one. The measured ratio was 3.0.

  The one-sentence paragraph. This file previously called it "a slot that forces its
  sentence to perform" (5 of 15, 33%). Calibrated against 1,181 paragraphs of published
  nonfiction, solo_ratio runs 0.00-0.37 and Jia's 0.33 is inside it -- two Bregman texts
  and a ProPublica investigation match or beat it. The signpost rate does separate them:
  0.005/para in narrative exemplars, 0.046 in Bregman, 0.333 in the flagged draft. Both
  wrong hypotheses are recorded so neither is re-proposed.

The gates below exist because lineage alone is not enough: an editor can invent a
proposition while truthfully naming a parent. Relations are the dangerous channel -- a
sentence can add no number, name or colour and still turn two facts into a cause.

Behavioural, no provider, no network.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import continuity as CE                 # noqa: E402

FAILURES: list = []
EXP = HERE.parent / ".claude" / "story-architecture" / "experiments"

BEFORE = ("On a beach in Bali, someone built a room out of salt. It was built from "
          "Himalayan salt brick and set partway into the ground. Inside, the pavilion "
          "held fragrances and botanical drinks. The stated aim was to engage all the "
          "senses. The published account gathers eight pavilions and calls them the most "
          "interesting.")
DRAFT = CE.label_draft(BEFORE)


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


_N = [0]


def edit(text, parents, op=CE.REPHRASE, **kw):
    _N[0] += 1
    d = {"id": "E%03d" % _N[0], "parents": parents, "operation": op, "text": text}
    d.update(kw)
    return d


def after(text):
    """Whole-article after-state: the untouched draft with one sentence swapped in."""
    return BEFORE.replace("It was built from Himalayan salt brick and set partway "
                          "into the ground.", text)


# ── lineage ──────────────────────────────────────────────────────────────────
def test_no_output_sentence_may_have_zero_parents():
    ok = [edit("It was salt brick, set partway into the ground.", ["D002"])]
    check("a rephrase with a parent validates", CE.validate_lineage(ok, DRAFT) == [],
          CE.validate_lineage(ok, DRAFT))
    orphan = [edit("The architect wanted it to feel sacred.", [])]
    check("an orphan output sentence is refused",
          any("ZERO semantic parents" in e for e in CE.validate_lineage(orphan, DRAFT)))
    ghost = [edit("Something else.", ["D099"])]
    check("a parent that is not in the draft is refused",
          any("not in the draft" in e for e in CE.validate_lineage(ghost, DRAFT)))
    badmerge = [edit("Two things at once.", ["D001"], CE.MERGE)]
    check("a MERGE declaring one parent is refused",
          any("fewer than two parents" in e for e in CE.validate_lineage(badmerge, DRAFT)))
    dele = [{"id": "E001", "parents": ["D001"], "operation": CE.DELETE, "text": "x"}]
    check("a DELETE carrying output text is refused",
          any("may not carry output text" in e for e in CE.validate_lineage(dele, DRAFT)))
    check("NO_CHANGE is a valid operation",
          CE.validate_lineage([edit(DRAFT["D001"], ["D001"], CE.NO_CHANGE)], DRAFT) == [])


# ── the fifteen required mutations (campaign section 29) ─────────────────────
def test_the_editor_cannot_invent_a_proposition_while_claiming_a_parent():
    """Each mutation names a true parent, so lineage passes. The delta gate must catch
    them anyway -- that is the whole point of pairing the two."""
    cases = [
        ("1 a colour", "It was built from pink salt brick.", "sensory"),
        ("2 a floor/spatial relation", "Its floor sat two metres below the sand.", "spatial"),
        ("3 a sensory experience", "The brick was warm and faintly bitter.", "sensory"),
        ("4 a new named entity", "It was built from brick by Tuscany Stone Boutique.", "entities"),
        ("6 'only eight'", "The account gathers only eight pavilions.", "relation"),
        ("7 silence into negative existence", "No visitor ever perceived it.", "relation"),
        ("8 'first ever'", "It was the first building ever made of salt.", "relation"),
        ("9 a designer motive", "The studio wanted the room to feel sacred.", "relation"),
        ("10 unsupported chronology", "After the ranking, the room was dismantled.", "relation"),
    ]
    for label, sentence, channel in cases:
        errs = CE.validate_semantic_delta(BEFORE, after(sentence))
        # lineage deliberately passes: the mutation claims a real parent
        lin = CE.validate_lineage([edit(sentence, ["D002"])], DRAFT)
        check("mutation %s is caught by the delta gate" % label, bool(errs), errs[:1])
        check("   and lineage alone would NOT have caught it", lin == [], lin)
    # 5: two sequential facts turned into causality
    causal = CE.validate_semantic_delta(
        BEFORE, BEFORE + " The room was ranked because it photographed well.")
    check("mutation 5 sequential facts turned causal is caught",
          any("CAUSAL" in e for e in causal), causal)
    # 15: a merge that creates a new relational meaning with no new nouns
    merged = CE.validate_semantic_delta(
        BEFORE, BEFORE.replace("The stated aim was to engage all the senses.",
                               "Because the aim was to engage all the senses, "
                               "the account ranked it highly."))
    check("mutation 15 a merge inventing a relation is caught",
          any("CAUSAL" in e for e in merged), merged)


def test_relations_are_caught_even_with_no_new_nouns():
    for label, sentence, kind in (
            ("exclusivity", "It held only fragrances.", "EXCLUSIVITY"),
            ("negation", "It held no drinks.", "NEGATION"),
            ("first/last", "It was the first such room.", "FIRST_LAST"),
            ("intent", "The studio intended it to feel sacred.", "INTENT"),
            ("comparison", "It was better than the others.", "COMPARISON"),
            ("generalization", "Every pavilion worked this way.", "GENERALIZATION")):
        errs = CE.validate_semantic_delta(BEFORE, BEFORE + " " + sentence)
        check("a new %s relation is caught" % label,
              any(kind in e for e in errs), errs[:1])
    check("pure rewording adds no relation class",
          CE.validate_semantic_delta(
              BEFORE, BEFORE.replace("Inside, the pavilion held fragrances and botanical "
                                     "drinks.",
                                     "The pavilion held fragrances and botanical drinks "
                                     "inside.")) == [])


def test_cut_material_and_the_crip_turn():
    """12: the editor may not polish away the lens. 11: nor smuggle CUT material."""
    from new_engine_v1 import story as ST
    art = EXP / "jia.NEW.continuity.final.md"
    arch = EXP / "jia.final.architecture.json"
    ct = EXP / "jia.cut_terms.json"
    if not (art.exists() and arch.exists() and ct.exists()):
        check("frozen continuity artefacts present", False, "missing")
        return
    body = art.read_text()
    a = json.loads(arch.read_text())["architecture"]
    r = ST.cut_adherence(body, a, json.loads(ct.read_text()))
    check("11 the edited article uses no CUT material", r["clean_prose"], r["violations"])
    # 12: the lens FUNCTION must survive, not any particular wording. The function is
    # the relation between what a record can carry and what becomes judgeable, so the
    # test looks for that relation rather than for a sentence -- an exact-sentence check
    # broke the moment the selected final changed, which is the wrong sensitivity.
    low = body.lower()
    lens_present = ("record" in low
                    and "perceiv" in low
                    and any(w in low for w in ("mean", "meant", "stood for")))
    check("12 the crip turn survives the edit", lens_present,
          [w for w in ("record", "perceiv", "mean") if w not in low])
    stripped = "\n\n".join(p for p in CE.paragraphs(body)
                           if "perceiv" not in p.lower() and "record" not in p.lower())
    check("   and a text with the lens paragraphs removed no longer carries it",
          not ("record" in stripped.lower() and "perceiv" in stripped.lower()))


# ── paragraphing is the editor's, and is not dictated by beats ───────────────
def test_paragraph_boundaries_are_not_dictated_by_beats():
    """Section 30: three beats must be able to produce a non-1:1 paragraph shape."""
    edits = [
        edit("On a beach in Bali, someone built a room out of salt.", ["D001"],
             CE.NO_CHANGE),
        edit("It was salt brick, set partway into the ground.", ["D002"]),
        edit("Inside it held fragrances and drinks, and the aim was to engage all the "
             "senses.", ["D003", "D004"], CE.MERGE, paragraph_break=True),
        edit("The account gathers eight and calls them the most interesting.", ["D005"]),
    ]
    check("lineage holds across a re-paragraphing", CE.validate_lineage(edits, DRAFT) == [],
          CE.validate_lineage(edits, DRAFT))
    out = CE.apply_edits(edits)
    paras = CE.paragraphs(out)
    check("3 beats' worth of material became 2 paragraphs", len(paras) == 2, len(paras))
    check("  no sentence was lost", len(CE.sentences(out)) == 4, len(CE.sentences(out)))
    check("  and story order is preserved",
          out.index("room out of salt") < out.index("fragrances")
          < out.index("most interesting"))
    check("  with no semantic delta", CE.validate_semantic_delta(BEFORE, out) == [],
          CE.validate_semantic_delta(BEFORE, out))
    # and no fixed paragraph-count rule was introduced
    src = (HERE / "new_engine_v1" / "continuity.py").read_text()
    check("no hardcoded paragraph count anywhere in the stage",
          "PARAGRAPH_COUNT" not in src and "MAX_PARAGRAPHS" not in src)


# ── writtenness diagnostics ──────────────────────────────────────────────────
def test_writtenness_finds_performance_slots_and_signposts():
    constructed = ("A room was built of salt.\n\nThat is an odd building to make.\n\n"
                   "The answer was mostly things you cannot look at.\n\n"
                   "So go back to the sand.\n\nThe account has it as brick.")
    w = CE.writtenness(constructed)
    # counted, and reported as telemetry only -- see the calibration tests below
    check("solo paragraphs are counted (descriptively)",
          w["solo_paragraphs"] == 5, w["solo_paragraphs"])
    check("  and solo_ratio does not claim to be a defect signal",
          w["solo_ratio_is_a_defect_signal"] is False)
    check("signpost openers are found, including one behind a connective",
          len(w["signpost_openers"]) >= 3,
          w["signpost_openers"])
    flowing = ("A room was built of salt. It was set partway into the ground, so it "
               "belonged to the beach.\n\nInside it held fragrances, and the aim was to "
               "engage all the senses. The account records the brick.")
    w2 = CE.writtenness(flowing)
    check("flowing prose has no solo paragraphs", w2["solo_paragraphs"] == 0)
    check("  and no signpost openers", w2["signpost_openers"] == [])


# ── calibration: what these numbers are allowed to mean ──────────────────────
# Added 2026-09-04 from craft-research-v2. The point of these tests is that the diagnostic
# reports the truth about its two signals: one separates the known defect, the other does not.
def test_solo_paragraphs_alone_are_not_a_writtenness_defect():
    """A: published-shaped prose with several one-sentence paragraphs is not condemned."""
    # Bregman's argument essays run 0.20-0.37 solo_ratio with pivot paragraphs at the hinges.
    published_like = "\n\n".join([
        "On 17 September 1738, in the American village of Burlington, a small, hunchbacked "
        "man came storming into a church service, wearing a long coat with something "
        "hidden underneath it.",
        "Everyone present belonged to the Religious Society of Friends.",
        "The service had been going on for a while when the little man finally rose to his "
        "feet, threw off his coat, and drove a sword through a hollowed-out book.",
        "The deniers are us.",
        "In 1738 slavery was normal across great swaths of the world, and the men in that "
        "room owned people themselves, which is what made the gesture unbearable to them.",
        "Genes cannot be undone. Poverty can.",
        "He was expelled from four congregations in his life, and each time he came back.",
        "Physically, Benjamin was a dwarf. Mentally, he was a giant.",
        "By the time he died the Quakers of Philadelphia had resolved to expel every slave "
        "trader from their community, which is not a coincidence anyone recorded at the time.",
        "It is high time we told his story again.",
        "The record of what he did survives only because a printer thought it worth keeping.",
        "He was buried in an unmarked grave, beside Sarah.",
    ])
    w = CE.writtenness(published_like)
    # This fixture is deliberately MORE solo-heavy than any real text in the corpus, to
    # prove the point at the extreme. Saying it is "inside the published range" would be
    # false -- 0.83 is well above 0.37 -- and the diagnostic must say so without turning
    # it into a defect.
    check("this fixture is solo-heavy (%.2f)" % w["solo_ratio"],
          w["solo_ratio"] >= 0.30, w["solo_ratio"])
    check("  solo_ratio is labelled TELEMETRY_ONLY",
          w["solo_ratio_interpretation"] == "TELEMETRY_ONLY")
    check("  and is not a defect signal", w["solo_ratio_is_a_defect_signal"] is False)
    check("  the published range is carried with it",
          w["solo_ratio_published_range"] == (0.0, 0.37))
    check("  above the published range is reported honestly, and still not a defect (%s)"
          % w["solo_ratio_vs_published"],
          w["solo_ratio_vs_published"] == "ABOVE_PUBLISHED_RANGE_STILL_NOT_A_DEFECT",
          w["solo_ratio_vs_published"])
    check("  the SIGNPOST band is clean despite the solo paragraphs (%s)"
          % w["signpost_reading"]["band"],
          w["signpost_reading"]["band"] == "WITHIN_PUBLISHED_RANGE",
          w["signpost_reading"])
    check("  and that band declares it applies to the signpost rate only",
          w["signpost_reading"]["applies_to"] == "SIGNPOST_OPENER_RATE_ONLY")
    check("  the two readings are named separately in the summary line",
          "signpost_reading=" in w["interpretation"]
          and "solo_ratio=" in w["interpretation"]
          and "TELEMETRY_ONLY" in w["interpretation"], w["interpretation"])
    check("  nothing in the diagnostic asserts a defect",
          "defect" not in w["interpretation"].lower(), w["interpretation"])


def test_repeated_structural_openers_are_detected():
    """B: prose whose paragraphs announce their structural job is caught."""
    heavy = "\n\n".join([
        "The room was built of salt brick and set partway into the ground.",
        "So now the question is what the record could carry.",
        "But first, the list itself.",
        "Go back to the sand for a moment.",
        "Read that again and notice what kind of description it is.",
        "Which brings us to the ranking.",
        "The point is that the account kept what the materials meant.",
        "That is an odd building to make.",
        "The answer was mostly things you cannot look at.",
        "Now consider the eight items one at a time.",
        "And then it was over, and the pavilions came down.",
        "This is a familiar shape to anyone who has read a citation.",
    ])
    w = CE.writtenness(heavy)
    check("most paragraphs are caught as structural openers (%d of %d)"
          % (len(w["signpost_openers"]), w["paragraphs"]),
          len(w["signpost_openers"]) >= 8, w["signpost_openers"])
    check("  the rate is above every published text measured (%.3f > 0.125)"
          % w["signpost_rate"], w["signpost_rate"] > 0.125, w["signpost_rate"])
    check("  and the band says so", w["signpost_reading"]["band"] == "ARCHITECTURE_VISIBLE",
          w["signpost_reading"])
    check("  even when told it is an argument essay, the rate is still too high",
          CE.writtenness(heavy, form="ARGUMENTATIVE_ESSAY")["signpost_reading"]["band"]
          == "ARCHITECTURE_VISIBLE")


def test_one_or_two_transitions_do_not_produce_an_exaggerated_diagnosis():
    """C: an occasional legitimate transition is not an indictment."""
    mostly_clean = "\n\n".join([
        "The detector registered a strange event on 16 June 2023, and the nucleus of a "
        "xenon atom appeared to have taken a hard knock.",
        "The team examined every background process it could name and found none that "
        "would account for what the instrument had recorded that night.",
        "Now look at the statistics, because they are where the claim thins out.",
        "The strongest models reach a local significance of 3.4 sigma, and after "
        "correction for the number of models tried, 2.6 remains.",
        "Particle physics conventionally wants five before anyone calls something a "
        "discovery, and the paper has not yet been through peer review.",
        "A theoretical physicist in Melbourne who was not involved called it an "
        "interesting observation and said it was very early.",
        "The experiment runs until at least 2028, and a second event of the same shape "
        "would change the arithmetic considerably.",
        "For now the tank of ultrapure liquid xenon sits a mile underground, waiting.",
        "Twenty years of similar hints have come and gone in this field.",
        "The collaboration published the anomaly anyway, which is itself a choice.",
        "It asked other physicists what they made of it.",
        "That is where the matter rests.",
    ])
    w = CE.writtenness(mostly_clean)
    check("only a couple of openers are caught (%d of %d)"
          % (len(w["signpost_openers"]), w["paragraphs"]),
          1 <= len(w["signpost_openers"]) <= 3, w["signpost_openers"])
    check("  the diagnosis is not ARCHITECTURE_VISIBLE (%s)"
          % w["signpost_reading"]["band"],
          w["signpost_reading"]["band"] != "ARCHITECTURE_VISIBLE", w["signpost_reading"])
    check("  and the reason given is the small absolute count, not the rate",
          "too few" in w["signpost_reading"]["note"], w["signpost_reading"]["note"])


def test_argument_forms_may_signpost_more_than_narrative():
    """D: the band is form-sensitive, because the corpus says it must be."""
    essay = "\n\n".join([
        "Twenty years ago climate denial was a problem of the right, and today something "
        "similar is happening on the left about artificial intelligence.",
        "Now look at what the capability curve has actually done since 2022.",
        "In 2022 the answer was about thirty seconds. In 2023 it was four minutes. In "
        "2024 it was forty minutes. In 2025 it was six hours.",
        "The people building these systems expect the line to keep climbing, and several "
        "of them have said so on the record.",
        "A microbiologist hired to pressure-test one model was shaken enough by what it "
        "told him that he went for a walk to clear his head.",
        "Two countries lead this race, and inside them a handful of corporations are "
        "building the most powerful tools in the history of the species.",
        "Political scientists have a name for what happens to countries that strike oil, "
        "and the mechanism is about who the ruler needs.",
        "Rulers have always needed money, and the only place to get it was their subjects.",
        "So what does work, if shutting it down does not?",
        "State capacity, international coordination, and building in the free world.",
        "None of it happens automatically, and the eight-hour day was taken rather than given.",
        "The models of today are the worst models we will ever have.",
    ])
    as_narrative = CE.writtenness(essay)
    as_argument = CE.writtenness(essay, form="ARGUMENTATIVE_ESSAY")
    check("the same text signposts at a Bregman-like rate (%.3f)"
          % as_narrative["signpost_rate"],
          0.02 <= as_narrative["signpost_rate"] <= 0.20, as_narrative["signpost_rate"])
    check("  read as narrative it is flagged as elevated (%s)"
          % as_narrative["signpost_reading"]["band"],
          as_narrative["signpost_reading"]["band"] in ("ELEVATED_FOR_FORM",
                                                       "ARCHITECTURE_VISIBLE"))
    check("  read as argument it is ordinary (%s)"
          % as_argument["signpost_reading"]["band"],
          as_argument["signpost_reading"]["band"] == "WITHIN_PUBLISHED_RANGE",
          as_argument["signpost_reading"])
    check("  and the form used is reported either way",
          as_argument["signpost_reading"]["form_assumed"] == "ARGUMENTATIVE_ESSAY")


def test_short_texts_get_no_band_at_all():
    """The rate is unstable under ten paragraphs, so no reading is offered."""
    tiny = "A room was built of salt.\n\nSo go back to the sand.\n\nIt was brick."
    w = CE.writtenness(tiny)
    check("a 3-paragraph text gets INSUFFICIENT_PARAGRAPHS",
          w["signpost_reading"]["band"] == "INSUFFICIENT_PARAGRAPHS", w["signpost_reading"])


def test_pivot_paragraphs_are_telemetry_and_nothing_asks_for_them():
    """E-adjacent: the pivot finding is counted, never requested."""
    text = ("The room was built of salt brick and set partway into the ground, which is "
            "an unusual thing to do with a building on a beach.\n\n"
            "Genes cannot be undone. Poverty can.\n\n"
            "But what was it for?\n\n"
            "The account records the brick and not the room.")
    piv = CE.pivot_paragraph_candidates(text)
    # three: the verdict, the question, and the nine-word closing line. All are short
    # standalone paragraphs, which is exactly what the category describes.
    check("short standalone paragraphs are counted", len(piv) == 3, piv)
    check("  a question pivot is labelled", any(p["shape"] == "QUESTION" for p in piv), piv)
    check("  a verdict pivot is labelled", any(p["shape"] == "STATEMENT" for p in piv), piv)
    src = pathlib.Path(CE.__file__).read_text()
    check("no generator rule, target or instruction for pivots exists in the module",
          "PIVOT_TARGET" not in src and "require_pivot" not in src
          and "produce a pivot" not in src.lower())
    check("  and the module says so in words",
          "COUNTED, NEVER REQUESTED" in src)


def test_the_calibration_evidence_is_carried_with_the_code():
    cal = CE.WRITTENNESS_CALIBRATION
    check("the corpus is named", "Bregman" in cal["corpus"] and "exemplars" in cal["corpus"])
    check("narrative and argument signpost maxima are both recorded",
          cal["signpost_per_paragraph"]["narrative_exemplars"]["max"] == 0.025
          and cal["signpost_per_paragraph"]["argument_essay_bregman"]["max"] == 0.125)
    check("the Jia pre-audit rate is recorded",
          cal["signpost_per_paragraph"]["jia_pre_audit"] == 0.333)
    check("solo_ratio carries its own DESCRIPTIVE_ONLY verdict",
          cal["solo_ratio"]["verdict"].startswith("DESCRIPTIVE_ONLY"))
    check("the published solo range contains the Jia value",
          cal["solo_ratio"]["narrative_exemplars"]["min"]
          <= cal["solo_ratio"]["jia_pre_audit"]
          <= cal["solo_ratio"]["argument_essay_bregman"]["max"])
    check("the language limitation is stated", "English-only" in cal["not_calibrated_for"])


def test_the_architect_rhetoric_detector_finds_the_transcription_channel():
    staged = {"crip_turn": "Go back to the sand and ask the reader to notice what is "
                           "missing.",
              "ending_move": "Return to the salt walls and land on the taste.",
              "beats": [{"beat_id": "B1", "happens": "Open with the salt.",
                         "why_reader_wants_next": "End the beat on a punchline."}]}
    errs = CE.validate_architect_is_semantic(staged)
    check("rhetorical direction in architect fields is caught", len(errs) >= 3, errs)
    for want in ("crip_turn", "ending_move", "B1"):
        check("  %s is named" % want, any(want in e for e in errs))
    semantic = {"crip_turn": "The sand's symbolic description is re-read as the record's "
                             "own mechanism.",
                "ending_move": "Close on the salt as a material with a property the "
                               "record does not carry.",
                "beats": [{"beat_id": "B1", "happens": "The room and its material.",
                           "why_reader_wants_next": "A salt building is strange."}]}
    check("semantic beat purpose passes", CE.validate_architect_is_semantic(semantic) == [],
          CE.validate_architect_is_semantic(semantic))


# ── the frozen result ────────────────────────────────────────────────────────
def test_the_frozen_continuity_final_holds_every_gate():
    b, c = EXP / "jia.NEW.final.md", EXP / "jia.NEW.continuity.final.md"
    ed = EXP / "jia.continuity.final.edits.json"
    if not (b.exists() and c.exists() and ed.exists()):
        check("frozen continuity artefacts present", False, "missing")
        return
    before, edits = b.read_text(), json.loads(ed.read_text())
    draft = CE.label_draft(before)
    out = CE.apply_edits(edits)
    check("lineage is clean", CE.validate_lineage(edits, draft) == [],
          CE.validate_lineage(edits, draft))
    check("every draft sentence is accounted for",
          set().union(*[set(e["parents"]) for e in edits]) == set(draft),
          set(draft) - set().union(*[set(e["parents"]) for e in edits]))
    check("semantic delta is clean", CE.validate_semantic_delta(before, out) == [],
          CE.validate_semantic_delta(before, out))
    d = CE.semantic_delta(before, out)
    check("  no added factual surface",
          not any(d["added_surface"].values()), d["added_surface"])
    check("  no added relation classes", not d["added_relation_classes"],
          d["added_relation_classes"])
    w0, w1 = CE.writtenness(before), CE.writtenness(out)
    # The SELECTED final is the minimal edit, not the aggressive one, and the contract
    # asserted here is reduction rather than elimination. That is deliberate and is the
    # campaign's main finding: an aggressive merge did drive solo paragraphs and signpost
    # openers to zero, and two independent evaluators then preferred the minimal version
    # anyway -- because merging dissolved the quoted specimen the argument turns on
    # ("The sand *embodied strength and fragility*") and a solo lens reader could no
    # longer recover the Crip insight from the aggressive text. Naturalness and lens
    # legibility traded against each other, and the lens won.
    # Descriptive: this is what the selected edit did to the fixture. It is NOT a claim
    # that fewer solo paragraphs is better -- see the calibration tests above.
    check("solo paragraphs changed as this fixture records (%d -> %d)"
          % (w0["solo_paragraphs"], w1["solo_paragraphs"]),
          w1["solo_paragraphs"] < w0["solo_paragraphs"], w1["solo_paragraphs"])
    check("signpost openers were reduced (%d -> %d)"
          % (len(w0["signpost_openers"]), len(w1["signpost_openers"])),
          len(w1["signpost_openers"]) < len(w0["signpost_openers"]),
          w1["signpost_openers"])
    check("paragraphs were re-owned by this stage (%d -> %d)"
          % (w0["paragraphs"], w1["paragraphs"]), w1["paragraphs"] < w0["paragraphs"])
    check("the opening was left alone",
          out.startswith("On a beach in Bali, someone built a room out of salt."))
    check("the quoted specimen at the pivot survived",
          "embodied strength and fragility*" in out or "*embodied" in out, out[:0])
    check("the closing line still stands alone",
          out.rstrip().endswith("The account has it as brick.")
          and out.rstrip().split("\n\n")[-1].strip() == "The account has it as brick.")
    check("NO_CHANGE was actually used", any(e["operation"] == CE.NO_CHANGE
                                             for e in edits))
    check("signposting was actually deleted", any(e["operation"] == CE.DELETE
                                                  for e in edits))
    # the losing aggressive version is retained as evidence, not discarded
    agg = EXP / "jia.NEW.continuity.v3-aggressive.md"
    check("the aggressive variant is kept for comparison", agg.exists())
    if agg.exists():
        wa = CE.writtenness(agg.read_text())
        check("  it did reach zero solo paragraphs and zero signposts (and lost anyway)",
              wa["solo_paragraphs"] == 0 and not wa["signpost_openers"])
        check("  but it lost the quoted specimen",
              "embodied strength and fragility*" not in agg.read_text())


def main() -> None:
    for fn in (test_no_output_sentence_may_have_zero_parents,
               test_the_editor_cannot_invent_a_proposition_while_claiming_a_parent,
               test_relations_are_caught_even_with_no_new_nouns,
               test_cut_material_and_the_crip_turn,
               test_paragraph_boundaries_are_not_dictated_by_beats,
               test_writtenness_finds_performance_slots_and_signposts,
               test_solo_paragraphs_alone_are_not_a_writtenness_defect,
               test_repeated_structural_openers_are_detected,
               test_one_or_two_transitions_do_not_produce_an_exaggerated_diagnosis,
               test_argument_forms_may_signpost_more_than_narrative,
               test_short_texts_get_no_band_at_all,
               test_pivot_paragraphs_are_telemetry_and_nothing_asks_for_them,
               test_the_calibration_evidence_is_carried_with_the_code,
               test_the_architect_rhetoric_detector_finds_the_transcription_channel,
               test_the_frozen_continuity_final_holds_every_gate):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL CONTINUITY EDITOR TESTS PASSED")


if __name__ == "__main__":
    main()
