#!/usr/bin/env python3
"""
selector_v2_runtime_hook_test.py -- the shadow's one production call site.

selector_v2.py could be perfectly isolated and still be worthless: at PR #49's previous
head no production code path invoked it at all, so it produced no comparisons and the
question it was built to answer -- would reading the source have chosen a different
story? -- stayed unanswered.

This file tests the hook that fixes that, and only the hook. Two properties matter more
than anything the shadow decides:

  * with CRIPMINDS_SELECTOR_V2_SHADOW unset there is NO fetch, NO model call and NO
    table -- the flag is the whole gate;
  * with it set, the seed the real pipeline used is bit-identical before and after, the
    shadow's disagreement is recorded rather than acted on, and any failure inside the
    shadow leaves the authoritative run exactly as it would have been.

And one property that is easy to get wrong and impossible to notice afterwards: BOTH
selectors must rank the SAME eligible pool. The seed write-back retires or rests the
anchor it is given, and those are eligibility filters -- so a shadow that runs after it
ranks a universe the authoritative winner has already been removed from, and can never
report agreement. A comparison that cannot say "the same" is not a comparison. The
same-winner regression below exists precisely to fail if the hook drifts back.

No network, no live article: the engine provider, the research pack and source
acquisition are all injected.
"""
from __future__ import annotations

import copy
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

AUTHORITATIVE_URL = "https://example.org/authoritative-anchor"
SHADOW_URL = "https://example.org/shadow-would-have-picked"


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:240]))
    if not ok:
        FAILURES.append(label)


# ── source bodies, never fetched ──────────────────────────────────────────────
RICH_BODY = (
    "The Nautilus reported that a blind, pale, worm-like fish was filmed in a flooded "
    "cave near Lugh in 2026 by a diver who posted the footage to TikTok. Dr Elena "
    "Marris of the University of Bologna identified it as a possible new species of "
    "Phreatichthys. The cave system has been surveyed twice, in 1974 and 2011, and "
    "neither survey recorded the animal. Marris says the specimen has not been "
    "collected and no tissue sample exists.\n\nThe aquifer feeds three towns.\n\n"
    + "Detail follows about the survey record and the aquifer. " * 90)

BODIES = {AUTHORITATIVE_URL: SOURCE + "\n\n" + ("Filler paragraph. " * 80),
          SHADOW_URL: RICH_BODY}


class _AssessmentProvider:
    """Stands in for the assessor the shadow calls. Answers every candidate, so the
    shadow reaches a winner and the comparison is a real one."""

    def __init__(self, raise_on_call=False, prefer="Phreatichthys"):
        self.raise_on_call = raise_on_call
        self.prefer = prefer            # the body marker that reads RICH
        self.calls = 0
        self.deadlines = []

    def complete(self, system, user, max_tokens=3000, timeout=180,
                 temperature=None, deadline=None):
        self.deadlines.append(deadline)
        self.calls += 1
        if self.raise_on_call:
            raise RuntimeError("stub: assessment provider failure")
        out = []
        for block in user.split("ID: ")[1:]:
            cid = block.split("\n", 1)[0].strip()
            body = block.split("<<<BODY\n", 1)[1].split("\nBODY>>>")[0]
            quote = " ".join(body.split()[:9])
            rich = "RICH" if self.prefer in body else "THIN"
            verdict = ("STRONG_CANDIDATE" if rich == "RICH" else "WEAK_CANDIDATE")
            out.append({"id": cid, "concrete_subject": "the thing itself",
                        "subject_anchor_quote": quote,
                        "investigable_question": "what is left open",
                        "question_basis_quote": quote, "material_richness": rich,
                        "researchability": "HIGH" if rich == "RICH" else "LOW",
                        "narrative_material": "HIGH", "source_shape": "SINGLE_SUBJECT",
                        "specificity": "HIGH", "assessment": verdict,
                        "reason": "because the body says so"})
        return Completion(text=json.dumps({"assessments": out}), requested_model="m",
                          actual_model="m", provider_label="stub")


