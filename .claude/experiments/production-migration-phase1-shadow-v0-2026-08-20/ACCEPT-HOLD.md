# Shadow ACCEPT / HOLD

Defined in `impl/shadow_v0/decision.py`. **Not connected to publication, and must not be.**

## Not a port of `_compute_should_block`

Production's policy is a **negative** test over degraded stage names: block if `fable_brief`,
`gate_llm` or `persona_biography_unresolved` degraded, or if ≥2 stages failed. It could not
be carried across even if wanted, because those stage names do not exist in the target
architecture.

The shadow rule is **positive**: ACCEPT only on evidence; HOLD otherwise.

## ACCEPT requires all of

1. **Required artifact lineage complete** — every required stage present. `GROUNDING_REPAIR`
   is optional; everything else is mandatory.
2. **Writer output exists and the provider did not fail** — `provider_status == "ok"` and
   non-empty text.
3. **Grounding status settled** — not `unresolved`.
4. **No unresolved genuine unsupported finding** — every `TRUE_UNSUPPORTED` finding must be
   matched by a patch in `GROUNDING_REPAIR`.
5. **`TRUE_UNCERTAIN` findings explicitly adjudicated** — see below.
6. **Repair verified clean** where a repair exists: `residual`, `introduced` and
   `unrelated_edits` must all be 0.

Anything else HOLDs.

## UNCERTAIN holds by default

Per the brief, uncertain grounding HOLDs unless the preserved architecture explicitly
establishes otherwise. V0 implements exactly that: a `TRUE_UNCERTAIN` finding HOLDs unless the
findings artifact carries `uncertain_adjudicated: true`.

Test 2 sets that flag legitimately — its single uncertain finding (F3, "the operator" vs the
2017 recommendation's actual addressee) was explicitly adjudicated no-patch during the Test-2
grounding audit, on the reasoning that repairing it would require naming entities the article
deliberately does not name. That is a recorded adjudication, not a default.

A test asserts that clearing the flag flips Test 2 from ACCEPT to HOLD.

## Provider failure holds — no template fallback

The legacy fallback path (`generate.py:1064` → `generate_fallback_article`) publishes a
generic template article when every provider fails. The shadow architecture does **not**
implement that path.

**Shadow policy: provider or stage failure → HOLD.** A test asserts this, and the HOLD reason
explicitly names the rejected legacy behaviour.

This is recorded as a **shadow policy candidate**. It remains an owner decision before
production migration.

## Results on the two replayed fixtures

| Fixture | Decision | Reasons |
|---|---|---|
| Test 2 — Staniforth Road | **ACCEPT** | writer output present, provider ok · grounding settled · 2 `TRUE_UNSUPPORTED`, all repaired patch-only · 1 `TRUE_UNCERTAIN`, explicitly adjudicated · repair verified 0/0/0 |
| FORM-1.3 — Edinburgh | **HOLD** | 2 unresolved `TRUE_UNSUPPORTED` findings (C1, C2) |

FORM-1.3 holds correctly and for the right reason: its frozen grounding audit records
`status: FAIL` with 2 unsupported claims, and no repair was ever performed for it. The
fixture was included precisely because it exercises the HOLD path — a decision contract that
only ever accepts proves nothing.

## Unresolved policy questions, recorded for later

1. **Should `TRUE_UNCERTAIN` ever ACCEPT automatically**, or must adjudication always be an
   explicit human/recorded act? V0 requires the explicit flag.
2. **What is the adjudication authority** for setting `uncertain_adjudicated`? Currently the
   findings artifact asserts it; nothing verifies who decided.
3. **Does ACCEPT imply publishable?** Not in V0 — ACCEPT is deliberately disconnected from
   publication. The connection is a Phase-4+ decision.
4. **Should a HOLD be retryable**, and if so how many times, and does a retried run produce a
   new lineage or extend the existing one?
5. **Fallback**: confirm HOLD-on-provider-failure as production policy, replacing the template
   fallback.
