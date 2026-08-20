# Owner Decisions Required — Static Site Integrity Audit

Isolated per the audit directive (§7, `OWNER_DECISION` disposition). Nothing
below has been acted on. Ordered by priority.

## OD-1 (ties to T-1, P1). Calibration research directory: exclude from build now, decide on already-indexed pages

**Status: (a) DONE 2026-08-20** — `calibration/` and `reader-lab/` added to
`_config.yml` `exclude:` and `robots.txt Disallow:`. Deployed and live-verified
non-200 on all 12 previously-exposed URLs. See Batch-1 containment commits
`f7a355d` / `3242e50` on `origin/main`, and `BATCH1-PRESERVED-STATE.md` in
this directory for the pre-fix snapshot.

**(b) still open** — active search-engine removal request for the previously
sitemap-listed `calibration/workflows/*` pages was explicitly out of scope for
this task ("no broad external takedown/removal"); revisit separately if
desired.

**(c) superseded by OD-7 below** — the website-level question ("should this be
built/served") is closed. Whether the data belongs in *this public repository
at all* (vs. relocated to a private repo) is now tracked as its own decision,
OD-7, because website exposure and repository exposure turned out to be two
different problems — see `ARCHITECTURE-AND-TRUST-FINDINGS.md` update below.

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

**Status: DONE 2026-08-20** — corrected finding: `reader-lab/` was not
actually empty/unexposed at containment time (`RL-2026-001.json` was live at
HTTP 200, same failure as calibration/). Closed by the same Batch-1 exclusion
as OD-1(a).

## OD-7 (new, P1). Public GitHub repository exposure — separate from website exposure

**Context**: Batch-1 closed *website* exposure (calibration/reader-lab are no
longer built or served by `cripminds.com`). It did **not** close *repository*
exposure. `disability-ai-collective` is a public GitHub repo. As of
`origin/main` (commit `3242e50`), `git ls-tree -r origin/main` still lists 16
tracked files under `calibration/` and `reader-lab/` — the underlying research
content (preregistration docs, candidate JSON, workflow instructions, the
calibration runner script + systemd unit) is still readable by anyone via the
GitHub web UI, `git clone`, or the GitHub API. It has been tracked since at
least commit `ffe44fb` ("Reader Lab control plane and calibration
orchestrator"). No secrets/credentials were found in these files (confirmed
during Batch-1 secret scan) — this is a confidentiality/positioning problem
("editorial mechanics remain private"), not a credential-exposure incident.

**PUBLIC REPOSITORY CURRENT-TREE EXPOSURE: YES**
**PUBLIC REPOSITORY HISTORY EXPOSURE: YES** (trivially — current tree is also
reachable through history; first-introduced in `ffe44fb`, `79649bd`, and later
touched in 4 more commits, 6 total).

**Status: DECIDED 2026-08-20 — Option 2 chosen.** Going forward, internal
research/calibration material (calibration/, Reader Lab, raw experiment
evidence, preregistration/workflow artifacts, the calibration runner) should
not continue accumulating in this public repository. **No migration was
performed in this task** — no repository created, no history moved, no
history rewritten, no force-push. This decision only updates public wording
(see below) and records the boundary for future work. Migrating the actual
research destination is a separate, later, controlled task.

Recorded status:
- WEBSITE EXPOSURE: CLOSED
- ONGOING FUTURE RESEARCH EXPOSURE: must stop before new research material
  accumulates in this repo — a private research destination is needed before
  that happens (see `ROADMAP-PRIVATE-RESEARCH.md` in this directory)
- HISTORICAL PUBLIC-GIT EXPOSURE: ACCEPTED / DISCLOSED, NOT PURGED (Option 3
  rejected as disproportionate — no credentials were found)

Public wording was corrected accordingly on 2026-08-20 (see content commit) —
no page now claims editorial mechanics have "always remained private"; pages
instead say the mechanics are "not part of the public write-up" (present
tense, no historical guarantee), and `press/system-report/index.html`'s
"Currently in development" section explicitly discloses that R&D material
behind the fuller architecture has previously existed in the public repo.

Three realistic options were recorded before the decision (kept below for
the record):

- **Option 1 — Keep public repo, narrow the public claim.** Change any
  on-site or off-site statement that editorial mechanics "remain private" to
  a truthful, narrower statement (e.g., "the published article and its
  sourcing are what we stand behind; draft-stage calibration research is not
  currently kept private"). Lowest effort, no data movement. Consequence: it
  is an honest downgrade of a trust claim, not a technical fix — the content
  stays exactly as exposed as it is today, indefinitely.
- **Option 2 — Move calibration/Reader Lab research to a private repository
  going forward.** Stop adding new calibration/reader-lab commits to the
  public repo; relocate the live workflow (runner, workflows/, future rounds)
  to a private repo or private storage. Historical Git exposure in the
  current public repo remains (already-cloned copies, GitHub's own caches,
  any forks). Consequence: closes the *ongoing* leak, does not undo the
  *historical* one; still requires Option-1-style honest wording for the
  historical period, or an explicit "as of [date], research work moved
  private" note.
- **Option 3 — Option 2 plus a Git-history purge/replacement of the public
  history.** Only relevant if actual confidentiality (not just tidiness)
  requires retroactively removing these paths from every reachable commit —
  e.g. via `git filter-repo` + a coordinated force-push, or a fresh
  history-less public mirror. Consequence is severe and irreversible in the
  ordinary sense: rewrites public commit SHAs, breaks any existing forks/
  clones/PRs referencing old history, requires force-push (this repo's own
  git-safety rules prohibit that without explicit, scoped authorization), and
  does not remove copies already cloned or cached by GitHub/search engines/
  third parties before the purge. Because no credentials were found, this
  audit does **not** recommend Option 3 as proportionate, but records it as
  a real option since the owner may weigh confidentiality (not just secrecy
  of secrets) differently.

**No history rewrite, no force-push, no deletion performed in this task**, per
directive. This decision blocks marking the "editorial mechanics remain
private" claim fully true again.

## OD-8 (new, from seven-surface supplement). Canonical contact address

**Status: RESOLVED 2026-08-20 — routing policy, not a single mailbox.**
`jascha@cripminds.com` = general/owner/project contact. `editor@cripminds.com`
= editorial questions, factual corrections, corrections requests.
`email@jaschablume.nl` = retired from all public CripMinds-surface
presentation (the mailbox itself was not touched, only its public listing).

Applied: `llms.txt`'s Contact section (previously `email@jaschablume.nl`) now
reads `jascha@cripminds.com`. On inspection, `about.html` (`editor@`),
`jascha.html`, `accessibility.html`, and `press/index.html` (all `jascha@`)
already matched this routing correctly — no change needed there.
`email@jaschablume.nl` had exactly one public-surface occurrence
(`llms.txt`); confirmed zero remaining after the fix via repo-wide grep of
the non-article static surface.
