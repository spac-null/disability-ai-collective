# Batch 2 Remediation Record — Metadata / Freshness / Representation Hygiene

2026-08-20. Follows Batch 1 (website containment + trust wording, commits
`f7a355d`/`3242e50`/`5ac5c9b`/`98ea267`/`2f61ed2`). Does not reopen Batch 1.
Does not start Batch 3 (positioning/story rewrite remains untouched). Built in
an isolated worktree/branch off `origin/main` (`batch2-metadata-hygiene-2026-08-20`),
never on local `main` (a peer session is active in that history).

## 1. Gallery noindex — CLOSED

`gallery.html` had `sitemap: false` but no `noindex: true`, unlike
`style-lab.html`/`realistic-scenes.html` which correctly set both (same
`robots.txt` disallow group: `/style-lab/`, `/gallery/`, `/realistic-scenes/`).
Added `noindex: true` to frontmatter — one line, matches the existing pattern
read from `_layouts/default.html`'s `{% if page.noindex %}` logic. Page
remains normally reachable for human visitors; only the `<meta name="robots">`
tag changed from the default `index, follow` to `noindex, nofollow`.

## 2. sameAs / Tumblr — CLOSED

Found the site's actual live Tumblr URL in the footer link
(`_layouts/default.html`): `https://www.tumblr.com/cripminds`. Verified live
before adding (WebFetch: active blog, posts through August 2026). Added to
the single upstream `Organization.sameAs` array in `_layouts/default.html`
(drives all pages' JSON-LD, not duplicated per-page). Existing Bluesky
`sameAs` entry (`https://bsky.app/profile/cripminds.bsky.social`) verified
still resolves (HTTP 200, real profile `did:plc:4x2xhho3ozmrknpxqbdjtmbv`,
handle `cripminds.bsky.social`) — left unchanged. No speculative/unverified
accounts added.

## 3. Tumblr bio stale wording — CONFIRMED STALE, NOT CORRECTED (off-repo)

Live bio fetched 2026-08-20 (`https://www.tumblr.com/cripminds`, read-only,
no login attempted): **"Disability-led AI arts journal. Four AI agents
explore crip culture, accessibility, and creative technology. cripminds.com"**

This contradicts current on-site positioning (`about.html`, `press/*`), which
since Batch 1 explicitly frames the four personas as fictional editorial
constructs authored by Jascha Blume, not autonomous AI agents. "Four AI
agents explore..." reads as exactly the autonomous-persona framing the site
now rules out.

**No credentials exist in this environment to log into Tumblr — this was not
attempted, and no posting tooling was built.** Recorded for owner action:

- Profile: `https://www.tumblr.com/cripminds`
- Current bio (verbatim, above)
- Recommended replacement: *"Crip Minds is a disability-led AI arts journal.
  Four fictional editorial personas, authored by Jascha Blume, explore crip
  culture, accessibility, and creative technology through AI-assisted
  writing. cripminds.com"* (or shorter, owner's call — the only requirement
  is not presenting the personas as autonomous agents)
- **Manual follow-up required: YES** — owner must edit the Tumblr profile
  bio directly.

## 4. Accessibility "last updated" date — CHANGED

