# STRIP item 4 — "collapse duplicated definitions": PARKED, both halves unfounded

**Nothing shipped.** Neither duplication exists, and acting on the first half would loosen
a gate the owner set deliberately.

## Half 2: the "deadline" duplication does not exist

> "composition.py and new_engine_v1/provider.py still mean different things by 'deadline'"

`composition.py` contains the string **zero** times (`grep -ci deadline` → 0). The word
appears only in `provider.py`, `claims.py`, `documents.py` and `grounding_v2.py`, where it
is one consistent thing: an absolute `time.monotonic()` value threaded through HTTP and
model calls. There is nothing to collapse.

## Half 1: there is one definition already, and the asymmetry is the point

> "the planned path's negative_permissions still requires BOTH proposition and span to
> shape-match while the audit admits either"

The *shape test* is already single-owner: `story.negative_shape_of()`, called by
`composition.attributed_negative_is_explicit` (line 2828), by `free_composition` and by
`negative_admission_audit`. `composition.py:2819` says so explicitly — the same owner is
used "so a permission and the audit enforcing it cannot disagree about what a negative is".

The "both vs either" difference is not two definitions of a negative. It is two different
questions:

- **negative_permissions** asks *may this FACT be declared as a permission?* It requires
  the frozen proposition **and** the verbatim support span to state the negative
  independently, because — owner-directed 2026-09-10, with retained proof
  `production-20260910T073435Z-703b7b90` (pediatric mTBI, F39) — "a proposition that
  resolves an ambiguous source into a negative the span does not carry stays refused".
- **negative_admission_audit** asks *is this SENTENCE negative?* One text, so one test.

Collapsing them to "either" would admit facts whose source span does not carry the
negative — the exact case the owner ruled out. That is a loosening, and it is not
authorised. Collapsing them to "both" is meaningless: the audit has only one text.

## What was actually right in the item

The underlying complaint — that the permission compiler and the audit could drift apart —
was real, and it was already fixed by routing both through `negative_shape_of`. The item
appears to predate that fix.
