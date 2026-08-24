#!/usr/bin/env python3
"""
commission_contract_test.py -- regression fixtures from the five real commission
outcomes of 2026-08-24, plus the capture secret-scanner false positive.

THE FIVE OBSERVED CASES (controlled run, 09:59-10:04 CEST, all sources
acquisition-usable):

  1 Guardian Minnie Evans / Whitney      DEFER commission_eligible_flag_malformed
  2 Conversation AI job boom             DEFER commission_mechanism_not_tied_to_anchor
  3 Conversation student visas           DEFER commission_eligible_flag_malformed
  4 Guardian Durham gallery / Emin       DEFER commission_mechanism_not_tied_to_anchor
  5 Guardian Latrobe Valley coal         DEFER commission_mechanism_not_tied_to_anchor

DIAGNOSIS ENCODED HERE
  * Cases 1 and 3 were a PROMPT/GATE CONTRACT MISMATCH, not a semantic failure:
    `eligible_execution_possible` was described only in the LAYER 1 prose and was
    absent from the LAYER 2 reply schema the model actually copies, so Opus
    omitted it and the validator (which reads it with no default) rejected both
    as malformed. Fixed by putting the field in the reply schema and
    canonicalising unambiguous string forms at parse time. The validator itself
    is unchanged and still fails closed on missing/ambiguous values.
  * Cases 2, 4 and 5 are GENUINE editorial defers by the contract's own
    standard: prompt and validator agree that the explanation must quote the
    grounded anchor, and it did not. That gate is NOT weakened, and these tests
    lock that in.

No network, no model calls.

Run (from repo root):
  python3 automation/commission_contract_test.py
"""

import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from orchestrator.grounding import validate_source_decision  # noqa: E402
from orchestrator.generate import MAX_PREWRITER_CANDIDATES  # noqa: E402
from orchestrator.discovery import (  # noqa: E402
    MAX_SOURCE_ACQUISITION_ATTEMPTS, _SOURCE_MIN_USABLE_CHARS,
    _SOURCE_MIN_USABLE_PARAGRAPHS,
)
import shadow_capture as SC  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


# --------------------------------------------------------------------------- #
ANCHOR = ("Evans began drawing in 1935, at the age offorty-three, after what she "
          "described as a directive she could not refuse.")
SOURCE = ("A retrospective opened this month. " + ANCHOR +
          " The museum has assembled sixty works. " * 3)


def _packet(source_text=SOURCE, origin="fetched_article", truncated=False):
    return {"source_text": source_text, "source_origin": origin,
            "source_truncated": truncated}


def _commission(**over):
    b = {
        "source_decision": "commission",
        "source_anchor_examined": ANCHOR,
        "hidden_mechanism": "The directive is treated as biography rather than as method.",
        "why_disability_knowledge_changes_subject":
            "Read through a disabled perceptual engine, \"" + ANCHOR + "\" stops being "
            "an origin anecdote and becomes a description of how the work was scheduled.",
        "eligible_execution_possible": True,
        "persona": "Maya Flux",
    }
    b.update(over)
    return b


def _verdict(brief, packet=None):
    ok, code, msg, _v = validate_source_decision(brief, packet or _packet())
    return ok, code


# --------------------------------------------------------------------------- #
def test_case_1_and_3_missing_eligible_flag_fails_closed():
    """Cases 1 + 3, exactly as observed: the field is ABSENT -> got None.

    The gate must keep failing closed. This is the behaviour the run showed and
    it stays correct -- the fix was to the prompt that never asked for the field,
    not to this check.
    """
    b = _commission()
    del b["eligible_execution_possible"]
    ok, code = _verdict(b)
    check("case 1/3: absent eligible flag still DEFERs", ok is False)
    check("case 1/3: exact observed reason code",
          code == "commission_eligible_flag_malformed", code)

    b2 = _commission(eligible_execution_possible=None)
    ok2, code2 = _verdict(b2)
    check("explicit null also fails closed",
          ok2 is False and code2 == "commission_eligible_flag_malformed", code2)


def test_ambiguous_eligible_values_fail_closed():
    """Ambiguous / non-canonical values must NOT be coerced into a pass."""
    for bad in ("maybe", "probably", "TRUE-ish", "1", 1, 0, 1.0, [], {}, "", "  "):
        ok, code = _verdict(_commission(eligible_execution_possible=bad))
        check("ambiguous eligible value %r fails closed" % (bad,),
              ok is False and code == "commission_eligible_flag_malformed", code)


