# Link & Surface Hygiene Findings — Static Surface

Section 6 of the audit directive. Internal links across the static
pages/layouts inventoried in `STATIC-PAGE-INVENTORY.md` were checked by direct
grep-cross-reference against the site's own permalink structure; external
social/contact links were spot-checked live. Article-body outbound links were
explicitly out of scope per the directive and were not crawled.

## Internal navigation — no broken links found

Checked: `_layouts/default.html` header nav (Home/Articles/Press/About) and
footer ("Explore": Articles, Reading Threads, The Collective, Press &
Background, Accessibility, About the Creator), plus every internal `<a href>`
appearing in `index.html`, `about.html`, `press/*`, `jascha.html`, `notes.html`,
`accessibility.html`, `research.html`, and the four `_collective/*.md` bios.
Every internal target (`/about/`, `/jascha/`, `/press/`, `/press/how-it-works/`,
`/press/system-report/`, `/research/`, `/research/#threads`, `/about/#agents`,
`/about/#language-note`, `/accessibility/`, `/collective/{persona}/`,
`/2026/03/16/the-map-that-stops-at-the-door/`, and the other two "Three places
to start" article links on `about.html`) resolves to a real, live page or a
real anchor on a real page. **No dead internal links found in the non-article
static surface.**

## F-4 cross-reference (see FACTUAL-FRESHNESS-FINDINGS.md)

`/notes/` is live and sitemap-indexed but unreachable from primary nav/footer —
recorded there as a discoverability question, not a broken link (the page
itself works fine once reached via an article footer).

## Robots.txt / sitemap / build-exclusion consistency

- `robots.txt` disallows three pages that no longer exist as built pages at all:
  `/style-lab/` and `/realistic-scenes/` both carry `published: false` in their
  frontmatter, so Jekyll never builds them — the `robots.txt` rules for them are
  now dead weight (harmless, but stale housekeeping; safe to remove once
  confirmed the pages are intentionally unpublished, not accidentally so — see
  OWNER-DECISIONS.md).
- `gallery.html` is the one page `robots.txt` disallows that IS actually built
  and live — see F-5 in FACTUAL-FRESHNESS-FINDINGS.md for its missing `noindex`
  meta tag.
- `/archive/`, `/automation/`, `/docs/` are both `robots.txt`-disallowed AND
  `_config.yml`-excluded — correctly double-covered, no gap.
- `/calibration/` is covered by **neither** mechanism — see T-1 in
  ARCHITECTURE-AND-TRUST-FINDINGS.md, the most significant finding of this
  audit.

## External / social surfaces

| Surface | Status |
|---|---|
| Bluesky (`bsky.app/profile/cripminds.bsky.social`) | Reference present in footer + JSON-LD `sameAs`; handle format confirmed, live-activity not independently re-verified this pass |
| Tumblr (`tumblr.com/cripminds`) | **Live, active**, posting cadence consistent with site's own recent article activity. Bio-text positioning conflict recorded as F-2 |
| Ko-fi (`ko-fi.com/T8K7Z04KYU`) | Present in footer + `jascha.html`; not independently checked live this pass |
| `mailto:editor@cripminds.com` | Present on `about.html` | not independently verified deliverable |
| `mailto:jascha@cripminds.com` | Present on `accessibility.html`, `press/index.html`, `jascha.html` | not independently verified deliverable |
| `jaschablume.nl` | Linked from `press/index.html` | not independently checked live this pass (out of primary scope — external personal site, not a CripMinds surface) |
| GoatCounter (`stats.cripminds.com`) | Script tag present in every page footer; not independently checked live this pass |
| Newsletter subscribe endpoint (`subscribe.cripminds.com/subscribe`) | Referenced in both the footer form and `_includes/subscribe-form.html`; not independently checked live this pass (would require a real POST to test, out of scope for a read-only audit) |

None of the above were found broken; several simply weren't independently
re-verified live in this pass (listed for completeness, not as findings).

## Duplicate / orphaned static pages

- No duplicate pages found covering the same content under two different paths.
- `collective.html` (bare `/collective/`) is a deliberate meta-refresh stub to
  `/about/#agents`, not an orphan — exists to catch old/external links to the
  bare collective URL. Working as designed.
- `cripminds-stats-2026-06.html` exists in the repo root but is explicitly
  excluded from the Jekyll build (`_config.yml`) — it is not live, not a
  duplicate-in-production, just a historical artifact sitting in the working
  tree. No action needed unless the owner wants it deleted for tidiness.
