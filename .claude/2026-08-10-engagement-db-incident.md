# Incident: `automation/engagement.db` overwritten by rsync, 2026-08-10

## What happened

While building `automation/phase_probe.py` (a dry-run test harness for the
article-quality blueprint), a routine code-sync command overwrote trident's
real, populated `automation/engagement.db` with an empty local stub of the
same file.

**Command that caused it** (run from `~/code/disability-collective-ai` on the
Mac):
```
rsync -az --exclude='.git' /Users/stargatesgx/code/disability-collective-ai/automation/ \
  jascha@trident.tail630536.ts.net:/srv/data/hermes/workspace/disability-ai-collective/automation/
```

**Root cause**: `*.db` is gitignored, so the local machine's copy of
`engagement.db` was never populated by git — it was a leftover 0-byte stub.
`rsync` does not consult `.gitignore`; it synced the entire `automation/`
directory tree verbatim, including that empty file, onto trident. This exact
"sync the whole `automation/` folder" pattern was used multiple times earlier
in the same session for other live tests; `disability_findings.db`'s hash
differs between the two machines, suggesting rsync's default size/mtime
quick-check skipped re-transferring it on those earlier runs (luck, not
protection — see item 7 below for the actual fix).

## Timeline (all times CEST)

- File `birth` time on trident (i.e. when rsync's rename() replaced it):
  **2026-08-10 16:29:16**
- Local stub's preserved mtime (rsync preserves mtimes by default): 12:28:57
  — this is the giveaway that the local, not the remote, version won.

## Forensic facts preserved

- Clobbered file kept, not deleted: renamed to
  `automation/engagement.db.clobbered-20260810` (0 bytes, inode 2383108).
- No open file descriptor found holding the pre-overwrite file (`lsof`,
  no-sudo — sudo requires an interactive password not available over this
  SSH session; a plain `lsof` covering jascha-owned processes found nothing,
  and no python process for this workspace was running at the time of
  investigation).
- No `-wal`/`-shm`/`-journal` side files exist or ever did — the codebase
  uses SQLite's default rollback-journal mode (no `PRAGMA journal_mode=WAL`
  anywhere), which doesn't leave persistent side files between transactions.
- Filesystem: plain ext4 on a single partition (`findmnt`/`lsblk`/`df -T`
  confirmed), no LVM, no btrfs/zfs — no snapshot layer exists.
- One other, unrelated checkout exists
  (`/srv/data/openclaw/workspaces/ops/disability-ai-collective`) but its last
  commit predates `engagement.db`'s existence entirely (May 7, vs. the
  feature that created this file shipping 2026-08-09) — not a viable replica.
- Decision taken: **no raw block-level ext4 undelete attempted.** Given the
  quantified blast radius below, the risk of invasive recovery on trident's
  live, multi-service root filesystem was judged not worth it for the actual
  stakes.

## Table-by-table blast radius

| Table | Contents | Loss |
|---|---|---|
| `engagement_metrics` | GoatCounter/GSC/Bluesky/Mastodon/Tumblr pageview data | **None, functionally.** Refetched fresh daily at 11:00 cron with a rolling 90-day window from external APIs that retain their own history. Re-running the collector recovers current-and-forward data completely. Nuance worth keeping: an exact point-in-time snapshot as it stood *before* the clobber is not reconstructible identically (rolling-window semantics, not immutable historical snapshots — this applies especially to GSC). |
| `review_signals` | Engagement-read verdicts, shadow-check hits, plan-follow-read verdicts per reviewed article | **None** — fully reconstructable. Every one of these is also written as plain text into `_reviews/<slug>-review.md` sidecars, confirmed git-tracked (129 files, entirely untouched by this incident), readable back through 2026-08-09/08-10. |
| `article_plans` | Raw `_fable_editorial_brief` JSON per article, feeding Stage B's plan-follow calibration effort | **At most 2 rows, unrecoverable.** This table only existed ~36 hours (created 2026-08-09, wiped 2026-08-10). Confirmed via `automation.log`: 2026-08-09 09:00 (Zen Circuit brief succeeded) and 2026-08-09 21:22 (Pixel Nova brief succeeded) are the only two real brief-generation events in the table's entire lifetime; the 2026-08-10 article's brief failed to parse and was never persisted (`_persist_article_plan`'s own `if not fable_brief: return` guard). Stage B's own design required ~20 real pairs before calibrating anything — this was 2/20 at most, not a mature dataset. **Decision: accept this loss. Do not fabricate replacement briefs from finished articles** — that is exactly the "infer a plan that wasn't there" error the N7 fix (2026-08-10, same day, see `_plan_follow_read`) was built to eliminate for the *reading* side; doing it on the *writing* side to backfill this table would reintroduce the identical epistemic mistake.

## `disability_findings.db` — separately audited, not part of this incident

Hash differs between the Mac and trident copies, consistent with rsync's
default quick-check skipping a re-transfer rather than any special
protection. [Verified separately post-incident: size/table counts/last-write
timestamps confirmed intact — see the commit that closed this incident for
the exact numbers.]

## Recovery actions taken (see commit history for exact commits)

1. Schema recreated through the application's own initialization code paths
   (not hand-authored SQL) — `_persist_article_plan`, `_persist_review_signals`,
   and `engagement_fetch.py`'s init, exercised once each and any resulting
   placeholder row deleted immediately after, so every column/migration
   (including the `ALTER TABLE ADD COLUMN` migrations already in
   `_persist_review_signals`) is created exactly the way production creates
   it.
