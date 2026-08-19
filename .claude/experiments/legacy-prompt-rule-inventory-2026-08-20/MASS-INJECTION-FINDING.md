# Mass-Injection Finding

**Question:** Did / does CripMinds have one or more mechanisms that inject a large
bundle of rules into prompts?

**Answer: YES — two distinct generations. The second one is live today.**

Jascha's recollection of a historical large/mass-injected rule set is **confirmed by
code and by the repo's own written record.** It was not dismissed; it was found.

---

## Generation 1 — HISTORICAL (pre-2026-08-09): hand-copied rule text

**What it was.** ~15 writing-style rules were hand-copied as raw prompt text into at
least **12 separate locations** across `automation/production_orchestrator.py` and two
now-deleted scripts: `opus_rewrite.py` and a root-level `production_orchestrator.py`.

**Source of the account.** `automation/style_rules.py` lines 5–15 — written by the
person who did the consolidation, describing the incident that prompted it.

**Confirmed drift it produced** (four instances, found by direct comparison at the time):

| Drift | Detail |
|---|---|
| Jargon wordlist diverged | 5 vs 7 vs 8 terms across 3 copies; one term present in exactly one copy |
| Metaphor-for-mechanism ban | no quoted-speech exception in any of 3 copies |
| List-length cap | contradicted by real source material in all 4 copies |
| R-number collision | a code comment mislabelled which rule a shared deterministic check belonged to, because two copies used different R-number schemes for the same rule |

**Status:** HISTORICAL. The two scripts are deleted. `production_orchestrator.py` is now
a 186-line entry point (module split completed 2026-08-09).

**But the drift class it caused is NOT gone** — see Generation 2 and
`DUPLICATES-AND-CONTRADICTIONS.md` §Numbering.

### The fix that was built and never connected

`automation/style_rules.py` (2026-08-09, migration Stage 2) is a 16-rule registry with
three text renderings per rule (`imperative` / `full` / `terse`), shared `exemptions`,
and render-time R-numbering keyed on stable slugs so "R14 means two different things in
two functions" would be structurally impossible.

**It has zero runtime consumers.**

Verified: `grep -rn "style_rules|render_gate(|render_review(|render_writer_bullet(|render_rewrite("`
over all `*.py` outside `.claude/experiments/` returns **no import and no call** from any
production module. Every hit is either inside `style_rules.py` itself, inside
`check_rule_drift.py`'s descriptive text, or a comment in `generate.py` / `gate.py` /
`automation/README.md` describing the wiring as a *still-open future step*:

> `automation/README.md`: "Wiring `style_rules.py`'s registry directly into
> `gate.py`/`review.py`'s hand-typed prompt text is a separate, still-open, genuinely
> riskier future step — not attempted as part of this split."

> `check_rule_drift.py:117`: "…`style_rules.py`'s registry with zero wiring anywhere in
> the actual [prompts]"

The accompanying drift linter, `automation/check_rule_drift.py`, **also has no automated
runner**: no `Makefile` exists in this repo, `.github/workflows/` contains only
`deploy.yml` (Jekyll build), and no cron entry or shell script invokes it. It runs only
if a human remembers to type it.

**Net effect: `style_rules.py` did not replace the mass injection. It became a fourth
parallel copy of it.**

---

## Generation 2 — CURRENT, LIVE TODAY

### 2a. The primary injection point

**`automation/orchestrator/generate.py:783–1050`**, inside
`_run_production_automation_locked()`.

A single `prompt = ( ... )` expression concatenating ~270 source lines into one string.

**Measured on the actual constructed prompt** (captured via the repo's own
`writer_prompt_test.py::_capture_writer_prompt`, zero network):

| Persona | chars | words |
|---|---|---|
| Maya Flux (fictional / editorial-canon provenance) | **59,161** | **9,862** |
| Pixel Nova (real-person-evidence provenance) | **54,673** | **8,965** |

**Composition of the Maya Flux prompt — 75 prescriptive rule units:**

| Component | Count |
|---|---|
| `Voice and style:` bullet rules | 42 |
| Standalone ALLCAPS rule blocks | 27 |
| `TITLE RULES — NON-NEGOTIABLE` bullets | 6 |
| **Total prescriptive units** | **75** |

Plus, in the same string:

- persona `prompt_block` from `personas.py` (3,323–4,337 chars depending on persona)
- persona canon from `automation/persona_canon/<slug>.md` — **injected twice** (7,216
  chars each for Maya, byte-identical; see contradiction C3)
- persona mutable state (obsessions / arguments / register)
- 10 dynamically-generated nudge blocks (see 2b)
- the source snapshot, news block, link block, angle, wound

