# Continuity Editor: can the reader stop seeing the Story Architect?

Base `40be348`. Branch `feat/story-architecture`, additive on checkpoints `4c758a7`,
`26c58e5`, `2f06ca7`, `bd0a0d1`. No OpenRouter spend. Nothing wired into production.

## The measured cause of the visible scaffolding

Two mechanisms, and the second is the one that mattered.

**Transcription.** The Story Architect's own prose fields carried the staging, and the
Writer copied them:

| architect field | finished sentence | similarity |
|---|---|---|
| `crip_turn` "Go back to the sand." | "So go back to the sand." | **0.93** |
| `ending_move` "Return to the salt walls: a surface someone could have put a tongue to…" | the closing sentence | **0.90** |

**Performance slots.** 5 of 15 paragraphs were a single sentence (33%), and they were
almost exactly the sentences the owner flagged. A one-sentence paragraph is a slot that
*forces* its sentence to perform, which is why rewriting the sentences never fixed it.

**What was NOT the cause:** beats becoming paragraphs one-for-one. The measured ratio was
**3.0**. That hypothesis was wrong and is recorded so it is not re-proposed.

## Jia, three levels

| | production baseline | #62 final (B) | continuity final (C) |
|---|---|---|---|
| words | 613 | 421 | 397 |
| paragraphs | 7 | 15 | **12** |
| words/paragraph | 88 | 28 | 33 |
| solo paragraphs | 0 | 5 (33%) | **2** |
| signpost openers | — | 5 | **3** |
| provenance frames | 10 | 0 | **0** |
| proper nouns | 38 | 13 | 13 |
| ending | 49-word hedge | 6 words, isolated | 6 words, isolated |
| factual delta vs B | — | — | **0 on every channel** |

## The finding that decided the campaign

I built two Continuity Editor designs and the aggressive one lost.

**v3 (aggressive merge)** achieved what the diagnostics asked for: solo paragraphs
**5 → 0**, signpost openers **5 → 0**, zero semantic delta. Then two independent
evaluators rejected it anyway:

- Blind editor, v3 vs minimal: **minimal, clear margin.** Concrete story **2 vs 4**,
  Crip fit **3 vs 4**, ending **3 vs 4**. Deciding factor: *"B quotes the record's own
  words at the hinge where A only reports them, and an argument about what writing can
  hold cannot afford to paraphrase its exhibit."*
- Solo lens reader on v3: **could not recover the lens** — *"as published it reads as
  generic media criticism about architecture writing."*
- Solo lens reader on minimal: **recovered it** — *"the piece catches an archive
  discriminating by sense… The ranking is not a ranking of pavilions. It's a ranking of
  describability, wearing a ranking of quality."*

Merging dissolved the quoted specimen the whole argument turns on — the italicised
*"The sand embodied strength and fragility"* — and with it the reader's ability to see
why the piece is a Crip Minds piece. **Naturalness and lens legibility traded against
each other, and the lens is worth more.**

So the selected final is the **minimal** edit: #62's prose with the two reader
instructions deleted and one performance slot folded in. It is the variant two
independent editors converged on unprompted, one of them writing before it existed:
*"A minus two sentences would beat both versions."*

## Blind preferences

| comparison | reader | editor |
|---|---|---|
| #62 final vs v3 aggressive | **v3**, clear | **v3**, slight (totals favoured #62 52–50) |
| v3 aggressive vs minimal | — | **minimal, clear** |
| lens recovery, solo | v3 **FAIL** | minimal **PASS** |

## Safety

Lineage clean; every draft sentence accounted for; semantic delta **zero on every
channel** — no new numbers, entities, sensory, spatial or scene terms, and **no new
relation classes** (causal, negation, exclusivity, first/last, intent, temporal,
comparison, generalization). Cut leakage 0. Provenance frames 0. Negative claims: 1,
covered by the audited-corpus fact. 15 required mutations plus paragraph-shape tests all
caught. Full suite **56 PASS / 59 files**, only the three known pre-existing failures.

