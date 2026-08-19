# Target Clean Architecture — candidate

Design only. Nothing implemented. Nothing deployed.

Derived from what has now been validated twice: the Edinburgh case (structural/semantic
discovery) and the Staniforth Road case (event/system/channel/recurrence), plus the
canonical SOFA method and the completed Legacy Prompt / Rule Inventory.

---

## Pipeline

```
WORLD / SOURCE
  → DISCOVERY
  → ARTICLE FORM
  → WRITER
  → WRITER GROUNDING
  → ACCEPT / HOLD
  → publication stages
```

**Not assumed:** that every current production stage survives. Several do not appear in
this pipeline at all, and that is deliberate — see `COMPONENT-DISPOSITIONS.md`.

---

## Stage responsibilities

### 0. WORLD / SOURCE

**Owns:** finding candidate material and freezing it before any analysis.

- Selects real published material with enough concrete evidence to carry an article.
- Freezes the source snapshot with SHA-256, URL and timestamp **before** discovery work.
- One strong primary packet preferred over a research bundle.

**Does not own:** whether the story is worth writing. That is Discovery's first question.

**Test-2 evidence:** the frozen source was 10,970 words of prose from a single document;
no external research was needed and none was authorised.

### 1. DISCOVERY

**Owns:** what the evidence appears to reveal, and whether it reveals enough.

- The dominant reading (stated, and not contradicted).
- The disturbance/mismatch — what does not fit the ordinary explanation.
- The perceptual instrument — which disability-derived way of perceiving makes the
  mechanism visible.
- What becomes knowable.
- **Commissionability** — whether the source supports a real mechanism at all. This is
  Story Rejection's question, and Story Rejection V1.1 already implements it in production.
- The grounding boundaries: what the source does not establish.

**Does not own:** sequence, form, or prose. Discovery must be stable before Article Form
begins.

**Rejection is a valid output.** A source that yields no sufficiently strong discovery is
declined, and no article is written.

### 2. ARTICLE FORM

**Owns:** material selection, the relationships among the material, argumentative burden,
sequence, the reader's route, where resistance goes, and the arrival and stop.

- Form follows material. There is no house form.
- Derived by asking the SOFA questions against *this* evidence: what must the reader meet
  first; what question does that create; what changes their interpretation; is there
  resistance at all; does it spiral, accumulate, reverse, narrow, or juxtapose; where has
  the reader arrived; what must not come after.
- Output is a route plus a burden statement, not a template.

**Validated across two shapes:** Edinburgh produced encounter → facts → countervoice →
semantic narrowing → distinction. Staniforth Road produced premise → channel taken apart →
event → resistance → accumulation → recurrence → structural arrival. Neither was derived
from the other.

**Editorial output constraints** (length, register) sit here — see `MIGRATION-SEQUENCE.md`
Phase 3 for why the length constraint is not yet specified.

### 3. WRITER

**Owns:** prose only.

- Receives: the Form route, the selected material with provenance, the grounding
  boundaries, and the full frozen source.
- **Byline ≠ prose persona.** The writer receives no persona canon, no biography, no wound,
  no voice block, no register selector, no beat, and does not write "in character."
- Writes in third person unless the material demands otherwise.
- No mass-injected style rule bundle. Test 2's entire instruction-and-material surface was
  **16,482 characters** against the legacy writer prompt's 59,161 characters of rules alone.

### 4. WRITER GROUNDING

**Owns:** sentence-level source fidelity.

Modular architecture, as exercised in Test 2:

1. faithful extraction of factual commitments
2. commitment decomposition (asserted state / source support / qualifier / preservation)
3. negative source proof for suspected unsupported commitments
4. deterministic modular arbitration
5. unsupported findings, classified

**Doctrine, load-bearing:** CripMinds may create new meaning from grounded facts. It may
not create new factual states about the world, people, or the source without evidence.
Interpretation is not patched merely because the source does not state it verbatim.

**Repair is patch-only.** No rewrite. Then verify: no residual, no repair-introduced claim,
no unrelated prose edits, Form movement preserved, voice preserved, arrival preserved.

**Status: SHADOW-CALIBRATED, successfully exercised once on Test 2. Not production-validated.**

### 5. ACCEPT / HOLD

**Owns:** whether the candidate may proceed.

- **ACCEPT** when: grounding is clean after calibated repair, the Form's arrival is present
  and terminal, and no safety finding survives.
- **HOLD** when any of those fail. A held article is not published and not silently
  degraded into publication.

Replaces the current `_should_block` degraded-stage policy with a positive-acceptance rule
rather than a count of failed stages.

### 6. PUBLICATION STAGES

Byline assignment (PRF1), images, links, social, publish. Largely unchanged; these are
downstream of acceptance and are not part of what Test 2 validated.

---

## What is deliberately absent from the target

| Absent stage | Why |
|---|---|
| **Whole-document rewrite** (`rewrite_with_opus`) | Test 2 had none and did not need one. The Form controls structure before writing; a 47-rule post-hoc rewrite re-imposes a house style the Form has already decided against. |
| **LLM rule-gate on numbered style rules** (`GATE_SYSTEM` R1–R17) | The rules it checks are the mass-injected style bundle. If the writer no longer receives that bundle, gating against it is checking conformance to a standard the piece was never written to. |
| **LLM rule-review on numbered style rules** (`RULES_SYSTEM` R1–R19) | Same. |
| **Persona canon injection into the writer** | `Byline ≠ prose persona`. |
| **Register / article-type / length weighted selectors** | Form follows material, chosen by Article Form, not sampled from a distribution before the material is read. |
| **Discovery anti-repetition nudges** | Corpus-hygiene machinery for a daily cadence, injected into the writer prompt. If retained at all it belongs in DISCOVERY's source selection, not in the writer's instructions. |

Their disappearance is the point: most of the inventory's 114 rule families are deleted by
this architecture rather than cleaned. See `LEGACY-RULE-MIGRATION.md`.
