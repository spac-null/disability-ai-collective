# WG-6N — WG6-N1 AND WG6-N2 CLOSED

Continuation under WG-6. No historical WG-6 evidence was modified: WG-6A/,
WG-6B/ and WG6-RESULTS.json are byte-identical to commit 91e00d6, re-verified
by SHA256SUMS.txt in the parent directory.

    WG6-N1  A — ROUTING_GAP_CLOSED
    WG6-N2  A — VERIFICATION_SEMANTICS_READY

No model calls. Both conditions re-derived from frozen, checksum-verified
component outputs by deterministic code. Not pushed, not deployed.

## N1 — the routing fix

Routing authority for a negative meta-source claim is now WG-4B's own
IN_SCOPE + NEGATIVE classification. WG-4A's COMMITMENT_TYPE is no longer a
prerequisite. One new path was added and nothing existing was touched:

    P3  negative parent, no SOURCE_META carrier, != 1 commitment
        -> emit a synthesised unit <PID>-NEG carrying WG-4B's own
           NEGATIVE_CLAIM verbatim, owned by WG-4B, verdict from PROOF_TYPE
        -> every existing WG-4A commitment is KEPT, unchanged, owned by WG-4A

Nothing is reassigned, so an independent commitment sharing the parent sentence
survives. `ARBITRATION_UNROUTED` is now unreachable and asserted so.

Re-score, corrected router, both frozen conditions:

    CONDITION A (original, pre-repair)
      TP 8  FP 0  FN 0   recall 1.000  precision 1.000
      unsupported set byte-identical to frozen WG-6A — appeared [], disappeared []
      G13-04 form1-3/P22  UNSUPPORTED / NONE            PASS
      GR2-02 r2/P21       UNSUPPORTED / NONE            PASS
      R3     r3/P29       SUPPORTED / BOUNDED_ABSENCE   PASS
      unrouted 0   disagreements 0   synthesised 0   forbidden fields read []

    CONDITION B (post-repair)
      unrouted 0   suppressed 0
      post-repair UNSUPPORTED 2 -> 3
      recovered: form1-3/P83/P83-NEG, the finding the old router suppressed

P3 fires on zero pre-repair parents, which is why condition A cannot move: all
8 calibrated WG-4B routes live in single-commitment parents. That is verified,
not assumed.

### P83, routed not adjudicated away

    P83-NEG  WG-4B  proof NONE -> UNSUPPORTED   (new unit, was suppressed)
    P83-C1   WG-4A  OTHER        INTERPRETATION (kept)
    P83-C2   WG-4A  HUMAN_STATE  SUPPORTED      (kept)

P83-C2 — "The work was previously unknown to the visitor", anchored on the
source's "you've never heard of" — is exactly the independent commitment that
parent-level reassignment would have swallowed. It keeps its own verdict.

## N2 — verification semantics

Byte-locality is measured at SENTENCE granularity. r2 line 13 proves why: that
paragraph contains both a patched sentence (Hasegawa) and the untouched
sentence carrying the finding.

The C/D boundary was fixed before adjudication. ADJUDICATED_STATUS comes from
the frozen source using Gold's own four values; UNSUPPORTED blocks, everything
else is recorded. UNCERTAIN sits on the D side for one reason only: the
existing gates already forbid UNCERTAIN items from becoming repair targets.

    REPAIR_INTRODUCED                    0
    REPAIR_RESIDUAL                      0
    PREEXISTING_GENUINE_NEWLY_DETECTED   1     <- BLOCKS
    DETECTOR_FALSE_POSITIVE / VARIANCE   2

    form1-3/P73-C2  "the visitor's afternoon"   UNSUPPORTED    C  BLOCKS
    form1-3/P83-NEG "The review's discovery is" INTERPRETATION D
    r2/P72-C2       "was found after 2013"      UNCERTAIN      D

## The result that matters, stated precisely

REPAIR INTRODUCED NOTHING. That is proven, and it is a narrower claim than
"no new unsupported".

The WG-6B repaired FORM-1.3 is NOT grounding-clean. "The word travels easily
between the visitor's afternoon and the artist's life" invents a duration the
source never gives — the source contains neither 'afternoon' nor 'hour' and
frames the visit as the whole festival. Gold V2.1 rates three identical
inventions UNSUPPORTED (G13-02 'an hour ago', GR3-01 'an hour earlier',
GR3-03 'in August'), and WG-6B's repair removed 'an hour ago' from this very
article. The same defect two paragraphs earlier survived only because no gold
finding named it.

Repair did not cause it. It still blocks publication. Those are different
statements and the report keeps them apart.

## Consequence for the final shadow replay

Both gates pass, so the replay is authorised. But the "afternoon" claim sits in
FORM-1.3's original text and the replay starts from that original. Its fate
turns on whether the pre-repair detector flags it: if it does, it becomes a
repair target and closes; if it repeats the pre-repair WG-6 behaviour and calls
it INTERPRETATION, it will resurface post-repair as category C and fail gate 16.
Recorded here in advance so the outcome cannot be reinterpreted afterwards.

## Layout

    PRE-REGISTRATION.md    routing rule + verification rule, fixed before running
    arbitrate_v2.py        corrected router (P1/P2 unchanged, P3 added)
    rescore_n1.py          re-score of both frozen conditions
    N1-RESCORE.json        matrices, controls, regression check, recovered findings
    N2-ADJUDICATION.json   independent source adjudication, with counter-arguments
    classify_n2.py         byte-locality + pre-registered category mapping
    N2-CLASSIFICATION.json the four counts, kept separate
