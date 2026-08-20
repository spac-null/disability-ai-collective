# Comparison Protocol

`harness/compare.py`. Deterministic. **No model call, no LLM judge, no prose-quality score.**

The harness reports what differs and what is attributable. It does not decide which article
is better, and it does not assume either system is correct.

## Input

```
python3 harness/compare.py <capture-bundle-dir> [--shadow-run <phase1-shadow-run-dir>]
```

The shadow side is optional. With no shadow lineage the harness still validates the bundle
and reports the legacy outcome (`verdict: LEGACY_ONLY`), so it is useful the moment capture
lands and before any shadow execution exists.

## Gate: source equivalence

A comparison is only sound if both sides consumed identical evidence. The harness proves this
by hash before reporting any outcome pairing:

| Verdict | Meaning |
|---|---|
| `EQUIVALENT` | shadow source SHA-256 == legacy `packet_source` SHA-256 → proceed |
| `SOURCE_MISMATCH` | → `REJECTED_SOURCE_MISMATCH`; outcomes are **not** compared |
| `NO_SHADOW_SOURCE_SUPPLIED` | → `LEGACY_ONLY` |

It also reports the legacy packet's own declared `source_hash` and `evidence_packet_hash`,
its `source_origin` and truncation state, and whether R1 (full cached extraction) and R3
(packet source) were identical for that run.

## Dimensions

### 1. Source equivalence
Hash proof, as above, across all four representations.

### 2. Legacy outcome
Raw writer hash and word count · post-rewrite hash and word count · whether the rewrite ran
and whether it changed content · word delta · gate result · degraded stages · `should_block`
· review clean · fact-check status · final disposition · slug.

### 3. Shadow outcome
Stage hashes, ACCEPT/HOLD decision, source hash, schema version — read from a Phase-1 shadow
run's `MANIFEST.json`.

### 4. Grounding
Reported **separately, never merged**, because the two systems measure different things:

- **Legacy** has no source-relative audit of the finished article. It has `grounding_status`
  and `grounding_violations` on the persisted brief (planner evidence-candidate validation)
  and `fact_check_status` (world-relative verification).
- **Shadow** Writer Grounding is source-relative on the finished prose, classified
  `TRUE_UNSUPPORTED` / `TRUE_UNCERTAIN` / `LEGITIMATE_INTERPRETATION`.

Collapsing these into one "grounding score" would be a category error, so the harness prints
both and states the distinction in its own output.

### 5. Structure
Word count, paragraph count, section breaks, mean paragraph length — for legacy raw, legacy
post-rewrite, and shadow. **Structural only.** There is no `difflib`, no `SequenceMatcher`,
no ratio, and a test asserts their absence in executable code.

### 6. Legacy rule effects
Attribution **only where the evidence supports it**:

- **Rewrite — attributable by construction.** Raw writer output vs post-rewrite output
  isolates the rewrite stage exactly, because nothing else executes between the two captures.
- **Persona injection — detectable.** The captured writer prompt is scanned for persona
  markers (`YOU ARE `, `WRITE LIKE THIS PERSON`, `YOUR WOUND`, `AUTHORIZED PERSONAL HISTORY`,
  `YOUR CANON`), with the prompt size recorded.
- **Gate/review rule judges — explicitly NOT attributable.** The gate can rewrite content in
  place and the capture records only its result, not a pre/post pair. The harness returns
  `NOT_ATTRIBUTABLE_FROM_THIS_BUNDLE` and says why, rather than inferring.

## Blocked legacy runs are valid data

Production currently blocks 4 of 7 drafts and has published nothing since 2026-08-11. Blocked
runs are **not excluded**. Publication status is an *observed legacy outcome*, not an
eligibility filter.

The harness records the pairing — e.g. `legacy: BLOCKED` / `shadow: ACCEPT` — and carries an
explicit note that neither system is assumed correct merely because it blocked. Explaining
*why* the pair diverged is the analytical work of Phase 2; the harness supplies the evidence
for that explanation and does not pre-empt it.

## Fail-closed verdicts

| Verdict | Trigger |
|---|---|
| `CAPTURE_INVALID` | unsealed bundle, missing required artifact, or any manifest hash not matching the file on disk |
| `REJECTED_SOURCE_MISMATCH` | shadow and legacy sources differ |
| `LEGACY_ONLY` | valid bundle, no shadow lineage yet |
| `COMPARABLE` | valid bundle, source equivalence proven |

`BundleError` is raised for a missing directory or a bundle with no manifest.
