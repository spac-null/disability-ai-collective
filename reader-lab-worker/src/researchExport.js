/**
 * Crip Minds Reader Lab — shared research-export service.
 *
 * The ONE place a completed round's judgments are ever turned into a
 * credential-free research artifact. The admin UI's download button, the
 * automatic completion hook (index.js), the manual "Retry export"
 * action, the cron reconciliation job, and the machine `/ops/rounds/:id/
 * export` route all call this same function — never a second, parallel
 * export path.
 *
 * Security-by-construction, not by review: the only tables this file
 * ever reads from are `rounds`, `items`, `assignments`, and `responses`.
 * It never references `invitations` or `sessions` — the two tables that
 * hold anything credential-shaped — so there is no code path here that
 * could leak a token, a token hash, a session id, or a session hash into
 * an export, regardless of what a future edit to this file gets wrong
 * elsewhere in it.
 */

import { sha256Hex, nowIso } from "./util.js";
import { ValidationError } from "./publish.js";

export const EXPORT_VERSION = "reader-lab-research-export-v1";

function canonicalItemOrder(a, b) {
  const ao = a.item_order == null ? Number.MAX_SAFE_INTEGER : a.item_order;
  const bo = b.item_order == null ? Number.MAX_SAFE_INTEGER : b.item_order;
  if (ao !== bo) return ao - bo;
  return a.item_id < b.item_id ? -1 : a.item_id > b.item_id ? 1 : 0;
}

async function collectRoundExportRows(env, roundId) {
  const rows = await env.DB.prepare(
    `SELECT a.item_id, a.item_order, a.reviewer_id, a.answered_at,
            i.source_snapshot, i.candidate_sentence, i.source_snapshot_id, i.candidate_claim_id,
            i.internal_note, i.provenance,
            r.selected_public_response, r.internal_normalized_response, r.confidence, r.comment,
            r.timestamp, r.reviewer_blind_to_model_output, r.reviewer_blind_to_other_reviewers,
            r.assistance_declared
     FROM assignments a
     JOIN items i ON i.item_id = a.item_id
     LEFT JOIN responses r
       ON r.item_id = a.item_id AND r.reviewer_id = a.reviewer_id AND r.practice_or_real = 'real'
     WHERE a.round_id = ?`
  )
    .bind(roundId)
    .all();
  return rows.results;
}

// Builds the canonical export object (deterministic key order, by
// construction — every array below is explicitly sorted before this
// function ever touches it, and object literals below are written in a
// fixed order every time this code runs).
function buildCanonicalPayload(round, rows) {
  const byItem = new Map();
  for (const row of rows) {
    if (!byItem.has(row.item_id)) {
      byItem.set(row.item_id, {
        item_id: row.item_id,
        item_order: row.item_order,
        source_snapshot: row.source_snapshot,
        candidate_sentence: row.candidate_sentence,
        source_snapshot_id: row.source_snapshot_id,
        candidate_claim_id: row.candidate_claim_id,
        internal_note: row.internal_note,
        provenance: row.provenance,
        judgments: [],
      });
    }
    if (!row.selected_public_response) {
      throw new Error(`missing_response_for_completed_round: item ${row.item_id}, reviewer ${row.reviewer_id}`);
    }
    byItem.get(row.item_id).judgments.push({
      reviewer_id: row.reviewer_id,
      selected_public_response: row.selected_public_response,
      internal_normalized_response: row.internal_normalized_response,
      confidence: row.confidence,
      comment: row.comment,
      timestamp: row.timestamp,
      reviewer_blind_to_model_output: !!row.reviewer_blind_to_model_output,
      reviewer_blind_to_other_reviewers: !!row.reviewer_blind_to_other_reviewers,
      assistance_declared: row.assistance_declared,
    });
  }

  const items = [...byItem.values()].sort(canonicalItemOrder);
  items.forEach((item, index) => {
    item.slot = index + 1;
    item.judgments.sort((a, b) => (a.reviewer_id < b.reviewer_id ? -1 : a.reviewer_id > b.reviewer_id ? 1 : 0));
  });

  const reviewerIds = [...new Set(rows.map((r) => r.reviewer_id))].sort();

  return {
    export_version: EXPORT_VERSION,
    generated_at: nowIso(),
    round_id: round.round_id,
    manifest_sha256: round.manifest_sha256 || null,
    dataset_purpose: round.dataset_purpose,
    dataset_purpose_note: round.dataset_purpose_note || null,
    task_type: round.task_type,
    task_version: round.task_version,
    research_question: round.research_question || null,
    reviewer_blind_to_model_output: !!round.reviewer_blind_to_model_output,
    reviewer_blind_to_other_reviewers: !!round.reviewer_blind_to_other_reviewers,
    assistance_mode_required: round.assistance_mode_required,
    created_at: round.created_at,
    frozen_at: round.frozen_at,
    published_at: round.published_at,
    completed_at: round.completed_at,
    reviewer_ids: reviewerIds,
    items: items.map((item) => ({
      slot: item.slot,
      item_id: item.item_id,
      source_snapshot: item.source_snapshot,
      candidate_sentence: item.candidate_sentence,
      source_snapshot_id: item.source_snapshot_id,
      candidate_claim_id: item.candidate_claim_id,
      internal_note: item.internal_note,
      provenance: item.provenance,
      judgments: item.judgments,
    })),
  };
}

