#!/usr/bin/env python3
"""
sofa_discovery_shadow_b3.py — Sofa Architecture B.3 ("blind writer").
SHADOW ONLY. Real Article Test 1 continuation.

Principle: Discovery may know hidden_mechanism. The WRITER must not.
The writer receives ATTENTION / ORDERED SOURCE MATERIAL / OPEN QUESTION /
GROUNDING BOUNDARIES / optional length guidance -- never hidden_mechanism,
working_reading, correction/resisting/rival INTERPRETATION, unresolved
tension, or any persona material. Source excerpts previously used for
correction/resistance may appear as ordinary ordered material, unlabeled.

No new Discovery-model call. Every excerpt below is checked as a literal
substring of the real source_text before being handed to the writer
(fail-closed, same discipline as build_b1_packet) -- this module does not
trust its own hardcoded quotes without verifying them against the actual
frozen source each time it runs.

Also implements the internal, post-writer DISCOVERY EVALUATION (A/B/C/D)
-- a distinct check from grounding, comparing the finished article against
the INTERNAL-ONLY hidden_mechanism. This is not a repair mechanism and
never rewrites the article.
"""
from __future__ import annotations

from orchestrator.sofa_discovery_shadow import SofaShadowError, assert_no_persona_leakage


def _require_substring(excerpt, source_text, label):
    if excerpt not in source_text:
        raise SofaShadowError(f"B.3 ordered-material excerpt ({label}) is not a literal "
                               f"substring of source_text — refusing to use it: {excerpt!r}")
    return excerpt


def build_b3_brief(commission_brief: dict, evidence_packet: dict) -> dict:
    """Deterministic, no model call. Fails closed if the commission isn't
    a real commission, if source_anchor isn't grounded, or if any of the
    six hardcoded ordered-material excerpts below isn't a literal
    substring of THIS run's actual source_text."""
    if commission_brief.get("source_decision") != "commission":
        raise SofaShadowError("B.3 brief can only be built from a commissioned brief")
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
        _require_substring(
            "stayed unpublished and unseen in his lifetime",
            source_text, "hasegawa",
        )
    )
    if resisting_excerpt:
        ordered_material.append(_require_substring(resisting_excerpt, source_text, "clarity_quote"))
    ordered_material.append(
        _require_substring(
            "It’s mind-meltingly indecipherable.",
            source_text, "indecipherable_1",
        )
    )
    ordered_material.append(
        _require_substring(
            "I love it, but I’m not sure how the art downstairs fails to work so well.",
            source_text, "indecipherable_2",
        )
    )

    brief = {
        "attention": (
            "The review repeatedly describes discovering the festival through verbs such as "
            "walk, follow your nose, sniff out, uncover and figure out."
        ),
        "ordered_material": ordered_material,
        "open_question": (
            "What happens to the festival's language of wandering and stumbling when it is "
            "placed beside artists whose work went unseen until after their deaths?"
        ),
        "grounding_boundaries": (
            "The source names no ticket prices, distances, opening hours, or physical access "
            "barriers (stairs, doors, ramps). It does not state who is excluded from visiting or "
            "why any artist's work went unseen during their lifetime — only that it did. No fact "
            "beyond the material below and the biographical dates it contains may be used."
        ),
        "length_guidance": "Roughly 700–850 words for this piece; stop when it has said what it has to say.",
    }
    return brief


def build_b3_writer_prompt(brief: dict, source_text: str):
    """Returns (system, user). Deliberately short -- no rule-heavy Sofa
    system prompt, per the task's explicit instruction not to add one
    back."""
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
        f"ATTENTION: {brief['attention']}\n\n"
        "MATERIAL:\n" + "\n".join(f"- {m}" for m in brief["ordered_material"]) + "\n\n"
        f"OPEN QUESTION: {brief['open_question']}\n\n"
        f"GROUNDING BOUNDARIES: {brief['grounding_boundaries']}\n\n"
        f"LENGTH: {brief['length_guidance']}\n\n"
        f"FULL SOURCE TEXT (the only source of any named person, quote, date, or number "
        f"you may use):\n---\n{source_text}\n---\n"
    )
    assert_no_persona_leakage(system + user)
    return system, user


