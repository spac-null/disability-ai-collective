/**
 * Crip Minds Reader Lab — calibration admin API (browser-facing, behind
 * adminApi.js's Cloudflare Access gate). Read-mostly: the only mutation
 * is "retry a failed run," which creates a fresh calibration_runs row +
 * Workflow instance — it never touches a response, export, or published
 * round.
 */

import { secureJson, newId, nowIso, sha256Hex } from "./util.js";
import { CALIBRATION_WORKFLOW_VERSION } from "./calibrationOrchestrator.js";

const NEXT_ACTION_BY_STATUS = {
  queued: "Calibration starting.",
  analysis_pending: "Analyzing the completed round.",
  evidence_updated: "Evidence updated — preparing the next round.",
  next_round_pending: "Preparing the next round.",
  needs_eligible_candidates: "Analysis complete — no eligible candidates yet for a next round.",
  waiting_for_human_approval: "Next round draft ready — review it in Rounds.",
  failed: "Calibration failed — see error below. Retry available.",
};

async function roundReviewerProgress(env, roundId) {
  const rows = await env.DB.prepare(
    `SELECT reviewer_id, COUNT(*) AS assigned, SUM(CASE WHEN answered_at IS NOT NULL THEN 1 ELSE 0 END) AS answered
     FROM assignments WHERE round_id = ? GROUP BY reviewer_id`
  )
    .bind(roundId)
    .all();
  return rows.results;
}

function nextActionForRound(round, run, reviewers) {
  if (round.status !== "completed" && round.status !== "published") {
    return "This round isn't published yet.";
  }
  if (round.status === "published") {
    const waiting = reviewers.filter((r) => r.answered < r.assigned).map((r) => r.reviewer_id);
    return waiting.length ? `Waiting for ${waiting.join(", ")}.` : "Waiting for round completion.";
  }
  if (!run) return "Waiting for calibration to start (usually immediate; the hourly reconciliation sweep catches any delay).";
  return NEXT_ACTION_BY_STATUS[run.status] || `Status: ${run.status}`;
}

