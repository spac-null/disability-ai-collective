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
    """STAGE 8c's fixed one-completion-pass budget (and Stage 8b's fixed one-repair
    budget alongside it) is SUPERSEDED, for Grounding, by grounding_completion_loop's
    progress-bounded loop (owner-directed, 2026-09-09). completion_eligible() and
    grounding_completion() above are still exercised directly, by the tests above them
    in this file -- their eligibility/validator-reuse guarantees are unchanged, in case
    anything else ever calls them again -- but neither function, nor grounding_repair()
    (Stage 8b), is wired into the main orchestration any more: grounding_completion_loop
    replaces all three call sites at once, and it is ITS OWN iteration ceiling that now
    bounds Grounding repair, not a fixed call count."""
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    tree = ast.parse(src)
    old_sites = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and getattr(n.func, "id", "") in ("grounding_completion", "grounding_repair")]
    check("the old fixed-budget functions have no call site left in the module "
          "(superseded by grounding_completion_loop)",
          len(old_sites) == 0, "%d found" % len(old_sites))
    loop_fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef)
                  and n.name == "grounding_completion_loop")
    check("the replacement is bounded by a WHILE with the max-iterations fuse, not an "
          "unbounded loop",
          any(isinstance(n, ast.While) for n in ast.walk(loop_fn)))
    check("the fuse constant is what the loop signature defaults to",
          "max_iterations: int = GROUNDING_COMPLETION_MAX_ITERATIONS" in src)
    orch = src.split("def run_story_architecture_composition")[-1]
    check("the orchestration calls the loop, not either old fixed-budget function",
          "grounding_completion_loop(" in orch
          and "completion_eligible(" not in orch
          and " grounding_completion(" not in orch)


def test_a_survivor_after_completion_still_holds():
    """A repair that leaves a claim standing is not a licence to pass: what it fails to
    remove still blocks. What runs the recheck that catches it is now
    grounding_completion_loop's own per-iteration Grounding call (see
    test_completion_can_happen_at_most_once for the replacement), not a fixed
    second/third attempt -- the survivor property itself is unchanged."""
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
    check("and a HOLD after some number of repair attempts is reported as such",
          "repair attempt(s) over" in src, src.count("repair attempt(s) over"))


# ── the model-call budget, structurally ─────────────────────────────────────────────
def test_the_model_call_budget():
    """grounding_completion_loop's own per-iteration budget: at most one repair-proposal
    call and one Grounding recheck call each pass through the loop body (Safety is
    deterministic -- the caller's own audit_fn, never a new _ask call), every call's
    model_calls actually accumulated rather than assumed, and the loop bounded by the
    max-iterations fuse rather than `while True`."""
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "grounding_completion_loop")
    calls_in_loop = [getattr(n.func, "id", "") for n in ast.walk(fn)
                     if isinstance(n, ast.Call)]
    check("exactly one repair-proposal call site in the loop body",
          calls_in_loop.count("grounding_repair_proposal") == 1, calls_in_loop)
    check("exactly one Grounding recheck call site in the loop body",
          calls_in_loop.count("ground_candidate") == 1, calls_in_loop)
    check("Safety is checked via the caller's own audit_fn, never a new _ask call",
          "_ask" not in calls_in_loop)
    check("the loop is bounded by the max-iterations fuse, not `while True`",
          any(isinstance(n, ast.While)
              and not (isinstance(n.test, ast.Constant) and n.test.value is True)
              for n in ast.walk(fn)))
    check("model_calls accumulates from every source actually spent",
          'model_calls += prop.get("model_calls", 0)' in src
          and 'model_calls += candidate_safety.get("model_calls", 0)' in src
          and 'model_calls += candidate_grounding.get("model_calls", 0)' in src)


# ══════════════════════════════════════════════════════════════════════════════
# grounding_completion_loop -- PROGRESS-BOUNDED COMPLETION, direct (owner-directed,
# 2026-09-09)
# ══════════════════════════════════════════════════════════════════════════════
# Direct tests of the loop itself: a scripted provider answers repair-proposal calls, a
# stubbed new_engine_v1.stages.ground (the same substitution every Grounding test in
# this repo uses) answers Grounding rechecks, and a hand-written audit_fn stands in for
# the real safety_audit() -- the loop takes audit_fn as an injected callable
# specifically so its OWN transactional logic (accept/reject, progress, repeats, the
# ceiling) can be tested without a full Writer packet/architecture/cut-report/negative-
# lineage rig. safety_audit()'s own correctness is proven elsewhere; these tests are
# about what the loop does with whatever audit_fn tells it.
import json as _json                                                  # noqa: E402
import new_engine_v1.stages as _stages                                # noqa: E402


