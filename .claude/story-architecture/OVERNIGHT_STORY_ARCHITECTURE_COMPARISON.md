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

## Verdict

The root cause is identified and measured, one article is materially better, and the
worth gate refuses three cases it would have been easy to force. But prose improvement
is **n = 1**, the Writer demonstrated it will fabricate when the packet is thin, and
nothing is integrated into production. That is not a breakthrough yet.
