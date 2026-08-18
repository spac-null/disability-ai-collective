# CODE-ROOT-INVENTORY.md

Supplemental to the 2026-08-18 reconciliation. Filesystem-level sweep of
`~/code/` — not restricted to `git worktree list`. Read-only; nothing moved,
deleted, extracted, or committed.

## Method

1. `ls -la ~/code/` (full immediate-child listing, 96 entries) — scanned for
   name patterns `disability-collective-ai*`, `disability-ai*`, `cripminds*`,
   `crip-minds*`, `collective-ai*`. No matches found outside the set below.
2. For every top-level directory containing a `.git`, checked
   `git remote get-url origin` and matched against
   `git@github.com:spac-null/disability-ai-collective.git` — this catches
   relevance by remote, not name, per the task's requirement. No matches
   found beyond the 22 already-known worktrees.
3. Checked for `*.zip/*.tar/*.tar.gz/*.tgz/*.bak` at `~/code` top level
   matching the name patterns above.
4. `git -C ~/code/disability-collective-ai worktree prune --dry-run
   --verbose` — checks for stale worktree administrative entries not
   reflected in the porcelain list. Empty output = none found.

## All CripMinds-related paths found (7 outside the 22 worktrees + the 22 worktrees themselves)

| Path | Type | Size | Last modified | Git HEAD/branch/remote | Dirty/untracked | Registered by `worktree list`? | Already in reconciliation inventory? | Unique content possible? | Safe status known? |
|---|---|---|---|---|---|---|---|---|---|
| `disability-collective-ai/` | CANONICAL_GIT_REPO | — | Aug 18 09:34 | `9f9bf35`/`main`/origin match | YES (1 modified + ~90 untracked) | YES | YES (this is the audit subject) | n/a | YES |
| `disability-collective-ai-{article-quality, base-build, editorial-upgrade-v1, eval-batch-1, format-lab, format-lab-v1, format-lab-v2, human-detail-provenance, integration-observability, integration-release, opening-quality, ops-release-hardening, persona-biography, persona-fail-closed, pub-surface-prod-candidate, publication-model-v1, publication-surface-v1, srv1, story-rejection-release, story-rejection-v11-fix, testimony-architecture, worktree}` (**22 dirs, corrected from an earlier miscount of 21 — see G-043**) | REGISTERED_GIT_WORKTREE | — | various, Aug 14–17 | see DECISION-RECONCILIATION.md / WORKTREE-CONTENT-EQUIVALENCE.md | NO (all 22 clean) | YES | YES (fully audited across two passes) | NO (all confirmed merged/duplicate/superseded/parked with known status as of the 2026-08-19 content-equivalence pass) | YES |
| `cripminds-preservation/` | EVIDENCE_DIRECTORY | 314M | Aug 16 22:04 | n/a (not a git repo itself; contains a git bundle) | n/a | n/a | YES (INVENTORY.md §F) | NO (its own manifest is authoritative) | YES |
| `cripminds-project-inventory-2026-08-16/` | EVIDENCE_DIRECTORY | 44K | Aug 16 17:16 | n/a | n/a | n/a | YES (INVENTORY.md §F) | NO (copy verified byte-identical to `cripminds-preservation/manifests/`) | YES |
| `disability-collective-ai-eval-batch-1-harness/` | PLAIN_DIRECTORY (non-git) | 2.6M | Aug 16 00:34 | n/a — confirmed `git rev-parse --is-inside-work-tree` fails, not a repo | n/a | **NO — not a worktree, never was one** | **NO — not referenced in the prior reconciliation's INVENTORY.md or UNPRESERVED-ARTIFACTS.md** | **YES, see finding below** | PARTIAL — PROJECT-MAP.md already names it (line 153) as a known non-worktree sibling, but the current reconciliation pass didn't cross-reference it |
| `disability-collective-ai.zip` | BACKUP_ARCHIVE | 362M | Aug 12 22:09 | embedded repo snapshot, remote confirmed matching (peeked `.git/config` inside the zip without extracting) | n/a | n/a | NOT in the 2026-08-18 reconciliation's own docs, but YES in the earlier 2026-08-16 PI2 audit (classified "F — safe archival, not fragile, no action needed") | NO — full static snapshot, superseded by live repo + git bundle for anything after 2026-08-12 | YES (already assessed) |

## Finding: the harness directory is not what G-026 assumed

`disability-collective-ai-eval-batch-1-harness/results/{01..07}/` contains
**all 7** of the five-article-eval candidates (titles confirmed: "Follow Your
Nose", "You Can't Walk Into a Gallery", "Sniff It Out", "Who Held The Pen
When Christy Brown Painted", "Nine Codecs And Not One Of Them Is For Her",
"What Kelsie Conley Meant By Slow", "23,000 Jobs And The Question Nobody
Asks"), each with `run_result.json`, `captured.json`, `prompt_calls.json`,
`actual_models.json`, `engagement_shadow.db`, `_drafts/`, `_reviews/` — the
same schema and apparently the same run as the `/tmp/claude-501/.../
scratchpad/five-article-eval/artifacts/{01..07}/` copy the prior reconciliation
flagged in UNPRESERVED-ARTIFACTS.md item 3 as "6 of 7 unpreserved, /tmp only."

**This is a durable `~/code` location, not an ephemeral `/tmp` scratchpad.**
The two copies were not byte-diffed in this pass (out of scope — no
extraction/deep-diff was performed per the read-only/shallow instruction),
so it is not confirmed whether they are identical, but their existence alone
means the prior claim "these 6 candidates exist nowhere durable" is
**overstated**. See GAP-LEDGER G-041 for the correction.

Also notable: `PROJECT-MAP.md` line 153 **already documents this exact
directory** as "sibling plain dir `-eval-batch-1-harness` (non-git,
`run_one_article.py`) sits alongside, not a worktree" — so canonical project
memory was not blind to its existence; the 2026-08-18 reconciliation simply
didn't cross-reference PROJECT-MAP.md's own worktree-table footnote against
its own `/tmp` findings.

## Everything else checked and confirmed NOT relevant / NOT new

- No directory under `~/code` matches the CripMinds name patterns beyond the
  7+22 listed above (full case-insensitive scan performed).
- No `.git` directory under any `~/code` top-level entry points at the
  `spac-null/disability-ai-collective` remote other than the 22 already-known
  worktrees (checked by remote URL, not name, for every top-level `.git`).
- No stale/orphaned worktree administrative entries exist (`git worktree
  prune --dry-run --verbose` returned empty).
- No other `.zip/.tar/.tar.gz/.tgz/.bak` files under `~/code` matching the
  name patterns.
- `disability-collective-ai-eval-batch-1-harness/__pycache__/` contains only
  a compiled `.pyc` of `run_one_article.py` — no hidden source.
