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

## 1. No feedback loop from real reader behavior

**The problem, confirmed by reading the code, not guessing:** `_store_social_uri`
only ever stores a Bluesky/Mastodon/Tumblr post URI so a *retraction* can delete
it later. Nothing anywhere reads back likes, reposts, replies, or click-through.
Register/length/article-type selection (`_REGISTERS`/`_LENGTHS`/`_ARTICLE_TYPES`
in `config.py`) are fixed weighted-random numbers, never adjusted by outcome.
The system publishes into a void.

**Proposed plan:**
- Build a small fetch job (own script or a `link_audit`-style method) that pulls
  current Bluesky like/repost/reply counts for posts from the last N days via
  the AT Protocol API (no auth needed for public post metrics, I believe —
  needs verifying).
- New DB table (`disability_findings.db` or a new dedicated one): article slug,
  persona, register, length, article_type, topic theme, post date, and a
  snapshot of engagement numbers at fetch time (metrics change over days, so
  probably want a few snapshots per article, not just one).
- Run on a schedule (daily cron, alongside `cripminds-daily.sh`).
- **Do NOT wire this into anything that changes generation behavior yet** —
  pure data collection first, same observation-before-action discipline as the
  shadow checks. Behavior changes come after enough data exists to trust a
  correlation, which is weeks away no matter what.

**Open questions for you:**
- Does cripminds.com have any page-view analytics (Google Analytics, Plausible,
  GitHub Pages' own insights, anything)? Bluesky engagement is one signal but
  people reading the actual article is the one that matters most, and I don't
  know if that's currently tracked anywhere at all.
- Bluesky is the channel with auto-posting already wired (`post_to_bluesky`) —
  is it also the channel you care most about, or do Mastodon/Tumblr numbers
  matter equally?
- Any privacy/ToS concern with polling Bluesky's public metrics on a schedule
  I should know about before building this?

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

I'd start with (a) — cheapest, lowest risk, tests whether "pick the better
opening" actually produces noticeably better pieces before spending more.

**Open questions for you:**
- What's an acceptable cost/latency increase? The pipeline currently runs once
  daily at 09:00 with no tight time budget I know of, but I don't know your
  actual API cost tolerance.
- Want to prototype (a) first and evaluate before committing to (b) or (c), or
  do you already have a strong intuition this needs the bigger swing?

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
