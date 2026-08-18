#!/usr/bin/env python3
"""
sofa_discovery_shadow_form1.py — Sofa Architecture FORM-1 ("Article Form"
stage). SHADOW ONLY. Real Article Test 1 continuation.

Adds the missing stage the B.3/B.4 diagnosis identified: between Discovery
(owns hidden_mechanism/correction/resisting evidence) and Writer (owns
prose craft), ARTICLE FORM decides sequence/selection of already-validated
material and states a destination in plain language — never exposing
field names (working_reading/correction_material/etc.), never asking the
writer to discover a thesis from raw fragments, never announcing an
editorial operation ("this complicates the argument").

FORM-1 GROUNDING CORRECTIONS (this session's explicit instructions):
  1. No invented search/curation mechanism for how George/Walter/Hasegawa's
     work reached its current presentation (no "estate," "archive," "went
     looking on purpose," "curator found it"). The source supports a
     CONTRAST between two different moments the festival calls
     "discovery" -- (A) a visitor now encountering work while moving
     through the festival, (B) work that went unseen during an artist's
     lifetime now being available to encounter -- and nothing about HOW
     B came about.
  2. The writer is told to return to the meaning of "discovery" after the
     three facts, without being told to announce that operation.
  3. The destination is stated only as the A/B contrast above -- never
     extended into consent, agency, motive, search procedure, or
     disability/accessibility theory.

No new Fable call, no Discovery-model call. Every excerpt is checked as a
literal substring of the real source_text before being used (fail-closed,
same discipline as prior B.x modules).
"""
from __future__ import annotations

from orchestrator.sofa_discovery_shadow import SofaShadowError, assert_no_persona_leakage
from orchestrator.sofa_discovery_shadow_b3 import _require_substring


# Phrases this module must never emit into a writer-facing brief -- the
# specific unsupported attractor observed across B.3 (Opus), B.4 (Opus),
# and cross-model replays (Grok, Qwen). Checked by a hard assertion below,
# not just by care in authoring the text.
_FORBIDDEN_ATTRACTOR_PHRASES = [
    "no choice", "could not advocate", "cannot advocate", "never meant to be found",
    "pleasure was possible because", "house style", "went looking on purpose",
    "an estate", "archive found", "curator found", "curator went looking",
    "consent", "agency", "advocate for themselves",
]


def _assert_no_attractor_language(text):
    lowered = text.lower()
    hits = [p for p in _FORBIDDEN_ATTRACTOR_PHRASES if p in lowered]
    if hits:
        raise SofaShadowError(
            f"FORM-1 brief contains forbidden attractor language: {hits} — "
            "refusing to hand this to the writer"
        )


