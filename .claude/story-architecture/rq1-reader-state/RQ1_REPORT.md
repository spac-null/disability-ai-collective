# RQ-1 — reader-state architecture: HOLD

Experiment only. No production behaviour changed, no OpenRouter spend, nothing merged, and no
authoritative generation path was modified.

## Result

**HOLD.**

The published-prose validation passed. The generation test did not. The brief requires all ten
success conditions and two of them fail — the two that matter most for the thing being tested.

| § | condition | verdict |
|---|---|---|
| 31.1 | reader-state describes a substantial share of strong transitions | **PASS** — 60% carry pressure, 63% recoverable by an independent reader |
| 31.2 | performs better than `why_reader_wants_next` on specificity / falsifiability | **PASS** — blind judge, 4 of 6 criteria including both named |
| 31.3 | **B preferred blind for information order / natural reading** | **FAIL** — both comparators gave order to A; per-boundary naturalness 91% A vs 75% B |
| 31.4 | B does not increase explicit rhetorical questioning | **PASS** — 0 question marks and 0 serialization hits in both |
| 31.5 | **B does not increase signpost scaffolding** | **FAIL** — B 1 signpost opener, A 0; both comparators named B worse |
| 31.6 | B does not introduce facts / relations | **PARTIAL** — B passes both mechanical gates that A fails, but carries 1 intent assertion, and blind readers found unsupported claims in both |
| 31.7 | architect-predicted questions substantially match blind readers | **PARTIAL** — 63% at least partial on n=30; 2 of 5 on the Jia article |
| 31.8 | `NONE`/`CONTINUES` genuinely used where no question exists | **PASS** — 40% of published boundaries, 40% of B's own plan |
| 31.9 | no new production behaviour | **PASS** |
| 31.10 | no new suite failures | **PASS** — 59/62, the same three pre-existing failures |

## What the experiment found

**The model describes published prose well.** Across 32 transitions in 8 texts, blind readers
reported an active unresolved need at 60% of boundaries and said the piece could simply carry
on at 40%. An independent judge scored the architect's description of that need as matching the
reader's own in 63% of cases, with a 3% invented-pressure rate. The 40% questionless share is
not a weakness of the model — it is the `NONE`/`CONTINUES` value doing exactly the job §7
demanded of it.

**The representation is better than the one it would replace.** A blind judge, told only that
these were two note-taking formats, chose reader-state on specificity, falsifiability,
predictiveness, and lower self-justification risk, and summarised the incumbent's weakness in
four words: *"It cannot be wrong."* The decisive evidence was accidental — two transitions in
the dataset turned out to have editorial boilerplate as their "next material", and the
reader-state format recorded `relation: NONE` and flagged them broken while
`why_reader_wants_next` produced entirely plausible motives for material that never arrives.

**And then it planned a worse article.** Given the identical frozen ledger, the reader-state
architecture made five attributable reordering decisions. Its largest — moving the festival
frame and the list of eight from the end to the opening — was identified independently by both
blind comparators as the specific place the article goes wrong, and a third evaluator working
paragraph by paragraph found the same fault a third time. The architecture's stated reason was
*"the reader needs a place and a frame before any material can register."* Three evaluators
said the frame cannot register until there is something for it to frame.

That is the finding. The reader-state model is a better *description* of prose that already
works and was, in this one case, a worse *instrument* for deciding order. Those are different
claims and the experiment separated them.

## Why HOLD rather than reject

Three reasons the evidence does not support rejecting reader-state:

1. The published-prose result is solid and was blind-scored on 30 transitions.
2. The comparison against `why_reader_wants_next` was won on the criteria that matter for an
   engine — a field that can register failure is worth more than a field that reads well.
3. The Jia failure is **n=1**, with two different writer agents, no continuity pass, and a 20%
   packet-length difference. It is enough to stop a cutover. It is not enough to conclude the
   model cannot plan order.

## Why HOLD rather than pass

The failure is not a near miss. It is the experiment's own central mechanism producing a
confident, articulate, false claim about a reader — at the one point where it departed most
from the control. §32 lists "reader questions are mostly invented by the architect" as a HOLD
condition; the published data says they mostly are not, but the Jia case shows what it looks
like when one is, and it looked exactly as persuasive as the correct ones.

