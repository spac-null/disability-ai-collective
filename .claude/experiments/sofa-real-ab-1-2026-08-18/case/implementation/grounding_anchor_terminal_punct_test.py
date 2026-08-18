#!/usr/bin/env python3
"""
grounding_anchor_terminal_punct_test.py — TEMP-WORKTREE-ONLY regression
tests for the narrow terminal-sentence-punctuation normalization added to
_validate_commission_grounding's anchor-in-explanation check (Sofa Real
Article Test 1 continuation).

Lives only in /tmp/cripminds-sofa-real-test-1 — never copied into the
live production checkout. Tests the exact helper
(_anchor_tied_to_explanation) and the full validate_source_decision path
so both the unit-level fix and its integration are verified before any
production patch decision is made.

Run: python3 automation/grounding_anchor_terminal_punct_test.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.grounding import (  # noqa: E402
    _anchor_tied_to_explanation,
    _strip_trailing_sentence_punct,
    validate_source_decision,
    build_evidence_packet,
)


class AnchorTiedToExplanationUnitTests(unittest.TestCase):
    # ---- Must ACCEPT ----
    def test_exact_match_still_accepted(self):
        anchor = "The category was something nobody had heard of."
        explanation = f'The source says "{anchor}" — which matters because it names the category directly.'
        self.assertTrue(_anchor_tied_to_explanation(anchor, explanation))

    def test_terminal_period_dropped_is_accepted(self):
        anchor = "The category was something nobody had heard of."
        stripped_quote = "The category was something nobody had heard of"
        explanation = f'The source says "{stripped_quote}" — which matters because it names the category directly.'
        self.assertTrue(_anchor_tied_to_explanation(anchor, explanation))

    def test_real_edinburgh_case_accepted(self):
        """The exact live case that motivated this fix (captured raw Fable
        response, Sofa Real Article Test 1)."""
        anchor = ("You can\u2019t walk into a gallery without learning about some "
                   "subcultural genius or longlost creative you\u2019ve never heard of.")
        explanation = (
            'The anchor — "You can\u2019t walk into a gallery without learning about some '
            'subcultural genius or longlost creative you\u2019ve never heard of" — reads as '
            "harmless idiom, but a cognitive-accessibility engine reads it as a load-bearing "
            "structural claim."
        )
        self.assertTrue(_anchor_tied_to_explanation(anchor, explanation))

    def test_terminal_question_mark_dropped_is_accepted(self):
        anchor = "Who gets to discover anything here?"
        explanation = 'The review asks "Who gets to discover anything here" without ever answering it.'
        self.assertTrue(_anchor_tied_to_explanation(anchor, explanation))

    def test_terminal_exclamation_dropped_is_accepted(self):
        anchor = "Follow your nose!"
        explanation = 'The instruction to "Follow your nose" treats wayfinding as a game, not a barrier.'
        self.assertTrue(_anchor_tied_to_explanation(anchor, explanation))

    # ---- Must still REJECT ----
    def test_changed_word_rejected(self):
        anchor = "The category was something nobody had heard of."
        explanation = 'The source says "the category was something nobody had ever heard of" — a small change.'
        self.assertFalse(_anchor_tied_to_explanation(anchor, explanation))

    def test_omitted_interior_phrase_rejected(self):
        anchor = "The category was something nobody had heard of."
        explanation = 'The source says "the category was something nobody heard of" — dropping "had".'
        self.assertFalse(_anchor_tied_to_explanation(anchor, explanation))

    def test_synonym_substitution_rejected(self):
        anchor = "The category was something nobody had heard of."
        explanation = 'The source says "the category was something nobody had encountered" — a synonym swap.'
        self.assertFalse(_anchor_tied_to_explanation(anchor, explanation))

    def test_materially_shorter_quote_rejected(self):
        anchor = "The category was something nobody had heard of."
        explanation = 'The source says "something nobody had heard of" — a much shorter fragment.'
        self.assertFalse(_anchor_tied_to_explanation(anchor, explanation))

    def test_matching_only_a_few_words_rejected(self):
        anchor = "The category was something nobody had heard of."
        explanation = 'The source mentions "nobody had heard" of the category, roughly.'
        self.assertFalse(_anchor_tied_to_explanation(anchor, explanation))

    def test_internal_punctuation_change_rejected(self):
        anchor = "The category was, in fact, something nobody had heard of."
        explanation = 'The source says "the category was something nobody had heard of" — commas removed.'
        self.assertFalse(_anchor_tied_to_explanation(anchor, explanation))

    def test_leading_punctuation_difference_not_tolerated(self):
        """The fix only strips TRAILING characters — a leading difference
        must still be rejected, proving this isn't accidentally permissive
        at the front of the string."""
        anchor = '"The category was something nobody had heard of."'
        explanation = "The source says the category was something nobody had heard of — no leading quote mark."
        self.assertFalse(_anchor_tied_to_explanation(anchor, explanation))

    def test_anchor_with_nothing_to_strip_gets_no_second_chance(self):
        """An anchor with no trailing punctuation at all must rely solely
        on exact matching — stripping a no-op should never manufacture a
        new, different match."""
        anchor = "the category was something nobody had heard of"  # no trailing punctuation
        explanation = 'The source discusses "the category was something nobody had heard about" loosely.'
        self.assertFalse(_anchor_tied_to_explanation(anchor, explanation))

    def test_stripped_anchor_identical_to_original_is_not_a_free_pass(self):
        stripped = _strip_trailing_sentence_punct("no punctuation here")
        self.assertEqual(stripped, "no punctuation here")


class ValidateSourceDecisionIntegrationTests(unittest.TestCase):
    """Exercises the full validate_source_decision -> _validate_commission_grounding
    path, not just the helper in isolation."""

    def _packet(self, source_text):
        return build_evidence_packet(source_text, source_origin="fixture")

    def test_full_commission_accepted_with_terminal_punct_dropped_in_explanation(self):
        source_text = "A long article. The category was something nobody had heard of. More text follows."
        anchor = "The category was something nobody had heard of."
        brief = {
            "source_decision": "commission",
            "source_anchor_examined": anchor,
            "hidden_mechanism": "A real mechanism claim.",
            "why_disability_knowledge_changes_subject": (
                'The source says "The category was something nobody had heard of" — which reframes the claim.'
            ),
            "eligible_execution_possible": True,
        }
        ok, code, reason, violations = validate_source_decision(brief, self._packet(source_text))
        self.assertTrue(ok, (code, reason, violations))
        self.assertEqual(code, "commission")

    def test_full_commission_still_rejected_on_synonym_substitution(self):
        source_text = "A long article. The category was something nobody had heard of. More text follows."
        anchor = "The category was something nobody had heard of."
        brief = {
            "source_decision": "commission",
            "source_anchor_examined": anchor,
            "hidden_mechanism": "A real mechanism claim.",
            "why_disability_knowledge_changes_subject": (
                'The source says "the category was something nobody had encountered" — a synonym swap.'
            ),
            "eligible_execution_possible": True,
        }
        ok, code, reason, violations = validate_source_decision(brief, self._packet(source_text))
        self.assertFalse(ok)
        self.assertEqual(code, "commission_mechanism_not_tied_to_anchor")

    def test_exact_match_case_unaffected_by_the_fix(self):
        """Positive control: a normal, already-working exact-match
        commission must still pass identically."""
        source_text = "A long article. The category was something nobody had heard of. More text follows."
        anchor = "The category was something nobody had heard of."
        brief = {
            "source_decision": "commission",
            "source_anchor_examined": anchor,
            "hidden_mechanism": "A real mechanism claim.",
            "why_disability_knowledge_changes_subject": (
                'The source explicitly states "The category was something nobody had heard of." verbatim.'
            ),
            "eligible_execution_possible": True,
        }
        ok, code, reason, violations = validate_source_decision(brief, self._packet(source_text))
        self.assertTrue(ok, (code, reason, violations))


if __name__ == "__main__":
    unittest.main()
