# DECISION-RECONCILIATION.md

Every explicit decision found in canonical docs, LOGBOOK.md, experiment docs,
and commit messages. STATUS reflects the highest-authority evidence found
(runtime/git > frozen artifact > owner decision > canonical doc > historical
doc), not just the newest text.

| ID | What | Status | Documented where | Superseded by |
|---|---|---|---|---|
| AP1 | Author-persona biography provenance fix | LIVE, blocking (`dbe0a96`) | WORK.md §3, LOGBOOK 08-15 | — |
| APE2 | Non-Opus preserved-biography edge case | LIVE (`e93bb1b`) | WORK.md §3 | — |
| PS1 | Detected-but-uncorrected persona claim fails closed | LIVE (`89cd082`/`169e8ff`) | WORK.md §3, LOGBOOK 08-16 | — |
| LPF1 | Legacy-draft auto-promotion closure | LIVE | WORK.md §3 | — |
| P1 | Human-detail provenance | SHADOW-ONLY, non-blocking | WORK.md §1/§3 | — |
| PRF1 (Persona Brief↔Writer Reconciliation) | Rotation-eligibility-first routing fix | DEPLOYED (`cb69c2d`) | WORK.md §3 | — |
| RG1 | Accepted PRFV-M1 as release-gate-sufficient | Decided, release proceeded | LOGBOOK 08-17 | — |
| DSR2 | Story Rejection V1 two-layer design (prototype) | Superseded by release below (patch-identical, confirmed via `git patch-id`) | LOGBOOK, worktree `-srv1`/`-story-rejection-release` | Story Rejection V1 |
| Story Rejection V1 | Two-layer commission/execution gate | **RELEASED, live in production, unconditional (not flag-gated)** — confirmed on trident | WORK.md §3, PROJECT-MAP, trident code | Story Rejection V1.1 |
| SRF3 / FC2 | False/permissive commission finding (first real V1 commission) | Forensic finding; motivated V1.1; **deliberately left unpatched at the time** (N=1, evidence artifact) | WORK.md §3 | closed by V1.1 fix |
| Story Rejection V1.1 | Semantic mechanism verifier + aggregator isolation | **RELEASED, live** (`d0204aa`), confirmed on trident | WORK.md §3 | — |
| CJ-1 | `cj1-v3.2-validity-before-recall` friction gate | FROZEN research contract, not a production gate, 3 parked implementation issues | WORK.md §6, `cj1-v3-friction-gate-2026-08-11.md` | — |
| CJ-2 | Competitive persona reframing (4-engine capsule) | **OFF** — `CJ2_INTEGRATION_MODE` confirmed unset at every level (code default, crontab, secrets) on trident; design frozen pre-freeze-protocol, no pipeline-wide terminal decision exists | WORK.md §6, `cj2-competitive-reframing-design-2026-08-11.md`, `final-evaluation-freeze-protocol-2026-08-13.md` | — |
| L2 testimony | Active companion-source retrieval | OFF (`L2_TESTIMONY_MODE` default), scaffolding only, live search deliberately not built | WORK.md §6 | — |
| RL-2026-001 | Reader Lab round 1 | COMPLETE (Shape-B hypothesis found) | LOGBOOK 08-12/13 | — |
| RL-2026-002 | Reader Lab round 2 | **PUBLISHED** to production D1 (corrected from an earlier "frozen, never published" misreading — a documented self-correction, not a live contradiction), 0/10 answered as of last check | WORK.md §6 | — |
| RL-2026-003 | Reader Lab round 3 | Designed/frozen locally, **untracked in git**, mid-flight, not published | WORK.md §6, preservation root `reader-lab/RL-2026-003/` | — |
| LC1 | Legacy corpus integrity | Phase 1 diagnosis complete, Phase 2 (semantic re-read, 122 unsampled articles) not started | WORK.md §4/§5, LOGBOOK 08-16 | — |
| A-M working list | 13-letter article-quality concern list | **No literal A-M document ever existed** — reconstructed working list; per-letter status: A/F/H/I/K/M done (A,F "done but evolved"); B/C/D/L partial; E split (selection done, essay-type adherence outstanding); G shadow-designed only; **J (STOP-risk/reader drop-off) never built at all** | `original-blueprint-A-M-reconciliation-2026-08-13.md` | — |
| Phase H (master-roadmap sense) | CJ-2 article-pilot validation | Preregistration only; does not schedule itself; gated on Phase F (not done); **naming collision with "H1" (LOGBOOK shorthand for the 08-14 overnight run) — different things** | WORK.md §6, `master-roadmap-2026-08-13.md` §13 | — |
| AR1 | Disability-as-epistemic-engine synthesis | Synthesis complete; 4 follow-on experiments designed, not run at time of writing | LOGBOOK 08-17, `artistic-reset-ar1-2026-08-17.md` | AR2 |
| AR2 / AR2C | Silent-Lens A/B (4 sources × 2 conditions) | Run; **no reliable writer-doctrine effect found** | LOGBOOK 08-17 | qualified by AR2.1 |
| AR2.1 / AR21B | 8-article forensic provenance audit of AR2's outputs | Complete; AR2's testimony **partly fabricated** (9 unsupported quotes, 2 attached to real named public figures); traced to NAMED VOICES/SOMEONE ELSE MUST SPEAK quota | LOGBOOK 08-17 | motivates AR3 |
| AR3 / AR3A | Testimony-quota removal, 3-condition/12-article | Run; removing quota cuts fabrication with **zero measured artistic cost**; quality gain monotonic A→B→C | LOGBOOK 08-17 | shipped as AR3-B |
| ARC1 | Perceptual Engine vs. Persona conceptual note | Preserved, **not decided**, 4 candidate architectures named, ordering left OPEN, deprioritized against Scout (not cancelled) | LOGBOOK 08-17 | — |
| AR3-B / SP1 | Production testimony-quota fix | **RELEASED, deployed** (`3225ea1`), confirmed on trident | LOGBOOK/WORK.md | — |
| SV0A | Scout V0 verdict (3 real Sofa articles generated) | **RECOMMENDED, PENDING JASCHA'S READ — not yet decided**, and the LOGBOOK entry recording it is itself uncommitted | LOGBOOK 08-17 (uncommitted) | — |
| SV0 B/C/D | Alternative Scout V0 verdicts | Referenced by label only in LOGBOOK's follow-up line; **never defined anywhere** — placeholder labels with no content | — (gap, see GAP-LEDGER G-002) | — |
| (unnamed) | SOFA-METHOD.md canonicalization | Self-declared canonical 2026-08-18; **never ratified by any decision entry, uncommitted** | `SOFA-METHOD.md` | — |
| (unnamed) | Sofa pipeline audit — 2 P0 blockers found (byline=persona=writer contradicts canonical §4; validated discovery dropped before writer) | Diagnosed 2026-08-18; **not committed, not in WORK.md/LOGBOOK.md**, no remediation decision made | `sofa-pipeline-audit-current-runtime-2026-08-18.md` | — |
| (unnamed) | Sofa Architecture v1 proposal — recommends "Architecture B" (Clean Separation) | Design proposal only, **not implemented, not decided on** | `sofa-architecture-v1-proposal-2026-08-18.md` | — |
| (unnamed) | Sofa shadow slice 1/1.1 | Mechanism sound, tested (51 passing tests) but explicitly **"READY FOR PRODUCTION WIRING: NO"** — never tested against real material or a live model | `sofa-shadow-slice-1[-1]-results-2026-08-18.md` | — |

