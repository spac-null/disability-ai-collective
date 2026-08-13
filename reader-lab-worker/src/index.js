/**
 * Crip Minds Reader Lab v0 — Cloudflare Worker
 *
 * Written, NOT deployed. See ../README.md for what deploying requires.
 * Hardened per the 2026-08-12 production-readiness audit — see
 * ../.claude/reader-lab-v0-design-2026-08-12.md and this pass's report
 * for what changed and why.
 *
 * Routes:
 *   GET  /invite/:token         validate invitation token, mint a session
 *                                cookie, 302 redirect to /session (the
 *                                token never appears in any URL again)
 *   GET  /session                serve the reviewer app shell (cookie auth)
 *   GET  /api/session            next batch, practice or real (cookie auth)
 *   POST /api/response           record one judgment (cookie auth)
 *   POST /ops/invitations        create a reviewer + token (X-Admin-Token)
 *   POST /ops/invitations/revoke revoke an invitation + its sessions (X-Admin-Token)
 *   POST /ops/items              create an item (X-Admin-Token)
 *   POST /ops/assignments        assign items to reviewer(s) (X-Admin-Token)
 *   GET  /ops/status             per-reviewer completion status (X-Admin-Token or X-Export-Token)
 *   GET  /ops/export             dump raw responses (X-Admin-Token or X-Export-Token)
 *   POST /ops/publish            one-shot manifest publish, for automation (X-Admin-Token)
 *   GET  /ops/rounds/:id/export  completed round's research export, read-only (X-Admin-Token or X-Export-Token)
 *   POST /ops/calibration/jobs/claim            claim a pending calibration job (X-Calibration-Runner-Token)
 *   POST /ops/calibration/jobs/:id/heartbeat    extend a claimed job's lease (X-Calibration-Runner-Token)
 *   POST /ops/calibration/jobs/:id/complete     submit a hash-validated result (X-Calibration-Runner-Token)
 *   POST /ops/calibration/jobs/:id/fail         report a failed attempt (X-Calibration-Runner-Token)
 *   POST /ops/calibration/candidates            B2 -> Reader Lab candidate bridge (X-Calibration-Runner-Token or X-Admin-Token)
 *
 *   GET  /admin                  admin control-plane UI (Cloudflare Access)
 *   *    /admin/api/*            admin control-plane JSON API (Cloudflare Access) — see adminApi.js
 *                                 (includes /rounds/:id/export/{status,download,retry}, /calibration/*, /policy, /candidates)
 *
 * A round completes itself (no route needed) — see maybeCompleteRound in
 * publish.js, called from handleResponse the instant the last reviewer's
 * assignment is answered. Research export generation is triggered from
 * that same moment via ctx.waitUntil — see buildResearchExport in
 * researchExport.js — plus an hourly scheduled() cron reconciliation
 * (see wrangler.toml's [triggers]) as a safety net for the rare case
 * where the background attempt failed. The moment the export is ready,
 * armCalibrationRun (calibrationOrchestrator.js) creates exactly one
 * Cloudflare Workflow instance (CalibrationWorkflow, see
 * calibrationWorkflow.js) for that round's calibration cycle — idempotent
 * by construction, keyed on round_id + export content hash + workflow
 * version, never duplicated by a replayed trigger or the same hourly
 * cron sweep. The Workflow creates claimable calibration_jobs rows that
 * only the private, Tailscale-only Trident runner
 * (calibration/runner/calibration_runner.py) ever picks up, via the
 * /ops/calibration/jobs/* routes above — this Worker has no direct
 * network path to Trident, and does not need one.
 *
 * CALIBRATION_RUNNER_TOKEN is a third, separate credential from
 * ADMIN_TOKEN/EXPORT_TOKEN — see requireCalibrationRunner. It can claim/
 * heartbeat/complete/fail a calibration job and nothing else.
 *
 * /ops/* deliberately does NOT share a path prefix with /admin — Cloudflare
 * Access's self-hosted app model protects a path and every subpath beneath
 * it, with no way to carve out an exception. Confirmed directly against
 * the live Access API: scoping the Access app to "lab.cripminds.com/admin"
 * alone still intercepted /admin/status, /admin/export, etc. before they
 * ever reached this Worker. /ops/* used to live under /admin/* — moved
 * here specifically to fix that.
 *
 * Two legacy admin credentials, least-privilege, machine/CLI use only —
 * never the normal human path (see README.md "Admin control plane"):
 * ADMIN_TOKEN can do everything above under /ops/*; EXPORT_TOKEN can only
 * ever reach the two read-only routes (/ops/status, /ops/export). Hand
 * EXPORT_TOKEN to a session that only needs to read pilot results; keep
 * ADMIN_TOKEN reserved for automation/emergency use. The normal human path
 * is /admin, authenticated via Cloudflare Access (access.js) — ADMIN_TOKEN
 * never reaches a browser.
 *
 * Design invariants this file exists to enforce (see the design doc — do
 * not relax without updating it):
 *   - client never supplies canonical source/candidate text; item content
 *     is always resolved server-side from item_id
 *   - a reviewer can only answer items actually assigned to them
 *   - practice responses never enter the real dataset (practice_or_real)
 *   - no response computation/aggregation happens in this file — raw
 *     storage only; agreement/consensus is a separate, later, manual step
 *   - the invitation token is a credential: never stored raw, never
 *     appears in a URL/body/log after the one-time /invite/:token visit
 *   - a submitted real response is immutable — first write wins
 */

import {
  BASE_SECURITY_HEADERS,
  secureJson,
  notFound,
  secureHtml,
  redirect,
  sha256Hex,
  randomHex,
  newNonce,
  newId,
  nowIso,
  timingSafeEqual,
  clientIp,
  parseCookie,
  checkRateLimit,
  isRateLimited,
  recordRateLimitAttempt,
} from "./util.js";
import { requireAccessAuth } from "./access.js";
import { adminApiFetch } from "./adminApi.js";
import { renderAdminShell } from "./adminUi.js";
import { directPublishFromManifest, maybeCompleteRound, ValidationError } from "./publish.js";
import { buildResearchExport } from "./researchExport.js";
import { armCalibrationRun, reconcileStuckCalibrationRuns } from "./calibrationOrchestrator.js";
import { calibrationJobsFetch } from "./calibrationJobs.js";
import { ingestCalibrationCandidates, CandidateValidationError } from "./candidateIngestion.js";

// Cloudflare Workflows require the class to be exported from the
// entrypoint file itself (this file) — re-exporting from
// calibrationWorkflow.js here, rather than defining it directly in this
// already-large file, keeps the Workflow's own logic in its own module.
export { CalibrationWorkflow } from "./calibrationWorkflow.js";

const PUBLIC_TO_INTERNAL = {
  source_supports: "source_established",
  reading_of_source: "interpretive_only",
  adds_unestablished: "unsupported_factual_dependency",
  not_sure: "uncertain",
};