# ── a seed database the shadow can read ───────────────────────────────────────
def _seed_db(path: pathlib.Path, competitor=True):
    """Two eligible seeds by default: the authoritative one the fake orchestrator hands
    to the engine, and a second one the assessor is told to prefer, so the shadow
    disagrees. With competitor=False only the authoritative seed is eligible, so the
    shadow can only agree -- if it is looking at the pool at the right moment."""
    conn = sqlite3.connect(str(path))
    NF.init_db(conn)
    for col in ("ce_attempt_terminal INTEGER DEFAULT 0", "ce_retry_after TEXT",
                "ce_attempted_date TEXT"):
        try:
            conn.execute("ALTER TABLE news_seeds ADD COLUMN %s" % col)
        except sqlite3.OperationalError:
            pass
    day = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    rows = [("auth-seed", AUTHORITATIVE_URL, "A council crossing report", "Council Wire",
             0.90),
            ("shadow-seed", SHADOW_URL, "A blind cave fish filmed near Lugh", "Nautilus",
             0.15)]
    if not competitor:
        rows = rows[:1]
    for sid, url, title, pub, score in rows:
        conn.execute(
            "INSERT INTO news_seeds (id,url,title,summary,source_name,source_tier,"
            "pub_date,fetched_date,relevance_score,themes,disability_angle,used,"
            "material_class) VALUES (?,?,?,?,?,1,?,?,?,'[]',NULL,0,?)",
            (sid, url, title, title, pub, day, day, score, MP.CULTURE))
    conn.commit()
    conn.close()
    return path


def _seed_snapshot(db):
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM news_seeds ORDER BY id")]
    conn.close()
    return rows


class FakeOrch:
    """The production orchestrator's surface, as `run_scheduled` uses it. Records every
    acquisition so a test can prove what was and was not fetched."""

    def __init__(self, db):
        self.logger = logging.getLogger("selector_v2_runtime_hook_test")
        self.logger.addHandler(logging.NullHandler())
        self.drafts_dir = pathlib.Path(tempfile.mkdtemp())
        self.discovery_db = db
        self.fetched: list = []
        self.seed_attempts: list = []

    # -- the authoritative selection, unchanged by anything in this PR --
    def get_news_seed_with_usable_source(self):
        return {"id": "auth-seed", "url": AUTHORITATIVE_URL,
                "title": "A council crossing report", "source_name": "Council Wire",
                "relevance_score": 0.90, "summary": "s"}

    # -- source acquisition, the one path the shadow is required to reuse --
    def get_source_text(self, url, fallback_text=None, underlying_url=None):
        self.fetched.append(url)
        return BODIES.get(url, SOURCE)

    def get_source_origin(self, url):
        return "fetched_article"

    def get_source_original_length(self, url):
        return len(BODIES.get(url, SOURCE))

    def get_source_paragraph_count(self, url):
        return 4

    @staticmethod
    def classify_source_acquisition(text, origin, paragraph_count=None):
        return ("USABLE", "ok") if text else ("SOURCE_ACQUISITION_FAILED", "empty")

    # -- seed write-back, which must still happen and only for the real anchor --
    def classify_current_engine_attempt(self, result):
        return ("editorial", result.get("decision", "HOLD"))

    def mark_news_seed_current_engine_attempt(self, seed_id, **kw):
        """Production retires or rests the seed here (PR #46). Modelled honestly rather
        than merely recorded: the whole point of the hook's position is that this write
        happens AFTER the shadow has read the pool, so a fixture that only appended to a
        list could not tell the two orderings apart."""
        self.seed_attempts.append(seed_id)
        conn = sqlite3.connect(str(self.discovery_db))
        conn.execute("UPDATE news_seeds SET ce_attempt_terminal = 1, "
                     "ce_attempted_date = ? WHERE id = ?",
                     (datetime.now().strftime("%Y-%m-%d"), seed_id))
        conn.commit()
        conn.close()


