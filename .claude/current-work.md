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
**PHASE 0A — HARNESS VERIFIED, BASELINE PENDING EXTERNAL MODEL HEALTH.**
Must complete (9/9 healthy, in one contiguous run) before ANY creative-prompt
phase starts (see DO NOT TOUCH YET).

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

**phase_probe.py's harness itself is proven working** (2 clean samples,
zero mutation, twice in a row — see above). Then the official 3×3 baseline
was attempted for real and hit a real external outage:

**Official baseline attempt 1: INVALID / INTERRUPTED BY EXTERNAL MODEL
AVAILABILITY.** 2/9 healthy samples completed (`sauna-0`, `sauna-1`).
Beginning with `sauna-2`, 7/9 runs were correctly `rejected_degraded` —
model services became unavailable mid-run. No degraded output belongs in
the baseline; **the baseline is NOT accepted.**

Observed failure pattern, starting at `sauna-2` and persisting for the rest
of the run: `OpenRouter direct → 402 Payment Required`, `CLIProxy → 500
Internal Server Error`, `Nous → 403 Forbidden`. This strongly supports an
external provider/account/proxy availability problem (each full sample
makes ~13 model calls; failure began right after ~2 successful samples'
worth of spend) — **but the three status codes alone don't by themselves
prove one single shared billing cause; that's a reasonable hypothesis, not
a proven root cause.** No evidence of a phase_probe logic failure.

**This is also a real, adversarial validation of Phase 0B**: before today,
this exact kind of provider collapse could have produced apparently-valid
articles silently. Now, all 7 bad generations were automatically detected
(`degraded_stages` populated) and excluded from the experiment — a stronger
proof than any synthetic 403 test.

Post-batch mutation proof run across the FULL 9-attempt batch (including
the 7 degraded ones — a better isolation test than 9 successes, since it
exercises failure paths repeatedly): git status, both DBs (hashes +
`news_seeds`/table row counts), `_drafts/`/`assets/`, persona state — all
confirmed unchanged. Zero mutation held even under real, repeated upstream
failure.

**Preserved as evidence, not baseline data**: the full attempt-1 output
(2 clean + 7 `DEGRADED-*.md` + `metrics.json`) is committed at
`automation/probe_out/baseline-attempt-1/` — this is Phase 0B regression
evidence, do not delete.

**Harness improvement added as a direct result**: `preflight()` in
`phase_probe.py` — one minimal real call each through the writer path
(Opus/CLIProxy) and the Fable-brief path (Fable/CLIProxy, with its
reasoning budget capped so mandatory thinking doesn't read as a false
failure), run automatically before `--run` spends a full sample's ~13
calls. `--preflight` also available standalone. Probe-only, does not touch
production behavior. Also added `--retry-failed PHASE_NAME`: re-runs only
non-`ok` samples in an existing `metrics.json` in place, marks each retried
entry `"retried": true` (never silently indistinguishable from a
first-attempt success) — built as general infrastructure but **NOT the
right tool for finishing baseline attempt 1** (see below).

**Root cause of the outage turned out to be TWO separate things, both now
fixed:** (1) OpenRouter account hit a spending limit — user added credits,
confirmed fixed by a direct curl to OpenRouter (clean 200). (2) CLIProxyAPI
itself (`127.0.0.1:8317`, a shared user-systemd service also used by
cineporto-wa/inbox-bot) was independently returning `500` in 0-1ms per
request — too fast to be a real upstream call, meaning CLIProxy was failing
internally before even reaching Anthropic/OpenRouter. Traced via
`journalctl --user -u cliproxyapi`: CLIProxy has TWO subscription OAuth
accounts on file (`~/.cli-proxy-api/*.json`) — a Claude.ai account (healthy)
and a Codex/ChatGPT-Plus account whose refresh token has been dead since
**2026-07-20** (three weeks), which had NOT been blocking Claude-model
requests all along (confirmed: today's successful early samples ran fine
with that same dead token) — so the periodic failed-refresh attempt against
it appears to intermittently corrupt CLIProxy's own internal state/routing
for ALL requests, not just Codex ones. **Not a phase_probe bug, not a
CLIPROXY_URL/legacy-routing issue** — traced end-to-end
(`config.py:90-91`, hardcoded `http://127.0.0.1:8317/v1`, genuinely the
intended live route, not a misnamed generic variable) and confirmed
CLIProxyAPI is real, intentional, actively-used shared infrastructure (cost
savings via subscription OAuth instead of metered billing), not something to
route around. Fix: `systemctl --user restart cliproxyapi` (no sudo needed,
user-owned service) — `--preflight` immediately passed clean afterward.
Worth a separate follow-up decision later: either fix/remove the dead Codex
account, or make CLIProxy's refresh failures per-account instead of global.

