# RQ1 — can `reader_now_wonders` be verified against what readers actually wonder?

Two datasets. Published prose (n=30, blind-scored by an independent judge) and the Jia B
article (n=5, scored against a blind per-boundary read).

## 1. Published prose, n=30

The architect wrote `reader_now_wonders` from the delivered material plus the approved next
material. Eight separate blind readers, who never saw a continuation, wrote what they actually
wanted to know. A third blind judge scored agreement without being told which answer was
which, or that a research hypothesis existed.

| verdict | n | share |
|---|---|---|
| STRONG_MATCH | 11 | 37% |
| PARTIAL_MATCH | 8 | 27% |
| NO_MATCH | 5 | 17% |
| architect said NONE, reader had a question | 5 | 17% |
| **ARCHITECT_INVENTED_PRESSURE** (architect asserted a need the reader did not feel) | **1** | **3%** |
| BOTH_NONE | 0 | 0% |

**At least partial agreement: 19/30 (63%).** The invented-pressure rate is 3%.

The asymmetry matters more than the headline. When the architect was wrong it under-called
pressure five times and over-called it once. Under-calling produces a `CONTINUES` plan, which
is the harmless direction; over-calling is what manufactures a question the reader does not
have.

**Specificity gap.** The judge rated the architect's questions SPECIFIC in 19/30 and GENERIC in
11/30. Real readers were SPECIFIC in 27/30. The architect is measurably less anchored in the
passage's own material than a reader is.

## 2. Jia article B, n=5

The reader-state architecture's own `reader_now_wonders_leaving` values, against what a blind
per-boundary reader of the finished B article said they wanted at the matching boundary.

| boundary | architect predicted | blind reader wanted | verdict |
|---|---|---|---|
| after S1 | *What was one of these eight pavilions actually made of?* | *So what do the eight entries actually describe?* | PARTIAL_MATCH |
| after S2 | *What did all that sensory material amount to for anyone standing inside it?* | *Does the account ever say what visitors actually experienced, or only what the designers intended?* | **STRONG_MATCH** |
| after S3 | **NONE** | *Is this pattern of crediting the materials, never a person, going to be the article's actual point?* | architect said NONE, reader had a question |
| after S4 | *What was the sand like to stand on?* | *Will the piece now name the pattern outright?* | **NO_MATCH** |
| after S5 (end) | **NONE** | *NOTHING IN PARTICULAR* | **BOTH_NONE** |

Two of five aligned (one strongly), one both-none, one under-called, one missed. On a sample of
five this is indicative only, and it is consistent with the published-prose rate rather than
better or worse than it.

The `after S4` miss is the informative one. The architect predicted the reader would want the
sand's felt quality — *what was the sand like to stand on?* — which is the sensation the whole
article exists to say was never recorded. The reader instead wanted the article to name its
pattern. The architect modelled the reader as wanting the thing the article withholds; the
reader wanted the thing the article was about to deliver. That is a plausible-sounding
prediction about reader desire which the reader did not share, and it is exactly the class of
error the four-field split is meant to make visible.

## 3. Answer

**`reader_now_wonders` can be partly verified, and the verification is worth having.** It
agrees with an independent reader of the same text about two-thirds of the time, its errors are
mostly in the safe direction, and — unlike `why_reader_wants_next` — a disagreement can be
detected at all. That is the whole difference: one field can be checked against something
outside itself, the other cannot.

But it is not *reliably* verified. One in six predictions pointed at genuinely different
material, and the architect is systematically less specific than a real reader. Treating the
field as a description of the reader would overstate what it is. Treating it as a **falsifiable
proposal about the reader, which a second pass can check**, is what the evidence supports.
