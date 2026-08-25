> **HISTORICAL — SUPERSEDED 2026-08-25.** This was the canonical `PROJECT-MAP.md` as of the
> 2026-08-16 Phase 3 audit (20 sibling worktrees, all on the `main`-checkout-is-canonical model).
> Superseded because canonical truth moved to `origin/main` while this file's home checkout
> (`~/code/disability-collective-ai`) diverged onto a 38-commit local-only line — see
> `.claude/WORK.md` and the new `.claude/PROJECT-MAP.md`. **The Story Rejection V1/V1.1 release
> history and the 19-branch lifecycle classifications below were NOT contradicted by the
> 2026-08-25 reconciliation** — both predate the fork point (2026-08-19/20) and are ancestors of
> current `origin/main` too. What's stale is the worktree COUNT (52 exist now, not 20) and the
> "`main` is canonical" framing — read the new `PROJECT-MAP.md` for current topology.

# CripMinds Project Map

**Physical topology only** — what long-lived worktrees/branches/evidence exist, where they
live, and their lifecycle status. NOT current truth (`WORK.md`), NOT chronology (`LOGBOOK.md`).
Machine-generated snapshot: `.claude/project-manifest.json` (regenerate with
`python3 scripts/cripminds_project_inventory.py`, read-only, safe to run anytime).

Installed 2026-08-16, Project Memory Phase 3, following the PI2 (audit) → PP1 (Mac
preservation) → PP2 (Mac+Trident cross-machine redundancy) preservation sequence. **Cleanup is
still not authorized** — this file documents state, it does not permit archival action on its own.

## Authority order

1. direct runtime / Git / DB evidence
2. `WORK.md` — what is true now
3. `LOGBOOK.md` — chronological history / how we got here
4. `PROJECT-MAP.md` (this file) — physical topology
5. `~/code/cripminds-preservation/PRESERVATION-MANIFEST.json` / linked evidence
6. historical documents (off-main, `.claude/experiments/`, etc.)
7. Claude-local/private memory summaries — never canonical, may be stale

## Canonical repository

- Path: `~/code/disability-collective-ai`
- Branch: `main`
- Origin: `git@github.com:spac-null/disability-ai-collective.git` (PUBLIC repo)
- Current role: sole canonical checkout; all 20 sibling worktrees are experiment/evidence
  copies, never a second "canonical"

## Production / Trident

- Production checkout: `jascha@trident.tail630536.ts.net:/srv/data/hermes/workspace/disability-ai-collective/`
  (checked out fresh by `cripminds-daily.sh` via `git pull` before each run)
- Production DB authority: same host, `disability_findings.db` — Trident is authoritative;
  the Mac-side copy is a separate, unreconciled, gitignored file, not a backup
- Evaluation root (Trident): `/srv/data/hermes/evaluations/` (currently: `cripminds-five-article-2026-08-16/`)
- Preservation mirror (Trident, archival only, NOT used by production automation):
  `/srv/data/hermes/preservation/cripminds/`
- Preservation root (Mac): `~/code/cripminds-preservation/`

## Active work

**Story Rejection prototype**
- Prototype (preserved, unmodified): `~/code/disability-collective-ai-srv1`, branch
  `proto/story-rejection-v1`, SHA `37432b983093274224a49cd1e2f820d41aa32bb6`. Backed by Mac
  worktree + Mac verified bundle + Trident verified bundle (PP2); not pushed to any remote —
  proposed remote ref `origin/experiments/proto-story-rejection-v1` still awaits owner approval.
- Release candidate: `~/code/disability-collective-ai-story-rejection-release`, branch
  `release/story-rejection-v1`, SHA `cff6dbc3140a5dea4ea6c2536ba664c633239995` (cherry-pick of
  `37432b9` onto current main `ba64e77`, byte-identical `automation/` content — zero conflicts,
  zero behavioral drift). Preserved as release evidence, not deleted.
- Merged into canonical main as `275470c` (`git cherry-pick -x cff6dbc...`), automation/ content
  re-verified byte-identical to the reviewed candidate post-merge. 28/28 automation tests pass,
  `snapshot_test.py --check` shows no drift, py_compile clean, orchestrator imports OK.
