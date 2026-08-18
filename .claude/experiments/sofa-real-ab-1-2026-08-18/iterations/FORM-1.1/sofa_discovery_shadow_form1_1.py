#!/usr/bin/env python3
"""
sofa_discovery_shadow_form1_1.py — Sofa Architecture FORM-1.1 (narrow
Form->Writer correction over FORM-1). SHADOW ONLY. Real Article Test 1
continuation.

FORM-1's grounding diagnosis found 4 findings: 3 writer-origin slippages
(editorial-selection-as-centrality, a dropped "most" qualifier smoothed
into a uniform pattern, and a reviewer's personal opinion reattributed to
"the festival's own account") and 1 Form-origin defect (the destination
sentence itself didn't carry forward Hasegawa's "most" hedge that Form's
own material list already preserved). This module makes exactly the
narrow corrections that diagnosis calls for -- no Discovery redesign, no
return to a blind writer, no new source.

CHANGES FROM FORM-1:
  1. PROVENANCE TAGGING: every material item now carries an explicit
     provenance type (SOURCE_FACT / REVIEWER_OPINION), and the resisting-
     material duty quote is tagged REVIEWER_OPINION with an explicit
     writer-facing instruction never to reattribute it to "the festival."
     A deterministic guard (_assert_no_reattribution_language) scans
     every Form-authored text field for the specific reattribution
     phrases the writer produced last time.
  2. QUALIFIER PRESERVATION: the destination sentence is rewritten to
     never claim a uniform three-artist pattern. It states only what
     George and Walter jointly establish without qualification.
  3. EDITORIAL SELECTION != SOURCE CENTRALITY: explicit writer boundary
     added, with the exact FORM-1 phrasing ("sit near the center of what
     the festival is doing") named as the thing not to write.
  4. HASEGAWA: OMITTED from correction_material for this generation (see
     build_form1_1_packet's own decision note) -- not because his
     qualifier is false, but because using him forces either an incorrect
     uniform generalization (FORM-1's actual failure) or added complexity
     managing three different qualification states to make one clean
     point. George + Walter alone establish the distinction without
     hedging.
  5. ARRIVAL DISCIPLINE: explicit instruction to stop immediately once
     the distinction lands, naming FORM-1's own restatement phrases
     ("These are two claims...", "The first is...", "The second is...",
     "That is the distinction...") as patterns not to repeat.

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

# New in FORM-1.1: the specific reattribution failure observed in FORM-1
# ("the festival's own account allows" for a quote the source itself
# marks as the reviewer's personal opinion, "I think..."). Checked
# against every Form-authored text field (never against the quoted
# source text itself, which legitimately contains the reviewer's words).
_FORBIDDEN_REATTRIBUTION_PHRASES = [
    "the festival says", "the festival argues", "the festival allows",
    "the festival admits", "eaf admits", "the festival's own account",
    "the festival claims", "the festival states",
]


def _assert_no_attractor_language(text):
    lowered = text.lower()
    hits = [p for p in _FORBIDDEN_ATTRACTOR_PHRASES if p in lowered]
    if hits:
        raise SofaShadowError(f"FORM-1.1 brief contains forbidden attractor language: {hits}")


def _assert_no_reattribution_language(text):
    lowered = text.lower()
    hits = [p for p in _FORBIDDEN_REATTRIBUTION_PHRASES if p in lowered]
    if hits:
        raise SofaShadowError(f"FORM-1.1 brief contains forbidden reattribution language: {hits}")


def build_form1_1_packet(commission_brief: dict, evidence_packet: dict) -> dict:
    """Deterministic, no model call. Fails closed on the same grounding
    invariants as FORM-1, plus the two attractor/reattribution guards
    applied to every Form-authored text field."""
    if commission_brief.get("source_decision") != "commission":
        raise SofaShadowError("FORM-1.1 packet can only be built from a commissioned brief")
    source_text = (evidence_packet or {}).get("source_text") or ""
    if not source_text:
        raise SofaShadowError("evidence_packet has no source_text")

    source_anchor = commission_brief.get("source_anchor_examined")
    if not source_anchor or source_anchor not in source_text:
        raise SofaShadowError("source_anchor_examined missing or not grounded in source_text")

    resisting = commission_brief.get("resisting_example") or {}
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

    # HASEGAWA DECISION: OMITTED. George + Walter alone give the
    # distinction without qualification (both fully "never showed"/"died
    # having never shown"). Hasegawa's real "most of his work" hedge adds
    # no necessary movement here -- it only reintroduces the exact
    # smoothing temptation FORM-1's writer fell into. Not removed to make
    # grounding "easier" in the abstract; removed because two clean cases
    # already carry this specific distinction and a third, qualified case
    # adds complexity without adding anything the piece needs.
    correction_material = [
        {
            "text": _require_substring(
                "Like a lot of people in EAF, she never showed her work publicly in her lifetime, "
                "and was only discovered after her death in 2013.",
                source_text, "sandra_george",
            ),
            "provenance": "SOURCE_FACT",
        },
        {
            "text": _require_substring(
                "died having never shown any of the thousands of paintings and drawings he amassed "
                "over his lifetime",
                source_text, "frank_walter",
            ),
            "provenance": "SOURCE_FACT",
        },
    ]

    resisting_material = []
    if resisting_excerpt:
        resisting_material.append({
            "text": _require_substring(resisting_excerpt, source_text, "clarity_quote"),
            "provenance": "REVIEWER_OPINION",
            "provenance_note": (
                "This is the reviewer's own stated opinion (the source's own words are "
                "'I think they have a duty') — not a statement the festival or its "
                "institutions make about themselves. If used, attribute it to the reviewer "
                "or quote it without reassigning its source; never write 'the festival "
                "says/argues/allows/admits' this."
            ),
        })

    # Corrected destination: narrow to what George + Walter jointly
    # establish, no uniform three-artist claim, no causal/consent/agency/
    # access-theory extension.
    destination = (
        "The review uses discovery for the visitor's present encounter with previously "
        "unknown work, while some of the work it celebrates had remained unshown during its "
        "maker's lifetime."
    )

    for item in [{"text": destination, "provenance": None}] + opening_material_as_items(opening_material) + correction_material + resisting_material:
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


def opening_material_as_items(opening_material):
    return [{"text": t, "provenance": "SOURCE_FACT"} for t in opening_material]


def build_form1_1_writer_prompt(packet: dict, source_text: str):
    """Returns (system, user). Adds, relative to FORM-1: an attribution
    boundary for reviewer-opinion material, an editorial-selection-is-
    not-centrality boundary, explicit arrival-discipline naming FORM-1's
    own restatement phrases, and no fixed length floor."""
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

    system = (
        "Write a narrative nonfiction article from the material below, in the order given. "
        "You are not filling in labeled sections — write it as one continuous piece of "
        "thinking.\n\n"
        "Begin with how the festival describes its own way of being encountered. Then bring "
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
        f"{resisting_note}\n\n"
        "Do not invent scenes, biography, motives, search procedures, or lived experience. "
        "Write in third person; do not adopt a first-person narrator unless quoting the "
        "source.\n\n"
        f"{packet['length_guidance']}\n\n"
        "You are not a character and have no biography. Write only the article, with a "
        "title on the first line."
    )

    material_lines = (
        [f"- {m}" for m in packet["opening_material"]]
        + [f"- {m['text']}" for m in packet["correction_material"]]
        + [f"- {m['text']}" for m in packet["resisting_material"]]
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


def run_form1_1_writer(packet: dict, source_text: str, writer_llm_call) -> str:
    system, user = build_form1_1_writer_prompt(packet, source_text)
    raw = writer_llm_call(system, user)
    if not raw or not isinstance(raw, str) or not raw.strip():
        raise SofaShadowError("FORM-1.1 writer model call returned no usable text")
    return raw.strip()