The scaffolding leak compounds it. The internal question did not reach the page as a rhetorical
question — the brief's enumerated risks all held — but it reached the page as a reading
instruction (*"Read across all eight of the entries, a pattern in what they contain becomes
plain"*), which is the same defect in a form the brief did not list.

## Answers to the three questions

### 1. Can `reader_now_wonders` be verified, or is it another self-justification field?

**It can be partly verified, and that is a real difference in kind.** An independent reader of
the same text recovers the architect's stated pressure about two-thirds of the time, the errors
run five-to-one toward under-calling rather than inventing, and — decisively — a wrong entry
can be *detected*, which is not true of `why_reader_wants_next`. The blind judge found that
format's entries could not be shown false at all.

But it is not reliably verified, and two qualifications travel with it. One in six predictions
pointed at genuinely different material. And the architect is systematically less specific than
a real reader: SPECIFIC in 19 of 30 cases against the readers' 27 of 30. The honest description
is that `reader_now_wonders` is a **falsifiable proposal about the reader**, not a description
of one. That is worth more than the incumbent and less than the brief hoped for.

### 2. Did reader-state planning improve information order without making the prose more explicitly structured?

**No, on both halves.** It made the order worse, by the unanimous judgement of three
independent evaluators who each located the same fault. And it made the prose *more* explicitly
structured, by one signpost opener that both comparators named unprompted.

What it did improve was everything the experiment was not testing: B won on compression,
breathing room, plain reading, concrete material, ending, momentum, and — from both comparators
— on whether the idea landed at all. Those gains are real but unattributable, because A and B
had different writers and there was one draft each. The anti-overfitting check rules out the
cheap explanations: B has *fewer* paragraphs, marginally *longer* sentences, and identical
question counts.

### 3. Replace, augment, reject, or insufficient evidence?

**AUGMENT.**

Not REPLACE: the one generation test available produced a worse order, and the field's own
biggest decision was the wrong one. Replacing a weak field with a field that can be
confidently wrong about readers is not an improvement.

Not REJECT_READER_STATE: the published-prose validation is the strongest result of the
campaign, and the falsifiability advantage is exactly what PR #62's `why_reader_wants_next`
lacks. Throwing that away because of a single Jia draft would be the mirror of the mistake this
whole programme has been correcting.

Not INSUFFICIENT_EVIDENCE: there is enough to know what to do next. The evidence separates a
description that works from an instrument that did not, which is a usable finding.

**Augment** means: keep `why_reader_wants_next` where it is, and add the one part of the
reader-state contract that carries the evidence — the recorded question plus its relation — as
a **checkable annotation that does not decide order**. Then the next experiment can ask the
question this one could not: does a *verifier* that compares the architect's claimed reader
pressure against a blind read catch bad orderings before they are written? That is a use of
reader-state which the data supports, because catching failure is the thing it demonstrably
does better.

## Recommended next implementation experiment

Not to be started now, and not to be implemented on the strength of this document.

**RQ-2, narrower than RQ-1: reader-state as a post-hoc verifier rather than a planner.** Keep
the current architect and its `why_reader_wants_next` untouched. After an architecture exists,
have a second, independent pass state the reader's information state at each boundary from the
*plan alone*, and flag boundaries where the plan's own justification and the independent read
disagree. Measure whether the flags predict the orderings that blind readers later dislike.

That design tests the capability this experiment actually established — detection — and avoids
the one it did not — planning. It also needs no new field in the authoritative contract, so it
can be run without touching generation at all.

## What must not be concluded from this

- Not that reader-state modelling does not work. One draft, one subject, one architect.
- Not that `why_reader_wants_next` is fine. It won on the Jia order and lost every
  falsifiability criterion; the blind judge's verdict on it was *"it cannot be wrong."*
- Not that B's prose advantage came from the architecture. Different writers, n=1.
- Not that the published-prose 63% match rate is a human result. Every evaluator was a model.

## Artifacts

```
RQ1_PUBLISHED_READER_STATE_VALIDATION.md   the 8-text, 32-transition study
RQ1_PUBLISHED_TRANSITIONS.jsonl            32 rows, 2 marked excluded, blind labels included
RQ1_JIA_CONTROL_ARCHITECTURE.json          A, unchanged frozen architecture
RQ1_JIA_READER_STATE_ARCHITECTURE.json     B, same ledger and permissions
RQ1_ARCHITECTURE_DELTA.json                5 reorderings, each with its reader-state basis
RQ1_JIA_A.packet.txt / RQ1_JIA_B.packet.txt  both rendered by the authoritative builder
RQ1_JIA_A.final.md / RQ1_JIA_B.final.md    the two drafts
RQ1_JIA_SAFETY_AB.json                     every audit, both drafts
RQ1_BLIND_AB_RESULTS.md                    two comparators, per-boundary reads, confounds
RQ1_READER_PREDICTION_MATCH.md             the §26 verification question, both datasets
../../automation/rq1_reader_state.py       experimental contract, imported by nothing
../../automation/rq1_reader_state_test.py  9 tests, including one asserting no wiring
```

Previous Jia artifacts under `../experiments/` are untouched.

## Scope compliance

Not merged. Production unchanged. OpenRouter $0 — Claude subscription only. No Article Form
Gate, no abstraction or altitude fields, no scene-provenance permissions, no section-break
rules, no pivot-paragraph rules. Research, Grounding, Fact Check, Selector and Writer doctrine
untouched. Local-main divergence not resolved.

The only change to a tracked engine file outside the experiment is the §2 labelling fix in
`continuity.py`: `solo_ratio` now reports `solo_ratio_interpretation: TELEMETRY_ONLY` and
`solo_ratio_vs_published`, and the signpost band declares
`applies_to: SIGNPOST_OPENER_RATE_ONLY`. Calibrated behaviour is unchanged; a test message that
claimed 0.83 was "inside the published 0.00–0.37" was false and has been corrected.

**One required step was not performed.** §22 asks for the current Continuity/Natural Prose
process on both A and B. It was not run; both drafts are raw Writer output. The ordering result
that decides this experiment does not depend on it, but the prose comparison would be more
trustworthy after an identical continuity pass, and that omission is mine rather than a finding.
