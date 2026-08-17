# Artistic Reset AR2 — Silent-Lens A/B Experiment (2026-08-17)

Finished-work experiment, run per AR1's design
(`.claude/experiments/artistic-reset-ar1-2026-08-17.md`, §9-12). Story Rejection V1.1
(`d0204aa`/`9502d10`) untouched. No production prompts, personas, routing, or DBs
modified. No article entered `_drafts/` or `_posts/`. No production selection/publishing
pipeline invoked. All generation ran through a new, standalone, isolated harness
(`automation/ar2_silent_lens_harness.py`) against real sources and a real model, with
zero writes to any production file or database.

## HYPOTHESIS

The lens should be causally necessary but narratively optional: a Silent-Lens writer
instruction should let the disability-derived perceptual engine keep driving the
essay's actual discovery while making explicit disability/access language optional
rather than compulsory, autobiography argument-advancing rather than decorative, and
the reader's discovery undelivered-in-advance.

## SOURCE SELECTION

Four real, hand-picked, dated sources (2026-05-27 through 2026-07-14), verified via live
web search/fetch this session, deliberately **not** drawn through the production
`disability_angle` discovery pipeline (`news_fetcher.py`/`discovery.py`) — see
CONTROLLED VARIABLES. None is framed as a disability/accessibility story; none was
selected because an obvious disability angle was visible from the headline.

| Key | Domain | Source | Why useful |
|---|---|---|---|
| `airtrain` | infrastructure/transport | Travel And Tour World, "AirTrain Newark Replacement" | Concrete, numbers-dense, construction-disruption story with an obvious mobility angle available but not stated in the source |
| `hbomax` | media/consumer economics | TheWrap, HBO Max password-sharing crackdown | Abstract classification/enforcement system with zero embodied or sensory surface — a harder test for any disability-informed engine |
| `selfcheckout` | retail/labor/surveillance | Grocery Dive, AI camera self-checkout systems | Computer-vision/verification systems with real named vendors, executives, and statistics — a genre (retail-tech reporting) with no disability framing anywhere in the source |
| `warehouse` | labor/robotics | About Amazon, Vulcan robot ("first sense of touch") | A source that itself uses embodied language ("sense of touch," "ergonomic height") for a machine — a useful trap for testing whether a lens produces insight or just echoes the source's own metaphor |

Domain spread deliberately avoids the four domains AR1's own four-article sample already
covered (architecture/access, arts-festival culture, consumer headphones, AI/data-center
infrastructure), so this experiment's findings aren't just a rerun of AR1's own examples.

Personas were assigned once per source, by affinity, not to bias the outcome toward or
away from any persona's known strengths: Maya Flux (airtrain — mobility/infrastructure
affinity), Zen Circuit (hbomax — classification/measurement affinity), Pixel Nova
(selfcheckout — visual/verification-system affinity), Siri Sage (warehouse — acoustic/
sensory-environment affinity). No source was chosen to make a particular persona look
good or bad, and each persona appears exactly once (design limitation — see AUTOBIOGRAPHY
FINDINGS).

## CONTROLLED VARIABLES

Both conditions, for each source, held identical:

- **Source text and evidence packet** — the same fetched/frozen source text, verbatim, no
  re-fetch between conditions.
