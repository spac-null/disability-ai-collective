# Artistic Reset — Conceptual Preservation Note: Perceptual Engines, Disturbance Discovery, and Shared Case Memory (2026-08-17)

## STATUS / SCOPE

Docs-only preservation. No production code, prompts, personas, routing, Story
Rejection, or DBs touched. No articles generated, no providers called. No whitepaper
version created. This is **not** a decided implementation plan — it is a serious
research hypothesis, written down so it survives future context loss, following
directly from AR3 (`.claude/experiments/artistic-reset-ar3-unforced-human-presence-
2026-08-17.md`, decision AR3A, commit `addbfbe`, confirmed as both `main` HEAD and
`origin/main` HEAD before this note was written — no commits landed between AR3 and
this one).

## WHY THIS NOTE EXISTS

AR1 through AR3 tested increasingly narrow causal questions about the *writer prompt*:
does Silent-Lens doctrine change subject-drift (AR2: no), is AR2's finished-work
evidence trustworthy (AR2.1: partly, once fabrication is accounted for), and does
removing the testimony quota reduce fabrication without an artistic cost (AR3: yes,
decisively, for the severe fabrication class). Each of those experiments held the
*architecture* fixed — four named personas, story-level discovery, human material
manufactured on demand. A conceptual discussion following AR3 raised the possibility
that this architecture itself, not just its prompt wording, may be the more
foundational thing to test. This note preserves that discussion without deciding it.

## WHITEPAPER STATUS

**UNCHANGED. No v0.3 justified yet.** Whitepaper v0.2 already contains, in its own
words, every concept this note builds on: disability-informed perception as an
epistemic instrument (§1), the warning against founder-capture and academic drift (§6),
discovery over delivery (§7), "testimony is not a quota" in spirit — v0.2 §9's "if a
quote merely decorates a conclusion already reached, it can be omitted" and v0.1 §6's
literal "testimony is not a quota; it is an argumentative event" — authorial presence as
"a particular intelligence noticing and arranging the world" rather than compulsory
identity performance (§8), and the engineering stopping rule (§18). Nothing in this
note's four candidate architectures, the disturbance-discovery principle, or the case-
library proposal contradicts the whitepaper. The live tension, as before, is between
whitepaper concept and **implementation assumption** — specifically the assumption,
never stated in the whitepaper itself, that the unit of epistemic difference must be a
named recurring fictional author with a fixed biography. A v0.3 becomes justified only
if the engine-before-persona experiment (§ below) establishes that the perceptual
position, not the persona, is the load-bearing unit — see WHITEPAPER V0.3 TRIGGER.

## PERSONA VS. PERCEPTUAL ENGINE

The bundle currently fused together in production (`personas.py`'s `AGENTS` dict,
`persona_canon/*.md`): perceptual engine + name + disability identity + biography +
wound + voice + topic affinity + state + author/byline. The working distinction to
preserve, not yet adopted as doctrine:

- **A. Perceptual engine** — a disability-derived way of interrogating reality, a
  portable epistemic instrument. Approximate current instances: Pixel Nova's
  mediation/translation/timing/sequence/interpretive-authority engine; Maya Flux's
  route/friction/dependency/promise-vs-delivery engine; Siri Sage's sensory-
  organization/channel-hierarchy/presence engine; Zen Circuit's classification/
  threshold/pattern/administrative-category engine.
- **B. Persona/personage** — the recurring fictional (or, for Pixel Nova, partially
  factual) public author wrapped around an engine: name, biography, memories, wound,
  location, voice, relationships, state, byline.

**Working hypothesis, explicitly not yet accepted as doctrine: the engine may be
fundamental; the personage may be optional.**

