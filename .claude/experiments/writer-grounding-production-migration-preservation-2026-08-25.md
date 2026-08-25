# Preservation Disposition — Writer Grounding / Production Migration Local Line

Stage A of the 2026-08-25 project-state reconciliation. This note records facts
about a divergent local git line and its disposition. It does not authorize,
ratify, or resume any of the work it describes.

## What this is

A local checkout at `~/code/disability-collective-ai` accumulated 38 commits
between 2026-08-19 and 2026-08-20 that were never pushed to `origin/main`.
Those commits contain the working history of a "writer grounding" fact-
verification effort and a "production migration" shadow-architecture effort,
plus several smaller closed items. Meanwhile `origin/main` moved on
independently and now contains a separate implementation (`NEW_ENGINE_V1`)
that picks up the same architectural idea.

This note exists so that history is not lost between two facts: (1) the local
line was never merged, rebased, or cherry-picked anywhere, and (2) the idea it
represents did reach production through different, later commits on
`origin/main`.

## Historical branch

- **Branch**: `archive/writer-grounding-production-migration-2026-08-20`
- **HEAD**: `732c84f9c4273e90516d38afd308b2e358971fb5`
  ("fix: exclude calibration/ and reader-lab/ from public build")
- **Merge-base with origin/main**: `9f9bf3519457479347113883a591c7cb92bce697`
- **Date range**: 2026-08-19 → 2026-08-20
- **Commit count**: 38, all still present verbatim, no rebase/merge/cherry-pick
  performed. Pushed directly from the exact local HEAD.
- **Pushed to**: `origin` (github.com:spac-null/disability-ai-collective),
  confirmed remote SHA == local SHA post-push.

## What the branch contains

In chronological order, four tracks of work:

1. **Sofa Article Form calibration** (FORM-1.2, FORM-1.3, variance replicates,
   Sofa method/benchmark lineage) — input-layer research feeding into writer
   grounding.
2. **Writer Grounding V0 → V6** (detector calibration, verdict calibration,
   extraction, decomposition, modular arbitration, closure calibration) plus a
   final integrated shadow-replay attempt.
3. **Legacy prompt/rule inventory** and **Real Article Test 2** (transfer
   validation of the frozen grounding approach against a real article).
4. **Production migration Phase 0–2** (baseline freeze, target-architecture
   shadow v0, passive-capture deployment prep) plus three small closed
   corrections (Swan Care cluster, legacy P0 care-labor, calibration/
   reader-lab build exclusion).

## Writer Grounding status

**OWNER-STOPPED. SHADOW-CALIBRATED CANDIDATE. NOT PRODUCTION-VALIDATED. NOT
TRANSFER-VALIDATED.**

Per commit `3a05f61` ("evidence: owner stop on writer grounding; final shadow
replay aborted before execution"): the final end-to-end shadow replay was
stopped by the owner before any model stage executed — zero model calls, zero
outputs. Writer Grounding is frozen at that point, not completed and not
resumed by any later commit on this branch.

**Explicit prohibition (still in force):** no WG-7, no further Edinburgh
grounding experiment, no new FORM version. Reopen only if a later
transfer/production test reveals a reproducible failure mapping back to this
architecture.

## Production migration Phase 0–2 status

**Superseded by `NEW_ENGINE_V1`.** The local Phase 0–2 line never merged and
its passive-capture deployment sat at 0/3 samples. A separate, later
implementation on `origin/main` (`NEW_ENGINE_V1`, first appearing 2026-08-24)
implements the same target pipeline
(`DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING`) and states it is
"built on the frozen work rather than a second architecture." `NEW_ENGINE_V1`
is live and has run successfully at least once in production as of
2026-08-25, but remains opt-in (`CRIPMINDS_ENGINE=current`); the default
engine is still `LEGACY`. This branch's Phase 0–2 evidence is historical
record of the shadow work that preceded the real cutover, not a parallel or
competing implementation to reconcile.

**Clarification added in the 2026-08-25 same-day correction pass:** "superseded" above refers
only to this branch's own passive-capture *code line* being superseded as the production
candidate by `NEW_ENGINE_V1`'s implementation. It does **not** mean the underlying Phase-2
passive-capture *requirement* (3 real samples of the legacy pipeline, captured for later
comparison against the target architecture) has been satisfied or retired — that requirement is
tracked separately on `origin/main` (`automation/shadow_capture.py`, still being actively
engineered as of `56eba2b`/2026-08-24) and remains **STILL OPEN**, current sample count unknown
without Trident access. See `.claude/WORK.md` BLOCKED/OUTSTANDING for the current, re-verified
status — do not infer from this note that the P2 gate is closed.

## Preservation completeness

All primary evidence for writer grounding, production migration, the legacy
prompt/rule inventory, Real Article Test 2, and the Sofa Article Form
calibration lineage was **already committed** in the 38 local-only commits
(verified: every relevant `.claude/experiments/*` directory referenced by
these commits is present in the local `main` tree, not merely staged as
untracked files). Pushing the archive branch is therefore sufficient — no
additional untracked material needed to be added to preserve this specific
history.

A separate, unrelated set of ~700 untracked files also exists in the local
checkout (CJ1/CJ2 probe fixtures from an earlier, already-superseded research
track; Playwright session cache; an in-progress Reader Lab round RL-2026-003;
a partial local copy of the static-site-integrity-audit that is superseded by
a more complete version already committed on `origin/main`). None of it
overlaps with writer grounding / production migration. It is inventoried but
intentionally **not** included in this preservation pass — see the Stage A
untracked-evidence classification in the reconciliation report for
disposition options.

## Data-loss risk

**RESOLVED for the material in scope.** Writer grounding, production
migration Phase 0–2, and the associated closed items now exist durably on
`origin` as `archive/writer-grounding-production-migration-2026-08-20`, in
addition to the local checkout.

## What this branch is not

This branch is historical record of stopped/superseded shadow work. It is
**not** production code, **not** a pending feature branch, and merging it into
`main` is **not** implied or recommended by its existence. `NEW_ENGINE_V1` on
`origin/main` is the current, live successor to the ideas this branch
explored.
