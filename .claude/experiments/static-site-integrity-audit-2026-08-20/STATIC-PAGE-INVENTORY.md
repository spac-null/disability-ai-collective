# Static Page Inventory — CripMinds Public Surface

Frozen 2026-08-20. Scope: non-article static pages/surfaces only. The 142-article
`_posts/` corpus is explicitly excluded (separate LC1 workstream, per audit
directive). Hashes are in `SHA256SUMS.txt` (same order as below); full path,
current git HEAD state.

Live deploy confirmed healthy at freeze time: `gh run list --workflow="Deploy to
GitHub Pages"` shows the latest push (commit touching `research/care-labor.html`)
built successfully 2026-08-20T12:07:57Z, ~7h before this freeze. No pending/failed
runs.

## A. Core static pages (root, rendered via `_layouts/default.html`)

| Page | Path | Public URL | Last git change | Built? |
|---|---|---|---|---|
| Home | `index.html` | `/` | `4adc6d2` 2026-08-12 | Yes |
| About | `about.html` | `/about/` | `4adc6d2` 2026-08-12 | Yes |
| Accessibility statement | `accessibility.html` | `/accessibility/` | `e4746db` 2026-08-12 | Yes |
| 404 | `404.html` | `/404.html` | `e4746db` 2026-08-12 | Yes (noindex) |
| Visual archive | `gallery.html` | `/gallery/` | `84c96a2` 2026-08-12 | Yes (sitemap:false, robots.txt disallow, **no noindex meta**) |
| Style Lab | `style-lab.html` | n/a | `84c96a2` 2026-08-12 | **No** — `published: false` |
| Realistic Scenes | `realistic-scenes.html` | n/a | `84c96a2` 2026-08-12 | **No** — `published: false` |
| Articles index | `research.html` | `/research/` | `aa0172e` 2026-08-15 | Yes |
| Jascha personal statement | `jascha.html` | `/jascha/` | `5646db8` 2026-08-12 | Yes |
| Notes (editor voice) | `notes.html` | `/notes/` | `b73c07c` 2026-06-15 | Yes — in sitemap.xml, **not linked from main nav or footer** |
| Collective redirect stub | `collective.html` | `/collective/` | `916af3e` 2026-06-15 | Yes — meta-refresh to `/about/#agents` |
| Stats snapshot | `cripminds-stats-2026-06.html` | n/a | `dd6bb6a` 2026-06-15 | **No** — explicitly in `_config.yml` `exclude:` |

## B. Press / background

| Page | Path | Public URL | Last git change |
|---|---|---|---|
| Press & background | `press/index.html` | `/press/` | `4d5efc4` 2026-08-12 |
| How Crip Minds Works | `press/how-it-works/index.html` | `/press/how-it-works/` | `a8587f3` 2026-08-12 |
| System Report | `press/system-report/index.html` | `/press/system-report/` | `a8587f3` 2026-08-12 |

## C. Research pillar/cluster pages (hand-authored `CollectionPage` + `hasPart` JSON-LD)

| Pillar | Path | Public URL | `hasPart` count (verified against real `_posts` files) | Count shown on `/research/` |
|---|---|---|---|---|
| Deaf Arts (Pixel Nova) | `research/deaf-arts.html` | `/research/deaf-arts/` | 9 — matches | "9 essays" ✅ |
| Care Labor (Maya Flux & Zen Circuit) | `research/care-labor.html` | `/research/care-labor/` | 5 — matches | "5 essays" ✅ |
| Extreme Male Brain (Zen Circuit) | `research/extreme-male-brain.html` | `/research/extreme-male-brain/` | 5 — matches | "5 essays" ✅ |
| Camouflaging (Zen Circuit) | `research/camouflaging.html` | `/research/camouflaging/` | 4 — matches | "4 essays" ✅ |

All 23 `hasPart` article URLs across the four pillars resolve to real `_posts/*.md`
files on disk — no dangling references, no stale counts. **KEEP as-is.**

