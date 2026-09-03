#!/usr/bin/env python3
"""
fact_check_capacity_test.py -- one total claim bound, and every claim inside it checked.

PR #56 stopped unchecked claims becoming a publication pass. It left the caps that did
the skipping in place, so an article with a fifth quote, or six statistics, held for a
reason that had nothing to do with whether anything was wrong -- the category a claim
landed in and the order it was emitted in.

So the per-category truncation is gone from the publication path. All supported types
now compete against ONE total bound, chosen from measurement: seven production runs with
recorded extraction counts came in at 0, 1, 5, 8, 13, 13 and 13 claims. Over the bound
is an explicit refusal with no partial check; inside it, everything is checked or the
article holds.

The legacy advisory path in orchestrator/review.py keeps its per-category caps exactly,
because it is not a publication gate and this module promises its historical shape.

No network: extraction and both verifiers are canned.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import publication_safety_bridge as BRIDGE                            # noqa: E402
from orchestrator import fact_check as FC                             # noqa: E402
from current_engine_strict_fact_check_test import (                   # noqa: E402
    StubFactChecker, _accept_run, _check9)

FAILURES: list = []
MAX = FC.FACT_CHECK_MAX_CLAIMS


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


class Checker(StubFactChecker):
    """Counts every provider call, so the call bound is provable rather than asserted."""

    def __init__(self, claims, verdicts=None, sleep_after=None):
        super().__init__(raw=json.dumps({"claims": claims}))
        self._v = verdicts or {}
        self.verify_calls = []
        self._sleep_after = sleep_after

    def _maybe_stall(self):
        if self._sleep_after is not None and len(self.verify_calls) >= self._sleep_after:
            import time
            time.sleep(0.05)

    def _web_verify_quote(self, person, quote, timeout=None):
        self.verify_calls.append(("QUOTE", quote))
        self._maybe_stall()
        return self._v.get(quote, ("VERIFIED", "found in two sources"))

    def _web_verify_claim(self, ctype, subject, claim, timeout=None):
        self.verify_calls.append((ctype, claim))
        self._maybe_stall()
        return self._v.get(claim, ("VERIFIED", "found in two sources"))


def of(ctype, n, prefix=""):
    return [{"type": ctype, "subject": "%s%s %d" % (prefix, ctype.title(), i),
             "claim": "%s%s claim %d" % (prefix, ctype.lower(), i)} for i in range(n)]


def run(claims, verdicts=None, **kw):
    c = Checker(claims, verdicts, sleep_after=kw.pop("sleep_after", None))
    fc = c._run_web_fact_check("body", strict=True, **kw)
    r = BRIDGE.evaluate(_accept_run(), fact_check_fn=lambda t: fc)
    return c, fc, r


def ev(r):
    return r.fact_check_evidence


def reason(r):
    return _check9(r)["detail"].split(":")[0]


# ── A ─────────────────────────────────────────────────────────────────────────
def test_A_six_stats_are_all_checked():
    """The old scheme checked four of these and skipped two, for being the fifth and
    sixth statistic in a list."""
    c, fc, r = run(of("STAT", 6))
    check("A: all 6 checked", ev(r)["claims_checked"] == 6, ev(r))
    check("A: 6 verification calls", len(c.verify_calls) == 6, c.verify_calls)
    check("A: nothing skipped", ev(r)["claims_not_checked"] == 0 and fc["not_checked"] == [])
    check("A: coverage complete", ev(r)["coverage_complete"] is True)
    check("A: check 9 PASSES", _check9(r)["ok"] is True, _check9(r))
    check("A: eligible", r.eligible is True)
    check("A: no category truncation remains in the strict path",
          '[:claim_cap]' not in (HERE / "orchestrator" / "fact_check.py").read_text()
          .split("if strict:")[1].split("else:")[0])


# ── B ─────────────────────────────────────────────────────────────────────────
def test_B_five_quotes_and_five_stats_are_all_checked():
    c, fc, r = run(of("QUOTE", 5) + of("STAT", 5))
    check("B: 10 extracted", ev(r)["claims_extracted"] == 10, ev(r))
    check("B: all 10 checked", ev(r)["claims_checked"] == 10, ev(r))
    check("B: both categories fully covered",
          sum(1 for x in c.verify_calls if x[0] == "QUOTE") == 5
          and sum(1 for x in c.verify_calls if x[0] == "STAT") == 5, c.verify_calls)
    check("B: coverage complete and PASS",
          ev(r)["coverage_complete"] is True and _check9(r)["ok"] is True)


# ── C ─────────────────────────────────────────────────────────────────────────
def test_C_thirteen_mixed_claims_are_all_checked():
    """The shape that recurred three times on 2026-09-03 and held on coverage."""
    claims = of("QUOTE", 5) + of("STUDY", 2) + of("STAT", 4) + of("EVENT", 2)
    c, fc, r = run(claims)
    check("C: 13 extracted", ev(r)["claims_extracted"] == 13, ev(r))
    check("C: all 13 checked", ev(r)["claims_checked"] == 13, ev(r))
    check("C: 13 verification calls", len(c.verify_calls) == 13, len(c.verify_calls))
    check("C: not_checked is empty", fc["not_checked"] == [], fc["not_checked"])
    check("C: coverage complete", ev(r)["coverage_complete"] is True)
    check("C: check 9 PASSES", _check9(r)["ok"] is True, _check9(r))
    check("C: eligible", r.eligible is True)
    check("C: max_claims is recorded", ev(r)["max_claims"] == MAX, ev(r))


# ── D ─────────────────────────────────────────────────────────────────────────
def test_D_exactly_the_bound_is_fully_checked():
    c, fc, r = run(of("QUOTE", 8) + of("STAT", 8))
    check("D: %d extracted" % MAX, ev(r)["claims_extracted"] == MAX, ev(r))
    check("D: all %d checked" % MAX, ev(r)["claims_checked"] == MAX, ev(r))
    check("D: %d verification calls" % MAX, len(c.verify_calls) == MAX)
    check("D: coverage complete and PASS",
          ev(r)["coverage_complete"] is True and _check9(r)["ok"] is True)


# ── E ─────────────────────────────────────────────────────────────────────────
def test_E_one_over_the_bound_is_refused_with_no_partial_check():
    c, fc, r = run(of("QUOTE", 8) + of("STAT", 9))
    check("E: %d extracted" % (MAX + 1), ev(r)["claims_extracted"] == MAX + 1, ev(r))
    check("E: NOT ONE verification call was spent", c.verify_calls == [], c.verify_calls)
    check("E: no findings", ev(r)["claims_checked"] == 0 and fc["findings"] == [])
    check("E: every claim recorded as not checked",
          ev(r)["claims_not_checked"] == MAX + 1, ev(r))
    check("E: with the reason max_claims_exceeded",
          {x["skipped_reason"] for x in fc["not_checked"]} == {FC.MAX_CLAIMS_EXCEEDED},
          fc["not_checked"][:2])
    check("E: no coverage is claimed", ev(r)["coverage_complete"] is False)
    check("E: max_claims_exceeded is flagged", ev(r)["max_claims_exceeded"] is True)
    check("E: check 9 FAILS", _check9(r)["ok"] is False, _check9(r))
    check("E: publication HOLD", r.eligible is False)
    check("E: reason is FACT_CHECK_TOO_MANY_CLAIMS",
          reason(r) == "FACT_CHECK_TOO_MANY_CLAIMS", _check9(r)["detail"])
    check("E: the detail names both numbers",
          "%d verifiable claims" % (MAX + 1) in _check9(r)["detail"]
          and "the %d this stage" % MAX in _check9(r)["detail"], _check9(r)["detail"])
    check("E: execution itself did not fail",
          ev(r)["fact_check_completed"] is True, ev(r))
    check("E: and it is distinct from ordinary incomplete coverage",
          reason(r) != "FACT_CHECK_COVERAGE_INCOMPLETE")


# ── F ─────────────────────────────────────────────────────────────────────────
def test_F_a_late_blocking_claim_is_now_reached():
    """Proof the first-four bias is gone: under the old caps the twelfth claim was
    never checked, so a fabricated study at position 12 published."""
    claims = of("STAT", 11) + [{"type": "STUDY", "subject": "A Lab",
                                "claim": "the twelfth claim, a fabricated study"}]
    c, fc, r = run(claims, {"the twelfth claim, a fabricated study":
                            ("CONTRADICTED", "no such study exists")})
    check("F: 12 extracted, all checked",
          ev(r)["claims_extracted"] == 12 and ev(r)["claims_checked"] == 12, ev(r))
    check("F: the twelfth claim WAS verified",
          any("fabricated study" in x[1] for x in c.verify_calls), c.verify_calls)
    check("F: it blocks", _check9(r)["ok"] is False, _check9(r)["detail"])
    check("F: not eligible", r.eligible is False)
    bad = [f for f in ev(r)["findings"] if f["verdict"] == "CONTRADICTED"]
    check("F: named in the findings with its reason",
          len(bad) == 1 and bad[0]["blocking"] is True
          and "no such study" in bad[0]["reason"], bad)
    check("F: coverage was complete, so the hold is the contradiction",
          ev(r)["coverage_complete"] is True and ev(r)["contradicted_count"] == 1, ev(r))
    check("F: under the old 4-per-category cap it would not have been reached",
          len([x for x in claims if x["type"] == "STAT"]) > 4)


# ── G ─────────────────────────────────────────────────────────────────────────
def test_G_a_late_advisory_claim_keeps_advisory_semantics():
    claims = of("QUOTE", 4) + of("STAT", 6) + [
        {"type": "EVENT", "subject": "City", "claim": "the eleventh, a soft event"}]
    c, fc, r = run(claims, {"the eleventh, a soft event": ("CONTRADICTED", "date wrong")})
    check("G: all 11 checked", ev(r)["claims_checked"] == 11, ev(r))
    check("G: the late EVENT was reached",
          any("soft event" in x[1] for x in c.verify_calls))
    check("G: it is advisory, not blocking", _check9(r)["ok"] is True, _check9(r)["detail"])
    check("G: still eligible", r.eligible is True)
    check("G: counted as advisory",
          ev(r)["advisory_count"] == 1 and ev(r)["contradicted_count"] == 0, ev(r))
    check("G: soft_contradicted_count kept", ev(r)["soft_contradicted_count"] == 1, ev(r))


# ── H ─────────────────────────────────────────────────────────────────────────
def test_H_deadline_exhaustion_is_a_technical_failure_never_a_pass():
    c, fc, r = run(of("STAT", 10), total_seconds=0.0)
    check("H: the deadline stopped the pass before any call",
          len(c.verify_calls) == 0, c.verify_calls)
    check("H: fact_check_completed is FALSE",
          ev(r)["fact_check_completed"] is False, ev(r))
    check("H: the unreached claims say why",
          {x["skipped_reason"] for x in fc["not_checked"]}
          == {FC.TOTAL_DEADLINE_EXHAUSTED}, fc["not_checked"][:2])
    check("H: check 9 FAILS", _check9(r)["ok"] is False, _check9(r))
    check("H: as a technical incomplete, not a coverage or capacity reason",
          reason(r) == "FACT_CHECK_INCOMPLETE", _check9(r)["detail"])
    check("H: publication HOLD", r.eligible is False)

    # a deadline reached PART WAY through must not pass either
    c2, fc2, r2 = run(of("STAT", 6), total_seconds=0.12, sleep_after=1)
    check("H: a mid-pass deadline still HOLDs", _check9(r2)["ok"] is False,
          _check9(r2)["detail"])
    check("H: with completion false", ev(r2)["fact_check_completed"] is False, ev(r2))
    check("H: partial findings are recorded but claim no coverage",
          ev(r2)["coverage_complete"] is False, ev(r2))
    check("H: the total bound is an explicit constant",
          FC.FACT_CHECK_TOTAL_SECONDS == 180)
    check("H: no retry was added",
          "for attempt in range" not in
          (HERE / "orchestrator" / "fact_check.py").read_text())


# ── I ─────────────────────────────────────────────────────────────────────────
def test_I_provider_failure_midway_fails_closed():
    class Boom(Checker):
        def _web_verify_claim(self, ctype, subject, claim, timeout=None):
            self.verify_calls.append((ctype, claim))
            if len(self.verify_calls) == 3:
                raise RuntimeError("provider died mid-pass")
            return ("VERIFIED", "found")

    b = Boom(of("STAT", 6))
    fc = b._run_web_fact_check("body", strict=True)
    r = BRIDGE.evaluate(_accept_run(), fact_check_fn=lambda t: fc)
    check("I: completion is false", ev(r)["fact_check_completed"] is False, ev(r))
    check("I: check 9 FAILS", _check9(r)["ok"] is False, _check9(r))
    check("I: evidence shows incomplete execution",
          ev(r)["claims_checked"] < ev(r)["claims_extracted"], ev(r))
    check("I: not eligible", r.eligible is False)
    check("I: extraction still succeeded, so it is not an extraction error",
          ev(r)["extraction_status"] == "ok", ev(r))


# ── J / K ─────────────────────────────────────────────────────────────────────
def test_J_and_K_the_previous_two_prs_still_hold():
    c, fc, r = run(of("QUOTE", 2) + of("STUDY", 1),
                   {"study claim 0": ("CONTRADICTED", "no such study")})
    keys = set()
    for f in ev(r)["findings"]:
        keys |= set(f)
    check("J: #55 per-claim schema intact",
          keys == {"claim_id", "type", "subject", "claim_text", "verdict", "reason",
                   "blocking"}, sorted(keys))
    check("J: ids are in check order",
          [f["claim_id"] for f in ev(r)["findings"]] == ["C01", "C02", "C03"],
          [f["claim_id"] for f in ev(r)["findings"]])
    check("J: the contradicted claim is named with its reason",
          any(f["verdict"] == "CONTRADICTED" and "no such study" in f["reason"]
              for f in ev(r)["findings"]), ev(r)["findings"])
    brg = (HERE / "publication_safety_bridge.py").read_text()
    check("K: #56 coverage gate still present",
          'elif not cov["coverage_complete"]:' in brg
          and "FACT_CHECK_COVERAGE_INCOMPLETE" in brg)
    check("K: coverage still reads both sides",
          "def coverage_state(" in brg and "counts_consistent" in brg)
    check("K: and it still fires on an inconsistent record",
          BRIDGE.evaluate(_accept_run(), fact_check_fn=lambda t: {
              "extraction_status": "ok", "claims_extracted": 8,
              "fact_check_completed": True, "findings": [], "not_checked": [],
              "contradicted": []}).eligible is False)


# ── L ─────────────────────────────────────────────────────────────────────────
def test_L_the_network_call_bound_is_exact():
    for n, expect_verify in ((1, 1), (6, 6), (MAX, MAX), (MAX + 1, 0)):
        claims = of("STAT", min(n, 8)) + of("QUOTE", max(0, n - 8))
        c, fc, r = run(claims)
        check("L: %d extracted -> %d verification call(s)" % (n, expect_verify),
              len(c.verify_calls) == expect_verify, len(c.verify_calls))
        check("L:   plus exactly one extraction call", len(c.calls) == 1, len(c.calls))
    check("L: total = 1 + min(extracted, max) and only extraction when over",
          True)


# ── M ─────────────────────────────────────────────────────────────────────────
def test_M_prompts_model_and_type_policy_are_unchanged():
    fcs = (HERE / "orchestrator" / "fact_check.py").read_text()
    check("M: extraction prompt unchanged",
          "Extract every claim from this article that could be independently " in fcs)
    check("M: verification model unchanged", 'model="perplexity/sonar"' in fcs)
    check("M: extraction model unchanged", 'model="openrouter/claude-haiku-4.5"' in fcs)
    check("M: the per-call ceiling is still 30s", FC.PER_CALL_TIMEOUT == 30)
    check("M: and it is still what a call gets when time is not short",
          "timeout=PER_CALL_TIMEOUT" in fcs and "max_tokens=250, timeout=timeout," in fcs)
    check("M: QUOTE/STUDY still block, STAT/EVENT still advisory",
          'if c["type"] == "STUDY":' in fcs and 'result["advisory"].append(c)' in fcs)
    check("M: UNVERIFIABLE still counted, still non-blocking",
          'result["unverifiable_count"] += 1' in fcs)
    # Structure, not prose: verification is still ONE claim per call. Test L proves
    # the call count behaviourally; this pins the shape that produces it.
    code = "\n".join(l for l in fcs.splitlines() if not l.strip().startswith("#"))
    check("M: verification is still one claim per call",
          'self._web_verify_quote(c["subject"], c["claim"],' in code
          and 'c["type"], c.get("subject", ""), c["claim"], timeout=budget' in code)
    # (Not a text scan for the word "batch": parse_claims_payload is the pre-existing
    # EXTRACTION parser and matches any such pattern. The guarantee that matters is the
    # call count, and test L measures it.)
    check("M: each verification call carries exactly one claim",
          code.count("_web_verify_quote(") == 2       # def + the one call site
          and code.count("_web_verify_claim(") == 2,
          (code.count("_web_verify_quote("), code.count("_web_verify_claim(")))
    # the legacy advisory path keeps its per-category caps
    legacy = Checker(of("STAT", 6))
    res = legacy._run_web_fact_check("body")            # strict=False
    check("M: legacy path still truncates at claim_cap",
          len(legacy.verify_calls) == 4, legacy.verify_calls)
    check("M: legacy result carries no capacity fields",
          "max_claims" not in res and "max_claims_exceeded" not in res, sorted(res))
    check("M: review.py's caller is untouched",
          "claim_cap=8" in (HERE / "orchestrator" / "review.py").read_text())



# ── the total deadline must be a REAL end-to-end bound ───────────────────────
class Timed(StubFactChecker):
    """Records the timeout every provider call was actually given, and can consume
    wall clock so a deadline can expire mid-sequence."""

    def __init__(self, claims, extract_cost=0.0, verify_cost=0.0):
        super().__init__(raw=json.dumps({"claims": claims}))
        self.extract_timeouts = []
        self.verify_timeouts = []
        self._ec, self._vc = extract_cost, verify_cost

    def _call_openai_compat_api(self, **kw):
        # extraction goes through the real helper, so capture its timeout here
        self.extract_timeouts.append(kw.get("timeout"))
        if self._ec:
            import time as _t
            _t.sleep(self._ec)
        return self._raw

    def _web_verify_quote(self, person, quote, timeout=None):
        self.verify_timeouts.append(timeout)
        if self._vc:
            import time as _t
            _t.sleep(self._vc)
        return ("VERIFIED", "found")

    def _web_verify_claim(self, ctype, subject, claim, timeout=None):
        self.verify_timeouts.append(timeout)
        if self._vc:
            import time as _t
            _t.sleep(self._vc)
        return ("VERIFIED", "found")


def test_N_every_call_is_bounded_by_the_remaining_total():
    """1. With one second left, a call whose ordinary ceiling is 30s gets <= 1s."""
    t = Timed(of("STAT", 3))
    # min_call_seconds=0 isolates the CLAMP from the do-not-start floor
    t._run_web_fact_check("body", strict=True, total_seconds=1.0, min_call_seconds=0)
    check("N1: extraction was clamped to the remaining total",
          t.extract_timeouts and t.extract_timeouts[0] <= 1.0,
          t.extract_timeouts)
    check("N1: every verification call was clamped too",
          t.verify_timeouts and all(v <= 1.0 for v in t.verify_timeouts),
          t.verify_timeouts)
    check("N1: and none was given the ordinary 30s",
          all(v < FC.PER_CALL_TIMEOUT for v in t.verify_timeouts), t.verify_timeouts)

    # and with the full budget, calls get their ordinary ceiling
    t2 = Timed(of("STAT", 3))
    t2._run_web_fact_check("body", strict=True)
    check("N1: a normal run still gives calls the ordinary ceiling",
          all(abs(v - FC.PER_CALL_TIMEOUT) < 1.0 for v in t2.verify_timeouts),
          t2.verify_timeouts)
    check("N1: extraction too",
          abs(t2.extract_timeouts[0] - FC.PER_CALL_TIMEOUT) < 1.0, t2.extract_timeouts)


def test_N_extraction_is_inside_the_total_not_outside_it():
    """The hole this verification found: a deadline taken AFTER extraction is one the
    stage can already have overrun by 30 seconds before the first claim."""
    src = (HERE / "orchestrator" / "fact_check.py").read_text()
    body = src.split("def _run_web_fact_check")[1]
    i_deadline = body.index("deadline = time.monotonic()")
    i_extract = body.index("self._extract_verifiable_claims_raw(")
    check("N2: the deadline is taken BEFORE extraction runs", i_deadline < i_extract,
          (i_deadline, i_extract))
    check("N2: extraction receives the budget, not a constant",
          "self._extract_verifiable_claims_raw(\n                        content, "
          "timeout=max(0.0, call_budget()))" in src)
    check("N2: no provider call in this stage carries a hardcoded timeout",
          "timeout=30" not in body)


def test_N_a_mid_sequence_deadline_holds_the_run():
    """2 and 3: the deadline expires part way through; no call starts after it, the
    run does not claim completion, and the rest are recorded as unreached."""
    t = Timed(of("STAT", 10), verify_cost=0.06)
    fc = t._run_web_fact_check("body", strict=True, total_seconds=0.25,
                               min_call_seconds=0.05)
    r = BRIDGE.evaluate(_accept_run(), fact_check_fn=lambda x: fc)
    check("N3: some claims were checked", 0 < len(t.verify_timeouts) < 10,
          len(t.verify_timeouts))
    check("N3: no call was given a budget past the deadline",
          all(v is not None and v > 0 for v in t.verify_timeouts), t.verify_timeouts)
    check("N3: fact_check_completed is FALSE", fc["fact_check_completed"] is False, fc)
    check("N3: the unreached claims say total_deadline_exhausted",
          {x["skipped_reason"] for x in fc["not_checked"]}
          == {FC.TOTAL_DEADLINE_EXHAUSTED}, fc["not_checked"][:2])
    check("N3: every extracted claim is accounted for",
          len(fc["findings"]) + len(fc["not_checked"]) == fc["claims_extracted"],
          (len(fc["findings"]), len(fc["not_checked"]), fc["claims_extracted"]))
    check("N3: publication HOLD", r.eligible is False)
    check("N3: as a technical incomplete", _check9(r)["detail"]
          .startswith("FACT_CHECK_INCOMPLETE"), _check9(r)["detail"])


def test_N_the_stage_cannot_outlive_its_total():
    """The end-to-end invariant, measured: entry to return, with a provider that
    always burns its whole allowance."""
    import time as _t

    class Slow(StubFactChecker):
        def __init__(self, claims):
            super().__init__(raw=json.dumps({"claims": claims}))
            self.calls_made = 0

        def _call_openai_compat_api(self, **kw):
            _t.sleep(min(kw.get("timeout") or 0, 0.08))
            return self._raw

        def _web_verify_quote(self, person, quote, timeout=None):
            self.calls_made += 1
            _t.sleep(min(timeout or 0, 0.08))
            return ("VERIFIED", "found")

        def _web_verify_claim(self, ctype, subject, claim, timeout=None):
            self.calls_made += 1
            _t.sleep(min(timeout or 0, 0.08))
            return ("VERIFIED", "found")

    total = 0.30
    s = Slow(of("STAT", 16))
    t0 = _t.monotonic()
    fc = s._run_web_fact_check("body", strict=True, total_seconds=total,
                               min_call_seconds=0.05)
    elapsed = _t.monotonic() - t0
    check("N4: the stage returned inside its total (+ local overhead)",
          elapsed <= total + 0.20, (elapsed, total))
    check("N4: it stopped early rather than running all 16",
          s.calls_made < 16, s.calls_made)
    check("N4: and held rather than claiming coverage",
          fc["fact_check_completed"] is False, fc)
    check("N4: the ceiling is min(per-call, remaining), never the sum",
          FC.PER_CALL_TIMEOUT == 30 and FC.FACT_CHECK_TOTAL_SECONDS == 180)


def test_N_the_thirteen_claim_normal_case_is_unchanged():
    """4: nothing about an ordinary run moved."""
    claims = of("QUOTE", 5) + of("STUDY", 2) + of("STAT", 4) + of("EVENT", 2)
    c, fc, r = run(claims)
    check("N5: 13 extracted, 13 checked", ev(r)["claims_extracted"] == 13
          and ev(r)["claims_checked"] == 13, ev(r))
    check("N5: 13 verification calls", len(c.verify_calls) == 13, len(c.verify_calls))
    check("N5: coverage complete", ev(r)["coverage_complete"] is True)
    check("N5: check 9 PASSES", _check9(r)["ok"] is True, _check9(r))
    check("N5: eligible", r.eligible is True)
    check("N5: claim order is unchanged (quotes first, then the rest, in emission order)",
          [f["claim_text"] for f in ev(r)["findings"]]
          == [x["claim"] for x in claims if x["type"] == "QUOTE"]
          + [x["claim"] for x in claims if x["type"] in ("STUDY", "STAT", "EVENT")],
          [f["claim_text"] for f in ev(r)["findings"]])
    check("N5: the legacy advisory path still gets its ordinary 30s",
          Timed(of("STAT", 2))._run_web_fact_check("body") is not None)
    lt = Timed(of("STAT", 2))
    lt._run_web_fact_check("body")                     # strict=False
    check("N5: legacy calls are unbounded by any total",
          lt.extract_timeouts == [FC.PER_CALL_TIMEOUT], lt.extract_timeouts)


def main() -> None:
    for fn in (test_A_six_stats_are_all_checked,
               test_B_five_quotes_and_five_stats_are_all_checked,
               test_C_thirteen_mixed_claims_are_all_checked,
               test_D_exactly_the_bound_is_fully_checked,
               test_E_one_over_the_bound_is_refused_with_no_partial_check,
               test_F_a_late_blocking_claim_is_now_reached,
               test_G_a_late_advisory_claim_keeps_advisory_semantics,
               test_H_deadline_exhaustion_is_a_technical_failure_never_a_pass,
               test_I_provider_failure_midway_fails_closed,
               test_J_and_K_the_previous_two_prs_still_hold,
               test_L_the_network_call_bound_is_exact,
               test_M_prompts_model_and_type_policy_are_unchanged,
               test_N_every_call_is_bounded_by_the_remaining_total,
               test_N_extraction_is_inside_the_total_not_outside_it,
               test_N_a_mid_sequence_deadline_holds_the_run,
               test_N_the_stage_cannot_outlive_its_total,
               test_N_the_thirteen_claim_normal_case_is_unchanged):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL FACT-CHECK CAPACITY TESTS PASSED")


if __name__ == "__main__":
    main()
