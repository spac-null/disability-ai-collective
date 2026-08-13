# Crip Minds Reader Lab — Worker (live in production)

**If you're reading this after months away: normal operation is
`https://lab.cripminds.com/admin` in a browser — sign in with your
Cloudflare-authenticated email, not a terminal.** See "Admin control
plane" below for what that surface does. Everything past this point is
either that surface's own internals, or the CLI/API paths that exist for
automation and emergencies only.

Deployed to `lab.cripminds.com` (Cloudflare Workers + D1, EU
jurisdiction). See `../.claude/reader-lab-v0-design-2026-08-12.md` for
the full design and history, and this file's own sections below for what
exists today and how to recover it without this conversation.

## Operational recovery — the whole workflow in one place

**As of 2026-08-12, normal Reader Lab operation requires ONLY
`https://lab.cripminds.com/admin` — no privileged Claude/Cloudflare
session, no CLI, no D1 query, ever, for routine use.** Round completion,
research export, calibration analysis, evidence, and a next-round draft
all happen automatically, server-side, the moment reviewers finish —
nobody has to notice or run anything.

```
1. Open https://lab.cripminds.com/admin
2. Create or import a round
3. Review it (exactly as a reviewer will see it)
4. Freeze & Publish
5. Wait for reviewers — the dashboard shows live progress
6. The dashboard automatically detects completion — no action needed
7. Open Results to read the raw judgments, or Calibration to see the
   automatic evidence map (agreement/disagreement/contested, never a
   computed "winner")
8. Once analysis finishes, a next-round draft is prepared automatically
   (or the system says NEEDS_ELIGIBLE_CANDIDATES if there's nothing
   eligible yet) — review it in Rounds and Freeze & Publish yourself,
   same as any other round. Nothing publishes without you.
9. Download the research handoff JSON any time, drop it straight into
   .claude/reader-lab-handoff/ — nothing to redact, nothing to clean up.
   This remains available as backup/audit tooling — the calibration
   pipeline no longer depends on this manual step happening at all.
```

A research session can still author a draft manifest
(`reader-lab/rounds/drafts/RL-YYYY-NNN.json`) with no credentials at all,
for Jascha to import in step 2 — that path still works exactly as
before, it's just no longer the only way to get a round started.

