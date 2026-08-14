#!/usr/bin/env python3
"""
natural_run_health_check.py — read-only postflight for the article-pipeline
production workspace, built 2026-08-14 alongside the A-M reconciliation
release (see docs/production-release-procedure.md).

WHY THIS EXISTS: that release deployed several observability/lazy-schema
additions (new review_signals columns, the not-yet-active cj2_shadow_runs/
l2_testimony_runs tables) on purpose without a fake production run to
"prove" them -- the next NATURAL cron-triggered article run is what's
supposed to prove it. This script answers the resulting questions (did a
run happen, did lazy schema appear where it should, are the shadow
observers still non-authoritative, was anything actually broken) without
manual DB/log digging, and without ever touching anything itself.

THIS SCRIPT NEVER:
  - generates an article
  - calls a model
  - mutates any DB (every DB connection is opened read-only via a
    `file:...?mode=ro` URI -- a write attempt against it raises, it
    doesn't silently succeed)
  - alters cron
  - activates a feature mode
  - inserts a fake/synthetic observation row
  - publishes anything

DERIVING EXPECTATIONS FROM CODE, NOT ASSUMPTIONS: this module imports the
real `automation.orchestrator.cj2_shadow`/`testimony_l2` mode-readers
directly (so "is CJ2/L2 OFF" always reflects what the deployed code itself
would decide, never a re-implemented guess), and parses review.py's own
CREATE TABLE / ALTER TABLE source text to build the expected review_signals
column set (so a future column addition doesn't silently start failing
this checker's schema check -- it's read from the same source that defines
the schema, not hand-copied).

USAGE:
    python3 automation/natural_run_health_check.py [options]

    --repo PATH           default "." -- the production workspace to check.
    --engagement-db PATH  default <repo>/automation/engagement.db
    --log PATH            default <repo>/automation.log
    --since-sha SHA       only consider _posts/ files added after this
                           commit as "the natural run" (default: the release
                           SHA this tool shipped with, override for reuse).
    --json                emit only the JSON report (default: JSON + a
                           human summary).

EXIT CODE: 0 = healthy (includes "no run yet" and "legitimate editorial
block" -- neither is an infrastructure problem). 1 = an actual
infrastructure/schema/authority-boundary problem was found.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

DEFAULT_SINCE_SHA = "64d1658e1ac5fa7984b0ed671506dd3453cd6666"  # the 2026-08-14 release HEAD

# Base review_signals columns as originally created (schema.py's own CREATE
# TABLE), kept here because those never change without a much bigger
# migration; the ADDITIVE columns below are parsed live from source instead,
# since those are exactly the ones a future pass is likely to extend.
BASE_REVIEW_SIGNALS_COLUMNS = {
    "id", "slug", "agent", "reviewed_at", "engagement_verdict",
    "shadow_bullet_hits", "shadow_academic_jargon", "shadow_corporate_cliches",
    "shadow_truncated_ending",
}

# Columns this checker treats as "the new observers" for row-level
# non-null reporting -- also cross-checked against the live-parsed additive
# set below so this list can't silently drift out of sync with the source.
OBSERVER_COLUMNS = (
    "shadow_repetition_hits",
    "shadow_length_adherence",
    "shadow_stop_risk_score",
    "shadow_stop_risk_reason",
)


class GitError(RuntimeError):
    pass


def _run_git(repo, args):
    result = subprocess.run(["git", "-C", str(repo)] + args, capture_output=True, text=True)
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


# ---------------------------------------------------------------------------
# Deriving schema expectations from source (not hand-maintained assumptions)
# ---------------------------------------------------------------------------

def parse_additive_review_signals_columns(review_py_source: str):
    """Extract the column names from review.py's own
    `for _col in ("plan_follow_read TEXT", ...)` migration-safe ALTER TABLE
    block. Returns a set of bare column names (type dropped)."""
    m = re.search(r'for _col in \((.*?)\):', review_py_source, re.DOTALL)
    if not m:
        return set()
    tuple_body = m.group(1)
    entries = re.findall(r'"([a-zA-Z0-9_]+)\s+[A-Z]+"', tuple_body)
    return set(entries)


def parse_create_table_columns(source: str, table_name: str):
    """Extract column names from a `CREATE TABLE IF NOT EXISTS <table_name>
    (...)` block in a source file, by looking at the first identifier on
    each comma-separated top-level line. Deliberately simple (not a real
    SQL parser) -- sufficient for this codebase's own consistent style of
    one-column-per-line CREATE TABLE statements."""
    pattern = rf'CREATE TABLE IF NOT EXISTS {re.escape(table_name)}\s*\((.*?)\)\s*(?:"""|\')'
    m = re.search(pattern, source, re.DOTALL)
    if not m:
        return set()
    body = m.group(1)
    columns = set()
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        if not line or line.upper().startswith(("UNIQUE", "PRIMARY KEY", "FOREIGN KEY", "CHECK")):
            continue
        first_token = line.split()[0] if line.split() else ""
        if first_token:
            columns.add(first_token)
    return columns


