#!/usr/bin/env python3
"""
current_engine_strict_fact_check_test.py -- regression suite for the CURRENT_ENGINE
strict world-relative fact-check contract.

THE DEFECT THIS LOCKS OUT
On 2026-08-25 the first natural CURRENT_ENGINE run
(production-20260825T070003Z-5a5f17d6) logged

    Verifiable-claim extraction failed: Extra data: line 15 column 1 (char 394)

and then published-eligible metadata anyway. `_extract_verifiable_claims` caught the
parse error and returned [], `_run_web_fact_check` reported contradicted=[] advisory=[]
unverifiable=0, and publication-safety check 9 read that absence of contradictions as a
pass. It stamped fact_check_status: verified and publication_eligible: true on a draft
against which no world-relative check had ever run.

Check 9 is the only bridge check that leaves the source-relative chain -- checks 1-8 can
all pass while a source faithfully repeats something false about the world. So an
extraction failure must never be indistinguishable from a clean verification.

WHAT IS ASSERTED (A-H)
  A  extraction raises                       -> bridge FAIL, no verified stamp
  B  malformed multi-object "Extra data"     -> bridge FAIL (the real 08-25 shape)
  C  extraction ok, zero claims              -> bridge FAIL (NO_VERIFIABLE_CLAIMS)
  D  extraction ok, >0 claims, no contra     -> bridge PASS, stamp carries the evidence
  E  extraction ok, >0 claims, contradiction -> bridge FAIL (existing policy)
  F  CURRENT_ENGINE candidate, verified+eligible but no extraction status -> SKIP
  G  CURRENT_ENGINE candidate, claims_extracted 0                        -> SKIP
  H  legacy candidate behaviour unchanged

Added 2026-08-27 (strict claim-extraction robustness). The 08-25 defect above was
only half of the collapse: an extraction failure that RAISED became visible, but a
provider reply that came back empty, truncated, prose-only or malformed did not
raise at all -- the greedy `\{.*\}` match simply found nothing and the extractor
returned [], so the bridge recorded extraction_status=ok / claims_extracted=0, which
is byte-identical to a model that read the article and honestly found no claims.
  I  unreadable reply (empty/None/whitespace/prose/truncated/malformed) -> EXTRACTION_ERROR
  J  genuine {"claims": []}                    -> extraction OK, still NO_VERIFIABLE_CLAIMS
  K  direct / fenced / prose-wrapped payloads  -> extracted normally
  L  two competing claims payloads             -> EXTRACTION_ERROR, never guessed or merged
  M  the extraction call is pinned temperature=0

No network, no model calls, no publication.

Run (from repo root):
  python3 automation/current_engine_strict_fact_check_test.py
"""

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import publication_safety_bridge as BRIDGE                   # noqa: E402
import publish_best as PB                                    # noqa: E402
from new_engine_v1 import runner as R                        # noqa: E402
from research_pack_fixture import stub_pack             # noqa: E402
from new_engine_v1_test import StubProvider, _source_payload, AT   # noqa: E402

sys.path.insert(0, str(HERE / "orchestrator"))
from orchestrator.fact_check import (                        # noqa: E402
    FactCheckMixin, EXTRACTION_OK, EXTRACTION_ERROR)

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


# ── a fact-checker with no network ────────────────────────────────────────────
class _Log:
    def __init__(self):
        self.warnings = []

    def warning(self, msg, *a):
        self.warnings.append(msg % a if a else msg)

    info = debug = error = warning


class StubFactChecker(FactCheckMixin):
    """FactCheckMixin with the one network call replaced by a canned response.

    `raw` is returned verbatim as the extractor's model output, so a malformed body
    exercises the REAL parsing path rather than a hand-simulated exception. `boom`
    raises instead, standing in for a provider/transport failure.
    """

    def __init__(self, raw=None, boom=None, verdicts=None):
        self.logger = _Log()
        self._raw = raw
        self._boom = boom
        self._verdicts = verdicts or {}
        self.calls = []                      # kwargs of every extraction call made

    def _call_openai_compat_api(self, **kw):
        self.calls.append(kw)
        if self._boom is not None:
            raise self._boom
        return self._raw

    def _web_verify_quote(self, person, quote, timeout=None):
        return self._verdicts.get("QUOTE", ("VERIFIED", "found"))

    def _web_verify_claim(self, ctype, subject, claim, timeout=None):
        return self._verdicts.get(ctype, ("VERIFIED", "found"))


