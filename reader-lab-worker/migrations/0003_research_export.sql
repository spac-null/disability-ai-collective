-- Reader Lab automatic completion + research export — migration 0003
-- Purely additive: new nullable columns + a new table. No existing
-- column dropped/retyped, no existing row deleted, no response content
-- touched. See ../.claude/reader-lab-v0-design-2026-08-12.md's
-- "routine operations automation" section for the full design.

-- Set once a round transitions published -> completed (every assignment
-- across every required reviewer answered). Application code
-- (publish.js's maybeCompleteRound) is the only writer, via a single
-- conditional UPDATE ... WHERE status = 'published', which is what makes
-- the transition atomic and idempotent — a replayed/concurrent trigger
-- that finds status already 'completed' simply changes zero rows.
ALTER TABLE rounds ADD COLUMN completed_at TEXT;

-- Frozen item order within a round. Nullable/additive — existing rows
-- (the pilot's own pre-round assignments, round_id IS NULL) are
-- unaffected. Set by publish.js's publishRound() from the manifest's
-- own item slot going forward.
ALTER TABLE assignments ADD COLUMN item_order INTEGER;

-- One-time backfill for RL-2026-001, which predates this column: the
-- slot -> item_id mapping below is not new inspection of anything --
-- it is the exact, already-public, already-independently-verified
-- mapping recorded in
-- .claude/reader-lab-handoff/RL-2026-001-publication-receipt.json at
-- publish time. No response/answer content is read or touched by this
-- backfill.
UPDATE assignments SET item_order = 1 WHERE round_id = 'RL-2026-001' AND item_id = 'ril_e01890e0-4a62-486b-85b4-c91fb38c6b44';
UPDATE assignments SET item_order = 2 WHERE round_id = 'RL-2026-001' AND item_id = 'ril_e08ba1e4-8e15-4ef0-8d2b-9f34f8ad4dd2';
UPDATE assignments SET item_order = 3 WHERE round_id = 'RL-2026-001' AND item_id = 'ril_9df9a4b6-cd47-4697-91ef-586fc28cc6b4';
UPDATE assignments SET item_order = 4 WHERE round_id = 'RL-2026-001' AND item_id = 'ril_ffc53c73-bf29-49fe-a1f2-946b81f07517';
UPDATE assignments SET item_order = 5 WHERE round_id = 'RL-2026-001' AND item_id = 'ril_2452d26c-f319-4dab-80c8-bcd1aa748c4e';

-- Canonical, credential-free research export snapshot. One row per
-- round; frozen once status = 'ready' (buildResearchExport in
-- researchExport.js never overwrites a 'ready' row — regenerating
-- requires an explicit administrative DELETE + retry, documented in
-- README.md, not a routine UI action). 'failed' rows carry error_detail
-- so the admin UI can show "EXPORT ERROR / RETRY AVAILABLE" without
-- losing the underlying (already-committed, already-immutable) reviewer
-- responses.
-- payload_json/content_sha256 are only set on a successful ('ready')
-- attempt; a 'failed' row carries error_detail instead and leaves those
-- two null. generated_at is always set — the time of the most recent
-- attempt, successful or not.
CREATE TABLE IF NOT EXISTS research_exports (
  round_id TEXT PRIMARY KEY REFERENCES rounds(round_id),
  export_version TEXT NOT NULL,
  payload_json TEXT,
  content_sha256 TEXT,
  generated_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ready',
  error_detail TEXT
);
