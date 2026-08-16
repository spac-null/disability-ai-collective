# WORK — Canonical Current State

**This is the authoritative entry point for CripMinds project state.** It is mutable and
describes CURRENT TRUTH only — not a diary. History lives in `.claude/LOGBOOK.md`. Full
evidence/methodology lives in the linked documents under `## DOCUMENT INDEX` — do not
duplicate their content here, and do not treat an older document's conclusion as authoritative
if this file marks it superseded.

**Maintenance rule:** every material production release, safety-invariant change, architectural
decision, experiment freeze/unfreeze must update `LOGBOOK.md`, and this file too if current
state changed, in the same commit or an immediately adjacent docs commit. A task that changes
project state but leaves this file stale is not fully closed. Routine article/content commits do
not need a LOGBOOK entry unless they expose a material system finding.

Last reconciled: 2026-08-16, against origin/main @ `667633f`.

---

## 1. CORE DOCTRINE (short canonical statements — full whitepaper is evidence-only, not reproduced here)

- **Core claim:** "The disability lens has to reveal the hidden mechanism of the thing itself, not just show that disabled people are affected by it."
- **Commissioning question:** "What does this disabled way of perceiving make knowable about the subject that the dominant framing misses?"
- **Reader experience:** "Don't tell me the insight. Make me discover it with you."
- **Method shape:** something concrete → mismatch → investigate → frame moves → disability-derived knowledge exposes hidden mechanism → subject becomes larger/different.
- **Publication logic:** SUBJECT → HIDDEN MECHANISM → WHAT MUST BE NOTICED → FORM.
- **Tool logic:** MECHANISM → FORM → MATERIAL → TOOL.
- Doctrine is called "K" in the A-M working list below; live in `automation/orchestrator/llm.py`'s system prompts today. Full doctrine/whitepaper evidence: `.claude/experiments/why-we-write-2026-08-10.md`.
- **Persona canon authority (do not relitigate):** a claimed biographical/experiential detail for a persona is authorized ONLY if it's in `automation/persona_canon/<slug>.md` or `<slug>-factual.md`. "Fits the persona" / "plausible" / "sounds consistent with the theme" is explicitly and repeatedly rejected as evidence (caught once already as a real mistake — see LOGBOOK "AP1"). Two provenance modes exist and are not interchangeable: `real_person_evidence` (Pixel Nova only) and `editorial_canon` (Maya Flux / Siri Sage / Zen Circuit — legitimate to draw on their own established fictional history, not license to invent beyond it).
- **Jascha archive scope (do not relitigate):** the real evidence archive behind Jascha Blume's own documented Deaf art practice authorizes facts for **Pixel Nova only** (the one persona modeled on Jascha's real biography). It is explicitly NOT factual authority for the other three personas' claimed experience — their `persona_factual_context` is intentionally empty/fail-closed. Evidence: `automation/persona_canon/pixel-nova-factual.md`, `.claude/experiments/phase-1.6-source-grounding-2026-08-11.md`.
- **Two independent safety domains (do not merge, do not assume one covers the other):**
  - *Source-derived human-detail provenance* — "is this detail really in what we read?" (checks claims against fetched source material). System: `automation/orchestrator/human_detail_provenance.py`. **Shadow-only, non-blocking.**
  - *Author-persona biography provenance* — "is this something this persona is actually authorized to say happened to them?" (checks first-person claims against persona canon). System: AP1/APE2 (see `## 3` below). **Live, blocking, as of 2026-08-15/16.**
  - Quoted directly from `.claude/author-persona-biography-provenance-2026-08-14.md`: "An article can pass the first check completely... and still fail the second... they are independent failure modes with independent evidence packets... Do not merge these into one guard or assume one subsumes the other."

## 2. CONCEPTUAL ARCHITECTURE — STATUS: UNCONFIRMED, DO NOT ASSUME LIVE

