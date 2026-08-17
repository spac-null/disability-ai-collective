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
