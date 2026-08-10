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
`bb38244` (repo `disability-collective-ai`, `main`, pushed, trident synced)

## DONE
- Phase 0B — fail-loud/degraded-run handling (`e4922e6`)
- Phase 0C — `_plan_follow_read` no-plan → deterministic N/A, not a model guess (`e4922e6`)
- `automation/engagement.db` incident — fully recovered and closed (`4ffb4c9`, `a37b169`). Full report: `.claude/2026-08-10-engagement-db-incident.md`
- Safe sync wrapper (`automation/sync_to_trident_for_testing.sh`) + automatic daily DB backups (`automation/backup_state_dbs.py`, trident cron 03:30) — `4ffb4c9`, `ae7cd5a`
- `temperature` param added to `_call_openai_compat_api` — opt-in, `None` by default, production behavior unchanged, pinned only inside the probe (`4ffb4c9`)
- 3 Fable briefs frozen successfully on trident (`automation/.probe_fixtures/brief_{sauna,hiring_tool,curb_cuts}.json`)

## CURRENT BLOCKER
**RESOLVED (commits `63d95da`, `bb38244`).** All 3 bugs fixed, verified live
on trident TWICE in a row: `error: None`, `degraded_stages: []`, real
~6.8K-char articles, zero production-state mutation proven before/after
(drafts hash, assets count, disability_findings.db hash + news_seeds
used-count, engagement.db's 3 table counts, persona_state hash, git status
— all identical). 3 Fable briefs committed as fixtures
(`automation/.probe_fixtures/brief_{sauna,hiring_tool,curb_cuts}.json`).

Bugs were: (1) `PROBE_REGISTER`/`PROBE_ARTICLE_TYPE` were 3-tuples copied
from raw config rows, but `_pick_register()`/`_pick_article_type()` return
2-tuples — root cause of the original crash (found by Agent A); (2)
`orch.drafts_dir`/`assets_dir` never `.mkdir()`'d after path isolation —
would've been the next crash; (3) degraded-run Telegram alerts read env
vars directly, unstubbed, could've messaged the real ops channel (2 and 3
found by Agent B's independent isolation audit, fixed by the main session).

**phase_probe.py's harness itself is now proven working.** Next action is
the actual 3×3 baseline run (2 more topics × 3 samples each, since topic 0
"sauna" already has 2 clean samples proven) — see NEXT ACCEPTANCE TEST below.

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
1. ✅ One healthy probe article: `error: None`, `degraded_stages: []`, real article text, real prompt saved. DONE.
2. ✅ Zero persistent-state mutation proven (before/after hashes/counts). DONE.
3. ✅ Repeated once more — same result, same zero-mutation proof. DONE (both on topic "sauna").
4. **NEXT**: run the OFFICIAL 3×3 baseline via the real CLI entry point (`python3 automation/phase_probe.py --run baseline --samples 3`), not the ad-hoc proof script used for steps 1-3 — this writes properly to `automation/probe_out/baseline/` with saved articles/prompts/`metrics.json`, which the ad-hoc proof script didn't do.
5. Freeze that baseline (commit hash + articles + prompts + metrics, committed to the repo) before touching anything in DO NOT TOUCH YET.

## DECISION LEDGER (settled, do not reopen)
- Production `temperature` stays unset/`None`. Only the probe pins it (0.9).
- Baseline = 3 topics (spanning 3 personas) × 3 samples each, same fixed article type/register/length across all — format variation is a separate, later probe.
- Testimony: extraction/preservation in the source block ships in the same round as the block-budget work; testimony-weighted *selection/ranking* stays shadow-only, its own future thread.
- Repetition judge (Phase 5) and ending judge (Phase 7): both ship shadow-only first, backtested against the real article corpus, never wired to auto-block/auto-rewrite until real false-positive data justifies promotion.
- The rest of cripminds' backlog (judge-panel/multi-draft generation, persona evolution, shadow-check promotion 2026-08-23, CJ-2, Stage B/D-E blockers) stays in `.claude/audience-engagement-tasklist.md`, untouched, NOT merged into this blueprint.
- `engagement.db`/`disability_findings.db` living inside the repo checkout is accepted as a known risk for now (mitigated by the safe sync wrapper + daily backups); moving them out entirely is deferred infrastructure hardening, not a blocker.
- WHY WE WRITE doctrine text is settled (short version, two guards: not-a-superpower, given-not-announced) — see project memory for exact wording. The *De Gebarentaaltolk en Ik* artwork reference stays OUT of the shipped prompt, confirmed.
