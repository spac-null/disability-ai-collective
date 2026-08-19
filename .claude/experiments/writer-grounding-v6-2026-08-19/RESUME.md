# WG-6 — PAUSED MID-TASK (session limit). RESUME HERE.

Paused 2026-08-19 by owner request ("lets pause for a while, due limit session").
Nothing was pushed. Nothing was deployed. Article Form untouched. Gold V2.1 untouched.

## STATUS

WG-6A — **COMPLETE. DECISION A — MODULAR_ARBITRATION_READY.**
WG-6B — **PARTIAL.** Repair + application + Form/voice + closure check done.
         Post-repair full re-audit NOT run.

No overall WG-6 decision has been made yet, because the WG-6B success gate
requires the post-repair re-audit numbers.

## WG-6A RESULT (final, scored, preserved)

Method: REUSE / RESCORE, no new model calls. WG-4A and WG-4B ran on the SAME
frozen WG-3A extraction (236 parents, verified identical hashes), so the
arbitration layer is pure deterministic code over existing artefacts.

    TP 8   FP 0   FN 0   recall 1.000   precision 1.000

    G13-04     form1-3/P22  UNSUPPORTED  owner WG-4B  proof NONE
    GR2-02     r2/P21       UNSUPPORTED  owner WG-4B  proof NONE
    R3 control r3/P29       SUPPORTED    owner WG-4B  proof BOUNDED_ABSENCE

Router: 8 negative source claims routed to WG-4B, 257 commitments to WG-4A,
0 unrouted, 0 proof/verdict disagreements, 0 forbidden fields read
(EXTRACTION_ANCHOR_WAS_EMPTY never used for a decision).

The WG-5 false positive is eliminated BY CONSTRUCTION (exclusive routing), not by
weakening negative grounding. WG-4B's rule is unchanged and still owns its class.

Gold UNCERTAIN both non-UNSUPPORTED, so neither can become a repair target.
Reclassified interpretations G13-03 / GR2-03 / GR3-02: gold-disjoint check PASS 3/3.

## WG-6B — WHAT IS DONE

Repair: 3 blind fresh-context calls (one per article), prompts persisted and
hashed BEFORE the calls. 8 patches, one per finding. No retries, no candidates.

Application: fail-closed, 0 rejections, 0 ambiguous, 0 overlapping,
boundary assertion 3/3, independent reconstruction match 3/3,
paragraph delta 0 on all three, containment 8/8 (every OLD_TEXT inside its
finding's PARENT_SENTENCE).

Article Form: preserved 3/3, zero dimensions changed on any article.
Arrival paragraph byte-identical 3/3, never patched.

Voice: every voice-token count identical before/after on all three articles.
The checker's `voice_regression=True` on r2 is an artifact — it flags any voice
token present in NEW_TEXT regardless of provenance; "here" occurs once in
OLD_TEXT and once in NEW_TEXT (carried through, not introduced).

R3 CONTROL: byte-identical, received no patch. Containment proof survives repair.

R2 UNDER-CLEARANCE (the WG-5 defect): FIXED. WG-5 left "a name that arrives
without preparation" behind. WG-6B's repair removed the whole carrier:
  "That is the texture of moving through it — a sequence of rooms, each producing a name."
Closure check on that sentence: CLOSED, no HUMAN_STATE residual.
Root cause of the WG-5 defect is now identified: WG-5's repair prompt passed
SENTENCE_CONTEXT = the offending span alone, so repair never saw the residual
carrier. WG-6B passes the real parent sentence plus an explicit closure duty.

Closure verdicts: 6 CLOSED, 1 UNDER_CLEARED (FORM1-3-P3), 1 OVER_EDITED (R2-P2).
Both non-CLOSED verdicts are UNADJUDICATED pending the post-repair re-audit.
Preliminary evidence on each (do not treat as concluded):
  * R2-P2 OVER_EDITED/GRAMMAR_BROKEN: the patch removed exactly
    " not because the review places them above the rest but simply" — the target
    claim plus its correlative. The main clause survives. The pre-patch sentence
    had NO finite main verb either (an authorial fragment), and the finite-verb
    inventory is unchanged. The checker's stated rationale ("excised the main
    clause") is factually wrong about what was removed. Only collateral: the
    intensifier "simply".
  * FORM1-3-P3 UNDER_CLEARED: checker calls retained "a person who did not know
    the work existed" a HUMAN_STATE residual. Gold V2.1's own min_correction for
    G13-02 is "Remove the invented interval; keep only source-supported
    unfamiliarity" — i.e. gold says the retained unfamiliarity IS supported. The
    same checker called the equivalent R3-P1 sentence CLOSED, so it is internally
    inconsistent between the two. The authoritative arbiter is the calibrated
    post-repair detector, which has NOT yet been run.

## EXACT NEXT STEPS TO RESUME

Everything is rendered, hashed and ready. Prompts are frozen; re-running them is
reproducible.

1. Run 3 blind extraction calls over the PATCHED articles. Prompts already
   persisted (system prompt is byte-identical to the frozen WG-3A file,
   sha 45586e5f37b881cf...):
     WG-6B/postaudit/{form1-3,r2,r3}-extract-{system,user}.txt
   Write outputs to WG-6B/postaudit/{tag}-extract-raw.json
   (These 3 calls were launched and then stopped at the pause; no partial output
   was written, so the stage is clean.)

2. Render the verdict prompts (reads WG-4A/WG-4B system prompts VERBATIM from the
   frozen WG-4 files, sha 7a4937c9... and 3e4739d2...):
     python3 WG-6B/postaudit/render_verdict_prompts.py

3. Run 6 blind calls: {tag}-wg4a and {tag}-wg4b per article, outputs to
   WG-6B/postaudit/{tag}-{wg4a,wg4b}-raw.json

4. Score the post-repair re-audit (re-applies the IDENTICAL arbitration rule):
     python3 WG-6B/postaudit/score_postaudit.py
   Required: gold unsupported remaining 0, new unsupported 0, uncertain patched 0.

5. Adjudicate the two non-CLOSED closure verdicts against that result:
     python3 WG-6B/closure/adjudicate.py

6. Write WG6-RESULTS.json, run ./make_checksums.sh, commit (do NOT push).

## GUARDS STILL IN FORCE

Do NOT: modify Article Form, create FORM-1.4, generate an article, run Real
Article Test 2, wire production, modify _should_block, deploy, push, or start the
LEGACY PROMPT / RULE INVENTORY (WORK.md §5c, still DEFERRED).
Do NOT run the final end-to-end shadow replay in this task.
