# Known Baseline Defects — preserved, NOT fixed

These are part of the frozen baseline. They describe what production actually does today.
**Nothing here was corrected in Phase 0.** Fixing any of them would make the baseline a
description of a system that has never run.

Each is verified against the runtime at HEAD `8af3622`, not read from documentation.

---

## D1 — AR3 contradiction: the testimony quota is still live in the rewriter

**Status: LIVE. NOT FIXED. HOTFIX DECISION PENDING.**

`rewrite_with_opus`'s SYSTEM prompt (`llm.py:394`) still contains both blocks AR3A removed
from the writer prompt:

- rule **33**: *"NAMED VOICES: The draft should have 2-3 real named people … **REQUIRED**:
  beyond the primary subject of the article, a second real named person must appear doing
  something specific in the body."*
- rule **33b**: *"SOMEONE ELSE MUST SPEAK: at least one other person must say something out
  loud inside actual quotation marks…"*

Meanwhile the writer prompt says (`generate.py:882`) *"Zero testimony is valid. Zero
quotations is valid. Zero secondary named people is valid."*

`rewrite_with_opus` is called on **every** production article (`generate.py:1168`).
Verified today: `"SOMEONE ELSE MUST SPEAK"` occurs **0** times in `generate.py`, **1** time
in `llm.py`.

Partial mitigation, not overstated: rule 33b forbids inventing a quote, and
`_reject_if_unsupported_specifics` guards the rewrite output. The fabrication path is partly
blocked; the editorial pressure AR3 identified as causal is not.

**Per Phase-0 instruction §11: `AR3 HOTFIX DECISION PENDING AFTER BASELINE FREEZE`.**

## D2 — R-number collisions between gate and review

**Status: LIVE. NOT FIXED.**

Nine rules carry different R identifiers in `GATE_SYSTEM` (R1–R17) and `RULES_SYSTEM`
(R1–R19), while `gate.py::_parse_rule_verdicts` / `_missing_rule_ids` key on those
identifiers.

| Rule | GATE | REVIEW |
|---|---|---|
| VAGUE WE | R5 | R6 |
| SYSTEM VOICE | R17 | R5 |
| CRAFTED RHETORIC | R15 | R16 |
| ONE IDEA PER SENTENCE | R16 | R17 |
| FRONT-LOADED SENTENCE | R6 | R7 |
| LONG LIST | R8 | R10 |
| PARAGRAPH LENGTH | R7 | R8 |
| JARGON | R10 | R13 |
| SUBJECT-VERB DISTANCE | R14 | R15 |

"R5" means SYSTEM VOICE in one prompt and VAGUE WE in the other.

## D3 — WP-13: UK-preference mismatch between writer and rewriter

**Status: LIVE. NOT FIXED.**

The writer prompt says only *"DO NOT locate arguments in the United States specifically."*
The rewrite SYSTEM's rule 32 adds a positive geographic preference the writer is never told
about: *"US-AVOIDANCE + UK-PREFERENCE … Preferred geographies: UK (DWP, PIP assessments,
NHS social care, Equality Act 2010, Section 117 aftercare), the Netherlands, Germany…"*

The rewriter therefore steers geography in a direction the writer had no instruction to
follow.

## D4 — Duplicated persona canon

**Status: LIVE. NOT FIXED.**

For the three fictional personas the same canon text is injected into the writer prompt
**twice, byte-identical** — once as `--- YOUR CANON (WHO YOU ARE, IMMUTABLY) ---` and again
as `--- AUTHORIZED PERSONAL HISTORY ---`. For Maya Flux that is 7,216 characters, ~12% of the
prompt, hash `4324a24e04071304…` on both copies.

The sentence joining them states the canon *"does NOT authorize autobiographical facts"* —
while pointing at that same text as the authorized factual history.

Pixel Nova is unaffected: `pixel-nova-factual.md` exists, so the two blocks legitimately
differ.

