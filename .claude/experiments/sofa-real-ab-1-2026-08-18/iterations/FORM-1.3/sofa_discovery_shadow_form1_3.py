#!/usr/bin/env python3
"""
sofa_discovery_shadow_form1_3.py — Sofa Architecture FORM-1.3 (Form-layer
semantic-ownership + functional-position correction over FORM-1.2).
SHADOW ONLY. Real Article Test 1 continuation.

FORM-1.2 disconfirmed the hypothesis that the remaining Edinburgh grounding
problem was provenance information being dropped between Form and Writer.
All three of its corrections landed and festival-possession claims still
increased. The Form-layer diagnosis that followed found two defects, both
inside Article Form's own remit (sequence, argumentative burden, ownership):

  DEFECT 1 — OWNERSHIP PROPAGATION FAILURE. FORM-1.1 already fixed the
  ungrounded ownership FORM-1 had encoded in `correction_function` ("The
  festival calls two different things 'discovery'"): it deleted that field
  and made the destination name the review as owner. But ownership was
  fixed ONLY in the destination. The one operative instruction governing
  the article's middle -- "After those facts, return to the meaning of
  'discovery'" -- left the word OWNERLESS, identically in FORM-1.1 and
  FORM-1.2. The Form named the correct owner once, at the finish line, and
  said nothing about ownership across the stretch where the writer works.
  Separately, the destination's pronoun ("the work IT celebrates") was
  ambiguous at the ownership-critical clause, and `festival` appeared 10x
  in the FORM-1.2 system prompt against `discovery` 2x, mostly in
  prohibitions naming the festival as a candidate speaker.

  DEFECT 2 — FUNCTIONAL POSITION NOT ENCODED. The packet field is named
  `resisting_material`, but that name never reached the writer; the only
  thing the prompt said about it was attributional. The Form also carried
  an internal contradiction: "in the order given" (which makes the
  resistance material terminal, being last in the list) versus "Once the
  distinction has genuinely landed, STOP" (which makes the arrival
  terminal). Both cannot hold. FORM-1.1 resolved it one way (resistance
  para 6, arrival para 8); FORM-1.2 resolved it the other (arrival para 8,
  resistance para 9, forcing a restatement paragraph). Neither writer
  disobeyed -- the Form permitted both.

CHANGES FROM FORM-1.2 -- ONLY THESE TWO:

  1. SEMANTIC OWNERSHIP.
     - The ownerless "return to the meaning of 'discovery'" is replaced by
       an instruction that returns to the REVIEWER'S OWN LANGUAGE of
       discovery and sets it beside the source-grounded George/Walter facts.
     - The destination is made provenance-neutral: "some of the work
       discussed in the review" replaces "the work it celebrates"
       (removing both the ambiguous pronoun and the festival-coded verb
       "celebrates", which the source attaches to the festival).
     - The three scattered festival prohibitions are replaced by ONE
       positive boundary: the festival is a setting/referent, not a
       speaker. This states the rule once instead of naming the festival
       as a candidate speaker three times in negations. Net effect is
       fewer festival mentions, not more. This is not a new guard and not
       a larger blocklist -- it is smaller than what it replaces.

  2. FUNCTIONAL POSITION.
     - "in the order given" and all global list-order authority are
       DELETED. The material list is a supply, not a running order.
     - One functional route is stated instead, placing the countervoice
       BEFORE the arrival:
         reviewer's encounter texture -> George/Walter facts ->
         reviewer's clarity/duty countervoice -> return to the reviewer's
         discovery language -> distinction/arrival -> STOP
     - The arrival is explicitly terminal.

KEPT FROM FORM-1.2 (these worked): the reviewer-framed opening, the
REVIEWER_NARRATION classification of opening_material, and provenance
availability in the writer context. Added narrowly: prose must not discuss
attribution with the reader (FORM-1.2 leaked one bookkeeping sentence,
"That is the reviewer's own conviction, not the festival's line about
itself").

UNCHANGED: source, commission, Discovery, George/Walter evidentiary
burden, intended discovery, no-agency/consent boundary, grounding
boundaries, length guidance, Hasegawa omission, attractor guard,
reattribution guard (still Form-text-only, still not redesigned),
single-generation discipline.

EXECUTION MODE: LOCAL_CLAUDE_SUBSCRIPTION. This is a manual
architecture-development run, NOT a production-path replay -- the writer
identity does not match the frozen Edinburgh lineage (Opus 4.8 via
CLIProxy), which is a real limitation on comparing it to FORM-1/1.1/1.2.
"""
from __future__ import annotations

import sys
from pathlib import Path

_AUTOMATION = Path("/Users/stargatesgx/code/disability-collective-ai/automation")
if str(_AUTOMATION) not in sys.path:
    sys.path.insert(0, str(_AUTOMATION))

from orchestrator.sofa_discovery_shadow import SofaShadowError, assert_no_persona_leakage


