# Eligible candidate pool

`calibration_candidates` (D1, migration `0004_calibration_orchestrator.sql`,
write path added `0006_candidate_bridge.sql`) is the **only** source
`prepare-next-round-v1` may ever select from — see
`../workflows/prepare-next-round-v1.md`. It started **empty** through the
whole first infrastructure pass, and correctly produced
`NEEDS_ELIGIBLE_CANDIDATES` for RL-2026-001 until it did:

> "For the first implementation, an empty/limited candidate pool is
> acceptable. If no eligible new candidate exists: the system should say
> `NEEDS_ELIGIBLE_CANDIDATES` rather than inventing one."

**Now has a real write path**, `../../reader-lab-worker/src/candidateIngestion.js`
(`POST /ops/calibration/candidates`, or `/admin` → Candidates as a
fallback) — see the design doc's `## 27` for the full design. RL-2026-002's
5 candidates were the first real ingestion, via
`../runner/prepare_calibration_candidates.py` run on Trident against real
production.

## Why this file, not seed data

Choosing what becomes an eligible Reader Lab candidate is a B2/CJ-2
research decision — which case, which failure class, which source, why
it's worth another human's independent read. The ingestion service below
never makes that decision itself; it only validates that a bundle
already deterministically states everything it claims (hashes,
provenance, `dataset_purpose`, explicit `eligible_for_reader_lab=true`)
and rejects it outright if not. The actual research judgment still
happens upstream, in whoever builds the source artifact — a human
research pass, as of RL-2026-002; `prepare-calibration-candidates-v1`
formalizes packaging that decision, never making a new one.

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

## Seeding it — now a real, canonical path

`src/candidateIngestion.js` is that "narrow, reviewed script" — never a
direct `INSERT` (idempotent by deterministic `candidate_id` + content
hash: identical resubmission is a no-op, same id with different content
fails closed, never silently overwritten), never this orchestrator
inventing a row on its own (it only ever reads rows this service wrote).
A round with genuinely nothing eligible still correctly reports
`NEEDS_ELIGIBLE_CANDIDATES` — not a bug to route around, still the
correct behavior when the pool really is empty.