## D. Persona / collective pages (`_collective` collection → `_layouts/author.html`)

| Persona | Source | Public URL |
|---|---|---|
| Pixel Nova | `_collective/pixel-nova.md` | `/collective/pixel-nova/` |
| Siri Sage | `_collective/siri-sage.md` | `/collective/siri-sage/` |
| Maya Flux | `_collective/maya-flux.md` | `/collective/maya-flux/` |
| Zen Circuit | `_collective/zen-circuit.md` | `/collective/zen-circuit/` |

All four last touched `5646db8` (2026-08-12), consistent with the same pass that
rewrote `about.html`/`jascha.html`. Positioning language (disability shapes *how*
a persona looks, never *what* it may look at) matches current canonical framing.

## E. Works collection

| Work | Source | Public URL |
|---|---|---|
| What the Room Heard | `_works/what-the-room-heard.html` | `/works/what-the-room-heard/` |

## F. Shared chrome / templates (not pages themselves, but render every page)

`_layouts/default.html`, `_layouts/post.html`, `_layouts/author.html`,
`_layouts/work.html`, `_layouts/debate.html`, `_includes/subscribe-form.html`,
`_data/related.yml`, `_data/threads.yml`, `_config.yml`, `robots.txt`.

## G. Unintended public surface — Reader Lab calibration artifacts

**Not originally in scope as a "page" — surfaced during freeze because these files
are live-fetchable on the production domain and several are sitemap-indexed.**
Full detail and disposition in `ARCHITECTURE-AND-TRUST-FINDINGS.md` (Finding T-1).

| File | Path | Live status (checked 2026-08-20) |
|---|---|---|
| Analyze human round v1/v2 | `calibration/workflows/analyze-human-round-v{1,2}.md` | Built to HTML, **in sitemap.xml** |
| Prepare candidates / next round | `calibration/workflows/prepare-{calibration-candidates,next-round}-v1.md` | Built to HTML, **in sitemap.xml** |
| Candidates README | `calibration/candidates/README.md` | Built to HTML |
| RL-2026-001/002 research context | `calibration/research-context/RL-2026-00{1,2}.json` | **Confirmed 200 OK live**, raw JSON, not sitemap-listed but not disallowed |
| RL-2026-002 candidates/preregistration JSON | `calibration/candidates/RL-2026-002-*.json` | Same as above, not individually verified but same directory/exclude status |

`/calibration/` (bare directory index) itself 404s — no directory listing — but
every individual file is reachable by direct path and none are blocked by
`robots.txt` or Jekyll's `exclude:` list.

## H. Explicitly excluded from Jekyll build (confirmed not live)

`accessibility/` (audit logs, distinct from `accessibility.html`), `archive/`,
`automation/`, `docs/`, `reader-lab-worker/`, `*.py`, `*.db`, `MANIFESTO.md`,
`PIPELINE.md`, `SCRAPING_ETHICS.md`, `requirements.txt`,
`cripminds-stats-2026-06.html`. `reader-lab/` is not in the exclude list but is
currently an empty directory (zero files) — not a live risk today, worth
excluding preemptively before it gains content (see CLEANUP-PLAN.md).

## I. Social / external surfaces linked from the static site

| Platform | URL (from footer/pages) | Checked live 2026-08-20 |
|---|---|---|
| Bluesky | `bsky.app/profile/cripminds.bsky.social` | Handle format confirmed present in footer/JSON-LD `sameAs`; live-activity not independently confirmed this pass |
| Tumblr | `tumblr.com/cripminds` | **Live and active**, most recent post 2026-08-10 matches most recent `_posts` activity. Bio text says "managed by four AI agents" — see Finding P-1 in FACTUAL-FRESHNESS-FINDINGS.md |
| Ko-fi | `ko-fi.com/T8K7Z04KYU` | Not independently checked this pass |
| Mastodon (disabled.social) | **Not present anywhere in current static site** | Per project memory this was pending account approval, never shipped — absence is consistent, not a defect |