This is not entirely new territory — `persona-architecture-audit.md` (cited by AR1)
already separates PERCEPTUAL ENGINE from CORE PERSON, MOTIVE, AFFINITY, RISK, and
TEXTURE as six distinct categories, already replaced "territory" with "affinity"
specifically to stop treating topic-ownership as intrinsic to a persona, and already
flagged (Finding #4) that wound material can become "a de facto attractor" independent
of whether the prompt asks for it — a concern AR2.1 and AR3 later confirmed empirically
with real fabricated and reused wound material. What this note adds beyond that audit
is the more radical version of the question: not just "is the engine well-specified
separately from the persona," but "does the persona need to exist at all, and does the
number need to be four."

## WHY FOUR IS OPEN

No known artistic or epistemic reason requires exactly four personages. Four was an
implementation choice, plausibly useful for manageable differentiation, recurring
voices, disability-perspective spread, and rotation — but it also generated the
secondary machinery `persona-architecture-audit.md` and AR1-AR3 have been auditing:
persona balancing, rotation, topic-affinity routing, biography/wound/state
maintenance, fictional-history provenance rules (AP1/APE2), byline consistency, "who
owns this story," "who hasn't written recently." The number four should not be treated
as sacred merely because it is what the software currently encodes.

## FOUR CANDIDATE ARCHITECTURES

**1 — One collective mind.** A single CripMinds editorial intelligence with access to
multiple disability-derived ways of perceiving, proposing whichever mechanism is
strongest for a given disturbance. Advantages: coherence, no fictional-identity
problem, no persona balancing. Risks: homogenization into one "master disability lens,"
loss of the productive epistemic difference the whitepaper's §5 ("CripMinds does not
need one master lens. It needs conditions in which differences between lenses become
informative") explicitly warns against, generic AI-essay voice.

**2 — Four current personas.** Pixel Nova, Maya Flux, Siri Sage, Zen Circuit, as they
exist today. Advantages: strong recurring identities, recognizable voices, existing
architecture. Risks, now empirically documented across AR1-AR3: fictional biography
mistaken for evidence, wounds becoming stock material, routing/affinity determining
discovery too early, engineering complexity, synthetic-disabled-person performance.

**3 — Four naked engines.** Approximately the current four perceptual engines, stripped
for discovery purposes of names, biography, wounds, voice mannerisms, location, state,
topic ownership, and the requirement to produce finished prose — asking only what each
instrument notices. Advantages: directly tests whether real intellectual difference
survives without character performance. Risks: engines may collapse into generic
analytical prompts without a persona's specificity to anchor them; authorial presence,
if still wanted for publication, would need a separate, later solution.

**4 — Many micro-lenses.** Perhaps 8-12 or more narrow instruments instead of four
large characters — illustratively (not prescriptively): latency, translation, route/
friction, threshold, variability, fatigue, dependency, sensory hierarchy, error
tolerance, pacing, classification, simultaneity, repair/workaround, legibility. These
are epistemic probes, explicitly not twelve fictional disabled people. The exact count
is deliberately unresolved.

None of these four is adopted here. All four are preserved as serious candidates for
the engine-before-persona experiment below.

## AUTHORSHIP AS A LATE, OPTIONAL LAYER

Preserve the possibility that authorship need not be the first architectural decision.
A candidate future pipeline shape:

world → disturbance → perceptual probes → discovery/hypothesis → research + case
retrieval → evidence → form → writer/voice/byline → publication

as opposed to the current implicit shape:

news story → disability angle → persona → persona biography → article

Under the candidate shape, "who writes the finished piece" becomes a decision made
*after* the mechanism is found, not before — and the eventual public voice could be one
of the existing personas, a much thinner persona, a collective CripMinds voice, an
unattributed editorial voice, or a form not yet designed. Not decided here.

## DISTURBANCE AS THE DISCOVERY UNIT

Emerging principle, stated plainly: **don't find stories for CripMinds — find
fractures in ordinary explanations.** The valuable unit may not be the whole article; a
long, ordinary mainstream/local/trade piece may contain one sentence or paragraph more
intellectually valuable than its own headline. Candidate disturbance shapes (illustrative,
not exhaustive, not topic keywords): official explanation vs. practical reality mismatch;
a workaround that has become normal; two systems describing the same object differently;
an edge case breaking a category; a measurement that excludes the thing it claims to
measure; representation overruling physical reality; a physical resource refusing a
legal/administrative boundary; a failure that forces repetition through the same failing
channel; an exception that exposes what the normal rule assumes; a small logistical fact
that makes the headline explanation insufficient; an object used successfully in a way
its designers never anticipated; a rule producing an absurd but lawful consequence;
information that exists but arrives too late, in the wrong form, or through the wrong
sequence to remain the same information. AR3's own four sources (a currency's forced
circulation, a routing algorithm with no field for a road's real width, a case report's
silence about what a lost capacity cost someone, a court distinguishing "obstruction as
event" from "obstruction as condition") are themselves instances of exactly this shape —
retrospectively, all four "Unexpected Corners" sources were selected because they
already contained a disturbance, not because they were interesting topics.

**Candidate discovery-unit fields, preserved not implemented:** source; source URL/
document; disturbance fragment (the exact sentence/paragraph/table row/finding); local
context needed to interpret it; why it looks strange; initial hypotheses (not claims);
what would need to be true for it to matter; what evidence would confirm or refute it. A
disturbance fragment is not enough for publication — it is permission to investigate.

## DISCOVERY EVIDENCE VS. PUBLICATION EVIDENCE

An important, explicitly preserved distinction. **Discovery evidence** is enough
trustworthy material to notice something may be strange and worth investigating — it
may be an RSS excerpt, one paragraph, a sentence buried in a long article, a court-
summary line, a municipal release, a trade-paper detail, a chart, a quote, a small local
report. It may legitimately produce a *question*. It may **not** authorize unsupported
factual mechanism claims. **Publication evidence** is enough grounded, authoritative
material to support the mechanism and every factual claim in a finished article — Story
Rejection V1.1 remains fully authoritative for this boundary, unmodified, unreopened,
and not weakened by anything in this note. Working principle: **discovery can be messy;
publication cannot.**

## FEED IMPLICATIONS

If disturbance, not topic, is the discovery unit, the feed's governing question may
change from "is this article interesting enough for CripMinds?" to "does anything
inside this material resist its own explanation?" Under that framing, broad and even
apparently boring source streams — major newspapers, local newspapers, municipal
material, trade press, court rulings, scientific papers, company releases, design
publications, specialist journals, public records — become valuable precisely because
originality would come less from *where* CripMinds searches than from *what it notices*.
This is a feed/discovery-stage implication only; nothing about the existing
`disability_angle` pipeline or `news_fetcher.py`/`discovery.py` is being changed by this
note, and the still-queued AR4 2x2 experiment (`disability_angle` × Fable planning)
remains a separate, valid question about the *current* architecture regardless of
whether this conceptual branch is later adopted.

## CASE / STORY LIBRARY

Proposal, preserved conceptually only: build a reservoir of real, documented stories
*before* an essay needs human texture, rather than asking the writer to manufacture it
on demand. AR2.1 and AR3 together are the direct empirical motivation — mandatory
testimony provably causes the model to invent people, quotes, visits, research
activity, and personal experience (9 unsupported quotes and 11 unsupported first-person
events across AR2's 8 articles; 3 unsupported quotes, 3 unsupported named people, and 4
unsupported first-person events in AR3's condition A alone), and removing the
compulsion (AR3, condition B) eliminated nearly all of it with no measured cost to
blind-reviewed quality. A pre-built reservoir of real cases would let genuine richness
enter an essay only when the argument actually calls for it, rather than forcing
invention when it doesn't.

**Candidate case-packet schema, preserved, not implemented:** case ID; short name; what
actually happened; source-documented sequence; real people; verified quotable material;
dates/places; primary sources; secondary sources; source hashes/provenance; the strange
detail; known mechanisms/concepts (framed as hypotheses, not owned interpretation); what
this case supports; what this case does not support; confidence; used-before tracking
(article/mechanism/date); related cases.

**Mechanism-based retrieval, not topic-based — this is the central design idea.** A
village-currency case should not be filed only under "economics" — it should be
retrievable by circulation, friction, leakage, boundary, local value, conversion,
movement. The easement case should be retrievable by rights-as-condition-vs-incident,
structure-vs-active-obstruction, persistent friction, geometry-as-law — not merely
"property law." The sat-nav case should be retrievable by representation-vs-territory,
translation loss, late information, classification, propagation, local-vs-system
knowledge. Research retrieval should eventually ask "have we seen this *structure*
somewhere else?" rather than "do we have another story on this *topic*?"

**What a documented case should do in an essay, and when it should not appear.** A case
earns its place only if it performs a real argumentative function: breaking the first
explanation, providing a counterexample, revealing the same mechanism in a completely
different domain, making an abstraction physically understandable, increasing
historical scale, demonstrating consequence, introducing contradiction, forcing a
revision of the mechanism, or changing what the original object means when the essay
returns to it. Working test: **does this documented case change the argument?** If no,
omit it — zero testimony remains valid, exactly as AR3's condition B/C language already
states.

**Books as maps to cases, not quote repositories.** Books can be valuable sources of
documented cases but CripMinds should not casually build an unbounded quote repository
from copyrighted material. For any book-derived case, preserve: author, title, edition,
page; CripMinds's own factual summary; short quotations only when genuinely needed and
appropriately limited; primary sources the book itself cites, recovered where possible;
an explicit line between what the book supports and what is CripMinds's own
interpretation. A book functions as a map to cases and to the original research it
points at, not as the source of record itself.

## BREGMAN STRUCTURAL CONNECTION

Relevant structurally, not stylistically — consistent with how the whitepaper (§7) and
this repo's own prior Bregman craft analyses already frame him. The operation worth
learning from is that a contemporary question travels through documented historical
events, real people, experiments, policies, forgotten cases, research, and small
communities, and returns to the initial object changed. CripMinds currently tends to ask
the writer to produce human texture *after* an argument already requires it — exactly
backward from Bregman's own method of having the case already in hand (Johan van Veen,
the Clarkson-on-horseback moment) before the argument needs it. A case library is one
way to make that ordering possible without inventing the case when the real one isn't at
hand.

## CONNECTION TO AR2.1 / AR3

AR3 (decision AR3A, commit `addbfbe`) found: current mandatory testimony rules produced
fabricated quotes, people, and events; removing the testimony quota reduced these
dramatically; artistic quality did not decline and instead improved across conditions
A→B→C on every blind-reviewed measure; broad compulsory HUMAN THREAD language was not
necessary for specificity to survive; a softer canon-adjacent embellishment class
remained unresolved even in the most constrained condition; provenance-audit-first was
shown to be load-bearing, not redundant with blind review, because blind review
reliably catches narratively-too-convenient fabrication but not fabrication dressed as
institutional or statistical fact; and four hand-picked "Unexpected Corners" sources
successfully produced genuine conceptual work without needing an obvious disability
angle. This strengthens the case for **earned richness over manufactured richness** as
a general principle, and directly supports researching a case reservoir: if real,
pre-documented stories can supply richness honestly precisely when an argument requires
it, the mechanism that produced AR3's fabrications (a structural compulsion to produce
human material on demand, regardless of whether real material exists) is addressed at
its source rather than patched after the fact.

