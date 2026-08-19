# WG-6 — COMPLETE

Superseded `RESUME.md` and `WG6-INTERIM-RESULTS.json` (the mid-task pause records),
both removed. Authoritative result: `WG6-RESULTS.json`.

    WG-6A   A — MODULAR_ARBITRATION_READY
    WG-6B   A — REPAIR_CLOSURE_READY
    OVERALL A — WRITER_GROUNDING_COMPONENTS_READY_FOR_FINAL_SHADOW_REPLAY

Not pushed. Not deployed. Article Form, FORM-1.3 and Gold V2.1 unmodified.
No article generated. Final shadow replay NOT run.

## Layout

    WG-6A/PRE-REGISTRATION.md     routing rule, fixed before scoring
    WG-6A/arbitrate.py            deterministic router + arbitration
    WG-6A/ARBITRATION.json        every arbitrated commitment, with owner and proof
    WG-6A/score_wg6a.py           scorer, gold mapping verbatim from WG-3/WG-4
    WG-6A/WG6A-SCORING.json       TP 8 / FP 0 / FN 0, controls, integrity checks
    WG-6A/inputs/                 frozen component outputs + gold + source + articles

    WG-6B/render_repair_prompt.py the repair contract (semantic closure)
    WG-6B/{tag}-{system,user}.txt persisted repair prompts, hashed pre-call
    WG-6B/{tag}-patches-raw.json  the 8 patches as returned
    WG-6B/apply_patches.py        fail-closed applier + containment assertion
    WG-6B/APPLICATION-REPORT.json application evidence and hashes
    WG-6B/{tag}-patched.md         patched articles
    WG-6B/{tag}.diff               sentence-level diffs
    WG-6B/verify.py                Article Form + voice + controls
    WG-6B/closure/                 per-patch semantic closure check + adjudication
    WG-6B/postaudit/               full post-repair re-audit, identical instrument
    WG-6B/postaudit/EXECUTION-NOTES.md  instrument hashes, the one infra re-run

## The two things that did NOT come from the charter

WG6-N1 — ARBITRATION_UNROUTED coverage gap. The router consults WG-4B's proof only
when WG-4A also typed a commitment SOURCE_META (or the parent has one commitment).
form1-3/P83 post-repair: WG-4B said NEGATIVE / PROOF NONE / UNSUPPORTED, WG-4A gave
two commitments typed OTHER and HUMAN_STATE, so the negative verdict was suppressed.
Benign against Gold V2.1 here, but a genuine recall hole. Fix and re-score BEFORE
the final replay.

WG6-N2 — Detector resampling variance. The identical frozen instrument, on
byte-identical untouched sentences, produced 2 UNSUPPORTED findings it had called
INTERPRETATION pre-repair, and changed extraction granularity (81->86, 74->72).
So a single post-repair count cannot serve as a literal absolute gate.

## Next step

Close WG6-N1, re-score WG-6A to prove nothing regresses, then ONE final untouched
end-to-end shadow replay. Do NOT start the LEGACY PROMPT / RULE INVENTORY — still
DEFERRED per WORK.md 5c.
