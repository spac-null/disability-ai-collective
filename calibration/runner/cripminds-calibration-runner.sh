#!/usr/bin/env bash
# cripminds-calibration-runner — systemd ExecStart wrapper.
#
# Checks out the pinned commit into its OWN dedicated git worktree
# (WORKSPACE/.calibration-checkout), never onto the shared content
# workspace's own working tree. This fixes a real incident: an earlier
# version of this script did `git checkout --detach <pin>` directly on
# the shared workspace, which collided with a separate, independent
# Trident automation (the daily content-publishing bot, same convention
# as cripminds-daily.sh) that also commits directly to this same repo's
# `main` branch. Two unrelated automations sharing one mutable working
# tree, with different assumptions about what HEAD should be, is the
# actual bug — not something either side did wrong on its own. A
# dedicated worktree (still inside this service's existing
# ReadWritePaths, since it's a subdirectory — no systemd unit change
# needed) gives this service its own working tree while the shared
# workspace stays on `main`, untouched, for the other automation.
#
# Pinned to an explicit commit SHA read from
# /srv/secrets/cripminds-calibration/deployed-commit-sha.txt. Updating
# that file (a deliberate, reviewed, one-line act — never something this
# script or the runner itself writes) is the entire "deploy a new runner
# version" step; restarting the service with an unchanged pin file
# re-checks out the exact same commit, so a crash-restart loop can never
# silently pick up in-progress work from a half-pushed branch.
#
# Falls back to tracking origin/main ONLY if the pin file doesn't exist
# yet (first install, before anyone has pinned a commit) — never falls
# back silently once a pin file exists and a checkout fails; a
# missing/unreachable pinned commit is a real error worth surfacing, not
# something to paper over by drifting back to `main`.
set -euo pipefail

WORKSPACE=/srv/data/hermes/workspace/disability-ai-collective
CHECKOUT_DIR="$WORKSPACE/.calibration-checkout"
LOG="$WORKSPACE/automation.log"
PIN_FILE=/srv/secrets/cripminds-calibration/deployed-commit-sha.txt

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [calibration-runner] $*" | tee -a "$LOG"; }

cd "$WORKSPACE"
git fetch origin main >> "$LOG" 2>&1 || log "WARNING: git fetch failed — continuing with whatever is checked out"

worktree_exists() { git -C "$WORKSPACE" worktree list | grep -qF "$CHECKOUT_DIR"; }

if [ -f "$PIN_FILE" ]; then
    PINNED_SHA=$(tr -d '[:space:]' < "$PIN_FILE")
    if [ -z "$PINNED_SHA" ]; then
        log "ERROR: $PIN_FILE exists but is empty — refusing to start rather than guess a revision"
        exit 1
    fi
    if worktree_exists; then
        if ! git -C "$CHECKOUT_DIR" checkout --detach "$PINNED_SHA" >> "$LOG" 2>&1; then
            log "ERROR: could not check out pinned commit $PINNED_SHA in $CHECKOUT_DIR — refusing to start"
            exit 1
        fi
    else
        if ! git worktree add --detach "$CHECKOUT_DIR" "$PINNED_SHA" >> "$LOG" 2>&1; then
            log "ERROR: could not create dedicated worktree at $CHECKOUT_DIR for pinned commit $PINNED_SHA — refusing to start"
            exit 1
        fi
    fi
    log "checked out pinned commit $PINNED_SHA in $CHECKOUT_DIR"
else
    log "WARNING: no pin file at $PIN_FILE — falling back to a worktree tracking origin/main (first-install state; pin a commit to stop seeing this)"
    if worktree_exists; then
        if ! git -C "$CHECKOUT_DIR" pull origin main >> "$LOG" 2>&1; then
            log "WARNING: git pull failed in $CHECKOUT_DIR — continuing with whatever is checked out"
        fi
    else
        if ! git worktree add "$CHECKOUT_DIR" main >> "$LOG" 2>&1; then
            log "ERROR: could not create fallback worktree at $CHECKOUT_DIR — refusing to start"
            exit 1
        fi
    fi
fi

log "starting calibration_runner.py from $CHECKOUT_DIR"
cd "$CHECKOUT_DIR"
exec python3 calibration/runner/calibration_runner.py
