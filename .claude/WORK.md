# WORK — Canonical Current State

**This is the authoritative entry point for CripMinds project state.** It is mutable and
describes CURRENT TRUTH only — not a diary. History lives in `.claude/LOGBOOK.md`. Physical
topology (worktrees, branches, preserved evidence locations) is tracked in
`.claude/PROJECT-MAP.md`. Deep safety-gate mechanics, doctrine, and persona-architecture detail
that predate this reconciliation live in `.claude/archive/WORK-2026-08-17-superseded.md` — that
file is last-known-state, **not independently re-verified against current code**, so treat it as
historical reference for the "why," not as current-state proof; this file is what to trust for
"what, right now," and only for the items its own DOCUMENT INDEX marks as re-verified.

**Maintenance rule (unchanged from the prior version, restated because the prior file broke it):**
every material production release, safety-invariant change, or architectural decision must update
`LOGBOOK.md`, and this file if current state changed, in the same or an adjacent commit. If a
section here is about to become a narrative, it belongs in a linked document instead.

**`RECONCILED_AGAINST_SHA` = `14997f07e23601f8fc7b920aed7ae15e2cb2e5cf`** (PR #26 merge,
2026-08-25). This is the `origin/main` HEAD this reconciliation was performed against — **it is a
snapshot marker, not a claim that this is still the current `origin/main` HEAD.** `origin/main`
will move past this SHA the moment normal work resumes, including the moment this file's own PR
merges. Before trusting anything in this file as current, run `git rev-parse origin/main` and
compare — do not assume `RECONCILED_AGAINST_SHA` is still HEAD.

This reconciliation was triggered by discovering a local checkout (`~/code/disability-collective-ai`,
HEAD `732c84f`) had diverged from `origin/main` at merge-base `9f9bf35` (2026-08-19/20) and
accumulated 38 unpushed commits — see `.claude/experiments/writer-grounding-production-migration-preservation-2026-08-25.md`
for full disposition. **Do not perform further canonical-tracker edits from that local checkout —
work from a worktree based on current `origin/main`.**

---

## PRODUCTION BASELINE

- **`PR26_PRODUCTION_BASELINE` (== `RECONCILED_AGAINST_SHA`): `14997f07e23601f8fc7b920aed7ae15e2cb2e5cf`.**
  This names a specific fact (PR #26 is the production baseline as of this reconciliation) —
  it does not mean this SHA is eternally "current `origin/main`." Re-check `git rev-parse
  origin/main` before relying on it as HEAD.
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
- **Persona "Wound" fabrication clusters — closed, corpus-wide, not just known instances.**
  Corrected sequence, both real and worth keeping distinct:
  - Pixel Nova (gallery/docent scene) — fixed, PR #10.
  - Maya Flux (wedding scene) — fixed, PR #12.
  - Siri Sage's 4 specifically-known instances (Rijksmuseum + Seville visits, 2 further dated
    visits) — fixed in the LC1 closure pass (`f1c2344`, PR #20, 2026-08-25 12:50 UTC). That
    commit explicitly says this was **not** a corpus-wide sweep.
  - **~90 minutes later, PR #24 (`b7492a5`, "Close the first-person factuality axis," 2026-08-25
    14:12 UTC) performed exactly that sweep**, corpus-wide: "All 103 live legacy bodies were read
    in full under the clarified rule that a persona's authored material is not evidence an event
    occurred... jobs, family, possessions, routines, **visits**, conversations, origin stories and
    dated or undated memories do not [establish a lens]. 142/142 legacy articles now carry an axis
    status." Result: 40 corrections, 2 withdrawals. The wound/fabrication failure family (personas
    presenting authored material as lived testimony — the same pattern as Siri Sage's visits) is
    the exact thing this axis checks; "visits" is named explicitly in the rule.
  - **Status: CORPUS-WIDE FAILURE FAMILY COVERED BY LC1's first-person factuality axis closure.**
    Not merely "known clusters fixed" — a full-corpus read against the governing rule was
    performed and completed, same programme, same day.
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
  publication-safety-only. Engine was not rolled back. **This is a distinct finding from the two
  contract gaps below** — different bug, different commit, same general period.