**Privileged ops / wrangler / direct D1 access is needed ONLY for:**
deployments, migrations, Cloudflare Access/Trident configuration, and
production incidents (e.g. an export or calibration run stuck in an
error state that the in-app Retry button somehow can't fix). It is
never needed to detect a round finishing, generate a research export,
run calibration analysis, prepare a next-round draft, check reviewer
progress, or publish a round —
all of that is now fully self-service from `/admin`.

Machine `/ops/*` routes (`ADMIN_TOKEN`/`EXPORT_TOKEN`) still exist for
automation/emergency/debugging use, including a read-only
`GET /ops/rounds/:id/export` — but nothing in the normal workflow above
ever touches them.

If `/admin` ever won't load or won't authenticate, that's a Cloudflare
Access problem, not a Worker problem — check Zero Trust → Access →
Applications → "lab" in the dashboard before touching any code.

## Auth model (read this before testing)

1. An admin creates an invitation → gets back a one-time plaintext
   token. Only its SHA-256 hash is ever stored (`invitations.token_hash`).
2. The reviewer visits `GET /invite/<token>` **once**. If valid, the
   Worker mints a random session id, stores only *its* hash
   (`sessions.session_id_hash`), sets it as a `Secure; HttpOnly;
   SameSite=Lax` cookie, and 302-redirects to `/session`.
3. From then on, the invitation token never appears in any URL, request
   body, response body, or log — only the session cookie does, and the
   browser (not any JS on the page) is what attaches it.
4. Every reviewer-facing request (`/session`, `/api/session`,
   `/api/response`) re-resolves the reviewer from that cookie **and**
   re-checks the invitation's `revoked`/`expires_at` fresh, every time —
   revoking an invitation cuts off an already-open browser tab
   immediately, not just future logins.

## Admin control plane (`/admin`) — the normal way to operate Reader Lab

**Normal human operation is through `/admin`.** The CLI/curl routes further
down this README (`/ops/invitations`, `/ops/items`, `/ops/assignments`,
`/ops/status`, `/ops/export`, `/ops/publish`, all gated by
`X-Admin-Token`) are for automation, emergencies, and debugging — not the
default workflow. If you're Jascha, six months from now, with no memory of
how this was built: open `https://lab.cripminds.com/admin`, not a terminal.

### What it does

Five screens, nothing more (see the design doc's admin-control-plane
section for the full spec this implements):

- **Dashboard** — current round, reviewer progress, what needs your
  attention, "New round" / "Import draft" actions.
- **Rounds** — list + detail. A round moves through
  `draft → review → frozen → published → completed`. Freezing locks the
  content (computes and records a manifest hash); publishing is the one
  moment anything is actually written to `items`/`assignments`. The
  detail page for a draft/frozen round shows every question exactly as
  a reviewer will see it, plus admin-only internal note/provenance
  fields that never reach the reviewer-facing routes.
- **Results** — raw per-reviewer judgments, grouped by question, tagged
  `agreement` / `disagreement` / `single_judgment`. Never computes or
  displays a "winner" — majority is never treated as truth (unchanged
  from the design doc's original rule). A completed round can be given
  a research disposition (`development_reference` / `contested` /
  `hold_for_later`) — this never touches the raw response rows.
- **Reviewers** — pseudonymous reviewer IDs, active/revoked, practice
  status, progress. Create/revoke/reactivate. Raw invitation tokens are
  shown exactly once, at creation — same rule as the legacy CLI route.
- **Import** — paste a manifest JSON (the same shape a research session
  already authors under `reader-lab/rounds/drafts/RL-YYYY-NNN.json`,
  including the older fully-annotated shape RL-2026-001.json itself
  used — see `canonicalizeManifest` in `src/publish.js`). Validates
  structure, recomputes and checks content hashes, flags warnings
  (duplicate content, a claim that already exists in production), and
  previews every question exactly as a reviewer will see it. Nothing is
  written until you explicitly choose **Save as draft** or
  **Freeze & Publish** — a validation error always blocks both.

### Automatic completion + research export (no privileged session needed)

A round transitions `published → completed` by itself, the instant every
assignment across every required reviewer has an answer — this happens
inside the same request that records the last reviewer's response
(`handleResponse` in `src/index.js` calls `maybeCompleteRound`, an
atomic, idempotent conditional `UPDATE ... WHERE status = 'published'`,
so a replayed/concurrent request can never double-complete a round or
double-fire what happens next). The moment a round completes, a
canonical, credential-free research export is generated in the
background (`ctx.waitUntil`, so the reviewer's own response never waits
on it) by the one shared service, `buildResearchExport` in
`src/researchExport.js`.

The round's detail page (and the dashboard's "Current round" card) then
shows:

```
COMPLETE
Research export ready
[ Download research handoff ]
```

The download is served by the Worker directly from the frozen export row
— predictable filename (`RL-2026-001-completed.json`), no `ADMIN_TOKEN`/
`EXPORT_TOKEN` ever touches the browser, Cloudflare Access is the only
authentication involved. The file is immediately usable by a
credential-free research session — drop it straight into
`.claude/reader-lab-handoff/`, no redaction step, ever: the export
service only ever reads from `rounds`/`items`/`assignments`/`responses`
— it has no code path that could reference `invitations` or `sessions`
(the two tables that hold anything credential-shaped), so there is
nothing to accidentally leak regardless of what a future edit elsewhere
in the file gets wrong.

**Immutability.** A `ready` export is a frozen snapshot — `buildResearchExport`
never recomputes or overwrites one once generated (calling it again on an
already-`ready` round is always a no-op, which is also what makes
completion-hook retriggers, manual retries, and the cron sweep below all
safe to run redundantly). If generation ever needs to happen again for a
genuine reason (a bug in the export format itself, say), that's a
deliberate, explicit, infrequent administrative action, not a UI
button: `DELETE FROM research_exports WHERE round_id = '...'` via
`wrangler d1 execute --remote`, then use the in-app Retry button.

**If export generation fails** (the background attempt threw for any
reason), the round stays `completed` — reviewer responses are never
rolled back or affected — and the UI shows:

```
EXPORT ERROR — Retry available
[ Retry export ]
```

Clicking Retry calls the exact same shared service again. A low-frequency
cron job (`scheduled()` in `src/index.js`, hourly — see `wrangler.toml`'s
`[triggers]`) is a second, independent safety net: it finds any completed
round without a `ready` export and retries it automatically, so even an
un-clicked Retry button eventually self-heals.

A machine-readable equivalent exists for automation/debugging:
`GET /ops/rounds/:id/export` (`X-Admin-Token` or `X-Export-Token`, calls
the identical shared service) — but nothing in the normal human workflow
ever needs it.

### One publication path, not three

Whether a round was authored in the admin UI, imported from a research
manifest, or published in one shot via the machine `/ops/publish` route,
all three call the exact same functions in `src/publish.js`
(`canonicalizeManifest` → `validateManifest` → `freezeRound` →
`publishRound`). This is what replaces the original RL-2026-001
publication path (a hand-run `wrangler d1 execute` against interpolated
SQL, which is exactly the kind of ad hoc write this exists to retire).
Every value reaches D1 through a bound parameter — never string
interpolation — which is also what makes multi-line and Unicode content
survive byte-for-byte (verified directly: see the local test pass below).
`publishRound` writes items + assignments + the round's `published`
status + an audit-log row in a single `env.DB.batch()` call (one D1
transaction, all-or-nothing), then re-queries to confirm the expected
number of assignments actually landed. Publishing an already-published
round returns the existing receipt instead of writing again
(double-publish is a no-op, not an error and not a duplicate).

### Auth model — Cloudflare Access, not ADMIN_TOKEN in a browser

`/admin` and `/admin/api/*` are gated by Cloudflare Access
(`src/access.js`), never by `ADMIN_TOKEN`. `ADMIN_TOKEN` is never sent
to, stored in, or reachable from any browser context for these routes.
Access verification is fully independent of Cloudflare's own edge check
(defense in depth): the Worker fetches the team's JWKS
(`https://<team-domain>.cloudflareaccess.com/cdn-cgi/access/certs`),
verifies the `Cf-Access-Jwt-Assertion` header (or `CF_Authorization`
cookie) as a real RS256-signed JWT, and checks `aud`/`exp`/`iss` itself —
this was unit-tested directly (self-signed key, valid/expired/wrong-aud/
wrong-issuer/tampered-signature/forged-different-key/malformed-token, all
seven behaving correctly) since there was no live Access instance to test
against this pass (see below).

**Current status: DEPLOYED.** Cloudflare Zero Trust was enabled and a
self-hosted Access application ("lab") created for this Worker. Verified
directly against the live Access API (`accounts/.../access/apps/...`),
not assumed:

- Team domain: `blue-king-f6e0` (`blue-king-f6e0.cloudflareaccess.com`)
- Application AUD: `a115fbf5da8905eb07a6c8f1277e1983792d969e5f26f4f9268cff0df38c0c36`
- One `allow` policy, `include` = exactly two specific emails, no
  `exclude`/`require` rules, no broad "everyone" rule
- Identity provider: Cloudflare's own built-in login only (no separate
  IdP/OTP added)
