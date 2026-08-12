/**
 * Crip Minds Reader Lab — calibration policy (versioned, append-only).
 *
 * The single place any part of this system reads "is X automatic right
 * now?" or changes that answer. A policy version is never edited or
 * deleted once created — getActivePolicy always returns the one row
 * with is_active=1; setActivePolicy inserts a NEW row (inheriting every
 * field not explicitly overridden from the version it replaces) and
 * flips is_active in the same D1 batch, so there is never a moment with
 * zero or two active policies.
 *
 * Every automatic decision this system makes (arming a calibration run,
 * drafting an additional-review round, deciding whether to auto-publish)
 * must record the policy_version it read — never re-read "the current
 * policy" later and retroactively reinterpret an old decision under a
 * newer one.
 */

import { nowIso } from "./util.js";

export const ROUND_PUBLICATION_POLICIES = ["human_approval", "shadow_automatic", "automatic_if_valid"];
export const EXISTING_REVIEWER_ASSIGNMENT_POLICIES = ["manual", "automatic_if_valid"];
export const ADDITIONAL_REVIEW_POLICIES = ["disabled", "manual", "automatic_if_valid"];

// Fields this pass exposes for editing (via /admin/api/policy). The
// other two policy-table fields (candidate_experiment_policy,
// fine_tune_experiment_policy) are readable but not offered an editing
// control here — no code path consumes any value except the seeded
// defaults yet (see migration 0005's own comment), so exposing a control
// that changes them would let someone toggle a setting nothing acts on.
// production_promotion_policy is fixed by a CHECK constraint and is
// never accepted as an override here regardless.
const EDITABLE_FIELDS = [
  "round_publication_policy",
  "existing_reviewer_assignment_policy",
  "additional_review_policy",
  "additional_reviewers_per_contested_item",
];

export class PolicyValidationError extends Error {
  constructor(errors) {
    super("policy_validation_failed");
    this.errors = errors;
  }
}

export async function getActivePolicy(env) {
  const row = await env.DB.prepare("SELECT * FROM calibration_policies WHERE is_active = 1 LIMIT 1").first();
  if (!row) throw new Error("no_active_policy — calibration_policies has no is_active=1 row; migration 0005 seeds one and must never be skipped");
  return row;
}

export async function getPolicyVersion(env, policyVersion) {
  return env.DB.prepare("SELECT * FROM calibration_policies WHERE policy_version = ?").bind(policyVersion).first();
}

export async function listPolicyHistory(env) {
  const rows = await env.DB.prepare("SELECT * FROM calibration_policies ORDER BY policy_version DESC").all();
  return rows.results;
}

function validateOverrides(overrides) {
  const errors = [];
  if (overrides.round_publication_policy !== undefined && !ROUND_PUBLICATION_POLICIES.includes(overrides.round_publication_policy)) {
    errors.push(`round_publication_policy must be one of ${ROUND_PUBLICATION_POLICIES.join("/")}`);
  }
  if (
    overrides.existing_reviewer_assignment_policy !== undefined &&
    !EXISTING_REVIEWER_ASSIGNMENT_POLICIES.includes(overrides.existing_reviewer_assignment_policy)
  ) {
    errors.push(`existing_reviewer_assignment_policy must be one of ${EXISTING_REVIEWER_ASSIGNMENT_POLICIES.join("/")}`);
  }
  if (overrides.additional_review_policy !== undefined && !ADDITIONAL_REVIEW_POLICIES.includes(overrides.additional_review_policy)) {
    errors.push(`additional_review_policy must be one of ${ADDITIONAL_REVIEW_POLICIES.join("/")}`);
  }
  if (
    overrides.additional_reviewers_per_contested_item !== undefined &&
    overrides.additional_reviewers_per_contested_item !== null &&
    !(Number.isInteger(overrides.additional_reviewers_per_contested_item) && overrides.additional_reviewers_per_contested_item > 0)
  ) {
    errors.push("additional_reviewers_per_contested_item must be a positive integer or null");
  }
  return errors;
}

// Creates policy_version = (current max + 1), copying every field from
// the currently-active version except whatever is explicitly overridden.
// Never touches an existing row. Returns the new row.
export async function setActivePolicy(env, overrides, { actor, notes } = {}) {
  const fieldErrors = validateOverrides(overrides || {});
  if (fieldErrors.length) throw new PolicyValidationError(fieldErrors);
  if (Object.prototype.hasOwnProperty.call(overrides || {}, "production_promotion_policy")) {
    throw new PolicyValidationError(["production_promotion_policy cannot be changed — production promotion is human-only by fixed design, not a policy setting"]);
  }

  const current = await getActivePolicy(env);
  const next = { ...current };
  for (const field of EDITABLE_FIELDS) {
    if (overrides && Object.prototype.hasOwnProperty.call(overrides, field)) {
      next[field] = overrides[field];
    }
  }

  const newVersion = current.policy_version + 1;
  const now = nowIso();
  await env.DB.batch([
    env.DB.prepare("UPDATE calibration_policies SET is_active = 0 WHERE is_active = 1"),
    env.DB.prepare(
      `INSERT INTO calibration_policies (
        policy_version, round_publication_policy, existing_reviewer_assignment_policy,
        additional_review_policy, additional_reviewers_per_contested_item,
        candidate_experiment_policy, fine_tune_experiment_policy, production_promotion_policy,
        is_active, created_at, created_by, notes
      ) VALUES (?,?,?,?,?,?,?,?,1,?,?,?)`
    ).bind(
      newVersion,
      next.round_publication_policy,
      next.existing_reviewer_assignment_policy,
      next.additional_review_policy,
      next.additional_reviewers_per_contested_item,
      next.candidate_experiment_policy,
      next.fine_tune_experiment_policy,
      next.production_promotion_policy,
      now,
      actor || null,
      notes || null
    ),
  ]);

  return getPolicyVersion(env, newVersion);
}
