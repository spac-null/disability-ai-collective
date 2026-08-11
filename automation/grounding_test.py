#!/usr/bin/env python3
"""
grounding_test.py — unit/schema tests for orchestrator/grounding.py.

Pure offline tests, no network, no orchestrator instantiation -- exactly the
first tier of Phase 1.6's strict test order (unit/schema -> deterministic-
validator -> mocked pipeline -> adversarial probes -> small real
confirmation; see .claude/phase-1.6-source-grounding.md). This file covers
tiers 1 and 2 together since grounding.py's validator IS the schema layer.

USAGE: python3 automation/grounding_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "orchestrator"))
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import grounding as g  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def field(status="not_found", editorial_need="test need", interpretation="", **ec_overrides):
    ec = {
        "status": status,
        "source_excerpt": "",
        "named_person": "",
        "direct_quote": "",
        "dates_numbers": [],
    }
    ec.update(ec_overrides)
    return {"editorial_need": editorial_need, "evidence_candidate": ec, "interpretation": interpretation}


SOURCE = (
    "The council voted 6-3 on Tuesday. Councillor Jane Doe said "
    "\"this was a difficult trade-off\" during the meeting. The vote "
    "happened on 2026-03-14 and affected 400 residents."
)


def test_build_evidence_packet():
    empty = g.build_evidence_packet(None)
    check("empty packet has no source_hash", empty["source_hash"] is None)
    check("empty packet has no source_text", empty["source_text"] is None)
    check("empty packet reports source_truncated False", empty["source_truncated"] is False)
    check("empty packet is explicit that original length is unknown", empty["source_original_length_chars"] is None)
    check("empty packet still carries schema version", empty["evidence_schema_version"] == g.EVIDENCE_SCHEMA_VERSION)

    p1 = g.build_evidence_packet(SOURCE)
    p2 = g.build_evidence_packet(SOURCE)
    check("same source text -> identical source_hash", p1["source_hash"] == p2["source_hash"])
    check("same source text -> identical evidence_packet_hash", p1["evidence_packet_hash"] == p2["evidence_packet_hash"])
    check("source_hash and evidence_packet_hash are distinct values", p1["source_hash"] != p1["evidence_packet_hash"])
    check("source_length_chars matches actual length", p1["source_length_chars"] == len(SOURCE))
    check("no cap supplied -> source_truncated not asserted True", p1["source_truncated"] is False)
    check("original length honestly unknown even when source is present", p1["source_original_length_chars"] is None)

    p3 = g.build_evidence_packet(SOURCE + " extra sentence.")
    check("different source text -> different source_hash", p1["source_hash"] != p3["source_hash"])
    check("different source text -> different evidence_packet_hash", p1["evidence_packet_hash"] != p3["evidence_packet_hash"])

    capped = g.build_evidence_packet(SOURCE[:50], source_max_chars=50)
    check("length hitting the requested cap IS flagged truncated", capped["source_truncated"] is True)
    uncapped = g.build_evidence_packet(SOURCE[:50], source_max_chars=5000)
    check("length well under the requested cap is NOT flagged truncated", uncapped["source_truncated"] is False)

    # Regression test for the exact collision caught on review: same
    # source_text, different source_truncated (via a different
    # source_max_chars), must NOT produce the same evidence_packet_hash --
    # the hash is supposed to be the packet's FULL provenance identity, not
    # just a proxy for the raw text.
    check(
        "same source_text with DIFFERENT source_truncated -> DIFFERENT evidence_packet_hash "
        "(hash covers full provenance payload, not just source_text)",
        capped["source_hash"] == uncapped["source_hash"] and capped["evidence_packet_hash"] != uncapped["evidence_packet_hash"],
    )

    # source_origin (found on review): purely explanatory, but must still
    # participate in evidence_packet_hash -- two otherwise-empty packets
    # with different origins ("a fetch failed and fell back to summary" vs
    # "there was genuinely no source") make different provenance claims and
    # must not be indistinguishable once source_text has been suppressed to
    # None for both.
    none_origin = g.build_evidence_packet(None, source_origin="none")
    fallback_origin = g.build_evidence_packet(None, source_origin="fallback_summary")
    check("both packets have source_text=None (fallback grants no evidence authority)", none_origin["source_text"] is None and fallback_origin["source_text"] is None)
    check("source_origin is recorded on the packet", fallback_origin["source_origin"] == "fallback_summary")
    check(
        "two otherwise-identical empty packets with DIFFERENT source_origin -> DIFFERENT evidence_packet_hash",
        none_origin["evidence_packet_hash"] != fallback_origin["evidence_packet_hash"],
    )
    with_text_a = g.build_evidence_packet(SOURCE, source_origin="fetched_article")
    with_text_b = g.build_evidence_packet(SOURCE, source_origin="fixture")
    check(
        "same source_text, different source_origin -> same source_hash but different evidence_packet_hash",
        with_text_a["source_hash"] == with_text_b["source_hash"] and with_text_a["evidence_packet_hash"] != with_text_b["evidence_packet_hash"],
    )
    try:
        g.build_evidence_packet(SOURCE, source_origin="somewhere_i_made_up")
        check("unrecognized source_origin raises", False)
    except ValueError:
        check("unrecognized source_origin raises", True)


def test_not_found():
    packet = g.build_evidence_packet(SOURCE)
    clean_nf = field(status="not_found")
    out, ok, code, reason = g.validate_evidence_field("resisting_example", clean_nf, packet)
    check("clean not_found passes", ok)
    check("clean not_found stays not_found", out["evidence_candidate"]["status"] == "not_found")

    dirty_nf = field(status="not_found", direct_quote="snuck in a quote anyway")
    out, ok, code, reason = g.validate_evidence_field("resisting_example", dirty_nf, packet)
    check("not_found with leftover direct_quote is rejected", not ok)
    check("reason code identifies the leftover-evidence violation", code == "not_found_with_leftover_evidence")
    check("rejected not_found is forced empty", out["evidence_candidate"]["direct_quote"] == "")

    dirty_nf2 = field(status="not_found", dates_numbers=["2026-01-01"])
    out, ok, code, reason = g.validate_evidence_field("correction_moment", dirty_nf2, packet)
    check("not_found with leftover dates_numbers is rejected", not ok)


def test_interpretation_is_structurally_separate_from_evidence():
    """The exact loophole flagged on review: interpretation must never be
    able to carry a factual claim under status=found without a real,
    checkable source_excerpt. There is no evidence_type="interpretive_move"
    escape hatch anymore -- a claim is either grounded or it's not_found."""
    packet = g.build_evidence_packet(SOURCE)

    # Attempting to assert a fact ONLY via interpretation, with status=found
    # but no source_excerpt at all, must be rejected -- interpretation text
    # itself is never inspected as if it might contain evidence.
    fake_via_interpretation = field(
        status="found",
        interpretation="Deborah Antwi told the council she supported the bike lane.",
    )
    out, ok, code, reason = g.validate_evidence_field("resisting_example", fake_via_interpretation, packet)
    check("status=found with NO source_excerpt is rejected even if interpretation carries a claim", not ok)
    check("rejection reason is the empty-excerpt check, not an interpretation check", code == "empty_source_excerpt")

    # A not_found candidate is allowed to carry interpretation freely (e.g.
    # "the source doesn't provide a resisting witness") -- interpretation is
    # never validated against the source, by design, because it is never
    # presented downstream as a factual claim.
    nf_with_interpretation = field(status="not_found", interpretation="The source does not provide a resisting witness.")
    out, ok, code, reason = g.validate_evidence_field("resisting_example", nf_with_interpretation, packet)
    check("not_found + free interpretation text passes untouched", ok)
    check("interpretation is preserved through validation", out["interpretation"] == "The source does not provide a resisting witness.")

    # A genuinely grounded claim may ALSO carry interpretation alongside it --
    # that's the intended, legitimate combination.
    grounded_with_interpretation = field(
        status="found",
        source_excerpt='Councillor Jane Doe said "this was a difficult trade-off" during the meeting.',
        named_person="Jane Doe",
        interpretation="This complicates Maya's framing of the vote as unanimous indifference.",
    )
    out, ok, code, reason = g.validate_evidence_field("resisting_example", grounded_with_interpretation, packet)
    check("grounded evidence + interpretation together is accepted", ok)
    check("interpretation survives alongside real evidence", out["interpretation"] != "")