const TASK_VERSION = "v0.1";
const ASSIGNMENT_VERSION = "v0.1";
const CLIENT_INTERFACE_VERSION = "reader-lab-v0.1";
const SESSION_BATCH_SIZE = 5;
const MAX_COMMENT_LENGTH = 500;
const SESSION_COOKIE_NAME = "rl_session";
const SESSION_TTL_SECONDS = 30 * 24 * 60 * 60; // 30 days — long enough for "a few items today, more next week"

// Rate limits are generous by design (v0 is a 2-person invited pilot) —
// they exist to blunt automated guessing, not to add friction to the
// two or three real visits a reviewer will ever make.
const RATE_LIMITS = {
  invite_attempt: { max: 30, windowSeconds: 300 },   // per IP, /invite/:token
  session_lookup: { max: 60, windowSeconds: 300 },   // per IP, cookie-based lookups
  admin_auth_fail: { max: 10, windowSeconds: 300 },  // per IP, wrong X-Admin-Token or X-Export-Token
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    try {
      let inviteMatch;
      if (url.pathname === "/session" && request.method === "GET") {
        return await handleSessionPage(request, env);
      }
      if (url.pathname === "/api/session" && request.method === "GET") {
        return await handleApiSession(request, env);
      }
      if (url.pathname === "/api/response" && request.method === "POST") {
        return await handleResponse(request, env, ctx);
      }
      // Legacy machine routes (X-Admin-Token / X-Export-Token) live under
      // /ops/*, NOT /admin/* — deliberately a disjoint path prefix.
      // Cloudflare Access's self-hosted app model protects a path AND
      // every subpath beneath it with no way to carve out an exception
      // (confirmed directly against the live Access API this pass —
      // scoping the app to "lab.cripminds.com/admin" alone still swept in
      // /admin/status, /admin/export, etc.). Sharing the /admin prefix
      // with the Access-protected browser control plane was found to be
      // unfixable from the Access side alone, so these routes moved here
      // instead — see README.md's "Admin control plane" section.
      if (url.pathname === "/ops/invitations" && request.method === "POST") {
        return await requireAdmin(request, env, handleAdminCreateInvitation);
      }
      if (url.pathname === "/ops/invitations/revoke" && request.method === "POST") {
        return await requireAdmin(request, env, handleAdminRevokeInvitation);
      }
      if (url.pathname === "/ops/items" && request.method === "POST") {
        return await requireAdmin(request, env, handleAdminCreateItem);
      }
      if (url.pathname === "/ops/assignments" && request.method === "POST") {
        return await requireAdmin(request, env, handleAdminCreateAssignments);
      }
      if (url.pathname === "/ops/status" && request.method === "GET") {
        return await requireReadAccess(request, env, handleAdminStatus);
      }
      if (url.pathname === "/ops/export" && request.method === "GET") {
        return await requireReadAccess(request, env, handleAdminExport);
      }
      // Machine read path for a completed round's research export — same
      // shared buildResearchExport() service the /admin UI's download
      // button and the automatic completion hook use; this route only
      // ever reads/generates, never mutates, so EXPORT_TOKEN is
      // sufficient (ADMIN_TOKEN also works, per requireReadAccess).
      let opsExportMatch;
      if (
        (opsExportMatch = /^\/ops\/rounds\/([^/]+)\/export$/.exec(url.pathname)) &&
        request.method === "GET"
      ) {
        return await requireReadAccess(request, env, (req, e) => handleOpsRoundExport(req, e, opsExportMatch[1]));
      }
      // Machine one-shot publish (automation/emergency use, ADMIN_TOKEN —
      // never a browser route). Internally the exact same publish.js
      // freeze+publish path the /admin UI uses — see handleAdminPublish.
      if (url.pathname === "/ops/publish" && request.method === "POST") {
        return await requireAdmin(request, env, handleAdminPublish);
      }
      // Calibration runner job API — CALIBRATION_RUNNER_TOKEN only, never
      // ADMIN_TOKEN/EXPORT_TOKEN. See calibrationJobs.js and
      // requireCalibrationRunner above.
      if (url.pathname.startsWith("/ops/calibration/jobs")) {
        return await requireCalibrationRunner(request, env, (req, e) => calibrationJobsFetch(req, e, url));
      }
      // B2 -> Reader Lab candidate-pool bridge. CALIBRATION_RUNNER_TOKEN
      // (the automatic path — see calibration/runner/prepare_calibration_
      // candidates.py) or ADMIN_TOKEN (fallback/audit, same shape as
      // /ops/publish's relationship to the admin UI). Never EXPORT_TOKEN —
      // this is a write route. Writes only ever land in
      // calibration_candidates via candidateIngestion.js's own validation
      // — this route can never create/revoke a reviewer, mutate a
      // response, change policy, or publish a round.
      if (url.pathname === "/ops/calibration/candidates" && request.method === "POST") {
        return await requireCalibrationRunnerOrAdmin(request, env, (req, e) => handleOpsCandidateIngestion(req, e));
      }
      // Browser-facing admin control plane — Cloudflare Access-gated
      // (see access.js). Fails closed (503) until Access is actually
      // configured for this Worker; see README.md.
      if (url.pathname.startsWith("/admin/api/")) {
        return await requireAccessAuth(request, env, (req, e, identity) => adminApiFetch(req, e, identity, url));
      }
      if (url.pathname === "/admin" || url.pathname === "/admin/") {
        return await requireAccessAuth(request, env, async () => {
          const nonce = newNonce();
          return secureHtml(renderAdminShell(nonce), 200, { nonce, csp: adminCsp(nonce) });
        });
      }
      if ((inviteMatch = /^\/invite\/([a-f0-9]{48})$/.exec(url.pathname)) && request.method === "GET") {
        return await handleInvite(request, env, inviteMatch[1]);
      }
      return notFound();
    } catch (err) {
      return secureJson({ error: "internal_error" }, 500);
    }
  },

  // Low-frequency safety net (see wrangler.toml's [triggers] cron), not
  // the primary completion path — the response-time hook in
  // handleResponse already generates an export the moment a round
  // completes. This only exists to catch the rare case where that
  // background waitUntil attempt failed (or never ran, e.g. an isolate
  // recycled mid-flight): find completed rounds without a ready export
  // and retry them. buildResearchExport is itself idempotent, so running
  // this against a round that's already fine is always a safe no-op.
  async scheduled(event, env, ctx) {
    const stuck = await env.DB.prepare(
      `SELECT r.round_id FROM rounds r
       LEFT JOIN research_exports e ON e.round_id = r.round_id
       WHERE r.status = 'completed' AND (e.round_id IS NULL OR e.status != 'ready')`
    ).all();
    for (const row of stuck.results) {
      ctx.waitUntil(buildResearchExport(env, row.round_id, { actor: "system:cron_reconciliation" }).catch(() => {}));
    }

    // Calibration reconciliation — covers a round that completed (and
    // exported) before this orchestrator existed or was deployed, or any
    // other case where armCalibrationRun was never successfully called
    // for a round that's ready for it. armCalibrationRun is itself
    // idempotent (keyed on round_id + export hash + workflow version),
    // so re-running this against an already-armed round is always a
    // no-op — see calibrationOrchestrator.js.
    const needsCalibration = await env.DB.prepare(
      `SELECT r.round_id FROM rounds r
       JOIN research_exports e ON e.round_id = r.round_id AND e.status = 'ready'
       LEFT JOIN calibration_runs c ON c.round_id = r.round_id
       WHERE r.status = 'completed' AND c.run_id IS NULL`
    ).all();
    for (const row of needsCalibration.results) {
      ctx.waitUntil(armCalibrationRun(env, row.round_id, { actor: "system:cron_reconciliation" }).catch(() => {}));
    }

    // Candidate-pool reconciliation safety net — the primary trigger is
    // synchronous, right after a candidate ingestion that added ≥1
    // newly eligible row (see handleOpsCandidateIngestion above). This
    // only exists to catch the case where that synchronous call itself
    // failed, or eligibility changed some other way (e.g. a direct
    // admin-import that raced a Worker restart). reconcileStuckCalibrationRuns
    // is itself idempotent (the resumed_by_run_id claim), so running
    // this against a round with nothing stuck is always a safe no-op.
    ctx.waitUntil(reconcileStuckCalibrationRuns(env, { actor: "system:cron_reconciliation" }).catch(() => {}));
  },
};

