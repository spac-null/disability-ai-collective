
## CURRENT PHASE (2026-08-20) — PRODUCTION ARCHITECTURE / MIGRATION PLANNING

- **REAL ARTICLE TEST 2: TRANSFER_PASS** (owner decision), evidence commit `8741804`.
  Source: RAIB Report 10/2026, Staniforth Road tram collision. Article "Bell or Horn".
  One writer call, local Claude subscription, clean shadow/manual path.
- **Article Form: TRANSFER-VALIDATED ON TWO MATERIALLY DIFFERENT STORY SHAPES.**
  Edinburgh = structural/semantic discovery case. Staniforth Road = event/system/channel/
  recurrence case. Neither Form was derived from the other.
- **Writer Grounding: SHADOW-CALIBRATED and successfully exercised on Test 2** — it found
  the 2 genuine factual slips, patch-only repair removed them, and no legitimate
  interpretation was flattened. **Still not production-validated.**
- **PRODUCTION IS STILL NOT MIGRATED.** Nothing above implies production validation.
  96 legacy rule families remain active on every live article run.
- Test 2's 1,587-word output (against a 900–1,200 request) is recorded as
  **NON-BLOCKING EDITORIAL / LENGTH-CONTROL DEBT**. Likely owner: ARTICLE FORM. It is NOT
  sufficient reason for another transfer-test generation. No rigid universal length
  mechanism until cross-story evidence exists. Do NOT rerun Test 2, do NOT create Test 2.1,
  do NOT generate a compressed variant. The frozen Test-2 article is not to be modified.
- **PHASE 0 (BASELINE FREEZE): COMPLETE 2026-08-20.**
  `.claude/experiments/production-migration-phase0-baseline-2026-08-20/`
  Production `8af3622` (live, publishing daily); local `c6f97b8`, 25 evidence commits ahead,
  **none deployed**; all 13 pipeline files verified byte-identical local↔Trident. Prompt
  surface hash-frozen. All 5 SQLite DBs safely backed up (`Connection.backup()` +
  `integrity_check: ok`) to a retained root. 5 held-out fixtures identified, no generation.
  snapshot_test passes clean.
  - **CORRECTION:** "no SQLite-safe backup exists" was **false** — a safe daily backup has run
    since 2026-08-10. Fixed in `PROJECT-MAP.md` and the migration plan.
  - **NEW: promotion is stalled** — nothing published since 2026-08-11; 4 of 7 drafts
    `blocked`; `_compute_should_block` actively firing. Baseline condition, not diagnosed.
  - **NEW Phase-2 blocker:** production does not persist fetched source text (only
    `source_hash`), so most fixtures can be verified but not byte-reproduced. Exception:
    `sniff-it-out` shares Edinburgh's frozen source hash `fee0a03b…` exactly.
  - **AR3 HOTFIX DECISION PENDING AFTER BASELINE FREEZE** — rewrite 33/33b NOT patched.
- **PHASE 1 (SHADOW V0): COMPLETE 2026-08-20.**
  `.claude/experiments/production-migration-phase1-shadow-v0-2026-08-20/`
  OFF-by-default vertical slice: 8 artifact contracts, source-text persistence (fixes the
  Phase-0 blocker), positive ACCEPT/HOLD. Golden replay: Test 2 → **ACCEPT**, FORM-1.3 →
  **HOLD** (2 unresolved unsupported). Deterministic across runs. 39/39 safety checks.
  Implementation lives under `.claude/experiments/`; **nothing in `automation/` imports it**;
  no sqlite3/network/subprocess in executable code. Commits `71a5a20` (impl), see LOGBOOK.
  - Writer Grounding receives `{writer_output, source}` only — it structurally cannot change
    the Article Form.
  - LIVE_SHADOW scaffolded, raises, never executed. No model call was made.
- **CURRENT PHASE: PRODUCTION ARCHITECTURE / MIGRATION — Phase 0 and Phase 1 done.
  Phase 2 (live-vs-shadow on held-out stories) NOT started.**
  Plan: `.claude/experiments/production-architecture-plan-2026-08-20/`
- **Central planning finding: ~81% of the 114-family legacy rule debt is DELETED by
  replacing three stages** (the writer prompt, the whole-document rewrite, the two LLM
  rule-judges) — not cleaned. Do NOT patch AR3's rewrite 33/33b, the 9 R-number collisions,
  the UK-preference divergence, or the persona-canon double-injection, and do NOT wire
  `style_rules.py`. Caveat: those debts stay live for the whole migration window; if the
  migration stalls, the cheap AR3 patch becomes correct. Owner decision.

### Superseded phase description (kept for continuity)

## CURRENT PHASE (2026-08-20, superseded) — LEGACY RULE INVENTORY COMPLETE

- **LEGACY PROMPT / RULE INVENTORY: COMPLETE**, commit `38c47b8`.
  Evidence root: `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/`
