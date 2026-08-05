# Design-quality scorecard — visual polish, not WCAG

## HANDOFF (read this first if resuming in a fresh session/context)

This session ran the site through several iterations of: real browser screenshot →
axe-core WCAG scan (light+dark) → fix → re-verify. **Almost the entire site is now
checked and clean.** What's left is a small, well-defined tail — see "Remaining work"
below. Resume by either running `/loop` fresh (new context) or dispatching a
general-purpose subagent with that section as its task list; don't try to hold the
whole site's state in one long-running context again, that's what filled this one up.

**Standing method, reuse as-is:**
1. Navigate to the page, both themes, inject axe-core (`https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js`)
2. Run the scan **3 times with ~300ms waits between**, trust only the stable result — a single scan can be a false positive/negative while images are still loading (`document.images` not all `.complete`)
3. Any `color-contrast` violation: get exact foreground/background hex from `failureSummary`, compute the real fix in Python (relative luminance / contrast ratio, target ≥5.0 not just 4.5 for margin), don't guess
4. Fix locally, `bundle exec jekyll build --limit_posts 5` + `jekyll serve` on a free port, re-verify via axe-core before shipping
5. Commit with the real numbers in the message (before/after contrast, exact selector), push
6. Update this scorecard

**Remaining work (small tail):**
- [x] 404 page — checked, 2 real bugs found + fixed (see log below)
- [x] `/research/camouflaging/`, `/research/care-labor/`, `/research/extreme-male-brain/` — verified individually, all clean both themes, no new bugs (same template as already-clean pages, assumption held this time)
- [x] `/cripminds-stats-2026-06.html` — confirmed orphaned (only reference sitewide is this scorecard file itself), skipped per instruction
- [x] Two reported visual bugs (empty grid cell on `/research/`, avatar moire on homepage) — both confirmed real, both fixed, see log below
- [x] Homepage's 7 open design findings from the first Fable critique — all closed, see "Open design findings" section below (now marked closed) and commits `44f7bbc`, `92096ae`
- [x] `about.html` avatar moire follow-up — fixed, points at the same `*_thumb.png` files now (commit `2c00a73`)
- [x] Article template (`/2026/07/31/injected-since-birth/`) — first Fable critique done, 5 findings fixed, see "Batch A: non-homepage Fable critique pass" below
- [x] `/research/` — first Fable critique done, 4 findings fixed (2 shared with the article template), 1 confirmed false positive from the local `--limit_posts 5` dev build, 1 confirmed browser-automation screenshot artifact (not a site bug) — see below
- [x] `/research/deaf-arts/` — **2026-08-05 follow-up: real Fable critique obtained** (OpenRouter direct, CLIProxyAPI abandoned). 3 findings, all shared-component (affects 4 other already-clean pages) — deliberately left, see "Batch A" section 3 below for full reasoning. No fixes needed.
- [x] `/about/` — **2026-08-05 follow-up: real Fable critique obtained** (light theme). 1 real page-specific bug found + fixed + verified both themes (`#start-here` section blending into the section above it), 2 shared-component findings deliberately left. See "Batch A" section 4 below. Commit `94ec300`.
- [~] `/press/` — **2026-08-05 follow-up: attempted, no critique obtained.** OpenRouter direct works in general (confirmed via successful calls on the other 2 pages this same session) but the vision route hit a hard, non-recovering block specific to image-bearing requests partway through the batch — not the same failure mode as the earlier CLIProxyAPI outage, see "Batch A" section 5 below for full diagnostic evidence (it's not image-size-sensitive, not simple credit exhaustion, didn't clear after a 4-min wait). Manually re-checked established bug patterns, none found, no fixes applied. Still needs an actual Fable critique — retry with either much more patience or a different vision model.
- **Batch A (5 pages) is now fully closed except `/press/`'s critique.** All 5 pages have
  been screenshotted and code-checked; 4 of 5 (article template, research.html,
  deaf-arts, about) have a real Fable critique on record with fixes applied where
  warranted. `/press/` alone is missing the actual critique — screenshots are
  captured in the session scratchpad
  (`/private/tmp/claude-501/.../scratchpad/screenshots/`, ephemeral — re-shoot if
  gone) so a follow-up just needs the API call once the OpenRouter vision route
  recovers.
- [~] **Batch B (5 pages: `/press/how-it-works/`, `/press/system-report/`, `/jascha/`,
  `/notes/`, `/accessibility/`) — attempted 2026-08-05, no Fable critique obtained.**
  OpenRouter's image-bearing route is still in the exact same non-recovering blocked
  state documented for `/press/` in Batch A section 5 — see "Batch B" section below for
  full diagnostic evidence (this session's own independent re-diagnosis, not just a
  repeat of the old finding). Screenshots for all 5 pages (light+dark, full page
  top-to-bottom) are captured and saved in the session scratchpad
  (`/private/tmp/claude-501/.../scratchpad/screenshots/`, ephemeral — re-shoot if gone)
  so a future retry just needs the API call once OpenRouter's vision route recovers.
  Manual code-pattern check (no Fable available) found no established-anti-pattern bugs
  on any of the 5 pages — see below for detail. No fixes applied, nothing needed fixing.
- [ ] Remaining pages (batch C — editorial-lens, collective pages, gallery) still need their first Fable design critique

**Note on this batch's process**: the subagent originally dispatched for the 7
homepage findings did the actual design work correctly (verified by reading its
uncommitted diff) but was killed mid-task by hitting the account's monthly Claude
spend limit before it could verify/commit. The orchestrating session finished the
verification (local build, screenshot both themes, axe-core 2x/theme, 0
violations) and committed it directly instead of re-dispatching. Also found+fixed
one new bug while re-verifying: `.agent-grid--2col` had a large dead gap between
the two cards (`repeat(2, 1fr)` stretching tracks to ~half the container width
while `.agent-card` capped at max-width:280px sat left-aligned in the oversized
cell) — predated this session, live on production, commit `92096ae`. **If
resuming with subagents again, budget/spend limits are a real constraint now —
check before dispatching another heavy (screenshot+axe+Fable-API) batch.**

**Pages verified clean this session (contrast only, not design-critiqued except homepage):**
`/`, article template, `/research/`, `/research/deaf-arts/`, `/research/camouflaging/`,
`/research/care-labor/`, `/research/extreme-male-brain/`, `/about/`, `/press/`,
`/press/how-it-works/`, `/press/system-report/`, `/jascha/`, `/notes/`,
`/accessibility/`, `/editorial-lens/`, all 4 `/collective/*/` pages, `/gallery/`, `404.html`

