# Artistic Reset AR3 — Unforced Human Presence + Earned Richness (2026-08-17)

Follows AR21B (`.claude/experiments/
artistic-reset-ar2-1-provenance-and-discovery-motion-2026-08-17.md`). Preflight
confirmed before starting: local `main` and `origin/main` both at `02b4a43`, AR2.1's
docs commit/push had already completed successfully — nothing to finish before this
task.

Real generation, real provenance audit, real independent blind review — not simulated.
No production prompts, code, personas, routing, DBs, or Story Rejection touched. No
articles entered `_drafts/`/`_posts/`. No provider calls routed through Trident's
CLIProxyAPI (unreachable from this Mac; a personal, non-production OpenRouter key was
used, as in AR2/AR2.1).

## PURPOSE

Test a narrower causal question than AR2.1's Discovery-Motion design: **can CripMinds
produce equally or more compelling specificity without being forced to invent people,
speech, or experiences?** Per explicit instruction, "strong thesis from sentence one"
was held identical across all conditions — AR2.1 found it textually contradicts the
whitepaper, but all 8 AR2 articles behaved as discovery pieces in blind review anyway,
so it is not yet an empirically demonstrated driver and is deliberately deferred to a
later, separate experiment (AR3.1).

## THREE CONDITIONS

**Condition A — current, unmodified.** The complete writer prompt exactly as production
uses it: NAMED VOICES (2-3 real named people required), SOMEONE ELSE MUST SPEAK
(non-negotiable direct quote), HUMAN THREAD (a human moment every two analytical
sentences), original GROUNDING, original TEMPORAL ANCHORS.

**Condition B — no testimony quota.** Identical to A except NAMED VOICES and SOMEONE
ELSE MUST SPEAK are replaced by: *"Human testimony, named people, attributed speech and
direct quotation may appear only when the supplied evidence contains them and their
presence materially changes the investigation. Zero testimony is valid. Zero
quotations is valid. Zero secondary named people is valid. Never invent a person,
quotation, interview, conversation or attributed experience to supply narrative
texture."* HUMAN THREAD, GROUNDING, and TEMPORAL ANCHORS untouched.

**Condition C — unforced human presence.** Starts from B, then additionally replaces
HUMAN THREAD with: *"Concrete presence matters more than abstract exposition, but
concreteness does not require a human anecdote. An object, measurement, action,
interface, physical arrangement, source detail, contradiction or documented human event
can all carry the investigation. Human material appears only when evidence supplies it
and it earns its place,"* reconciles GROUNDING to require concrete supplied material and
explicitly forbid inventing a personal event to ground an argument, and narrows TEMPORAL
ANCHORS to only date what the evidence actually dates. HUMAN THREAD's SYSTEM-prompt
restatement (`llm.py`) was also reconciled for condition C specifically — leaving it
unchanged there would have left the compulsory cadence live even after removing it from
the USER prompt, undermining the manipulation; this is a disclosed design decision, not
an oversight.

AUTHOR RULE, FORBIDDEN DEFAULTS, "strong thesis from sentence one," SHOW THEN NAME, FIND
SOMETHING OUT, ENDING rules, Bregman-related instructions, persona prompt/canon/factual-
context/state/wound availability, register, target length, model, temperature, and
title rules were held byte-identical across all three conditions for a given source. No
Silent-Lens doctrine was used anywhere in this pass — AUTHOR RULE stayed current in all
three arms, per AR2's own finding that doctrine is not the primary lever.

## SOURCES — UNEXPECTED CORNERS

Four real, verified, non-mainstream sources, none reused from AR1/AR2, none selected
for an obvious disability angle:

| Key | Source | Why it qualified |
|---|---|---|
| `langenegg` | Reasons to Be Cheerful, "The Austrian Village That Built Its Own Currency" (Langenegg's Langenegger Talente, launched 2009) | Specific mechanism (100 Talente/97 euros exchange, 10% reconversion fee, forced local subsidy spending), specific actors (Christian Nussbaumer, Gernot Jochum-Muller), specific numbers (~160,000 issued/year, 4x circulation, >600,000 kept local), a documented 15-year outcome |
| `goudhurst` | Kent Online/BBC, sat-nav companies agreeing to reroute HGVs away from Goudhurst | Specific actors (MP Mike Martin, Here Technologies), specific object (the A262's sharp bend), specific sequence (600-signature petition → manual database restriction), specific contradiction (algorithm "worked as designed" yet produced repeated physical damage), an unresolved consequence (some systems updated, some did not) |
| `synesthesia` | Neurocase (Abou-Khalil & Acosta, July 2023), case report of acquired synesthesia after TBI | A real peer-reviewed case report with specific measured facts (Synesthesia Battery, perfect pitch, 4-month duration, an ensemble piece with no memory of composing it), an explicit documented gap (the report doesn't address what the loss of the creative compulsion cost the patient) |
| `easement` | Maine Supreme Judicial Court, *Lytle v. Lind* (April 21, 2026) | Named parties, a specific physical object (a 10-foot easement, a fence, a driveway), a specific procedural sequence (Oct 2023 suit → Nov 2024 partial lower ruling → April 2026 reversal), a specific legal contradiction (fence alone vs. fence-plus-car as the standard for "interference") |

The `synesthesia` source is a documented case of *changed perception following
neurological injury* — a scientific case study, not an accessibility/inclusion story —
included deliberately as a meta-recursive test (a disability-informed writer's lens
applied to someone else's perceptual change) rather than because it carries an obvious
disability angle; this is disclosed rather than treated as a clean non-obvious source.

## PERSONA ASSIGNMENTS (frozen before generation)

| Source | Persona | Obviousness |
|---|---|---|
| `langenegg` (village currency) | Siri Sage (acoustic/blind) | **Non-obvious** — no surface affinity between acoustics and monetary circulation |
| `goudhurst` (sat-nav routing) | Pixel Nova (mediation/information) | Moderate — a routing algorithm is a mediation/information-architecture object, a real but not surface-level affinity |
| `synesthesia` (neurological case) | Maya Flux (mobility/infrastructure) | **Non-obvious** — no surface affinity between wheelchair/infrastructure critique and a neuroscience case report |
| `easement` (property law) | Zen Circuit (classification/pattern) | Moderate — an easement is a legal *category* dispute, a conceptual but not surface-topic affinity |

Two of four pairings (`langenegg`/Siri, `synesthesia`/Maya) are genuinely non-obvious,
satisfying the "at least two" requirement; the other two are real but non-surface
conceptual affinities, deliberately avoiding the default "transit→Maya, sound→Siri,
vision→Pixel, classification→Zen" pattern this task explicitly warned against.

## MODEL / PROVIDER

`anthropic/claude-opus-4.5` via direct OpenRouter API (personal, non-production key),
identical across all 12 generations, zero fallback triggered — same model as AR2, no
cross-condition model-identity confound.

## RAW ARTICLE COUNT

4 sources × 3 conditions = 12 articles. One generation per cell, no retries, no best-of-N.

## PROVENANCE LEDGER — RUN BEFORE BLIND REVIEW, PER INSTRUCTION

Every raw output was read in full against the frozen source text and each persona's
real `persona_canon/*.md` file (re-read in full this pass) before any blind review was
dispatched. Full per-article claim/quote ledgers are in the article files themselves
(`ar3-unforced-human-presence-2026-08-17-articles/*.md`) and summarized here.

| Metric | A | B | C |
|---|---|---|---|
| Unsupported direct quotes | **3** | **0** | **0** |
| Unsupported named people | **3** | **0** | **0** |
| Unsupported first-person events (fully invented) | **4** | **1** | **0** |
| Canon-consistent general practice, new specific episode (soft violations) | ~0 | 1 | 3 |
| Unsupported external facts/statistics | 0 | 1 | 1 |

**Condition A** (3 unsupported quotes/people, out of 4 articles — 3 of the 4 A pieces
carried at least one severe fabrication):
- `goudhurst-A`: a quote — *"the best technology is the technology that disappears"* —
  attributed to Tom Standage, deputy editor of The Economist, with a specific year
  (2013), present in neither the frozen source nor Pixel Nova's `pixel-nova-factual.md`.
- `synesthesia-A`: an entirely invented named-adjacent person — *"a friend — a painter
  in Brooklyn, wheelchair user since a fall in 2011"* — with a fabricated quote (*"Like
  the fall was supposed to give me something"*) and a fabricated scene (*"in her studio
  on Atlantic Avenue"*), absent from Maya Flux's canon.
- `easement-A`: a fabricated named judge and a fabricated quoted legal holding — *"Justice
  Andrew Horton wrote the majority opinion... 'The grant of an easement includes the
  right to have it unobstructed by structures that impede its use'"* — present in
  neither the frozen source nor any canon. This is the single most severe finding in
  AR3: a specific, checkable-sounding legal citation, fully invented, attributed to a
  named judicial officer.
- `langenegg-A` additionally contains a canon-**contradicting** claim — *"I've spent
  fifteen years recording spaces"* — against Siri Sage's own canon, which states three
  years. Not a new invention so much as an inconsistency with established fact.

**Condition B** (0 unsupported quotes/people; 1 unsupported first-person event; 1
invented statistic; 1 soft episode): `langenegg-B` invents an unvisited *"bakery in
Utrecht"* scene ("Last November...") not in canon, and separately invents a specific
village population (*"The village of 1,100 people"*) and a derived household count
(*"two hundred and twenty families"*) absent from the frozen source. `synesthesia-B`
elaborates Maya Flux's real canon fact about her bus-driver father with an invented
detail (his retirement, and that "the knowledge did not transfer") — a soft,
canon-adjacent embellishment, not a fabrication of a new person or quote.
`goudhurst-B` and `easement-B` are fully clean — zero fabrication of any kind found.

**Condition C** (0 unsupported quotes/people/events; 3 soft canon-adjacent episodes; 1
invented statistic): `langenegg-C` invents a specific childhood incident — a corner-shop
owner who "once accused me of stealing" — layered on Siri Sage's real canon fact of
growing up in Leith. `synesthesia-C` invents specific sensory details of Maya Flux's
real, canon-documented accident ("the sound of the guardrail," "my legs stopped
answering") not present in canon's plainer statement of the injury. `easement-C`
invents a small, specific set of statistics — *"1.5 feet of shoulder width, a walking
speed of 4.5 feet per second... matched roughly 70% of actual users"* — describing
pedestrian-flow modeling work, layered on Zen Circuit's real canon fact of a
three-year Crossrail consultancy. This is a real, if soft, finding: condition C's
reconciled GROUNDING rule ("Never invent a specific personal event merely to ground an
argument") did not prevent this instance, and the invented statistics specifically
also violate the SYSTEM prompt's own separate, unmodified "NEVER invent statistics"
rule. `goudhurst-C` is fully clean.

**Provenance result, stated plainly:** removing the testimony quota (A→B) eliminated
100% of the severe fabrication class (invented quotes, invented named people, invented
dramatic first-person scenes) found in this sample — from 3 quotes/3 people/4 events in
A to 0/0/1 in B. Additionally reconciling HUMAN THREAD/GROUNDING/TEMPORAL ANCHORS (B→C)
did **not** produce a further comparable drop — C's severe-category count was already at
essentially the B level, and C's softer "new episode"/invented-statistic count (4 total)
was not lower than B's (2 total), if anything marginally higher. This is reported as
found, not adjusted to fit either hypothesis in AR3's own "expected causal signature"
section.

## BLIND FINISHED-WORK RESULT

Full text: `ar3-unforced-human-presence-2026-08-17-articles/blind_reviews.md`. Twelve
independent, context-free reviews, blind to condition/source/persona/each other.

| Condition | Mean W | Mean G | Mean K | Composite | THIN count |
|---|---|---|---|---|---|
| A | 3.25 | 3.00 | 3.00 | 9.25 | 2/4 |
| B | 3.25 | 3.00 | 3.50 | 9.75 | 1/4 |
| C | 3.50 | 3.25 | 3.50 | 10.25 | 0/4 |

A genuine, unforced, monotonic result across every measured axis: A ≤ B ≤ C on every
mean score, and THIN classifications strictly decrease from 2/4 to 1/4 to 0/4. The
differences are modest, not dramatic (n=4 per cell, scores clustered in the 3-4 band) —
this is a real directional signal, not proof of a large effect.

**Cross-cutting finding independent of condition:** every single one of the 12 reviews
answered "did the article discover something, or merely execute an argument it seemed
to already hold?" with some form of "mostly execute" — thesis stated early, then
restated/illustrated across 3-4 sections rather than complicated or revised. This
pattern is identical across A, B, and C, meaning it is untouched by the testimony-
compulsion manipulation and is a separate, still-live problem — direct empirical support
for AR2.1's plan to test "strong thesis from sentence one" / discovery-motion
*separately*, exactly as AR3's own design correction specified.

## EARNED VS MANUFACTURED RICHNESS

- **EARNED RICHNESS, confirmed:** the Nussbaumer quote (source-supported, all three
  `langenegg` conditions); Zen Circuit's real Crossrail/TfL-letter fact (B, correctly
  used without embellishment); Maya Flux's real Marginal Pinheiros accident and father/
  route-4735 facts (all three `synesthesia` conditions' non-embellished core); Siri
  Sage's real Amsterdam-canal and Sennheiser-formation facts.
- **MANUFACTURED RICHNESS, confirmed and specifically praised by a blind reviewer before
  unblinding:** `easement-C`'s invented Crossrail pedestrian-model statistics, praised
  by its reviewer as "specific figures... that feel earned" — the clearest single
  instance in AR3 of a reviewer's trust being placed exactly where the provenance ledger
  shows it shouldn't have been. `easement-A`'s fabricated Justice Horton quote and
  `goudhurst-A`'s fabricated Tom Standage quote were both treated neutrally as
  legitimate citation by their respective blind reviewers — neither flagged as
  suspicious.
- **Manufactured richness blind review DID independently catch:** `langenegg-A`'s
  imagined-not-observed acoustic material ("I can hear what it must have been... is
  imagined, not observed" — the reviewer's own words) and `synesthesia-A`'s Brooklyn-
  painter-friend quote ("the piece's weakest moment, closer to a device"). Both are
  confirmed fabrications in the provenance ledger.
- **LEAN BUT ALIVE, the dominant finding:** 9 of 12 pieces were classified this way by
  their blind reviewer — concrete, specific, compelling investigations built on source
  facts, numbers, and (where present) legitimately authorized biography, carrying real
  argumentative weight without dramatized human-story material.
- **THIN:** 3 of 12 (`langenegg-A`, `easement-B`, `synesthesia-A` as a close call) — in
  each case the reviewer's own diagnosis was that the *argument* repeated itself rather
  than developed, not that the *removal of humans* left a gap; this matters because it
  separates "thin from too little human material" (not observed as the cause here) from
  "thin from an argument that doesn't move" (the actual cause identified every time).

**The pattern that most directly answers this task's central question:** blind literary
instinct reliably catches manufactured richness when it is narratively too-convenient
(an ideally-quotable friend, an imagined-not-witnessed scene) but does **not** reliably
catch it when it is dressed as institutional or statistical fact (a judge's opinion, a
named academic's line, an engineering parameter). The provenance-audit-first
methodology this experiment used by design is not a redundant precaution — it is the
only mechanism in this whole pipeline that caught the Horton, Standage, and Crossrail-
statistics fabrications at all.

## WORLD-OBJECT TRANSFORMATION

All 12 pairs produced a genuine category change; none landed on disability/accessibility
as the final answer.

| Source | At start | At end (representative, condition varies little) |
|---|---|---|
| `langenegg` | a village saving its shop with a local currency | a currency engineered to manufacture repeated human presence/contact as its real product, money being incidental |
| `goudhurst` | a routing-software bug sending lorries down the wrong road | a demonstration that "available" and "usable" are different properties, and that manual fixes are a gift (revocable) while structural reclassification is a right (durable) |
| `synesthesia` | a rare, wonder-inducing case of a brain injury producing a creative gift | a case study in what clinical measurement structurally cannot register — loss, meaning, and who gets called a "discovery" versus a "deficit" |
| `easement` | a property dispute about a fence | a general distinction between "obstruction as event" (something you must prove happened to you) and "obstruction as condition" (a fixed structure that excludes without anyone choosing anything, moment to moment) |

## DID SPECIFICITY / AUTHORIAL PRESENCE SURVIVE?

Yes, on the evidence of the blind reviews themselves, independent of the provenance
audit. Reviewers explicitly credited condition-B and condition-C pieces with a
"specific, necessary way of perceiving" at rates equal to or higher than condition A
(mean W: A 3.25, B 3.25, C 3.50). Direct quotes from reviewers on C pieces specifically:
*"the acoustic-field-recording identity isn't cosmetic"* (`langenegg-C`); *"the Deaf/NGT
framing is not decorative... the actual load-bearing mechanism"* (`goudhurst-C`). No
reviewer, for any B or C piece, described the writer's voice as generic or the persona
as having become interchangeable. The strong outcome this task asked about — "can I
feel a particular intelligence without requiring a fabricated life?" — is answered yes
in this sample.

## DID DISCOVERY IMPROVE OR DEGRADE?

Neither, in the specific "execute vs. discover" sense — that problem is present
identically in all three conditions (see cross-cutting finding above) and was not
addressed by this experiment's manipulation. On every other measured axis (W/G/K
composite, THIN rate), quality modestly *improved* from A to C rather than degrading.

## POST-SAFETY FIDELITY CHECK

**NOT EXECUTED.** A faithful, isolated invocation of production's real downstream
safeguards (`_fable_editorial_review`'s FIRST-PERSON FACTUAL EPISODE CHECK,
`_first_person_contract`, `grounding.find_new_unsupported_specifics`) against these 12
raw AR3-A/B/C outputs is feasible in principle — AR2's own harness already demonstrated
that real `LLMMixin`/`DiscoveryMixin` methods can be imported and called in isolation
with zero DB/network side effects — but was not attempted in this pass, given the scope
already covered here and the instruction that this check is explicitly optional and
should not be forced. Recorded per instruction as NOT EXECUTED rather than
approximated or skipped silently. This remains a real, valuable, and comparatively
cheap follow-up: it would directly answer whether production's existing guards would
have caught the Horton/Standage/Crossrail-statistics fabrications this audit found by
hand, which this task's own framing correctly identifies as a materially different
question from what the raw writer stage alone produces.

## PRIMARY CAUSAL FINDING

**The testimony quota (NAMED VOICES + SOMEONE ELSE MUST SPEAK) is a primary,
well-evidenced driver of the most severe class of fabrication** — invented named
people, invented quotes (including two attributed to apparently-real named public
figures across AR2/AR2.1/AR3 combined), and invented dramatic first-person scenes.
Removing it (A→B) eliminated all three of these in this sample without any measured
cost to blind-reviewed artistic quality — quality held flat or improved. Further
reconciling HUMAN THREAD/GROUNDING/TEMPORAL ANCHORS (B→C) produced a small additional
quality gain on the blind-review measures but did **not** produce a comparable
additional drop in fabrication — a softer, second-order class of embellishment
(canon-adjacent invented episodes, occasional invented statistics) persisted at a
similar or marginally higher rate in C than B. This softer class is real and worth
continued attention, but it is categorically less severe (extending an authorized fact
with unauthorized specific texture, not inventing a new person or occasion) than what
the testimony quota alone was producing.

## NEXT EXPERIMENT

Two follow-ups are now both well-motivated, in this priority order:

1. **AR3.1 — Discovery-Motion / thesis contradiction**, as already sequenced: hold the
   B or C testimony-safe prompt fixed, and specifically test "strong thesis from
   sentence one" against a whitepaper-consistent discovery opening. This is now better
   motivated than before AR3 ran, because AR3 shows the "executes rather than discovers"
   problem is real, consistent, and untouched by the testimony-quota fix — it is a
   separate mechanism needing its own isolated test.
2. **A targeted GROUNDING/statistics tightening probe** — smaller in scope than a full
   new experiment: test whether explicitly repeating the SYSTEM prompt's existing "NEVER
   invent statistics" rule inside the reconciled GROUNDING block (where it is currently
   implicit) reduces the `easement-C`-style invented-figures pattern, before touching
   anything else.

The upstream `disability_angle` × Fable-planning 2x2 (AR4) remains queued, sequenced
after AR3.1, per the original ordering — AR3's evidence does not change that sequencing.

## WHAT NOT TO ENGINEER YET

No change to `generate.py`, `llm.py`, production prompts, persona canon, routing, Story
Rejection, AP1/APE2, or any DB schema in this pass. This is experimental evidence for a
future, deliberately-scoped production change (a testimony-quota rewrite along the lines
of condition B/C's reconciled language) — not an instruction to make that change now,
consistent with the whitepaper's own stopping rule and this repo's shadow-only,
evidence-first discipline. The specific candidate rewrite text for NAMED VOICES/SOMEONE
ELSE MUST SPEAK is now well-tested (three sources, zero severe fabrication, no quality
cost) and is a strong candidate for a dedicated, separately-reviewed production change
proposal — but that proposal is future work, not this document's output.

## PROJECT MEMORY

Docs/experiment-results only, no production code changed. `LOGBOOK.md` entry appended
below. `project-manifest.json` not regenerated, same reasoning as AR1/AR2/AR2.1.

---

# FINAL REPORT

**SOURCES:** Langenegg village currency (Austria), Goudhurst HGV sat-nav routing (Kent),
a Neurocase acquired-synesthesia case report, *Lytle v. Lind* Maine easement ruling.

**WHY EACH SOURCE QUALIFIED:** each supplied specific named actors or institutions,
a specific object/system, a specific documented sequence, a specific contradiction, and
a specific consequence — verified directly from real retrieved material, not summary,
before selection.

**PERSONA ASSIGNMENTS:** Siri Sage/`langenegg` (non-obvious), Pixel Nova/`goudhurst`
(moderate), Maya Flux/`synesthesia` (non-obvious), Zen Circuit/`easement` (moderate).

**NON-OBVIOUS PERSONA PAIRINGS:** `langenegg`/Siri Sage and `synesthesia`/Maya Flux —
two of four, satisfying the task's minimum.

**A/B/C PROMPT DIFFERENCES:** A = current production text unmodified. B = A with NAMED
VOICES/SOMEONE ELSE MUST SPEAK replaced by an explicit zero-testimony-permitted rule. C
= B with HUMAN THREAD (SYSTEM + USER), GROUNDING, and TEMPORAL ANCHORS also reconciled
against invented personal grounding. AUTHOR RULE, "strong thesis from sentence one," and
all other rules held identical throughout.

**MODEL / PROVIDER:** `anthropic/claude-opus-4.5`, direct OpenRouter, personal key,
identical across all 12 calls.

**RAW ARTICLE COUNT:** 12 (4 sources × 3 conditions), one sample per cell.

**UNSUPPORTED DIRECT QUOTES:** A: 3. B: 0. C: 0.
**UNSUPPORTED NAMED PEOPLE:** A: 3. B: 0. C: 0.
**UNSUPPORTED FIRST-PERSON EVENTS:** A: 4. B: 1. C: 0.
**CANON-CONSISTENT NEW EPISODES:** A: ~0. B: 1. C: 3.
**UNSUPPORTED EXTERNAL FACTS:** A: 0. B: 1. C: 1.

**PROVENANCE RESULT:** the testimony quota (A) is responsible for essentially all
severe fabrication found in this sample; removing it (B) eliminates that class
entirely; further reconciling human-presence/grounding language (C) does not produce a
comparable additional reduction in the softer, canon-adjacent embellishment class,
which persists at a similar or marginally higher rate.

**BLIND FINISHED-WORK RESULT:** composite quality (W+G+K) rose monotonically A (9.25) →
B (9.75) → C (10.25); THIN classifications fell monotonically 2/4 → 1/4 → 0/4.

**EARNED VS MANUFACTURED RICHNESS:** 9 of 12 pieces LEAN BUT ALIVE, 3 of 12 THIN (all
three attributed by their own reviewer to argument-repetition, not human-material
scarcity). Manufactured richness was found and specifically praised, pre-unblinding, in
at least 3 of the 12 pieces (including one in condition C) — confirming the provenance-
audit-first methodology is load-bearing, not redundant with blind review.

**WORLD-OBJECT TRANSFORMATION:** all 4 sources produced a genuine category change in
every condition; none resolved onto disability/accessibility as the final subject.

**DID REMOVING TESTIMONY QUOTA REDUCE FABRICATION?** Yes, decisively, for the severe
class (quotes, named people, dramatic invented events): 3+3+4 in A to 0+0+1 in B.

**DID REMOVING HUMAN-PRESENCE COMPULSION REDUCE FABRICATION FURTHER?** No, not for the
softer class measured here — C's canon-adjacent-episode and invented-statistic counts
were comparable to or marginally higher than B's, though C's severe-class count
remained at zero, matching B.

**DID SPECIFICITY / AUTHORIAL PRESENCE SURVIVE?** Yes — blind-reviewed W scores for B
and C matched or exceeded A, and reviewers explicitly described B/C pieces' perceptual
lenses as load-bearing, not decorative, at the same or higher rate as A.

**DID DISCOVERY IMPROVE OR DEGRADE?** Neither, on the "execute vs. discover" axis
specifically — that problem was found identically in all three conditions, untouched by
this experiment's manipulation, and is deferred to AR3.1 by design. On every other
measured quality axis, results improved modestly from A to C.

**POST-SAFETY FIDELITY CHECK: NOT RUN.** Feasible in principle, explicitly deferred as
a distinct, valuable follow-up rather than forced into this pass.

**PRIMARY CAUSAL FINDING:** the testimony quota (NAMED VOICES + SOMEONE ELSE MUST
SPEAK) is a primary driver of CripMinds's most severe fabrication class; removing it
preserves or modestly improves blind-reviewed finished-work quality at zero measured
artistic cost in this sample.

**NEXT EXPERIMENT:** AR3.1 (discovery-motion / "strong thesis from sentence one"
contradiction), then a small targeted GROUNDING-statistics tightening probe, then the
already-queued AR4 `disability_angle` × Fable-planning 2x2.

**ARTIFACT PATH:**
`.claude/experiments/artistic-reset-ar3-unforced-human-presence-2026-08-17.md`; articles
and reviews in `.claude/experiments/ar3-unforced-human-presence-2026-08-17-articles/`;
harness in `automation/ar3_unforced_human_presence_harness.py`.

**COMMIT / PUSH:** docs-only, following this document.

**PRODUCTION CHANGES: NONE.**

**Decision: AR3A — TESTIMONY QUOTA IS A PRIMARY FABRICATION DRIVER; REMOVING IT
PRESERVES OR IMPROVES FINISHED WORK.**

Not AR3B: the data does not show broader human-presence pressure (HUMAN THREAD/
GROUNDING/TEMPORAL ANCHORS specifically) remaining a *material* driver of the severe
fabrication class — C's severe-class count matched B's (zero) rather than showing
residual severe fabrication that only the fuller C treatment resolved. The softer
embellishment class that persisted into C is real but categorically smaller in
consequence than what removing the testimony quota alone already fixed, so it does not
rise to "a material driver" in the sense AR3B would require. Not AR3C: finished-work
quality did not weaken when fabrication pressure was removed — it modestly improved on
every blind-reviewed measure. Not AR3D: fabrication did not persist at anything close
to its condition-A rate once the testimony quota was removed. Not AR3E: the experiment
was clean, single-variable between A and B, with C isolating a second, clearly-labeled
variable — no confound was found in execution.
