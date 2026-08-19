# Master Inventory

One row per rule family (not per sentence).

**VERIFIED COUNT: 114 rule families / rule sources.**

Counted mechanically from this file's own table rows (unique IDs), not estimated:

| Prefix | Category | Families |
|---|---|---|
| SR | Style / prose rules (the duplicated core) | 22 |
| WP | Writer-prompt rules with no architectural owner | 35 |
| TV | Testimony / named voices | 5 |
| GR | Grounding / evidence | 7 |
| ST | Story Rejection | 5 |
| PB | Persona / byline (PRF1) | 11 |
| AF | Article form / register / length | 5 |
| DI | Discovery / anti-repetition nudges | 14 |
| DE | Dead / unwired rule infrastructure | 10 |
| | **TOTAL** | **114** |

By execution surface:

| Surface | Families |
|---|---|
| PRODUCTION (active on every run) | 96 |
| HISTORICAL | 7 |
| SHADOW (gated OFF or unwired) | 6 |
| DEAD (no consumer) | 5 |
| **TOTAL** | **114** |

CORRECTION NOTE (2026-08-20): the first verbal summary of this audit reported
"98 rule families / 79 production / 8 shadow / 11 historical-dead". Those figures were
a miscount in the summary, not in this file. The tables below were always the evidence;
recounting them mechanically gives 114 / 96 / 6 / 7+5. Use the numbers above.

Columns: ID · RULE · ORIGINAL LOCATION · CURRENT LOCATION · ORIGIN · CURRENT CONSUMER ·
ACTIVE? · EXECUTION SURFACE · ARCHITECTURAL OWNER · STATUS · NOTES

Origin dates are recoverable only where a file, docstring, `added=` field, or LOGBOOK
entry records one. `?` means not recoverable without deeper git archaeology, which was
not performed.

---

## I. Style / prose rules — the duplicated core

All 16 registry rules carry an `added=` date from `style_rules.py`. All are live in
production **via hand-typed copies**, never via the registry.

