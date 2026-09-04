# RQ1 — does reader information state describe why strong nonfiction moves where it moves?

Validation of the experimental reader-state model against published prose, before any
generation. Experiment only; nothing here is production-authoritative.

## 1. Method

Eight published texts with reliable unit boundaries, four forms, two authorship classes:

| id | source | form | units | words |
|---|---|---|---|---|
| T1 | BR-01 Bregman, *Benjamin Lay* | narrative history | 68 | 5,072 |
| T2 | BR-02 Bregman, *An Inconvenient Truth About AI* | argumentative essay | 105 | 4,738 |
| T3 | BR-14 Bregman, *Why do the poor make such poor decisions?* | explanatory feature | 50 | 2,578 |
| T4 | BR-09 Bregman, *No, you're not fine just the way you are* | reported essay | 56 | 3,465 |
| T5 | CX-02 Ed Yong, *North Atlantic Right Whales* | explanatory feature | 17 | 1,316 |
| T6 | CX-12 Andrew Grant, *Voyager 1* | science news | 16 | 993 |
| T7 | CX-08 Fletcher Reveley, *Unsolved Kidney Disease Mystery* | narrative feature | 68 | 7,166 |
| T8 | CX-09 B. Toastie Oaster, *Pacific Lamprey* | narrative feature | 54 | 4,937 |

Four boundaries per text at roughly 20/40/60/80% — **32 transitions, 30 analysed.**
Scientias was deliberately excluded: the model is being tested first against
popular/narrative nonfiction, per the brief.

**Two exclusions.** `T5_b2` and `T6_b2` were dropped because the unit following the boundary
is Open Notebook editorial sidebar text, not article prose. This was not caught when the
dataset was built; it was caught by one of the blind architect passes, which recorded
`next_move_relation: NONE` rather than inventing a relation for boilerplate. The detector
working as intended is why the contamination surfaced at all.

**Blindness.** Three independent populations of evaluator, none told the research hypothesis,
none told that Crip Minds or an engine was involved:

- **8 blind readers.** Each received four passages drawn from four *different* articles, cut
  off at the boundary, and never the continuation of any passage it judged. Asked only: what
  do you now know, what do you most want to know next, and could this simply continue?
- **4 blind architects.** Each received eight transitions as an architect would see them —
  everything delivered, plus the approved next material — and produced *both* representations
  independently: the four reader-state fields, and a single `why_reader_wants_next` sentence
  in PR #62's register. Blind to the readers' answers, so no copying was possible.
- **2 blind judges.** One scored agreement between predicted and actual reader questions
  without being told which was which. One compared the two representations as "two
  note-taking formats an editor might use", with no mention of an engine.

This is the design's main strength and its main limitation: the evaluators are language
models, not humans. What follows is evidence that the reader-state description is *recoverable
by an independent reader of the same text*, not evidence about human readers.

## 2. Is reader information pressure a real description of published prose?

Yes for a clear majority, and — just as important — no for a substantial minority.

| blind reader's judgement at the boundary | n | share |
|---|---|---|
| an active unresolved need ("could it just continue?" = NO) | 18 | 60% |
| the piece could naturally continue without resolving anything | 12 | 40% |
| no strong question at all | 1 | 3% |

**Sixty percent** of boundaries in strong published nonfiction left an independent reader with
a specific unresolved information need they could state in one sentence. **Forty percent** did
not: chronology, scene momentum or an unfolding list carried the text forward without any
pressure to discharge.

That 40% is the result that matters most for design. A model that forced every transition into
question-and-answer would misdescribe two boundaries in five of the best available prose. The
`NONE` / `CONTINUES` value is not a safety valve; it is where nearly half the real cases live.

Where continuation was natural, the reasons were exactly the ones the brief anticipated:

> *"The biography is running forward in plain chronology toward the 1738 scene already
> narrated, so the next stretch is simply the next years of his life."* (T1_b4)
> *"It stops mid-scene on a boat heading to the falls; the trip can simply proceed."* (T8_b2)
> *"It's an accumulating argument-essay; another danger domain or data point could follow
> indefinitely without resolving anything."* (T2_b3)

## 3. Can `reader_now_wonders` be verified rather than declared?

Partly. This is the campaign's central question and the answer is a qualified yes.

| blind judge's verdict on architect-predicted vs actual reader question | n | share |
|---|---|---|
| STRONG_MATCH — substantially the same thing | 11 | 37% |
| PARTIAL_MATCH — same next material would satisfy both | 8 | 27% |
| NO_MATCH — genuinely different things | 5 | 17% |
| architect said NONE, reader had a question | 5 | 17% |
| **architect asserted pressure the reader did not feel** | **1** | **3%** |
| both said NONE | 0 | 0% |

**19 of 30 (63%) at least partial agreement**, against a 3% rate of the failure mode the brief
names `ARCHITECT_INVENTED_PRESSURE`. The asymmetry is the encouraging part: when the architect
was wrong it was five times more likely to *under-call* pressure than to invent it, and
under-calling is the safe direction — it produces a `CONTINUES` plan, not a manufactured
question.

The single invented-pressure case is `T8_b4`: at 80% through the lamprey feature the architect
asked *"Who was Elmer Crow, and what happened to him?"* while the blind reader reported
`NO STRONG QUESTION` and said the piece read as an accumulating braid that could simply carry
on. The next material *is* about Elmer Crow, so the architect predicted the content correctly
and mischaracterised the reader's state — which is precisely the confusion the four-field
split is supposed to expose, and here it did.

**Specificity gap.** The blind judge rated the architect's questions SPECIFIC in 19/30 cases
and GENERIC in 11/30. Real readers were SPECIFIC in 27/30. The architect is measurably less
anchored in the passage's own material than a reader is — a real weakness, and one that is
visible only because there was something to compare against.

