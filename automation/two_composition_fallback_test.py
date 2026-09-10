#!/usr/bin/env python3
"""two_composition_fallback_test.py -- TWO compositions per Worth-PASS story, no third.

WHY IT EXISTS. Worth-PASS stories were dying on their own prose, and the answer had been
an ever-longer chain of local repairs on that prose. A frozen ten-run production batch
published nothing: one night run spent five repair proposals on a single draft, accepted
one, and still held. The retained evidence could not even say whether the proposals were
bad or the gate simply read differently the second time. Local repair had reached its
useful end, and the only lever left was the owner arbitrating wording by hand -- which is
exactly what must never be required.

So a Worth-PASS story now gets at most TWO complete compositions: A, the normal engine
with every bounded completion it already has, and -- only for an eligible
composition-surface HOLD -- ONE fresh SAFE_RECOMPOSE from the SAME frozen upstream.

WHAT THESE TESTS HOLD. That B is a fresh composition and not a repair of A (no article,
no package, no edits, no findings cross over); that upstream is reused and never re-run;
that every gate still runs on B; that only the winning attempt can publish; that there
can never be a third; and that the accounting tells A's cost from B's.

Offline: the real composition orchestration, the real gates, the real validators, a
scripted provider. No network.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP                            # noqa: E402
from new_engine_v1 import runner as RUNNER                             # noqa: E402
import story_architecture_composition_test as H                        # noqa: E402

FAILURES: list = []


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %s" % (detail,)))
    if not ok:
        FAILURES.append(label)


# ── harness ───────────────────────────────────────────────────────────────────
def _package_dek() -> str:
    """The dek the deterministic test packager builds from the known-good draft."""
    _, clean = H.run(H.full_script())
    return (clean["package"] or {})["dek"]


def _pkg_finding(dek: str, fid="P1") -> dict:
    """A blocking finding whose quote lives in the PACKAGE, not the article.

    Chosen deliberately: it drives A to a terminal GROUNDING HOLD through the engine's
    own real path -- one furniture repackage, then a completion loop with no
    article-surface target -- without scripting a single repair-proposal reply. It is the
    exact shape of retained night-batch run 3.
    """
    return {"id": fid, "classification": "TRUE_UNSUPPORTED", "quote": dek[:80],
            "why": "not carried by the evidence"}


def _fallback_run(ground_seq, *, a_script=None, b_script=None, out_dir=None,
                  fact_check_fn=None, reader_reply=None):
    """run_composition_with_fallback with the Grounder stubbed at the stages boundary.

    A's script is the full six-reply composition; B's is three replies (writer envelope,
    continuity edits, reader), because B replays LEDGER, WORTH and ARCHITECTURE and so
    makes no model call for any of them -- which is itself asserted below.
    """
    import new_engine_v1.stages as S
    real = S.ground
    seq = list(ground_seq)
    calls = {"n": 0}

    def fake(*a, **k):
        calls["n"] += 1
        return dict(seq.pop(0) if seq else H.GROUND_CLEAN)

    S.ground = fake
    # NOTE. `a_script` must be EXACTLY what A consumes. An A that holds before the Reader
    # never pops a Reader reply, and a leftover one would be handed to B's Writer as its
    # first reply -- unusable, so write_article would retry and the call sequence would
    # show a spurious extra WRITER.
    script = list(a_script if a_script is not None else H.full_script())
    script += list(b_script or [])
    prov = H.Scripted(script)
    try:
        out = CP.run_composition_with_fallback(
            prov, pack=H.PACK, source_text=H.S0, source_sha="x",
            subject=H.PACK["subject"], out_dir=out_dir,
            fact_check_fn=fact_check_fn or (lambda a: dict(H.FC_CLEAN)))
        return prov, calls, out
    finally:
        S.ground = real


def _a_script_no_reader():
    """A's replies for a run that HOLDs before the Reader: ledger, worth, architecture,
    writer envelope, continuity edits. PROSE FINISH and PACKAGE are answered by the
    harness itself, and the Reader is never reached."""
    return H.full_script()[:5]


def _b_script(article=None, reader=None):
    art = article if article is not None else H.DRAFT
    return [H.envelope(art), H._edits_from(art), reader or H.READER_OK]


def _stages_seen(prov):
    return [prov.stage_of(i) for i in range(len(prov.calls))]


# ── 1. a passing A never produces a B ─────────────────────────────────────────
def test_a_clean_pass_never_generates_a_second_composition():
    """1. The fallback is for a failed composition surface. A run that publishes has no
    failed surface, so B must not exist -- and must not have cost a call."""
    prov, gcalls, out = _fallback_run([dict(H.GROUND_CLEAN)])
    check("A passes", out["status"] == CP.PASS, out.get("failure_reason"))
    check("exactly one composition happened", out["composition_attempts_count"] == 1,
          out["composition_attempts"])
    check("the fallback did not trigger",
          out["fallback_recomposition_triggered"] is False, out)
    check("and it says why", "passed" in out["fallback_recomposition_reason"],
          out["fallback_recomposition_reason"])
    check("no second WRITER call was made",
          _stages_seen(prov).count("WRITER") == 1, _stages_seen(prov))
    check("attempt B has no cost recorded", out["attempt_b_model_calls"] is None, out)
    check("the winning attempt is A", out["winning_attempt"] == "A", out)


# ── 2. an eligible GROUNDING hold produces exactly one B ──────────────────────
def test_an_eligible_grounding_hold_generates_b_exactly_once():
    """2. A's real terminal GROUNDING HOLD -- one furniture repackage, then a completion
    loop with nothing on the article surface to repair -- is handed to ONE fresh
    composition, which passes."""
    dek = _package_dek()
    f = _pkg_finding(dek)
    prov, gcalls, out = _fallback_run(
        [{"status": "settled", "findings": [dict(f)]},      # A initial: package-only
         {"status": "settled", "findings": [dict(f)]},      # A post-repackage recheck
         dict(H.GROUND_CLEAN)],                             # B: clean
        a_script=_a_script_no_reader(), b_script=_b_script())
    a, b = out["composition_attempts"]
    check("A held at GROUNDING", a["terminal_stage"] == CP.GROUNDING, a)
    check("A ran in NORMAL mode", a["mode"] == CP.COMPOSE_NORMAL, a)
    check("the fallback triggered", out["fallback_recomposition_triggered"] is True, out)
    check("exactly two compositions, never three",
          out["composition_attempts_count"] == 2, out["composition_attempts"])
    check("B ran in SAFE_RECOMPOSE mode", b["mode"] == CP.COMPOSE_SAFE_RECOMPOSE, b)
    check("B passed", b["status"] == CP.PASS, b)
    check("the run's verdict is B's", out["status"] == CP.PASS
          and out["winning_attempt"] == "B", out)
    check("exactly two WRITER calls, one per composition",
          _stages_seen(prov).count("WRITER") == 2, _stages_seen(prov))


# ── 3. an eligible SAFETY hold produces exactly one B ─────────────────────────
def test_an_eligible_safety_hold_generates_b_exactly_once():
    """3. The same, for Safety: an unapproved sensory word in A's prose."""
    bad = H.DRAFT.replace("The room was built from Himalayan salt bricks",
                          "The room was built from pink Himalayan salt bricks")
    prov, _g, out = _fallback_run(
        [dict(H.GROUND_CLEAN)],
        # A's Safety HOLD path spends its ONE safety-repair call (Stage 9b) before it
        # gives up, so A's script has to answer it. An empty object is a proposal with no
        # usable edits: the repair is abandoned and A holds at SAFETY, which is the
        # terminal this test is about.
        a_script=H.full_script()[:3] + [H.envelope(bad), H._edits_from(bad), {}],
        b_script=_b_script())
    a, b = out["composition_attempts"]
    check("A held at SAFETY", a["terminal_stage"] == CP.SAFETY, a)
    check("the fallback triggered once", out["fallback_recomposition_triggered"] is True
          and out["composition_attempts_count"] == 2, out)
    check("B is the SAFE_RECOMPOSE attempt and it passed",
          b["mode"] == CP.COMPOSE_SAFE_RECOMPOSE and b["status"] == CP.PASS, b)
    check("the run publishes B", out["winning_attempt"] == "B"
          and out["status"] == CP.PASS, out)


