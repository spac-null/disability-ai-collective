-- Reader Lab admin control plane — migration 0002
-- Purely additive: new nullable columns on existing tables (no CHECK
-- constraints added to items/rounds — SQLite/D1 requires a full table
-- rebuild to add one to a table that already has rows, which is more
-- risk than this pass needs; validity for the new columns is enforced
-- in application code, in publish.js). No existing column dropped or
-- retyped, no existing row deleted. See
-- ../.claude/reader-lab-v0-design-2026-08-12.md admin-control-plane
-- section for the full design this supports.

-- Admin-only per-item fields. Never sent to any reviewer-facing route
-- (handleApiSession's toPublicItem() does not select these columns).
ALTER TABLE items ADD COLUMN internal_note TEXT;
ALTER TABLE items ADD COLUMN provenance TEXT;

-- Round lifecycle: draft -> review -> frozen -> published -> completed
-- (archived is a later, still-manual disposition). No CHECK constraint
-- (see note above) — publish.js is the single place that enforces valid
-- transitions.
ALTER TABLE rounds ADD COLUMN status TEXT NOT NULL DEFAULT 'draft';
ALTER TABLE rounds ADD COLUMN published_at TEXT;
ALTER TABLE rounds ADD COLUMN manifest_sha256 TEXT;
ALTER TABLE rounds ADD COLUMN source TEXT NOT NULL DEFAULT 'admin_ui';
ALTER TABLE rounds ADD COLUMN research_question TEXT;
ALTER TABLE rounds ADD COLUMN dataset_purpose_note TEXT;

-- One-time backfill for rounds that predate this column. RL-2026-001 is
-- already live (frozen_at set, both reviewers assigned) — it was
-- published by hand via a direct D1 write, not through any Worker route,
-- which is exactly the ad hoc path this control plane replaces going
-- forward. Its own content/responses are NOT touched here — only the
-- new status/source columns this round didn't have before are backfilled
-- to reflect what already happened.
UPDATE rounds SET status = 'published', source = 'import'
  WHERE frozen_at IS NOT NULL AND status = 'draft';

-- Draft manifest storage while a round is authored/reviewed/frozen,
-- before anything is written to items/assignments. Removed by
-- publish.js once the round is actually published — items/assignments/
-- rounds are the durable source of truth after that, per the existing
-- schema's own "never store a join redundantly" convention.
CREATE TABLE IF NOT EXISTS round_drafts (
  round_id TEXT PRIMARY KEY REFERENCES rounds(round_id),
  payload_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- Minimal durable audit trail for admin actions (round created/frozen/
-- published, reviewer created/revoked/reactivated, manifest imported).
-- Never stores secrets — actor is an Access-authenticated email or the
-- literal string "admin_token" for machine calls, never a credential.
CREATE TABLE IF NOT EXISTS audit_log (
  id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT,
  actor TEXT,
  created_at TEXT NOT NULL,
  content_hash TEXT,
  detail_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
