> **HISTORICAL — SUPERSEDED 2026-08-25.** This file was the canonical `WORK.md` through
> 2026-08-17 (`ORIGIN_MAIN_HEAD cb69c2d`). It was superseded by a new, concise `.claude/WORK.md`
> during the 2026-08-25 project-state reconciliation, which found this file had drifted into a
> diary (550 lines) despite its own maintenance rule against that. **The safety-gate mechanics
> described here (AP1, APE2, PS1, LPF1, Persona Brief↔Writer Reconciliation, Story Rejection
> V1.1), the conceptual-architecture debate (`## 2`), the persona-architecture Phase 3 backlog
> (`## 5` item 5), and CJ-2/L2 parked status (`## 6`) were NOT independently re-verified against
> current code during the 2026-08-25 reconciliation — "not found reverted in a targeted pass" is
> not the same claim as "verified current behavior."** Treat this file as historical / last-known
> technical documentation only. Do not infer current operational state from it — consult current
> code and `.claude/WORK.md` before acting on anything described here. `.claude/WORK.md` lists
> exactly what the 2026-08-25 reconciliation (and its 2026-08-25 correction pass) actually did
> independently re-verify: LC1 closure and its corpus-wide first-person-axis scope, engine-switch
> semantics, two specific `NEW_ENGINE_V1` contract findings, writer-grounding/production-migration
> disposition, the legacy prompt-rule inventory's status, the Phase-2 passive-capture gate's actual
> status, and Sofa/Form ratification evidence (G-009). Everything else in this archived file is
> last-known-state only.

# WORK — Canonical Current State (2026-08-17 snapshot — SUPERSEDED, see banner above)

**This is the authoritative entry point for CripMinds project state.** It is mutable and
describes CURRENT TRUTH only — not a diary. History lives in `.claude/LOGBOOK.md`. Full
evidence/methodology lives in the linked documents under `## DOCUMENT INDEX` — do not
duplicate their content here, and do not treat an older document's conclusion as authoritative
if this file marks it superseded. **Physical topology (worktrees, branches, preserved evidence
locations, lifecycle status) is now canonically tracked in `.claude/PROJECT-MAP.md`** (installed
2026-08-16, Project Memory Phase 3) — do not duplicate that content here either.

**Maintenance rule:** every material production release, safety-invariant change, architectural
decision, experiment freeze/unfreeze must update `LOGBOOK.md`, and this file too if current
state changed, in the same commit or an immediately adjacent docs commit. A task that changes
project state but leaves this file stale is not fully closed. Routine article/content commits do
not need a LOGBOOK entry unless they expose a material system finding.

Last reconciled: 2026-08-17 (AR3-B testimony-quota fix release; see `## 5a`), against
`ORIGIN_MAIN_HEAD` — see exact value in `## 3`'s SHA table, not restated here to avoid this header
going stale again the way the SHA claim did in the PM1 pass.

---

## 1. CORE DOCTRINE (short canonical statements — full whitepaper is evidence-only, not reproduced here)