- **114 rule families** found (96 active in production, 6 shadow/gated-OFF, 7 historical, 5 dead).
- **Mass injection CONFIRMED LIVE**: the writer prompt is assembled per run at
  `automation/orchestrator/generate.py:783–1050` — 59,161 chars / 9,862 words / 75 prescriptive
  rule units for Maya Flux. Four further live rule bundles (rewrite 25,019 ch, planner 15,358 ch,
  review 9,035 ch, gate 8,105 ch). ~130,000 chars of rule text per article.
- **Current production prompt architecture contains substantial legacy baggage**: 19 rule families
  duplicated across 3+ surfaces (8 across all 5), 8 contradictions, 11 owner decisions open.
- **PRODUCTION HAS NOT BEEN CLEANED.** No rule was edited, deleted, wired, or retired.
  Production cleanup is **DEFERRED** until after Article Form transfer validation.
- **REAL ARTICLE TEST 2 MUST USE THE CLEAN SHADOW/MANUAL ARCHITECTURE**, not the current legacy
  production writer prompt. Path: DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING, executed on
  the local Claude subscription. Test 2 is transfer validation, **not** a production-fidelity test.
  Therefore the 96 production-active rule families do **not** block Test 2 — they are excluded.
  Boundary: `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/TEST2-BOUNDARY.md`
  Triage:   `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/OWNER-TRIAGE.md`
- Writer Grounding: **SHADOW-CALIBRATED CANDIDATE — NOT PRODUCTION-VALIDATED, NOT TRANSFER-VALIDATED**
- WG6-N1 (routing) and WG6-N2 (verification semantics): **CLOSED**, commit `a1f2889`
- Final end-to-end shadow replay: **ABORTED_BY_OWNER — DIMINISHING_RETURNS_STOP**, zero model calls.
  Not a failure; nothing was measured. Do NOT reconstruct its missing outputs.
- **Do NOT create WG-7, another Edinburgh grounding experiment, or another FORM version.**
- **NEXT TASK: REAL ARTICLE TEST 2 — design / story selection.**
- Full statement of the binding OWNER STOP RULE: `WORK.md` `## 5b`.

### Four production-critical debts — RECORDED, NOT FIXED

| Debt | Classification |
|---|---|
| AR3 testimony quota still live in `llm.py` rewrite rules 33/33b | MUST_FIX_BEFORE_PRODUCTION_MIGRATION |
| GATE vs REVIEW R-number collisions (9 rules, parsing keys on them) | MUST_FIX_BEFORE_PRODUCTION_MIGRATION |
| Persona canon injected twice, byte-identical, contradictory framing | CONSOLIDATE_BEFORE_PRODUCTION |
| Mass-injected writer prompt | EXCLUDE_FROM_TEST2 + CONSOLIDATE_BEFORE_PRODUCTION |

**Qualification on AR3:** the testimony quota was removed from the **writer prompt** only.
It is still active in the **rewriter**, which runs on every production article. Any wording
claiming testimony requirements are fully removed from the pipeline is inaccurate.

### Superseded phase description (kept for continuity)

- SOFA editorial/artistic method: **CANONICAL** (`.claude/SOFA-METHOD.md`)
- Article Form: **LEADING WORKING ARCHITECTURE** (not production canonical)
- Edinburgh **FORM-1.3**: **FROZEN STRUCTURAL CALIBRATION CANDIDATE**, 3/3 structurally stable
  across byte-identical replicates (source `fee0a03b`, packet `a620d0ce`, prompt `12e520e4`)
- Article Form production status: **NOT DEPLOYED**
- Article Form transfer status: **NOT YET VALIDATED ON A SECOND STORY SHAPE**
- Blocker before Real Article Test 2: **SYSTEMATIC WRITER / GROUNDING FIDELITY**
- **No FORM-1.4.** FORM-1.3 stays frozen so the next experiment isolates the writer/grounding layer.

Boundary: Article Form owns semantic relationships, argumentative burden, reader route, functional
placement, arrival/stop. Writer + grounding control own factual specificity, qualifier preservation,
the fact/interpretation distinction, source-faithful names/times/states/details.

See `.claude/WORK.md` `## 5b` and
`.claude/experiments/sofa-real-ab-1-2026-08-18/iterations/REPLICATE-SET-RESULTS.md`.

READ CURRENT STATE FIRST: `.claude/WORK.md` — doctrine, current production safety state (with
exact SHA), active/next work, parked work, historical corrections, document index. An older
research/audit document is NOT current authority when WORK.md marks its conclusion superseded.

FOR HISTORY: `.claude/LOGBOOK.md` — chronological, compact entries (what changed, when, why,
commit SHA, what it superseded).

FOR EVIDENCE: follow the linked research/audit documents from WORK.md's document index — do not
re-derive conclusions those documents already establish.

