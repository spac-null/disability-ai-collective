# Cleanup Recommendations

**NOTHING IN THIS FILE HAS BEEN EXECUTED.** No rule was deleted, moved, rewritten, or
disabled. This is a proposal for owner review.

The goal is not shorter prompts. The goal is: every surviving instruction has one
architectural owner, one justified purpose, no contradiction, no unnecessary duplication.

Recommendation vocabulary: **KEEP · MIGRATE · CONSOLIDATE · RETIRE · DELETE_AFTER_VERIFICATION · PRESERVE_HISTORICAL_ONLY · OWNER_DECISION**

---

## Top 10 cleanup candidates, ranked by risk × cheapness

| # | Candidate | Recommendation | Why it ranks here |
|---|---|---|---|
| 1 | **Rewrite rules 33 + 33b — testimony quota** (`llm.py`) | **RETIRE** — replace with TV-01's text, exactly as AR3A did for the writer | Live contradiction with a decision already taken and tested. Smallest possible diff. The AR3 experiment already produced the replacement wording |
| 2 | **Persona canon double-injection** (C3) | **DELETE_AFTER_VERIFICATION** — when `_persona_factual_text == _canon`, emit the block once and fix the joining sentence | Removes 7,216 chars (~12%) from the writer prompt for 3 of 4 personas and resolves a self-contradiction. Needs verification that the reviewer/executor lineage checks still find their substring |
| 3 | **`llm.py:232` SYSTEM "strong thesis from sentence one"** (C2) | **RETIRE** (already queued as AR3.1) | One clause. Contradicts the writer prompt in the same call |
| 4 | **`style_rules.py` + `check_rule_drift.py` status** (DE-01…DE-04) | **OWNER_DECISION** — either wire it in (the original plan) or mark it explicitly dead in the docstring and `.claude/CONTEXT.md` | Currently a live trap: it looks like the source of truth and is not. Leaving it ambiguous guarantees a future session edits the wrong file |
| 5 | **GATE/REVIEW R-number collisions** (9 rules) | **CONSOLIDATE** — one number scheme, or slug-keyed verdicts | `_parse_rule_verdicts` keys on numbers that mean different rules in the two prompts |
| 6 | **`PLAIN VOCABULARY` stated twice in one prompt** (C7) | **CONSOLIDATE** — merge to one bullet | Trivial, zero risk |
| 7 | **8 five-copy style families** (SR-01…SR-08) | **CONSOLIDATE** via #4's decision | ~40 copies of 8 rules. The cheapest structural win available, but only after the `style_rules.py` question is settled |
| 8 | **WP-13 UK-PREFERENCE divergence** | **OWNER_DECISION** | The rewriter steers geography in a direction the writer was never told about. Either is defensible; the split is not |
| 9 | **`_AGENT_BEATS` persona territories** (C5) | **OWNER_DECISION** | Directly contradicts SOFA §2. Independently removable without touching the persona architecture |
| 10 | **`CRAFTED RHETORIC` exemption drift** (SR-11) | **CONSOLIDATE** | The quoted-speech and `not X but Y` carve-outs are stated at three different lengths. This is exactly the class of drift that caused the 2026-08-09 incident |

---

## Per-family recommendations

### Style rules (SR-01 … SR-22)

| Family | Recommendation | Notes |
|---|---|---|
| SR-01…SR-08 (5 copies each) | **CONSOLIDATE** | Blocked on the `style_rules.py` owner decision (#4). Suggested end state: registry renders GATE + REVIEW + REWRITE text; writer keeps a short *imperative* rendering only |
| SR-09, SR-10, SR-13, SR-18, SR-19 | **CONSOLIDATE** | Same mechanism |
| SR-11 CRAFTED RHETORIC | **CONSOLIDATE (priority)** | Exemptions must be single-sourced |
| SR-12 ONE IDEA PER SENTENCE | **CONSOLIDATE** | Writer copy carries a full verbatim bad-example sentence; consider whether the judge copies need it too |
| SR-14, SR-15, SR-16 | **MIGRATE into the registry first** | Live in 4 places but absent from the registry — the registry is incomplete as well as unwired |
| SR-17 SUBJECT-VERB DISTANCE | **KEEP as check-only** | Deliberately absent from the writer prompt; that is correct design, document it |
| SR-20, SR-21, SR-22 | **KEEP** | Gate-only, no duplication |
| SR-07 PARAGRAPH LENGTH | **OWNER_DECISION** | C6: canonical method wants developed paragraphs, a blocking gate rejects them. This is an artistic decision, not a cleanup |

### Ownerless writer-prompt rules (WP-01 … WP-35)

| Family | Recommendation | Notes |
|---|---|---|
| WP-01 BREGMAN WRITING MODEL | **OWNER_DECISION** | SOFA §10 now states the writing standard in its own terms. Keeping both means two voice models. Retiring it is a real artistic change, not housekeeping |
| WP-02 `'ARGUMENT'` NEAR-ZERO | **OWNER_DECISION** | Carries a stale corpus statistic (63/138 of a corpus that has since grown). Either re-measure or generalise |
| WP-03 ANTI-SYSTEMIC TEST | **RETIRE** | Fully covered by SR-03 SYSTEM VOICE, which is gate-checked |
| WP-04 / WP-05 DISCOVERY VOICE + SIGNPOST PHRASES vs NO SIGNPOSTING | **OWNER_DECISION** | Prescribed stock phrases in one rule, forbidden narration in another. Not strictly contradictory, but they pull opposite ways and both are unchecked |
| WP-06…WP-11 craft heuristics | **KEEP** | Unchecked but coherent; they are the generative texture. Assign to WRITER as owner rather than leaving ownerless |
| WP-12 FORBIDDEN DEFAULTS | **OWNER_DECISION** | Highest-payload negative prohibition. SOFA's disturbance-first framing may make it unnecessary |
| WP-13 US-AVOIDANCE / UK-PREFERENCE | **OWNER_DECISION** | See #8 |
| WP-14 TITLE RULES | **KEEP** | Assign owner |
| WP-15…WP-17 wordlists | **CONSOLIDATE with SR-01** | Three separate forbidden-word lists (academic jargon, corporate clichés, gate R12 cultural-studies vocab) with no shared source |
| WP-18…WP-34 | **KEEP** | Assign WRITER as owner; no action |
| WP-25 AUTHOR RULE | **KEEP** | The one legacy rule that survives intact into SOFA. Consider promoting it to SOFA METHOD ownership explicitly |
| WP-35 persona voice framing | **OWNER_DECISION** | Governed by C4. Do not touch until the SOFA production migration is an actual decision |
| WP-26 GROUNDING | **KEEP + RENAME** | Named "GROUNDING" but unrelated to Writer Grounding. The name collision is a real comprehension hazard in a repo that now has a Writer Grounding architecture |

### Testimony (TV-01 … TV-05)

| Family | Recommendation |
|---|---|
| TV-01 | **KEEP** — current canonical form |
| TV-02, TV-03 | **RETIRE** — see #1 |
| TV-04 INSIDER WITNESS | **KEEP** — correctly phrased as protect-not-install |
| TV-05 L2 | **KEEP PARKED** |

### Grounding (GR-01 … GR-07)

All **KEEP**. GR-07 **KEEP PARKED** — owner stop is in force; this inventory does not
touch it and recommends nothing about it.

### Story Rejection (ST-01 … ST-05)

All **KEEP**. ST-04's known FC2 finding (first commission was false/permissive, N=1,
deliberately unpatched) is out of scope here and is not re-opened.

