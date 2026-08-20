# Architecture & Trust/Provenance Findings — Static Surface

Axes C (narrative/positioning) and D (trust/provenance) from the audit
directive, cross-checked against the canonical state in `.claude/WORK.md` §5 of
the audit spec:

- SOFA METHOD = canonical (editorial doctrine)
- Article Form = transfer-validated, **not yet production deployed**
- Writer Grounding = shadow-calibrated / migration-stage
- legacy production = still live during migration
- daily generation != daily publication
- publication selector ≈ every two days / odd-day cron
- legacy corpus != retrospectively validated by current engine
- new engine public cutover = **not yet complete**

## Result: no static page misrepresents this state

Every page that touches methodology (`about.html` §"How These Articles Are
Made," all three `press/*` pages, `_layouts/author.html`'s persona bios) already
uses careful, hedged, non-overclaiming language:

- "A fuller version of the Mind Engine... is still in development."
- "That fuller architecture is not presented here as finished production."
- "Current production includes automated research, drafting, checking, and
  editorial selection." (present tense, accurate — this is what's actually live)
- No page names Sofa Method, Article Form, Writer Grounding, CJ-1/CJ-2, or any
  other internal engineering codename — the public copy stays at the level of
  "the Mind Engine," described consistently as private-mechanics/public-purpose
  across all three press pages.
- No page claims historical articles were produced by a "new" or "fuller"
  engine, or retroactively validated by anything not yet built.

This is a **KEEP** finding for the entire positioning/provenance layer of the
public-facing prose. It reads as though it was deliberately reconciled against
the same canonical state this audit is checking against — likely the
2026-08-09/10 "documentation-debt closure" pass referenced in project memory,
which specifically softened an earlier overclaim on `press/how-it-works/`.

---

## T-1. Reader Lab calibration methodology is live, unrestricted, and partly search-engine-declared on the public production domain

- **What's public-facing vs. what's actually there**: Every page above tells
  readers the project's "exact mechanics remain part of the project's private
  working method" / "private editorial system." Separately, and apparently
  unintentionally, `calibration/` — a real internal directory containing Reader
  Lab reviewer-calibration research design (how human reviewers are calibrated to
  judge AI-generated candidate article material: preregistration documents,
  candidate JSON, round-analysis workflow instructions) — is:
  1. **Not** in `_config.yml`'s `exclude:` list (unlike `automation/`, `archive/`,
     `docs/`, `accessibility/`, `reader-lab-worker/`, all of which ARE excluded).
  2. **Not** disallowed in `robots.txt` (unlike `/style-lab/`, `/gallery/`,
     `/realistic-scenes/`, `/archive/`, `/automation/`, `/docs/`, all of which
     ARE disallowed).
  3. Consequently built by Jekyll into real HTML pages for every `.md` file in
     `calibration/workflows/` and `calibration/candidates/README.md`.
  4. **Confirmed live 2026-08-20**: `calibration/workflows/analyze-human-round-v1/`,
     `-v2/`, `prepare-calibration-candidates-v1/`, `prepare-next-round-v1/`,
     `calibration/candidates/`, and `calibration/runner/` all appear as real URLs
     **in the live `sitemap.xml`** — meaning the site is actively telling search
     engines to index this internal methodology, not merely failing to hide it.
  5. **Confirmed live 2026-08-20**: `calibration/research-context/RL-2026-002.json`
     returns HTTP 200 with the real research-context document verbatim (research
     question, methodology, instrumentation notes) at
     `https://cripminds.com/calibration/research-context/RL-2026-002.json`. The
     bare `calibration/` directory index itself 404s (no directory listing), but
     every individual file path is directly fetchable.
  6. `calibration/runner/*.py`, `*.sh`, `*.service` files are also uncovered by
     any exclude rule; whether Jekyll's build actually copies non-convertible
     binary/script files verbatim was not independently re-verified in the local
     `_site/` (which is stale, see note below) — treat as **unconfirmed, check
     live directly** before assuming they are or aren't reachable.

