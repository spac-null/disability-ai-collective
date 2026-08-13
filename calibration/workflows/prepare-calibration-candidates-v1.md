# prepare-calibration-candidates-v1

**Registered:** 2026-08-13 · Not a Cloudflare Workflow job type — see
"Why this runs outside the claim/complete queue" below.

## Purpose

Turn an already-frozen B2/CJ-2 research artifact into a structured
**candidate ingestion bundle** for `POST /ops/calibration/candidates`
(`src/candidateIngestion.js`). It never invents content, never re-runs
any B2/CJ-2 stage, and never decides on its own whether a case is "good
enough" to become eligible — that research judgment happens upstream,
by whoever built the source artifact (a human research pass today; a
future automated selection step later, if one is ever built). This
workflow's job is narrower: package what's already been decided into the
exact shape the ingestion endpoint validates, with enough provenance that
a rejection is always explainable.

## Why this runs outside the claim/complete queue

`analyze-human-round-v1`/`prepare-next-round-v1` are Cloudflare Workflow
job types because a concrete Worker-side event (a round completing)
creates the job for the runner to claim. There is no equivalent trigger
here — nothing in the Worker knows a B2 research pass finished, and
nothing should have to poll for that. This workflow is instead a plain
script (`calibration/runner/prepare_calibration_candidates.py`) that
**pushes** a bundle directly to the Worker over the same
`CALIBRATION_RUNNER_TOKEN`-authenticated HTTPS path the runner already
uses for everything else — invoked whenever a frozen research artifact
is ready (today: manually or via a small cron; later: from the tail end
of whatever produces the frozen artifact, once one exists as a running
pipeline rather than an ad hoc script).

## Why this is deterministic, not model-assisted

Every field this workflow reads (`dataset_purpose`, `eligible_for_reader_lab`,
`source_snapshot`/`candidate_sentence`, `provenance`, `machine_role`/
`machine_support`/etc.) must already be present, explicit, and
unambiguous in the source artifact. If any required field is missing or
a value this workflow doesn't recognize (e.g. `dataset_purpose` is
absent, or `eligible_for_reader_lab` isn't literally `true`/`false`),
the script reports **`NEEDS_HUMAN_ACTION`** for that specific record and
excludes it from the bundle — it never guesses, and it never lets one
bad record block the rest of a batch. `held_out_evaluation` material is
rejected outright, the same fail-closed rule enforced independently at
every other layer of this system (`calibrationWorkflow.js`'s SQL filter,
`calibration_runner.py`'s `run_prepare_next_round`, and now a third time
here, plus a fourth time server-side in `candidateIngestion.js` itself —
belt and suspenders on the one rule this whole system exists to never
violate).

## Input

A local JSON file: an array of records shaped like
`calibration/candidates/*-candidates.json` (see
`calibration/candidates/README.md` for the per-row contract). Each
record must already state, explicitly:

- `source_snapshot`, `candidate_sentence` (exact frozen text)
- `provenance` (non-empty string — which B2/CJ-2 run/case this came from)
- `dataset_purpose` (one of `pilot`/`development`/`blind_calibration`/
  `contested` — never `held_out_evaluation`)
- an explicit `eligible_for_reader_lab` (`true` or `false` — this script
  passes through whatever the record already states; it never computes
  or overrides this value itself, matching the standing instruction that
  an AI never decides dataset eligibility freely)

Optional: `source_snapshot_id`/`candidate_claim_id` (recomputed and
verified server-side regardless — see `candidateIngestion.js`),
`internal_rationale`, `machine_role`/`machine_support`/`machine_problems`/
`machine_why`/`researcher_side_family_criteria_met` (folded into
`machine_reference_json`).

## Output — the ingestion bundle

```json
{
  "workflow_name": "prepare-calibration-candidates",
  "workflow_version": "v1",
  "source_experiment_ids": ["cj2-fresh-batch-1", "cj2-reference-probe-1"],
  "selection_rationale": "string — which records were included/excluded and why",
  "candidates": [
    {
      "source_snapshot": "...", "candidate_sentence": "...",
      "source_snapshot_id": "sha256:...", "candidate_claim_id": "sha256:...",
      "provenance": "...", "dataset_purpose": "development",
      "eligible_for_reader_lab": true,
      "internal_rationale": "...",
      "machine_reference_json": { "machine_role": "...", "machine_support": "...", "...": "..." }
    }
  ],
  "excluded": [
    { "provenance": "...", "reason": "NEEDS_HUMAN_ACTION: missing dataset_purpose" }
  ]
}
```

Posted as-is to `POST /ops/calibration/candidates`
(`X-Calibration-Runner-Token`). The Worker's own `candidateIngestion.js`
re-validates everything from scratch — this script's own checks exist to
produce a clean, explainable bundle and an early, useful error message,
never as the actual security/correctness boundary.

## What this workflow never does

- Invents a candidate, a hash, or a provenance string.
- Overrides a record's own stated `dataset_purpose`/`eligible_for_reader_lab`.
- Re-runs D0/C0/R1/R2/repair/Stage C or any other B2/CJ-2 stage.
- Retries a rejected record with relaxed criteria — a rejection is
  reported once, with a reason, and stays rejected until a human fixes
  the source artifact.
