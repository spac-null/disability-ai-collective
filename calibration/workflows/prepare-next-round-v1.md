# prepare-next-round-v1

**Job type:** `prepare_next_round` · **Version:** `v1` · **Registered:** 2026-08-12

## Purpose

Given a completed round's analysis, produce a **draft** for the next
Reader Lab round — never a publish action. This job cannot make a round
live; only `POST /admin/api/rounds/:id/publish` (Cloudflare
Access-authenticated, i.e. Jascha) can do that, per `## 21` of the
design doc. If this job's output is ever consumed automatically by
anything that publishes without a human step, that is a violation of
this workflow's own contract, not an intended use of it.

## Why this is fully deterministic in v1

`## 19` of the design doc requires an explicit, server-side eligible
candidate pool (`calibration_candidates` table) — no candidate may ever
be invented by a selector, model-assisted or otherwise. **The pool is
empty as of this version's first deployment**, per `## 19`'s own
explicit instruction that an empty pool is an acceptable v1 state. With
nothing eligible to select from, there is nothing for a model to
meaningfully rank or choose between yet — so v1 has no model call at
all. A future version, once the pool is non-empty, may add a
model-assisted ranking step (e.g. "which contested case most deserves a
follow-up candidate") — that is a new version (`v2`), not a silent
change to this one.

## Input contract

```json
{
  "round_id": "RL-2026-NNN",
  "analysis": { "...": "this round's analyze-human-round-v1 output, verbatim" },
  "eligible_candidates": [
    {
      "candidate_id": "string",
      "source_snapshot": "string", "candidate_sentence": "string",
      "source_snapshot_id": "sha256:...", "candidate_claim_id": "sha256:...",
      "provenance": "string", "dataset_purpose": "string",
      "internal_rationale": "string", "machine_reference_json": "string|null"
    }
  ],
  "active_reviewer_ids": ["reviewer_parent_a", "reviewer_parent_b", "..."]
}
```

`eligible_candidates` is pre-filtered by the caller (the Cloudflare
Workflow step, `src/calibrationWorkflow.js`) to
`WHERE eligible_for_reader_lab = 1` — this job never queries
`calibration_candidates` itself and never re-derives eligibility; it
trusts the caller's filter and additionally asserts, as a hard,
fail-closed check, that **no candidate in this list has
`dataset_purpose = 'held_out_evaluation'`** — if one is found, the job
fails closed (`error`, does not produce a draft) rather than silently
dropping it or silently using it. A held-out case entering human
calibration is exactly the leak `## 11` of the design doc exists to
prevent; failing loudly here is the intended behavior, not a bug to
route around.

## Output contract

Exactly one of:

```json
{ "status": "NEEDS_ELIGIBLE_CANDIDATES", "round_id": "RL-2026-NNN", "reason": "eligible_candidates was empty" }
```

```json
{
  "status": "DRAFT_READY",
  "round_id": "RL-2026-NNN",
  "draft": {
    "dataset_purpose": "development | blind_calibration | contested",
    "reviewer_ids": ["..."],
    "items": [ { "slot": 1, "source_snapshot": "...", "candidate_sentence": "...", "internal_note": "...", "provenance": "..." } ],
    "selection_rationale": "string — which candidates were chosen and why (e.g. 'candidate X targets the contested item from RL-2026-001, slot 2')"
  }
}
```

A `DRAFT_READY` output is consumed by the Cloudflare Workflow step,
which calls the existing `saveDraft()` in `publish.js` (the exact same
shared function the admin UI's own draft-authoring screen uses — no
second draft-creation path) to create a **draft-status** round. It is
never frozen or published by this job or by the Workflow — that remains
a `WAITING_FOR_HUMAN_APPROVAL` state until Jascha reviews it in
`/admin` and explicitly freezes/publishes, exactly like any other draft.

## Selection rule (v1, deterministic)

1. If `eligible_candidates` is empty → `NEEDS_ELIGIBLE_CANDIDATES`.
   Stop. Do not degrade into inventing a placeholder candidate.
2. Otherwise, prefer candidates whose `internal_rationale` references a
   `contested` or `needs_more_reviewers` item from the input `analysis`
   (simple substring/tag match, not semantic inference) — these get
   priority in `selection_rationale`. Fall back to any remaining
   eligible candidates, in `created_at` order, to fill up to a 5-item
   round (matching `## 20.7`'s existing default reviewer-load target).
3. `reviewer_ids` defaults to every reviewer in `active_reviewer_ids`
   that is not revoked — no policy yet exists for assigning a subset (see
   `## 20` of this pass's own design section on reviewer-pool support);
   v1 assigns every active reviewer to every drafted round, matching
   RL-2026-001's own precedent.
4. `dataset_purpose` defaults to `development` unless every selected
   candidate explicitly declares a different purpose in common — never
   inferred, never defaulted to `blind_calibration`/`contested` by
   guesswork.

## Provenance

SHA256 of this file is recorded in `calibration_workflow_versions` at
deploy time. See the design doc's calibration-orchestrator section for
the exact value as of deployment.