## ENGINE-BEFORE-PERSONA EXPERIMENT — PRESERVE, DO NOT RUN

Conceptual design only. Use approximately 5-6 strong disturbance fragments (not full
articles). Run the identical disturbance through: (A) one collective CripMinds mind;
(B) the four current personas, full biography/voice/wound intact; (C) the four current
perceptual engines stripped of name, biography, wound, state, topic ownership, voice
mannerism, and any requirement to produce polished prose; (D) approximately 8-12 micro-
lenses, narrow epistemic instruments rather than people. For every output, ask only:
what is strange here; what assumption does the ordinary explanation depend on; what
does this way of perceiving notice; what could the original world object become if this
holds; what would prove or disprove the mechanism. No essay, no autobiography, no
byline, no polish. Compare on: conceptual diversity, non-redundancy, surprise,
specificity, world-object transformation, grounding requirements, genericness,
repetition, and whether disability-derived knowledge remains causally legible without
character performance. This is the direct, larger-scale successor to `persona-
architecture-audit.md`'s own already-queued "same-source/four-persona probe" — not a
duplicate of it, since it additionally tests the one-mind and many-micro-lens
architectures that audit never considered. The experiment should answer two questions:
do we have four genuinely distinct epistemic engines or four branded writers, and is
four even the right granularity?

