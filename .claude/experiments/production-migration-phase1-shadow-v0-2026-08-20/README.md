# Production Migration Phase 1 — Clean Shadow Vertical Slice V0

**STATUS: PHASE 1 COMPLETE. OFF BY DEFAULT. NO PRODUCTION CODE MODIFIED. NOT DEPLOYED. NOT PUSHED.**

Built at local HEAD `bdb7e57`, production baseline `8af3622`.

Smallest OFF-by-default shadow vertical slice of the validated target architecture:

```
WORLD / SOURCE → DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING → SHADOW ACCEPT/HOLD
```

Purpose: architectural plumbing and artifact integrity. **Not an editorial calibration
experiment. Not production migration.**

## Documents

| File | Contents |
|---|---|
| `ARCHITECTURE.md` | Implementation location, isolation proof, modes, stage boundaries |
| `STAGE-CONTRACTS.md` | The eight artifact contracts and fail-closed rules |
| `SOURCE-PERSISTENCE.md` | The Phase-2 blocker and how V0 fixes it |
| `ACCEPT-HOLD.md` | The positive acceptance rule + open policy questions |
| `REPLAY-RESULT.md` | Golden replay results and the bugs fixed in-task |
| `SAFETY-TESTS.md` | 39 checks, mapped to the brief's requirements |
| `impl/` | The implementation (622 lines package + tests) |
| `runs/` | Replay artifacts, source snapshots, manifests, console output |

## Phase-1 success conditions

| | Condition | Result |
|---|---|---|
| A | Clean target stage contracts exist | ✔ 8 stages, `shadow-v0.1` |
| B | Source text persistence exists | ✔ contract-enforced; text + provenance, not just a hash |
| C | One complete preserved lineage replays end-to-end | ✔ Test 2 → ACCEPT; FORM-1.3 → HOLD |
| D | Shadow ACCEPT/HOLD works deterministically | ✔ identical hashes across runs |
| E | Legacy production prompt surfaces absent | ✔ 29 markers rejected by contract; 0 hits in both fixtures |
| F | No production state changed | ✔ 0 production files modified, 0 DB writes, 0 content writes |
| G | Safety tests demonstrate default-OFF / fail-closed | ✔ 39/39 |
| H | Implementation small enough to review | ✔ 622 lines package, 4 modules |

**PHASE 1 COMPLETE: YES.**

## Isolation summary

Nothing in `automation/` references this package — verified by grep, not asserted. `run()`
refuses unless `SHADOW_V0_MODE` is set explicitly. There is no `sqlite3`, no network client
and no subprocess in the executable code, so a production DB write or a publication is not
merely disallowed but unimplementable from here.

## What Phase 1 deliberately did not do

No live shadow run. No model call. No production import. No legacy prompt cleanup. No AR3
patch. No Story Rejection change. No `_should_block` change. No modification to
`snapshot_test.py`. No new article generated to test plumbing — both fixtures are preserved
evidence.

## AR3

Unchanged and still deferred, per owner decision: rewrite rules 33/33b remain known migration
debt. The stall is `fact_check` blocking (4 of 7 drafts), and there is no evidence AR3 causes
it.
