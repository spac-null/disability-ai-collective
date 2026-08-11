# Current Work Checkpoint

Update this after every meaningful commit, not at the end of a session. A
fresh session should need this file, not conversation archaeology. Full
methodology/results for closed experiments live in `.claude/experiments/`
and are linked below, not duplicated here.

## GOAL
Article-quality repair blueprint — rebuild cripminds' article-generation
prompt system around its true purpose (see project memory
`project_cripminds_editorial_blueprint.md` / `project_cripminds_true_purpose.md`),
not as ten isolated style fixes.

## ROADMAP / ACTIVE PHASE
Order changed 2026-08-10 evening after the Phase 1.5B planning-brief audit
below promoted grounding ahead of Phase 2 — do not reorder again without a
stated reason.

- **DONE** — Phase 0 (reliability + canonical baseline).
- **DONE** — Phase 1, WHY WE WRITE → **KEEP**, scope-corrected. Full
  record: `.claude/experiments/why-we-write-2026-08-10.md`.
- **DONE** — Phase 1.5A, Persona Architecture Audit (design/audit only,
  no code changes, no generations) → `.claude/persona-architecture-audit.md`.
- **PAUSED, not concluded** — Phase 1.5B, Fable review-seat ROI. Full
  record: `.claude/experiments/fable-review-roi-2026-08-10.md`.
- **DONE** — Phase 1.6, source-grounding hardening. DONE, not perfect —
  see `## PHASE 1.6 — DONE` below for the verdict and known limitations;
  full implementation/control history archived to
  `.claude/experiments/phase-1.6-source-grounding-2026-08-11.md`. Do not
  reopen by drift; only touch this code again if the regression suite
  fails or a real new grounding seam is found live.
- **NEXT** — persona-selection/routing architecture: `discovery.py`'s
  `_THEME_TO_PERSONA` dict and `generate.py`'s domain-keyword chain
  (~line 203) hard-route topics to personas independent of anything in
  `personas.py` — confirmed by direct trace, not assumed (Phase 1.6
  continuation, third-session). Today `space_cosmos`/`technology`/
  `science_nature`/`philosophy`/`behavioral_science` all route to Zen
  Circuit, not Pixel Nova — meaning Pixel's newly-rebuilt engine
  ("Deafness supplies Pixel's instrument, not Pixel's subject list") is
  true inside her prompt but NOT yet true at the selection layer: she
  cannot naturally win an astronomy/AI/science/philosophy story today,
  regardless of how strong her perceptual reframe would be. This is the
  next real work, not more grounding — abolish hard topic ownership so
  a persona is selected on the strength of their perceptual reframe, not
  a theme-keyword lookup. Affects all 4 personas' topic exposure, not
  just Pixel's — a redesign, not a one-line fix.