- **Why this matters (trust/provenance, not just hygiene)**: the public pages
  make an explicit, repeated promise that private mechanics stay private and
  that in-development work ("a fuller Mind Engine that can compare different
  ways of seeing... before a persona writes") is described but not exposed. The
  calibration directory is exactly the kind of in-development editorial R&D that
  promise is meant to cover — reviewer calibration for the Reader Lab program,
  not published articles. Its accidental public exposure, actively reinforced by
  sitemap inclusion, is a real gap between the site's stated privacy posture and
  its actual behavior. This is not a case of an old claim going stale — it is a
  live, present-tense contradiction between what the site says and what the site
  does.

- **Note on the local `_site/` directory**: it is **stale** (files dated March
  through August 2026, inconsistent with current source — e.g. it still has a
  `cripminds-how-it-works.html` from March, `cripminds-system-report.html` from
  July, and `disability-ai-collective-about.html` from March, none of which
  match current filenames). It was **not** used as evidence for any finding in
  this audit; all live-state claims here were checked directly against
  production (`cripminds.com`) or the GitHub Actions deploy log, not the local
  build artifact. This is itself worth a one-line cleanup note (delete or
  `.gitignore` the local `_site/`) but is not a public-surface finding since
  `_site/` is not itself served.

- **Evidence**: REPO VERIFIED (`_config.yml` exclude list, `robots.txt`,
  `git ls-files calibration/`) + WEB VERIFIED (live `sitemap.xml` fetch, live
  `calibration/research-context/RL-2026-002.json` fetch, both 2026-08-20).

- **Proposed direction** (not executed — audit only): add `calibration/` to
  `_config.yml`'s `exclude:` list (removes it from future builds) and/or add a
  `Disallow: /calibration/` line to `robots.txt` as an immediate mitigation,
  then decide whether the already-built, already-indexed pages need a
  `noindex`/removal request or a sitemap resubmission once excluded. Whether the
  underlying data should also move out of the Jekyll site root entirely (into
  `automation/` or a non-repo location) is a larger question for the owner,
  since `calibration/runner/` also contains an operational script + systemd
  service file, not just research artifacts.

- **Classification**: UPDATE_TRUST_DISCLOSURE. **Priority P1** — this is a live
  contradiction between the site's explicit public privacy claim and its actual
  public behavior, on internal editorial-R&D material, not merely a stale
  documentation line.

- **STATUS: CLOSED (Batch 1, 2026-08-20).** `calibration/` and `reader-lab/`
  added to `_config.yml`'s `exclude:` list (commit `f7a355d`, pushed directly
  as an isolated fix on top of `origin/main` via a scratch worktree — the
  containing local `main` branch, which had ~35 unrelated unpushed Phase-2/LC1
  commits underneath, was deliberately left untouched rather than pushed).
  `robots.txt` also given `Disallow: /calibration/` and `Disallow: /reader-lab/`
  as defense-in-depth. Live-verified post-deploy 2026-08-20: all 9 previously-
  confirmed calibration URLs plus 3 reader-lab URLs now return 404;
  `sitemap.xml` has zero calibration/reader-lab entries (was showing 6+
  workflow/candidate/runner paths); normal pages unaffected. Full before-state,
  SHA-256 of all 20 source files, and secret-scan result (NONE FOUND) preserved
  in `BATCH1-PRESERVED-STATE.md`. Underlying source files were **not** deleted
  or moved — only excluded from the Jekyll build. Stale search-engine caches of
  the removed URLs may persist temporarily; no external takedown action taken
  (out of scope for this batch).
  **Caveat**: these files remain in git history (multiple commits, dating back
  at least to `ffe44fb` for the reader-lab control-plane work) even though
  they're no longer in the public *build*. "Not publicly built" ≠ "scrubbed
  from history" — if that distinction matters (e.g. because a real secret were
  ever found, which it was not), history rewriting would be a separate,
  much higher-risk owner decision, not part of this batch.

---

## ADDENDUM to T-1/T-2 (2026-08-20, Batch-1 follow-up): website exposure ≠ repository exposure

Closing the *website* build/serve exposure surfaced a second, distinct
problem that the original T-1/T-2 findings did not separate out: **the
`disability-ai-collective` GitHub repository is public**, and Batch-1's fix
(a Jekyll `exclude:` entry) only stops these files from being *built into the
served site*. It does nothing to the *repository*.

