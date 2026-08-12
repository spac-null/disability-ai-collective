/**
 * Crip Minds Reader Lab — automatic additional review.
 *
 * After a round is analyzed (analyze-human-round-v1), some items may
 * come back `contested` (2+ reviewers disagreed) or
 * `needs_more_reviewers` (this round's own research_context flagged the
 * item as under-reviewed). This module decides — under policy, never by
 * inventing a threshold — whether to automatically seek further
 * independent judgment on those items from EXISTING approved reviewers,
 * without ever touching the original round's own items/assignments/
 * responses (published rounds are immutable; this always creates a NEW
 * round instead).
 *
 * Safeguards, all enforced here, none of them optional:
 *  - never assigns a reviewer who already judged the exact same content
 *    (by candidate_claim_id, not item_id — a follow-up item is always a
 *    fresh row with a fresh item_id; see reviewerEligibility.js)
 *  - never reuses the original round's items/assignments — always a new
 *    round, so the original judgments are never at risk of being edited,
 *    overwritten, or reinterpreted
 *  - bounded — an additional-review round is itself capped at generation
 *    1; if IT still shows contested/needs_more_reviewers items after its
 *    own analysis, this module escalates to a human rather than
 *    automatically spawning a third round
 *  - if the policy hasn't decided how many extra reviewers to seek, or
 *    there aren't enough eligible existing reviewers to fulfill that
 *    number, this reports a clean status and does nothing else — it
 *    never guesses a number or partially assigns to "make automation
 *    continue"
 */

import { saveDraft } from "./publish.js";
import { selectReviewersForBatch } from "./reviewerEligibility.js";

const ESCALATABLE_DISPOSITIONS = ["contested", "needs_more_reviewers"];

// An additional-review round (generation 1) whose own analysis still
// shows contested/needs_more_reviewers items stops here — this module
// will not automatically draft a generation-2 round from it. This is
// the explicit, simple loop bound the design calls for; raising it is a
// deliberate future policy decision, not something this pass encodes as
// a policy field (there is no evidence yet that one hop is ever
// insufficient, and inventing a second knob before that evidence exists
// would be exactly the kind of unearned methodology this project avoids
// elsewhere).
export const MAX_ADDITIONAL_REVIEW_GENERATION = 1;

function summarizeFlagged(items) {
  return items.map((i) => ({ item_id: i.item_id, slot: i.slot, disposition: i.disposition }));
}

export async function planAdditionalReview(env, { roundId, analysis, policy, nextRoundId, actor }) {
  if (policy.additional_review_policy === "disabled") {
    return { status: "DISABLED" };
  }

  const flaggedItems = (analysis.items || []).filter((item) => ESCALATABLE_DISPOSITIONS.includes(item.disposition));
  if (flaggedItems.length === 0) {
    return { status: "NONE_NEEDED" };
  }

  if (policy.additional_review_policy === "manual") {
    return { status: "NEEDS_HUMAN_ACTION", reason: "additional_review_policy is 'manual'", flagged_items: summarizeFlagged(flaggedItems) };
  }

  // automatic_if_valid from here on — but "automatic" only for the
  // dimension the policy has actually decided. It has not decided a
  // count until additional_reviewers_per_contested_item is set.
  if (policy.additional_reviewers_per_contested_item == null) {
    return {
      status: "NEEDS_POLICY_CONFIGURATION",
      reason: "additional_reviewers_per_contested_item is not configured — no threshold is invented here",
      flagged_items: summarizeFlagged(flaggedItems),
    };
  }

  const originRound = await env.DB.prepare("SELECT additional_review_generation FROM rounds WHERE round_id = ?")
    .bind(roundId)
    .first();
  const generation = (originRound && originRound.additional_review_generation) || 0;
  if (generation >= MAX_ADDITIONAL_REVIEW_GENERATION) {
    return {
      status: "NEEDS_HUMAN_ACTION",
      reason: `${roundId} is itself an additional-review round (generation ${generation}) — automatic re-escalation stops after one hop; this needs a human decision, not a third round`,
      flagged_items: summarizeFlagged(flaggedItems),
    };
  }

  const itemIds = flaggedItems.map((item) => item.item_id);
  const placeholders = itemIds.map(() => "?").join(",");
  const itemRows = await env.DB.prepare(
    `SELECT item_id, source_snapshot, candidate_sentence, candidate_claim_id, provenance FROM items WHERE item_id IN (${placeholders})`
  )
    .bind(...itemIds)
    .all();
  const itemsById = new Map(itemRows.results.map((row) => [row.item_id, row]));

  const missingContent = flaggedItems.filter((item) => !itemsById.has(item.item_id));
  if (missingContent.length) {
    // Defensive only — should never happen for a genuinely completed
    // round's own items; a bug here is worth surfacing, not papering over.
    return { status: "NEEDS_HUMAN_ACTION", reason: "item_content_missing", flagged_items: summarizeFlagged(missingContent) };
  }

  const candidateClaimIds = flaggedItems.map((item) => itemsById.get(item.item_id).candidate_claim_id);
  const requiredCount = policy.additional_reviewers_per_contested_item;
  const picked = await selectReviewersForBatch(env, { candidateClaimIds, count: requiredCount });

  if (picked.length < requiredCount) {
    return {
      status: "NEEDS_HUMAN_ACTION",
      reason: `only ${picked.length} of ${requiredCount} required existing approved reviewers are eligible for every flagged item at once (excluded: already judged this exact content, inactive-for-calibration, revoked, or over a per-reviewer cap)`,
      flagged_items: summarizeFlagged(flaggedItems),
    };
  }

  const originalRound = await env.DB.prepare("SELECT dataset_purpose FROM rounds WHERE round_id = ?").bind(roundId).first();
  const dispositions = [...new Set(flaggedItems.map((item) => item.disposition))];

  const items = flaggedItems.map((flagged, index) => {
    const row = itemsById.get(flagged.item_id);
    return {
      slot: index + 1,
      source_snapshot: row.source_snapshot,
      candidate_sentence: row.candidate_sentence,
      internal_note: `Additional review — flagged ${flagged.disposition} in ${roundId}, slot ${flagged.slot} (item ${flagged.item_id}). This is a NEW, independent assignment of the same claim to different reviewers; the original judgment(s) are preserved unchanged, never overwritten.`,
      provenance: row.provenance || null,
    };
  });

  await saveDraft(
    env,
    nextRoundId,
    {
      round_id: nextRoundId,
      dataset_purpose: (originalRound && originalRound.dataset_purpose) || "development",
      task_version: "v0.1",
      research_question: `Additional independent review of ${flaggedItems.length} item(s) flagged ${dispositions.join("/")} in ${roundId}.`,
      reviewer_ids: picked,
      items,
      source: "calibration_orchestrator_additional_review",
    },
    { actor: actor || "system:additional_review", status: "draft" }
  );

  await env.DB.prepare("UPDATE rounds SET additional_review_of_round_id = ?, additional_review_generation = ? WHERE round_id = ?")
    .bind(roundId, generation + 1, nextRoundId)
    .run();

  return {
    status: "DRAFTED",
    draft_round_id: nextRoundId,
    reviewer_ids: picked,
    flagged_items: summarizeFlagged(flaggedItems),
  };
}
