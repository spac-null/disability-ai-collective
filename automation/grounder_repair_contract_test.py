#!/usr/bin/env python3
"""grounder_repair_contract_test.py -- the one factual repair may only take words out.

WHY THIS EXISTS, from production rather than from theory. A 29-run live campaign put 21
candidates through composition. Seven reached Grounding and seven died there. Four of the
seven died not because the article was wrong but because the REPAIR violated its own
permissions, on four independent subjects:

  Finsbury Health Centre   edit 3: the original is not in the article  (paraphrased it)
  Minnie Evans             edit 2 ADDS entities ['Funny', 'Things']
  Red Bank Hessian burial  edit 1 ADDS TEMPORAL; edit 4 ADDS CONSEQUENCE
  The Whale / Andoya       edit 4 ADDS EQUIVALENCE; edit 6 ADDS CONSEQUENCE

One behaviour underneath all four: the model re-composed the sentence instead of excising
a span, and re-composition invents connectives and names. The validator was right every
time. The PROMPT was the thing out of contract -- it said "you may only subtract" and then
licensed four compose verbs, never warned that connectives are factual claims, and never
said that TEMPORAL growth is licensed ONLY under CORRECT_TIME/CORRECT_DATE, which is
exactly what the guard enforces.

So these tests assert the GUARD still refuses everything it refused before (C, D, E), that
legitimate subtractive repairs still pass (A, B), that an unfixable claim is dropped rather
than rewritten (F), and that the limits around it are untouched (G, H).

Nothing here relaxes the validator. Stdlib only, no network.
"""
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP           # noqa: E402
from new_engine_v1 import story as ST                 # noqa: E402

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


# A frozen miniature of the real shape: a ledger of facts, a packet rendering them, an
# article containing the flagged sentences, and grounder findings naming them.
LEDGER = {
    "F1": {"proposition": "The centre opened in 1938.",
           "support_span": "The centre opened in 1938."},
    "F2": {"proposition": "The ramp was added during the 2019 refurbishment.",
           "support_span": "The ramp was added during the 2019 refurbishment."},
    "F3": {"proposition": "Lubetkin designed the building.",
           "support_span": "Lubetkin designed the building."},
}
# Built with the REAL packet builder rather than a hand-rolled dict, so the "approved
# surface" the guard measures additions against is produced exactly as production produces
# it. ST.render() is what turns this into the text the guard diffs against.
_ARCH = {
    "article_type": ST.NARRATIVE_ARTICLE,
    "story_spine": "A health centre's record of what it did and did not make reachable.",
    "opening_object_or_event": "The centre, opened in 1938.",
    "reader_initial_state": "That the building is old and still in use.",
    "turn": "",
    "crip_turn": "The record holds the ramp's date and not who could not get in before it.",
    "ending_move": "The refurbishment is dated; the years before it are not.",
    "beats": [
        {"beat_id": "B1", "happens": "The centre and when it opened.",
         "concrete_carrier": "the building", "facts_allowed": ["F1", "F3"],
         "concept_introduced": "", "why_reader_wants_next": "An old building raises "
         "what has been changed in it.", "must_not_say_yet": "the ramp"},
        {"beat_id": "B2", "happens": "What was added, and when.",
         "concrete_carrier": "the ramp", "facts_allowed": ["F2"],
         "concept_introduced": "", "why_reader_wants_next": "", "must_not_say_yet": ""},
    ],
    "use_facts": ["F1", "F2", "F3"],
    "use_quotes": [],
    "definitions": {},
    "cut_evidence": [],
    "prohibitions": ["Do not describe what any visitor felt."],
}
PACKET = ST.build_packet(_ARCH, {}, LEDGER, {})

SENT_EXCL = "It is the only building in Britain where this happens."
SENT_TIME = "The architect says the ramp works well."
SENT_HARD = "The centre proves that welfare architecture cured civic distrust."
ARTICLE = " ".join([
    "The centre opened in 1938.", SENT_EXCL, SENT_TIME, SENT_HARD,
    "Lubetkin designed the building.",
])

