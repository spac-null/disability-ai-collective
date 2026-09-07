#!/usr/bin/env python3
"""
grounding_completion_test.py -- one completion pass, for a residue the Grounder has
already found and named. Not a retry loop.

WHY IT EXISTS. Two production runs made ONE unsupported claim in TWO places, and the one
repair reached only one of them:

  production-20260907T173433Z-ab65bb22 (Lubetkin)
      repaired: "...for buildings of exceptional interest."
      survived: "The Grade I listing marks the building as of exceptional interest..."

  production-20260907T191059Z-90687a49 (Daily Nous)
      repaired: "...a single dial standing for how far a democracy falls short of fully
                 transferring policy authority to the majority."
      survived: "The dial the veto is mapped onto measures the arrangement: it records
                 that redistributive authority can now be overridden..."

The Daily Nous pair shares almost no wording, and #104's "find every occurrence"
instruction was already live when it happened. What worked both times was the RECHECK: it
located the survivor exactly. So completion is aimed at a named residue, not at the
original problem.

WHAT THESE TESTS HOLD: the eligibility gate in every direction, that completion reuses
the SAME validator rather than a weaker one, that it can run at most once, and that a
survivor after completion still HOLDs.

Offline: real sentences from the retained runs, the real validator, no provider, no
network.

USAGE: python3 automation/grounding_completion_test.py
"""
from __future__ import annotations

import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP                          # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:240]))
    if not ok:
        FAILURES.append(label)


def finding(fid, cls="TRUE_UNCERTAIN", quote="q", repairable=True, why="w"):
    return {"id": fid, "classification": cls, "quote": quote,
            "repairable": repairable, "why": why}


def repair(edits=1, status=None):
    return {"status": status or CP.PASS,
            "edits": [{"finding_id": "F1"}] * edits, "model_calls": 1}


def grounding(blocking, status=None):
    return {"status": status or CP.GROUNDING_HOLD, "blocking": blocking}


# ── A. a residue after a successful repair is eligible ──────────────────────────────
def test_a_single_repairable_residue_is_eligible():
    ok, why, sel = CP.completion_eligible(grounding([finding("F1")]), repair())
    check("one repairable survivor after an accepted repair is eligible", ok, why)
    check("and it is the finding selected", [f["id"] for f in sel] == ["F1"], sel)
    ok2, _w, sel2 = CP.completion_eligible(
        grounding([finding("F1"), finding("F2", "TRUE_UNSUPPORTED")]), repair())
    check("two are still eligible (the limit is 2)", ok2 and len(sel2) == 2, sel2)


# ── D/E/F. every reason NOT to run it ───────────────────────────────────────────────
def test_more_than_two_survivors_does_not_complete():
    ok, why, _ = CP.completion_eligible(
        grounding([finding("F%d" % i) for i in range(1, 4)]), repair())
    check("three survivors do NOT trigger completion", not ok, why)
    check("...and the reason says why", "over the completion limit" in why, why)
    check("the limit constant is 2", CP.COMPLETION_MAX_FINDINGS == 2)


def test_a_nonrepairable_survivor_does_not_complete():
    ok, why, _ = CP.completion_eligible(
        grounding([finding("F1", repairable=False)]), repair())
    check("a finding the grounder did not mark repairable blocks completion", not ok, why)
    check("...named as not repairable by subtraction",
          "not repairable by subtraction" in why, why)
    # A classification subtraction cannot answer is equally excluded.
    ok2, why2, _ = CP.completion_eligible(
        grounding([finding("F1", cls="LEGITIMATE_INTERPRETATION")]), repair())
    check("a LEGITIMATE_INTERPRETATION survivor does not complete either", not ok2, why2)


def test_no_first_repair_edits_does_not_complete():
    ok, why, _ = CP.completion_eligible(grounding([finding("F1")]), repair(edits=0))
    check("a first repair that applied no edit blocks completion", not ok, why)
    check("...named", "applied no edit" in why, why)


def test_a_failed_or_absent_first_repair_does_not_complete():
    for rep, label in ((None, "no repair at all"),
                       ({"status": "SKIPPED", "edits": []}, "a skipped repair"),
                       ({"status": CP.GROUNDING_HOLD, "edits": [{}]}, "a held repair")):
        ok, why, _ = CP.completion_eligible(grounding([finding("F1")]), rep)
        check("%s blocks completion" % label, not ok, why)