class _Reply:
    def __init__(self, text):
        self.text = text

    def identity(self):
        return {"provider": "test", "requested_model": "test", "actual_model": "test",
               "fallback_used": False}


class _LoopProvider:
    """Answers repair-proposal calls in order. Nothing else inside
    grounding_completion_loop calls provider.complete() -- Safety is audit_fn, Grounding
    is the stubbed new_engine_v1.stages.ground."""
    model = "test"
    url = "http://127.0.0.1:0/v1"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0
        self.prompts: list = []

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                deadline=None):
        self.calls += 1
        self.prompts.append(user)
        if not self.replies:
            raise AssertionError("grounding_completion_loop made more repair-proposal "
                                 "calls than the test scripted")
        r = self.replies.pop(0)
        return _Reply(r if isinstance(r, str) else _json.dumps(r))


def _ground_seq(replies):
    """Install a scripted new_engine_v1.stages.ground -- `replies` are
    {"status": "settled", "findings": [...]} dicts, the shape S.ground itself returns
    (ground_candidate(), the REAL function, does the unsupported/blocking derivation).
    Returns (restore, calls) -- callers MUST call restore() in a finally block."""
    real = _stages.ground
    seq = list(replies)
    calls = {"n": 0}

    def fake(*a, **k):
        calls["n"] += 1
        return dict(seq.pop(0) if seq else {"status": "settled", "findings": []})

    _stages.ground = fake

    def restore():
        _stages.ground = real
    return restore, calls


def _ground_reply(findings):
    return {"status": "settled", "findings": list(findings)}


def _initial(findings):
    """A ground_candidate()-shaped result to hand the loop as its already-computed
    `initial` -- only `status` and `blocking` are read internally; `grounding_status` is
    carried for parity with the real function's own output shape."""
    return {"status": CP.PASS if not findings else CP.GROUNDING_HOLD,
           "blocking": list(findings),
           "grounding_status": "settled" if not findings else "held"}


def _finding(fid, quote, cls="TRUE_UNSUPPORTED"):
    return {"id": fid, "classification": cls, "quote": quote, "repairable": True,
           "why": "the sources do not carry this"}


def _pass_audit(text, package, **kw):
    return {"status": CP.PASS, "blocking": [], "model_calls": 0}


def _edit(fid, original, repaired):
    return {"edits": [{"finding_id": fid, "operation": "DELETE", "original": original,
                       "repaired": repaired, "fact_ids": []}]}


LOOP_ARTICLE = ("The room was painted in 1990. The chair was carved in 1991. The table "
                "was built in 1992.")
# Licenses every WORD in LOOP_ARTICLE's three sentences (room/painted/chair/carved/
# table/built) but not the years -- the deterministic subtractive path can never touch a
# bare number (its word regex does not match digits), so these tests' fictional "the
# grounder is unhappy about the year" findings stay squarely on the MODEL proposal path,
# unaffected by DELETE_UNSUPPORTED_SURFACE (that path has its own dedicated tests below).
LOOP_LEDGER: dict = {
    "L1": {"proposition": "The room was painted.", "support_span": "The room was painted"},
    "L2": {"proposition": "The chair was carved.", "support_span": "The chair was carved"},
    "L3": {"proposition": "The table was built.", "support_span": "The table was built"},
}
LOOP_PACKET: dict = {}
LOOP_ARCH = None
LOOP_PACK = {"subject": "test", "sources": []}

F1 = _finding("F1", "The room was painted in 1990.")
F2 = _finding("F2", "The chair was carved in 1991.")
F3 = _finding("F3", "The table was built in 1992.")
EDIT1 = _edit("F1", "The room was painted in 1990.", "The room was painted.")
EDIT2 = _edit("F2", "The chair was carved in 1991.", "The chair was carved.")
EDIT3 = _edit("F3", "The table was built in 1992.", "The table was built.")