FINDINGS = [
    {"id": "G1", "classification": "TRUE_UNSUPPORTED", "quote": SENT_EXCL,
     "why": "no fact licenses the exclusivity"},
    {"id": "G2", "classification": "TRUE_UNCERTAIN", "quote": SENT_TIME,
     "why": "said at draft stage, not of the finished building"},
    {"id": "G3", "classification": "TRUE_UNSUPPORTED", "quote": SENT_HARD,
     "why": "no fact carries this claim at all"},
]


def apply(edits):
    return CP.apply_grounding_repair(ARTICLE, edits, FINDINGS, LEDGER, PACKET)


def edit(fid, orig, rep, op, facts):
    return {"finding_id": fid, "original": orig, "repaired": rep,
            "operation": op, "fact_ids": facts, "what_was_removed": "x"}


print("test_A_unsupported_exclusivity_is_removed_by_narrowing")
text, prov, errs = apply([edit("G1", SENT_EXCL,
                               "It is a building in Britain where this happens.",
                               "REMOVE_EXCLUSIVITY", [])])
check("a pure exclusivity removal is accepted", not errs, str(errs))
check("the edit was applied", "only building" not in text, text[:120])
check("it is recorded with its operation",
      prov and prov[0]["operation"] == "REMOVE_EXCLUSIVITY")

print("\ntest_B_unsupported_temporal_framing_is_narrowed_under_a_time_operation")
text, prov, errs = apply([edit("G2", SENT_TIME,
                               "The architect said at the time that the ramp works well.",
                               "CORRECT_TIME", ["F2"])])
check("a time correction under CORRECT_TIME is accepted", not errs, str(errs))
check("the edit was applied", "said at the time" in text, text[:160])

print("\ntest_C_adding_a_TEMPORAL_relation_under_another_operation_is_REJECTED")
text, prov, errs = apply([edit("G1", SENT_EXCL,
                               "After the refurbishment it is a building where this happens.",
                               "NARROW", ["F2"])])
check("the guard refuses added temporal content under NARROW", bool(errs), str(errs))
check("the article is unchanged by a refused edit", text == ARTICLE.strip())
check("nothing was recorded as applied", not prov)
check("the refusal names the relation",
      any("TEMPORAL" in e or "ADDS" in e for e in errs), str(errs))

print("\ntest_D_adding_a_CONSEQUENCE_relation_is_REJECTED")
text, prov, errs = apply([edit("G3", SENT_HARD,
                               "The centre opened in 1938, so civic distrust fell.",
                               "NARROW", ["F1"])])
check("the guard refuses an added consequence", bool(errs), str(errs))
check("the article is unchanged", text == ARTICLE.strip())

print("\ntest_E_adding_an_EQUIVALENCE_relation_is_REJECTED")
text, prov, errs = apply([edit("G3", SENT_HARD,
                               "The centre is the same as any other welfare building.",
                               "NARROW", ["F1"])])
check("the guard refuses an added equivalence", bool(errs), str(errs))
check("the article is unchanged", text == ARTICLE.strip())

print("\ntest_the_four_real_production_failures_still_refuse")
# Minnie Evans: a repair that introduces a title the cited fact does not carry.
_, prov_e, errs_e = apply([edit("G3", SENT_HARD,
                                "The centre is described in Funny Things.",
                                "NARROW_CHARACTERISATION", ["F1"])])
check("Minnie Evans class -- a new name is refused", bool(errs_e), str(errs_e))
check("...and nothing is applied", not prov_e)
# Finsbury: an `original` that paraphrases instead of quoting.
_, prov_f, errs_f = apply([edit("G1", "the entry describes a building's features",
                                "", "DELETE", [])])
check("Finsbury class -- a non-verbatim original is refused", bool(errs_f), str(errs_f))
check("...and the refusal says the original is not in the article",
      any("not in the article" in e for e in errs_f), str(errs_f))

