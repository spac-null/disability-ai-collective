/**
 * Crip Minds Reader Lab — calibration job API (`/ops/calibration/jobs/*`).
 *
 * The only interface the Trident calibration runner ever talks to.
 * Authenticated by CALIBRATION_RUNNER_TOKEN — a narrow credential,
 * completely separate from ADMIN_TOKEN/EXPORT_TOKEN, that can do exactly
 * four things: claim a job, heartbeat it, complete it, or report it
 * failed. It has no code path here (or anywhere else in this Worker) to
 * create/revoke a reviewer, publish a round, alter a response, alter a
 * research export, or reach any /admin route — see requireCalibrationRunner
 * in index.js, which is the only place this token is ever checked.
 */

import { secureJson, newId, nowIso, sha256Hex } from "./util.js";
import { sortedStringify } from "./publish.js";

const LEASE_SECONDS = 30 * 60; // 30 minutes — modest, matches a model call taking at most a couple of minutes
const CLAIM_RETRY_ATTEMPTS = 3; // essentially insurance against a race that, with one runner, should never happen

async function sendWorkflowEvent(env, runId, jobId, status) {
  const run = await env.DB.prepare("SELECT workflow_instance_id FROM calibration_runs WHERE run_id = ?").bind(runId).first();
  if (!run || !env.CALIBRATION_WORKFLOW) return;
  try {
    const instance = await env.CALIBRATION_WORKFLOW.get(run.workflow_instance_id);
    await instance.sendEvent({ type: "calibration-job-event", payload: { job_id: jobId, status } });
  } catch {
    // The waiting Workflow step has its own timeout (see
    // calibrationWorkflow.js's JOB_WAIT_TIMEOUT) and will eventually
    // treat a never-woken wait as a failed attempt and retry — a failed
    // sendEvent here is not silently lost, just slower to notice.
  }
}

async function handleClaim(request, env) {
  const body = (await request.json().catch(() => ({}))) || {};
  const runnerId = typeof body.runner_id === "string" && body.runner_id ? body.runner_id : "unknown-runner";

  for (let attempt = 0; attempt < CLAIM_RETRY_ATTEMPTS; attempt++) {
    const candidate = await env.DB.prepare(
      "SELECT job_id FROM calibration_jobs WHERE status = 'pending' ORDER BY created_at LIMIT 1"
    ).first();
    if (!candidate) return secureJson({ no_job: true });

    const now = nowIso();
    const leaseExpires = new Date(Date.now() + LEASE_SECONDS * 1000).toISOString();
    const result = await env.DB.prepare(
      "UPDATE calibration_jobs SET status='claimed', claimed_by=?, claimed_at=?, lease_expires_at=? WHERE job_id=? AND status='pending'"
    )
      .bind(runnerId, now, leaseExpires, candidate.job_id)
      .run();

    if ((result.meta.changes || 0) > 0) {
      const job = await env.DB.prepare("SELECT * FROM calibration_jobs WHERE job_id = ?").bind(candidate.job_id).first();
      return secureJson({
        job_id: job.job_id,
        run_id: job.run_id,
        job_type: job.job_type,
        workflow_version: job.workflow_version,
        input: JSON.parse(job.input_json),
        input_hash: job.input_hash,
        lease_expires_at: job.lease_expires_at,
      });
    }
    // Someone else claimed it between our SELECT and UPDATE — try the
    // next-oldest pending job instead of giving up immediately.
  }
  return secureJson({ no_job: true });
}

async function handleHeartbeat(request, env, jobId) {
  const body = (await request.json().catch(() => ({}))) || {};
  const runnerId = body.runner_id;
  const job = await env.DB.prepare("SELECT * FROM calibration_jobs WHERE job_id = ?").bind(jobId).first();
  if (!job) return secureJson({ error: "not_found" }, 404);
  if (job.status !== "claimed" || job.claimed_by !== runnerId) {
    return secureJson({ error: "not_claimed_by_this_runner" }, 409);
  }
  const leaseExpires = new Date(Date.now() + LEASE_SECONDS * 1000).toISOString();
  await env.DB.prepare("UPDATE calibration_jobs SET lease_expires_at = ? WHERE job_id = ?").bind(leaseExpires, jobId).run();
  return secureJson({ ok: true, lease_expires_at: leaseExpires });
}