A staged conceptual pipeline shape (e.g. DISCOVERY → SOURCE → SUBJECT → MECHANISM → LENS →
VOICE) was named in a task brief as something to audit. **Direct research against the two most
likely documents (`master-roadmap-2026-08-13.md`, `original-blueprint-A-M-reconciliation-2026-08-13.md`)
found no such named scheme anywhere in the repo.** What actually exists as the live pipeline's
real stage list (per the master roadmap's own reconstruction, since no end-to-end design doc
exists): topic/source acquisition → persona selection (keyword-routed, not yet CJ-2) → pre-write
editorial brief ("Fable brief") → draft generation → pre-commit gate → fact-check → publish →
post-publish async review → social. **If a DISCOVERY/SOURCE/SUBJECT/MECHANISM/LENS/VOICE
document exists, it has not been located by this consolidation pass — treat as unconfirmed until
someone points to it directly, do not cite it as established architecture.**

Similarly **unconfirmed**: a brief mentioned "GENERATE originally meant representational material,
not generative AI; MATERIALIZE was later recommended terminology." Not found in either roadmap
doc. May live in the Format Lab v1/v2 worktree docs (branches referencing "generative media,"
dated 2026-08-14) — not yet checked. Do not assert this terminology history as fact until checked
directly.

## 3. CURRENT PRODUCTION SAFETY STATE

**Current production SHA: `667633f21088b3f0ff556633d036bc39fba4eb0d`** (= `origin/main`, confirmed
identical, pushed). Commit: "fix: legacy-draft auto-promotion fail-closed closure." **Do not
copy any SHA reported in an older `.claude/*.md` document without re-checking — several of those
documents explicitly describe their own commits as "not pushed" at time of writing; some of those
have since landed, some proposals have not.**

Authoritative safety-invariant chain, verified directly in code (not just doc claims):

1. **AP1** (`dbe0a96`, 2026-08-15) — author-persona biography provenance, primary fix. Closed two
   gaps: `rewrite_with_opus` had zero invented-biography check (now runs the same
   `_reject_if_unsupported_specifics` guard the other two revision paths use); the editorial
   reviewer's first-person-episode check existed but was under-enforced (competed for a shared
   note budget, could be silently dropped) — now a dedicated `unsupported_persona_claims` field
   that deterministically forces `verdict="revise"`.
2. **APE2** (`e93bb1b`, 2026-08-15) — edge case: a non-Opus draft with a pre-existing unsupported
   persona claim that `rewrite_with_opus` *preserves* (not introduces) was invisible to AP1's
   diff-based guard. Fixed by extracting the review+guard cycle into one shared method called
   from both the Opus and non-Opus branches.
3. Two further fail-closed corrections landed 2026-08-16 (`89cd082`, `169e8ff`) — DETECTED-BUT-
   UNCORRECTED persona-biography claims now fail closed (previously a detected-but-not-repaired
   claim could still slip through).
4. **PS1 + LPF1** (`667633f`, 2026-08-16, current HEAD) — the legacy-draft auto-promotion hole.
   `publish_best.py`'s only prior content-safety check was `fact_check_status != "blocked"` — a
   missing field, or a stale legacy `"verified"` from before AP1/APE2 existed, both read as
   promotion-eligible with zero re-check against current safety code. This is exactly how
   "Reached by Boat or Plane" (see LOGBOOK) promoted itself unexamined. Fix, verified directly in
   `automation/orchestrator/generate.py` and `automation/publish_best.py`:
   - `generate.py._maybe_stamp_publication_safety_version` stamps `publication_safety_version: 1`
     onto a draft's front matter ONLY once `fable_brief`/`gate_llm`/`persona_biography_unresolved`
     have all settled clean for that run AND `fact_check_status` is the literal `"verified"`,
     re-read from disk (not a cached verdict).
   - `publish_best.py` now requires BOTH `fact_check_status: verified` AND
     `publication_safety_version >= REQUIRED_SAFETY_VERSION` (currently `1`) before a draft is
     promotion-eligible. Anything else is HELD (`NEEDS_CURRENT_REVALIDATION`), left untouched on
     disk, never auto-archived or auto-rewritten by this gate.

**Invariant: UNKNOWN SAFETY != SAFE.** A draft or legacy article lacking a current
`publication_safety_version` is held for revalidation, not treated as safe by default.

