> **SUPERSEDED — PRE-FREEZE DRAFT, RETAINED FOR PROVENANCE.**
> This draft was found internally inconsistent before it became authoritative: it kept GR2-02
> UNSUPPORTED while leaving the structurally identical FORM-1.3 claim "not because the review
> ranks them or gathers them into a group" as INTERPRETATION. The authoritative version is
> **GOLD-V2.1-OWNER-CALIBRATION-AND-CONSISTENCY-CORRECTION.md** (95 / 44 / 41 / 2 / 8).
> Nothing below has been edited — the tension it records in §9.2 is exactly what V2.1 fixes.

---

# GOLD-V2 / OWNER-CALIBRATION-AMENDMENT

**Date:** 2026-08-19
**Authority:** Jascha (owner decision)
**Derived from:** GOLD V1 — `../writer-grounding-v2-2026-08-19/inputs/gold-ledger-FROZEN.json`
**Gold V1 status:** UNCHANGED AND STILL FROZEN. Not edited, not rewritten, byte-identical,
hash-verified against that experiment's `SHA256SUMS.txt`.
**Model calls made for this amendment:** NONE. No re-run, no re-audit, no new sampling.

---

## 1. WHY THIS AMENDMENT EXISTS

WG-2 closed with DECISION D — VERDICT_BOUNDARY_STILL_UNSOLVED and one open question recorded
for the owner: the five residual disagreements were not spread across classes. Two independent
detector configurations, under two different prompts, classified all five identically as
INTERPRETATION. That stability suggested the residue might be partly a **gold-calibration**
question rather than purely a detector defect.

The owner has now resolved it — and the resolution is that the five were **not one family**.
Three were gold-calibration errors. Two are genuine detector misses.

---

## 2. THE EDITORIAL PRINCIPLE (owner decision)

CripMinds may make new analytical, evaluative and comparative meaning from source-grounded
material. The source does **not** need to state the article's interpretation verbatim.

Interpretation may **not** manufacture:

- concrete world-state facts;
- visitor / reader / person knowledge, preparation or intention states;
- factual claims about what the source or reviewer says, ranks, intends, omits, centres or
  believes;

unless the commissioned evidence supports them.

> **INTERPRETATION MAY CREATE NEW MEANING FROM GROUNDED FACTS.**
> **INTERPRETATION MAY NOT CREATE NEW FACTS ABOUT THE WORLD, PEOPLE, OR THE SOURCE.**

---

## 3. CHANGED VERDICTS — THREE ITEMS

Only these three adjudications changed. No proposition was added, removed, or re-worded. The
original V1 findings are preserved verbatim in `gold-ledger-V2.json` under
`reclassified_to_interpretation_v2`.

### G13-03 — UNSUPPORTED → INTERPRETATION
> "It is a two-sided obligation, and the second side is the one that presses."

**Reason:** an evaluative comparison made by the article from source-grounded material. The
source establishes the two directions of the duty; the article weighs them. No new concrete
world-state fact is introduced.

### GR2-03 — UNSUPPORTED → INTERPRETATION
> "It is stated as an obligation running two ways at once, and the second direction is the
> harder one."

**Reason:** same construction, same grounding, same reason as G13-03.

### GR3-02 — UNSUPPORTED → INTERPRETATION
> "And that second obligation is harder to discharge, because the subject is not in the room to
> say whether it has been met."

**Reason:** the underlying absence/death is source-grounded (both artists died before their work
was shown). The comparative and causal weight placed on it is article analysis, not a new fact.

**Class effect:** `INTERPRETATION_AS_FACT` was exactly these three findings. Under Gold V2 that
class is **empty** — it was a calibration artifact, not a defect class.

---

## 4. KEPT AS UNSUPPORTED — TWO ITEMS

### GR2-01 — REMAINS UNSUPPORTED
> "without the visitor having brought anything to the encounter except the willingness to walk in"

**Reason:** asserts an ungrounded visitor preparation/knowledge state. The source supports only
unfamiliarity ("some subcultural genius or longlost creative you've never heard of"). Not having
heard of an artist is not "having brought nothing to the encounter". This is a claim about a
person's internal state, not an evaluation of grounded material.

### GR2-02 — REMAINS UNSUPPORTED
> "taken here not because the review places them above the rest but simply because they can be
> set beside each other"

**Reason:** asserts a factual proposition about what the review *does or does not rank*. That is
a claim about source behaviour and provenance, not free article analysis, and it requires source
support. The source arguably contradicts it ("it's all eclipsed by his weird little paintings").

**Explicitly not a reason to reclassify it:** that it expresses the writer's own selection
rationale. The selection rationale is the article's to state; the negative assertion about the
review's ranking is not.

---

## 5. GOLD V2 TOTALS — VERIFIED ARITHMETIC

Totals are **derived** from the per-article records, not typed.

