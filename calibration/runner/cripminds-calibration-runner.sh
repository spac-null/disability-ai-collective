#!/usr/bin/env bash
# cripminds-calibration-runner — systemd ExecStart wrapper.
#
# Matches /srv/scripts/ops/cripminds-daily.sh's own git-pull-then-run
# convention on this host: the canonical source lives in the repo, this
# wrapper just makes sure the checkout is current before each service
# start/restart. A pull failure is non-fatal (log and continue on
# whatever's checked out) — same reasoning cripminds-daily.sh itself
# documents: a temporary network blip during a restart shouldn't take
# the whole calibration runner down.
set -euo pipefail

WORKSPACE=/srv/data/hermes/workspace/disability-ai-collective
LOG="$WORKSPACE/automation.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [calibration-runner] $*" | tee -a "$LOG"; }

cd "$WORKSPACE"
if ! git pull origin main >> "$LOG" 2>&1; then
    log "WARNING: git pull failed — continuing with whatever is checked out"
fi

log "starting calibration_runner.py"
exec python3 calibration/runner/calibration_runner.py
