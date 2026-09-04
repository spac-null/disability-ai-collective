# RQ1 — blind A/B on the Jia article

`article_one` = **B**, the reader-state architecture. `article_two` = **A**, the control using
the current `why_reader_wants_next`. Randomised with a fixed seed; no evaluator was told which
was which, that one was experimental, or that a hypothesis existed. Labels are decoded here
only.

Identical inputs: same frozen ledger, same eleven facts, same thirteen declared cuts, same
lens, same ending move, same eleven prohibitions, same article type. **Fact parity verified
IDENTICAL.** Both drafts written by separate agents from a rendered packet, with identical
writing instructions.

## 1. Two independent blind comparators

| criterion | comparator 1 | comparator 2 | net |
|---|---|---|---|
| would publish / overall | **B** | **B** | **B** |
| **information order** | **A** | **A** | **A** |
| **visible machinery / scaffolding** | **B worse** | **B worse** | **B worse** |
| semantic compression | A worse | A worse | B better |
| the idea landed more surely | **B** | **B** | **B** |
| ease of entry | A | — | A |
| explanation timing | A | — | A |
| momentum | B | — | B |
| breathing room | B | — | B |
| plain, natural reading | B | — | B |
| concrete material | B | — | B |
| ending | B | — | B |
| would keep reading | B | — | B |
| invented / overclaimed | found in both | found in both | both |

**B is the better piece of writing and has the worse information order.** Both comparators
reached that split independently, and both located the same fault in the same place.

## 2. The ordering fault, in the evaluators' own words

Comparator 2:

> *"ONE spends its entire second paragraph on meta-argument before a single pavilion exists on
> the page… The reader has been given no room, no salt, no sand — nothing yet worth losing — so
> the claim about what the record fails to keep arrives before there is anything for it to be
> about. TWO holds the same material until paragraph 13, after the salt walls, the sand and the
> rain chains have been seen."*

Comparator 1:

> *"Two holds the festival logistics until line 11, where the dates actually do work… whereas
> One front-loads dates and then the entire selection thesis long before there is anything for
> it to be about."*

This is a direct contradiction of the experimental architecture's own stated reasoning for its
single biggest reordering. The B architect wrote:

> *"The reader needs a place and a frame before any material can register, so the shoreline and
> the account's eight come first."*

Two independent readers said the opposite: the frame cannot register until there is material
for it to frame. The reader-state model produced a confident, articulate, and wrong claim about
what a reader needs — and it produced it at the one place where it departed most from the
control.

## 3. Scaffolding

B contains one signpost opener; A contains none.

> B: *"Read across all eight of the entries, a pattern in what they contain becomes plain."*

Both comparators named it unprompted, comparator 2 adding that it *"flatters itself with
'becomes plain' before showing anything."* A's nearest equivalent — *"What the eight
descriptions carry is a particular kind of information"* — was called *"a section header in
sentence costume"*, so A is not innocent, but the detector and both humans-in-role agree B is
worse.

This is the leakage risk the format comparison predicted: the internal question became a
reading instruction. It did not become a *rhetorical question* — question marks are zero in
both — but the ordering model surfaced in the prose anyway, in the one form the brief did not
enumerate.

## 4. Per-boundary reader-state evaluation (§25, "the most important evaluation")

A blind reader worked through each article one paragraph at a time, stating what they
understood and what they wanted next, then judging how the next paragraph felt.

| | boundaries | NATURAL | SLIGHTLY_FORCED | UNRELATED / OVEREXPLAINED / TOO_EARLY / TOO_LATE |
|---|---|---|---|---|
| **A** (control) | 11 | **10 (91%)** | 1 | 0 |
| **B** (reader-state) | 8 | 6 (75%) | 2 | 0 |

**A scored better on the test the brief calls most important.** Neither article produced an
UNRELATED, OVEREXPLAINED, TOO_EARLY or TOO_LATE judgement, so both are within tolerance — but
the control's transitions felt natural more often than the experiment's.

B's two frictions, in the reader's words: *"the piece pivoted to meta-commentary about the
record slightly before I had enough concrete material to want that reflection"* — the same
fault, found for a third time by a fourth evaluator.

## 5. Safety comparison (§23)

| | A (control) | B (reader-state) |
|---|---|---|
| hard factual-surface signals clean | **NO** — unapproved scene term `screen` | **YES** |
| unapproved numbers / entities / sensory | none | none |
| CUT violations | 0 | 0 |
| negative-admission audit | **FAIL** — 1 unmatched negative sentence | **PASS** — 0 unmatched |
| provenance-frame leaks | 0 | 0 |
| scaffold-name leaks | 0 | 0 |
| intent/causal assertions | 0 | 1 |
| question serialization | 0 | 0 |
| question marks in body | 0 | 0 |

The mechanical audits favour B: it is the only one of the two that passes both the hard
factual-surface gate and the negative-admission audit. But the brief's bar is *zero* on all
four counts for both, and **neither draft meets it** — A fails on two, B carries one
intent/causal assertion. And both blind comparators independently found unsupported claims that
no mechanical audit caught, in both drafts:

- A: *"People went inside it."* — flatly asserted, in an article whose thesis is that no visitor
  perception was recorded. Also *"After the fifth day the pavilions came down"*, which the
  ledger does not support.
- B: *"The eight descriptions of it do not have an end date"* — called *"a figure of speech
  dressed as a fact"*. Also *"it travelled"*, asserted and unevidenced.

Reader-state planning did not purchase better prose with factual invention. It also did not
prevent it.

## 6. Anti-overfitting check (§28)

Did B win its prose criteria because reader-state helped, or because it got more paragraphs,
shorter sentences or more questions?

| | A | B |
|---|---|---|
| words | 615 | 609 |
| **paragraphs** | 12 | **9** |
| sentences | 43 | 41 |
| mean sentence length | 14.30 | 14.85 |
| sentence-length IQR | 10 | 11 |
| single-clause share | 0.581 | 0.659 |
| commas per sentence | 0.74 | 0.68 |
| ≥4-clause share | 0.047 | 0.049 |
| question marks | 0 | 0 |
| solo paragraphs | 0 | 0 |

**None of the cheap explanations holds.** B has *fewer* paragraphs, not more. Sentence length is
marginally *longer*. Question count is identical at zero. The only real difference is an 8-point
gain in single-clause share, which is consistent with B being less compressed — the one prose
criterion both comparators agreed on.

So B's prose advantage is real and is not an artefact of fragmentation. **But it is confounded:**
A and B were written by two different agents. Nothing in this design separates "the reader-state
packet produced better prose" from "the second writer wrote better prose". With n=1 draft per
arm, the prose comparison cannot be attributed to the architecture at all.

The *ordering* comparison is the one that can be attributed, because the order was fixed by the
architecture rather than chosen by the writer. And on ordering, the experiment lost.

## 7. Confounds and limitations

1. **One draft per arm.** Everything about prose quality is unattributable.
2. **Different writer agents.** Not controlled.
3. **Packet length differed**: A 783 words, B 943. B's architect wrote longer section
   descriptions. Not the variable under test, and not normalised, because normalising would
   have meant rewriting B's content by hand.
4. **All evaluators are language models**, not human readers. The published-prose study at
   least used eight of them independently; the Jia A/B used four.
5. **B's architecture fails the authoritative validator by construction** —
   `validate_architecture` requires `why_reader_wants_next` on every non-final beat, which is
   the field being replaced. Recorded, not worked around.
6. **No Continuity pass was run on either draft.** Both are Writer output. Comparing them after
   an identical continuity stage would be a better test and was not done here.