**Negative-prohibition density:** 80 negative tokens (`Never` ×18, `never` ×19,
`Do not`/`do not`/`Do NOT` ×29, `BANNED` ×6, `banned` ×5, `FORBIDDEN` ×3). Several carry
concrete nouns or verbatim bad-example sentences that Edinburgh's finding says can
resurface as positive prose claims — see `DUPLICATES-AND-CONTRADICTIONS.md` §Negative
Prohibition Risk.

### 2b. Dynamic rule injectors feeding it

Ten separate methods generate rule text at runtime and are concatenated into the same
prompt. All live in `discovery.py` unless noted, all called from `generate.py:655–773`:

| Injector | Injects |
|---|---|
| `_get_beat_nudge` | "You haven't written about `<beat>` recently" — from `_AGENT_BEATS` |
| `_get_scholar_nudge` | anti-repetition on cited scholars |
| `_get_blocked_theorists` | `BLOCKED THEORISTS — Do NOT cite, name, or even allude to: <names>` |
| `_get_recent_dates_nudge` | avoid recently-used date anchors |
| `_get_shape_nudge` | nudge away from overused article shapes |
| `_get_calendar_event_nudge` | disability/cultural calendar proximity |
| `_get_claims_nudge` | persona's active falsifiable claims |
| `_get_recent_title_patterns` | `TITLE RULES` + recent titles to avoid |
| `_get_overused_themes` | `DIVERSITY NOTE` on clustered themes |
| `_check_title_freshness` | `FRESHNESS NOTE` on title word overlap |

### 2c. The other four live rule bundles

Every one of these is a separate hand-typed rule list reaching a live model call:

| # | Bundle | Location | Size | Rules | Stage |
|---|---|---|---|---|---|
| 1 | Writer prompt | `generate.py:783` | 59,161 ch | 75 | GENERATE (user) |
| 2 | Writer SYSTEM | `llm.py:232` | 3,212 ch | — | GENERATE (system) |
| 3 | **Rewrite SYSTEM** | `llm.py:394` | **25,019 ch** | **47 numbered** | REWRITE |
| 4 | Planner / Story Rejection brief | `llm.py::_fable_editorial_brief` | 15,358 ch (user) | 4 blocks + field contract | PLAN |
| 5 | `RULES_SYSTEM` | `review.py:1173` | 9,035 ch | R1–R19 | REVIEW |
| 6 | `GATE_SYSTEM` | `gate.py:233` | 8,105 ch | R1–R17 | GATE (blocking) |

Smaller live rule-bearing prompts: engagement read (4,161), `_EXECUTOR_CONTRACT` (2,007),
persona cross-cite (1,484), register `FIX_SYSTEM` (1,221), link editor (1,070),
fact-check (905), `_EXECUTOR_PERSONA_HISTORY_CONTRACT` (750), `SUBJECT_SYSTEM`
article-type compliance (533), `CITATION_SYSTEM` (517), form `FIX_SYSTEM` (421).

### 2d. Total rule payload per article run

**≈ 130,000 characters** of rule-bearing prompt text across all stages of one article,
carrying **≈ 158 distinct prescriptive rule statements** (75 writer + 47 rewrite +
19 review + 17 gate), before persona canon, source material and nudges.

---

## Which model calls receive it

| Call | Receives | Provider path |
|---|---|---|
| `call_llm_via_openclaw_session(prompt)` — the writer | bundles 1 + 2 (~62,373 ch) | Hermes/Nous session path, CLIProxy fallback |
| `rewrite_with_opus(content, …)` | bundle 3 (25,019 ch) | `_call_openai_compat_api` |
| `_fable_editorial_brief(...)` | bundle 4 (~18,035 ch total) | `_call_editorial_model` |
| `validate_article(...)` | bundle 5 + 4 smaller review prompts | `_call_openai_compat_api` |
| `_pre_commit_gate(...)` | bundle 6 (+ FIX_SYSTEMs on repair) | `_call_openai_compat_api` |

All five run on **every** production article. Nothing here is gated behind a flag.

---

## Still active? — explicit answer

| Mechanism | Active today |
|---|---|
| Generation 1 hand-copied rules across 12 locations | **NO** — files deleted / module split |
| Generation 2 writer-prompt mass concatenation | **YES** |
| Generation 2 rewrite / planner / review / gate bundles | **YES** |
| `style_rules.py` registry as a prompt source | **NO** — zero consumers, never wired |
| `check_rule_drift.py` linter | **NO automated runner** — manual only |

The consolidation was designed, built, documented, and never connected. What Jascha
remembers as "a historical large mass-injected rule set" was consolidated *on paper*
and is still mass-injected *in code*.
