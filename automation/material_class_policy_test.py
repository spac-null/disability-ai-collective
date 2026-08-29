#!/usr/bin/env python3
"""
material_class_policy_test.py -- contextual freshness, and only that.

The pool ran on one clock: ingest 7 days, consider 3, delete at 14. That is a news
wire's clock. Under it a research paper published three weeks ago could not enter the
pool, and one published today became ineligible on its fourth day and was deleted on its
fifteenth -- which is why the low-cadence feeds in the configuration have produced
nothing that ever reached selection.

These tests pin the two halves of that fix and, just as importantly, pin what it must
NOT do: no class earns ranking points, no publisher is boosted or penalised, and
disability-led provenance carries no weight in either direction.

SQLite and pure functions only. No network, no model, no production DB.
"""
from __future__ import annotations

import logging
import pathlib
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import material_policy as MP                                       # noqa: E402
import news_fetcher as NF                                          # noqa: E402
from orchestrator.discovery import DiscoveryMixin                  # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:220]))
    if not ok:
        FAILURES.append(label)


class Orch(DiscoveryMixin):
    def __init__(self, db):
        self.discovery_db = db
        self.logger = logging.getLogger("material_class_policy_test")


def _db(seeds):
    """seeds: (id, days_old, score, angle, material_class)"""
    d = pathlib.Path(tempfile.mkdtemp()) / "disability_findings.db"
    o = Orch(d)
    conn = sqlite3.connect(str(d))
    o._init_news_seeds_table(conn)
    o._ensure_decline_columns(conn)
    for sid, age, score, angle, cls in seeds:
        day = (datetime.now() - timedelta(days=age)).strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO news_seeds (id, url, title, summary, source_name, source_tier,"
            " pub_date, fetched_date, relevance_score, themes, disability_angle, used,"
            " material_class) VALUES (?,?,?,?,?,?,?,?,?,?,?,0,?)",
            (sid, "https://example.org/%s" % sid, "Title %s" % sid, "s", "Example", 1,
             day, day, score, "[]", angle, cls))
    conn.commit(); conn.close()
    return o


def _pick(o):
    s = o.get_news_seed()
    return s["id"] if s else None


# ── eligibility by class ──────────────────────────────────────────────────────
def test_current_news_keeps_the_old_window():
    o = _db([("fresh", 2, 0.9, "angle", MP.CURRENT_NEWS)])
    check("a 2-day-old news seed is eligible", _pick(o) == "fresh")
    o = _db([("stale", 5, 0.9, "angle", MP.CURRENT_NEWS)])
    check("a 5-day-old news seed is not", _pick(o) is None, _pick(o))


def test_essay_culture_and_research_get_their_own_horizons():
    for cls, ages in ((MP.ESSAY_OPINION, (10, 25)), (MP.CULTURE, (10, 25)),
                      (MP.RESEARCH_REPORT, (30, 60, 85)), (MP.EVERGREEN, (60, 150))):
        for age in ages:
            o = _db([("s", age, 0.9, "angle", cls)])
            check("%s: a %d-day-old seed is still eligible" % (cls, age),
                  _pick(o) == "s", _pick(o))
        too_old = MP.eligibility_days(cls) + 5
        o = _db([("s", too_old, 0.9, "angle", cls)])
        check("%s: a %d-day-old seed is past its horizon" % (cls, too_old),
              _pick(o) is None, _pick(o))


def test_null_class_behaves_exactly_as_before():
    o = _db([("legacy", 2, 0.9, "angle", None)])
    check("an unclassified 2-day-old seed is eligible", _pick(o) == "legacy")
    o = _db([("legacy", 5, 0.9, "angle", None)])
    check("an unclassified 5-day-old seed is not -- the legacy 3-day rule",
          _pick(o) is None, _pick(o))
    check("NULL resolves to OTHER", MP.normalise(None) == MP.OTHER)
    check("OTHER is the legacy clock",
          MP.policy_for(MP.OTHER) == {"ingest_lookback_days": 7, "eligibility_days": 3,
                                      "retention_days": 14})