// ---------------------------------------------------------------------
// reviewer-app-specific response/crypto helpers. Generic versions
// (secureJson, notFound, sha256Hex, rate limiting, etc.) now live in
// ./util.js, shared with the admin API and publication service.
// ---------------------------------------------------------------------

function htmlCsp(nonce) {
  // default-src 'none' + explicit allow-list: this app fetches only
  // same-origin JSON and loads exactly one cross-origin resource (the
  // main site's stylesheet, for visual consistency — see README on why
  // that's an acceptable trust boundary: it's a stylesheet, not script).
  return [
    "default-src 'none'",
    `script-src 'self' 'nonce-${nonce}'`,
    `style-src 'nonce-${nonce}' https://cripminds.com`,
    "connect-src 'self'",
    "img-src 'self'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");
}

// Same policy shape as htmlCsp (same trust boundary: same-origin JSON +
// the main site's stylesheet only) — kept as its own function since the
// admin shell and the reviewer app are conceptually separate surfaces,
// even though today they'd be identical strings.
function adminCsp(nonce) {
  return htmlCsp(nonce);
}

// ---------------------------------------------------------------------
// reviewer-specific id/cookie helpers (invitation token, session id —
// generic crypto/rate-limit/cookie-parsing helpers now live in util.js)
// ---------------------------------------------------------------------

function newInvitationToken() {
  return randomHex(24); // 192 bits — same construction/entropy as the session id below
}

function newSessionId() {
  return randomHex(24); // 192 bits, opaque, never guessable; stored only as a hash
}

function sessionCookieHeader(sessionId, maxAgeSeconds) {
  // Secure + HttpOnly: never readable/sendable from page JS, only sent
  // by the browser to this exact origin over HTTPS.
  // SameSite=Lax: the entry flow is a top-level GET navigation (the
  // reviewer clicking their invite link), which Lax always allows; every
  // subsequent call is a same-origin fetch from the app itself, which
  // also always carries a Lax cookie. What Lax specifically blocks is a
  // THIRD-PARTY page issuing a cross-site POST/fetch that rides this
  // cookie — exactly the CSRF shape /api/response would otherwise be
  // exposed to. Strict was considered and rejected: some browsers still
  // withhold Strict cookies on the very first cross-site-referred
  // top-level navigation into the site (e.g. a reviewer opening the
  // invite link from a Telegram/WhatsApp message), which would break
  // the one navigation this app most depends on.
  return `${SESSION_COOKIE_NAME}=${sessionId}; Path=/; Max-Age=${maxAgeSeconds}; Secure; HttpOnly; SameSite=Lax`;
}

function clearSessionCookieHeader() {
  return `${SESSION_COOKIE_NAME}=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax`;
}

// ---------------------------------------------------------------------
// auth resolution
// ---------------------------------------------------------------------

// Shared by both credential checks below — only FAILED attempts consume
// rate-limit budget, so a burst of legitimate calls (e.g. seeding a
// pilot batch: several items + an invitation + an assignment in quick
// succession) never locks anyone out. Only repeated wrong tokens do.
async function checkToken(request, env, headerName, envKey, bucket = "admin_auth_fail") {
  const ip = clientIp(request);
  const alreadyBlocked = await isRateLimited(env, bucket, ip, RATE_LIMITS.admin_auth_fail);
  if (alreadyBlocked) return false;

  const provided = request.headers.get(headerName) || "";
  const secret = env[envKey];
  if (!secret || !timingSafeEqual(provided, secret)) {
    await recordRateLimitAttempt(env, bucket, ip, RATE_LIMITS.admin_auth_fail);
    return false;
  }
  return true;
}

// Full admin credential — every write route (/admin/invitations*,
// /admin/items, /admin/assignments) requires this and only this.
async function requireAdmin(request, env, handler) {
  const ok = await checkToken(request, env, "x-admin-token", "ADMIN_TOKEN");
  // Same shape/status regardless of *why* it failed (missing header,
  // wrong value, ADMIN_TOKEN unset) — never distinguish these to the
  // caller.
  if (!ok) return secureJson({ error: "unauthorized" }, 401);
  return handler(request, env);
}

// Read-only routes (/admin/status, /admin/export) accept EITHER the
// full ADMIN_TOKEN (X-Admin-Token) or the narrower EXPORT_TOKEN
// (X-Export-Token). EXPORT_TOKEN is deliberately scoped to only these
// two checks — it is never consulted by requireAdmin above, so holding
// it can never create, revoke, or write anything.
async function requireReadAccess(request, env, handler) {
  const hasAdminHeader = request.headers.get("x-admin-token") !== null;
  const ok = hasAdminHeader
    ? await checkToken(request, env, "x-admin-token", "ADMIN_TOKEN")
    : await checkToken(request, env, "x-export-token", "EXPORT_TOKEN");
  if (!ok) return secureJson({ error: "unauthorized" }, 401);
  return handler(request, env);
}

// Third, separate credential — CALIBRATION_RUNNER_TOKEN — gates
// /ops/calibration/jobs/* and (see requireCalibrationRunnerOrAdmin below)
// /ops/calibration/candidates. Deliberately never accepted as an
// alternative on requireAdmin/requireReadAccess above, and
// ADMIN_TOKEN/EXPORT_TOKEN are never accepted on the jobs routes either:
// holding this token can claim/heartbeat/complete/fail a calibration job
// and submit a candidate bundle — nothing else. It still has no path to
// create/revoke a reviewer, mutate a response, change policy, or publish
// a round. Its own rate-limit bucket, isolated from the other two
// tokens' failure counters.
async function requireCalibrationRunner(request, env, handler) {
  const ok = await checkToken(request, env, "x-calibration-runner-token", "CALIBRATION_RUNNER_TOKEN", "calibration_runner_auth_fail");
  if (!ok) return secureJson({ error: "unauthorized" }, 401);
  return handler(request, env);
}

