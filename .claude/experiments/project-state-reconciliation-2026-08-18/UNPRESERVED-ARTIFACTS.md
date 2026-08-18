# UNPRESERVED-ARTIFACTS.md

Temp-to-evidence completeness check. Nothing here has been copied or moved —
discovery only. Disk space is not a constraint (27Gi free / 460Gi).

## At-risk (needs preservation, no canonical copy) — 4 groups

### 1. "Sofa Real Article Test 1" — HIGHEST RISK
| | |
|---|---|
| Location | `~/.claude/jobs/2c987bae/tmp/` (~30 files: `sofa-b1..b4.md`, `sofa-form1.md`, `sofa-form1-1.md`, `sofa-shadow.md`, `legacy-shadow.md`, grounding-audit JSON, `sofa_discovery_shadow*.py`, `sofa_{b1,b2,b3,b4,form1,form1_1,shadow}_run.py`, `audit_*.py`, `generate.py`, `dry_run_form1_1.py`) plus `/tmp/sofa_real_ab_1_harness.py`, `/tmp/grounding_remote.py`, `/tmp/grounding_anchor_terminal_punct_test.py` |
| Purpose | A live A/B test of legacy-shadow vs. sofa-shadow pipelines against a **real fetched** Edinburgh Art Festival review (Sandra George source material) — the closest thing in this whole project to a real (non-synthetic) Sofa shadow run |
| Last modified | 2026-08-18, ~15:00–17:48 |
| Canonical copy? | **NO.** `.claude/experiments/sofa-shadow-cases/` and `sofa-shadow-output/` only contain a synthetic fixture (`synth-1-*`) |
| Risk | The `/tmp`-root files' own header states they live "only in `/tmp/cripminds-sofa-real-test-1`" (a detached worktree) — **that worktree has already been confirmed deleted**. These files are the only surviving copy of a real-material Sofa shadow test. |
| Suggested destination | `.claude/experiments/sofa-real-article-test-1-2026-08-18/` |
| Required action | Owner decision: preserve verbatim (do not silently improve/rerun) before the job dir is cleaned up |

### 2. CJ1-v3 / CJ2-stage-B2 development artifacts
| | |
|---|---|
| Location | `~/.claude/jobs/2c987bae/tmp/{cj2/*, b2_v1_*_{system,preflight,user_template}.txt, stage-c-first-probe-bundle/*.py (15 scripts) + .probe_fixtures/ (~1.3MB), cj2-b2-v141-run/automation/*}` + ~25 `*_static_tests.py.log` regression logs |
| Purpose | Runnable probes/fixtures/regression logs backing the written conclusions in `cj1-v3-friction-gate-2026-08-11.md` and `cj2-competitive-reframing-design-2026-08-11.md` |
| Last modified | 2026-08-11 to 2026-08-13 |
| Canonical copy? | **PARTIAL.** Written conclusions are preserved in the two `.claude/experiments/*.md` docs; the underlying runnable evidence is not in the repo anywhere (also separately confirmed still-untracked-on-main by the PI2 cross-check, see GAP-LEDGER G-013) |
| Suggested destination | `.claude/experiments/cj1-cj2-b2-dev-artifacts-2026-08-11/` (regression `.log` files: low priority, reproducible by rerunning — optional) |

