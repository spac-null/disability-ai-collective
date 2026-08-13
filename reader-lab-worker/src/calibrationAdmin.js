/**
 * Crip Minds Reader Lab — calibration admin API (browser-facing, behind
 * adminApi.js's Cloudflare Access gate). Read-mostly: the only mutation
 * is "retry a failed run," which creates a fresh calibration_runs row +
 * Workflow instance — it never touches a response, export, or published
 * round.
 */

import { secureJson } from "./util.js";
import { armFreshCalibrationRun } from "./calibrationOrchestrator.js";
import { getActivePolicy } from "./policy.js";

// Labels the design doc's `## 26` automation cockpit shows Jascha — one
// line per routine decision category, derived from the active policy,
// never hard-coded to "automatic" independent of what the policy
// actually says. additional_review specifically surfaces the
// NEEDS_POLICY_CONFIGURATION case (policy says automatic, but the
// required count is unset) as its own label, since "automatic" would
// otherwise overstate what the system can currently do.
function automationStateFromPolicy(policy) {
  return {
    round_construction: "Automatic",
    analysis: "Automatic",
    existing_reviewer_assignment: policy.existing_reviewer_assignment_policy === "automatic_if_valid" ? "Automatic" : "Manual",
    additional_review:
      policy.additional_review_policy === "disabled"
        ? "Disabled"
        : policy.additional_review_policy === "manual"
          ? "Manual"
          : policy.additional_reviewers_per_contested_item == null
            ? "Policy-driven — not yet configured (set a reviewer count in Policy)"
            : "Policy-driven — automatic when eligible",
    publication:
      policy.round_publication_policy === "human_approval"
        ? "Human approval"
        : policy.round_publication_policy === "shadow_automatic"
          ? "Shadow — recorded, never acted on"
          : "Automatic when valid",
    candidate_experiments: policy.candidate_experiment_policy === "research_gated" ? "Infrastructure-ready — research-gated" : policy.candidate_experiment_policy,
    fine_tune_experiments: policy.fine_tune_experiment_policy === "disabled" ? "Disabled" : policy.fine_tune_experiment_policy,
    production_promotion: "Human only (fixed — no policy can change this)",
  };
}

export async function publicationDecisionForRound(env, draftRoundId) {
  if (!draftRoundId) return null;
  const row = await env.DB.prepare(
    "SELECT content_json FROM calibration_artifacts WHERE round_id = ? AND artifact_type = 'publication_policy_decision' ORDER BY created_at DESC LIMIT 1"
  )
    .bind(draftRoundId)
    .first();
  return row ? JSON.parse(row.content_json) : null;
}

// Cross-round "does anything need Jascha right now" — draft/review/
// frozen rounds waiting on him, failed calibration runs, and any
// additional-review attempt that came back NEEDS_HUMAN_ACTION or
// NEEDS_POLICY_CONFIGURATION. Deliberately does not include
// shadow-mode publication decisions here — a shadow decision is
// informational (see Calibration), never something Jascha must act on.
export async function handleAutomationSummary(request, env) {
  const policy = await getActivePolicy(env);
  const actionRequired = [];

  // Only genuinely blocking states surface here — a mid-edit draft is
  // Jascha's own unfinished work, never a surprise, and never listed
  // (see adminApi.js's handleDashboard, which covers "frozen — ready to
  // send" directly with plain wording; round_needs_review below exists
  // only so /admin/api/calibration/automation on its own still reports
  // frozen rounds, without duplicating that note twice on the Dashboard).
  const rounds = await env.DB.prepare("SELECT round_id, status FROM rounds WHERE status = 'frozen' ORDER BY created_at DESC").all();
  for (const r of rounds.results) {
    actionRequired.push({ type: "round_needs_review", round_id: r.round_id, note: `${r.round_id} is ready to send — review and publish when you're ready.` });
  }

  const failedRuns = await env.DB.prepare("SELECT run_id, round_id FROM calibration_runs WHERE status = 'failed' ORDER BY created_at DESC LIMIT 10").all();
  for (const r of failedRuns.results) {
    actionRequired.push({ type: "calibration_failed", round_id: r.round_id, run_id: r.run_id, note: `${r.round_id}: something needs your attention — see Calibration.` });
  }

  // A round can accumulate more than one additional_review_plan artifact
  // over time — one per calibration run, and a round gets a fresh run
  // every time one is armed (manual retry, or the reconciliation sweep
  // resuming a stuck run). Without deduping by round_id here, a round
  // whose shortage of eligible reviewers hasn't been fixed yet produces
  // one action-required card per re-run, not one per round. Rows arrive
  // ORDER BY created_at DESC, so the first row seen for a given round_id
  // is always its latest plan.
  const recentPlans = await env.DB.prepare(
    "SELECT round_id, content_json, created_at FROM calibration_artifacts WHERE artifact_type = 'additional_review_plan' ORDER BY created_at DESC LIMIT 20"
  ).all();
  const latestPlanByRound = new Map();
  for (const row of recentPlans.results) {
    if (!latestPlanByRound.has(row.round_id)) latestPlanByRound.set(row.round_id, row);
  }
  for (const row of latestPlanByRound.values()) {
    let plan;
    try {
      plan = JSON.parse(row.content_json);
    } catch {
      continue;
    }
    if (plan.status === "NEEDS_HUMAN_ACTION" || plan.status === "NEEDS_POLICY_CONFIGURATION") {
      const count = (plan.flagged_items || []).length;
      actionRequired.push({
        type: `additional_review_${plan.status.toLowerCase()}`,
        round_id: row.round_id,
        note:
          plan.status === "NEEDS_POLICY_CONFIGURATION"
            ? `${row.round_id}: ${count} question${count === 1 ? "" : "s"} would benefit from one more independent reviewer, but this isn't configured yet.`
            : `${row.round_id}: ${count} question${count === 1 ? "" : "s"} would benefit from one more independent reviewer. There are currently no other approved reviewers available.`,
      });
    }
  }

  return secureJson({
    policy,
    automation: automationStateFromPolicy(policy),
    action_required: actionRequired,
    no_action_required: actionRequired.length === 0,
  });
}

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
    `SELECT a.reviewer_id, i.display_name, COUNT(*) AS assigned, SUM(CASE WHEN a.answered_at IS NOT NULL THEN 1 ELSE 0 END) AS answered
     FROM assignments a JOIN invitations i ON i.reviewer_id = a.reviewer_id
     WHERE a.round_id = ? GROUP BY a.reviewer_id`
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
    const waiting = reviewers.filter((r) => r.answered < r.assigned).map((r) => r.display_name || r.reviewer_id);
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