def _claims_json(n, ctype="STAT"):
    return json.dumps({"claims": [{"type": ctype, "subject": "Org %d" % i,
                                   "claim": "claim number %d" % i} for i in range(n)]})


# The exact 08-25 failure shape: two JSON objects concatenated. The extractor's
# greedy `\{.*\}` spans both, and json.loads raises "Extra data: line N column 1".
MULTI_OBJECT_RAW = '{"claims": [{"type": "STAT", "subject": "A", "claim": "x"}]}\n{"note": "trailing second object"}'


def _accept_run():
    with tempfile.TemporaryDirectory() as d:
        return R.run(_source_payload(), pathlib.Path(d), StubProvider(), "v", AT,
                     mode=R.MODE_LIVE, research_fn=stub_pack)


def _bridge_with(fc_result):
    return BRIDGE.evaluate(_accept_run(), fact_check_fn=lambda text: fc_result)


def _check9(r):
    return next(c for c in r.checks if c["check"] == "world_relative_fact_check")


# ── A. extraction exception fails closed ──────────────────────────────────────
def test_A_extraction_exception_fails_closed():
    fc = StubFactChecker(boom=RuntimeError("provider exploded"))
    res = fc._run_web_fact_check("body", strict=True)
    check("A: strict result reports EXTRACTION_ERROR",
          res["extraction_status"] == EXTRACTION_ERROR, res)
    check("A: strict result does not claim completion",
          res["fact_check_completed"] is False, res)
    check("A: strict result extracted zero claims", res["claims_extracted"] == 0, res)
    check("A: the failure is logged", any("extraction failed" in w
                                          for w in fc.logger.warnings), fc.logger.warnings)

    r = _bridge_with(res)
    check("A: bridge check 9 FAILS", _check9(r)["ok"] is False, _check9(r))
    check("A: bridge detail names EXTRACTION_ERROR",
          "EXTRACTION_ERROR" in _check9(r)["detail"], _check9(r)["detail"])
    check("A: candidate is not eligible", r.eligible is False)
    stamp = BRIDGE.stamp_fields(r)
    check("A: no verified stamp", stamp.get("fact_check_status") != "verified", stamp)
    check("A: publication_eligible is not true",
          stamp.get("publication_eligible") is not True, stamp)
    check("A: blocked_by names the fact check",
          "world_relative_fact_check" in stamp.get("publication_safety_blocked_by", ""), stamp)

    # legacy path is deliberately untouched: it still swallows and returns []
    legacy = fc._run_web_fact_check("body")
    check("A: legacy (non-strict) shape unchanged -- no strict keys leak in",
          "extraction_status" not in legacy and legacy["contradicted"] == [], legacy)


# ── B. the real malformed-response shape ──────────────────────────────────────
def test_B_multi_object_extra_data_fails_closed():
    fc = StubFactChecker(raw=MULTI_OBJECT_RAW)
    res = fc._run_web_fact_check("body", strict=True)
    # This assertion used to require the literal string "Extra data" -- the symptom
    # of the greedy `\{.*\}` match, which spanned both objects and handed a
    # two-object string to json.loads. The deterministic parser no longer produces
    # that error; it refuses the reply for the real reason instead. The outcome the
    # test exists to protect -- EXTRACTION_ERROR, never a silent zero -- is unchanged.
    check("B: multi-object response is refused as ambiguous, not parsed",
          "ambiguous" in (res.get("extraction_error") or ""), res)
    check("B: reported as EXTRACTION_ERROR, not as zero claims",
          res["extraction_status"] == EXTRACTION_ERROR, res)
    r = _bridge_with(res)
    check("B: bridge check 9 FAILS", _check9(r)["ok"] is False, _check9(r))
    check("B: candidate is not eligible", r.eligible is False)
    check("B: no verified stamp",
          BRIDGE.stamp_fields(r).get("fact_check_status") != "verified")

    # and the legacy swallow is exactly what the 08-25 run hit
    legacy = fc._run_web_fact_check("body")
    check("B: legacy path still returns the vacuous clean result "
          "(which is why CURRENT_ENGINE must not use it)",
          legacy["contradicted"] == [] and "extraction_status" not in legacy, legacy)


