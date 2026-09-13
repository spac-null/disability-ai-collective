#!/usr/bin/env python3
"""fast_lane_grounding_completion_test.py -- Fast Lane gets ONE grounding-completion pass.

THE DEFECT. The completion call was guarded `compose_mode != COMPOSE_FAST_LANE`, so in
Fast Lane any repairable Grounding finding was automatically terminal. Measured on
production-20260913T083824Z-f83f4b8a: three findings, all `repairable: true`, each
carrying the Grounder's own narrow attribution patch, and the run held anyway.

THE POLICY. Fast Lane may spend exactly one turn of the SAME transactional loop, and only
when EVERY blocking finding is repairable. Structural checks read the source, because the
behaviours that matter here are "which branch is guarded by what" and "what is bounded by
which constant" -- a mocked ladder would assert the mock.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP

SRC = (HERE / "new_engine_v1" / "composition.py").read_text()
FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        FAILURES.append(name)
        print("  FAIL %s  %s" % (name, detail))


def _f(cls, quote="a claim the article makes"):
    return {"classification": cls, "quote": quote}


# ── A ────────────────────────────────────────────────────────────────────────
def test_a_grounding_pass_is_untouched():
    print("\nA. Fast Lane Grounding PASS -> unchanged")
    body = SRC.split("_fast_lane = compose_mode == COMPOSE_FAST_LANE")[1][:600]
    check("completion is still gated on a non-PASS grounding status",
          'if g["status"] != PASS and' in body, body[:200])
    check("a PASS never reaches the eligibility predicate",
          CP.fast_lane_grounding_completion_eligible({"blocking": []}) is False)


# ── B ────────────────────────────────────────────────────────────────────────
def test_b_a_nonrepairable_blocker_is_terminal():
    print("\nB. Fast Lane HOLD with a non-repairable blocker -> terminal")
    mixed = {"blocking": [_f("TRUE_UNCERTAIN"), _f("TRUE_UNSUPPORTED"),
                          _f("LEGITIMATE_INTERPRETATION")]}
    check("one non-repairable finding makes the whole HOLD ineligible",
          CP.fast_lane_grounding_completion_eligible(mixed) is False)
    check("a finding with no quote is not repairable either",
          CP.fast_lane_grounding_completion_eligible(
              {"blocking": [_f("TRUE_UNCERTAIN"), {"classification": "TRUE_UNSUPPORTED",
                                                   "quote": "  "}]}) is False)
    check("this is stricter than the normal lane, which enters on ANY repairable finding",
          len(CP.repairable_findings(mixed["blocking"])) == 2
          and not CP.fast_lane_grounding_completion_eligible(mixed))


# ── C ────────────────────────────────────────────────────────────────────────
def test_c_three_repairable_attribution_findings_are_eligible():
    print("\nC. Fast Lane HOLD with 3 repairable attribution findings -> one pass")
    three = {"blocking": [_f("TRUE_UNCERTAIN", "The stated intent is to spread the work"),
                          _f("TRUE_UNCERTAIN", "the collection it says the work"),
                          _f("TRUE_UNCERTAIN", "the museum had just bought")]}
    check("all three are repairable", len(CP.repairable_findings(three["blocking"])) == 3)
    check("the HOLD is eligible for the one pass",
          CP.fast_lane_grounding_completion_eligible(three) is True)
    check("the loop is entered when Fast Lane is eligible",
          "if g[\"status\"] != PASS and (not _fast_lane or _fl_eligible):" in SRC)
    check("eligibility is computed from the grounding result, not the mode alone",
          "_fl_eligible = _fast_lane and fast_lane_grounding_completion_eligible(g)"
          in SRC)

    # ONE turn answers all three: both free origins are all-or-nothing over the whole
    # target list, so a single iteration is a single BATCHED proposal.
    doc = re.sub(r"\s+", " ", CP.suggested_patch_candidate.__doc__ or "")
    check("the suggested-patch candidate covers the WHOLE target list",
          "WHOLE target list" in doc and "EVERY finding" in doc, doc[:120])
    check("and costs no repair-model call", '"model_calls": 0' in
          SRC.split("def suggested_patch_candidate")[1][:1400])


# ── D / E / F ────────────────────────────────────────────────────────────────
def test_d_claim_mapper_reruns_on_repaired_bytes():
    print("\nD. Claim Mapper runs on the repaired final bytes")
    accepted = SRC.split('if gc["grounding_repairs_accepted"]:')[1][:2200]
    check("the repaired text becomes final", 'final = gc["article_text"]' in accepted)
    check("Fast Lane re-maps after the repair",
          "if _fast_lane:" in accepted and "claim_map_article(" in accepted)
    check("the claim map is re-bound to the NEW bytes",
          'wr["claim_map_article_sha256"] = C.sha256_text(final)' in accepted)
    check("a failed re-map holds the run rather than publishing a stale map",
          "did not validate" in accepted and "WRITER_HOLD" in accepted)
    check("the end-of-run binding assertion still exists",
          'wr.get("claim_map_article_sha256") != C.sha256_text(final)' in SRC)


def test_e_safety_reruns_on_repaired_bytes():
    print("\nE. Safety is evaluated on the repaired bytes")
    loop = SRC.split("def grounding_completion_loop")[1][:9000]
    check("every candidate is audited before it can be accepted",
          "candidate_safety = audit_fn(candidate_text, package, repair=prop)" in loop)
    check("a candidate that introduces a Safety blocker is rejected",
          'introduced a new Safety blocker' in loop)
    check("the accepted candidate's OWN audit is what gets recorded",
          'sa_gc = gc["final_safety"]' in SRC)
    check("and a failed post-repair Safety holds the run",
          "an accepted grounding repair did not survive the safety " in SRC)


def test_f_grounding_reruns_exactly_once():
    print("\nF. Grounding re-runs exactly once in Fast Lane")
    check("Fast Lane is bounded by its own constant",
          CP.FAST_LANE_GROUNDING_COMPLETION_MAX_ITERATIONS == 1,
          CP.FAST_LANE_GROUNDING_COMPLETION_MAX_ITERATIONS)
    check("the normal lane keeps its own larger budget",
          CP.GROUNDING_COMPLETION_MAX_ITERATIONS == 5,
          CP.GROUNDING_COMPLETION_MAX_ITERATIONS)
    check("the bound is passed at the call site",
          "max_iterations=(FAST_LANE_GROUNDING_COMPLETION_MAX_ITERATIONS" in SRC)
    loop = SRC.split("def grounding_completion_loop")[1][:9000]
    check("the loop recheck-grounds once per iteration",
          loop.count("candidate_grounding = ground_candidate(") == 1)
    check("and the loop is bounded by max_iterations",
          "while g[\"status\"] != PASS and iterations < max_iterations:" in loop)


# ── G ────────────────────────────────────────────────────────────────────────
def test_g_a_second_hold_is_terminal():
    print("\nG. A second Grounding HOLD is terminal -- no second repair")
    # The post-repackage loop-back is the only other route into completion, and it stays
    # Fast-Lane-disabled, so one pass cannot become two by another path.
    check("the post-repackage loop-back is still Fast-Lane-disabled",
          "if (compose_mode != COMPOSE_FAST_LANE and repackaged[0]" in SRC)
    after = SRC.split("_fl_eligible = _fast_lane")[1]
    check("a surviving HOLD returns through the terminal grounding exit",
          "return out(GROUNDING," in after)
    check("there is exactly one completion entry point for the pre-repackage phase",
          SRC.count("gc = grounding_completion_loop(") == 1,
          SRC.count("gc = grounding_completion_loop("))


# ── H ────────────────────────────────────────────────────────────────────────
def test_h_no_new_source_research_or_writer_call():
    print("\nH. No new source, research or Writer call")
    loop = SRC.split("def grounding_completion_loop")[1].split("\ndef ")[0]
    for banned in ("search_urls", "requests.", "urlopen", "fetch(", "research(",
                   "write(", "WRITER_SYSTEM"):
        check("the completion loop never calls %r" % banned, banned not in loop)
    check("repairs are claim-local and subtractive",
          "apply_local_grounding_repair" in loop)
    doc = CP.apply_local_grounding_repair.__doc__ or ""
    check("the local repair cites no new facts", "claim-local" in doc.lower())
    accepted = SRC.split('if gc["grounding_repairs_accepted"]:')[1][:2200]
    check("the Fast Lane re-map calls the Claim Mapper, never the Writer",
          "claim_map_article(" in accepted and "S.write(" not in accepted)
    cm = re.sub(r"\s+", " ", (CP.claim_map_article.__doc__ or "").lower())
    check("and the Claim Mapper never touches the article",
          "never touches the article" in cm and "never calls the writer" in cm,
          cm[-120:])


# ── I ────────────────────────────────────────────────────────────────────────
def test_i_normal_lane_behaviour_is_unchanged():
    print("\nI. Non-Fast-Lane grounding repair behaviour is unchanged")
    check("the normal lane still enters completion on any non-PASS grounding",
          "if g[\"status\"] != PASS and (not _fast_lane or _fl_eligible):" in SRC)
    check("a non-Fast-Lane run is never gated by the Fast Lane predicate",
          "_fl_eligible = _fast_lane and " in SRC)
    check("the normal lane still gets GROUNDING_COMPLETION_MAX_ITERATIONS",
          "else GROUNDING_COMPLETION_MAX_ITERATIONS)" in SRC)
    check("the loop's default budget is still the normal one",
          "max_iterations: int = GROUNDING_COMPLETION_MAX_ITERATIONS" in SRC)


# ── audit identity ───────────────────────────────────────────────────────────
def test_the_original_hold_is_preserved_not_rewritten():
    print("\nAudit: the original HOLD survives the repair")
    check("the raw verdict is captured before the loop runs",
          SRC.index('st["GROUNDING_RAW"]') < SRC.index("gc = grounding_completion_loop("))
    for field in ("blocking", "blocking_count", "repairable_count", "article_sha256",
                  "compose_mode", "grounding_status"):
        check("  it records %s" % field,
              '"%s"' % field in SRC.split('st["GROUNDING_RAW"] = {')[1][:700])
    check("it reaches disk", 'dump("GROUNDING_RAW.json"' in SRC)
    check("and the post-repair read is recorded separately",
          'g = record(GROUNDING, gc)' in SRC)
    check("the completion's own audit still reaches disk",
          'dump("FACTUAL_COMPLETION.json"' in SRC)
    # The module must still parse and the touched functions must still be functions.
    tree = ast.parse(SRC)
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    for fn in ("grounding_completion_loop", "fast_lane_grounding_completion_eligible",
               "repairable_findings", "suggested_patch_candidate", "claim_map_article"):
        check("  %s is defined" % fn, fn in names)


def main():
    for t in (test_a_grounding_pass_is_untouched,
              test_b_a_nonrepairable_blocker_is_terminal,
              test_c_three_repairable_attribution_findings_are_eligible,
              test_d_claim_mapper_reruns_on_repaired_bytes,
              test_e_safety_reruns_on_repaired_bytes,
              test_f_grounding_reruns_exactly_once,
              test_g_a_second_hold_is_terminal,
              test_h_no_new_source_research_or_writer_call,
              test_i_normal_lane_behaviour_is_unchanged,
              test_the_original_hold_is_preserved_not_rewritten):
        t()
    print()
    if FAILURES:
        print("%d failure(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("All Fast Lane grounding-completion tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
