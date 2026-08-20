# Production Migration — Phase 0: Baseline Freeze

**STATUS: PHASE 0 COMPLETE. NO IMPLEMENTATION. NO DEPLOYMENT. NO PRODUCTION CODE MODIFIED.**

Captured 2026-08-20. Local HEAD `c6f97b8`, production HEAD `8af3622`.

Purpose: make later live-vs-shadow comparison meaningful and reversible. This is a
description of what production does **today**, including its defects — not a corrected
version of it.

## Documents

| File | Contents |
|---|---|
| `GIT-AND-RUNTIME-BASELINE.md` | Local + production Git state, divergence, cron, flags, provider routing, disk |
| `PRODUCTION-COMPONENT-MAP.md` | Every component located in runtime/code, with observed state |
| `PROMPT-BASELINE.md` | Hash-frozen prompt surface + pipeline source hashes |
| `KNOWN-DEFECTS.md` | D1–D9, preserved as defects, unfixed |
| `DATABASE-BACKUP-MANIFEST.md` | 5 DBs, safe backup method, integrity, hashes |
| `PUBLICATION-STATE.md` | Content counts, draft queue, DB row counts |
| `HELD-OUT-FIXTURES.md` | 5 identified fixtures + the source-persistence blocker |
| `SNAPSHOT-TEST-COVERAGE.md` | What the safety net covers and does not |
| `db-backup-manifest.json` | Machine-readable backup manifest |
| `SHA256SUMS.txt` | Integrity record for this root |

## Phase-0 success conditions

| | Condition | Result |
|---|---|---|
| A | Exact local + production Git/runtime state known | ✔ Local `c6f97b8` (25 ahead / 2 behind, none deployed); production `8af3622` = origin, clean; **13 pipeline files verified byte-identical across both** |
| B | Live production architecture mapped | ✔ 17 stages in execution order, every component located in code |
| C | Live prompt surface hash-frozen | ✔ 12 static prompts + 5 canon files + 4 persona blocks + 13 source files; assembled writer prompt re-derived and **verified byte-identical** to the preserved capture |
| D | Known defects preserved, not corrected | ✔ D1–D9, all unfixed |
| E | Migration-relevant SQLite state safely backed up | ✔ 5/5 via `Connection.backup()`, 5/5 `integrity_check: ok` |
| F | Publication/content baseline recorded | ✔ 142 posts, 7 drafts, 138 reviews, DB row counts |
| G | Held-out fixtures identified | ✔ 5, no generation performed |
| H | Snapshot/regression coverage understood | ✔ passes clean; gaps recorded |

**PHASE 0 COMPLETE: YES.**

## Two findings that change the plan

**1. The daily DB backup already exists and is safe.** The migration plan and
`PROJECT-MAP.md` both carried "no SQLite-safe backup exists yet (open risk)". That is false:
`automation/backup_state_dbs.py` has run daily since 2026-08-10 using SQLite's backup API
with integrity verification. Corrected in both places. The real limitation is 14-day
retention, which is why this task took a **separate retained baseline** at
`/srv/backups/cripminds-phase0-baseline/`.

**2. Production source text is not persisted.** Only `source_hash` is stored. For most
fixtures the exact bytes the writer saw cannot be recovered, only verified by re-fetch. This
is a **Phase-2 blocker**. One fixture escapes it: `sniff-it-out` used source hash
`fee0a03b…`, byte-identical to the Edinburgh source already frozen in the FORM-1.3
experiment — giving a direct legacy-vs-Article-Form comparison on identical input.

## Also observed

Production is **live and publishing** — it generated and pushed an article this morning. And
it is **currently blocking**: 4 of 7 drafts carry `fact_check_status: blocked`, and nothing
has reached `_posts` since 2026-08-11. Recorded as baseline condition D9, not diagnosed.

## AR3

**`AR3 HOTFIX DECISION PENDING AFTER BASELINE FREEZE`** — per instruction §11. Rewrite rules
33/33b were **not** patched. The baseline now captures the real current behaviour, so the
decision can be made against evidence: accept the debt if migration begins soon, or apply a
tiny isolated hotfix as insurance if the window is long.

## Not done

No Phase 1 implementation. No shadow modules. No prompt cleanup. No AR3 patch. No Story
Rejection change. No `_should_block` change. No Test 3. No deploy. No push.
