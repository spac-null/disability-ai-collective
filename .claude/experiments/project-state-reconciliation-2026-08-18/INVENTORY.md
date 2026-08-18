# Project State Reconciliation — INVENTORY

Discovery-only audit. No canonical docs edited. Produced by 6 parallel read-only
research passes on 2026-08-18. This file inventories every state source that was
actually inspected and what was found in it, at a high level — see the companion
docs for the synthesized gap ledger.

Authority order used throughout (per `PROJECT-MAP.md`'s own stated rule, applied
here): (1) direct runtime/git/DB evidence, (2) frozen experiment artifact,
(3) explicit owner decision, (4) current canonical doc, (5) historical doc,
(6) inference/memory. Claude-local/session memory was NOT used as authority for
any fact in this ledger — everything below is evidence-sourced.

## A. Canonical `.claude/` state docs (repo: `~/code/disability-collective-ai`)

| File | mtime | Git status | As-of claim |
|---|---|---|---|
| `WORK.md` | 2026-08-17 18:56 | clean, = HEAD `9f9bf35` | "Last reconciled 2026-08-17 (AR3-B release)" |
| `LOGBOOK.md` | 2026-08-17 21:49 | **modified, uncommitted** (Scout V0 entry) | last committed entry 2026-08-17 |
| `CONTEXT.md` | 2026-08-16 22:15 | clean | operational reference, no phase narrative |
| `PROJECT-MAP.md` | 2026-08-17 16:30 | clean | installed 2026-08-16, "topology only, not current truth" |
| `project-manifest.json` | generated 2026-08-17T16:56 UTC | clean | machine snapshot, HEAD `3225ea1` (one commit behind current HEAD `9f9bf35`) |
| `current-work.md` | 2026-08-16 12:15 | clean | self-marked SUPERSEDED by WORK.md, kept as diary/archive |
| `SOFA-METHOD.md` | **2026-08-18 11:53** | **untracked, never committed** | self-declared "CANONICAL OPERATIONAL METHOD" |
| `master-roadmap-2026-08-13.md` | 2026-08-14 03:55 | clean | frozen 2026-08-13, WORK.md calls it HISTORICAL |
| `original-blueprint-A-M-reconciliation-2026-08-13.md` | 2026-08-14 03:55 | clean | frozen 2026-08-13 |

**Headline finding**: everything from 2026-08-10 through the 2026-08-17 Scout V0
entry is documented in WORK.md/LOGBOOK.md. Everything dated 2026-08-18 (Sofa
Method canonicalization, a full pipeline audit, an architecture redesign
proposal, two shadow-code slices, the entire FOX/HOUR/MOBILE versioned rewrite
lineage) exists only as untracked files with **zero LOGBOOK/WORK.md/PROJECT-MAP
reference** — see GAP-LEDGER G-001.

## B. `.claude/experiments/` (37 top-level items, recursively inventoried)

Two lineages found:
1. **Pre-Sofa research lineage (2026-08-10 → 08-13)**: `why-we-write`,
   `fable-review-roi`, `phase-1.6-source-grounding`, `cj1-v3-friction-gate`,
   `cj2-competitive-reframing-design` (697KB), `final-evaluation-freeze-protocol`.
   All well cross-referenced in WORK.md/LOGBOOK.md.
2. **Artistic Reset → Scout → Sofa lineage (2026-08-17 → 08-18)**: AR1 → AR2 →
   AR2.1 → AR3 (→ AR3-B shipped to production) → concept-preservation (ARC1) →
   Scout V0 (SV0A, pending) → FOX/HOUR/MOBILE versioned benchmark lineage (10
   dirs, 2026-08-17/18) → `sofa-method-v0`/`v0.1`/`v0.2` → `SOFA-METHOD.md`
   (canonical) → pipeline audit → architecture proposal → shadow slices 1/1.1.
   Everything from AR1 through Scout V0 (2026-08-17) is in LOGBOOK.md. Nothing
   from 2026-08-18 onward is, except `SOFA-METHOD.md` itself naming its own
   three `sofa-method-v0*` ancestors.

No "Edinburgh" experiment lineage exists in this repo under that name — see
EXPERIMENT-RECONCILIATION.md for the correction (the actual A→B→FORM-shaped
lineage is FOX/HOUR/MOBILE; "Edinburgh" appears only as a persona-canon
birthplace detail in generated prose).