- Status: **RELEASED**. Docs commit `9e1c81d` pushed to `origin/main`; Trident production checkout
  fast-forwarded `ba64e77..9e1c81d` (`git pull origin main`, no conflicts). Production DB
  (`disability_findings.db` at the Trident repo root — confirmed during this deploy to be the
  actual `news_seeds`-holding DB; `automation/disability_findings.db` is a same-named but distinct
  file holding only `link_pool`, and `rss_disability_findings.db` at repo root is yet another
  distinct legacy file with neither `news_seeds` nor decline data — this resolves the "DB naming
  collision across 3 paths" item below as: not a collision, three genuinely different files that
  happen to share a naming pattern; `REPO/disability_findings.db` per `news_fetcher.py`'s own `DB`
  constant is unambiguous) migrated via the real, already-tested
  `news_fetcher.init_db()` additive path: 5 new columns added (`declined`, `declined_date`,
  `decline_json`, `decline_schema_version`, `declined_source_hash`), row count unchanged at 1116
  before/after, `used`/unused distribution unchanged (97/1019), zero data loss. Read-only smoke
  check confirmed: orchestrator imports, `STORY_REJECTION_CONTRACT_VERSION = "sr1"` present in both
  `grounding.py` and `news_fetcher.py`, the real contract-version exclusion SQL clause executes
  cleanly against the migrated schema, PRF1 reconciliation code present, CJ2/L2 still OFF, deployed
  `automation/` content byte-identical to reviewed candidate `cff6dbc`. No article generation, no
  Fable/provider calls, performed as part of this release or its verification.
  PRF1's routing invariant was confirmed under a real, manually-triggered production run
  (PRFV-M1, 2026-08-17 00:02 CEST); RG1 accepted that evidence as release-gate-sufficient since no
  code-level distinction exists between a cron-triggered and manually-triggered invocation of the
  identical entrypoint. A full adversarial release review then re-verified the two-layer
  (source-commissionability / PRF1-execution) architecture, both previously-identified defect fixes
  (contract-version-aware decline exclusion in the real SQL selection paths; NO_ELIGIBLE_CARRIER
  fallthrough never re-entering legacy commission), source-authority gating, additive/idempotent DB
  migration, and PRF1 non-regression — all verified against isolated SQLite fixtures before release,
  then against the real production DB during deployment. Known non-blocking follow-up:
  `eligible_execution_possible` lacks explicit boolean type validation on the commission branch
  (bounded by downstream eligible-persona check); deliberately not patched in this release. No
  candidate-2 retry exists by design — a legitimate "no article today" (decline, no-eligible-
  carrier, or defer) is an accepted real outcome of future production runs, not a defect.

**Story Rejection V1.1 (commission grounding + aggregator isolation)**
- Cause: the first real V1 commission (2026-08-17, "7,000 Rooms With No Door For Anyone") was
  forensically classified **FC2 — false/permissive commission** (SRF3). Two concrete defects: (A)
  `validate_source_decision()` validated DECLINE authoritatively but let COMMISSION `return True`
  trivially — zero grounding required; (B) the source was a Techmeme aggregator page fetched whole,
  letting an unrelated neighboring story (a Grok/Jane Doe lawsuit mentioning "7,000+ images")
  contaminate the evidence and contribute the article's title motif.