# ── 4./5./6. eligibility is deterministic and fail-closed ─────────────────────
def _res(stage, code, **kw):
    """A composition result of the shape the eligibility owner actually reads."""
    base = {"status": CP.HOLD, "compose_mode": CP.COMPOSE_NORMAL,
            "failure_stage": stage, "reason_code": code,
            "stages": {CP.LEDGER: CP.PASS, CP.WORTH: CP.PASS,
                       CP.ARCHITECTURE: CP.PASS},
            "article_text": "# t\n\nsome prose",
            "detail": {CP.LEDGER: {"ledger": {"F1": {}}},
                       CP.ARCHITECTURE: {"architecture": {"a": 1}}}}
    base.update(kw)
    return base


def test_every_eligible_composition_terminal_is_accepted():
    """4. The composition-surface terminals a fresh composition can plausibly answer."""
    for stage, code in ((CP.SAFETY, CP.SAFETY_HOLD), (CP.GROUNDING, CP.GROUNDING_HOLD),
                        (CP.FACT_CHECK, CP.FACT_CHECK_HOLD)):
        ok, why = CP.fallback_recomposition_eligible(_res(stage, code))
        check("%s is an eligible composition terminal" % stage, ok, why)


def test_a_reader_hold_does_not_earn_a_recomposition():
    """A READER hold is NOT eligible. B recomposes from the same frozen architecture, and
    the Reader's complaint is about that plan -- across five retained Reader-terminal runs
    the same five dimensions hold every time and the Reader names the selection, not the
    sentences. Twice in production B then regressed below an A that had cleared the whole
    factual stack (8a338f42, 1906b00c), discarding the better draft."""
    ok, why = CP.fallback_recomposition_eligible(_res(CP.READER, CP.READER_HOLD))
    check("a READER hold is refused", not ok, why)
    check("and the refusal names the stage, not the mode",
          "READER" in why and "eligible composition terminal" in why, why)


