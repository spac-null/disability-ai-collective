# Factual & Freshness Findings — Static Surface

Axes A (factual accuracy) and B (freshness) from the audit directive. Each finding
has: current text/claim, problem, evidence, proposed direction, classification.

## Overview

The core pages (`about.html`, `jascha.html`, `press/*`, `_collective/*.md`) were
all rewritten together on 2026-08-12/13/15 in a pass that already hedged nearly
every claim that would otherwise go stale — "does not promise a fixed publishing
rhythm," "the exact mechanics remain part of the project's private working
method," etc. This matches current canonical state (`.claude/WORK.md`,
`.claude/SOFA-METHOD.md`) closely. Most of the core surface is **KEEP**. The real
findings are narrower and concentrated in dates, one external platform's bio
copy, and one schema field.

---

### F-1. Accessibility statement "last updated" date predates a later audit

- **Current text**: `accessibility.html` — "Last updated: June 12, 2026. Standards: WCAG 2.1 AA."
- **Problem**: `.claude/design-scorecard.md` (repo-internal) records a site-wide
  WCAG/visual-polish audit that closed **2026-08-05** — nearly two months after
  the date this page claims as its last update. If that audit touched anything
  the accessibility statement describes (contrast, toggles, WCAG scope), the date
  is stale; if it touched nothing relevant to this page's claims, the date is
  accurate but coincidental.
