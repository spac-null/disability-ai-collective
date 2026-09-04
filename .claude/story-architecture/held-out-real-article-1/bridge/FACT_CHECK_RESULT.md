# Fact Check — ran on trident, PASS by contract, HELD by reading

`python3 automation/heldout_factual_bridge.py --fact-check`, isolated clone at
`/tmp/heldout-fc`, credentials from `/srv/secrets/openclaw.env`. Production workspace
untouched; no cron, no defaults, not merged.

## Grounder V1

22 facts checked · **22 GROUNDED** · 0 UNGROUNDED · 0 UNFETCHED.
`F10` grounded through the official fallback: all five component assertions verified
against Pub. L. 91-152 (GPO) and 42 U.S.C. 1437a with amendment notes.

## Fact Check

`FactCheckMixin._run_web_fact_check(claim_cap=8, strict=True)`

| | |
|---|---|
| extraction | ok |
| claims extracted | 8 |
| completed | True |
| blocking contradictions | 0 |
| soft (EVENT/STAT) contradictions | 2 |
| unverifiable | 4 |
| not checked | 0 |
| runtime | 40.7s (49.1s whole run) |
| provider calls | 9 — 1 extraction (claude-haiku-4.5 via CLIProxy) + 8 verifications (Perplexity Sonar via OpenRouter) |

Component status: **PASS** — QUOTE/STUDY contradictions block; EVENT/STAT are advisory.

## The failing claim

**C04 — CONTRADICTED (EVENT).** Article paragraph 5, third sentence:

> "The threshold is traced to a 1969 amendment by Senator Edward Brooke."

The two sentences before it are "HUD adopted the thirty percent figure in 1981. Earlier
public-housing programmes had used twenty-five percent." So "The threshold" most naturally
reads as the thirty percent one, and the extractor read it that way: *"The thirty percent
threshold is traced to a 1969 amendment by Senator Edward Brooke."*

On that reading it is wrong, and the fact check says so:

> "Senator Edward Brooke's 1969 amendment set public-housing rent at 25%, and the 30%
> threshold was raised later in 1981, so tracing the 30% threshold directly to the 1969
> amendment is inaccurate."

This is **independently corroborated by the primary law this same run used to ground F10** —
the two checks agree against the article:

- Pub. L. 91-152 (Dec. 24, 1969): rent "shall not exceed **one-fourth** of the family's
  income" — the Brooke Amendment set 25%.
- Pub. L. 97-35, title III, §322(a) (Aug. 13, 1981): added the subsection carrying
  "**30 per centum** of the family's monthly adjusted income".

**Where it came from.** `F10`'s frozen proposition already carries the ambiguity, and
carries it beyond its own evidence:

- proposition: "HUD adopted the 30 percent figure in 1981; earlier public-housing programmes
  had used 25 percent, **and the threshold is traced to a 1969 amendment by Senator Edward
  Brooke**."
- support_span: "HUD adopted the 30% standard in 1981, evolving from a 25% threshold used in
  earlier public housing programs"

The Brooke clause is **not in the support span**. It was added to the proposition at freeze
time and no gate has ever compared a proposition against its own span — every check in this
programme so far has taken the proposition as given. The Writer then reproduced it faithfully,
which is what it is supposed to do.

So this is not a Writer defect, not a turn defect, and not a carrier defect. It is a **ledger
defect**: a frozen fact asserting more than the span under it.

## The other contradiction — a false positive

**C06 — CONTRADICTED (STAT).** "Median asking rent in the area was $2,250 in 2021."
The checker compared against **citywide** StreetEasy figures ($2,700 Q1/Q4 2021, $2,699 Q3).
The article says *in the area* — Windsor Terrace / Sunset Park — and Gothamist attributes
exactly that neighbourhood figure to StreetEasy. Grounder V1 confirmed the article reports
its source verbatim. A neighbourhood median is not a citywide one; no defect here.

The four UNVERIFIABLE results (C03, C05, C07, C08) are search-coverage limits, not
contradictions; C08's own reason text in fact supports the claim.

## Verdict

Not cleared. The component passed it because an EVENT contradiction is advisory by design,
but C04 is a real inaccuracy on the most natural reading, agreed on by two independent checks,
and the article should not be published carrying it.