## C. Temp / job / worktree scratch locations

Checked: `~/.claude/jobs/` (one job dir, `2c987bae`, this session), `/tmp/`
root (12 empty `cripminds-*` skeleton dirs + a confirmed-gone
`/tmp/cripminds-sofa-real-test-1`), and `/tmp/claude-501/*` per-session
scratchpads. Four artifact groups found with no canonical copy — see
UNPRESERVED-ARTIFACTS.md. Disk space is not a constraint (27Gi free).

## D. Git state (main repo + 22 sibling worktrees = 23 total, corrected 2026-08-19)

Main repo `~/code/disability-collective-ai`, branch `main`, HEAD `9f9bf35`
(2026-08-17), up to date with `origin/main`. Working tree carries one modified
file (`LOGBOOK.md`) and ~90 untracked paths (Sofa/Scout/CJ1/CJ2 material).
**Correction**: an earlier pass of this reconciliation stated "22 worktrees
(main + 21)" — the verified count is **23 total (main + 22 sibling
worktrees)**; see GAP-LEDGER G-043. All 22 sibling worktrees are internally
clean (0 uncommitted changes each). A second-pass content-equivalence audit
(see WORKTREE-CONTENT-EQUIVALENCE.md) has since resolved every item G-010
originally flagged as needing owner review — 3 are confirmed patch-equivalent
duplicates via `git cherry`, and the 4th (`-opening-quality`) is confirmed
superseded by a later canonical implementation — so G-010 no longer requires
owner action. Only 2 of the last 40 commits lack any doc representation
(both minor/operational).

## E. Production state (trident, `/srv/data/hermes/workspace/disability-ai-collective`, read-only)

HEAD `9f9bf35` — matches local Mac `main` exactly, clean except 3 untracked
non-code artifacts. `CJ2_INTEGRATION_MODE` confirmed unset (OFF) at every level
(code default, crontab, secrets env). Story Rejection confirmed live and
**unconditional** (no flag gates it — it's schema-versioned, not feature-flagged).
Scout/Sofa: **zero code exists in production** — confirmed via full-tree grep,
present only as WORK.md/LOGBOOK.md prose describing future work. A
`cripminds-calibration-runner.service` systemd unit is running against an
isolated pinned checkout and is currently logging `internal_error` on its claim
endpoint — see RUNTIME-DOC-MISMATCHES.md.

## F. Preservation root (`~/code/cripminds-preservation/`) + prior PI2 audit

Well-documented by its own manifest/README (PP1/PP2, 2026-08-16, 674 files,
hash-verified). Most of the 2026-08-16 PI2 audit's 9 findings were genuinely
acted on (dangling commits fixed, Story Rejection shipped, DB naming resolved,
broken doc reference repaired). Two indexing gaps remain (`probe_out-
baseline-attempt-2/` and the 3 `manifests/inventory-2026-08-16/` filenames
aren't referenced by name in any canonical doc) and one finding is
preserved-as-backup but not actually resolved at the git level (CJ1/CJ2 engineering
files are still untracked on `main` today, same as when PI2 flagged them).

## G. Cross-model evidence (Grok / Qwen / Perplexity)

**All three specific claims are MISSING EVIDENCE** — no raw-output artifact
found anywhere in the canonical repo or preservation root for a Grok clean
first-generation comparison, a Qwen clean first-generation comparison +
reasoning trace, or a Perplexity weaker/contaminated comparison. What exists:
a generic `compare_models.py` script (Grok/Gemini/GPT-4o/Claude in its model
list, no Qwen, no Perplexity, no run output preserved), Qwen as a production
fallback-LLM/image-gen model reference only, and Perplexity/sonar as a real,
well-evidenced fact-checking API integration (different artifact than a
model-comparison test). See GAP-LEDGER G-020/021/022.

## H. Edinburgh reader feedback

**MISSING EVIDENCE** — neither Jascha's own "sofa-read" reaction nor an
outside reader's/father figure's feedback on the Edinburgh article was found
in any file across the repo or preservation root. The Edinburgh Art Festival
material that does exist in the repo is machine-generated draft content and
automated simulated-reader reviews (5-article evaluation, 2026-08-16), not
human reader feedback. See GAP-LEDGER G-023.
