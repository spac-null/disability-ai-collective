/**
 * Crip Minds Reader Lab — calibration-run arming.
 *
 * The one place a Cloudflare Workflow instance is ever created for a
 * completed round. Called from two sites — the automatic
 * completion+export hook in index.js's handleResponse, and the hourly
 * cron reconciliation sweep — and both call this exact same function,
 * never a second ad hoc creation path.
 *
 * Idempotency: the Workflow instance id (and the calibration_runs row's
 * own idempotency_key) is sha256(round_id + research export content hash
 * + workflow version) — never a timestamp, never random. A replayed
 * completion event, a duplicate reconciliation sweep hit, or a genuine
 * race between the two call sites all compute the identical key, so at
 * most one calibration_runs row and one Workflow instance can ever exist
 * for a given round+export+version, regardless of how many times this
 * function is called for it.
 */

import { sha256Hex, newId, nowIso } from "./util.js";

export const CALIBRATION_WORKFLOW_VERSION = "v1"; // pairs analyze-human-round-v1 + prepare-next-round-v1

export async function armCalibrationRun(env, roundId, { actor } = {}) {
  const exportRow = await env.DB.prepare("SELECT content_sha256, status FROM research_exports WHERE round_id = ?")
    .bind(roundId)
    .first();
  if (!exportRow || exportRow.status !== "ready") {
    return { armed: false, reason: "export_not_ready" };
  }

  const idempotencyKey = await sha256Hex(`${roundId}:${exportRow.content_sha256}:${CALIBRATION_WORKFLOW_VERSION}`);

  const existing = await env.DB.prepare("SELECT run_id, status FROM calibration_runs WHERE idempotency_key = ?")
    .bind(idempotencyKey)
    .first();
  if (existing) {
    return { armed: false, reason: "already_armed", run_id: existing.run_id, status: existing.status };
  }

  const runId = newId("crun");
  const now = nowIso();
  await env.DB.prepare(
    `INSERT INTO calibration_runs (run_id, round_id, research_export_hash, workflow_version, workflow_instance_id, idempotency_key, status, created_at)
     VALUES (?,?,?,?,?,?, 'queued', ?)
     ON CONFLICT (idempotency_key) DO NOTHING`
  )
    .bind(runId, roundId, exportRow.content_sha256, CALIBRATION_WORKFLOW_VERSION, idempotencyKey, idempotencyKey, now)
    .run();

  try {
    await env.CALIBRATION_WORKFLOW.create({
      id: idempotencyKey,
      params: { run_id: runId, round_id: roundId, research_export_hash: exportRow.content_sha256, workflow_version: CALIBRATION_WORKFLOW_VERSION },
    });
    return { armed: true, run_id: runId };
  } catch (err) {
    // Distinguish "this instance already exists" (a benign race between
    // the completion hook and the cron sweep, or a genuine replay) from
    // a real creation failure. Only the latter should mark the run
    // failed — a duplicate-id rejection means the real instance is
    // already out there doing its job.
    let alreadyExists = false;
    try {
      await env.CALIBRATION_WORKFLOW.get(idempotencyKey).status();
      alreadyExists = true;
    } catch {
      alreadyExists = false;
    }
    if (alreadyExists) {
      return { armed: true, run_id: runId, note: "workflow_instance_already_existed" };
    }
    await env.DB.prepare("UPDATE calibration_runs SET status='failed', error=?, completed_at=? WHERE run_id=?")
      .bind(`workflow_create_failed: ${String((err && err.message) || err)}`, now, runId)
      .run();
    return { armed: false, reason: "workflow_create_failed", run_id: runId, error: String((err && err.message) || err) };
  }
}