## DISTURBANCE-MINING EXPERIMENT — PRESERVE, DO NOT RUN

Compare whole-article commission search (the current discovery model) against fragment/
disturbance mining. Take a broad set of ordinary articles/documents; have a discovery
stage identify only one to three potentially consequential fragments per document, each
with the exact quote/fragment, local context, why it looks strange, a candidate hidden
assumption, questions raised, and what evidence would be needed. Then evaluate whether
the strongest resulting essay ideas originate from headline/topic-level search or from
buried anomalies. No production discovery machinery should be built for this — it is a
small, bounded comparison.

## CASE-LIBRARY SHADOW EXPERIMENT — PRESERVE, DO NOT BUILD YET

Before any database or vector store is engineered, a small manual/shadow prototype using
roughly 20-50 rigorously documented cases could test: does mechanism-based retrieval
actually improve essays; does it introduce genuinely useful conceptual travel; does it
reduce the pressure to invent testimony (measurable directly via the same provenance-
ledger method AR2.1/AR3 already validated); does it produce Bregman-like argumentative
movement without imitating his voice; does it help an essay return to its original world
object changed. Only if this small prototype shows real benefit should a durable
case-library architecture be considered at all.

## OPEN QUESTIONS

Is four the right number of engines, or any fixed number? Does authorship need to
precede discovery, or can it be decided last? Can a "naked" engine (architecture C)
retain enough specificity to avoid genericness, or does some form of persona remain
necessary for authorial presence even if biography is minimized? Does mechanism-based
case retrieval actually outperform topic-based retrieval in practice, or is this a
plausible-sounding idea that underperforms once tested? Does fragment-level disturbance
mining find better material than whole-article commission search, or does it just add a
new failure surface (irrelevant fragments, fragments taken out of context)? None of
these are answered by this note — they are the reason the experiments above exist.

