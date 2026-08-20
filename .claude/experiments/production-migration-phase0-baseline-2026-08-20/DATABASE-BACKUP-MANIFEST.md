# Database Backup Manifest

**Requirement:** a migration-relevant live SQLite database must have a verified safe backup,
taken with SQLite's own backup mechanism — never a naïve `cp`.

**Result: all 5 databases backed up safely. All 5 verified `integrity_check: ok`.**

Machine-readable copy: `db-backup-manifest.json`.

## Method

SQLite's online backup API — `sqlite3.Connection.backup()` — reading each source through a
read-only URI (`file:…?mode=ro`). No file copy, no `cp`, no `rsync`. Each backup was then
opened independently and `PRAGMA integrity_check` run against the **copy**, and a SHA-256
taken of the resulting file.

Backup root: `/srv/backups/cripminds-phase0-baseline/` — deliberately **separate** from the
daily rotation directory (see "Retention" below).

Timestamp (all five): `2026-08-20T07:31:59.935624+00:00`

## Manifest

| DB | Source path | Source bytes | Journal mode | Tables | Backup bytes | integrity | SHA-256 |
|---|---|---|---|---|---|---|---|
| **disability_findings.db** | `…/disability-ai-collective/disability_findings.db` | 14,942,208 | delete | 7 | 14,942,208 | **ok** | `ad83572c3104f461ccb71ba8b61ab7df6cb6eb34e79b00b7b7a127626bd63f09` |
| **engagement.db** | `…/automation/engagement.db` | 1,130,496 | delete | 4 | 1,130,496 | **ok** | `c7a45c167a55ad93faa14ef5c55cf969d173dba5bf71cfea246e3620f9fa0ac8` |
| rss_disability_findings.db | `…/rss_disability_findings.db` | 5,693,440 | delete | 4 | 5,693,440 | **ok** | `ee68802c2146e24d01b1a25045252c907a0bf433943e94b0d40331f88fb5d681` |
| automation/disability_findings.db | `…/automation/disability_findings.db` | 1,785,856 | delete | 1 | 1,785,856 | **ok** | `50c41336cec922c67b1e4a04e8ec6a160d8132205b7357221ae69a72cfbabc90` |
| automation/link_pool.db | `…/automation/link_pool.db` | 0 | delete | 0 | 4,096 | **ok** | `ac7fbf4732ec6b1a11c3af81cea48005c158e39d9043800a4d7895506a32b5b5` |

Page size is 4,096 for all five.

## Migration relevance

| DB | Relevance | Reason |
|---|---|---|
| `disability_findings.db` | **MIGRATION-RELEVANT** | The live pipeline's state: `news_seeds` (1,274 rows, incl. Story Rejection decline records), `findings` (1,430), `article_beats` (145), `link_pool` (22,147), `citation_ledger` (13), `category_jump_shadow`. Written every run. |
| `engagement.db` | **MIGRATION-RELEVANT** | `article_plans` (8 rows — the persisted Fable briefs), `review_signals` (11), `engagement_metrics`. This is the lineage a live-vs-shadow comparison reads. |
| `rss_disability_findings.db` | not relevant | Stale since 2026-05-02. Backed up anyway — cheap. |
| `automation/disability_findings.db` | not relevant | Stale since 2026-05-02, superseded by the root-level DB. |
| `automation/link_pool.db` | not relevant | 0 bytes, never populated. |

## Pre-existing daily backup — correction to prior documentation

A prior note carried in `PROJECT-MAP.md` and repeated in the migration plan claimed **"no
SQLite-safe backup exists yet (open risk)."** That is **false** and is corrected here.

`automation/backup_state_dbs.py` has run daily at 03:30 since 2026-08-10, added after the
`engagement.db` clobbering incident. Verified by reading the script and its log:

- uses `Connection.backup()` — its own docstring states *"Uses SQLite's own backup API
  (Connection.backup), not a raw file copy"*
- runs `PRAGMA integrity_check` on each copy and fails loudly if it is not `ok`
- writes to `/srv/backups/cripminds`, **outside the repo**, so no clean/checkout/worktree
  operation can touch it
- retention: 14 days
- covers exactly the two migration-relevant DBs

Today's log lines:

```
OK engagement.db -> engagement-2026-08-20.db (1126400 bytes, integrity_check: ok)
OK disability_findings.db -> disability_findings-2026-08-20.db (14893056 bytes, integrity_check: ok)
```

Eleven daily `engagement` backups and today's `disability_findings` backup are on disk.

## Why a separate Phase-0 baseline was still needed

The daily job's retention is **14 days**, and its cleanup globs `*.db` inside
`/srv/backups/cripminds` — so any baseline left there would be deleted around 2026-09-03,
very likely before the migration completes.

The Phase-0 baseline therefore lives in `/srv/backups/cripminds-phase0-baseline/`, which the
rotation does not touch. It is a fixed rollback point for the whole migration, not a daily
snapshot.

## Residual risk

- **The backups are on the same physical disk as the source** (`/dev/nvme0n1p2`, 85% used,
  18G free). This protects against logical corruption and accidental overwrite — the actual
  2026-08-10 failure mode — but not against disk loss. Offsite backup remains a separate,
  pre-existing open item and is **not** resolved by this task.
- No blockers were encountered. Permissions and credentials were sufficient; no unsafe copy
  was substituted at any point.
