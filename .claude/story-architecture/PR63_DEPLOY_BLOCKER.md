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

**CLEARED 2026-09-05.** Nothing in PR #63 addressed it, and PR #63 must still not be read
as having done so — it was built separately, on the deploy path, exactly where the blocker
said it belonged.

`/srv/scripts/ops/cripminds-deploy-guard.sh` now resolves the intended SHA before anything
runs, and `cripminds-daily.sh` aborts the run and alerts when the guard exits non-zero
instead of logging a warning and carrying on. Each condition, and how it was verified:

1. **A failed code update aborts production.** The guard's failure path prints
   `DEPLOY_STATUS=FAIL` with a `DEPLOY_ERROR` code; `run_article` exits 1 without
   reaching the pipeline.
2. **Untracked collisions abort loudly.** `DEPLOY_COLLISION` names the exact paths. The
   guard never stashes, resets or cleans — a person decides.
3. **Stale code cannot continue running.** A fetch failure is fatal rather than a reason
   to use what is on disk: a deploy that cannot name what it is deploying is not a deploy.
4. **`CODE_SHA` is explicitly verified.** The guard prints both `EXPECTED_CODE_SHA` and
   `LIVE_CODE_SHA`, and the run logs `DEPLOY_STATUS=PASS` only when they match.

Demonstrated live twice on 2026-09-05, deploying PR #65 and PR #66:

```
EXPECTED_CODE_SHA=e8b63788bb93b0f02c63ec3c7047bd21ecdb17e5
LIVE_CODE_SHA=e8b63788bb93b0f02c63ec3c7047bd21ecdb17e5
DEPLOY_STATUS=PASS
```

The rest of the document stands as written, including the reason it is not theoretical.
A green canary is still not permission to deploy.