def run_b3_writer(brief: dict, source_text: str, writer_llm_call) -> str:
    system, user = build_b3_writer_prompt(brief, source_text)
    raw = writer_llm_call(system, user)
    if not raw or not isinstance(raw, str) or not raw.strip():
        raise SofaShadowError("B.3 writer model call returned no usable text")
    return raw.strip()


_DISCOVERY_EVAL_VALID = {"A", "B", "C", "D"}


def build_discovery_eval_prompt(hidden_mechanism: str, source_text: str, article_text: str):
    """Returns (system, user) for the INTERNAL-ONLY post-writer discovery
    evaluation. Distinct from grounding: this asks whether a meaningful
    discovery happened relative to hidden_mechanism, not whether claims
    are supported. Must NOT reject/downgrade an article merely for
    differing from hidden_mechanism -- C is an accepted, welcome outcome
    when earned by real evidence."""
    system = (
        "You are evaluating whether a finished article represents a meaningful editorial "
        "discovery, relative to the internal working hypothesis that commissioned it. You "
        "do not evaluate prose quality or factual support (a separate grounding process "
        "does that). You classify the RELATIONSHIP between the article's own arrived-at "
        "understanding and the original hidden mechanism.\n\n"
        "Classify into exactly one:\n"
        "A. REACHES ORIGINAL MECHANISM — the article arrives, through its own evidence, at "
        "substantially the same understanding as the original mechanism.\n"
        "B. MAKES IT MORE PRECISE — same territory, sharper or narrower than the original.\n"
        "C. PRODUCTIVELY CONTRADICTS OR REPLACES IT — the article's evidence leads somewhere "
        "genuinely different from, or opposed to, the original mechanism, and that departure "
        "is earned by real material in the article, not merely asserted.\n"
        "D. NO MEANINGFUL DISCOVERY — the article tours the source without arriving anywhere, "
        "or manufactures an arrival using claims the source doesn't support.\n\n"
        "A, B, and C are all ACCEPTABLE outcomes. Do not penalize an article for reaching C "
        "instead of A — a conceptual leap beyond the original mechanism is welcome as long as "
        "it is grounded in the article's own evidence, not fabricated. Only D is a failure, "
        "and only because nothing was actually discovered or the discovery was faked — not "
        "because the article disagrees with the original mechanism.\n\n"
        "Reply with JSON only: {\"verdict\": \"A\"|\"B\"|\"C\"|\"D\", \"reason\": \"...\"} — "
        "reason under 100 words."
    )
    user = (
        f"ORIGINAL HIDDEN MECHANISM (internal, never shown to the writer):\n{hidden_mechanism}\n\n"
        f"SOURCE TEXT:\n---\n{source_text}\n---\n\n"
        f"FINISHED ARTICLE:\n---\n{article_text}\n---\n"
    )
    return system, user


def run_discovery_eval(hidden_mechanism: str, source_text: str, article_text: str, eval_llm_call) -> dict:
    import json as _json
    import re as _re
    system, user = build_discovery_eval_prompt(hidden_mechanism, source_text, article_text)
    raw = eval_llm_call(system, user)
    if not raw or not isinstance(raw, str):
        raise SofaShadowError("discovery-evaluation model call returned no usable text")
    cleaned = _re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=_re.MULTILINE)
    parsed = _json.loads(cleaned)
    verdict = parsed.get("verdict")
    if verdict not in _DISCOVERY_EVAL_VALID:
        raise SofaShadowError(f"discovery-evaluation returned invalid verdict: {verdict!r}")
    return {"verdict": verdict, "reason": parsed.get("reason", "")}
