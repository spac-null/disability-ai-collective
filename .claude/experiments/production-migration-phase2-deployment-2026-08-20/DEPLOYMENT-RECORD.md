# Phase-2 Capture — Deployment Record

**Deployed and enabled 2026-08-20. Sample collection is IN PROGRESS and cannot complete
in this session — see `STATUS.md`.**

## Pre-deploy correction

`capture()` and `seal()` caught `BaseException`, which would have swallowed `SystemExit`
and `KeyboardInterrupt`. Narrowed to `Exception` in five handlers. Ordinary failures are
still swallowed so a capture failure cannot alter, block or fail an article run; process
signals now propagate so the orchestrator shuts down cleanly.

No other change to the capture code. Commit `8c4b4a5` on the observability branch.

Two test defects were found and fixed alongside it, both cases of a test not exercising
what it claimed:

- `test_hooks_are_additive_only` diffed the working tree against `HEAD`, which is empty once
  the patch is committed — it proved nothing. Now diffs against the `8af3622` baseline.
- The ad-hoc signal check passed a payload that never reached a raising code path, so it
  reported "swallowed" for both signals even after the fix. Replaced with
  `test_process_signals_propagate`, which patches `SC._write` to raise and asserts
  `KeyboardInterrupt`/`SystemExit` escape while `RuntimeError` does not.

## Deployment source — verified

| Field | Value |
|---|---|
| Branch | `production-observability-2026-08-20` |
| Descends from | `8af3622` — verified, directly |
| Commits | `20a7e3a` (capture) + `8c4b4a5` (Exception fix) |
| Diff vs baseline | 3 files, **+572 / −0** |
| `.claude/` research files in the branch | **NONE** — verified by `git diff --name-only` |
| Legacy prompt changes | none |
| AR3 changes | none |
| writer/rewrite/gate/review behaviour changes | none |

## Trident

| | |
|---|---|
| HEAD before | `8af3622339210a9f13b96f944f028e8c28343f3e` — **unmoved since Phase 0**, working tree clean |
| Method | `git format-patch` → piped over ssh → `git am`. Exact commits preserved; no push, no research history transferred |
| HEAD after | `ad7b8c7f1dd8dc84c48ed1a892169dca41a6bbaa` |

Commit SHAs differ from local (`git am` re-stamps the committer) but **file content is
byte-identical**, verified by SHA-256 on all three files:

```
750b9d89…  automation/shadow_capture.py
5e45b47f…  automation/shadow_capture_test.py
21b0111b…  automation/orchestrator/generate.py
```

## Pre-enable safety checks — all passed, flag OFF

| Check | Result |
|---|---|
| capture safety tests on Trident | **39/39 pass** |
| `snapshot_test.py --check` | *"No drift — 6 article(s) match recorded fixtures"* |
| `production_orchestrator` imports | OK |
| capture artifacts written while OFF | **0** |
| writer SYSTEM hash | unchanged `c8ffc682…` |
| rewrite SYSTEM hash | unchanged `921c9076…` |
| `GATE_SYSTEM` hash | unchanged `19404edf…` |
| `RULES_SYSTEM` hash | unchanged `7ce0893a…` |
| `llm.py` / `gate.py` / `review.py` file hashes | identical to the Phase-0 baseline |
| AR3 rewrite 33 / 33b | **present and unchanged** (1 occurrence each) |
| `_posts` / `_drafts` counts | 142 / 7 — unchanged |
| SQLite schema/state | untouched |

## Capture root

| | |
|---|---|
| Path | `/srv/data/cripminds-shadow-capture` |
| Owner / mode | `jascha:jascha`, **700** — not world-readable |
| Writeable by the production job user | yes |
| Inside the repo / `_posts` / `_drafts` / a SQLite DB | no |
| Under `/srv/backups/cripminds` (14-day rotation) | **no** |
| Mixed with rotating logs | no — dedicated root |
| Disk | 18G free, 85% used |

## Enablement

| | |
|---|---|
| Enabled at | **2026-08-20T09:36:55Z** (11:36:55 CEST) |
| Method | `SHADOW_CAPTURE=1` prefixed to the **article** cron line only |
| Cron backup | `/srv/data/cripminds-shadow-capture/crontab.backup-before-capture-enable` |
| Lines changed | exactly 1 of 63 |
| Cron lines carrying the flag | 1 |
| Shadow V0 / new Discovery / Article Form / Writer / Writer Grounding | **NOT enabled** — passive legacy capture only |

**Flag propagation verified end-to-end**, not assumed: `cripminds-daily.sh` uses `set -a` +
`source` (which *adds* to the environment rather than clearing it), and `enabled()` returns
`True` through a nested shell exactly as cron will invoke it. Without this check, three days
could have passed with capture silently inert.

## Consequence that needs owner awareness

**Trident's `main` is now 2 commits ahead of `origin/main`, and production will push them to
the public GitHub repo automatically at the next article run.**

I did **not** push. But `publish.py::commit_to_git` calls `_git_push_safe()`, which runs
`git stash --include-untracked` → `git pull --rebase origin main` → `git push origin main` at
the end of every article run. So the observability commits reach public `origin/main` at
09:00 on 2026-08-21 regardless.

This is unavoidable given production's design — the only way to prevent it would be not to
deploy. It also drove the deployment method: an *uncommitted* working-tree patch would have
been stashed and popped on every run, and a single pop conflict would silently delete the
capture code mid-flight. Committing is the safe option.

The patch contains no secrets (the only credential-shaped strings are the literal marker
list the scanner uses to *refuse* secrets), and the repository already contains the entire
pipeline publicly. Risk assessed as low, but it is a real publication event and is recorded
here rather than left to surprise.

The divergence will not break tomorrow's run: `pull --rebase` is a no-op with origin
unmoved, and the push fast-forwards.

## Rollback

- **Disable capture:** restore the cron line — one token. Backup at the path above.
- **Revert the code:** `git revert ad7b8c7 445fbbc` on Trident. The patch is purely additive
  (+572 / −0), so a revert cannot damage legacy behaviour.
