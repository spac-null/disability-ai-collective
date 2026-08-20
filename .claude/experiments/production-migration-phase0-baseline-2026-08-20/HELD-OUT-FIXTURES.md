# Held-Out Comparison Fixtures

**No new articles were generated.** These are existing production outputs, identified for
later live-vs-shadow comparison. Selected for material diversity and lineage completeness —
explicitly **not** for which makes production look best. Two of the five are blocked
articles, and one is production's weakest grounding case.

## Critical constraint discovered during this freeze

**The fetched source text is not persisted anywhere in production.**

`article_plans.plan_json` stores `source_hash`, `evidence_packet_hash`,
`source_length_chars`, `source_original_length_chars`, `source_truncated` and
`source_origin` — but **not the source text itself**. `news_seeds` stores only the RSS
`summary`, not the fetched article body. There is no source-text cache table.

Consequence for Phase 2: for most fixtures the exact bytes the writer saw **cannot be
recovered** — only *verified*. A re-fetch can be hashed against the stored `source_hash`; if
the page has changed or is blocked (Dezeen fetching is a known open problem), the fixture
cannot support a byte-exact comparison.

**This is a Phase-2 blocker, not a Phase-0 failure.** Mitigations, for owner decision:
1. Freeze source text at generation time going forward, as Test 2 did.
2. Accept hash-verified-or-flagged fixtures, and mark any whose re-fetch does not match.
3. Prefer fixtures whose source text is already frozen elsewhere in the repo.

Option 3 is available for the single most valuable fixture — see F1.

## The five fixtures

### F1 — `sniff-it-out-follow-your-nose-whatever-your-legs-can` ★ highest value

| Field | Value |
|---|---|
| Date / author | 2026-08-16 / Maya Flux |
| Source | Guardian, *Edinburgh art festival review*, 2026-08-14 |
| `source_hash` | `fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753` |
| `evidence_packet_hash` | `3bef4a7324bb6c9e703bfdc499c7d3460f5a9f1dbdc24cdcbe759ea7062a71e9` |
| source length | 8,629 chars, not truncated |
| grounding | `validated_with_rejections` — one rejection: `correction_moment` named_person 'Sandra George' not found within its own source_excerpt |
| status / words | verified / 2,445 |

| Lineage | |
|---|---|
| source available? | **YES — and already frozen in-repo.** `source_hash` `fee0a03b…` is byte-identical to the source snapshot preserved in `.claude/experiments/sofa-real-ab-1-2026-08-18/iterations/FORM-1.3/` (recorded there as source `fee0a03b`) |
| commission/brief available? | YES — `article_plans` |
| production prompt available? | NO (not stored; reconstructable from code + frozen source) |
| production article available? | YES — `_drafts/2026-08-16-…md` |
| grounding/provenance available? | YES — plan JSON + `_reviews/` sidecar |
| **usable as fixture?** | **YES — the strongest available** |

**Why it matters:** production ran the legacy path on *exactly the source Edinburgh/FORM-1.3
was calibrated on*, byte-identical. This gives a direct legacy-vs-Article-Form comparison on
identical input, with both sides already preserved. Nothing else in the corpus offers that.

### F2 — `what-the-word-modular-quietly-removes`

| Field | Value |
|---|---|
| Date / author | 2026-08-13 / Pixel Nova |
| Source | Dezeen, modular housing / UCLA |
| `source_hash` | `9fd1a11e441e4983e722031f9406916bd895b298b70256bf21c5a45c5ac52f5a` |
| source length | 3,000 chars, **truncated** |
| grounding | `validated_with_rejections` — `correction_moment` direct_quote not in quotation marks |
| status / words | verified / 1,163 |
| source available? | **AT RISK** — Dezeen full-article fetch is a known open problem |
| **usable as fixture?** | **YES, conditionally** — only if a re-fetch matches `9fd1a11e…` |

Pairs with the 2026-08-14 Zen Circuit draft, which used the **same** `source_hash` — a
free persona-variance control on identical input.

### F3 — `7-000-rooms-with-no-door-for-anyone`

| Field | Value |
|---|---|
| Date / author | 2026-08-17 / Maya Flux |
| Source | Techmeme — Malaysia Q2 GDP, manufacturing and construction growth |
| `source_hash` | `3f76239be8637391cbef35999a41fac3976708558870697d9051fbaf7ff15800` |
| `evidence_packet_hash` | `e8474d8f3576374bd237cbf4db9b0659b9ac4ea271fd356e8bf004411e2d4cc9` |
| source length | 9,656 chars, not truncated |
| grounding | `validated`, no violations; `source_decision=commission` |
| status / words | **blocked** — `persona_biography_unresolved` / 1,556 |
| **usable as fixture?** | **YES** |

Materially different: statistical/economic material. Also the only fixture with an explicit
`source_decision=commission` recorded, and it exercises the persona-biography fail-closed path.

### F4 — `galaxy-h1-was-already-sorted-before-it-had-a-shape`

| Field | Value |
|---|---|
| Date / author | 2026-08-17 / Pixel Nova |
| Source | The Verge — Samsung Galaxy H1 over-ear headphones |
| `source_hash` | `772b98c733e173333674103acc11bd93619532c189b39604b04894e44c399a4d` |
| source length | 1,434 chars, not truncated — the thinnest source in the set |
| grounding | `validated`, no violations |
| status / words | **blocked** — `gate_llm`, `persona_biography_unresolved` / 1,776 |
| **usable as fixture?** | **YES** |

Technology/product material, and the only fixture exercising `gate_llm` degradation. A
1,434-char source producing a 1,776-word article is a useful stress case for grounding.

### F5 — `surovell-built-a-box-warren-tested-it-for-access-and`

| Field | Value |
|---|---|
| Date / author | 2026-08-20 / Siri Sage |
| Source | Daily Nous — *Two Argument Mapping Tools (guest post)* |
| `source_hash` | **none — no `article_plans` row exists** |
| status / words | **blocked** — `fable_brief` / 2,140 |
| commission/brief available? | **NO** — the brief degraded, so nothing was persisted |
| **usable as fixture?** | **YES, but only as a degraded-path case** |

Included deliberately: it is the newest output, and it is the one case where the brief itself
failed. Any migration that changes brief behaviour must be checked against it. It cannot
support packet-level comparison.

## Summary

| Fixture | Source recoverable | Brief | Article | Grounding | Usable |
|---|---|---|---|---|---|
| F1 sniff-it-out | **YES, frozen in-repo** | YES | YES | YES | **YES ★** |
| F2 what-the-word-modular | at risk (Dezeen) | YES | YES | YES | conditional |
| F3 7-000-rooms | re-fetch + verify | YES | YES | YES | YES |
| F4 galaxy-h1 | re-fetch + verify | YES | YES | YES | YES |
| F5 surovell | re-fetch + verify | **NO** | YES | partial | degraded-path only |

Diversity check: 4 personas, 5 source domains (arts review, architecture, macroeconomics,
consumer technology, philosophy pedagogy), 3 verified / 4 blocked across the wider draft set,
source lengths 1,434–9,656 chars, article lengths 1,163–2,445 words, and two truncated sources.
