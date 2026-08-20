# Safety Results

**72 checks. 72 pass.** Full output: `results/capture-tests.txt`, `results/harness-tests.txt`.

## Capture side — 36 checks (`automation/shadow_capture_test.py`)

| Required by brief | Test | Result |
|---|---|---|
| capture default OFF | `test_default_off` — `enabled()` false with no flag; **OFF writes nothing at all** | ✔ |
| flag ON writes only capture artifacts | `test_flag_on_writes_only_capture_artifacts` — every write under the run id, no `.part` leftovers, append-only manifest, `COMPLETE` seal | ✔ |
| flag OFF ⇒ byte-identical legacy path | `snapshot_test.py --check` in the observability worktree: *"No drift — 6 article(s) match recorded fixtures"* | ✔ |
| capture failure does not alter legacy result | `test_capture_failure_never_raises` — unserialisable payload and an unwritable root both swallowed; unknown event and missing run id are no-ops | ✔ |
| no DB writes from capture code | `test_no_db_publication_or_network_in_capture_code` — no `sqlite3` | ✔ |
| no content writes | same — no `_posts`, no `_drafts` | ✔ |
| no publication calls | same — no `commit_to_git`, no `subprocess` | ✔ |
| raw source content preserved | `test_source_representations_preserved` — R1/R2/R3 verbatim and **kept distinct** | ✔ |
| evidence packet preserved | same — R4 round-trips | ✔ |
| writer-visible evidence preserved | `test_writer_visible_evidence_and_raw_output` — prompt verbatim | ✔ |
| hash mismatch detected | `test_hashes_recorded_and_mismatch_detectable` | ✔ |
| atomic/incomplete bundle detectable | `test_incomplete_bundle_detectable` — unsealed vs sealed | ✔ |
| no secrets captured | `test_no_secrets_persisted` — artifact refused, refusal recorded, **secret value absent from the whole bundle** | ✔ |

Additional: `test_raw_writer_and_rewrite_distinct` (raw ≠ rewritten, and the manifest records
`rewrite_changed_content`), and `test_hooks_are_additive_only` (the `generate.py` patch
deletes **0** lines and adds fewer than 80).

## Harness side — 36 checks (`harness/compare_test.py`)

| Required by brief | Test | Result |
|---|---|---|
| harness rejects source mismatch | `test_rejects_source_mismatch` → `REJECTED_SOURCE_MISMATCH`, with a reason stating outcomes are not sound to compare | ✔ |
| harness accepts exact hash match | `test_accepts_exact_hash_match` → `COMPARABLE`, `source_equivalence: EQUIVALENT` | ✔ |
| blocked legacy run remains comparable | `test_blocked_run_remains_comparable` → `COMPARABLE`; pairing recorded as legacy `BLOCKED` / shadow `ACCEPT`; note asserts neither system is assumed correct | ✔ |
| raw writer and rewritten output remain distinct | `test_raw_writer_and_rewrite_distinct` — different hashes, rewrite effect attributable by construction | ✔ |

Additional: `LEGACY_ONLY` mode with no shadow supplied; unsealed bundle → `CAPTURE_INVALID`;
tampered file → `CAPTURE_INVALID` naming the artifact; missing directory and manifest-less
directory both raise `BundleError`; no LLM/network machinery and no `difflib`/`SequenceMatcher`
in executable code; all four source representations reported; grounding measurements kept
separate rather than merged.

Fixtures are built by calling the **real** capture module, not a hand-rolled imitation of the
bundle format, so the tests exercise the actual on-disk shape.

## Two test-precision fixes made during this task

Both were my own tests matching prose rather than code, and both were tightened to scan
**executable code only** — identifiers, imports and non-docstring string literals, via AST:

1. the capture-side "no `_posts`/`_drafts`" check would have failed on those words appearing
   in a docstring;
2. the harness-side "no prose similarity" check **did** fail on the word *similarity* inside
   `compare.py`'s own docstring stating it does not do similarity.

The second was a real failing test, fixed rather than deleted. A test that asserts what the
prose says instead of what the code does is not a safety test.

## Not changed

`automation/snapshot_test.py` — unmodified, run only to confirm the legacy baseline holds.
No production behaviour, schema, prompt, or content was altered.