## WHAT NOT TO ENGINEER

Per instruction, explicitly not to be built from this note alone: 12 personas; 12
micro-lens production routing; a new byline system; a collective CripMinds writer; a
case-library database; a vector store; a disturbance scraper; a sentence-ranking
production model; a new whitepaper version; a new persona-balancing system; an
automatic story-retrieval stage; another production LLM gate. The conceptual branch must
first be tested with cheap, controlled experiments — the three designs above, in
whichever order is chosen after this note is reviewed.

## WHITEPAPER V0.3 TRIGGER

A future v0.3 becomes justified specifically if the engine-before-persona experiment
establishes that the unit of epistemic difference in CripMinds is the perceptual
position, not necessarily the persona. If that result lands, the only clarification
this note anticipates needing is narrow: *"A perceptual position may be embodied by a
recurring writer, combined with other positions, expressed through a collective voice,
or remain publicly unattributed. Editorial architecture must not confuse epistemic
difference with fictional identity."* This sentence is preserved here as a candidate,
not inserted into the whitepaper now.

## ROADMAP CONSEQUENCE

The previously queued sequence (AR3.1 discovery-motion/thesis contradiction, then AR4
`disability_angle` × Fable planning) is not blindly continued by this note. Both remain
valid, well-motivated experiments on the *current* architecture. But the conceptual
questions this note preserves — engine/persona architecture, disturbance discovery,
shared case memory — may be more foundational, since a positive result on
engine-before-persona could change what AR3.1 and AR4 are even testing (a discovery-
motion fix or a `disability_angle` isolation test both currently presume the four-
persona, story-level-discovery architecture). **Experiment ordering is therefore now
open and should be decided after this note is reviewed, not assumed to continue
AR3.1 → AR4 automatically.**

## PROJECT MEMORY

Docs-only. `LOGBOOK.md` entry appended below, per established convention for a material
research-direction branch. `project-manifest.json` not regenerated — same reasoning as
AR1/AR2/AR2.1/AR3 (a git/worktree-topology snapshot with no document-index field this
addition would populate). No change made to `current-work.md`'s FROZEN DECISIONS or any
other production-truth document — this note is additive, pointed to from LOGBOOK only.

