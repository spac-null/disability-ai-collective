# FINAL WRITER-GROUNDING SHADOW REPLAY — PRE-REGISTRATION

Persisted BEFORE any model call. This is the final calibration replay. No
tuning after it begins. Nothing below may be edited once the first call runs.

Date 2026-08-19. Execution mode LOCAL_CLAUDE_SUBSCRIPTION, claude-opus-5[1m],
fresh-context blind subagent calls — the same identity and mode WG-6 recorded.

## WHAT IS UNDER TEST

The complete modular Writer Grounding pipeline, end to end, on the ORIGINAL
frozen articles. Not the WG-6B repaired copies. Every component is frozen and
every system prompt is read verbatim from its frozen file, never retyped.

    inputs/form1-3-article.md          9a78d9a4c28f4a89...  (FORM-1.3, original)
    inputs/form-1.3-r2-article.md      5ea20461cc09484d...  (R2, original)
    inputs/form-1.3-r3-article.md      27b1038c80af9890...  (R3, original)
    inputs/source-snapshot.txt         fee0a03b8bb0c56b...
    inputs/WG3A-EXTRACTION-SYSTEM-FROZEN.txt  45586e5f37b881cf...
    inputs/WG4A-DECOMP-SYSTEM-FROZEN.txt      7a4937c9ef8dadf9...
    inputs/WG4B-NEGPROOF-SYSTEM-FROZEN.txt    3e4739d24ea15b4f...
    inputs/WG6B-REPAIR-SYSTEM-FROZEN.txt      7914f9898a852684...
    inputs/gold-ledger-V2.1-FROZEN.json       8bb6eb3655386ab2...

The three component system hashes match the values WG-6B recorded. The repair
system prompt is byte-identical to WG-6B/form1-3-system.txt, proven by diff.

## PIPELINE — FIXED

    ORIGINAL ARTICLE
    -> WG-3A FAITHFUL EXTRACTION                         3 calls
    -> WG-4A COMMITMENT DECOMPOSITION / VERDICT          3 calls
    -> WG-4B NEGATIVE SOURCE PROOF                       3 calls
    -> CORRECTED DETERMINISTIC MODULAR ARBITRATION       code
    -> UNSUPPORTED FINDINGS
    -> WG-6B SEMANTIC-CLOSURE PATCH REPAIR               3 calls
    -> FAIL-CLOSED DETERMINISTIC PATCH APPLICATION       code
    -> POST-REPAIR WG-3A                                 3 calls
    -> POST-REPAIR WG-4A                                 3 calls
    -> POST-REPAIR WG-4B                                 3 calls
    -> CORRECTED MODULAR ARBITRATION                     code
    -> N2 CAUSAL VERIFICATION                            code + adjudication
    -> ARTICLE FORM / VOICE VERIFICATION                 code
    -> FREEZE OUTPUTS
    -> ONLY THEN SCORE AGAINST GOLD V2.1

21 model calls. No monolithic WG-5 verdict prompt anywhere.

## GOLD ISOLATION

Gold V2.1 enters NO model prompt at any stage. Repair receives detector
findings only — no gold ids, no gold verdicts, no gold spans. Gold is opened
for the first time after all outputs are frozen, by the scorer alone.

Every subagent is instructed to read exactly one prompt file and write exactly
one output file, and to read nothing else in the repository.

## ROUTING RULE — from WG-6N, unchanged

lib/arbitrate_v2.py is a byte-identical copy of the router whose correction
closed WG6-N1 (sha 18a7194bad571d37...). Authority for a negative meta-source
claim is WG-4B's own IN_SCOPE + NEGATIVE. Proof semantics: EXPLICIT ->
SUPPORTED, BOUNDED_ABSENCE -> SUPPORTED, NONE -> UNSUPPORTED. P3 emits a
synthesised carrier and reassigns nothing. EXTRACTION_ANCHOR_WAS_EMPTY stays a
forbidden decision input.

