# Owner Triage — Sequencing, Not Cleanup

Date: 2026-08-20
Source: this directory's `MASTER-INVENTORY.md` (114 rule families). **No new discovery
pass was performed.** Every row below is triaged from the already-committed inventory.

**This document authorizes nothing.** It assigns each family a *next-action bucket* so
that Real Article Test 2 can proceed without waiting on production cleanup.

## Buckets

| Bucket | Meaning |
|---|---|
| `KEEP_CURRENTLY` | Leave exactly as-is. No action before or after Test 2 |
| `EXCLUDE_FROM_TEST2` | Must not be inherited by Test 2's path |
| `MUST_FIX_BEFORE_PRODUCTION_MIGRATION` | Blocks migrating the clean architecture into production. Does **not** block Test 2 |
| `CONSOLIDATE_BEFORE_PRODUCTION` | Duplication/divergence to resolve during production cleanup |
| `RETIRE_AFTER_VERIFICATION` | Evidence says dead or superseded; remove only after confirming no consumer |
| `PRESERVE_HISTORICAL_ONLY` | Keep as record, never as a live input |
| `OWNER_DECISION_LATER` | Genuine artistic/architectural choice, deferred past transfer validation |

---

## Bucket totals (114 families)

| Bucket | Families |
|---|---|
| `EXCLUDE_FROM_TEST2` | 82 |
| `CONSOLIDATE_BEFORE_PRODUCTION` | 24 |
| `MUST_FIX_BEFORE_PRODUCTION_MIGRATION` | 4 |
| `KEEP_CURRENTLY` | 21 |
| `OWNER_DECISION_LATER` | 11 |
| `RETIRE_AFTER_VERIFICATION` | 6 |
| `PRESERVE_HISTORICAL_ONLY` | 12 |

Buckets overlap by design: a family can be both `EXCLUDE_FROM_TEST2` (now) and
`CONSOLIDATE_BEFORE_PRODUCTION` (later). The **primary** bucket is the leftmost one that
applies in the order the table above lists them.

---

## I. Style / prose rules — SR-01 … SR-22

| ID | Family | Primary bucket | Also | Note |
|---|---|---|---|---|
| SR-01…SR-08 | JARGON, NOMINALIZATION, SYSTEM VOICE, VAGUE WE, FRONT-LOADED, LONG LIST, PARAGRAPH LENGTH, SECTION BREAKS | `EXCLUDE_FROM_TEST2` | `CONSOLIDATE_BEFORE_PRODUCTION` | 5 copies each. SOFA §10 owns the writing standard for Test 2 |
| SR-07 | PARAGRAPH LENGTH specifically | `EXCLUDE_FROM_TEST2` | `OWNER_DECISION_LATER` | Contradicts SOFA §10 "developed paragraphs" via a **blocking** gate. Artistic decision |
| SR-09, SR-10, SR-13, SR-18, SR-19 | NAMED REFERENCES, NO DECODING, ENDING SHAPE, META-LANGUAGE, STACKED TEMPORAL | `EXCLUDE_FROM_TEST2` | `CONSOLIDATE_BEFORE_PRODUCTION` | SR-13 verified consistent across its 4 copies |
| SR-11 | CRAFTED RHETORIC | `EXCLUDE_FROM_TEST2` | `CONSOLIDATE_BEFORE_PRODUCTION` | Priority: exemption text diverges across 3 copies. Highest drift risk |
| SR-12 | ONE IDEA PER SENTENCE | `EXCLUDE_FROM_TEST2` | `CONSOLIDATE_BEFORE_PRODUCTION` | Carries a verbatim published bad sentence |
| SR-14, SR-15, SR-16 | INLINE DEFINITIONS, PLAIN VOCABULARY, ONE MODIFIER | `EXCLUDE_FROM_TEST2` | `CONSOLIDATE_BEFORE_PRODUCTION` | Live in 4 places, **absent from the registry** — registry is incomplete as well as unwired |
| SR-17 | SUBJECT-VERB DISTANCE | `KEEP_CURRENTLY` | | Deliberately check-only, never in the writer prompt. Correct design |
| SR-20, SR-21, SR-22 | LATINATE/CULTURAL-STUDIES wordlists, RHYTHMIC MONOTONY, LONG SENTENCE | `KEEP_CURRENTLY` | | Gate-only, no duplication |

