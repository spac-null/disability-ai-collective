#!/usr/bin/env python3
"""
lens_wire_contract_test.py -- the lens validators run against the shape the architect
actually emits, not the shape a fixture happened to carry.

WHY THIS FILE EXISTS, SEPARATELY FROM story_architecture_test.py. That suite already has
ten assertions on `validate_lens_embodiment`, and every one of them passed while the
function returned [] on the first line for every architecture production ever built. They
passed because they inject the WORTH-stage lens -- `{"verdict": ..., "evidence_ids": ...}`
-- and the production caller passes the ARCHITECTURE's `final_lens`, which
ARCHITECT_SCHEMA gives neither field. A test that supplies the shape the wire does not is
not testing the wire.

So the fixture here is built from ARCHITECT_SCHEMA itself, and the first assertion is that
the schema still does not mention `verdict` -- if someone adds one, this file should be the
thing that notices, not a production run.

Behavioural, no provider, no network, no filesystem.
"""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP   # noqa: E402
from new_engine_v1 import ledger as LG        # noqa: E402
from new_engine_v1 import story as ST         # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print("  PASS  %s" % label)
    else:
        FAILURES.append(label)
        print("  FAIL  %s   <- %r" % (label, detail))


SRC = ("The council published a ranking sheet in March. Ten entries were photographed "
       "for the catalogue. The catalogue was printed by a local firm. "
       "A servo was fitted to the display case.")


def _fact(fid, prop, span):
    return {"fact_id": fid, "proposition": prop, "claim_type": LG.POSITIVE,
            "claim_kind": "OCCURRENCE", "evidence_ids": ["S0"], "support_span": span,
            "entities": [], "scope": LG.WORLD, "corpus_size": 0,
            "prohibited_extensions": []}


LEDGER = {
    "F01": _fact("F01", "The council published a ranking sheet in March.",
                 "The council published a ranking sheet in March."),
    "F02": _fact("F02", "Ten entries were photographed for the catalogue.",
                 "Ten entries were photographed for the catalogue."),
    "F03": _fact("F03", "The catalogue was printed by a local firm.",
                 "The catalogue was printed by a local firm."),
    "F04": _fact("F04", "A servo was fitted to the display case.",
                 "A servo was fitted to the display case."),
}


def arch(**over) -> dict:
    """An architecture in the shape ARCHITECT_SCHEMA asks for -- every key, no extras."""
    a = {
        "article_type": "NARRATIVE_ARTICLE",
        "story_spine": "The council published a ranking sheet and ten entries were "
                       "photographed.",
        "opening_object_or_event": "the ranking sheet",
        "reader_initial_state": "a ranking sheet exists",
        "lens_realization": "IMPLICIT",
        "crip_turn_rereads": "B1",
        "turn": "",
        "crip_turn": "The ranking sheet records what could be photographed.",
        "ending_move": "the catalogue closes",
        "beats": [
            {"beat_id": "B1", "happens": "The council published a ranking sheet in March.",
             "concrete_carrier": "the ranking sheet", "facts_allowed": ["F01"],
             "concept_introduced": "", "beat_function": "REVEAL",
             "why_reader_wants_next": "the sheet leads to the entries",
             "must_not_say_yet": "the catalogue"},
            {"beat_id": "B2", "happens": "Ten entries were photographed for the catalogue.",
             "concrete_carrier": "the entry photographs", "facts_allowed": ["F02", "F01"],
             "concept_introduced": "", "beat_function": "REVEAL",
             "why_reader_wants_next": "the photographs lead to the printing",
             "must_not_say_yet": "the printer"},
            {"beat_id": "B3", "happens": "The catalogue was printed by a local firm.",
             "concrete_carrier": "the ranking sheet", "facts_allowed": ["F03", "F01"],
             "concept_introduced": "", "beat_function": "REVEAL",
             "why_reader_wants_next": "", "must_not_say_yet": ""},
        ],
        "use_facts": ["F01", "F02", "F03"],
        "primary_carrier": "F01",
        "evidence_roles": {"F01": "LOAD_BEARING", "F02": "SUPPORTING",
                           "F03": "SUPPORTING"},
        "supports": {"F02": ["F01"], "F03": ["F01"]},
        "use_quotes": [],
        "definitions": {},
        "cut_evidence": [{"evidence_id": "F04", "reason": "REDUNDANT_PROOF"}],
        "prohibitions": ["Do not invent a witness."],
        "final_lens": {
            "lens_claim": "A ranking sheet records what could be photographed.",
            "evidence_basis": ["F01", "F02"],
            "what_changes_for_the_reader": "the reader now understands the sheet as a "
                                           "record of photographability",
            "story_beat_before": "B1",
            "crip_turn": "The ranking sheet records what could be photographed.",
            "story_beat_after": "B3",
            "before_reading": "a ranking of design",
            "after_reading": "a ranking of photographability",
            "crip_turn_carrier": "the ranking sheet",
        },
    }
    fl = over.pop("final_lens", None)
    a.update(over)
    if fl:
        a["final_lens"] = dict(a["final_lens"], **fl)
    return copy.deepcopy(a)


def embodiment(a):
    """Exactly what check_architecture does at composition.py's LENS_EMBODIMENT line."""
    return ST.validate_lens_embodiment(a, a.get("final_lens") or {})


