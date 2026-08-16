# ORIGINAL A–M ARTICLE-QUALITY BLUEPRINT — RECONCILIATION (2026-08-13)

**Status: historical + current-state reconciliation. Zero model calls. Zero
implementation changes. Commit `128fda8` (Phase G.2) unmodified, unpushed —
confirmed at the end of this pass.**

## 0. THE FINDING THIS DOCUMENT LEADS WITH — READ THIS FIRST

**Exhaustive git archaeology found no literal, lettered A-through-M
article-quality blueprint document anywhere in this repository's history.**
This is stated first, plainly, because the task that produced this document
assumed such a document exists and asked for its reconciliation — and the
honest, evidence-based answer is that the assumption itself could not be
verified. Per this project's own instruction not to "silently retrofit"
history, this document does not invent one to fill the gap.

**What was actually searched** (full detail in `## 1`): every distinctive
phrase from the task's own description ("STOP RISK," "reader drop-off,"
"fused opening," "thesis timing," "review truncation," "fail loud," "VOICE
ANCHOR," "persona territory," etc.) via `git log --all -i -S"<phrase>"`
across this repo's full 1,320-commit history — zero hits for most terms,
anywhere, ever. Every `.claude/*.md` file ever added, across all history,
was enumerated and checked by name — none is a lettered A–M list.

