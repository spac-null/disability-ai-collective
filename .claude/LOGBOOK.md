# LOGBOOK — Chronological History

Append-only. Newest entry at the bottom. Format:

```
## YYYY-MM-DD — CODE
STATUS: ...
DECISION: ...
EVIDENCE: <doc/path>
CODE: <commit SHA(s)>
SUPERSEDES: ...
FOLLOW-UP: ...
```

Keep entries short — do not paste whole reports, link to them. If a project-memory shorthand
code (like "H1"/"RLS1" below) isn't a literal term found in repo docs, that's noted once here;
see `.claude/WORK.md` `## 7` for the full list.

**Chronology/evidence-priority rule** (see `.claude/WORK.md` `## 7a` for the full statement):
newer does not automatically outrank older. Priority order when documents conflict: (1) direct
current runtime/code/DB evidence, (2) a frozen experiment artifact, (3) an explicit owner
decision, (4) current canonical documentation, (5) historical documentation, (6) inference. Check
uncommitted working-tree state and reachable production hosts before declaring evidence
nonexistent — see the 2026-08-16 PM1.1 entry below for what this rule was written in response to.

---

## 2026-08-09 — DISCOVERY CLEANUP
STATUS: DONE
DECISION: Deleted `run_discovery.py`, root-level `production_orchestrator.py`, `opus_rewrite.py` — confirmed dead (crontab + `findings` table not growing since 2026-05-02). `automation/production_orchestrator.py` is the only orchestrator.
EVIDENCE: `docs/DISCOVERY.md` (self-marked historical)
CODE: (2026-08-09 cleanup commits)
SUPERSEDES: any doc still describing `run_discovery.py`/root orchestrator as live.
FOLLOW-UP: none.

## 2026-08-10 — ENGAGEMENT DB INCIDENT
STATUS: CLOSED / RECOVERED
DECISION: Ad hoc rsync overwrote production `engagement.db` with an empty local stub (no `*.db` exclusion in sync command). `engagement_metrics` re-fetchable, `review_signals` reconstructed from 129 `_reviews/*.md` sidecars, `article_plans` (≤2 rows) permanently lost, not fabricated back.
EVIDENCE: `.claude/2026-08-10-engagement-db-incident.md`
CODE: `4ffb4c9`
SUPERSEDES: n/a (incident record)
FOLLOW-UP: `automation/sync_to_trident_for_testing.sh` hard-excludes `*.db*`; `automation/backup_state_dbs.py` daily 03:30 backups, 14-day retention. Moving state DBs out of the repo checkout entirely remains deferred infra hardening, not blocking.

## 2026-08-10 — WHY WE WRITE (doctrine)
STATUS: SHIPPED
DECISION: KEEP, scope-corrected — doctrine validated for "the then-current planning architecture," not guaranteed under Phase 1.6+ changes without a smoke re-check.
EVIDENCE: `.claude/experiments/why-we-write-2026-08-10.md`
CODE: `01339ce`
FOLLOW-UP: small smoke confirmation after Phase 1.6, not a full re-run.

## 2026-08-11 — CJ-1 FROZEN
STATUS: FROZEN (research contract, not a production gate)
DECISION: `cj1-v3.2-validity-before-recall` frozen as the CJ-2 input contract. 3 implementation issues parked (smart-quote resolver wiring, `resisting_detail` citing material outside `source_anchors`, source-completeness "authoritative NO" unresolved) — none block CJ-2.
EVIDENCE: `.claude/experiments/cj1-v3-friction-gate-2026-08-11.md`
CODE: (research artifacts only, `automation/.probe_fixtures/cj1-v3*`)
FOLLOW-UP: none unless a fresh batch exposes a new failure class.