def test_source_grounded():
    packet = g.build_evidence_packet(SOURCE)

    valid = field(
        status="found",
        source_excerpt='Councillor Jane Doe said "this was a difficult trade-off" during the meeting.',
        named_person="Jane Doe",
        direct_quote="this was a difficult trade-off",
    )
    out, ok, code, reason = g.validate_evidence_field("resisting_example", valid, packet)
    check("real excerpt + real quote + real name all inside excerpt -> accepted", ok)

    fake_person = field(
        status="found",
        source_excerpt=valid["evidence_candidate"]["source_excerpt"],
        named_person="Deborah Antwi",
        direct_quote=valid["evidence_candidate"]["direct_quote"],
    )
    out, ok, code, reason = g.validate_evidence_field("resisting_example", fake_person, packet)
    check("named_person not present in its own excerpt -> rejected (the Antwi case)", not ok)
    check("reason code identifies named_person violation", code == "named_person_not_in_excerpt")
    check("rejected source candidate forced to not_found", out["evidence_candidate"]["status"] == "not_found")

    fake_excerpt = field(status="found", source_excerpt="This sentence does not appear anywhere in the source.")
    out, ok, code, reason = g.validate_evidence_field("resisting_example", fake_excerpt, packet)
    check("source_excerpt not a substring of source_text -> rejected", not ok)
    check("reason code identifies excerpt violation", code == "source_excerpt_not_in_source")

    fake_quote = field(
        status="found",
        source_excerpt='Councillor Jane Doe said "this was a difficult trade-off" during the meeting.',
        direct_quote="words she never said",
    )
    out, ok, code, reason = g.validate_evidence_field("resisting_example", fake_quote, packet)
    check("direct_quote not inside its own excerpt -> rejected", not ok)
    check("reason code identifies quote violation", code == "direct_quote_not_in_excerpt")

    # REGRESSION -- the exact live adversarial-control failure (2026-08-11):
    # an ordinary declarative sentence, verbatim in the excerpt, but nobody
    # is quoted as saying it. Text-presence alone used to pass this.
    unattributed_declarative_packet = g.build_evidence_packet(
        "City crews will repaint a curb ramp after surface wear was observed. "
        "The ramp will be temporarily closed during repainting. Work will resume when the surface is dry."
    )
    unattributed_declarative = field(
        status="found",
        source_excerpt="Work will resume when the surface is dry.",
        direct_quote="Work will resume when the surface is dry.",
    )
    out, ok, code, reason = g.validate_evidence_field("correction_moment", unattributed_declarative, unattributed_declarative_packet)
    check(
        "LIVE REGRESSION: an unattributed declarative sentence used as direct_quote (verbatim, but nobody is "
        "quoted saying it) is REJECTED, not merely because it's untrue but because it isn't actually a quote",
        not ok,
    )
    check("reason code identifies the quotation-marks violation specifically", code == "direct_quote_not_in_quotation_marks")
    check("rejected direct_quote-without-attribution candidate forced to not_found", out["evidence_candidate"]["status"] == "not_found")

    # Real quotation inside DOUBLE quotes -- already covered by `valid` above
    # (passes). Confirm British-style STRAIGHT SINGLE-quote attribution
    # (common in real sources -- Dezeen, etc.) is NOT penalized just for
    # using single rather than double quotes.
    single_quote_packet = g.build_evidence_packet(
        "The council voted 6-3 on Tuesday. 'This was a difficult trade-off,' said council transport lead Dana Ruiz."
    )
    single_quote_valid = field(
        status="found",
        source_excerpt="'This was a difficult trade-off,' said council transport lead Dana Ruiz.",
        named_person="Dana Ruiz",
        direct_quote="This was a difficult trade-off",
    )
    out, ok, code, reason = g.validate_evidence_field("resisting_example", single_quote_valid, single_quote_packet)
    check("British-style straight-single-quote attribution is accepted, not penalized for punctuation style", ok)

    # A quote-shaped string that merely CONTAINS an apostrophe elsewhere in
    # the excerpt (a possessive/contraction, not a real quote boundary)
    # must not accidentally satisfy the quotation-marks check.
    possessive_packet = g.build_evidence_packet(
        "The council's transport lead said the plan works as intended for every resident who uses it."
    )
    possessive_field = field(
        status="found",
        source_excerpt="The council's transport lead said the plan works as intended for every resident who uses it.",
        direct_quote="transport lead said the plan works as intended for every resident who uses it",
    )
    out, ok, code, reason = g.validate_evidence_field("resisting_example", possessive_field, possessive_packet)
    check(
        "a possessive apostrophe elsewhere in the excerpt does not accidentally satisfy the quotation-marks check",
        not ok,
    )
    check("possessive-apostrophe false-positive case rejected with the quotation-marks reason code", code == "direct_quote_not_in_quotation_marks")

    real_date = field(
        status="found",
        source_excerpt="The vote happened on 2026-03-14 and affected 400 residents.",
        dates_numbers=["2026-03-14"],
    )
    out, ok, code, reason = g.validate_evidence_field("correction_moment", real_date, packet)
    check("real date found in excerpt -> accepted", ok)

    fake_date = field(
        status="found",
        source_excerpt="The vote happened on 2026-03-14 and affected 400 residents.",
        dates_numbers=["1999-01-01"],
    )
    out, ok, code, reason = g.validate_evidence_field("correction_moment", fake_date, packet)
    check("invented date not in excerpt -> rejected", not ok)
    check("reason code identifies date violation", code == "date_number_not_in_excerpt")

    no_source_packet = g.build_evidence_packet(None)
    out, ok, code, reason = g.validate_evidence_field("resisting_example", valid, no_source_packet)
    check("status=found with no source text at all in the packet -> rejected", not ok)
    check("reason code identifies missing-source violation", code == "no_source_text_available")

    no_excerpt = field(status="found", source_excerpt="")
    out, ok, code, reason = g.validate_evidence_field("resisting_example", no_excerpt, packet)
    check("status=found with empty source_excerpt -> rejected", not ok)
    check("reason code identifies empty-excerpt violation", code == "empty_source_excerpt")


