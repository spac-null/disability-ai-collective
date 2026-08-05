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
- [~] `/research/deaf-arts/` — Fable unreachable (see below), manually checked for the batch's already-established bug patterns, none found, no fixes needed/applied; critique itself still pending a retry
- [~] `/about/` — Fable unreachable (same outage as deaf-arts.html), manually checked for the batch's already-established bug patterns, none found, no fixes needed/applied; critique itself still pending a retry
- [~] `/press/` — Fable unreachable (same outage, persisted the entire batch), manually checked, none of the established bug patterns found, one measured non-bug (the below-fold gap before the footer), no fixes needed/applied; critique itself still pending a retry
- **Batch A (5 pages) is done as far as it can go this session.** 2 pages got
  a real Fable critique + fixes (article template, research.html), 3 pages
  (`/research/deaf-arts/`, `/about/`, `/press/`) got screenshots + a manual
  established-pattern check but no actual Fable critique — the CLIProxyAPI
  endpoint went down partway through the batch (`402` then persistent `500
  auth_unavailable`) and never recovered across ~15+ min of retries. Follow-up:
  **re-run the Fable critique call for those 3 pages** once the endpoint is
  confirmed healthy (`curl` a trivial request first) — screenshots are already
  captured in the session scratchpad
  (`/private/tmp/claude-501/.../scratchpad/screenshots/{deaf-arts,about,press}/`,
  ephemeral — re-shoot if that scratchpad is gone) so it doesn't need a full
  re-shoot, just the API call + any resulting fixes.
- [ ] Remaining pages (batches B/C — press subpages, jascha, notes, accessibility, editorial-lens, collective pages, gallery) still need their first Fable design critique

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

### 3. `/research/deaf-arts/` (research-thread subpage) — Fable unreachable, no fixes needed

Screenshotted both themes (full scroll, 3 shots/theme) as normal. The Fable
critique call itself failed 3x in a row with **two different errors**
across attempts — `402 Payment Required` on the first try, then
`500 {"error":{"message":"auth_unavailable: no auth available", ...}}` on
the second and third (after an 8s backoff) — pointing to a live problem on
the CLIProxyAPI/trident side (matches the pattern in this repo's own recent
git log: "log lasagna-smoke-gate auth fix"), not a request-shape issue on
this end (the exact same request shape worked 3x already for the article
template and research.html in this same session). Per the task's fallback
instructions, did not block the batch on this — moved forward.

In place of the critique, manually grepped `research/deaf-arts.html` for
the three bug patterns already established as real in this same batch
(pipe separators, hardcoded `rgba(255,255,255,...)`, raw non-`_thumb`
persona avatar images) — **zero hits, all three**. The page also renders
no `<img>` tags at all (confirmed via grep) — it's a pure-text template
(hero copy, a 3×3 grid of text-only teaser cards, an author card, footer),
so the avatar-visibility and image-quality bug classes that hit the other
two pages don't apply here by construction. No code changes made.

**Still needed**: the actual Fable design critique (typography/hierarchy/
spacing judgment) — retry once the endpoint is healthy. Screenshots are
already captured in the session scratchpad if a follow-up wants to reuse
them rather than re-shoot.

Commit: `4fa4e61`

### 4. `/about/` — Fable unreachable, no fixes needed

Same outage as `/research/deaf-arts/` above — retried the endpoint 3 more
times for this page specifically (including a 20s backoff) across roughly
5 minutes of elapsed session time, same `500 auth_unavailable` every time.
Confirmed sustained, not a one-off blip. Screenshotted both themes anyway
(full scroll, 7 shots/theme — this is a long page, ~5700px).

Manually checked for the same three established bug patterns: zero hits on
pipe separators and hardcoded `rgba(255,255,255,...)`. The persona-avatar
`<img>` tags already point at the `*_thumb.png` files with correct
`width="192" height="192"` — this page's avatar-moire bug was already found
and fixed in a prior session (commit `b40dd6e`, explicitly logged as a
follow-up from the homepage fix), confirmed still in place. Also checked
the `.agent-grid--2col` dead-gap bug (also previously fixed on the homepage,
commit `92096ae`) — since that fix lives in the shared CSS rule, not a
homepage-specific override, it already applies here too; the 2×2 persona
grid renders as a centered pair with no dead gap in the screenshots. No
code changes made.

**Still needed**: the actual Fable design critique — retry once the
endpoint is healthy. Screenshots already captured in the session
scratchpad.

Commit: `cb021ce`

### 5. `/press/` — Fable unreachable, no fixes needed

Same sustained outage, persisted for the entire remainder of this batch
(~15+ min elapsed across all 3 skipped-critique pages, multiple distinct
error bodies seen: `402 Payment Required` once, `500 auth_unavailable`
every other time). Screenshotted both themes (5 shots/theme, ~4500px page).

Manually checked for the batch's established patterns: no pipe separators,
no hardcoded `rgba(255,255,255,...)`, no persona-avatar images at all (this
page, like deaf-arts.html, is a pure-text template — confirmed via grep,
zero `<img>` tags).

**Specifically investigated the large visual gap between the "How Crip
Minds Works / System Report" buttons and the footer** (visible in the last
screenshot of both themes) since it looks similar to a gap Fable flagged as
a possible bug on the article template earlier in this batch (which turned
out to be normal spacing there). Measured via `getBoundingClientRect()`:
button-bottom → `main` bottom is 164px, `main` bottom → `#footer` top is a
further 64px (the latter matches the standard section-to-footer spacing
already confirmed normal on the article template). The extra 100px on top
of that traces to an explicit, deliberate inline style on this page's
content wrapper (`padding-bottom: 100px`, set in the page's own markup,
not a stacking accident) — this is a page that intentionally trails off
with utility links rather than a strong closing statement, so the extra
breathing room reads as a deliberate choice, not a layout bug. Left as-is.

No code changes made. **Still needed**: the actual Fable design critique —
retry once the endpoint is healthy. Screenshots already captured in the
session scratchpad.

Commit: (pending, see log)

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
