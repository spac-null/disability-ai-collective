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
import { getActivePolicy } from "./policy.js";

// Decoupled on purpose (previously one shared "v1" constant paired both
// job types together): the candidate-bridge pass added role_alignment/
// support_alignment/overall_relation to analyze_human_round's output
// (analyze-human-round-v2) without touching prepare_next_round's logic
// at all — forcing prepare-next-round through its own meaningless "v2"
// would register a version label for a file that never changed. Each
// job type now versions independently; calibration_jobs.workflow_version
// (per-job-row, not per-run) already supported this, nothing else needed
// to change to make it real.
export const ANALYZE_HUMAN_ROUND_VERSION = "v2";
export const PREPARE_NEXT_ROUND_VERSION = "v1";
// Retained only as the run-level identity stamp (calibration_runs.
// workflow_version, the Workflow instance idempotency key) — represents
// "which analysis generation this run's evidence was produced under,"
// since that's the field with real comparison-schema implications.
// Never read by either job's own dispatch (calibration_runner.py's
// JOB_HANDLERS keys purely on job_type name).
export const CALIBRATION_WORKFLOW_VERSION = ANALYZE_HUMAN_ROUND_VERSION;

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

  // The run is stamped with the policy version active RIGHT NOW, at
  // creation — never re-read as "whatever is active" later in the
  // Workflow, which could otherwise change mid-run (a Workflow can wait
  // for the Trident runner for up to 3 days). Every policy-gated
  // decision this run ever makes uses this frozen value, so a run
  // started under policy_version=3 stays interpretable under
  // policy_version=3 forever, even after policy_version=4 goes active.
  const activePolicy = await getActivePolicy(env);

  const runId = newId("crun");
  const now = nowIso();
  await env.DB.prepare(
    `INSERT INTO calibration_runs (run_id, round_id, research_export_hash, workflow_version, workflow_instance_id, idempotency_key, status, policy_version, created_at)
     VALUES (?,?,?,?,?,?, 'queued', ?, ?)
     ON CONFLICT (idempotency_key) DO NOTHING`
  )
    .bind(runId, roundId, exportRow.content_sha256, CALIBRATION_WORKFLOW_VERSION, idempotencyKey, idempotencyKey, activePolicy.policy_version, now)
    .run();

  try {
    await env.CALIBRATION_WORKFLOW.create({
      id: idempotencyKey,
      params: {
        run_id: runId,
        round_id: roundId,
        research_export_hash: exportRow.content_sha256,
        workflow_version: CALIBRATION_WORKFLOW_VERSION,
        policy_version: activePolicy.policy_version,
      },
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

// Shared by two callers: a human clicking Retry on a genuinely `failed`
// run (calibrationAdmin.js), and the automatic reconciliation sweep
// resuming a run stuck at `needs_eligible_candidates` now that
// candidates exist (below). Both are the same underlying situation — a
// run reached a terminal state without producing what was needed, and
// conditions may have since changed — so both get the identical "fresh
// run from scratch" treatment: a new run_id, a new idempotency key
// derived from the original (bypassing armCalibrationRun's own
// round+export+version key, which would otherwise just report
// "already_armed" and refuse to create anything new), and a freshly
// re-read active policy. Always re-runs analyze_human_round too, not
// just prepare_next_round — analysis is versioned/recomputable by
// design (never treated as immutable the way a research export is), so
// a fresh full run is simpler and safer than trying to splice a new
// prepare_next_round attempt onto an old, already-completed Workflow
// instance (which Cloudflare Workflows has no mechanism to resume once
// its run() has returned). The prior run's own row and artifacts are
// never modified — this only ever adds a new run/artifact, alongside
// the old one, exactly the "additive, never rewrite" discipline this
// project already applies everywhere else.
export async function armFreshCalibrationRun(env, priorRun, { actor, reason } = {}) {
  const activePolicy = await getActivePolicy(env);
  const newRunId = newId("crun");
  const newIdempotencyKey = await sha256Hex(`${priorRun.idempotency_key}:resume:${newRunId}`);
  const now = nowIso();

  await env.DB.prepare(
    `INSERT INTO calibration_runs (run_id, round_id, research_export_hash, workflow_version, workflow_instance_id, idempotency_key, status, policy_version, created_at)
     VALUES (?,?,?,?,?,?, 'queued', ?, ?)`
  )
    .bind(newRunId, priorRun.round_id, priorRun.research_export_hash, CALIBRATION_WORKFLOW_VERSION, newIdempotencyKey, newIdempotencyKey, activePolicy.policy_version, now)
    .run();

  try {
    await env.CALIBRATION_WORKFLOW.create({
      id: newIdempotencyKey,
      params: {
        run_id: newRunId,
        round_id: priorRun.round_id,
        research_export_hash: priorRun.research_export_hash,
        workflow_version: CALIBRATION_WORKFLOW_VERSION,
        policy_version: activePolicy.policy_version,
      },
    });
  } catch (err) {
    await env.DB.prepare("UPDATE calibration_runs SET status='failed', error=?, completed_at=? WHERE run_id=?")
      .bind(`workflow_create_failed: ${String((err && err.message) || err)}`, nowIso(), newRunId)
      .run();
    return { armed: false, reason: "workflow_create_failed", run_id: newRunId, error: String((err && err.message) || err) };
  }

  return { armed: true, run_id: newRunId, resumed_from_run_id: priorRun.run_id, trigger_reason: reason || null };
}

// Called after candidate ingestion adds ≥1 newly eligible candidate, and
// from the hourly cron as a safety net. Finds every calibration_runs row
// stuck at `needs_eligible_candidates` that hasn't already been resumed
// (`resumed_by_run_id IS NULL`), atomically claims each one (the UPDATE
// itself is the claim — only the caller that actually flips
// resumed_by_run_id from NULL proceeds, so a concurrent cron tick and a
// concurrent ingestion call can never both resume the same stuck run),
// and arms a fresh run for it. Never requires a human to click "retry
// next round" — that button remains available, but only matters if this
// automatic path genuinely fails.
export async function reconcileStuckCalibrationRuns(env, { actor } = {}) {
  const stuck = await env.DB.prepare(
    "SELECT * FROM calibration_runs WHERE status = 'needs_eligible_candidates' AND resumed_by_run_id IS NULL"
  ).all();

  const outcomes = [];
  for (const priorRun of stuck.results) {
    const claim = await env.DB.prepare(
      "UPDATE calibration_runs SET resumed_by_run_id = ? WHERE run_id = ? AND resumed_by_run_id IS NULL"
    )
      .bind("claiming", priorRun.run_id)
      .run();
    if ((claim.meta.changes || 0) === 0) {
      outcomes.push({ round_id: priorRun.round_id, run_id: priorRun.run_id, outcome: "already_claimed" });
      continue;
    }

    // Two-phase claim: the sentinel above already prevents a second
    // caller from racing this same row. If armFreshCalibrationRun itself
    // throws (rather than returning armed:false, which it handles
    // internally), the sentinel is rolled back to NULL rather than left
    // stuck forever — a genuinely unexpected failure should be retryable
    // by the next reconciliation pass, not permanently wedged.
    try {
      const result = await armFreshCalibrationRun(env, priorRun, {
        actor: actor || "system:candidate_ingestion_reconciliation",
        reason: "eligible_candidates_now_exist",
      });
      await env.DB.prepare("UPDATE calibration_runs SET resumed_by_run_id = ? WHERE run_id = ?").bind(result.run_id, priorRun.run_id).run();
      outcomes.push({ round_id: priorRun.round_id, run_id: priorRun.run_id, outcome: result.armed ? "resumed" : "resume_failed", new_run_id: result.run_id });
    } catch (err) {
      await env.DB.prepare("UPDATE calibration_runs SET resumed_by_run_id = NULL WHERE run_id = ? AND resumed_by_run_id = 'claiming'").bind(priorRun.run_id).run();
      outcomes.push({ round_id: priorRun.round_id, run_id: priorRun.run_id, outcome: "resume_error", error: String((err && err.message) || err) });
    }
  }
  return { checked: stuck.results.length, outcomes };
}
