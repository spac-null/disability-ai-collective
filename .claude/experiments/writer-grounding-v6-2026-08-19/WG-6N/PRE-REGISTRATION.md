# WG-6N PRE-REGISTRATION — CLOSING WG6-N1 (ROUTING) AND WG6-N2 (VERIFICATION SEMANTICS)

Written and fixed BEFORE the corrected router was executed and before any
re-scoring was run. Nothing below was adjusted after seeing a confusion matrix.

WG-6N is a continuation under WG-6, not a replacement. No historical WG-6
evidence is modified. WG-6A/ARBITRATION.json, WG-6A/WG6A-SCORING.json,
WG-6B/postaudit/POSTAUDIT-SCORING.json and WG6-RESULTS.json stay byte-identical;
the corrected router writes its own outputs in this directory.

Article Form, FORM-1.3/R2/R3 and Gold V2.1 are read-only here.

## PART 1 — WG6-N1, THE ROUTING DEFECT

### Observed

WG-6B post-repair, form1-3/P83:

    WG-4B  IN_SCOPE YES / NEGATIVE YES / PROOF_TYPE NONE / VERDICT UNSUPPORTED
    WG-4A  two commitments, typed OTHER and HUMAN_STATE, neither SOURCE_META

The WG-6A router consults WG-4B only when WG-4A supplies a SOURCE_META
commitment, or when the parent holds exactly one commitment. P83 satisfied
neither, so WG-4B's UNSUPPORTED was recorded as ARBITRATION_UNROUTED and
suppressed. A generic WG-4A label decided a negative meta-source claim.

### Corrected invariant (fixed here, not tunable)

    IF WG-4B says IN_SCOPE == YES AND NEGATIVE == YES for a parent
    proposition, WG-4B OWNS the negative meta-source verdict for that
    proposition, regardless of any WG-4A COMMITMENT_TYPE.

WG-4A SOURCE_META is NOT a prerequisite. Proof semantics are unchanged and
still WG-4B's own:

    EXPLICIT         -> SUPPORTED
    BOUNDED_ABSENCE  -> SUPPORTED
    NONE             -> UNSUPPORTED
    anything else    -> ARBITRATION_ERROR (fail loud)

No WG-4A verdict may override a valid WG-4B proof.

### The carrier — how ownership attaches without hiding anything

WG-4B judges at PARENT granularity and names exactly one NEGATIVE_CLAIM per
parent. WG-4A decomposes the same parent into commitments. Ownership therefore
needs a carrier. Fixed in advance, by declared fields only:

    P1  is_neg AND >=1 SOURCE_META commitment
        -> those SOURCE_META commitments carry WG-4B's verdict.
           Every other commitment in the parent stays with WG-4A.
           (unchanged WG-6A behaviour)

    P2  is_neg AND no SOURCE_META AND exactly 1 commitment
        -> that commitment carries WG-4B's verdict.
           Parent == commitment, so nothing else exists to hide.
           (unchanged WG-6A behaviour)

    P3  is_neg AND no SOURCE_META AND != 1 commitment          [NEW]
        -> emit a SYNTHESISED arbitration unit `<PID>-NEG`, anchored to the
           parent EXACT_SPAN and carrying WG-4B's own NEGATIVE_CLAIM verbatim
           as its proposition, owned by WG-4B, verdict from PROOF_TYPE.
           EVERY existing WG-4A commitment in that parent is retained,
           unchanged, owned by WG-4A, with its own SUPPORT_STATUS.

