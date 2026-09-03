#!/usr/bin/env python3
"""
selector_v2_cutover_test.py -- Selector V2 as the authoritative selector.

Four natural shadow runs (30 Aug - 2 Sep 2026) showed the ranking is operationally
safe. They could not show what happens when its winner is actually used, because in
shadow mode nothing consumed it. That is what this file tests: the seed V2 chooses is
the seed the engine writes about, the existing attempt write-back still owns the
consequences, and a seed that has been used up does not come back tomorrow.

The failure contract is the other half. A selector that cannot select must HOLD
loudly, not quietly hand the day to the other selector -- a silent selector swap is
the kind of change nobody notices for a week.

No network, no provider: acquisition, the assessor and the engine are all injected.
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import material_policy as MP                              # noqa: E402
import news_fetcher as NF                                 # noqa: E402
import new_engine_production as NEP                       # noqa: E402
import selector_v2 as SV                                  # noqa: E402
from new_engine_v1.provider import Completion             # noqa: E402
from new_engine_v1_test import SOURCE, StubProvider       # noqa: E402
from research_pack_fixture import stub_pack               # noqa: E402

FAILURES: list = []
RICH_URL = "https://example.org/rich-single-subject"
THIN_URL = "https://example.org/thin-legacy-favourite"


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:240]))
    if not ok:
        FAILURES.append(label)


RICH = ("The council report records that a blind, pale, worm-like fish was filmed in a "
        "flooded cave near Lugh in 2026 by a diver. Dr Elena Marris of the University "
        "of Bologna identified it as a possible new species. The cave was surveyed "
        "twice, in 1974 and 2011, and neither survey recorded the animal.\n\n"
        + "Detail follows about the survey record and the aquifer. " * 90)
THIN = SOURCE + "\n\n" + ("Filler paragraph about the crossing. " * 80)
BODIES = {RICH_URL: RICH, THIN_URL: THIN}


class Assessor:
    """Answers every candidate; the rich body reads strong, everything else thin."""

    def __init__(self, raise_on_call=False):
        self.raise_on_call = raise_on_call
        self.calls = 0
        self.deadlines = []

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                 deadline=None):
        self.deadlines.append(deadline)
        self.calls += 1
        if self.raise_on_call:
            raise RuntimeError("stub: assessment provider failure")
        out = []
        for block in user.split("ID: ")[1:]:
            cid = block.split("\n", 1)[0].strip()
            body = block.split("<<<BODY\n", 1)[1].split("\nBODY>>>")[0]
            quote = " ".join(body.split()[:9])
            rich = "Phreatichthys" in body or "worm-like fish" in body
            out.append({"id": cid, "concrete_subject": "the thing itself",
                        "subject_anchor_quote": quote,
                        "investigable_question": "what is left open",
                        "question_basis_quote": quote,
                        "material_richness": "RICH" if rich else "THIN",
                        "researchability": "HIGH" if rich else "LOW",
                        "narrative_material": "HIGH", "source_shape": "SINGLE_SUBJECT",
                        "specificity": "HIGH",
                        "assessment": "STRONG_CANDIDATE" if rich else "WEAK_CANDIDATE",
                        "reason": "because the body says so"})
        return Completion(text=json.dumps({"assessments": out}), requested_model="m",
                          actual_model="m", provider_label="stub")


def _db(path, seeds):
    conn = sqlite3.connect(str(path))
    NF.init_db(conn)
    for col in ("ce_attempt_terminal INTEGER DEFAULT 0", "ce_retry_after TEXT",
                "ce_attempted_date TEXT", "ce_attempt_run TEXT",
                "ce_attempt_outcome TEXT", "ce_pack_verdict TEXT",
                "ce_pack_subject_words INTEGER"):
        try:
            conn.execute("ALTER TABLE news_seeds ADD COLUMN %s" % col)
        except sqlite3.OperationalError:
            pass
    day = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    for sid, url, title, pub, score, angle in seeds:
        conn.execute(
            "INSERT INTO news_seeds (id,url,title,summary,source_name,source_tier,"
            "pub_date,fetched_date,relevance_score,themes,disability_angle,used,"
            "material_class) VALUES (?,?,?,?,?,1,?,?,?,'[]',?,0,?)",
            (sid, url, title, title, pub, day, day, score, angle, MP.CULTURE))
    conn.commit()
    conn.close()
    return path


# The legacy selector prefers the THIN seed: higher score AND an angle, which is
# exactly the ordering the four observed runs showed separating nothing useful.
SEEDS = [("rich-seed", RICH_URL, "A blind cave fish filmed near Lugh", "Nautilus",
          0.30, None),
         ("thin-seed", THIN_URL, "A council crossing report", "Council Wire",
          0.90, "an angle")]


class FakeOrch:
    """The production orchestrator's surface as run_scheduled uses it."""

    def __init__(self, db):
        self.logger = logging.getLogger("selector_v2_cutover_test")
        self.logger.addHandler(logging.NullHandler())
        self.logger.propagate = False
        self.drafts_dir = pathlib.Path(tempfile.mkdtemp())
        self.discovery_db = db
        self.fetched: list = []
        self.seed_attempts: list = []
        self.legacy_calls = 0
        self.get_news_seed_calls = 0
        self.dead_sources = False

    # -- legacy selector, untouched and still reachable --
    def get_news_seed(self, exclude_ids=None):
        self.get_news_seed_calls += 1
        conn = sqlite3.connect(str(self.discovery_db))
        conn.row_factory = sqlite3.Row
        r = conn.execute(
            "SELECT * FROM news_seeds WHERE used = 0 AND ce_attempt_terminal IS NOT 1 "
            "ORDER BY disability_angle IS NULL, relevance_score DESC LIMIT 1").fetchone()
        conn.close()
        return None if r is None else {k: r[k] for k in r.keys()}

    def get_news_seed_with_usable_source(self, max_attempts=3, exclude_ids=None):
        self.legacy_calls += 1
        return self.get_news_seed()

    # -- acquisition --
    def get_source_text(self, url, fallback_text=None, underlying_url=None):
        self.fetched.append(url)
        if self.dead_sources:
            return ""
        return BODIES.get(url, THIN)

    def get_source_origin(self, url):
        return "fetched_article"

    def get_source_original_length(self, url):
        return len(BODIES.get(url, THIN))

    def get_source_paragraph_count(self, url):
        return 6

    @staticmethod
    def classify_source_acquisition(text, origin, paragraph_count=None):
        return ("USABLE", "ok") if text else ("SOURCE_ACQUISITION_FAILED", "empty")

    # -- the existing authoritative write-back, modelled honestly --
    def classify_current_engine_attempt(self, result):
        return ("TERMINAL", result.get("decision", "HOLD"))

    def mark_news_seed_current_engine_attempt(self, seed_id, *, run, klass, outcome,
                                              **kw):
        self.seed_attempts.append(seed_id)
        conn = sqlite3.connect(str(self.discovery_db))
        conn.execute("UPDATE news_seeds SET ce_attempt_terminal = 1, "
                     "ce_attempted_date = ?, ce_attempt_run = ?, ce_attempt_outcome = ? "
                     "WHERE id = ?",
                     (datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), run,
                      "%s:%s" % (klass, outcome), seed_id))
        conn.commit()
        conn.close()


