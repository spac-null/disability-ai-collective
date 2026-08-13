-- Reader Lab — B2 → Reader Lab candidate-pool bridge (additive).
--
-- Adds a real write path's supporting schema for calibration_candidates
-- (previously read-only from the orchestrator's point of view — see
-- calibration/candidates/README.md's own "seeding it, a future pass"
-- note) and the reconciliation columns needed to resume a calibration
-- run that stopped at NEEDS_ELIGIBLE_CANDIDATES once candidates exist.
-- See .claude/reader-lab-v0-design-2026-08-12.md's candidate-bridge
-- section for the full design.

-- Stable identity: candidate_id is derived deterministically from
-- candidate_claim_id (see src/candidateIngestion.js) — this index makes
-- that a real, enforced guarantee, not just an application convention.
-- A second attempt to ingest the exact same claim text always resolves
-- to the same row, never a duplicate.
CREATE UNIQUE INDEX idx_calibration_candidates_claim_id ON calibration_candidates(candidate_claim_id);

-- content_sha256 is the canonical hash of every ingestion-relevant field
-- (source_snapshot, candidate_sentence, provenance, dataset_purpose,
-- internal_rationale, machine_reference_json, eligible_for_reader_lab) —
-- computed the same way as everywhere else in this codebase
-- (src/publish.js's sortedStringify). A resubmission with an identical
-- hash is a no-op; a resubmission under the same candidate_claim_id with
-- a DIFFERENT hash is rejected outright — never silently overwritten.
ALTER TABLE calibration_candidates ADD COLUMN content_sha256 TEXT;

-- Audit trail: which authenticated path ingested this row, and who/what
-- as recorded by that path (a runner_id string for the machine path, an
-- Access-authenticated email for the admin-import fallback).
ALTER TABLE calibration_candidates ADD COLUMN ingested_via TEXT;
ALTER TABLE calibration_candidates ADD COLUMN ingestion_actor TEXT;

-- Reconciliation claim guard: when eligible candidates newly exist, a
-- calibration_runs row stuck at NEEDS_ELIGIBLE_CANDIDATES gets resumed by
-- a fresh run (armFreshCalibrationRun, calibrationOrchestrator.js) — the
-- exact same "create a new run from scratch" mechanism already used for
-- retrying a genuinely failed run. This column is set atomically at the
-- moment a stuck run is claimed for resumption, so a second reconciliation
-- pass (the hourly cron, or a second concurrent ingestion) can never
-- resume the same stuck run twice.
ALTER TABLE calibration_runs ADD COLUMN resumed_by_run_id TEXT;