class _ResearchRecorder:
    """The Research Pack. Records the anchor it was asked about, so a test can prove the
    shadow never commissioned research for the story it preferred."""

    def __init__(self):
        self.anchors: list = []

    def __call__(self, provider, *, anchor, now_iso, **kw):
        self.anchors.append(anchor)
        return stub_pack(provider, anchor=anchor, now_iso=now_iso, **kw)


def _run(flag: str | None, *, assessor=None, hook_raises=False, engine_kwargs=None,
         competitor=True, on_shadow=None):
    """One full run_scheduled, with the engine provider and the shadow's assessor both
    injected. Returns (result, orch, db, assessor, research recorder)."""
    db = _seed_db(pathlib.Path(tempfile.mkdtemp()) / "disability_findings.db",
                  competitor=competitor)
    orch = FakeOrch(db)
    research = _ResearchRecorder()
    assessor = assessor or _AssessmentProvider()

    os.environ.pop(SV.SHADOW_ENV, None)
    if flag is not None:
        os.environ[SV.SHADOW_ENV] = flag
    os.environ["NEW_ENGINE_V1_MODE"] = "LIVE"
    # The shadow hook exists only while the legacy selector is authoritative. Once
    # V2 selects, the hook self-disables rather than running a second selection --
    # see selector_v2_cutover_test.py for that. These tests describe the hook.
    os.environ["CRIPMINDS_SELECTOR"] = "legacy"

    real_provider, real_run_shadow = NEP.Provider, SV.run_shadow
    NEP.Provider = lambda model=None, **kw: (
        assessor if getattr(NEP, "_in_shadow", False)
        else StubProvider(**(engine_kwargs or {})))

    # The engine and the shadow both build a Provider; the flag below distinguishes
    # them without touching either module's real construction path.
    real_hook = NEP._selector_v2_shadow

    def hook(*a, **kw):
        NEP._in_shadow = True
        if on_shadow is not None:
            on_shadow(db)                 # observe the pool AS THE SHADOW SEES IT
        try:
            return real_hook(*a, **kw)
        finally:
            NEP._in_shadow = False
    NEP._selector_v2_shadow = hook

    if hook_raises:
        SV.run_shadow = lambda *a, **kw: (_ for _ in ()).throw(
            RuntimeError("shadow exploded"))
    try:
        result = NEP.run_scheduled(orch, evidence_root=tempfile.mkdtemp(),
                                   research_fn=research)
    finally:
        NEP.Provider = real_provider
        SV.run_shadow = real_run_shadow
        NEP._selector_v2_shadow = real_hook
        NEP._in_shadow = False
        os.environ.pop(SV.SHADOW_ENV, None)
        os.environ.pop("NEW_ENGINE_V1_MODE", None)
        os.environ.pop("CRIPMINDS_SELECTOR", None)
    return result, orch, db, assessor, research


def _shadow_runs(db):
    conn = sqlite3.connect(str(db))
    try:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute("SELECT * FROM %s" % SV.RUNS_TABLE)]
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()


def _tables(db):
    conn = sqlite3.connect(str(db))
    t = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    return t


# ── 1. flag OFF ───────────────────────────────────────────────────────────────
def test_flag_off_the_hook_does_nothing():
    calls = []
    real = SV.run_shadow
    SV.run_shadow = lambda *a, **kw: calls.append(1)
    try:
        result, orch, db, assessor, research = _run(None)
    finally:
        SV.run_shadow = real
    check("the run completed", result["status"] in ("accept", "hold"), result)
    check("run_shadow was never called", calls == [], calls)
    check("no model call was spent on assessment", assessor.calls == 0)
    check("only the authoritative source was fetched",
          set(orch.fetched) == {AUTHORITATIVE_URL}, orch.fetched)
    tables = _tables(db)
    check("no assessment table exists", SV.TABLE not in tables, tables)
    check("no comparison table exists", SV.RUNS_TABLE not in tables, tables)


