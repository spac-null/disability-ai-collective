# F10 ledger repair — cleared

## The defect

`F10`'s proposition appended a clause its own span did not carry:

- proposition: "HUD adopted the 30 percent figure in 1981; earlier public-housing
  programmes had used 25 percent, **and the threshold is traced to a 1969 amendment by
  Senator Edward Brooke**."
- support_span: "HUD adopted the 30% standard in 1981, evolving from a 25% threshold used
  in earlier public housing programs"

Read naturally, the article sentence made the **thirty** percent threshold date from 1969.
Primary law refutes it: 1969 capped rent at one-fourth; 30 per centum arrived in 1981. Not
a Writer, carrier or turn defect — a ledger freeze defect, faithfully reproduced downstream.

## The repair — five atomic facts, each inside its own span

| | proposition | span | source |
|---|---|---|---|
| F10a | rent standard is 30 per centum of monthly adjusted income | "30 per centum of the family's monthly adjusted income" | S6 |
| F10b | Pub. L. 97-35 added that subsection in 1981 | "1981 -Pub. L. 97-35 added subsecs. (a) and (c)" | S6 |
| F10c | rents may not exceed one-fourth of a low-rent tenant's income | "the rents fixed by public housing agencies may not exceed one-fourth of a low-rent housing tenant's income" | S5 |
| F10d | that cap is the Brooke Amendment, Pub. L. 91-152 | "``Brooke Amendment,'' which amended the United States Housing Act of 1937 to cap public housing rents (Pub. L. 91-152)" | S7 |
| F10e | Pub. L. 91-152 was enacted 24 December 1969 | "PUBLIC LAW 91-152-DEC. 24, 1969" | S5 |

New frozen sources: **S5** Statutes at Large vol. 83 (GPO) · **S6** 42 U.S.C. 1437a with
amendment notes (OLRC via GPO) · **S7** Federal Register, FHFA housing goals, footnote 13.

`F10c` initially said "The **1969** Act required…" — the new audit caught that its own span
carries no year, and the clause was removed. The date now lives in `F10e`, where its span
carries it.

## The regression — an audit, not a gate

`proposition_exceeds_span()` reports dates and titled persons a proposition asserts and its
span does not. The general form of this idea — every name and number must appear in the
span — flags **18 of 36** facts in this ledger, nearly all legitimate: a proposition names
its subject where the span says "he", or writes "HUD" where the span spells the department
out. A screen that cries wolf half the time gets skipped. Narrowed to the two shapes the
real defect was made of, it flags **2**.

Both remaining flags are genuine and are **left for the owner**, since only F10 was in
scope:

- **F13** — proposition says "$2,250 **in 2021**, when Citi Bike docks arrived… per
  StreetEasy"; its span was clipped to "the median asking rent was $2,250 … that figure grew
  to $3,800". Gothamist does carry the year and the attribution; the span under-quotes.
- **F27** (CUT, unused) — same shape, years 2020 and 2026.

Neither is an over-claim like F10's. Both are spans that stop too early.

## Grounder V1 — repaired ledger

26 facts checked · **26 GROUNDED** · 0 UNGROUNDED · 0 UNFETCHED.
Prose-scan hits fell from 5 to 2 as the primary law entered the source set; the two left are
known artifacts (`US Department` — the sources write "Department of Housing and Urban
Development"; `NYU Furman Center` — the source writes "NYU**'s**").

## Fact Check — the authoritative component, on trident

| | before repair | after repair |
|---|---|---|
| claims extracted | 8 | 7 |
| blocking contradictions | 0 | **0** |
| soft (EVENT/STAT) | 2 | **1** |
| unverifiable | 4 | **1** |
| runtime | 40.7s | 36.2s |

The two claims that failed last run are now **VERIFIED**:

- C02 "HUD adopted the thirty percent figure in 1981" — *"the 30% benchmark was raised in
  1981 by Congress and then used by HUD as the affordability standard"*
- C03 "The Brooke Amendment dates to 1969" — *"enacted in 1969 as part of the Housing and
  Urban Development Act of 1969"*

### The one advisory, stated plainly

**C04 (STAT, CONTRADICTED, non-blocking).** "Median household income in the community
district covering Windsor Terrace and Sunset Park was about $97,000 in 2024" — the checker
cites NYC Planning's Community Profiles for Brooklyn CD7 at $55,816.

This is a source-versus-source divergence, not a reporting error. The article does not
assert the figure; it attributes it — *"per an analysis by the NYU Furman Center"* — which
is exactly what its ledger fact (`F12`) is typed as, `ATTRIBUTION`, and Grounder V1
confirmed the sentence reproduces Gothamist verbatim. Under the authoritative Fact Check's
own policy a STAT contradiction is advisory, and no new policy was invented here.

It is worth the owner's attention on its own terms: two public bodies publish very different
median incomes for the same district, and the gap is large. That is a question for the
Furman Center's figure, not for the article's accuracy in reporting it.

The remaining UNVERIFIABLE (C06, "$3,800 five years later") is a search-coverage limit; the
figure is grounded verbatim in the frozen source.
