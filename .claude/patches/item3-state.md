# STRIP item 3 — CUT machinery on the free path: PARKED, already done

**Nothing shipped. Nothing to ship.** The item asks to "remove the CUT machinery from the
free path's audit — skipped on this path, cannot fire". Measured: it is already inert
there, by design, and the only way to "remove" it further would take it from the planned
path too, where it legitimately fires.

## What the code already does

`new_engine_v1/free_composition.py` (module docstring, ~line 74) hands Safety what is true
of a path with no plan:

```
packet  = a licensing record over the WHOLE Ledger -- nothing was withheld
arch    = {}  nothing was planned
cut     = {}  nothing was cut, so nothing can leak
```

and records the measurement that motivated it: on both offline arms, CUT_LEAKAGE fired on
F19/F20 — "Ledger facts, licensed and true, that the ARCHITECTURE had chosen to cut" —
and with `cut = {}` "every CUT_LEAKAGE finding disappears, no new finding appears, and
UNSUPPORTED_NEGATIVES still blocks".

Confirmed on a live free-path run (…60929T230317Z-36065d96), all three audits:
`cut_declared: 0, violations: 0, advisories: 0, ok: True`.

## What the record says

| | runs | CUT_LEAKAGE holds |
|---|---|---|
| free | 9 | **0** |
| planned | 175 | 10 |

The kill count the item cites was earned on the **planned** path, where CUT is doing its
job: watching facts the Architecture deliberately cut. `factual_surface_audit` /
`safety_audit` are SHARED between the paths, so deleting the machinery would remove a
live gate from the planned path. That is a loosening, and it is not authorised.

## Where the "23 blocks, 13 sole cause" figure goes

I could not reproduce it. Counting runs whose `COMPOSITION_RESULT.json` carries a
`CUT_LEAKAGE`/`PACKAGE_CUT_LEAKAGE` finding gives **10**, all planned-path. 35 runs mention
the string somewhere (MANIFEST, SHADOW_DECISION included), so the figure depends entirely
on what is counted. **I could not measure "sole cause" at all** — my first attempt treated
stage statuses (`NOT_RUN`, `SAFETY`, `SAFETY_HOLD`) as findings, which makes the number
meaningless, and I am recording that rather than reporting a figure I cannot defend.

Caveat on the other side: only **9** free-path runs exist in the record, because the engine
switched recently. "Never fires on free" rests on the code and the `cut = {}` contract,
not on those 9 runs.

## If anything is left here

A tidying at most: the free path still *computes* cut adherence over an empty cut set on
all three audits. It costs a little work and puts an always-zero block in every
SAFETY_AUDIT.json. That is telemetry noise, not a gate, and not worth a deploy on its own.