def _run_loop(provider, initial, audit_fn=_pass_audit, max_iterations=None,
             article=None, ledger=None, packet=None):
    kw = {}
    if max_iterations is not None:
        kw["max_iterations"] = max_iterations
    return CP.grounding_completion_loop(
        provider, article if article is not None else LOOP_ARTICLE, None, initial,
        ledger if ledger is not None else LOOP_LEDGER,
        packet if packet is not None else LOOP_PACKET, LOOP_ARCH, LOOP_PACK,
        "source text", "sha", audit_fn, **kw)


def test_three_independent_blockers_all_repair_and_pass():
    """3 independent local Grounding blockers can all be repaired and PASS -- the
    article must NOT HOLD merely because there were more than the old
    COMPLETION_MAX_FINDINGS=2 ceiling. Each proposal answers ONE finding; the recheck
    after each shows the blocking set strictly shrinking, 3 -> 2 -> 1 -> 0."""
    restore, gcalls = _ground_seq([
        _ground_reply([F2, F3]), _ground_reply([F3]), _ground_reply([])])
    try:
        result = _run_loop(_LoopProvider([EDIT1, EDIT2, EDIT3]), _initial([F1, F2, F3]))
    finally:
        restore()
    check("the run reaches PASS", result["status"] == CP.PASS, result.get("blocking"))
    check("all three years are gone",
          "1990" not in result["article_text"] and "1991" not in result["article_text"]
          and "1992" not in result["article_text"], result["article_text"])
    check("three iterations, three proposals, three acceptances",
          result["grounding_completion_iterations"] == 3
          and result["grounding_repair_proposals"] == 3
          and result["grounding_repairs_accepted"] == 3, result)
    check("zero rejections -- every proposal made progress",
          result["grounding_repairs_rejected"] == 0, result)
    check("initial/final blocker counts are exact",
          result["initial_blocker_count"] == 3 and result["final_blocker_count"] == 0,
          result)
    check("all three edits are individually auditable",
          {e["finding_id"] for e in result["accepted_edits"]} == {"F1", "F2", "F3"},
          result["accepted_edits"])
    check("the grounder ran exactly three times, once per accepted repair",
          gcalls["n"] == 3, gcalls)


def test_accepted_repair_strictly_reduces_blocker_set():
    restore, _ = _ground_seq([_ground_reply([F2])])
    try:
        result = _run_loop(_LoopProvider([EDIT1]), _initial([F1, F2]), max_iterations=1)
    finally:
        restore()
    check("the accepted candidate's blocking set is strictly smaller",
          result["final_blocker_count"] < result["initial_blocker_count"], result)
    check("one accepted repair", result["grounding_repairs_accepted"] == 1, result)


def test_a_repair_that_replaces_one_blocker_with_another_is_rejected():
    """1 blocker -> 1 DIFFERENT blocker is not progress: the count did not shrink."""
    different = _finding("F9", "A completely different unsupported claim.")
    restore, gcalls = _ground_seq([_ground_reply([different])])
    try:
        result = _run_loop(_LoopProvider([EDIT1]), _initial([F1]), max_iterations=1)
    finally:
        restore()
    check("the proposal is rejected, not accepted",
          result["grounding_repairs_accepted"] == 0, result)
    check("the accepted text is unchanged from the input",
          result["article_text"] == LOOP_ARTICLE, result["article_text"])
    check("the ORIGINAL blocker is what the final state still shows -- a rejected "
          "candidate's blocking set is never adopted",
          result["blocking"] == [F1], result["blocking"])


def test_a_repair_introducing_a_new_safety_blocker_is_rejected_and_never_mutates_the_article():
    calls = {"n": 0}

    def audit_fn(text, package, **kw):
        calls["n"] += 1
        return {"status": CP.HOLD,
               "blocking": [{"classification": "NEW_UNSUPPORTED_FACTS", "quote": "x"}],
               "model_calls": 0}

    restore, gcalls = _ground_seq([])  # never reached -- Safety rejects first
    try:
        result = _run_loop(_LoopProvider([EDIT1]), _initial([F1]), audit_fn=audit_fn,
                           max_iterations=1)
    finally:
        restore()
    check("no repair was accepted", result["grounding_repairs_accepted"] == 0, result)
    check("the accepted article is byte-for-byte the input",
          result["article_text"] == LOOP_ARTICLE, result["article_text"])
    check("Safety was checked and Grounding was never reached",
          calls["n"] == 1 and gcalls["n"] == 0, (calls, gcalls))


