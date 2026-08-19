# Legacy Prompt / Rule Inventory — 2026-08-20

STATUS: **INVENTORY COMPLETE. NO CLEANUP EXECUTED.**

Audit task, not an experiment. No models were called. No articles were generated.
No production file was modified. No deploy. Writer Grounding calibration was not
reopened, and no WG-7 / FORM version / Gold calibration was created.

Repo audited: `/Users/stargatesgx/code/disability-collective-ai`
HEAD at audit time: `3a05f61` (verified). Rule-family count: **114** (see MASTER-INVENTORY.md; an early verbal summary said 98 — that was a summary miscount, corrected 2026-08-20), branch `main`, working tree carrying only
untracked experiment fixtures.

## What this answers

Which historical CripMinds prompt/rule baggage still exists after the newer
architecture (SOFA Method, Discovery→Article Form→Writer, Writer Grounding,
Story Rejection, PRF1) was developed — and which of it still runs.

## Files

| File | Contents |
|---|---|
| `MASTER-INVENTORY.md` | Every rule family: ID, location, origin, consumer, active?, execution surface, architectural owner, status |
| `ACTIVE-RULE-SURFACE.md` | The exact prompt census — every rule-bearing string that reaches a live model call, with measured sizes |
| `MASS-INJECTION-FINDING.md` | Answer to the mass-injection question: what it was, what it is, where, how many, which calls |
| `MIGRATION-MAP.md` | Rule → structural owner. What migrated, what should have and didn't |
| `DUPLICATES-AND-CONTRADICTIONS.md` | Duplication matrix + 8 contradictions, severity-ranked |
| `CLEANUP-RECOMMENDATIONS.md` | Per-family recommendation. Nothing executed. Owner decisions listed |
| `inventory.csv` | Machine-readable master inventory |
| `prompt-census.json` | Machine-readable prompt census with measured sizes |

## Evidence artefacts (captured, not authored)

| File | What it is |
|---|---|
| `writer_prompt_maya.txt` | The **actual** assembled live writer prompt (Maya Flux), 59,161 chars |
| `writer_prompt_pixel.txt` | Same for Pixel Nova (real-person-evidence provenance path), 54,673 chars |
| `planner_user_prompt.txt` | The actual assembled planner/Story-Rejection brief prompt, 15,358 chars |

These were captured by running the repo's own existing zero-network capture
harnesses (`automation/writer_prompt_test.py::_capture_writer_prompt` and
`automation/snapshot_test.py::_snapshot_generate_calls`) — no new harness was
built, no network call was made, no model was invoked.

## Headline

1. **Mass injection is real and is live today.** The single largest is a
   59,161-char / 9,862-word writer prompt assembled per run in
   `automation/orchestrator/generate.py:783–1050`.
2. **`automation/style_rules.py` — the 2026-08-09 "single source of truth" built
   specifically to end rule duplication — was never wired into any prompt.** It is
   a fourth parallel copy of the rules with zero runtime consumers.
3. **The testimony quota AR3 removed from the writer still runs in the rewriter**
   (`llm.py` rewrite rules 33 and 33b), on every article.
4. **Persona canon is injected twice, byte-identical, for fictional personas**, and
   the sentence joining the two copies contradicts itself.