| ID | RULE | ORIGINAL LOC | CURRENT LOC | ORIGIN | CONSUMER | ACTIVE | SURFACE | OWNER | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| SR-01 | JARGON — strip institutional vocabulary | `production_orchestrator.py` (pre-split) | writer, rewrite 28, GATE R10, REVIEW R13, registry `jargon` | 2026-08-04 | all 4 model calls | YES | PRODUCTION | WRITER (gen) + OTHER (gate) | **DUPLICATE ×5** |
| SR-02 | NOMINALIZATION — actions stay verbs | same | writer, rewrite 19, GATE R4, REVIEW R4, registry | 2026-08-01 | all 4 | YES | PRODUCTION | same | **DUPLICATE ×5** |
| SR-03 | SYSTEM VOICE — no bureaucratic passive | same | writer, rewrite 18, GATE R17, REVIEW R5, registry | 2026-08-09 | all 4 | YES | PRODUCTION | same | **DUPLICATE ×5** (number collision) |
| SR-04 | VAGUE WE — 'we' needs a referent | same | writer, rewrite 19b, GATE R5, REVIEW R6, registry | 2026-08-01 | all 4 | YES | PRODUCTION | same | **DUPLICATE ×5** (collision) |
| SR-05 | FRONT-LOADED SENTENCE | same | writer, rewrite 21, GATE R6, REVIEW R7, registry | 2026-08-01 | all 4 | YES | PRODUCTION | same | **DUPLICATE ×5** |
| SR-06 | LONG LIST / LISTS OF THREE (+payoff exception) | same | writer, rewrite 13, GATE R8, REVIEW R10, registry | 2026-08-04 | all 4 | YES | PRODUCTION | same | **DUPLICATE ×5** — exception text differs per copy |
| SR-07 | PARAGRAPH LENGTH ≤5 sentences | same | writer, rewrite 23, GATE R7, REVIEW R8, registry | 2026-08-01 | all 4 | YES | PRODUCTION | same | **DUPLICATE ×5 + CONTRADICTED** (C6) |
| SR-08 | SECTION BREAKS ≤3 `---` | same | writer, rewrite 18b, GATE R9, REVIEW R9, registry | 2026-08-01 | all 4 | YES | PRODUCTION | same | **DUPLICATE ×5** |
| SR-09 | NAMED REFERENCES — name + 1 sentence | same | writer, rewrite 20, REVIEW R12, registry | 2026-08-01 | 3 | YES | PRODUCTION | WRITER | DUPLICATE ×4 |
| SR-10 | NO DECODING REQUIRED | same | writer, rewrite 35b, REVIEW R14, registry | 2026-08-01 | 3 | YES | PRODUCTION | WRITER | DUPLICATE ×4 |
| SR-11 | CRAFTED RHETORIC (6 sub-devices + exemptions) | same | writer, GATE R15, REVIEW R16, registry | 2026-08-04 | 3 | YES | PRODUCTION | OTHER (gate) | **DUPLICATE ×4 — RISKY**, exemption text diverges |
| SR-12 | ONE IDEA PER SENTENCE | same | writer, GATE R16, REVIEW R17, registry | 2026-08-01 | 3 | YES | PRODUCTION | OTHER (gate) | DUPLICATE ×4 |
| SR-13 | ENDING — no house shape, 5 valid | same | writer, rewrite 7 + 25, REVIEW R11, registry | 2026-08-01 | 3 | YES | PRODUCTION | WRITER | DUPLICATE ×4 — **verified consistent** |
| SR-14 | INLINE PARENTHETICAL DEFINITIONS | same | writer, rewrite 16, GATE R1, REVIEW R1 | ? | 4 | YES | PRODUCTION | OTHER (gate) | DUPLICATE ×4, **absent from registry** |
| SR-15 | PLAIN VOCABULARY / LATINATE | same | writer ×2, rewrite 17, GATE R2, REVIEW R2 | ? | 4 | YES | PRODUCTION | WRITER | DUPLICATE ×5 incl. **twice inside one prompt** (C7) |
| SR-16 | ONE MODIFIER PER NOUN | same | writer, rewrite 12, GATE R3, REVIEW R3 | ? | 4 | YES | PRODUCTION | OTHER (gate) | DUPLICATE ×4, absent from registry |
| SR-17 | SUBJECT-VERB DISTANCE | ? | GATE R14, REVIEW R15, registry | 2026-08-01 | 2 | YES | PRODUCTION | OTHER (gate) | DUPLICATE ×3 — **not in writer prompt** (check-only) |
| SR-18 | META-LANGUAGE COMMENTARY | writer prompt | writer, REVIEW R18, registry | 2026-08-09 | 2 | YES | PRODUCTION | WRITER | DUPLICATE ×3 |
| SR-19 | STACKED TEMPORAL CLAUSES | writer prompt | writer, REVIEW R19, registry | 2026-08-09 | 2 | YES | PRODUCTION | WRITER | DUPLICATE ×3 |
| SR-20 | LATINATE CLUSTERS / CULTURAL STUDIES VOCAB wordlists | ? | GATE R2, R12 | ? | gate | YES | PRODUCTION | OTHER | ACTIVE |
| SR-21 | RHYTHMIC MONOTONY (+anaphora exception) | ? | GATE R13 | ? | gate | YES | PRODUCTION | OTHER | ACTIVE |
| SR-22 | LONG SENTENCE >30 words | ? | GATE R11 | ? | gate | YES | PRODUCTION | OTHER | ACTIVE |

## II. Writer-prompt rules with no architectural owner