def test_a_rejected_repair_can_be_followed_by_a_different_successful_proposal():
    """First proposal fixes F1, but the recheck reports F3 newly flagged alongside the
    still-unfixed F2 -- the same count (2), so no progress and the proposal is rejected,
    accepted_text unchanged. The second proposal, told why, answers F2 instead and the
    set genuinely shrinks (2 -> 1); the third resolves F3 (still present, since the
    rejected first attempt never touched the article) and reaches PASS."""
    restore, gcalls = _ground_seq([
        _ground_reply([F3, F2]),   # after 1st proposal: 2 -> 2, no shrink -- rejected
        _ground_reply([F3]),       # after 2nd proposal: 2 -> 1, shrinks -- accepted
        _ground_reply([])])        # after 3rd proposal: 1 -> 0, PASS
    try:
        result = _run_loop(_LoopProvider([EDIT1, EDIT2, EDIT3]), _initial([F1, F2]),
                           max_iterations=5)
    finally:
        restore()
    check("the run reaches PASS", result["status"] == CP.PASS, result)
    check("two repairs are eventually accepted",
          result["grounding_repairs_accepted"] == 2, result)
    check("one was rejected first", result["grounding_repairs_rejected"] == 1, result)
    check("three iterations were spent", result["grounding_completion_iterations"] == 3,
          result)
    check("the accepted edits are the SECOND and THIRD proposals', not the rejected "
          "first", [e["finding_id"] for e in result["accepted_edits"]] == ["F2", "F3"],
          result)


def test_repeating_the_same_ineffective_proposal_terminates_hold():
    restore, gcalls = _ground_seq([_ground_reply([F1])])  # same blocking after the retry
    try:
        result = _run_loop(_LoopProvider([EDIT1, EDIT1]), _initial([F1]),
                           max_iterations=5)
    finally:
        restore()
    check("the run HOLDs", result["status"] != CP.PASS, result)
    check("only one recheck was ever spent -- the repeat is caught before a second one",
          gcalls["n"] == 1, gcalls)
    check("two proposals were made (detected, not silently retried forever)",
          result["grounding_repair_proposals"] == 2, result)


def _distinct_valid_narrowings(n: int) -> list:
    """`n` distinct, individually-valid subtractive rewrites of F1's sentence -- distinct
    by internal spacing (which apply_local_grounding_repair's number/entity extraction
    treats identically to the single-spaced form, so every one of them is accepted at
    the local-permission check), never by whitespace-only content that .strip() would
    collapse to the same "" every time."""
    return [{"edits": [{"finding_id": "F1", "operation": "DELETE",
                        "original": "The room was painted in 1990.",
                        "repaired": ("The room" + " " * i + "was painted."),
                        "fact_ids": []}]} for i in range(1, n + 1)]


def test_a_no_progress_repair_terminates_hold_within_the_fuse():
    """Every retry swaps in yet another different single blocker -- never repeating a
    signature, so only the STRICT-SHRINK requirement (not the repeat guard) is what
    stops this from running forever."""
    swaps = [_finding("F%d" % i, "claim %d" % i) for i in range(2, 8)]
    restore, gcalls = _ground_seq([_ground_reply([f]) for f in swaps])
    try:
        result = _run_loop(_LoopProvider(_distinct_valid_narrowings(6)), _initial([F1]),
                           max_iterations=CP.GROUNDING_COMPLETION_MAX_ITERATIONS)
    finally:
        restore()
    check("the run HOLDs -- no progress was ever made", result["status"] != CP.PASS,
          result)
    check("nothing was ever accepted", result["grounding_repairs_accepted"] == 0, result)
    check("the fuse, not an infinite retry, is what stopped it",
          result["grounding_completion_iterations"]
          == CP.GROUNDING_COMPLETION_MAX_ITERATIONS, result)