**The whitepaper itself is now recovered and installed** — `docs/whitepaper/cripminds-whitepaper-v0.2-2026-08-14.md` ("CripMinds: Reclaiming Ways of Knowing," v0.2). The Core claim/Commissioning question/Reader experience bullets below are verbatim or near-verbatim from its Abstract and §7; checked directly against the recovered text, not misstated. Read the whitepaper itself for the artistic-lineage argument behind these statements (Jascha's 2013 thesis, terughalen/terugeisen, "artistic compass vs. epistemic material," §18's engineering-restraint rule) — none of that argument is reproduced here.

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
- **Status: Phase 3 (motive sentences, CJ-2 competitive-reframing replacement, the OWNERSHIP/
  SUPPRESSION prompt-clause fixes) confirmed NOT STARTED — but one narrow, separate slice IS now
  fixed:** the 2026-08-16 evidence's headline finding (`## 4a`) — Fable's own mechanism-aware
  persona choice being silently overridden by a subject-blind rotation check afterward, with the
  mechanism/angle shipping unchanged under the substitute persona — is closed as of `## 3` item 5
  (Persona Brief <-> Writer Reconciliation, `cb69c2d`). This is NOT the CJ-2 competitive-reframing
  replacement recommended just above, and NOT a fix to Siri's OWNERSHIP clause or the
  FORBIDDEN_DEFAULTS SUPPRESSION collision — those three remain fully unstarted. What's fixed is
  narrower: rotation/fairness can no longer silently discard Fable's own persona+mechanism decision
  after the fact; it now constrains that decision up front instead.

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
| `ORIGIN_MAIN_HEAD` | `cb69c2da1e1a586a70a0f7ba053bc464f9be20a9` | latest commit on GitHub `origin/main` |
| `TRIDENT_DEPLOYED_HEAD` | `cb69c2da1e1a586a70a0f7ba053bc464f9be20a9` (confirmed via direct SSH read, 2026-08-16) | what the production checkout on Trident has actually pulled and is running — matches `ORIGIN_MAIN_HEAD` exactly as of this reconciliation |
| `LAST_PRODUCTION-CODE_RELEASE` | `cb69c2d` | last commit that changed `automation/` behavior — Persona Brief <-> Writer Reconciliation (below); supersedes `667633f` (PS1/LPF1) as the most recent code change |
| `LAST_MEMORY_RECONCILIATION_COMMIT` | this file's own edit (immediately adjacent to `cb69c2d`, not the same commit — see header's maintenance rule) | docs-only, no production code changed |

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
4. **LPF1** (`667633f`, 2026-08-16) — the legacy-draft
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

5. **Persona Brief <-> Writer Reconciliation** (`cb69c2d`, 2026-08-16, current
   `LAST_PRODUCTION-CODE_RELEASE`) — a routing-correctness fix, not a new blocking safety gate
   (does not stamp `fact_check_status`/`publication_safety_version`), but directly upstream of why
   AP1/APE2/PS1 have had real fabrication incidents to catch. OLD: `_fable_editorial_brief` chose a
   persona freely (mechanism-aware), then `generate.py` ran that choice back through
   `_balance_agent` (rotation-fairness, mechanism-BLIND) a SECOND time and could silently substitute
   a different persona while every downstream field (angle, correction_moment, resisting_example,
   cross_cite) stayed exactly as Fable wrote it for the ORIGINAL persona — confirmed root cause of
   the 5/5 brief/byline mismatches in the 2026-08-16 evaluation (`## 4a`) and of "Reached by Boat or
   Plane"'s divergence (below), and directly implicated in 2 of that evaluation's 4 real
   unsupported-persona-biography fabrication incidents (runs 05/07 — the writer, lacking the
   substitute persona's actual canon support for the inherited mechanism, appears to have invented
   biography to bridge the gap). NEW: rotation eligibility (`discovery.py`'s new
   `_rotation_eligible_agents`) is computed BEFORE Fable's decision and passed into
   `_fable_editorial_brief` as a hard constraint; Fable must choose persona + mechanism together
   from within it, and the whole brief is rejected (same fail-closed path as any other schema
   violation) if it names an ineligible persona. The post-brief silent-override block is deleted
   outright. Invariant now holds structurally: `fable_brief["persona"] == agent_name == the
   persisted plan persona == the byline`, for every successful Fable path. `_balance_agent` itself
   is unchanged, still used only for the crude pre-brief keyword seed and the discarded-brief
   fallback. **Does NOT retroactively repair "Reached by Boat or Plane"** — that article's own
   remediation decision remains separately pending (below); this fix only prevents the SAME routing
   failure from recurring in future generation runs. Also explicitly NOT done as part of THIS
   fix: source/feed concentration, CJ-2 activation, or `persona-architecture-audit.md` findings
   #1 (Siri Sage's OWNERSHIP prompt clause) / #2 (FORBIDDEN_DEFAULTS SUPPRESSION collision) — all
   remain Phase 3, confirmed not started (see `## 5` item 5 below). Story-rejection capability
   itself has since moved past prototype (see LOGBOOK 2026-08-17): PRF1 (this fix, `cb69c2d`) was
   the release gate it was waiting on — that gate is now satisfied, the reviewed release candidate
   (`cff6dbc3140a5dea4ea6c2536ba664c633239995`) was merged onto canonical `main` as `275470c`
   (automation/ content re-verified byte-identical post-merge, all tests green) and **deployed to
   Trident** (`git pull`, fast-forward `ba64e77..9e1c81d`); the production `disability_findings.db`
   (repo root) was migrated via the real, already-tested additive `news_fetcher.init_db()` path
   (5 new columns, 1116 rows before/after, zero data loss) and a read-only smoke check confirmed
   the deployed code/schema/contract-version match the reviewed candidate. **Story-rejection is now
   live in production** as of 2026-08-17 — a future generation run may write an article, decline a
   source, find no eligible carrier, or defer, and all four are legitimate outcomes, not failures.
   **UPDATE, same day**: the first real V1 commission ("7,000 Rooms With No Door For Anyone") was
   forensically found to be a false/permissive commission (SRF3) — the deterministic grounding gate
   validated DECLINE but not COMMISSION, and a Techmeme aggregator page was fetched whole, letting
   an unrelated neighboring story contaminate the evidence. **V1.1** (`d0204aa`, fast-forwarded onto
   `main` from `b925a5d`, deployed to Trident, `underlying_article_url` column added via the same
   additive path, 1116 rows unchanged) closes both defects: a bounded, separately-invoked semantic
   verifier (`_verify_commission_mechanism_support`) now rejects commissions whose claimed mechanism
   isn't actually supported by the source evidence (fail-closed to `defer` on UNSUPPORTED/UNCERTAIN/
   any provider failure — never a silent decline or write), and aggregator sources are isolated to
   the selected item (or its underlying article) before evidence ever reaches Layer 1. Story
   Rejection is now on **V1.1**, live in production, with no code/persona/PRF1 changes beyond this
   scope.

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

