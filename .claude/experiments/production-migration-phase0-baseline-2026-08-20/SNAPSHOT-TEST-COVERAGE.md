# snapshot_test.py — Coverage and Gaps

**`snapshot_test.py` was not modified.** It was read and run in `--check` mode only.

## Current state

```
$ python3 automation/snapshot_test.py --check
No drift — 6 article(s) match recorded fixtures.
```

**Passes clean at baseline.** Exit 0.

## What it freezes

| # | Class | Covered |
|---|---|---|
| 1 | **Deterministic checks** | `_readability_score`, `_check_buried_clause_sentences`, `_check_argument_word_overuse`, `_check_sentence_length_distribution`, `_parse_rule_verdicts` — exact-value snapshots over 6 real published articles, plus synthetic verdict cases including the 2026-08-02/06 `[FAIL]`→`[PASS]` reversal bug |
| 2 | **Gate/review LLM call construction** | `_pre_commit_gate`'s `GATE_SYSTEM`, `validate_article`'s `RULES_SYSTEM` and `CITATION_SYSTEM`, plus model / `max_tokens` / `timeout` |
| 3 | **Plan prompt construction** | `_fable_editorial_brief`'s system and user prompts and call parameters (`_snapshot_generate_calls`) |

Discipline: it **never calls the network** — `_call_openai_compat_api`, `_web_verify_quote`
and `_web_verify_claim` are monkeypatched to recorders/stubs, so a byte-for-byte diff of
*what would have been sent* survives any refactor. All writes are redirected into a temp
directory by `_isolate_paths`; it never touches `_posts/`, `_reviews/` or `_drafts/`.

One acknowledged side effect: a few lines are appended to the gitignored `automation.log`,
because the `FileHandler` is bound in `__init__` before any override is possible.

Fixture articles (6): `2026-08-07-one-in-twelve-and-no-surprises`,
`2026-07-31-injected-since-birth`, `2026-07-26-vally-wieselthier…`,
`2026-07-22-fourteen-nodes-on-nicholson-street`, `2026-07-29-weegee-heard-the-body-first`,
`2026-08-07-a-stack-of-colours…`.

Recorded fixtures: `.snapshot_fixtures/deterministic.json` (4,537 B),
`generate_calls.json` (36,826 B), `llm_calls.json` (449,904 B).

## What it does NOT cover — verified by grep

| Production surface | snapshot_test | writer_prompt_test | Covered anywhere? |
|---|---|---|---|
| **`rewrite_with_opus` SYSTEM** (25,019 ch, 47 rules) | 0 refs | 0 refs | **NO — the largest uncovered prompt** |
| assembled writer prompt | 1 incidental ref | 29 refs | yes, by `writer_prompt_test.py` |
| `call_llm_via_openclaw_session` | 0 refs | 6 refs | yes, by `writer_prompt_test.py` |
| `_engagement_read` (4,161 ch) | 0 refs | 0 refs | **NO** |
| `_check_persona_crosscite_accuracy` (1,484 ch) | 0 refs | 0 refs | **NO** |
| `FIX_SYSTEM` register (1,221) / form (421) | 0 refs | 0 refs | **NO** |
| `SUBJECT_SYSTEM` (533 ch) | 0 refs | 0 refs | **NO** |
| `fact_check.py` SYSTEM (905 ch) | 0 refs | 0 refs | **NO** |
| `content_checks.py` link SYSTEM (1,070 ch) | 0 refs | 0 refs | **NO** |
| persona canon payloads | not snapshotted | not snapshotted | **NO** |
| end-to-end article output | out of scope by design | out of scope | **NO** |

The wider suite is 31 `*_test.py` files, including `writer_prompt_test.py`,
`story_rejection_v1_test.py`, `story_rejection_v1_1_test.py`,
`persona_brief_writer_reconciliation_test.py` and `natural_run_health_check.py`.

## Is it reusable for migration regression checks?

**YES — with two named limits.**

**Reusable because:** it is exactly the right shape for a staged migration. It freezes
*constructed prompts* rather than model responses, so it detects unintended prompt changes
deterministically and at zero network cost. Phase 4 deletes three prompt-bearing stages; this
harness is what proves each deletion changed only what was intended.

**Limit 1 — the rewrite stage is invisible to it.** Phase 4 step 1 removes
`rewrite_with_opus`, whose 25,019-character SYSTEM has no snapshot anywhere. That deletion
would be the largest prompt change in the migration and the harness would not register it.
Before deleting, the rewrite SYSTEM should be captured into this Phase-0 evidence root — its
hash is already recorded in `PROMPT-BASELINE.md`
(`921c907645358aa113bb64f324ced7e9c34a6be631685700cd800cdfe10d9db3`), which is sufficient to
prove what was removed.

**Limit 2 — baselines must be re-recorded deliberately, per deletion.** The repo's own rule
is that `--record` is only for a deliberate rule fix, never a refactor. Each Phase-4 commit
that changes a prompt must re-record and state in the commit why the diff is intended.
Re-recording all baselines in one squashed migration commit would destroy the harness's value
at the exact moment it is most needed.

## Gaps recorded, not filled

No test file was written, modified, or re-recorded in Phase 0. The gaps above are inputs to
Phase 1 planning, not work items for this task.
