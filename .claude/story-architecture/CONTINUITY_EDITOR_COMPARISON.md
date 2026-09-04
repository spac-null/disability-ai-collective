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