**Confirmed gap, not yet closed:** the PS1 gate above does **not** reference
`human_detail_provenance` at all (checked directly — zero hits in `generate.py`'s stamping
method). Source-derived human-detail provenance remains shadow-only and is not part of the
promotion gate. This is the correct current state of the "two independent domains" split in `## 1`
— it is not a bug, but it means PS1 only closes the persona-biography failure mode, not the
source-provenance one.

**Not yet remediated publicly:** "Reached by Boat or Plane" (`_posts/2026-08-11-reached-by-boat-or-plane.md`,
published 2026-08-15) still carries the pre-LPF1 `fact_check_status: verified` stamp with **no
`publication_safety_version` field at all** — confirmed directly by reading its current front
matter. Under the new gate's own criteria this article would be `NEEDS_CURRENT_REVALIDATION`
today. It has not been corrected, withdrawn, or re-verified since LPF1 landed. See LOGBOOK entry.

## 4. LEGACY CORPUS INTEGRITY — REMEDIATION REQUIRED (Phase 1 complete, Phase 2 not started)

Full audit: `.claude/legacy-corpus-integrity-phase1-2026-08-16.md` +
`.claude/audits/legacy-corpus-integrity-2026-08-16.json`. Decision recorded: **LC1 — material
legacy credibility risk, begin prioritized remediation.** Highest-priority single item:
`research/care-labor.html` (real named individual + real named company, factual mismatch against
the actual tribunal record). Do not re-run Phase 1's inventory/era-mapping from scratch — read
the report and JSON manifest first.

## 5. ACTIVE / NEXT WORK (one causal thread, not five separate projects)

These are stages of **one investigation** — persona-routing/architecture correctness feeds the
conceptual-architecture question, which is the actual prerequisite for CJ-2, which is the actual
prerequisite for the source/feed-concentration audit blind spot being worth fixing structurally
rather than one-off. Do not spin these up as five independent efforts.

1. **Conceptual-architecture causal audit** — confirm or refute whether a
   DISCOVERY→SOURCE→SUBJECT→MECHANISM→LENS→VOICE (or any) staged architecture is real,
   documented, and intended vs. an unconfirmed brief artifact (see `## 2`). Do this before
   trusting any roadmap language that assumes it exists.
2. **Legacy corpus remediation, Phase 2** — semantic re-read of the 122 unsampled articles from
   the Phase 1 audit, starting with `research/care-labor.html` (static page, immediate).
3. **"Reached by Boat or Plane" recommission/remediation decision** — not yet decided. Do not
   silently withdraw or silently patch; this is a real editorial decision pending, see LOGBOOK.
4. **Source/feed concentration investigation** — Guardian dominates ~59% (50/85) of
   `source_url`-bearing articles and was entirely WebFetch-unreachable during the article-quality
   evidence pass, meaning that slice of the corpus could not be independently source-audited this
   session. Distinct from feed *diversity* — this is an **audit blind spot**, not (yet) a
   confirmed editorial-diversity problem.
5. **Persona-routing authority investigation** — `_THEME_TO_PERSONA` / keyword-routing bugs found
   by `.claude/persona-architecture-audit.md` (Maya Flux is the default/`else` bucket yet has the
   lowest 60-day publish count; the global FORBIDDEN_DEFAULTS ramp/curb-cut/grab-rail ban
   collides almost entirely with Maya's own core evidentiary vocabulary). Target architecture
   (CJ-2-based soft-affinity routing) is **Phase 3, confirmed not started.**

Also open, not part of the causal thread above but real and unresolved:
- `rewrite_with_opus`'s duplication-blind acceptance check (`automation/orchestrator/llm.py`,
  weak `count("---") >= 2` check) is **still live and unpatched** — only the one known symptom
  (`the-floor-plan-of-disappearance`) was manually repaired (`64d1658`), the class of bug was not.
  Any future non-Opus-origin draft could reproduce it.

## 6. PARKED / DO NOT ACCIDENTALLY RESTART

