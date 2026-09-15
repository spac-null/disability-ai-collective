#!/usr/bin/env python3
"""
materiality_test.py -- the publication consequence of an unsupported factual finding.

Safety is authoritative about SUPPORT and is not touched by any of this. These tests pin
the separate question: does a finding STOP publication?

    raw_safety_decision = HOLD
    materiality         = MINOR
    effective_decision  = PASS_WITH_MINOR_FINDINGS

The two regression fixtures are the real consecutive production runs that were lost to
one word -- 2026-09-14 (production-20260914T070213Z-d20b3807) and 2026-09-15
(production-20260915T072045Z-40294a3a). Their blocking strings and paragraphs are
reproduced verbatim so the test is deterministic and offline.

No model calls, no network, no evidence root, no production database.

Run (from repo root):
  python3 automation/materiality_test.py
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import materiality as MAT                       # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


# ── the real runs ───────────────────────────────────────────────────────────────────

SEP14_BLOCKING = ("NEW_UNSUPPORTED_FACTS: the final prose carries factual surface the "
                  "packet never granted -- numbers=[] entities=['Italian'] sensory=[]")
SEP14_TITLE = "# Three beds, or four, at via Gambini"
SEP14_PARA = (
    "Shortly before 8pm, patients at the via Gambini Mental Health Centre in Trieste are "
    "moved out — to another of the city's mental health centres, or to the diagnosis "
    "and treatment ward of the Maggiore hospital, the psychiatric ward where a person can "
    "be admitted as an inpatient. A Mental Health Centre, CSM in Italian, is a "
    "neighbourhood centre run by the health authority, the one a person is registered "
    "with and can walk into for help. Trieste has four.")
SEP14_ARTICLE = SEP14_TITLE + "\n\n" + SEP14_PARA

SEP15_PARA = (
    "In the Italian region of Lombardy, a Comune — the municipality a person lives in "
    "— has ninety days from the submission of the request to carry out the Progetto "
    "di vita process.")
SEP15_ARTICLE = "# Ninety days from the request\n\n" + SEP15_PARA


def _sa(blocking):
    return {"status": "HOLD", "blocking": list(blocking)}


def _minor_reply(tokens):
    return {"findings": [{"finding": t, "classification": "MINOR",
                          "counterfactual": "the sentence reads identically without it; "
                                            "no fact in the piece depends on it",
                          "changes_reader_understanding": "NO",
                          "affected_dimensions": ["none"],
                          "reason": "a peripheral language gloss"} for t in tokens]}


# ── 1. the fixtures ─────────────────────────────────────────────────────────────────

def test_sep14_is_adjudicable_and_minor():
    buckets, eligible = MAT.parse_blocking([SEP14_BLOCKING])
    check("14 Sep: blocking parses as an eligible category", eligible)
    check("14 Sep: the finding is the entity 'Italian'",
          buckets["entities"] == ["Italian"], buckets)
    check("14 Sep: nothing is hard-material",
          MAT.hard_material(buckets, SEP14_ARTICLE, {}) == [])
    toks = MAT.adjudicable(buckets, SEP14_ARTICLE, {})
    check("14 Sep: 'Italian' is adjudicable", toks == ["Italian"], toks)
    sentence, para = MAT.locate(SEP14_ARTICLE, "Italian")
    check("14 Sep: the containing sentence is located",
          "CSM in Italian" in sentence, sentence[:80])
    v = MAT.verdict(_minor_reply(toks), toks)
    check("14 Sep: verdict is MINOR", v["classification"] == "MINOR", v)
    check("14 Sep: publication may continue", v["may_continue"] is True, v)


def test_sep15_is_adjudicable_and_minor_on_its_own():
    """The 15 Sep finding, taken alone, is the same peripheral gloss. (The run itself
    also discarded continuity for an added CAUSAL relation, which the composition layer
    refuses separately -- see test_continuity_discard_is_not_adjudicable.)"""
    buckets, eligible = MAT.parse_blocking([SEP14_BLOCKING])   # same finding shape
    toks = MAT.adjudicable(buckets, SEP15_ARTICLE, {})
    check("15 Sep: 'Italian' is adjudicable", toks == ["Italian"], toks)
    sentence, _ = MAT.locate(SEP15_ARTICLE, "Italian")
    check("15 Sep: the containing sentence is located",
          "Italian region of Lombardy" in sentence, sentence[:80])
    v = MAT.verdict(_minor_reply(toks), toks)
    check("15 Sep: publication may continue", v["may_continue"] is True, v)


def test_raw_finding_is_never_rewritten():
    """The point of the design: nothing here licenses the claim."""
    sa = _sa([SEP14_BLOCKING])
    before = {"status": sa["status"], "blocking": list(sa["blocking"])}
    buckets, _ = MAT.parse_blocking(sa["blocking"])
    MAT.hard_material(buckets, SEP14_ARTICLE, {})
    MAT.adjudicable(buckets, SEP14_ARTICLE, {})
    MAT.verdict(_minor_reply(["Italian"]), ["Italian"])
    check("the Safety finding is not mutated by adjudication",
          sa["status"] == before["status"] and sa["blocking"] == before["blocking"]
          and "unsupported" not in sa["status"].lower(), sa)
    check("the raw finding still names the unsupported element",
          "entities=['Italian']" in sa["blocking"][0])


# ── 2. hard MATERIAL overrides, decided before any model call ───────────────────────

def test_hard_material_number():
    b, _ = MAT.parse_blocking(["NEW_UNSUPPORTED_FACTS: ... numbers=['90000'] "
                               "entities=[] sensory=[]"])
    hard = MAT.hard_material(b, "# T\n\nAbout 90000 people.", {})
    check("an unsupported NUMBER is hard-material", [t for t, _ in hard] == ["90000"], hard)
    check("...and is never adjudicable", MAT.adjudicable(b, "x", {}) == [])


def test_hard_material_invented_scene():
    for channel in ("sensory", "scene", "spatial"):
        b, _ = MAT.parse_blocking(["NEW_UNSUPPORTED_FACTS: ... numbers=[] entities=[] "
                                   "%s=['quiet']" % channel])
        hard = MAT.hard_material(b, "# T\n\nThe quiet room.", {})
        check("unsupported %s surface is hard-material" % channel,
              [t for t, _ in hard] == ["quiet"], hard)


def test_hard_material_quotation():
    art = ('# T\n\nShe said "the Ministry refused us" that morning.')
    b, _ = MAT.parse_blocking(["NEW_UNSUPPORTED_FACTS: ... numbers=[] "
                               "entities=['Ministry'] sensory=[]"])
    hard = MAT.hard_material(b, art, {})
    check("an entity inside a QUOTATION is hard-material",
          [t for t, _ in hard] == ["Ministry"], hard)
    check("...and is never adjudicable", MAT.adjudicable(b, art, {}) == [])


def test_hard_material_thesis_surface():
    art = "# The Ministry that stopped answering\n\nA paragraph about the Ministry."
    b, _ = MAT.parse_blocking(["NEW_UNSUPPORTED_FACTS: ... numbers=[] "
                               "entities=['Ministry'] sensory=[]"])
    hard = MAT.hard_material(b, art, {})
    check("an entity in the TITLE is hard-material",
          [t for t, _ in hard] == ["Ministry"], hard)
    art2 = "# Something else\n\nA paragraph about the Ministry."
    hard2 = MAT.hard_material(b, art2, {"dek": "How the Ministry stopped answering"})
    check("an entity in the DEK is hard-material",
          [t for t, _ in hard2] == ["Ministry"], hard2)


def test_unknown_blocking_category_is_ineligible():
    _, eligible = MAT.parse_blocking([SEP14_BLOCKING, "CUT_AUDIT_BLIND: derivation bug"])
    check("an unfamiliar blocking category makes the whole attempt ineligible",
          eligible is False)


# ── 3. the model may not buy its way through ────────────────────────────────────────

def test_model_material_holds():
    reply = {"findings": [{"finding": "Ministry", "classification": "MATERIAL",
                           "counterfactual": "the allegation loses its subject",
                           "changes_reader_understanding": "YES",
                           "affected_dimensions": ["allegation"],
                           "reason": "names who is accused"}]}
    v = MAT.verdict(reply, ["Ministry"])
    check("a MATERIAL verdict holds", v["may_continue"] is False, v)


def test_minor_but_changes_understanding_holds():
    r = _minor_reply(["X"])
    r["findings"][0]["changes_reader_understanding"] = "YES"
    check("MINOR + changes_reader_understanding=YES holds",
          MAT.verdict(r, ["X"])["may_continue"] is False)


def test_minor_but_names_a_dimension_holds():
    for dim in ("carrier", "chronology", "causality", "allegation", "argument",
                "conclusion"):
        r = _minor_reply(["X"])
        r["findings"][0]["affected_dimensions"] = [dim]
        check("MINOR that names %s holds" % dim,
              MAT.verdict(r, ["X"])["may_continue"] is False)


def test_none_plus_dimension_is_contradictory():
    r = _minor_reply(["X"])
    r["findings"][0]["affected_dimensions"] = ["none", "argument"]
    check("'none' paired with a dimension is contradictory and holds",
          MAT.verdict(r, ["X"])["may_continue"] is False)


def test_unexplained_verdict_holds():
    for field in ("counterfactual", "reason"):
        r = _minor_reply(["X"])
        r["findings"][0][field] = ""
        check("a verdict with no %s holds" % field,
              MAT.verdict(r, ["X"])["may_continue"] is False)


def test_malformed_or_partial_replies_hold():
    check("no findings holds", MAT.verdict({}, ["X"])["may_continue"] is False)
    check("non-list findings holds",
          MAT.verdict({"findings": "MINOR"}, ["X"])["may_continue"] is False)
    check("unadjudicated finding holds",
          MAT.verdict(_minor_reply(["X"]), ["X", "Y"])["may_continue"] is False)
    check("findings not asked about hold",
          MAT.verdict(_minor_reply(["X", "Z"]), ["X"])["may_continue"] is False)
    r = _minor_reply(["X"])
    r["findings"][0]["classification"] = "PROBABLY_FINE"
    check("an invented classification holds", MAT.verdict(r, ["X"])["may_continue"] is False)
    r2 = _minor_reply(["X"])
    r2["findings"][0]["affected_dimensions"] = ["vibes"]
    check("an invented dimension holds", MAT.verdict(r2, ["X"])["may_continue"] is False)


def test_every_finding_must_be_minor():
    r = _minor_reply(["X", "Y"])
    r["findings"][1]["classification"] = "MATERIAL"
    check("one MATERIAL among several holds",
          MAT.verdict(r, ["X", "Y"])["may_continue"] is False)


def main():
    for fn in [test_sep14_is_adjudicable_and_minor,
               test_sep15_is_adjudicable_and_minor_on_its_own,
               test_raw_finding_is_never_rewritten,
               test_hard_material_number,
               test_hard_material_invented_scene,
               test_hard_material_quotation,
               test_hard_material_thesis_surface,
               test_unknown_blocking_category_is_ineligible,
               test_model_material_holds,
               test_minor_but_changes_understanding_holds,
               test_minor_but_names_a_dimension_holds,
               test_none_plus_dimension_is_contradictory,
               test_unexplained_verdict_holds,
               test_malformed_or_partial_replies_hold,
               test_every_finding_must_be_minor]:
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL MATERIALITY TESTS PASSED")


if __name__ == "__main__":
    main()
