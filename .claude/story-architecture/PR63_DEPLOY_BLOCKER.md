# PR #63 — HARD DEPLOYMENT BLOCKER

**This PR must not merge or go live until the four conditions below hold and are
verified.** It is independent of the composition engine's correctness. The editorial
pipeline passing every gate — safety, Grounder, Fact Check, Reader — does not touch it.

A green canary is not permission to deploy.

## Required before merge/deploy

1. **A failed code update aborts production.** No article run may proceed on a failed
   update.
2. **Untracked collisions abort loudly.** No silent overwrite, no silent skip.
3. **Stale code cannot continue running** after a failed update.
4. **The deployed `CODE_SHA` is explicitly verified equal to the intended merged SHA.**

## Why this is not theoretical

The cripminds production checkout is `/srv/data/hermes/workspace/disability-ai-collective`.
When this campaign began it sat on PR #61 (`40be348`) while `origin/main` was already at
PR #62 (`6677e33`) — production was two PRs behind and nothing said so.

The daily job is `/srv/scripts/ops/cripminds-daily.sh`, a git-pull-then-run shape under
jascha's crontab. That is precisely the arrangement in which a failed pull runs stale
code and reports success: the pull's exit status is not the run's gate, and the run has
no idea which SHA it is executing.

`COMPOSITION_ENGINE` defaults to `legacy`, so merging alone changes no behaviour. The
blocker is on the deploy path, not the flag.

## Status

NOT BUILT. Nothing in PR #63 addresses it, and PR #63 must not be read as having done so.
