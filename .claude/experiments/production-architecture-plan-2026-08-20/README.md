# Production Architecture / Migration Plan — 2026-08-20

**STATUS: PLAN ONLY. NO IMPLEMENTATION. NO DEPLOYMENT. NO CODE MODIFIED.**

Written at HEAD `8741804`, after Real Article Test 2 closed as **TRANSFER_PASS**.

## Inputs

| Input | Commit |
|---|---|
| Legacy Prompt / Rule Inventory — 114 rule families | `38c47b8` |
| Owner triage + Test-2 boundary | `7778ee1` |
| Real Article Test 2 — frozen packet | `2dd9a86` |
| Real Article Test 2 — execution and evaluation | `8741804` |
| Canonical SOFA method | `.claude/SOFA-METHOD.md` |

## Documents

| File | Contents |
|---|---|
| `TARGET-ARCHITECTURE.md` | The candidate pipeline and each stage's responsibility, including what is deliberately absent |
| `LIVE-VS-TARGET.md` | Live stage order from `generate.py`, mapped against the target |
| `COMPONENT-DISPOSITIONS.md` | Every current component: KEEP / ADAPT / REPLACE / REMOVE / PARK / UNKNOWN |
| `LEGACY-RULE-MIGRATION.md` | Which of the 114 rule families die with their stage rather than needing cleanup |
| `PRODUCTION-DEBT-BEFORE-MIGRATION.md` | Inventory debts re-adjudicated against stage fate; the real migration blockers |
| `MIGRATION-SEQUENCE.md` | Phases 0–6, each with an exit criterion |
| `ROLLBACK-AND-SHADOW-PLAN.md` | Shadow discipline reused from `cj2_shadow.py`; per-phase rollback |

## The central finding

**~81% of the inventory's live rule debt is deleted by replacing three stages** — the writer
prompt, the whole-document rewrite, and the two LLM rule-judges. Nearly every item on the
inventory's top-10 cleanup list should therefore **not be cleaned**: not the AR3 testimony
quota, not the 9 R-number collisions, not the UK-preference divergence, not the persona-canon
double-injection, not the eight five-copy style families, and not `style_rules.py`.

The correct action on that debt is to do nothing until its stage is deleted — with one
caveat recorded in `PRODUCTION-DEBT-BEFORE-MIGRATION.md`: those debts stay live for the whole
migration window, and if the migration stalls, the cheap AR3 patch becomes correct after all.
That is an owner decision, not the plan's.

## Status of each architecture layer

| Layer | Status |
|---|---|
| SOFA editorial/artistic method | CANONICAL |
| Article Form | **TRANSFER-VALIDATED ON TWO MATERIALLY DIFFERENT STORY SHAPES** — not production-deployed |
| Writer Grounding | SHADOW-CALIBRATED, successfully exercised on Test 2 — not production-validated |
| Story Rejection V1.1 | live in production, KEEP |
| Production pipeline | **NOT MIGRATED** |

Nothing here implies production validation.
