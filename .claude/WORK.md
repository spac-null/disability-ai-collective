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

**Two different SHA facts, kept deliberately separate — do not collapse them:**

- **`CURRENT_MAIN` — not recorded in this file, by design.** No document can hold it durably. Get
  it with `git rev-parse origin/main`. Any SHA written here is a marker of when something was
  checked, never a claim about present HEAD.
- **`LAST_RUNTIME_CHANGING_BASELINE` = `ad4beccb18d79d0119293625af0867abec629b42`** (PR #41 merge,
  2026-08-27). The most recent commit on `main` that changed **runtime behaviour** — engine,
  prompts, Writer/Form, fact-check. This is the engine behaviour currently in production and the
  behaviour the next natural run validates. It stays correct as `origin/main` advances, and is
  only superseded when another runtime/code change lands.
- **`STATE_SYNC_SHA` = `ad4beccb18d79d0119293625af0867abec629b42`** — the `origin/main` HEAD this
  file was last synced against (same commit as the runtime baseline, because the sync immediately
  followed PR #41; the two are separate facts that merely coincide right now).

**Documentation-only commits do not move `LAST_RUNTIME_CHANGING_BASELINE`.** This file's own PR
(#42, docs-only) advances `origin/main` past `ad4becc` without altering runtime behaviour, so it
does not invalidate the natural-run validation below. Same for any other docs-only descendant.
Before trusting anything here as current, run `git rev-parse origin/main` and compare.

The earlier marker `RECONCILED_AGAINST_SHA` = `14997f07e23601f8fc7b920aed7ae15e2cb2e5cf` (PR #26
merge, 2026-08-25) is retained as history: it names the full project-state reconciliation pass, of
which the 2026-08-27 sync is a narrower documentation-only follow-up (engine state, PRs #39–#41,
current-phase pointer). Nothing outside those areas was re-verified on 2026-08-27.

This reconciliation was triggered by discovering a local checkout (`~/code/disability-collective-ai`,
HEAD `732c84f`) had diverged from `origin/main` at merge-base `9f9bf35` (2026-08-19/20) and
accumulated 38 unpushed commits — see `.claude/experiments/writer-grounding-production-migration-preservation-2026-08-25.md`
for full disposition. **Do not perform further canonical-tracker edits from that local checkout —
work from a worktree based on current `origin/main`.**

---

## PRODUCTION BASELINE

- **`LAST_RUNTIME_CHANGING_BASELINE`: `ad4beccb18d79d0119293625af0867abec629b42`** (PR #41 merge,
  2026-08-27) — the runtime behaviour the engine state below describes. This is **not** a claim
  about current `origin/main`, which moves independently (docs-only commits included); run
  `git rev-parse origin/main` for that.
- **`PR26_PRODUCTION_BASELINE`: `14997f07e23601f8fc7b920aed7ae15e2cb2e5cf`** — historical. Names
  the main-site IA/visual-redesign baseline (below), not the current HEAD.
- **PRs #28–#38 landed between those two baselines and are NOT individually recorded here or in
  `LOGBOOK.md` — a known documentation gap, not a claim about their content.** From branch names
  only (git truth, not audited in the 2026-08-27 sync): `#28` new-engine-v1 stage-failure
  containment; `#29` static-page content audit; `#30` legacy public hygiene; `#31` jascha link;
  `#32`/`#33` reissue pilots 1–2; `#34`–`#37` backlist reissue waves 1–4; `#38` selected-backlist
  IA. Anyone needing their detail must read the diffs — do not assume this list is complete or
  that these PRs left no state worth tracking.
- **PR #26 (main-site IA + visual-language redesign v2): COMPLETE and DEPLOYED.** GitHub Pages
  run `32879430779`, deployed SHA matches `origin/main`. Live-verified 2026-08-25: Home, Articles,
  About, Press, Articles search/count all PASS.
- Current publication counts: **143 total, 41 withdrawn, 102 readable** — live-verified
  2026-08-25 and re-confirmed against the tree at `ad4becc` on 2026-08-27 (`_posts/*.md` = 143,
  `withdrawn: true` = 41). The 2026-08-25 breakdown (3 Latest / 99 archive; collection counts
  4/9/4/3) was NOT re-verified after PRs #34–#38 touched backlist/IA — treat the totals as
  current and the breakdown as last-known.
- Do not reopen D1.x visual design unless a concrete production regression is found.

## COMPLETED

- **`NEW_ENGINE_V1` default cutover — COMPLETE.** PR #39, merge `b1f568c`, 2026-08-27.
  `NEW_ENGINE_V1` became the formal code default. Full state: ENGINE STATE table above. No
  cutover blocker remains; do not reopen cutover auditing.

- **Readability / title coherence / evidence-boundary tightening — COMPLETE.** PR #40, merge
  `423bb80`, 2026-08-27. **The "hard to read" problem is no longer an open engineering task.**
  What shipped, in `automation/new_engine_v1/stages.py` (ARTICLE FORM + WRITER prompts),
  `automation/title_coherence.py` (new), `automation/new_engine_production.py`:
  - *Reduced repetition:* the argument gets one clear statement; a paragraph earns its place only
    by adding evidence, a new implication, a necessary qualification, or a real step forward.
    Enforced at the Form stage too — a route that circles one insight has one movement, not
    several, and no movement may exist to preview or reprise the arrival.
  - *Concrete-first:* the article opens on the thing itself — object, project, person, what was
    made or done — before any movement interprets it. No framing device in front of the subject.
  - *Easier reading:* one idea moving at a time, no stacked abstraction, ordinary word over the
    specialist one, no sentence needing a reread before its main claim is clear, plain sentences
    across the evidence→meaning gap.
  - *Length:* `target_words` is the smallest range in which the argument completes — an upper
    bound, never a quota. Coming in under it is a good outcome.
  - *Title coherence:* the writer must now emit `TITLE: <headline>`, and a dependency-free,
    model-free check counts headline content words absent from the body. Origin: the real
    2026-08-27 run `production-20260827T070010Z-fd846f06`, where a writer emitted no headline, the
    candidate silently inherited the Dezeen roundup's, and an article about a tactile exhibition
    system sat under a headline about a mountain trike. This check **reports; it does not gate
    publication** and is not part of the publication-safety bridge.
  - *Evidence boundary:* a reading of how something works is not a finding about how the world
    works. A claim about a design may not widen into a general truth about cognition, perception,
    behaviour or institutions unless the source supports it or it is marked as a reading.
  - **Further readability work should be driven by actual reader feedback on new output, not
    speculative prompt tuning.** No open readability task exists to pick up.

- **Strict claim-extraction robustness — COMPLETE.** PR #41, merge `ad4becc`, 2026-08-27.
  `automation/orchestrator/fact_check.py`: strict extraction now distinguishes a **genuine zero
  claims** result (reaches the publication-safety bridge as `NO_VERIFIABLE_CLAIMS`) from an
  **empty, truncated, prose-only, malformed or ambiguous provider reply** (`EXTRACTION_ERROR`).
  Extraction runs at `temperature=0`. **Both statuses fail closed** — a failure is never returned
  as `[]`, so an extraction failure can no longer read as an absence of contradictions. **No
  taxonomy expansion was made**; the two states above are the whole change.

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

## ENGINE STATE — DEFAULT CUTOVER COMPLETE (2026-08-27)

Read this block first; the bullets under it are the supporting detail.

| Fact | State |
|---|---|
| `NEW_ENGINE_V1` default cutover | **COMPLETE** (2026-08-27, PR #39, `b1f568c`) |
| Default engine | **`NEW_ENGINE_V1`** — `automation/engine_switch.py`: `DEFAULT = NEW_ENGINE_V1`; unset `CRIPMINDS_ENGINE` selects it |
| Production cron | **unchanged — still explicitly `CRIPMINDS_ENGINE=new_engine_v1` on the 09:00 line, LIVE** |
| Scheduler migration/change | **NONE.** The cutover aligned the code default with the engine the scheduler had already been passing explicitly since 2026-08-24. Default and scheduler are separate controls and were deliberately not changed together |
| Explicit legacy rollback | **AVAILABLE** — set `CRIPMINDS_ENGINE=legacy` on the cron line. No data migration. Note: *unsetting* the variable no longer means legacy, so rollback is an explicit value, not a deletion |
| Unknown `CRIPMINDS_ENGINE` value | fails closed (raises, never guesses) |
| Post-start fallback | **NONE by design.** Once `new_engine_v1` begins a run it owns that run; a HOLD is a result, not a reason to re-run on legacy |
| Cutover blockers | **NONE.** Do not reopen cutover auditing |

*Provenance (2026-08-27 sync): the default-engine, rollback and fail-closed rows were verified
directly against `automation/engine_switch.py` at `ad4becc`. The **production cron** row was NOT
re-verified on Trident this pass — it is carried forward from the PR #39 cutover record. If it
matters to a decision, check the live crontab before relying on it.*

**Legacy is rollback debt, not current production work.** It remains available and untouched as the
rollback target. Its known unresolved prompt/rule items (see BLOCKED / OUTSTANDING) stay outstanding
and are **not** cutover blockers — they never blocked the completed default cutover.

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
- **Engine default is `NEW_ENGINE_V1` (formal cutover 2026-08-27).** `automation/engine_switch.py`:
  `DEFAULT = NEW_ENGINE_V1`; an unset `CRIPMINDS_ENGINE` env var now selects the new engine.
  Until 2026-08-27 the default was `LEGACY` and `new_engine_v1` was opt-in; the 09:00 scheduler had
  been passing it explicitly since 2026-08-24, so the cutover aligned the code default with the
  engine already running in production rather than migrating the scheduler. It waited on the
  2026-08-27 natural run (`production-20260827T070010Z-fd846f06`), which reached a legitimate
  ACCEPT, executed the strict publication-safety bridge, and failed closed on
  `world_relative_fact_check` (0 claims extracted) with `publication_eligible: false` and nothing
  published — the corrected form of the 2026-08-25 fail-open defect. Unknown values still fail
  closed (raise, never silently default). Still no post-start fallback — once `new_engine_v1`
  begins a run, it owns that run; a HOLD is a result, not a reason to re-run on legacy. Rollback =
  set `CRIPMINDS_ENGINE=legacy` on the cron line; the legacy engine is untouched and that value
  still dispatches to it, and no data migration is involved. Note the one rollback semantic the
  cutover changed: UNSETTING the variable no longer reverts to legacy, so rollback is now an
  explicit value rather than a deletion. The 09:00 cron keeps its explicit
  `CRIPMINDS_ENGINE=new_engine_v1` override — the formal default and the scheduler are separate
  controls and were deliberately not changed together.
- **"Implemented / live-capable" and "default production engine" remain different facts in
  general — but for `NEW_ENGINE_V1` they now coincide.** It is both, as of 2026-08-27. Keep the
  distinction in mind for any *future* engine or stage, not as a live caveat about this one.

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
  `CONSOLIDATE_BEFORE_PRODUCTION` items — UNRESOLVED, and RECLASSIFIED 2026-08-27 as LEGACY
  ROLLBACK DEBT, NOT A CUTOVER BLOCKER.** These items belong to the legacy engine, which is now
  the rollback target rather than the production default. They did **not** block the completed
  default cutover and must not be re-cited as if they did. They also remain genuinely unresolved —
  **do not mark them resolved, obsolete, or satisfied.** Their practical weight is now: if a
  rollback to `CRIPMINDS_ENGINE=legacy` ever happens, this is known debt on the engine being
  rolled back to. The only proven facts: this inventory
  (`.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/OWNER-TRIAGE.md`) exists on
  `archive/writer-grounding-production-migration-2026-08-20`; the `MUST_FIX`/`CONSOLIDATE` labels
  were assigned against the historical (pre-`NEW_ENGINE_V1`) architecture; `NEW_ENGINE_V1`'s code
  contains no direct reference to these 28 entries. That is **not sufficient to conclude they
  currently block anything** — absence of a reference is not evidence of resolution, obsolescence,
  or continued relevance. A future re-triage phase should sort each item into: (A) a still-required
  invariant absent from `NEW_ENGINE_V1`, (B) an equivalent invariant already implemented
  differently, (C) obsolete because the new architecture removed the failure mode, (D)
  documentation/consolidation only, or (E) genuinely blocking. Do not port legacy rules into
  `NEW_ENGINE_V1` and do not treat this list as either satisfied or blocking until that triage
  runs. That triage is no longer gated on anything and is no longer urgent — it is not the
  current phase and should not be started as a side effect of reading this entry.
- **Phase-2 passive-capture requirement — STILL OPEN, current sample count UNKNOWN; NOT a cutover
  blocker (clarified 2026-08-27).** It observes the **legacy** pipeline so a later comparison has
  frozen evidence; the default cutover completed without it and did not depend on it. Still open,
  still not satisfied — do not mark it resolved. Re-examined
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

## IN REVIEW — NOT MERGED

- **PR #43 — readability / popular-nonfiction writing contract: MERGED** 2026-08-28,
  merge `16068cc`. `PROSE_DOCTRINE`, `FORM_SYSTEM` and one line of `build_writer_input`
  only; no research, network, source-selection, fact-check, bridge, cron or publishing
  change. What it fixed and what it explicitly could not fix without better input is in
  its own PR body.
- **PR #44 — RESEARCH PACK: OPEN, NOT MERGED.** Adds a bounded pre-writing research
  stage between the anchor snapshot and Discovery, so an article is written from
  material rather than from one fact read five ways.
  - New artifact `RESEARCH_PACK` (`automation/new_engine_v1/research.py`), additive in
    `contracts.py` — **`SCHEMA_VERSION` deliberately unchanged** and the stage is
    OPTIONAL in `REQUIRED_STAGES`, so the eight frozen stages keep their payloads and
    hashes and a pre-existing shadow run still validates.
  - Pipeline: `SOURCE_SNAPSHOT → RESEARCH_PACK → sufficiency → DISCOVERY → ARTICLE_FORM
    → WRITER_INPUT → WRITER_OUTPUT → GROUNDING (over the pack) → fact check → bridge`.
  - Bounds: 4 queries, 12 candidate URLs, 5 fetched sources, 12k chars/source, 40k pack
    budget, 20s per fetch, no retry loop.
  - A search result is not a source: material enters only from bytes fetched, hashed and
    persisted, and every excerpt must be a verbatim span of the text the pack carries —
    enforced in `contracts.validate`, not by convention.
  - Sufficiency: `ARTICLE` / `SHORT_ARTICLE` / `NARROW` / `HOLD_INSUFFICIENT_RESEARCH`,
    model-free, judged on roles and independence rather than a URL count.
  - Bridge gains one narrow blocking check, `research_pack_provenance`. No existing
    check was weakened; the strict fact check and claim taxonomy are untouched.
  - Evidence: two isolated NON-LIVE regressions (`automation/research_pack_test.py` for
    the contract; run records under `/tmp/research-regress-out/` on Trident).
    The 28 August Ljubljana anchor reaches **HOLD_INSUFFICIENT_RESEARCH**; a richer
    single-subject anchor (Guardian on Minnie Evans) reaches **ARTICLE** with a PRIMARY
    museum source and two independent ones. Neither run wrote an article.
  - Second increment (2026-08-28, same PR): `TERTIARY` role — carries verified material,
    buys no independence, substitutes for no first-party source; independence counted per
    publisher as well as per duplicate cluster; `subject_span` binds Discovery to the
    subject the pack was built for, so a roundup cannot be researched for one item and
    written about another (`DISCOVERY_SUBJECT_OUTSIDE_RESEARCHED_SCOPE`, HOLD, one pass).
  - Live end-to-end (isolated `/tmp`, nothing in `_drafts/`): pack `ARTICLE` — 5 fetched
    sources, 3 independent publishers, 755 verified subject words, scope verified,
    624-word article, grounding settled — then **HOLD on the pre-existing V0 policy**
    (2 unadjudicated `TRUE_UNCERTAIN` findings). `decision.py` untouched. **Open
    question for deployment: a richer pack produces more checkable specifics, so V0's
    HOLD-on-any-uncertain rule may fire more often than it did on single-source runs.**
  - **Not production-ready on unit tests alone. Not merged, not deployed.**

- **FOLLOW-UP — GROUNDER STABILITY. Read-only investigation required, after the Research
  Pack merges, before any repair layer is built on grounder output.** Observed twice
  during PR #44's live runs: (a) materially identical supported text changed
  classification between grounding passes (`LEGITIMATE_INTERPRETATION` → `TRUE_UNSUPPORTED`,
  same sentence, same source); (b) run `production-20260828T185627Z` returned three
  `TRUE_UNSUPPORTED` findings whose own `why` text says the claim IS grounded in the
  anchor. Distinct from a genuine source conflict, which the same run also produced and
  which is correct behaviour: the anchor says "nearly 100 pieces", the High Museum source
  says "more than 100". Not investigated, not fixed, no grounder prompt or policy touched.

- **FOLLOW-UP — UNCERTAINTY ADJUDICATION. Implementation preserved at
  `backup/uncertainty-adjudication-2026-08-28` (`d91d34adf31b4c6c8db3f3b95575fdf4f8dbaf12`).
  NOT part of PR #44, NOT approved for merge, decision deferred until the grounder-stability
  investigation has run.** It consumes grounder classifications, so it must not be built on
  top of classifications whose consistency is unproven. `decision.py`'s dormant
  `uncertain_adjudicated` flag remains dormant and untouched.
- **28 August candidate — HELD.** `_drafts/_archive/2026-08-28-the-order-in-which-you-meet-a-picture.md`,
  outside `publish_best.py`'s top-level `_drafts/*.md` glob, byte-identical, evidence
  directory intact. Owner read it and did not approve it for publication.

## CURRENT PHASE

**`POST-CUTOVER NATURAL-RUN VALIDATION`**

**CURRENT ACTION:** Observe the next natural scheduled `NEW_ENGINE_V1` production run (the 09:00
CEST cron) from the then-current `origin/main`. Classify the actual outcome before making further
engine changes.

For engine-behaviour comparison the run is validating `LAST_RUNTIME_CHANGING_BASELINE` =
`ad4becc` (PR #41) — **unless another runtime/code change lands on `main` before the run**, in
which case that becomes the baseline and this pointer needs updating. The run does not have to
execute at that exact SHA, and it will not: documentation-only commits after `ad4becc` (this
sync's own PR #42 among them) advance `origin/main` without changing runtime behaviour, so the
comparison still holds. Check `git log ad4becc..origin/main` for runtime-touching commits before
assuming the baseline is unchanged.

**No manual LIVE run is requested, and a manual run must not be used to replace the natural run.**
The first natural scheduled run after the combined PR #39/#40/#41 changes is the validation point;
a hand-triggered execution is not that evidence.

Once the run has happened, follow only the branch that actually occurred:

1. **A candidate is produced** — review the resulting article **as a reader first**, before
   reading any log. Specifically assess whether the earlier "hard to read" problem is *materially*
   improved: does it open on the concrete thing, does it say its point once, can each paragraph be
   named for what it adds. Only then look at the run artifacts.
2. **HOLD** — inspect only the concrete HOLD reason. Do not re-audit the pipeline around it.
3. **`EXTRACTION_ERROR`** — inspect the concrete provider/extractor evidence for that run. This is
   now a distinct, fail-closed state (PR #41) and is real information, not a mystery.
4. **Another failure** — investigate only that path.

Explicitly NOT this phase: new engine architecture, calibration, WG-7, cutover re-auditing,
porting legacy rules into `NEW_ENGINE_V1`, speculative readability tuning, or the legacy
prompt-rule re-triage.

### FOLLOW-UP AFTER THE NATURAL RUN — historical "BIC pen" issue

Not started, and **deliberately not investigated during the 2026-08-27 documentation sync.** Do not
start it before the natural-run validation above is classified.

Task: locate the original finding and classify it as **FIXED BY CURRENT CONTRACT / STILL POSSIBLE /
OBSOLETE**.

Where to start looking (located, not analysed, in the 2026-08-27 sync):
- `.claude/experiments/why-we-write-2026-08-10.md` — records that `llm.py`'s `PUBLICATION LENS` /
  `INTELLECTUAL FORMATION` founder-biography blocks (Van Abbemuseum / Exploded City / **bic pen** /
  Tussenruimte) were deleted and replaced by the short WHY WE WRITE doctrine in isolated commit
  `01339ce` (2026-08-10). This is the nearest thing to an origin record found.
- `editorial-lens.md` (repo root) — still carries the "He draws in Bic pen" text. `git grep` found
  **no automation reference to it**, which is a lead, not a conclusion.
- `automation/compare_models.py:122` and `automation/probe_out/**` — historical prompt copies that
  still embed the lens text; these are fixtures/probe records, not live prompts.
- The failure family to check it against is the one LC1 closed on the corpus:
  personas presenting authored/absorbed biographical material as lived first-person testimony
  (see COMPLETED → persona "Wound" clusters, and
  `.claude/legacy-corpus-integrity-phase1-2026-08-16.md`).

The open question is whether `NEW_ENGINE_V1`'s current prompt contract structurally prevents
owner-biography leakage into persona voice, or merely no longer feeds it in one path.

## DOCUMENT INDEX

| Document | Status | What it's for |
|---|---|---|
| `.claude/WORK.md` | **CURRENT** | this file |
| `.claude/LOGBOOK.md` | **CURRENT** | chronological history, compact entries |
| `.claude/PROJECT-MAP.md` | **CURRENT** | repository/worktree/branch topology |
| `automation/engine_switch.py` | **CURRENT (code, authoritative)** | the one engine-selection boundary — the real answer to "which engine is default" and how rollback works; its module docstring is kept in sync with the ENGINE STATE table above |
| `.claude/project-manifest.json` | **CURRENT (machine-generated)** | same, machine-readable |
| `.claude/archive/WORK-2026-08-17-superseded.md` | **HISTORICAL** | full pre-fork state: doctrine, conceptual architecture, safety-gate mechanics (AP1/APE2/PS1/LPF1), persona-architecture Phase 3 backlog — not reverified 2026-08-25, not contradicted either |
| `.claude/experiments/writer-grounding-production-migration-preservation-2026-08-25.md` | **CURRENT (disposition record)** | writer-grounding/production-migration archive-branch disposition |
| `archive/writer-grounding-production-migration-2026-08-20` (git branch) | **HISTORICAL, preserved** | 38-commit writer-grounding/production-migration/Sofa evidence line, owner-stopped, not production code |
| `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/OWNER-TRIAGE.md` (on archive branch) | **UNRESOLVED — LEGACY ROLLBACK DEBT, NOT A CUTOVER BLOCKER** | 4 must-fix / 24 consolidate items, still unresolved; reclassified 2026-08-27 — the default cutover completed without them and they must not be re-cited as blocking it |
| `.claude/experiments/production-migration-phase2-prep-2026-08-20/PHASE2-CAPTURE-DESIGN.md` (on archive branch) | **STILL OPEN, sample count UNKNOWN — not a cutover blocker** | defines what the P2 passive-capture gate actually validates (legacy-side observation, not `NEW_ENGINE_V1` validation) |
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
