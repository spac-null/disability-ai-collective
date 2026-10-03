# Crip Minds STRIP list — overnight run, 2026-10-02 → 03

## The finding that matters more than the code

**Three of the four STRIP items were wrong as written.** The list was built from a
measurement that said "26 distinct tokens have ever blocked a run on the factual-surface
screen and every one is a false positive". Checked against the record one item at a time,
that claim did not survive.

| | item as written | what measuring it showed |
|---|---|---|
| 1 | entities become advisory / phrase repair | would let invented `NASA`, `DWP`, `June`, `April` reach publication. **Parked** |
| 2 | stop `A$90 million` yielding `90` | the reverse — `A$90m` yielded **nothing**, so an invented `A$250m` was never screened. **Shipped**, on the fourth shape |
| 3 | remove CUT from the free path | already done by design; "finishing" it would strip a live gate from the planned path. **Parked** |
| 4 | collapse duplicated definitions | neither duplication exists. **Parked** |

The one real defect was the one item whose description had it backwards.

## What shipped

**Item 2** — `fix: the factual-surface screen reads a figure wearing a unit suffix`
commit `1127a67`, merge `9b7f3dd` on `origin/main`, live at
`/srv/data/hermes/workspace/disability-ai-collective`.
Gate: **134 pass / 26 fail, no regressions** against baseline `28960e35`.

`_numbers`' trailing `\b` cannot hold between a digit and a letter, so `A$90m` produced no
token at all while `A$90 million` produced `90`. That caused the one number ever to block
a run in the record (`production-20260905T210605Z-2d62633a`) — and, far worse, meant prose
could carry an invented `A$250m`, `5km` or `20kg` past a HARD screen that saw no figure
there. Falsified: on the clean tree the invented-`A$250m` test fails with `[]` and
`hard_ok` True. **That escape was live.**

It took four shapes, and the three failures are the useful part — none was about numbers:

- **A** — make `A$90m` yield the bare `90`. One line, fixes everything. Also lets an
  approved `A$90m` license a prose **"90 deaths"**, which blocks today. Rejected.
- **B** — add `90m` to `_numbers` alongside its existing tokens. No licensing problem, and
  it broke something three files away: `_numbers` feeds **CUT watch-term selection**,
  which pushes results first, longest first, into a **capped** list. Six suffixed figures
  in a cut fact pushed the identifier `abc123` off the end and a hard `CUT_LEAKAGE`
  finding became a pass. A gate lowered by a fixed-size budget, not by anything about
  tokens. Rejected.
- **C** — confine the reading to `factual_surface_audit`, both sides. Lowered nothing, and
  newly **held** an article whose own dek abbreviated its own figure (`50 kilometres` →
  `50km`), through the package screen. Rated the likeliest shape in real copy. Rejected.
- **D** — shipped. A suffixed figure is new only if its **numeral** is new. The numeral is
  the figure; the suffix is how it is written.

115 of 115 record runs unchanged. 17 tests, registered and count-checked. 6 guards severed
one at a time, 6 caught. Fourth adversary pass: no blocker.

Deliberately not fixed, pinned by a test: a packet saying `A$90m` and prose saying `A$90
million` still disagree. Closing that needs variant A's trade, which is the owner's call.

**Baseline regenerated and repointed.** Clean-tree run at the shipped SHA:
160 suites, 134 pass / 26 fail, `code_sha 9b7f3dd`, `tree: clean`.
`/srv/data/cripminds-qa/current.txt` now carries it (previous baseline kept as
`current.txt.bak-2026-10-03`; the run is also at `suites_baseline_9b7f3dd.txt`).
The three held `assets/*.jpg` are back in the build clone, which is at `9b7f3dd` with
nothing dirty but those untracked jpgs.

## What was parked, and why

**Item 1 — entity phrase repair.** Measured on the record: 25 gate-path entity flags, of
which 8 are correct refusals with confusing labels, 11 are single tokens the repair cannot
help, and 6 are real false positives. Of those 6, two were already fixed by passing the
Ledger into the audit, and four (`CULT`, `DEATH`, `REAL`, `SATANIC`) turn out to be a
**casing** problem — the phrase is in the packet, in ordinary case, and `_entities`
compares case-sensitively. The patch "fixes" them by deleting every ALL-CAPS token, which
is why `NASA` and `DWP` escaped. The suite caught it too: `safety_matcher_precision_test`
has a named check, *"an all-caps acronym in the title is still an entity"*, whose case is
literally **NASA**.

**Item 3 — CUT on the free path.** `free_composition.py` already hands Safety `cut = {}`
— "nothing was cut, so nothing can leak" — deliberately, with its measurement in the
docstring. Confirmed on a live run: `cut_declared: 0, violations: 0, ok: True`. The record
shows 0 CUT_LEAKAGE holds in 9 free runs against 10 in 175 planned runs, and the audit is
**shared**, so deleting the machinery would remove a working gate from the planned path.
The cited "23 blocks, 13 sole cause" could not be reproduced — I count 10, and my first
attempt at "sole cause" counted stage statuses as findings, so no figure is claimed.

**Item 4 — duplicated definitions.** `composition.py` contains the string `deadline`
**zero** times. And `negative_shape_of` is already the single shared owner used by the
permission compiler, the free path and the audit — explicitly so they "cannot disagree
about what a negative is". The both-vs-either difference is two different questions, and
the stricter side is owner-directed from 2026-09-10 with a retained production proof.

## My own measurements were wrong five times

Each error changed the answer, and each was caught only by checking the artefact by hand:

1. counted `RESEARCH_PACK.json` as approved material — it is raw source and licenses nothing
2. counted `EDITORIAL_PACKAGE.json` as approved — it holds only generated output (title,
   dek, excerpt), so matching an audited title against it is self-licensing
3. read only `LEDGER.json`, leaving the approved blob **empty** for seven pre-Ledger-era
   runs whose approved material is `WRITER_PACKET.txt` — every fragment in them read as
   "unlicensed" vacuously, and it produced a verdict I had already written down
4. treated a missing artefact as a refusal rather than reporting `NO_APPROVED_ARTEFACT`
5. included `architect_prose_telemetry` in proportions — it gates nothing and is **85 of
   the record's 207** entity flags

## Open, for the owner

- **The state notes in `.claude/patches/` are untracked.** They hold the measurements
  behind every verdict above. Commit them if you want them kept.
- **Case-folded entity comparison** would fix item 1's four ALL-CAPS false positives
  without dropping the class. Identified, not authorised, not built.
- **The `A$90m` / `A$90 million` false positive** needs variant A's trade to close.
- **Two patches remain parked and unshipped**: `parked-entity-advisory.patch` (marked
  do-not-ship) and `parked-editorial-record.patch` (the desk's editorial signals reaching
  the Writer — tested, falsified, one command from live, awaiting your word).