## Addendum (2026-08-19 second-pass content-equivalence audit)

**AP1's relationship to the `-persona-biography` worktree branch, conclusively resolved.**
The `-persona-biography` worktree (`e93bb1b`) carries 3 commits that appear
patch-different from canonical `main` via `git cherry` — this could look like
3 commits' worth of unmerged work. It is not. Canonical commit `dbe0a96`'s
own message states: "Reconstructed as a single commit rather than merging the
research branch — carries only the pipeline code and its tests; excludes
`automation/persona_biography_review_capture.py` (a research-only semantic
spot-check capture tool, explicitly 'NOT part of the pipeline' per its own
docstring, not imported by any production code)." The pipeline logic was
deliberately hand-ported into AP1; the one file left behind was deliberately
excluded, not overlooked. No gap, no owner action needed. Full evidence in
WORKTREE-CONTENT-EQUIVALENCE.md.

This also closes out **G-010** (worktrees needing owner review): 3 of its 4
items are now confirmed patch-equivalent duplicates via `git cherry`
(`-article-quality`, `-human-detail-provenance`, `-ops-release-hardening`),
and the 4th (`-opening-quality`) is confirmed superseded by a later,
independently-written canonical implementation of the same-named files.

## Process-sequencing observation (not a decision, flagged for the owner)

LOGBOOK's own Scout V0 entry states the next step is Jascha's read and a
verdict among SV0A/B/C/D — "not a further engineering step." What actually
happened next (per the evidence) was a full day of further engineering:
Sofa Method canonicalization, a pipeline audit, an architecture redesign
proposal, and two shadow-code implementation slices — all before that verdict
was recorded anywhere as given. This is not a contradiction between documents;
it's a gap between what the process said should happen and what evidence
shows did happen. See GAP-LEDGER G-002.