FOR THE ARTICLE ARCHITECTURE QUESTION: `.claude/WORK.md` `## 2a` separates four things that are
easy to conflate — the canonical artistic method, the current *working* architecture
(DISCOVERY -> ARTICLE FORM -> WRITER, a hypothesis), what production actually runs (it is NOT
Article Form), and what is parked. `.claude/SOFA-METHOD.md` is the canonical method; read its
SCOPE banner before citing it as architecture. Audit trail:
`.claude/experiments/project-state-reconciliation-2026-08-18/`.

FOR PHYSICAL PROJECT/WORKTREE/EVIDENCE TOPOLOGY: `.claude/PROJECT-MAP.md` — where worktrees,
branches, and preserved evidence physically live and their lifecycle status. Machine-generated
manifest: `.claude/project-manifest.json` (regenerate: `python3 scripts/cripminds_project_inventory.py`).

---

Resume prompt — cripminds.com session continuation

  Project: cripminds.com — Jekyll publication, disability-led AI editorial, 4 AI personas (Pixel Nova/Deaf, Siri Sage/Blind, Maya
  Flux/Mobility, Zen Circuit/Neurodivergent). GitHub: spac-null/disability-ai-collective (PUBLIC repo). Deploys via GitHub Actions
  on push to main — confirm live with `gh run list --workflow="Deploy to GitHub Pages"`, a landed push is not proof it's live.
  SSH: /usr/bin/ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes jascha@trident
  Repo on server: /srv/data/hermes/workspace/disability-ai-collective/ (checked out fresh by cripminds-daily.sh via `git pull`
    before each run — NOT the older /srv/data/openclaw/workspaces/ops/... path, which is stale/pre-migration)
  Orchestrator: automation/production_orchestrator.py (the only orchestrator file as of 2026-08-09 — root-level manual copy and
    opus_rewrite.py were both confirmed dead and deleted that day)
  Rule: always git push origin main after every commit.

  ---
  Cron schedule (verified directly against trident's crontab 2026-08-09 — do not trust older doc claims about schedule times):
  - 06:05 daily: cripminds-daily.sh news       → automation/news_fetcher.py (RSS + keyword scoring → news_seeds table)
  - 09:00 daily: cripminds-daily.sh article     → automation/production_orchestrator.py (writes article, images, Bluesky, deploy)
  - 10:30 daily: cripminds-daily.sh stale-check → alerts if no article in 4+ days
  - Sunday 03:00: automation/link_pool_crawler.py
  - Saturday 10:15: automation/bsky_outreach_auto.py
  - Sunday 10:30: newsletter-weekly-digest.py
  - every 2 days 08:00: automation/publish_best.py
  run_discovery.py and opus_rewrite.py are NOT in the crontab — both deleted 2026-08-09, see git log.

  ---
  Key paths:
  - DB: /srv/data/hermes/workspace/disability-ai-collective/disability_findings.db
    Tables: news_seeds (live, written by news_fetcher.py), findings (dead since 2026-05-02, was run_discovery.py's — kept for
    production_orchestrator.py's fallback read path, never repopulated), article_beats, link_pool, citation_ledger
  - Style rules: **automation/style_rules.py is NOT wired into any prompt** (verified 2026-08-20,
    commit `38c47b8`: 16-rule registry, five render functions, ZERO consumers — the only
    `from style_rules import` in the repo is inside its own docstring example). The rules that
    actually run are hand-typed in four places: generate.py's writer prompt, llm.py's rewrite
    SYSTEM, gate.py's GATE_SYSTEM, review.py's RULES_SYSTEM. Editing style_rules.py changes
    NOTHING at runtime. automation/check_rule_drift.py has no automated runner (no Makefile,
    no CI job, no cron) — manual only. Both classified RETIRE_AFTER_VERIFICATION; do not wire
    style_rules.py in merely because it exists.
  - Social URIs: _social/*.json (bsky_uri + agent)
  - Reviews: _reviews/*.md (citation check sidecars)
  - Engage state: automation/bsky_engage_seen.json
  - Secrets: /srv/secrets/openclaw.env (BSKY_*, TELEGRAM_*, OPENROUTER_API_KEY), /srv/secrets/tumblr.env
  - Model routing: Claude Opus 4.8 via OpenRouter primary; CLIProxy (http://127.0.0.1:8317/v1) is a fallback path only, not
    primary — see automation/README.md for detail, this drifted in older docs before

  ---
  Ongoing work (see project memory `project-cripminds-fabrication-sweep-2026-08-09` for full detail):
  - Style-rules migration: registry + drift-detector shipped; incremental convergence of the ~12 hand-copied rule locations to
    the registry is in progress, one rule per commit.
  - Known gap: writer prompt's "ONE IDEA PER SENTENCE" rule has no downstream gate/review check — advisory-only in prompt text.
