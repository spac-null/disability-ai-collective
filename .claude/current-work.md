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
- **NEXT / BLOCKING** — Phase 1.6, source-grounding hardening. Design doc:
  `.claude/phase-1.6-source-grounding.md`. Not started — no code changes,
  no generations against this design yet.
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

## THE BLOCKING FINDING — why Phase 1.6 exists
Phase 1.5B's brief audit found all 4 audited frozen planning briefs contain
at least one source-unsupported factual element (a named individual,
testimony, or quote) in `resisting_example`/`correction_moment`, written
by Fable at planning time from only a ~400-char source summary — not by
the writer. Causal chain: FABLE PLANNING BRIEF invents unsupported
evidence (confirmed 4/4 topics) → WRITER inherits/incorporates it
(confirmed 8/8 raw drafts) → REVIEW (Fable/Opus) is source-blind and
sometimes demands "the real words" → EXECUTOR (Opus) fabricates a
verbatim quote to comply (confirmed 4/8 Fable-triggered, 1/8
Opus-triggered). Full methodology and attribution tables:
`.claude/experiments/fable-review-roi-2026-08-10.md`.

## PHASE 1.6 — SOURCE-GROUNDING HARDENING (next, not started)
Full design: `.claude/phase-1.6-source-grounding.md`. Four substeps,
shipped together (not sequentially, to avoid leaving later stages free to
manufacture new unsupported specificity): (1) planner schema change —
structured evidence-candidate object with `status: found|not_found`,
never a flat string; (2) deterministic non-LLM validator between planner
and writer (quote/name/date substring + pointer checks); (3) source-aware
reviewer — receives the evidence packet, cannot demand evidence that
isn't in it; (4) source-aware executor — same constraint, never converts
paraphrase into quotation. Acceptance test uses adversarial
negative-control sources (deliberately lacking a witness/quote/anecdote)
as well as positive controls, not just cooperative sources.

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
