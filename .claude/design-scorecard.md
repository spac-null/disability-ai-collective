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
- [ ] Homepage's remaining **design** (not contrast) findings, still open from the first Fable critique — see "Open design findings" section below. These are visual-polish items, lower priority than contrast, but were the original point of the exercise before the WCAG detour
- [ ] The rest of the site hasn't had a Fable *design* critique at all yet (only homepage did) — everything else has only been contrast-checked. If continuing the design-quality thread (not just accessibility), that's a separate pass still to do on every page below
- [ ] `about.html` uses the same `.agent-card__image` pattern as the homepage with the same 4 full-size (1024px) source images at the same 72-96px render size — same latent moire issue, NOT fixed this session (out of scope, homepage was the only page reported). Trivial follow-up: point its 4 `<img src>` at the `*_thumb.png` files created this session (see finding below), same as index.html.

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

## Open design findings (homepage only — from the one Fable critique run this session)

Not contrast bugs — genuine design/polish findings, still open:
- Hero H1 uses generic default sans while article titles use a serif with real
  character — brand identity is weaker than the content's own typography
- Light mode reads as "dark mode recolored," not separately designed (persona
  accents + the black essay-hero artwork have no light-specific treatment)
- Inconsistent meta separators (middot in hero vs. pipe in grid cards)
- Essay-grid avatar dot rendering inconsistency (may just be a load-order flash,
  worth a second look before assuming it's a real bug)
- WCAG 2.1 AA footer badge is bare text, not treated as the credential it is
- Persona accent border colors read "timid" on dark
- Hero's right column is dead/empty space, not intentional asymmetry

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
