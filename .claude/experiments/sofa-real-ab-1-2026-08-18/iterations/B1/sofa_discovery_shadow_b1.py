#!/usr/bin/env python3
"""
sofa_discovery_shadow_b1.py — Sofa Architecture B.1 (Real Article Test 1
continuation, "SOFA B.1"). SHADOW ONLY. Not called by production_orchestrator.py,
not on any cron path, not wired to publish/social/gate.

Minimum correction over Slice 1/1.1's sofa_discovery_shadow.py (left
completely untouched — this is a new, separate module reusing its
primitives, not a replacement). The diagnosis this responds to: Slice
1/1.1's build_discovery_packet reads only source_anchor_examined and
hidden_mechanism off an already-commissioned Fable brief, silently
dropping correction_moment/resisting_example/cross_cite/angle — the four
fields whose explicit job in the LEGACY writer prompt is to put the
mechanism at risk on the page. That drop is why the Sofa writer received
"a mechanism to demonstrate" instead of "a working reading capable of
being changed."

NO NEW MODEL CALL. Every B.1 field is a DETERMINISTIC repackaging of
fields the commission brief already contains (hidden_mechanism, angle,
correction_moment, resisting_example, cross_cite) — never regenerated,
never re-decided. The only transformation applied is persona-
neutralization of specific known persona-named phrasings (see
_neutralize below) plus a hard post-check that no fragment of the
byline persona's own name survives in any editorial text handed to the
writer.

SIX POSSIBLE FIELDS (not all required — a field is omitted, never
invented, when the commission doesn't supply the underlying material):
  working_reading      <- hidden_mechanism (verbatim; reframed as
                           provisional at the WRITER-PROMPT level, not by
                           altering its stored content)
  live_question         <- angle (verbatim; already persona-neutral in
                           this case)
  correction_material   <- correction_moment, only if evidence_candidate.
                           status == "found"; split into SOURCE_EVIDENCE
                           (source_excerpt) and EDITORIAL_INTERPRETATION
                           (interpretation, persona-neutralized)
  resisting_material     <- resisting_example, same split/condition
  rival_reading          <- cross_cite, only if non-empty
  unresolved_tension     <- derived from resisting_material's OWN stated
                           tension (never a fresh synthesis) — only
                           present when resisting_material is present
"""
from __future__ import annotations

from datetime import datetime as _dt

from orchestrator.sofa_discovery_shadow import (  # noqa: E402 -- reused, not duplicated
    SofaShadowError,
    _field,
    EVIDENCE,
    EDITORIAL_INTERPRETATION,
    EDITORIAL_GUIDANCE,
    EDITORIAL_METADATA,
    assert_no_persona_leakage,
)

SCHEMA_VERSION = "sofa-b1-1.0"

# The ONLY text transformation this module ever applies: a small, explicit,
# disclosed substitution table for the specific persona-named phrasings
# found in THIS commission's correction_moment/resisting_example
# interpretations. Never a generic rewrite. Followed by a hard per-token
# guard (see _neutralize) that raises if any fragment of the persona's own
# name survives regardless of whether it matched one of these phrases.
_PERSONA_NEUTRALIZATION = [
    ("Zen's access argument", "this working reading"),
    ("it resists Zen too", "it resists this reading too"),
    ("the pattern-analyst's clean-interface instinct", "this reading's own instinct for a clean interface"),
    ("The pattern-analyst's clean-interface instinct", "This reading's own instinct for a clean interface"),
]


def _neutralize(text, persona_name=None):
    """Applies the explicit substitution table above, then hard-fails if
    any single token of `persona_name` (e.g. "Zen", "Circuit") still
    appears anywhere in the result -- never silently ships a persona
    reference that the fixed table didn't happen to anticipate."""
    if not text:
        return text
    out = text
    for old, new in _PERSONA_NEUTRALIZATION:
        out = out.replace(old, new)
    if persona_name:
        for token in persona_name.split():
            if token and token in out:
                raise SofaShadowError(
                    f"persona-neutralization left a literal fragment of persona name "
                    f"{persona_name!r} ({token!r}) in editorial text -- refusing to "
                    f"hand this to the writer: {out!r}"
                )
    return out