# ── C. zero claims fails closed ───────────────────────────────────────────────
def test_C_zero_claims_fails_closed():
    fc = StubFactChecker(raw='{"claims": []}')
    res = fc._run_web_fact_check("body", strict=True)
    check("C: extraction status is ok", res["extraction_status"] == EXTRACTION_OK, res)
    check("C: claims_extracted is 0", res["claims_extracted"] == 0, res)
    check("C: reported as NO_VERIFIABLE_CLAIMS", res["lines"] == ["NO_VERIFIABLE_CLAIMS"], res)

    r = _bridge_with(res)
    check("C: bridge check 9 FAILS on zero claims", _check9(r)["ok"] is False, _check9(r))
    check("C: bridge detail names NO_VERIFIABLE_CLAIMS",
          "NO_VERIFIABLE_CLAIMS" in _check9(r)["detail"], _check9(r)["detail"])
    check("C: candidate is not eligible", r.eligible is False)
    check("C: no verified stamp",
          BRIDGE.stamp_fields(r).get("fact_check_status") != "verified")


# ── D. a real successful strict check passes ──────────────────────────────────
def test_D_real_strict_check_passes():
    fc = StubFactChecker(raw=_claims_json(3))
    res = fc._run_web_fact_check("body", strict=True)
    check("D: extraction ok", res["extraction_status"] == EXTRACTION_OK, res)
    check("D: 3 claims extracted", res["claims_extracted"] == 3, res)
    check("D: verification completed", res["fact_check_completed"] is True, res)
    check("D: nothing contradicted", res["contradicted"] == [], res)

    r = _bridge_with(res)
    check("D: bridge check 9 PASSES", _check9(r)["ok"] is True, _check9(r))
    check("D: detail proves execution, not just absence of contradictions",
          "claims_extracted=3" in _check9(r)["detail"], _check9(r)["detail"])
    check("D: candidate is eligible", r.eligible is True,
          [c for c in r.checks if not c["ok"]])
    stamp = BRIDGE.stamp_fields(r)
    check("D: verified stamp is granted", stamp["fact_check_status"] == "verified", stamp)
    check("D: stamp carries extraction status evidence",
          stamp["fact_check_extraction_status"] == "ok", stamp)
    check("D: stamp carries the claim count",
          stamp["fact_check_claims_extracted"] == 3, stamp)
    check("D: bridge summary records the evidence for the run record",
          r.summary()["fact_check_evidence"]["claims_extracted"] == 3, r.summary())


# ── E. a contradiction still blocks ───────────────────────────────────────────
def test_E_contradiction_still_blocks():
    fc = StubFactChecker(raw=_claims_json(2, "STUDY"),
                         verdicts={"STUDY": ("CONTRADICTED", "no such report")})
    res = fc._run_web_fact_check("body", strict=True)
    check("E: extraction ok and claims found",
          res["extraction_status"] == EXTRACTION_OK and res["claims_extracted"] == 2, res)
    check("E: contradiction recorded", len(res["contradicted"]) == 2, res)
    r = _bridge_with(res)
    check("E: bridge check 9 FAILS under the existing policy",
          _check9(r)["ok"] is False, _check9(r))
    check("E: candidate is not eligible", r.eligible is False)
    check("E: no verified stamp",
          BRIDGE.stamp_fields(r).get("fact_check_status") != "verified")


# ── E2. a non-strict result can never satisfy CURRENT_ENGINE ──────────────────
def test_E2_non_strict_result_fails_closed():
    legacy_shape = {"contradicted": [], "advisory": [], "unverifiable_count": 0,
                    "soft_contradicted_count": 0}
    r = _bridge_with(legacy_shape)
    check("E2: a legacy-shaped clean result does NOT pass check 9",
          _check9(r)["ok"] is False, _check9(r))
    check("E2: detail names the missing strict contract",
          "NON_STRICT_FACT_CHECK" in _check9(r)["detail"], _check9(r)["detail"])
    check("E2: no fact-check function at all still fails closed",
          BRIDGE.evaluate(_accept_run(), fact_check_fn=None).eligible is False)


