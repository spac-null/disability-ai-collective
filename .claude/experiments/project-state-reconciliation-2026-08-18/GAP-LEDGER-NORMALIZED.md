# GAP-LEDGER-NORMALIZED.md

Normalization pass, 2026-08-19. **The historical ledger is not rewritten** — `GAP-LEDGER.md`
keeps its original wording and its later correction sections. This file is the coherent view.

Taxonomy drifted across passes (`RESOLVED`, `DISPROVEN`, `LOST`, `FULL_RAW_NOT_FOUND` were used
as if they were STATUS values; they are not). Normalized into four orthogonal fields:

- **STATUS** — CURRENT / HISTORICAL / PARKED / MISSING / UNRESOLVED / DUPLICATE / CONTRADICTED
- **RESOLUTION** — OPEN / RESOLVED / SUPERSEDED / DISPROVEN
- **LOSS** — NONE / CONFIRMED_LOST / NEVER_PERSISTED / FULL_RAW_NOT_FOUND
- **BUCKET** — BLOCKER / DEBT / HISTORICAL / OWNER

BUCKET is the field that stops the project carrying 53 equally-weighted open loops. Only
**BLOCKER** items should gate Article Form work.

| ID | STATUS | RESOLUTION | LOSS | BUCKET | One line |
|---|---|---|---|---|---|
| G-001 | UNRESOLVED | OPEN | NONE | **BLOCKER** | 08-18 Sofa work untracked. Commit `7d59bb3` covered preservation evidence only — SOFA-METHOD.md, the 3 method docs, pipeline audit, architecture proposal, 2 shadow-slice results, 3 shadow code files and all 11 `scout-v0-*` dirs (incl. the FOX/HOUR/MOBILE frozen benchmarks) are STILL untracked |
| G-002 | HISTORICAL | SUPERSEDED | NONE | OWNER | Scout SV0 verdict gate — see SV0 section in PROPOSED-PROJECT-STATE |
| G-003 | UNRESOLVED | OPEN | NONE | DEBT | FOX benchmark file carries no `frozen-sofa-benchmark` marker (HOUR/MOBILE do) |
| G-004 | UNRESOLVED | OPEN | NONE | DEBT | No blind review anywhere in the FOX/HOUR/MOBILE lineage the Sofa Method is extracted from |
| G-005 | MISSING | RESOLVED | CONFIRMED_LOST | HISTORICAL | AR3 free-text blind-review reasoning not preserved; note the limitation, nothing recoverable |
| G-006 | HISTORICAL | SUPERSEDED | NONE | HISTORICAL | Shadow slice 1/1.1 "not ready for real material" — overtaken by the real-material Edinburgh runs |
| G-007 | UNRESOLVED | OPEN | NONE | OWNER | Pipeline audit's 2 P0s / 7 P1s; remediation decision. Partly answered by FORM-1/1.1 evidence |
| G-008 | UNRESOLVED | OPEN | NONE | **BLOCKER** | Two competing canonical pipeline statements (WORK.md §2A vs SOFA-METHOD.md) — must reconcile before canonical sync |
| G-009 | UNRESOLVED | OPEN | NONE | OWNER | SOFA-METHOD.md self-declares CANONICAL, never ratified, still untracked |
| G-010 | HISTORICAL | RESOLVED | NONE | HISTORICAL | Worktree patch-id equivalence established |
| G-011 | MISSING | OPEN | NONE | DEBT | 2 commits with no doc representation |
| G-012 | MISSING | OPEN | NONE | DEBT | Preservation filenames not referenced by name in PROJECT-MAP |
| G-013 | PARKED | OPEN | NONE | DEBT | 52 `cj*.py` + fixtures still untracked on main; durable backup exists, so low risk |
| G-014 | PARKED | OPEN | NONE | DEBT | No SQLite-safe backup method for the production DBs |
| G-015 | PARKED | OPEN | NONE | OWNER | `proto/story-rejection-v1` has no remote copy; push needs approval |
| G-016 | PARKED | OPEN | NONE | DEBT | `pixel-validation/control` diverged |
| G-017 | UNRESOLVED | OPEN | NONE | DEBT | `cripminds-calibration-runner.service` logging `internal_error` — untriaged, production-adjacent |
| G-018 | HISTORICAL | OPEN | NONE | DEBT | `automation/README.md` still names Pollinations FLUX |
| G-019 | HISTORICAL | OPEN | NONE | DEBT | `project-manifest.json` stale |
| G-020 | MISSING | OPEN | FULL_RAW_NOT_FOUND | HISTORICAL | Grok model-comparison artifact — distinct from the Edinburgh Grok run, still absent |
| G-021 | MISSING | OPEN | FULL_RAW_NOT_FOUND | HISTORICAL | Qwen model-comparison artifact + reasoning trace |
| G-022 | CONTRADICTED | RESOLVED | NONE | HISTORICAL | "Perplexity comparison" was actually a fact-check integration; characterization corrected |
| G-023 | MISSING | **RESOLVED** | NONE | HISTORICAL | Reader feedback had no durable trace — both readers' evidence now preserved under `external-evidence/human-reading/` |
| G-024 | CONTRADICTED | DISPROVEN | NONE | HISTORICAL | "No Edinburgh lineage exists" — disproven; lineage preserved and committed |
| G-025 | MISSING | RESOLVED | NONE | HISTORICAL | Sofa Real Article Test 1 preserved in full |
| G-026 | DUPLICATE | RESOLVED | NONE | HISTORICAL | Five-article eval had a durable copy |
| G-027 | MISSING | RESOLVED | CONFIRMED_LOST | HISTORICAL | Superseded by G-047 |
| G-028 | UNRESOLVED | OPEN | NONE | OWNER | "Reached by Boat or Plane" — published article with confirmed content/byline mismatch |
| G-029 | PARKED | OPEN | NONE | DEBT | Legacy corpus integrity Phase 2 (122 unsampled articles) |
| G-030 | UNRESOLVED | OPEN | NONE | DEBT | Guardian ~59% source concentration unverified |
| G-031 | UNRESOLVED | OPEN | NONE | DEBT | `_THEME_TO_PERSONA` hard keyword table contradicts the soft-affinity model; 2 confirmed bugs |
| G-032 | PARKED | OPEN | NONE | DEBT | `rewrite_with_opus` weak duplication check |
| G-033 | UNRESOLVED | OPEN | NONE | OWNER | `_should_block` permissive threshold — undecided rather than deliberate |
| G-034 | MISSING | OPEN | NEVER_PERSISTED | DEBT | STOP-risk / reader-drop-off detection never built |
| G-035 | PARKED | OPEN | NONE | DEBT | AR3.1 and AR4 queued, never run |
| G-036 | PARKED | OPEN | NONE | DEBT | Engine-before-persona / disturbance-mining / case-library — note Article Form partially answers the first |
| G-037 | UNRESOLVED | OPEN | NONE | DEBT | `_fable_update_state` runs before review, contradicting its docstring |
| G-038 | PARKED | OPEN | NONE | DEBT | CLIProxy dead OAuth account can poison routing |
| G-039 | UNRESOLVED | OPEN | NONE | DEBT | Degraded-article stamping gap |
| G-040 | UNRESOLVED | OPEN | NONE | DEBT | `audience-engagement-tasklist.md` never re-triaged |
| G-041 | DUPLICATE | RESOLVED | NONE | HISTORICAL | Byte-identical durable copy confirmed |
| G-042 | HISTORICAL | RESOLVED | NONE | HISTORICAL | Repo zip already assessed safe |
| G-043 | CONTRADICTED | RESOLVED | NONE | HISTORICAL | Worktree count 22 → 23 |
| G-044 | PARKED | OPEN | NONE | DEBT | 3 branch-only artifact groups, on protected refs |
| G-045 | CONTRADICTED | RESOLVED | NONE | HISTORICAL | Worktree alive on trident, not deleted |
| G-046 | HISTORICAL | RESOLVED | NONE | HISTORICAL | CJ1/CJ2 risk overstated; residue preserved |
| G-047 | MISSING | RESOLVED | **CONFIRMED_LOST** | HISTORICAL | 4 editorial-pairing drafts destroyed 2026-08-19 00:00; not recreatable |
| G-048 | HISTORICAL | RESOLVED | NONE | HISTORICAL | 3 `/tmp`-root Edinburgh files preserved |
| G-049 | HISTORICAL | SUPERSEDED | NONE | HISTORICAL | Superseded by G-052 |
| G-050 | UNRESOLVED | OPEN | FULL_RAW_NOT_FOUND | DEBT | Grok/Perplexity raw recovered; **Qwen raw + its input still absent** |
| G-051 | CONTRADICTED | RESOLVED | NONE | HISTORICAL | Two "reader" lines are Legacy article text |
| G-052 | CONTRADICTED | DISPROVEN | NONE | HISTORICAL | Cross-model convergence claim — models were fed B.3's prose as source |
| G-053 | HISTORICAL | RESOLVED | NONE | HISTORICAL | Father's feedback bound to the Legacy arm |

## Counts

| Bucket | n |
|---|---|
| **BLOCKER** | 2 (G-001, G-008) |
| OWNER | 6 (G-002, G-007, G-009, G-015, G-028, G-033) |
| DEBT | 22 |
| HISTORICAL | 23 |
| **Total IDs** | 53 |

| Resolution | n |
|---|---|
| RESOLVED | 21 |
| SUPERSEDED | 3 |
| DISPROVEN | 2 |
| OPEN | 27 |

| Loss | n |
|---|---|
| CONFIRMED_LOST | 3 (G-005, G-027, G-047) |
| FULL_RAW_NOT_FOUND | 3 (G-020, G-021, G-050) |
| NEVER_PERSISTED | 1 (G-034) |
| NONE | 46 |
