# Phase 1.6 — Source-Grounding Hardening (design, not implemented)

Authoritative design document for the next blocking phase. Promoted ahead
of Phase 2 (brevity/evidence/testimony) — see `current-work.md`'s roadmap.
**No code changes, no generations have been made against this design yet.**
This document says what to build; it is not a log of what was built.

## Why this phase exists

Phase 1.5B's brief audit (`experiments/fable-review-roi-2026-08-10.md`)
found that all 4 audited frozen planning briefs contain at least one
source-unsupported factual element in `resisting_example` or
`correction_moment`, written by Fable at planning time. The causal chain:

```
FABLE PLANNING BRIEF — invents named individual + testimony/quote,
   no source-verification step (confirmed, 4/4 topics)
   ↓
WRITER — inherits and incorporates the invented material, typically as
   paraphrase (confirmed, 8/8 raw drafts)
   ↓
REVIEW (Fable/Opus) — source-blind, cannot verify or catch it, sometimes
   demands "the real words" not knowing the person doesn't exist
   ↓
EXECUTOR (Opus) — source-blind, converts invented paraphrase into a
   fabricated verbatim quotation to comply (confirmed, 4/8 Fable-
   triggered, 1/8 Opus-triggered)
```

A prose "don't hallucinate" instruction is insufficient: we already
watched two frontier models confidently invent a named person, then
separately discuss "retrieving her real words from the record" — the
current brief/review prompts already gesture at not fabricating ("a brief
is an assignment to go find something out, not a conclusion") and it did
not work. **Make grounding machine-checkable, not aspirational.**

Fix all four substeps below in the SAME hardening phase, not sequentially
deferred: the causal chain shows sequential amplification (planner
invents → writer naturalizes → reviewer demands a stronger version →
executor turns it into quotation) — fixing only the planner leaves stages
3-4 free to manufacture NEW unsupported specificity from otherwise
now-legitimate paraphrase.

## 1. Planner grounding

`_fable_editorial_brief` currently receives only `news_title` +
`news_summary[:400]` (a ~400-char truncated summary), never the full
`source_text` — an even narrower window than the writer gets later. Give
it the actual source/evidence.

Change the schema from a flat string:
```json
"resisting_example": "Deborah Antwi supported..."
```
to a structured object carrying provenance:
```json
"resisting_example": {
  "text": "...",
  "evidence_type": "source" | "interpretive_move" | "none_available",
  "source_excerpt": "...",
  "source_locator": "paragraph/chunk identifier"
}
```
Same structure for `correction_moment`.

**Do not use a loose schema where `evidence_type = interpretive_move`
becomes a loophole for fabricated facts.** Separate the editorial NEED
from the evidence CANDIDATE explicitly — they are different fields with
different failure modes:
```
editorial_need:
  "A resisting case would test the thesis."

evidence_candidate:
  status: found | not_found
  source_span_ids: [...]
  fact_summary: ...
  direct_quote: null | exact quote
```
Interpretive reasoning is a separate field and must not introduce new
factual claims — an `interpretive_move` may reframe or connect evidence
already present, it may not add a name, quote, date, number, or event
that isn't in the source.

The planner MUST be allowed to output `evidence_candidate.status ==
"not_found"` / `evidence_type == "none_available"`. Editorial need does
not imply the evidence exists. The system currently seems designed around
always producing the requested editorial object rather than admitting the
source doesn't contain one — that's the actual mechanism to fix, more
than any single prompt's wording. For named people, quotations, dates,
numbers, specific events: require an evidence pointer, or the claim
doesn't reach downstream generation at all.

## 2. Deterministic, non-LLM validator

Sits between planner and writer. Do not rely on the writer to police a
bad brief; the writer should not be the principal fact-checker of its own
planner.

Simple, high-value, non-LLM checks:
- **Direct quotation** — exact source-span match required (substring
  match against the supplied source text).
- **Source pointer** — must resolve (the referenced `source_locator`/
  `source_span_ids` must exist in the document).
- **Named person** — must occur in the referenced evidence span.
- **Date/number** — must occur in the referenced evidence chunk.
- **`status == "not_found"`** — the corresponding factual candidate
  field must actually be absent/null; a `not_found` status paired with a
  populated `direct_quote` or named claim is itself a validation failure.
- **Required evidence field isn't empty when `evidence_type == "source"`.**

An invalid/unproven evidence candidate must not reach the writer prompt —
only validated evidence does. This won't prove every paraphrase is
semantically faithful to its source (substring matching doesn't verify
arbitrary paraphrase fidelity) — it closes the catastrophic "invent
Deborah Antwi and treat her as source material" path specifically, which
is the failure mode actually observed. Preserve source-span provenance on
every validated item so later models/humans can inspect it.

## 3. Source-aware reviewer

The reviewer currently receives only `brief_angle` (a short editorial
question) — never the source or evidence package, and (per the static
prompt audit in `experiments/fable-review-roi-2026-08-10.md`) the shared
review prompt has a real, if partially-offset, structural lean toward
finding something to flag.

Change: give the reviewer the source/evidence packet, plus an explicit
contract — it may not demand "real words," statistics, named-person
testimony, or record evidence unless that evidence is actually available
in the supplied packet. A request for stronger evidence must cite what's
available to strengthen toward, not gesture at evidence that may not
exist.

Do not solve the separate interventionist-lean/model-choice question
(both Fable and Opus said revise 8/8, while raw-only blind judges produced
7/16 publish_as_is and 7/16 minor_revision) inside Phase 1.6 unless
necessary for grounding safety — that's the still-paused Phase 1.5B
model-seat decision, not this phase's scope.

## 4. Source-aware executor

Same evidence packet as the reviewer. Hard constraint: never convert
paraphrase into quotation, and never introduce a new quotation,
statistic, date, number, named-person statement, or source-specific
detail that isn't already in the draft or in the supplied evidence
packet. If a review note demands evidence that does not exist in the
packet, the executor must preserve the passage as-is and report the
instruction as unsupported, rather than inventing material to comply.

## Acceptance design

Must include NEGATIVE and POSITIVE controls — success on cooperative
sources alone doesn't prove anything, since the current pipeline already
looks fine on those.

**Negative/adversarial controls** — sources deliberately LACKING:
- a named disabled witness,
- a direct quote,
- a resisting anecdote.

Success: the planner/reviewer correctly outputs "not available in
source" / `not_found` rather than inventing a plausible-sounding
substitute. This is the behavior that actually needs proving — whether
the system still produces pretty articles on cooperative sources is not
the test.

**Positive controls** — sources deliberately CONTAINING:
- a named witness,
- an exact quote,
- concrete resisting evidence.

Success: the planner extracts the correct source span; the validator
accepts it; the writer preserves the quote/paraphrase distinction; the
reviewer/executor can use the evidence without factual mutation.

## After Phase 1.6 lands

- A small grounded WHY-WE-WRITE smoke confirmation only (one clean,
  verifiably-grounded source × two personas, or four clean single
  samples) — confirms the doctrine doesn't interact badly with a
  properly-sourced plan; this is verification of an existing decision
  (see `experiments/why-we-write-2026-08-10.md`), not reopening it. Do
  not rerun the full 12+12 doctrine experiment.
- Then a small grounded review-seat follow-up before the final
  Fable-vs-Opus review-seat decision (Phase 1.5B, paused — see
  `experiments/fable-review-roi-2026-08-10.md`).
