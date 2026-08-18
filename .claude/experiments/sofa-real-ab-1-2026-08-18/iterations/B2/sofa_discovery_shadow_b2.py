#!/usr/bin/env python3
"""
sofa_discovery_shadow_b2.py — Sofa Architecture B.2 (Real Article Test 1
continuation, "SOFA B.2"). SHADOW ONLY. Reuses B.1's internal packet
construction UNCHANGED (build_b1_packet, sofa_discovery_shadow_b1.py —
not modified) — the diagnosis this responds to is not that B.1's internal
reasoning was wrong, it's that exposing six labeled fields
(WORKING READING / LIVE QUESTION / CORRECTION MATERIAL / RESISTING
MATERIAL / RIVAL READING / UNRESOLVED TENSION) directly in the writer
prompt taught the model to narrate the packet's own schema ("So the
working suspicion is easy to state...", "This is the working reading
arriving from the aesthetic direction...").

B.2 keeps the SAME internal packet (same fields, same grounding, same
persona-neutralization) but never shows the writer those field names.
Instead it compiles a compact, natural-language STORY BRIEF (editorial
direction / important material / resistance / stop condition — not a
fixed template, built from whatever the packet actually contains) and
gives the writer material, not labels.

For this Edinburgh case, `rival_reading`/`unresolved_tension` are
deliberately left out of the B.2 brief -- not because the packet lacks
them, but because the task's own worked example (4 blocks, no RIVAL
section) and the arrival-economy instruction ("do not automatically
escalate... do not add another conceptual layer") both point toward a
smaller brief for this specific case. The packet itself still carries
all six fields internally (see sofa_discovery_shadow_b1.build_b1_packet)
-- nothing is deleted from the reasoning, only from what reaches the
writer's prompt.
"""
from __future__ import annotations

from orchestrator.sofa_discovery_shadow import SofaShadowError, assert_no_persona_leakage


# B.1's own persona-neutralization (sofa_discovery_shadow_b1._neutralize)
# replaced persona-named phrases with generic terms like "this working
# reading" / "it resists this reading too" -- correct for removing the
# persona name, but "working reading" is itself schema-flavored language
# that leaked into B.1's actual prose ("This is the working reading
# arriving from the aesthetic direction..."). B.2 applies one further,
# equally explicit substitution pass so that specific phrasing doesn't
# recur, without touching the packet itself or B.1's own neutralization.
_SCAFFOLD_LANGUAGE_SOFTENING = [
    ("this working reading arriving from the aesthetic side", "an access argument arriving from the aesthetic side"),
    ("it resists this reading too", "it resists that too"),
    ("this working reading", "that argument"),
]


def _soften_scaffold_language(text):
    if not text:
        return text
    out = text
    for old, new in _SCAFFOLD_LANGUAGE_SOFTENING:
        out = out.replace(old, new)
    return out


def build_b2_story_brief(packet: dict) -> dict:
    """Compiles a compact, persona-neutral, natural-language brief from a
    B.1-shape packet. Returns a dict with plain-English keys (never the
    packet's own schema names) so the writer prompt builder below never
    has to reproduce WORKING_READING/CORRECTION_MATERIAL/etc. as visible
    section headers.

    Fields present only if the underlying packet material exists —
    nothing invented here that build_b1_packet didn't already ground."""
    working_reading = packet["working_reading"]["value"]
    source_anchor = packet["source_anchor"]["value"]

    brief = {
        "opening_direction": (
            f"Begin from the source's own repeated image for how discovery happens here "
            f"— walking into a gallery, following your nose, stumbling on the unheralded "
            f"(the source's own words: \"{source_anchor}\"). The shape worth starting from: "
            f"{working_reading}"
        ),
    }

    if "correction_material" in packet:
        cm = packet["correction_material"]
        brief["important_material"] = {
            "source_evidence": cm["source_evidence"]["value"],
            "note": _soften_scaffold_language(cm["editorial_interpretation"]["value"]),
        }

    if "resisting_material" in packet:
        rm = packet["resisting_material"]
        brief["resistance"] = {
            "source_evidence": rm["source_evidence"]["value"],
            "note": _soften_scaffold_language(rm["editorial_interpretation"]["value"]),
        }

    brief["stop_condition"] = (
        "Once the strongest source-grounded changed understanding has landed, stop. Do "
        "not add another disability example, another world, an analogy, or a larger "
        "theory merely to keep going. A correction does not have to make the thesis "
        "bigger — it may simply make it more precise."
    )
    return brief


