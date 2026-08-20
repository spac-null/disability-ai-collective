# Phase-1 Golden Replay — Result

Run in `REPLAY` mode. **No model call, no network, no production state touched.**
Full console output: `runs/REPLAY-OUTPUT.txt`.

## Fixture 1 — Real Article Test 2 (Staniforth Road) — **PASS**

| Requirement | Result |
|---|---|
| source snapshot hash matches frozen source | ✔ `be381bbc157f967ea11c46817616d91567394dbfb5801b08898ca1fa46466c6c` — identical to the Test-2 frozen source |
| Discovery artifact preserved | ✔ `ab3a7a87cbed3842…` |
| Article Form artifact preserved | ✔ `f6c9bb66143c5d45…` |
| writer-input prompt/hash preserved | ✔ `043ba338e7c95808…`; underlying prompt is the frozen `60b1d54e…` |
| writer-output hash preserved | ✔ `976f691349436d5c…`; underlying article is the frozen `2efae22e…` |
| Writer Grounding handoff preserved | ✔ `82f31ae3a4ff868d…`, consuming `writer_output` + `source` only |
| final patched/output artifact preserved | ✔ `GROUNDING_REPAIR` `82e6f0cfb56d1842…`, 2 patches, patch-only |
| SHADOW decision deterministically produced | ✔ `067ff23ef373133e…` → **ACCEPT** |
| no production state touched | ✔ |

Source: 10,970 words, persisted as text, not just hashed.

**Decision: ACCEPT.** Reasons: writer output present and provider ok · grounding settled ·
2 `TRUE_UNSUPPORTED` findings, all repaired patch-only · 1 `TRUE_UNCERTAIN`, explicitly
adjudicated · repair verified 0 residual / 0 introduced / 0 unrelated edits.

**One complete article lineage carried end-to-end through the new contracts.** That is the
Phase-1 objective.

## Fixture 2 — FORM-1.3 (Edinburgh) — **PASS (HOLD, correctly)**

Run only after Test 2 succeeded, as instructed.

| Requirement | Result |
|---|---|
| source snapshot hash matches frozen source | ✔ `fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753` |
| all required stages emitted | ✔ (`GROUNDING_REPAIR` absent — none was ever performed) |
| decision deterministic | ✔ `b9f6d3d04880d5f8…` → **HOLD** |

**Decision: HOLD** — 2 unresolved `TRUE_UNSUPPORTED` findings (C1, C2), drawn from that
experiment's own frozen grounding audit (`status: FAIL`, `unsupported_count: 2`).

This fixture matters because it exercises the **HOLD** path. A decision contract that only
ever accepts proves nothing. It also confirms the contracts accept a fixture that predates
them: FORM-1.3 has no standalone Discovery document, so that payload is derived from its own
frozen Form specification and marked `provenance.origin: derived_from_frozen_form_spec` — the
artifact never claims more than the evidence supports.

Its source hash is additionally the one that is **byte-identical to production's**
`article_plans.source_hash` for the draft `sniff-it-out-follow-your-nose-whatever-your-legs-can`,
which is what makes a future live-vs-shadow comparison provable for that story.

## Determinism

Two independent replays of Test 2 produce identical content hashes for all eight stages.
Guaranteed by `created_at` being injected rather than clock-read; asserted by
`test_determinism`.

## Two implementation bugs found and fixed inside this task

Both were caught by running the thing, and are exactly the class the brief permits fixing:

1. **Repo-root resolution was off by one** — `parents[4]` resolved to `.claude/` rather than
   the repository root, so every fixture path was wrong. Fixed to `parents[5]` with an
   assertion that fails loudly rather than silently mis-resolving.
2. **The replay entry point forced the mode**, passing `mode=MODE_REPLAY` explicitly and so
   bypassing `SHADOW_V0_MODE`. That defeated the default-OFF guarantee through the only
   executable entry point. Fixed: `replay.py` now reads the flag, and OFF genuinely refuses.

A third issue was found in the safety tests themselves: the "no `_posts`/`_drafts` reference"
check scanned raw file text and failed on those words appearing inside `runner.py`'s own
safety docstring. The test was tightened to scan **executable code only** — identifiers,
imports and non-docstring string literals, via AST — so it asserts what the code does rather
than what its prose says.
