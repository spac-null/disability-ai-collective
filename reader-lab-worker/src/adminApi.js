/**
 * Crip Minds Reader Lab — admin API (browser-facing, Cloudflare
 * Access-gated — see access.js). This is the JSON layer the /admin SPA
 * (adminUi.js) talks to. Every mutation here goes through publish.js —
 * this file never writes item/assignment content directly.
 *
 * Deliberately NOT the same surface as the legacy /admin/* routes in
 * index.js (X-Admin-Token) — those remain for CLI/automation/emergency
 * use, per the design doc. This file is the normal, human, browser path.
 */

import { secureJson, sha256Hex, randomHex, nowIso, newId } from "./util.js";
import {
  saveDraft,
  freezeRound,
  publishRound,
  setDisposition,
  validateManifest,
  canonicalizeManifest,
  getPublicationReceipt,
  writeAuditLog,
  ValidationError,
  ALLOWED_DATASET_PURPOSES,
  ALLOWED_DISPOSITIONS,
} from "./publish.js";
import { buildResearchExport, getExportStatus, getExportPayloadJson } from "./researchExport.js";
import { handleCalibrationStatus, handleCalibrationRetry, handleAutomationSummary } from "./calibrationAdmin.js";
import { getActivePolicy, listPolicyHistory, setActivePolicy, PolicyValidationError } from "./policy.js";
import { ingestCalibrationCandidates, CandidateValidationError } from "./candidateIngestion.js";
import { reconcileStuckCalibrationRuns } from "./calibrationOrchestrator.js";

function jsonError(err, fallbackStatus = 500) {
  if (err instanceof ValidationError) {
    return secureJson({ error: "validation_failed", errors: err.errors, warnings: err.warnings }, 422);
  }
  return secureJson({ error: "internal_error", detail: String(err && err.message || err) }, fallbackStatus);
}