# ── ranking must not move ─────────────────────────────────────────────────────
def test_class_grants_no_ranking_advantage():
    """Eligibility is not preference. A research seed that is merely still eligible
    must not beat fresher, higher-scoring news."""
    o = _db([("news", 1, 0.9, "angle", MP.CURRENT_NEWS),
             ("paper", 40, 0.95, "angle", MP.RESEARCH_REPORT)])
    check("the higher score wins regardless of class", _pick(o) == "paper")
    o = _db([("news", 1, 0.95, "angle", MP.CURRENT_NEWS),
             ("paper", 40, 0.9, "angle", MP.RESEARCH_REPORT)])
    check("and so does the higher-scoring news", _pick(o) == "news")
    o = _db([("older", 3, 0.9, "angle", MP.CULTURE),
             ("newer", 1, 0.9, "angle", MP.CULTURE)])
    check("equal scores still break by pub_date DESC", _pick(o) == "newer")
    src = (HERE / "orchestrator" / "discovery.py").read_text()
    check("the ORDER BY is untouched",
          src.count("ORDER BY relevance_score DESC, pub_date DESC") >= 2)
    check("no class appears in any ORDER BY",
          not any("material_class" in line and "ORDER BY" in line
                  for line in src.splitlines()))


def test_no_disability_boost_and_no_quota():
    # Executable code only -- the module docstring says out loud that provenance
    # carries no weight, and scanning raw text would flag it for saying so.
    import ast
    tree = ast.parse((HERE / "material_policy.py").read_text())
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docstrings.add(body[0].value.value)
    code_strings = [n.value.lower() for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and n.value not in docstrings]
    names = [n.id.lower() for n in ast.walk(tree) if isinstance(n, ast.Name)]
    names += [n.attr.lower() for n in ast.walk(tree) if isinstance(n, ast.Attribute)]
    surface = " ".join(code_strings + names)
    for word in ("disability", "disabled", "crip", "quota", "boost", "penal", "weight"):
        check("no %r appears in material_policy's executable surface" % word,
              word not in surface, word)
    check("class policy contains only temporal fields",
          all(set(v) == {"ingest_lookback_days", "eligibility_days", "retention_days"}
              for v in MP.POLICY.values()))
    # a disability-led feed is classed by what it supplies, like any other
    feeds = {f["name"]: f.get("class") for f in NF.QUALITY_FEEDS}
    check("Disability News Service is CURRENT_NEWS (a news feed)",
          feeds.get("Disability News Service") == MP.CURRENT_NEWS, feeds.get("Disability News Service"))
    check("Disability Arts Online is CULTURE (an arts feed)",
          feeds.get("Disability Arts Online") == MP.CULTURE)
    check("Disability Visibility Project is ESSAY_OPINION (an essay feed)",
          feeds.get("Disability Visibility Project") == MP.ESSAY_OPINION)
    check("no feed carries a weight, score or quota field",
          not any(set(f) - {"url", "name", "class", "tier"} for f in NF.QUALITY_FEEDS),
          [set(f) for f in NF.QUALITY_FEEDS if set(f) - {"url", "name", "class", "tier"}])


# ── ingest ────────────────────────────────────────────────────────────────────
def test_ingest_lookback_follows_the_feed_class():
    seen = {}

    def fake_fetch(feed, days=None):
        seen[feed["name"]] = days if days is not None else MP.ingest_lookback_days(feed.get("class"))
        return []

    real = NF.fetch_feed
    NF.fetch_feed = fake_fetch
    try:
        NF.fetch_all_feeds()
    finally:
        NF.fetch_feed = real
    news = [n for n, f in ((f["name"], f) for f in NF.QUALITY_FEEDS)
            if f.get("class") == MP.CURRENT_NEWS]
    research = [f["name"] for f in NF.QUALITY_FEEDS if f.get("class") == MP.RESEARCH_REPORT]
    evergreen = [f["name"] for f in NF.QUALITY_FEEDS if f.get("class") == MP.EVERGREEN]
    check("a news feed still looks back 7 days", seen.get(news[0]) == 7, seen.get(news[0]))
    check("a research feed looks back 90", seen.get(research[0]) == 90, seen.get(research[0]))
    check("an evergreen feed looks back 180", seen.get(evergreen[0]) == 180,
          seen.get(evergreen[0]))
    check("every configured feed was asked", len(seen) == len(NF.QUALITY_FEEDS))


def test_historical_ingestion_stays_bounded():
    check("a per-feed fetch cap exists and is small",
          0 < MP.MAX_ITEMS_PER_FEED_PER_FETCH <= 100, MP.MAX_ITEMS_PER_FEED_PER_FETCH)
    src = (HERE / "news_fetcher.py").read_text()
    check("fetch_feed applies the cap", "MAX_ITEMS_PER_FEED_PER_FETCH" in src)
    check("the cap keeps the newest items",
          "items.sort(key=lambda i: i.get(\"pub_date\") or \"\", reverse=True)" in src)