def _run(selector=None, *, assessor=None, engine_kwargs=None, seeds=SEEDS, db=None,
         dead_sources=False):
    db = db or _db(pathlib.Path(tempfile.mkdtemp()) / "disability_findings.db", seeds)
    orch = FakeOrch(db)
    orch.dead_sources = dead_sources
    assessor = assessor or Assessor()
    for k in (SV.SELECTOR_ENV, SV.SHADOW_ENV):
        os.environ.pop(k, None)
    if selector is not None:
        os.environ[SV.SELECTOR_ENV] = selector
    os.environ["NEW_ENGINE_V1_MODE"] = "LIVE"
    real_provider = NEP.Provider
    NEP.Provider = lambda model=None, **kw: (
        assessor if getattr(NEP, "_in_selector", False)
        else StubProvider(**(engine_kwargs or {})))
    real_select = NEP._select_seed

    def selecting(*a, **kw):
        NEP._in_selector = True
        try:
            return real_select(*a, **kw)
        finally:
            NEP._in_selector = False
    NEP._select_seed = selecting
    try:
        result = NEP.run_scheduled(orch, evidence_root=tempfile.mkdtemp(),
                                   research_fn=stub_pack)
    finally:
        NEP.Provider = real_provider
        NEP._select_seed = real_select
        NEP._in_selector = False
        os.environ.pop(SV.SELECTOR_ENV, None)
        os.environ.pop("NEW_ENGINE_V1_MODE", None)
    return result, orch, db, assessor


