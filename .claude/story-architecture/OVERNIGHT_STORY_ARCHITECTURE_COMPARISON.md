# Story architecture: current engine vs experiment

Base `40be348`. Branch `feat/story-architecture`. No OpenRouter spend; all generation and
evaluation done through the Claude subscription in-session.

## Honest limits of this evaluation, stated first

- **I am both generator and evaluator.** The campaign brief asks for blind A/B. I wrote
  the experimental article, so I cannot be blind to which is which. Randomising the
  order would be theatre. What follows is a stated editorial judgement plus mechanical
  diagnostics, not a blind trial, and no significance is claimed.
- **One article was regenerated, not four.** Three of the five corpus cases were
  *refused* by the worth gate (below), which is the correct outcome but means the
  prose-improvement evidence is **n = 1**.
- **The Galton positive control does not exist** as a frozen artefact (searched
  `_posts`, `_drafts`, all-branch history, `reader-lab`, `calibration`, every evidence
  root). Canon-best `map-that-stops-at-the-door` stands in as a diagnostic target only;
  it was not regenerated, so "positive control not damaged" means "not touched".

## Per case

### jia-curated — the good-idea case. NEW preferred.

**Current engine's reader problems:** press-release dateline opening ("The fifth edition
of Jia Curated ran from 13 to 17 August…"); 10 provenance frames; 3 essay moves; 38
proper nouns in 613 words; a whole penultimate paragraph of disclaimers; a 49-word
hedged final sentence.

**What changed:** the packet carries the story, not the research. The article opens on a
room built of salt, withholds the photograph problem until the festival has ended, and
lets the ranking turn out to be a ranking of photographability. The Crip turn applies
the lens to *the ranking*, not to the pavilions — so it does interpretive work without
making the accessibility claim the evidence cannot support.

| diagnostic | current | new | canon reference |
|---|---|---|---|
| words | 613 | 518 | 1819 |
| paragraphs | 7 | **16** | 49 |
| words/paragraph | 88 | **32** | 37 |
| median sentence | 14 | 16 | 10 |
| max sentence | 49 | **26** | 82 |
| sentences > 30 words | 4 | **0** | 11 |
| proper nouns | 38 | **15** | 56 |
| provenance frames | 10 | **0** | 1 |
| essay moves | 3 | **0** | 0 |
| opening type | press-release/date | **scene/object** | — |
| final sentence words | 49 | **6** | 6 |

**A/B preference: NEW. Material improvement: YES.** Not "shorter sentences" — the
article now has a subject (a room) and a movement (five days, then only pictures) where
before it had a topic and a survey.

**Safety changed: YES, and this is the campaign's most important finding — see below.**

### smolin — wrong-publication control. Correctly REFUSED.

