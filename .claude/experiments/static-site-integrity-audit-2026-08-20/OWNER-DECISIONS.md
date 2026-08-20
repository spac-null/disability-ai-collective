# Owner Decisions Required — Static Site Integrity Audit

Isolated per the audit directive (§7, `OWNER_DECISION` disposition). Nothing
below has been acted on. Ordered by priority.

## OD-1 (ties to T-1, P1). Calibration research directory: exclude from build now, decide on already-indexed pages

**Decision needed**: (a) approve adding `calibration/` to `_config.yml`
`exclude:` and/or `robots.txt Disallow: /calibration/` as immediate mitigation;
(b) decide whether the pages already indexed via `sitemap.xml`
(`calibration/workflows/*`) need an active removal request from search engines,
or whether simply excluding them from future builds/sitemaps is sufficient; (c)
decide whether `calibration/`'s data (research context, candidates,
preregistration, the runner script + systemd service file) belongs inside the
public Jekyll site root at all, even unexcluded — vs. relocating it under
`automation/` (already excluded) or outside the repo entirely.

## OD-2 (ties to F-2, P2). Tumblr bio text — off-repo fix

**Decision needed**: the live Tumblr bio ("a disability-led AI arts journal
managed by four AI agents") contradicts current on-site positioning. This repo
cannot fix it — the owner needs to edit the Tumblr profile bio directly. Flagging
for awareness and a decision on new wording; no repo action possible.

## OD-3 (ties to F-1, P3). Accessibility statement date

**Decision needed**: confirm whether the 2026-08-05 design-scorecard audit
touched anything `accessibility.html` claims (toggles, WCAG feature list). If
yes, bump "Last updated" to the correct date. If the audit found the page
already compliant and changed nothing on it, no action needed — the June 12
date would remain accurate. This diff was not performed in this pass (would
require reading the 62KB `design-scorecard.md` end-to-end against the current
page, judged out of scope for a static-surface-only audit with a hard stop).

## OD-4 (ties to LINK-AND-NAV, P4). Dead `robots.txt` rules for unpublished pages

**Decision needed**: `robots.txt` disallows `/style-lab/` and
`/realistic-scenes/`, but both pages carry `published: false` and are never
built. Confirm this is intentional (pages are deliberately shelved/experimental,
not accidentally orphaned) before removing the now-unnecessary `robots.txt`
lines — if they're expected to come back, leave the rules in place as
forward cover.

## OD-5 (ties to F-4, P4). `/notes/` discoverability

**Decision needed**: is `/notes/` meant to be a real, ongoing editorial-voice
channel (in which case it should probably join the footer's "Explore" list) or
an intentionally low-key surface only reachable from an article footer? Either
is defensible; just needs a decision so it isn't an accident either way.

## OD-6 (ties to T-2, P3). Pre-emptively exclude `reader-lab/`

**Decision needed**: low-stakes, cheap — approve adding the currently-empty
`reader-lab/` directory to `_config.yml`'s `exclude:` list now, before it
collects content and becomes a second T-1.