def _seed_row(db, seed_id):
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    r = conn.execute("SELECT * FROM news_seeds WHERE id=?", (seed_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


# ── A: the V2 winner is the seed the engine writes about ─────────────────────
def test_the_v2_winner_is_the_seed_passed_downstream():
    check("V2 is authoritative by default", SV.resolve_selector() == SV.SELECTOR_V2)
    result, orch, db, assessor = _run()
    check("the run reached the engine", result["status"] in ("accept", "hold"), result)
    check("the anchor is V2's winner, not the legacy favourite",
          result["source_url"] == RICH_URL, result.get("source_url"))
    check("the legacy selector was never consulted for the anchor",
          orch.legacy_calls == 0, orch.legacy_calls)
    check("the legacy favourite was the higher-scoring seed with the angle",
          _seed_row(db, "thin-seed")["relevance_score"] == 0.90)
    if result.get("candidate"):
        cand = pathlib.Path(result["candidate"]).read_text()
        check("the candidate carries the V2 anchor", RICH_URL in cand)


# ── B: the existing write-back owns the consequences ─────────────────────────
def test_the_selected_seed_goes_through_the_existing_write_back():
    result, orch, db, assessor = _run()
    check("exactly one seed was written back", orch.seed_attempts == ["rich-seed"],
          orch.seed_attempts)
    row = _seed_row(db, "rich-seed")
    check("ce_attempt_run names this run", row["ce_attempt_run"] == result["engine_run"],
          row["ce_attempt_run"])
    check("ce_attempt_outcome was written", bool(row["ce_attempt_outcome"]),
          row["ce_attempt_outcome"])
    prod = (HERE / "new_engine_production.py").read_text()
    writeback = prod.split("def _record_seed_attempt")[1].split("\ndef ")[0]
    check("the write-back, not the selector, calls the orchestrator's seed methods",
          "mark_news_seed_current_engine_attempt" in writeback
          and "classify_current_engine_attempt" in writeback)
    check("the selector calls neither",
          "mark_news_seed" not in (HERE / "selector_v2.py").read_text())


# ── C: a consumed seed does not simply win again tomorrow ────────────────────
def test_a_terminal_v2_seed_leaves_the_pool():
    """Shadow mode could never exercise this: nothing consumed V2's winner, so the
    day-two behaviour was untested. The eligible pool filters on the same columns
    the write-back sets, so consumption should be automatic -- proven, not assumed."""
    result, orch, db, assessor = _run()
    check("day one chose the rich seed", result["source_url"] == RICH_URL)
    row = _seed_row(db, "rich-seed")
    check("day one marked it terminal", row["ce_attempt_terminal"] == 1, row)

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    pool = [r["id"] for r in SV.eligible_pool(conn, datetime.now())]
    conn.close()
    check("it is gone from the eligible pool", "rich-seed" not in pool, pool)
    check("the other seed is still there", "thin-seed" in pool, pool)

    # day two, same database
    result2, orch2, db2, _ = _run(db=db)
    check("day two cannot choose it again", result2.get("source_url") != RICH_URL,
          result2.get("source_url"))
    check("day two chose the remaining seed or found none",
          result2.get("source_url") in (THIN_URL, None), result2.get("source_url"))


# ── D: the assessment layer writes nothing authoritative ─────────────────────
def test_the_selector_writes_no_authoritative_state():
    COLS = ("SELECT id, used, used_date, disability_angle, angle_checked, "
            "ce_attempt_terminal, ce_attempted_date, ce_attempt_outcome "
            "FROM news_seeds ORDER BY id")
    seen = {}
    real = SV.run_shadow

    def bracketing(conn, *a, **kw):
        seen["before"] = [tuple(r) for r in conn.execute(COLS)]
        try:
            return real(conn, *a, **kw)
        finally:
            seen["after"] = [tuple(r) for r in conn.execute(COLS)]
    SV.run_shadow = bracketing
    SV.run_selection = bracketing
    try:
        _run()
    finally:
        SV.run_shadow = real
        SV.run_selection = real
    check("the selector ran", "before" in seen and "after" in seen)
    check("news_seeds is identical across the selection",
          seen.get("before") == seen.get("after"), (seen.get("before"), seen.get("after")))
    src = (HERE / "selector_v2.py").read_text()
    for banned in ("UPDATE news_seeds", "INSERT INTO news_seeds", "mark_news_seed",
                   "disability_angle ="):
        check("selector_v2 never writes %r" % banned, banned not in src)


# ── E: explicit legacy rollback ──────────────────────────────────────────────
def test_legacy_rollback_selects_through_the_old_path():
    result, orch, db, assessor = _run(selector="legacy")
    check("the legacy selector was used", orch.legacy_calls == 1, orch.legacy_calls)
    check("the anchor is the legacy favourite", result["source_url"] == THIN_URL,
          result.get("source_url"))
    check("no assessment call was spent", assessor.calls == 0, assessor.calls)
    conn = sqlite3.connect(str(db))
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    check("no selector table was created under rollback",
          SV.TABLE not in tables and SV.RUNS_TABLE not in tables, tables)
    check("the legacy selector source is unmodified by this PR",
          "def get_news_seed_with_usable_source" in
          (HERE / "orchestrator" / "discovery.py").read_text())


# ── F: fail closed ───────────────────────────────────────────────────────────
def test_a_selector_failure_holds_and_does_not_fall_back():
    # a genuine technical failure
    real = SV.run_selection
    SV.run_selection = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("db is gone"))
    try:
        result2, orch2, db2, _ = _run()
    finally:
        SV.run_selection = real
    check("a technical failure HOLDs", result2["status"] == "hold", result2["status"])
    check("with a selector reason code",
          result2.get("reason_code") == "SELECTOR_FAILURE", result2.get("reason_code"))
    check("and is visible to the operator as an infra failure",
          (result2.get("run_status") or {}).get("status") == "PROVIDER_FAILURE",
          result2.get("run_status"))
    check("it did NOT fall back to the legacy selector",
          orch2.legacy_calls == 0, orch2.legacy_calls)
    check("no seed was written back on a failed selection",
          orch2.seed_attempts == [], orch2.seed_attempts)

    import production_orchestrator as PO
    check("the scheduled wrapper will exit non-zero",
          PO._is_infra_or_contract_failure(result2) is True)

    # an unknown selector value refuses rather than guessing
    os.environ[SV.SELECTOR_ENV] = "v3"
    try:
        SV.resolve_selector()
        check("an unknown selector value raises", False, "it returned")
    except SV.UnknownSelector:
        check("an unknown selector value raises", True)
    finally:
        os.environ.pop(SV.SELECTOR_ENV, None)


# ── G, H, I: budgets, cache, repetition ──────────────────────────────────────
def test_the_hard_budgets_are_unchanged_by_the_cutover():
    check("run budget still 120s", SV.RUN_BUDGET_SECONDS == 120)
    check("acquisition sub-budget still 75s", SV.ACQUISITION_BUDGET_SECONDS == 75)
    check("sub-budget still contained by the total",
          SV.ACQUISITION_BUDGET_SECONDS + 40 <= SV.RUN_BUDGET_SECONDS)
    check("call ceiling still 10", SV.MAX_CALLS_PER_RUN == 10)
    check("one candidate per call", SV.BATCH_SIZE == 1)
    check("exposure still 6/4/2", (SV.STREAM_THEME, SV.STREAM_URGENCY,
                                   SV.STREAM_EXPLORE) == (6, 4, 2))
    _, _, _, assessor = _run()
    check("the authoritative call carries the run deadline",
          assessor.deadlines and assessor.deadlines[0] is not None, assessor.deadlines)


def test_the_cache_still_works_authoritatively():
    db = _db(pathlib.Path(tempfile.mkdtemp()) / "disability_findings.db", SEEDS)
    _, _, _, a1 = _run(db=db)
    first = a1.calls
    check("the first run paid for its assessments", first >= 1, first)
    # reset the attempt so the same seeds are eligible again with unchanged bytes
    conn = sqlite3.connect(str(db))
    conn.execute("UPDATE news_seeds SET ce_attempt_terminal = 0, ce_attempted_date = NULL")
    conn.commit()
    conn.close()
    _, _, _, a2 = _run(db=db)
    check("the second run was served from cache", a2.calls == 0, a2.calls)
    conn = sqlite3.connect(str(db))
    n = conn.execute("SELECT count(*) FROM %s" % SV.TABLE).fetchone()[0]
    conn.close()
    check("assessments are still keyed by (seed_id, source sha)", n == len(SEEDS), n)


def test_publisher_repetition_is_still_soft():
    src = (HERE / "selector_v2.py").read_text()
    check("penalty is bounded and decays", SV.PUBLISHER_PENALTY_MAX == 0.30
          and SV.PUBLISHER_PENALTY_DAYS == 7)
    check("it is a number in the sort, never an exclusion",
          'r["publisher_penalty"]' in src and "publisher_penalty" not in
          src.split("def eligible_pool")[1].split("def recent_selections")[0])
    # Asserted on the mechanism, not the vocabulary: the words "ban" and "quota"
    # appear in the docstring that promises there is neither, and a substring scan
    # would fail on the very sentence stating the property.
    rank = src.split("def rank(")[1].split("\n\n\n")[0]
    check("the penalty only enters the sort", 'r["publisher_penalty"]' in rank)
    check("nothing filters or excludes on it",
          not [l for l in src.splitlines()
               if "publisher_penalty" in l
               and any(k in l for k in ("continue", "if ", "WHERE", "filter", "skip"))])
    check("it is dominated by the material keys, which sort first",
          rank.index('_ORDER["assessment"]') < rank.index('r["publisher_penalty"]')
          if '_ORDER["assessment"]' in rank else True)


# ── J: nothing downstream changed ────────────────────────────────────────────
def test_no_downstream_stage_changed():
    import subprocess
    out = subprocess.run(["git", "diff", "--name-only", "origin/main"],
                         cwd=str(HERE.parent), capture_output=True, text=True).stdout
    changed = [f for f in out.split() if f.strip()]
    # NOTE (2026-09-03): this is a WORKING-TREE scope guard, not an engine invariant --
    # it diffs against a moving origin/main, so every PR after the cutover has to declare
    # its own files here or the check fires. That makes it self-invalidating, and it is
    # the reason this file appears in a provenance-bugfix PR at all. Left in place rather
    # than deleted, because whether the guard should become per-PR or go away is the
    # owner's call; see the PR description.
    allowed = {"automation/selector_v2.py", "automation/new_engine_production.py",
               "automation/selector_v2_cutover_test.py",
               "automation/selector_v2_runtime_hook_test.py",
               "automation/cutover_validation_test.py",
               "automation/new_engine_v1_test.py",
               ".claude/WORK.md", ".claude/LOGBOOK.md",
               # the research_pack_provenance false-positive fix (2026-09-03): the
               # stray-source detector read whole source bodies as scaffolding.
               "automation/publication_safety_bridge.py",
               "automation/research_pack_test.py"}
    stray = [f for f in changed if f not in allowed]
    check("only the selector and declared bugfix scope changed", not stray, stray)
    # The engine STAGES the cutover must never have touched. The bridge is no longer in
    # this list: it is deliberately changed by the provenance bugfix, and its call site
    # invariance is asserted below instead.
    for untouched in ("automation/new_engine_v1/research.py",
                      "automation/new_engine_v1/stages.py",
                      "automation/new_engine_v1/decision.py",
                      "automation/new_engine_v1/runner.py",
                      "automation/orchestrator/discovery.py"):
        check("unchanged: %s" % untouched.split("/")[-1], untouched not in changed)
    src = (HERE / "new_engine_production.py").read_text()
    body = src.split("def run_scheduled(")[1]
    check("the engine call is unchanged", "out = R.run(payload, root, Provider(model=model), run" in body)
    check("the bridge call is unchanged", "bridge = BRIDGE.evaluate(out, fact_check_fn=_strict_fc)" in body)



# ── the authoritative path must not run the selector it replaced ─────────────
def test_authoritative_mode_never_runs_the_legacy_selector():
    """Not even to fill in a diagnostic. get_news_seed acquires nothing and changes no
    row, but it opens a writable connection and commits idempotent schema DDL, and the
    replaced selector has no business executing in the path that replaced it."""
    result, orch, db, assessor = _run()
    check("get_news_seed_with_usable_source was not called", orch.legacy_calls == 0,
          orch.legacy_calls)
    check("plain get_news_seed was not called either", orch.get_news_seed_calls == 0,
          orch.get_news_seed_calls)
    check("only the V2 winner's source was ever fetched",
          set(orch.fetched) <= set(BODIES), orch.fetched)
    prod = (HERE / "new_engine_production.py").read_text()
    sel = prod.split("def _select_seed")[1].split("\ndef ")[0]
    auth = sel.split("if not SV.v2_is_authoritative():")[1].split("return orch.get_news_seed_with_usable_source(), None")[1]
    # Code, not prose: the branch carries a comment explaining why it does not call
    # get_news_seed, and a scan that fails on its own explanation tests nothing.
    auth_code = "\n".join(l for l in auth.splitlines() if not l.strip().startswith("#"))
    for banned in ("get_news_seed", "mark_news_seed", "source_unusable", "acquire("):
        check("the authoritative branch never calls %r" % banned,
              banned not in auth_code, [l.strip() for l in auth_code.splitlines()
                                        if banned in l])
    check("no legacy counterfactual helper remains",
          "_legacy_would_have_chosen" not in prod)
    check("the authoritative selection records no old winner", "old_winner=None" in sel)

    # and the row it does write is still useful for inspecting the first live runs
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM %s" % SV.RUNS_TABLE)]
    conn.close()
    check("one diagnostic row for the run", len(rows) == 1, len(rows))
    if rows:
        r = rows[0]
        check("it names the run", r["run_id"] == result["engine_run"])
        check("it records what V2 chose and why",
              r["shadow_seed_id"] == "rich-seed" and r["shadow_assessment"]
              and r["shadow_explanation"], r["shadow_seed_id"])
        check("it records the work done",
              r["candidates"] and r["fetched"] is not None
              and r["model_calls"] is not None, r["candidates"])
        check("and no legacy counterfactual is claimed", r["old_seed_id"] is None,
              r["old_seed_id"])



# ── the silence that is an outage, not a quiet day ───────────────────────────
def test_a_total_assessment_failure_is_an_infrastructure_failure():
    """assess() catches provider errors per batch and records ASSESSMENT_ERROR, so a
    complete assessment outage produces no winner and looks, from outside, exactly
    like a day with nothing worth writing about. It is not. We had the pool and could
    not judge it, and reporting that as no-usable-source would make a broken day look
    like a quiet one."""
    result, orch, db, assessor = _run(assessor=Assessor(raise_on_call=True))
    check("every assessment call failed", assessor.calls >= 1, assessor.calls)
    check("sources WERE acquired", len(orch.fetched) >= 1, orch.fetched)
    check("the run HOLDs", result["status"] == "hold", result["status"])
    check("as SELECTOR_FAILURE, not no_usable_source",
          result.get("reason_code") == "SELECTOR_FAILURE", result.get("reason_code"))
    check("the reason says the pool could not be judged",
          "could not be judged" in " ".join(result.get("reasons") or []),
          result.get("reasons"))
    check("visible to the wrapper as an infrastructure failure",
          (result.get("run_status") or {}).get("status") == "PROVIDER_FAILURE",
          result.get("run_status"))
    import production_orchestrator as PO
    check("the scheduled wrapper exits non-zero",
          PO._is_infra_or_contract_failure(result) is True)
    check("no legacy selector call", orch.legacy_calls == 0 and orch.get_news_seed_calls == 0,
          (orch.legacy_calls, orch.get_news_seed_calls))
    check("no seed attempt write-back", orch.seed_attempts == [], orch.seed_attempts)


def test_an_invalid_assessment_contract_is_also_technical():
    """Not only a raising provider: output that breaks its own contract leaves the same
    silence and must be classified the same way."""

    class Malformed(Assessor):
        def complete(self, system, user, max_tokens=3000, timeout=180,
                     temperature=None, deadline=None):
            self.calls += 1
            return Completion(text="not json at all", requested_model="m",
                              actual_model="m", provider_label="stub")

    result, orch, db, _ = _run(assessor=Malformed())
    check("malformed model output HOLDs as SELECTOR_FAILURE",
          result.get("reason_code") == "SELECTOR_FAILURE", result.get("reason_code"))
    check("no legacy fallback", orch.legacy_calls == 0 and orch.get_news_seed_calls == 0)


def test_no_material_at_all_is_an_ordinary_day():
    """The other side of the same rule: when nothing was acquired there is nothing to
    judge, and that IS an editorial no-usable-source day."""
    # every source unreadable
    result, orch, db, assessor = _run(dead_sources=True)
    check("acquisition was attempted", len(orch.fetched) >= 1, orch.fetched)
    check("no assessment was spent on unusable material", assessor.calls == 0,
          assessor.calls)
    check("all-acquisitions-unusable is no_usable_source",
          result["status"] == "no_usable_source", result["status"])
    check("not an infrastructure failure", "run_status" not in result, result.keys())

    # empty eligible pool: every seed already terminal
    db2 = _db(pathlib.Path(tempfile.mkdtemp()) / "disability_findings.db", SEEDS)
    conn = sqlite3.connect(str(db2))
    conn.execute("UPDATE news_seeds SET ce_attempt_terminal = 1")
    conn.commit()
    conn.close()
    result2, orch2, _, assessor2 = _run(db=db2)
    check("an empty pool is no_usable_source",
          result2["status"] == "no_usable_source", result2["status"])
    check("nothing was fetched", orch2.fetched == [], orch2.fetched)
    check("nothing was assessed", assessor2.calls == 0, assessor2.calls)
    check("still no infrastructure failure", "run_status" not in result2, result2.keys())


def test_a_valid_assessment_always_yields_a_winner():
    """'Valid assessments complete but no winner' is impossible by contract: rank()
    orders every OK record ahead of the rest and the winner is the first OK record, so
    one valid assessment is one winner. This is asserted so the claim cannot rot."""
    src = (HERE / "selector_v2.py").read_text()
    check("the winner is simply the first OK record",
          'winner = next((r for r in ranked if r["assessment_status"] == OK), None)'
          in src)
    check("rank puts every OK record first",
          'ok = [r for r in records if r["assessment_status"] == OK]' in src
          and 'return ok + [r for r in records if r["assessment_status"] != OK]' in src)
    result, orch, db, assessor = _run()
    check("a run with valid assessments has a winner",
          result.get("source_url") == RICH_URL, result.get("source_url"))


def main():
    for fn in (test_the_v2_winner_is_the_seed_passed_downstream,
               test_the_selected_seed_goes_through_the_existing_write_back,
               test_a_terminal_v2_seed_leaves_the_pool,
               test_the_selector_writes_no_authoritative_state,
               test_legacy_rollback_selects_through_the_old_path,
               test_a_selector_failure_holds_and_does_not_fall_back,
               test_the_hard_budgets_are_unchanged_by_the_cutover,
               test_the_cache_still_works_authoritatively,
               test_publisher_repetition_is_still_soft,
               test_a_total_assessment_failure_is_an_infrastructure_failure,
               test_an_invalid_assessment_contract_is_also_technical,
               test_no_material_at_all_is_an_ordinary_day,
               test_a_valid_assessment_always_yields_a_winner,
               test_authoritative_mode_never_runs_the_legacy_selector,
               test_no_downstream_stage_changed):
        print("\n" + fn.__name__)
        fn()
    for k in (SV.SELECTOR_ENV, SV.SHADOW_ENV, "NEW_ENGINE_V1_MODE"):
        os.environ.pop(k, None)
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL SELECTOR V2 CUTOVER TESTS PASSED")


if __name__ == "__main__":
    main()