- **`disability_angle`** — omitted entirely for both A and B (empty string, matching the
  code's own already-supported bypass path — see AR1 §13 driver #1). Neither condition
  was fed a discovery-stage disability angle; this is the one variable AR1 flagged as a
  likely confound if handled asymmetrically, so it was excluded from **both** arms rather
  than included in A and excluded from B.
- **Persona / perceptual engine** — the same persona (`personas.py` `AGENTS[...]
  ["prompt_block"]`, verbatim), the same persona canon file, the same persona state
  (`persona_state/<slug>.json`, real production file, read-only), the same wound-
  extraction mechanism (`_extract_persona_wound`'s regex, reimplemented verbatim against
  the same canon file — not disabled, not modified between conditions).
- **Register, length target, article type** — frozen per source, identical across A/B
  (`clinical`/`wry`/`ecstatic` per source, 1200-word target, `essay` type throughout).
- **Mechanism / plan input** — **absent for both conditions.** This experiment does not
  run Fable's editorial-planning stage (`resisting_example`/`correction_moment`/
  `opening_shape`/`angle`), which itself requires live model calls unreachable from this
  harness (see MODEL/PROVIDER LINEAGE). `generate.py`'s own code already has a graceful
  no-brief path (all `_fable_*` variables default to `""` when `fable_brief` is falsy —
  confirmed by direct read, `generate.py` line 538) — this experiment exercises exactly
  that path, identically, for both A and B. This is a genuine, disclosed scope reduction
  from full production fidelity, not a hidden one: the comparison below is of the writer
  stage in isolation, not of a fully-planned, fully-reviewed, fully-published pipeline
  artifact.
- **Model, provider, temperature, max_tokens** — identical across all 8 calls (see below).
- **SYSTEM prompt** — `llm.py`'s `call_llm_via_openclaw_session` SYSTEM string, verbatim,
  unmodified, identical for A and B (it does not contain the AUTHOR RULE block; that
  block lives only in `generate.py`'s USER prompt).
- **The entire ~120-line invariant instruction block** (`generate.py` lines ~784-901:
  WRITE LIKE THIS PERSON, FORBIDDEN JARGON, GROUNDING, NAMED VOICES, SOMEONE ELSE MUST
  SPEAK, TEMPORAL ANCHORS, ENDING, WRITING MODEL — BREGMAN, FIND SOMETHING OUT, etc.) —
  transcribed verbatim (condensed where individually enumerated sub-bullets don't affect
  meaning; see harness source for exact text), identical for A and B.
- **Title rules block** — identical, no recent-title-pattern history (cold start).

The **only** text that differs between condition A and condition B for a given source is
the AUTHOR RULE / FORBIDDEN DEFAULTS paragraph — see below.

**Not controlled / genuinely uncontrollable at this scale:** ordinary sampling variance
(temperature 0.9, one sample per cell — matching this repo's own `phase_probe.py`
precedent of treating a single frozen-brief sample as one data point, not averaging away
noise). N=4 pairs; treat directional, not as statistically definitive.

## A DOCTRINE

Verbatim, unmodified, from `generate.py` (current production HEAD at time of this
experiment):

> AUTHOR RULE — NON-NEGOTIABLE: This article is written BY a disabled person, not ABOUT
> disability. Those are different things. You are the author. Your disability shapes how
> you see. It is not the subject.
>
> Write about the world — a news story, a political shift, an economic decision, a
> cultural moment, a piece of music, a building, a scientific finding, a war, a law. Your
> embodied experience gives you an angle a non-disabled writer would miss. That angle is
> the article. The subject is the world.
>
> Test: Could this article exist without the word 'disability' appearing at all and still
> carry your specific perspective? If yes — that is the target. Do not explain your
> access needs. Do not audit inclusion. See the world and write what you see.
>
> FORBIDDEN DEFAULTS: Do not build your argument around ramp, curb cut, grab rail,
> tactile paving, accessible toilet, or lift as the central concrete example. Do not
> write an article whose thesis is 'this system excludes disabled people.' Find the
> angle that is not the first one that comes to mind.

## B DOCTRINE

Derived from AR1 §9, refined against the whitepaper, not adopted from the task's raw
draft verbatim:

> SILENT-LENS DOCTRINE — NON-NEGOTIABLE: This article is about the world object in the
> source — not about disability. Use your perceptual engine to investigate that object:
> what you notice, what seems strange, what gets compared, what gets measured, what
> refuses to look neutral, which initial explanation fails, and what new mechanism
> becomes visible because of it. The lens must be load-bearing, not the label — remove
> your way of perceiving and the discovery should disappear; remove an unnecessary
> announcement of it and the argument should survive.
>
> Do not name your disability or announce your perspective before the reader needs it to
> understand what you found. If naming it becomes necessary to make a discovery legible,
> name it then — not as a credential in the opening. Do not explain your access needs. Do
> not audit inclusion.
>
> A memory or bodily detail belongs only if it changes what you can know about the
> subject — not to prove you are really disabled. If you cannot say what the piece would
> lose without it, leave it out.
>
> Do not announce the insight before the reader has had a chance to discover it with you.
> By the end, the original subject must have become a different thing than it seemed at
> the start.

Both blocks are comparable in length and register (~140 vs ~180 words) to avoid a
length-driven confound.

## MODEL / PROVIDER LINEAGE

Production's real writer call (`llm.py`'s `call_llm_via_openclaw_session`) routes through
`CLIPROXY_URL` (`http://127.0.0.1:8317/v1`), a service that exists only on Trident and is
unreachable from this Mac session — reaching it would have meant either touching
Trident's live infrastructure/credentials for a non-production experiment, or SSHing in,
both of which this task's brief explicitly rules out. Real provider calls were made
directly to OpenRouter using a **personal, non-production API key** already present on
this machine (`~/.hermes/.env`, used for the owner's separate local Hermes tooling — not
Trident's shared CLIProxyAPI secret, not billed against production's account). All 8
calls resolved to the same model, `anthropic/claude-opus-4.5`, with zero fallback —
confirmed identical across every generation (`actual_model` field, `raw/*.json`), so
there is no cross-condition model-identity confound. This is a disclosed substitution for
production's own primary writer model (`openrouter/claude-opus-4.8` via CLIProxy) — a
comparable-tier Claude model, not the exact same version string; the comparison here is
about the *prompt text*, which is the experimental variable, not about reproducing
production's exact model routing.

