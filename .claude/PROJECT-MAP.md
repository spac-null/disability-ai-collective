# CripMinds Project Map

**Physical topology only** — what long-lived worktrees/branches/evidence exist, where they
live, and their lifecycle status. NOT current truth (`WORK.md`), NOT chronology (`LOGBOOK.md`).
Machine-generated snapshot: `.claude/project-manifest.json` (regenerate with
`python3 scripts/cripminds_project_inventory.py`, read-only, safe to run anytime).

Installed 2026-08-16, Project Memory Phase 3, following the PI2 (audit) → PP1 (Mac
preservation) → PP2 (Mac+Trident cross-machine redundancy) preservation sequence. **Cleanup is
still not authorized** — this file documents state, it does not permit archival action on its own.

## Authority order

1. direct runtime / Git / DB evidence
2. `WORK.md` — what is true now
3. `LOGBOOK.md` — chronological history / how we got here
4. `PROJECT-MAP.md` (this file) — physical topology
5. `~/code/cripminds-preservation/PRESERVATION-MANIFEST.json` / linked evidence
6. historical documents (off-main, `.claude/experiments/`, etc.)
7. Claude-local/private memory summaries — never canonical, may be stale

## Canonical repository

- Path: `~/code/disability-collective-ai`
- Branch: `main`
- Origin: `git@github.com:spac-null/disability-ai-collective.git` (PUBLIC repo)
- Current role: sole canonical checkout; all 20 sibling worktrees are experiment/evidence
  copies, never a second "canonical"

## Production / Trident

- Production checkout: `jascha@trident.tail630536.ts.net:/srv/data/hermes/workspace/disability-ai-collective/`
  (checked out fresh by `cripminds-daily.sh` via `git pull` before each run)
- Production DB authority: same host, `disability_findings.db` — Trident is authoritative;
  the Mac-side copy is a separate, unreconciled, gitignored file, not a backup
- Evaluation root (Trident): `/srv/data/hermes/evaluations/` (currently: `cripminds-five-article-2026-08-16/`)
- Preservation mirror (Trident, archival only, NOT used by production automation):
  `/srv/data/hermes/preservation/cripminds/`
- Preservation root (Mac): `~/code/cripminds-preservation/`

## Active work

**Story Rejection prototype**
- Path: `~/code/disability-collective-ai-srv1`
- Branch: `proto/story-rejection-v1`
- SHA: `37432b983093274224a49cd1e2f820d41aa32bb6`
- Status: **FROZEN — AWAITING PRFV1**. Do not edit, merge, rebase, or deploy. Backed by Mac
  worktree + Mac verified bundle + Trident verified bundle (PP2); not pushed to any remote —
  proposed remote ref `origin/experiments/proto-story-rejection-v1` awaits owner approval.

No other worktree/branch is currently ACTIVE — all remaining 19 are FROZEN-adjacent, PARKED,
SUPERSEDED, or SAFE-TO-ARCHIVE-LATER (below). All 20 sibling worktrees are internally clean
(0 dirty, 0 untracked) as of the 2026-08-16 audit — only canonical `main` carries untracked
material (see Evidence stores).

## Historical experiment worktrees / branches

