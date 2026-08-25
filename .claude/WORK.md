# WORK — Canonical Current State

**This is the authoritative entry point for CripMinds project state.** It is mutable and
describes CURRENT TRUTH only — not a diary. History lives in `.claude/LOGBOOK.md`. Physical
topology (worktrees, branches, preserved evidence locations) is tracked in
`.claude/PROJECT-MAP.md`. Deep safety-gate mechanics, doctrine, and persona-architecture detail
that predate this reconciliation and were not contradicted by it live in
`.claude/archive/WORK-2026-08-17-superseded.md` — read that for the "why," this file for the
"what, right now."

**Maintenance rule (unchanged from the prior version, restated because the prior file broke it):**
every material production release, safety-invariant change, or architectural decision must update
`LOGBOOK.md`, and this file if current state changed, in the same or an adjacent commit. If a
section here is about to become a narrative, it belongs in a linked document instead.

Last reconciled: **2026-08-25**, against `origin/main` HEAD `14997f07e23601f8fc7b920aed7ae15e2cb2e5cf`
(PR #26 merge). This reconciliation was triggered by discovering a local checkout
(`~/code/disability-collective-ai`, HEAD `732c84f`) had diverged from `origin/main` since
2026-08-19/20 and accumulated 38 unpushed commits — see `.claude/experiments/writer-grounding-production-migration-preservation-2026-08-25.md`
for full disposition. **Do not perform further canonical-tracker edits from that local checkout —
work from a worktree based on current `origin/main`.**

---

## PRODUCTION BASELINE

- `origin/main` HEAD: `14997f07e23601f8fc7b920aed7ae15e2cb2e5cf`
- **PR #26 (main-site IA + visual-language redesign v2): COMPLETE and DEPLOYED.** GitHub Pages
  run `32879430779`, deployed SHA matches `origin/main`. Live-verified 2026-08-25: Home, Articles,
  About, Press, Articles search/count all PASS.
- Current publication counts (live-verified): **143 total, 41 withdrawn, 102 readable**
  (3 Latest / 99 archive; collection counts 4/9/4/3).
- Do not reopen D1.x visual design unless a concrete production regression is found.

## COMPLETED

- **LC1 legacy-corpus integrity programme — COMPLETE.** 142/142 articles reviewed (PRs #1–24,
  2026-08-24/25). First-person factuality axis closed: 40 corrections, 2 withdrawals (`b7492a5`,
  PR #24). Readable/withdrawn model above reflects this closure.
- **Swan Care cluster** — closed, 0 withdrawals, 3 corrections (fixed independently on both the
  local archive line and `origin/main`, same underlying patch).
- **Legacy P0 care-labor correction** — closed against the actual tribunal record (fixed on both
  lines, same patch).
- **Persona "Wound" fabrication clusters, partially closed:**
  - Pixel Nova (gallery/docent scene) — fixed, PR #10.
  - Maya Flux (wedding scene) — fixed, PR #12.
  - Siri Sage — the 4 specific known instances (Rijksmuseum + Seville visits, 2 further dated
    visits) fixed in the LC1 closure pass (`f1c2344`, 2026-08-25). **This was explicitly not a
    corpus-wide sweep** — see BLOCKED/OUTSTANDING.
- **Pre-fork safety-gate stack** (AP1, APE2, PS1, LPF1, Persona Brief↔Writer Reconciliation,
  Story Rejection V1.1) — shipped 2026-08-15/17, predates the fork point, ancestor of current
  `origin/main`. Not independently reverified in this pass; no contrary evidence found. Full
  mechanics: `.claude/archive/WORK-2026-08-17-superseded.md` `## 3`.

## LIVE / CURRENT BUT NOT FULLY CUT OVER

- **`NEW_ENGINE_V1` exists and has run successfully.** Implements
  `DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING`, explicitly built on the frozen
  writer-grounding work rather than as a second architecture (see `.claude/experiments/writer-grounding-production-migration-preservation-2026-08-25.md`).
  First natural `CURRENT_ENGINE` production run: `production-20260825T070003Z-5a5f17d6`
  (2026-08-25 09:00 CEST) — full editorial path (source→discovery→anchor→form→writer→grounding)
  PASS, 0 `TRUE_UNSUPPORTED`, ACCEPT.
- **Same-day fail-open bug found and fixed** (`b7800ee`): publication-safety check 9 was reading
  an extraction *failure* as an absence of contradictions (= pass). Now requires positive evidence
  that fact-checking actually executed. The editorial path itself was sound; the defect was
  publication-safety-only. Engine was not rolled back.
- **Engine default remains `LEGACY`.** `automation/engine_switch.py`: `DEFAULT = LEGACY`; an
  unset `CRIPMINDS_ENGINE` env var changes nothing. `CRIPMINDS_ENGINE=new_engine_v1` is opt-in
  only. Unknown values fail closed (raise, never silently default). No post-start fallback — once
  `new_engine_v1` begins a run, it owns that run; a HOLD is a result, not a reason to re-run on
  legacy. Rollback = remove the env var from the cron line; no data migration involved.
- **Do not conflate "implemented / live-capable" with "default production engine."** They are
  different facts.

## INTENTIONALLY DEFERRED

- **WG-7 / further Edinburgh grounding experiment / new FORM version.** Owner-stopped 2026-08-19
  (`3a05f61`, on `archive/writer-grounding-production-migration-2026-08-20`). Standing
  prohibition still in force: reopen only if a later transfer/production test reveals a
  reproducible grounding failure mapping back to this architecture.
- **CJ-2 competitive-reframing routing architecture** — OFF by design (`CJ2_INTEGRATION_MODE`
  defaults `"OFF"`), per the pre-fork baseline. Not reverified this pass; no evidence found of
  activation on `origin/main`.
- **L2 testimony (active companion-source retrieval)** — OFF by design, unchanged.

## SHADOW / UNRATIFIED

- **Sofa Method / Article Form.** `SOFA-METHOD.md` exists only in the local historical checkout
  and the archive branch — it never landed on `origin/main`, and no owner-ratification decision
  for it exists anywhere on origin. Conceptually, its ARTICLE FORM stage lives on inside
  `NEW_ENGINE_V1`'s pipeline, but the standalone Sofa Method framework itself remains unratified
  as its own artifact.
- **Persona-routing architecture Phase 3** (CJ-2-based competitive reframing, Siri Sage's
  OWNERSHIP prompt clause, the FORBIDDEN_DEFAULTS/Maya Flux vocabulary collision) — confirmed not
  started as of the pre-fork baseline; not reverified this pass, no origin evidence of having
  since been done. Worth a light recheck in a future pass, not currently blocking anything.

## BLOCKED / OUTSTANDING

- **Legacy prompt/rule inventory's 4 `MUST_FIX_BEFORE_PRODUCTION_MIGRATION` + 24
  `CONSOLIDATE_BEFORE_PRODUCTION` items — NEEDS OWNER DECISION.** This triage
  (`.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/OWNER-TRIAGE.md`) exists only on
  `archive/writer-grounding-production-migration-2026-08-20`; it was never carried onto origin, and
  `NEW_ENGINE_V1`'s implementation contains no reference to it. Do not assume it's still blocking,
  and do not assume it was silently resolved — re-triage the 28 flagged items against
  `NEW_ENGINE_V1` as actually built before treating either assumption as fact.
- **Local Phase-2 passive-capture harness's 0/3 sample target — SUPERSEDED.** The underlying goal
  (real signal on the new engine against real production articles) was reached through a stronger
  mechanism instead: an actual live opt-in run with the full pipeline passing end-to-end
  (2026-08-25), rather than the originally-planned passive-shadow-capture harness. That harness
  code itself never advanced past 0/3 and is not needed now.
- **Corpus-wide "wound rule" sweep — STILL REQUIRED if full-corpus assurance is wanted.** Per
  `f1c2344`'s own commit text, only already-identified clusters (Zen Circuit's car/driveway scene
  ×3, Siri Sage ×4 visits, Pixel Nova, Maya Flux) have been fixed; "a corpus-wide application of
  the clarified rule remains outstanding and is reported rather than attempted here."
- **~20 stale worktrees with no matching merged PR** (`format-lab-v0/v1/v2`,
  `persona-safety-fail-closed`, `story-rejection` variants, `visual-study/variant-a–d`, etc.) —
  inventoried, not yet classified merged-by-direct-push vs. genuinely abandoned. See
  `.claude/PROJECT-MAP.md`.
- **Data-loss risk on the local-only writer-grounding/production-migration line: RESOLVED.**
  Preserved on `archive/writer-grounding-production-migration-2026-08-20` (pushed to origin,
  SHA-verified). The local checkout itself remains diverged and should not be used for further
  canonical work.

## DOCUMENT INDEX

| Document | Status | What it's for |
|---|---|---|
| `.claude/WORK.md` | **CURRENT** | this file |
| `.claude/LOGBOOK.md` | **CURRENT** | chronological history, compact entries |
| `.claude/PROJECT-MAP.md` | **CURRENT** | repository/worktree/branch topology |
| `.claude/project-manifest.json` | **CURRENT (machine-generated)** | same, machine-readable |
| `.claude/archive/WORK-2026-08-17-superseded.md` | **HISTORICAL** | full pre-fork state: doctrine, conceptual architecture, safety-gate mechanics (AP1/APE2/PS1/LPF1), persona-architecture Phase 3 backlog — not reverified 2026-08-25, not contradicted either |
| `.claude/experiments/writer-grounding-production-migration-preservation-2026-08-25.md` | **CURRENT (disposition record)** | writer-grounding/production-migration archive-branch disposition |
| `archive/writer-grounding-production-migration-2026-08-20` (git branch) | **HISTORICAL, preserved** | 38-commit writer-grounding/production-migration/Sofa evidence line, owner-stopped, not production code |
| `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/OWNER-TRIAGE.md` (on archive branch) | **NEEDS RE-TRIAGE** | 4 must-fix / 24 consolidate items, not yet checked against `NEW_ENGINE_V1` |
| `.claude/current-work.md` | **SUPERSEDED (self-marked)** | pre-2026-08-16 historical log |
| `.claude/master-roadmap-2026-08-13.md` | **HISTORICAL, frozen 2026-08-13** | CJ-2/B2 phase table, superseded by Sofa Method → `NEW_ENGINE_V1` lineage |
| `.claude/reader-lab-handoff/*` | **EVIDENCE-ONLY, pre-dates LC1** | RL-2026-001 ops-request/receipt/analysis trail |
| `PIPELINE.md` | **HISTORICAL (not rewritten this pass)** | describes a pipeline shape 5+ months out of date; needs a dedicated technical-documentation pass, not a reconciliation-pass rewrite |
| `docs/DISCOVERY.md` | **HISTORICAL (self-marked)** | describes a deleted script |
| `.claude/legacy-corpus-integrity-phase1-2026-08-16.md` + `.claude/audits/*.json` | **CURRENT** | original LC1 Phase 1 audit that the now-complete LC1 programme executed against |

---

*Update this file when current state changes. Do not let it grow into a diary — if a section is
about to become a narrative, it belongs in a linked document instead, with a pointer here.*
