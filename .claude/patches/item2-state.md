# STRIP item 2 — the number tokeniser: SHIPPED 2026-10-03

**Gate: 134 pass / 26 fail, NO REGRESSIONS** against baseline `28960e35`. (26 is the
known pre-existing count; item 1's run showed 28 because of its two regressions.)

- commit `1127a67` on `fix/number-tokeniser-unit-suffix-2026-10-02`
- merge `9b7f3dd` → `origin/main`
- **deployed**: `/srv/data/hermes/workspace/disability-ai-collective` is at `9b7f3dd`
- baseline regenerated at the shipped SHA on a clean tree: 160 suites, 134 pass / 26 fail,
  `code_sha 9b7f3dd`, `tree: clean`. `/srv/data/cripminds-qa/current.txt` repointed
  (previous kept as `current.txt.bak-2026-10-03`); held assets restored to the build clone


**Branch** `fix/number-tokeniser-unit-suffix-2026-10-02`, base 37884dc = origin/main = live.
Worktree: session c586b819 scratchpad, `num/`.

## The item was written backwards

"Fix the tokeniser so `A$90 million` does not yield the token 90" — but the prose yielding
`90` is correct. The defect is on the other side:

```
_numbers = set(re.findall(r"\b\d[\d,.]*\b", text))
```

The trailing `\b` cannot hold between `0` and `m`, and the regex finds no shorter match,
so **`A$90m` yields no token at all**. Measured on
`production-20260905T210605Z-2d62633a`: packet `A$90m`, prose `A$90 million`, `90` blocked
as unapproved — the only number ever to block a run in the retained record.

**The false positive is the mild half.** `90m`, `5km`, `20kg`, `3bn`, `1990s`, `19th` are
invisible to the HARD numbers screen on BOTH sides, so prose can carry an invented
`A$250m` and nothing looks at it. Falsified: with clean `story.py` the test
"an invented figure in suffixed notation is caught" fails with `[]` and `hard_ok` True.
**That escape is live in production right now.**

## THE SHIPPED SHAPE IS VARIANT D — adversaries rejected A, B and C

**Variant D:** `_numbers` byte-for-byte unchanged. `_figures_with_units()` reads
case-folded unit-suffixed figures. `_unit_figure_leaks(body, approved, a_nums)` is called
only from `factual_surface_audit` and refuses a prose suffixed figure **only if the
approved side grants neither the same token nor its bare numeral**.

```
invented   approved "A$75 million"      prose "A$250m"    -> ['250m']  BLOCKS
notation   approved "50 kilometres"     prose "50km"      -> []        clean
same       approved "A$90m"             prose "A$90m"     -> []        clean
cross-use  approved "A$90m"             prose "90 people" -> ['90']    BLOCKS
```

Record-wide: **115 of 115 runs unchanged**. 17 tests, registered and count-checked.
6 guards falsified, all 6 caught.

**Fourth adversary pass: no blocker found.** Verified by grep that the only production
call to `_unit_figure_leaks` is `factual_surface_audit`, that `_figures_with_units` is
called only by that helper, and that no `_numbers` caller changed — CUT selection
included. D's flags are a strict subset of C's for a fixed approved surface, so it cannot
remove an old bare-numeral block. C's five new-hold shapes: four **fixed** by D
(`50 kilometres`, `50 km`, `50-km`, `50**km**` → `50km`), one remains at MINOR and low
likelihood (`A$90million` → `A$90m`).

Residuals, recorded and accepted:
- **MAJOR, not a regression:** approved `250 homes` → prose `A$250m` passes, because the
  numeral `250` is licensed for a different fact. It passes **today as well** — D is
  strictly better here, never worse. An exact numeral reused for a different fact is
  moderately likely in a figure-rich article; closing it needs unit-aware licensing,
  which is the design question, not this patch.
- **MINOR, pre-existing:** `_numbers("1,000kg")` is `{"1,"}` because the trailing `\b`
  backtracks onto the comma, so `1,000 kilograms` → `1,000kg` holds through the unchanged
  bare-numeral path. True today; untouched here.

**Why C was rejected.** C added unit tokens to both sides of the audit. No loosening — the
adversary confirmed no old block becomes a pass — but it created a **new hard hold** on
the most likely shape in real copy: article "50 kilometres", dek "50km". That reaches the
package screen through `composition.py:3813`, which calls this audit. Holding an article
because its dek abbreviated its own figure is exactly the defect the STRIP list exists to
remove. D's rule — the numeral is the figure, the suffix is how it is written — emits a
strict subset of C's flags, so it cannot loosen either.

## Earlier rejected shapes

**Variant C:** `_numbers` is **byte-for-byte unchanged**. A new helper
`story._figures_with_units()` reads case-folded unit-suffixed figures and is used ONLY
inside `factual_surface_audit`, on both sides. Grammatical suffixes (`107th`, `3rds`,
`1990s`, `2nd`, `5s`) excluded; separator run bounded to 20.

Record-wide: **115 of 115 runs unchanged**. 16 tests, registered and count-checked.
5 guards falsified, all 5 caught.

**Why B was rejected — a tested BLOCKER, and a mechanism I did not anticipate.**
`_numbers` feeds CUT watch-term selection at `composition.py:2535`, which pushes its
results FIRST, longest first, into a **capped** candidate list. Extra tokens *displace*
later candidates: with a cut fact carrying six suffixed figures, the identifier `abc123`
fell off the list and a hard `CUT_LEAKAGE` finding became a pass. An old hold becoming a
new pass is a loosening whatever its mechanism — and this one came from a fixed-size
budget downstream, not from token semantics at all. Confining the new reading to the one
screen that needs it removes the entire class: CUT identity, CUT candidates, the repair
parser, the package check, continuity deltas, the per-100-word metric and translation
parity all behave exactly as they do today. `test_the_number_tokeniser_itself_is_unchanged`
is the guard.

Also from that pass: case is now folded, because approved `A$90M` vs prose `A$90m`
produced a NEW hold on typography alone; and the separator run is bounded, because the
unbounded form is quadratic (8,000 chars ≈ 0.19s).

## Variant B (rejected) and variant A (rejected)

**Variant A (symmetric, rejected):** `{t.rstrip(".,") for t in re.findall(r"\b\d[\d,.]*", text)}`
— makes `A$90m` and `A$90 million` the same token `90`. It fixes the false positive AND
closes the blindness, but the adversary constructed a real loosening: an approved `A$90m`
would then license a prose **"90 deaths"**, which blocks today. Record evidence was
reassuring (2 fixes, 0 tightenings; both fixes same-figure-same-meaning, `28C` ↔ `28
degrees`) but the case is constructible, and "the record doesn't show it" is exactly the
reasoning that was wrong about item 1. Not shipped.

**Variant B (shipped):** bare-numeral tokens are left **exactly** as they were; a figure
with a non-grammatical suffix adds its own token (`90m`). The approved side therefore
gains nothing that can cover a bare numeral, so no case that blocks today can pass — the
only possible movement is MORE flags. Record-wide: **115 of 115 runs unchanged**.

What B deliberately does NOT fix: the measured false positive (packet `A$90m` vs prose
`A$90 million`) is still there, pinned by a test named
`test_the_two_notations_still_disagree_and_that_is_on_purpose`. Closing it requires
variant A's trade, which is the owner's call.

Grammatical suffixes (`107th`, `1990s`, `2nd`) are excluded — `107th` was the one and only
tightening B produced across the record before that exclusion. `composition.py:4471`
already pre-substitutes an `_ORDINAL` regex, so the codebase knew.

## The change

```
{t.rstrip(".,") for t in re.findall(r"\b\d[\d,.]*", text)}
```

Separators are stripped explicitly because, without the boundary forcing a backtrack, the
greedy class swallows them and `2018,` must stay `2018`.

## Evidence

- **Record-wide impact** (`scratchpad/measure_num_impact.py`, 115 runs scored, era-correct
  approved artefacts): **2 fixes** (`90`, and `28` in …60910T110024Z), **0 tightenings**.
  No run starts flagging. 113 unchanged.
- **Tests**: 4 new in `safety_entity_extraction_test.py`, registered in `main()` and
  verified present (12 declared, 12 registered). All 4 fail on clean `story.py` —
  including the safety one.
- **Suite**: running on trident, `/tmp/suites_item2.txt` vs `/srv/data/cripminds-qa/current.txt`.
- **Adversary**: `codex exec --sandbox read-only`, asked to construct counterexamples
  (unicode digits, fractions, ranges, versions, dates, times, scientific notation,
  locale separators, figures inside words) and to check caller symmetry.

## Next

Read both results, address BLOCKER/MAJOR, re-run tests, then commit → merge --no-ff →
push → deploy → restore held assets → regenerate baseline → repoint current.txt.

## Noted, not done here (one defect class per ship)

`safety_entity_extraction_test.py` still uses a hand-written test list in `main()`. On this
branch the new tests are registered by hand and the count is checked. The switch to
discovery lives on the parked item-1 branch and is worth landing on its own.