- **PUBLIC REPOSITORY CURRENT-TREE EXPOSURE: YES.** `git ls-tree -r
  origin/main` (as of commit `3242e50`) still lists all 16 calibration/
  reader-lab source files — research-context JSON, candidate JSON,
  preregistration docs, workflow instructions, and the calibration runner
  script + systemd unit — fully readable by anyone via the GitHub web UI,
  `git clone`, or the GitHub API.
- **PUBLIC REPOSITORY HISTORY EXPOSURE: YES.** These paths have been tracked
  since at least `ffe44fb` ("Reader Lab control plane and calibration
  orchestrator"), across 6 total commits touching the paths.
- **No secrets found** in any of these files (confirmed in Batch-1's secret
  scan) — so this is a confidentiality/positioning gap against the site's own
  "editorial mechanics remain private" claim, not a credential-exposure
  incident.
- **This means the "editorial mechanics remain private" claim is currently
  PARTIAL, not TRUE**, even after Batch-1: true for the deployed website,
  false for the source repository backing it.
- Three owner options (keep-public-narrow-the-claim / move-research-private-
  going-forward / history-purge), with consequences, are recorded in
  `OWNER-DECISIONS.md` OD-7. **No history rewrite, force-push, or deletion was
  performed** — this addendum is read-only classification, per directive.

This does not change the STATUS: CLOSED lines above — those refer
specifically to *website* exposure, which is accurate and stays closed. The
repository-level question is tracked separately and remains open.

---

## T-2. `reader-lab/` is empty today but not excluded — a latent version of T-1

- **Correction (2026-08-20, Batch 1)**: this finding's premise was wrong.
  `reader-lab/rounds/drafts/RL-2026-001.json` and `RL-2026-002.json` were
  already tracked in git (commit `ffe44fb`, "Reader Lab control plane and
  calibration orchestrator") and were live-confirmed HTTP 200 at the time
  Batch 1 ran — i.e. this was **not** a latent/preventive-only issue, it was a
  second live instance of T-1's exact failure mode that the original audit
  pass missed (likely because `find reader-lab -type f` was run against a
  stale local checkout, or the files were added between the audit freeze and
  Batch 1). Treated as live and in-scope for Batch 1 regardless. See
  `BATCH1-PRESERVED-STATE.md` for the corrected record.

- **What's there**: `reader-lab/` (distinct from the correctly-excluded
  `reader-lab-worker/`) exists as a directory. It is not in `_config.yml`'s
  `exclude:` list.
- **Why it matters**: if this directory receives Reader Lab content in the
  future (plausible, given the naming parallel to `reader-lab-worker/` and
  `calibration/`), it would repeat Finding T-1 with zero additional review
  unless the exclude list is fixed first.
- **Evidence**: REPO VERIFIED (`find reader-lab -type f` returns nothing;
  `_config.yml` exclude list checked directly).
- **Proposed direction**: add `reader-lab/` to `_config.yml`'s `exclude:` list
  now, pre-emptively, while it's free (zero behavior change today, since it's
  empty).
- **Classification**: UPDATE_ARCHITECTURE_DESCRIPTION (originally scoped as
  preventive; actually closed a live P1-class exposure, see correction above).

- **STATUS: CLOSED BY BUILD EXCLUSION (Batch 1, 2026-08-20).** Same commit and
  verification as T-1 above — `reader-lab/` is in the same `_config.yml`
  exclude entry and `robots.txt` Disallow line as `calibration/`. Both known
  `reader-lab/` URLs live-verified 404 post-deploy.

---

## Non-findings

- No static page anywhere claims or implies that any of the 142-article legacy
  corpus was "retrospectively validated" by a newer engine, nor that current
  safeguards (grounding, fabrication repair, persona-crosscite checks) applied
  historically. The `press/*` pages consistently use present-tense, current-only
  language about what checks exist.
- No page describes production as already running Article Form / Writer
  Grounding / any Sofa-Method-staged pipeline as deployed.
- Persona pages (`_collective/*.md`) correctly avoid persona-owns-topic framing
  and correctly scope Pixel Nova's stronger factual grounding vs. the other three
  personas' constructed status — matches `automation/persona_canon/*.md`
  authority and the `.claude/author-persona-biography-provenance-2026-08-14.md`
  AP1/APE2 safety doctrine (checked by cross-reference, not independently
  re-audited byte-for-byte in this pass).