P3 is the whole fix. It routes on WG-4B's own semantic classification, adds the
suppressed verdict as its own unit, and reassigns nothing — so an independent
commitment sharing the parent sentence (the P83-C2 case: "The work was
previously unknown to the visitor", SUPPORTED) keeps its WG-4A verdict.
Nothing is deleted, nothing is relabelled, nothing is adjudicated away.

`ARBITRATION_UNROUTED` becomes unreachable. That is asserted, not hoped for.

The synthesised unit is not an invented claim. It is WG-4B's declared
NEGATIVE_CLAIM string, promoted to a first-class arbitration unit because
WG-4B is a first-class detector.

### What routing may read

Declared component fields only: WG-4B IN_SCOPE / NEGATIVE / PROOF_TYPE /
NEGATIVE_CLAIM, WG-4A COMMITMENT_TYPE / SUPPORT_STATUS, WG-3A EXACT_SPAN.
`EXTRACTION_ANCHOR_WAS_EMPTY` remains a forbidden decision input and the guard
asserting so is carried over verbatim. No prose pattern-matching. No model
call. No gold.

### N1 re-score — pre-registered targets

Run the corrected router over BOTH frozen conditions, no new model calls.

    (A) original WG-6A condition, pre-repair components
        REQUIRED, or N1 fails:
            TP 8 / FP 0 / FN 0, recall 1.000, precision 1.000
            G13-04     form1-3/P22  UNSUPPORTED, proof NONE
            GR2-02     r2/P21       UNSUPPORTED, proof NONE
            R3 control r3/P29       SUPPORTED,   proof BOUNDED_ABSENCE
            unrouted negatives 0, proof/verdict disagreements 0

    (B) WG-6B post-repair condition
            report every finding the old router suppressed, P83 included.
            P83 must be ROUTED, not adjudicated away. Whatever verdict its
            proof yields is recorded as-is and handed to Part 2.

### N1 decision rule

    A. ROUTING_GAP_CLOSED           unrouted 0, suppressed 0, (A) matrix intact
    B. ROUTING_STILL_INCOMPLETE     anything else -> STOP, no final replay

## PART 2 — WG6-N2, VERIFICATION SEMANTICS

### The problem

The identical frozen instrument, re-run on the patched articles, changed
extraction granularity (form1-3 81->86, r3 74->72) and moved verdicts on
byte-identical untouched prose. So a raw POST_REPAIR_UNSUPPORTED_COUNT cannot
answer "did repair introduce a grounding failure?". It conflates repair quality
with detector resampling.

This is NOT solved by weakening grounding, and NOT solved by excusing a finding
because its bytes are unchanged.

### Byte-locality record — required for every post-repair UNSUPPORTED finding

    EXACT_SPAN
    CONTAINING_SENTENCE                      (sentence, not paragraph)
    OVERLAPS_CHANGED_BYTES        YES/NO     (span vs applied patch spans)
    CONTAINING_SENTENCE_PATCHED   YES/NO
    DEPENDS_SEMANTICALLY_ON_PATCH YES/NO
    PRE_REPAIR_TEXT_BYTE_IDENTICAL YES/NO
    PRE_REPAIR_VERDICT                       (same instrument, if the span existed)
    POST_REPAIR_VERDICT
    ADJUDICATED_STATUS                       (independent, against frozen source)

Byte-locality is measured at SENTENCE granularity. A paragraph may contain both
a patched sentence and an untouched one; paragraph-level comparison would
wrongly mark the untouched sentence as repair-adjacent.

### Causal categories

    A. REPAIR_RESIDUAL
       unsupported commitment survives within, or is semantically carried by,
       a patched sentence/span.

    B. REPAIR_INTRODUCED
       did not exist before and depends on changed text.

    C. PREEXISTING_GENUINE_NEWLY_DETECTED
       entirely in byte-identical prose untouched by repair, AND independent
       source adjudication finds it genuinely unsupported.
       BLOCKS. Repair did not cause it; the article is still not publication-safe.

    D. DETECTOR_FALSE_POSITIVE / VARIANCE
       in unchanged prose, AND independent source adjudication finds it
       grounded, legitimate interpretation, or genuinely UNCERTAIN.
       Recorded, does not block.

### The C/D boundary — fixed in advance

Independent adjudication assigns ADJUDICATED_STATUS from the frozen source
snapshot, using the same four-valued taxonomy Gold V2.1 uses:

    ADJUDICATED_STATUS == UNSUPPORTED                      -> C, BLOCKS
    ADJUDICATED_STATUS in {SUPPORTED, INTERPRETATION, UNCERTAIN} -> D, recorded

UNCERTAIN sits on the D side for one pre-registered reason only: the WG-6
success gates forbid UNCERTAIN items from becoming repair targets. Routing an
adjudicated-UNCERTAIN item into repair would violate a gate that already
exists. It is NOT called grounded, and the report must say UNCERTAIN, not
"grounded" and not "false positive".

Gold V2.1 enumerates spans only for its 8 unsupported, 3 reclassified and 2
uncertain items; it does not enumerate its 44 supported or 41 interpretation
propositions. Gold silence on a span is therefore NOT evidence that gold judged
it grounded, and may not be used as such. Adjudication goes to the source.

### N2 success condition

N2 is ready when the verifier reports these four counts SEPARATELY, each with
byte-locality evidence:

    REPAIR_INTRODUCED
    REPAIR_RESIDUAL
    PREEXISTING_GENUINE_NEWLY_DETECTED
    DETECTOR_FALSE_POSITIVE / VARIANCE

An article is grounding-clean only if the first three are all zero. Readiness
of the verifier and cleanliness of the article are separate results and are
reported separately.

Forbidden output: "new unsupported = 0" when what is known is only "repair
introduced none".

### N2 decision rule

    A. VERIFICATION_SEMANTICS_READY     all four counts derivable with evidence
    B. VERIFICATION_STILL_AMBIGUOUS     any finding not classifiable -> STOP

## SCOPE LIMIT

WG-6N closes two defects. It runs NO new model calls: both conditions are
re-derived from frozen, checksum-verified component outputs, because the
corrected router is pure deterministic code over artefacts that already exist.
It does not repair anything, does not regenerate an article, and does not
authorise the final replay by itself.