- **CJ-2** (competitive persona-reframing architecture) — OFF (`CJ2_INTEGRATION_MODE` defaults to
  `"OFF"` in code, confirmed in `generate.py`/`cj2_shadow.py`). Substantial design work exists
  (4-engine-capsule Stage A/Stage C architecture, frozen after 4 correction rounds). OFF because
  the evaluation-freeze protocol's requirements remain outstanding, NOT because the work was
  abandoned. Outstanding, per `.claude/experiments/final-evaluation-freeze-protocol-2026-08-13.md`:
  RL-2026-002 analysis incomplete; RL-2026-003 designed but not ingested/published; Stage-C has
  0/14 natural safe admissions (needs ≥2 qualitatively different ones); no fresh held-out corpus
  exists anywhere in the repo yet; exactly one consolidated B2 revision (not one per round) is
  still owed. **CJ-1** is separately frozen as `cj1-v3.2-validity-before-recall` — a research
  input contract, not yet a production gate.
- **L2 testimony** (active companion-source retrieval) — OFF (`L2_TESTIMONY_MODE` defaults to
  `"OFF"` in code, confirmed). Scaffolding shipped, live search deliberately not built. Blocked on
  cost/latency (a Sonar call per eligible run), ranking design (no tie-break rule), source-trust
  policy (can a companion share an outlet with the primary source?), and heuristic calibration —
  not a single blocker.
- **Reader Lab RL-2026-002** — analyzed-in-progress, not paused/abandoned; other phases (B-F of
  the CJ-2 roadmap) wait on it, it does not wait on them. **RL-2026-003**: fully designed/frozen
  locally (`reader-lab/rounds/drafts/RL-2026-003.json`, `calibration/candidates/RL-2026-003-*.json`)
  but **these files are untracked in git as of this audit** — genuinely uncommitted work-in-progress,
  not yet ingested or published. Do not assume this is a clean "parked" state; it's mid-flight.
- **Formula/rhetorical-device quality work** — a "production formula root-cause audit" (`dc3186f`,
  2026-08-14) traced 7 rhetorical devices (e.g. a reversal-sentence pattern, ~44% corpus
  prevalence) to actual code causes, multi-causal. **Do not blindly patch prompts** — the fix
  requires addressing multiple root causes together, not a one-line prompt edit. Full detail not
  yet re-verified by this consolidation pass; treat `dc3186f`'s commit body as the current source
  until someone reads it in full.
- **Production Editorial Upgrade V1 / "E2"** — mixed paired-experiment result referenced by the
  author-persona-biography doc (Maya Flux/Siri Sage each invented an anecdote under this
  experiment). **Do not deploy** V1 as-is; this is what led to AP1.
- **Phase H (master-roadmap sense: CJ-2 article-level/full-pipeline validation)** — preregistration
  only, written 2026-08-14 (`.claude/phase-h-article-pilot-protocol-2026-08-14.md`), explicitly
  "does not schedule Phase H." Gated on Phase F (production-candidate review) completing, which
  has not happened. **Naming collision, recorded so it isn't rediscovered as a contradiction:**
  this is a DIFFERENT "H" than the G/H/I items in the article-quality A-M working list (`## 7`
  below) — same letters, two unrelated numbering schemes, confirmed by cross-checking both source
  documents.

## 7. HISTORICAL CORRECTIONS (prevent these mistakes from recurring)

- **No literal historical A-M blueprint document exists in this repo.** Exhaustive git
  archaeology (`git log --all -i -S"<phrase>"` across 1,320+ commits) found zero hits for any
  distinctive A-M phrase. The 13-topic A-M list is a **reconstructed working list**, letters kept
  as labels only, not a citation to a real historical document. Full status per letter:
  `.claude/original-blueprint-A-M-reconciliation-2026-08-13.md`.
