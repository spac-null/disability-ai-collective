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

Last reconciled: 2026-08-16 (PM1.1 correction pass), against `ORIGIN_MAIN_HEAD` — see exact value
in `## 3`'s SHA table, not restated here to avoid this header going stale again the way the SHA
claim did in the PM1 pass.

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

## 2. CONCEPTUAL ARCHITECTURE

**Two genuinely different things use similar-sounding "staged pipeline" language. Do not conflate them.**

**(A) DISCOVERY → SOURCE → SUBJECT → MECHANISM → LENS → VOICE — STILL UNCONFIRMED, do not assume
live.** This exact shorthand was named as something to audit; direct research against the two
most likely documents (`master-roadmap-2026-08-13.md`, `original-blueprint-A-M-reconciliation-2026-08-13.md`)
found no such named scheme anywhere in the repo, and a further targeted search of the Format Lab/
Publication Model branch docs (`.claude/cripminds-publication-model-v1-2026-08-14.md` and
siblings, recovered from git branches `format-lab-v0/v1/v2-2026-08-14`, `publication-model-v1-2026-08-14`
— none of these landed on `main`) also found no match. What actually exists as the live pipeline's
real stage list (per the master roadmap's own reconstruction, since no end-to-end design doc
exists): topic/source acquisition → persona selection (keyword-routed, not yet CJ-2) → pre-write
editorial brief ("Fable brief") → draft generation → pre-commit gate → fact-check → publish →
post-publish async review → social. **If a DISCOVERY/SOURCE/SUBJECT/MECHANISM/LENS/VOICE document
exists, it has not been located after two consolidation passes — treat as unconfirmed until
someone points to it directly, do not cite it as established architecture.** The 2026-08-16
five-article evaluation (`## 4a` below) gives real-world evidence that persona-routing/mechanism
correctness is a live, material problem — it does NOT establish that this specific staged
architecture is the intended fix; that's still open.

**(B) The persona target architecture — CORE PERSON / PERCEPTUAL ENGINE / MOTIVE / AFFINITY /
RISK / TEXTURE — IS established, documented design history (2026-08-10), separate from (A) and
NOT invented by this consolidation.** Recovered in full from `.claude/persona-architecture-audit.md`
(Phase 1.5A, per-persona hypotheses already drafted for all four personas under these six
categories) and from commit `b2773c8` (2026-08-10) — content that was later pruned from
`current-work.md` during its `d6ad389` "lean operational checkpoint" rewrite and is reconstructed
here from git history so it isn't lost twice:

