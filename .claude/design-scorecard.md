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
- [ ] 404 page — never checked
- [ ] `/research/camouflaging/`, `/research/care-labor/`, `/research/extreme-male-brain/` — same template as `/research/deaf-arts/` (already checked, clean) and `/research/` (checked, clean) — likely fine, but not actually verified individually, so don't assume
- [ ] `/cripminds-stats-2026-06.html` — confirm it's still linked/live before spending time; if orphaned, skip
- [ ] Homepage's remaining **design** (not contrast) findings, still open from the first Fable critique — see "Open design findings" section below. These are visual-polish items, lower priority than contrast, but were the original point of the exercise before the WCAG detour
- [ ] The rest of the site hasn't had a Fable *design* critique at all yet (only homepage did) — everything else has only been contrast-checked. If continuing the design-quality thread (not just accessibility), that's a separate pass still to do on every page below

**Pages verified clean this session (contrast only, not design-critiqued except homepage):**
`/`, article template, `/research/`, `/research/deaf-arts/`, `/about/`, `/press/`,
`/press/how-it-works/`, `/press/system-report/`, `/jascha/`, `/notes/`,
`/accessibility/`, `/editorial-lens/`, all 4 `/collective/*/` pages, `/gallery/`

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

## Log

- 2026-08-04: scorecard created for WCAG audit, reframed same session to design
  quality after user clarified intent (AAA meant "looks premium," not WCAG
  conformance level). AA contrast work continued anyway per explicit confirmation
  it's a hard floor. Session paused here — context filling up — handoff prepared
  above for continuation in a fresh session or via subagent.
