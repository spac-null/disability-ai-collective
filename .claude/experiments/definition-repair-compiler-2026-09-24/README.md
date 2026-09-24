# Repairing one commitment without recompiling the definition around it

2026-09-24. Branch `repair/definition-local-edit-2026-09-24`. Zero authority, not wired,
flag off, nothing published.

## The question

The Definition Claim Support Shadow finds an unsupported factual commitment inside an
Architecture-authored definition. The repair primitive that acts on that finding succeeded
once and destroyed an article once. This asks whether a constrained local edit can remove
what the evidence does not license **and** keep what the reader needed the explanation to
teach them.

## Verified state before any work

| Thing | Handoff said | Verified |
|---|---|---|
| Production host | trident, Ubuntu | `trident`, Linux 6.17, reachable |
| Production workspace | — | `/srv/data/hermes/workspace/disability-ai-collective` (from `cripminds-daily.sh`) |
| Deployed runtime | `5e2ae3d` | HEAD is `b806008`; **runtime diff against `5e2ae3d` over `automation/` is empty** — `b806008` touches only `.claude/`. Handoff correct. |
| Compose mode | FAST_LANE | cron sets `CRIPMINDS_FAST_LANE_COMPOSE=1`; both comparison branches record `FAST_LANE` |
| Detector branch | `80554bd` | remote tip `80554bd`; **local branch is `ae98e91`, one commit ahead**. `ae98e91` changes `CLAIM_UNITS.md` only, so detector code identity is `80554bd` as stated. |
| Detector system SHA | `a374…0214` | matches in every frozen artifact |
| Frozen evidence, 5 sets | listed | all 5 present. `sha256sum -c` reports exactly one failure per set: `./SHA256SUMS.txt` listing **itself**. Every content file verifies. |

One trap avoided: `repair-counterfactual-bandgap-2026-09-23/branch/ARCHITECTURE.json` is
**not** the baseline — it was overwritten with the repaired architecture (identical sha to
`REPAIRED_ARCHITECTURE.json`). The real baseline is
`claim-shadow-batch2-2026-09-23/run2-20260923T212313Z/ARCHITECTURE.json`.

## Why the whole-definition rewrite failed

Not a wording miss. Read `REPAIR_INPUT_PROMPT.txt` line 655: the repair was injected as one
bullet under **THE EXACT VALIDATION FAILURES**, the generic Architecture self-repair channel,
whose reply schema asks for the *entire* architecture — `story_spine`, `beats`, `use_facts`,
`final_lens`, `definitions`, thirty-odd fields. So:

1. the edit surface was the whole architecture, not even the whole definition;
2. the definition was regenerated from nothing, as one field among thirty;
3. the two clauses are one grammatical construction —
   `set by the bandgap energy` sits inside
   `the long-wavelength edge …, set by the bandgap energy engineered in …` —
   and a model rewriting the construction rewrites both halves;
4. preservation existed **only as a sentence in a prompt**. It said "Preserve the explanatory
   purpose of the definition." Nothing checked it, so nothing enforced it.

The deleted clause had already been classified `NON_FACTUAL_OR_NOT_CHECKABLE` by the same
shadow — explicitly *not* the defect.

## The finding that decided the design

The detector's output **already contains the repair IR**. Its claims anchor into the gloss and
tile it. Measured over every frozen artifact, with no tuning:

| dataset | definitions | claims | exact + unique anchor | overlaps |
|---|---|---|---|---|
| calibration (A_run1, B_run3) | 4 | 16 | 16 | 0 |
| claim-shadow-batch2 | 5 | 24 | 24 | 0 |
| claim-shadow-batch3 | 3 | 14 | 14 | 0 |
| **total** | **12** | **54** | **54 (100%)** | **0** |

Coverage of each gloss by claim spans: mean 92.1%, median 93.9%, min 81.9%. The residue
between spans is punctuation and function words — `", "`, `" "`, `" — "`, `", with "`, `"."`.

The hard case partitions like this, with nothing invented:

```
U1 PROTECTED   NON_FACTUAL  [  0: 68] the long-wavelength edge of what the detector material will register
G1 glue                     [ 68: 70] ", "
U2 REPAIRABLE  NOT_ESTABL.  [ 70: 95] set by the bandgap energy
G2 glue                     [ 95: 96] " "
U3 PROTECTED   SUPPORTED    [ 96:147] engineered in the mercury cadmium telluride mixture
G3 glue                     [147:150] " — "
U4 PROTECTED   SUPPORTED    [150:186] for Roman, approximately 2.5 microns
G4 glue                     [186:193] ", with "
U5 PROTECTED   SUPPORTED    [193:235] the WFI sensitive from 0.48 to 2.3 microns
G5 glue                     [235:236] "."
```

`definition_claim_shadow.validate()` does **not** check that a commitment is a substring — it
only checks it is non-empty. So 54/54 is a good instrument, not a contract, and anchoring
failure refuses the repair rather than guessing an offset.

## Repair literature

Primary sources; inferences for Crip Minds marked as such.

| system | repair representation | preservation mechanism | take | reject |
|---|---|---|---|---|
| **RARR** (Gao et al., ACL 2023) | research (question gen → retrieval → **agreement gate**) strictly separated from revision; editor rewrites the whole claim/sentence and returns new text | **measured, not enforced.** `Pres` combines intent preservation with character-level Levenshtein similarity, harmonic-meaned with attribution. I checked the reference implementation (`utils/editor.py`): it returns `edited_claim` directly — **no Levenshtein threshold, no character cap, no length-ratio rejection**. The editor prompt teaches minimality by example, never by instruction. | the gate/edit split, and that the gate is a separate prior decision with a structured reason. Our detector already is that gate, and is already zero-authority. Per-claim gating so clean text is never sent to an editor. | preservation as a post-hoc score over free sentence regeneration. That is precisely what we did on bandgap, and precisely what failed. A metric you compute afterwards cannot stop a deletion. |
| **FactEditor** (Iso et al., ACL 2020) | explicit **Keep / Drop / Gen** action sequence over a buffer → stream, with facts in memory. Retention is an *action*, not an emergent property of decoding. | none formal. Actions come from a learned policy trained by supervised learning on action sequences derived from longest-common-subsequence alignment (WebEdit 233k, RotoEdit 37k). Retention is a prediction. *(Inference:* a predicted Keep can be a wrong Keep, so supported content can be dropped.*)* | **the representation.** Making retention an explicit inspectable decision rather than something that merely happens. Having DROP be chosen rather than "not generated". | word-level granularity and the learned policy. Our units are claim-spans that already carry an evidence status; word-level Keep/Drop would shred prose, and we have no 233k-example training set and no way to build one. |
| **VENCE** (Chen et al., AAAI 2023) | factual error correction as **iterative constrained editing** — Metropolis-Hastings sampling of insert/replace/delete actions at token positions | minimality as an **energy term**: LM fluency + truthfulness + **Hamming distance** to the original. Explicitly to stop "over-correction", i.e. generating substantially different text instead of fixing the error. | naming minimality a first-class constraint, and the diagnosis that the failure to prevent is *wholesale regeneration*, which is exactly our bandgap failure. | iterative sampling. §24 forbids retry loops and we take one call. Also a *soft penalty* can always be paid: a large enough truthfulness gain buys an arbitrarily large edit. And optimising edit distance as a score is forbidden by §19. |

**The gap all three leave.** Preservation is measured (RARR), learned (FactEditor), or
penalised (VENCE). None makes it a hard precondition that fails closed. Crip Minds can do
better than all three for one reason none of them has: **the detector already emits a
per-span status**. RARR must *find* what to edit; FactEditor must *learn* what to keep; VENCE
must *search*. We are handed the partition for free — so protection can be **verified**
rather than optimised.

## Representations compared

| option | preservation strength | prose quality | verdict |
|---|---|---|---|
| A — span edit script | strongest; deterministic application | glue around the edit needs handling | **chosen, with DROP as a first-class op** |
| B — model emits KEEP/DROP/GEN units | strong *if* the model emits every unit — but then **the model owns the partition and can silently omit a unit** | assembly can read awkwardly | rejected: it reintroduces the failure it is meant to fix, one level down |
| C — constrained rewrite + alignment map | weakest: preservation checked against *model-declared* provenance | best prose | rejected: §12 wants protection represented, not attested |
| D — derived | — | — | the chosen design is A with the partition computed by code from detector output, which is the part none of the papers do |

