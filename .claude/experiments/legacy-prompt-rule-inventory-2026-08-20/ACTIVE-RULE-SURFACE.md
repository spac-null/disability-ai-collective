# Active Rule Surface

Every rule-bearing string that reaches a live model call on a production article run.
Sizes are **measured**, not estimated: static literals via AST `literal_eval`, dynamic
prompts via the repo's own zero-network capture harnesses.

Nothing in this file is inferred from documentation. Where documentation and code
disagree, code wins and the disagreement is noted.

---

## 1. PRODUCTION — reaches a model on every run

| ID | Prompt | Source | Size (ch) | Rule units | Assembly | Consumer call |
|---|---|---|---|---|---|---|
| P-WRITER | Writer user prompt | `orchestrator/generate.py:783–1050` | 59,161 (Maya) / 54,673 (Pixel) | 75 | dynamic concat, ~270 src lines | `call_llm_via_openclaw_session` |
| P-WSYS | Writer system prompt | `orchestrator/llm.py:232` | 3,212 | ~8 blocks | static literal | `call_llm_via_openclaw_session` |
| P-REWRITE | Whole-document rewrite system | `orchestrator/llm.py:394` | 25,019 | 47 numbered | static literal | `rewrite_with_opus` |
| P-PLAN | Planner brief user prompt (carries Story Rejection L1/L2) | `orchestrator/llm.py::_fable_editorial_brief` | 15,358 | 4 blocks + JSON field contract | dynamic concat | `_call_editorial_model` |
| P-PLANSYS | Planner system prompt | same, `system = (…)` | ~380 | 1 block | static | `_call_editorial_model` |
| P-REVIEW | `RULES_SYSTEM` | `orchestrator/review.py:1173` | 9,035 | R1–R19 | static literal | `validate_article` |
| P-GATE | `GATE_SYSTEM` | `orchestrator/gate.py:233` | 8,105 | R1–R17 | static literal | `_pre_commit_gate` (**BLOCKING**) |
| P-ENGAGE | Engagement read ("busy reader on a phone") | `orchestrator/review.py::_engagement_read` | 4,161 | — | static | `validate_article` |
| P-EXEC | `_EXECUTOR_CONTRACT` | `orchestrator/llm.py:61` | 2,007 | 1 contract | static literal | executor passes |
| P-XCITE | Persona cross-cite accuracy | `orchestrator/fact_check.py::_check_persona_crosscite_accuracy` | 1,484 | — | static | `validate_article` |
| P-FIXREG | `FIX_SYSTEM` (register repair) | `orchestrator/gate.py:510` | 1,221 | — | static | gate repair path |
| P-LINK | Link editor | `orchestrator/content_checks.py:373` | 1,070 | — | static | `smart_inject_links` |
| P-FACT | Claim extraction | `orchestrator/fact_check.py:33` | 905 | 4 categories | static | `_run_web_fact_check` |
| P-EXECPH | `_EXECUTOR_PERSONA_HISTORY_CONTRACT` | `orchestrator/llm.py:101` | 750 | 1 contract | static literal | executor passes |
| P-SUBJ | `SUBJECT_SYSTEM` (article-type compliance) | `orchestrator/gate.py:51` | 533 | — | static | `_check_article_type_compliance` |
| P-CITE | `CITATION_SYSTEM` | `orchestrator/review.py:879` | 517 | 4 categories | static | `validate_article` |
| P-FIXFORM | `FIX_SYSTEM` (form repair) | `orchestrator/gate.py:530` | 421 | — | static | gate repair path |

**Total rule-bearing prompt text per article ≈ 130,000 characters.**
**Total distinct prescriptive rule statements ≈ 158** (75 + 47 + 19 + 17).

### Data tables that become prompt text (PRODUCTION)

| ID | Table | Source | Size | Consumer |
|---|---|---|---|---|
| P-FORM | `_ARTICLE_TYPES` — 9 forms, weighted | `orchestrator/config.py:140` | 9 entries | `_pick_article_type` → `FORM:` line in P-WRITER |
| P-INDEF | `_INDEFENSIBLE_PROMPTS` — 4 persona-specific forms | `orchestrator/config.py:183` | 4 entries | same, when type == `indefensible` |
| P-REG | `_REGISTERS` — 6 registers, weighted | `orchestrator/config.py:115` | 6 entries | `_pick_register` → `STARTING REGISTER:` in P-WRITER |
| P-LEN | `_LENGTHS` — 6 word-count buckets, weighted | `orchestrator/config.py:131` | 6 entries | `_pick_length` → `LENGTH:` in P-WRITER |
| P-BEATS | `_AGENT_BEATS` — persona→subject territories | `orchestrator/config.py:258` | 4×4 | `_get_beat_nudge` → `BEAT NOTE:` in P-WRITER |
| P-THEME | `_THEME_CLUSTERS` | `orchestrator/config.py:266` | 4 clusters | `_get_overused_themes` → `DIVERSITY NOTE` |
| P-CONFL | `_PERSONA_CONFLICTS` | `orchestrator/config.py:274` | pairs | fault-line block in P-PLAN |
| P-SHAPE | `_STRUCTURAL_SHAPES` | `orchestrator/config.py:359` | — | `_get_shape_nudge` |
| P-PB | `AGENTS[*]['prompt_block']` | `orchestrator/personas.py:15` | 3,323–4,337 ch each | opens P-WRITER |
| P-CANON | `persona_canon/<slug>.md` | 5 files, 5,930–9,170 ch | | `_load_persona_canon` → **injected twice** into P-WRITER |
| P-FACTUAL | `persona_canon/pixel-nova-factual.md` | 8,264 ch | | `_load_persona_factual_context` (Pixel only) |