## What is still wrong, and it is one thing

Both solo readers, independently, classified even the minimal final as
**VISIBLE_SCAFFOLDING**, and both named the same cause: **the thesis is restated four
times at rising altitudes.**

1. "Across all eight of those descriptions, none reports what any visitor perceived."
2. "The account keeps what the sand was said to mean and loses what it was to stand on it."
3. "It holds the meanings and drops the encounters."
4. "A record decides what kind of perceiving it can carry."

(2) and (3) are adjacent sentences saying the same thing. One reader: *"the paragraphing
is the scaffolding… Each one-line paragraph is a beat, and I can count the beats."*

**The Continuity Editor cannot fix this**, because each restatement is a declared beat
(B5, `turn`, `crip_turn`, `ending_move`). Deleting one means deleting a beat, which is a
Story Architect decision, not a prose decision. That is the remaining architectural
blocker, and it is upstream of this stage.

Also unresolved and named by two readers: the piece contains no perceiver. An article
about records that drop the encounter has no encounter of its own beyond one hypothetical
tongue.

## Second prose control: NONE EXISTS

Every published post was checked for a complete new-engine evidence run. Exactly one has
one — Roman — and Roman is correctly HELD (`WEAK_ANALOGY`; its intended ending is a
world-scoped negative-existence claim the evidence cannot support). No Worth Gate was
weakened to manufacture a sample. Per §49 this caps the classification.

---

# Semantic compression (final iteration)

Owner ruling: the Story Architect may not require multiple restatements of one lens
proposition. The defect was upstream, not a Continuity Editor failure.

## What changed in the architecture

Propositions now carry a **role** — EVIDENCE, STORY_EVENT, COMPLICATION, LENS_OWNER,
CONSEQUENCE, CALLBACK — and **exactly one** may be LENS_OWNER. `turn` collapsed into
`crip_turn` (recorded as `turn_collapsed_into`), and `ending_move` is now checked against
the lens so it may embody the insight without explaining it again.

**A finding worth keeping:** word overlap is nearly useless for this job. The two Jia
abstractions — *"it holds the meanings and drops the encounters"* and *"a record decides
what kind of perceiving it can carry"* — are the same idea with **zero shared content
words**, and an overlap test scores them **0.00**. The load-bearing check had to be
structural: more than one *abstract* proposition means the article explains itself twice,
whatever words each uses. The role contract, not the similarity number, is the control.

Also honest: the collapse of `turn` and `crip_turn` in the Jia case was **my editorial
judgement**, not the gate's. Both beats named a carrier, so the abstraction test correctly
said "distinct". The gate catches duplicate *abstractions*; it cannot detect two
concrete-anchored beats encoding one movement.

## Result

| | continuity final | compression final |
|---|---|---|
| words / paragraphs | 403 / 12 | **323 / 8** |
| distinct statements of the central idea | **5–7** | **2–3** |
| signpost openers | 3 | **0** |
| lens articulated | 5 ways | **once** |
| semantic delta | — | **0 on every channel** |

**Blind reader: compression, clear.** Non-repetition 2→4, visible scaffolding 2→4,
momentum 2→4, ending 3→5. **Blind editor: compression, clear.** Asked directly whether
saying it once cost anything: *"Almost nothing, and what it cost is not the insight — it
is two beats of rhythm."*

Both editors independently required one further deletion — the abstract clause
*"described by the part of itself that could be written down"* immediately followed by its
own concrete restatement. Applied; the paragraph now runs "The salt room is on that list.
Its mineral is in the record; its content is not."

## Why this is a HOLD, not a PASS

The **solo** reader — article only, no comparison — still returns
**VISIBLE_SCAFFOLDING**, and on the lens says the piece reads *"about 60% media
criticism, 40% something sharper it declines to say out loud."* That is weaker than the
earlier minimal variant, where the same test recovered the lens cleanly.