async function readJsonBody(request) {
  try {
    return await request.json();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------
// dashboard
// ---------------------------------------------------------------------

async function roundReviewerProgress(env, roundId) {
  const rows = await env.DB.prepare(
    `SELECT reviewer_id, COUNT(*) AS assigned, SUM(CASE WHEN answered_at IS NOT NULL THEN 1 ELSE 0 END) AS answered
     FROM assignments WHERE round_id = ? GROUP BY reviewer_id`
  )
    .bind(roundId)
    .all();
  return rows.results;
}

async function roundSummary(env, round) {
  const base = {
    round_id: round.round_id,
    task_type: round.task_type,
    task_version: round.task_version,
    dataset_purpose: round.dataset_purpose,
    dataset_purpose_note: round.dataset_purpose_note,
    research_question: round.research_question,
    status: round.status,
    source: round.source,
    created_at: round.created_at,
    frozen_at: round.frozen_at,
    published_at: round.published_at,
    completed_at: round.completed_at,
    manifest_sha256: round.manifest_sha256,
    dataset_disposition: round.dataset_disposition,
  };

  if (round.status === "published" || round.status === "completed") {
    const reviewers = await roundReviewerProgress(env, round.round_id);
    const itemCountRow = await env.DB.prepare(
      "SELECT COUNT(DISTINCT item_id) AS n FROM assignments WHERE round_id = ?"
    )
      .bind(round.round_id)
      .first();
    const exportStatus = round.status === "completed" ? await getExportStatus(env, round.round_id) : null;
    return {
      ...base,
      item_count: itemCountRow.n,
      reviewer_count: reviewers.length,
      reviewers,
      // Authoritative signal is round.status itself (flipped atomically
      // by maybeCompleteRound the moment the last real response commits)
      // — not recomputed from assignments here, so there's exactly one
      // source of truth for "is this round done."
      completion_state: round.status === "completed" ? "complete" : "in_progress",
      export_status: exportStatus,
    };
  }

  const draft = await env.DB.prepare("SELECT payload_json FROM round_drafts WHERE round_id = ?").bind(round.round_id).first();
  const manifest = draft ? JSON.parse(draft.payload_json) : null;
  return {
    ...base,
    item_count: manifest ? manifest.items.length : 0,
    reviewer_count: manifest ? manifest.reviewer_ids.length : 0,
    reviewers: [],
    completion_state: "not_started",
  };
}

async function handleDashboard(request, env, identity) {
  const rounds = await env.DB.prepare("SELECT * FROM rounds ORDER BY created_at DESC").all();
  const summaries = await Promise.all(rounds.results.map((r) => roundSummary(env, r)));

  // "Current round": prefer one still in progress; otherwise keep
  // showing the most recently completed one until it has a research
  // disposition set, so finishing doesn't make a round vanish from the
  // dashboard the instant the last reviewer answers.
  const active =
    summaries.find((r) => r.status === "published") ||
    summaries.find((r) => r.status === "completed" && !r.dataset_disposition);

  const needsAttention = [];
  // dataset_disposition (development_reference/contested/hold_for_later)
  // is a deliberate human GOVERNANCE field, not something the system
  // needs an answer to before it can proceed — completion, export,
  // analysis, additional review, and next-round preparation all already
  // work correctly with it unset. Surfacing "no disposition set" as
  // ACTION REQUIRED would manufacture a task Jascha doesn't actually
  // need to do — see the design doc's candidate-bridge section (## 12
  // of the handoff this implements). It's reported separately, as
  // optional governance, never merged into needsAttention.
  const optionalGovernance = [];
  for (const r of summaries) {
    if (r.status === "draft") needsAttention.push({ round_id: r.round_id, note: "Draft — not yet reviewed or frozen." });
    if (r.status === "review") needsAttention.push({ round_id: r.round_id, note: "Ready for review — freeze when it looks right." });
    if (r.status === "frozen") needsAttention.push({ round_id: r.round_id, note: "Frozen — ready to publish." });
    if (r.status === "completed" && r.export_status && r.export_status.status === "failed") {
      needsAttention.push({ round_id: r.round_id, note: "Export error — retry from the round page." });
    }
    if (r.status === "completed" && !r.dataset_disposition) {
      optionalGovernance.push({ round_id: r.round_id, note: "Research disposition not set — optional, never required for routine operation." });
    }
  }

  // Merges in anything the policy-driven automation layer (## 26)
  // couldn't resolve on its own — a failed calibration run, or an
  // additional-review attempt that came back NEEDS_HUMAN_ACTION /
  // NEEDS_POLICY_CONFIGURATION. The dashboard's own round-status items
  // above and this automation feed are two views of the same underlying
  // idea ("does Jascha need to do anything"), so they're shown together,
  // not as two competing lists.
  const automationSummaryResponse = await handleAutomationSummary(request, env);
  const automationSummary = await automationSummaryResponse.json();
  for (const item of automationSummary.action_required) {
    if (item.type === "round_needs_review") continue; // already covered by needsAttention above
    needsAttention.push({ round_id: item.round_id, note: item.note });
  }

  return secureJson({
    active_round: active || null,
    rounds: summaries,
    needs_attention: needsAttention,
    optional_governance: optionalGovernance,
    automation: automationSummary.automation,
    policy: automationSummary.policy,
    admin_identity: identity.email,
  });
}

// ---------------------------------------------------------------------
// rounds
// ---------------------------------------------------------------------

async function handleRoundsList(request, env) {
  const rounds = await env.DB.prepare("SELECT * FROM rounds ORDER BY created_at DESC").all();
  const summaries = await Promise.all(rounds.results.map((r) => roundSummary(env, r)));
  return secureJson({ rounds: summaries });
}

async function handleRoundDetail(request, env, roundId) {
  const round = await env.DB.prepare("SELECT * FROM rounds WHERE round_id = ?").bind(roundId).first();
  if (!round) return secureJson({ error: "not_found" }, 404);
  const summary = await roundSummary(env, round);

  let items;
  if (round.status === "published" || round.status === "completed") {
    const rows = await env.DB.prepare(
      `SELECT item_id, source_snapshot, candidate_sentence, internal_note, provenance, dataset_bucket
       FROM items WHERE item_id IN (SELECT DISTINCT item_id FROM assignments WHERE round_id = ?)`
    )
      .bind(roundId)
      .all();
    items = rows.results;
  } else {
    const draft = await env.DB.prepare("SELECT payload_json FROM round_drafts WHERE round_id = ?").bind(roundId).first();
    items = draft ? JSON.parse(draft.payload_json).items : [];
  }

  const receipt = round.status === "published" || round.status === "completed" ? await getPublicationReceipt(env, roundId) : null;

  return secureJson({ ...summary, items, publication_receipt: receipt });
}

async function handleRoundCreateOrSaveDraft(request, env, identity, roundId) {
  const body = await readJsonBody(request);
  if (!body) return secureJson({ error: "invalid_json" }, 400);
  const targetRoundId = roundId || body.round_id;
  if (!targetRoundId) return secureJson({ error: "missing_round_id" }, 400);
  try {
    const { manifest } = await saveDraft(env, targetRoundId, body, { actor: identity.email, status: body.status === "review" ? "review" : "draft" });
    return secureJson({ round_id: targetRoundId, manifest });
  } catch (err) {
    return jsonError(err);
  }
}

async function handleRoundFreeze(request, env, identity, roundId) {
  const body = (await readJsonBody(request)) || {};
  try {
    const draft = await env.DB.prepare("SELECT payload_json FROM round_drafts WHERE round_id = ?").bind(roundId).first();
    if (!draft) return secureJson({ error: "no_draft_to_freeze" }, 400);
    const manifest = JSON.parse(draft.payload_json);
    const result = await freezeRound(env, roundId, { ...manifest, ...body }, { actor: identity.email });
    return secureJson({ round_id: roundId, manifest_sha256: result.manifestHash, warnings: result.warnings });
  } catch (err) {
    return jsonError(err);
  }
}

async function handleRoundPublish(request, env, identity, roundId) {
  try {
    const result = await publishRound(env, roundId, { actor: identity.email });
    return secureJson({ round_id: roundId, ...result });
  } catch (err) {
    return jsonError(err);
  }
}

async function handleRoundDisposition(request, env, identity, roundId) {
  const body = await readJsonBody(request);
  if (!body || !body.disposition) return secureJson({ error: "missing_disposition" }, 400);
  try {
    await setDisposition(env, roundId, body.disposition, { actor: identity.email });
    return secureJson({ round_id: roundId, dataset_disposition: body.disposition });
  } catch (err) {
    return jsonError(err);
  }
}

// ---------------------------------------------------------------------
// import
// ---------------------------------------------------------------------

async function handleImport(request, env, identity) {
  const body = await readJsonBody(request);
  if (!body || !body.manifest) return secureJson({ error: "missing_manifest" }, 400);
  const action = body.action || "validate";

  let canonical;
  try {
    canonical = canonicalizeManifest(body.manifest).manifest;
  } catch (err) {
    return jsonError(err, 400);
  }
  if (body.round_id) canonical.round_id = body.round_id;

  const { valid, errors, warnings } = await validateManifest(env, canonical);

  if (action === "validate" || !valid) {
    return secureJson({ valid, errors, warnings, preview: canonical });
  }

  try {
    if (action === "save_draft") {
      await saveDraft(env, canonical.round_id, { ...canonical, source: "import" }, { actor: identity.email, status: "draft" });
      await writeAuditLog(env, { action: "manifest_imported", entityType: "round", entityId: canonical.round_id, actor: identity.email, detail: { as: "draft" } });
      return secureJson({ valid, errors, warnings, round_id: canonical.round_id, saved_as: "draft" });
    }
    if (action === "freeze_and_publish") {
      await freezeRound(env, canonical.round_id, { ...canonical, source: "import" }, { actor: identity.email });
      const result = await publishRound(env, canonical.round_id, { actor: identity.email });
      await writeAuditLog(env, { action: "manifest_imported", entityType: "round", entityId: canonical.round_id, actor: identity.email, detail: { as: "published" } });
      return secureJson({ valid, errors, warnings, round_id: canonical.round_id, ...result });
    }
    return secureJson({ error: `unknown_action: ${action}` }, 400);
  } catch (err) {
    return jsonError(err);
  }
}

// ---------------------------------------------------------------------
// results
// ---------------------------------------------------------------------

async function handleResults(request, env, roundId) {
  const round = await env.DB.prepare("SELECT round_id FROM rounds WHERE round_id = ?").bind(roundId).first();
  if (!round) return secureJson({ error: "not_found" }, 404);

  const responses = await env.DB.prepare(
    `SELECT r.item_id, r.reviewer_id, r.selected_public_response, r.internal_normalized_response,
            r.confidence, r.comment, r.timestamp, i.source_snapshot, i.candidate_sentence
     FROM responses r
     JOIN items i ON i.item_id = r.item_id
     WHERE r.item_id IN (SELECT DISTINCT item_id FROM assignments WHERE round_id = ?) AND r.practice_or_real = 'real'
     ORDER BY r.item_id, r.timestamp`
  )
    .bind(roundId)
    .all();

  const byItem = new Map();
  for (const row of responses.results) {
    if (!byItem.has(row.item_id)) {
      byItem.set(row.item_id, {
        item_id: row.item_id,
        source_snapshot: row.source_snapshot,
        candidate_sentence: row.candidate_sentence,
        judgments: [],
      });
    }
    byItem.get(row.item_id).judgments.push({
      reviewer_id: row.reviewer_id,
      selected_public_response: row.selected_public_response,
      internal_normalized_response: row.internal_normalized_response,
      confidence: row.confidence,
      comment: row.comment,
      timestamp: row.timestamp,
    });
  }

  const items = [...byItem.values()].map((item) => {
    const distinctAnswers = new Set(item.judgments.map((j) => j.internal_normalized_response));
    const agreement =
      item.judgments.length < 2 ? "single_judgment" : distinctAnswers.size === 1 ? "agreement" : "disagreement";
    return { ...item, agreement };
  });

  return secureJson({ round_id: roundId, items });
}

// ---------------------------------------------------------------------
// research export (completed rounds only) — browser download, no
// ADMIN_TOKEN/EXPORT_TOKEN ever involved; Cloudflare Access already
// authenticated this request before adminApiFetch was even called.
// ---------------------------------------------------------------------

async function handleExportStatus(request, env, roundId) {
  const round = await env.DB.prepare("SELECT status FROM rounds WHERE round_id = ?").bind(roundId).first();
  if (!round) return secureJson({ error: "not_found" }, 404);
  const status = await getExportStatus(env, roundId);
  return secureJson({ round_id: roundId, round_status: round.status, ...status });
}

async function handleExportRetry(request, env, identity, roundId) {
  try {
    const result = await buildResearchExport(env, roundId, { actor: identity.email });
    return secureJson({ round_id: roundId, status: result.status, error: result.error, generated_at: result.generated_at });
  } catch (err) {
    return jsonError(err);
  }
}

async function handleExportDownload(request, env, roundId) {
  const round = await env.DB.prepare("SELECT status FROM rounds WHERE round_id = ?").bind(roundId).first();
  if (!round) return secureJson({ error: "not_found" }, 404);
  if (round.status !== "completed") {
    return secureJson({ error: "round_not_completed", round_status: round.status }, 409);
  }
  const payloadJson = await getExportPayloadJson(env, roundId);
  if (!payloadJson) {
    return secureJson({ error: "export_not_ready" }, 409);
  }
  return new Response(payloadJson, {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "content-disposition": `attachment; filename="${roundId}-completed.json"`,
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}

// ---------------------------------------------------------------------
// policy — versioned, append-only (see src/policy.js). Viewing/changing
// calibration policy is one of the four things the design doc's `## 26`
// keeps as Jascha's own job — this is the one write path for it, gated
// by the same Cloudflare Access identity as every other admin action.
// ---------------------------------------------------------------------

async function handlePolicyGet(request, env) {
  const active = await getActivePolicy(env);
  const history = await listPolicyHistory(env);
  return secureJson({ active, history });
}

async function handlePolicySet(request, env, identity) {
  const body = (await readJsonBody(request)) || {};
  try {
    const policy = await setActivePolicy(env, body, { actor: identity.email, notes: body.notes });
    await writeAuditLog(env, {
      action: "policy_changed",
      entityType: "policy",
      entityId: String(policy.policy_version),
      actor: identity.email,
      detail: body,
    });
    return secureJson({ policy });
  } catch (err) {
    if (err instanceof PolicyValidationError) {
      return secureJson({ error: "validation_failed", errors: err.errors }, 422);
    }
    return jsonError(err);
  }
}

// ---------------------------------------------------------------------
// calibration candidates — read-mostly visibility, plus an import
// fallback that goes through the exact same candidateIngestion.js
// service the runner's own machine path uses (see index.js's
// /ops/calibration/candidates). Routine operation should never require
// this screen — it exists for recovery/debugging and for Jascha to see
// what's eligible without a D1 query.
// ---------------------------------------------------------------------

async function handleCandidatesList(request, env) {
  const rows = await env.DB.prepare(
    `SELECT candidate_id, provenance, dataset_purpose, eligible_for_reader_lab, internal_rationale,
            ingested_via, ingestion_actor, created_at, candidate_claim_id
     FROM calibration_candidates ORDER BY created_at DESC`
  ).all();

  // "already reviewed / assigned" -- whether this exact claim already
  // exists as a live Reader Lab item, and if so, how many
  // assignments/responses it has. Read-only, no response content.
  const candidates = await Promise.all(
    rows.results.map(async (c) => {
      const item = await env.DB.prepare("SELECT item_id FROM items WHERE candidate_claim_id = ?").bind(c.candidate_claim_id).first();
      let assignmentCount = 0;
      let answeredCount = 0;
      if (item) {
        const counts = await env.DB.prepare(
          "SELECT COUNT(*) AS assigned, SUM(CASE WHEN answered_at IS NOT NULL THEN 1 ELSE 0 END) AS answered FROM assignments WHERE item_id = ?"
        )
          .bind(item.item_id)
          .first();
        assignmentCount = counts.assigned || 0;
        answeredCount = counts.answered || 0;
      }
      return {
        candidate_id: c.candidate_id,
        provenance: c.provenance,
        dataset_purpose: c.dataset_purpose,
        held_out: c.dataset_purpose === "held_out_evaluation",
        eligible_for_reader_lab: !!c.eligible_for_reader_lab,
        internal_rationale: c.internal_rationale,
        ingested_via: c.ingested_via,
        ingestion_actor: c.ingestion_actor,
        created_at: c.created_at,
        already_live_item_id: item ? item.item_id : null,
        assigned_count: assignmentCount,
        answered_count: answeredCount,
      };
    })
  );
  return secureJson({ candidates });
}

async function handleCandidatesImport(request, env, identity) {
  const body = await readJsonBody(request);
  if (!body || !body.bundle) return secureJson({ error: "missing_bundle" }, 400);
  try {
    const result = await ingestCalibrationCandidates(env, body.bundle, { actor: identity.email, ingestedVia: "admin_import" });
    let reconciliation = null;
    if (result.newly_eligible_candidate_count > 0) {
      reconciliation = await reconcileStuckCalibrationRuns(env, { actor: "system:candidate_ingestion_reconciliation" });
    }
    return secureJson({ ...result, reconciliation });
  } catch (err) {
    if (err instanceof CandidateValidationError) {
      return secureJson({ error: "validation_failed", errors: err.errors }, 422);
    }
    return jsonError(err);
  }
}

// ---------------------------------------------------------------------
// reviewers
// ---------------------------------------------------------------------

async function handleReviewersList(request, env) {
  const rows = await env.DB.prepare(
    `SELECT i.reviewer_id, i.created_at, i.expires_at, i.revoked, i.practice_completed,
            i.active_for_calibration, i.max_items_per_round,
            COUNT(a.assignment_id) AS total_assigned,
            SUM(CASE WHEN a.answered_at IS NOT NULL THEN 1 ELSE 0 END) AS total_answered
     FROM invitations i
     LEFT JOIN assignments a ON a.reviewer_id = i.reviewer_id
     GROUP BY i.reviewer_id
     ORDER BY i.created_at`
  ).all();
  return secureJson({ reviewers: rows.results });
}

// Distinct from revoke/reactivate: a reviewer can remain a valid, working
// account (credential intact, past responses untouched) while no longer
// being offered new AUTOMATIC assignments — see reviewerEligibility.js's
// own docstring for why `revoked` alone can't express this. Setting
// active_for_calibration=0 never touches an invitation's token/session.
async function handleReviewerSetEligibility(request, env, identity, reviewerId) {
  const body = (await readJsonBody(request)) || {};
  const fields = [];
  const values = [];
  if (Object.prototype.hasOwnProperty.call(body, "active_for_calibration")) {
    fields.push("active_for_calibration = ?");
    values.push(body.active_for_calibration ? 1 : 0);
  }
  if (Object.prototype.hasOwnProperty.call(body, "max_items_per_round")) {
    const n = body.max_items_per_round;
    if (n !== null && (!Number.isInteger(n) || n <= 0)) {
      return secureJson({ error: "max_items_per_round must be a positive integer or null" }, 400);
    }
    fields.push("max_items_per_round = ?");
    values.push(n);
  }
  if (!fields.length) return secureJson({ error: "no_fields_to_update" }, 400);
  await env.DB.prepare(`UPDATE invitations SET ${fields.join(", ")} WHERE reviewer_id = ?`)
    .bind(...values, reviewerId)
    .run();
  await writeAuditLog(env, { action: "reviewer_eligibility_changed", entityType: "reviewer", entityId: reviewerId, actor: identity.email, detail: body });
  return secureJson({ ok: true });
}

async function handleReviewerCreate(request, env, identity) {
  const body = (await readJsonBody(request)) || {};
  const reviewerId = body.reviewer_id || `reader_${randomHex(3)}`;
  const token = randomHex(24);
  const tokenHash = await sha256Hex(token);
  const now = nowIso();
  await env.DB.prepare(
    `INSERT INTO invitations (reviewer_id, token_hash, contact_channel, created_at, expires_at, revoked, practice_completed)
     VALUES (?,?,?,?,?,0,0)`
  )
    .bind(reviewerId, tokenHash, body.contact_channel || null, now, body.expires_at || null)
    .run();
  await writeAuditLog(env, { action: "reviewer_created", entityType: "reviewer", entityId: reviewerId, actor: identity.email });
  return secureJson({ reviewer_id: reviewerId, token, invite_url_path: `/invite/${token}` });
}

async function handleReviewerRevoke(request, env, identity, reviewerId) {
  await env.DB.prepare("UPDATE invitations SET revoked = 1 WHERE reviewer_id = ?").bind(reviewerId).run();
  await writeAuditLog(env, { action: "reviewer_revoked", entityType: "reviewer", entityId: reviewerId, actor: identity.email });
  return secureJson({ ok: true });
}

async function handleReviewerReactivate(request, env, identity, reviewerId) {
  await env.DB.prepare("UPDATE invitations SET revoked = 0 WHERE reviewer_id = ?").bind(reviewerId).run();
  await writeAuditLog(env, { action: "reviewer_reactivated", entityType: "reviewer", entityId: reviewerId, actor: identity.email });
  return secureJson({ ok: true });
}

// ---------------------------------------------------------------------
// router
// ---------------------------------------------------------------------

export async function adminApiFetch(request, env, identity, url) {
  const path = url.pathname.replace(/^\/admin\/api/, "") || "/";
  const method = request.method;
  let m;

  if (path === "/dashboard" && method === "GET") return handleDashboard(request, env, identity);
  if (path === "/meta" && method === "GET")
    return secureJson({ dataset_purposes: ALLOWED_DATASET_PURPOSES, dispositions: ALLOWED_DISPOSITIONS });

  if (path === "/rounds" && method === "GET") return handleRoundsList(request, env);
  if (path === "/rounds" && method === "POST") return handleRoundCreateOrSaveDraft(request, env, identity, null);

  if ((m = /^\/rounds\/([^/]+)$/.exec(path)) && method === "GET") return handleRoundDetail(request, env, m[1]);
  if ((m = /^\/rounds\/([^/]+)$/.exec(path)) && (method === "PUT" || method === "POST"))
    return handleRoundCreateOrSaveDraft(request, env, identity, m[1]);
  if ((m = /^\/rounds\/([^/]+)\/freeze$/.exec(path)) && method === "POST") return handleRoundFreeze(request, env, identity, m[1]);
  if ((m = /^\/rounds\/([^/]+)\/publish$/.exec(path)) && method === "POST") return handleRoundPublish(request, env, identity, m[1]);
  if ((m = /^\/rounds\/([^/]+)\/disposition$/.exec(path)) && method === "POST")
    return handleRoundDisposition(request, env, identity, m[1]);
  if ((m = /^\/rounds\/([^/]+)\/export\/status$/.exec(path)) && method === "GET")
    return handleExportStatus(request, env, m[1]);
  if ((m = /^\/rounds\/([^/]+)\/export\/retry$/.exec(path)) && method === "POST")
    return handleExportRetry(request, env, identity, m[1]);
  if ((m = /^\/rounds\/([^/]+)\/export\/download$/.exec(path)) && method === "GET")
    return handleExportDownload(request, env, m[1]);

  if (path === "/import" && method === "POST") return handleImport(request, env, identity);

  if ((m = /^\/results\/([^/]+)$/.exec(path)) && method === "GET") return handleResults(request, env, m[1]);

  if (path === "/calibration/status" && method === "GET") return handleCalibrationStatus(request, env, url);
  if (path === "/calibration/automation" && method === "GET") return handleAutomationSummary(request, env);
  if ((m = /^\/calibration\/runs\/([^/]+)\/retry$/.exec(path)) && method === "POST")
    return handleCalibrationRetry(request, env, identity, m[1]);

  if (path === "/policy" && method === "GET") return handlePolicyGet(request, env);
  if (path === "/policy" && method === "POST") return handlePolicySet(request, env, identity);

  if (path === "/candidates" && method === "GET") return handleCandidatesList(request, env);
  if (path === "/candidates/import" && method === "POST") return handleCandidatesImport(request, env, identity);

  if (path === "/reviewers" && method === "GET") return handleReviewersList(request, env);
  if (path === "/reviewers" && method === "POST") return handleReviewerCreate(request, env, identity);
  if ((m = /^\/reviewers\/([^/]+)\/revoke$/.exec(path)) && method === "POST")
    return handleReviewerRevoke(request, env, identity, m[1]);
  if ((m = /^\/reviewers\/([^/]+)\/reactivate$/.exec(path)) && method === "POST")
    return handleReviewerReactivate(request, env, identity, m[1]);
  if ((m = /^\/reviewers\/([^/]+)\/eligibility$/.exec(path)) && method === "POST")
    return handleReviewerSetEligibility(request, env, identity, m[1]);

  return secureJson({ error: "not_found" }, 404);
}
