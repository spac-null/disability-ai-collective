#!/usr/bin/env python3
"""
sofa_discovery_shadow_form1_2.py — Sofa Architecture FORM-1.2 (narrow
provenance correction over FORM-1.1). SHADOW ONLY. Real Article Test 1
continuation.

FORM-1.1's grounding diagnosis found that all four non-grounded findings
collapse into ONE mechanism:

    REVIEWER CHARACTERIZATION -> FESTIVAL SELF-DESCRIPTION / POSSESSION

and that three Form-layer defects produce it:

  (1) the writer system prompt opened with "Begin with how the festival
      describes its own way of being encountered." The frozen source
      contains NO festival self-description at all -- it is a first-person
      critic's review. That instruction commanded an ungroundable framing.
  (2) opening_material was tagged SOURCE_FACT by opening_material_as_items()
      when it is in fact the reviewer's own narration/observation.
  (3) provenance was computed and stored in the packet, then DROPPED when
      the writer prompt was built (material_lines emitted only m['text']),
      so the writer never saw which material was fact and which was the
      reviewer talking.

FORM-1.2 makes exactly those three corrections and nothing else.

CHANGES FROM FORM-1.1 -- ONLY THESE THREE:
  A. FALSE OPENING INSTRUCTION REMOVED. "Begin with how the festival
     describes its own way of being encountered." is replaced with
     "Begin with the reviewer's description of what it is like to move
     through and encounter the festival." No destination preload, no new
     thesis.
  B. OPENING MATERIAL PROVENANCE CORRECTED. opening_material items now
     carry provenance REVIEWER_NARRATION instead of being tagged
     SOURCE_FACT. One narrow provenance type is added to the existing
     vocabulary (SOURCE_FACT / REVIEWER_OPINION -> + REVIEWER_NARRATION).
     The packet schema is otherwise unchanged.
  C. PROVENANCE PRESERVED INTO WRITER CONTEXT. material_lines now renders
     each item with a natural, writer-facing provenance prefix, and the
     system prompt carries an explicit attribution boundary.

NOT CHANGED: discovery, commission, source, selection, sequence,
argumentative burden, destination, arrival discipline, no-centrality
boundary, Hasegawa omission, grounding boundaries, length guidance,
attractor guards, writer model, generation parameters.

DELIBERATELY NOT CHANGED (recorded finding, out of scope for this
experiment): _FORBIDDEN_REATTRIBUTION_PHRASES is a literal verb blocklist
that FORM-1.1's writer evaded with a novel verb ("keeps its faith in"),
and it is applied ONLY to Form-authored text at packet-build time, never
to writer output -- so it is structurally incapable of catching the
failure it was built for. Redesigning it would add a second architectural
variable. FORM-1.2 tests the corrected information interface first; the
downstream grounding audit remains the check.

No new Fable call, no Discovery-model call. Every excerpt is checked as a
literal substring of the real source_text before use.
"""
from __future__ import annotations

from orchestrator.sofa_discovery_shadow import SofaShadowError, assert_no_persona_leakage
from orchestrator.sofa_discovery_shadow_b3 import _require_substring


_FORBIDDEN_ATTRACTOR_PHRASES = [
    "no choice", "could not advocate", "cannot advocate", "never meant to be found",
    "pleasure was possible because", "house style", "went looking on purpose",
    "an estate", "archive found", "curator found", "curator went looking",
    "advocate for themselves",
]

# Unchanged from FORM-1.1 (see module docstring: deliberately not redesigned).
_FORBIDDEN_REATTRIBUTION_PHRASES = [
    "the festival says", "the festival argues", "the festival allows",
    "the festival admits", "eaf admits", "the festival's own account",
    "the festival claims", "the festival states",
]

# CHANGE B: the provenance vocabulary. SOURCE_FACT and REVIEWER_OPINION
# already existed in FORM-1.1; REVIEWER_NARRATION is the one narrow type
# added, for material that is the reviewer describing/characterizing the
# festival rather than stating a checkable fact about it.
PROVENANCE_SOURCE_FACT = "SOURCE_FACT"
PROVENANCE_REVIEWER_NARRATION = "REVIEWER_NARRATION"
PROVENANCE_REVIEWER_OPINION = "REVIEWER_OPINION"

_VALID_PROVENANCE = {
    PROVENANCE_SOURCE_FACT,
    PROVENANCE_REVIEWER_NARRATION,
    PROVENANCE_REVIEWER_OPINION,
}

# CHANGE C: writer-facing rendering for each provenance type. Natural
# language, not schema/field labels -- the writer is told where a piece of
# material comes from, never shown an editorial-analysis field name.
_PROVENANCE_PREFIX = {
    PROVENANCE_SOURCE_FACT: "Source fact",
    PROVENANCE_REVIEWER_NARRATION: "From the reviewer's narration",
    PROVENANCE_REVIEWER_OPINION: "The reviewer explicitly argues",
}


def _assert_no_attractor_language(text):
    lowered = text.lower()
    hits = [p for p in _FORBIDDEN_ATTRACTOR_PHRASES if p in lowered]
    if hits:
        raise SofaShadowError(f"FORM-1.2 brief contains forbidden attractor language: {hits}")


