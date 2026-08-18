# EXPERIMENT-RECONCILIATION.md

For every experiment found. Artifact completeness columns: source / prompt-input /
model-identity / parameters / raw-output / audit / human-judgment / decision-result.
Each is YES / NO / PARTIAL / NA. An experiment is NOT called "preserved" just
because its article output exists — see PARTIAL/NO cells below.

## Pre-Sofa research lineage (2026-08-10 → 08-13) — well preserved, well documented

| Experiment | Question | Status | Completeness (src/prompt/model/params/raw/audit/judg/decision) |
|---|---|---|---|
| **why-we-write** (`why-we-write-2026-08-10.md`) | Does a short doctrine statement beat founder-biography prompt blocks? | SHIPPED, KEEP frozen — later **scope-corrected**: all 4 frozen briefs used contained Fable-planning-stage fabricated evidence, narrowing (not invalidating) the claim | YES/YES/YES/YES/YES/YES/YES/YES |
| **fable-review-roi** (`fable-review-roi-2026-08-10.md`) | Which model should do editorial review? (pivoted mid-run) | **PAUSED, not concluded** on its original question; definitive safety finding: unsupported named-individual/testimony material traced to Fable's own planning-brief stage, not writer hallucination | YES/YES/YES/YES/YES/YES/YES/PARTIAL |
| **Phase 1.6 source-grounding** (`phase-1.6-source-grounding-2026-08-11.md`) | Can a deterministic evidence-validation layer close the planning-stage fabrication hole? | SHIPPED (`grounding.py`), with explicit still-outstanding items (full positive-control run never completed; heuristic-not-NER name-attribution limitation) | YES/YES/YES/YES/YES/YES/YES/YES |
| **CJ-1 v3 friction gate** (`cj1-v3-friction-gate-2026-08-11.md`) | What source-eligibility test isn't too strict (v2: 0/20 passed)? | **FROZEN** as `cj1-v3.2-validity-before-recall`, 3 parked implementation issues named, not yet wired into production | YES/YES/YES/YES/YES/YES/YES/YES |
| **CJ-2 competitive reframing** (`cj2-competitive-reframing-design-2026-08-11.md`, 697KB) | Does a 4-anonymous-engine capsule + comparator architecture produce better reframes? | CURRENT (frozen architecture, pre-freeze) — genuinely unfinished, human-review packet built but **never scored**; no pipeline-wide terminal decision | YES/YES/PARTIAL/PARTIAL/YES/YES/PARTIAL/PARTIAL |
| **Final evaluation freeze protocol** (`final-evaluation-freeze-protocol-2026-08-13.md`) | Governance only: what gate must CJ-2/B2 pass to exit dev tuning? | CURRENT — this document is the literal, sole reason CJ-2 remains OFF; held-out corpus does not exist (every `dataset_purpose` in repo is `"development"`) | NA/NA/NA/NA/NA/YES/NA/YES |

## Artistic Reset → Scout → Sofa lineage (2026-08-17 → 08-18)