// Candidate ingestion accepts CALIBRATION_RUNNER_TOKEN (the automatic
// path) OR ADMIN_TOKEN (fallback/audit — same relationship /ops/publish
// has to the admin UI's own publish action) — never EXPORT_TOKEN, since
// this is a write route. This is not a privilege expansion for the
// runner token in practice: it already fully controls prepare_next_
// round's OUTPUT (the draft content it computes and submits back via
// the jobs API), so letting it also populate the pool that step reads
// from is the same trust boundary one step earlier, not a new one — see
// the design doc's candidate-bridge section for the full reasoning.
async function requireCalibrationRunnerOrAdmin(request, env, handler) {
  const hasRunnerHeader = request.headers.get("x-calibration-runner-token") !== null;
  const ok = hasRunnerHeader
    ? await checkToken(request, env, "x-calibration-runner-token", "CALIBRATION_RUNNER_TOKEN", "calibration_runner_auth_fail")
    : await checkToken(request, env, "x-admin-token", "ADMIN_TOKEN");
  if (!ok) return secureJson({ error: "unauthorized" }, 401);
  return handler(request, env);
}

async function lookupInvitationByToken(env, token) {
  if (!token || !/^[a-f0-9]{48}$/.test(token)) return null;
  const tokenHash = await sha256Hex(token);
  const row = await env.DB.prepare("SELECT * FROM invitations WHERE token_hash = ?").bind(tokenHash).first();
  if (!row) return null;
  if (row.revoked) return null;
  if (row.expires_at && new Date(row.expires_at) < new Date()) return null;
  return row;
}

// Resolves the authenticated reviewer from the session cookie, and — on
// every single call, not just at login — re-checks the underlying
// invitation. This is what makes revocation actually cut off an
// in-progress session immediately, not just future logins.
async function resolveReviewerFromRequest(request, env) {
  const sessionId = parseCookie(request, SESSION_COOKIE_NAME);
  if (!sessionId || !/^[a-f0-9]{48}$/.test(sessionId)) return null;
  const sessionHash = await sha256Hex(sessionId);
  const session = await env.DB.prepare(
    "SELECT * FROM sessions WHERE session_id_hash = ?"
  )
    .bind(sessionHash)
    .first();
  if (!session) return null;
  if (new Date(session.expires_at) < new Date()) return null;
  const reviewer = await env.DB.prepare(
    "SELECT * FROM invitations WHERE reviewer_id = ?"
  )
    .bind(session.reviewer_id)
    .first();
  if (!reviewer || reviewer.revoked) return null;
  if (reviewer.expires_at && new Date(reviewer.expires_at) < new Date()) return null;
  return reviewer;
}

// ---------------------------------------------------------------------
// reviewer-facing: invite → session → app
// ---------------------------------------------------------------------

async function handleInvite(request, env, token) {
  const allowed = await checkRateLimit(env, "invite_attempt", clientIp(request), RATE_LIMITS.invite_attempt);
  if (!allowed) return secureHtml(renderInvalidLinkPage(), 429);

  const invitation = await lookupInvitationByToken(env, token);
  if (!invitation) return secureHtml(renderInvalidLinkPage(), 404);

  const sessionId = newSessionId();
  const sessionHash = await sha256Hex(sessionId);
  const now = new Date();
  const expiresAt = new Date(now.getTime() + SESSION_TTL_SECONDS * 1000).toISOString();

  await env.DB.prepare(
    "INSERT INTO sessions (session_id_hash, reviewer_id, created_at, expires_at) VALUES (?,?,?,?)"
  )
    .bind(sessionHash, invitation.reviewer_id, now.toISOString(), expiresAt)
    .run();

  // From here on, the invitation token never appears in a URL, a fetch
  // body, or a stored record again — only this opaque session cookie
  // does, and only as its hash in D1.
  return redirect("/session", {
    "set-cookie": sessionCookieHeader(sessionId, SESSION_TTL_SECONDS),
  });
}

async function handleSessionPage(request, env) {
  const allowed = await checkRateLimit(env, "session_lookup", clientIp(request), RATE_LIMITS.session_lookup);
  if (!allowed) return secureHtml(renderInvalidLinkPage(), 429);

  const reviewer = await resolveReviewerFromRequest(request, env);
  if (!reviewer) {
    return secureHtml(renderInvalidLinkPage(), 401, {
      extraHeaders: { "set-cookie": clearSessionCookieHeader() },
    });
  }
  const nonce = newNonce();
  return secureHtml(renderAppShell(nonce), 200, { nonce, csp: htmlCsp(nonce) });
}

async function handleApiSession(request, env) {
  const allowed = await checkRateLimit(env, "session_lookup", clientIp(request), RATE_LIMITS.session_lookup);
  if (!allowed) return secureJson({ error: "rate_limited" }, 429);

  const reviewer = await resolveReviewerFromRequest(request, env);
  if (!reviewer) return secureJson({ error: "invalid_session" }, 401);

  if (!reviewer.practice_completed) {
    const practiceItems = await env.DB.prepare(
      "SELECT item_id, source_snapshot, candidate_sentence, practice_explanation " +
        "FROM items WHERE is_practice = 1 ORDER BY item_id LIMIT 4"
    ).all();
    // Operational safety net: if no practice items have been seeded yet
    // (an admin ordering mistake — practice items should exist before
    // any invitation is sent), don't strand the reviewer in a
    // permanent empty-practice loop. Fall through to real mode instead.
    if (practiceItems.results.length > 0) {
      return secureJson({
        mode: "practice",
        items: practiceItems.results.map(toPublicItem),
      });
    }
  }

  // Serve already-assigned-but-unanswered items, oldest first. v0 does
  // not auto-top-up from an unassigned pool — assignment is a deliberate
  // admin action (per the design doc's independence/assignment model),
  // not something a reviewer's own request should be able to trigger.
  const pending = await env.DB.prepare(
    `SELECT a.item_id, a.assignment_version, i.source_snapshot, i.candidate_sentence
     FROM assignments a JOIN items i ON i.item_id = a.item_id
     WHERE a.reviewer_id = ? AND a.answered_at IS NULL
     ORDER BY a.created_at LIMIT ?`
  )
    .bind(reviewer.reviewer_id, SESSION_BATCH_SIZE)
    .all();

  const now = nowIso();
  for (const row of pending.results) {
    await env.DB.prepare(
      "UPDATE assignments SET served_at = COALESCE(served_at, ?) WHERE reviewer_id = ? AND item_id = ?"
    )
      .bind(now, reviewer.reviewer_id, row.item_id)
      .run();
  }

  return secureJson({
    mode: "real",
    items: pending.results.map(toPublicItem),
  });
}

function toPublicItem(row) {
  return {
    item_id: row.item_id,
    source_snapshot: row.source_snapshot,
    candidate_sentence: row.candidate_sentence,
    // only present because this query only ever selects it for
    // is_practice=1 rows — the real-item query above never selects
    // this column at all, so there is nothing to accidentally leak.
    // practice_correct_answer is deliberately never sent to the client:
    // it's an internal research label (e.g. "interpretive_only") and
    // the reviewer-facing explanation is keyed off the reviewer's own
    // choice, not a right/wrong comparison against it — see renderItem.
    practice_explanation: row.practice_explanation || undefined,
  };
}

