# Migration Sequence

Finite, staged, derived from repository evidence. **No implementation in this task.**

Each phase states its exit criterion. A phase that cannot meet its exit criterion stops the
sequence — it does not get worked around.

---

## Phase 0 — Freeze the production baseline

**Do:**
- Re-record `snapshot_test.py` baselines deliberately at current HEAD and tag the commit as
  the pre-migration baseline. The repo already carries `.snapshot_fixtures/generate_calls.json`
  and `llm_calls.json`; these become the reference for "what production did before."
- Capture N real recent articles with their full prompt/response chain as a comparison corpus.
- Record the live config state: `CJ2_INTEGRATION_MODE=OFF`, `L2_TESTIMONY_MODE=OFF`, cron
  schedule, Trident checkout SHA.

**Why first:** B3 — nothing currently compares two architectures. Without a frozen baseline
there is nothing to compare against, and every later phase's result is unfalsifiable.

**Exit:** a tagged baseline commit, a recorded corpus, and `snapshot_test.py --check` passing
against it.

**Touches production behaviour:** no.

---

## Phase 1 — Build the new architecture in shadow only

**Do:**
- Implement DISCOVERY + ARTICLE FORM as production modules, starting from
  `sofa_discovery_shadow.py` rather than from scratch (B2). It already has packet
  building/validation, `to_writer_context`, and `assert_no_persona_leakage`.
- Implement WRITER GROUNDING's modular arbitration as a production module on top of the
  existing `grounding.py` primitives (B1). This is the largest build: extraction,
  decomposition, negative source proof, arbitration, classified findings, patch-only repair,
  residual verification.
- Wire both behind an OFF-by-default flag, following the discipline `cj2_shadow.py` already
  establishes: never touches the published article, never raises, persists its own outcome.

**Why this order:** the two missing implementations are the only hard blockers. Everything
else in the plan is deletion, which is cheap and comes later.

**Exit:** both modules run end-to-end on the frozen Test-2 packet and reproduce the Test-2
result (Form followed, 2 unsupported found, 2 patches, clean after repair). If they cannot
reproduce a result we already have, they are not ready to meet new material.

**Touches production behaviour:** no — flag OFF.

---

## Phase 2 — Compare live vs shadow on held-out real stories

**Do:**
- Build the comparison harness (B3): same source, two architectures, both outputs preserved.
- Run on held-out real stories that are **not** Edinburgh and **not** Staniforth Road.
- Record for each: Form shape produced, grounding findings, patch count, arrival present and
  terminal, word count, and whether the legacy path's known pressures (testimony quota,
  persona roleplay, prohibition echo) appear in the legacy output and not the shadow one.

**Length data is collected here as a by-product** — this is where cross-story evidence for
the length question comes from, without running generations for that purpose.

**Exit:** enough comparisons to state where the two architectures genuinely differ, separated
from where they merely differ in wording.

**Touches production behaviour:** no.

---

## Phase 3 — Resolve only migration-blocking differences

**Do:**
- Define ACCEPT / HOLD in code (B5). This is a new rule, not a port of `_compute_should_block`.
- Resolve Story Rejection's FC2 finding, or explicitly accept it into the target (B6).
- Address only differences from Phase 2 that block migration. **Not** every difference, and
  **not** prose-quality differences.
- Decide the length question only if Phase 2 produced cross-story evidence for it. If it did
  not, it stays deferred.

**Explicitly not done here:** cleaning any legacy rule family. See
`LEGACY-RULE-MIGRATION.md` — 81% of them are deleted by Phase 4, not fixed.

**Exit:** a written list of resolved blockers, and a written list of accepted differences.

---

## Phase 4 — Production candidate: delete, then switch

**Do, in this order — deletion before switching, because deletion is what makes the switch
small:**

1. Remove the rewrite stage (`rewrite_with_opus` and its call site). Retires TV-02, TV-03,
   WP-13 and 47 rules at once.
2. Remove the two LLM rule-judges (`GATE_SYSTEM`, `RULES_SYSTEM`), keeping every
   deterministic check in `gate.py` and `review.py`. Retires the 9 R-number collisions and
   36 numbered rules.
3. Replace the writer prompt with the Form-derived prompt. Retires ~75 rule units, the
   persona canon double-injection, the register/type/length selectors, and the
   prohibition-heavy surface.
4. Decompose `_fable_editorial_brief`: keep Layer-1 commissionability and Layer-2 byline;
   drop the planner-authored prose fields.
5. Retire `style_rules.py` and `check_rule_drift.py`.
6. Move CJ-2/CJ-1 probe scripts out of `automation/` into `.claude/experiments/`.

**Exit:** the full test suite passes with deliberately re-recorded snapshots, each
re-recording justified in the commit as an intended rule change rather than a refactor
accident.

**Touches production behaviour:** yes — but not yet on Trident.

---

## Phase 5 — Production-fidelity test on Trident

**Do:**
- Deploy the candidate to Trident and run it against the real provider path.
- This phase **must** run on Trident: the production writer call routes through Trident-only
  CLIProxyAPI and is unreachable from the Mac (B4). Every prior phase's local result is
  therefore provider-agnostic and does not establish production fidelity.
- Compare against the Phase 0 baseline on the same sources.

**Exit:** the candidate produces acceptable articles on the real path, with grounding clean
after repair, and no regression in the deterministic checks.

---

## Phase 6 — Controlled migration with rollback available

**Do:**
- Switch the daily cadence to the new pipeline behind a flag that can be reversed in one
  step.
- Watch for a defined observation window before removing the legacy path from the codebase.
- Keep the legacy path present-but-unused until the window closes. Deleting it and switching
  in the same change removes the rollback.

**Exit:** observation window closed with no rollback triggered.

---

## Sequence summary

| Phase | Name | Blockers resolved | Production behaviour changes |
|---|---|---|---|
| 0 | Freeze baseline | — | no |
| 1 | Build in shadow | B1, B2 | no |
| 2 | Live-vs-shadow comparison | B3 | no |
| 3 | Resolve blocking differences | B5, B6, (B7 if evidence) | no |
| 4 | Production candidate — delete then switch | — | yes, locally |
| 5 | Production-fidelity test on Trident | B4 | yes, on Trident |
| 6 | Controlled migration | — | yes, live |

**Phases 0–3 change nothing a reader sees.** The first four phases are baseline, build,
compare, decide. That ordering exists so that the deletion in Phase 4 is made against
evidence rather than against the inventory's severity ranking.
