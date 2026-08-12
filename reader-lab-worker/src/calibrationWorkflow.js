/**
 * Crip Minds Reader Lab — Calibration Orchestrator Workflow.
 *
 * One Cloudflare Workflow instance per completed round's calibration
 * cycle. This class is deliberately thin: it creates a claimable job,
 * waits for the (private, Tailscale-only) Trident runner to complete it
 * via HTTP (see index.js's /ops/calibration/jobs/* routes), validates
 * the result, persists it, and moves to the next step. The actual
 * analysis logic — the deterministic disposition rules in
 * calibration/workflows/analyze-human-round-v1.md — lives in the
 * runner's Python script, not here; this file never computes a
 * disposition/agreement/reference-strength value itself.
 *
 * Durable-state principle (see the design doc): this Workflow instance's
 * own execution state is Cloudflare's problem to persist (that's what
 * Workflows are for). Everything a human or a future session needs to
 * SEE — status, evidence, artifacts — is written to D1 as we go, not
 * left inside the Workflow's own internal state, because Workflow
 * instance data is deleted after its retention period (see gotchas).
 *
 * What this file explicitly never does: publish a round, invite a
 * reviewer, promote a B2 version, or run a fine-tune. The furthest it
 * ever gets on its own is a DRAFT round (via the exact same saveDraft()
 * the admin UI's own authoring screen uses) sitting in
 * waiting_for_human_approval — freezing/publishing remains a Cloudflare
 * Access-authenticated human action, always.
 */

import { WorkflowEntrypoint } from "cloudflare:workers";
import { sha256Hex, newId, nowIso } from "./util.js";
import { saveDraft, sortedStringify } from "./publish.js";
import { getPolicyVersion } from "./policy.js";
import { listActiveReviewerIds } from "./reviewerEligibility.js";
import { planAdditionalReview } from "./additionalReview.js";
import { applyRoundPublicationPolicy } from "./roundPublicationPolicy.js";

const JOB_WAIT_TIMEOUT = "3 days";
const MAX_ATTEMPTS_PER_JOB = 2;
const JOB_EVENT_TYPE = "calibration-job-event";

function requireKeys(obj, keys) {
  if (!obj || typeof obj !== "object") return false;
  return keys.every((k) => Object.prototype.hasOwnProperty.call(obj, k));
}

function validateAnalysisShape(result) {
  if (!requireKeys(result, ["analysis_version", "round_id", "items", "round_summary"])) return false;
  return Array.isArray(result.items);
}

function validatePrepareShape(result) {
  if (!requireKeys(result, ["status", "round_id"])) return false;
  if (result.status === "NEEDS_ELIGIBLE_CANDIDATES") return true;
  if (result.status === "DRAFT_READY") return requireKeys(result, ["draft"]) && Array.isArray(result.draft.items);
  return false;
}

