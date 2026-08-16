# Current Work Checkpoint

> **SUPERSEDED (2026-08-16) as the session-entry file.** This document grew into an
> append-only diary rather than the lean current-state file it was meant to be — read
> **`.claude/WORK.md`** first instead; it's the new canonical current-truth file, with
> **`.claude/LOGBOOK.md`** as the chronological history. This file is kept as a historical/
> evidence archive (its detailed experiment narratives are still real and citable), not deleted,
> but do not treat it as authoritative current state — if it disagrees with `WORK.md`, `WORK.md`
> wins. See `.claude/LOGBOOK.md`'s 2026-08-16 "PROJECT MEMORY RECOVERY + INSTALLATION" entry.

Update this after every meaningful commit, not at the end of a session. A
fresh session should need this file, not conversation archaeology. Full
methodology/results for closed experiments live in `.claude/experiments/`
and are linked below, not duplicated here.

## GOAL
Article-quality repair blueprint — rebuild cripminds' article-generation
prompt system around its true purpose (see project memory
`project_cripminds_editorial_blueprint.md` / `project_cripminds_true_purpose.md`),
not as ten isolated style fixes.

## READER LAB v0 (PARALLEL TRACK — LIVE, TWO-PERSON PILOT IN PROGRESS, 2026-08-12)
Independent-human-reference collection system — separate from, and not a
dependency of, the CJ-1/CJ-2/B2 track below. Neither track blocks the
other; see `## B2 v2` pointer below for that track's own current state.

**STATUS: READER LAB v0 IS LIVE / TWO-PERSON PILOT IN PROGRESS.** Not a
public audience feature, not statistically meaningful human calibration
yet — the pilot's only claim is narrower: can two independent
non-technical reviewers understand and use the factual-floor review
instrument without coaching. `reader-lab-worker/wrangler.toml` now shows
`lab.cripminds.com` attached as an active Worker Custom Domain (route
enabled, `workers_dev` also left on) and a concrete D1 `database_id`
(`29eb76ef-7a33-4cee-bbf6-17d628e6b6f8`) for `cripminds-reader-lab` — no
longer a placeholder. **Caveat, stated precisely: this session had no
`wrangler` authentication available (`wrangler whoami` returned
"not authenticated"), so the live Cloudflare account/D1 state (EU
jurisdiction, exact reviewer-record count, session/rate-limit table
contents) could NOT be independently re-verified against the API from
here — the LIVE status above rests on the deploy configuration on disk
plus direct confirmation, not on a fresh API read this session.** Two
real pilot reviewer records (`reviewer_parent_a`/`reviewer_parent_b`),
same four development/pilot assignments each, are understood to exist;
each reviewer's responses are isolated by the existing per-reviewer
assignment/response schema (`UNIQUE (reviewer_id, item_id)` on
`responses`, no cross-reviewer read path anywhere in the reviewer-facing
routes) — this isolation property IS verified directly from
`reader-lab-worker/schema.sql`/`src/index.js`, independent of the D1
question above.

**Security note — credential rotation event, recorded without raw
tokens.** Two originally generated parent invitation credentials were
exposed in conversation and were subsequently revoked. Fresh credentials
were generated directly against D1 and written temporarily to
`reader-lab-worker/.pilot-invites` (chmod 600, gitignored — confirmed via
`git check-ignore -v`, matches `.gitignore:63`). **Correction to the
handoff note that prompted this check: that file was NOT actually
deleted** — it was found still present on disk (183 bytes, chmod 600,
modified same day) during this pass's verification. It has now been
deleted as cleanup, consistent with the already-stated intent that it
never persist once the links were sent privately. No raw invitation URL
or token value is recorded anywhere in this file or in
`reader-lab-v0-design-2026-08-12.md`.

Full design + the live-state detail above + the new recurring
calibration-round protocol (Reader Lab Calibration Rounds, RL-YYYY-NNN):
`.claude/reader-lab-v0-design-2026-08-12.md`. Auth model: session-cookie
flow (invitation token used once, never persists in the URL/body/logs
after that); revoke/status admin endpoints; rate limiting, CSP,
constant-time admin auth, response immutability; two real accessibility
bugs found and fixed by code review. 42 automated local checks passed
pre-deploy against `wrangler dev --local`, plus a full two-reviewer pilot
walkthrough with the actual pilot content
(`reader-lab-worker/pilot-pack-v0.md`).

**UPDATE 2026-08-12 (session/ops separation — new, standing operating
model):** this research session runs, and is intended to keep running,
with NO Cloudflare API token, ADMIN_TOKEN, EXPORT_TOKEN, or D1 access —
by design, not by accident. A separate, privileged ops session handles
all production Cloudflare/D1 reads and writes. The interface between the
two is versioned, credential-free handoff files under
`.claude/reader-lab-handoff/` (git-tracked, contain only research data —
reviewer pseudonymous IDs, item content/hashes, responses, timestamps,
provenance — never invitation tokens, session hashes, or any
infrastructure secret) plus locally-authored, hash-frozen round manifests
under `reader-lab/rounds/drafts/` that a research session can create
without ever touching Cloudflare. Publication of a frozen manifest is
requested via a small ops-request file (also under
`.claude/reader-lab-handoff/`, also hashed) and executed only by the
privileged session, which returns a credential-free receipt. This session
does not treat a stale caveat about unverified production state as
current: the privileged ops session has since independently confirmed
D1 serves from EEUR/FRA, both pilot reviewers completed, and no secrets
are present in any handoff artifact — this research session still has
none of that access itself, nor does it need it.

**PARENT PILOT: COMPLETE, ANALYZED — TWO SEPARATE RESULTS, NOT ONE
(correction/clarification, 2026-08-12 later pass).** The pilot answers
two DIFFERENT questions, and they must be recorded and read separately,
never collapsed into a single verdict:

- **READER LAB INSTRUMENT USABILITY: PASS.** Both independent
  non-technical reviewers completed practice + real items with no
  coaching; disagreements were articulated/substantive, not evidence of
  UI/category confusion. This is a claim about whether people can *use*
  the instrument.
- **HUMAN LABEL RELIABILITY: NOT YET ESTABLISHED.** Only 1/4 real pilot
  items received clean two-rater agreement; 3/4 produced substantive
  disagreement. The 4 pilot items were invented UX/development examples,
  not a calibration sample. This is a claim about whether the *labels
  produced* are a reliable reference signal — a separate, unresolved
  question the 4-item, 2-rater pilot was never sized or designed to
  answer. **Two-rater agreement is never ground truth, and disagreement
  is never read as a failure of Reader Lab itself** — both directions of
  that conflation are explicitly wrong and are the reason this entry
  exists as a correction.

Read directly from the credential-free handoff
(`.claude/reader-lab-handoff/parent-pilot-completed-2026-08-12.json`,
SHA256 `a7790d64b3aa752076f50a1a62e732ad4f08a2d4b03a58dd0c79b9c61be10afe`,
verified locally against the value the ops session reported — matched).
Both `reviewer_parent_a`/`reviewer_parent_b`: `practice_completed=1`,
4/4 practice + 4/4 real items answered, independently, no assistance
flagged, within the design's own few-minutes-per-session target (~4-6 min
for 4 items each). Full analysis in
`.claude/reader-lab-v0-design-2026-08-12.md` `## 21`. Headline: both
reviewers' free-text comments demonstrate genuine, correctly-applied
understanding of the reading-vs-claim distinction in their own words: no
evidence either reviewer is confused about what the four options mean.
Real-item agreement was 1/4 clean, 3/4 disagreement — but every
disagreement traces to a substantive judgment call (causal language,
what a hedge implies, whether "high-visibility" alone implies "brighter
than before"), not UI/category confusion — this is treated as an
INDEPENDENT TWO-REVIEWER HUMAN REFERENCE, never as consensus ground
truth, per design doc `## 14`. One real usability caveat, not a blocker:
neither reviewer used "I'm not sure" even once across 8 total judgments
each, including on the one practice item built specifically to elicit it
— flagged for future-round monitoring, not treated as evidence the other
three categories are misunderstood.

**RL-2026-001: PUBLISHED, LIVE, ACTIVE / WAITING FOR BOTH RESPONSES.**
Local manifest `reader-lab/rounds/drafts/RL-2026-001.json`, SHA256
`f04bc4ec5970d2c6a135100208e31e78d7d25ecf419b3942f17c3b35242ef6ee`,
published by the privileged ops session per
`.claude/reader-lab-handoff/RL-2026-001-publication-receipt.json`
(manifest/ops-request hashes independently re-verified before publish,
both matched; `0001_calibration_rounds.sql` applied to production,
purely additive, pilot's own 4 assignments still `round_id=NULL` per
design doc `## 20.8`; both reviewers assigned 5/5, answered 0/5 as of
the receipt). **This research session does not poll production and will
not analyze responses until both reviewers complete — no partial-response
inspection, no manifest edits, no Round 002 yet.**
`dataset_purpose: "development"` (not blind_calibration, not
held_out_evaluation). 5 items, both reviewers get the identical 5,
independently: H08 (decomposition-coverage miss), H17 (R1-factual/
R2-interpretive hedge conflict), H14 (support-strength target — role
agreement, support-strength question, NOT a coverage/decomposition test),
H05 (second independent R1/R2 hedge-conflict instance, chosen over H03 to
avoid repeating H17's identical short NSFC source snapshot in the same
5-item session), and the De Hooch/Z development-set claim as CONTROL (R1
and R2 already agree — `r1_agreement: "consistent"` — clean internal
adjudication, chosen over an NSFC/SNSF control for topic diversity and
non-specialist accessibility). All internal labels/expected
answers/R1-R2 machinery stripped from the reviewer-facing form (SOURCE /
THE SENTENCE / 4 plain-language choices only). Ops publish request
frozen at `.claude/reader-lab-handoff/RL-2026-001-ops-request.json`,
SHA256 `5f14efc7ac257f8a6d35635b9bbd764a36c3a88d7fbe97c7a752ed1920723d53`
— **not sent, no production write attempted by this session.** Reuses
both reviewers' existing pilot invitations; no new credentials requested.
Per explicit instruction: do not analyze Round 001 responses until BOTH
reviewers complete, once published.

**ADMIN CONTROL PLANE (`/admin`) — BUILT + LOCALLY TESTED, NOT DEPLOYED
(2026-08-12, privileged ops session).** A visual admin surface (dashboard/
rounds/results/reviewers/import — five screens, not a CMS) now exists in
`reader-lab-worker/src/{publish,access,adminApi,adminUi}.js` plus additive
migration `0002_admin_control_plane.sql`, so operating Reader Lab (create
a round, review it, freeze it, publish it, read results, manage
reviewers) no longer has to depend on remembering CLI commands or a
specific privileged session. **Normal human operation going forward is
`/admin`; the existing `X-Admin-Token`/`X-Export-Token` CLI routes remain,
but only for automation/emergency/debugging use.** Full design in
`.claude/reader-lab-v0-design-2026-08-12.md` `## 23`. Headlines:

- **One publication path.** `src/publish.js`'s `canonicalizeManifest ->
  validateManifest -> freezeRound -> publishRound` is now the only way a
  round's content is ever written to `items`/`assignments` — the admin
  UI, `POST /admin/api/import`, and the machine `POST /admin/publish`
  all call the exact same functions. This retires the original
  RL-2026-001 publication path (hand-run `wrangler d1 execute` against
  interpolated SQL); every value now reaches D1 through a bound
  parameter. Verified directly: a round with embedded newlines,
  em-dashes, curly quotes, and non-ASCII content round-tripped
  byte-for-byte through draft -> freeze -> publish -> the reviewer-facing
  API.
- **Auth is Cloudflare Access, not `ADMIN_TOKEN` in a browser** —
  `src/access.js` independently verifies the Access JWT itself (JWKS +
  RS256 signature + aud/exp/iss), never trusting a header blindly.
  **Checked directly against the Cloudflare API this pass: Zero Trust is
  NOT enabled on this account** (`access.api.error.not_enabled`), which
  needs a one-time interactive dashboard step no API token can perform.
  Per the standing instruction for exactly this situation, the admin
  surface is fully built and tested but **deliberately not deployed to
  production** — every `/admin*` route already fails closed (503)
  without `ACCESS_TEAM_DOMAIN`/`ACCESS_AUD` set, so this is safe to
  deploy later without exposing anything before Access is wired up.
  Exact remaining manual steps documented in
  `reader-lab-worker/README.md`'s "Admin control plane" section. Since
  there's no live Access instance to test against yet, the JWT
  verification itself was unit-tested in isolation (self-signed key,
  monkey-patched JWKS fetch): valid/expired/wrong-audience/wrong-issuer/
  tampered-signature/forged-different-key/malformed all behaved
  correctly.
- **Local test pass, not production.** Migration + all new code tested
  against a fresh local D1 replica only — RL-2026-001 and the pilot's
  production data were never touched by this pass (no `--remote` D1
  command was run against them; only earlier read-only queries against
  production, already covered above, were run to confirm current state
  before writing any code). Full test list in the design doc `## 23.6`.
- **Files added:** `reader-lab-worker/src/util.js` (generic helpers,
  extracted out of `index.js`), `src/access.js`, `src/publish.js`,
  `src/adminApi.js`, `src/adminUi.js`,
  `migrations/0002_admin_control_plane.sql`. `src/index.js` gained three
  new routes (`/admin`, `/admin/api/*`, `/admin/publish`) and now imports
  the shared helpers from `util.js` instead of duplicating them — no
  reviewer-facing route (`/invite`, `/session`, `/api/session`,
  `/api/response`) or legacy `/admin/*` `X-Admin-Token` route changed
  behavior.
- **Not done in this pass, on purpose:** no production deploy, no
  production migration apply, no B2/CJ research change, no Round 002, no
  auto-publication of anything, no change to RL-2026-001's content or
  responses, no change to the pilot reviewers' credentials, `cripminds.com`
  untouched.

**ADMIN CONTROL PLANE — DEPLOYED AND LIVE (2026-08-12, continuation
pass), supersedes the "NOT DEPLOYED" entry above.** Jascha enabled
Cloudflare Zero Trust and created the Access application manually. This
pass verified that configuration directly against the live Access API
(not taken on trust), found and fixed two real gaps before deploying —
the app initially had zero policies attached (not "too broad," simply
unconfigured — fixed to one `allow` policy restricted to two specific
emails), and the app's path scope initially also intercepted the
pre-existing `X-Admin-Token`/`X-Export-Token` machine routes, which
shared the `/admin` prefix (Cloudflare Access protects a path and every
subpath beneath it, with no exception mechanism — confirmed directly,
not assumed). **Fix: the legacy machine routes moved from `/admin/*` to
`/ops/*`** — `/ops/invitations`, `/ops/invitations/revoke`, `/ops/items`,
`/ops/assignments`, `/ops/status`, `/ops/export`, `/ops/publish` — a
structural fix, not a workaround. Migration `0002` applied to production
(before/after row counts identical, all 14 item content hashes
byte-identical, RL-2026-001 correctly backfilled to
`status='published'`). Worker deployed. Full live security test pass (10
checks): unauthenticated `/admin` and `/admin/api/*` blocked at
Cloudflare's edge with zero data leakage; reviewer routes unaffected;
`EXPORT_TOKEN` confirmed read-only (works on `/ops/status`/`/ops/export`,
rejected on every write route); no secrets in any response. One check
not positively completed: this session doesn't retain the production
`ADMIN_TOKEN` value (by design), so only its rejection of a wrong token
was verified, not a correct one succeeding. Visual confirmation of the
rendered `/admin` UI itself was NOT done by this session — Access
intercepts every request to that path at Cloudflare's edge regardless of
how it's reached (confirmed even via a live `wrangler dev --remote`
preview), so only Jascha's own authenticated visit can complete that
check; the underlying data (pilot complete, RL-2026-001 published/active,
both parents 5/5 assigned/0/5 answered, reviewers list, rounds list) was
independently confirmed correct via `EXPORT_TOKEN` reads. **No test round
published or assigned to any reviewer. No B2/CJ change. No RL-2026-001
content/response change. No new/rotated reviewer credentials.** Full
detail: `.claude/reader-lab-v0-design-2026-08-12.md` `## 23.8`.

**LOGIN FIX + VISUAL CONFIRMATION (same day, immediately after
deploy).** First real login attempt failed ("That account does not have
access") — root cause: Cloudflare's built-in Access IdP authenticates
against the visitor's actual Cloudflare-dashboard login, and this
account's only member is `dev@nullspace.it`, which wasn't in the
policy's two-email allowlist. Confirmed with Jascha directly (not
guessed), then added `dev@nullspace.it` to the same `allow` policy
via API (now 3 emails, still one policy, no exclude/require, no broad
rule — re-verified). Jascha then confirmed by screenshot: the live
dashboard at `https://lab.cripminds.com/admin` renders correctly —
`RL-2026-001` Active, `reviewer_parent_a`/`reviewer_parent_b` both 0/5,
rounds table correct, New round/Import draft actions present. Visual
smoke test (the one item not completed by this session directly) is now
independently confirmed.

**CLOSE-OUT PASS (same day).** Human production smoke test recorded
complete above and in the design doc's new `## 23.9`. Ran a post-deploy
regression check confirming the six legacy machine paths
(`/admin/status`/`/admin/export`/`/admin/items`/`/admin/invitations`/
`/admin/assignments`/`/admin/publish`) do not work as an accidental
second API surface: all six return `302` in production (Access
intercepts first) and plain `404` against a clean local instance with no
Access involved (proves the Worker's own routing table doesn't recognize
them, not just that Access happens to sit in front) — the real `/ops/*`
equivalents confirmed working in both. Now a standing, repeatable
procedure in `reader-lab-worker/README.md`. Updated remaining
present-tense `/admin/invitations`/`/admin/items`/`/admin/assignments`/
`/admin/status`/`/admin/export`/`/admin/publish` mentions in the design
doc's forward-looking sections (`## 20.3`–`## 20.7`, `## 23.3`–`## 23.4`)
to `/ops/*`, each pointing back to `## 23.8` for why — genuinely
historical narrative (past hardening-pass log entries, the `## 23.8` bug
account itself) left untouched on purpose, per this file's own
append-only convention. **Standing, deliberately preserved caveat:** a
correct `ADMIN_TOKEN` succeeding against `/ops/*` still hasn't been
positively exercised — this session doesn't retain that value and did
not rotate it to manufacture a test; only wrong-token rejection is
verified. **Operating model, confirmed live:** human → `/admin` via
Cloudflare Access; machine → `/ops/*` via `ADMIN_TOKEN`/`EXPORT_TOKEN`
per route; reviewer → existing invite/session flow, unchanged throughout.
No Round 002. No RL-2026-001 response inspection. No B2/CJ change. No
credential rotated. No further deploy — documentation and one Access
policy addition only.

**ROUTINE-OPERATIONS AUTOMATION — DEPLOYED (2026-08-12, infrastructure
pass).** The privileged Claude/Cloudflare session is no longer needed for
day-to-day Reader Lab operation at all. A round now completes itself —
`src/publish.js`'s `maybeCompleteRound` runs inside the same request as
the last reviewer's response, an atomic `UPDATE ... WHERE status =
'published'` that only the one request which actually finishes the round
can ever trigger (idempotent by construction, no polling, no scheduled
"did anything finish?" check anywhere). The moment that happens, a
canonical, credential-free research export generates automatically in
the background (`ctx.waitUntil`) via one shared service,
`buildResearchExport` in the new `src/researchExport.js` — the same
function the admin UI's Download/Retry buttons, the hourly cron
reconciliation sweep, and the machine `GET /ops/rounds/:id/export` route
all call, never a second export path. The export's own SQL only ever
touches `rounds`/`items`/`assignments`/`responses` — no reference
anywhere to `invitations`/`sessions` — so a leaked token or session hash
is structurally impossible, not just avoided by care. A `ready` export is
immutable (never recomputed once generated); a failed attempt leaves
responses fully intact and shows `EXPORT ERROR — Retry available` in the
admin UI, with both a manual Retry button and an hourly cron safety net
able to repair it. Migration `0003_research_export.sql` (additive:
`rounds.completed_at`, `assignments.item_order`, new `research_exports`
table) applied to production — verified purely additive (all row counts
unchanged, all 14 pre-existing items' content hashes byte-identical).
RL-2026-001's `item_order` backfilled from its own already-public
publication receipt (structural metadata, not response content). Full
local test pass (18 scenarios: partial/full/idempotent completion,
secret exclusion, ordering/hash determinism, Unicode/newline
preservation, incomplete-round rejection, auth boundaries, genuine
failure + recovery + idempotent retry, cron self-heal) all passed before
deploy; production deploy verified read-only (reviewer route unaffected,
`EXPORT_TOKEN` counts matched pre-deploy exactly, admin still
Access-gated). RL-2026-001 remains `published`, not `completed` — its
completion *count* was checked before and after (never its answer
content). **Normal human workflow is now, in full: open `/admin`,
create/import a round, review it, Freeze & Publish, wait — the dashboard
auto-detects completion — then download the research handoff JSON
directly into `.claude/reader-lab-handoff/` with no redaction step.**
Privileged ops/wrangler is needed only for deploys, migrations, Access
config, and incidents. Full detail:
`.claude/reader-lab-v0-design-2026-08-12.md` `## 24`. No Round 002. No
RL-2026-001 answers inspected. No B2/CJ change. No credential rotated. No
reviewer invitation/session model change.

**CALIBRATION ORCHESTRATOR — DEPLOYED, RUNNER RUNNING NON-PERSISTENTLY
(2026-08-12, infrastructure pass).** A completed round now analyzes
itself. The moment a round's research export is ready, a Cloudflare
Workflow instance (`CalibrationWorkflow`) starts automatically —
idempotent by construction (keyed on round_id + export hash + workflow
version, same discipline as `## 24`'s export idempotency) — creates a
claimable job, and durably waits for the private, Tailscale-only Trident
runner (`calibration/runner/calibration_runner.py`) to poll, execute, and
submit a hash-validated result back over `/ops/calibration/jobs/*`,
authenticated by its own new, narrow `CALIBRATION_RUNNER_TOKEN` (never
`ADMIN_TOKEN`/`EXPORT_TOKEN` — verified directly against production that
it cannot touch any general admin/ops route). Two versioned, hashed
workflow definitions (`calibration/workflows/analyze-human-round-v1.md`,
`prepare-next-round-v1.md`) — both **mostly deterministic**, direct
transcriptions of categories this project already established in prose
(`## 20.4`/`## 14` of the design doc) rather than new research judgment;
the one model call (an optional per-item descriptive `notes` field) can
never affect disposition/agreement/reference-strength/machine-comparison,
all computed before it's ever invoked. `prepare-next-round-v1` has no
model call at all in v1 — the eligible-candidate pool
(`calibration_candidates`) starts and stays empty on purpose (a research
decision this infrastructure pass doesn't make), so it correctly reports
`NEEDS_ELIGIBLE_CANDIDATES` rather than inventing a candidate, and
independently fails closed — twice — if `held_out_evaluation` material
ever appears in that pool. `/admin`'s new Calibration section shows
current round, workflow state, evidence summary, timestamped history,
and next action, with a Retry button for a failed run (fresh
run+instance from scratch — analysis is versioned/recomputable, unlike
the immutable-once-generated research export).

Migration `0004` applied to production, verified additive. Both workflow
definitions registered with real file hashes. RL-2026-001's
`research_context` backfilled as a `calibration_artifacts` row from
already-public repo artifacts (rationale/provenance fields already in
`reader-lab/rounds/drafts/RL-2026-001.json` and this file's own earlier
RL-2026-001 entry) — no response content read to build it, this pass or
any prior one. A full synthetic end-to-end test (real runner code, real
local Worker, two synthetic reviewers, a real 2-item round) caught and
fixed three real bugs before any of this touched production: `step.
waitForEvent` resolves to the full event envelope, not just the payload,
contradicting Cloudflare's own worked doc example; Workflow instance ids
have a charset+length limit the retry handler's naive concatenated key
violated; and cross-language (JS/Python) result-hash validation needed
its own canonical serialization, since plain `JSON.stringify`/`json.dumps`
disagree on whitespace/key-order/Unicode-escaping — `calibrationWorkflow.js`
itself had this exact bug in its own validation step until the test
caught it. A fourth real bug was found only by testing against live
production: Python's default `urllib` User-Agent was silently `403`'d by
Cloudflare's edge before ever reaching the Worker (identical `curl`
succeeded) — fixed by setting an explicit User-Agent, then verified
working end-to-end against real production immediately after.

**This pass required the first-ever commit+push of this whole Reader
Lab engagement** — Trident can only run code from `git pull origin
main`, and nothing had been committed before (per this repo's standing
"commit only when asked" rule). Explicitly authorized this pass: a
scoped commit (`ffe44fb`, plus fix `c1730e6`) built by inspecting the
complete diff and staging exactly the Reader Lab + calibration
transitive dependency set, deliberately excluding this file
(`current-work.md` — its uncommitted diff was inseparably interleaved
with unrelated CJ-1/CJ-2 research narrative from other passes) and every
B2/CJ-1/CJ-2 research file. A secret scan on the exact staged diff found
nothing before committing. Trident pulled and was pinned to the exact
commit SHA (recorded on Trident, not just asserted), verified via a
direct file-hash comparison against the local copy.

**Not yet done, one remaining manual step:** the systemd unit
(`cripminds-calibration-runner.service`) is not installed —
`/etc/systemd/system/` needs root, and `sudo` on Trident needs an
interactive password this session doesn't have. The runner is currently
alive as a plain background process (started this pass, confirmed
polling production cleanly) but will **not** survive a Trident reboot or
an accidental kill until Jascha runs the three-line install in
`calibration/runner/README.md`. Full detail, including exactly what the
synthetic test caught and how idempotency/failure-safety were verified:
`.claude/reader-lab-v0-design-2026-08-12.md` `## 25`.

B2 (unchanged pointer): current research state is still whatever
`## ROADMAP / ACTIVE PHASE` below says — this pass did not read, run, or
change any B2/CJ-1/CJ-2 code, prompt, fixture, or experiment. RL-2026-001
remains `published`, not `completed` — parent_a still has not answered
(checked by count only, before and after this pass, never by reading
response content).

**POLICY-DRIVEN AUTONOMY — DEPLOYED (2026-08-12, continuation of the
interrupted infrastructure pass).** Picked up exactly where the prior
session stopped (`.claude/reader-lab-v0-design-2026-08-12.md` `## 26.0`,
the "4/9 is lifetime, not RL-2026-001 progress" count-audit correction —
re-verified unchanged before touching anything: `reviewer_parent_a` still
5 assigned/0 answered on RL-2026-001). Replaced three hard-coded
automation boundaries (reviewer assignment, additional review, round
publication) with an explicit, versioned `calibration_policies` table
(migration `0005_policy_driven_autonomy.sql`) — `src/policy.js`,
`src/reviewerEligibility.js`, `src/additionalReview.js`,
`src/roundPublicationPolicy.js`, wired into `calibrationWorkflow.js`/
`calibrationOrchestrator.js`/`calibrationAdmin.js`, plus a new `/admin` →
**Policy** screen and an automation-state summary on the Dashboard
("No action required." shown as plain text, not an empty list, when
nothing needs Jascha). Full design, exact mechanics, and the real
end-to-end verification (three policy values tested against a live local
Worker + D1 + the actual `calibration_runner.py`, not a mock — disagreement
→ correctly flagged `NEEDS_POLICY_CONFIGURATION` rather than inventing a
threshold; after configuring a count, a third synthetic reviewer who
hadn't judged that content was automatically assigned and, under
`automatic_if_valid`, auto-published) in the design doc's new `## 26.1`–
`## 26.8`.

**A coordination incident happened mid-pass, corrected before any damage:**
a background research fork (tasked read-only) independently began
implementing this same feature under different file/module names in the
same working tree, in parallel with this session's own independent
implementation. Caught via `git status` showing unexpected file changes,
confirmed via `ListAgents`, stopped immediately (`TaskStop`) before it
touched any Cloudflare/D1 write path. Reviewed both implementations in
full; the fork's (further along — already wired end-to-end, and its
design was in a few real ways stronger: a NULL-by-default reviewer count
that fails closed instead of guessing, content-hash-based reviewer dedup,
one shared publish-decision function reused for both draft types) was
kept as canonical; this session's own now-redundant files were deleted
before any of them were committed or deployed. No duplicate/conflicting
code reached git or production.

Also fixed, found true during this pass's own verification: the runner's
pin-file mechanism the README already claimed existed (`/srv/secrets/
cripminds-calibration/deployed-commit-sha.txt`) was real on disk (checked
directly on Trident) but **the wrapper script never read it** — it still
unconditionally `git pull origin main`'d every restart. Fixed in
`calibration/runner/cripminds-calibration-runner.sh` (design doc
`## 26.8`). **Not yet applied to Trident's live copy** — this session can
write files on Trident as `jascha` over SSH but does not have
passwordless `sudo` for the `systemctl restart` needed to pick up either
the new wrapper script or a freshly-pinned commit SHA; not blocking,
since every new mechanism in this pass lives in the Worker/D1, which
deploys directly via the Cloudflare API, and the runner's own Python code
is unchanged. **One remaining manual step for Jascha:** copy this pass's
`calibration/runner/cripminds-calibration-runner.sh` to
`/srv/scripts/ops/cripminds-calibration-runner.sh` on Trident, write the
new commit SHA to the pin file, and run `sudo systemctl restart
cripminds-calibration-runner`.

No B2/CJ change. No RL-2026-001 content/response read or modified. No new
reviewer invited to production (all end-to-end testing used synthetic
`reviewer_test_*` accounts against a local D1 replica only, cleaned up
after). No fine-tuning run. No production-promotion mechanism built.

**RL-2026-001 COMPLETE, ANALYZED, FIRST REAL HUMAN×B2 CALIBRATION
EVIDENCE (2026-08-13).** Both reviewers 5/5. Autonomous
`analyze-human-round-v1` ran (policy-v2): **2 strong_reference (slots
3/H14, 5/De-Hooch-Z), 3 contested (slots 1/H08, 2/H17, 4/H05)**, 0
provisional/needs_more/insufficient — the only arithmetically possible
split with 2/2 reviewers answering, confirmed against the deterministic
rule table before trusting the counts. Pulled read-only from production
D1 by a peer ops session per cross-session request (this session has no
D1/Cloudflare credentials by design) — `.claude/reader-lab-handoff/
RL-2026-001-analysis.json` + `-research-export.json`, not committed yet.

**Key finding, not visible from the round_summary counts alone:**
`machine_comparison` only compares ROLE (factual-dependency-shaped vs.
interpretive), never support DIRECTION. Slot 5 (the control!) shows
`machine_comparison: aligns` on role, but both reviewers independently
selected "source supports this" (`source_established`) while B2's own
R1/R2 agreed the same claim is `unsupported` — a real, substantive
divergence the role-only field masks. Slots 2 and 4 (the two
R1-factual/R2-interpretive hedge-conflict cases, H17/H05) both split
the SAME way — one reviewer `interpretive_only`, one
`source_established` — and in NEITHER case did either reviewer pick
"adds something unestablished." Replicated twice, this is structured
evidence, not noise: on this failure shape, independent human readers
landed on positions at least as permissive as R2's own resolution, not
stricter. Slot 3 (H14) is genuine full alignment (both reviewers
`unsupported_factual_dependency`, matching B2 in both role and
direction) — the one case B2's conservatism is human-endorsed. Slot 1
(H08, the coverage-miss target) is mixed: one reviewer independently
flagged `adds_unestablished` (partially validating the miss B2 should
have caught), the other said `uncertain` for stated comprehension-
difficulty reasons, not epistemic disagreement about source support.