**Evidence found**: commit `e4746db` ("site: align public metadata and
persona framing", 2026-08-12) substantively edited `accessibility.html`'s own
contact-response commitment — removed the specific "Acknowledge: within 24
hours / Critical fixes: within 48 hours" SLA language and the "I'll respond
within 48 hours" line, replacing both with softer, non-time-bound commitment
language ("I read accessibility reports and prioritize fixes according to
their impact"). This is a substantive change to exactly the kind of claim
this page's own "Last updated" line is meant to track, dated 2026-08-12 —
five weeks after the page's stated "Last updated: June 12, 2026," and it is
also the most recent commit touching this file (confirmed via
`git log -- accessibility.html`). The separate, oft-cited 2026-08-05
design-scorecard audit was checked too and found to have made **zero**
substantive changes to this specific page (confirmed reviewed-but-clean per
`.claude/design-scorecard.md` Batch B) — so that particular audit does not
independently justify a date change, but the `e4746db` commit does.

**Action**: bumped "Last updated" from June 12, 2026 to **August 12, 2026**
in `accessibility.html`, matching the actual last substantive-content commit.

## 5. Feed config hygiene — CLOSED (inert config removed)

**Traced actual behavior**: `feed.xml` and all four persona feeds
(`feed-maya-flux.xml`, `feed-pixel-nova.xml`, `feed-siri-sage.xml`,
`feed-zen-circuit.xml` — live at `/feed.xml` and `/feed/<persona>.xml` via
frontmatter `permalink`) are hand-authored Liquid/RSS templates. `feed.xml`
hardcodes `limit:10` and reads `site.title`/`site.description` directly; each
persona feed hardcodes `limit: 20` and its own persona-specific description
string. None of the four reference `site.feed.*` anywhere.

`_config.yml` listed `jekyll-feed` in `plugins:` and carried a `feed:` block
(`path: feed.xml`, `template: feed.xml`, `limit: 20`, a `description:`
string, `author:`, `categories:`). Because a real `feed.xml` file already
exists at the plugin's configured output path, jekyll-feed's own generation
is suppressed for that path (Jekyll does not overwrite an existing page at
the same destination) — and no page anywhere uses the plugin's `feed_meta`
Liquid tag (checked `_layouts/`, `_includes/` — zero hits). The entire `feed:`
config block was therefore inert: not read by `feed.xml`, not read by any
persona feed, not read by any template tag.

**Action**: removed the inert `feed:` block from `_config.yml`, replaced with
a one-line comment explaining actual behavior and pointing at the real
template files. Did **not** touch `jekyll-feed`'s entry in `plugins:` (a
larger, separate call about whether to keep declaring an unused plugin — out
of scope for "config hygiene," left alone). Did **not** rewrite `feed.xml` or
any persona feed to match the old config — config was corrected to match
reality, not the reverse.

## 6. Persona feed discoverability — OWNER_DECISION, unchanged

Git history for the four persona-feed files shows exactly one substantive
commit (`2555d44`, 2026-03-14, message: "add per-author RSS feeds" — no
further elaboration) plus one metadata-only touch in the same Batch-1-era
pass (`e4746db`). Repo-wide grep for any reference to `/feed/maya-flux.xml`
(or the other three) outside the feed files themselves returns **zero
hits** — no autodiscovery `<link>` tag, no persona-page mention, no footer/nav
reference, five-plus months after creation. Intent (deliberately
undiscoverable vs. simply orphaned) cannot be established deterministically
from available evidence.

**Disposition: OWNER_DECISION.** Left unchanged — still generated correctly,
still reachable by direct URL, still not linked from anywhere on-site. Not
treated as a blocker for Batch 2 completion per directive.

## 7. Robots/sitemap remaining hygiene (OD-4) — NO CHANGE — CLAIM VERIFIED

Did not touch the Batch-1 `/calibration/`/`/reader-lab/` rules.

For OD-4 (dead-looking `robots.txt` lines for `/style-lab/`/
`/realistic-scenes/`, both `published: false`): found commit `84c96a2`
("site: keep visual working methods private", 2026-08-12 — same session as
`e4746db` above) which explicitly added `published: false` to both pages with
clear, deliberate intent language ("keep visual working methods private").
This is a permanent-shelving decision, not accidental orphaning, and it
mirrors the exact defense-in-depth pattern Batch 1 used for
`/calibration/`/`/reader-lab/`: build-exclusion (here, `published: false`) as
the real mechanism, `robots.txt` disallow as a backstop against any future
accidental re-publish. **The `robots.txt` lines are correctly kept as
defense-in-depth, not dead code — no removal.**

Verified post-change: `sitemap.xml` still has **zero** `/calibration/` or
`/reader-lab/` entries (unchanged from Batch 1; nothing in Batch 2 touches
that exclusion).

## 8. Propagated metadata sanity check — PASS

Bounded to the already-corrected articles from the recent integrity work
(identified via `git log --all --oneline | grep -i "swan care\|care-labor"`):

- `_posts/2026-06-04-swan-care-solutions-ltd-classified-someone-as-equipment.md`
- `_posts/2026-06-19-swan-care-is-appealing-the-appeal-is-the-mechanism.md`
  (retitled "Winning the Case Does Not Turn Off the Clock")
- `_posts/2026-06-20-i-use-care-workers-we-are-caught-in-the-same-trap-from-two-directions.md`
- `_posts/2026-05-30-nhs-lancashire-and-south-cumbria-recruited.md`
- `_posts/2026-06-09-three-months-in.md`
- `research/care-labor.html` (static research pillar page, hand-written)

Checked the actual fix-commit diffs (`c07e19a`, `7c4719d`, `70d9292`): the
corrections touched **frontmatter fields directly** (`title`, `excerpt`,
`description`), not just body prose. Since card titles/descriptions, JSON-LD,
OpenGraph tags, and all four feeds are built from this same frontmatter via
Liquid at deploy time (`site.posts` loops on the homepage, `feed.xml`,
persona feeds), they are correct by construction — confirmed the homepage
(`index.html`) has no hardcoded excerpt copy, only `{% for post in
site.posts %}` loops.

`research/care-labor.html` (hand-written, not built from post frontmatter)
was separately checked. A repo-wide grep for the old fabricated figures
(`£28,048`, `£5 an hour`, `deducted his housing`) turned up one hit in this
file — read in context, it is the page's own dated correction/transparency
note ("**Correction, 20 August 2026:** An earlier version of this page
stated that Shabin Shaji was paid £5 an hour... None of these are supported
by the tribunal record...") — i.e., the corrected page explicitly quoting the
prior error to disclose it, not a live stale claim. Not a finding.

Two internal-only artifacts also matched the same grep
(`_reviews/2026-06-04-swan-care-solutions-ltd-classified-someone-as-equipment-review.md`,
`.claude/legacy-corpus-integrity-phase1-2026-08-16.md`) — neither is served
publicly by the Jekyll build; noted, not in scope for a public-surface check.

**Result: PASS. No remaining stale public representations found** for these
articles' cards, JSON-LD, OpenGraph, feed entries, or index references.

## Deployment

`git diff --stat` against prior `origin/main` tip: `_config.yml`,
`_layouts/default.html`, `accessibility.html`, `gallery.html` — 4 files, 9
insertions, 10 deletions. No `automation/`, no `_posts/`, no migration code.
`automation/` and Phase-2 capture confirmed unaffected (diff scope alone is
sufficient evidence — neither is anywhere in this diff).

---

# Batch-2 closure verification — 2026-08-20 (independent pass)

The remediation above was executed and committed but its record stopped at
`git diff --stat`: it named no deployment run and asserted no live
verification. This section closes that gap. Every claim below was checked
against the **live site**, not the repository.

## Deployment

| | |
|---|---|
| Content commit | `5f411a1` — gallery noindex, Tumblr `sameAs`, feed config, accessibility date |
| Evidence commit | `0226e2b` — the record above |
| Deploy run | **`32372116318`-series: run for `0226e2b` completed `success` 2026-08-20T13:18:19Z** (the content in `5f411a1` reached production through it) |

## Live verification — all four changed surfaces

| Change | Live result |
|---|---|
| `gallery.html` noindex (F-5) | `/gallery/` serves `<meta name="robots" content="noindex, nofollow">`; `sitemap.xml` contains **0** `/gallery/` entries |
| `Organization.sameAs` (F-3) | homepage JSON-LD serves `["https://bsky.app/profile/cripminds.bsky.social", "https://www.tumblr.com/cripminds"]` |
| accessibility date (F-1) | `/accessibility/` serves "Last updated: August 12, 2026. Standards: WCAG 2.1 AA" |
| `_config.yml` `feed:` removal (S-6) | see regression check below |

## Feed regression check — the one real risk in Batch 2

Removing the `feed:` block while leaving `jekyll-feed` in `plugins:` could in
principle have let the plugin start generating a competing feed. **It did not.**

| Feed | HTTP | `<item>` count | First item |
|---|---|---|---|
| `/feed.xml` | 200 | **10** | Reached by Boat or Plane |
| `/feed/maya-flux.xml` | 200 | 20 | One in Twelve, and No Surprises |
| `/feed/pixel-nova.xml` | 200 | 20 | Twenty Minutes When the Courtyard Disapp… |
| `/feed/siri-sage.xml` | 200 | 20 | Reached by Boat or Plane |
| `/feed/zen-circuit.xml` | 200 | 20 | Jebel Irhoud Broke the Single Dot I Was… |

`/feed.xml` still serves the hand-authored **RSS 2.0** document with the
`dc:` namespace and its hardcoded `limit:10` — jekyll-feed emits Atom, so the
served output confirms the hand-written template still wins. All five feeds
retained their pre-change item counts. **No regression.**

## Accessibility date — evidence re-verified independently

This is the only Batch-2 change that could have manufactured freshness, so the
justification was re-checked from scratch rather than taken from the record.

`e4746db` ("site: align public metadata and persona framing", **2026-08-12**)
substantively changed what `accessibility.html` itself promises: it removed a
concrete service-level claim — the "Acknowledge: within 24 hours / Critical
fixes: within 48 hours" list and the "I'll respond within 48 hours" line — and
replaced both with impact-based, non-time-bound wording. `git log` confirms it
is also the most recent commit touching the file before Batch 2.

A page's "Last updated" line exists to track exactly that kind of change, so
**August 12, 2026 is the accurate date and the bump is evidence-backed, not
manufactured.** Note the original OD-3 question asked only about the
2026-08-05 design-scorecard audit, which indeed changed nothing on this page;
the bump rests on `e4746db` instead.

## Propagation integrity — independently re-verified, PASS

Bounded to the retitled Swan Care article (the case that originally exposed
stale representation):

- canonical frontmatter title: "Winning the Case Does Not Turn Off the Clock"
- article page `<title>`, `og:title`, and JSON-LD `headline`: **all three carry
  the new title**
- old title ("…the appeal is the mechanism"): **0 hits** across `/`,
  `/research/`, `/feed.xml`, `/sitemap.xml`, and the article page body
- `/research/` index: new title present; `/feed/maya-flux.xml`: present

Absence from `/feed.xml` and `/` is correct, not stale — a June article falls
outside the canonical feed's 10-item window and the homepage's recent-posts
loop. **PASS.**

## Owner-decision status reconciliation

Two entries in `OWNER-DECISIONS.md` still read "Decision needed" although
Batch 2 resolved them. Their status lines are corrected there; recorded here so
the two documents agree:

- **OD-3** (accessibility date) → **DONE**, bumped to 2026-08-12 on `e4746db` evidence.
- **OD-4** (robots.txt lines for `/style-lab/`, `/realistic-scenes/`) → **DONE — NO CHANGE, intentional.** `84c96a2` ("site: keep visual working methods private") deliberately shelved both pages; the disallow lines are defense-in-depth against accidental re-publish, matching the Batch-1 pattern. Not dead code.

## Final Batch-2 disposition table

| ID | Surface | Priority | Disposition |
|---|---|---|---|
| **F-5** | `gallery.html` | P3 | **CLOSED** — `noindex: true`, live-verified |
| **F-3** | `_layouts/default.html` JSON-LD | P3 | **CLOSED** — Tumblr in `sameAs`, live-verified |
| **S-6** | `_config.yml` / `feed.xml` | P3 | **CLOSED** — inert config removed, no feed regression |
| **F-1 / OD-3** | `accessibility.html` | P3 | **CLOSED** — date bumped on verified evidence |
| **OD-4** | `robots.txt` | P4 | **NO CHANGE — VERIFIED CORRECT** (defense-in-depth) |
| **S-5** | five feeds | — | **NO CHANGE — VERIFIED CORRECT** (0 representation failures) |
| **S-4** | `/research/` claim | — | **NO CHANGE — VERIFIED CORRECT** |
| Propagation | corrected articles' cards/JSON-LD/OG/feeds | — | **PASS** |
| **F-2 / OD-2** | Tumblr profile bio (off-repo) | P2 | **MANUAL FOLLOW-UP** — owner must edit Tumblr; replacement copy drafted above |
| **S-7** | four persona feeds | P3 | **CLOSED — `KEEP_AS_DIRECT_URL`** per `CLOSEOUT-2026-08-20.md`, which supersedes the earlier deferred OWNER_DECISION: keep generating, add no nav links, add no autodiscovery, do not retire |
| **F-4 / OD-5** | `/notes/` discoverability | P4 | **OWNER_DECISION** — still open, canonically a Batch-3 item; not a Batch-2 blocker |

**BATCH 2: COMPLETE.** Every canonical Batch-2 finding has a final
disposition. Zero P0, zero P1, zero actionable P2/P3 code or content changes
remain in scope.

Not started, deliberately: Batch 3 (positioning), LC1 corpus remediation,
private-research migration (OD-7 Option 2), local-`main` reconciliation.
`automation/`, `_posts/`, `calibration/`, `reader-lab/` and Phase-2 capture were
not touched by Batch 2 or by this verification pass.
