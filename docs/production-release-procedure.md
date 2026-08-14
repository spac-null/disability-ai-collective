# Production release procedure — automation/ engineering changes

This document exists because the 2026-08-14 release (12 engineering commits —
A-M reconciliation safety fixes + the floor-plan article repair) hit real
concurrency with the daily content-publishing bot mid-release, and the
recovery procedure worked but was invented live in conversation. This is that
procedure, written down so it's a checklist next time, not a fresh
derivation.

Scope: this covers releasing changes to `automation/` (the article-generation
pipeline: orchestrator code, gate/review logic, config). It does not cover
Reader Lab (`reader-lab-worker/`, wholly separate deploy path — see that
directory's own README) or content itself (articles are never "released,"
they're published directly by the bot or by hand).

## The concurrency this procedure exists for

`origin/main` is not a quiet branch. A content-publishing bot
(`Disability-AI Collective Bot`, cron-driven from Trident — see
`automation/README.md` and `.claude/CONTEXT.md`) commits and pushes directly
to `main` on its own schedule: a new article most days around 09:00 UTC, a
weekly draft-archive sweep, occasional Bluesky/newsletter housekeeping
commits. None of this goes through a PR. **There is no branch protection on
`main`** (verified directly: `gh api repos/.../branches/main/protection` →
404 "Branch not protected") — nothing server-side stops a bad push; the
discipline below is the only thing that does.

A multi-commit engineering release, prepared over hours, can therefore find
`origin/main` has moved by the time it's ready to ship. That is normal,
expected concurrency — not a release failure — provided the moved-past
commits are the bot's routine content activity and don't touch any file the
release also touches.

## The verified flow

```
FETCH
  → PREFLIGHT (classify what moved, decide safe/unsafe)
  → SAFE REBASE (only if preflight says so)
  → TEST (full suite, against the REBASED tree — new commit ids, don't trust
    the pre-rebase run)
  → FINAL FETCH / RACE CHECK (immediately before push — did origin move
    again in the meantime?)
  → PUSH (ordinary fast-forward, never --force)
  → TRIDENT EXACT-SHA UPDATE (git pull on the production workspace, don't
    wait for the next cron tick if the fix is time-sensitive)
  → POST-DEPLOY TESTS (rerun the suite ON Trident too — same code, different
    machine, worth the 30 seconds)
  → NATURAL RUN (let the next real cron-triggered run be the first thing
    that exercises anything requiring a live model call; never fake one to
    "prove" a release)
```

### 1. Prepare
Do the engineering work on a branch or worktree, never directly advancing a
long-lived shared branch other than `main` itself once ready. Get tests
green locally before touching anything remote.

### 2. Preflight
Run `automation/release_preflight.py` (see below) with your release's base
commit. It fetches `origin/main`, diffs it against your last-known base, and
classifies every origin-only commit. It never rebases, pushes, or deploys —
it only tells you which of five states you're in:

- `CLEAN_FAST_FORWARD` — origin/main hasn't moved. Skip straight to push.
- `SAFE_REBASE_REQUIRED` — origin/main moved, but only with commits confined
  to content paths (see classification below) that don't overlap your
  release's own changed files. Rebase is expected to be conflict-free.
- `OVERLAPPING_REMOTE_CHANGE` — an origin-only commit (bot or otherwise)
  touched a file your release also touches. **Stop.** A human needs to look
  at this; the tool will not decide for you whether it's safe.
- `DIRTY_WORKTREE` — you have uncommitted tracked changes that aren't part
  of the release. Protect them (see step 3) before doing anything else.
- `UNKNOWN_REMOTE_CHANGE` — an origin-only commit doesn't match any known
  content-bot pattern (unrecognized author, unrecognized path shape, or
  both). Treat as require-human-review, same as an overlapping change.

### 3. Protect unrelated uncommitted work
If preflight reports `DIRTY_WORKTREE`, and the dirty files are genuinely
unrelated to the release (e.g. this repo's `.claude/current-work.md`
running checkpoint notes, which by convention is never part of a feature
commit), protect them with a scoped `git stash push -m "<reason>" -- <path>`
before rebasing, and `git stash pop` once the rebase is done. Never `git
checkout -- <path>` or `git clean` to make the tree look clean — that
discards, stashing preserves.

Also create a local safety-net branch pointing at your pre-rebase release
HEAD (e.g. `release-pre-rebase-YYYY-MM-DD`) before rebasing. Never push it.
Keep it until at least one clean natural run has happened on the new SHA;
delete it (locally) whenever, after that.

### 4. Rebase (only if preflight said `SAFE_REBASE_REQUIRED`)
```
git rebase origin/main
```
Plain rebase, no `--onto` gymnastics unless preflight's own diagnosis
specifically calls for it (it doesn't in the common case — the release
commits and the origin-only commits are on the same line of history, just
diverged). If this produces ANY conflict, that falsifies preflight's
zero-overlap classification — stop, do not resolve casually, and go figure
out why the file-overlap check missed something (a rename? a generated
file preflight doesn't track?).

### 5. Retest
Rebasing changes every commit id in the range. Do not trust a pre-rebase
test run as evidence about the post-rebase tree. Rerun the full
`automation/*_test.py` suite plus `snapshot_test.py --check`, and do a
plain import + `ProductionOrchestrator()` instantiation check.

### 6. Final race check
Immediately before pushing:
```
git fetch origin main
```
Compare the fetched SHA against the base you just rebased onto.
- Unchanged → push.
- Advanced again, still only with non-overlapping content-bot commits →
  rebase once more onto the new base, rerun at least the focused/fast tests
  + snapshot check, then repeat this race check.
- Advanced with anything else → stop.

### 7. Push
```
git push origin main
```
Never `--force`, never `--force-with-lease` as a substitute for actually
resolving a real divergence. This should always be an ordinary fast-forward
if steps 1-6 were followed. Verify `git rev-parse origin/main` afterward
matches your local HEAD exactly.

### 8. Update Trident to the exact SHA
The daily cron (`cripminds-daily.sh`) already does `git pull origin main`
before every run — code ships automatically, eventually, without any manual
step. But if the release is time-sensitive (a safety fix, not routine), pull
manually rather than waiting:
```
ssh jascha@trident 'cd /srv/data/hermes/workspace/disability-ai-collective && git pull origin main'
```
Before pulling: confirm the workspace's tracked-file working tree is clean
(`git status --short`, ignoring known pre-existing untracked artifacts — see
`automation/release_preflight.py`'s `KNOWN_TRIDENT_UNTRACKED` list, kept in
sync with reality, not guessed fresh each time). If it's dirty in tracked
files in a way you can't explain, stop — don't overwrite unknown production
edits.

After pulling, verify `git rev-parse HEAD` on Trident equals the SHA you
just pushed. Re-run the test suite there too (same code, a different
Python/dependency environment than your laptop — cheap insurance).

### 9. Let the natural run prove the rest
Anything that only exercises at real-article-generation time (lazy schema
creation, a real model call's shape, an actual gate/review pass) should be
verified by the next real cron-triggered run, not a manufactured one. Use
`automation/natural_run_health_check.py` (see below) after that run to
check its output without digging through logs/DB by hand.

## Bot-commit classification

A commit found on `origin/main` that isn't in your release is either safe
to rebase past, or it isn't. The classifier (`automation/
release_preflight.py`'s `classify_commit`) never trusts the commit message
alone — it looks at the actual changed file paths:

**`SAFE_ROUTINE_CONTENT`** — every single file the commit touches matches
one of:
- `_posts/**`, `_drafts/**`, `_drafts/_archive/**` (published/draft articles)
- `_reviews/**` (citation-check sidecars)
- `assets/**` (article images)
- `_social/**` (Bluesky URI records)

A commit matching this AND authored by the known bot identity
(`Disability-AI Collective Bot <contact@disability-ai-collective.org>`) is
classified `SAFE_ROUTINE_CONTENT`. The path check runs regardless of
author — an unfamiliar author touching only these paths is still content-
shaped and gets flagged for the softer "verify, don't assume" treatment
described below, never silently treated as identical to a known-bot commit.

**`CODE_OR_INFRASTRUCTURE`** — the commit touches anything else at all:
`automation/orchestrator/**`, `automation/*.py` outside the content dirs
above, `.github/workflows/**`, `_config.yml`, any `reader-lab*` path,
`calibration/**`, migrations, or literally anything not on the safe-path
allowlist. **One non-content file anywhere in the commit is enough to
classify the whole commit this way** — there is no partial credit.

**`UNRECOGNIZED`** — path shape doesn't clearly match either bucket (e.g. a
new top-level directory the classifier has never seen). Treated identically
to `CODE_OR_INFRASTRUCTURE` for safety — require human review rather than
guess.

The preflight tool checks these in order:
1. Any file-path overlap at all between origin-only commits and the
   release's own changed files, **regardless of classification** →
   `OVERLAPPING_REMOTE_CHANGE` (stop). A bot commit that happens to touch a
   file the release also touches is still a real collision.
2. Otherwise, if any origin-only commit is `CODE_OR_INFRASTRUCTURE` or
   `UNRECOGNIZED` (even with zero file overlap) → `UNKNOWN_REMOTE_CHANGE`
   (stop) — an unreviewed code/infrastructure change sitting on `main`
   deserves a human look before anything rebases past it, overlap or not.
3. Otherwise (every origin-only commit is `SAFE_ROUTINE_CONTENT`, zero
   overlap) → `SAFE_REBASE_REQUIRED`.

## What this procedure deliberately does NOT automate (yet)

`release_preflight.py` diagnoses only. It never rebases, pushes, deploys,
or deletes a branch — a human (or an agent acting on a human's explicit
instruction) performs those steps, informed by its output. Automating the
rebase/push itself can be revisited once this diagnostic tool has some real
mileage on it.

## Never

- Never force-push `main`.
- Never treat a routine bot commit as a release failure — it's expected
  concurrency, not a problem.
- Never treat an unreviewed code/infrastructure commit on `origin/main` as
  automatically safe to rebase past, no matter how small it looks.
- Never fake a production run (no synthetic article, no manually inserted
  observation rows, no manually created schema) to "prove" a release works.
  Let the next natural cron run do that, then check its output with
  `natural_run_health_check.py`.