def test_the_emergency_ceiling_prevents_runaway_execution():
    """Each proposal's wording differs (so the repeat-signature guard alone would not
    stop it), and the grounder is scripted to keep reporting exactly one blocker every
    time -- so ONLY the max_iterations fuse can end this."""
    restore, gcalls = _ground_seq([_ground_reply([F1]) for _ in range(8)])
    try:
        result = _run_loop(_LoopProvider(_distinct_valid_narrowings(8)), _initial([F1]),
                           max_iterations=3)
    finally:
        restore()
    check("the loop stops at exactly the fuse, not before or after",
          result["grounding_completion_iterations"] == 3, result)
    check("still HOLD", result["status"] != CP.PASS, result)


def test_local_neighbor_context_is_supplied_to_the_repair_model():
    """Real production shape (retained Poetry, 2026-09-09): the sentence after the
    flagged passage refers back to it ('Something similar...') -- the repair proposal
    must be SHOWN that neighbor, read-only, so it can avoid breaking it."""
    article = ("The device was tested in a lab. The chair was carved in 1991. "
              "Something similar happened with the table.")
    findings = [_finding("F1", "The chair was carved in 1991.")]
    prov = _LoopProvider([_edit("F1", "The chair was carved in 1991.", "")])
    result = CP.grounding_repair_proposal(prov, article, findings, LOOP_LEDGER,
                                          LOOP_PACKET)
    check("a repair proposal was made", result["status"] == CP.PASS, result)
    check("the previous sentence is in the prompt",
          "The device was tested in a lab." in prov.prompts[0], prov.prompts[0])
    check("the next sentence -- the one with the dangling reference -- is in the prompt",
          "Something similar happened with the table." in prov.prompts[0],
          prov.prompts[0])
    check("the system prompt instructs against breaking what a neighbor depends on",
          "DO NOT REMOVE INFORMATION THAT AN UNEDITED NEIGHBORING SENTENCE DEPENDS ON"
          in CP.GROUNDING_COMPLETION_LOOP_SYSTEM)
    check("and the prompt itself labels the context as read-only",
          "NEXT SENTENCE (read-only" in prov.prompts[0], prov.prompts[0])


def test_grounding_repair_proposal_uses_the_claim_local_validator():
    """Factual permission stays claim-local, unchanged: the proposal step is verified by
    apply_local_grounding_repair(), never the packet-wide apply_grounding_repair() --
    the SAME guarantee test_grounding_repair_permission_is_claim_local_not_packet_wide
    already proves for the function itself; this proves the LOOP actually calls it."""
    tree = ast.parse((HERE / "new_engine_v1" / "composition.py").read_text())
    fn = next(n for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef) and n.name == "grounding_repair_proposal")
    calls = {getattr(n.func, "id", "") for n in ast.walk(fn) if isinstance(n, ast.Call)}
    check("grounding_repair_proposal validates with the claim-local function",
          "apply_local_grounding_repair" in calls, sorted(calls))
    check("never the packet-wide one", "apply_grounding_repair" not in calls,
          sorted(calls))


def test_no_worth_or_ledger_rerun_inside_the_loop():
    """No Worth rerun, no Ledger rerun, no new research, no Architecture rerun, no
    Writer regeneration, anywhere the progress-bounded loop can reach."""
    tree = ast.parse((HERE / "new_engine_v1" / "composition.py").read_text())
    for name in ("grounding_completion_loop", "grounding_repair_proposal"):
        fn = next(n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == name)
        calls = {getattr(n.func, "id", "") for n in ast.walk(fn)
                if isinstance(n, ast.Call)}
        check("%s reruns none of Worth/Ledger/Architecture/Writer" % name,
              not calls & {"freeze_ledger", "worth_gate", "architect", "write_article"},
              sorted(calls))


# ══════════════════════════════════════════════════════════════════════════════
# DELETE_UNSUPPORTED_SURFACE -- deterministic subtractive repair (owner-directed,
# 2026-09-09)
# ══════════════════════════════════════════════════════════════════════════════
# The real retained-Poetry shape: the licensed fact says "one experiment involved 27
# German-speaking participants"; the article says "a SEPARATE experiment with 27
# German-speaking participants". The unsupported word is a single adjective, and the
# very next (unedited) sentence -- "Something similar is at work..." -- is the exact
# sentence a bigger rewrite orphaned in the real run these tests are named after.
SUB_ARTICLE = (
    "Psychology experts have given an account of why a poem should move anyone at all. "
    "In a separate experiment with 27 German-speaking participants, researchers used "
    "psychophysiology to show that recited poetry could produce a range of responses "
    "from chills to goosebumps. Something similar is at work in ongoing doctoral "
    "research by the author of these exercises.")
