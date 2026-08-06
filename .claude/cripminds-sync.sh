#!/bin/bash
# Keeps the local Mac clone of disability-ai-collective in step with the live
# pipeline checkout on trident (/srv/data/hermes/workspace/disability-ai-collective,
# run daily by cripminds-daily.sh via Hermes). Two things go stale locally:
#   1. git commits — trident commits + pushes to GitHub itself; local just
#      needs a fast-forward pull.
#   2. gitignored runtime state (_social/, automation.log, persona_state/,
#      bsky_engage_seen.json) — never committed by design (see .gitignore),
#      so a git pull alone never brings it over. Only a real sync catches it.
# Modeled on ~/code/trident/scripts/trident-sync.sh.
set -euo pipefail

TRIDENT="jascha@100.98.217.79"
REMOTE_REPO="/srv/data/hermes/workspace/disability-ai-collective"
LOCAL_REPO="$HOME/code/disability-collective-ai"
LOG="$LOCAL_REPO/.claude/sync.log"

log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"; }

cd "$LOCAL_REPO"

# 1. Fast-forward from GitHub (trident pushes here directly).
git fetch origin main --quiet
LOCAL_HEAD=$(git rev-parse HEAD)
REMOTE_HEAD=$(git rev-parse origin/main)
if [ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]; then
  log "origin/main has new commits ($LOCAL_HEAD -> $REMOTE_HEAD), pulling..."
  git merge origin/main --ff-only 2>&1 | tee -a "$LOG" || log "WARN: fast-forward failed — local has diverging commits, resolve manually"
else
  log "Git in sync ($LOCAL_HEAD)"
fi

# 2. Mirror gitignored runtime state from trident's live checkout (read-only,
# local is never the source of truth for these — trident always wins).
log "Syncing runtime state from trident..."
rsync -az --delete \
  "$TRIDENT:$REMOTE_REPO/_social/" \
  "$LOCAL_REPO/_social/" 2>&1 | tee -a "$LOG"

rsync -az \
  "$TRIDENT:$REMOTE_REPO/automation.log" \
  "$LOCAL_REPO/automation.log" 2>&1 | tee -a "$LOG"

rsync -az \
  "$TRIDENT:$REMOTE_REPO/automation/persona_state/" \
  "$LOCAL_REPO/automation/persona_state/" 2>&1 | tee -a "$LOG"

rsync -az \
  "$TRIDENT:$REMOTE_REPO/automation/bsky_engage_seen.json" \
  "$LOCAL_REPO/automation/bsky_engage_seen.json" 2>&1 | tee -a "$LOG"

log "Sync complete."