export class CalibrationWorkflow extends WorkflowEntrypoint {
  async run(event, step) {
    const { run_id, round_id, workflow_version, policy_version } = event.payload;

    await step.do("mark-started", async () => {
      await this.env.DB.prepare(
        "UPDATE calibration_runs SET status='analysis_pending', started_at=COALESCE(started_at,?), current_step='analyze_human_round' WHERE run_id=?"
      )
        .bind(nowIso(), run_id)
        .run();
    });

    // Loaded ONCE, by the exact version this run was armed under (see
    // calibrationOrchestrator.js's armCalibrationRun) — never re-read as
    // "whatever is active now." A policy change made while this run is
    // durably waiting on Trident (up to 3 days) must never retroactively
    // change what this run does; it takes effect on the NEXT run armed
    // after the change, never this one.
    const policy = await step.do("load-policy", async () => {
      const row = await getPolicyVersion(this.env, policy_version);
      if (!row) throw new Error(`policy_version_not_found: ${policy_version}`);
      return row;
    });

    let analysis;
    try {
      analysis = await this.runJobWithRetries(step, run_id, "analyze_human_round", workflow_version, validateAnalysisShape, async () => {
        const exportRow = await this.env.DB.prepare("SELECT payload_json, status FROM research_exports WHERE round_id = ?")
          .bind(round_id)
          .first();
        if (!exportRow || exportRow.status !== "ready") {
          throw new Error("research_export_not_ready");
        }
        const contextRow = await this.env.DB.prepare(
          "SELECT content_json FROM calibration_artifacts WHERE round_id = ? AND artifact_type = 'research_context' ORDER BY created_at DESC LIMIT 1"
        )
          .bind(round_id)
          .first();
        return {
          round_id,
          research_export: JSON.parse(exportRow.payload_json),
          research_context: contextRow ? JSON.parse(contextRow.content_json) : null,
        };
      });
    } catch (err) {
      await this.markFailed(step, run_id, "analyze_human_round", err);
      return { status: "failed", step: "analyze_human_round" };
    }

    await step.do("record-analysis-artifact", async () => {
      const artifactId = newId("cart");
      const contentJson = JSON.stringify(analysis);
      const hash = await sha256Hex(contentJson);
      await this.env.DB.prepare(
        `INSERT INTO calibration_artifacts (artifact_id, artifact_type, round_id, run_id, workflow_version, content_json, content_sha256, created_at)
         VALUES (?, 'analysis', ?, ?, ?, ?, ?, ?)`
      )
        .bind(artifactId, round_id, run_id, workflow_version, contentJson, hash, nowIso())
        .run();
      await this.env.DB.prepare(
        "UPDATE calibration_runs SET status='evidence_updated', current_step='prepare_next_round', analysis_artifact_id=? WHERE run_id=?"
      )
        .bind(artifactId, run_id)
        .run();
      return artifactId;
    });

    // Additional review is orthogonal to next-round preparation below —
    // it targets THIS round's own contested/needs_more_reviewers items
    // using EXISTING reviewers, never the eligible-candidate pool
    // prepare-next-round-v1 draws from. Both may fire from the same
    // completed round; neither blocks the other.
    const additionalReviewResult = await step.do("plan-additional-review", async () => {
      const draftRoundId = await this.nextRoundId(round_id);
      return planAdditionalReview(this.env, {
        roundId: round_id,
        analysis,
        policy,
        nextRoundId: draftRoundId,
        actor: "system:calibration_orchestrator",
      });
    });

    await this.writeArtifact(round_id, run_id, workflow_version, "additional_review_plan", additionalReviewResult, nowIso());

    if (additionalReviewResult.status === "DRAFTED") {
      await step.do("apply-publication-policy-additional-review", async () => {
        return applyRoundPublicationPolicy(this.env, additionalReviewResult.draft_round_id, {
          policy,
          actor: "system:calibration_orchestrator",
          runId: run_id,
        });
      });
    }

    await step.do("mark-next-round-pending", async () => {
      await this.env.DB.prepare("UPDATE calibration_runs SET status='next_round_pending' WHERE run_id = ?").bind(run_id).run();
    });

    let preparation;
    try {
      preparation = await this.runJobWithRetries(step, run_id, "prepare_next_round", workflow_version, validatePrepareShape, async () => {
        const candidateRows = await this.env.DB.prepare(
          "SELECT * FROM calibration_candidates WHERE eligible_for_reader_lab = 1 AND dataset_purpose != 'held_out_evaluation'"
        ).all();
        // "Active reviewer" for automatic next-round assignment means
        // EXISTING APPROVED reviewer (not revoked AND
        // active_for_calibration — see reviewerEligibility.js), not just
        // "not revoked." A reviewer set inactive-for-calibration keeps a
        // working invitation but stops being offered new automatic work.
        const activeReviewerIds =
          policy.existing_reviewer_assignment_policy === "automatic_if_valid" ? await listActiveReviewerIds(this.env) : [];
        return {
          round_id,
          analysis,
          eligible_candidates: candidateRows.results,
          active_reviewer_ids: activeReviewerIds,
        };
      });
    } catch (err) {
      await this.markFailed(step, run_id, "prepare_next_round", err);
      return { status: "failed", step: "prepare_next_round" };
    }

    const finalStatus = await step.do("finalize-run", async () => {
      const now = nowIso();

      if (preparation.status === "NEEDS_ELIGIBLE_CANDIDATES") {
        await this.writeArtifact(round_id, run_id, workflow_version, "next_round_draft", preparation, now);
        await this.env.DB.prepare("UPDATE calibration_runs SET status='needs_eligible_candidates', completed_at=? WHERE run_id=?")
          .bind(now, run_id)
          .run();
        return "needs_eligible_candidates";
      }

      // DRAFT_READY — create a draft round via the exact same shared
      // publish.js function the admin UI's own authoring screen uses.
      // Never frozen, never published, from here.
      const draftRoundId = await this.nextRoundId(round_id);
      await saveDraft(
        this.env,
        draftRoundId,
        {
          round_id: draftRoundId,
          dataset_purpose: preparation.draft.dataset_purpose,
          task_version: "v0.1",
          research_question: preparation.draft.selection_rationale || null,
          reviewer_ids: preparation.draft.reviewer_ids,
          items: preparation.draft.items,
          source: "calibration_orchestrator",
        },
        { actor: "system:calibration_orchestrator", status: "draft" }
      );

      const artifactId = await this.writeArtifact(
        round_id,
        run_id,
        workflow_version,
        "next_round_draft",
        { ...preparation, draft_round_id: draftRoundId },
        now
      );

      // Policy decides what happens to the freshly-drafted round from
      // here — human_approval leaves it exactly as before (a draft
      // waiting in /admin); shadow_automatic computes and records the
      // decision without publishing; automatic_if_valid actually
      // publishes it through the same freeze/publish path a human uses.
      // Same function, same rules, as whatever the additional-review
      // draft above just went through — one decision point, not two.
      const decision = await applyRoundPublicationPolicy(this.env, draftRoundId, {
        policy,
        actor: "system:calibration_orchestrator",
        runId: run_id,
      });
      const finalRunStatus =
        decision.action === "published_automatically"
          ? "next_round_published_automatically"
          : decision.action === "shadow_recorded"
            ? "next_round_shadow_recorded"
            : "waiting_for_human_approval";

      await this.env.DB.prepare(
        "UPDATE calibration_runs SET status=?, completed_at=?, next_round_draft_artifact_id=? WHERE run_id=?"
      )
        .bind(finalRunStatus, now, artifactId, run_id)
        .run();
      return finalRunStatus;
    });

    return { status: finalStatus, run_id };
  }

