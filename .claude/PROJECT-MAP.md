# CripMinds Project Map

**Physical topology only** — what long-lived worktrees/branches/evidence exist, where they
live, and their lifecycle status. NOT current truth (`WORK.md`), NOT chronology (`LOGBOOK.md`).
Machine-generated snapshot: `.claude/project-manifest.json` (regenerate with
`python3 scripts/cripminds_project_inventory.py --no-trident`, read-only, safe to run anytime).

Rebuilt 2026-08-25 during the project-state reconciliation. The 2026-08-16 version of this file
(`.claude/archive/PROJECT-MAP-2026-08-16-superseded.md`) assumed the local `~/code/disability-collective-ai`
checkout's `main` branch was canonical. **That assumption no longer holds** — see below.

## Authority order

1. direct runtime / Git / DB evidence
2. `WORK.md` — what is true now
3. `LOGBOOK.md` — chronological history / how we got here
4. `PROJECT-MAP.md` (this file) — physical topology
5. `~/code/cripminds-preservation/PRESERVATION-MANIFEST.json` / linked evidence
6. historical documents (off-main, `.claude/experiments/`, etc.)
7. Claude-local/private memory summaries — never canonical, may be stale

## Canonical repository — CORRECTED MODEL

- **Canonical branch: `origin/main`** (GitHub `spac-null/disability-ai-collective`, PRIVATE repo),
  currently `14997f07e23601f8fc7b920aed7ae15e2cb2e5cf` (PR #26 merge).
- **`~/code/disability-collective-ai` (local checkout, `main` branch) is NOT canonical.** Its
  `main` diverged from `origin/main` at merge-base `9f9bf35` (2026-08-19/20) and carries 38
  commits never pushed. Do not treat this checkout's `main` or its `.claude/` trackers as current
  truth — see `.claude/WORK.md`.
- **This reconciliation's own worktree**: `~/code/disability-collective-ai-reconcile`, branch
  `reconcile/project-state-2026-08-25`, based exactly on `origin/main`. Not yet merged.
- **Preservation branch (Stage A, 2026-08-25)**: `archive/writer-grounding-production-migration-2026-08-20`,
  pushed to origin, HEAD `732c84f` (== the divergent local checkout's exact HEAD at time of
  preservation). Historical record, not production code. No local worktree checked out for it.

## Production / Trident

Not independently re-verified this pass (no SSH check performed — this reconciliation was kept
strictly local/git-based). Carried forward from the 2026-08-16 map, treat as last-known, not
reconfirmed:
- Production checkout: `jascha@trident.tail630536.ts.net:/srv/data/hermes/workspace/disability-ai-collective/`
- Production DB authority: same host, `disability_findings.db`
- Preservation mirrors: `/srv/data/hermes/preservation/cripminds/` (Trident), `~/code/cripminds-preservation/` (Mac)

## Worktree inventory (52 total, from `project-manifest.json`)

Programmatically classified against `origin/main` this pass (`git merge-base --is-ancestor`):

- **26 confirmed MERGED** into `origin/main` (HEAD is an ancestor) — mostly the LC1 batch
  worktrees and job-tmp `dac-*` session worktrees from the recent legacy-corpus sweep. Safe to
  treat as historical/closed; not yet pruned (cleanup not authorized this pass).
- **12 PARKED**, **5 SAFE-TO-ARCHIVE-LATER**, **2 SUPERSEDED**, **1 FROZEN**, **1 ACTIVE** — per
  the 2026-08-16 hand-classification in `scripts/cripminds_project_inventory.py`'s
  `LIFECYCLE_STATUS` dict, unchanged by this pass. Full detail:
  `.claude/archive/PROJECT-MAP-2026-08-16-superseded.md` (Story Rejection V1/V1.1 release history
  there is still accurate — it predates the fork).
- **5 NOT ancestors of `origin/main`, individually reviewed this pass:**

| Worktree | Branch | Ahead of origin/main | Classification |
|---|---|---|---|
| `disability-collective-ai-ia-redesign` | `ia-redesign/main-site-2026-08-25` | 1 commit ("Main-site IA redesign: work-first hierarchy, withdrawal-safe listings") | **SUPERSEDED** — an earlier IA-redesign iteration; PR #26's "v2" shipped instead. Preserve, don't delete. |
| `disability-collective-ai-production-observability` | `production-observability-2026-08-20` | 2 commits ("fix: capture sidecar catches Exception, not BaseException" + 1 more) | **GENUINELY UNMERGED — real outstanding work.** No corresponding PR found. Owner decision needed: land it or explicitly park it. |
| `disability-collective-ai-static-audit-completion` | `static-audit-completion-2026-08-20` | 1 commit ("evidence: complete static site integrity audit coverage") | **Likely SUPERSEDED** — `origin/main` already carries a more complete version of the same static-site-integrity-audit (`COMPLETION-SUPPLEMENT-SEVEN-SURFACES.md`, `CLOSEOUT-2026-08-20.md`), landed independently. Not byte-diffed this pass; treat as probably-redundant, not confirmed-redundant. |
| `disability-collective-ai-reconcile` | `reconcile/project-state-2026-08-25` | this reconciliation itself | **ACTIVE**, not yet merged, awaiting owner review. |
| `disability-collective-ai-story-rejection-release` | `release/story-rejection-v1` | (cherry-picked, not a literal ancestor) | **RELEASED via cherry-pick**, already documented in the 2026-08-16 map — expected false-negative from the ancestor check, not a new gap. |

**~20 additional worktrees flagged by the pre-reconciliation research pass as having "no matching
PR in the 26-PR list"** (`format-lab-v0/v1/v2`, `persona-safety-fail-closed`, `story-rejection`
variants, `visual-study/variant-a–d`, etc.) turned out, on the `--is-ancestor` check above, to
mostly resolve one of two ways: either merged by direct fast-forward/cherry-pick rather than a
GitHub PR (matching the project's own established, non-PR-only workflow — see the 2026-08-16 map's
Story Rejection entries), or already individually classified PARKED/SUPERSEDED in the
hand-maintained `LIFECYCLE_STATUS` dict. None of them showed up in the "not an ancestor" table
above, meaning none represent unmerged, unclassified, at-risk work beyond the three flagged there.

