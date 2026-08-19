# Live Production vs Target Architecture

Live stage order read directly from `automation/orchestrator/generate.py`
(`_run_production_automation_locked`) at HEAD `8741804`. Line numbers are evidence, not
decoration.

## Live pipeline, in execution order

| # | Live stage | Call site | Target counterpart |
|---|---|---|---|
| 1 | news seed / DB discovery | `generate.py:208,211` | WORLD / SOURCE |
| 2 | source fetch + evidence packet | `discovery.py:1142`, `grounding.py:129` | WORLD / SOURCE (freeze) |
| 3 | L2 testimony shadow attempt | `generate.py:414` (`L2_TESTIMONY_MODE=OFF`) | — (parked) |
| 4 | Fable commission / persona brief | `generate.py:420` → `llm.py::_fable_editorial_brief` | **split**: DISCOVERY + byline selection |
| 5 | Story Rejection verdict handling | `generate.py:435,442,447` | DISCOVERY (commissionability) |
| 6 | CJ-2 shadow attempt | `generate.py:551` (`CJ2_INTEGRATION_MODE=OFF`) | — (parked) |
| 7 | **writer prompt assembly + writer call** | `generate.py:783–1050`, `:1057` | ARTICLE FORM + WRITER |
| 8 | fallback article | `generate.py:1064` | ACCEPT/HOLD (should HOLD, not publish) |
| 9 | persona biography editorial pass | `generate.py:1154,1197` | WRITER GROUNDING (persona-history arm) |
| 10 | **whole-document rewrite** | `generate.py:1168` → `llm.py:343` | — (**absent from target**) |
| 11 | pre-publication check | `generate.py:1207` | publication stages |
| 12 | article plan persistence | `generate.py:1276` | evidence/lineage |
| 13 | **pre-commit gate** (R1–R17, blocking) | `generate.py:1302` → `gate.py:218` | **split**: deterministic checks KEEP, LLM rule-gate absent |
| 14 | degraded-run block policy | `generate.py:1353` → `_compute_should_block` | ACCEPT / HOLD |
| 15 | `validate_article` (review) | `generate.py:1401` → `review.py:849` | **split**: fact-check + engagement KEEP, LLM rule-review absent |
| 16 | publication safety stamp | `generate.py:1415` | ACCEPT / HOLD |

## Structural differences

**1. The Form does not exist in production.** Live production has no stage between "brief"
and "write." Sequence, burden, resistance and arrival are all implicit in a 59,161-character
writer prompt that is identical for every story. The target inserts ARTICLE FORM, derived
per story, which is the thing Test 2 validated.

**2. Grounding runs in production but only as a scanner, not as an arbiter.**
`grounding.py`'s deterministic scanners (`find_new_unsupported_specifics`,
`scan_draft_for_unsupported_specifics`, `validate_evidence_field`) are real and live. What
does not exist in production is the modular arbitration architecture — extraction,
decomposition, negative source proof, classified findings, patch-only repair with residual
verification. Test 2 exercised that; production has never run it.

**3. Production corrects after the fact; the target decides before.** Live: write against a
universal rule bundle, then rewrite against a second rule bundle, then gate against a third,
then review against a fourth. Target: decide the form from the material, write once, verify
fidelity, accept or hold.

**4. Persona is prose voice in production; byline in the target.** Live, the writer prompt
opens `YOU ARE MAYA FLUX` and carries the canon twice. The target sends the writer no
persona material at all.

**5. Blocking is negative in production, positive in the target.** `_compute_should_block`
blocks when named stages degraded or 2+ stages failed — an absence-of-failure test. The
target ACCEPTs on positive evidence: grounding clean, arrival present, no safety finding.

## What live production has that the target keeps

Story Rejection V1.1, the evidence packet and its lineage/containment checks, the
deterministic prose and integrity checks, web fact-check, PRF1 rotation as byline selection,
and every post-acceptance publication stage. These are not casualties of the migration —
several are the strongest parts of the current system.
