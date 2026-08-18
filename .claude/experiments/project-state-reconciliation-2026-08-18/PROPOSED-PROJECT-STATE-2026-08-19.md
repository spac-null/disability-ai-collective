# PROPOSED TRUE PROJECT STATE — 2026-08-19

Derived from preserved evidence, runtime reads and Git — not from prior documentation.
**No canonical doc was edited to produce this.** It is a proposal for a later canonical sync.

Local main: `7d59bb3` (evidence checkpoint). Trident deployed: `9f9bf35`. origin/main: `9f9bf35`.

---

## A. The four states, separated

### A1. CANONICAL ARTISTIC / EDITORIAL METHOD — unchanged, still valid

Nothing in the Edinburgh work challenges the method. Disability-derived perception as an
instrument that changes what a disturbance *becomes*; hidden mechanism over topic; source truth
and grounding as fail-closed preconditions; reader discovery over thesis delivery; plain
sophisticated prose; form follows material; articles are written **by** a disability lens, not
**about** disability. The Perplexity run is a clean negative demonstration of the last point: told
"for cripminds.com" it collapsed straight into disability-as-subject with an accessibility
checklist the source never earned.

### A2. CURRENT WORKING ARCHITECTURE — hypothesis, Edinburgh-calibrated

```
DISCOVERY → ARTICLE FORM → WRITER
```

- **Discovery** owns what the editorial system learned.
- **Article Form** owns selection, sequence, the change in reader understanding, the argumentative
  burden, and the arrival / stop point.
- **Writer** owns prose execution. The writer may know the destination; the **reader** experiences
  the discovery.

Status: **working hypothesis. Edinburgh-calibrated. Transfer validation pending. Not canonical,
not deployed.**

### A3. LIVE PRODUCTION ARCHITECTURE — what actually runs

Persona-brief pipeline with Fable as editorial director; Story Rejection V1.1 fail-closed
commission gate; PRF1 persona-routing invariant; AP1/APE2/PS1/LPF1 biography-provenance chain;
AR3-B testimony rule (zero testimony explicitly valid). CJ2 OFF (`CJ2_INTEGRATION_MODE` unset,
confirmed on trident). **Article Form and the Sofa shadow module are NOT deployed** —
`automation/orchestrator/sofa_discovery_shadow.py` does not exist on trident and is referenced by
neither `production_orchestrator.py` nor `generate.py`.

### A4. REJECTED / PARKED / SUPERSEDED

| Approach | Classification | Evidence |
|---|---|---|
| Blind-writer B.3/B.4 as default | **REJECTED as default** | Both produced unsupported dead-artist agency escalation |
| Conclusion-preloaded B.1/B.2 | **SUPERSEDED** | B.1 leaked editorial machinery into prose; B.2 hid labels but kept the preload |
| Mandatory testimony quota | **REJECTED, already shipped out** | AR3-B, live in production |
| CJ2 | **PARKED, OFF** | Do not enable. Its generate→verify→repair loop is a reusable idea, not the four-competitor frame |
| Reader Lab | **PARKED** | Untracked `RL-2026-003` candidates/preregistration on disk; no active thread |
| Old Scout gate (SV0 as blocker) | **SUPERSEDED** | See §C |
| Architecture B slices 1/1.1 | **SUPERSEDED by Article Form** | Synthetic-only; the real-material Edinburgh runs overtook them |

---

## B. The Edinburgh evidence chain — what it actually supports

Measured from the preserved grounding audits (not from narrative):

| Iteration | Words | Claims | UNSUP | UNCERT | SUPP | Unsupported rate |
|---|---|---|---|---|---|---|
| Legacy | 1227 | 10 | 6 | 1 | 3 | 60% |
| Sofa (original) | 1090 | 7 | 4 | 2 | 1 | 57% |
| B.1 | 1040 | 6 | 3 | 1 | 2 | 50% |
| B.2 | 873 | 7 | 5 | 2 | 0 | 71% |
| B.3 | 835 | 9 | 3 | 2 | 4 | 33% |
| B.4 | 829 | 7 | 4 | 2 | 1 | 57% |
| FORM-1 | 756 | 6 | 2 | 2 | 2 | **33%** |
| FORM-1.1 | 583 | 5 | 3 | 1 | 1 | **60%** |

Every iteration is grounding FAIL. Two honest readings, both required:

1. **Length and arrival discipline improved monotonically and substantially** — 1227 → 583 words,
   a 52% reduction, with FORM-1.1 stopping at arrival rather than continuing past it. That is a
   real, measured Article Form effect.