- **Evidence**: REPO VERIFIED (`.claude/design-scorecard.md` closure date) vs.
  `accessibility.html` frontmatter/body (not independently re-diffed against the
  scorecard's specific changes in this pass — that cross-check is the open item).
- **Proposed direction**: Diff the design-scorecard's actual changes against
  `accessibility.html`'s claims; if the page's substantive claims (toggles, WCAG
  features list) were touched by that audit, bump the date to 2026-08-05 or the
  actual last substantive-content commit. If not touched, leave as-is — a stale
  date on an otherwise-accurate page is cosmetic, not a factual error.
- **Classification**: UPDATE_FRESHNESS. Priority **P3** (stale project fact, no
  false claim identified yet — becomes P2 if the diff check finds untouched
  substantive content).

---

### F-2. Tumblr bio text contradicts the site's own "authored system" positioning

- **Current text**: The live Tumblr blog (`tumblr.com/cripminds`, linked from the
  site footer) describes itself as "a disability-led AI arts journal managed by
  **four AI agents**."
- **Problem**: This directly contradicts the current, carefully-worded positioning
  on `about.html`, `press/index.html`, `press/how-it-works/index.html`, and
  `press/system-report/index.html` — all of which now explicitly state the
  personas are "fictional editorial personas, not autonomous disabled people,"
  authored and designed by Jascha Blume, with AI working "inside" that authored
  system. "Managed by four AI agents" reads as exactly the autonomous-persona
  framing those pages were rewritten to rule out.
- **Evidence**: WEB VERIFIED (live Tumblr fetch, 2026-08-20) vs. REPO VERIFIED
  (current `about.html`/`press/*` text, all `_collective/*.md` bios).
- **Proposed direction**: This is external platform bio copy, not a repo file —
  cannot be fixed by editing this repo. Requires the owner to update the Tumblr
  profile bio directly (outside this repo's control surface).
- **Classification**: UPDATE_POSITIONING, but **OWNER_DECISION** since the fix is
  off-repo. Priority **P2** (materially misleading positioning on a linked public
  surface, not just stale wording).

---

### F-3. JSON-LD `Organization.sameAs` lists only Bluesky, not Tumblr

- **Current text**: `_layouts/default.html` — `"sameAs": ["https://bsky.app/profile/cripminds.bsky.social"]`
  in the site-wide `Organization` schema block.
- **Problem**: The footer links both Bluesky and Tumblr as "Connect" channels, and
  Tumblr has been live and actively autoposting since before the current
  `_config.yml` version (3.2, "Resolution"). The structured-data `sameAs` field
  should list every owned profile for correct entity consolidation; it's missing
  a real, active one.
- **Evidence**: REPO VERIFIED (`_layouts/default.html` line ~97 vs. footer block
  lines ~248-253).
- **Proposed direction**: Add the Tumblr URL to the `sameAs` array. One-line
  template change, no content risk.
- **Classification**: UPDATE_FACT. Priority **P4** (cosmetic/SEO hygiene, zero
  reader-facing impact).

---

### F-4. `/notes/` is a real, sitemap-indexed page with a single article, unlinked from primary navigation

- **Current text**: n/a (structural, not a copy problem).
- **Problem**: `notes.html` (permalink `/notes/`) lists posts authored by "Jascha
  Blume" (the site's real, non-persona editorial voice). It IS in the live
  sitemap.xml and IS linked from `_layouts/post.html` (so readers arrive at it
  from an article footer), but it is absent from the main site nav and from the
  footer's "Explore" list — a visitor browsing from the homepage or footer alone
  has no path to it. Not a factual/freshness defect, but flagged here since it
  affects whether a real, live page is discoverable, which bears on "is the site
  telling one coherent story."
- **Evidence**: REPO VERIFIED (`grep` across all static HTML + layouts for
  `/notes/` — only `notes.html` itself and `_layouts/post.html` reference it;
  `_layouts/default.html`'s nav/footer do not).
- **Proposed direction**: Owner call — either add `/notes/` to the footer
  "Explore" list (if it's meant to be a real, ongoing editorial-voice channel) or
  leave as an intentionally low-key, article-footer-only surface.
- **Classification**: OWNER_DECISION. Priority **P4**.

---

### F-5. Gallery page has no `noindex` meta despite being `robots.txt`-disallowed

- **Current text**: `gallery.html` frontmatter: `sitemap: false` only — no
  `noindex: true`.
- **Problem**: `robots.txt` disallows `/gallery/` for all crawlers, but the page's
  own `<meta name="robots">` tag (set via `_layouts/default.html`'s
  `{% if page.noindex %}` logic) defaults to `index, follow` because `noindex` is
  never set on this page. `style-lab.html` and `realistic-scenes.html` both set
  `noindex: true` correctly; `gallery.html` is the one page with `sitemap: false`
  but not `noindex: true`. Low real-world impact (compliant crawlers already
  honor the `robots.txt` disallow and never request the page to see the meta tag)
  but the two signals disagree, and a non-compliant/aggregator crawler that
  ignores `robots.txt` would see "index, follow."
- **Evidence**: REPO VERIFIED (`gallery.html` frontmatter vs. `style-lab.html`/
  `realistic-scenes.html` frontmatter vs. `robots.txt`).
- **Proposed direction**: Add `noindex: true` to `gallery.html`'s frontmatter for
  consistency with the other two internal/experimental pages `robots.txt` names.
- **Classification**: UPDATE_FACT (metadata consistency). Priority **P4**.

---

## Non-findings worth recording (checked, confirmed accurate)

- Research pillar `hasPart` counts (9/5/5/4) match real post files exactly —
  see `STATIC-PAGE-INVENTORY.md` §C. No stale counts.
- "The source code for the site is public" (`press/index.html`) — REPO/WEB
  VERIFIED, `gh repo view --json visibility` confirms public (per prior session
  memory, re-affirmed by this repo's own public GitHub remote).
- No page anywhere in the static surface claims a fixed daily/specific publishing
  cadence — every instance found ("does not promise a fixed... rhythm") already
  matches the canonical "daily generation != daily publication,
  publication selector ≈ every two days" state from `.claude/WORK.md`.
- No page describes Article Form / Writer Grounding / the Sofa Method's staged
  architecture as deployed — all references to "the Mind Engine" are deliberately
  vague and explicitly marked "in development" / "private," consistent with
  `.claude/SOFA-METHOD.md`'s own scope banner ("Production has NOT migrated...").

---

# SUPPLEMENT (2026-08-20) — factual/freshness findings from the seven uncovered surfaces

## S-4 · `/research/` index claim — CORRECT, no finding

`llms.txt` says articles are "indexed at /research/". Verified: `research.html` renders
`<h1>Articles</h1>`, iterates `site.posts`, and serves at `/research/`. Accurate. Recorded so
the suspicion is not re-raised.

## S-5 · Feed representation integrity — 0 failures · KEEP

Swan Care standing rule applied to all five feeds. **All article-derived fields are generated
from canonical post data at build time** (`post.title`, `post.excerpt`/`post.content`,
`post.url`, `post.author`, `post.categories`); persona feeds select via
`where: "author", "<Persona>"`. A stale article representation is therefore structurally
impossible in a feed.

Useful contrast for the standing rule: the 2026-06-19 Swan Care article was retitled
2026-08-08 and its feed entry followed automatically, while the hand-maintained card in
`research/care-labor.html` went stale for twelve days. **Generated surfaces self-heal;
hand-maintained cards do not.**

## S-6 · `feed.xml` config drift — P3 · UPDATE_FACT

`_config.yml` configures `jekyll-feed` with `limit: 20` and its own `description`, but a
hand-written `feed.xml` at the same path is what ships, using `limit:10` and
`{{ site.description }}`. The `feed:` block's `limit`/`description`/`author`/`categories` are
inert. Two site descriptions exist in the repo; only one is served.
