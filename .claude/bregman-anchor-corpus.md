# Bregman anchor corpus — for register calibration, not for training

Standing reference for any future test/judge/tuning pass on the "read like Bregman"
effort (see `.claude/bregman-architecture-analysis.md` and
`.claude/bregman-write-economy-analysis.md` for the technique-level analysis this
complements). Built 2026-08-07. Short illustrative fragments only — full source
texts are copyrighted and not reproduced here; go to the original for anything
beyond a calibration snippet.

## Section 1 — ESSAY/REPORTAGE register (use these for anchor calibration)

This is the register cripminds personas should actually be matched against: Bregman
reporting something he found out, not persuading a live audience. All confirmed
consistent with each other across English and Dutch sources.

**Sources:**
- TED talk, "Poverty isn't a lack of character; it's a lack of cash" (2017)
- "The neoliberal era is ending. What comes next?", The Correspondent (2020)
- "The real Lord of the Flies", The Guardian (2020, excerpted from *Humankind*)
- *Utopia for Realists* / *Gratis geld voor iedereen*, ch. 1 (2016)
- *De geschiedenis van de vooruitgang*, Prologue (2013)
- *Het water komt* (2020)

**Confirmed shared habits (triangulated across all six sources):**
- Flat declarative opener, often very short ("Vroeger was alles slechter" — things
  used to be worse). No throat-clearing, no framework named before anything concrete
  happens.
- Abstract claim immediately followed by one concrete named source/study/statistic,
  never left as a bare thesis. ("A paper by a few American psychologists...";
  Spanish researchers, Nature, 464,411 songs, one number, one conclusion.)
- Real named people carry the argument, quoted directly and briefly — never "a
  researcher found," never a composite or unnamed authority.
- Verbatim-refrain repetition (a short list or phrase repeated word-for-word later
  in the piece) is a real device — distinct from wordplay, since nothing changes
  or twists between repetitions.
- Short "punch" sentences, sometimes just the repeated subject as its own sentence,
  for dramatic pause at a turning point ("Het water. Het water staat te hoog.").
- Sentence economy: short declarative → short declarative → payload. Lists run to
  three. One modifier, not three.
- Dates and places anchor every anecdote, including the author's own.
- Endings land on a plain fact, a real quote, or a concrete narrative beat — not a
  crafted twist or epigram.
- At most one named source developed at a time (a paragraph of context, then the
  quote, then its implication) before moving to the next — not stacked citations.

**What's essentially absent in this register** (confirmed by two independent
model-judged tests against real generated samples, 2026-08-07): metaphor standing
in for a plain mechanical fact, mirrored/cleft antithesis ("X is not Y, it is Z"),
aphoristic or ironic closers, sustained wordplay, treating an abstract framework —
or an inanimate object (a building, a drawing) — as a deliberate agent.

## Section 2 — ORATORY/LECTURE register (reference only — do NOT use for anchor calibration)

**Source:** The Reith Lectures 2025 with Rutger Bregman, Lecture 2 "How to start a
moral revolution" (BBC Radio 4, transcript, first 10 pages)

This is a *different register* and mixing it into Section 1's anchors would teach
the wrong lesson. A lecture is built to move a live audience toward a call to
action; cripminds personas write essays reporting what they found out, not stump
speeches. Confirmed present in this source, absent from Section 1:

- Sustained historical parallelism as a structuring device (explicitly drawing "just
  like Russia in 1917, just like the world today" across the whole piece).
- A named sequence of historical figures presented as a list to build momentum
  (three-in-a-row), the same shape flagged as a violation ("citation density") in
  Section 1's register.
- At least one genuinely aphoristic, quotable line built for the ear, not the
  page — a lecture is meant to produce a line that circulates afterward.
- Explicit rhetorical structuring announced to the audience ("I promised I'd
  structure this series as a classic three-part sermon").

**Takeaway:** Bregman's rhetorical intensity is register-dependent, not a fixed
personal style. Any future anchor-gathering should keep sourcing from his written
journalism/books, not his lectures or talks aimed at persuasion — even though both
are "real Bregman," they calibrate toward different, sometimes contradictory
targets.

## Section 3 — how to use this file

Two model-based repair strategies were tested against real flawed drafts on
2026-08-07 and neither broke through a real ceiling (both plateaued at 10-15
remaining issues per sample): rule-based repair (refined over 3 rounds) and
exemplar-based repair (shown Section 1's anchors directly, no rule list). Neither
beat the other consistently. That means this file's value is as a fixed,
reusable **judge reference** — for scoring/comparing future generation or repair
attempts consistently — not as a magic ingredient that fixes generation on its own
if fed to a writer or fixer model. See the "multi-draft-and-pick" and "dedicated
register-editor stage" ideas logged in this session's conversation for the more
promising next architectural moves; this corpus is what any of those approaches
would need as their fixed comparison target.
