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
**PHASE 0: COMPLETE.** Ready to start Phase 1 (see NEXT STEP below).

## CURRENT HEAD
`dcca441` (code) + baseline committed on top (repo `disability-collective-ai`, `main`, pushed, trident synced)

## PHASE 0 — DONE
- 0B fail-loud/degraded-run handling; 0C plan-follow N/A invariant (both `e4922e6`)
- `automation/engagement.db` incident: fully recovered/closed (`4ffb4c9`, `a37b169`) — full report `.claude/2026-08-10-engagement-db-incident.md`
- `automation/phase_probe.py` built: dry-run harness, `--freeze-briefs`, `--preflight`, `--retry-failed`, zero production-state mutation (proven repeatedly, including under real provider failure)
- **Canonical baseline frozen**: `automation/probe_out/baseline/` — 9/9 `status=ok`, 9/9 `degraded_stages=[]`, 3 topics (sauna/Siri Sage, hiring_tool/Zen Circuit, curb_cuts/Maya Flux) × 3 samples, same frozen brief hash per topic, commit `dcca441`, temperature 0.9, register wry, article_type essay, target 1000 words. Post-batch zero-mutation proof passed. An earlier attempt (`baseline-attempt-1/`, 2 ok + 7 rejected_degraded) is preserved as Phase 0B regression evidence, NOT part of the baseline — real mid-run outage (OpenRouter billing limit + a separate CLIProxyAPI internal fault, both fixed; see INFRASTRUCTURE BACKLOG).

## NEXT STEP — first creative experiment (narrow, do this one thing only)
Replace ONLY the founder-biography/`PUBLICATION LENS`/`INTELLECTUAL FORMATION`
system block in `llm.py`'s `SYSTEM` string with the short WHY WE WRITE
doctrine (exact text in `project_cripminds_editorial_blueprint.md` memory —
two guards: not-a-superpower, given-not-announced; keep the *De
Gebarentaaltolk en Ik* artwork reference OUT of the prompt). Nothing else in
this pass — not personas.py, not thesis/correction rules, not `_LENGTHS`.
Then re-run the SAME frozen 3×3 inputs (`--run whywewrite-v1` or similar) and
compare against `probe_out/baseline/`. Question this answers: did carving in
cripminds' real purpose make writing more purposeful/persona-specific, or
just make it talk about disability more?

## DO NOT TOUCH YET (until their own dedicated experiment)
`_LENGTHS`/evidence-budget restructure, testimony extraction/weighting,
Siri Sage's VOICE ANCHOR / any other persona prompt, thesis-timing /
correction-discipline rules.

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
