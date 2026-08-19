# Production Debt Before Migration

Brought forward from the Legacy Prompt / Rule Inventory (`38c47b8`) and re-adjudicated
against the target architecture. **Nothing is fixed here.**

The key re-adjudication: the inventory classified debts by severity. This plan classifies
them by **whether the owning stage survives**. A severe debt in a stage that is being
deleted is not a migration blocker — it is work to avoid.

---

## Previously MUST_FIX_BEFORE_PRODUCTION_MIGRATION — re-adjudicated

| Debt | Inventory class | Owning stage fate | **New disposition** |
|---|---|---|---|
| **AR3 testimony quota alive in rewrite 33/33b** | MUST_FIX | rewrite stage **REMOVE** | **DO NOT FIX — DELETE WITH STAGE.** Patching two rules inside a 47-rule prompt that is being removed is wasted work. *Caveat below.* |
| **Gate/review R-number collisions (9 rules)** | MUST_FIX | both LLM rule-judges **REMOVE** | **DO NOT FIX — DELETE WITH STAGE.** Renumbering a scheme that is being abolished is wasted work. |
| **WP-13 UK-preference mismatch** | MUST_FIX | rewrite stage **REMOVE** | **DO NOT FIX — DELETE WITH STAGE.** |
| **Canonical/runtime inconsistency** (`CONTEXT.md` claiming `style_rules.py` is the single source of truth; `check_rule_drift.py` presented as a linter to run) | MUST_FIX | documentation | **ALREADY FIXED** in commit `7778ee1`. No further action. |

### The one caveat, stated plainly

These three debts are live **today** and remain live for the whole duration of the
migration. AR3's quota will keep pressuring every production article toward a second named
voice and a spoken quote until the rewrite stage is actually removed. If the migration
stalls, is deprioritised, or runs longer than a couple of months, that reasoning inverts and
the cheap patch becomes correct.

**Owner decision required:** accept the debt for the migration window, or apply the ~3-line
AR3 patch now as insurance. The plan's recommendation is to **accept it**, on the condition
that a stall triggers reconsideration — but this is the owner's call, not the plan's, because
it trades a known live editorial pressure against avoided work.

---

## Previously CONSOLIDATE_BEFORE_PRODUCTION — re-adjudicated

| Debt | Owning stage fate | **New disposition** |
|---|---|---|
| **Duplicated persona canon** (7,216 ch injected twice, byte-identical, contradictory framing) | writer prompt **REPLACE**; target writer receives no persona canon | **DO NOT CONSOLIDATE — DELETE WITH STAGE.** |
| **Mass-injected writer prompt** (59,161 ch / 75 rule units) | **REPLACE** | **DO NOT CLEAN — REPLACE WHOLESALE.** This is the migration's central act. |
| 8 five-copy style families, 16 four-copy families | writer/rewrite/gate/review copies all **DELETED_WITH_STAGE** | **DO NOT DE-DUPLICATE.** |
| Three separate forbidden-word lists | all in deleted stages | **DO NOT CONSOLIDATE.** |
| `CRAFTED RHETORIC` exemption drift across 3 copies | all in deleted stages | **DO NOT CONSOLIDATE.** |

---

## Previously a PRODUCTION CLEANUP RISK

**Negative-prohibition density** — 80 negative tokens in the live writer prompt, several
carrying concrete nouns and verbatim bad-example sentences (Edinburgh's finding that
negative Form instructions can surface as positive prose claims).

**New disposition: RESOLVED BY REPLACEMENT.** The surface is not audited, rebalanced, or
rewritten — it is removed with the writer prompt. Test 2's writer prompt carried its
prohibitions as narrow, story-specific grounding boundaries rather than a universal
prohibition bundle, and the output showed no prohibition-echo. That is one story's evidence,
not proof, but it is the right direction and it costs nothing to adopt.

---

## Actual migration blockers

These are the things that genuinely prevent the migration from proceeding, derived from
repository evidence rather than from the inventory.

| # | Blocker | Evidence | Resolution phase |
|---|---|---|---|
| **B1** | **Writer Grounding has no production implementation.** The modular arbitration architecture exists only under `.claude/experiments/writer-grounding-*`; nothing in `automation/` imports it. | grep: zero production references | Phase 1 — largest build |
| **B2** | **Article Form has no production implementation.** `sofa_discovery_shadow.py` (65,335 ch) exists but is imported by no production module. | grep: importers are experiment dirs and its own test only | Phase 1 |
| **B3** | **No live-vs-shadow comparison harness exists.** `snapshot_test.py` compares production against *itself*; nothing compares two architectures on the same story. | `snapshot_test.py` docstring | Phase 2 |
| **B4** | **The production writer path is unreachable from this machine.** The real writer call routes through Trident-only CLIProxyAPI; `call_llm_via_openclaw_session`'s provider list has no OpenRouter-direct fallback the way `_call_editorial_model` does. | `LOGBOOK.md` AR3A entry, recorded as a standing constraint | Phase 5 — must run on Trident |
| **B5** | **ACCEPT/HOLD has no definition in code.** `_compute_should_block` cannot be carried across: it keys on stage names (`gate_llm`, `fable_brief`) that will not exist with their current meanings. | `generate.py:71–105` | Phase 3 |
| **B6** | **Story Rejection's FC2 finding is open.** The commission path has no grounding verification equivalent to the decline path's. N=1, deliberately unpatched. Story Rejection is KEEP, so this debt travels into the target. | `project_cripminds_story_rejection_fc2_finding_2026-08-17` | Owner decision, before Phase 4 |
| **B7** | **Length control is unspecified.** See below. | Test 2: 1,587 words vs 900–1,200 | Deliberately deferred |

---

## Length control — non-blocking editorial debt

Test 2 produced 1,587 words against a requested 900–1,200.

**Classification: NON-BLOCKING EDITORIAL / LENGTH-CONTROL DEBT.** Recorded, not solved.

**Likely owner: ARTICLE FORM**, as an editorial output constraint — the same layer that owns
sequence, burden and arrival. The Staniforth Road overrun concentrated in the two movements
that asked for many enumerable facts in a fixed order, which suggests the missing control is
a *compression rule per movement*, not a global word cap.

**Do not introduce a rigid universal length mechanism yet.** One story is not enough
evidence. Edinburgh landed inside its range; Staniforth Road did not; the difference
correlates with how much enumerable fact the material supplies. A universal cap imposed on
that evidence would be a house rule invented from n=2 — precisely the class of thing the
legacy prompt accumulated 75 of.

**Requires future cross-story evidence before any mechanism is introduced.** No model
experiment now. If length data is wanted, it should be collected as a by-product of Phase 2's
shadow comparison, not by running generations for the purpose.