## II. Ownerless writer-prompt rules — WP-01 … WP-35

All 35 are `EXCLUDE_FROM_TEST2` (they exist only inside the legacy writer prompt Test 2
does not use). Secondary buckets:

| ID | Family | Also | Note |
|---|---|---|---|
| WP-01 | BREGMAN WRITING MODEL | `OWNER_DECISION_LATER` | SOFA §10 now states the writing standard in its own terms. Keeping both = two voice models |
| WP-02 | `'ARGUMENT'` NEAR-ZERO | `OWNER_DECISION_LATER` | Carries a stale corpus statistic (63/138 of a corpus that has grown) |
| WP-03 | ANTI-SYSTEMIC TEST | `RETIRE_AFTER_VERIFICATION` | Fully covered by SR-03, which is gate-checked |
| WP-04, WP-05 | DISCOVERY VOICE / SIGNPOST PHRASES vs NO SIGNPOSTING | `OWNER_DECISION_LATER` | One prescribes stock phrases, one forbids narration. Both unchecked |
| WP-06…WP-11 | craft heuristics (microscope/telescope, end-weight, momentum, landing, aphorism budget, arrival paragraph) | `CONSOLIDATE_BEFORE_PRODUCTION` | Coherent generative texture. **Assign WRITER as owner** rather than leaving ownerless |
| WP-12 | FORBIDDEN DEFAULTS | `OWNER_DECISION_LATER` | Highest-payload negative prohibition. May be unnecessary under disturbance-first discovery |
| WP-13 | US-AVOIDANCE / UK-PREFERENCE split | `MUST_FIX_BEFORE_PRODUCTION_MIGRATION` | The rewriter steers geography in a direction the writer is never told. A silent divergence, not a preference |
| WP-14 | TITLE RULES | `CONSOLIDATE_BEFORE_PRODUCTION` | Assign owner |
| WP-15, WP-16 | academic-jargon + corporate-cliché wordlists | `CONSOLIDATE_BEFORE_PRODUCTION` | Three separate forbidden-word lists (these two + gate R12) with no shared source |
| WP-17…WP-24, WP-27…WP-34 | remaining craft rules | `CONSOLIDATE_BEFORE_PRODUCTION` | Assign WRITER as owner; no content change proposed |
| WP-25 | AUTHOR RULE — BY not ABOUT | `KEEP_CURRENTLY` | The one legacy rule surviving intact into SOFA (§2/§4 restate it). Candidate for promotion to SOFA METHOD ownership |
| WP-26 | GROUNDING (argument lives in the body) | `CONSOLIDATE_BEFORE_PRODUCTION` | **Rename.** Name collides with Writer Grounding and means something entirely different. Real comprehension hazard |
| WP-35 | WRITE LIKE THIS PERSON / persona voice framing | `EXCLUDE_FROM_TEST2` | `OWNER_DECISION_LATER` | Governed by C4. Superseded for Test 2 by SOFA §4 `Byline ≠ prose persona` |

## III. Testimony — TV-01 … TV-05

| ID | Family | Primary bucket | Note |
|---|---|---|---|
| TV-01 | HUMAN TESTIMONY / NAMED VOICES — zero is valid | `KEEP_CURRENTLY` | Current canonical form (AR3A). Test 2 inherits the *principle* from SOFA §7, not this prompt text |
| TV-02 | rewrite 33 — 2-3 named people REQUIRED | **`MUST_FIX_BEFORE_PRODUCTION_MIGRATION`** | `EXCLUDE_FROM_TEST2`. See §A below |
| TV-03 | rewrite 33b — SOMEONE ELSE MUST SPEAK | **`MUST_FIX_BEFORE_PRODUCTION_MIGRATION`** | `EXCLUDE_FROM_TEST2`. See §A below |
| TV-04 | INSIDER WITNESS — protect if present, never install | `KEEP_CURRENTLY` | Correctly phrased |
| TV-05 | L2 testimony companion | `KEEP_CURRENTLY` | Parked, `L2_TESTIMONY_MODE=OFF` |

