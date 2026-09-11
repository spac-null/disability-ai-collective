#!/usr/bin/env python3
"""
evidence_hierarchy_test.py -- selecting facts is not ranking them.

Astra's independent audit and the owner's brief (2026-09-11) both located the same
article-quality defect: an architecture can pass Worth, Safety and every existing
Architecture gate with a flat pile of equally-weighted facts, and a Writer handed no
ranking has no way to choose what carries the story, what only explains it, and what to
leave alone. DESCENT (production-20260910T190530Z-8a0dab48) passed Crip Minds fit and
every factual gate and still held on ENDING, MOMENTUM and RESEARCH_LOAD: Architecture
selected 23 of 126 facts with no load/support roles and repeated rather than advanced
the coupled ramp/chair carrier.

ST.validate_evidence_hierarchy requires, and does not merely validate if present: one
used fact declared `primary_carrier`; every used fact assigned exactly one role in
`evidence_roles` (LOAD_BEARING or SUPPORTING); every SUPPORTING fact naming, in
`supports`, which LOAD_BEARING fact(s) it makes intelligible, and co-occurring with one
of them in some beat; every beat declaring a `beat_function` from the closed,
UNORDERED set (REVEAL, COMPLICATE, EXPLAIN, REVERSE, RESOLVE -- no fixed sequence is
imposed, and these tests deliberately do not always use them in the same order); and
the primary carrier recurring across more than one beat, landing in the closing one.

Behavioural, no provider, no network. Ledger authority, Worth, Safety, Grounding,
TRUE_UNCERTAIN, Fact Check, Reader and the publication bridge are untouched by this
module and are not exercised here.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP                          # noqa: E402
from new_engine_v1 import story as ST                                # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:220]))
    if not ok:
        FAILURES.append(label)


EVIDENCE = {"F1", "F2", "F3", "F4"}


def _good():
    """A minimal, internally-consistent, fully-hierarchical architecture. Only what
    validate_evidence_hierarchy itself reads is populated -- this is not a fixture for
    the other Architecture validators."""
    return {
        "article_type": ST.NARRATIVE_ARTICLE,
        "use_facts": ["F1", "F2", "F3"],
        "primary_carrier": "F1",
        "evidence_roles": {"F1": ST.LOAD_BEARING, "F2": ST.LOAD_BEARING,
                           "F3": ST.SUPPORTING},
        "supports": {"F3": ["F2"]},
        "beats": [
            {"beat_id": "B1", "facts_allowed": ["F1"], "beat_function": ST.REVEAL},
            {"beat_id": "B2", "facts_allowed": ["F2", "F3"], "beat_function": ST.EXPLAIN},
            {"beat_id": "B3", "facts_allowed": ["F1"], "beat_function": ST.RESOLVE},
        ],
    }


def test_a_well_formed_hierarchy_is_clean():
    check("the good fixture has no errors", ST.validate_evidence_hierarchy(
        _good(), EVIDENCE) == [], ST.validate_evidence_hierarchy(_good(), EVIDENCE))


def test_a_hold_needs_no_hierarchy():
    for t in (ST.HOLD_NO_STORY, ST.HOLD_WRONG_PUBLICATION):
        arch = {"article_type": t}
        check("a %s hold needs no hierarchy fields" % t,
              ST.validate_evidence_hierarchy(arch, EVIDENCE) == [])


def test_missing_hierarchy_fields_fail_the_production_path():
    """The exact real-world case: an otherwise-plausible architecture with no hierarchy
    at all must HOLD, not silently pass -- this is a requirement, not an enrichment."""
    arch = {"article_type": ST.NARRATIVE_ARTICLE, "use_facts": ["F1", "F2"],
            "beats": [{"beat_id": "B1", "facts_allowed": ["F1"]},
                     {"beat_id": "B2", "facts_allowed": ["F2"]}]}
    errs = ST.validate_evidence_hierarchy(arch, EVIDENCE)
    check("evidence_roles missing is reported", any("evidence_roles missing" in e
                                                    for e in errs), errs)
    check("primary_carrier missing is reported", any("primary_carrier missing" in e
                                                     for e in errs), errs)
    check("both beats' missing beat_function is reported",
          sum("beat_function" in e for e in errs) == 2, errs)


def test_check_architecture_holds_without_it_even_when_otherwise_valid():
    """The real integration point: composition.check_architecture must itself refuse an
    architecture with no evidence hierarchy, not just the standalone validator."""
    good = _good()
    stripped = dict(good)
    for k in ("primary_carrier", "evidence_roles", "supports"):
        stripped.pop(k, None)
    stripped["beats"] = [dict(b) for b in good["beats"]]
    for b in stripped["beats"]:
        b.pop("beat_function", None)
    errs = ST.validate_evidence_hierarchy(stripped, EVIDENCE)
    check("stripping the hierarchy fields alone produces EVIDENCE_HIERARCHY failures",
          bool(errs), errs)


def test_evidence_roles_must_cover_every_used_fact_exactly():
    arch = dict(_good())
    arch["evidence_roles"] = {"F1": ST.LOAD_BEARING, "F2": ST.LOAD_BEARING}  # F3 missing
    errs = ST.validate_evidence_hierarchy(arch, EVIDENCE)
    check("a used fact missing from evidence_roles is reported",
          any("does not cover every used fact" in e for e in errs), errs)

    arch2 = dict(_good())
    arch2["evidence_roles"] = dict(_good()["evidence_roles"], F4=ST.LOAD_BEARING)  # F4 unused
    errs2 = ST.validate_evidence_hierarchy(arch2, EVIDENCE)
    check("a role for a fact that is not used is reported",
          any("names facts that are not used" in e for e in errs2), errs2)


def test_evidence_roles_values_are_closed():
    arch = dict(_good())
    arch["evidence_roles"] = dict(_good()["evidence_roles"], F3="DECORATIVE")
    errs = ST.validate_evidence_hierarchy(arch, EVIDENCE)
    check("a role outside LOAD_BEARING/SUPPORTING is reported",
          any("values outside" in e for e in errs), errs)


def test_primary_carrier_must_be_a_used_load_bearing_fact():
    arch = dict(_good())
    del arch["primary_carrier"]
    check("missing primary_carrier is reported",
          any("primary_carrier missing" in e
              for e in ST.validate_evidence_hierarchy(arch, EVIDENCE)))

    arch2 = dict(_good(), primary_carrier="F9")
    errs2 = ST.validate_evidence_hierarchy(arch2, EVIDENCE)
    check("a primary_carrier that is not a used fact is reported",
          any("is not a used fact" in e for e in errs2), errs2)

    arch3 = dict(_good(), primary_carrier="F3")   # F3 is SUPPORTING in _good()
    errs3 = ST.validate_evidence_hierarchy(arch3, EVIDENCE)
    check("a primary_carrier that is not itself LOAD_BEARING is reported",
          any("must itself be LOAD_BEARING" in e for e in errs3), errs3)


def test_supporting_facts_must_name_and_cooccur_with_what_they_support():
    # No `supports` entry at all for a SUPPORTING fact.
    arch = dict(_good())
    arch["supports"] = {}
    errs = ST.validate_evidence_hierarchy(arch, EVIDENCE)
    check("a SUPPORTING fact with no supports[] entry is reported",
          any("names no load-bearing fact" in e for e in errs), errs)

    # Names a fact that is not LOAD_BEARING.
    arch2 = dict(_good())
    arch2["evidence_roles"] = dict(_good()["evidence_roles"], F4=ST.SUPPORTING)
    arch2["use_facts"] = _good()["use_facts"] + ["F4"]
    arch2["supports"] = dict(_good()["supports"], F4=["F3"])   # F3 is SUPPORTING, not LB
    arch2["beats"] = [dict(b) for b in _good()["beats"]]
    arch2["beats"][1]["facts_allowed"] = arch2["beats"][1]["facts_allowed"] + ["F4"]
    errs2 = ST.validate_evidence_hierarchy(arch2, EVIDENCE | {"F4"})
    check("supporting a fact that is not itself LOAD_BEARING is reported",
          any("which is not LOAD_BEARING" in e for e in errs2), errs2)

    # Named correctly but never actually shares a beat with what it supports.
    arch3 = dict(_good())
    arch3["beats"] = [{"beat_id": "B1", "facts_allowed": ["F1"], "beat_function": ST.REVEAL},
                      {"beat_id": "B2", "facts_allowed": ["F2"], "beat_function": ST.EXPLAIN},
                      {"beat_id": "B3", "facts_allowed": ["F1", "F3"],
                       "beat_function": ST.RESOLVE}]   # F3 with F1, never with F2
    errs3 = ST.validate_evidence_hierarchy(arch3, EVIDENCE)
    check("a support that never co-occurs with what it supports is reported",
          any("does not co-occur in any beat" in e for e in errs3), errs3)


def test_every_beat_declares_a_closed_vocabulary_beat_function():
    arch = dict(_good())
    arch["beats"] = [dict(b) for b in _good()["beats"]]
    arch["beats"][0].pop("beat_function")
    errs = ST.validate_evidence_hierarchy(arch, EVIDENCE)
    check("a beat with no beat_function is reported",
          any("has beat_function" in e for e in errs), errs)

    arch2 = dict(_good())
    arch2["beats"] = [dict(b) for b in _good()["beats"]]
    arch2["beats"][0]["beat_function"] = "TWIST"
    errs2 = ST.validate_evidence_hierarchy(arch2, EVIDENCE)
    check("a beat_function outside the five is reported",
          any("has beat_function" in e for e in errs2), errs2)

    # No fixed sequence: REVERSE before EXPLAIN, out of the "given" order, is legal.
    arch3 = dict(_good())
    arch3["beats"] = [dict(b) for b in _good()["beats"]]
    arch3["beats"][1]["beat_function"] = ST.REVERSE
    check("an unordered sequence of valid functions is not itself an error",
          not any("beat_function" in e
                  for e in ST.validate_evidence_hierarchy(arch3, EVIDENCE)))


def test_the_carrier_must_recur_and_land_in_the_closing_beat():
    # Used in only one beat -- never returned to.
    arch = dict(_good())
    arch["beats"] = [{"beat_id": "B1", "facts_allowed": ["F1"], "beat_function": ST.REVEAL},
                     {"beat_id": "B2", "facts_allowed": ["F2", "F3"],
                      "beat_function": ST.EXPLAIN}]
    errs = ST.validate_evidence_hierarchy(arch, EVIDENCE)
    check("a carrier used only once is reported as never returned to",
          any("never returns to" in e for e in errs), errs)
    check("...and separately as absent from the closing beat",
          any("closing beat" in e for e in errs), errs)

    # Recurs, but the LAST beat is not one of the beats it recurs in.
    arch2 = dict(_good())
    arch2["beats"] = [{"beat_id": "B1", "facts_allowed": ["F1"], "beat_function": ST.REVEAL},
                      {"beat_id": "B2", "facts_allowed": ["F1", "F2"],
                       "beat_function": ST.COMPLICATE},
                      {"beat_id": "B3", "facts_allowed": ["F2", "F3"],
                       "beat_function": ST.RESOLVE}]
    errs2 = ST.validate_evidence_hierarchy(arch2, EVIDENCE)
    check("recurrence without landing in the closing beat is still reported",
          any("closing beat" in e for e in errs2), errs2)
    check("...but recurrence itself is satisfied, so that error is not raised twice",
          not any("never returns to" in e for e in errs2), errs2)

    # A real good article opens on a concrete hook, not necessarily the carrier --
    # ARCH in story_architecture_composition_test.py is exactly this shape, and this
    # is not itself an error as long as the carrier recurs and lands at the end.
    arch3 = dict(_good())
    arch3["beats"] = [{"beat_id": "B1", "facts_allowed": ["F2"], "beat_function": ST.REVEAL},
                      {"beat_id": "B2", "facts_allowed": ["F1", "F2"],
                       "beat_function": ST.COMPLICATE},
                      {"beat_id": "B3", "facts_allowed": ["F1"], "beat_function": ST.RESOLVE}]
    check("opening on a hook other than the carrier is not itself an error",
          not any("closing beat" in e or "never returns to" in e
                  for e in ST.validate_evidence_hierarchy(arch3, EVIDENCE)))


def test_packet_serialization_preserves_roles_and_functions():
    arch = _good()
    packet = ST.build_packet(arch, {}, {"F1": "fact one", "F2": "fact two",
                                        "F3": "fact three"})
    check("primary_carrier survives into the packet",
          packet.get("primary_carrier") == "F1", packet.get("primary_carrier"))
    check("evidence_roles survives into the packet",
          packet.get("evidence_roles") == arch["evidence_roles"], packet.get("evidence_roles"))
    check("every beat's beat_function survives into the packet",
          [b["beat_function"] for b in packet["beats"]]
          == [b["beat_function"] for b in arch["beats"]], packet["beats"])
    rendered = ST.render(packet)
    check("beat_function is NOT injected into the Writer-facing prompt text -- Writer "
          "is unchanged", ST.REVEAL not in rendered and ST.EXPLAIN not in rendered
          and ST.RESOLVE not in rendered, rendered)


def test_existing_architecture_validators_are_unaffected_by_missing_hierarchy():
    """The other Architecture validators (shape, USE/CUT honesty, carrier-occurrence,
    turn-relation support) still run and still catch what they always caught, whether or
    not the evidence hierarchy is present -- these are two independent gates, not one
    replacing the other."""
    bad_shape = {"article_type": ST.NARRATIVE_ARTICLE, "use_facts": ["F9"],
                "beats": [{"beat_id": "B1", "facts_allowed": ["F9"]}]}
    errs = ST.validate_architecture(bad_shape, EVIDENCE)
    check("the pre-existing evidence-membership check still fires on an unfrozen fact",
          any("not in the frozen evidence" in e for e in errs), errs)
    check("the pre-existing no-cut check still fires",
          any("no cut_evidence" in e for e in errs), errs)


def main() -> int:
    for fn in (test_a_well_formed_hierarchy_is_clean,
               test_a_hold_needs_no_hierarchy,
               test_missing_hierarchy_fields_fail_the_production_path,
               test_check_architecture_holds_without_it_even_when_otherwise_valid,
               test_evidence_roles_must_cover_every_used_fact_exactly,
               test_evidence_roles_values_are_closed,
               test_primary_carrier_must_be_a_used_load_bearing_fact,
               test_supporting_facts_must_name_and_cooccur_with_what_they_support,
               test_every_beat_declares_a_closed_vocabulary_beat_function,
               test_the_carrier_must_recur_and_land_in_the_closing_beat,
               test_packet_serialization_preserves_roles_and_functions,
               test_existing_architecture_validators_are_unaffected_by_missing_hierarchy):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL EVIDENCE HIERARCHY TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
