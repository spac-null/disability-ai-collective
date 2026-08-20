# Recommended Cleanup Batches — Static Site Integrity Audit

Per the audit directive: maximum 3 finite batches, proposal only, **no edits
made**. Ordered by dependency and risk (lowest-risk/highest-value first).

## Batch 1 — Exposure containment (P1, needs OD-1 approval first)

Scope: stop the live contradiction between "private working method" and the
calibration directory's actual public exposure.

1. Add `calibration/` to `_config.yml`'s `exclude:` list.
2. Add `Disallow: /calibration/` to `robots.txt` as defense-in-depth (covers the
   window between this deploy and any search-engine re-crawl).
3. Pre-emptively add `reader-lab/` to the same `exclude:` list (OD-6 — free
   while it's empty).
4. Redeploy, then re-check `sitemap.xml` and a direct fetch of
   `calibration/research-context/RL-2026-002.json` to confirm both return
   404/absent post-deploy.
5. Follow up with search-console removal requests for the already-indexed
   `calibration/workflows/*` URLs if OD-1(b) decides that's warranted — separate
   from the repo change itself.

Depends on: OD-1 owner sign-off (this changes what's built/crawlable, not
article content, but it is a real behavior change to the live site).

## Batch 2 — Metadata/consistency hygiene (P3–P4, no owner blocker)

Scope: small, independently-safe frontmatter/template edits, none of which
change reader-facing prose.

1. Add `noindex: true` to `gallery.html` frontmatter (F-5).
2. Add the Tumblr URL to `Organization.sameAs` in `_layouts/default.html` (F-3).
3. Resolve OD-4 (confirm intentional, then optionally trim the two dead
   `robots.txt` lines for `/style-lab/`/`/realistic-scenes/`).

Depends on: nothing blocking — these are safe defaults; only OD-4's disallow-line
removal benefits from an explicit "yes, still shelved" confirmation first.

## Batch 3 — Factual/date verification (P2–P3, requires reading source docs)

Scope: the two findings that need a real diff against another document before
any text changes, not just a template tweak.

1. F-1: diff `.claude/design-scorecard.md`'s actual changes against
   `accessibility.html`'s current claims; bump the "Last updated" date only if
   the audit touched something this page describes.
2. F-2: draft replacement Tumblr bio copy for the owner to paste in directly
   (off-repo action, but this repo can prepare the suggested wording once OD-2
   is decided).
3. OD-5: once decided, either add `/notes/` to the footer "Explore" list (one
   line in `_layouts/default.html`) or explicitly document it as intentionally
   nav-free.

Depends on: OD-2, OD-3, OD-5 decisions from OWNER-DECISIONS.md.

---

**Not batched, explicitly out of scope for this audit**: the 142-article
corpus (separate LC1 workstream, per directive), Phase-2 capture work
(untouched), any production-automation changes (untouched). Nothing in this
plan touches `automation/`, `_posts/`, or any deploy/generation script.
