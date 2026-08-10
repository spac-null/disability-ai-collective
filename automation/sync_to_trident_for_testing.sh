#!/usr/bin/env bash
# sync_to_trident_for_testing.sh — safe wrapper for syncing UNCOMMITTED local
# changes to trident's checkout for live testing before a real commit+push.
#
# Added 2026-08-10 after an incident: a plain `rsync -az automation/
# jascha@trident:.../automation/` command synced an empty local stub of
# automation/engagement.db over trident's real, populated copy, because *.db
# is gitignored (so it was never populated locally) and rsync does not
# consult .gitignore. See .claude/2026-08-10-engagement-db-incident.md.
#
# Real production deployment is git-based (push, then the daily cron's own
# `git pull`), which already respects .gitignore and was never at risk --
# this script exists only for the "test an uncommitted change live before
# committing" workflow this session has used repeatedly. Use THIS, not a
# raw rsync command, for that purpose from now on.
set -euo pipefail

TRIDENT_HOST="jascha@trident.tail630536.ts.net"
TRIDENT_PATH="/srv/data/hermes/workspace/disability-ai-collective/automation/"
LOCAL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/"

echo "Syncing $LOCAL_PATH -> $TRIDENT_HOST:$TRIDENT_PATH"
echo "(excluding all database/state files -- see script header)"

rsync -az \
  --exclude='*.db' \
  --exclude='*.db-wal' \
  --exclude='*.db-shm' \
  --exclude='*.db-journal' \
  --exclude='.snapshot_fixtures/*.json' \
  --exclude='probe_out/' \
  --exclude='.probe_fixtures/' \
  "$LOCAL_PATH" "$TRIDENT_HOST:$TRIDENT_PATH"

echo "Done. Verify with: ssh $TRIDENT_HOST 'md5sum $TRIDENT_PATH*.db' before/after if in doubt."