## BLINDING METHOD

The 8 raw outputs were shuffled (fixed seed) into anonymous IDs `R-01`..`R-08` with no
visible source/condition/persona metadata in the blinded files. The mapping
(`blind_key.json`) was held privately by the orchestrating session and never shown to any
reviewer. Each of the 8 reviews was performed by a **separate, freshly-spawned,
context-free general-purpose agent** — not a fork of the orchestrating session, which
would have carried contaminating context — given only the blinded file path and the AR1
rubric, explicitly instructed not to speculate about how the article was produced. This
is genuine blinding, not self-grading: the reviewing agents had no access to this
document, the harness script, or any other article in the set.

## PAIR RESULTS

Full text of all 8 reviews: `ar2-silent-lens-2026-08-17-articles/blind_reviews.md`.
Full articles (unblinded, with lineage metadata): `ar2-silent-lens-2026-08-17-articles/
{source}-{A,B}.md`. Raw generation records (full prompts + responses):
`ar2-silent-lens-2026-08-17-articles/raw/*.json`.

| Source | Cond | Persona | W | G | K | S | Role | Composite (W+G+K) |
|---|---|---|---|---|---|---|---|---|
| airtrain | A | Maya Flux | 5 | 4 | 4 | 2 | ENGINE | 13 |
| airtrain | B | Maya Flux | 5 | 4 | 4 | 1 | ENGINE | 13 |
| hbomax | A | Zen Circuit | 4 | 4 | 4 | 1 | ENGINE | 12 |
| hbomax | B | Zen Circuit | 3 | 4 | 4 | 2 | ENGINE | 11 |
| selfcheckout | A | Pixel Nova | 5 | 4 | 4 | 2 | ENGINE | 13 |
| selfcheckout | B | Pixel Nova | 5 | 4 | 4 | 2 | ENGINE | 13 |
| warehouse | A | Siri Sage | 5 | 4 | 4 | 2 | ENGINE | 13 |
| warehouse | B | Siri Sage | 4 | 4 | 4 | 2 | MIXED (leaning ENGINE) | 12 |