**Decision, confirmed explicitly**: do NOT patch attempt 1 by retrying just
the 7 failed slots — combining `sauna-0`/`sauna-1` (one window) with 7
samples from a different window (different external conditions) would leave
an uncontrolled variable inside a baseline meant to detect subtle writing
differences later. Instead: preflight passed → running a completely FRESH
3×3, all new, as `--run baseline-attempt-2 --samples 3` (writes to
`probe_out/baseline-attempt-2/`). Requires 9/9 healthy in one contiguous run.
If this one is also interrupted, that's the moment to revisit whether nine
contiguous healthy generations is operationally realistic — not before.

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
4. ✅ Ran the official 3×3 baseline for real — hit a real external outage partway through (2/9 healthy, 7/9 correctly rejected). Preserved as `probe_out/baseline-attempt-1/` evidence, NOT accepted as the baseline. Added `--preflight` (auto-runs before `--run`) so a dead environment aborts before spending a full sample's calls.
5. **NEXT**: run `python3 automation/phase_probe.py --preflight` first, standalone, and confirm both routes pass. If clean: run a completely FRESH `--run baseline --samples 3` (writes to a new `probe_out/baseline/`, since attempt 1 now lives at `baseline-attempt-1/`) — require 9/9 `status: ok`, no exceptions, all in one contiguous run.
6. Re-run the mutation proof (before/after) across that fresh run too.
7. Freeze that baseline (commit hash + articles + prompts + metrics, committed to the repo) — only THEN update this file's ACTIVE PHASE to "Phase 0 COMPLETE" and start Phase 1.

## INFRASTRUCTURE BACKLOG (not Phase 0A, do not fix now)
- CLIProxyAPI's dead Codex/ChatGPT-Plus OAuth account (expired 2026-07-20)
  appears capable of poisoning routing for ALL requests, not just its own —
  a restart fixed it today, but an unrelated expired account shouldn't be
  able to break shared, healthy accounts. Fix later: either remove/refresh
  the dead Codex account, or file upstream that per-account refresh failures
  shouldn't affect other accounts' requests.

## DECISION LEDGER (settled, do not reopen)
- Production `temperature` stays unset/`None`. Only the probe pins it (0.9).
- Baseline = 3 topics (spanning 3 personas) × 3 samples each, same fixed article type/register/length across all — format variation is a separate, later probe.
- Testimony: extraction/preservation in the source block ships in the same round as the block-budget work; testimony-weighted *selection/ranking* stays shadow-only, its own future thread.
- Repetition judge (Phase 5) and ending judge (Phase 7): both ship shadow-only first, backtested against the real article corpus, never wired to auto-block/auto-rewrite until real false-positive data justifies promotion.
- The rest of cripminds' backlog (judge-panel/multi-draft generation, persona evolution, shadow-check promotion 2026-08-23, CJ-2, Stage B/D-E blockers) stays in `.claude/audience-engagement-tasklist.md`, untouched, NOT merged into this blueprint.
- `engagement.db`/`disability_findings.db` living inside the repo checkout is accepted as a known risk for now (mitigated by the safe sync wrapper + daily backups); moving them out entirely is deferred infrastructure hardening, not a blocker.
- WHY WE WRITE doctrine text is settled (short version, two guards: not-a-superpower, given-not-announced) — see project memory for exact wording. The *De Gebarentaaltolk en Ik* artwork reference stays OUT of the shipped prompt, confirmed.
- **First creative experiment, once Phase 0 baseline is frozen, is deliberately narrow**: replace ONLY the founder-biography/`PUBLICATION LENS`/`INTELLECTUAL FORMATION` system block with the short WHY WE WRITE doctrine — nothing else in the same pass. Then re-run the SAME frozen 3×3 inputs and compare against the frozen baseline. This answers one specific question first (did carving in the real purpose make writing more purposeful/persona-specific/worth reading, or just make it talk about disability more) before any other Phase 1 change gets layered on.
