#!/usr/bin/env python3
"""
fact_check_evidence_test.py -- the fact-check decision has to be diagnosable later.

Twice on 2026-09-03 an article reached the publication-safety bridge, passed nine of ten
checks, and was blocked by world_relative_fact_check with contradicted=1. Both runs
persisted the count and nothing else: not which of the thirteen claims was contradicted,
not the verdict, not the reason. The gate was fail-closed and its decision was
unrecoverable without going back to the network -- which nobody may do afterwards,
because a live search does not answer what the run saw.

So these tests hold two lines at once. The evidence must be there, and the DECISION must
not have moved: every verdict, every count and every blocking rule is still read from
the same result by the same code.

No network. The one model call is canned, as it already was.
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
    StubFactChecker, _accept_run, _check9, _Log)

FAILURES: list = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


class PerClaimChecker(StubFactChecker):
    """Verdicts keyed by claim text, so one claim among several can be contradicted."""

    def __init__(self, claims, per_claim):
        super().__init__(raw=json.dumps({"claims": claims}))
        self._per_claim = per_claim

    def _web_verify_quote(self, person, quote):
        return self._per_claim.get(quote, ("VERIFIED", "found in two sources"))

    def _web_verify_claim(self, ctype, subject, claim):
        return self._per_claim.get(claim, ("VERIFIED", "found in two sources"))


def bridge_for(fc_result):
    return BRIDGE.evaluate(_accept_run(), fact_check_fn=lambda text: fc_result)


def ev(r):
    return r.fact_check_evidence


# ── A ─────────────────────────────────────────────────────────────────────────
def test_A_all_clean_claims_are_all_recorded():
    claims = [{"type": "STAT", "subject": "Org %d" % i, "claim": "claim %d" % i}
              for i in range(3)]
    fc = PerClaimChecker(claims, {})
    res = fc._run_web_fact_check("body", strict=True)
    check("A: every claim has a finding", len(res["findings"]) == 3, res["findings"])
    check("A: every verdict recorded",
          [f["verdict"] for f in res["findings"]] == ["VERIFIED"] * 3, res["findings"])
    check("A: each carries its claim text",
          [f["claim_text"] for f in res["findings"]] == ["claim 0", "claim 1", "claim 2"],
          res["findings"])
    check("A: none blocking", not any(f["blocking"] for f in res["findings"]))
    check("A: nothing contradicted", res["contradicted"] == [])

    r = bridge_for(res)
    check("A: bridge check 9 PASSES", _check9(r)["ok"] is True, _check9(r))
    check("A: aggregates preserved",
          (ev(r)["extraction_status"], ev(r)["claims_extracted"],
           ev(r)["fact_check_completed"]) == ("ok", 3, True), ev(r))
    check("A: findings reach the persisted evidence",
          len(ev(r)["findings"]) == 3, ev(r)["findings"])
    check("A: contradicted_count is zero", ev(r)["contradicted_count"] == 0)


# ── B ─────────────────────────────────────────────────────────────────────────
def test_B_the_one_contradicted_claim_is_named():
    """The exact regression. Three claims, one contradicted, and afterwards a reader of
    the run must be able to say which and why."""
    claims = [{"type": "QUOTE", "subject": "A Person", "claim": "a quote that is real"},
              {"type": "STUDY", "subject": "A Lab", "claim": "the study says X"},
              {"type": "STAT", "subject": "An Agency", "claim": "inflation reached 300%"}]
    fc = PerClaimChecker(claims, {
        "the study says X": ("CONTRADICTED", "no such study; the cited lab published "
                                             "nothing on this in 2026")})
    res = fc._run_web_fact_check("body", strict=True)
    r = bridge_for(res)

    check("B: bridge still FAILS", _check9(r)["ok"] is False, _check9(r))
    check("B: run is not eligible", r.eligible is False)
    check("B: aggregate contradicted is still 1", ev(r)["contradicted_count"] == 1, ev(r))

    bad = [f for f in ev(r)["findings"] if f["verdict"] == "CONTRADICTED"]
    check("B: exactly one contradicted finding", len(bad) == 1, bad)
    if bad:
        f = bad[0]
        check("B: the exact claim text is recorded",
              f["claim_text"] == "the study says X", f)
        check("B: the verdict is the existing vocabulary",
              f["verdict"] == "CONTRADICTED", f)
        check("B: the reason the checker gave is recorded",
              "no such study" in f["reason"], f["reason"])
        check("B: the type is recorded", f["type"] == "STUDY", f)
        check("B: the subject is recorded", f["subject"] == "A Lab", f)
        check("B: it is marked blocking", f["blocking"] is True, f)
    check("B: the clean claims are recorded too, not just the failure",
          sorted(x["claim_text"] for x in ev(r)["findings"])
          == ["a quote that is real", "inflation reached 300%", "the study says X"],
          ev(r)["findings"])
    check("B: a frozen run can answer 'which claim and why' from evidence alone",
          any(x["verdict"] == "CONTRADICTED" and x["reason"] and x["claim_text"]
              for x in json.loads(json.dumps(ev(r)))["findings"]))


# ── C ─────────────────────────────────────────────────────────────────────────
def test_C_unverifiable_and_advisory_keep_their_exact_semantics():
    claims = [{"type": "STAT", "subject": "Agency", "claim": "a soft stat"},
              {"type": "EVENT", "subject": "City", "claim": "an event happened"},
              {"type": "QUOTE", "subject": "Someone", "claim": "an unfindable quote"}]
    fc = PerClaimChecker(claims, {
        "a soft stat": ("CONTRADICTED", "the figure does not match the agency release"),
        "an unfindable quote": ("UNVERIFIABLE", "search returned nothing either way")})
    res = fc._run_web_fact_check("body", strict=True)

    check("C: a contradicted STAT is advisory, not blocking",
          len(res["advisory"]) == 1 and res["contradicted"] == [], res)
    check("C: soft_contradicted_count still counts it",
          res["soft_contradicted_count"] == 1, res)
    check("C: unverifiable still counted", res["unverifiable_count"] == 1, res)

    by_text = {f["claim_text"]: f for f in res["findings"]}
    check("C: the advisory claim is recorded with its verdict",
          by_text["a soft stat"]["verdict"] == "CONTRADICTED", by_text.get("a soft stat"))
    check("C: and marked NON-blocking",
          by_text["a soft stat"]["blocking"] is False, by_text["a soft stat"])
    check("C: its reason is recorded",
          "does not match" in by_text["a soft stat"]["reason"])
    check("C: the unverifiable claim is recorded",
          by_text["an unfindable quote"]["verdict"] == "UNVERIFIABLE")
    check("C: with its reason", "nothing either way"
          in by_text["an unfindable quote"]["reason"])

    r = bridge_for(res)
    check("C: an advisory contradiction alone does NOT block",
          _check9(r)["ok"] is True, _check9(r))
    check("C: counts surface in evidence",
          (ev(r)["advisory_count"], ev(r)["unverifiable_count"],
           ev(r)["soft_contradicted_count"]) == (1, 1, 1), ev(r))


# ── D ─────────────────────────────────────────────────────────────────────────
def test_D_identity_survives_duplicate_claim_text():
    """Two claims with identical text are two findings, and the blocking one is still
    identifiable. Position in check order is the identity, not the string."""
    same = "the same sentence twice"
    claims = [{"type": "STAT", "subject": "First", "claim": same},
              {"type": "STAT", "subject": "Second", "claim": same},
              {"type": "STAT", "subject": "Third", "claim": "a different one"}]

    class Positional(PerClaimChecker):
        def _web_verify_claim(self, ctype, subject, claim):
            return (("CONTRADICTED", "the second one is wrong")
                    if subject == "Second" else ("VERIFIED", "fine"))

    fc = Positional(claims, {})
    res = fc._run_web_fact_check("body", strict=True)
    ids = [f["claim_id"] for f in res["findings"]]
    check("D: ids are unique", len(set(ids)) == len(ids) == 3, ids)
    check("D: ids follow check order", ids == ["C01", "C02", "C03"], ids)
    dup = [f for f in res["findings"] if f["claim_text"] == same]
    check("D: both duplicates are present", len(dup) == 2, dup)
    check("D: they are distinguished by subject",
          sorted(f["subject"] for f in dup) == ["First", "Second"], dup)
    bad = [f for f in res["findings"] if f["verdict"] == "CONTRADICTED"]
    check("D: exactly one is contradicted and it is identifiable",
          len(bad) == 1 and bad[0]["subject"] == "Second"
          and bad[0]["claim_id"] == "C02", bad)
    # determinism
    again = Positional(claims, {})._run_web_fact_check("body", strict=True)
    check("D: the same input records the same findings",
          again["findings"] == res["findings"])


# ── E ─────────────────────────────────────────────────────────────────────────
def test_E_provider_and_parse_failure_stay_fail_closed():
    fc = StubFactChecker(boom=RuntimeError("provider exploded"))
    res = fc._run_web_fact_check("body", strict=True)
    r = bridge_for(res)
    check("E: still EXTRACTION_ERROR", res["extraction_status"] == "error", res)
    check("E: still does not claim completion",
          res["fact_check_completed"] is False, res)
    check("E: bridge still FAILS", _check9(r)["ok"] is False, _check9(r))
    check("E: not eligible", r.eligible is False)
    check("E: no findings are invented for claims never checked",
          ev(r)["findings"] == [] and ev(r)["claims_checked"] == 0, ev(r))
    check("E: the diagnostic error string is persisted",
          "provider exploded" in (ev(r)["extraction_error"] or ""),
          ev(r)["extraction_error"])

    # a malformed reply goes through the REAL parser, as before
    fc2 = StubFactChecker(raw='{"claims": []}{"claims": []}')
    res2 = fc2._run_web_fact_check("body", strict=True)
    r2 = bridge_for(res2)
    check("E: a malformed reply still fails closed", _check9(r2)["ok"] is False,
          _check9(r2))
    check("E: and records why", (ev(r2)["extraction_error"] or "") != ""
          or ev(r2)["extraction_status"] == "error", ev(r2))

    # zero claims: extraction worked, nothing checked, still not a pass
    fc3 = StubFactChecker(raw='{"claims": []}')
    res3 = fc3._run_web_fact_check("body", strict=True)
    r3 = bridge_for(res3)
    check("E: zero claims still fails closed", _check9(r3)["ok"] is False, _check9(r3))
    check("E: and records no findings", ev(r3)["findings"] == [])


# ── F ─────────────────────────────────────────────────────────────────────────
def test_F_no_hidden_reasoning_is_persisted():
    """Only the structured result and the stated reason. The reason is the checker's
    own REASON: field, which is an output; nothing here stores a thinking trace."""
    claims = [{"type": "STUDY", "subject": "Lab", "claim": "the study says X"}]
    fc = PerClaimChecker(claims, {
        "the study says X": ("CONTRADICTED", "no such study")})
    res = fc._run_web_fact_check("body", strict=True)
    r = bridge_for(res)
    keys = set()
    for f in ev(r)["findings"]:
        keys |= set(f)
    check("F: the finding schema is exactly the declared one",
          keys == {"claim_id", "type", "subject", "claim_text", "verdict", "reason",
                   "blocking"}, sorted(keys))
    blob = json.dumps(ev(r)).lower()
    for banned in ("chain_of_thought", "chain of thought", "reasoning_content",
                   "thinking", "<think", "scratchpad", "rationale_trace"):
        check("F: no %r in the persisted payload" % banned, banned not in blob)
    src = (HERE / "orchestrator" / "fact_check.py").read_text()
    for banned in ("reasoning_content", "chain_of_thought", "include_reasoning"):
        check("F: the checker does not request %r" % banned, banned not in src)
    check("F: the reason is the checker's stated REASON field",
          'REASON:' in src)


# ── G ─────────────────────────────────────────────────────────────────────────
def test_G_the_decision_itself_did_not_move():
    src = (HERE / "publication_safety_bridge.py").read_text()
    fcs = (HERE / "orchestrator" / "fact_check.py").read_text()
    check("G: blocking still means a contradicted list entry",
          'r.add("world_relative_fact_check", not contradicted,' in src)
    check("G: zero claims still fails closed", "NO_VERIFIABLE_CLAIMS" in src)
    check("G: extraction error still fails closed", "EXTRACTION_ERROR" in src)
    check("G: incompleteness still fails closed", "FACT_CHECK_INCOMPLETE" in src)
    check("G: a missing extraction_status still fails closed",
          "NON_STRICT_FACT_CHECK" in src)
    check("G: a STUDY contradiction still blocks and a STAT/EVENT still does not",
          'if c["type"] == "STUDY":' in fcs and 'result["advisory"].append(c)' in fcs)
    check("G: the claim cap is unchanged", "claim_cap=4" in fcs)
    check("G: the verify model is unchanged", 'model="perplexity/sonar"' in fcs)
    check("G: no retry was added",
          "for attempt in range" not in fcs.split("def _run_web_fact_check")[1]
          .split("\n    def ")[0])
    check("G: what the cap skipped is recorded, not silently passed",
          '"not_checked"' in fcs)

    # the aggregate keys callers already read are all still present
    claims = [{"type": "STAT", "subject": "A", "claim": "c"}]
    res = PerClaimChecker(claims, {})._run_web_fact_check("body", strict=True)
    for k in ("lines", "contradicted", "advisory", "unverifiable_count",
              "soft_contradicted_count", "extraction_status", "extraction_error",
              "claims_extracted", "fact_check_completed"):
        check("G: legacy result key %r still present" % k, k in res, sorted(res))
    r = bridge_for(res)
    for k in ("extraction_status", "claims_extracted", "fact_check_completed"):
        check("G: aggregate %r still in evidence" % k, k in ev(r), sorted(ev(r)))
    check("G: the run artefact is written the same plain way SAFETY_BRIDGE.json is",
          'FACT_CHECK.json' in (HERE / "new_engine_production.py").read_text())


def main() -> None:
    for fn in (test_A_all_clean_claims_are_all_recorded,
               test_B_the_one_contradicted_claim_is_named,
               test_C_unverifiable_and_advisory_keep_their_exact_semantics,
               test_D_identity_survives_duplicate_claim_text,
               test_E_provider_and_parse_failure_stay_fail_closed,
               test_F_no_hidden_reasoning_is_persisted,
               test_G_the_decision_itself_did_not_move):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL FACT-CHECK EVIDENCE TESTS PASSED")


if __name__ == "__main__":
    main()