---

# FINAL REPORT

**ARTIFACT PATH:** `.claude/experiments/artistic-reset-concept-perceptual-engines-
disturbances-case-memory-2026-08-17.md` (this file).

**WHITEPAPER STATUS: UNCHANGED.** No update required now — see WHITEPAPER V0.3 TRIGGER
for the specific, narrow condition under which one would become justified.

**FOUR-PERSONA STATUS: IMPLEMENTATION HYPOTHESIS**, not doctrine and not superseded.
The whitepaper never mandated four personas; `persona-architecture-audit.md` already
began separating engine from biography/affinity; this note extends that into an
explicitly open architectural question pending the engine-before-persona experiment.

**PERCEPTUAL-ENGINE HYPOTHESIS:** the engine (a portable, disability-derived way of
interrogating reality) may be the fundamental unit of epistemic difference; the
personage (name, biography, wound, voice, state, byline) may be an optional layer
addable after the fact, not a precondition for the engine to work. Not yet tested at
the scale this note proposes.

**DISTURBANCE-DISCOVERY HYPOTHESIS:** the valuable discovery unit may be a fracture
inside an ordinary document (a mismatch, an edge case, a late-arriving fact) rather than
a whole story selected for topical interest — retrospectively consistent with how AR3's
own four sources were actually chosen, though not formally tested as a discovery-stage
principle.

**CASE-LIBRARY HYPOTHESIS:** a pre-built, mechanism-indexed reservoir of real,
documented cases could supply richness honestly, only when an argument requires it,
directly addressing the fabrication mechanism AR2.1 and AR3 both found empirically.
Untested; a small shadow prototype is the proposed first step, not a database.

**BREGMAN CONNECTION:** structural only — a case already in hand before the argument
needs it, not a voice to imitate; consistent with the whitepaper's own framing and this
repo's prior Bregman craft analyses.

**AR3 CONNECTION:** AR3's finding that removing manufactured-testimony pressure cost
nothing and gained modestly on every blind-reviewed measure is the direct empirical
motivation for preferring earned over manufactured richness generally, and for treating
a case library as a way to make earned richness reliably available rather than
occasional.

**NEXT EXPERIMENT OPTIONS:** (1) AR3.1, discovery-motion/thesis contradiction, on the
current architecture; (2) AR4, the `disability_angle` × Fable-planning 2x2, on the
current architecture; (3) the engine-before-persona architecture comparison; (4) the
disturbance-mining comparison; (5) the case-library shadow prototype.

**RECOMMENDED NEXT EXPERIMENT:** the engine-before-persona architecture comparison
(§17-equivalent above), because a positive result would change what AR3.1 and AR4 are
even testing, and because it is cheap (5-6 disturbance fragments, no full essays, no
publication) relative to its potential to redirect the whole roadmap. This is a
recommendation for the next conversation to weigh, not a decision made here.

**WHITEPAPER V0.3 TRIGGER:** only if the engine-before-persona experiment shows the
perceptual position, not the persona, is the load-bearing unit of epistemic difference —
see the candidate clarifying sentence preserved above.

**COMMIT / PUSH:** docs-only, following this document.

**PRODUCTION CHANGES: NONE.**

**Decision: ARC1 — CONCEPTUAL BRANCH PRESERVED; FOUR-PERSONA ARCHITECTURE REMAINS AN
OPEN HYPOTHESIS PENDING ENGINE-BEFORE-PERSONA TESTING.**

Not ARC2: existing canon (`persona-architecture-audit.md`) has already begun separating
engine from persona-biography and already queued a same-source/four-persona probe, but
it does not resolve — and does not claim to resolve — whether four is the right count,
whether authorship should be a late/optional layer, or whether disturbance-level
discovery and a shared case library would outperform the current story-level,
biography-first architecture. No conflict was found between this note and existing
canon; the note extends unresolved threads that canon itself left open, so there is
nothing to report as a contradiction requiring resolution before further experiment.