def test_malformed_shape():
    packet = g.build_evidence_packet(SOURCE)
    out, ok, code, reason = g.validate_evidence_field("resisting_example", "just a flat legacy string", packet)
    check("legacy flat-string candidate is rejected outright (schema mismatch)", not ok)
    check("legacy flat-string reason code is malformed_shape", code == "malformed_shape")
    check("legacy flat-string candidate forced to not_found", out["evidence_candidate"]["status"] == "not_found")

    out, ok, code, reason = g.validate_evidence_field("resisting_example", {"evidence_candidate": {"status": "found"}}, packet)
    check("dict missing editorial_need/interpretation is rejected", not ok)

    bad_status = field()
    bad_status["evidence_candidate"]["status"] = "maybe"
    out, ok, code, reason = g.validate_evidence_field("resisting_example", bad_status, packet)
    check("invalid status enum value is rejected", not ok)

    wrong_type = field(status="found", dates_numbers="not-a-list")
    out, ok, code, reason = g.validate_evidence_field("resisting_example", wrong_type, packet)
    check("wrong-typed field (dates_numbers as str) is rejected", not ok)

    no_evidence_type_field_exists = "evidence_type" not in field(status="found")["evidence_candidate"]
    check("schema has no evidence_type key at all (the removed loophole)", no_evidence_type_field_exists)

    no_fact_summary_field_exists = "fact_summary" not in field(status="found")
    check("schema has no fact_summary key at all (the removed loophole)", no_fact_summary_field_exists)


def test_validate_brief():
    packet = g.build_evidence_packet(SOURCE)
    good = field(
        status="found",
        source_excerpt='Councillor Jane Doe said "this was a difficult trade-off" during the meeting.',
        named_person="Jane Doe", direct_quote="this was a difficult trade-off",
    )
    bad = field(status="found", source_excerpt="invented", named_person="Deborah Antwi")

    brief = {"persona": "Maya Flux", "angle": "x", "resisting_example": good, "correction_moment": field()}
    validated, log = g.validate_brief(brief, packet)
    check("all-clean brief -> grounding_status validated", validated["grounding_status"] == "validated")
    check("all-clean brief -> no grounding_violations", validated["grounding_violations"] == [])
    check("validate_brief stamps brief_schema_version", validated["brief_schema_version"] == g.BRIEF_SCHEMA_VERSION)
    check(
        "validate_brief stamps grounding_scope so 'validated' can't be misread as whole-brief grounding",
        validated["grounding_scope"] == g.GROUNDING_SCOPE_EVIDENCE_FIELDS_ONLY,
    )
    check("validate_brief stamps source_hash", validated["source_hash"] == packet["source_hash"])
    check("validate_brief stamps source_truncated", "source_truncated" in validated)
    check("validate_brief does not mutate caller's dict", "brief_schema_version" not in brief)

    brief2 = {"persona": "Maya Flux", "angle": "x", "resisting_example": bad, "correction_moment": field()}
    validated2, log2 = g.validate_brief(brief2, packet)
    check("brief with ONE bad field out of two asserted -> validated_with_rejections", validated2["grounding_status"] == "validated_with_rejections")
    check("rejected field forced to not_found in the returned brief", validated2["resisting_example"]["evidence_candidate"]["status"] == "not_found")
    check("grounding_violations records the rejected field", any(v["field"] == "resisting_example" for v in validated2["grounding_violations"]))
    check("grounding_violations carries the reason_code", validated2["grounding_violations"][0]["reason_code"] == "source_excerpt_not_in_source")

    brief2b = {"persona": "Maya Flux", "angle": "x", "resisting_example": bad, "correction_moment": bad}
    validated2b, _ = g.validate_brief(brief2b, packet)
    check("brief with ALL asserted fields bad -> rejected (not merely validated_with_rejections)", validated2b["grounding_status"] == "rejected")
    check("rejected-status brief still returns a safe, usable (all not_found) brief", validated2b["resisting_example"]["evidence_candidate"]["status"] == "not_found" and validated2b["correction_moment"]["evidence_candidate"]["status"] == "not_found")

    no_source_packet = g.build_evidence_packet(None)
    brief3 = {"persona": "Maya Flux", "angle": "x", "resisting_example": field()}
    validated3, log3 = g.validate_brief(brief3, no_source_packet)
    check("no source available + only legitimate not_found fields -> no_source_available", validated3["grounding_status"] == "no_source_available")
    check("no_source_available with no misbehavior -> no violations recorded", validated3["grounding_violations"] == [])

    brief3b = {"persona": "Maya Flux", "angle": "x", "resisting_example": good}
    validated3b, _ = g.validate_brief(brief3b, no_source_packet)
    check(
        "planner asserting status=found with NO source available at all is still caught as a real violation, "
        "not folded silently into no_source_available",
        validated3b["grounding_status"] == "rejected" and len(validated3b["grounding_violations"]) == 1,
    )

    brief4 = {"persona": "Maya Flux", "angle": "x"}
    validated4, log4 = g.validate_brief(brief4, packet)
    check("brief with neither evidence field present doesn't crash", validated4["grounding_status"] == "validated")
    check("brief with neither evidence field present has no violations", validated4["grounding_violations"] == [])


