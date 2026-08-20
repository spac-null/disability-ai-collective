# Git and Runtime Baseline

Captured 2026-08-20. **Neither checkout was modified.** The only Git operation performed
was `git fetch origin` locally, to make the divergence figures accurate; it changed no
working-tree file and did not move HEAD.

## Canonical local repo

| Field | Value |
|---|---|
| Path | `/Users/stargatesgx/code/disability-collective-ai` |
| Branch | `main` |
| HEAD | `c6f97b84e158c2de512613f8963dc6979b4d4dac` (`c6f97b8`) |
| Tracked working tree | clean |
| Untracked paths | 78 (experiment fixtures, CJ-1/CJ-2 probe scripts, `sofa_discovery_shadow.py`) |
| Remote | `git@github.com:spac-null/disability-ai-collective.git` (PUBLIC) |

## Production checkout (Trident)

| Field | Value |
|---|---|
| Path | `/srv/data/hermes/workspace/disability-ai-collective` |
| Host | `trident` (up 11 days) |
| Branch | `main` |
| HEAD | `8af3622339210a9f13b96f944f028e8c28343f3e` (`8af3622`) |
| Tracked working tree | clean |
| Untracked | 3 — `.calibration-checkout/`, `automation/engagement.db.clobbered-20260810`, `automation/probe_out/baseline-attempt-2/` |
| vs origin/main | 0 ahead, 0 behind — **in sync** |

## origin/main

| Field | Value |
|---|---|
| HEAD | `8af3622339210a9f13b96f944f028e8c28343f3e` |
| Latest commit | `8af3622 Add new article: 2026-08-20-surovell-built-a-box-warren-tested-it-for-access-and` |

## Divergence — stated explicitly

**Local is 25 commits AHEAD of origin/main and 2 commits BEHIND.**

- The **25 ahead** are entirely `.claude/` evidence and documentation commits: the Sofa
  Article Form calibration lineage, Writer Grounding V0–V6, the Legacy Prompt/Rule
  Inventory, the owner triage, Real Article Test 2, and the migration plan.
  **None of them has been pushed. None of them is deployed. None of them touches
  `automation/` or any content directory.**
- The **2 behind** are production's own output, made on Trident and pushed from there:
  `11826e4 archive 1 draft(s) unpublished after 7d` and `8af3622 Add new article: …`.

**Production is actively running while this planning work proceeds.** It generated an
article this morning (2026-08-20) and pushed it. Any migration work must assume the daily
cadence continues.

## Code identity: local vs production — VERIFIED IDENTICAL

All 13 core production files were hashed on both machines and compared:

`production_orchestrator.py`, `orchestrator/{generate,llm,gate,review,grounding,discovery,config,personas,fact_check,cj2_shadow,testimony_l2}.py`, `style_rules.py`

**Result: 13 identical, 0 differing.**

This matters: it is what makes a locally-captured prompt baseline a *production* prompt
baseline. The 25 unpushed local commits change no pipeline code, so the two checkouts run
byte-identical logic even while their Git histories differ.

## Runtime configuration

### Production cron (the live cadence)

```
5  6  * * *   /srv/scripts/ops/cripminds-daily.sh news
0  9  * * *   /srv/scripts/ops/cripminds-daily.sh article     <-- daily generation
30 10 * * *   /srv/scripts/ops/cripminds-daily.sh stale-check
0  3  * * 0   automation/link_pool_crawler.py
30 10 * * 0   newsletter-weekly-digest.py
15 10 * * 6   git pull && automation/bsky_outreach_auto.py
0  8  */2 * * git pull && automation/publish_best.py          <-- draft -> _posts promotion
0  11 * * *   git pull && automation/engagement_fetch.py --days 90
30 3  * * *   automation/backup_state_dbs.py                  <-- daily safe DB backup
```

### Feature flags

`CJ2_INTEGRATION_MODE` and `L2_TESTIMONY_MODE` are **not set anywhere** on the production
host — not in `/srv/secrets/`, not in `/etc/environment`. Both therefore take their code
defaults: **`OFF`**. CJ-2 and L2 testimony are confirmed inert in production.

### Provider routing

`/srv/secrets/openclaw.env` carries (keys only, no values read): `ANTHROPIC_API_KEY`,
`ANTHROPIC_BASE_URL`, `OPENROUTER_API_KEY`, `CLIPROXY_KEY`, `GEMINI_API_KEY`,
`DEEPSEEK_API_KEY`, `NVIDIA_API_KEY`, plus publishing/social credentials.

The writer call routes through `call_llm_via_openclaw_session`; the editorial/gate/review
calls route through `_call_openai_compat_api` against `CLIPROXY_URL`
(`http://127.0.0.1:8317/v1`). **CLIProxy is local to Trident**, which is why the production
writer path is unreachable from the Mac and why migration Phase 5 must run on Trident.

### Disk

`/dev/nvme0n1p2` — 116G total, 93G used, **18G available, 85% used**. Adequate for the
Phase-0 backup (24 MB) but worth watching before any phase that writes large artefacts.
