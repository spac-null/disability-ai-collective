#!/usr/bin/env python3
"""prose_finish_test.py -- one surface pass, before anything factual is checked.

The published WildSumaco article was factually clean and still read as assembled research:
the Reader held READABILITY, MOMENTUM, BREATHING, RESEARCH_LOAD and ENGINE_LANGUAGE_LEAK on
a piece whose facts were all correct. This stage exists for that gap.

PLACEMENT IS THE CONTRACT. It runs between CONTINUITY and SAFETY, so the exact bytes that
publish are the bytes Safety, Grounding and Fact Check read. A polish after them would
invalidate every stamp they issued; a polish after Fact Check would publish prose nothing
had checked.

FAIL-SAFE, like Continuity above it. The incoming article is already publishable, so a bad
polish is discarded whole and costs the run nothing.

Stdlib only, no network.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


ART = ("# The upper room\n\n"
       + "The classroom has no locks and the architects describe it as open to all. " * 6
       + "\n\n" + "The directory entry records an accessibility field. " * 6)
ARCH = {"story_spine": "two registers of who may pass", "ending_move": "the field reads No"}


class Prov:
    def __init__(self, reply=None, boom=False):
        self.reply, self.boom, self.calls = reply, boom, 0
    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                 deadline=None):
        self.calls += 1
        if self.boom:
            raise RuntimeError("provider exploded")
        body = user.split("THE ARTICLE\n", 1)[-1].strip()
        class R:
            text = self.reply if self.reply is not None else body
            def identity(self_): return {"provider": "t"}
        return R()


print("test_placement_before_the_factual_stack")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "new_engine_v1", "composition.py")).read()
i_cont = src.index("cont[\"negative_lineage_carried\"] = lineage")
i_pf = src.index("pf = record(PROSE_FINISH, prose_finish(P, final, arch))")
i_safety = src.index("sa = record(SAFETY, audit(final, pkg))")
i_fc = src.index("fc = record(FACT_CHECK,")
check("it runs after Continuity", i_cont < i_pf)
check("it runs BEFORE Safety", i_pf < i_safety)
check("it runs BEFORE Fact Check", i_pf < i_fc)
check("the polished text is what Safety audits",
      "sa = record(SAFETY, audit(final, pkg))" in src
      and "return safety_audit(draft, text, wr[\"packet\"]" in src)
check("the stage is in the declared stage list", CP.PROSE_FINISH in CP.STAGES)
check("it sits between Continuity and Safety in that list",
      CP.STAGES.index(CP.CONTINUITY) < CP.STAGES.index(CP.PROSE_FINISH)
      < CP.STAGES.index(CP.SAFETY))

print("\ntest_it_polishes_and_the_text_is_carried_forward")
p = Prov(reply=None)
r = CP.prose_finish(p, ART, ARCH)
check("one model call, never two", p.calls == 1, str(p.calls))
check("the polish is applied", r["applied"] is True and r["status"] == CP.PASS)
check("the title survives", r["article_text"].startswith("# The upper room"),
      r["article_text"][:40])

print("\ntest_it_is_fail_safe")
r = CP.prose_finish(Prov(boom=True), ART, ARCH)
check("a provider failure does not raise", r["status"] == CP.SKIPPED)
check("...and carries the incoming article unchanged", r["article_text"] == ART)
check("...and says why", "provider failure" in r["reason"])

r = CP.prose_finish(Prov(reply=""), ART, ARCH)
check("an empty reply is discarded", r["applied"] is False and r["article_text"] == ART)
check("...and is reported", "returned nothing" in r["reason"])

r = CP.prose_finish(Prov(reply="# The upper room\n\nToo short."), ART, ARCH)
check("a reply that cuts the article is discarded", r["applied"] is False)
check("...and named as a cut, not a polish", "that is a cut" in r["reason"], r["reason"])
check("...and the incoming text is carried", r["article_text"] == ART)

long = "# The upper room\n\n" + ("An added sentence that was never there. " * 200)
r = CP.prose_finish(Prov(reply=long), ART, ARCH)
check("a reply that expands the article is discarded", r["applied"] is False)
check("...and named as an expansion", "that is an expansion" in r["reason"], r["reason"])

print("\ntest_it_may_not_research_or_add")
sysp = CP.PROSE_FINISH_SYSTEM
check("it is told to add nothing", "ADD NOTHING" in sysp)
check("no invented scene or sensory detail",
      "no sensory detail" in sysp and "no invented particular" in sysp)
check("the argument may not change", "DO NOT CHANGE THE ARGUMENT" in sysp)
check("it is warned the text is checked afterwards",
      "checked against a frozen evidence ledger" in sysp)
check("it targets research-report cadence", "the paper reports" in sysp)
check("it targets manufactured clinchers", "manufactured clinchers" in sysp)
check("it forbids decoration and imitation",
      "purple prose" in sysp and "imitation of a particular writer" in sysp)
check("it is allowed to leave good prose alone",
      "leave it exactly as it is" in sysp)
check("it returns only the article body", "Return ONLY the finished article body" in sysp)

print("\ntest_a_replay_does_not_polish_a_frozen_article")
check("a frozen article is REPLAYED, not re-polished",
      'st[PROSE_FINISH] = {"status": REPLAYED' in src)
check("...and costs no model call",
      "calls[PROSE_FINISH] = repairs[PROSE_FINISH] = 0" in src)

print("\ntest_stale_sentence_lineage_is_not_carried_over_a_rewrite")
check("the polish resets the Writer's per-sentence negative lineage",
      'lineage = wr["negative_lineage_verified"]' in
      src[i_pf:i_pf + 900],
      "a sentence map from before a rewrite no longer points at those sentences")

print("\ntest_the_polish_may_not_author_a_factual_relation")
# THE THREE CASES THE FIX WAS BUILT FROM. One live, one historical, one ordinary.
#
# 1. production-20260925T070817Z-8ad3b4be. The Writer and Continuity added nothing; this
#    stage split one sentence and wrote "It also aimed to", a second INTENT predication.
#    Safety refused the article; re-auditing the incoming text returned PASS.
INTENT_IN = ("# The dummy\n\nThe project aimed to provide open tools and testing "
             "protocols for evaluating new safety systems, covering more types of road "
             "user than traditional physical crash safety tests do, and to bridge the "
             "gap between virtual testing and standardised safety assessments.")
INTENT_OUT = ("# The dummy\n\nThe project aimed to provide open tools and testing "
              "protocols for evaluating new safety systems, covering more types of road "
              "user than traditional physical crash safety tests do. It also aimed to "
              "bridge the gap between virtual testing and standardised safety "
              "assessments.")
r = CP.prose_finish(Prov(reply=INTENT_OUT), INTENT_IN, ARCH)
check("the live INTENT drift is discarded", r["applied"] is False)
check("  and the exact incoming prose is carried forward",
      r["article_text"] == INTENT_IN)
check("  and it is reported as meaning, not as a length or shape problem",
      "INTENT" in " ".join(r.get("semantic_delta_errors") or []), str(r.get("reason")))
check("  and the discard costs no extra model call", r["model_calls"] == 1)
check("  and there is no retry", r["repairs"] == 0)

# 2. production-20260922T070219Z-adb08587 drifted by one NEGATION relation post-Writer.
#    The class differs; the rule may not.
NEG_IN = ("# The survey\n\nThe register records a reading for each of the nine rooms, "
          "and the report sets those readings beside the measured range.")
NEG_OUT = ("# The survey\n\nThe register records a reading for each of the nine rooms. "
           "The report sets those readings beside the measured range, which no earlier "
           "survey had done.")
r = CP.prose_finish(Prov(reply=NEG_OUT), NEG_IN, ARCH)
check("the historical NEGATION-class drift is discarded too", r["applied"] is False)
check("  and that text never reaches a downstream stage",
      r["article_text"] == NEG_IN)

# 3. An ordinary polish: same relations, better surface. It must still survive, or the
#    guard has simply turned the stage off.
CLEAN_IN = ("# The room\n\nThe classroom has no locks, and the architects describe it as "
            "open to all, and the directory entry records an accessibility field, and "
            "the field is one the survey counted.")
CLEAN_OUT = ("# The room\n\nThe classroom has no locks. The architects describe it as "
             "open to all. The directory entry records an accessibility field, one the "
             "survey counted.")
r = CP.prose_finish(Prov(reply=CLEAN_OUT), CLEAN_IN, ARCH)
check("an ordinary polish that adds no relation still applies",
      r["applied"] is True and r["status"] == CP.PASS, str(r.get("reason")))
check("  and it is the polished text that is carried",
      r["article_text"] == CLEAN_OUT)
check("  and a clean polish records an empty delta, not a missing one",
      r.get("semantic_delta_errors") == [])

check("the guard is the SAME validator Continuity uses, not a second one",
      "CE.validate_semantic_delta(incoming, out)" in src,
      "two post-editors must not drift apart in what they may do")

print("\ntest_a_polish_may_not_cost_a_run_the_unpolished_text_would_have_won")
i_fb = src.index("probe = audit(pre_polish, None)")
window = src[i_fb - 1400:i_fb + 400]
# Asserted on the CONDITION, not on the surrounding prose: the comment above it quotes
# the clause it removed, and an earlier version of this check matched that quotation.
check("the pre-polish fallback no longer excludes the fast lane",
      'if (compose_mode != COMPOSE_FAST_LANE and sa["status"] != PASS' not in src,
      "every scheduled production run is FAST_LANE, so the gated fallback never ran")
check("  and it still only fires when Safety actually failed",
      'if sa["status"] != PASS and pre_polish is not None:' in src)
check("  and it re-audits the preserved artifact rather than asking for new prose",
      "probe = audit(pre_polish, None)" in window
      and "prose_finish(" not in window)
check("  and it only continues if that preserved version passes",
      'if probe["status"] == PASS:' in src)

print("\n" + "-" * 60)
if FAILURES:
    print("PROSE FINISH: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d PROSE FINISH TESTS PASSED" % CHECKS[0])