async function handleResponse(request, env, ctx) {
  const allowed = await checkRateLimit(env, "session_lookup", clientIp(request), RATE_LIMITS.session_lookup);
  if (!allowed) return secureJson({ error: "rate_limited" }, 429);

  let body;
  try {
    body = await request.json();
  } catch {
    return secureJson({ error: "invalid_json" }, 400);
  }

  const reviewer = await resolveReviewerFromRequest(request, env);
  if (!reviewer) return secureJson({ error: "invalid_session" }, 401);

  const { item_id, selected_public_response, confidence, comment, practice_or_real, session_id } = body;

  if (typeof item_id !== "string" || !item_id) {
    return secureJson({ error: "invalid_item_id" }, 400);
  }
  if (!Object.prototype.hasOwnProperty.call(PUBLIC_TO_INTERNAL, selected_public_response)) {
    return secureJson({ error: "invalid_response_value" }, 400);
  }
  if (confidence && !["pretty_sure", "somewhat_sure", "not_very_sure"].includes(confidence)) {
    return secureJson({ error: "invalid_confidence_value" }, 400);
  }
  if (!["practice", "real"].includes(practice_or_real)) {
    return secureJson({ error: "invalid_practice_or_real" }, 400);
  }
  const safeComment = typeof comment === "string" ? comment.slice(0, MAX_COMMENT_LENGTH) : null;
  const safeSessionId = typeof session_id === "string" && session_id.length <= 100 ? session_id : newId("sess");

  const item = await env.DB.prepare("SELECT * FROM items WHERE item_id = ?").bind(item_id).first();
  if (!item) return secureJson({ error: "unknown_item" }, 404);

  let assignment = null;
  if (practice_or_real === "practice") {
    if (!item.is_practice) return secureJson({ error: "item_not_practice" }, 400);
  } else {
    if (item.is_practice) return secureJson({ error: "item_is_practice" }, 400);
    assignment = await env.DB.prepare(
      "SELECT * FROM assignments WHERE reviewer_id = ? AND item_id = ?"
    )
      .bind(reviewer.reviewer_id, item_id)
      .first();
    if (!assignment) {
      // A reviewer can only answer items actually assigned to them —
      // never an arbitrary item_id guessed or replayed from elsewhere.
      return secureJson({ error: "item_not_assigned" }, 403);
    }
  }

  // Idempotency / immutability, made explicit rather than left to rely
  // solely on the UNIQUE constraint: a reviewer's first completed
  // response to an item is permanent. A double-click, a page refresh
  // after submit, or a network-level retry all land here and are all
  // reported back as "already recorded", never as a silent overwrite
  // and never as a second row.
  const existing = await env.DB.prepare(
    "SELECT response_id FROM responses WHERE reviewer_id = ? AND item_id = ?"
  )
    .bind(reviewer.reviewer_id, item_id)
    .first();
  if (existing) {
    return secureJson({ ok: true, already_recorded: true });
  }

  const responseId = newId("resp");
  const timestamp = nowIso();

  await env.DB.prepare(
    `INSERT INTO responses (
      response_id, session_id, reviewer_id, item_id, task_type, task_version,
      assignment_version, source_snapshot_id, candidate_claim_id,
      selected_public_response, internal_normalized_response, confidence,
      comment, timestamp, reviewer_blind_to_model_output,
      reviewer_blind_to_other_reviewers, assistance_declared, practice_or_real,
      client_interface_version
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,1,'independent',?,?)
    ON CONFLICT (reviewer_id, item_id) DO NOTHING`
  )
    .bind(
      responseId,
      safeSessionId,
      reviewer.reviewer_id,
      item_id,
      "factual_floor_v0",
      TASK_VERSION,
      ASSIGNMENT_VERSION,
      item.source_snapshot_id,
      item.candidate_claim_id,
      selected_public_response,
      PUBLIC_TO_INTERNAL[selected_public_response],
      confidence || null,
      safeComment,
      timestamp,
      practice_or_real,
      CLIENT_INTERFACE_VERSION
    )
    .run();

  if (practice_or_real === "real") {
    await env.DB.prepare(
      "UPDATE assignments SET answered_at = COALESCE(answered_at, ?) WHERE reviewer_id = ? AND item_id = ?"
    )
      .bind(timestamp, reviewer.reviewer_id, item_id)
      .run();

    // Automatic round completion + research export — the whole point of
    // this being automatic is that no privileged session ever has to
    // notice a round finished. maybeCompleteRound is an atomic,
    // idempotent conditional UPDATE (published -> completed); only the
    // single request that actually flips it proceeds to kick off export
    // generation. Export generation runs in the background (waitUntil)
    // so a reviewer's own response latency never depends on it, and a
    // failure there can never roll back or block the response that was
    // already committed above.
    if (assignment && assignment.round_id) {
      const { justCompleted } = await maybeCompleteRound(env, assignment.round_id);
      if (justCompleted && ctx && typeof ctx.waitUntil === "function") {
        // Export first, then arm the calibration orchestrator only once
        // the export is actually 'ready' — armCalibrationRun itself also
        // checks this, but chaining it here means a slow/failed export
        // never races a calibration run being armed against a
        // not-yet-real export hash.
        ctx.waitUntil(
          buildResearchExport(env, assignment.round_id, { actor: "system:completion_detection" })
            .then((result) => {
              if (result.status === "ready") {
                return armCalibrationRun(env, assignment.round_id, { actor: "system:completion_detection" });
              }
            })
            .catch(() => {})
        );
      }
    }
  } else {
    // Mark practice complete once this reviewer has answered every
    // current practice item — not just the one just submitted — so
    // adding a practice item later doesn't retroactively "complete"
    // someone who never saw it.
    const totalPractice = await env.DB.prepare(
      "SELECT COUNT(*) AS n FROM items WHERE is_practice = 1"
    ).first();
    const answeredPractice = await env.DB.prepare(
      "SELECT COUNT(*) AS n FROM responses WHERE reviewer_id = ? AND practice_or_real = 'practice'"
    )
      .bind(reviewer.reviewer_id)
      .first();
    if (totalPractice.n > 0 && answeredPractice.n >= totalPractice.n) {
      await env.DB.prepare(
        "UPDATE invitations SET practice_completed = 1 WHERE reviewer_id = ?"
      )
        .bind(reviewer.reviewer_id)
        .run();
    }
  }

  return secureJson({ ok: true, already_recorded: false });
}

// ---------------------------------------------------------------------
// admin (utilitarian, v0 scope — no dashboard, just JSON endpoints, all
// behind X-Admin-Token, all constant-shape on auth failure)
// ---------------------------------------------------------------------