def _require_substring(excerpt, source_text, label):
    """Vendored verbatim from orchestrator.sofa_discovery_shadow_b3 (which
    lives only in the Trident experiment worktree), so this module is
    self-contained for the local run. Behaviour identical."""
    if excerpt not in source_text:
        raise SofaShadowError(f"B.3 ordered-material excerpt ({label}) is not a literal "
                              f"substring of source_text — refusing to use it: {excerpt!r}")
    return excerpt


_FORBIDDEN_ATTRACTOR_PHRASES = [
    "no choice", "could not advocate", "cannot advocate", "never meant to be found",
    "pleasure was possible because", "house style", "went looking on purpose",
    "an estate", "archive found", "curator found", "curator went looking",
    "advocate for themselves",
]

# Unchanged from FORM-1.1/1.2. Still applied only to Form-authored text at
# packet-build time. Deliberately not redesigned (would add a variable).
_FORBIDDEN_REATTRIBUTION_PHRASES = [
    "the festival says", "the festival argues", "the festival allows",
    "the festival admits", "eaf admits", "the festival's own account",
    "the festival claims", "the festival states",
]

PROVENANCE_SOURCE_FACT = "SOURCE_FACT"
PROVENANCE_REVIEWER_NARRATION = "REVIEWER_NARRATION"
PROVENANCE_REVIEWER_OPINION = "REVIEWER_OPINION"

_VALID_PROVENANCE = {
    PROVENANCE_SOURCE_FACT,
    PROVENANCE_REVIEWER_NARRATION,
    PROVENANCE_REVIEWER_OPINION,
}

_PROVENANCE_PREFIX = {
    PROVENANCE_SOURCE_FACT: "Source fact",
    PROVENANCE_REVIEWER_NARRATION: "From the reviewer's narration",
    PROVENANCE_REVIEWER_OPINION: "The reviewer explicitly argues",
}


def _assert_no_attractor_language(text):
    lowered = text.lower()
    hits = [p for p in _FORBIDDEN_ATTRACTOR_PHRASES if p in lowered]
    if hits:
        raise SofaShadowError(f"FORM-1.3 brief contains forbidden attractor language: {hits}")


def _assert_no_reattribution_language(text):
    lowered = text.lower()
    hits = [p for p in _FORBIDDEN_REATTRIBUTION_PHRASES if p in lowered]
    if hits:
        raise SofaShadowError(f"FORM-1.3 brief contains forbidden reattribution language: {hits}")


def _render_material_line(item):
    prov = item.get("provenance")
    if prov not in _VALID_PROVENANCE:
        raise SofaShadowError(
            f"FORM-1.3 material item has invalid/missing provenance {prov!r}; "
            f"must be one of {sorted(_VALID_PROVENANCE)}"
        )
    return f"- {_PROVENANCE_PREFIX[prov]}: {item['text']}"