def test_the_fallback_budget_is_spent_whichever_attempt_wins():
    """THE INVARIANT WINNER SELECTION NEARLY BROKE. Returning the furthest attempt means a
    tie returns A's own result, whose compose_mode is NORMAL. If eligibility read only the
    mode, that result would look like a fresh first attempt and a caller could spend a
    third composition. The budget is recorded on the result itself."""
    spent_a = _res(CP.GROUNDING, CP.GROUNDING_HOLD,
                   fallback_recomposition_triggered=True)
    ok, why = CP.fallback_recomposition_eligible(spent_a)
    check("an A-won result after a fallback ran is refused", not ok, why)
    check("and the refusal names the maximum", "maximum" in why, why)
    spent_b = _res(CP.GROUNDING, CP.GROUNDING_HOLD,
                   compose_mode=CP.COMPOSE_SAFE_RECOMPOSE,
                   fallback_recomposition_triggered=True)
    check("a B-won result after a fallback ran is refused",
          not CP.fallback_recomposition_eligible(spent_b)[0], "")
    check("a fresh attempt with no fallback spent is still eligible",
          CP.fallback_recomposition_eligible(_res(CP.GROUNDING, CP.GROUNDING_HOLD))[0], "")


def test_the_run_reports_the_attempt_that_got_furthest():
    """A regressing B must not relabel the run. Publication rights are untouched: only a
    PASS can be publication_ready, so this can never promote a held article."""
    A_reader = {"status": CP.HOLD, "failure_stage": CP.READER}
    B_ground = {"status": CP.HOLD, "failure_stage": CP.GROUNDING}
    check("A at READER outranks B at GROUNDING",
          CP.attempt_progress(A_reader) > CP.attempt_progress(B_ground), "")
    check("a PASS outranks every HOLD",
          CP.attempt_progress({"status": CP.PASS}) > CP.attempt_progress(A_reader), "")
    check("a tie does not displace A",
          not (CP.attempt_progress(dict(A_reader)) > CP.attempt_progress(dict(A_reader))), "")
    check("an unknown stage sorts last, never ahead of a real one",
          CP.attempt_progress({"status": CP.HOLD, "failure_stage": "NOPE"})
          < CP.attempt_progress(B_ground), "")


def test_pre_composition_holds_are_never_eligible():
    """5. Research, Ledger, Worth and Architecture HOLDs are selection or authority
    failures. A second draft from the same authority cannot answer any of them."""
    for stage, code in ((CP.WORTH, CP.WORTH_HOLD), (CP.LEDGER, CP.LEDGER_HOLD),
                        (CP.ARCHITECTURE, CP.ARCHITECTURE_HOLD),
                        (CP.CUT_TERMS, CP.CUT_TERMS_HOLD),
                        (CP.WRITER, CP.WRITER_HOLD),
                        (CP.CONTINUITY, CP.CONTINUITY_HOLD)):
        ok, why = CP.fallback_recomposition_eligible(_res(stage, code))
        check("%s HOLD is refused" % stage, not ok, why)
    # A research HOLD never reaches composition at all: there is no composition result.
    ok, why = CP.fallback_recomposition_eligible(None)
    check("a run with no composition result is refused", not ok, why)