def test_legacy_schema_gate():
    packet = g.build_evidence_packet(SOURCE)
    real_brief = {"persona": "Maya Flux", "angle": "x", "resisting_example": field(), "correction_moment": field()}
    validated, _ = g.validate_brief(real_brief, packet)
    check("a brief that actually went through validate_brief() is current schema", g.is_current_brief_schema(validated))

    check("brief missing brief_schema_version is NOT current schema (legacy)", not g.is_current_brief_schema({"persona": "x"}))
    check("brief with old version number is NOT current schema", not g.is_current_brief_schema({"brief_schema_version": 1}))
    check("non-dict input is NOT current schema", not g.is_current_brief_schema("not even a dict"))

    # REGRESSION for the exact weakness caught on review: brief_schema_version
    # alone is NOT sufficient -- a hand-edited/stale JSON claiming v2 without
    # the rest of validate_brief's real provenance stamp must still fail.
    check(
        "a brief with ONLY brief_schema_version=2 (no grounding_scope/evidence_schema_version/"
        "grounding_status/hashes) is REJECTED, not accepted on version number alone",
        not g.is_current_brief_schema({"brief_schema_version": 2}),
    )
    incomplete = dict(validated)
    del incomplete["source_hash"]
    check("current-looking brief missing source_hash key entirely -> rejected", not g.is_current_brief_schema(incomplete))
    missing_origin = dict(validated)
    del missing_origin["source_origin"]
    check("current-looking brief missing source_origin key entirely -> rejected", not g.is_current_brief_schema(missing_origin))
    check("validate_brief stamps source_origin as a key even when its value is None (legacy/unspecified)", "source_origin" in validated)
    wrong_scope = dict(validated)
    wrong_scope["grounding_scope"] = "something_else"
    check("brief with an unrecognized grounding_scope -> rejected", not g.is_current_brief_schema(wrong_scope))
    wrong_status = dict(validated)
    wrong_status["grounding_status"] = "totally_fine_trust_me"
    check("brief with a grounding_status outside validate_brief's own defined values -> rejected", not g.is_current_brief_schema(wrong_status))

    # REGRESSION: schema/hash identity alone cannot distinguish "validated
    # under an older rule set" from "validated under the current one" when
    # a validation RULE changes without the packet/brief structure changing
    # (exactly the direct_quote_not_in_quotation_marks case). This is what
    # grounding_validator_version exists to catch.
    check("validate_brief stamps grounding_validator_version", validated["grounding_validator_version"] == g.GROUNDING_VALIDATOR_VERSION)
    stale_validator = dict(validated)
    stale_validator["grounding_validator_version"] = g.GROUNDING_VALIDATOR_VERSION - 1
    check(
        "a brief validated by an OLDER validator version is rejected even though schema/hashes still match "
        "(schema-current is not the same claim as validated-under-current-rules)",
        not g.is_current_brief_schema(stale_validator),
    )
    missing_validator_version = dict(validated)
    del missing_validator_version["grounding_validator_version"]
    check("current-looking brief missing grounding_validator_version key entirely -> rejected", not g.is_current_brief_schema(missing_validator_version))

    no_source_brief = {"persona": "Maya Flux", "angle": "x"}
    no_source_validated, _ = g.validate_brief(no_source_brief, g.build_evidence_packet(None))
    check(
        "a legitimately source_hash=None (no-source run) brief still passes -- key presence, not truthiness, is what's checked",
        g.is_current_brief_schema(no_source_validated),
    )


def test_writer_prompt_block():
    nf = field(status="not_found", interpretation="nothing found, but here's why that matters")
    check("not_found produces NO writer block (interpretation alone is not evidence to write from)", g.writer_prompt_block("RESISTING EXAMPLE", nf) == "")

    grounded = field(
        status="found",
        source_excerpt="Jane Doe called it a difficult trade-off.",
        direct_quote="a difficult trade-off",
        interpretation="This complicates the thesis.",
    )
    block = g.writer_prompt_block("RESISTING EXAMPLE", grounded)
    check("writer block contains the label", "RESISTING EXAMPLE" in block)
    check("writer block contains the real excerpt under its own heading", "VALIDATED SOURCE EVIDENCE" in block and "Jane Doe called it a difficult trade-off." in block)
    check("writer block contains the exact quote under its own heading", "OPTIONAL EXACT QUOTE" in block and "a difficult trade-off" in block)
    check("writer block does NOT leak planner interpretation prose (closed laundering path)", "This complicates the thesis." not in block)
    check("writer block does NOT contain an editorial_need/interpretation heading at all", "PLANNER INTERPRETATION" not in block and "EDITORIAL NEED" not in block)
    check("writer block contains the fixed code-authored instruction, not planner prose", "Do not invent context around it." in block)
    check("writer block never contains a bare 'fact_summary'-style unlabeled assertion", "fact_summary" not in block.lower())

    no_quote = field(status="found", source_excerpt="Just a plain excerpt with no quotation in it.")
    block2 = g.writer_prompt_block("CORRECTION MOMENT", no_quote)
    check("writer block omits the quote section when there is no quote", "OPTIONAL EXACT QUOTE" not in block2)

    check(
        "legacy flat string is REJECTED by writer_prompt_block (production write path -- "
        "tolerance for old data belongs only in evidence_text, the historical-read path)",
        g.writer_prompt_block("X", "a legacy sentence") == "",
    )

    # Regression test for the exact scenario caught on review before any
    # snapshot was recorded: a REAL, validated source_excerpt paired with a
    # FABRICATED claim in interpretation. Before this fix, interpretation
    # was handed to the writer as "PLANNER INTERPRETATION" prose -- passing
    # validate_evidence_field (which never checks interpretation, by design)
    # was enough to get an invented factual claim about a named person in
    # front of the writer under a trusted-looking heading.
    laundering_attempt = field(
        status="found",
        source_excerpt="The council approved the new bike lane on Tuesday.",
        interpretation="Deborah Antwi had already complained to the council in writing.",
    )
    laundering_block = g.writer_prompt_block("RESISTING EXAMPLE", laundering_attempt)
    check(
        "fabricated interpretation claim (a named person, an unverified prior action) never reaches the writer block",
        "Deborah Antwi" not in laundering_block and "complained to the council in writing" not in laundering_block,
    )


