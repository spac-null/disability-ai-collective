# GOLD V2.1 — OWNER CALIBRATION + CONSISTENCY CORRECTION

**AUTHORITATIVE. FROZEN 2026-08-19.**

**Supersedes:** `GOLD-V2-OWNER-CALIBRATION-AMENDMENT.md` + `gold-ledger-V2.json` — retained
unedited in this directory as a **pre-freeze calibration draft, for provenance only**.
**Gold V1** — `../writer-grounding-v2-2026-08-19/inputs/gold-ledger-FROZEN.json` — unchanged,
byte-identical, still separately frozen.
**Model calls made for V2 or V2.1:** NONE. WG-2A/WG-2B outputs reused frozen, never re-run.

---

## 1. WHY V2.1 EXISTS

The Gold V2 draft was internally inconsistent and was caught before it became authoritative.

V2 accepted the owner principle that a factual claim about **what the review does or does not
rank** requires source support, and kept **GR2-02** UNSUPPORTED on exactly that ground. But
FORM-1.3 contains the same construction —

> "not because the review ranks them or gathers them into a group"

— and it was sitting in the unitemised INTERPRETATION mass. Two structurally identical
propositions carried two different verdicts. V2.1 fixes that, and then sweeps for any other
instance before freezing.

---

## 2. THE CORRECTION — G13-04

**FORM-1.3 · INTERPRETATION → UNSUPPORTED · new ID `G13-04`**

> "not because the review ranks them or gathers them into a group"

**Class:** `FORM_INSTRUCTION_AS_PROSE_CLAIM` · **Origin:** FORM
(matching GR2-02 — the same Form no-centrality boundary surfacing as a prose assertion)

**Reason.** It asserts a factual proposition about what the review does *not* do. A claim about
source behaviour requires source support. The source arguably contradicts it: the review does
rank and evaluate — *"that of Sandra George… is worth telling"*, *"it deserves to be seen far
outside the city's confines"*, *"it's all eclipsed by his weird little paintings"*. Under the
principle already accepted in V2, structurally equivalent propositions must receive structurally
equivalent verdicts.

**This is recorded as a change, not a silent rewrite.** The V2 draft stands unedited alongside
this file; `gold-ledger-V2.1-FROZEN.json` carries `consistency_correction_v2_1` naming the change,
its pairing with GR2-02, and the finding's prior verdict.

**Detector note.** WG-2A verdicted this proposition (FORM-1.3/P15) INTERPRETATION with the
reasoning that the negative observation "the source text bears out" — while returning an **empty**
`SOURCE_ANCHOR_RETURNED`. It asserted source support and cited nothing. GR2-02 (R2/P12) did the
same. Both class-B misses returned no anchor. See §7.

---

## 3. CONSISTENCY SWEEP — NARROW, PRE-FREEZE

**Scope.** INTERPRETATION-classified propositions asserting either
**(A)** human/visitor knowledge, preparation, intention or mental state, or
**(B)** what the source/review says, ranks, omits, centres, intends, believes or does not do.
Ordinary metaphor, synthesis, evaluation and comparison were **not** reopened. The gold set was
**not** re-adjudicated as a whole.

**Method caveat, stated plainly.** Gold V1/V2/V2.1 itemise only the findings with exact spans;
the SUPPORTED/INTERPRETATION mass is recorded as counts, not text. The sweep therefore ran over
the three frozen articles against the frozen source, cross-indexed to the 176 itemised WG-2A
propositions — the only itemised proposition set that exists.

**Result: 22 candidates inspected (7 class A, 15 class B). 1 change. 1 flagged, not changed.**
Full record with per-item reasoning: `CONSISTENCY-SWEEP-V2.1.json`.

### Class A — 7 inspected, 0 changed

Every one restates the source's own *unfamiliarity* ("some subcultural genius or longlost creative
you've never heard of") and stops there: *"previously unknown to them"*, *"no way of anticipating"*,
*"someone who did not know it existed"*, *"a story becoming known to someone who did not know it"*,
*"the visitor navigates by appetite"*, *"a name that arrives without preparation"*, *"a word that
puts the visitor at the moment of revelation"*.

