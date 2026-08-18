#!/usr/bin/env python3
"""
sofa_discovery_shadow_b4.py — Sofa Architecture B.4 ("perceptual
instrument + blind writer"). SHADOW ONLY. Real Article Test 1
continuation.

Identical interface shape to B.3 (build_b3_brief/build_b3_writer_prompt in
sofa_discovery_shadow_b3.py, untouched) except ATTENTION is replaced by a
PERCEPTUAL INSTRUMENT and OPEN QUESTION is replaced with the newly
selected, leak-tested question. Same ordered source material as B.3 (same
nine excerpts, same substring-verification discipline against the real
frozen source_text each run). Same grounding boundaries, same length
guidance. No hidden_mechanism, working_reading, or any interpretation
field is read from commission_brief anywhere in this module.
"""
from __future__ import annotations

from orchestrator.sofa_discovery_shadow import SofaShadowError, assert_no_persona_leakage
from orchestrator.sofa_discovery_shadow_b3 import _require_substring


PERCEPTUAL_INSTRUMENT = (
    "Notice what the described process requires someone to perceive, remember, sequence, "
    "coordinate, or decide for it to work as described. Treat these as operational "
    "conditions, not automatically difficulties or barriers. Test the first condition you "
    "notice against later material, and let later evidence make it smaller, larger, wrong, "
    "or irrelevant."
)

OPEN_QUESTION = (
    "What does the festival's own account of how to encounter it actually require of "
    "someone who takes that account at its word?"
)


def build_b4_brief(commission_brief: dict, evidence_packet: dict) -> dict:
    """Deterministic, no model call. Same nine ordered-material excerpts
    as B.3 (same grounding-verified list), with ATTENTION replaced by
    PERCEPTUAL_INSTRUMENT and OPEN_QUESTION replaced with the new,
    leak-tested question. Fails closed on the same conditions as B.3's
    build_b3_brief."""
    if commission_brief.get("source_decision") != "commission":
        raise SofaShadowError("B.4 brief can only be built from a commissioned brief")
    source_text = (evidence_packet or {}).get("source_text") or ""
    if not source_text:
        raise SofaShadowError("evidence_packet has no source_text")

    source_anchor = commission_brief.get("source_anchor_examined")
    if not source_anchor or source_anchor not in source_text:
        raise SofaShadowError("source_anchor_examined missing or not grounded in source_text")

    correction = commission_brief.get("correction_moment") or {}
    resisting = commission_brief.get("resisting_example") or {}
    correction_excerpt = (correction.get("evidence_candidate") or {}).get("source_excerpt", "")
    resisting_excerpt = (resisting.get("evidence_candidate") or {}).get("source_excerpt", "")

    ordered_material = [
        _require_substring(
            "You can’t walk into a gallery without learning about some subcultural genius or "
            "longlost creative you’ve never heard of.",
            source_text, "walking_1",
        ),
        _require_substring(
            "You’ve just got to follow your nose and hope you sniff out something you like.",
            source_text, "walking_2",
        ),
        _require_substring(
            "There are curated displays, satellite exhibitions, performances, off-site projects, "
            "and it’s impossible to figure out how any of it fits together.",
            source_text, "dispersed_festival",
        ),
    ]
    if correction_excerpt:
        ordered_material.append(_require_substring(correction_excerpt, source_text, "sandra_george"))
    ordered_material.append(
        _require_substring(
            "died having never shown any of the thousands of paintings and drawings he amassed "
            "over his lifetime",
            source_text, "frank_walter",
        )
    )
    ordered_material.append(
        _require_substring("stayed unpublished and unseen in his lifetime", source_text, "hasegawa")
    )
    if resisting_excerpt:
        ordered_material.append(_require_substring(resisting_excerpt, source_text, "clarity_quote"))
    ordered_material.append(
        _require_substring("It’s mind-meltingly indecipherable.", source_text, "indecipherable_1")
    )
    ordered_material.append(
        _require_substring(
            "I love it, but I’m not sure how the art downstairs fails to work so well.",
            source_text, "indecipherable_2",
        )
    )

    return {
        "perceptual_instrument": PERCEPTUAL_INSTRUMENT,
        "ordered_material": ordered_material,
        "open_question": OPEN_QUESTION,
        "grounding_boundaries": (
            "The source names no ticket prices, distances, opening hours, or physical access "
            "barriers (stairs, doors, ramps). It does not state who is excluded from visiting or "
            "why any artist's work went unseen during their lifetime — only that it did. No fact "
            "beyond the material below and the biographical dates it contains may be used."
        ),
        "length_guidance": "Roughly 700–850 words for this piece; stop when it has said what it has to say.",
    }


def build_b4_writer_prompt(brief: dict, source_text: str):
    """Returns (system, user). Same short, rule-light system prompt shape
    as B.3 — perceptual instrument replaces the attention line, everything
    else identical."""
    system = (
        "Write a narrative nonfiction article from the supplied source material.\n\n"
        "Follow what the material actually gives you. The question is genuinely open; do "
        "not decide its answer in advance.\n\n"
        "If a later fact changes the significance of an earlier one, let that change "
        "happen without announcing the editorial operation.\n\n"
        "Do not invent scenes, biography, motives, access barriers, distances, reporting "
        "actions, or lived experience. Do not introduce explicit disability examples "
        "merely because this is a disability-led publication.\n\n"
        "Stop when the strongest source-grounded understanding has arrived.\n\n"
        "You are not a character and have no biography. Write only the article, with a "
        "title on the first line."
    )
    user = (
        f"PERCEPTUAL INSTRUMENT: {brief['perceptual_instrument']}\n\n"
        "MATERIAL:\n" + "\n".join(f"- {m}" for m in brief["ordered_material"]) + "\n\n"
        f"OPEN QUESTION: {brief['open_question']}\n\n"
        f"GROUNDING BOUNDARIES: {brief['grounding_boundaries']}\n\n"
        f"LENGTH: {brief['length_guidance']}\n\n"
        f"FULL SOURCE TEXT (the only source of any named person, quote, date, or number "
        f"you may use):\n---\n{source_text}\n---\n"
    )
    assert_no_persona_leakage(system + user)
    return system, user


def run_b4_writer(brief: dict, source_text: str, writer_llm_call) -> str:
    system, user = build_b4_writer_prompt(brief, source_text)
    raw = writer_llm_call(system, user)
    if not raw or not isinstance(raw, str) or not raw.strip():
        raise SofaShadowError("B.4 writer model call returned no usable text")
    return raw.strip()