- **Two contract gaps found by the 2026-08-24 acceptance run — both RESOLVED, same commit
  (`dd7b00a`, "controlled cutover preparation — anchor invariant, failure record, engine
  switch"):**
  - **Discovery anchor validator** — Discovery asked for a source-grounded verbatim anchor, but
    nothing proved the anchor actually occurred in the source snapshot. Fixed:
    `automation/new_engine_v1/invariants.py` adds `source_anchor_quote` (additive to the frozen
    Phase-1 contract, so existing artifacts stay valid) and `check_anchor()`, a deterministic
    verbatim-substring check with one bounded, re-validated repair attempt. Wired into
    `runner.py` (called at Discovery and again post-repair). RESOLVED, verified in code.
  - **Failed-writer contract gap** — `contracts.py`'s `WRITER_OUTPUT` validation (`_require`)
    treats an empty `article_text` as a missing field regardless of `provider_status`, so a
    genuinely failed writer call could not be expressed as a valid artifact. **Still true of the
    frozen contract itself** — not amended, deliberately, to avoid invalidating already-accepted
    artifacts. RESOLVED at the runner level instead: `runner.py` (comment "PART B, 2026-08-24")
    now detects `provider_status != "ok"` before attempting to build a `WRITER_OUTPUT` artifact,
    records a separate `RUN_STATUS=PROVIDER_FAILURE`, and the run HOLDs with no `WRITER_OUTPUT`
    artifact at all. The contract's own inability to represent failure is now moot because the
    runner never asks it to.
- **The `PHASE-2` passive-capture requirement is a SEPARATE, SEPARATELY-TRACKED mechanism from
  either the acceptance run above or the natural `CURRENT_ENGINE` production run below — do not
  conflate them.** See BLOCKED/OUTSTANDING for its own re-verified status; a controlled acceptance
  run explicitly disclaims counting as a P2 sample (`automation/new_engine_v1_acceptance.py`:
  "NOT_PUBLICATION. NOT_P2_SAMPLE.").
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

- **Sofa Method / Article Form — UNRATIFIED, supported by an explicit tracked open-decision item,
  not merely a missing file.** `.claude/experiments/sofa-method-reconciliation-2026-08-19/PRESERVATION-MANIFEST.md`
  (archive branch) records this as **G-009, an explicitly named open owner decision**:
  `SOFA-METHOD.md` "still self-declares `STATUS: CANONICAL OPERATIONAL METHOD`; that remains an
  open owner decision (G-009)." The original was deliberately left untracked "to avoid committing
  an unratified status claim into a canonical-looking location" — an intentional editorial choice,
  not an oversight. No resolution of G-009 was found anywhere in either line's history. Separately,
  the file's absence from `origin/main`'s tree is also true, but is not itself the evidence for
  UNRATIFIED — G-009 is. Conceptually, its ARTICLE FORM stage lives on inside `NEW_ENGINE_V1`'s
  pipeline, but the standalone Sofa Method framework itself remains unratified as its own artifact.
- **Persona-routing architecture Phase 3** (CJ-2-based competitive reframing, Siri Sage's
  OWNERSHIP prompt clause, the FORBIDDEN_DEFAULTS/Maya Flux vocabulary collision) — confirmed not
  started as of the pre-fork baseline; not reverified this pass, no origin evidence of having
  since been done. Worth a light recheck in a future pass, not currently blocking anything.

## BLOCKED / OUTSTANDING

- **Legacy prompt/rule inventory's 4 `MUST_FIX_BEFORE_PRODUCTION_MIGRATION` + 24
  `CONSOLIDATE_BEFORE_PRODUCTION` items — UNRESOLVED, RE-TRIAGE REQUIRED BEFORE
  DEFAULT-CUTOVER DECISION.** The only proven facts: this inventory
  (`.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/OWNER-TRIAGE.md`) exists on
  `archive/writer-grounding-production-migration-2026-08-20`; the `MUST_FIX`/`CONSOLIDATE` labels
  were assigned against the historical (pre-`NEW_ENGINE_V1`) architecture; `NEW_ENGINE_V1`'s code
  contains no direct reference to these 28 entries. That is **not sufficient to conclude they
  currently block anything** — absence of a reference is not evidence of resolution, obsolescence,
  or continued relevance. A future re-triage phase should sort each item into: (A) a still-required
  invariant absent from `NEW_ENGINE_V1`, (B) an equivalent invariant already implemented
  differently, (C) obsolete because the new architecture removed the failure mode, (D)
  documentation/consolidation only, or (E) genuinely blocking. Do not port legacy rules into
  `NEW_ENGINE_V1` and do not treat this list as either satisfied or blocking until that triage runs.
- **Phase-2 passive-capture requirement — STILL OPEN, current sample count UNKNOWN.** Re-examined
  this pass; the earlier "SUPERSEDED" conclusion was unsupported and is withdrawn. What P2 actually
  validates (per `.claude/experiments/production-migration-phase2-prep-2026-08-20/PHASE2-CAPTURE-DESIGN.md`,
  archive branch): passive, `SHADOW_CAPTURE`-gated observation of the **legacy** pipeline's
  intermediate representations on real production runs, so a later comparison against the target
  architecture has frozen, faithful evidence to compare against — not a validation of
  `NEW_ENGINE_V1` running live. Confirming this is a live, separately-tracked concern on
  `origin/main`, not abandoned: `automation/shadow_capture.py` (ancestor of both lines) shipped a
  "phase2-capture-v0.1" fix (`56eba2b`, 2026-08-21) after a real capture attempt was found
  `CAPTURE_INVALID` (bundle `20260821T070006Z-647ffe6d` — captured writer output didn't match the
  persisted post-rewrite body); further capture-adjacent fixes landed through 2026-08-24
  (`a5891bd`, `cb772c2`). None of this shows a current valid-sample count. Separately, and
  explicitly: `automation/new_engine_v1_acceptance.py`'s own docstring disclaims counting toward
  this gate ("NOT_PUBLICATION. NOT_P2_SAMPLE."), and the 2026-08-25 natural `CURRENT_ENGINE`
  production run is a different mechanism entirely (an actual opt-in engine execution, not a
  passive legacy-side capture) — **neither can be cited as evidence this gate is satisfied.**
  Classification: **STILL OPEN.** Current sample count requires a Trident-side check not performed
  this pass (this reconciliation stayed git/filesystem-only). No new samples were run and no
  experiment was resumed to produce this finding — read-only code/history archaeology only.
- **Production-observability worktree (`production-observability-2026-08-20`, 2 commits,
  unmerged) — SUPERSEDED, not a current blocker.** Read-only comparison this pass: its two unique
  commits ("feat: passive OFF-by-default production capture for phase-2 comparison,"
  "fix: capture sidecar catches Exception, not BaseException") share their exact commit messages
  with two commits that DID land on `origin/main` (`b54dd70`, `82ec110`) — independently authored,
  same underlying fix, different session. `origin/main`'s version is **more advanced**: it also
  carries the `56eba2b` v0.1 capture-contract fix this worktree lacks. Diffing `shadow_capture.py`
  between the worktree and `origin/main` confirms the worktree has nothing origin doesn't already
  have in a more complete form (`except Exception` already present on origin, plus the v0.1
  contract logic entirely absent from the worktree). Was previously mislabeled "genuinely unmerged
  real work" in `PROJECT-MAP.md` on unmerged-status alone — corrected there too.
- **~20 stale worktrees with no matching merged PR** (`format-lab-v0/v1/v2`,
  `persona-safety-fail-closed`, `story-rejection` variants, `visual-study/variant-a–d`, etc.) —
  inventoried, not yet classified merged-by-direct-push vs. genuinely abandoned. See
  `.claude/PROJECT-MAP.md`.

## PRESERVATION RISK (scoped — see also `.claude/experiments/writer-grounding-production-migration-preservation-2026-08-25.md`)

- **In scope (writer-grounding / production-migration / Sofa / legacy-triage evidence):
  RESOLVED.** Preserved verbatim on `archive/writer-grounding-production-migration-2026-08-20`
  (pushed to origin, SHA-verified `732c84f`). The local checkout itself remains diverged and
  should not be used for further canonical work, but the evidence itself is durable off that one
  machine now.
- **Out of scope (the ~700 other untracked local files): RESIDUAL RISK EXISTS, not resolved, not
  claimed to be low-urgency.** This includes an explicitly **in-flight** Reader Lab round
  (RL-2026-003, `reader-lab/rounds/drafts/RL-2026-003.json` + `calibration/candidates/RL-2026-003-*.json`)
  that exists only on the one local machine, with no durable backup verified this pass. It also
  includes CJ1/CJ2 probe fixtures/scripts from an earlier, separately-superseded research track,
  and a partial local copy of the static-site-integrity-audit that a more complete version already
  covers on `origin/main`. None of this was archived, deleted, or committed this pass — it remains
  exactly where it was, and its risk is stated here rather than assumed away.

## PROPOSED NEXT PHASE (not started, not authorized by this document)

**`DEFAULT-CUTOVER READINESS RECONCILIATION`** — establish the finite set of actual blockers (or
prove none remain) to making `NEW_ENGINE_V1`/`CURRENT_ENGINE` the default, by reconciling in one
pass: the historical 4+24 legacy prompt-rule inventory (triage per the A–E taxonomy above), the
Phase-2 passive-capture gate's actual current sample count (requires Trident access this pass
didn't use), whether any further `NEW_ENGINE_V1` contract findings exist beyond the two already
resolved, and any other still-open production validation gate. Explicitly NOT this phase: no new
engine architecture, no calibration, no WG-7, no automatic porting of legacy rules into
`NEW_ENGINE_V1`. Output should be a small, evidence-backed blocker list (or a clean bill), not more
architecture.

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
| `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/OWNER-TRIAGE.md` (on archive branch) | **UNRESOLVED — RE-TRIAGE REQUIRED BEFORE DEFAULT-CUTOVER** | 4 must-fix / 24 consolidate items, not proven blocking or resolved either way |
| `.claude/experiments/production-migration-phase2-prep-2026-08-20/PHASE2-CAPTURE-DESIGN.md` (on archive branch) | **STILL OPEN, sample count UNKNOWN** | defines what the P2 passive-capture gate actually validates (legacy-side observation, not `NEW_ENGINE_V1` validation) |
| `.claude/experiments/sofa-method-reconciliation-2026-08-19/PRESERVATION-MANIFEST.md` (on archive branch) | **UNRATIFIED (G-009, explicit open decision)** | Sofa Method ratification evidence |
| `.claude/current-work.md` | **SUPERSEDED (self-marked)** | pre-2026-08-16 historical log |
| `.claude/master-roadmap-2026-08-13.md` | **HISTORICAL, frozen 2026-08-13** | CJ-2/B2 phase table, superseded by Sofa Method → `NEW_ENGINE_V1` lineage |
| `.claude/reader-lab-handoff/*` | **EVIDENCE-ONLY, pre-dates LC1** | RL-2026-001 ops-request/receipt/analysis trail |
| `PIPELINE.md` | **HISTORICAL (not rewritten this pass)** | describes a pipeline shape 5+ months out of date; needs a dedicated technical-documentation pass, not a reconciliation-pass rewrite |
| `docs/DISCOVERY.md` | **HISTORICAL (self-marked)** | describes a deleted script |
| `.claude/legacy-corpus-integrity-phase1-2026-08-16.md` + `.claude/audits/*.json` | **CURRENT** | original LC1 Phase 1 audit that the now-complete LC1 programme executed against |

---

*Update this file when current state changes. Do not let it grow into a diary — if a section is
about to become a narrative, it belongs in a linked document instead, with a pointer here.*
