# WG-6A PRE-REGISTRATION — MODULAR VERDICT ARBITRATION

Written and committed to BEFORE any scoring was run. The routing rule below is
fixed. It was not adjusted after seeing the confusion matrix.

## QUESTION

WG-5 composed WG-4A decomposition + WG-3B object-awareness + WG-4B negative-source
proof into ONE monolithic LLM verdict prompt. Recall reached 8/8 but the composed
prompt lost WG-4B's standalone BOUNDED_ABSENCE distinction and produced one false
positive on the R3 control.

WG-6A asks: can component behaviour be preserved by composing VERDICTS through
small deterministic arbitration instead of merging SEMANTICS into one judgment?

## METHOD — REUSE / RESCORE, NOT A FRESH SAMPLED RUN

No new model calls. This is stated up front because it changes what the result
can and cannot prove.

WG-4A and WG-4B were run on the SAME frozen WG-3A extraction (236 parents,
identical input hashes). Their raw outputs are preserved and checksum-verified.
The arbitration layer under test is pure deterministic code. Therefore the
arbitrated verdict set is fully determined by artefacts that already exist, and
executing the components again would only add sampling noise to inputs that are
already frozen.

WHAT THIS PROVES: that deterministic modular arbitration over the calibrated
component outputs yields the target confusion matrix, and that the WG-5 false
positive is removed BY CONSTRUCTION (routing) rather than by weakening negative
grounding.

WHAT THIS DOES NOT PROVE: robustness of the components themselves under resampling.
That is a property of WG-3A/WG-4A/WG-4B, already measured in their own tasks, and
is not re-opened here.

## SUBSTRATE

- Verdict unit: the WG-4A COMMITMENT (finest available granularity).
- Parent substrate: frozen WG-3A extraction, 236 parents across the three articles.
- WG-4B judges at PARENT granularity and emits a proof object per parent.

## ROUTER (deterministic, field-driven only)

For each WG-4A commitment `c` inside parent `P` of article `t`:

    b = WG4B[t][P]

    IF b.IN_SCOPE == "YES"
       AND b.NEGATIVE == "YES"
       AND c.COMMITMENT_TYPE == "SOURCE_META":
         CLASS = NEGATIVE_SOURCE
         OWNER = WG-4B
    ELSE:
         CLASS = ORDINARY
         OWNER = WG-4A

Routing reads ONLY declared component fields. It does not read prose, does not
pattern-match spans, and does not consult gold.

## ARBITRATION

OWNER = WG-4A:
    verdict = c.SUPPORT_STATUS   (verbatim, no transformation)

OWNER = WG-4B: verdict derived from the PROOF OBJECT, not from WG-4B's own
verdict string:
    PROOF_TYPE == "EXPLICIT"          -> SUPPORTED
    PROOF_TYPE == "BOUNDED_ABSENCE"   -> SUPPORTED
    PROOF_TYPE == "NONE"              -> UNSUPPORTED
    PROOF_TYPE anything else          -> ARBITRATION_ERROR (fail loud)

An assertion records whether the proof-derived verdict agrees with WG-4B's own
VERDICT field. Disagreement is reported, never silently resolved.

## HARD CONSTRAINTS

1. A generic/ordinary verdict may NEVER override a valid WG-4B proof. Guaranteed
   structurally: routing is exclusive, so only one owner decides any commitment.
2. `EXTRACTION_ANCHOR_WAS_EMPTY` is NOT an input to routing or to verdict
   derivation. An empty anchor alone neither proves nor disproves a negative
   source claim. The code asserts this field is never read for a decision.
3. No new all-purpose prompt is written.

## PRE-REGISTERED EDGE CASE

If a parent has `NEGATIVE == "YES"` but WG-4A emitted NO commitment of type
SOURCE_META inside it, the negative claim has no routing target. Fallback, fixed
in advance:

  - exactly ONE commitment in the parent -> route that commitment to WG-4B
  - MORE THAN ONE and none SOURCE_META  -> leave all with WG-4A and record the
    commitment as ARBITRATION_UNROUTED, reported as a coverage gap

## SCORING

Gold -> parent mapping is copied VERBATIM from `score_wg4.py`, itself carried
verbatim from WG-3, so it cannot be retuned. Gold V2.1 is read-only.

- TP: a gold UNSUPPORTED finding whose mapped parents contain >=1 arbitrated
  UNSUPPORTED commitment
- FN: a gold UNSUPPORTED finding with none
- FP: an arbitrated UNSUPPORTED commitment in a parent claimed by no gold finding

## PRE-REGISTERED TARGETS

    TP = 8, FN = 0, FP = 0

Named controls:
    G13-04     (form1-3 / P22) -> UNSUPPORTED, proof NONE
    GR2-02     (r2 / P21)      -> UNSUPPORTED, proof NONE
    R3 control (r3 / P29)      -> SUPPORTED,   proof BOUNDED_ABSENCE

Additional required checks:
    - no commitment whose WG-4A status was INTERPRETATION is flipped to
      UNSUPPORTED by arbitration
    - the 3 owner-calibrated reclassified interpretations (G13-03, GR2-03,
      GR3-02) are not UNSUPPORTED
    - the 2 gold UNCERTAIN items are not UNSUPPORTED (so cannot become repair
      targets)

## DECISION RULE

A. MODULAR_ARBITRATION_READY   — 8/8 recall, 0 FP, R3 control retained
B. ARBITRATION_RECALL_REGRESSION — any FN
C. ARBITRATION_PRECISION_GAP     — FP >= 1

WG-5's FP=1 tolerance is explicitly NOT inherited. Eliminating that specific
false positive is the purpose of WG-6A. If the decision is not A, WG-6B does not run.