SUB_LEDGER = {
    "F12": {"proposition": "One experiment involved 27 German-speaking participants.",
           "support_span": "In one experiment that involved 27 German-speaking "
                           "participants"},
    "F13": {"proposition": "In that experiment researchers used psychophysiology, "
                           "brain imaging and behavioural responses to show that "
                           "recited poetry could produce a range of responses from "
                           "chills to goosebumps.",
           "support_span": "researchers used psychophysiology (the study of how "
                           "thoughts and emotions link to physical responses in the "
                           "human body), brain imaging and behavioural responses to "
                           "show that recited poetry could produce a range of "
                           "responses from chills to goosebumps"},
}
SUB_FINDING = dict(_finding(
    "F1", "In a separate experiment with 27 German-speaking participants",
    cls="TRUE_UNCERTAIN"),
    suggested_patch="In one experiment involving 27 German-speaking participants")


def test_unsupported_modifier_is_removed_by_deterministic_subtraction():
    """1. "a separate experiment" -> deterministic subtraction removes "separate" and
    nothing else -> the Grounding blocker disappears, spending no repair-model call."""
    edit = CP.deterministic_subtractive_edit(SUB_ARTICLE, SUB_FINDING, SUB_LEDGER)
    check("a deterministic edit is constructed", edit is not None, edit)
    check("what was removed is exactly the one unsupported word",
          edit["what_was_removed"] == "separate", edit)
    check("everything else in the sentence survives verbatim",
          edit["repaired"] ==
          "In a experiment with 27 German-speaking participants, researchers used "
          "psychophysiology to show that recited poetry could produce a range of "
          "responses from chills to goosebumps.", edit["repaired"])

    restore, gcalls = _ground_seq([_ground_reply([])])   # PASS once "separate" is gone
    try:
        prov = _LoopProvider([])   # would raise if the model path were ever reached
        result = _run_loop(prov, _initial([SUB_FINDING]), article=SUB_ARTICLE,
                           ledger=SUB_LEDGER)
    finally:
        restore()
    check("the run reaches PASS via the deterministic edit alone",
          result["status"] == CP.PASS, result.get("blocking"))
    check("the deterministic path is what was accepted, not the model",
          result["grounding_deterministic_accepted"] == 1
          and result["grounding_repairs_accepted"] == 1, result)
    check("the neighboring sentence is untouched in the final article",
          "Something similar is at work in ongoing doctoral research by the author "
          "of these exercises." in result["article_text"], result["article_text"])


def test_deterministic_subtraction_spends_zero_model_calls_when_it_succeeds():
    """2. No repair-model call is made at all when the deterministic path resolves the
    finding -- provider.complete() is never invoked. The mandatory Grounding recheck
    after ANY candidate (deterministic or not) is still a real Grounder call and still
    costs its one model_calls -- what this proves is that the REPAIR step itself, the
    one grounding_repair_proposal() would have spent, is skipped."""
    restore, gcalls = _ground_seq([_ground_reply([])])
    try:
        prov = _LoopProvider([])
        result = _run_loop(prov, _initial([SUB_FINDING]), article=SUB_ARTICLE,
                           ledger=SUB_LEDGER)
    finally:
        restore()
    check("the provider was never called for a repair proposal", prov.calls == 0,
          prov.calls)
    check("model_calls reflects only the mandatory recheck (1), not a repair call too",
          result["model_calls"] == 1, result)