def test_find_new_unsupported_specifics():
    original = 'The council met on Tuesday. A wheelchair user said the new route was inconvenient.'

    check("no revision (identical text) -> no violations", g.find_new_unsupported_specifics(original, original, SOURCE) == [])

    # The exact Phase 1.5B failure class: reviewer says "get her real words",
    # executor fabricates a verbatim quotation that wasn't there before.
    fabricated_quote_revision = (
        'The council met on Tuesday. A wheelchair user, Priya Nathan, said '
        '"this route makes me feel invisible to the people who planned it."'
    )
    hits1 = g.find_new_unsupported_specifics(original, fabricated_quote_revision, SOURCE)
    check("newly fabricated quotation not in source -> flagged", any(r == "new_quote_not_in_source" for r, _ in hits1))

    # A quotation that WAS already in the original draft is not "new" even
    # if it also isn't in source_text -- the guard targets NEWLY introduced
    # specifics, not every unsourced string already shipped in the draft.
    original_with_quote = original + ' She added, "it adds twenty minutes to my commute."'
    revision_keeping_same_quote = original_with_quote.replace("Tuesday", "Tuesday afternoon")
    hits2 = g.find_new_unsupported_specifics(original_with_quote, revision_keeping_same_quote, SOURCE)
    check("quote already present in the original draft is NOT flagged as new", not any(r == "new_quote_not_in_source" for r, _ in hits2))

    # A quotation that genuinely IS in source_text is legitimate to introduce.
    grounded_quote_revision = original + ' Councillor Jane Doe said "this was a difficult trade-off".'
    hits3 = g.find_new_unsupported_specifics(original, grounded_quote_revision, SOURCE)
    check("newly introduced quote that IS verbatim in source -> not flagged", not any(r == "new_quote_not_in_source" for r, _ in hits3))
    check("correctly-attributed quote is not flagged as misattributed either", not any(r == "new_quote_misattributed" for r, _ in hits3))

    # REGRESSION: the exact misattribution scenario caught on review -- the
    # quote text is real (verbatim in source), but the revision reassigns it
    # to a fabricated speaker. This is the closest possible failure to the
    # original catastrophic quote-fabrication bug, and text-only checking
    # cannot catch it.
    misattributed_revision = original + ' Deborah Antwi said "this was a difficult trade-off" to reporters.'
    hits_misattr = g.find_new_unsupported_specifics(original, misattributed_revision, SOURCE)
    check(
        "quote text real, but reassigned to a fabricated speaker -> flagged as misattributed",
        any(r == "new_quote_misattributed" for r, _ in hits_misattr),
    )
    check(
        "misattribution is flagged as its own reason_code, not conflated with new_quote_not_in_source",
        not any(r == "new_quote_not_in_source" for r, _ in hits_misattr),
    )

    # A quote with no named attribution nearby (just real text) is not
    # penalized -- there's nothing to check the attribution of.
    unattributed_revision = original + ' Someone at the meeting said "this was a difficult trade-off".'
    hits_unattr = g.find_new_unsupported_specifics(original, unattributed_revision, SOURCE)
    check("quote with no nearby named attribution -> not flagged as misattributed", not any(r == "new_quote_misattributed" for r, _ in hits_unattr))

    # REGRESSION (hardening round): a nearby proper-name-like phrase with NO
    # attribution verb near it must NOT be treated as an attribution claim at
    # all -- e.g. an organization name mentioned near the quote for an
    # unrelated reason.
    no_verb_source = 'Jane Doe said "this was a difficult trade-off" during the meeting.'
    no_verb_revision = original + ' Deborah Antwi Consulting Group reviewed the file. "this was a difficult trade-off"'
    hits_no_verb = g.find_new_unsupported_specifics(original, no_verb_revision, no_verb_source)
    check(
        "a nearby capitalized phrase with NO attribution verb is not treated as an attribution claim",
        not any(r == "new_quote_misattributed" for r, _ in hits_no_verb),
    )

    # REGRESSION: curly single quotes ('...') must be recognized, not just
    # straight/curly double quotes.
    curly_single_source = 'Jane Doe said ‘this was a difficult trade-off’ during the meeting.'
    curly_single_misattributed = original + ' Deborah Antwi said ‘this was a difficult trade-off’ to reporters.'
    hits_curly = g.find_new_unsupported_specifics(original, curly_single_misattributed, curly_single_source)
    check(
        "curly single quotes ('...') are recognized as quoted spans, and misattribution within them is caught",
        any(r == "new_quote_misattributed" for r, _ in hits_curly),
    )

    # REGRESSION: check ALL occurrences of a repeated quote in source, not
    # just the first -- the correct attribution may sit near a LATER
    # occurrence of the same quote text.
    repeated_quote_source = (
        'A flyer distributed downtown read "this was a difficult trade-off". '
        'Later at the hearing, Jane Doe said "this was a difficult trade-off" to reporters.'
    )
    repeated_quote_revision = original + ' Jane Doe said "this was a difficult trade-off" at the hearing.'
    hits_repeated = g.find_new_unsupported_specifics(original, repeated_quote_revision, repeated_quote_source)
    check(
        "attribution corroborated near a LATER occurrence of a repeated quote is accepted, "
        "not rejected for failing to match only the first occurrence",
        not any(r == "new_quote_misattributed" for r, _ in hits_repeated),
    )

    # New fabricated number.
    fabricated_number_revision = original + ' The petition collected 9200 signatures.'
    hits4 = g.find_new_unsupported_specifics(original, fabricated_number_revision, SOURCE)
    check("newly introduced number not in source -> flagged", any(r == "new_number_not_in_source" for r, _ in hits4))

    # Number already in source is fine to introduce.
    grounded_number_revision = original + ' This affected 400 residents.'
    hits5 = g.find_new_unsupported_specifics(original, grounded_number_revision, SOURCE)
    check("newly introduced number that IS in source -> not flagged", not any(r == "new_number_not_in_source" for r, _ in hits5))

    check("None original/revised text -> no crash, no violations", g.find_new_unsupported_specifics(None, None, SOURCE) == [])


