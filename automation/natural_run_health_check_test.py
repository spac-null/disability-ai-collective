#!/usr/bin/env python3
"""
natural_run_health_check_test.py — static test suite for
natural_run_health_check.py.

Builds one shared, throwaway fixture repo per test (real `git` + real
sqlite3 files under a temp dir -- never a mock of either), varying the
engagement.db contents, automation.log contents, and environment per
scenario. Never touches any real production path.

Covers the scenarios from the ops task's own list:
  - missing schema (no engagement.db at all)
  - old schema (engagement.db exists, missing the new observer columns)
  - partial run (row exists, observers still null)
  - completed run (full schema, full observer data, fact_check_status: verified)
  - legitimate editorial block (fact_check_status: blocked) -> still PASS
  - infrastructure failure (automation.log shows a wrapper-reported failure
    or a raw traceback) -> FAIL
  - CJ2/L2 OFF -> tables correctly not expected, not flagged
  - accidental mode activation -> flagged, non-silent

USAGE: python3 automation/natural_run_health_check_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

import natural_run_health_check as hc  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def sh(cwd, *args):
    result = subprocess.run(["git", "-C", str(cwd)] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {args} in {cwd} failed: {result.stderr}")
    return result.stdout


GENERATE_PY_SAFE = '''
class GenerateMixin:
    @staticmethod
    def _compute_should_block(degraded_stages):
        stages = set(degraded_stages)
        return "fable_brief" in stages or "gate_llm" in stages or len(stages) >= 2

    def other_method(self):
        pass
'''

GENERATE_PY_LEAKED = '''
class GenerateMixin:
    @staticmethod
    def _compute_should_block(degraded_stages):
        stages = set(degraded_stages)
        if stages.intersection({"shadow_repetition_hits"}):
            return True
        return "fable_brief" in stages or "gate_llm" in stages or len(stages) >= 2

    def other_method(self):
        pass
'''

REVIEW_PY = '''
class ReviewMixin:
    def _persist_review_signals(self):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS review_signals (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                slug                   TEXT NOT NULL,
                agent                  TEXT,
                reviewed_at            TEXT NOT NULL,
                engagement_verdict     TEXT,
                shadow_bullet_hits     INTEGER,
                shadow_academic_jargon TEXT,
                shadow_corporate_cliches TEXT,
                shadow_truncated_ending TEXT,
                UNIQUE(slug, reviewed_at)
            )
        """)
        for _col in ("plan_follow_read TEXT", "shadow_seam_hits TEXT",
                     "pre_rewrite_plan_follow_read TEXT", "shadow_repetition_hits TEXT",
                     "shadow_length_adherence TEXT", "shadow_stop_risk_score INTEGER",
                     "shadow_stop_risk_reason TEXT"):
            try:
                conn.execute(f"ALTER TABLE review_signals ADD COLUMN {_col}")
            except Exception:
                pass
'''

CJ2_SHADOW_PY = '''
import os

_MODE_OFF = "OFF"


def _current_integration_mode():
    return os.environ.get("CJ2_INTEGRATION_MODE", _MODE_OFF).strip().upper()


class CJ2ShadowMixin:
    def _persist_cj2_shadow_run(self, record):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cj2_shadow_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT,
                bridge_valid INTEGER
            )
        """)
'''

TESTIMONY_L2_PY = '''
import os

_MODE_OFF = "OFF"


def _current_l2_mode():
    return os.environ.get("L2_TESTIMONY_MODE", _MODE_OFF).strip().upper()


class TestimonyL2Mixin:
    def _persist_l2_testimony_run(self, record):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS l2_testimony_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT,
                testimony_needed INTEGER
            )
        """)