async function buildHistory(env, roundId, run) {
  const events = [];
  const round = await env.DB.prepare("SELECT completed_at FROM rounds WHERE round_id = ?").bind(roundId).first();
  if (round && round.completed_at) events.push({ label: "Round complete", timestamp: round.completed_at });

  if (!run) return events.sort((a, b) => (a.timestamp || "").localeCompare(b.timestamp || ""));

  events.push({ label: "Calibration run created", timestamp: run.created_at });

  const jobs = await env.DB.prepare("SELECT * FROM calibration_jobs WHERE run_id = ? ORDER BY created_at").bind(run.run_id).all();
  for (const job of jobs.results) {
    const label = `${job.job_type.replace(/_/g, " ")} — ${job.status}`;
    events.push({ label, timestamp: job.completed_at || job.claimed_at || job.created_at });
  }

  const artifacts = await env.DB.prepare("SELECT * FROM calibration_artifacts WHERE run_id = ? ORDER BY created_at").bind(run.run_id).all();
  for (const artifact of artifacts.results) {
    events.push({ label: `${artifact.artifact_type.replace(/_/g, " ")} recorded`, timestamp: artifact.created_at });
  }

  if (run.completed_at) events.push({ label: `Run ${run.status}`, timestamp: run.completed_at });

  return events.filter((e) => e.timestamp).sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

export async function handleCalibrationStatus(request, env, url) {
  const requestedRoundId = url.searchParams.get("round_id");
  let roundId = requestedRoundId;
  if (!roundId) {
    // Default to the most recently created round that has (or should
    // have) a calibration story — published or completed, most recent
    // first.
    const row = await env.DB.prepare(
      "SELECT round_id FROM rounds WHERE status IN ('published','completed') ORDER BY created_at DESC LIMIT 1"
    ).first();
    roundId = row ? row.round_id : null;
  }
  if (!roundId) return secureJson({ round_id: null, calibration_run: null, evidence_summary: null, history: [], next_action: "No round yet — create or import one." });

  const round = await env.DB.prepare("SELECT * FROM rounds WHERE round_id = ?").bind(roundId).first();
  if (!round) return secureJson({ error: "not_found" }, 404);

  const reviewers = await roundReviewerProgress(env, roundId);
  const run = await env.DB.prepare("SELECT * FROM calibration_runs WHERE round_id = ? ORDER BY created_at DESC LIMIT 1")
    .bind(roundId)
    .first();

  let evidenceSummary = null;
  if (run && run.analysis_artifact_id) {
    const artifact = await env.DB.prepare("SELECT content_json FROM calibration_artifacts WHERE artifact_id = ?")
      .bind(run.analysis_artifact_id)
      .first();
    if (artifact) evidenceSummary = JSON.parse(artifact.content_json).round_summary;
  }

  let nextRoundDraft = null;
  if (run && run.next_round_draft_artifact_id) {
    const artifact = await env.DB.prepare("SELECT content_json FROM calibration_artifacts WHERE artifact_id = ?")
      .bind(run.next_round_draft_artifact_id)
      .first();
    if (artifact) nextRoundDraft = JSON.parse(artifact.content_json);
  }

  const history = await buildHistory(env, roundId, run);

  return secureJson({
    round_id: roundId,
    round_status: round.status,
    reviewers,
    calibration_run: run
      ? {
          run_id: run.run_id,
          status: run.status,
          current_step: run.current_step,
          created_at: run.created_at,
          started_at: run.started_at,
          completed_at: run.completed_at,
          error: run.error,
        }
      : null,
    evidence_summary: evidenceSummary,
    next_round_draft: nextRoundDraft,
    history,
    next_action: nextActionForRound(round, run, reviewers),
  });
}

export async function handleCalibrationRetry(request, env, identity, runId) {
  const failedRun = await env.DB.prepare("SELECT * FROM calibration_runs WHERE run_id = ?").bind(runId).first();
  if (!failedRun) return secureJson({ error: "not_found" }, 404);
  if (failedRun.status !== "failed") {
    return secureJson({ error: "run_not_failed", status: failedRun.status }, 409);
  }

  // A fresh attempt from scratch — a new run_id and a new Workflow
  // instance id (the old idempotency_key stays attached to the failed
  // run so its history is never lost or overwritten). Safe to re-run:
  // analyze-human-round-v1/prepare-next-round-v1 are both versioned/
  // recomputable, never treated as immutable-once-generated the way a
  // research export is.
  const newRunId = newId("crun");
  // Workflow instance ids have both a charset restriction ([a-zA-Z0-9-_],
  // no colons) and a length limit — confirmed directly this pass: a
  // concatenated `${oldKey}-retry-${newRunId}` string (~110 chars) was
  // rejected outright ("Workflow instance has invalid id"), and before
  // that, a colon-containing id hung the request until the Workers
  // runtime force-canceled it. A fresh sha256 hex digest (64 chars,
  // same shape armCalibrationRun already uses successfully) sidesteps
  // both problems rather than guessing at the exact limit.
  const newIdempotencyKey = await sha256Hex(`${failedRun.idempotency_key}:retry:${newRunId}`);
  const now = nowIso();
  await env.DB.prepare(
    `INSERT INTO calibration_runs (run_id, round_id, research_export_hash, workflow_version, workflow_instance_id, idempotency_key, status, created_at)
     VALUES (?,?,?,?,?,?, 'queued', ?)`
  )
    .bind(newRunId, failedRun.round_id, failedRun.research_export_hash, CALIBRATION_WORKFLOW_VERSION, newIdempotencyKey, newIdempotencyKey, now)
    .run();

  try {
    await env.CALIBRATION_WORKFLOW.create({
      id: newIdempotencyKey,
      params: {
        run_id: newRunId,
        round_id: failedRun.round_id,
        research_export_hash: failedRun.research_export_hash,
        workflow_version: CALIBRATION_WORKFLOW_VERSION,
      },
    });
  } catch (err) {
    // Same discipline as armCalibrationRun: never leave a 'queued' row
    // with no real Workflow instance behind it — a create() failure
    // marks the fresh run 'failed' immediately, visible for another
    // retry, rather than silently stuck.
    await env.DB.prepare("UPDATE calibration_runs SET status='failed', error=?, completed_at=? WHERE run_id=?")
      .bind(`workflow_create_failed: ${String((err && err.message) || err)}`, nowIso(), newRunId)
      .run();
    return secureJson({ error: "workflow_create_failed", detail: String((err && err.message) || err) }, 500);
  }

  return secureJson({ ok: true, run_id: newRunId });
}