| Name | Path | Purpose | Status | Unique evidence/doc pointer |
|---|---|---|---|---|
| audit/story-rejection-design | `-worktree` | ad hoc audit checkout, HEAD matches Trident's deployed commit exactly | MERGED | none — 0 commits ahead of main |
| (detached) | `-base-build` | historical build checkpoint | MERGED | none — 0 commits ahead of main |
| (detached) | `-eval-batch-1` | evaluation harness checkout | MERGED | none — 0 commits ahead of main; sibling plain dir `-eval-batch-1-harness` (non-git, `run_one_article.py`) sits alongside, not a worktree |
| integration-observability-2026-08-14 | `-integration-observability` | observability integration work | MERGED | none — 0 commits ahead of main |
| integration-first-work-persona-safety-2026-08-15 | `-integration-release` | persona-safety release integration | MERGED | none — 0 commits ahead of main |
| persona-safety-fail-closed-2026-08-16 | `-persona-fail-closed` | PS1 candidate fix (`89cd082`) | SUPERSEDED | same patch-id as merged release commit `169e8ff` — content is on `main` under a different SHA, not literally an ancestor |
| author-persona-biography-provenance-2026-08-14 | `-persona-biography` | APE2 candidate fix (`e93bb1b`) | SUPERSEDED | folded into merged `dbe0a96` ("AP1 + edge-case closure") on `main`, which is a superset of this branch's diff |
| article-quality-next-2026-08-14 | `-article-quality` | article-quality evidence pass | PARKED | `.claude/article-quality-evidence-pass-2026-08-14.md` already exists on `main`; branch's own 13 ahead commits not exhaustively diffed — confirm before archiving |
| format-lab-v0-2026-08-14 | `-format-lab` | Format Lab V0 design | PARKED | off-main doc preserved: `cripminds-format-lab-v0-2026-08-14.md` |
| format-lab-v1-generative-media-2026-08-14 | `-format-lab-v1` | Format Lab V1 design | PARKED | off-main doc preserved: `cripminds-format-lab-v1-generative-media-2026-08-14.md` |
| format-lab-v2-what-the-room-heard-2026-08-14 | `-format-lab-v2` | Format Lab V2 prototype | PARKED | off-main doc preserved: `cripminds-format-lab-v2-what-the-room-heard-2026-08-14.md` |
| human-detail-provenance-2026-08-14 | `-human-detail-provenance` | P1 human-detail-provenance experiment | PARKED | concept doc already CURRENT on `main`; branch's own 2 ahead commits not confirmed identical to main's shipped implementation |
| opening-quality-shadow-2026-08-14 | `-opening-quality` | opening-template shadow detector | PARKED | not confirmed superseded — old base (20 behind), owner review recommended |
| ops-release-hardening-2026-08-14 | `-ops-release-hardening` | release-concurrency preflight + health checker | PARKED | main independently has `release_preflight.py`; not confirmed identical — owner review recommended |
| publication-surface-production-candidate-2026-08-14 | `-pub-surface-prod-candidate` | production-candidate review (Phase F, per WORK.md, not yet done) | PARKED | gated on Phase F completing |
| publication-model-v1-2026-08-14 | `-publication-model-v1` | Publication Model V1 synthesis; source of confirmed GENERATE→MATERIALIZE terminology | PARKED — **OFF-MAIN CANONICAL HISTORICAL DOCUMENT pending separate import-to-main correction** | off-main doc preserved: `cripminds-publication-model-v1-2026-08-14.md`; verified byte-identical (SHA-256 `c8edb91c...`) between the live branch blob and the PP1-preserved export — WORK.md cites this document 3x by a path that doesn't exist on `main`; import is a separate follow-up (Phase 3B), not done here |
| publication-surface-v1-2026-08-14 | `-publication-surface-v1` | Publication Surface V1, promotes "What the Room Heard" to a first-class Work | PARKED | off-main doc preserved: `cripminds-publication-surface-v1-2026-08-14.md` |
| production-editorial-upgrade-v1-2026-08-14 | `-editorial-upgrade-v1` | Editorial Upgrade V1 / "E2" experiment — **explicitly "do not deploy as-is" per WORK.md `## 6`** | PARKED | 2 off-main docs preserved: `production-editorial-upgrade-v1-2026-08-14.md`, `production-formula-root-cause-audit-2026-08-14.md` |
| testimony-architecture-2026-08-14 | `-testimony-architecture` | L1/L2 testimony architecture audit | PARKED | off-main doc preserved: `testimony-L1-L2-audit-2026-08-14.md` |

