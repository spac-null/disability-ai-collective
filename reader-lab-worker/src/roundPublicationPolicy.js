/**
 * Crip Minds Reader Lab — policy-controlled round publication.
 *
 * The ONE place a policy-drafted round (next-round-v1 or
 * additional-review) is ever frozen/published/shadow-evaluated
 * automatically. Called once, right after `saveDraft()` creates such a
 * round, by src/calibrationWorkflow.js — never duplicated per draft
 * type, so "what does automatic_if_valid actually mean" has exactly one
 * implementation regardless of which mechanism produced the draft.
 *
 * Three policy values (src/policy.js's round_publication_policy),
 * three behaviors, same validation underneath every one:
 *
 *   human_approval     — do nothing. Round stays `draft`, exactly as
 *                         today. Jascha reviews/freezes/publishes by hand.
 *   shadow_automatic    — compute the FULL decision a policy of
 *                         automatic_if_valid would make (freeze, run
 *                         every real check) and RECORD it as an
 *                         artifact. Never calls publishRound. Lets the
 *                         cockpit show "the system would have published
 *                         this" before that gate is ever actually lifted.
 *   automatic_if_valid  — same computation; if it comes back valid,
 *                         actually publish, through the exact same
 *                         freezeRound/publishRound every human
 *                         publication uses. Never a shortcut path, never
 *                         a relaxed check.
 *
 * "Valid" for an AUTOMATIC decision is validateManifest()'s existing
 * hard checks PLUS one automation-specific requirement human publication
 * doesn't need: every assigned reviewer must be active_for_calibration
 * (not just non-revoked) — see migration 0005. A human publishing by
 * hand can still knowingly assign a reviewer who's merely inactive-for-
 * automation; the system publishing on its own may not.
 */

import { freezeRound, publishRound, ValidationError } from "./publish.js";
import { listActiveReviewerIds } from "./reviewerEligibility.js";
import { newId, nowIso, sha256Hex } from "./util.js";

async function recordDecisionArtifact(env, { roundId, runId, policyVersion, action, decision }) {
  const artifactId = newId("cart");
  const content = {
    round_id: roundId,
    policy_version: policyVersion,
    action,
    decided_at: nowIso(),
    ...decision,
  };
  const contentJson = JSON.stringify(content);
  const hash = await sha256Hex(contentJson);
  await env.DB.prepare(
    `INSERT INTO calibration_artifacts (artifact_id, artifact_type, round_id, run_id, content_json, content_sha256, created_at)
     VALUES (?, 'publication_policy_decision', ?, ?, ?, ?, ?)`
  )
    .bind(artifactId, roundId, runId || null, contentJson, hash, nowIso())
    .run();
  return artifactId;
}

export async function applyRoundPublicationPolicy(env, roundId, { policy, actor, runId } = {}) {
  const policyVersion = policy.policy_version;
  await env.DB.prepare("UPDATE rounds SET policy_version = ? WHERE round_id = ?").bind(policyVersion, roundId).run();

  if (policy.round_publication_policy === "human_approval") {
    return { action: "left_for_human", policy_version: policyVersion };
  }

  const draftRow = await env.DB.prepare("SELECT payload_json FROM round_drafts WHERE round_id = ?").bind(roundId).first();
  if (!draftRow) {
    // Nothing to do — most likely the round was already frozen/published
    // by a human between saveDraft() and this call. Never an error case
    // this function should fail loudly over.
    return { action: "no_draft_found", policy_version: policyVersion };
  }
  const manifest = JSON.parse(draftRow.payload_json);

  let freezeResult = null;
  let freezeError = null;
  try {
    freezeResult = await freezeRound(env, roundId, manifest, { actor });
  } catch (err) {
    freezeError = err instanceof ValidationError ? { errors: err.errors, warnings: err.warnings } : { errors: [String(err && err.message || err)] };
  }

  if (freezeError) {
    await recordDecisionArtifact(env, {
      roundId,
      runId,
      policyVersion,
      action: policy.round_publication_policy === "shadow_automatic" ? "shadow_recorded" : "left_for_human",
      decision: { would_publish: false, reason: "validation_failed", validation: freezeError },
    });
    return { action: "left_for_human", would_publish: false, reason: "validation_failed", policy_version: policyVersion };
  }

  // Automation-specific extra check: every reviewer assigned must be an
  // EXISTING APPROVED reviewer in the automation sense, not merely
  // non-revoked (validateManifest() already enforced non-revoked as a
  // hard error inside freezeRound above).
  const activeIds = new Set(await listActiveReviewerIds(env));
  const inactiveAssigned = manifest.reviewer_ids.filter((id) => !activeIds.has(id));
  const wouldPublish = inactiveAssigned.length === 0;
  const reason = wouldPublish ? null : `reviewer_not_active_for_calibration: ${inactiveAssigned.join(", ")}`;

  if (policy.round_publication_policy === "shadow_automatic") {
    await recordDecisionArtifact(env, {
      roundId,
      runId,
      policyVersion,
      action: "shadow_recorded",
      decision: {
        would_publish: wouldPublish,
        reason,
        selected_reviewer_ids: manifest.reviewer_ids,
        selected_item_count: manifest.items.length,
        manifest_sha256: freezeResult.manifestHash,
        validation_warnings: freezeResult.warnings,
      },
    });
    return { action: "shadow_recorded", would_publish: wouldPublish, reason, policy_version: policyVersion };
  }

  // automatic_if_valid
  if (!wouldPublish) {
    await recordDecisionArtifact(env, {
      roundId,
      runId,
      policyVersion,
      action: "left_for_human",
      decision: { would_publish: false, reason, selected_reviewer_ids: manifest.reviewer_ids },
    });
    return { action: "left_for_human", would_publish: false, reason, policy_version: policyVersion };
  }

  const { receipt } = await publishRound(env, roundId, { actor: "system:policy_automatic_publication" });
  await recordDecisionArtifact(env, {
    roundId,
    runId,
    policyVersion,
    action: "published_automatically",
    decision: {
      would_publish: true,
      selected_reviewer_ids: manifest.reviewer_ids,
      selected_item_count: manifest.items.length,
      manifest_sha256: receipt.manifest_sha256,
    },
  });
  return { action: "published_automatically", would_publish: true, policy_version: policyVersion, receipt };
}