2. `review_signals` reconstructed from the 129 git-tracked `_reviews/*.md`
   sidecars via a dedicated, idempotent, `--dry-run`-capable script.
   `plan_follow_read` is rebuilt per the POST-N7-fix invariant (no persisted
   plan → N/A), not by trusting the old sidecar's pre-fix values verbatim —
   the 2026-08-10 sidecar's own plan-follow verdicts are exactly the bogus
   "verified a plan that was never made" output N7 fixed the same day, and
   restoring them as if they were valid evidence would reintroduce the bug
   this incident report is adjacent to.
3. `engagement_metrics` re-fetched via `engagement_fetch.py` (dry-run first,
   confirmed all 5 sources responding, then a real fetch).
4. `article_plans` left empty. Stage B's calibration restarts counting from
   whatever plans get persisted going forward.
5. A timestamped, verified (`PRAGMA integrity_check`) copy of the
   reconstructed DB was taken immediately after reconstruction, before any
   further writes.

## Structural fix — making this class of incident impossible, not just fixed once

**Immediate (done)**: every future code-sync command to trident excludes
mutable state explicitly:
```
--exclude='*.db' --exclude='*.db-wal' --exclude='*.db-shm' --exclude='*.db-journal'
```

**Larger, deliberately NOT done same-day**: move persistent runtime state
(`engagement.db`, `disability_findings.db`, `persona_state/`) out of the
deployable repo tree entirely (e.g. `/srv/data/cripminds-state/`), with paths
supplied via config/environment rather than hardcoded relative to
`repo_root`. This is the real fix — an rsync, git pull, checkout, worktree,
or clean operation becomes physically incapable of touching production data
— but it touches the live daily cron's working assumptions and deserves its
own careful, tested change, not a same-day patch bolted on during incident
recovery. Tracked as its own follow-up, not closed by this incident.

**Also needed, not yet built**: automatic daily SQLite backup of the state
directory (timestamped, retained, `PRAGMA integrity_check`'d, stored outside
the deployable tree) — this incident is the proof these files stopped being
throwaway caches once real accumulation started.

## Closure (commit `4ffb4c9`)

**Recovered:**
- Schema recreated through the application's own `init_db()`/`_persist_article_plan()`/`_persist_review_signals()` code paths, not hand-authored SQL. `PRAGMA integrity_check: ok`.
- `review_signals`: reconstructed for exactly its true lifetime (2 rows, the only 2 sidecars dated on/after 2026-08-09 when this table was introduced) — did not fabricate rows for the 127 older sidecars, which never had a corresponding row in the original table. `plan_follow_read`/`pre_rewrite_plan_follow_read` rebuilt per the post-N7-fix invariant (no persisted plan → deterministic N/A), not by trusting the old sidecars' bogus verdicts verbatim.
- `engagement_metrics`: re-fetched fresh, all 5 sources individually confirmed — GoatCounter 132 rows, GSC 180, Bluesky 132, Mastodon 3, Tumblr correctly recorded as "no distributed posts yet" (0 rows, not a failure — no `tumblr_url` exists on any of the 76 recent articles).
- Reconstructed DB backed up (`/srv/backups/cripminds/engagement-2026-08-10.db`, `PRAGMA integrity_check: ok`, verified row counts match the live DB exactly: 447/2/0).

**Lost:** at most 2 raw `article_plans` JSON rows from 2026-08-09 (Zen Circuit + Pixel Nova briefs). Not reconstructed — doing so from finished articles would fabricate the exact "infer a plan that wasn't there" error the N7 fix eliminated the same day. Stage B's calibration needed ~20 real pairs before being usable at all; this was ≤2/20, far below threshold, not a mature dataset.

**Unaffected:** `disability_findings.db` (independently audited: identical hash before/after every sync this session, `PRAGMA integrity_check: ok`, 880 news_seeds / 1,430 findings / 21,669 link_pool rows, mtime matching the legitimate 09:00 production run). All 129 `_reviews/*.md` sidecars. Git history. External engagement sources themselves (GoatCounter/GSC/Bluesky/Mastodon/Tumblr retain their own history independently).

**Recurrence prevention, done:**
- `automation/sync_to_trident_for_testing.sh` — the safe replacement for the ad hoc rsync that caused this. Hard-excludes `*.db`/`*.db-wal`/`*.db-shm`/`*.db-journal`. Run for real post-recovery; transfer list inspected and confirmed zero database files present.
- `automation/backup_state_dbs.py` — daily backup via SQLite's own backup API, `PRAGMA integrity_check`'d, 14-day retention, written to `/srv/backups/cripminds/` (outside the deployable tree). Wired into trident's crontab at 03:30 daily (`crontab -l`).

**Deliberately deferred, not blocking further work:** moving `engagement.db`/`disability_findings.db` out of the repo checkout entirely (e.g. `/srv/data/cripminds-state/`) is the real long-term fix — an rsync, git pull, checkout, worktree, or clean operation becomes physically incapable of touching production data — but it touches the live daily cron's path assumptions and deserves its own careful, tested change. Tracked as infrastructure hardening, not something today's incident recovery should block on.
