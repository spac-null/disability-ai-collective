# Current Work Checkpoint

Update this after every meaningful commit, not at the end of a session. A
fresh session should need this file (~500 words), not conversation
archaeology.

## GOAL
Article-quality repair blueprint — rebuild cripminds' article-generation
prompt system around its true purpose (see project memory
`project_cripminds_editorial_blueprint.md` / `project_cripminds_true_purpose.md`),
not as ten isolated style fixes.

## ACTIVE PHASE
**PHASE 0: COMPLETE.** First creative experiment (WHY WE WRITE v1) IN PROGRESS — see NEXT STEP.

## CURRENT HEAD
`01339ce` (repo `disability-collective-ai`, `main`, pushed, trident fast-forwarded onto this exact commit via `git pull` — not rsync)

## PHASE 0 — DONE
- 0B fail-loud/degraded-run handling; 0C plan-follow N/A invariant (both `e4922e6`)
- `automation/engagement.db` incident: fully recovered/closed (`4ffb4c9`, `a37b169`) — full report `.claude/2026-08-10-engagement-db-incident.md`
- `automation/phase_probe.py` built: dry-run harness, `--freeze-briefs`, `--preflight`, `--retry-failed`, zero production-state mutation (proven repeatedly, including under real provider failure)
- **Canonical baseline frozen**: `automation/probe_out/baseline/` — 9/9 `status=ok`, 9/9 `degraded_stages=[]`, 3 topics (sauna/Siri Sage, hiring_tool/Zen Circuit, curb_cuts/Maya Flux) × 3 samples, same frozen brief hash per topic, commit `dcca441`, temperature 0.9, register wry, article_type essay, target 1000 words. Post-batch zero-mutation proof passed. An earlier attempt (`baseline-attempt-1/`, 2 ok + 7 rejected_degraded) is preserved as Phase 0B regression evidence, NOT part of the baseline — real mid-run outage (OpenRouter billing limit + a separate CLIProxyAPI internal fault, both fixed; see INFRASTRUCTURE BACKLOG).