def test_eligibility_fails_closed_on_everything_it_does_not_recognise():
    """6. A blocker whose remedy is different evidence, a different provider or different
    code is refused -- and so is anything unfamiliar, rather than being guessed at."""
    ok, why = CP.fallback_recomposition_eligible(
        _res(CP.WRITER, CP.CLAUDE_SUBSCRIPTION_LIMIT))
    check("a subscription limit is not a composition defect", not ok, why)
    ok, why = CP.fallback_recomposition_eligible(
        _res(CP.GROUNDING, "SOME_FUTURE_CODE_NOBODY_HAS_SEEN"))
    check("an unrecognised reason_code is refused, not assumed repairable", not ok, why)
    ok, why = CP.fallback_recomposition_eligible(_res("SOME_FUTURE_STAGE", CP.SAFETY_HOLD))
    check("an unrecognised failure stage is refused", not ok, why)
    # Upstream that did not actually succeed leaves nothing sound to recompose FROM.
    ok, why = CP.fallback_recomposition_eligible(
        _res(CP.GROUNDING, CP.GROUNDING_HOLD,
             stages={CP.LEDGER: CP.PASS, CP.WORTH: CP.HOLD,
                     CP.ARCHITECTURE: CP.PASS}))
    check("a story whose Worth did not pass is refused", not ok, why)
    ok, why = CP.fallback_recomposition_eligible(
        _res(CP.GROUNDING, CP.GROUNDING_HOLD, detail={CP.ARCHITECTURE: {}}))
    check("no frozen ledger to recompose from is refused", not ok, why)
    ok, why = CP.fallback_recomposition_eligible(
        _res(CP.SAFETY, CP.SAFETY_HOLD, article_text="   "))
    check("an attempt that produced no article is refused", not ok, why)
    check("a REPLAYED upstream is still sound authority",
          CP.fallback_recomposition_eligible(
              _res(CP.GROUNDING, CP.GROUNDING_HOLD,
                   stages={CP.LEDGER: CP.REPLAYED, CP.WORTH: CP.REPLAYED,
                           CP.ARCHITECTURE: CP.REPLAYED}))[0], "")


# ── 7./8./20. what crosses from A to B, and what cannot ───────────────────────
def test_b_inherits_frozen_authority_and_nothing_else():
    """7./8./20. The isolation B depends on is a return type, not a promise in a prompt:
    _frozen_upstream_of() can only produce three keys, and the replay slot that would
    carry an article is never populated."""
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    body = src.split("def _frozen_upstream_of(")[1].split("\ndef ")[0]
    got = CP._frozen_upstream_of(
        {"detail": {CP.LEDGER: {"ledger": {"F1": {}}}, CP.WORTH: {"status": CP.PASS},
                    CP.ARCHITECTURE: {"architecture": {"a": 1}},
                    CP.WRITER: {"article_text": "A PROSE"},
                    CP.PACKAGE: {"package": {"dek": "A DEK"}},
                    CP.GROUNDING: {"grounding": {"findings": [1]},
                                   "grounding_completion_history": [{"x": 1}]},
                    CP.READER: {"dimensions": {}}},
         "article_text": "A PROSE", "package": {"dek": "A DEK"}})
    check("exactly ledger, worth and architecture cross over",
          set(got) == {"ledger", "worth", "architecture"}, sorted(got))
    blob = json.dumps(got, default=str)
    for leak, what in (("A PROSE", "article A's prose"), ("A DEK", "package A's prose")):
        check("%s does not cross into B" % what, leak not in blob, blob[:200])
    code = "\n".join(ln for ln in body.splitlines()
                      if ln.strip() and not ln.lstrip().startswith("#")
                      and '"""' not in ln)
    code = code.split("return {", 1)[-1] if "return {" in code else code
    for banned in ('"article"', "article_text", "package", "grounding",
                   "completion_history", "reader", "edits", "repair"):
        check("_frozen_upstream_of cannot carry %s" % banned, banned not in code, code)
    # And the caller never fills the article replay slot either.
    caller = src.split("def run_composition_with_fallback(")[1]
    check("the fallback never populates frozen['article']",
          '"article"' not in caller and "'article'" not in caller, caller[-600:])