# ── retention ─────────────────────────────────────────────────────────────────
def test_retention_never_deletes_an_eligible_seed():
    for cls in MP.CLASSES:
        check("%s: retention exceeds eligibility" % cls,
              MP.retention_days(cls) > MP.eligibility_days(cls),
              (MP.retention_days(cls), MP.eligibility_days(cls)))

    o = _db([("paper", 60, 0.9, "angle", MP.RESEARCH_REPORT),
             ("news", 20, 0.9, "angle", MP.CURRENT_NEWS)])
    conn = sqlite3.connect(str(o.discovery_db))
    NF.prune_old(conn)
    left = {r[0] for r in conn.execute("SELECT id FROM news_seeds")}
    conn.close()
    check("a 60-day-old research seed survives (still eligible)", "paper" in left, left)
    check("a 20-day-old news seed is pruned (past its 14-day retention)",
          "news" not in left, left)
    check("and the surviving research seed is still selectable", _pick(o) == "paper")

    o2 = _db([("ancient", 130, 0.9, "angle", MP.RESEARCH_REPORT)])
    conn = sqlite3.connect(str(o2.discovery_db))
    NF.prune_old(conn)
    left = {r[0] for r in conn.execute("SELECT id FROM news_seeds")}
    conn.close()
    check("a research seed past 120 days is finally pruned", left == set(), left)


# ── migration / backfill ──────────────────────────────────────────────────────
def test_migration_and_backfill_are_safe():
    d = pathlib.Path(tempfile.mkdtemp()) / "legacy.db"
    conn = sqlite3.connect(str(d))
    conn.execute("""CREATE TABLE news_seeds (
        id TEXT PRIMARY KEY, url TEXT, title TEXT, summary TEXT, source_name TEXT,
        source_tier INTEGER, pub_date TEXT, fetched_date TEXT, relevance_score REAL,
        themes TEXT, disability_angle TEXT, used INTEGER DEFAULT 0, used_date TEXT)""")
    day = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    conn.execute("INSERT INTO news_seeds VALUES ('a','u','t','s','Aeon',1,?,?,0.9,'[]',"
                 "'angle',0,NULL)", (day, day))
    conn.execute("INSERT INTO news_seeds VALUES ('b','u2','t','s','Some Feed That Left',1,"
                 "?,?,0.9,'[]','angle',0,NULL)", (day, day))
    conn.commit()
    NF.init_db(conn)
    rows = dict(conn.execute("SELECT id, material_class FROM news_seeds").fetchall())
    conn.close()
    check("a row from a configured feed is backfilled from that feed's class",
          rows["a"] == MP.ESSAY_OPINION, rows)
    check("a row whose feed is not configured is left NULL, not guessed",
          rows["b"] is None, rows)
    o = Orch(d)
    check("the backfilled 20-day-old essay is now selectable", _pick(o) == "a", _pick(o))
    conn = sqlite3.connect(str(d))
    before = dict(conn.execute("SELECT id, material_class FROM news_seeds").fetchall())
    NF.backfill_material_class(conn)
    after = dict(conn.execute("SELECT id, material_class FROM news_seeds").fetchall())
    conn.close()
    check("re-running the backfill changes nothing", before == after)


def test_pr46_attempt_filters_still_apply():
    o = _db([("paper", 40, 0.95, "angle", MP.RESEARCH_REPORT),
             ("news", 1, 0.9, "angle", MP.CURRENT_NEWS)])
    check("the research seed wins on score", _pick(o) == "paper")
    klass, outcome = Orch.classify_current_engine_attempt(
        {"decision": "HOLD", "reason_code": "HOLD_INSUFFICIENT_RESEARCH"})
    o.mark_news_seed_current_engine_attempt("paper", run="r", klass=klass, outcome=outcome)
    check("a terminal attempt still retires it, whatever its class", _pick(o) == "news")


def test_every_configured_feed_has_a_class():
    unclassified = [f["name"] for f in NF.QUALITY_FEEDS
                    if MP.normalise(f.get("class")) != f.get("class")]
    check("every feed declares a valid class", not unclassified, unclassified)
    check("all 57 feeds are classified", len(NF.QUALITY_FEEDS) == 57, len(NF.QUALITY_FEEDS))


def main():
    for fn in (test_current_news_keeps_the_old_window,
               test_essay_culture_and_research_get_their_own_horizons,
               test_null_class_behaves_exactly_as_before,
               test_class_grants_no_ranking_advantage,
               test_no_disability_boost_and_no_quota,
               test_ingest_lookback_follows_the_feed_class,
               test_historical_ingestion_stays_bounded,
               test_retention_never_deletes_an_eligible_seed,
               test_migration_and_backfill_are_safe,
               test_pr46_attempt_filters_still_apply,
               test_every_configured_feed_has_a_class):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL MATERIAL-CLASS POLICY TESTS PASSED")


if __name__ == "__main__":
    main()