Root cause: `_load_persona_factual_context` (`llm.py:589`) falls back to
`_load_persona_canon()` in full for personas without a `-factual.md` file.

## D5 — Mass-injected writer prompt

**Status: LIVE. NOT FIXED.**

`generate.py:783–1050` assembles **59,161 characters / 9,862 words / 75 prescriptive rule
units** per run for Maya Flux (54,673 for Pixel Nova), plus persona canon twice and ten
dynamically generated nudge blocks.

Four further live bundles: rewrite SYSTEM 25,019 ch (47 rules), planner 15,358 ch,
`RULES_SYSTEM` 9,035 ch, `GATE_SYSTEM` 8,105 ch. **≈130,000 characters of rule text per
article.**

## D6 — `style_rules.py` unwired

**Status: LIVE. NOT FIXED, AND MUST NOT BE WIRED.**

The 16-rule registry built 2026-08-09 as the "single source of truth" has **zero runtime
consumers**. Verified again today: `grep "from style_rules import"` across
`automation/orchestrator/` returns **0** results; the only occurrence in the repo is inside
`style_rules.py`'s own docstring example.

Its companion linter `check_rule_drift.py` has no automated runner — no Makefile, no CI job
(`.github/workflows/` contains only `deploy.yml`), no cron entry.

## D7 — Legacy negative-prohibition surface

**Status: LIVE. NOT FIXED.**

The assembled writer prompt contains **80 negative-prohibition tokens** (`Never` ×18,
`never` ×19, `Do not`/`do not`/`Do NOT` ×29, `BANNED` ×6, `banned` ×5, `FORBIDDEN` ×3).

Several carry concrete nouns or verbatim bad-example sentences that Edinburgh's finding says
can resurface as positive prose claims: `FORBIDDEN DEFAULTS` names the banned objects;
`TITLE RULES` lists banned opening nouns; `BLOCKED THEORISTS` injects real theorist names
only to forbid them; `ONE IDEA PER SENTENCE` quotes a full published bad sentence.

## D8 — Fallback behaviour unresolved

**Status: LIVE. NOT FIXED. OWNER DECISION OPEN.**

On total provider failure the pipeline calls `generate_fallback_article`
(`generate.py:1064` → `content_checks.py:297`) and continues toward publication with a
generic template, rather than holding. Under the target architecture's ACCEPT/HOLD rule this
would arguably be a HOLD. Not decided.

---

## D9 — NEW, observed during this freeze: promotion is currently stalled

**Status: LIVE. NOT FIXED. Not previously recorded.**

This was not a known defect before Phase 0; it was observed by inspecting the running system.

- Latest **published** post: `_posts/2026-08-11-reached-by-boat-or-plane.md`.
- **Seven drafts** sit in `_drafts/`, dated 2026-08-13 through 2026-08-20.
- **Four of the seven carry `fact_check_status: blocked`**, three with an explicit
  `pipeline_degraded` list:

| Draft | status | degraded stages |
|---|---|---|
| 2026-08-13 what-the-word-modular-quietly-removes | verified | — |
| 2026-08-14 modular-means-it-comes-apart… | verified | — |
| 2026-08-15 hand-hammered-edge… | **blocked** | (none listed) |
| 2026-08-16 sniff-it-out… | verified | — |
| 2026-08-17 7-000-rooms… | **blocked** | `[persona_biography_unresolved]` |
| 2026-08-17 galaxy-h1… | **blocked** | `[gate_llm, persona_biography_unresolved]` |
| 2026-08-20 surovell-built-a-box… | **blocked** | `[fable_brief]` |

`_compute_should_block` is therefore **actively firing in production**, and nothing has been
promoted to `_posts` for nine days. Whether that is correct behaviour (the safety net working)
or a stall worth investigating is **not decided here** — it is recorded as the baseline
condition so that any change after migration can be attributed correctly.

This is important for Phase 2: a live-vs-shadow comparison that ignores blocking would
compare the new architecture against articles production itself declined to publish.
