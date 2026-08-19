# ABORTED_BY_OWNER — DIMINISHING_RETURNS_STOP

This evidence root holds the SETUP ONLY for a final writer-grounding shadow
replay that was stopped by the owner before any model stage executed.

    STATUS            ABORTED_BY_OWNER — DIMINISHING_RETURNS_STOP
    DATE              2026-08-19
    MODEL CALLS MADE  0
    MODEL OUTPUTS     NONE
    ARTICLES CHANGED  NONE
    SCORED AGAINST GOLD  NO

This is NOT an experiment failure. No stage ran, so nothing was measured, and
no result — positive or negative — may be inferred from this directory.

## What actually happened

The setup completed through prompt rendering for stage 1 only. Three fresh
blind extraction subagents were launched over the ORIGINAL FORM-1.3 / R2 / R3
articles and were stopped by the owner while still reading their prompt files.
None wrote an output file. No verdict, repair, or post-repair call was ever
launched.

## What is preserved here, and what it is worth

Preserved, complete and checksummed:

    PRE-REGISTRATION.md   the full pipeline, routing rule, verification rule and
                          success gates, fixed before any call
    inputs/               the frozen articles, source, gold and the four frozen
                          system prompts, hash-verified against WG-6's records
    lib/                  the deterministic stages, ready to run
    pre/                  the three rendered stage-1 prompts with their hashes

NOT preserved, because it never existed: any extraction, verdict, repair,
patched article, arbitration, score, or verification output.

Missing outputs must NOT be reconstructed, simulated, or completed later. If
this replay is ever revived it starts from stage 1 with fresh calls.

## Owner stop decision, recorded verbatim in intent

Repeated stochastic audits of the same Edinburgh prose will not be required to
produce zero newly discovered propositions forever. The finite Gold V2.1
calibration and the completed WG experiments have served their purpose.

Writer Grounding is frozen as:

    SHADOW-CALIBRATED CANDIDATE
    NOT PRODUCTION-VALIDATED
    NOT TRANSFER-VALIDATED

### Known limitation, accepted

Source-relative LLM detection is stochastic. A finite gold benchmark cannot
prove that every possible unsupported proposition in an article has been
enumerated forever. WG-6N measured this directly: the identical frozen
instrument, re-run on byte-identical untouched prose, changed extraction
granularity and moved verdicts, surfacing propositions the earlier pass had not
isolated. That is a property of the method, not a defect to be ground out by
more replays of one case.

## The last completed evidence checkpoint

    a1f2889   evidence: close writer grounding V6 routing and verification gaps

WG6-N1 and WG6-N2 are CLOSED. Their results stand on their own and do not
depend on this replay:

    WG6-N1  A — ROUTING_GAP_CLOSED
            corrected router, original condition TP 8 / FP 0 / FN 0,
            unsupported set byte-identical to frozen WG-6A, unrouted 0
    WG6-N2  A — VERIFICATION_SEMANTICS_READY
            repair introduced 0, repair residual 0,
            preexisting genuine newly detected 1, detector variance 2

## Standing rules

    Do NOT create WG-7.
    Do NOT create another Edinburgh grounding experiment.
    Do NOT run another FORM version.
    Reopen Edinburgh Writer Grounding ONLY if a later transfer or production
    test reveals a reproducible failure that maps back to this architecture.

Next roadmap task: LEGACY PROMPT / RULE INVENTORY (WORK.md 5c).
After that: Real Article Test 2 / transfer validation.
Neither was started in this session.
