# Held-out safety repair 1 — HOLD

The interrupted session's diagnosis was right and its fix works. The article regenerated
from the repaired architecture is safe on every screen. It is still a HOLD, and the
blocker has moved one level up, to the lens itself.

## 1. The disposition → event bug

**Root cause.** `concrete_carrier` was unvalidated against the ledger. Beat `B6`'s carrier
read "a block group with no published figure, and the brake that therefore does not move".
Its `facts_allowed` were `F17 F19 F20 F21 F22`, all dispositional: the ledger says what the
device DOES when it meets an unpublished block group, never that a ride went through one. A
Writer obeying the packet wrote the instance, and every existing screen passed it, because
the invention adds no new noun, number, date or scene — only a new happening.

**Minimal fix.** `validate_carrier_occurrence()` in `story.py`. A carrier that has stopped
naming a thing and started asserting one (finite verb, consequence connective, or a
participle doing a verb's work) needs an allowed fact whose `claim_kind` is `OCCURRENCE`.
Undeclared kinds read as `DISPOSITION`. Explicitly conditional carriers are hypothetical
and pass on dispositions alone. Wired into `validate_architecture()` behind an optional
`ledger` argument, so every existing caller is unchanged.

**Stated limit, in the code.** It asks whether SOME occurrence is allowed at the beat, not
whether it is the one the carrier asserts. It catches the shape that produced this bug and
no more. It is confined to beats: `final_lens.crip_turn_carrier` can hold the same bug, but
its `evidence_basis` nearly always contains some occurrence, so the same test there would
pass whatever it was given.

**B6, final carrier:** `a block group with no published figure`.
`B2` and `final_lens.crip_turn_carrier` were reworded the same way. `facts_allowed`,
`use_facts`, `cut_evidence`, `lens_claim`, `evidence_basis`, Worth result and prohibitions
are byte-identical to the held-out run.

## 2. The CUT audit correction

**"3D-printed" was not a leak.** `F02` is a USED fact and reads "... in a 3D-printed
enclosure". The attribute in the opening is licensed by used evidence. The previous
report's "Second defect" section is wrong and is corrected in place.

**The watch-term bug was real and was upstream of the checker.** The held-out audit passed
`cut_adherence` a structure it did not expect, so the function iterated the wrong strings
and the reported "0 CUT violations" measured nothing. Watch terms have now been derived per
cut fact from the content unique to it — `F32`'s terms are `specifications`, `download`,
`other cities`, deliberately not `printer`, because the printer is also in used `F02` — and
frozen in `CUT_WATCH_TERMS.json`.

**Actual CUT leakage, measured correctly: 0.** 10 of 10 cut facts watched, 0 terms dropped
as too short, 0 violations, on both the previous final and the regenerated one.

**Morphology fix: kept.** Narrow, tested, additive, and useful on its own — a term written
`scan` against prose saying `scans` was invisible. It is a robustness fix, not the repair of
a known escape, and the code now says so. The pre-existing literal pass remains a raw
substring test, which over-reports rather than under-reports; left alone.

## 3. The regenerated article

Architecture → Writer → Continuity, once, from the same frozen evidence, ledger, Worth
result, lens and USE/CUT decisions. 678 words.

Safety, every class zero: disposition→event inventions 0, new occurrences 0, new facts 0,
new relations 0, actual CUT leakage 0, unsupported negatives 0, machine language 0.
Continuity's semantic delta is empty — no added surface, no added relation classes, no new
content words.

Continuity made one **removal**, and it is the finding. The draft's turn paragraph read:

> "Both of those conditions arrive at the legs as the same sensation: less pressure on the
> pedals."

`F19` says the device renders a missing estimate as **no reading rather than as zero**. It
does not say the brake goes slack there. So the sentence inferred a physical output the
ledger withholds — the same family as the B6 bug, produced again, at the turn. The
prescribed repair for an unsupported claim is removal, and removal is what was applied. A
rewrite was attempted first and `validate_semantic_delta` correctly refused it for adding
two NEGATION and one COMPARISON relation.

## 4. The remaining blocker: the lens contradicts its own ledger

The turn could not be rewritten into something supported, because the architecture's declared
turn is not supported.

> `crip_turn`: "... the instrument can only pass on what the measure holds, so it is
> **quietest where the pressure is least counted**."

"Quietest" means low resistance — flat ground. The ledger says the opposite twice:

- `F19`: the device and the map render an unpublished block group "as **no reading rather
  than as zero**" — explicitly not flat.
- `F20`: Blinder wrote that "showing it as flat ground would be **a lie** told by the
  visualization rather than by the data."

So the fusion the lens asks for — the easing over public housing and the unreadable block
group as one fact — is licensed for the *easing* half and refused for the *blank* half. This
is why the Writer minted a sentence in the held-out run and minted one again here: the
architecture asked for a joint the evidence will not make. The carrier validator caught the
symptom at the beat; the lens carries the same defect one level up, where nothing checks it.

The article is safe because the unsupported sentence was removed. It is a HOLD because with
that sentence gone the declared crip turn never lands, and it cannot land on this ledger.

## 5. Reader audit

| | |
|---|---|
| OPENING | PASS |
| READABILITY | PASS |
| ACCESSIBLE READING | PASS |
| MOMENTUM | HOLD |
| BREATHING | PASS |
| RESEARCH LOAD | PASS |
| CRIP MINDS FIT | HOLD |
| ENDING | HOLD |
| ENGINE-LANGUAGE LEAK | PASS (0) |

MOMENTUM: four consecutive paragraphs of limitation — the sample and its margins, the
unpublished block groups, what rent burden does not measure, and what the difficulty does not
translate to — with no scene, consequence or forward pull between them.

CRIP MINDS FIT and ENDING: with the turn removed the piece ends as a description of an
instrument and its limits. The loose brake cables, which the architecture wanted as the thing
the device turned up that the measure had no field for, arrive as an anecdote rather than a
payoff, because the re-read that would have earned them is gone.

## 6. Residual observations, recorded not acted on

1. **`opening_object_or_event` supplies a physical particular the ledger does not hold** —
   "a wire running down to the brake arm". `F03` gives a servo pulling a brake arm along the
   cable's axis; the wire is the architect's. No screen sees it, because architect prose
   enters the packet as approved material.
2. **`architect_prose_audit` reports `Near` as an unapproved entity** — sentence-initial
   false positive, pre-existing.
3. **`validate_final_lens` reports four missing fields** on this architecture — the frozen
   schema carries `crip_turn` and `crip_turn_rereads` at top level. Pre-existing, unchanged
   by this repair; confirmed identical at `99df14c`.

## 7. Not reached

**Grounding and Fact Check: NOT REACHED**, for the reason the held-out run already recorded
and which has not changed: the composition layer (`story.py`, `ledger.py`, `continuity.py`)
is imported by no production module, which is what makes its rollback a no-op. There is no
wired path from a finished article here to the authoritative Grounder or Fact Check.

**AUTHORITATIVE_PIPELINE_BRIDGE_REQUIRED.** Not built in this task.

Production unchanged. No OpenRouter spend: every stage in this run was performed in-session,
as in the held-out run.
