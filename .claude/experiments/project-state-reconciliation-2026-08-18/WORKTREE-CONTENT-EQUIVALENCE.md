# WORKTREE-CONTENT-EQUIVALENCE.md

Second-pass content-equivalence / disposition audit. Supplements
CODE-ROOT-INVENTORY.md and CODE-ROOT-CROSSCHECK.md, which established
directory-level census but not content disposition. Read-only: no checkout,
reset, merge, cherry-pick, commit, or deploy performed. Canonical HEAD used
throughout: `9f9bf3519457479347113883a591c7cb92bce697`.

## Correction to prior counts

The prior reconciliation (both the original pass and the first supplemental
sweep) stated "22 worktrees" / "REGISTERED + EXISTS: 22/22". Re-running
`git -C ~/code/disability-collective-ai worktree list --porcelain | grep -c
"^worktree "` gives **23**, confirmed by independently counting
`ls -d ~/code/disability-collective-ai-*` (23 sibling directories) + main
itself. **The correct count is 23 registered worktrees (main + 22 sibling
worktrees).** This was a real counting error in the prior passes, not a
fabricated premise — see GAP-LEDGER G-043.

## Method

For every non-main worktree: `git merge-base`, `git rev-list --count` in
both directions from the merge-base, and `git cherry <canonical-HEAD>
<worktree-HEAD>` (patch-id comparison: `-` = patch already equivalent to
something in canonical history, `+` = genuinely new patch). Where commits
were genuinely new, `git diff --stat <merge-base> <head>` was read to
identify actual file-level content, then cross-checked against canonical
`git ls-files` and the `cripminds-preservation/documents/off-main-2026-08-16/`
export set.

## Part A — per-worktree disposition (all 22 non-main worktrees)

