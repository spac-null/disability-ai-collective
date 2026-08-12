# analyze-human-round-v1

**Job type:** `analyze_human_round` · **Version:** `v1` · **Registered:** 2026-08-12

## Purpose

Turn one completed Reader Lab round's frozen research export into a
structured **evidence map** — not a fine-tuning step, not a verdict, not
a step toward automatically changing any B2/CJ prompt or model. Its only
job is to make what the humans said legible and comparable, per-item,
without ever collapsing independent judgments into a manufactured
consensus.

## Why this is deterministic, not model-assisted, for v1

Every disposition/agreement rule below is a direct, literal
transcription of categories this project already established, before
any orchestrator existed —
`.claude/reader-lab-v0-design-2026-08-12.md` `## 20.4` ("Reference-strength
categories — never collapsed into one label") and `## 14` ("two
independent humans agree" is "stronger provisional human reference,"
never "ground truth"). This workflow does not invent new research
judgment; it mechanizes judgment this project had already made in prose.
The one place a model is used (the optional `notes` field, `## 5` below)
never affects `disposition`, `agreement_state`, or any other field a
future statistical decision might key off — it is prose color only.

## Input contract

```json
{
  "round_id": "RL-2026-NNN",
  "research_export": { "...": "the full frozen export object from researchExport.js — see its own EXPORT_VERSION for that object's shape" },
  "research_context": {
    "...": "this round's frozen calibration_artifacts row of type research_context — see ## 10 of the design doc and RL-2026-001's own backfilled artifact for the shape",
    "per_item": {
      "<item_id>": {
        "b2_case_reference": "string, e.g. 'H08 (fresh-batch-1, engine Z)' — free text, not a live pointer into B2 code",
        "b2_failure_class_or_agreement": "string, e.g. 'R1 decomposition-coverage miss' or 'R1/R2 consistent agreement (control)'",
        "machine_reference_label": "'factual_dependency' | 'interpretive_only' | 'boundary_ambiguous' | null — the already-frozen B2 R1/R2 state for this item at round-creation time, NOT recomputed here",
        "dataset_purpose": "must match the item's own dataset_bucket — never used to override it"
      }
    }
  }
}
```

The research export is treated as read-only and immutable — this
workflow never writes to `research_exports`. `research_context` is also
read-only here; it was frozen at round publication (or, for RL-2026-001,
backfilled from already-public repo artifacts — see
`calibration/research-context/RL-2026-001.json`), never recomputed by
this job.

## Output contract

```json
{
  "analysis_version": "analyze-human-round-v1",
  "round_id": "RL-2026-NNN",
  "generated_at": "ISO-8601",
  "items": [
    {
      "item_id": "string",
      "slot": "number",
      "reviewer_judgments": [
        { "reviewer_id": "string", "internal_normalized_response": "string", "confidence": "string|null", "has_comment": "boolean" }
      ],
      "agreement_state": "agreement | disagreement | single_judgment",
      "confidence_summary": "string, e.g. '2 pretty_sure' or '1 pretty_sure, 1 not_very_sure' or 'none stated'",
      "comments_present": "boolean",
      "reference_strength": "strong_provisional | single_provisional | none",
      "machine_comparison": "aligns | diverges | no_machine_reference | not_applicable",
      "disposition": "strong_reference | provisional_reference | contested | needs_more_reviewers | insufficient_evidence",
      "notes": "string | null — optional, model-assisted, prose-only, see ## 5"
    }
  ],
  "round_summary": {
    "strong_reference": "count", "provisional_reference": "count",
    "contested": "count", "needs_more_reviewers": "count", "insufficient_evidence": "count"
  }
}
```

**Never present in this output:** a "winner," a computed correct answer,
a confidence score attached to the disposition itself, any judgment
about whether a human or B2 was "right."

## 1. `reviewer_judgments`

Copied directly from the research export's per-item `judgments` array —
`reviewer_id`, `internal_normalized_response`, `confidence`,
`has_comment` (derived: `!!comment`, never the comment text itself
copied into this analysis artifact — comments stay in the export/raw
responses, this artifact only ever notes *that* one exists). Ordered by
`reviewer_id`, matching the export's own ordering convention.

## 2. `agreement_state`

- 1 judgment → `single_judgment`
- 2+ judgments, all identical `internal_normalized_response` → `agreement`
- 2+ judgments, not all identical → `disagreement`

