#!/usr/bin/env python3
"""
backup_state_dbs.py — daily backup of this pipeline's stateful SQLite databases.

Added 2026-08-10 after automation/engagement.db was accidentally overwritten
by an rsync command that synced an empty local stub over trident's real,
populated copy (see .claude/2026-08-10-engagement-db-incident.md). These
files stopped being throwaway caches once real accumulation started
(engagement_metrics, review_signals, article_plans; discovery/news-seed
state in disability_findings.db) -- this is the minimum safety net until the
larger fix (moving persistent state out of the deployable repo tree
entirely) lands.

Uses SQLite's own backup API (Connection.backup), not a raw file copy --
safe even if a write happens to be mid-transaction, unlike `cp` or `rsync`
against a live database file.

Deliberately writes OUTSIDE this repo's own directory tree, so a future git
clean/checkout/worktree operation on the repo itself cannot touch backups.

USAGE (intended to run from cron, once daily):
    python3 automation/backup_state_dbs.py
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
BACKUP_DIR = Path("/srv/backups/cripminds")
RETENTION_DAYS = 14

DATABASES = [
    REPO_ROOT / "automation" / "engagement.db",
    REPO_ROOT / "disability_findings.db",
]


def backup_one(db_path, today):
    if not db_path.exists():
        print(f"SKIP {db_path.name}: does not exist")
        return True
    dest = BACKUP_DIR / f"{db_path.stem}-{today}.db"
    try:
        src = sqlite3.connect(str(db_path))
        dst = sqlite3.connect(str(dest))
        src.backup(dst)
        dst.close()
        src.close()
    except Exception as e:
        print(f"FAILED {db_path.name}: backup API error: {e}", file=sys.stderr)
        return False

    check_conn = sqlite3.connect(str(dest))
    result = check_conn.execute("PRAGMA integrity_check").fetchone()[0]
    check_conn.close()
    if result != "ok":
        print(f"FAILED {db_path.name}: backup copy failed integrity_check: {result}", file=sys.stderr)
        return False

    print(f"OK {db_path.name} -> {dest.name} ({dest.stat().st_size} bytes, integrity_check: {result})")
    return True


def prune_old(today):
    cutoff = datetime.strptime(today, "%Y-%m-%d")
    for f in BACKUP_DIR.glob("*.db"):
        try:
            date_str = f.stem.rsplit("-", 3)[-3:]  # e.g. engagement-2026-08-10 -> ['2026','08','10']
            file_date = datetime.strptime("-".join(date_str), "%Y-%m-%d")
        except (ValueError, IndexError):
            continue
        if (cutoff - file_date).days > RETENTION_DAYS:
            f.unlink()
            print(f"PRUNED {f.name} (older than {RETENTION_DAYS} days)")


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    ok = all(backup_one(db, today) for db in DATABASES)
    prune_old(today)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
