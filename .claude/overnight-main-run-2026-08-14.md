# Overnight Main Run — 2026-08-14

Start: 2026-08-14 04:01 CEST
Starting HEAD: 204c3bc (Live pipeline rule/review integrity: invisible rules, review truncation, repetition shadow)
On top of: 128fda8 (Add CJ-2 winner bridge + OFF-by-default shadow integration hook, Phase G.2)
origin/main: d014c19 (Reader Lab admin: cleanup patch)
Ahead by: 2 commits, confirmed unchanged, verified against expected state in the run instructions.

Dirty state at start (pre-existing, not touched by this run unless noted):
- Modified: .claude/current-work.md
- Untracked (research docs / probe fixtures per repo convention): .claude/experiments/*, .claude/master-roadmap-2026-08-13.md,
  .claude/original-blueprint-A-M-reconciliation-2026-08-13.md, .claude/reader-lab-handoff/*, automation/.probe_fixtures/*,
  automation/cj1_v3_*.py, automation/cj2_*.py, calibration/candidates/RL-2026-00{2,3}-*.json,
  calibration/research-context/RL-2026-00{2,3}.json, reader-lab/rounds/drafts/RL-2026-00{2,3}.json

RL-002 status: ACTIVE / UNKNOWN — no safe local metadata path available (would require querying the deployed remote
Cloudflare D1 via wrangler; local .wrangler/state is dev/miniflare state, not authoritative for live rounds). Not
pursued, per instruction not to let RL-002 block other packages. Will re-check at later package boundaries only if a
safe path appears.

## Package queue (priority order per instruction section 29)
1. Package A — `_should_block` gate_llm degradation policy
2. Package B — L2 active human-testimony retrieval
3. Package C — E essay-length adherence
4. Package D — G repetition-shadow offline evidence harvest
5. Package E — J STOP-risk observability
6. Package F — Article-level pilot protocol (Phase H design)
7. Package G — Combined release-candidate audit

## Key grounding found (existing repo docs, not re-derived from scratch)
`.claude/original-blueprint-A-M-reconciliation-2026-08-13.md` already documents the exact open questions this run
is tasked with resolving (sections A-M, esp. E, G, J, L, M) — this run treats that document as authoritative prior
audit evidence rather than re-auditing from zero.

---

## PACKAGE A — `_should_block` gate_llm degradation policy
STATUS: DONE
DECISION: A1 — lone `gate_llm` degradation now blocks. Grounded in existing repo
  evidence: `.claude/original-blueprint-A-M-reconciliation-2026-08-13.md` `## M`
  already documented this as an open gap (`_should_block == ["gate_llm"]` alone
  did not block); gate.py's own log lines already treat gate_llm's failure/
  truncation/missing-rule cases as "mechanical rule violations are UNKNOWN, not
  zero" — the same authoritative-safety-net-loss reasoning fable_brief already
  gets. CJ-2/shadow failures never reach `_degraded_stages` at all (confirmed by
  grep + a structural test), so this policy only ever sees authoritative stages.
FILES CHANGED:
  - automation/orchestrator/generate.py — extracted `_should_block` computation
    into `GenerateMixin._compute_should_block(degraded_stages)` (staticmethod),
    added `"gate_llm" in stages` to the lone-blocking set, updated the inline
    policy comment.
  - automation/should_block_policy_test.py (new) — 12 checks: empty/fable_brief-
    alone/gate_llm-alone/other-single-stage/unknown-stage/2+-combinations/
    duplicate-stage dedup/order-independence/structural shadow-non-reachability.
TESTS: should_block_policy_test.py 12/12 PASS. Re-ran neighboring suites for
  regression: gate_rule_completeness_test.py, gate_pre_commit_integration_test.py,
  review_wholeness_test.py, repetition_shadow_test.py, cj2_winner_bridge_test.py,
  cj2_shadow_integration_test.py — all PASS. snapshot_test.py --check: no drift,
  6/6 articles match (confirms this change didn't touch any snapshotted LLM-call
  construction, as expected since it's pure post-hoc policy logic).
DECISION: implemented, not deferred — repo evidence was sufficient (A1).
OPEN QUESTIONS: none remaining for this package.
COMMIT: 7f03ec3
NEXT PACKAGE: C (E — essay-length adherence), then B (L2), then D/E/F/G.
  (Reordered C before B: gate.py already has the exact extension point
  `_check_article_type_compliance` for E, making it well-scoped and fast;
  L2 needs a longer discovery.py audit first. Priority list in section 29
  of the run instructions is unaffected — both remain ahead of D/E/F/G.)

---

## PACKAGE C — E essay-length adherence
STATUS: DONE (shadow-only, per instructions — no threshold ever chosen before this,
  so blocking authority was never justified; observation only)
CONTRACT:
  - field_note / portrait / series_part: absolute contract mirroring gate.py's real
    enforcement exactly (≤500 / ≥1200) — IN_RANGE or HARD_DEVIATION, no soft tier,
    cross-checked structurally to never disagree with the real hard-enforcement.
  - essay / pleasure / fury / confusion / indefensible: relative to the per-run
    `target_words` drawn from config.py's _LENGTHS (no fixed range exists for these —
    continuous 450-2800 weighted-random draw). IN_RANGE 0.7-1.3x, SOFT_DEVIATION
    0.5-0.7x/1.3-1.6x, HARD_DEVIATION outside that. First uncalibrated guess, same
    discipline as G's similarity_threshold.
  - UNKNOWN_FORMAT: unrecognized/missing article_type, or missing target_words for a
    relative-path type.
FILES CHANGED:
  - automation/orchestrator/review.py — new `ReviewMixin._check_length_adherence_shadow`
    classmethod; `validate_article` gained `article_type=None` kwarg, computes word_count,
    calls the new check; `_persist_review_signals` gained `shadow_length_adherence` param
    + migration-safe column; sidecar rendering updated.
  - automation/orchestrator/generate.py — call site now passes `article_type=article_type`.
  - automation/length_adherence_shadow_test.py (new) — 34 checks.
TESTS: 34/34 PASS. snapshot_test.py --check: no drift, 6/6 match. Neighboring suites
  (gate_rule_completeness, gate_pre_commit_integration, review_wholeness,
  repetition_shadow, should_block_policy) all re-ran clean.
DECISION: SHADOW/OBSERVABILITY per instruction — no promotion before 2026-08-28,
  same convention as G's repetition shadow check.
OPEN QUESTIONS: none for the shadow scaffold itself; real observation data will decide
  whether 0.7-1.3/0.5-1.6 bands are the right cutoffs, exactly what this window exists
  to inform.
COMMIT: d9f9827
NEXT PACKAGE: D (G offline evidence harvest — read-only, no code changes expected).

---

## PACKAGE D — G repetition-shadow offline evidence harvest
STATUS: DONE
METHOD: ran the existing (unmodified) `_check_repetition_shadow` across all 140
  committed published articles in `_posts/` — safe local corpus, zero network.
  Script: automation/repetition_shadow_corpus_harvest.py.
FINDINGS (full detail: .claude/repetition-shadow-corpus-harvest-2026-08-14.md):
  1. 60% of all 50 candidate pairs (30) are figure-block-vs-figure-block false
     positives — image captions in the same article share title/slug words +
     boilerplate attrs. Candidate preprocessing fix recorded, NOT implemented
     (detector mechanics frozen during the observation window).
  2. `_posts/2026-03-31-the-floor-plan-of-disappearance.md` appears to have its
     content duplicated within the same published file (8 near-identical
     paragraph pairs, sim 0.91-1.00, consistent ~14-15 paragraph offset). REAL
     content-integrity bug, unrelated to G's calibration question. NOT fixed —
     flagged for human/editorial review, editing published content is not this
     run's call to make unilaterally.
  3. After removing 1+2, only 7 genuinely calibration-relevant prose pairs
     remain (0.35-0.85 similarity) — too small a sample to validate/reject
     similarity_threshold=0.35 from this pass alone.
DECISION: no threshold change, no promotion, no detector-code change (all
  correctly out of scope per instructions). Evidence recorded for the
  2026-08-28 promotion decision.
COMMIT: c15151b
OPEN QUESTIONS (for a human, not this run): (a) should the floor-plan-of-
  disappearance duplication be fixed via republish/edit — needs editorial
  judgment; (b) should the figure-block preprocessing fix be applied before or
  independent of the 2026-08-28 promotion decision.
NEXT PACKAGE: B (L2 active human-testimony retrieval) — longest remaining
  package, needs a discovery.py/evidence_packet audit before any design work.

---

## PACKAGE B — L2 active human-testimony retrieval scaffold
STATUS: DONE (SHADOW scaffold implemented; live search deliberately deferred as design)
AUDIT: discovery.py fetches exactly one already-identified URL (fetch_source_article/
  get_source_text), zero companion-source search anywhere. grounding.py's
  build_evidence_packet is a single-source identity payload (source_text/source_hash/
  evidence_packet_hash) with no multi-source concept. No search integration exists
  anywhere in the codebase except fact_check.py's _web_verify_quote/_web_verify_claim
  (Perplexity Sonar via OpenRouter) — narrow verification queries, not open search.
IMPLEMENTED: automation/orchestrator/testimony_l2.py — mirrors cj2_shadow.py's exact
  OFF/SHADOW/env-var/fixture-only/never-raises discipline.
  - `_testimony_needed_heuristic`: deterministic, zero-network — attributed
    first-person quote present -> not needed; else needed.
  - `_check_companion_eligibility`: missing fields / unverifiable attribution
    (no named person) / too short / duplicate-of-primary (hash or substring) ->
    reject; else eligible.
  - `TestimonyL2Mixin._l2_testimony_attempt`: OFF (default) = zero mutation, zero
    DB file created. SHADOW = heuristic + fixture-bridge (L2_COMPANION_FIXTURE env
    var, same "fixture only, no live orchestration" precedent as CJ-2's winner
    input), attaches `evidence_packet["companion_source"]` as a SEPARATE key —
    source_text/source_hash/evidence_packet_hash (primary factual authority) never
    touched. Persisted to new engagement.db table `l2_testimony_runs`.
  - Wired into generate.py right after evidence_packet is built, mutating in place
    (not returning a new object) to preserve the "exactly one evidence_packet
    object threaded by reference" invariant from the Pixel-validation incident.
  - Registered in production_orchestrator.py's mixin list.
NOT IMPLEMENTED (by design, per instructions — genuine semantic/ranking question):
  live companion-source SEARCH. Full design + open questions (cost/latency budget,
  multi-result ranking, source-type trust, heuristic false-negative rate, doctrine
  fit with item K) in .claude/l2-testimony-design-2026-08-14.md. Recommended next
  step: an offline Sonar-only experiment against ~10-20 published articles' real
  source URLs before any live wiring.
TESTS: 30/30 PASS (automation/testimony_l2_test.py) — covers every scenario
  instruction 9 named. snapshot_test.py: no drift. All neighboring shadow-check
  suites re-ran clean.
COMMIT: 168c047
OPEN QUESTIONS: the live-search questions listed in the design doc; none block
  the shadow scaffold itself, which is real and tested today.
NEXT PACKAGE: E (J STOP-risk observability design).

---

## PACKAGE E — J STOP-risk observability
STATUS: DONE (implemented, not just designed — avoided a redundant model call)
AUDIT: confirmed zero grep hits anywhere for stop_risk/drop-off/attrition before
  this pass (matches reconciliation doc exactly). _engagement_read already asks a
  holistic "would a reader keep going" question in one Sonnet call/article — the
  sufficient existing signal per instruction 15's own guidance to avoid a
  redundant call.
IMPLEMENTED: STOP_RISK: 1-5 added as a 4th field to _engagement_read's existing
  prompt (VERDICT/HOOK/DRAG/STOP_RISK), with explicit calibration language scoring
  the REASON (delayed payoff / unclear purpose / repetitive middle / excessive
  abstraction / unresolved cognitive burden) rather than difficulty/form/length —
  a deliberately hard or slow essay that earns it scores low risk. max_tokens
  300->400. New `ReviewMixin._extract_stop_risk_shadow` deterministically parses
  the line from the response already obtained — zero extra network cost. Persisted
  to 2 new engagement.db columns, rendered in review sidecar.
SAFETY: never touches is_clean/_should_block/publication — structurally guarded
  by a test asserting _compute_should_block's source never mentions stop_risk.
  No promotion date set (no proposed blocking use exists to promote toward,
  unlike G/E).
TESTS: 20/20 PASS (stop_risk_shadow_test.py). Snapshot fixtures re-recorded
  (deliberate prompt change — confirmed the diff was exactly the new STOP_RISK
  line before running --record). Full neighboring suite re-ran clean.
COMMIT: 20a5c52
OPEN QUESTIONS: none for the shadow instrument itself; whether/how to ever use
  this signal is a future editorial decision, not a code question.
NEXT PACKAGE: F (article-level pilot protocol preregistration — design/doc only,
  no code, no CJ-2 model runs).

---

## PACKAGE F — Phase H article-level pilot protocol
STATUS: DONE (preregistration only, as instructed — no CJ-2 runs, no
  CJ2_WINNER_DRAFT mode built)
GROUNDING: master-roadmap-2026-08-13.md `## 13` already names this exactly as
  Phase H, gated on Phase G (done, 128fda8). Built the protocol against real
  existing code (cj2_winner_bridge's claimed_contribution/engine_move fields,
  cj2_shadow.py's already-named-but-unreachable PATH_CJ2_WINNER_DRAFT constant)
  rather than inventing new terminology.
CONTENT: paired LEGACY_ARTICLE vs CJ2_WINNER_SOURCED_ARTICLE contract (same
  evidence_packet/source snapshot/run context; mismatched-hash pairs void by
  construction); dimensions split DETERMINISTIC (reuses existing gate.py/E/G
  checks + one new not-yet-built internal-labels-absent scan) / MODEL-JUDGE
  (winning insight preserved, disability-lens-reveals-mechanism per item K,
  factual grounding via existing validate_evidence_field, category jump,
  progression/repetition folding in reconciliation item D, correction
  integrity, public-language quality) / HUMAN CALIBRATION; stop rule using
  structural gates + paired comparison, INCONCLUSIVE as an explicit third
  outcome rather than forcing a premature yes/no.
COMMIT: 5257ee1
NOT DONE (by design): CJ2_WINNER_DRAFT mode, the internal-labels-absent
  deterministic check, any actual pilot run.
NEXT PACKAGE: G (combined release-candidate audit — final package).

---

## PACKAGE G — combined release-candidate audit
STATUS: DONE
SCOPE: origin/main (d014c19) .. HEAD (5257ee1) = 8 commits, 23 files changed,
  +3810/-35, comprising the 2 pre-existing local commits (128fda8, 204c3bc) plus
  tonight's 6 (7f03ec3, d9f9827, c15151b, 168c047, 20a5c52, 5257ee1).
FINDINGS:
  - Compile: `python3 -m py_compile` clean across every file in automation/ and
    automation/orchestrator/.
  - Instantiation: ProductionOrchestrator (now 12 mixins incl. TestimonyL2Mixin)
    instantiates with no MRO conflicts; every new method
    (_l2_testimony_attempt/_cj2_shadow_attempt/_compute_should_block/
    _check_length_adherence_shadow/_extract_stop_risk_shadow) present and
    reachable on the real class, not just the mixin in isolation.
  - Full test battery: ALL 16 test files in automation/*_test.py pass, exit 0,
    including 5 files never run earlier tonight (cj2_b2_d0_h08_structural_test,
    executor_guard_test, grounding_test, lineage_persistence_test,
    writer_prompt_test) — zero regressions from tonight's work in any of them.
  - snapshot_test.py --check: no drift (fixtures re-recorded once tonight, for
    the deliberate STOP_RISK prompt change, then re-verified clean).
  - Schema/migration: every new engagement.db table (l2_testimony_runs) and
    column (shadow_length_adherence, shadow_stop_risk_score/reason) uses the
    same CREATE TABLE IF NOT EXISTS + ALTER TABLE ADD COLUMN + catch
    OperationalError pattern already proven across prior deploys — no
    migration script needed, idempotent, zero data-loss risk. Local
    automation/engagement.db is a 0-byte gitignored dev artifact, not the real
    production DB (which lives on the deployed host) — migrations apply on
    first real run there, not touched tonight.
  - New environment variables, all optional/default-safe (unset = today's exact
    behavior): L2_TESTIMONY_MODE, L2_COMPANION_FIXTURE (new tonight),
    CJ2_INTEGRATION_MODE, CJ2_SHADOW_WINNER_FIXTURE (pre-existing from 128fda8,
    also still unset/OFF in production).
  - THE ONE NON-ADDITIVE PRODUCTION BEHAVIOR CHANGE: Package A's gate_llm fix
    (7f03ec3) is NOT env-gated — it changes real blocking behavior starting
    from whenever this is deployed: a lone gate_llm degradation (LLM rule-check
    exception/truncation/missing-verdict) will now stamp
    `fact_check_status: blocked` instead of shipping unblocked. This is the
    deliberate point of the fix (A-M reconciliation `## M`), not an accident,
    but it is the one item in this release candidate that changes default
    daily-run behavior rather than adding a new inert-by-default signal —
    flagged explicitly rather than left implicit.
  - Cron/daily-run impact: confirmed via automation/README.md that the live
    cron on trident invokes a separately-deployed Hermes workspace copy
    (`/srv/data/hermes/workspace/...`), NOT this git checkout directly — none
    of tonight's local commits affect any real run until deployed (pushed +
    synced), independent of this run's own no-push/no-deploy rule.
  - Backward compatibility: validate_article's new `article_type=None` kwarg
    and generate.py's new call-site arg are both additive with safe defaults;
    every existing caller (snapshot_test.py, which passes neither
    target_words nor article_type) still works unchanged.
DECISION: release candidate is clean. No blocking issues found. Not pushed,
  not deployed, per instructions.
COMMIT RANGE: 128fda8..5257ee1 (origin/main still at d014c19)
NEXT PACKAGE: none — all 7 packages complete. See morning report below.

---

## FINAL RL-002 CHECK (package boundary, per instruction section 24)
Re-checked before writing the morning report: no new RL-002 handoff artifact
exists (`.claude/reader-lab-handoff/` still only has RL-2026-001 files). RL-002
= ACTIVE / UNKNOWN, unchanged from session start. No safe metadata path
appeared. Conditional completion branch (section 23) correctly skipped, no
penalty, per section 24.

---

# MORNING REPORT — 2026-08-14 overnight run

**STARTING STATE**
- HEAD 204c3bc, on top of 128fda8, origin/main at d014c19 (2 commits ahead,
  confirmed unchanged) — verified exactly as the run instructions described.
- Pre-existing dirty state (research docs, probe fixtures) left untouched
  throughout, per instructions.

**PACKAGE A — GATE DEGRADATION**
Decision: A1, lone `gate_llm` degradation now blocks. Grounded directly in
`.claude/original-blueprint-A-M-reconciliation-2026-08-13.md`'s own flagged
open question (`## M`) rather than re-derived from scratch. Extracted into
testable `GenerateMixin._compute_should_block`. 12 tests, commit `7f03ec3`.

**PACKAGE B — L2**
Architecture: mirrors `cj2_shadow.py`'s OFF/SHADOW/fixture-only discipline
exactly. Deterministic testimony-needed heuristic + companion-eligibility
checks + `evidence_packet["companion_source"]` slot with provenance kept
separate from primary factual authority, implemented and wired (OFF by
default). Live companion-source SEARCH deliberately left as a design doc
(`.claude/l2-testimony-design-2026-08-14.md`) — a real ranking/cost/trust
design question, not a wiring task. 30 tests, commit `168c047`.

**PACKAGE C — E**
Contract: absolute (field_note/portrait/series_part, mirrors gate.py's real
enforcement) vs. relative-to-target_words (every other type). SHADOW only, no
promotion before 2026-08-28. 34 tests, commit `d9f9827`.

**PACKAGE D — G**
Offline corpus evidence: ran the existing detector across all 140 published
articles. Two real findings — 60% of all candidates are a mechanical
figure-block false-positive artifact (candidate fix recorded, not applied),
and `_posts/2026-03-31-the-floor-plan-of-disappearance.md` appears to have its
content genuinely duplicated within the same published file (flagged for
human/editorial review, not fixed). No threshold change. Commit `c15151b`.

**PACKAGE E — J**
Status: implemented, not just designed — avoided a redundant model call by
adding STOP_RISK as a 4th field to the existing `_engagement_read` call.
Explicit calibration language scores the reason (delayed payoff/unclear
purpose/repetitive middle/excessive abstraction/unresolved cognitive burden),
not difficulty or form. 20 tests, commit `20a5c52`.

**PACKAGE F — ARTICLE PILOT**
Preregistered Phase H (master roadmap already named it, gated on Phase G
which is done) — paired-artifact contract, three-tier dimensions
(deterministic/model-judge/human), stop rule with an explicit INCONCLUSIVE
outcome rather than a forced yes/no. Zero CJ-2 runs. Commit `5257ee1`.

**RL-002**
Remained ACTIVE/UNKNOWN throughout — no safe local metadata path existed in
this environment (would require querying the deployed remote D1). Checked at
start and again at the final package boundary; never blocked any other
package, per instructions.

**RELEASE CANDIDATE**
`origin/main..HEAD` = 8 commits (2 pre-existing + 6 tonight), +3810/-35 across
23 files. Full local test battery (16 files) passes clean, including 5 files
never exercised earlier in the session. snapshot_test.py: no drift (fixtures
deliberately re-recorded once, for the STOP_RISK prompt change, then
re-verified). Only one non-additive production-behavior change in the whole
candidate: Package A's gate_llm fix, which is the deliberate point of that
fix, not an oversight — flagged explicitly in Package G's findings above.
Confirmed via automation/README.md that the live cron runs from a separately-
deployed workspace, not this checkout, so none of tonight's local commits
affect production regardless of push status.

**UNRESOLVED (genuine, for a human)**
- Whether/how to fix `2026-03-31-the-floor-plan-of-disappearance.md`'s
  apparent content duplication (Package D finding 2) — editorial call, not a
  code question.
- Whether to apply the figure-block preprocessing fix to the repetition
  shadow check before or independent of its own 2026-08-28 promotion decision
  (Package D finding 1).
- L2's live-search design open questions (cost/latency, ranking, source
  trust) — listed in `.claude/l2-testimony-design-2026-08-14.md`, not blocking
  the shadow scaffold itself.
- RL-002's eventual completion and its Shape-B calibration branch — untouched,
  as instructed.

**NEXT MORNING ACTION**
- Highest-value next step: human review of the two Package D findings (both
  are real discoveries about live published content/detector accuracy, not
  code to write).
- Requires privileged deployment: nothing yet — this is a release candidate,
  not deployed. Pushing `origin/main..HEAD` and deciding whether/when to flip
  any of the new env-gated modes (L2_TESTIMONY_MODE, CJ2_INTEGRATION_MODE) to
  SHADOW in the real deployed workspace is a separate, deliberate decision.
- Can continue autonomously: Package B's live-search experiment (the small
  offline Sonar-only pilot suggested in the L2 design doc), or drafting the
  internal-labels-absent deterministic check Package F's protocol names as
  the one missing piece of Phase H's tooling.

**CONFIRMED**
- No push. No deploy. No partial Reader Lab inspection. No B2 semantic
  revision (none attempted or needed — out of scope for this run's queue).