**The line that separates them from GR2-01:** unfamiliarity is *entailed* by the source. GR2-01
does not assert unfamiliarity — it asserts what the visitor **brought** ("having brought anything
to the encounter except the willingness to walk in"). That is a preparation state, and nothing in
the source establishes it.

### Class B — 15 inspected, 1 changed

Changed: **B1 → G13-04** (§2).

Not changed, and worth naming because they show the correction is narrow:

- **"The number is the review's, and it sits there without commentary"** (R3) — the *same shape*
  as G13-04/GR2-02: a negative claim about source omission. **It stands**, because it is borne out:
  the source states "thousands of paintings and drawings he amassed over his lifetime" and adds no
  remark on the quantity. Class-B claims need evidence; this one has it.
- **"Two of those names are worth setting down with their facts attached"** (R3) — the article
  selects, without asserting anything about the review. R3 is the clean variant of the construction
  that fails in FORM-1.3 and R2. The defect is the meta-claim, not the act of selecting.
- Verifiable claims about the source's own text — *"the word the review keeps reaching for"*,
  *"the verbs belong to the visitor"*, *"the review opens"*, *"used more than once"*,
  *"the reviewer's own position"* — all check out against the source.
- Readings of grounded material — *"the line is a joke"*, *"less a strategy than an admission"*,
  *"the word does real work in the piece"* — evaluation, no new fact.

**The rule this establishes: a negative or characterising claim about the source is not banned.
It is evidence-bearing.** It must be checkable against the commissioned evidence, and it must
survive the check.

### Flagged for owner, deliberately not changed

**B8 — R2: "Midway through the review comes a demand."** The duty passage is the 13th of 19
source paragraphs (~68%), not the midpoint. Left unchanged because "midway" is a loose narrative
connective with no fixed threshold, not an assertion about the review's stance, ranking or
omission — and WG-2A independently landed on UNCERTAIN for this same span, not UNSUPPORTED.
It is the one genuinely arguable residual. Changing it would move the frozen V2.1 totals, so it
is surfaced rather than absorbed.

### Out of scope

Two propositions are already UNCERTAIN in Gold V1 — *"the festival's characteristic verb"* and
*"What it does not describe, and cannot"*. The sweep covers INTERPRETATION only. Both left as-is.

---

## 4. GOLD V2.1 TOTALS — VERIFIED, DERIVED NOT TYPED

| | V1 | V2 draft | **V2.1 FROZEN** |
|---|---|---|---|
| TOTAL PROPOSITIONS | 95 | 95 | **95** |
| SUPPORTED | 44 | 44 | **44** |
| INTERPRETATION | 39 | 42 | **41** |
| UNCERTAIN | 2 | 2 | **2** |
| UNSUPPORTED | 10 | 7 | **8** |

Sum: 44 + 41 + 2 + 8 = **95** ✓

| Article | SUP | INT | UNC | UNSUP | total |
|---|---|---|---|---|---|
| FORM-1.3 | 19 | 17 | 0 | 3 | 39 ✓ |
| FORM-1.3-R2 | 13 | 10 | 2 | 3 | 28 ✓ |
| FORM-1.3-R3 | 12 | 14 | 0 | 2 | 28 ✓ |

**UNSUPPORTED set (8):** G13-01, G13-02, **G13-04**, GR2-01, GR2-02, GR2-04, GR3-01, GR3-03
**By class:** INVENTED_VISITOR_STATE/TEMPORAL_SPECIFICITY 2 · INVENTED_VISITOR_STATE 1 ·
FORM_INSTRUCTION_AS_PROSE_CLAIM 2 · INVENTED_PROPER_NOUN 1 · INVENTED_TEMPORAL_SPECIFICITY 1 ·
QUALIFIER_DROPPED 1 — total 8 ✓
**By origin:** WRITER 6 · FORM 2 — total 8 ✓

Net change from V1: three UNSUPPORTED → INTERPRETATION (owner calibration: G13-03, GR2-03,
GR3-02) and one INTERPRETATION → UNSUPPORTED (consistency: G13-04). No proposition added,
removed or re-worded. `INTERPRETATION_AS_FACT` is now an empty class.

---

## 5. WG-2A RESCORED AGAINST V2.1 — NO NEW MODEL CALL

Frozen WG-2A output reused unchanged (176 propositions; 114 SUPPORTED · 56 INTERPRETATION ·
5 UNSUPPORTED · 1 UNCERTAIN).

```
TP = 5      FP = 0      FN = 3

UNSUPPORTED RECALL    = 5 / 8 = 62.5%
UNSUPPORTED PRECISION = 5 / 5 = 100%
```

True positives: P51→G13-01 · P53→G13-02 · P60→GR2-04 · P12(R3)→GR3-01 · P43(R3)→GR3-03

**The three false negatives:**

| Gold | span | class | WG-2A | anchor returned |
|---|---|---|---|---|
| **G13-04** | "not because the review ranks them or gathers them into a group" | FORM_INSTRUCTION_AS_PROSE_CLAIM | INTERPRETATION | **EMPTY** |
| **GR2-01** | "without the visitor having brought anything to the encounter except the willingness to walk in" | INVENTED_VISITOR_STATE | INTERPRETATION | yes |
| **GR2-02** | "taken here not because the review places them above the rest…" | FORM_INSTRUCTION_AS_PROSE_CLAIM | INTERPRETATION | **EMPTY** |

Recall across the three gold versions on the *same unchanged detector output*: V1 50% → V2 71.4%
→ V2.1 62.5%. The movement is entirely gold calibration. Precision has been 100% throughout.

---

## 6. CORRECTION TO THE WG-1B CLAIM

WG-1B has been described as *"100% claim enumeration — omission is solved."* **That wording is
retired.** It is true about sentences and false about content.

**Corrected statement:**

> WG-1B achieved exhaustive **sentence accounting** (40/31/38 sentences, 176 claims) and located
> material corresponding to every gold finding. But **proposition normalization is lossy.**
> Enumeration may abstract an epistemically risky assertion into a safer paraphrase before any
> verdict is formed.
>
> Demonstrated by GR2-01. The prose
> *"without the visitor having brought anything to the encounter except the willingness to walk in"*
> was normalized to *"successive unprepared encounters with unfamiliar names"* — dissolving the
> visitor-state assertion into an adjective. The verdict stage then correctly judged the weakened
> proposition to be interpretation.
>
> **Sentence coverage was exhaustive. Content preservation was not.** The detector must preserve
> the factual content relevant to grounding, not merely visit every sentence.

Consequence: a verdict-only experiment **cannot** recover GR2-01, and would report a ceiling that
is an artifact of enumeration loss.

---

## 7. WG-3 — SPLIT INTO TWO INDEPENDENT CALIBRATIONS (DESIGN ONLY, NOT RUN)

### WG-3A — EXTRACTION FIDELITY

**Question:** Can exhaustive enumeration preserve the exact epistemically relevant content of
every proposition, rather than summarize it into a safer abstraction?

Content that must survive extraction: **human knowledge · preparation · mental state · time and
duration · proper nouns · qualifiers · source/reviewer behaviour.**

Candidate output contract per proposition:

```
SENTENCE_ID · EXACT_SPAN · ATOMIC_PROPOSITION · SUBJECT · PREDICATE ·
OBJECT/COMPLEMENT · SOURCE_ANCHOR
```

**The binding rule:** `ATOMIC_PROPOSITION` may normalize grammar. It may **not** delete factual
content present in `EXACT_SPAN`. It must not turn *"the visitor brought nothing except willingness
to walk in"* into *"an unprepared encounter"* — that deletes the visitor-state assertion.

Splitting SUBJECT / PREDICATE / OBJECT is not decoration: it forces the object of the claim to
become explicit, which is precisely what WG-3B needs to key on.

**Primary measure: UNSUPPORTED CONTENT PRESERVATION RECALL** — for each Gold V2.1 UNSUPPORTED
finding, does some enumerated proposition still carry the assertion that makes it unsupported?
Not "was the sentence inspected." Scored against `EXACT_SPAN`, blind to gold.

**No verdict changes in WG-3A.** Tested against frozen Gold V2.1.

### WG-3B — OBJECT-OF-CLAIM VERDICT

**Question:** With extraction fidelity assured, can the semantic verdict stage decide by **what
the proposition is claiming about** — so that article analysis of grounded subject matter stays
free, while a factual claim about a human state or about the source itself requires evidence?

| Object of the claim | Verdict rule |
|---|---|
| Grounded subject matter — evaluative comparison, metaphor, synthesis, causal reading | INTERPRETATION may be valid, **provided no new concrete fact is smuggled in** |
| A human state — knowledge, preparation, intention, belief | Requires source support |
| The source/review itself — what it says, ranks, omits, centres, intends, believes, does not do | Requires source support |

Class-B examples that are **not** automatically free interpretation merely because they sit inside
an essay: *"the review does not rank them"*, *"the reviewer centres X"*, *"the source never treats
them as…"*, *"the festival intends…"*.

**Concrete signal from V2.1, worth testing as a WG-3B probe:** both class-B misses (G13-04, GR2-02)
returned an **empty** `SOURCE_ANCHOR_RETURNED` and were nonetheless verdicted INTERPRETATION — one
of them reasoning that the source "bears out" a claim it cited nothing for. A meta-source claim
with no anchor should not be able to pass as interpretation. This is an **anchor-obligation** rule
keyed on the object of the claim, not a syntax rule.

The R3 pair is the discrimination test WG-3B must pass: *"it sits there without commentary"* must
stay INTERPRETATION (evidence supports it) while *"not because the review ranks them"* must go
UNSUPPORTED (evidence does not). Same shape, opposite verdicts, decided by evidence.

**Explicitly ruled out — already refuted, do not revisit:**

- comparative or causal syntax rules (WG-2B R5: 4 gold, 4 false — and the comparative family is
  now gold-INTERPRETATION, so the rule is net-harmful)
- visible hedge/interpretation-marker requirements (net discrimination **zero**: recovered 4 gold,
  falsely converted 4 legitimate)
- vocabulary or subject-noun blocklists for classes A and B (30:1 and 64:1 noise, measured)
- union with the narrow deterministic rules (strictly dominated: zero added recall, six added FPs)

**Success gate — unchanged, not softened:** UNSUPPORTED recall 100% at ≤ 2 false positives.
Baseline against Gold V2.1 is 62.5% / 100%. Unmet.

---

## 8. ARCHITECTURAL PRINCIPLE — REFINED GROUNDING DOCTRINE

> **CripMinds is allowed to say something the source never says.**
> That is the purpose of Discovery and interpretation.
>
> The grounding boundary is **NOT**: *"Does the source literally say this?"*
>
> The boundary is: **"Is this new meaning derived from source-grounded material, or did the writer
> add a new factual state about the world, a person, or the source itself?"**

This must survive future detector design. Every refuted approach in §7 failed for the same reason:
it tested the *form* of the sentence instead of the *object* of the claim.

Corollaries already measured, not asserted:

- Interpretation requires **no visible hedge**. Do not force "on this reading" / "perhaps" /
  "it seems" to make analysis legal.
- A negative or characterising claim about the source is **not banned** — it is **evidence-bearing**.
- Evaluative comparison of grounded material is **free**. `INTERPRETATION_AS_FACT` is an empty class.

---

## 9. UNTOUCHED

Gold V1 · WG-2A / WG-2B outputs · Article Form · repair (WG-0B) · production · deployment ·
Real Article Test 2. No models run. `.claude/WORK.md` and `.claude/LOGBOOK.md` not modified by
this amendment — the §8 doctrine is not yet promoted into the canonical docs. Owner's call.
