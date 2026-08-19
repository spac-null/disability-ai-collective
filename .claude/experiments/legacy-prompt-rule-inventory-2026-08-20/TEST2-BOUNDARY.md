# Real Article Test 2 — Legacy Boundary

Date: 2026-08-20
Status: **OWNER DECISION RECORDED. TEST 2 NOT STARTED.**

This document defines what Test 2 must not inherit. It does **not** design Test 2, select
a story, or propose a replacement prompt.

---

## 1. The owner decision

> **REAL ARTICLE TEST 2 MUST NOT USE THE CURRENT LEGACY PRODUCTION WRITER PROMPT OR
> MASS-INJECTION SURFACE.**

Test 2 is **transfer validation** of the architecture developed through Sofa Method /
Article Form / Writer Grounding — does it transfer to a materially different story shape?

Intended path:

```
DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING
```

using the **clean manual/shadow architecture**, executed on the **local Claude
subscription** — not `automation/orchestrator/generate.py`'s writer prompt.

**Test 2 is NOT a production-path fidelity test.** Production migration happens later.

### Consequence

The **96 production-active rule families do not block Test 2.** They are excluded, not
fixed. This is deliberate: it prevents production cleanup from becoming another long
precondition before we learn whether Article Form transfers at all.

---

## 2. Excluded surfaces — Test 2 must NOT inherit any of these

Each row was inspected against the committed inventory. "Inspected → EXCLUDE" means the
task's §5 list was checked and the exclusion is affirmative, with the reason stated.