| ID | RULE | CURRENT LOC | ORIGIN | ACTIVE | SURFACE | OWNER | STATUS |
|---|---|---|---|---|---|---|---|
| WP-01 | WRITING MODEL — RUTGER BREGMAN (process not residue) | writer + rewrite 27 | ~2026-08-07 (`bregman-*` analysis docs) | YES | PRODUCTION | **NONE** | ACTIVE — superseded in spirit by SOFA §10 |
| WP-02 | `'ARGUMENT'` — NEAR-ZERO (cites 63/138 corpus stat) | writer | 2026-08 corpus audit | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-03 | ANTI-SYSTEMIC TEST (read aloud / committee) | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE — overlaps SR-03 |
| WP-04 | DISCOVERY VOICE (stock realisation phrases) | writer + rewrite 24 | ? | YES | PRODUCTION | **NONE** | ACTIVE — tension with WP-05 |
| WP-05 | SIGNPOST PHRASES AT TRANSITIONS (prescribes) vs NO SIGNPOSTING (forbids) | writer, both | ? | YES | PRODUCTION | **NONE** | ACTIVE — internally uneasy pair |
| WP-06 | MICROSCOPE AND TELESCOPE | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE, unchecked |
| WP-07 | END-WEIGHT | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE, unchecked |
| WP-08 | PARAGRAPH MOMENTUM / LANDING | writer + rewrite 14,15 | ? | YES | PRODUCTION | **NONE** | ACTIVE, unchecked |
| WP-09 | ONE APHORISM, MAXIMUM | writer + rewrite 27,40 | ? | YES | PRODUCTION | **NONE** | ACTIVE — interacts with WP-10 ceiling |
| WP-10 | TRANSLATE ONE ABSTRACTION (+ rewrite 35c protect-one) | writer + rewrite 35c | ? | YES | PRODUCTION | **NONE** | ACTIVE — 35c is the longest single rule in the codebase |
| WP-11 | ARRIVAL PARAGRAPH — optional, costs the aphorism | writer + rewrite 40 | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-12 | FORBIDDEN DEFAULTS (ramp/curb cut/grab rail/…) | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE — negative, carries the banned nouns |
| WP-13 | US-AVOIDANCE (writer) / US-AVOIDANCE + **UK-PREFERENCE** (rewrite 32) | writer bullet, rewrite 32 | ? | YES | PRODUCTION | **NONE** | **DIVERGENT** — rewrite adds a geography preference the writer never sees |
| WP-14 | TITLE RULES — NON-NEGOTIABLE (6 bullets + recent titles) | writer, built in `generate.py:773` | ? | YES | PRODUCTION | **NONE** | ACTIVE, unchecked |
| WP-15 | FORBIDDEN ACADEMIC JARGON wordlist (17 terms) | writer | ? | YES | PRODUCTION | overlaps SR-01 | ACTIVE |
| WP-16 | FORBIDDEN CORPORATE/JOURNALESE CLICHÉS (9 terms) | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-17 | NO EMPTY GRANDEUR | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-18 | SHOW THEN NAME | writer + rewrite 34 | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-19 | TEMPORAL ANCHORS / PERSONAL ANECDOTE SPECIFICITY | writer + rewrite 29 | ? | YES | PRODUCTION | partial: grounding | ACTIVE |
| WP-20 | HISTORICAL/BIOGRAPHICAL ANECDOTE TEST | writer | 2026-08-17 (AR3 kept it) | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-21 | FIND SOMETHING OUT — NON-NEGOTIABLE | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-22 | DO NOT MANAGE THE READER | writer + rewrite 27(a) | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-23 | NO ENCYCLOPEDIC APPOSITIVES | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-24 | HUMAN THREAD — NON-NEGOTIABLE | writer + rewrite 36 (ANALYTICAL WALL) | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-25 | AUTHOR RULE — BY not ABOUT | writer + rewrite 10b + `llm.py:232` SYSTEM | early | YES | PRODUCTION | SOFA METHOD (§2/§4 restate it) | ACTIVE — closest thing to a canonical rule surviving intact |
| WP-26 | GROUNDING — argument lives in the body | writer + rewrite 31 | ? | YES | PRODUCTION | **NONE** | ACTIVE — *not* Writer Grounding; unrelated |
| WP-27 | NO HEDGING AGAINST NOBODY | writer + rewrite 30 | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-28 | READER ADDRESS / voice the objection | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-29 | TRANSLATE LARGE NUMBERS TO HUMAN SCALE | writer | ? | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-30 | REGISTER — smart person explaining to a friend | writer + rewrite 11 | ? | YES | PRODUCTION | overlaps `_REGISTERS` | ACTIVE |
| WP-31 | SENTENCE LENGTH / no chained comma-clauses | writer + rewrite 5 | ? | YES | PRODUCTION | overlaps GATE R11 | ACTIVE |
| WP-32 | REPLACE THE METAPHOR URGE WITH ACCUMULATION | writer | 2026-08 Bregman pass | YES | PRODUCTION | overlaps SR-11 | ACTIVE |
| WP-33 | RHETORICAL QUESTIONS — two patterns | writer | 2026-08 Bregman pass | YES | PRODUCTION | **NONE** | ACTIVE |
| WP-34 | A PLAIN LIST CAN REPEAT VERBATIM AS A REFRAIN | writer | 2026-08 Bregman pass | YES | PRODUCTION | carve-out to SR-11 | ACTIVE |
| WP-35 | WRITE LIKE THIS PERSON / persona voice framing | writer opening | early | YES | PRODUCTION | PERSONA/BYLINE | **CONTRADICTED** by SOFA §4 (C4, documented divergence) |

