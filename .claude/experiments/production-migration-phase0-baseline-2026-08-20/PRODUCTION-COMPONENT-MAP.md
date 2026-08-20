# Production Component Map — from runtime, not from docs

Every location below was read from code or runtime at HEAD `8af3622` (production) /
`c6f97b8` (local, byte-identical pipeline code). Where a document and the runtime disagreed,
the runtime is recorded.

## Entry point and stage order

`/srv/scripts/ops/cripminds-daily.sh article` (cron, 09:00 daily)
→ `automation/production_orchestrator.py` — a 186-line entry point that composes 13 mixins
→ `GenerateMixin._run_production_automation_locked()` (`generate.py:191–1454`)

| # | Stage | Call site | Notes |
|---|---|---|---|
| 1 | news seed / DB discovery | `generate.py:208,211` | `news_seeds` table, 1,274 rows |
| 2 | source fetch + evidence packet | `discovery.py:1142`, `grounding.py:129` | fetched text is **not persisted** |
| 3 | L2 testimony shadow | `generate.py:414` | `L2_TESTIMONY_MODE` unset → OFF |
| 4 | Fable brief / commission | `generate.py:420` → `llm.py::_fable_editorial_brief` | ~18,035 ch prompt |
| 5 | Story Rejection verdict | `generate.py:435,442,447` | decline / defer / no-execution |
| 6 | CJ-2 shadow | `generate.py:551` | `CJ2_INTEGRATION_MODE` unset → OFF |
| 7 | writer prompt assembly | `generate.py:783–1050` | 59,161 ch assembled (Maya) |
| 8 | writer call | `generate.py:1057` | `call_llm_via_openclaw_session` |
| 9 | fallback article | `generate.py:1064` | generic template on total provider failure |
| 10 | persona biography editorial pass | `generate.py:1154,1197` | can set `persona_biography_unresolved` |
| 11 | whole-document rewrite | `generate.py:1168` → `llm.py:343` | 25,019 ch SYSTEM, 47 rules |
| 12 | pre-publication check | `generate.py:1207` | |
| 13 | article plan persistence | `generate.py:1276` | → `engagement.db.article_plans` |
| 14 | pre-commit gate | `generate.py:1302` → `gate.py:218` | **blocking**, R1–R17 |
| 15 | degraded-run block policy | `generate.py:1353` → `_compute_should_block` | `generate.py:71` |
| 16 | review | `generate.py:1401` → `review.py:849` | R1–R19 + fact-check + engagement |
| 17 | publication safety stamp | `generate.py:1415` | writes `pipeline_degraded` frontmatter |

## Component-by-component

| Component | Runtime location | Observed state |
|---|---|---|
| **production_orchestrator / generate path** | `automation/production_orchestrator.py` (186 lines, 13 mixins); `orchestrator/generate.py` (128,399 bytes) | LIVE, runs 09:00 daily |
| **Fable brief / commission** | `llm.py::_fable_editorial_brief` (`llm.py:847–1330`) | LIVE. Emits `source_decision`, persona, register, `opening_scene`, `seed_sentence`, `angle`, `cross_cite`, `correction_moment`, `resisting_example` |
| **Story Rejection V1.1** | `grounding.py::validate_source_decision`, `STORY_REJECTION_CONTRACT_VERSION`; `discovery.py:1443,1487,1518,1572`; handlers `generate.py:1455/1495/1526` | LIVE. Decline persisted to `news_seeds.decline_json` with contract version |
| **PRF1** | `discovery.py::_rotation_eligible_agents:126`; consumed `generate.py:388`, constraint built `llm.py:918` | LIVE. Rotation constrains persona execution |
| **writer prompt assembly** | `generate.py:783–1050` | LIVE. 59,161 ch / 9,862 words / 75 rule units (Maya Flux) |
| **writer SYSTEM prompt** | `llm.py:232` | LIVE. 3,212 ch |
| **persona canon injection** | `llm.py::_load_persona_canon:571`, `_load_persona_factual_context:589`; files `automation/persona_canon/*.md` | LIVE. Injected **twice** for fictional personas |
| **rewrite stage** | `llm.py::rewrite_with_opus:343`, SYSTEM at `llm.py:394` | LIVE. 25,019 ch, 47 numbered rules |
| **gate stage** | `gate.py::_pre_commit_gate:218`, `GATE_SYSTEM:233`, `SUBJECT_SYSTEM:51`, `FIX_SYSTEM:510,530` | LIVE, **blocking**. Deterministic checks at `gate.py:76,117,130,623` |
| **review stage** | `review.py::validate_article:849`, `RULES_SYSTEM:1173`, `CITATION_SYSTEM:879`, `_engagement_read:24` | LIVE, advisory |
| **web fact-check** | `fact_check.py::_run_web_fact_check:225`, `_attempt_fabrication_repair:281`; called `review.py:924,995,1003` | LIVE |
| **grounding.py** | `automation/orchestrator/grounding.py` (84,672 bytes) | LIVE. Packet building, field validation, unsupported-specifics scanners, lineage. **No modular arbitration layer** |
| **`_compute_should_block`** | `generate.py:71–105` | LIVE and **actively firing** — blocks on `fable_brief`, `gate_llm`, `persona_biography_unresolved`, or ≥2 degraded stages |
| **publication / promotion** | `automation/publish_best.py` via cron `0 8 */2 * *`; drafts → `_posts` | LIVE, every 2 days |
| **fallback article path** | `generate.py:1064` → `content_checks.py::generate_fallback_article:297` | LIVE, publishes a generic template rather than holding |
| **model / provider routing** | writer: `call_llm_via_openclaw_session` (`llm.py:218`); editorial/gate/review: `_call_openai_compat_api` → `CLIPROXY_URL` `http://127.0.0.1:8317/v1` | LIVE. CLIProxy is Trident-local |
| **CJ2** | `orchestrator/cj2_shadow.py` | **OFF** — flag unset on host; entry point not called |
| **Reader Lab** | `reader-lab/`, `reader-lab-worker/` (Cloudflare worker) | **NOT WIRED** — verified: nothing in `automation/` imports it |

## Corrections to prior documentation

| Prior claim | Runtime reality |
|---|---|
| "No SQLite-safe backup exists yet (open risk)" — carried in `PROJECT-MAP.md` and repeated in the migration plan's `ROLLBACK-AND-SHADOW-PLAN.md` | **False.** `automation/backup_state_dbs.py` has run daily at 03:30 since 2026-08-10, using SQLite's `Connection.backup()` API with a post-backup `integrity_check` and 14-day retention to `/srv/backups/cripminds`. Both live DBs are covered and today's backups verified `ok`. Corrected in this task. |
| Migration plan listed the DB backup gap as a constraint gating later phases | That constraint is **removed**. The real remaining gap is that backups **rotate at 14 days**, which is why this task took a separate retained Phase-0 baseline. |
