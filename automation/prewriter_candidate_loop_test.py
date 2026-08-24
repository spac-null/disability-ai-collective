#!/usr/bin/env python3
"""
prewriter_candidate_loop_test.py -- PREWRITER_CANDIDATE_LOOP_V1, deterministic tests.

THE PROBLEM THIS CLOSES
A single candidate failing the commission gate used to end the entire scheduled
daily generation attempt. `commission_mechanism_not_tied_to_anchor` did exactly
that on 2026-08-21 (canary), 2026-08-22 (natural) and 2026-08-24 (acceptance),
while 100+ unused stories sat in the pool. The gate is correct and is NOT
touched here -- it simply must not consume the day.

THE HARD BOUNDARY
Pre-writer, a finite number of candidates may be considered. Post-writer, none.
Once the writer begins for a candidate, that candidate owns the run through
writer, transformations, review, final output and disposition; a draft blocked
downstream ends the run. There is no outcome-fishing.

Covers brief cases A-H. No network, no model calls, no production DB.

Run (from repo root):
  python3 automation/prewriter_candidate_loop_test.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from snapshot_test import _import_orchestrator, _isolate_paths  # noqa: E402
from orchestrator.generate import MAX_PREWRITER_CANDIDATES  # noqa: E402
from orchestrator.discovery import MAX_SOURCE_ACQUISITION_ATTEMPTS  # noqa: E402
import shadow_capture as SC  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


def _orch():
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    _isolate_paths(orch, tempfile.mkdtemp())
    for d in (orch.posts_dir, orch.drafts_dir, orch.assets_dir):
        d.mkdir(parents=True, exist_ok=True)
    return orch


def _script(orch, results):
    """Replace the single-candidate attempt with a scripted sequence.

    Records the exclusion list handed to each attempt, which is how we prove the
    loop never re-offers a candidate it has already commissioned-and-deferred.
    """
    calls = []

    def fake(exclude_seed_ids=None):
        calls.append(list(exclude_seed_ids or []))
        if len(calls) > len(results):
            raise AssertionError("loop ran attempt %d with only %d scripted results "
                                 "-- budget overrun" % (len(calls), len(results)))
        return results[len(calls) - 1]

    orch._run_single_candidate_attempt = fake
    return calls


def _defer(seed_id, code="commission_mechanism_not_tied_to_anchor"):
    return {"status": "defer", "source_decision": "defer", "defer_reason_code": code,
            "news_seed_id": seed_id, "declined": False, "commit_success": False}


def _decline(seed_id):
    return {"status": "declined", "source_decision": "decline", "verdict": "declined",
            "news_seed_id": seed_id, "commit_success": False}


def _article(seed_id, blocked=False):
    return {"status": "success", "news_seed_id": seed_id, "commit_success": True,
            "disposition": "draft_blocked" if blocked else "draft",
            "should_block": blocked}


# --------------------------------------------------------------------------- #
def test_A_acquisition_fail_then_defer_then_pass():
    """TEST A -- c1 acquisition-failed (handled inside attempt 1, which then
    commissions c2 and defers), c3 passes on attempt 2. Writer starts once."""
    o = _orch()
    calls = _script(o, [_defer("c2"), _article("c3")])
    res = o._run_production_automation_locked()
    check("loop made exactly 2 attempts", len(calls) == 2, calls)
    check("attempt 1 started with no exclusions", calls[0] == [], calls[0])
    check("attempt 2 excluded the deferred candidate", calls[1] == ["c2"], calls[1])
    check("the article-producing candidate is c3", res.get("news_seed_id") == "c3", res)
    check("run ends on the article candidate -- writer entered once",
          res.get("status") == "success")
    check("candidate lineage is recorded", res.get("candidate_count") == 2,
          res.get("prewriter_candidates"))
    check("lineage names both candidates in order",
          [a["seed_id"] for a in res["prewriter_candidates"]] == ["c2", "c3"],
          res["prewriter_candidates"])


def test_B_defer_then_pass():
    """TEST B -- c1 defers, c2 reaches writer."""
    o = _orch()
    calls = _script(o, [_defer("c1"), _article("c2")])
    res = o._run_production_automation_locked()
    check("2 attempts", len(calls) == 2, calls)
    check("c1 excluded on attempt 2", calls[1] == ["c1"], calls[1])
    check("c2 produced the article", res.get("news_seed_id") == "c2")


def test_C_decline_then_pass():
    """TEST C -- c1 declines (persistence preserved), c2 reaches writer."""
    o = _orch()
    declined = []
    o.mark_news_seed_declined = lambda seed_id, rec: declined.append(seed_id)
    calls = _script(o, [_decline("c1"), _article("c2")])
    res = o._run_production_automation_locked()
    check("2 attempts", len(calls) == 2, calls)
    check("declined candidate excluded for the rest of the run", calls[1] == ["c1"])
    check("c2 produced the article", res.get("news_seed_id") == "c2")
    check("the loop does not un-decline or re-decline anything itself",
          declined == [], declined)


def test_D_five_prewriter_outcomes_exhaust():
    """TEST D -- five usable candidates all defer/decline. No sixth."""
    o = _orch()
    seq = [_defer("c1"), _decline("c2"), _defer("c3"), _defer("c4"), _decline("c5")]
    calls = _script(o, seq)
    res = o._run_production_automation_locked()
    check("exactly MAX_PREWRITER_CANDIDATES attempts", len(calls) == MAX_PREWRITER_CANDIDATES == 5,
          len(calls))
    check("no sixth candidate", len(calls) == 5)
    check("explicit exhaustion status",
          res.get("status") == "no_article_prewriter_candidates_exhausted", res.get("status"))
    check("all five candidates recorded", res.get("candidate_count") == 5)
    check("exclusions accumulated across every attempt",
          calls[-1] == ["c1", "c2", "c3", "c4"], calls[-1])
    check("no article committed", res.get("commit_success") is False)


def test_E_post_writer_block_does_not_rotate():
    """TEST E -- ESSENTIAL. c1 defers, c2 reaches writer but the draft is BLOCKED
    downstream. No candidate 3 may be tried."""
    o = _orch()
    calls = _script(o, [_defer("c1"), _article("c2", blocked=True)])
    res = o._run_production_automation_locked()
    check("exactly 2 attempts -- no candidate 3 after a blocked draft", len(calls) == 2, calls)
    check("the blocked draft's own outcome is returned unchanged",
          res.get("disposition") == "draft_blocked" and res.get("should_block") is True, res)
    check("a blocked draft is NOT treated as a pre-writer outcome",
          res.get("status") == "success")


def test_E2_no_rotation_on_other_terminal_outcomes():
    """Only defer/decline rotate. Everything else ends the run immediately."""
    for status, payload in (
            ("skipped", {"status": "skipped", "message": "article exists"}),
            ("no_article_source_acquisition_exhausted",
             {"status": "no_article_source_acquisition_exhausted", "attempt_count": 3}),
            ("aborted", {"status": "aborted", "reason": "template_collision"}),
            ("no_execution", {"status": "no_execution", "source_decision": "commission"}),
            ("partial", {"status": "partial", "news_seed_id": "c1"})):
        o = _orch()
        calls = _script(o, [payload, _article("never")])
        res = o._run_production_automation_locked()
        check("%s terminates the loop immediately" % status, len(calls) == 1, calls)
        check("...and its result is returned unchanged", res.get("status") == status)


def test_F_no_state_leaks_between_candidates():
    """TEST F -- each attempt starts clean.

    Two guarantees: the loop hands a fresh attempt call (own locals, own capture
    run id, own evidence packet -- that is what restarting at the attempt
    boundary buys), and the one piece of ACCUMULATING instance state,
    _degraded_stages, is reset by the attempt itself.
    """
    o = _orch()
    calls = _script(o, [_defer("c1"), _defer("c2"), _article("c3")])
    res = o._run_production_automation_locked()
    check("every attempt received its own exclusion list, growing monotonically",
          calls == [[], ["c1"], ["c1", "c2"]], calls)
    check("no candidate is ever offered twice in one run",
          len(set(a["seed_id"] for a in res["prewriter_candidates"])) == 3)

    # the real attempt resets _degraded_stages before doing anything else
    o2 = _orch()
    o2._degraded_stages = ["stale_from_previous_candidate"]
    o2.check_for_existing_article_today = lambda: "2026-08-24-already-there.md"
    out = o2._run_single_candidate_attempt(exclude_seed_ids=["x"])
    check("attempt resets _degraded_stages before anything else",
          o2._degraded_stages == [], o2._degraded_stages)
    check("...and the early-exit path still works", out.get("status") == "skipped")

    # structural: the loop restarts at the attempt boundary, not by resetting vars
    src = (Path(__file__).parent / "orchestrator" / "generate.py").read_text()
    check("the loop calls the single-candidate attempt, not an inlined re-run",
          src.count("self._run_single_candidate_attempt(") == 1, )
    check("evidence capture lives inside the per-candidate attempt",
          src.index("def _run_single_candidate_attempt") < src.index('"evidence", _capture_run_id'))


def test_G_source_acquisition_retry_unchanged():
    """TEST G -- SOURCE_ACQUISITION_RETRY_V1 is untouched."""
    check("acquisition budget still 3", MAX_SOURCE_ACQUISITION_ATTEMPTS == 3,
          MAX_SOURCE_ACQUISITION_ATTEMPTS)
    check("pre-writer budget is a separate constant", MAX_PREWRITER_CANDIDATES == 5)
    o = _orch()
    # acquisition exhaustion is terminal and does NOT consume pre-writer rotation
    calls = _script(o, [{"status": "no_article_source_acquisition_exhausted",
                         "attempt_count": 3}, _article("never")])
    res = o._run_production_automation_locked()
    check("acquisition exhaustion ends the run without rotating candidates",
          len(calls) == 1 and res["status"] == "no_article_source_acquisition_exhausted", calls)
    src = (Path(__file__).parent / "orchestrator" / "discovery.py").read_text()
    check("acquisition classifier untouched by this change",
          "classify_source_acquisition" in src and "_SOURCE_MIN_USABLE_PARAGRAPHS" in src)


def test_H_capture_contract_unchanged():
    """TEST H -- phase2-capture-v0.1 REQUIRED_EVENTS unchanged, default OFF."""
    check("REQUIRED_EVENTS unchanged",
          SC.REQUIRED_EVENTS == ("evidence", "commission", "writer",
                                 "final_output", "disposition"), SC.REQUIRED_EVENTS)
    check("contract version unchanged", SC.CAPTURE_CONTRACT == "phase2-capture-v0.1")
    import os
    os.environ.pop(SC.ENV_FLAG, None)
    check("capture still OFF by default", SC.enabled() is False)


def main():
    for fn in [test_A_acquisition_fail_then_defer_then_pass,
               test_B_defer_then_pass,
               test_C_decline_then_pass,
               test_D_five_prewriter_outcomes_exhaust,
               test_E_post_writer_block_does_not_rotate,
               test_E2_no_rotation_on_other_terminal_outcomes,
               test_F_no_state_leaks_between_candidates,
               test_G_source_acquisition_retry_unchanged,
               test_H_capture_contract_unchanged]:
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL PRE-WRITER CANDIDATE LOOP TESTS PASSED")


if __name__ == "__main__":
    main()
