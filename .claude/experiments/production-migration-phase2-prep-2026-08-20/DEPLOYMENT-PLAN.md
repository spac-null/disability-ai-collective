# Deployment Plan

**NOT DEPLOYED. NOT PUSHED. FLAG NOT ENABLED. CRON UNCHANGED.**

The patch is deliberately left for review first.

## The deployable commit

| Field | Value |
|---|---|
| Worktree | `/Users/stargatesgx/code/disability-collective-ai-production-observability` |
| Branch | `production-observability-2026-08-20` |
| Based exactly on | `8af3622` — the frozen production baseline, = `origin/main` |
| Commit | **`20a7e3a`** — *feat: passive OFF-by-default production capture for phase-2 comparison* |
| Diff | 3 files, **+530 lines, 0 deletions**; `generate.py` is **+52, −0** |

The branch carries **none** of the local research/evidence history, so the commit is
independently cherry-pickable onto production and the deployment history stays unambiguous.

## Review checklist before deploying

1. Read the `generate.py` diff — 52 added lines, five one-line hooks, no deletion.
2. Confirm the storage root `/srv/data/cripminds-shadow-capture` is acceptable, and that it
   is outside the repo, outside `_posts`/`_drafts`, and outside `/srv/backups/cripminds`
   where 14-day rotation would delete bundles.
3. Confirm the secret-marker refusal list is adequate for this environment.
4. Note that with `SHADOW_CAPTURE` unset the patch is inert; deploying it does not enable it.

## Deployment sequence, when authorised

1. Cherry-pick `20a7e3a` onto `main`, push, and let Trident fast-forward — the existing
   `git pull origin main` pattern already in cron.
2. Verify file hashes match between Mac and Trident post-pull, as the AR3A release did.
3. Run `python3 automation/shadow_capture_test.py` **on Trident** — 36 checks, no network.
4. Run `python3 automation/snapshot_test.py --check` on Trident to confirm the legacy path is
   unchanged in the deployed tree.
5. Create the capture root: `mkdir -p /srv/data/cripminds-shadow-capture`.
6. Only then enable, by adding `SHADOW_CAPTURE=1` to the article cron's environment. **This
   is the single enabling step and is reversible by removing it.**
7. Confirm disk headroom first — Phase 0 recorded `/dev/nvme0n1p2` at 85% used, 18G free. A
   bundle is roughly the size of one source plus two article drafts, so a few hundred KB per
   run; three runs is negligible, but the root should be reviewed before long-term running.

## Rollback

- **Before enablement:** nothing to roll back; the code is inert.
- **After enablement:** remove `SHADOW_CAPTURE` from the cron environment. Capture stops
  immediately; no other behaviour changes.
- **Full revert:** `git revert 20a7e3a`. Because the patch is purely additive with zero
  deletions, the revert cannot damage legacy behaviour.

## Stop conditions

Stop and report rather than continuing if:

- `shadow_capture_test.py` fails on Trident;
- `snapshot_test.py --check` shows drift after the pull;
- any captured bundle contains a `REFUSED_POSSIBLE_SECRET` entry — that means an upstream bug
  is putting credential-shaped text into a source packet, which is a real finding and should
  be investigated before capture continues;
- the capture root fills unexpectedly.

## What happens after three runs

Disable capture, or leave it running — that is an owner decision. The pre-registered
comparison set is the **first three complete eligible runs after enablement**
(`FIRST-3-PRE-REGISTRATION.md`), and running longer does not change which three are the
sample.
