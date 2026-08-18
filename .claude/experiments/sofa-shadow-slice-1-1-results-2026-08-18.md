# Sofa Shadow Slice 1.1 — Results

- **Date**: 2026-08-18
- **Status**: SHADOW ONLY. Nothing below was wired into, called by, or reachable from the live 09:00 production pipeline. Story Rejection, source selection, and grounding.py were not modified — this slice imports and reuses `build_evidence_packet` and `scan_free_prose_field` from `grounding.py` unmodified, and adds nothing to that module. No deployment occurred.
- **Scope**: fixes the two epistemic problems Shadow Slice 1 exposed (`.claude/experiments/sofa-shadow-slice-1-results-2026-08-18.md`) — material-item mistyping and packet-grounding-≠-article-grounding — and adds a post-writer grounding audit, per this task's instructions.

---

## SCHEMA CORRECTION

### Problem 1 — material items no longer hide interpretation inside an EVIDENCE envelope

**Before (Slice 1)**: `supporting_evidence`/`carrying_material` items were `{value: {kind, source_excerpt, note}, epistemic_type: EVIDENCE}` — one envelope, one type, covering a dict that mixed a literal source quote with free-text editorial commentary. A note like *"the written rule that does the actual work of hiding the units"* — a real interpretive claim about what a document reveals — sat inside a field typed as if the whole thing were source fact.

**After (Slice 1.1)**: each item is now

```
{
  "kind": "document",
  "source_excerpt": {"value": "...", "epistemic_type": "EVIDENCE"},
  "editorial_note":  {"value": "...", "epistemic_type": "EDITORIAL_GUIDANCE" | "EDITORIAL_INTERPRETATION"}
}
```

`source_excerpt` remains substring-checked against `source_text` exactly as before (grounding never weakened). `editorial_note` must be typed `EDITORIAL_INTERPRETATION` (the note asserts what the excerpt means or reveals) or `EDITORIAL_GUIDANCE` (the note is advice about using the material in the article) — **never `EVIDENCE`**, enforced in `validate_discovery_packet` as a hard validation failure, not a warning. A note-bearing item with no `note_type`, or an invalid one, is rejected at construction time (`_check_material_list` in `sofa_discovery_shadow.py`).

Applied to the SYNTH-1 regression case: *"the written rule that does the actual work of hiding the units, and its claim to be standard practice"* is now explicitly `EDITORIAL_INTERPRETATION`; *"a two-week question-and-answer sequence is a stronger narrative spine than the raw 61/214 ratio alone"* is explicitly `EDITORIAL_GUIDANCE` (advice about narrative use, not a claim about the world). These are different epistemic acts and are now typed as different things.

### Problem 2 (schema half) — known_gaps now typed GROUNDING_BOUNDARY

**Before**: `known_gaps` was one field, `{value: [str, ...], epistemic_type: EVIDENCE}` — a list of absence-statements typed as if it were a list of facts.

**After**: a new fifth epistemic type, `GROUNDING_BOUNDARY`, defined alongside `EVIDENCE`/`EDITORIAL_INTERPRETATION`/`EDITORIAL_GUIDANCE`/`EDITORIAL_METADATA`. Each gap is now its own envelope: `{"value": "...", "epistemic_type": "GROUNDING_BOUNDARY"}`. A gap statement is neither a fact (it asserts an absence, not a presence) nor ordinary interpretation/guidance — it's a hard editorial boundary on what the article may claim, and `validate_discovery_packet` now rejects a `known_gaps` item typed anything else, including `EVIDENCE`.

`hidden_mechanism` is unchanged: still `EDITORIAL_INTERPRETATION`, still inherited verbatim from the commission brief, still never regenerated. This correction was not touched, per the task's explicit instruction not to weaken it — `test_hidden_mechanism_never_labeled_as_evidence` still passes.

---

## ARTICLE-GROUNDING AUDIT

### Why a grounded packet did not guarantee a grounded article