- Historical persona territories are **hypotheses, not canon** — the four personas should NOT
  own subject territories. Two confirmed bug classes: OWNERSHIP (Siri Sage's own prompt block
  contains a literal "those belong to Pixel Nova" prohibition — a textual ownership claim, not an
  affinity) and SUPPRESSION (a global FORBIDDEN_DEFAULTS list bans exactly the concrete imagery
  — ramp/curb-cut/grab-rail — that is Maya Flux's own core evidentiary vocabulary).
- **AFFINITY replaces "territory"**: a soft routing prior only, never an ownership gate. A strong
  reframe from a "wrong" persona should beat a mediocre reframe from the "assigned" one.
- **Success criterion**: a persona's perceptual engine makes the SAME WORLD OBJECT become a
  different thing — not "which persona is appropriate for this topic."
- **Preregistered validation idea (design only, not run):** give ONE genuinely rich,
  non-disability source — deliberately chosen OUTSIDE all four personas' assumed affinities (a
  supermarket pricing system, a school timetable, a heatwave policy) — to all four personas, and
  score: **WHAT DID THIS MIND NOTICE** (a mechanism the other three missed?), **CATEGORY JUMP**
  (did the lens change what kind of thing the source turned out to be?), **IRREDUCIBILITY** (could
  another persona's name be swapped onto the essay without fundamentally changing it?),
  **OVERLAP** (did two+ personas converge on the same mechanism?), **LORE LEAKAGE** (did the
  writer just import their disability biography into an unrelated story instead of actually
  perceiving something?). "If a persona is only distinctive inside their assumed topic, they don't
  yet have a perceptual engine — they have a beat."
- **Downstream consequence for CJ-2** (recorded 2026-08-10, not scheduled): routing should become
  "what does each persona's perceptual engine expose about this source, then which reframe is
  strongest/least generic/best evidenced" — competitive reframing, not topic assignment.
  Affinities survive only as small priors, never a gate.
- **Status: Phase 3, confirmed NOT STARTED.** No motive sentences are finalized for any of the
  four personas. The 2026-08-16 evidence (`## 4a`) shows real brief-persona/byline-persona
  mismatches in production-realistic runs — this is new empirical support that the problem is
  real, it did **not** invent this architecture; the architecture predates it by six days.

**GENERATE vs. MATERIALIZE — CONFIRMED**, found in `.claude/cripminds-publication-model-v1-2026-08-14.md`
(git branch `publication-model-v1-2026-08-14`, never merged to `main`): the roadmap phrase
**"WHY → KNOW → SEE → GENERATE → MAKE → PROVE"** used GENERATE to mean "what representational
material must exist for the insight to become perceptible" — every document using this roadmap
had to explicitly restate that GENERATE does *not* mean "use generative AI." **MATERIALIZE was
recommended (not applied) as replacement terminology** going forward from that document only —
explicitly NOT retroactively rewritten into the earlier V0/V1 docs, "those are historical records
of what was actually reasoned and decided at the time." Verbatim source quote preserved in that
branch document; do not retroactively edit V0/V1 language to match.

## 3. CURRENT PRODUCTION SAFETY STATE

**SHA semantics — these are legitimately different fields, do not collapse them:**

| Field | Value | What it means |
|---|---|---|
| `ORIGIN_MAIN_HEAD` | `ed741bb57e90d9077277777adf87569680f1a6e6` | latest commit on GitHub `origin/main` (this PM1.1 correction commit) |
| `TRIDENT_DEPLOYED_HEAD` | `667633f21088b3f0ff556633d036bc39fba4eb0d` (confirmed via direct SSH read, 2026-08-16) | what the production checkout on Trident has actually pulled and is running — **one commit behind** `ORIGIN_MAIN_HEAD` as of this reconciliation, because deployment happens via the daily cron's `git pull`, not immediately on push |
| `LAST_PRODUCTION-CODE_RELEASE` | `667633f` | last commit that changed `automation/` behavior (PS1/LPF1, below) |
| `LAST_MEMORY_RECONCILIATION_COMMIT` | `ed741bb` (PM1 install), corrected again in this same section's own commit (PM1.1) | docs-only, no production code changed |

A docs-only memory commit advancing `ORIGIN_MAIN_HEAD` does NOT mean production code changed —
check `LAST_PRODUCTION-CODE_RELEASE` for that. **Do not copy any SHA reported in an older
`.claude/*.md` document without re-checking** — several of those documents explicitly describe
their own commits as "not pushed" at time of writing; some have since landed, some proposals have not.

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
3. **PS1** (candidate `89cd082`, deployed integration `169e8ff`, 2026-08-16) — DETECTED-BUT-
   UNCORRECTED author-persona biography fail-closed closure: previously a claim the reviewer
   flagged for revision, but which the revision failed to actually remove, could still slip
   through to publication. Now a known flagged persona claim surviving a failed revision blocks
   publication outright. **Direct empirical case that motivated this fix:** the 2026-08-16
   five-article evaluation found exactly this failure mode twice (runs 05 and 07 — a flagged
   claim survived revision into the final draft text); see
   `.claude/post-release-five-article-evaluation-2026-08-16.md`.
4. **LPF1** (`667633f`, 2026-08-16, current `LAST_PRODUCTION-CODE_RELEASE`) — the legacy-draft
   auto-promotion hole, a DIFFERENT closure from PS1 above (do not conflate — PS1 is about a
   flagged claim surviving revision *within one generation run*; LPF1 is about a *historical*
   draft/article with stale or missing safety metadata being auto-promoted later without
   re-checking against current safety code). `publish_best.py`'s only prior content-safety check
   was `fact_check_status != "blocked"` — a missing field, or a stale legacy `"verified"` from
   before AP1/APE2/PS1 existed, both read as promotion-eligible with zero re-check. This is
   exactly how "Reached by Boat or Plane" (see LOGBOOK) promoted itself unexamined. Fix, verified
   directly in `automation/orchestrator/generate.py` and `automation/publish_best.py`:
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

**Confirmed gap, not yet closed:** the LPF1 gate above does **not** reference
`human_detail_provenance` at all (checked directly — zero hits in `generate.py`'s stamping
method). Source-derived human-detail provenance (**P1**, a third, separate label from PS1/LPF1 —
see `## 1`'s two-domains note) remains shadow-only and is not part of the promotion gate. This is
the correct current state of the "two independent domains" split in `## 1` — it is not a bug, but
it means LPF1 only closes the persona-biography failure mode, not the source-provenance one.

**Not yet remediated publicly, and its plan/persona divergence is now CONFIRMED (was UNVERIFIED
in the PM1 pass):** "Reached by Boat or Plane" (`_posts/2026-08-11-reached-by-boat-or-plane.md`,
published 2026-08-15) still carries the pre-LPF1 `fact_check_status: verified` stamp with **no
`publication_safety_version` field at all** — confirmed directly by reading its current front
matter. Under the new gate's own criteria this article would be `NEEDS_CURRENT_REVALIDATION`
today. It has not been corrected, withdrawn, or re-verified since LPF1 landed.

Direct query against Trident's production `engagement.db`, `article_plans` table (`planned_at:
2026-08-11 09:05:59`), confirms: the DB `agent` column for this slug is **Siri Sage**, but the
persisted `plan_json`'s own `"persona"` field is **Maya Flux**, and the plan's `correction_moment`/
`resisting_example` evidence is centered on the building's physical-access/commission requirements
("wheelchair clearance, threshold, and approach," a courtyard gate's specified dimensions) —
Maya Flux's mobility/access domain. The final published article is instead about
acoustics/listening/ferry-recordings — Siri Sage's domain, and a different sensory mechanism
than the persisted plan specified. **The exact Aug-11 "Agent rebalanced X → Y" log line is not
recoverable** (checked directly: `grep` against `automation.log` for this slug returns no
routing-decision line) — the specific rebalancing EVENT is inferred from this surrounding
mechanism/plan evidence, not directly logged. The persisted PLAN ↔ final PERSONA/ARTICLE
divergence itself, however, is direct DB evidence, not inference. See LOGBOOK entry.

## 4. LEGACY CORPUS INTEGRITY — REMEDIATION REQUIRED (Phase 1 complete, Phase 2 not started)

Full audit: `.claude/legacy-corpus-integrity-phase1-2026-08-16.md` +
`.claude/audits/legacy-corpus-integrity-2026-08-16.json`. Decision recorded: **LC1 — material
legacy credibility risk, begin prioritized remediation.** Highest-priority single item:
`research/care-labor.html` (real named individual + real named company, factual mismatch against
the actual tribunal record). Do not re-run Phase 1's inventory/era-mapping from scratch — read
the report and JSON manifest first.

## 4a. POST-RELEASE FIVE-ARTICLE EVALUATION (2026-08-16) — separate experiment, do not merge with the Aug-14 evidence pass

Full evidence doc (reconstructed from Trident-preserved run artifacts, not from memory):
`.claude/post-release-five-article-evaluation-2026-08-16.md`. Ran on Trident, isolated worktree,
exact release `691c365`, real production providers, 7 generation attempts across 5 distinct
stories, zero production mutation (`commit_success: false` on every run). Durable findings,
each corrected against raw counts a prior pass got wrong:

- Brief-persona ≠ final byline-persona in **5 of 5** runs where a brief was captured (not "4/4").
- **4 of 7** runs (not "5 of 7") produced a genuine natural unsupported-persona-biography attempt
  (checked against `fable_reviews[0].unsupported_persona_claims`, cross-checked against the final
  draft text).
- Of those 4 detected attempts, **2 were successfully corrected** (removed from final text) and
  **2 survived the revision into the final draft** (runs 05, 07) — this exact failure mode is
  what PS1 (`## 3`) was built to close.
- Real image stack (OpenRouter → Recraft V4.1) reconfirmed, corroborating the earlier finding.
- No preserved literary-quality ranking exists — a "3 STRONG / 2 PROMISING" claim is **not
  confirmed by any artifact** and is not asserted as fact; would need a fresh editorial read.

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
- **Reader Lab RL-2026-002 — PUBLISHED to production D1, not "frozen, never published."** The
  local research-session draft file (`reader-lab/rounds/drafts/RL-2026-002.json`) still carries
  its own original `status: "draft_prepared_by_research_session_not_saved_to_production"` line,
  which is why an earlier pass read it as unpublished — but that file has its own uncommitted
  `status_correction_2026-08-14` annotation (verified directly, present in the working tree,
  matched identically on Trident) stating: production D1 `rounds.status='published'`,
  `published_at=2026-08-13T14:32:22.184Z`, `source='admin_ui'`, `manifest_sha256=b2c82a2e...`.
  Publication happened via the admin UI/candidate-bridge path, independent of the research-session
  file, which was simply never updated afterward. **Current structural state (as last checked,
  2026-08-14): 5 items, 10 assignments (2 reviewers × 5 items), 0 served, 0 answered** — not
  because of any code/data defect, but because neither assigned reviewer (`reviewer_parent_a`,
  `reviewer_parent_b`, both valid/active) has revisited their invite link since publication. No
  evidence of active pressure on reviewers to continue immediately. Other CJ-2 freeze-protocol
  phases (B-F) wait on this round's eventual analysis; it does not wait on them.
  **RL-2026-003**: fully designed/frozen locally (`reader-lab/rounds/drafts/RL-2026-003.json`,
  `calibration/candidates/RL-2026-003-*.json`) but **these files are untracked in git as of this
  audit** — genuinely uncommitted work-in-progress, not yet ingested or published. Do not assume
  this is a clean "parked" state; it's mid-flight.
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
- **"RLS1" and "H1" as used in project-memory shorthand are NOT literal strings found in repo
  docs** — they are labels this consolidation introduced to name real, evidence-backed events
  (unlike "PS1"/"LPF1"/"P1" below, which ARE grounded in real commit/doc language, just previously
  mislabeled/conflated):
  - RLS1 = the combined 2026-08-15 release (Work "What the Room Heard", `aa0172e`/`691c365` +
    AP1 persona-biography safety, `dbe0a96`) — both shipped and documented same day.
  - H1 = the 2026-08-14 natural overnight production run + morning-stabilization validation
    (`.claude/overnight-main-run-2026-08-14.md` + `.claude/morning-stabilization-2026-08-14.md`).
    **Not the same thing as master-roadmap "Phase H"** (see `## 6` above) — do not conflate.
- **Three genuinely different things have all been called some variant of "P1"/"PS1" across this
  project's own documents — do not merge them, and prefer the full descriptive name over the bare
  code everywhere:**
  1. **P1** = 2026-08-14 source-derived human-detail-provenance gap finding
     (`.claude/human-detail-provenance-and-source-completeness-2026-08-14.md`) — shadow-only,
     `automation/orchestrator/human_detail_provenance.py`.
  2. **PS1** = 2026-08-16 detected-but-uncorrected AUTHOR-PERSONA biography fail-closed closure
     (candidate `89cd082`, deployed integration `169e8ff`) — a known flagged persona claim
     surviving a failed revision now blocks publication. See `## 3`.
  3. **LPF1** = 2026-08-16 LEGACY DRAFT AUTO-PROMOTION fail-closed closure (`667633f`) — the
     `publication_safety_version` contract; a historical/unknown-safety draft cannot auto-promote.
     See `## 3`. APE2 (2026-08-15, `e93bb1b`) remains the earlier, separate non-Opus
     preserved-biography edge-case closure that predates and is distinct from PS1.
  4. (A fourth, unrelated use: `.claude/cripminds-publication-model-v1-2026-08-14.md` also uses
     "P1" once, informally, to mean "if this is the next engineering priority" — a scheduling
     label, not a safety system. Noted only so it isn't mistaken for #1 above if found later.)
- **GENERATE vs. MATERIALIZE terminology claim: CONFIRMED** (see `## 2` for the exact source quote
  and branch) — an earlier pass marked this unconfirmed after checking only two roadmap docs; the
  actual source is a Format Lab/Publication Model branch doc that never landed on `main`.
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
- **There are TWO distinct article-quality evaluations — an earlier pass wrongly treated them as
  one and concluded the wrong one "doesn't exist."** (a) 2026-08-14: a 140-article deterministic
  sweep + a 15-article manual stratified sample (`.claude/article-quality-evidence-pass-2026-08-14.md`);
  persona-biography fabrication in THAT pass was a **designed paired experiment** (two personas
  each deliberately tested), plus one separate real historical incident (a fabricated "Rotterdam
  wayfinding review" that shipped before any guard existed). (b) 2026-08-16: a real, separate
  **post-release five-article/seven-run evaluation** on Trident against exact release `691c365`,
  real production providers, zero production mutation — see `## 4a` and
  `.claude/post-release-five-article-evaluation-2026-08-16.md`. Do not conflate the two, and note
  that even this reconciliation pass's own first attempt at (b) got two counts wrong (5/5 not
  4/4 brief-mismatch runs; 4/7 not 5/7 detected fabrication attempts) — verify counts directly
  against the preserved artifacts rather than re-copying a prior summary.
- **The real image-generation stack is OpenRouter + Recraft V4.1**, confirmed directly in
  `automation/gen_images.py`/`gen_persona_avatars.py`. `automation/README.md` still says
  "Pollinations FLUX API" — stale, not corrected as of this audit.
- **`docs/DISCOVERY.md` is explicitly self-marked historical** ("this document describes
  `run_discovery.py`, deleted 2026-08-09... treat everything past this notice as historical, not
  current architecture") — a good example of the marking convention to reuse elsewhere.

## 7a. CHRONOLOGY / EVIDENCE-PRIORITY RULE

When two documents conflict, **newer evidence does not automatically win merely by date.** Prefer,
in this order: (1) direct current runtime/code/DB evidence, (2) a frozen experiment
artifact/result, (3) an explicit owner decision, (4) current canonical documentation (this file),
(5) historical documentation, (6) inference. A later consolidation document (including this one)
cannot erase a real experiment merely because that experiment was never committed to the repo —
if important evidence exists only in an uncommitted working-tree file, a remote server, or a
session artifact, recover it into a durable project document before declaring it nonexistent. This
is exactly the mistake the PM1 pass made with the 2026-08-16 five-article evaluation and with
RL-2026-002's actual publication status — both existed as real evidence (Trident artifacts; an
uncommitted `status_correction` annotation already in the working tree) that a documentation-only
search missed. Check the working tree's own uncommitted diffs and reachable production hosts
before declaring something unconfirmed.

## 8. DOCUMENT INDEX

| Document | Status | What it's for |
|---|---|---|
| `.claude/post-release-five-article-evaluation-2026-08-16.md` | **CURRENT** | the real 2026-08-16 evaluation, reconstructed from Trident artifacts — see `## 4a` |
| CripMinds whitepaper ("Reclaiming Ways of Knowing," v0.2, 2026-08-14) | **NOT LOCATED** | searched: full repo git history (all branches/worktrees, `git log --all -S`), Trident production checkout, Google Drive — no match found anywhere reachable from this session. Do not assume it doesn't exist; assume it hasn't been found yet. If someone can supply it, add a Markdown copy here and update this row. Closest existing doctrinal analogues in this repo: `.claude/experiments/why-we-write-2026-08-10.md` (doctrine validation, not the whitepaper itself — dated 08-10 not 08-14/v0.2), `about.html`/`llms.txt` (public-facing summary of the same doctrine), `MANIFESTO.md` (stale "four AI agents" framing, does not match current persona-fiction framing, do not treat as authoritative). Core doctrine points this whitepaper is expected to carry, per the request that surfaced it (preserve if a copy is later found): disabled ways of perceiving can produce knowledge about the world itself; CripMinds should not become a machine attaching disability perspectives to ordinary journalism, or a set of AI personas imitating disabled identities; Jascha's archive is an artistic/methodological compass, while disability scholarship/testimony/source evidence is the epistemic grounding — these two are not the same kind of authority. |
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