# ── 2. flag ON, exactly once ──────────────────────────────────────────────────
def test_flag_on_runs_the_shadow_exactly_once():
    calls = []
    real = SV.run_shadow

    def counting(*a, **kw):
        calls.append(1)
        return real(*a, **kw)
    SV.run_shadow = counting
    try:
        result, orch, db, assessor, research = _run("1")
    finally:
        SV.run_shadow = real
    check("the shadow ran exactly once", len(calls) == 1, len(calls))
    check("it read sources other than the anchor",
          SHADOW_URL in orch.fetched, orch.fetched)
    check("it spent at least one assessment call", assessor.calls >= 1)
    check("and stayed inside its declared ceiling",
          assessor.calls <= SV.MAX_CALLS_PER_RUN, assessor.calls)
    check("both shadow tables now exist",
          {SV.TABLE, SV.RUNS_TABLE} <= _tables(db), _tables(db))


def test_the_hook_runs_once_whatever_the_outcome():
    """The hook sits before the ACCEPT/HOLD branch, so the outcome cannot change how
    often it runs. It used to sit on both terminal paths -- one call each, never both,
    but two call sites is one more than the invariant needs, and the HOLD site was the
    one that ran after the write-back."""
    counts = {}
    real = SV.run_shadow
    for label, kwargs in (("accept", {}), ("hold", {"article": ""})):
        calls = []

        def counting(*a, _c=calls, **kw):
            _c.append(1)
            return real(*a, **kw)
        SV.run_shadow = counting
        try:
            result, orch, db, assessor, research = _run("1", engine_kwargs=kwargs)
        finally:
            SV.run_shadow = real
        counts[label] = (len(calls), result["status"], len(_shadow_runs(db) or []))
    check("an ACCEPT run shadows exactly once", counts["accept"][0] == 1, counts["accept"])
    check("a HOLD run shadows exactly once", counts["hold"][0] == 1, counts["hold"])
    check("the two outcomes really were different",
          counts["accept"][1] == "accept" and counts["hold"][1] == "hold", counts)
    check("each recorded exactly one comparison",
          counts["accept"][2] == 1 and counts["hold"][2] == 1, counts)
    src = (HERE / "new_engine_production.py").read_text()
    body = src.split("def run_scheduled(")[1]
    check("there is exactly one call site in run_scheduled",
          body.count("_selector_v2_shadow(") == 1, body.count("_selector_v2_shadow("))


