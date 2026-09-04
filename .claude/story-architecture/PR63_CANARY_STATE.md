# PR #63 — automated canary state

Where the autonomous composition path got to on the held-out Ground Truth subject,
and what each run established. Four runs, each one a real provider call.

## Stage progress across runs

| run | LEDGER | WORTH | ARCHITECTURE | what it established |
|---|---|---|---|---|
| 1 | HOLD | — | — | `502 unknown provider for model anthropic/claude-opus-4.8` — the brief's provider premise was false |
| 2 | HOLD | — | — | 2 WORLD negatives of 64 facts killed a verified ledger → reject the fact, not the run |
| 3 | PASS | HOLD | — | `NO_PLAUSIBLE_LENS` was a **truncation**, not a judgement; then Worth had defined the interpretive verdict out of existence |
| 4 | PASS | **PASS** | HOLD | carrier repair under-informed; then **OpenRouter credits exhausted (402)** |

Run 4 is the furthest: ledger and Worth both pass autonomously, with no human
touching an intermediate.

## Automated vs manual baseline, on what has run

| | manual baseline | automated run 4 |
|---|---|---|
| ledger facts | 36 | **64** |
| sources fetched | 8 (2 unfetched) | 4 (1 unfetched, 403) |
| span verification | by hand, per fact | machine-checked against source bytes, all |
| ledger repairs | — (built by hand) | 1 |
| Worth verdict | STRONG_INTERPRETIVE_LENS | **STRONG_INTERPRETIVE_LENS** |
| narrative yield | 11 / 11 | **11 / 11** |
| lens substance | what a published measure can and cannot hand to a body | the same insight, independently reached: what rent burden cannot register, and what the ACS suppresses |
| architecture | valid after **2** repairs | HOLD after **1** (the budget) |
| model calls to this point | not countable — human in the loop | 3 |

The Worth result is the significant one. The manual gate was a person who knew the
publication's standard; the automated gate reached the same verdict, the same yield
score, and the same underlying reading from the ledger alone.

## Open, and not code

**OpenRouter credits: $268.12 of $269 used, $0.88 left.** Run 4 died at the
architecture stage on `402 in_flight_budget_exhausted`. Nothing downstream of Worth has
executed on this subject, so Writer, Continuity, safety, Grounder, Fact Check and the
reader gate are **unproven end-to-end**.

CLIProxy is not an alternative: it holds no Claude auth (every native `claude-*` route
returns 401 expired, refresh token `invalid_refresh_token`).

## The repair budget is a real finding

The manual baseline needed **two** architecture repairs — REPAIR_1 for a carrier
asserting an occurrence, REPAIR_2 for a minted turn relation. The campaign budgets
**one**. Run 4 held on exactly the class REPAIR_1 fixed. The repair prompt has since
been given the detector's actual grammatical rule with examples pinned in both
directions by test, which may close it in one attempt — but if the budget is genuinely
one, the pipeline is being asked to do in a single attempt what the proven manual run
took two to do. That is a decision for the owner, not a bug to patch.

## Bar to note

Stage 27 asks the automated canary to reach **reader gate PASS**. The manual
baseline's own reader audit was **6 HOLDs of 10 dimensions** (NATURAL READING,
ACCESSIBILITY, BREATHING, MOMENTUM, WRITTENNESS, ORDER). The manual run never passed
its own reader gate, so that bar is higher than the ground truth met.

## Full suite

60 of 63 pass. The 3 failures — `legacy_draft_promotion_test.py`,
`opening_template_detector_test.py`, `snapshot_test.py` — fail identically on base
`6677e33` and are untouched, per the campaign's own instruction.