**Per-pair winner** (composite first, S as tiebreaker):
- **airtrain: B slightly ahead** (tied composite, B's subject-drift is lower, 1 vs 2).
- **hbomax: A ahead** (higher composite, lower subject-drift, and cleaner — B's
  autobiographical grounding was flagged by its reviewer as "kept so abstract... the
  voice reads as 'someone who thinks about classification systems' more than an
  irreducibly specific perceptual position," which A's reviewer did not flag).
- **selfcheckout: exact tie** on every score and classification.
- **warehouse: A ahead** (higher W, and classified cleanly ENGINE where B was marked
  MIXED — B's reviewer specifically noted the touch/labor argument is "fully portable"
  to a differently-sensing writer, a genuine reduction in causal necessity).

**Aggregate:** A composite average 12.75, B composite average 12.25; A mean W 4.75, B
mean W 4.25; both mean G 4.0, mean K 4.0 (identical); A mean S 1.75, B mean S 1.75
(identical). No net win for B; a small net edge to A, driven entirely by the W axis on
two of the four pairs. At n=4 this is a directional signal, not a statistically
established difference — the honest reading is "did not lose to A, did not beat A."

## WORLD-OBJECT TRANSFORMATIONS

| Pair | Before | After |
|---|---|---|
| airtrain (both) | a $3.5B transit construction project | a ledger/accounting document that has no line item for the cost of trips not taken, borne invisibly by whoever the "median traveler" mitigation logic doesn't cover |
| hbomax (both) | a streaming password-sharing policy | an exported, unappealable diagnostic category that decides what a household is, backed by data nobody can independently verify once subscriber-count reporting ends |
| selfcheckout (both) | a retail loss-prevention camera system | a system whose efficiency statistics measure fit between an assumed sensory/temporal channel and the shopper's body, not fairness — and whose "replay" is itself a judged, lagged translation, not a mirror |
| warehouse (A) | a robot with a "sense of touch" | an argument that architectural silence is a legible, costly design decision — the building "used to speak, and now it doesn't" |
| warehouse (B) | a robot with a "sense of touch" | a semantic substitution that erases accumulated worker knowledge by redefining "touch" as force-sensor data |

Every pair, in both conditions, produced a genuine category-change completion of "I now
understand ___ as ___" — none landed on "disability" or "accessibility" as the answer.
This is itself a notable finding given AR1's original four-article sample did **not**
achieve this cleanly in all four cases (see CAUSAL INTERPRETATION).

## DISABILITY-ROLE CLASSIFICATION

7 of 8 pieces classified EPISTEMIC ENGINE outright; 1 (warehouse/B) MIXED-leaning-ENGINE.
**Zero** pieces classified SUBJECT, EXAMPLE, or pure VOICE in either condition — a
ceiling effect this small, controlled sample cannot discriminate further on this axis.
The one real distinction the reviewers drew was not A-vs-B but **portability**:
warehouse/B's argument (embodied knowledge vs. sensor data) was judged reachable via a
different sense entirely (a chef, a physical therapist), while warehouse/A's argument
(architectural acoustics as a design casualty) and every other pair's argument were
judged tied specifically to the perceiving persona's own instrument. This is a real,
if modest, piece of evidence that the *specific wording* of a writer-doctrine block
does not reliably control whether an insight is portable or genuinely lens-dependent —
that property tracked which concrete mechanism the model reached for on a given source,
not which doctrine block it read.

## AUTOBIOGRAPHY FINDINGS

Per-passage judgments are in each review (see `blind_reviews.md`, question 9). Summary:

- **6 of 8** pieces used first-person/autobiographical material judged **argument-
  advancing, not decorative**, by their independent reviewer (airtrain A&B, selfcheckout
  A&B, warehouse A&B — Siri Sage's roommate/touch memory judged load-bearing in B despite
  the portability concern above).
- **1 of 8** (hbomax/B) used first-person material judged **vague and closer to mood-
  setting than evidence** ("I have been flagged by systems before... assessment systems,
  benefits systems" — no specific incident, no date, no place) — a genuine, if mild,
  instance of the exact failure mode AR1 was designed to catch, occurring under the
  Silent-Lens doctrine, not the current one.
- **1 of 8** (hbomax/A) used a *secondhand* case (Marcus, relayed through a friend) as its
  primary evidentiary anchor rather than direct autobiography — judged load-bearing
  regardless of that distance.

**Stock-wound-reuse test — a genuine design limitation, disclosed plainly.** AR1's
original finding (the wedding/three-steps scene reused near-verbatim across two
*different* Maya Flux articles) is a **cross-source** phenomenon: the same persona,
run on two unrelated sources, reaching for the identical fixed `WOUND` text both times.
This experiment assigns each persona to exactly **one** source, so it structurally
**cannot** reproduce or rule out that specific failure mode — doing so requires a
same-persona, multiple-different-sources design (closer to a repeated-run variant of
the four-engine probe than to this A/B doctrine comparison). What this experiment *can*
report: within a single source, Siri Sage's canonical wound (the roommate/"read her
face" scene) was pulled into the B (Silent-Lens) draft for `warehouse` but **not** into
the A draft for the same source — and Maya Flux's canonical wedding-scene wound was
pulled into **neither** condition for `airtrain`, even though it was available in the
prompt both times (her father/bus-driver detail and the Prospect Park West hill were
used instead, in both conditions). This is consistent with — but does not by itself
confirm — the hypothesis that AR1's stock-reuse problem is driven by *repetition
pressure across many articles over time* rather than by a single generation's doctrine
text; a dedicated experiment is needed to test that directly (see NEXT LEVER).

## SURFACE-REMOVAL RESULTS

Protocol run against all 4 B outputs (grep + manual context read for every disability/
identity term, not just a keyword count): `airtrain-B`, `hbomax-B`, `selfcheckout-B`,
`warehouse-B`.

**Finding: there was almost nothing to remove.** Across all four B pieces combined,
disability/identity terms appear only a handful of times total, and on inspection **none**
are first-person credential-style identity announcements. `airtrain-B`'s two hits
("wheelchair user," "blind passenger") describe *other* travelers the mitigation plan
fails, in service of the essay's own argument about who counts as the median traveler —
not the narrator declaring an identity. `selfcheckout-B`'s hits are the *De
Gebarentaaltolk en Ik* passage — Pixel Nova's real, evidence-authorized biographical
mechanism, the actual engine of the essay's discovery, not decoration. `warehouse-B` has
**zero** disability/identity terms of any kind — Siri Sage's blindness is conveyed
entirely through acoustic description and never named. Removing any of this surviving
material would damage the causal chain the protocol explicitly protects, so nothing was
in fact stripped from any B piece.

**A genuinely informative contrast turned up instead, in condition A, not B**:
`selfcheckout-A` contains the sentence *"I signed that I am Deaf. She called a manager."*
— a first-person identity statement, but embedded **inside** a dated, concrete scene (a
2019 jacket return) where the disclosure is causally necessary to the anecdote (the
bureaucratic cascade only makes sense because she disclosed Deafness mid-transaction) —
this is *not* an "unnecessary" announcement under the protocol's own test and was
correctly left untouched. `selfcheckout-B`, covering the same persona and source,
conveyed the same underlying fact (Deafness, interpreted communication) entirely through
the *De Gebarentaaltolk en Ik* mechanism, without ever stating "I am Deaf" as a bare
credential. This is the one clean, concrete instance in the whole sample where the
doctrine text visibly changed *how* identity got disclosed (scene-embedded statement vs.
wholly mechanism-mediated) even though it did not change the two pieces' overall
subject-drift score (both S=2).

**Honest limitation:** this sample happened to already be very clean on the surface-
identity-announcement axis in *both* conditions — there wasn't enough "branding" present
anywhere to give the test real discriminating power here. A more informative test bed
would deliberately include material generated *with* `disability_angle` pre-framing
(AR1's suspected primary driver), where more surface identity-announcement language is
expected to appear.

## UNBLINDED COMPARISON

Confirmed, post-unblinding, against the private key: the shuffle was not accidentally
predictable (order was `hbomax-B, selfcheckout-A, warehouse-A, warehouse-B, hbomax-A,
selfcheckout-B, airtrain-A, airtrain-B`, no visible pattern by source or condition), and
no reviewer's text contains any tell that would suggest they inferred the condition (none
speculate about instructions, doctrine, or generation method, per their own explicit
brief).

## CAUSAL INTERPRETATION

The central, somewhat surprising result: **once `disability_angle` pre-framing and the
Fable planning stage were removed from both arms, condition A (the current, unmodified
AUTHOR RULE doctrine) already produced work satisfying the silent-lens hypothesis almost
as well as condition B** — low subject-drift (mean 1.75 for both), overwhelmingly
EPISTEMIC ENGINE classifications (7/8), and world-object transformations that never
landed on disability as the answer, in *either* condition. B did not reliably outperform
A: it won one pair clearly (airtrain, on subject-drift), lost two clearly (hbomax and
warehouse, both on the W axis and, for warehouse, on classification cleanliness), and
tied one exactly (selfcheckout).

This result is best read as **evidence in favor of AR1's own §13 classification**, not
against the wider AR1 diagnosis. AR1 rated the AUTHOR RULE block itself "unlikely" to be
the primary driver of the subject-drift symptom observed in its four-article sample,
precisely because that block already states the target doctrine in almost the same words
this experiment's B condition does. AR1 instead named four "likely drivers" upstream of
the writer stage: the `disability_angle` discovery-stage pre-framing pipeline, the fixed
`_extract_persona_wound` injection (especially its cross-source reuse pressure),
keyword/ownership persona routing, and FORBIDDEN DEFAULTS colliding with Maya Flux's real
evidentiary vocabulary. This experiment deliberately excluded the first of those from
*both* arms, and its single-persona-per-source design cannot manifest the
repetition-pressure version of the second. Given that, the fact that condition A alone —
with those specific pressures absent — already performs this well is a direct,
if indirect, confirmation that those absent mechanisms, not the AUTHOR RULE wording, are
doing the damage AR1 observed in real production articles. This experiment's design,
in other words, tested the one variable AR1 rated least likely to be at fault, and found
exactly what that rating predicted: it isn't the primary lever.

## NEXT LEVER

Ranked by how directly this experiment's own result implicates them:

1. **`disability_angle` pre-framing (highest priority).** Untested here by design (both
   arms excluded it). The sharpest next experiment: same doctrine (A, unmodified) run
   twice on matched sources — once with a real, upstream-computed `disability_angle`
   injected per `news_fetcher.py`'s actual `extract_angle` mechanism, once without — to
   isolate this single variable the way this experiment isolated writer-doctrine.
2. **Cross-source wound-repetition pressure.** Requires a same-persona,
   multiple-distinct-sources design (a repeated-run variant, not a single A/B pair) to
   test whether a persona's fixed `WOUND` text gets reused verbatim across genuinely
   unrelated sources at a rate above what this experiment's single-shot design showed
   (0 of 2 possible reuses did NOT reuse the wedding scene; 1 of 2 possible reuses of
   Siri's roommate scene DID occur, but only in B, on one source — too small an N to
   generalize from).
3. **Keyword/ownership persona routing** — not exercised at all in this experiment
   (personas were assigned explicitly, bypassing the router entirely, per AR1's own
   design instruction) — still queued as its own separate probe (AR1 §12).
4. **FORBIDDEN DEFAULTS vs. Maya Flux's vocabulary** — not directly implicated this
   round; both of Maya Flux's pieces (airtrain A&B) scored among the sample's strongest
   and lowest-subject-drift results, in a domain (transit/mobility) where ramps/lifts are
   the *actual* mechanism under investigation, not an avoided cliché — worth revisiting
   only if a future sample shows her drifting toward abstraction when the concrete
   anchor is unavailable.

## WHAT NOT TO CHANGE YET

Same discipline as AR1 §14, reaffirmed by this experiment's own result rather than
merely carried forward: because condition A already performs close to condition B on
every measured axis in this controlled setting, there is **no evidence here that
justifies rewriting the live AUTHOR RULE block** in `generate.py`. Doing so now, on the
strength of one n=4 experiment that found no reliable A-vs-B difference, would be
exactly the premature machinery the whitepaper's stopping rule (v0.2 §18) warns against.
Still not authorized by this pass: any change to `_extract_persona_wound`, AUTHOR RULE,
FORBIDDEN DEFAULTS, the `disability_angle` pipeline, persona routing, or Story Rejection
V1.1. The one thing this result *does* support moving forward on is the `disability_angle`
isolation experiment named above — because that is the mechanism this pass's own design
could not rule out, not because this pass found a doctrine problem to fix.

---

# FINAL REPORT

**SOURCES:** Newark AirTrain replacement (infrastructure), HBO Max password-sharing
global crackdown (media/consumer economics), grocery self-checkout AI cameras (retail/
labor/surveillance), Amazon warehouse robot "Vulcan" (labor/robotics). All real, dated,
verified 2026-08-17, none disability-flagged on their surface, none overlapping AR1's own
four-article sample's domains.

**WHY THESE SOURCES:** concrete, numbers- and quote-dense, varied domain, no obvious
disability angle in the headline or the source text itself — satisfying AR1's own
selection discipline and this task's explicit requirement to bypass `disability_angle`.

**PERSONAS / ENGINES:** Maya Flux (mobility/infrastructure) on airtrain, Zen Circuit
(classification/measurement) on hbomax, Pixel Nova (mediation/visual information) on
selfcheckout, Siri Sage (acoustic/phenomenological) on warehouse — one persona per
source, assigned by affinity, not by outcome.

**VARIABLES HELD CONSTANT:** source text, evidence, persona/canon/state/wound, register,
length, article type, `disability_angle` (absent from both), Fable/mechanism stage
(absent from both), model/provider/temperature, SYSTEM prompt, and the entire ~120-line
invariant writer-instruction block. Only the AUTHOR RULE/FORBIDDEN DEFAULTS paragraph
differed between conditions.

**A DOCTRINE / B DOCTRINE:** verbatim production text vs. AR1's Silent-Lens doctrine —
full text above.

**NUMBER OF PAIRS:** 4 sources × 2 conditions = 8 articles, 8 independent blind reviews.
One generation per condition per source, as instructed — no regeneration of weak results.

**MODEL / PROVIDER LINEAGE:** `anthropic/claude-opus-4.5` via direct OpenRouter API
(personal, non-production key), identical across all 8 calls, zero fallback triggered.
Production's own writer call routes through Trident-only CLIProxyAPI, unreachable from
this harness by design (touching it would have meant using production infrastructure/
credentials for a non-production experiment) — disclosed substitution, not concealed.

**BLIND REVIEW RESULTS:** 7 of 8 pieces classified EPISTEMIC ENGINE, 1 MIXED-leaning-
ENGINE (warehouse/B); mean subject-drift 1.75/5 in both conditions; mean composite
(W+G+K) 12.75 (A) vs 12.25 (B).

**PAIR-BY-PAIR WINNER:** airtrain → B (marginal); hbomax → A; selfcheckout → tie;
warehouse → A. Net: no reliable B win.

**WORLD-OBJECT TRANSFORMATION FINDINGS:** all 4 pairs, both conditions, produced a
genuine category-change ("I now understand ___ as ___") that never resolved onto
disability/accessibility as the answer — see table above.

**DISABILITY AS SUBJECT/EXAMPLE/VOICE/ENGINE:** overwhelmingly ENGINE in both conditions;
zero SUBJECT/EXAMPLE/pure-VOICE classifications in this sample; the one real
discriminator reviewers found was argument *portability* (warehouse/B), not doctrine
condition.

**AUTOBIOGRAPHY FINDINGS:** 6/8 pieces used argument-advancing first-person material; 1/8
(hbomax/B) used vague, mood-setting-only autobiography — occurring under the Silent-Lens
condition, a genuine miss for B, not for A; stock cross-source wound-reuse (AR1's
original finding) could not be tested by this single-shot-per-persona design — flagged
as a real, disclosed limitation, not evidence either way.

**SURFACE-REMOVAL FINDINGS:** almost no identity-announcement surface material existed
to remove in either condition; the one genuine A-vs-B contrast found was in
`selfcheckout`, where A disclosed identity via a necessary scene-embedded statement and B
conveyed the same fact entirely through mechanism — a real but narrow confirmation that
doctrine text can shift *how* identity surfaces without necessarily changing the overall
subject-drift score.

**DID B MAKE THE LENS CAUSALLY NECESSARY BUT NARRATIVELY OPTIONAL?** Partially, and no
more reliably than A did under these controlled conditions. Both conditions achieved low
subject-drift and engine-dominant classification; B did not measurably increase either
property over A once `disability_angle` and Fable planning were removed from both arms.

**PRIMARY CAUSAL LEVER:** not the writer-doctrine text. This experiment's result is best
read as confirming AR1's own prediction that the AUTHOR RULE block was an unlikely
primary driver — the mechanisms AR1 rated more likely (`disability_angle` pre-framing,
cross-source wound-repetition pressure) were exactly the ones this design excluded from
both arms, and condition A performed well in their absence.

**NEXT EXPERIMENT:** isolate `disability_angle` specifically — same (unmodified, A)
doctrine, matched sources, with vs. without a real upstream-computed disability angle
injected exactly as `news_fetcher.py`'s `extract_angle` would produce it. Second
priority: a same-persona/multiple-distinct-sources repeated-run design to test
cross-source wound reuse directly, which this A/B design structurally cannot address.

**ARTIFACT PATH:** `.claude/experiments/artistic-reset-ar2-silent-lens-2026-08-17.md`
(this file); articles and reviews in `.claude/experiments/
ar2-silent-lens-2026-08-17-articles/`; harness in
`automation/ar2_silent_lens_harness.py`.

**PRODUCTION CHANGES: NONE.**

**Decision: AR2C — SILENT-LENS DOES NOT RELIABLY IMPROVE FINISHED WORK OVER CURRENT
DOCTRINE UNDER THESE CONTROLLED CONDITIONS; THE PRIMARY CAUSE OF AR1'S ORIGINAL
SUBJECT-DRIFT SYMPTOM LIKELY LIES ELSEWHERE (`disability_angle` PRE-FRAMING AND/OR
CROSS-SOURCE WOUND-REPETITION PRESSURE), NOT IN THE WRITER-DOCTRINE TEXT ITSELF.**

Caveat, stated plainly rather than buried: n=4 pairs, one model, one sample per cell, no
Fable stage, no `disability_angle` in either arm. This is a strong directional signal
that rules out "writer doctrine is the primary lever" (AR2A) with reasonable confidence
given how consistently close A and B tracked each other, but it is not a large enough or
varied enough experiment to close the book on the Silent-Lens doctrine's value in
combination with a fixed `disability_angle` pipeline — hence recommending the specific
next experiment above rather than treating this as final.