def test_b_writer_gets_the_same_packet_but_the_safe_contract():
    """9./19. Same factual permission, different writing contract -- and the packet is
    identical because the Ledger and Architecture behind it were reused, not re-run."""
    dek = _package_dek()
    f = _pkg_finding(dek)
    prov, _g, out = _fallback_run(
        [{"status": "settled", "findings": [dict(f)]},
         {"status": "settled", "findings": [dict(f)]},
         dict(H.GROUND_CLEAN)],
        a_script=_a_script_no_reader(), b_script=_b_script())
    w = [c for c in prov.calls
         if "writing one finished article from an approved" in c["system"].lower()]
    check("both compositions called the Writer", len(w) == 2, len(w))
    if len(w) != 2:
        return
    check("B's writer packet is byte-identical to A's -- the same factual permission",
          w[0]["user"] == w[1]["user"], "")
    check("A used the normal contract", w[0]["system"] == CP.WRITER_SYSTEM, "")
    check("B used the SAFE_RECOMPOSE contract",
          w[1]["system"] == CP.WRITER_SYSTEM_SAFE_RECOMPOSE, "")
    check("the safe contract is the normal one plus a conservative hand",
          w[1]["system"].startswith(w[0]["system"])
          and CP.SAFE_RECOMPOSE_DELTA in w[1]["system"], "")
    check("A's prose is nowhere in B's writer call",
          "salt bricks from Tuscany" not in w[1]["system"], "")
    # 19./20. Upstream was reused, so it made no model call in B -- and no research call
    # was made by the fallback at any point.
    seen = _stages_seen(prov)
    check("LEDGER ran once, for A only", seen.count("LEDGER") == 1, seen)
    check("WORTH ran once, for A only", seen.count("WORTH") == 1, seen)
    check("ARCHITECTURE ran once, for A only", seen.count("ARCHITECTURE") == 1, seen)
    b = out["composition_attempts"][1]
    for s in (CP.LEDGER, CP.WORTH, CP.ARCHITECTURE):
        check("B records %s as REPLAYED, not re-run" % s,
              b["stages"].get(s) == CP.REPLAYED, b["stages"])
    check("no research call was made inside the fallback",
          not any("research" in c["system"].lower()[:80] for c in prov.calls), "")


def test_as_prose_cannot_reach_bs_writer_call():
    """1. THE STRONGEST AVAILABLE LEAK TEST, and the reason the source scan above is not
    relied on alone. A's article carries the token "pink", which exists nowhere in the
    ledger, the packet or the base draft -- it is exactly the unapproved surface that got
    A refused. If ANY of A's prose, or any repair derived from it, reached B, that token
    would appear in B's Writer call. It appears in neither half of it."""
    bad = H.DRAFT.replace("The room was built from Himalayan salt bricks",
                          "The room was built from pink Himalayan salt bricks")
    prov, _g, out = _fallback_run(
        [dict(H.GROUND_CLEAN)],
        a_script=H.full_script()[:3] + [H.envelope(bad), H._edits_from(bad), {}],
        b_script=_b_script())
    a = out["composition_attempts"][0]
    check("A really was refused for that token",
          "pink" in str(a["failure_reason"]), a["failure_reason"])
    w = [c for c in prov.calls
         if "writing one finished article from an approved" in c["system"].lower()]
    check("both compositions called the Writer once each", len(w) == 2, len(w))
    if len(w) != 2:
        return
    check("A's unapproved token is not in B's writer system prompt",
          "pink" not in w[1]["system"], "")
    check("nor in B's writer user prompt -- B was handed the packet, not the draft",
          "pink" not in w[1]["user"], "")
    check("and B's packet is byte-identical to A's: same authority, no inherited prose",
          w[0]["user"] == w[1]["user"], "")


def test_b_produces_its_own_prose_and_its_own_package():
    """9./11. B's article is B's, and its package is generated fresh FROM B -- package A
    never seeds it."""
    dek = _package_dek()
    f = _pkg_finding(dek)
    other = H.DRAFT.replace("# The room made of salt", "# A room of salt")
    prov, _g, out = _fallback_run(
        [{"status": "settled", "findings": [dict(f)]},
         {"status": "settled", "findings": [dict(f)]},
         dict(H.GROUND_CLEAN)],
        a_script=_a_script_no_reader(), b_script=_b_script(article=other))
    a, b = out["composition_attempts"]
    check("B's article differs from A's",
          a["article_sha256"] != b["article_sha256"], (a["article_sha256"],
                                                       b["article_sha256"]))
    check("the run's article is B's", out["article_sha256"] == b["article_sha256"], "")
    check("B has its own package", bool(out["package"]), out.get("package_status"))
    pkg_calls = [c for c in prov.calls
                 if "editor who decides how a finished article is presented"
                 in c["system"].lower()]
    check("every package call was given an article to work from, never a previous package",
          all("THE FINISHED ARTICLE" in c["user"] for c in pkg_calls), len(pkg_calls))
    check("B's package was written from B's own article",
          any("A room of salt" in c["user"] for c in pkg_calls), "")