async function handleAdminCreateInvitation(request, env) {
  const body = await request.json().catch(() => ({}));
  const reviewerId = body.reviewer_id || `reader_${randomHex(3)}`;
  const token = newInvitationToken();
  const tokenHash = await sha256Hex(token);
  const now = nowIso();

  await env.DB.prepare(
    `INSERT INTO invitations (reviewer_id, token_hash, contact_channel, created_at, expires_at, revoked, practice_completed)
     VALUES (?,?,?,?,?,0,0)`
  )
    .bind(reviewerId, tokenHash, body.contact_channel || null, now, body.expires_at || null)
    .run();

  return secureJson({
    reviewer_id: reviewerId,
    token, // returned once, plaintext, never stored — copy it now
    invite_url_path: `/invite/${token}`,
  });
}

async function handleAdminRevokeInvitation(request, env) {
  const body = await request.json().catch(() => ({}));
  if (!body.reviewer_id) return secureJson({ error: "missing_reviewer_id" }, 400);
  await env.DB.prepare("UPDATE invitations SET revoked = 1 WHERE reviewer_id = ?")
    .bind(body.reviewer_id)
    .run();
  // Revocation is effective immediately on the NEXT request from that
  // reviewer, cookie or not — resolveReviewerFromRequest re-checks
  // invitations.revoked on every call, it doesn't cache the check at
  // login time. Existing sessions rows are left in place (harmless: the
  // join to invitations will reject them) rather than deleted, so the
  // revoke action itself can't accidentally destroy audit trail.
  return secureJson({ ok: true });
}

async function handleAdminCreateItem(request, env) {
  const body = await request.json().catch(() => ({}));
  const required = ["source_snapshot", "candidate_sentence"];
  for (const field of required) {
    if (!body[field]) return secureJson({ error: `missing_${field}` }, 400);
  }
  const itemId = body.item_id || newId("ril");
  const sourceSnapshotId = "sha256:" + (await sha256Hex(body.source_snapshot));
  const candidateClaimId = "sha256:" + (await sha256Hex(body.candidate_sentence));
  const isPractice = body.is_practice ? 1 : 0;
  const bucket = body.dataset_bucket || "pilot";

  await env.DB.prepare(
    `INSERT INTO items (
      item_id, task_version, source_snapshot, source_snapshot_id,
      candidate_sentence, candidate_claim_id, dataset_bucket, is_practice,
      practice_explanation, practice_correct_answer, created_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?)`
  )
    .bind(
      itemId,
      TASK_VERSION,
      body.source_snapshot,
      sourceSnapshotId,
      body.candidate_sentence,
      candidateClaimId,
      bucket,
      isPractice,
      body.practice_explanation || null,
      body.practice_correct_answer || null,
      nowIso()
    )
    .run();

  return secureJson({ item_id: itemId, source_snapshot_id: sourceSnapshotId, candidate_claim_id: candidateClaimId });
}

async function handleAdminCreateAssignments(request, env) {
  const body = await request.json().catch(() => ({}));
  const { reviewer_ids, item_ids } = body;
  if (!Array.isArray(reviewer_ids) || !Array.isArray(item_ids)) {
    return secureJson({ error: "reviewer_ids_and_item_ids_must_be_arrays" }, 400);
  }
  const now = nowIso();
  let created = 0;
  for (const reviewerId of reviewer_ids) {
    for (const itemId of item_ids) {
      const assignmentId = newId("asg");
      await env.DB.prepare(
        `INSERT INTO assignments (assignment_id, reviewer_id, item_id, assignment_version, created_at)
         VALUES (?,?,?,?,?)
         ON CONFLICT (reviewer_id, item_id) DO NOTHING`
      )
        .bind(assignmentId, reviewerId, itemId, ASSIGNMENT_VERSION, now)
        .run();
      created += 1;
    }
  }
  // Independence is structural here, not a policy note: each (reviewer_id,
  // item_id) pair is its own row, and nothing in this file or schema ever
  // joins across reviewer_ids when reading assignments/responses back to
  // a reviewer's own session.
  return secureJson({ requested: reviewer_ids.length * item_ids.length, created });
}

async function handleAdminStatus(request, env) {
  const rows = await env.DB.prepare(
    `SELECT i.reviewer_id, i.practice_completed, i.revoked, i.created_at,
            COUNT(a.assignment_id) AS assigned_count,
            SUM(CASE WHEN a.answered_at IS NOT NULL THEN 1 ELSE 0 END) AS answered_count
     FROM invitations i
     LEFT JOIN assignments a ON a.reviewer_id = i.reviewer_id
     GROUP BY i.reviewer_id
     ORDER BY i.created_at`
  ).all();
  // Deliberately excludes token_hash/contact_channel — this endpoint is
  // for "who's done what," not a credential or contact-list export.
  return secureJson({ reviewers: rows.results });
}

async function handleAdminExport(request, env) {
  const url = new URL(request.url);
  const includePractice = url.searchParams.get("include_practice") === "1";
  const query = includePractice
    ? "SELECT * FROM responses ORDER BY timestamp"
    : "SELECT * FROM responses WHERE practice_or_real = 'real' ORDER BY timestamp";
  const rows = await env.DB.prepare(query).all();
  return secureJson({ count: rows.results.length, responses: rows.results });
}

// Machine equivalent of the admin UI's download button — same shared
// buildResearchExport() service (see researchExport.js), never a
// separate export path. Read-only: generates the export if the round is
// completed and none exists yet, but never mutates round/item/response
// content.
async function handleOpsRoundExport(request, env, roundId) {
  try {
    const result = await buildResearchExport(env, roundId, { actor: "ops_token" });
    if (result.status !== "ready") {
      return secureJson({ round_id: roundId, status: result.status, error: result.error }, 502);
    }
    return secureJson(result.export);
  } catch (err) {
    if (err instanceof ValidationError) {
      return secureJson({ error: "validation_failed", errors: err.errors }, 422);
    }
    return secureJson({ error: "internal_error", detail: String((err && err.message) || err) }, 500);
  }
}

// One-shot machine publish path (automation/emergency use — the ops
// session that previously hand-ran `wrangler d1 execute` against
// interpolated SQL to publish RL-2026-001 should use this instead, going
// forward: POST the manifest JSON, get a credential-free receipt back).
// Internally this is the exact same freeze+publish code the /admin UI
// uses — see publish.js's directPublishFromManifest.
async function handleAdminPublish(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return secureJson({ error: "invalid_json" }, 400);
  }
  if (!body || typeof body !== "object" || !body.manifest) {
    return secureJson({ error: "missing_manifest" }, 400);
  }
  try {
    const result = await directPublishFromManifest(env, body.manifest, { actor: "admin_token" });
    return secureJson(result);
  } catch (err) {
    if (err instanceof ValidationError) {
      return secureJson({ error: "validation_failed", errors: err.errors, warnings: err.warnings }, 422);
    }
    return secureJson({ error: "internal_error", detail: String((err && err.message) || err) }, 500);
  }
}