def test_deletion_cannot_introduce_new_factual_authority():
    """3. Verified by the SAME mechanical guard as any other Grounding repair, and it
    structurally cannot add a number, entity or relation -- it only ever removes words
    already present."""
    edit = CP.deterministic_subtractive_edit(SUB_ARTICLE, SUB_FINDING, SUB_LEDGER)
    text, prov, errs = CP.apply_local_grounding_repair(
        SUB_ARTICLE, [edit], [SUB_FINDING], SUB_LEDGER, {})
    check("the mechanical guard accepts it -- nothing was added", not errs and prov, errs)
    check("no number in the repaired sentence beyond what the original already had",
          not (CP._numbers_of(edit["repaired"]) - CP._numbers_of(edit["original"])),
          edit)
    check("no entity in the repaired sentence beyond what the original already had",
          not (CP.ST._entities(edit["repaired"], skip_sentence_initial=False)
               - CP.ST._entities(edit["original"], skip_sentence_initial=False)), edit)


def test_deletion_that_leaves_an_unsupported_proposition_is_rejected():
    """4. If removing the word does not actually resolve the finding (the recheck still
    reports the SAME finding), the deterministic candidate is rejected transactionally,
    exactly like a model proposal that fails to shrink the blocking set."""
    restore, gcalls = _ground_seq([_ground_reply([SUB_FINDING])])
    try:
        result = _run_loop(_LoopProvider([]), _initial([SUB_FINDING]),
                           article=SUB_ARTICLE, ledger=SUB_LEDGER, max_iterations=1)
    finally:
        restore()
    check("the candidate is rejected, not accepted",
          result["grounding_repairs_accepted"] == 0, result)
    check("the deterministic path is what was tried",
          result["grounding_deterministic_attempts"] == 1, result)
    check("the accepted article is unchanged", result["article_text"] == SUB_ARTICLE,
          result["article_text"])


def test_deletion_that_creates_a_safety_problem_is_rejected():
    """5. Even a pure deletion can be transactionally rejected by Safety -- the guard is
    real for the deterministic path too, not a formality."""
    calls = {"n": 0}

    def audit_fn(text, package, **kw):
        calls["n"] += 1
        return {"status": CP.HOLD,
               "blocking": [{"classification": "NEW_UNSUPPORTED_FACTS", "quote": "x"}],
               "model_calls": 0}

    restore, gcalls = _ground_seq([])   # never reached -- Safety rejects first
    try:
        result = _run_loop(_LoopProvider([]), _initial([SUB_FINDING]),
                           audit_fn=audit_fn, article=SUB_ARTICLE, ledger=SUB_LEDGER,
                           max_iterations=1)
    finally:
        restore()
    check("no repair was accepted", result["grounding_repairs_accepted"] == 0, result)
    check("the accepted article is byte-for-byte the input",
          result["article_text"] == SUB_ARTICLE, result["article_text"])
    check("Safety was checked once and Grounding was never reached",
          calls["n"] == 1 and gcalls["n"] == 0, (calls, gcalls))


def test_neighboring_sentence_is_byte_for_byte_unchanged():
    """6. The deletion touches only the ONE sentence the finding names -- the exact
    property the real bug needed and did not have: the opening sentence and the
    "Something similar..." sentence both survive untouched."""
    cand = CP.deterministic_subtraction_candidate(SUB_ARTICLE, [SUB_FINDING],
                                                  SUB_LEDGER, {})
    check("a candidate is built", cand is not None, cand)
    check("the neighbor sentence survives byte-for-byte",
          "Something similar is at work in ongoing doctoral research by the author "
          "of these exercises." in cand["article_text"], cand["article_text"])
    check("the opening sentence survives byte-for-byte too",
          "Psychology experts have given an account of why a poem should move anyone "
          "at all." in cand["article_text"], cand["article_text"])


def test_fallback_to_model_proposal_when_subtraction_is_not_applicable():
    """7. A finding the deterministic path cannot resolve (F1's real overclaim here is
    the YEAR -- a bare number, which the word-content-only operator can never touch)
    falls straight through to the existing grounding_repair_proposal() model path,
    unchanged."""
    restore, gcalls = _ground_seq([_ground_reply([])])
    try:
        result = _run_loop(_LoopProvider([EDIT1]), _initial([F1]))
    finally:
        restore()
    check("the run reaches PASS via the model path", result["status"] == CP.PASS,
          result)
    check("no deterministic repair was accepted -- the model's proposal was used "
          "instead", result["grounding_deterministic_accepted"] == 0
          and result["grounding_repairs_accepted"] == 1, result)


