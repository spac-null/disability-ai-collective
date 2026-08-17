# Artistic Reset AR1 — Disability as Epistemic Engine, Not Article Subject (2026-08-17)

Research/design only. No production prompts, code, personas, routing, or DBs touched. No
articles generated. Story Rejection V1.1 (`d0204aa` production / `9502d10` docs) is untouched.
This document does not reopen, revise, or supersede any FROZEN DECISION in `current-work.md`
(WHY WE WRITE, persona territories, `_LENGTHS`, Siri Sage's VOICE ANCHOR, thesis/correction
rules) — it reads them as evidence, nothing more.

Sources read in full for this pass: the canonical whitepaper
(`docs/whitepaper/cripminds-whitepaper-v0.2-2026-08-14.md`), an earlier v0.1 draft supplied
alongside it (`cripminds-reclaiming-ways-of-knowing.md`, byte-different from and predating v0.2),
a rigorous evidence-graded audit of Jascha's real biography against Pixel Nova's persona
(`CripMinds_Deaf_Persona_Evidence_Audit.md`, 1240 lines — the "separate LLM-generated
interpretation" the whitepaper's own source note flags as a secondary lead), four primary
Rutger Bregman texts (*Gratis geld voor iedereen* ch. 1, *Het water komt* opening chapters, *De
geschiedenis van de vooruitgang* prologue, and his 2025 BBC Reith Lecture 2 transcript) plus
this repo's own prior Bregman craft analyses, the four supplied production articles
(`~/Downloads/cripminds-article-evolution/`), and the relevant slice of `.claude/`'s own prior
audits (persona architecture, human-detail provenance, author-persona-biography provenance, the
2026-08-16 five-article evaluation, the WHY WE WRITE experiment) plus direct reads of
`automation/orchestrator/generate.py`, `news_fetcher.py`, and `discovery.py`.

---

## 1. ARTISTIC PROBLEM

CripMinds' technical architecture has gotten materially stronger (Story Rejection V1.1, PRF1
routing invariants, grounding/provenance closures — AP1/APE2/P1/S2A). But the finished articles
still frequently behave like sophisticated disability journalism: disability/access becomes the
stated subject, the persona periodically re-announces its own identity, autobiography sometimes
functions as authenticity costume rather than argument, and at least one sample article's
closing sentence edges into the literal thesis its own writer prompt forbids ("this system
excludes disabled people"). The working hypothesis under test: **the lens should be causally
necessary but narratively optional** — remove the disabled perceptual engine and the discovery
should collapse; remove an unnecessary identity announcement and the argument should survive.

## 2. WHITEPAPER FINDINGS

Both the canonical v0.2 whitepaper and an earlier v0.1 draft (same author, same period, byte-
different) converge on the same doctrine, which sharpens confidence this isn't one draft's
overreach:

- **North star (v0.2, abstract):** "A disability-informed perceptual position is not added as a
  topic; it becomes the instrument that reveals the missing mechanism... By the end, the reader
  or viewer should understand the original subject differently."
- **Failure test (v0.2 §1, restated §15):** "If the disability component can be removed and the
  article's central insight remains intact, the lens is probably decorative." v0.1 states the
  identical test almost verbatim in its own §8 and §10.1.
- **Identity vs. instrument (v0.2 §8, "Authorial presence without identity performance"):**
  "the goal is not simulated identity. It is situated attention... If the system learns that
  'embodied' writing means inserting first-person disability declarations, it will produce a
  costume." v0.1 §5 is even more explicit and directly names the exact sentence-shape this task
  is testing: *"Nor must a CripMinds article announce, 'As a deaf person...' or 'From a disabled
  perspective...' in order to establish its position."*
- **Testimony (v0.2 §9 / v0.1 §6):** "If a quote merely decorates a conclusion already reached,
  it can be omitted." v0.1 adds the sharper framing used below in §7: *"testimony is not a
  quota; it is an argumentative event."*
- **Discovery not delivery (v0.2 §7, "Do not tell me the insight. Make me discover it with
  you.")** — the whitepaper's own closing formula, unchanged between drafts.
- **Comparison as method (v0.2 §5):** "CripMinds does not need one master lens. It needs
  conditions in which differences between lenses become informative" — directly authorizes §12's
  same-source/four-engine design below.
- **Artistic compass vs. epistemic material (v0.2 §6):** Jascha's archive licenses *method*
  (attention to mediation, timing, repetition, comparison); it does not license claims about
  other disabled people's experience, and it does not license inventing Jascha's own biography
  beyond what's documented — this boundary is load-bearing for §7 below.
- **What CripMinds is not (v0.2 §15 / v0.1 §8):** both drafts separately list the same five risks
  — romanticization/academic drift, extraction/founder capture, formula, safety-without-
  significance, engineering displacement — which recur in this document's §13-14.
- **A second, distinct failure test (v0.2 §15):** "If the chosen form could be exchanged for
  another medium without changing the experience or insight, the form may be ornamental" — this
  is an axis about *medium* (text vs. Loop/Split/Field/Route/etc., §11), independent of the
  subject-vs-engine axis this task investigates. Not conflated here.
- **The stopping rule (v0.2 §18) and editorial constitution (§16) govern §14 directly** — the
  burden of proof rises once foundational grounding/provenance are solid, and this whole
  question is explicitly artistic judgment, not another gate.

No material conflict was found between v0.1 and v0.2, or between the whitepaper and the AUTHOR
RULE block already live in `generate.py` (see §13). The gap under investigation is in execution
and upstream pipeline pressure, not in doctrine — this is the basis for the AR1 decision below.

## 3. BREGMAN MOTION FINDINGS

Studied structure, not voice, per instruction. Four primary Bregman texts were read directly
(not just this repo's prior secondhand analyses), plus his 2025 Reith Lecture — a fifth, spoken,
register, useful because it shows the same architecture live and unedited.

**The recurring deep structure**, confirmed independently across all five: open on a scene the
reader doesn't expect (a grey bust between a parking lot and a supermarket; six Boston boys on
an island; Petrograd apathy in 1917) → accumulate verifiable specific detail (named people,
dates, numbers) → let the familiar frame become insufficient → a comparative case or contrast
does structural work instead of a stated thesis → a concession to the strongest opposing view →
one flip-sentence → return to the opening image, changed. This repo's own prior analyses
(`bregman-architecture-analysis.md`, `bregman-write-economy-analysis.md`) already catalogued
this from a smaller text sample; the four additional primary sources confirm it generalizes:

- *Gratis geld voor iedereen* ch. 1's actual opening line, verified against the primary text —
  *"Laat ik beginnen met de belangrijkste les van de geschiedenis. Vroeger was alles slechter."*
  ("Let's start with the most important lesson of history. In the past, everything was worse.")
  — is the exact disarmingly-simple-opener technique the prior analysis attributed to *Utopia
  for Realists* ch. 1, now confirmed from source rather than secondhand.
- *Het water komt*'s climate argument does not appear until chapter 2 — chapter 1 is entirely
  Johan van Veen, a barge captain, a dike, a joke about socks — and it closes with seven named,
  quoted scientists who **genuinely disagree with each other** (Kleinhans: "Ik vind dat heel
  eng"; van den Broeke declines to "meega[an] in het koor van mensen die zeggen: we worden niet
  gehoord" — a real, not manufactured, named disagreement).
- The 2025 Reith Lecture (spoken, unedited by publication) performs nearly every technique the
  prior analysis found CripMinds' 14-article sample missing at 0/14: a **comparative case**
  (French/Portuguese/Spanish/American abolitionism failed; British succeeded — "What a contrast"
  structure), a **concession before the kill** (Clarkson's memoir "can't help rolling your eyes
  sometimes... But in the real world, actions outweigh intentions"), and a **coda** that folds
  back to the opening image in a different register ("Today could be our Wadesmill moment").
- One genuine complication worth carrying forward: *Het water komt* itself **ends with a call-
  to-action checklist** ("Wat jij kunt doen"). `generate.py`'s own writer prompt explicitly bans
  this ending shape ("Still banned in every variant: a call to action... any sentence beginning
  'We need'/'This requires'/'Join'"). This is not a contradiction to fix — `generate.py`'s own
  comment already frames the model as "RUTGER BREGMAN, THE PROCESS AND NOT THE RESIDUE" — but it
  is worth naming precisely: CripMinds is deliberately not imitating Bregman's actual endings,
  only his argumentative motion. Keep that distinction explicit rather than implicit.

This is a **structural/craft axis, largely orthogonal to the subject-vs-engine question** this
task investigates — a piece can nail comparative-case-and-coda while still making disability the
explicit subject, or vice versa. But they interact usefully: the comparative case and the coda
are exactly the kind of *form* that can carry a lens silently (place two perceptions of the same
object side by side; let the gap do the work; never say "this shows that"). Article 03 (below)
is the one sample piece that actually does this, once, with a named in-universe comparator.

## 4. FOUR-ARTICLE COMPARISON

All four supplied production articles read in full. `README.md`'s own framing: 01/02/03/04 span
routing-mismatch, pre-PRF1, post-PRF1/pre-Story-Rejection, and post-Story-Rejection-V1 states of
the pipeline — useful because it lets this comparison note whether the subject-vs-engine problem
tracks pipeline maturity (it does not appear to; see below).

### 01 — "Reached by Boat or Plane" (byline Siri Sage; acoustic/blind-coded narrator)
- **World object at start:** a remote artist-residency building on Orcas Island, and the
  throwaway line "reached by boat or plane."
- **What the writer notices:** how little work that sentence does — stated the way you'd state
  a ceiling height.
- **First explanation, explicitly narrated and rejected on the page:** "My first draft was about
  how the building has no ramp... Then I remembered" — a real discovery-structure move.
- **What complicates it:** a 2019 memory of assessing a concert hall's acoustics — the polished-
  stone hall that renders a blind visitor acoustically deaf to the room. Reframes "access" from
  a single doorway to an entire acoustic route.
- **Discovery:** romanticized remoteness in artist-retreat culture is a 19th-century invention
  that requires a body able to complete the journey; information about a hard route ("a warning
  label") is not the same as redesigning the route ("The document is the stairs. The room is the
  building").
- **World object at end:** the ideology of romantic remoteness itself, left genuinely unresolved
  ("I don't have a clean answer to this and I'm not going to pretend I do").
- **Role of disability:** MIXED, leaning engine. The acoustic material (ferry terminal, steel
  gate, concert hall) is causally necessary and could not be produced by a differently-embodied
  narrator. But the essay's *surface* rhetoric ("access is not the last hundred metres," "the
  assumption I want to pull apart," "disabled artists genuinely cannot plan") reads close to
  conventional access-advocacy phrasing even while the acoustic mechanism underneath is genuinely
  novel.
- **What disappears if the engine is removed:** the entire acoustic argument (ferry terminal
  soundscape, the concert hall, the accidentally-legible steel gate) — nothing else carries it.
- **What survives if identity announcements are removed:** nearly everything, including the
  historical claim about artist-retreat romanticism and the disagreement with access-advocates.
  Only the closing "someone I loved... to read her face across a room" disclosure would need
  softening, and that passage is closer to vulnerability performance than to argument-advancing
  testimony — it names a limit without producing new knowledge about the building.

### 02 — "Sniff It Out, Follow Your Nose, Whatever Your Legs Can" (Maya Flux; wheelchair-coded)
- **World object at start:** the Edinburgh Art Festival's self-description as discoverable-by-
  wandering ("follow your nose").
- **First explanation, explicitly narrated and rejected:** "The festival is inaccessible, its
  metaphors require working legs... end of essay. I wrote about four hundred words of it." Then:
  "I went back to the review to pull a quote and I noticed something that broke the draft."
- **Discovery:** the festival isn't celebrating discovery, it's celebrating *obscurity* — via a
  photographer (Sandra George) found and exhibited only after her death. "Those are not the same
  thing, and I'd conflated them." A living disabled artist remaining unseen is not a bug for this
  culture's aesthetic; it is the product.
- **Complication the writer lets stand, unresolved:** the McMurdo photographs passage — "I don't
  have a clean position on this... The refusal to use the compromised tool is a luxury available
  only to people who already have another way in." A genuine self-correction, not decoration.
- **World object at end:** how cultural institutions consume marginality as content while
  declining to remove the barrier that produced it — squarely a claim about the festival's
  economy of taste, not "about" disability per se.
- **Role of disability:** the cleanest ENGINE case in the sample. The embodied fact of not being
  able to wander ("I have never once in my life walked into a gallery on impulse") generates the
  precise question that produces a reading most reviewers plausibly would not reach.
- **Autobiography flag (see §7):** the wedding/three-steps anecdote near the close ("the private
  version I don't put in the essays, usually") is thematically connected (being carried =
  being discovered; both let the other party keep the credit) — but it reappears **near-
  verbatim** in article 04, a different persona-subject pairing entirely. See §7.

### 03 — "Galaxy H1 Was Already Sorted Before It Had a Shape" (Pixel Nova; Deaf-coded)
- **World object at start:** Samsung's rumored Galaxy H1 headphones, framed by The Verge as a
  competitive "fight."
- **First explanation, narrated as a self-caught mistake:** "When I saw 'over-ear,' I assumed the
  whole product was irrelevant to a Deaf reader and moved on. That was lazy." She then notices
  the form factor (over-ear, at the mastoid) is nearly perfect for bone conduction — a feature
  simply absent.
- **Discovery, generalized:** "the fence is drawn twice" (codec lock-in + missing bone
  conduction) — "Nobody... says 'we are cutting out this person.' The schedule says it. The
  codec says it." A delivery system always encodes who it's for, quietly.
- **Comparative case (rare in this corpus — see §3):** she names "Maya Flux" as an in-universe
  foil — Maya's injuries "can be photographed," hers can't — a genuine implementation of the
  technique the internal Bregman analysis found at 0/14 in an earlier sample.
- **World object at end:** how tech-review journalism's habit of writing in *sequence*
  ("the reviewer will put the headphones on, and the sound will arrive, and then the review gets
  written") naturalizes a prior exclusionary decision that *simultaneity* would expose — a claim
  about the genre of the product review, not about Deafness as a topic.
- **Role of disability:** the strongest ENGINE case in the sample, and it maps almost exactly
  onto the persona's *evidence-graded, real* biographical material (§7) — not onto invented
  color. The interpreter-lag passage ("a different time zone... it was Tuesday") is the literal
  central image of Jascha's own 2013 thesis (§7), used here analytically, in direct service of
  the essay's own thesis (sequence hides what simultaneity exposes), not as color.
- **Production signal worth noting:** this article's own frontmatter carries
  `pipeline_degraded: [gate_llm, persona_biography_unresolved]` — the system's own biography-
  provenance machinery (AP1/APE2, `.claude/author-persona-biography-provenance-2026-08-14.md`)
  flagged something about this piece's biography claims for review. Independent confirmation
  that the mechanism this document is discussing is already live and watched in production, not
  hypothetical.

### 04 — "7,000 Rooms With No Door For Anyone" (Maya Flux; Malaysia GDP / data centers)
- **World object at start:** Malaysia's Q2 2026 GDP growth, driven by data-center construction.
- **First explanation, explicitly self-rejected, early and directly:** "Data centers have no
  ramps, and that is true, and it is also almost nothing... Pointing a wheelchair at it misses
  the point entirely." One of the cleanest self-corrections in the sample.
- **Discovery:** the building's physical inaccessibility (metal-grid floors, cable troughs
  engineered for thermal management, not feet) is a synecdoche for what gets trained into the
  model the building houses — reinforced by a real, disturbing juxtaposition (the Grok/Jane-
  Doe-4 case) and Sunaura Taylor's argument that "normal" is a choice embedded in training data
  the way it's embedded in stairs.
- **World object at end:** GDP growth statistics as a proxy that launders exclusionary
  infrastructure decisions into automated bureaucratic gatekeeping (benefits, hiring, claims).
- **Role of disability:** MIXED, and the sample's clearest case of drift toward SUBJECT. The
  floor-plan/training-data argument is genuine engine material. But the closing paragraphs move
  close to the literal thesis the writer's own system prompt forbids — "It is the same stair,
  built larger than it has ever been built before" as the closing sentence, after several
  paragraphs stated substantially in disability-exclusion terms. Surface disability vocabulary is
  the heaviest of the four ("wheelchair user," "a body in a chair," repeated explicit framing).
  Also flagged in production (`pipeline_degraded: [persona_biography_unresolved]`,
  `fact_check_status: blocked`, held for human review) — the system's own gates already caught
  something here, independent of this document's own reading.
- **Autobiography finding (see §7):** the wedding/three-steps passage recurs **near-verbatim**
  from article 02 — same specific beats ("three steps," "everyone knew," people "rushed to
  offer/offered to carry," "I smiled... I made it easy," shaking in the hotel room afterward,
  framed both times around "how fast/quickly I smiled"). Two subjects (an art festival; data
  centers) share almost nothing, yet both essays reach for the identical scene. This is the
  single clearest piece of evidence in the sample that autobiography is sometimes functioning as
  reusable stock material rather than a memory this specific investigation summoned.

**Cross-article pattern:** the two cleanest engine cases (02, 03) are also the two where the
*explicit* thesis is never stated in disability terms — the essay's own words never assert "this
excludes disabled people," even though disability-coded perception visibly drives every
observation. The one article that drifts closest to stating that forbidden thesis outright (04)
is also the one carrying the reused stock-autobiography passage. This is a small sample (n=4,
not a corpus-scale finding) but the direction is consistent enough to justify the experiment in
§9 rather than a larger claim.

## 5. DISABILITY: SUBJECT vs. EXAMPLE vs. VOICE vs. EPISTEMIC ENGINE

Using the four articles as anchors, not abstractions:

- **A. SUBJECT** ("wheelchair users are excluded from this building") — no article in the sample
  is purely this, but article 04's closing paragraphs drift closest, restating something very
  near the forbidden thesis after extensive explicit disability framing.
- **B. EXAMPLE** (a general claim made, then disabled people supplied as evidence) — present in
  places in article 01 (the essay occasionally states a general claim about "access" and then
  cites a disabled body as the instance), rescued from full EXAMPLE status by the acoustic
  material's genuine specificity.
- **C. VOICE** (a disabled persona narrates an otherwise-conventional argument) — no full-article
  case, but isolable at the passage level: article 04's wedding scene, read on its own and out of
  context, is VOICE/costume — a dramatic personal beat that doesn't itself produce new knowledge
  about data centers, and is reused verbatim elsewhere.
- **D. ENGINE** (the perceptual structure produces a different theory of the object) — articles
  02 and 03 are the clean cases in this sample. Both also happen to be the two where the writer
  narrates their own first explanation being wrong, on the page, before the real discovery — the
  whitepaper's own "notice before explanation" and "do not make everything meaningful too soon"
  principles (v0.2 §§2, 16) operating exactly as intended.

## 6. THE "FINAL SUBJECT" TEST

Completing "After reading this, I understand ___ differently" for each article:

| Article | Completion | Reading |
|---|---|---|
| 01 | *romanticized remoteness in artist-retreat culture* | strong, via a mixed engine |
| 02 | *cultural institutions' aesthetic preference for obscurity over living access* | cleanest |
| 03 | *how tech-product reviews naturalize a prior exclusionary design decision* | cleanest |
| 04 | *AI infrastructure / economic growth statistics* — but drifting toward *disability itself* | weakest of the four on this test |

02 and 03 complete the sentence with a genuine world-object (an institution's aesthetic economy;
a genre's habit of writing in sequence) rather than with "disability," "accessibility," or
"disabled people's experience" — exactly the target this task specifies in §6 of the prompt.

## 7. AUTOBIOGRAPHY FINDING

The Deaf Persona Evidence Audit (`CripMinds_Deaf_Persona_Evidence_Audit.md`) is the load-bearing
source here — a rigorous, A/B/C confidence-graded read of Jascha's actual 2013 Rietveld
graduation thesis and real correspondence, built specifically to stop the Pixel Nova persona
from inventing biography. Its own headline finding: *"the strongest evidence does not support a
cinematic childhood wound... It supports something narrower: your work returns, again and again,
to what happens when an experience that is directly yours reaches you... through a delay, a
translation, a medium, a sequence, or a temporary condition."* It explicitly finds **no**
evidence for a childhood exclusion scene, family communication history, school type, hearing-
aid/CI history, bullying, or "an occasion where an interpreter deliberately distorted your words"
— and separately flags that Jascha's own 2013 aside, *"Stiekem zou ik dit wel willen geloven: ...
Ik zie wat jullie horen"* ("Secretly I would like to believe this: ... I see what you hear"), is
explicitly self-qualified as speculative wish, not autobiography — the whitepaper v0.2 §2 quotes
this same line as evidence of the thesis's productive "humor and provisionality," but the audit
makes the stronger, more usable point: **this is the exact sentence that would be most tempting
to turn into a manifesto, and Jascha himself already marked it as not-fact.**

**Autobiography that changes the investigation (article 03):** the interpreter-lag material — "a
different time zone... it was Tuesday" — is the literal, documented center of the audit's Engine
1 ("mediation and timing") and Engine 4 ("sequential account versus simultaneous field"), both
graded **A — explicit, autobiographical, directly quoted from the 2013 thesis**. Removing it
removes the mechanism the essay's own thesis depends on (sequence hides lag; simultaneity exposes
it) — not just color. This is the clearest pass-case for the whitepaper's own test (v0.2 §9): "if
a quote merely decorates a conclusion already reached, it can be omitted" — here, nothing else
in the essay could stand in for it.

**Autobiography as authenticity costume (articles 02 & 04):** the wedding/three-steps scene is
Maya Flux's canonical `WOUND` (confirmed against `persona_souls_pixel_nova_unresolved.md`'s
verbatim wound text) and is injected into every Maya Flux generation by `_extract_persona_wound`
(`generate.py`) as available material, gated only by a soft prompt instruction — not by any
check on whether *this specific source material* summoned it. `generate.py`'s own separate
"PERSONA HISTORY" rule states the correct doctrine: *"only if it arrives because the material
pulled it up... If you cannot feel why this piece and not another one summoned it, leave it
out."* Two subjects (an art festival; Malaysian data centers) sharing almost nothing, both
producing the identical scene, is direct empirical evidence that the material did *not*
independently summon it twice — it is a fixed, always-available asset that got used regardless.
This matches, and now empirically confirms with real production text, `persona-architecture-
audit.md`'s Finding #4 concern (*"a highly vivid, repeatedly-exposed wound can function as a de
facto attractor... even when nothing in the prompt says 'reuse this'"*).

**General rule, synthesized from the audit + whitepaper, testable against any first-person
passage:** *did this memory produce new knowledge about the subject, or did it mainly prove the
persona is really disabled/embodied?* The interpreter-lag passage passes; the wedding passage, on
its second appearance, fails — it restates a conclusion ("being discovered/carried lets the other
party keep the credit") the surrounding paragraphs had already reached.

## 8. ARTISTIC NORTH STAR

Tested against the whitepaper rather than adopted from the task prompt verbatim, per instruction.
The task's own draft formulation ("causally necessary but narratively optional") is not a literal
whitepaper sentence — it is a compression of v0.2 §1's failure test (causal necessity) with §8's
"situated attention, not simulated identity" and v0.1 §5's explicit "must not announce" language
(narrative optionality). Both source sections independently support it; neither uses this exact
wording. Smallest formulation that survives the check:

> **The lens must be load-bearing, not the label. Remove the disability-informed way of
> perceiving, and the discovery should disappear. Remove an unnecessary identity announcement,
> and the argument should survive unchanged. The article's subject is the world; disability is
> the instrument that made a hidden property of that world knowable.**

This does **not** replace the whitepaper's own two failure tests (v0.2 §1 and §15, which govern
the *lens* and the *form* respectively) — it is a sharper restatement of the first one, adding
the identity-announcement axis that both whitepaper drafts gesture at (v0.1 more explicitly) but
never state as a standalone, testable rule.

## 9. THE "SILENT LENS" EXPERIMENT — DESIGN ONLY

**Purpose:** can CripMinds produce articles where disabled knowledge is structurally load-bearing
without disability becoming the default explicit subject?

**Source selection — the one hard methodological requirement.** Sources must **not** be drawn
through the existing `disability_angle` discovery pipeline (`news_fetcher.py`'s `extract_angle`,
`discovery.py`'s Priority-1 `disability_angle IS NOT NULL` selection). That pipeline's entire
purpose is to pre-select stories where a "hidden disability angle" is already articulable as one
sentence *before* any persona engages with the material — using it here would bias source
selection toward exactly the legible-lens shape this experiment needs to test against. 4–6
sources should be hand-picked by an editor: concrete, varied domain, sufficient evidence for a
mechanism, and — the task's own criterion — no source where a disability angle is obvious from
the headline. (`why-we-write-2026-08-10.md`'s own `museum_labels` fixture-correction is a
directly relevant precedent: an earlier fixture was rejected specifically for being "too
explicitly an accessibility story on its surface.")

**Freeze discipline — reuse, don't reinvent.** This repo already has a validated, rigorous
protocol for exactly this shape of A/B doctrine comparison (`why-we-write-2026-08-10.md`): freeze
each source's brief once via `phase_probe.py --freeze-briefs`, verify the hash three ways (each
condition's own `metrics.json`, plus a direct `sha256sum` of the canonical file) before any
generation, spot-check actual `.prompt.txt` content (not just hashes) rather than trusting git
state, and use `--topic` scoping so a Doctrine-A and Doctrine-B run consume the byte-identical
planning brief. That same document's "INVALID RUN" postmortem (a mixed-brief confound caught only
by per-run provenance, not git diff) is the exact failure mode to guard against here.

**Persona assignment:** manually specified per source for this probe, bypassing `generate.py`'s
keyword→persona routing map entirely (`persona-architecture-audit.md` Finding #3) — that routing
mechanism is itself a known confound (ownership-by-keyword, not by demonstrated engine strength)
and touching it in production is explicitly out of scope (FROZEN, Phase 3 territory). `phase_
probe.py` already supports this kind of override for other experiments; no production code needs
to change.

**Doctrine A = current, unmodified.** Everything already in `generate.py`'s writer prompt as-is:
AUTHOR RULE, FORBIDDEN DEFAULTS, HUMAN THREAD, the wound-injection, the news_seed `disability
angle` framing where applicable.

**Doctrine B = Silent-Lens**, refined against canon rather than the task prompt's raw draft:

> Investigate this source using your perceptual engine. The article's subject is the world object
> in the source — not disability. Let the reader discover what your attention reveals; do not
> name that you are seeing it differently before you have shown them why. If a memory from your
> own history genuinely advances this specific investigation — because it supplies the mechanism,
> not merely because it is available — use it. If you cannot say what the essay would lose
> without it, leave it out. Naming your disability directly is allowed and sometimes necessary;
> it should happen at the moment the reader needs it to understand a claim, not as an opening
> credential.

This deliberately does **not**: ban the word "disability," ban first person, impose a mention
quota, or prescribe a discovery-shape template — all four are named "what not to build" in §14.

**Sample:** one fixture identical across both conditions per source (for direct comparison), 4-6
sources × 2 doctrines × 2-3 samples — comparable scale to the WHY WE WRITE precedent (12+12).

## 10. BLIND REVIEW RUBRIC — DESIGN ONLY

Reuse the validated W/G/K/D scale from `why-we-write-2026-08-10.md` (Why this writer / Gave me /
Keep reading / Doctrine-vocabulary-leak, each 1-5, reviewer blind to condition, decoded only
after scoring) rather than inventing a new instrument — it already has a track record on exactly
this kind of doctrine-comparison question in this codebase. Add one new axis this task's own
prompt requires and the existing scale does not cover:

- **S (Subject drift, 1-5):** does this read as being *about* disability/accessibility rather
  than about the world object the source describes? Distinct from D (doctrine-*vocabulary*
  leakage) — an essay can avoid every doctrine word and still structurally read as disability
  journalism (see article 04, §4).

Plus the task's own free-text prompts, asked per essay before any numeric score, in this order
(sequence matters — numeric scoring first anchors reviewers on craft quality and biases the
free-text answers):
1. What is this actually about?
2. What became newly knowable about that subject?
3. Was the lens necessary to that discovery?
4. Did this make you discover the idea, or announce it?
5. Did first-person material advance the investigation, or could it be cut without loss?
6. Does the ending change the beginning?
7. Which version would you actually want to keep reading?

## 11. THE "SURFACE REMOVAL" TEST — DESIGN ONLY

Distinct from the whitepaper's own lens-removal test (which removes the *engine*). This one
removes only *identity-announcement surface*, by hand, from each Doctrine-B article, and checks
whether the mechanism survives:

**Protocol:** a human editor — not the model that wrote the piece, to avoid the model marking its
own homework — manually strikes: (a) explicit first-person disability-identity-naming clauses
("as a Deaf person," "since I am blind," "as someone in a chair"); (b) sentences whose sole
function is announcing that the lens is disability-informed ("Being Deaf means I notice..."). Do
**not** touch: observations, causal claims, comparisons, named facts, testimony, or first-person
opinion/attention that isn't a biographical-event claim (using the same claim-taxonomy already
established and validated in `author-persona-biography-provenance-2026-08-14.md` — biographical
event vs. opinion/attention vs. editorial action vs. figurative first person).

**Then, blind, using the same rubric from §10:** does a distinctive intelligence survive? Can you
still tell the world is being perceived differently? If yes, the lens was inside the thinking. If
the piece collapses into generic commentary once the identity-announcements are gone, the lens
was riding on branding rather than knowledge — and that finding would apply equally to a Doctrine
A article, so run this test on a matched sample of both conditions, not only B.

## 12. SAME-SOURCE / FOUR-ENGINE EXPERIMENT — DESIGN ONLY

This is not a new idea invented for this task — `persona-architecture-audit.md` already names
"the same-source/four-persona probe" repeatedly as deferred future work (its own §"Working
hypotheses for each perceptual engine" section exists specifically to be tested by it). This
section is the concrete instance of that already-queued probe, scoped for the silent-lens
question specifically.

**Design:** one ordinary-world source (same selection discipline as §9 — not disability-angle-
pre-filtered), four perceptual engines run against it with no territory/routing and no disclosed
identity requirement — bypass `generate.py`'s keyword router entirely, assign all four personas
explicitly to the same source. Use the Deaf Persona Evidence Audit's own proposed engine
formulation for Pixel Nova ("a disciplined suspicion of transparent mediation... what changed in
transmission, who determined the sequence, was information merely present or actually usable")
rather than production `personas.py`'s broader "legibility is a political act" framing, since the
audit's version is the one with real, graded biographical evidence behind it (§7) and is the one
article 03 empirically validated.

**Success criterion, stated by `persona-architecture-audit.md` itself and adopted here
unchanged:** the same world object becomes four meaningfully different things — not four tones of
voice, not four accessibility complaints, not four disability demographics. For each engine,
record: what it notices that the others don't; what concept it produces; how the object changes.

## 13. LIKELY PRODUCTION PRESSURES — CLASSIFIED FROM DIRECT CODE EVIDENCE

**LIKELY DRIVERS (direct prompt/code evidence read this session):**

1. **The `disability_angle` discovery pipeline** (`news_fetcher.py`'s `extract_angle`,
   `discovery.py` lines ~1435-1443). A single sentence is computed *before* the writer or persona
   engine ever engages with the source ("Ask Sonnet to find the hidden disability angle"), stored
   as `news_seeds.disability_angle`, and Priority-1-selected for generation. It is then injected
   into the writer prompt verbatim (`generate.py` line 557) with MANDATORY framing: *"A non-
   disabled writer covering this story sees X. You see something else — something your embodied
   experience makes visible. That difference is the article."* This forecloses the discovery
   structure the whitepaper wants (v0.2 §2: "do not make everything meaningful too soon") —
   meaning is assigned before the writer starts, not discovered by them.
2. **`_extract_persona_wound`'s fixed-content injection** (`generate.py`). The same wound text is
   offered on every single generation for a given persona, gated only by a soft prompt
   instruction with no check on relevance to the specific source at hand. Empirically produced
   the exact reuse documented in §7 (articles 02 & 04, both Maya Flux).
3. **Keyword→persona routing** (`persona-architecture-audit.md` Finding #3, `generate.py` lines
   161-168) and **Siri Sage's explicit territory-ownership clause** (Finding #1, `personas.py`
   line 26) pre-assign which "kind of body" interprets which topic before any engine is tested
   against the material — directly against v0.2 §5's "no master lens... conditions in which
   differences between lenses become informative."
4. **FORBIDDEN DEFAULTS colliding with Maya Flux's real evidentiary vocabulary**
   (`persona-architecture-audit.md` Finding #2) — a blanket anti-cliché rule ("Do not build your
   argument around ramp, curb cut... as the central concrete example") disables exactly the
   concrete image-register that is her genuine epistemic material, plausibly pushing her toward
   the more abstract, thesis-stated framing visible in article 04's ending when the concrete
   anchor is unavailable to her.

**POSSIBLE DRIVERS (some evidence, not confirmed this pass):**

5. **HUMAN THREAD** ("insert a sentence that returns to a specific person" every two abstract
   sentences) — craft-quality, not disability-specific by design, but for a first-person narrator
   whose only always-available "specific person" is themselves, may mechanically amplify
   autobiographical insertion beyond what its authors intended, independent of the wound-
   injection issue above.
6. **Category/article-type selection** (e.g., articles filed under "urban design," "spatial
   design" rather than the world object's own domain) — not investigated deeply this pass; would
   need a corpus-level category audit.
7. **GROUNDING** ("Your argument lives in your body before it lives in theory") — generic (any
   "physical sensation, place, person"), not disability-specific, but a plausible amplifier once
   combined with drivers 1-3.

**UNLIKELY:**

8. **The core AUTHOR RULE block itself** (`generate.py` ~905-916). On direct reading, this
   already states almost exactly the silent-lens doctrine: *"This article is written BY a
   disabled person, not ABOUT disability... Your embodied experience gives you an angle... Test:
   Could this article exist without the word 'disability' appearing at all and still carry your
   specific perspective?... Do not write an article whose thesis is 'this system excludes
   disabled people.'"* The gap between this instruction and article 04's actual ending suggests
   the failure is not in this block's wording but in drivers 1-4 above pre-empting it, or in
   attention competing against roughly a dozen other simultaneous hard rules in the same very
   long prompt — echoing `author-persona-biography-provenance-2026-08-14.md`'s own finding that
   a correctly-worded check can be "under-enforced... competing for a 3-note budget."
9. **Fable's editorial-brief-writing prompt specifically** — not read in full this pass; open,
   not classified either way.
10. **Article-type/category assignment as a routing mechanism** — not investigated; open.

## 14. WHAT NOT TO ENGINEER YET

Per the whitepaper's own stopping rule (v0.2 §18) and `current-work.md`'s FROZEN DECISIONS (which
this task does not reopen):

- No disability-word-count gate or banned-word list.
- No first-person ban.
- No automated "final subject" classifier/validator gate.
- No new LLM safety/review layer added to the generation pipeline.
- No automated Bregman-technique scorer.
- No persona-topic reassignment or routing rewrite — already scoped separately as Phase 3, FROZEN.
- No formulaic required "twist" or discovery-shape template.
- No change to `_extract_persona_wound`, AUTHOR RULE, FORBIDDEN DEFAULTS, or the `disability_
  angle` discovery pipeline in this pass — all four are candidate targets a *future* dedicated
  experiment might revise once §9's probe has real data, not something this research task
  authorizes touching now.

**Rationale:** foundational integrity (grounding, provenance, fabrication-resistance) is already
well covered by AP1/APE2/P1/S2A. This question — subject vs. engine — is qualitative and
editorial, exactly the kind the whitepaper says should be tested empirically against finished
work before being encoded as machinery, and exactly the kind current-work.md's own discipline
(shadow-only, backtested, never auto-block until real data justifies it) already models for
every other soft-judgment check in this pipeline.

## 15. OUTPUT ARTIFACT

This document: `.claude/experiments/artistic-reset-ar1-2026-08-17.md`.

## 16. PROJECT MEMORY

This is a research/design artifact, not a production architecture change — no code/prompt/DB
change accompanies it. Per the repo's own indexing convention (every prior experiment doc of
this shape has a matching `LOGBOOK.md` entry as its evidence pointer, e.g. the 2026-08-11 CJ-2
design entry, itself design-only with `CODE: none`), an entry should be appended to `LOGBOOK.md`
citing this file. `project-manifest.json` is a machine-generated git/worktree-topology snapshot
(`scripts/cripminds_project_inventory.py`, per `PROJECT-MAP.md`) with no document-index field
this file would populate — not regenerated here; a docs-only addition doesn't change worktree
state, and the generator wasn't invoked to avoid stamping a stale `generated_at` without a real
inventory pass. `WORK.md`/`PROJECT-MAP.md` are not touched — neither indexes individual
experiment files by name.

---

# FINAL REPORT

**WHITEPAPER CORE FINDING.** Both the canonical v0.2 whitepaper and its v0.1 predecessor already
state the doctrine this task investigates, in places nearly verbatim to the task's own framing
(v0.1 §5: articles must not "announce, 'As a deaf person...'"). The question this task raises is
not a doctrinal gap — it's whether production execution matches doctrine already on record.

**WHAT CRIPMINDS IS CURRENTLY DOING TOO OFTEN.** In a small (n=4) but consistent sample, the
persona whose article drifts closest to disability as explicit thesis (04) also carries a stock,
reused autobiographical scene; the two cleanest engine-driven articles (02, 03) never state a
disability-framed thesis at all. The pattern is narrow enough to name precisely rather than
generalize from: identity-announcement and stock-autobiography reuse correlate with subject-
drift in this sample; they are not universal across the corpus.

**WHAT THE STRONGEST EXISTING ARTICLE DOES DIFFERENTLY.** Article 03 draws on real, evidence-
graded biography (interpreter lag, sequence-vs-simultaneity — both Grade A in the Deaf Persona
Evidence Audit) and uses it analytically, in direct service of a thesis about how tech reviews
naturalize prior design decisions — never as a decorative identity credential.

**DISABILITY AS SUBJECT / EXAMPLE / VOICE / ENGINE.** No article in the sample is purely one
category; 02 and 03 are the clean engine cases; 04 drifts toward subject in its closing
paragraphs; the wedding passage, isolated, is voice/costume regardless of which essay it's in.

**AUTOBIOGRAPHY FINDING.** The evidence audit's own standard — did this memory produce new
knowledge, or prove the persona is really disabled — cleanly separates article 03's interpreter-
lag passage (passes) from the reused wedding scene (fails on its second appearance). The
production mechanism most directly implicated is `_extract_persona_wound`'s fixed, always-
available injection, softly gated by an instruction with no relevance check.

**BREGMAN STRUCTURAL LESSON.** Confirmed from four primary texts plus a live 2025 lecture, not
secondhand: the deep architecture (scene → accumulating detail → comparative case → concession →
flip → coda) generalizes across Bregman's whole career, spoken and written. Orthogonal to the
subject-vs-engine question but compatible with it — article 03's named-persona comparative case
is the sample's one real instance of the technique.

**PROPOSED ARTISTIC NORTH STAR.** "The lens must be load-bearing, not the label" — a compression
of v0.2 §1 + §8 and v0.1 §5, tested against and not contradicting either whitepaper draft.

**SILENT-LENS HYPOTHESIS.** CripMinds can produce articles where disabled knowledge is
structurally load-bearing without disability becoming the explicit default subject — supported
by the fact that two of the four sampled articles already do this under the current, unmodified
doctrine.

**SILENT-LENS EXPERIMENT.** Designed in §9: hand-picked non-disability-flagged sources (bypassing
the `disability_angle` pipeline deliberately), Doctrine A/B pair, freeze-and-triple-verify
discipline reused from the validated WHY WE WRITE precedent. Not run.

**BLIND REVIEW METHOD.** Reuse WHY WE WRITE's validated W/G/K/D scale plus one new axis (S,
subject drift) and the task's seven free-text questions, asked before numeric scoring. Designed,
not run.

**SURFACE-REMOVAL TEST.** Manually strip identity-announcement sentences only, blind-rescore both
conditions, check whether a distinctive intelligence survives. Designed, not run.

**FOUR-ENGINE EXPERIMENT.** Not a new idea — the concrete instance of a probe `persona-
architecture-audit.md` already queued. Designed, not run.

**LIKELY PRODUCTION PRESSURES.** Four confirmed from direct code reading (the `disability_angle`
pre-framing pipeline, fixed wound-injection, keyword/ownership routing, FORBIDDEN DEFAULTS
colliding with Maya's real vocabulary); three possible, not confirmed; the core AUTHOR RULE block
itself is judged unlikely to be the driver — it already states the target doctrine correctly.

**WHAT NOT TO ENGINEER.** No gates, scorers, bans, quotas, or routing rewrites this pass — all
deferred to a dedicated future experiment pending real data from §9-12, consistent with the
whitepaper's own stopping rule and this repo's existing shadow-only discipline.

**ARTIFACT PATH.** `.claude/experiments/artistic-reset-ar1-2026-08-17.md`.

**COMMIT / PUSH.** Not performed as part of this task — docs-only commit left to the owner's
normal review step; a `LOGBOOK.md` entry is recommended (§16) but not made automatically here.

**PRODUCTION CHANGES: NONE.**

**Decision: AR1 — ARTISTIC RESET SYNTHESIS COMPLETE; SILENT-LENS EXPERIMENT READY TO RUN.**

The whitepaper (both drafts) and the live AUTHOR RULE prompt already agree on doctrine; the gap
found is in upstream pipeline pressure and inconsistent execution, not in artistic-canon
conflict — this rules out AR3. The available evidence (whitepaper, evidence-graded persona audit,
four production articles, and prior internal audits) is specific and convergent enough to name a
clear, testable hypothesis and a concrete experiment design — this rules out AR2.