## IV. Grounding — GR-01 … GR-07

| ID | Family | Primary bucket | Note |
|---|---|---|---|
| GR-01…GR-06 | evidence packet, field schema, unsupported-specifics scans, fallback-summary authority, executor contracts, lineage | `KEEP_CURRENTLY` | Production grounding arm. Test 2 uses the **shadow** Writer Grounding candidate, not these |
| GR-07 | Writer Grounding V0–V6 arbitration | `KEEP_CURRENTLY` | **Owner stop in force.** Frozen as SHADOW-CALIBRATED CANDIDATE. Test 2's grounding stage starts here, unchanged |

## V. Story Rejection — ST-01 … ST-05

All five `KEEP_CURRENTLY`. ST-04's known FC2 finding (first commission false/permissive,
N=1, deliberately unpatched) is out of scope and not reopened. Test 2 inherits Story
Rejection as **doctrine** (does this source support a commission), applied manually.

## VI. Persona / byline — PB-01 … PB-11

| ID | Family | Primary bucket | Note |
|---|---|---|---|
| PB-01 | `AGENTS[*].prompt_block` | `EXCLUDE_FROM_TEST2` | Persona voice injection; superseded by `Byline ≠ prose persona` |
| PB-02 | persona canon files, **injected twice** | `EXCLUDE_FROM_TEST2` + **`CONSOLIDATE_BEFORE_PRODUCTION`** | See §B below |
| PB-03, PB-04 | provenance modes, PENDING VERIFICATION exclusion | `KEEP_CURRENTLY` | Sound design; the *fallback consequence* is the problem, not these |
| PB-05 | `_INDEFENSIBLE_PROMPTS` | `EXCLUDE_FROM_TEST2` | ARTICLE FORM owns form for Test 2 |
| PB-06 | `_AGENT_BEATS` persona subject territories | `EXCLUDE_FROM_TEST2` + `OWNER_DECISION_LATER` | Contradicts SOFA §2. Independently removable |
| PB-07…PB-10 | fault lines, cross-cite check, wound, mutable state | `EXCLUDE_FROM_TEST2` | Persona-roleplay machinery |
| PB-11 | `assert_no_persona_leakage` | `KEEP_CURRENTLY` | SOFA's own lens/writer separation guard. **Test 2 should use it** |

## VII. Article form / register / length — AF-01 … AF-05

| ID | Family | Primary bucket | Note |
|---|---|---|---|
| AF-01 | `_ARTICLE_TYPES` (9 legacy forms) | `EXCLUDE_FROM_TEST2` | Test 2 uses the Edinburgh-calibrated ARTICLE FORM, not these |
| AF-02 | `_REGISTERS` (6) | `EXCLUDE_FROM_TEST2` + `CONSOLIDATE_BEFORE_PRODUCTION` | Two independent register concepts (this + WP-30) shaping one piece |
| AF-03 | `_LENGTHS` (6 weighted buckets + caps) | `EXCLUDE_FROM_TEST2` + `OWNER_DECISION_LATER` | SOFA §9: no fixed word count |
| AF-04 | article-type compliance check + repair | `KEEP_CURRENTLY` | Known efficacy gap tracked separately |
| AF-05 | SOFA Article Form stage | `KEEP_CURRENTLY` | Frozen. **Test 2's form owner** |

## VIII. Discovery nudges — DI-01 … DI-14