# ── F/G. selector defense in depth ────────────────────────────────────────────
_CE_BASE = {"engine_generation": "CURRENT_ENGINE", "editorial_engine": "NEW_ENGINE_V1",
            "publication_eligible": "true", "fact_check_status": "verified",
            "publication_safety_version": "1",
            "publication_safety_profile": "CURRENT_ENGINE_V1"}


def _selector_skips(fm):
    """Mirror the selector's CURRENT_ENGINE gate order for one candidate."""
    bad, why = PB._current_engine_ineligible(fm)
    if bad:
        return True, why
    bad, why = PB._current_engine_strict_fact_check_missing(fm)
    if bad:
        return True, why
    if PB._interlocked(fm):
        return True, "interlocked"
    if not PB._ordinary_eligibility_ok(fm):
        return True, "fact_check_status not verified"
    if not PB._current_safety_contract_ok(fm):
        return True, "safety version too low"
    return False, ""


def test_F_current_engine_without_extraction_status_is_skipped():
    fm = dict(_CE_BASE)                                   # no extraction evidence at all
    skip, why = _selector_skips(fm)
    check("F: verified + eligible but no extraction status -> SKIP", skip is True, fm)
    check("F: skip reason names fact_check_extraction_status",
          "fact_check_extraction_status" in why, why)

    fm_err = dict(_CE_BASE, fact_check_extraction_status="error",
                  fact_check_claims_extracted="0")
    check("F: an explicit extraction error -> SKIP", _selector_skips(fm_err)[0] is True)

    fm_junk = dict(_CE_BASE, fact_check_extraction_status="OK-ish",
                   fact_check_claims_extracted="4")
    check("F: a non-'ok' status string -> SKIP", _selector_skips(fm_junk)[0] is True)


def test_G_current_engine_zero_claims_is_skipped():
    fm = dict(_CE_BASE, fact_check_extraction_status="ok",
              fact_check_claims_extracted="0")
    skip, why = _selector_skips(fm)
    check("G: extraction ok but 0 claims -> SKIP", skip is True, fm)
    check("G: skip reason names fact_check_claims_extracted",
          "fact_check_claims_extracted" in why, why)

    fm_bad = dict(_CE_BASE, fact_check_extraction_status="ok",
                  fact_check_claims_extracted="not-a-number")
    check("G: unparseable claim count -> SKIP", _selector_skips(fm_bad)[0] is True)

    fm_ok = dict(_CE_BASE, fact_check_extraction_status="ok",
                 fact_check_claims_extracted="3")
    check("G: a fully evidenced CURRENT_ENGINE candidate is NOT skipped",
          _selector_skips(fm_ok)[0] is False, _selector_skips(fm_ok))


def test_G2_guard_is_actually_wired_into_the_selector():
    src = (HERE / "publish_best.py").read_text()
    check("G2: selector calls the strict guard",
          "_current_engine_strict_fact_check_missing(fm)" in src)
    check("G2: skip is printed with a named reason code",
          "CURRENT_ENGINE_FACT_CHECK_UNPROVEN" in src)
    check("G2: the guard does not re-run any fact check",
          "_run_web_fact_check" not in src and "_web_verify" not in src)
    prod = (HERE / "new_engine_production.py").read_text()
    check("G2: production passes strict=True to the bridge's fact check",
          "strict=True" in prod)


# ── H. legacy candidates unchanged ────────────────────────────────────────────
def test_H_legacy_candidate_behaviour_unchanged():
    legacy_ok = {"fact_check_status": "verified", "publication_safety_version": "1"}
    check("H: legacy candidate with no engine_generation is not touched by the guard",
          PB._current_engine_strict_fact_check_missing(legacy_ok) == (False, ""))
    check("H: legacy candidate still selectable without any strict fields",
          _selector_skips(legacy_ok)[0] is False, _selector_skips(legacy_ok))
    check("H: legacy blocked still blocked",
          _selector_skips({"fact_check_status": "blocked",
                           "publication_safety_version": "1"})[0] is True)
    check("H: legacy missing fact_check_status still held",
          _selector_skips({"publication_safety_version": "1"})[0] is True)
    check("H: legacy safety-version gate intact",
          _selector_skips({"fact_check_status": "verified"})[0] is True)
    check("H: guard ignores a non-CURRENT_ENGINE engine_generation too",
          PB._current_engine_strict_fact_check_missing(
              {"engine_generation": "LEGACY"}) == (False, ""))