// B2 -> Reader Lab candidate-pool bridge, machine path. See
// candidateIngestion.js for the actual validation/idempotency; this
// handler only resolves who's calling (runner_id from the body for the
// runner token, "admin_token" for the admin fallback) and, on any newly
// eligible candidate, immediately tries to resume any calibration run
// stuck at needs_eligible_candidates — never leaving that to wait for
// the hourly cron alone.
async function handleOpsCandidateIngestion(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return secureJson({ error: "invalid_json" }, 400);
  }
  const isRunner = request.headers.get("x-calibration-runner-token") !== null;
  const actor = isRunner ? `runner:${(body && body.runner_id) || "unknown"}` : "admin_token";
  const ingestedVia = isRunner ? "runner" : "admin_import";

  try {
    const result = await ingestCalibrationCandidates(env, body, { actor, ingestedVia });
    let reconciliation = null;
    if (result.newly_eligible_candidate_count > 0) {
      reconciliation = await reconcileStuckCalibrationRuns(env, { actor: "system:candidate_ingestion_reconciliation" });
    }
    return secureJson({ ...result, reconciliation });
  } catch (err) {
    if (err instanceof CandidateValidationError) {
      return secureJson({ error: "validation_failed", errors: err.errors }, 422);
    }
    return secureJson({ error: "internal_error", detail: String((err && err.message) || err) }, 500);
  }
}

// ---------------------------------------------------------------------
// reviewer app HTML (self-contained, reuses cripminds.com's own
// stylesheet cross-origin — no CSS duplicated here beyond layout that's
// specific to Reader Lab)
// ---------------------------------------------------------------------