def test_real_booleans_pass_the_flag_check():
    ok, code = _verdict(_commission(eligible_execution_possible=True))
    check("real boolean True passes the flag check", ok is True, code)
    ok2, code2 = _verdict(_commission(eligible_execution_possible=False))
    check("real boolean False is a valid parse (routed by Layer 2, not malformed)",
          code2 != "commission_eligible_flag_malformed", code2)


def test_unambiguous_string_forms_are_canonicalised_at_parse_time():
    """The parse-time normaliser turns only exact, unambiguous strings into bools.

    Mirrors llm.py's normalisation step. Ambiguous input is left alone so the
    validator still fails closed on it.
    """
    canon = {"true": True, "false": False, "yes": True, "no": False}

    def normalise(v):
        if isinstance(v, str):
            return canon.get(v.strip().lower(), v)
        return v

    for raw, want in (("true", True), ("false", False), ("TRUE", True),
                      (" Yes ", True), ("no", False)):
        check("%r canonicalises to %s" % (raw, want), normalise(raw) is want)
    for raw in ("maybe", "1", "y", "affirmative", ""):
        check("%r is NOT canonicalised (validator then fails closed)" % raw,
              not isinstance(normalise(raw), bool))
    # end to end: a normalised string now satisfies the gate
    ok, _ = _verdict(_commission(eligible_execution_possible=normalise("true")))
    check("a normalised 'true' satisfies the gate", ok is True)
    ok2, code2 = _verdict(_commission(eligible_execution_possible=normalise("maybe")))
    check("a non-canonical string still DEFERs",
          ok2 is False and code2 == "commission_eligible_flag_malformed", code2)


def test_cases_2_4_5_mechanism_gate_not_weakened():
    """Cases 2, 4, 5: the explanation does not quote the grounded anchor.

    Prompt and validator agree on this representation, so these are genuine
    editorial defers. The rule stays binding -- locked in here so no later
    change quietly relaxes it.
    """
    # the observed shape: topic association, anchor never quoted
    b = _commission(why_disability_knowledge_changes_subject=(
        "Outsider art is routinely explained through biography, and disability "
        "reframes how institutions narrate an artist's beginnings."))
    ok, code = _verdict(b)
    check("case 2/4/5: unquoted anchor still DEFERs", ok is False)
    check("case 2/4/5: exact observed reason code",
          code == "commission_mechanism_not_tied_to_anchor", code)

    # near-miss paraphrase must also fail -- the rule is verbatim anchoring
    ok2, code2 = _verdict(_commission(why_disability_knowledge_changes_subject=(
        "Evans started drawing in 1935 aged forty-three after a directive, which "
        "reframes the work as scheduled rather than spontaneous.")))
    check("a paraphrase of the anchor does NOT satisfy the gate",
          ok2 is False and code2 == "commission_mechanism_not_tied_to_anchor", code2)

    # and a genuine verbatim quote passes -- proving the gate is satisfiable
    ok3, _ = _verdict(_commission())
    check("a verbatim-quoting explanation DOES pass (gate is satisfiable, not a wall)",
          ok3 is True)

    # ungrounded anchor keeps its own distinct code
    ok4, code4 = _verdict(_commission(source_anchor_examined="a sentence not in the source"))
    check("an anchor absent from the source keeps its own code",
          ok4 is False and code4 == "commission_anchor_not_grounded", code4)


# --------------------------------------------------------------------------- #
def test_capture_allows_ordinary_prose_containing_secret():
    """The 2026-08-24 false positive: candidate 3's four source representations
    were refused because the article prose contained the word "secret"."""
    prose = ("The bequest was kept a secret for decades. Curators needed no password "
             "and authorization was informal; the bearer of the letter simply walked in. "
             "The task-force weighed the risk-benefit tradeoff.")
    check("ordinary prose containing 'secret' is NOT flagged",
          SC._scan_for_secrets(prose) == [], SC._scan_for_secrets(prose))
    with tempfile.TemporaryDirectory() as d:
        os.environ[SC.ENV_FLAG] = "1"
        os.environ[SC.ENV_ROOT] = d
        SC.capture("evidence", "ok1", None, packet_source=prose,
                   raw_cached_source=prose, returned_source=prose)
        b = pathlib.Path(d) / "ok1"
        check("prose source IS persisted", (b / "source/packet_source.txt").exists())
        check("persisted byte-for-byte",
              (b / "source/packet_source.txt").read_text() == prose)
        ev = json.loads((b / "manifest.jsonl").read_text().splitlines()[0])
        check("no refusal recorded in the manifest",
              all("status" not in v for v in ev["entries"].values()
                  if isinstance(v, dict)), ev["entries"])
        os.environ.pop(SC.ENV_FLAG, None)


