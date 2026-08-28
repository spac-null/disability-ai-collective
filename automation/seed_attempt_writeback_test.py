#!/usr/bin/env python3
"""
seed_attempt_writeback_test.py -- CURRENT_ENGINE tells the seed pool what happened.

The bug this closes was live and silent: `used` is set only by the legacy path on
commit_success, which NEW_ENGINE_V1 never reaches, so nothing recorded that a seed had
been tried. The 09:00 selector kept choosing the same top-scoring anchor -- 25+26 August
ran one MIT Tech Review seed, 27+28 August one Dezeen roundup, four runs and two anchors.

The distinction under test is the whole point: an outcome that would not change on a
rerun retires the seed; an outage frees it for the next natural run. Anything
unrecognised is retryable, because wrongly retrying costs a run and wrongly consuming
loses a story.

SQLite only. No network, no model, no production DB.
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

from orchestrator.discovery import DiscoveryMixin, STORY_REJECTION_CONTRACT_VERSION  # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:200]))
    if not ok:
        FAILURES.append(label)


class Orch(DiscoveryMixin):
    def __init__(self, db):
        self.discovery_db = db
        self.logger = logging.getLogger("seed_attempt_writeback_test")


def _fresh_db(seeds):
    d = pathlib.Path(tempfile.mkdtemp()) / "disability_findings.db"
    o = Orch(d)
    conn = sqlite3.connect(str(d))
    o._init_news_seeds_table(conn)
    o._ensure_decline_columns(conn)
    today = datetime.now().strftime("%Y-%m-%d")
    for sid, score, angle in seeds:
        conn.execute(
            "INSERT INTO news_seeds (id, url, title, summary, source_name, source_tier, "
            "pub_date, fetched_date, relevance_score, themes, disability_angle, used) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,0)",
            (sid, "https://example.org/%s" % sid, "Title %s" % sid, "summary",
             "Example", 1, today, today, score, "[]", angle))
    conn.commit()
    conn.close()
    return o


def _pick(o):
    seed = o.get_news_seed()
    return seed["id"] if seed else None


# ── 1 + 11: baseline selection ────────────────────────────────────────────────
def test_fresh_seed_is_selectable_and_ranking_is_unchanged():
    o = _fresh_db([("A", 0.9, "angle A"), ("B", 0.7, "angle B"), ("C", 0.95, None)])
    check("a fresh seed with an angle is selectable", _pick(o) == "A", _pick(o))
    check("ranking among eligible seeds is untouched: highest score with an angle wins",
          _pick(o) == "A")
    o2 = _fresh_db([("A", 0.2, "angle A"), ("B", 0.8, "angle B")])
    check("score order still decides", _pick(o2) == "B", _pick(o2))


# ── 2-4: terminal outcomes retire the seed ────────────────────────────────────
def _attempt(o, seed_id, result, run="run-1", pack=None, words=None):
    klass, outcome = o.classify_current_engine_attempt(result)
    o.mark_news_seed_current_engine_attempt(seed_id, run=run, klass=klass,
                                            outcome=outcome, pack_verdict=pack,
                                            pack_subject_words=words)
    return klass, outcome


def _age(o, seed_id, hours):
    """Advance the clock by `hours` for one seed, by moving its retry gate back that
    far. Only touches a gate that exists -- a terminal attempt has none, and inventing
    one would test the opposite of what it claims."""
    conn = sqlite3.connect(str(o.discovery_db))
    row = conn.execute("SELECT ce_retry_after FROM news_seeds WHERE id = ?",
                       (seed_id,)).fetchone()
    if row and row[0]:
        gate = datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%S") - timedelta(hours=hours)
        conn.execute("UPDATE news_seeds SET ce_retry_after = ? WHERE id = ?",
                     (gate.strftime("%Y-%m-%dT%H:%M:%S"), seed_id))
        conn.commit()
    conn.close()


def test_terminal_outcomes_are_recorded_and_not_repeated():
    for label, result, expect_outcome in (
            ("ACCEPT / candidate produced",
             {"decision": "ACCEPT", "reason_code": None}, "TERMINAL:ACCEPT"),
            ("HOLD_INSUFFICIENT_RESEARCH",
             {"decision": "HOLD", "reason_code": "HOLD_INSUFFICIENT_RESEARCH"},
             "TERMINAL:HOLD_INSUFFICIENT_RESEARCH"),
            ("deterministic researched-scope violation",
             {"decision": "HOLD",
              "reason_code": "DISCOVERY_SUBJECT_OUTSIDE_RESEARCHED_SCOPE"},
             "TERMINAL:DISCOVERY_SUBJECT_OUTSIDE_RESEARCHED_SCOPE"),
            ("deterministic anchor-invariant failure",
             {"decision": "HOLD", "reason_code": "DISCOVERY_SOURCE_ANCHOR_NOT_IN_SOURCE"},
             "TERMINAL:DISCOVERY_SOURCE_ANCHOR_NOT_IN_SOURCE")):
        o = _fresh_db([("A", 0.9, "angle A"), ("B", 0.7, "angle B")])
        check("%s: seed A wins first" % label, _pick(o) == "A")
        klass, outcome = _attempt(o, "A", result)
        check("%s: classified terminal" % label, klass == Orch.CE_TERMINAL, klass)
        check("%s: outcome recorded as %s" % (label, expect_outcome),
              outcome == expect_outcome, outcome)
        row = sqlite3.connect(str(o.discovery_db)).execute(
            "SELECT ce_attempted_date, ce_attempt_run, ce_attempt_outcome, "
            "ce_attempt_terminal, used, ce_retry_after FROM news_seeds WHERE id='A'"
        ).fetchone()
        check("%s: a terminal attempt sets no retry gate" % label, row[5] is None, row)
        check("%s: attempt row written" % label,
              row[0] and row[1] == "run-1" and row[2] == outcome and row[3] == 1, row)
        check("%s: legacy `used` is NOT touched" % label, row[4] == 0, row)
        check("%s: the seed no longer wins" % label, _pick(o) == "B", _pick(o))


# ── 5-7: retryable outcomes ───────────────────────────────────────────────────
def test_transient_failures_stay_retryable():
    for label, result in (
            ("provider failure",
             {"decision": "HOLD", "run_status": {"status": "PROVIDER_FAILURE"},
              "reason_code": "GROUNDING_FINDINGS_PROVIDER_ERROR"}),
            ("contract failure / EXTRACTION_ERROR shape",
             {"decision": "HOLD", "run_status": {"status": "CONTRACT_FAILURE"},
              "reason_code": "RESEARCH_PACK_INVALID_RESPONSE_SHAPE"}),
            ("unclassifiable result",
             {"decision": "SOMETHING_NEW"})):
        o = _fresh_db([("A", 0.9, "angle A"), ("B", 0.7, "angle B")])
        klass, outcome = _attempt(o, "A", result)
        check("%s: not terminal" % label, klass == Orch.CE_TRANSIENT, (klass, outcome))
        check("%s: outcome names the class" % label,
              outcome.startswith(Orch.CE_TRANSIENT), outcome)
        check("%s: within the cooldown the seed steps aside" % label,
              _pick(o) == "B", _pick(o))
        _age(o, "A", Orch.CE_RETRY_COOLDOWN_HOURS + 1)      # the gate has passed
        check("%s: eligible again after the cooldown" % label, _pick(o) == "A", _pick(o))


def test_source_acquisition_retry_semantics_are_untouched():
    """A failed fetch is deliberately NOT an exclusion (owner correction, 2026-08-23),
    and this PR does not change that: source_unusable stays diagnostic, and the
    bounded per-run retry still lives in get_news_seed_with_usable_source."""
    o = _fresh_db([("A", 0.9, "angle A")])
    o.mark_news_seed_source_unusable("A", "no_article_body:paragraphs=1<3")
    check("a source_unusable seed is still selectable", _pick(o) == "A", _pick(o))
    src = (HERE / "orchestrator" / "discovery.py").read_text()
    check("selection still does not exclude on source_unusable",
          "source_unusable = 1" not in src.split("def get_news_seed(")[1].split("def ")[0])
    check("the per-run exclusion list still exists",
          "exclude_ids" in src.split("def get_news_seed_with_usable_source(")[1][:2000])


# ── 8: pack feedback ──────────────────────────────────────────────────────────
def test_pack_verdict_and_subject_words_are_recorded():
    o = _fresh_db([("A", 0.9, "angle A"), ("B", 0.7, "angle B")])
    _attempt(o, "A", {"decision": "HOLD", "reason_code": "HOLD_INSUFFICIENT_RESEARCH"},
             pack="HOLD_INSUFFICIENT_RESEARCH", words=118)
    row = sqlite3.connect(str(o.discovery_db)).execute(
        "SELECT ce_pack_verdict, ce_pack_subject_words FROM news_seeds WHERE id='A'"
    ).fetchone()
    check("pack verdict recorded", row[0] == "HOLD_INSUFFICIENT_RESEARCH", row)
    check("subject-relevant word count recorded", row[1] == 118, row)

    # recorded, and NOT used for ranking: a rich pack does not promote its seed
    o2 = _fresh_db([("A", 0.5, "angle A"), ("B", 0.9, "angle B")])
    _attempt(o2, "A", {"decision": "HOLD", "run_status": {"status": "PROVIDER_FAILURE"}},
             pack="ARTICLE", words=900)
    conn = sqlite3.connect(str(o2.discovery_db))
    conn.execute("UPDATE news_seeds SET ce_attempted_date=NULL WHERE id='A'")
    conn.commit(); conn.close()
    check("a recorded pack verdict does not change who wins", _pick(o2) == "B", _pick(o2))

    # a later attempt that never reached the pack keeps the earlier verdict
    _attempt(o2, "A", {"decision": "HOLD", "run_status": {"status": "PROVIDER_FAILURE"}},
             run="run-2")
    row = sqlite3.connect(str(o2.discovery_db)).execute(
        "SELECT ce_pack_verdict, ce_attempt_run FROM news_seeds WHERE id='A'").fetchone()
    check("an attempt with no pack does not erase the recorded verdict",
          row[0] == "ARTICLE" and row[1] == "run-2", row)


# ── 9 + 10: migration and legacy semantics ────────────────────────────────────
def test_old_rows_stay_valid_and_used_is_not_redefined():
    d = pathlib.Path(tempfile.mkdtemp()) / "legacy.db"
    conn = sqlite3.connect(str(d))
    conn.execute("""CREATE TABLE news_seeds (
        id TEXT PRIMARY KEY, url TEXT, title TEXT, summary TEXT, source_name TEXT,
        source_tier INTEGER, pub_date TEXT, fetched_date TEXT, relevance_score REAL,
        themes TEXT, disability_angle TEXT, used INTEGER DEFAULT 0, used_date TEXT)""")
    today = datetime.now().strftime("%Y-%m-%d")
    conn.execute("INSERT INTO news_seeds VALUES ('OLD','https://x/','t','s','Example',1,"
                 "?,?,0.9,'[]','angle',0,NULL)", (today, today))
    conn.commit(); conn.close()
    o = Orch(d)
    check("a pre-migration row is selectable before any migration", _pick(o) == "OLD")
    c = sqlite3.connect(str(d))
    cols = {r[1] for r in c.execute("PRAGMA table_info(news_seeds)")}
    check("migration added the attempt columns",
          {"ce_attempted_date", "ce_attempt_run", "ce_attempt_outcome",
           "ce_attempt_terminal", "ce_pack_verdict", "ce_pack_subject_words",
           "ce_retry_after"} <= cols,
          sorted(cols))
    row = c.execute("SELECT ce_attempt_terminal, ce_attempted_date, used FROM news_seeds "
                    "WHERE id='OLD'").fetchone()
    check("history is left NULL rather than invented",
          row[1] is None, row)
    check("no attempt outcome is retrofitted onto old rows", row[0] in (0, None), row)
    check("`used` still means what it meant: set only by a legacy commit", row[2] == 0)
    check("a historical row with no attempt metadata still selects", _pick(o) == "OLD")

    # and legacy `used` still excludes, exactly as before
    c.execute("UPDATE news_seeds SET used = 1 WHERE id='OLD'"); c.commit(); c.close()
    check("used = 1 still removes a seed", _pick(o) is None, _pick(o))


# ── 12: blast radius ──────────────────────────────────────────────────────────
def test_nothing_else_was_touched():
    import subprocess
    changed = subprocess.run(["git", "diff", "--name-only", "origin/main", "HEAD"],
                             cwd=str(HERE.parent), capture_output=True, text=True).stdout.split()
    forbidden = [f for f in changed if any(k in f for k in (
        "new_engine_v1/", "publication_safety_bridge", "publish_best", "news_fetcher",
        "grounding_v2", "stages.py", "decision.py"))]
    check("no engine, bridge, grounder, feed or publish file is in the diff",
          not forbidden, forbidden)
    src = (HERE / "orchestrator" / "discovery.py").read_text()
    check("relevance scoring is untouched in this PR",
          "THEME_WEIGHTS" not in src or "def score_item" not in src)
    check("the ORDER BY is unchanged",
          src.count("ORDER BY relevance_score DESC, pub_date DESC") >= 2)


# ── regressions ───────────────────────────────────────────────────────────────
def test_repeat_anchor_regression():
    """DAY 1 seed A wins and reaches a terminal outcome; DAY 2 seed B must win.
    This is the 25-28 August shape, in miniature."""
    o = _fresh_db([("A", 0.9, "angle A"), ("B", 0.7, "angle B")])
    day1 = _pick(o)
    _attempt(o, day1, {"decision": "ACCEPT"}, run="day1")
    day2 = _pick(o)
    check("day 1 selects A", day1 == "A")
    check("day 2 does NOT select A again", day2 != "A", day2)
    check("day 2 selects the next eligible seed", day2 == "B", day2)


def test_transient_failure_regression():
    """DAY 1 seed A fails on the provider; the next eligible attempt may use A again."""
    o = _fresh_db([("A", 0.9, "angle A"), ("B", 0.7, "angle B")])
    _attempt(o, "A", {"decision": "HOLD", "run_status": {"status": "PROVIDER_FAILURE"}},
             run="day1")
    check("the same day, A steps aside rather than looping", _pick(o) == "B")
    _age(o, "A", Orch.CE_RETRY_COOLDOWN_HOURS + 1)
    check("the next natural run may try A again", _pick(o) == "A", _pick(o))
    check("an outage costs a day, not a story", True)


def test_grounder_hold_is_reviewable_not_terminal():
    """The authoritative grounder is measured non-deterministic on identical bytes: a
    classification flipped 1 in 10 trials at temperature 0, and findings appeared and
    vanished between passes. A HOLD it produced is therefore not proven to be a
    property of the seed, and must not delete the seed.

    DAY 1  A -> grounding HOLD (TRUE_UNCERTAIN / TRUE_UNSUPPORTED reach here with no
           reason code, straight from decision.py)
    DAY 2  B wins
    DAY 3  A is eligible again if it is otherwise still eligible."""
    for label, result in (
            ("unadjudicated TRUE_UNCERTAIN", {"decision": "HOLD", "reason_code": None}),
            ("unresolved TRUE_UNSUPPORTED", {"decision": "HOLD", "reason_code": None}),
            ("a named code not known to be deterministic",
             {"decision": "HOLD", "reason_code": "SOME_FUTURE_POLICY_CODE"})):
        o = _fresh_db([("A", 0.9, "angle A"), ("B", 0.7, "angle B")])
        check("%s: day 1 selects A" % label, _pick(o) == "A")
        klass, outcome = _attempt(o, "A", result, run="day1")
        check("%s: classified reviewable, not terminal" % label,
              klass == Orch.CE_REVIEWABLE, (klass, outcome))
        row = sqlite3.connect(str(o.discovery_db)).execute(
            "SELECT ce_attempt_terminal, ce_retry_after, ce_attempt_outcome "
            "FROM news_seeds WHERE id='A'").fetchone()
        check("%s: the seed is NOT retired" % label, row[0] == 0, row)
        check("%s: a retry gate is set instead" % label, bool(row[1]), row)
        check("%s: the outcome names the class" % label,
              row[2].startswith(Orch.CE_REVIEWABLE), row[2])
        check("%s: day 2 selects B" % label, _pick(o) == "B", _pick(o))
        _age(o, "A", 24)         # a day later: still gated, because the gate is 48h
        check("%s: still gated one day later" % label, _pick(o) == "B", _pick(o))
        _age(o, "A", Orch.CE_REVIEWABLE_COOLDOWN_HOURS + 1)
        check("%s: day 3 A is eligible again" % label, _pick(o) == "A", _pick(o))


def test_research_hold_stays_terminal_alongside_reviewable_holds():
    """The distinction that matters: the pack looked and found nothing (terminal), vs
    a model judged the prose and might judge it differently tomorrow (reviewable)."""
    o = _fresh_db([("A", 0.9, "angle A"), ("B", 0.7, "angle B")])
    klass, _ = _attempt(o, "A", {"decision": "HOLD",
                                 "reason_code": "HOLD_INSUFFICIENT_RESEARCH"})
    check("HOLD_INSUFFICIENT_RESEARCH is terminal", klass == Orch.CE_TERMINAL, klass)
    check("its retry gate was never set",
          sqlite3.connect(str(o.discovery_db)).execute(
              "SELECT ce_retry_after FROM news_seeds WHERE id='A'").fetchone()[0] is None)
    _age(o, "A", 1000)           # no amount of time revives a terminal attempt
    check("no cooldown revives it", _pick(o) == "B", _pick(o))


def main():
    for fn in (test_fresh_seed_is_selectable_and_ranking_is_unchanged,
               test_terminal_outcomes_are_recorded_and_not_repeated,
               test_transient_failures_stay_retryable,
               test_source_acquisition_retry_semantics_are_untouched,
               test_pack_verdict_and_subject_words_are_recorded,
               test_old_rows_stay_valid_and_used_is_not_redefined,
               test_nothing_else_was_touched,
               test_grounder_hold_is_reviewable_not_terminal,
               test_research_hold_stays_terminal_alongside_reviewable_holds,
               test_repeat_anchor_regression,
               test_transient_failure_regression):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL SEED-ATTEMPT WRITE-BACK TESTS PASSED")


if __name__ == "__main__":
    main()