Frozen evidence contains **no disability material**: `disab` 1 (arXiv's "Disable
MathJax" UI string), `crip` 3 (all inside "subscription"/"description"), `blind`,
`deaf`, `impair`, `neurodiver`, `autis` all **0**. A lens would have to be imported.

The forced version — "Just as disabled people face barriers, this theory faced
barriers" — is **mechanically rejected** by `validate_lens` on three separate empty
formulations. Verdict `GREAT_GENERAL_STORY_WRONG_PUBLICATION`, which validates cleanly
and is not publishable. **Control passes: the architecture refuses rather than rescues.**

### eel — negative control. REFUSED, not improved.

The real story material is ZSL's, not the student proposal's: glass eels arriving 8cm
and transparent after 6,500km, **over 2,000 barriers** in the Thames system, **189
hectares** made accessible by eel passes. Strong story, but the only available lens is
barriers-to-migration → barriers-to-access, which is exactly the generic "barriers"
formulation §12 disallows. Verdict **WEAK_ANALOGY → HOLD**.

The existing human reader gate held this article partly for insufficient Crip warrant.
The architecture reaches the same conclusion earlier and for a stated reason, which is
the improvement here — but it produces no better article, because it should not.

### langrug — strong story material. REFUSED on lens.

Excellent narrative material (36,000 litres/day of water polluted by sewage, chemicals
and drug traces; Kevin Winter; established 2018; treated water now growing vegetables;
communal toilets and dysfunctional drainage in the settlement). Disability material in
the frozen pack: `disab` 0, `blind` 0, `deaf` 0, `impair` 0. Verdict **NO_PLAUSIBLE_LENS
in the frozen evidence → HOLD**, per §30's instruction not to force disability onto water
filtration.

### map-that-stops — positive control substitute. Untouched.

Used to calibrate the diagnostics, and it is where the paragraph-density target came
from: 49 paragraphs at 37 words, median sentence 10, final sentence 6, provenance frames
1. Not regenerated, so no claim is made about preserving its strengths beyond not having
touched it.

## The finding that matters most: the architecture moved the failure mode

Loop 1's article scored beautifully and **introduced four factual defects that were not
in the baseline**:

| defect in the experimental article | status |
|---|---|
| "the ears" — sensory channel traceable only to a fact the architect had **CUT** | **hard fail** (§25, Writer used CUT evidence) |
| "The pavilions are gone now" | contradicted evidence that one would be relocated to Medewi Beach permanently |
| a "pink" wall (×2) | the word appears **nowhere** in the frozen evidence |
| "the floor sat lower than the sand", "laid up like masonry" | invented physical arrangement |

So removing the research machinery removed the *visible* hedging and left room for
*invisible* embellishment — which is the worse failure, because a reader cannot detect
it and only the Grounder can. **A declared CUT list is not a control.**

The architectural response was `cut_adherence()`, a deterministic post-writer screen.
Its first version then returned **OK on an article containing a cut term**, because a
sentinel-length threshold silently discarded the 3-character term "ear" that would have
caught it. It now reports skipped terms and unwatched cut items and refuses to claim
success while either exists. Loop 2's article is clean on all four defects, on cut
adherence, on provenance frames and on scaffold leakage.

## Reader-simulation on the final article (jia, loop 2)

1. *What happened?* Someone built a small room out of salt on a Bali beach; it held
   smells and drinks; the festival ended; what travelled afterwards was photographs and
   a list of eight.
2. *Carrier?* The salt room — an object.
3. *Why continue after the opening?* A room made of salt is strange, and the second
   paragraph makes it stranger without explaining it away.
4. *Where is the thread lost?* The crip-turn paragraph is the weakest seam: it shifts
   from the festival to "anyone whose way of being in the world runs through a channel
   the assessment does not carry" in one move. It earns it, but only just.
5. *Unnecessary names?* None obviously — 15, and Spatial Sonata is the only studio named.
6. *The difficult idea?* That a medium of circulation silently selects which work can
   circulate at all, and then the selection gets read as a judgement of quality.
7. *Why is it Crip Minds?* Because being assessed through a channel that cannot carry
   you is the subject, not a comparison bolted on at the end.
8. *Research-note sentences?* None found; mechanically zero provenance frames.
9. *Does the ending land?* Yes — six words, returning to the salt.
10. *Would I keep reading in a book?* Yes.

## CONTINUATION (phases 2-10)

See the appended section below. The n=1 limitation recorded above was resolved.

## Verdict (superseded -- see continuation)

The root cause is identified and measured, one article is materially better, and the
worth gate refuses three cases it would have been easy to force. But prose improvement
is **n = 1**, the Writer demonstrated it will fabricate when the packet is thin, and
nothing is integrated into production. That is not a breakthrough yet.


---

# CONTINUATION: phases 2-10

## Phase 2 -- a second legitimate prose case

- **map-that-stops CANNOT be regenerated.** Published 2026-03-16; the earliest
  new-engine evidence root is 2026-08-26. It carries **0** engine metadata fields and no
  `source_url`, and appears in `/srv/data/cripminds-held` only inside audit documents.
  There is no research pack, no anchor, no discovery. Phase 9 outcome **B**. It was not
  reconstructed.
- **Second control found and used: `roman-launches-with-its-data-pipeline-built-in`.**
  Published (so its lens was human-accepted at the time), new-engine era, 14 frozen
  artefacts, and a different subject from jia. Its baseline exhibits the same defect:
  6 paragraphs at 104 words, median sentence 19, 12 numbers, and a full provenance-audit
  paragraph ("Here the source's evidence ends, and the limit should be marked once").

## Phase 3 -- independent blind evaluation: 4 passes, 4/4 for the new architecture

Each evaluator ran in a separate context, received only article text, and was told
nothing about architectures, labels or my prior judgements. Orders counterbalanced.

| pair | evaluator | preferred | margin |
|---|---|---|---|
| jia baseline vs new | reader | **NEW** | decisive |
| jia baseline vs new | editor | **NEW** | decisive |
| roman baseline vs new | reader | **NEW** | decisive |
| roman baseline vs new | editor | **NEW** | decisive |

Mean of the 11 rubric scores: jia baseline **2.0** vs new **4.5**; roman baseline
**1.9** vs new **3.9**.

They independently identified the exact leak sentences the diagnosis predicted, unprompted
-- "Here the source's evidence ends, and the limit should be marked once" was called
"an instruction to itself, verbatim", and "This is a reading, and it should be marked as
one" was called "the sound of a piece arguing with its own fact-checker in public".

### Their convergent criticism of the NEW output, which drove loop 3

All four, on two unrelated subjects, said the same thing about the crip turn:

- "written in the passive-universal -- no body, no name, no incident. It is the thesis
  paragraph and it is the only paragraph with nobody in it."
- "a single late, abstract aside ... should be seeded earlier and in something as
  physical as the salt."
- "nothing in the piece is written from disability experience. The teacher is a
  placeholder where a person should be." (crip fit **2/5**)
- "because the lens never surfaces, an editor could reasonably file this as a smart
  access-policy column. Fit is earned, not asserted." (crip fit **3/5**)

One reader also caught a factual liability I had not: **"The teacher is invented -- an
unreported, unnamed hypothetical carrying the entire payload of the piece."**

## Phase 4/5 -- factual containment without restoring the research memo

Three screens, at three stages, none of which puts source bodies back in the packet:

| screen | stage | catches |
|---|---|---|
| `validate_packet` | pre-writer | the auditing frame, scaffold names, description-shaped prohibitions |
| `cut_adherence` | post-writer | declared CUT material reappearing, and its own blind spots |
| `factual_surface_audit` | post-writer | numbers, names, sensory and scene vocabulary the packet never granted |
| `architect_prose_audit` | pre-writer | the same three channels in the architect's OWN prose |

## Phase 5 -- three of my own checks were broken, and only testing found it

1. `cut_adherence` returned **OK on an article containing a cut term**, because a
   sentinel-length threshold silently dropped the 3-character term "ear". It now reports
   skipped terms and unwatched cut items and cannot claim success while either exists.
2. The entity channel flagged `Curated` and `Jakarta` as unapproved when both were in
   the packet -- possessive and hyphen token mismatch (`Curated's`, `Jakarta-based`).
3. `the material` and the scene words `room` / `standing` / `somewhere` fired on ordinary
   prose ("a hundred times the material", "it has to go somewhere", a building
   "standing"). Narrowed, with the over-breadth kept as regression tests.

## The most important correction: "pink" was NOT a Writer fabrication

Checkpoint 1 reported it as one. It was not. **"pink" had been written into the
architecture's own `turn` field by hand**, so the packet had already legitimised it, and
`factual_surface_audit` -- which compares prose to the packet -- structurally could not
see it. An audit whose ground truth is itself generated cannot detect a fabrication
introduced upstream of it. Hence `architect_prose_audit`, which applies the same three
hard channels one stage earlier and does catch it. Of checkpoint 1's four reported
defects, **three were the Writer's ("ears", the relocation contradiction, the invented
floor) and one was mine.**