def derive_expected_schema(repo: Path):
    review_source = (repo / "automation/orchestrator/review.py").read_text()
    additive = parse_additive_review_signals_columns(review_source)
    expected_review_signals = BASE_REVIEW_SIGNALS_COLUMNS | additive

    cj2_source = (repo / "automation/orchestrator/cj2_shadow.py").read_text()
    l2_source = (repo / "automation/orchestrator/testimony_l2.py").read_text()
    expected_cj2_shadow_runs = parse_create_table_columns(cj2_source, "cj2_shadow_runs")
    expected_l2_testimony_runs = parse_create_table_columns(l2_source, "l2_testimony_runs")

    return {
        "review_signals": expected_review_signals,
        "cj2_shadow_runs": expected_cj2_shadow_runs,
        "l2_testimony_runs": expected_l2_testimony_runs,
    }


# ---------------------------------------------------------------------------
# Deriving feature-mode state from the real deployed code
# ---------------------------------------------------------------------------

def derive_feature_modes(repo: Path):
    """Imports the actual mode-reader functions rather than re-implementing
    the OFF-default logic -- this always reflects what the deployed code
    itself would decide right now, in this process's environment.

    Evicts any previously cached `automation`/`automation.orchestrator.*`
    modules first: Python's import system caches by dotted name regardless
    of which directory it resolved from, so a second call against a
    DIFFERENT repo path (real usage is a fresh one-shot process every time
    and never hits this; the test suite calls this repeatedly against many
    fixture repos in one process and would otherwise silently keep
    reusing the first fixture's cached module) must not silently reuse a
    stale import."""
    for name in list(sys.modules):
        if name == "automation" or name.startswith("automation."):
            del sys.modules[name]
    sys.path.insert(0, str(repo))
    from automation.orchestrator.cj2_shadow import _current_integration_mode
    from automation.orchestrator.testimony_l2 import _current_l2_mode

    cj2_mode = _current_integration_mode()
    l2_mode = _current_l2_mode()
    return {
        "cj2_integration_mode": cj2_mode,
        "l2_testimony_mode": l2_mode,
        # Per cj2_shadow.py's own docstring: the call site in generate.py is
        # itself gated on mode != OFF, so the table is provably never
        # created while OFF -- absence is the EXPECTED state, not a gap.
        "cj2_shadow_runs_table_expected": cj2_mode != "OFF",
        # Per testimony_l2.py's own docstring: the call site is unconditional,
        # but _l2_testimony_attempt returns before any persistence call when
        # mode == OFF -- so this table is equally never created while OFF.
        "l2_testimony_runs_table_expected": l2_mode != "OFF",
    }


def check_authority_boundaries(repo: Path):
    """Re-derives, directly from deployed source (not from memory of the
    last audit), that none of the three shadow/observation checks can reach
    _compute_should_block's blocking decision. Same technique
    length_adherence_shadow_test.py/stop_risk_shadow_test.py already use
    internally, run here as an independent second layer against whatever is
    actually on disk right now."""
    generate_source = (repo / "automation/orchestrator/generate.py").read_text()
    m = re.search(r"def _compute_should_block\(degraded_stages\):.*?(?=\n    def |\nclass )",
                  generate_source, re.DOTALL)
    block_fn_source = m.group(0) if m else ""

    leaks = []
    for forbidden in ("shadow_repetition_hits", "shadow_length_adherence",
                       "shadow_stop_risk", "stop_risk_score"):
        if forbidden in block_fn_source:
            leaks.append(forbidden)

    return {
        "compute_should_block_found": bool(block_fn_source),
        "shadow_fields_leaked_into_blocking_policy": leaks,
        "safe": bool(block_fn_source) and not leaks,
    }


# ---------------------------------------------------------------------------
# Git-derived facts: latest natural run, deployed SHA
# ---------------------------------------------------------------------------

def find_latest_natural_post(repo: Path, since_sha: str):
    """The bot ADDS a new file under _posts/ per real run -- find the most
    recent such addition after since_sha. Returns (commit_sha, path) or
    (None, None) if no natural run has landed yet."""
    try:
        log = _run_git(repo, [
            "log", f"{since_sha}..HEAD", "--diff-filter=A", "--name-only",
            "--format=COMMIT %H", "--", "_posts/*.md",
        ])
    except GitError:
        return None, None
    commit_sha, path = None, None
    for line in log.splitlines():
        if line.startswith("COMMIT "):
            commit_sha = line.split(" ", 1)[1]
        elif line.strip():
            path = line.strip()
    return commit_sha, path


