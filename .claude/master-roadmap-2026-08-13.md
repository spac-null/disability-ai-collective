# CURRENT RECONCILED ROADMAP — 2026-08-13

**Status: reconciliation/governance document. Zero model calls. No
RL-2026-002 partial answers inspected. No RL-2026-003 ingestion. No
B2/Stage-C code touched. No held-out content read (none exists). No
product features implemented.**

This document reconciles the B2/CJ2 research-track roadmap
(`.claude/experiments/final-evaluation-freeze-protocol-2026-08-13.md`)
against the project's actual production reality, because — as this pass
found — **they are two separate systems that have never been wired
together**, and no existing document said so plainly. It supersedes
nothing by rewriting; it adds the missing reconciliation layer. Original
documents remain in place, unedited, as historical/parallel context (see
`## 1`).

---

## 1. CANONICAL BLUEPRINT/ROADMAP — WHAT ACTUALLY EXISTS

There is no single dedicated `BLUEPRINT.md`/`ARCHITECTURE.md`. Do not
assume one that predates the research track is still authoritative — the
closest candidates are:

- **`.claude/audience-engagement-tasklist.md`** (54KB, last updated
  2026-08-10) — the real project-wide backlog for the **live production
  pipeline's** evolution. Self-described, in its own opening paragraph:
  *"This file is a discussion draft, not an approved plan — each item
  needs your input before anything gets built."* Treat as a live,
  maintained document, but not an approved roadmap.
- **`README.md`** (repo root) — high-level pitch only (4 personas,
  Jekyll/GitHub Pages, WCAG). No pipeline detail. Not stale, just thin.
- **`docs/DISCOVERY.md`** — **confirmed stale**, self-flagged at the top
  of the file: *"This document describes `run_discovery.py`, deleted
  2026-08-09... Treat everything past this notice as historical, not
  current architecture."* The live discovery mechanism is
  `automation/news_fetcher.py` (RSS + keyword-bucket scoring), cited
  correctly inside that same warning banner.
- **`.claude/experiments/cj2-competitive-reframing-design-2026-08-11.md`**
  and **`.claude/experiments/final-evaluation-freeze-protocol-2026-08-13.md`**
  — canonical, but **only for the CJ-1/CJ-2/B2/Stage-C research track**,
  not the whole system.

**The single most important finding of this audit:** the live daily
production pipeline (`automation/production_orchestrator.py` +
`automation/orchestrator/*.py` — `discovery.py`, `personas.py`,
`generate.py`, `gate.py`, `fact_check.py`, `review.py`, `publish.py`,
`social.py`, `debate.py`, `images.py`, `content_checks.py`, `llm.py`,
`config.py`) and the CJ-1/CJ-2/B2/Stage-C research track
(`automation/cj1_*.py`, `automation/cj2_*.py`) are **two structurally
separate systems that have never been integrated.** Verified directly,
not assumed: a repo-wide import check found zero references to
`cj1_*`/`cj2_*` from anywhere in `orchestrator/*.py` or
`production_orchestrator.py`, and the only reference in the opposite
direction is `orchestrator.config`'s shared `CLIPROXY_URL`/`CLIPROXY_KEY`
constants, imported by three CJ probe files (`cj1_v3_probe.py`,
`cj2_reference_probe.py`, and one other) — a shared low-level transport
config, not pipeline wiring. No candidate, prompt, or decision from the
CJ track has ever reached the live pipeline, and vice versa.

This corrects an assumption embedded in how this task was framed:
persona execution, editorial review, and article-level validation are
**not unbuilt future blueprint layers** — they are built, live, and
publishing real articles to cripminds.com every day, via a completely
different, older, simpler mechanism than the one B2/CJ2 has been
researching.

---

## 2. RECONSTRUCTED ORIGINAL END-TO-END VISION

Reconstructed from the docs above (live pipeline) — there is no single
document describing an *intended* end-to-end system combining the live
pipeline with CJ-2's competitive-reframing model; what follows is the
live pipeline's actual current stage list, since that is the only
executable "end-to-end vision" that exists on disk today:

| Stage | What it does today | Source | Matches original intent? |
|---|---|---|---|
| Topic/source acquisition | RSS fetch, news-seed DB, diversity nudges (beats/themes/openings) | `orchestrator/discovery.py` | Yes, but the *documented* version (`docs/DISCOVERY.md`) is stale — the live mechanism replaced it without a doc update |
| Persona selection | One of 4 fixed personas (Siri Sage, Pixel Nova, Maya Flux, Zen Circuit), single-persona pick per article | `orchestrator/personas.py`, `README.md` | Yes — this is the original, still-current model |
| Pre-write editorial brief ("Fable brief") | `_fable_editorial_brief` produces a structural plan (opening shape, correction moment, resisting example, angle, seed sentence) before drafting | `orchestrator/generate.py` | Yes, live and hash-checked against the evidence packet |
| Draft generation | Single ~150-line prompt, one writer call per persona/article | `orchestrator/generate.py` | Yes — single-candidate, not competitive |
| Pre-commit gate | Deterministic regex checks + LLM rule check + one surgical-fix pass | `orchestrator/gate.py` | Yes, live, blocking |
| Fact-check | Claim extraction + live Perplexity Sonar verification + one-shot fabrication repair + cross-persona citation check | `orchestrator/fact_check.py` | Yes, live — this is the production system's OWN factuality layer, structurally unrelated to D0/C0/R1/R2 |
| Publish | Write, commit, push | `orchestrator/publish.py` | Yes |
| Post-publish review | Citation check, engagement read (advisory only), readability, RULES_SYSTEM check, Telegram alert | `orchestrator/review.py` | Yes, non-blocking |
| Social | Bluesky posting | `orchestrator/social.py` | Yes |
| **CJ-1 (source-friction gate)** | Research-only, frozen as `cj1-v3.2-validity-before-recall`, a candidate/CJ-2 input contract — never called by the live pipeline | `automation/cj1_v3_*.py` | **Never integrated** |
| **CJ-2 (multi-persona competitive reframing, Stage A/B/B2/C)** | Research-only. 4 anonymous "engine capsule" candidates per source compete; Stage C comparator picks a structured winner (an angle/pitch object, not prose) | `automation/cj2_*.py` | **Never integrated; this is a different generation model than the live single-persona pick, not an upgrade bolted on top of it** |
| Multi-candidate / "judge-panel" generation (the *production-blueprint's own* deferred idea, distinct from CJ-2) | Decided in principle (2-draft "option b"), never built; explicitly left with an unresolved sequencing conflict against a separate "anchor-architecture Stage E" | `.claude/audience-engagement-tasklist.md` (lines ~452-556) | **Deferred, and never reconciled with CJ-2 — see `## 11`** |

---

## 3. CURRENT REALITY VS. BLUEPRINT — COMPONENT STATUS

| Component | Status |
|---|---|
| Grounding (live pipeline's evidence packet) | **DONE**, production-integrated |
| CJ-1 (friction gate) | **IN EXPERIMENTAL VALIDATION** — frozen candidate contract, not production-integrated |
| CJ-2 (competitive reframing, Stage A/B) | **IN EXPERIMENTAL VALIDATION** — architecture designed and probed, not production-integrated |
| D0/C0 (proposition coverage) | **BUILT, IN EXPERIMENTAL VALIDATION** — apparatus stable per the freeze protocol, semantics still being calibrated |
| R1/R2 (factuality) | **BUILT, IN EXPERIMENTAL VALIDATION** — same status as D0/C0 |
| Validator-guided repair (repair-v1) | **BUILT, IN EXPERIMENTAL VALIDATION** |
| B2 → Stage C admission gate | **BUILT, IN EXPERIMENTAL VALIDATION** — deterministic, fail-closed, never yet exercised on a natural safe admission (0/14 to date) |
| Reader Lab | **BUILT AND LIVE (as infrastructure)**, but its *task* (B2 factuality calibration) is **IN EXPERIMENTAL VALIDATION** — see `## 8` for the DONE/ongoing split |
| Autonomous calibration (`analyze-human-round-v1/v2`) | **DONE** (apparatus), feeding an **IN EXPERIMENTAL VALIDATION** research question |
| Policy-driven reviewer/round automation | **DONE**, deployed and live |
| Final freeze protocol | **DONE** (as a document) — governs a future state, not yet reached |
| Live production pipeline (discovery→personas→generate→gate→fact_check→publish→review→social) | **DONE, DONE BUT ARCHITECTURE CHANGED in spots** (discovery mechanism swapped, doc never updated) — **production-integrated and running daily, independent of every item above** |
| "Mind Engine" | **UNKNOWN / not a real subsystem** — appears once in the repo as informal shorthand for "the live generative apparatus," not an architectural component with its own design doc |
| Fable editorial review (CJ-track "review-seat" experiment) | **NOT YET BUILT / PAUSED** (Phase 1.5B) — separate from, and not to be confused with, the live pipeline's own Fable *pre-write brief*, which is DONE |
| Bridge: CJ-2 Stage-C winner → publishable article | **NOT YET BUILT** — no code path exists; this is the actual next layer, see `## 4` |
| Article-level validation for CJ-2-sourced output | **NOT YET BUILT** — `gate.py`/`review.py` validate the live pipeline's own drafts only; nothing has ever validated a CJ-2-originated draft, because none has ever been produced |
| Multi-candidate/"judge-panel" generation (production blueprint's own deferred item) | **NOT YET BUILT**, and its relationship to CJ-2 is unresolved (`## 11`) |

---

## 4. WHAT COMES AFTER B2 CALIBRATION — THE ACTUAL NEXT LAYER

**Not "production." Not "article drafting" as a from-scratch layer — that
already exists and runs daily, just for a different, non-competitive
generation model.**

The concrete next layer, once B2/CJ-2 reaches production-candidate status
per the freeze protocol, is a **decision and a bridge**, in that order:

1. **An explicit architectural decision**, currently undocumented
   anywhere, on how CJ-2's validated candidate-selection mechanism relates
   to the live pipeline's single-persona generation model. Three shapes
   this could take (not designed here, per instruction — flagged only):
   replace the live model's persona-pick step with CJ-2's competitive
   selection; run CJ-2 as a parallel/optional generation mode; or use
   CJ-2's Stage-C winner only as an upgraded input to the *existing*
   `_fable_editorial_brief` step, leaving the rest of `generate.py`
   unchanged.
2. **The bridge itself**: code that takes a Stage-C winner (currently a
   structured angle/pitch object — `resisting_detail`, `engine_move`,
   `seed_engagement`, `interpretive_inference`, `conceptual_shift`,
   `claimed_contribution` — not prose) and turns it into an actual
   persona-voiced draft. This does not exist in any form today.
3. **Article-level validation** for whatever the bridge produces (`## 6`,
   `## 7`) — `gate.py`/`review.py` were built and tuned for the live
   pipeline's own drafting mechanism; nothing confirms they're adequate,
   or even applicable unmodified, to a CJ-2-originated draft.

This is a genuine, currently-unscheduled research-and-engineering phase —
not a checkbox on the way to "production," and not automatically implied
by B2/CJ-2 passing held-out evaluation.

---

## 5. TWO ROADMAPS, KEPT SEPARATE

### A. REMAINING RESEARCH ROADMAP (today → production-candidate freeze)
This is exactly `final-evaluation-freeze-protocol-2026-08-13.md`'s own
roadmap (`## 15` there), unchanged by this pass:
RL-2026-002 → RL-2026-003 (if still justified) → one consolidated B2
revision → two stable development regression probes → ≥2 qualitatively
different natural Stage-C admissions → semantic freeze → fresh held-out
collection → held-out evaluation → production-candidate review.
**This roadmap validates the CJ-1/CJ-2/B2/Stage-C factuality/selection
mechanism in isolation — it does not validate an article, because no
article-production path from Stage C exists yet.**

### B. POST-VALIDATION PRODUCT ROADMAP (production candidate → working
publishing system)
Only begins once (A) reaches production-candidate status:
1. Architectural integration decision (`## 4`.1).
2. Build the Stage-C-winner → draft bridge (`## 4`.2).
3. Extend/validate `gate.py`/`review.py` (or build equivalents) against
   CJ-2-sourced drafts specifically (`## 6`, `## 7`) — a new experimental
   layer, not automatically covered by (A)'s held-out result.
4. Reconcile with the live pipeline's own deferred multi-candidate/
   judge-panel idea (`## 11`) so two competing "pick the best candidate"
   mechanisms don't ship independently.
5. Human production-candidate review and promotion decision (unchanged
   from the freeze protocol's own `## 10` — still human-only).
6. Live rollout, monitoring, and whatever automation boundary `## 10`
   below implies.

**These are not the same milestone.** "System is experimentally
validated" (A) describes the factuality/selection engine in a probe
harness. "Site can automatically produce publication-ready articles"
using that engine (B) is a separate, currently-unscheduled body of work —
the live site already does the latter today, just without CJ-2.

---

## 6. IS STAGE C REALLY THE LAST RESEARCH STAGE? — NO

Stage C selects a winning *structured candidate*, not a finished article.
Layers that exist conceptually downstream of Stage C and remain
completely unvalidated, because they have no implementation to validate:
- **Winner-brief-to-prose fidelity** — whether a generated draft actually
  preserves the winning candidate's specific insight (`claimed_contribution`,
  `resisting_detail`) rather than drifting during drafting.
- **Article generation quality** from a CJ-2 origin specifically (the
  live pipeline's drafting quality has years of implicit production
  experience behind it for its own persona/brief model; CJ-2 has none).
- **Persona fidelity** under a CJ-2-selected angle, as opposed to the
  live pipeline's own persona-pick logic.
- **"Mind Engine" behavior** — not applicable as a distinct validation
  target, since it isn't a real subsystem (`## 3`).
- **Accessibility/readability** of a CJ-2-sourced draft — `gate.py`'s
  Flesch-Kincaid/buried-clause checks were tuned against the live
  pipeline's own writing patterns, not verified against anything CJ-2
  would produce.
- **Editorial selection** in the sense of a human/Fable judge picking
  among finished drafts — this is the paused Phase 1.5B experiment, a
  different and still-open question from Stage C's own comparator.
- **Source grounding in final prose** — Stage A/B/B2/R1/R2 verify
  grounding in the *candidate*, structured-object stage. Nothing verifies
  that grounding survives translation into persona prose, because that
  translation step doesn't exist yet.

**Do not assume held-out B2/CJ-2 evaluation validates the entire article
system — it explicitly does not, because the system it would need to
validate (CJ-2-to-article) hasn't been built.**

---

## 7. ARTICLE-LEVEL VALIDATION

**Does the blueprint define or require it? Partially — and only for the
live pipeline, which is not the system this research track is validating.**

The live pipeline already enforces most of what "article-level
validation" would mean, for its OWN drafts:
- Source-groundedness → `fact_check.py` (live web verification + one-shot
  repair).
- Accessible public language → `gate.py` (Flesch-Kincaid, buried-clause/
  argument-word/sentence-length checks).
- No internal-machinery leakage / editorial publishability → the
  deterministic regex + LLM rule check in `gate.py`, plus the RULES_SYSTEM
  check in `review.py`.
- "Does not turn disability into the topic by default" and "embodies the
  disability lens" → not confirmed as an explicit automated check by this
  pass (worth a follow-up read of `gate.py`'s full rule set specifically
  for this — flagged, not verified either way here).

**None of this exists for CJ-2-sourced output**, because no such output
exists. Searched explicitly for the terms "article-level validation,"
"final article," "published article quality" across the repo — zero
hits. **This is confirmed as a genuine, currently undesigned late-stage
validation layer for the CJ-2 track specifically** — not merely an
unread document. It belongs in Phase E of `## 13`, and per instruction is
flagged here, not designed.

---

## 8. READER LAB'S LONG-TERM ROLE — BOTH, WITH A GAP

Reader Lab v0's own design doc (`.claude/reader-lab-v0-design-2026-08-12.md`)
answers this directly:
- `## 1 Purpose` frames v0 as existing specifically because B2/CJ-2
  research "has repeatedly needed" independent human judgment — a
  response to the current calibration gap, not a permanent commitment on
  its face.
- `## 2 Non-goals` explicitly excludes "category-jump quality, persona
  selection, engine quality, disability theory, CJ architecture,
  originality, or overall article quality" from v0's scope — v0 the
  *task* is narrow and temporary by design.
- `## 19 Future expansion (not designed here, only flagged)` explicitly
  names likely reuse: "a second Reader Lab task type once v0's mechanism
  is validated (e.g. category-jump quality, once CJ-2 is further along)"
  and "cross-model or cross-reviewer statistical calibration tooling."
  This is direct evidence the underlying **mechanism** (reviewer
  onboarding, round publication, response collection, automated
  completion-detection/export/analysis) is intended to persist and be
  reused — not single-purpose scaffolding.

**Answer: BOTH.** The current *task* (B2 factuality calibration via
RL-2026-001/002/003) is temporary and should be retired once the freeze
protocol's calibration stop rule (`## 12` there) is satisfied. The
*infrastructure* (Cloudflare Worker, D1 schema, admin UI, policy engine,
calibration orchestrator) is explicitly designed for reuse and should
persist — a natural fit for exactly the article-level/persona-fidelity
validation layer `## 6`/`## 7` identify as missing.

**Gap found, not fixed:** the freeze protocol document governs the B2
held-out/freeze gate but says nothing about Reader Lab's role after that
gate closes. This reconciliation document is the first place that gap is
named; it is not resolved here.

---

## 9. FINE-TUNING — NO BLUEPRINT ASSUMPTION TO SUPERSEDE

Checked exhaustively: **no original blueprint document ever mentions
fine-tuning as a milestone.** Zero hits in `README.md`,
`.claude/audience-engagement-tasklist.md`, or `docs/DISCOVERY.md`. Every
mention found anywhere in the repo (`reader-lab-v0-design-2026-08-12.md`,
`current-work.md`, the two research-track experiment docs,
`reader-lab-worker/README.md`, `calibration/workflows/analyze-human-round-v1.md`)
is recent (post-2026-08-12, Reader-Lab-era) and every single one already
frames fine-tuning as optional, non-required optimization — the freeze
protocol's `## 11` framing is consistent with, not a walk-back of,
everything that came before it.

**Correct statement: there was no prior commitment to supersede.** The
idea that fine-tuning might ever have been a required milestone appears
nowhere in this project's actual history — it is worth saying this
plainly so it doesn't get reintroduced later as a phantom "original plan."

---

## 10. AUTOMATION END STATE

**Important correction to how this section was framed in the request:**
much of the described automatic/human split **already exists today**, on
the live pipeline side, independent of B2/CJ-2. Restating it accurately:

**Already automatic, live, running daily (no B2/CJ-2 involvement):**
- Topic/source discovery (`discovery.py`, cron).
- Persona selection, editorial brief, drafting (`personas.py`,
  `generate.py`).
- Pre-commit gating and fact-checking (`gate.py`, `fact_check.py`).
- Publication and social posting (`publish.py`, `social.py`).
- Post-publish review sidecar + Telegram alert (`review.py`).

**Already automatic, live, running on the research-track side:**
- Calibration candidate ingestion, round preparation, completion
  detection, research export, autonomous analysis
  (`analyze-human-round-v1/v2`), policy-driven reviewer eligibility/
  additional-review/publication decisions — all deployed (per
  `current-work.md`'s `## 26`/`## 27` entries).

**Still human, by explicit design, and should stay that way per Jascha's
minimize-human-intervention goal being about eliminating *unnecessary*
plumbing, not eliminating judgment:**
- Policy value changes (`calibration_policies` table) — deliberate,
  infrequent, high-leverage decisions.
- Reviewer onboarding (adding a new named reviewer).
- Final production promotion (the freeze protocol's `## 10`, unchanged —
  always human).
- Exceptional cases (the `NEEDS_HUMAN_ACTION`/`NEEDS_POLICY_CONFIGURATION`
  states already built to surface exactly these and nothing else).

**Not yet automatic because not yet built, not because a human was left
in the loop on purpose:** the CJ-2-to-article bridge (`## 4`), and
whatever validation layer eventually governs it. Closing this gap with
automation, once it's designed, is consistent with minimizing human
intervention — it is future scope, not a rejected option.

---

## 11. ROADMAP DRIFT

| Change | Classification | Why |
|---|---|---|
| Reader Lab (independent human calibration infra) | **GOOD EVOLUTION** | Filled a real, repeatedly-hit gap (B2 needed human judgment it had no mechanism to get); built with real discipline (leakage rules, fail-closed policy defaults) |
| D0/C0 (proposition-coverage architecture) | **GOOD EVOLUTION** | A structural fix to a real coverage gap found in earlier B2 iterations, not scope creep — narrowly targeted |
| B2 repair layer (repair-v1) | **GOOD EVOLUTION** | Narrow, validator-guided, fail-closed by design; doesn't expand what B2 is allowed to accept |
| Policy-driven calibration automation | **GOOD EVOLUTION**, with one open thread | Replaced three hard-coded automation boundaries with a versioned, inspectable policy table — reduces future manual plumbing, exactly the stated goal; the open thread is that this document (`## 8`) is the first place Reader Lab's *post-B2* policy scope is even raised |
| Fail-closed admission gating | **GOOD EVOLUTION** | Directly enforces the project's own safety default; zero natural admissions to date is a sign it's working as designed, not that it's broken |
| **CJ-1/CJ-2 emerging as a full research track, seemingly independent of the production blueprint's own deferred "judge-panel/multi-draft" item** | **NEEDS BLUEPRINT UPDATE** | The production tasklist's own status taxonomy lists CJ-2 and "the judge-panel/multi-draft experiment" as two separate deferred items, and CJ-2's actual design (4 competing candidates, comparator-selected winner) closely resembles the tasklist's own described "full judge-panel" option — but no document anywhere states whether CJ-2 IS that item's eventual answer, a superset of it, or a genuinely separate thing. This is the drift with the most real downstream cost (`## 4`, `## 5`B) if left unresolved |
| Reader Lab infrastructure being framed only as "B2 calibration tooling" in this project's day-to-day narrative, while its own design doc already flags broader reuse | **NEEDS BLUEPRINT UPDATE** | Not wrong, just incomplete — `## 8`'s gap |
| Fine-tuning appearing in recent research-track docs at all, given no blueprint ever required it | **STILL UNRESOLVED, low stakes** | Not scope creep (it's explicitly optional everywhere it appears), just worth naming so it isn't mistaken for an old commitment later |
| The live production pipeline continuing to evolve (Fable pre-write brief, fact_check.py's Sonar-based verification) with zero cross-reference to the CJ research track's own, much more rigorous factuality architecture | **POSSIBLE SCOPE CREEP, in the sense of two systems solving the same problem independently** | Not creep in the "did too much" sense — both are individually well-scoped — but two factuality mechanisms (D0/C0/R1/R2 vs. `fact_check.py`'s live-verification approach) now exist with no stated relationship, which risks real duplicated effort once integration is attempted |

---

## 12. THE REAL "FINISH LINE" — THREE DIFFERENT ANSWERS

**1. When is B2/CJ-2 research finished?**
Exactly when `final-evaluation-freeze-protocol-2026-08-13.md`'s own gate
says: production-candidate status reached (`## 10` there) — human
calibration sufficient, one consolidated revision tested through two
stable probes, Stage C exercised on ≥2 qualitatively different natural
admissions, semantic freeze held, held-out evaluation passed without
triggering a burn. This is an isolated-mechanism milestone.

**2. When is the full article-generation system experimentally
validated?**
**Not yet defined by any existing document, and not implied by
milestone 1.** It requires, at minimum, everything in `## 4` and `## 5`B
to exist first (the integration decision, the bridge, article-level
validation for CJ-2-sourced output) — none of which is designed or
scheduled today. This milestone doesn't have a protocol yet; it needs
one, later, once milestone 1 is closer.

**3. When is CripMinds ready for routine production use?**
**Already true today, for the live single-persona pipeline** —
`production_orchestrator.py` runs daily, publishes real articles, and has
its own gate/fact-check/review discipline, independent of any of this
research. If "CripMinds" is read as "the CJ-2-validated, competitively-
selected version," this milestone is downstream of milestones 1 and 2
both, and has no target date because milestone 2 has no protocol yet.

**These are three genuinely different lines, not phrasings of one
milestone** — the request to keep them explicit was correct, and
conflating them (specifically treating milestone 1 as if it implied 3) is
the single most likely source of a false "we're basically done" read
later.

---

## 13. RECONCILED MASTER ROADMAP

| Phase | Purpose | Prerequisites | Exit criterion | Human intervention | Semantic tuning allowed? |
|---|---|---|---|---|---|
| **A — Current calibration** | Resolve Shape B (RL-2026-002), decide Shape E/C | None (in progress) | RL-2026-002 analyzed; Shape-E justification re-confirmed; Shape-C strictness decision stands or is revisited | Reviewer participation only | No |
| **B — Consolidated B2 revision** | One targeted, preregistered semantic fix addressing evidenced families | `## 4` checklist (freeze protocol) fully satisfied | Revision drafted, preregistered, hashed | Draft/approve the revision | **Yes — the only allowed window** |
| **C — Development regression (2 probes)** | Prove the revision is stable, no new failure class, anti-overcorrection holds | Phase B complete | Two hash-identical-input probes both pass `## 7` (freeze protocol) criteria | None beyond running the probes | No |
| **D — Stage-C natural-admission exercise** | Prove Stage C's gates/comparator actually execute on real output | Phase C complete (may co-occur with it) | ≥2 qualitatively different natural `EFFECTIVE_VERDICT_SAFE` admissions, mechanically valid Stage-C output | None | No |
| **E — Semantic freeze + held-out evaluation** | Lock the mechanism, test once, honestly | Phase D complete | Held-out run completes without triggering a burn (freeze protocol `## 9`) | Fresh corpus collection, run execution | **No — absolutely none** |
| **F — Production-candidate review (research-track scope)** | Human decision: is the isolated B2/CJ-2 mechanism sound? | Phase E complete | Explicit human review per freeze protocol `## 10` | **Full — human-only** | No |
| **G — Integration decision + bridge** | Decide how CJ-2 relates to the live pipeline; build the Stage-C-winner→draft path | Phase F complete | A working, documented path from a Stage-C winner to a persona-voiced draft exists | Architectural decision (human); implementation | N/A — new system, not yet subject to the freeze discipline |
| **H — Article-level / full-pipeline validation** | Prove CJ-2-sourced articles preserve the winning insight, stay grounded, embody the disability lens without defaulting to it as topic, stay accessible, don't leak machinery, are publishable | Phase G complete | A new, not-yet-designed validation protocol passes (this is milestone 2 of `## 12`) | Design + review | To be defined by that future protocol |
| **I — Productionization / automation** | Wire the validated bridge into daily operation; reconcile with the deferred judge-panel item (`## 11`) | Phase H complete | Live, monitored, running with the same automatic/human boundary already proven on the existing pipeline (`## 10`) | Ongoing exceptional-case handling only | No |
| **J — Optional optimization / fine-tuning** | Cost/latency/consistency improvements, never architecture replacement | Phase F or I (either track may reach this independently) | N/A — ongoing, optional | Decision to pursue at all | No — optimization only, never a substitute for architecture |

Phases A–F are the research roadmap (`## 5`A). Phases G–J are the product
roadmap (`## 5`B) and are currently unscheduled — no dates, no
preregistration, because the decision in Phase G hasn't been made yet.

---

## NEXT ACTION

**What can proceed now, while RL-2026-002 is still active (not
inspected):**
- Nothing in Phases G/H/I requires waiting on RL-2026-002 at all — the
  architectural integration *decision* in Phase G (not its implementation)
  could be discussed and recorded independently of B2's own calibration
  status, since it's a question about system design, not about B2's
  factuality semantics. Flagged as available, not started, since it
  wasn't requested this pass.
- The Reader-Lab-post-freeze gap (`## 8`) and the CJ-2-vs-judge-panel
  reconciliation gap (`## 11`) can both be *named and discussed* now
  without touching B2/Stage-C or Reader Lab data — they're documentation
  gaps, not blocked on any pending result.

**What must wait for human calibration / the freeze protocol:**
- Everything in Phases A–F, unchanged from the freeze protocol's own
  gating (RL-2026-002 completion and analysis, any consolidated B2
  revision, both regression probes, Stage-C's natural-admission
  exercise, the freeze itself, held-out collection and evaluation).
- Phase G's *implementation* (as opposed to the decision) should
  reasonably wait for Phase F, since building a bridge to a mechanism
  that might still change is premature — but this is a sequencing
  recommendation, not a hard technical dependency, and is open to
  revision if there's a reason to prototype earlier.

No execution taken this pass beyond writing this document and its
current-work.md pointer.

---

## PHASE G ADDENDUM (2026-08-13, same day, continuation pass) — CJ-2 ↔
## LIVE PRODUCTION INTEGRATION DECISION

**Zero model calls. Zero production changes. Zero B2/Stage-C changes. No
bridge implemented. RL-2026-002 not inspected, RL-2026-003 not touched.**
This addendum answers Phase G's own question from `## 13` above ("an
explicit architectural decision... on how CJ-2's validated
candidate-selection mechanism relates to the live pipeline's
single-persona generation model") with a specific, code-grounded target
architecture. It does not revise anything written above — it closes the
two gaps `## 8` and `## 11` flagged, and adds the decision `## 4`/`## 5`B
said was still missing.

### G.1 — Live pipeline, exact stage map

| Stage | File:function | Input | Output | Model call? | Failure behavior |
|---|---|---|---|---|---|
| Discovery (RSS) | `discovery.py:_fetch_rss_news` | persona, feed config | `{title,url,summary,source,date}` | No | Empty feed → `[]`, degrades gracefully |
| Discovery (news_seeds DB) | `discovery.py:get_news_seed` | — | `{id,url,title,summary,source_name,relevance_score,themes,disability_angle,pub_date}` or `None` | No | `None` on no match |
| Persona routing | `discovery.py:_news_seed_to_agent`/`_balance_agent` | themes/preferred agent | agent name | No | Falls through to `"Maya Flux"` default |
| Source fetch | `discovery.py:fetch_source_article` | url, fallback text | `(text, origin)`, origin ∈ `{fetched_article, fallback_summary, none}` | No | Cascades fetch methods → `None`, never blocks |
| Evidence packet | `grounding.py:build_evidence_packet` | source_text, origin | `{source_text, source_hash, source_truncated, provenance}` | No | Pure function |
| **Fable editorial brief** | `llm.py:_fable_editorial_brief` (~L686) | title, summary, angle, agent, evidence_packet | `{persona, angle, register, seed_sentence, opening_scene, opening_shape, correction_moment:{evidence_candidate}, resisting_example, cross_cite, grounding_status, grounding_violations}` | **Yes** | `None` on schema failure → publishes without brief (logged, not blocked) |
| Grounding validation | `grounding.py:validate_brief` | brief, evidence_packet | brief, unverifiable fields forced to `"not_found"` | No | Fail-closed per field only |
| Draft generation | `generate.py` + `llm.py:call_llm_via_openclaw_session` | brief + persona + evidence prompt (~150 lines) | article body | **Yes**, 5-provider cascade (Opus→Sonnet→GPT-5.2→Gemini→local Qwen) | Provider cascade absorbs individual failures |
| **Fable editorial review** (already live — distinct from the paused Phase 1.5B "review-seat ROI" experiment) | `llm.py:_fable_editorial_review` (~L925) | draft, agent, brief_angle, evidence_packet | `(verdict, notes)` | Yes | Non-blocking |
| Pre-commit gate | `gate.py:_pre_commit_gate` (~L188) | content, article_type | `(content, changed)` | Yes (1 surgical-fix pass max) | Readability hard-fail + 15 rules (R1-R15); blocking |
| Fact-check | `fact_check.py` | article content | contradicted-claims list; repaired file | Yes (extraction + live Perplexity Sonar + one-shot repair) | One-shot; failure leaves content as-is |
| Publish | `publish.py` | metadata, content | file + git commit/push | No | Push failure caught |
| Post-publish review | `review.py:validate_article` (~L419) | content, slug | citation flags, engagement read, telemetry | Yes | Explicitly **never gates publication** |

**Editorial doctrine — where it actually lives (exact citations):**
- *Disability as instrument, not required topic*: `llm.py:234-238` — "Disability as culture and identity — never tragedy or inspiration porn... a way of knowing that can reveal something the dominant world has failed to notice"; `llm.py:717-719` — "writes about the world through their specific disability lens, not about disability as a topic."
- *No superpower/compensation framing*: `llm.py:239` — "not a superpower, compensation, heightened sense, inspiration"; reinforced per-persona in `personas.py:26`.
- *"Category jump"*: **not found anywhere in the live pipeline** — confirmed as research-track/tasklist vocabulary only, not a live enforcement mechanism.
- *No internal-machinery leakage*: not a named rule — true only structurally, because the live pipeline has no CJ vocabulary to leak (it never imports the CJ tree). `gate.py`'s jargon rules (R10/R12) catch generic academic register, not internal-machinery leakage specifically — **this does not automatically protect a future CJ-2-sourced draft**, since that draft's inputs would carry genuinely new vocabulary (`engine_move`, `R1_R2_SEMANTIC_CONFLICT`, etc.) gate.py has never been tuned against.
- **Gap confirmed, not assumed**: "disability lens reveals the mechanism of the subject" is argued for in prompt rationale but gated by no deterministic or LLM check today.

### G.2 — CJ-1/CJ-2/B2/Stage-C, exact field-level schema

- **CJ-1** (`cj1_v3_validator.py`): `decision` (PASS/NO), `ostensible_category`, `resisting_detail`, `source_anchors` (1-3 exact source excerpts), `friction_type` (enum), `open_question`, `reason`. No headline field.
- **Stage A** (`cj2_reference_probe.py`): `status` (candidate/abstain), `seed_evidence_refs`, `additional_source_observations` (≤2 more excerpts), `engine_move`, `seed_engagement`, `interpretive_inference`, `conceptual_shift`, `claimed_contribution`, `removed_engine_test` (stripped before Stage C ever sees it), `abstain_reason`. Tagged by capsule label P/S/Z/M. **No headline/angle-summary field.**
- **Stage B**: deterministic only, zero model calls — schema/anchor validation, not ranking. Output: `{valid, violations}` per candidate.
- **B2 terminal state** (`compute_effective_v2`): `{per_claim: {role, support, declaration, consistency, effective_status}, effective_verdict: safe|unsafe|ambiguous}` — candidate-level, worst-case across claims.
- **Admission gate**: `{terminal_state, routing, enter_stage_c, repair_occurred, item_id}` — explicitly documented as carrying "no claim content, no source text, nothing Stage C's own prompt should ever see."
- **Stage C** (frozen prompt `cj2-stage-c-v1.txt`): per-letter `{factual_integrity, seed_engagement, engine_dependence, conceptual_movement, distinctive_contribution, assessment, reason}` plus `selection: {editorial_winner, runner_up, margin, why}`. **`editorial_winner` is a bare anonymized letter, not content** — the letter→candidate mapping is deliberately kept in a separate `letter_map` file, outside Stage C's own payload, for anonymity during judging.

**Direct finding, load-bearing for `## G.4` below: nothing anywhere in
this pipeline — CJ-1, Stage A, or Stage C — produces headline, lede, or
angle-in-plain-English text.** Every field at every stage is internal
analytical language written for a comparator/auditor, not a reader.
`claimed_contribution`/`conceptual_shift` are the closest things to a
"pitch," but Stage C's own instructions explicitly treat
`claimed_contribution` as unreliable candidate self-testimony, not usable
copy. This is confirmed by direct code reading, not inferred from the
research narrative.

### G.3 — Responsibility overlap, classified

| Function | Live pipeline | CJ-2/B2 | Classification |
|---|---|---|---|
| Idea/angle generation | `_fable_editorial_brief`, single persona | Stage A, 4 competing capsules | **COMPLEMENTARY** — different diversity axis (see `## G.4`) |
| Candidate selection/judging | None today (single candidate, no competition) | Stage C comparator | **SEPARATE PURPOSE** — live pipeline has no equivalent step to overlap with |
| Factuality checking | `fact_check.py` — live web verification of already-drafted prose | D0/C0/R1/R2/B2 — deterministic anchor-verification of a pre-draft structured claim | **COMPLEMENTARY, not duplicate** — different failure surfaces (see `## G.7`) |
| Persona-voice fidelity | `_fable_editorial_review` (already live) | None — CJ-2 has no prose, so no voice to check | **SEPARATE PURPOSE**, and a real future asset (`## G.10`) |
| Prose-quality gating | `gate.py` (readability, jargon, mechanical rules) | None | **SEPARATE PURPOSE** — CJ-2 produces no prose to gate |
| Old "judge-panel/multi-draft" idea | Deferred, never built (`audience-engagement-tasklist.md:452-556`) | Stage C | **OLD VERSION / SUPERSEDED CONCEPT for a NARROWER slice only** — see `## G.4`, this is not a clean supersession |

### G.4 — Judge-panel/multi-draft reconciliation (closes the roadmap gap)

Read the full section directly (not re-derived from prior summary).
Decision on 2026-08-09 was to build option (b) — **two full parallel
drafts, same persona, judged, best kept** — never option (a) (cheap,
opening-paragraph-only) or (c) (expensive, full multi-persona panel).
Concrete design existed (parallel writer calls, a new comparative judge
prompt, shadow-mode first) but **the code was never written** — attention
moved to a separate "anchor-architecture blueprint (Stages A-E)."

**Every candidate-divergence mechanism discussed there — structural-shape
alternation, sub-angle within the same topic, persona-beat foregrounding,
freeform "don't take the obvious angle," even a later-proposed Stage-G
variant using two independent `_fable_editorial_brief` calls — keeps the
SAME persona for both candidates.** Divergence comes from angle/shape,
never from persona. **CJ-2 is categorically different: 4 distinct
personas' engine capsules compete simultaneously.**

**Answer: NOT a clean supersession.** The old item addresses *same-persona
angle diversity*; CJ-2 addresses *cross-persona competitive selection*.
These are different axes that could both independently be worth building.
**Corrected status for the old roadmap item: still deferred, but now
explicitly known to be a distinct mechanism from CJ-2, not a duplicate
awaiting CJ-2's arrival** — its own build decision does not need to wait
for, and is not resolved by, the CJ-2 integration decision below. Neither
is implemented by this pass.

### G.5 — Integration options evaluated

**A. CJ-2 replaces the existing candidate-selection/judge layer.**
Rejected as premature: the live pipeline has no candidate-selection layer
to replace in the first place (only one candidate is ever generated per
article), so "replacing" it would mean deleting the entire single-persona
brief→draft path and substituting something that has never produced an
article, has no persona-voice mechanism, no prose-level fact-check, and
no editorial-doctrine enforcement of its own. High latency/cost (D0/C0/
R1/R2/repair/Stage-C × up to 4 candidates, vs. one brief + one draft
call). Would silently drop years of production-tuned `gate.py`/
`fact_check.py`/persona-voice review with nothing proven to replace them.

**C. CJ-2 remains a parallel research/audit system indefinitely.**
Rejected as underusing validated work: once B2/CJ-2 reaches
production-candidate status, never feeding it anywhere wastes the actual
value it offers (a materially stronger, anchor-verified factuality floor
on the *idea* stage, plus genuine cross-persona competition the live
pipeline has never had).

**B/D. CJ-2 augments the existing brief step — chosen, specified
precisely as D.** Not "B" left vague — a specific mechanism: **CJ-2's
validated Stage-C winner becomes an alternate, optional UPSTREAM SOURCE
for `_fable_editorial_brief`'s role, not a replacement for anything
downstream of it.** A small, deterministic bridge function translates the
reconstructed winning candidate (Stage-A fields + CJ-1's verified
`source_anchors`) into the *same output shape* `_fable_editorial_brief`
already produces today, so `generate.py`'s draft call, `_fable_editorial_review`,
`gate.py`, `fact_check.py`, `review.py`, and `publish.py` all run
**completely unchanged**. CJ-2 only ever competes for *which idea* gets
written, in a form indistinguishable, downstream, from today's brief.

Evaluated against the requested criteria: **architectural simplicity** —
highest of the three real options, one small new function, zero changes
to seven existing modules; **duplicate model work** — none, the bridge is
deterministic; **source-grounding integrity** — improved (CJ-1's
resolver-verified anchors are stronger than the brief's own per-field
`validate_brief` check, which still runs anyway as a second layer);
**factuality authority** — cleanly split, see `## G.7`; **editorial
quality** — unaffected, since `gate.py`/persona prompts/`_fable_editorial_review`
are untouched; **persona/Mind Engine preservation** — fully preserved,
CJ-2 never touches persona voice; **latency/cost** — CJ-2's own cost is
real (multi-candidate D0/C0/R1/R2/Stage-C) but is isolated to the
upstream idea-selection step, doesn't add a second full drafting pass;
**failure isolation** — clean, see `## G.11`; **rollback** — trivial,
disable the bridge, brief step reverts to its current behavior
unmodified; **human intervention** — none added; **compatibility with
current publication pipeline** — total, by construction.

### G.6 — Editorial doctrine preserved, explicitly

Architecture D never asks CJ-2 to own disability-lens/no-superpower/
category-framing enforcement — those remain exactly where `## G.1`
found them (persona system prompts in `llm.py`/`personas.py`, and
`gate.py`'s rule set). CJ-2 was never designed to own them and does not
need to be. The one real new risk: `gate.py`'s jargon rules (R10/R12) have
never been checked against CJ-2-specific vocabulary reaching a draft
prompt — mitigated structurally by `## G.8`'s bridge contract explicitly
excluding all such vocabulary from ever crossing the bridge, not by
relying on `gate.py` to catch it after the fact.

### G.7 — Authoritative factuality layer, verified against implementation

Confirmed, not assumed: **B2 and `fact_check.py` check different failure
surfaces and both remain necessary.** B2/R1/R2 verify whether a
*structured analytical claim about the source* is anchored to real source
text, entirely before any prose exists — it cannot see, and structurally
cannot catch, something the drafting model invents *while writing prose*
from an otherwise-sound brief. `fact_check.py` verifies the *opposite*
failure surface — live-web verification of claims that actually appear in
finished prose — and cannot see whether the underlying *idea* overreaches
beyond what the source supports, since it has no visibility into Stage A/
B2's own reasoning. **Neither passing implies the other would pass.**
Division of authority: **B2 = pre-draft factual eligibility of the
winning idea. `fact_check.py`/`gate.py`/`_fable_editorial_review` = post-draft
factuality and fidelity of the actual generated prose.** Both stay; this
is complementary layering, not redundant authority.

### G.8 — Bridge contract: Stage-C winner → `_fable_editorial_brief`-shaped input

Target shape is the brief's own existing output schema (`## G.1`), since
that's what `generate.py` already consumes unchanged.

| Target field | Source | Classification |
|---|---|---|
| `persona` | Stage-A capsule label (P/S/Z/M) | **DERIVABLE, PROBABLE, NOT CONFIRMED** — initials plausibly map to Pixel Nova/Siri Sage/Zen Circuit/Maya Flux, but no explicit correspondence table was found in code this pass. **Verify before any implementation — do not assume.** |
| `angle` | Stage-A `claimed_contribution`/`conceptual_shift` | **MUST BE ADDED TO WINNER BRIEF** — both are analytical, not angle-shaped prose; needs a translation step, not a passthrough |
| `register` | — | **SHOULD REMAIN PRODUCTION-PIPELINE RESPONSIBILITY** — CJ-2 has no equivalent concept |
| `seed_sentence` | — | **MUST BE ADDED** — no CJ-2 field is a draftable sentence |
| `opening_scene`/`opening_shape` | — | **SHOULD REMAIN PRODUCTION-PIPELINE RESPONSIBILITY** — CJ-2 was never designed to make this decision |
| `correction_moment.evidence_candidate` | CJ-1 `source_anchors` + Stage-A `additional_source_observations` | **AVAILABLE DIRECTLY** — resolver-verified real excerpts are already evidence-candidate-shaped; the single cleanest reusable field |
| `resisting_example` | CJ-1/Stage-A `resisting_detail` | **DERIVABLE** — near-identical concept, likely light reshaping only |
| `cross_cite` | — | **UNNECESSARY / PRODUCTION-PIPELINE RESPONSIBILITY** — cross-references other personas' past pieces, unrelated to CJ-2 |
| `grounding_status`/`grounding_violations` | B2 `effective_verdict`/per-claim `support` as a strong prior; `validate_brief` still runs on the translated output | **DERIVABLE AS A PRIOR, MECHANISM STAYS PRODUCTION-PIPELINE RESPONSIBILITY** — B2 passing doesn't retroactively certify fields invented during translation |

**Must NOT cross the bridge, explicitly:** R1/R2 role/support/declaration
labels, `R1_R2_SEMANTIC_CONFLICT` state, B2's per-claim `consistency`/
`effective_status`, Stage C's five assessment enums, the anonymization
letter-map, any calibration/Reader-Lab label. None are needed downstream
and all are exactly the internal machinery this task's own instructions
warn against exposing to a writer prompt.

**Smallest-bridge conclusion**: only `angle` and `seed_sentence` require
genuinely new translation logic; `correction_moment`/`resisting_example`
are close-to-direct reuse; `register`/`opening_scene`/`opening_shape`/
`cross_cite` correctly stay production-owned regardless of candidate
origin.

### G.9 — Can the existing generator consume this with minor adaptation? YES

Per `## G.1`/`## G.8`, `generate.py`'s draft call consumes whatever shape
`_fable_editorial_brief` returns — it has no dependency on *how* that
shape was produced. A bridge that emits the identical shape requires zero
change to draft generation, `_fable_editorial_review`, `gate.py`,
`fact_check.py`, `review.py`, or `publish.py`. **No new writer
architecture is needed or justified.** The only missing capability is the
translation function itself (`## G.8`), not a generation capability.

### G.10 — Article-level validation boundary (future phase, not designed here)

Per the roadmap's own `## 6`/`## 7`, a future phase (Phase H) must prove,
for CJ-2-sourced drafts specifically, that: the winner's actual insight
(`claimed_contribution`) survives translation and drafting; the final
prose remains grounded (both B2's pre-draft check AND `fact_check.py`'s
post-draft check passing, not just one); the disability lens remains the
instrument (existing `llm.py` persona-prompt doctrine actually holds when
the input angle originated from CJ-2 rather than a live brief);
readability/accessibility hold (`gate.py`'s existing checks, run against
real CJ-2-derived drafts, not assumed to generalize); no internal label
leaks (`## G.6`'s new risk, needs its own explicit check, not just
`gate.py`'s generic jargon rules); the result is editorially publishable
by the same non-blocking review already in place
(`_fable_editorial_review`, `review.py`). **Not designed this pass** —
this is the "no protocol exists yet" gap the roadmap's `## 12` milestone 2
already named; this addendum only sharpens what that future protocol must
check.

### G.11 — Failure/fallback architecture

| Condition | Policy | Rationale |
|---|---|---|
| CJ-1 yields nothing | **FALL BACK TO EXISTING PIPELINE** (live brief runs as today) | CJ-1 finding nothing is a normal, frequent outcome (it's a strict friction gate), not an infrastructure failure — the source simply isn't CJ-1-eligible today |
| B2 blocks every candidate | **FALL BACK TO EXISTING PIPELINE** | Same reasoning — B2 is meant to be strict; 0/N passing is expected behavior, not breakage |
| Stage C has zero entrants | **FALL BACK TO EXISTING PIPELINE** | Already the documented behavior today (a synthetic null-selection result, no model call) — consistent, not new |
| Stage C fails mechanically (schema error, timeout) | **FALL BACK TO EXISTING PIPELINE**, log distinctly from "zero entrants" | Mechanical failure and "nothing qualified" must be told apart in logs even though the user-facing fallback is identical, so a real outage doesn't hide behind normal strictness |
| CJ-2 infrastructure unavailable entirely (Trident runner down, D1 unreachable) | **FALL BACK TO EXISTING PIPELINE** | Same as above; the live pipeline's own daily operation must never depend on CJ-2 infrastructure being up |

**Explicit risk analysis, as instructed — do not treat "fall back to
existing pipeline" as free.** Every fallback above resolves to the SAME
existing pipeline that has run daily without CJ-2's factuality floor for
as long as the site has existed — falling back is not a downgrade from
some CJ-2-secured baseline, it is a return to the status quo. The real
risk is different and worth naming precisely: **if CJ-2 involvement ever
becomes silently invisible in the published output** (no marker of
whether a given article's brief originated from CJ-2 or from the live
pipeline's own default), a rising CJ-1/B2 block rate could quietly erode
the fraction of articles getting CJ-2's benefit without anyone noticing a
regression, since the site keeps publishing normally either way. Mitigate
by recording, per article, which path produced its brief (a new,
non-secret metadata field on the draft) — flagged here as a requirement
for whenever the bridge is actually built, not implemented now.

### G.12 — Rollout strategy (sequenced, no step executed)

1. **SHADOW MODE** — CJ-2 runs alongside production on the same sources,
   its Stage-C winner (if any) translated via the bridge and logged, but
   `_fable_editorial_brief`'s own live output is what actually publishes.
   Compare, don't decide.
2. **COMPARISON MODE** — record, per article, whether CJ-2's translated
   brief and the live brief would have led to visibly different angles;
   still never controls publication.
3. **CJ-2-SOURCED DRAFTS, NOT PUBLISHED** — actually run the drafting
   step on CJ-2's translated brief for a sample of sources, compare the
   resulting draft against the normally-published one on the `## G.10`
   criteria, entirely offline.
4. **EDITORIAL PILOT** — human-reviewed CJ-2-sourced articles, published
   only after explicit review, small volume.
5. **PRODUCTION AUTHORITY** — CJ-2's bridge output allowed to publish
   through the normal automated pipeline like any other brief, once
   Phase H's protocol (once designed and passed) says so.

Each step requires evidence from the one before it before advancing;
none of this is executed by this pass.

### G.13 — Reader Lab post-B2-freeze role (closes the roadmap gap)

Confirmed and finalized, extending `## 8` above rather than replacing it:
Reader Lab's underlying mechanism (reviewer onboarding, round publication,
automated completion-detection/export/analysis, policy engine) is
**PERMANENT REUSABLE CALIBRATION INFRASTRUCTURE**. B2-specific calibration
rounds (RL-2026-001/002/003) end once the freeze protocol's stop rule is
satisfied — that part of the *task* is temporary, exactly as `## 8`
already said. After freeze, the same mechanism is the natural home for:
future factuality drift monitoring, a genuinely new task type once one is
needed (the design doc's own `## 19` names "category-jump quality" as a
plausible example — directly relevant to `## G.10`'s article-level
validation gap), model-change recalibration, and contested-production-case
review. **This does not become mandatory human approval for every
article** — consistent with minimizing human intervention, Reader Lab
stays a sampling/spot-check/contested-case mechanism, invoked by policy
(as `calibration_policies` already does today), never a per-article gate.

### G.14 — Human authority, unchanged

No new manual plumbing introduced. Human authority remains exactly where
the freeze protocol and `## 10` above already placed it: production
promotion, policy changes, reviewer onboarding, exceptional safety/
editorial disputes, and — new, added by this addendum — the Phase G
architectural decision itself and any future decision to advance a
rollout step in `## G.12`. Routine operation (bridge translation,
fallback selection, shadow/comparison logging) is fully automatic by
design, consistent with the standing goal.

### G.15 — Target integration architecture: **D**

**D — CJ-2's Stage-C winner becomes an alternate, optional upstream
source for the existing `_fable_editorial_brief` step, via a small
deterministic bridge, with zero changes to every downstream module.**
Not A (too risky, replaces working infrastructure with something
unproven at the article level), not C (wastes validated work), and a
concrete refinement of B rather than B left abstract. Justified directly
from `## G.1`-`## G.11`'s code-grounded findings, not preference.

### G.16 — Phase G exit artifact: the future integration contract

```
LIVE SOURCE/TOPIC INPUT (discovery.py — UNCHANGED)
  -> existing stage remains: news_fetcher/news_seeds, persona routing, source fetch, evidence packet
  -> [NEW, future] CJ-1 entry point: same evidence packet, offered to CJ-1 as an alternate path
       -> CJ-1 (friction gate) -> Stage A (4 capsules) -> Stage B (validation)
       -> B2 (D0/C0/R1/R2/repair, effective_verdict) -> admission gate -> Stage C (comparator)
       -> Stage-C winner (anonymized letter + letter_map -> reconstructed Stage-A candidate)
  -> [NEW, future] BRIDGE (deterministic, no model call): translates the reconstructed
       winner + CJ-1 source_anchors into a _fable_editorial_brief-shaped object (## G.8)
  -> _fable_editorial_brief (UNCHANGED) -- now optionally fed by the bridge's output
       instead of / alongside its own live model call, per whatever rollout step is active
  -> grounding.validate_brief (UNCHANGED) -> draft generation (UNCHANGED)
  -> _fable_editorial_review (UNCHANGED) -> gate.py (UNCHANGED) -> fact_check.py (UNCHANGED)
  -> publish.py (UNCHANGED) -> review.py (UNCHANGED) -> social.py (UNCHANGED)

FALLBACK (## G.11): any failure/empty-result anywhere in the CJ-1..Stage-C
  chain -> _fable_editorial_brief runs its own live path exactly as today,
  with a logged path marker (which origin produced this article's brief).
```

**Exact future insertion point:** a new call from wherever
`_fable_editorial_brief` is invoked, offering it a pre-computed brief-shaped
object when one exists, before falling back to its own live model call.

**Modules likely affected (future work, not this pass):** a new bridge
module (does not exist yet); `llm.py`'s `_fable_editorial_brief` call site
(needs to accept an optional precomputed input); `discovery.py` or
wherever articles are queued (needs to decide, per rollout step, whether
to attempt the CJ-1..Stage-C path at all for a given source).

**Modules explicitly NOT affected:** `personas.py`, `generate.py`'s draft
call, `_fable_editorial_review`, `gate.py`, `fact_check.py`, `publish.py`,
`review.py`, `social.py`, `grounding.py`, and every CJ-1/CJ-2/B2/Stage-C
module itself (D0/C0/R1/R2/repair-v1/admission-gate/Stage-C remain
untouched — the bridge only ever reads their already-computed output).

**Bridge schema:** `## G.8`'s table.

**Fallback behavior:** `## G.11`'s table.

**Rollout plan:** `## G.12`'s five steps.

**Nothing above is implemented by this pass.**

---

## PHASE G.1 — WINNER BRIDGE + ROLLOUT CONTRACT (2026-08-13, same day,
## continuation pass)

**Zero model calls. Zero production changes. No bridge code written. No
B2/Stage-C code touched. RL-2026-002 not inspected. RL-2026-003 not
touched.** This freezes the bridge/rollout contract Phase G's `## G.8`/
`## G.12` left as a table into an exact, code-verified design — resolving
the one open uncertainty Phase G flagged (persona mapping) and correcting
one assumption Phase G made without having read `_fable_editorial_brief`'s
actual body yet.

### G.1.1 — P/S/Z/M resolved: NOT an implemented mapping, and not needed

Traced directly against the frozen `CAPSULES` dict in
`cj2_reference_probe.py:46-72` — the actual executable definition, not
prose. Each of P/S/Z/M is defined ONLY by an `instrument`/`move`/
`strong_contribution`/`failure_mode` (four analytical *methods*: attends
to mediation/timing/translation; actor-environment relation; measurement/
classification; promise-vs-practice gap) — **zero persona-name references
anywhere in that dict**, confirmed by direct reading, not grep-absence
alone.

The canonical design doc (`cj2-competitive-reframing-design-2026-08-11.md:546-554`)
explains why, quoted exactly: *"The round-1 capsules named the persona
and, in their failure-mode lines, reintroduced exactly the disability
vocabulary... this whole design otherwise keeps out of the blind
competition... The Stage A model should not know a persona name at all —
it sees only an anonymous engine capsule. Internally: **Engine P = Pixel
Nova, Engine S = Siri Sage, Engine Z = Zen Circuit, Engine M = Maya
Flux** — that mapping exists only in the orchestrator, never in the Stage
A prompt."*

**Verified, and this matters: that mapping does NOT actually exist in any
orchestrator code found this pass.** An exhaustive grep for all four
persona names across every `automation/cj1_*.py`/`cj2_*.py` file returned
zero hits. The design doc states an *intended* correspondence for future
human/orchestration reference; no executable lookup table implements it
today. **This is outcome D (documented intent, inconsistent with current
code) with a twist: the anonymization itself is correctly, deliberately
implemented (matches design intent exactly) — only the reverse mapping
back to a persona name was never wired into code.**

**Per instruction, this pass does not guess that mapping into existence.
It also does not need to** — see `## G.1.2`: the bridge's consumer
(`_fable_editorial_brief`) doesn't take persona as an effective input at
all, so no design decision here is blocked on resolving it. If a future
pass ever needs the literal P→persona correspondence (e.g. for shadow-mode
logging attribution, `## G.1.9`), it must be **hand-authored fresh** from
the design doc's own quote above, or re-derived by comparing each engine
capsule's `instrument` text against each persona's own documented
`prompt_block` obsessions (`personas.py`) — never assumed live, and never
inferred from the P/S/Z/M *letters* themselves (they are not persona
initials; the doc's "P=Pixel/S=Siri/Z=Zen/M=Maya" correspondence is
readable as a mnemonic, not a citable code fact — do not encode it into
the bridge as if it were).

### G.1.2 — `_fable_editorial_brief`, exact input contract (read in full,
### `automation/orchestrator/llm.py:686-924`)

**Corrects one Phase-G assumption**: persona is NOT an effective input to
this function, even though `current_agent` is a formal parameter.

| Parameter | Classification | Actual role, verified in code |
|---|---|---|
| `news_title` | factual/source-adjacent context | Interpolated into the prompt as "Today's story" |
| `news_summary` | factual-adjacent context, NOT validated source evidence | Truncated to 400 chars; prompt explicitly warns it's unchecked |
| `disability_angle` | editorial context, NOT validated source evidence | Inspiration only, same explicit warning |
| `current_agent` (called `agent_name` at the one call site, `generate.py:280`) | **persona identity — but confirmed UNUSED inside the function body** (zero references in lines 686-924 beyond the signature) | The function independently lists **all 4 personas** and makes its own persona pick as part of its *output*, validated only against `self.agents` membership (`llm.py:884`). `current_agent` exists purely so the caller has a fallback identity if the brief is discarded — it is not consulted to constrain or bias Fable's own choice. |
| `evidence_packet` | the real factual/source material | `.get("source_text")` read directly for the prompt; the full object is also passed into `validate_brief()` at line 899 for hash/field checks |

**Practical consequence for the bridge: persona selection remains
entirely `_fable_editorial_brief`'s own existing responsibility, exactly
as it is today for live-sourced stories — the bridge does not need to,
and per `## G.1.1` cannot cleanly, supply a `persona` field.** This
directly satisfies `## 8` of this pass's own instructions ("Stage C is
NOT a persona-writing stage") more strongly than Phase G realized:
Stage C isn't just *not* a persona-writing stage — even the *existing
live persona-picking stage* doesn't take a pre-decided persona as binding
input. Whichever persona Fable would already have picked for a
CJ-2-sourced story is unaffected by adding the bridge.

**`angle`/`seed_sentence` — why they need real translation (verified from
the actual prompt text, not inferred):**
- `angle` must be **"the question the persona is finding out the answer
  to... one where you cannot predict their conclusion."** The prompt's
  own strongest instruction: *"BRIEF A QUESTION, NOT A VERDICT... Hand
  them something they do not know the answer to."* CJ-2's
  `claimed_contribution`/`conceptual_shift` are the opposite shape — a
  **completed** analytical judgment about what's editorially new, closer
  to a verdict than an open question. **A naive deterministic rename
  risks reintroducing the exact anti-pattern this prompt was rewritten to
  eliminate** (per its own history, `.claude/experiments/fable-review-roi-2026-08-10.md`
  — old briefs "produced essays that were delivery mechanisms for a
  conclusion the writer already held"). This is a genuine content-shape
  mismatch, not a labeling mismatch.
- `seed_sentence` must be **"concrete, not a question,"** subject to a
  deterministic post-check that silently blanks it if it contains an
  unverified specific. Lower risk than `angle` — a concrete, grounded
  sentence is closer in shape to CJ-1's own `resisting_detail`/anchor
  excerpts.

**Per this task's own instruction 5: `angle` translation is flagged as a
candidate new experimental component, not hidden inside the bridge as if
mechanical.** A deterministic best-effort composition is still specified
below (`## G.1.5`) as the default, but its risk of producing a
verdict-shaped `angle` must be checked empirically before trusting it —
not assumed safe because it's "just a rename."

**`correction_moment`/`resisting_example` — verified structured, not
prose, and NOT pre-supplied today:** exact object shape is `{editorial_need:
str, evidence_candidate: {status: found|not_found, source_excerpt,
named_person, direct_quote, dates_numbers}, interpretation: str}`
(`llm.py:826-853`). Today Fable itself proposes a candidate excerpt from
the evidence packet and `validate_brief`/`validate_evidence_field`
deterministically verifies it after the fact, force-downgrading anything
unverifiable to `not_found` — **the caller never pre-supplies a verified
excerpt today.** This is good news for the bridge: CJ-1's own
`source_anchors` (already resolver-verified exact substrings, a stricter
check than `validate_evidence_field` performs) can be inserted directly
as `evidence_candidate.source_excerpt` with `status="found"` — see
`## G.1.6`.

**Grounding/evidence-packet threading — verified, and load-bearing for
the bridge's grounding design (`## G.1.7`):** `generate.py:274` builds
**exactly one** `evidence_packet` per run and threads it by reference into
`_fable_editorial_brief`, which calls `validate_brief(brief, evidence_packet)`
internally (`llm.py:899`), stamping `source_hash`/`evidence_packet_hash`
from that exact object onto the returned brief. `generate.py:299-309` then
**independently re-checks** that the returned brief's stamped hashes match
the SAME `evidence_packet` object this run is using — **discarding the
brief entirely, fail-closed, on any mismatch** (identical severity to a
parse failure). This is a hard architectural constraint, not a soft
preference: **a CJ-2-sourced brief object must be validated via the exact
same `validate_brief()` call, against the exact same `evidence_packet`
object `generate.py` already built for this run** — it cannot carry its
own, separately-stamped provenance and expect to survive this check.

### G.1.3 — Winner object, reconfirmed (unchanged from Phase G, verified
### again, no contradiction found)

Stage C (`cj2-stage-c-v1.txt` frozen prompt) returns only
`{candidate_assessments: {letter: {...5 enums, reason}}, selection:
{editorial_winner: letter|null, runner_up, margin, why}}` — a bare
anonymized letter, never the winning content itself. The letter→capsule
mapping (`letter_map`) is deliberately persisted in a **separate** file,
outside Stage C's own payload, specifically for judging-blindness. To
reconstruct usable content: `editorial_winner` letter → `letter_map` →
engine label (P/S/Z/M) → that label's own Stage-A record (`engine_move`,
`interpretive_inference`, `conceptual_shift`, `claimed_contribution`,
`seed_evidence_refs`, `additional_source_observations`) → and, separately,
CJ-1's own frozen `source_anchors`/`resisting_detail` for the same seed
(available from the same run, not part of the Stage-A object itself but
sitting alongside it). **Confirmed again: nothing in this reconstructed
object is headline/lede-shaped** — this finding from Phase G stands
unchanged.

### G.1.4 — Bridge v1 schema: `cj2_winner_bridge_v1` — **SUPERSEDED, see
### `## PHASE G.1.1` below.** Kept verbatim, not rewritten, per this
### document's own append-only convention. The schema below targeted
### `_fable_editorial_brief`'s OUTPUT shape, which — as `## PHASE G.1.1`
### found — concealed exactly the semantic-ownership ambiguity Phase G.1.1
### exists to resolve. Do not implement from this version.

Target shape is `_fable_editorial_brief`'s own existing return schema
(`## G.1.2`), since that is the one thing every downstream module already
consumes unchanged. Naming follows this project's own `_v1`/`_v2` module
convention (`cj1_v3_anchor_resolver.py`, `cj2_b2_v2_probe.py`, etc.).

```
cj2_winner_bridge_v1 = {
  # -- SOURCE-A: direct from the reconstructed winner, no transform --
  "editorial_need_context": {                # SOURCE A
    "friction_type": <CJ-1 friction_type>,
    "resisting_detail": <CJ-1/Stage-A resisting_detail, verbatim>,
  },
  "verified_anchors": [                       # SOURCE A
    {"excerpt": <exact source substring>, ...}
    for each CJ-1 source_anchor + Stage-A additional_source_observation
  ],

  # -- SOURCE B: deterministic transform from the winner capsule --
  "seed_sentence": <derived, ## G.1.5>,        # SOURCE B
  "resisting_example": {                       # SOURCE B (near-direct, ## G.1.6)
    "editorial_need": <templated from friction_type/reason>,
    "evidence_candidate": {
      "status": "found",
      "source_excerpt": <one verified_anchors[i].excerpt, verbatim>,
      "named_person": <extracted deterministically IF excerpt contains one, else "">,
      "direct_quote": <extracted deterministically IF excerpt is itself quoted speech, else "">,
      "dates_numbers": [<extracted deterministically from excerpt, else []>],
    },
    "interpretation": <templated from CJ-1 reason/resisting_detail text>,
  },
  "correction_moment": { <same shape, second-best verified_anchors entry if one exists, else status="not_found"> },  # SOURCE B

  # -- SOURCE C: existing production context, untouched by CJ-2 --
  "register": null,             # SOURCE C -- left for _fable_editorial_brief's own equivalent logic to set, unaffected by winner origin
  "opening_scene": null,        # SOURCE C -- same
  "opening_shape": null,        # SOURCE C -- same
  "cross_cite": "",             # SOURCE C -- unrelated to CJ-2, always production-owned

  # -- SOURCE D: generated only by whichever process actually drafts the brief --
  "persona": null,              # SOURCE D -- see ## G.1.2, NOT supplied by the bridge
  "angle": <FLAGGED, ## G.1.5 -- deterministic attempt with explicit content-shape validation, or a new experimental component>,

  # -- provenance, out-of-band, never entering any prompt --
  "_bridge_provenance": {
    "bridge_version": "cj2_winner_bridge_v1",
    "cj1_seed_id": <str>, "stage_c_letter": <str>, "engine_label": <P|S|Z|M>,
    "admission_gate_terminal_state": <str>,   # provenance only, per ## 4's own instruction
    "source_hash": null,  # MUST be stamped from generate.py's own evidence_packet at validation time, never from CJ-1's separate snapshot -- ## G.1.7
  },
}
```

**Explicitly BARRED from ever entering this object** (verified against
`## G.2` of Phase G — reconfirmed, no exceptions found): R1/R2 `role`/
`support`/`declaration` labels, `problems`, `R1_R2_SEMANTIC_CONFLICT`
state, B2's `effective_status`/`consistency`, Stage C's five assessment
enums (`factual_integrity`, `engine_dependence`, etc.), the anonymization
`letter_map`, any Reader Lab/calibration label. `_bridge_provenance` may
carry the admission gate's own already-content-free `terminal_state`
string (documented as containing "no claim content, no source text" —
`## G.2`) for operational logging only — it must never be interpolated
into any prompt text.

### G.1.5 — `angle`/`seed_sentence` translation, precisely

**`seed_sentence` — deterministic, default path.** Compose from the
single strongest `verified_anchors` entry (prefer CJ-1's own primary
anchor over a Stage-A `additional_source_observation`): a light
deterministic reformat (e.g. quote the exact excerpt, or restate it as a
declarative sentence using only words already in the excerpt) — no new
facts introduced, satisfying "concrete, not a question" without a model
call. Must still pass through the SAME deterministic post-check
`_fable_editorial_brief` already runs on this field today (reuse, don't
reimplement).

**`angle` — flagged, not solved as mechanical.** A best-effort
deterministic default is specified (compose an open-question wrapper
around the *tension* CJ-1's own `friction_type`/`open_question` fields
already describe — CJ-1 literally has an `open_question` field, the
single closest existing match to what Fable's `angle` wants), but **this
pass explicitly does not certify that composition as safe** — per
instruction 5, it is recorded here as requiring its own small validation
pass (does the composed `angle` read as a live, unpredictable question,
or does it smuggle CJ-2's own `claimed_contribution` verdict in
question-clothing?) before any pilot uses it. This is deferred as a
named future check, not hidden inside "the bridge is deterministic
therefore safe."

### G.1.6 — `correction_moment`/`resisting_example`, verified near-direct

Confirmed, not just assumed: CJ-1's `source_anchors` and Stage-A's
`additional_source_observations` are both already-verified exact
substrings (resolver-checked, stricter than `validate_evidence_field`'s
own check) and slot directly into `evidence_candidate.source_excerpt`
with `status="found"` — no wording transformation needed for that
sub-field. `named_person`/`direct_quote`/`dates_numbers` require a small
deterministic extraction pass over the excerpt text (regex-shaped, not a
model call) — these are mechanical, low-risk. `editorial_need`/
`interpretation` are free prose in the live schema but are NOT
evidence-checked fields (`llm.py:850-853`: "this is NOT evidence and is
never checked against the source") — a template composed from CJ-1's own
`friction_type`/`reason` text is a safe, low-stakes deterministic fill,
not a semantic-generation risk on the level of `angle`.

### G.1.7 — Source/grounding handoff, corrected from Phase G

Phase G's `## G.8` said B2's `effective_verdict` could serve "as a strong
prior" for `grounding_status`. Confirmed still true, but `## G.1.2`
surfaces a stricter, load-bearing requirement Phase G didn't have:
**the bridge's output must be validated by calling `grounding.validate_brief()`
directly, against `generate.py`'s own already-built `evidence_packet` for
this run — not against CJ-1's own separately-fetched `source_snapshot`.**
If CJ-1 ran against a different fetch of the same source than
`generate.py`'s live `evidence_packet`, the two texts could diverge
(re-fetch timing, truncation length, extraction method), and
`generate.py`'s own fail-closed hash check (`## G.1.2`) would legitimately
discard the bridge's brief — not a bug, exactly the intended fail-closed
behavior, but a design implication worth stating plainly: **for the
bridge to work reliably rather than fail closed on most runs, CJ-1's own
source-fetch step should eventually consume the SAME `source_text` that
`discovery.py`/`generate.py` already fetch for that day's topic — a
future shared-fetch requirement, not solved by the bridge itself.** Not
implemented this pass; flagged as a real prerequisite for any pilot
beyond shadow/comparison mode, where hash mismatches wouldn't matter
since nothing publishes yet.

### G.1.8 — Persona responsibility, reconfirmed

Per `## G.1.2`, `_fable_editorial_brief` already owns persona selection
completely and independently of any winner's origin — this satisfies
instruction 8 directly: the bridge carries no `persona_id`, and existing
persona execution (voice, disability lens, editorial perspective) is
structurally untouched, not merely "preserved by design intent."

### G.1.9 — Path provenance tag

```
cj2_path_provenance ∈ {
  LIVE_LEGACY_PATH,     # today's only value -- _fable_editorial_brief's own live model call
  CJ2_SHADOW,           # bridge computed and logged, never offered to _fable_editorial_brief
  CJ2_WINNER_DRAFT,     # bridge output offered to and used in an unpublished pilot draft
  CJ2_PRODUCTION,       # bridge output used in a published article
}
```
Operational metadata only (a field in the run's own log/DB record, e.g.
alongside the existing `review.py` sidecar) — **never rendered in article
prose, never exposed to any public UI**, satisfying instruction 9's own
constraint. Purpose, stated in Phase G and reconfirmed: makes "did this
article originate from a CJ-2 winner or the existing path" answerable
per-article, preventing silent erosion of CJ-2's actual contribution rate
as CJ-1/B2's strictness fluctuates.

### G.1.10 — Fallback policy, by rollout stage (not one rule for all)

| Stage | CJ-2 failure/empty result | Fallback article allowed? | Rationale |
|---|---|---|---|
| **SHADOW MODE** | Existing pipeline proceeds exactly as today; log failure + `LIVE_LEGACY_PATH` | Yes, always — CJ-2 never touches publication | No risk; the point is observation |
| **COMPARISON MODE** | Same as shadow; additionally record the divergence (or lack of one) | Yes, always | Still purely observational |
| **UNPUBLISHED CJ-2 DRAFT PILOT** | No CJ-2 draft generated for that slot; the normal production article for that source may still proceed on its own, separately, unaffected | Yes, the *normal* article, not a CJ-2 one | CJ-2 output isn't published at this stage regardless, so "fallback" here just means "the experiment produced no comparison artifact this time" |
| **EDITORIAL PILOT** | **No CJ-2-sourced fallback article is auto-published.** A CJ-2 failure at this stage means: no CJ-2 candidate for human review that day — the pilot simply has one fewer reviewed item. The existing pipeline running its OWN normal article for a DIFFERENT source that day is unaffected and is not "a fallback" for the failed one. | No, not for the specific failed slot | At pilot stage, articles are individually human-reviewed before publishing — inventing an auto-published substitute defeats the purpose of a pilot |
| **CJ2 PRODUCTION AUTHORITY** | **Evaluated explicitly below — this is the one stage where "just fall back to the old pipeline" is not automatically acceptable.** | **See analysis below** | |

**Production-authority analysis, per instruction's own recommended
principle ("once a guarantee is advertised as part of production, silent
fallback must not erase that guarantee"):** of the five options offered
(A fail-closed/no article, B queue/retry, C explicit visible-flag
fallback, D human exception, E silent old-pipeline fallback) — **E alone,
silently, is rejected as the default at this stage.** Reasoning: by the
time CJ-2 reaches production authority, its factuality floor and
cross-persona selection are presumably part of what the site *is*
claiming to do for at least some fraction of articles; a silent E would
mean that claim quietly stops being true whenever CJ-1/B2 is strict
(which, per this project's own held-out-evaluation discipline, is
*expected* to happen often — B2 has produced 0/14 safe admissions to
date). **Recommended combination, not a single letter: C (existing
pipeline fallback IS allowed, but only with a persisted, visible
`cj2_path_provenance=LIVE_LEGACY_PATH` marker, never silent) + B for
routine strictness (retry the SAME source/topic against CJ-2 on a later
cycle before falling back, since B2 blocking today doesn't mean the
source is permanently ineligible) + A only for the narrow case of total
CJ-2 infrastructure unavailability persisting past a defined retry budget
(then no article for that specific slot, rather than quietly reverting to
be indistinguishable from `LIVE_LEGACY_PATH` while claiming otherwise).**
D (human exception) is reserved, not routine — consistent with `## 14`'s
minimize-human-intervention principle; it's the release valve for a
persistent pattern the automatic B/C combination doesn't resolve, not the
normal path. **This is a recommendation for the eventual production-authority
design, not a decision executed now** — no rollout stage anywhere near
this one is reached yet.

### G.1.11 — Zero-entrant behavior, by rollout stage

- **Shadow/comparison**: production entirely unaffected by construction
  (`## G.1.10`); zero entrants is simply logged as a normal, expected
  outcome given B2's own strictness.
- **CJ-2 draft pilot**: no CJ-2 draft generated for that source that
  cycle; not an error.
- **Production authority**: per `## G.1.10`'s combination — retry later
  (B), then fall back with a visible provenance marker (C), never a
  silent identical-looking article. **B2 is never weakened to manufacture
  a safe admission just to maintain daily volume** — explicitly rejected,
  matching this project's own standing fail-closed discipline
  (`final-evaluation-freeze-protocol-2026-08-13.md`).

### G.1.12 — Cost/latency budget, architectural estimate only

Current live path per article (from `## G.1`'s stage map): ~1 brief call
+ 1 draft call + 1 Fable-review call + ≤1 gate surgical-fix call + fact-check
extraction/verification (~2-4 calls) + post-publish review's own checks
(~2-3 calls) ≈ **6-10 model calls today, already, with no CJ-2
involved.**

Adding the CJ-1→Stage C chain (architecture D adds, never replaces):
CJ-1 (1 call) + Stage A (4 calls, one per capsule — naturally parallel,
independent of each other) + D0/C0 for however many candidates survive
Stage B (up to 4 × 2 = 8, parallel across surviving candidates) + R1/R2
similarly (up to 4 × 2 = 8, parallel) + repair-v1 (conditional, 0-4) +
Stage C (**1 single comparator call evaluating all surviving candidates
together**, per the frozen prompt's own multi-candidate schema — not one
call per candidate). **Total added: roughly 14-26 calls in the worst
case, concentrated entirely in the new upstream stage.** This is a
substantial addition, not incremental — architecture D can roughly
double-to-triple total model-call volume per CJ-2-attempted article.

**Latency, distinct from raw count**: if Stage A's 4 calls run in
parallel, and D0/C0/R1/R2 run in parallel across whichever candidates
survive Stage B, wall-clock adds roughly 5-6 sequential *rounds*
(CJ-1 → Stage A batch → D0/C0 batch → R1/R2 batch → optional repair →
Stage C), not 14-26 sequential calls. **Flagged, not solved: every
existing CJ-1/CJ-2 probe script read this session runs its calls
sequentially, as an offline research harness** — none were built for
low-latency production use inside a daily cron window. Parallel execution
is an implementation requirement for any pilot beyond shadow mode, not
something to assume is already true of the research code.

**No optimization performed or recommended here** — flagged for whoever
eventually implements the bridge, per instruction 12's own scope.

### G.1.13 — Shadow-mode observability, minimum required fields

Per run, logged (never public-facing):
`source_identity` (url/hash), `cj1_candidate_count` (0/1 — CJ-1 is a
single-candidate friction gate, not multi-candidate), `stage_a_candidate_count`,
`stage_b_valid_count`, `b2_admitted_count`/`b2_blocked_count`,
`stage_c_execution_state` (executed | zero_entrants | mechanical_failure),
`stage_c_winner_engine_label` (P/S/Z/M, not a persona name — `## G.1.1`),
`bridge_validity` (pass/fail against `validate_brief`), `cj2_path_provenance`
(`## G.1.9`), `existing_pipeline_brief_persona`/`angle` (what the live path
would have/did produce for the same source, for comparison), and
`failure_reason` (structured, one of a fixed enum, matching `## G.1.10`'s
own fallback-decision inputs). **No R1/R2/B2 internal reasoning content
appears in any log surfaced to a non-engineering audience** — satisfying
instruction 13's own boundary; engineering-only debug logs may still carry
full internal detail, since that's not "public logs/UI."

### G.1.14 — Article-level pilot contract (artifact pair only, no scoring
### study designed)

Future unpublished pilot compares exactly two artifacts per sampled
source: **(a)** the article the existing live pipeline would generate
today (its own real brief → draft → gate → fact-check chain, run
normally), and **(b)** an article generated from the SAME source using
the bridge's `cj2_winner_bridge_v1` output as `_fable_editorial_brief`'s
input instead of a live model call, then run through the **identical**
unchanged downstream chain (draft → `_fable_editorial_review` → `gate.py`
→ `fact_check.py`). Both must be tagged with their `cj2_path_provenance`
value and share the same `source_hash`/`evidence_packet_hash` (`## G.1.7`).
**Required later evaluation dimensions** (per instruction 14, not scored
now): whether (b) preserves the Stage-C winner's actual insight
(`claimed_contribution`) through drafting; whether (b) remains as grounded
as (a) under `fact_check.py`; whether the disability lens in (b) reads as
instrument rather than topic, same doctrine as `## G.1` found governing
(a); readability parity under `gate.py`'s existing checks; editorial
quality parity under `_fable_editorial_review`; whether (b) exhibits a
genuine category-jump/contribution the old judge-panel item's own
language names; and whether drafting introduced any NEW factual error not
present in the winning candidate's own B2-cleared claims. **Not designed
as a scoring study this pass** — only the artifact pair and required
provenance are frozen here.

### G.1.15 — Reader Lab post-freeze role, formalized (per instruction 15,
### restating Phase-G's `## G.13` as the settled position, not a new one)

Unchanged from Phase G: B2-specific Reader Lab rounds (RL-2026-001/002/003)
end once the freeze protocol's own stop rule is satisfied. The underlying
mechanism (reviewer onboarding, round publication, automated completion-
detection/export/analysis, policy engine) is **permanent, reusable
calibration infrastructure**, explicitly available for — not limited to —
future factuality drift after a model change, a genuinely new task type
(the design doc's own `## 19` names article-level/category-jump judgment
as a plausible example, directly relevant to `## G.1.14`'s future pilot),
and recurring contested-failure-class review. **It does not become
per-article mandatory human approval** — Reader Lab remains a
sampling/policy-invoked mechanism (`calibration_policies`, already live),
never a universal publication gate. Nothing changed by this pass; this
section exists only to confirm the position is now recorded in two places
consistently.

### G.1.16 — Old judge-panel/multi-draft item, restated (per instruction
### 16 — no new scheduling decision)

Unchanged from Phase G's `## G.4`: same-persona angle diversity (the old
item) and cross-persona competitive selection (CJ-2) are distinct axes,
neither superseding the other. **Explicitly not scheduled by this pass
either** — remains deferred, to be revisited only if future evidence shows
same-persona angle diversity is a real, separately-measured production
bottleneck, not because it appears in a discussion draft.

### G.1.17 — Phase G.1 exit: bridge contract frozen as design, not code

**Confirmed: no runtime bridge code was written. No `production_orchestrator.py`,
`generate.py`, or `llm.py` edit was made. No model call was made. No
B2/Stage-C module was touched. RL-2026-002 was not inspected. RL-2026-003
was not ingested or published.** `cj2_winner_bridge_v1` (`## G.1.4`) is a
frozen conceptual schema, ready to be implemented in a future pass once a
rollout decision (`## G.12`) authorizes shadow mode specifically — this
pass does not authorize that either, it only makes the contract precise
enough to implement correctly when authorized.

**Correction, same day, `## PHASE G.1.1` below: `## G.1.4`'s schema
targeted the wrong shape and is superseded, not merely refined — see that
section before implementing anything from this one.**

---

## PHASE G.1.1 — BRIDGE SEMANTIC-OWNERSHIP CLARIFICATION (2026-08-13,
## same day, continuation pass)

**Zero model calls. Zero code changes.** Not another architecture audit —
this closes one specific contract ambiguity `## G.1` left open: `## G.1.4`
called `cj2_winner_bridge_v1` "deterministic," then immediately flagged
`angle` as needing "real composition" because CJ-2's material is
verdict-shaped while Fable's own prompt demands an open question. A
deterministic bridge cannot also contain an unflagged editorial decision —
this section resolves who owns that transformation, using only what's
already established from direct code reading (`## G.1.2`), no new
research.

### Principle applied

Every bridge transformation is classified as **A. deterministic structural
transport**, **B. deterministic formatting**, or **C. semantic/editorial
composition**. Only A/B belong in the bridge. C must live in an explicitly
semantic stage — and one already exists and already owns exactly this
job: `_fable_editorial_brief` itself.

### The error `## G.1.4` made, stated plainly

`## G.1.2`'s own table already contained the fix and wasn't applied to
the schema: `angle`, `seed_sentence`, `correction_moment`,
`resisting_example`, `persona`, `register`, `opening_scene`,
`opening_shape`, and `cross_cite` are **every one of them fields
`_fable_editorial_brief` PRODUCES as output** — none of them are function
*parameters*. `_fable_editorial_brief`'s actual input parameters
(`## G.1.2`) are exactly five: `news_title`, `news_summary`,
`disability_angle`, `current_agent` (confirmed unused), `evidence_packet`.
**`## G.1.4` designed a bridge that manufactures Fable's OUTPUT and hands
it over pre-made — which is precisely how a bridge conceals a new
editorial decision as if it were data transport.** The fix is not to find
a cleverer deterministic template for `angle` — it's to stop trying to
produce `angle` at all, and feed Fable's *existing, unchanged* five input
parameters instead, exactly as `discovery.py` already does for a
live-sourced story.

### ANGLE OWNER: **Fable — with no input-contract adaptation required**

`_fable_editorial_brief` has never accepted a precomposed `angle`; it has
no parameter for one. The preferred architecture the task describes
("Stage-C winner → bridge carries semantic material + anchors →
`_fable_editorial_brief` performs its existing editorial transformation")
is not just supported by the code — **it is the only architecture the
current input contract permits.** No adaptation is needed because there
was never an input slot to adapt around: the ambiguity existed only in
`## G.1.4`'s design, not in the actual function signature. This adds
zero model calls — it is the SAME single existing Fable call, given a
CJ-2-originated "news item" instead of a live-discovered one.

### SEED OWNER: **Fable, same reasoning, no exception**

`seed_sentence` is equally an output field (`## G.1.2`), never an input.
Nothing about its lower semantic-risk profile (noted in `## G.1.5`) changes
who owns producing it — lower risk was never a reason to move ownership
into the bridge; a deterministic template that happens to be easy to
write is still category C if the field it fills is one `_fable_editorial_brief`
generates itself. It stays Fable-owned, unconditionally.

### ANCHORS: correction_moment / resisting_example — also Fable-owned
### outputs, reached through evidence_packet, not a new field

Same fix applies: these are outputs too (`## G.1.2`: Fable "proposes a
candidate excerpt from the evidence packet" itself; `validate_brief`
verifies it after the fact). **They do not need, and must not receive, a
pre-supplied value from the bridge.** CJ-1's verified `source_anchors` and
Stage-A's `additional_source_observations` are exact substrings of the
same source text — reachable already, because that source text is (or,
per `## G.1.7`, must be) the SAME text inside the canonical
`evidence_packet` Fable already searches on its own. No new field is
required for these excerpts to be *available* to Fable.

**Exact source fields, for the record:** CJ-1 `source_anchors` (resolver-
verified exact substrings, from `cj1_v3_validator.py`'s schema) and
Stage-A `additional_source_observations` (same exactness guarantee, from
`cj2_reference_probe.py`'s schema) — both already-verified, both already
inside the shared source text once `## G.1.7`'s invariant holds.

**One real, honest gap, distinct from the angle/seed_sentence question:**
today Fable searches the evidence packet freely and may land on a
DIFFERENT (still valid) excerpt than the one CJ-1/Stage-A specifically
flagged as the friction point — nothing currently steers it toward the
winning candidate's own anchor. This is not a semantic-ownership
ambiguity (Fable still owns the composition either way) — it's a fidelity
question: does the winning insight reliably survive? Addressed below via
`disability_angle`, using an existing input slot, not a new one.

### EVIDENCE_PACKET INVARIANT (formalized, unchanged from `## G.1.7`,
### restated here as a hard precondition on this section's design)

**A CJ-2-sourced bridge is valid only when it reconnects to the exact
same canonical `evidence_packet` object `generate.py` already built for
this run, and passes that same object through `validate_brief()`
unmodified.** An equivalent, separately-fetched text is not sufficient,
even if byte-identical in content — the check is against the SAME object
reference/hash, not against equivalent meaning. The bridge must never
construct a second, competing provenance universe from CJ-1's own source
fetch. Practical consequence, unchanged from `## G.1.7`: CJ-1's own
source-fetch step should eventually consume the same `source_text`
`discovery.py`/`generate.py` already fetch, or most bridge attempts will
correctly fail closed on hash mismatch.

### PERSONA (confirmed non-requirement, restated for completeness)

P/S/Z/M are analytical-instrument labels (`## G.1.1` above), not runtime
persona identity. The design doc's P=Pixel Nova/S=Siri Sage/Z=Zen
Circuit/M=Maya Flux correspondence is documentary intent, never an
implemented mapping. `_fable_editorial_brief` ignores `current_agent` and
picks its own persona from all 4, unconditionally. **No persona mapping
is created here, and none is needed** — this section changes nothing
about that finding.

### FINAL BRIDGE V1 — revised, minimal, no Fable-owned field present

```
cj2_winner_bridge_v1 = {
  # -- Inputs to _fable_editorial_brief's EXISTING, UNCHANGED parameter
  #    list. The function itself is not modified; it receives a
  #    CJ-2-originated "news item" instead of a live-discovered one. --

  "news_title": <DETERMINISTIC FORMAT
                  -- the source article's own real title/metadata, the
                  same one CJ-1 evaluated; Fable's prompt already treats
                  this as flavor context ("Today's story"), never
                  validated evidence>,

  "news_summary": <DETERMINISTIC FORMAT
                    -- the source's own real summary if available, else a
                    plain factual restatement of CJ-1's friction_type/
                    resisting_detail; Fable's prompt already discounts
                    this field as unchecked>,

  "disability_angle": <DIRECT
                        -- CJ-1's resisting_detail/open_question carried
                        near-verbatim into this EXISTING "inspiration
                        only" slot -- the same functional role the live
                        pipeline's own news_seed.disability_angle already
                        plays. This is the mechanism, not a new one, that
                        gives the winning candidate's specific insight a
                        real (if non-binding) chance of steering Fable's
                        own angle/correction_moment toward the anchor
                        Stage C actually selected -- addressing the
                        fidelity gap noted above using an existing slot>,

  "current_agent": <PRODUCTION CONTEXT
                     -- whatever the caller already passes; confirmed
                     unused inside the function, not a bridge concern>,

  "evidence_packet": <PRODUCTION CONTEXT / HARD INVARIANT
                       -- MUST be generate.py's own already-built object
                       for this run; never a separately-fetched CJ-1
                       snapshot -- see EVIDENCE_PACKET INVARIANT above>,

  # -- Provenance, out-of-band, never entering any prompt --
  "_bridge_provenance": {
    "bridge_version": "cj2_winner_bridge_v1",
    "cj1_seed_id": <str>, "stage_c_letter": <str>, "engine_label": <P|S|Z|M>,
    "admission_gate_terminal_state": <str>,
    "source_hash": null,  # stamped from evidence_packet at validation time
  },
}
```

**Fields removed entirely from the bridge, relative to `## G.1.4`'s
superseded version — all now correctly absent, not merely null:**
`angle`, `seed_sentence`, `register`, `opening_scene`, `opening_shape`,
`correction_moment`, `resisting_example`, `cross_cite`, `persona`,
`grounding_status`, `grounding_violations`. **Every one is
FABLE-OWNED SEMANTIC COMPOSITION**, produced by Fable's own single,
unchanged, existing model call — identical mechanism whether the "news
item" came from live discovery or from a CJ-2 winner.

**BARRED INTERNAL FIELDS, unchanged from every prior pass, still zero
exceptions found:** R1/R2 `role`/`support`/`declaration`, `problems`,
`R1_R2_SEMANTIC_CONFLICT`, B2's `effective_status`/`consistency`, Stage
C's five assessment enums, the anonymization `letter_map`, any Reader
Lab/calibration label.

This bridge is now four real input fields plus provenance metadata — no
field in it requires anything that isn't **A** (structural transport:
`current_agent`, `evidence_packet`, all of `_bridge_provenance`) or **B**
(deterministic formatting: `news_title`, `news_summary`) or a **DIRECT**
carry-over into an existing permissive slot (`disability_angle`). No field
requires **C**.

### DECISION

**A — DETERMINISTIC BRIDGE CONTRACT NOW CLOSED.** The ambiguity `## G.1`
left open is resolved using the CURRENT `_fable_editorial_brief` input
contract, with zero function-signature changes and zero new model calls —
the semantic-ownership question wasn't a hard implementation problem, it
was `## G.1.4` targeting the wrong schema (Fable's output instead of its
input). One narrow, explicitly non-blocking observation for a future
pass, not a reason to choose B: `disability_angle` gives the winning
candidate's specific insight a real but non-binding chance of surviving
into Fable's own composition; a future dedicated "suggested evidence
candidate" input parameter would make that survival more reliable rather
than merely likely — flagged as an optional future enhancement, not a
precondition for closing this contract.

**Superseded:** `## G.1.4`'s schema (kept, marked, not deleted).
**Unchanged:** `## G.1.1`–`## G.1.3`, `## G.1.7`–`## G.1.17`'s
provenance/fallback/rollout/observability/Reader-Lab/judge-panel content —
none of it depended on the flawed schema and all of it still holds.

**No implementation. No `_fable_editorial_brief` modification. No model
call. RL-2026-002 not inspected. RL-2026-003 not touched. No new roadmap
audit started.**

---

## PHASE G.2 — SHADOW INTEGRATION IMPLEMENTATION (2026-08-13, same day,
## implementation pass)

**First actual code pass in this whole Phase-G sequence.** Builds the
smallest scaffold making `## G.1.1`'s closed bridge contract operable in
OFF (default) and SHADOW mode, with zero semantic tuning, zero production-
authority code, and zero live CJ-2 model calls anywhere.

### Insertion point (traced before writing anything)

`automation/orchestrator/generate.py`'s `_run_production_automation_locked`,
immediately before its existing `_fable_editorial_brief` call (line ~280):
`evidence_packet` is built exactly once (line 274); `_ns_title`/
`_ns_summary`/`_ns_dangle`/`agent_name` are already finalized. The hook
itself is placed a few lines LATER — right after the existing fable_brief/
degraded-stage `if/else` block fully resolves (after line ~350) — so it
can observe the run's final `agent_name`/`evidence_packet` without being
able to affect the real call at all (it runs strictly after that call has
already happened and its result has already been used).

### Bridge module: `automation/cj2_winner_bridge.py`

`cj2_winner_bridge_v1`, pure, dependency-free, zero I/O beyond its
arguments. `build_bridge_payload(winner, seed, evidence_packet,
current_agent, *, cj1_seed_id, stage_c_letter, engine_label,
admission_gate_terminal_state)` returns exactly the 5 arguments
`_fable_editorial_brief` already accepts (`news_title`, `news_summary`,
`disability_angle`, `current_agent`, `evidence_packet`) plus an
out-of-band `_bridge_provenance` dict. Matches `## G.1.1`'s revised schema
exactly: `news_title` — deterministic fallback chain (seed's own
`title`/`url`/`slug`, never invented); `news_summary` — always `""` (no
clean single field exists anywhere in the CJ-1/Stage-A schema; fabricating
one would be semantic composition); `disability_angle` — the seed's own
`resisting_detail`, verbatim, the single field per Phase G.1.1's own
no-invented-ranking-heuristic instruction; `current_agent`/`evidence_packet`
— passed through by reference, unchanged. No `angle`/`seed_sentence`/
`correction_moment`/`resisting_example`/`persona`/`register`/
`opening_scene`/`opening_shape`/`cross_cite` field exists in this module at
all — not null, absent, since all nine are Fable-owned outputs.

**Rejections, fail-closed, each with a structured `.reason`:** a raw
Stage-C comparator payload or bare `letter_map` passed instead of a
reconstructed winner (`WINNER_RECONSTRUCTION_FAILED`); a winner missing
required Stage-A fields or with `status != "candidate"`
(`WINNER_RECONSTRUCTION_FAILED`); a seed with no `resisting_detail`
(`WINNER_RECONSTRUCTION_FAILED`); any denylisted internal field found
anywhere in the assembled payload via a recursive scan
(`BRIDGE_VALIDATION_FAILED`) — defense in depth, since today's design
never actually forwards winner content wholesale, this guards a future
change that might. Denylist covers every field named in Phase G/G.1/G.1.1's
barred-field lists (R1/R2 labels, `problems`, `R1_R2_SEMANTIC_CONFLICT`,
B2 terminal state, Stage-C's five assessment enums, `letter_map`, Reader
Lab/calibration labels). `_bridge_provenance` uses an explicit 6-key
ALLOWLIST instead (`bridge_version`, `cj1_seed_id`, `stage_c_letter`,
`engine_label`, `admission_gate_terminal_state`, `source_hash`) — stricter
than a denylist for the one sub-dict where an admission-gate string is
legitimately allowed to travel, operationally, never as prompt text.

### Evidence-packet invariant, enforced in code (`## G.1.1`'s hard
### precondition, not just documented this time)

`_check_evidence_packet_identity`: requires `seed.source_sha256` AND
`evidence_packet.source_hash` both present and equal — absence on either
side is treated as a mismatch, not silently trusted, per the doc's own
"an unverifiable claim of identity is not identity." Never rebuilds or
re-fetches anything; only compares hashes generate.py/CJ-1 each already
computed independently.

### Orchestrator hook: `automation/orchestrator/cj2_shadow.py`
### (`CJ2ShadowMixin`, added to `ProductionOrchestrator`'s bases)

`_cj2_shadow_attempt(agent_name, evidence_packet)` — called from
`generate.py` only when `CJ2_INTEGRATION_MODE` (env var, default unset →
`"OFF"`) is not `"OFF"`. In `"SHADOW"` mode: loads a winner fixture from
`CJ2_SHADOW_WINNER_FIXTURE` (env var, a file path) if configured; with no
live CJ-1..Stage-C orchestration wired up anywhere yet, and none invoked
by this pass, a fixture is the ONLY possible source of a winner today —
in real, unconfigured production this env var is simply unset, so the
hook, even if some future pass turns SHADOW on, will always and only
record `NO_CJ2_WINNER` until a real producer exists. Bridges the fixture
via `cj2_winner_bridge`, discards the resulting payload immediately after
recording its outcome — nothing about it is read again by anything.
**Never appends to `self._degraded_stages`** — deliberately separate
tracking, since that list has a real, live blocking policy
(`generate.py` ~line 1127: `fable_brief` failing, or 2+ stages failing,
sets `fact_check_status: blocked` in the article's own frontmatter) a
CJ-2 shadow computation must never trigger. The entire method, plus its
own persistence call, is wrapped in one outer `try/except Exception`,
mirroring `_persist_article_plan`'s existing discipline exactly — cannot
raise into the real pipeline under any failure.

**Hook call site in `generate.py`:**
```python
if os.environ.get("CJ2_INTEGRATION_MODE", "OFF").strip().upper() != "OFF":
    self._cj2_shadow_attempt(agent_name, evidence_packet)
```
Three lines, self-contained (`os` already imported), no import of
`cj2_shadow`/`cj2_winner_bridge` at this line — that import is deferred
inside `_cj2_shadow_attempt` itself, so OFF mode adds no dependency of any
kind, not even an import, beyond one environment-variable read and one
string comparison.

### Mode behavior

**OFF (default):** proven, not just argued — `cj2_shadow_integration_test.py`
confirms the `cj2_shadow_runs` table isn't even created (the hook is never
called at all) and the real writer prompt is byte-identical to a run
where `CJ2_INTEGRATION_MODE` is unset entirely. **SHADOW:** the fixture is
bridged (or a structured failure recorded) and persisted; the SAME test
proves a *successful* SHADOW bridge produces a byte-identical writer
prompt to OFF mode — a valid CJ-2 winner being available changes nothing
about what actually publishes. No `PRODUCTION_AUTHORITY`/pilot mode exists
anywhere in this code.

### Provenance persisted (`automation/engagement.db`, new `cj2_shadow_runs`
### table — same file `_persist_article_plan`/`_persist_review_signals`
### already write to)

`integration_mode`, `path_provenance` (`LIVE_LEGACY_PATH`/`CJ2_SHADOW`
defined; `CJ2_WINNER_DRAFT`/`CJ2_PRODUCTION` defined but never emitted
this pass — no code path reaches them), `bridge_valid`, `failure_reason`,
`winner_present`, `bridge_version`, `engine_label`, `stage_c_letter`,
`cj1_seed_id`, `slug`, `agent`, `recorded_at`. No R1/R2/B2 reasoning, no
Reader Lab/reviewer data, no raw winner content — only the same
content-free identifiers Phase G's own `## G.2` already documented as
safe to log operationally.

### Test matrix (instruction 16) — results

Two suites, 53 checks total, all pass:
- `automation/cj2_winner_bridge_test.py` (26 checks) — valid payload
  shape; evidence-packet mismatch/missing-hash fail closed; malformed/
  abstained/incomplete winner rejected; **raw Stage-C letter/letter_map
  input rejected** (item F); denylist scanner unit-tested directly (item
  G); provenance allowlist drops anything unlisted; no ranking heuristic
  invented across competing winner fields; `news_title` fallback chain.
- `automation/cj2_shadow_integration_test.py` (27 checks) — runs the REAL,
  unmodified `_run_production_automation_locked()` via the existing
  `snapshot_test.py`/`writer_prompt_test.py` harness
  (`_import_orchestrator`/`_patch_methods`/`_isolate_paths`, same
  `BaseException`-sentinel capture-and-abort technique), covering: **(A)
  OFF mode inert** — table never created, prompt unaffected, no
  `_degraded_stages` entry; **(D) SHADOW/no winner** — records
  `NO_CJ2_WINNER`; **(B) SHADOW/valid winner** — bridges successfully,
  records it; **(C) SHADOW/wrong evidence_packet** — fails closed with
  `EVIDENCE_PACKET_MISMATCH`; **(E) malformed fixture JSON** — recorded as
  `WINNER_RECONSTRUCTION_FAILED`, never crashes production; **(F) a real
  Fable failure** — `_degraded_stages` gets exactly `["fable_brief"]`, CJ-2
  shadow's own independent success/failure never conflated with it; **(G)
  the load-bearing assertion** — OFF-mode's writer prompt is byte-identical
  to a successful-SHADOW-mode run's writer prompt.

**Existing test suite (item J): zero regressions.** Re-ran
`snapshot_test.py --check` (exact-value diff against 6 real published
articles' recorded fixtures), `writer_prompt_test.py`,
`lineage_persistence_test.py`, `executor_guard_test.py`,
`grounding_test.py` — all pass unchanged.

### Semantic isolation, confirmed directly

No CJ-1 prompt, Stage-A/B/C code, D0/C0, R1/R2, repair-v1, admission-gate
policy, `_fable_editorial_brief`'s own prompt, `gate.py` rule, or
`fact_check.py` logic was touched — confirmed via `git status` (exactly 4
files changed/added in production code: `generate.py`,
`production_orchestrator.py`, plus the 2 new bridge/hook modules and their
2 test files; nothing else).

### RL-2026-002 boundary, confirmed

This entire pass is deterministic plumbing — it does not read, wait for,
or depend on RL-2026-002 in any way, exactly per instruction 14. No
partial response inspected. No manual polling introduced.

### Deployment

**Not deployed** in the sense of being pushed to `origin/main` this pass.
**Committed locally** (see commit message) — the code is genuinely inert
by default (proven by test G above, not just argued) and adds no
dependency when `CJ2_INTEGRATION_MODE` is unset, which satisfies
instruction 17's bar for "may be deployed." Pushing is left as a deliberate,
separate decision for Jascha: this is still a live, unattended, daily-
publishing pipeline this session cannot integration-test against real
production secrets/DB/cron, and the general git-safety principle this
project already applies elsewhere (pushing is a shared-state action,
confirmed explicitly, not assumed) applies here too — recommended, not
executed automatically.

### Article-pilot readiness (instruction 18 — preparation only, not
### executed)

The pairing `## G.1.14` already specified (a normal-production article vs.
a bridge-sourced article for the same source) is now technically
possible in principle — the bridge exists, provenance exists, the
evidence-packet invariant is enforced in code — but requires (a) a real
CJ-1..Stage-C run producing a real winner (not invoked this pass), and (b)
`CJ2_INTEGRATION_MODE` advanced past SHADOW into the unbuilt
`CJ2_WINNER_DRAFT` state, which does not exist in code yet. Not designed
further; Phase H itself remains out of scope for this pass, per
instruction.

**No B2/CJ-1/CJ-2/Stage-C/Fable-prompt/gate/fact_check semantic change.
No model call. No production-authority code. No push to `origin/main`.
RL-2026-002 not inspected. RL-2026-003 not touched. Phase H not started.**

---

## ORIGINAL A–M BLUEPRINT RECONCILIATION (2026-08-13, same day) — POINTER

Full doc: `.claude/original-blueprint-A-M-reconciliation-2026-08-13.md`.
**Headline finding: no literal historical A–M blueprint document exists
anywhere in this repo's git history** (exhaustive search, zero hits for
every distinctive phrase) — a genuinely different, smaller, real lettered
scheme exists (the anchor-architecture Stages 0/A–E, `review.py`) and must
not be confused with the 13-topic list this reconciliation actually
answers. Verified against live code, not assumed: G (repetition), H
(review-truncation — `_engagement_read`'s `content[:6000]` slice, confirmed
live), and I (a truncated/omitted gate.py rule silently never contributes
a FAIL, confirmed live) are the highest-priority genuinely outstanding
gaps, **all independent of B2/CJ-2/RL-2026-002 entirely** — live-pipeline
`gate.py`/`review.py`/`discovery.py` work, zero CJ dependency either
direction. K (why-we-write doctrine) is embedded live in `llm.py` and is a
direct (if undocumented) ancestor of CJ-1's own rationale; no original
article-quality problem is actually solved by CJ-2/B2/Stage-C, since CJ-2
has never produced an article. **Roadmap decision: C — run this work in
parallel with the Phase G/H sequence, not before it and not instead of
it** — no shared blocking dependency exists in either direction. Commit
`128fda8` reconfirmed unmodified, unpushed, at the end of this pass.

---

## LIVE PIPELINE INTEGRITY PASS — I/H FIXED, G SHADOW-INSTRUMENTED
## (2026-08-14, real implementation, commit `204c3bc`)

Full detail: `.claude/original-blueprint-A-M-reconciliation-2026-08-13.md`,
updated in place with resolved statuses (not rewritten — the original
2026-08-13 entries stay, marked with what changed). Summary: **I (invisible/
unevaluated gate rules) and H (review-read truncation) are DONE, real code,
tested, zero regressions** — both `gate.py`'s R1-R17 mechanical rule check
and `review.py`'s own independent R1-R19 check gained `check_truncation=True`
plus a new completeness check (a missing rule now behaves exactly like the
pre-existing `gate_llm` exception path, never silently reads as clean);
`review.py`'s `_engagement_read` now receives the whole article instead of
`content[:6000]` (no technical reason found for that limit — model context
window is far larger than any article this pipeline produces). **G
(repetition) is SHADOW-INSTRUMENTED, explicitly not promoted** — a new
deterministic paragraph-pair candidate detector, computed/persisted/
rendered exactly like this file's existing shadow checks, verified to carry
zero blocking authority; observation window opens 2026-08-14, no promotion
before 2026-08-28 at the earliest and only with real false-positive data.

**Bonus fix, found while wiring I's completeness check through:** a
pre-existing, unrelated test-harness bug in `snapshot_test.py`'s own LLM-call
mock (signature had drifted behind the real function, silently swallowing
`review.py`'s persona-cross-cite-accuracy call with zero test coverage for
as long as that call has used `check_truncation=True`) — fixed, fixtures
re-recorded, confirmed via direct before/after reproduction, not assumed.

**M re-checked, per instruction:** the originally-named blind spot (a
truncated gate rule silently reading as clean) is now closed. A second,
different, **pre-existing** (not introduced by this pass) gap was found and
explicitly NOT fixed, per the instruction not to broaden scope:
`generate.py`'s `_should_block` threshold means a *sole* `gate_llm`
degradation — even now that it correctly detects both total failure and
partial/missing-rule failure — does not by itself force
`fact_check_status: blocked`. Flagged as an open policy question, not
decided.

**87 checks across 6 test suites** (2 pre-existing regression-checked,
4 new: `gate_rule_completeness_test.py`, `gate_pre_commit_integration_test.py`,
`review_wholeness_test.py`, `repetition_shadow_test.py`) — all pass. Zero
regressions on every pre-existing generate/gate/review/CJ-shadow test
suite, including `snapshot_test.py --check`'s exact-value diff (re-recorded
twice, each time verified as a legitimate, deliberate change via direct
before/after reproduction, never assumed).

**Commit strategy note:** intended to split I/H (gate.py) from G
(review.py's new shadow check) into two commits per the task's own stated
preference, but H and G turned out to be finely interleaved within the same
file (13 hunks) alongside a shared, un-splittable snapshot-fixture file
whose correctness depends on both changes together — attempting a hunk-level
split risked leaving an intermediate commit that fails its own test suite,
which is worse than one clearly-organized combined commit. Made one commit,
with the three logical parts (I/H/G) kept clearly distinct in the message
and in the diff's own file/line boundaries.

**No B2/CJ-1/CJ-2/Stage-C/Reader-Lab/Fable-prompt-semantic change anywhere.
No model calls. RL-2026-002 not inspected. RL-2026-003 not touched. Commit
`128fda8` (Phase G.2) confirmed unmodified, unamended, unsquashed, unpushed
— `[origin/main: ahead 2]` after this pass's own new commit.**