| ID | Family | Primary bucket | Note |
|---|---|---|---|
| DI-01 | `_get_beat_nudge` | `EXCLUDE_FROM_TEST2` + `OWNER_DECISION_LATER` | Contradicts SOFA §2 |
| DI-02…DI-10 | scholar/theorist blocks, dates, shapes, calendar, claims, titles, themes, openings, cross-refs | `EXCLUDE_FROM_TEST2` + `CONSOLIDATE_BEFORE_PRODUCTION` | Anti-repetition machinery bolted onto the writer prompt. Assign DISCOVERY as owner |
| DI-11 | SOFA disturbance-first discovery | `KEEP_CURRENTLY` | **Test 2's discovery owner** |
| DI-12, DI-13 | CJ-1 v3, CJ-2 B2 probe scripts (~20 files in `automation/`) | `PRESERVE_HISTORICAL_ONLY` | Consider relocating under `.claude/experiments/` so `automation/` holds only live code |
| DI-14 | CJ-2 shadow hook | `KEEP_CURRENTLY` | Parked, `CJ2_INTEGRATION_MODE=OFF` |

## IX. Dead / unwired — DE-01 … DE-10

| ID | Family | Primary bucket | Note |
|---|---|---|---|
| DE-01, DE-02 | `style_rules.py` registry + renderers | `RETIRE_AFTER_VERIFICATION` | See §D below. **Do not wire it merely because it exists** |
| DE-03 | `check_rule_drift.py` | `RETIRE_AFTER_VERIFICATION` | No automated runner. Either give it one during production cleanup, or mark manual-only |
| DE-04 | `.claude/CONTEXT.md` "single source of truth" claim | `MUST_FIX_BEFORE_PRODUCTION_MIGRATION` | The claim is false today and is a live trap for the next session. **Corrected in this task** — see §9 |
| DE-05…DE-08 | `editorial-lens.md`, `MANIFESTO.md`, `PIPELINE.md`, `prose_audit.py`, `archive/` | `PRESERVE_HISTORICAL_ONLY` | |
| DE-09 | deleted mass-injection copies | `PRESERVE_HISTORICAL_ONLY` | Files already gone |
| DE-10 | unreachable CJ2 path constants | `KEEP_CURRENTLY` | Self-documented forward declarations, harmless |

---

## Production-critical debt (§6 of the task) — classified, not fixed

### A. AR3 / testimony contradiction — `MUST_FIX_BEFORE_PRODUCTION_MIGRATION`

`llm.py` `rewrite_with_opus` SYSTEM rules 33 and 33b still require/pressure a second
named person and a spoken quote, after AR3A removed the same requirement from the writer
prompt. `rewrite_with_opus` runs on every production article (`generate.py:1168`).

**Qualification required in canonical wording.** Any statement that "the testimony quota
was removed" is true of the *writer prompt* and false of the *pipeline*. AR3A's own
release note records checking `style_rules.py` and `gate.py`; `llm.py` was not checked.
The correct claim is: *removed from the writer, still active in the rewriter.*

Partial mitigation, stated so this is not overclaimed: rule 33b ends "do not invent a
quote; never attribute words to a real named person that were not in the draft", and
`_reject_if_unsupported_specifics` guards the rewrite output. The fabrication path is
partly blocked; the editorial pressure AR3 identified as causal is not removed.

**Not fixed in this task.** No runtime change made.

### B. Duplicated persona canon — `CONSOLIDATE_BEFORE_PRODUCTION`

7,216 chars injected twice, SHA-256 identical, for the 3 fictional personas — labelled
`YOUR CANON (WHO YOU ARE, IMMUTABLY)` and again `AUTHORIZED PERSONAL HISTORY`, with a
joining sentence stating the canon "does NOT authorize autobiographical facts" while
pointing at that same text as the authorized history. Pixel Nova is correct (the two
blocks legitimately differ). ~12% of the writer prompt, for 3 of 4 personas.

### C. R-number collisions — `MUST_FIX_BEFORE_PRODUCTION_MIGRATION`

9 rules carry different R identifiers in `GATE_SYSTEM` vs `RULES_SYSTEM` (R5 = SYSTEM
VOICE in one, VAGUE WE in the other), while `gate.py::_parse_rule_verdicts` /
`_missing_rule_ids` key on those identifiers. This is the exact bug class `style_rules.py`
was built to make structurally impossible, still live because the registry was never wired.

### D. `style_rules.py` — `RETIRE_AFTER_VERIFICATION`

Evidence: 16-rule registry, three renderings each, five render functions, **zero
consumers**. The only `from style_rules import ...` occurrence in the repo is inside that
module's own docstring USAGE example. Four hand-typed copies are the real behaviour.

