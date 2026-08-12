-- Reader Lab Calibration Orchestrator — migration 0004
-- Purely additive: five new tables, no existing table touched. See
-- ../.claude/reader-lab-v0-design-2026-08-12.md's calibration-orchestrator
-- section for the full design.
--
-- Durable-state principle this migration exists to enforce: the running
-- state of a calibration cycle (what round, what step, what evidence)
-- lives HERE — production D1 — not in a Claude conversation, not in
-- Jascha's memory, not in a terminal history. The local git repo remains
-- canonical for SOURCE CODE (workflow definitions, this schema, the
-- runner script) and research DESIGN — it is not where a running
-- instance's state lives.

-- Registry of deployable workflow definitions (calibration/workflows/*.md
-- in the repo — this table records which versions exist and their
-- content hash; it does not duplicate the definition text itself, so
-- there is exactly one place — the repo file — that can drift, and this
-- table can always be re-verified against it).
CREATE TABLE IF NOT EXISTS calibration_workflow_versions (
  name TEXT NOT NULL,                -- e.g. "analyze-human-round"
  version TEXT NOT NULL,              -- e.g. "v1"
  sha256 TEXT NOT NULL,                -- hash of calibration/workflows/<name>-<version>.md
  definition_path TEXT NOT NULL,
  input_contract TEXT,                 -- short human-readable description
  output_contract TEXT,
  registered_at TEXT NOT NULL,
  PRIMARY KEY (name, version)
);

-- One row per Cloudflare Workflow instance — one instance per completed
-- Reader Lab round's calibration cycle. idempotency_key is derived from
-- round_id + research_export_hash + workflow_version (see
-- calibrationWorkflow.js's armCalibrationRun) and is UNIQUE, which is
-- what actually prevents a duplicate completion/reconciliation event
-- from ever producing two runs for the same round+export+version —
-- belt-and-suspenders alongside the Workflow platform's own
-- create()-throws-on-duplicate-id behavior (workflow_instance_id is
-- literally set to this same key).
CREATE TABLE IF NOT EXISTS calibration_runs (
  run_id TEXT PRIMARY KEY,
  round_id TEXT NOT NULL,
  research_export_hash TEXT NOT NULL,
  workflow_version TEXT NOT NULL,
  workflow_instance_id TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'queued',
    -- queued -> analysis_pending -> analysis_running -> analysis_complete
    -- -> evidence_updated -> next_round_pending -> next_round_running ->
    -- next_round_draft_ready | needs_eligible_candidates -> completed
    -- (or: failed, at any step)
  current_step TEXT,
  created_at TEXT NOT NULL,
  started_at TEXT,
  completed_at TEXT,
  error TEXT,
  analysis_artifact_id TEXT,
  next_round_draft_artifact_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_calibration_runs_round ON calibration_runs(round_id);

-- The claimable unit the Trident runner polls for. One row per attempt —
-- a retried job (after a 'failed' attempt) is a NEW row, never a mutated
-- one, so the attempt history stays visible rather than being
-- overwritten in place.
CREATE TABLE IF NOT EXISTS calibration_jobs (
  job_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES calibration_runs(run_id),
  job_type TEXT NOT NULL,              -- 'analyze_human_round' | 'prepare_next_round'
  workflow_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
    -- pending -> claimed -> completed | failed
  input_json TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  claimed_by TEXT,
  claimed_at TEXT,
  lease_expires_at TEXT,
  completed_at TEXT,
  result_json TEXT,
  result_hash TEXT,
  error TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_calibration_jobs_run ON calibration_jobs(run_id);
CREATE INDEX IF NOT EXISTS idx_calibration_jobs_status ON calibration_jobs(status);

-- Durable artifact storage: research_context (per-round, admin/research-only,
-- frozen at round publication — see backfill for RL-2026-001), analysis
-- (analyze-human-round-v1's structured evidence map), next_round_draft
-- (prepare-next-round-v1's output — a DRAFT reference only, never a
-- publish action). Recomputable/versioned, per ## 17 — unlike
-- research_exports, these are NOT treated as immutable-once-generated;
-- a re-run creates a new row, the old one is never deleted.
CREATE TABLE IF NOT EXISTS calibration_artifacts (
  artifact_id TEXT PRIMARY KEY,
  artifact_type TEXT NOT NULL,          -- 'research_context' | 'analysis' | 'next_round_draft'
  round_id TEXT NOT NULL,
  run_id TEXT,                          -- null for research_context (frozen at publication, before any run exists)
  workflow_version TEXT,
  content_json TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_calibration_artifacts_round ON calibration_artifacts(round_id, artifact_type);

-- Eligible candidate pool for prepare-next-round-v1 (## 19). Starts
-- EMPTY in this migration and stays empty until a deliberate, separate
-- research decision seeds it — this pass does not invent or select any
-- source/candidate pair. Only eligible_for_reader_lab=1 rows may ever be
-- selected; dataset_purpose='held_out_evaluation' rows must never be
-- silently promoted regardless of this flag (enforced in application
-- code, not just this schema — see prepare-next-round-v1.md).
CREATE TABLE IF NOT EXISTS calibration_candidates (
  candidate_id TEXT PRIMARY KEY,
  source_snapshot TEXT NOT NULL,
  candidate_sentence TEXT NOT NULL,
  source_snapshot_id TEXT NOT NULL,
  candidate_claim_id TEXT NOT NULL,
  provenance TEXT,
  dataset_purpose TEXT NOT NULL,
  internal_rationale TEXT,
  machine_reference_json TEXT,
  eligible_for_reader_lab INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
