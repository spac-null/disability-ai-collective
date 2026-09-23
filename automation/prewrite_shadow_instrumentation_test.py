#!/usr/bin/env python3
"""
prewrite_shadow_instrumentation_test.py -- the shadow keeps zero authority and becomes
evidence rather than anecdote.

NOTHING HERE GIVES IT AUTHORITY, and the first test says so. There is still no PASS, no
HOLD, no score and no publishability verdict, the editorial question is unchanged, the
schema and vocabulary are unchanged, and nothing was tuned from the two dry observations.
prewrite_story_shadow_test.py continues to own the zero-authority and OFF-means-absent
contract; this file owns only whether a future audit can trust what it is reading.

The four instrumentation defects, all live on 2e96aa7:

  1. `art.update(obj)` let the MODEL REPLY overwrite the tool's own metadata, including
     `authority` -- the field whose whole job is to say this observation decides nothing.
  2. `discovery_arc` is keyed by beat_id and nothing checked those against the
     architecture, so an arc could describe beats that do not exist. That is the
     invented-observation failure the fact-id check already prevents, one field over.
  3. The transport retries once on a malformed reply, so "one bounded call" was a budget
     rather than a measurement, and the retry was invisible: the wrapper discarded the
     identity carrying the attempt count.
  4. The artifact carried no code, input or prompt identity, so two of them could not be
     told apart or joined to the execution whose Writer/Grounding/Reader outcome they
     were collected to be compared against.

And one fidelity defect: the fact block listed the WHOLE ledger flat, so the shadow was
answering "can this plan be written from this evidence?" about a set the Writer never
sees.

Behavioural, no provider, no network.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import prewrite_story_shadow as PSS   # noqa: E402
from new_engine_v1 import provenance as PV               # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print("  PASS  %s" % label)
    else:
        FAILURES.append(label)
        print("  FAIL  %s   <- %r" % (label, detail))


PACK = {"subject": "a council ranking sheet"}
LEDGER = {"F01": {"proposition": "The council published a ranking sheet in March."},
          "F02": {"proposition": "Ten entries were photographed for the catalogue."},
          "F03": {"proposition": "A servo was fitted to the display case."}}
WORTH = {"story_candidate": {"real_event_or_change": "a sheet was published"},
         "worth_gate": {"lens_claim": "a sheet records what could be photographed"}}
ARCH = {"story_spine": "a sheet was published", "opening_object_or_event": "the sheet",
        "primary_carrier": "F01", "ending_move": "the catalogue closes",
        "use_facts": ["F01", "F02"],
        "cut_evidence": [{"evidence_id": "F03", "reason": "REDUNDANT_PROOF"}],
        "definitions": {"ranking sheet": "the list a council publishes"},
        "beats": [{"beat_id": "B1", "happens": "the sheet is published",
                   "concrete_carrier": "the sheet", "facts_allowed": ["F01"],
                   "beat_function": "REVEAL"},
                  {"beat_id": "B2", "happens": "entries are photographed",
                   "concrete_carrier": "the photographs", "facts_allowed": ["F02"],
                   "beat_function": "REVEAL"}]}

GOOD = {
    "theme_statement": "what a sheet can record", "central_question": "what travels?",
    "concrete_entry": {"description": "the sheet", "fact_ids": ["F01"]},
    "reader_promise": "how the ranking was made",
    "discovery_arc": [{"beat_id": "B1", "before": "nothing", "after": "a sheet exists",
                       "move": "REVEALS", "fact_ids": ["F01"]},
                      {"beat_id": "B2", "before": "a sheet exists",
                       "after": "it ranks photographs", "move": "DEEPENS_MECHANISM",
                       "fact_ids": ["F02"]}],
    "load_bearing_concepts": [{"concept": "ranking sheet", "why_load_bearing": "central",
                               "plain_language_meaning": "a published list",
                               "evidence_fact_ids": ["F01"], "status": "READY"}],
    "grounding_readiness": [{"planned_element": "the ranking", "status": "EVIDENCE_BACKED",
                             "fact_ids": ["F01"]}],
    "crip_minds_turn": "", "why_carrier_reveals_it": "it is the object itself",
    "research_budget": {"load_bearing": ["F01"], "credibility_once": [],
                        "provenance_only": [], "cuttable": []},
    "landing": {"reader_at_start": "nothing", "reader_at_end": "a ranking",
                "changed_understanding": "what it ranks", "lands": "YES"},
    "argument_readiness": "ARGUMENT_READY", "cut_before_writing": [], "risks": [],
}


def run_with(reply, **kw):
    os.environ[PSS.ENV_FLAG] = "1"
    try:
        return PSS.run(lambda s, u: reply, PACK, LEDGER, WORTH, ARCH, **kw)
    finally:
        os.environ.pop(PSS.ENV_FLAG, None)


# ── the contract that must not move ───────────────────────────────────────────
def test_it_still_has_no_authority():
    art = run_with(GOOD)
    check("authority is ZERO", art["authority"] == "ZERO", art.get("authority"))
    check("it still says no article exists yet", art["article_not_written_yet"] is True)
    for banned in ("verdict", "decision", "score", "publishable", "recommendation"):
        check("no %r in the artifact" % banned, banned not in art)
    check("the schema still offers no verdict field",
          "No verdict field" in PSS.SCHEMA or "no verdict field" in PSS.SCHEMA)
    check("OFF still means absent", PSS.run(lambda s, u: GOOD, PACK, LEDGER, WORTH,
                                            ARCH) is None)


# ── 1. the reply may not rewrite the tool's own record ────────────────────────
def test_a_reply_cannot_overwrite_tool_metadata():
    art = run_with(dict(GOOD, authority="HIGH", status="OK",
                        schema_version="whatever-i-like",
                        article_not_written_yet=False))
    check("authority survives a reply that claims otherwise",
          art["authority"] == "ZERO", art["authority"])
    check("schema_version survives", art["schema_version"] == PSS.SCHEMA_VERSION)
    check("article_not_written_yet survives", art["article_not_written_yet"] is True)
    check("and the attempt is recorded rather than silently dropped",
          art.get("tool_fields_ignored") == ["article_not_written_yet", "authority",
                                             "schema_version", "status"],
          art.get("tool_fields_ignored"))
    check("a well-behaved reply records no such field",
          "tool_fields_ignored" not in run_with(GOOD))
    check("the model's own fields still arrive",
          run_with(GOOD)["theme_statement"] == GOOD["theme_statement"])


# ── 2. an arc may not describe beats that do not exist ────────────────────────
def test_beat_ids_are_checked_against_the_architecture():
    bad = json.loads(json.dumps(GOOD))
    bad["discovery_arc"][1]["beat_id"] = "B99"
    errs = PSS.validate(bad, LEDGER, ["B1", "B2"])
    check("an arc naming a beat the architecture lacks is invalid",
          any("B99" in e and "does not contain" in e for e in errs), errs)
    check("the good arc is still valid", PSS.validate(GOOD, LEDGER, ["B1", "B2"]) == [])
    check("two-argument callers are unaffected", PSS.validate(bad, LEDGER) == [],
          PSS.validate(bad, LEDGER))

    art = run_with(bad)
    check("and the run marks the artifact INVALID rather than storing it as an observation",
          art["status"] == "INVALID", art["status"])


# ── 3. what the observation actually cost ─────────────────────────────────────
def test_the_physical_call_count_is_recorded():
    check("one physical call is recorded as one",
          run_with(GOOD, call_meta={"physical_model_calls": 1})[
              "physical_model_calls"] == 1)
    check("a transport retry is recorded as two",
          run_with(GOOD, call_meta={"physical_model_calls": 2})[
              "physical_model_calls"] == 2)
    check("and an unreported count is None, not a guess of 1",
          run_with(GOOD)["physical_model_calls"] is None)
    check("a reply cannot invent its own cost",
          run_with(dict(GOOD, physical_model_calls=99),
                   call_meta={"physical_model_calls": 1})["physical_model_calls"] == 1)


# ── 4. what the observation is OF ─────────────────────────────────────────────
def test_the_artifact_can_be_joined_to_its_execution():
    art = run_with(GOOD)
    ex = art["execution"]
    check("it names the code", ex["code"] == PV.code_identity(), ex["code"])
    for k in ("ledger_sha256", "worth_sha256", "architecture_sha256",
              "system_sha256", "user_prompt_sha256"):
        check("it hashes %s" % k, len(ex[k]) == 64, ex.get(k))

    other = dict(ARCH, story_spine="a different plan entirely")
    os.environ[PSS.ENV_FLAG] = "1"
    try:
        art2 = PSS.run(lambda s, u: GOOD, PACK, LEDGER, WORTH, other)
    finally:
        os.environ.pop(PSS.ENV_FLAG, None)
    check("a different architecture gives a different architecture hash",
          art2["execution"]["architecture_sha256"] != ex["architecture_sha256"])
    check("  and a different rendered prompt",
          art2["execution"]["user_prompt_sha256"] != ex["user_prompt_sha256"])
    check("a reply cannot overwrite the execution record",
          run_with(dict(GOOD, execution={"code": "mine"}))["execution"] == ex)


# ── 5. Writer-available is not the same as present ────────────────────────────
def test_the_prompt_distinguishes_writer_available_evidence():
    user = PSS.build_user(PACK, LEDGER, WORTH, ARCH)
    check("a used fact is marked USED", "[USED  ] F01" in user, user)
    check("a cut fact is marked CUT", "[CUT   ] F03" in user, user)
    check("the block says what the marking means",
          "reaches the Writer" in user)
    check("every fact is still shown",
          all(f in user for f in ("F01", "F02", "F03")))


def main():
    for fn in (test_it_still_has_no_authority,
               test_a_reply_cannot_overwrite_tool_metadata,
               test_beat_ids_are_checked_against_the_architecture,
               test_the_physical_call_count_is_recorded,
               test_the_artifact_can_be_joined_to_its_execution,
               test_the_prompt_distinguishes_writer_available_evidence):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL PREWRITE SHADOW INSTRUMENTATION TESTS PASSED")


if __name__ == "__main__":
    main()
