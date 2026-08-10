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

## CURRENT BLOCKER (mostly resolved, verification pending)

**Root cause FOUND (Agent A)**: `PROBE_REGISTER`/`PROBE_ARTICLE_TYPE` were
3-tuples `(name, weight, prompt)` copy-pasted from `_REGISTERS`/
`_ARTICLE_TYPES`'s raw config rows, but the real `_pick_register()`/
`_pick_article_type()` return 2-tuples `(name, prompt)` — generate.py does
`register, register_prompt = self._pick_register()`, which broke with
"too many values to unpack (expected 2)" once stubbed to the 3-tuple. Fixed:
both constants are now real 2-tuples in `phase_probe.py`. Not yet committed.

**Two more gaps found (Agent B, independent isolation audit) and already
fixed locally on top of Agent A's fix, NOT yet pushed/committed:**
1. `orch.drafts_dir` was never `.mkdir()`'d after `_isolate_paths` reassigns
   it — would have been the NEXT crash (`create_article_file` does a bare
   `open()`, no parent mkdir). Added `.mkdir(parents=True, exist_ok=True)`
   for both `drafts_dir` and `assets_dir` in `_run_one_sample`.
2. Degraded-run/fallback-mode Telegram alerts in `generate.py` read
   `REEF_BOT_TOKEN`/`REEF_CHAT_ID` from the environment directly (not
   patchable) — could send a REAL message to the real ops channel if a
   sample's `_degraded_stages` comes back non-empty on a host where those
   are exported (plausible on trident). Added a save/pop/restore of both
   env vars scoped to just the `_run_production_automation_locked()` call.

Agent B's audit otherwise confirmed every other production-mutation path
(git, disability_findings.db used-flags, persona state, beat/citation
ledgers, article_plans, engagement.db, social queue, image generation,
Fable brief) is genuinely covered — read line-by-line, not assumed.

**Status as of this checkpoint: local repo has all 3 fixes applied
(register/type tuple + drafts_dir mkdir + Telegram neutralization), syntax-
verified, but NOT yet re-tested live on trident with all 3 together, NOT
committed, NOT pushed.** Agent A was notified of the extra 2 fixes and
asked to do the final combined verification + commit + push. **Check
whether that landed before re-diagnosing or re-fixing anything.**

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
