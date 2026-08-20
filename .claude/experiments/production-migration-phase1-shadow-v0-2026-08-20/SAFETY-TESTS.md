# Safety Tests

`impl/safety_tests.py` — **39 checks across 17 test functions. 39/39 pass.**
Full output: `runs/SAFETY-TEST-OUTPUT.txt`.

Isolation, fail-closed behaviour and stage separation only. **No literary quality tests.**

| Required by brief | Test | Result |
|---|---|---|
| shadow default OFF | `test_default_off` — mode is `OFF` with no env var; `run()` raises `ShadowDisabled` | ✔ |
| no production DB writes | `test_no_db_or_publication_code` — no `sqlite3` in executable code | ✔ |
| no publication path | same — no `subprocess`, no network client | ✔ |
| no `_posts`/`_drafts` writes | same, plus `test_writes_confined_to_run_root` asserts `_posts` mtimes unchanged and that every written file sits under the run root | ✔ |
| source snapshot persisted | `test_source_text_persisted_not_just_hash` — text present, provenance present, hash self-consistent, and equal to the frozen Test-2 source hash | ✔ |
| hash mismatch fails closed | `test_hash_mismatch_fails_closed` | ✔ |
| missing stage artifact fails closed | `test_missing_stage_artifact_holds` (→ HOLD) and `test_missing_required_field_fails_closed` (→ `ContractViolation`) | ✔ |
| grounding unresolved → HOLD | `test_grounding_unresolved_holds` (FORM-1.3) and `test_uncertain_holds_by_default` | ✔ |
| provider failure → HOLD | `test_provider_failure_holds` — and the reason explicitly rejects the legacy template fallback | ✔ |
| legacy prompt markers absent | `test_no_legacy_prompt_surface` — both fixtures clean; contract rejects an injected marker | ✔ |
| Article Form and Writer Grounding remain separate | `test_form_and_grounding_are_separate_stages` | ✔ |

Additional tests beyond the required list:

| Test | Asserts |
|---|---|
| `test_live_shadow_not_executable` | `LIVE_SHADOW` raises `NotImplementedError` — scaffolded, never run |
| `test_lineage_break_fails_closed` | a declared input hash that does not match the supplied artifact raises |
| `test_accept_path` | Test 2 replays to ACCEPT (the positive case) |
| `test_repair_is_patch_only` | a repair claiming `mode: rewrite` is rejected |
| `test_determinism` | two replays produce identical hashes for all eight stages |

## Stage-separation assertions, specifically

These encode the architectural boundary the migration depends on:

```
Writer Grounding receives    {writer_output, source}      -- and nothing else
Writer Grounding does NOT receive article_form
Article Form derives from    {discovery, source}
Discovery derives from       {source}
ARTICLE_FORM and GROUNDING_FINDINGS are distinct artifacts
```

Grounding structurally cannot change the Form, because it is never given it.

## Production safety net untouched

`automation/snapshot_test.py` was **not modified**. It was run to confirm the baseline is
still intact: *"No drift — 6 article(s) match recorded fixtures."*

The shadow path has its own golden tests, kept entirely separate. Production's
`snapshot_test.py` remains the frozen legacy safety net.

**Future integration point, recorded not built:** when Phase 4 deletes the rewrite stage and
the two LLM rule-judges, the shadow's replay hashes and production's `snapshot_test`
baselines should be re-recorded in the same commit series, each re-recording justified. Note
the Phase-0 finding that `rewrite_with_opus`'s 25,019-character SYSTEM has **zero** snapshot
coverage in any harness; its hash is recorded in the Phase-0 prompt baseline so its removal
stays provable.
