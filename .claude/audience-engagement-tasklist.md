# Audience-engagement architecture tasklist

Origin: 2026-08-09 architecture review, after the module-split + rule-convergence
work finished that day (see `.claude/bregman-anchor-corpus.md` Section 6 and git
log `168ee79`..`97600e2`). The question asked was: *if I were building this system
to generate fun, engaging articles for a broad audience, would I build it the way
it currently is?* Verdict: the pipeline is well-built for **correctness**
(fabrication, passive voice, buried clauses, jargon) but has almost no machinery
for **engagement** — nothing closes a loop from real reader behavior back into
what gets written. This file is a discussion draft, not an approved plan — each
item needs your input before anything gets built. Don't start on any of these
without discussing first.

**How to use this file:** each item has a plan I'd propose, but also open
questions I can't answer without you. Read through, then let's talk — either
inline per item or as a general reaction.

**Status taxonomy, added 2026-08-10 after a multi-round reconciliation
check against session logs kept surfacing the same confusion.** Four
genuinely different states get flattened into "not done" if you're not
careful, and this file now has real examples of all four — check which
one actually applies before treating anything below as neglected:
- **DEFERRED** — designed, deliberately not built yet, waiting on a
  decision or on upstream evidence (e.g. CJ-2, anchor Stage D/E, the
  judge-panel/multi-draft experiment).
- **OPEN BUG** — actually broken, needs a fix (rare below; most of these
  got closed same-night as found).
- **WAITING FOR DATA** — built and running correctly, just needs real
  volume to accumulate before a decision can be made (CJ-1's 50/100
  threshold, anchor Stage B's real calibration pairs, adaptive use of
  engagement data).
- **REJECTED** — considered and explicitly turned down, not a future TODO
  (the fixed movement-sequence architecture; a broad "policy" keyword
  exclusion; a "Tier B" welfare exclusion list).