**Root cause of the divergence above is now understood and closed going forward** (item 5,
Persona Brief <-> Writer Reconciliation, `cb69c2d`, above): the exact silent post-brief rotation
override that produced this article's Maya-Flux-planned/Siri-Sage-published split can no longer
happen in new generation runs. This does NOT retroactively repair this specific article — its own
remediation decision (repair in place / withdraw / leave as-is) remains separately pending, per
`## 5` item 3 below.

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
   collides almost entirely with Maya's own core evidentiary vocabulary). **One narrow slice of
   this is now fixed** (`## 3` item 5, Persona Brief <-> Writer Reconciliation, `cb69c2d`,
   2026-08-16): the silent post-brief rotation override is closed. Still open, unchanged: the
   `_THEME_TO_PERSONA` keyword map itself (still a hard lookup table, not affinity-weighted), Siri's
   OWNERSHIP prompt clause, the FORBIDDEN_DEFAULTS/Maya collision, and Maya's low-publish-count root
   cause (still unconfirmed which of routing-frequency vs. downstream quality explains it — the
   funnel-instrumentation diagnostic `persona-architecture-audit.md` finding #3 proposed has still
   not been run). Full target architecture (CJ-2-based competitive-reframing routing) is **Phase 3,
   confirmed not started.**

Also open, not part of the causal thread above but real and unresolved:
- `rewrite_with_opus`'s duplication-blind acceptance check (`automation/orchestrator/llm.py`,
  weak `count("---") >= 2` check) is **still live and unpatched** — only the one known symptom
  (`the-floor-plan-of-disappearance`) was manually repaired (`64d1658`), the class of bug was not.
  Any future non-Opus-origin draft could reproduce it.

## 5a. NEAR-TERM PRIORITY (2026-08-17): SOFA ARTICLES, NOT DEEPER ARCHITECTURE

**Priority changed, not superseding `## 5`'s causal thread** — that thread remains real and
un-cancelled, just deprioritized against a faster-turnaround target. Near-term artistic target
is now **"Sofa Articles"**: pieces Jascha would genuinely sit down and read for pleasure (closer
to a strong Bregman essay than to "a disability article") — concrete opening, a strange detail
worth following, real documented material, investigation rather than thesis delivery, disability-
derived perception doing causal work without becoming the subject, no manufactured human texture.
Operational rule: prioritize work with a plausible path to a noticeably better finished article
within 1-3 steps; an artistic experiment should normally produce ~3-6 finished pieces before
ship/reject/redirect, not run into a long chain. This does not relax evidence/provenance rigor —
see the AR-series below, all of which is real generation + real provenance audits, not shortcuts.

