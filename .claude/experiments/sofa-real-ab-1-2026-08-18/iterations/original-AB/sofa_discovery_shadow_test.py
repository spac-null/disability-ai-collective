#!/usr/bin/env python3
"""
sofa_discovery_shadow_test.py — focused tests for the Sofa Architecture V1
Shadow Slice 1 module (automation/orchestrator/sofa_discovery_shadow.py).

SHADOW ONLY. These tests exercise a module that is not imported by, wired
into, or reachable from the live pipeline. No network calls — every LLM
call in this module is injected, and every test here supplies a
deterministic stub instead of a real client.

Run (from repo root):
  python3 automation/sofa_discovery_shadow_test.py
or:
  python3 -m pytest automation/sofa_discovery_shadow_test.py -q
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.sofa_discovery_shadow import (  # noqa: E402
    SofaShadowError,
    build_discovery_packet,
    validate_discovery_packet,
    to_writer_context,
    assert_no_persona_leakage,
    build_shadow_writer_prompt,
    run_shadow_discovery,
    run_shadow_writer,
    run_deterministic_prescan,
    run_shadow_grounding_audit,
    grounding_audit_passes,
    grounding_audit_status,
    discovery_packet_eligible_for_comparison,
    EVIDENCE, EDITORIAL_INTERPRETATION, EDITORIAL_GUIDANCE, EDITORIAL_METADATA,
    GROUNDING_BOUNDARY, AUDIT_SUPPORTED, AUDIT_UNSUPPORTED, AUDIT_UNCERTAIN,
    DISCOVERY_LENS_UNATTRIBUTED,
    GROUNDING_STATUS_GROUNDED, GROUNDING_STATUS_REVIEWABLE_WITH_UNCERTAINTY, GROUNDING_STATUS_FAIL,
)
from orchestrator.grounding import build_evidence_packet  # noqa: E402


SOURCE_TEXT = (
    "The council's own maintenance log shows the lift at Elm Street station was "
    "marked \"temporarily out of service\" on eleven separate occasions in 2024, "
    "totalling 340 days. The log records no single occasion longer than 34 days. "
    "A rider named Joan Ferris told the transport committee in March that she had "
    "stopped using the station entirely. The committee's own accessibility audit, "
    "filed in January, does not mention the lift at all."
)


def _commission_brief(**overrides):
    brief = {
        "source_decision": "commission",
        "source_anchor_examined": "The log records no single occasion longer than 34 days.",
        "hidden_mechanism": (
            "A status label meant to describe a brief interruption becomes, through repetition, "
            "a permanent condition that the record itself is structured to never show as permanent."
        ),
        "why_disability_knowledge_changes_subject": (
            "Knowing that access categories are audited by their longest single instance, not "
            "their frequency, reveals why 'temporarily out of service' can describe a de facto "
            "year without ever being false on any one day."
        ),
        "persona": "Maya Flux",
        "eligible_execution_possible": True,
    }
    brief.update(overrides)
    return brief


def _evidence_packet():
    return build_evidence_packet(SOURCE_TEXT, source_origin="fixture")


def _valid_packet_kwargs():
    return dict(
        disturbance="Eleven short outages add up to almost a year without ever registering as one.",
        reader_contract="A label can be true every single day and still hide the truth of a whole year.",
        reader_contract_distinctness_reason="This is about what a reader notices, not the audit mechanism itself.",
        supporting_evidence=[
            {"kind": "measurement", "source_excerpt": "totalling 340 days",
             "note": "the real annual total", "note_type": EDITORIAL_INTERPRETATION},
            {"kind": "document",
             "source_excerpt": "The committee's own accessibility audit, filed in January, does not mention the lift at all.",
             "note": "the audit's blind spot", "note_type": EDITORIAL_INTERPRETATION},
        ],
        carrying_material=[
            {"kind": "person_action",
             "source_excerpt": "A rider named Joan Ferris told the transport committee in March that she had stopped using the station entirely.",
             "note": "a person who acted on the pattern", "note_type": EDITORIAL_GUIDANCE},
            {"kind": "unresolved_absence", "source_excerpt": "",
             "note": "no explanation in the record for why the audit omitted the lift", "note_type": EDITORIAL_INTERPRETATION},
        ],
        known_gaps=["The evidence does not say why the January audit omitted the lift."],
        form_suggestion="essay",
    )


class PacketSchemaTests(unittest.TestCase):
    def test_valid_packet_builds_and_validates(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ok, errors = validate_discovery_packet(packet)
        self.assertTrue(ok, errors)
        for key in ("source_anchor", "disturbance", "hidden_mechanism", "discovery_lens", "byline_persona",
                    "reader_contract", "reader_contract_distinctness_reason", "form_suggestion"):
            self.assertIn(key, packet)

    def test_required_fields_present(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        for key in ("supporting_evidence", "carrying_material", "known_gaps"):
            self.assertIn(key, packet)


class EpistemicTypingTests(unittest.TestCase):
    def test_every_field_has_explicit_epistemic_type(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        self.assertEqual(packet["source_anchor"]["epistemic_type"], EVIDENCE)
        self.assertEqual(packet["hidden_mechanism"]["epistemic_type"], EDITORIAL_INTERPRETATION)
        self.assertEqual(packet["disturbance"]["epistemic_type"], EDITORIAL_INTERPRETATION)
        self.assertEqual(packet["reader_contract"]["epistemic_type"], EDITORIAL_GUIDANCE)
        self.assertEqual(packet["discovery_lens"]["epistemic_type"], EDITORIAL_METADATA)
        self.assertEqual(packet["byline_persona"]["epistemic_type"], EDITORIAL_METADATA)
        for item in packet["supporting_evidence"] + packet["carrying_material"]:
            self.assertEqual(item["source_excerpt"]["epistemic_type"], EVIDENCE)
            self.assertIn(item["editorial_note"]["epistemic_type"], (EDITORIAL_GUIDANCE, EDITORIAL_INTERPRETATION))
        for gap in packet["known_gaps"]:
            self.assertEqual(gap["epistemic_type"], GROUNDING_BOUNDARY)

    def test_hidden_mechanism_never_labeled_as_evidence(self):
        """The exact epistemic correction the task required: hidden_mechanism
        must never be typed EVIDENCE, no matter what."""
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        self.assertNotEqual(packet["hidden_mechanism"]["epistemic_type"], EVIDENCE)

    def test_invalid_epistemic_type_rejected_by_validator(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        packet["reader_contract"]["epistemic_type"] = "SOURCE_FACT"  # not a real type
        ok, errors = validate_discovery_packet(packet)
        self.assertFalse(ok)
        self.assertTrue(any("epistemic_type" in e for e in errors))

    def test_material_editorial_note_cannot_be_typed_evidence(self):
        """Slice 1.1 Problem 1: an editorial note describing a piece of
        evidence must never itself be typed EVIDENCE, even if a caller
        tries to force it after the fact."""
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        packet["supporting_evidence"][0]["editorial_note"]["epistemic_type"] = EVIDENCE
        ok, errors = validate_discovery_packet(packet)
        self.assertFalse(ok)
        self.assertTrue(any("editorial_note" in e for e in errors))

    def test_material_note_type_rejected_when_missing_but_note_present(self):
        kwargs = _valid_packet_kwargs()
        kwargs["supporting_evidence"] = [
            {"kind": "measurement", "source_excerpt": "totalling 340 days", "note": "a real note with no type"},
        ]
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(_commission_brief(), _evidence_packet(), **kwargs)

    def test_known_gaps_typed_grounding_boundary_not_evidence(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        for gap in packet["known_gaps"]:
            self.assertEqual(gap["epistemic_type"], GROUNDING_BOUNDARY)
            self.assertNotEqual(gap["epistemic_type"], EVIDENCE)

    def test_known_gap_typed_as_evidence_rejected_by_validator(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        packet["known_gaps"][0]["epistemic_type"] = EVIDENCE
        ok, errors = validate_discovery_packet(packet)
        self.assertFalse(ok)
        self.assertTrue(any("known_gaps" in e for e in errors))


class GroundingPreservedTests(unittest.TestCase):
    def test_source_anchor_must_exist_in_source_text(self):
        brief = _commission_brief(source_anchor_examined="This sentence is not in the source at all.")
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(brief, _evidence_packet(), **_valid_packet_kwargs())

    def test_fabricated_carrying_material_excerpt_rejected(self):
        kwargs = _valid_packet_kwargs()
        kwargs["carrying_material"] = [
            {"kind": "quote", "source_excerpt": "This quote was never said by anyone in the source.",
             "note": "fabricated", "note_type": EDITORIAL_INTERPRETATION},
        ]
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(_commission_brief(), _evidence_packet(), **kwargs)

    def test_fabricated_supporting_evidence_excerpt_rejected(self):
        kwargs = _valid_packet_kwargs()
        kwargs["supporting_evidence"] = [
            {"kind": "measurement", "source_excerpt": "9,999 days, a number invented for this test",
             "note": "fabricated", "note_type": EDITORIAL_INTERPRETATION},
        ]
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(_commission_brief(), _evidence_packet(), **kwargs)

    def test_unresolved_absence_allowed_with_empty_excerpt(self):
        kwargs = _valid_packet_kwargs()
        kwargs["carrying_material"] = [
            {"kind": "unresolved_absence", "source_excerpt": "", "note": "no stated reason",
             "note_type": EDITORIAL_INTERPRETATION},
        ]
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **kwargs)
        self.assertEqual(len(packet["carrying_material"]), 1)

    def test_non_absence_kind_requires_an_excerpt(self):
        kwargs = _valid_packet_kwargs()
        kwargs["carrying_material"] = [
            {"kind": "quote", "source_excerpt": "", "note": "missing excerpt, wrong kind for that",
             "note_type": EDITORIAL_INTERPRETATION},
        ]
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(_commission_brief(), _evidence_packet(), **kwargs)


class MechanismInheritedNotRegeneratedTests(unittest.TestCase):
    def test_hidden_mechanism_value_is_inherited_verbatim(self):
        brief = _commission_brief(hidden_mechanism="EXACT MECHANISM STRING FROM FABLE LAYER 1")
        # source_anchor must still be a real substring, unrelated to the mechanism text
        packet = build_discovery_packet(brief, _evidence_packet(), **_valid_packet_kwargs())
        self.assertEqual(packet["hidden_mechanism"]["value"], "EXACT MECHANISM STRING FROM FABLE LAYER 1")

    def test_declined_brief_never_reaches_discovery(self):
        brief = _commission_brief(source_decision="decline")
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(brief, _evidence_packet(), **_valid_packet_kwargs())

    def test_run_shadow_discovery_rejects_non_commission_brief_before_calling_model(self):
        calls = []

        def _spy_llm(system, user):
            calls.append((system, user))
            return "{}"

        brief = _commission_brief(source_decision="defer")
        with self.assertRaises(SofaShadowError):
            run_shadow_discovery(brief, _evidence_packet(), _spy_llm)
        self.assertEqual(calls, [], "model must never be called for a non-commissioned brief")


class ReaderContractDistinctnessTests(unittest.TestCase):
    def test_reader_contract_identical_to_mechanism_rejected(self):
        brief = _commission_brief(hidden_mechanism="The label hides the total.")
        kwargs = _valid_packet_kwargs()
        kwargs["reader_contract"] = "The label hides the total."  # identical, case aside
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(brief, _evidence_packet(), **kwargs)

    def test_reader_contract_case_insensitive_match_still_rejected(self):
        brief = _commission_brief(hidden_mechanism="The label hides the total.")
        kwargs = _valid_packet_kwargs()
        kwargs["reader_contract"] = "THE LABEL HIDES THE TOTAL."
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(brief, _evidence_packet(), **kwargs)


class WriterContextExclusionTests(unittest.TestCase):
    def test_writer_context_excludes_internal_only_commission_fields(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ctx = to_writer_context(packet, SOURCE_TEXT)
        blob = json.dumps(ctx)
        self.assertNotIn("why_disability_knowledge_changes_subject", blob)
        self.assertNotIn("eligible_execution_possible", blob)

    def test_writer_context_excludes_distinctness_reason(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ctx = to_writer_context(packet, SOURCE_TEXT)
        self.assertNotIn("reader_contract_distinctness_reason", ctx)

    def test_writer_context_rejects_smuggled_persona_material(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        packet["disturbance"]["value"] = "YOUR WOUND is the reason this matters."
        with self.assertRaises(SofaShadowError):
            to_writer_context(packet, SOURCE_TEXT)

    def test_writer_prompt_contains_no_persona_roleplay_language(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ctx = to_writer_context(packet, SOURCE_TEXT)
        system, user = build_shadow_writer_prompt(ctx)
        for phrase in ("WRITE LIKE THIS PERSON", "YOUR WOUND", "AUTHORIZED PERSONAL HISTORY",
                       "You are a disabled person"):
            self.assertNotIn(phrase, system)
            self.assertNotIn(phrase, user)

    def test_assert_no_persona_leakage_catches_a_planted_phrase(self):
        with self.assertRaises(SofaShadowError):
            assert_no_persona_leakage("Some text containing WRITE LIKE THIS PERSON in it.")

    def test_assert_no_persona_leakage_passes_clean_text(self):
        assert_no_persona_leakage("Ordinary house-style prose instructions with no roleplay language.")


class KnownGapsPreservedTests(unittest.TestCase):
    def test_known_gaps_survive_into_writer_context(self):
        kwargs = _valid_packet_kwargs()
        kwargs["known_gaps"] = ["The evidence does not say who filed the January audit."]
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **kwargs)
        ctx = to_writer_context(packet, SOURCE_TEXT)
        self.assertEqual(ctx["known_gaps"], ["The evidence does not say who filed the January audit."])

    def test_known_gaps_must_be_list_of_strings(self):
        kwargs = _valid_packet_kwargs()
        kwargs["known_gaps"] = [{"not": "a string"}]
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(_commission_brief(), _evidence_packet(), **kwargs)


class FailClosedTests(unittest.TestCase):
    def test_missing_hidden_mechanism_fails_closed(self):
        brief = _commission_brief()
        del brief["hidden_mechanism"]
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(brief, _evidence_packet(), **_valid_packet_kwargs())

    def test_missing_source_anchor_fails_closed(self):
        brief = _commission_brief()
        del brief["source_anchor_examined"]
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(brief, _evidence_packet(), **_valid_packet_kwargs())

    def test_empty_source_text_fails_closed(self):
        empty_packet = build_evidence_packet(None, source_origin="none")
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(_commission_brief(), empty_packet, **_valid_packet_kwargs())

    def test_empty_reader_contract_fails_closed(self):
        kwargs = _valid_packet_kwargs()
        kwargs["reader_contract"] = ""
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(_commission_brief(), _evidence_packet(), **kwargs)

    def test_malformed_material_list_fails_closed(self):
        kwargs = _valid_packet_kwargs()
        kwargs["carrying_material"] = "not a list"
        with self.assertRaises(SofaShadowError):
            build_discovery_packet(_commission_brief(), _evidence_packet(), **kwargs)

    def test_to_writer_context_fails_closed_on_invalid_packet(self):
        with self.assertRaises(SofaShadowError):
            to_writer_context({"not": "a valid packet"}, SOURCE_TEXT)


class ShadowDiscoveryOrchestrationTests(unittest.TestCase):
    def test_run_shadow_discovery_parses_model_json_and_builds_packet(self):
        def _stub_llm(system, user):
            return json.dumps({
                "disturbance": "Eleven short outages never register as the near-year they add up to.",
                "reader_contract": "A record can be accurate every day and still misrepresent the year.",
                "reader_contract_distinctness_reason": "Concerns reader interest, not the audit mechanism.",
                "supporting_evidence": [
                    {"kind": "measurement", "source_excerpt": "totalling 340 days",
                     "note": "the real total", "note_type": EDITORIAL_INTERPRETATION},
                ],
                "carrying_material": [
                    {"kind": "person_action",
                     "source_excerpt": "A rider named Joan Ferris told the transport committee in March that she had stopped using the station entirely.",
                     "note": "a person who acted on the pattern", "note_type": EDITORIAL_GUIDANCE},
                ],
                "known_gaps": ["The evidence does not say why the audit omitted the lift."],
                "form_suggestion": "essay",
            })

        packet = run_shadow_discovery(_commission_brief(), _evidence_packet(), _stub_llm, discovery_lens="Maya Flux")
        ok, errors = validate_discovery_packet(packet)
        self.assertTrue(ok, errors)
        self.assertEqual(packet["discovery_lens"]["value"], "Maya Flux")

    def test_run_shadow_discovery_rejects_unparseable_model_output(self):
        with self.assertRaises(SofaShadowError):
            run_shadow_discovery(_commission_brief(), _evidence_packet(), lambda s, u: "not json at all")

    def test_run_shadow_writer_returns_model_text(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ctx = to_writer_context(packet, SOURCE_TEXT)
        article = run_shadow_writer(ctx, lambda s, u: "TITLE\n\nBody text.")
        self.assertEqual(article, "TITLE\n\nBody text.")

    def test_run_shadow_writer_fails_closed_on_empty_model_output(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ctx = to_writer_context(packet, SOURCE_TEXT)
        with self.assertRaises(SofaShadowError):
            run_shadow_writer(ctx, lambda s, u: "")


# --------------------------------------------------------------------------- #
# Slice 1.1 — post-writer grounding audit tests
# --------------------------------------------------------------------------- #

def _full_packet():
    return build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())


class DeterministicPrescanTests(unittest.TestCase):
    def test_prescan_flags_invented_number(self):
        article = "The outage totalling 9,999,999 days was the real story."
        flags = run_deterministic_prescan(article, SOURCE_TEXT)
        self.assertTrue(any("number" in code for code, _ in flags))

    def test_prescan_clean_on_grounded_number(self):
        article = "The log shows totalling 340 days across the year."
        flags = run_deterministic_prescan(article, SOURCE_TEXT)
        self.assertEqual(flags, [])

    def test_prescan_does_not_catch_planted_causal_or_motive_overreach(self):
        """This is the exact class of failure the task requires a SEPARATE
        model-based audit for — the deterministic pass has no shape (no
        quote, no number, no proper noun) to catch these on, by design."""
        article = (
            "Nobody at the transport committee was lying about the lift. "
            "The omission did not happen by accident, and the status cannot legally "
            "outlast forty-five days."
        )
        flags = run_deterministic_prescan(article, SOURCE_TEXT)
        self.assertEqual(flags, [], "deterministic pre-scan is documented to miss this class; "
                                     "if this now fails, the model-audit layer is no longer necessary "
                                     "for this class and this test's premise should be revisited")


class ShadowGroundingAuditTests(unittest.TestCase):
    def test_audit_catches_planted_unsupported_factual_specificity(self):
        article = "The lift was out for 9,999,999 days, far more than the log shows."

        def _stub_llm(system, user):
            return json.dumps({"claims": [
                {"claim": "The lift was out for 9,999,999 days",
                 "verdict": AUDIT_UNSUPPORTED,
                 "reason": "no such figure appears in the source; the log's own total is 340 days"},
            ]})

        audit = run_shadow_grounding_audit(SOURCE_TEXT, _full_packet(), article, _stub_llm)
        self.assertTrue(any(c["verdict"] == AUDIT_UNSUPPORTED for c in audit["claims"]))
        ok, reasons = grounding_audit_passes(audit)
        self.assertFalse(ok)
        self.assertTrue(reasons)

    def test_audit_catches_planted_motive_and_causality_claims(self):
        """Regression for the exact SYNTH-1 failures the task names:
        'Nobody was lying', 'did not appear by accident', 'cannot legally
        outlast forty-five days' — none of these trip the deterministic
        pre-scan; the audit call must be the layer that catches them."""
        article = (
            "Nobody on the other end of those calls was lying. The gap did not appear "
            "by accident, and the hold cannot legally outlast forty-five days."
        )

        def _stub_llm(system, user):
            return json.dumps({"claims": [
                {"claim": "Nobody on the other end of those calls was lying",
                 "verdict": AUDIT_UNSUPPORTED,
                 "reason": "the source establishes no one's knowledge or intent"},
                {"claim": "The gap did not appear by accident",
                 "verdict": AUDIT_UNSUPPORTED,
                 "reason": "the source never establishes intentionality behind the gap"},
                {"claim": "the hold cannot legally outlast forty-five days",
                 "verdict": AUDIT_UNSUPPORTED,
                 "reason": "the source states a policy definition, not a legal enforceability finding"},
            ]})

        audit = run_shadow_grounding_audit(SOURCE_TEXT, _full_packet(), article, _stub_llm)
        unsupported = [c for c in audit["claims"] if c["verdict"] == AUDIT_UNSUPPORTED]
        self.assertEqual(len(unsupported), 3)
        ok, reasons = grounding_audit_passes(audit)
        self.assertFalse(ok)

    def test_clean_grounded_article_can_pass(self):
        article = "The log shows the lift totalling 340 days out, with no single occasion longer than 34 days."

        def _stub_llm(system, user):
            return json.dumps({"claims": []})

        audit = run_shadow_grounding_audit(SOURCE_TEXT, _full_packet(), article, _stub_llm)
        ok, reasons = grounding_audit_passes(audit)
        self.assertTrue(ok, reasons)

    def test_undocumented_uncertain_treated_as_failure(self):
        def _stub_llm(system, user):
            return json.dumps({"claims": [
                {"claim": "Something plausible but unverifiable", "verdict": AUDIT_UNCERTAIN, "reason": ""},
            ]})

        audit = run_shadow_grounding_audit(SOURCE_TEXT, _full_packet(), "some article", _stub_llm)
        ok, reasons = grounding_audit_passes(audit)
        self.assertFalse(ok)

    def test_documented_uncertain_does_not_fail_the_audit(self):
        def _stub_llm(system, user):
            return json.dumps({"claims": [
                {"claim": "Something plausible but unverifiable", "verdict": AUDIT_UNCERTAIN,
                 "reason": "the source does not say either way; would need the full maintenance log"},
            ]})

        audit = run_shadow_grounding_audit(SOURCE_TEXT, _full_packet(), "some article", _stub_llm)
        ok, reasons = grounding_audit_passes(audit)
        self.assertTrue(ok, reasons)

    def test_malformed_claim_verdict_fails_closed(self):
        def _stub_llm(system, user):
            return json.dumps({"claims": [{"claim": "x", "verdict": "PROBABLY_FINE"}]})

        with self.assertRaises(SofaShadowError):
            run_shadow_grounding_audit(SOURCE_TEXT, _full_packet(), "some article", _stub_llm)

    def test_unparseable_audit_output_fails_closed(self):
        with self.assertRaises(SofaShadowError):
            run_shadow_grounding_audit(SOURCE_TEXT, _full_packet(), "some article", lambda s, u: "not json")


class EligibilityTests(unittest.TestCase):
    """§5: packet substring validation and article grounding are two
    different checks and must never be reported as one 'grounding'
    verdict."""

    def test_eligible_when_both_packet_and_audit_pass(self):
        packet = _full_packet()
        clean_audit = {"claims": []}
        eligible, status, reasons = discovery_packet_eligible_for_comparison(packet, clean_audit)
        self.assertTrue(eligible, reasons)
        self.assertEqual(status, GROUNDING_STATUS_GROUNDED)

    def test_eligible_but_reviewable_when_audit_has_documented_uncertainty(self):
        packet = _full_packet()
        uncertain_audit = {"claims": [
            {"claim": "x", "verdict": AUDIT_UNCERTAIN, "reason": "cannot verify either way from this source"},
        ]}
        eligible, status, reasons = discovery_packet_eligible_for_comparison(packet, uncertain_audit)
        self.assertTrue(eligible)
        self.assertEqual(status, GROUNDING_STATUS_REVIEWABLE_WITH_UNCERTAINTY)
        self.assertTrue(reasons, "a REVIEWABLE_WITH_UNCERTAINTY result must visibly carry its uncertainty reasons")

    def test_not_eligible_when_audit_has_unsupported_claim_even_if_packet_valid(self):
        packet = _full_packet()
        bad_audit = {"claims": [{"claim": "x", "verdict": AUDIT_UNSUPPORTED, "reason": "not in source"}]}
        eligible, status, reasons = discovery_packet_eligible_for_comparison(packet, bad_audit)
        self.assertFalse(eligible)
        self.assertEqual(status, GROUNDING_STATUS_FAIL)
        self.assertTrue(any("ARTICLE" in r for r in reasons))

    def test_not_eligible_when_packet_invalid_even_if_audit_clean(self):
        broken_packet = {"not": "a valid packet"}
        clean_audit = {"claims": []}
        eligible, status, reasons = discovery_packet_eligible_for_comparison(broken_packet, clean_audit)
        self.assertFalse(eligible)
        self.assertTrue(any("PACKET" in r for r in reasons))

    def test_packet_validity_alone_is_never_reported_as_article_grounding(self):
        """A valid packet + no audit run at all must not be treated as
        'grounded' — this is the exact conflation the task forbids."""
        packet = _full_packet()
        eligible, status, reasons = discovery_packet_eligible_for_comparison(packet, {"not": "a real audit"})
        self.assertFalse(eligible)


# --------------------------------------------------------------------------- #
# Real Article Test 1 — Phase 0 correction regression tests
# --------------------------------------------------------------------------- #

class PersonaLeakageFalsePositiveTests(unittest.TestCase):
    """0A: ordinary words that happen to match a banned KEY name must not
    trigger persona leakage when they occur inside legitimate prose
    VALUES — only an actual dictionary key, or a distinctive multi-word
    boilerplate phrase in raw text, is a real violation."""

    def test_raw_text_reason_word_does_not_trigger(self):
        assert_no_persona_leakage("The committee gave the reason for the delay in its own minutes.")

    def test_raw_text_artistic_canon_does_not_trigger(self):
        assert_no_persona_leakage("She has been part of the artistic canon for three decades.")

    def test_raw_text_a_wound_does_not_trigger(self):
        assert_no_persona_leakage("The report describes a wound that never fully healed.")

    def test_raw_text_her_mood_does_not_trigger(self):
        assert_no_persona_leakage("Her mood shifted the moment the letter arrived.")

    def test_structured_context_with_reason_word_in_value_does_not_trigger(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        packet["disturbance"]["value"] = "The committee never gave a reason, which is itself the disturbance."
        ctx = to_writer_context(packet, SOURCE_TEXT)  # must not raise
        self.assertIn("reason", ctx["disturbance"])

    def test_structured_context_with_wound_and_mood_and_canon_in_source_does_not_trigger(self):
        source_with_words = SOURCE_TEXT + " Her mood, an old wound, and the artistic canon were never mentioned."
        packet = build_discovery_packet(
            _commission_brief(), build_evidence_packet(source_with_words, source_origin="fixture"),
            **_valid_packet_kwargs(),
        )
        ctx = to_writer_context(packet, source_with_words)  # must not raise
        self.assertIn("wound", ctx["reference_source"])

    def test_actual_banned_key_in_structured_data_still_caught(self):
        """Positive control: a REAL key named 'wound' (not just the word
        inside a value) must still be rejected by the recursive key
        scanner directly — to_writer_context's own output is a fixed,
        narrow whitelist of keys by construction, so this exercises the
        scanner (`_find_banned_keys`, imported for this one test) against
        an arbitrary nested structure the way it would be used if a future
        writer-context field ever became a nested dict."""
        from orchestrator.sofa_discovery_shadow import _find_banned_keys, _PERSONA_ROLEPLAY_KEYS
        smuggled = {"disturbance": "prose text", "nested": {"wound": "an actual key, not prose"}}
        hits = _find_banned_keys(smuggled, _PERSONA_ROLEPLAY_KEYS)
        self.assertTrue(hits)
        self.assertTrue(any("wound" in h for h in hits))

    def test_find_banned_keys_ignores_the_same_word_in_a_value(self):
        from orchestrator.sofa_discovery_shadow import _find_banned_keys, _PERSONA_ROLEPLAY_KEYS
        clean = {"disturbance": "a story about an old wound that never healed"}
        hits = _find_banned_keys(clean, _PERSONA_ROLEPLAY_KEYS)
        self.assertEqual(hits, [])

    def test_actual_boilerplate_phrase_in_raw_text_still_caught(self):
        with self.assertRaises(SofaShadowError):
            assert_no_persona_leakage("Some preamble. WRITE LIKE THIS PERSON. More text.")


class DiscoveryLensByLinePersonaSeparationTests(unittest.TestCase):
    """0B: discovery_lens must never be silently copied from byline_persona."""

    def test_discovery_lens_defaults_to_unattributed_not_persona(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        self.assertEqual(packet["discovery_lens"]["value"], DISCOVERY_LENS_UNATTRIBUTED)
        self.assertEqual(packet["byline_persona"]["value"], "Maya Flux")
        self.assertNotEqual(packet["discovery_lens"]["value"], packet["byline_persona"]["value"])

    def test_discovery_lens_never_equals_byline_persona_by_default_even_when_persona_changes(self):
        brief = _commission_brief(persona="Zen Circuit")
        packet = build_discovery_packet(brief, _evidence_packet(), **_valid_packet_kwargs())
        self.assertEqual(packet["byline_persona"]["value"], "Zen Circuit")
        self.assertEqual(packet["discovery_lens"]["value"], DISCOVERY_LENS_UNATTRIBUTED)
        self.assertNotEqual(packet["discovery_lens"]["value"], packet["byline_persona"]["value"])

    def test_explicit_discovery_lens_is_preserved_when_actually_provided(self):
        kwargs = _valid_packet_kwargs()
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(),
                                         discovery_lens="Pixel Nova", **kwargs)
        self.assertEqual(packet["discovery_lens"]["value"], "Pixel Nova")
        self.assertEqual(packet["byline_persona"]["value"], "Maya Flux")

    def test_writer_context_exposes_both_fields_separately(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ctx = to_writer_context(packet, SOURCE_TEXT)
        self.assertIn("discovery_lens", ctx)
        self.assertIn("byline_persona", ctx)
        self.assertEqual(ctx["discovery_lens"], DISCOVERY_LENS_UNATTRIBUTED)


class ReferenceSourceTests(unittest.TestCase):
    """0C: the writer must receive the full source text as a reference,
    in addition to the ranked material, with an explicit hierarchy."""

    def test_writer_context_requires_source_text(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        with self.assertRaises(SofaShadowError):
            to_writer_context(packet, "")
        with self.assertRaises(SofaShadowError):
            to_writer_context(packet, None)

    def test_writer_context_reference_source_is_the_full_source_text(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ctx = to_writer_context(packet, SOURCE_TEXT)
        self.assertEqual(ctx["reference_source"], SOURCE_TEXT)

    def test_writer_prompt_states_the_material_hierarchy(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ctx = to_writer_context(packet, SOURCE_TEXT)
        system, user = build_shadow_writer_prompt(ctx)
        self.assertIn("MATERIAL HIERARCHY", system)
        self.assertIn("REFERENCE SOURCE", user)
        self.assertIn(SOURCE_TEXT, user)

    def test_writer_prompt_reference_source_does_not_override_ranked_spine_instruction(self):
        packet = build_discovery_packet(_commission_brief(), _evidence_packet(), **_valid_packet_kwargs())
        ctx = to_writer_context(packet, SOURCE_TEXT)
        system, _ = build_shadow_writer_prompt(ctx)
        self.assertIn("do not abandon", system.lower())


class GroundingStatusTriStateTests(unittest.TestCase):
    """Uncertainty terminology correction: GROUNDED / REVIEWABLE_WITH_UNCERTAINTY / FAIL,
    never a bare PASS that hides a documented uncertainty."""

    def test_no_claims_is_grounded(self):
        status, reasons = grounding_audit_status({"claims": []})
        self.assertEqual(status, GROUNDING_STATUS_GROUNDED)
        self.assertEqual(reasons, [])

    def test_documented_uncertain_is_reviewable_not_grounded(self):
        status, reasons = grounding_audit_status({"claims": [
            {"claim": "x", "verdict": AUDIT_UNCERTAIN, "reason": "would need the full log to verify"},
        ]})
        self.assertEqual(status, GROUNDING_STATUS_REVIEWABLE_WITH_UNCERTAINTY)
        self.assertTrue(reasons)

    def test_undocumented_uncertain_is_fail_not_reviewable(self):
        status, reasons = grounding_audit_status({"claims": [
            {"claim": "x", "verdict": AUDIT_UNCERTAIN, "reason": ""},
        ]})
        self.assertEqual(status, GROUNDING_STATUS_FAIL)

    def test_unsupported_is_fail(self):
        status, reasons = grounding_audit_status({"claims": [
            {"claim": "x", "verdict": AUDIT_UNSUPPORTED, "reason": "not in source"},
        ]})
        self.assertEqual(status, GROUNDING_STATUS_FAIL)

    def test_mixed_supported_and_documented_uncertain_is_reviewable(self):
        status, reasons = grounding_audit_status({"claims": [
            {"claim": "x", "verdict": AUDIT_SUPPORTED, "reason": ""},
            {"claim": "y", "verdict": AUDIT_UNCERTAIN, "reason": "ambiguous but plausible"},
        ]})
        self.assertEqual(status, GROUNDING_STATUS_REVIEWABLE_WITH_UNCERTAINTY)

    def test_malformed_audit_is_fail(self):
        status, reasons = grounding_audit_status({"not": "a real audit"})
        self.assertEqual(status, GROUNDING_STATUS_FAIL)

    def test_grounding_audit_passes_wrapper_matches_status(self):
        ok, _ = grounding_audit_passes({"claims": [{"claim": "x", "verdict": AUDIT_UNCERTAIN, "reason": "documented"}]})
        self.assertTrue(ok)  # REVIEWABLE_WITH_UNCERTAINTY still passes the boolean wrapper
        ok2, _ = grounding_audit_passes({"claims": [{"claim": "x", "verdict": AUDIT_UNSUPPORTED, "reason": "no"}]})
        self.assertFalse(ok2)


if __name__ == "__main__":
    unittest.main()