**The inversion.** The repair model does not decide what is protected. `build_ir()` computes
the partition deterministically from the detector's statuses. Protected text is then **copied
out of the original string** by `compile_repair()`:

```python
return _tidy(win["prefix"] + left_glue + mid + right_glue + win["suffix"])
```

`prefix` and `suffix` are slices of the original gloss. The model's answer only ever reaches
`mid`. There is no path by which it can delete protected text — a static test asserts this
holds even for a deliberately hostile reply that was *not* validated.

## The IR

```
gloss            the original string, verbatim, hashed
units[]          ordered, non-overlapping, GAP-FREE partition; every character in exactly one
  role          PROTECTED | REPAIRABLE | GLUE
  status        SUPPORTED | NON_FACTUAL_OR_NOT_CHECKABLE | NOT_ESTABLISHED | CONTRADICTED
  start,end     offsets into gloss
repairable_unit  exactly one, named by the caller when a gloss carries more than one
edit_window      [a,b) = left glue + repairable + right glue; prefix/suffix are gloss slices
```

Total coverage is by construction: glue is *defined* as the residue, so there is no part of
the original the compiler can lose track of. `build_ir` asserts
`"".join(u.text) == gloss` and refuses otherwise.

## Minimal glue, bounded

Glue repairs a **juncture**, not a meaning. A juncture needs punctuation, an article, a
preposition or a coordinator; it never needs a noun, verb, adjective, adverb or number. So
glue is a **closed whitelist**, ≤24 chars, no digits. Relativisers (`which`, `that`, `where`)
are deliberately excluded: they are the cheapest way to start a clause, and a clause is where
a new commitment hides. Anything outside the list fails closed — including words that would
be harmless here, because "harmless here" is the judgement the module exists to avoid making.

Generated `replacement` text is separately disciplined: length ≤ span + 24 chars; every
content word must trace to the **declared evidence or the gloss's own protected text** (never
the whole ledger); every digit string must appear in that evidence; and it may not re-contain
the unsupported span.

## Results

Three cases, **one model call each, no retries, no variants**. Positive control runs first and
without a provider, so a clean definition cannot cost a call.

| case | op | change | protected survived | explanatory survived | chars changed |
|---|---|---|---|---|---|
| **A cutoff wavelength** (hard) | DROP | `set by the bandgap energy` removed | 4/4 verbatim, in order | **1/1** | 25 / 236 (10.6%) |
| **B Dressing for Evacuation** (regression) | REPLACE | `were minutes away` → `were imminent` | 4/4 verbatim, in order | 1/1 | 12 / 288 (4.2%) |
| **C transfer-to-seat** (diagnostic) | REPLACE | `fixed seat` → `dedicated seat` | 5/5 verbatim, in order | n/a (none) | 3 / 188 (1.6%) |

The hard case, before and after:

> the long-wavelength edge of what the detector material will register, ~~set by the bandgap
> energy~~ engineered in the mercury cadmium telluride mixture — for Roman, approximately 2.5
> microns, with the WFI sensitive from 0.48 to 2.3 microns.

The explanation the free rewrite destroyed survives **byte for byte**, and the repair
generated no text at all.

The model chose DROP vs REPLACE correctly without any lexical special-casing, and said why:
on C, *"dropping would break the sentence after 'into a'"* — which is exactly right, because
the protected span ends on a dangling article. On B, *"DROP would leave the clause … without a
predicate, and the evidence supports only 'imminent'"*. It reached `imminent` — the word F46
licenses, and the same word the original successful free rewrite found.

**Positive control.** 6 clean definitions across three plans (`dark current`,
`sensor chip assembly (SCA)`, `plein air`, `East meets East`, `Utsuroi`, and the two clean ones
beside the flagged one) produced **zero** repair calls. Total across the experiment: 3 calls
for 3 flagged commitments.

## Claim Support re-check

The **unchanged** detector, not told a repair happened, re-run over the repaired plans:

| case | target commitment | still flagged in that definition | baseline supported content lost |
|---|---|---|---|
| A | gone | none | **none** |
| B | gone | `and to gather a limited selection of belongings` — the *second*, deliberately unrepaired warning | **none** |
| C | gone | none | **none** |

A first pass reported some baseline SUPPORTED spans "not reconfirmed". That was my metric
being wrong, not the repair: it compared exact strings across two independent segmentations.
The detector re-segments — `'the WFI sensitive from …'` came back as `'with the WFI sensitive
from …'`, and on C it merged `'…into a'` + `'fixed seat'` into one SUPPORTED claim
`'a guest moves out of their own wheelchair into a dedicated seat'`. Checking containment
instead of equality: **no supported content lost in any case.**

A clean re-check is necessary and not sufficient — the bandgap free rewrite was already clean
by this measure. That is why preservation is proven separately and mechanically.

## Paired downstream replay — and the finding that changes the verdict

One replay, frozen Research / Ledger / Worth, repaired Architecture, current contracts,
FAST_LANE, fresh namespace, nothing published. `replay-C-20260924T065921Z`.

The plan reached the Writer with the repaired gloss — `WRITER_PACKET.txt` line 99 carries it
verbatim, with no `bandgap` in it. The run HOLDs at SAFETY on
`MACHINE_LANGUAGE: provenance frames [('the source', 1)]`, the same unrelated defect that
stopped both comparison branches, so Grounding did not run in any of the three.

**The Writer put the bridge back.**

| branch | definition gloss | article: `bandgap → cutoff` bridge | article: explanation |
|---|---|---|---|
| A baseline | explanation + bridge | **present** | present |
| B free rewrite | circular, no explanation | **gone** | **gone** |
| C constrained repair | explanation, no bridge | **present** | present |

> **C, `WRITER_DRAFT.md`:** "The mixture is the design parameter. Varying the fraction of
> cadmium engineers a specific bandgap energy, **which sets the cutoff wavelength**, the
> long-wavelength edge of what the material will register."

It is in the Writer draft, so Continuity did not add it. And the controls are exact: **all
three branches have byte-identical `beats` and `use_facts`** — the free rewrite, though handed
the whole architecture, changed only the definition too. The gloss is the single variable
across A, B and C.

So the honest reading is uncomfortable and worth having:

1. **The repair did what it was contracted to do, provably.** The bridge is gone from the
   definition, the explanation survives byte for byte, the detector re-check is clean, and the
   architecture passes `validate_definition_support`.
2. **The definition was not the article's only route to the claim.** Beat B3's `happens` —
   never touched, identical in all three branches — reads: *"The fraction of cadmium in the
   mixture can be varied to engineer a specific bandgap energy; for Roman, with a desired
   cutoff wavelength of approximately 2.5 microns, it was tuned to 0.445."* That sentence is
   faithful to F86 and F87 and asserts no bridge, but it places bandgap and cutoff wavelength
   either side of a semicolon. The Writer, told to explain `cutoff wavelength` at first use in
   exactly that stretch of prose, closed the gap with `which sets`.
3. **B removed the bridge downstream only as collateral damage.** Killing the explanatory
   apposition removed the Writer's landing place for it. In the finished sentence the bridge
   and the explanation are one construction —
   `which sets the cutoff wavelength, the long-wavelength edge of what the material will
   register` — so the rewrite that destroyed the article is also the only branch that removed
   the defect. Preserving the explanation preserved the route back to the bridge.

That coupling is the actual discovery, and nothing short of running the paired replay with
identical beats would have shown it.

## Against the success criteria

| # | criterion | result |
|---|---|---|
| 1 | unsupported bridge absent | **in the definition yes; in the article NO** |
| 2 | useful explanation of `cutoff wavelength` survives | yes |
| 3 | protected explanatory content demonstrably preserved | yes — mechanically, 1/1 |
| 4 | supported factual content survives | yes — 3/3, verbatim |
| 5 | no new unsupported commitment | yes |
| 6 | **Writer does not recreate the bridge** | **NO — this is the failure** |
| 7 | article still explains the concept | yes |
| 8 | package does not recreate the bridge | yes — package is clean |
| 9 | no materially equivalent defect replaces it | yes — the *same* defect persists by another route |