**Evidence trail (do not re-litigate, read before touching writer-prompt testimony rules again):**
`.claude/experiments/artistic-reset-ar1-2026-08-17.md` (AR1 — disability as epistemic engine, not
subject) → `artistic-reset-ar2-silent-lens-2026-08-17.md` (AR2 — Silent-Lens doctrine tested, not
the primary lever) → `artistic-reset-ar2-1-provenance-and-discovery-motion-2026-08-17.md` (AR2.1 —
provenance audit found AR2's testimony partly fabricated, isolated NAMED VOICES/SOMEONE ELSE MUST
SPEAK as the likely driver) → `artistic-reset-ar3-unforced-human-presence-2026-08-17.md` (AR3,
decision AR3A — confirmed via a real 3-condition/12-article/12-review experiment: removing the
testimony quota cuts fabrication with zero measured artistic cost) →
`artistic-reset-concept-perceptual-engines-disturbances-case-memory-2026-08-17.md` (preserved
conceptual branch: engine vs. persona, disturbance-level discovery, mechanism-indexed case
memory — real, not cancelled, explicitly deprioritized against Scout).

**SHIPPED (this entry):** the AR3-B testimony-quota fix is live in production —
`automation/orchestrator/generate.py`'s NAMED VOICES / SOMEONE ELSE MUST SPEAK / NO INVENTED
QUOTES three-part mandatory block replaced by one compact, evidence-bound "HUMAN TESTIMONY /
NAMED VOICES" rule (zero testimony/quotation/named-people explicitly valid; inventing any of it
for narrative texture forbidden; real-name fabrication severity warning carried forward). HUMAN
THREAD, GROUNDING, TEMPORAL ANCHORS, AUTHOR RULE, "strong thesis from sentence one," Story
Rejection, PRF1, persona architecture, `disability_angle`, Fable planning, and routing are all
explicitly untouched by this release — full regression suite + 2 new `writer_prompt_test.py`
tests pass locally and on the live Trident deploy. See LOGBOOK for the release record.

**Immediate sequence, in order (do not skip ahead without generating/reading real work first):**
1. Ship the AR3-B testimony fix — **DONE**, this entry.
2. Build CripMinds Scout (broad source material → disturbance-fragment detection → a very small
   number of strange, grounded leads → real finished Sofa Articles) — cheap and bounded first
   version only; not new routing architecture, not a persona redesign, not a case-library
   database, not a 12-micro-lens engine, not an autonomous research platform.
3. Generate/read a very small set (~3) of real finished articles from Scout's leads.
4. Add small, verified case-memory retrieval only if Scout's own output makes a real mechanism-
   reuse opportunity concrete — not speculatively.
