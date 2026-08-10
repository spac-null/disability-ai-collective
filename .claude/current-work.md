# Current Work Checkpoint

Update this after every meaningful commit, not at the end of a session. A
fresh session should need this file (~500 words), not 100,000 tokens of
conversation archaeology.

## GOAL
Article-quality repair blueprint — rebuild cripminds' article-generation
prompt system around its true purpose (see `.claude/2026-08-10-*` docs and
project memory `project_cripminds_editorial_blueprint.md` / `project_cripminds_true_purpose.md`),
not as ten isolated style fixes.

## ACTIVE PHASE
**0A — controlled generation baseline** (`automation/phase_probe.py`).
Must complete before ANY creative-prompt phase starts (see DO NOT TOUCH YET).

## CURRENT HEAD
`ae7cd5a` (repo `disability-collective-ai`, `main`, pushed)

## DONE
- Phase 0B — fail-loud/degraded-run handling (`e4922e6`)
- Phase 0C — `_plan_follow_read` no-plan → deterministic N/A, not a model guess (`e4922e6`)
- `automation/engagement.db` incident — fully recovered and closed (`4ffb4c9`, `a37b169`). Full report: `.claude/2026-08-10-engagement-db-incident.md`
- Safe sync wrapper (`automation/sync_to_trident_for_testing.sh`) + automatic daily DB backups (`automation/backup_state_dbs.py`, trident cron 03:30) — `4ffb4c9`, `ae7cd5a`
- `temperature` param added to `_call_openai_compat_api` — opt-in, `None` by default, production behavior unchanged, pinned only inside the probe (`4ffb4c9`)
- 3 Fable briefs frozen successfully on trident (`automation/.probe_fixtures/brief_{sauna,hiring_tool,curb_cuts}.json`)

## CURRENT BLOCKER
First single-sample `phase_probe.py` run failed:
```
ValueError: too many values to unpack (expected 2)
```
Inside `_run_one_sample()`'s `capturing_call` wrapper (monkeypatches
`_call_openai_compat_api`) or somewhere in `call_llm_via_openclaw_session`'s
provider-cascade that unpacks its return value. **Root cause: UNKNOWN until
a full traceback is captured — do not guess further, do not keep editing
the harness blind.**

A debugging agent was dispatched (2026-08-10) with instructions to: capture
the real traceback, find the exact line, apply the smallest fix, re-verify
one clean sample live on trident (`error: None`, `degraded_stages: []`, real
article text), prove zero production-state mutation before/after (drafts,
assets, disability_findings.db news_seeds.used, engagement.db all 3 table
counts, persona_state), commit, push. **Check whether that agent's fix has
landed before re-diagnosing from scratch.**

An independent isolation-audit agent was also dispatched in parallel: reads
`phase_probe.py` against `_run_production_automation_locked`'s real tail and
lists every production-mutation path (git, drafts, assets, seeds, findings,
persona state, beat/citation ledgers, engagement DB, social queue),
confirming each is actually stubbed/redirected — a checklist, not a code
change. **Check its findings too before trusting the probe's isolation.**

## DO NOT TOUCH YET
Nothing in this list gets edited until Phase 0A's baseline (3 topics × 3
samples, healthy, zero-mutation-proven) exists and is frozen:
- WHY WE WRITE doctrine (`llm.py` SYSTEM block)
- `_LENGTHS` / length redistribution (`config.py`)
- Evidence-budget restructure (checklist → budget, `generate.py`)
- Testimony extraction/weighting in the source block (`generate.py`, `discovery.py`)
- Siri Sage's VOICE ANCHOR / any persona prompt (`personas.py`)
- Thesis-timing / correction-discipline rules (`generate.py`)

## NEXT ACCEPTANCE TEST (in order)
1. One healthy probe article: `error: None`, `degraded_stages: []`, real article text, real prompt saved.
2. Zero persistent-state mutation proven (before/after hashes/counts, see checklist above).
3. Repeat once more — same result, same zero-mutation proof.
4. Only then: run the full 3 topics × 3 samples = 9-article baseline.
5. Freeze that baseline (commit hash + articles + prompts + metrics) before touching anything in DO NOT TOUCH YET.

## DECISION LEDGER (settled, do not reopen)
- Production `temperature` stays unset/`None`. Only the probe pins it (0.9).
- Baseline = 3 topics (spanning 3 personas) × 3 samples each, same fixed article type/register/length across all — format variation is a separate, later probe.
- Testimony: extraction/preservation in the source block ships in the same round as the block-budget work; testimony-weighted *selection/ranking* stays shadow-only, its own future thread.
- Repetition judge (Phase 5) and ending judge (Phase 7): both ship shadow-only first, backtested against the real article corpus, never wired to auto-block/auto-rewrite until real false-positive data justifies promotion.
- The rest of cripminds' backlog (judge-panel/multi-draft generation, persona evolution, shadow-check promotion 2026-08-23, CJ-2, Stage B/D-E blockers) stays in `.claude/audience-engagement-tasklist.md`, untouched, NOT merged into this blueprint.
- `engagement.db`/`disability_findings.db` living inside the repo checkout is accepted as a known risk for now (mitigated by the safe sync wrapper + daily backups); moving them out entirely is deferred infrastructure hardening, not a blocker.
- WHY WE WRITE doctrine text is settled (short version, two guards: not-a-superpower, given-not-announced) — see project memory for exact wording. The *De Gebarentaaltolk en Ik* artwork reference stays OUT of the shipped prompt, confirmed.
