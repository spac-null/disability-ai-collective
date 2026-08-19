# Migration Map — Rule vs Structure

For every legacy rule family: **is this responsibility now enforced structurally
elsewhere?** If yes, the old prompt copy is a candidate for retirement regardless of
whether it still reads sensibly.

Architectural owners: **SOFA METHOD** · **DISCOVERY** · **ARTICLE FORM** · **WRITER** ·
**WRITER GROUNDING** · **STORY REJECTION** · **PERSONA/BYLINE (PRF1)** · **OTHER** · **NONE**

---

## A. Responsibility genuinely migrated to structure — old prompt copy now redundant

| Legacy rule | Old home | Structural owner now | Evidence | Status |
|---|---|---|---|---|
| "Do not invent facts / statistics / quotes" | writer prompt `NO INVENTED STATISTICS`, rewrite 26 `NO INVENTED DATA` | **Deterministic grounding** — `grounding.py`: `validate_evidence_field`, `scan_free_prose_field`, `find_new_unsupported_specifics`, `scan_draft_for_unsupported_specifics` | code-enforced on the executor path, `_reject_if_unsupported_specifics` rejects rewrites introducing new specifics | **MIGRATED** (prompt copy now belt-and-braces, not load-bearing) |
| "Never invent a persona memory / meeting / trip" | writer `PERSONA HISTORY`, `AUTHORIZED PERSONAL HISTORY` block | **PERSONA/BYLINE (PRF1)** — `build_persona_factual_context`, `_load_persona_factual_context` provenance modes, `find_new_unsupported_personal_history` | two provenance modes; PENDING VERIFICATION text structurally excluded | **MIGRATED** |
| "Is this source worth writing at all" | implicit in the old writer/planner prompt | **STORY REJECTION** — `validate_source_decision`, `STORY_REJECTION_CONTRACT_VERSION`, `_handle_declined_run` / `_handle_defer_run` / `_handle_no_execution_run` | Layer 1 commission/decline/defer, persisted with contract version | **MIGRATED** |
| Testimony quota ("2-3 named people REQUIRED", "someone else must speak") | writer prompt | **retired by AR3 decision** — no structural replacement, deliberately: zero testimony is valid | `generate.py:882` | **SUPERSEDED in writer / STILL ACTIVE in rewriter — see C1** |
| Truncated / duplicated / structurally broken output | rewrite rule 37, gate prose checks | **OTHER (deterministic)** — `rewrite_integrity.py`, `_check_truncated_ending_shadow`, `find_duplicated_block` | | **MIGRATED** |
| Opening-template repetition | writer `OPENING — NO FIXED SHAPE`, planner openings block | **OTHER (deterministic)** — `opening_template_detector.py` (`find_template_match`, shingling) | | **MIGRATED** (prompt copy still useful as generative instruction) |
| Article-type / form adherence | writer `FORM:` line | **ARTICLE FORM** — `config.py:_ARTICLE_TYPES` + `gate.py:_check_article_type_compliance` + `SUBJECT_SYSTEM` + form `FIX_SYSTEM` | | **MIGRATED** (but see known gap below) |
| Personal contact-detail claims | none explicit | **OTHER** — `human_detail_provenance.py` | | **MIGRATED** |

## B. Responsibility that has an architectural owner *on paper* but no production wiring

| Rule family | Nominal owner | Reality | Status |
|---|---|---|---|
| All 16 style rules in `style_rules.py` | itself, "single source of truth" | zero consumers; four hand-typed copies remain the real behaviour | **NOT MIGRATED — the migration was designed and abandoned mid-way** |
| Source-relative unsupported-proposition detection in finished prose | **WRITER GROUNDING** | shadow-calibrated candidate, lives only in `.claude/experiments/writer-grounding-*`, no production import | **PARKED** (owner-declared; do not reopen) |
| Discovery → Article Form → Writer staging, persona-leakage prevention | **SOFA METHOD** | `sofa_discovery_shadow.py` exists (65 KB) but is imported by **no** production module | **PARKED** |
| CJ-1 source friction gate | DISCOVERY | probe scripts only | **HISTORICAL** |
| CJ-2 competitive reframing | DISCOVERY / WRITER | `cj2_shadow.py` gated `OFF`; `PRODUCTION_AUTHORITY` mode does not exist | **PARKED** |
| L2 testimony companion | WRITER | gated `OFF`, explicitly kept shadow | **PARKED** |