def build_b1_packet(commission_brief: dict, evidence_packet: dict) -> dict:
    """Deterministic repackaging -- no model call. Fails closed (raises
    SofaShadowError) on the same grounding invariants Slice 1.1 enforces:
    commission must be source_decision=="commission"; source_anchor must
    be a literal substring of source_text; any correction/resisting
    source_excerpt must be a literal substring of source_text; an
    editorial interpretation is never typed EVIDENCE."""
    if not isinstance(commission_brief, dict):
        raise SofaShadowError("commission_brief must be a dict")
    if commission_brief.get("source_decision") != "commission":
        raise SofaShadowError(
            "B.1 packet can only be built from a commissioned brief "
            f"(source_decision={commission_brief.get('source_decision')!r})"
        )

    source_anchor = commission_brief.get("source_anchor_examined")
    hidden_mechanism = commission_brief.get("hidden_mechanism")
    if not source_anchor or not isinstance(source_anchor, str):
        raise SofaShadowError("commission_brief.source_anchor_examined missing or not a string")
    if not hidden_mechanism or not isinstance(hidden_mechanism, str):
        raise SofaShadowError("commission_brief.hidden_mechanism missing or not a string")

    source_text = (evidence_packet or {}).get("source_text") or ""
    if not source_text:
        raise SofaShadowError("evidence_packet has no source_text — cannot ground a B.1 packet")
    if source_anchor not in source_text:
        raise SofaShadowError(
            "source_anchor_examined is not a literal substring of evidence_packet.source_text"
        )

    persona_name = commission_brief.get("persona") or ""

    packet = {
        "schema_version": SCHEMA_VERSION,
        "built_at": _dt.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "evidence_packet_hash": (evidence_packet or {}).get("evidence_packet_hash"),
        "byline_persona": _field(
            persona_name, EDITORIAL_METADATA,
            note="the execution persona selected by Fable Layer 2 — byline/attribution "
                 "metadata only, never fed to the writer as voice/roleplay material",
        ),
        "source_anchor": _field(source_anchor, EVIDENCE, note="verbatim, from commission_brief"),
        "working_reading": _field(
            hidden_mechanism, EDITORIAL_INTERPRETATION,
            note="the strongest current editorial interpretation — provisional, not a "
                 "verdict the article must prove; inherited verbatim from Fable Layer 1, "
                 "never regenerated",
        ),
    }

    angle = commission_brief.get("angle")
    if angle and isinstance(angle, str):
        packet["live_question"] = _field(
            angle, EDITORIAL_GUIDANCE,
            note="the real unresolved question inherited from the commission's angle — "
                 "guidance for stance, not a sentence to quote",
        )

    def _material_from(field_name):
        item = commission_brief.get(field_name)
        if not isinstance(item, dict):
            return None
        candidate = item.get("evidence_candidate") or {}
        if candidate.get("status") != "found":
            return None
        excerpt = candidate.get("source_excerpt")
        interpretation = item.get("interpretation")
        if not excerpt or not isinstance(excerpt, str):
            return None
        if excerpt not in source_text:
            raise SofaShadowError(
                f"{field_name}.evidence_candidate.source_excerpt is not a literal "
                "substring of source_text — refusing to carry an ungrounded excerpt"
            )
        return {
            "source_evidence": _field(excerpt, EVIDENCE, note=f"verbatim, from commission_brief.{field_name}"),
            "editorial_interpretation": _field(
                _neutralize(interpretation, persona_name), EDITORIAL_INTERPRETATION,
                note=f"editor's reasoning about what this material may do to the working "
                     f"reading — never itself a source fact; persona-neutralized from "
                     f"commission_brief.{field_name}.interpretation",
            ),
        }

    correction_material = _material_from("correction_moment")
    if correction_material:
        packet["correction_material"] = correction_material

    resisting_material = _material_from("resisting_example")
    if resisting_material:
        packet["resisting_material"] = resisting_material

    cross_cite = commission_brief.get("cross_cite")
    if cross_cite and isinstance(cross_cite, str) and cross_cite.strip():
        packet["rival_reading"] = _field(
            _neutralize(cross_cite, persona_name), EDITORIAL_INTERPRETATION,
            note="a competing interpretation genuinely present in the commission — "
                 "persona-neutralized from commission_brief.cross_cite",
        )

    # unresolved_tension is NEVER a fresh synthesis -- for this case it is
    # the resisting_material's own already-written closing tension
    # statement (the commission's interpretation text already names what
    # it declines to resolve). Only present when resisting_material is.
    # A future case with no such closing statement in its resisting_example
    # simply omits this field rather than inventing one.
    if resisting_material and interpretation_ends_in_a_named_tension(commission_brief):
        packet["unresolved_tension"] = _field(
            _neutralize(commission_brief["resisting_example"]["interpretation"], persona_name),
            EDITORIAL_INTERPRETATION,
            note="derived verbatim from resisting_example's own stated tension — not a "
                 "new synthesis; present only because that field already names what it "
                 "declines to resolve",
        )

    return packet


