# Phase-2 Preparation — Passive Capture + Comparison Harness

**STATUS: COMPLETE. NOT DEPLOYED. NOT PUSHED. FLAG NOT ENABLED. NO PRODUCTION BEHAVIOUR CHANGED.**

| Field | Value |
|---|---|
| Research HEAD (at start) | `7ee5fda` |
| Production baseline | `8af3622` = `origin/main` = Trident HEAD |
| Observability worktree | `/Users/stargatesgx/code/disability-collective-ai-production-observability`, branch `production-observability-2026-08-20`, based exactly on `8af3622` |
| **Deployable capture commit** | **`20a7e3a`** |

## Why the separate worktree

The canonical local repo is 25+ commits ahead of origin with `.claude/` evidence that is
deliberately never deployed. Building deployable instrumentation on top of that history would
make the deployment ambiguous. The patch is therefore committed on a branch based directly on
`8af3622`, carrying none of the research history, so it is independently cherry-pickable.

## Documents

| File | Contents |
|---|---|
| `PHASE2-CAPTURE-DESIGN.md` | Traced evidence flow, what is captured and why, isolation guarantees |
| `CAPTURE-SCHEMA.md` | Bundle layout, manifest format, integrity properties |
| `COMPARISON-PROTOCOL.md` | The six comparison dimensions and fail-closed verdicts |
| `FIRST-3-PRE-REGISTRATION.md` | The pre-registered Phase-2 sample rule |
| `SAFETY-RESULTS.md` | 72/72 checks, mapped to the brief |
| `DEPLOYMENT-PLAN.md` | Review checklist, deployment sequence, rollback, stop conditions |
| `harness/compare.py` | The comparison harness (307 lines) |
| `harness/compare_test.py` | 36 harness checks |
| `results/` | Test output |

The deployable code lives in the observability worktree, not here:
`automation/shadow_capture.py`, `automation/shadow_capture_test.py`, and a +52/−0 patch to
`automation/orchestrator/generate.py`.

## Key design points

**"Source text" is not one object.** Tracing the code before writing any capture found four
distinct representations — the full cached extraction, the returned slice, the
post-fallback-downgrade packet source, and the evidence packet. All are captured separately
rather than assumed equal; today R1 and R2 coincide only because both call sites use the same
20,000-char default, which is configuration, not an invariant.

**The raw writer output is the critical capture.** It exists only between the writer call and
the rewrite that overwrites it, and is on no disk today. Because the target architecture
removes the rewrite stage, separating what the legacy *writer* produced from what the legacy
*rewriter* changed is the most informative available signal — and it is attributable by
construction, since nothing executes between the two captures.

**Capture is non-authoritative by design.** A capture failure is logged and swallowed. It must
never hold an article. This is a deliberate exception to the target architecture's fail-closed
posture: capture observes the legacy baseline and is not part of ACCEPT/HOLD.

**Blocked runs are data, not noise.** Production currently blocks 4 of 7 drafts. The harness
records the outcome pairing and explicitly declines to treat either system as correct merely
because it blocked.

## Completion conditions

| | Condition | Result |
|---|---|---|
| A | Deployable passive capture exists | ✔ `20a7e3a`, +530/−0 |
| B | Source/evidence equivalence provable later | ✔ four representations + packet persisted as bytes, hash-verified |
| C | Raw writer vs rewrite distinguishable | ✔ captured separately, attributable by construction |
| D | Comparison harness exists | ✔ `harness/compare.py`, six dimensions, fail-closed |
| E | First 3 runs pre-registered | ✔ before enablement, before any run observed |
| F | Safety tests pass | ✔ 72/72 |
| G | No production behaviour changed | ✔ `snapshot_test --check` clean; flag OFF; not deployed |

## Not done

No model call. No live shadow run. No deploy. No push. No cron change. No flag enablement.
No AR3 patch. No architecture change. `snapshot_test.py` unmodified.