# ── 10./12./13. B is a full composition, not a shortcut ───────────────────────
def test_b_runs_every_gate_and_keeps_as_artifacts():
    """10./12./13. B meets Safety, Grounding, Fact Check and the Reader exactly as A did,
    its bounded completion machinery is its own, and A's artifacts are still on disk."""
    dek = _package_dek()
    f = _pkg_finding(dek)
    fc = {"n": 0}

    def counting_fact_check(article):
        fc["n"] += 1
        return dict(H.FC_CLEAN)

    with tempfile.TemporaryDirectory() as d:
        out_dir = pathlib.Path(d) / "run"
        prov, gcalls, out = _fallback_run(
            [{"status": "settled", "findings": [dict(f)]},
             {"status": "settled", "findings": [dict(f)]},
             dict(H.GROUND_CLEAN)],
            a_script=_a_script_no_reader(),
            # B writes DISTINCT prose here on purpose: if B reused A's exact article the
            # hashes would coincide and the "top level is not A's article" assertion
            # could not tell a fixed persister from a broken one.
            b_script=_b_script(article=H.DRAFT.replace("# The room made of salt",
                                                       "# A room of salt")),
            out_dir=out_dir, fact_check_fn=counting_fact_check)
        a, b = out["composition_attempts"]
        check("B's own gates all ran",
              all(b["stages"].get(s) == CP.PASS
                  for s in (CP.SAFETY, CP.GROUNDING, CP.FACT_CHECK, CP.READER)),
              b["stages"])
        check("the Grounder ran for B as well as A", gcalls["n"] == 3, gcalls)
        check("the Fact Check ran for B", fc["n"] >= 1, fc)
        check("the Reader ran for B -- and only for B, since A never reached it",
              _stages_seen(prov).count("READER") == 1
              and b["stages"].get(CP.READER) == CP.PASS
              and a["stages"].get(CP.READER) == CP.NOT_RUN,
              (_stages_seen(prov), a["stages"].get(CP.READER)))
        # ATTEMPT ARTIFACT INTEGRITY. Production run
        # production-20260910T093541Z-8a338f42 held ONE directory describing TWO
        # different articles: A's COMPOSITION_RESULT.json/ARTICLE_FINAL.md beside the
        # runner-level WRITER_OUTPUT.json built from B. The old assertions here treated
        # "the top-level result still says A held" as A-retention working, and so could
        # not see it. Winner identity at top level is the invariant.
        a_dir, b_dir = out_dir / "attempt-A", out_dir / "attempt-B"
        check("A's artifacts moved, whole, into attempt-A/", a_dir.is_dir()
              and (a_dir / "COMPOSITION_RESULT.json").exists()
              and (a_dir / "WRITER_DRAFT.md").exists(),
              sorted(x.name for x in out_dir.iterdir()))
        check("B persisted to its own directory", b_dir.is_dir(),
              sorted(x.name for x in out_dir.iterdir()))
        a_res = json.loads((a_dir / "COMPOSITION_RESULT.json").read_text())
        check("A's own retained record is intact and still says A held at GROUNDING",
              a_res["failure_stage"] == CP.GROUNDING
              and a_res["compose_mode"] == CP.COMPOSE_NORMAL, a_res.get("failure_stage"))
        b_res = json.loads((b_dir / "COMPOSITION_RESULT.json").read_text())
        check("B's retained record is the SAFE_RECOMPOSE pass",
              b_res["status"] == CP.PASS
              and b_res["compose_mode"] == CP.COMPOSE_SAFE_RECOMPOSE, b_res.get("status"))
        # THE DEFECT ITSELF: the top level must describe the attempt the verdict came
        # from, and must not still be carrying the other attempt's article.
        top = json.loads((out_dir / "COMPOSITION_RESULT.json").read_text())
        check("the TOP-LEVEL result is the winning attempt's, not A's",
              top["compose_mode"] == CP.COMPOSE_SAFE_RECOMPOSE
              and top["status"] == CP.PASS, (top.get("compose_mode"), top.get("status")))
        check("the top-level result agrees with what the orchestrator returned",
              top["article_sha256"] == out["article_sha256"]
              == b_res["article_sha256"], "")
        check("and it is NOT A's article",
              top["article_sha256"] != a_res["article_sha256"], "")
        check("the top-level article file is the winner's too",
              (out_dir / "ARTICLE_FINAL.md").read_text() == out["article_text"], "")
        check("A's bounded Grounding completion is recorded on A, not on B",
              (a_dir / "FACTUAL_COMPLETION.json").exists()
              and not (b_dir / "FACTUAL_COMPLETION.json").exists(), "")
        check("no stale A-only artifact was left at the top level",
              not any(x.is_file() and x.name.startswith("FACTUAL_COMPLETION")
                      for x in out_dir.iterdir()), "")