def _assert_no_reattribution_language(text):
    lowered = text.lower()
    hits = [p for p in _FORBIDDEN_REATTRIBUTION_PHRASES if p in lowered]
    if hits:
        raise SofaShadowError(f"FORM-1.2 brief contains forbidden reattribution language: {hits}")


def _render_material_line(item):
    """CHANGE C. Renders one material item with its provenance surviving
    into the writer's context, in natural writer-facing language."""
    prov = item.get("provenance")
    if prov not in _VALID_PROVENANCE:
        raise SofaShadowError(
            f"FORM-1.2 material item has invalid/missing provenance {prov!r}; "
            f"must be one of {sorted(_VALID_PROVENANCE)}"
        )
    return f"- {_PROVENANCE_PREFIX[prov]}: {item['text']}"


def build_form1_2_packet(commission_brief: dict, evidence_packet: dict) -> dict:
    """Deterministic, no model call. Identical to FORM-1.1 except that
    opening_material items carry explicit REVIEWER_NARRATION provenance
    (CHANGE B) instead of being tagged SOURCE_FACT."""
    if commission_brief.get("source_decision") != "commission":
        raise SofaShadowError("FORM-1.2 packet can only be built from a commissioned brief")
    source_text = (evidence_packet or {}).get("source_text") or ""
    if not source_text:
        raise SofaShadowError("evidence_packet has no source_text")

    source_anchor = commission_brief.get("source_anchor_examined")
    if not source_anchor or source_anchor not in source_text:
        raise SofaShadowError("source_anchor_examined missing or not grounded in source_text")

    resisting = commission_brief.get("resisting_example") or {}
    resisting_excerpt = (resisting.get("evidence_candidate") or {}).get("source_excerpt", "")

    # CHANGE B: same three items, same order, same text -- correctly
    # classified. All three are the reviewer describing what moving
    # through the festival is like, not checkable source facts about it.
    # (Item 3 mixes a plain list of formats with the reviewer's judgment
    # that it is "impossible to figure out how any of it fits together";
    # it is labeled as narration because mislabeling narration as fact is
    # exactly the defect under correction, while the reverse is safe.)
    opening_material = [
        {
            "text": _require_substring(
                "You can’t walk into a gallery without learning about some subcultural genius or "
                "longlost creative you’ve never heard of.",
                source_text, "walking_1",
            ),
            "provenance": PROVENANCE_REVIEWER_NARRATION,
        },
        {
            "text": _require_substring(
                "You’ve just got to follow your nose and hope you sniff out something you like.",
                source_text, "walking_2",
            ),
            "provenance": PROVENANCE_REVIEWER_NARRATION,
        },
        {
            "text": _require_substring(
                "There are curated displays, satellite exhibitions, performances, off-site projects, "
                "and it’s impossible to figure out how any of it fits together.",
                source_text, "dispersed_festival",
            ),
            "provenance": PROVENANCE_REVIEWER_NARRATION,
        },
    ]

    # UNCHANGED from FORM-1.1.
    correction_material = [
        {
            "text": _require_substring(
                "Like a lot of people in EAF, she never showed her work publicly in her lifetime, "
                "and was only discovered after her death in 2013.",
                source_text, "sandra_george",
            ),
            "provenance": PROVENANCE_SOURCE_FACT,
        },
        {
            "text": _require_substring(
                "died having never shown any of the thousands of paintings and drawings he amassed "
                "over his lifetime",
                source_text, "frank_walter",
            ),
            "provenance": PROVENANCE_SOURCE_FACT,
        },
    ]

    # UNCHANGED from FORM-1.1.
    resisting_material = []
    if resisting_excerpt:
        resisting_material.append({
            "text": _require_substring(resisting_excerpt, source_text, "clarity_quote"),
            "provenance": PROVENANCE_REVIEWER_OPINION,
            "provenance_note": (
                "This is the reviewer's own stated opinion (the source's own words are "
                "'I think they have a duty') — not a statement the festival or its "
                "institutions make about themselves. If used, attribute it to the reviewer "
                "or quote it without reassigning its source; never write 'the festival "
                "says/argues/allows/admits' this."
            ),
        })

    # UNCHANGED from FORM-1.1 -- destination is explicitly not under test.
    destination = (
        "The review uses discovery for the visitor's present encounter with previously "
        "unknown work, while some of the work it celebrates had remained unshown during its "
        "maker's lifetime."
    )

    for item in ([{"text": destination, "provenance": PROVENANCE_SOURCE_FACT}]
                 + opening_material + correction_material + resisting_material):
        _assert_no_attractor_language(item["text"])
        _assert_no_reattribution_language(item["text"])

    return {
        "opening_material": opening_material,
        "correction_material": correction_material,
        "resisting_material": resisting_material,
        "destination": destination,
        "hasegawa_decision": (
            "OMITTED — George and Walter alone establish the distinction without qualification "
            "(both fully documented as never shown in their lifetimes). Hasegawa's real 'most of "
            "his work' hedge would force either an inaccurate uniform generalization across three "
            "artists (FORM-1's actual failure) or added complexity managing three different "
            "qualification states for one clean point. Not omitted to make grounding easier in "
            "the abstract — omitted because two clean cases already carry this specific movement."
        ),
        "grounding_boundaries": (
            "The source does not say why George or Walter went unseen during their lifetimes, "
            "does not describe how their work came to be shown now, and does not describe their "
            "wishes, intentions, or capacity regarding exhibition. It names no access barriers, "
            "distances, or excluded audiences."
        ),
        "length_guidance": (
            "Roughly 550–700 words for this piece — there is no fixed requirement to reach 700. "
            "Do not pad. If the distinction has genuinely landed at 550 words, stop there."
        ),
    }