- **"RLS1", "H1", "PS1" as used in project-memory shorthand are NOT literal strings found in repo
  docs** — they are labels this consolidation introduced to name real, evidence-backed events:
  - RLS1 = the combined 2026-08-15 release (Work "What the Room Heard", `aa0172e`/`691c365` +
    AP1 persona-biography safety, `dbe0a96`) — both shipped and documented same day.
  - H1 = the 2026-08-14 natural overnight production run + morning-stabilization validation
    (`.claude/overnight-main-run-2026-08-14.md` + `.claude/morning-stabilization-2026-08-14.md`).
    **Not the same thing as master-roadmap "Phase H"** (see `## 6` above) — do not conflate.
  - PS1 = the `publication_safety_version` contract introduced in `667633f` (2026-08-16). A
    **different** document separately uses the label "P1" for the human-detail-provenance gap
    finding — a different system. Do not conflate PS1 (persona-biography promotion gate) with P1
    (human-detail provenance shadow finding).
- **GENERATE vs. MATERIALIZE terminology claim: unconfirmed** (see `## 2`).
- **Jascha archive is a compass for Pixel Nova's own factual authorization only** — not training
  data or factual authority for the other three (fully fictional) personas' claimed experience.
- **Persona canon authorizes specific biography; "fits the persona" is not evidence.** A notary/
  legal-deed anecdote was once mistakenly marked AUTHORIZED in Pixel Nova's canon on exactly that
  reasoning, then caught and corrected — see `automation/persona_canon/pixel-nova-factual.md`.
- **Source-human-detail provenance and author-persona-biography provenance are different safety
  domains** — see `## 1`. A fix to one is never evidence the other is covered.
- **RL-2026-002 is not "blocked"** — it is actively awaited by other phases, not itself stalled by
  anything technical. Treat "parked" language about it cautiously (see `## 6`); "in progress,
  proceeding asynchronously" is the more accurate framing per the two most current source docs.
- **The "five-article production-parity batch" does not exist as such.** The actual evaluation
  behind that claim is a 140-article deterministic sweep + a 15-article manual stratified sample
  (`.claude/article-quality-evidence-pass-2026-08-14.md`). Persona-biography fabrication in that
  evaluation was a **designed paired experiment** (two personas each deliberately tested), not
  spontaneous/naturalistic model behavior — plus one separate real historical incident (a
  fabricated "Rotterdam wayfinding review" that shipped before any guard existed).
- **The real image-generation stack is OpenRouter + Recraft V4.1**, confirmed directly in
  `automation/gen_images.py`/`gen_persona_avatars.py`. `automation/README.md` still says
  "Pollinations FLUX API" — stale, not corrected as of this audit.
