# Crip Minds Reader Lab v0 — Design (2026-08-12)

Status: **DESIGN + reviewer-facing prototype only. No backend, no persistence,
no deployment.** Access-control/hosting decision is open — see
`## OPEN DECISION` below. Do not link this from the public site, do not add
real invitation tokens, do not populate with held-out evaluation cases,
until that decision is made and a real backend exists.

Prototype location: `reader-lab-prototype/` at repo root — plain standalone
HTML/CSS/JS, **excluded from the Jekyll build** (`_config.yml` `exclude:`),
not linked from anywhere, safe to open directly in a browser for review.
It is a click-through of the reviewer experience with fake local data
(`localStorage`), not a working product.

---

## 1. Purpose

Crip Minds' CJ-2/B2 research (`cj2-competitive-reframing-design-2026-08-11.md`)
has repeatedly needed one thing it cannot produce for itself: a judgment
about a piece of text that comes from a person who wasn't shown the
model's own answer, wasn't primed by which bug the team is currently
chasing, and didn't compare notes with anyone else first. Every existing
"human" label in that research (`human-review-labels-v1.json`,
`human-ai-assisted-adjudications-v1.json`) is explicitly annotated as
**not independent** — Jascha judged, with a model helping interpret or
formulate the label. That's useful diagnostically. It is not reference
data.

Reader Lab v0 exists to start accumulating the thing that's actually
missing: small amounts of **genuinely independent human judgment**,
collected slowly, from people who trust Jascha enough to spend three
minutes on a small task, with no audience requirement and no crowd.

## 2. Non-goals (explicit, so scope doesn't creep)

- Not crowd voting, not a public benchmark, not a leaderboard.
- Not a training signal. Nothing a reviewer submits ever automatically
  changes a prompt, a model, a routing decision, or the Mind Engine. See
  `## 15. GOVERNANCE — no automatic feedback loop` — this is the one rule
  in this document that must never be relaxed by a future version without
  a deliberate, documented decision.
- Not judging category-jump quality, persona selection, engine quality,
  disability theory, CJ architecture, originality, or overall article
  quality. v0 asks exactly one question: **does this sentence claim
  something the source doesn't establish, or is it a reading of the
  source?**
- Not a big platform. If v0 works, later versions get proposed — this
  document does not pre-design them.

## 3. What a reviewer sees vs. what the research needs

| Reviewer-facing (plain language) | Research label (never shown) |
|---|---|
| "The source supports this" | `source_established` (a supported factual dependency) |
| "This is a reading of the source" | `interpretive_only` |
| "This adds something the source doesn't establish" | `unsupported_factual_dependency` |
| "I'm not sure" | `uncertain` |