- **THEN** — Phase 2, brevity + evidence budget + testimony.
- **THEN** — Phase 3, persona architecture implementation (perceptual
  engines, motives, soft affinities, remove hard territories/prohibitions —
  informed by 1.5A's findings).
- **THEN** — same-source/four-persona probe (validates whatever Phase 3
  produces).
- **THEN** — Phases 4-8 (correction/repetition/readability/ending/final
  audit), original blueprint order, unaffected by this insert.

## HEAD / PROVENANCE
- **WHY WE WRITE doctrine commit**: `01339ce` — the SYSTEM-prompt swap in
  `automation/orchestrator/llm.py`, the permanent/frozen shared doctrine.
- **Fable review-seat ROI probe commit**: `b99d379` — generated the 8
  Phase 1.5B cases; later checkpoint commits only add provenance/docs, did
  not regenerate data.
- **CURRENT MAIN HEAD**: whatever `git rev-parse HEAD` says after the
  latest checkpoint commit — always AHEAD of the commits above by
  docs-only commits. A session seeing a different HEAD than cited here is
  not a bug.

## PHASE 1.6 — DONE

Source-grounding hardening. DONE, not perfect — known limitations below
are explicitly bounded, not hidden. Full implementation history (7
adversarial offline review rounds, live API controls, two corrected
rounds of live acceptance controls) archived verbatim to
`.claude/experiments/phase-1.6-source-grounding-2026-08-11.md`. Design
doc: `.claude/phase-1.6-source-grounding.md`.

**Story evidence:** planner/writer/reviewer/executor share one
`source_hash` and one `evidence_packet_hash` (`evidence_lineage`),
confirmed through the real `generate.py` persistence path, not just by
code inspection.

**Persona history:** writer/reviewer/executor share one persona
`context_hash` (`persona_factual_lineage`), separate provenance from
story evidence on purpose — one answers what source grounded the
article, the other what authorized a persona's first-person claims.

**Tamper:** candidate-excerpt-forgery rejection — PASS (`validate_evidence_field`).
Real `_load_frozen_brief` packet-identity-mismatch rejection — PASS (the
actual production gate, not a manual hash recreation).

**Hostile executor:** v2 (valid input) exposed two real failures — a
Berlin/2022 personal-memory fabrication, and a subtler unsupported-
premise-laundering failure ("What upset Rossi was..." — the source never
established that she was upset). Deterministic containment caught the
former (a bare new number). A prompt-contract fix ("EDITORIAL NOTES ARE
INSTRUCTIONS, NOT EVIDENCE") addressed the latter. v3 (same hostile
input, after the fix) showed no recurrence of either failure in one live
trial with Opus as the active fallback model.

**Deterministic-guard limitation, stated precisely:** the guards
(`find_new_unsupported_specifics`, `find_new_unsupported_personal_history`)
catch quote/name/number-shaped signals only — never treat "0 hits" as
semantic truth validation of arbitrary prose.

**Fable-specific behavior:** NOT independently tested post-fix — Fable
was unavailable in the v3 live call, so the executing model was Opus via
CLIProxy. Do not infer Fable's own behavior from this result; if it
matters, it belongs with the already-paused Phase 1.5B model-seat
question, not source-grounding.

**Permanent regressions** (run all five before touching this code again):
`grounding_test.py`, `executor_guard_test.py`, `writer_prompt_test.py`,
`lineage_persistence_test.py`, `snapshot_test.py --check`.

**Open, unrelated issue (logged, not fixed):** `_fable_update_state`'s own
docstring says "post-publish," but `generate.py` actually calls it before
the reviewer/executor block — see `OPEN INFRASTRUCTURE ISSUES` below.
Unrelated to grounding; do not derail a future session with it.

## FROZEN DECISIONS (do not reopen by drift)
- WHY WE WRITE (commit `01339ce`) is the shared publication doctrine.
  KEEP, scope-corrected: entitled to claim "improved or preserved the four
  personas under the then-current planning architecture," NOT "works
  under the final intended CripMinds pipeline" (that architecture is now
  known to include the contamination above). Do not rerun the 12+12
  doctrine experiment — after Phase 1.6, a small smoke confirmation
  suffices (see phase-1.6 doc's closing section).
- Historical persona territories are hypotheses, not canon — target
  architecture (perceptual engine / motive / affinity / risk / texture)
  is Phase 3 work, not started. Audit: `.claude/persona-architecture-audit.md`.
- Phase 1.5A persona audit is done; implementation waits for Phase 3.
- Phase 1.5B final model-seat decision waits until after Phase 1.6
  grounding — both reviewers in that experiment judged drafts whose
  factual substrate was already contaminated by an ungrounded planner.
- Production `temperature` stays unset/`None`; only probes pin it (0.9).
- Repetition judge (Phase 5) and ending judge (Phase 7): shadow-only
  first, backtested, never auto-block/auto-rewrite until real
  false-positive data justifies it.
- `engagement.db`/`disability_findings.db` living inside the repo checkout
  remains a known, mitigated risk (safe sync wrapper + daily backups);
  moving them out is deferred infrastructure hardening.
- CJ-2 remains future competitive persona reframing ("what does each
  persona's engine expose, which reframe is strongest" — not topic
  ownership), not scheduled.
- `_LENGTHS`/evidence-budget restructure, testimony extraction/weighting,
  Siri Sage's VOICE ANCHOR / any other persona prompt, thesis-timing /
  correction-discipline rules: do not touch until their own dedicated
  experiment.

## PAUSED EXPERIMENTS — what resumes after grounding
- **Fable review-seat ROI (Phase 1.5B)**: full 3-layer blind evaluation +
  causal safety audit done, model-seat decision deferred. Resumes as a
  small grounded review-seat follow-up once Phase 1.6 lands, not a repeat
  of the 8-case experiment. Record: `.claude/experiments/fable-review-roi-2026-08-10.md`.
- **WHY WE WRITE**: KEEP decision stands; resumes only as the small smoke
  confirmation described above. Record: `.claude/experiments/why-we-write-2026-08-10.md`.

## OPEN INFRASTRUCTURE ISSUES (not blocking Phase 1.6)
- `_fable_update_state`'s own docstring says "Post-publish: Fable reads
  the article and updates the persona's state.json... Called after a
  successful publish" -- found live 2026-08-11 while building
  `lineage_persistence_test.py` that this is NOT what the real code does:
  `generate.py` calls it at "Step 3b-0" (line ~908), BEFORE the reviewer/
  executor block, meaning persona state can evolve from a PRE-REVIEW
  draft, not the final published article. Unrelated to Phase 1.6
  grounding, not fixed -- logged here per explicit instruction not to
  derail this phase with it.
- CLIProxyAPI's dead Codex/ChatGPT-Plus OAuth account (expired 2026-07-20)
  can poison routing for ALL requests, not just its own — a `systemctl
  --user restart cliproxyapi` fixed it same-day. Still needs: remove/
  refresh the dead account, or file upstream that per-account refresh
  failures shouldn't affect other accounts.
- Real production article shipped degraded on 2026-08-10 09:03:24: Fable
  review returned `revise` but all four rewrite fallback attempts failed
  (403s/500/monthly key limits), so the article shipped unrevised and
  without images. Open question, not yet answered: was this stamped
  `pipeline_degraded` correctly, given `generate.py`'s Step 3b
  image-generation failure doesn't appear to be tracked by
  `_degraded_stages` at all — possibly undercounting the real failure
  surface. Not investigated further; check against the published
  article's frontmatter when reliability work has capacity.
- `--retry-failed` exists as general `phase_probe` infrastructure but was
  deliberately not used to patch `baseline-attempt-1` — a contiguous clean
  run was required instead, to avoid mixing external-condition windows in
  data meant to detect subtle writing differences.
- Rest of cripminds' backlog (judge-panel generation, persona evolution,
  shadow-check promotion, CJ-2, Stage B/D-E) stays in
  `.claude/audience-engagement-tasklist.md`, untouched.

## HISTORICAL RECORDS (full detail, not condensed)
- `.claude/experiments/phase-1.6-source-grounding-2026-08-11.md` — Phase 1.6
  full implementation history: 7 adversarial offline review rounds, live
  API controls, two corrected rounds of live acceptance controls (tamper +
  hostile-executor-input).
- `.claude/experiments/why-we-write-2026-08-10.md` — Phase 1 WHY WE WRITE
  3-topic + Pixel Nova 4th-persona validation, full 4-persona decision.
- `.claude/experiments/fable-review-roi-2026-08-10.md` — Phase 1.5B
  harness, 8-case run, 3-layer blind evaluation, safety audit that found
  the Phase 1.6 blocking finding.
- `.claude/persona-architecture-audit.md` — Phase 1.5A six-category
  persona matrix and territory-ownership bugs.
- `.claude/2026-08-10-engagement-db-incident.md` — Phase 0's
  `engagement.db` incident, fully recovered/closed.
- `.claude/audience-engagement-tasklist.md` — rest of the backlog, untouched by this roadmap.
