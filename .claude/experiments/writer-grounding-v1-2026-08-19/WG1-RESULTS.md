# WG-1 — Detector Recall Calibration

Shadow only. No production wiring. LOCAL_CLAUDE_SUBSCRIPTION. Repair untouched (WG-0B frozen).
Article Form untouched. Gold ledger frozen and used as the authority — not re-adjudicated.

## Frozen calibration set
FORM-1.3 / R2 / R3 + Guardian source + 95-proposition gold ledger (44 SUPPORTED,
39 INTERPRETATION, 2 UNCERTAIN, **10 UNSUPPORTED**).

## Configurations
- **WG-0 BASELINE** — deterministic pre-scan + ONE source-relative LLM audit. Preserved from
  WG-0A, not re-run.
- **WG-1A** — the SAME unchanged audit prompt, 3 independent samples per article (9 total),
  scored as UNION (any sample) and MAJORITY (>=2 of 3).
- **WG-1B** — ONE experimental prompt variant: exhaustive sentence-by-sentence claim enumeration.
  Every sentence numbered and accounted for; NO_CHECKABLE_CLAIM required where none exists.
  Blind to the gold ledger. Same source, same four verdicts, no new taxonomy.

## Results (denominator = 10 gold UNSUPPORTED; FP scored against the 95-proposition ledger)

| detector | TP | FN | FP | recall | precision |
|---|---|---|---|---|---|
| BASELINE strict | 6 | 4 | 0 | 60% | 100% |
| BASELINE lenient | 8 | 2 | 1 | 80% | 89% |
| WG-1A UNION strict | 6 | 4 | 1 | 60% | 86% |
| WG-1A UNION lenient | 7 | 3 | 8 | 70% | 47% |
| WG-1A MAJORITY strict | 3 | 7 | 0 | 30% | 100% |
| WG-1A MAJORITY lenient | 6 | 4 | 3 | 60% | 67% |
| WG-1B EXHAUSTIVE strict | 5 | 5 | 1 | 50% | 83% |
| WG-1B EXHAUSTIVE lenient | 5 | 5 | 3 | 50% | 62% |

**No configuration reaches the 100% unsupported-recall standard.**

## The decisive split (WG-1B)

- **CLAIM ENUMERATION RECALL: 10/10 = 100%**
- **UNSUPPORTED-VERDICT RECALL: 5/10 = 50%**

Every gold finding was seen. Five were seen and then classified **INTERPRETATION**:
G13-03, GR2-01, GR2-02, GR2-03, GR3-02.

Omission is solved. What remains is a **verdict-boundary** problem, not a coverage problem.

## Never detected by ANY configuration
- G13-03 "the second side is the one that presses" — INTERPRETATION_AS_FACT
- GR2-03 "the second direction is the harder one" — INTERPRETATION_AS_FACT

Both were enumerated by WG-1B and called INTERPRETATION. Sampling never surfaced either.

## Class coverage

| class | gold | base-s | 1A-union-s | 1A-union-l | 1B verdict | 1B enumeration |
|---|---|---|---|---|---|---|
| VISITOR_STATE/TEMPORAL | 3 | 1 | 1 | 2 | 2 | **3** |
| INTERPRETATION_AS_FACT | 3 | 1 | 1 | 1 | **0** | **3** |
| INVENTED_PROPER_NOUN | 1 | 1 | 1 | 1 | 1 | 1 |
| FORM_INSTRUCTION_AS_PROSE_CLAIM | 1 | 1 | 1 | 1 | 0 | 1 |
| QUALIFIER_DROPPED | 1 | 1 | 1 | 1 | 1 | 1 |
| INVENTED_TEMPORAL_SPECIFICITY | 1 | 1 | 1 | 1 | 1 | 1 |

Optional normalized parent category, added WITHOUT rewriting the original gold labels:
**UNSUPPORTED_SPECIFICITY** = VISITOR_STATE/TEMPORAL + INVENTED_TEMPORAL_SPECIFICITY +
INVENTED_PROPER_NOUN (5 findings). Historical labels preserved.

## Cost
- BASELINE: 1 audit call/article.
- WG-1A: **3** audit calls/article; observed latency 49-81s each.
- WG-1B: **1** audit call/article, ~3-4x output tokens (56/64/56 claims vs 3/8/4);
  observed latency 189-200s.

## Decision
**C — BOTH_INSUFFICIENT**, with the qualification that WG-1B changed the shape of the problem:
100% enumeration converts invisible failures into misclassified ones.

## Recorded, not acted on
Future repair-verification scope: VOICE / PERSON CONSISTENCY (R2 GR2-03's "seems to me").
WG-0B remains frozen.
