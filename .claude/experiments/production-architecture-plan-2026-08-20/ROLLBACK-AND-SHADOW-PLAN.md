# Shadow and Rollback Plan

## Shadow discipline

The repository already contains a working, proven shadow pattern. **Reuse it rather than
inventing one:** `orchestrator/cj2_shadow.py` establishes the discipline and
`testimony_l2.py` follows it.

The established contract, taken from `cj2_shadow.py`'s own docstring and code:

1. **OFF by default**, read from an environment variable, and when OFF the entry point is
   not called at all by `generate.py` — and still no-ops if it somehow were.
2. **Additive only.** Never touches `fable_brief`, `agent_name`, the article content, or any
   value the real pipeline uses. The return value is never consumed.
3. **Never raises.** Mirrors `_persist_article_plan`'s try/except discipline exactly, so a
   shadow-path failure can never be mistaken for, or cause, a real production failure.
4. **Persists its own outcome** to its own table, so the shadow run is auditable without
   touching production data.
5. **Modes are explicit and only reachable states are emitted.** `cj2_shadow.py` declares
   `PATH_CJ2_WINNER_DRAFT` and `PATH_CJ2_PRODUCTION` as forward documentation and never emits
   them.

New flags follow the same shape:

| Flag | Default | Meaning |
|---|---|---|
| `SOFA_DISCOVERY_MODE` | `OFF` | `SHADOW` runs DISCOVERY + ARTICLE FORM alongside the live path, persisting the Form it would have produced. Never influences the published article. |
| `WRITER_GROUNDING_MODE` | `OFF` | `SHADOW` runs modular arbitration on the live draft, persisting findings. Never patches the published article. |
| `SOFA_PIPELINE_MODE` | `OFF` | Phase 4+ only. `CANDIDATE` routes generation through the new pipeline. This is the single reversible switch. |

**`PRODUCTION_AUTHORITY` must not exist as a mode until Phase 4.** CJ-2 got this right and
it is worth copying: a mode that does not exist cannot be set by accident.

## What shadow can and cannot establish

**Can:** that the new modules run without error on real inputs; what Form they produce; what
grounding findings they raise on real drafts; how the two architectures differ; length data
across stories.

**Cannot:** production fidelity. Every local shadow result is provider-agnostic, because the
real writer call routes through Trident-only CLIProxyAPI (blocker B4). A shadow pass on the
Mac says nothing about what the production provider will do with the same prompt. This is why
Phase 5 exists and cannot be skipped.

**Cannot:** that the new pipeline is *better*. Shadow establishes difference, not quality.
Quality judgements stay with the owner and with the reader evidence, not with the harness.

## Rollback

### Phases 0–3
No rollback needed. Nothing production-facing changes. `git revert` on the evidence commits
is sufficient.

### Phase 4 — the deletions
This is where rollback matters most, because Phase 4 removes stages.

- **Each deletion is its own commit.** Rewrite stage, gate rule-judge, review rule-judge,
  writer prompt, brief decomposition, `style_rules.py` retirement — six commits, not one.
  A single squashed "migrate to new architecture" commit has no useful rollback granularity.
- **Deleted prompt text is preserved in the evidence root before deletion**, not recovered
  from git archaeology later. The captured prompts already in
  `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/` cover the writer and
  planner; the rewrite/gate/review systems should be captured the same way before removal.
- **`snapshot_test.py` baselines are re-recorded per deletion**, with the commit stating
  what changed and why it is intended. The repo's own rule already says: only re-record when
  a change is a deliberate rule fix, never for a refactor.

### Phase 5 — Trident
- Deploy by fast-forward only, as the current process already does.
- Verify file hashes match between Mac and Trident post-pull, as the AR3A release did.
- Roll back by fast-forwarding to the previous SHA. No database migration is planned, so
  there is nothing to reverse in data.

### Phase 6 — live switch
- The switch is `SOFA_PIPELINE_MODE`. Rollback is unsetting it. One step, no deploy required.
- **The legacy path stays in the codebase, present but unused, until the observation window
  closes.** Deleting the old path and switching to the new one in the same change removes
  the rollback and must not be done.
- Only after the window closes does the legacy code get removed, as its own commit.

## Standing safety constraints carried in

- `scatter.sh` is additive and never deletes `.env` or server-only files.
- No secrets in git-tracked files; `openclaw.json` uses `${VAR}` resolved at runtime.
- Never bare-rsync a directory that may contain gitignored state — this caused a real data
  loss incident on 2026-08-10.
- A push landing on `main` does not mean the site is live; confirm the Pages workflow.
- The production DB has no SQLite-safe backup yet. **This is an open risk that predates this
  plan and is not resolved by it.** Any phase that could write to `disability_findings.db` or
  `engagement.db` should not proceed until it is.

## Observability during shadow

Persist, per shadow run: source hash, packet hash, prompt hash, Form produced, grounding
findings with classifications, patch count, residual check result, word count, and wall-clock
cost. The Test-2 packet already demonstrates this shape — reuse its fields rather than
designing new ones.