- `ACCESS_TEAM_DOMAIN` set via `wrangler.toml` `[vars]` (not a secret —
  it's the same value any unauthenticated visitor to `/admin` already
  receives in Cloudflare's own redirect); `ACCESS_AUD` set via
  `wrangler secret put`

**A real path-scoping issue was found and fixed during deployment,
worth recording here rather than just in a commit message.** Cloudflare
Access's self-hosted app model protects a path *and every subpath
beneath it*, with no way to carve out an exception. The Access app was
initially scoped to `lab.cripminds.com/admin` (+ `/admin/*`), which — as
confirmed by directly testing `/admin/status`, `/admin/export`, etc. in
production — also intercepted the **legacy machine routes**, which used
to live under `/admin/*` too. There was no Access-side fix (no "protect
this path but not its children" option exists), so the legacy machine
routes moved to **`/ops/*`** instead — a prefix that shares nothing with
`/admin`, so Access's subpath behavior can never sweep them in again.
See the route list above and the "Admin usage" section below, which
already reflect `/ops/*`.

Never set `ACCESS_DEV_BYPASS` anywhere except a local, gitignored
`.dev.vars` file (see "Local development" below) — it is not read from
`wrangler.toml` or any deploy step in this project, so it cannot reach
production by accident, but it would defeat Access entirely if it ever
did.

## Calibration orchestrator — completed rounds analyze themselves

The moment a round's research export is ready (see "Automatic
completion + research export" above), a Cloudflare Workflow instance
(`CalibrationWorkflow`, `src/calibrationWorkflow.js`) starts automatically
— created idempotently by `armCalibrationRun`
(`src/calibrationOrchestrator.js`), keyed on
`round_id + export content hash + workflow version`, so a replayed
trigger or the hourly cron reconciliation sweep can never produce a
second run for the same round. No privileged session has to notice a
round finished or kick off analysis by hand.

The Workflow creates a claimable `calibration_jobs` row and durably waits
(`step.waitForEvent`, no compute consumed while waiting) for a **private,
Tailscale-only Trident daemon** (`calibration/runner/calibration_runner.py`)
to poll for it, execute it, and submit the result back over
`/ops/calibration/jobs/*` — authenticated by its own narrow
`CALIBRATION_RUNNER_TOKEN`, never `ADMIN_TOKEN`/`EXPORT_TOKEN`. That
token can claim/heartbeat/complete/fail a calibration job and nothing
else — it cannot create/revoke a reviewer, publish a round, or touch a
response/export; verified directly against production, not just
asserted (see the design doc's `## 25.10`).

Two job types, both versioned/hashed/documented in
`calibration/workflows/`:

- **`analyze-human-round-v1`** — turns a completed round's frozen export
  into a structured per-item evidence map (`agreement_state`,
  `reference_strength`, `disposition`, `machine_comparison` against this
  round's already-known B2 reference labels). Deterministic — direct
  transcription of categories this project already established in prose
  (design doc `## 20.4`/`## 14`) — except one optional, narrowly-scoped,
  banned-word-filtered model-generated `notes` field that can never
  affect any of the deterministic fields. Never computes a "winner,"
  never treats agreement as ground truth.
- **`prepare-next-round-v1`** — given the analysis, drafts (never
  publishes) a next round from an explicit, server-side
  `calibration_candidates` eligible pool — see
  `calibration/candidates/README.md`. That pool starts and remains
  **empty** until a deliberate, separate research decision seeds it;
  until then this reports `NEEDS_ELIGIBLE_CANDIDATES` rather than
  inventing a candidate, and independently fails closed (twice — once
  in the Workflow, once in the runner) if any `held_out_evaluation`
  material ever appears in that pool.

`/admin`'s **Calibration** section shows the current round, the
workflow's state, an evidence summary, a simple timestamped history, and
the next action in plain language — with a **Retry** button for a
`failed` run (creates a fresh run/instance from scratch; analysis is
versioned/recomputable, never treated as immutable the way a research
export is). Failure is bounded and safe: two attempts per job type
before a run is marked `failed`; raw responses/exports are never
affected by a failed or retried analysis.

**Deploying/updating the runner:** see
`calibration/runner/README.md` for the full first-time-install and
update procedure (systemd, secrets file layout, health checks). The
canonical source is this repo — Trident's checkout is pinned to an exact
commit SHA read from
`/srv/secrets/cripminds-calibration/deployed-commit-sha.txt` by the
service's own wrapper script (`git fetch` + `git checkout --detach
<sha>`, refusing to start rather than silently falling back to `main` if
the pin file is missing content or the commit can't be checked out) —
never left tracking a moving branch. Deploying a new runner version is
exactly: update that one file, then `sudo systemctl restart
cripminds-calibration-runner`.

## Calibration policy — what's automatic, and who can change it (`## 26`)

`/admin` → **Policy** shows the active, versioned calibration policy and
lets Jascha create a new version (every past run stays interpretable
under whichever version actually governed it — nothing is ever edited in
place). `/admin` → **Dashboard** shows the resulting automation state per
category and a merged "Action required" list that says **"No action
required."** in plain text whenever nothing needs him. Full design:
`../.claude/reader-lab-v0-design-2026-08-12.md` `## 26`. In one line per
category, as of this policy version: round construction and analysis are
always automatic; existing-reviewer assignment and additional review are
automatic when the policy says so (the latter needs a configured
reviewer count, or it reports `NEEDS_POLICY_CONFIGURATION` rather than
guessing one); round publication defaults to `shadow_automatic` (the
system computes and records what it *would* publish, but a human still
clicks Publish); candidate/fine-tune experiments are infrastructure-ready
but not built; production promotion is always human-only, by a fixed
constraint no policy setting can change.

## B2 → Reader Lab candidate bridge (`## 27`)

`calibration_candidates` — the pool `prepare-next-round-v1` selects
from — now has a real write path: `POST /ops/calibration/candidates`
(`X-Calibration-Runner-Token` or `X-Admin-Token`), or `/admin` →
**Candidates** as a visibility/import-fallback screen. The moment
ingestion adds an eligible candidate, any calibration run stuck at
`NEEDS_ELIGIBLE_CANDIDATES` resumes itself — no "retry" click needed
unless that genuinely fails. `analyze-human-round-v2` additionally
computes `role_alignment`/`support_alignment`/`overall_relation` per
item (only when reviewers agreed) — `machine_comparison` keeps its
original, role-only meaning for compatibility. Full design:
`../.claude/reader-lab-v0-design-2026-08-12.md` `## 27`.

## What "going live" requires, step by step

1. **A scoped Cloudflare API token.** Create a new token (not the
   existing n8n key — its scope for Workers/D1 is unverified) with
   `Account.Workers Scripts:Edit`, `Account.D1:Edit`, and
   `Zone.DNS:Edit` for the `cripminds.com` zone only.
2. `npx wrangler login` (or `CLOUDFLARE_API_TOKEN=... wrangler whoami`
   with the token from step 1).
3. `npx wrangler d1 create cripminds-reader-lab` — copy the returned
   `database_id` into `wrangler.toml` (currently a placeholder).
4. `npx wrangler d1 execute cripminds-reader-lab --remote --file=./schema.sql`
   — applies the schema to the real (not local) D1 instance. Do this
   once, before the first deploy.
5. `npx wrangler secret put ADMIN_TOKEN` — generate a long random value
   yourself (e.g. `openssl rand -hex 32`); this gates every `/ops/*`
   route (the legacy machine surface — see "Admin control plane" above
   for the visual `/admin` surface, which uses Cloudflare Access
   instead). Do not reuse it anywhere else, and never put it in
   `wrangler.toml`, `--var`, or shell history.
6. `npx wrangler deploy` — deploys the Worker to a `workers.dev`
   subdomain first. Confirm the full invite → practice → real → thank-you
   flow works there (with a throwaway pilot item) before touching DNS.
7. Only after step 6 is verified: add the custom domain / route in
   `wrangler.toml` (commented out today) and add the corresponding DNS
   record in the Cloudflare dashboard for `cripminds.com` — a new
   subdomain record (`lab.cripminds.com` proposed), not a change to the
   existing apex or `www` records that serve GitHub Pages.
8. Only after DNS is live and re-verified: create real invitations and
   send the two pilot links.

None of steps 1–8 should happen without a separate explicit go-ahead —
this README documents the path, it doesn't authorize walking it.

## Local development

```bash
cd reader-lab-worker
npx wrangler d1 execute cripminds-reader-lab --local --file=./schema.sql
npx wrangler d1 execute cripminds-reader-lab --local --file=./migrations/0001_calibration_rounds.sql
npx wrangler d1 execute cripminds-reader-lab --local --file=./migrations/0002_admin_control_plane.sql
npx wrangler d1 execute cripminds-reader-lab --local --file=./migrations/0003_research_export.sql
npx wrangler dev --local --port 8787
```

`wrangler dev --local` runs entirely on your machine against a local D1
replica — no Cloudflare account, no network egress. It automatically
reads `ADMIN_TOKEN` from `.dev.vars` (gitignored, create it yourself —
see `.dev.vars` isn't checked in; a one-line
`ADMIN_TOKEN=<anything-for-local-testing>` is enough). Never put a real
production admin token in `.dev.vars`.

To exercise `/admin`/`/admin/api/*` locally without a real Cloudflare
Access setup, add `ACCESS_DEV_BYPASS=1` to the same `.dev.vars` file —
this line must never exist in `wrangler.toml`, a `wrangler secret`, or
any committed file; `access.js` only honors it as an env var, and this
project's own deploy steps never set it. Remove it from `.dev.vars`
before testing the real fail-closed (503) behavior.

## Admin usage (v0 — curl, not a UI)

The routes below are the **legacy/machine path** — automation, emergency
use, and debugging. The normal way to operate Reader Lab is
`/admin` (see "Admin control plane" above).

Create a reviewer + invitation link:

```bash
curl -s -X POST http://localhost:8787/ops/invitations \
  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{}'
# => {"reviewer_id":"reader_...","token":"...","invite_url_path":"/invite/..."}
# The token is returned once, plaintext. Copy it now — only its hash is stored.
# Full link to send the reviewer: https://lab.cripminds.com<invite_url_path>
```

Revoke an invitation (cuts off any open session immediately):

```bash
curl -s -X POST http://localhost:8787/ops/invitations/revoke \
  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"reviewer_id":"reader_..."}'
```

Create an item (never a held-out evaluation case for the pilot — see the
design doc's pilot protocol):

```bash
curl -s -X POST http://localhost:8787/ops/items \
  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "source_snapshot": "The clinic saw a 12% rise in appointments after the new signage went up.",
    "candidate_sentence": "The new signage made the clinic more welcoming to patients.",
    "dataset_bucket": "pilot"
  }'
```

Assign items to one or more reviewers independently:

```bash
curl -s -X POST http://localhost:8787/ops/assignments \
  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"reviewer_ids":["reader_...","reader_..."],"item_ids":["ril_...","ril_..."]}'
```

Check completion status (no tokens/hashes/contact info returned):

```bash
curl -s http://localhost:8787/ops/status -H "X-Admin-Token: $ADMIN_TOKEN"
```

Export raw responses (real only, by default):

```bash
curl -s "http://localhost:8787/ops/export" -H "X-Admin-Token: $ADMIN_TOKEN"
```

Publish a complete round manifest in one shot (automation/emergency use —
this is the machine equivalent of the admin UI's Import → Freeze &
Publish; both call the exact same `src/publish.js` functions, so this is
no longer a separate, ad hoc write path):

```bash
curl -s -X POST http://localhost:8787/ops/publish \
  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"manifest": { "round_id": "RL-2026-002", "dataset_purpose": "development", "reviewer_ids": ["reviewer_parent_a"], "items": [ {"slot": 1, "source_snapshot": "...", "candidate_sentence": "..."} ] } }'
```

## Read-only access for other sessions/collaborators (EXPORT_TOKEN)

`/ops/status` and `/ops/export` — and only those two routes — also
accept a second, narrower credential: `X-Export-Token: $EXPORT_TOKEN`.
Anyone holding `EXPORT_TOKEN` can read pilot status and raw responses,
but cannot create/revoke invitations, create items, or create
assignments — those routes check `ADMIN_TOKEN` only, never
`EXPORT_TOKEN`. Set it the same way as `ADMIN_TOKEN`:

```bash
wrangler secret put EXPORT_TOKEN
```

Give `EXPORT_TOKEN` (not `ADMIN_TOKEN`) to a session/collaborator that
only needs to read results — e.g. a research session doing analysis, or
anyone checking pilot progress. Keep `ADMIN_TOKEN` reserved for whoever
is actually approving new reviewers, items, or rounds.

```bash
curl -s "https://lab.cripminds.com/ops/status" -H "X-Export-Token: $EXPORT_TOKEN"
curl -s "https://lab.cripminds.com/ops/export" -H "X-Export-Token: $EXPORT_TOKEN"
```

## Testing the reviewer flow with curl (cookie jar)

```bash
TOKEN=$(curl -s -X POST http://localhost:8787/ops/invitations \
  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')

curl -s -c /tmp/rl-cookies.txt -o /dev/null -D - "http://localhost:8787/invite/$TOKEN"
# note the Set-Cookie + 302 Location: /session

curl -s -b /tmp/rl-cookies.txt http://localhost:8787/api/session
# cookie-authenticated — no token in the URL anywhere from here on
```

## Regression check — legacy `/admin/*` paths must never come back as a second API

The machine routes used to live under `/admin/*` before the path-scoping
fix described in "Admin control plane" above moved them to `/ops/*`. If
anyone ever reintroduces a route under `/admin/*` other than the exact
`/admin` page and `/admin/api/*`, it risks either (a) becoming invisibly
protected by Cloudflare Access, breaking machine/automation use, or worse
(b) if Access's app config is ever changed without matching care,
becoming an unintended second, less-scrutinized entry point next to the
real one. Re-run this after any routing change in `src/index.js`:

```bash
# Against production — every one of these must be intercepted by
# Cloudflare Access (302 to blue-king-f6e0.cloudflareaccess.com) or 404,
# never a 200/401 from the Worker's own admin logic:
for p in /admin/status /admin/export /admin/items /admin/invitations /admin/assignments /admin/publish; do
  curl -s -o /dev/null -w "$p -> %{http_code}\n" -X POST "https://lab.cripminds.com$p"
done

# Against a fresh local `wrangler dev --local` (no Access involved at
# all) — every one of these must be a plain 404, proving the Worker code
# itself doesn't route them, not just that Access happens to be in front:
for p in /admin/status /admin/export /admin/items /admin/invitations /admin/assignments /admin/publish; do
  curl -s -o /dev/null -w "$p -> %{http_code}\n" -X POST "http://localhost:8787$p" -H "X-Admin-Token: $ADMIN_TOKEN"
done

# The real /ops/* equivalents must still work:
curl -s http://localhost:8787/ops/status -H "X-Admin-Token: $ADMIN_TOKEN"
```

Last run 2026-08-12 (post-deploy close-out pass): all six legacy paths
returned 302 in production and 404 against a clean local instance; the
`/ops/*` equivalents responded correctly in both.

## Practice items

Seed 3–4 practice items via `/ops/items` with `is_practice: true`,
`practice_explanation`, and `practice_correct_answer` set — using
invented examples, never real held-out fixtures (per the design doc and
this pass's explicit audit — none of H03/H05/H08/H09/H14/H17/De Hooch-Z/
cross-publisher material may be used, disguised or not).

## What this Worker deliberately does not do

- No aggregation, no consensus computation, no "who's right" logic —
  `/ops/export` is raw rows only. Agreement/disagreement tagging is a
  separate, manual, later step, per the design doc's Section 14.
- No cross-reviewer visibility anywhere in the reviewer-facing routes.
- No write path exists for a reviewer to answer an item not assigned to
  them (`item_not_assigned`, 403).
- No general-purpose CMS — the admin control plane (`/admin`, see above)
  is deliberately five focused screens (dashboard/rounds/results/
  reviewers/import), not a generic content editor. Still no consensus
  computation anywhere in it — Results shows raw judgments and an
  `agreement`/`disagreement` tag only, never a computed "winner."
- No CAPTCHA/Turnstile/third-party analytics in the reviewer experience.
