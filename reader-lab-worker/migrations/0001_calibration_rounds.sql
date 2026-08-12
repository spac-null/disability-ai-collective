-- Reader Lab Calibration Rounds — migration 0001
-- Design only, per .claude/reader-lab-v0-design-2026-08-12.md section 20.
-- NOT applied to any database (local or production) as of this commit.
-- Purely additive: does not touch any existing table's columns or data,
-- and every existing row remains valid (assignments.round_id is nullable,
-- so the pilot's own four pre-round assignments stay round_id = NULL,
-- deliberately not retroactively assigned to a round).

CREATE TABLE IF NOT EXISTS rounds (
  round_id TEXT PRIMARY KEY,                   -- e.g. "RL-2026-001"
  task_type TEXT NOT NULL,                      -- e.g. "factual_floor_v0"
  task_version TEXT NOT NULL,                   -- e.g. "v0.1"
  dataset_purpose TEXT NOT NULL
    CHECK (dataset_purpose IN
      ('pilot','development','blind_calibration','held_out_evaluation','contested')),
  created_at TEXT NOT NULL,                     -- ISO-8601 UTC
  frozen_at TEXT,                               -- null until the item set + assignments
                                                 -- are finalized; no new item/assignment
                                                 -- may reference this round after this is set
                                                 -- (enforced in application code, not SQL)
  reviewer_blind_to_model_output INTEGER NOT NULL DEFAULT 1,
  reviewer_blind_to_other_reviewers INTEGER NOT NULL DEFAULT 1,
  assistance_mode_required TEXT NOT NULL DEFAULT 'independent',
  dataset_disposition TEXT,                     -- null until a manual/editorial
                                                 -- adjudication pass sets it; never auto-set
  notes TEXT
);

-- Nullable and additive: every row that exists today (including the
-- pilot's own four assignments) stays valid with round_id = NULL.
ALTER TABLE assignments ADD COLUMN round_id TEXT REFERENCES rounds(round_id);

CREATE INDEX IF NOT EXISTS idx_assignments_round ON assignments(round_id);
