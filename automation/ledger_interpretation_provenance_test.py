#!/usr/bin/env python3
"""
ledger_interpretation_provenance_test.py -- an interpretation must read something real.

An INTERPRETATION is deliberately exempt from quoting a verbatim support_span: it reads
the evidence rather than reporting it. It was NOT meant to be exempt from saying which
evidence it reads, but it was: `check_ledger` skipped interpretations with a `continue`
placed ABOVE the source-id resolution, and `ledger.validate_fact` only requires
`evidence_ids` to be non-empty. Those are the only two places a cited id is looked at, so
an interpretation citing a source that does not exist passed the whole engine.

That made INTERPRETATION the only claim type in the taxonomy with no evidence binding at
all. Every other type is held by the verbatim span; an interpretation has no span, so the
id is the entire binding, and an unresolvable id is no binding.

The tests below pin both halves: the exemption that is real (no span required) and the
exemption that never was (any source id you like).

Behavioural, no provider, no network, no filesystem.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP   # noqa: E402
from new_engine_v1 import ledger as LG        # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print("  PASS  %s" % label)
    else:
        FAILURES.append(label)
        print("  FAIL  %s   <- %r" % (label, detail))


S0 = ("The council published a ranking sheet in March. Ten entries were photographed "
      "for the catalogue. No entry was withdrawn.")
S1 = "The catalogue was printed by a local firm."
SRCS = {"S0": S0, "S1": S1}


def fact(fid, **over):
    f = {"fact_id": fid,
         "proposition": "The council published a ranking sheet in March.",
         "claim_type": LG.POSITIVE, "claim_kind": "OCCURRENCE",
         "evidence_ids": ["S0"],
         "support_span": "The council published a ranking sheet in March.",
         "entities": [], "scope": LG.WORLD, "corpus_size": 0,
         "prohibited_extensions": []}
    f.update(over)
    return f


def interp(fid, **over):
    base = {"claim_type": LG.INTERPRETATION,
            "proposition": "The ranking is best understood as an index of visibility.",
            "support_span": ""}
    base.update(over)
    return fact(fid, **base)


def failures_for(f):
    return CP.check_ledger({f["fact_id"]: f}, SRCS).get(f["fact_id"], [])


def cites_unknown_source(errs):
    return any("cites source ids that are not in the pack" in e for e in errs)


# ── the hole ──────────────────────────────────────────────────────────────────
def test_an_interpretation_may_not_cite_a_source_that_does_not_exist():
    errs = failures_for(interp("F90", evidence_ids=["S_DOES_NOT_EXIST"]))
    check("an interpretation citing a nonexistent source id is refused",
          cites_unknown_source(errs), errs)

    errs = failures_for(interp("F91", evidence_ids=["S0", "S_DOES_NOT_EXIST"]))
    check("  and one real id does not launder an unreal one",
          cites_unknown_source(errs), errs)


def test_an_interpretation_citing_a_real_source_is_accepted():
    check("an interpretation citing S0 is accepted",
          failures_for(interp("F92")) == [], failures_for(interp("F92")))
    check("an interpretation citing S1 is accepted",
          failures_for(interp("F93", evidence_ids=["S1"])) == [],
          failures_for(interp("F93", evidence_ids=["S1"])))


def test_the_span_exemption_is_untouched():
    """The exemption that IS real: an interpretation reads evidence, it does not quote
    it. It must not acquire a verbatim-span requirement as a side effect of acquiring a
    source-id requirement."""
    check("an interpretation needs no support_span",
          failures_for(interp("F94", support_span="")) == [],
          failures_for(interp("F94", support_span="")))
    check("and is not held to verbatim even when it carries one",
          failures_for(interp("F95", support_span="words nowhere in any source")) == [],
          failures_for(interp("F95", support_span="words nowhere in any source")))
    check("while ledger.validate_fact still demands SOME evidence id",
          any("must name the evidence it reads" in e
              for e in LG.validate_fact(interp("F96", evidence_ids=[]), S0)),
          LG.validate_fact(interp("F96", evidence_ids=[]), S0))


# ── everything else, unchanged ────────────────────────────────────────────────
def test_positive_behaviour_is_unchanged():
    check("a positive fact with a verbatim span from its cited source is accepted",
          failures_for(fact("F01")) == [], failures_for(fact("F01")))
    check("a positive fact citing a nonexistent source is refused",
          cites_unknown_source(failures_for(fact("F02",
                                                 evidence_ids=["S_DOES_NOT_EXIST"]))))
    errs = failures_for(fact("F03", evidence_ids=["S1"]))
    check("a span quoted from S0 but attributed to S1 is still refused",
          any("not verbatim in any cited source" in e for e in errs), errs)
    errs = failures_for(fact("F04", support_span="a span in no source at all"))
    check("a span in no source at all is still refused",
          any("not verbatim" in e for e in errs), errs)


def test_negative_behaviour_is_unchanged():
    neg = fact("F05", claim_type=LG.ABSENCE,
               proposition="No entry was withdrawn.",
               support_span="No entry was withdrawn.")
    check("a WORLD negative whose span states the negative is accepted",
          failures_for(neg) == [], failures_for(neg))

    silent = fact("F06", claim_type=LG.ABSENCE,
                  proposition="No entry was withdrawn.",
                  support_span="Ten entries were photographed for the catalogue.")
    check("a WORLD negative resting on a non-negative span is still refused",
          any("silence is not evidence of absence" in e for e in failures_for(silent)),
          failures_for(silent))

    check("a negative citing a nonexistent source is refused",
          cites_unknown_source(failures_for(
              fact("F07", claim_type=LG.ABSENCE,
                   proposition="No entry was withdrawn.",
                   support_span="No entry was withdrawn.",
                   evidence_ids=["S_DOES_NOT_EXIST"]))))


def main():
    for fn in (test_an_interpretation_may_not_cite_a_source_that_does_not_exist,
               test_an_interpretation_citing_a_real_source_is_accepted,
               test_the_span_exemption_is_untouched,
               test_positive_behaviour_is_unchanged,
               test_negative_behaviour_is_unchanged):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL LEDGER INTERPRETATION PROVENANCE TESTS PASSED")


if __name__ == "__main__":
    main()