Treat this file as the authoritative current state; raw session logs are
provenance, not the live status — a claim that was correct when a log was
written (e.g. "404 Media is DNS-blocked," "ANSA's zero items might be a
date-parsing bug") can be superseded by later work in this same file
without the log itself being wrong at the time.

---

## Addendum, 2026-08-09: the anchor-architecture blueprint (feeds into item 3)

Separate from the priority list below, a real design investigation grew out
of studying a real Bregman excerpt (publisher-licensed, this session) for how
strong essays sustain a governing anchor across a whole piece. Full design
document produced by an Opus design agent — see this session's transcript;
key finding was that a "Stage 1 plan-then-write" mechanism already exists
(`_fable_editorial_brief`, `llm.py`) and runs daily, completely unverified.
This directly refines item 3 (judge-panel generation): the blueprint's Stage G
says once this mechanism is proven, two independent brief calls give the
judge panel genuine structural angle divergence for free.

**Progress so far, in the blueprint's own staged order:**
- **Stage 0 (persist the plan) — DONE.** `_persist_article_plan` (`generate.py`)
  logs the full brief JSON to a new `article_plans` table in
  `automation/engagement.db`. Pure logging, zero behavior change.
- **Stage A (baseline measurement) — DONE, and it validates the project.**
  The design agent's own crude script found 88% of articles already sustain
  a recurring term — a number that would have killed the project (the
  blueprint's own decision rule: >70% means the premise is dead). A more
  careful version (larger blocklist, confirmed non-sentence-initial
  occurrences, multi-word phrase matching) found the real number is **26%**,
  and roughly half of those are topical necessity (a piece about Deaf
  culture just says "Deaf" a lot) rather than a deliberate anchor device —
  the real rate for something resembling Bregman's device is closer to
  10-15%. **The gap is real. Building this is worth doing.**
- **Stage B (verification judge) — DONE, shipped in shadow.**
  `_plan_follow_read` (`review.py`) checks whether `correction_moment`/
  `resisting_example`/`opening_shape` were actually executed — wired into
  `validate_article`, persisted to `review_signals`. Before shipping, ran a
  **positive-control calibration**: fed the judge the real Bregman excerpt
  with a plan derived from the close-read, checked whether it agreed with
  the independent human analysis. First run surfaced two real bugs
  (`max_tokens=300` too low, `content[:14000]` truncating ~half the excerpt);
  after fixing both, **6/6 verdict-level agreement**. This is NOT the formal
  calibration the check's own design calls for (20 real cripminds
  (article, plan) pairs, ≥80% agreement) — that data doesn't exist yet since
  plans were never persisted before today. It's a sanity check that the
  judge design itself isn't broken, done before waiting weeks for real data.
- **Stage C (seam detector) — DONE, shipped in shadow.** `_check_seam_shadow`
  (`review.py`) — deterministic, detects a sentence ANNOUNCING a callback
  ("as I said", "to return to") rather than just making it. Built before
  Stage D/E exist, specifically so the instrument is ready before the
  mechanism that could trigger this failure ships. 2/6 real fixture articles
  tripped on "here is where i" — a real hit, not yet investigated (that's
  what the observation window is for).
- **Stage D (anchor/refrain brief fields), Stage E (writer-prompt block) —
  NOT STARTED.** Stage E is the first change that would actually direct what
  gets written; per the blueprint, it should not start before Stage B has
  accumulated real calibration data (~20 articles, several weeks at current
  cadence). Four blockers surfaced during design — see
  `.claude/bregman-anchor-corpus.md` Section 7 for full detail. Two are
  FIXED (2026-08-09 continuation): (3) `snapshot_test.py` now covers
  `_fable_editorial_brief`'s prompt construction (was zero coverage before);
  (4) the rewrite-pass/plan-following attribution gap is closed —
  `review_signals` now has a comparable pre- vs. post-rewrite verdict pair.
  Two remain deliberately unresolved, on explicit instruction: (1) the
  anchor-must-be-real constraint and (2) the refrain/crafted-rhetoric-ban
  conflict both only make sense as actual prompt text once Stage D/E is
  being built — pre-drafting that wording now would bias whoever designs it
  later (ideally another Opus-tier pass, same as the original blueprint).
  The requirement is documented; the wording is intentionally not.

**Explicitly rejected by the blueprint, with real evidence, not deferred:**
a fixed "movement sequence" (the original design's second half) — it's a
repackaging of a structural template this repo's own corpus file already
rejected twice, the real Bregman chapter's movements are legible only
because of section headings this pipeline explicitly bans, and there's no
arithmetic room at the pipeline's modal 950-word length. Replaced with a
"recurrence budget" (anchor + refrain, no ordering) which keeps the upside
without reversing that prior decision.

---

## Priority order (my read — argue with this)

1. Capture real engagement data (foundational — everything else needs this)
2. Persist engagement-read + shadow-check output to a queryable DB (cheap, unlocks analysis)
3. Judge-panel / multi-candidate generation (highest ceiling, highest cost) —
   **unresolved sequencing conflict, flagged 2026-08-09 audit, not yet
   decided:** item 3's own section below already committed to a hand-written
   "explicit angle instruction" divergence mechanism, built independently of
   the anchor-architecture blueprint. But the blueprint's addendum (above)
   separately claims that once Stage 0-E matures, two independent
   `_fable_editorial_brief` calls give judge-panel divergence "for free" —
   a different, likely-better mechanism for the same problem. These two
   plans have never been reconciled: does item 3 get built now with the
   hand-written approach, wait for Stage E, or get re-scoped so the
   hand-written version is explicitly a placeholder Stage E later replaces?
   Needs a decision before item 3 is actually built, not after.
4. Smarter topic/premise scoring at discovery time
5. Persona evolution tied to real reception (needs #1 first)
6. Shadow-check promotion decisions (already dated, 2026-08-23 — housekeeping, not new work)

---

## 1. No feedback loop from real reader behavior — DATA COLLECTION BUILT, 2026-08-09

**STATUS: `automation/engagement_fetch.py` built, tested end-to-end on trident
against real live data, working.** 354 real metric rows written on first run
(76 articles, last 90 days): GoatCounter pageviews for 39 articles, GSC
clicks/impressions/ctr/position for 45, Bluesky likes/reposts/replies/quotes
for 33, Mastodon favourites/reblogs for 1 (only one Mastodon post exists so
far). Tumblr returned nothing yet — expected, see the real bug found and
fixed below. All 5 sources needed zero new secrets beyond what already
existed on trident (see the credentials section below for exactly why).
Writes to `automation/engagement.db` (gitignored, stays on trident, same as
`disability_findings.db`).

**Second real bug found and fixed, 2026-08-09 continuation: scroll-depth
silently collected ZERO rows since launch, despite this section originally
claiming otherwise.** The 354-row figure above did NOT include scroll-depth
— corrected here rather than left wrong. GoatCounter stores automatic
pageview hits (event=0) without a trailing slash but custom-event paths
(event=1, this site's own scroll-depth tracker in `_layouts/default.html`)
with whatever `location.pathname` gave it — which always has the trailing
slash for this site's permalink structure. `engagement_fetch.py`'s scroll
query stripped the trailing slash the same way the (correct) pageview query
does, so every scroll-depth lookup matched zero rows from this script's
first commit onward — confirmed by reading GoatCounter's raw `paths` table
directly, not by inspecting the fetch script's logic alone. Fixed (one
query, plus added depth 100 which the site's JS tracks but the script never
queried), re-run manually to backfill: went from 354 to 447 rows, with real
scroll-depth data now present — 35/39 articles reaching scroll-25%, 31
reaching scroll-50%, 24 reaching scroll-75%, 3 reaching scroll-100%.

**Real bug found and fixed along the way: Tumblr posting had likely never
actually worked.** While testing whether Tumblr engagement was readable,
found that `config.py`'s secrets-loading block only ever sourced
`openclaw.env` and `reef-bot.env` — never `tumblr.env`, despite it having
real, valid, non-empty credentials the whole time. Every `post_to_tumblr`
call hit `os.environ.get("TUMBLR_CONSUMER_KEY", "")` → empty string → the
method's own `if not all([...]): return None` guard silently no-op'd it at
debug level. Confirmed via zero `_social/*.json` files, across every article
ever published, ever having a `tumblr_url` field. Fixed (one line, `config.py`
now also loads `tumblr.env`) and confirmed on trident: credentials load
correctly now. The next `publish_best.py` cron run (every 2 days, 08:00) will
be the first time Tumblr posting has actually fired.

**Not yet done:** this isn't scheduled on cron yet — ran manually twice
during testing. Needs your go-ahead before it becomes a recurring job (see
open question below). Still pure data collection either way — nothing reads
this table back into generation decisions yet, same as before.

**The problem, confirmed by reading the code, not guessing:** `_store_social_uri`
only ever stores a Bluesky/Mastodon/Tumblr post URI so a *retraction* can delete
it later. Nothing anywhere reads back likes, reposts, replies, or click-through.
Register/length/article-type selection (`_REGISTERS`/`_LENGTHS`/`_ARTICLE_TYPES`
in `config.py`) are fixed weighted-random numbers, never adjusted by outcome.
The system publishes into a void.

**Confirmed 2026-08-09, this is better than either of us assumed going in.**
Real analytics infrastructure already exists — just never wired into the
pipeline:
- **GoatCounter**, self-hosted at `stats.cripminds.com` (`_layouts/default.html`
  line 355). Already firing real custom events: per-article scroll-depth
  tracking (`scroll-25%`, `scroll-50%`, etc. — a genuinely better "did someone
  actually read this" signal than raw pageviews) and homepage
  section-reach/click events. Confirmed by reading the actual script tags —
  this was NOT the Google Analytics either of us first guessed.
- **Google Search Console** — real, actively used (a past session resolved a
  GSC indexing question, see project memory `cripminds-gsc-continuation`).
  Gives search query/impression/click/CTR data per URL — a different, also
  valuable signal (does the *headline* make people click from search results).
- **Zero wiring into `automation/` for either** — confirmed via a repo-wide
  grep for "goatcounter"/"analytics" outside the HTML templates: no hits.

**Revised plan, now concrete instead of speculative:**
- GoatCounter exposes a stats API (self-hosted instance, needs an API token —
  check `/srv/secrets/` on trident for whether one already exists from manual
  dashboard use, or generate one in the GoatCounter admin UI). Pull per-path
  pageviews + scroll-depth event counts for recent articles on a schedule.
- GSC has a Search Analytics API (needs a Google Cloud service account or
  OAuth — check if one already exists for the prior GSC investigation before
  setting up a new one). Pull per-URL impressions/clicks/CTR.
- New DB table: article slug, persona, register, length, article_type, topic
  theme, post date, GoatCounter pageviews + scroll-depth-50%+ rate, GSC
  impressions/clicks/CTR — a few snapshots per article over time, not just one
  (both metrics accumulate for days/weeks after publish).
- Run on a schedule (daily cron, alongside `cripminds-daily.sh`).
- **Do NOT wire this into anything that changes generation behavior yet** —
  pure data collection first, same observation-before-action discipline as the
  shadow checks. Behavior changes come after enough data exists to trust a
  correlation, which is weeks away no matter what.

**Confirmed 2026-08-09 (from you): all three social platforms are live and in
scope** — Bluesky, Mastodon, and Tumblr (the "gallery" one, image-forward).
All three already have posting wired (`post_to_bluesky`/`post_to_mastodon`/
`post_to_tumblr` in `social.py`) and URIs stored for retraction — same
zero-feedback-loop gap as described above, just three channels instead of
one. Revised table plan: same schema as above, plus per-platform
like/repost/reply/favorite counts (each platform's API differs — Bluesky via
AT Protocol, Mastodon via its REST API, Tumblr via its API — three small
fetchers instead of one, same shape).

**Credentials — ALL FIVE CONFIRMED WORKING, zero new secrets needed
anywhere** (checked and tested directly on trident, 2026-08-09; key names
only where relevant, no secret values ever read into this conversation):
- **GoatCounter:** not behind an API at all — a systemd service on the host
  storing everything in a plain SQLite file at
  `/srv/data/goatcounter/goatcounter.db`. Queried directly, read-only, no
  auth. Real numbers: e.g. one article reached scroll-25% by 12 sessions,
  scroll-50% by 11, scroll-75% by 8; July 2026 articles range 1-18 pageviews
  — genuinely low-traffic for a young publication, worth keeping in mind for
  how long "enough data" will realistically take to accumulate.
- **GSC:** reuses the existing `google-calendar.json` service account
  (`trident-calendar@gen-lang-client-0047032066.iam.gserviceaccount.com`) via
  an RS256-signed JWT — no new credential file. You enabled the Search
  Console API and added that service account as a property user; tested the
  full flow (JWT → OAuth token → Search Analytics query) and got real
  per-page clicks/impressions/ctr/position back. One correction from the
  original plan: the property is the **domain property**
  `sc-domain:cripminds.com`, not the URL-prefix `https://cripminds.com/` I
  first guessed — confirmed via a real `/sites` list call; the wrong format
  403s.
- **Bluesky:** `app.bsky.feed.getPosts` on the **public, unauthenticated**
  endpoint (`public.api.bsky.app`) — no session/login needed at all to read
  engagement on public posts. Tested against 33 real posts, got real
  like/repost/reply/quote counts back.
- **Mastodon:** `GET /api/v1/statuses/<id>` is also public, zero auth needed.
  Tested against a real published post, got real favourites/reblogs/replies
  counts back.
- **Tumblr:** `GET /v2/blog/<blog>/posts?api_key=...` returns real
  `note_count` per post using just the plain consumer API key as a query
  param — no OAuth1 signing needed for reading (posting still needs full
  OAuth1, unchanged). Tested against real live posts on the blog.

**ITEM 1 COMPLETE, 2026-08-09.** Scheduled on trident's crontab: daily 11:00,
`git pull` + `python3 automation/engagement_fetch.py --days 90`, logging to
`automation/engagement_fetch.log`. Installed via a diffed crontab swap
(confirmed exactly 3 lines added, nothing else touched, then verified the
installed crontab matches byte-for-byte). No more open questions on this
item — it now runs unattended, accumulating real engagement data every day.
Nothing reads this data back into generation decisions yet, per the
observation-before-action discipline established for the shadow checks —
that's a separate, later item once enough data exists (see the priority
order at the top of this file).
  already on trident covers auth.
**Decisions (2026-08-09):**
- Build all three (GoatCounter, GSC, social) together — one schema, in one
  pass, rather than sequencing by priority.
- Candidate-divergence mechanism for item 3 (below): explicit angle
  instruction, not temperature alone.
- Item 3 rollout: shadow mode first — generate 2, judge, but keep publishing
  whatever the current single-draft path produces until the judge's picks
  have been eyeballed against real outcomes.

**Engagement-system audit, 2026-08-10 — three confirmed bugs fixed, one
left OPEN, one flagged for later.** An Opus review, briefed to trace real
records rather than just inspect functions, found the schema/design
choices (V8: time-series genuinely preserved, not overwritten; correct
GSC JWT flow; correct Bluesky/Mastodon ID handling; nothing downstream
reads this data yet, confirming the observation-freeze claim is actually
true) were sound, but found real correctness bugs underneath:
- **B1 Tumblr matching — FIXED IN CODE, LIVE VERIFICATION PENDING.**
  Precision matters here: "fixed" describes the join logic, not an
  end-to-end confirmation — those are different claims and this file
  should not flatten them. The join key was an exact string match between
  two URL shapes that are not the same (stored `tumblr_url` has no slug
  segment; the API's real `post_url` always does) — `remaining.pop()`
  returned `None` on every post, forever. Fixed in `a945f9a`: join on
  numeric post ID instead, checked against the actual Tumblr API response
  shape. But the test run that confirmed this returned early — zero
  `_social/*.json` files currently contain a `tumblr_url` at all, so the
  matching branch itself never executed; the run just hit the "nothing to
  match" short-circuit. The full chain this needs to prove is: CripMinds
  article → Tumblr publish → `tumblr_url` persisted → Tumblr API fetch →
  matching branch executes → metrics stored. That chain has not happened
  once yet. First real verification is whenever the next `publish_best.py`
  cycle actually posts to Tumblr — separately, real `note_count` on the
  blog is currently 0 regardless (**Tumblr current engagement signal —
  WAITING FOR DATA**, distinct from the code-correctness question:
  repairing collection does not manufacture engagement that doesn't
  exist). Do not read "verified end-to-end" into this fix before that
  chain fires once — that would be an overclaim this file has specifically
  tried to stop making tonight.
- **B2 source isolation — FIXED.** GoatCounter's fetcher was the only one
  of five with no try/except, and ran first — an exception there
  previously aborted the whole run and rolled back everything already
  collected that day before GSC/Bluesky/Mastodon/Tumblr even ran. Now
  isolated per-article; every fetcher commits its own writes immediately.
- **B3 run/failure observability — FIXED.** No failure signal existed
  anywhere — exit code always 0, log always said "Wrote N rows" whether
  or not every source actually worked. This is the exact condition that
  let B1 and the earlier scroll-depth bug hide from first commit. Per
  explicit requirement (partial success must never look identical to full
  success): `main()` now reports one of three states — SUCCESS (all 5
  clean), PARTIAL (some failed), FAILURE (none did) — exit 0/1/2.
- **B4 cron/git-pull observability — OPEN BUG, not fixed.** `git pull &&
  python3 engagement_fetch.py` in the crontab means a pull failure
  silently skips the entire fetch with zero visible difference from a
  normal successful day. Same failure family as B3, one layer up, outside
  the Python collector. Left open deliberately — an operational wrapper
  fix, not touched in the same pass as B1-B3. Today's 11:00 run is still
  the first-ever unattended execution of this script (confirmed: the log
  file didn't exist before this session, all 447 prior rows came from
  manual test runs) — worth checking after it fires.
- **Tumblr historical diagnosis — DOC CORRECTION.** This file previously
  claimed Tumblr "had likely never actually worked." Independently
  confirmed false: the blog published roughly daily until 2026-05-07, then
  stopped — the break lines up with the Hermes migration (2026-05-02), not
  a never-worked architectural defect. The `config.py` env-loading fix
  from item 1's original writeup is still the right fix; the diagnosis of
  *why* it was needed was wrong. Matters because "never integrated" and
  "worked, then regressed at a known boundary" point debugging in
  different directions.
- **GSC rolling-90-day window — WAITING / ANALYSIS PREREQUISITE, not
  fixed.** Every run queries a trailing 90-day window; GoatCounter and
  social counts are cumulative/lifetime. A GSC value recorded today can be
  *lower* than the same metric weeks ago purely because old days aged out
  of the window — a naive time-series read would misread that as
  engagement decay. Must be accounted for before GSC history is ever used
  to compare articles or inform a weight. Not urgent while nothing reads
  this data back (see below).
- **Engagement → generation leak — VERIFIED ABSENT.** Repo-wide grep
  found no consumer of `engagement_metrics` anywhere. The observation-
  freeze claim already made in this file is independently confirmed true,
  not just asserted.

---

## 2. Persist engagement-read + shadow-check output — DONE, 2026-08-09

**STATUS: COMPLETE.** `_persist_review_signals` (`review.py`) logs every
`_engagement_read` verdict and all 3 shadow-check results to a new
`review_signals` table, called from `validate_article` right after the
existing markdown sidecar write — the sidecar still gets written too,
nothing removed. Written to the *same* `automation/engagement.db` that
`engagement_fetch.py` (item 1) already writes real reader-engagement data
to — same file, different table, so correlating "did the judge guess this
was good" against "did readers actually stick around" is a plain `JOIN` on
`slug`, not a cross-database query. Wrapped in try/except — a persistence
failure can never affect `validate_article`'s own return value.

Verified via a direct functional test (real write + confirmed the
`UNIQUE(slug, reviewed_at)` upsert behavior works, not just "doesn't
crash" — caught and fixed a real robustness gap in the process: the DB's
parent directory isn't guaranteed to exist in every context, now created
defensively). Deployed to trident and confirmed the method loads correctly
there. Real data will start accumulating from the next `validate_article`
call in the daily 09:00 generation cron.

This also makes the 3 shadow checks' 2026-08-23 promotion decision
evidence-based — query real false-positive counts from `review_signals`
instead of re-reading `_reviews/*.md` files by hand.

---

## 3. Judge-panel / multi-candidate generation — DELIBERATELY DEFERRED, NOT BUILT

**STATUS, made explicit 2026-08-10 after a reconciliation check caught this
item had no status marker at all (every other item does) and could easily
get silently read as "handled" by a future skim.** Option (b) was decided
in principle on 2026-08-09 (see "Decisions" below) but the two-draft
generation code itself was never written — the session's attention moved
to the Bregman close-read instead, which produced the whole anchor-
architecture blueprint (Stages A-E below) and, separately, the discovery-
side category-jump judge (item 4). Neither of those retroactively builds
this. Revisit only after the upstream premise/anchor experiments (item 4's
category-jump calibration, anchor Stage B) have real evidence — building
a judge panel on top of an unvalidated angle-selection mechanism would be
premature.

**The problem:** the gate's own validated test data (see the comment in
`gate.py` around the register-violation escalation logic, from a real
2026-08-07 test) found that even a full-rewrite pass barely moves a bad draft —
13-15 remaining issues, down from 15-24. The ceiling on quality is set almost
entirely by the first draft. Nothing downstream can turn a mediocre draft into
a great one; it can only make a mediocre draft slightly less mediocre.

**Proposed plan — three options, increasing cost/risk:**
- **(a) Cheap:** generate 2-3 candidate *opening paragraphs* only (not full
  articles) from different angles, judge which is strongest, commit to that
  angle before generating the rest. Small added cost (a few hundred tokens ×
  2-3), no change to the main generation call.
- **(b) Medium:** generate 2 full draft candidates in parallel, judge, keep the
  better one, discard the other. Roughly doubles generation cost and adds
  latency (parallel calls mitigate the latency, not the cost).
- **(c) Expensive:** full judge-panel — 3+ candidates from genuinely different
  angles/personas' takes on the same topic, scored by multiple judges,
  synthesize or select. Highest ceiling, highest cost, most complex to build
  and debug on a live pipeline.

**Decision (2026-08-09): going straight to (b) — full 2-draft generation.**
Skipping the cheaper opening-only prototype; testing the real ceiling question
directly.

**Concrete design for (b):**
- In `_run_production_automation_locked` (`generate.py`): after building the
  ~150-line generation prompt (unchanged), call the writer LLM twice — same
  prompt, relying on sampling temperature for divergence, OR add one line
  telling candidate B to "take a different angle than the obvious first
  instinct" for a more reliable difference (needs deciding — pure temperature
  variance may not diverge enough to matter).
- New comparative judge step: a dedicated prompt showing both full drafts side
  by side, asking which one a real reader would rather keep reading and why —
  distinct from `_engagement_read` (which judges one piece in isolation, no
  comparison). Could either build this fresh or extend `_engagement_read` to
  optionally take two candidates; fresh is probably cleaner since "judge A vs
  B" and "judge one piece" are different enough prompts.
- Keep the winning draft, discard the loser entirely (do not try to merge/
  graft — that's real complexity for a first version; a straight pick is
  simpler and testable).
- The winning draft proceeds through the existing pipeline unchanged (gate,
  images, publish) — this only touches the generation step.
- Cost: roughly doubles the main writer-generation call's cost, plus one
  judge call. Latency: the two generation calls can run in parallel; the
  pipeline's daily 09:00 cron has no tight downstream time budget I'm aware
  of, so added latency is likely fine, but worth confirming nothing else waits
  on this cron slot finishing by a specific time.

**Decisions (2026-08-09):** explicit angle instruction for candidate B (not
temperature alone); ship in shadow mode first (generate 2, judge, but keep
publishing whatever the current single-draft path produces) — log both the
winning and losing draft plus the judge's reasoning to the review sidecar so
picks can be eyeballed before this is trusted to decide what actually
publishes, same discipline as the 3 shadow checks already running.

**How "explicit angle instruction" would actually work — four candidate
mechanisms discussed in conversation, never written down before this audit
(2026-08-09):**
1. **Structural-shape alternation.** `_STRUCTURAL_SHAPES` is already a fixed
   list in the codebase (quantify-then-critique, scene-then-theory,
   reframe-definition, historical-anchor, counter-assumption,
   comparative-case) — currently only used as a flat diversity guard
   (checks overuse after the fact), not something a candidate is told to
   commit to before writing. Candidate A generates normally; candidate B
   gets explicitly told to use a different shape from the list. Most
   concrete and cheapest to implement — a fixed list already exists, and
   it's easy to explain in the judge's reasoning ("candidate B used X
   shape, A used Y, judge preferred X because...").
2. **Sub-angle within the same topic.** E.g. for a topic like AI hiring
   bias, candidate A leans into the audit/compliance angle, candidate B
   into the lived-experience angle. More interesting than (1) but needs the
   discovery/prompt step to surface more than one candidate angle for a
   given topic — not guaranteed to exist for every discovery item.
3. **Persona-beat foregrounding.** Each persona already has multiple beats
   (`_AGENT_BEATS`); candidate A emphasizes one, candidate B another.
4. **Freeform instruction** — "don't take the most obvious angle" — relying
   on the model's own judgment of "obvious" with no concrete alternative
   given. Simplest to implement, vaguest to reason about why one candidate
   won, hardest to learn from when eyeballing shadow-mode results.

No final choice among these four was recorded before the session moved on
to the Bregman close-read that produced the anchor-architecture blueprint —
which is why the sequencing conflict flagged in the priority-order section
above exists: the blueprint's Stage G note (two independent
`_fable_editorial_brief` calls giving divergence "for free") is really a
fifth candidate mechanism, proposed later and never compared against these
four. Whoever builds item 3 needs to pick one of these five, not assume
"explicit angle instruction" already specifies which.

---

## 4. Smarter topic/premise scoring at discovery time

**Discovery-pipeline overhaul, 2026-08-09/10 — DONE, recorded here after a
reconciliation check found none of this had actually made it into this
file, only into commit messages and conversation.** Triggered by watching
a real generated article turn out to be an NHS-mental-health-cuts policy
piece. In order: excluded mental-health-news-cycle content; found the
real root cause (the disability-lens boost was empirically a welfare-
administration-journalism detector, not a lens detector — 74% of boosted
items cleared selection vs 18% unboosted, concentrated in 2 feeds) and
rescoped it; added `THEME_WEIGHTS` multipliers so the existing
architecture/space/mythology editorial preference (508cc86) is actually
encoded in ranking, not just feed selection; added a narrow policy-process
exclusion (program names like "white paper"/"DWP", not the bare word
"policy" — a broader version was tested and rejected for false-positiving
on real art journalism — **REJECTED, not deferred**); added 12 new feeds
(Deaf/disability-specific, art/design, tech/industry on explicit request
despite editorial mismatch, international/regional) plus a genuine
root-cause fix for 404 Media (DNS poisoning on trident's own WiFi resolver
via the router, not a real network block). A follow-up review then found
the exclusion lists were zeroing real disability-arts content that
mentioned an excluded phrase in passing — fixed by gating exclusions on
dominant theme. Owner-requested healthcare exclusion (broader than
mental-health, explicitly accepted the collateral-risk tradeoff going in)
briefly re-broke the same two art pieces and was reverted to the same
theme-gated pattern within the hour.

**Real first-fetch results from the 12 new feeds** (never previously
written down): Techmeme, Rest of World, The Limping Chicken, Le Monde
Arts, ANSA English, and Creative Boom all cleared the 0.4 selection gate
on real content the same night — better than a synthetic pre-check had
predicted for the tech/industry feeds specifically. Hacker News and The
Creative Independent scored real items but stayed below the gate (n too
small to judge yet). Two feeds returned zero items, both diagnosed as
**external-source conditions, not pipeline bugs**:
- **Disability Visibility Project** — dormant. `lastBuildDate` on the live
  feed is 2026-02-13, six months stale, HTTP 200 throughout. Same pattern
  already documented elsewhere in this file for El Pais English (live but
  frozen). No code issue.
- **ANSA Emilia-Romagna** — healthy feed, scorer mismatch. Confirmed via
  direct fetch: real items dated today, RFC-822 dates parse cleanly, zero
  errors. Real headlines (generic Italian local crime/accident news —
  child hospitalizations, traffic incidents) score `0.0` under
  `score_item()` because the content is in Italian and `THEME_KEYWORDS` is
  English-only vocabulary — there is no bug for a hand-check to find; the
  feed and the scorer are both doing exactly what they're built to do,
  they just don't intersect for this source's typical content.

**The problem, corrected 2026-08-09 after verifying against the actual code
(the original write-up below had the wrong file for one piece of it):**
topic scoring is RSS-keyword matching, but it lives in `automation/
news_fetcher.py` (`score_item`, a separate 06:00 cron script) — not
`discovery.py`. `news_fetcher.py` scores each RSS item via whole-word
`THEME_KEYWORDS` matching plus a +0.3 disability-angle booster, stores it as
`relevance_score` in the `news_seeds` table; `discovery.py` then does a
deterministic greedy top-1 pick by that score (`get_news_seed`), or by a
similar keyword-density `confidence` score from the legacy `findings` table
(`get_discovery_from_database`), or a persona-keyword-hit count with an
80/20 top-1-vs-top-5 randomizer (`_pick_news_item`). All the craft investment
downstream (personas, rules, the engagement-read check) is applied to
whatever this keyword-matching step picked. If the premise itself isn't
interesting, no amount of sentence-level polish saves it. **What's
confirmed NOT to exist anywhere in this chain: any LLM judgment of how
*interesting* a candidate angle is** — the one existing LLM call at
discovery time (`extract_angle` in `news_fetcher.py`) only decides whether a
disability angle exists at all (produces an angle sentence or `NONE`), it
doesn't rank quality/interest.

**Diversity-tracking question, resolved 2026-08-09 (was previously
unverified) — all three mechanisms are genuinely ACTED ON, not just
tracked, so item 4 would be adding something new, not duplicating an
unused mechanism:**
- `_get_recent_title_patterns` (`discovery.py`) is spliced directly into the
  writer prompt's title-rules block (`generate.py`) — "recent title
  structures to avoid repeating."
- `_get_recent_openings` (`discovery.py`) feeds the editorial-brief prompt
  (`llm.py`) with an explicit "pick a different shape" instruction when
  recent openings all share one.
- `_STRUCTURAL_SHAPES` — correcting a misattribution from an earlier
  session: this is NOT used in `review.py` as a diversity guard. The real
  mechanism is `_classify_shape`/`_get_shape_nudge` in `discovery.py`,
  which reads the last 10 articles' shapes and, if the last 3 repeat,
  injects a "find a different argumentative entry point" nudge directly
  into the writer prompt at generation time (`generate.py`) — a real,
  pre-generation soft nudge, just not where it was previously said to live.

**Proposed plan (mechanism unchanged by the above; still needs your input
before building):**
- Add an LLM-judged "angle interest" score at discovery time — similar
  mechanism to `_engagement_read` but running on the *candidate topic +
  proposed angle*, before generation, not on the finished article. Cheap
  (short prompt, short response) since it's judging a headline + summary, not
  a full article. This would slot in after `news_fetcher.py`'s keyword
  scoring and before `discovery.py`'s greedy top-1 pick — genuinely new,
  not a duplicate of anything found above.
- Once #1's real engagement data exists, correlate which topic clusters/
  themes actually perform, and feed that back into `THEME_KEYWORDS`'
  weighting in `news_fetcher.py` — but this is downstream of #1, not
  something to build first.

**RESOLVED, 2026-08-10 continuation — calibration input obtained via an
external model with real history on the owner's taste** (not by the owner
recalling examples from memory as originally asked — a portable prompt was
built and used instead). Two consultation rounds, the second explicitly
correcting the first:

- **Positive gold-standard** (kept after both rounds): Sara Hendren, "All
  Technology Is Assistive" (WIRED) — Eames splint -> modernist furniture;
  Jane Jacobs, "The Uses of Sidewalks: Safety" — busy sidewalk -> security
  infrastructure.
- **Downgraded on the second round**: Ta-Nehisi Coates, "The Case for
  Reparations" — real category jump (house purchase -> extraction
  mechanism), but judged too broad a taste prediction; the owner already
  holds the underlying argument, so the case makes it tangible without
  making the owner rethink the object as violently as the other two.
