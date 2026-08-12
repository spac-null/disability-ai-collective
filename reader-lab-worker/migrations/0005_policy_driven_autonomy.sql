-- Reader Lab Policy-Driven Autonomy — migration 0005
-- Purely additive: one new table, new nullable/defaulted columns on
-- existing tables. No existing column dropped/retyped, no existing row
-- deleted, no response content touched. See
-- ../.claude/reader-lab-v0-design-2026-08-12.md ## 26 for the full design.
--
-- Purpose: replace hard-coded automation boundaries ("publication is
-- always manual", "reviewer assignment always needs Jascha") with an
-- explicit, versioned, auditable POLICY that governs them instead. The
-- boundary between automatic and human-required can now move by adding a
-- new policy row — never by another architecture change, and never by
-- silently loosening validation.

-- Append-only policy history. Exactly one row has is_active=1 at any
-- time (enforced in application code — src/policy.js's setActivePolicy
-- — never in SQL, since D1/SQLite has no partial-unique-index shortcut
-- worth the complexity here). Old rows are NEVER edited or deleted: a
-- run/round that recorded policy_version=3 must remain interpretable
-- forever, even after policy_version=4 becomes active.
CREATE TABLE IF NOT EXISTS calibration_policies (
  policy_version INTEGER PRIMARY KEY,

  -- Whether a policy-drafted round (next-round or additional-review) may
  -- publish itself once it passes every deterministic validation check.
  round_publication_policy TEXT NOT NULL DEFAULT 'human_approval'
    CHECK (round_publication_policy IN ('human_approval', 'shadow_automatic', 'automatic_if_valid')),

  -- Whether an EXISTING, approved (active_for_calibration=1, not
  -- revoked) reviewer may be auto-assigned to a policy-drafted round
  -- without Jascha picking reviewers by hand. Never governs inviting a
  -- NEW reviewer — that stays human-only regardless of this value (see
  -- production_promotion_policy's own fixed-value discipline below; the
  -- same discipline applies to reviewer ADMISSION, just not encoded as
  -- its own policy field since nothing here can override it).
  existing_reviewer_assignment_policy TEXT NOT NULL DEFAULT 'automatic_if_valid'
    CHECK (existing_reviewer_assignment_policy IN ('manual', 'automatic_if_valid')),

  -- Whether a contested/needs_more_reviewers item may automatically get
  -- further independent judgments from existing approved reviewers.
  -- 'disabled' = never attempt it. 'manual' = flag it, let Jascha act.
  -- 'automatic_if_valid' = attempt it, still subject to
  -- additional_reviewers_per_contested_item below and every other
  -- safeguard in src/additionalReview.js.
  additional_review_policy TEXT NOT NULL DEFAULT 'automatic_if_valid'
    CHECK (additional_review_policy IN ('disabled', 'manual', 'automatic_if_valid')),

  -- How many EXTRA independent reviewers to seek per contested/
  -- needs_more_reviewers item. NULL means "not yet decided" — the
  -- mechanism must then report NEEDS_POLICY_CONFIGURATION and do
  -- nothing, per the explicit instruction not to invent a consensus
  -- threshold on anyone's behalf. Seeded NULL in this migration for
  -- exactly that reason, even though additional_review_policy above
  -- defaults to 'automatic_if_valid' — "automatic when the policy CAN
  -- decide" and "the policy currently CAN decide" are deliberately kept
  -- as two separate facts.
  additional_reviewers_per_contested_item INTEGER,

  -- Infrastructure-ready, research-gated. No code path in this pass
  -- creates or tests a candidate system modification — this field exists
  -- so a future pass can turn that on via a NEW policy version, not a
  -- code change. Deliberately no CHECK constraint restricting future
  -- values (unlike the fields above, which already have real code paths
  -- for every legal value) — SQLite/D1 can't widen a CHECK without a
  -- table rebuild, and constraining this to today's one known value
  -- would force a rebuild the day it's actually needed.
  candidate_experiment_policy TEXT NOT NULL DEFAULT 'research_gated',

  -- Infrastructure-ready, deliberately inert. No fine-tuning code exists
  -- anywhere in this repo; this field is not wired to anything. Exists
  -- so a future sandbox-fine-tune pass is a new policy version, not a
  -- rule this migration hard-codes as permanently impossible.
  fine_tune_experiment_policy TEXT NOT NULL DEFAULT 'disabled',

  -- Fixed. Not a live decision this table is free to change — every
  -- CHECK below still only allows the one value that has ever been true
  -- for this project: promoting anything to production requires Jascha.
  -- Recorded as a real column (not hard-coded in application logic
  -- alone) so it is auditable per-policy-version like everything else,
  -- and so a future value would require an explicit, reviewable
  -- migration, never a silent application-code change.
  production_promotion_policy TEXT NOT NULL DEFAULT 'human_only'
    CHECK (production_promotion_policy = 'human_only'),

  is_active INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  created_by TEXT,
  notes TEXT
);

-- Seed: the initial safe policy, matching exactly the "CURRENT PRODUCTION
-- POLICY" already in force before this migration (## 24/## 25 already
-- shipped completion/export/analysis/evidence as unconditionally
-- automatic; publication has always required Jascha). This migration
-- does not change production behavior on its own — it only makes the
-- existing behavior a named, versioned row instead of an implicit fact.
INSERT INTO calibration_policies (
  policy_version, round_publication_policy, existing_reviewer_assignment_policy,
  additional_review_policy, additional_reviewers_per_contested_item,
  candidate_experiment_policy, fine_tune_experiment_policy, production_promotion_policy,
  is_active, created_at, created_by, notes
) VALUES (
  1, 'human_approval', 'automatic_if_valid',
  'automatic_if_valid', NULL,
  'research_gated', 'disabled', 'human_only',
  1, '2026-08-12T00:00:00.000Z', 'migration_0005_seed',
  'Initial policy: matches pre-existing production behavior exactly. additional_reviewers_per_contested_item is deliberately NULL (unconfigured) — the additional-review mechanism will report NEEDS_POLICY_CONFIGURATION rather than guess a threshold.'
);