**Known manifest-generator staleness (not fixed this pass):** `project-manifest.json`'s
`active_prototypes` field is a hardcoded block in the generator script and still reports Story
Rejection V1 as `"FROZEN — AWAITING PRFV1"` — that gate was satisfied and Story Rejection shipped
V1.1 to production back in 2026-08-16/17 (see `.claude/archive/WORK-2026-08-17-superseded.md`
`## 3` item 5). The generator script's hardcoded sections need their own maintenance pass; out of
scope for this reconciliation (tracker docs only, no code changes authorized).

## Evidence stores (unchanged from 2026-08-16, not re-verified this pass)

- Mac preservation root: `~/code/cripminds-preservation/`
- Trident preservation mirror: `/srv/data/hermes/preservation/cripminds/`
- CJ1/CJ2 engineering + probe fixtures: still untracked on the local checkout's `main`
  (~700 files, ~33MB) — classified during Stage A preservation as reproducible/superseded
  material, not primary evidence; see the preservation note. Not yet archived off-repo.
- Reader Lab RL-2026-003: still untracked, in-flight, unrelated to this reconciliation's scope.

## Safety rules (unchanged)

- No worktree removal before this file + a preservation-manifest check confirms unique
  commits/docs/untracked material are covered.
- No `git gc`/`git prune` before a fresh `git fsck --unreachable --dangling` check.
- Untracked evaluation evidence must be preserved or indexed before any removal.
- Claude-local/private memory is never canonical for this project.

## Open structural issues carried forward, re-checked this pass

- Database backup for `disability_findings.db` / `automation/engagement.db` — still no
  SQLite-safe snapshot method; unchanged, not re-verified this pass (no Trident access used).
- `production-observability-2026-08-20` — see table above, genuinely unmerged, needs an owner
  decision.
- Legacy prompt/rule inventory (4 must-fix / 24 consolidate items) — needs re-triage against
  `NEW_ENGINE_V1`; see `.claude/WORK.md` BLOCKED/OUTSTANDING.
- Local checkout's own 38-commit divergence — preserved (Stage A), but the checkout itself
  remains diverged. It should either be reset to track `origin/main` for future canonical work,
  or explicitly retired in favor of a fresh clone — owner decision, not performed this pass.
