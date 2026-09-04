# Held-out safety repair 2 — PASS

Repair 1 fixed the carrier and the article was still HELD, because the invention had moved
up one semantic level: into the declared turn. That is now checked, and the turn is repaired
from the same frozen evidence.

## 1. The failure

The declared turn read:

> "The easing over public housing and the unreadable block group are **re-read as the same
> fact**: the instrument can only pass on what the measure holds, so it is **quietest where
> the pressure is least counted**."

Every fact under it is true. The relation is not. The ledger keeps two cases apart:

| | |
|---|---|
| `F14` (OCCURRENCE) | near the NYCHA complexes the device released resistance — a **LOW** reading |
| `F19` (DISPOSITION) | where no estimate is published, device and map show "no reading **rather than as zero**" — an **ABSENT** reading |
| `F20` (DISPOSITION) | Blinder: showing it as flat ground "would be **a lie** told by the visualization rather than by the data" |

So the evidence does not merely fail to license `low == absent`. It refuses it, twice, in as
many words. This is why the Writer minted a sentence in the held-out run and minted another
in repair 1: the architecture kept asking for a joint the evidence will not make.

The same invented relation was in all three declarations of the lens — `crip_turn`,
`final_lens.lens_claim`, `final_lens.after_reading`.

## 2. Root cause

The ledger constrains facts. Repair 1 made it constrain carriers. Nothing constrained the
**relations** the turn asserts, so a turn could combine individually valid facts into an
equivalence, a comparison, a cause or a superlative that no fact carries — adding no new
noun, number, entity or occurrence, and passing every existing screen.

## 3. The validator

`validate_turn_support(turn, fact_ids, ledger)` in `story.py`. Two checks, both fail-closed.

**Relation licensing.** `turn_relations()` decomposes the turn into classes —
`EQUIVALENCE`, `COMPARISON`, `SUPERLATIVE`, `CAUSE`, `CONSEQUENCE`, `GENERALIZATION`,
`NEGATION`, `ABSENCE`, `TEMPORAL`. A class present in the turn and absent from every
licensing proposition is refused as `TURN_RELATION_NOT_SUPPORTED`.

Deliberately **not** `continuity.RELATION_SHAPES`, and deliberately not merged with it. That
list answers "did editing add a relation class"; this one answers "is this relation
licensed", and needs the two classes that list does not carry — equivalence and the
superlative — which are exactly the two the failing turn was built from. Widening the
continuity list to serve both would tighten a gate that is working.

**Absence given a magnitude.** The shape that produced the bug, checked at term level rather
than class level: a sentence that names an absent value (`no estimate`, `no figure`,
`unpublished`, `unreadable`, `uncounted`) and gives it a size (`zero`, `flat`, `low`,
`less`, `quiet`, `slack`, `eases`) is asserting that an unpublished figure is a small one.
A licensing fact that says "X **rather than** Y", "is not a Y", or "would be a lie" is
**refusing** the pairing, and refusal dominates: `TURN_ABSENCE_GIVEN_A_MAGNITUDE` names the
refusing facts. A turn that itself carries the refusal is restating the ledger, not minting,
and passes.

**Wired before the Writer.** Called from `validate_architecture()` behind the same optional
`ledger` argument as the carrier check, which runs before `build_packet()`. An unlicensed
turn never reaches the Writer to be "tried", because a Writer handed an unlicensed turn
writes it. All three declarations are checked, or the machine-side record goes on asserting
what the packet was stopped from saying.

**Stated limit.** The positive licence is coarse: it asks whether a relation class is
available in the licensing set, not whether the relation holds between these particular
terms. The one place it is term-level is the absence/magnitude pairing — the shape that
produced the bug. The precise general version is a semantic model; this is a gate.

## 4. Mutation tests

Both directions, in `story_architecture_test.py`:

| | |
|---|---|
| the exact held-out turn | REFUSED — equivalence, superlative, and the F19/F20 refusal all named |
| A fact + fact, turn says "the same" | REFUSED |
| B a fact that states the equivalence | ACCEPTED |
| C unpublished figure called low / zero / flat ground | REFUSED, three ways |
| D absence stated as an absence | ACCEPTED |
| E comparison, consequence, "therefore" with no licensing fact | REFUSED |
| E consequence licensed by a fact that carries one | ACCEPTED |
| restating the ledger's own "rather than" refusal | ACCEPTED |
| `interest`, `protest`, `honest`, `forest`, `request` | not read as superlatives |
| a published low value | not treated as an absent one |
| a ledger refusal against an otherwise-licensing fact | refusal wins |
| unlicensed turn at `validate_architecture` | REFUSED before `build_packet` |

The pre-repair architecture now fails validation on all three lens fields; the repaired one
passes. Full suite: 59 pass, 3 fail — `legacy_draft_promotion`, `opening_template_detector`,
`snapshot`, all three verified failing identically at the pre-repair-1 baseline `99df14c`.

## 5. The repaired turn

> Near the complexes the brake eased on a figure the survey had published and measured
> lower. Where the survey publishes no figure, the device shows no reading rather than a
> zero, and Blinder wrote that an absence of data is not an absence of pressure.

`final_lens.lens_claim` and `final_lens.after_reading` were rewritten to the same
distinction. Evidence, ledger, `use_facts`, `cut_evidence`, `beats`, `prohibitions` and the
Worth inputs are unchanged. The old turn is preserved verbatim in `_turn_repair_note`.

The distinction the ledger does hold: **a measured low value is not an absent one.**

## 6. Worth, re-derived

`STRONG_INTERPRETIVE_LENS` — re-asked, not inherited. The prior claim's second half is gone.
What remains still names a mechanism and still changes what the story means. The Crip Minds
warrant is narrower and now rests on what a measure structurally cannot hold about a life
(`F21`: not overcrowding, eviction risk, harassment, feelings of safety, or how long a
household has been holding on) and on who is absent from it by construction (`F22`), rather
than on a claim that the ride goes quiet where suffering is greatest. Narrower, and true.

## 7. The article

Architecture → Writer → Continuity, once. 699 words. Continuity merged two sentence pairs
and added nothing; the semantic delta is empty.

NEW FACTS 0 · NEW OCCURRENCES 0 · NEW RELATIONS 0 · CUT LEAKAGE 0 (10/10 cut facts watched)
· UNSUPPORTED NEGATIVES 0 · MACHINE LANGUAGE 0.

Manual recombination sweep: the only asserted occurrences are the three the ledger reports —
the Prospect Park ride (`F11`), the ride near the complexes (`F14`), and the installation and
removal of the devices (`F25`). No ride through an unpublished block group, in any wording.

Reader gate: all eight PASS.

## 8. Residual observations

1. **`lens_is_serialized` now reports `True`** (0.5 overlap on "Where the survey publishes no
   figure, the device and the map both show no reading rather than a zero"), against a
   declared `IMPLICIT` realization. This is a measurement artifact of having repaired the
   `lens_claim` into the ledger's own vocabulary — the matching sentence is the concrete
   disposition, not an abstract announcement. Reported, never required, never forbidden.
2. **`opening_object_or_event` still supplies "a wire running down to the brake arm"**, a
   physical particular the ledger does not hold. Carried over from the held-out run,
   unchanged, still unseen by any screen because architect prose enters the packet as
   approved material.
3. **The positive relational licence is coarse**, as stated in the code. "That figure was
   lower" is licensed at class level; the entailment from `F14` + `F15` + the score-to-
   resistance mechanism was supplied by hand, not proved by the gate.

## 9. Not reached

**Grounding and Fact Check: NOT REACHED**, unchanged. The composition layer is imported by no
production module. `AUTHORITATIVE_PIPELINE_BRIDGE_REQUIRED`, not built here.

Production unchanged. No OpenRouter spend.