def test_scan_free_prose_field():
    check("empty text -> no violations", g.scan_free_prose_field("", SOURCE) == [])
    check("None text -> no violations", g.scan_free_prose_field(None, SOURCE) == [])

    clean = "The council voted 6-3 on Tuesday, and that was that."
    check("prose with no quotes/names/numbers not in source -> clean", g.scan_free_prose_field(clean, SOURCE) == [])

    grounded_specifics = 'Councillor Jane Doe said "this was a difficult trade-off" to 400 residents.'
    check(
        "prose whose quote/name/number all appear verbatim in source -> clean",
        g.scan_free_prose_field(grounded_specifics, SOURCE) == [],
    )

    fabricated_quote = 'The mayor said "we will fix this by next spring" to the crowd.'
    hits1 = g.scan_free_prose_field(fabricated_quote, SOURCE)
    check("invented quotation not in source -> flagged", any(r == "quoted_text_not_in_source" for r, _ in hits1))

    fabricated_name = "Deborah Antwi rolled into the March council meeting ready to fight."
    hits2 = g.scan_free_prose_field(fabricated_name, SOURCE)
    check("invented named person not in source -> flagged", any(r == "possible_named_entity_not_in_source" for r, _ in hits2))

    fabricated_number = "Nine thousand two hundred signatures forced the council's hand."
    hits3 = g.scan_free_prose_field("The petition collected 9200 signatures.", SOURCE)
    check("invented number not in source -> flagged", any(r == "possible_number_not_in_source" for r, _ in hits3))

    check(
        "no source at all -> any quote/name/number is automatically a violation",
        len(g.scan_free_prose_field(fabricated_name, None)) > 0,
    )

    # KNOWN LIMITATION, documented not hidden (found on review): a plain
    # invented factual claim using none of the three detected shapes slips
    # through undetected. This is exactly why scan_free_prose_field is
    # diagnostic-only and NOT wired into validate_brief -- the real fix is
    # that generate.py no longer injects opening_scene/seed_sentence text
    # into the writer prompt at all, regardless of what this function finds.
    undetectable_fabrication = "The council had ignored earlier complaints for months."
    check(
        "KNOWN LIMITATION: a plain fabricated claim with no quote/Title-Case name/number "
        "produces NO hits -- this scanner cannot be a safety boundary on its own",
        g.scan_free_prose_field(undetectable_fabrication, SOURCE) == [],
    )


def test_validate_brief_does_not_touch_free_prose_fields():
    """validate_brief() deliberately does NOT validate, clear, or otherwise
    touch opening_scene/seed_sentence (REVERTED after review -- see
    _FREE_PROSE_FIELDS's comment in grounding.py for why an earlier version
    of this function force-cleared these fields and why that was wrong: the
    scanner it used cannot detect all unsupported-specificity shapes, so
    "scanned clean" was never a valid grounding claim). The actual safety
    fix lives in generate.py (these fields are no longer injected into the
    writer prompt at all) -- validate_brief has no opinion on their content
    either way, clean or fabricated."""
    packet = g.build_evidence_packet(SOURCE)
    contaminated_brief = {
        "persona": "Maya Flux", "angle": "x",
        "opening_scene": "Deborah Antwi rolled into the March council meeting ready to fight.",
        "seed_sentence": "This was, by the council's own account, a difficult trade-off.",
    }
    validated, _ = g.validate_brief(contaminated_brief, packet)
    check(
        "validate_brief leaves opening_scene untouched even when fabricated "
        "(no false sense of safety from a partial scanner)",
        validated["opening_scene"] == contaminated_brief["opening_scene"],
    )
    check("validate_brief leaves seed_sentence untouched", validated["seed_sentence"] == contaminated_brief["seed_sentence"])
    check(
        "grounding_status is not affected by opening_scene/seed_sentence content at all",
        validated["grounding_status"] == "validated",
    )


def test_evidence_text():
    check("legacy flat string passes through unchanged", g.evidence_text("a legacy resisting example") == "a legacy resisting example")
    check(
        "structured found -> descriptive summary, not a bare unlabeled fact string",
        "source excerpt:" in g.evidence_text(field(status="found", source_excerpt="the fact")),
    )
    check("structured not_found -> empty string", g.evidence_text(field(status="not_found")) == "")
    check("None -> empty string", g.evidence_text(None) == "")
    check("empty string -> empty string", g.evidence_text("") == "")


PIXEL_CANON_EXCERPT = (
    "## FROM THE INTERVIEWS\n\n"
    "Legibility written into law: founding a legal entity, a notary literally inscribed into the deed "
    "that the Deaf signer was capable of reading the translated language and therefore understood what "
    "he signed — the official visibly uneasy sitting with someone who could not follow speech."
)

ARTICLE_SOURCE_EXCERPT = (
    "On 6 August 2026, wheelchair user Elena Rossi tested the temporary entrance. "
    '"I can enter independently now, but the sign still sends me toward the stairs," Rossi said.'
)


def test_build_persona_factual_context():
    empty = g.build_persona_factual_context(None)
    check("empty persona context has no canon_hash", empty["canon_hash"] is None)
    check("empty persona context has no canon_text", empty["canon_text"] is None)
    check("empty persona context still carries schema version", empty["persona_factual_context_schema_version"] == g.PERSONA_FACTUAL_CONTEXT_SCHEMA_VERSION)

    ctx = g.build_persona_factual_context(PIXEL_CANON_EXCERPT, persona_name="Pixel Nova")
    check("persona context records persona_name", ctx["persona_name"] == "Pixel Nova")
    check("persona context hashes canon_text", ctx["canon_hash"] == g._sha256_text(PIXEL_CANON_EXCERPT))
    check("persona context records canon_length_chars", ctx["canon_length_chars"] == len(PIXEL_CANON_EXCERPT))

    ctx2 = g.build_persona_factual_context(PIXEL_CANON_EXCERPT, persona_name="Pixel Nova")
    check("same canon_text -> identical canon_hash", ctx["canon_hash"] == ctx2["canon_hash"])
    ctx3 = g.build_persona_factual_context(PIXEL_CANON_EXCERPT + " extra.", persona_name="Pixel Nova")
    check("different canon_text -> different canon_hash", ctx["canon_hash"] != ctx3["canon_hash"])