Slice 1's SYNTH-1 shadow article introduced four claims the packet never authorized:

1. *"its hold cannot legally outlast forty-five days"* — a legal-enforceability conclusion; the source and packet only establish a **policy definition** (45 days), not a legal limit.
2. *"Nobody on the other end of those calls was lying"* — a claim about the knowledge/intent of unnamed people; the source establishes what Marcus Oyelaran was told, not what the tellers believed.
3. *"did not appear by accident"* — asserts deliberate design behind the rule's origin, directly contradicting the packet's own documented `known_gaps` entry that the evidence does not establish who created the practice or when.
4. *"for three years, nobody outside the authority had a reason to look for it"* (Slice 1 wording) — an unsupported claim about who else knew or looked.

None of these trip a literal-substring check, because none of them are excerpts at all — they are the writer's own sentences, and the packet-level grounding machinery (both Slice 1's and Slice 1.1's) only ever validates `source_excerpt` fields, never the finished article. This is exactly the gap the task named: **packet grounding and article grounding are two different questions, checked against two different objects.**

### Existing primitives inspected before writing anything new

Per the task's instruction, `grounding.py` was inspected first:

- **`scan_free_prose_field(text, source_text)`** — reused directly (imported, not duplicated) as `run_deterministic_prescan`. It is documented in its own docstring as catching only three shapes (quoted spans, Title-Case-run entities, 2+-digit numbers) and explicitly NOT a complete detector. Confirmed live against the planted regression text: it returns `[]` (nothing flagged) for *"Nobody...was lying... did not happen by accident... cannot legally outlast forty-five days"* — exactly the blind spot the task described, reproduced as `test_prescan_does_not_catch_planted_causal_or_motive_overreach`.
- **`find_new_unsupported_specifics`** — a before/after diff checker for revision passes, not applicable here (there is no "original" draft to diff against in this slice's flow).
- **`_fable_editorial_review`** (llm.py) — inspected as the task's preferred-reuse candidate. **Not reused**, for concrete reasons: it hard-enforces "first-person throughout" (canonical Sofa explicitly forbids mandatory first person), it is structurally built around persona canon/wound/first-person-episode checking (exactly the machinery this shadow track exists to route around), and it produces open-ended revision *notes*, not a per-claim SUPPORTED/UNSUPPORTED/UNCERTAIN verdict the task asked for. Reusing it would either reintroduce persona coupling into a persona-free module or require stripping so much of it down that little would actually be reused.

### What was built instead

A small, new auditor in `sofa_discovery_shadow.py` (not a new file — kept in the same module, since it's the same shadow concern): `build_shadow_grounding_audit_prompt` / `run_shadow_grounding_audit`, which runs the deterministic pre-scan first, then makes **one** model call scoped narrowly to the failure classes the deterministic pass cannot catch: unsupported causal claims, unsupported motives, unsupported certainty, and interpretation-from-the-packet presented as if it were source fact. It returns a structured `{"claims": [{"claim", "verdict", "reason"}, ...]}`, fails closed on unparseable output or a malformed claim (missing text or an invalid verdict).

`grounding_audit_passes(audit)` passes only if no claim is `UNSUPPORTED`, and every `UNCERTAIN` claim carries a non-empty `reason` — an undocumented `UNCERTAIN` is treated as a failure, matching the task's "or every remaining uncertainty is explicitly documented."

`discovery_packet_eligible_for_comparison(packet, audit)` is the **one** function that combines packet validation and article-grounding-audit results into an eligibility verdict — deliberately kept separate from `validate_discovery_packet` so packet-substring-validity is never reported as "the article is grounded." `sofa_shadow_probe.py` now runs this after every generation and writes `eligibility.json` alongside the article.

No automatic rewriting was implemented — diagnosis only, per the task's explicit instruction.

---

## SYNTH-1 REGRESSION RESULTS

The same synthetic case (`.claude/experiments/sofa-shadow-cases/synth-1-priority-b-hold.json`, fictional, disclosed) was re-run end to end through `sofa_shadow_probe.py` with `--offline`. As in Slice 1, no live model credentials exist in this environment, so the three model-shaped responses (Discovery, Writer, Grounding Audit) are **agent-authored, disclosed** in `.claude/experiments/sofa-shadow-cases/synth-1-fixture.json`'s own `_disclosure` field — this demonstrates the mechanism, not real model behavior.

The shadow article was deliberately kept close to Slice 1's original text, with the exact planted phrases the task named preserved or restored (plus one added fabricated number, "fifty-two," to also test the deterministic layer):

| Planted claim | Deterministic pre-scan | Model audit verdict |
|---|---|---|
| "cannot legally outlast forty-five days" (x2) | Not flagged (no quote/number/proper-noun shape) | **UNSUPPORTED** — policy definition ≠ legal limit |
| "fifty-two of the sixty-one units" (fabricated number, spelled out) | Not flagged (spelled-out numbers aren't in `_MULTIDIGIT_NUMBER_RE`'s digit-only pattern) | **UNSUPPORTED** — flagged as part of the same claim, explicitly named as an invented figure |
| "Nobody on the other end of those calls was lying" | Not flagged | **UNSUPPORTED** — unsupported motive/knowledge claim |
| "did not appear by accident" | Not flagged | **UNSUPPORTED** — contradicts the packet's own documented `known_gaps` |
| "It simply existed, already standard practice, the first time anyone official asked" | Not flagged | **SUPPORTED** — stays at the level the January 29 letter and the known_gaps actually support |
| "Neither document is lying" | Not flagged | **UNCERTAIN**, with a documented reason |

Result: **4 UNSUPPORTED, 1 UNCERTAIN (documented), 1 SUPPORTED**. `eligibility.json`: `"audit_passes": false`, `"eligible_for_comparison": false`. The deterministic pre-scan's own two hits were both false positives from the article's own title/heading being read as a "named entity" — a known, documented limitation of that blunt regex, not a real problem.

This directly confirms the task's premise: the deterministic layer alone would have let all four planted failures through silently (`test_prescan_does_not_catch_planted_causal_or_motive_overreach` proves this in isolation), and the model-audit layer is what actually catches the class of failure the task was concerned about (`test_audit_catches_planted_motive_and_causality_claims` is the direct regression test).

---

## TEST RESULTS

`automation/sofa_discovery_shadow_test.py`: **51 tests, 0 failures, 0 network calls** (up from 33 in Slice 1). Run: `python3 automation/sofa_discovery_shadow_test.py`.

New test classes added this slice:
- `DeterministicPrescanTests` (3) — confirms the reused `scan_free_prose_field` wrapper catches invented numbers, stays clean on grounded ones, and explicitly documents (via a test whose docstring states the premise) that it does NOT catch the causal/motive class.
- `ShadowGroundingAuditTests` (7) — catches planted unsupported factual specificity, catches all three planted motive/causality regression phrases in one case, lets a clean article pass, treats an undocumented `UNCERTAIN` as a failure, lets a documented `UNCERTAIN` pass, and fails closed on a malformed verdict or unparseable output.
- `EligibilityTests` (4) — eligible only when both packet and audit pass; not eligible if either fails alone; confirms packet-validity is never, by itself, reported as article-grounding.
- Extended `EpistemicTypingTests` with 4 new cases: material `editorial_note` can never be typed `EVIDENCE` (construction-time reject and post-hoc validator reject), and `known_gaps` items are `GROUNDING_BOUNDARY`, not `EVIDENCE` (construction-time and post-hoc validator reject).

All 33 Slice 1 tests were preserved and updated in place (fixtures now carry `note_type` per material item) rather than deleted — `git diff` on the test file shows extension, not replacement, of the original suite's intent.

---

## PACKET EPISTEMICS: PASS

Every field in a Discovery Packet now carries an explicit, individually-validated epistemic type, and the two Slice 1 mistyping bugs are both closed: a material item's `editorial_note` cannot be typed `EVIDENCE` (enforced at construction and by the standalone validator), and `known_gaps` items are typed `GROUNDING_BOUNDARY`, not `EVIDENCE`. `hidden_mechanism` remains `EDITORIAL_INTERPRETATION`, untouched, verified by a dedicated regression test.

## ARTICLE GROUNDING AUDIT: PASS (as a diagnostic capability — the SYNTH-1 article itself correctly reports FAIL)

The audit *mechanism* passes its own test suite and correctly identified all four planted regression failures plus one legitimate `UNCERTAIN` in the one case it was run against. To be precise about what "PASS" means here: the **capability** built this slice works as designed (catches the named failure class, fails closed on malformed output, correctly separates packet-grounding from article-grounding). The **specific SYNTH-1 article** it audited is correctly reported as **not** eligible for comparison (`eligible_for_comparison: false`) — that is the audit doing its job, not a defect in it.

## READY FOR REAL-MATERIAL SHADOW RUN: NO

Same material-availability gap as Slice 1, unchanged by this slice's work: no clean local evidence packet exists for Fox/Hour/Mobile (only prose drafts), no local production commissions exist (`engagement.db` is a 0-byte file in this checkout), and no live model credentials exist in this environment. This slice fixed the epistemic machinery and added the missing audit layer; it did not and could not create real test material or a live model connection. Both fixes are demonstrated only against the disclosed synthetic case.

## NEXT STEP:

Exactly the next-smallest-slice the task itself specifies: a **read-only export of 2-3 real accepted commissions** (their actual persisted Fable brief plus actual fetched source text — from the real production `engagement.db`/`article_plans` on the trident host, exported offline, never live-published against) **plus their existing production articles**, followed by a live Discovery + generic Writer + grounding-audit run against real credentials, compared side by side against the real production article using the same eight questions from Slice 1's §E. This is the first run that would test the actual hypothesis ("does this produce a noticeably better, still-grounded article from the same material") rather than only testing that the epistemic plumbing and the audit mechanism are sound — which is what Slice 1 and Slice 1.1 have now both confirmed, separately, in isolation.

---

## Files changed/created this session

- `automation/orchestrator/sofa_discovery_shadow.py` — modified: new `GROUNDING_BOUNDARY` type, restructured material-item schema (`source_excerpt`/`editorial_note` separated), `known_gaps` retyped, new post-writer grounding-audit section (`run_deterministic_prescan`, `build_shadow_grounding_audit_prompt`, `run_shadow_grounding_audit`, `grounding_audit_passes`, `discovery_packet_eligible_for_comparison`). `hidden_mechanism` semantics unchanged.
- `automation/sofa_discovery_shadow_test.py` — modified/extended: 51 tests (was 33), all Slice 1 fixtures updated to the new item shape, new test classes for the audit and eligibility logic.
- `automation/sofa_shadow_probe.py` — modified: now runs Discovery → Writer → Grounding Audit → Eligibility in one pass, writes `grounding_audit.json` and `eligibility.json` alongside the existing outputs.
- `.claude/experiments/sofa-shadow-cases/synth-1-fixture.json` — regenerated with `note_type` per material item and a new `audit` fixture (agent-authored, disclosed).
- `.claude/experiments/sofa-shadow-output/synth-1/{discovery_packet.json, writer_context.json, shadow_article.md, grounding_audit.json, eligibility.json}` — regenerated from the updated run.
- `.claude/experiments/sofa-shadow-slice-1-1-results-2026-08-18.md` — this file.

No file outside `.claude/experiments/` and the three `automation/` files above was touched. `git diff --stat -- automation/` shows zero changes to any tracked production file; `sofa_discovery_shadow.py`, `sofa_discovery_shadow_test.py`, and `sofa_shadow_probe.py` remain untracked/additive. Nothing was committed to git as part of this instruction.
