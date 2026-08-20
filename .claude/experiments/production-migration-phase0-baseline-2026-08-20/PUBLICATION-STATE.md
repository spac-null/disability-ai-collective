# Publication / Content Baseline

Captured from the production checkout at HEAD `8af3622`, 2026-08-20.
**No content was modified. Nothing was published.**

## Content counts (production checkout)

| Directory | Count |
|---|---|
| `_posts/*.md` (published) | **142** |
| `_drafts/*.md` (generated, unpromoted) | **7** |
| `_reviews/*.md` (review sidecars) | **138** |
| `_social/*.json` | **131** |

## Latest published

| | |
|---|---|
| Most recent post | `_posts/2026-08-11-reached-by-boat-or-plane.md` |
| Days since last publication | **9** (as of 2026-08-20) |

Five most recent posts, in filename order:

```
_posts/2026-08-07-a-stack-of-colours-has-not-made-a-single-sound-yet.md
_posts/2026-08-07-one-in-twelve-and-no-surprises.md
_posts/2026-08-07-twenty-minutes-when-the-courtyard-disappeared.md
_posts/2026-08-08-jebel-irhoud-broke-the-single-dot-i-was-trusting.md
_posts/2026-08-11-reached-by-boat-or-plane.md
```

## Latest production output

The most recent generation is `_drafts/2026-08-20-surovell-built-a-box-warren-tested-it-for-access-and.md`,
committed as `8af3622` and pushed to origin by the production host. Generation ran at
09:00 on 2026-08-20 as scheduled.

Its log line records the angle as argument mapping and neurodivergent epistemology; it is
`fact_check_status: blocked`, `pipeline_degraded: [fable_brief]`.

## Draft queue — full state

| Draft | Author | Status | Degraded stages | Words |
|---|---|---|---|---|
| 2026-08-13 what-the-word-modular-quietly-removes | Pixel Nova | verified | — | 1,163 |
| 2026-08-14 modular-means-it-comes-apart-the-same-way-every-time | Zen Circuit | verified | — | 567 |
| 2026-08-15 hand-hammered-edge-and-nobody-asked-what-it-sounds | Siri Sage | **blocked** | — | 668 |
| 2026-08-16 sniff-it-out-follow-your-nose-whatever-your-legs-can | Maya Flux | verified | — | 2,445 |
| 2026-08-17 7-000-rooms-with-no-door-for-anyone | Maya Flux | **blocked** | `persona_biography_unresolved` | 1,556 |
| 2026-08-17 galaxy-h1-was-already-sorted-before-it-had-a-shape | Pixel Nova | **blocked** | `gate_llm`, `persona_biography_unresolved` | 1,776 |
| 2026-08-20 surovell-built-a-box-warren-tested-it-for-access-and | Siri Sage | **blocked** | `fable_brief` | 2,140 |

**4 of 7 blocked.** See `KNOWN-DEFECTS.md` D9 — this stall is part of the baseline, not
something Phase 0 corrected.

Note on length: the legacy path's own outputs range 567–2,445 words. Test 2's 1,587-word
result sits inside that range, which is useful context for the deferred length question —
long outputs are not new behaviour introduced by the new architecture.

## Live database state

### `disability_findings.db`

| Table | Rows |
|---|---|
| `news_seeds` | 1,274 |
| `findings` | 1,430 |
| `article_beats` | 145 |
| `link_pool` | 22,147 |
| `citation_ledger` | 13 |
| `category_jump_shadow` | present |

- `news_seeds` with `used=1`: **99**
- Latest `fetched_date`: **2026-08-20** (the news cron ran this morning)

### `engagement.db`

| Table | Rows |
|---|---|
| `article_plans` | **8** |
| `review_signals` | **11** |
| `engagement_metrics` | present |

`article_plans` holds the persisted Fable brief per article — the lineage a live-vs-shadow
comparison depends on. Only 8 rows exist, covering 2026-08-11 to 2026-08-17. The 2026-08-20
article has **no plan row**, consistent with its `fable_brief` degradation: the brief failed,
so nothing was persisted.

## What this baseline is for

If, after migration, published counts jump or collapse, drafts stop being blocked, or
`article_plans` stops being written, the change can be attributed by comparison against
these numbers rather than reconstructed from memory.