# ── 14./15./16./17. ownership, terminality, no third, accounting ──────────────
def test_a_single_attempt_run_keeps_the_old_artifact_layout_exactly():
    """The fallback must cost the common case nothing, INCLUDING nothing in its artifact
    shape: a run that never falls back still persists straight into out_dir, with no
    attempt-A/ or attempt-B/ subdirectory for a consumer to have to know about."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out_dir = pathlib.Path(d) / "run"
        prov, _g, out = _fallback_run([dict(H.GROUND_CLEAN)], out_dir=out_dir)
        check("the run passed on its first attempt", out["status"] == CP.PASS
              and out["composition_attempts_count"] == 1, out.get("failure_reason"))
        names = sorted(x.name for x in out_dir.iterdir())
        check("no attempt subdirectories were created",
              "attempt-A" not in names and "attempt-B" not in names, names)
        top = json.loads((out_dir / "COMPOSITION_RESULT.json").read_text())
        check("the top-level result is that single attempt's",
              top["compose_mode"] == CP.COMPOSE_NORMAL
              and top["article_sha256"] == out["article_sha256"], "")


def test_only_the_winning_attempt_can_publish():
    """14./18. The orchestrator returns the winning attempt's OWN result, so a held
    article and a refused package from A cannot reach publication state at all."""
    dek = _package_dek()
    f = _pkg_finding(dek)
    other = H.DRAFT.replace("# The room made of salt", "# A room of salt")
    prov, _g, out = _fallback_run(
        [{"status": "settled", "findings": [dict(f)]},
         {"status": "settled", "findings": [dict(f)]},
         dict(H.GROUND_CLEAN)],
        a_script=_a_script_no_reader(), b_script=_b_script(article=other))
    a, b = out["composition_attempts"]
    check("only B is publication_ready", b["publication_ready"] is True
          and a["publication_ready"] is False, (a["publication_ready"],
                                                b["publication_ready"]))
    check("the returned result is publication_ready", out["publication_ready"] is True,
          out)
    check("the returned article is B's, not A's",
          out["article_text"] == b and False or "A room of salt" in out["article_text"],
          out["article_sha256"])
    check("the returned bundle hash is B's", out["bundle_sha256"] == b["bundle_sha256"],
          "")
    check("A's held article is not what publishes",
          out["article_sha256"] != a["article_sha256"], "")
    check("the returned result carries no failure stage", out["failure_stage"] is None,
          out["failure_stage"])


def test_a_held_b_is_terminal_and_there_is_no_third_composition():
    """15./16. B HOLDing is the end of the story. The rule is enforced by the eligibility
    owner reading the attempt's OWN mode, so it cannot be defeated by call order."""
    dek = _package_dek()
    f = _pkg_finding(dek)
    prov, gcalls, out = _fallback_run(
        [{"status": "settled", "findings": [dict(f)]},   # A initial
         {"status": "settled", "findings": [dict(f)]},   # A recheck
         {"status": "settled", "findings": [dict(f)]},   # B initial
         {"status": "settled", "findings": [dict(f)]}],  # B recheck
        a_script=_a_script_no_reader(), b_script=_b_script())
    check("both compositions held", out["status"] == CP.HOLD, out.get("failure_reason"))
    check("exactly two compositions happened",
          out["composition_attempts_count"] == CP.MAX_COMPOSITION_ATTEMPTS,
          out["composition_attempts_count"])
    check("exactly two WRITER calls -- no third draft",
          _stages_seen(prov).count("WRITER") == 2, _stages_seen(prov))
    ok, why = CP.fallback_recomposition_eligible(out)
    check("the returned result is not eligible for a further fallback", not ok, why)
    check("and the refusal names the maximum", "maximum" in why, why)
    check("the run records that its fallback budget is spent",
          out["fallback_recomposition_triggered"] is True, out)
    check("nothing publishes", not out["publication_ready"], out)


def test_model_call_accounting_separates_the_two_attempts():
    """17. A's cost is A's and B's is B's -- no double counting, and the incremental price
    of the fallback is readable off the result."""
    dek = _package_dek()
    f = _pkg_finding(dek)
    prov, _g, out = _fallback_run(
        [{"status": "settled", "findings": [dict(f)]},
         {"status": "settled", "findings": [dict(f)]},
         dict(H.GROUND_CLEAN)],
        a_script=_a_script_no_reader(), b_script=_b_script())
    a, b = out["composition_attempts"]
    check("A's calls are recorded", (out["attempt_a_model_calls"] or 0) > 0, out)
    check("B's calls are recorded separately",
          (out["attempt_b_model_calls"] or 0) > 0
          and out["attempt_b_model_calls"] == b["model_calls_total"], out)
    check("neither attempt's own total includes the other's",
          a["model_calls_total"] == out["attempt_a_model_calls"]
          and a["model_calls_total"] != out["composition_model_calls_total"], out)
    check("the combined total is exactly the sum of the two",
          out["composition_model_calls_total"]
          == a["model_calls_total"] + b["model_calls_total"], out)
    check("B is cheaper than A, having reused upstream",
          b["model_calls_total"] < a["model_calls_total"],
          (a["model_calls_total"], b["model_calls_total"]))
    check("B made no LEDGER, WORTH or ARCHITECTURE call",
          all(b["model_calls_by_stage"].get(s, 0) == 0
              for s in (CP.LEDGER, CP.WORTH, CP.ARCHITECTURE)),
          b["model_calls_by_stage"])