5. Return to deeper architecture (Engine Before Persona, AR3.1 discovery-motion/thesis
   contradiction, AR4 `disability_angle` x Fable-planning 2x2, disturbance-mining comparison, case-
   library shadow prototype) only once finished work makes the question consequential. **None of
   these are cancelled** — they remain preserved, real, queued research questions; they are simply
   not the next thing to build.

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
| `docs/whitepaper/cripminds-whitepaper-v0.2-2026-08-14.md` | **CURRENT — CONCEPTUAL / ARTISTIC AUTHORITY** | "CripMinds: Reclaiming Ways of Knowing," v0.2, 14 August 2026 — recovered verbatim from a local pre-repo artifact (originally `~/Downloads/cripminds-whitepaper-v0.2.md`; the full original export batch, including `.docx`/`.pdf` siblings, is durably preserved outside the repo at `~/code/cripminds-preservation/whitepaper/v0.2/` — archival only, not required for ordinary project use, see LOGBOOK's preservation entry). This is the founder's own artistic/editorial doctrine document — the whitepaper referenced but not reproduced by `## 1`'s "full whitepaper is evidence-only" line. **Read it for WHY the project is shaped this way (artistic lineage from Jascha's 2013 graduation thesis, the terughalen/terugeisen distinction, "artistic compass vs. epistemic material," the Bregman discovery-reading-experience reference, the Section 18 engineering-restraint rule). It is NOT: empirical evidence of any disabled person's lived experience, persona biography canon (see `automation/persona_canon/*.md` for that authority), or production configuration/prompt text (see `automation/orchestrator/llm.py` for what's actually live).** A prior consolidation pass (PM1.1) searched the full repo git history, Trident, and Google Drive and could not find it, and correctly recorded it as "NOT LOCATED" rather than reconstructing it from memory — see LOGBOOK's recovery-correction entry for exactly where it turned up. |
| `.claude/WORK.md` | **CURRENT** | this file |
| `.claude/LOGBOOK.md` | **CURRENT** | chronological history, compact entries |
| `.claude/CONTEXT.md` | **CURRENT** | ops facts: cron schedule, DB tables, secrets paths, model routing — read this for "how do I operate the pipeline," not "what's the state of the research" |
| `.claude/current-work.md` | **SUPERSEDED (by this file)** | 266KB historical log, kept as an archive/evidence trail, no longer the entry point — see banner at its top |
| `.claude/master-roadmap-2026-08-13.md` | **HISTORICAL, frozen 2026-08-13** | CJ-2/B2 phase table (A-J), reconciles two ancestor docs; repo has moved past its "ahead N commits" claims — trust its phase-table structure, not its "current HEAD" claims |
| `.claude/original-blueprint-A-M-reconciliation-2026-08-13.md` | **HISTORICAL, frozen 2026-08-13, re-checked 2026-08-14 (commit `204c3bc`)** | per-letter A-M status; G/H/I re-confirmed done that day |
| `.claude/experiments/final-evaluation-freeze-protocol-2026-08-13.md` | **CURRENT (governance)** | the actual CJ-2/B2 freeze requirements — read this, not a paraphrase, before touching CJ-2 |
| `.claude/experiments/artistic-reset-concept-perceptual-engines-disturbances-case-memory-2026-08-17.md` | **CURRENT (preserved hypothesis, not decided)** | engine-vs-persona, disturbance-level discovery, mechanism-indexed case memory — deprioritized against Sofa Articles/Scout, not cancelled, see `## 5a` |
| `.claude/experiments/artistic-reset-ar3-unforced-human-presence-2026-08-17.md` | **CURRENT (shipped, AR3A)** | 3-condition/12-article/12-review real experiment; testimony-quota removal cuts fabrication at zero measured artistic cost — production fix shipped this release, see `## 5a` |
| `.claude/experiments/artistic-reset-ar2-1-provenance-and-discovery-motion-2026-08-17.md` | **CURRENT (forensic audit, AR21B)** | provenance ledger on AR2's 8 articles; found AR2's testimony partly fabricated, isolated NAMED VOICES/SOMEONE ELSE MUST SPEAK as the likely driver — motivated AR3 |
| `.claude/experiments/artistic-reset-ar2-silent-lens-2026-08-17.md` | **CURRENT (real experiment, AR2C)** | 4-source/2-condition Silent-Lens doctrine test; writer doctrine is not the primary lever of subject-drift |
| `.claude/experiments/artistic-reset-ar1-2026-08-17.md` | **CURRENT (synthesis, AR1)** | disability-as-epistemic-engine vs. article-subject; whitepaper cross-read against 4 real production articles; designed (didn't run) the Silent-Lens/AR2 experiment |
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
| `.claude/cripminds-publication-model-v1-2026-08-14.md` | **HISTORICAL — CONCEPTUAL/ARCHITECTURAL EVIDENCE (recovered onto `main` 2026-08-16, Phase 3B; never implemented, branch never merged)** | Publication Model V1 synthesis from branch `publication-model-v1-2026-08-14`; source of the confirmed GENERATE vs. MATERIALIZE terminology cited in `## 2` — historical design/terminology evidence only, not current production configuration or proof the old branch's architecture is active |

---

*Update this file when current state changes. Do not let it grow into a diary — if a section is
about to become a narrative, it belongs in a linked document instead, with a pointer here.*