def test_scan_draft_for_unsupported_specifics():
    authorized_corpus = ARTICLE_SOURCE_EXCERPT + "\n\n" + PIXEL_CANON_EXCERPT

    check("empty draft -> no violations", g.scan_draft_for_unsupported_specifics("", authorized_corpus) == [])
    check("None draft -> no violations", g.scan_draft_for_unsupported_specifics(None, authorized_corpus) == [])

    clean_draft = (
        'Elena Rossi said "I can enter independently now, but the sign still sends me toward the stairs."'
    )
    check("draft using only real source material -> clean", g.scan_draft_for_unsupported_specifics(clean_draft, authorized_corpus) == [])

    # REGRESSION -- the exact live finding (2026-08-11 downstream positive
    # control): a fabricated first-person witnessed event with a specific
    # invented date, absent from both source and persona canon.
    fabricated_anecdote = (
        "In March 2024 I sat through a wayfinding review for a Rotterdam civic building "
        "and watched exactly that meeting happen."
    )
    hits = g.scan_draft_for_unsupported_specifics(fabricated_anecdote, authorized_corpus)
    check(
        "LIVE REGRESSION: the fabricated '2024' from the Rotterdam anecdote is flagged",
        any(r == "possible_number_not_in_authorized_corpus" and "2024" in reason for r, reason in hits),
    )

    # REGRESSION -- the punctuation-edge false positive also found live: the
    # real article quoted persona canon's notary anecdote accurately but
    # added a trailing comma the canon source doesn't have. Must NOT be
    # flagged once edge punctuation is stripped.
    real_canon_quote_with_added_comma = (
        'The persona recalled a notary who wrote that the Deaf signer was '
        '"capable of reading the translated language and therefore understood what he signed,"'
    )
    hits2 = g.scan_draft_for_unsupported_specifics(real_canon_quote_with_added_comma, authorized_corpus)
    check(
        "a real canon quote with an added trailing comma (grammatical embedding) is NOT flagged as unsupported",
        not any(r == "quoted_text_not_in_authorized_corpus" for r, _ in hits2),
    )

    # A genuinely fabricated quotation must still be caught.
    fabricated_quote_draft = 'The museum director said "we never received a single complaint about signage."'
    hits3 = g.scan_draft_for_unsupported_specifics(fabricated_quote_draft, authorized_corpus)
    check("a genuinely fabricated quotation not in either corpus is flagged", any(r == "quoted_text_not_in_authorized_corpus" for r, _ in hits3))

    check(
        "no authorized corpus at all -> any quote/name/number is automatically a violation",
        len(g.scan_draft_for_unsupported_specifics(fabricated_anecdote, None)) > 0,
    )


def test_find_new_unsupported_personal_history():
    """The executor-boundary counterpart to find_new_unsupported_specifics
    (which only checks against source_text) -- added same day as the
    executor persona-history guard, closing the seam a hostile-review
    control ("strengthen this with a personal example") would otherwise
    have exposed: the executor had no persona-factual boundary at all."""
    authorized_corpus = ARTICLE_SOURCE_EXCERPT + "\n\n" + PIXEL_CANON_EXCERPT
    original = "A plain draft with no first-person biographical claims at all."

    # A genuinely new fabricated episode (number signal) must be flagged.
    revised_fabricated = original + " In 2019 I visited CERN and watched physicists debate the data live."
    hits = g.find_new_unsupported_personal_history(original, revised_fabricated, authorized_corpus)
    check(
        "a newly introduced fabricated personal episode (new number) is flagged",
        any(r == "possible_number_not_in_authorized_corpus" and "2019" in reason for r, reason in hits),
    )

    # The same episode already present in BOTH original and revised (i.e.
    # NOT newly introduced by this revision) must not be flagged -- this is
    # the diff-based framing, deliberately not a whole-draft check, so a
    # pre-existing issue the writer stage already logged advisory-only
    # doesn't get blamed on the executor.
    already_present = original + " In 2019 I visited CERN and watched physicists debate the data live."
    hits_unchanged = g.find_new_unsupported_personal_history(already_present, already_present, authorized_corpus)
    check(
        "an issue present in BOTH original and revised (unchanged by this revision) is NOT flagged as new",
        hits_unchanged == [],
    )

    # Using real, authorized canon material (the notary anecdote's
    # surrounding context, from PIXEL_CANON_EXCERPT) must not be flagged.
    revised_authorized = original + (
        ' The persona recalled a notary who wrote that the Deaf signer was '
        '"capable of reading the translated language and therefore understood what he signed."'
    )
    hits_authorized = g.find_new_unsupported_personal_history(original, revised_authorized, authorized_corpus)
    check(
        "referencing real, authorized canon material is NOT flagged",
        not any(r == "quoted_text_not_in_authorized_corpus" for r, _ in hits_authorized),
    )

    check("empty revised_text -> no violations", g.find_new_unsupported_personal_history(original, "", authorized_corpus) == [])
    check("None original_text -> treated as empty, no crash", g.find_new_unsupported_personal_history(None, revised_fabricated, authorized_corpus) == hits)


def _lineage_source_hashes(lineage):
    return {e["source_hash"] for e in lineage.values() if e and e["source_hash"] is not None}


def _lineage_packet_hashes(lineage):
    return {e["packet_hash"] for e in lineage.values() if e and e["packet_hash"] is not None}


def test_evidence_lineage_entry():
    check("entry with both hashes None -> None (nothing to report)", g.evidence_lineage_entry(None, None, "validator_stamped", "validator_stamped") is None)
    entry = g.evidence_lineage_entry("sh1", "ph1", "present_in_actual_prompt", "declared_shared_packet")
    check(
        "entry carries source_hash/packet_hash and SEPARATE source_verification/packet_verification",
        entry == {
            "source_hash": "sh1", "packet_hash": "ph1",
            "source_verification": "present_in_actual_prompt", "packet_verification": "declared_shared_packet",
        },
    )
    check(
        "a stage's source_verification and packet_verification can legitimately differ in strength "
        "(the containment check proves the text, not the packet's other metadata)",
        entry["source_verification"] != entry["packet_verification"],
    )
    try:
        g.evidence_lineage_entry("sh1", "ph1", "trust_me_bro", "declared_shared_packet")
        check("unrecognized source_verification string raises", False)
    except ValueError:
        check("unrecognized source_verification string raises", True)
    try:
        g.evidence_lineage_entry("sh1", "ph1", "validator_stamped", "trust_me_bro")
        check("unrecognized packet_verification string raises", False)
    except ValueError:
        check("unrecognized packet_verification string raises", True)