**Pattern across 5 cases: 1 confirms B2, 3 lean more-permissive-than-B2
(2 clearly, 1 mixed), 1 is a genuine control reversal.** Small sample
(n=2 reviewers, n=5 items) — not proof, but real first-round signal
specifically on the R1-factual/R2-interpretive hedge shape and on the
base unsupported/support threshold generally. **additional_review
(policy-v2) correctly reported `NEEDS_HUMAN_ACTION` on all 3 contested
items — 0 of 1 required eligible reviewers exist, since parent_a/b
already judged everything** — not a bug, blocked by reviewer-pool size,
needs a new approved reviewer or Jascha's manual adjudication.
`dataset_disposition` (the admin UI's "research disposition" nudge) is
a separate, deliberate, never-auto-set editorial field
(`development_reference`/`contested`/`hold_for_later`) — unset is not
blocking, not a bug. `calibration_candidates` pool remains deliberately
empty (`prepare-next-round-v1` → `NEEDS_ELIGIBLE_CANDIDATES`, expected
v1 state) — no RL-2026-002 created. No D0/C0/R1/R2/repair-v1/admission-
policy edit. No Stage C run. No contested case rescored into binary
truth.

**B2 HUMAN-CALIBRATED SUPPORT-BOUNDARY AUDIT (2026-08-13, same
session), DECISION A.** Read the exact frozen R1/R2 record (role,
support, `why`, conflict state) for H14/De-Hooch/H17/H05's specific
reviewed claims — zero model calls. **Precise mechanism found:** H14
and De Hooch share identical role (`factual_dependency`), identical
support call (`unsupported`), identical no-conflict state, yet only
H14 is human-endorsed (both reviewers: `unsupported_factual_dependency`).
The `why` text pinpoints exactly why: H14 invents a wholly new,
textually-unanchored property (the word's semantic "function," never
addressed anywhere in the source); De Hooch's `causality_hardening`
flag instead penalizes CONNECTING two facts the source already states
adjacently, same speaker, same quote (the curator's own words move from
"more obvious drinking game" straight to "more moralistic... the
intention") — reviewer A's own comment independently isolates this
exact same connective move, then judges it doesn't cross the support
line. H17/H05 corroborate from the other side: R1's blind
`empirical_dependency=true` is never validated by either human; R2's
own override to `interpretive_only` already tracks human leniency more
closely — the friction is the R1/R2 disagreement itself, not R2's
resolution.

**Calibration hypothesis, narrow and falsifiable:** B2/R2's
`causality_hardening`/mechanism check doesn't distinguish "new fact, no
textual anchor" (H14-shaped, human-endorsed) from "causal synthesis of
two already-adjacent, same-passage source facts" (De-Hooch-shaped,
human-reversed) — independent readers draw exactly that line, B2
currently doesn't. Plausible (not proven) connection to the 0/14
Stage-C zero-safe finding: adjacent-fact synthesis is close to
definitionally what Stage A's `interpretive_inference`/
`conceptual_shift` fields are built to do — if R2 flags that common
move the same as a wholly unanchored fact, that would help explain the
pervasive `unsafe` rate. Reader Lab instrumentation gap recorded (not
fixed): `machine_comparison` checks role only, never support direction
— exactly what made De Hooch's "aligns" label misleading; a future
additive schema (`role_alignment`/`support_alignment`/`overall_relation`)
is designed but not built. Next-experiment design proposed (boundary-fit
+ contrast + anti-overcorrection + fresh cases, no held-out leakage) but
not executed. No D0/C0/R1/R2/repair-v1/admission-gate/Stage-C/Reader-Lab
code change this pass. Full detail in the experiment doc's `## B2
HUMAN-CALIBRATED SUPPORT-BOUNDARY AUDIT` section.

**B2 SUPPORT-BOUNDARY TARGETED CALIBRATION ROUND DESIGN (RL-2026-002
DRAFT, 2026-08-13, same session) — PREPARED, NOT PUBLISHED, BLOCKED ON
A REAL INFRASTRUCTURE GAP.** Zero model calls. Searched 3 already-
completed real corpora for `causality_hardening`/`mechanism_invention`
claims fitting the two hypothesized families. **Honest yield:** many
clean `UNANCHORED_PROPERTY` candidates found (H11/c6, `01_cave_dna/S`
c8); only **one** unambiguous `ADJACENT_FACT_SYNTHESIS` candidate found
(H04/c10) plus one weaker compound-tagged second (H12/c6) — corroborates
the audit's own point that the clean pattern is rare. Several real
candidates explicitly excluded, not force-fit (H13's causal claims —
source never draws the link itself, unlike De Hooch; H02's mechanism
claims — elaborate around one fact, not a synthesis of two; older H18
candidates — a third, over-precise-resequencing shape; De Hooch/Z's
other claims — same reading as RL-2026-001's already-used one,
near-duplicate). **Final round: 5 items** (2+2+1 control — H16/c4, a
genuinely `supported` claim, since De Hooch/Z turned out not to be a
clean supported baseline). Zero `candidate_claim_id` overlap with
RL-2026-001, verified. Both reviewers eligible (fresh content).
Produced, all local/uncommitted: the calibration_candidates-shaped
manifest, the analysis preregistration (exact hypothesis, per-family
plan, anti-overcorrection check, no arbitrary threshold), the
research-context artifact (storing `machine_role`/`machine_support`/
`machine_effective_state` SEPARATELY from the start — the fix for
RL-2026-001's own role-only blind spot, applied forward without
touching RL-2026-001's history), and the reviewer-facing draft (family
labels/hypothesis/machine fields all hidden). **Real blocker, confirmed
by code inspection: `calibration_candidates` has no write path
anywhere in the codebase** — `calibrationWorkflow.js` only ever
`SELECT`s from it, no admin-API insert route exists — so
`prepare-next-round-v1` cannot run on this round for real without raw
SQL, which this pass's own instructions forbid treating as the launch
path. **Stopped here per instruction** — nothing inserted, nothing
published, RL-2026-001 untouched. Full detail in the experiment doc's
`## B2 SUPPORT-BOUNDARY TARGETED CALIBRATION ROUND DESIGN` section.

**CANDIDATE BRIDGE BUILT + RL-2026-002 INGESTED — DEPLOYED (2026-08-13,
infrastructure pass, picks up exactly where the entry above stopped).**
Removed the "no write path" blocker: `src/candidateIngestion.js` is now
the one write path for `calibration_candidates` (deterministic identity,
idempotent, fail-closed on held-out/reuse/hash-mismatch/`eligible_for_
reader_lab != true`), reachable via `POST /ops/calibration/candidates`
(`CALIBRATION_RUNNER_TOKEN` or `ADMIN_TOKEN`) or `/admin` → Candidates.
Corrected RL-2026-002's own H12/c6 candidate internally (own subtype,
`ADJACENT_FACT_SYNTHESIS_WITH_HEDGE_HARDENING`, not a clean co-equal
instance) before ingestion — reviewer-facing content untouched. Added
`analyze-human-round-v2`: `role_alignment`/`support_alignment`/
`overall_relation`, additive, fixing the exact De Hooch/Z blind spot
(`## 26.0`'s own audit) — `machine_comparison` keeps its old, role-only
meaning for compatibility, never retroactively reinterpreted.
`reconcileStuckCalibrationRuns` resumes a run stuck at
`NEEDS_ELIGIBLE_CANDIDATES` automatically the moment eligible candidates
exist — no "retry" click required.

Ingested the real, frozen RL-2026-002 bundle (all 5 candidates, zero
rejections) via `prepare_calibration_candidates.py`, run on Trident with
the real production runner token — not simulated, not raw SQL.
Reconciliation fired automatically, resumed RL-2026-001's stuck run, and
autonomously produced a round named **RL-2026-002** (the sequential
numbering logic's own choice, matching the research design's planned
name by coincidence, not by hardcoding). Under the active policy
(`policy-v2`, `shadow_automatic`): `would_publish: true` recorded, round
left `frozen`, **not published** — confirmed directly against
production. RL-2026-001's original v1 analysis artifact confirmed
byte-identical (hash matched) throughout; its round-scoped counts
(5/5, 5/5) unchanged. One honest note: the resumed run's own re-analysis
of RL-2026-001 happened to run under old (v1) runner code — a benign
timing artifact of a mid-deploy restart, not a defect; the v2 fix itself
was independently verified via a real local De-Hooch-shaped test
producing exactly the corrected fields.

**A real incident was found and fixed while deploying, unrelated to the
candidate bridge itself:** the calibration runner's own pin mechanism
(from the *previous* infrastructure pass) detached HEAD directly on
Trident's shared content workspace — which turned out to collide with a
separate, independent daily content-publishing automation that also
commits straight to this repo's `main` on the same shared working tree.
Two of that bot's commits (a routine publish + a new article, both
genuine, both unpushed) landed on the detached HEAD instead of advancing
`main`, reachable only via `git reflog`. **Recovered, not lost** — `git
branch -f main <tip>`, no push (publishing that bot's content is its own
decision, not this pass's). **Fixed at the root**: the runner now checks
out its pin into its own dedicated git worktree
(`.calibration-checkout`, a subdirectory already inside its existing
`ReadWritePaths` — no systemd change needed), leaving the shared
workspace on `main` permanently for the other bot. Full detail, design
doc's `## 27`, especially `## 27.7`.

No B2/CJ semantic change (D0/C0/R1/R2/repair/Stage C untouched). No
fine-tune. No policy changed to `automatic_if_valid`. No RL-2026-001
judgment changed. No new reviewer identity manufactured.

**REVIEWER EXPERIENCE — CASE INTEREST / ACCESSIBILITY (2026-08-13,
same session, design/backlog only).** From direct operator/reviewer
observation during RL-2026-001/002 (both already published/active,
neither touched by this entry). **Correction worth stating precisely:
source length is not the primary complaint — the actual problem is
niche, overly technical, awkwardly written, or specialist-dependent
CONTENT**, which risks turning participation into unpaid specialist
fact-checking rather than something a volunteer returns to. Recorded
in the design doc's new `## 28`: (1) the non-negotiable boundary —
reviewer experience improves only through case selection/round
composition, never by rewriting source/claim/hedges/evidence, since
that would change what's being calibrated; (2) an immediate, safe,
non-semantic rule adopted starting with the *next* round design (not
retroactive): before accepting a niche/technical candidate, check
whether an equally informative, more generally readable one exists;
keep roughly ≤1–2 especially demanding items per normal 5-item round
unless the research question itself requires an all-technical set;
(3) round-composition variety guidance where the hypothesis permits
it; (4) a `reviewer_accessibility`/`accessibility_notes` internal
metadata field, **designed only, not implemented** — never reviewer-
visible, never allowed to influence any disposition/alignment field;
(5) a future `prepare-next-round` priority order (methodological
eligibility → hypothesis value → blindness/provenance → accessibility
→ variety, with accessibility/variety strictly secondary) — design
intent, not built; (6) backlog item **READER EXPERIENCE V2** (mini-
puzzle framing, topic mixing, progress cues, post-round context) with
an explicit avoid-list (no gamification, no leaderboards, never
revealing whether a reviewer was "correct," nothing that could bias
calibration). No round created. No prompt/schema change. RL-2026-001/
002 unchanged.

**B2 ZERO-SAFE BOTTLENECK ATTRIBUTION AUDIT (2026-08-13, same session),
zero model calls.** Eligible corpus: the 14-item Stage-C probe minus
RL-2026-002's 4 (H04/H11/H12/H16) = 10 items (H06/H15 D0-blocked; 8
unsafe: H01/H02/H03/H07/H09/H10/H13/H18). **Headline finding: 0/8 are
`POTENTIALLY_UNLOCKED` by RL-2026-002's hypothesis** — read all 42
unsupported claims' exact tags + full `why` text; none matches the
clean two-fact adjacent-synthesis shape RL-2026-002 actually tests.
Real dominant shapes instead: **Shape A, wholly unanchored** (H03 6/6,
H09 1/1, H10 5/5 — population/motivation/instrument-limitation claims
with zero source anchor); **Shape E, single-fact mechanism elaboration
with only partial anchor** (H02 11/11, H13 10/12, H18 1/2 — a real but
DIFFERENT pattern from clean synthesis, currently untested by any
Reader Lab round, and the exact reason H13's claims were already
excluded from RL-2026-002's own pool); **Shape C, hedge/modality
hardening** (H01 2/2, H07 2/3); **Shape F, D0 structural** (H06, H15).
**Meta-finding: the `causality_hardening`/`mechanism_invention` TAGS
conflate clean adjacent-synthesis (rare) with single-fact mechanism
elaboration (common) — tag ≠ shape, required full `why`-text reading
to separate.** Anti-overcorrection set recorded (H03/c7, H03/c9,
H09/c10, H10/c1 — clean Shape-A, non-Reader-Lab). Zero potential future
Stage-C admission cases found — the one clean synthesis instance
(H04/c10) was already spent on RL-2026-002 itself. Roadmap: Phase 1
(current, RL-2026-002) → **Phase 1.5 (new recommendation): a separate
round testing Shape E specifically, the largest uncalibrated category**
→ Phase 2 (targeted B2 experiment, scope likely needs Shape E too) →
Phase 3 (re-run integrated probe, check natural admissions + anti-
overcorrection set holds) → Phase 4 (held-out eval, only once stable
across ≥2 probes) → Phase 5 (freeze/promotion). Exit criteria are
qualitative/structural, no invented percentages. No B2/Stage-C/RL-2026-002
touch this pass. Full detail in the experiment doc's `## B2 ZERO-SAFE
BOTTLENECK ATTRIBUTION AUDIT` section.

**B2 SHAPE-E TARGETED HUMAN-CALIBRATION ROUND DESIGN (RL-2026-003
DRAFT, 2026-08-13, same session) — ZERO MODEL CALLS, FROZEN LOCALLY,
NOT PUBLISHED, NOT INGESTED.** Shape E defined precisely against A/B:
source states ONE fact, candidate supplies an invented explanatory
mechanism/cause/motive for it (real anchor, unlike A; only one fact,
unlike B's two-fact synthesis). **Found a 4th, previously-unused,
unusually accessible source** — `07_ai_cheating_exam/M` (the original
FIRST REFERENCE PROBE corpus) — carrying clean Shape-E claims, avoiding
over-reliance on just H02/H13/H18. **Final 5, each from a different
item:** Shape E x3 (AI-cheating-exam c13, H13/c11, H02/c17 — 3 distinct
topics), Shape-A contrast (H03/c14 — fresh, NOT one of the 4 reserved
regression cases, which stay untouched), control (H18/c2, genuinely
supported; the round's one more-technical item, within the ~1-2
guidance). Zero overlap with RL-2026-001/002 `candidate_claim_id`s,
verified. Preregistration includes an explicit interpretation guide
(unsupported → strictness supported; interpretive/established →
justified future target; mixed → wait). Structural backlog recorded,
not acted on: modality hardening (Shape C, H01/H07) as a possible
future third round; D0 span-resolution failures (H06/H15) as a future
structural audit, not a Reader Lab question. **Automation: confirmed
from code that `reconcileStuckCalibrationRuns` only resumes
`needs_eligible_candidates` runs — RL-2026-002 isn't one, so ingesting
now would likely be safe — but chose NOT to rely on that inference;
kept everything frozen locally, ingesting nothing, publishing nothing,
per the task's own conservative fallback.** RL-2026-002's in-progress
responses not inspected. Full detail in the experiment doc's `## B2
SHAPE-E TARGETED HUMAN-CALIBRATION ROUND DESIGN` section.

**SIMPLE MODE / ADVANCED MODE UX PASS — CODE COMPLETE, LOCALLY VERIFIED,
NOT YET DEPLOYED (2026-08-13).** Structural continuation of the
`0d41ce0` plain-language admin pass: nav restructured to Home/Rounds/
Reviewers + one "Advanced" dropdown (Research results/Policy/
Candidates/Import, all prior URLs unchanged); New round/Import draft
moved off the Dashboard into a collapsed Advanced/Recovery block on
Rounds; Policy and Candidates each gained a plain-language summary
above their existing raw editor/table, now collapsed under Advanced.
Reviewer identity gained an additive `display_name` column
(`migrations/0007_reviewer_display_name.sql`, `reviewer_id` remains the
sole identity key everywhere else) with a friendly Add-Reviewer
flow (Name + optional note → invitation-ready card with copy-link) and
reviewer cards replacing the raw table; every place `reviewer_id` was
shown to Jascha directly now shows `display_name || reviewer_id`
(Results screen specifically replaces the anonymized "Reviewer A/B"
letters with real names, correct here since these are known consenting
reviewers, not a blinded comparison).

**Two real bugs found and fixed via direct investigation, not
assumption:** (1) the duplicate "add another reviewer" Action Required
card — `calibrationAdmin.js`'s automation summary read the last 20
`additional_review_plan` artifacts without deduping by `round_id`, so
a round re-run by the reconciliation sweep or a manual retry produced
one card per run instead of one per round; fixed by keeping only the
latest artifact per round, verified against a synthetic duplicate
locally (two cards → one). (2) `index.js`'s reviewer-facing `el()`
helper set `style="..."` as a raw HTML attribute, which this app's own
CSP silently blocks (same bug class `0d41ce0` already fixed in the
admin UI, just never ported to the reviewer app) — concretely, this
meant the optional comment textarea was visible by default instead of
collapsed behind "Want to say why?", contradicting this doc's own `##
9`. Fixed with the same CSSOM-`style.setProperty` pattern; verified
directly in-browser (`getComputedStyle` before/after, then a full
welcome→practice→real-item→submit walkthrough). A third, smaller bug
(the new Advanced nav dropdown clipping off a 390px mobile viewport)
was also found and fixed the same way.

Reviewer-facing wording itself (four factual-floor choice labels,
practice explanations, welcome/thank-you copy) was checked directly
against this doc's `## 5`/`## 6` and found already correct — left
unchanged, category semantics untouched. One microcopy change only:
progress line now reads "Question 3 of 5" instead of bare "3 of 5".

All of the above verified against a local `wrangler dev --local`
instance with real Playwright browser sessions (not just API calls) —
dashboard dedup, nav at desktop and mobile widths, the full reviewer-
creation-through-copy-link flow, Policy/Candidates/Import's new split,
and a complete reviewer walkthrough including a live response
submission. Synthetic local-only fixtures only (the `0d41ce0` pass's
five `RL-2099-*` rounds, a synthetic duplicate artifact, one real local
Maria invitation) — no production D1 read or write this pass, no
RL-2026-001/002 change, no B2/calibration semantic change, no policy
value changed. Full design rationale and exact verification steps in
`.claude/reader-lab-v0-design-2026-08-12.md` `## 29`. **Not yet
deployed** — migration `0007` has not been applied to production and
the Worker has not been redeployed; stopped here pending explicit
go-ahead given this is presentation work touching a live, in-progress
round (RL-2026-002).

**SIMPLE MODE / ADVANCED MODE UX PASS — DEPLOYED (2026-08-13, same
session, explicit go-ahead given).** Recorded RL-2026-001/RL-2026-002
counts (status, manifest hash, item/reviewer counts, per-reviewer
assigned/answered) before touching anything; confirmed directly against
production the exact duplicate-card bug this pass fixes (two
`additional_review_plan` rows for RL-2026-001, 10:05 and 13:50, both
`NEEDS_HUMAN_ACTION`). Applied migration `0007` to production (`ALTER
TABLE invitations ADD COLUMN display_name TEXT` — one statement, no
default, no NOT NULL) and verified immediately after: same 4 invitation
rows, same `reviewer_id`s/order/`revoked`/`practice_completed`/
`active_for_calibration` values, all `display_name` NULL as expected —
**no backfill exists in the migration**, so `reviewer_parent_a`/`b` keep
showing their raw `reviewer_id` in production until a name is set (no
rename UI was built this pass, deliberately, to stay inside the
requested "no additional code changes" boundary — flagged to Jascha
directly rather than assumed away). Deployed
(`npx wrangler deploy`, Version ID `91bbb680-100f-4812-9b82-c84e6114bdf2`),
verified read-only: `/admin` and `/admin/api/*` still 302 to Cloudflare
Access (not content), `/ops/status` still 401s on missing/bad token, an
invalid reviewer session still fails closed with the plain "This link
isn't valid anymore" page (no crash, no test response submitted). Re-
checked RL-2026-002 after deploy: status/manifest hash/item count/
reviewer count/per-reviewer assigned-answered counts all byte-identical
to the pre-deploy baseline — nobody answered during the short deploy
window, which is expected, not a regression either way. Committed
(`bcc06bd`, six files: the four touched `src/*.js`, migration `0007`,
and the design doc's new `## 29` — `current-work.md` and every B2/CJ-1/
CJ-2/automation file deliberately excluded, same convention as
`ffe44fb`/`0d41ce0`) and pushed to `origin/main`. This session did not
have a working `ADMIN_TOKEN`/`EXPORT_TOKEN` (the on-disk `.export-token`
returned `unauthorized` — stale/rotated, not investigated further) but
does hold a real Cloudflare API token for this account, used only for
the migration/deploy/read-only-verification queries above; full visual
confirmation of the rendered `/admin` UI itself still needs Jascha's own
authenticated visit, same standing limitation as `## 23.8`. No B2/CJ
change. No RL-2026-001/002 response content read. No policy value
changed. No further UX pass started this session per explicit
instruction.

**B2 D0 SPAN-RESOLUTION FAILURE AUDIT (2026-08-13, same session), zero
model calls, both failures reproduced offline.** H06/c4: **Category A**
(model contract violation) — D0 invented a connective ("as") stitching
a paraphrase to a real quoted fragment from a non-adjacent sentence;
confirmed not a fluke — the SAME response's own c3 correctly quotes the
identical real phrase verbatim elsewhere. H15/c13: **Category B**
(resolver too brittle) — exact one-character diff, a dropped trailing
period before the closing quote; confirmed via the SAME response's own
c12, which quotes the identical phrase correctly WITH the period —
the model produced the byte-exact version elsewhere in the same call.
Near-miss search: exactly 1 found (H15/c13 itself, a same-response
sibling of c12) across 21 quote-ending spans this run + a 10-item prior
corpus. **Impact, computed not inferred:** excluding just the one bad
claim from each item, segment-consistency and coverage both pass
cleanly (0 uncovered segments) — the span failure was the SOLE blocker
for both, not a symptom of broader breakdown. **Decision: C — MIXED
MULTIPLE FAILURE CLASSES.** Future fix specified, NOT implemented: a
narrow, ordered fallback on `resolve_anchor` — if the excerpt ends in a
closing quote, try inserting one sentence-terminal punctuation mark
before it, accept only on a unique match, always recover the ORIGINAL
source text (never the model's version) — with a required regression
suite (H15 positive, H06 + synthetic paraphrase cases must-fail, H15's
own sibling c12 non-regression, full corpus non-regression sweep,
synthetic Unicode/punctuation edge cases). No D0/C0/R1/R2/repair-v1/
admission-gate edit. RL-2026-002 not inspected. RL-2026-003 not
ingested, not published. Full detail in the experiment doc's `## B2 D0
SPAN-RESOLUTION FAILURE AUDIT` section.

**B2 ANCHOR RESOLVER TERMINAL-PUNCTUATION RECOVERY — IMPLEMENTED,
VERIFIED (2026-08-13, same session), zero model calls, DECISION A.**
Implemented exactly the H15-shaped fallback in `cj1_v3_anchor_resolver.py`
(now `RESOLVER_VERSION="v2"`, hash `d8f761e5...`→`724f5109...`): if
steps 1-2 (exact/quote-fold) both find zero matches and the excerpt
ends in a closing quote, try inserting one of `.`/`?`/`!` right before
it, accept only on exactly one resulting source location, always
recover the ORIGINAL source text. Consumer update narrowly scoped to
`cj2_b2_d0_prototype.py`'s D0-structural-gate call sites only (hash
`34f52ed9...`→`5810c80b...`) — **deliberately did NOT touch**
`cj2_b2_v2_probe.py`/`cj2_b2_probe_v1_4_1.py`'s R1/R2 auditor-evidence
checks (hardcode the old status string), staying inside the "no R1/R2"
boundary; flagged as a known future follow-up. **H15: `no_match` →
`terminal_punct_recovered`, recovering the exact original text with its
period; full gate replay confirms `should_call_r1: true` (D0 no longer
blocks), C0 never actually called.** **H06: unchanged, still
`no_match`** — the fix only ever touches one character position, never
interior text. **Full offline sweep: reconstructed the pre-change
algorithm and diffed it against the live one across every completed D0
corpus in the repo — 48 files, 1,123 spans, exactly 1 changed (H15),
zero other differences.** New `cj1_v3_anchor_resolver_static_tests.py`
(25 checks) plus all 14 existing project-wide static suites touching
D0/the resolver: all pass. Historical 14-item probe result unchanged
(H15 remains `span_resolution_failed` as recorded under the
then-frozen resolver) — this is a new resolver version for future
probes, not a retroactive rescoring. H06 recorded as a standing KNOWN
D0 EXACT-SPAN CONTRACT VIOLATION, permanent must-fail regression case;
no D0 prompt change. RL-2026-002 not inspected; RL-2026-003 untouched.
Full detail in the experiment doc's `## B2 ANCHOR RESOLVER
TERMINAL-PUNCTUATION RECOVERY` section.

**B2 ANCHOR RESOLVER V2 STATUS-PROPAGATION COMPATIBILITY PASS —
IMPLEMENTED, VERIFIED (2026-08-13, continuation after a context-limit
interruption), zero model calls, DECISION A.** Closes the follow-up the
entry above flagged: R1/R2's `validate_auditor_evidence` in
`cj2_b2_v2_probe.py` now calls the resolver's own `is_resolved_anchor`
instead of hardcoding `diag["status"] == "normalized_unique_match"`, so
a `terminal_punct_recovered` excerpt (H15's shape) is now accepted as
valid auditor-evidence provenance — previously it was not. The exact-
match fast path and every other function in the file (`validate_r1`,
`validate_r2`, `compute_consistency`, `compute_effective_v2`, repair-v1)
are untouched. `cj2_b2_d0_prototype.py`'s `_RESOLVED_SPAN_STATUSES` is
now `= RESOLVED_STATUSES` (imported, not duplicated) — behaviorally
inert on its own, pure provenance plumbing. This entry was written by a
fresh session after the implementing session hit its context limit;
every claim was re-verified directly against on-disk code and by
re-running tests, not recovered from the prior (visually garbled)
transcript. Full consumer audit found every other reference to
`resolve_anchor`/the status vocabulary already correctly classified:
historical/frozen files (`cj2_b2_probe.py`, `_v1_2/_v1_3/_v1_4_1`,
`cj2_fresh_batch1_pipeline.py`) still hardcode the old status alone, as
intended; diagnostic-only call sites (`cj1_v3_probe.py`,
`cj1_v3_calibration_run.py`, `cj2_reference_probe.py`) never gated
validity on it either before or after. All 4 changed files compile/
import cleanly, no duplicate/stale patch fragments found. Resolver's own
static suite now 40 checks (up from 25) — H15 accepted via
`terminal_punct_recovered` through `validate_auditor_evidence` (labeled
explicitly as synthetic control-flow, not a real H15 R1/R2 result — H15
never reached R1/R2 in the original probe), H06 still rejected, all 3
accepted/3 rejected statuses + malformed/no-substring edge cases
directly tested. **All 14 project-wide static suites re-run: 14/14 pass.
No unintended behavioral delta** — D0's own acceptance surface unchanged
(same 3 statuses as the prior pass, just single-sourced); the only real
behavior change is R1/R2 newly accepting `terminal_punct_recovered`,
which is this pass's own intended propagation, not a side effect.
Classification: DETERMINISTIC PROVENANCE APPARATUS UPDATE, not a D0/R1/
R2 semantic revision, not B2 v2.1. No Stage C run, no RL-2026-002/003
inspection or change. Full detail, including exact hashes and the
complete consumer classification, in the experiment doc's `## B2 ANCHOR
RESOLVER V2 STATUS-PROPAGATION COMPATIBILITY PASS` section.

**FINAL EXPERIMENTAL FREEZE + HELD-OUT EVALUATION PROTOCOL — WRITTEN
(2026-08-13, same session), zero model calls, preregistration/governance
only.** Dedicated doc:
`.claude/experiments/final-evaluation-freeze-protocol-2026-08-13.md`.
Defines, before seeing RL-2026-002's outcome or any held-out result: the
semantic-freeze gate (human calibration → one consolidated B2 revision →
two stable dev regression probes → Stage-C exercised on ≥2 qualitatively
different natural admissions → freeze → fresh held-out corpus → held-out
eval → production-candidate review); a structural "done tuning" checklist
(no arbitrary percentage); the held-out contract (input/execution/scoring)
and predeclared failure handling per case (provider outage/apparatus
bug/schema-invalid/new failure class/unsafe admission/zero admissions) —
**with the explicit rule that any held-out set that causes a semantic
change is burned and cannot remain the final evaluation set**; the human-
calibration stop rule (contested results are a valid, sufficient outcome —
no consensus requirement); the Reader-Lab leakage rule (once spent, an
item is permanently development-classified, never reusable as blind
material); and fine-tuning's role as optional post-hoc optimization only.

**Metadata-only finding, no content read, verified exhaustively:** no
held-out corpus exists anywhere in this repo right now — every
`dataset_purpose` value on disk is `"development"`; every
`held_out_evaluation` code reference is a fail-closed guard that has never
fired; the "cross-publisher" protocol is preregistered, design-only, no
source collection done. It must be freshly collected after freeze, never
from already-spent development/Reader-Lab material.

**Shape C decision (using only existing development evidence, no new
round, no model calls): OPTIONAL / CAN REMAIN STRICT before freeze**, not
required. It's real (H01 2/2, H07 2/3 of their unsupported claims) but the
smallest of the three semantic families in the zero-safe bottleneck audit
(4/42 vs. Shape A's 12/42 and Shape E's 22/42), has no Reader Lab evidence
either way, and one historical data point (`cj2-stage-b2-v1.2`'s
modality-hardening tightening causing an unrelated clean-candidate
overcorrection) argues for caution, not urgency, in touching it. Revisit
only if its bottleneck share grows or held-out evidence forces the
question — not scheduled as a precondition for freeze.

RL-2026-002's partial answers were not inspected to write this document.
RL-2026-003 was not ingested or published. No D0/C0/R1/R2/repair-v1/
admission-gate/Stage-C code touched. No `v2.1`. No fine-tuning designed.

**BLUEPRINT / ROADMAP RECONCILIATION AUDIT — WRITTEN (2026-08-13, same
session), zero model calls.** Dedicated doc:
`.claude/master-roadmap-2026-08-13.md`. **Central finding: the live daily
production pipeline (`production_orchestrator.py`/`orchestrator/*.py` —
discovery, personas, generate, gate, fact_check, review, publish, social)
and the CJ-1/CJ-2/B2/Stage-C research track are two structurally separate
systems that have never been integrated** — zero real cross-imports
either direction (confirmed directly), only a shared low-level
`orchestrator.config` transport constant used by 3 CJ probe files. This
corrects an assumption in how the audit was framed: persona execution,
Fable editorial input, and article-level validation are NOT unbuilt — the
live pipeline already has all three (single-persona pick among 4 fixed
personas, a pre-write `_fable_editorial_brief`, and `gate.py`/
`fact_check.py`/`review.py`) and publishes real articles daily. What's
actually missing is the bridge from a CJ-2 Stage-C winner (a structured
angle/pitch object, not prose) to an actual article, plus article-level
validation for whatever that bridge would produce — neither exists in
any form, and neither is implied by B2/CJ-2 passing held-out evaluation.
No canonical single blueprint doc exists (`docs/DISCOVERY.md` is
self-flagged stale; `.claude/audience-engagement-tasklist.md` is
self-described as "a discussion draft, not an approved plan").

**Three finish lines, kept explicit per instruction, not collapsed into
one:** (1) B2/CJ-2 research finished = the freeze protocol's own
production-candidate gate, an isolated-mechanism milestone; (2) the full
article-generation system experimentally validated = **no protocol exists
for this yet** — requires the integration decision + bridge + a new
article-level validation layer, none scheduled; (3) CripMinds ready for
routine production use = **already true today**, for the live pipeline,
independent of any of this research — only "the CJ-2-validated version in
production" remains open, and has no target date since (2) has no
protocol yet.

**Two gaps named, not fixed:** Reader Lab's post-B2-freeze role (its
mechanism is explicitly designed for reuse per its own `## 19`, but
`final-evaluation-freeze-protocol-2026-08-13.md` never addresses this);
and CJ-2's relationship to the production tasklist's own separately-
deferred "judge-panel/multi-draft" item — both name the same kind of
problem (multiple competing candidates → pick a winner) with no document
ever stating whether CJ-2 is that item's answer, a superset, or unrelated.

Reconciled master roadmap: Phases A-F (research, matches the freeze
protocol exactly) -> Phase G (integration decision + bridge, unscheduled)
-> Phase H (article-level/full-pipeline validation, no protocol exists
yet) -> Phase I (productionization) -> Phase J (optional fine-tuning,
either track). RL-2026-002 not inspected. RL-2026-003 not touched. No
B2/Stage-C/production code changed. No product features implemented.

**PHASE G — CJ-2 ↔ PRODUCTION INTEGRATION DECISION MADE (2026-08-13, same
day, continuation), zero model calls, zero production/B2/Stage-C
changes.** Full addendum in `.claude/master-roadmap-2026-08-13.md`'s new
`## PHASE G ADDENDUM` section. **Target architecture: D** — CJ-2's Stage-C
winner becomes an alternate, optional upstream source for the EXISTING
`_fable_editorial_brief` step (already live, `llm.py`), via one new small
deterministic bridge function, with zero changes to every downstream
module (draft generation, `_fable_editorial_review` — already live and
distinct from the paused Phase 1.5B experiment —, `gate.py`,
`fact_check.py`, `publish.py`, `review.py`, `social.py`). Not "replace"
(A, too risky — the live pipeline has no candidate-selection layer to
replace, and CJ-2 has no persona-voice/prose-factuality mechanism of its
own to substitute for what would be lost) and not "stay parallel forever"
(C, wastes validated work) — a concrete refinement of "augment" (B).

**Bridge contract (field-level, verified against actual Stage-C/Stage-A/
CJ-1 schemas, not assumed):** only `angle` and `seed_sentence` need new
translation logic; `correction_moment`/`resisting_example` are near-direct
reuse of CJ-1's resolver-verified `source_anchors`/`resisting_detail`;
`register`/`opening_scene`/`opening_shape`/`cross_cite` correctly stay
production-owned. **Confirmed by direct code reading: nothing anywhere in
CJ-1/Stage-A/Stage-C produces headline/lede/angle-shaped text** — every
field is internal analytical language for a comparator, not a reader.
R1/R2 labels, conflict state, calibration labels, Stage-C's assessment
enums, and the anonymization letter-map are explicitly excluded from ever
crossing the bridge. `persona` (P/S/Z/M capsule label → one of the 4 live
personas) is only a probable, unconfirmed mapping — flagged to verify
before implementation, not assumed.

**Factuality authority resolved:** B2 = pre-draft factual eligibility of
the winning idea; `fact_check.py`/`gate.py`/`_fable_editorial_review` =
post-draft factuality/fidelity of actual generated prose. Confirmed
complementary, not redundant — neither passing implies the other would.

**Judge-panel/multi-draft reconciliation (gap closed):** NOT a clean
supersession. The old deferred item (decided as "two full parallel
drafts, SAME persona, judged") addresses same-persona angle diversity;
CJ-2 addresses cross-persona competitive selection — different axes, both
independently buildable, neither resolved by the other.

**Reader Lab post-freeze role (gap closed):** confirmed PERMANENT REUSABLE
CALIBRATION INFRASTRUCTURE for the mechanism (reviewer/round/policy/
analysis), while B2-specific rounds end at freeze — never mandatory
per-article approval.

**Failure/fallback:** every CJ-1/B2/Stage-C failure mode (nothing found,
everything blocked, zero entrants, mechanical failure, infra down) falls
back to the existing live pipeline unchanged — explicitly not a downgrade
from a CJ-2-secured baseline, since that's the status quo the site has
run on all along. Real risk named: a silently invisible CJ-2 contribution
rate could erode without anyone noticing; mitigation is a per-article path
marker, flagged for whenever the bridge is built, not built now.

**Rollout, sequenced, none executed:** shadow mode → comparison mode →
CJ-2-sourced drafts (unpublished) → editorial pilot → production
authority.

No implementation. No production/B2/Stage-C/CJ-2 code touched. RL-2026-002
not inspected. RL-2026-003 not touched.

**PHASE G.1 — WINNER BRIDGE + ROLLOUT CONTRACT FROZEN (2026-08-13, same
day, continuation), zero model calls, zero implementation.** Full contract
in `.claude/master-roadmap-2026-08-13.md`'s `## PHASE G.1` section.

**P/S/Z/M resolved by direct code read, not guessed:** the frozen
`CAPSULES` dict (`cj2_reference_probe.py:46-72`) defines P/S/Z/M purely as
4 analytical instruments (mediation/timing; actor-environment; measurement/
classification; promise-vs-practice) — zero persona-name references
anywhere in it, by design (round-2 anonymization, confirmed correctly
implemented). The design doc states an intended P=Pixel Nova/S=Siri
Sage/Z=Zen Circuit/M=Maya Flux correspondence "internally, in the
orchestrator" — but an exhaustive grep found **that mapping implemented
nowhere in any actual code.** Documented intent, not a wired fact. **This
doesn't block the bridge**, because of the next finding.

**Corrects a Phase-G assumption, verified by reading `_fable_editorial_brief`
in full (`llm.py:686-924`):** `persona` is a formal parameter
(`current_agent`) but is confirmed UNUSED inside the function body — Fable
makes its own free persona pick from all 4 personas every time, regardless
of what's passed in. **Persona selection is already, today, entirely
Fable's own responsibility, independent of any winner's origin** — the
bridge carries no `persona_id` at all, more strongly than Phase G's
already-correct "Stage C is not a persona-writing stage" conclusion.

**`angle`/`seed_sentence` translation risk sharpened, not just flagged:**
`angle` must be phrased as a genuinely unpredictable open question ("BRIEF
A QUESTION, NOT A VERDICT" is the prompt's own strongest instruction) —
CJ-2's `claimed_contribution`/`conceptual_shift` are the opposite shape, a
completed verdict-like judgment. A naive deterministic rename risks
reintroducing the exact pre-Phase-1.6 failure mode (essays as delivery
mechanisms for a pre-held conclusion). Recorded as needing its own small
validation check before trust, per this pass's own instruction not to hide
semantic generation inside a "deterministic" bridge. `seed_sentence` is
lower-risk, closer to CJ-1's own `resisting_detail`/anchors.

**New hard constraint found, not in Phase G:** `generate.py` builds
exactly ONE `evidence_packet` per run and fail-closed discards any brief
whose stamped `source_hash`/`evidence_packet_hash` don't match it exactly
(`generate.py:274,299-309`). A bridge-produced brief must be validated via
the same `grounding.validate_brief()` call against THAT SAME object — it
cannot carry independently-stamped provenance from CJ-1's own separate
source fetch. Practical implication: CJ-1's own source-fetch should
eventually share the same fetched `source_text` as `discovery.py`/
`generate.py`, or most bridge attempts will legitimately fail closed on
hash mismatch (correct behavior, but a real prerequisite for any pilot
past shadow mode).

**Bridge v1 schema (`cj2_winner_bridge_v1`) frozen**: only `angle` (flagged)
and `seed_sentence` (deterministic default) need real composition;
`correction_moment`/`resisting_example` are near-direct reuse of CJ-1's
already-verified anchors; `register`/`opening_scene`/`opening_shape`/
`cross_cite`/`persona` stay production-owned exactly as today. R1/R2
labels, `problems`, conflict state, B2 internals, Stage-C's assessment
enums, and the anonymization letter-map are explicitly barred from ever
entering the object.

**Fallback-by-stage defined** (shadow/comparison: fully unaffected;
pilot: no auto-published substitute; production authority: silent
old-pipeline fallback explicitly REJECTED as a default — recommended
combination is retry-then-visible-fallback-marker, human exception
reserved not routine). **Zero-entrant policy**: B2 is never weakened to
manufacture volume, at any stage.

**Cost/latency estimate**: live path already ~6-10 model calls per
article with no CJ-2 involved; adding CJ-1→Stage C roughly doubles-to-triples
total call volume (14-26 added calls worst case), concentrated upstream.
Every existing CJ-2 probe script runs sequentially (research harness, not
production-latency-tuned) — parallel execution flagged as a real
prerequisite for any pilot, not assumed to already exist.

**Reader Lab post-freeze role and the judge-panel/old-roadmap-item
relationship**: both restated exactly as Phase G already concluded, now
formalized in a second location for consistency — no new decision, no new
scheduling.

No implementation. No production/B2/Stage-C/CJ-2 code touched. RL-2026-002
not inspected. RL-2026-003 not touched.

**PHASE G.1.1 — BRIDGE SEMANTIC-OWNERSHIP CORRECTION (2026-08-13, same
day, continuation), zero model calls, zero code changes. Supersedes the
`cj2_winner_bridge_v1` schema logged above, not just refines it.** Found
the exact error: `## G.1.4`'s bridge schema targeted
`_fable_editorial_brief`'s OUTPUT shape (`angle`/`seed_sentence`/
`correction_moment`/`resisting_example`/`persona`/etc. are all fields
Fable *produces*, confirmed none are function parameters) — which is
precisely how a "deterministic" bridge conceals a real editorial decision.
**Fix: the bridge instead feeds Fable's actual, unchanged 5 input
parameters** (`news_title`, `news_summary`, `disability_angle`,
`current_agent`, `evidence_packet`) with CJ-2-derived material, then
Fable runs its own single existing model call exactly as it does for a
live-sourced story — zero new model calls, zero function-signature
changes. `angle`/`seed_sentence`/`correction_moment`/`resisting_example`
are removed from the bridge entirely, not left null — all confirmed
Fable-owned, unconditionally. CJ-1's `resisting_detail`/`open_question`
now slots into the EXISTING `disability_angle` "inspiration only" input
(same functional role the live pipeline's own `news_seed.disability_angle`
already plays), giving the winning candidate's specific insight a real,
non-binding chance to steer Fable's own composition — this is how the
fidelity question (does the winning insight survive?) is addressed
without smuggling in a precomposed field. Evidence-packet invariant and
persona non-requirement both reconfirmed unchanged. **Decision: A —
deterministic bridge contract now closed**, using the current input
contract as-is; one optional future enhancement flagged (a dedicated
"suggested evidence candidate" input parameter for tighter anchor
fidelity) but explicitly not required to close this contract. Full
correction in `.claude/master-roadmap-2026-08-13.md`'s new
`## PHASE G.1.1` section, with `## G.1.4` marked superseded in place, not
deleted. No implementation. No `_fable_editorial_brief` edit. RL-2026-002
not inspected. RL-2026-003 not touched. No new roadmap audit started.

**PHASE G.2 — SHADOW INTEGRATION IMPLEMENTATION (2026-08-13, same day),
first actual code pass in the Phase-G sequence.** New:
`automation/cj2_winner_bridge.py` (`cj2_winner_bridge_v1`, pure, matches
G.1.1's schema exactly — no `angle`/`seed_sentence`/`correction_moment`/
`resisting_example`/`persona` field exists in it at all; fail-closed
evidence-packet-hash invariant enforced in code; denylist scan +
raw-Stage-C-letter rejection); `automation/orchestrator/cj2_shadow.py`
(`CJ2ShadowMixin`, `_cj2_shadow_attempt`, OFF-by-default via
`CJ2_INTEGRATION_MODE` env var, persists to a new `cj2_shadow_runs` table
in the existing `engagement.db`, never touches `self._degraded_stages`'
real blocking policy). Small hook added to `generate.py` (3 lines, after
the existing fable_brief block) and `CJ2ShadowMixin` wired into
`ProductionOrchestrator`'s bases — nothing else in production code
touched. **53 tests across 2 new suites, all pass**, including the
load-bearing one: a successful SHADOW-mode bridge produces a
byte-identical writer prompt to OFF mode — proven by running the real,
unmodified `_run_production_automation_locked()` via the existing
`snapshot_test.py` harness, not argued from code reading. **Zero
regressions** on all 5 pre-existing generate.py-adjacent test suites
(`snapshot_test.py --check` included, exact-value diff against 6 real
published articles). No live CJ-1..Stage-C orchestration exists yet, so
SHADOW mode in real production would only ever record `NO_CJ2_WINNER`
today — this pass is plumbing, not a live shadow run. **Committed
locally, NOT pushed to `origin/main`** — genuinely inert by default
(proven, not assumed) but this is a live daily-publishing pipeline this
session can't integration-test against real secrets/DB/cron; pushing left
as Jascha's own deliberate decision. No B2/CJ-1/CJ-2/Stage-C/Fable-prompt/
gate/fact_check semantic change anywhere. RL-2026-002 not inspected.
RL-2026-003 not touched. Phase H not started. Full detail in
`.claude/master-roadmap-2026-08-13.md`'s new `## PHASE G.2` section.

**ORIGINAL A-M BLUEPRINT RECONCILIATION (2026-08-13, same day), zero model
calls, zero implementation.** Dedicated doc:
`.claude/original-blueprint-A-M-reconciliation-2026-08-13.md`. **Central,
load-bearing finding, not buried: exhaustive git archaeology (every
distinctive phrase from the request, every `.claude/*.md` file ever added
across 1,320 commits) found no literal historical A-M article-quality
blueprint document anywhere in this repo.** A different, real, smaller
lettered scheme exists (anchor-architecture Stages 0/A-E, `review.py`,
governing one narrow plan-following/seam-detection mechanism) and is not
this. Treated the request's own 13 described concerns as a working list
and answered each directly against live code instead of fabricating a
recovered document. **Confirmed live gaps, all independent of B2/CJ-2/
RL-2026-002:** G (repetition — no general mechanism anywhere), H (review
coverage — `review.py`'s `_engagement_read` truncates to `content[:6000]`,
confirmed), I (`gate.py`'s `_parse_rule_verdicts` — a rule truncated out of
the LLM's raw output is silently absent, never contributes a FAIL,
confirmed). J (STOP-risk/reader-drop-off) confirmed never built anywhere
in code, not abandoned. E (length) is split: selection is genuinely DONE
BUT EVOLVED (old 2200-word bucket removed, deliberate weighted pool) but
the dominant "essay" type has no deterministic length-adherence check. K
(why-we-write doctrine) is DONE, live in `llm.py`, and — though no explicit
written link exists anywhere — is substantively a direct ancestor of
CJ-1's own friction-gate rationale. **No original article-quality problem
is actually solved by CJ-2/B2/Stage-C** — CJ-2 has never produced an
article, only candidate-selection language. **Roadmap decision: C — run
G/H/I fixes in parallel with the existing Phase G/H sequence**, since none
of them gate on or are gated by B2's freeze/RL-2026-002/the CJ-2 bridge.
Commit `128fda8` reconfirmed unmodified and unpushed (`[origin/main: ahead
1]`) at the end of this pass.

**LIVE PIPELINE INTEGRITY PASS — I/H FIXED, G SHADOW-INSTRUMENTED
(2026-08-14, real implementation), commit `204c3bc`.** Full detail in
`.claude/master-roadmap-2026-08-13.md`'s new `## LIVE PIPELINE INTEGRITY
PASS` section and `.claude/original-blueprint-A-M-reconciliation-2026-08-13.md`
(updated in place, not rewritten). **I: DONE** — `gate.py`'s R1-R17 check
and `review.py`'s own independent R1-R19 check both gained
`check_truncation=True` (reusing `llm.py`'s existing mechanism) plus a new
`_missing_rule_ids` completeness check; a silently-omitted rule now behaves
exactly like the pre-existing `gate_llm` exception path, never reads as
clean. **H: DONE** — `_engagement_read` now receives the whole article
(was `content[:6000]`, no technical reason found for the limit — verified
`gate.py`/`review.py`'s other two LLM calls already send full content,
only this one truncated). **G: SHADOW-INSTRUMENTED, not promoted** — new
deterministic `_check_repetition_shadow` (paragraph-pair content-word
Jaccard overlap), wired exactly like this file's existing shadow checks,
verified zero blocking authority; no promotion before 2026-08-28, same
discipline as every sibling shadow check. **Bonus fix**: a pre-existing,
unrelated `snapshot_test.py` mock-signature bug was silently swallowing
real test coverage of `review.py`'s persona-cross-cite check since
whenever it started using `check_truncation=True` — found and fixed
(same bug class this project already fixed once before for a different
mock), fixtures re-recorded and reverify verified clean via direct
before/after reproduction. **M re-checked**: originally-named blind spot
closed; a second, pre-existing, different gap found and reported, not
fixed — `generate.py`'s `_should_block` threshold means a sole `gate_llm`
degradation still doesn't force a block on its own, an open policy
question. 87 checks across 6 suites (4 new), zero regressions. One
combined commit made (not two, per an explicit, documented reasoning —
H and G turned out finely interleaved in the same file alongside a
shared snapshot fixture that can't be correctly split between two
commits). Commit `128fda8` (Phase G.2) reconfirmed unmodified, unamended,
unpushed — `[origin/main: ahead 2]`. No B2/CJ-2/Reader-Lab/Fable-prompt
semantic change. RL-2026-002 not inspected, RL-2026-003 not touched.

## ROADMAP / ACTIVE PHASE
Order changed 2026-08-10 evening after the Phase 1.5B planning-brief audit
below promoted grounding ahead of Phase 2 — do not reorder again without a
stated reason.

- **DONE** — Phase 0 (reliability + canonical baseline).
- **DONE** — Phase 1, WHY WE WRITE → **KEEP**, scope-corrected. Full
  record: `.claude/experiments/why-we-write-2026-08-10.md`.
- **DONE** — Phase 1.5A, Persona Architecture Audit (design/audit only,
  no code changes, no generations) → `.claude/persona-architecture-audit.md`.
- **PAUSED, not concluded** — Phase 1.5B, Fable review-seat ROI. Full
  record: `.claude/experiments/fable-review-roi-2026-08-10.md`.
- **DONE** — Phase 1.6, source-grounding hardening. DONE, not perfect —
  see `## PHASE 1.6 — DONE` below for the verdict and known limitations;
  full implementation/control history archived to
  `.claude/experiments/phase-1.6-source-grounding-2026-08-11.md`. Do not
  reopen by drift; only touch this code again if the regression suite
  fails or a real new grounding seam is found live.
- **IN PROGRESS, DESIGN ONLY** — persona-selection/routing architecture,
  scoped into two stages: CJ-1 (source friction gate) → CJ-2 (four-
  persona contribution competition).
  **CJ-1 FROZEN** as `cj1-v3.2-validity-before-recall` — research-
  calibrated candidate / CJ-2 input contract, NOT YET a production
  eligibility gate. Full history (v2 audit → v3/v3.1/v3.2 → temperature
  isolation → Fresh Calibration Batch 1, 10/10 PASS outputs manually
  judged grounded, 2/2 NO outputs showed no obvious missed friction, 0
  observed unsupported-relation/framing-only/unsupported-anchor
  failures — NOT an independently labeled benchmark, NOT a production
  pass-rate estimate) in
  `.claude/experiments/cj1-v3-friction-gate-2026-08-11.md`. Three
  implementation issues parked (not solved): smart-quote exact-anchor
  resolver wiring, `resisting_detail` occasionally citing real material
  outside `source_anchors`, source completeness/authoritative-NO still
  unresolved — none block CJ-2.
  **CJ-2 architecture designed (research-only, no prompts/code/calls)**
  in `.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md`,
  **corrected 2026-08-11 (4 fixes, same day)** after review:
  (1) evidence/inference boundary corrected — CJ-1 anchors are the
  mandatory shared SEED friction only; CJ-2 may add its own
  `source_observations` beyond CJ-1's anchors, but EVERY additional
  factual premise needs its own exact grounding (CJ-1 passing does NOT
  blanket-authorize new facts a persona introduces downstream);
  (2) the self-reported `new_factual_claims` disqualifier was removed
  (a validator can't reliably detect a fabricated fact hidden in free
  prose) and replaced by structurally forcing every factual premise
  through `source_observations` — explicitly logged that semantic
  factual-laundering (two real facts → an unsupported causal claim)
  remains a human/comparator concern determinism can't solve;
  (3) the 4-blind-calls topology is now labeled RESEARCH REFERENCE
  architecture only, not a production-topology decision — a cheaper
  "one call, four isolated passes" variant is flagged to A/B test
  LATER, once the reference run establishes what correct behavior
  looks like; (4) no-distinctive-contribution behavior is now FROZEN,
  not left open: `editorial_winner: null`, skip/backlog, never fall
  back to the hard router or let rotation manufacture a winner — plus
  a new balance/rotation rule (clear CJ-2 winner → balance can't
  override; close margin → balance may tiebreak; no winner → balance
  can't manufacture one), a real behavior change flagged for whenever
  `_balance_agent` (`discovery.py:87`) is next touched. The 4 engine
  capsules are now drafted (checked against
  `persona-architecture-audit.md`'s per-persona matrix, not just
  accepted as proposed) — still candidate text, not a frozen prompt;
  the actual Stage A/C system prompts still need composing around them.
  `discovery.py`'s `_THEME_TO_PERSONA` dict and `generate.py`'s
  domain-keyword chain (~line 203) hard-route topics independent of
  `personas.py`, confirmed by direct trace — matters only as a fallback,
  to be replaced by CJ-2 per the audit's own plan
  (`.claude/persona-architecture-audit.md` lines 339-364). Separately,
  `news_fetcher.py`'s `disability_angle` eligibility gate remains the
  deeper upstream problem, unaffected by CJ-1/CJ-2 work so far.

  **SECOND CJ-2 CORRECTION ROUND (2026-08-11, same day), 5 fixes before
  any prompt drafting:** (1) Stage C now receives `source_snapshot`
  itself — it was previously asked to catch semantic factual
  laundering ("A caused B" smuggled from co-occurrence) from candidate
  prose alone, which isn't architecturally possible; (2) CJ-1 anchors
  are now referenced by stable ID (`cj1:a1`/`a2`/`a3`) instead of
  retyped into each candidate's evidence field — avoids the known
  smart-quote transcription failure recurring 4x per story on evidence
  already canonicalized once; added explicit `abstain` invariants;
  (3) Stage A capsules are now fully ANONYMOUS — `Engine P/S/Z/M`,
  mapped to Pixel/Siri/Zen/Maya only inside the orchestrator, never in
  the prompt the model sees, with all disability vocabulary (Deafness,
  blindness, autism, ramp/curb-cut) removed from the capsule text
  itself (round 1's failure-mode lines had reintroduced exactly what
  the blind design was supposed to keep out) — changes the research
  question from "can it roleplay four identities" to "do four
  instruments produce different knowledge"; (4) Pixel/Zen/Maya
  capsules generalized (Pixel: instrument only, no pre-installed
  "politics of legibility" conclusion; Zen: works on any
  object/system, not just people; Maya: promise-vs-operation, not
  promise-vs-body) — Siri deliberately left as-is so the probe
  discovers, rather than presumes, how portable her more literally
  spatial engine is; (5) Stage A input narrowed further — CJ-1's
  `open_question` AND `ostensible_category` both excluded (not just
  `disability_angle`), so CJ-1 shows the friction without also telling
  all four engines what question to investigate; Stage C is now fully
  affinity-blind (round 1 still allowed affinity as a close-margin
  tiebreaker inside the comparator — removed entirely from the
  gold-reference run). Full detail in the experiment doc's "second
  correction round" summary.

  **THIRD CJ-2 CORRECTION ROUND (2026-08-11, same day), 5 more fixes:**
  (1) `friction_type` removed from BOTH Stage A and Stage C model
  input — the biggest confound caught yet: `measurement_discrepancy`
  quietly advantages Engine Z, `transformation` advantages P,
  `dependency` advantages M, before any engine looks at the source;
  kept audit-only, never shown to either model; (2) added
  `seed_engagement` as an audit field — citing one `cj1:aN` anchor
  doesn't prove a reframe actually transformed the shared friction vs.
  citing it then pivoting elsewhere; Stage C checks this independently;
  (3) Stage A's `removed_engine_test` is now advisory only — Stage C
  produces its OWN independent `candidate_assessments[letter]`
  (factual_integrity, seed_engagement, engine_dependence,
  conceptual_movement, distinctive_contribution, assessment) for every
  surviving candidate before any winner is picked — Phase 1.6's
  evidence-gets-checked-not-trusted lesson now applied to genericness
  claims too; `disqualified`/`disqualify_reason` removed from Stage
  A's own model schema (Stage B owns that via a
  `provenance_validation` wrapper, not the model self-reporting it);
  (4) the `Candidate A/B/C/D` permutation is now FROZEN — a fresh
  anonymization layer (not reusing `Engine P/S/Z/M`), seeded
  reproducibly from `source_sha256`, computed outside the prompt;
  TITLE removed entirely from both stages (round 2's "metadata, not
  evidence" compromise retracted — CJ-1's own Wired case already
  showed a model can lean on a channel even when told not to treat it
  as authority); (5) Engine S rewritten to drop its own pre-installed
  destination ("whose comfort the design assumed"); Engine P/M failure
  lines retightened to stop naming a fallback topic (exclusion;
  infrastructure) the wording itself was priming; Engine Z unchanged.
  Full detail in the experiment doc's "third correction round"
  summary.

  **FOURTH CJ-2 CORRECTION ROUND (2026-08-11, same day), schema-only
  cleanup, 4 fixes — architecture itself no longer reopened:** (1)
  `persona_inference` renamed `interpretive_inference` — "persona" had
  no business in a schema built to test anonymous instruments; (2)
  `claimed_contribution` reinstated (round 3 had folded `contribution`
  away, losing a genuinely distinct signal) — Stage A claims it, Stage
  C independently judges `distinctive_contribution`; (3)
  `removed_engine_test` now persisted for Stage A research/audit ONLY
  — a new Stage C-view projection strips it from Stage C's actual
  payload, closing the gap where Stage C's "independent"
  `engine_dependence` judgment could otherwise be read straight off the
  candidate's own self-assessment; (4) Stage C's qualification rule is
  now a FROZEN hard gate (`does_not_qualify` if ANY of
  `factual_integrity=fail`/`seed_engagement=none`/
  `engine_dependence=generic`/`conceptual_movement=none`/
  `distinctive_contribution=none`; `strong`/`partial` only compares
  already-qualifying candidates, never grants eligibility) — closes the
  gap where a comparator could score everything poorly and still
  rationalize a winner; orchestration edge cases frozen (0 valid
  candidates → no Stage C call at all; exactly 1 → still independently
  assessed, never an automatic win). Full detail in the experiment
  doc's "fourth correction round" summary. **Architecture and schema
  now considered stable — four correction rounds is the stopping
  point.**

  **PROMPTS COMPOSED AND FROZEN (2026-08-11, same day): `cj2-stage-a-v1`
  / `cj2-stage-c-v1`.** Two rounds of prompt-level (not architecture)
  review: initial draft, then 5 corrections (invalid-JSON-in-examples
  fixed; Stage C's evidence/inference wording corrected so it no
  longer reads as "the source must support the interpretation," which
  would have contradicted the whole point of CJ-2; Stage C's
  independence from `engine_move`/`seed_engagement`/
  `claimed_contribution` made explicit — assess `engine_dependence`
  from the capsule + `interpretive_inference` + `conceptual_shift` +
  evidence, never from the candidate's own claim; a literal "Do
  inflate" → "Do NOT inflate" typo fixed; `additional_source_observations`
  capped at 0-2 items so one engine can't out-excavate the others; a
  primary (`distinctive_contribution`+`engine_dependence`)/secondary
  (`conceptual_movement`+`seed_engagement`) ranking rule added for the
  2+-qualifiers case, with `factual_integrity` explicitly pass/fail
  only, never extra credit). Ran a static preflight (no LLM calls) —
  banned terms, excluded CJ-1 fields, TITLE absence, `removed_engine_test`
  absence from Stage C, `abstain_reason` presence, all JSON examples
  actually parsing, Stage A engine-neutrality — all PASS after fixing
  two false positives in the preflight script itself (a naive substring
  check flagged "persona" inside "personally"; another failed on a
  soft line-wrap that reads fine as prose). Both full prompt strings +
  user-input templates persisted verbatim in the experiment doc's
  `## PROMPTS FROZEN` section. Call conditions decided: `temperature=0.0`
  for both stages for the first reference probe — randomness is an
  unwanted fifth variable in an experiment isolating one.

  **FIRST REFERENCE PROBE RUN (2026-08-11, same day).** Harness bug
  fixed first (an `or True` made a TITLE-absence check vacuous; fixed,
  equivalent Stage C check added, re-ran clean — did not unfreeze
  either prompt). 3 sources (`01_cave_dna`, `05_dutch_painting_soldier`,
  `07_ai_cheating_exam` — already-frozen CJ-1 Batch-1 PASS fixtures,
  no refetch/rerun, no pre-registered expected winner), canonical
  `cj1:aN` evidence rebuilt from ORIGINAL source substrings (never the
  model's smart-quote-mutated version). 12 Stage A + 3 Stage C calls,
  `openrouter/claude-sonnet-4.6`, `temperature=0.0`, neither frozen
  prompt touched. **Result: 12/12 Stage A schema-valid, 11/12
  Stage-B-valid** (1 excluded on a NEW transport-technicality class —
  `PROVENANCE_TRANSPORT_CONFOUNDED`, a real accurately-quoted fact
  excluded only because the model collapsed a paragraph break while
  quoting it, distinct from the known apostrophe issue), **2/3 Stage C
  outputs usable** (1 was a harness extraction bug — valid JSON
  misreported as unparseable, recovered; 1 is genuinely, unrecoverably
  truncated — the model prefixed unrequested prose before the JSON in
  2/3 calls despite "no other text," consuming enough of the token
  budget that one run never completed). Grounding held: zero smuggled
  facts found in any of the 11 Stage-B-valid candidates on direct
  re-check against source text (one apparent alarm, "a campus
  shooting," verified as a real quoted source fact, not a
  fabrication). Zero abstentions across all 12 calls (flagged as
  inconclusive at n=3, not celebrated). Convergence finding, the most
  important one: all 12 readings share the same ABSTRACT SHAPE
  ("an apparent certainty is produced by an unexamined mechanism") but
  target four consistently DIFFERENT specific mechanisms across all
  three unrelated domains (P→transmission/format, S→environment/
  relational-field, Z→measurement/proxy-validity, M→unenforced
  operational condition) without seeing each other's output or being
  told the domain. Full mechanical integrity report, cross-source
  comparison table, and 8-question qualitative analysis (differentiation
  through convergence) in the experiment doc's `## FIRST REFERENCE
  PROBE` sections. Two experiment-only repo scripts added
  (`cj2_build_canonical_seed.py`, `cj2_reference_probe.py`),
  uncommitted — no production pipeline code changed.

  **CORRECTION (2026-08-11, same day): the "zero smuggled facts"
  conclusion above is RETRACTED.** An offline semantic factuality
  audit (no new model calls) of all 12 Stage A candidates against
  their complete source texts found the probe's **first real observed
  CJ-2 safety failure: `SEMANTIC_FACT_LAUNDERING`** — a candidate
  starts from a real, correctly-quoted fact, then strengthens it via
  modality/causality/mechanism/population claims into something the
  source doesn't establish, while citing only real excerpts (so
  Stage B's exact-substring check can't catch it). 6 of 12 candidates
  are fully clean (all 4 De Hooch candidates) — the other 6 show it,
  worst in Cave DNA's Engine S (invented that carbonate deposition
  "erases the maker's biological signature" — the source never
  connects dating to biological-signature erasure at all) and 3 of AI
  Exam's 4 engines (S: "reluctant to return" hardened into "couldn't
  enter"/"adapting not cheating"; M: dropouts framed as causally
  "load-bearing for enrollment," which the source never establishes).
  **Stage C caught 0 of ~6 instances** across both available runs,
  despite being explicitly designed to enforce "conceptual inference
  may go beyond the source; factual assertion may not." Corrected
  judgment: the engines show real differentiation, but CJ-2 v1 hasn't
  yet demonstrated it can tell a bold interpretation from a
  strengthened factual premise — that's the open problem now, not
  convergence. Per explicit instruction, Stage A/capsules are NOT
  implicated and remain untouched; Stage C is diagnosed, not yet
  revised. Harness issues (JSON extraction, token budget/preamble,
  whitespace-transport resolver gap, missing De Hooch result) logged
  separately, deliberately not mixed into the semantic finding. Full
  per-candidate audit table in the experiment doc's `## OFFLINE
  SEMANTIC FACTUALITY AUDIT` section.

  **CORRECTION + ARCHITECTURE CHANGE (2026-08-11, same day).**
  "Stage A/capsules not implicated" was too strong — corrected to a
  two-part diagnosis: Stage A GENERATES the intensification (that's
  where every laundered claim originates; Engine S/M's
  mechanism/dependency-naming instructions may carry more risk than
  P/Z's limit-finding instructions, logged as an n=3 hypothesis, not
  acted on), Stage C FAILS TO DETECT it. Designed (not drafted) a new
  research stage, **Stage B2 — SEMANTIC FACTUALITY GATE** — inserted
  between Stage B and Stage C: one candidate at a time, ENGINE-BLIND
  (no capsule, no label, no other candidates, no
  `removed_engine_test`) — because letting the auditor see the engine
  invites exactly the "well, that's a reasonable reading for this
  lens" rationalization that let Stage C's failure through. Corrected
  proposition taxonomy from 3 confused roles to 2 clean ones:
  `INTERPRETIVE_ONLY` (may exceed the source, no support needed) vs.
  `FACTUAL_DEPENDENCY` (needs source support; `SOURCE_ESTABLISHED` is
  just a supported factual dependency, not a separate category — the
  original 3-way split couldn't say which label wins when a claim is
  both). Uncertainty handling reuses CJ-1 v3.2's own precedent:
  unclear interpretive-vs-factual → lean interpretive (avoid
  `FALSE_UNSAFE`, which would destroy CJ-2 as surely as the opposite
  error); unclear whether a confirmed factual claim is supported →
  lean unsupported. Stage C's schema simplifies once factual safety is
  upstream — drops `factual_integrity`, hard gate shrinks from 5
  dimensions to 4, resolving the two-conflicting-jobs problem instead
  of just tightening the same combined instruction. The 12 existing
  candidates are now an explicit development/regression set (post-hoc
  labels, not independent ground truth) — B2's first real test will
  be measuring BOTH `FALSE_SAFE` (fabrication slips through) and
  `FALSE_UNSAFE` (legitimate interpretation wrongly rejected) against
  them. A sharper hypothesis than "De Hooch had denser quotes" logged
  but not acted on: risk may track evidentiary AFFORDANCE (thin/
  underdetermined source mechanism → engine manufactures connective
  tissue) rather than quotation density as such — explicitly not fed
  back into CJ-1. Full design in the experiment doc's `## STAGE B2`
  section.

  **B2 ROUND 2 CORRECTIONS (2026-08-11, same day), before any prompt
  drafting:** (1) audit scope widened — B2 must check ALL claim-
  bearing fields (`additional_source_observations[].observation`,
  `engine_move`, `seed_engagement`, `interpretive_inference`,
  `conceptual_shift`, `claimed_contribution`), not just what the core
  inference logically needs — the actual AI-Exam-S failure originated
  inside an `observation` field the narrower scope would have missed
  entirely; added `importance` (load_bearing/supporting/incidental) as
  diagnostic-only, since even an incidental unsupported claim still
  reaches Stage C and can sway it; (2) new axis `declaration`
  (declared/undeclared/not_applicable) separate from `support` — a
  fact Stage A should have routed through `additional_source_observations`
  but didn't, which B2 then finds elsewhere in the source, must NOT be
  silently rescued as "safe" (new problem type
  `UNDECLARED_FACTUAL_DEPENDENCY`) — otherwise Stage A's declaration
  contract becomes optional whenever B2 can find the forgotten fact;
  (3) retracted "uncertain → lean interpretive" as an escape hatch —
  every laundering case found in the audit already sounds interpretive
  on first read, so that default sat exactly where the failure hides;
  added a real third role `boundary_ambiguous` and a 3-valued verdict
  `safe|unsafe|ambiguous` (ambiguous is withheld from Stage C AND
  tracked separately, not merged into either bucket, since it's
  exactly the calibration signal an untested gate needs); (4) B2's own
  `auditor_evidence` citations get a post-B2 deterministic provenance
  check, same discipline as Stage B — B2 finding supporting text
  doesn't fix a `declaration=undeclared` violation, and an unverifiable
  B2 citation reverts that claim to `uncertain`, not to a rescued
  "supported." Orchestration edge cases and the development-set error
  measurement both updated for the 3-valued verdict. Full detail in the
  experiment doc's `## STAGE B2` corrections.

  **B2 ROUND 3 (FINAL SCHEMA CLEANUP, 2026-08-11, same day) before
  prompt drafting:** (1) `verdict` removed from the model-facing
  output entirely — B2 now returns `{"claims": [...]}` only; the
  orchestrator (not the model) computes `effective_verdict` from a
  provenance check + a field/invariant check + the claims list — same
  authority separation as Stage A→Stage B, applied one level deeper;
  (2) `boundary_ambiguous` given real structural invariants
  (`support=uncertain`, `declaration=uncertain`, both forced, since
  the auditor can't judge declaration before it's even resolved
  whether a claim is factual) — `declaration` gained a 4th value,
  `uncertain`; legal role/support/declaration combinations are now
  exhaustive and anything else is a schema violation, not coerced into
  shape; (3) `problem` (singular) → `problems` (list) — a claim can
  violate more than one axis at once (e.g. modality-hardening AND
  undeclared in the same proposition), and a singular enum was forcing
  the auditor to discard information; (4) the post-B2 provenance check
  now WRAPS instead of mutating — an unverifiable `auditor_evidence`
  citation no longer silently rewrites `support=supported` into
  `support=uncertain`; both the original claim and the validation
  result are preserved as siblings, and the orchestrator derives a
  third outcome (`effective_status="unresolved"`) that preserves "B2
  made a confident judgment from evidence that didn't check out" as
  its own recorded finding rather than erasing it; (5) `resisting_detail`
  frozen as context-only, never factual authority for B2 — only
  `source_snapshot`, canonical `cj1:aN`, and declared `obs:N` excerpts
  establish facts; added `source_field` to every claim (which of the
  6 candidate fields it came from) specifically so a future decision
  about whether Stage A itself needs a targeted fix can be based on
  WHERE laundering concentrates, not just that it occurs. Full final
  schema, structural invariants, and the 3-step post-B2 pipeline
  (auditor-evidence check → field/invariant check → orchestrator
  effective-verdict computation) in the experiment doc's `## CORRECTION
  (round 3)` section.

  **B2 ROUND 4 (2026-08-11, same day) — the real remaining hole plus
  three cleanups, before prompt drafting:** (1) **field coverage
  manifest added** — the actual missing safety invariant. `claims[]`
  alone can't distinguish "I inspected this field and found nothing
  factual" from "I never looked at this field" — no string check can
  catch a proposition the auditor silently never extracted. Added
  `field_audits[]`: the orchestrator (which built the candidate, so it
  already knows every claim-bearing field instance that exists)
  requires B2 to account for each one explicitly, including an
  explicit `no_auditable_propositions=true` for a field with nothing
  to flag — doesn't prove semantic completeness, but makes omission
  structurally visible instead of invisible; (2) **fixed a real bug**:
  round 3's verdict rule accidentally routed an unverifiable
  `auditor_evidence` citation into `UNSAFE` — corrected to
  `audit_unresolved` → `AMBIGUOUS`, since a failed audit is not
  evidence the candidate's claim was false, only that the audit didn't
  establish safety; (3) added a run-status layer
  (`valid|schema_invalid|call_failed`) ABOVE the semantic verdict — a
  malformed or failed B2 call now produces `effective_verdict:
  "not_computed"` and is withheld from Stage C on its own, never
  coerced into "unsafe" or "ambiguous" as if it were a finding about
  the candidate; (4) `support=supported` now requires at least one
  `supports_claim` citation that survives provenance validation
  (previously structurally optional — a supported claim with zero
  evidence was legal); applied the same requirement symmetrically to
  `unsupported`. Verified directly (not just asserted) that the
  canonical schema block itself contains no duplicate keys, no
  singular `problem`, and no model-facing `verdict` — the actual
  contamination turned out to be confined to the already-labeled
  historical round-2 example, not the canonical block, but a single
  unambiguous `B2_MODEL_OUTPUT_V1` block was written anyway per
  explicit request. Full schema, coverage/structural invariants, and
  the 3-layer post-B2 pipeline in the experiment doc's `## CORRECTION
  (round 4)` section. Still no B2 prompt, no `cj2-stage-c-v2`, no code,
  no API calls, no Stage A/capsule/CJ-1 changes. Schema/invariant work
  on B2 is now considered done — next real step is drafting B2's
  actual system prompt and testing it against the frozen development
  set for `FALSE_SAFE`, `FALSE_UNSAFE`, `ambiguous` rate/content, AND
  `schema_invalid`/`call_failed` rate.

  **CURRENT POINTER: `cj2-stage-b2-v1.4.1` REGRESSION RUN EXECUTED --
RESULT: FAIL (2026-08-12).** Accepted for execution per explicit
instruction; prompt/matrix/validators/schema/resolver/harness/Stage
A-B-C left untouched before and during the run. Ran the same 30-
candidate corpus (12 dev + 18 fresh-batch-1) as the v1.3 regression,
same model/temperature/max_tokens/timeout/input-construction/
validators/resolver/run_status logic -- only the v1.4.1 prompt swapped.
Built a machine-readable transcription of the frozen claim-level matrix
(SHA256 `fdabba24...`) before the first call, per instruction. Executed
on trident (CLIProxyAPI localhost-only) in an isolated scratch, all 25
inputs and both output sets hash-verified byte-identical before/after,
scratch removed. **30/30 valid, 0 schema_invalid, 0 call_failed** --
better than v1.3's 29/1, but this did not translate into a claim-level
win. **PRIMARY SCORING: 2 PASS / 5 FAIL of 7 targets.** H08 still
`interpretive_only` (unchanged). H17 still `interpretive_only`
(unchanged) but by a NEW mechanism -- diagnostic confirmed it is no
longer hedge-driven (v1.3's specific bug, fixed) but now bypasses the
MANDATORY CONCRETE RESTATEMENT step via an unfixed "conceptual
reframing" shortcut, the same failure family reasserting through a
different route. **H09 target claim REGRESSED** to `interpretive_only`
(was correctly `factual_dependency` under v1.3, just schema-blocked);
run is now schema-valid, but the candidate's `unsafe` verdict comes
only from an unrelated claim -- doesn't count as a repair, per the
scoring rule's own anticipated failure mode. **H14 and De Hooch/Z --
both previously fixed under v1.3 -- REGRESSED** back to
`interpretive_only` on all 4 target claims combined; De Hooch/Z's
candidate verdict reverted `unsafe` -> `safe`. H05 and H03 controls
held (PASS). Diagnostic contrast, same run: H05/c11's own reasoning
explicitly performs the concrete restatement by name and correctly
lands on `factual_dependency`/`unsupported` -- proof the procedure
works when invoked, and is being selectively skipped on the failing
targets, not universally broken. **Global guards (v1.2 baseline,
unchanged thresholds): both PASS mechanically** (aggregate: interpretive_
only ROSE +5.2pp/factual_dependency FELL -4.8pp -- wrong direction for
the cap to catch; flip-rate 0.86%, well under 20%) -- neither gate is
built to catch a swing AWAY from factual_dependency, which is exactly
what happened; a diagnostic-only reverse-flip measure (not a new gate)
found >=4.52% of v1.2's factual_dependency claims flipped back to
interpretive_only, and 7 of 8 v1.3->v1.4.1 candidate-verdict
transitions moved toward `safe`. **ACCEPTANCE STATUS: FAIL** -- "broad
regression toward interpretive_only via an unfixed conceptual-reframing
bypass of the mandatory concrete-restatement step; 5 of 7 targets fail,
including 2 that were already fixed and are now broken." Applied
mechanically, no invented partial-pass category. Artifacts hashed:
`acceptance-matrix-v1.json` (`fdabba24...`), `b2-v1.4.1-regression-
comparison.json` (`b47bbf06...`), `b2-v1.4.1-regression-report.md`
(`4f72a12a...`). `cj2-stage-b2-v1.2`/`v1.3` outputs, and the still-
genuinely-never-executed `cj2-stage-b2-v1.4` prompt, all preserved
unchanged. Full result in the experiment doc's `##
cj2-stage-b2-v1.4.1 REGRESSION RUN -- COMPLETE, RESULT: FAIL` section.
**`cj2-stage-b2-v1.4.1` NOT modified in response to this result. No
v1.4.2/v1.5 designed. No cross-publisher batch. No Stage C. No tuning
from individual failures. Stopping here, per instruction. CURRENT
POINTER is now: cj2-stage-b2-v1.4.1 is EXECUTED and FAILED its
preregistered gate -- next real decision (not made this pass) is
whether to design a v1.4.2 targeting the conceptual-reframing/STEP-2-
bypass mechanism specifically, or reconsider whether a prompt-only fix
is sufficient at all.**

  **(HISTORICAL, superseded by the entry above) `cj2-stage-b2-v1.4.1`,
FROZEN, NOT EXECUTED (2026-08-12).** `cj2-stage-b2-v1.4` (designed from
the diagnostic below,
SHA256 `c817af5a...`) was frozen but never executed — no API call was
ever made against it. A pre-execution audit (not a post-run tuning
pass, since there was no run) found two problems before it would have
been reasonable to spend a 30-candidate regression on it: (1) v1.4's
STEP 3 hedge rule overstated in the OPPOSITE direction from the H17
bug it fixed — its own worked example ("The rule may encode an
assumption that X" -> "Classify it factual_dependency") treated an
ambiguous, hedged, conceptually-phrased sentence as flatly factual
from the hedge/verb alone, the mirror-image shortcut to the one that
caused H17's miss; (2) v1.4's regression acceptance criteria (e.g.
"H08 must no longer be interpretive_only") didn't pin down what it
must become instead — a reclassification to `boundary_ambiguous`
would satisfy the literal wording without being a real repair, given
the diagnostic already establishes H08's target claim is an
unambiguous miss, not a genuine boundary case. Re-verified v1.4's
hash before touching anything (matched); re-read the full file
directly (not the earlier pasted terminal output, which looked
visually malformed) and confirmed it's clean -- no duplication, no
contradiction between STEP 3 and the older `HEDGES DO NOT IMMUNIZE A
CLAIM` section. `cj2-stage-b2-v1.4` is preserved unchanged at its own
path -- status corrected to FROZEN / UNEXECUTED / SUPERSEDED
PRE-EXECUTION BY v1.4.1, not "failed" (it never ran). Created
`cj2-stage-b2-v1.4.1` (SHA256 `b67630dc...`): a 4-lines-removed/
8-lines-added, single-location prompt-only delta rewriting STEP 3 to
the symmetric rule -- hedge words decide neither role (Steps 1-2, the
world-truth test and concrete restatement, decide role; the hedge only
scales the strength required of whatever support that role needs) --
with a worked example that correctly stays factual_dependency despite
a hedge ("The committee may have believed X") and one that correctly
stays interpretive_only despite a hedge ("One way to read the rule is
as a picture of X"). No schema/enum/validator/resolver/Stage A/B/C
change. Static preflight 45/45 PASS (run programmatically against the
actual file, not asserted) -- old absolute header/example confirmed
gone, new symmetric language confirmed present, all 22 carried-forward
section headers present, no fixture wording leaked, no duplicated
paragraphs, all JSON examples parse. Built an exact claim-level
regression acceptance matrix from the frozen diagnostic/regression
JSON artifacts directly (not memory) for H03/H05/H08/H09/H14/H17/
`05_dutch_painting_soldier`/Z -- exact claim text, expected role/
support/problems, and (for H08/H17) explicit "does NOT count as
repaired if it becomes `boundary_ambiguous`" language, plus (for H09)
"does NOT count as repaired unless the run is also schema-valid."
Global anti-overcorrection guards (<=15pp aggregate cap, <=20%
flip-rate cap, v1.2 baseline) carried forward UNCHANGED, not retuned.
Full audit, delta, hashes, preflight, and the complete matrix in the
experiment doc's `## PRE-EXECUTION AUDIT + PROMPT FROZEN:
cj2-stage-b2-v1.4.1` and `## EXACT CLAIM-LEVEL REGRESSION ACCEPTANCE
MATRIX` sections. **No API calls made. No new source collection. No
Stage C. Stopping here, before execution, per instruction.**

  **STATUS CORRECTED to FAIL + TARGETED FAILURE-MECHANISM DIAGNOSTIC
  (2026-08-12) — the preregistered gate is a fail, not a partial pass;
  root-caused each failure precisely.** Corrected: a binary
  preregistered criterion (all 5 misses repaired) doesn't become
  "partial pass" because some sub-parts succeeded.
  **`cj2-stage-b2-v1.3` REGRESSION STATUS: FAIL — PARTIAL IMPROVEMENT.**
  Criterion 1: FAIL (H05/H14 fixed, H09 claim-level fixed but run
  schema_invalid so doesn't count as a repair, H08/H17 still missed).
  Criteria 2/3: PASS (unchanged). **Direct consequence: v1.3 is NOT
  eligible for the cross-publisher batch.** Ran the targeted diagnostic
  the user specified, covering H08/H09/H17/De Hooch-Z plus H05/H14 as
  controls: **(A) H08** — the target proposition was extracted as its
  own atomic claim in both v1.2 and v1.3 (rules out decomposition
  loss); v1.3's own reasoning never invokes the new CONCRETE
  RESTATEMENT TEST at all, despite the claim being a near-exact match
  for that section's own worked example — **`role_classification_failure`,
  rule bypassed not failed**. **(B) H09 vs H17 controlled contrast**
  (same source): H09's wording is a flat, unhedged, exactly-quantified
  assertion ("specifically five years' worth"); H17's wording contains
  a self-qualifying hedge inside the claim itself ("an ASSUMED...
  pattern (e.g., childbearing)"), and v1.3's own reasoning explicitly
  treats that internal hedge as exempting the whole claim — the
  pre-existing HEDGES DO NOT IMMUNIZE A CLAIM rule (unchanged since
  v1.1) did NOT override this. The rule v1.3 is actually applying
  looks like "if the candidate's own wording flags something as
  illustrative, treat the whole claim as interpretive" — the opposite
  of both the old and new rules' own instructions. **(C) H09's
  schema_invalid**: root-caused to a DIFFERENT claim (c7) missing a
  required semantic-problem tag alongside `undeclared_factual_dependency`
  — classified `malformed_claim_object`; whether it's related to the
  v1.3 prompt delta or ordinary temperature-0 stochasticity is
  **explicitly recorded as uncertain**, not guessed at; not re-run.
  **(D) De Hooch/Z**: audited the exact original candidate wording
  ("De Hooch's moralism functioned through..." — flatly asserted, not
  hedged) — genuinely `factual_dependency`/`unsupported` (requires de
  Hooch's actual historical intent, which the source never states),
  not `boundary_ambiguous`; flagged that attributing "design mechanism"
  to an individual historical artist sits at an edge of the new
  section's institutional/systemic scope, not resolved. **(E)
  controls**: H05/H14 both match the new section's own worked examples
  closely AND use flat, unhedged wording — but critically, **H08 also
  matches a worked example nearly word-for-word and still wasn't
  caught**, so matching an example is not sufficient; presence/absence
  of a self-qualifying hedge in the candidate's own wording looks like
  the more likely actual driver. Produced and hashed
  `b2-v1.3-failure-mechanism-diagnostic-v1.json` (SHA256
  `28dcaef5...`). No prompt wording proposed for v1.4. Full diagnostic
  in the experiment doc's `## STATUS CORRECTION` and `## TARGETED
  v1.3 FAILURE-MECHANISM DIAGNOSTIC` sections. **v1.3 not modified. No
  v1.4. No cross-publisher batch. No Stage C.**

  **`cj2-stage-b2-v1.3` REGRESSION RUN EXECUTED — RESULT: PARTIAL PASS
  (2026-08-12).** Closed both preregistration gaps first, as
  clarifications not results-driven: role-migration criterion made
  exact (≤15pp aggregate cap AND ≤20% flip-rate cap, both mechanically
  decidable); `publisher_key` frozen as `row["source_name"]` (already
  present verbatim in the frozen stream, no domain-parsing needed).
  Ran v1.3 against the full 30-candidate corpus (12 dev + 18 fresh),
  same conditions as every prior B2 run, v1.2 outputs preserved
  untouched. **30/30 run, 29 valid / 1 schema_invalid (H09), 0
  call_failed.** 6/30 verdicts changed — each individually inspected at
  the claim level, not accepted on the verdict alone. **Criterion 1
  (fix the 5 misses): PARTIAL — 2/5 confirmed fixed (H05, H14), 1/5
  fixed at the claim level but the run itself is schema_invalid from
  an unrelated compliance slip on a different claim (H09), 2/5 still
  missed (H08, H17)** — the correction didn't generalize consistently
  even within its own target subtype, and never touched the modality/
  certainty-hardening case at all. **Criterion 2 (H03 stays caught):
  PASS.** **Criterion 3 (role migration): PASS on both — aggregate
  interpretive_only% actually ROSE 1.1pp (wrong direction for
  overcorrection), flip-rate was 1.72% against a 20% cap — no blanket
  collapse.** **Criterion 4**: 2 new unsafe findings on the dev set
  individually inspected — De Hooch/M is a strong, well-grounded catch
  (same speculative-motive pattern already adjudicated once before);
  De Hooch/Z is genuinely closer to the anti-overcorrection boundary
  (attributes "moral signal" as artist intent, closer to ordinary art
  criticism than a clear world-claim) — flagged as debatable, not
  resolved. **One new safe verdict (H16) also inspected**: same claim
  text both runs, v1.3 simply found a second, genuinely better
  citation v1.2 missed — a real improvement, not a regression.
  Produced and hashed `b2-v1.3-regression-comparison.json` (SHA256
  `f9d7f093...`) and `b2-v1.3-regression-report.md` (SHA256
  `75f443c7...`). Full result in the experiment doc's `## cj2-stage-
  b2-v1.3 REGRESSION RUN — COMPLETE` section. **v1.3 NOT tuned
  further. No v1.4. No cross-publisher batch collected. No Stage C.**

  **`cj2-stage-b2-v1.3` DESIGNED (prompt-only), regression criteria +
  next cross-publisher protocol PREREGISTERED — NOT EXECUTED
  (2026-08-12).** Formalized the corrected diagnosis as the record's
  latest interpretation without erasing the original: pre-adjudication
  formal counts (9 caught/5 potential false-safe/1 potential
  false-unsafe/3 unscored) preserved and explicitly labeled
  pre-adjudication; the post-run adjudication is now the latest
  substantive read (5 confirmed misses, 0 confirmed false-unsafes
  among the six disagreements, H03=reference inconsistency not a
  boundary, H08 has exactly 1 genuinely `boundary_ambiguous` claim on
  re-audit). `CONCEPTUAL-SUBJECT FACTUALITY SHIELDING` marked
  explicitly PROVISIONAL (3 subtypes, one instance each, one
  publisher-cluster) — not a validated taxonomy. Designed
  `cj2-stage-b2-v1.3`: a PURE INSERTION into v1.2 (confirmed by diff —
  21 lines added, 0 removed/changed, one location) — no schema/enum/
  validator/resolver/Stage A/B/C change. New section: role is
  determined by propositional dependency ("what must actually be true
  in the world"), not by subject type — an institution/policy/rule/
  system CAN be a `factual_dependency`. Added a CONCRETE RESTATEMENT
  TEST with 4 generic patterns (policy-encodes-assumption,
  system-obligates, measurement-has-no-signal,
  feature-characteristic-across-population) covering all 3 observed
  subtypes without copying fresh-batch wording verbatim, plus an
  anti-overcorrection rule (metaphors stay interpretive when their
  force doesn't depend on an unstated empirical premise; declarative
  grammar alone isn't factual). SHA256 `8a5b279e...`. Static preflight
  109/109 PASS (all v1.1/v1.2 checks re-verified + new checks +
  explicit absence of fresh-batch-1 fixture wording — same discipline
  already applied to the development set). **Preregistered regression
  acceptance criteria** (5 rules: all 7 confirmed miss instances must
  stop resolving safe; H03 must stay caught; no broad
  interpretive→factual migration; every new unsafe verdict individually
  inspected; no further tuning without a new named version) — both the
  12-candidate dev set AND the 18 fresh-batch candidates are now
  explicitly development/regression material, no longer held-out.
  **Preregistered (design-only) the next cross-publisher sampling
  protocol** — same frozen-stream discipline as fresh-batch-1, plus a
  new max-1-accepted-source-per-publisher/domain rule and a 7th skip
  reason (`publisher_quota_reached`), explicitly stated as correcting
  the Nature feed-order clustering mechanism, not any publisher
  preference; legacy DB state still non-exclusionary. Full text/delta/
  preflight/criteria/protocol in the experiment doc's `## LATEST
  SUBSTANTIVE INTERPRETATION`, `## PROMPT FROZEN: cj2-stage-b2-v1.3`,
  `## REGRESSION ACCEPTANCE CRITERIA`, and `## NEXT EVALUATION BATCH —
  CROSS-PUBLISHER SAMPLING PROTOCOL` sections. **No v1.3 execution, no
  new source collection, no Stage C.**

  **DIAGNOSIS CORRECTED via post-run re-audit against frozen sources
  (2026-08-12) — the "one institutional-motive pattern" framing was
  too narrow AND too generous to the reference; both corrected, B2
  still NOT tuned.** Re-audited each of the 6 B2-vs-human-AI
  disagreements (H03/H05/H08/H09/H14/H17) directly against their
  frozen `source_snapshot`, independent of either side's framing.
  Found: only H05/H09/H17 are institutional-rationale/obligation-
  attribution misses; **H08 is modality/certainty-hardening** (source
  hedges "might not have existed"/"often could not"; candidate asserts
  "in fact" settled certainty); **H14 is scope/content generalization**
  (source: word appears in title/abstract of 3,700+ projects; candidate:
  word is "substantively load-bearing" across that whole population).
  Corrected failure class: **CONCEPTUAL-SUBJECT FACTUALITY SHIELDING**
  — B2 sometimes grants `interpretive_only` because of how a subject is
  phrased (institution/system/rule/scale) rather than what the
  proposition actually claims, regardless of which of the 7
  strengthening patterns applies; a fix aimed only at "institutions
  have motives too" would leave H08 and H14 uncaught. **Separately,
  H03 was wrongly used as "probable genuine boundary" evidence** —
  re-audited directly against `fresh02`'s (extremely thin, one-
  sentence) source: B2's `unsafe` verdict on H03 is independently
  confirmed CORRECT; the real explanation is
  `human-ai-assisted-adjudications-v1.json` being inconsistent across
  H03/H09/H17 on the identical source/proposition family — not a
  genuine interpretive/factual boundary. Created
  `post-run-disagreement-adjudications-v1.json` (SHA256
  `d6fcb1d5...`), `review_mode: post_run_model_assisted_diagnostic`,
  `independent_reference: false`, `b2_output_visible: true` — the
  original `human-ai-assisted-adjudications-v1.json` re-verified
  byte-identical, untouched. 5 confirmed B2 misses (7 claim instances),
  1 claim downgraded to `boundary_ambiguous` on re-audit (H08/c5), H03
  reclassified as reference-inconsistency not a B2 error. Full
  per-claim rationale, grounded in the actual source text, in the
  experiment doc's `## CORRECTION: THE "ONE INSTITUTIONAL-MOTIVE
  PATTERN" INTERPRETATION IS SUPERSEDED` section (original,
  now-superseded text preserved verbatim above it, not deleted).
  `cj2-stage-b2-v1.2` still not edited. No v1.3 designed. No Stage C.

  **METHODOLOGY CORRECTION + EXPLORATORY B2-vs-HUMAN-AI COMPARISON RUN
  (2026-08-11, same day) — 5 potential false-safes, 1 potential
  false-unsafe, both patterns specific and reported, B2 NOT tuned.**
  Corrected provenance: the 18 filled labels were produced through an
  interactive MODEL-ASSISTED review (Jascha judged, a model helped
  interpret/formulate) — NOT independent human ground truth. Copied
  into the repo as `human-ai-assisted-adjudications-v1.json` (SHA256
  `cd6a95b0...`) with corrected `_metadata`
  (`review_mode: human_ai_assisted`, `independent_human_reference:
  false`) — labels/violations/notes byte-identical to source, only
  metadata authored. 14 `factuality_contract_violation` / 3
  `ambiguous_boundary` / 1 `clean`. Ran frozen, unedited
  `cj2-stage-b2-v1.2` against the same 18 candidates
  (`cj2_freshbatch1_b2_probe.py`, reusing `cj2_b2_probe_v1_2.py`'s
  logic unmodified) — 18/18 valid, 0 schema_invalid/call_failed, 11
  unsafe/7 safe/0 ambiguous. **9 caught, 5 potential false-safes, 1
  potential false-unsafe, 3 unscored.** The 5 false-safes are NOT
  scattered misses — all 5 share one precise pattern: an
  institutional/system-level motive-or-rationale claim ("panels were
  socially obligated to...", "the cutoff encodes an institutional
  assumption...") that B2 classifies `interpretive_only` every time,
  because v1.2's own MOTIVATION pattern and all its worked examples
  only cover individual/group human actors, never an institution/
  policy/rule "encoding" or being "obligated" to something — a real
  gap the development set never exercised. The 1 false-unsafe (H03)
  sits inside a three-way inconsistency with H09/H17 — same source,
  same underlying proposition family (5-year sex-differentiated
  cutoff as institutional assumption), where BOTH the human-AI labels
  and B2's own verdicts disagree with each other across the three
  readings — flagged as a probable genuine boundary case, not
  resolved. `cj2-stage-b2-v1.2` was NOT edited in response to any of
  this. Full comparison table and pattern analysis in the experiment
  doc's `## human-ai-assisted-adjudications-v1.json — METHODOLOGY
  CORRECTION` and `## EXPLORATORY FRESH GENERALIZATION COMPARISON`
  sections. Stopped before Stage C, per instruction.

  **`human-review-packet-v1.1.md` frozen (re-confirmed SHA256
  `9886afba...`), empty `human-review-labels-v1.json` skeleton created
  for H01-H18 (2026-08-11, same day) — no labels populated or
  suggested.** Skeleton: every entry `label`/`reviewer_note` null,
  `violations` `[]`; `_metadata` records `packet_version`,
  `packet_sha256`, `reviewer: "Jascha"`,
  `reference_created_before_b2: true`, `b2_output_seen_by_reviewer:
  false`, plus the schema (7 allowed `source_field` values including
  both `additional_source_observations[N].observation` indices, 3
  labels, 2 violation_types, 6 semantic_problem_types, and the rule
  that an `undeclared_factual_dependency`-only violation gets
  `semantic_problem_types: []`). Nature-cluster scope note reconfirmed
  as persisted, unchanged. Full record in the experiment doc's `##
  human-review-packet-v1.1.md — FROZEN` and `## human-review-labels-v1.json
  — EMPTY SKELETON CREATED` sections. No B2, no candidate commentary,
  no suggested labels.

  **HUMAN-PACKET-ONLY CORRECTIONS: v1.1, plus a Nature-cluster scope
  note (2026-08-11, same day) — walk/CJ-1/Stage-A/Stage-B untouched,
  still no labels/B2/Stage C.** `human-review-packet-v1.md` marked
  `STATUS: SUPERSEDED BEFORE HUMAN LABELING` (kept, not deleted — 0
  labels ever produced from it). Built `human-review-packet-v1.1.md`
  reusing the v1 builder's `collect_surviving()`/`assign_hidden_ids()`
  UNMODIFIED — verified all 18 candidates' content byte-identical to
  v1 except two new metadata lines per block
  (`source_truncated`/`source_length_chars`, copied mechanically from
  the frozen fixtures). Four packet-only corrections: (1)
  source-snapshot authority reframed as "the exact frozen text
  available, may be truncated/paywall-limited — only this is factual
  authority, no web search, no outside knowledge"; (2) blinding claim
  corrected from an unqualified "engine-blind" to precise: engine
  label/capsule/persona/hidden-mapping withheld, but candidate
  reasoning prose (the audit target) and repeated source snapshots are
  NOT hidden and may make the instrument/shared-source inferable —
  explicit instruction not to use that inference when judging
  factuality; (3) added explicit "interpretive wrappers don't shield
  facts" + a 7-check support-strengthening list (same one in
  `cj2-stage-b2-v1.2`'s own prompt) directly into the packet, and
  restated support-vs-declaration as two questions that must never
  collapse; (4) `ambiguous_boundary` now requires a real, specific
  `reviewer_note` (source_field + exact proposition + why it's
  unresolvable) — empty/generic notes explicitly disallowed. Verified
  zero leaked persona names/engine labels/slugs in v1.1 (SHA256
  `9886afba...`). **Separately recorded a scope note before any human
  label exists**: all 6 accepted sources are nature.com — verified,
  not assumed. This is a mechanical artifact of `fetch_all_feeds()`'s
  own return order (Nature's feed is first in `QUALITY_FEEDS`), not a
  discretionary selection — batch is NOT discarded or resampled.
  Interpretation rule frozen: zero confirmed false-safes passes this
  fresh Nature-CLUSTER safety probe specifically, does not by itself
  establish cross-publisher generalization; a separate cross-publisher
  probe is required before Stage-C/production advancement — not
  designed or started this turn. Full detail in the experiment doc's
  `## human-review-packet-v1.md — STATUS: SUPERSEDED`, `##
  human-review-packet-v1.1.md — PACKET-ONLY CORRECTIONS`, and `##
  SCOPE NOTE` sections.

  **CORRECTED WALK COMPLETE, ENGINE-BLIND HUMAN-REVIEW PACKET BUILT,
  STOPPED FOR HUMAN LABELING (2026-08-11, same day).** Re-ran
  `cj2_fresh_batch1_pipeline.py` (fixed) from `stream_index=1` against
  the SAME `blind-stream-v2.json` (hash re-verified before and after).
  Walked 14 rows, accepted exactly 6 (`stream_index` 1/3/9/12/13/14 →
  fresh01-fresh06), then stopped. Skip counts: `shape_exclusion`=1,
  `cj1_no`=7 (all clean decision=NO, zero "PASS but not resolver-
  recoverable" this time), 0 each for the other 4 reasons. **The fix
  mattered empirically**: 3 of 6 accepted sources (fresh03/05/06) were
  `resolver_recovered` — real, grounded PASSes that only failed strict
  validation on curly-quote transcription; under the old defective
  gate these would have been wrongly rejected, half the batch. 24
  Stage-A candidates total, 0 abstentions, 6 Stage-B exclusions (all
  transport-confound-shaped, same pre-existing frozen Stage-B logic,
  not a new defect) → **18 surviving candidates**. Built the
  engine-blind packet (`human-review-packet-v1.md`, SHA256
  `f5880424...`) with a separate hidden `H0N`→(slug,engine) mapping
  (`human-review-hidden-mapping-v1.json`, SHA256 `8175cb90...`) —
  verified zero leaked P/S/Z/M/capsule/persona/disability_angle content,
  grouping well-scrambled. Recorded a harness-hardening note per
  instruction (not acted on): `compute_effective_cj1_eligibility()`
  currently fails OPEN (returns eligible=True) if `validation` is ever
  `None` or has `valid=False` with zero violations — not a live bug
  this run, but should fail closed before reuse elsewhere. **Stopped
  here — no B2 call, no labeling by Claude, no second-model check.**
  Full walk/packet detail in the experiment doc's `## CORRECTED WALK —
  COMPLETE`, `## ENGINE-BLIND HUMAN-REVIEW PACKET`, and `## HARNESS-
  HARDENING NOTE` sections. Waiting for human-supplied labels.

  **`blind-stream-v2.json` CAPTURED (1061 items, SHA256 `19963578...`),
  FIRST WALK KILLED MID-RUN AND INVALIDATED — real harness defect, not
  a CJ-1 issue (2026-08-11, same day).** Executed the capture
  (`fetch_all_feeds(days=7)`, zero DB/scoring interaction) and started
  the walk; caught mid-run (2 sources already accepted) that the
  accept/reject gate used `decision=="PASS" and strict_valid` only,
  dropping CJ-1 v3.2's own already-calibrated resolver-recovery
  contract (a curly/straight-quote-only anchor mismatch should recover
  via `normalized_unique_match` and use the resolved original
  substring, per Fresh Calibration Batch 1's own precedent) — meaning
  a real grounded PASS could get silently rejected as `cj1_no` for a
  transcription artifact, corrupting which sources enter the "frozen"
  sample. Killed the process immediately, preserved its 2 accepted
  sources' outputs untouched at
  `automation/.probe_fixtures/cj2-fresh-batch-1-INVALIDATED-walk1/`
  (not deleted). Fixed the harness (`compute_effective_cj1_eligibility()`
  in `cj2_fresh_batch1_pipeline.py`) to implement the existing contract
  exactly — CJ-1 itself untouched, no whitespace/dash/fuzzy/semantic
  matching added. Ran the required 6-case deterministic preflight
  (exact_match/normalized_unique_match/no_match/ambiguous_match/
  out_of_scope/decision=NO) plus 1 extra (non-anchor violation must
  never be resolver-rescued) — all 7 pass, no API calls. Confirmed
  local/remote `blind-stream-v2.json` hashes still match. Restarting
  the walk from `stream_index=1` against the SAME frozen stream — no
  refetch. Full defect/fix/preflight record in the experiment doc's
  `## blind-stream-v2.json — CAPTURED AND FROZEN` and `## FIRST WALK —
  INVALIDATED BEFORE COMPLETION` sections.

  **FRESH-BATCH PROTOCOL, FOURTH/FIFTH CORRECTIONS (2026-08-11, same
  day) — removed a selection bias I'd just reintroduced, moved
  content filtering to walk-time, softened the human-completeness
  claim, pre-registered disagreement handling. Still zero network
  calls, zero source selection.** My own third-correction design had
  proposed excluding any URL already `disability_angle`-touched or
  `used=1` in the live DB (`legacy_conditioned_duplicate`) — caught as
  wrong: a story's odds of having those states IS a function of the
  legacy pipeline, so excluding on that basis biases the sample away
  from whatever legacy selection favored, reintroducing the exact
  conditioning being removed. **Fixed: legacy DB state can never
  affect inclusion, in either direction** — only `prior_fixture` and
  `confirmed_already_published` (deterministic URL provenance) remain
  as historical exclusions; legacy state may only be attached as
  post-hoc audit metadata after everything is already frozen. Also
  fixed: `BLOCKED_TITLE_PATTERNS`/title-dedup were being applied
  *before* freezing the stream, meaning the "raw" capture already
  reflected a content-based membership decision — moved both to
  walk-time as explicit skip reasons (`shape_exclusion`,
  `capture_duplicate`), with the rationale corrected from "these
  shapes have no friction potential" (false — an obituary can contain
  real friction) to "eligibility rule inherited from the discovery
  pipeline, not an epistemic claim." Six final allowed skip reasons:
  prior_fixture / confirmed_already_published / shape_exclusion /
  capture_duplicate / fetch_failed / cj1_no. Softened "itemize EVERY
  problematic proposition" to "violation on at least one identified
  proposition, itemize what's found, not claimed exhaustive" — matches
  B2's own candidate-gate framing instead of turning the reviewer into
  an exhaustive auditor. Pre-registered disagreement handling before
  it can happen again: HUMAN clean + B2 unsafe always counts as a
  formal fresh false-unsafe under the frozen manifest, PLUS a separate
  non-mutating adjudication record inspecting the specific proposition
  — same pattern as the De Hooch/P case, now frozen in advance instead
  of improvised after. Full corrected construction, skip-reason
  definitions, and disagreement rule in the experiment doc's `###
  cj2-fresh-batch-1/blind-stream-v2.json — construction, corrected` and
  `## FRESH EVALUATION SEMANTICS` sections. Still no `fetch_all_feeds()`
  call, no source selected, no CJ-1/Stage-A/B2 calls.

  **FRESH-BATCH PROTOCOL, THIRD CORRECTION (2026-08-11, same day) —
  `used=0` was NOT neutral; blind-stream-v1 superseded before any
  source was walked; human-label contract fixed to match B2's real
  safety boundary. Still zero sources selected, zero CJ-1/Stage-A/B2
  calls.** The second correction's `blind-stream-v1.json` (859 rows,
  SHA256 `2c07756e...`) got built and hashed, but before walking it:
  `used=0` turned out to be the OUTCOME of production's own
  disability_angle/relevance-based daily selection (`get_news_seed`
  picks 1/day, preferring `disability_angle`-having rows), not an
  independent population — dropping the `disability_angle` column from
  the query never removed that indirect conditioning. Marked
  `blind-stream-v1.json` `STATUS: SUPERSEDED BEFORE SOURCE WALK` (kept,
  not deleted/rewritten — 0 sources ever selected from it). Traced
  `news_fetcher.py`'s real pipeline (`main()` lines 1187-1245) and
  found a SECOND, earlier conditioning point nobody had caught yet:
  `score_item()` is itself CripMinds' own disability/editorial-theme
  relevance scorer (`THEME_WEIGHTS` upweights architecture/history/
  space/indigenous/philosophy, downweights health/labor;
  `POLICY_PROCESS_EXCLUDE` zeroes welfare/DWP/PIP stories by name;
  `MIN_SCORE=0.15` applied on this score before a row is even stored)
  — any `news_seeds`-sourced population, any WHERE clause, was already
  filtered by a milder version of the exact thing this experiment
  needs to sit upstream of. Found the real structural boundary:
  `fetch_all_feeds()` is a standalone, side-effect-free function (pure
  RSS pull, zero DB, zero scoring) that can be reused unmodified to
  build a genuinely pre-angle, pre-scoring population — no production
  code change needed. Designed (not executed) `blind-stream-v2.json`:
  `fetch_all_feeds()` → only the content-*shape* filter
  (`BLOCKED_TITLE_PATTERNS` — obituaries/promo-spam, verified
  disability-neutral by reading its pattern list) → in-run title dedup
  only → `stream_index` assigned in feed-return order → freeze/hash →
  only afterward, a read-only live-DB cross-check flags any URL that
  already has `disability_angle` set or `used=1` elsewhere as a new
  5th skip reason, `legacy_conditioned_duplicate`. Also corrected
  published-exclusion completeness: only 83/140 `_posts/` have
  `source_url` frontmatter; traced `publish.py`'s conditional write and
  checked `article_beats` (no url/seed_id column) — found no other
  recoverable provenance for the other 57, recorded as an honest,
  disclosed limit, not claimed as resolved. Built the fixture-derived
  exclusion set from artifacts directly (18 URLs across every CJ-1/CJ-2
  probe fixture directory). **Separately, fixed the human-label
  contract itself**: B2 marks a candidate unsafe for either an
  unsupported claim OR a source-supported-but-undeclared one — the old
  3-way label space (clean/semantic_fact_laundering/ambiguous_boundary)
  had no way to represent the second case without it registering as a
  fake false-unsafe (the same shape of gap already seen once with De
  Hooch/P). Replaced with clean/factuality_contract_violation/
  ambiguous_boundary, itemized `violation_types`
  (semantic_fact_laundering + undeclared_factual_dependency, can be
  both) + `semantic_problem_types`, and the review packet must now show
  declaration lineage (candidate's own `seed_evidence_refs`/`obs:N`)
  with support-vs-declaration spelled out as separate questions.
  Updated the evaluation semantics table to match. Full analysis in the
  experiment doc's `## blind-stream-v1.json — STATUS: SUPERSEDED`,
  the pipeline-boundary tracing, and `## HUMAN REFERENCE CONTRACT —
  CORRECTED` sections. **No discovery run, no source selected, no
  CJ-1/Stage-A/B2 calls.** Awaiting go-ahead on `fetch_all_feeds()`.

  **FRESH-BATCH PROTOCOL, SECOND CORRECTION (2026-08-11, same day) —
  ordering key/population/snapshot boundary now actually frozen,
  still no API calls, no DB query run.** The first correction (below)
  fixed the human-independence boundary, disability-routing, and
  evaluation semantics but left the selection query with a "whichever
  is the true arrival order" placeholder and no snapshot boundary.
  Resolved by reading `news_seeds`' schema/insertion code only (no
  title/content inspected): `id` is an MD5 hash of the URL
  (`url_id()`), not an arrival-order key; `fetched_date` is
  `%Y-%m-%d`-only (date, not timestamp), so same-day rows tie with no
  defined order; the table has no `WITHOUT ROWID`/`INTEGER PRIMARY
  KEY`, so SQLite's own hidden `rowid` is live and is the actual
  monotonic insertion-order column. **Froze `ORDER BY rowid ASC`** —
  overturning the earlier "id ASC is likely cleanest" guess, which the
  code proved wrong. Confirmed `used=0` means "not yet consumed as a
  real published-article seed" (via `mark_news_seed_used`/
  `get_news_seed`), froze it as the sampling population. Froze a
  snapshot-boundary procedure (record `selection_timestamp` +
  `SELECT MAX(rowid)` before walking, bound the query to
  `rowid <= snapshot_max_rowid`) so a live-table race can't let new
  rows sneak into the blind stream mid-walk. Froze the exact query,
  and a named frozen-stream artifact
  (`automation/.probe_fixtures/cj2-fresh-batch-1/blind-stream-v1.json`,
  hash recorded once written, before CJ-1 runs on anything). Dropped
  `disability_angle` from the selection artifact entirely (not just
  "unused as a filter") — it stays in the live DB; any correlation
  study happens only as a post-hoc analysis after this batch's results
  are frozen. Full resolved protocol in the experiment doc's `### 1.
  Source selection — corrected, second pass` subsection. **Still no
  sources selected, no SQL run, no snapshot taken.** Awaiting final
  go-ahead on Step 1.

  **FRESH-BATCH PROTOCOL CORRECTED (2026-08-11, same day) — three
  methodological holes fixed before Step 1, still no API calls.**
  Review caught: (1) "independent human factuality audit" cannot mean
  Claude labels the candidates itself, even before running B2 — that's
  a pre-B2 LLM reference audit, not independent evidence, and risks
  correlated error with B2 (also an LLM). Fixed: Claude's job now ends
  at constructing an ENGINE-BLIND HUMAN REVIEW PACKET (neutral IDs
  H01/H02/..., no P/S/Z/M, no capsule, no persona, no disability_angle,
  no B2 material — only source_snapshot/canonical evidence/candidate
  fields) and then STOPPING; a human (or an explicitly-labeled model,
  never called "human" if it isn't) supplies labels before B2 runs.
  (2) Source pool must sit upstream of `disability_angle` filtering —
  traced production's real `get_news_seed` query
  (`WHERE ... disability_angle IS NOT NULL`) and froze the corrected
  query against `news_seeds` WITHOUT that filter, `disability_angle`
  recorded but never used to include/exclude. (3) No pre-registered
  decision rule existed for the fresh batch — froze one now, before
  any result: false-safe/false-unsafe/clean-withheld/ambiguous-
  unscored semantics, proposition-level recall still diagnostic-only,
  primary rule (any confirmed fresh laundered candidate marked safe →
  do not advance B2, investigate mechanism, never prompt-tune against
  this set; zero false-safes → passed the safety axis, then check
  precision before deciding on Stage-C research). Batch size raised
  4→6 sources (~24 candidates) so one source can't dominate the
  result. Full corrected protocol in the experiment doc's `## FRESH
  GENERALIZATION BATCH — DESIGN ONLY, CORRECTED` section (supersedes
  the previous draft). No sources selected, no calls, no packet built
  yet — awaiting go-ahead on Step 1.

  **`cj2-stage-b2-v1.2` ADJUDICATED + FROZEN, fresh-batch protocol
  DESIGNED (2026-08-11, same day) — no further tuning, no API calls
  for the fresh batch yet.** Corrected the prior round's framing: the
  FORMAL pre-registered result stays FAIL (unchanged, `clean`-labeled
  `05_dutch_painting_soldier`/P received `unsafe`), but the
  substantive interpretation is `likely_human_annotation_defect`, not
  demonstrated B2 overcorrection — the source only offers the modesty
  motive as speculative, the candidate asserts it as operative, and
  v1.1 had already independently flagged this exact sentence
  `boundary_ambiguous` before v1.2 existed. Recorded BOTH conclusions
  side by side, per instruction, without editing the frozen original
  manifest (`b2-development-labels-v1.json`, re-verified byte-
  identical, SHA256 unchanged). New immutable overlay file created:
  `automation/.probe_fixtures/cj2-reference-probe-1/b2-development-adjudications-v1.json`
  (SHA256 `8d96db14...6f05`) holding the De Hooch/P case with
  `original_manifest_modified: false`. Methodological ruling recorded:
  AI Exam/S counts as operationally fixed because B2 is a candidate
  gate — one valid unsafe claim withholds the whole candidate from
  Stage C, so its 2 remaining proposition-level misses are diagnostic
  recall gaps, not safety failures; chasing 100% proposition agreement
  on this same 12-candidate set would be overfitting, not progress —
  explicitly ruled out. Transport conclusion frozen: prompt-level copy
  discipline did not fix citation transcription (the two worst v1.1
  failures recurred byte-identically); the deterministic
  audit_unresolved wrapper is what actually prevents wrong verdicts,
  and that's enough for now — structural transport redesign deferred
  until a future test shows material eligibility loss, not just
  correctly-handled ambiguity. **`cj2-stage-b2-v1.2` status set to
  `DEVELOPMENT-CALIBRATED CANDIDATE, FROZEN — NO FURTHER TUNING ON THE
  12-CANDIDATE DEVELOPMENT SET`** (deliberately not "validated" or
  "production-ready"). Designed (not executed) a fresh independent
  generalization-batch protocol with the order enforced as the actual
  safeguard: select sources (blind, before-fetch, excluding the
  existing 3 sources + cross-checked against `_posts/`) → freeze the
  set (CJ-1 PASS gate + canonical seeds, hashed) → run frozen
  `cj2-stage-a-v1` to generate new candidates → independent human
  factuality audit with NO B2 output visible (same 3-way label space,
  `ambiguous_boundary` preserved as a real category) → hash and freeze
  those labels → only THEN run frozen `cj2-stage-b2-v1.2` → compare.
  Proposed size: 4 new sources (~12-16 candidates), open to revision.
  Full adjudication reasoning, the freeze note, and the 6-step protocol
  are in the experiment doc's `## cj2-stage-b2-v1.2 — ADJUDICATION +
  FREEZE` and `## FRESH GENERALIZATION BATCH — DESIGN ONLY` sections.
  **No API calls made in this round. No sources selected yet — only
  the selection method is fixed.** No Stage C work, no production
  integration.

  **`cj2-stage-b2-v1.2` SECOND DEVELOPMENT-REGRESSION RUN (2026-08-11,
  same day) — DEVELOPMENT ACCEPTANCE FAILS (overcorrection).** Ran the
  frozen v1.2 prompt against the same 12 candidates (harness:
  `automation/cj2_b2_probe_v1_2.py`, verified byte-identical to the
  v1.1 script except the docstring and two path constants; all other
  inputs — manifest, Stage A JSONs, canonical seeds, resolver —
  hash-confirmed unchanged). **The target fix landed**:
  `07_ai_cheating_exam`/S flipped `safe`→`unsafe`, and the central known
  claim (source: "reluctant to return"; candidate: "aversive or
  inaccessible") is now correctly flagged `unsupported`/
  `modality_hardening`, explicitly rejecting the old "reasonable
  characterization" reasoning. Of its 4 known problematic instances: 2
  matched, 1 partial, 1 still missed (not a clean sweep — "adapting to
  the environment they were actually in" remains `interpretive_only`).
  **But `05_dutch_painting_soldier`/P (labeled `clean`) also flipped
  `ambiguous`→`unsafe`** — the same exact proposition v1.1 had already
  called `boundary_ambiguous` (a genuine motive-attribution question),
  now resolved decisively under the new stricter SUPPORT test. Per the
  rule pre-registered BEFORE this run: AI Exam/S fixed BUT a clean
  candidate went unsafe → **DEVELOPMENT ACCEPTANCE FAILS due to
  overcorrection** → stop prompt-tuning, do not write v1.3 reactively,
  do NOT silently move to a fresh batch. Logged
  `possible_new_human_audit_finding=true` for the De Hooch/P case as
  its own separate note (the original audit never specifically
  adjudicated that exact proposition) — explicitly NOT used to
  retroactively pass the criterion. Role-migration check came back
  clean: total claims 164→167 (~+2%), `interpretive_only`
  101→92/`factual_dependency` 59→74 (single-digit-point shift, not the
  101/59→45/130 blanket-distrust shape) — the correction is targeted,
  not wholesale. Auditor-evidence transport check: copy-discipline did
  NOT reduce failures (4→5) — the two original recurring failures
  (paragraph collapse, parenthetical elision) reproduced byte-
  identically despite being explicitly banned in the prompt; one
  original failure (quote-splice-across-attribution) didn't recur, two
  new subtypes appeared (quote-mark rewrapping, case alteration) — but
  all 5 still resolved correctly (`audit_unresolved`→ambiguous or
  rescued by a second valid citation), zero wrong verdicts, resolver
  untouched as instructed. Full candidate-level and proposition-level
  delta tables, the De Hooch/P and Cave-DNA/Z case analyses, and the
  transport comparison are in the experiment doc's `## cj2-stage-b2-v1.2
  — SECOND DEVELOPMENT-REGRESSION RUN` section. Stopped after the
  comparison report per instruction — no fresh batch, no Stage C
  changes, no v1.3.

  **`cj2-stage-b2-v1.1` STATUS: EXECUTED, `cj2-stage-b2-v1.2` FROZEN
  (2026-08-11, same day) — review of the development-regression run,
  two named prompt-level failure classes, prompt-only fix, no API
  calls yet.** Review identified two distinct failure classes behind
  the one development false-safe (`07_ai_cheating_exam`/S):
  `CONCEPTUAL_WRAPPER_SHIELDING` (a sentence with both conceptual
  framing and a factual world-claim gets classified wholesale
  `interpretive_only`, shielding the embedded fact) and
  `SUPPORT_STRENGTHENING` (a stronger candidate claim gets accepted as
  `supported` because it's "a reasonable characterization" of weaker
  source wording, rather than checked for equal-or-greater factual
  strength). Explicit decision: fixable entirely inside the B2 prompt —
  no `B2_MODEL_OUTPUT_V2`, no new stage/role/validator; the 4 auditor-
  evidence transport failures (paragraph collapse, parenthetical
  deletion, quote splicing) stay prompt-level fixes (short/contiguous
  citations, multiple entries for non-contiguous support) — explicitly
  NOT a resolver expansion (rejected as unsafe fuzzy/reconstructive
  repair). `cj2-stage-b2-v1.2` adds 4 corrections, all additive, no
  schema/enum change: (A) `ATOMIC CLAIM DECOMPOSITION` section + two
  new generic (queue/customers; interface/two-populations) worked
  examples — a compound sentence with both framing and a world-claim
  must be split, not classified as one interpretive whole; (B)
  `SUPPORT MEANS EQUAL-OR-GREATER FACTUAL STRENGTH, NOT A PLAUSIBLE
  PARAPHRASE` section with an explicit 7-pattern strengthening
  checklist (modality/capability, causality, necessity-dependency,
  motivation, capability, population linkage, temporal scope), each
  mapped to the existing problems enum with no new values; (C)
  explicit "claims may share a source_field" statement + a 4th JSON
  example demonstrating it; (D) `COPY DISCIPLINE` subsection banning
  the three named transport-confound shapes, requiring 2 separate
  `auditor_evidence` entries for non-contiguous support. A real
  contamination bug was caught by the static preflight itself before
  freezing: a first draft accidentally echoed the AI Exam/S fixture's
  own wording ("reluctant to return") into a generic example — fixed,
  re-verified. Static preflight 158/158 PASS (all v1.1 checks
  re-verified + every new item on review's list). Pre-registered
  acceptance criteria for the next run, so goalposts can't move after
  the fact: AI Exam/S must not come back safe and no clean candidate
  may become unsafe; NOT requiring 12/12 agreement with the (non-
  independent) human audit. Decision rule set in advance: if v1.2
  fixes AI Exam/S cleanly, move to a fresh batch; if it still calls it
  safe, stop prompt-tuning and reconsider B2's mechanism rather than
  write v1.3/v1.4/... Full corrections, prompt, template, preflight,
  and acceptance criteria in the experiment doc's `## cj2-stage-b2-v1.1
  — STATUS: EXECUTED` and `## PROMPT FROZEN: cj2-stage-b2-v1.2`
  sections. No API calls made in this round. No changes to
  `cj2-stage-a-v1`, `cj2-stage-c-v1`, the capsules, `B2_MODEL_OUTPUT_V1`,
  the resolver, or CJ-1.

  **`cj2-stage-b2-v1.1` FIRST DEVELOPMENT-REGRESSION RUN (2026-08-11,
  same day) — 12 real API calls, one per frozen Stage A candidate.**
  Pre-registered a development-labels manifest from the existing
  offline audit BEFORE any B2 call (6 clean / 5 semantic_fact_laundering
  / 1 ambiguous_boundary — preserved as its own label rather than
  forced binary; SHA256 recorded in the experiment doc). Built an
  experiment-only harness (`automation/cj2_b2_probe.py`, dry-run
  validator-tested against 5 synthetic cases first) implementing the
  full frozen B2 protocol: field coverage manifest, claim structural
  invariants, a deterministic `declared_refs`-vs-actual-declared-set
  check, an auditor-evidence provenance layer (wraps, never mutates),
  and the 3-layer `run_status`→`effective_verdict` computation exactly
  per `B2_MODEL_OUTPUT_V1` round-4 rules. Ran on trident (CLIPROXY is
  localhost-only) in an isolated `/tmp` scratch, hash-verified in both
  directions, scratch removed after pull-back — same convention as the
  first reference probe. **Result: 12/12 valid, 4 safe/4 unsafe/4
  ambiguous, 0 schema_invalid, 0 call_failed.** Candidate-level: 4/5
  known-laundered candidates correctly reproduced as unsafe, 0
  development false-unsafe, but **1 development false-safe** —
  `07_ai_cheating_exam`/S, the single worst-laundered candidate in the
  set, came back fully safe, missing every one of its 4 known
  problematic propositions (B2's own reasoning explicitly accepted
  "aversive or inaccessible" as "a reasonable characterization of
  reluctant to return to the classroom" — the exact laundering move).
  Proposition-level: 7/12 known problematic claims matched, 5 missed,
  1 new B2-only finding. Found 3 new subtypes of the known
  provenance-transport-confound class inside B2's OWN auditor-evidence
  citations (paragraph-break collapse, parenthetical elision,
  quote-fragment splice across an attribution clause) — all correctly
  routed to `audit_unresolved`→AMBIGUOUS, never UNSAFE, confirming the
  round-4 bug fix holds live. 0 extraction-coverage anomalies (0/66
  fields marked `no_auditable_propositions=true`). Full 12-row table,
  per-claim detail, and the ambiguous-outcomes breakdown in the
  experiment doc's `## FIRST DEVELOPMENT-REGRESSION RUN` section.
  This is a non-independent development-regression result (the labels
  come from the same audit that discovered the failure class), not a
  generalization claim. Per instruction: prompt not edited, false-safe
  case not rerun, no fresh-source test, no Stage-C-v2, no production
  wiring. Stopped for review.

  **`cj2-stage-b2-v1` SUPERSEDED BEFORE FIRST CALL, `cj2-stage-b2-v1.1`
  FROZEN (2026-08-11, same day).** A pre-execution prompt-contract
  review (no API calls made against v1) found four defects: (1) the
  user template gave B2 all canonical `cj1:aN` evidence but never the
  candidate's own `seed_evidence_refs`, making SUPPORT vs DECLARATION
  structurally indistinguishable; (2) v1's own `INTERPRETIVE_ONLY`
  bridge example smuggled an unsupported "official safety rating" claim
  behind "can be read as" — teaching the exact laundering pattern B2
  exists to catch — and the sorting-algorithm example had no concrete
  source statement to audit against; (3) `importance` and `problems`
  were required output fields with no precise definitions/invariants;
  (4) the user template's `additional_source_observations[0]:
  observation:` nesting didn't literally match the schema's
  `additional_source_observations[0].observation` identifier. v1.1
  fixes all four: adds a `CANDIDATE-DECLARED SEED EVIDENCE` block +
  a `DECLARATION LINEAGE` section (a real excerpt does not certify its
  own paraphrase); replaces the bridge example with a safe pair
  (closure-as-shift-in-treating-safety vs.
  engineers-believed-collapse-was-imminent) plus a new `HEDGES DO NOT
  IMMUNIZE A CLAIM` section, and drops the sorting-algorithm example
  entirely; adds full `importance` definitions (diagnostic-only, never
  an exemption) and the 8-value `problems` enum with frozen invariants;
  presents every claim-bearing field as literal `source_field: <exact
  id>` blocks matching the schema exactly, plus a new worked example
  (`c3`) showing correct `declared_refs` lineage. No architecture/schema
  reopened. Static preflight (92 checks, superset of v1's) — ALL PASS.
  Explicitly logged: the frozen 12-candidate set is a development/
  regression set with post-hoc labels, not a held-out benchmark — the
  first v1.1 run against it tests reproduction of known failure classes,
  not generalization. Full prompt/template/preflight and the v1
  supersession note in the experiment doc's `## cj2-stage-b2-v1 —
  STATUS: NOT EXECUTED` and `## PROMPT FROZEN: cj2-stage-b2-v1.1`
  sections. No API calls made. No changes to `cj2-stage-a-v1`,
  `cj2-stage-c-v1`, the capsules, `B2_MODEL_OUTPUT_V1`, or CJ-1.

  **PROMPT FROZEN: `cj2-stage-b2-v1` (2026-08-11, same day) — historical,
  superseded above before first execution.** B2
  architecture/schema review is done — this is the first B2 prompt,
  composed against `B2_MODEL_OUTPUT_V1` exactly, with one operational
  clarification decided during composition: **"auditable proposition"
  ≠ "factual proposition"** — without saying so explicitly, the field-
  coverage manifest could be satisfied either by extracting and
  classifying a genuine interpretive claim (`interpretive_only`) or by
  skipping it as `no_auditable_propositions=true` on the grounds that
  it's "not factual" — both legal under the schema, but the second
  choice would make coverage prove only "I searched for factual-
  looking material," never "I distinguished interpretation from
  factual dependency," which is B2's whole purpose. Also added:
  explicit trigger-word guidance (produces/creates/causes/etc. don't
  themselves determine role) and two generic, non-development
  examples (a bridge inspection, a sorting algorithm) so the frozen
  12-candidate set stays an untouched test set rather than material
  B2 has already seen phrased identically. Static preflight (banned
  terms, no self-reported `verdict`/`effective_verdict`/`run_status`,
  no development-fixture content, `resisting_detail` labeled context-
  only, both worked JSON examples parse and contain no verdict/status
  keys) — all PASS. Full prompt + user-input template + preflight log
  in the experiment doc's `## PROMPT FROZEN: cj2-stage-b2-v1` section.
  No API calls made. No changes to `cj2-stage-a-v1`, `cj2-stage-c-v1`,
  the capsules, the B2 schema, or CJ-1. Next: run B2 against the
  frozen 12-candidate development set (no new Stage A calls) and
  measure `FALSE_SAFE`/`FALSE_UNSAFE`/`ambiguous`/`schema_invalid`
  rates before touching Stage C.
- **THEN** — Phase 2, brevity + evidence budget + testimony.
- **THEN** — Phase 3, persona architecture implementation (perceptual
  engines, motives, soft affinities, remove hard territories/prohibitions —
  informed by 1.5A's findings).
- **THEN** — same-source/four-persona probe (validates whatever Phase 3
  produces).
- **THEN** — Phases 4-8 (correction/repetition/readability/ending/final
  audit), original blueprint order, unaffected by this insert.

## HEAD / PROVENANCE
- **WHY WE WRITE doctrine commit**: `01339ce` — the SYSTEM-prompt swap in
  `automation/orchestrator/llm.py`, the permanent/frozen shared doctrine.
- **Fable review-seat ROI probe commit**: `b99d379` — generated the 8
  Phase 1.5B cases; later checkpoint commits only add provenance/docs, did
  not regenerate data.
- **CURRENT MAIN HEAD**: whatever `git rev-parse HEAD` says after the
  latest checkpoint commit — always AHEAD of the commits above by
  docs-only commits. A session seeing a different HEAD than cited here is
  not a bug.

## PHASE 1.6 — DONE

Source-grounding hardening. DONE, not perfect — known limitations below
are explicitly bounded, not hidden. Full implementation history (7
adversarial offline review rounds, live API controls, two corrected
rounds of live acceptance controls) archived verbatim to
`.claude/experiments/phase-1.6-source-grounding-2026-08-11.md`. Design
doc: `.claude/phase-1.6-source-grounding.md`.

**Story evidence:** planner/writer/reviewer/executor share one
`source_hash` and one `evidence_packet_hash` (`evidence_lineage`),
confirmed through the real `generate.py` persistence path, not just by
code inspection.

**Persona history:** writer/reviewer/executor share one persona
`context_hash` (`persona_factual_lineage`), separate provenance from
story evidence on purpose — one answers what source grounded the
article, the other what authorized a persona's first-person claims.

**Tamper:** candidate-excerpt-forgery rejection — PASS (`validate_evidence_field`).
Real `_load_frozen_brief` packet-identity-mismatch rejection — PASS (the
actual production gate, not a manual hash recreation).

**Hostile executor:** v2 (valid input) exposed two real failures — a
Berlin/2022 personal-memory fabrication, and a subtler unsupported-
premise-laundering failure ("What upset Rossi was..." — the source never
established that she was upset). Deterministic containment caught the
former (a bare new number). A prompt-contract fix ("EDITORIAL NOTES ARE
INSTRUCTIONS, NOT EVIDENCE") addressed the latter. v3 (same hostile
input, after the fix) showed no recurrence of either failure in one live
trial with Opus as the active fallback model.

**Deterministic-guard limitation, stated precisely:** the guards
(`find_new_unsupported_specifics`, `find_new_unsupported_personal_history`)
catch quote/name/number-shaped signals only — never treat "0 hits" as
semantic truth validation of arbitrary prose.

**Fable-specific behavior:** NOT independently tested post-fix — Fable
was unavailable in the v3 live call, so the executing model was Opus via
CLIProxy. Do not infer Fable's own behavior from this result; if it
matters, it belongs with the already-paused Phase 1.5B model-seat
question, not source-grounding.

**Permanent regressions** (run all five before touching this code again):
`grounding_test.py`, `executor_guard_test.py`, `writer_prompt_test.py`,
`lineage_persistence_test.py`, `snapshot_test.py --check`.

**Open, unrelated issue (logged, not fixed):** `_fable_update_state`'s own
docstring says "post-publish," but `generate.py` actually calls it before
the reviewer/executor block — see `OPEN INFRASTRUCTURE ISSUES` below.
Unrelated to grounding; do not derail a future session with it.

## CJ-1/CJ-2 RESEARCH CHECKPOINT (2026-08-11, design only — no code/tests run)

Active work, mid-design. Architecture: **CJ-1 (source friction gate) →
CJ-2 (four-persona contribution competition, not started)**. Do not
resume by re-deriving from scratch — pick up from the frozen v3 draft
below.

**CJ-1's job, narrowed twice this session:** NOT "does this reveal a
hidden mechanism" (v2, too demanding — 0/20 real production judgments
ever returned YES, and 0/2 genuine positive-control sources passed
either). NOT "has the source's own account failed to resolve the
tension" (an interim proposal, rejected — still interpretive, still
risks a permanent false-negative). Settled on: **is there at least one
concrete, exactly-quoted relation between facts in the real source that
doesn't sit easily together** — nothing more. `hidden_mechanism`,
`category_jump`, and `correction` all move downstream to CJ-2; CJ-1 never
produces them.

**Frozen v3 design decisions (prompt drafted in conversation, not yet
written to any file):**
- **Full-source-only.** CJ-1 never runs on a bare RSS summary — summary-
  level judgment was shown live to suppress detectable friction that
  real source text revealed (Dogs, Conducting). `NO_SOURCE` is a
  deterministic pre-check outside the model (reusing `get_source_text`/
  `get_source_origin`, already free/no-LLM-cost), not a third model
  output alongside PASS/NO.
- **`source_anchors`**: 1-3 EXACT verbatim substrings of the source (not
  paraphrase) — friction is often relational between two facts (e.g.
  Conducting: "musicians... don't need a conductor for the core tasks"
  + "an exceptional conductor... an electricity can flow"), and exact
  substrings make the anchor deterministically verifiable later, the
  same discipline Phase 1.6 already uses for `source_excerpt`/
  `direct_quote`.
- **Deliberately high-recall, not high-precision.** Explicit asymmetry:
  a false PASS costs one downstream CJ-2 comparison that finds nothing;
  a false NO permanently excludes a source from ever being seen by any
  persona. "When genuinely uncertain, PASS" is stated directly in the
  prompt.
- **Persona-blind AND disability-topic-blind.** No persona names, no
  `format_or_mediation`/`measurement_gap`-style taxonomy that leaks
  toward a specific persona's known interests (`transformation` covers
  format/mediation generically instead). No disability-relevance
  language anywhere, not even as a "doesn't count on its own" guard —
  removed entirely rather than restated, since the v2 prompt's own
  worked examples (not just its rules) were the likely source of "no
  disability-relevant friction" leaking into live NO verdicts even
  though the v2 rule already disclaimed topic-relevance.
- **No worked semantic examples with an implied destination.** v2's
  illustrative examples (splint→furniture, sidewalk→security, etc.) were
  removed even in a topic-neutral disguise (an earlier v3 draft's
  "body restraint → structural elegance" style examples were cut too,
  same session, for still encoding a resolved destination and still
  being disability-adjacent via "body"/"limitation"). v3's examples are
  relation *shapes* only (two facts don't sit together, a stated-
  necessary component is absent but the process still works, etc.), with
  no resolution implied.
- **`open_question` (not `hidden_mechanism`)**: one unanswered question
  about the anchored relation, explicitly NOT allowed to contain a
  proposed answer. A weak/missing `open_question` must never downgrade
  an otherwise grounded PASS — it's handoff metadata for CJ-2, not a gate
  condition.

**What was tested live before this design settled (real API calls, real
production data — see conversation history, not yet written to
`.claude/experiments/`):** provenance audit found the shadow-judge table
contaminated by manual TEST/TEST2 rows with blank provenance (all 3
apparent "YES" verdicts were these, not real judgments) — corrected;
real production history is 20 unique seeds, 0 YES, 20 NO under
`v2-evidentiary-bridge`. A full-source resolution probe (Dogs, Conducting,
Roman wreck) showed richer input changes what the judge can see (Dogs
produced a real `resisting_detail` it didn't have at summary level;
Conducting produced a full hidden-mechanism-shaped answer, rejected only
on the bridge-to-interpretation requirement v3 has since removed). Two
attempted "positive controls" from already-published CripMinds essays
were BOTH judged invalid as controls, not just as data points: the
Beaker Street piece is exactly the old accessibility-topic engine the
redesign is trying to escape, and the AI-curb source was not actually
independent — `2026-07-22-fourteen-nodes-on-nicholson-street.md` was
already prompted by that exact URL, a real error this session made and
should not repeat (cross-check candidate fixtures against `_posts/`
before calling anything a blind prediction). A free (no-LLM-cost)
source-fetch coverage sample (n=40) found 88% `fetched_article`, with
`space.com` failing 0/4 (systematic, not incidental) and `dezeen.com`
2/3 (matches an existing memory note on Dezeen fetch reliability).

**Explicitly not done:** v3 prompt has not been run against anything,
against the frozen 8-fixture set, or against the positive-control
candidates. No file has been written. No production code (news_fetcher.py,
discovery.py, generate.py) has been touched for this thread. The
`_THEME_TO_PERSONA`/domain-keyword hard router has NOT been modified or
removed — still not disproven as mattering only as a fallback.

**Next step, when resumed:** run the frozen v3 prompt (still only in
conversation, needs to be written to a scratch/experiment location first)
against the 8-fixture set + a couple of genuinely fresh, never-tested
sources, using real production fetch — NOT against previously-published
CripMinds essays as labels. Only after that does CJ-2 design begin.

**UPDATE 2026-08-11 (same day, later session):** v3 prompt frozen (four
review rounds), written to
`.claude/experiments/cj1-v3-friction-gate-2026-08-11.md`, validator built
(`automation/cj1_v3_validator.py`), and a first real paired v2/v3 probe run
on 4 fixtures (Conducting, Dogs, Roman shipwreck, one live-selected thin
promo-code control) — full results in that experiment doc's `## ROUND 1
RESULTS` section, not duplicated here. Headline: on `dogs_fear_sadness`,
v2 rejected BECAUSE the source explains its own mechanism (the exact
failure mode the redesign targets); v3, same frozen snapshot, PASSed on a
different real asymmetry without being blocked by that explanation — the
clearest live confirmation the redesign works. All 3 v3-PASS validator
failures traced to benign causes (curly-vs-straight apostrophe
normalization; one anchor quoting the TITLE rather than the snapshot
body), not hallucination — carried forward as implementation notes for
the real validator, not prompt changes. v3 prompt text unchanged as a
result. No production code touched, no CJ-2 started.

**UPDATE 2026-08-11 (round 2, same day):** deterministic resolver
(`automation/cj1_v3_anchor_resolver.py`, no model calls) confirmed both
round-1 `COPY_FIDELITY_FAILURE`s resolve to `normalized_unique_match`
(real anchors, curly-vs-straight-apostrophe transcription only) and the
`OUT_OF_SCOPE_ANCHOR` resolves to confirmed `out_of_scope` (real text,
just from the TITLE field, not `source_snapshot`). Fixed the harness
leak that caused that: v3's user prompt no longer includes TITLE (v2
unchanged, observed as-is). Re-ran ONLY v3, body-only, on the Wired
promo fixture (1 new model call, same frozen snapshot, hash-verified) —
still PASS, but now fully schema-valid, on a genuine numeric
inconsistency in the sale copy itself (25% tiered cap vs. an
unsubstantiated "up to 40% off" claim). So the harness leak is
confirmed and fixed, but does NOT retire the broader question of
whether CJ-1's recall bias is too permissive on real-but-trivial
friction — left open, not tuned. Full detail in the experiment doc's
`## ROUND 2` section. v3 prompt still unchanged, no production code
touched, no CJ-2 started.

**UPDATE 2026-08-11 (v3.1 + round 3, same day):** added a 4th failure
class (`UNSUPPORTED_RELATION` — every anchor real, but the claimed
relation between them requires an unstated shared-scope premise;
reclassifies Round 2's Wired PASS). Froze v3.1 (`RELATION GROUNDING`
+ `RHETORICAL-FRAMING GUARD`, two insertions only, no materiality
language) and ran exactly 3 new v3.1-only calls (Dogs, Conducting,
Wired — Roman and v2 untouched, no refetch, hashes verified). Result:
Dogs PASSed as hoped, genuinely grounded (single relational fact, no
added premise). Conducting and Wired did NOT flip to NO as hoped —
both still PASS, and manual inspection confirms both guards failed to
hold on this sample: Conducting's anchors are still opinion-opposition
framing dressed in guard-adjacent language, not a reported behavior;
Wired's 3-way "contradiction" is still an unstated-same-scope
assumption across what the source presents as several differently-
named, sequential sale events. Whether this is guard-wording weakness
or single-sample stochastic variance at `temperature=0.9` is
unresolved. Full detail in the experiment doc's `## ROUND 3` section.
v3.1 prompt unchanged since freezing, no production code touched, no
CJ-2 started.

**UPDATE 2026-08-11 (round 4, temperature isolation, same day):** ran
the same 3 fixtures through frozen v3.1 at `temperature=0.0` (Round
3 was 0.9) — no prompt edits, hashes re-verified, new namespaced
result files, Round 3 untouched. Dogs: zero effect, identical
grounded PASS at both temperatures. Conducting: still PASS at 0.0, but
landed on a DIFFERENT rhetorical route (musicians' persisting
mistrust) than Round 3's (con artist/God framing) — evidence the
rhetorical-framing leak is structural, not a one-off high-temperature
sample. Wired: still PASS at 0.0, still `UNSUPPORTED_RELATION`-shaped,
though a closer call than Round 3 (this time both anchors sit under a
name — "the Design Within Reach summer sale" — the source itself
reuses across both paragraphs, narrowing but not resolving the
unstated-shared-ceiling premise). Verdict: structural prompt-
compliance issue, not mainly sampling variance — temperature was not
the fix. Full detail in the experiment doc's `## ROUND 4` section.

**UPDATE 2026-08-11 (v3.2 + round 5, same day):** froze v3.2
(`VALIDITY COMES BEFORE RECALL` precedence block inserted before
`DECISION RULE`; old unconditional "when uncertain, PASS" line
replaced with one scoped to apply only after validity is established;
cost-asymmetry rationale deliberately removed from the model prompt
entirely, kept only as doc rationale). Ran exactly 3 new v3.2-only
calls at `temperature=0.0` (Dogs, Conducting, Wired — hashes
verified, no v2/v3/v3.1 reruns). Result: **2 of 3 fixed.** Dogs
unchanged (never depended on recall bias). Wired correctly flipped to
NO — the fix worked as designed, no longer manufacturing a shared-
scope equivalence between the 25%/40% figures. **Conducting still
PASSes**, and inspection shows a more concerning failure mode than
before: the model's own `reason` field explicitly asserts validity-
condition compliance ("grounded in verbatim text and does not require
any premise the snapshot fails to supply") while the underlying
anchors are still opinion/attitude content (musicians' mistrust vs.
the "God" view), not a phenomenon-level fact — provisionally logged
as a candidate 5th failure class, `GUARD_RATIONALIZATION`, not yet
formalized. This does NOT match the pre-registered clean-fix outcome,
so per explicit criterion we have NOT reached the point of moving to
a broader calibration set. Full detail in the experiment doc's
`## ROUND 5` section.

**UPDATE 2026-08-11 (course correction + Fresh Calibration Batch 1,
same day):** on review, retracted the Round 5 framing of Conducting as
a proven guard failure — reclassified as `AMBIGUOUS / CONTESTED
FRICTION`, not `GUARD_RATIONALIZATION` (too anthropomorphic, and
persistent-practitioner-mistrust may itself be a legitimate social
phenomenon CripMinds should be able to investigate; forcing this one
snapshot to NO risked encoding an unintended physical/scientific-vs-
social bias). Dogs/Conducting/Wired are now load-bearing regression
fixtures, retired from further prompt tuning — continuing to iterate
until Conducting says NO would be overfitting, not progress.

v3.2 (`cj1-v3.2-validity-before-recall`) froze unchanged. Built and
ran Fresh Calibration Batch 1: 12 fresh seeds, none previously
discussed in this design history, selected from the LIVE production
DB on trident (`/srv/data/hermes/workspace/disability-ai-collective/`
— this repo's local checkout was found stale, max `fetched_date`
2026-06-22 vs. live 2026-08-11, logged as a real discovery) BEFORE any
fetch or LLM call, independent of `disability_angle`/persona, spanning
6 categories × 2. 2 of the original 12 (both Le Monde English) failed
to fetch (`fallback_summary`, not `fetched_article`) and were replaced
by the same blind selection method, also recorded before fetching.
Ran v3.2-only, `temperature=0.0`, body-only, 12 real calls.

**Result: 10 `CLEAN_PASS`, 2 `CLEAN_NO`, zero false positives, zero
false negatives, zero ambiguous** — every PASS manually checked
against full source context (not just isolated anchors), every anchor
either `exact_match` or `normalized_unique_match` (same known
apostrophe-transport issue, zero `no_match`/`ambiguous_match`). No
`UNSUPPORTED_RELATION`, no `FALSE_PASS_FRAMING_ONLY` recurred on fresh
material — Wired's and Conducting's failure shapes did not
generalize. Human/institutional/behavioral subject matter (AI-cheating
academic response, researcher trust in an AI tool, central-bank
policy reasoning) all PASSed correctly on concrete source-stated
facts, not attitude-opposition — no sign of the science-vs-social bias
the course correction flagged as a risk, though n=12 doesn't prove its
general absence. Full detail in the experiment doc's
`## FRESH CALIBRATION BATCH 1` sections (selection + results). No v3.3,
no production wiring, no CJ-2. Next: awaiting decision on whether this
is enough signal to consider a broader/staged calibration, or to begin
scoping CJ-2.

**UPDATE 2026-08-12 (CJ-2 Stage B2 saga, condensed — full detail lives
in `.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md`,
not duplicated here):** CJ-2's Stage B2 (semantic factuality gate,
engine-blind, sits between Stage A and Stage C) went through v1/v1.1/
v1.2/v1.3/v1.4/v1.4.1, each a prompt-only fix targeting a specific
diagnosed failure in how the auditor classifies a claim as
`interpretive_only` vs `factual_dependency`. **v1.4.1 REGRESSION
STATUS: FAIL** — it fixed the narrow hedge-as-exemption bug v1.3 was
diagnosed with, but the same underlying bypass (skipping the MANDATORY
CONCRETE RESTATEMENT step and instead calling a real empirical claim
"a lens applied to established facts") resurfaced through a different
verbal route, and **regressed two previously-fixed targets** (H14, De
Hooch/Z) back to unsafe-classified-as-safe. Conclusion recorded:
**prompt-only role-classification correction has reached a reliability
limit for this failure class** — not "prompt-only can never work," but
"another prompt-only patch is not the next move." No `v1.4.2` designed
or run. Designed (architecture only, NOT implemented, NOT executed) a
structural successor, `B2 v2 — EXPLICIT PROPOSITION CONTRACT`: splits
the single B2 call into R1 (proposition analysis — world-truth test +
concrete restatement, evidence-blind, produces a required, checkable
artifact) and R2 (role/factuality audit — consumes R1's fixed output,
cannot re-decompose or silently disagree with it without a logged,
non-empty override rationale). Deterministic consistency layer
fail-closes the exact observed failure direction (R1 says a real
dependency exists, R2 calls it interpretive, no override → schema_
invalid) via the existing `schema_invalid` mechanism, no new verdict
invented. Full schemas, invariants, cost estimate (~2x B2-stage calls,
less than 2x tokens), honest new-failure-mode list (correlated bias
between R1/R2 not eliminated; override-gaming risk), regression plan,
and a bidirectional role-migration-report spec (existing global guards
only measured drift toward `factual_dependency`; v1.4.1 drifted the
opposite way and both frozen gates were silent on it) are all in the
experiment doc's `## B2 v2 — EXPLICIT PROPOSITION CONTRACT` section.
**Nothing implemented. No `cj2_b2_probe_v2*.py` exists. No API calls.**
Several implementation decisions explicitly left open (same-model
R1/R2 or not, keyword-backstop for the restatement trigger, override-
rationale substantiveness bar, whether to gate the "R2 stricter than
R1" direction, whether any new metric becomes a frozen threshold) —
none resolved, per instruction, until a dedicated implementation pass.

**UPDATE 2026-08-12 (B2 v2, Revision 2 — two architecture corrections,
still design only):** two real defects in the first B2 v2 draft were
corrected before any implementation. **(1)** The draft treated an
unresolved R1/R2 *semantic* disagreement (R1 says a real dependency
exists, R2 calls the claim `interpretive_only`) as `schema_invalid` —
wrong; that conflates a contract violation with a legitimate research
finding. Corrected: `schema_invalid` is now reserved strictly for
actual malformation (missing fields, illegal enums, mismatched claim-
ID sets). A genuine disagreement is exposed as its own deterministic,
orchestrator-computed state, `R1_R2_SEMANTIC_CONFLICT`, which — only in
the safety-relevant direction (R1=dependency, R2=interpretive) — maps
into the EXISTING `ambiguous` fail-closed path via one new
`effective_status` value (`unresolved_semantic_conflict`) that routes
exactly like the existing `uncertain`/`audit_unresolved` statuses
already do. Critically: R2's free-text `override_rationale` field is
kept for diagnostics but **cannot clear the conflict** — the
deterministic check reads only `R1.empirical_dependency` and `R2.role`,
never the rationale text, closing off "R1 catches it → R2 writes a
fluent paragraph → it silently becomes interpretive_only" by
construction, not policy. The other three cells of the 3×3 (empirical_
dependency × role) table are NOT gated — most notably, R2 being
*stricter* than R1 (R1=false, R2=factual_dependency) is logged as a
diagnostic "escalation," not auto-rejected, per instruction to evaluate
that direction for overcorrection rather than reflexively blocking it.
**(2)** The draft's `requires_concrete_restatement` trigger (keyword/
subject-type conditional) was itself a new bypass point — removed
entirely. R1 now performs the full proposition contract (`world_truth_
question`, `concrete_restatement`, `empirical_dependency`) for EVERY
atomic claim, unconditionally; an already-concrete claim just gets an
identity restatement, which is correct, not a shortcut. Also decided:
same model for R1/R2 on the first structural test (isolates the
structural-externalization variable; correlated same-model bias
explicitly not eliminated, no independence claimed), and R2's output
no longer redundantly carries claim text at all (removes an entire
"claim reshaped" risk category rather than policing it after the
fact — R2 is keyed by `claim_id` only, joined against R1's fixed
`propositions[]`). Full corrected schemas, the exhaustive directional-
consistency table, and a fully-enumerated bidirectional migration-
report spec (6 role-level + 6 candidate-level transition counts, no
thresholds chosen) are in the experiment doc's `## B2 v2 — REVISION 2`
section.

## B2 v2 — CURRENT POINTER (2026-08-12): R2 CAPACITY-RECOVERY RUN EXECUTED —
## 3 REPAIRED / 3 FLAGGED_NOT_RESOLVED / 1 MISS (SEPARATE FROM, DOES NOT
## OVERWRITE, REGRESSION #1's FROZEN FAIL)

**Regression #1 (below) is preserved exactly as historical record: formal
gate FAIL, plus an added interpretation, SEMANTIC EVALUATION INCOMPLETE —
17/30 candidates never produced a valid R2 result due to systemic
MAX_TOKENS truncation, so the semantic architecture was never fully
exercised.** Not retroactively changed to pass or fail differently.

**Diagnosed before any new call, per instruction:** H08's "R1 never
extracted the proposition" finding is confirmed NOT an implementation
defect — the frozen design doc's own Correction 3 explicitly states R1 is
"the first and only place decomposition happens," with no upstream
atomic-claim-extraction step to preserve. H14 documented precisely as a
support-calibration disagreement (R1/R2 agree on role; R2's support
judgment differs), not tuned. R2 sizing analyzed empirically from
Regression #1's own data (no calls) — froze `MAX_TOKENS=12000` (largest
corpus candidate projects to ~6.7-7.8k tokens; 12k gives real headroom).
Full diagnosis: `automation/.probe_fixtures/cj2-b2-v2-regression/regression-1-methodological-addendum.md`.

**B2-v2 R2 CAPACITY-RECOVERY REGRESSION executed** — NOT v2.1, NOT semantic
tuning: the only experimental change was R2's `max_tokens` (5000→12000, a
runtime override, no frozen file edited — hashes of the harness/prompts
confirmed identical to Regression #1). R1 was **reused, not rerun** (frozen
R1 outputs from Regression #1, hash-verified). 30 calls (0 R1 + 30 R2), 0
transport failures, executed on trident/CLIProxyAPI, local-canonical, all
hashes verified before and after (this time including the driver itself,
closing Regression #1's disclosed gap).

**Run health: 29/30 valid, 0 truncations** — the target infrastructure
result is met. The one schema_invalid (H18) is unrelated to capacity: a
complete, well-formed response with one illegal invented `problems` enum
value.

**Seven targets: 3 REPAIRED (H09, H14, De Hooch/Z) / 3 FLAGGED_NOT_RESOLVED
(H17, H05, H03, unchanged) / 1 MISS (H08, unchanged — R1-side, unfixable by
an R2-only recovery).** H09 and De Hooch/Z, disqualified purely by
truncation before, now resolve cleanly. H17's failure mode is confirmed
identical on rerun (R2's own reasoning repeats the same hedge-citation
language verbatim in substance) — proving it's a reasoning issue, not a
capacity artifact.

**Conflict rate: 183/522 valid claims (35.1%) are `R1_R2_SEMANTIC_CONFLICT`
— described with corrected language throughout: "safety-relevant
disagreement" / "potential false-safe prevented," never "confirmed
false-safes."** R1 is not human ground truth; this remains a measured rate,
not an adjudicated one. Dominant candidate-verdict shift: 11/30 safe→unsafe,
0 unsafe→safe.

Full artifacts: `automation/.probe_fixtures/cj2-b2-v2-r2-recovery/`
(`recovery-run-report.md`, `recovery-run-comparison.json`, 30 raw
per-candidate results). No v2.1 designed. No Stage C. No Reader Lab data
used. No selective reruns. **Next real decision, not made this pass:**
whether the 3 REPAIRED results generalize, and whether H17/H05/H03's
persistent reasoning-level failure (not capacity) now warrants an actual
v2.1 prompt-design pass.

## B2 NEXT-STRUCTURE — CURRENT POINTER (2026-08-13, same session): B2
## R2 REPAIR-TAXONOMY CONSEQUENCE AUDIT COMPLETE — ZERO MODEL CALLS —
## CATEGORY IDENTITY IS NON-CONSEQUENTIAL TO SAFETY

**Pure code/design audit, no model calls.** Primary question: does the
exact identity of an R2 `problems` category affect downstream safety/
control flow, or is it explanatory metadata on an already-fixed
`support=unsupported` judgment?

**Taxonomy, read from canonical source, not inferred**: R2's own frozen
prompt states verbatim, "A claim may have more than one problem at
once" — multi-label by explicit design, not mutually exclusive, no
unique correct answer was ever the intent. (Minor pre-existing prompt
inconsistency noted, not fixed: `mechanism_invention` is a valid schema
enum the prompt's own 7-pattern checklist never actually maps to.)

**Data flow, traced directly in code**: exactly ONE function in
`cj2_b2_v2_probe.py` reads `problems` — `validate_r2` itself, and only
for presence/type checking (never which specific value). `compute_
consistency`, `compute_effective_v2` (the function that computes the
FINAL safe/unsafe/ambiguous disposition), `validate_auditor_evidence`,
and every reporting/migration helper were checked directly — none read
`problems`. Stage C has no code path consuming R2's `claims[]` in the
current architecture at all.

**Safety consequence test, verified programmatically**: re-ran H13's
full downstream pipeline substituting all 7 valid semantic-problem
values in place of the actual repair choice, one at a time. **All 7
produce a byte-identical `validate_r2.valid`/`effective_verdict`/
`per_claim`/`consistency` output.** Not argued from code-reading alone
— directly executed and confirmed.

**Controlled-arm reference audit**: the 3 "ground-truth" values were,
per the repair probe's own preregistration, themselves just "3
EXISTING... claims with a real semantic-problem tag" from an ORDINARY
earlier R2 call — never a hand-verified authoritative label. Combined
with R2's own "more than one at once" design statement: exact-match was
never a well-posed correctness test. **Original 0/3 result preserved
unchanged, not re-scored** — only its interpretation changes (evidence
about cross-call reproducibility, not "wrongness").

**Natural inconsistency (H03/c7 vs H09/c10), classified**: both claims'
own `why` text independently name the same "population/social pattern"
framing, yet only H03/c7 got `population_relation_hardening` tagged.
**Classified APPARENT INCONSISTENCY** (not meaningfully different, not
a clean soft-taxonomy alternative — a real, observed category-omission
instability) — but confirmed, via the same programmatic substitution
method, to have zero downstream safety consequence.

**FINAL CLASSIFICATION: A. CATEGORY IDENTITY IS NON-CONSEQUENTIAL TO
SAFETY.** Repair semantics should use a compatibility/plausibility
notion, not single-label exact match, for future calibration — stated,
not implemented this pass. Not declared production-ready: the repair
step's cross-call inconsistency (though consequence-free) still merits
attention before any integrated-adoption decision. Per the minimize-
human-intervention principle: since identity is explanatory metadata,
routine automatic repair of this narrow allowlisted class doesn't need
per-repair human adjudication of WHICH label was chosen — only that
revalidation passes and immutable fields stayed frozen, both already
deterministically checked. **Zero model calls. No prompt edit
anywhere. No validator weakening. No Stage C execution. No Reader Lab
material.** Full evidence in the experiment doc's `## B2 R2 REPAIR-
TAXONOMY CONSEQUENCE AUDIT` section. **Stopping here.**

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above) B2 R2 VALIDATOR-GUIDED CONTRACT-REPAIR PROBE
## EXECUTED — MECHANICALLY CLEAN (6/6), SEMANTIC RELIABILITY UNCLEAR
## (0/3 EXACT MATCH ON CONTROLLED ARM, ONE CROSS-CALL INCONSISTENCY
## FOUND)

**Pre-design finding, before any model call**: inspected all 8 already-
observed R2 failing claims' `why` text (H13 x3, H03 x4, H09 x1) — every
one describes total source SILENCE on the claim's topic, not a weaker-
stated-relation being hardened (the shape R2's 6 named patterns are
built for). No deterministic rule reliably reproduces a careful
reader's category choice across all 8 — model-assisted repair adopted
on this finding, not chosen by default.

**Narrow, versioned repair contract**: new prompt `r2-contract-repair-
v1.txt` (R2's own prompt untouched), fires ONLY on the exact allowlisted
condition (`support=unsupported` + zero semantic-problem tags — the
identical check `validate_r2` itself makes). Immutable fields:
everything except `problems`, which may only be APPENDED to, never
replaced. Flat strict `json_schema` patch. **44/44 static safety checks
pass**, including adversarial simulations (a hypothetical merge that
drops an existing value, changes `support`, or changes the claim-id set
is caught by the verifier; an out-of-allowlist claim_id in a patch is
silently ignored).

**Executed: 6/6 calls (3 natural + 3 controlled), no stop, ~15s.**

**Natural arm (H13, H03, H09 — frozen from already-completed runs, R1/R2
NOT rerun): 3/3 `repaired_valid`.** Semantic review: 8/9 individual
claim repairs well-justified against their own evidence. **One real
cross-call inconsistency found, not smoothed over**: H03/c7 and H09/c10
assert a near-identical population-interruption-rate claim but got
DIFFERENT category treatment across two separate repair calls — neither
nonsensical, but not stable either.

**Controlled arm (3 known-valid claims, `problems` stripped to simulate
the exact failure, ground truth withheld from the model): 3/3
mechanically valid, 0/3 exact ground-truth match.** On close review,
**0/3 were nonsensical or evidence-incompatible** — H12_c5's answer
included the correct tag PLUS a well-justified addition (grounded in
the source's own "can be at odds with" hedge, arguably MORE complete
than the single-tag ground truth); H07_c8/H03_c3 chose a defensible
alternate reading (`other`) instead of a more specific tag — genuine
taxonomy-boundary ambiguity, exactly as the pre-design finding
predicted.

**What remains fail-closed, unconditionally**: every other
`validate_r2` violation shape (role/support mismatches, `r1_agreement`/
`override_rationale` violations, claim-id-set mismatches) — none of
those are in this V1 allowlist.

**FINAL CLASSIFICATION: B. CONTRACT REPAIR MECHANICALLY WORKS BUT
SEMANTIC RELIABILITY UNCLEAR.** Not A: the controlled arm's own exact-
match test came back 0/3, and a real cross-call inconsistency was
found — "mechanically clean" isn't the same as "reliably reproduces the
intended specific answer." Not C: nothing nonsensical or unsafe was
produced anywhere. No R1/R2/D0/C0 prompt edit. No `validate_r2`
weakening. No Stage C. No v2.1. No next design step (v2 repair prompt,
voting mechanism, etc.) proposed or attempted, per instruction. Full
tables and hashes in the experiment doc's `## B2 R2 VALIDATOR-GUIDED
CONTRACT-REPAIR PROBE — EXECUTED, RESULTS SCORED` section. **Stopping
here.**

**TAXONOMY-CONSEQUENCE AUDIT (same day, zero model calls, code/design
only): CATEGORY IDENTITY IS NON-CONSEQUENTIAL TO SAFETY.** Traced every
consumer of `problems` in code — exactly one (`validate_r2`'s own
non-empty/type check), never read by `compute_effective_v2` or
`compute_consistency`. Programmatic counterfactual: substituting every
one of the 7 valid problem values into H13's repaired claims produced
byte-identical downstream output every time. The "B" classification
above concerned exact-label reproducibility, which this audit shows was
never the safety-relevant question — repair semantics should use
compatibility, not exact-match. Full detail: experiment doc's `## B2 R2
REPAIR-TAXONOMY CONSEQUENCE AUDIT` section.

**B2 R2 CONTRACT-REPAIR INTEGRATED RECHECK — EXECUTED, RESULTS SCORED
(2026-08-13), DECISION A, SUPERSEDES "B" FOR THE STAGE-C QUESTION.** Ran
the actual composed R1->R2->repair execution path (not three separate
frozen-artifact experiments) on the same 9 gate-passed candidates.
Recovered from Trident scratch by a fresh session after the run
completed but before the prior session could score it — full
provenance verified (all 13 frozen harness/module files + the
preregistration byte-identical local-vs-trident-vs-recorded-hash, no
rerun). **21/21 calls clean** (9 R1 + 9 R2 + 3 repair; zero config
failures, truncations, or exceptions). R1 9/9 valid; R2 6/9 valid
directly, 3/9 (H03, H09, H13 — the exact same known-failure items from
the two prior separate probes, no new failure class) triggered repair;
**3/3 repairs succeeded**, all 7 individual claim-level additions
semantically compatible with their own frozen `why` text (0
incompatible, 0 questionable), zero immutable-field changes, zero
integration failures, and every repaired claim's `effective_status`
stayed `unsupported` (the harness's own live safety check, never
triggered). **Final: 9/9 candidates fully valid end-to-end** (up from
6/9 without repair). **Decision: A — R2 REPAIR LAYER OPERATIONALLY
ADEQUATE, ready to reconsider Stage C next** (reconsidering it is not
itself starting it). Full tables, per-repair semantic review, and the
one already-expected cross-call category inconsistency (non-
consequential per the taxonomy audit above) in the experiment doc's
`## B2 R2 CONTRACT-REPAIR INTEGRATED RECHECK` section. No v2.1
assigned. No R1/R2/D0/C0/repair-prompt edit. No Stage C run. Reader Lab
untouched — Jascha reports both parents completed RL-2026-001, not
inspected or analyzed this pass, left to the autonomous calibration
pipeline per its own design.

**B2 → STAGE C INTEGRATION CONTRACT AUDIT (2026-08-13, same session,
design/audit only, zero model calls, zero code changes) — DECISION B.**
Re-verified the repair recheck's final counts directly from disk before
anything else (9/9 final validator-valid, all 9 `effective_verdict:
unsafe`, confirmed — not inferred). Reconstructed Stage C from code
(`cj2_reference_probe.py` + frozen `cj2-stage-c-v1.txt`): it receives
zero B2 fields today, no R2 claim object, confirmed directly from
`build_stage_c_user`. Its own `factual_integrity` dimension has a
**measured 0/6 catch rate** on the exact semantic-fact-laundering
failure class from the offline audit above — not hypothetical, already
observed. Traced every B2 output field codebase-wide: zero wiring into
Stage C anywhere. Key structural finding: B2's `item_id` (H0N) and
Stage A's `(source_slug, engine_label)` candidate are the SAME unit
(confirmed via `cj2_fresh_batch1_pipeline.py`/`_build_packet.py`), so
no unit-mismatch design problem exists. Proposed contract: B2 becomes
the authoritative ELIGIBILITY gate (full terminal-state routing table
in the experiment doc); Stage C's prompt/schema need **zero new
fields** — a candidate that doesn't clear B2 is simply never added to
Stage C's candidate set, exactly like a Stage-B-invalid candidate is
excluded today. Non-obvious finding from the actual repaired items:
because the safety invariant keeps every repaired claim `unsupported`,
**repair can never move an item into `safe`/`ambiguous` by
construction** — it only changes *why* a candidate is excluded, not
whether. Real gap flagged, not glossed over: **no `effective_verdict:
safe` example exists anywhere yet** (no run, no test fixture) — the
`safe`→Stage-C-eligible branch has never actually been exercised.
**Decision: B — one narrow orchestrator-side filter function needs to
be written (inserted into `run_source()` between Stage B and
anonymization) before any Stage C integration probe; no edit to
D0/C0/R1/R2/repair-v1 or the Stage C prompt itself.** Full terminal-
state table, dry-run cases, and the Cave-DNA/Engine-S concrete
illustration in the experiment doc's `## B2 → STAGE C INTEGRATION
CONTRACT AUDIT` section. No Stage C run. No Reader Lab consumption
(both parents reported complete, left to the autonomous pipeline).

**B2 → STAGE C ADMISSION GATE — IMPLEMENTED, MECHANICALLY TESTED
(2026-08-13, same session), DECISION A.** Built the narrow change the
audit above called for. New file `automation/cj2_b2_stage_c_admission_
gate.py` — zero non-`__future__` imports, reads only a small dict
envelope, never touches D0/C0/R1/R2/repair-v1/Stage-C-prompt/`problems`.
Implements the audited routing table exactly: 12 terminal-state labels
→ `ENTER_STAGE_C`/`BLOCK_BEFORE_STAGE_C`, unrecognized input always
fails closed (no "unknown → allow" path anywhere — verified by tests).
Wired into `automation/cj2_reference_probe.py`'s `run_source()` at the
exact audited insertion point (after Stage B's filter, before
`anonymize()`/`candidates_by_label`) via new `require_b2_admission=True`
(default, cannot be bypassed by `main()`) / `b2_admission_lookup=None`
params — missing B2 data for a candidate blocks it, never admits it.
Bypass audit: confirmed exactly one Stage C invocation path exists in
the whole codebase, now gated. New static suite: **112/112 checks
pass**, zero model calls — including a real reconstruction of H03's
actual C0 gate-block (replaying already-completed, on-disk D0/C0
output through the real unmodified `compute_pipeline_gate`) and real
H01/H03/H09/H13 repaired-but-still-`unsafe` cases. **Honest coverage
gap, stated explicitly, not smoothed over: `EFFECTIVE_VERDICT_SAFE` —
the only row that admits — has zero real precedent anywhere in this
project and is tested only via a clearly-labeled SYNTHETIC CONTROL-FLOW
FIXTURE.** After this pass: the `ENTER_STAGE_C` control-flow branch is
mechanically proven; B2 naturally producing a safe candidate remains
empirically unproven. All 12 pre-existing static suites re-run,
**12/12 still pass** — zero regressions. **Decision: A — routing layer
implemented and mechanically validated, ready for a Stage C integration
probe**, with that coverage gap carried forward into the probe's own
design. No Stage C execution. No Reader Lab consumption. Full detail in
the experiment doc's `## B2 → STAGE C ADMISSION GATE` section.

**B2 → STAGE C FIRST INTEGRATED DEVELOPMENT PROBE — EXECUTED, RESULTS
SCORED (2026-08-13, same session), DECISION B: ZERO NATURAL STAGE-C
ADMISSIONS.** First real, live run of the full composed path on 14
real development candidates (the 10 already-frozen + 4 genuinely fresh
ones, H11/H15/H16/H18, never before run through this architecture; both
verified byte-clean and RL-2026-001-free). **50 real model calls** (14
D0, 12 C0, 12 R1, 12 R2, 0 repair, 0 Stage C) — first launch attempt
made zero calls (401 auth error from a missing `CLIPROXY_KEY` env var
in the non-interactive SSH session; fixed) and needed 2 more
transitively-imported files added to the bundle after a
`ModuleNotFoundError`, both caught before any model call. **2/14
(H06, H15) blocked at D0's own structural stage** — a new terminal
state (`span_resolution_failed`, a hallucinated span) never seen
before, serving as this run's live negative control (proven directly:
zero downstream calls for either). Of the 12 that reached C0, 12/12
said `complete` — the intended negative control, H02, did NOT
reproduce its earlier known block this time (known D0/C0 cross-call
instability, already documented elsewhere in this track, not a
contradiction). **12/12 R1 valid, 12/12 R2 valid directly — zero
repairs needed for the first time in this project's history.** 200
claims scored: 64 `R1_R2_SEMANTIC_CONFLICT` (32%, the highest rate seen
yet), 60 unsupported, 52 supported. **12/12 final `effective_verdict:
unsafe`** (every item had ≥1 unsupported/undeclared factual claim) —
**0/14 admitted, Stage C never called, exactly matching the admitted
count.** `EFFECTIVE_VERDICT_SAFE` remains, after this pass, entirely
untested by real data. Interpretation: B2 is extremely conservative on
this corpus (10/14 items were already known-unsafe; the pattern
generalizes to the 4 fresh ones too) — open question is whether B2 is
correctly strict or over-triggering, which this probe can't resolve on
its own. **Decision: B — routing validated, Stage C semantic
integration still unobserved on real data.** Full detail in the
experiment doc's `## B2 → STAGE C FIRST INTEGRATED DEVELOPMENT PROBE`
section. No Reader Lab consumption (both parents reported complete).

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above) B2 R1/R2 PARTIAL STRUCTURED-OUTPUT PROBE EXECUTED
## — SHAPE FAILURES FULLY RESOLVED (18/18), CROSS-FIELD INVARIANT
## FAILURE PERSISTS ON DIFFERENT ITEMS — NOT READY FOR STAGE C

**Deliberately different question from the stopped EXECUTION-CONTRACT
RECOVERY**: not "does structured output solve R1/R2's full contract"
(known impossible) but "does PARTIAL provider enforcement (flat type/
enum only) improve mechanical compliance while unchanged
`validate_r1`/`validate_r2` stay authoritative for everything else?"

**Two-layer contract, verified before freezing**: Layer A = narrowest
flat `json_schema` (strict) for R1/R2's existing shape/enums only, no
`if`/`then`/`allOf`/etc anywhere (verified programmatically). Layer B =
unmodified `validate_r1`/`validate_r2`, authoritative for every cross-
field invariant Layer A cannot express — including H13's own exact
known failure. Explicit mapping table: R1 3/10, R2 9/20 requirements
provider-enforced; ALL requirements stay deterministic-validator-
enforced. One live capability test (nested array + boolean + nullable
string + enum) confirmed every construct actually used is genuinely
enforced on this route.

**Corpus**: the same 9 gate-passed items from the integrated probe
(H02 excluded by construction — it was that run's blocked item). D0/C0
not rerun.

**Executed: 18/18 calls (9 R1 + 9 R2), no stop, ~14 min.**

**Provider layer (A): 18/18 = 100% `provider_structurally_valid`** —
zero prose, zero truncation, zero shape mismatches. Answers "does flat
enforcement eliminate basic-shape failures" cleanly: yes.

**Deterministic layer (B): R1 9/9 valid; R2 7/9 valid.** The 2 R2
failures (`H03`, `H09`, 5 claims total) show the EXACT SAME shape as
H13's own original known failure ("support=unsupported requires >=1
problem") — confirmed live, exactly as the mapping table predicted this
un-expressible cross-field rule would still fail. **H13 itself recovered
incidentally this run** (R2 valid, `unsafe`) — explicitly NOT
attributed to Layer A (the schema can't express the rule it violated
before; this is the same kind of call-to-call variability already
documented twice for D0). Confirmed live, twice: `provider_structurally_
valid` + `validator_invalid` is a real, correctly-contained outcome —
never silently accepted.

**Semantics: no regression.** 6/7 valid pipelines still show
`unresolved_semantic_conflict` firing correctly; `H13` additionally
shows the existing `audit_unresolved` provenance-wrap behavior working
as designed. Verdicts: 6/7 unsafe, 1/7 ambiguous, 0 safe — consistent
with prior runs on this same real corpus.

**Before/after**: R2 valid 8/9 (integrated probe) → 7/9 (this pass) —
the cross-field-invariant failure did NOT shrink on this n=9, it moved
to different items (1 item/3 claims → 2 items/5 claims).

**FINAL CLASSIFICATION: B. NOT READY — MECHANICAL FAILURE RATE / SHAPE
STILL NEEDS WORK.** The basic-shape/prose/truncation class is fully
resolved (100%). The cross-field-invariant class (H13's shape) is
unresolved and didn't shrink on this small sample — a bounded, fail-
closed, non-silent, well-understood failure mode, but not yet meeting
the "no unresolved execution-contract failure" bar for READY. No
semantic regression (rules out classification C). No Stage C. No
prompt tuning. No v2.1. Full tables and hashes in the experiment doc's
`## B2 R1/R2 PARTIAL STRUCTURED-OUTPUT PROBE — EXECUTED, RESULTS
SCORED` section. **Stopping here, per instruction.**

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above) B2 R1/R2 EXECUTION-CONTRACT RECOVERY — STOPPED
## PRE-RUN, EXACT PROVIDER ENFORCEMENT CONFIRMED UNAVAILABLE — ZERO
## RECOVERY MODEL CALLS MADE

**No R1/R2 prompt/schema/parser change. No recovery calls executed —
stopped before any, per instruction, once the capability question was
answered.**

Direct inspection of `validate_r1`/`validate_r2` found R2's real
contract depends on EXTENSIVE cross-field conditionals (role constrains
legal support/declaration values; `declaration=undeclared` requires a
specific `problems` entry; `r1_agreement=override` requires
`override_rationale`; and — directly relevant — `support=unsupported`
requires >=1 semantic-problem value in `problems`, exactly the
invariant H13 violated in the completed integrated probe).

**One minimal live test call** (a toy `if`/`then` schema, same
`response_format: json_schema strict` mechanism that already enforced
C0's flat schema successfully) confirmed: **conditional schema
constructs are silently dropped on this route** — the model returned
plain prose instead of JSON, no error. Flat type/enum constraints work
(already proven for C0); cross-field conditionals do not. **Exact,
schema-preserving provider-level enforcement of R1/R2's real contract
is therefore confirmed unavailable** — not a model failure, not new
schema-invalid data, not evidence R1/R2's semantics are wrong. A
precisely bounded execution-route capability limit.

**Explicitly not substituted**: a narrower flat/type-only schema
(matching C0's own already-accepted reduced scope, leaving all cross-
field invariants to the unchanged validators) was identified as
achievable but deliberately NOT used here — that would answer a
different, weaker question than this recovery was preregistered to
answer, and blurring the two without a fresh preregistration was
avoided. **Zero recovery calls made. The 9 gate-passed candidates were
not rerun.**

**H13 status unchanged, NOT claimed repaired**: still the known pre-
existing R1/R2 mechanical compliance failure from the integrated probe.
No tool available this pass could have fixed it without changing R2's
semantics.

**A separate, NOT-launched future experiment identified**: "R1/R2
PARTIAL STRUCTURED-OUTPUT PROBE" — whether flat provider enforcement
reduces simple contract failures while the unchanged validators still
catch cross-field violations. A legitimately weaker question, not
designed further, not launched.

**FINAL CLASSIFICATION: B. NOT READY — EXECUTION CONTRACT STILL
UNRESOLVED**, with the qualification that the blocker is now precisely
understood and bounded, not open-ended. D0/C0/GATE integration remains
mechanically stable (unchanged from the integrated probe); R1/R2's
semantic-conflict layer remains confirmed functioning on 8/9 cases
(unchanged). No Stage C. No v2.1. No prompt tuning. Full detail in the
experiment doc's `## B2 R1/R2 EXECUTION-CONTRACT RECOVERY — STOPPED
PRE-RUN, EXACT PROVIDER ENFORCEMENT UNAVAILABLE` section.

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above) B2 D0/C0/R1/R2 INTEGRATED DEVELOPMENT PROBE
## EXECUTED — GATE CONFIRMED WORKING, SECOND INDEPENDENT true_detection
## FOUND, ZERO INTEGRATION FAILURES

**Architecture corrected before execution, per explicit user
correction**: R1 has NEVER accepted an externally-supplied proposition
set (confirmed by direct code inspection of `cj2_b2_v2_probe.py`) — it
always does its own independent, evidence-blind extraction from raw
text. D0/C0 function ONLY as a fail-closed pre-R1 GATE
(`compute_pipeline_gate`/`should_call_r1`, reused unmodified), never as
a proposition supplier. This probe tested exactly that gate — topology
`D0 -> C0 -> GATE -> [R1 -> R2]` — not proposition-set continuity across
stages (there is none, and none was invented).

**No D0/C0/R1/R2 prompt/schema change.** Execution-level only: (A) D0
MAX_TOKENS=16000 (carried forward), (B) C0 `json_schema` strict (carried
forward), (C) R1/R2's shared `MAX_TOKENS` global raised 5000→12000,
matching the already-executed "R2 capacity-recovery run" precedent
exactly. Same 10-item real corpus as before, no substitution. R1/R2
candidate+seed data extracted programmatically and cross-checked
field-for-field against the frozen corpus (50/50 match, zero
transcription drift).

**Executed: 38/38 calls (10 D0 + 10 C0 + 9 R1 + 9 R2), no stop, ~24.7
min, zero integration failures** (structurally verified: every gate-
pass item has exactly one R1/R2 result, every gate-block item has
none).

**The preregistered STRUCTURE held exactly (1 blocked, 9 pass) but the
preregistered ITEM did not — reported honestly, not reframed.** H03
(expected to block, per the completed recovery run) instead achieved
genuine D0 completeness this run — D0's fresh 33-claim output now
includes a new claim capturing the previously-omitted "discriminatory
asymmetry" half; C0 correctly said `complete` because nothing was
missing this time. This is D0 call-to-call variability, not a gate or
C0 failure.

**H02 was blocked instead — a SECOND independently confirmed genuine
`true_detection`, same failure shape as H03's, different item, different
run.** H02's `conceptual_shift` field is another single-segment "X -> Y"
arrow structure ("reviewer error in judgment -> environment-induced
precision artifact: ..."); D0's 23 claims capture only the Y half, and
C0 correctly caught the missing X half (verified directly — a
coincidental keyword match in an unrelated claim from a different field
does NOT rescue it). **Two independent occurrences of the identical
failure shape, across two separate runs, strongly suggests a systematic
D0 blind spot on `conceptual_shift`'s arrow/colon structure specifically**
— not acted on, logged for a future decision.

**R1/R2 on the 9 gate-pass items**: 8/9 fully valid pipelines, 1/9
(H13) R2 schema_invalid — reproducing the EXACT SAME pre-existing R1/R2
compliance shape already found once before on a different item (H09) in
an earlier regression, not a new failure class from the integration.
**All 8 valid pipelines resolved `unsafe`, and all 8 show at least one
`unresolved_semantic_conflict`** — R1/R2's existing frozen conflict
safeguard fired consistently on real material, exactly as designed;
its high rate here reflects these specific candidates' interpretive
density, not investigated further per instruction not to touch R1/R2
semantics.

**Interpretation**: D0/C0 earns its place as a GATE (confirmed twice
now, zero false alarms across both runs' full samples) — it does NOT
feed or improve R1's own proposition set, and that claim is not made.
Two independent fail-closed layers (the gate; R1/R2's own conflict
safeguard) both fired correctly without interfering with each other.
Mechanically stable (0 integration failures); the strongest evidence
yet for eventually considering Stage C integration, though that
decision is explicitly not made here.

**Confirmed: no D0/C0/R1/R2 prompt/schema edit, no D0->R1 claim-set
handoff invented, no corpus substitution, no parser broadening, no
v2.1, no Stage C, no Reader Lab material.** Full tables, traces (H02
gate-block trace + H03 non-block trace), and interpretation in the
experiment doc's `## B2 D0/C0/R1/R2 INTEGRATED DEVELOPMENT PROBE —
EXECUTED, RESULTS SCORED` section. **Stopping here, per instruction.**

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above) D0/C0 REAL-MATERIAL EXECUTION-ENVELOPE RECOVERY
## EXECUTED — BOTH EXECUTION FAILURES FULLY RESOLVED; FIRST-EVER
## CONFIRMED NATURAL TRUE_DETECTION

**No D0/C0 semantic revision.** Only two execution-level changes vs. the
transfer probe, both verified by object-identity in the static suite:
(A) `D0_MAX_TOKENS` 3000→16000 (rationale: transfer probe's successful
completions used 9,369-11,606 chars/22-27 claims; its 4 truncated ones
were cut off at 10,797-11,298 chars while still incomplete — 16000
gives >=5x margin, consistent with this project's own R2
MAX_TOKENS=12000 precedent); (B) C0 requests now carry `response_format:
json_schema (strict)` matching `validate_c0_schema`'s structural
contract exactly. **Investigated live before building anything**:
`response_format=json_object` was silently ignored on this route;
`json_schema` WAS enforced (verified with a trivial prompt, then two
end-to-end tests on real D0/challenge content). Same 10 natural + 4
challenge items, same prompts, same corpus — no substitution.

**Executed: 24/24 calls, no stop, ~5.5 min.** Full hash-verified
provenance.

**BOTH transfer-probe execution failures fully resolved:**
- **D0 truncation: 10/10 valid** (was 6/10) — the 4 previously-truncated
  items now complete fully (29-32 claims each).
- **C0 mechanical compliance: 14/14 = 100%** (was 9/14) — zero prose-
  preamble, zero truncation, on both arms.

**Challenge arm: 4/4 `detected_preregistered_omission`, 0 extra, 0
missed** — now on a fully mechanically-valid foundation (H16/H18 are
exact string matches to the preregistered target).

**Natural arm: 9/10 `correct_complete`, 1/10 a CONFIRMED GENUINE
`true_detection` — the first one in this entire two-probe research
program.** `H03`'s `conceptual_shift` field ("X → Y", one un-split
segment) had D0 claim only the SECOND half (Y) across all 32 claims —
the word "discriminatory" (from the omitted first half, X) appears
nowhere in D0's output. Coverage-satisfied, semantically incomplete —
exactly the shape the 2026-08-12 adversarial audit predicted, now
observed live and correctly caught by C0. Verified by direct
inspection (all 32 claims checked), not assumed.

**A pre-run caveat did NOT reproduce**: a validation test call showed a
different semantic conclusion under structured output than the
original diagnostic reading for the same item; in the official run
that item (`H02`) scored `correct_complete`, matching its ORIGINAL
transfer-probe reading — the specific worry (structured output
systematically distorts C0's conclusions) did not manifest as a
reproducible pattern, though the test used slightly different input
(old vs. new D0 claims) so this isn't a full resolution, just an
update.

**DECISION RULE: EXECUTION PROBLEM RESOLVED. SEMANTIC REVISION NOT YET
JUSTIFIED** — one confirmed omission, correctly caught by the
UNMODIFIED C0, is the architecture working as designed, not a defect;
a single instance isn't "repeatable" evidence for revising anything.
This is, if anything, the strongest evidence yet FOR the current C0
design, not against it.

**Confirmed: no D0/C0 prompt/schema edit, no corpus substitution, no
parser broadening, no v2.1, no R1/R2 change, no Stage C, no Reader Lab
material.** Full tables, hashes, and interpretation in the experiment
doc's `## B2 D0/C0 REAL-MATERIAL EXECUTION-ENVELOPE RECOVERY —
EXECUTED, RESULTS SCORED` section. **Stopping here, per instruction.**

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above) D0/C0 REAL-MATERIAL TRANSFER PROBE EXECUTED —
## CORE FINDINGS TRANSFER, BUT A NEW MAX_TOKENS TRUNCATION FAILURE MODE
## EMERGED ON BOTH D0 AND C0

**RL-2026-001 conflict caught and flagged before any corpus was built:**
the task's own suggested example cases (H08, H17, H14, H05, De Hooch/Z)
are literally RL-2026-001's 5 currently-live assigned candidate texts.
User chose to exclude all 5 entirely and require an explicit eligibility
audit table rather than inferring membership from fixture proximity.
**Eligibility audit** (`eligibility-table.json`) found a **clean pool of
14** real, already-exposed, development/not-held-out `cj2-fresh-batch-1`
candidates (H01,H02,H03,H04,H06,H07,H09,H10,H11,H12,H13,H15,H16,H18) —
well above the underpowered threshold, no padding needed. Split: **10
natural (all 5 candidate-reasoning fields each) + 4 controlled real-
material omission challenges** (single richest field each, scoped down
from all 5 -- stated explicitly, not hidden). D0/C0 prompts BYTE-
IDENTICAL to the completed first probe; parser is the recovery pass's
frozen normalizer, NOT broadened despite new failure shapes appearing.

**Executed: 24/24 calls, no stop, ~6.7 min.** Full hash-verified
provenance, same LOCAL/TRIDENT discipline as every prior B2 run.

**A genuinely NEW failure mode: MAX_TOKENS truncation, on BOTH stages.**
4/10 D0 calls (`H03,H09,H12,H13`) truncated mid-JSON — real 5-field
candidates need far more claims (22-27, vs. a synthetic max of 3) than
`D0_MAX_TOKENS=3000` (inherited unchanged, byte-identical to the
synthetic probe) can hold. Correctly recorded as genuine `call_failed`
(HTTP 200, real content, just incomplete) — the frozen normalizer
correctly leaves truncated JSON REJECTED, never coerced into "recovered."
**This cascades**: the same 4 items' natural-arm C0 calls, fed an empty
claim set, tried to honestly enumerate everything as missing across 5
dense fields and ALSO truncated, this time against `C0_MAX_TOKENS=2000`.
**A third new finding: C0's JSON-only compliance got WORSE on real
material** — 5 of 14 total C0 calls this pass (1 natural + all 4
challenge) show a full reasoning walkthrough before the JSON block,
vs. 2/12 in the synthetic probe — correctly, uniformly REJECTED by the
unbroadened normalizer, never recovered.

**ARM A (natural, 10 items):** 6/10 D0 calls recoverable and
structurally `valid` (0 omissions — matches the synthetic 8/8 finding,
smaller n). Of those, 5/6 C0 mechanically `correct_complete`; 1/6
(`H02`) mechanically `call_failed` (prose-preamble) but diagnostically
also concludes `complete`. **0/6 false_alarm anywhere — the item-8-
shaped non-propositional false-alarm class did NOT reproduce on any
real material this pass.** The 4 truncated items are marked
`CONFOUNDED_BY_HARNESS_INPUT_CORRUPTION` / secondary-truncation-
unrecoverable — never scored as a semantic category. **NATURAL
DETECTION SENSITIVITY STILL NOT OBSERVED** (0 omissions existed to
detect, restated per instruction).

**ARM B (controlled challenge, 4 items):** **0/4 mechanically
compliant** (all Class B). **Diagnostic-only reading: 4/4 identified
exactly the one preregistered target omission, zero extras** — the
same clean single-target detection signal as the synthetic probe,
transferring cleanly at the content level even as mechanical compliance
worsened. Explicitly NOT used to replace the mechanical (all-rejected)
result — reported side by side, per instruction.

**Interpretation, precisely bounded:** the core semantic findings that
DID produce usable data continue to look favorable (0 D0 omissions
where measurable; 0 false alarms; 4/4 challenge detection at the
content level) — but the harness/execution-level evidence (truncation
on both stages; worsening JSON-only compliance) is now strong enough
that **the more urgent open question is a token-budget/output-
discipline fix, not a semantic C0 prompt revision.** Not acted on this
pass. What remains genuinely unknown: true D0/C0 behavior on the 4
truncated items (unmeasured, not "probably fine"); whether the false-
alarm absence holds on a larger sample or on real material that DOES
contain citation/heading/rhetorical-transition shapes (this pool
doesn't); whether raising the token ceilings alone would fix truncation
without side effects (not tested).

**Confirmed: no D0/C0 prompt/schema edit, no parser broadening despite
new failure shapes, no v2.1, no Stage C, no Reader Lab data used/read/
polled (RL-2026-001 excluded by construction, its own progress untouched
and unwaited-for), no fix attempted for the two new truncation modes or
the worsened compliance — logged as open findings for the next
decision.** Full tables, hashes, and interpretation in the experiment
doc's `## B2 D0/C0 REAL-MATERIAL TRANSFER PROBE — EXECUTED, RESULTS
SCORED` section. **Stopping here, per instruction.**

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above) D0/C0 FIRST SEMANTIC PROBE — NARROWLY-SCOPED
## RECOVERY PASS COMPLETE (PARSE NORMALIZER + NATURAL-C0 INPUT-RECOVERY
## RUN, 8 NEW CALLS)

**No D0 or C0 prompt tuning this pass, per explicit instruction.** The
Attempt-2 results below are preserved exactly as executed — a
harness/execution defect (not a semantic one) confounded 4 of the
natural arm's 8 C0 calls, and this pass fixes that plumbing only.

**Exact format classification of Attempt 2's 6 `json.loads()`
failures** (not collapsed into one "markdown fence" bucket): **Class A
— pure JSON in one fence, nothing else outside — 4/6**, all D0
(`1_clean_simple`, `4_compound_coordination`, `5_attribution_embedded`,
`7_modality_assumption`); **Class B — fence preceded by 1109/794 chars
of substantive prose — 2/6**, both C0-challenge (`ch2_attribution_reversed`,
`ch4_modality_reversed`). Classes C (multiple blocks) and D (truncated)
had zero instances.

**New deterministic normalizer built and tested, not a permissive
parser**: `automation/cj2_b2_d0c0_output_normalizer.py` (SHA256
`a32d897bcb82dfab9084c9bd966e993da23025e18dd7d4673c3c33f5a156af0c`) —
recovers Class A only (exactly one fence, nothing substantive outside
it); Class B is REJECTED by construction, never silently accepted. 32/32
static checks pass, including direct execution against the real 6
Attempt-2 failures. No D0/C0 prompt, schema, corpus, or reference-
manifest file touched.

**Offline reparse (zero API calls) of all 20 Attempt-2 results**:
D0 recovery reported as two separate numbers — ORIGINAL MECHANICAL: 4
parsed / 4 parser-failed; RECOVERED SEMANTIC (Class A, via the
normalizer): **8/8 complete, 0 omissions**, matching the reference
exactly. Controlled-C0 recovery reported as three separate numbers —
mechanical 2/4; parse-recovered under the normalizer STILL 2/4 (`ch2`/
`ch4` correctly stay rejected, Class B); diagnostic-only manual reading
(explicitly not the normalizer, not used for scoring) shows all 4/4
detected the exact preregistered omission, WITH the formatting-
compliance caveat that 2 of those 4 only reached that content by
violating the JSON-only contract — not hidden, not papered over.

**The 4 originally-confounded natural-arm C0 results are re-labeled
`CONFOUNDED_BY_HARNESS_INPUT_CORRUPTION`** — never `miss`/`false_alarm`/
`true_detection`/`correct_complete`. Reparsing old D0 output can't repair
what C0 actually saw at call time, so a new, narrowly-scoped experiment
was run instead:

**NATURAL C0 INPUT-RECOVERY RUN — EXECUTED, 8/8 calls, no stop.** Froze
the 8 recovered D0 claim sets from Attempt 2 (hashed,
`frozen-recovered-d0-claims-v1.json` SHA256
`a1658230894dd9819cb8c8de0fea0ca3025c8cb5d08a85c6a5a551d2f855d0eb`) as
the sole input; new harness `cj2_b2_d0c0_natural_c0_recovery.py`
imports the ORIGINAL, unmodified C0 prompt/schema/`build_c0_user`/
`_call` — zero D0 calls, zero challenge-arm calls, enforced structurally
(68/68 static checks pass). Preregistered
(`cj2_b2_d0c0_natural_c0_recovery_preregistration.json`, SHA256
`8f3d6e84a67025bbaa125d21c4773b9178ee420b0437e19d4834ff6a37bea24b`):
only runtime input plumbing changed, explicitly. Executed on trident,
full bundle hash-verified byte-identical before and after, ~15s
wall-clock, all 10 output artifacts hash-verified on copy-back.

**Result: 7/8 `correct_complete`, 1/8 `false_alarm`, 0 true_detection, 0
miss, 0 schema_invalid, 0 call_failed.** Item 8 (the non-propositional
control) reproduces Attempt 2's EXACT false-alarm shape — same two
spans (`appendix B` citation, "the following section addresses
limitations" rhetorical transition) — across two independent calls at
`temperature=0.0`. Because D0 was confirmed 8/8 complete (twice now),
the natural arm produced ZERO `true_detection`/`miss` opportunities, as
anticipated — the only informative natural-arm C0 signal from this
probe is its false-alarm rate, 1/8 (12.5%).

**Interpretation, precisely bounded:** reproducing across 2 identical-
input calls establishes self-consistency at temp 0, NOT generalization
to other citation/rhetorical wording — that would need new, differently
-worded items, not collected this pass. Whether C0's false-alarm
behavior is "systematic enough to justify a future semantic revision" is
explicitly marked NOT YET DECIDABLE from n=1 item. The challenge arm's
Class-B compliance violation (2/4 calls) remains completely unaddressed
— no prompt fix attempted. **Confirmed: no D0/C0 prompt edit, no
schema/corpus/reference-manifest edit, no v2.1, no Stage C, no Reader
Lab data, no re-run of the challenge arm, no selective re-run of only
the 4 previously-confounded items (all 8 natural items re-run
uniformly).** Full tables, hashes, and interpretation in the experiment
doc's `## B2 D0/C0 FIRST SEMANTIC PROBE — NARROWLY-SCOPED RECOVERY PASS`
section. **Stopping here, per instruction — no C0 prompt revision this
pass, even having now confirmed the false-alarm shape twice.**

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above — the Attempt-2 facts below remain true and
## unchanged, now with the 4 confounded C0 results explicitly
## re-labeled above, not overwritten here) D0/C0 FIRST SEMANTIC PROBE
## EXECUTED (REVISION 2, 20 CALLS: 8 D0 + 8 C0-NATURAL + 4 C0-CHALLENGE) —
## 2 EXECUTION ATTEMPTS, RESULTS SCORED

Reconstructed state from disk after a prior session's context ran out
mid-preparation: revision 2 (a controlled C0 challenge arm, added to
solve a denominator problem — if D0 decomposes all 8 natural items
completely, C0 has zero known omissions to detect) was already fully
written to disk (`challenge-corpus-v1.json`, `reference-manifest-v1.json`,
`preregistration-first-probe.json`, `pre-run-identity.json`) but never
narrated in this file or the experiment doc. Verified precisely rather
than trusting the handoff: all JSON strictly parses (no duplicate keys),
all `.py` files compile and import, all 10 hashes in both the
preregistration and pre-run-identity records independently recomputed
and matched exactly, `expected_call_count.maximum_total` unambiguously
`20` everywhere (no stale "16" survived), and all 6 static/preflight
suites re-run clean with zero explicit failures.

**Attempt 1: CONFIG_FAILURE, stopped correctly after 1 call.** CLIProxyAPI
now enforces `api-keys` auth (key rotated 2026-08-07 after the already-
recorded public-repo exposure incident); this harness's `_call()`, like
every prior B2 `_call()`, defaults to an empty key. `HTTPError 401` on
the very first call → `classify_call_outcome()` correctly returned
`config_failure` → the run stopped immediately, 1 call made, error
persisted. A genuine execution-configuration failure, not a probe
defect — closed as its own attempt, not silently retried, per the
preregistration's own stop-rule text.

**Attempt 2: EXECUTED, COMPLETE, 20/20 calls, no stop.** Fresh scratch,
same hash-verified bundle, the service's own required key (found in its
own `config.yaml`, not a third-party secret) supplied as an env var for
that one process only — never printed, persisted, or committed anywhere
this session wrote. All 20 calls completed in ~70s; all 22 output
artifacts hash-verified local vs. trident, byte-identical.

**Found live: a harness JSON-extraction bug, logged separately from the
semantic findings** (same discipline as the FIRST REFERENCE PROBE's own
JSON-extraction bug above) — 4/8 D0 natural calls wrapped valid JSON in
a markdown fence, and 2/4 C0 challenge calls prefixed prose before a
valid trailing JSON block; both mechanically recorded as `call_failed`
per the taxonomy (correct — an EXPERIMENT RESULT, not a config failure).
Diagnostic-only re-parse (no new API calls) showed all 6 were actually
schema-valid. Consequence: the 4 affected D0 items' own natural-arm C0
tests are CONFOUNDED — `run_probe()` feeds C0 an empty claim set when
D0's parse fails, so C0 "correctly" flagged those as missing, but this
says nothing about C0's real detection ability, since D0 never actually
omitted anything there.

**Headline result 1 (natural arm, 8 items):** D0's TRUE performance
(diagnostic-only fence-stripping applied for interpretation, not scoring)
is 8/8 complete, zero omissions, including the two hardest-designed
cases (item 6's full 3-proposition causal-link reading; item 8's
non-propositional material excused with exactly the reference manifest's
expected reason codes). This reproduces the denominator problem
revision 2 was built to solve — zero natural D0 omissions existed for
C0 to be genuinely tested against.

**Headline result 2 (natural arm, genuine finding, NOT confounded):**
item 8 — the direct positive-control test for non-propositional handling
— is a real C0 FALSE ALARM. D0 handled it perfectly (0 spurious claims,
3/3 correct reason codes). C0, given that same correct input, invented
two "missing propositions" out of a citation/reference line and a
purely rhetorical transition sentence — exactly the material the
reference manifest's own `boundary_notes` says has "zero genuine
propositions expected." A single data point, not a measured rate, but a
clean, unconfounded miss on the direct control.

**Headline result 3 (controlled challenge arm, 4 items):** C0 detected
the exact preregistered omission in 4/4 items at the content level (2/4
mechanically clean, 2/4 recoverable only via the preamble-extraction
above) — zero extra/unpreregistered omissions proposed in any case. This
is the first live confirmation C0 can catch the specific "claim spans
the whole segment but represents only one of two propositions" omission
shape the 2026-08-12 adversarial audit proved D0's own bookkeeping
cannot catch.

**Interpretation, stated precisely:** C0 shows a real, demonstrated
incremental capability (4/4 challenge detection) AND a real, demonstrated
false-alarm failure mode (item 8) in the same small probe — neither
finding should be read without the other. Same-model, no-independence
caveat unchanged (`FIRST_PROBE_MODEL_DECISION`: "separate evidence-blind
coverage audit," never "independent model adjudication"). Both corpora
are single-sentence/single-segment by design — no claim of generalization
to real multi-paragraph B2/CJ2 candidate material. Token counts were not
captured this pass (`_call()` discards the `usage` field) — a real gap
in the cost/latency research question, not filled in retroactively.

**Confirmed: no semantic tuning of either prompt after seeing results,
no v2.1, no Stage C, no cross-publisher/held-out material, no Reader Lab
data used/read/polled (RL-2026-001 untouched), no selective rerun of the
6 fence/preamble-affected items despite knowing their true content, no
`cj2-stage-b2-v2` frozen artifact touched, no D0/C0 prototype module
modification, no production/Cloudflare/D1 access.** Full result tables,
hashes, and the complete interpretation in the experiment doc's `## B2
D0/C0 FIRST SEMANTIC PROBE — REVISION 2 ... + EXECUTED, 2 ATTEMPTS —
RESULTS` section. **Next real decision, not made this pass:** whether a
harness-level fix (tolerant JSON extraction) is worth making before any
second D0/C0 probe, and whether C0's item-8-shaped false-alarm risk
warrants a prompt revision on a larger synthetic sample — neither
designed or drafted this pass.

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above — the revision-1 preparation facts below remain
## true and unchanged) D0/C0 FIRST SEMANTIC PROBE PREPARED (PROMPTS +
## HARNESS + PREFLIGHT
## WRITTEN) — STOPPED BEFORE ANY MODEL/API CALL, PER EXPLICIT INSTRUCTION

Named explicitly `B2 D0/C0 FIRST SEMANTIC PROBE`, NOT `v2.1`. Took the
prior pointer's own "next real step" (below): wrote the actual D0 and C0
prompts, a probe harness, an 8-item development-only corpus, a new static/
preflight suite, and a full preregistration record — **zero model/API
calls made against either prompt, this pass or ever, against this
topology.**

D0 prompt (`automation/.probe_fixtures/cj2-b2-d0c0-first-probe/frozen_prompts/cj2-stage-b2-d0.txt`,
SHA256 `98813045450db8f56267d7eeb1b66a3504a99748fb03c7bac8332c838fd1674d`)
and C0 prompt (same dir, `cj2-stage-b2-c0.txt`, SHA256
`745d6b7e11bd97a3ca20e7d52d479a63a0c0106b64283b14b8f0b6b62f948c3d`) are
generic and evidence-blind by construction: no B2 development-corpus
examples, no H08/H17/H14 semantics, no persona/engine/disability
vocabulary, no R1/R2 terminology, output schemas matching
`cj2_b2_d0_prototype.py`/`cj2_b2_c0_prototype.py`'s existing versions
exactly (both prototype modules imported read-only, unmodified, hashes
confirmed unchanged). Harness
`automation/cj2_b2_d0c0_first_probe.py` (SHA256
`2c373944342a89e7ce99b851881d961ec1b4a27f3746f9c14faef5ec507f8f07`)
builds both stages' user messages, reuses the existing deterministic
validators unmodified, defines its own standalone `_call()` (documented
reason: `cj2_b2_v2_probe.py`'s own MODEL/MAX_TOKENS constants are
cosmetic, not load-bearing — its real `_call()` reads
`cj2_b2_probe_v1_4_1`'s module globals at runtime, not its own; a real
observation about existing code, not acted on elsewhere this pass), and
`main()` refuses to run, matching `cj2_b2_v2_probe.py`'s own precedent.

**Probe corpus deliberately contains ZERO real B2/CJ2 development-corpus
material and ZERO overlap with the currently-live RL-2026-001 round, by
construction, not by argument** — 8 items, 3 freshly authored, 5 reused
verbatim from `cj2_b2_d0_adversarial_coverage_audit.py`'s existing
purely-synthetic `CASES` dict, both provenance claims checked
programmatically. H08's real field and H17's real RL-2026-001 sentence
were BOTH explicitly considered and REJECTED for this corpus, even though
reusing real B2 fixture text as a diagnostic-only input has precedent
elsewhere in this project (the H08 structural test; C0's own H17-shaped
static-test case) — precisely because both are currently live as
RL-2026-001 items, and this probe's "no Reader Lab data" guarantee is
meant to be verifiable by construction. RL-2026-001 itself was not read,
polled, or otherwise touched.

**New static suite `automation/cj2_b2_d0c0_first_probe_static_tests.py`
(SHA256 `ffdd4c7c0abd02002b72722734c18f8384247051ef988663aaa834f06cef0c21`)
— ALL CHECKS PASS, zero API calls.** Re-ran every pre-existing suite
unmodified too: D0 static tests PASS, H08 structural test PASS (6/6),
adversarial coverage audit CONFIRMED/PASS, C0 static tests PASS, frozen
B2-v2 static tests PASS (untouched). One self-correction recorded rather
than hidden: this pass's own first draft of the new suite initially
banned bare English words ("claims", "support", "safe", "importance",
"evidence excerpt") as leaks, which false-failed on the prompts' correct,
deliberate use of R1's own established "you do NOT receive X" scope-
boundary convention — fixed to check for schema-KEY-shaped leakage
(`"word":` patterns) instead of bare-word presence, which is the real
risk the instruction was protecting against.

Full preregistration record (hashes, model/call params
`openrouter/claude-sonnet-4.6`/temperature 0.0/D0 max_tokens 3000/C0 max_
tokens 2000/timeout 120s/no retries, expected call count 16 = 8 D0 + 8
C0, `dataset_purpose: "development"`, predefined outcome taxonomy, 7
research questions, 5 known risks including the PROBE-ONLY deviation
where C0 is called even after a D0 structural failure — which has no
production analogue):
`automation/.probe_fixtures/cj2-b2-d0c0-first-probe/preregistration-first-probe.json`.
Full narrative:
`.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md`'s
`## B2 D0/C0 FIRST SEMANTIC PROBE — PREPARED, NOT EXECUTED` section.

**Confirmed: no model/API calls, no `v2.1`, no Stage C, no cross-
publisher/held-out material, no Reader Lab data used/read/polled, no
`cj2-stage-b2-v2` frozen artifact touched, no D0/C0 prototype module
modified, no production/Cloudflare/D1 access.** Next real step, not
taken this pass: execute the 16 calls against the corpus, with explicit
authorization, and score against the predefined outcome taxonomy.

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the entry above) 2026-08-12: D0 REVISED TO OPTION B (ID-BASED
## SEGMENT ACCOUNTING) + C0 INDEPENDENT COVERAGE AUDIT ADDED — TOPOLOGY
## NOW D0→C0→R1→R2 — STILL NO MODEL/API
## CALLS, NO PROMPTS WRITTEN

Acted on the adversarial-audit finding below: **surface coverage is
necessary but not sufficient for proposition completeness — accepted,
not disputed.** Revised the plan per explicit correction: do NOT gate
the semantic checker on a `>=90%` span-coverage heuristic, since that
heuristic is derived from the same signal already shown insufficient (a
100%-spanning claim can still omit a proposition).

**D0 revised (`D0_SCHEMA_VERSION` 0.1→0.2):** `segment_ids` is now a
REQUIRED, explicit field on every claim/`non_propositional` record
(Option B) — no more overlap-fraction heuristic anywhere in the
coverage decision. A new `validate_segment_id_consistency()` check
requires declared `segment_ids` to equal EXACTLY the real geometric
overlap of a claim's resolved span — catches bookkeeping fabrication,
still says nothing about semantic completeness. Documented explicitly,
in the module's own docstring: "SEGMENT ACCOUNTING DOES NOT ESTABLISH
SEMANTIC COMPLETENESS. It is structural bookkeeping only." Re-ran the
adversarial audit against the new mechanism — **confirmed the same 6/6
gap still holds**, exactly as predicted when Option B was accepted as
bookkeeping-only, not a semantic fix.

**C0 added** (`automation/cj2_b2_c0_prototype.py`,
`C0_SCHEMA_VERSION="c0-prototype-0.1"`): independent, evidence-blind
proposition-coverage audit, one question only — "does the D0 claim set
represent every proposition asserted in the candidate text?" Output
`complete`/`missing_proposition` + `missing_items[]`. Structurally
(not just documentation-ally) barred from ever classifying factuality
or revising D0's claim set — a recursive banned-key scan rejects any
output containing role/support/declaration/factual_dependency/etc. or
claims/revised_claims/d0_claims keys. C0's proposed missing items are
diagnostic only this pass — deliberately NOT merged back into D0's
claim set (that's a separate, later research question). New
`compute_pipeline_gate()` combines D0's own structural result with C0's
semantic result: a `D0_COVERAGE_FAILURE` from EITHER
`detected_by` (`segment_accounting` or `c0_semantic_audit`) blocks R1
via `should_call_r1()` — confirmed it can never silently become
`valid`. Same-model-vs-independence decision documented explicitly
(`FIRST_PROBE_MODEL_DECISION`): same model, separate blind calls,
explicitly NOT claimed as statistical independence — matches this
project's own R1/R2 precedent.

**Static-test results:** D0 suite 36/36, H08 structural test 6/6
(unchanged conclusion, now reported as `D0_COVERAGE_FAILURE
[segment_accounting]`), adversarial audit 6/6 (re-confirmed under the
new mechanism), **C0 suite 29/29** — including a diagnostic-only
H17-shaped case (real, already-selected RL-2026-001 sentence) that
concretely demonstrates C0's necessity: D0 alone reports `valid` for a
claim that honestly spans the whole sentence while representing only
half its content; only a correctly-functioning (simulated, not run) C0
catches it. Frozen `cj2_b2_v2_static_tests.py` re-confirmed 51/51,
untouched.

**Topology is now D0 → C0 → R1 → R2 — up to 4 model calls per candidate
before Stage C, reported plainly, not hidden or pre-optimized** (the
cost-cutting thin-segment heuristic was explicitly rejected per
instruction, pending real data on whether C0 is even worth its cost).
Full first-probe design (candidate shapes, metrics: D0 omission rate,
C0 detection rate, C0 false-alarm rate, coverage-failure frequency,
claim-count expansion, cost/latency — no thresholds pre-chosen) in the
experiment doc's `## B2 NEXT-STRUCTURE PROTOTYPE — D0 REVISED (Option
B) + C0 ADDED` section. **Confirmed: no D0/C0 prompt written, no
model/API calls, no `v2.1`, no Stage C, no cross-publisher/held-out
material, RL-2026-001 untouched (used only as a diagnostic text
fixture, same discipline as the real H08 reuse), no merge/
reconciliation logic between C0 and D0 built.** Next real step, not
taken this pass: write the actual D0 and C0 prompts and run the small
development-material probe.

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the pointer above — the adversarial-audit facts below remain true
## and unchanged) ADVERSARIAL COVERAGE AUDIT — SURFACE COVERAGE CONFIRMED
## INSUFFICIENT ALONE, ONE MORE STRUCTURAL LAYER NEEDED BEFORE ANY D0
## PROMPT — STILL NO MODEL/API CALLS

**Before writing a D0 prompt, ran an adversarial audit of the coverage
validator itself** (`automation/cj2_b2_d0_adversarial_coverage_audit.py`,
static only). Tested: does a D0 claim whose `exact_surface_span` covers
a WHOLE segment, but whose `atomic_claim` semantically represents only
one of that segment's 2-3 real propositions, pass coverage? **Confirmed
YES, 6/6 generic adversarial cases** (coordination "but", causal
"because", attribution+embedded content, relative clause, comparison
"while", modality/assumption) — the validator reports `valid` in every
case, silently losing the un-mentioned proposition. **Not hypothetical:**
the real H17 sentence already selected for `RL-2026-001` segments into
exactly ONE unit (em-dash, not semicolon) while bundling two assertions
— nothing currently stops a real D0 call from claiming only half of it
and passing cleanly.

**Precise correction to the prior pass's framing:** "surface coverage"
(what's implemented) is NOT "proposition completeness" (the design's
actual goal) — surface coverage catches whole-segment omission (the
real H08 shape, re-confirmed this pass: R1's real claims jump cleanly
from seg5 to seg7/8, zero claim of any kind touches seg6 — a clean skip,
not an embedded-alongside-another-proposition case, so the existing
H08 structural test's shape stands unchanged) but provides ZERO
protection against a proposition hidden inside an over-broad span
sharing a claimed segment.

**Decision: B — coverage contract needs one more structural layer
before a model probe is meaningful.** Smallest justified addition
(optimized for making silent loss observable, not for elegance):
(1) adopt ID-based segment accounting (`segment_id → proposition_ids[]`)
instead of span-overlap-fraction heuristics — cheap, removes ambiguity,
do regardless, but a bookkeeping improvement, not a semantic fix; (2)
add a narrow, evidence-blind, independent coverage-check restricted to
segments D0 leaves "thin" (one claim/non-prop record covering ≥90% of
the segment) — asks only `complete`/`missing_proposition` + span, never
role/support/factuality. **Neither is written or run this pass** — both
remain design-only. Full audit, all 4 options assessed, in the
experiment doc's `## B2 NEXT-STRUCTURE PROTOTYPE — ADVERSARIAL COVERAGE
AUDIT` section. **Confirmed: no D0 prompt written, no model/API calls,
no `v2.1`, RL-2026-001 untouched, no cross-publisher material, all prior
39/39 static tests + this pass's 6/6 adversarial checks still green
(zero regressions to `cj2_b2_d0_prototype.py` itself).**

## B2 NEXT-STRUCTURE — (PRIOR POINTER, superseded-in-status-language-only
## by the adversarial audit above — the prototype/static-test facts below
## remain true and unchanged) PROTOTYPE IMPLEMENTED + STATIC-VALIDATED
## (39/39 PASS, INCLUDING H08 STRUCTURAL VERIFICATION) — NO MODEL/API
## CALLS, NOT v2.1

Proceeded from the design below to an EXPERIMENT-ONLY deterministic
implementation, working identity **B2 NEXT-STRUCTURE PROTOTYPE —
D0/R1/R2** (deliberately not `v2.1`). New files, all uncommitted:
`automation/cj2_b2_d0_prototype.py` (D0 schema, segmentation, span
resolution reusing `cj1_v3_anchor_resolver`, the coverage validator,
fixed-claim handoff check shared by D0→R1 and R1→R2),
`automation/cj2_b2_d0_static_tests.py` (33 generic-invented checks, all
PASS), `automation/cj2_b2_d0_h08_structural_test.py` (6 checks, all
PASS — the one file using real H08 text, kept separate on purpose).

**The point of this pass, verified directly rather than assumed:** built
H08's real `interpretive_inference` field text, hand-authored a D0 claim
set covering all 8 of its deterministically-segmented units EXCEPT the
one containing the real target proposition R1 actually missed in both
live regressions, and confirmed the coverage validator raises
`coverage_incomplete` naming exactly that segment, with zero false
flags on the other 7. **This shows the checking mechanism would have
caught H08's real failure shape — it does not show a real D0 model call
will decompose correctly, since no model was run.**

Segmentation decision resolved (not left open): sentence-level, further
split on semicolons; colons deliberately NOT a split point (confirmed
against H14's own real sentence that colon-splitting would fragment a
single proposition); compound "and"/"but" sentences deliberately not
split (documented, accepted granularity-mismatch limitation, not
solved). `non_propositional` marking is reported by rate/reason-code,
never auto-trusted as correct. Fail-closed priority: `schema_invalid` >
`span_resolution_failed` > `coverage_incomplete` > `valid` — kept
structurally distinct from R1/R2's own `unresolved_semantic_conflict`.

Full detail: `.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md`
`## B2 NEXT-STRUCTURE PROTOTYPE — D0/R1/R2`. **Confirmed: no D0 prompt
written, no R1/R2 model call, no frozen `cj2-stage-b2-v2` artifact
touched, no Stage C, no cross-publisher material, RL-2026-001 responses
not inspected (round still awaiting both reviewers).** Next real step,
not taken this pass: write an actual D0 prompt and run it live to see
whether a real model's output, checked by this same validator, reduces
`coverage_incomplete` relative to R1 alone.

## B2 NEXT-STRUCTURE DESIGN — D0/R1/R2 (2026-08-12, design only, no code/API calls)

Diagnosed H08 and H14 as two DIFFERENT problems that must not be
conflated or fixed by the same mechanism: **H08** is a decomposition-
coverage miss — R1 is currently the first/only place decomposition
happens, the complete candidate sentence reached it, and it never
produced a `claim_id` for the target proposition at all, invisible to
every existing check (all of which operate on the claims R1 *did*
produce). **H14** is R2 support-strength run-to-run variability (role
agreement both runs; support differs between Regression #1 and the
recovery run under identical frozen input/temperature=0.0) — a separate,
deferred question; a D0 stage does nothing for it, and it must not be
cited as evidence for or against D0.

Proposed topology (design only): `candidate → D0 (atomic proposition
extraction, evidence-blind, no factual/role judgment) → R1 (proposition
contract, now scope-narrowed to the FIXED D0 claim set, cannot decompose)
→ R2 (unchanged) → deterministic conflict+coverage layer`. Central
question addressed head-on per instruction: **"extract every claim" as a
prompt instruction is explicitly rejected as insufficient** — that is
what R1 already does unconditionally today (v2 Revision 2 already
removed the one bypass trigger that could have caused this), and H08
proves a real omission survives it anyway. Proposed real fix: deterministic,
code-computed segment-level coverage accounting — independently
sentence-segment each source field (not model self-report), and verify
every segment is either covered by an `exact_surface_span` (resolved via
the same exact/normalized-match logic already built for
`auditor_evidence`) or explicitly marked `non_propositional` with a
reason; anything covered by neither is a deterministic `coverage_incomplete`
fail-closed state, reusing the existing `unresolved_semantic_conflict`-style
routing rather than inventing a new verdict. An independent-model
backstop checker was considered and explicitly deferred (recommend
testing the deterministic mechanism alone first). Honest new-risk list
recorded: coverage-gaming (span attached without genuine correct scoping),
sentence/clause granularity mismatch, `non_propositional`-marking abuse
(the D0 analogue of R2's `override_rationale` risk), correlated D0/R1
bias if same model, and the new deterministic layer itself needing the
same static-test rigor as the existing R1/R2 consistency layer before any
live run. Adds a THIRD model call per candidate — reported plainly, not
minimized. Several decisions explicitly left open (segmentation
granularity, same-model-or-not for D0, whether `coverage_incomplete`
needs its own `effective_status` or reuses an existing one, whether D0
claims must be final-granularity). Full design:
`.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md`
`## B2 NEXT-STRUCTURE DESIGN — D0/R1/R2`. **No prompts written, no
harness code, no API calls, no v2.1 assigned, no Stage C, no
cross-publisher material.**

## B2 v2 — (HISTORICAL, superseded-in-status-language-only, see pointer
## above) 30-CANDIDATE REGRESSION EXECUTED, RESULT: FAIL — DOMINATED BY A
## MAX_TOKENS TRUNCATION DEFECT, NOT SEMANTICS

**Explicitly authorized and executed since the entry below.** Ran on
trident via localhost CLIProxyAPI (local repo canonical, trident
execution-only — same methodology as v1.2/v1.3/v1.4.1; the earlier "don't
use trident" instruction was user-clarified to be scoped to the
design/static-test pass, not a permanent ban). 60 calls (30 R1 + 30 R2),
0 transport failures, hashes verified byte-identical before/after copy,
scratch deleted after local verification.

**THE DOMINANT FINDING: 17/30 candidates (56.7%) failed at R2** — all with
an identical signature (output truncated at ~5,000-token ceiling, same
schema violation). One systemic `MAX_TOKENS=5000` insufficiency for R2's
per-claim-verbose schema, correlated with R1's claim count, not 17
independent content failures. Not fixed or retried this pass, per
instruction.

**Seven targets: 0 REPAIRED / 3 FLAGGED_NOT_RESOLVED (H17, H05, H03) / 4
MISS (H08, H09, H14, De Hooch/Z), for three different reasons** — 2 MISS
purely from the truncation defect (R1 caught both correctly); H08 is a new
failure mode (R1 never extracted the target proposition from its own
source field, invisible to field-level coverage validation); H14 is
another new pattern (R1/R2 agree on role, R2 judges support more
permissively than expected — not a hedge failure, not a false-safe).

**R1/R2 disagreement rate: 88 of 212 valid claims (41.5%) are
R1-catches/R2-disagrees** — far above an edge case. The deterministic
conflict layer prevented a false-safe on every single one, without
exception (2 candidates' whole verdict flips from v1.4.1's safe to v2's
ambiguous purely because of this rule). Zero instances of the opposite
"conservative escalation" direction. The architecture works exactly as
designed; a 41.5% flagged-not-resolved rate under this exact prompt
pairing is itself a central finding.

Full artifacts + hashes: `automation/.probe_fixtures/cj2-b2-v2-regression/`.
Full narrative: `.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md`'s
`## B2 v2 — 30-CANDIDATE REGRESSION RUN EXECUTED` section. `cj2-stage-b2-v1.4.1`
and `cj2-stage-b2-v2` (prompts/harness) both unmodified. No tuning after
results. No Reader Lab data used. No Stage C run. **Next real decision,
not made this pass: raise MAX_TOKENS before any further B2-v2 evaluation
is meaningful, and separately whether the 41.5% conflict rate + the two
newly-observed failure modes warrant a v2.1 design pass.**

## B2 v2 — (HISTORICAL, superseded by the entry above) STRUCTURAL HARNESS
## IMPLEMENTED, STATIC TESTS PASS, ZERO API CALLS MADE

**B2: v2 structural implementation in progress — parallel track, does not
block or wait on READER LAB above.** Proceeded from Revision 2's frozen
design to implementation. R1/R2 prompts written
(`automation/.probe_fixtures/cj2-b2-v2/frozen_prompts/cj2-stage-b2-v2-r1.txt`
/ `-r2.txt`); harness built
(`automation/cj2_b2_v2_probe.py` — R1/R2 schemas, validators, the new
Layer 1.5 consistency computation reading only `empirical_dependency`/
`role` per Correction 5's exhaustive table, the corrected effective-
verdict layer with the `unresolved_semantic_conflict` branch, bidirectional
migration-report utilities); deterministic test suite built and RUN,
**51/51 checks PASS, zero API calls, zero network access**
(`automation/cj2_b2_v2_static_tests.py` — covers concrete/interpretive/
hedged/institutional/individual/causal/measurement/population/identity-
restatement cases, missing-field/illegal-enum/claim-set-mismatch schema
violations, the R1-true/R2-interpretive fail-closed conflict, the
R1-false/R2-factual escalation, and the real distinction between
`audit_unresolved` (ambiguous) and the unchanged `declaration=undeclared`-
forces-`unsafe` rule, which the test suite's own first draft got wrong and
which was caught and fixed during this pass, not left as a latent bug);
preregistered acceptance specification written
(`automation/.probe_fixtures/cj2-b2-v2/acceptance-matrix-v2-preregistered.json`
— carries forward the exact same 7 H08/H09/H17/H05/H14/H03/De-Hooch-Z
targets from the v1.4.1 regression verbatim, adds a 3-outcome
`REPAIRED`/`FLAGGED_NOT_RESOLVED`/`MISS` scoring vocabulary so a claim R1
catches but R2 still misses is reported as its own diagnostic category
rather than folded into a flat pass/fail, carries the two global
anti-overcorrection guards forward UNCHANGED, adds new v2-only diagnostics
— consistency rates, self-report-mismatch rate, identity-restatement rate
— with explicitly no threshold chosen). Full file-by-file record in the
experiment doc's `## B2 v2 — IMPLEMENTATION` section.

**No API call made against either R1 or R2 prompt. No 30-candidate
regression run (the harness/corpus paths are wired but `main()` refuses to
execute). No cross-publisher material spent. No Stage C. No production
wiring touched. `cj2-stage-b2-v1.4.1` (FAIL) unmodified.** Next real step,
not taken this pass: an explicitly authorized live run against the
30-candidate corpus, scored against the preregistered matrix above.

## FROZEN DECISIONS (do not reopen by drift)
- WHY WE WRITE (commit `01339ce`) is the shared publication doctrine.
  KEEP, scope-corrected: entitled to claim "improved or preserved the four
  personas under the then-current planning architecture," NOT "works
  under the final intended CripMinds pipeline" (that architecture is now
  known to include the contamination above). Do not rerun the 12+12
  doctrine experiment — after Phase 1.6, a small smoke confirmation
  suffices (see phase-1.6 doc's closing section).
- Historical persona territories are hypotheses, not canon — target
  architecture (perceptual engine / motive / affinity / risk / texture)
  is Phase 3 work, not started. Audit: `.claude/persona-architecture-audit.md`.
- Phase 1.5A persona audit is done; implementation waits for Phase 3.
- Phase 1.5B final model-seat decision waits until after Phase 1.6
  grounding — both reviewers in that experiment judged drafts whose
  factual substrate was already contaminated by an ungrounded planner.
- Production `temperature` stays unset/`None`; only probes pin it (0.9).
- Repetition judge (Phase 5) and ending judge (Phase 7): shadow-only
  first, backtested, never auto-block/auto-rewrite until real
  false-positive data justifies it.
- `engagement.db`/`disability_findings.db` living inside the repo checkout
  remains a known, mitigated risk (safe sync wrapper + daily backups);
  moving them out is deferred infrastructure hardening.
- CJ-2 remains future competitive persona reframing ("what does each
  persona's engine expose, which reframe is strongest" — not topic
  ownership), not scheduled.
- `_LENGTHS`/evidence-budget restructure, testimony extraction/weighting,
  Siri Sage's VOICE ANCHOR / any other persona prompt, thesis-timing /
  correction-discipline rules: do not touch until their own dedicated
  experiment.

## PAUSED EXPERIMENTS — what resumes after grounding
- **Fable review-seat ROI (Phase 1.5B)**: full 3-layer blind evaluation +
  causal safety audit done, model-seat decision deferred. Resumes as a
  small grounded review-seat follow-up once Phase 1.6 lands, not a repeat
  of the 8-case experiment. Record: `.claude/experiments/fable-review-roi-2026-08-10.md`.
- **WHY WE WRITE**: KEEP decision stands; resumes only as the small smoke
  confirmation described above. Record: `.claude/experiments/why-we-write-2026-08-10.md`.

## OPEN INFRASTRUCTURE ISSUES (not blocking Phase 1.6)
- `_fable_update_state`'s own docstring says "Post-publish: Fable reads
  the article and updates the persona's state.json... Called after a
  successful publish" -- found live 2026-08-11 while building
  `lineage_persistence_test.py` that this is NOT what the real code does:
  `generate.py` calls it at "Step 3b-0" (line ~908), BEFORE the reviewer/
  executor block, meaning persona state can evolve from a PRE-REVIEW
  draft, not the final published article. Unrelated to Phase 1.6
  grounding, not fixed -- logged here per explicit instruction not to
  derail this phase with it.
- CLIProxyAPI's dead Codex/ChatGPT-Plus OAuth account (expired 2026-07-20)
  can poison routing for ALL requests, not just its own — a `systemctl
  --user restart cliproxyapi` fixed it same-day. Still needs: remove/
  refresh the dead account, or file upstream that per-account refresh
  failures shouldn't affect other accounts.
- Real production article shipped degraded on 2026-08-10 09:03:24: Fable
  review returned `revise` but all four rewrite fallback attempts failed
  (403s/500/monthly key limits), so the article shipped unrevised and
  without images. Open question, not yet answered: was this stamped
  `pipeline_degraded` correctly, given `generate.py`'s Step 3b
  image-generation failure doesn't appear to be tracked by
  `_degraded_stages` at all — possibly undercounting the real failure
  surface. Not investigated further; check against the published
  article's frontmatter when reliability work has capacity.
- `--retry-failed` exists as general `phase_probe` infrastructure but was
  deliberately not used to patch `baseline-attempt-1` — a contiguous clean
  run was required instead, to avoid mixing external-condition windows in
  data meant to detect subtle writing differences.
- Rest of cripminds' backlog (judge-panel generation, persona evolution,
  shadow-check promotion, CJ-2, Stage B/D-E) stays in
  `.claude/audience-engagement-tasklist.md`, untouched.

## HISTORICAL RECORDS (full detail, not condensed)
- `.claude/experiments/phase-1.6-source-grounding-2026-08-11.md` — Phase 1.6
  full implementation history: 7 adversarial offline review rounds, live
  API controls, two corrected rounds of live acceptance controls (tamper +
  hostile-executor-input).
- `.claude/experiments/why-we-write-2026-08-10.md` — Phase 1 WHY WE WRITE
  3-topic + Pixel Nova 4th-persona validation, full 4-persona decision.
- `.claude/experiments/fable-review-roi-2026-08-10.md` — Phase 1.5B
  harness, 8-case run, 3-layer blind evaluation, safety audit that found
  the Phase 1.6 blocking finding.
- `.claude/persona-architecture-audit.md` — Phase 1.5A six-category
  persona matrix and territory-ownership bugs.
- `.claude/2026-08-10-engagement-db-incident.md` — Phase 0's
  `engagement.db` incident, fully recovered/closed.
- `.claude/audience-engagement-tasklist.md` — rest of the backlog, untouched by this roadmap.
