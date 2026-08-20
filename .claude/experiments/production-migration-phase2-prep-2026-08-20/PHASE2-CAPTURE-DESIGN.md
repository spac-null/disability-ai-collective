# Phase-2 Capture Design

## Why this step exists

Phase 2 must compare legacy production against the clean shadow architecture **on exactly
the same frozen evidence**. Phase 0 found production cannot currently prove that: it stores
`source_hash` and `evidence_packet_hash` but never the bytes, and `news_seeds` holds only the
RSS summary. Re-fetching a URL later is not proof — pages change, and some sites block
fetching outright.

This closes that gap once. It is **observability only**.

## Evidence flow, traced from code before any capture was written

`get_source_text` does not return one object, and "source text" is not one thing. Four
distinct representations exist, and the code permits them to diverge:

| # | Representation | Where |
|---|---|---|
| R1 | **Full cached extraction** — `_source_text_cache[url]`, capped at `_SOURCE_TEXT_CACHE_MAX_CHARS` (20,000) | `discovery.py:1255` |
| R2 | **Returned slice** — `cached[:max_chars]` handed to the caller | `discovery.py` `get_source_text` return |
| R3 | **Post-downgrade packet source** — set to `None` when `source_origin == fallback_summary`, so a real-but-short RSS summary is not granted source-snapshot authority | `generate.py:275`, `:303` |
| R4 | **Evidence packet** — `build_evidence_packet(R3, …)`, threaded unmodified into planner, reviewer and executor | `generate.py:397` |

R1 and R2 are identical today only because both call sites rely on the same 20,000 default.
That is a coincidence of configuration, not an invariant, so all three text forms are
captured separately rather than assumed equal.

Downstream, the writer-visible evidence is the `SOURCE MATERIAL` block interpolated into the
writer prompt at `generate.py:917` from the same `source_text` variable — so capturing the
assembled prompt captures exactly what the writer saw.

## What is captured

| Event | Artifacts |
|---|---|
| `evidence` | R1, R2, R3 as separate files; R4 as JSON; provenance (URL, origin, seed/discovery ids, underlying article URL, original length, max-chars) |
| `commission` | commission input + the Fable brief |
| `writer` | the assembled writer prompt, the **RAW writer output**, provider and model |
| `rewrite` | pre-rewrite and post-rewrite text, plus a `rewrite_changed_content` flag |
| `disposition` | gate result, degraded stages, `_should_block`, review clean flag, fact-check status, final disposition, slug, article file |

### The raw writer output is the critical capture

`raw_content` exists only between `generate.py:1057` and the rewrite a hundred lines later,
where it is reassigned. It is on no disk anywhere today. The target architecture **removes
the whole-document rewrite stage**, so separating what the legacy *writer* produced from what
the legacy *rewriter* changed is the single most informative comparison signal available —
and it is attributable by construction, because nothing else executes between the two
captures.

## Isolation

| Property | Guarantee |
|---|---|
| Default | **OFF** — `SHADOW_CAPTURE` unset means every entry point returns immediately |
| Failure | `capture()` catches `BaseException`, logs, returns. **A capture failure can never alter, block or fail an article run.** This exception is deliberate: capture observes the legacy baseline and is not part of the target ACCEPT/HOLD architecture |
| Writes | append-only, atomic (temp + `os.replace`), under its own root only |
| Databases | no `sqlite3` in executable code |
| Content | no `_posts` or `_drafts` path in executable code |
| Network / subprocess / LLM | none in executable code |
| Mutation | payloads are serialised, never modified |
| Secrets | any artifact containing credential-shaped markers is **refused**, not written; the refusal is recorded in the manifest |

## Patch size

`+52 lines, 0 deletions` in `generate.py` — five one-line hooks, two helper assignments at
the source-acquisition branches, safe defaults, and one import. Plus two new files
(`shadow_capture.py`, `shadow_capture_test.py`) that nothing else imports.

`snapshot_test.py --check` passes unchanged with the capture code present and OFF, which is
the evidence that the legacy prompt-construction path is byte-identical.

## Storage root

`/srv/data/cripminds-shadow-capture/<run-id>/` (override: `SHADOW_CAPTURE_ROOT`).

Chosen against host conventions: outside the repo, outside `_posts/` and `_drafts/`, not in
any SQLite database, not mixed with rotating logs, and **not** under `/srv/backups/cripminds`
where the 14-day DB-backup rotation would delete it.