def test_H2_bridge_and_fact_check_constants_agree():
    check("H2: bridge and fact_check agree on 'ok'", BRIDGE.FC_EXTRACTION_OK == EXTRACTION_OK)
    check("H2: bridge and fact_check agree on 'error'",
          BRIDGE.FC_EXTRACTION_ERROR == EXTRACTION_ERROR)




# ── I. an unreadable provider reply is an EXTRACTION_ERROR, never a zero ──────
# The 2026-08-27 natural run (production-20260827T070010Z-fd846f06) recorded
# extraction_status=ok / claims_extracted=0 and was blocked as NO_VERIFIABLE_CLAIMS.
# Read-only replay of that exact article returned 1-3 claims in 25/25 attempts and
# never 0, while CLIProxy logged four 502s inside the same 61-second window. The
# recorded evidence could not tell "the model read the article and found nothing"
# apart from "the model returned nothing readable", because every unreadable shape
# below reached the bridge as a successful extraction of zero claims.
_UNREADABLE = [
    ("empty string", ""),
    ("None", None),
    ("whitespace only", "   \n\t "),
    ("prose with no JSON payload", "I could not analyse this article."),
    ("truncated JSON", '```json\n{"claims": [{"type": "QUOTE"'),
    ("malformed JSON", '{"claims": [oops]}'),
    ("JSON without a claims list", '{"result": "none"}'),
]


def test_I_unreadable_provider_reply_is_extraction_error():
    for label, raw in _UNREADABLE:
        fc = StubFactChecker(raw=raw)
        res = fc._run_web_fact_check("body", strict=True)
        check("I[%s]: EXTRACTION_ERROR, not ok" % label,
              res["extraction_status"] == EXTRACTION_ERROR, res)
        check("I[%s]: not reported as NO_VERIFIABLE_CLAIMS" % label,
              res["lines"] != ["NO_VERIFIABLE_CLAIMS"], res)
        check("I[%s]: completion is not asserted" % label,
              res["fact_check_completed"] is False, res)
        check("I[%s]: an error string is recorded" % label,
              bool(res.get("extraction_error")), res)
        r = _bridge_with(res)
        check("I[%s]: bridge check 9 FAILS" % label, _check9(r)["ok"] is False, _check9(r))
        check("I[%s]: bridge names EXTRACTION_ERROR" % label,
              "EXTRACTION_ERROR" in _check9(r)["detail"], _check9(r)["detail"])
        check("I[%s]: candidate is not eligible" % label, r.eligible is False)
        check("I[%s]: no verified stamp" % label,
              BRIDGE.stamp_fields(r).get("fact_check_status") != "verified")


# ── J. a genuine empty claim list is still a SUCCESSFUL extraction ────────────
def test_J_genuine_zero_is_not_an_extraction_error():
    fc = StubFactChecker(raw='{"claims": []}')
    res = fc._run_web_fact_check("body", strict=True)
    check("J: genuine zero extracts successfully", res["extraction_status"] == EXTRACTION_OK, res)
    check("J: zero claims", res["claims_extracted"] == 0, res)
    check("J: no error string recorded", not res.get("extraction_error"), res)
    check("J: still fails closed as NO_VERIFIABLE_CLAIMS",
          res["lines"] == ["NO_VERIFIABLE_CLAIMS"], res)
    check("J: extraction did run to completion", res["fact_check_completed"] is True, res)
    r = _bridge_with(res)
    check("J: bridge check 9 FAILS", _check9(r)["ok"] is False, _check9(r))
    check("J: bridge names NO_VERIFIABLE_CLAIMS, not EXTRACTION_ERROR",
          "NO_VERIFIABLE_CLAIMS" in _check9(r)["detail"]
          and "EXTRACTION_ERROR" not in _check9(r)["detail"], _check9(r)["detail"])
    check("J: candidate is not eligible", r.eligible is False)

    # the distinction the fix exists for: same claim count, different status
    bad = StubFactChecker(raw="")._run_web_fact_check("body", strict=True)
    check("J: genuine zero and unreadable reply are distinguishable",
          res["extraction_status"] != bad["extraction_status"]
          and res["claims_extracted"] == bad["claims_extracted"] == 0,
          (res["extraction_status"], bad["extraction_status"]))