## III. Testimony / named voices

| ID | RULE | CURRENT LOC | ORIGIN | ACTIVE | SURFACE | OWNER | STATUS |
|---|---|---|---|---|---|---|---|
| TV-01 | HUMAN TESTIMONY / NAMED VOICES — zero is valid | `generate.py:882` | 2026-08-17 AR3A (`3225ea1`) | YES | PRODUCTION | WRITER | **ACTIVE — current canonical form** |
| TV-02 | `NAMED VOICES: 2-3 real named people … REQUIRED` | **`llm.py` rewrite rule 33** | pre-AR3 | **YES** | PRODUCTION | none — retired in writer | **CONTRADICTED / SHOULD HAVE MIGRATED — C1** |
| TV-03 | `SOMEONE ELSE MUST SPEAK` (quote in quotation marks required) | **`llm.py` rewrite rule 33b** | pre-AR3 | **YES** | PRODUCTION | none | **CONTRADICTED / SHOULD HAVE MIGRATED — C1** |
| TV-04 | INSIDER WITNESS — protect if present, never invent | rewrite 35 | ? | YES | PRODUCTION | **NONE** | ACTIVE — correctly phrased (protect-not-install) |
| TV-05 | L2 testimony companion sourcing | `testimony_l2.py` | 2026-08-14 (`l2-testimony-design`) | NO | SHADOW | WRITER | PARKED (`L2_TESTIMONY_MODE=OFF`) |

## IV. Grounding / evidence

| ID | RULE | CURRENT LOC | ORIGIN | ACTIVE | SURFACE | OWNER | STATUS |
|---|---|---|---|---|---|---|---|
| GR-01 | Evidence packet + source hash / truncation honesty | `grounding.py:build_evidence_packet` | Phase 1.6, 2026-08-11 | YES | PRODUCTION | WRITER GROUNDING (production arm) | ACTIVE |
| GR-02 | Evidence-candidate field schema + `status=not_found` | `grounding.py:validate_evidence_field` | Phase 1.6 | YES | PRODUCTION | STORY REJECTION / WRITER | ACTIVE |
| GR-03 | `find_new_unsupported_specifics` — reject new specifics in a rewrite | `grounding.py` | Phase 1.6 | YES | PRODUCTION | WRITER GROUNDING | ACTIVE |
| GR-04 | Fallback-summary is NOT source authority | writer prompt + planner `NO SOURCE TEXT` block | Phase 1.6 | YES | PRODUCTION | WRITER GROUNDING | ACTIVE |
| GR-05 | `_EXECUTOR_CONTRACT` + persona-history contract | `llm.py:61`, `:101` | Phase 1.6 | YES | PRODUCTION | WRITER GROUNDING | ACTIVE |
| GR-06 | Evidence lineage containment checks | `generate.py` `_writer_evidence_entry` | Phase 1.6 | YES | PRODUCTION | WRITER GROUNDING | ACTIVE |
| GR-07 | Source-relative unsupported-proposition arbitration (V0–V6) | `.claude/experiments/writer-grounding-*` | 2026-08-19 | NO | SHADOW | WRITER GROUNDING | **PARKED — owner stop in force** |

## V. Story Rejection

| ID | RULE | CURRENT LOC | ORIGIN | ACTIVE | SURFACE | OWNER | STATUS |
|---|---|---|---|---|---|---|---|
| ST-01 | LAYER 1 commissionability — commission / decline | `llm.py::_fable_editorial_brief` `_layer1_block` | V1 released 2026-08-17 | YES | PRODUCTION | STORY REJECTION | ACTIVE |
| ST-02 | Decline ≠ persona unavailability; never decline on insufficient evidence | same | V1 | YES | PRODUCTION | STORY REJECTION | ACTIVE |
| ST-03 | `validate_source_decision` + contract version + decline persistence | `grounding.py`, `discovery.py:1443` | V1 / V1.1 | YES | PRODUCTION | STORY REJECTION | ACTIVE |
| ST-04 | Commission path grounding verification | `_validate_commission_grounding`, `_verify_commission_mechanism_support` | V1.1 | YES | PRODUCTION | STORY REJECTION | ACTIVE — memory records first commission was FC2 (false/permissive), N=1, deliberately unpatched |
| ST-05 | LAYER 2 eligible-persona constraint (PRF1 rotation) | `_eligible_constraint` | PRF1 | YES | PRODUCTION | PERSONA/BYLINE | ACTIVE |

