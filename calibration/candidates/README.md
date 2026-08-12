# Eligible candidate pool

`calibration_candidates` (D1, migration `0004_calibration_orchestrator.sql`)
is the **only** source `prepare-next-round-v1` may ever select from —
see `../workflows/prepare-next-round-v1.md`. It starts **empty** as of
this pass's first deployment, and stays empty until a deliberate,
separate research decision seeds it. This is not an oversight; it is the
explicit, correct v1 state:

> "For the first implementation, an empty/limited candidate pool is
> acceptable. If no eligible new candidate exists: the system should say
> `NEEDS_ELIGIBLE_CANDIDATES` rather than inventing one."

## Why this file, not seed data

Choosing what becomes an eligible Reader Lab candidate is a B2/CJ-2
research decision — which case, which failure class, which source, why
it's worth another human's independent read. This infrastructure pass
does not make that decision on anyone's behalf; it only builds the pipe
the decision flows through once someone (a future research pass, not
this one) makes it.

## Every row needs, at minimum

| Column | Meaning |
|---|---|
| `candidate_id` | stable ID, never reused |
| `source_snapshot` / `candidate_sentence` | exact frozen text |
| `source_snapshot_id` / `candidate_claim_id` | `sha256:...` content hashes |
| `provenance` | e.g. `"H09 (fresh-batch-1, engine M)"` |
| `dataset_purpose` | `pilot` \| `development` \| `blind_calibration` \| `contested` — **never** `held_out_evaluation` for anything meant to become `eligible_for_reader_lab = 1` |
| `internal_rationale` | why this candidate is worth another independent read |
| `machine_reference_json` | this candidate's already-known B2 R1/R2 state, if any (same shape as a `research_context.per_item` entry) |
| `eligible_for_reader_lab` | `0` by default; only an explicit, reviewed `1` makes it selectable |

## The fail-closed rule, enforced twice

`dataset_purpose = 'held_out_evaluation'` material must never enter
human calibration. This is checked **twice**, independently:

1. The Cloudflare Workflow step that builds `prepare_next_round`'s input
   (`calibrationWorkflow.js`) queries
   `WHERE eligible_for_reader_lab = 1 AND dataset_purpose != 'held_out_evaluation'`.
2. The Trident runner's own `run_prepare_next_round` (`calibration_runner.py`)
   re-checks every candidate it's handed and **fails the job** (does not
   silently drop the offending row and continue) if any
   `held_out_evaluation` material appears anyway — e.g. because of a
   future bug in step 1, or a manual `UPDATE calibration_candidates`
   that set both flags in a way step 1's query wouldn't anticipate.

Both checks existing independently is deliberate: a single point of
enforcement is a single point of failure for the one rule this whole
system exists to never violate.

## Seeding it (a future pass, not this one)

When a research decision is made to seed real candidates, do it via a
narrow, reviewed script or a direct `INSERT` — not by relaxing
`eligible_for_reader_lab`'s default, and not by this orchestrator
inventing rows on its own. Until then, `prepare-next-round-v1` reporting
`NEEDS_ELIGIBLE_CANDIDATES` after every completed round is the correct,
expected behavior — not a bug to route around.