## 2026-08-11 — CJ-2 ARCHITECTURE DESIGNED
STATUS: DESIGN FROZEN, PRE-PROMPT-COMPOSITION (later development calls happened 2026-08-12/13, still pre-freeze)
DECISION: 4 anonymous engine-capsules (P/S/Z/M, no persona names/disability vocabulary in-prompt) → Stage A independent reframes → deterministic Stage B provenance check → Stage C comparator, 5-axis hard gate. 4 correction rounds same day (evidence/inference boundary, anchor stable-IDs, full anonymization, no-distinctive-contribution FROZEN behavior, `source_snapshot` given to Stage C, jargon leak fixes).
EVIDENCE: `.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md`
CODE: none (research/design only at origin; dev-only regression runs followed under `automation/.probe_fixtures/cj2-b2-*`)
SUPERSEDES: an earlier `cj2_winner_bridge_v1` schema (marked SUPERSEDED in master-roadmap `## G.1.4`, replaced by `## G.1.1`'s schema).
FOLLOW-UP: see FINAL EVALUATION FREEZE PROTOCOL below.

## 2026-08-11 — PHASE 1.6 SOURCE-GROUNDING HARDENING
STATUS: DONE (not perfect — known limitations recorded)
DECISION: Evidence-packet source-hash design, legacy-brief rejection policy, 7 adversarial offline review rounds + live acceptance controls. Established Jascha-archive-authorizes-Pixel-Nova-only scope.
EVIDENCE: `.claude/experiments/phase-1.6-source-grounding-2026-08-11.md`
CODE: (Phase 1.6 commit range, 2026-08-09 to 08-11 — see WORK.md era table in legacy-corpus audit for exact SHAs)
FOLLOW-UP: only re-open if the regression suite fails or a real new grounding seam is found live.

## 2026-08-12 — READER LAB v0 LIVE (two-person pilot)
STATUS: LIVE, TWO-PERSON PILOT (not a public feature, not statistical calibration)
DECISION: Cloudflare Worker + D1, `lab.cripminds.com`, session-cookie one-time-invitation auth, RL-YYYY-NNN calibration-round naming convention established. Session/ops separation: research sessions run with zero Cloudflare/D1 credentials; a separate privileged ops session handles all live reads/writes via versioned handoff files.
EVIDENCE: `.claude/reader-lab-v0-design-2026-08-12.md`, `.claude/reader-lab-handoff/*`
CODE: `reader-lab-worker/` (this directory)
FOLLOW-UP: RL-2026-001 (below).

## 2026-08-12/13 — RL-2026-001 COMPLETE
STATUS: COMPLETE
DECISION: 5-item round, both reviewers 5/5, backfilled to `status='published'`. First real calibration finding: the "Shape-B" (adjacent-fact-synthesis, H14-vs-De-Hooch) hypothesis.
EVIDENCE: `.claude/reader-lab-handoff/RL-2026-001-*.json`
CODE: n/a (data round, not code)
FOLLOW-UP: exposed 2 gaps (no eligible additional reviewer; empty `calibration_candidates`), fixed same window (§27 of the design doc).

## 2026-08-13 — RL-2026-002 INGESTED AND PUBLISHED (corrected 2026-08-16 — was wrongly recorded as "frozen, never published")
STATUS: PUBLISHED to production D1, awaiting reviewer engagement — not frozen, not blocked
DECISION: All 5 candidates ingested via the real production path, zero rejections, round_id auto-assigned (`79649bd`). **Correction (2026-08-16 PM1.1 pass):** the round WAS published via the admin UI/candidate-bridge path on `2026-08-13T14:32:22.184Z` (`rounds.status='published'`, `source='admin_ui'`, `manifest_sha256=b2c82a2e9262211425c456097f1bbf6d1a79588a6526e079904f20fd752fced4`) — this evidence was already sitting as an uncommitted `status_correction_2026-08-14` annotation directly inside `reader-lab/rounds/drafts/RL-2026-002.json` and `calibration/candidates/RL-2026-002-preregistration.json` (verified identical on Trident and locally), simply never committed or read during the PM1 pass. The research-session draft file's OWN `status` line still says `"draft_prepared_by_research_session_not_saved_to_production"` — that line describes the research-session file, not the production D1 round, and is what caused the earlier misreading.
EVIDENCE: `reader-lab/rounds/drafts/RL-2026-002.json`'s and `calibration/candidates/RL-2026-002-preregistration.json`'s own `status_correction_2026-08-14` field (uncommitted, present in working tree)
CODE: `79649bd` (ingestion); publication itself happened via the admin UI, not a commit
SUPERSEDES: the "frozen, never published" framing of this entry as it read before 2026-08-16.
FOLLOW-UP: as of the last check (2026-08-14): 5 items, 10 assignments (2 reviewers × 5), 0 served, 0 answered — reviewers simply haven't reopened their invite link, no code/data defect, no evidence of pressure to continue immediately. Other CJ-2 freeze-protocol phases (B-F) wait on this round's eventual analysis; it does not wait on them. RL-2026-003 remains separately uncommitted/mid-flight (see WORK.md `## 6`).

## 2026-08-13 — MASTER ROADMAP + A-M RECONCILIATION
STATUS: DOCUMENTED (frozen snapshot as of this date)
DECISION: Confirmed no literal A-M blueprint document exists (see WORK.md `## 7`). Reconstructed 13-topic working list, phase table A-J for CJ-2/B2 research+product roadmap.
EVIDENCE: `.claude/master-roadmap-2026-08-13.md`, `.claude/original-blueprint-A-M-reconciliation-2026-08-13.md`
CODE: n/a (docs)
SUPERSEDES: nothing wholesale — internally marks `cj2_winner_bridge_v1` superseded by `## G.1.1`'s schema.
FOLLOW-UP: repo has since moved past this doc's "ahead N commits" claims — trust its phase-table structure, not its branch-state claims.

## 2026-08-13 — FINAL EVALUATION FREEZE PROTOCOL
STATUS: GOVERNANCE ESTABLISHED, requirements outstanding
DECISION: Preregistered the exact conditions for CJ-2/B2 to move from development tuning to a frozen held-out evaluation: human-calibration stop rule per semantic-failure family, exactly ONE consolidated B2 revision, two stable regression probes, ≥2 qualitatively different natural Stage-C safe admissions (0/14 to date), anti-overcorrection re-check, then semantic freeze, then a freshly-collected held-out corpus (none exists yet — every stored `dataset_purpose` is `"development"`), then held-out evaluation, then production-candidate review (human-only, not production promotion).
EVIDENCE: `.claude/experiments/final-evaluation-freeze-protocol-2026-08-13.md`
CODE: n/a (governance doc)
FOLLOW-UP: this is why CJ-2 is OFF — see WORK.md `## 6`.

## 2026-08-14 — H1 (natural overnight production run + morning stabilization)
STATUS: DONE. One current pipeline bug confirmed, not fixed this pass.
DECISION: 9-commit stack verified clean (zero B2/CJ-1 semantic files, zero RL data, zero secrets, `CJ2_INTEGRATION_MODE`/`L2_TESTIMONY_MODE` both confirmed OFF by default). Found a genuine generation-time duplication bug in `automation/orchestrator/llm.py`'s `rewrite_with_opus` (weak `count("---") >= 2` accept-check) that produced duplicated prose in `_posts/2026-03-31-the-floor-plan-of-disappearance.md` since its original 2026-03-31 creation commit. Release recommendation: ship the 9-commit stack; repair the one bad article separately.
EVIDENCE: `.claude/overnight-main-run-2026-08-14.md`, `.claude/morning-stabilization-2026-08-14.md`
CODE: 9-commit stack `128fda8`..`eba8290`
SUPERSEDES: n/a
FOLLOW-UP: shared duplication guard for all 3 revision/rewrite acceptance paths in `llm.py` — NOT built (see 2026-08-16 note below, still open).
NOTE: "H1" is project-memory shorthand, not a literal repo term — do not confuse with master-roadmap "Phase H" (CJ-2 article-pilot, separately preregistered same day, not started). See WORK.md `## 6`/`## 7`.

## 2026-08-14 — FLOOR-PLAN ARTICLE CONTENT FIX
STATUS: FIXED (content); underlying pipeline bug NOT fixed
DECISION: `_posts/2026-03-31-the-floor-plan-of-disappearance.md`'s duplicated prose removed. The repair-proposal doc's own text ("proposal, NOT executed... article file not touched") was accurate only at the moment it was written — confirmed the fix landed later the same day.
EVIDENCE: `.claude/floor-plan-repair-proposal-2026-08-14.md` (superseded by the commit below)
CODE: `64d1658`
FOLLOW-UP: `llm.py`'s class-wide weak duplication-accept check is still live and unpatched as of 2026-08-16 (verified: only commit ever to touch that check is the original 2026-08-09 extraction). Any future non-Opus draft could reproduce the bug.

## 2026-08-14 — A-M RECONCILIATION RE-CHECK (G/H/I closed)
STATUS: DONE
DECISION: G (repetition shadow detector), H (review-coverage truncation removed), I (invisible/truncated rule checks) all re-verified DONE, upgrading their 2026-08-13 "STILL OUTSTANDING" classification.
EVIDENCE: `.claude/original-blueprint-A-M-reconciliation-2026-08-13.md` (re-check appended, not overwritten)
CODE: `204c3bc`
FOLLOW-UP: J (STOP-risk/reader drop-off) never built, still outstanding. A second M-adjacent gap found and left unfixed: a *sole* `gate_llm` degradation doesn't by itself force `fact_check_status: blocked`.

## 2026-08-14 — REPETITION-SHADOW CORPUS HARVEST
STATUS: SHADOW-ONLY, no-promotion date 2026-08-28
DECISION: Ran the existing unmodified repetition detector across all 140 committed articles, zero network calls. 60% of raw candidate pairs are figure/caption-boilerplate false positives. One real content-duplication bug found (floor-plan article, above).
EVIDENCE: `.claude/repetition-shadow-corpus-harvest-2026-08-14.md`
CODE: `204c3bc` (detector, unmodified this pass)
FOLLOW-UP: threshold (0.35) unchanged; candidate fix (exclude `<figure>` blocks before paragraph splitting) recorded, not implemented.

## 2026-08-14 — ARTICLE-QUALITY EVIDENCE PASS (corrects "five-article" framing)
STATUS: DONE — deterministic sweep across 140 articles + 15-article manual stratified sample. NOT a "five-article production-parity batch"; that phrase does not appear in the source document.
DECISION: Persona-biography fabrication risk demonstrated via a **designed paired experiment** (Maya Flux + Siri Sage each deliberately invented one first-person anecdote untraceable to canon), plus one separate real historical incident (a fabricated "Rotterdam wayfinding review" that shipped before any guard existed) — this is what led directly to AP1 (below). Author-presence gaps (~47% generic/delayed openings) and testimony gaps (~53% of sample lacking real lived-experience testimony, L2-related) found and rated medium severity — real but not catastrophic (0/15 correction-integrity failures). Source-outlet concentration: Guardian is 50/85 of `source_url`-bearing articles and was entirely WebFetch-unreachable this session — an **audit blind spot**, not a confirmed diversity problem.
EVIDENCE: `.claude/article-quality-evidence-pass-2026-08-14.md`
CODE: n/a (read-only evidence pass, isolated worktree)
SUPERSEDES: any prior "five-article"/"production-parity" framing of this evaluation.
FOLLOW-UP: AP1 (below); L2 companion-search design (`.claude/l2-testimony-design-2026-08-14.md`, OFF).

## 2026-08-14 — HUMAN-DETAIL PROVENANCE (P1) + SOURCE-TRUNCATION FIX (S2A)
STATUS: P1 material, shipped SHADOW-ONLY. S2A shipped.
DECISION: `human_detail_provenance.py` checks personal-contact claims against fetched source text — 2 confirmed real incidents + 5 structurally-ungrounded articles across a 141-article sweep. Never blocks, never feeds `_should_block`/`gate.py`. Separately: source-truncation limit raised/unified to 20,000 chars and now disclosed (`source_original_length_chars`), corrected mid-doc from an initial "S3" mischaracterization to the accurate "S2A" classification.
EVIDENCE: `.claude/human-detail-provenance-and-source-completeness-2026-08-14.md`
CODE: branch `human-detail-provenance-2026-08-14` (not merged to main as of this doc)
SUPERSEDES: n/a — explicitly a DIFFERENT safety domain than AP1/APE2 (see WORK.md `## 1`). Do not confuse "P1" here with "PS1" (2026-08-16, below).
FOLLOW-UP: still shadow-only as of this consolidation (2026-08-16) — not part of the PS1 promotion gate.

## 2026-08-14 — L2 TESTIMONY DESIGN
STATUS: OFF (scaffolding only)
DECISION: `testimony_l2.py` shipped (heuristic, eligibility checks, SHADOW-mode fixture bridging, 30 tests). Live companion-source search deliberately not built.
EVIDENCE: `.claude/l2-testimony-design-2026-08-14.md`
CODE: `automation/orchestrator/testimony_l2.py`
FOLLOW-UP: blocked on cost/latency, ranking design, source-trust policy, and heuristic calibration — revisit once the human-detail-provenance shadow has real accumulated data.

## 2026-08-14 — PRODUCTION RELEASE PROCEDURE WRITTEN
STATUS: CURRENT PROCESS
DECISION: The 2026-08-14 release (12 commits: A-M safety fixes + floor-plan repair) hit real concurrency with the daily bot mid-release; recovery was invented live, then written down as a formal checklist (FETCH → PREFLIGHT classify → safe rebase if needed → retest → final race check → push → Trident exact-SHA pull → post-deploy retest → let cron exercise anything live-model-dependent).
EVIDENCE: `docs/production-release-procedure.md`
CODE: n/a (process doc)
FOLLOW-UP: scope is `automation/` only — Reader Lab has its own, separate deploy path.

## 2026-08-15 — RLS1 (first Work + author-persona release)
STATUS: SHIPPED
DECISION: Two release changes shipped and documented together: (a) first-class CripMinds Work, "What the Room Heard," with a model-example `provenance_summary` front-matter block and a full CC0 rights-closure record (original source rejected for weak PD claim, replaced with a verified CC0 Freesound recording); (b) AP1 (author-persona biography provenance safety, see 2026-08-14 entry above) shipped to `main`.
EVIDENCE: `.claude/cripminds-what-the-room-heard-rights-closure-2026-08-15.md`, `.claude/author-persona-biography-provenance-2026-08-14.md`
CODE: `aa0172e` (Work), `691c365` (docs), `dbe0a96` (AP1), `f069852` (AP1 design+decision), `e93bb1b` (APE2)
NOTE: "RLS1" is project-memory shorthand introduced by this consolidation, not a literal repo term — see WORK.md `## 7`.
FOLLOW-UP: APE2 edge case (same day, e93bb1b) — see WORK.md `## 3`.

## 2026-08-16 — PS1 (detected-but-uncorrected persona claims fail closed)
STATUS: SHIPPED
DECISION: A detected-but-not-repaired persona-biography claim could previously still slip through if the revision meant to fix it silently failed; now a known flagged claim surviving a failed revision fails closed instead of publishing. **Corrected label (2026-08-16 PM1.1 pass): this closure is "PS1," a different thing from the `publication_safety_version` contract ("LPF1," see next entry) — an earlier pass conflated the two under one combined label.** Direct empirical case that motivated this exact fix, found during the separate 2026-08-16 five-article evaluation (see `.claude/post-release-five-article-evaluation-2026-08-16.md`): runs 05 and 07 both had a claim the reviewer flagged for revision, which the revision failed to actually remove — the flagged text was still present in the final draft.
EVIDENCE: commit messages (no separate design doc found); corroborating evidence in `.claude/post-release-five-article-evaluation-2026-08-16.md`
CODE: candidate `89cd082`, deployed integration `169e8ff`
FOLLOW-UP: none open.

## 2026-08-16 — LPF1 (legacy-draft auto-promotion fail-closed closure)
STATUS: DEPLOYED (current `LAST_PRODUCTION-CODE_RELEASE`, pushed to origin/main)
DECISION: `publish_best.py`'s only content-safety check was `fact_check_status != "blocked"` — a missing field or a stale legacy `"verified"` both read as promotion-eligible with zero re-check against current safety code. This is exactly how "Reached by Boat or Plane" (below) promoted itself unexamined. Fix: `generate.py` now stamps `publication_safety_version: 1` only once every authoritative check (`fable_brief`, `gate_llm`, persona-biography check, fact-check) has settled clean; `publish_best.py` now requires BOTH `fact_check_status: verified` AND a current `publication_safety_version` before promotion. Anything else: HELD (`NEEDS_CURRENT_REVALIDATION`), untouched on disk. **This is a distinct closure from PS1 above — LPF1 is about a historical draft with stale/missing safety metadata being auto-promoted later; PS1 is about a flagged claim surviving a failed revision within one generation run.**
EVIDENCE: commit body (`git show 667633f`)
CODE: `667633f`
SUPERSEDES: `publish_best.py`'s old `fact_check_status != "blocked"` eligibility check.
FOLLOW-UP: does NOT cover human-detail provenance (P1 — a third, separate label, still shadow-only — see 2026-08-14 entry). Legacy drafts/articles lacking current-safety proof are held, not automatically revalidated — "Reached by Boat or Plane" is the standing example (below).

## 2026-08-16 — "REACHED BY BOAT OR PLANE" — LEGACY-PROMOTION-HOLE PILOT/FAILURE CASE (plan-divergence upgraded to CONFIRMED, 2026-08-16 PM1.1 pass)
STATUS: NOT YET REMEDIATED PUBLICLY (confirmed by reading current front matter — no `publication_safety_version` field, `fact_check_status: verified` is a pre-LPF1 stamp)
DECISION (established facts only):
- Generated as a historical draft (2026-08-11) before AP1/APE2/PS1/LPF1 existed; published 2026-08-15.
- Its own async citation review (`_reviews/2026-08-11-reached-by-boat-or-plane-review.md`) found a CONTRADICTED stat (courtyard gate height), an UNVERIFIABLE event date, and multiple UNATTRIBUTED personal-history claims (a claimed Amsterdam concert-hall visit March 2019, claimed ferry recordings in the Firth of Forth/Wadden Sea) — none of this blocked publication because citation review here is explicitly async/advisory, not gating.
- Its own Plan-Follow Read found `OPENING_SHAPE: MISMATCH` — the pre-generation brief's committed opening shape did not match the final article's actual first sentence.
- **CONFIRMED (direct query against Trident's production `engagement.db`, `article_plans` table, `planned_at: 2026-08-11 09:05:59`):** the DB `agent` column is **Siri Sage**; the persisted `plan_json`'s own `"persona"` field is **Maya Flux**; the plan's `correction_moment`/`resisting_example` evidence fields are centered on the building's physical-access/commission requirements (explicitly: "wheelchair clearance, threshold, and approach," a courtyard gate's specified dimensions/maker) — Maya Flux's mobility/access domain, not acoustics. The final published article is instead entirely about acoustics/listening/ferry-recordings, Siri Sage's domain. **This upgrades the plan/persona-divergence claim from UNVERIFIED (PM1 pass) to CONFIRMED.** The exact Aug-11 "Agent rebalanced X → Y" log line is NOT recoverable (checked directly: no such line found in `automation.log` for this slug) — the specific routing EVENT is inferred from this surrounding mechanism/plan evidence, but the persisted PLAN ↔ final PERSONA/ARTICLE divergence itself is direct DB evidence, not inference.
- The historical `fact_check_status: verified` metadata was trusted at promotion time with zero re-check — this IS the exact hole LPF1 (above) closed, confirmed directly in code.
EVIDENCE: `_posts/2026-08-11-reached-by-boat-or-plane.md` (current front matter), `_reviews/2026-08-11-reached-by-boat-or-plane-review.md`, `automation/engagement.db`'s `article_plans` table (Trident, direct query 2026-08-16), `.claude/legacy-corpus-integrity-phase1-2026-08-16.md` (independently flagged this article RED in Phase 1 of the legacy corpus audit, same day)
CODE: n/a (content, not code)
SUPERSEDES: this entry's own prior UNVERIFIED framing of the plan-divergence claim.
FOLLOW-UP: recommission/remediation decision NOT yet made — do not silently withdraw or silently patch. See WORK.md `## 5` item 3.

## 2026-08-16 — LEGACY CORPUS INTEGRITY AUDIT, PHASE 1
STATUS: DIAGNOSIS COMPLETE (Phase 2 not started)
DECISION: LC1 — material legacy credibility risk, begin prioritized remediation. Highest-severity finding: `research/care-labor.html` (real named individual + real company, factual mismatch vs. actual tribunal record). 32/142 published articles have no citation-review file at all; ~40% of sampled review files are stale (audit a draft that no longer matches the live article).
EVIDENCE: `.claude/legacy-corpus-integrity-phase1-2026-08-16.md`, `.claude/audits/legacy-corpus-integrity-2026-08-16.json`
CODE: n/a (audit, no content changed)
FOLLOW-UP: Phase 2 semantic pass across the 122 unsampled articles; immediate look at `research/care-labor.html`.

## 2026-08-10 — PERSONA TARGET ARCHITECTURE DESIGNED (recovered from git history 2026-08-16 — was silently dropped from current-work.md's lean rewrite)
STATUS: DESIGN ESTABLISHED, Phase 3 implementation NOT STARTED (still true as of 2026-08-16)
DECISION: Six-category persona model (CORE PERSON / PERCEPTUAL ENGINE / MOTIVE / AFFINITY / RISK / TEXTURE) recorded, with AFFINITY explicitly replacing "territory" as a soft routing prior, never ownership. Preregistered validation idea: one rich non-disability source → all four personas → score WHAT DID THIS MIND NOTICE / CATEGORY JUMP / IRREDUCIBILITY / OVERLAP / LORE LEAKAGE. Downstream CJ-2 consequence recorded: routing should become "what does each persona's perceptual engine expose about this source" not "which persona is appropriate for this topic."
EVIDENCE: `.claude/persona-architecture-audit.md` (Phase 1.5A, per-persona hypotheses under all six categories); full original wording recovered from commit `b2773c8`
CODE: n/a (design doc)
SUPERSEDES: n/a
NOTE: this content was present in `current-work.md` as of `b2773c8` (2026-08-10) but is absent from the file's current form — commit `d6ad389` ("rewrite current-work.md as lean operational checkpoint") is where it was pruned. Recovered here so it isn't lost a second time. **Do not confuse this established architecture with the unconfirmed DISCOVERY→SOURCE→SUBJECT→MECHANISM→LENS→VOICE shorthand** (see WORK.md `## 2`) — that shorthand is a different, still-unconfirmed thing named by a later task brief; this six-category model is real, dated, established design history that predates it.
FOLLOW-UP: Phase 3 (implementation) not started. No motive sentences finalized for any persona.

## 2026-08-16 — POST-RELEASE FIVE-ARTICLE EVALUATION (separate from the 2026-08-14 article-quality evidence pass)
STATUS: COMPLETE (evaluation run); no report existed in the repo until this pass wrote one from the preserved artifacts
DECISION: 7 generation attempts across 5 distinct stories, on Trident, isolated worktree, exact release `691c365`, real production providers (OpenRouter: opus-4.8/fable-5/haiku-4.5/sonnet-4.6; perplexity/sonar), zero production mutation. Brief-persona ≠ final byline-persona in 5/5 runs with a captured brief. 4/7 runs produced a genuine unsupported-persona-biography attempt (not 5/7 — corrected from an initial miscount); of those 4, 2 were successfully corrected and 2 (runs 05, 07) survived the revision into the final draft — the direct empirical case behind PS1 (above). No preserved literary-quality ranking exists; a "3 STRONG/2 PROMISING" claim is not confirmed by any artifact.
EVIDENCE: `.claude/post-release-five-article-evaluation-2026-08-16.md` (written this pass from `/srv/data/hermes/evaluations/cripminds-five-article-2026-08-16/artifacts/{01..07}/*` on Trident)
CODE: n/a (evaluation, no production code changed by the runs themselves)
SUPERSEDES: nothing — this is a new record, not a replacement for the 2026-08-14 pass.
FOLLOW-UP: a fresh editorial read of the 5 primary drafts if a literary-quality ranking is actually needed.

## 2026-08-16 — PROJECT MEMORY RECOVERY + INSTALLATION
STATUS: INSTALLED
DECISION: `.claude/WORK.md` established as canonical current-state file (existing `.claude/current-work.md` does not cleanly serve that role — 266KB append-only diary — marked superseded, not deleted). `.claude/LOGBOOK.md` (this file) established as canonical chronological history. `.claude/CONTEXT.md` (already the natural session-entry file, matching this user's own global fallback convention) given a pointer banner to both. No existing WORK.md/LOGBOOK.md found prior to this entry.
EVIDENCE: this file + `.claude/WORK.md`
CODE: commit `ed741bb`
FOLLOW-UP: maintenance rule now in force — see WORK.md header. Post-installation review (below) found several material chronology/evidence errors in this pass's content — architecture kept, content corrected.

## 2026-08-16 — PM1.1 CANONICAL CORRECTION PASS
STATUS: CORRECTED
DECISION: The WORK/LOGBOOK architecture from the entry above was correct and is kept unchanged. Several content errors from that first pass are corrected in this entry's sibling entries above: (1) the 2026-08-16 five-article evaluation was wrongly declared nonexistent — it exists on Trident, now documented in `.claude/post-release-five-article-evaluation-2026-08-16.md`, with two of its own headline counts (5/5 not 4/4 brief-mismatches; 4/7 not 5/7 fabrication attempts) corrected against the raw artifacts. (2) The persona target architecture (CORE PERSON/PERCEPTUAL ENGINE/MOTIVE/AFFINITY/RISK/TEXTURE) was real, dated 2026-08-10 design history that had been silently dropped from `current-work.md`'s lean rewrite — recovered from commit `b2773c8`, not invented. (3) "Reached by Boat or Plane"'s plan/persona divergence, previously marked UNVERIFIED, is now CONFIRMED via a direct query against Trident's production `engagement.db`. (4) PS1 and LPF1 were incorrectly conflated as one combined closure — split into two distinct, correctly-labeled entries; a third label, P1, remains separate again. (5) RL-2026-002 was wrongly recorded as "frozen, never published" — an uncommitted `status_correction_2026-08-14` annotation already sitting in the working tree (matched on Trident) shows it was published via the admin UI on 2026-08-13. (6) SHA reporting split into `ORIGIN_MAIN_HEAD`/`TRIDENT_DEPLOYED_HEAD`/`LAST_PRODUCTION-CODE_RELEASE`/`LAST_MEMORY_RECONCILIATION_COMMIT` so a docs-only commit is never again read as a production-code change. (7) GENERATE→MATERIALIZE terminology confirmed with exact source quote (`.claude/cripminds-publication-model-v1-2026-08-14.md`, git branch `publication-model-v1-2026-08-14`, never merged to main). (8) Whitepaper "CripMinds: Reclaiming Ways of Knowing v0.2" searched exhaustively (full repo history, all branches, Trident, Google Drive) and NOT located — recorded as a gap, not fabricated.
EVIDENCE: this file's corrected entries above; `.claude/WORK.md` (corrected); `.claude/post-release-five-article-evaluation-2026-08-16.md` (new)
CODE: commit (this correction pass — see WORK.md `## 3` for exact `LAST_MEMORY_RECONCILIATION_COMMIT`)
SUPERSEDES: the PM1-pass content of the "PROJECT MEMORY RECOVERY + INSTALLATION" entry above (architecture, not superseded — only content).
FOLLOW-UP: none of the corrections above required a code, article, or deploy change — documentation/evidence reconciliation only, per instruction.

## 2026-08-16 — PERSONA BRIEF <-> WRITER RECONCILIATION (routing fail-closed)
STATUS: DEPLOYED (current `LAST_PRODUCTION-CODE_RELEASE`, pushed to origin/main, pulled on Trident)
DECISION: OLD — `_fable_editorial_brief` chose a persona freely (mechanism-aware, no rotation awareness at all: `current_agent` was passed but never read inside the function); `generate.py` then ran Fable's own persona choice back through `_balance_agent` (a purely rotation-fairness, mechanism-BLIND check) a SECOND time and, if rotation objected, silently substituted a different persona while every downstream field (angle, correction_moment, resisting_example, cross_cite) stayed exactly as Fable wrote it for the ORIGINAL persona. Confirmed root cause of 5/5 brief-persona/byline mismatches in the 2026-08-16 seven-run evaluation (above) and of "Reached by Boat or Plane"'s plan/byline divergence (Fable planned Maya Flux/mobility-access evidence; final byline Siri Sage/acoustic voice). Directly implicated in 2 of the 4 real unsupported-persona-biography fabrication incidents that evaluation found (runs 05/07) — the writer, lacking the substitute persona's actual canon support for the inherited mechanism, appears to have reached for invented biography to bridge the gap.
NEW — rotation/fairness eligibility (`discovery.py`'s new `_rotation_eligible_agents`, a set-returning sibling of the unchanged `_balance_agent`) is computed BEFORE Fable's decision and passed into `_fable_editorial_brief` as a hard constraint (`eligible_agents=`); Fable must choose persona + mechanism/angle TOGETHER from within that set, and the whole brief is rejected (same fail-closed path as any other schema violation — logged, returns `None`) if the model names a persona outside it. The post-brief silent-override block in `generate.py` is deleted outright, with a defensive invariant check (logs + discards, doesn't crash) in case any future caller ever bypasses the internal one. Invariant now holds structurally for every successful Fable path: `fable_brief["persona"] == agent_name == the persisted plan persona == the byline`. `_balance_agent` itself is unchanged (byte-for-byte) and still used only for the crude keyword-seeded guess before any brief exists, and as the sole fallback persona when a brief is unavailable/discarded.
Explicitly NOT done in this pass (separate scope, matches the audit's own boundaries): story-rejection capability (the pipeline still cannot conclude "no strong CripMinds mechanism, decline"), source/feed concentration, CJ-2 activation, or `persona-architecture-audit.md`'s findings #1 (Siri Sage's prompt-block OWNERSHIP clause) / #2 (global FORBIDDEN_DEFAULTS SUPPRESSION collision with Maya Flux's evidentiary vocabulary) — those remain Phase 3, confirmed not started.
EVIDENCE: this file; `automation/orchestrator/{discovery,generate,llm}.py` (direct code read, before and after); `.claude/post-release-five-article-evaluation-2026-08-16.md` (root-cause evidence); `.claude/persona-architecture-audit.md` finding #3 (prior, separate design note this fix narrowly implements one slice of — NOT the full CJ-2/competitive-reframing replacement it also recommends)
CODE: `cb69c2d` (new regression suite: `automation/persona_brief_writer_reconciliation_test.py`, 20 deterministic checks, zero network cost; `lineage_persistence_test.py` mock signature updated for compatibility)
SUPERSEDES: the silent post-brief `_balance_agent` re-check in `generate.py` (deleted, not merely modified).
FOLLOW-UP: (1) story-rejection capability — real gap, not addressed here. (2) Source/feed concentration — real gap, not addressed here. (3) CJ-2 — remains OFF, evaluation-freeze requirements outstanding, unaffected by this fix. (4) persona-architecture-audit.md findings #1/#2 (ownership clause, suppression collision) — unaddressed, Phase 3. (5) "Reached by Boat or Plane" itself — this fix prevents the SAME routing failure from recurring in future runs; it does not retroactively repair that already-published article, whose remediation decision remains separately pending (see the standing LOGBOOK entry above).

## 2026-08-16 — WHITEPAPER ARTIFACT RECOVERY (correction to PM1.1's "NOT LOCATED")
STATUS: RECOVERED, INSTALLED
DECISION: PM1.1 (above) could not locate "CripMinds: Reclaiming Ways of Knowing" v0.2 after searching the full repo git history (all branches/worktrees, `git log --all -S`), the Trident production checkout, and Google Drive — correctly recorded as a gap rather than reconstructed from memory. The original artifact was never inside any of those three locations: it was created and exported locally, outside the canonical repo, and left in `~/Downloads/` (never committed, never synced to Drive). Recovered from `~/Downloads/cripminds-whitepaper-v0.2.md` (sibling `.docx`/`.pdf` exports of the same batch, all timestamped the same export run, also present there but not committed — Markdown preferred as the durable source per the no-duplicate-copies rule). Identity verified directly against the recovered text before import: frontmatter title/subtitle/author/date/version (`"CripMinds: Reclaiming Ways of Knowing"`, v0.2, 14 August 2026) match exactly; all five core doctrine anchors named in the recovery request (disabled perceiving as world-knowledge, not-ordinary-journalism, not-persona-imitation, Jascha-archive-as-compass vs. disability-scholarship-as-epistemic-grounding, the engineering-restraint stopping rule) are present, verbatim in several cases; the document is structurally complete (Abstract through §19 + a "Source and evidence note" closing section, no truncation). A second, unversioned candidate found in the same search (`~/Downloads/cripminds-reclaiming-ways-of-knowing.md`, no `version:` frontmatter field, different subtitle/structure) was examined and set aside as an earlier/alternate draft, not the v0.2 artifact requested — not imported. Installed as a byte-for-byte verbatim copy (confirmed via `diff`), no editorial changes, no PDF/DOCX binaries committed. `.claude/WORK.md`'s document-index row and `## 1` doctrine section updated to point to it (pointers only — the doctrine bullets already there were checked against the recovered text and are accurate quotes/paraphrases, not rewritten).
EVIDENCE: this file; `.claude/WORK.md` (`## 1`, document index); `docs/whitepaper/cripminds-whitepaper-v0.2-2026-08-14.md` (the recovered artifact itself, moved here from `.claude/` — see the directory-preservation follow-up entry below)
CODE: n/a (documentation-only; no `automation/` behavior changed)
SUPERSEDES: nothing in PM1.1's search process or reasoning — that pass's "NOT LOCATED" conclusion was correct given what was actually searched; this entry only adds the fact that the artifact has since been found, and where.
FOLLOW-UP: none. This is a recovered artifact, not a newly authored or reconstructed whitepaper.

## 2026-08-16 — WHITEPAPER DURABLE DIRECTORY / EXPORT PRESERVATION (follow-up to WR1)
STATUS: PRESERVED, MOVED
DECISION: Two remaining dependencies on non-durable locations from the WR1 recovery (above) are closed. (1) The tracked canonical Markdown lived loose at `.claude/cripminds-whitepaper-v0.2-2026-08-14.md`, not in a dedicated whitepaper directory — moved via `git mv` (0 insertions/0 deletions, confirmed a pure rename) to `docs/whitepaper/cripminds-whitepaper-v0.2-2026-08-14.md`; still the single tracked copy, no duplicate Markdown created. (2) The whitepaper's durability still depended on `~/Downloads/`, which is not a preservation location — the full original export batch (`.md`/`.pdf`/`.docx`, all from the same 2026-08-14 14:57 export, confirmed by matching file sizes) is now copied (not moved — Downloads originals left untouched) to `~/code/cripminds-preservation/whitepaper/v0.2/`, outside the Git repository, archival only. SHA-256 confirms three-way byte-identity: Downloads originals == preservation archive == tracked repo Markdown, for the `.md` file; `.pdf`/`.docx` sizes match their Downloads originals exactly (54,585 / 197,534 bytes). `.claude/WORK.md`'s document-index row, its `## 1` pointer, and this file's own prior entry's EVIDENCE line were updated to the new `docs/whitepaper/` path; `.claude/CONTEXT.md` and the rest of the indexed docs had no reference to the old path to begin with (checked directly, zero hits). WORK.md is written so ordinary project use never requires the local preservation directory to be mounted — it is named only as an archival pointer, not a dependency.
EVIDENCE: this file; `.claude/WORK.md` (document index + `## 1`); `docs/whitepaper/cripminds-whitepaper-v0.2-2026-08-14.md` (moved file); `~/code/cripminds-preservation/whitepaper/v0.2/{cripminds-whitepaper-v0.2.md,.pdf,.docx}` (local archive, not in Git)
CODE: n/a (documentation-only; no `automation/` behavior changed; no binaries or local-archive path committed to Git)
SUPERSEDES: the `.claude/cripminds-whitepaper-v0.2-2026-08-14.md` path referenced by the entry immediately above — same file, same content, new location.

## 2026-08-16 — PROJECT MEMORY PHASE 3: DURABLE PROJECT MAP + GENERATED MANIFEST
STATUS: INSTALLED
DECISION: Following the preservation sequence PI2 (full audit) → PP1 (Mac-side durable preservation of unique history/evidence) → PP2 (Mac+Trident cross-machine redundancy, both fully verified, no removals), this pass installs a fourth, distinct file: `.claude/PROJECT-MAP.md` — physical topology only (worktrees, branches, evidence-store locations, lifecycle status), explicitly not current-truth (`WORK.md`) or chronology (this file), and pointed to from both. A read-only generator, `scripts/cripminds_project_inventory.py`, produces `.claude/project-manifest.json` (git/worktree/branch/preservation-ref state, distinguishing `untracked_status_entries` from `untracked_recursive_files` so the two different counts reported across PI2/PP1 are never again read as contradictory); run twice, confirmed deterministic apart from `generated_at`, zero filesystem/git mutation, degrades gracefully with `--no-trident` if SSH is unavailable. All 21 registered worktrees classified using direct Git evidence (ancestor checks, patch-id comparisons against `main`, off-main-doc cross-references) — 5 MERGED→SAFE-TO-ARCHIVE-LATER, 2 SUPERSEDED (patch-identical content already on `main` under a different commit SHA), 12 PARKED, 1 FROZEN (Story Rejection, unchanged), 1 ACTIVE (`main` itself). The `.claude/cripminds-publication-model-v1-2026-08-14.md` broken reference is NOT repaired here — its off-main blob was verified byte-identical to the PP1-preserved export and recorded in `PROJECT-MAP.md` as an off-main canonical historical document pending a separate import (Phase 3B). Cleanup remains NOT authorized by this pass.
EVIDENCE: this file; `.claude/PROJECT-MAP.md`; `.claude/project-manifest.json`; `scripts/cripminds_project_inventory.py`; `~/code/cripminds-preservation/PRESERVATION-MANIFEST.json` (cross-referenced, not duplicated)
CODE: this commit (docs/tooling-only; no `automation/` behavior changed)
SUPERSEDES: nothing — additive navigation layer only.
FOLLOW-UP: Phase 3B (import the publication-model-v1 doc to `main` as its own isolated commit) and the database-backup follow-up from PP1/PP2 both remain open, tracked in `PROJECT-MAP.md`'s "Open structural issues".
FOLLOW-UP: none. Both the tracked copy and the original export batch now live in durable, non-`Downloads` locations.

## 2026-08-16 — PROJECT MEMORY PHASE 3B: PUBLICATION MODEL DOCUMENT RECOVERY
STATUS: RESOLVED
DECISION: The broken `WORK.md` reference flagged in Phase 3 is closed. `.claude/cripminds-publication-model-v1-2026-08-14.md` was extracted via `git show` from branch `publication-model-v1-2026-08-14` (never checked out) and installed verbatim — no reconstruction, no summarization, no editorial changes — at the same canonical path `WORK.md` already cited. SHA-256 (`c8edb91c...`) confirmed identical across three copies: the live branch blob, the PP1-preserved export at `~/code/cripminds-preservation/documents/off-main-2026-08-16/`, and the newly installed `main` copy. `WORK.md`'s document index (`## 8`) now lists it as **HISTORICAL — CONCEPTUAL/ARCHITECTURAL EVIDENCE**, explicitly not current production configuration and not proof the old branch's architecture is live. `PROJECT-MAP.md`'s branch table and "Open structural issues" updated to reflect the recovery. The historical branch `publication-model-v1-2026-08-14` itself remains PARKED — importing one document does not change a branch's lifecycle status. No production behavior changed; `automation/` untouched; Story Rejection (`proto/story-rejection-v1` @ `37432b9`) untouched, still FROZEN — AWAITING PRFV1; Trident production checkout untouched (no pull).
EVIDENCE: this file; `.claude/WORK.md` (`## 8`); `.claude/PROJECT-MAP.md`; `.claude/cripminds-publication-model-v1-2026-08-14.md` (the recovered file itself); `.claude/project-manifest.json` (regenerated, `broken_document_references` no longer lists this file)
CODE: n/a (documentation-only; no `automation/` behavior changed)
SUPERSEDES: Phase 3's "not repaired here, deferred to Phase 3B" note — that deferral is now resolved.
FOLLOW-UP: none for this document. Database-backup follow-up and the `pixel-validation/control` divergence remain open, tracked in `PROJECT-MAP.md`.

## 2026-08-17 — STORY REJECTION V1: PRFV-M1 ACCEPTED (RG1), RELEASE REVIEW PASSED
STATUS: RELEASE CANDIDATE, NOT YET DEPLOYED
DECISION: PRF1's routing invariant (Fable persona == writer `agent_name` == persisted `article_plans` persona == final byline, no post-Fable substitution) was validated three separate times before this pass: (1) a 2026-08-16 09:00 natural scheduler run was forensically proven, via commit-timestamp/reflog evidence, to have executed under `691c365` — over 3.5 hours *before* the PRF1 fix (`cb69c2d`) was even committed, so it could not and did not test PRF1 (**PRFV-N0**); (2) a same-day manual invocation of the exact scheduled wrapper hit the daily dedup gate, since today's article already existed (**PRFV-M3**, no Fable path exercised); (3) a deliberate post-midnight (2026-08-17 00:02 CEST) manual invocation of the identical, unmodified `cripminds-daily.sh article` wrapper — real providers, real DBs, real lock, real safety pipeline, zero forced/mocked paths — ran the full pipeline for real and confirmed the invariant holds end-to-end (Fable persona `Pixel Nova` == writer == persisted plan == byline, no post-Fable substitution, grounding hashes matched planner→writer→reviewer→executor) (**PRFV-M1**). The following real 09:00 cron fired normally and correctly dedup-skipped (today's slot was already occupied by the 00:02 run) — this is scheduler health, not a PRF1 gap, and does not produce an independent natural-run confirmation (**PRFV-N1 unavailable**). A direct code check (grep for invocation-source branching in `production_orchestrator.py`/`generate.py`/`discovery.py`) found no cron-vs-manual distinction anywhere in the pipeline — the routing logic under test cannot observe who started the process. On that basis, RG1 was accepted: PRFV-M1 alone satisfies the Story Rejection release gate; waiting for a calendar-day natural run would add ceremony, not evidence. A full adversarial release review followed: the prototype (`proto/story-rejection-v1` @ `37432b983093274224a49cd1e2f820d41aa32bb6`, left untouched as preserved evidence) was cherry-picked (`git cherry-pick -x`, zero conflicts, byte-identical `automation/` content) onto a fresh `release/story-rejection-v1` branch/worktree built from current `main` (`ba64e77` at the time) — candidate SHA `cff6dbc3140a5dea4ea6c2536ba664c633239995`. Re-verified from scratch, not deferring to the prior prototype review: the Layer-1 (source-commissionability, all four lenses, no persona-biography/current-state lore)/Layer-2 (PRF1-eligible execution) separation holds with five outcomes staying distinct (commissionable+write, editorial decline, commissionable+no-eligible-carrier, defer/insufficient-evidence, technical failure); both previously-identified defects are genuinely fixed in the real code paths production executes (not merely in an unreached helper) — contract-version-aware decline exclusion is present in `get_news_seed`'s two priority queries, `extract_top_angles`, and `sample_shadow_candidates` (verified against isolated SQLite fixtures: a current-contract decline is excluded from real selection SQL, a stale-contract decline is correctly reconsidered and re-offered, restart-after-decline persists the exclusion with full structured JSON/timestamp/contract-version/source-hash); and `eligible_execution_possible=False` returns via a dedicated `_handle_no_execution_run` short-circuit that never assigns a substitute persona, never runs the writer, and never persists a decline record. Source-authority gating confirmed: `fallback_summary`/`none`/truncated/ungrounded-anchor sources cannot decline; `fixture`-origin is real in `validate_source_decision` but traced to be reachable only from `automation/phase_probe.py`, a standalone dry-run harness never imported by `production_orchestrator.py` — unreachable from real production. DB migration confirmed additive/idempotent (fresh DB, legacy pre-SR1 DB with data preserved through migration, repeated re-init all clean) with no overload of `used`/`used_date`/`angle_checked`. All 28 `automation/*_test.py` files pass (27 direct-script + `snapshot_test.py --check`, zero drift), `py_compile` clean on all changed files, orchestrator instantiates. One minor, non-blocking robustness gap noted for future hardening, not a release blocker: `eligible_execution_possible` is read via `.get(key, True) is False`, so a hypothetical non-boolean JSON value from the model (e.g. a stringly-typed `"false"`) would not trigger the no-execution path — bounded in practice by the existing eligible-persona-membership check downstream, and covered by the prototype's own test case N for the realistic (named-persona) variant of this scenario, but the type itself is unvalidated on the commission branch unlike the heavily-validated decline branch.
EVIDENCE: this file; `.claude/PROJECT-MAP.md` (Story Rejection status updated to RELEASE CANDIDATE — PRFV-M1 GATE SATISFIED); `~/code/disability-collective-ai-story-rejection-release` (worktree, branch `release/story-rejection-v1`, commit `cff6dbc3140a5dea4ea6c2536ba664c633239995`); `~/code/disability-collective-ai-srv1` (original prototype, untouched, `37432b9`); local test output (28/28 automation test files pass; isolated SQLite migration/decline-semantics fixtures, not committed — throwaway `/tmp` files)
CODE: local-only. `release/story-rejection-v1` branch/commit exists solely in the new local worktree; NOT merged into `main`, NOT pushed to `origin`, NOT deployed to Trident, NO production DB mutated, NO production generation run in this pass.
SUPERSEDES: nothing — Story Rejection's prior "FROZEN — AWAITING PRFV1" status is updated, not erased; the prototype worktree/branch/SHA remain intact as the original evidence.
FOLLOW-UP: an explicit human release decision (merge to `main` / push to `origin` / deploy to Trident) is still required before Story Rejection reaches production — this pass produced a verified release candidate, not a deployment. The database-backup and `pixel-validation/control` divergence follow-ups remain open, tracked in `PROJECT-MAP.md`.

## 2026-08-17 — STORY REJECTION V1: MERGED TO MAIN, DEPLOYMENT PENDING
STATUS: MERGED TO MAIN, NOT YET DEPLOYED
DECISION: Following owner authorization to release the reviewed candidate, the release candidate (`cff6dbc3140a5dea4ea6c2536ba664c633239995`, released review SRR1) was cherry-picked (`git cherry-pick -x`) onto canonical `main` (candidate's base `ba64e77` had advanced only by one docs commit, `1f0de4f`, with zero `automation/` overlap — confirmed via `git diff --name-status` before integrating) producing commit `275470c`. Post-merge `automation/` content re-diffed directly against `cff6dbc` and confirmed byte-identical — no reimplementation, no opportunistic changes. Full pre-push gate re-run on integrated `main`: all 28 `automation/*_test.py` files pass, `snapshot_test.py --check` reports zero drift, `py_compile` clean on all changed files, orchestrator imports successfully. Per the release principle, the known non-blocking `eligible_execution_possible` type-validation gap was deliberately NOT patched in this pass. `proto/story-rejection-v1` (`37432b9`) and `release/story-rejection-v1` (`cff6dbc`) and their worktrees remain preserved, untouched, not deleted — release evidence.
EVIDENCE: this file; `.claude/PROJECT-MAP.md` (Story Rejection status updated to MERGED TO MAIN — DEPLOYMENT PENDING); `git log` on canonical `main` (`275470c`); local pre-push test output (28/28 pass, snapshot clean, py_compile clean, orchestrator import OK)
CODE: `275470c` on canonical `main` (local at time of this entry — origin push and Trident deployment are separate, subsequent steps of this same release task, recorded in their own entry once confirmed).
SUPERSEDES: nothing — this is the next step after the prior entry's release-candidate review, not a correction of it.
FOLLOW-UP: origin push, Trident deployment, production DB migration verification, and a read-only production smoke check remain to be completed and recorded before Story Rejection can be marked RELEASED.

## 2026-08-17 — STORY REJECTION V1: RELEASED (DEPLOYED TO TRIDENT)
STATUS: RELEASED
DECISION: Completed the remaining release steps from the prior entry. Docs commit `9e1c81d` (Story Rejection merge-status update) pushed to `origin/main` (`ba64e77..9e1c81d`, no force). Trident production checkout fast-forwarded via its own normal `git pull origin main` (no manual file copy) — resulting Trident HEAD `9e1c81d` confirmed equal to the new origin/main SHA. Before touching the production DB, resolved a naming ambiguity flagged since the PI2 audit ("DB naming collision across 3 paths"): `news_fetcher.py`'s own `DB = REPO / "disability_findings.db"` constant resolves to the **Trident repo root** file, which does hold `news_seeds` (1116 rows) — this is a genuinely different file from `automation/disability_findings.db` (holds only `link_pool`) and from `rss_disability_findings.db` (holds `article_beats`/`findings`/`link_pool`, no `news_seeds`). Not a collision after all — three distinct files that happen to share a naming pattern. Migrated the correct file via the real, already-tested idempotent path: invoked `news_fetcher.init_db(conn)` directly against `disability_findings.db` (no network fetch, no article generation — `init_db` is a pure schema-init call, separate from `main()`'s feed-fetching). Schema before: legacy pre-SR1 shape (already had `angle_checked` from an earlier migration, lacked all 5 Story Rejection columns). Schema after: 5 new columns added (`declined INTEGER DEFAULT 0`, `declined_date TEXT`, `decline_json TEXT`, `decline_schema_version TEXT`, `declined_source_hash TEXT`). Row count verified identical before/after: 1116 total, 1019 unused / 97 used — zero data loss, zero destructive change, purely additive `ALTER TABLE ADD COLUMN`. Read-only production smoke check (no Fable/provider calls, no article generated): orchestrator imports cleanly; `STORY_REJECTION_CONTRACT_VERSION = "sr1"` present in both `grounding.py` and `news_fetcher.py`; the real contract-version exclusion SQL clause (`NOT (declined = 1 AND decline_schema_version = ?)`) executes without error against the migrated schema; PRF1's authoritative-persona reconciliation code confirmed present in `generate.py`; CJ2/L2 env vars confirmed absent; deployed `automation/` content re-diffed against `cff6dbc` and confirmed byte-identical. No candidate-2 retry exists by design; future runs may legitimately decline, find no eligible carrier, defer, or write an article — "no article today" is not a failure signal.
EVIDENCE: this file; `.claude/WORK.md` (Story Rejection marked live in production); `.claude/PROJECT-MAP.md` (status RELEASED, DB-naming-collision note resolved); `git log origin/main` (`9e1c81d`); Trident `git rev-parse HEAD` (`9e1c81d`); Trident `disability_findings.db` schema dump before/after; Trident smoke-check command output (this session)
CODE: `9e1c81d` pushed to `origin/main`; Trident deployed at `9e1c81d` via normal `git pull`. Production DB schema at Trident's `disability_findings.db` migrated additively (see above) — this is the first real production-state change from this release.
SUPERSEDES: the prior entry's "MERGED TO MAIN, NOT YET DEPLOYED" status — deployment is now complete.
FOLLOW-UP: none blocking. Non-blocking: `eligible_execution_possible` type-validation hardening (noted in release review, deliberately deferred); database-backup method still needed for `disability_findings.db`/`automation/engagement.db` (separate, long-standing follow-up); `pixel-validation/control` divergence (separate, long-standing, low priority); Story Rejection prototype branch itself still has no remote copy (proposed ref awaiting owner approval, unrelated to this release).

## 2026-08-17 — STORY REJECTION V1.1: FALSE-COMMISSION FIX RELEASED (DEPLOYED TO TRIDENT)
STATUS: RELEASED
DECISION: The first real V1 commission ("7,000 Rooms With No Door For Anyone", 2026-08-17) was forensically classified **FC2 — false/permissive commission** (SRF3): `validate_source_decision()` validated DECLINE authoritatively but let COMMISSION `return True` trivially (zero grounding fields even solicited), and the source was a Techmeme aggregator page fetched whole, letting an unrelated neighboring lawsuit story contaminate the evidence and contribute the article's title motif. Per explicit instruction this was observed, not patched, at the time (N=1, Story Rejection V1 stayed live and unpatched). A follow-up V1.1 fix chain closed both defects on branch `fix/story-rejection-v1-1-grounding`: (1) `d2821cf`/`a5988dc` added deterministic commission grounding (origin/truncation/verbatim-anchor/mechanism-tied-to-anchor/boolean-type gates in a new `_validate_commission_grounding()`), per-item aggregator isolation (`discovery.py`/`news_fetcher.py` recover `underlying_url` scoped to the selected RSS item, never fetch the whole aggregator page), a new `source_decision: "defer"` outcome so bad commission evidence is never silently persisted as an editorial decline, `underlying_article_url` source-lineage persistence, and provider-lineage logging (`requested_model`/`actual_model`/`fallback_used`). (2) An adversarial re-review then proved this deterministic layer alone was still insufficient: constructing a **real, verbatim-grounded anchor** + an explanation that **quotes it** + an **invented, factually-unsupported mechanism** (the exact "7,000 Rooms" pattern: GDP/construction facts → invented raised-floor/cable-trough claims) passed the live, unmodified validator (`ok=True, code="commission"`) — proving "anchor exists" and "anchor is quoted" is not the same as "anchor supports the mechanism." (3) `d0204aa` added `_verify_commission_mechanism_support()`, a narrow, separately-invoked, freshly-prompted semantic verifier (inputs: source text + anchor + mechanism + explanation only; no persona biography, no web, no downstream article) whose only valid pass condition is an unambiguous `SUPPORTED` token — UNSUPPORTED, UNCERTAIN, and any provider failure/timeout/malformed reply all fail closed to `defer`, never to decline or a silent write. An adversarial revert proved the gate load-bearing: disabling only this gate let the exact attack through to commission again; restoring it returned the suite to green. A final adversarial release review (SR11R1) re-verified the complete two-fix diff, the parser's exact-token strictness against 14 adversarial inputs (only unambiguous `SUPPORTED` variants pass), verifier/Layer-1 source-body identity (same `evidence_packet["source_text"]` object, no independent re-fetch), decline/PRF1 non-regression, and DB-migration safety against isolated fixtures — passing, with one honestly-recorded caveat: only one of five planned adversarial reverts (disabling the semantic gate itself) was freshly re-executed against `d0204aa` in that review; the other four relied on code inspection and earlier-phase evidence. The owner was informed of this narrower coverage and explicitly chose to proceed with release. Release integration used a fast-forward merge rather than a cherry-pick, since `fix/story-rejection-v1-1-grounding` turned out to be a direct, undiverged, 3-commit linear descendant of `main` — the cleanest possible auditable method, guaranteeing the integrated tree is `d0204aa` byte-for-byte with no rewrite risk. Canonical `main` fast-forwarded `b925a5d..d0204aa`, pushed to `origin/main`, no force. Trident deployed the same way (`git pull`, fast-forward, no manual file copy); all five changed production files (`grounding.py`, `llm.py`, `discovery.py`, `generate.py`, `news_fetcher.py`) hash-verified byte-identical between Trident and the reviewed candidate. Before the DB migration, re-confirmed (not merely trusted from V1's release note) that `news_fetcher.py`'s own `DB` constant still resolves to the Trident repo-root `disability_findings.db`. Ran the same already-tested `news_fetcher.init_db()` additive path: `underlying_article_url` column added, all 5 existing Story Rejection V1 decline columns intact, row count unchanged at 1116 before/after (98 used / 1018 unused, unchanged), re-running the migration confirmed idempotent (no duplicate-column error). Read-only production smoke check confirmed orchestrator instantiation, presence of `_verify_commission_mechanism_support`, `_validate_commission_grounding`, `_handle_defer_run`, aggregator-domain logic, `underlying_article_url` schema, the PRF1 persona-assignment marker, and the `eligible_execution_possible` boolean check, plus CJ2/L2 env vars confirmed absent — all without any live provider call or article generation. The defining release-gate attack (real anchor + invented mechanism + verifier UNSUPPORTED) was re-verified through the actual `_run_production_automation_locked()` dispatch path on the deployed code during this release (not merely re-cited from the earlier isolated-function test), confirming DEFER with zero writer/article/plan/decline/mark-used side effects. No production generation, no live Fable/Opus call, performed at any point in this release or its verification.
EVIDENCE: this file; `.claude/WORK.md` (Story Rejection marked V1.1, live in production); `.claude/PROJECT-MAP.md` (Story Rejection V1.1 section added, causal sequence preserved alongside V1's); `git log origin/main` (`d0204aa`); Trident `git rev-parse HEAD` (`d0204aa`); Trident file-hash comparison output (5/5 identical); Trident `disability_findings.db` schema dump before/after; Trident smoke-check command output; a standalone real-dispatch verification script run against the deployed code (this session)
CODE: `d0204aa` pushed to `origin/main` (fast-forward from `b925a5d`); Trident deployed at `d0204aa` via normal `git pull`. Production DB schema at Trident's `disability_findings.db` migrated additively (see above) — the only real production-state change from this release.
SUPERSEDES: nothing about V1's own release record — this is an addition to the causal sequence (V1 → SRF3 finding → V1.1 fix → V1.1 release), not a correction of the prior entries. Story Rejection's live-in-production status continues uninterrupted; V1.1 replaces V1's commission-validation behavior only.
FOLLOW-UP: none blocking. Non-blocking, carried forward: database-backup method still needed for `disability_findings.db`/`automation/engagement.db`; `pixel-validation/control` divergence, low priority; Story Rejection prototype branch (`proto/story-rejection-v1`) still has no remote copy, proposed ref awaiting owner approval; Atom-feed aggregator underlying-URL extraction not implemented (explicit scope limit, not a blocker — the only known real aggregator, Techmeme, is RSS 2.0); reverts B–E of the final adversarial release review were not freshly re-executed against `d0204aa` (see decision text above) — worth a fresh full five-revert pass if V1.1 is touched again before more natural production evidence accumulates.

## 2026-08-17 — ARTISTIC RESET AR1: DISABILITY AS EPISTEMIC ENGINE, NOT ARTICLE SUBJECT (RESEARCH/DESIGN ONLY, EXPLICITLY DEFERRED FROM STORY REJECTION V1.1)
STATUS: SYNTHESIS COMPLETE, EXPERIMENT DESIGNED, NOT RUN
DECISION: Separate from and does not touch Story Rejection V1.1 (`d0204aa`/`9502d10`, released same day, above) — this is a pure artistic-research pass, explicitly scoped to exclude production prompts/code/personas/routing/DBs and article generation. Read both the canonical whitepaper (`docs/whitepaper/cripminds-whitepaper-v0.2-2026-08-14.md`) and an earlier v0.1 draft in full; both independently state the target doctrine ("the lens must be causally necessary but narratively optional") in terms close to or identical with the task's own framing — no doctrinal conflict found between whitepaper and the live `generate.py` AUTHOR RULE block, which already states nearly the same thing. Close-read all four supplied production articles (`~/Downloads/cripminds-article-evolution/`) against the whitepaper's own tests: two (persona bylines Maya Flux "Sniff It Out...", Pixel Nova "Galaxy H1...") are clean epistemic-engine cases whose final subject is the world object, not disability; one (Maya Flux, "7,000 Rooms...") drifts toward stating the literal forbidden thesis in its closing paragraphs and carries a wedding/three-steps autobiographical scene reused **near-verbatim** from the other Maya Flux article in the sample — direct empirical evidence for `persona-architecture-audit.md`'s Finding #4 concern that a persona's fixed `WOUND` material can function as a stock, always-available attractor regardless of whether the specific source material summoned it. Cross-referenced this against a rigorous, evidence-graded audit of Jascha's real 2013 Rietveld thesis and correspondence (`CripMinds_Deaf_Persona_Evidence_Audit.md`, supplied this session) establishing exactly what is authorized-real vs. invented in Pixel Nova's biography — the strongest sample article's central mechanism (interpreter-lag/sequence-vs-simultaneity) maps onto that audit's Grade-A evidence exactly, confirming the whitepaper's own testimony principle empirically rather than only in theory. Classified four production mechanisms as likely drivers of subject-drift from direct code reading, none touched: the `disability_angle` discovery-stage pre-framing pipeline (`news_fetcher.py`/`discovery.py`, computes and injects a single named "angle" before the writer engages the source at all), `_extract_persona_wound`'s fixed always-available injection (`generate.py`), keyword/ownership persona routing (`persona-architecture-audit.md` Findings #1/#3), and FORBIDDEN DEFAULTS colliding with Maya Flux's real evidentiary vocabulary (Finding #2). Designed but did not run: a Silent-Lens A/B experiment (Doctrine A = current unmodified prompt; Doctrine B = a canon-tested instruction that keeps first person and disability-naming allowed but forbids identity-announcement-before-discovery), reusing the already-validated freeze/triple-hash-verify discipline from `why-we-write-2026-08-10.md` and explicitly requiring sources be hand-picked rather than drawn through the `disability_angle` pipeline (which would bias selection toward exactly the legible-lens shape under test); a blind review rubric extending WHY WE WRITE's validated W/G/K/D scale with one new axis (S — subject drift); a surface-removal test (strip identity-announcement sentences only, blind-rescore, check whether the mechanism survives); and a same-source/four-engine probe — not a new idea, the concrete instance of a probe `persona-architecture-audit.md` already named as deferred future work. Explicitly declined to engineer anything from this pass (no gates, scorers, word bans, quotas, or routing changes) per the whitepaper's own stopping rule and this repo's shadow-only discipline for soft-judgment questions.
EVIDENCE: `.claude/experiments/artistic-reset-ar1-2026-08-17.md`
CODE: none (research/design only; no prompts, personas, routing, DBs, or articles touched)
SUPERSEDES: nothing — orthogonal to Story Rejection V1/V1.1's factual-integrity/commission-validation lineage above; this concerns editorial/artistic quality of already-eligible, already-commissioned articles, not source-eligibility gating.
FOLLOW-UP: run the Silent-Lens experiment (§9 of the linked artifact) once an editor is available to hand-pick non-disability-flagged sources; the same-source/four-engine probe remains queued from the persona architecture audit independent of this entry; no other action authorized by this pass.

## 2026-08-17 — ARTISTIC RESET AR2: SILENT-LENS A/B EXPERIMENT RUN — NO RELIABLE WRITER-DOCTRINE EFFECT FOUND (RESEARCH ONLY)
STATUS: EXPERIMENT RUN, DECISION AR2C
DECISION: Ran the Silent-Lens A/B experiment AR1 designed but did not execute. Built an isolated, standalone harness (`automation/ar2_silent_lens_harness.py`, new file, zero production code/DB touched) that reconstructs the real writer SYSTEM prompt (`llm.py`'s `call_llm_via_openclaw_session`, verbatim) and the real ~120-line invariant USER-prompt instruction block (`generate.py`, verbatim) alongside real `personas.py` AGENTS prompt_blocks, real `persona_canon/*.md`/`persona_state/*.json` files (read-only), and real frozen register/length/article_type constants — swapping only the AUTHOR RULE/FORBIDDEN DEFAULTS paragraph between condition A (unmodified production text) and condition B (AR1's Silent-Lens doctrine). `disability_angle` was omitted from BOTH conditions (not asymmetrically, per AR1's own confound warning), and Fable's editorial-planning stage was skipped for both (a disclosed scope reduction — `generate.py`'s own no-brief code path, exercised identically both ways). Hand-picked 4 real, dated, non-disability-flagged sources across infrastructure/transport, media/consumer-economics, retail/surveillance, and labor/robotics (verified via live web fetch, none overlapping AR1's own four-article sample's domains), one persona per source by affinity (Maya Flux/Zen Circuit/Pixel Nova/Siri Sage). Real model calls: `anthropic/claude-opus-4.5` via direct OpenRouter API using a personal, non-production key (`~/.hermes/.env` — Trident's CLIProxyAPI, the production route, is unreachable from this Mac session and touching it would have meant using production infrastructure for a non-production experiment), identical across all 8 generations, zero fallback. Generated exactly one sample per condition per source (8 articles total, no regeneration of weak results), blinded them to anonymous IDs with a privately-held key, and had 8 independent, freshly-spawned, context-free agents each blind-review exactly one article using AR1's rubric plus a W/G/K/S numeric scale (W/G/K reused verbatim from the already-validated `why-we-write-2026-08-10.md` framework; S — subject drift — new, inverted 1-5). Result: 7 of 8 pieces classified EPISTEMIC ENGINE (1 MIXED-leaning-ENGINE), mean subject-drift 1.75/5 in BOTH conditions, mean composite W+G+K 12.75 (A) vs 12.25 (B) — B won 1 pair (airtrain, marginally), A won 2 (hbomax, warehouse), 1 exact tie (selfcheckout). No pair in either condition landed on disability/accessibility as its final world-object transformation. Surface-removal test found almost no identity-announcement material to strip in either condition (one clean A-vs-B contrast in `selfcheckout`: A disclosed Deafness via a necessary scene-embedded statement, "I signed that I am Deaf," inside a dated 2019 anecdote; B conveyed the same fact entirely through the *De Gebarentaaltolk en Ik* mechanism without ever stating it as a credential — same subject-drift score either way). Autobiography audit: 6/8 pieces used argument-advancing first-person material; the one weak instance (vague, undated "flagged by systems" language) occurred under condition B, not A. Stock cross-source wound-reuse (AR1's original four-article finding, where Maya Flux's wedding scene recurred verbatim across two different sources) could not be tested by this single-persona-per-source design — explicitly disclosed as a design limitation, not resolved either way; within this design, Maya Flux's wedding wound was NOT pulled into either condition for her one source, and Siri Sage's roommate wound was pulled into B but not A for her one source. Causal read: because condition A alone, once `disability_angle` and Fable planning were removed, already performs this close to condition B, the result confirms rather than contradicts AR1's own §13 classification of the AUTHOR RULE block as an "unlikely" primary driver of the original subject-drift symptom — the mechanisms AR1 rated more likely (`disability_angle` pre-framing, cross-source wound-repetition pressure) are exactly what this design excluded from both arms. No production prompt, code, persona, routing, DB, or Story Rejection component touched or reopened.
EVIDENCE: `.claude/experiments/artistic-reset-ar2-silent-lens-2026-08-17.md`; full articles + raw generation records + all 8 review texts + unblinding key in `.claude/experiments/ar2-silent-lens-2026-08-17-articles/`
CODE: `automation/ar2_silent_lens_harness.py` added (new standalone experiment script, not wired into `production_orchestrator.py` or any production entry point; zero production files modified)
SUPERSEDES: nothing — this is AR1's own designed follow-up experiment, not a correction of it; AR1's diagnosis stands and is directly supported by this result.
FOLLOW-UP: next experiment is a `disability_angle`-isolation test (same A doctrine, matched sources, with vs. without a real upstream-computed angle) — the variable this pass deliberately excluded from both arms and now the strongest remaining suspect; second priority is a same-persona/multiple-distinct-sources repeated-run design to test cross-source wound-reuse directly, which an A/B doctrine comparison structurally cannot address. Do not rewrite the live AUTHOR RULE block on the strength of this one n=4 result — no reliable A-vs-B difference was found, so there is nothing here to encode into production prompts.

## 2026-08-17 — ARTISTIC RESET AR2.1: EIGHT-ARTICLE PROVENANCE AUDIT — AR2'S TESTIMONY WAS PARTLY FABRICATED, CAUSAL CONCLUSION STANDS WITH QUALIFICATION (RESEARCH ONLY)
STATUS: AUDIT COMPLETE, DECISION AR21B
DECISION: Read-only forensic re-audit of all 8 AR2 articles against exactly what the writer was given — the frozen source texts in `automation/ar2_silent_lens_harness.py`, each persona's real `persona_canon/*.md` (read in full this pass), and Pixel Nova's stricter `pixel-nova-factual.md` — with no web search used to rescue any claim, per instruction. Built a claim/quote/first-person-event ledger across all 8 pieces (~65 meaningful claims, 9 direct quotations). Finding: **9 unsupported direct quotations** across the 8 articles (2 in `airtrain-A`, 4 in `airtrain-B`, 1 each in `hbomax-A`, `hbomax-B`, `warehouse-A`; 0 in both `selfcheckout` pieces and `warehouse-B`) — invented named or pseudonymized people (a gate agent "Dolores," "Mette," "Marcus," an unnamed bus driver, an unnamed Port Authority spokesperson, a German ex-coworker) given fabricated attributed speech, plus **2 of the 9 attached to apparently-real, non-pseudonymized named public figures** (Kevin Irvine of Riders Alliance; Aimi Hamraie of Vanderbilt) with quotes the writer had no basis for — the single most severe finding, directly matching `generate.py`'s own explicit warning that "a fabricated quote in real quotation marks attached to a real name is the single most exposed factual error this publication can make." Also found 11 fully fabricated first-person events (an EIS-reading session with invented page-count statistics, a three-airport bus-count survey, a Rotterdam self-checkout visit, a 2019 department-store return, a press-office call, etc.) plus 3 softer "canon-consistent general practice, new specific episode" cases for fictional personas (Siri Sage inventing a specific 2016 Rotterdam warehouse visit and a specific "project on industrial acoustics" beyond her canon's general 3-years-field-recording fact) — precisely the failure shape `author-persona-biography-provenance-2026-08-14.md`'s AP1/APE2 closures were built to catch, occurring here unchecked because AR2's harness deliberately ran the raw writer stage only, with no Fable review, `_first_person_contract`, or `find_new_unsupported_specifics` pass (a disclosed AR2 scope reduction, not a new gap). Cross-checked every AR2 blind-review passage specifically praised as load-bearing/evidentiary against this ledger: of 14 checked, 8 were "apparent richness" built on fabricated material (including the single highest score in the whole AR2 dataset, `selfcheckout-A`'s W=5, resting on a fabricated first-person scene for Pixel Nova — the one persona whose authorization standard is real-person evidence with zero editorial-canon safety net), 2 mixed, 4 genuinely earned (notably `selfcheckout-B`'s *De Gebarentaaltolk en Ik* material, Grade-A authorized and correctly used). Traced every fabrication instance against the five candidate prompt pressures: NAMED VOICES ("2-3 real named people... REQUIRED") and SOMEONE ELSE MUST SPEAK ("NON-NEGOTIABLE") are strongly implicated in every fabricated-quote instance; GROUNDING and TEMPORAL ANCHORS are strongly implicated in fabricated first-person events without a second speaker. Critically, both of these rules live in the SHARED invariant instruction block AR2 held identical across conditions A and B — not in the AUTHOR RULE/Silent-Lens block AR2 actually varied — so AR2's own doctrine-comparison conclusion is not differentially confounded (both arms fabricated under the same uncontrolled pressure), even though the absolute "both conditions produced strong work" read is now known to be partly a measurement of shared fabrication rate, not shared quality. Confirmed a direct, explicit contradiction: the writer prompt's NAMED VOICES/SOMEONE ELSE MUST SPEAK language is a hard testimony quota with no zero-testimony escape valve, directly contradicting the whitepaper's own stated doctrine ("testimony is not a quota; it is an argumentative event," v0.1 §6). Also confirmed a second, separate contradiction: the SYSTEM prompt's "strong thesis from sentence one" directly opposes the USER prompt's later "never state it" doctrine and the whitepaper's "don't tell me the insight" north star — currently resolved in practice (every one of AR2's 8 reviews independently reported thesis-by-discovery, not thesis-by-announcement), but a real, unreconciled inconsistency in the prompt text. Designed (did not run): a discovery-motion experiment (condition A unchanged vs. a condition B that removes/reconciles only the strong-thesis SYSTEM clause, the HUMAN THREAD cadence, and the NAMED VOICES/SOMEONE ELSE MUST SPEAK quota, replacing the quota with an explicit zero-testimony-permitted rule — deliberately a removal of compulsion, not a new doctrine layer); six "Unexpected Corners" source archetypes (local currency, neighbor resource dispute, village repopulation, mapping error with physical consequence, a documented neurological-perceptual-change case, a mundane bureaucratic rule with a documented strange outcome) with an explicit small-disturbance-with-hidden-system eligibility test borrowed directly from Story Rejection V1.1's own anchor-vs-mechanism discipline; and a later upstream 2x2 (disability_angle x Fable planning) explicitly sequenced AFTER the discovery-motion experiment, since AR2 removed both variables simultaneously and cannot itself attribute its own improvement to either one. No production prompt, code, persona, routing, DB, or Story Rejection component touched, reopened, or patched — this is diagnostic only, matching the same shadow-only, evidence-first discipline that produced the real AP1/APE2 closures.
EVIDENCE: `.claude/experiments/artistic-reset-ar2-1-provenance-and-discovery-motion-2026-08-17.md`
CODE: none (read-only forensic audit; no articles generated, no provider calls made, no production files touched)
SUPERSEDES: nothing — narrows and qualifies AR2's own conclusion rather than reversing it; AR2's specific doctrine-comparison finding (writer doctrine is not the primary driver of subject-drift) stands, its implicit claim of high absolute finished-work quality in both arms does not survive unqualified.
FOLLOW-UP: run the discovery-motion experiment (this entry's own design) before drawing further artistic conclusions from any future silent-lens variant; any future experiment of this shape must run this same claim/quote/first-person-event provenance ledger against its own outputs BEFORE treating blind review as primary evidence, not as an afterthought correction; the upstream disability_angle x Fable-planning 2x2 remains queued but explicitly ordered after the discovery-motion fix; do not patch NAMED VOICES/SOMEONE ELSE MUST SPEAK/HUMAN THREAD/the SYSTEM-prompt thesis contradiction in live production prompts on the strength of this audit alone — the fix belongs in the designed, not-yet-run, controlled experiment.

## 2026-08-17 — ARTISTIC RESET AR3: TESTIMONY-QUOTA REMOVAL EXPERIMENT RUN — DECISION AR3A (RESEARCH ONLY)
STATUS: EXPERIMENT RUN, DECISION AR3A
DECISION: Ran the three-condition (A/B/C) testimony-compulsion isolation experiment AR2.1 designed. Preflight confirmed AR2.1's commit (`02b4a43`) was already pushed before starting. Held AUTHOR RULE current (not Silent-Lens, per AR2's own finding) and "strong thesis from sentence one" identical across all three conditions, deliberately deferring that contradiction to a later experiment (AR3.1) rather than conflating it with this one. Condition A = current unmodified writer prompt (NAMED VOICES 2-3 required, SOMEONE ELSE MUST SPEAK non-negotiable, original HUMAN THREAD/GROUNDING/TEMPORAL ANCHORS). Condition B = A with NAMED VOICES/SOMEONE ELSE MUST SPEAK replaced by an explicit zero-testimony-permitted rule, HUMAN THREAD/GROUNDING/TEMPORAL ANCHORS untouched. Condition C = B with HUMAN THREAD (both the `llm.py` SYSTEM-prompt restatement and the `generate.py` USER-prompt restatement — reconciling only one would have left the compulsory cadence live), GROUNDING, and TEMPORAL ANCHORS also reconciled against inventing personal material to ground an argument. Used 4 new, real, verified "Unexpected Corners" sources never used in AR1/AR2 (Langenegg's village currency; Goudhurst's HGV sat-nav rerouting; a real Neurocase acquired-synesthesia case report; the Maine Supreme Judicial Court's *Lytle v. Lind* easement ruling), with personas assigned by design before generation — two of four pairings deliberately non-obvious (Siri Sage on the currency story, Maya Flux on the neuroscience case), avoiding the default topic-affinity mapping. Generated all 12 articles (4 sources × 3 conditions, one sample each, `anthropic/claude-opus-4.5` throughout, personal OpenRouter key, zero fallback) via a new standalone harness (`automation/ar3_unforced_human_presence_harness.py`). Ran the AR2.1-style provenance ledger against all 12 RAW outputs BEFORE any blind review, per explicit instruction: condition A carried 3 unsupported direct quotes (a fabricated Tom Standage/Economist citation, a fabricated Brooklyn-painter friend and quote, and the single most severe finding across AR2/AR2.1/AR3 combined — a fabricated named Maine judge, "Justice Andrew Horton," with a fabricated quoted legal holding), 3 unsupported named people, and 4 fully unsupported first-person events; condition B dropped to 0 unsupported quotes, 0 unsupported named people, 1 unsupported first-person event (an invented Utrecht bakery visit) and 1 invented statistic (an invented village population figure); condition C also held at 0/0 on the severe classes but showed 3 softer "canon-consistent general practice, new specific episode" cases (Siri Sage inventing a specific childhood shop-theft accusation beyond her real Leith upbringing; Maya Flux inventing specific sensory details of her real, canon-documented accident; Zen Circuit inventing specific pedestrian-flow-model statistics beyond her real Crossrail employment) plus 1 invented statistic set — meaning the softer embellishment class did not show the same dramatic drop from B to C that the severe class showed from A to B. Blinded all 12 outputs and dispatched 12 independent, context-free reviews (compact finished-work rubric, not the full AR1/AR2 rubric) BEFORE unblinding: composite quality (W+G+K) rose monotonically A (9.25) → B (9.75) → C (10.25), and THIN classifications fell monotonically 2/4 → 1/4 → 0/4 — a genuine, unforced result showing no artistic cost, and a modest gain, from removing the testimony compulsion. Cross-checked blind praise against provenance: `easement-C`'s reviewer explicitly praised the fabricated Crossrail statistics as feeling "earned," and both `easement-A`'s and `goudhurst-A`'s reviewers treated the fabricated Justice Horton and Tom Standage quotes as unremarkable legitimate citation — confirming, as AR2.1 first found, that blind literary review does not reliably catch fabrication dressed as institutional/statistical fact, only the more narratively-convenient kind (which two reviewers did independently flag, in `langenegg-A` and `synesthesia-A`). Also found, independent of condition: all 12 reviews, without exception, judged the piece to "execute" a pre-held argument rather than "discover" one — identical across A/B/C, confirming this is a separate, untouched mechanism correctly deferred to AR3.1. Production-safety fidelity check (running real `_fable_editorial_review`/`_first_person_contract` against these raw outputs) was explicitly NOT executed this pass, per the task's own optional/do-not-force framing — recorded as a valuable, feasible, distinct follow-up. No production prompt, code, persona, routing, DB, or Story Rejection component touched.
EVIDENCE: `.claude/experiments/artistic-reset-ar3-unforced-human-presence-2026-08-17.md`; full articles + raw generation records + all 12 review scores + unblinding key in `.claude/experiments/ar3-unforced-human-presence-2026-08-17-articles/`
CODE: `automation/ar3_unforced_human_presence_harness.py` added (new standalone experiment script; zero production files modified)
SUPERSEDES: nothing — confirms and sharpens AR2.1's diagnosis rather than reversing it. AR2's doctrine-comparison conclusion continues to stand; AR2.1's testimony-quota hypothesis is now the best-evidenced single finding across this whole AR-series.
FOLLOW-UP: AR3.1 (discovery-motion / "strong thesis from sentence one" vs. whitepaper discovery doctrine) is now better motivated than before and should run next, holding the B/C testimony-safe prompt fixed; a small, separate follow-up should test whether repeating the SYSTEM prompt's existing "NEVER invent statistics" rule inside the reconciled GROUNDING block reduces the `easement-C`-style invented-figures pattern; the upstream disability_angle x Fable-planning 2x2 (AR4) remains queued after AR3.1. The condition-B/C NAMED VOICES/SOMEONE ELSE MUST SPEAK rewrite is now a well-tested candidate for an eventual, separately-reviewed production change proposal — not authorized to ship from this entry alone.

## 2026-08-17 — ARTISTIC RESET CONCEPTUAL PRESERVATION NOTE: PERCEPTUAL ENGINES VS. PERSONAS, DISTURBANCE DISCOVERY, SHARED CASE MEMORY (RESEARCH ONLY, ARC1)
STATUS: CONCEPTUAL BRANCH PRESERVED, NOT DECIDED, DECISION ARC1
DECISION: Preserved (did not implement) a post-AR3 conceptual discussion that may materially change CripMinds' future architecture. Core distinction recorded: PERCEPTUAL ENGINE (a portable, disability-derived way of interrogating reality — e.g. Pixel Nova's mediation/timing/sequence engine, Maya Flux's route/friction/promise-vs-delivery engine, Siri Sage's sensory-organization/presence engine, Zen Circuit's classification/threshold engine) may be separable from PERSONA/PERSONAGE (name, biography, wound, voice, state, byline) — working hypothesis only, explicitly not adopted as doctrine. Recorded that the number four has no known artistic or epistemic justification and was an implementation choice carrying substantial secondary machinery (persona balancing, rotation, topic affinity, wound/state maintenance, fictional-history provenance, byline consistency) that `persona-architecture-audit.md` and AR1-AR3 have been auditing piece by piece. Preserved four candidate architectures for a future engine-before-persona experiment: (1) one collective CripMinds mind; (2) the four current personas as-is; (3) the four current perceptual engines stripped of name/biography/wound/state/topic-ownership/voice-mannerism; (4) roughly 8-12 narrower micro-lenses instead of four large characters. Preserved the possibility that authorship/byline could become a late, optional decision made after discovery rather than the first step (world → disturbance → perceptual probes → discovery → research/case retrieval → evidence → form → writer/voice/byline → publication, replacing the current implicit news-story → disability-angle → persona → biography → article shape). Preserved a "disturbance, not topic" discovery principle — the valuable unit may be a fracture inside an ordinary document (a mismatch between official explanation and practical reality, a workaround that became normal, a measurement excluding what it claims to measure, information arriving too late to remain the same information, etc.) rather than a whole story selected for topical interest; noted retrospectively that all four of AR3's own "Unexpected Corners" sources were in fact selected because they already contained exactly this kind of disturbance. Preserved the discovery-evidence-vs-publication-evidence distinction (messy evidence can produce a question; only Story Rejection V1.1's existing, unmodified, unreopened standard can support a published claim). Preserved a shared, mechanism-indexed CASE LIBRARY proposal — real, documented, source-hashed cases retrievable by structural mechanism (circulation, friction, boundary, translation loss, obstruction-as-condition) rather than by topic, entering an essay only when a case genuinely changes the argument (breaks the first explanation, supplies a counterexample, reveals the same mechanism in a different domain) — directly motivated by AR2.1/AR3's empirical finding that mandatory testimony causes fabrication and that removing it cost nothing artistically. Connected this to Bregman structurally (a case already in hand before the argument needs it, not a voice to imitate) and confirmed no whitepaper update is needed now — the tension remains between whitepaper concept and implementation assumption, not a whitepaper failure; a narrow v0.3 clarifying sentence was drafted and explicitly held back pending the engine-before-persona experiment's result. Confirmed via direct comparison that `persona-architecture-audit.md` already began separating engine from biography/affinity and already queued a same-source/four-persona probe, but does not resolve the deeper questions this note raises (whether four is the right count, whether authorship must come first, whether disturbance-level discovery or a case library would outperform the current architecture) — no conflict found between this note and existing canon, so ARC2 (report a conflict) does not apply. Explicitly declared experiment ordering now OPEN rather than automatically continuing AR3.1 → AR4 — recommended (not decided) that an engine-before-persona comparison run next, being cheap (5-6 disturbance fragments, no full essays) relative to its potential to redirect the whole roadmap. No production code, prompts, personas, routing, Story Rejection, or DBs touched; nothing engineered from this note (explicitly listed as not-yet-authorized: new personas/micro-lens routing, a byline system, a collective writer, a case-library database/vector store, a disturbance scraper, a new whitepaper version, a new persona-balancing system, an automatic retrieval stage, another production gate).
EVIDENCE: `.claude/experiments/artistic-reset-concept-perceptual-engines-disturbances-case-memory-2026-08-17.md`
CODE: none (conceptual preservation only; no code, prompts, or articles touched)
SUPERSEDES: nothing — does not alter AR1/AR2/AR2.1/AR3's own findings or decisions, and does not alter `persona-architecture-audit.md`'s FROZEN/carried-forward items; extends open threads those documents already left unresolved.
FOLLOW-UP: experiment ordering (AR3.1, AR4, engine-before-persona comparison, disturbance-mining comparison, case-library shadow prototype) is open and should be decided in a future session by weighing this note against the previously queued AR3.1/AR4 sequence — this entry recommends, but does not commit to, running the engine-before-persona comparison first. None of the five candidate experiments are authorized to touch production; all remain design-only until separately run and reported.

## 2026-08-17 — AR3-B TESTIMONY-QUOTA FIX RELEASED (PRODUCTION); SOFA-ARTICLE PRIORITY EMBEDDED
STATUS: RELEASED, DEPLOYED, DECISION SP1
DECISION: Shipped the smallest production change directly supported by AR3 (decision AR3A, `.claude/experiments/artistic-reset-ar3-unforced-human-presence-2026-08-17.md`, commit `addbfbe`) — condition B's testimony-quota removal only, not condition C wholesale, per explicit instruction. Confirmed the live source of truth first (`automation/orchestrator/generate.py` lines 882/884/885, not `style_rules.py` — grepped and confirmed NAMED VOICES/SOMEONE ELSE MUST SPEAK have never been migrated into that file's `RULES` single-source-of-truth system, and `gate.py` has no deterministic check keyed to their presence, so removing them can't silently break a post-hoc gate). Replaced the three-part mandatory block (`NAMED VOICES: Use 2-3 real named people... REQUIRED`, `SOMEONE ELSE MUST SPEAK — NON-NEGOTIABLE`, `NO INVENTED QUOTES OR OCCASIONS FOR REAL PEOPLE — THIS OVERRIDES THE RULE ABOVE`) with one compact rule, `HUMAN TESTIMONY / NAMED VOICES`: testimony/named people/quotation appear only when supplied evidence contains them and they materially change the investigation; zero of each is explicitly valid; inventing any of it for narrative texture is forbidden; the real-name-fabrication severity warning ("a fabricated quote in real quotation marks attached to a real name is the single most exposed factual error this publication can make, and it is checkable") is carried forward explicitly rather than dropped. `HISTORICAL/BIOGRAPHICAL ANECDOTE TEST` (a separate, valid rule that happened to sit between the two removed blocks) is untouched, byte-identical, left in its original position — a narrower edit than AR3's own experimental harness took (which had also appended a traceability clause to that rule; the production release deliberately did not, per "ONE PROVEN CHANGE" / minimal-diff instruction). Confirmed via direct text comparison that the shipped rule is semantically equivalent to AR3's tested condition-B change on the actual experimental variable (explicit zero-testimony permission + invention ban) — did not rerun the 12-article experiment or another blind review, per instruction. Could not run a live fixture generation to sanity-check the edited code end-to-end (same constraint as AR1-AR3: production's real writer call routes through Trident-only CLIProxyAPI, unreachable from this Mac, and `call_llm_via_openclaw_session`'s own PROVIDERS list has no OpenRouter-direct fallback the way `_call_editorial_model` does) — skipped per the task's own "only if cheap... otherwise skip" allowance. Added two new regression tests to the existing `writer_prompt_test.py` (same real-pipeline-capture-and-abort harness already used by that file, zero network cost): `test_testimony_quota_removed` (old quota language absent, new rule present and permits zero testimony/quotations/named-people, HISTORICAL/BIOGRAPHICAL ANECDOTE TEST/HUMAN THREAD/GROUNDING/TEMPORAL ANCHORS/AUTHOR RULE all unchanged) and `test_system_prompt_thesis_line_unchanged` (static check that "strong thesis from sentence one," which lives in `llm.py`'s SYSTEM string and is never captured by this harness's mocked `call_llm_via_openclaw_session`, was not accidentally touched — that contradiction remains real and is queued as AR3.1, not fixed here). Ran the full existing test suite (`automation/*_test.py`, 28 files) plus `snapshot_test.py --check`: all pass, no drift, including `story_rejection_v1_test.py` (23/23), `story_rejection_v1_1_test.py` (23/23), and `persona_brief_writer_reconciliation_test.py` (PRF1's own invariant) — confirming this release touches nothing outside its stated scope. Committed (`3225ea1`), pushed to `origin/main`, then deployed via SSH + `git merge --ff-only` on Trident's production checkout (`/srv/data/hermes/workspace/disability-ai-collective/`, previously frozen at `d0204aa` since before AR1 — this is the first time any of the AR1-AR3/concept-preservation docs commits reached Trident at all, since none of those tasks authorized a deploy; all landed in this one fast-forward alongside the code fix). Verified `generate.py` and `writer_prompt_test.py` SHA-256-identical between local and Trident post-pull. Ran `writer_prompt_test.py`, `story_rejection_v1_1_test.py`, `story_rejection_v1_test.py`, and `persona_brief_writer_reconciliation_test.py` live on Trident against the deployed code (not just the local copy): all pass. Confirmed `CJ2_INTEGRATION_MODE` unset (OFF, unchanged), cron schedule unchanged, and `disability_findings.db` untouched (mtime predates this release) — no DB migration was needed or performed, no article was generated to "prove" the deploy. Separately embedded a near-term priority shift in `.claude/WORK.md` `## 5a` (new section): near-term artistic target is now "Sofa Articles" (finished pieces worth reading for pleasure, closer to a strong Bregman essay than "a disability article"), with an explicit immediate sequence — ship this fix (done) → build CripMinds Scout (disturbance-fragment discovery, cheap/bounded first version) → generate/read ~3 real finished articles from Scout's leads → add case-memory retrieval only if Scout surfaces a concrete reuse opportunity → return to deeper architecture (Engine Before Persona, AR3.1, AR4, disturbance-mining, case-library) only once finished work makes it consequential. Explicitly NOT cancelled, only deprioritized: all five deeper-architecture threads from the concept-preservation note. Added `## 8` DOCUMENT INDEX rows for AR1/AR2/AR2.1/AR3/concept-preservation (previously undocumented there).
EVIDENCE: `automation/orchestrator/generate.py` (diff: 4 lines removed/changed to 1); `automation/writer_prompt_test.py` (108 lines added, 2 new test functions); `.claude/WORK.md` `## 5a` and `## 8`; full test-suite run output (this session); Trident SHA-256 verification (this session)
CODE: `3225ea1` pushed to `origin/main` (fast-forward from `ab893bf`); Trident production checkout fast-forwarded `d0204aa..3225ea1` via `git merge --ff-only`, verified byte-identical. No DB migration, no schema change, no article generated.
SUPERSEDES: the removed `NAMED VOICES`/`SOMEONE ELSE MUST SPEAK`/`NO INVENTED QUOTES OR OCCASIONS FOR REAL PEOPLE` block text in `generate.py`, which is now historical (see AR2/AR2.1/AR3 for why). Does not supersede or reopen Story Rejection V1.1, PRF1, persona architecture, `disability_angle`, Fable planning, or any FROZEN DECISION in `current-work.md` — none of those were touched.
FOLLOW-UP: next implementation priority is CripMinds Scout (disturbance-fragment discovery → a very small number of grounded leads → real finished Sofa Articles), scoped cheap and bounded — not new routing architecture, not a persona redesign, not a case-library database, not a 12-micro-lens engine, not an autonomous research platform; design/build is separate future work, not started here. AR3.1 (discovery-motion/thesis contradiction), AR4 (`disability_angle` x Fable-planning 2x2), the engine-before-persona comparison, the disturbance-mining comparison, and the case-library shadow prototype all remain preserved, real, queued research questions — deprioritized against Scout, not cancelled, and experiment ordering among them remains open per the concept-preservation note above.

## 2026-08-17 — CRIPMINDS SCOUT V0: DISTURBANCE DISCOVERY → THREE SOFA ARTICLES (RESEARCH/SHADOW ONLY)
STATUS: EXPERIMENT COMPLETE, SHADOW-ONLY, DECISION SV0A (RECOMMENDED, PENDING JASCHA'S READ)
DECISION: Built the smallest possible version of the Scout `## 5a` sequence's item 2 — no database, no vector store, no daemon, no new persona/routing architecture — as a one-shot pipeline: six parallel real-web-search discovery passes across non-disability source categories (court/legal+municipal, trade/business, science/research, design/architecture+technology, culture+specialist, general/local news), deliberately excluding disability/accessibility search terms and the four banned example searches, producing 24 disturbance cards from 24+ real sources read in depth (60+ touched total, non-yielding ones logged for audit trail, not discarded silently). Selected 3 candidates on disturbance strength alone, before any persona discussion, then ran a compact 3-persona perceptual probe per candidate (not the full engine-before-persona experiment from the concept-preservation note — a cheap selection aid only, explicitly not treated as an architectural finding). Ran three parallel deep-research passes to build real, fully-cited evidence packets, which caught two consequential errors in the original disturbance cards before any prose was written: the xAI card's "turbines relocated to reset the compliance clock" hypothesis is not supported by primary documents (real mechanism is continuous addition of new units, not relocation); the ACV-depreciation card had misattributed its most-quoted fragment to the wrong Michigan bulletin number (2024-18-INS vs. the actual 2024-26-INS). Wrote three finished articles (Pixel Nova on camera-trap detection bias; Zen Circuit on xAI's turbine classification; Maya Flux on ACV labor depreciation), each persona chosen by probe result only (Siri Sage was genuinely tried against all three and genuinely lost each time — not omitted by rotation), using the real, current writer doctrine read directly from `automation/orchestrator/generate.py` (AR3-B's zero-testimony-valid rule, AUTHOR RULE, HUMAN THREAD, FORBIDDEN DEFAULTS, no invented statistics) rather than paraphrased from memory. Ran a full provenance audit against the evidence packets before finalizing: found and corrected 6 issues across the 3 drafts (a statistic-conflation in the camera-trap piece, a mischaracterized source type and a corrected hypothesis in the xAI piece, a bulletin-timeline error and an imprecise fraction in the insurance piece) — one evidence-preserving correction pass per piece, no reroll, per the brief's own §14 instruction. Two claims surfaced during research but excluded from the final drafts as insufficiently verified: an unconfirmed "DOJ shields xAI" story, and a cancer-risk statistic that credible reporting could misattribute to xAI's own emissions rather than the pre-existing decades-old neighborhood burden it actually measures. All three personas' authorial grounding traces to existing immutable/factual canon (Pixel Nova's interpreter-lag and unusable-phone-channel facts from `pixel-nova-factual.md`; Zen Circuit's age-19 diagnosis and Maya Flux's immigrant-insurance-navigation background from their own immutable canon files) — no new biography, wound, or memory invented for any persona. One disclosed, unresolved tension: all three selected disturbances are American-sourced, in tension with the writer prompt's "no American laws or institutions" instruction, which reads as aimed at ADA/FEMA-style disability-policy framing (absent from all three pieces) rather than a blanket ban on US-sourced evidence — flagged explicitly rather than silently resolved, consistent with AR3's own precedent of using an American state supreme court case as source material.
EVIDENCE: `.claude/experiments/cripminds-scout-v0-sofa-articles-2026-08-17.md` (full record, per-article provenance notes, verdict); `.claude/experiments/scout-v0-sofa-articles-2026-08-17/` (source pool, 24 disturbance cards, perceptual-probe selection record, 3 evidence packets, 3 final articles)
CODE: none. No file under `automation/`, `_posts/`, `_drafts/`, or any `.db` was created, modified, or touched — confirmed via `git status` before and after this session; all new files are under `.claude/experiments/`.
SUPERSEDES: nothing — this is the first real execution of `## 5a`'s "Immediate sequence" item 2 (Build CripMinds Scout), which was previously only a plan. Does not touch Story Rejection, persona canon, routing, `disability_angle`, or any FROZEN DECISION.
FOLLOW-UP: per `## 5a`'s own sequence, item 3 ("generate/read a very small set (~3) of real finished articles from Scout's leads") is now done; item 4 (case-memory retrieval) remains explicitly conditional on Scout's output making a real reuse opportunity concrete, not automatic — this pass did not surface one, since none of the 24 disturbance cards pointed at a mechanism already documented elsewhere in this project's own corpus. The actual next decision is Jascha's own read of the three articles and a verdict among SV0A/B/C/D (see the full record's "SCOUT V0 VERDICT" section) — not a further engineering step. `## 5a` item 5 (deeper architecture: Engine Before Persona, AR3.1, AR4, disturbance-mining, case-library) remains correctly deprioritized, not started, not touched by this pass.

## 2026-08-18/19 — EDINBURGH ARTICLE FORM CALIBRATION, EVIDENCE PRESERVATION, STATE RECONCILIATION
STATUS: EXPERIMENTS FROZEN · EVIDENCE PRESERVED AND COMMITTED · CANONICAL STATE RECONCILED · NOTHING DEPLOYED
DECISION: Real-material Article Form calibration ran against one frozen Edinburgh commission (Guardian EAF review, source snapshot 8,629 chars, SHA-256 `fee0a03b...`, commission captured 2026-08-18 15:42:44 and revalidated offline after a terminal-punctuation anchor fix — not regenerated). Lineage: original Legacy/Sofa A/B -> B.1 -> B.2 -> B.3 -> B.4 -> FORM-1 -> FORM-1.1. Every iteration grounding FAIL. Article Form (introduced at FORM-1) removed the dead-artist agency/consent attractor that B.3/B.4 produced, improved coherence, and at FORM-1.1 stopped at arrival at 583 words — a 52% length reduction from Legacy's 1227. Grounding did not follow: FORM-1 is 2 unsupported of 6 audited claims, FORM-1.1 is 3 of 5, so FORM-1.1 regressed on unsupported proportion. This is explicitly NOT monotonic improvement and NOT an equivalence claim against Legacy; the claim sets are small and different. Stable conclusion: Article Form materially improved form/coherence/arrival, grounding remains unresolved. `DISCOVERY -> ARTICLE FORM -> WRITER` recorded as the leading WORKING architecture (hypothesis, Edinburgh-calibrated, transfer validation pending) — not production canonical, not deployed.
CORRECTION (material, supersedes the earlier record): the claim that Opus, Grok and Qwen "independently converged" on the agency thesis is FALSE and must not be restated. Raw Grok and Perplexity sessions recovered 2026-08-19 show the text pasted into the prompt's FULL SOURCE slot was not the Guardian review but a damaged terminal capture with Opus B.3's article interleaved into it — ten B.3-specific phrases appear 0x in the real source and 1x in the models' input; Grok reproduced B.3's sentences and repaired B.3's corruption; Perplexity's first article opens with the paste's final line. Grok and Perplexity are contaminated and cannot confirm anything. Qwen's original prompt/output/reasoning remain unavailable: UNKNOWN, not corroboration. The supported statement is two clean Opus experiments (B.3, B.4). Perplexity's later "for cripminds.com" topical collapse is an illustrative observation inside a contaminated session, not a controlled test.
CORRECTION: G-024's conclusion that no Edinburgh lineage existed is disproven — it lived on Trident (runs need CLIProxy, unreachable from the Mac), not on this laptop. Reader evidence corrected too: the father's WhatsApp feedback is bound to the LEGACY arm (PDF SHA-256 `5f6777d5...`, produced 17:22, message 19:02), so his "underground twice" message restates the article he had just read rather than arriving at it independently. What it does support: the argument survived reader compression, he judged it original and important, and he independently found the piece insufficiently coherent with an unclear "I"/perspective. Jascha independently preferred Legacy's early motion, found the Deaf anecdote a jump, and found the piece too long after arrival.
CODE: none. No file under `automation/`, `_posts/`, `_drafts/`, or any `.db` was created, modified or deleted. No deploy, no push, no model call.
EVIDENCE: `.claude/experiments/sofa-real-ab-1-2026-08-18/` (full lineage + `external-evidence/`), `.claude/experiments/sofa-method-reconciliation-2026-08-19/`, `.claude/experiments/project-state-reconciliation-2026-08-18/` (G-001..G-053 + normalization), `.claude/experiments/cj1-cj2-b2-dev-artifacts-2026-08-11/`, `.claude/experiments/editorial-pairing-blind-test-2026-08-14/`. Preservation commits `7d59bb3` (203 files) and `5256f08` (76 files), evidence-only, unpushed.
LOSSES: the four Aug-14 editorial-pairing candidate drafts are CONFIRMED LOST — catalogued as at-risk at 23:55 on 2026-08-18, destroyed by 00:00, probable macOS /tmp reaping. Do not recreate them. Distinct from FULL_RAW_NOT_FOUND material (Qwen, and two older model-comparison artifacts), where there is no evidence anything was ever persisted locally.
SUPERSEDES: `## 5a`'s Scout sequence as the active thread (its items 1-3 are done; Scout's articles became the FOX/HOUR/MOBILE benchmarks). Scout's disturbance/discovery front-end is PARKED, not rejected — the old SV0 owner gate was never formally completed at the time, and has been superseded as a current blocker by the later benchmark and real-material work.
FOLLOW-UP: FORM-1.1 grounding diagnosis ONLY — for each of the 3 UNSUPPORTED and 1 UNCERTAIN claims, record exact claim, exact source support, verdict, failure class, and origin (Form / writer / source paraphrase / auditor). No regeneration, no FORM-1.2, until that is complete. Production migration of the pipeline-audit P0s is DEFERRED PENDING ARTICLE FORM VALIDATION.

## 2026-08-19 — FORM-1.2 / FORM-1.3 / FORM-1.3 REPLICATE SET
STATUS: Article Form structural behaviour STABLE 3/3; sentence-level grounding SYSTEMATICALLY DEFICIENT.
DECISION: D — SYSTEMATIC_GROUNDING_PROBLEM. FORM-1.3 frozen as the Edinburgh structural calibration
candidate. No FORM-1.4. Phase moves to writer/grounding control design. Real Article Test 2 blocked
until sentence-level fidelity is addressed.
DETAIL: FORM-1.2 disconfirmed the "provenance dropped between Form and Writer" hypothesis (all three
corrections landed; festival-possession claims rose 3→6; did not stop after arrival). Form-layer
diagnosis found two defects — ownership asserted only in the destination while the operative
instruction stayed ownerless, and an internal contradiction between "in the order given" and "STOP at
arrival". FORM-1.3 corrected exactly those two. Three byte-identical runs then gave 0/0/0
festival-as-speaker, countervoice before a terminal arrival 3/3, 0 paragraphs after arrival 3/3, no
leakage, no agency attractor. Residuals are writer-origin and class-stable: invented
visitor-state/temporal specificity 3/3, interpretation-as-fact 2/3, plus isolated dropped qualifier,
invented proper noun, and one Form boundary surfacing as a prose claim.
NOTE: FORM-1.3 and its replicates ran LOCAL_CLAUDE_SUBSCRIPTION (claude-opus-5[1m]), NOT the frozen
Edinburgh writer path (openrouter/claude-opus-4.8 via CLIProxy). Manual architecture-development runs,
not production-path replays — a real confound against FORM-1/1.1/1.2.
EVIDENCE: .claude/experiments/sofa-real-ab-1-2026-08-18/iterations/{FORM-1.2,FORM-1.3,FORM-1.3-R2,
FORM-1.3-R3}/ and iterations/REPLICATE-SET-RESULTS.md
CODE: ec540b6 (FORM-1.2), 006ea10 (FORM-1.3), 7248c61 (replicates)
SUPERSEDES: WORK.md ## 5b's prior "FORM-1.1 grounding diagnosis only" next-action.
FOLLOW-UP: Design writer/grounding control V0 against the six recurring classes. Keep FORM-1.3 frozen.

## 2026-08-19 — LEGACY PROMPT / RULE INVENTORY QUEUED
STATUS: DEFERRED — REQUIRED. Not started; no old rules inspected or modified.
DECISION: Jascha explicitly requested a future dedicated audit of CripMinds' historical prompt-era
rule surface, so it cannot be lost between sessions. Early development accumulated many
mass-injected / prompt-level rules (writing rules, persona constraints, grounding instructions,
editorial prohibitions, blocklists). Once Writer Grounding is solved we determine which of them
remain ACTIVE, have MIGRATED into the newer architecture, are CONTRADICTED by it, are DUPLICATED
across layers, or are DEAD and deletable.
TRIGGER: after Writer Grounding is calibrated/solved and end-to-end shadow validation is complete;
BEFORE production migration or final architecture cleanup.
RATIONALE: the objective is not shorter prompts. It is that every surviving instruction has one
justified architectural owner, one clear purpose, no contradiction with the current method, no
unnecessary duplication, and evidence it is still needed. FORM-1.3/R2 supplies the specific worry:
a negative Form constraint surfaced as a prose proposition, so prohibition-heavy historical prompts
need explicit review rather than assumed harmlessness.
SCOPE NOTE: cleanup is recommendation-only. No historical or production rule is deleted without a
separate authorized cleanup task. Preservation first.
EVIDENCE: .claude/WORK.md ## 5c
SUPERSEDES: nothing — this is an addition to the roadmap, no prior entry rewritten.
FOLLOW-UP: do not start before the trigger above. Writer Grounding (## 5b) continues meanwhile.

## 2026-08-19 — WG6-N1/N2 CLOSED, THEN OWNER STOP ON WRITER GROUNDING
STATUS: WG6-N1 and WG6-N2 CLOSED. Final end-to-end shadow replay ABORTED BY OWNER before any model
stage executed. Writer Grounding frozen as SHADOW-CALIBRATED CANDIDATE — NOT PRODUCTION-VALIDATED,
NOT TRANSFER-VALIDATED. Nothing pushed, nothing deployed, no article generated, Gold V2.1 and
FORM-1.3 unmodified.
DECISION:
  WG6-N1 — A, ROUTING_GAP_CLOSED. Routing authority for a negative meta-source claim is now WG-4B's
  own IN_SCOPE + NEGATIVE classification, not a WG-4A COMMITMENT_TYPE label. A negative parent with
  no SOURCE_META carrier emits a synthesised WG-4B unit and reassigns nothing, so an independent
  commitment sharing the parent sentence keeps its own verdict. Re-scored on both frozen conditions
  with no model calls: original condition TP 8 / FP 0 / FN 0, unsupported set byte-identical to
  frozen WG-6A, unrouted 0; post-repair the previously suppressed finding is recovered.
  WG6-N2 — A, VERIFICATION_SEMANTICS_READY. Sentence-level byte-locality plus independent source
  adjudication yields four separately reported counts: repair introduced 0, repair residual 0,
  preexisting genuine newly detected 1, detector variance 2. "Repair introduced none" is a narrower
  claim than "no new unsupported"; the two may not be collapsed. The one genuine survivor is
  FORM-1.3's "the visitor's afternoon", an invented duration absent from the source, same class as
  gold G13-02 / GR3-01 / GR3-03 — repair did not cause it, gold simply never named it.
OWNER STOP RULE (binding): repeated stochastic audits of the same Edinburgh prose will not be
required to produce zero newly discovered propositions forever. Source-relative LLM detection is
stochastic and a finite gold benchmark cannot prove every possible unsupported proposition in an
article has been enumerated forever — WG6-N2 measured this directly. The finite Gold V2.1
calibration and the completed WG experiments have served their purpose. Do NOT create WG-7, do NOT
create another Edinburgh grounding experiment, do NOT run another FORM version. Reopen Edinburgh
Writer Grounding only if a later transfer/production test reveals a reproducible failure that maps
back to this architecture.
ABORT NOTE: the final-replay directory holds pre-registration, frozen inputs, deterministic stages
and three rendered stage-1 prompts — and ZERO model calls, ZERO outputs. It is not an experiment
failure; nothing was measured, so no result may be inferred from it. Missing outputs must not be
reconstructed, simulated or completed later.
EVIDENCE: .claude/experiments/writer-grounding-v6-2026-08-19/WG-6N/STATUS.md (read first),
N1-RESCORE.json, N2-CLASSIFICATION.json, N2-ADJUDICATION.json;
.claude/experiments/writer-grounding-final-shadow-2026-08-19/STATUS.md (ABORTED_BY_OWNER)
CODE: a1f2889 (WG-6N closure, last completed evidence checkpoint)
SUPERSEDES: the "NEXT: close WG6-N1 then run one final shadow replay" plan in WORK.md ## 5b. The
first half was done; the second half is cancelled by owner decision, not by failure. WG-6's own
results (WG6-RESULTS.json, decision A) are unchanged and were not rewritten.
FOLLOW-UP: next roadmap task is LEGACY PROMPT / RULE INVENTORY (## 5c) — its trigger is now reached.
Then Real Article Test 2 / transfer validation. Neither started in this session.

## 2026-08-20 — LEGACY PROMPT / RULE INVENTORY COMPLETE (LPRI1)
STATUS: Inventory COMPLETE. Owner triage recorded. **No cleanup performed, no production change,
no model call, no deploy, no push.**
DECISION: Audited the full CripMinds prompt/rule surface at HEAD `3a05f61`. Found **114 rule
families** (96 active in production, 6 shadow/gated-OFF, 7 historical, 5 dead), counted mechanically
from the inventory's own rows. **Mass injection confirmed live**, answering Jascha's recollection
affirmatively rather than dismissing it: two generations exist. The historical one (~15 style rules
hand-copied into ≥12 locations across `production_orchestrator.py`, `opus_rewrite.py` and a
root-level orchestrator copy, with four documented drift instances) is gone — those files were
deleted in the 2026-08-09 module split. The current one is live: `generate.py:783–1050` assembles a
**59,161-char / 9,862-word / 75-rule-unit** writer prompt per run, plus four further live bundles
(rewrite SYSTEM 25,019 ch / 47 rules; planner brief 15,358 ch; `RULES_SYSTEM` 9,035 ch / R1–R19;
`GATE_SYSTEM` 8,105 ch / R1–R17, blocking) — ~130,000 chars of rule text per article. Sizes were
measured, not estimated: static literals via AST `literal_eval`, dynamic prompts by running the
repo's own existing zero-network capture harnesses (`writer_prompt_test.py::_capture_writer_prompt`,
`snapshot_test.py::_snapshot_generate_calls`). No new harness was built and no model was invoked.
KEY FINDING: **`automation/style_rules.py` was never wired in.** Built 2026-08-09 as the "single
source of truth" specifically to end this duplication — 16 rules, three renderings each, five render
functions, R-numbers assigned at render time so the "R14 means two different things" bug class would
be structurally impossible. It has **zero consumers**; the only `from style_rules import` in the repo
is inside its own docstring USAGE example. It became a fourth parallel copy. Its companion drift
linter `check_rule_drift.py` has no automated runner (no Makefile, no CI job, no cron). Consequence:
19 rule families are duplicated across 3+ surfaces, 8 across all 5, and 9 rules carry **different R
identifiers in `GATE_SYSTEM` vs `RULES_SYSTEM`** (R5 = SYSTEM VOICE in one, VAGUE WE in the other)
while `gate.py::_parse_rule_verdicts` keys on those identifiers — precisely the bug the registry was
built to prevent, still live. 8 contradictions found, 24 families marked MIGRATED/REDUNDANT
CANDIDATE, 11 owner decisions open.
CORRECTION (AR3, canonical wording): the testimony quota was removed from the **writer prompt** only
(`generate.py:882`, AR3A commit `3225ea1`). It is **still active in the rewriter** — `llm.py`
`rewrite_with_opus` SYSTEM rules 33 ("REQUIRED: … a second real named person must appear") and 33b
("SOMEONE ELSE MUST SPEAK") — which runs on every production article via `generate.py:1168`. AR3A's
own release note records checking `style_rules.py` and `gate.py` for surviving copies; `llm.py` was
not checked. Any wording claiming testimony requirements are fully removed from the pipeline is
inaccurate and needs qualification. Not overclaimed: rule 33b forbids inventing a quote and
`_reject_if_unsupported_specifics` guards the rewrite output, so the fabrication path is partly
blocked; the editorial pressure AR3 identified as causal is not removed. **Not fixed in this task.**
ALSO FOUND: persona canon is injected **twice, SHA-256 identical** (7,216 ch, ~12% of the prompt) for
the three fictional personas, with a joining sentence declaring the canon "does NOT authorize
autobiographical facts" while pointing at that same text as the AUTHORIZED PERSONAL HISTORY. Pixel
Nova is correct (its two blocks legitimately differ). Root cause is `_load_persona_factual_context`'s
canon fallback — deliberate and well-argued for provenance, but its prompt-assembly consequence is
undocumented. Also: 80 negative-prohibition tokens in the writer prompt, several carrying concrete
nouns and verbatim bad-example sentences (Edinburgh risk class) — recorded as surface area, not a
measured failure; no experiment run or proposed.
OWNER DECISION: **Real Article Test 2 must NOT use the legacy production writer prompt or
mass-injection surface.** Test 2 is transfer validation of Article Form + Writer Grounding on a
materially different story shape, run through DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING on
the **local Claude subscription**, not `production_orchestrator.py`. It is **not** a production-path
fidelity test. Therefore the 96 production-active rule families do **not** block Test 2 — 82 families
across 13 legacy surfaces are excluded (`TEST2-BOUNDARY.md`), not fixed. Production prompt cleanup is
**DEFERRED until after transfer validation**, so that cleaning 114 rule families does not become
another long precondition before we learn whether Article Form transfers at all.
PRODUCTION STATE: **UNCHANGED AND UNCLEANED.** 96 rule families remain active on every live article
run. Nothing in this entry describes a production fix.
EVIDENCE: `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/` — `MASTER-INVENTORY.md`,
`ACTIVE-RULE-SURFACE.md`, `MASS-INJECTION-FINDING.md`, `MIGRATION-MAP.md`,
`DUPLICATES-AND-CONTRADICTIONS.md`, `CLEANUP-RECOMMENDATIONS.md`, `OWNER-TRIAGE.md`,
`TEST2-BOUNDARY.md`, `inventory.csv`, `prompt-census.json`, plus captured live prompts
(`writer_prompt_maya.txt`, `writer_prompt_pixel.txt`, `planner_user_prompt.txt`).
CODE: `38c47b8` (inventory evidence). No production commit.
SUPERSEDES: `.claude/CONTEXT.md`'s claim that `style_rules.py` is the "single source of truth" and
that `check_rule_drift.py` should be "run before touching any style-rule text" — corrected in this
task. Supersedes `WORK.md` `## 5c`'s DEFERRED status for the inventory.
COUNT CORRECTION: an early verbal summary of this audit reported "98 rule families / 79 production /
8 shadow / 11 historical-dead". That was a summary miscount, not an error in the artifacts.
Mechanical recount gives **114 / 96 / 6 / 7+5**; the committed files carry the corrected figures.
FOLLOW-UP: Real Article Test 2 — design / story selection. Then production architecture / legacy
prompt cleanup planning, then production migration + fidelity testing. Do NOT begin cleanup, do NOT
wire `style_rules.py` merely because it exists, do NOT reopen Writer Grounding calibration.

## 2026-08-20 — REAL ARTICLE TEST 2 CLOSED AS TRANSFER_PASS; MIGRATION PLANNING OPENED (RAT2)
STATUS: Test 2 **TRANSFER_PASS** by owner decision, reclassified from the run's own
LOCAL_DEFECT verdict. Current phase is now PRODUCTION ARCHITECTURE / MIGRATION PLANNING —
planning only. **No code modified, no deployment, no cleanup, nothing pushed.**
DECISION: Test 2 executed once at packet `2dd9a86`, evidence `8741804`. Source: RAIB Report
10/2026, collision between a tram and two pedestrians at Staniforth Road, Sheffield. One
writer call on the local Claude subscription (claude-opus-5[1m]), frozen prompt `60b1d54e`
executed unmodified, no retries, no candidates, no hand editing. Article "Bell or Horn".
The owner reclassified the outcome as TRANSFER_PASS on the grounds that the architecture
succeeded on every substantive transfer criterion: a materially different Article Form
emerged; no Edinburgh geometry reversion; the perceptual instrument stayed necessary but
narratively invisible (zero occurrences of deaf/disability/access/impairment); the
resistance and recurrence material was structurally load-bearing; the arrival was earned and
terminal; Writer Grounding identified the genuine factual slips; patch repair removed them;
no legitimate interpretation was damaged; the final article was source-grounded.
The 1,587-word output against a 900–1,200 request is recorded as **NON-BLOCKING EDITORIAL /
LENGTH-CONTROL DEBT**, likely owned by ARTICLE FORM as an editorial output constraint. It is
explicitly NOT sufficient reason for another transfer-test generation. No rigid universal
length mechanism is to be introduced until cross-story evidence exists; that evidence should
be collected as a by-product of shadow comparison, not by running generations for it.
**Do not rerun Test 2, create Test 2.1, or generate a compressed variant. The frozen Test-2
article is not to be modified.**
CANONICAL STATE: Article Form is now **TRANSFER-VALIDATED ON TWO MATERIALLY DIFFERENT STORY
SHAPES** — Edinburgh as the structural/semantic discovery case, Staniforth Road as the
event/system/channel/recurrence case; neither Form was derived from the other. Writer
Grounding remains **SHADOW-CALIBRATED**, now successfully exercised on Test 2, and is still
**not production-validated**. **Production is still NOT migrated**; 96 legacy rule families
remain active on every live article run. Nothing in this entry implies production validation.
MIGRATION PLAN: seven documents at
`.claude/experiments/production-architecture-plan-2026-08-20/`. Target pipeline:
WORLD/SOURCE → DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING → ACCEPT/HOLD →
publication stages. Every current major component given a disposition. KEEP: Story Rejection
V1.1, `grounding.py` primitives, web fact-check, deterministic integrity checks, publication
stages. ADAPT: Fable brief (decomposed into commissionability + byline, dropping the
planner-authored prose fields), PRF1 (byline only, not prose voice), gate and review (split —
deterministic checks kept, LLM rule-judges removed), `sofa_discovery_shadow.py` as the seed
of DISCOVERY/ARTICLE FORM. REPLACE: the 59,161-character writer prompt, `_should_block` →
ACCEPT/HOLD. REMOVE: the whole-document rewrite stage, persona canon injection into the
writer, register/type/length selectors, `style_rules.py`, `check_rule_drift.py`. PARK: CJ-2,
L2 testimony, Reader Lab (verified not imported by `automation/`).
CENTRAL FINDING: **~81% of the 114-family legacy rule debt is deleted by replacing three
stages** — the writer prompt, the whole-document rewrite, and the two LLM rule-judges —
rather than cleaned. This inverts most of the inventory's top-10 cleanup list. Do NOT patch
AR3's rewrite rules 33/33b, do NOT renumber the 9 gate/review R-number collisions, do NOT fix
the WP-13 UK-preference divergence, do NOT de-duplicate the persona canon double-injection,
do NOT consolidate the eight five-copy style families, and do NOT wire `style_rules.py`.
The correct action on that debt is to do nothing until its stage is deleted.
CAVEAT, recorded honestly and owner-facing: those debts stay live for the entire migration
window. AR3's quota keeps pressuring every production article toward a second named voice and
a spoken quote until the rewrite stage is actually removed. If the migration stalls or is
deprioritised, the ~3-line AR3 patch becomes correct after all. That is an owner decision,
not the plan's.
MIGRATION BLOCKERS identified from repository evidence, not from the inventory: B1 Writer
Grounding has no production implementation; B2 Article Form has no production implementation
(`sofa_discovery_shadow.py` exists but is imported by nothing in production); B3 no
live-vs-shadow comparison harness exists; B4 the production writer path routes through
Trident-only CLIProxyAPI and is unreachable from the Mac, so Phase 5 must run on Trident;
B5 ACCEPT/HOLD has no definition in code and `_compute_should_block` cannot be ported because
it keys on stage names that will no longer exist; B6 Story Rejection's FC2 finding is open and
travels into the target; B7 length control unspecified (deliberately deferred).
SEQUENCE: Phase 0 freeze baseline → 1 build in shadow (OFF by default, reusing
`cj2_shadow.py`'s discipline) → 2 live-vs-shadow on held-out real stories → 3 resolve only
blocking differences → 4 production candidate, deleting before switching, six separate commits
→ 5 production-fidelity test on Trident → 6 controlled migration with the legacy path retained
until the observation window closes.
EVIDENCE: `.claude/experiments/production-architecture-plan-2026-08-20/` —
`TARGET-ARCHITECTURE.md`, `LIVE-VS-TARGET.md`, `COMPONENT-DISPOSITIONS.md`,
`LEGACY-RULE-MIGRATION.md`, `PRODUCTION-DEBT-BEFORE-MIGRATION.md`, `MIGRATION-SEQUENCE.md`,
`ROLLBACK-AND-SHADOW-PLAN.md`.
CODE: none. No production commit.
SUPERSEDES: the run's own LOCAL_DEFECT verdict in
`.claude/experiments/real-article-test-2-2026-08-20/run/DECISION.md` (kept as the run record;
the owner reclassification is the operative status). Supersedes `WORK.md` `## 5c`'s
"CURRENT — Real Article Test 2".
FOLLOW-UP: Phase 0 — freeze the production baseline. Do NOT implement, deploy, clean, create
Test 3, or return to Edinburgh.

## 2026-08-20 — PRODUCTION MIGRATION PHASE 0: BASELINE FROZEN (PM-P0)
STATUS: **PHASE 0 COMPLETE.** No implementation, no deployment, no production code modified,
no cleanup, no AR3 patch, nothing pushed.
DECISION: Froze the current production baseline so later live-vs-shadow comparison is
meaningful and reversible. Local HEAD `c6f97b8` (25 commits ahead of origin, all `.claude/`
evidence, **none deployed**; 2 behind — production's own output commits). Production checkout
`/srv/data/hermes/workspace/disability-ai-collective` at `8af3622`, clean, in sync with
origin. **Verified all 13 core pipeline files byte-identical between local and Trident**,
which is what makes a locally-captured prompt baseline a genuine production baseline.
RUNTIME: production is **live and publishing** — it generated and pushed an article at 09:00
this morning while this planning work proceeded. Cron confirmed: news 06:05, article 09:00,
stale-check 10:30, publish_best every 2 days 08:00, DB backup 03:30. `CJ2_INTEGRATION_MODE`
and `L2_TESTIMONY_MODE` are unset on the host, so both default OFF — CJ-2 and L2 confirmed
inert. Writer routes through `call_llm_via_openclaw_session`; editorial/gate/review through
CLIProxy at `127.0.0.1:8317`, Trident-local, confirming migration Phase 5 must run there.
PROMPT BASELINE: hash-froze 12 static prompts, 5 persona canon files, 4 `personas.py` prompt
blocks and 13 pipeline source files. The assembled writer prompt was **re-derived with the
repo's own zero-network harness and reproduces byte-identically** to the capture preserved in
the Legacy Inventory (`38c47b8`), so it is referenced by path+commit+hash rather than
duplicated. No model call was made anywhere in Phase 0.
DATABASES: 5 SQLite DBs found in the production workspace; **all 5 backed up with SQLite's
`Connection.backup()` API** (never `cp`), **all 5 verified `integrity_check: ok`**, hashed,
to a retained root `/srv/backups/cripminds-phase0-baseline/`. No blockers; no unsafe copy was
substituted.
CORRECTION: the claim carried in `PROJECT-MAP.md` and repeated in the migration plan that
**"no SQLite-safe backup exists yet"** is **false and now corrected in both files**.
`automation/backup_state_dbs.py` has run daily at 03:30 since 2026-08-10 (added after the
engagement.db incident), using the SQLite backup API with a post-backup `integrity_check`,
writing outside the repo with 14-day retention, covering both live DBs. The real limitation is
that 14-day rotation would delete a baseline before migration completes — which is why a
separate retained Phase-0 root was created. Residual risk, unresolved: backups share the
source disk; offsite backup remains a separate open item.
NEW BASELINE FINDING (D9): **promotion is currently stalled.** Latest published post is
2026-08-11 — nine days ago. Seven drafts sit unpromoted, and **four of the seven carry
`fact_check_status: blocked`**, three with explicit `pipeline_degraded` lists
(`persona_biography_unresolved`; `gate_llm` + `persona_biography_unresolved`; `fable_brief`).
`_compute_should_block` is actively firing in production. Whether that is the safety net
working correctly or a stall worth investigating is **not decided** — it is recorded as the
baseline condition so post-migration change can be attributed. It also matters for Phase 2: a
comparison that ignores blocking would compare the new architecture against articles
production itself declined to publish.
NEW PHASE-2 BLOCKER: **production does not persist fetched source text anywhere.**
`article_plans.plan_json` stores `source_hash`/`evidence_packet_hash`/lengths but not the text;
`news_seeds` stores only the RSS summary; there is no source-text cache table. For most
fixtures the exact bytes the writer saw cannot be recovered, only verified by re-fetch against
the stored hash. Mitigations recorded for owner decision (freeze at generation time going
forward; accept hash-verified-or-flagged fixtures; prefer already-frozen sources).
HELD-OUT FIXTURES: five identified from existing production output, **no generation
performed**, selected for material diversity and lineage completeness rather than quality —
two are blocked articles. The strongest is `sniff-it-out-follow-your-nose-whatever-your-legs-can`
(2026-08-16, Maya Flux): its `source_hash` `fee0a03b8bb0c56b…` is **byte-identical to the
Edinburgh source already frozen in FORM-1.3**, giving a direct legacy-vs-Article-Form
comparison on identical input with both sides preserved. Others: `what-the-word-modular`
(Dezeen, fetch at risk, pairs with a same-source different-persona draft), `7-000-rooms`
(macroeconomic, `source_decision=commission`), `galaxy-h1` (1,434-char source → 1,776-word
article, exercises `gate_llm`), `surovell` (degraded-path only, no brief persisted).
SNAPSHOT TEST: runs clean at baseline ("No drift — 6 article(s) match recorded fixtures"), was
**not modified**. Reusable for migration regression checks, with two named limits: (1) the
25,019-character `rewrite_with_opus` SYSTEM has **zero snapshot coverage in any harness**, and
Phase 4 deletes it — its hash is now recorded in the Phase-0 prompt baseline so the removal is
still provable; (2) baselines must be re-recorded deliberately per deletion, never in one
squashed migration commit. Other uncovered surfaces recorded: engagement read, persona
cross-cite, both `FIX_SYSTEM`s, `SUBJECT_SYSTEM`, fact_check and link SYSTEMs, persona canon
payloads, and end-to-end output.
DEFECTS PRESERVED, NOT FIXED: D1 AR3 testimony quota live in rewrite 33/33b; D2 nine
gate/review R-number collisions; D3 WP-13 UK-preference mismatch; D4 duplicated persona canon
(7,216 ch, byte-identical); D5 mass-injected writer prompt (59,161 ch); D6 `style_rules.py`
unwired and `check_rule_drift.py` unrun; D7 80 negative-prohibition tokens; D8 fallback
publishes a template rather than holding; D9 promotion stalled.
AR3: **HOTFIX DECISION PENDING AFTER BASELINE FREEZE**, per instruction. Rewrite 33/33b were
NOT patched — the baseline had to capture real current behaviour first.
EVIDENCE: `.claude/experiments/production-migration-phase0-baseline-2026-08-20/` — README,
GIT-AND-RUNTIME-BASELINE, PRODUCTION-COMPONENT-MAP, PROMPT-BASELINE, KNOWN-DEFECTS,
DATABASE-BACKUP-MANIFEST, PUBLICATION-STATE, HELD-OUT-FIXTURES, SNAPSHOT-TEST-COVERAGE,
db-backup-manifest.json, SHA256SUMS.txt.
CODE: none. No production commit. Backups written to `/srv/backups/` on Trident only.
SUPERSEDES: `PROJECT-MAP.md`'s "no SQLite-safe backup exists yet" and the same claim in
`production-architecture-plan-2026-08-20/ROLLBACK-AND-SHADOW-PLAN.md`.
FOLLOW-UP: owner decision on AR3 hotfix; then Phase 1 (build DISCOVERY/ARTICLE FORM and
Writer Grounding arbitration as OFF-by-default shadow modules). Do NOT implement, deploy,
clean, or create Test 3 before that decision.

## 2026-08-20 — MIGRATION PHASE 1: CLEAN SHADOW VERTICAL SLICE V0 (PM-P1)
STATUS: **PHASE 1 COMPLETE.** OFF by default. No production code modified, no deployment, no
publication, no legacy cleanup, no AR3 patch, nothing pushed. **No model call was made.**
DECISION: Built the smallest OFF-by-default shadow vertical slice of the validated target
architecture — WORLD/SOURCE → DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING → SHADOW
ACCEPT/HOLD — as plumbing and artifact-integrity validation, not another editorial experiment.
LOCATION / ISOLATION: implementation lives entirely under
`.claude/experiments/production-migration-phase1-shadow-v0-2026-08-20/impl/shadow_v0/`,
deliberately outside `automation/`. The brief allowed either; the experiment root makes "no
production import" true by construction rather than convention, and the repo already has a
cautionary precedent in `sofa_discovery_shadow.py` (inside `automation/`, imported by nothing,
left untracked). Verified: `grep -rn "shadow_v0" automation/` returns nothing; `run()` raises
`ShadowDisabled` unless `SHADOW_V0_MODE` is set; the package has no `sqlite3`, no network
client and no `subprocess` in executable code, so a production DB write or a publication is
unimplementable from here rather than merely disallowed.
CONTRACTS: 8 artifacts at schema `shadow-v0.1` — SOURCE_SNAPSHOT, DISCOVERY, ARTICLE_FORM,
WRITER_INPUT, WRITER_OUTPUT, GROUNDING_FINDINGS, GROUNDING_REPAIR (optional), SHADOW_DECISION.
Each carries schema_version, stage, injected `created_at`, `input_hashes` and payload, with a
content hash over all of it. Fail-closed on: unknown stage, wrong schema, missing required
field, self-inconsistent hash, lineage break, non-`patch_only` repair, and any of 29 legacy
prompt markers appearing in WRITER_INPUT.
SOURCE PERSISTENCE — PHASE-2 BLOCKER FIXED: `SOURCE_SNAPSHOT` must carry the source **text**
plus provenance (origin, url, retrieved, upstream identifiers, frozen_at/commit), not just a
hash; validation recomputes the hash and rejects a mismatch, so a hash-only artifact cannot be
constructed. The runner also writes `source-snapshot.txt` beside the JSON. This is passive
capture — production source handling is unchanged.
STAGE SEPARATION, enforced by the artifact graph rather than by comment and asserted by test:
Discovery consumes `{source}`; Article Form consumes `{discovery, source}`; **Writer Grounding
consumes `{writer_output, source}` and never `article_form`**, so grounding structurally cannot
change the Form. Discovery and Article Form are not collapsed into a writer prompt, and no
persona material enters WRITER_INPUT at all.
ACCEPT/HOLD: deliberately **not** a port of `_compute_should_block` (which is a negative test
over stage names that will not exist). Positive rule: ACCEPT requires complete lineage, writer
output with `provider_status == ok`, settled grounding, every TRUE_UNSUPPORTED repaired,
TRUE_UNCERTAIN explicitly adjudicated, and repair verification 0/0/0. Everything else HOLDs.
**Provider failure → HOLD, not the legacy template fallback** — recorded as a shadow policy
candidate, still an owner decision. ACCEPT is not connected to publication.
GOLDEN REPLAY: Test 2 (Staniforth Road) replays end-to-end to **ACCEPT** with source hash
`be381bbc…` intact, all 8 stages emitted and lineage-chained, 2 patches applied patch-only,
repair verified. FORM-1.3 (Edinburgh) replays to **HOLD** on 2 unresolved TRUE_UNSUPPORTED
findings drawn from its own frozen audit (`status: FAIL`) — included precisely because a
decision contract that only ever accepts proves nothing. FORM-1.3's source hash `fee0a03b…` is
the one byte-identical to production's `article_plans.source_hash` for the draft
`sniff-it-out-…`, which is what will make a Phase-2 comparison provable for that story.
Replay is deterministic: two runs produce identical hashes for all 8 stages, guaranteed by
`created_at` being injected rather than clock-read.
BUGS FOUND AND FIXED IN-TASK (all caught by running it): (1) repo-root resolution was off by
one — `parents[4]` resolved to `.claude/`, breaking every fixture path; fixed to `parents[5]`
with a loud assertion. (2) `replay.py` passed `mode=MODE_REPLAY` explicitly, bypassing
`SHADOW_V0_MODE` and defeating default-OFF through the only executable entry point; fixed to
read the flag. (3) The safety test for "no `_posts`/`_drafts` reference" scanned raw file text
and failed on those words inside `runner.py`'s own safety docstring; tightened to scan
executable code only (identifiers, imports, non-docstring string literals via AST), so it
asserts what the code does rather than what its prose says.
SAFETY TESTS: 39 checks across 17 functions, **39/39 pass** — default OFF, LIVE_SHADOW refuses,
no DB/publication/network code, writes confined to the run root with `_posts` mtimes unchanged,
source text persisted, hash mismatch fails closed, lineage break fails closed, missing stage →
HOLD, missing field → ContractViolation, grounding unresolved → HOLD, unadjudicated UNCERTAIN →
HOLD, provider failure → HOLD, legacy marker rejected, Form/Grounding separation, patch-only
enforcement, determinism. No literary quality tests.
PRODUCTION SAFETY NET: `automation/snapshot_test.py` was **not modified**; re-run to confirm
the baseline holds ("No drift — 6 article(s) match recorded fixtures"). The shadow path has its
own golden tests, kept separate. Integration point recorded for Phase 4, including the Phase-0
finding that `rewrite_with_opus`'s 25,019-char SYSTEM has zero snapshot coverage anywhere.
AR3: unchanged and still deferred per owner decision — rewrite 33/33b remain known migration
debt; the stall is fact_check blocking and there is no evidence AR3 causes it.
EVIDENCE: `.claude/experiments/production-migration-phase1-shadow-v0-2026-08-20/` — README,
ARCHITECTURE, STAGE-CONTRACTS, SOURCE-PERSISTENCE, ACCEPT-HOLD, REPLAY-RESULT, SAFETY-TESTS,
SHA256SUMS, `impl/` (622 lines package + tests), `runs/` (both fixtures' artifacts + outputs).
CODE: `71a5a20` (implementation). No production commit.
FOLLOW-UP: Phase 2 — live-vs-shadow comparison on held-out real stories. Blockers recorded:
historical fixtures are verifiable but not byte-reproducible (production still does not persist
source text); a comparison harness does not yet exist; and Phase-2 must account for production
currently blocking 4 of 7 drafts. Do NOT run live shadow, deploy, or clean legacy prompts.

## 2026-08-20 — PHASE 2 PREP: PASSIVE CAPTURE + COMPARISON HARNESS (PM-P2PREP)
STATUS: **COMPLETE.** Not deployed, not pushed, flag not enabled, cron untouched, no
production behaviour changed. No model call.
DECISION: Built the one-off evidence fix Phase 2 requires, plus the harness that will consume
it. Owner decisions honoured: AR3 still deferred; production source persistence approved but
**observability only**; Phase-2 sample = first 3 complete eligible runs after enablement.
SEPARATION OF DEPLOYABLE CODE: the canonical local repo is 25+ commits ahead of origin with
`.claude/` evidence that is never deployed, so building instrumentation on that history would
make deployment ambiguous. Created worktree
`../disability-collective-ai-production-observability`, branch
`production-observability-2026-08-20`, **based exactly on `8af3622`** — verified it carries
zero research-history commits. Deployable commit **`20a7e3a`**: 3 files, **+530/−0**, with
`generate.py` at **+52/−0** (five one-line hooks, two helper assignments, safe defaults, one
import). Independently cherry-pickable.
EVIDENCE FLOW TRACED FIRST (before writing capture code): **"source text" is not one object.**
Four distinct representations exist and the code permits divergence — R1 the full cached
extraction (`_source_text_cache[url]`, capped 20,000), R2 the returned slice
(`cached[:max_chars]`), R3 the post-fallback-downgrade value handed to `build_evidence_packet`
(set to `None` when `source_origin == fallback_summary`), and R4 the evidence packet threaded
unmodified into planner/reviewer/executor. R1 and R2 coincide today only because both call
sites use the same 20,000 default — configuration, not an invariant — so all three text forms
are captured separately rather than assumed equal. Writer-visible evidence is the SOURCE
MATERIAL block interpolated at `generate.py:917` from the same variable, so capturing the
assembled prompt captures exactly what the writer saw.
CRITICAL CAPTURE: the **RAW writer output**, which exists only between `generate.py:1057` and
the rewrite that reassigns it, and is on no disk today. Because the target architecture removes
the whole-document rewrite stage, separating what the legacy WRITER produced from what the
legacy REWRITER changed is the most informative comparison signal available — and it is
attributable **by construction**, since nothing executes between the two captures.
CAPTURE CONTRACT: OFF unless `SHADOW_CAPTURE` is set; `capture()` catches `BaseException`, logs
and returns, so **a capture failure can never alter, block or fail an article run** (a
deliberate exception to the target architecture's fail-closed posture — capture observes the
legacy baseline and is not part of ACCEPT/HOLD); append-only `manifest.jsonl`; atomic temp +
fsync + `os.replace`; `COMPLETE` seal so partial bundles are detectable; refuses to persist any
artifact containing credential-shaped markers and records the refusal; no sqlite3, no network,
no subprocess, nothing under `_posts/` or `_drafts/` in executable code. Storage root
`/srv/data/cripminds-shadow-capture` — outside the repo, outside content dirs, and deliberately
**not** under `/srv/backups/cripminds` where 14-day rotation would delete bundles.
PROOF OF NO BEHAVIOUR CHANGE: `snapshot_test.py --check` passes unchanged in the observability
worktree with the capture code present and OFF ("No drift — 6 article(s) match recorded
fixtures"), and the patch deletes zero lines.
COMPARISON HARNESS (research side, `harness/compare.py`, 307 lines): six dimensions — source
equivalence (hash-gated; a mismatch **rejects** the comparison before any outcome is
reported), legacy outcome, shadow outcome, grounding, structure, legacy rule effects. No LLM
judge, no `difflib`/`SequenceMatcher`, no prose-quality score — asserted by test against
executable code. Grounding is reported **separately, never merged**: legacy has only
brief-field validation plus world-relative fact-check, while shadow Writer Grounding is
source-relative on finished prose; collapsing them would be a category error. Gate/review
rule-judge effects are explicitly returned as `NOT_ATTRIBUTABLE_FROM_THIS_BUNDLE` rather than
inferred, because the gate rewrites in place and only its result is captured.
BLOCKED RUNS ARE DATA: production currently blocks 4 of 7 drafts and has published nothing
since 2026-08-11. The harness records the pairing (e.g. legacy BLOCKED / shadow ACCEPT) and
carries an explicit note that neither system is assumed correct merely because it blocked.
PRE-REGISTRATION: Phase-2 comparison set = the **first 3 complete eligible runs after capture
enablement**, in capture-run-id order, registered before deployment and before any run was
observed. Eligibility is mechanical (normal article run, sealed complete bundle with matching
hashes, enough lineage). Topic, quality, publication state, fact-check block, degraded stages
and apparent winner are all explicitly NOT grounds for exclusion. `CAPTURE_INVALID` bundles are
recorded and the next chronological complete run is taken.
TESTS: **72 checks, 72 pass** — 36 capture-side, 36 harness-side. Fixtures are built by calling
the real capture module, not a hand-rolled imitation of the bundle format.
TEST-PRECISION FIXES: two of my own tests matched prose rather than code and were tightened to
scan executable code only (AST: identifiers, imports, non-docstring literals). The harness one
was a genuine failing test — it matched the word "similarity" inside `compare.py`'s own
docstring stating it does not do similarity. Fixed rather than deleted: a test asserting what
the prose says instead of what the code does is not a safety test.
EVIDENCE: `.claude/experiments/production-migration-phase2-prep-2026-08-20/` —
PHASE2-CAPTURE-DESIGN, CAPTURE-SCHEMA, COMPARISON-PROTOCOL, FIRST-3-PRE-REGISTRATION,
SAFETY-RESULTS, DEPLOYMENT-PLAN, README, SHA256SUMS, `harness/`, `results/`.
CODE: `20a7e3a` in the observability worktree only. No commit to production, nothing pushed.
FOLLOW-UP: owner reviews the +52-line `generate.py` diff, then cherry-pick, deploy, run both
test files on Trident, create the capture root, and enable `SHADOW_CAPTURE=1` in the article
cron — the single reversible enabling step. Then collect the pre-registered three runs. Do NOT
run live shadow or change architecture before that.

## 2026-08-20 — PHASE-2 CAPTURE DEPLOYED AND ENABLED; SAMPLE 0/3 (PM-P2DEPLOY)
STATUS: Capture deployed to Trident and enabled. **Sample collection incomplete: 0 of 3 runs.**
No shadow execution, no model call, no architecture change, no AR3 patch, nothing pushed.
PRE-DEPLOY CORRECTION: `capture()`/`seal()` caught `BaseException`, which would swallow
`SystemExit`/`KeyboardInterrupt`. Narrowed to `Exception` in five handlers — ordinary failures
still swallowed so capture can never alter/block/fail a run, but process signals now propagate.
Commit `8c4b4a5`. Two of my own tests were found not to exercise what they claimed and were
fixed: `test_hooks_are_additive_only` diffed the working tree against HEAD (empty once
committed, so it proved nothing) and now diffs against the `8af3622` baseline; the ad-hoc
signal check passed a payload that never reached a raising code path and reported "swallowed"
even after the fix, replaced by `test_process_signals_propagate` which patches `SC._write` to
raise. 39/39 pass.
DEPLOYMENT: branch `production-observability-2026-08-20` verified to descend directly from
`8af3622`, +572/−0 across 3 files, **zero `.claude/` research files**. Trident HEAD confirmed
still `8af3622` and clean, so the patch was compatible. Deployed by `git format-patch` piped
over ssh to `git am` — exact commits preserved, no push, no research history transferred.
Trident `8af3622` → `ad7b8c7`. SHAs differ (git am re-stamps) but all three files verified
SHA-256 identical to local.
PRE-ENABLE CHECKS (flag OFF), all passed: 39/39 capture tests on Trident; `snapshot_test
--check` "No drift"; `production_orchestrator` imports; **0 artifacts written while OFF**;
writer/rewrite/GATE/RULES SYSTEM hashes all unchanged; `llm.py`, `gate.py`, `review.py` file
hashes identical to the Phase-0 baseline; **AR3 rewrite 33/33b present and unchanged**;
`_posts` 142 / `_drafts` 7 unchanged; SQLite untouched.
CAPTURE ROOT: `/srv/data/cripminds-shadow-capture`, owner jascha, **mode 700** (not
world-readable — source material may be sensitive), writeable by the job user, outside the
repo/`_posts`/`_drafts`/SQLite, **not** under `/srv/backups/cripminds` where 14-day rotation
would delete bundles, not mixed with logs. 18G free.
ENABLED: 2026-08-20T09:36:55Z, `SHADOW_CAPTURE=1` prefixed to the **article** cron line only —
1 of 63 lines changed, cron backed up to the capture root. Shadow V0 / Discovery / Article
Form / Writer / Writer Grounding were NOT enabled; production remains the exact legacy
pipeline and capture is observational. **Flag propagation verified end-to-end** rather than
assumed: `cripminds-daily.sh` uses `set -a` + `source` (adds to the environment, does not
clear it) and `enabled()` returns True through a nested shell as cron invokes it — without
this check three days could have passed with capture silently inert.
SAMPLE 0/3 — HONEST INCOMPLETION: the article cron fires once daily at 09:00 CEST and today's
run completed at 09:09, **before** enablement at 11:36, so it is correctly excluded. The three
pre-registered eligible runs are 2026-08-21, -22 and -23. The brief forbids triggering
artificial runs to fill the sample, so collection takes three real days and cannot be done in
the deploying session. Nothing was faked, forced or back-dated.
TOOLING SO THE REST IS MECHANICAL: added `harness/validate_bundle.py` — 11 deterministic
checks (complete, sealed, raw source, normalized source, evidence packet, writer-visible
evidence, raw writer output, rewrite output, disposition, hashes verify, secrets clean), exit
0/1, emitting the manifest row as JSON. Self-tested against bundles built by the real capture
module: a **blocked** run validates VALID (blocked runs count) and an unsealed one returns
CAPTURE_INVALID. Plus `VALIDATION-RUNBOOK.md` with exact pull/validate/index/disable commands
and stop conditions, and a frozen `PHASE2-SAMPLE-MANIFEST.md` skeleton.
OWNER-FACING CONSEQUENCE: Trident `main` is now 2 commits ahead of `origin/main`. I did not
push — but `publish.py::commit_to_git` calls `_git_push_safe()`, which runs
`git stash --include-untracked` → `git pull --rebase` → `git push origin main` at the end of
every article run, so the observability commits will reach the **public** GitHub repo at 09:00
on 2026-08-21 regardless. Unavoidable short of not deploying. That same mechanism also drove
the deployment method: an uncommitted working-tree patch would be stashed and popped every
run, and one pop conflict would silently delete the capture code mid-flight. The patch carries
no secrets (the only credential-shaped strings are the literal marker list the scanner uses to
*refuse* secrets) and the repo already contains the whole pipeline publicly. Recorded rather
than left to surprise.
EVIDENCE: `.claude/experiments/production-migration-phase2-deployment-2026-08-20/` — STATUS,
DEPLOYMENT-RECORD, PHASE2-SAMPLE-MANIFEST, VALIDATION-RUNBOOK, README, SHA256SUMS, `bundles/`.
CODE: `20a7e3a` + `8c4b4a5` (local branch) = `445fbbc` + `ad7b8c7` (Trident). No research
commit deployed.
FOLLOW-UP: after each of the three runs, pull the bundle and run `validate_bundle.py`; assign
P2-01/02/03 in chronological order; record CAPTURE_INVALID bundles and take the next run;
after P2-03 **disable the flag** (cron backup saved) and confirm production continues
normally, leaving the capture code dormant. Then STOP — live-vs-shadow execution is a separate
task. Do NOT run Discovery/Article Form/Writer/Writer Grounding on captured sources yet.

## 2026-08-20 — PUBLICATION CADENCE / SELECTOR AUDIT (PUBAUD1)
STATUS: Read-only audit. No code, cron, capture or production change. Phase-2 capture left
enabled throughout; sample still 0/3.
OWNER RECOLLECTION CONFIRMED: generate candidates daily, publish ONE best eligible article
~every two days from a ~seven-day candidate window. That is exactly what
`automation/publish_best.py` does. Daily generation is NOT daily publication.
MECHANISM: `automation/publish_best.py`, cron `0 8 */2 * *`. **Precision the docstring rounds
off:** `*/2` in the day-of-month field steps from the field's first legal value (1), so it
fires on **ODD days 1,3,…,31** — confirmed against every promotion commit (08-01/03/05/07/09/
11/13/15/17/19). In a 31-day month the boundary runs land on the 31st and the 1st, two
consecutive days; a 30-day month gives a normal 2-day gap.
SELECTOR: window `AGE_WINDOW_DAYS=7` (>=7 days -> archived to `_drafts/_archive/`); eligibility
requires BOTH explicit `fact_check_status: verified` AND `publication_safety_version >= 1`;
rank `draft_score(def 7.0)*0.6 + topic_freshness*10*0.25 + persona_rotation*10*0.15 +
min(publish_attempts*0.15, 0.6)`; publishes exactly ONE or none; archives expired regardless.
WHAT "BEST" ACTUALLY MEANS: not editorial quality. `draft_score` is only written when the
conditional Opus editorial pass fires — live evidence 2 of 7 drafts carry it — so the 60% term
is usually the 7.0 constant and freshness/rotation/aging do the real deciding. The script's own
docstring already flags this as an open decision.
CORRECTION TO PHASE 0 (my error): Phase 0 recorded "nothing published since 2026-08-11" by
reading filenames. Drafts keep their **write-date filename** while `set_publish_date` rewrites
only front-matter `date:`. `_posts/2026-08-11-reached-by-boat-or-plane.md` carries
`date: 2026-08-15`. **The last publication was 2026-08-15** (commit `50c1a2d`); the gap is 5
days and 2 missed cycles, not 9 days.
PROMOTION RUN HISTORY: 08-15 published + archived 3 (`50c1a2d`); 08-17 archive-only
(`ba64e77`); 08-19 archive-only (`11826e4`); 08-21 upcoming. **The selector fired on schedule
every time — it is not broken and not failing to run.**
ROOT CAUSE OF THE STALL — two compounding causes. (1) A hard cutover with no migration path:
commit `667633f` (2026-08-16 11:55) added BOTH halves of the publication-safety contract at
once — `publish_best.py` began requiring `publication_safety_version >= 1` and `generate.py`
began stamping it — with no backfill, so every draft written before that commit reached Trident
lacks the stamp permanently and is HELD until it ages out and is archived unpublished (08-13,
08-14, 08-16 — all `verified`, one scoring 9/10). (2) Every post-cutover run has been
`blocked` (`persona_biography_unresolved`; `gate_llm + persona_biography_unresolved`;
`fable_brief`), so no new draft has earned a stamp either.
STRIKING FINDING: **0 of 165 articles on disk has EVER carried `publication_safety_version`**
— 0/142 `_posts`, 0/7 `_drafts`, 0/16 `_archive`. `_maybe_stamp_publication_safety_version`
requires `should_block` falsy AND `fact_check_status: verified` re-read from disk, and no run
has satisfied both since it went live. **The stamper's correctness is UNPROVEN in production —
it has never had the opportunity to fire.** Phase-2 captures may be its first observation.
Diagnosed with a `--dry-run` on Trident, which the script documents as write-free.
CLASSIFICATION: **WORKING-BUT-NO-ELIGIBLE-CANDIDATE** — closest to option D (blocking policy
excludes everything), reached via a cutover with no backfill rather than by malfunction. The
gate behaves exactly as designed; the design has no path for in-flight drafts and no alarm for
"pool empty across consecutive cycles".
CADENCE DECISION RECORDED: daily generation is INTENTIONAL and should stay daily — it builds
the candidate pool a less frequent selector needs. Do NOT make the article cron every-two-days.
TARGET ARCHITECTURE COMPLETED: `SOURCE → DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING
→ ACCEPT/HOLD → ACCEPTED CANDIDATE POOL → PERIODIC SELECTOR → PUBLISH ONE / PUBLISH NONE →
publication stages`. **ACCEPT = eligible candidate, NOT publish-now.** CripMinds must not
auto-publish every ACCEPTed article; editorial scarcity is preserved by the selector.
SELECTOR DISPOSITION: **ADAPT** (not replace). SURVIVES: `fact_check_status`, topic freshness,
persona rotation, `publish_attempts` aging, filename-date window, `set_publish_date`.
REPLACED_BY_TARGET_STAGE: `publication_safety_version` — `gate_llm` disappears with the LLM
rule-judge and `fable_brief` becomes DISCOVERY, so the contract must be re-derived from
ACCEPT/HOLD. REMOVE-or-REPLACE (owner decision): `draft_score`, already largely inert.
PHASE-2 IMPLICATION: pre-registered sample UNCHANGED (first 3 complete eligible daily runs).
A selector observation IS additionally needed, because migration changes one of the selector's
two gate inputs — but ONE naturally-occurring decision suffices; do not expand Phase 2.
Current capture is NOT sufficient for the selector (`shadow_capture.py` hooks only
`generate.py`). **Minimum missing capture may be zero code:** `publish_best.py` already prints
its full scoring table and gate verdicts and the cron already appends stdout to
`automation.log`; the only gaps are that those lines are untimestamped (`print()`, not logger)
and live in a rotating log. Preferred options, NOT implemented: (1) copy the relevant
`automation.log` slice into the capture root at the next odd-day run; (2) redirect that one
cron job's stdout to a dated file under the capture root — a cron-line change, no code;
(3) only if structured data proves necessary, a `--json` flag.
EVIDENCE: `.claude/experiments/publication-cadence-audit-2026-08-20/PUBLICATION-CADENCE-AUDIT.md`
CODE: none.
FOLLOW-UP: owner decisions on (a) backfilling or re-validating the three HELD drafts before
they age out (08-14 expires 08-21, 08-16 expires 08-23), (b) `draft_score`'s fate, (c) whether
an empty-pool alarm is wanted. Do NOT fix any of it yet.

## 2026-08-20 — SAFETY-CUTOVER COMPATIBILITY: NO BACKFILL, NO HOTFIX (CUTFIX1)
STATUS: Investigation complete. **No draft stamped. No code hotfix. No safety requirement
weakened. No cron change.** Phase-2 capture stayed enabled; sample still 0/3.
FREEZE: Trident `ad7b8c7`, clean; `publish_best.py` `1dbc4fac…`; `generate.py` `21b0111b…`;
all 7 draft hashes + front matter preserved in `PRE-HOTFIX-FREEZE.txt`. Verified after the
task that both candidate drafts are byte-identical to the freeze and still unstamped.
EXACT PREDICATE: `stamp iff should_block falsy AND ^fact_check_status:\s*verified\s*$ re-read
from disk AND no existing ^publication_safety_version:`. `should_block = "fable_brief" in
stages or "gate_llm" in stages or "persona_biography_unresolved" in stages or len(stages)>=2`.
Inputs are run-local `self._degraded_stages` plus the file's own fact_check_status. **No LLM
call, no network** — pure file I/O.
RECONSTRUCTABILITY: `pipeline_degraded` frontmatter has existed since 2026-08-10 (`e4922e6`)
and is written by `create_article_file` (line 1326, after the gate at 1302), so for a
post-08-10 draft its absence does mean the stage list was empty at write time. Necessary but
NOT sufficient.
**BLOCKING TERM — `persona_biography_unresolved`.** Introduced 2026-08-16 (`89cd082`/
`169e8ff`). Trident's own reflog settles when it landed: `394a02e HEAD@{2026-08-16 09:09:00}:
commit: Add new article: 2026-08-16-sniff-it-out-…` then `169e8ff HEAD@{2026-08-16 11:20:38}:
pull origin main`. The 08-16 draft was written at 09:09; the check arrived at 11:20, **two
hours and eleven minutes later**. It never ran on that draft, and a fortiori not on the 08-14
one. So `"persona_biography_unresolved" not in stages` is UNVERIFIABLE for both — its absence
means *never evaluated*, not *evaluated and passed*. That is exactly the gate's own stated
principle: UNKNOWN safety is not safety. `_compute_should_block` also changed on 08-14
(`b1d919c`) and 08-16 (`667633f`), so the 08-14 draft ran under an older, weaker rule too.
**VERDICT: CANNOT_SAFELY_BACKFILL for both.** No blanket backfill was used; equating
`fact_check_status == verified` with "current safety contract passed" would have silently
bypassed the requirement for precisely the drafts it was written to catch.
THE TWO DRAFTS — both `fact_check_status: verified`, no `pipeline_degraded`, no existing stamp;
both PASS the fact-check and no-existing-stamp components and are UNVERIFIABLE on
`should_block`. `2026-08-14-modular-means-it-comes-apart…` (Zen Circuit, expires 08-21,
draft_score absent → 7.0 default) — **not stamped**. `2026-08-16-sniff-it-out…` (Maya Flux,
expires 08-23, **draft_score 9**, the highest-scoring candidate on disk, on the Edinburgh
source) — **not stamped**. Both will archive unpublished. Archiving is preferable to bypassing
publication safety.
NO CODE HOTFIX — and this is the substantive judgement. The cutover trap is self-limiting: it
affects only drafts predating `667633f` reaching Trident, i.e. exactly the three on disk
(08-13 archived today, 08-14 on 08-21, 08-16 on 08-23). After 08-23 no pre-cutover draft
remains and the gate behaves normally. Any rescue would have to take the form of a permanent
"pre-2026-08-16 drafts don't need `publication_safety_version`" exemption — the legacy bypass
debt the brief explicitly forbids — added to save two drafts, one expiring tomorrow. The
remaining barrier afterwards is `fact_check_status: blocked` on recent runs, which is the
safety system working, not a cutover artefact.
STAMPER VERIFIED (it had never fired — 0/165 articles carry the stamp): **23/23 deterministic
checks** against temp fixtures, no article created, no model call, no production file touched.
Confirms pass-condition writes the version exactly once inside front matter; unrelated front
matter and body byte-preserved with exactly one line added; idempotent on repeat; writes
nothing for should_block=True, or for fact_check_status blocked/unverified/wrong-case/empty/
missing; never overwrites or duplicates an existing stamp; and `publish_best.py`'s own
`_ordinary_eligibility_ok` + `_current_safety_contract_ok` accept a stamped draft and reject an
unstamped one. The mechanism is sound; it has simply never had a qualifying run. Kept as
evidence rather than added to the deployable branch so the observability patch under review
stays unchanged — promoting it to a permanent test is a reasonable follow-up.
08-21 SELECTOR OBSERVATION ARMED, ZERO CHANGE: `publish_best.py` already prints its full
scoring table and cron already appends stdout to `automation.log`; confirmed no logrotate rule
matches that log. Instead of touching cron, wrote a byte-offset anchor to
`/srv/data/cripminds-shadow-capture/selector/ANCHOR-before-2026-08-21.json` (offset 211415,
log sha `260ada9d…`, extract `tail -c +211416`). Everything appended after it contains the
natural 08:00 run — candidate set, eligibility verdicts, scores, selection or none, archive
actions, git result. No cron change, no code change, no manual trigger.
MIGRATION DEBT RECORDED (not implemented): (1) cadence — `0 8 */2 * *` fires on odd days of
month and can fire on consecutive days at 31st→1st; target should enforce a real ">= 48 hours
since last publication" cooldown independent of calendar day, selector free to run daily;
(2) ranking — `draft_score` is absent on most drafts and defaults to 7.0, so freshness/
rotation/aging dominate despite the nominal 60% weight, and the ranking must stop presenting
that default as measured editorial quality; (3) cutover discipline — the root failure was
shipping a requirement and its producer in one commit with no compatibility path and no alarm
for "eligible pool empty across consecutive cycles"; any future gate of this kind needs a
migration plan for in-flight artefacts before it goes live.
EVIDENCE: `.claude/experiments/safety-cutover-hotfix-2026-08-20/` — SAFETY-CUTOVER-HOTFIX.md,
PRE-HOTFIX-FREEZE.txt, STAMPER-VERIFICATION.txt, verify_stamper.py, SHA256SUMS.txt.
CODE: none. No production change of any kind beyond one new evidence file in the capture root.
FOLLOW-UP: after 2026-08-21 08:00, extract the selector slice with the anchor's command. P2-01
remains the natural 09:00 run. Owner decision open on whether an empty-pool alarm is wanted.

## 2026-08-20 — ROADMAP RECORD: PUBLIC CORPUS INTEGRITY / ENGINE ERA SEPARATION (CORPINT1)
STATUS: **Record only.** No article scanned, no published content modified, no social media
touched, no code, no deploy. Phase-2 capture and migration work uninterrupted.
DECISION: Recorded a required pre-public-cutover workstream in `WORK.md` `## 5d`. CripMinds has
**142 published articles** (162 public items total), many promoted socially, all produced under
the legacy editorial engine. Deploying the new architecture must not make that corpus appear to
have been produced or validated by DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING. It was
not. **The trust problem is provenance ambiguity, not the existence of legacy articles** —
wholesale rewriting of the old corpus is explicitly NOT the plan.
BUILDS ON EXISTING WORK — DO NOT RESTART: `.claude/legacy-corpus-integrity-phase1-2026-08-16.md`
plus `.claude/audits/legacy-corpus-integrity-2026-08-16.json` already completed a Phase-1
diagnosis on 2026-08-16 — public inventory, production eras, structural scan of all 142
articles, a 14% semantic sample, and a scoping estimate of **60–100 of 142 articles** needing
remediation. Its verdict was **LC1 — MATERIAL LEGACY CREDIBILITY RISK; BEGIN PRIORITIZED
REMEDIATION**, and that has **not been actioned**. Section 5d is the policy/sequencing layer on
top of that diagnosis, not a new investigation.
STILL-OPEN HIGH-PRIORITY ITEM SURFACED, NOT FIXED: Phase 1 identified a confirmed
real-person/real-company factual mismatch on the live static page `research/care-labor.html`
concerning a real tribunal case, and recommended it be the first thing fixed independent of the
rest of the corpus. It has been live and unaddressed since 2026-08-16. Flagged here because it
is the highest factual-risk item in the corpus; **not touched in this task** (record-only).
RECORDED REQUIREMENTS: (1) hard era boundary `LEGACY_ENGINE` (before validated cutover) vs
`CURRENT_ENGINE` (after actual deployment), the date set by the real cutover, not by intent;
(2) article-level provenance metadata DEFINED ONLY, not implemented — `engine_generation`,
`integrity_audit_status`, `source_provenance_status`, `last_integrity_review`, with the
Phase-0 caveat that production never persisted generation-time source text so
`source_provenance_status` will be unrecoverable for most legacy articles by construction;
(3) a finite risk-prioritised audit — HIGH covering quotes, named-person testimony, specific
numbers/dates, human states/motives, studies/statistics, institutional/source claims and
fabrication-sensitive specifics; MEDIUM ordinary factual/source-fidelity claims; LOW
interpretation/style/Form — noting Phase 1's finding that the dominant failure mode is
**invented personal-history testimony**, which the existing citation scanner structurally
cannot see, so HIGH must include a personal-history-specific re-read rather than citation
checking alone; (4) allowed outcomes `KEEP_AS_LEGACY` / `CORRECT_WITH_DISCLOSURE` / `WITHDRAW`,
with **no automatic re-running of historical articles through the new engine** — that would
produce a new article, not a corrected one, and would destroy the very provenance distinction
the workstream exists to preserve; (5) social-media principle — the article URL is the
canonical correction record, update/follow up where a materially corrected article was
promoted, remove promotion where an article is withdrawn for fundamental unreliability, and
**no blanket deletion** of historical social posts (`_social/` holds 127+ post-URI artifacts so
the trail is recoverable per article); (6) a public editorial-method/history or corrections
statement before any public new-engine claim, explicitly **not** claiming the historical corpus
has been retrospectively Writer-Grounding validated unless it has — Phase 1 also found the
site's stated editorial policies are already contradicted by its own published content, which
must be resolved in the same pass rather than compounded.
SEQUENCING: Phase-2 migration/capture continues now. Engine-era separation + integrity policy
are REQUIRED BEFORE PUBLIC CUTOVER. The legacy audit may run in finite batches in parallel and
must not become another endless calibration project. Production migration Phases 3–6 may
proceed on their own track — what is gated is the **public claim** about the new engine, not
the engineering.
EVIDENCE: `WORK.md` `## 5d`. No new experiment root created; the Phase-1 audit documents remain
the substantive evidence.
CODE: none.
FOLLOW-UP: do NOT start scanning articles. When authorised, begin from the Phase-1 findings and
its JSON manifest rather than re-inventorying, and take `research/care-labor.html` first.

## 2026-08-20 — LEGACY P0 CORRECTED: care-labor real-person factual error (LCP0-1)
STATUS: **P0 corrected and live.** One content commit, published. No new audit, no rescan of
142 articles. Phase-2 capture, crons, selector, AR3, Writer Grounding and production prompts
all untouched.
THE FINDING (from the existing Phase-1 audit, not rediscovered): `research/care-labor.html`
named a real individual (Shabin Shaji) and a real company (Swan Care Solutions Ltd) in
connection with genuine UK employment tribunal case 1308762/2023, and asserted claims the
record does not support. Flagged 2026-08-16 as "HIGHEST-SEVERITY FINDING IN AUDIT"; public
until today.
VERIFIED AGAINST THE PRIMARY SOURCE — the tribunal's own written reasons, retrieved from
assets.publishing.service.gov.uk and preserved (sha256 `910c1bd6…`), cross-checked against
Guardian and Work Rights Centre coverage. **Four errors, not the three Phase 1 listed** — the
date error surfaced during verification: (1) "paid £5 an hour" — FALSE, zero matches for `£5`/
`per hour`/`hourly`/`an hour` anywhere in the decision; he was paid nothing; (2) "housing was
deducted as wages" — FALSE, no accommodation deduction found, the word appears only in
narrative about where he arranged to live before starting; (3) "Swan Care is appealing" —
UNSUPPORTED, "appeal" does not appear in the decision and no appeal is in any published
report; (4) "In June 2026" — FALSE, heard 2–4 March 2026, judgment sent to the parties 5 March
2026.
WHAT THE RECORD SAYS: sponsored for a 40-hour week at £22,880 gross p.a., employed 15 Apr 2023
– 21 Apr 2024, *"ready, willing and able to perform his duties, and the only reason he did not
do so was because the respondent did not provide him with work"*; the full gross salary for
the period was treated as an unauthorised deduction. Awards £20,400.76 net + £2,168.85 net
holiday pay + £4,080.15 + £433.77 uplift + £1,760. **The truth is worse than what was
published** — not underpayment but a year of withheld work and withheld pay under a
sponsorship visa.
REMEDIATION: **CORRECT_WITH_DISCLOSURE**, not WITHDRAW — the page's central argument (the
health and care visa as a sponsorship trap) survives and is strengthened by the real record;
the false specifics were local to the lede and metadata. 18 insertions / 5 deletions in one
file: front-matter description, JSON-LD description, the lede, the "appeal as attrition" clause
(which presupposed the appeal), plus a visible correction note stating what changed without
describing internal architecture and without claiming retrospective validation. No rewrite
through the new engine, no stylistic modernisation, URL unchanged, no unrelated prose touched.
PUBLISH METHOD — deliberately narrow: local `main` was **34 commits ahead of origin, 33 of them
`.claude/` evidence that has never been deployed**, so a naive push would have published the
entire research history. Cherry-picked the single content commit onto a branch at `origin/main`
and pushed only that: `8af3622..70d9292`, one file. Verified afterwards that origin/main
contains exactly one new commit touching exactly one file. GitHub Pages deploy run
`32367255606` completed **success** in 1m7s, and the live page was confirmed by `curl` to carry
the correction — a push landing on main is not evidence it is live.
WIDER PROBLEM FLAGGED, NOT FIXED: the corrected page is an index, and the same unsupported
claims are asserted by **published articles** — `2026-06-19-swan-care-is-appealing-the-appeal-
is-the-mechanism.md` (entire article and title built on the non-existent appeal; strongest
WITHDRAW candidate in the corpus), `2026-06-04-swan-care-solutions-ltd-classified-someone-as-
equipment.md` (housing-deduction claim; has a recorded Bluesky post), and
`2026-06-09-three-months-in.md` (repeats a Swan Care claim as settled fact). The live page
still shows the appeal article's own title in a link card; that is **disclosed in the
correction note** rather than hidden, since this page cannot rename another article.
SOCIAL: `_social/` tracks Bluesky URIs only. One record exists —
`at://did:plc:4x2xhho3ozmrknpxqbdjtmbv/app.bsky.feed.post/3mnh2k2ymo22v` (Zen Circuit) for the
2026-06-04 article. No X/Reddit/LinkedIn/Facebook records in the repo. **No social modification
performed**; the corrected article is the canonical correction record. Follow-up becomes high
priority if the 2026-06-19 article is withdrawn.
LC1 BACKLOG RECORDED (not started), `WORK.md` `## 5d`/`7a`: finite batches capped at 10–20
articles — BATCH 1 highest-risk personal-history/real-person claims **starting with the three
Swan Care items above**, BATCH 2 quotes/attribution/named-person testimony, BATCH 3 specific
factual claims/numbers/dates/institutional claims, then lower-risk material. Each article ends
as KEEP_AS_LEGACY / CORRECT_WITH_DISCLOSURE / WITHDRAW. Do not re-inventory; do not auto-rerun
any article through the new engine.
EVIDENCE: `.claude/experiments/legacy-p0-care-labor-correction-2026-08-20/` — P0-CORRECTION-
RECORD.md, preserved pre-correction page + preserved tribunal written reasons, hashes.
CODE: none. CONTENT COMMIT: `5cd80ff` local / `70d9292` published.
FOLLOW-UP: Batch 1, starting with the 2026-06-19 appeal article. Do NOT start it in the same
task as other work.

## 2026-08-20 — SWAN CARE CLUSTER CLOSED: 0 withdrawals, 3 corrections (SWANCLOSE1)
STATUS: Cluster closed. 3 content corrections published and verified live. **No withdrawals.**
Phase-2 capture, crons, selector, AR3, Writer Grounding and production prompts untouched.
CORRECTION TO MY OWN PRIOR FINDING: the previous task reported
`2026-06-19-swan-care-is-appealing-the-appeal-is-the-mechanism` as "the strongest WITHDRAW
candidate in the corpus" because its title and thesis rested on a non-existent appeal. **That
was wrong — I read the index card, not the article.** The article was **already rebuilt on
2026-08-08** (commit `7c4719d`, *"rebuild second Swan Care article — its entire thesis was
fabricated"*), retitled from "Swan Care Is Appealing. The Appeal Is the Mechanism." to
**"Winning the Case Does Not Turn Off the Clock"**, with a new thesis about visa curtailment
when a sponsor licence is revoked — which the record supports. The only "appeal" strings left
in it are three asset filenames derived from the old slug. What was actually broken was
`research/care-labor.html`, never updated when the article was rebuilt, so for twelve days it
presented the withdrawn title and an appeal-based description as a normal current article, in
both the visible card and the JSON-LD itemList.
CLUSTER (7 public items checked against the already-preserved tribunal record, not re-derived):
`research/care-labor.html` CORRECT_WITH_DISCLOSURE (P0 lede fixed in `70d9292`, stale cards
fixed here); `2026-05-30-nhs-lancashire-and-south-cumbria-recruited` CORRECT_WITH_DISCLOSURE —
said Swan Care "classified a migrant care worker's accommodation as wages", a finding the
tribunal never made; `2026-06-09-three-months-in` CORRECT_WITH_DISCLOSURE — described the
subject as "a wheelchair user" when he is a migrant care worker (a NEW false claim found in
this pass); `2026-06-04-…classified-someone-as-equipment` KEEP_AS_LEGACY — verified accurate;
`2026-06-19-…` KEEP_AS_LEGACY — already rebuilt; `2026-06-20-i-use-care-workers…`
KEEP_AS_LEGACY — accurate; `research.html` + `cripminds-stats-2026-06.html` no action, title
references only.
06-04 VERIFIED ACCURATE against the judgment: zero hours for a year, 40hrs/£22,880 certificate,
£17,000 to an agent, "twenty thousand four hundred pounds in unpaid wages" (£20,400.76), the
27 December 2023 letter the tribunal found *"did not exist as at 27 December 2023"*, and the
sponsorship licence *"ultimately revoked in 2024"*. Two press-sourced specifics (the tap-water/
bread quote and the "39,000 care workers / 470 revoked sponsorships" statistic) are **not in
the judgment but not disproven by that** — absence from a judgment is not disproof, and the
article cites Guardian Society. Logged as MEDIUM-risk LC1 items, explicitly NOT Swan Care
falsehoods.
CHANGES: 3 files, 18 insertions / 10 deletions, each correction carrying a visible dated
disclosure. No style modernisation, no unrelated interpretation touched, no article rewritten
through the new engine, no URL changed.
URL LEFT ALONE DELIBERATELY: `/2026/06/19/swan-care-is-appealing-the-appeal-is-the-mechanism/`
still carries the pre-rebuild slug. Renaming it would break the canonical record, inbound
links and the article's own asset paths, to fix a slug on an article whose content is now
correct. The index card discloses it. Owner decision, not a factual necessity.
SOCIAL: `_social/` records Bluesky URIs only. **Exactly one post exists in the whole cluster** —
`at://did:plc:4x2xhho3ozmrknpxqbdjtmbv/app.bsky.feed.post/3mnh2k2ymo22v` (Zen Circuit) for the
2026-06-04 article, which is **accurate**. NO_ACTION. Nothing was withdrawn, so no promotional
post is circulating an invalidated claim. No X/Reddit/LinkedIn/Facebook records exist.
DEPLOY DISCIPLINE REPEATED: local `main` was 36 commits ahead of origin with `.claude/`
evidence never intended for deployment; the content commit was cherry-picked onto `origin/main`
and pushed alone (`70d9292..86a91d3`), verified to contain zero `.claude/` files before
pushing. Pages deploy run `32368084791` **success** (55s); all four affected URLs verified live
by `curl`.
EVIDENCE: `.claude/experiments/swan-care-cluster-closure-2026-08-20/` —
SWAN-CARE-CLUSTER-CLOSURE.md, pre/post hashes, preserved copies, cluster-fix.diff, SHA256SUMS.
CODE: none. CONTENT COMMIT: `83c6a6b` local / `86a91d3` published.
FOLLOW-UP: **Swan Care incident is CLOSED.** Do NOT begin LC1 Batch 1 or the static-site audit
in the same task. Two MEDIUM-risk press-sourced specifics in the 06-04 article are queued for a
later batch, not P0.