function renderInvalidLinkPage() {
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
<title>Crip Minds Reader Lab</title>
</head><body style="font-family: sans-serif; max-width: 40rem; margin: 4rem auto; padding: 0 1.25rem; text-align:center;">
  <p style="font-size:1.25rem;">This link isn&rsquo;t valid anymore.</p>
  <p style="opacity:0.7;">If you think that&rsquo;s wrong, reach out to whoever invited you.</p>
</body></html>`;
  // Deliberately has no <link> to cripminds.com here: an invalid-link
  // page is the one place unauthenticated traffic (including anyone
  // probing token guesses) reaches, so it stays fully self-contained —
  // no cross-origin request of any kind, nothing worth a CSP header pair.
}

function renderAppShell(nonce) {
  // No invitation token and no session id are ever embedded in this
  // page — authentication is entirely the browser's HttpOnly cookie.
  // The client-side app authenticates every fetch() implicitly via that
  // cookie (same-origin requests always include it).
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>Crip Minds Reader Lab</title>
<link rel="stylesheet" href="https://cripminds.com/assets/css/main-redesign.css">
<style nonce="${nonce}">
  body { background: var(--foundation-white, #fef9f2); color: var(--foundation-black, #0d0c0b); }
  .rl-shell { max-width: 640px; margin: 0 auto; padding: 3rem 1.25rem 5rem; }
  .rl-progress { font-size: 0.85rem; opacity: 0.7; margin-bottom: 1.5rem; }
  .rl-block { margin-bottom: 1.75rem; }
  .rl-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.6; margin-bottom: 0.5rem; }
  .rl-text { font-size: 1.15rem; line-height: 1.6; }
  .rl-choice { display: block; width: 100%; text-align: left; padding: 1rem 1.25rem; margin-bottom: 0.75rem;
    border: 2px solid var(--foundation-gray-300, #c4b5a0); border-radius: 0.5rem; background: transparent;
    color: inherit; font-size: 1rem; cursor: pointer; min-height: 44px; }
  .rl-choice:hover { border-color: var(--brand-crip-blue, #3f5f89); }
  .rl-choice[aria-checked="true"] { border-color: var(--brand-crip-blue, #3f5f89); background: var(--brand-crip-blue-50, #eef2f7); }
  .rl-choice:focus-visible { outline: 2px solid var(--brand-crip-blue, #3f5f89); outline-offset: 2px; }
  .rl-secondary { margin-top: 1.5rem; }
  .rl-hidden { display: none; }
  .rl-footnote { font-size: 0.8rem; opacity: 0.6; margin-top: 3rem; }
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
</head>
<body>
<main id="rl-app" class="rl-shell" aria-live="polite"></main>
<script nonce="${nonce}">
(function () {
  var app = document.getElementById("rl-app");
  var state = { mode: null, items: [], index: 0, sessionId: crypto.randomUUID() };

  function el(tag, attrs, children) {
    var e = document.createElement(tag);
    for (var k in (attrs || {})) {
      if (k === "style") {
        // This page's CSP has no 'unsafe-inline' on style-src (same
        // nonce-only policy as script-src), so setting the style
        // ATTRIBUTE directly is silently blocked by the browser —
        // every style:"prop:value;" call site below (the welcome
        // checkbox row, the confidence-button wrap, and the comment
        // textarea's initial display:none) would otherwise render
        // without the layout it depends on. Setting individual CSSOM
        // properties via element.style.setProperty is not attribute-
        // level inline style and isn't restricted by style-src.
        String(attrs[k]).split(";").forEach(function (decl) {
          var idx = decl.indexOf(":");
          if (idx < 0) return;
          var prop = decl.slice(0, idx).trim();
          var val = decl.slice(idx + 1).trim();
          if (prop && val) e.style.setProperty(prop, val);
        });
        continue;
      }
      e.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function (c) { e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }

  function fetchSession() {
    return fetch("/api/session", { credentials: "same-origin" }).then(function (r) { return r.json(); });
  }

  function submitResponse(payload) {
    return fetch("/api/response", {
      method: "POST",
      credentials: "same-origin",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(Object.assign({ session_id: state.sessionId }, payload)),
    }).then(function (r) { return r.json(); });
  }

  function renderWelcome(onContinue) {
    app.innerHTML = "";
    app.appendChild(el("h1", { class: "text-h2" }, ["Crip Minds Reader Lab"]));
    app.appendChild(el("p", { class: "text-lead rl-block" }, [
      "Sometimes a piece here draws on a source, and somewhere along the way a reading turns into a claim. We want to get better at seeing exactly where that happens."
    ]));
    app.appendChild(el("p", { class: "rl-block" }, [
      "You'll read a short passage and one sentence written from it. Then you tell us what kind of sentence it is. No specialist knowledge needed \\u2014 just your own read."
    ]));
    app.appendChild(el("p", { class: "rl-block" }, [
      "A session takes a few minutes. You'll never see more than 5 items at once, and you can come back another time for more."
    ]));
    var declareWrap = el("label", { class: "rl-block", style: "display:flex;gap:0.6rem;align-items:flex-start;" });
    var checkbox = el("input", { type: "checkbox", id: "rl-declare" });
    declareWrap.appendChild(checkbox);
    declareWrap.appendChild(el("span", {}, [
      "I'll answer on my own \\u2014 not with ChatGPT, a search engine, or someone else's opinion."
    ]));
    app.appendChild(declareWrap);
    var btn = el("button", { class: "btn btn--primary", disabled: "disabled" }, ["Start"]);
    checkbox.addEventListener("change", function () { btn.disabled = !checkbox.checked; });
    btn.addEventListener("click", onContinue);
    app.appendChild(btn);
  }

  // Keyed by the reviewer-facing public label, never the internal
  // research label — nothing in this shipped script should ever name
  // the internal taxonomy (see design doc section 3).
  var PRACTICE_EXPLANATIONS = {
    source_supports: "The passage states this directly, so the sentence just reports it.",
    reading_of_source: "The sentence draws a conclusion or frames the passage a certain way, but it doesn't need a new fact to be true \\u2014 it's an interpretation.",
    adds_unestablished: "The sentence depends on something \\u2014 a cause, a motive, a number, a group of people \\u2014 that the passage never actually says.",
    not_sure: "That's a fair call when the passage genuinely doesn't give you enough to decide. It's useful information, not a wrong answer."
  };

  function renderItem(item, isPractice, onDone) {
    app.innerHTML = "";
    app.appendChild(el("p", { class: "rl-progress" }, [
      (isPractice ? "Practice question " : "Question ") + (state.index + 1) + " of " + state.items.length
    ]));
    app.appendChild(el("p", { class: "rl-label" }, ["Source"]));
    app.appendChild(el("p", { class: "rl-text rl-block" }, ["\\u201C" + item.source_snapshot + "\\u201D"]));
    app.appendChild(el("p", { class: "rl-label" }, ["The sentence"]));
    app.appendChild(el("p", { class: "rl-text rl-block" }, ["\\u201C" + item.candidate_sentence + "\\u201D"]));
    app.appendChild(el("p", { class: "rl-block", style: "font-weight:600;" }, ["Which feels most accurate?"]));

    var choices = [
      ["source_supports", "The source supports this"],
      ["reading_of_source", "This is a reading of the source"],
      ["adds_unestablished", "This adds something the source doesn't establish"],
      ["not_sure", "I'm not sure"]
    ];
    var chosen = null;
    var choiceButtons = [];
    var choiceWrap = el("div", { role: "radiogroup", "aria-label": "Which feels most accurate?" });
    choices.forEach(function (pair) {
      // role="radio" + aria-checked matches the radiogroup container
      // above — mutually-exclusive single-choice, not independent
      // toggle buttons (aria-pressed would have been the wrong pattern
      // here: it describes N independent on/off toggles, not "choose
      // one of four").
      var b = el("button", { class: "rl-choice", role: "radio", "aria-checked": "false", type: "button" }, [pair[1]]);
      b.addEventListener("click", function () {
        chosen = pair[0];
        choiceButtons.forEach(function (cb) { cb.setAttribute("aria-checked", "false"); });
        b.setAttribute("aria-checked", "true");
        showSecondary();
      });
      choiceButtons.push(b);
      choiceWrap.appendChild(b);
    });
    app.appendChild(choiceWrap);

    var secondary = el("div", { class: "rl-secondary rl-hidden" });
    app.appendChild(secondary);

    function showSecondary() {
      secondary.classList.remove("rl-hidden");
      secondary.innerHTML = "";
      if (isPractice) {
        secondary.appendChild(el("p", { class: "text-secondary rl-block" }, [PRACTICE_EXPLANATIONS[chosen]]));
        var cont = el("button", { class: "btn btn--primary" }, ["Continue"]);
        cont.addEventListener("click", function () {
          submitResponse({ item_id: item.item_id, selected_public_response: chosen, practice_or_real: "practice" });
          onDone();
        });
        secondary.appendChild(cont);
        return;
      }
      secondary.appendChild(el("p", { class: "rl-label" }, ["How sure are you? (optional)"]));
      var confWrap = el("div", { style: "display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;" });
      var confidence = null;
      [["pretty_sure", "Pretty sure"], ["somewhat_sure", "Somewhat sure"], ["not_very_sure", "Not very sure"]].forEach(function (pair) {
        var cb = el("button", { class: "btn btn--outline btn--sm", type: "button" }, [pair[1]]);
        cb.addEventListener("click", function () {
          confidence = pair[0];
          Array.prototype.forEach.call(confWrap.children, function (c) { c.style.fontWeight = "normal"; });
          cb.style.fontWeight = "700";
        });
        confWrap.appendChild(cb);
      });
      secondary.appendChild(confWrap);

      var commentToggle = el("button", { class: "btn btn--outline btn--sm rl-block", type: "button" }, ["Want to say why?"]);
      var commentBox = el("textarea", { maxlength: "500", rows: "3", style: "width:100%;display:none;", "aria-label": "Optional comment" });
      commentToggle.addEventListener("click", function () { commentBox.style.display = "block"; commentToggle.style.display = "none"; });
      secondary.appendChild(commentToggle);
      secondary.appendChild(commentBox);

      var submit = el("button", { class: "btn btn--primary", style: "display:block;margin-top:1rem;" }, ["Continue"]);
      submit.addEventListener("click", function () {
        submit.disabled = true;
        submitResponse({
          item_id: item.item_id,
          selected_public_response: chosen,
          confidence: confidence,
          comment: commentBox.value || null,
          practice_or_real: "real"
        }).then(onDone);
      });
      secondary.appendChild(submit);
    }
  }

  function renderThankYou() {
    app.innerHTML = "";
    app.appendChild(el("h1", { class: "text-h2" }, ["That's it for today."]));
    app.appendChild(el("p", { class: "text-lead" }, [
      "Thank you \\u2014 this genuinely helps. Come back whenever you'd like for a few more."
    ]));
    app.appendChild(el("p", { class: "rl-footnote" }, [
      "Your answers are stored for Crip Minds' own research and editorial calibration, under a private reviewer record \\u2014 never shown publicly, never automatically used to change anything Crip Minds publishes. You can stop taking part at any time."
    ]));
  }

  function runQueue(items, isPractice, onAllDone) {
    state.items = items;
    state.index = 0;
    if (!items.length) { onAllDone(); return; }
    function step() {
      if (state.index >= state.items.length) { onAllDone(); return; }
      renderItem(state.items[state.index], isPractice, function () {
        state.index += 1;
        step();
      });
    }
    step();
  }

  function start() {
    fetchSession().then(function (session) {
      if (session.error) {
        app.innerHTML = "";
        app.appendChild(el("p", { class: "text-lead" }, ["This link isn't valid anymore."]));
        return;
      }
      if (session.mode === "practice") {
        renderWelcome(function () {
          app.innerHTML = "";
          app.appendChild(el("h2", { class: "text-h3" }, ["First, a few practice rounds."]));
          app.appendChild(el("p", { class: "text-secondary rl-block" }, [
            "These don't count \\u2014 they're just so the four choices make sense before you see the real ones. We'll tell you why after each one."
          ]));
          var beginBtn = el("button", { class: "btn btn--primary" }, ["Begin practice"]);
          beginBtn.addEventListener("click", function () {
            runQueue(session.items, true, function () {
              fetchSession().then(function (real) { runQueue(real.items || [], false, renderThankYou); });
            });
          });
          app.appendChild(beginBtn);
        });
      } else if (!session.items || !session.items.length) {
        app.innerHTML = "";
        app.appendChild(el("h1", { class: "text-h2" }, ["Nothing new for you right now."]));
        app.appendChild(el("p", { class: "text-lead" }, ["Check back later \\u2014 we'll have more when it's ready."]));
      } else {
        runQueue(session.items, false, renderThankYou);
      }
    });
  }

  start();
})();
</script>
</body>
</html>`;
}
