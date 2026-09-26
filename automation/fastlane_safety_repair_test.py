#!/usr/bin/env python3
"""fastlane_safety_repair_test.py -- the one Safety repair runs where articles are made.

The repair, its eligibility rule and its single-attempt guarantee all predate this file
and are exercised directly in story_architecture_composition_test.py. What was broken
was only WHERE it ran: the call site read `compose_mode != COMPOSE_FAST_LANE`, and every
scheduled production run is FAST_LANE, so the path had never executed in production.

production-20260926T072441Z-66967ce4 is the cost: a finished 917-word article held on
exactly two findings, UNSUPPORTED_NEGATIVES (one sentence) and MACHINE_LANGUAGE (the
phrase "this reading", once), both of them in SAFETY_REPAIRABLE_PREFIXES.

These tests assert the guarantees that had to survive removing that clause. Stdlib only,
no network, no model call.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP   # noqa: E402

FAILURES: list = []
CHECKS = [0]


def check(label, ok, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if ok else "  FAIL  %s") % label
          + (("" if ok else " -- " + str(detail)) if detail else ""))
    if not ok:
        FAILURES.append(label)


SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "new_engine_v1", "composition.py")).read()
BLOCK = SRC[SRC.index("# ONE SAFETY REPAIR, tried before"):
            SRC.index("# ONE PACKAGE-ONLY SAFETY REPAIR")]
# Assert on CODE, never on the prose around it. The comment above the call site quotes
# the clause it removed, and an earlier version of this file matched that quotation --
# the same way the prose-finish test did the day before. Strip comments first.
CODE = "\n".join(ln for ln in BLOCK.splitlines()
                 if ln.strip() and not ln.strip().startswith("#"))
LOOPS = [ln for ln in CODE.splitlines()
         if ln.strip().startswith(("for ", "while "))]


class Counting:
    """A provider that records how many times it was asked for anything."""

    def __init__(self):
        self.calls = 0

    def complete(self, system, user, max_tokens=3000, **kw):
        self.calls += 1
        raise AssertionError("no model call should have been made")


print("test_the_repair_runs_on_the_fast_lane")
check("the call site no longer excludes FAST_LANE",
      "compose_mode" not in CODE, CODE.splitlines()[0])
check("  and it still only runs on a Safety hold",
      'if sa["status"] != PASS:' in CODE)
check("  and non-FAST_LANE behaviour is the same code path",
      CODE.count("safety_repair(P,") == 1,
      "one call site, mode-independent, so no mode has its own branch")

print("\ntest_exactly_one_attempt_and_no_loop")
check("the repair is attempted at most once", CODE.count("safety_repair(P,") == 1)
check("  and the block contains no loop", LOOPS == [], str(LOOPS))
check("  and a second failure falls through to the unchanged HOLD",
      "srep[\"status\"] == PASS" in CODE and "else" not in CODE.split("srep[")[1][:400],
      "no alternative branch retries or substitutes prose")

print("\ntest_the_repaired_text_must_pass_a_fresh_audit")
check("the package is rebuilt from the repaired article",
      "pkg = pkg_ref[0] = make_package(final)" in CODE)
check("  and Safety is re-run from scratch on the result",
      "sa = record(SAFETY, audit(final, pkg, repair=srep))" in CODE)
check("  and the re-audit is what decides, not the repair's own status",
      CODE.index("make_package(final)") < CODE.index("audit(final, pkg, repair=srep)"))

print("\ntest_eligibility_is_all_or_nothing")
TEXT = ("The note sets a rule about type. One passage is written in the first person. "
        "This reading of the page is what the article turns on.")
REPAIRABLE = {
    "blocking": ["MACHINE_LANGUAGE: provenance frames [('this reading', 1)], "
                 "scaffold names []"],
    "audits": {"continuity_final": {"prose_leaks": {"frames": [["this reading", 1]]}}},
}
NON_REPAIRABLE = {
    "blocking": ["NEW_UNSUPPORTED_FACTS: the final prose carries factual surface the "
                 "packet does not"],
    "audits": {"continuity_final": {}},
}
MIXED = {
    "blocking": REPAIRABLE["blocking"] + ["SOMETHING_THIS_STAGE_CANNOT_LOCATE: x"],
    "audits": REPAIRABLE["audits"],
}

got = CP.safety_repair_findings(REPAIRABLE, TEXT, "")
check("a wholly repairable hold yields locatable findings", bool(got), str(got)[:120])
check("  and every finding quotes text that is actually in the article",
      all(f["quote"] in TEXT or f["quote"].strip(".") in TEXT for f in (got or [])),
      str(got)[:160])

check("an unrecognised category makes the whole attempt ineligible",
      CP.safety_repair_findings(NON_REPAIRABLE, TEXT, "") is None)
check("a MIXED set never repairs, even though one member is repairable",
      CP.safety_repair_findings(MIXED, TEXT, "") is None)
check("an empty blocking list is not a repair opportunity",
      CP.safety_repair_findings({"blocking": [], "audits": {}}, TEXT, "") is None)

print("\ntest_an_ineligible_hold_costs_no_model_call")
p = Counting()
for label, sa in (("unrecognised category", NON_REPAIRABLE), ("mixed set", MIXED)):
    found = CP.safety_repair_findings(sa, TEXT, "")
    if found:
        CP.safety_repair(p, TEXT, found, {}, {})
check("an ineligible hold never reaches the provider", p.calls == 0, str(p.calls))
check("  so the added cost is at most one call, only on an eligible hold",
      CODE.count("safety_repair(P,") == 1 and 'if sa["status"] != PASS:' in CODE)

print("\ntest_no_repairable_class_was_added_or_weakened")
check("SAFETY_REPAIRABLE_PREFIXES is unchanged",
      CP.SAFETY_REPAIRABLE_PREFIXES == (
          "MACHINE_LANGUAGE", "PACKAGE_MACHINE_LANGUAGE",
          "CUT_LEAKAGE", "PACKAGE_CUT_LEAKAGE",
          "NEW_UNSUPPORTED_FACTS", "PACKAGE_UNSUPPORTED_FACTS",
          "CONTINUITY_ADDED_MATERIAL", "UNSUPPORTED_NEGATIVES"),
      str(CP.SAFETY_REPAIRABLE_PREFIXES))
check("  and both of the live blockers are covered by it",
      all(any(c.startswith(p_) for p_ in CP.SAFETY_REPAIRABLE_PREFIXES)
          for c in ("UNSUPPORTED_NEGATIVES: 1 negative-shaped sentence(s)",
                    "MACHINE_LANGUAGE: provenance frames [('this reading', 1)]")))

print("\n" + "-" * 60)
if FAILURES:
    print("FAST LANE SAFETY REPAIR: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d FAST LANE SAFETY REPAIR TESTS PASSED" % CHECKS[0])