### 3. Five-article evaluation — RESOLVED 2026-08-19, was overstated as at-risk
| | |
|---|---|
| Location | `/tmp/claude-501/.../disability-collective-ai/.../scratchpad/five-article-eval/artifacts/{01..07}/` **and** `~/code/disability-collective-ai-eval-batch-1-harness/results/{01..07}/` |
| Purpose | Full pipeline eval run, 7 candidate articles with complete generation provenance |
| Last modified | 2026-08-16 11:14 (both copies) |
| Canonical copy? | Artifact 01 ("Follow Your Nose") matches the published draft + reviews + assets in `cripminds-preservation/evaluations/cripminds-five-article-2026-08-16/`, as originally noted. **Correction (2026-08-19 second-pass audit)**: the other 6 candidates are NOT actually confined to an ephemeral `/tmp` scratchpad — `disability-collective-ai-eval-batch-1-harness/` in `~/code` (a durable, non-git plain directory already footnoted in `PROJECT-MAP.md:153`) contains all 7, and `diff -rq` confirms it is **byte-identical** to the `/tmp` copy for every candidate. Representative SHA-256: `results/07/prompt_calls.json` = `ae481358e88a3afe82bc4d9adfa3bccb59289e605088edd0e2112734673b5b2c`. |
| Risk | **Downgraded to LOW.** The `/tmp` copy could still vanish on reboot, but the `~/code` copy is durable and unaffected by that. Only genuine gap remaining: this data isn't indexed inside `.claude/experiments/` under its own name (it's known-to-exist via PROJECT-MAP.md's footnote, but not cross-referenced there as *containing* the 6 missing eval candidates). |
| Suggested destination | Low-priority: add a one-line pointer in `PROJECT-MAP.md`'s footnote (or index the existing `~/code` directory in `.claude/experiments/`) rather than treating this as an active preservation task | See GAP-LEDGER G-041 and WORKTREE-CONTENT-EQUIVALENCE.md Part B for full evidence. |

### 4. Editorial-pairing blind test
| | |
|---|---|
| Location | `/tmp/claude-501/.../disability-collective-ai-reader-lab-worker/.../scratchpad/editorial_pairing/` (`f1_A/B`…`f4_A/B` + blind pair files) + `persona_bio_spotcheck/{case1,case2}.txt` |
| Purpose | Blind A/B editorial-quality pairing test, 4 candidate articles ("Ledger Item", "The Six-Second Rule", "Nine Days", "Rewind") + an editorial-director revision-note simulation |
| Last modified | 2026-08-14 16:57 |
| Canonical copy? | **NO** — none of the 4 titles found in `_drafts/`, `_posts/`, or `.claude/experiments/` |
| Suggested destination | `.claude/experiments/editorial-pairing-blind-test-2026-08-14/` |

### 5. Unmerged-branch-only non-doc artifacts (found 2026-08-19, G-044) — LOW risk, unindexed

| | |
|---|---|
| Location | `automation/editorial_pairing_capture.py` (265 lines, only on `-editorial-upgrade-v1`); `format-lab-temporal-gap.html` (347 lines, on `-format-lab`, `-format-lab-v1`, `-format-lab-v2`, `-publication-model-v1`, `-publication-surface-v1`); `_layouts/work.html` + `_config.yml` Jekyll integration (on `-pub-surface-prod-candidate`, `-publication-surface-v1`) |
| Purpose | A research-only capture tool, an interactive HTML prototype (Format Lab), and a Jekyll site-integration scaffold |
| Canonical copy? | NO for all three — confirmed absent from canonical `main`, from `cripminds-preservation/`, and from every other worktree via `find`/`grep` |
| Risk | LOW, not urgent — these live on protected git branch refs (not dangling commits), so they survive normal operation. They would only be lost if one of these 5 branches were explicitly deleted, which is not currently planned. |
| Suggested destination | Optional: extract to `.claude/experiments/` for indexing if these branches are ever considered for deletion; no action needed otherwise |

## Checked and found NOT at risk

