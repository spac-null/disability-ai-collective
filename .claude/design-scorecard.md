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
| `/` (homepage) | 🟨 | Fable design critique run (5 real screenshots, light+dark). Fixed: `.agent-grid` flex→grid (unequal card heights 496-554px, and `.agent-grid--2col` modifier was silently dead under flex — homepage was rendering 4-across instead of intended 2x2); duplicate subscribe form removed (footer already has one on every page). **Not yet fixed, real findings from Fable, next iteration:** hero H1 uses generic default sans while article titles use a serif with real character — brand identity is weaker than the content's own typography; subscribe button is unbranded Tailwind indigo; light mode reads as "dark mode recolored" not separately designed (persona accents + the black essay-hero artwork have no light-mode-specific treatment); inconsistent meta separators (middot in hero vs. pipe in grid cards, inconsistent spacing even within the pipe style); small essay-grid author avatar dots render inconsistently (worth checking if it's a real asset issue or just a load-order flash); WCAG 2.1 AA footer badge is bare text, not treated as the credential it is; persona accent border colors read as "timid" on dark — could afford more saturation/contrast without breaking the muted aesthetic; right column of hero is dead/empty space, not intentional asymmetry. |
| article template (`_layouts/post.html`) | ⬜ | | |
| `/research/` | ⬜ | | |
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

(populated as patterns emerge across pages)

## Log

- 2026-08-04: scorecard created for WCAG audit, reframed same session to design
  quality after user clarified intent. AA contrast bug found and fixed before
  the reframe (kept, since AA is a confirmed hard requirement regardless).