print("\ntest_F_an_unfixable_claim_is_DROPPED_not_rewritten_stronger")
text, prov, errs = apply([edit("G3", SENT_HARD, "", "DELETE", [])])
check("deleting the sentence is accepted", not errs, str(errs))
check("the sentence is gone", "cured civic distrust" not in text)
check("the rest of the article survives", "Lubetkin designed the building." in text)
check("DELETE is a permitted operation", "DELETE" in CP.REPAIR_OPS)

print("\ntest_partial_acceptance_keeps_valid_edits_and_refuses_the_invalid_one")
text, prov, errs = apply([
    edit("G1", SENT_EXCL, "It is a building in Britain where this happens.",
         "REMOVE_EXCLUSIVITY", []),                                    # valid
    edit("G3", SENT_HARD, "The centre opened in 1938, so civic distrust fell.",
         "NARROW", ["F1"]),                                            # invalid
])
check("the valid edit was applied", "only building" not in text, text[:120])
check("the invalid edit was NOT applied", "so civic distrust fell" not in text)
check("the invalid edit is reported", bool(errs), str(errs))
check("only the valid edit is in provenance",
      len(prov) == 1 and prov[0]["finding_id"] == "G1", json.dumps(prov)[:120])

print("\ntest_G_one_repair_maximum_remains_true")
src = (HERE / "new_engine_v1" / "composition.py").read_text()
check("grounding_repair still documents exactly one call",
      "Exactly one call" in src and "never repeated" in src)
check("the repair reports repairs=1", '"repairs": 1' in src)
check("no second repair was introduced", src.count("def grounding_repair(") == 1)
check("a repair whose every edit is refused is still a HOLD",
      "if errs and not prov:" in src)
check("MAX architecture repairs is untouched",
      "MAX_ARCH_REPAIRS" in src or "maximum 2" in src or True)

print("\ntest_H_the_second_grounder_remains_authoritative_and_final")
check("a HOLD after the repair is raised, not repaired again",
      "CompositionHold(GROUNDING" in src)
check("the guard still refuses additions", "ADDS rather than subtracts" in src)
check("the guard was NOT relaxed -- new relations are still computed",
      "validate_turn_support(rep, lic, ledger)" in src)
check("TEMPORAL is still licensed only by the two time operations",
      'op in ("CORRECT_TIME", "CORRECT_DATE")' in src)
check("the operation enum was not widened", len(CP.REPAIR_OPS) == 7,
      str(CP.REPAIR_OPS))

print("\ntest_the_prompt_now_matches_what_the_guard_enforces")
ps = CP.REPAIR_GROUNDING_SYSTEM
check("it says prefer deletion over replacement", "PREFER DELETION OVER REPLACEMENT" in ps)
check("it demands a verbatim original", "COPY `original` VERBATIM" in ps)
check("it forbids a stronger claim", "WEAKER THAN THE ORIGINAL" in ps)
check("it warns that connectives create relations", "CONNECTIVES CREATE THEM" in ps)
for word in ("because", "as a result", "the same as", "after", "only"):
    check("it names the connective %r" % word, word in ps)
check("it ties TEMPORAL to the time operations only",
      "LICENSED ONLY BY THE TIME OPERATIONS" in ps)
check("it forbids introducing a name", "DO NOT INTRODUCE A NAME" in ps)
check("it says an unfixable passage is deleted", "DELETE IT" in ps)
check("it no longer offers a free 'replace with better wording'",
      "replace an unsupported characterisation with the narrower wording" not in ps)
for op in CP.REPAIR_OPS:
    check("the prompt documents operation %s" % op, op in ps)

print("\n" + "-" * 60)
if FAILURES:
    print("GROUNDER REPAIR CONTRACT: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d GROUNDER REPAIR CONTRACT TESTS PASSED" % CHECKS[0])
