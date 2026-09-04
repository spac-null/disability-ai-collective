# Safety audit — held-out real article 1

Machine audits on the Writer draft and the Continuity final, then a hand fact-lineage check
of every claim in the final against the frozen manifest.

## 1. Machine audits

| audit | writer draft | continuity final |
|---|---|---|
| hard factual-surface signals clean | **NO** — `unapproved_spatial: ['narrow']` | **YES** |
| unapproved entities | none | none |
| unapproved numbers | none | none |
| unapproved sensory | none | none |
| unapproved scene vocabulary | none | none |
| negative-admission audit | pass, 0 unmatched | pass, 0 unmatched |
| negative-shape sentences | 0 | 0 |
| intent / causal assertions | 0 | 0 |
| provenance-frame leaks | 0 | 0 |
| scaffold-name leaks | 0 | 0 |
| signpost openers | 0 | 0 |
| solo_ratio | 0.00 (telemetry only) | 0.00 (telemetry only) |
| CUT adherence | 0 violations | **0 violations — but see §3** |
| semantic delta draft → final | — | **no added surface, no added relation classes, validate CLEAN** |

The Continuity pass minted nothing: the semantic and relational delta between draft and final
is empty, and every edit it declared was a cut, a split, a reordering or a rewording.

## 2. Hand fact-lineage check

Every claim in the 771-word final was traced to the frozen manifest. Twenty of twenty-two used
facts trace cleanly. Two claims do not.

### 2.1 BLOCKER — a documented behaviour written as a documented event

**Passage, final paragraph 11, first sentence:**

> "The bike coasted past the housing complexes, and **it coasted through the block group with
> no published figure.**"

The first half is supported: `F14` reports that riding near NYCHA complexes, the device
released resistance.

The second half is not. The only fact about unmeasured block groups is `F19`:

> "Where a block group's sample is too small or unreliable, the ACS publishes no estimate, and
> both the device and the map render this as no reading rather than as zero."

That establishes what the device **does** when it meets a suppressed block group. No source
reports that any ride passed through one. The documented rides are Prospect Park West into
Windsor Terrace (`F11`) and past the NYCHA complexes (`F14`), and that is all.

So the article states, as a thing that happened, an event the evidence supports only as a
general property of the machine. It is a fabricated occurrence built entirely out of approved
nouns — which is why no detector saw it.

This claim is also load-bearing rather than incidental. It is the sentence that fuses the two
halves of the lens, and the paragraph's conclusion — *the instrument goes slack where the
pressure is least counted* — rests on it.

**Present in the Writer draft**, and preserved by Continuity. Continuity did not introduce it,
which is why the semantic delta is clean.

### 2.2 Second defect — a cut fact used in the prose

The article opens on a "3D-printed box". The only fact carrying the 3D printer is `F32`, which
the architecture declared **CUT** with reason `BREAKS_STORY_MOMENTUM`.

The claim is true and sourced — it is in the frozen manifest. It is not invented. But it was
declared cut and then used, which is a CUT-discipline failure rather than a factual one. Its
origin is upstream of the Writer: the architect wrote "A 3D-printed box" into
`opening_object_or_event`, so the packet handed the Writer a cut attribute in its opening
instruction.

Root cause of `F32` being cut at all: the fact bundles two unrelated things — that the
enclosure was 3D-printed, and that Blinder hopes others will download the specifications. Only
the second was unwanted. Cutting the whole fact was a ledger-granularity error made when the
manifest was frozen.

## 3. Why the audits passed

Both defects are invisible to the current screens, and each for a specific reason worth
recording.

**The fabricated event** introduces no new entity, number, date, place, sensory word or scene
term. `factual_surface_audit` looks for new *surface*; this claim adds none. It recombines
"the bike", "coasted", "the block group" and "no published figure" — all approved — into an
occurrence. Nothing in the current stack checks whether a stated event is in the ledger as an
event rather than as a disposition.

**The cut leakage** was missed by exact substring matching. The watch term derived from `F32`
was `printer`; the article says `printed`. `cut_adherence` reported `violations: []` and
`clean_prose: True`.

## 4. Verdict against the section 20 bar

| requirement | result |
|---|---|
| NO architect-minted facts | **FAIL** — `opening_object_or_event` carried a cut attribute; `B6`'s `concrete_carrier` described a physical instance ("the brake that therefore does not move") the ledger supports only as a disposition |
| NO editor-minted facts | PASS — semantic delta empty |
| NO fabricated scenes | **FAIL** — final ¶11: a ride through an unmeasured block group |
| NO fabricated visitor or perceiver | PASS — no rider other than the maker appears |
| NO unsupported causality | PASS |
| NO unsupported motive | PASS |
| NO CUT leakage | **FAIL** — "3D-printed" from cut `F32` |

Section 20 requires all seven before proceeding. Three fail. The article does not proceed to
Grounding or Fact Check, and no final article artifact is produced.