def interpretation_ends_in_a_named_tension(commission_brief):
    """Narrow, disclosed heuristic: true only if resisting_example's
    interpretation text contains an explicit not-to-be-resolved marker
    ("sit inside", "not resolve", "does not resolve", "tension"). Exists
    so unresolved_tension is never fabricated for a case whose
    resisting_example doesn't actually name one — checked against THIS
    case's real text, not assumed true in general."""
    text = ((commission_brief.get("resisting_example") or {}).get("interpretation") or "").lower()
    return any(marker in text for marker in ("sit inside", "not resolve", "does not resolve", "tension"))


def to_b1_writer_context(packet: dict, source_text: str) -> dict:
    """Projects a B.1 packet to exactly what the writer receives. Same
    discipline as Slice 1.1's to_writer_context: unwraps epistemic
    envelopes to plain values, requires the real source_text as
    reference_source, and hard-checks for persona-roleplay leakage before
    returning."""
    if not source_text or not isinstance(source_text, str):
        raise SofaShadowError("to_b1_writer_context requires the real source_text")

    context = {
        "byline_persona": packet["byline_persona"]["value"],
        "source_anchor": packet["source_anchor"]["value"],
        "working_reading": packet["working_reading"]["value"],
        "reference_source": source_text,
    }
    if "live_question" in packet:
        context["live_question"] = packet["live_question"]["value"]
    if "correction_material" in packet:
        context["correction_material"] = {
            "source_evidence": packet["correction_material"]["source_evidence"]["value"],
            "editorial_interpretation": packet["correction_material"]["editorial_interpretation"]["value"],
        }
    if "resisting_material" in packet:
        context["resisting_material"] = {
            "source_evidence": packet["resisting_material"]["source_evidence"]["value"],
            "editorial_interpretation": packet["resisting_material"]["editorial_interpretation"]["value"],
        }
    if "rival_reading" in packet:
        context["rival_reading"] = packet["rival_reading"]["value"]
    if "unresolved_tension" in packet:
        context["unresolved_tension"] = packet["unresolved_tension"]["value"]

    assert_no_persona_leakage(__import__("json").dumps(context))
    return context