def test_the_runner_persists_the_attempt_audit():
    """The A/B row reaches disk, so which article, package and gate verdicts belong to
    which attempt is answerable off the artifact."""
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d)
        RUNNER._persist_attempts(out, {
            "composition_attempts": [{"attempt": "A", "mode": CP.COMPOSE_NORMAL,
                                      "model_calls_total": 7},
                                     {"attempt": "B",
                                      "mode": CP.COMPOSE_SAFE_RECOMPOSE,
                                      "model_calls_total": 4}],
            "composition_attempts_count": 2, "attempt_a_model_calls": 7,
            "attempt_b_model_calls": 4, "composition_model_calls_total": 11,
            "fallback_recomposition_triggered": True,
            "fallback_recomposition_reason": "because", "winning_attempt": "B"})
        f = out / "COMPOSITION_ATTEMPTS.json"
        check("the runner writes COMPOSITION_ATTEMPTS.json", f.exists(),
              sorted(p.name for p in out.iterdir()))
        if not f.exists():
            return
        o = json.loads(f.read_text())
        check("it names both attempts and their modes",
              [x["attempt"] for x in o["composition_attempts"]] == ["A", "B"]
              and o["composition_attempts"][1]["mode"] == CP.COMPOSE_SAFE_RECOMPOSE, o)
        check("it separates the two costs and states the maximum",
              (o["attempt_a_model_calls"], o["attempt_b_model_calls"]) == (7, 4)
              and o["max_compositions_per_worth_pass_story"]
              == CP.MAX_COMPOSITION_ATTEMPTS, o)
    # A run that never fell back writes no row at all.
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d)
        RUNNER._persist_attempts(out, {})
        check("a run with no attempt record writes nothing",
              not (out / "COMPOSITION_ATTEMPTS.json").exists(), "")


def test_no_factual_standard_moved():
    """The fallback is a WRITING contract above the gates. Nothing about acceptance, the
    ledger's authority or any gate's threshold moved to make room for it."""
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    check("the safe contract adds to the writer prompt and replaces nothing",
          CP.WRITER_SYSTEM_SAFE_RECOMPOSE
          == CP.WRITER_SYSTEM + CP.SAFE_RECOMPOSE_DELTA, "")
    check("the Grounding fuse is unchanged",
          CP.GROUNDING_COMPLETION_MAX_ITERATIONS == 5, "")
    check("two compositions is the stated maximum", CP.MAX_COMPOSITION_ATTEMPTS == 2, "")
    body = src.split("def run_composition_with_fallback(")[1]
    for banned in ("uncertain_adjudicated", "blocking = ", "REPAIR_OPS",
                   "freeze_ledger(", "worth_gate(", "story_architecture(",
                   "research"):
        check("the orchestrator does not touch %s" % banned, banned not in body, "")
    elig = src.split("def fallback_recomposition_eligible(")[1].split("\ndef ")[0]
    check("eligibility asks no model anything",
          "provider" not in elig and "complete(" not in elig and "_ask(" not in elig, "")
    check("eligibility reads only the stage/reason record",
          "article_text" in elig and "reason_code" in elig
          and "failure_stage" in elig, "")


def main() -> int:
    for fn in (test_a_clean_pass_never_generates_a_second_composition,
               test_an_eligible_grounding_hold_generates_b_exactly_once,
               test_an_eligible_safety_hold_generates_b_exactly_once,
               test_every_eligible_composition_terminal_is_accepted,
               test_a_reader_hold_does_not_earn_a_recomposition,
               test_the_fallback_budget_is_spent_whichever_attempt_wins,
               test_the_run_reports_the_attempt_that_got_furthest,
               test_pre_composition_holds_are_never_eligible,
               test_eligibility_fails_closed_on_everything_it_does_not_recognise,
               test_b_inherits_frozen_authority_and_nothing_else,
               test_b_writer_gets_the_same_packet_but_the_safe_contract,
               test_as_prose_cannot_reach_bs_writer_call,
               test_b_produces_its_own_prose_and_its_own_package,
               test_b_runs_every_gate_and_keeps_as_artifacts,
               test_a_single_attempt_run_keeps_the_old_artifact_layout_exactly,
               test_only_the_winning_attempt_can_publish,
               test_a_held_b_is_terminal_and_there_is_no_third_composition,
               test_model_call_accounting_separates_the_two_attempts,
               test_the_runner_persists_the_attempt_audit,
               test_no_factual_standard_moved):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL TWO-COMPOSITION FALLBACK TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