# ── the wire fact itself ──────────────────────────────────────────────────────
def test_the_architecture_schema_still_has_no_verdict():
    check("ARCHITECT_SCHEMA declares no `verdict` (the field the old guard read)",
          "verdict" not in CP.ARCHITECT_SCHEMA)
    check("a schema-shaped final_lens has no `verdict`",
          "verdict" not in arch()["final_lens"])
    check("and names its evidence `evidence_basis`, not `evidence_ids`",
          "evidence_basis" in arch()["final_lens"]
          and "evidence_ids" not in arch()["final_lens"])


# ── the checks the old guard skipped, on the real shape ───────────────────────
def test_a_clean_architecture_is_accepted():
    check("a schema-shaped architecture embodies its lens", embodiment(arch()) == [],
          embodiment(arch()))
    check("and check_architecture accepts it whole",
          CP.check_architecture(arch(), LEDGER) == [],
          CP.check_architecture(arch(), LEDGER))


def test_crip_turn_rereads_is_validated_at_all():
    """It has no other validator anywhere in the engine. Before this contract repair the
    only function that read it could not be reached, so any value at all was accepted."""
    a = arch()
    del a["crip_turn_rereads"]
    check("a turn with no declared antecedent is refused",
          any("crip_turn_rereads missing" in e for e in embodiment(a)), embodiment(a))

    a2 = arch(crip_turn_rereads="B99")
    check("a turn pointing at a beat that does not exist is refused",
          any("not a beat" in e for e in embodiment(a2)), embodiment(a2))
    check("and check_architecture refuses it too",
          any("LENS_EMBODIMENT" in e for e in CP.check_architecture(a2, LEDGER)),
          CP.check_architecture(a2, LEDGER))

    a3 = arch(crip_turn_rereads="B3")
    check("a turn re-reading the FINAL beat is refused",
          any("reader has had time" in e for e in embodiment(a3)), embodiment(a3))

    a4 = arch(crip_turn_rereads="B2")
    check("a turn naming nothing from the beat it claims to re-read is refused",
          any("does not name anything from B2" in e for e in embodiment(a4)),
          embodiment(a4))


def test_the_lens_may_not_rest_on_evidence_no_beat_shows():
    """`evidence_basis` is read now, so a lens standing on a CUT fact is visible. F04 is
    in the ledger and in cut_evidence, so validate_final_lens's `basis - set(ledger)`
    check cannot see it -- this is the check that can."""
    a = arch(final_lens={"evidence_basis": ["F04"]})
    check("a lens resting on a cut fact is refused",
          any("cites evidence the beats never show" in e for e in embodiment(a)),
          embodiment(a))
    check("and check_architecture refuses it too",
          any("LENS_EMBODIMENT" in e for e in CP.check_architecture(a, LEDGER)),
          CP.check_architecture(a, LEDGER))


def test_the_worth_shape_is_still_read():
    """The frozen loop-3 artefacts carry `evidence_ids`. Reading only the architecture's
    field name would have quietly stopped exercising them."""
    a = arch()
    fl = dict(a["final_lens"])
    fl.pop("evidence_basis")
    fl["evidence_ids"] = ["F04"]
    a["final_lens"] = fl
    check("a Worth-shaped `evidence_ids` is still checked",
          any("cites evidence the beats never show" in e for e in embodiment(a)),
          embodiment(a))
    check("lens_evidence_ids reads both names, evidence_basis first",
          ST.lens_evidence_ids({"evidence_basis": ["F01"], "evidence_ids": ["F02"]})
          == {"F01"}
          and ST.lens_evidence_ids({"evidence_ids": ["F02"]}) == {"F02"}
          and ST.lens_evidence_ids({"evidence_basis": "F03"}) == {"F03"}
          and ST.lens_evidence_ids({}) == set())


def test_a_hold_is_exempt():
    """What the old `verdict` guard was for: an architecture with no story to embody."""
    for t in (ST.HOLD_NO_STORY, ST.HOLD_WRONG_PUBLICATION):
        a = arch(article_type=t)
        del a["crip_turn_rereads"]
        check("%s needs no embodied turn" % t, embodiment(a) == [], embodiment(a))


# ── the dead packet field ─────────────────────────────────────────────────────
def test_the_packet_no_longer_carries_a_permanently_empty_lens():
    pk = ST.build_packet(arch(), arch()["final_lens"], LG.propositions(LEDGER))
    check("build_packet emits no `lens` key", "lens" not in pk, sorted(pk))
    check("and the leak scan no longer lists one",
          "lens" not in ST._GENERATED_PACKET_FIELDS, ST._GENERATED_PACKET_FIELDS)
    txt = ST.render(pk)
    check("the machine-side lens_claim still does not reach the Writer",
          arch()["final_lens"]["lens_claim"] not in txt, txt[:200])
    check("and what the reader must arrive at still does, as crip_turn",
          arch()["crip_turn"] in txt, txt[:200])


def main():
    for fn in (test_the_architecture_schema_still_has_no_verdict,
               test_a_clean_architecture_is_accepted,
               test_crip_turn_rereads_is_validated_at_all,
               test_the_lens_may_not_rest_on_evidence_no_beat_shows,
               test_the_worth_shape_is_still_read,
               test_a_hold_is_exempt,
               test_the_packet_no_longer_carries_a_permanently_empty_lens):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL LENS WIRE CONTRACT TESTS PASSED")


if __name__ == "__main__":
    main()