## VI. Persona / byline (PRF1)

| ID | RULE | CURRENT LOC | ORIGIN | ACTIVE | SURFACE | OWNER | STATUS |
|---|---|---|---|---|---|---|---|
| PB-01 | `AGENTS[*].prompt_block` — 4 persona voice blocks | `personas.py:15` | early | YES | PRODUCTION | PERSONA/BYLINE | ACTIVE |
| PB-02 | `persona_canon/*.md` — 5 canon files | `automation/persona_canon/` | 2026-06 / 2026-08 | YES | PRODUCTION | PERSONA/BYLINE | **ACTIVE — injected twice per prompt (C3)** |
| PB-03 | Two provenance modes (real-person-evidence vs editorial-canon) | `llm.py:589` | 2026-08-14 | YES | PRODUCTION | PERSONA/BYLINE | ACTIVE |
| PB-04 | `## PENDING VERIFICATION` structurally excluded | same | 2026-08-14 | YES | PRODUCTION | PERSONA/BYLINE | ACTIVE |
| PB-05 | `_INDEFENSIBLE_PROMPTS` — 4 persona-specific forms | `config.py:183` | ? | YES | PRODUCTION | ARTICLE FORM | ACTIVE |
| PB-06 | `_AGENT_BEATS` — persona subject territories | `config.py:258` | early | YES | PRODUCTION | none | **CONTRADICTED by SOFA §2 (C5)** |
| PB-07 | `_PERSONA_CONFLICTS` / fault lines | `config.py:274` | ? | YES | PRODUCTION | PERSONA/BYLINE | ACTIVE |
| PB-08 | Persona cross-cite accuracy check | `fact_check.py` | ? | YES | PRODUCTION | PERSONA/BYLINE | ACTIVE |
| PB-09 | `YOUR WOUND` extraction | `llm.py:580` | early | YES | PRODUCTION | PERSONA/BYLINE | ACTIVE |
| PB-10 | Persona mutable state (obsessions/arguments/mood) | `persona_state/` | early | YES | PRODUCTION | PERSONA/BYLINE | ACTIVE |
| PB-11 | `assert_no_persona_leakage` (SOFA lens/writer separation) | `sofa_discovery_shadow.py:619` | 2026-08-18 | NO | SHADOW | SOFA METHOD | PARKED |

## VII. Article form / register / length

| ID | RULE | CURRENT LOC | ORIGIN | ACTIVE | SURFACE | OWNER | STATUS |
|---|---|---|---|---|---|---|---|
| AF-01 | `_ARTICLE_TYPES` — 9 weighted forms | `config.py:140` | ? | YES | PRODUCTION | ARTICLE FORM | ACTIVE |
| AF-02 | `_REGISTERS` — 6 weighted registers | `config.py:115` | ? | YES | PRODUCTION | ARTICLE FORM | ACTIVE — overlaps WP-30 |
| AF-03 | `_LENGTHS` — 6 weighted word buckets | `config.py:131` | 2026-08-04 | YES | PRODUCTION | ARTICLE FORM | ACTIVE — **tension with SOFA §9 "no fixed word count"** |
| AF-04 | Article-type compliance check + repair | `gate.py:27,51,530` | ? | YES | PRODUCTION | ARTICLE FORM | ACTIVE — known efficacy gap on record |
| AF-05 | SOFA Article Form stage | `SOFA-METHOD.md` §9 | 2026-08-19 | NO | SHADOW | SOFA METHOD | PARKED |

## VIII. Discovery / anti-repetition nudges