- Fix chain (all on branch `fix/story-rejection-v1-1-grounding`, worktree
  `~/code/disability-collective-ai-story-rejection-v11-fix`):
  - `d2821cf` + `a5988dc`: deterministic commission grounding (`_validate_commission_grounding()` —
    origin/truncation/verbatim-anchor/mechanism-tied-to-anchor/boolean-type gates), aggregator
    item isolation (`discovery.py`/`news_fetcher.py` recover `underlying_url` per-RSS-item, never
    fetch the whole aggregator page), new `source_decision: "defer"` outcome (bad commission
    evidence ≠ editorial decline), `underlying_article_url` source-lineage column, and
    provider-lineage logging.
  - Adversarial review then proved `a5988dc` alone still let a **real, verbatim-grounded anchor +
    an explanation that quotes it + an invented, factually-unsupported mechanism** pass as
    COMMISSION — the deterministic gate checks "does the anchor exist" and "is the anchor quoted,"
    not "does the anchor's content actually support the mechanism." Confirmed live against the
    unmodified validator (`ok=True, code="commission"`).
  - `d0204aa`: added `_verify_commission_mechanism_support()`, a narrow, separately-invoked,
    freshly-prompted semantic verifier (inputs: source text + anchor + mechanism + explanation
    only — no persona biography, no web, no downstream article). Output strictly
    SUPPORTED/UNSUPPORTED/UNCERTAIN; only an unambiguous SUPPORTED token continues to commission,
    everything else (including any provider failure/timeout/malformed reply) fails closed to
    `defer`. Adversarial revert proved the gate load-bearing: disabling it alone made the exact
    attack pass through again; restoring it brought the suite back to green.
  - Decisions along the way: SR11E-2 (entailment gap confirmed + fixed), SR11R1 (final adversarial
    release review passed — note: that review freshly re-executed only revert-A of five planned
    adversarial reverts against `d0204aa`; reverts B–E relied on code inspection and earlier-phase
    evidence rather than a fresh live re-run. The owner was informed of this narrower coverage and
    chose to proceed with release regardless).
- **Status: RELEASED.** Canonical main fast-forwarded `b925a5d..d0204aa` (a direct linear descendant
  of main — no cherry-pick needed, integrated tree is `d0204aa` byte-for-byte), pushed to
  `origin/main`. Trident fast-forwarded the same way; deployed file hashes confirmed identical to
  the reviewed candidate for all five changed production files. Production DB migrated via the same
  `news_fetcher.init_db()` additive path: `underlying_article_url` column added, all 5 existing
  Story Rejection V1 decline columns intact, row count unchanged at 1116 before/after, migration
  re-run confirmed idempotent. Read-only smoke check confirmed all V1.1 code markers present
  (semantic verifier, aggregator-domain logic, defer dispatch, boolean type check, provider-lineage
  logging) and CJ2/L2 still OFF. The defining release-gate attack (real anchor + invented mechanism
  + verifier UNSUPPORTED) was re-verified through the actual `_run_production_automation_locked()`
  dispatch path during this release, confirming DEFER with no writer/article/plan/decline/mark-used
  side effects. No production generation, no live provider call, performed at any point during this
  release or its verification.
- Known scope limit (recorded, not fixed): Atom-feed underlying-URL extraction is not implemented —
  the only known real aggregator case (Techmeme) is RSS 2.0. Not a blocker unless an Atom aggregator
  is discovered in actual use.
- Prototype (`proto/story-rejection-v1` @ `37432b9`), V1 release worktree
  (`release/story-rejection-v1` @ `cff6dbc`), and the V1.1 fix worktree/branch above are all
  preserved as release evidence — none deleted, none pushed to origin beyond canonical main itself.
- Legitimate outcomes for any future production run now include: DECLINE, DEFER (deterministic
  grounding failure, semantic UNSUPPORTED, semantic UNCERTAIN, or verifier failure), COMMISSIONABLE
  + NO_ELIGIBLE_CARRIER, or COMMISSIONABLE + WRITE. "No article today" is not a failure. No
  candidate-2 retry exists by design.

No other worktree/branch is currently ACTIVE — all remaining 19 are FROZEN-adjacent, PARKED,
SUPERSEDED, or SAFE-TO-ARCHIVE-LATER (below). All 20 sibling worktrees are internally clean
(0 dirty, 0 untracked) as of the 2026-08-16 audit — only canonical `main` carries untracked
material (see Evidence stores).

## Historical experiment worktrees / branches