# ── the pool ──────────────────────────────────────────────────────────────────
def test_both_selectors_rank_the_same_pool_and_can_agree():
    """The regression for the timing bug.

    _record_seed_attempt sets ce_attempt_terminal (or ce_retry_after) on the anchor, and
    selector_v2.eligible_pool filters on exactly those columns. Run the shadow after that
    write-back and the authoritative winner is gone from the pool before the shadow ever
    looks -- so same_winner could never be 1, and every comparison would report a
    disagreement that did not happen.

    Here the authoritative seed is the only eligible one and the assessor reads it as
    strong material, so agreement is the only honest answer. If the hook drifts back
    behind the write-back, the shadow finds an empty pool and this fails.
    """
    seen = {}

    def observe(db):
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        seen["pool"] = [r["id"] for r in SV.eligible_pool(conn, datetime.now())]
        seen["terminal"] = [tuple(r) for r in conn.execute(
            "SELECT id, ce_attempt_terminal, ce_retry_after, ce_attempted_date "
            "FROM news_seeds ORDER BY id")]
        conn.close()

    result, orch, db, assessor, research = _run(
        "1", competitor=False, assessor=_AssessmentProvider(prefer="crossing"),
        on_shadow=observe)

    # 1. at shadow time the anchor is still eligible, and untouched
    check("the authoritative seed is in the pool the shadow ranks",
          seen.get("pool") == ["auth-seed"], seen.get("pool"))
    check("no attempt write-back had happened yet",
          all(r[1] in (0, None) and r[2] is None and r[3] is None
              for r in seen.get("terminal", [])), seen.get("terminal"))

    # 2. the comparison can therefore say "the same"
    rows = _shadow_runs(db)
    check("exactly one comparison row", rows is not None and len(rows) == 1, rows)
    row = (rows or [{}])[0]
    check("old and shadow winner are the same seed",
          row.get("old_seed_id") == row.get("shadow_seed_id") == "auth-seed",
          (row.get("old_seed_id"), row.get("shadow_seed_id")))
    check("same_winner is recorded as 1", row.get("same_winner") == 1,
          row.get("same_winner"))
    check("agreement is a real assessment, not an empty pool",
          row.get("shadow_assessment") == "STRONG_CANDIDATE" and row.get("candidates") == 1,
          (row.get("shadow_assessment"), row.get("candidates")))

    # 3. the real pipeline continued with that same seed
    check("the pipeline still ran on the authoritative anchor",
          result["source_url"] == AUTHORITATIVE_URL, result["source_url"])

    # 4. the write-back still retires the seed afterwards, and that later mutation
    #    does not reach back into the comparison already written
    conn = sqlite3.connect(str(db))
    terminal = conn.execute(
        "SELECT ce_attempt_terminal FROM news_seeds WHERE id='auth-seed'").fetchone()[0]
    conn.row_factory = sqlite3.Row
    after_pool = [r["id"] for r in SV.eligible_pool(conn, datetime.now())]
    conn.close()
    check("the attempt write-back still happened, after the shadow",
          orch.seed_attempts == ["auth-seed"] and terminal == 1,
          (orch.seed_attempts, terminal))
    check("and it did remove the seed from the pool -- which is why order matters",
          after_pool == [], after_pool)
    check("the recorded comparison is unchanged by that later mutation",
          _shadow_runs(db) == rows)


# ── 3 & 4. authority ──────────────────────────────────────────────────────────
def test_the_authoritative_seed_is_untouched_and_only_recorded():
    result, orch, db, assessor, research = _run("1")
    rows = _shadow_runs(db)
    check("exactly one comparison row", rows is not None and len(rows) == 1, rows)
    row = (rows or [{}])[0]
    check("the row names the run", row.get("run_id") == result["engine_run"],
          row.get("run_id"))
    check("the old winner recorded is the authoritative seed",
          row.get("old_seed_id") == "auth-seed", row.get("old_seed_id"))
    check("the shadow preferred a different seed",
          row.get("shadow_seed_id") == "shadow-seed", row.get("shadow_seed_id"))
    check("and says so explicitly", row.get("same_winner") == 0, row.get("same_winner"))
    check("the shadow's rank and explanation are kept",
          row.get("shadow_rank") is not None and row.get("shadow_explanation"),
          (row.get("shadow_rank"), str(row.get("shadow_explanation"))[:80]))
    check("the shadow's own verdict is kept",
          row.get("shadow_assessment") == "STRONG_CANDIDATE", row.get("shadow_assessment"))

    # the article the pipeline actually produced is anchored to the OLD seed
    check("the pipeline's source is still the authoritative one",
          result["source_url"] == AUTHORITATIVE_URL, result["source_url"])
    check("the seed write-back names the authoritative seed only",
          orch.seed_attempts == ["auth-seed"], orch.seed_attempts)
    if result.get("candidate"):
        cand = pathlib.Path(result["candidate"]).read_text()
        check("the candidate does not carry the shadow's seed",
              SHADOW_URL not in cand and "shadow-seed" not in cand)


def test_the_shadow_never_commissions_research_discovery_or_a_writer():
    result, orch, db, assessor, research = _run("1")
    check("Research Pack ran for one anchor only", len(research.anchors) == 1,
          len(research.anchors))
    joined = json.dumps(research.anchors)
    check("and that anchor is not the shadow's story",
          SHADOW_URL not in joined and "Phreatichthys" not in joined, joined[:200])
    src = (HERE / "selector_v2.py").read_text()
    # imports only: the module docstring names these stages precisely to say it cannot
    # reach them, so a substring search over prose would fail on its own promise.
    imports = "\n".join(l for l in src.splitlines()
                        if l.startswith(("import ", "from ")) or " import " in l)
    for banned in ("research_pack", "new_engine_v1.runner", "new_engine_v1.stages",
                   "new_engine_v1 import runner", "new_engine_v1 import stages",
                   "orchestrator", "new_engine_production", "article_form", "writer"):
        check("the shadow imports nothing from %r" % banned, banned not in imports,
              imports)
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    for banned in ("R.run(", "stages.", "run_scheduled", "persist_candidate"):
        check("the shadow never calls %r" % banned, banned not in code)