### Dynamic rule injectors (PRODUCTION)

`discovery.py`: `_get_beat_nudge`, `_get_scholar_nudge`, `_get_blocked_theorists`,
`_get_recent_dates_nudge`, `_get_shape_nudge`, `_get_calendar_event_nudge`,
`_get_claims_nudge`, `_get_recent_title_patterns`, `_get_overused_themes`,
`_check_title_freshness`, `_get_recent_openings`, `_get_cross_reference`.
All concatenated into P-WRITER or P-PLAN at `generate.py:655–773` / `llm.py:960–990`.

### Deterministic (non-LLM) rule enforcement — PRODUCTION

These encode rule responsibility in code rather than prompt text and are genuinely active:

| Check | Location |
|---|---|
| `_check_buried_clause_sentences`, `_check_argument_word_overuse`, `_check_sentence_length_distribution`, `_check_article_type_compliance` | `gate.py` |
| `_check_opening_template_shadow`, `_check_bullet_points_shadow`, `_check_truncated_ending_shadow`, `_check_seam_shadow`, `_check_repetition_shadow`, `_check_length_adherence_shadow`, `_check_forbidden_word_lists_shadow` | `review.py` |
| `validate_evidence_field`, `scan_free_prose_field`, `find_new_unsupported_specifics`, `validate_brief`, `validate_source_decision`, `scan_draft_for_unsupported_specifics`, `find_new_unsupported_personal_history` | `grounding.py` |
| `validate_rewrite_integrity`, `find_duplicated_block` | `rewrite_integrity.py` |
| `find_personal_contact_claims`, `check_provenance` | `human_detail_provenance.py` |
| `find_template_match`, `shared_shingle_count` | `opening_template_detector.py` |

---

## 2. SHADOW — implemented, gated OFF, or unreachable from production

| ID | Surface | Location | Gate | Status |
|---|---|---|---|---|
| S-CJ2 | CJ-2 shadow integration | `orchestrator/cj2_shadow.py` | `CJ2_INTEGRATION_MODE` (default `OFF`) | mixin exists on the orchestrator; entry point not called when OFF; `PRODUCTION_AUTHORITY` mode does not exist in the module |
| S-L2 | L2 testimony companion | `orchestrator/testimony_l2.py` | `L2_TESTIMONY_MODE` (default `OFF`) | deterministic heuristic + companion eligibility; explicitly kept shadow, feeds future calibration |
| S-SOFA | SOFA discovery/writer/grounding-audit shadow | `orchestrator/sofa_discovery_shadow.py` (65,335 ch) | none — **not imported by production at all** | `build_shadow_discovery_prompt`, `build_shadow_writer_prompt`, `build_shadow_grounding_audit_prompt`, `assert_no_persona_leakage`. Only importers are `.claude/experiments/sofa-real-ab-1-2026-08-18/**` and `automation/sofa_discovery_shadow_test.py` |
| S-WG | Writer Grounding V0–V6 + final shadow | `.claude/experiments/writer-grounding-*/` only | n/a | **zero production wiring.** Owner status: SHADOW-CALIBRATED CANDIDATE, not production-validated, not transfer-validated |
| S-CJ1 | CJ-1 v3 source-friction gate | `automation/cj1_v3_probe.py` + `cj1_v3_*.py` | n/a | probe scripts, three prompt versions (`V3_SYSTEM_PROMPT`, `V3_1_`, `V3_2_`) |
| S-CJ2B2 | CJ-2 B2 competitive reframing | `automation/cj2_b2_*.py` (~15 files) | n/a | probe/prototype scripts |

**Confirmed:** `grep -rn "sofa_discovery_shadow"` over `production_orchestrator.py` and
`orchestrator/*.py` returns **nothing**. Production does not touch the SOFA
implementation.

---

## 3. Documented-vs-code discrepancies found during this audit

| Doc claim | Code reality |
|---|---|
| `.claude/CONTEXT.md:81` — "Style rules: `automation/style_rules.py` (single source of truth…)" | It is not a source of truth for anything at runtime. Zero consumers. The prompts are hand-typed elsewhere |
| `.claude/CONTEXT.md:81` — "+ `automation/check_rule_drift.py` (linter…)" | No Makefile, no CI job, no cron invokes it. Manual only |
| `SOFA-METHOD.md` — declares production has **not** migrated to Article Form | **Accurate.** Confirmed: no SOFA import in production |
| `LOGBOOK.md` AR3A entry — checked `style_rules.py` and `gate.py` for surviving copies of the removed testimony quota | Correct as far as it went; `llm.py`'s rewrite rules 33/33b were not checked and still carry it |