| Name | Path | Purpose | Status | Unique evidence/doc pointer |
|---|---|---|---|---|
| audit/story-rejection-design | `-worktree` | ad hoc audit checkout, HEAD matches Trident's deployed commit exactly | MERGED | none — 0 commits ahead of main |
| (detached) | `-base-build` | historical build checkpoint | MERGED | none — 0 commits ahead of main |
| (detached) | `-eval-batch-1` | evaluation harness checkout | MERGED | none — 0 commits ahead of main; sibling plain dir `-eval-batch-1-harness` (non-git, `run_one_article.py`) sits alongside, not a worktree |
| integration-observability-2026-08-14 | `-integration-observability` | observability integration work | MERGED | none — 0 commits ahead of main |
| integration-first-work-persona-safety-2026-08-15 | `-integration-release` | persona-safety release integration | MERGED | none — 0 commits ahead of main |
| persona-safety-fail-closed-2026-08-16 | `-persona-fail-closed` | PS1 candidate fix (`89cd082`) | SUPERSEDED | same patch-id as merged release commit `169e8ff` — content is on `main` under a different SHA, not literally an ancestor |
| author-persona-biography-provenance-2026-08-14 | `-persona-biography` | APE2 candidate fix (`e93bb1b`) | SUPERSEDED | folded into merged `dbe0a96` ("AP1 + edge-case closure") on `main`, which is a superset of this branch's diff |
| article-quality-next-2026-08-14 | `-article-quality` | article-quality evidence pass | PARKED | `.claude/article-quality-evidence-pass-2026-08-14.md` already exists on `main`; branch's own 13 ahead commits not exhaustively diffed — confirm before archiving |
| format-lab-v0-2026-08-14 | `-format-lab` | Format Lab V0 design | PARKED | off-main doc preserved: `cripminds-format-lab-v0-2026-08-14.md` |
| format-lab-v1-generative-media-2026-08-14 | `-format-lab-v1` | Format Lab V1 design | PARKED | off-main doc preserved: `cripminds-format-lab-v1-generative-media-2026-08-14.md` |
| format-lab-v2-what-the-room-heard-2026-08-14 | `-format-lab-v2` | Format Lab V2 prototype | PARKED | off-main doc preserved: `cripminds-format-lab-v2-what-the-room-heard-2026-08-14.md` |
| human-detail-provenance-2026-08-14 | `-human-detail-provenance` | P1 human-detail-provenance experiment | PARKED | concept doc already CURRENT on `main`; branch's own 2 ahead commits not confirmed identical to main's shipped implementation |
| opening-quality-shadow-2026-08-14 | `-opening-quality` | opening-template shadow detector | PARKED | not confirmed superseded — old base (20 behind), owner review recommended |
| ops-release-hardening-2026-08-14 | `-ops-release-hardening` | release-concurrency preflight + health checker | PARKED | main independently has `release_preflight.py`; not confirmed identical — owner review recommended |
| publication-surface-production-candidate-2026-08-14 | `-pub-surface-prod-candidate` | production-candidate review (Phase F, per WORK.md, not yet done) | PARKED | gated on Phase F completing |
| publication-model-v1-2026-08-14 | `-publication-model-v1` | Publication Model V1 synthesis; source of confirmed GENERATE→MATERIALIZE terminology | PARKED — **historical source document recovered onto `main` (Phase 3B, 2026-08-16)** | document `cripminds-publication-model-v1-2026-08-14.md` recovered verbatim (SHA-256 `c8edb91c...`, confirmed identical to the branch blob and the PP1-preserved export) onto `main` at `.claude/cripminds-publication-model-v1-2026-08-14.md`; WORK.md's 3x citations now resolve. The branch itself remains PARKED — importing one document does not change its lifecycle status |
| publication-surface-v1-2026-08-14 | `-publication-surface-v1` | Publication Surface V1, promotes "What the Room Heard" to a first-class Work | PARKED | off-main doc preserved: `cripminds-publication-surface-v1-2026-08-14.md` |
| production-editorial-upgrade-v1-2026-08-14 | `-editorial-upgrade-v1` | Editorial Upgrade V1 / "E2" experiment — **explicitly "do not deploy as-is" per WORK.md `## 6`** | PARKED | 2 off-main docs preserved: `production-editorial-upgrade-v1-2026-08-14.md`, `production-formula-root-cause-audit-2026-08-14.md` |
| testimony-architecture-2026-08-14 | `-testimony-architecture` | L1/L2 testimony architecture audit | PARKED | off-main doc preserved: `testimony-L1-L2-audit-2026-08-14.md` |