def test_the_shadow_writes_nothing_to_news_seeds():
    """Bracketed tightly around the shadow itself. Comparing end-of-run against
    start-of-run would fold in the seed write-back, which is production's own legitimate
    write and happens after -- this has to isolate the shadow, not the run."""
    COLS = ("SELECT id, disability_angle, angle_checked, used, relevance_score, "
            "ce_attempt_terminal, ce_retry_after, ce_attempted_date "
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
    try:
        result, orch, db, assessor, research = _run("1")
    finally:
        SV.run_shadow = real
    check("the shadow actually ran", "before" in seen and "after" in seen)
    check("news_seeds is identical across the shadow",
          seen.get("before") == seen.get("after"),
          (seen.get("before"), seen.get("after")))
    check("disability_angle stayed NULL for both seeds",
          all(r[1] is None for r in seen.get("after", [])), seen.get("after"))
    check("no seed was marked used, retired or rested by the shadow",
          all(r[3] in (0, None) and r[5] in (0, None) and r[6] is None
              for r in seen.get("after", [])), seen.get("after"))
    conn = sqlite3.connect(str(db))
    cols = {r[1] for r in conn.execute("PRAGMA table_info(news_seeds)")}
    conn.close()
    for banned in ("shadow_seed_id", "same_winner", "shadow_rank", "shadow_assessment"):
        check("no comparison column was added to news_seeds: %s" % banned,
              banned not in cols)


# ── 5. crash containment ──────────────────────────────────────────────────────
def test_a_shadow_failure_leaves_the_real_run_exactly_as_it_was():
    control, c_orch, _, _, c_research = _run(None)
    broken, b_orch, db, _, b_research = _run("1", hook_raises=True)
    for key in ("status", "decision", "source_url", "publication_eligible",
                "engine", "engine_generation", "reason_code"):
        check("%s survives a shadow that raises" % key,
              control.get(key) == broken.get(key), (control.get(key), broken.get(key)))
    check("the seed write-back still happened",
          b_orch.seed_attempts == ["auth-seed"], b_orch.seed_attempts)
    check("a candidate was still produced" if control.get("candidate") else
          "the HOLD is unchanged",
          bool(control.get("candidate")) == bool(broken.get("candidate")))
    check("Research Pack ran the same number of times",
          len(c_research.anchors) == len(b_research.anchors))


def test_a_provider_failure_inside_the_shadow_is_contained_and_visible():
    logs = []
    result, orch, db, assessor, research = _run(
        "1", assessor=_AssessmentProvider(raise_on_call=True))
    check("the real run still finished", result["status"] in ("accept", "hold"), result)
    check("the anchor is unchanged", result["source_url"] == AUTHORITATIVE_URL)
    # the shadow degrades rather than disappearing: it still records what it read
    rows = _shadow_runs(db)
    check("a comparison row still exists", rows is not None and len(rows) == 1, rows)
    if rows:
        check("with no shadow winner, stated plainly",
              rows[0]["shadow_seed_id"] is None
              and rows[0]["status"] == "NO_SHADOW_WINNER", rows[0])


def test_the_hook_is_fail_open_by_construction():
    src = (HERE / "new_engine_production.py").read_text()
    fn = src.split("def _selector_v2_shadow(")[1].split("\ndef ")[0]
    check("the hook opens with the flag gate",
          "if not SV.enabled():" in fn
          and "return" in fn.split("if not SV.enabled():")[1][:40])
    check("everything after the gate is inside try/except", fn.count("try:") >= 1
          and "except Exception" in fn)
    check("the exception is logged, not swallowed", "logger.warning" in fn)
    check("nothing is re-raised out of the hook", "raise" not in fn)
    check("the connection is closed on every path",
          "finally:" in fn and "conn.close()" in fn)
    check("the hook returns nothing a caller could act on", "-> None" in
          src.split("def _selector_v2_shadow(")[1].split("\n")[0])
    body = src.split("def run_scheduled(")[1]
    check("the hook is never assigned to anything in run_scheduled",
          "= _selector_v2_shadow" not in body)
    check("run_scheduled calls it exactly once",
          body.count("_selector_v2_shadow(") == 1, body.count("_selector_v2_shadow("))
    call = body.index("_selector_v2_shadow(")
    check("the call is before the engine runs", call < body.index("out = R.run("))
    check("the call is before any seed write-back",
          call < body.index("_record_seed_attempt(orch"))
    check("the call is after the anchor and its source are settled",
          body.index("seed, selection = _select_seed(orch, model)") < call
          and body.index('payload = {') < call)


# ── 8. cron ───────────────────────────────────────────────────────────────────
def test_the_flag_is_not_enabled_anywhere_in_the_repository():
    """The comparison is opt-in. Nothing checked in may turn it on -- not a shell script,
    not a default, not a config file. The scheduler enables it, or it does not run."""
    root = HERE.parent
    setters = []
    for p in root.rglob("*"):
        # Prose is allowed to name the flag -- documenting how an operator would turn
        # it on is the opposite of turning it on. This guards code and config.
        if (not p.is_file() or ".git/" in str(p)
                or p.suffix in (".png", ".jpg", ".db", ".md")):
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        if SV.SHADOW_ENV not in text:
            continue
        for line in text.splitlines():
            if SV.SHADOW_ENV not in line:
                continue
            stripped = line.strip()
            if (stripped.startswith(("#", "*", "-", '"""')) or "os.environ.get" in line
                    or "SHADOW_ENV =" in line or "SV.SHADOW_ENV" in line
                    or "environ.pop" in line):
                continue
            if "=" in line.split(SV.SHADOW_ENV, 1)[1][:3] or "export" in line:
                setters.append("%s: %s" % (p.relative_to(root), stripped[:100]))
    check("no checked-in file sets the flag", not setters, setters)
    check("the default really is off",
          (os.environ.pop(SV.SHADOW_ENV, None), SV.enabled() is False)[1])
    switch = (HERE / "engine_switch.py").read_text()
    check("the engine switch is untouched by the shadow",
          "selector_v2" not in switch and SV.SHADOW_ENV not in switch)
    po = (HERE / "production_orchestrator.py").read_text()
    check("production_orchestrator does not enable or import the shadow",
          "selector_v2" not in po and SV.SHADOW_ENV not in po)


def main():
    for fn in (test_flag_off_the_hook_does_nothing,
               test_flag_on_runs_the_shadow_exactly_once,
               test_the_hook_runs_once_whatever_the_outcome,
               test_both_selectors_rank_the_same_pool_and_can_agree,
               test_the_authoritative_seed_is_untouched_and_only_recorded,
               test_the_shadow_never_commissions_research_discovery_or_a_writer,
               test_the_shadow_writes_nothing_to_news_seeds,
               test_a_shadow_failure_leaves_the_real_run_exactly_as_it_was,
               test_a_provider_failure_inside_the_shadow_is_contained_and_visible,
               test_the_hook_is_fail_open_by_construction,
               test_the_flag_is_not_enabled_anywhere_in_the_repository):
        print("\n" + fn.__name__)
        fn()
    os.environ.pop(SV.SHADOW_ENV, None)
    os.environ.pop("NEW_ENGINE_V1_MODE", None)
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL SELECTOR V2 RUNTIME HOOK TESTS PASSED")


if __name__ == "__main__":
    main()
