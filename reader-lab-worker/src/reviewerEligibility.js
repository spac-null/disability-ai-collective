/**
 * Crip Minds Reader Lab — existing-approved-reviewer pool.
 *
 * Generalizes reviewer selection beyond the two named pilot parents.
 * "Existing approved reviewer" = not revoked AND active_for_calibration
 * (migration 0005) — a distinction `revoked` alone can't express: a
 * reviewer can remain a valid, working account (their invitation still
 * resolves, their past responses stay intact) while no longer being
 * offered new automatic assignments, without anyone touching their
 * credential.
 *
 * This module is the ONE place that pool is read for automatic
 * assignment purposes — src/calibrationWorkflow.js's next-round
 * preparation and src/additionalReview.js's contested-item follow-up
 * both call into here, never re-deriving the eligibility rule
 * separately.
 */

export async function listActiveReviewerIds(env) {
  const rows = await env.DB.prepare(
    "SELECT reviewer_id FROM invitations WHERE revoked = 0 AND active_for_calibration = 1 ORDER BY created_at, reviewer_id"
  ).all();
  return rows.results.map((r) => r.reviewer_id);
}

async function listEligibleReviewerRows(env) {
  const rows = await env.DB.prepare(
    "SELECT reviewer_id, max_items_per_round FROM invitations WHERE revoked = 0 AND active_for_calibration = 1 ORDER BY created_at, reviewer_id"
  ).all();
  return rows.results;
}

// Every reviewer_id who has ever ANSWERED an item with this exact
// candidate_claim_id (content hash, not item_id — publishRound always
// mints a fresh item_id, even for a content-identical follow-up copy of
// a contested item, so item_id-based dedup would miss the case this
// exists to prevent). Used to stop the same reviewer from being asked to
// judge the same claim twice, per the explicit "no duplicate reviewer/
// case assignment" safeguard — unless a future, explicit repeat-
// reliability policy permits it, which nothing in this codebase does yet.
export async function reviewersWhoJudgedContent(env, candidateClaimId) {
  const rows = await env.DB.prepare(
    `SELECT DISTINCT a.reviewer_id FROM assignments a
     JOIN items i ON i.item_id = a.item_id
     WHERE i.candidate_claim_id = ? AND a.answered_at IS NOT NULL`
  )
    .bind(candidateClaimId)
    .all();
  return new Set(rows.results.map((r) => r.reviewer_id));
}

/**
 * Picks up to `count` existing approved reviewers for one piece of
 * content, excluding anyone who already judged it and anyone whose
 * per-round cap (max_items_per_round) would be exceeded once
 * tentativeCounts (a Map<reviewer_id, number> the caller keeps updated
 * across every item it's building into the same draft round) is
 * accounted for. Deterministic order (created_at, reviewer_id) — no
 * randomness, so the same input always produces the same selection,
 * which matters for a mechanism a synthetic test needs to reproduce
 * exactly.
 *
 * Returns fewer than `count` reviewer_ids if fewer are eligible — it is
 * the caller's job (src/additionalReview.js) to decide whether a partial
 * result is usable or must escalate; this function never pads a
 * shortfall by relaxing a safeguard.
 */
export async function selectAdditionalReviewers(env, { candidateClaimId, count, tentativeCounts }) {
  const eligible = await listEligibleReviewerRows(env);
  const alreadyJudged = await reviewersWhoJudgedContent(env, candidateClaimId);
  const picked = [];
  for (const row of eligible) {
    if (picked.length >= count) break;
    if (alreadyJudged.has(row.reviewer_id)) continue;
    const tentative = (tentativeCounts && tentativeCounts.get(row.reviewer_id)) || 0;
    if (row.max_items_per_round != null && tentative >= row.max_items_per_round) continue;
    picked.push(row.reviewer_id);
  }
  return picked;
}

/**
 * Picks up to `count` existing approved reviewers who are eligible for
 * EVERY piece of content in `candidateClaimIds` at once — used when a
 * whole additional-review round (uniform reviewer_ids applied to every
 * item, matching how every Reader Lab round already works — see
 * publish.js's publishRound, which assigns the full reviewer_ids ×
 * items cross product) is being built from several contested items in
 * one pass. A reviewer who already judged ANY one of the pieces of
 * content is excluded from the whole batch, even for the items they
 * never saw — simpler and more conservative than per-item selection,
 * and correct for this schema, which has no per-item reviewer subset.
 * `max_items_per_round` is checked against the FULL batch size (every
 * picked reviewer is assigned to every item in the batch).
 */
export async function selectReviewersForBatch(env, { candidateClaimIds, count }) {
  const eligible = await listEligibleReviewerRows(env);
  const excluded = new Set();
  for (const claimId of candidateClaimIds) {
    const judged = await reviewersWhoJudgedContent(env, claimId);
    for (const reviewerId of judged) excluded.add(reviewerId);
  }
  const itemCount = candidateClaimIds.length;
  const picked = [];
  for (const row of eligible) {
    if (picked.length >= count) break;
    if (excluded.has(row.reviewer_id)) continue;
    if (row.max_items_per_round != null && itemCount > row.max_items_per_round) continue;
    picked.push(row.reviewer_id);
  }
  return picked;
}