- **Same-genre negative controls** (competent journalism that still fails):
  a Guardian first-person wheelchair-accessibility piece, and an older
  Guardian web-accessibility piece with a real named source (Paresh
  Jotangia) and real screen-reader detail. Both kept specifically to kill
  a shortcut: "named person + concrete detail + disability" is NOT
  sufficient — the lens has to change what the *system* is or does, not
  just show who it excludes.

**The core test, sharper than Stage B's "correction moment + resisting
example" fields (generation side)**: a disability lens must reveal a
hidden mechanism of the thing/system itself. "Public transport is hard for
wheelchair users" names harm; "a feature meant to speed passenger flow
strands one kind of passenger" reveals the system's actual optimization
target.

**Naming note, added 2026-08-10 after a reconciliation check flagged this:**
this section's "Stage 1"/"Stage 2" are renamed **CJ-1/CJ-2** (category-jump
1/2) below, to stop colliding with the UNRELATED anchor-architecture
Stages A-E above (and an even older "Stage 1 plan-then-write" reference in
this file's Addendum, from before that work was renumbered Stage 0). Same
mechanisms, same decisions — naming only.

**CJ-1 (category-jump judge) — BUILT, shipped in shadow mode,
2026-08-10.** `category_jump_judge()` (`automation/news_fetcher.py`) runs
on the same candidates `extract_angle()` already processes, returns a
structured verdict (decision, ostensible_category, resisting_detail,
hidden_mechanism, category_jump, evidentiary_bridge, correction, reason),
persisted to a new `category_jump_shadow` table. Never conditions
selection/generation — pure observation.

Real first-batch results, then corrected after live calibration feedback:
- Banksy statue piece (blindness-as-nationalist-metaphor) → NO, correctly
  — disability is the stated metaphor already, nothing forces a
  reclassification. Named as a deliberate negative example: "metaphorical
  disability rather than embodied epistemology" is close to the *inverse*
  of what this publication is for.
- El Salvador health-monitoring-app story → flipped YES to NO after adding
  the **evidentiary-bridge test** (test 6): the judge must quote/paraphrase
  the exact source fact supporting a proposed jump, not invent the causal
  bridge itself ("Google is private, therefore private demand generation"
  is the model's own inference, not a stated/implied fact). Flagged as
  "probably the most important calibration change" before this leaves
  shadow mode — confirmed live, it does exactly what it was meant to.
- Alzheimer's-drug efficacy review → strong YES, with a real grounded
  bridge (the source explicitly states both the "gamechanger" framing and
  the "trivial" trial result). Real bug found and fixed along the way:
  `max_tokens=500` was too tight (a valid, verbose response landed within
  a few dozen tokens of the cap; a less lucky generation on the same item
  hit the cap mid-JSON-string and silently returned None) — bumped to 900.

**Sampler decoupled from real selection, 2026-08-10, second calibration
round.** Judging only `extract_angle`'s keyword-scored top-10 would
re-import the exact problem CJ-1 exists to escape. `sample_shadow_
candidates`/`run_category_jump_shadow` now sample independently — a fixed,
NOT-tuned-by-early-results 3-lane split (~30% `keyword_top`, ~30%
`keyword_low` — genuinely lowest-scoring, not merely "outside the top 10"
— ~40% `broad_random`, capped per-source), sampled before any semantic
ranking (only legitimately-unusable items excluded: used, already
angle-checked, outside the age window). Writes only to
`category_jump_shadow`; `extract_angle`'s pool, which actually drives
selection via `disability_angle` gating `get_news_seed`, is untouched.
Every row tagged with `candidate_origin`, `sampler_version`,
`judge_prompt_version`, `model_version` so a later change never silently
contaminates historical comparisons. Judge failures now split into
`attempt_status` (success/error) and `error_type` (timeout/model_error/
empty_response/invalid_json/no_api_key) — decision coverage and taste
calibration are different questions, must never be conflated (the same
lesson as the max_tokens bug above). Verified end-to-end on trident: 3
real judgments, one per lane, all fields populated correctly.

The question this now lets the shadow window actually answer, per the
calibration source: not just "does CJ-1 work" but *where do the real
YESes come from* — if `keyword_top` produces more YESes but calibration
prefers the ones found in `keyword_low`/`broad_random`, that's a much
sharper diagnosis than "keywords bad": it means the old scorer selects
*obvious* mechanisms while suppressing the *stranger* ones this
publication actually wants.

**Deliberately deferred until the first sampler-balanced batch says the
basic experiment works** (do not build before then): mechanism-fingerprint
fields (surface_object/hidden_action/hidden_function, to make the
"grand-theory sink" false-positive checkable in the data), bridge-strength
self-report (DIRECT/IMPLIED/SPECULATIVE), retry logic, CJ-2, novelty/
familiarity judging. Resist touching the judge prompt again until then —
"you now have enough instrumentation to learn from the system instead of
continuing to design it theoretically."

**CJ-2 (persona-specific reframe) — DESIGNED, NOT BUILT.** Deliberately
asymmetric from CJ-1: CJ-1 asks "is there something objectively
strange here"; CJ-2 asks "does this persona's specific embodied lens
reveal something *additional* about that strangeness" — given the CJ-1
jump as a hypothesis to interrogate, not independently re-derived per
persona (avoids recreating the original keyword-density problem four
times over, with personas as motivated reasoners manufacturing relevance).
CJ-2 needs its own NO: a real category jump can exist with nothing
distinctive for any of the four personas to add. Operational test: "if I
removed the persona's disability from the argument, would substantially
the same essay remain? If yes, CJ-2 fails." Full prompt drafted (system
prompt + 6-test structure + JSON schema), run independently once per
persona (4x), article survives if at least one persona produces a strong
YES. Held deliberately — bigger, separate decision, not built until
CJ-1's shadow data confirms the anomaly-detection gate itself works.

**False-positive taxonomy to watch for during the shadow window** (named
during calibration, not yet systematically checked against real shadow
data):
1. *Grand-theory sink* — jump lands on a large ideology (capitalism,
   surveillance, neoliberalism) rather than a specific mechanism (converts,
   ranks, delays, measures, hides, rewards, substitutes, routes,
   normalizes, prices, filters). Weak: "AI monitoring -> capitalism."
   Strong: "AI monitoring -> mechanism that converts diagnosis into
   privately controlled follow-up demand."
2. *Clever reinterpretation without source friction* — LLMs are good at
   producing a plausible-sounding jump with no real resisting detail
   grounding it (the evidentiary-bridge test targets exactly this).
3. *Real mechanism, no persona leverage* — e.g. "concert ticket queue ->
   dynamic pricing market" could be a great Atlantic piece and a bad
   CripMinds piece if no embodied lens changes what dynamic pricing means.
   CJ-2's job, not CJ-1's.
4. *Culturally exhausted mechanism* — passes every logical test and is
   still dull ("social media feed -> attention extraction machine" — true,
   concrete, and already widely known). Needs a familiarity filter, not
   yet designed: would an informed reader already know the destination
   before paragraph one?
5. *Metaphorical disability as material, not epistemology* — the Banksy
   case's category. Almost the inverse of this publication's purpose.
6. *Category jump without a scene* — a real mechanism (e.g. credit scores
   encoding geographic segregation) with only aggregate statistics, no
   person/object/decision/moment to build an essay around. Real research
   material, not necessarily essay-generating material on its own.

**Shadow-mode exit criterion, decided but not yet reached**: do not
promote out of shadow mode on volume alone. Target: manually examine at
least 50 CJ-1 YESes and 100 NOs (150 items total — corrected 2026-08-10,
~15 days at ~10/day sampled, not "about a week" as first estimated;
asymmetric — false positives cost more
here than missed stories, since RSS supplies endless raw material but
each YES consumes expensive downstream stages) from a corpus sampled
across ALL source types deliberately, not just tech/disability/medicine
feeds (calibrating only on those rebuilds topical selection through the
back door). For the YES batch: target ~8/10 feeling genuinely worth
investigating, not merely defensible — if only ~5/10 do, the gate is too
permissive. For the NO batch: spot-check rather than only reviewing near
misses; if a meaningful fraction make you say "that's exactly the sort of
strange thing this should have caught," the gate is too tight.
Periodically send blind batches back to the calibration source (item
title+summary only, no hint which the model called YES/NO) rather than
asking it to confirm existing verdicts — anchoring the read defeats the
purpose. Re-run this whenever the CJ-1 prompt, model, RSS source mix,
or upstream filtering changes.

---

## 5. Persona evolution tied to real reception

**The problem:** `_fable_update_state` evolves each persona's `obsessions`/
`ongoing_arguments` based on the LLM's own self-assessment of what it just
wrote — never on how real readers responded.

**Proposed plan:**
- Depends entirely on #1 existing first. Once real per-persona engagement data
  accumulates, feed a signal into persona state evolution — e.g., "this
  obsession/angle correlated with real engagement, lean into it more."
- **Hard guardrail, non-negotiable:** never let performance-tuning erode a
  persona's core identity (the wound, the indefensible thing, the embodied
  specificity in `personas.py`/`persona_canon/*.md`) — only tune peripheral
  things like which themes a persona gravitates toward. Optimizing personas
  toward "whatever performs" is exactly how you get the generic-AI-voice
  problem back after building all this specificity to avoid it.

**Open questions for you:**
- This is the item I'd defer longest — it's speculative until #1 has weeks of
  real data. Flagging it now mainly so the eventual temptation to "just make
  Persona X more like whatever's performing" gets checked against the
  guardrail above, not because it's actionable soon.

---

## 6. Shadow-check promotion decisions (housekeeping, already scheduled)

Not new work — already tracked. Three shadow checks (`_check_bullet_points_shadow`,
`_check_forbidden_word_lists_shadow`, `_check_truncated_ending_shadow`) shipped
2026-08-09, observation-only, do-not-promote-before 2026-08-23. When that date
arrives, pull real `_reviews/*.md` sidecar data from trident's live runs (not
synthetic test cases) and decide promote/reject each individually, backed by
real false-positive counts. #2 above (persisting this to a DB) makes that
decision much easier than reading files by hand.

---

## What I'm explicitly NOT proposing

- Nothing here changes generation behavior immediately — items 1, 2, 4's first
  half, and 6 are pure data/observation work. Only 3, 4's second half, and 5
  actually change what gets written, and all three are gated on either your
  sign-off or real data existing first.
- No promotion of any shadow check before 2026-08-23, no exceptions, per the
  hard guardrail already established this session.