## C. Rules with NO architectural owner — pure legacy prompt text still steering output

These are the ones that most deserve an owner decision. Each is live, each shapes prose,
none is claimed by SOFA METHOD, ARTICLE FORM, WRITER GROUNDING, STORY REJECTION or PRF1.

| Rule | Where | Why it has no owner |
|---|---|---|
| `WRITING MODEL — RUTGER BREGMAN` (writer + rewrite 27) | writer prompt, rewrite | An imported external voice model. SOFA §10 defines the writing standard now, in its own terms, without naming Bregman |
| `'ARGUMENT' — NEAR-ZERO` | writer prompt | A one-off corpus-statistics reaction (2026-08 word-frequency audit), never generalised into a rule family |
| `ANTI-SYSTEMIC TEST` ("read it aloud, committees don't get irritated") | writer prompt | Overlaps SYSTEM VOICE, which *is* owned and gate-checked |
| `DISCOVERY VOICE` + `SIGNPOST PHRASES AT TRANSITIONS` | writer, rewrite 24 | Prescribes specific stock phrases ("it turns out…", "Now comes the strange part.") — arguably in tension with SOFA §10 "avoid repeated paraphrases" and with `NO SIGNPOSTING` in the same prompt |
| `MICROSCOPE AND TELESCOPE`, `END-WEIGHT`, `PARAGRAPH MOMENTUM`, `LANDING` | writer, rewrite | Craft heuristics with no check anywhere and no owner |
| `ONE APHORISM, MAXIMUM` / `ARRIVAL PARAGRAPH` | writer, rewrite 40 | Budget rules interacting with `TRANSLATE ONE ABSTRACTION`'s own ceiling; no check |
| `FORBIDDEN DEFAULTS` (ramp/curb cut/…) | writer prompt | A 2026-era anti-cliché patch; SOFA's disturbance-first model addresses the same failure differently |
| `US-AVOIDANCE + UK-PREFERENCE` | writer bullet, rewrite 32 | Geographic policy. Rewrite 32 adds a **UK preference** the writer prompt does not state — the writer is told only "not the US" |
| `BLOCKED THEORISTS` / `_AGENT_BEATS` / `_THEME_CLUSTERS` / title-freshness | `discovery.py` nudges | Anti-repetition machinery; overlaps DISCOVERY conceptually but predates it and is not part of it |
| `TITLE RULES — NON-NEGOTIABLE` | writer prompt | No owner; no check |
| `_REGISTERS` (6) + `STARTING REGISTER` | `config.py` + writer | Predates ARTICLE FORM; register and form are two independent selectors both shaping the same piece |

## D. Known gap already on record (not a new finding)

`.claude` memory records an open **article-type compliance gap**: field_note/portrait are
selected correctly but outputs ignore the form's rules. This inventory confirms the
enforcement path *exists* (`_check_article_type_compliance` + `SUBJECT_SYSTEM` +
form `FIX_SYSTEM`), so the gap is about efficacy, not absence. Not investigated further —
out of scope for an inventory.

---

## Summary

| Bucket | Families |
|---|---|
| **MIGRATED** — structural owner now enforces it | 8 |
| **PARKED** — owner exists but is shadow/unwired | 6 |
| **NOT MIGRATED** — consolidation designed then abandoned | 1 (the 16-rule registry, affecting 19 duplicated families) |
| **NO OWNER** — pure legacy prompt text, live | 11 |