def build_form1_packet(commission_brief: dict, evidence_packet: dict) -> dict:
    """Deterministic, no model call. Fails closed on the same grounding
    invariants as prior B.x modules, plus the attractor-language guard
    above applied to every text field this function constructs."""
    if commission_brief.get("source_decision") != "commission":
        raise SofaShadowError("FORM-1 packet can only be built from a commissioned brief")
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

    opening_material = [
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

    correction_material = []
    if correction_excerpt:
        correction_material.append(_require_substring(correction_excerpt, source_text, "sandra_george"))
    correction_material.append(
        _require_substring(
            "died having never shown any of the thousands of paintings and drawings he amassed "
            "over his lifetime",
            source_text, "frank_walter",
        )
    )
    correction_material.append(
        _require_substring("stayed unpublished and unseen in his lifetime", source_text, "hasegawa")
    )

    resisting_material = []
    if resisting_excerpt:
        resisting_material.append(_require_substring(resisting_excerpt, source_text, "clarity_quote"))

    # INTERNAL-ONLY: what the correction does, stated ONLY as a contrast
    # between two meanings of "discovery" -- never a causal/search-
    # mechanism claim, never agency/consent language. This is Form's own
    # editorial note, never shown to the writer verbatim as a labeled
    # field; only its DESTINATION (below) reaches the writer, restated in
    # plain instruction form.
    correction_function = (
        "The festival calls two different things 'discovery': a visitor now encountering work "
        "while moving through the festival, and work that went unseen during an artist's "
        "lifetime now being available to encounter. These are different moments, described with "
        "the same word. The source supports this contrast; it does not establish how the second "
        "kind of availability came about."
    )

    destination = (
        "discovery as the visitor encounters it now, versus work becoming visible only after "
        "having gone unseen during the artist's lifetime"
    )

    for text in [correction_function, destination] + opening_material + correction_material + resisting_material:
        _assert_no_attractor_language(text)

    return {
        "opening_material": opening_material,
        "correction_material": correction_material,
        "resisting_material": resisting_material,
        "correction_function": correction_function,  # internal-only
        "destination": destination,
        "grounding_boundaries": (
            "The source does not say why George, Walter, or Hasegawa went unseen during their "
            "lifetimes, does not describe how their work came to be shown now, and does not "
            "describe their wishes, intentions, or capacity regarding exhibition. It names no "
            "access barriers, distances, or excluded audiences."
        ),
        "length_guidance": "Roughly 650–800 words for this piece; do not pad — stop when it has said what it has to say.",
    }


def build_form1_writer_prompt(packet: dict, source_text: str):
    """Returns (system, user). Writer receives opening/correction/
    resisting material as plain ordered facts (no CORRECTION/RESISTANCE
    labels), the destination in plain language (not as a named field),
    and an instruction to return to the meaning of 'discovery' without
    announcing that it is doing so."""
    _assert_no_attractor_language(packet["destination"])

    system = (
        "Write a narrative nonfiction article from the material below, in the order given. "
        "You are not filling in labeled sections — write it as one continuous piece of "
        "thinking.\n\n"
        "Begin with how the festival describes its own way of being encountered. Then bring "
        "in the facts about the three artists, together. After those facts, return to the "
        "meaning of 'discovery' — let the facts narrow what that word means without "
        "announcing that you are doing so (do not write sentences like 'this complicates the "
        "argument' or 'here is where the reading collides with itself'; let the facts do the "
        "work).\n\n"
        f"The piece should land on this distinction: {packet['destination']}. Do not extend "
        "this into any claim about why these artists went unseen, how their work came to be "
        "shown now, what they wanted, or whether they had a choice — the source does not say, "
        "and neither should the article. Do not introduce access barriers, consent, agency, or "
        "a disability example; stay with the plain distinction and stop once it has landed.\n\n"
        "Do not invent scenes, biography, motives, search procedures, or lived experience. "
        "Write in third person; do not adopt a first-person narrator unless quoting the "
        "source.\n\n"
        f"{packet['length_guidance']}\n\n"
        "You are not a character and have no biography. Write only the article, with a title "
        "on the first line."
    )

    material_lines = (
        [f"- {m}" for m in packet["opening_material"]]
        + [f"- {m}" for m in packet["correction_material"]]
        + [f"- {m}" for m in packet["resisting_material"]]
    )
    user = (
        "MATERIAL (in order):\n" + "\n".join(material_lines) + "\n\n"
        f"GROUNDING BOUNDARIES: {packet['grounding_boundaries']}\n\n"
        f"FULL SOURCE TEXT (the only source of any named person, quote, date, or number you "
        f"may use):\n---\n{source_text}\n---\n"
    )
    assert_no_persona_leakage(system + user)
    # The attractor-language guard is applied to the CONTENT fields only
    # (material + destination, already checked in build_form1_packet) --
    # not to this function's own system-prompt PROHIBITION text, which
    # must legitimately name "consent"/"agency" to instruct the writer
    # against introducing them. Re-checking the assembled material lines
    # here (not the full prompt) confirms nothing slipped past that
    # per-field check when building the ordered list above.
    for line in material_lines:
        _assert_no_attractor_language(line)
    return system, user


def run_form1_writer(packet: dict, source_text: str, writer_llm_call) -> str:
    system, user = build_form1_writer_prompt(packet, source_text)
    raw = writer_llm_call(system, user)
    if not raw or not isinstance(raw, str) or not raw.strip():
        raise SofaShadowError("FORM-1 writer model call returned no usable text")
    return raw.strip()
