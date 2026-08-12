#!/usr/bin/env bash
# cripminds-calibration-runner — systemd ExecStart wrapper.
#
# Pins the checkout to an explicit commit SHA read from
# /srv/secrets/cripminds-calibration/deployed-commit-sha.txt (root of the
# ReadOnlyPaths this service's systemd unit already grants it — see
# cripminds-calibration-runner.service) rather than tracking whatever
# `main` happens to be at restart time. Updating that file (a deliberate,
# reviewed, one-line act — never something this script or the runner
# itself writes) is now the entire "deploy a new runner version" step;
# restarting the service with an unchanged pin file re-checks out the
# exact same commit, so a crash-restart loop can never silently pick up
# in-progress work from a half-pushed branch.
#
# Falls back to the previous git-pull-main behavior ONLY if the pin file
# doesn't exist yet (first install, before anyone has pinned a commit) —
# never falls back silently once a pin file exists and a checkout fails;
# a missing/unreachable pinned commit is a real error worth surfacing,
# not something to paper over by drifting back to `main`.
set -euo pipefail

WORKSPACE=/srv/data/hermes/workspace/disability-ai-collective
LOG="$WORKSPACE/automation.log"
PIN_FILE=/srv/secrets/cripminds-calibration/deployed-commit-sha.txt

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [calibration-runner] $*" | tee -a "$LOG"; }

cd "$WORKSPACE"
git fetch origin main >> "$LOG" 2>&1 || log "WARNING: git fetch failed — continuing with whatever is checked out"

if [ -f "$PIN_FILE" ]; then
    PINNED_SHA=$(tr -d '[:space:]' < "$PIN_FILE")
    if [ -z "$PINNED_SHA" ]; then
        log "ERROR: $PIN_FILE exists but is empty — refusing to start rather than guess a revision"
        exit 1
    fi
    if ! git checkout --detach "$PINNED_SHA" >> "$LOG" 2>&1; then
        log "ERROR: could not check out pinned commit $PINNED_SHA — refusing to start"
        exit 1
    fi
    log "checked out pinned commit $PINNED_SHA"
else
    log "WARNING: no pin file at $PIN_FILE — falling back to tracking origin/main (first-install state; pin a commit to stop seeing this)"
    if ! git pull origin main >> "$LOG" 2>&1; then
        log "WARNING: git pull failed — continuing with whatever is checked out"
    fi
fi

log "starting calibration_runner.py"
exec python3 calibration/runner/calibration_runner.py