Branches with no worktree (not in the table above, still exist): `persona-safety-fail-closed-release-2026-08-16`
(`169e8ff`, MERGED — this is the release commit that supersedes the candidate above),
`release-pre-rebase-2026-08-14` (`2ad2300`, ancestor of `article-quality-next`),
`pixel-validation/control` (`2a190ad` — diverges from `origin/pixel-validation/control`, see
Open structural issues).

Allowed lifecycle statuses: `ACTIVE`, `FROZEN`, `PARKED`, `MERGED`, `SUPERSEDED`,
`EVIDENCE-ONLY`, `SAFE-TO-ARCHIVE-LATER`, `UNKNOWN`. Never `SAFE-TO-DELETE`.

## Evidence stores

- Mac preservation root: `~/code/cripminds-preservation/` (bundle, CJ1/CJ2 engineering,
  RL-2026-003, off-main docs, whitepaper v0.2 exports, PI2 inventory copy, manifest)
- Trident preservation mirror: `/srv/data/hermes/preservation/cripminds/` (PP2, cross-machine
  redundant copy of the above — hash-verified identical, 674/674 files)
- Five-article evaluation: authoritative original on Trident
  (`/srv/data/hermes/evaluations/cripminds-five-article-2026-08-16/`), preservation copy on Mac
  (`~/code/cripminds-preservation/evaluations/...`) — already cross-machine redundant, do not
  re-copy either direction
- Reader Lab: `reader-lab/rounds/drafts/RL-2026-003.json` + `calibration/candidates/RL-2026-003-*.json`
  — untracked, in-flight, preserved (not published) at `~/code/cripminds-preservation/reader-lab/RL-2026-003/`
- CJ1/CJ2 engineering: `automation/cj1_v3_*.py`, `automation/cj2_*.py`,
  `automation/.probe_fixtures/` — untracked on canonical `main` (52 scripts + fixtures),
  preserved at `~/code/cripminds-preservation/engineering/cj1-cj2-2026-08-16/`
- Production DB authority: Trident's `disability_findings.db` /
  `automation/engagement.db` — no SQLite-safe backup exists yet (open risk, below)

## Safety rules

- No worktree removal before a `PROJECT-MAP.md` + preservation-manifest check confirms the
  worktree's unique commits/docs/untracked material are covered.
- No `git gc`/`git prune` before a fresh `git fsck --unreachable --dangling` check — the 19
  `refs/cripminds-preserve/reflog-2026-08-16/*` refs must keep showing 0 unreachable commits.
- Untracked evaluation evidence must be preserved or indexed before any removal.
- Code authority (Git) and evidence authority (Trident production data, evaluation artifacts)
  are distinct — do not assume one backs up the other.
- Claude-local/private memory is never canonical for this project — treat it as a stale-prone
  pointer, always re-check against this file and `WORK.md`/`LOGBOOK.md`.

## Open structural issues

- Database backup — no SQLite-safe snapshot method exists yet for `disability_findings.db` /
  `automation/engagement.db`; naive `cp` of a live SQLite file is not safe. Separate follow-up.
- `.claude/cripminds-publication-model-v1-2026-08-14.md` — broken reference in `WORK.md` (cited
  3x); the exact off-main blob is preserved and verified byte-identical, but not yet imported to
  `main`. Phase 3B, not done here.
- `pixel-validation/control` (local, `2a190ad`) diverges from `origin/pixel-validation/control`
  (`bfbc017`, 2 commits ahead) — unreconciled, low priority, both sides are git-backed.
- Story Rejection prototype (`proto/story-rejection-v1`) — **FROZEN, AWAITING PRFV1**. No
  remote (GitHub) copy yet; proposed ref `origin/experiments/proto-story-rejection-v1` awaits
  owner approval.
- Trident production checkout is 2 commits behind Mac `main` as of this pass (missing the
  whitepaper-recovery and whitepaper-directory-move docs commits) — routine `git pull`, not a
  preservation risk.