Criterion 6 fails, so the hard case is not proven end to end.

## What the representation got wrong

Not preservation — that held, and held against a hostile reply. Not the edit boundary — only
permitted spans changed, 10.6% / 4.2% / 1.6% of each gloss. Not anchoring, not glue, not
evidence discipline, not the call budget.

**The IR's scope is one Architecture field. The commitment's licence in the finished article
is distributed across the gloss and the beat that supplies its context.** Repairing the gloss
changes what the plan *says* without changing what the plan *affords*. Nothing in the IR
represents the beat that keeps the two concepts adjacent with both facts allowed, so nothing
noticed that the repair left the inference reachable.

The next representation has to make the unit of repair the **commitment across the plan**, not
the span inside one field — while keeping this module's one real achievement, which is that
protected text is copied rather than regenerated and therefore cannot be lost. The detector
would have to see beats to find the second carrier, and §2 records exactly why it does not
yet: the evidence that would have justified reaching beats was a misreading of a truncated
proposition. That widening needs its own calibration, not an assumption.

## Stop rules

None of §24's stop conditions fired. Anchoring held 54/54; no protected content disappeared
without validator failure; the minutes-away regression still works; clean positive controls
triggered nothing; no retries were needed — 3 flagged commitments, 3 calls, 3 accepted first
answers; and no lexical special case for bandgap, minutes or fixed-seat exists anywhere in the
module. The prototype contract was written once and not revised.

## Decision

`LOCAL_EDIT_REPAIR_NEEDS_REDESIGN` — the mechanism is sound and proven at the level it
operates on; its scope is wrong for this defect.

---

# Phase 2 — repairing the commitment across the plan

The definition repair worked and the article did not change, because the definition was not
the only surface that could produce the claim. So the repair unit moves from *a span inside
one field* to *a commitment across the plan*, keeping everything from phase 1 that held:
exact anchoring, protected text copied rather than regenerated, one call, fail closed, zero
authority, detector untouched.

## The invariant, stated carefully

Not "the two concepts never co-occur in one field". That condition is satisfiable only by
deleting one of them — it would prevent regeneration by removing half the article, which is
what branch B did by accident and what made it a failure rather than a fix.

> **No single Writer instruction context may combine the INGREDIENTS with the RHETORICAL DUTY
> that makes the unsupported claim the natural completion.**

So surfaces are classified:

| class | meaning | must close? |
|---|---|---|
| `FULL` | both ends of the relation reachable **and** the first-use duty for the term | **yes** |
| `INGREDIENTS_ONLY` | both ends reachable, no duty | no — this is where legitimate material about the second concept may keep living |

That distinction is what makes `MOVE` a real option rather than a fig leaf.

**A fact in `facts_allowed` affords even when the prose never mentions it** — the Writer Packet
prints fact propositions under the beat, so removing only the prose leaves the route open. A
static test asserts that exact shortcut fails to close the route.

## Retroactive validation — the check predicts the failure we already paid for

Run backwards over the three frozen branches, anchored identically:

| branch | FULL affording surfaces | article outcome |
|---|---|---|
| A baseline | `definition:cutoff wavelength`, `beat:B3` | bridge present |
| B free rewrite | `beat:B3` | bridge absent (explanation destroyed) |
| **C constrained repair** | **`beat:B3`** | **bridge present — the failure** |

It flags B3 in C *before* the Writer is consulted. That is the point: it would have predicted
the phase-1 failure without paying for the replay.

Honest limit: B also shows `FULL` and B's Writer did not take the route — because that branch
had destroyed the apposition the bridge attaches to. **Affordance present does not mean the
claim will be written; affordance closed means the route is gone.** A conservative
over-approximation is the right shape: it can cost an unnecessary repair, it cannot miss the
carrier.

## Rarity selects the anchor; it is not the semantics

`set by the bandgap energy` yields candidates `{bandgap: df 1, energy: df 4}`. Unfiltered,
"energy" matches F09 — *dark energy* — in a beat about cosmology, a clear false positive.
Taking the rarest tier gives `{bandgap}` and the false positive disappears.