**What this does NOT mean:** it does not mean the concerns described in the
task are fictional or unimportant. The task's own per-letter descriptions
(persona territory, fused opening, thesis timing, correction discipline,
brevity, mechanical gates, repetition, review coverage, review truncation,
stop-risk, doctrine, testimony, fail-loud) are specific and detailed enough
that they plausibly reflect a real prior analysis — most likely one that
existed only in a conversation never committed to this git repository, or
briefly as an untracked file. **This project has real, confirmed precedent
for exactly that**: `bregman-architecture-analysis.md`/
`bregman-write-economy-analysis.md` sat untracked in the repo root for
months (per commit `808aa7b`'s own message) before being archived — proving
important design documents in this project have existed off-git before.

**What this document does instead:** treats the task's own 13 described
concerns as a **working list of real article-quality questions worth
answering**, and answers each one directly against current code — the same
work the reconciliation needed either way, just without a false claim of
having recovered a historical document that doesn't exist in this repo.
Where the task uses letters A–M, this document keeps those letters as
labels for the working list, not as citations to a verified historical
source.

**A different, real, smaller lettered scheme DOES exist and must not be
confused with this one:** the "anchor-architecture blueprint," Stages
**0/A/B/C/D/E** (tracked in `.claude/audience-engagement-tasklist.md`'s
2026-08-09 addendum, implemented in `review.py`). It concerns one narrow
mechanism — sustaining a governing anchor/refrain across an essay,
Bregman-style plan-following/seam-detection — not the 13-topic list this
document covers. Status, for completeness, not conflated with anything
below: Stage 0 DONE; Stage A DONE (validated — real anchor-recurrence rate
~10-15%, well below its own 70% kill-threshold); Stage B DONE-shipped-in-
shadow (`_plan_follow_read`); Stage C DONE-shipped-in-shadow
(`_check_seam_shadow`, explicitly not promotable "before 2026-08-23... only
with real false-positive data in hand"); Stage D/E NOT STARTED, deliberately,
pending real calibration volume.

---

## 1. ARCHAEOLOGY METHOD AND RESULT

Searched (all zero hits unless noted): `"STOP RISK"`/`"stop_risk"`/
`"stop-risk"`, `"reader drop-off"`/`"dropoff"`, `"fused opening"`,
`"thesis timing"`, `"review truncation"`, `"12k truncation"`, `"fail loud"`
(hits exist but are unrelated — Reader Lab/Phase 1.6 commit messages, not
this scheme). **Two terms DO have real history, but only inside an
unlettered audit doc, not an A–M list:** `"VOICE ANCHOR"` and `"persona
territory"` both appear in `.claude/persona-architecture-audit.md` (Phase
1.5A, audit-only, no lettered structure). Every `.claude/*.md` file ever
`git add`ed across all history was enumerated via `git log --all
--diff-filter=A --name-only` — none matches a lettered A–M scheme.

Real, substantial work exists addressing similar themes, under different
organizational names, cited throughout `## 2` below: `persona-architecture-
audit.md` (Phase 1.5A), `experiments/why-we-write-2026-08-10.md` (Phase 1),
`experiments/fable-review-roi-2026-08-10.md` (Phase 1.5B),
`experiments/phase-1.6-source-grounding-2026-08-11.md` (Phase 1.6),
`bregman-architecture-analysis.md`/`bregman-write-economy-analysis.md`
(rule-27 protected shapes, archived commit `808aa7b`, 2026-08-07). GoatCounter
scroll-depth tracking (25/50/75/100%, `audience-engagement-tasklist.md` item
1) is the closest real analogue to a reader-attrition metric — live,
collecting real data, but explicitly never wired into any generation
decision, and never framed as a lettered task.

---

## 2. THE WORKING LIST — CURRENT STATE, VERIFIED AGAINST LIVE CODE

Every row below was checked directly against `automation/orchestrator/*.py`
(personas.py, generate.py, llm.py, gate.py, review.py, fact_check.py,
discovery.py, grounding.py, config.py) — not inferred from a tasklist
checkbox, per the task's own instruction.

### A — Persona territory / voice anchor
**Concern:** should each of the 4 personas have a distinct perceptual
domain, and should one be prohibited from writing in another's mode?
**Current state:** `personas.py` — **PROMPT-ONLY, explicitly soft by
design.** Siri Sage's own text states the policy directly: *"aren't
off-limits to you by rule... a difference in perceptual instrument, not an
assigned territory."* No code-level routing/exclusion exists anywhere; no
gate/review check verifies a persona "stayed in territory."
**Classification: DONE BUT EVOLVED.** The evidence reads as a deliberate
shift away from hard boundaries toward soft, described affinities — not
neglect. Caveat: without a confirmed original success criterion, this
reads as evolution rather than abandonment, but that inference rests on
`personas.py`'s own framing, not a recovered original spec.

### B — Author presence / fused opening
**Concern:** the writer should be perceptible early via embodied
observation, without a formulaic "As a disabled person, I..." opening, and
without the opening being fundamentally autobiographical.
**Current state:** `generate.py` bans a fixed "house opening"/
throat-clearing and offers 5 valid opening shapes; `llm.py` requires the
opening "earn its shape via the persona's embodied experience." No rule
specifically bans "As a disabled person, I..." Nothing in `gate.py`/
`review.py` checks any of this. **PROMPT-ONLY, unenforced.**
**Classification: PARTIALLY DONE** (real, specific prompt language exists;
zero verification).

### C — Thesis / question timing
**Concern:** reader should grasp the central question early without a
mechanical thesis-statement opening.
**Current state:** `llm.py`: *"BRIEF A QUESTION, NOT A VERDICT... hand them
something they do not know the answer to."* `generate.py`: *"If you write
'My thesis is'... delete it"*; explicit "INVESTIGATIVE STANCE" instruction.
Strong, specific, repeated prompt language — **zero gate/review rule scans
for a stated-thesis pattern in the published text.**
**Classification: PARTIALLY DONE** (well-specified intent, unenforced).

### D — Correction discipline
**Concern:** a correction should deepen/reinterpret rather than invalidate;
a withdrawn example should not silently reappear, uncorrected, later.
**Current state:** `llm.py`'s `correction_moment` — the FACTUAL half is
real and deterministic (`source_excerpt` must verbatim-match the source;
unverifiable content is force-rejected). But the field's own definition is
framed as proving the reader wrong/stopping/correcting them — closer to
refutation than "deepen." **No language requires the deepen-not-invalidate
shape, and no check anywhere cross-references whether a corrected claim
resurfaces uncorrected in the conclusion.**
**Classification: PARTIALLY DONE** — factual-grounding half enforced;
editorial-shape half and conclusion-reappearance check both **absent**.

### E — Brevity / length architecture
**Concern:** historical 1600/2200/2800-word bloat problem; is longform
deliberate or emergent?
**Current state — the old bloat problem is genuinely resolved, differently
than the task assumed.** `config.py`'s `_LENGTHS` is a deliberate weighted-
random pool — `450(.08) / 700(.15) / 950(.27) / 1200(.24) / 1600(.16) /
2800(.10)` — explicitly commented as intentional ("2800 fires roughly once
every 10 days... matches 'let one piece a week run long'"). **The old 2200
bucket is gone.** Hard, deterministic, code-enforced ceilings exist ONLY
for two article types: `field_note` (≤500 words, checked) and
`portrait`/`series_part` (≥1200 words, checked), in `gate.py`. **The
dominant type, `"essay"` (35% weight), has zero deterministic post-hoc
length check** — `generate.py`'s "arrive early rather than late" instruction
is prompt-only, never verified.
**Classification: split — DONE BUT EVOLVED** for length *selection*
(genuinely solved, real engineering, old bloat buckets removed);
**STILL OUTSTANDING** for essay-type length *adherence* (no ceiling
enforcement for the majority of articles).

### F — Mechanical gate calibration
**Concern:** deterministic thresholds (e.g. a ~60-word sentence cap) vs.
model-owned judgment calls.
**Current state:** `gate.py` runs real deterministic checks —
`_readability_score` (Flesch-Kincaid, hard-fails <55), article-type word
counts, buried-clause regex, argument-word overuse, and a genuinely
sophisticated `_check_sentence_length_distribution` (stdev/mean-based, not
a single-sentence cap) against a real corpus baseline. **No 60-word
deterministic sentence cap exists anywhere.** R1–R15 (the LLM-judged rule
set) include R11 "LONG SENTENCE" — but at a **30-word** threshold, and
judged by the LLM, not counted in code.
**Classification: DONE BUT EVOLVED.** A single crude length cap appears to
have been replaced by a more sophisticated distributional check — a real
improvement, though R11's un-reconciled 30-word LLM-judged rule sitting
alongside it is a loose end, not a contradiction that blocks calling this
resolved.

### G — Repetition / restated claim
**Concern:** repeated thesis/examples across paragraphs; distinguish flaw
from deliberate refrain.
**Original state (2026-08-13):** only a narrow prompt-level ban on
restating the thesis in the ending, enforced through an LLM rewrite pass,
not a deterministic check; `_check_seam_shadow` detects *announcing* a
callback, not repeating one; no general mid-article repetition checker
existed.
**RESOLVED, 2026-08-14 (live pipeline integrity pass, commit `204c3bc`):**
new `_check_repetition_shadow` (review.py) — a deterministic, stdlib-only
candidate detector: paragraph-pair content-word Jaccard overlap
(stopword-filtered, minimum-content-word floor, intro/conclusion pair
exempted by design). Computed, persisted (new `shadow_repetition_hits`
column, `engagement.db`), and rendered in the review sidecar, exactly like
this file's other shadow checks — verified structurally that it can never
enter `is_clean`'s computation. **Classification: SHADOW-DESIGNED, NOT
DONE** — this is deliberately not a completion, it is the instrument this
concern needed to start gathering real evidence with, matching every
other shadow check's own "do not promote before a real observation window
and documented false-positive data" discipline (same 2-week-minimum
convention, here 2026-08-28). 7 tests pass (`repetition_shadow_test.py`).

### H — Editorial review coverage / wholeness
**Concern:** does review see the whole article, or a truncated slice?
**Original state (2026-08-13) — a real, confirmed live gap.**
`_engagement_read` ("would a reader finish this") truncated to
`content[:6000]` — for any article longer than that, the ending was never
read by this check. GATE_SYSTEM/RULES_SYSTEM truncation was flagged
unverified.
**RESOLVED, 2026-08-14 (commit `204c3bc`):** follow-up verification done —
`gate.py`'s GATE_SYSTEM call and `review.py`'s RULES_SYSTEM call both
already send the FULL article (`user_prompt=content`, no slice); only
`_engagement_read` truncated, and only `_plan_follow_read`'s own
`content[:20000]` limit exists elsewhere, comfortably above the longest
real article tier (~16,000 chars) and left unchanged. No technical
justification found for the 6000-char limit — the model's context window
is far larger than any article this pipeline produces. Truncation removed;
`_engagement_read` now receives the whole article, plus
`check_truncation=True` for defense in depth. **Classification: DONE.**
11 tests pass (`review_wholeness_test.py`), including a structural
regression fixture proving a marker placed past the old 6000-char boundary
is now actually sent, and would not have been under the old code.

### I — Review truncation / invisible rules
**Concern:** distinguish "rule passed" from "rule never evaluated" from
"output truncated."
**Original state (2026-08-13) — confirmed unresolved, a real live risk.**
A rule that never appeared at all in the raw LLM output (truncated/
incomplete response) was simply absent from the verdicts dict — absence
never contributed a FAIL. No "N rules expected, M found" assertion existed
anywhere.
**RESOLVED, 2026-08-14 (commit `204c3bc`):** two-layer fix, both call
sites — `gate.py`'s GATE_SYSTEM (R1-R17) and `review.py`'s own,
independently-numbered RULES_SYSTEM (R1-R19, found while auditing H —
the exact same vulnerability existed in a second file, undiscovered until
now). Layer 1: `check_truncation=True` added to both (reuses `llm.py`'s
existing 2026-08-10 truncation-detection mechanism — a response cut off by
the API's own `finish_reason` now raises, caught by the pre-existing
`except Exception` path). Layer 2: new `_missing_rule_ids` completeness
check — catches every OTHER way a rule can go silently missing (no
API-reported truncation, just an omitted or malformed line); a gap now
treated identically to the pre-existing `gate_llm` exception path
(`gate_llm_ok=False`, `_degraded_stages.append("gate_llm")` for gate.py;
an explicit `RULE_CHECK_INCOMPLETE` entry forcing `is_clean=False` for
review.py's own advisory report). **Classification: DONE.** 27 tests pass
across two suites (`gate_rule_completeness_test.py`,
`gate_pre_commit_integration_test.py`), covering every matrix item the
original task specified (all-present, one FAIL, one absent, truncated
tail, malformed block, duplicate rule, unknown extra rule, whitespace
variation, zero parsed rules) plus the load-bearing assertion: missing/
invalid expected rules can never yield a clean report.

**Bonus finding, same pass:** fixing this also exposed and fixed a
pre-existing, unrelated test-harness bug — `snapshot_test.py`'s own
`_call_openai_compat_api` mock had silently drifted behind the real
function's signature (missing `check_truncation`/`temperature`), meaning
`review.py`'s persona-cross-cite-accuracy check (which already used
`check_truncation=True` in production, unrelated to this pass) had **zero
real test coverage** — its own `except Exception` was silently absorbing
a bare `TypeError` from the stale mock every time the test suite ran, for
as long as that call has existed. Fixed; snapshot fixtures re-recorded to
reflect the now-genuinely-exercised call.

### J — STOP risk / reader drop-off
**Concern:** a reader-attrition metric, possibly shadow-only, possibly
abandoned.
**Current state:** **zero grep hits anywhere in `automation/` for
stop_risk, drop-off, or attrition.** This is not an abandoned partial
build — there is no trace of it ever existing in code. The real analogue
(GoatCounter scroll-depth, `## 1`) is a different mechanism, never framed
this way, never wired into generation.
**Classification: STILL OUTSTANDING (never built)** — distinct from
"built then abandoned," which the evidence does not support.

### K — Why we write (doctrine)
**Concern:** disability as instrument (a way of perceiving that reveals
the hidden mechanism of the subject), not disability as the default topic.
**Current state:** `llm.py` — *"a way of knowing that can reveal something
the dominant world has failed to notice... find that contribution in the
subject"* and *"not about disability as a topic"* — real, live, in the
production system prompt today. Phrased slightly narrower than "reveal the
hidden mechanism of the thing itself," but the same spirit, not a
different doctrine.
**Classification: DONE** — genuinely embedded in the live prompt, not
aspirational-only. (Its relationship to CJ-1/CJ-2 is addressed separately
in `## 4`.)

### L — Human testimony / source architecture
**Concern (task's own L1/L2 split):** L1 — use/hoist testimony already in
a fetched source; L2 — actively retrieve companion first-person sources.
**Current state:** `discovery.py`'s `fetch_source_article`/`get_source_text`
fetch exactly the one already-identified source. **No companion-source
search, no first-person-testimony-specific retrieval, no weighting favoring
human testimony over other text anywhere.** Grounding's "testimony"-adjacent
logic validates quotes already present in a draft — it does not find more.
**Classification: PARTIALLY DONE** — L1 exists (passive use); **L2 is
absent**, exactly the distinction the task itself warned against
collapsing.

### M — Fail loud / machinery failure
**Concern:** can a stage fail while production shows a false PASS?
**Current state:** `_degraded_stages` (`production_orchestrator.py`,
`generate.py`, `gate.py`) genuinely blocks — `fable_brief` failing, or 2+
stages failing, forces `fact_check_status: blocked` into the article's own
frontmatter — for the **authoritative live pipeline only.** Phase G.2 (this
session, commit `128fda8`) deliberately keeps CJ-2 shadow failures OUT of
this mechanism, correctly, since shadow is non-authoritative.

**RE-CHECKED, 2026-08-14, after I/H fixed (commit `204c3bc`), per
instruction 8:** the specific blind spot named above — a truncated/
missing gate rule silently registering as a clean pass — **is now
closed**, confirmed directly: `gate_llm_ok=False` fires identically
whether the LLM call raises outright or simply omits an expected rule,
and both routes append `"gate_llm"` to `_degraded_stages` the same way.
**Classification: DONE**, the originally-named blind spot is closed.

**A second, different, NOT-the-same-class gap found during this
re-check, reported per instruction 8 rather than silently fixed (scope:
this pass was I/H/G only):** `generate.py`'s own blocking threshold —
`_should_block = "fable_brief" in _stages or len(_stages) >= 2` — means
`_degraded_stages == ["gate_llm"]` **alone** does not force
`fact_check_status: blocked`. This was already true before this pass (not
introduced by it) and is a genuinely different problem from I's own
missing-rule class: it's about the *combination threshold* two or more
degraded stages must cross, not about whether a single stage's own
failure is correctly detected. Concretely: a complete gate-LLM outage, or
now a fully-missing rule set, is correctly logged as `gate_llm` and
correctly makes the log say "INCOMPLETE" not "PASS" — but if it's the
*only* thing that went wrong that run, the article still ships
unblocked, on the reasoning (documented in `production_orchestrator.py`'s
own `__init__`) that `fable_brief` alone is uniquely disqualifying and
anything else needs a second failure to matter. Whether that threshold
is still the right call now that gate.py's own rule check has a real,
confirmed history of both totally failing and partially failing is a
genuine open question, **flagged here, not decided or fixed this pass.**

---

## 3. IS THIS EXHAUSTIVE — ANY LETTER AFTER M?

**No basis to confirm or deny.** Since no enclosing A–M document was found
at all (`## 1`), there is no historical list whose end could be verified.
This document covers exactly the 13 concerns the reconciliation task
itself described (A–M) and no more, honestly bounded by what was actually
asked, not by a recovered original scope.

---

## 4. RELATIONSHIP TO CJ-1 / CJ-2 / B2

| Letter | Relationship | Basis |
|---|---|---|
| A | **PARTIAL ANCESTOR** | A's own evolution (soft "perceptual instrument, not territory") is thematically continuous with CJ-2's engine-capsule design (4 distinct, anonymized analytical instruments) — not a mechanistic descent, but the same underlying idea, formalized differently, in a different system. |
| B | NO RELATION | CJ-2 never touches prose/openings at all. |
| C | **PARTIAL ANCESTOR** | Thematic only: CJ-1's `open_question` field and Fable's "brief a question, not a verdict" doctrine share a lineage, but CJ never governs article-level thesis-timing prose — this is candidate-selection language, not article language. Do not read this as "solved by CJ." |
| D | NO RELATION | Repair-v1 repairs R2 support *labels*, a deterministic classification fix — unrelated to article-prose editorial correction shape. |
| E | NO RELATION | |
| F | NO RELATION | |
| G | NO RELATION | |
| H | NO RELATION | CJ's own R1/R2 validators check structured claims, not "did the reviewer see the whole article" — a different failure surface entirely. |
| I | NO RELATION | |
| J | NO RELATION | |
| K | **DIRECT ANCESTOR** | No explicit written link was found anywhere (a real documentation gap, confirmed by direct search) — but the *substance* is a direct descent: CJ-1's whole friction-gate rationale (finding a genuine disability-lens contribution, not surface "disability is affected by X") IS K's doctrine, formalized into a validity gate with a resolver-verified evidence requirement. |
| L | **PARTIAL ANCESTOR (L1 only)** | CJ-1's `source_anchors` resolver-verification is a materially stronger version of L1's "make sure testimony/quotes are real" — but CJ never attempts L2's active retrieval of companion sources. Do not credit CJ with solving L. |
| M | NO RELATION (parallel evolution) | B2's own fail-closed admission-gate discipline (`RESOLVED_STATUSES`/`is_resolved_anchor`) applies the identical "fail loud, never silently degrade" principle to a completely different pipeline — independently arrived at, not descended from M. |

**No original article-level problem is "solved" by CJ architecture** —
this reconciliation found zero cases where CJ-2/B2/Stage-C actually closed
an article-quality gap, because CJ-2 has never produced an article (per
Phase G's own finding). Every DIRECT/PARTIAL ANCESTOR relationship above is
about shared **doctrine or candidate-selection philosophy**, never about
CJ solving a final-prose problem.

---

## 5. FORGOTTEN WORK — RANKED, EVIDENCE-BASED

Ranked by confirmed effect on published-article quality, frequency, current
protection, and cost — not by assumption:

1. **G — repetition** (STILL OUTSTANDING, no general mechanism). Affects
   every article; zero current protection beyond a narrow ending-thesis
   ban.
2. **I — invisible/truncated rule checks** (STILL OUTSTANDING, confirmed).
   A live, currently-real silent-failure mode inside `gate.py`'s own
   authoritative check — undermines confidence in every gate pass, not
   just some.
3. **H — review-truncation gap** (STILL OUTSTANDING, confirmed, one
   concrete instance found: `_engagement_read`'s `content[:6000]`).
   Affects specifically longer articles' endings.
4. **L2 — active testimony retrieval** (absent). Real but lower urgency —
   affects depth/richness, not correctness; meaningfully higher
   implementation cost (new retrieval infrastructure, not a check).
5. **E — essay-type length adherence** (no ceiling check for the dominant
   type). Real gap, but the deliberate length-*selection* architecture
   already constrains the worst-case distribution somewhat; adherence
   enforcement is a good, moderate-cost addition, not an emergency.
6. **D — correction editorial shape + conclusion-reappearance check**
   (absent). Real but narrower frequency — only articles containing a
   `correction_moment` are exposed.
7. **J — STOP risk** (never built). Lowest priority: no incident evidence
   this is currently causing measurable harm (untested hypothesis, not a
   confirmed gap); requires new instrumentation plus a study phase before
   it could even inform anything.
8. **A/B/C — persona-territory/opening-formula/thesis-timing enforcement**
   (all real, all prompt-only). Ranked lowest not because they don't
   matter, but because no incident/frequency data exists either way —
   flagged as **unmeasured**, not confirmed low-priority. A future pass
   should measure before re-ranking these, not assume they're fine.

---

## 6. RECONCILIATION WITH THE CURRENT MASTER ROADMAP

Cross-referenced against `.claude/master-roadmap-2026-08-13.md` and
`.claude/experiments/final-evaluation-freeze-protocol-2026-08-13.md`.

| Item | Placement | Why |
|---|---|---|
| G (repetition) | **PARALLEL TO CJ-2 CALIBRATION** | Pure live-pipeline engineering; has zero dependency on RL-2026-002/B2 freeze status. |
| I (invisible rules) | **PARALLEL TO CJ-2 CALIBRATION** | Same — a `gate.py`-internal fix, no CJ dependency. Arguably urgent given it undermines gate.py's own authoritative-check integrity. |
| H (review truncation) | **PARALLEL TO CJ-2 CALIBRATION** | Same reasoning; needs the one follow-up verification flagged in `## 2` before scoping a fix. |
| L2 (active testimony retrieval) | **PARALLEL TO CJ-2 CALIBRATION**, but lower urgency | Independent of CJ; larger build, can run alongside RL-2026-002 without conflict. |
| E (essay length adherence) | **PARALLEL TO CJ-2 CALIBRATION** | Independent of CJ; a `gate.py` addition. |
| D (correction shape) | **PART OF ARTICLE-LEVEL VALIDATION** (Phase H, master roadmap) | Actually the SAME kind of question Phase H already exists to eventually answer for CJ-2-sourced drafts — worth folding into that future validation design rather than a separate one-off fix, since both ask "does the article do the editorial thing it's supposed to do." |
| J (STOP risk) | **DEFER / NO CURRENT EVIDENCE** | No incident data justifies building this now; revisit if/when real engagement data (GoatCounter) suggests a specific failure pattern worth instrumenting for. |
| A/B/C (persona territory/opening/thesis enforcement) | **DEFER / NO CURRENT EVIDENCE**, pending measurement | Same reasoning as `## 5`'s ranking — measure first. |

**Critically: none of this is BEFORE CJ-2 FREEZE or AFTER CJ-2 FREEZE —
every genuinely outstanding item (G/H/I/L2/E) is independent of B2's
semantic freeze gate entirely.** They touch the live pipeline's OWN
gate.py/review.py/discovery.py, none of which the freeze protocol governs.
**RL-2026-002 is not a blocker for any of them** — confirmed directly, not
assumed, per the task's own instruction not to let it become one.

---

## 7. CHALLENGING THE CURRENT "NEXT STEP"

The roadmap was heading toward observability → article-pilot protocol →
production-integration readiness (Phase H) for the CJ-2 bridge specifically.
**Decision: C — run original blueprint items in parallel with G/H, not
before and not instead.**

Not **A** (continue unchanged) — G/I/H are real, confirmed, currently-live
gaps in the pipeline that publishes real articles every day, right now,
independent of CJ-2 entirely; ignoring them because attention is on CJ-2
integration has no technical justification. Not **B** (insert before Phase
H) — none of G/I/H/L2/E gate or depend on Phase H's design, so sequencing
them strictly *before* it would be an artificial dependency, not a real
one. Not **D** (replan a material portion) — the CJ-2 roadmap itself
(Phases A–J, `master-roadmap-2026-08-13.md`) remains correct and
unaffected; nothing found here contradicts or invalidates it. **C** is
justified specifically because these are independent workstreams touching
different code (live-pipeline gate/review internals vs. the CJ-2 bridge/
research track) with no shared blocking dependency in either direction.

---

## 8. FINAL REPORT

**ORIGINAL BLUEPRINT:** no verified historical A–M document exists in this
repository's git history, despite exhaustive search (`## 1`). Treated
instead as a working list of 13 real concerns, answered directly against
current code (`## 2`).

**IMPLEMENTATION ORDER:** not recoverable — no historical dependency
structure exists to recover, for the same reason. The *unrelated*
anchor-architecture Stage 0–E scheme's own order (0→A→B→C→D→E, sequential,
each gated on real calibration volume before advancing) is real but
governs a different, narrower mechanism (`## 0`).

**A–M STATUS** (updated 2026-08-14, commit `204c3bc`), one line each: A
DONE BUT EVOLVED · B PARTIALLY DONE · C PARTIALLY DONE · D PARTIALLY DONE ·
E split (selection DONE BUT EVOLVED / essay-adherence STILL OUTSTANDING) ·
F DONE BUT EVOLVED · **G SHADOW-DESIGNED, NOT DONE (was STILL OUTSTANDING —
deterministic candidate detector now live, shadow-only, no blocking
authority)** · **H DONE (was STILL OUTSTANDING — `_engagement_read` now
receives the whole article)** · **I DONE (was STILL OUTSTANDING —
completeness check closes the invisible-rule gap in both gate.py and
review.py)** · J STILL OUTSTANDING (never built) · K DONE · L PARTIALLY
DONE (L1 only) · **M DONE, originally-named blind spot now closed; a
second, different, unfixed threshold-logic gap found and reported (`## M`
above)**.

**DONE/EVOLVED:** A, E's length-selection half, F, K, **H, I (newly
closed)** — genuinely closed, verified against live code and tests, not
tasklist-inferred.

**SHADOW-DESIGNED, NOT DONE:** **G** — real code, real tests, zero
blocking authority, explicitly gathering evidence before any promotion
decision.

**STILL OUTSTANDING:** J, E's essay-adherence half, L's L2 half, and the
newly-found `_should_block` single-stage-degradation threshold question
(`## M`) — real, confirmed, currently live gaps with zero-to-partial
protection.

**CJ RELATIONSHIP:** K is a direct ancestor of CJ-1's whole rationale
(undocumented link, real substance). A, C, L are partial/thematic
ancestors only. **No original article-quality problem is actually solved
by CJ-2/B2/Stage-C** — CJ has never produced an article.

**FORGOTTEN WORK, updated priority (I and H now closed, G now
shadow-instrumented):** the `_should_block` threshold question (`## M`,
newly found) > L2 (active testimony) > E (essay adherence) > D
(correction shape) > J (STOP risk) > A/B/C (unmeasured) > G (already has
its instrument; now genuinely waiting on real observation data, not
neglect).

**ROADMAP IMPACT: C — run in parallel with G/H, not before, not instead**
(unchanged conclusion; G/H/I's own resolution this pass confirms, rather
than revises, that these were always independent of B2/CJ-2 and never
should have waited).

**NEXT ACTION, updated 2026-08-14, while RL-2026-002 continues
asynchronously:** G/I/H are now closed (commit `204c3bc`). Remaining
zero-CJ-dependency live-pipeline work, in priority order: (1) decide
whether `generate.py`'s `_should_block` threshold should treat a
sole `gate_llm` degradation as blocking on its own, now that both a
total-failure and a partial/missing-rule failure are correctly detected
(`## M`'s newly-found gap) — a policy decision, not a code question; (2)
begin the 2026-08-28 observation window for G's new shadow detector,
collecting real false-positive data before any promotion decision; (3)
L2 (active companion-testimony retrieval) and E (essay-type length
adherence) as the next real engineering items, per `## 5`'s ranking.

**G.2 CONFIRMED UNCHANGED:** `128fda8` remains in `main`'s history,
unmodified, unamended, unsquashed — `git branch -vv` confirms
`[origin/main: ahead 2]` (this pass's own commit `204c3bc` sits cleanly on
top of it) — not pushed. Nothing in this pass modified, amended, or
pushed it.