def build_b1_writer_prompt(writer_context: dict):
    """Returns (system, user) for the B.1 generic writer. Built directly
    from the task's CRITICAL WRITER INSTRUCTION / NO FORMULA / PERSPECTIVE
    DISCIPLINE / ARRIVAL-STOP DISCIPLINE / grounding-lessons sections --
    not from generate.py's persona-voice prompt, which this function does
    not read, import, or reference."""
    system = (
        "You are a prose writer for a disability-led publication. You are not a character "
        "and you have no biography — you are a writing function.\n\n"
        "You are given a WORKING READING below — the strongest current editorial "
        "interpretation of the source material. It is provisional, not a verdict. Your job "
        "is not to prove it or make it intelligible through decoration. Follow the supplied "
        "material — especially any CORRECTION MATERIAL or RESISTING MATERIAL below — and "
        "let it make the working reading narrower, larger, different, or wrong, if it "
        "genuinely does that. Do not manufacture a reversal that isn't there. If the "
        "correction material changes the reading, let it change it. If it doesn't, don't "
        "fake a turn.\n\n"
        "NO FORMULA: there is no required shape (no mandatory opening-thesis-then-"
        "correction-then-larger-thesis template). Some material suggests a real turn; "
        "other material doesn't. Let the material decide the movement, not a habit.\n\n"
        "ARRIVAL: once the strongest available correction has produced a more precise "
        "understanding, you may stop. Do not automatically search for another disability "
        "example, another world, another analogy, another conceptual escalation, or a "
        "larger universal thesis just to extend the piece. A correction does not have to "
        "make the argument bigger — it may simply make it more precise. Do not force the "
        "piece to include more explicit disability content than the material itself earns; "
        "the disability lens can be causally necessary to how this piece sees without being "
        "narratively mandatory to state.\n\n"
        "PERSPECTIVE: default to third-person / impersonal narrative nonfiction. First "
        "person is allowed ONLY to name a real editorial/reporting action actually "
        "supported by the material below (e.g. 'I read...', 'the source shows...') — never "
        "a fabricated lived-experience episode, a biography, a wound, or a claim to have "
        "personally witnessed or experienced anything. If nothing in the material below "
        "supports a real first-person reporting action, write in third person throughout. "
        "No persona voice, no roleplay, no disclosed or undisclosed character.\n\n"
        "GROUNDING (do not violate these, no exceptions): never state an editorial "
        "interpretation as if it were a measured, settled fact. Never invent a concrete "
        "detail (a barrier, a distance, a name, a date, a cause) beyond what SOURCE "
        "EVIDENCE / REFERENCE SOURCE below actually contains. Never invent a source for a "
        "detail (e.g. attributing a real fact to 'the wall text' or any object/document not "
        "actually named as its source). An editorial interpretation or note is never itself "
        "a fact — only a quoted excerpt is. Write the article now. Do not explain your "
        "reasoning. Output only the article, with a title on the first line."
    )

    parts = [
        f"WORKING READING (provisional editorial interpretation — not a verdict to prove):\n"
        f"{writer_context['working_reading']}\n",
        f"SOURCE ANCHOR (verbatim evidence the reading rests on): {writer_context['source_anchor']}\n",
    ]
    if "live_question" in writer_context:
        parts.append(
            "LIVE QUESTION (the real unresolved question — write as if finding the answer "
            f"on the page, not stating a thesis you already hold):\n{writer_context['live_question']}\n"
        )
    if "correction_material" in writer_context:
        cm = writer_context["correction_material"]
        parts.append(
            "CORRECTION MATERIAL (source-grounded — capable of making the working reading "
            "too small, wrong, or incomplete; the [editorial note] is the editor's own "
            "reasoning, never itself a source fact):\n"
            f"- source evidence: {cm['source_evidence']}\n"
            f"- (editorial note) {cm['editorial_interpretation']}\n"
        )
    if "resisting_material" in writer_context:
        rm = writer_context["resisting_material"]
        parts.append(
            "RESISTING MATERIAL (source-grounded — does not fit the working reading "
            "cleanly; do not automatically neutralize it; the [editorial note] is the "
            "editor's own reasoning, never itself a source fact):\n"
            f"- source evidence: {rm['source_evidence']}\n"
            f"- (editorial note) {rm['editorial_interpretation']}\n"
        )
    if "rival_reading" in writer_context:
        parts.append(
            f"RIVAL READING (a genuinely competing interpretation — argue with its "
            f"substance if it bears on this piece, not a name to check):\n{writer_context['rival_reading']}\n"
        )
    if "unresolved_tension" in writer_context:
        parts.append(
            f"UNRESOLVED TENSION (what the available material cannot honestly settle — "
            f"you are not required to resolve this):\n{writer_context['unresolved_tension']}\n"
        )
    parts.append(
        f"REFERENCE SOURCE (the complete original source text — the only source of any "
        f"named person, quote, date, or number you may use):\n---\n{writer_context['reference_source']}\n---\n"
    )
    user = "\n".join(parts)
    assert_no_persona_leakage(system + user)
    return system, user


def run_b1_writer(writer_context: dict, writer_llm_call) -> str:
    system, user = build_b1_writer_prompt(writer_context)
    raw = writer_llm_call(system, user)
    if not raw or not isinstance(raw, str) or not raw.strip():
        raise SofaShadowError("B.1 writer model call returned no usable text")
    return raw.strip()
