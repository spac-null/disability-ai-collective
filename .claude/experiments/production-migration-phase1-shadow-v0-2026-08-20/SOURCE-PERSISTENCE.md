# Source Persistence — the Phase-2 blocker, fixed here

## The blocker

Phase 0 found that **production never persists the fetched source text**.
`article_plans.plan_json` stores `source_hash`, `evidence_packet_hash`,
`source_length_chars`, `source_original_length_chars`, `source_truncated` and
`source_origin` — but not the bytes. `news_seeds` stores only the RSS `summary`. There is no
source-text cache table.

Consequence: for most production articles the exact text the writer saw **cannot be
recovered, only verified** by re-fetching the URL and comparing hashes. If the page has
changed, or the site blocks fetching (a known open problem for Dezeen), the comparison
cannot be made at all. That makes Phase-2 live-vs-shadow comparison unprovable for those
stories.

## The fix, in the shadow architecture

`SOURCE_SNAPSHOT` **must carry the source text itself.** This is enforced by the contract,
not by convention: validation recomputes `sha256(source_text)` and rejects the artifact if it
does not equal the declared `source_sha256`. An artifact carrying only a hash cannot be
constructed.

Every shadow run persists:

| Field | Purpose |
|---|---|
| `source_text` | the exact bytes, in the artifact **and** written out as `source-snapshot.txt` |
| `source_sha256` | recomputed and checked at validation time |
| `provenance.origin` | required — e.g. `frozen_evidence`, later `fetched_article` |
| `provenance.url` | where available |
| `provenance.retrieved` | fetch timestamp where known |
| `provenance.upstream_pdf_sha256` | upstream identifier where the source is a document |
| `provenance.frozen_at` / `frozen_commit` | which committed artefact this came from |
| `words` | convenience count |

The runner also writes `source-snapshot.txt` beside the JSON artifacts, so the bytes are
readable without parsing anything.

## Why this satisfies Phase 2

A future live-vs-shadow comparison must be able to prove production and shadow saw the *same*
frozen source. With text persisted on the shadow side, that proof reduces to comparing the
shadow's `source_sha256` against production's stored `source_hash` for the same story — and
if they match, the shadow copy **is** the recoverable text for both sides.

This already works for the strongest available fixture. FORM-1.3's frozen Edinburgh source
hashes to `fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753`, which is
byte-identical to the `source_hash` recorded in production's `article_plans` row for the
draft `sniff-it-out-follow-your-nose-whatever-your-legs-can`. The shadow run for that fixture
reproduces the same hash, so both sides are provably reading the same bytes.

## Explicitly passive

This is evidence capture only. Nothing here alters production source handling, fetch
behaviour, truncation, or publication. Production continues to store what it always stored;
the shadow simply stores more, in its own run root.

## Recorded for later

Production's own source handling is **not** changed in Phase 1. Whether production should
start persisting source text before the migration completes — which would make historical
fixtures recoverable rather than merely verifiable — is an open owner decision, listed in
`README.md` under blockers before Phase 2.