- **`docs/DISCOVERY.md` is explicitly self-marked historical** ("this document describes
  `run_discovery.py`, deleted 2026-08-09... treat everything past this notice as historical, not
  current architecture") — a good example of the marking convention to reuse elsewhere.

## 8. DOCUMENT INDEX

| Document | Status | What it's for |
|---|---|---|
| `.claude/WORK.md` | **CURRENT** | this file |
| `.claude/LOGBOOK.md` | **CURRENT** | chronological history, compact entries |
| `.claude/CONTEXT.md` | **CURRENT** | ops facts: cron schedule, DB tables, secrets paths, model routing — read this for "how do I operate the pipeline," not "what's the state of the research" |
| `.claude/current-work.md` | **SUPERSEDED (by this file)** | 266KB historical log, kept as an archive/evidence trail, no longer the entry point — see banner at its top |
| `.claude/master-roadmap-2026-08-13.md` | **HISTORICAL, frozen 2026-08-13** | CJ-2/B2 phase table (A-J), reconciles two ancestor docs; repo has moved past its "ahead N commits" claims — trust its phase-table structure, not its "current HEAD" claims |
| `.claude/original-blueprint-A-M-reconciliation-2026-08-13.md` | **HISTORICAL, frozen 2026-08-13, re-checked 2026-08-14 (commit `204c3bc`)** | per-letter A-M status; G/H/I re-confirmed done that day |
| `.claude/experiments/final-evaluation-freeze-protocol-2026-08-13.md` | **CURRENT (governance)** | the actual CJ-2/B2 freeze requirements — read this, not a paraphrase, before touching CJ-2 |
| `.claude/experiments/cj1-v3-friction-gate-2026-08-11.md` | **CURRENT (frozen research artifact)** | CJ-1 frozen contract + 3 parked implementation issues |
| `.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md` | **CURRENT (frozen architecture, pre-freeze)** | CJ-2 4-engine-capsule design, 4 correction rounds |
| `.claude/experiments/phase-1.6-source-grounding-2026-08-11.md` | **CURRENT (shipped)** | source-grounding hardening, Jascha-archive/Pixel-Nova scope evidence |
| `.claude/experiments/why-we-write-2026-08-10.md` | **CURRENT (shipped doctrine decision)** | full doctrine/whitepaper validation |
| `.claude/experiments/fable-review-roi-2026-08-10.md` | **PAUSED, not concluded** | Fable review-seat ROI, resumes post-grounding |
| `.claude/author-persona-biography-provenance-2026-08-14.md` | **CURRENT (shipped, AP1/APE2)** | canon authority rule, two-domains statement |
| `.claude/human-detail-provenance-and-source-completeness-2026-08-14.md` | **CURRENT (shadow-only)** | P1 finding, source-truncation fix (S2A) |
| `.claude/l2-testimony-design-2026-08-14.md` | **CURRENT (OFF, scaffolding only)** | why L2 isn't live yet |
| `.claude/floor-plan-repair-proposal-2026-08-14.md` | **SUPERSEDED (content fixed by `64d1658`)** | proposal text now historical; underlying `llm.py` bug is NOT fixed, see `## 5` |
| `.claude/repetition-shadow-corpus-harvest-2026-08-14.md` | **CURRENT (shadow-only, no-promotion date 2026-08-28)** | repetition detector characterization |
| `.claude/persona-architecture-audit.md` | **CURRENT (Phase 1.5A done, Phase 3 not started)** | territory-ownership bugs, target architecture |
| `.claude/persona-souls-pixel-nova-unresolved.md` | **EVIDENCE-ONLY** | the 4 personas' origin/wound/giddiness/indefensible/Tuesday texture notes |
| `.claude/reader-lab-v0-design-2026-08-12.md` | **CURRENT (live system, addenda through 2026-08-13)** | Reader Lab architecture, RL-YYYY-NNN convention |
| `.claude/reader-lab-handoff/*` | **EVIDENCE-ONLY** | RL-2026-001's ops-request/receipt/analysis/export trail |
| `.claude/bregman-anchor-corpus.md` | **CURRENT (standing style-judge reference)** | Rutger Bregman craft-analysis corpus |
| `.claude/bregman-architecture-analysis.md` / `-write-economy-analysis.md` | **CURRENT (completed analysis passes)** | technique breakdowns feeding style_rules.py |
| `.claude/design-scorecard.md` | **HISTORICAL, closed 2026-08-05** | site-wide WCAG/visual-polish audit, methodology reusable if new pages ship |
| `.claude/audience-engagement-tasklist.md` | **CURRENT (live backlog, not yet approved)** | engagement-loop discussion draft, DEFERRED/OPEN BUG/WAITING/REJECTED taxonomy |
| `.claude/2026-08-10-engagement-db-incident.md` | **CLOSED/EVIDENCE-ONLY** | fully recovered, standing mitigation shipped |
| `.claude/audit-prompt.md` | **CURRENT (reusable template)** | live-pipeline QA audit procedure |
| `docs/production-release-procedure.md` | **CURRENT** | automation/ release checklist (Reader Lab explicitly out of scope) |
| `docs/DISCOVERY.md` | **HISTORICAL (self-marked)** | describes a deleted script, kept as disability-studies reference only |
| `.claude/legacy-corpus-integrity-phase1-2026-08-16.md` + `.claude/audits/*.json` | **CURRENT** | public-corpus credibility audit, Phase 1 (Phase 2 not started) |
| `automation/persona_canon/*.md` | **CURRENT (authoritative)** | the actual persona factual-authorization files |

---

*Update this file when current state changes. Do not let it grow into a diary — if a section is
about to become a narrative, it belongs in a linked document instead, with a pointer here.*