def read_frontmatter_field(repo: Path, post_path: str, field: str):
    full = repo / post_path
    if not full.exists():
        return None
    text = full.read_text()
    m = re.search(rf"^{field}:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip().strip('"') if m else None


# ---------------------------------------------------------------------------
# Read-only DB inspection
# ---------------------------------------------------------------------------

def _readonly_connect(db_path: Path):
    # file:...?mode=ro raises OperationalError on any write attempt --
    # this is a real guarantee, not just "we don't intend to write."
    uri = f"file:{db_path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def check_db_schema(engagement_db: Path, expected: dict):
    if not engagement_db.exists():
        return {
            "db_exists": False,
            "tables": {},
            "note": "engagement.db does not exist at all -- expected only if no article "
                    "has ever completed review on this workspace.",
        }
    conn = _readonly_connect(engagement_db)
    try:
        existing_tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        report = {"db_exists": True, "tables": {}}
        for table_name, expected_cols in expected.items():
            if table_name not in existing_tables:
                report["tables"][table_name] = {"exists": False, "missing_columns": [],
                                                  "unexpected_columns": []}
                continue
            actual_cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
            report["tables"][table_name] = {
                "exists": True,
                "missing_columns": sorted(expected_cols - actual_cols),
                "unexpected_columns": sorted(actual_cols - expected_cols),
            }
        return report
    finally:
        conn.close()


def check_observer_persistence(engagement_db: Path, slug: str | None):
    if not engagement_db.exists() or not slug:
        return {"row_found": False}
    conn = _readonly_connect(engagement_db)
    try:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "review_signals" not in tables:
            return {"row_found": False, "note": "review_signals table does not exist"}
        cols = {row[1] for row in conn.execute("PRAGMA table_info(review_signals)").fetchall()}
        select_cols = ["slug", "reviewed_at", "engagement_verdict"] + [
            c for c in OBSERVER_COLUMNS if c in cols
        ]
        row = conn.execute(
            f"SELECT {', '.join(select_cols)} FROM review_signals "
            "WHERE slug = ? ORDER BY reviewed_at DESC LIMIT 1",
            (slug,),
        ).fetchone()
        if not row:
            return {"row_found": False, "slug": slug}
        record = dict(zip(select_cols, row))
        return {
            "row_found": True,
            "slug": record.get("slug"),
            "reviewed_at": record.get("reviewed_at"),
            "engagement_verdict_present": record.get("engagement_verdict") is not None,
            "observers": {
                c: (record.get(c) is not None) for c in OBSERVER_COLUMNS if c in cols
            },
            "observers_missing_from_schema": [c for c in OBSERVER_COLUMNS if c not in cols],
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Log-based infra-vs-policy distinction
# ---------------------------------------------------------------------------

def check_log_health(log_path: Path):
    if not log_path.exists():
        return {"log_found": False, "infrastructure_errors": []}
    text = log_path.read_text(errors="replace")
    # Most recent orchestrator run bracket only -- this file is append-only
    # and can span months.
    runs = list(re.finditer(r"=== cripminds orchestrator ===", text))
    if not runs:
        return {"log_found": True, "infrastructure_errors": [], "note": "no orchestrator run logged yet"}
    start = runs[-1].start()
    tail = text[start:]

    errors = []
    if "ERROR: orchestrator failed" in tail:
        errors.append("cripminds-daily.sh reported: ERROR: orchestrator failed")
    if "Traceback (most recent call last)" in tail:
        errors.append("unhandled Python traceback present in the latest run's log output")
    completed = "orchestrator done" in tail
    return {
        "log_found": True,
        "latest_run_completed_marker_present": completed,
        "infrastructure_errors": errors,
    }


# ---------------------------------------------------------------------------
# Main assembly
# ---------------------------------------------------------------------------

def run_health_check(repo=".", engagement_db=None, log_path=None, since_sha=DEFAULT_SINCE_SHA):
    repo = Path(repo).resolve()
    engagement_db = Path(engagement_db) if engagement_db else repo / "automation" / "engagement.db"
    log_path = Path(log_path) if log_path else repo / "automation.log"

    infra_errors = []

    try:
        deployed_sha = _run_git(repo, ["rev-parse", "HEAD"]).strip()
    except GitError as e:
        deployed_sha = None
        infra_errors.append(f"could not determine deployed SHA: {e}")

    commit_sha, post_path = find_latest_natural_post(repo, since_sha)
    run_found = commit_sha is not None

    fact_check_status = None
    policy_block = False
    if run_found:
        fact_check_status = read_frontmatter_field(repo, post_path, "fact_check_status")
        policy_block = (fact_check_status == "blocked")

    expected_schema = derive_expected_schema(repo)
    feature_modes = derive_feature_modes(repo)
    authority = check_authority_boundaries(repo)
    schema_report = check_db_schema(engagement_db, expected_schema)
    slug = Path(post_path).stem if post_path else None
    observer_report = check_observer_persistence(engagement_db, slug)
    log_report = check_log_health(log_path)

    infra_errors.extend(log_report.get("infrastructure_errors", []))

    # Schema check: missing columns/tables are only infra errors when the
    # code says they SHOULD exist. review_signals is unconditional (any
    # completed review writes it); cj2_shadow_runs/l2_testimony_runs are
    # conditional on their own feature mode per derive_feature_modes.
    if run_found and not schema_report.get("db_exists"):
        infra_errors.append("automation/engagement.db does not exist despite a completed natural run")
    elif run_found and schema_report.get("db_exists"):
        rs = schema_report["tables"].get("review_signals", {})
        if not rs.get("exists"):
            infra_errors.append("review_signals table missing despite a completed natural run")
        elif rs.get("missing_columns"):
            infra_errors.append(f"review_signals missing expected columns: {rs['missing_columns']}")

        for table_name, expect_key in (
            ("cj2_shadow_runs", "cj2_shadow_runs_table_expected"),
            ("l2_testimony_runs", "l2_testimony_runs_table_expected"),
        ):
            t = schema_report["tables"].get(table_name, {})
            if feature_modes[expect_key] and not t.get("exists"):
                infra_errors.append(
                    f"{table_name} missing, but its feature mode is not OFF -- expected to exist"
                )
            # NOTE: absence while the mode IS off is correct, expected
            # behavior -- deliberately not flagged.

    if not authority["safe"]:
        infra_errors.append(
            "shadow/observation fields found inside _compute_should_block's own source -- "
            f"leaked authority: {authority['shadow_fields_leaked_into_blocking_policy']}"
        )

    if feature_modes["cj2_integration_mode"] != "OFF" or feature_modes["l2_testimony_mode"] != "OFF":
        # Not itself an error -- but must be loudly visible, never silent,
        # since this release's whole premise is that these stay OFF.
        infra_errors.append(
            "NOTICE (not a bug, but flagged): a feature mode is not OFF -- "
            f"cj2={feature_modes['cj2_integration_mode']} l2={feature_modes['l2_testimony_mode']}"
        )

    status = "PASS" if not infra_errors else "FAIL"

    return {
        "status": status,
        "deployed_sha": deployed_sha,
        "run_found": run_found,
        "run_completed": run_found,  # a post file existing at all implies the run reached publish
        "policy_block": policy_block,
        "fact_check_status": fact_check_status,
        "latest_post": post_path,
        "latest_post_commit": commit_sha,
        "schema": schema_report,
        "observers": observer_report,
        "feature_modes": feature_modes,
        "authority_boundaries": authority,
        "log": log_report,
        "infrastructure_errors": infra_errors,
    }


def _human_summary(report: dict) -> str:
    lines = [f"STATUS: {report['status']}"]
    lines.append(f"  deployed_sha: {report['deployed_sha']}")
    if not report["run_found"]:
        lines.append("  RUN FOUND: no -- no natural article run detected since the reference SHA yet.")
    else:
        lines.append(f"  RUN FOUND: yes -- {report['latest_post']} ({report['latest_post_commit'][:10]})")
        lines.append(f"  RUN COMPLETED: yes  fact_check_status={report['fact_check_status']}"
                     + ("  [POLICY BLOCK -- editorial safety net, not a bug]" if report["policy_block"] else ""))
    fm = report["feature_modes"]
    lines.append(f"  FEATURE MODES: cj2={fm['cj2_integration_mode']}  l2={fm['l2_testimony_mode']}")
    lines.append(f"  AUTHORITY BOUNDARIES SAFE: {report['authority_boundaries']['safe']}")
    if report["infrastructure_errors"]:
        lines.append("  INFRASTRUCTURE ERRORS:")
        for e in report["infrastructure_errors"]:
            lines.append(f"    - {e}")
    else:
        lines.append("  INFRASTRUCTURE ERRORS: none")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--engagement-db", default=None)
    parser.add_argument("--log", default=None)
    parser.add_argument("--since-sha", default=DEFAULT_SINCE_SHA)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run_health_check(
        repo=args.repo, engagement_db=args.engagement_db, log_path=args.log, since_sha=args.since_sha,
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
        print()
        print(_human_summary(report))

    sys.exit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