This is a **search heuristic for locating the concept in plan text**, not the truth condition.
Affordance is defined in terms of reach and duty and never in terms of rarity. `anchor_report()`
prints every candidate with its document frequency so the heuristic stays inspectable. If a
future relation joins two common concepts, this degrades to keeping several anchors and
repairing more conservatively — the safe direction — rather than to being wrong about what
affordance means.

## The slice, and the repair it produced

One call. `code=1a21093`, `system_sha256=f49c5638…`, `slice_sha256=dd142b26…`,
`edit_plan_sha256=484313ab…`, authority ZERO.

```
COMMITMENT  'set by the bandgap energy'  NOT_ESTABLISHED
  anchors   E1={cutoff, wavelength}   E2={bandgap}   (candidates: bandgap df1, energy df4)

AFFORDING (before)
  FULL  definition:cutoff wavelength   [gloss]
  FULL  beat:B3                        [happens, facts_allowed, FIRST_USE_SITE]

SLICE
  definition:cutoff wavelength
    PROTECTED U1  'the long-wavelength edge of what the detector material will register'
    REPAIR    U2  'set by the bandgap energy'
    PROTECTED U3  'engineered in the mercury cadmium telluride mixture'
    PROTECTED U4  'for Roman, approximately 2.5 microns'
    PROTECTED U5  'the WFI sensitive from 0.48 to 2.3 microns'
  beat:B3
    PROTECTED B3.C1  'The detectors are hybrids: …as a Sensor Chip Assembly.'
    AFFORDING B3.C2  'The fraction of cadmium … can be varied to engineer a specific bandgap energy;'
    PROTECTED B3.C3  'for Roman, with a desired cutoff wavelength … human eyes can see.'
    facts routing the second idea in: [F86]
```

The model chose, in one call and without being told the strategy:

* `DROP U2` — the bridge leaves the gloss; the explanatory clause survives byte for byte;
* `REPLACE B3.C2` → *"The precise mixture of HgCdTe, specifically the fraction of cadmium, can
  be varied;"* — keeping the cadmium-fraction antecedent that C3's *"it was tuned to 0.445"*
  needs, and dropping only the bandgap consequent;
* `MOVE F86 → B4`, the fabrication-and-screening beat.

Its own reason: *"the beat prose retains only the cadmium-fraction antecedent needed for the
cutoff sentence, while the bandgap fact is now offered in the fabrication beat, so no beat
holds both ideas together."*

That is the target shape — separation, not deletion.

## Static outcome

| line | result |
|---|---|
| `TARGET_COMMITMENT_REMOVED` | **True** |
| `AFFORDANCE_REMOVED` | **True** — affording surfaces after: none at all |
| `PROTECTED_CONTENT_PRESERVED` | **True** — U1,U3,U4,U5,B3.C1,B3.C3 verbatim; 0 lost; 0 orthographic adjustments; plan outside the slice byte-identical |
| `UNRELATED_FACT_PRESERVED_OR_EXPLICITLY_DROPPED` | **True** — F86 `OFFERED_IN_B4`, declared `MOVE`, explicit |
| `WRITER_REGENERATION` | pending the paired replay |

`use_facts` unchanged; only B3 and B4 differ from baseline; the engine's own
`validate_architecture`, `validate_definition_support` and `validate_evidence_hierarchy` all
return CLEAN.

## A residual this does not fix, and is not allowed to chase

B3's repaired prose says the cadmium fraction *"can be varied"* — a dispositional generality
whose licence was F86, which B3 no longer offers. B3's remaining F87 licenses only the
specific *"was tuned to 0.445"*. So the beat prose reaches very slightly past the beat's own
facts: the same defect class, one level down.

It is a reduction in claim strength rather than a regression, no current check covers it, and
covering it is exactly the relation-coverage work recorded as
`VERIFIED_STRUCTURAL_HOLE / NOT_VALIDATED_FOR_AUTHORITY` and explicitly out of scope. Recorded,
not pursued.

Also worth saying plainly: `MOVE` preserves a fact's **availability**, not its appearance. B4's
prose is about screening at GSFC and does not mention the recipe, so the Writer may simply not
use F86. If bandgap vanishes from the article that way, it vanished by editorial choice with
the material still on the table — which is different from having been deleted from the plan,
but is not the same as having been kept.
