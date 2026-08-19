# Legacy Rule Migration — what dies with its stage

Source: `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/` (commit `38c47b8`),
114 rule families, 96 active in production.

**The governing principle: do not spend effort cleaning a component the migration will
delete.** Every family below is classified by *fate under migration*, not by how bad it is.

---

## Fate classes

| Class | Meaning |
|---|---|
| `DELETED_WITH_STAGE` | The owning stage is REMOVED or REPLACED. No cleanup work. The family simply ceases to exist. |
| `SURVIVES_NEEDS_WORK` | The owning component is KEEP/ADAPT, so the debt travels with it and must be resolved. |
| `SURVIVES_CLEAN` | Owning component survives and carries no debt. |
| `ALREADY_DEAD` | No live consumer today. |

---

## Headline count

| Fate | Families | Share |
|---|---|---|
| `DELETED_WITH_STAGE` | **~92** | 81% |
| `SURVIVES_NEEDS_WORK` | **~6** | 5% |
| `SURVIVES_CLEAN` | ~11 | 10% |
| `ALREADY_DEAD` | 5 | 4% |

**Roughly four fifths of the inventory's debt is retired by replacing three stages** — the
writer prompt, the rewrite pass, and the two LLM rule-judges. That is the single most
important finding in this plan.

---

## Family-by-family fate

### Deleted with the writer prompt (REPLACE)

| Families | Fate |
|---|---|
| **WP-01 … WP-35** — all 35 ownerless writer-prompt rules (Bregman writing model, `'ARGUMENT'` near-zero, anti-systemic test, discovery voice, signpost phrases, microscope/telescope, end-weight, paragraph momentum, landing, one-aphorism budget, translate-one-abstraction, arrival paragraph, forbidden defaults, US-avoidance, title rules, the three forbidden-word lists, no-empty-grandeur, show-then-name, temporal anchors, historical-anecdote test, find-something-out, do-not-manage-the-reader, no-encyclopedic-appositives, human thread, author rule, grounding-in-the-body, no-hedging, reader address, translate-large-numbers, register, sentence length, metaphor-urge, rhetorical questions, plain-list refrain, persona voice framing) | `DELETED_WITH_STAGE` |
| **SR-01 … SR-19** — the writer-prompt copy of every duplicated style family | `DELETED_WITH_STAGE` (writer copy) |
| **PB-01, PB-02, PB-05, PB-07 … PB-10** — persona prompt blocks, canon injection (including the byte-identical double injection), indefensible forms, fault lines, wound, mutable state | `DELETED_WITH_STAGE` |
| **AF-01, AF-02, AF-03** — article types, registers, length buckets | `DELETED_WITH_STAGE` |
| **DI-01 … DI-10** — the ten anti-repetition nudge injectors | `DELETED_WITH_STAGE` *as writer-prompt injections*; the underlying corpus-hygiene function is an owner decision to relocate or drop |
| **TV-01** — the AR3 testimony rule text | `DELETED_WITH_STAGE`; the principle is canonical in SOFA §7 and needs no prompt copy |
| **The prohibition-heavy surface** — 80 negative tokens, and the concrete nouns and verbatim bad-example sentences they carry | `DELETED_WITH_STAGE`. This is the cleanest resolution of the Edinburgh negative-prohibition risk available: the surface is not audited or rebalanced, it is removed. |

### Deleted with the rewrite stage (REMOVE)

| Families | Fate |
|---|---|
| **TV-02, TV-03** — rewrite rules 33 and 33b, the AR3 testimony quota | `DELETED_WITH_STAGE` — **this is why the AR3 debt should not be patched now** |
| **WP-13** — the unilateral UK-preference in rewrite rule 32 | `DELETED_WITH_STAGE` — same reasoning |
| **TV-04** — insider witness | `DELETED_WITH_STAGE` (correctly phrased, but has no home in the target) |
| The rewrite copy of **SR-01 … SR-16**, and all 47 numbered rules | `DELETED_WITH_STAGE` |

### Deleted with the LLM rule-judges (REMOVE from gate and review)