def build_form1_3_packet(commission_brief: dict, evidence_packet: dict) -> dict:
    """Deterministic, no model call. Identical to FORM-1.2 except the
    destination wording (CHANGE 1)."""
    if commission_brief.get("source_decision") != "commission":
        raise SofaShadowError("FORM-1.3 packet can only be built from a commissioned brief")
    source_text = (evidence_packet or {}).get("source_text") or ""
    if not source_text:
        raise SofaShadowError("evidence_packet has no source_text")

    source_anchor = commission_brief.get("source_anchor_examined")
    if not source_anchor or source_anchor not in source_text:
        raise SofaShadowError("source_anchor_examined missing or not grounded in source_text")

    resisting = commission_brief.get("resisting_example") or {}
    resisting_excerpt = (resisting.get("evidence_candidate") or {}).get("source_excerpt", "")

    # UNCHANGED from FORM-1.2 (this classification worked).
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

    # UNCHANGED from FORM-1.1/1.2. No Hasegawa burden.
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

    # UNCHANGED material; the provenance_note's verb list stays in the
    # PACKET (it is Form-internal documentation) but is no longer echoed
    # into the writer prompt as a prohibition -- see CHANGE 1.
    resisting_material = []
    if resisting_excerpt:
        resisting_material.append({
            "text": _require_substring(resisting_excerpt, source_text, "clarity_quote"),
            "provenance": PROVENANCE_REVIEWER_OPINION,
            "provenance_note": (
                "This is the reviewer's own stated opinion (the source's own words are "
                "'I think they have a duty') — not a statement the festival or its "
                "institutions make about themselves."
            ),
            "narrative_function": "COUNTERVOICE — must press on the emerging reading BEFORE arrival.",
        })

    # CHANGE 1: provenance-neutral. "the work discussed in the review"
    # replaces "the work it celebrates" -- removing the ambiguous pronoun
    # and the festival-coded verb the source attaches to the festival
    # ("the whole festival is a celebration of the underground and
    # unheralded").
    destination = (
        "The review uses discovery for the visitor's present encounter with previously "
        "unknown work, while some of the work discussed in the review had remained unshown "
        "during its maker's lifetime."
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
        "narrative_route": [
            "reviewer's encounter texture",
            "George/Walter source facts",
            "reviewer's clarity/duty countervoice",
            "return to the reviewer's discovery language",
            "distinction / arrival",
            "STOP",
        ],
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


def build_form1_3_writer_prompt(packet: dict, source_text: str):
    """Returns (system, user). Differs from FORM-1.2 in exactly two places:
    semantic ownership (CHANGE 1) and functional position (CHANGE 2)."""
    _assert_no_attractor_language(packet["destination"])
    _assert_no_reattribution_language(packet["destination"])

    # CHANGE 1: ONE positive boundary, replacing FORM-1.2's three scattered
    # prohibitions that each named the festival as a candidate speaker.
    festival_boundary = (
        "The festival is a setting in this piece — a place the reviewer moves through, looks at, "
        "and describes. It is not a speaker. The source records no festival-authored language of "
        "any kind: no programme copy, no marketing, no curatorial statement, no spokesperson. So "
        "the festival has no vocabulary, intent, self-description, naming, or position of its own "
        "here. The language of discovery in this material is the reviewer's."
    )

    # CHANGE 1 (cont.) + KEPT FROM 1.2: provenance stays available, but the
    # writer must not narrate attribution to the reader (FORM-1.2 leaked
    # exactly one such sentence).
    provenance_note = (
        "Each piece of material below is labelled with where it comes from: a source fact, the "
        "reviewer's narration, or the reviewer's explicit argument. Keep that provenance true in "
        "your prose — attribute in the ordinary way prose does ('the reviewer writes', 'in the "
        "review'). But do not discuss attribution with the reader: no sentences about whose view "
        "something is or is not, and never state what someone did not say. The labels are for "
        "your accuracy only; they must never appear in the article or be commented on."
    )

    # CHANGE 2: one functional route. "in the order given" is DELETED.
    system = (
        "Write a narrative nonfiction article from the material below. You are not filling in "
        "labeled sections — write it as one continuous piece of thinking. The material below is "
        "a supply to draw on, not a running order; the route is the route given here.\n\n"
        "Follow this route:\n"
        "1. Begin with the reviewer's description of what it is like to move through and "
        "encounter the festival.\n"
        "2. Then the facts about the two artists, together, using a plain, neutral transition — "
        "do not claim these two are central to the festival, representative of it, or the heart "
        "of its programme; you are choosing to look at them, the source does not rank them "
        "against anything else in the festival.\n"
        "3. Then the reviewer's stated conviction about telling hidden stories clearly. Let it "
        "press on the reading you are forming, while that reading is still forming — it has to "
        "complicate the piece before the piece resolves.\n"
        "4. Then return to the reviewer's own language of discovery — the words the review itself "
        "uses for finding work no one had seen before — and set that language beside the facts "
        "about the two artists. Let those facts narrow what the reviewer's use of the word can "
        "mean, without announcing that you are doing so.\n"
        "5. Arrive at the distinction, and stop there.\n\n"
        f"The piece should land on this distinction: {packet['destination']} Do not extend "
        "this into any claim about why these artists went unseen, how their work came to be "
        "shown now, what they wanted, or whether they had a choice — the source does not "
        "say, and neither should the article. Do not introduce access barriers, consent, "
        "agency, or a disability example.\n\n"
        "The arrival is the end of the piece. Nothing follows it. Do not restate the distinction "
        "a second or third time in different words, and do not write anything shaped like 'These "
        "are two claims...', 'The first is... The second is...', or 'That is the distinction...' "
        "followed by another paraphrase of the same point. A piece may end immediately after its "
        "strongest precise arrival — it does not need a conventional closing paragraph.\n\n"
        f"{festival_boundary}\n\n"
        f"{provenance_note}\n\n"
        "Do not invent scenes, biography, motives, search procedures, or lived experience. "
        "Write in third person; do not adopt a first-person narrator unless quoting the "
        "source.\n\n"
        f"{packet['length_guidance']}\n\n"
        "You are not a character and have no biography. Write only the article, with a "
        "title on the first line."
    )

    material_lines = (
        [_render_material_line(m) for m in packet["opening_material"]]
        + [_render_material_line(m) for m in packet["correction_material"]]
        + [_render_material_line(m) for m in packet["resisting_material"]]
    )
    user = (
        "MATERIAL:\n" + "\n".join(material_lines) + "\n\n"
        f"GROUNDING BOUNDARIES: {packet['grounding_boundaries']}\n\n"
        f"FULL SOURCE TEXT (the only source of any named person, quote, date, or number you "
        f"may use):\n---\n{source_text}\n---\n"
    )
    assert_no_persona_leakage(system + user)
    for line in material_lines:
        _assert_no_attractor_language(line)
        _assert_no_reattribution_language(line)
    return system, user