Branches with no worktree (not in the table above, still exist): `persona-safety-fail-closed-release-2026-08-16`
(`169e8ff`, MERGED — this is the release commit that supersedes the candidate above),
`release-pre-rebase-2026-08-14` (`2ad2300`, ancestor of `article-quality-next`),
`pixel-validation/control` (`2a190ad` — diverges from `origin/pixel-validation/control`, see
Open structural issues).

Allowed lifecycle statuses: `ACTIVE`, `FROZEN`, `PARKED`, `MERGED`, `SUPERSEDED`,
`EVIDENCE-ONLY`, `SAFE-TO-ARCHIVE-LATER`, `UNKNOWN`. Never `SAFE-TO-DELETE`.

## Evidence stores

- Mac preservation root: `~/code/cripminds-preservation/` (bundle, CJ1/CJ2 engineering,
  RL-2026-003, off-main docs, whitepaper v0.2 exports, PI2 inventory copy, manifest)
- Trident preservation mirror: `/srv/data/hermes/preservation/cripminds/` (PP2, cross-machine
  redundant copy of the above — hash-verified identical, 674/674 files)
- Five-article evaluation: authoritative original on Trident
  (`/srv/data/hermes/evaluations/cripminds-five-article-2026-08-16/`), preservation copy on Mac
  (`~/code/cripminds-preservation/evaluations/...`) — already cross-machine redundant, do not
  re-copy either direction
- Reader Lab: `reader-lab/rounds/drafts/RL-2026-003.json` + `calibration/candidates/RL-2026-003-*.json`
  — untracked, in-flight, preserved (not published) at `~/code/cripminds-preservation/reader-lab/RL-2026-003/`
- CJ1/CJ2 engineering: `automation/cj1_v3_*.py`, `automation/cj2_*.py`,
  `automation/.probe_fixtures/` — untracked on canonical `main` (52 scripts + fixtures),
  preserved at `~/code/cripminds-preservation/engineering/cj1-cj2-2026-08-16/`
- Production DB authority: Trident's `disability_findings.db` /
  `automation/engagement.db` — no SQLite-safe backup exists yet (open risk, below)

## Safety rules

- No worktree removal before a `PROJECT-MAP.md` + preservation-manifest check confirms the
  worktree's unique commits/docs/untracked material are covered.
- No `git gc`/`git prune` before a fresh `git fsck --unreachable --dangling` check — the 19
  `refs/cripminds-preserve/reflog-2026-08-16/*` refs must keep showing 0 unreachable commits.
- Untracked evaluation evidence must be preserved or indexed before any removal.
- Code authority (Git) and evidence authority (Trident production data, evaluation artifacts)
  are distinct — do not assume one backs up the other.
- Claude-local/private memory is never canonical for this project — treat it as a stale-prone
  pointer, always re-check against this file and `WORK.md`/`LOGBOOK.md`.

## Open structural issues

- Database backup — no SQLite-safe snapshot method exists yet for `disability_findings.db` /
  `automation/engagement.db`; naive `cp` of a live SQLite file is not safe. Separate follow-up.
- ~~`.claude/cripminds-publication-model-v1-2026-08-14.md` — broken WORK.md reference~~ —
  **RESOLVED, Phase 3B (2026-08-16)**: recovered verbatim onto `main`, WORK.md's 3x citations
  now resolve. Document classified HISTORICAL — CONCEPTUAL/ARCHITECTURAL EVIDENCE in `WORK.md ## 8`.
- `pixel-validation/control` (local, `2a190ad`) diverges from `origin/pixel-validation/control`
  (`bfbc017`, 2 commits ahead) — unreconciled, low priority, both sides are git-backed.
- Story Rejection — **RELEASED** (see Active work above), merged as `275470c`, deployed to
  Trident at `9e1c81d` 2026-08-17. The prototype branch itself (`proto/story-rejection-v1`) still
  has no remote (GitHub) copy — proposed ref `origin/experiments/proto-story-rejection-v1` still
  awaits owner approval; this is unrelated to the release, which is a merge+deploy from `main`,
  not a push of the prototype branch itself.
- Trident production checkout is 2 commits behind Mac `main` as of this pass (missing the
  whitepaper-recovery and whitepaper-directory-move docs commits) — routine `git pull`, not a
  preservation risk.
