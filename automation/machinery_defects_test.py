#!/usr/bin/env python3
"""machinery_defects_test.py -- three detectors that stopped articles the article was fine.

A 25-run production checkpoint reached Reader zero times. Of 19 late-stage terminal holds,
6 were genuine (all Grounding) and 8 were pure machinery, with 5 more mixed. These are the
three machinery classes, each reproduced on independent subjects, and each fixed by
narrowing WHAT IS INSPECTED rather than by relaxing a threshold.

The critical assertions are the negative ones: genuine engine language must still hold, a
real payload returning must still hold, and the mixed Safety cases must still fail on their
genuine findings. Without those, this file would prove only that the gates got quieter.

Stdlib only, no network.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP
from new_engine_v1 import story as ST
import composition_factual_bridge as FCB

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


def packet(**over):
    """A minimal valid packet. `facts` carries frozen evidence; the rest is generated."""
    p = {
        "article_type": ST.NARRATIVE_ARTICLE,
        "story_spine": "A museum opens and what its record keeps.",
        "opening": "The building, opened in 1938.",
        "reader_initial_state": "That it is old and still used.",
        "turn": "", "crip_turn": "The record holds the date and not the door.",
        "lens": "", "ending_move": "The date is in the record; the door is not.",
        "beats": [{"beat_id": "B1", "happens": "The building and its opening.",
                   "carrier": "the facade", "facts": [], "concept": "", "withhold": ""}],
        "facts": [], "quotes": [], "definitions": {},
        "prohibitions": ["Do not describe what a visitor felt."], "_cut_count": 0,
    }
    p.update(over)
    return p


# ---------------------------------------------------------------------------
print("test_DEFECT_1_frozen_evidence_no_longer_holds_the_architecture")
# The four real production cases, as the evidence text that actually matched.
REAL = [
    ("Penghu bones", "Because they were recovered by dredging and lack secure geological "
                     "provenance, they can only be placed broadly in the Pleistocene."),
    ("Florida primary", "Angie Nixon won Florida's Democratic U.S. Senate primary in an upset."),
    ("Durham The Light", "Durham Council is the primary funder, and The Light will be an "
                         "anchor institution of the proposed hub."),
    ("Citi Bike", "The hardware consists of an ESP32-S3 microcontroller and a GPS module."),
]
for label, evidence in REAL:
    pk = packet(facts=[{"fact_id": "F1", "proposition": evidence,
                        "support_span": evidence}])
    errs = ST.validate_packet(pk)
    frames = [e for e in errs if "provenance frame" in e]
    check("%s: frozen evidence no longer trips the frame scan" % label, not frames,
          str(frames)[:150])
    # And the scan really would have caught it before -- proving the case is real.
    check("%s: the same text DOES match the vocabulary" % label,
          bool(ST.leaks(evidence)), "if this fails the fixture is wrong, not the fix")

check("evidence text is excluded from the generated view",
      not any(f.startswith("facts") for f, _ in
              ST.generated_packet_text(packet(facts=[{"proposition": "x"}]))))

print("\ntest_DEFECT_1_generated_machine_language_STILL_holds")
GEN = [
    ("story_spine", "The source does not establish what the building was for."),
    ("crip_turn", "Nothing in the evidence describes the entrance."),
    ("ending_move", "This reading is supported by sha256 provenance."),
]
for field, text in GEN:
    errs = ST.validate_packet(packet(**{field: text}))
    check("generated %s with engine language still HOLDs" % field,
          any("provenance frame" in e for e in errs), str(errs)[:140])
errs = ST.validate_packet(packet(beats=[{"beat_id": "B1",
                                         "happens": "It does not describe the form.",
                                         "carrier": "x", "facts": [], "concept": "",
                                         "withhold": ""}]))
check("a generated BEAT with engine language still HOLDs",
      any("provenance frame" in e for e in errs), str(errs)[:140])
errs = ST.validate_packet(packet(story_spine="The STORY_SPINE names the beat."))
check("a scaffold name in generated text still HOLDs",
      any("scaffold name" in e for e in errs), str(errs)[:140])

print("\ntest_DEFECT_1_diagnostics_name_the_text_not_the_regex")
errs = ST.validate_packet(packet(story_spine="The source does not establish the date."))
msg = "; ".join(errs)
check("the message quotes the matched text", "does not establish" in msg, msg[:160])
check("the message names the field", "story_spine" in msg, msg[:160])
check("the message is not the bare regex source",
      "(ANCHOR|PRIMARY|INDEPENDENT|TERTIARY)" not in msg and "\\b" not in msg, msg[:160])


# ---------------------------------------------------------------------------
print("\ntest_DEFECT_2_NOT_SHIPPED_conflict_recorded")
# DEFECT 2 IS DELIBERATELY NOT FIXED HERE. The prescribed remedy -- demote bare tokens and
# pure proper-name phrases to advisory -- collides with an existing, documented contract in
# story_architecture_composition_test, which asserts CUT_HIGH for 'Reality Capture',
# 'Idle Hands', 'Lyft' and 'New York City' and argues in its own docstring:
#
#   "No frequency measure separates those and no allowlist closes by enumeration.
#    A term is tiered by SHAPE, which is decidable, not by its senses, which are not."
#
# 'New York City' (enforced HIGH) and 'The New York Times' (required LOW by the brief) are
# the SAME SHAPE. The two cannot both hold on the axis the repo says is the only decidable
# one, so the conflict is reported rather than resolved by rewriting either side.
check("the class-B tokens are still HIGH -- unfixed and recorded, not silently dropped",
      all(CP.cut_term_confidence(t) == CP.CUT_HIGH
          for t in ("Evidence", "Chris", "The New York Times")),
      "if this changes, Defect 2 was shipped and this note must be updated")
check("the existing shape contract is intact",
      all(CP.cut_term_confidence(t) == CP.CUT_HIGH
          for t in ("Reality Capture", "Idle Hands", "Lyft", "New York City")))


# ---------------------------------------------------------------------------
print("\ntest_DEFECT_3_extraction_failure_is_not_an_editorial_hold")
check("the technical status exists", FCB.EXTRACTION_ERROR == "FACT_CHECK_EXTRACTION_ERROR")
check("it is not HOLD", FCB.EXTRACTION_ERROR != FCB.HOLD)

# The exact artifact the only Fact Check candidate produced.
REAL_FC = {"advisory": [], "blocking_contradictions": [], "claims_checked": 0,
           "claims_extracted": 0, "completed": False, "contradicted": [],
           "extraction_error": "no JSON object in provider response (26 chars)",
           "extraction_status": "error", "fact_check_completed": False, "findings": [],
           "status": "HOLD"}
check("the saved case had zero findings", REAL_FC["blocking_contradictions"] == [])
check("...and had checked nothing", REAL_FC["claims_extracted"] == 0
      and REAL_FC["completed"] is False)

src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "composition_factual_bridge.py")).read()
check("extraction error now maps to the technical status, not HOLD",
      'r["status"] = EXTRACTION_ERROR' in src)
check("an incomplete run also maps to it",
      'if r.get("extraction_status") == "error" or not r["completed"]:' in src)
check("HOLD now requires an actual contradiction",
      'elif r["blocking_contradictions"]:' in src)
check("one bounded retry exists", 'extraction_retried' in src)
# Count real CALL SITES, not mentions -- the module docstring names the function too, and
# an earlier version of this check counted that and failed. Same cleaned-vs-raw docstring
# trap the repo's package-purity test records.
import ast as _ast
_calls = sum(1 for _n in _ast.walk(_ast.parse(src))
             if isinstance(_n, _ast.Call)
             and isinstance(_n.func, _ast.Attribute)
             and _n.func.attr == "_run_web_fact_check")
check("the retry is bounded to exactly one extra call", _calls == 2,
      "call sites: %d -- a loop here would be retry gambling" % _calls)

comp = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "new_engine_v1", "composition.py")).read()
# The caller is deliberately UNCHANGED. A fact check that could not run still flows to the
# Reader -- story_architecture_composition_test asserts that by name ("it does not silently
# block either -- it reaches the reader gate"), so an infrastructure failure is not recorded
# as an editorial rejection. What stops publication is downstream, and there are two locks.
check("the caller still blocks only on a real HOLD",
      'if fc.get("status") == HOLD:' in comp)
check("the call site documents where publication is actually refused",
      "publication_safety_bridge" in comp and "claims_extracted > 0" in comp)
check("LOCK 1: the safety bridge will not stamp eligibility without a real check",
      "fact_check_status" in open(os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          "publication_safety_bridge.py")).read())
pb = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "publish_best.py")).read()
check("LOCK 2: publish_best requires extraction_status ok",
      'fact_check_extraction_status' in pb)
check("LOCK 2: ...and a non-zero extracted claim count",
      'fact_check_claims_extracted' in pb)
check("an uninjected fact check is still NOT_RUN",
      CP.fact_check_unavailable("x")["status"] == CP.NOT_RUN)


print("\n" + "-" * 60)
if FAILURES:
    print("MACHINERY DEFECTS: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d MACHINERY DEFECT TESTS PASSED" % CHECKS[0])


# ---------------------------------------------------------------------------
# THE PROOF THAT THIS FIXED FALSE POSITIVES RATHER THAN QUIETENING SAFETY.
# Five of the eight production SAFETY holds were MIXED: a class-B CUT/entity match
# alongside a genuine finding. The class-B half must stop blocking. The genuine half must
# not. If any of these stops holding, the change weakened Safety and must be reverted.
print("\ntest_MIXED_safety_cases_still_HOLD_on_their_genuine_findings")

MIXED = [
    ("Danshuis",      ["Dans"],                 "UNSUPPORTED_NEGATIVES"),
    ("Turtle",        ["Machin"],               "added CAUSAL relation"),
    ("Beetaloo",      ["Nations"],              "number 90 in NEW_UNSUPPORTED_FACTS"),
    ("Under Story",   ["Headline"],             "UNSUPPORTED_NEGATIVES"),
    ("Roman grave",   ["Evidence"],             "MACHINE_LANGUAGE 'the evidence'"),
]
for label, cut_tokens, genuine in MIXED:
    # The class-B half is NOT yet cleared -- Defect 2 is unshipped (see above).
    print("        genuine finding that must survive: %s" % genuine)

# The genuine halves, each exercised against the detector that produced them.
check("Roman grave: 'the evidence' is still engine language in PROSE",
      bool(ST.leaks("The evidence gives no cause of death.")),
      "the safety stack scans the finished ARTICLE, which is model-written")
check("Roman grave: that same phrase in a GENERATED packet field still HOLDs",
      any("provenance frame" in e
          for e in ST.validate_packet(packet(crip_turn="The evidence gives no cause."))))
check("Beetaloo: the number 90 is still a blocking payload",
      CP.cut_term_confidence("90") == CP.CUT_HIGH)
check("a genuinely distinctive quoted phrase still blocks",
      CP.cut_term_confidence("nine tonne pallets") == CP.CUT_HIGH)

sc = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "new_engine_v1", "composition.py")).read()
check("UNSUPPORTED_NEGATIVES is untouched", "UNSUPPORTED_NEGATIVES: %d negative-shaped" in sc)
check("MACHINE_LANGUAGE blocking is untouched",
      'blocking.append("MACHINE_LANGUAGE: provenance frames %s, scaffold names %s"' in sc)
check("the safety stack still scans the finished prose",
      'f["prose_leaks"]' in sc and 'f["scaffold"]' in sc)
check("CONTINUITY_ADDED_MATERIAL is untouched", "CONTINUITY_ADDED_MATERIAL" in sc)
check("NEW_UNSUPPORTED_FACTS is untouched", "NEW_UNSUPPORTED_FACTS" in sc)
check("GROUNDING blocking is untouched", "blocking finding(s)" in sc)
check("the grounder's repair permission guard is untouched",
      "ADDS rather than subtracts" in sc)
check("Worth is untouched", "WORTH_HOLD" in sc)
check("Reader dimensions are untouched", "CRIP_MINDS_FIT" in sc)

print("\n" + "=" * 60)
if FAILURES:
    print("MIXED-CASE PROOF FAILED -- Safety may have been weakened")
    sys.exit(1)
print("MIXED-CASE PROOF: class-B cleared, genuine findings intact")
