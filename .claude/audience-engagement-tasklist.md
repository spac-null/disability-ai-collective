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

---

## Priority order (my read — argue with this)

1. Capture real engagement data (foundational — everything else needs this)
2. Persist engagement-read + shadow-check output to a queryable DB (cheap, unlocks analysis)
3. Judge-panel / multi-candidate generation (highest ceiling, highest cost)
4. Smarter topic/premise scoring at discovery time
5. Persona evolution tied to real reception (needs #1 first)
6. Shadow-check promotion decisions (already dated, 2026-08-23 — housekeeping, not new work)

---

## 1. No feedback loop from real reader behavior — DATA COLLECTION BUILT, 2026-08-09

**STATUS: `automation/engagement_fetch.py` built, tested end-to-end on trident
against real live data, working.** 354 real metric rows written on first run
(76 articles, last 90 days): GoatCounter pageviews/scroll-depth for 39
articles, GSC clicks/impressions/ctr/position for 45, Bluesky likes/reposts/
replies/quotes for 33, Mastodon favourites/reblogs for 1 (only one Mastodon
post exists so far). Tumblr returned nothing yet — expected, see the real bug
found and fixed below. All 5 sources needed zero new secrets beyond what
already existed on trident (see the credentials section below for exactly
why). Writes to `automation/engagement.db` (gitignored, stays on trident,
same as `disability_findings.db`).

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

---

## 2. Persist engagement-read + shadow-check output (cheap, do this early)

**The problem:** `_engagement_read`'s verdict and the 3 shadow checks currently
only get written to the `_reviews/<slug>-review.md` sidecar file — a human has
to open each file by hand to see a pattern. There's no way to ask "does Zen
Circuit systematically get worse engagement-read verdicts than Maya Flux" without
manually reading dozens of files.

**Proposed plan:**
- Add a DB table logging every `_engagement_read` verdict and shadow-check
  result per article (slug, persona, date, verdict text, shadow-check hit
  counts). Cheap — just structured logging of data already being computed,
  no new checks, no new LLM calls.
- This makes the shadow-checks' own 2026-08-23 promotion decision *evidence-
  based* instead of "go re-read a bunch of markdown files by hand."
- Also sets up the correlation work in #1 and #5 — once real engagement data
  exists, you can join it against this table.

**Open questions for you:**
- Worth building now (this week) since it's cheap and unlocks everything else,
  or bundle it with #1's DB work so there's only one schema to design once?

---

## 3. Judge-panel / multi-candidate generation

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

---

## 4. Smarter topic/premise scoring at discovery time

**The problem:** `discovery.py`'s topic selection is RSS feeds + keyword-bucket
matching (`THEME_KEYWORDS`) — a blunt instrument. All the craft investment
downstream (personas, rules, the engagement-read check) is applied to whatever
this blunt instrument picked. If the premise itself isn't interesting, no
amount of sentence-level polish saves it.

**Proposed plan:**
- Add an LLM-judged "angle interest" score at discovery time — similar
  mechanism to `_engagement_read` but running on the *candidate topic +
  proposed angle*, before generation, not on the finished article. Cheap
  (short prompt, short response) since it's judging a headline + summary, not
  a full article.
- Once #1's real engagement data exists, correlate which topic clusters/themes
  actually perform, and feed that back into `THEME_KEYWORDS`' weighting — but
  this is downstream of #1, not something to build first.
- Check whether the existing diversity-tracking machinery
  (`_get_recent_title_patterns`, `_get_recent_openings`, `_STRUCTURAL_SHAPES`)
  is actually being *acted on* anywhere or just tracked — I didn't verify this
  during the review and it's worth checking before building something new that
  duplicates it.

**Open questions for you:**
- Can you point to 2-3 past articles you felt had a genuinely great premise,
  and 2-3 you felt were mediocre? Concrete examples would let me calibrate
  what "interesting angle" should actually mean here, rather than me guessing.

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