# ── K. the reply shapes a compliant model actually returns still work ─────────
_READABLE = [
    ("direct valid JSON", _claims_json(2), 2),
    ("one fenced payload", "```json\n" + _claims_json(3) + "\n```", 3),
    ("fenced payload wrapped in prose",
     "Here you go:\n```json\n" + _claims_json(1) + "\n```\nHope that helps.", 1),
    # greedy `\{.*\}` ran to the LAST brace in the reply, so a closing brace in
    # trailing prose corrupted an otherwise valid payload.
    ("valid payload then prose containing a stray brace",
     _claims_json(2) + "\nNote: see item 3} for detail", 2),
    ("a brace inside a claim string",
     '{"claims": [{"type": "STAT", "subject": "A", "claim": "uses {braces} inside"}]}', 1),
]


def test_K_valid_payload_shapes_extract_normally():
    for label, raw, n in _READABLE:
        fc = StubFactChecker(raw=raw)
        res = fc._run_web_fact_check("body", strict=True)
        check("K[%s]: extraction ok" % label, res["extraction_status"] == EXTRACTION_OK, res)
        check("K[%s]: %d claim(s) extracted" % (label, n), res["claims_extracted"] == n, res)
        check("K[%s]: verification completed" % label, res["fact_check_completed"] is True, res)


# ── L. competing payloads fail closed rather than being guessed at ────────────
_AMBIGUOUS = [
    ("two claims payloads (self-correcting model)",
     "```json\n" + _claims_json(1) + "\n```\nActually, on review:\n```json\n"
     + _claims_json(3) + "\n```"),
    ("claims payload plus a trailing object", MULTI_OBJECT_RAW),
]


def test_L_ambiguous_payloads_fail_closed():
    for label, raw in _AMBIGUOUS:
        fc = StubFactChecker(raw=raw)
        res = fc._run_web_fact_check("body", strict=True)
        check("L[%s]: EXTRACTION_ERROR" % label,
              res["extraction_status"] == EXTRACTION_ERROR, res)
        check("L[%s]: refused as ambiguous" % label,
              "ambiguous" in (res.get("extraction_error") or ""), res)
        check("L[%s]: no claims were guessed at or merged" % label,
              res["claims_extracted"] == 0, res)
        r = _bridge_with(res)
        check("L[%s]: candidate is not eligible" % label, r.eligible is False)


# ── M. extraction is pinned to temperature=0 ──────────────────────────────────
def test_M_extraction_is_pinned_to_temperature_zero():
    fc = StubFactChecker(raw=_claims_json(1))
    fc._run_web_fact_check("body", strict=True)
    check("M: the extraction call was made", len(fc.calls) >= 1, fc.calls)
    kw = fc.calls[0]
    check("M: temperature is passed explicitly", "temperature" in kw, kw)
    check("M: temperature is 0", kw.get("temperature") == 0, kw)
    check("M: still the cheap extraction model",
          kw.get("model") == "openrouter/claude-haiku-4.5", kw)


def main():
    for fn in [test_A_extraction_exception_fails_closed,
               test_B_multi_object_extra_data_fails_closed,
               test_C_zero_claims_fails_closed,
               test_D_real_strict_check_passes,
               test_E_contradiction_still_blocks,
               test_E2_non_strict_result_fails_closed,
               test_F_current_engine_without_extraction_status_is_skipped,
               test_G_current_engine_zero_claims_is_skipped,
               test_G2_guard_is_actually_wired_into_the_selector,
               test_H_legacy_candidate_behaviour_unchanged,
               test_H2_bridge_and_fact_check_constants_agree,
               test_I_unreadable_provider_reply_is_extraction_error,
               test_J_genuine_zero_is_not_an_extraction_error,
               test_K_valid_payload_shapes_extract_normally,
               test_L_ambiguous_payloads_fail_closed,
               test_M_extraction_is_pinned_to_temperature_zero]:
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL STRICT FACT-CHECK REGRESSION TESTS PASSED")


if __name__ == "__main__":
    main()