### One adaptation, declared in advance

build_repair_inputs.py maps COMMITMENT_TYPE to FAILURE_CLASS through a fixed
dict that predates the P3 path and has no entry for the synthesised type. It
is extended, before running, by:

    NEGATIVE_SOURCE_CLAIM -> UNPROVEN_NEGATIVE_SOURCE_CLAIM
    any other unknown type -> "UNSUPPORTED_" + the declared type

This only prevents a crash on a type the old dict never saw. It changes no
verdict and no routing decision.

## VERIFICATION RULE — from WG-6N, unchanged

Sentence-level byte-locality. Categories A REPAIR_RESIDUAL, B REPAIR_INTRODUCED,
C PREEXISTING_GENUINE_NEWLY_DETECTED, D DETECTOR_FALSE_POSITIVE/VARIANCE.
ADJUDICATED_STATUS == UNSUPPORTED -> C, blocks. SUPPORTED / INTERPRETATION /
UNCERTAIN -> D, recorded. The four counts are always reported separately.
"REPAIR_INTRODUCED = 0" may never be written as "no new unsupported".

## EXECUTION DISCIPLINE

One successful execution per model stage. No candidate selection. No retries
after a successful output. If an infrastructure failure produces NO usable
output, that is recorded explicitly and the same byte-identical prompt may be
relaunched once, recorded as an infrastructure retry, never as a candidate.
Prompt and config are never modified between attempts.

## SUCCESS GATES

### Gate 1 — pre-repair detector, scored only after freezing

    TP = 8 REQUIRED
    FN = 0 REQUIRED
    FP = 0 preferred; if FP > 0, adjudicate independently BEFORE repair
    legitimate INTERPRETATION must not become a repair target
    UNCERTAIN must not become a repair target
    Missing any of the 8 -> FINAL REPLAY FAILS, do not repair

### Gate 2 — repair

    gold V2.1 UNSUPPORTED remaining          0
    REPAIR_RESIDUAL                          0
    REPAIR_INTRODUCED                        0
    PREEXISTING_GENUINE_NEWLY_DETECTED       0
    legitimate INTERPRETATION edited         0
    UNCERTAIN edited                         0

### Gate 3 — structure / voice, all three articles

    festival-as-speaker/possessor            0
    discovery ownership failure              0
    countervoice before arrival              YES
    arrival final                            YES
    paragraphs after arrival                 0
    post-arrival restatement                 none
    attribution-bookkeeping leakage          0
    agency/consent attractor                 0
    VOICE / PERSON                           stable
    arrival byte-identical unless directly targeted by an unsupported finding
    R3 bounded-absence control unpatched and correct
    R2 visitor-preparation residual absent

## DECISION

    A. WRITER_GROUNDING_CALIBRATED
    B. FINAL_REPLAY_DETECTOR_FAILURE
    C. FINAL_REPLAY_REPAIR_FAILURE
    D. FINAL_REPLAY_VERIFICATION_OR_STRUCTURE_FAILURE

## RECORDED IN ADVANCE — a known live risk

WG-6N adjudicated "The word travels easily between the visitor's afternoon and
the artist's life" (FORM-1.3, original text, untouched by WG-6B repair) as
GENUINELY UNSUPPORTED: the source contains neither 'afternoon' nor 'hour' and
frames the visit as the whole festival. Gold V2.1 does not name it, so it is
not one of the 8.

Its fate here is binary and is written down before the run so it cannot be
reinterpreted afterwards:

  * pre-repair detector flags it -> it becomes a repair target and closes.
    It will score as an FP against gold, and independent adjudication under
    Gate 1 must confirm it is genuine rather than discard it.
  * pre-repair detector calls it INTERPRETATION -> it is not repaired, and if
    the post-repair pass then flags it, it is category C and Gate 2 FAILS.

Neither outcome may be reclassified after the fact.
