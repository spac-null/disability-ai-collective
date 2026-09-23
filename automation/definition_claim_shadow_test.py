#!/usr/bin/env python3
"""
definition_claim_shadow_test.py -- the shadow has no authority, OFF means absent, and it
asks about one definition's own evidence and nothing else.

The editorial question this module asks is open and is being calibrated separately. What is
NOT open is whether it can affect anything. These tests own that, plus the two properties
that make its output usable as evidence later: one call per plan, and an artifact bound to
the execution that produced it which the model reply cannot rewrite.

Behavioural, no provider, no network.
"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP            # noqa: E402
from new_engine_v1 import definition_claim_shadow as D  # noqa: E402
from new_engine_v1 import provenance as PV             # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print("  PASS  %s" % label)
    else:
        FAILURES.append(label)
        print("  FAIL  %s   <- %r" % (label, detail))


LEDGER = {
    "F46": {"fact_id": "F46",
            "proposition": "participants were asked to dress as if alerted to an imminent "
                           "large-scale evacuation",
            "support_span": "asked to dress as if alerted to an imminent large-scale "
                            "evacuation"},
    "F48": {"fact_id": "F48",
            "proposition": "the project focuses on getting dressed and gathering a limited "
                           "selection of possessions",
            "support_span": "getting dressed and gathering a limited selection"},
    "F73": {"fact_id": "F73",
            "proposition": "its developers describe it as a knowledge and experience centre",
            "support_span": "a knowledge and experience centre"},
}

ARCH = {
    "article_type": "NARRATIVE_ARTICLE",
    "definitions": {
        "dressing exercise": "people were asked to put on what they would wear if told an "
                             "evacuation were minutes away",
        "centre": "the category the developers use for what they are building",
    },
    "definition_evidence": {"dressing exercise": ["F46", "F48"], "centre": ["F73"]},
}

GOOD = {"definitions": [
    {"term": "centre",
     "claims": [{"commitment": "the developers describe it this way", "status": D.SUPPORTED,
                 "evidence_ids": ["F73"], "reason": "F73 states it"}]},
    {"term": "dressing exercise",
     "claims": [
         {"commitment": "people were asked what they would wear", "status": D.SUPPORTED,
          "evidence_ids": ["F46"], "reason": "F46 states it"},
         {"commitment": "minutes away", "status": D.NOT_ESTABLISHED,
          "evidence_ids": [], "reason": "F46 says imminent, not a duration"}]},
]}


def run_with(reply, arch=ARCH, **kw):
    os.environ[D.ENV_FLAG] = "1"
    try:
        return D.run(lambda s, u: reply, arch, LEDGER, **kw)
    finally:
        os.environ.pop(D.ENV_FLAG, None)


# ── authority ─────────────────────────────────────────────────────────────────
def test_off_means_absent():
    os.environ.pop(D.ENV_FLAG, None)
    check("unset flag returns None", D.run(lambda s, u: GOOD, ARCH, LEDGER) is None)
    for v in ("0", "", "no", "off"):
        os.environ[D.ENV_FLAG] = v
        check("flag %r is OFF" % v, D.run(lambda s, u: GOOD, ARCH, LEDGER) is None)
    os.environ.pop(D.ENV_FLAG, None)


def test_it_has_no_authority():
    art = run_with(GOOD)
    check("authority is ZERO", art["authority"] == "ZERO", art.get("authority"))
    check("it says no article exists yet", art["article_not_written_yet"] is True)
    for banned in ("verdict", "decision", "score", "publishable", "recommendation",
                   "pass", "hold", "repair"):
        check("no %r key in the artifact" % banned, banned not in art)
    check("the schema offers no verdict", "No verdict" in D.SCHEMA)
    check("the system prompt forbids a proceed/stop judgement",
          "not yours to give" in D.SYSTEM)
    check("and forbids suggesting a repair", "do not suggest a repair" in D.SYSTEM)


def test_no_definitions_means_no_call():
    called = []

    def ask(s, u):
        called.append(1)
        return GOOD
    os.environ[D.ENV_FLAG] = "1"
    try:
        out = D.run(ask, {"definitions": {}}, LEDGER)
    finally:
        os.environ.pop(D.ENV_FLAG, None)
    check("a plan with no definitions returns None", out is None, out)
    check("  and makes no model call", called == [], called)


def test_every_failure_path_is_silent():
    art = run_with("not an object")
    check("a non-object reply is INVALID, not an exception", art["status"] == "INVALID")

    def boom(s, u):
        raise RuntimeError("provider exploded")
    os.environ[D.ENV_FLAG] = "1"
    try:
        art = D.run(boom, ARCH, LEDGER)
    finally:
        os.environ.pop(D.ENV_FLAG, None)
    check("a provider failure is FAILED, not raised", art["status"] == "FAILED", art)
    check("  and the error is recorded", "provider exploded" in art.get("error", ""))

    # The composition wrapper must never propagate. A provider that cannot serve a call at
    # all is recorded as FAILED by run() itself; the wrapper's own except is the second net,
    # for a failure inside this module. Either way the caller sees a value, not an exception.
    os.environ[D.ENV_FLAG] = "1"
    raised = None
    try:
        out = CP.run_definition_claim_shadow(object(), ARCH, LEDGER)
    except Exception as e:                                        # noqa: BLE001
        raised, out = e, None
    finally:
        os.environ.pop(D.ENV_FLAG, None)
    check("the composition wrapper does not raise", raised is None, raised)
    check("  and reports the failure rather than inventing a result",
          out is None or out.get("status") == "FAILED", out)
    check("  with no claims in it", out is None or "definitions" not in out, out)


# ── one call per plan ─────────────────────────────────────────────────────────
def test_one_call_for_every_definition():
    seen = []

    def ask(system, user):
        seen.append(user)
        return GOOD
    os.environ[D.ENV_FLAG] = "1"
    try:
        D.run(ask, ARCH, LEDGER)
    finally:
        os.environ.pop(D.ENV_FLAG, None)
    check("exactly one call for a 2-definition plan", len(seen) == 1, len(seen))
    check("  and both terms are in that one request",
          "dressing exercise" in seen[0] and "centre" in seen[0])

    big = dict(ARCH,
               definitions={("t%d" % i): "gloss %d" % i for i in range(11)},
               definition_evidence={("t%d" % i): ["F46"] for i in range(11)})
    seen.clear()
    os.environ[D.ENV_FLAG] = "1"
    try:
        D.run(ask, big, LEDGER)
    finally:
        os.environ.pop(D.ENV_FLAG, None)
    check("still one call at the corpus maximum of 11 definitions", len(seen) == 1,
          len(seen))


# ── evidence isolation ────────────────────────────────────────────────────────
def test_each_definition_sees_only_its_own_evidence():
    user = D.build_user(ARCH, LEDGER)
    centre = user.split("TERM: centre")[1].split("TERM:")[0]
    check("the centre block carries F73", "F73" in centre)
    check("  and not F46 or F48", "F46" not in centre and "F48" not in centre, centre)
    check("the whole ledger is not dumped in",
          "F99" not in user and user.count("F73") == 1)
    check("support spans are included", "verbatim from source" in user)


def test_a_claim_may_not_cite_evidence_its_term_did_not_declare():
    bad = json.loads(json.dumps(GOOD))
    bad["definitions"][0]["claims"][0]["evidence_ids"] = ["F46"]   # centre declared F73 only
    errs = D.validate(bad, ARCH)
    check("citing another term's evidence is invalid",
          any("not evidence this term declared" in e for e in errs), errs)
    check("the good reply validates clean", D.validate(GOOD, ARCH) == [],
          D.validate(GOOD, ARCH))

    bad2 = json.loads(json.dumps(GOOD))
    bad2["definitions"][0]["term"] = "a term nobody defined"
    check("an undefined term is invalid",
          any("does not define" in e for e in D.validate(bad2, ARCH)))

    bad3 = json.loads(json.dumps(GOOD))
    bad3["definitions"] = bad3["definitions"][:1]
    check("a missing term report is invalid",
          any("no report for defined term" in e for e in D.validate(bad3, ARCH)))

    bad4 = json.loads(json.dumps(GOOD))
    bad4["definitions"][1]["claims"][0]["status"] = "PROBABLY_FINE"
    check("an undeclared status is invalid",
          any("is not one of" in e for e in D.validate(bad4, ARCH)))


# ── provenance ────────────────────────────────────────────────────────────────
def test_the_artifact_is_bound_to_its_execution():
    art = run_with(GOOD, execution_id="run-xyz")
    ex = art["execution"]
    check("execution_id recorded", ex["execution_id"] == "run-xyz")
    check("code identity recorded", ex["code"] == PV.code_identity(), ex["code"])
    for k in ("architecture_sha256", "evidence_sha256", "system_sha256",
              "user_prompt_sha256"):
        check("%s is a sha256" % k, len(ex[k]) == 64, ex.get(k))
    check("physical_model_calls recorded",
          run_with(GOOD, call_meta={"physical_model_calls": 2})[
              "physical_model_calls"] == 2)
    check("  and unreported is None, not a guess",
          art["physical_model_calls"] is None)

    other = dict(ARCH, definitions=dict(ARCH["definitions"], centre="a different gloss"))
    art2 = run_with(GOOD, arch=other)
    check("a changed gloss changes the architecture hash",
          art2["execution"]["architecture_sha256"] != ex["architecture_sha256"])
    check("  and the rendered prompt hash",
          art2["execution"]["user_prompt_sha256"] != ex["user_prompt_sha256"])

    led2 = json.loads(json.dumps(LEDGER))
    led2["F73"]["proposition"] = "something else entirely"
    os.environ[D.ENV_FLAG] = "1"
    try:
        art3 = D.run(lambda s, u: GOOD, ARCH, led2)
    finally:
        os.environ.pop(D.ENV_FLAG, None)
    check("a changed fact changes the evidence hash",
          art3["execution"]["evidence_sha256"] != ex["evidence_sha256"])


def test_the_reply_cannot_rewrite_the_record():
    art = run_with(dict(GOOD, authority="HIGH", status="OK",
                        schema_version="mine", article_not_written_yet=False,
                        execution={"code": "mine"}, physical_model_calls=99))
    check("authority survives", art["authority"] == "ZERO", art["authority"])
    check("schema_version survives", art["schema_version"] == D.SCHEMA_VERSION)
    check("article_not_written_yet survives", art["article_not_written_yet"] is True)
    check("execution survives", art["execution"]["code"] == PV.code_identity())
    check("physical_model_calls survives", art["physical_model_calls"] is None)
    check("and the attempt is recorded",
          set(art.get("tool_fields_ignored") or []) ==
          {"article_not_written_yet", "authority", "execution", "physical_model_calls",
           "schema_version", "status"},
          art.get("tool_fields_ignored"))
    check("a clean reply records no such field", "tool_fields_ignored" not in run_with(GOOD))


def test_it_writes_its_own_file():
    with tempfile.TemporaryDirectory() as d:
        run_with(GOOD, out_dir=d)
        f = pathlib.Path(d) / "DEFINITION_CLAIM_SHADOW.json"
        check("DEFINITION_CLAIM_SHADOW.json written", f.exists())
        check("  and it is the artifact",
              json.loads(f.read_text())["authority"] == "ZERO")


def main():
    for fn in (test_off_means_absent,
               test_it_has_no_authority,
               test_no_definitions_means_no_call,
               test_every_failure_path_is_silent,
               test_one_call_for_every_definition,
               test_each_definition_sees_only_its_own_evidence,
               test_a_claim_may_not_cite_evidence_its_term_did_not_declare,
               test_the_artifact_is_bound_to_its_execution,
               test_the_reply_cannot_rewrite_the_record,
               test_it_writes_its_own_file):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL DEFINITION CLAIM SHADOW TESTS PASSED")


if __name__ == "__main__":
    main()