## Phase 6 -- grounding, deterministic half only

The V1 Grounder and V2 classifier both require model calls through the production
provider route, which was forbidden. What ran, on trident against the full frozen packs:

| article | sentences | backbone errors | sentences with retrievable evidence | top_score med/min/max |
|---|---|---|---|---|
| jia loop3 | 35 | **0** | **35 / 35** | 4.5 / 0.0 / 35.2 |
| roman loop3 | 35 | **0** | **35 / 35** | 6.6 / 0.0 / 38.2 |

Segmentation and offset/hash backbone verify cleanly, and every sentence retrieves
evidence from its own pack. **Classification was not run** -- so no SUPPORTED /
UNSUPPORTED / LEGITIMATE_INTERPRETATION counts exist, and none are claimed.

## Phase 7 -- fact-check compatibility, proxy only

Claim extraction is model-gated (`model="openrouter/claude-haiku-4.5"`), so it was not
run. Deterministic proxy on what an extractor keys on:

| case | version | numbers | named entities | quoted spans | recorded claims |
|---|---|---|---|---|---|
| jia | baseline | 3 | 42 | 1 | 2 |
| jia | **new** | **2** | **12** | 0 | not run |
| roman | baseline | 10 | 32 | 1 | 13 |
| roman | **new** | **7** | **24** | 1 | not run |

Verification load falls on every channel in both cases. `FACT_CHECK_MAX_CLAIMS` is
unchanged at 16; roman's baseline was already at 13, and the new version reduces every
input to extraction, so a `TOO_MANY_CLAIMS` hold is less likely, not more.

## Phase 8 -- the final improvement loop (3 of 3)

One generalized change, motivated by two cases and four evaluators, not by jia:
**a lens claim must be embodied in a beat the reader has already been shown.**

The architect now declares `crip_turn_rereads: <beat_id>`, and the turn must name
something from that beat's own concrete carrier. This was made a *declared* relation
only after a first version that *inferred* it from token overlap passed both
architectures the readers had criticised -- matching on the word "named". A proxy that
lenient is not a check.

Scene vocabulary was promoted to a hard signal in the same loop, because of the invented
teacher. The screen had already surfaced `laptop`, `room`, `somewhere`, `waiting` as
candidates and **nobody looked**. A signal nobody inspects is not a control.

## Phase 10 -- integration: NOT done, and why

`story.py` makes **zero** provider calls; it validates and renders. But the three stages
it defines contracts for -- finder, worth gate, architect -- each require a model call to
*produce* their output, and that route is OpenRouter, which was forbidden tonight.
Wiring them into `runner.py` would ship a production path I could not execute even once.
That is a technical blocker, not a judgement, so no `#63` was opened and nothing imports
`story.py`.