def test_strict_progress_semantics_unchanged_for_deterministic_candidates():
    """8. Strict progress (blocking set STRICTLY smaller, no new Safety blocker) applies
    identically regardless of a candidate's origin -- proven directly above (tests 4 and
    5 reject a deterministic candidate on no-progress and on a new Safety blocker, the
    SAME two gates test_a_repair_that_replaces_one_blocker_with_another_is_rejected and
    test_a_repair_introducing_a_new_safety_blocker_is_rejected_and_never_mutates_the_
    article already prove for a model proposal); this asserts the loop's own source
    routes both origins through the identical check, not a parallel weaker one."""
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    fn_src = src.split("def grounding_completion_loop(")[1].split("\ndef ")[0]
    check("there is exactly one strict-shrink comparison in the loop, shared by every "
          "candidate origin", fn_src.count("< before_count") == 1, fn_src.count(
              "< before_count"))
    check("there is exactly one Safety-status check in the loop, shared by every "
          "candidate origin",
          fn_src.count('candidate_safety["status"] != PASS') == 1, fn_src)


def test_emergency_ceiling_unchanged():
    """9. GROUNDING_COMPLETION_MAX_ITERATIONS is still 5, and the deterministic path's
    "try once, then fall back to the model" rule (a candidate already in `tried` is
    skipped) still counts against the SAME iteration ceiling -- it does not buy the
    deterministic path any extra attempts. Iteration 1 is the deterministic candidate
    (rejected, no progress); iterations 2-5 are distinct model proposals (each rejected
    the same way), and the loop still stops at exactly 5."""
    check("the ceiling constant is unchanged", CP.GROUNDING_COMPLETION_MAX_ITERATIONS
          == 5)
    original_sentence = (
        "In a separate experiment with 27 German-speaking participants, researchers "
        "used psychophysiology to show that recited poetry could produce a range of "
        "responses from chills to goosebumps.")
    model_edits = [{"edits": [{"finding_id": "F1", "operation": "DELETE",
                               "original": original_sentence,
                               "repaired": original_sentence.replace(
                                   "psychophysiology", "psychophysiology" + " " * i),
                               "fact_ids": []}]} for i in range(1, 5)]
    restore, gcalls = _ground_seq([_ground_reply([SUB_FINDING])] * 5)
    try:
        result = _run_loop(_LoopProvider(model_edits), _initial([SUB_FINDING]),
                           article=SUB_ARTICLE, ledger=SUB_LEDGER)
    finally:
        restore()
    check("the loop stops at exactly the (unchanged) ceiling",
          result["grounding_completion_iterations"]
          == CP.GROUNDING_COMPLETION_MAX_ITERATIONS, result)
    check("exactly one of the five attempts was the deterministic candidate",
          result["grounding_deterministic_attempts"] == 1, result)
    check("still HOLD", result["status"] != CP.PASS, result)


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
               test_the_model_call_budget,
               test_three_independent_blockers_all_repair_and_pass,
               test_accepted_repair_strictly_reduces_blocker_set,
               test_a_repair_that_replaces_one_blocker_with_another_is_rejected,
               test_a_repair_introducing_a_new_safety_blocker_is_rejected_and_never_mutates_the_article,
               test_a_rejected_repair_can_be_followed_by_a_different_successful_proposal,
               test_repeating_the_same_ineffective_proposal_terminates_hold,
               test_a_no_progress_repair_terminates_hold_within_the_fuse,
               test_the_emergency_ceiling_prevents_runaway_execution,
               test_local_neighbor_context_is_supplied_to_the_repair_model,
               test_grounding_repair_proposal_uses_the_claim_local_validator,
               test_no_worth_or_ledger_rerun_inside_the_loop,
               test_unsupported_modifier_is_removed_by_deterministic_subtraction,
               test_deterministic_subtraction_spends_zero_model_calls_when_it_succeeds,
               test_deletion_cannot_introduce_new_factual_authority,
               test_deletion_that_leaves_an_unsupported_proposition_is_rejected,
               test_deletion_that_creates_a_safety_problem_is_rejected,
               test_neighboring_sentence_is_byte_for_byte_unchanged,
               test_fallback_to_model_proposal_when_subtraction_is_not_applicable,
               test_strict_progress_semantics_unchanged_for_deterministic_candidates,
               test_emergency_ceiling_unchanged):
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
