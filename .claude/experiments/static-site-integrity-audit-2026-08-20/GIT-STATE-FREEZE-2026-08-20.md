# Git State Freeze — 2026-08-20

Recorded per Batch-1-follow-up directive §C ("freeze the diverged git
state"). No branch was moved, rebased, or reset. This is a read-only record.

## Why this exists

Local `main` in `~/code/disability-collective-ai` and `origin/main` have
diverged: local `main` carries 38 commits not on `origin/main` (ongoing
Phase-2 capture / LC1 corpus / Sofa Method R&D work — active, not to be
touched by this audit track), and `origin/main` carries 6 commits not on
local `main` (the deployed-site containment work from this audit track, plus
unrelated legacy-corpus fixes and normal daily article publishing that landed
on the remote directly). A live peer session (`disability-collective-ai-60`)
is understood to be currently working in this same repository — per
directive, no rebase/reset of shared `main` was performed, and none should be
until that is confirmed clear with the owner.

## Durable reference points (local-only tags, not pushed)

- `freeze-local-research-2026-08-20` → local `main` HEAD (`732c84f`) at time
  of this freeze. **Not pushed to origin** — pushing this tag would also push
  the 38 underlying commit objects (Phase-2/LC1 research history) to the
  public repo, which is exactly the "one task = one branch/worktree, no
  concurrent work landing on shared/public state by accident" problem this
  freeze exists to prevent. It stays as a local bookmark only.
- `freeze-origin-public-2026-08-20` → `origin/main` HEAD (`3242e50`) at time
  of this freeze. Already public (it's what's deployed); tag kept local for
  convenience, redundant with the branch ref itself.

## Merge-base and divergence

- Merge-base(`main`, `origin/main`) = `9f9bf35`
- Local-only commits (`origin/main..main`): 38 — most recent
  `732c84f` ("fix: exclude calibration/ and reader-lab/ from public build" —
  the duplicate-content commit noted in the Batch-1 report; same change as
  `origin/main`'s `f7a355d`, different SHA because it was built on a
  different parent), oldest visible in this range going back through
  Sofa Method / Writer Grounding / Article Form preservation and shadow-
  pipeline work.
- Origin-only commits (`main..origin/main`): 6 — `3242e50` (Batch-1 evidence),
  `f7a355d` (Batch-1 fix), `86a91d3` / `70d9292` (Swan Care factual-cluster
  fixes), `8af3622` (new article published), `11826e4` (draft
  archival/housekeeping).

## Convention adopted going forward (per directive)

- `origin/main` = deployed/public history.
- `research/*` (naming convention, not yet applied to any existing branch) =
  R&D/`.claude` history.
- One task = one branch/worktree. This supplement itself was produced in
  `audit/static-site-supplement-2026-08-20`, branched fresh from `origin/main`,
  specifically to avoid adding a third divergent commit to local `main`.
- No concurrent agents operate directly on shared `main`. Local `main`'s
  reconciliation (38-ahead/6-behind) is **not** resolved by this freeze and is
  explicitly left for the owner / the session already working in that
  history — this document only makes the current split legible and durable,
  it does not fix it.

## Local main reconciliation status

**NOT RECONCILED.** Left exactly as found. No commits, resets, or rebases
were applied to local `main` in this task.