def test_a_passing_recheck_does_not_complete():
    ok, why, _ = CP.completion_eligible(
        {"status": CP.PASS, "blocking": []}, repair())
    check("a recheck that passed does not trigger completion", not ok, why)


# ── B/C. the real Daily Nous residue, through the REAL validator ────────────────────
SURVIVOR = ("The dial the veto is mapped onto measures the arrangement: it records that "
            "redistributive authority can now be overridden, and the competence of "
            "whoever does the overriding has already been conceded.")
KEEP = ("The council becomes a setting of their imperfect-democracy parameter.")
ARTICLE = KEEP + " " + SURVIVOR + "\n"
LEDGER = {
    "F10": {"fact_id": "F10", "proposition": "The appendix maps the veto to Acemoglu and "
            "Robinson's imperfect-democracy parameter.",
            "support_span": "maps the veto to Acemoglu and Robinson's "
                            "imperfect-democracy parameter"},
}
PACKET = {"article_type": "field_note", "story_spine": "a veto", "opening": "a veto",
          "reader_initial_state": "", "beats": [], "turn": "", "crip_turn": "",
          "lens": "", "ending_move": "", "facts": [], "quotes": [],
          "definitions": {}, "prohibitions": []}
FINDINGS = [finding("F1", quote=SURVIVOR,
                    why="the source establishes only that the appendix maps the veto to "
                        "the parameter, never what the dial substantively records")]


def test_a_completion_edit_removing_the_daily_nous_survivor_passes_the_validator():
    text, prov, errs = CP.apply_grounding_repair(
        ARTICLE,
        [{"finding_id": "F1", "operation": "DELETE", "original": SURVIVOR,
          "repaired": "", "fact_ids": [], "what_was_removed": "the whole claim"}],
        FINDINGS, LEDGER, PACKET)
    check("deleting the surviving claim is accepted", not errs, errs)
    check("the claim is gone", "measures the arrangement" not in text, text)
    check("the supported sentence is untouched", KEEP in text, text)
    check("the edit is recorded", len(prov) == 1, prov)

    # Narrowing is equally allowed.
    text2, _p, errs2 = CP.apply_grounding_repair(
        ARTICLE,
        [{"finding_id": "F1", "operation": "NARROW", "original": SURVIVOR,
          "repaired": "The veto is mapped onto the dial.",
          "fact_ids": ["F10"], "what_was_removed": "what the dial records"}],
        FINDINGS, LEDGER, PACKET)
    check("narrowing it to the mapping alone is accepted", not errs2, errs2)
    check("and the substantive claim is gone",
          "records that redistributive authority" not in text2, text2)


def test_a_completion_edit_that_adds_is_still_refused():
    for repaired, relation in (
            ("Every such dial records the same thing.", "GENERALIZATION"),
            ("The dial amounts to the same as the veto itself.", "EQUIVALENCE")):
        _t, _p, errs = CP.apply_grounding_repair(
            ARTICLE,
            [{"finding_id": "F1", "operation": "NARROW", "original": SURVIVOR,
              "repaired": repaired, "fact_ids": ["F10"], "what_was_removed": "x"}],
            FINDINGS, LEDGER, PACKET)
        check("a completion edit adding %s is refused" % relation, bool(errs), errs)
        check("...by the same ADDS-rather-than-subtracts check",
              any("ADDS rather than subtracts" in e and relation in e for e in errs), errs)


def test_completion_uses_the_same_validator_not_a_copy():
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "grounding_completion")
    calls = {getattr(n.func, "id", "") for n in ast.walk(fn) if isinstance(n, ast.Call)}
    check("grounding_completion calls apply_grounding_repair",
          "apply_grounding_repair" in calls, sorted(calls))
    check("and defines no validator of its own",
          not any(k in src.split("def grounding_completion")[1].split("\ndef ")[0]
                  for k in ("validate_turn_support", "_numbers_of(", "def ")),
          "a private check inside completion would be a weaker second validator")


# ── the Lubetkin residue, same shape ────────────────────────────────────────────────
LUB_KEEP = ("On the National Heritage List for England it is listed at Grade I, list "
            "entry number 1297993.")
LUB_SURVIVOR = ("The Grade I listing marks the building as of exceptional interest, and "
                "the condition record describes the same building.")


