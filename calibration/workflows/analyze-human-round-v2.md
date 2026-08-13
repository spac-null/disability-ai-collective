# analyze-human-round-v2

**Job type:** `analyze_human_round` · **Version:** `v2` · **Registered:** 2026-08-13

## What changed from v1, and why

RL-2026-001's own completed analysis exposed a real instrumentation gap:
`machine_comparison` (v1's only human/machine comparison field) checks
**role** only — does the human reading and the machine reading agree the
claim is `factual_dependency` vs. `interpretive_only`? It never checks
**support direction**. The De Hooch/Z control item showed exactly why
that's a blind spot: both reviewers agreed `source_established` (role:
factual_dependency, support: supported), B2 independently calls the
identical claim `unsupported` (role: factual_dependency, support:
unsupported) — same role, opposite support — and v1's role-only field
reported `machine_comparison: "aligns"`, silently masking the reversal.

v2 adds three fields, additively, to every item analyze-human-round
already produced. **`machine_comparison` itself is unchanged in meaning**
— kept exactly as v1 defined it (role-only), for continuity — never
retroactively reinterpreted as if it had always meant something more.

## Everything v1 already guaranteed, still true in v2

- Each reviewer's judgment is preserved independently
  (`reviewer_judgments`) — never collapsed.
- Disagreement (`disposition: "contested"`) is a first-class outcome, not
  an error state, and is never converted into a manufactured consensus.
- No "ground truth," "winner," or "correct" language anywhere in the
  deterministic fields (the one model-generated field, `notes`, is
  independently banned-word-filtered — unchanged from v1).
- `role_alignment`/`support_alignment`/`overall_relation` are computed
  **only** when `disposition == "strong_reference"` (the reviewers
  agreed) — for `contested`/`needs_more_reviewers`/`insufficient_evidence`/
  `provisional_reference`, all three are `not_comparable`, exactly
  matching `machine_comparison`'s own existing `not_applicable` carve-out.
  This is structural, not a judgment call this pass adds: **a
  disagreement can never be silently resolved into an alignment claim.**

## New research_context shape (backward compatible)

v1's research_context carried one field, `machine_reference_label`
(role only, e.g. `"factual_dependency"`). v2 reads two new, separate
fields when present — `machine_role` and `machine_support` — set from
the start in any research_context built after this pass (e.g.
`calibration/research-context/RL-2026-002.json`). If only the old
`machine_reference_label` field exists (e.g. a historical round's
research_context predating this pass), `machine_comparison` still works
exactly as before (it falls back to `machine_role` only if
`machine_reference_label` is absent, never the reverse), but
`role_alignment`/`support_alignment`/`overall_relation` correctly report
`not_comparable` — v2 does not retroactively invent a support value for
research context that never recorded one. This is a deliberate,
accepted asymmetry, not a bug: **fixing the instrumentation going
forward never means quietly upgrading old, already-frozen research
context to look like it always had the new field.**

## New fields, per item

```json
{
  "role_alignment": "aligned | divergent | not_comparable",
  "support_alignment": "aligned | human_more_permissive | machine_more_permissive | divergent | not_comparable",
  "overall_relation": "full_alignment | role_only_alignment | divergence | not_comparable"
}
```

- **`role_alignment`** — `_role_alignment` in `calibration_runner.py`:
  `not_comparable` if there's no machine role reference, or the
  reviewers' agreed reading is itself `uncertain`, or the machine's own
  reference is `boundary_ambiguous`; otherwise `aligned` if human role ==
  machine role, else `divergent`.
- **`support_alignment`** — only meaningful when *both* sides treat the
  claim as `factual_dependency` (an interpretive reading has no support
  direction on either side, so it's `not_comparable`, never forced into
  a spurious match). `aligned` if the human's agreed support direction
  (`source_established` → supported, `unsupported_factual_dependency` →
  unsupported) matches `machine_support`; `human_more_permissive` if
  humans read it as supported and the machine flagged it unsupported
  (the De Hooch/Z shape); `machine_more_permissive` for the reverse
  (included for completeness — not observed in this project's own data
  yet).
- **`overall_relation`** — plain-language rollup: `not_comparable` if
  role itself isn't comparable; `divergence` if role diverges (support
  is moot once the underlying claim TYPE doesn't even match);
  `full_alignment` if role aligns and support either aligns too or isn't
  applicable (an agreed interpretive reading); **`role_only_alignment`**
  if role aligns but support doesn't — this is the exact case v1's
  `machine_comparison` alone could not distinguish from full alignment,
  and the reason this version exists.

Two enum values suggested in the original design sketch —
`support_only_alignment` and a `contested` value for `overall_relation`
— were deliberately dropped: neither is reachable given how
`role_alignment`/`support_alignment` are actually derived from the four
real reviewer-choice categories (there is no path to "support matches
but role doesn't," and `contested` already exists as the item's own
`disposition` — duplicating it into `overall_relation` would be
redundant, not additive). A cleaner four-value set beat forcing in two
values nothing in this data model can ever produce.

## Versioning mechanics

`analyze_human_round` and `prepare_next_round` now version
independently (`ANALYZE_HUMAN_ROUND_VERSION = "v2"`,
`PREPARE_NEXT_ROUND_VERSION = "v1"` in
`reader-lab-worker/src/calibrationOrchestrator.js`) — this pass changed
only the analysis side; forcing prepare-next-round through a meaningless
version bump would register a label for a file that never changed.
Job dispatch is still by `job_type` name only
(`calibration_runner.py`'s `JOB_HANDLERS`), not by version string — there
is exactly one deployed copy of `analyze_item` at a time. This is safe
specifically because every already-recorded v1 analysis artifact is an
immutable D1 row this code never reads back and mutates; v2 only ever
computes fresh output for a run armed after this deploy, never rewrites
history.

## Provenance

SHA256 of this file is recorded in `calibration_workflow_versions`
alongside the original v1 registration, which is never removed or
edited.