## 3. `reference_strength` and `disposition`

Direct transcription of `## 20.4`'s four categories, plus
`needs_more_reviewers` (an item this round's own `research_context`
explicitly flags as under-reviewed — e.g. only one reviewer was ever
assigned it) and `insufficient_evidence` (defensive fallback; should not
occur for a genuinely completed round, since completion requires every
assigned reviewer to have answered — if it ever does occur, that is a
bug worth investigating, not a silent pass-through):

| reviewer count | agreement_state | reference_strength | disposition |
|---|---|---|---|
| 1 (and not flagged needing more) | `single_judgment` | `single_provisional` | `provisional_reference` |
| 1 (flagged needing more) | `single_judgment` | `single_provisional` | `needs_more_reviewers` |
| 2+ | `agreement` | `strong_provisional` | `strong_reference` |
| 2+ | `disagreement` | `none` | `contested` |
| 0 | — | `none` | `insufficient_evidence` |

`strong_reference` is still, explicitly, "stronger provisional human
reference" in the sense of `## 14` — never ground truth, never
auto-promotable to a training label without the separate, human,
editorial steps `## 15` of the design doc already requires.

## 4. `machine_comparison`

Only meaningful when `disposition = strong_reference` (a strong human
reference actually exists to compare). Compares the agreed
`internal_normalized_response`'s role — factual dependency vs.
interpretive — against `research_context.per_item[item_id].machine_reference_label`:

- `aligns` — the human strong reference and the frozen machine label
  agree on role (factual_dependency vs. interpretive_only).
- `diverges` — they disagree.
- `no_machine_reference` — `research_context` has no machine label for
  this item (e.g. a hand-authored control never run through B2).
- `not_applicable` — disposition isn't `strong_reference` (provisional/
  contested/needs_more_reviewers/insufficient_evidence never get a
  machine comparison; comparing a single or contested judgment against
  a machine label would misrepresent both).

This is a comparison, never an adjudication — it does not decide who was
"right." A `diverges` result is exactly the kind of finding this whole
project exists to surface, not paper over.

## 5. `notes` (optional, model-assisted)

The only field a model touches. Purpose: a short, plain-language
description of *what the judgments actually show* — e.g. "Both reviewers
read the causal framing as an addition the source doesn't establish" or
"One reviewer read this as a direct restatement of the source; the other
flagged the added cause as unsupported." Generated by the Trident runner
calling the local CLIProxyAPI route
(`calibration/runner/calibration_runner.py`), given only this item's
`source_snapshot`, `candidate_sentence`, and the reviewers' public
selections/comments (never `research_context`, never the machine
comparison, never any other item's data — kept narrowly scoped so it
cannot smuggle in a consensus opinion from context it wasn't given).

**Structural constraint, enforced by the runner, not just requested of
the model:** the model's output is never written into `disposition`,
`agreement_state`, `reference_strength`, or `machine_comparison` — those
four fields are computed by the deterministic rules above and are never
touched by model output. If the model call fails or returns something
that doesn't parse as a plain string, `notes` is simply `null` — this
never blocks or degrades the deterministic analysis, which has already
been computed by the time `notes` is attempted.

**Prompt used** (verbatim, temperature 0.0, no other instructions,
result truncated/discarded if it introduces a verdict word from the list
below):

```
You are describing what two independent readers noticed about a short
passage and a sentence written from it — never judging who was right.

SOURCE:
{source_snapshot}

THE SENTENCE:
{candidate_sentence}

READER JUDGMENTS:
{for each judgment: "{reviewer_label}: chose '{selected_public_response}'
(confidence: {confidence or 'not stated'}). Comment: {comment or
'none'}."}

In one or two plain sentences, describe what these judgments show about
how the sentence was read. Do not say which reader was correct. Do not
use the words "ground truth," "winner," "correct," or "consensus." If
the judgments simply agree, say what they agree the sentence does. If
they differ, say what specifically they differ about.
```

A banned-word check (`ground truth`, `winner`, `correct`, `consensus`)
runs on the model's raw output before it is accepted as `notes`; a
violation discards the output (`notes: null`), same as an outright call
failure — the deterministic fields are never affected either way.

## Provenance

SHA256 of this file is recorded in `calibration_workflow_versions` at
deploy time (`wrangler d1 execute`, not hand-typed) — see the design
doc's calibration-orchestrator section for the exact value as of
deployment.