  async writeArtifact(roundId, runId, workflowVersion, artifactType, content, createdAt) {
    const artifactId = newId("cart");
    const contentJson = JSON.stringify(content);
    const hash = await sha256Hex(contentJson);
    await this.env.DB.prepare(
      `INSERT INTO calibration_artifacts (artifact_id, artifact_type, round_id, run_id, workflow_version, content_json, content_sha256, created_at)
       VALUES (?,?,?,?,?,?,?,?)`
    )
      .bind(artifactId, artifactType, roundId, runId, workflowVersion, contentJson, hash, createdAt)
      .run();
    return artifactId;
  }

  async markFailed(step, runId, stepName, err) {
    await step.do(`mark-failed-${stepName}`, async () => {
      await this.env.DB.prepare("UPDATE calibration_runs SET status='failed', error=?, completed_at=? WHERE run_id=?")
        .bind(`${stepName}: ${String((err && err.message) || err)}`, nowIso(), runId)
        .run();
    });
  }

  // Creates a claimable calibration_jobs row, waits (durably — this
  // instance consumes no compute while waiting) for the Trident runner
  // to complete it via /ops/calibration/jobs/:id/complete, and validates
  // the result. Retries up to MAX_ATTEMPTS_PER_JOB times — a fresh job
  // row per attempt, never a mutated one, so the attempt history stays
  // visible in calibration_jobs rather than being silently overwritten.
  async runJobWithRetries(step, runId, jobType, workflowVersion, shapeValidator, inputBuilder) {
    let lastError = "unknown";
    for (let attempt = 1; attempt <= MAX_ATTEMPTS_PER_JOB; attempt++) {
      const jobId = await step.do(`create-job-${jobType}-${attempt}`, async () => {
        const input = await inputBuilder();
        const inputJson = JSON.stringify(input);
        const inputHash = await sha256Hex(inputJson);
        const id = newId("cjob");
        await this.env.DB.prepare(
          `INSERT INTO calibration_jobs (job_id, run_id, job_type, workflow_version, status, input_json, input_hash, created_at)
           VALUES (?,?,?,?, 'pending', ?,?,?)`
        )
          .bind(id, runId, jobType, workflowVersion, inputJson, inputHash, nowIso())
          .run();
        return id;
      });

      // step.waitForEvent resolves to the FULL event envelope
      // ({ payload, type, timestamp }), not just the inner payload —
      // confirmed directly against the running local Workflows engine
      // during the synthetic end-to-end test, which is what caught this
      // (the docs' own worked example reads as if the payload were
      // returned directly; empirically it is not).
      let woke = true;
      try {
        const wrapper = await step.waitForEvent(`wait-${jobType}-${attempt}`, { type: JOB_EVENT_TYPE, timeout: JOB_WAIT_TIMEOUT });
        const payload = wrapper && wrapper.payload;
        if (!payload || payload.job_id !== jobId) woke = false;
      } catch {
        woke = false;
      }

      if (!woke) {
        lastError = `timed out or wrong event waiting for ${jobType} (attempt ${attempt})`;
        continue;
      }

      const validated = await step.do(`validate-${jobType}-${attempt}`, async () => {
        const job = await this.env.DB.prepare("SELECT * FROM calibration_jobs WHERE job_id = ?").bind(jobId).first();
        if (!job) return { ok: false, error: "job_row_missing" };
        if (job.status === "failed") return { ok: false, error: job.error || "job_failed" };
        if (job.status !== "completed") return { ok: false, error: `unexpected_job_status:${job.status}` };
        let parsed;
        try {
          parsed = JSON.parse(job.result_json);
        } catch {
          return { ok: false, error: "result_json_unparseable" };
        }
        // Must match calibrationJobs.js's handleComplete exactly — that's
        // where result_hash was actually computed and validated against
        // the runner's own submission (sortedStringify, not plain
        // JSON.stringify, since that's what's comparable across the
        // Python runner's canonical_json). Re-deriving it here with a
        // different method would never match and would make every
        // successful completion look like a hash mismatch — this file
        // had exactly that bug until the synthetic end-to-end test
        // caught it (see the design doc's calibration-orchestrator
        // section for the full account).
        const recomputedHash = await sha256Hex(sortedStringify(parsed));
        if (recomputedHash !== job.result_hash) return { ok: false, error: "result_hash_mismatch" };
        if (!shapeValidator(parsed)) return { ok: false, error: "result_shape_invalid" };
        return { ok: true, result: parsed };
      });

      if (validated.ok) return validated.result;
      lastError = validated.error;
    }
    throw new Error(`${jobType} failed after ${MAX_ATTEMPTS_PER_JOB} attempts: ${lastError}`);
  }

  // RL-YYYY-NNN, next sequential number for the current year. Simple,
  // deterministic, matches ## 20.1's existing convention — not a
  // step.do because it's pure computation over an already-fetched
  // row set, no I/O of its own beyond the query itself (which the
  // caller already wraps in a step where needed).
  async nextRoundId(currentRoundId) {
    const year = currentRoundId.match(/^RL-(\d{4})-/)?.[1] || new Date().getUTCFullYear().toString();
    const rows = await this.env.DB.prepare("SELECT round_id FROM rounds WHERE round_id LIKE ?").bind(`RL-${year}-%`).all();
    let max = 0;
    for (const row of rows.results) {
      const n = parseInt(row.round_id.split("-")[2], 10);
      if (!Number.isNaN(n) && n > max) max = n;
    }
    return `RL-${year}-${String(max + 1).padStart(3, "0")}`;
  }
}
