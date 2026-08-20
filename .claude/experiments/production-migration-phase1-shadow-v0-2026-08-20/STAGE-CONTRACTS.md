# Stage Contracts

Schema version `shadow-v0.1`. Defined in `impl/shadow_v0/contracts.py`.

Every stage emits one `Artifact`. The pipeline is reconstructable from the artifacts alone.

## Common envelope

| Field | Purpose |
|---|---|
| `schema_version` | `shadow-v0.1`; a mismatch fails closed |
| `stage` | stage identity, from a fixed vocabulary |
| `created_at` | **injected, never clock-read** — replay must be deterministic |
| `input_hashes` | `{name: content_hash}` of every artifact consumed |
| `payload` | stage-specific content |
| `content_hash` | SHA-256 over canonical JSON of all of the above |

`created_at` being injected is what makes artifact hashes stable across runs. A test asserts
two independent replays produce identical hashes for all eight stages.

## Per-stage payload requirements

| Stage | Required fields | Additional enforcement |
|---|---|---|
| `SOURCE_SNAPSHOT` | `source_text`, `source_sha256`, `provenance.origin` | `sha256(source_text)` must equal `source_sha256` |
| `DISCOVERY` | `dominant_reading`, `disturbance`, `perceptual_instrument`, `what_becomes_knowable`, `grounding_boundaries` | |
| `ARTICLE_FORM` | `route`, `arrival`, `burden` | `route` must be a non-empty list of movements |
| `WRITER_INPUT` | `prompt_text`, `prompt_sha256` | hash must match; **29 legacy prompt markers rejected** |
| `WRITER_OUTPUT` | `article_text`, `article_sha256`, `provider_status` | hash must match; status ∈ {`ok`,`failed`} |
| `GROUNDING_FINDINGS` | `status`, `findings` | status ∈ {`settled`,`unresolved`}; every finding classified `TRUE_UNSUPPORTED` / `TRUE_UNCERTAIN` / `LEGITIMATE_INTERPRETATION` |
| `GROUNDING_REPAIR` | `mode`, `patches`, `article_text`, `article_sha256` | `mode` must be `patch_only` — **a rewrite is rejected** |
| `SHADOW_DECISION` | `decision`, `reasons` | decision ∈ {`ACCEPT`,`HOLD`} |

`GROUNDING_REPAIR` is the only optional stage: a draft with no unsupported findings has
nothing to repair.

## Fail-closed behaviour

`ContractViolation` is raised, never swallowed, on:

- unknown stage, wrong schema version, missing `created_at`
- any missing or empty required payload field
- a declared content hash that does not match its own content
- a declared input hash that does not match the artifact actually supplied (`verify_lineage`)
- a legacy prompt marker in `WRITER_INPUT`
- a repair claiming any mode other than `patch_only`

Each of these has a test.

## Writer Grounding contract

Writer Grounding was **not redesigned**. It is represented as a downstream stage whose
interface carries the frozen shadow-calibrated architecture's outputs: faithful extraction,
commitment decomposition, negative-source proof, modular arbitration, patch-only repair, and
verification (`residual`, `introduced`, `unrelated_edits`, plus movement/voice/arrival
preservation flags).

For V0 replay these are read from the preserved Test-2 audit rather than recomputed. The
migration property being proven is the handoff shape: **grounding receives writer output plus
the source snapshot, and cannot alter the Article Form.**