| | GOLD V1 | GOLD V2 |
|---|---|---|
| TOTAL PROPOSITIONS | 95 | **95** |
| SUPPORTED | 44 | **44** |
| INTERPRETATION | 39 | **42** |
| UNCERTAIN | 2 | **2** |
| UNSUPPORTED | 10 | **7** |

Sum check: 44 + 42 + 2 + 7 = **95** ✓

Per article (each article's total is unchanged):

| Article | SUP | INT | UNC | UNSUP | total |
|---|---|---|---|---|---|
| FORM-1.3 | 19 | 18 | 0 | 2 | 39 ✓ |
| FORM-1.3-R2 | 13 | 10 | 2 | 3 | 28 ✓ |
| FORM-1.3-R3 | 12 | 14 | 0 | 2 | 28 ✓ |

**Gold V2 UNSUPPORTED set (7):** G13-01, G13-02, GR2-01, GR2-02, GR2-04, GR3-01, GR3-03

By class: INVENTED_VISITOR_STATE / TEMPORAL_SPECIFICITY 2 · INVENTED_VISITOR_STATE 1 ·
INVENTED_PROPER_NOUN 1 · INVENTED_TEMPORAL_SPECIFICITY 1 · QUALIFIER_DROPPED 1 ·
FORM_INSTRUCTION_AS_PROSE_CLAIM 1 — total 7 ✓
By origin: WRITER 6 · FORM 1 — total 7 ✓

---

## 6. WG-2A RESCORED AGAINST GOLD V2 — NO NEW MODEL CALL

The frozen WG-2A output was reused unchanged (176 propositions;
SUPPORTED 114 · INTERPRETATION 56 · UNSUPPORTED 5 · UNCERTAIN 1). It was **not** re-run.

WG-2A's five UNSUPPORTED flags, matched to gold by exact-span containment:

| WG-2A | span | Gold |
|---|---|---|
| FORM-1.3 / P51 | "the gallery at City Art Centre" | G13-01 |
| FORM-1.3 / P53 | "…did not know the work existed an hour ago" | G13-02 |
| R2 / P60 | "…stayed unpublished and unseen in his lifetime" | GR2-04 |
| R3 / P12 | "an hour earlier" | GR3-01 |
| R3 / P43 | "walking around Edinburgh in August" | GR3-03 |

```
TP = 5
FN = 2
FP = 0

UNSUPPORTED RECALL    = 5 / 7 = 71.4%
UNSUPPORTED PRECISION = 5 / 5 = 100%
```

**Remaining false negatives — exactly two:**

- **GR2-01** — unsupported visitor preparation/knowledge state
- **GR2-02** — unsupported factual claim about what the review ranks

**The three reclassified items are now scored correct.** WG-2A had verdicted all three
INTERPRETATION (P30, P35, P32), which is what Gold V2 now says. They generate no new false
positives, which is why precision stays at 100%.

Under Gold V1 this same output scored TP 5 / FN 5 / FP 0 — recall 50%. The improvement to 71.4%
comes entirely from correcting the gold, not from any change to the detector.

---

## 7. THE GROUNDING BOUNDARY — WORKING PRINCIPLE

**SUPPORTED** — proposition directly licensed by the commissioned evidence.

**INTERPRETATION** — article analysis, synthesis, metaphor, comparison, or causal/evaluative
reading operating on source-grounded material, without introducing a new concrete factual state.

**UNSUPPORTED** — proposition that introduces factual content not licensed by the evidence,
including unsupported:

- names
- times, dates, durations
- human knowledge / preparation / intention states
- institutional positions or intentions
- claims about what the source or reviewer says, ranks, means or omits
- absolute claims created by qualifier loss
- other concrete world-state additions

**Interpretation does NOT require a visible hedge token.** Do not force "on this reading",
"perhaps", or "it seems" merely to make analysis legal. Natural CripMinds interpretation must
remain possible. This is not a style preference — WG-2B measured it: requiring a visible
interpretation marker recovered exactly four gold findings and falsely converted exactly four
legitimate interpretations. Net discrimination **zero**.

---

## 8. THE REAL DETECTOR GAP AFTER GOLD V2

The remaining problem is no longer "comparative interpretation". It is two narrower classes:

- **A. HUMAN / VISITOR STATE INVENTION** (GR2-01)
- **B. META-SOURCE FACTUAL CLAIM** (GR2-02)

### Can they be detected narrowly without damaging legitimate interpretation?

**Measurement caveat, stated plainly:** Gold V1/V2 itemise only the 12 findings with exact spans;
the other 83 propositions are recorded as counts, not text. So the surface-syntax inspection was
run over the **176 enumerated WG-2A propositions** for the same three articles — the only
itemised proposition set that exists — not over an itemised 95.

Surface-syntax triggers, measured:

| Candidate trigger | props matched | of which legitimate (SUPPORTED/INTERPRETATION) | gold UNSUPPORTED caught |
|---|---|---|---|
| Class A vocabulary (visitor/viewer/knew/unfamiliar/prepared/expects…) | 31 | 30 | 1 |
| Class B subject (the review / the source / the reviewer…) | 65 | 64 | 0 |
| Class B + negation | 8 | 8 | 0 |

**Conclusion: neither class is separable by surface syntax.** A class-A vocabulary rule would fire
on 31 propositions to catch 1, and a class-B subject rule on 65 to catch 0 — the target GR2-02 is
not even in the negation subset as enumerated. These are noise ratios of 30:1 and 64:1. This is
the same failure mode WG-2B already demonstrated with R4_QUALIFIER_DROPPED (1 real, ~25 spurious).

**Any WG-3 rule written at the level of vocabulary or markers is already refuted.** The
distinction has to be semantic and about the object of the claim.

---

## 9. TWO OPEN TENSIONS FOUND WHILE RESCORING

Neither was acted on. Both are recorded for the owner.

### 9.1 The GR2-01 miss happens at ENUMERATION, not at the verdict

WG-2A enumerated GR2-01's span

> EXACT_SPAN: "…without the visitor having brought anything to the encounter except the
> willingness to walk in"

as the proposition

> PROPOSITION: "The festival experience consists of successive unprepared encounters with
> unfamiliar names."

The assertive content — *the visitor brought nothing but willingness* — was dissolved into the
adjective "unprepared" **before any verdict was formed**. The verdict stage then correctly judged
the weakened proposition to be interpretation. The stage that lost the claim is enumeration.

This matters for WG-3 scope: sharpening only the verdict prompt cannot recover GR2-01, because by
the time the verdict runs, the invented state is no longer in the text being judged.

### 9.2 The same class-B construction appears in FORM-1.3 and is NOT a gold finding

FORM-1.3 contains

> "not because the review ranks them or gathers them into a group"

which is the same negative meta-source claim as GR2-02's "not because the review places them
above the rest". WG-2A enumerated it as P15 and verdicted it INTERPRETATION — with the reasoning
"The review does not rank the two artists or place them in a group".

Gold V1 itemises GR2-02 (in R2) as UNSUPPORTED but does not itemise the FORM-1.3 equivalent.
Under the owner principle just adopted, both should carry the same verdict.

**Not acted on.** Only the five nominated items were re-adjudicated, and the instruction was not
to rewrite the historical gold. Resolving this would change the Gold V2 totals, so it is left as
an explicit owner question for a possible GOLD V2.1. The figures in §5 and §6 stand as issued.

---

## 10. PROPOSED WG-3 — DESIGN ONLY, NOT RUN

**Question WG-3 must answer:**

> Can the semantic verdict stage distinguish **article analysis of grounded material** from an
> **unsupported factual assertion about a person's state or about the source itself** — without
> suppressing legitimate interpretation?

**The candidate distinction is the OBJECT OF THE CLAIM, not its form.**

- If the article is evaluating, comparing, or synthesising grounded subject matter →
  INTERPRETATION may be valid, with or without a hedge.
- If the proposition asserts a concrete fact about **a human internal state** (knowledge,
  preparation, intention, expectation) or about **what the source itself does, says, ranks,
  centres or omits** → it needs direct evidence, and absent that evidence it is UNSUPPORTED
  regardless of how interpretive its surrounding sentence is.

**Explicitly ruled out, with the evidence that ruled them out:**

- Broad comparative or causal marker rules — disproven by WG-2B
  (R5_UNMARKED_COMPARATIVE_CAUSAL: 4 gold, 4 false; and the whole comparative family is now
  gold-INTERPRETATION under Gold V2, so the rule would be net-harmful).
- A generic "visible interpretation marker" requirement — net discrimination zero.
- Surface vocabulary or subject-noun rules for classes A and B — 30:1 and 64:1 noise, §8.
- Union with the narrow deterministic rules — WG-2 already showed it is strictly dominated by
  WG-2A alone (zero added recall, six added false positives).

**WG-3 must also test the enumeration stage, not only the verdict stage** (§9.1). A verdict-only
experiment cannot recover GR2-01 and would report a ceiling that is an artifact of enumeration
loss. Suggested split:

- **WG-3A — enumeration fidelity.** Does the enumerated proposition preserve every assertive
  component of its EXACT_SPAN? Scored against the span, blind to gold.
- **WG-3B — object-of-claim verdict.** With fidelity assured, can the verdict stage apply the §7
  boundary to classes A and B?

**Success gate — unchanged and not softened:** UNSUPPORTED recall 100% at ≤ 2 false positives.
Gold V2 raises the WG-2A baseline to 71.4% / 100%; the gate is still unmet.

---

## 11. WHAT THIS AMENDMENT DID NOT TOUCH

- Gold V1 — unchanged, still frozen, hash-verified
- WG-2A / WG-2B outputs — unchanged, not re-run
- Article Form — untouched
- Repair (WG-0B) — untouched
- Production — untouched, nothing wired, nothing deployed
- Real Article Test 2 — not started
- `.claude/WORK.md` / `.claude/LOGBOOK.md` — not modified by this amendment; the §7 boundary is
  not yet promoted into the canonical docs. Owner's call whether it should be.
