# PR #106 rehearsal cohort — 2026-09-23

Three bounded production-like rehearsals run against PR #106 HEAD (`69c0bc5`) before merge.
This is the **baseline evidence set** for the prewrite contract as merged, and the first
current-contract examples of the defect class the next experiment targets.

Artifacts frozen read-only on trident:

    /srv/data/cripminds-evidence/pr106-rehearsal-cohort-2026-09-23/
      run1-20260923T193833Z/   run2-20260923T195207Z/   run3-20260923T195823Z/
      CANDIDATES.json  PROGRESS.txt  rehearsal_driver.py  DRIVER_DELTA.diff  SHA256SUMS.txt

`SHA256SUMS.txt` covers all 58 files. The tree is `chmod -R a-w`.

## Method

| | |
|---|---|
| Code | `69c0bc5` (PR #106 HEAD), isolated worktree; live workspace untouched at `2e96aa7` |
| Harness | `rehearsal_driver.py` — the committed `story_architecture_canary.py` plus ONE argument |
| Driver delta | `compose_mode=CP.scheduled_compose_mode()` — see `DRIVER_DELTA.diff` |
| Provider | real subscription adapter, `/usr/bin/claude -p --model claude-opus-5` |
| Mode | `CRIPMINDS_FAST_LANE_COMPOSE=1`, `CRIPMINDS_PREWRITE_STORY_SHADOW=1` |
| Candidates | ranks 1–3 of production's Priority-1 ranking, read **read-only**, frozen before any run |
| Publication | none. The canary has no publication bridge; `production_orchestrator.py` never ran. |

The canary hardcodes `COMPOSE_NORMAL`; production runs FAST_LANE. Without the one-argument
delta the rehearsal would not have exercised the FAST_LANE writing contract at all, which is
what PR #106's quotation patch changes. `scheduled_compose_mode()` is production's own
selector, so the delta makes the rehearsal more faithful, not less. Confirmed after the fact:
run 1's recorded `system_sha256` matches the branch's FAST_LANE system prompt exactly.

Seeds were read read-only because `get_news_seed_with_usable_source()` performs
`UPDATE news_seeds SET used = 1` — exercising the commissioning path would have consumed
real seeds and starved the next scheduled run.

## Outcomes

| | run 1 — RCA School | run 2 — HS2 station | run 3 — The Whale |
|---|---|---|---|
| Furthest stage | Grounding | Worth | Grounding |
| Architecture | PASS (2 calls, 1 repair) | NOT_RUN | PASS (2 calls, 1 repair) |
| `definition_evidence` | supplied naturally, 2 terms | — | supplied naturally, 2 terms |
| Lens | PASS, re-checks clean | — | PASS, re-checks clean |
| Shadow | OK · ZERO · 1 call · bound to `69c0bc5` | not reached | OK · ZERO · 1 call · bound to `69c0bc5` |
| Safety | PASS_WITH_MINOR_FINDINGS | — | PASS |
| Grounding | HOLD, 6 blocking | — | HOLD, 4 blocking |
| Fact Check / Reader | NOT_RUN | NOT_RUN | NOT_RUN |
| Calls / runtime | 12 / 725.9s | 2 / 281.7s | 13 / 893.3s |

No run passed the complete chain. Run 2 is a correct editorial rejection
(`GREAT_GENERAL_STORY_WRONG_PUBLICATION`) decided before Architecture.

**No patch produced a mechanical HOLD.** `DEFINITION_SUPPORT`, `LENS_EMBODIMENT` and
`QUOTE_CHANNEL` appear in no artifact or log in any of the three runs. Both architectures
re-check clean under the full current contract.

## Defect class A — `ARCHITECTURE_AUTHORED_UNSUPPORTED_SPECIFICITY`

**One confirmed current-contract instance: run 1.**

Architecture declared, with valid evidence ownership:

    definitions['Dressing for Evacuation']
      "A research project in which people were asked to put on what they would wear if told
       a large-scale evacuation were MINUTES AWAY, and to gather a limited selection of
       belongings; ..."

    definition_evidence['Dressing for Evacuation'] = [F46, F47, F48]
      F46  "...participants were asked to dress as if alerted to an IMMINENT large-scale
            evacuation, and responses were recorded in a photoshoot and accompanying survey."
      F47  "...culminated in life size photographic portraits shown at the Tentworks
            exhibition..."
      F48  "...focuses on the human emergency response of getting dressed and gathering a
            limited selection of possessions."

No fact in the run-1 ledger contains the word "minutes". `minutes` appears at exactly one
line of `WRITER_PACKET.txt` — line 64, the `EXPLAIN AT FIRST USE` block. The Writer
transcribed it, and three of six blocking Grounding findings are that phrase.

**The attribution was correct and the entailment was not.** All three cited facts are
genuinely about this project, all are in `use_facts`, none is CUT. PR #106's definition
contract checks numbers, entities and relation classes; "minutes away" carries no digit, no
capitalised token and no relation cue, and `validate_definition_support` states in its own
docstring that it is not a general entailment gate.

Cost of late detection, measured: the defect was fixed in the plan when Architecture emitted
that gloss. Everything after — **7 of 12 calls and 239s of 726s** — was spent discovering
something already decided.

## Defect class B — `PACKAGE_AUTHORED_UNSUPPORTED_SPECIFICITY`

**Run 3. This is NOT a prewrite/compiler defect and must not be counted as one.**

Architecture was clean. `crip_turn` reads "communication, cooperation, caregiving", and F18's
verbatim span licenses exactly that:

    F18  "A massive suspended whale sculpture will introduce guests to the creatures' size,
          sounds and behavior, with a focus on their social nature and similarities to
          humans—INCLUDING COMMUNICATION, COOPERATION AND CAREGIVING."

The article sentence carrying it was not flagged. The three TRUE_UNSUPPORTED findings live in
**editorial package fields**:

    DEK          "Its ENTRANCE GALLERY introduces whales through 'communication, ...'"
    EXCERPT      "A massive whale sculpture will hang suspended AT THE ENTRANCE, ..."
    SOCIAL_HOOK  "The Whale's ENTRANCE GALLERY will introduce cetaceans by ..."

No run-3 fact contains "entrance". The galleries in evidence are named — Soundscape,
Horizons, the anatomy and food-web rooms — and none is an "entrance gallery". The only
article-body finding is TRUE_UNCERTAIN, not TRUE_UNSUPPORTED.

`editorial_package()` receives `story_spine`, the Worth lens claim and the finished article.
It does not receive the Ledger. So a post-prose stage invented factual specificity about
material it can see but cannot check. That is a second, independent invention boundary and
needs its own investigation — plausibly whether package fields must be constrained to
article-supported wording, or checked against the same evidence surface the article is.

## Correction recorded deliberately

An earlier reading of this cohort reported run 3 as a **second** instance of class A, on the
basis that `crip_turn` had invented "cooperation, caregiving" and that a relation-checked
field had therefore failed. **That was wrong.** F18 was read from a 160-character truncated
display that cut off before "including communication, cooperation and caregiving". The full
proposition licenses the triad.

The conclusion drawn from the error — that the claim-support shadow should broaden beyond
definitions to `crip_turn` and the lens fields — lost its evidence when the error was found,
and the scope stays definitions-only.

**Standing rule for diagnostics: inspect full propositions and support spans, never truncated
display text.** A truncated proposition produced a confident, specific, wrong attribution —
the same failure mode the claim-support shadow exists to detect, committed by the diagnostic
rather than by the engine.

## Relation observation (descriptive, not `validate_turn_support`)

Across both architectures, zero unsupported relation-bearing commitments in `story_spine`,
beat `happens` or `ending_move` reached prose. Run 1's one candidate — a silence-as-absence
inference in B5 — never reached the article. Run 3's single cue sat in a descriptive beat
fully covered by its ten facts.

This is consistent with the separate 114-run relation audit
(`VERIFIED_STRUCTURAL_HOLE / NOT_VALIDATED_FOR_AUTHORITY`, recorded on PR #106): the
representation gap is real, and relation classes are the wrong unit for closing it.

## What this cohort establishes

1. PR #106's contracts are satisfiable by naturally generated Architecture — 2/2, under real
   FAST_LANE, with no mechanical HOLD. Given that 100% of 114 retained architectures declare
   definitions, this was the merge's largest risk.
2. Evidence ownership does not guarantee entailment. One confirmed instance.
3. A post-prose stage can independently invent specificity. One confirmed instance.
4. Sample is thin: three runs, two architectures, four definitions, one instance of each
   defect class. Calibration of any detector needs more natural runs than this.
