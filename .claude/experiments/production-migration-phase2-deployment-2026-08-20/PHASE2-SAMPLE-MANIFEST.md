# Phase-2 Sample Manifest

**FROZEN RULE, registered before enablement (2026-08-20, `8776e9d`):**

> PHASE-2 COMPARISON SET = the **FIRST 3 COMPLETE ELIGIBLE PRODUCTION ARTICLE RUNS AFTER
> CAPTURE ENABLEMENT**, in capture-run-id order. No cherry-picking.

Capture enabled **2026-08-20T09:36:55Z**. Today's article run had already completed at
09:09 CEST, *before* enablement, so it is **not** in the sample.

## Status: AWAITING RUNS — 0 of 3 captured

The article cron fires once daily at 09:00 CEST. The three eligible runs are therefore:

| Index | Expected run | Status |
|---|---|---|
| **P2-01** | 2026-08-21 09:00 CEST | pending |
| **P2-02** | 2026-08-22 09:00 CEST | pending |
| **P2-03** | 2026-08-23 09:00 CEST | pending |

**This cannot be completed in the deploying session.** Collecting the sample requires
waiting three real days of normal production. Per the brief, extra runs must **not** be
triggered artificially to fill it.

## Manifest table — to be filled strictly in chronological order

| Index | Run ID | Timestamp | Slug | Source URL | Source SHA-256 | Evidence packet hash | Raw writer SHA-256 | Rewrite SHA-256 | Gate | Review | Fact-check | Legacy disposition | Bundle SHA-256 | Validity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P2-01 | | | | | | | | | | | | | | |
| P2-02 | | | | | | | | | | | | | | |
| P2-03 | | | | | | | | | | | | | | |

### Invalid captures

| Run ID | Date | Reason | Action |
|---|---|---|---|
| *(none yet)* | | | |

A `CAPTURE_INVALID` bundle does not count toward the three. Record it and take the next
chronological complete run.

## Legacy disposition is OBSERVATION, not truth

Record the actual state — `PUBLISHED`, `DRAFT`, `BLOCKED`, `FAILED`, `FALLBACK`. Do **not**
treat published as correct or blocked as incorrect. Production currently blocks 4 of 7 drafts
and has published nothing since 2026-08-11; blocked runs are valid, expected sample material.
Phase 2 compares the *reasons*, later.

## Source equivalence is the key artifact

For each accepted bundle the captured generation-time evidence is **authoritative**. Do not
re-fetch the source later. Do not re-normalize later. The bundle holds the exact bytes
production consumed, so a later shadow run can be proven to have consumed the same frozen
evidence by hash rather than by re-derivation.

## No editorial evaluation

Nothing in this manifest evaluates article quality. Eligibility is mechanical: normal article
run, sealed complete bundle, hashes verify, enough lineage.