### Persona / byline (PB-01 … PB-11)

| Family | Recommendation |
|---|---|
| PB-02 | **DELETE_AFTER_VERIFICATION** — see #2 |
| PB-06 `_AGENT_BEATS` | **OWNER_DECISION** — see #9 |
| PB-11 | **KEEP PARKED** |
| rest | **KEEP** |

### Article form (AF-01 … AF-05)

| Family | Recommendation |
|---|---|
| AF-02 `_REGISTERS` vs WP-30 REGISTER | **CONSOLIDATE** — two independent register concepts shaping one piece |
| AF-03 `_LENGTHS` | **OWNER_DECISION** — SOFA §9 says no fixed word count; production has 6 weighted buckets plus hard caps and minimums |
| AF-04 | **KEEP** — known efficacy gap tracked separately |
| AF-05 | **KEEP PARKED** |
| AF-01 | **KEEP** |

### Discovery nudges (DI-01 … DI-14)

| Family | Recommendation |
|---|---|
| DI-01 `_get_beat_nudge` | **OWNER_DECISION** — see #9 |
| DI-02…DI-10 | **KEEP** — but assign DISCOVERY as owner; they are currently ownerless anti-repetition machinery bolted onto the writer prompt |
| DI-12, DI-13 (CJ-1, CJ-2 B2 probe scripts) | **PRESERVE_HISTORICAL_ONLY** — ~20 files in `automation/`; consider moving under `.claude/experiments/` so `automation/` holds only live code |
| DI-11, DI-14 | **KEEP PARKED** |

### Dead infrastructure (DE-01 … DE-10)

| Item | Recommendation |
|---|---|
| DE-01, DE-02 `style_rules.py` | **OWNER_DECISION** — wire it or declare it dead. Do not leave as-is |
| DE-03 `check_rule_drift.py` | **OWNER_DECISION** — give it a runner or mark manual-only in the docstring |
| DE-04 `.claude/CONTEXT.md:81` | **DELETE_AFTER_VERIFICATION** — the claim is false today |
| DE-05…DE-08 | **PRESERVE_HISTORICAL_ONLY** |
| DE-09 | already gone |
| DE-10 | **KEEP** — self-documented forward declarations, harmless |

---

## Owner decisions required (11)

1. `style_rules.py`: wire in, or declare dead? (blocks 8+ consolidations)
2. `check_rule_drift.py`: give it a runner, or mark manual-only?
3. WP-01 Bregman writing model: keep alongside SOFA §10, or retire?
4. SR-07 / C6 paragraph length: developed paragraphs (SOFA) or ≤5-sentence blocking gate?
5. AF-03 `_LENGTHS`: keep weighted word buckets against SOFA §9's "no fixed word count"?
6. WP-13: adopt the rewriter's UK preference in the writer, or strip it from the rewriter?
7. PB-06 / DI-01 `_AGENT_BEATS`: keep persona subject territories against SOFA §2?
8. WP-12 FORBIDDEN DEFAULTS: still needed under a disturbance-first model?
9. WP-04/05: reconcile prescribed discovery-voice phrases with NO SIGNPOSTING?
10. WP-02: re-measure or generalise the `'ARGUMENT'` corpus statistic?
11. DI-12/DI-13: relocate ~20 retired probe scripts out of `automation/`?

## Explicitly NOT recommended

- No change to Writer Grounding (GR-07). Owner stop is in force.
- No new experiment, harness, calibration, or FORM version.
- No production deploy.
- No article generation to "verify" any finding above. Every finding in this inventory
  was established from code and from captured prompt text, with zero model calls.
