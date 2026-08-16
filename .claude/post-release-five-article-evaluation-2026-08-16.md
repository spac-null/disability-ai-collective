# Post-Release Five-Article Evaluation — 2026-08-16

Reconstructed from preserved run artifacts on Trident (`/srv/data/hermes/evaluations/cripminds-five-article-2026-08-16/`) during the PM1.1 project-memory correction pass — this document did not exist as a durable repo record before this pass; it is written from the actual preserved artifacts (`run_result.json`, `captured.json`, `actual_models.json`, `_reviews/*.md`, `_drafts/*.md` per run), not from memory or inference. No repo report existed prior to this file.

**This is a DIFFERENT evaluation from `.claude/article-quality-evidence-pass-2026-08-14.md`** (the 140-article deterministic sweep + 15-article manual sample). Do not merge the two. This one:

- Ran on **Trident**, isolated worktree (`/srv/data/hermes/evaluations/cripminds-five-article-2026-08-16/`), against **exact origin/main release `691c365`** (the checkout is at that commit; `git status --short` on the checkout shows an untracked `.calibration-checkout/` and two `probe_out/`-adjacent scratch artifacts only — no tracked-file modifications).
- Used **real production providers** (confirmed directly in `artifacts/0N/actual_models.json`): `openrouter/claude-opus-4.8`, `anthropic/claude-opus-4.8`, `openrouter/claude-fable-5`, `openrouter/claude-haiku-4.5`, `openrouter/claude-sonnet-4.6`, `perplexity/sonar` — not mocked/stubbed calls.
- Every run: `"commit_success": false`, `"citations_clean": false`, `"status": "partial"` — **confirmed zero production mutation**. Drafts live only under `/tmp/cripminds-eval-*/_drafts/` inside the isolated checkout, never touched `_posts/`.

## Run inventory — 7 generation attempts, 5 distinct underlying stories

| Run | Source story | Byline (final `agent`) | Fable-brief `persona` (if captured) |
|---|---|---|---|
| 01 | Edinburgh arts festival / "you can't walk into a gallery" | Pixel Nova | Maya Flux |
| 02 | *same source as 01* | Siri Sage | Maya Flux |
| 03 | *same source as 01* | Zen Circuit | *(brief not captured — empty)* |
| 04 | Christy Brown / AI-assisted authorship, AAC parallel | Pixel Nova | *(brief not captured — empty)* |
| 05 | Premium headphones / audio codecs, deaf/HoH access | Siri Sage | Pixel Nova |
| 06 | Kelsie Conley's hand-crafted tactile map | Maya Flux | Siri Sage |
| 07 | AI-jobs-apocalypse (Reich) / disability economics | Maya Flux | Zen Circuit |

Runs 01/02/03 share one source, run with 3 different persona assignments — these are the "2 supplementary same-source runs" relative to whichever of the 3 is treated as that story's primary result. Runs 04–07 are each a distinct story, run once. **5 distinct stories total, 7 generation attempts total** — matches the brief's "5 primary distinct-story articles + 2 supplementary same-source runs" framing.

## Finding 1 — brief-persona ≠ final byline-persona: 5 of 5 runs where a brief was captured

Every run where `captured.json`'s `fable_brief.persona` field was non-empty (01, 02, 05, 06, 07 — 5 runs) shows a **different** persona in the final published byline (`run_result.json`'s `agent` field) than the brief specified. Runs 03 and 04 have an empty/uncaptured brief field, so no comparison is possible for those two. **Corrected count: 5/5 of runs with a captured brief, not "4/4"** as an earlier draft of this finding stated — verified directly against both JSON fields for all 7 runs.

## Finding 2 — natural unsupported-persona-biography attempts: 4 of 7 runs, not 5

`captured.json`'s `fable_reviews[0].unsupported_persona_claims` is non-empty in **4 runs**, confirmed by direct read:

- **Run 02** (Siri Sage byline): implies Siri physically attended this year's festival in Edinburgh — "an event established nowhere in her canon (she lives in Amsterdam) or the source."
- **Run 03** (Zen Circuit byline): invents a specific 2013 Crossrail interchange-sequencing episode and a July venue-mapping afternoon — canon only establishes 2012–2015 Crossrail employment generally, not these specific episodes.
- **Run 05** (Siri Sage byline): embellishes Pixel Nova's real canon fact (mother was an audiologist) with an invented duration ("thirty years in Edinburgh") and a fitting-room scene not in canon.
- **Run 07** (Maya Flux byline): invents a specific father's-knees-failing/job-ending event not present in the canon fact it's built on (22 years driving route 4735 is canon; the knees/job-loss detail is not).

Runs 01, 04, 06 show an empty `unsupported_persona_claims` list, and no separate citation-review flag of this type either. Run 04's own citation review flags a first-person claim ("studied at the Gerrit Rietveld Academie... NGT interpreter") but this is **Pixel Nova's real, authorized canon** (Jascha's own documented biography) — merely uncited, not fabricated, so it is not counted as a genuine unsupported-persona-biography attempt.

**Corrected count: 4 of 7 runs, not 5 of 7.**

## Finding 3 — correction outcome: 2 of the 4 detected attempts survived into the final draft

Checked directly whether each flagged phrase still appears in the run's final `_drafts/*.md` text:

- **Run 02** — flagged phrase absent from final draft. **Corrected.**
- **Run 03** — flagged phrases absent from final draft. **Corrected.**
- **Run 05** — flagged phrase ("thirty years in Edinburgh as an audiologist... fitted their aids") **still present** in the final draft. **Correction failed.**
- **Run 07** — flagged phrase ("when his knees went, so did both") **still present** in the final draft. **Correction failed.**

**This — runs 05 and 07 — is the direct empirical case that motivated PS1** (the 2026-08-16 "detected-but-uncorrected persona claims now fail closed" closure, `89cd082`/`169e8ff`): a claim the reviewer *did* detect and flag for revision nonetheless survived into what would have been the final published text, because the pre-PS1 pipeline trusted the revision to have actually removed it rather than re-checking.

## Finding 4 — image stack

Confirmed independently (not from this evaluation's artifacts, but directly from source in the main checkout, cross-checked here): `automation/gen_images.py`/`gen_persona_avatars.py` use **OpenRouter → Recraft V4.1**, not the Pollinations FLUX API `automation/README.md` still describes. This evaluation's own runs did not reach the image-generation step (`commit_success: false` halts before that stage), so this finding is corroborated from the main codebase, not from this evaluation's run artifacts specifically.

## Finding 5 — literary quality ranking: NOT a preserved artifact, not independently reconstructed here

No synthesized ranking, report, or "STRONG/PROMISING" verdict file exists anywhere in the evaluation directory (checked: no `SUMMARY`/`REPORT`/`RANKING`/`VERDICT` file, no such section in any `run0N.log`). A claim of "3 STRONG, 2 PROMISING" among the 5 primary drafts is **not confirmed by any preserved artifact** and is not asserted as fact here. If a literary quality ranking is wanted, it needs a fresh editorial read of the 5 primary drafts (01 or 02 or 03 — whichever is treated as primary for the shared source —, 04, 05, 06, 07) — flagged as follow-up work, not performed in this reconciliation pass.

## Source data

`/srv/data/hermes/evaluations/cripminds-five-article-2026-08-16/artifacts/{01..07}/{run_result.json,captured.json,actual_models.json,_drafts/*.md,_reviews/*.md}` (Trident, read-only access via existing SSH key). Not copied into this repo — these are large, per-run raw artifacts; this document is the durable summary. If exact reproduction is needed later, the discovery snapshot provenance is recorded in that directory's own `discovery_snapshot_provenance.txt` (source: a read-only copy of `disability_findings.db` at eval time).