def test_build_evidence_lineage():
    packet = g.build_evidence_packet(SOURCE)
    sh, ph = packet["source_hash"], packet["evidence_packet_hash"]

    planner = g.evidence_lineage_entry(sh, ph, "validator_stamped", "validator_stamped")
    writer = g.evidence_lineage_entry(sh, ph, "present_in_actual_prompt", "declared_shared_packet")
    reviewer = g.evidence_lineage_entry(sh, ph, "declared_shared_packet", "declared_shared_packet")
    executor = g.evidence_lineage_entry(sh, ph, "declared_shared_packet", "declared_shared_packet")

    all_ran = g.build_evidence_lineage(planner, writer, reviewer, executor)
    check("lineage has all 4 keys", set(all_ran.keys()) == {"planner", "writer", "reviewer", "executor"})
    check("all 4 stages -> exactly one distinct source_hash", len(_lineage_source_hashes(all_ran)) == 1)
    check("all 4 stages -> exactly one distinct packet_hash", len(_lineage_packet_hashes(all_ran)) == 1)
    check(
        "per-stage verification strength is preserved per-identity, not collapsed into one label",
        all_ran["planner"]["source_verification"] == "validator_stamped"
        and all_ran["writer"]["source_verification"] == "present_in_actual_prompt"
        and all_ran["writer"]["packet_verification"] == "declared_shared_packet"
        and all_ran["reviewer"]["source_verification"] == "declared_shared_packet",
    )

    partial = g.build_evidence_lineage(planner, writer, None, None)
    check("reviewer/executor didn't run -> their entries are None, not fabricated", partial["reviewer"] is None and partial["executor"] is None)
    check("planner/writer still recorded even when reviewer/executor didn't run", partial["planner"] is not None and partial["writer"] is not None)
    check("acceptance check tolerates skipped stages: non-None source_hashes still all equal", len(_lineage_source_hashes(partial)) == 1)

    no_entries = g.build_evidence_lineage(None, None, None, None)
    check("nothing supplied -> every entry is None (nothing to prove)", all(v is None for v in no_entries.values()))

    # REGRESSION for the exact weakness caught on review, twice: (a) a
    # mismatched SOURCE TEXT must be visible as a real inequality, and (b) a
    # mismatched PACKET (e.g. same source_text, different truncation
    # metadata -- see build_evidence_packet's own collision regression test)
    # must ALSO be visible as a real inequality even when source_hash still
    # matches -- collapsing to source_hash alone would hide exactly this.
    other_packet = g.build_evidence_packet(SOURCE, source_max_chars=len(SOURCE))  # same text, source_truncated=True -> different packet_hash
    check("sanity: same source text, different packet construction -> same source_hash but different packet_hash", other_packet["source_hash"] == sh and other_packet["evidence_packet_hash"] != ph)

    mismatched_source = g.build_evidence_lineage(
        planner, g.evidence_lineage_entry("a-different-source-hash-entirely", ph, "present_in_actual_prompt", "declared_shared_packet"), reviewer, executor,
    )
    check("a genuinely mismatched SOURCE hash produces a real inequality the acceptance check would catch", len(_lineage_source_hashes(mismatched_source)) > 1)

    mismatched_packet = g.build_evidence_lineage(
        planner, g.evidence_lineage_entry(other_packet["source_hash"], other_packet["evidence_packet_hash"], "present_in_actual_prompt", "declared_shared_packet"), reviewer, executor,
    )
    check(
        "a stage with the SAME source_hash but a DIFFERENT packet_hash is caught by the packet-equality "
        "check even though source-equality alone would have missed it",
        len(_lineage_source_hashes(mismatched_packet)) == 1 and len(_lineage_packet_hashes(mismatched_packet)) > 1,
    )


def test_persona_factual_lineage_entry():
    check(
        "entry with context_hash=None -> None (nothing to report)",
        g.persona_factual_lineage_entry("Pixel Nova", None, 2, "real_person_evidence", "present_in_actual_prompt") is None,
    )
    entry = g.persona_factual_lineage_entry("Pixel Nova", "ch1", 2, "real_person_evidence", "present_in_actual_prompt")
    check(
        "entry carries persona_name/context_hash/schema_version/provenance_mode/verification",
        entry == {
            "persona_name": "Pixel Nova", "context_hash": "ch1", "schema_version": 2,
            "provenance_mode": "real_person_evidence", "verification": "present_in_actual_prompt",
        },
    )
    try:
        g.persona_factual_lineage_entry("Pixel Nova", "ch1", 2, "real_person_evidence", "trust_me_bro")
        check("unrecognized verification string raises", False)
    except ValueError:
        check("unrecognized verification string raises", True)


def test_build_persona_factual_lineage():
    writer = g.persona_factual_lineage_entry("Pixel Nova", "ch1", 2, "real_person_evidence", "present_in_actual_prompt")
    reviewer = g.persona_factual_lineage_entry("Pixel Nova", "ch1", 2, "real_person_evidence", "declared_shared_context")

    lineage = g.build_persona_factual_lineage(writer, reviewer)
    check("lineage has all 3 keys (writer/reviewer/executor)", set(lineage.keys()) == {"writer", "reviewer", "executor"})
    check("executor defaults to None (no current caller wires persona_factual_context into the executor)", lineage["executor"] is None)
    check(
        "writer/reviewer entries preserved, distinct verification strengths per stage",
        lineage["writer"]["verification"] == "present_in_actual_prompt"
        and lineage["reviewer"]["verification"] == "declared_shared_context",
    )

    # REGRESSION: two personas' entries must not be silently conflatable --
    # a fictional persona's editorial_canon context and Pixel's
    # real_person_evidence context must remain distinguishable per stage,
    # not collapsed into one shared "provenance" the way source_hash alone
    # once collapsed evidence identity (same lesson, different lineage).
    maya_writer = g.persona_factual_lineage_entry("Maya Flux", "ch2", 2, "editorial_canon", "present_in_actual_prompt")
    check(
        "different personas' provenance_mode is preserved per-entry, not overwritten",
        writer["provenance_mode"] == "real_person_evidence" and maya_writer["provenance_mode"] == "editorial_canon",
    )

    empty = g.build_persona_factual_lineage(None, None)
    check("nothing supplied -> writer/reviewer are None, executor still None", all(v is None for v in empty.values()))


if __name__ == "__main__":
    test_build_evidence_packet()
    test_not_found()
    test_interpretation_is_structurally_separate_from_evidence()
    test_source_grounded()
    test_malformed_shape()
    test_validate_brief()
    test_legacy_schema_gate()
    test_writer_prompt_block()
    test_find_new_unsupported_specifics()
    test_scan_free_prose_field()
    test_validate_brief_does_not_touch_free_prose_fields()
    test_evidence_text()
    test_build_persona_factual_context()
    test_scan_draft_for_unsupported_specifics()
    test_find_new_unsupported_personal_history()
    test_evidence_lineage_entry()
    test_build_evidence_lineage()
    test_persona_factual_lineage_entry()
    test_build_persona_factual_lineage()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All grounding.py unit/schema tests passed.")
    sys.exit(0)