'''


class Fixture:
    """A throwaway repo with just enough real source shape for
    natural_run_health_check.py's source-parsing/import logic to work
    against, plus helpers to vary the DB/log/posts per scenario."""

    def __init__(self, tmp, generate_py=GENERATE_PY_SAFE):
        self.root = Path(tmp)
        (self.root / "automation" / "orchestrator").mkdir(parents=True)
        (self.root / "_posts").mkdir(parents=True)

        (self.root / "automation" / "orchestrator" / "generate.py").write_text(generate_py)
        (self.root / "automation" / "orchestrator" / "review.py").write_text(REVIEW_PY)
        (self.root / "automation" / "orchestrator" / "cj2_shadow.py").write_text(CJ2_SHADOW_PY)
        (self.root / "automation" / "orchestrator" / "testimony_l2.py").write_text(TESTIMONY_L2_PY)
        (self.root / "automation" / "__init__.py").write_text("")
        (self.root / "automation" / "orchestrator" / "__init__.py").write_text("")

        sh(self.root, "init", "-q", "-b", "main")
        sh(self.root, "-c", "user.email=t@example.com", "-c", "user.name=T",
           "add", "-A")
        sh(self.root, "-c", "user.email=t@example.com", "-c", "user.name=T",
           "commit", "-q", "-m", "release baseline")
        self.since_sha = sh(self.root, "rev-parse", "HEAD").strip()

    def add_post(self, slug, fact_check_status=None):
        fm = "---\ntitle: test\n"
        if fact_check_status:
            fm += f"fact_check_status: {fact_check_status}\n"
        fm += "---\nBody text.\n"
        path = f"_posts/{slug}.md"
        (self.root / path).write_text(fm)
        sh(self.root, "add", path)
        sh(self.root, "-c", "user.email=bot@example.com", "-c", "user.name=Bot",
           "commit", "-q", "-m", f"Add new article: {slug}")
        return path

    def make_engagement_db(self, schema="full", rows=None):
        db_path = self.root / "automation" / "engagement.db"
        conn = sqlite3.connect(db_path)
        if schema == "none":
            conn.close()
            db_path.unlink()
            return db_path
        if schema == "old":
            conn.execute("""
                CREATE TABLE review_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT, agent TEXT, reviewed_at TEXT,
                    engagement_verdict TEXT, shadow_bullet_hits INTEGER,
                    shadow_academic_jargon TEXT, shadow_corporate_cliches TEXT,
                    shadow_truncated_ending TEXT
                )
            """)
        elif schema == "full":
            conn.execute("""
                CREATE TABLE review_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT, agent TEXT, reviewed_at TEXT,
                    engagement_verdict TEXT, shadow_bullet_hits INTEGER,
                    shadow_academic_jargon TEXT, shadow_corporate_cliches TEXT,
                    shadow_truncated_ending TEXT, plan_follow_read TEXT,
                    shadow_seam_hits TEXT, pre_rewrite_plan_follow_read TEXT,
                    shadow_repetition_hits TEXT, shadow_length_adherence TEXT,
                    shadow_stop_risk_score INTEGER, shadow_stop_risk_reason TEXT
                )
            """)
        for row in (rows or []):
            cols = ", ".join(row.keys())
            placeholders = ", ".join("?" for _ in row)
            conn.execute(f"INSERT INTO review_signals ({cols}) VALUES ({placeholders})",
                         list(row.values()))
        conn.commit()
        conn.close()
        return db_path

    def make_log(self, kind="clean"):
        log_path = self.root / "automation.log"
        if kind == "clean":
            log_path.write_text("[t] === cripminds orchestrator ===\n[t] orchestrator done\n")
        elif kind == "wrapper_error":
            log_path.write_text(
                "[t] === cripminds orchestrator ===\n[t] ERROR: orchestrator failed\n"
            )
        elif kind == "traceback":
            log_path.write_text(
                "[t] === cripminds orchestrator ===\nTraceback (most recent call last):\n"
                "  File x\nRuntimeError: boom\n"
            )
        elif kind == "none":
            if log_path.exists():
                log_path.unlink()
        return log_path


def with_fixture(generate_py=GENERATE_PY_SAFE):
    def deco(fn):
        def wrapper():
            tmp = tempfile.mkdtemp(prefix="health_check_test_")
            old_cj2 = os.environ.pop("CJ2_INTEGRATION_MODE", None)
            old_l2 = os.environ.pop("L2_TESTIMONY_MODE", None)
            try:
                fx = Fixture(tmp, generate_py=generate_py)
                fn(fx)
            finally:
                if old_cj2 is not None:
                    os.environ["CJ2_INTEGRATION_MODE"] = old_cj2
                else:
                    os.environ.pop("CJ2_INTEGRATION_MODE", None)
                if old_l2 is not None:
                    os.environ["L2_TESTIMONY_MODE"] = old_l2
                else:
                    os.environ.pop("L2_TESTIMONY_MODE", None)
                shutil.rmtree(tmp, ignore_errors=True)
        return wrapper
    return deco


# ---------------------------------------------------------------------------

@with_fixture()
def case_no_run_yet(fx):
    fx.make_log(kind="none")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("no run yet: run_found False", report["run_found"] is False)
    check("no run yet: status PASS (absence of a run is not a failure)", report["status"] == "PASS")


@with_fixture()
def case_missing_schema(fx):
    fx.make_engagement_db(schema="none")
    fx.add_post("2026-08-15-first")
    fx.make_log(kind="clean")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("missing schema: run_found True", report["run_found"] is True)
    check("missing schema: status FAIL (review_signals should exist after a completed run)",
          report["status"] == "FAIL")
    check("missing schema: infrastructure_errors mentions the missing engagement.db",
          any("engagement.db" in e for e in report["infrastructure_errors"]))


@with_fixture()
def case_old_schema_missing_new_columns(fx):
    fx.make_engagement_db(schema="old")
    fx.add_post("2026-08-15-first")
    fx.make_log(kind="clean")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("old schema: status FAIL", report["status"] == "FAIL")
    missing = report["schema"]["tables"]["review_signals"]["missing_columns"]
    check("old schema: missing_columns includes the new observer columns",
          "shadow_repetition_hits" in missing and "shadow_stop_risk_score" in missing)


@with_fixture()
def case_partial_run_observers_null(fx):
    slug = "2026-08-15-partial"
    fx.make_engagement_db(schema="full", rows=[{
        "slug": slug, "agent": "Pixel", "reviewed_at": "2026-08-15T09:00:00Z",
        "engagement_verdict": None,
        "shadow_repetition_hits": None, "shadow_length_adherence": None,
        "shadow_stop_risk_score": None, "shadow_stop_risk_reason": None,
    }])
    fx.add_post(slug)
    fx.make_log(kind="clean")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("partial run: row found", report["observers"]["row_found"] is True)
    check("partial run: engagement_verdict_present False",
          report["observers"]["engagement_verdict_present"] is False)
    check("partial run: all observer columns present but null",
          all(v is False for v in report["observers"]["observers"].values()))
    check("partial run: schema itself is still healthy (status PASS -- null values "
          "aren't a schema problem)", report["status"] == "PASS")


@with_fixture()
def case_completed_run_clean(fx):
    slug = "2026-08-15-complete"
    fx.make_engagement_db(schema="full", rows=[{
        "slug": slug, "agent": "Pixel", "reviewed_at": "2026-08-15T09:00:00Z",
        "engagement_verdict": "would finish",
        "shadow_repetition_hits": "[]", "shadow_length_adherence": "{}",
        "shadow_stop_risk_score": 2, "shadow_stop_risk_reason": "NONE",
    }])
    fx.add_post(slug, fact_check_status="verified")
    fx.make_log(kind="clean")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("completed run: status PASS", report["status"] == "PASS")
    check("completed run: policy_block False", report["policy_block"] is False)
    check("completed run: all observers non-null",
          all(v is True for v in report["observers"]["observers"].values()))
    check("completed run: no missing schema columns",
          report["schema"]["tables"]["review_signals"]["missing_columns"] == [])


@with_fixture()
def case_legitimate_editorial_block(fx):
    slug = "2026-08-15-blocked"
    fx.make_engagement_db(schema="full", rows=[{
        "slug": slug, "agent": "Pixel", "reviewed_at": "2026-08-15T09:00:00Z",
        "engagement_verdict": "would stop early",
        "shadow_repetition_hits": "[]", "shadow_length_adherence": "{}",
        "shadow_stop_risk_score": 5, "shadow_stop_risk_reason": "delayed payoff",
    }])
    fx.add_post(slug, fact_check_status="blocked")
    fx.make_log(kind="clean")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("editorial block: policy_block True", report["policy_block"] is True)
    check("editorial block: status STILL PASS (a legitimate block is not an infra failure)",
          report["status"] == "PASS")


@with_fixture()
def case_infrastructure_failure_wrapper_error(fx):
    fx.make_engagement_db(schema="full")
    fx.make_log(kind="wrapper_error")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("infra failure (wrapper error): status FAIL", report["status"] == "FAIL")
    check("infra failure (wrapper error): reported in infrastructure_errors",
          any("orchestrator failed" in e for e in report["infrastructure_errors"]))


@with_fixture()
def case_infrastructure_failure_traceback(fx):
    fx.make_engagement_db(schema="full")
    fx.make_log(kind="traceback")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("infra failure (traceback): status FAIL", report["status"] == "FAIL")
    check("infra failure (traceback): reported in infrastructure_errors",
          any("traceback" in e.lower() for e in report["infrastructure_errors"]))


@with_fixture()
def case_cj2_l2_off_tables_absent_not_flagged(fx):
    slug = "2026-08-15-modesoff"
    fx.make_engagement_db(schema="full", rows=[{
        "slug": slug, "agent": "Pixel", "reviewed_at": "2026-08-15T09:00:00Z",
        "engagement_verdict": "ok",
        "shadow_repetition_hits": "[]", "shadow_length_adherence": "{}",
        "shadow_stop_risk_score": 1, "shadow_stop_risk_reason": "NONE",
    }])
    fx.add_post(slug, fact_check_status="verified")
    fx.make_log(kind="clean")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("CJ2/L2 OFF: cj2_shadow_runs_table_expected False",
          report["feature_modes"]["cj2_shadow_runs_table_expected"] is False)
    check("CJ2/L2 OFF: l2_testimony_runs_table_expected False",
          report["feature_modes"]["l2_testimony_runs_table_expected"] is False)
    check("CJ2/L2 OFF: absent tables not in infrastructure_errors",
          not any("cj2_shadow_runs" in e or "l2_testimony_runs" in e
                  for e in report["infrastructure_errors"]))
    check("CJ2/L2 OFF: overall status PASS", report["status"] == "PASS")


@with_fixture()
def case_accidental_mode_activation_flagged(fx):
    os.environ["CJ2_INTEGRATION_MODE"] = "SHADOW"
    fx.make_engagement_db(schema="full")
    fx.make_log(kind="clean")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("accidental activation: cj2_integration_mode reported as SHADOW",
          report["feature_modes"]["cj2_integration_mode"] == "SHADOW")
    check("accidental activation: flagged in infrastructure_errors, never silent",
          any("cj2=SHADOW" in e for e in report["infrastructure_errors"]))
    check("accidental activation: overall status FAIL", report["status"] == "FAIL")


@with_fixture(generate_py=GENERATE_PY_LEAKED)
def case_shadow_field_leaked_into_blocking_authority(fx):
    fx.make_engagement_db(schema="full")
    fx.make_log(kind="clean")
    report = hc.run_health_check(repo=fx.root, since_sha=fx.since_sha)
    check("leaked authority: authority_boundaries.safe False",
          report["authority_boundaries"]["safe"] is False)
    check("leaked authority: shadow_repetition_hits flagged as leaked",
          "shadow_repetition_hits" in report["authority_boundaries"]["shadow_fields_leaked_into_blocking_policy"])
    check("leaked authority: overall status FAIL", report["status"] == "FAIL")


if __name__ == "__main__":
    case_no_run_yet()
    case_missing_schema()
    case_old_schema_missing_new_columns()
    case_partial_run_observers_null()
    case_completed_run_clean()
    case_legitimate_editorial_block()
    case_infrastructure_failure_wrapper_error()
    case_infrastructure_failure_traceback()
    case_cj2_l2_off_tables_absent_not_flagged()
    case_accidental_mode_activation_flagged()
    case_shadow_field_leaked_into_blocking_authority()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