2. **Grounding did not improve, and FORM-1.1 regressed on it.** FORM-1 is the best result in the
   lineage by unsupported rate (33%, tied with B.3); FORM-1.1 shortened the article but its
   unsupported rate rose to 60% — the same as raw Legacy. Fewer total claims, worse ratio.

**Do not describe the lineage as monotonic improvement.** It is: Article Form fixed the *form*
problem (coherence, arrival, the agency/consent attractor did not recur after FORM-1) and has not
yet fixed the *grounding* problem. That distinction is the whole reason FORM-1.1's exact diagnosis
is the correct next action.

### Cross-model claim — corrected

The supported statement is narrower than previously recorded:

> Two clean Opus experiments, B.3 and B.4, using related blind-writer architectures, independently
> produced closely related unsupported dead-artist agency/choice escalation.

This suggests a failure in the blind-writer setup/material path. It does **not** establish
model-independent generality. Grok and Perplexity were fed a corrupted source containing B.3's
prose and cannot be used as confirmation (G-052). Qwen is **UNKNOWN** — neither its raw output nor,
more importantly, its input has been recovered.

---

## C. Scout SV0 — evidence-backed classification

**STATUS = HISTORICAL. RESOLUTION = SUPERSEDED. It is not a blocker.**

The old reconciliation (G-002) treated the SV0A/B/C/D verdict as a gate that later engineering had
improperly outrun. The evidence says the work did not outrun it — it consumed it:

- The three frozen benchmarks the canonical Sofa Method is extracted from all come from Scout
  directories: `scout-v0-4-fox-material-2026-08-17/the-fox-the-camera-missed-v044.md`,
  `scout-v0-2-hour-sofa-2026-08-18/the-hour-that-has-no-age-v025.md`,
  `scout-v0-5-mobile-evidence-reset-2026-08-18/mobile-v054.md`.
- Scout V0 continued into V0.1 → V0.5 as a *writing* lineage, and its outputs became the method's
  evidentiary base. That is the practical answer to "ship / reject / redirect": its articles were
  adopted as benchmarks.
- What was **not** adopted is Scout's *discovery front-end*. Edinburgh's commission came from an
  ordinary fetched news article (`source_origin: fetched_article`, 8,629 chars), not a disturbance
  card.

So the article-quality question SV0 posed is answered by use. The remaining question is narrow and
genuinely the owner's:

> **Is Scout's disturbance-discovery front-end still wanted?** Article Form calibration has been
> running off ordinary news seeds and working. Scout-as-discovery is currently neither adopted nor
> rejected — it is simply unused.

---

## D. Human-reader evidence — corrected weight

**Father.** He read the **Legacy** arm (PDF `5f6777d5…`, produced 17:22, message 19:02). His
"two undergrounds" message restates the article's own discovery back — he had just read it. It is
**not** independent arrival at the argument. What it does support: the argument survived reader
compression intact; he judged it original and important; he independently found the overall piece
insufficiently coherent ("hangt niet zo goed samen"), less on one line than others ("Blijft minder
op een lijn"), and the "I"/perspective unclear.

**Jascha.** Preferred Legacy's early narrative motion; found the Deaf anecdote a sudden jump; found
the article too long after arrival.

**Convergence worth keeping:** two readers, independently, praised the discovery and faulted what
came after it. That is the reader evidence behind the arrival/stop-point requirement — and it is
about **Legacy**, not about a Sofa output.

---

## E. Experimental-integrity requirements (method finding, not production code)

Before any future architecture/model test executes, preserve and hash: exact source snapshot +
hash, exact **rendered** prompt + hash, model identity, parameters, raw output + hash. Then
**verify that the source embedded in the rendered prompt equals the intended frozen source.**

That last check is not hypothetical. The Grok/Perplexity runs received a damaged terminal capture
with B.3's article interleaved into the Guardian review; ten B.3-specific phrases appear 0× in the
real source and 1× in what the models were given. A single prompt-vs-source hash comparison would
have caught it before any conclusion was drawn from it.

Two further method findings, already recorded in `GAP-LEDGER.md`:

- For `/tmp` evidence, cataloguing an at-risk artifact is **not** preservation — copy and hash
  during discovery. G-047 is the proof: four drafts catalogued at 23:55, destroyed by 00:00.
- Infer execution location from the runner's infrastructure needs. Check trident when a run
  required something the Mac cannot reach. Do not infer absence from a Mac-only search.