| ID | RULE | CURRENT LOC | ACTIVE | SURFACE | OWNER | STATUS |
|---|---|---|---|---|---|---|
| DI-01 | `_get_beat_nudge` | `discovery.py:464` | YES | PRODUCTION | none | ACTIVE — see C5 |
| DI-02 | `_get_scholar_nudge` / `_get_blocked_theorists` | `discovery.py:737,854` | YES | PRODUCTION | none | ACTIVE |
| DI-03 | `_get_recent_dates_nudge` | `discovery.py:442` | YES | PRODUCTION | none | ACTIVE |
| DI-04 | `_get_shape_nudge` / `_STRUCTURAL_SHAPES` | `discovery.py:699` | YES | PRODUCTION | none | ACTIVE |
| DI-05 | `_get_calendar_event_nudge` | `discovery.py:791` | YES | PRODUCTION | none | ACTIVE |
| DI-06 | `_get_claims_nudge` | `discovery.py:812` | YES | PRODUCTION | none | ACTIVE |
| DI-07 | `_get_recent_title_patterns` / `_check_title_freshness` | `discovery.py:891,271` | YES | PRODUCTION | none | ACTIVE |
| DI-08 | `_get_overused_themes` / `_THEME_CLUSTERS` | `discovery.py:618` | YES | PRODUCTION | none | ACTIVE |
| DI-09 | `_get_recent_openings` (planner) | `discovery.py:907` | YES | PRODUCTION | none | ACTIVE |
| DI-10 | `_get_cross_reference` / `_should_cross_reference` | `discovery.py:936,961` | YES | PRODUCTION | none | ACTIVE |
| DI-11 | SOFA disturbance-first discovery | `SOFA-METHOD.md` §1–3, `sofa_discovery_shadow.py` | NO | SHADOW | SOFA METHOD | PARKED |
| DI-12 | CJ-1 v3 source friction gate (3 prompt versions) | `automation/cj1_v3_*.py` | NO | HISTORICAL | DISCOVERY | HISTORICAL |
| DI-13 | CJ-2 B2 competitive reframing (~15 probe files) | `automation/cj2_b2_*.py` | NO | HISTORICAL | DISCOVERY | HISTORICAL |
| DI-14 | CJ-2 shadow integration hook | `orchestrator/cj2_shadow.py` | NO | SHADOW | DISCOVERY | PARKED (`CJ2_INTEGRATION_MODE=OFF`) |

## IX. Dead / unwired rule infrastructure

| ID | ITEM | LOCATION | CONSUMER | ACTIVE | SURFACE | STATUS |
|---|---|---|---|---|---|---|
| DE-01 | `style_rules.py` RULES registry (16 rules, 3 renderings each) | `automation/style_rules.py` | **none** | NO | DEAD | **DEAD** — never wired; four hand-typed copies are the real behaviour |
| DE-02 | `render_gate()` / `render_review()` / `render_writer_bullet()` / `render_rewrite()` / `render_docs()` | same | **none** | NO | DEAD | **DEAD** |
| DE-03 | `check_rule_drift.py` drift linter | `automation/check_rule_drift.py` | no CI / cron / Makefile | NO (automated) | DEAD-ish | **DEAD as a gate**, usable manually |
| DE-04 | `.claude/CONTEXT.md:81` claim that `style_rules.py` is the single source of truth | doc | — | — | DEAD | **CONTRADICTED by code** |
| DE-05 | `editorial-lens.md` | repo root | `prose_audit.py` only | NO | HISTORICAL | HISTORICAL |
| DE-06 | `MANIFESTO.md` / `PIPELINE.md` | repo root | Jekyll-excluded; `prose_audit.py`, `archive/ethical_research_bot.py` | NO | HISTORICAL | PRESERVE_HISTORICAL_ONLY |
| DE-07 | `prose_audit.py` | repo root | no runner | NO | DEAD | HISTORICAL |
| DE-08 | `archive/` scripts (6 files) | `archive/` | none | NO | HISTORICAL | PRESERVE_HISTORICAL_ONLY |
| DE-09 | Historical mass-injected copies in `opus_rewrite.py` + root `production_orchestrator.py` | deleted | — | NO | HISTORICAL | **DEAD (files removed)** |
| DE-10 | `PATH_CJ2_WINNER_DRAFT` / `PATH_CJ2_PRODUCTION` constants | `cj2_shadow.py:41-42` | none | NO | DEAD | DEAD — self-documented as unreachable |