## NEXT STEP — WHY WE WRITE v1 (in progress, do not touch mid-run)
Done: `llm.py`'s `SYSTEM` string had its `PUBLICATION LENS`/`INTELLECTUAL
FORMATION` founder-biography blocks (lines 130-164, Van Abbemuseum/Exploded
City/bic pen/Tussenruimte etc.) deleted and replaced with the short WHY WE
WRITE doctrine, verbatim as given 2026-08-10 (not the earlier
`project_cripminds_editorial_blueprint.md` wording — this session's text
supersedes it for v1). Reader block and everything else (incl. the
"strong thesis from sentence one" line — thesis-timing is explicitly
untouched this pass) left alone. Isolated commit `01339ce`, one file, exactly
that block replacement — verified via `git show --stat` + `git show`.
`_LENGTHS`/personas.py/thesis/correction rules: untouched, confirmed by diff.

**Provenance incident, caught before it mattered**: first attempt started the
3×3 run against trident's *uncommitted* rsynced copy of the change while HEAD
still pointed at the baseline commit — would have made every sample's
recorded commit hash lie about what code produced it. Caught before any
sample was written (0 files in `probe_out/whywewrite-v1/`), killed the
process, committed+pushed properly, fast-forwarded trident onto `01339ce` via
normal `git pull` (not `sync_to_trident_for_testing.sh` — that script is
rsync-only and explicitly for *pre-commit* live testing, not for getting a
committed experiment onto trident), re-ran `--preflight`, then started the
real run. **Lesson for every future phase_probe experiment**: commit the
prompt change FIRST, verify trident's `git rev-parse HEAD` matches, THEN run
`--run <phase>` — never probe against an uncommitted rsync.

Currently running (background, trident, started 2026-08-10 ~18:18 CET):
`python3 automation/phase_probe.py --run whywewrite-v1 --samples 3`.
**Do not touch code, do not commit anything else, and do not read partial
`probe_out/whywewrite-v1/*.md` output while this is in flight** — ten
minutes for nine full production-path generations (writer + real
`_pre_commit_gate` call each) is normal, not stuck.

**When it finishes, mechanical acceptance BEFORE reading any prose**:
9/9 files exist, 9/9 `status=ok`, 9/9 `degraded_stages=[]`, all 9 provenance
fields say `01339ce`, 3 samples per frozen topic (sauna/hiring_tool/curb_cuts),
frozen brief hashes match baseline's, then the full post-run
production-state zero-mutation proof. Only after all of that passes:

**Structured comparison, blind where practical, across baseline vs v1's 9
outputs each** — the four predeclared questions (WHY THIS WRITER / WHAT DID
THEY GIVE ME / WHY KEEP READING / REGRESSION — did v1 just make the prose say
"disability/perception/knowledge/marginality/reclamation/contribution" more
often instead of changing what gets noticed and how it's organized), PLUS a
mechanical smoke check the regression question implies: raw frequency/context
count of doctrine-adjacent vocabulary, baseline vs v1 — not a quality score,
just a prompt-leakage detector. Use two independent sub-agents (one
implementation-verification, one blind editorial comparison) per the
original request. Report KEEP / REVISE / REJECT before discussing anything
else, including the queued experiment below.

## DO NOT TOUCH YET (until their own dedicated experiment)
`_LENGTHS`/evidence-budget restructure, testimony extraction/weighting,
Siri Sage's VOICE ANCHOR / any other persona prompt, thesis-timing /
correction-discipline rules.

## MODEL-SEAT ROI EXPERIMENT — queued, DO NOT CHANGE during WHY WE WRITE v1
Recorded 2026-08-10 as a future controlled experiment, explicitly NOT applied
to the run currently in flight — changing model routing mid-WHY-WE-WRITE-v1
would add a second independent variable and destroy the causal comparison.

Fable currently occupies several expensive editorial seats; we haven't
independently proven each seat's ROI:
1. **Planning/editorial brief** — production uses Fable here. `phase_probe`
   experiments (baseline, v1, and future ones) do NOT retest this seat —
   briefs are frozen fixtures, deliberately, so every creative-prompt
   experiment gets identical planning input. Any future finding from the
   seats below must NOT be generalized to this seat.
2. **Whole-article editorial review** — Fable evaluates an Opus-written
   draft, identifies structural problems.
3. **Polish/revision** — if Fable requests a revision, Fable may currently
   also perform the rewrite. Suspected most-expensive-least-necessary seat:
   deciding what's wrong may need more editorial judgment than executing a
   specified rewrite.

Hypothesis: Fable may earn its cost as editor/director, not necessarily as
writer/rewrite engine. Expected sweet spot to test, not assume: Fable
decides, Opus writes.

Suggested first comparison (frozen inputs, blind grading):
- A — CURRENT: Fable review + Fable revision
- B — HYBRID: Fable review + Opus executes the requested revision
- C — ECONOMICAL: Opus review + Opus revision

Compare on: final article quality, structural-problem detection, false-positive
editorial notes, whether requested revisions actually improve the article,
per-article token/cost, latency, degradation/failure rate.

Primary question: does Fable materially improve the DECISION about what's
wrong? Secondary question: once the problem is specified, does paying Fable
(vs Opus) to perform the rewrite materially improve the result?

Sequencing: test B vs A first (cheapest hypothesis, changes ~nothing about
editorial intelligence, potentially eliminates the priciest low-leverage
Fable usage). Only if B ≈ A, ask whether C ≈ B (does Fable earn the review
seat either). The planning-seat question (Fable-authored plan vs Opus-authored
plan) needs a separate experimental design later — the frozen-brief
architecture here structurally cannot answer it, so don't infer planning ROI
from this ablation.

Placement: run this fairly early in the phase sequence (after WHY WE WRITE
v1 is resolved, before deciding exact slotting relative to length/evidence/
testimony work) — if the hybrid holds quality, every later 3×3 experiment
gets cheaper. But finish WHY WE WRITE v1 first, with the exact model
architecture the baseline used, or we lose the cleanest causal comparison
built so far.

## INFRASTRUCTURE BACKLOG (not blocking Phase 1)
CLIProxyAPI's dead Codex/ChatGPT-Plus OAuth account (expired 2026-07-20)
can apparently poison routing for ALL requests, not just its own — a
`systemctl --user restart cliproxyapi` fixed it same-day. Fix later:
remove/refresh the dead account, or file upstream that per-account refresh
failures shouldn't affect other accounts.

## DECISION LEDGER (settled, do not reopen)
- Production `temperature` stays unset/`None`; only the probe pins it (0.9).
- Baseline = 3 topics × 3 samples, same fixed type/register/length — format variation is a separate future probe.
- Testimony: extraction/preservation ships with the block-budget work; weighted *selection* stays shadow-only.
- Repetition judge (Phase 5) and ending judge (Phase 7): shadow-only first, backtested, never auto-block/auto-rewrite until real false-positive data justifies it.
- Rest of cripminds' backlog (judge-panel generation, persona evolution, shadow-check promotion, CJ-2, Stage B/D-E) stays in `.claude/audience-engagement-tasklist.md`, untouched.
- `engagement.db`/`disability_findings.db` living inside the repo checkout is a known, mitigated risk (safe sync wrapper + daily backups); moving them out is deferred infrastructure hardening.
- `--retry-failed` exists as general phase_probe infrastructure but was deliberately NOT used to patch baseline-attempt-1 — a contiguous clean run was required instead, to avoid mixing external-condition windows in data meant to detect subtle writing differences.