| Families | Fate |
|---|---|
| **GATE_SYSTEM R1–R17** and **RULES_SYSTEM R1–R19** | `DELETED_WITH_STAGE` |
| **The 9 R-number collisions** | `DELETED_WITH_STAGE` — **do not renumber; the numbering scheme goes away** |
| **SR-20, SR-21, SR-22** — latinate/cultural-studies wordlists, rhythmic monotony, long-sentence | `DELETED_WITH_STAGE` (gate-only families) |

### Survives — needs work

| Family | Owner | Work required |
|---|---|---|
| **GR-01 … GR-06** — evidence packet, field schema, unsupported-specifics scanners, fallback-summary authority, executor contracts, lineage | `grounding.py` → WRITER GROUNDING | Not debt. But the modular arbitration layer must be **built** on top of them. Largest single build in the migration. |
| **GR-07** — Writer Grounding V0–V6 arbitration | `.claude/experiments/` only | Must be implemented as a production module. Currently zero production wiring. |
| **ST-01 … ST-05** — Story Rejection | KEEP | Carries the open FC2 finding (commission path has no grounding verification equivalent to decline's; N=1, deliberately unpatched). Decide before or during migration. |
| **PB-03, PB-04** — provenance modes, `PENDING VERIFICATION` exclusion | ADAPT | Sound design. Must be re-pointed once persona material no longer reaches the writer — decide where first-person claims remain possible at all. |
| **AF-04** — article-type compliance check | KEEP | Known efficacy gap on record (types selected correctly, outputs ignore the form's rules). Under the target, ARTICLE FORM owns form, so this check's subject changes. Re-scope rather than fix. |
| **PB-06 / DI-01** — `_AGENT_BEATS` persona subject territories | ADAPT/REMOVE | Contradicts SOFA §2. Dies if the nudges are dropped; survives if corpus hygiene is relocated. Owner decision. |

### Survives — clean

Deterministic checks (`rewrite_integrity.py` — narrowed scope, `opening_template_detector.py`,
`human_detail_provenance.py`), gate's deterministic prose checks, review's shadow structural
checks and engagement read, web fact-check, PB-08 cross-cite accuracy, PB-11
`assert_no_persona_leakage` (which becomes *more* load-bearing under `Byline ≠ prose persona`),
DE-10, and all publication stages.

### Already dead

**DE-01, DE-02** (`style_rules.py` registry + renderers), **DE-03** (`check_rule_drift.py`),
**DE-05 … DE-09** (`editorial-lens.md`, `MANIFESTO.md`/`PIPELINE.md`, `prose_audit.py`,
`archive/`, deleted mass-injection copies).

**`style_rules.py` gets a definitive answer from this plan:** the four hand-typed copies it
was built to unify are, with the exception of a handful of deterministic checks, all
`DELETED_WITH_STAGE`. There will be nothing left for it to be the single source of truth
*for*. **Retire it. Do not wire it in.**

---

## The 24 migrated / redundant families

The inventory identified 24 families whose responsibility already has a structural owner.
Under this plan every one of them is `DELETED_WITH_STAGE` — the prompt copy goes when its
stage goes, and the structural owner is the only remaining implementation:

| Structural owner | Prompt copies retired |
|---|---|
| SOFA METHOD | Bregman writing model, anti-systemic test, author rule, paragraph targets |
| ARTICLE FORM | article types, registers, length buckets, indefensible forms, arrival paragraph, ending shape |
| WRITER GROUNDING | no-invented-statistics, no-invented-data, temporal-anchor invention ban |
| STORY REJECTION | ad-hoc "find an angle" pressure in the legacy planner |
| PRF1 | provenance modes; and the redundancy of the persona-roleplay machinery |
| Deterministic code | fabrication, rewrite integrity, opening templates, contact claims |

---

## Consequence for sequencing

Cleanup work that would have been needed under an incremental approach and is **not needed**
under this plan:

- renumbering gate/review rules to remove 9 collisions
- de-duplicating 8 five-copy style families across four surfaces
- consolidating three separate forbidden-word lists
- auditing or rebalancing 80 negative prohibitions
- patching AR3's rewrite 33/33b
- fixing the UK-preference divergence
- de-duplicating the persona canon double-injection
- wiring `style_rules.py`

That is the great majority of `CLEANUP-RECOMMENDATIONS.md`'s top-10 list. **The correct
action on nearly all of it is to do nothing until the stage is deleted.**