| Experiment | Question | Status | Completeness |
|---|---|---|---|
| **AR1** | Is disability an epistemic engine or article subject? (synthesis, no run) | Synthesis complete; 4 follow-ons designed | NA/NA/NA/NA/NA/YES/YES/YES |
| **AR2 (Silent-Lens A/B)** + `ar2-...-articles/` | Does removing the AUTHOR RULE doctrine change subject-drift? (4 sources × 2 cond, 8 gen, 8 blind reviews) | Run; **no reliable doctrine effect found** (AR2C) — later qualified by AR2.1 | YES/YES/YES/YES/YES/NA/YES/YES |
| **AR2.1** (forensic audit of AR2) | Was AR2's own testimony grounded? | Complete; **partly fabricated** (9 unsupported quotes, 2 on real named public figures) — traced to testimony-quota prompt language | YES/NA/NA/NA/NA/YES/YES/YES |
| **AR3 (testimony-quota removal)** + `ar3-...-articles/` | Does removing the testimony quota cut fabrication without artistic cost? (3 cond × 4 sources = 12 gen, 12 blind reviews) | Run; **quota removal wins outright** (AR3A), zero cost, monotonic quality gain | YES/YES/YES/YES/YES/NA/**PARTIAL** (full free-text reasoning for the 12 reviews not durably preserved — a real completeness gap vs. AR2's directory)/YES |
| **ARC1** (concept preservation) | Should Perceptual Engine be separated from Persona? (no run) | Preserved, **not decided**, deprioritized against Scout | NA/NA/NA/NA/NA/NA/YES/PARTIAL |
| **AR3-B** | Production shipment of AR3's B condition | **RELEASED**, deployed (`3225ea1`), confirmed live on trident | n/a — production release, not a standalone experiment |
| **Scout V0** (`cripminds-scout-v0-sofa-articles-2026-08-17.md` + evidence dir) | Can a real-web discovery pass (excluding disability search terms) find genuine disturbances and produce finished articles? (6 discovery passes → 24 cards → 3 articles: FOX/HOUR/MOBILE) | Complete, shadow-only; verdict **SV0A pending Jascha's read**, SV0 B/C/D never defined | YES/**NO** (no prompt artifact preserved)/YES(asserted only)/PARTIAL/**NO** (no `raw/` dir exists, unlike AR2/AR3)/YES/**NO** (no blind review run at all — real methodological asymmetry vs AR2/AR3)/PARTIAL (argued, not ratified) |
| **FOX/HOUR/MOBILE versioned rewrite lineage** (10 dirs, `scout-v0-1-*` … `scout-v0-5-*`) | Iterative prose rewriting toward "Sofa Article" quality, per-mechanism | HOUR frozen at v02.5 (`frozen-sofa-benchmark`), MOBILE frozen at v05.4 (`frozen-sofa-benchmark`, after 2 title renames), **FOX never carries an explicit frozen marker** despite being used as a benchmark — see GAP-LEDGER G-003 | YES(inherited)/NO/NO/NO/NO/PARTIAL (only v0.1's NOTES.md has an explicit provenance statement)/**NO** (no blind-review apparatus anywhere in this lineage)/PARTIAL |
| **sofa-method-v0 / v0.1 / v0.2** (method extraction from the frozen benchmarks) | What transfers across Fox+Hour (v0/v0.1), then Fox+Hour+Mobile (v0.2)? | HISTORICAL, superseded for operational use by `SOFA-METHOD.md` (named explicitly, verbatim, in its own supersession banner — the single clearest cross-reference found in this whole audit) | YES/NA/NA/NA/NA/YES/YES/YES |
| **SOFA-METHOD.md** canonicalization | Formalize the extracted method as canonical operating doctrine | Self-declared canonical 2026-08-18; **uncommitted, never ratified by an owner decision entry** | n/a — doctrine document, not an experiment |
| **Sofa pipeline audit** | Does the live `automation/` runtime match SOFA-METHOD.md? | **2 P0 blockers found**: (1) byline=persona=writer contradicts canonical §4 "Lens≠Writer"; (2) validated discovery dropped before the writer sees it. 7 P1 degraders also found. Not committed, not in WORK.md/LOGBOOK.md | YES(code reads, cited by file/line)/NA/NA/NA/NA/YES/YES/YES |
| **Sofa Architecture v1 proposal** | How should the pipeline be redesigned to fix the 2 P0s? | Recommends "Architecture B" (Clean Separation); **not implemented** | YES/NA/NA/NA/NA/YES/YES/YES |
| **Sofa shadow slice 1 / 1.1** | Does a standalone Discovery Packet module work mechanically, and can a post-writer grounding audit catch unauthorized claims? | Mechanism sound (51 passing tests, 0 network calls); **explicitly "READY FOR PRODUCTION WIRING: NO"** — never run against real material (no evidence packets exist for Fox/Hour/Mobile beyond prose; `engagement.db` is a 0-byte file locally; no live credentials) or a real model | source=**NO** (synthetic, disclosed fictional case)/prompt=YES/model=**NO**/params=NA/raw-output=**NO** (agent-authored disclosed substitute)/audit=YES/judgment=NA/decision=YES (MIXED verdict) |
| **"Sofa Real Article Test 1"** (found in `~/.claude/jobs/` + orphaned `/tmp` files, NOT in canonical `.claude/experiments/`) | A/B of legacy-shadow vs sofa-shadow against a **real fetched** Edinburgh Art Festival article | Exists only as unpreserved temp artifacts — see UNPRESERVED-ARTIFACTS.md item 1; **status/verdict unknown to this audit**, not in any canonical doc | Not assessable without reading the files directly — flagged for owner review, not analyzed further here (scope was preservation-risk, not content) |

## Correction: no "Edinburgh" experiment lineage exists under that name

"Edinburgh" appears in exactly two places in this repo, both as **Siri Sage's
persona-canon birthplace** (Leith) inside generated article prose
(`ar2-silent-lens-2026-08-17-articles/warehouse-B.md`,
`ar3-unforced-human-presence-2026-08-17-articles/langenegg-C.md`) — never as a
project/experiment/version-lineage codename. The actual A→B.1→B.2→B.3→B.4→
FORM-1→FORM-1.1-shaped pattern this reconciliation was asked to trace is the
**FOX/HOUR/MOBILE lineage** above (three parallel chains, not one linear
chain). See GAP-LEDGER G-024.

## Cross-model comparison "experiments" — none found as run artifacts

No Grok, Qwen, or Perplexity model-vs-model article-generation comparison run
exists in the repo or preservation root. See INVENTORY.md §G and GAP-LEDGER
G-020/021/022.