- **AR2/AR3 harness + blinded outputs** (`~/.claude/jobs/2c987bae/tmp/{ar2,ar3}/*`) — fully preserved; canonical `ar2-silent-lens-2026-08-17-articles/` and `ar3-unforced-human-presence-2026-08-17-articles/` match, and the harness code itself lives in `automation/ar2_silent_lens_harness.py` / `automation/ar3_unforced_human_presence_harness.py`.
- **`tmp/scout/{evidence,cards,articles,sources}`** — empty, 0 files.
- **`/tmp/cripminds-sofa-real-test-1`** — confirmed does not exist (already gone; its content is item 1 above, orphaned in `/tmp` root and the job dir).
- **12 `/tmp/cripminds-*-review` skeleton dirs** (`cripminds-copy-review`, `cripminds-final-build`, `cripminds-full-public-audit{,-2,-3,-final}`, `cripminds-lens-copy-review`, `cripminds-portrait-review`, `cripminds-public-labs-review`, `cripminds-public-sync-review`, `cripminds-rewrite-check.7DVCya`, `cripminds-shared-copy-review`, `cripminds-world-range-review`) — all empty, 0 files at any depth.
- **`site-cand/` SEO/crawler scratchpad** — preserved; matches live `crawler_config.yaml`/`statistics_report.json`/`calibration/runner/` in the repo.
- **Bulletin PDFs, room-acoustics WAV/RMS files** — unrelated source material / an unrelated audio task that happened to share a cwd; out of scope.
- **`tmp/{worktree_detail.txt, claude_files.txt, ...}` verification scratch** — these are this reconciliation job's own sub-agent outputs; superseded by this synthesis, not separately at risk.

## Summary count (updated 2026-08-19)

**3 groups genuinely at meaningful risk** (groups 1, 2, 4 — Sofa Real
Article Test 1, CJ1/CJ2 dev artifacts, editorial-pairing blind test), plus
**1 group at LOW risk** (group 5, unmerged-branch-only non-doc artifacts —
safe unless branches are deleted). **Group 3 (five-article eval) is
resolved as not at risk** — a durable, byte-identical `~/code` copy exists.
Highest-urgency remains group 1 (Sofa Real Article Test 1) — its stated home
directory is already deleted, making the job-dir/`/tmp`-root copies the sole
surviving evidence.

---

## STATUS CORRECTIONS — TRIDENT COUNTERPART AUDIT (2026-08-19)

Original wording above is left verbatim. These corrections supersede it where they conflict.

**Group 1 — Sofa Real Article Test 1: RESOLVED, and its risk framing was wrong in an
instructive way.** The row above states the worktree "has already been confirmed deleted." It
was not deleted — it is alive and complete on **trident** at `/tmp/cripminds-sofa-real-test-1`,
absent only on the Mac, because the runs route through CLIProxy which the Mac cannot reach. The
job-dir copy was a *partial* copy, not the sole surviving evidence. Preserved in full:
`.claude/experiments/sofa-real-ab-1-2026-08-18/` (see G-045). Three further group-1 files living
in the Mac `/tmp` root were missed by that pass and are now preserved too (G-048).

**Group 2 — CJ1-v3 / CJ2-B2: RESOLVED, overstated.** "The underlying runnable evidence is not in
the repo anywhere" is literally true and materially misleading: a complete durable backup exists
at `~/code/cripminds-preservation/engineering/cj1-cj2-2026-08-16/` (650 files, 33 MB). Verified by
hash — all 52 untracked `cj*.py` byte-identical, 18 `.probe_fixtures` dirs, CJ2 stage prompts under
canonical `frozen_prompts/` names. 68 residual files had no durable copy and are now preserved at
`.claude/experiments/cj1-cj2-b2-dev-artifacts-2026-08-11/` (G-046). No trident counterpart exists;
this work ran on the Mac.

**Group 4 — Editorial-pairing blind test: LOST.** The four candidate drafts and their blind-pair
files no longer exist anywhere — Mac, job dirs, repo, `cripminds-preservation/`, or trident. The
scratchpad now holds one empty `blind/` directory, mtime 2026-08-19 00:00, minutes after this file
was written. `persona_bio_spotcheck/case{1,2}.txt` survived and are preserved at
`.claude/experiments/editorial-pairing-blind-test-2026-08-14/`. See G-047. Do not reconstruct.

**Group 5 — unchanged.** Branch-only artifacts remain on protected refs; not touched, not merged.

**Revised summary count:** of the 4 groups once considered at meaningful risk, 1 is now preserved
in full (group 1), 1 was largely already safe with its residue now preserved (group 2), 1 is
resolved as never-at-risk (group 3), and 1 is **lost** (group 4). Group 5 remains LOW.