-- Records which policy version governed each automatic decision, at the
-- moment it was made — never updated retroactively when the active
-- policy later changes, so a historical run/round remains interpretable
-- under the policy that actually produced it.
ALTER TABLE calibration_runs ADD COLUMN policy_version INTEGER;
ALTER TABLE rounds ADD COLUMN policy_version INTEGER;

-- Generalizes the reviewer pool beyond "not revoked". A reviewer with
-- active_for_calibration=0 remains a valid, non-revoked reviewer (their
-- past responses are untouched, their invitation still works) but is
-- simply not offered to any automatic assignment mechanism — the
-- distinction between "this person's account still works" and "the
-- system should keep giving them more work automatically" that
-- `revoked` alone can't express. max_items_per_round is a per-reviewer,
-- optional cap (NULL = no cap) — deliberately no cooldown/scheduling
-- field yet, per the explicit instruction to avoid over-engineering
-- quotas before there is any real multi-reviewer volume to tune against.
ALTER TABLE invitations ADD COLUMN active_for_calibration INTEGER NOT NULL DEFAULT 1;
ALTER TABLE invitations ADD COLUMN max_items_per_round INTEGER;

-- Additional-review rounds are drafted from an existing round's contested/
-- needs_more_reviewers items, using fresh item rows with duplicated
-- content (publishRound always mints a new item_id — see publish.js —
-- so this is never a rewrite of the original round's own items). This
-- column records that provenance so a round's ancestry is queryable
-- without parsing free text: which round (if any) this one was drafted
-- in response to, and how many such hops deep it is (generation 0 = not
-- an additional-review round at all; capped at 1 by
-- src/additionalReview.js as a simple, explicit infinite-loop guard —
-- see its own comment for why a second automatic hop escalates to a
-- human action instead of drafting a third round).
ALTER TABLE rounds ADD COLUMN additional_review_of_round_id TEXT REFERENCES rounds(round_id);
ALTER TABLE rounds ADD COLUMN additional_review_generation INTEGER NOT NULL DEFAULT 0;