**`cripminds-stats-2026-06.html`**: confirmed orphaned (not linked from any live page,
`grep -rl` across the repo only turns up this scorecard) — skipped, not checked.

---

Reframed 2026-08-04: original ask sounded like WCAG "AAA" (accessibility conformance
level) but actually meant design/visual quality — typography, layout, polish,
"does this look like a top-tier studio built it." WCAG AA remains a hard floor
(explicitly confirmed) but is no longer the loop's main subject — see below for
that thread, which ended up being most of this session's actual output.

Design-critique method (only run on homepage so far): real browser screenshot
(light + dark, desktop) → Fable 5 design critique (typography, hierarchy,
spacing/rhythm, color cohesion, image quality, whitespace, "does this read as
intentional or default") → concrete fix → re-screenshot to confirm.

## Legend
- ⬜ not yet reviewed
- 🔍 reviewed, issues found, not yet fixed
- 🟨 partially addressed
- ✅ reviewed and fixed to a genuinely polished standard (contrast) — design critique still pending unless noted

## Homepage design findings — CLOSED (commits `44f7bbc`, `92096ae`)

From the first Fable critique run this session, all 7 now fixed and verified
(local build, screenshot both themes, axe-core 0 violations):
- Hero H1 → `--font-family-serif` (was generic default sans), matches article
  title typography
- Light mode now gets its own treatment: `.home-hero__card` gets a 3px accent
  top border in light mode, reverts to the original 1px neutral border in dark
  (where the near-black artwork already blends naturally)
- Meta separators standardized to middot sitewide on the homepage (was pipe in
  grid cards, middot in hero — now consistently middot)
- Essay-grid avatar dot rendering — was already fixed in the prior batch
  (moire/aliasing → proper thumbnails), re-verified clean, no further change
- WCAG 2.1 AA footer badge now a real pill (border, background, checkmark),
  not bare text
- Persona accent border colors on dark now use the already-vetted lightened
  text-contrast variants instead of raw brand hues — more presence, still
  clears the 3:1 UI-component floor (border/background fill unchanged)
- Hero's dead right-column space filled with a real pull-quote (Jascha's own
  personal statement)

Also found + fixed while re-verifying (not from the original critique):
`.agent-grid--2col` dead gap between cards, see note above (commit `92096ae`).

## Batch A: non-homepage Fable critique pass (5 pages)

Method: real browser screenshot, full scroll (5 shots top-to-bottom), light +
dark, desktop 1440px → one Fable 5 critique call per page (all screenshots in
one message) → concrete CSS/HTML fixes → re-screenshot → axe-core 3x/theme on
any color-touching fix. Endpoint: CLIProxyAPI on trident, `openrouter/claude-fable-5`,
`max_tokens` needs ~6000+ for this model (3000 truncated mid-response with
`finish_reason` still reported as if complete in one run — retried higher, got
a full `stop`-terminated 7.5k-char response; worth remembering for the
remaining 4 pages in this batch).

### 1. Article template (`/2026/07/31/injected-since-birth/`) — DONE

Fable's punch list (9 items, full text not reproduced here) covered: an
orphaned-looking content column, the sans-serif lede paragraph + drop-cap
treatment, accent-color sprawl, a perceived dead zone before the footer,
newsletter module inconsistencies between themes, the floating
Dyslexia/theme-toggle pills, prev/next card padding, missing typographic
furniture (subheads/pull-quotes), and small dark-mode fit-and-finish issues
(byline avatar, author card).

