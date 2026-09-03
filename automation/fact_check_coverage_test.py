#!/usr/bin/env python3
"""
fact_check_coverage_test.py -- an unchecked claim may not become a publication pass.

On 2026-09-01 an article was published on a world_relative_fact_check PASS that had
examined at most eight of its thirteen verifiable claims. Nothing was wrong with the
check that ran: the per-category cap of four skipped the other five, `contradicted` was
empty because nothing contradictory had been looked at, and no branch of the bridge
could see the difference. `fact_check_completed` was true, and it meant what it has
always meant -- the loops finished -- which a reader of the artefact had every reason to
read as "the claims were checked".

The cap is a cost and latency bound. These tests hold the line that it is not a
publication pass, and that the four outcomes a run can have -- technical failure,
incomplete coverage, blocking contradiction, clean full-coverage pass -- are
distinguishable afterwards from the artefact alone, with no network.

The caps themselves are untouched here. So is every per-type verdict policy.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import publication_safety_bridge as BRIDGE                            # noqa: E402
from current_engine_strict_fact_check_test import (                   # noqa: E402
    StubFactChecker, _accept_run, _check9)

FAILURES: list = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


# ── drivers ───────────────────────────────────────────────────────────────────
class Checker(StubFactChecker):
    """The real _run_web_fact_check over canned extraction and canned verdicts."""

    def __init__(self, claims, verdicts=None):
        super().__init__(raw=json.dumps({"claims": claims}))
        self._by_claim = verdicts or {}

    def _web_verify_quote(self, person, quote, timeout=None):
        return self._by_claim.get(quote, ("VERIFIED", "found in two sources"))

    def _web_verify_claim(self, ctype, subject, claim, timeout=None):
        return self._by_claim.get(claim, ("VERIFIED", "found in two sources"))


def via_engine(claims, verdicts=None):
    """Bridge result produced through the REAL fact-check code path."""
    fc = Checker(claims, verdicts)._run_web_fact_check("body", strict=True)
    return fc, BRIDGE.evaluate(_accept_run(), fact_check_fn=lambda t: fc)


def via_literal(fc):
    """Bridge result over a hand-shaped result, for count states the real path
    cannot produce (a malformed record)."""
    return BRIDGE.evaluate(_accept_run(), fact_check_fn=lambda t: fc)


def literal(extracted, findings, not_checked, contradicted=(), advisory=(),
            completed=True, status="ok"):
    return {"extraction_status": status, "claims_extracted": extracted,
            "fact_check_completed": completed,
            "findings": [{"claim_id": "C%02d" % (i + 1), "type": "STAT",
                           "subject": "S", "claim_text": "c%d" % i,
                           "verdict": "VERIFIED", "reason": "found",
                           "blocking": False} for i in range(findings)],
            "not_checked": [{"type": "STAT", "subject": "S", "claim_text": "n%d" % i,
                             "skipped_reason": "claim_cap=4 per category"}
                            for i in range(not_checked)],
            "contradicted": list(contradicted), "advisory": list(advisory),
            "unverifiable_count": 0, "soft_contradicted_count": 0, "lines": []}


def quotes(n, prefix="q"):
    return [{"type": "QUOTE", "subject": "Person %d" % i,
             "claim": "%s quote %d" % (prefix, i)} for i in range(n)]


def stats(n, prefix="s"):
    return [{"type": "STAT", "subject": "Agency %d" % i,
             "claim": "%s stat %d" % (prefix, i)} for i in range(n)]


def ev(r):
    return r.fact_check_evidence


def reason_of(r):
    return _check9(r)["detail"].split(":")[0]


# ── A ─────────────────────────────────────────────────────────────────────────
def test_A_full_coverage_and_clean_passes():
    fc, r = via_engine(quotes(3) + stats(3))
    check("A: 6 extracted", ev(r)["claims_extracted"] == 6, ev(r))
    check("A: 6 checked", ev(r)["claims_checked"] == 6, ev(r))
    check("A: nothing skipped", ev(r)["claims_not_checked"] == 0 and fc["not_checked"] == [])
    check("A: coverage_complete is true", ev(r)["coverage_complete"] is True, ev(r))
    check("A: check 9 PASSES", _check9(r)["ok"] is True, _check9(r))
    check("A: eligible", r.eligible is True)
    check("A: the detail states coverage",
          "coverage=complete" in _check9(r)["detail"], _check9(r)["detail"])


# ── B ─────────────────────────────────────────────────────────────────────────
def test_B_a_partially_checked_record_does_not_pass():
    """The 2026-09-01 shape: 13 extracted, 8 checked, 5 unchecked, none of the eight
    contradicted. That used to pass and publish.

    PR #57 removed the per-category caps from the publication path, so the STRICT
    checker no longer produces this state by truncation -- 13 claims are now all
    checked, or the article holds. The GATE still has to hold the line for every other
    way a record can arrive partial (a deadline, a malformed result, a future caller),
    so it is exercised here directly on the record shape rather than through the caps
    that used to make it.
    """
    r = via_literal(literal(13, 8, 5))
    check("B: 13 extracted", ev(r)["claims_extracted"] == 13, ev(r))
    check("B: 8 checked", ev(r)["claims_checked"] == 8, ev(r))
    check("B: 5 not checked", ev(r)["claims_not_checked"] == 5, ev(r))
    check("B: nothing among the checked was contradicted",
          ev(r)["contradicted_count"] == 0, ev(r))
    check("B: execution still reports completed",
          ev(r)["fact_check_completed"] is True, ev(r))
    check("B: but coverage_complete is FALSE", ev(r)["coverage_complete"] is False, ev(r))
    check("B: check 9 FAILS", _check9(r)["ok"] is False, _check9(r))
    check("B: publication_eligible is false", r.eligible is False)
    check("B: the reason is FACT_CHECK_COVERAGE_INCOMPLETE",
          reason_of(r) == "FACT_CHECK_COVERAGE_INCOMPLETE", _check9(r)["detail"])
    d = _check9(r)["detail"]
    check("B: the detail names the counts", "8 of 13" in d and "5 were not" in d, d)

    # and the strict path's own behaviour on the same 13 claims, after #57
    fc, r2 = via_engine(quotes(5) + stats(8))
    check("B: the strict checker now checks all 13 instead",
          ev(r2)["claims_checked"] == 13 and ev(r2)["coverage_complete"] is True,
          ev(r2))


# ── C ─────────────────────────────────────────────────────────────────────────
def test_C_no_total_count_shortcut_is_used():
    """The regression a naive `claims_extracted <= 8` shortcut would have introduced.
    Six claims of one category used to be truncated to four; after PR #57 they are all
    checked, so the shortcut is untestable through the caps -- but the gate must still
    never conclude coverage from a total alone.
    """
    for extracted, checked, skipped in ((6, 4, 2), (5, 3, 2), (8, 6, 2), (3, 1, 2)):
        r = via_literal(literal(extracted, checked, skipped))
        check("C: %d extracted / %d checked is incomplete regardless of the total"
              % (extracted, checked), ev(r)["coverage_complete"] is False, ev(r))
        check("C:   and FAILS", _check9(r)["ok"] is False)
    brg = (HERE / "publication_safety_bridge.py").read_text()
    check("C: no total-count shortcut exists in the gate",
          "<= 8" not in brg and "claims_n <= 8" not in brg and "> 8" not in brg)
    # six claims of one category are now fully covered by the strict checker
    fc, r2 = via_engine(stats(6))
    check("C: six same-category claims are all checked after #57",
          ev(r2)["claims_checked"] == 6 and ev(r2)["coverage_complete"] is True, ev(r2))
    check("C: and none recorded as skipped", fc["not_checked"] == [], fc["not_checked"])


# ── D ─────────────────────────────────────────────────────────────────────────
def test_D_exactly_at_the_caps_is_full_coverage():
    fc, r = via_engine(quotes(4) + stats(4))
    check("D: 8 extracted", ev(r)["claims_extracted"] == 8, ev(r))
    check("D: 8 checked", ev(r)["claims_checked"] == 8, ev(r))
    check("D: 0 skipped", ev(r)["claims_not_checked"] == 0, ev(r))
    check("D: coverage_complete is true", ev(r)["coverage_complete"] is True, ev(r))
    check("D: check 9 PASSES", _check9(r)["ok"] is True, _check9(r))
    check("D: eligible", r.eligible is True)


# ── E ─────────────────────────────────────────────────────────────────────────
def test_E_technical_failure_is_still_fail_closed_and_still_distinct():
    fc = StubFactChecker(boom=RuntimeError("provider exploded"))
    res = fc._run_web_fact_check("body", strict=True)
    r = via_literal(res)
    check("E: extraction error fails closed", _check9(r)["ok"] is False)
    check("E: reason is EXTRACTION_ERROR, not a coverage reason",
          reason_of(r) == "EXTRACTION_ERROR", _check9(r)["detail"])

    r2 = via_literal(literal(6, 6, 0, completed=False))
    check("E: incomplete execution fails closed", _check9(r2)["ok"] is False)
    check("E: reason is FACT_CHECK_INCOMPLETE",
          reason_of(r2) == "FACT_CHECK_INCOMPLETE", _check9(r2)["detail"])

    r3 = via_literal(literal(0, 0, 0))
    check("E: zero claims fails closed", _check9(r3)["ok"] is False)
    check("E: reason is NO_VERIFIABLE_CLAIMS",
          reason_of(r3) == "NO_VERIFIABLE_CLAIMS", _check9(r3)["detail"])

    r4 = via_literal(literal(6, 6, 0, status=None))
    check("E: a non-strict result fails closed", _check9(r4)["ok"] is False)
    check("E: reason is NON_STRICT_FACT_CHECK",
          reason_of(r4) == "NON_STRICT_FACT_CHECK", _check9(r4)["detail"])
    check("E: no fact-check function at all still fails closed",
          BRIDGE.evaluate(_accept_run(), fact_check_fn=None).eligible is False)


# ── F ─────────────────────────────────────────────────────────────────────────
def test_F_a_blocking_contradiction_still_blocks_under_full_coverage():
    for ctype, label in (("STUDY", "a STUDY"), ("QUOTE", "a QUOTE")):
        claims = ([{"type": ctype, "subject": "X", "claim": "the bad one"}]
                  + (stats(3) if ctype == "STUDY" else quotes(3)))
        fc, r = via_engine(claims, {"the bad one": ("CONTRADICTED", "not true")})
        check("F: %s contradiction blocks" % label, _check9(r)["ok"] is False,
              _check9(r)["detail"])
        check("F: coverage was complete, so the reason is the contradiction",
              ev(r)["coverage_complete"] is True
              and reason_of(r) == "extraction=ok claims_extracted=4 claims_checked=4 "
                                  "coverage=complete contradicted=1 advisory=0 "
                                  "unverifiable=0".split(":")[0],
              (ev(r)["coverage_complete"], _check9(r)["detail"]))
        check("F: and it is named in the findings",
              any(f["verdict"] == "CONTRADICTED" and f["blocking"]
                  for f in ev(r)["findings"]), ev(r)["findings"])
        check("F: not eligible", r.eligible is False)


# ── G ─────────────────────────────────────────────────────────────────────────
def test_G_advisory_semantics_are_untouched():
    for ctype in ("STAT", "EVENT"):
        claims = [{"type": ctype, "subject": "A", "claim": "the soft one"}] + stats(2)
        fc, r = via_engine(claims, {"the soft one": ("CONTRADICTED", "figure differs")})
        check("G: a contradicted %s is advisory, not blocking" % ctype,
              _check9(r)["ok"] is True, _check9(r)["detail"])
        check("G: %s: coverage complete" % ctype, ev(r)["coverage_complete"] is True)
        check("G: %s: still eligible" % ctype, r.eligible is True)
        check("G: %s: counted as advisory" % ctype,
              ev(r)["advisory_count"] == 1 and ev(r)["contradicted_count"] == 0, ev(r))
        check("G: %s: soft_contradicted_count kept" % ctype,
              ev(r)["soft_contradicted_count"] == 1, ev(r))
    # UNVERIFIABLE, unchanged: counted, never blocking on its own
    fc, r = via_engine(stats(3), {"s stat 0": ("UNVERIFIABLE", "nothing either way")})
    check("G: an UNVERIFIABLE claim alone does not block", _check9(r)["ok"] is True)
    check("G: and is counted", ev(r)["unverifiable_count"] == 1, ev(r))


# ── H ─────────────────────────────────────────────────────────────────────────
def test_H_inconsistent_counts_fail_closed():
    """Coverage is read from both sides. A record that does not close is not evidence."""
    for label, fc in (
            ("checked==extracted but a skip is recorded", literal(8, 8, 1)),
            ("fewer checked than extracted with no skips", literal(8, 7, 0)),
            ("neither side closes", literal(8, 5, 1)),
            ("more checked than extracted", literal(4, 6, 0))):
        r = via_literal(fc)
        check("H: %s -> coverage FALSE" % label,
              ev(r)["coverage_complete"] is False, ev(r))
        check("H: %s -> check 9 FAILS" % label, _check9(r)["ok"] is False)
        check("H: %s -> not eligible" % label, r.eligible is False)
    r = via_literal(literal(8, 8, 1))
    check("H: the arithmetic mismatch is reported, not smoothed over",
          ev(r)["counts_consistent"] is False
          and "counts do not close" in _check9(r)["detail"], _check9(r)["detail"])
    r2 = via_literal(literal(13, 8, 5))
    check("H: a consistent-but-incomplete record says so",
          ev(r2)["counts_consistent"] is True
          and ev(r2)["coverage_complete"] is False, ev(r2))


# ── the four outcomes must be distinguishable from the artefact alone ─────────
def test_the_four_outcomes_are_distinguishable_without_network():
    cases = {}
    _, r = via_engine(quotes(2) + stats(2))
    cases["CLEAN_FULL_COVERAGE_PASS"] = r
    cases["COVERAGE_INCOMPLETE"] = via_literal(literal(13, 8, 5))
    _, r = via_engine([{"type": "STUDY", "subject": "X", "claim": "bad"}] + stats(2),
                      {"bad": ("CONTRADICTED", "no such study")})
    cases["BLOCKING_CONTRADICTION"] = r
    cases["TECHNICAL_FAILURE"] = via_literal(
        StubFactChecker(boom=RuntimeError("boom"))._run_web_fact_check("b", strict=True))

    for name, r in cases.items():
        # only the persisted artefact is consulted: a round trip through JSON
        art = json.loads(json.dumps({"checks": r.checks, "eligible": r.eligible,
                                     "fact_check_evidence": ev(r)}))
        e = art["fact_check_evidence"]
        c = [x for x in art["checks"] if x["check"] == "world_relative_fact_check"][0]
        if name == "CLEAN_FULL_COVERAGE_PASS":
            ok = (c["ok"] and e["coverage_complete"] and e["contradicted_count"] == 0
                  and e["extraction_status"] == "ok")
        elif name == "COVERAGE_INCOMPLETE":
            ok = (not c["ok"] and e["extraction_status"] == "ok"
                  and e["fact_check_completed"] and not e["coverage_complete"]
                  and e["claims_not_checked"] > 0
                  and c["detail"].startswith("FACT_CHECK_COVERAGE_INCOMPLETE"))
        elif name == "BLOCKING_CONTRADICTION":
            ok = (not c["ok"] and e["coverage_complete"]
                  and e["contradicted_count"] >= 1
                  and any(f["verdict"] == "CONTRADICTED" and f["blocking"]
                          for f in e["findings"]))
        else:
            ok = (not c["ok"] and e["extraction_status"] != "ok"
                  and not e["fact_check_completed"] and e["claims_checked"] == 0)
        check("%s is identifiable from the artefact alone" % name, ok,
              {"ok": c["ok"], "detail": c["detail"][:80],
               "coverage": e.get("coverage_complete"),
               "not_checked": e.get("claims_not_checked")})


# ── nothing else moved ────────────────────────────────────────────────────────
def test_the_caps_and_the_policies_are_untouched():
    fcs = (HERE / "orchestrator" / "fact_check.py").read_text()
    brg = (HERE / "publication_safety_bridge.py").read_text()
    check("the legacy advisory path keeps its per-category caps", "claim_cap=4" in fcs)
    check("legacy QUOTE cap slice intact",
          'quote_claims = [c for c in claims if c["type"] == "QUOTE"][:claim_cap]' in fcs)
    check("legacy other cap slice intact", '[:claim_cap]' in fcs)
    strict_block = fcs.split("if strict:\n                max_claims")[1].split("else:")[0]
    check("the publication path truncates by NO category (PR #57)",
          "[:claim_cap]" not in strict_block, strict_block[:200])
    check("model unchanged", 'model="perplexity/sonar"' in fcs)
    check("extraction prompt unchanged",
          "Extract every claim from this article that could be independently " in fcs)
    check("no extra network call added",
          fcs.split("def _run_web_fact_check")[1].split("\n    def ")[0]
          .count("_call_openai_compat_api") == 0)
    check("STUDY still blocks, STAT/EVENT still advisory",
          'if c["type"] == "STUDY":' in fcs and 'result["advisory"].append(c)' in fcs)
    check("the contradiction verdict line is unchanged",
          'r.add("world_relative_fact_check", not contradicted,' in brg)
    check("fact_check_completed is neither renamed nor removed",
          '"fact_check_completed": completed,' in brg
          and "fact_check_completed" in fcs)
    check("coverage is a separate prerequisite, not a redefinition of completion",
          'elif not cov["coverage_complete"]:' in brg)


def main() -> None:
    for fn in (test_A_full_coverage_and_clean_passes,
               test_B_a_partially_checked_record_does_not_pass,
               test_C_no_total_count_shortcut_is_used,
               test_D_exactly_at_the_caps_is_full_coverage,
               test_E_technical_failure_is_still_fail_closed_and_still_distinct,
               test_F_a_blocking_contradiction_still_blocks_under_full_coverage,
               test_G_advisory_semantics_are_untouched,
               test_H_inconsistent_counts_fail_closed,
               test_the_four_outcomes_are_distinguishable_without_network,
               test_the_caps_and_the_policies_are_untouched):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL FACT-CHECK COVERAGE TESTS PASSED")


if __name__ == "__main__":
    main()
