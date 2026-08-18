#!/usr/bin/env python3
"""
fable_editorial_brief_schema.py — TEMP-WORKTREE-ONLY strict JSON Schema
representing the EXISTING Fable editorial-brief contract (Sofa Real Article
Test 1, strict json_schema capability experiment).

This is NOT a redesign of the editorial contract. Every field here comes
directly from the literal "Reply with JSON only" instruction block in
_fable_editorial_brief's user prompt (llm.py) -- nothing added, nothing
required that the prompt itself treats as optional.

Field provenance (verbatim from the prompt):
  Always filled, both branches: source_decision, source_anchor_examined.
  Commission-only (Layer 2): hidden_mechanism,
    why_disability_knowledge_changes_subject, eligible_execution_possible,
    blocked_carry_persona (only when eligible_execution_possible=false),
    persona, angle, register, seed_sentence, opening_scene, opening_shape,
    correction_moment, resisting_example, cross_cite (explicitly optional
    even within commission -- "Leave empty unless...").
  Decline-only: dominant_framing, why_disability_knowledge_does_not_change_subject,
    reason. Prompt: "leave the Layer 2 fields empty" on decline -- modeled
    here as nullable, not omitted (strict mode requires every property to
    appear in `required`; nullable is the honest way to express "optional
    per the existing contract" without a schema-level branch that would be
    a bigger structural change than this experiment calls for).

correction_moment / resisting_example are each an object with exactly the
THREE PARTS the prompt itself names ("Each of these two fields is now an
OBJECT with THREE SEPARATE PARTS"): editorial_need, evidence_candidate,
interpretation. NOTE: one of the two real captured responses (fixed2)
spontaneously added a fourth key, "interpretation_note", never asked for by
the prompt. This schema deliberately does NOT include it -- strict mode's
additionalProperties:false will reject that drift if it recurs, which is
the correct behavior for a schema representing the INTENDED contract, not
incidental model additions.

evidence_candidate's four fields (status/source_excerpt/named_person/
direct_quote) plus dates_numbers are exactly the prompt's "THREE SEPARATE
PARTS" breakdown of evidence_candidate itself. Per the prompt: "otherwise
empty" for source_excerpt/named_person/direct_quote when not applicable --
modeled as required (present) but empty-string-or-populated, since the
prompt never treats "" as absent, only as one valid value; same is true for
dates_numbers as an empty list.
"""

_EVIDENCE_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["found", "not_found"]},
        "source_excerpt": {"type": "string"},
        "named_person": {"type": "string"},
        "direct_quote": {"type": "string"},
        "dates_numbers": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "source_excerpt", "named_person", "direct_quote", "dates_numbers"],
    "additionalProperties": False,
}

_GROUNDED_MOMENT_SCHEMA = {
    "type": ["object", "null"],
    "properties": {
        "editorial_need": {"type": "string"},
        "evidence_candidate": _EVIDENCE_CANDIDATE_SCHEMA,
        "interpretation": {"type": "string"},
    },
    "required": ["editorial_need", "evidence_candidate", "interpretation"],
    "additionalProperties": False,
}

FABLE_EDITORIAL_BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "source_decision": {"type": "string", "enum": ["commission", "decline"]},
        "source_anchor_examined": {"type": "string"},
        "hidden_mechanism": {"type": ["string", "null"]},
        "why_disability_knowledge_changes_subject": {"type": ["string", "null"]},
        "eligible_execution_possible": {"type": ["boolean", "null"]},
        "blocked_carry_persona": {"type": ["string", "null"]},
        "persona": {"type": ["string", "null"]},
        "angle": {"type": ["string", "null"]},
        "register": {"type": ["string", "null"]},
        "seed_sentence": {"type": ["string", "null"]},
        "opening_scene": {"type": ["string", "null"]},
        "opening_shape": {
            "type": ["string", "null"],
            "enum": ["plain_claim", "cold_scene", "question", "fact", "declaration_of_hunt", None],
        },
        "correction_moment": _GROUNDED_MOMENT_SCHEMA,
        "resisting_example": _GROUNDED_MOMENT_SCHEMA,
        "cross_cite": {"type": ["string", "null"]},
        "dominant_framing": {"type": ["string", "null"]},
        "why_disability_knowledge_does_not_change_subject": {"type": ["string", "null"]},
        "reason": {"type": ["string", "null"]},
    },
    "required": [
        "source_decision", "source_anchor_examined", "hidden_mechanism",
        "why_disability_knowledge_changes_subject", "eligible_execution_possible",
        "blocked_carry_persona", "persona", "angle", "register", "seed_sentence",
        "opening_scene", "opening_shape", "correction_moment", "resisting_example",
        "cross_cite", "dominant_framing", "why_disability_knowledge_does_not_change_subject",
        "reason",
    ],
    "additionalProperties": False,
}

FABLE_EDITORIAL_BRIEF_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "fable_editorial_brief",
        "strict": True,
        "schema": FABLE_EDITORIAL_BRIEF_SCHEMA,
    },
}

# Sofa Real Article Test 1, step 3: force OpenRouter to refuse routing this
# request to a backend that would silently ignore structured_outputs rather
# than honor or reject it. TEMP experiment only -- not a deliberate
# provider/model change (see llm.py's provider passthrough docstring).
FABLE_REQUIRE_STRUCTURED_OUTPUT_PROVIDER = {"require_parameters": True}
