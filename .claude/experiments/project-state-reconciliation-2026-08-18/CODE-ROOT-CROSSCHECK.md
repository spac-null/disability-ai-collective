# CODE-ROOT-CROSSCHECK.md

Supplemental to the 2026-08-18 reconciliation. Read-only. No worktree
metadata repaired, nothing moved/deleted/committed.

## 1. Worktree crosscheck (`git worktree list --porcelain` vs filesystem)

**CORRECTED 2026-08-19**: this section originally miscounted — it said "22
registered worktrees (main + 21 siblings)". Re-verified count via
`git worktree list --porcelain | grep -c "^worktree "`: **23** (main + 22
sibling worktrees). See GAP-LEDGER G-043 and WORKTREE-CONTENT-EQUIVALENCE.md.

All 23 registered worktrees (main + 22 siblings) exist on disk and match
their registered HEAD. **REGISTERED + EXISTS: 23/23. REGISTERED + MISSING: 0.
EXISTS + NOT REGISTERED (git repos pointed at the same remote but absent from
the worktree list): 0.**

Method: parsed `git -C ~/code/disability-collective-ai worktree list
--porcelain` (23 `worktree` lines: main + 22), confirmed each path exists via
`ls`, and separately enumerated every `.git` under `~/code` top-level and
checked its `origin` remote against `git@github.com:spac-null/
disability-ai-collective.git` — the resulting set was identical to the
porcelain list, confirming no unregistered clone of this remote exists
under `~/code`.

`git worktree prune --dry-run --verbose` returned empty — no stale worktree
administrative entries (i.e., no case of a worktree removed from disk but
still referenced in `.git/worktrees/`).

## 2. Non-worktree CripMinds siblings under `~/code`

Two found, both already partially known to the project's own canonical
memory (see below) but neither fully cross-referenced by the 2026-08-18
reconciliation's own inventory before this supplement:

| Path | Purpose | Unique content? | Duplicated elsewhere? | Referenced by docs? | Preservation risk |
|---|---|---|---|---|---|
| `disability-collective-ai-eval-batch-1-harness/` | A standalone (non-git) harness (`run_one_article.py`) + its 7-candidate output from the five-article evaluation run | Possibly not unique — appears to be the same run as a `/tmp` scratchpad copy the prior reconciliation found (not byte-diffed to confirm) | Likely, against the `/tmp` scratchpad copy in UNPRESERVED-ARTIFACTS.md item 3 — unconfirmed | YES — `PROJECT-MAP.md` line 153 names it explicitly as a known non-worktree sibling | LOW (durable `~/code` location, not `/tmp`) but **not indexed in `.claude/experiments/`** |
| `disability-collective-ai.zip` | Full static repo snapshot, 2026-08-12, including `.git` (362M) | NO — superseded by the live repo + the 2026-08-16 git bundle in `cripminds-preservation/git/` for anything after 2026-08-12 | Effectively yes (older subset of the preserved git bundle) | YES — the 2026-08-16 PI2 audit (`CRIPMINDS-PRESERVATION-RISKS.md`, `CRIPMINDS-PROJECT-TREE.md`, `CRIPMINDS-PROJECT-MANIFEST.json`) already classified it "F — safe archival, not fragile, no action needed" | NONE — already assessed safe by PI2; just not referenced in the current reconciliation's own docs |

## 3. Archives / backups

Only one archive file matching the CripMinds name patterns exists under
`~/code`: `disability-collective-ai.zip` (see above). No `.tar`, `.tar.gz`,
`.tgz`, or `.bak` files matching these patterns were found. Not extracted
(its `.git/config` was peeked via `unzip -p` without extraction, confirming
the embedded remote matches the canonical repo — sufficient to classify it
without a full extract).

## 4. Nested / misplaced repos

None found. Every `.git` under `~/code` top-level pointing at the CripMinds
remote is one of the 22 registered worktrees (see §1). No old clones,
accidental clones, orphan worktrees, or tool-created copies were found
elsewhere under `~/code`.

## 5. Cross-check against the 2026-08-16 PI2 preservation audit

| Old known path (from `CRIPMINDS-PROJECT-TREE.md` / `CRIPMINDS-PROJECT-MANIFEST.json`, 2026-08-16) | Still exists? | Current type | Current status | Now in gap ledger? |
|---|---|---|---|---|
| `~/code/disability-collective-ai/` (+ 22 sibling worktrees) | YES | CANONICAL_GIT_REPO + REGISTERED_GIT_WORKTREE ×22 | unchanged in kind, HEAD advanced from `13b6767`→`9f9bf35` since PI2 | already fully covered, not a new gap |
| `~/code/disability-collective-ai.zip` | YES | BACKUP_ARCHIVE | unchanged, still "F — safe archival" per PI2 | **G-042 (new, minor indexing gap only)** |
| `~/code/disability-collective-ai-eval-batch-1-harness/` | YES | PLAIN_DIRECTORY | unchanged; PROJECT-MAP.md line 153 documents it, but the 2026-08-18 reconciliation's own INVENTORY.md/UNPRESERVED-ARTIFACTS.md never cross-referenced it against the `/tmp` five-article-eval finding | **G-041 (new — corrects G-026's severity)** |
| `~/code/cripminds-preservation/` (PP1/PP2 output) | YES | EVIDENCE_DIRECTORY | unchanged | already covered (INVENTORY.md §F) |
| `~/code/cripminds-project-inventory-2026-08-16/` (PI2 output) | YES | EVIDENCE_DIRECTORY | unchanged, confirmed byte-identical to its mirrored copy inside `cripminds-preservation/manifests/` | already covered |

**No previously-known CripMinds filesystem object has disappeared without a
recorded disposition.** Every path PI2 knew about in 2026-08-16 still exists
today, in the same form.

## Answer to the governing question

Does "all 23 worktrees inspected" (corrected from the originally-stated 22 —
see G-043) mean all CripMinds objects under `~/code` are accounted for?
**NO, not by itself** — worktree enumeration alone would have missed
`disability-collective-ai-eval-batch-1-harness/` and
`disability-collective-ai.zip`, neither of which is a registered worktree.
However, this filesystem-root sweep confirms that once you *also* check
(a) every top-level `.git`'s remote URL and (b) the two non-worktree plain
paths, **the full CripMinds filesystem footprint under `~/code` is now
accounted for** — nothing new and unknown was found; the two items that
worktree-only enumeration would have missed were each already partially
known to canonical docs (PROJECT-MAP.md line 153; the 2026-08-16 PI2 audit),
just not cross-referenced against this reconciliation's own findings until
now.