**Fixed (5 findings, real bugs confirmed by code inspection + measurement,
not just taking Fable's read at face value):**
1. **Byline avatar (`.post-meta__agent-icon`) and author-card avatar
   (`.post-author-avatar`) — persona portrait nearly invisible in dark mode.**
   Verified by pixel-cropping both theme screenshots: light mode shows a
   clear filled circle, dark mode shows almost nothing but a faint ring.
   Root cause confirmed via direct pixel read of the source PNG
   (`zen_circuit_style_matched.png`): its own background color is `rgb(26,16,22)`,
   nearly identical to the dark theme's page background (`#2b2b2f`), so the
   portrait optically merges with the page at small size. Fixed two ways:
   swapped `author_icon` (all 4 personas, `_layouts/post.html`) from the raw
   1024px source to the already-existing `*_thumb.png` files (same fix
   pattern as commit `23a5445` — that commit fixed the homepage grid but
   explicitly left this article-template usage as a noted follow-up), and
   strengthened both avatars' border from `--color-border-secondary` to the
   stronger `--color-border-primary` (`.post-meta__agent-icon` also bumped
   1px→1.5px) so the boundary reads even when the portrait's own fill is
   close to the surrounding background. Verified both themes post-fix —
   avatar now clearly legible in dark mode.
2. **Two different "Subscribe" buttons on the same page, two different
   colors.** The in-article `.post-subscribe__row button` used
   `var(--color-text-primary)`/`var(--color-background-primary)` (black
   button, white text in light mode) while the footer's
   `.subscribe-section__btn` (same CTA, same page) already correctly used
   `var(--color-accent)`/`var(--color-on-accent)` (teal). Switched the
   in-article button to match the footer's token pairing — same fix
   philosophy as the sitewide `--color-on-accent`/`--color-on-brand` work
   from the earlier session.
3. **In-article newsletter email input unreadable in light mode.**
   `.post-subscribe__row input[type="email"]` used hardcoded
   `rgba(255,255,255,0.06)` background / `rgba(255,255,255,0.15)` border —
   a white-based translucent overlay that only reads against a dark card
   surface. Against the light-mode card it was nearly invisible (matches
   Fable's "underline-only in light mode" observation). Replaced with
   theme-aware tokens: `var(--color-background-primary)` /
   `var(--color-border-primary)`, focus ring `var(--color-focus)` (was also
   hardcoded `rgba(255,255,255,0.35)`).
4. **Halftone dot texture only visible in dark mode.**
   `.post-subscribe::after` (decorative screenprint-style dot cluster,
   top-right of the newsletter card) used hardcoded
   `rgba(255,255,255,0.1)` dots — invisible against the light-mode card,
   confirmed by Fable and by inspection. Changed to
   `var(--color-text-primary)` (flips near-black/near-white per theme) at
   low opacity (0.07 light / 0.1 dark via a `.dark-theme` override so dark
   mode's existing look is preserved exactly), so the texture now shows in
   both themes instead of only dark.
5. Verified fixes with axe-core (`wcag2a`+`wcag2aa`), 3 runs each theme after
   a scroll-forced reflow — **0 violations, both themes**, before and after.

**Deliberately left (checked, judged not to need a fix, reasoning below):**
- **"Orphaned" content column (Fable's #1, called the biggest issue).**
  Measured via `getBoundingClientRect()` at 1440px: the actual gap is
  `.post-shell` right edge 1170px vs `.prose` right edge 1041px — **129px**,
  not the "350px empty third" Fable eyeballed from a static screenshot. It
  exists because `.prose` (68ch measure, ~755px) is narrower than
  `.post-shell`'s content box (~868px) and isn't centered within it, so the
  unused width sits entirely on the right. A real, measured asymmetry — but
  fixing it means picking a real information-architecture direction
  (centering the prose column would indent body text ~56px relative to the
  flush-left H1/breadcrumb/meta bar above it, which is its own new
  inconsistency; widening the prose measure would fight Fable's own
  agreement that "the measure itself is correct"). This needs a considered
  column-width decision for the whole article template, not a one-line CSS
  patch — flagged for a follow-up design pass rather than guessed at here.
- **Sans-serif lede paragraph + drop cap on "I" (Fable's #2).** Confirmed
  via CSS (`.prose > p:first-of-type`) this is an intentional dek/standfirst
  treatment (larger sans-serif lead-in, explicit code comment), a legitimate
  and common editorial pattern (De Correspondent, The Verge do the same).
  Fable's specific complaint — the drop cap on a capital "I" reads as a thin
  black bar/cursor — is real but is a narrow-letter drop-cap problem
  inherent to any `::first-letter` implementation; a targeted fix would need
  per-article Liquid/JS logic to detect the actual first character, which is
  disproportionate for a cosmetic ding on one letter. Left as a known,
  accepted limitation.
- **"Large dead gap before the footer" (Fable's #4).** Measured via
  `getBoundingClientRect()`: `article.section` bottom to `#footer` top is
  64px (the section's own `padding-bottom`) — normal spacing, not a bug.
  What reads as a big gap in the screenshot is the visual effect of a
  centered pill button with padding around it at that scroll position, not
  an actual oversized gap.
- **Prev/next card "image bleed" and "asymmetric padding" (Fable's #7).**
  Checked `.post-nav__link` / `.post-nav__link--next` CSS: both cards share
  the same `gap`/`padding` rules, only `flex-direction: row-reverse` differs
  (a deliberate mirrored older/newer layout), and the thumbnail sits in an
  `overflow: hidden` box so there's no actual clipping/bleed bug. Read as a
  stylistic mirrored-card choice, not an asymmetry bug.
- **Missing typographic furniture — subheads/pull-quotes on this specific
  essay (Fable's #8).** The site already has CSS for `.prose h2` and
  `.prose blockquote` (pull-quote styling exists, confirmed in CSS); this
  particular short essay just doesn't use them. Content-level choice per
  article, not a template bug — not touched.
- **Floating Dyslexia/theme-toggle pills styled like a browser extension
  (Fable's #6).** Real aesthetic point but this is a sitewide fixed-position
  component (`accessibility.js`), not article-template-specific — restyling
  it site-wide is out of scope for a single-page fix in this batch; noted
  for a future dedicated pass on that component.
- **Newsletter headline weight / hierarchy (part of Fable's #5).** Font
  weight is `--font-weight-light` on a 2xl headline next to a small
  uppercase eyebrow — a legitimate, if arguable, editorial weight contrast.
  Judgment call to leave as-is; the objectively broken parts of the same
  finding (input contrast, button color, dot texture) were fixed.

Commit: `f36240d`

### 2. `/research/` (articles index) — DONE

Fable's punch list (10 items) covered: blank-looking cards above the fold,
an apparent essay-count contradiction, sticky filter bar clipping content,
the Reading Threads module's alignment/dead-space, duplicate newsletter
modules, an invisible light-mode radio button, a stray background band,
mismatched image art direction across cards, dark mode "flattening" the
persona system, and pipe-separator meta lines.

**Fixed (4 findings — 2 of these are the same root-cause bug already fixed
on the article template, found independently here; 2 are new):**
1. **Pipe separators (`|`) in `.article-card__meta`** — same "default-
   WordPress tell" the earlier homepage pass already fixed for the
   homepage's own cards but never propagated here. `research.html`
   hardcoded `<span class="article-card__sep">|</span>` twice per card.
   Swapped both to `&middot;`, matching the sitewide standard.
2. **`.article-card__author-icon` (20px avatar per card) — same near-
   invisible-in-dark-mode bug as the article template's byline avatar**,
   same root cause (raw 1024px source image's own near-black background
   almost matches the dark theme page background). Added a new
   `research_author_icon_thumb` Liquid variable (kept the existing
   `research_author_icon` — raw source — untouched, since it also feeds
   the large `card__media` fallback image and swapping that to a 192px
   thumb would have degraded quality for any future post without a custom
   `page.image`) and pointed only the small avatar `<img>` at the thumb.
   Border strengthened `--color-border-secondary` → `--color-border-primary`,
   1px → 1.5px, matching the article-template fix.
3. **`.filter-persona-icon` (16px persona-filter chip avatars) — same bug,
   worse at this size.** A prior session's commit (`23a5445`) explicitly
   checked this element and found "no visible artifact at that size" — but
   that check was against the *default/light* state; the default (non-
   hover, non-active) state has no border at all (`opacity: 0.75`, no
   invert filter — the invert only applies on `:hover`/`.active`), so in
   dark mode the Zen Circuit chip's icon nearly disappeared into the dark
   filter-bar background. Swapped all 4 filter-button `src`s to the
   `_thumb.png` variants and added `border: 1px solid var(--color-border-primary)`
   so there's a visible boundary in the un-hovered state regardless of the
   portrait's own fill color. Verified both themes.
4. **`.subscribe-section__freq input[type="radio"]` (frequency toggle in
   the shared newsletter include, `_includes/subscribe-form.html`) —
   hardcoded `rgba(255,255,255,0.3)` border, matching Fable's "'Each
   article' shows no visible control at all" in light mode.** Same
   white-overlay-on-dynamic-background anti-pattern already fixed twice on
   the article template. Swapped to `var(--color-border-primary)`. Because
   this is the *shared* subscribe-form include, the fix is live everywhere
   that include is used (research.html's "Keep reading" module + the
   sitewide footer) — one CSS fix, sitewide reach, not just this page.
5. Verified with axe-core (`wcag2a`+`wcag2aa`), 3 runs/theme after a
   scroll-forced reflow — **0 violations, both themes**.

**Confirmed false positives / non-bugs (checked, not fixed):**
- **"5 essays" hero count contradicts the Reading Threads' 5/9/5/4 counts"
  (Fable's #2).** The hero count is `{{ site.posts.size }} essays` —
  dynamic, and this session's local build uses `--limit_posts 5` for speed,
  so it coincidentally prints "5" and looks like it's being contradicted by
  a "9 essays" thread. The thread counts are hardcoded curated numbers
  reflecting the real ~137-post archive; in production `site.posts.size`
  would show the true total, and there'd be no apparent contradiction.
  Confirmed by reading the Liquid source — not a real bug, an artifact of
  this session's local dev build.
- **"First row of cards renders as empty boxes" (Fable's #1) — confirmed a
  browser-automation screenshot artifact, not a real site bug, via two
  independent checks.** First: `document.querySelectorAll('.card__media')`
  showed every image `complete: true` with valid `naturalWidth` at the
  exact moment a screenshot still rendered them blank — ruling out an
  actual network/lazy-load failure. Second: forcing a reflow (scroll away
  and back, the same workaround already documented in this scorecard's
  "stale-paint" lesson from the theme-toggle work) made the images render
  correctly on the next screenshot with no other change. This matches the
  known extension-bridge timing bug already logged in "Site-wide findings"
  below, now confirmed to also affect plain image paint, not just
  post-theme-toggle color reads. Not fixed (nothing to fix — it's a gap
  between the automation tool's screenshot and the compositor, not
  something a real visitor's browser would exhibit).
- **Sticky filter bar "decapitating" card titles mid-scroll (Fable's #3).**
  This is the ordinary, universal visual effect of any sticky bar sitting
  above scrolling content at an arbitrary scroll position — not a scroll-
  margin or fade/shadow issue. No fix applied.
- **Reading Threads baseline misalignment + full-width 4th cell "dead
  space" (Fable's #4).** The baseline shift is just an unequal-height
  consequence of one thread's title wrapping to 2 lines vs. 1 — normal
  card-grid behavior, not a bug. The full-width 4th cell
  (`.research-thread--full`) is a *previous* session's deliberate, already-
  verified fix for a worse bug (an empty void in that grid cell, see
  "Visual bugs found + fixed" #1 above) — re-litigating it isn't warranted
  by one critique pass disliking the tradeoff; Fable's alternative (give
  threads real visual weight/imagery) is a legitimate but bigger content-
  level enhancement, out of scope here.
- **Duplicate newsletter modules — mid-page "Keep reading" + footer
  Subscribe (Fable's #5).** Two subscribe CTAs at different scroll depths
  on a long page is a common, deliberate editorial pattern (captures
  readers who bail at different points), not a template bug. Left as-is.
- **Stray background band before the footer (Fable's #7).** This is the
  site's existing `section--primary`/`section--secondary` alternating-band
  pattern, used the same way on every other page (including the already-
  reviewed homepage) — consistent with established sitewide language, not
  a research.html-specific defect.
- **Mixed image art direction — constructivist posters next to a vintage
  anatomical engraving and a technical blueprint (Fable's #8).** Real
  observation, but it's about *which* images specific past articles used
  (an editorial/content decision), not something a template CSS pass can
  fix — noted, not actioned.

Commit: `209067d`

### 3. `/research/deaf-arts/` (research-thread subpage) — Fable critique obtained, no fixes applied

**2026-08-05 follow-up session**: switched from the now-abandoned CLIProxyAPI
to OpenRouter direct (`https://openrouter.ai/api/v1/chat/completions`,
`anthropic/claude-fable-5`, key pulled fresh from
`/srv/secrets/openclaw.env` on trident). Confirmed working — got a real
critique for this page, both themes (2 separate single-image calls; see
"OpenRouter vision-budget finding" below for why single-image-per-call was
necessary).

Fable's findings (light theme, cut off by a token-budget constraint before
finishing, see below):
1. **The 9-card teaser grid is a "wall of sameness"** — identical size,
   border, and gray fill on every card, with the "CULTURE" eyebrow label as
   the only differentiator, so no story reads as more important than
   another; reads as a default template, not an editorial decision.
2. **Type scale jumps too abruptly** — huge confident H1, then everything
   below (intro, essay paragraph, card body) collapses to nearly one small
   size; missing an intermediate tier for rhythm between hero and dense
   content.
3. (cut off mid-sentence on "Vertical sp..." — insufficient text to act on,
   not counted as a finding)

Dark theme add-on: **the teal accent is doing almost nothing** — appears
only in the tiny card category labels, the "All articles →" link, and the
footer Subscribe button, so the mint CTA color has very little presence on
this page.

**Checked, judged not to need a page-specific fix (all three real findings
above)**: every element named — `.related-articles__grid`,
`.related-articles__card`, `.related-articles__cat`, `.related-articles__title`
— is a **shared component**, confirmed via grep: also live on
`research/care-labor.html`, `research/camouflaging.html`,
`research/extreme-male-brain.html`, `_layouts/post.html` (article template),
and `_layouts/debate.html`. All of those are already marked clean/verified
elsewhere in this scorecard. A page-specific override here would either (a)
diverge this page's teaser-card treatment from 4 sibling pages that use the
identical component, or (b) require a shared-CSS change that's out of scope
for a single-page fix in a batch explicitly scoped to 3 pages only. Same
judgment call already made and documented for comparable shared-component
findings on the article template and research.html batch (see above) — this
is a real finding, flagged for a future dedicated pass on `.related-articles`
site-wide, not fixed here.

No code changes made to deaf-arts.html this session.

Commit (2026-08-04, prior attempt): `4fa4e61`. This session's findings are
docs-only, folded into the batch-close commit below.

### 4. `/about/` — Fable critique obtained (partial), 1 fix applied

**2026-08-05 follow-up session.** Got a real critique for the light theme —
one call's `max_tokens` was exhausted by the model's internal reasoning
before it emitted final-answer text, but the reasoning trace itself
contained a complete, coherent 3-point critique (verified this is genuine
critique content, not a hallucination — every point named a specific real
element, checked against the page). Could not get a second call through for
the dark theme before the vision route stopped accepting any image request
for the rest of the session (see finding below).

Fable's findings (light theme):
1. **Narrow text measure creates uncomfortably long gray columns.** Real,
   but `.prose { max-width: 68ch }` is the same shared class already
   deliberately kept on the article template in the prior Fable batch
   ("the measure itself is correct" — Fable's own words there). Applying
   the opposite judgment here for the identical CSS property would be
   inconsistent. Left as-is, same reasoning as the article-template
   precedent.
2. **"Three places to start" has no visual separation from the "About This
   Project" section above it — they blur together.** Confirmed via code:
   `#about-project` and `#start-here` both used `section section--secondary`
   back-to-back, and the page header above them is *also* secondary — three
   consecutive same-background sections. **Fixed**: `#start-here` switched
   to `section--primary` (verified unique to about.html via grep, no other
   page affected). Re-screenshotted both themes — clear visual break now in
   both. Checked the new adjacency this creates (`#start-here` primary
   directly before `#agents`, which was already primary) — not a repeat of
   the same bug, because the content type changes (prose list → bordered
   card grid) and cards carry their own visual boundary regardless of
   section background; confirmed by inspection, no dead blur. axe-core
   (`wcag2a`+`wcag2aa`, 2 runs/theme after scroll-forced reflow): **0
   violations, both themes**, before and after (background-only swap
   between two already-vetted theme tokens, no new colors introduced).
3. **The four voice cards rely entirely on their colored tag pills (purple/
   green/blue/orange) as the only saturated accent in an otherwise muted
   palette, feeling disconnected from the rest of the design system.** Real
   observation, but `.agent-identity` per-persona coloring is a shared
   component that was already deliberately tuned for contrast + "presence"
   in the homepage's 7-finding design pass this same scorecard (see
   "Homepage design findings — CLOSED" above). Retuning it again based on
   one page's critique risks re-litigating a decision already made
   holistically across every page that uses it (homepage, about, and any
   future collective pages). Left as-is.

No code changes made beyond the `#start-here` fix.

Commit (2026-08-04, prior attempt): `cb021ce`. This session's fix:
`94ec300`.

### 5. `/press/` — no Fable critique obtained; OpenRouter vision route hit a hard, non-recovering block

**2026-08-05 follow-up session.** OpenRouter direct (not CLIProxyAPI) is
confirmed working in general — plain text-only calls to `anthropic/claude-fable-5`
succeeded throughout this session, and 3 image-bearing calls succeeded
earlier in the batch (deaf-arts ×2, about-light ×1). But by the time this
page's turn came up, **every image-bearing request started failing with
`402 Prompt tokens limit exceeded: 1604 > <shrinking ceiling>`**, regardless
of image content. This is a materially different, more specific failure
than the prior session's CLIProxyAPI outage, worth documenting precisely
for the next person who hits it:

- The account's actual dollar balance was healthy throughout (`$12.42` of a
  `$20` monthly cap on this key, confirmed via `/v1/key` — not remotely
  exhausted).
- The rejection is **not sensitive to image size** — tested progressively
  smaller resizes (1440px → 800px → 450px → 260px width) and even a direct
  crop to the *exact* 450×718px dimensions of the deaf-arts image that had
  already succeeded earlier — every single one reported the identical
  `1604` prompt-token figure, including a 100×50px near-blank crop. Once
  the block set in, no amount of image downscaling helped.
- Waited it out with a 20s pause and then a dedicated 4-minute polling
  monitor (12 retries at 20s intervals) — the ceiling never moved
  (`1604 > 1088` → `1604 > 1088`, unchanged across the entire wait).
- Text-only calls to the same model kept working the whole time at normal
  cost (~$0.0003/call), ruling out a full key lockout.
- Best working theory: this specific model (`claude-fable-5` via Amazon
  Bedrock, per the `provider` field in successful responses) is unusually
  expensive per completion token (~$0.05/token, ~50-100x typical Claude
  pricing observed from real `usage.cost` data) and OpenRouter's pre-flight
  cost estimator reserves a large, apparently non-decreasing worst-case
  budget per image once it has observed a few real (expensive) completions
  in the session — i.e. a one-way ratchet, not a simple balance countdown.
  If true, waiting longer (this session tested ~15 min total) likely
  wouldn't have helped; a full quota reset (billing-cycle-linked, or a
  cooldown measured in hours) would be needed. Unconfirmed — OpenRouter
  doesn't expose the estimator's internals — but the evidence (flat
  rejection number independent of actual request content, healthy real
  balance, text calls unaffected) rules out plain credit exhaustion.
- **For a future retry**: don't bother re-resizing images if this error
  reappears — it doesn't help. Check `/v1/key` balance first to confirm
  it's not simple exhaustion, then either wait substantially longer than
  15 minutes or use a different/cheaper vision-capable OpenRouter model for
  the critique pass.

Manually re-checked the same established bug patterns already confirmed
absent on this page in the prior session (no pipe separators, no hardcoded
`rgba(255,255,255,...)`, no `<img>` tags at all — still a pure-text
template) — nothing new found. Did not re-litigate the previously-measured
"gap before the footer" (confirmed deliberate `padding-bottom: 100px` in
the page's own markup, not a bug — see prior session's note, still holds).

No code changes made to press/index.html this session.

Commit (2026-08-04, prior attempt): `1e97585`. This session: docs-only, see
batch-close commit below.

## Batch B: non-homepage Fable critique pass (5 pages) — 2026-08-05, no critique obtained

Method: same as Batch A — real browser screenshot (Chrome extension bridge), full
scroll top-to-bottom (2-5 shots per theme depending on page length), light + dark,
desktop 1440px viewport (actual capture ~1372x870 due to display constraints —
window resize beyond ~1900px height silently clips to visible screen bounds on this
Mac, confirmed by testing; scrolling shots substitute for a taller single capture).
Pages and shot counts: `/press/how-it-works/` (9321px tall, 5 shots/theme),
`/press/system-report/` (5954px, 5 shots/theme), `/jascha/` (2590px, 3 shots/theme),
`/notes/` (1303px, 2 shots/theme), `/accessibility/` (2703px, 4 shots/theme).

**OpenRouter's image-bearing vision route is still blocked, same failure signature
as `/press/` in Batch A section 5, confirmed independently this session:**

- First call (10 images: 5 light + 5 dark for `/press/how-it-works/`) → `402`,
  `"can only afford 217"` tokens against a requested 7000.
- Reducing to 1 image, `max_tokens` 2500 → same `402`, same `"can only afford 217"`.
- Reducing `max_tokens` to 150 → different but equally telling message: `"Prompt
  tokens limit exceeded: 1605 > 1075"` — near-identical to the `1604 > 1088` figure
  logged for `/press/` in the prior session, confirming this is the same underlying
  block, not a new/different issue.
- `/v1/key` balance check: `$12.42` of `$20` monthly cap, unchanged before and after
  every failed call — not real credit exhaustion.
- Ran a fresh, independent 4.5-minute active poll (9 attempts at 30s intervals,
  single-image request each time) — the block **never cleared**, every attempt
  failed with the same `1605 > 1075` signature.
- Cross-checked with a different page's image (`/accessibility/` light-theme shot,
  different content/size than the `/press/` image used in all other tests) — **same
  exact `1605 > 1075` error**, confirming the block is account/key-level, not tied
  to any specific page's image content or size (consistent with Batch A's finding
  that resizing down to 100×50px didn't help either).
- Text-only calls to the same model continued to work throughout (confirmed once,
  not re-tested exhaustively since Batch A already established this thoroughly).

**Conclusion: this is the same one-way-ratchet condition documented in Batch A
section 5, and it has not cleared across a session boundary (this is a different
session from the one that first hit it).** Given the account-level (not per-page)
nature confirmed above, further per-page retries within this batch would just
reproduce the identical result — not attempted for all 5 pages individually, one
thorough cross-page diagnostic was judged sufficient. Screenshots for all 5 pages
are saved in the scratchpad, ready for a future retry without re-shooting.

**Manual code-pattern check (in place of a critique, using established anti-pattern
list from prior batches) — no fixes needed on any of the 5 pages:**
- No `<img>` tags at all on any of the 5 pages (all pure-text/prose templates, same
  as `/press/` in Batch A) — rules out the avatar-moire and thumb-vs-raw-source
  pattern entirely.
- No pipe (`|`) separators (grepped `article-card__sep` and literal `|` — none).
- No hardcoded `rgba(255,255,255,...)` white-overlay anti-pattern (grepped, none).
- No `opacity: 0.6-0.75` stacked on already-muted text (grepped, none).
- One instance of a raw hex fallback: `press/system-report/index.html` (1 occurrence)
  and `press/how-it-works/index.html` (3 occurrences) both use inline
  `style="border-left: 3px solid var(--color-border-brand, #3f5f89); ..."` on
  blockquotes. Checked whether this is live: `--color-border-brand` **is** properly
  defined for both themes (`main-redesign.css` lines 98 and 152) so the `#3f5f89`
  fallback is dead code, never actually rendered — confirmed by inspecting the
  screenshots (`/press/system-report/` dark-theme blockquote border reads as the
  theme's actual brand-border color, not a static hex). Not a visual bug. The inline
  `style=` attribute itself (vs. a shared `.prose blockquote` class) is a minor code
  cleanliness point, not a design/contrast issue — not touched, out of scope for a
  critique-driven pass with no critique to act on.
- `/accessibility/`'s "What to include in your report" card, which renders visually
  empty in every screenshot — confirmed via source (`accessibility.html` line 85-86,
  a native `<details>`/`<summary>` element) to be a collapsed accordion, not a bug.

No code changes made to any of the 5 Batch B pages this session (nothing to fix —
the manual check found no established-pattern bugs, and no Fable critique was
obtainable to surface anything beyond that). Commit: docs-only, this scorecard
update.

## Contrast bugs found + fixed this session (chronological, all verified via axe-core)

1. `.agent-identity` persona badges, dark mode — raw brand hex as text, Maya Flux
   1.65:1. Fixed with lightened dark-theme variants. (commit efbf0aa)
2. `.agent-grid` flex→grid — unequal Collective-card heights (496-554px measured),
   and silently broke the existing `.agent-grid--2col` modifier (was rendering
   4-across instead of 2x2). Duplicate homepage subscribe form removed. (commit cb68c53)
3. **`--color-accent` was undefined sitewide** — all 9 usages fell back to a
   hardcoded `#7c6af7` (literally Pixel Nova's color, not a real brand choice).
   Defined properly: teal, light `#0e7568` / dark `#3fc9b8`, real contrast math,
   Fable-recommended (sits in the open hue gap between the four persona hues).
   Found + fixed a follow-on bug from that same change: white button text
   unreadable on the new lighter dark-mode teal (2.05:1) — added
   `--color-on-accent` token (white light-mode / near-black dark-mode).
   `.post-category-label` had the same raw-hex-as-text bug as #1. author.html
   byline had opacity:0.6 stacked on already-muted text. (commit 9a60079)
4. **Sitewide systemic bug**: "already-muted color + opacity:0.6-0.75" stacking —
   verified via real math to fail AA in 11 of 13 instances checked codebase-wide
   (the muted/secondary tokens are already correctly de-emphasized on their own,
   7:1+; the opacity was pure redundant harm). Fixed 6 instances: `.site-tagline`
   (every page), `.post-breadcrumb__link`, `.post-author-eyebrow`,
   `.research-threads__eyebrow`, `.post-meta__register`, `.post-meta__item`
   separator, `.link--subtle`. Plus a 4th raw-persona-hex instance: the
   "More by {persona}" button, was inline-styled, moved to data-persona+CSS.
   (commit 647629b)
5. Two more opacity-bug instances found on `/research/` ("137 essays") and
   `/` ("The Collective" eyebrow). (commit c50f967)
6. **Light mode had never been checked** for the persona-color-as-text fixes —
   only dark mode was verified when each was first fixed. Turned out 3 of 4
   personas fail in light mode too (`.agent-identity`, `.post-category-label`,
   `.persona-more-btn`): Pixel Nova 3.54-3.58:1, Siri Sage 4.33:1, Zen Circuit
   4.24:1. Maya Flux already passes at full brand color, left alone. Computed
   darkened light-mode variants (HSL lightness walked down to 5:1+) for all
   three. (commit c50f967 same commit as #5)
7. `/gallery/` filter buttons — `opacity:0.5` on the whole button (meant to dim
   an icon for the inactive-filter state) was also dimming the readable text
   label inside it, to 2.16:1 in both themes. I had actually looked at this
   exact rule earlier and judged it "legitimate UI state, leave alone" — that
   judgment was wrong because I checked semantic reasonableness, not the actual
   numbers. Moved the opacity to just the icon; label now always fully legible.
   (commit bfd182a)
8. `404.html`, `.error-page__code` ("404" ghost text) — used
   `--color-border-primary` as a text color, 1.91:1 light / 1.97:1 dark
   (need 3:1, large bold text). Switched to `--color-text-muted`: 7.04:1
   light / 6.68:1 dark. (commit f928355)
9. `404.html` and sitewide, `.btn--primary` / `.btn` / `.btn-generative` /
   `.section--brand` / `.skip-link` (every consumer of
   `--color-background-brand`) — paired with `--color-text-inverse`, which
   flips to near-black (#161618) in dark mode. That's correct when paired
   with a light surface, but `--color-background-brand` in dark mode is a
   mid-tone "lifted" blue (#4a648a), not light — near-black text measured
   2.99:1 (need 4.5:1). Light mode was fine (8.63:1) since background-brand
   there is dark navy. Added a new `--color-on-brand` token (white in both
   themes: 8.63:1 light, 5.59:1 dark) and swapped it into the 6 rules that
   pair text with `--color-background-brand`, leaving `--color-text-inverse`
   and its other consumer (`.text-inverse` utility) untouched. Grepped for
   other live usages of `.btn--primary`/`.btn-generative`/`.section--brand`
   after fixing: only `index.html` and `research.html` also reference
   `.btn--primary`, both inside the `{% else %}` empty-posts-state block
   that never renders while posts exist — so this bug was effectively only
   ever live on 404.html in production, not a retroactive miss on other
   already-"clean"-marked pages. Fixed the token anyway since it's the
   correct general fix and future empty-state/skip-link renders would have
   hit the same bug. (commit f928355)

## Site-wide findings / lessons (apply once, don't re-litigate per page)

- **Always check BOTH themes, not just one** — see finding #6 above.
- **axe-core needs 2-3 repeated runs after page settle**, not a single scan — see
  method section at top.
- **"Muted/secondary text color + opacity:0.6-0.75" is a real recurring
  anti-pattern** — 8 confirmed instances fixed. If a new page shows a similarly-
  muted element failing contrast, check for this exact pattern first.
- **Don't trust your own "this looks like a legitimate design choice" judgment
  without checking the actual axe-core numbers** — the gallery filter opacity
  (finding #7) is the counterexample: it looked like a normal active/inactive
  UI pattern and was actually a real, severe bug (2.16:1).
- **`--color-accent` is now properly defined** — don't reintroduce a hardcoded
  `#7c6af7` fallback anywhere; use `var(--color-accent)` bare. Foreground-on-accent
  should use `var(--color-on-accent)`, not hardcoded white — the two accent
  values invert lightness between themes.
- **New: `--color-on-brand` token** (added this session, finding #9) — anything
  painted on top of `--color-background-brand` (buttons, `.section--brand`,
  skip-link) should use `var(--color-on-brand)`, not `--color-text-inverse`.
  `--color-text-inverse` is for pairing with light/near-white surfaces only —
  it flips to near-black in dark mode, which breaks badly against the
  mid-tone "lifted" brand blue dark mode uses.
- **New: stale-paint / stale-read artifact in the browser automation itself**
  (not a site bug) — immediately after toggling the theme class via
  `javascript_tool`, a `getComputedStyle` read or an axe-core scan can
  return WRONG values for elements below the fold (colors from the
  *previous* theme, or a mix), even after a 1s wait and even across 3
  repeated axe runs with delays between them. A real browser screenshot
  taken at the same moment shows the CORRECT (already-switched) rendering —
  so this is a read/eval timing bug in the extension bridge, not an actual
  flash-of-wrong-theme on the live site. Fix: after toggling theme, force a
  reflow before trusting any JS-read color value or axe result — scrolling
  the page (e.g. down then back up, or down to the element in question) was
  sufficient every time this was hit. Screenshot first if a scan result
  looks implausible (e.g. reports dark-mode colors right after switching to
  light) before treating it as a real bug. Cost real time this session on
  404.html (chased a phantom `#bd-email` "1.02:1" violation twice, in both
  directions, before recognizing the pattern) — check for this specifically
  if a violation's reported foreground/background hex pair doesn't match
  the theme you think you just set.

## Visual bugs found + fixed this session (non-contrast, user-reported)

1. **`/research/` "Reading threads" grid — empty tan/beige void.** `research.html`
   hardcodes exactly 4 `.research-thread` items into a 3-column CSS grid
   (`.research-threads`, `assets/css/main-redesign.css` ~line 1351). Row 2 had
   only 1 populated cell; the other 2 grid tracks were empty, showing the
   container's border-colored background fill through the `gap:1px` trick —
   read as a large ugly filled box. Fixed with a `.research-thread--full`
   modifier (`grid-column: 1 / -1`) on the 4th item so it spans the full row.
   Confirmed via grep this grid pattern isn't reused elsewhere in the repo.
   Verified visually both themes — void gone, reads as an intentional
   full-width row. (commit 117ddbe)
2. **Homepage persona avatars (Maya Flux, Zen Circuit) — "glitchy/corrupted
   static" look.** Confirmed real, not a load-order flash (this was an open
   question carried over from the first Fable design pass). Root cause:
   source images are legitimate screen-print-style artwork (verified by
   viewing the full 1024px source directly — dense circuit-grid /
   cityscape-grid line art, not corrupted) but are 1024x1024 WebP files
   saved with a `.png` extension, rendered at 72-96px via a plain `<img>`
   with `object-fit: cover` — a textbook moire/aliasing trigger on
   Zen Circuit's periodic dot/dash grid especially. Fixed by pre-generating
   real 192x192 PNG thumbnails (PIL: Gaussian pre-blur radius 1.4, then
   `Image.LANCZOS` resize) for all 4 personas and pointing
   `index.html`'s `.agent-card__image` `src` at the new `*_thumb.png`
   files. Checked all 4 personas even though only 2 showed visibly in the
   report. Verified by direct inspection of the generated thumbnail files
   and in-browser screenshots at actual render size, both themes.
   `.filter-persona-icon` (research.html, 16px) checked and confirmed
   unaffected at that size — left alone. `about.html` has the identical
   unfixed pattern (same images, same `.agent-card__image` class, same
   size) — noted as a follow-up, not fixed this session (out of scope: only
   the homepage was reported). (commit 23a5445)
3. **Homepage `.agent-grid--2col` — large dead gap between the two Collective
   cards.** Not user-reported; found while re-verifying the homepage design
   pass. `grid-template-columns: repeat(2, 1fr) !important` stretched each
   column track to ~half the (wide) container, while `.agent-card` itself is
   capped at `max-width: 280px` and left-aligned within its much-wider cell —
   Pixel Nova/Siri Sage (and Maya Flux/Zen Circuit) rendered at opposite edges
   of the row with empty space between instead of a centered pair. Predated
   this session's changes, was live on production. Fixed by sizing the 2
   tracks to the card's own width (`repeat(2, minmax(252px, 280px))`,
   matching the base `.agent-grid`'s auto-fit range) so the existing
   `justify-content: center` actually centers the pair. Verified visually
   both themes; axe-core clean before and after. (commit 92096ae)

## Log

- 2026-08-04: scorecard created for WCAG audit, reframed same session to design
  quality after user clarified intent (AAA meant "looks premium," not WCAG
  conformance level). AA contrast work continued anyway per explicit confirmation
  it's a hard floor. Session paused here — context filling up — handoff prepared
  above for continuation in a fresh session or via subagent.
- 2026-08-04 (later session, subagent): closed out the remaining tail —
  404.html + 3 individual research subpages contrast-checked (2 new bugs found
  + fixed on 404.html, subpages were clean), orphaned stats page confirmed +
  skipped, both reported visual bugs (research-threads grid void, homepage
  avatar moire) confirmed real and fixed. 4 commits (f928355, 117ddbe,
  23a5445, plus this doc update), all pushed to origin/main. Remaining open
  work is unchanged: homepage's other open design findings, and a full Fable
  design critique pass on every non-homepage page (contrast-only so far).
  New follow-up noted: `about.html` has the same unfixed avatar-moire pattern
  as the homepage did (same images, same class) — trivial fix, same
  `*_thumb.png` files already exist, just needs the 4 `src` swaps.
- 2026-08-05: dispatched a subagent for the homepage's 7 open design findings
  (typography, light-mode treatment, separators, footer badge, persona border
  presence, hero dead space). It did the actual design work correctly — but
  hit the account's monthly Claude spend limit mid-task and was killed before
  it could verify or commit, leaving the diff uncommitted. The orchestrating
  session read the diff, confirmed it addressed all 7 findings coherently,
  finished verification itself (local jekyll build+serve, real screenshots
  both themes, axe-core 2x/theme, 0 violations), and committed it directly
  rather than re-dispatching. While re-verifying, found and fixed a new
  pre-existing bug (not from the original critique): `.agent-grid--2col`'s
  dead gap between cards (see visual bugs #3 above). Also closed the
  `about.html` avatar-moire follow-up noted in the previous log entry.
  3 commits (44f7bbc, 92096ae, 2c00a73) plus this doc update, pushed to
  origin/main. **Spend limit is now a live constraint** — flagged to the user
  before continuing further; if resuming with subagents, confirm headroom
  first or expect to finish verification/commit steps directly instead.
  Remaining work: the full Fable design-critique pass on every non-homepage
  page (still only contrast-checked, not design-critiqued) — batches 3-5,
  not yet started as of this entry.
- 2026-08-05 (follow-up session): finished Batch A's 3 pages that the
  previous session couldn't reach Fable for (CLIProxyAPI was down that
  whole session). Switched to OpenRouter direct
  (`anthropic/claude-fable-5`, key pulled fresh from trident's
  `/srv/secrets/openclaw.env`) — confirmed working, unlike CLIProxyAPI.
  Got real critiques for `/research/deaf-arts/` (both themes) and `/about/`
  (light theme) before the vision route hit a hard, non-recovering block
  specific to image-bearing requests (documented in full under "Batch A"
  section 5 above — not image-size-sensitive, not simple credit
  exhaustion, didn't clear after ~15 min of active + passive waiting,
  while the account balance stayed healthy the whole time and text-only
  calls kept working). `/press/` never got its critique as a result. 1 real
  page-specific bug found + fixed on `/about/` (`#start-here` section
  blending into the section above it — verified both themes, axe-core 0
  violations). All other Fable findings across the 3 pages were shared-
  component observations (touching other already-clean pages) —
  deliberately left with reasoning logged per finding, consistent with
  this scorecard's established judgment calls elsewhere. 1 code commit
  (`94ec300`) + this doc update, pushed to origin/main. Remaining work:
  `/press/`'s actual Fable critique (retry once the vision route recovers
  — screenshots already captured, don't need a re-shoot), plus the
  unstarted batches B/C.
- 2026-08-05 (later follow-up session, batch B): attempted the 5 batch-B pages
  (`/press/how-it-works/`, `/press/system-report/`, `/jascha/`, `/notes/`,
  `/accessibility/`). Screenshotted all 5, both themes, full page top-to-bottom.
  Re-diagnosed the OpenRouter vision-route block independently (fresh 4.5-minute/
  9-attempt active poll, cross-page image test, balance check) — confirmed it's the
  same account-level one-way-ratchet condition documented for `/press/` in Batch A,
  and it has not cleared across the session boundary. No Fable critique obtained for
  any of the 5 pages. Did a manual code-pattern check against every established
  anti-pattern from prior batches (pipe separators, hardcoded white rgba, opacity-
  muted-text stacking, raw-source avatars) — none found; the 5 pages are pure-text
  templates with no `<img>` tags. One harmless dead-code fallback hex noted (inline
  blockquote style, `--color-border-brand` already properly defined so the fallback
  never renders) — not fixed, not a bug. No code changes. 1 docs-only commit (this
  scorecard update) pushed to origin/main. Remaining work: retry Batch B's Fable
  critique once OpenRouter's vision route recovers (screenshots already captured,
  no re-shoot needed), then batch C (editorial-lens, collective pages, gallery).
