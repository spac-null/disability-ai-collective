# Exposure scope + git-state freeze — 2026-08-20

Read-only record. No remediation performed, no history rewritten, no refs moved.

## 1. Website exposure ≠ repository exposure

Batch 1 closed the **website** exposure. It did not, and could not, close the
**public repository** exposure. These are three separate states and are recorded
separately here so the distinction is not collapsed again later.

| Layer | State | Evidence (verified 2026-08-20, anonymous requests) |
|---|---|---|
| **Public website** | **CLOSED** | `https://cripminds.com/reader-lab/rounds/drafts/RL-2026-001.json` → **404**; `https://cripminds.com/calibration/research-context/RL-2026-002.json` → **404**. Sitemap carries zero `calibration/` or `reader-lab/` entries; `robots.txt` has defensive `Disallow` entries. |
| **Public repo — current tree** | **OPEN** | `spac-null/disability-ai-collective` is **PUBLIC** (`gh repo view` → `"visibility":"PUBLIC"`). `git ls-tree -r origin/main` lists **16** tracked files under `calibration/` (14) and `reader-lab/` (2). Anonymous `raw.githubusercontent.com` fetches of `reader-lab/rounds/drafts/RL-2026-001.json`, `calibration/research-context/RL-2026-002.json` and `calibration/runner/calibration_runner.py` all returned **HTTP 200**. |
| **Public repo — history** | **OPEN** | **6** commits on `origin/main` touch those paths: `ffe44fb`, `c1730e6`, `d5f0d05`, `79649bd`, `c35079e`, `b8051c3`. Even if the current tree were cleared, these remain publicly readable. |

Excluding a directory from the Jekyll build stops it being *served*. It does not
untrack it, and this repo is public — so the calibration/Reader Lab material is
still readable by anyone, just at `github.com` instead of `cripminds.com`.

### Consequence for the public claim — RESOLVED 2026-08-20

The claim that **"editorial mechanics remain private"** was
**PARTIAL / NOT LITERALLY TRUE**: the calibration runner, its workflows, the
pre-registration and candidate files, and both Reader Lab draft rounds are
public in a public repository.

**Owner decision: OPTION 2.** Recorded in `OWNER-DECISIONS.md` OD-7 and
`ROADMAP-PRIVATE-RESEARCH.md`:

- **Historical public-Git exposure: ACCEPTED / DISCLOSED, NOT PURGED.** No
  credentials or secrets were found, so a history rewrite is disproportionate
  and was neither authorized nor attempted.
- **Future research exposure: MUST END.** `calibration/`, Reader Lab, raw
  experiment evidence, internal pre-registration and workflow artifacts move to
  a private research destination. The public repo keeps the site, deployable
  production code, and public documentation. **No migration was performed** —
  that is a separate, later, controlled task, and it must land before material
  internal research continues.
- **Public wording corrected and deployed 2026-08-20** (commit `98ea267`, live
  run `32372116318`). No page now claims the mechanics have *always* been
  private; they read "not part of the public write-up" (present tense, no
  historical guarantee), and `press/system-report/` explicitly discloses that
  R&D material behind the fuller architecture has previously existed in the
  public repository.

The claim is **truthful now** — narrowed to the present tense, with the
historical exposure disclosed rather than denied.

## 2. Git-state freeze (recorded, NOT reconciled)

| | |
|---|---|
| `main` (local research line) | `732c84f9c4273e90516d38afd308b2e358971fb5` |
| `origin/main` (public / deployed authority) | `3242e50cd120d9dcb986335acc9823826f3cf2ed` |
| merge-base | `9f9bf3519457479347113883a591c7cb92bce697` |
| local-only commits | **38** |
| origin-only commits | **6** |

Backup refs **already existed** at the correct values and were left untouched
(not overwritten):

- `backup/research-main-2026-08-20` → `732c84f` (= current local `main`)
- `backup/origin-main-2026-08-20` → `3242e50` (= current `origin/main`)

The 38 local-only commits carry the research/`.claude` evidence lineage. The
three public-content changes on that line were previously verified
**patch-equivalent** to their already-deployed `origin` counterparts, so **no
unique public content needs rescuing** from the research line. Reconciliation is
deliberately **not** performed here: no rebase, reset, merge, cherry-pick or
force-push. Shared local `main` was never checked out or modified by this task.

## 3. Workflow rule (recorded)

**No two agents work directly on shared `main` concurrently.** Going forward:
public/deployable work gets a fresh branch/worktree from current `origin/main`;
research/`.claude` evidence gets its own; one task, one branch/worktree. A
research checkout never pushes public `main`.

This task followed that rule and stayed inside the isolated
`static-audit-completion-2026-08-20` worktree.

## 4. Duplicate supplement — RESOLVED 2026-08-20

Two supplements were produced concurrently for the same seven surfaces. The
owner designated **this one authoritative**:

| | Commit | Fate |
|---|---|---|
| **Authoritative completion** | `0015c53` (landed on `main` by this commit) | integrates all seven surfaces, recalculates every audit deliverable, updates `inventory.json` and the 32→39 surface total, records the exposure split and the git-state freeze |
| **Superseded supplement** | `5ac5c9b` | `SEVEN-SURFACE-SUPPLEMENT.md` — same seven findings, less precise, **no** totals recalculation |

`5ac5c9b` had already been merged to `main` by a peer session before this
landing, so it is permanently in history and was **not** reverted or purged.
Instead `SEVEN-SURFACE-SUPPLEMENT.md` carries a superseded banner pointing here,
so only one document is authoritative. Its taxonomy differed in one place — it
dispositioned persona-feed discoverability as `UPDATE_ARCHITECTURE_DESCRIPTION`
P3 where this audit records a plain P3; the substance is identical.

### Unique material carried forward from `5ac5c9b`

Reviewed file-by-file. Everything about the seven surfaces was duplicate at
lower precision. Three items were genuinely unique and are preserved:

1. **Two local freeze tags exist** (verified present, verified *not* on origin):
   - `freeze-local-research-2026-08-20` → `732c84f`
   - `freeze-origin-public-2026-08-20` → `3242e50`

   **These must never be pushed.** Pushing the research tag would drag the 38
   underlying research commits into the public repo — precisely the exposure
   this track exists to stop. They are local bookmarks only, redundant with the
   `backup/*` branch refs recorded in §2.

2. **The 6 origin-only commits, enumerated:** `3242e50` (Batch-1 evidence),
   `f7a355d` (Batch-1 exclusion fix), `86a91d3` + `70d9292` (Swan Care factual
   cluster), `8af3622` (article published), `11826e4` (draft archival).

3. **Local `732c84f` is the same change as origin's `f7a355d`** — different SHA
   only because it was built on a different parent. This is concrete support for
   the standing "no unique public content on the research line" conclusion.

`5ac5c9b`'s `GIT-STATE-FREEZE-2026-08-20.md` is therefore **kept**, not
superseded: it is the origin of items 1–3.