| # | Legacy surface | Location | Size / scope | Verdict | Reason |
|---|---|---|---|---|---|
| 1 | **The giant writer prompt** | `orchestrator/generate.py:783–1050` | 59,161 ch / 9,862 words / 75 rule units | **EXCLUDE** | The mass-injection surface itself. Its rule families predate and partly contradict SOFA §10 and Article Form |
| 2 | **Writer SYSTEM prompt** | `orchestrator/llm.py:232` | 3,212 ch | **EXCLUDE** | Contains "strong thesis from sentence one", which contradicts both the writer prompt and SOFA §12/§6. Would silently import contradiction C2 into Test 2 |
| 3 | **Duplicated persona canon blocks** | `_load_persona_canon` + `_load_persona_factual_context` fallback | 7,216 ch **×2** (Maya) | **EXCLUDE** | Double injection plus a self-contradicting authority framing (C3). Also superseded: `Byline ≠ prose persona` means Test 2's writer does not receive persona biography as voice material at all |
| 4 | **Old rewrite prompt rules** | `orchestrator/llm.py:394` `rewrite_with_opus` SYSTEM | 25,019 ch / 47 numbered rules | **EXCLUDE** | Second-largest legacy bundle. Carries the testimony quota (#5) and the unilateral UK-preference (WP-13). Test 2 has no whole-document rewrite stage |
| 5 | **Historical testimony quotas** | rewrite rules 33 + 33b | — | **EXCLUDE (hard)** | TV-02/TV-03. Directly contradicts AR3's finding and SOFA §7 "Not mandatory: human testimony… quotes… an interview subject". Inheriting these would invalidate Test 2's evidence stage |
| 6 | **Old style-rule bundles** | writer bullets, rewrite 1–47, `GATE_SYSTEM` R1–R17, `RULES_SYSTEM` R1–R19, `style_rules.py` registry | ~40 rule copies across 22 families | **EXCLUDE** | SOFA §10 is the writing standard for Test 2. Importing 4 divergent copies of the same 22 rules re-imports the drift the inventory just documented |
| 7 | **Prohibition-heavy legacy fragments** | writer prompt, GATE R15, REVIEW R16 | 80 negative tokens in the writer prompt alone | **EXCLUDE** | Edinburgh: negative Form instructions can surface as positive prose propositions. Several carry concrete nouns and verbatim bad sentences (FORBIDDEN DEFAULTS, TITLE RULES banned nouns, BLOCKED THEORISTS, quoted bad examples) |
| 8 | **Production gate/review R-number contracts** | `gate.py:233` + `_parse_rule_verdicts`; `review.py:1173` | R1–R17 / R1–R19, 9 collisions | **EXCLUDE** | Test 2 has no pre-commit gate. The identifiers are ambiguous across the two prompts (C-R-number), so any verdict parsing built on them would be unsound |
| 9 | **Persona-roleplay instructions** | `personas.py` `prompt_block`, `WRITE LIKE THIS PERSON`, `YOUR WOUND`, `YOUR LIFE`, `_PERSONA_CONFLICTS`, persona mutable state | 3,323–4,337 ch + canon | **EXCLUDE** | Superseded by SOFA §4: "The writer must not roleplay disability… insert biography as credential, or write 'in character' because the byline is a persona. **Byline ≠ prose persona.**" |
| 10 | **`_AGENT_BEATS` subject territories + beat nudge** | `config.py:258`, `discovery.py:464` | 4×4 beats | **EXCLUDE** | SOFA §2: "Do not treat any persona as owning a subject territory (mobility ≠ transportation stories…)" |
| 11 | **Legacy article types + registers + length buckets** | `config.py:115/131/140/183` | 9 forms, 6 registers, 6 length buckets, 4 indefensible | **EXCLUDE** | ARTICLE FORM (Edinburgh-calibrated) is Test 2's form owner. SOFA §9: no fixed word count, no required form elements |
| 12 | **Discovery anti-repetition nudges** | `discovery.py` DI-02…DI-10 | 10 injectors | **EXCLUDE** | Corpus-hygiene machinery for a daily publication cadence. Irrelevant to a single transfer-validation article, and it steers topic selection away from the story actually chosen |
| 13 | **Legacy planner brief prompt** | `llm.py::_fable_editorial_brief` | 15,358 ch | **EXCLUDE (partial)** | The *prompt* is excluded. Story Rejection **doctrine** (Layer 1 commissionability) is inherited — see §3 |

**Total excluded: 82 rule families across 13 surfaces.**

---

## 3. What Test 2 DOES inherit

Test 2 starts from the **existing frozen** architecture. No replacement prompt is invented
in this task.

| Stage | Owner | Source of truth | State |
|---|---|---|---|
| DISCOVERY | **SOFA METHOD** §1–3, §7, §8 | `.claude/SOFA-METHOD.md` (ratified 2026-08-19) | CANONICAL |
| — commissionability | **STORY REJECTION** doctrine | Layer 1 commission/decline logic, applied manually | doctrine only, not the prompt |
| — lens/writer separation | **PRF1** + `assert_no_persona_leakage` | `sofa_discovery_shadow.py:619` | available, recommended |
| ARTICLE FORM | **ARTICLE FORM** | Edinburgh-calibrated, frozen | CALIBRATED |
| WRITER | **SOFA METHOD** §6, §9–§12 | `.claude/SOFA-METHOD.md` | CANONICAL |
| WRITER GROUNDING | **WRITER GROUNDING** | `.claude/experiments/writer-grounding-*` V6 / final shadow | **SHADOW-CALIBRATED CANDIDATE** — frozen, owner stop in force |
| BYLINE | **PRF1** | `Byline ≠ prose persona` (SOFA §4) | CANONICAL |

**Execution:** local Claude subscription, manual/shadow path.
**Not** `production_orchestrator.py`, not CLIProxy, not the Hermes/Nous session path.

---

## 4. Standing constraints carried into Test 2

These are not legacy baggage; they are the current architecture's own limits and must be
restated so Test 2 does not silently overclaim.

- Writer Grounding is **SHADOW-CALIBRATED CANDIDATE**, not production-validated and not
  transfer-validated. Test 2 is what tests the transfer claim; it does not retroactively
  validate the calibration.
- Accepted known limitation, unchanged: source-relative LLM detection is stochastic, and
  a finite gold benchmark cannot prove every possible unsupported proposition in an
  article has been enumerated. **This does not reopen calibration.**
- Article Form is Edinburgh-calibrated on one story shape. Test 2 exists precisely because
  transfer to a materially different shape is unproven.
- No production code path is exercised, so Test 2 says nothing about production fidelity.

---

## 5. What this decision explicitly does NOT mean

- It does **not** mean production has been cleaned. It has not. 96 rule families remain
  active on every live article run.
- It does **not** mean the excluded surfaces are safe. Four items are classified
  `MUST_FIX_BEFORE_PRODUCTION_MIGRATION` (see `OWNER-TRIAGE.md`).
- It does **not** authorize deleting any excluded surface. Exclusion from Test 2 is a
  routing decision, not a cleanup decision.
- It does **not** start Test 2.

---

## 6. Phase boundary

```
DONE   Sofa method calibration
DONE   Edinburgh Article Form calibration
DONE   Writer Grounding shadow calibration
DONE   Legacy Prompt / Rule Inventory            (commit 38c47b8)
NOW    Owner triage / Test-2 boundary            (this document)
NEXT   REAL ARTICLE TEST 2 — transfer validation on a materially different story shape,
       clean Article Form + Writer Grounding path, local Claude subscription
AFTER  Production architecture / legacy prompt cleanup planning
THEN   Production migration + fidelity testing
```

**Production prompt cleanup does not happen before Test 2**, because no legacy surface is
required by Test 2 — all 13 are excluded above.