Reviewers never see: CJ-1, CJ-2, B2, R1, R2, "factual_dependency",
"interpretive_only", "semantic conflict", "schema_invalid", regression
fixtures, prompt versions, engine/persona names, or routing logic. The
onboarding copy names the general problem ("the boundary between an
interpretation and a claim that needs evidence") without naming the
system that has the problem.

## 4. Reviewer flow

```
invitation link (opaque token)
  → short welcome (first visit only)
  → assistance declaration (first visit only, one-time checkbox)
  → practice mode (first visit only, 3–4 invented examples, explained)
  → session: item 1 of N (N = 3–5)
  → item 2 of N
  → ... 
  → thank-you screen
```

Practice repeats only if the reviewer asks, or after a major task-version
change (`task_version` bump — see schema). A reviewer who already did
practice skips straight to a session on later visits.

Each session is short by design: 3–5 items, target 2–4 minutes.
Reviewers get many small sessions over time, not one long one — the
invitation system needs to support "3 items today, 4 next week, 5 another
time" without re-onboarding each time.

## 5. Public wording (Crip Minds voice)

Voice reference used: `MANIFESTO.md` and `editorial-lens.md` — plain
vocabulary, sentence economy, warm but unpadded, no lecturing, no
throat-clearing, respects the reader's time.

### First visit

> **Crip Minds Reader Lab**
>
> Sometimes a piece here draws on a source, and somewhere along the way
> a reading turns into a claim. We want to get better at seeing exactly
> where that happens.
>
> You'll read a short passage and one sentence written from it. Then you
> tell us what kind of sentence it is. No specialist knowledge needed —
> just your own read.
>
> A session takes a few minutes. You'll never see more than 5 items at
> once, and you can come back another time for more.
>
> One thing that matters: please answer on your own. No AI, no search,
> no asking someone else. Your independent read is the whole point.

Continue → assistance declaration:

> Before you start: **please make these judgments yourself** — not with
> ChatGPT, a search engine, or someone else's opinion. If you're ever
> unsure, "I'm not sure" is a real, useful answer.
>
> [ ] I'll answer on my own.
>
> [Start practice]

### Practice intro

> **First, a few practice rounds.**
>
> These don't count — they're just so the four choices make sense before
> you see the real ones. We'll tell you why after each one.

### Practice explanation copy (after each practice answer — plain, brief)

- Source establishes it: *"The passage states this directly, so the
  sentence just reports it."*
- Reading of the source: *"The sentence draws a conclusion or frames the
  passage a certain way, but it doesn't need a new fact to be true — it's
  an interpretation."*
- Adds something unestablished: *"The sentence depends on something —
  a cause, a motive, a number, a group of people — that the passage
  never actually says."*
- Not sure: *"That's a fair call when the passage genuinely doesn't give
  you enough to decide. It's useful information, not a wrong answer."*

### Core review screen

```
Reader Lab                                              2 of 4

SOURCE
"[short excerpt, exactly as given]"

THE SENTENCE
"[candidate sentence]"

Which feels most accurate?

○ The source supports this
○ This is a reading of the source
○ This adds something the source doesn't establish
○ I'm not sure

How sure are you?  (optional)
Pretty sure · Somewhat sure · Not very sure

Want to say why?  (optional, collapsed by default)

[ Continue ]
```

### Thank-you screen

> **That's it for today.**
>
> Thank you — this genuinely helps. Come back whenever you'd like for a
> few more.

No model answer, no "correct" answer, no other reviewers' votes, no
consensus, no score, ever shown to a reviewer at any point.

## 6. Task semantics (internal)

Reuses B2's own factuality question, translated to what a single sentence
in isolation can support without exposing B2's machinery:

- `source_established` — the passage directly supports the sentence's
  claim (a supported factual dependency).
- `interpretive_only` — the sentence frames, reads, or draws a conclusion
  from the passage, but doesn't require an unstated real-world fact to be
  true.
- `unsupported_factual_dependency` — the sentence depends on a fact,
  cause, motive, mechanism, or population claim the passage doesn't
  establish.
- `uncertain` — legitimate "I'm not sure." Recorded as real data, not
  penalized, not hidden as failure.

Practice categories (A/B/C/D in the source brief) map 1:1 onto these four;
v0 does not introduce a fifth practice-only category.

## 7. Source presentation

Only the frozen excerpt needed for the task is shown — never a full
article. The excerpt must carry enough context that a fair judgment is
possible; if a reviewer genuinely can't tell from what's shown,
"I'm not sure" is the correct answer, not a sign the UI failed. A future
version may add "I need more context" as its own option — v0 does not,
per instruction, to keep the first version narrow.

## 8. Confidence

Secondary, optional, three-point (`pretty_sure` / `somewhat_sure` /
`not_very_sure`) — never a 1–10 scale. The primary label never depends on
confidence; confidence is stored alongside it, not used to adjust it.

## 9. Comments

Never required. Collapsed "Want to say why?" text field, capped at a
reasonable length (see schema) to bound abuse/storage, shown after the
primary answer is given.

## 10. Privacy & reviewer identity

- No real names required. Internal ID: `reader_001`, `reader_002`, ...
- Invitation records (who a `reader_id` maps to) are held **separately**
  from response data — never joined in anything reviewer-facing, and
  joined in admin tooling only when necessary (e.g. sending someone their
  next invitation).
- No leaderboards, no gamified agreement, no cross-reviewer visibility of
  any kind.
- Minimum collection: no email required for the link to work (the token
  *is* the identity) — an email/contact channel for sending new session
  links is a separate, optional record, not part of the response schema.

## 11. Blindness & independence protocol

- A reviewer never sees the model's/B2's/R1's/R2's answer for an item,
  before, during, or after judging it.
- A reviewer never sees another reviewer's answer, or whether they
  agreed, at any point — not even on later visits.
- No hint, direct or indirect, about which failure mode the system is
  currently investigating.
- Two reviewers may be independently assigned the same item; assignment
  records are per-reviewer and neither can see the other exists on that
  item.
- Recorded on every response: `reviewer_blind_to_model_output: true`,
  `reviewer_blind_to_other_reviewers: true` — not because it varies in
  v0 (it doesn't), but so a future version that *does* vary this has to
  do so explicitly, in the data, not by omission.

## 12. Data model (versioned)

No backend exists yet (see `## OPEN DECISION`), so this is the schema a
future backend must implement, not a live table today. Server-side
values are authoritative; a client-submitted copy of source/candidate
text is never trusted as canonical — the server (whatever it ends up
being) resolves `item_id` to its own stored source/candidate content
before recording a response.

```json
{
  "response_id": "uuid",
  "session_id": "uuid",
  "reviewer_id": "reader_003",
  "item_id": "ril-000042",
  "task_type": "factual_floor_v0",
  "task_version": "v0.1",
  "assignment_version": "v0.1",
  "source_snapshot_id": "sha256:...",
  "candidate_claim_id": "sha256:...",
  "selected_public_response": "source_supports"
    | "reading_of_source" | "adds_unestablished" | "not_sure",
  "internal_normalized_response": "source_established"
    | "interpretive_only" | "unsupported_factual_dependency" | "uncertain",
  "confidence": "pretty_sure" | "somewhat_sure" | "not_very_sure" | null,
  "comment": "string, max 500 chars, optional",
  "timestamp": "ISO-8601 UTC",
  "reviewer_blind_to_model_output": true,
  "reviewer_blind_to_other_reviewers": true,
  "assistance_declared": "independent",
  "practice_or_real": "practice" | "real",
  "client_interface_version": "reader-lab-v0.1"
}
```

Invitation record (held separately, never joined into exports by
default):

```json
{
  "reviewer_id": "reader_003",
  "invitation_token_hash": "sha256:...",
  "contact_channel": "optional, e.g. an email or nothing at all",
  "created_at": "ISO-8601 UTC",
  "expires_at": "ISO-8601 UTC | null",
  "revoked": false,
  "practice_completed": true,
  "assistance_declaration_accepted_at": "ISO-8601 UTC"
}
```

Item record (authoritative, server-side; a reviewer's browser only ever
receives what's needed to render the current item):

```json
{
  "item_id": "ril-000042",
  "task_version": "v0.1",
  "source_snapshot": "frozen excerpt text",
  "source_snapshot_id": "sha256:...",
  "candidate_sentence": "frozen candidate text",
  "candidate_claim_id": "sha256:...",
  "dataset_bucket": "development" | "blind_calibration" | "contested" | "pilot",
  "is_practice": false
}
```

## 13. Assistance declaration

Collected once, at first onboarding, not re-asked per item:

> "For these tasks, please answer on your own rather than using ChatGPT,
> search, or another person."

Stored as `assistance_declared: "independent"` on every response from
that reviewer's real sessions. A future assisted-review experiment would
need its own `task_version`/`assignment_version`, never mixed into v0's
independent-only data.

## 14. Dataset destinations (research-side, not reviewer-visible)

Three conceptual buckets a completed judgment can later be sorted into by
a human/editorial process — **never automatically**:

- **development** — cases the team may inspect while changing the system.
- **blind calibration** — frozen, human-reviewed cases not yet used for
  tuning anything.
- **contested** — real disagreement between reviewers, or high
  `uncertain` rate on an item.

v0's own pilot content is tagged `dataset_bucket: "pilot"` and is never
silently promoted into calibration/contested data — a pilot response
proves the *mechanism* works, not that the *item* is a validated
reference case.

Two independent reviewers agreeing is "stronger provisional human
reference," not automatic ground truth. Majority vote is never
auto-applied as truth. This sorting is an editorial/research action taken
in admin tooling, never a public-UI computation.

## 15. GOVERNANCE — no automatic feedback loop

**Nothing a reviewer submits ever automatically modifies a prompt, model
weight, routing rule, threshold, or any part of the Mind Engine.** Reader
Lab data flows one direction only:

```
human judgment → versioned response data → later editorial/research
adjudication → development / blind-calibration / contested datasets →
controlled experiments → only then, possibly, a proposed system change
  (proposed and reviewed the same way every other B2/CJ change has been
   in this project's history — never wired directly)
```

Any future automation that reads Reader Lab data to influence system
behavior is a deliberate architecture change requiring its own design
document — it is not an incremental extension of v0.

## 16. Security & access control requirements

- A hidden URL is not access control. `noindex, nofollow` is not access
  control. Both are still required, but neither substitutes for real
  auth.
- Opaque, non-guessable, unique-per-reviewer token; server-side
  validated. No account/password for the reviewer to manage.
- Token revocation/expiration capability.
- No secret answers, labels, or reviewer master list ever shipped in
  client-delivered HTML/JS/JSON.
- Rate limiting appropriate to whatever backend is chosen.
- CSRF protection on the submission endpoint.
- Input length limits on the optional comment field; output escaping
  everywhere reviewer text is later rendered (admin views).
- `noindex, nofollow` (Crip Minds' `default.html` layout already supports
  `page.noindex` — a dedicated Reader Lab layout should set this
  unconditionally, not rely on per-page front matter being remembered).
- Absent from public nav, `sitemap.xml` (jekyll-sitemap: `sitemap: false`
  front matter, or full exclusion), `feed.xml` (safe by construction —
  feed only includes the `posts` collection), `llms.txt`, and any public
  structured data (no `Organization`/`Article` JSON-LD block on Reader
  Lab pages).
- No sensitive personal information collected (see `## 10`).

## 17. Admin / research workflow (v0 scope)

A normal reviewer never sees research data. v0's admin surface can be
minimal — CLI/JSON, not a dashboard:

- Create/revoke invitation records.
- Create a small assignment batch (which `item_id`s go to which
  `reviewer_id`s); support assigning the same item to 2+ reviewers
  independently.
- Check completion status per reviewer/session.
- Export raw responses (JSON/CSV) — raw only, no auto-computed "truth."
- A separate, later step (still manual) compares reviewers after
  completion and tags agreement/disagreement/contested — not part of the
  export itself.
- Inspect item/task-version hashes for provenance.

Reviewer UX gets real design care (see prototype). Admin UX is
deliberately utilitarian for v0.

## 18. Pilot protocol

**Goal:** can two ordinary invited people (a parent, a friend)
independently complete 3–5 tasks with no explanation from Jascha beyond
the onboarding screen? Do they understand the four choices? Does a
session take only a few minutes? Are their answers stored with clean
provenance?

**Not the goal:** does this improve B2 immediately. Pilot data is
`dataset_bucket: "pilot"`, built only from existing development-set
cases already safe to look at (never held-out evaluation material),
never presented as blind evaluation data.

Success = all four questions above answered "yes" for both pilot
reviewers. Nothing more is claimed from a 2-person, 3-5-item pilot.

## 19. Future expansion (not designed here, only flagged)

- Second Reader Lab task type once v0's mechanism is validated (e.g.
  category-jump quality, once CJ-2 is further along).
- "I need more source context" as a fifth option, if v0's excerpt length
  turns out to be a real limitation.
- Localization (Dutch) — copy is written with this in mind (no research
  logic embedded in display strings), but no i18n infrastructure exists
  in this Jekyll site today and none is built for v0.
- Cross-model or cross-reviewer statistical calibration tooling, once
  there's enough volume to make it meaningful.

---

## OPEN DECISION — hosting & persistence (not implemented, needs a choice)

**Finding:** cripminds.com is 100% static — Jekyll, built and deployed by
`.github/workflows/deploy.yml` straight to GitHub Pages. GitHub Pages
cannot run server code, cannot authenticate a request, and cannot persist
a submission. There is no existing backend anywhere in this repo's
production path. This is exactly the "cannot reasonably be implemented
inside the current stack" case the brief asked me to stop at, rather than
silently build around.

Two other facts changed what "smallest new addition" means here, so I'm
not presenting this as a blank slate:

- `dig` confirms cripminds.com's nameservers are already Cloudflare
  (`cris.ns.cloudflare.com` / `lady.ns.cloudflare.com`), with the apex
  pointed at GitHub Pages' IPs and `www` CNAME'd to `spac-null.github.io`.
  Adding a new subdomain (e.g. `lab.cripminds.com`) is a DNS record in an
  account that's already in place — not a new registrar, not a domain
  migration.
- Trident already has a Cloudflare Workers API key provisioned (found in
  `n8n.env` on trident, per `trident-specs.md`) — though it's scoped for
  n8n's own use, not proof Workers hosting is already running for this
  project. I'm not treating it as more than a signal that Cloudflare
  account access already exists somewhere in this ecosystem.

Trident itself (`jascha@trident`, Tailscale-only, `100.98.217.79` /
`*.tail630536.ts.net`) has no public reverse proxy, no port-forwarding,
no TLS termination for public traffic documented anywhere in
`trident-specs.md`. Every existing bot/stack on it (Reef, Compass,
Sentinel, inbox-bot) is reached over Tailscale or Telegram, never a raw
public URL. Reviewers here are "two parents, a few friends" — people who
will not install Tailscale to click a link.

### Option 1 — Cloudflare Workers + D1 (recommended)

A small Worker handles `GET /:token` (serve the reviewer app + validate
the token) and `POST /api/response` (validate token, write to D1).
D1 (Cloudflare's serverless SQLite) holds invitations/items/responses.
Static reviewer frontend can be the same Worker or a tiny Cloudflare
Pages project. New DNS record only (`lab.cripminds.com` → Worker route);
apex and `www` are untouched, so the main site's GitHub Pages deploy is
never at risk.

- Smallest new footprint: no server to patch, no new domain/registrar,
  reuses the Cloudflare account that already manages this domain's DNS.
- Needs: a scoped Cloudflare API token with Workers + D1 permissions
  (the existing n8n key's scope is unknown/unverified — likely needs its
  own token rather than reusing that one), `wrangler` CLI access,
  Cloudflare Workers/D1 enabled on the account (free tier covers this
  volume easily).
- Isolated from trident entirely — a home-server outage doesn't affect
  Reader Lab, and Reader Lab doesn't add any exposure to trident.

### Option 2 — Small app on trident, exposed via Tailscale Funnel

A tiny Flask/FastAPI + SQLite app (same shape as Reef's own web UI on
port 8080) reused from the automation patterns already in this
ecosystem, exposed publicly through Tailscale Funnel (`tailscale funnel`)
— gives a real public HTTPS URL without opening router ports or managing
TLS by hand.

- Reuses trident's existing Tailscale identity and Python/SQLite patterns
  instead of a new vendor.
- Real downside: Funnel exposes a public HTTPS endpoint *from* trident —
  the same box that runs `las-admin-v2`'s API, `coop-las` financial data,
  and several bots. Even a well-isolated container changes trident's
  threat model from "reachable only over Tailscale" to "has one public
  door," a bigger, harder-to-reverse decision than Option 1's isolated
  Worker.

### Option 3 — New managed hosting (Fly.io / Render / Deno Deploy + hosted Postgres/Turso)

A conventional small backend on a platform not otherwise used by this
project.

- Most new surface area of the three: new vendor account, new billing
  relationship, new deploy pipeline to learn and maintain, no DNS/account
  head start the way Option 1 has.
- Only worth it if Option 1 turns out to be blocked for some reason not
  yet known (e.g. Workers/D1 unavailable on the account for a billing
  reason).

**My recommendation is Option 1** — it's the only one that adds no new
public exposure to trident and reuses infrastructure access that already
exists for this exact domain. But it's still a first-of-its-kind addition
(first Worker, first D1 database for this project) touching a live
domain's DNS, so I'm asking rather than building it silently.

**DECIDED (2026-08-12): Option 1, Cloudflare Workers + D1.** Implementation
lives in `reader-lab-worker/` (Worker source, D1 schema, deploy README) —
written, **not deployed**. Deploying requires: a scoped Cloudflare API
token (Workers + D1 permissions, not yet created), running the schema
migration against a new D1 database, setting an `ADMIN_TOKEN` secret, and
adding a DNS record for the chosen subdomain (`lab.cripminds.com`
proposed, not yet added). None of that happens without a separate,
explicit go-ahead — this decision authorized the *architecture*, not a
live deploy.

**LIVE (2026-08-12) — TWO-PERSON PILOT IN PROGRESS.** Deployment progressed
past the hardening pass below: `reader-lab-worker/wrangler.toml` shows
`lab.cripminds.com` attached as an active Worker Custom Domain route
(`workers_dev` also left on, per the file's own header comment: "Stage 1
... deployed to workers.dev only. Stage 2 ... lab.cripminds.com attached
as a Worker Custom Domain") and a concrete D1 `database_id`
(`29eb76ef-7a33-4cee-bbf6-17d628e6b6f8`) for database name
`cripminds-reader-lab` — neither is a placeholder any longer. Main
`cripminds.com`/`www` remain untouched GitHub Pages, per the original
design's isolation goal.

**Verification caveat, stated precisely rather than glossed over:** the
session that wrote this update had no Cloudflare authentication available
(`npx wrangler whoami` returned "You are not authenticated") and could not
independently query the live account/D1 over the API. The LIVE status
above is drawn from the deploy configuration on disk (`wrangler.toml`'s own
comments and concrete IDs) plus direct instruction, not from a fresh API
read performed by this pass. EU jurisdiction for the production D1
instance, the exact row counts in `sessions`/`rate_limit_events`, and the
live reviewer-record count are stated as understood facts, not
independently re-confirmed here. Anyone continuing this work with real
`wrangler` access should run a read-only confirmation
(`wrangler d1 info cripminds-reader-lab`, `wrangler d1 execute
cripminds-reader-lab --remote --command "SELECT COUNT(*) FROM
invitations"` — a count only, never a raw-row dump of `token_hash`/
`contact_channel`) before treating any of the above as re-verified.

**Reviewer isolation IS independently verified from the code itself**,
regardless of the API-access gap above: `schema.sql`'s `responses` table
carries `UNIQUE (reviewer_id, item_id)`, and no reviewer-facing route in
`src/index.js` reads across `reviewer_id` values — `reviewer_parent_a` and
`reviewer_parent_b` cannot see each other's answers by construction, not
merely by policy.

**Credential-rotation incident, recorded without raw tokens.** Two
originally generated parent invitation credentials were exposed in
conversation and were subsequently revoked (`POST
/admin/invitations/revoke`, per the README's documented procedure). Fresh
credentials were generated directly against D1 and written temporarily to
`reader-lab-worker/.pilot-invites`, `chmod 600`, gitignored (confirmed via
`git check-ignore -v reader-lab-worker/.pilot-invites` →
`.gitignore:63:reader-lab-worker/.pilot-invites`). The fresh links were
sent privately.

**Correction, found during this pass's verification, not merely
restated:** the intended final state ("the temporary file was then
deleted") had NOT actually happened — `reader-lab-worker/.pilot-invites`
was still present on disk, 183 bytes, `chmod 600`, last modified the same
day this update was written. It has now been deleted, matching the
already-stated intent that it never persist once links are sent. No raw
invitation URL or token value is recorded in this document, in
`current-work.md`, or anywhere else in this repo at any point — only the
fact of the rotation and the (corrected) cleanup step.

**Current pilot status: READER LAB v0 — LIVE / TWO-PERSON PILOT IN
PROGRESS.** Not a public audience feature. Not statistically meaningful
human calibration — a 2-person, 4-item pilot proves the mechanism is
usable, nothing about the underlying factual-floor task's difficulty or
reliability at scale. `reviewer_parent_a` and `reviewer_parent_b` share the
same four `dataset_bucket: "pilot"` development/pilot assignments (see
`## 18. Pilot protocol` above); their responses are the pilot's own
comprehension-check data, per the frozen invariant below — never
retroactively upgraded into calibration or held-out-evaluation material.

**HARDENED (2026-08-12, production-readiness audit before first pilot).**
Second pass rewrote the auth model: the invitation token now mints a
one-time `Secure; HttpOnly; SameSite=Lax` session cookie
(`GET /invite/<token>` → 302 → `/session`) instead of living in the URL
for the whole session — the token never appears in a URL, fetch body, or
log again after that one redirect. Added: a `sessions` table (session id
hashed, same as the invitation token); revocation that cuts off an
already-open cookie immediately (re-checked on every request, not just
at login); an `/admin/invitations/revoke` endpoint (previously missing);
an `/admin/status` completion-tracking endpoint (previously missing,
returns no credentials); constant-time admin-token comparison; a
D1-backed rate limiter (peek-then-increment for admin auth so legitimate
bursts of correct-token calls never self-lock, count-every-attempt for
invite/session lookups); explicit response immutability (`already_recorded`
flag, first-submission-wins); CSP with per-request nonces, Referrer-Policy,
X-Content-Type-Options, X-Frame-Options, Cache-Control: no-store; and two
real accessibility fixes found by code review (radiogroup was pairing
`role=radiogroup` with `aria-pressed` buttons instead of `role=radio`/
`aria-checked`; the confidence-button row had no `flex-wrap`, risking
overflow on narrow phones). All of this is locally tested end-to-end
(42 automated checks, zero failures, plus a full two-reviewer pilot
walkthrough with the actual pilot content) against `wrangler dev --local`
— see this pass's production-readiness report for the complete test list
and results. **Still not deployed** — no Cloudflare API token created, no
production D1, no DNS record, no invitations sent.

---

## 20. RECURRING HUMAN CALIBRATION — READER LAB CALIBRATION ROUNDS (2026-08-12, design only, Round 001 NOT sent)

Purpose: let Crip Minds accumulate independent human judgment over
months/years without turning Reader Lab into continuous online learning.
A **round** is the unit of that accumulation — a small, named, frozen
batch of assignments with an explicit purpose, explicit blindness
properties, and an explicit (later, manual) disposition. This section
formalizes the protocol; it does not send any round.

### 20.1 Identifier convention

`RL-YYYY-NNN` — e.g. `RL-2026-001`, `RL-2026-002`. Sequential per calendar
year, zero-padded to 3 digits. Chosen for the same reason CJ-1/CJ-2's own
versioning is legible in prose (`cj2-stage-b2-v1.4.1`): a round number
should be nameable in a sentence without ambiguity about what it refers
to.

### 20.2 What every round records

| Field | Source | Notes |
|---|---|---|
| `round_id` | assigned at creation | `RL-YYYY-NNN` |
| `task_type` | fixed for v0 | `factual_floor_v0` (matches the existing per-response `task_type`) |
| `task_version` | fixed at creation | e.g. `v0.1` — matches the existing `task_version` semantics; a round never silently changes task semantics mid-flight |
| `created_at` | set at creation | ISO-8601 UTC |
| `frozen_at` | set explicitly, later | null until the item set + reviewer assignments are finalized; after this, no item or assignment may be added to the round |
| `dataset_purpose` | set at creation | one of `pilot` \| `development` \| `blind_calibration` \| `held_out_evaluation` \| `contested` (extends the existing `dataset_bucket` vocabulary with the one value it was missing — see `## 20.6`) |
| `item_ids` | derived, not stored redundantly | every `item_id` assigned to any reviewer under this `round_id` (join, not a duplicated list) |
| `reviewer_ids` | derived, not stored redundantly | every `reviewer_id` assigned any item under this `round_id` (join) |
| `reviewer_blind_to_model_output` | fixed for v0 | `true` — always, no round-level override exists yet (see `## 11`); recorded per round anyway so a future round TYPE that varies this has to do so explicitly in the data |
| `reviewer_blind_to_other_reviewers` | fixed for v0 | `true` — same reasoning |
| `assistance_mode_required` | fixed for v0 | `independent` — matches `## 13`'s existing declaration; a future assisted-review round would need its own `task_version`, never mixed into a round tagged `independent` |
| `completion_state` | computed, not stored | derived from whether every assignment under the round has `answered_at` set — never cached, so it can never go stale |
| `dataset_disposition` | set later, manually, by editorial/research action | null until an adjudication pass runs (see `## 20.4`) — never auto-set |

### 20.3 Round workflow

```
create manifest (round_id, task_type, task_version, dataset_purpose)
  → freeze item set (existing items, or new ones via /ops/items — moved
    from /admin/items 2026-08-12, see ## 23.8 — dataset_bucket matching
    the round's dataset_purpose)
  → assign reviewers (existing /ops/assignments — moved from
    /admin/assignments, same pass — extended with round_id, see ## 20.6)
  → freeze the round (frozen_at set; no further items/assignments accepted)
  → send invitations — REUSE existing reviewer credentials whenever the
    reviewer already has a valid, unrevoked invitation (see ## 20.5); only
    create a new invitation for a genuinely new reviewer
  → reviewers complete asynchronously (existing session/response flow,
    entirely unchanged — a round is invisible to the reviewer-facing UI,
    which shows items exactly as it does today)
  → export frozen responses, scoped to the round (existing /ops/export —
    moved from /admin/export, see ## 23.8 — filtered by round_id via
    assignments)
  → produce a human-reference summary (manual/editorial step, see ## 20.4)
```

Nothing in this workflow requires a new reviewer-facing route, a new
onboarding flow, or a dashboard. The reviewer never sees a round boundary
— they see "N items today," exactly as designed in `## 4`.

### 20.4 Reference-strength categories — never collapsed into one label

A round's raw judgments are never replaced by a single consensus value.
Provenance categories, recorded per claim/item, not per round:

- **one independent judgment** — exactly one reviewer has answered this
  item so far.
- **two independent humans agree** — two reviewers, assigned
  independently (neither could see the other's answer at any point, per
  `## 11`), gave the same `internal_normalized_response`. Recorded as
  **stronger provisional human reference**, never as "ground truth" — the
  same discipline this project already applies to B2's own development
  labels (`human-review-labels-v1.json`'s explicit
  `independent_human_reference` field is the direct precedent for this
  distinction).
- **independent humans disagree / contested** — two reviewers gave
  different answers. This is itself a finding, not a defect to average
  away — matches `dataset_purpose: contested`. Majority vote, if a third
  reviewer is ever added to break a tie, is never auto-applied as truth
  (`## 14`, unchanged).
- **independently adjudicated after disagreement** — an explicit, later,
  manual/editorial step reviewed a contested item and recorded a
  reasoned resolution. This does NOT overwrite or delete the original
  disagreement — the raw judgments remain queryable (existing
  `/ops/export` — moved from `/admin/export`, see `## 23.8` — is raw rows
  only, per `## 17` and the README's own
  "What this Worker deliberately does not do" list) with the adjudication
  stored as an additional, separate record, the same non-mutating pattern
  B2's own `auditor_evidence` provenance layer already uses ("wraps,
  never mutates").

Exact label strings may differ once this is implemented (e.g.
`single_judgment` / `concordant_pair` / `contested` / `adjudicated`) — the
four categories above are the fixed semantics; naming is not.

### 20.5 Returning reviewers need no new credentials

A round assigns EXISTING reviewers (`reviewer_parent_a`, `reviewer_parent_b`,
and whoever joins later) to a new batch of items via `/ops/assignments`
(moved from `/admin/assignments`, see `## 23.8`; extended per `## 20.6`)
using their current, unrevoked invitation. The
existing session-cookie flow (`## `Auth model`` in
`reader-lab-worker/README.md`) already supports "3 items today, 4 next
week, 5 another time" without re-onboarding — a reviewer who already
completed practice never sees it again (`## 4`, unchanged); they simply
see a new set of assigned items whenever they next visit. A new invitation
is created ONLY for a genuinely new reviewer. Do not regenerate credentials
for an existing reviewer just because a new round exists.

### 20.6 Admin/storage support — the smallest extension, not a dashboard

**Can most of this be represented without a schema change?** Item-level
`dataset_bucket` already has 4 of the 5 needed values
(`development`/`blind_calibration`/`contested`/`pilot`) — `held_out_
evaluation` is the only gap, and no item needs that value yet (Round 001
is explicitly deferred, see `## 20.7`), so extending that `CHECK`
constraint is deferred until an item actually needs it, rather than
solved preemptively (SQLite/D1 `CHECK` constraints require a table
rebuild to modify, not a plain `ALTER TABLE ADD COLUMN` — not worth doing
before it's needed).

**What genuinely needs a small schema addition:** round-level identity
and purpose (nothing existing represents "this batch of assignments is
one named, frozen unit"), and a way to say which `round_id` an assignment
belongs to. Designed as two additive changes, written as a migration file
NOT yet applied to any database (local or production):

`reader-lab-worker/migrations/0001_calibration_rounds.sql` (new file,
purely additive — see the actual file for the exact DDL):
- `CREATE TABLE rounds (round_id TEXT PRIMARY KEY, task_type TEXT NOT
  NULL, task_version TEXT NOT NULL, dataset_purpose TEXT NOT NULL CHECK
  (...), created_at TEXT NOT NULL, frozen_at TEXT, reviewer_blind_to_
  model_output INTEGER NOT NULL DEFAULT 1, reviewer_blind_to_other_
  reviewers INTEGER NOT NULL DEFAULT 1, assistance_mode_required TEXT NOT
  NULL DEFAULT 'independent', dataset_disposition TEXT, notes TEXT)`
- `ALTER TABLE assignments ADD COLUMN round_id TEXT REFERENCES
  rounds(round_id)` — nullable, so every existing assignment (including
  the pilot's own four) stays valid with `round_id = NULL`. **The pilot's
  four assignments are deliberately NOT retroactively assigned a
  `round_id`** — they predate round tracking and stay tagged
  `dataset_bucket: "pilot"` only, per `## 18`'s own rule against upgrading
  pilot data after the fact.

`item_ids`/`reviewer_ids` for a round are never stored redundantly — both
are simple joins (`assignments WHERE round_id = ?`) against tables that
already exist. `completion_state` is likewise never cached — computed
from `assignments.answered_at` at read time, so it can never go stale.

**Deliberately not built in this pass:** the `POST /admin/rounds` /
`POST /admin/rounds/:id/freeze` / `GET /admin/rounds/:id/export` endpoint
code itself. The migration above is a real, reviewable schema design;
wiring it into `src/index.js` is a small, natural next step in the same
style as the existing admin endpoints, but implementing it wasn't asked
for in this design pass and risks exactly the "large dashboard" scope
creep this section is instructed to avoid. A manifest + the EXISTING
`/ops/items` and `/ops/assignments` endpoints (moved from `/admin/items`/
`/admin/assignments`, see `## 23.8` — extended to accept an optional
`round_id`) plus a manual export/adjudication step is sufficient for
Round 001's actual scale (3-5 items, 2+ reviewers). (A visual admin
control plane was later built at `/admin` — see `## 23` — superseding
"deliberately not built" above.)

### 20.7 Reviewer load

Default target: 3-5 items per reviewer per round, a few minutes each —
matches `## 4`'s existing session-size design exactly; a round is a
naming/bookkeeping layer over the existing small-session mechanism, not a
new UX size. The same trusted reviewers may return periodically. The
protocol must work correctly with only two reviewers (today's actual
count) — nothing above requires a third. More reviewers may join later
without any protocol change; `/ops/assignments` (moved from
`/admin/assignments`, see `## 23.8`) already supports assigning N
reviewers to the same item independently.

### 20.8 Frozen invariant — pilot data stays pilot data

`RL`-round tracking is a NEW mechanism, layered on top of, not a
replacement for, the existing `dataset_bucket` field. The pilot's four
items remain `dataset_bucket: "pilot"` forever, regardless of anything
this section adds — round tracking does not retroactively reclassify
anything that already happened. **Round 001 is NOT sent by this design
pass.** When it eventually is, it should use carefully selected real Crip
Minds claims/sources appropriate for factual-floor judgment — not the
pilot's invented library/museum/garden material, and not untouched
held-out cross-publisher evaluation cases without a separate, explicit
research decision to spend that material (the same discipline the B2/CJ-2
track already applies to its own held-out corpus).

## 21. PARENT PILOT — ANALYSIS + INSTRUMENT RESULT (2026-08-12)

Analyzed directly from the credential-free handoff export
(`.claude/reader-lab-handoff/parent-pilot-completed-2026-08-12.json`,
SHA256 `a7790d64b3aa752076f50a1a62e732ad4f08a2d4b03a58dd0c79b9c61be10afe`)
— read raw, not from a summary. This section is an **INDEPENDENT
TWO-REVIEWER HUMAN REFERENCE analysis, not a ground-truth adjudication**
(`## 14`'s rule applies in full: two reviewers agreeing is "stronger
provisional human reference," never truth).

### 21.1 Completion

Both `reviewer_parent_a` and `reviewer_parent_b`: `practice_completed=1`,
`assigned_count=4`, `answered_count=4` for the real items, plus all 4
practice items answered. Both completed independently
(`reviewer_blind_to_other_reviewers=1` on every response,
`assistance_declared="independent"` throughout). Session timing: Parent
A's 4 real items span ~6 minutes (13:34:04–13:40:11); Parent B's span
~4 minutes (12:38:28–12:42:29) — both within the design's few-minutes
target. Neither reviewer left an item blank or asked for help.

### 21.2 Practice comprehension

| Item | Correct answer | Parent A | Parent B |
|---|---|---|---|
| P1 (library hours) | `source_established` | `unsupported_factual_dependency` (miss) | `unsupported_factual_dependency` (miss) |
| P2 (rope barriers) | `interpretive_only` | `interpretive_only` (hit) | `unsupported_factual_dependency` (miss) |
| P3 (after-school enrollment) | `unsupported_factual_dependency` | `unsupported_factual_dependency` (hit) | `unsupported_factual_dependency` (hit) |
| P4 (board vote) | `uncertain` | `interpretive_only` (miss) | `unsupported_factual_dependency` (miss) |

Raw practice scores (2/4, 1/4) look low in isolation, but practice is
explicitly a *teaching* device (`## 4`: "we'll tell you why after each
one"), not a comprehension test — what matters is whether the
explanation shown after each miss was carried forward into the real
items. It was: both reviewers' real-item comments echo the practice
explanations' own reasoning almost verbatim (see `## 21.3`). Both
reviewers' consistent miss on P1 (calling a directly-stated fact
`unsupported_factual_dependency`) and both misses on P4 (never reaching
`uncertain`) are read together as one real, generalizable signal, not
two coincidences — see `## 21.4`.

### 21.3 Real items — agreement, disagreement, and whether disagreement is substantive

| Item | Parent A | Parent B | Agree? |
|---|---|---|---|
| 1 (café lighting → "calmer") | `interpretive_only` ("doesn't equal calm... an interpretation") | `interpretive_only` (no comment) | YES |
| 2 (newsletter mail → "older residents asked") | `interpretive_only` ("I hesitate between reading and adding something") | `unsupported_factual_dependency` ("no mention of why") | NO |
| 3 (bike rack → "made it easier to attend") | `interpretive_only` ("interpretation of the cause") | `unsupported_factual_dependency` ("it adds an explanation") | NO |
| 4 (crosswalk repaint → "now painted brighter than before") | `unsupported_factual_dependency` ("we don't know if the initial painting was less bright") | `source_established` ("more info in the source so its OK!") | NO |

1/4 clean agreement, 3/4 disagreement. **Every single comment, on both
sides of every disagreement, is a substantive, on-topic engagement with
the actual reading-vs-claim distinction** — not a sign either reviewer
misunderstood what the four options mean:

- Item 2: Parent A explicitly names the exact boundary she's weighing
  ("I hesitate between reading and adding something to the source") —
  this is a reviewer *correctly identifying* that the item sits on the
  interpretive/factual boundary, which is precisely what a working
  instrument should surface, not evidence it's confusing her.
- Item 3: both reviewers agree the sentence makes a causal claim
  ("interpretation of the cause" / "it adds an explanation") — they
  disagree only on whether that specific causal framing is a reading or
  an added dependency. This is the exact same live tension the B2/CJ-2
  architecture itself is contending with around causal-hardening claims
  (see `H08`/`H09` in the CJ-2 experiment doc) — reassuring evidence that
  naive human readers hit the same real boundary the model architecture
  does, not that the instrument is broken.
- Item 4 is the one case worth flagging on its own: Parent B's
  `source_established` read, with comment "more info in the source so
  its OK!", is hard to fully reconcile with the source, which never
  states the crosswalk's prior color — Parent A's `unsupported_
  factual_dependency` read ("we don't know if the initial painting was
  less bright") tracks the source more precisely. This could be a
  genuine miss by Parent B, or a defensible reading that "high-
  visibility yellow" alone implies brighter without needing an explicit
  prior-color baseline. Recorded as an open, single-instance signal —
  not adjudicated, not treated as proof of confusion, and not ignored.

### 21.4 One real usability caveat, not a blocker

**Neither reviewer used "I'm not sure" even once, across all 8
judgments each (4 practice + 4 real) — including P4, the one practice
item built specifically to have `uncertain` as its answer.** Both
reviewers instead defaulted to a concrete category (`interpretive_only`
or `unsupported_factual_dependency`) on every single item, even ones
explicitly designed to be genuinely ambiguous. This does not look like
confusion about what "I'm not sure" means (the copy is plain: `## 5`'s
practice explanation directly normalizes it as "a fair call... a useful
answer, not a wrong one") — it looks more like a disposition to commit
to *some* concrete reading rather than register genuine ambiguity,
possibly reinforced by both reviewers being asked to help/be useful.
**Flagged for monitoring in future rounds and possible copy iteration
(e.g. surfacing "I'm not sure" more prominently, or revisiting whether
P4's specific wording actually reads as ambiguous to a non-technical
reader) — not treated as grounds for `NEEDS_REVISION`,** since it is a
single, consistent-across-both-reviewers pattern rather than evidence of
divergent or confused category use.

### 21.5 Instrument-level result — TWO SEPARATE CLAIMS, NOT ONE

**This section originally stated a single "READER LAB PILOT: PASS"
verdict. Correction (2026-08-12, same day, later pass): that collapsed
two genuinely different questions into one label, which risks being
misread as "the pilot validated the labels" — it did not, and was never
sized to.** The pilot supports exactly two separate, independently-scoped
conclusions:

**READER LAB INSTRUMENT USABILITY: PASS.**

Basis: both reviewers completed all items unaided, within the time
target, with zero requests for help and zero blank/skipped items;
real-item disagreements are traceable to substantive, articulated
judgment calls about the actual factual-floor boundary (including one
reviewer explicitly naming the boundary she was weighing), not to
confusion about the four-option interface; practice misses were
followed by demonstrated uptake of the shown explanation into real-item
reasoning. The one caveat (`## 21.4`, zero `uncertain` usage) is
recorded as a real, worth-watching usability signal, not evidence the
interface or task definition itself is confusing — the explicit STOP
condition for this pilot ("clear evidence the interface/task definition
itself is confusing") is not met. **This is a claim about whether two
ordinary people can operate the instrument without coaching — nothing
more.**

**HUMAN LABEL RELIABILITY: NOT YET ESTABLISHED.**

Basis: only 1 of the 4 real pilot items produced clean two-rater
agreement; the other 3 produced substantive disagreement (`## 21.3`).
The 4 pilot items were themselves invented UX/development examples
(`## 18`), not a sample sized or selected to measure inter-rater
reliability. A 4-item, 2-rater pilot cannot and does not establish
whether Reader Lab judgments are a reliable reference signal — that
question remains genuinely open and is exactly what a larger, purpose-
built calibration round (e.g. `RL-2026-001`, `## 20`) is for, not
something the pilot itself answers. **Two independent reviewers agreeing
is never ground truth (`## 14`, unchanged); two independent reviewers
disagreeing is never evidence the instrument or Reader Lab itself
failed** — the disagreements observed were substantive engagement with a
genuinely hard boundary (`## 21.3`), which is a sign the instrument is
correctly surfacing real difficulty, not a defect in either the
instrument or the reviewers. Reporting USABILITY=PASS and RELIABILITY
side by side, rather than a single collapsed verdict, is now the
standing convention for every future pilot/round in this document.

## 22. SESSION/OPS SEPARATION — CREDENTIAL-FREE HANDOFF (2026-08-12, standing convention)

As of this pass, the Crip Minds research/development session (this one)
runs **by design** with no Cloudflare API token, `ADMIN_TOKEN`,
`EXPORT_TOKEN`, or direct D1 access, and is not expected to request any
of the above going forward. A separate, privileged ops session performs
all production Cloudflare/D1 reads and writes. This does not change
anything in `## 15`–`## 17` about governance or admin scope — it adds a
concrete mechanical boundary for *which session* is allowed to hold
which credential, on top of the access-control rules already specified
there.

**The interface between the two sessions is versioned, credential-free
files, never a shared secret:**

- **Handoffs (ops → research):** `.claude/reader-lab-handoff/*.json` —
  git-tracked, timestamped, self-describing (each carries its own
  `handoff_metadata` block naming exactly what was read, what's included,
  and what's explicitly excluded). Permitted contents: reviewer
  pseudonymous IDs, item/round IDs, exact frozen source/candidate content
  or stable hashes, reviewer choices, confidence, comments, timestamps,
  blindness/provenance metadata, completion state. **Never permitted:**
  invitation tokens or hashes, session cookie/`session_id_hash`,
  `ADMIN_TOKEN`, `EXPORT_TOKEN`, any Cloudflare API token, `contact_channel`,
  or any other infrastructure secret. A handoff is a snapshot as of its
  recorded `export_timestamp` — not treated as live after that moment;
  a fresh handoff is requested (from the ops session) rather than assumed
  current.
- **Round drafts (research, local-only until published):**
  `reader-lab/rounds/drafts/RL-YYYY-NNN.json` — authored entirely from
  already-available local repo material (development-set fixtures,
  prior B2/CJ-2 artifacts) with no Cloudflare access needed to create,
  validate, or freeze. States: `draft` → `ready_for_review` →
  `frozen_ready_for_publish` → (after an ops session executes it)
  `published` → `completed`. Once `frozen_ready_for_publish` (manifest
  content hashed, hash recorded in the manifest's own metadata and in the
  ops request below), the file is not edited silently — a content change
  after freezing requires a new, explicitly-named round or an explicit,
  logged re-freeze, the same discipline this project already applies to
  frozen prompts/harnesses elsewhere.
- **Ops requests (research → ops):**
  `.claude/reader-lab-handoff/RL-YYYY-NNN-ops-request.json` — names the
  frozen manifest path + SHA256, the requested action, explicit
  constraints (no content edits, no new credentials, no held-out
  material), and what post-write verification is wanted back. The
  research session does not attempt the Cloudflare write itself, and
  does not request or read `ADMIN_TOKEN`/`EXPORT_TOKEN` to construct this
  file.
- **Publication receipts (ops → research, after a request is executed):**
  a credential-free confirmation (item/assignment IDs created, hash
  confirmation that published content matches the frozen manifest) — not
  yet needed as of this pass, since no round has been published yet.

**What this changes about `## 17` (admin/research workflow):** the admin
CLI/curl surface described there still exists and is still how the
privileged ops session actually operates — this section does not
replace it, it constrains *who* is expected to hold the credential that
surface requires. A future proper Reader Lab control plane/admin portal
remains explicitly out of scope until separately authorized (`## 19`) —
this file-based handoff is the smallest mechanism that solves the
current session-access separation, not a first draft of that portal.

**Production state, as independently confirmed by the privileged ops
session (not re-verified by this research session, which has no means
to):** D1 serves from `EEUR` (colo `FRA`) — resolves the prior "EU
jurisdiction not independently re-confirmed" caveat recorded in
`current-work.md`'s `## OPEN DECISION` section. That caveat's specific
wording should be read as superseded by this confirmation, not as an
open question this research session is expected to chase further.

## 23. ADMIN CONTROL PLANE (`/admin`) — 2026-08-12, privileged ops session

Purpose: everything in `## 22` above (file-based, credential-free
research↔ops handoff) still exists and still works, but it depends on a
privileged Claude session remembering the workflow and running CLI/API
commands by hand. This section adds a small, visual, in-application
control plane so that operating Reader Lab — creating a round, reviewing
it, publishing it, reading results, managing reviewers — no longer
depends on that. **Normal human operation is now `/admin`; the CLI/API
paths described in `## 17`/`reader-lab-worker/README.md` remain, but only
for automation, emergencies, and debugging.**

### 23.1 Scope — five screens, not a CMS

Dashboard, Rounds (list + detail, including create/review/freeze/publish),
Results, Reviewers, Import. Explicitly not built: public accounts,
leaderboards, automatic B2 tuning, an AI chat inside the admin, generic
role management, or a generic analytics suite. This is the same
discipline `## 2` (non-goals) already applies to the reviewer-facing
product, applied to the admin surface too.

### 23.2 Round lifecycle — draft → review → frozen → published → completed

A round authored in the admin UI is not written to `items`/`assignments`
until explicitly published. States, persisted on `rounds.status`
(migration `0002_admin_control_plane.sql`, additive):

- **draft** — freely editable; content lives in a new `round_drafts`
  table (one row per in-progress round), never in `items`/`assignments`.
- **review** — same storage, a status label only; the round detail page
  in this state (and `frozen`) renders every question exactly as a
  reviewer will see it (SOURCE / THE SENTENCE only — no internal note,
  no provenance, no expected answer), so freezing is an informed choice.
- **frozen** — the manifest's content hash is computed and recorded
  (`rounds.manifest_sha256`); this is the "review screen" state the
  original brief asked for, with an explicit **Cancel** (back to draft —
  re-editing before publish is safe, since nothing has been published
  yet) / **Freeze & Publish** choice.
- **published** — the one moment anything is written to `items`/
  `assignments`. Content is immutable from here on, per `## 20`'s
  existing invariant — a correction is a new round, never a rewrite of
  this one's history.
- **completed** — not yet automated (no code currently flips this state);
  reserved for a later, still-manual step once every assignment in the
  round has an answer.

RL-2026-001 itself was backfilled to `status='published'`,
`source='import'` by the migration (based on its pre-existing
`frozen_at` value) — its own item/response content was not touched.

### 23.3 One publication path — `reader-lab-worker/src/publish.js`

The single, shared function set every round publication goes through,
regardless of origin:

```
canonicalizeManifest (accepts both a clean manifest AND the older,
  fully-annotated shape RL-2026-001.json itself shipped in — maps
  internal_ref -> provenance, rationale_internal_not_shown_to_reviewer ->
  internal_note, so existing research-session authoring habits don't need
  to change)
  -> validateManifest (structural checks, hash verification against
     content, reviewer existence/revocation, duplicate detection —
     see ## 23.5)
  -> freezeRound (locks content, records manifest_sha256)
  -> publishRound (one env.DB.batch() — items + assignments + round
     status + audit-log row, all-or-nothing; re-queries afterward to
     confirm the expected assignment count actually landed; idempotent —
     publishing an already-published round returns the existing receipt
     instead of writing again)
```

Three entry points, one shared implementation: the admin UI's own
draft/freeze/publish screens, `POST /admin/api/import` (paste/upload a
manifest, same JSON shape as `reader-lab/rounds/drafts/RL-YYYY-NNN.json`),
and `POST /ops/publish` (machine one-shot, `X-Admin-Token` — moved from
`/admin/publish` during deployment, see `## 23.8`, for automation that
wants to hand over a complete manifest and get a receipt back in one
call). **This retires the original RL-2026-001 publication
path** (a hand-run `wrangler d1 execute` against interpolated SQL) —
every value from here on reaches D1 through a bound parameter, never
string interpolation, which is what actually made that original path
fragile with multi-line content, not D1/SQLite itself. Verified directly
this pass: a round with embedded newlines, em-dashes, curly quotes, and
non-ASCII characters in both the source and candidate fields round-tripped
byte-for-byte through save-draft → freeze → publish → the reviewer-facing
`/api/session` response.

### 23.4 Auth — Cloudflare Access, not `ADMIN_TOKEN` in a browser

`/admin` and `/admin/api/*` require a Cloudflare Access-issued JWT
(`reader-lab-worker/src/access.js`), verified independently by the Worker
itself (JWKS fetched from the team's `.cloudflareaccess.com` endpoint,
RS256 signature checked via Web Crypto, `aud`/`exp`/`iss` checked) rather
than trusted from Cloudflare's edge alone — defense in depth. `ADMIN_TOKEN`
and `EXPORT_TOKEN` are unchanged and still gate the legacy machine routes
exactly as before (`## 17`) — those routes live at `/ops/*`, not
`/admin/*`, specifically so Access's protection of `/admin` can never
sweep them in (see `## 23.8` for the bug this fixes); neither credential
ever reaches a browser for the new surface.

**Status below reflects this pass's own point in time — superseded by
`## 23.8`, which records the actual completed deployment, the Access
path-scope bug found and fixed, and the human production smoke test
Jascha completed and confirmed by screenshot. Left unedited here as an
accurate record of what was true when this paragraph was written, not as
current status.**

**Current status (as of this pass): READY, BUT ACCESS SETUP IS BLOCKED —
not deployed to production.** Checked directly against the Cloudflare API
this pass (not assumed): `GET /accounts/:id/access/apps` returns
`access.api.error.not_enabled` — Cloudflare Zero Trust has never been
turned on for this account, and enabling it the first time needs an
interactive dashboard step (choosing a team name) no API token can do.
Per the explicit instruction for exactly this situation, the admin
control plane is fully built and locally tested (see `## 23.6`) but
deliberately not deployed — every `/admin*` route already fails closed
(`503 admin_access_not_configured`) whenever `ACCESS_TEAM_DOMAIN`/
`ACCESS_AUD` are unset, a second, independent reason this is safe to
deploy later without exposing anything before Access is actually wired
up. The exact remaining manual steps are in
`reader-lab-worker/README.md`'s "Admin control plane" section (enable
Zero Trust → create a self-hosted Access application scoped to
`lab.cripminds.com/admin*` restricted to Jascha's email → set
`ACCESS_AUD`/`ACCESS_TEAM_DOMAIN` → apply migration `0002` to production
→ `wrangler deploy`).

Because there is no live Access instance to test against, the JWT
verification logic itself was unit-tested in isolation this pass (a
self-signed RSA keypair standing in for Cloudflare's own signing key,
`fetch` monkey-patched to serve a fake JWKS): a valid token verifies and
returns the expected claims; an expired token, a wrong-audience token, a
wrong-issuer token, a tampered signature, and a token forged with a
*different* key under the *same* `kid` all correctly return null; a
malformed token also returns null. This confirms the code path does real
signature verification, not just a `kid` lookup.

### 23.5 Manifest validation (`validateManifest`)

Enforced as hard errors (never silently repaired): `round_id`/
`task_type`/`task_version` present; `dataset_purpose` in
`pilot`/`development`/`blind_calibration`/`contested` (`held_out_
evaluation` deliberately not yet offered — see `## 23.7`); at least one
item; every item has non-empty source/candidate text; a declared
`source_snapshot_id`/`candidate_claim_id` (if present, e.g. from an
already-hashed research-session manifest) must match a fresh recompute of
the actual content — a mismatch is a hard error, not a silent overwrite;
every `reviewer_id` must exist and not be revoked; no duplicate slots, no
duplicate reviewer_ids. Flagged only as warnings (round_id not matching
the `RL-YYYY-NNN` convention, two items with identical source+sentence
within the same manifest, a candidate sentence that already exists as a
different item_id in production) — real, but not something the tool
should refuse to publish over, since some of these are legitimate (e.g.
intentionally re-presenting a claim in a later round).

### 23.6 Local test pass (before any production step)

Run against a fresh local D1 replica (schema + both migrations) via
`wrangler dev --local`, `ACCESS_DEV_BYPASS=1` in a gitignored `.dev.vars`
only: unauthenticated `/admin`/`/admin/api/*` correctly fail closed 503
once the bypass was removed (not 401 — there is no valid Access
configuration to even attempt authenticating against yet); reviewer
routes (`/invite`, `/session`, `/api/session`, `/api/response`) unaffected
throughout; legacy `X-Admin-Token`-gated `/admin/status` still works
unchanged (this route was still named `/admin/status` at this point in
the work — moved to `/ops/status` during the deployment pass, `## 23.8`);
full draft → freeze → publish cycle for a test round with
deliberately adversarial content (embedded newlines, em-dashes, curly
quotes, non-ASCII) confirmed byte-identical in D1 afterward; double-publish
returns the original receipt rather than writing again; `round_drafts` row
is deleted post-publish; `audit_log` recorded every action
(`reviewer_created`, `round_draft_saved`, `round_frozen`,
`round_published`) with a plausible actor; import validation correctly
rejected a hash-mismatched item and an unknown reviewer as hard errors,
and accepted (with only a warning) two items with identical content;
importing the actual RL-2026-001.json file's own shape (internal_ref,
rationale_internal_not_shown_to_reviewer, declared hashes and all)
validated cleanly under a new round_id, confirming the older
research-session authoring format doesn't need to change; revoking a
reviewer immediately invalidated their already-open session (401 on the
next request), and reactivating restored it; the served `/admin` HTML was
checked directly for `ADMIN_TOKEN`/`EXPORT_TOKEN`/bypass-flag substrings —
none found. Cleaned up: local test round/reviewer rows are local-only
(never touched production D1), and `ACCESS_DEV_BYPASS` was removed from
`.dev.vars` again after testing.

### 23.7 Known, deliberately deferred gaps

- `held_out_evaluation` is a valid `rounds.dataset_purpose` value (added
  in migration `0001`) but is NOT yet offered as a round dataset_purpose
  in the admin UI/validator, because `items.dataset_bucket`'s own `CHECK`
  constraint (`schema.sql`) doesn't include it, and SQLite/D1 can't ALTER
  a CHECK in place — only a full table rebuild would fix this, which
  this pass deliberately didn't do to a live table with real reviewer
  response foreign keys, matching the identical call already made in
  `## 20.6`.
- `completed` is a defined round status with no code path that sets it
  yet — a later, still-manual step (once every assignment has an
  answer), not automated in this pass.
- No email/notification automation for newly created reviewer
  invitations — the admin UI shows the link once, same as the legacy CLI
  route; sending it is still a manual, out-of-band step.

### 23.8 DEPLOYMENT (2026-08-12, continuation pass) — LIVE

Jascha enabled Cloudflare Zero Trust and created a self-hosted Access
application manually (the one interactive step `## 23.4` said was
required). This pass verified that configuration directly against the
live Access API — not taken on trust — found and fixed a real path-scope
bug, then completed the deploy this section's earlier draft had
deliberately stopped short of.

**Access verification, done properly this time.** The API token used by
this session initially had no Access/Zero Trust read scope at all
(`access/organizations`, `access/groups`, `access/identity_providers`
all returned authentication errors; `access/apps` returned an empty list
despite an app existing, confirmed by directly hitting
`https://lab.cripminds.com/admin` unauthenticated and getting Cloudflare's
own 302 to `blue-king-f6e0.cloudflareaccess.com`). Jascha added read scope,
then — after this pass found the app initially had **zero policies
attached** (not "too broad," genuinely unconfigured) — added a single
`allow` policy. Both gaps were caught and fixed in sequence, each
re-verified via API before proceeding: final state is one `allow` policy,
`include` = exactly two specific email addresses (`jaschablume@gmail.com`,
`email@jaschablume.nl` — the second added after this pass flagged that
the first alone didn't match the email on file elsewhere), no
`exclude`/`require` rules, no broad "everyone" rule, identity provider
`type: "cloudflare"` only (nothing added). Team domain `blue-king-f6e0`
and AUD `a115fbf5da8905eb07a6c8f1277e1983792d969e5f26f4f9268cff0df38c0c36`
confirmed by two independent means (the live unauthenticated redirect,
and the Access API directly) — both matched.

**Real bug found in production, before it caused lasting damage: Access
path scope swept in the legacy machine routes.** Cloudflare's self-hosted
Access app model protects a path *and every subpath beneath it* — there
is no "protect this exact path, not its children" option. The app was
initially scoped to `lab.cripminds.com/admin` (+ an explicit, and it turns
out entirely redundant, `/admin/*`). Live testing (not assumed) showed
this also intercepted `/admin/status`, `/admin/export`, `/admin/items`,
`/admin/invitations` — the pre-existing `X-Admin-Token`/`X-Export-Token`
machine routes, which happened to share the `/admin` prefix. Narrowing
`self_hosted_domains` to just `lab.cripminds.com/admin` +
`lab.cripminds.com/admin/api` didn't fix it either — confirmed live that
the bare `/admin` entry alone still matched `/admin/status` — proving
there was no Access-side fix available at all. **The actual fix: the
legacy machine routes moved from `/admin/*` to `/ops/*`**, a prefix
sharing nothing with `/admin`, so Access's subpath behavior can never
reach them again. `src/index.js`'s route table, `README.md`'s route list
and every curl example, updated accordingly. This is a structural,
permanent fix, not a workaround — it doesn't depend on Access
configuration staying a particular way.

**Pre-deploy local re-verification** (against the real production
`ACCESS_TEAM_DOMAIN`/`ACCESS_AUD` values, real JWKS fetched live over the
network, no Access instance to fake so only negative cases were
testable): no token → 401; malformed token → 401; a token forged with a
different key but a **real `kid` from the production JWKS** and the
**real `aud`/`iss` claims** → still 401 (proves the signature check
itself is load-bearing, not just a `kid` lookup). Round lifecycle
re-confirmed byte-exact with CJK characters added to the adversarial
content this time, not just Latin/em-dash/curly-quote content.

**Production migration.** Before/after snapshot taken (table list, exact
row counts, RL-2026-001 metadata, every item's content hash) — migration
`0002` applied via `wrangler d1 execute --remote`, verified purely
additive: same row counts before/after (4 invitations / 14 items / 26
assignments / 25 responses / 1 round), all 14 items' content hashes
byte-identical (diffed programmatically, not eyeballed), RL-2026-001
correctly backfilled to `status='published'`, `source='import'`.

**Live security tests, all ten (A–J from the operator's checklist),
against the real deployed Worker:** unauthenticated `/admin` and
`/admin/api/dashboard` both 302 to Access, zero admin markup/data in the
redirect body; path-variant and wrong-legacy-header bypass attempts all
302'd (never reached the Worker); reviewer routes (`/invite`,
`/api/session`) unaffected and Access-unaware; `/ops/status`/`/ops/export`
reachable directly with the real `EXPORT_TOKEN` (read succeeded, showing
correct live counts — both parents `4/9` answered, matching pilot-complete
+ RL-2026-001-untouched); the same `EXPORT_TOKEN` correctly rejected on
every write route (`/ops/items`, `/ops/invitations`); no secrets in any
response header or the served `/admin` HTML. **One check not positively
completed:** confirming a *correct* `ADMIN_TOKEN` succeeds on `/ops/*` —
this session doesn't retain that secret's value (by design, consistent
with `## 22`'s credential-separation convention), so only the negative
case (wrong token → 401) was verified; the auth gate's presence and
behavior are unchanged from before this pass either way.

**Visual smoke test — data confirmed, pixel rendering not.** Verified
directly (not assumed) that the correct data is present: pilot complete
(both parents 4/4), RL-2026-001 published/active (both parents 5/5
assigned, 0/5 answered — unread and untouched, per `## 20.8`), reviewers
list correct, rounds list correct. Could NOT visually render the actual
`/admin` page itself — Cloudflare Access intercepts every request to that
hostname/path at Cloudflare's own edge before any Worker code runs,
confirmed even via `wrangler dev --remote` (a live edge-routed preview,
not a local simulation) getting the same 302. This is Access working
correctly, not a limitation to route around — only Jascha's own
authenticated browser session can complete this specific check.

**No test round published or assigned to any reviewer during this pass.**
No B2/CJ/CJ-1/CJ-2 change. No RL-2026-001 content or response change. No
new reviewer credentials created or rotated in production.

### 23.9 HUMAN PRODUCTION SMOKE TEST — COMPLETE (2026-08-12)

The one check `## 23.8` couldn't complete itself is now done. First
attempt failed: "That account does not have access," from Cloudflare's
built-in IdP authenticating against the visitor's actual Cloudflare
dashboard login rather than an arbitrary typed email. Root-caused (not
guessed): this Cloudflare account's only member is `dev@nullspace.it`,
which wasn't in the policy's two-email allowlist. Confirmed directly with
Jascha before changing anything, then added `dev@nullspace.it` to the
same `allow` policy via the Access API (three emails now, still one
policy, still no `exclude`/`require`/broad rule — re-verified after the
change, not assumed). Jascha then visited `https://lab.cripminds.com/admin`
and confirmed by screenshot: the dashboard renders correctly against real
production data — `RL-2026-001` shown `ACTIVE`, `reviewer_parent_a`/
`reviewer_parent_b` both `0 / 5`, rounds table listing `RL-2026-001`
correctly (`Development`, 5 questions, 2 reviewers,
`2026-08-12 18:05`), `New round`/`Import draft` actions present. This is
independent confirmation of everything `## 23.8`'s own "visual smoke
test" section could only verify indirectly (via `EXPORT_TOKEN` reads) —
the admin control plane is now fully deployed, access-controlled, and
human-verified working end to end.

**Post-deployment regression check (2026-08-12, close-out pass):**
confirmed directly (not assumed) that the six legacy machine paths
(`/admin/status`, `/admin/export`, `/admin/items`, `/admin/invitations`,
`/admin/assignments`, `/admin/publish`) do not function as an accidental
second API surface. Against production: all six return `302` (intercepted
by Cloudflare Access before reaching the Worker at all). Against a fresh
local `wrangler dev --local` instance with no Access involved whatsoever:
all six return a plain `404` — proving structurally that the Worker's own
routing table no longer recognizes these paths, not merely that Access
happens to be in front of them. The real `/ops/*` equivalents were
confirmed reachable and functioning correctly in both environments. This
check is now a standing, repeatable procedure — see
`reader-lab-worker/README.md`'s "Regression check" section, to be re-run
after any future routing change.

**Standing verification caveat, preserved deliberately, not resolved:**
a *correct* `ADMIN_TOKEN` succeeding against `/ops/*` has still not been
positively exercised by this session — only wrong-token rejection was
verified (both times: initial deploy and this close-out pass). This
session does not retain the production `ADMIN_TOKEN` value, by design,
matching `## 22`'s credential-separation convention, and the secret was
NOT rotated to manufacture a test. The auth gate's presence and rejection
behavior are confirmed unchanged; only the positive-success path remains
unverified by this session specifically.

**Normal operating model, now live and confirmed:**

```
HUMAN:     https://lab.cripminds.com/admin, via Cloudflare Access
MACHINE:   /ops/* (X-Admin-Token or X-Export-Token, per-route privilege)
REVIEWER:  existing /invite -> /session -> /api/session -> /api/response flow, unchanged
```

No Round 002 created. No RL-2026-001 responses inspected or analyzed. No
B2/CJ/CJ-1/CJ-2 change. No credential rotated. No further deploy performed
in this close-out pass — every change was documentation plus the one
Access-policy addition (`dev@nullspace.it`) needed to let the confirmed
human identity in.

## 24. ROUTINE-OPERATIONS AUTOMATION (2026-08-12, infrastructure pass)

Purpose: everything through `## 23.9` still required Jascha (or a
privileged session) to notice a round had finished, and required a
privileged session to generate the credential-free research export
(`## 22`'s file-based handoff). This pass removes that dependency
entirely for routine use: **completion detection and research-export
generation are now fully automatic**, triggered by the reviewer's own
response, no polling, no scheduled process required to "notice"
anything. After this pass, the privileged Claude/Cloudflare session is
needed only for infrastructure work — deploys, migrations, Cloudflare
Access configuration, incidents — never for day-to-day round operation.

### 24.1 Completion detection — atomic, idempotent, no new route

`src/publish.js`'s `maybeCompleteRound(env, roundId)` is called from
`handleResponse` (`src/index.js`) immediately after a real response
commits and `assignments.answered_at` is set, using the assignment row
already fetched for the existing `item_not_assigned` check (no extra
query round-trip). It counts `total`/`answered` across every assignment
under that `round_id` and, only if every one is answered, performs:

```sql
UPDATE rounds SET status = 'completed', completed_at = ?
WHERE round_id = ? AND status = 'published'
```

The `WHERE status = 'published'` clause is the entire idempotency/
concurrency story: D1 serializes writes to a database, so exactly one
caller — the single request whose write happens to be the one that
finds every assignment answered — sees `changes > 0` and proceeds to
kick off export generation; a replayed/duplicate response (already
short-circuited earlier in `handleResponse` by the existing
`already_recorded` check, so it never even reaches this code) and any
near-simultaneous second reviewer finishing at the same instant both see
`changes = 0` and do nothing further. No cron, no polling loop, no
separate "did anything just finish?" query anywhere in the system — the
one response that completes a round is, by construction, the one and
only place that's ever true.

### 24.2 Research export — one shared service, never duplicated

`src/researchExport.js`'s `buildResearchExport(env, roundId, {actor})` is
the **only** place a round's judgments are ever turned into an export
artifact. Three call sites, one implementation:

- the automatic completion hook (`ctx.waitUntil` inside `handleResponse`)
- the admin UI's Retry button / the `/admin/api/rounds/:id/export/retry`
  route
- the hourly cron reconciliation sweep (`## 24.5`)
- the machine `GET /ops/rounds/:id/export` route

Security is by construction, not by review: the function's own SQL only
ever joins `rounds`/`items`/`assignments`/`responses` — it has no
reference anywhere to `invitations` or `sessions`, the two tables that
hold anything credential-shaped (`token_hash`, `session_id_hash`,
`contact_channel`). A future edit to this file that got the field list
wrong could still never leak a token or session hash, because the join
that would carry one simply doesn't exist in the query.

**Determinism.** Items are ordered by `assignments.item_order` (set from
the manifest's own slot number at publish time — a new, additive
`assignments.item_order` column; existing pre-migration assignments,
including RL-2026-001's, were explicitly backfilled from that round's
own already-public publication receipt, not fabricated — see `## 24.6`).
Reviewer IDs and each item's judgments are both sorted lexicographically
by `reviewer_id` — simple, stable, and reproducible on every regeneration
attempt, rather than trying to preserve authorial/submission order (which
isn't recoverable after the fact in this schema anyway, since batched
inserts within one `publishRound()` call share an identical timestamp).
The payload object is built with a fixed key order in code (never a
generic key-sorter), so `JSON.stringify` of it is byte-identical every
time the same underlying data is fed in.

**What's included**, matching the brief's own list: `export_version`,
`generated_at`, `round_id`, `manifest_sha256`, `dataset_purpose(_note)`,
`task_type`/`task_version`, `research_question`, blindness/provenance
metadata (`reviewer_blind_to_model_output`/`reviewer_blind_to_other_reviewers`/
`assistance_mode_required`), round timestamps
(`created_at`/`frozen_at`/`published_at`/`completed_at`), the frozen
`reviewer_ids` list, and per item: `slot`, `item_id`, `source_snapshot`,
`candidate_sentence`, both content hashes, `internal_note`, `provenance`,
and every reviewer's raw judgment (`selected_public_response`,
`internal_normalized_response`, `confidence`, `comment`, `timestamp`,
blindness flags, `assistance_declared`). **No computed "winner," no
consensus, no aggregation of any kind** — matching `## 14`'s original,
unchanged rule; a completed round's raw judgments are exactly as
authoritative and exactly as un-adjudicated as they've always been.

### 24.3 Immutability

A `ready` row in the new `research_exports` table (migration
`0003_research_export.sql`, additive) is a frozen snapshot.
`buildResearchExport` checks for an existing `ready` row FIRST and
returns it unchanged if found — it never recomputes, and the
`INSERT ... ON CONFLICT DO UPDATE ... WHERE research_exports.status != 'ready'`
that would otherwise write is itself conditioned on the row NOT already
being `ready`, a second, independent enforcement of the same rule at the
SQL layer. This is also exactly what makes every retriggerable path
(auto-trigger, manual retry, cron sweep, machine route) safe to call
redundantly on an already-complete round — "regenerate" and "no-op" are
the same code path once a round is `ready`.

Deliberately NOT built: a UI control to force-regenerate a `ready`
export. Per the brief's own instruction ("regenerate only through an
explicit versioned administrative operation if ever necessary"), if the
export *format itself* ever needs to change for a round that's already
exported, the correct action is a privileged, infrequent, manual step —
`DELETE FROM research_exports WHERE round_id = '...'` via
`wrangler d1 execute --remote`, then use the ordinary in-app Retry
button — not a self-service button that could be clicked by accident.
This is intentionally NOT a routine operation.

### 24.4 Storage choice — D1, not R2

Reader Lab rounds are small (3–5 items, a short excerpt + one sentence
each, two or three reviewers) — a complete export payload is a few KB,
nowhere close to D1's per-value size limits. Storing
`payload_json`/`content_sha256` directly in the new `research_exports`
table avoids adding a second storage binding, a second IAM/access
surface, and a second place secrets-exclusion has to be independently
verified, for no benefit at this scale. R2 would only earn its keep if
exports were large binary blobs or needed CDN-style public serving
outside the Worker — neither is true here. Not added.

### 24.5 Failure handling + reconciliation

If `buildResearchExport`'s own generation step throws for any reason, the
function catches it, writes `status = 'failed'` + `error_detail` to
`research_exports` (never losing track of the attempt), and returns a
structured failure — it never lets an export failure roll back or affect
the reviewer responses that were already durably committed before this
code ever runs. The round stays `completed`; the UI shows
`EXPORT ERROR — Retry available`.

Two independent retry paths, both calling the identical shared service:
an in-app **Retry export** button (round detail page and dashboard
card), and an hourly `scheduled()` cron job (`wrangler.toml`'s
`[triggers]`, `0 * * * *`) that finds every `completed` round without a
`ready` export row and retries each — a simple, idempotent safety net,
not a queue or workflow, per the brief's own "keep it simple" guidance.
Verified directly this pass (not assumed): a completed round with a
`failed` export was picked up and repaired by the cron sweep without any
manual action.

### 24.6 Migration `0003_research_export.sql` — additive

- `rounds.completed_at` (nullable) — set once, by `maybeCompleteRound`,
  never touched again.
- `assignments.item_order` (nullable) — set going forward by
  `publishRound()` from the manifest's own slot; backfilled for
  RL-2026-001's five pre-existing assignments from the exact,
  already-public slot→item_id mapping recorded in
  `.claude/reader-lab-handoff/RL-2026-001-publication-receipt.json` at
  publish time — this is not new inspection of anything (it's structural
  metadata already committed to this repo, not response content), and no
  answer/response content was read or touched to perform it.
- `research_exports` table (new) — one row per round;
  `payload_json`/`content_sha256` populated only on a successful
  attempt, `error_detail` only on a failed one, `generated_at` always
  set to the time of the most recent attempt either way.

Applied to production 2026-08-12: before/after row counts identical
across every existing table, all 14 pre-existing items' content hashes
byte-identical (diffed programmatically), RL-2026-001's `item_order`
backfill confirmed correct, RL-2026-001's `status`/`completed_at`
confirmed unchanged (still `published`/`null` — parent_a had not yet
answered at deploy time, confirmed via assignment counts only, never
response content).

### 24.7 Local test pass (before any production step)

Full round lifecycle exercised against a fresh local D1 replica with two
real test reviewers and adversarial content (embedded newlines, em-dash,
curly quotes, emoji, CJK characters, in both source/candidate text and
reviewer comments):

- one reviewer fully answered, the other not at all → round correctly
  stayed `published`, no export attempted.
- the second reviewer's final response (the actual last of four total
  answers across both reviewers) → round atomically flipped to
  `completed`, export generated automatically in the background with no
  added response latency.
- replaying that exact final response → `already_recorded: true`,
  export hash unchanged, exactly one `round_completed` audit-log row,
  exactly one response row — no duplicate completion, no duplicate
  export.
- downloaded export inspected directly: correct filename
  (`RL-2026-FINAL1-completed.json`), correct `Content-Disposition:
  attachment`, items in slot order, judgments within each item sorted by
  `reviewer_id`, every adversarial character preserved byte-exact
  (verified programmatically against the source strings, not eyeballed),
  zero occurrences of any secret/credential-shaped substring anywhere in
  the file.
- a separate round frozen/published but left unanswered → both the
  admin download route and the admin retry route and the machine
  `/ops/rounds/:id/export` route all correctly refused with
  `round_not_completed`.
- `EXPORT_TOKEN` successfully read a completed round's export via
  `/ops/rounds/:id/export`, and was independently confirmed unable to
  write anywhere (`/ops/items`, and no route exists for `POST` on the
  export path at all — `404`).
- a genuine failure was exercised (a round forced to `completed` status
  with a deliberately still-missing response, simulating a real bug
  class rather than assuming one): `buildResearchExport` correctly
  produced `status: "failed"` with a specific `error_detail`, wrote it to
  `research_exports`, and left every underlying response/assignment row
  completely untouched; fixing the missing response and retrying then
  succeeded; retrying again after success was confirmed idempotent
  (identical `generated_at`, proving no recomputation).
- unauthenticated access to the admin export download route: `401`.
  Reviewer-facing `/api/session` confirmed to never expose export or
  round-completion data of any kind — structurally impossible, since
  that handler's own query never selects those columns.
- the cron `scheduled()` handler was invoked directly (`wrangler dev
  --local --test-scheduled`) against a round whose export had been
  forced back to `failed`, and correctly repaired it to `ready` with no
  manual trigger.

### 24.8 Production deployment

Migration applied and verified additive (`## 24.6`). Worker deployed
(new Version ID recorded at deploy time) with the completion hook, the
export service, the new admin/`/ops` routes, and the hourly cron trigger
all live. Post-deploy verification, read-only throughout: reviewer route
unaffected (`404` for an invalid invite token, unchanged); `/ops/status`
via `EXPORT_TOKEN` showed `reviewer_parent_a` and `reviewer_parent_b`'s
assignment/answered counts exactly matching their pre-deploy values (no
data movement from the deploy itself, as expected — deploys change code,
never data); `/admin` still correctly Access-gated (`302`) for an
unauthenticated request. RL-2026-001's content, responses, and
in-progress (not yet `completed`) status were all independently
re-confirmed unchanged before and after — its answers were checked only
for *completion count*, never read or interpreted as research content,
consistent with every other pass touching this round.

### 24.9 Operating model, now fully self-service

```
HUMAN (normal, routine operation):
  https://lab.cripminds.com/admin — create/import, review, freeze &
  publish, wait (dashboard auto-detects completion), read Results,
  download the research handoff. Nothing else required.

PRIVILEGED OPS / wrangler / direct D1 (rare, infrastructure only):
  deployments, migrations, Cloudflare Access configuration,
  production incidents (e.g. a genuinely stuck export the in-app
  Retry button can't resolve).

MACHINE /ops/* (ADMIN_TOKEN / EXPORT_TOKEN):
  still exists for automation/debugging, including a read-only research
  export route — never required for the normal workflow above.

REVIEWER:
  existing /invite -> /session -> /api/session -> /api/response flow,
  completely unchanged throughout this entire pass.
```

No Round 002 created. No RL-2026-001 response inspected or interpreted —
only completion *counts* were ever read, both before and after this
pass's changes. No B2/CJ/CJ-1/CJ-2 change. No credential rotated. No
reviewer invitation/session model altered.