Classified `RETIRE_AFTER_VERIFICATION`, not `DEAD`-and-delete, because during production
cleanup its canonical rule text (with worked exceptions and a shared exemptions list) is
the best-quality single source available for the consolidation work. Retire the *claim of
authority* now; decide the code's fate during cleanup. **Do not wire it merely because it
exists.**

### E. Mass-injected writer prompt — `EXCLUDE_FROM_TEST2` + `CONSOLIDATE_BEFORE_PRODUCTION`

59,161 chars / 9,862 words, 75 prescriptive rule units, assembled per run at
`generate.py:783–1050`. Not rewritten in this task and not to be rewritten before
transfer validation.

### F. Negative prohibition density — `PRODUCTION CLEANUP RISK`, not a Test-2 blocker

80 negative-prohibition tokens in the live writer prompt, concentrated in rules carrying
concrete nouns and verbatim bad-example sentences. Given Edinburgh's observation that
negative Form instructions can surface as positive prose propositions, this is a real
cleanup risk — but Test 2 does not inherit the surface, so it does not gate Test 2.

**This remains an observation about surface area, not a measured failure.** No experiment
was run and none is proposed.

---

## Migrated responsibilities — structural owners now exist

Where an old prompt rule duplicates a structural responsibility below, it is marked
**MIGRATED / REDUNDANT CANDIDATE**. None is deleted.

| Structural owner | Owns | Old prompt families now redundant |
|---|---|---|
| **SOFA METHOD** | editorial / artistic doctrine, writing standard, evidence hierarchy, stop conditions | WP-01 (Bregman model), WP-03, WP-25 (restated as §2/§4), SR-07's paragraph target |
| **ARTICLE FORM** | sequence, argumentative burden, reader path, arrival, ending | AF-01, AF-02, AF-03, PB-05, WP-11 (arrival), SR-13 (ending shape) |
| **WRITER GROUNDING** | sentence-level source fidelity | WP-19 partial, "NO INVENTED STATISTICS", rewrite 26 "NO INVENTED DATA", GR-03 |
| **STORY REJECTION** | whether a source is grounded enough to commission | ST-01…ST-04; supersedes ad-hoc "find an angle" pressure in the legacy planner |
| **PRF1 / persona-byline** | persona/byline boundaries, factual provenance | PB-03, PB-04; and it is what makes PB-01/PB-07…PB-10 roleplay machinery redundant for Test 2 |
| **Deterministic code** | fabrication, rewrite integrity, opening templates, contact claims | GR-01…GR-06, `rewrite_integrity.py`, `opening_template_detector.py`, `human_detail_provenance.py` |

**MIGRATED / REDUNDANT CANDIDATE count: 24 families.** All retained pending cleanup.

---

## Owner decisions still required — 11

Unchanged from `CLEANUP-RECOMMENDATIONS.md`; all are **deferred past transfer validation**
except #1, which is answered by this task (retire the authority claim, decide the code
later).

1. `style_rules.py`: wire in, or retire? → **answered: retire the claim now, decide code during cleanup**
2. `check_rule_drift.py`: give it a runner, or mark manual-only?
3. WP-01 Bregman writing model: keep alongside SOFA §10, or retire?
4. SR-07 / C6: developed paragraphs (SOFA §10) or the ≤5-sentence blocking gate?
5. AF-03 `_LENGTHS`: weighted word buckets vs SOFA §9's "no fixed word count"?
6. WP-13: adopt the rewriter's UK preference in the writer, or strip it from the rewriter?
7. PB-06 / DI-01 `_AGENT_BEATS`: keep persona subject territories against SOFA §2?
8. WP-12 FORBIDDEN DEFAULTS: still needed under a disturbance-first model?
9. WP-04/05: reconcile prescribed discovery-voice phrases with NO SIGNPOSTING?
10. WP-02: re-measure or generalise the `'ARGUMENT'` corpus statistic?
11. DI-12/DI-13: relocate ~20 retired probe scripts out of `automation/`?
