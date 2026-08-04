# Design-quality scorecard — visual polish, not WCAG

Reframed 2026-08-04: original ask sounded like WCAG "AAA" (accessibility conformance
level) but actually meant design/visual quality — typography, layout, polish,
"does this look like a top-tier studio built it." WCAG AA remains a hard floor
(explicitly confirmed) but is no longer the loop's main subject — see the one-time
axe-core pass below for that.

Method per page: real browser screenshot (light + dark, desktop + mobile widths) →
Fable 5 design critique (typography, hierarchy, spacing/rhythm, color cohesion,
image quality, whitespace, "does this read as intentional or default") → concrete
fix → re-screenshot to confirm.

## Legend
- ⬜ not yet reviewed
- 🔍 reviewed, issues found, not yet fixed
- 🟨 partially addressed
- ✅ reviewed and fixed to a genuinely polished standard

## One-time WCAG AA pass (accessory, not the main loop)

Ran a live axe-core scan (WCAG 2.2 A/AA/AAA, all tags) against the homepage in
dark mode before the reframe:
- **Real AA violation found and fixed**: `.agent-identity` persona badges used raw
  brand hex as text color on dark card backgrounds — Maya Flux as low as 1.65:1
  against the 4.5:1 AA minimum. Fixed in `assets/css/main-redesign.css` (dark-theme
  text variants added, hue preserved, lightened to clear 5:1). Commit efbf0aa.
- 16 nodes flagged for AAA-only enhanced contrast (7:1) on muted/secondary text
  (eyebrows, labels, dates) — these already pass AA and are a normal editorial
  "muted metadata" convention; not chasing AAA text contrast site-wide, since
  that's a much larger, more invasive change than what was actually asked for.
- Other pages not yet scanned with axe-core. If something looks visually
  suspicious during the design pass (low-contrast text, etc.) treat it as a
  design finding AND flag it here for a quick contrast check, but don't run a
  full axe pass on every page as a matter of course — that was the old scope.

## Pages (priority order — high-traffic first, per GSC/GoatCounter data)

| Page | Status | Findings | Fixes |
|---|---|---|---|
| `/` (homepage) | 🟨 | Pass 2 done. **Fixed so far:** `.agent-grid` flex→grid (unequal card heights, and `.agent-grid--2col` was silently dead under flex — was rendering 4-across instead of 2x2); duplicate subscribe form removed; **`--color-accent` was undefined sitewide, silently falling back to Pixel Nova's exact hex in all 9 usages** — defined properly as teal (#0e7568 light / #3fc9b8 dark, real contrast math, Fable-recommended for sitting in the open hue gap between personas); found+fixed a follow-on bug from that same fix (white button text unreadable on the new lighter dark-mode teal, 2.05:1 — added `--color-on-accent` token); `.post-category-label` had the same raw-persona-hex-as-text bug as the earlier `.agent-identity` fix (Maya Flux 1.91:1 on author pages); author.html byline had a stacked `opacity:0.6` pushing already-muted text under 4.5:1. All verified via axe-core before/after, not assumed — homepage dark, author page light+dark all clean now (0 AA violations). **Still open, next iteration:** hero H1 typography (generic sans) vs. article titles (serif with character) — brand identity gap; light mode reads as "dark mode recolored," not separately designed (persona accents + black essay-hero artwork have no light-specific treatment); inconsistent meta separators (middot vs. pipe); essay-grid avatar dot rendering; WCAG 2.1 AA footer badge is bare text, not treated as a credential; persona accent border colors read "timid" on dark; hero's right column is dead space. |
| article template (`_layouts/post.html`) | ✅ | Reading experience itself already reads well typographically (serif body, good line length/height, legible both themes) — no design fixes needed here, this pass was all contrast. **Found a sitewide systemic bug**: "already-muted color + opacity:0.6-0.75" stacking, verified via real math to fail AA in 11 of 13 instances checked codebase-wide. Fixed all 6 real instances (`.site-tagline` — every page, `.post-breadcrumb__link`, `.post-author-eyebrow`, `.research-threads__eyebrow`, `.post-meta__register`, `.post-meta__item` separator, `.link--subtle`), plus a 4th instance of the raw-persona-hex-as-text bug (the "More by {persona}" button, was inline-styled, moved to data-persona+CSS). Verified clean via axe-core, light+dark. | commit 647629b |
| `/research/` | ✅ | Found + fixed a 5th instance of the opacity-on-muted-text bug (inline in research.html, "137 essays"). Otherwise clean both themes. | commit c50f967 |
| `/about/` | ⬜ | | |
| `/press/` | ⬜ | | |
| `/press/how-it-works/` | ⬜ | | |
| `/press/system-report/` | ⬜ | | |
| `/collective/*` (4 persona pages, 1 template) | ⬜ | | |
| `/jascha/` | ⬜ | | |
| `/notes/` | ⬜ | | |
| `/accessibility/` | ⬜ | | |
| `/editorial-lens/` | ⬜ | | unfamiliar page — check what it is first |
| `/research/camouflaging/` etc. (topic filters) | ⬜ | | likely same template as /research/ |
| `/cripminds-stats-2026-06.html` | ⬜ | | confirm still linked before spending time |
| 404 page | ⬜ | | |

## Site-wide findings (apply once, fix once)

- **Always check BOTH themes, not just one.** `.agent-identity`, `.post-category-label`,
  and `.persona-more-btn` were each fixed for dark mode first (where the bug was found),
  and each turned out to ALSO fail in light mode for 3 of 4 personas — a check I hadn't
  run initially. Now fixed in both directions for all three. When checking any new page,
  scan light AND dark before considering it clean.
- **axe-core needs 2-3 repeated runs after page settle, not a single scan.** A few checks
  this session gave inconsistent violation counts between calls on the same page/theme —
  traced to images still loading (`document.images` not all `.complete`) affecting
  computed-style timing. Pattern that works: run the scan once (discard), wait ~300ms,
  run again, and if still unsure, run a 3rd time — stable results only.
- **"Muted/secondary text color + opacity:0.6-0.75" is a real recurring anti-pattern**,
  not a one-off — 8 confirmed instances found and fixed across the CSS file and inline
  styles (site-tagline, breadcrumb, author-eyebrow, research-threads-eyebrow, post-meta
  register/separator, link--subtle, "137 essays", "The Collective" eyebrow). If a new
  page shows a similarly-muted element failing contrast, check for this exact pattern
  first before assuming something new.
- **`--color-accent` is now properly defined** (teal, light `#0e7568` / dark `#3fc9b8`) —
  don't reintroduce a hardcoded `#7c6af7` fallback anywhere; use `var(--color-accent)`
  bare. Foreground-on-accent (e.g. button text) should use `var(--color-on-accent)`,
  not a hardcoded white — the two accent values have inverted lightness between themes
  so a fixed white/black foreground can't serve both.

## Log

- 2026-08-04: scorecard created for WCAG audit, reframed same session to design
  quality after user clarified intent. AA contrast bug found and fixed before
  the reframe (kept, since AA is a confirmed hard requirement regardless).