async function readExportRow(env, roundId) {
  return env.DB.prepare("SELECT * FROM research_exports WHERE round_id = ?").bind(roundId).first();
}

// Idempotent: generate-or-return. A 'ready' export is never recomputed
// or overwritten by this function — that's what makes it a frozen
// snapshot rather than a live view. Generating for an already-'ready'
// round (auto-trigger replay, manual retry click, cron sweep all hitting
// the same round) just returns the existing row. Only a missing row or
// a 'failed' row causes an actual (re)attempt.
export async function buildResearchExport(env, roundId, { actor } = {}) {
  const round = await env.DB.prepare("SELECT * FROM rounds WHERE round_id = ?").bind(roundId).first();
  if (!round) throw new ValidationError([`unknown_round: ${roundId}`]);
  if (round.status !== "completed") {
    throw new ValidationError([`round_not_completed: status is "${round.status}" — export is only available once every reviewer has finished`]);
  }

  const existing = await readExportRow(env, roundId);
  if (existing && existing.status === "ready") {
    return { status: "ready", export: JSON.parse(existing.payload_json), content_sha256: existing.content_sha256, generated_at: existing.generated_at };
  }

  const attemptedAt = nowIso();
  try {
    const rows = await collectRoundExportRows(env, roundId);
    const payload = buildCanonicalPayload(round, rows);
    const payloadJson = JSON.stringify(payload);
    const hash = await sha256Hex(payloadJson);

    await env.DB.prepare(
      `INSERT INTO research_exports (round_id, export_version, payload_json, content_sha256, generated_at, status, error_detail)
       VALUES (?,?,?,?,?,'ready',NULL)
       ON CONFLICT (round_id) DO UPDATE SET
         export_version = excluded.export_version,
         payload_json = excluded.payload_json,
         content_sha256 = excluded.content_sha256,
         generated_at = excluded.generated_at,
         status = 'ready',
         error_detail = NULL
       WHERE research_exports.status != 'ready'`
    )
      .bind(roundId, EXPORT_VERSION, payloadJson, hash, attemptedAt)
      .run();

    return { status: "ready", export: payload, content_sha256: hash, generated_at: attemptedAt };
  } catch (err) {
    const errorDetail = String((err && err.message) || err);
    await env.DB.prepare(
      `INSERT INTO research_exports (round_id, export_version, payload_json, content_sha256, generated_at, status, error_detail)
       VALUES (?,?,NULL,NULL,?,'failed',?)
       ON CONFLICT (round_id) DO UPDATE SET
         generated_at = excluded.generated_at,
         status = 'failed',
         error_detail = excluded.error_detail
       WHERE research_exports.status != 'ready'`
    )
      .bind(roundId, EXPORT_VERSION, attemptedAt, errorDetail)
      .run();
    return { status: "failed", error: errorDetail, generated_at: attemptedAt };
  }
}

export async function getExportStatus(env, roundId) {
  const row = await readExportRow(env, roundId);
  if (!row) return { status: "not_ready" };
  return {
    status: row.status,
    generated_at: row.generated_at,
    content_sha256: row.content_sha256 || null,
    error_detail: row.error_detail || null,
  };
}

// Serves the stored payload verbatim (never re-serialized) so the
// downloaded bytes always match content_sha256 exactly.
export async function getExportPayloadJson(env, roundId) {
  const row = await readExportRow(env, roundId);
  if (!row || row.status !== "ready") return null;
  return row.payload_json;
}