def test_the_lubetkin_residue_completes():
    art = LUB_KEEP + " " + LUB_SURVIVOR + "\n"
    f = [finding("F1", cls="TRUE_UNSUPPORTED", quote=LUB_SURVIVOR,
                 why="the listing does not carry the exceptional-interest gloss")]
    ok, why, sel = CP.completion_eligible(grounding(f), repair())
    check("the Lubetkin survivor is eligible for completion", ok, why)
    text, _p, errs = CP.apply_grounding_repair(
        art, [{"finding_id": "F1", "operation": "NARROW", "original": LUB_SURVIVOR,
               "repaired": "The condition record describes the same building.",
               "fact_ids": [], "what_was_removed": "the exceptional-interest gloss"}],
        sel, {}, PACKET)
    check("the completion edit is accepted", not errs, errs)
    check("the duplicate claim is gone", "exceptional interest" not in text, text)
    check("the listing sentence the first repair produced is untouched",
          LUB_KEEP in text, text)


# ── G/H. once only, and a survivor still holds ──────────────────────────────────────
def test_completion_can_happen_at_most_once():
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    tree = ast.parse(src)
    sites = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and getattr(n.func, "id", "") == "grounding_completion"]
    check("there is exactly one call site in the whole module", len(sites) == 1,
          "%d found" % len(sites))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "grounding_completion")
    check("grounding_completion itself makes one provider call and no loop",
          len([n for n in ast.walk(fn) if isinstance(n, ast.Call)
               and getattr(n.func, "id", "") == "_ask"]) == 1
          and not any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(fn)))
    # And the runner cannot reach it twice: the call sits under `attempt = 2`, and the
    # only grounding call after it sets attempt = 3, after which nothing loops back.
    body = src.split("def _run_story_architecture")[-1] if "_run_story_architecture" in src else src
    check("no grounding attempt beyond 3 exists anywhere",
          '"attempt"] = 4' not in src and "attempt = 4" not in src)
    check("completion is reached only after a passing first repair",
          "if rep[\"status\"] == PASS:" in src
          and src.index("if rep[\"status\"] == PASS:")
              < src.index("_ok, _why, _comp_findings = completion_eligible"))


def test_a_survivor_after_completion_still_holds():
    """Completion is not a licence to pass: what it fails to remove still blocks."""
    art = KEEP + " " + SURVIVOR + "\n"
    text, prov, errs = CP.apply_grounding_repair(
        art, [{"finding_id": "F1", "operation": "NARROW", "original": SURVIVOR,
               "repaired": SURVIVOR.replace("has already been conceded", "is conceded"),
               "fact_ids": ["F10"], "what_was_removed": "nothing of substance"}],
        FINDINGS, LEDGER, PACKET)
    check("a cosmetic completion edit is applied, not rejected", not errs and prov, errs)
    check("but the claim is still in the text for the final recheck to find",
          "measures the arrangement" in text, text)
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    check("and a third-attempt hold is reported as such",
          "AFTER one factual repair and one completion pass" in src)


# ── the model-call budget, structurally ─────────────────────────────────────────────
def test_the_model_call_budget():
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    seg = src.split("_ok, _why, _comp_findings = completion_eligible")[1].split(
        "pkg = pkg_ref[0]")[0]
    check("completion adds nothing when it is not eligible",
          "if _ok:" in seg and seg.index("if _ok:") < seg.index("grounding_completion("))
    check("the completion repair is one call", seg.count("grounding_completion(") == 1)
    check("the final recheck is one call", seg.count("ground_candidate(") == 1)
    check("the post-completion safety audit is deterministic, not a provider call",
          "audit(final, pkg, repair=comp)" in seg and "_ask(" not in seg)
    check("its model_calls are accounted to GROUNDING",
          'calls[GROUNDING] = calls.get(GROUNDING, 0) + comp.get("model_calls", 0)' in seg)


def main():
    for fn in (test_a_single_repairable_residue_is_eligible,
               test_more_than_two_survivors_does_not_complete,
               test_a_nonrepairable_survivor_does_not_complete,
               test_no_first_repair_edits_does_not_complete,
               test_a_failed_or_absent_first_repair_does_not_complete,
               test_a_passing_recheck_does_not_complete,
               test_a_completion_edit_removing_the_daily_nous_survivor_passes_the_validator,
               test_a_completion_edit_that_adds_is_still_refused,
               test_completion_uses_the_same_validator_not_a_copy,
               test_the_lubetkin_residue_completes,
               test_completion_can_happen_at_most_once,
               test_a_survivor_after_completion_still_holds,
               test_the_model_call_budget):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL GROUNDING COMPLETION TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