The mechanism is precise and it is a genuine tension in the brief. §14 requires **one**
explicit lens articulation, not zero. But the solo reader experiences that single
articulation as the one place the article stops trusting them:

> "A record decides what kind of perceiving it can carry… I understood that at ¶7 and had
> it confirmed by the last sentence of ¶9. This sentence tells me the moral of a story I
> had already finished reading. It's the one place the article stops trusting me."

So the remaining defect is not repetition any more — it is that **a standalone abstract
articulation reads as thesis-announcement however few times it appears**. Cutting it
satisfies the writtenness gate and violates the lens gate; keeping it satisfies the lens
gate and fails the writtenness gate. That is the one mechanism left, and it is an owner
decision about which gate yields.

Second, unchanged and named by every solo reader: the article contains no perceiver. It
prosecutes a record for reporting no perception while itself reporting none.

---

# Lens realization (final)

Owner ruling: do not accept VISIBLE_SCAFFOLDING as the floor, and do not require one
explicit abstract lens sentence. The conflict between "the lens must be visible" and "the
scaffolding must be invisible" came from equating **visibility** with **articulation**.

## Contract change

The architecture still keeps one machine-side `LENS_OWNER`, plus `evidence_basis`,
`before_reading`, `after_reading` and `crip_turn_carrier` — it must be able to say
exactly why the piece belongs here. What changed is the packet. It used to hand the
Writer "*the idea that does this work:* <lens_claim>", and the Writer duly wrote it out.
It now asks for **what the reader should understand differently by the end**, and says
in as many words: realise this through the material, and do not state it as a general
principle unless that is the most natural sentence available.

`lens_is_serialized()` reports which form an article chose. It never requires or forbids
either. Nothing in the gate searches the prose for the lens wording — searching for the
wording is the contract being replaced.

## Result: the abstraction was not load-bearing

One sentence deleted — *"A record decides what kind of perceiving it can carry, and what
it carried is what anyone downstream can weigh."* — with no replacement.

| | with explicit lens | without (final) |
|---|---|---|
| words / paragraphs | 329 / 8 | **303 / 8** |
| naturalness (reader) | 3 | **4** |
| visible scaffolding (reader) | 2 | **4** |
| momentum (reader) | 3 | **5** |
| ending (reader) | 4 | **5** |
| **lens recovery** | 4 / 3 | **4 / 3 — unchanged** |
| solo writtenness class | VISIBLE_SCAFFOLDING | **MOSTLY_NATURAL** |

**Blind reader: clear preference.** *"Does the one without the general principle still
deliver the insight? Yes, completely. Removing that sentence costs nothing… The principle
was never load-bearing; it was a summary of load already carried."*

**Blind editor: clear preference.** *"A's sentence is not what makes the difference…
'a record decides what kind of perceiving it can carry' is a claim about archives, not
about bodies. It is the most generic sentence in either draft. So A does not buy lens
with it; A buys abstraction and pays in momentum."*

**Article-only lens recovery — PASS.** *"the article's whole method is knowing that a
description can be complete-looking and still contain nothing you could have perceived.
That's a way of reading that comes from being on the wrong side of a channel."* Asked
whether it states a thesis: *"No."* Asked whether it trusts the reader: *"Yes,
considerably. It never says 'this is about ableism'… The restraint is the technique."*
Asked whether it would sit in a good nonfiction book: *"Yes — as a short chapter."*

No evaluator called it generic media criticism. The editor: *"Neither draft is generic
design criticism."*

## What remains, and it is not the lens

Both blind evaluators, independently, name the same residual: **there is no perceiver in
the piece.** The strongest sensory moment is a conditional — "could have put a tongue
to." The article indicts a record for containing no perception while containing none
itself. The editor's required change is one sentence of actual perceiving, from a person
who was there or any first-hand account.

The frozen evidence contains no documented encounter, and inventing one is forbidden. So
this is a **research** limit, not an architecture limit: the fix is a source, not a
sentence.