| Worktree | HEAD | ahead | cherry (new/equiv) | Disposition | Evidence |
|---|---|---|---|---|---|
| `-article-quality` | `d55e49d` | 13 | 0 / 13 | **DUPLICATE — all 13 commits patch-equivalent to canonical.** Resolves G-010's open item for this branch. | `git cherry` |
| `-base-build` | `32aa975` | 0 | — | MERGED (0 ahead) | `git rev-list` |
| `-editorial-upgrade-v1` | `dc3186f` | 4 | 4 / 0 | **PARKED, explicitly "do not deploy as-is."** 2 docs (`production-editorial-upgrade-v1-2026-08-14.md`, `production-formula-root-cause-audit-2026-08-14.md`) preserved as off-main text exports. `automation/editorial_pairing_capture.py` (265 lines) is genuinely unique code, confirmed present nowhere else (`grep`/`find` across canonical + all worktrees) — see G-044. | `diff --stat`, `find` |
| `-eval-batch-1` | `691c365` | 0 | — | MERGED | `git rev-list` |
| `-format-lab` (v0) | `4df5770` | 2 | 2 / 0 | PARKED. Doc preserved as off-main export. `format-lab-temporal-gap.html` (347 lines) unique, not preserved outside this branch lineage — see G-044. | `diff --stat` |
| `-format-lab-v1` | `7f38b47` | 3 | 3 / 0 | PARKED, cumulative superset of v0. Doc preserved. Same HTML file as v0 (unpreserved outside branches). | `diff --stat` |
| `-format-lab-v2` | `40dd5af` | 4 | 4 / 0 | PARKED, cumulative superset of v0+v1. Doc preserved. Adds `what-the-room-heard.html` + `assets/format-lab-v2/room-source.ogg` — **these two happen to be incidentally preserved** inside `cripminds-preservation/evaluations/cripminds-five-article-2026-08-16/` (confirmed present there, byte content not diffed) as a side effect of that Jekyll-site backup, not a deliberate Format Lab preservation. `format-lab-temporal-gap.html` still has no copy outside the branches. | `diff --stat`, `find` in preservation root |
| `-human-detail-provenance` | `c7ef217` | 2 | 0 / 2 | **DUPLICATE — both commits patch-equivalent to canonical.** Resolves G-010's open item for this branch. | `git cherry` |
| `-integration-observability` | `7a367f4` | 0 | — | MERGED | `git rev-list` |
| `-integration-release` | `691c365` | 0 | — | MERGED | `git rev-list` |
| `-opening-quality` | `8b8c033` | 2 | 1 / 1 | **Mixed, both resolved.** Commit `8b8c033` (docs) is patch-equivalent — its content is folded into canonical's aggregated "article-quality evidence pass" LOGBOOK entry. Commit `6fe020b` (feat: B/C opening-quality shadow — adds `opening_template_corpus_sweep.py`, `opening_template_detector.py` + tests) is patch-*different* from canonical, but files of the **same names already exist on canonical `main`** (confirmed via `git ls-files`) — i.e. **SUPERSEDED BY A LATER, INDEPENDENTLY-WRITTEN CANONICAL IMPLEMENTATION**, not missing work. Resolves G-010's open item for this branch. | `git cherry`, `git ls-files` on main |
| `-ops-release-hardening` | `394f2b7` | 1 | 0 / 1 | **DUPLICATE — patch-equivalent to canonical.** Resolves G-010's open item for this branch (canonical's independent `release_preflight.py` is confirmed the same patch, not merely "not confirmed identical" as previously stated). | `git cherry` |
| `-persona-biography` | `e93bb1b` | 3 | 3 / 0 | **CONCLUSIVELY RESOLVED, not a gap.** Canonical commit `dbe0a96`'s own message states explicitly: "Reconstructed as a single commit rather than merging the research branch... excludes `automation/persona_biography_review_capture.py` (a research-only semantic spot-check capture tool, explicitly 'NOT part of the pipeline' per its own docstring, not imported by any production code)." The 3 "ahead" commits appearing patch-different is *expected and intentional* — the pipeline logic was deliberately hand-reconstructed into AP1, and the one file left behind was deliberately excluded, not overlooked. | `git show dbe0a96` (commit message) |
| `-pub-surface-prod-candidate` | `1772d30` | 3 | 3 / 0 | PARKED. Adds a full alternate Jekyll publication-surface prototype: `_config.yml`, `_layouts/work.html`, `_works/what-the-room-heard.html`, `research.html` + the `.ogg` asset. The `.html`/`.ogg` content happens to exist in the preservation root's five-article-eval site backup (see `-format-lab-v2` row), but the `_layouts/work.html` + `_config.yml` **site-integration/packaging is unique and not preserved anywhere outside this branch** — see G-044. | `diff --stat` |
| `-publication-model-v1` | `90988d7` | 5 | 5 / 0 | PARKED, superset of `-format-lab-v2` plus `cripminds-publication-model-v1-2026-08-14.md`. That doc was **separately recovered onto canonical `main`** (Phase 3B, already confirmed in the original reconciliation) — doc content is safe; HTML/asset findings same as `-format-lab-v2`. | `diff --stat` |
| `-publication-surface-v1` | `4a9505a` | 6 | 6 / 0 | PARKED, superset of `-publication-model-v1` plus `-pub-surface-prod-candidate`. Adds `cripminds-publication-surface-v1-2026-08-14.md` (preserved as off-main export). Jekyll layout/config findings same as `-pub-surface-prod-candidate`. | `diff --stat` |
| `-srv1` | `37432b9` | 1 | 0 / 1 | **DUPLICATE — patch-equivalent to canonical** (confirms the original reconciliation's earlier patch-id check). | `git cherry` |
| `-story-rejection-release` | `cff6dbc` | 1 | 0 / 1 | **DUPLICATE — patch-equivalent to canonical.** | `git cherry` |
| `-story-rejection-v11-fix` | `d0204aa` | 0 | — | MERGED | `git rev-list` |
| `-testimony-architecture` | `41e6c5e` | 1 | 1 / 0 | Doc-only commit (`.claude/testimony-L1-L2-audit-2026-08-14.md`, 373 lines). **Fully preserved** as an off-main text export in `cripminds-preservation/documents/off-main-2026-08-16/` — unmerged as code/live-doc, but content is not at risk. Not a gap. | `diff --stat`, off-main file list |
| `-worktree` | `c485236` | 0 | — | MERGED | `git rev-list` |

## Divergent `.claude` state docs — confirmed NOT a live contradiction

Checked whether `WORK.md`/`LOGBOOK.md`/`PROJECT-MAP.md`/`project-manifest.json`
exist at all on the 12 worktrees with genuinely-ahead or format-lab-lineage
commits: **none of them contain any of these four files** (`git ls-files`
returned empty for all). This is expected, not a divergence to reconcile —
these four files were only created 2026-08-16 (per LOGBOOK's own "Project
memory recovery + installation" entry), and every one of these branches was
cut on or before 2026-08-15. `CONTEXT.md`'s last commit on the checked
branches (`editorial-upgrade-v1`, `persona-biography`) is `9d2c924`
(2026-08-09), predating the branch point — confirming these are simply the
historical version inherited at branch-time, not a divergent edit. **No
gap.** This confirms the task's caution was warranted in principle, but the
evidence resolves it cleanly rather than surfacing a real contradiction.

## Part B — non-git directory content audit

### `disability-collective-ai-eval-batch-1-harness/` (51 files, 2.6M)

Full recursive inventory taken. Contains `run_one_article.py` (+ compiled
`.pyc`) and `results/{01..07}/` — each with `run_result.json`,
`captured.json`, `prompt_calls.json`, `actual_models.json`,
`engagement_shadow.db`, `_drafts/*.md`, `_reviews/*.md`. Titles confirmed:
"Follow Your Nose" (01), "You Can't Walk Into A Gallery" (02), "Sniff It
Out" (03), "Who Held The Pen When Christy Brown Painted" (04), "Nine Codecs
And Not One Of Them Is For Her" (05), "What Kelsie Conley Meant By Slow"
(06), "23,000 Jobs And The Question Nobody Asks" (07).

**Definitive resolution of G-041 (raised in the first supplemental pass):**
the `/tmp/claude-501/.../scratchpad/five-article-eval/artifacts/{01..07}/`
copy this reconciliation's original UNPRESERVED-ARTIFACTS.md flagged as
"6 of 7 unpreserved, /tmp only" **still exists**, and `diff -rq` against
`disability-collective-ai-eval-batch-1-harness/results/{01..07}/` returns
**zero differences for all 7 candidate directories — fully byte-identical.**
The only delta between the two locations is a single-line
`discovery_snapshot_provenance.txt` (`source: /srv/data/hermes/workspace/
disability-ai-collective/disability_findings.db (read-only copy)`) present
only in the `/tmp` copy — trivial, not evidence data.

**This means the original "at risk" framing was overstated**: a complete,
durable, non-ephemeral copy of all 7 candidates already exists in `~/code`,
not only in `/tmp`. Representative hash (SHA-256):
`results/07/prompt_calls.json` = `ae481358e88a3afe82bc4d9adfa3bccb59289e605088edd0e2112734673b5b2c`;
`results/01/run_result.json` = `9a98bb008d2b97afb6ffc36885c049de72241a7b83ebd1c38a34e44038796f73`.

The directory is already footnoted by name in `PROJECT-MAP.md:153` ("sibling
plain dir `-eval-batch-1-harness` (non-git, `run_one_article.py`) sits
alongside, not a worktree") — but its *content* had never been
cross-referenced against the `/tmp` finding until this pass.

### `cripminds-project-inventory-2026-08-16/` (5 files, 44K)

Re-read `CRIPMINDS-PRESERVATION-RISKS.md` in full. All 9 of its findings
were already cross-checked against current state in the original
reconciliation's INVENTORY.md §F (with a status column: RESOLVED /
PARTIALLY RESOLVED / STILL OPEN per finding). This second pass identifies
**no additional authority surface or artifact** in this document beyond
what's already captured in GAP-LEDGER G-012 and G-013. Confirmed
byte-identical to its mirrored copy inside
`cripminds-preservation/manifests/inventory-2026-08-16/` (already noted in
the original reconciliation; re-confirmed here, not re-diffed byte-for-byte
in this pass since the original `diff -rq` finding stands and nothing in
this repo has touched either copy since).

### `cripminds-preservation/` (314M, not re-crawled/reorganized)

Not rewritten or reorganized, per instruction. Cross-checked its own
`PRESERVATION-MANIFEST.json`/`README.md` claims (already fully inventoried
in the original reconciliation's INVENTORY.md §F) against this pass's new
findings: it preserves `documents/off-main-2026-08-16/` (8 `.md` exports via
`git show branch:path` — confirmed above to correspond to the doc-only
content found on the format-lab/publication-surface/editorial-upgrade/
testimony-architecture branches), `engineering/cj1-cj2-2026-08-16/` (650
files), `evaluations/cripminds-five-article-2026-08-16/` (the full Jekyll
site backup that incidentally also contains `what-the-room-heard.html` and
`room-source.ogg`), a full git bundle, `manifests/`, `reader-lab/`,
`trident/probe_out-baseline-attempt-2/`, and `whitepaper/v0.2/`.

**Confirmed still absent from `cripminds-preservation/` after this pass**:
`format-lab-temporal-gap.html` (present in 5 unmerged branches, never
extracted as a standalone artifact), `automation/editorial_pairing_capture.py`
(present only in `-editorial-upgrade-v1`), and the `_layouts/work.html` +
`_config.yml` Jekyll integration files (present only in
`-pub-surface-prod-candidate` and `-publication-surface-v1`). None of these
are literally at risk of deletion (they live on protected branch refs, not
dangling commits — `git worktree prune --dry-run` and the absence of any
`git gc`/branch-deletion activity confirm this), but none are indexed by
name in canonical docs or the preservation manifest either. See G-044.
