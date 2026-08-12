-- Crip Minds Reader Lab v0 — D1 schema
-- Server-side authoritative storage. Client never supplies canonical
-- source/candidate text — only ever reads it back via item_id.

CREATE TABLE IF NOT EXISTS invitations (
  reviewer_id TEXT PRIMARY KEY,               -- e.g. "reader_003"
  token_hash TEXT NOT NULL UNIQUE,             -- sha256 of the opaque invitation token — RAW TOKEN NEVER STORED
  contact_channel TEXT,                        -- optional, e.g. an email; never required
  created_at TEXT NOT NULL,                    -- ISO-8601 UTC
  expires_at TEXT,                             -- ISO-8601 UTC, nullable = no expiry
  revoked INTEGER NOT NULL DEFAULT 0,          -- 0/1 — revoking also invalidates every session for this reviewer
  practice_completed INTEGER NOT NULL DEFAULT 0,
  assistance_declaration_accepted_at TEXT
);

-- A session is minted from a valid invitation token and lives in a
-- cookie from then on — the invitation token itself never appears in
-- any URL, request body, or response body after this row is created.
CREATE TABLE IF NOT EXISTS sessions (
  session_id_hash TEXT PRIMARY KEY,            -- sha256 of the opaque session id — RAW SESSION ID NEVER STORED
  reviewer_id TEXT NOT NULL REFERENCES invitations(reviewer_id),
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
  item_id TEXT PRIMARY KEY,                    -- e.g. "ril_..."
  task_version TEXT NOT NULL,
  source_snapshot TEXT NOT NULL,               -- frozen excerpt, server-authoritative
  source_snapshot_id TEXT NOT NULL,            -- sha256 of source_snapshot
  candidate_sentence TEXT NOT NULL,
  candidate_claim_id TEXT NOT NULL,            -- sha256 of candidate_sentence
  dataset_bucket TEXT NOT NULL DEFAULT 'pilot' -- development|blind_calibration|contested|pilot
    CHECK (dataset_bucket IN ('development','blind_calibration','contested','pilot')),
  is_practice INTEGER NOT NULL DEFAULT 0,      -- 0/1
  practice_explanation TEXT,                   -- shown only if is_practice=1; never sent for real items
  practice_correct_answer TEXT,                -- shown only if is_practice=1; never sent for real items
  created_at TEXT NOT NULL
);

-- Which items are assigned to which reviewer, and whether served/answered yet.
-- This is the independence boundary: a row here is invisible to every
-- other reviewer_id, always.
CREATE TABLE IF NOT EXISTS assignments (
  assignment_id TEXT PRIMARY KEY,
  reviewer_id TEXT NOT NULL REFERENCES invitations(reviewer_id),
  item_id TEXT NOT NULL REFERENCES items(item_id),
  assignment_version TEXT NOT NULL,
  served_at TEXT,                              -- set when first shown to the reviewer
  answered_at TEXT,                            -- set when a response is first recorded (immutable after that)
  created_at TEXT NOT NULL,
  UNIQUE (reviewer_id, item_id)
);

CREATE TABLE IF NOT EXISTS responses (
  response_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  reviewer_id TEXT NOT NULL REFERENCES invitations(reviewer_id),
  item_id TEXT NOT NULL REFERENCES items(item_id),
  task_type TEXT NOT NULL DEFAULT 'factual_floor_v0',
  task_version TEXT NOT NULL,
  assignment_version TEXT NOT NULL,
  source_snapshot_id TEXT NOT NULL,
  candidate_claim_id TEXT NOT NULL,
  selected_public_response TEXT NOT NULL
    CHECK (selected_public_response IN
      ('source_supports','reading_of_source','adds_unestablished','not_sure')),
  internal_normalized_response TEXT NOT NULL
    CHECK (internal_normalized_response IN
      ('source_established','interpretive_only','unsupported_factual_dependency','uncertain')),
  confidence TEXT
    CHECK (confidence IS NULL OR confidence IN ('pretty_sure','somewhat_sure','not_very_sure')),
  comment TEXT,                                -- capped app-side at 500 chars
  timestamp TEXT NOT NULL,                     -- first-submission time; immutable after insert (see app logic)
  reviewer_blind_to_model_output INTEGER NOT NULL DEFAULT 1,
  reviewer_blind_to_other_reviewers INTEGER NOT NULL DEFAULT 1,
  assistance_declared TEXT NOT NULL DEFAULT 'independent',
  practice_or_real TEXT NOT NULL CHECK (practice_or_real IN ('practice','real')),
  client_interface_version TEXT NOT NULL,
  UNIQUE (reviewer_id, item_id)                -- one response per reviewer per item — first write wins, never overwritten
);

-- Minimal, generously-thresholded abuse counter. Bucketed by a fixed
-- window (computed in application code, not SQL date functions) so a
-- flood of invalid attempts (guessed tokens, wrong admin token) can be
-- capped without adding any external dependency or CAPTCHA.
CREATE TABLE IF NOT EXISTS rate_limit_events (
  bucket_key TEXT NOT NULL,
  window_start INTEGER NOT NULL,               -- unix seconds, floored to the window size
  count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (bucket_key, window_start)
);

CREATE INDEX IF NOT EXISTS idx_assignments_reviewer ON assignments(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_responses_item ON responses(item_id);
CREATE INDEX IF NOT EXISTS idx_sessions_reviewer ON sessions(reviewer_id);