def build_b2_writer_prompt(source_text: str, brief: dict, target_words=(750, 850)):
    """Returns (system, user). Deliberately does NOT use any of the B.1
    packet's field names as prompt labels. Does NOT script a turn
    ('place the correction before the midpoint') — instructs the writer
    to let a later fact change an earlier reading only if it genuinely
    does, and never to announce that it's doing so."""
    lo, hi = target_words
    system = (
        "You are a prose writer for a disability-led publication. You are not a character "
        "and you have no biography — you are a writing function.\n\n"
        "You will be given an editorial direction and some material below. Write one "
        "article of narrative nonfiction from it. You are not filling in labeled sections "
        "or executing a sequence of editorial operations — write it as a single piece of "
        "thinking, the way a writer would after doing the reporting themselves.\n\n"
        "If later material genuinely changes how the opening should be understood, let it "
        "change — but do not announce the operation. Do not write sentences like 'this "
        "complicates the argument,' 'here is where the reading collides with itself,' or "
        "'the question becomes.' Let the new fact do the work; the reader should feel the "
        "understanding shift, not be told that it is shifting. The movement should feel "
        "caused by the world, not narrated by an editor.\n\n"
        "There is no required shape. Do not treat this as: state a thesis, then a "
        "correction, then a resistance, then a bigger thesis. Some material earns a real "
        "turn; nothing requires you to manufacture one you don't find.\n\n"
        f"LENGTH: roughly {lo}–{hi} words for this piece. Do not pad to reach the upper "
        f"end — if the material has said what it has to say at {lo} words or a little "
        f"under, stop there. Only go somewhat longer if you have a genuine, specific "
        f"reason the material demands it.\n\n"
        "ARRIVAL: once the strongest available material has produced a more precise (not "
        "necessarily bigger) understanding, you may stop. Do not automatically escalate "
        "into a second world, a diagnosis, an institution, or a universal theory just to "
        "extend the piece. Do not force more explicit disability content into the piece "
        "than the material itself earns — the disability lens can matter to how this "
        "piece sees without being stated as a topic.\n\n"
        "PERSPECTIVE: default to third-person / impersonal narrative nonfiction. First "
        "person is allowed ONLY to name a real editorial/reporting action actually "
        "supported by the material below (e.g. 'the review states...', 'reading this "
        "again...') — never a fabricated lived-experience episode, a biography, a wound, "
        "or a claim to have personally witnessed or experienced anything. If nothing below "
        "supports a real first-person reporting action, write in third person throughout. "
        "No persona voice, no roleplay, no disclosed or undisclosed character.\n\n"
        "GROUNDING (no exceptions): never state an editorial interpretation as if it were "
        "a measured, settled fact. Never invent a concrete detail (a barrier, a distance, "
        "a name, a date, a cause) beyond what the material below or the reference source "
        "actually contains. Never invent a source for a detail (e.g. attributing a real "
        "fact to 'the wall text' or any object/document not actually named as its source "
        "in the reference source). An editorial note below is never itself a fact — only a "
        "quoted excerpt is. Do not assert population-level or measured claims (e.g. 'the "
        "least distributed capacity') that the material doesn't establish.\n\n"
        "Write the article now. Do not explain your reasoning. Output only the article, "
        "with a title on the first line."
    )

    parts = [f"EDITORIAL DIRECTION:\n{brief['opening_direction']}\n"]

    if "important_material" in brief:
        im = brief["important_material"]
        parts.append(
            "MATERIAL THAT MATTERS (a source excerpt, and the editor's own note about it "
            "— the note is not itself a fact, only the excerpt is):\n"
            f"- excerpt: {im['source_evidence']}\n"
            f"- note: {im['note']}\n"
        )
    if "resistance" in brief:
        rs = brief["resistance"]
        parts.append(
            "MATERIAL THAT DOES NOT FIT CLEANLY (use it only if it genuinely advances the "
            "understanding above — do not force it in; the note is not itself a fact):\n"
            f"- excerpt: {rs['source_evidence']}\n"
            f"- note: {rs['note']}\n"
        )

    parts.append(f"{brief['stop_condition']}\n")
    parts.append(
        "REFERENCE SOURCE (the complete original source text — the only source of any "
        f"named person, quote, date, or number you may use):\n---\n{source_text}\n---\n"
    )
    user = "\n".join(parts)
    assert_no_persona_leakage(system + user)
    return system, user


def run_b2_writer(source_text: str, brief: dict, writer_llm_call) -> str:
    system, user = build_b2_writer_prompt(source_text, brief)
    raw = writer_llm_call(system, user)
    if not raw or not isinstance(raw, str) or not raw.strip():
        raise SofaShadowError("B.2 writer model call returned no usable text")
    return raw.strip()