def build_form1_2_writer_prompt(packet: dict, source_text: str):
    """Returns (system, user). Differs from FORM-1.1 in exactly two places:
    the opening instruction (CHANGE A) and the provenance boundary +
    provenance-carrying material rendering (CHANGE C)."""
    _assert_no_attractor_language(packet["destination"])
    _assert_no_reattribution_language(packet["destination"])

    resisting_note = ""
    if packet["resisting_material"]:
        resisting_note = (
            "\n\nOne piece of material below is the reviewer's own personal opinion, not a "
            "statement the festival makes about itself (the source's own words are 'I "
            "think...'). If you use it, keep it as the reviewer's view — never write 'the "
            "festival says,' 'the festival argues,' 'the festival allows,' 'the festival "
            "admits,' or any phrase that reassigns it to the festival or its institutions."
        )

    # CHANGE C: the attribution boundary. Tells the writer that provenance
    # must survive into the prose; says nothing about what conclusion to
    # draw beyond the Form's existing destination.
    provenance_boundary = (
        "\n\nEach piece of material below is labelled with where it comes from: a source "
        "fact, the reviewer's narration, or the reviewer's explicit argument. That "
        "provenance must survive into your prose. Do not convert a reviewer's observation, "
        "vocabulary, or opinion into the festival's or an institution's own self-description, "
        "position, or language unless the source itself supports that attribution. The labels "
        "are for attribution only — never name or quote them in the article."
    )

    system = (
        "Write a narrative nonfiction article from the material below, in the order given. "
        "You are not filling in labeled sections — write it as one continuous piece of "
        "thinking.\n\n"
        # CHANGE A: was "Begin with how the festival describes its own way of being
        # encountered." The source contains no festival self-description.
        "Begin with the reviewer's description of what it is like to move through and "
        "encounter the festival. Then bring "
        "in the facts about the two artists, together, using a plain, neutral transition — "
        "do not claim these two are central to the festival, representative of it, or the "
        "heart of its programme; you are choosing to look at them, the source does not rank "
        "them against anything else in the festival. After those facts, return to the "
        "meaning of 'discovery' — let the facts narrow what that word means without "
        "announcing that you are doing so.\n\n"
        f"The piece should land on this distinction: {packet['destination']} Do not extend "
        "this into any claim about why these artists went unseen, how their work came to be "
        "shown now, what they wanted, or whether they had a choice — the source does not "
        "say, and neither should the article. Do not introduce access barriers, consent, "
        "agency, or a disability example.\n\n"
        "Once the distinction has genuinely landed, STOP. Do not restate it a second or "
        "third time in different words. Do not write anything shaped like 'These are two "
        "claims...', 'The first is... The second is...', or 'That is the distinction...' "
        "followed by another paraphrase of the same point. A piece may end immediately after "
        "its strongest precise arrival — it does not need a conventional closing paragraph."
        f"{resisting_note}"
        f"{provenance_boundary}\n\n"
        "Do not invent scenes, biography, motives, search procedures, or lived experience. "
        "Write in third person; do not adopt a first-person narrator unless quoting the "
        "source.\n\n"
        f"{packet['length_guidance']}\n\n"
        "You are not a character and have no biography. Write only the article, with a "
        "title on the first line."
    )

    # CHANGE C: provenance now survives into the rendered material list.
    material_lines = (
        [_render_material_line(m) for m in packet["opening_material"]]
        + [_render_material_line(m) for m in packet["correction_material"]]
        + [_render_material_line(m) for m in packet["resisting_material"]]
    )
    user = (
        "MATERIAL (in order):\n" + "\n".join(material_lines) + "\n\n"
        f"GROUNDING BOUNDARIES: {packet['grounding_boundaries']}\n\n"
        f"FULL SOURCE TEXT (the only source of any named person, quote, date, or number you "
        f"may use):\n---\n{source_text}\n---\n"
    )
    assert_no_persona_leakage(system + user)
    for line in material_lines:
        _assert_no_attractor_language(line)
        _assert_no_reattribution_language(line)
    return system, user


def run_form1_2_writer(packet: dict, source_text: str, writer_llm_call) -> str:
    system, user = build_form1_2_writer_prompt(packet, source_text)
    raw = writer_llm_call(system, user)
    if not raw or not isinstance(raw, str) or not raw.strip():
        raise SofaShadowError("FORM-1.2 writer model call returned no usable text")
    return raw.strip()