// Everything the Calibration screen needs for one round, factored out so
// roundSummary() (adminApi.js — used by Dashboard/Rounds cards) can pull
// the same plain-language-able facts (evidence counts, additional-review
// outcome, shadow decision) without a second, drifting query path.
// Returns null fields rather than throwing when nothing has run yet.
export async function getCalibrationSummaryForRound(env, roundId) {
  const round = await env.DB.prepare("SELECT * FROM rounds WHERE round_id = ?").bind(roundId).first();
  if (!round) return null;

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

  // Additional review runs alongside next-round preparation, not instead
  // of it (see calibrationWorkflow.js) — surfaced separately so "did this
  // round's disagreement get a follow-up reviewer" is answerable without
  // digging into raw artifacts. Each of the two draft-producing steps
  // (additional review, next-round prep) can have its own recorded
  // publication decision — shadow or live — once policy has anything to
  // say about it.
  let additionalReviewPlan = null;
  if (run) {
    const artifact = await env.DB.prepare(
      "SELECT content_json FROM calibration_artifacts WHERE run_id = ? AND artifact_type = 'additional_review_plan' ORDER BY created_at DESC LIMIT 1"
    )
      .bind(run.run_id)
      .first();
    if (artifact) additionalReviewPlan = JSON.parse(artifact.content_json);
  }

  const nextRoundPublicationDecision = await publicationDecisionForRound(env, nextRoundDraft && nextRoundDraft.draft_round_id);
  const additionalReviewPublicationDecision = await publicationDecisionForRound(env, additionalReviewPlan && additionalReviewPlan.draft_round_id);

  return {
    round_id: roundId,
    round_status: round.status,
    policy_version: run ? run.policy_version : null,
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
    next_round_publication_decision: nextRoundPublicationDecision,
    additional_review: additionalReviewPlan,
    additional_review_publication_decision: additionalReviewPublicationDecision,
    next_action: nextActionForRound(round, run, reviewers),
  };
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

  const summary = await getCalibrationSummaryForRound(env, roundId);
  if (!summary) return secureJson({ error: "not_found" }, 404);

  const run = summary.calibration_run
    ? await env.DB.prepare("SELECT * FROM calibration_runs WHERE run_id = ?").bind(summary.calibration_run.run_id).first()
    : null;
  const history = await buildHistory(env, roundId, run);

  return secureJson({ ...summary, history });
}

export async function handleCalibrationRetry(request, env, identity, runId) {
  const failedRun = await env.DB.prepare("SELECT * FROM calibration_runs WHERE run_id = ?").bind(runId).first();
  if (!failedRun) return secureJson({ error: "not_found" }, 404);
  if (failedRun.status !== "failed") {
    return secureJson({ error: "run_not_failed", status: failedRun.status }, 409);
  }

  // Same "fresh run from scratch" mechanism the automatic candidate-
  // ingestion reconciliation uses for a run stuck at
  // needs_eligible_candidates (calibrationOrchestrator.js) — a human
  // retry and an automatic resume are the same underlying situation.
  const result = await armFreshCalibrationRun(env, failedRun, { actor: identity.email, reason: "human_retry" });
  if (!result.armed) {
    return secureJson({ error: "workflow_create_failed", detail: result.error }, 500);
  }
  return secureJson({ ok: true, run_id: result.run_id });
}