## 4. Relation vocabulary — the enum is too large

Architect usage across 30 valid transitions:

| relation | n |
|---|---|
| ANSWERS | 16 |
| DEEPENS | 5 |
| CONTINUES | 5 |
| DEFERS | 3 |
| COMPLICATES | 1 |
| CHANGES_SCALE | **0** |
| NONE | 0 (2 in the excluded pair) |

`CHANGES_SCALE` was never used once. `COMPLICATES` was used once. Half of all transitions were
labelled `ANSWERS`.

Two readings, and both are worth recording. The charitable one: published prose really does
answer more than it complicates. The uncharitable one, which the blind judge raised
independently: `ANSWERS` at 16/32 is *itself* a formula risk — "the label vocabulary collapses
into ANSWERS half the time." A four-value set (`ANSWERS`, `DEFERS`, `CONTINUES`, and one of
`DEEPENS`/`COMPLICATES`) would carry this dataset with no loss.

## 5. Reader-state versus `why_reader_wants_next`

Blind judge, told only that these were two note-taking formats. X = reader-state, Y =
`why_reader_wants_next`. It was not told which was the incumbent.

| criterion | winner | the judge's reasoning, condensed |
|---|---|---|
| specificity | **X** | X carries named and numeric content; in Y, 26 of 32 entries contain the phrase "the reader" and 23 assert the reader "wants", "needs", is "owed" or is "waiting" |
| falsifiability | **X** | X's question can be checked two ways a second person can actually run — against the next material, and against an independent reader. "Nothing about 'the reader wants to know who is causing this' can be shown false." |
| self-justification risk | higher in **Y** | the decisive cases are the two contaminated transitions: X recorded `NONE` and flagged them broken; Y produced entirely reasonable-sounding motives for material that never arrives |
| predictiveness | **X** | question plus relation predicts content *and* move; Y "carries no move type, so DEEPENS versus DEFERS versus CONTINUES is invisible" |
| formula risk | higher in **Y** | 12 of 32 Y entries are literally "[the piece] has just X, and the reader wants Y"; but X's `ANSWERS`-half-the-time is named as a real secondary risk |
| **prose-leakage risk** | **higher in X** | X's field "is a finished rhetorical question in the reader's voice — 27 of 32 end in a question mark — so 'So what can be done?' style scaffolding is one copy-paste away" |

Overall verdict: **X**, on the ground that it is the only one of the two that can register
failure. Its named weakness: the question is the annotator's, not necessarily a reader's, and
it hands the writer a ready-made rhetorical question. Y's named weakness: *"It cannot be
wrong."*

**The prose-leakage finding is the one that cuts against the experiment**, and it is not
hypothetical — the blind judge noticed that the published Bregman text at `T3_b4` contains
exactly the pivot sentence ("So what can be done?") that its own reader-state entry would have
suggested. Any implementation must therefore keep the question strings away from the Writer,
which is what the Jia A/B does.

## 6. Counterexamples the model must preserve

Recorded because a model that cannot accommodate these is wrong.

1. **Chronology alone carries a text.** T1_b4, T8_b2, T7_b1 — the reader explicitly said the
   next stretch is simply the next thing in time.
2. **Accumulation without resolution.** T2_b3, T3_b1, T3_b4 — evidence essays where "another
   data point could follow indefinitely without resolving anything."
3. **No question at all.** T8_b4 — a narrative feature 80% through, and the reader reported no
   curiosity to serve. The architect invented one here.
4. **A writer deliberately interrupting curiosity with context.** T1_b1 and T1_b3: the reader
   was holding one long-range question (*did this outcast actually change the Quakers' minds?*)
   across a background block that generated no local pressure of its own. The architect coded
   the second of these `DEFERS`, which is the correct description — the pressure exists, is not
   served, and the delay is deliberate. This is the case the model handles best.
5. **An explicit thesis working better than discovery.** T6 (Voyager) states its whole
   significance in sentence one and the reader's questions throughout are mechanical
   ("how did they determine it?"), not thematic. Reader-state planning did not need a withheld
   answer to work here.
6. **Prediction can be right about content and wrong about state.** T8_b4 again — the
   distinction only becomes visible because the representation separates the two.

## 7. Where the model is less useful

- **Long narrative features** (T7, T8). Both had the most `NONE`/continue judgements and the
  most `NO_MATCH` scores. Scene and chronology do the work; information pressure is a weaker
  description of why the next paragraph is next.
- **Argument essays with announced lists** (T2, T4). Here the "question" is trivial and
  structural — *what are the other two?* — which the model captures but which needs no model:
  the article told the reader the list length.
- **Explanatory features and science news** (T3, T5, T6) are where the model performs best: 8
  of 11 STRONG_MATCH scores come from these three texts.

That last point matters for Crip Minds, whose material is usually explanatory rather than
narrative.

## 8. Verdict on the published-prose gate

The brief's bar: *is reader information pressure a useful, recoverable description of why
strong nonfiction moves where it moves?* — with the instruction to HOLD if it explains only a
minority of real transitions.

It describes **60%** of boundaries as carrying active pressure, and an independent reader of
the same text recovers the architect's description of that pressure in **63%** of cases, with
a 3% invented-pressure rate. The 40% that move without pressure are explained by the model's
own `NONE`/`CONTINUES` value rather than being counterexamples to it.

**The gate is passed, promisingly rather than overwhelmingly.** Two qualifications travel with
it: the relation enum is larger than the data needs, and the question field is one copy-paste
from becoming the visible scaffolding the whole project is trying to remove.