async function handleComplete(request, env, jobId) {
  const body = (await request.json().catch(() => ({}))) || {};
  const { runner_id: runnerId, result, result_hash: resultHash } = body;
  if (!result || typeof result !== "object" || typeof resultHash !== "string") {
    return secureJson({ error: "missing_result_or_hash" }, 400);
  }

  const job = await env.DB.prepare("SELECT * FROM calibration_jobs WHERE job_id = ?").bind(jobId).first();
  if (!job) return secureJson({ error: "not_found" }, 404);

  // Idempotent completion — a runner retrying an HTTP call after a
  // network hiccup gets the same success response, not a second write
  // or an error.
  if (job.status === "completed") {
    return secureJson({ ok: true, already_completed: true });
  }
  if (job.status !== "claimed" || job.claimed_by !== runnerId) {
    return secureJson({ error: "not_claimed_by_this_runner" }, 409);
  }
  if (job.lease_expires_at && new Date(job.lease_expires_at) < new Date()) {
    return secureJson({ error: "lease_expired" }, 409);
  }

  // Hash the CANONICAL (sorted-key, whitespace-free) form, not plain
  // JSON.stringify — Python's json.dumps and JS's JSON.stringify differ
  // in whitespace/key-order/non-ASCII-escaping defaults, none of which
  // survive identically across languages. sortedStringify is simple
  // enough that the runner reproduces it exactly (see
  // calibration_runner.py's canonical_json) rather than relying on
  // either language's own default serializer.
  const resultJson = JSON.stringify(result);
  const recomputedHash = await sha256Hex(sortedStringify(result));
  if (recomputedHash !== resultHash) {
    return secureJson({ error: "result_hash_mismatch" }, 400);
  }

  const now = nowIso();
  const updateResult = await env.DB.prepare(
    "UPDATE calibration_jobs SET status='completed', completed_at=?, result_json=?, result_hash=? WHERE job_id=? AND status='claimed'"
  )
    .bind(now, resultJson, recomputedHash, jobId)
    .run();

  if ((updateResult.meta.changes || 0) > 0) {
    await sendWorkflowEvent(env, job.run_id, jobId, "completed");
  }
  return secureJson({ ok: true, already_completed: false });
}

async function handleFail(request, env, jobId) {
  const body = (await request.json().catch(() => ({}))) || {};
  const { runner_id: runnerId, error } = body;
  const job = await env.DB.prepare("SELECT * FROM calibration_jobs WHERE job_id = ?").bind(jobId).first();
  if (!job) return secureJson({ error: "not_found" }, 404);
  if (job.status === "failed") return secureJson({ ok: true, already_failed: true });
  if (job.status !== "claimed" || job.claimed_by !== runnerId) {
    return secureJson({ error: "not_claimed_by_this_runner" }, 409);
  }

  const now = nowIso();
  const updateResult = await env.DB.prepare(
    "UPDATE calibration_jobs SET status='failed', completed_at=?, error=? WHERE job_id=? AND status='claimed'"
  )
    .bind(now, String(error || "runner_reported_failure"), jobId)
    .run();

  if ((updateResult.meta.changes || 0) > 0) {
    await sendWorkflowEvent(env, job.run_id, jobId, "failed");
  }
  return secureJson({ ok: true, already_failed: false });
}

export async function calibrationJobsFetch(request, env, url) {
  const path = url.pathname.replace(/^\/ops\/calibration\/jobs/, "") || "/";
  const method = request.method;
  let m;

  if (path === "/claim" && method === "POST") return handleClaim(request, env);
  if ((m = /^\/([^/]+)\/heartbeat$/.exec(path)) && method === "POST") return handleHeartbeat(request, env, m[1]);
  if ((m = /^\/([^/]+)\/complete$/.exec(path)) && method === "POST") return handleComplete(request, env, m[1]);
  if ((m = /^\/([^/]+)\/fail$/.exec(path)) && method === "POST") return handleFail(request, env, m[1]);

  return secureJson({ error: "not_found" }, 404);
}