def test_capture_still_refuses_real_credentials():
    """Scanning is NOT disabled: credential-shaped content is still refused."""
    reals = [
        ("original fixture", "key material: OPENROUTER api_key=sk-abc123"),
        ("client_secret assignment", "client_secret: aZ39fjKd83jfkeuw92xQ"),
        ("authorization header", "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.abcdefghijklmnop"),
        ("private key header", "-----BEGIN PRIVATE KEY-----\\nMIIEvQ"),
        ("github token", "ghp_16CharsOfTokenHere"),
        ("slack token", "xoxb-1234-5678-abcdef"),
        ("password assignment", "password=hunter2hunter2"),
        ("access_token field", '"access_token": "ya29.a0ARrdaM-longvalue"'),
    ]
    for label, txt in reals:
        check("still refused: %s" % label, SC._scan_for_secrets(txt) != [],
              SC._scan_for_secrets(txt))
    with tempfile.TemporaryDirectory() as d:
        os.environ[SC.ENV_FLAG] = "1"
        os.environ[SC.ENV_ROOT] = d
        SC.capture("evidence", "bad1", None,
                   packet_source="key material: OPENROUTER api_key=sk-abc123")
        b = pathlib.Path(d) / "bad1"
        check("credential-bearing artifact refused, not written",
              not (b / "source/packet_source.txt").exists())
        ev = json.loads((b / "manifest.jsonl").read_text().splitlines()[0])
        check("refusal recorded in manifest",
              ev["entries"]["source/packet_source.txt"]["status"] == "REFUSED_POSSIBLE_SECRET")
        blob = "\n".join(p.read_text(errors="ignore")
                         for p in b.rglob("*") if p.is_file())
        check("the credential value appears nowhere in the bundle", "sk-abc123" not in blob)
        os.environ.pop(SC.ENV_FLAG, None)


# --------------------------------------------------------------------------- #
def test_frozen_policies_unchanged():
    check("PREWRITER loop still max 5", MAX_PREWRITER_CANDIDATES == 5, MAX_PREWRITER_CANDIDATES)
    check("source acquisition retry still 3", MAX_SOURCE_ACQUISITION_ATTEMPTS == 3)
    check("source classifier thresholds unchanged",
          (_SOURCE_MIN_USABLE_CHARS, _SOURCE_MIN_USABLE_PARAGRAPHS) == (600, 3))
    check("capture REQUIRED_EVENTS unchanged",
          SC.REQUIRED_EVENTS == ("evidence", "commission", "writer",
                                 "final_output", "disposition"), SC.REQUIRED_EVENTS)
    check("capture contract version unchanged", SC.CAPTURE_CONTRACT == "phase2-capture-v0.1")
    src = (HERE / "orchestrator" / "generate.py").read_text()
    check("post-writer failure still cannot rotate a candidate -- only defer/declined do",
          '_PREWRITER_OUTCOMES = ("defer", "declined")' in src)
    g = (HERE / "orchestrator" / "grounding.py").read_text()
    check("the mechanism-anchor rule is still verbatim containment (not weakened)",
          "anchor not in explanation" in g)


def main():
    for fn in [test_case_1_and_3_missing_eligible_flag_fails_closed,
               test_ambiguous_eligible_values_fail_closed,
               test_real_booleans_pass_the_flag_check,
               test_unambiguous_string_forms_are_canonicalised_at_parse_time,
               test_cases_2_4_5_mechanism_gate_not_weakened,
               test_capture_allows_ordinary_prose_containing_secret,
               test_capture_still_refuses_real_credentials,
               test_frozen_policies_unchanged]:
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL COMMISSION-CONTRACT + CAPTURE-SCANNER TESTS PASSED")


if __name__ == "__main__":
    main()
