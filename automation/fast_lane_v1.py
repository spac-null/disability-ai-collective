#!/usr/bin/env python3
"""FAST LANE V1 -- minimum pipeline: LEDGER -> ARTICLE_PACKET -> ONE_WRITER -> SAFETY ->
GROUNDING -> FACT_CHECK -> READER.

No Continuity, no Prose Finish, no repair loop, no Architecture LLM call. Reuses the
canonical Safety/Grounding/Fact-Check/Reader stage functions from new_engine_v1.composition
and composition_factual_bridge UNCHANGED -- the only new code here is the ARTICLE_PACKET
compiler, the deterministic packet->arch translation, the ONE_WRITER prompt/schema
(a superset of the existing WRITER_SYSTEM, adding CLAIM_MAP), and mechanical CLAIM_MAP
validation.

Isolated from canonical production: run from the feat/fast-lane-v1-minimal worktree only.
Not wired into new_engine_production.py or the publication bridge's normal selection path.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import composition_factual_bridge as FCB                 # noqa: E402
from new_engine_v1 import composition as CP               # noqa: E402
from new_engine_v1 import story as ST                     # noqa: E402
from new_engine_v1 import ledger as LG                     # noqa: E402
from new_engine_v1.provider import Provider, DEFAULT_MODEL  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# ARTICLE_PACKET -- compiled by hand from the retained, already-corrected Ledger for
# this first replay. A later Fast Lane run compiles this from a fresh Ledger the same
# way; nothing here is specific to the replay path except which facts were picked.
# ══════════════════════════════════════════════════════════════════════════════
def build_article_packet() -> dict:
    return {
        "question": (
            "What does it mean for a communication system to learn one person's "
            "language and still retain a function called ‘reset to default’?"
        ),
        "primary_carrier": {
            "carrier": "TD Snap's word-prediction reset",
            "evidence_ids": ["F60", "F45"],
        },
        "load_bearing_facts": ["F60", "F45", "F46", "F39", "F40", "F43"],
        "supporting_facts": ["F10", "F12", "F13", "F32", "F21"],
        "forbidden_claims": [
            "attribute TD Talk's phrase-prediction, voice, or any other property to "
            "TD Snap -- TD Talk and TD Snap are separate products in the Ledger",
            "describe any technical or storage mechanism behind TD Snap's word-prediction "
            "reset beyond what is stated: that it learns from spoken messages and can be "
            "reset to default",
            "conflate the TD Snap release notes document version/date (1.40.2, "
            "2026-08-17) with the release version/date that added the reset (1.31, "
            "2024-02-23), or transfer either onto TD Talk",
            "claim Tobii Dynavox uses learned word-prediction data to train shared or "
            "company-wide AI models -- the Ledger licenses only the negative, that it "
            "does not",
            "begin with ‘the release notes say’, ‘the documentation "
            "describes’, ‘the statement asserts’, or any other "
            "source-first framing",
            "turn this into a general accessibility-service story or a review of AAC "
            "technology",
        ],
        "ending_return": (
            "Return to the reset-to-default action beside the personalized model it "
            "erases -- the concrete operation, not a conclusion beyond what the Ledger "
            "states."
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# GENERAL FAST LANE RULE (2026-09-12): IMPLEMENTATION_DETAILS_REQUIRE_DIRECT_LICENSE.
#
# The retained TD Snap replay's Grounding hold was one shape three times over: a
# capability fact ("word prediction learns from spoken messages", "resetting restores
# the default") got an invented IMPLEMENTATION wrapped around it -- an interface
# location ("in the menus"), an action count ("one action"), an update cadence ("each
# message"). None of those were in the cited fact; all three read as natural details a
# capability like this "would" have. A capability does not license its implementation.
#
# This is a standing prohibition, not a matcher: no code here scans prose for these
# words and blocks on a hit (Grounding already does that job, against the real
# sources). It exists so future Article Packets don't hand the Writer language that
# already asserts the detail (see beat B4's fixed "happens" text above, and
# story_spine, both of which originally said "menu action" themselves) and so the
# Writer is told the rule directly, not just left to infer it from what got held.
# ══════════════════════════════════════════════════════════════════════════════
GENERAL_CONTRACT_PROHIBITIONS = [
    "Do not state or imply an interface location (a menu, a screen, a settings page) "
    "for any action unless the cited fact names that location.",
    "Do not state or imply a number of clicks, steps, taps or actions unless the "
    "cited fact states that number.",
    "Do not state or imply a frequency or cadence (per message, per session, "
    "continuously, immediately) for any update or change unless the cited fact "
    "states it.",
    "Do not state or imply per-event or per-message update behavior for a learning "
    "or adaptation process unless the cited fact describes events individually.",
    "Do not state or imply where data is stored, transmitted or processed unless the "
    "cited fact says so.",
    "Do not state or imply an internal technical mechanism (how something is "
    "computed, saved or triggered) beyond what the cited fact itself states.",
    "Do not state or imply a device or data-flow implementation (which device, app "
    "or system component performs an action) unless the cited fact names it.",
]


# ══════════════════════════════════════════════════════════════════════════════
# PACKET -> ARCH. Deterministic, no model call. Bypasses the Architect LLM stage and
# check_architecture()/validate_evidence_hierarchy() entirely (Fast Lane does not run
# a full Architecture stage) -- but the shape it produces is what
# story.build_packet()/validate_packet() already expect, so write_article()'s own
# packet-building and rendering path is reused unmodified downstream.
# ══════════════════════════════════════════════════════════════════════════════
def build_synthetic_arch(packet: dict, article_type: str) -> dict:
    load = packet["load_bearing_facts"]
    support = packet["supporting_facts"]
    beats = [
        {"beat_id": "B1",
         "happens": "TD Snap's word prediction is described as learning from a "
                    "person's own spoken messages to build predictions personal to "
                    "them, on software used by people accessing communication through "
                    "alternative methods such as eye gaze or switches",
         "concrete_carrier": "the personalized word-prediction model",
         "facts_allowed": ["F60", "F32", "F21"],
         "concept_introduced": "", "why_reader_wants_next":
             "a model built from one person's own words is not yet known to be "
             "erasable",
         "must_not_say_yet": "the reset action"},
        {"beat_id": "B2",
         "happens": "A later TD Snap release added an action that resets that "
                    "learned model back to its default, documented in the release "
                    "notes and in the current manual",
         "concrete_carrier": "the reset-to-default action",
         "facts_allowed": ["F45", "F46", "F43", "F10"],
         "concept_introduced": "", "why_reader_wants_next":
             "what happens to the learned model once reset is not yet known",
         "must_not_say_yet": "the data boundary"},
        {"beat_id": "B3",
         "happens": "Tobii Dynavox's own boundary commitments say personalization "
                    "data stays specific to the individual and is never used to "
                    "train shared AI models, while TD Snap itself works only within "
                    "its own hardware and support boundary",
         "concrete_carrier": "the boundary around the learned data",
         "facts_allowed": ["F12", "F13", "F40", "F39"],
         "concept_introduced": "", "why_reader_wants_next": "",
         "must_not_say_yet": ""},
        {"beat_id": "B4",
         "happens": "The reset sits beside the model it can erase: a personal "
                    "language pattern that exists nowhere else",
         "concrete_carrier": "the reset to default",
         "facts_allowed": ["F60", "F45"],
         "concept_introduced": "", "why_reader_wants_next": "",
         "must_not_say_yet": ""},
    ]
    prohibitions = []
    for claim in packet["forbidden_claims"]:
        prohibitions.append("Do not " + claim + ".")
    prohibitions += GENERAL_CONTRACT_PROHIBITIONS
    return {
        "article_type": article_type,
        "story_spine": "A communication system that learns one person's language "
                       "still keeps a reset that returns that model to default.",
        "opening_object_or_event": "The personalized word-prediction model TD Snap "
                                   "builds from one person's own spoken messages.",
        "reader_initial_state": "",
        "beats": beats,
        "turn": "",
        "crip_turn": packet["question"],
        "ending_move": packet["ending_return"],
        "use_facts": list(load) + list(support),
        "use_quotes": [],
        "definitions": {},
        "prohibitions": prohibitions,
        "cut_evidence": [],
        "final_lens": {},
    }


# ══════════════════════════════════════════════════════════════════════════════
# ONE_WRITER -- the existing WRITER_SYSTEM (house doctrine, unchanged) plus one
# additional required output field, CLAIM_MAP. Uses the existing writer_packet()/
# ST.build_packet()/ST.render() and the existing CP._ask() call-and-retry-once helper.
# ══════════════════════════════════════════════════════════════════════════════
ESTABLISHED, ATTRIBUTED, DISPUTED, UNCERTAIN = (
    "ESTABLISHED", "ATTRIBUTED", "DISPUTED", "UNCERTAIN")
CLAIM_STATUSES = (ESTABLISHED, ATTRIBUTED, DISPUTED, UNCERTAIN)
# Only ESTABLISHED is "unqualified" -- the other three all mean "this still needs its
# speaker or its uncertainty carried in the prose", so the one thing that must never
# happen is one of them arriving at the Writer's own reported ESTABLISHED.
QUALIFIED_STATUSES = (ATTRIBUTED, DISPUTED, UNCERTAIN)

FAST_LANE_WRITER_SYSTEM = (
    CP.WRITER_SYSTEM
    + "\n\nIMPLEMENTATION_DETAILS_REQUIRE_DIRECT_LICENSE. A fact that grants a "
      "capability (something a system does, or can do) does not grant its "
      "implementation. Unless the specific fact you are using says so directly, do "
      "not add: an interface location (a menu, a screen); a number of clicks, steps "
      "or actions; a frequency or cadence (per message, continuously, immediately); "
      "per-event update behavior for a learning process; a storage or data-flow "
      "location; or an internal technical mechanism. Write the capability and its "
      "stated effect, and stop there -- do not supply the natural-sounding detail of "
      "how it would work.\n"
    + "\n\nATTRIBUTION_AND_STATUS_MUST_SURVIVE. Every fact below is marked "
      "ESTABLISHED, ATTRIBUTED, DISPUTED or UNCERTAIN in FACT STATUS. You may make "
      "the prose natural, but the status must survive into it exactly:\n"
      "  ESTABLISHED -> write it as fact.\n"
      "  ATTRIBUTED -> keep the speaker in the sentence ('her lawyer says...', "
      "'a DHS spokesperson said...'). Do not convert \"X's lawyer said X did\" into "
      "\"X did\".\n"
      "  DISPUTED -> keep BOTH sides attributed to their own speaker. Do not silently "
      "adopt one side as what happened.\n"
      "  UNCERTAIN -> keep the hedge; do not resolve it.\n"
      "None of the four may be written as a stronger one, ever, however natural the "
      "stronger sentence would read. Do not merge two facts into a stronger claim "
      "neither states alone. Do not invent a document, a file, a decision record, a "
      "signing date, a sequence, a before/after relation, a motive or a belief that "
      "is not explicitly in a fact below -- a date attached to an EVENT is not the "
      "date of a DOCUMENT, and two separately dated facts do not by themselves create "
      "a chronology between them. Literary force is never factual permission.\n"
    + "\n\nEXCLUSIVITY_AND_SUFFICIENCY_REQUIRE_DIRECT_LICENSE. Do not introduce a "
      "claim built on only, enough, sufficient, required, needed, alone, "
      "regardless of, without needing, or no longer necessary when it implies that "
      "another fact, person, account or action was irrelevant, unnecessary, "
      "excluded, or causally sufficient by itself -- unless a fact below explicitly "
      "licenses that relation. Two attributed accounts placed side by side may "
      "disagree; the article may not then add a further sentence ranking them "
      "('only one was needed', 'the other did not matter'). Let the reader hold the "
      "disagreement -- do not resolve it for them."
)


def render_fact_status(fact_status: dict) -> str:
    """The supplementary block fast_lane_write() appends after the rendered packet,
    naming each selected fact's status explicitly rather than leaving the Writer to
    infer it only from proposition wording. Fast-Lane-only; story.render() itself is
    untouched."""
    if not fact_status:
        return ""
    lines = ["", "FACT STATUS (carry this into the prose exactly; never upgrade it)"]
    for fid, ann in sorted(fact_status.items()):
        status = ann.get("claim_status", ESTABLISHED)
        who = ann.get("attribution_to")
        bit = "  %s: %s" % (fid, status)
        if who:
            bit += " (%s)" % who
        lines.append(bit)
    return "\n".join(lines) + "\n"


FAST_LANE_WRITER_TIMEOUT = 400  # seconds; CP._ask()'s Provider.complete() default is
# 180s, shared by every canonical stage. This one call is long (house doctrine +
# FACT STATUS block, up to 6,000 output tokens) and hit that shared default twice in
# a row on the real immigration run. Overridden HERE ONLY, for this one Fast-Lane
# call -- provider.py's own default, and every canonical composition.py caller of
# _ask(), are untouched.


def fast_lane_ask(provider, system: str, user: str, max_tokens: int, stage: str,
                  code: str, timeout: int = FAST_LANE_WRITER_TIMEOUT) -> tuple:
    """Local equivalent of composition._ask(), differing ONLY in threading a longer
    `timeout` through to provider.complete() -- _ask() itself has no timeout
    parameter to override. Same parse-and-retry-ONCE-on-malformed-JSON behavior, and
    a transport/provider exception is NOT retried, exactly as _ask() does not retry
    one either: this changes how long one attempt may run, not how many attempts a
    failure gets."""
    last = None
    for attempt in (1, 2):
        try:
            comp = provider.complete(system=system, user=user, max_tokens=max_tokens,
                                     timeout=timeout)
        except Exception as e:
            if CP._is_subscription_limit(e):
                raise CP.CompositionHold(
                    stage, CP.CLAUDE_SUBSCRIPTION_LIMIT,
                    ["the Claude subscription cannot serve this call: %s"
                     % str(e)[:300], "stopping; no paid fallback was attempted"])
            if not isinstance(e, CP.ProviderError) and type(e).__name__ != "ClaudeCLIError":
                raise
            raise CP.CompositionHold(stage, code, ["provider unavailable: %s" % e])
        try:
            return CP.parse_json_object(comp.text), CP._identity(comp, attempt)
        except CP.ProviderError as e:
            last = e
    raise CP.CompositionHold(stage, CP.INVALID_JSON_REPLY,
                             ["reply was not one JSON object after two attempts: %s"
                              % last])


def fast_lane_write(provider, arch: dict, ledger: dict,
                    fact_status: dict | None = None) -> tuple:
    """ARTICLE ONLY (2026-09-12). Returns (article_text, negative_lineage, packet,
    identity) -- no claim_map. Production evidence showed asking one call to both
    write strong prose AND maintain sentence-level fact-id bookkeeping caused the
    bookkeeping to drift even when the prose itself was correct (fact ids shifted
    across several consecutive sentences while the article text stayed accurate).
    Claim-mapping is now a SEPARATE, READ-ONLY pass over the frozen article -- see
    claim_map_article() below -- so a bookkeeping retry never risks the prose, and a
    prose retry is never needed to fix bookkeeping.

    `fact_status` is still passed to the Writer (via FACT STATUS) so attribution and
    dispute status shape the prose itself; only the Writer's own self-reporting of
    that status per sentence has moved to the Claim Mapper.
    """
    packet, rendered = CP.writer_packet(arch, ledger, cut_prohibitions=None)
    rendered = rendered + render_fact_status(fact_status or {})
    obj, ident = fast_lane_ask(provider, FAST_LANE_WRITER_SYSTEM, rendered, 6_000,
                               "FAST_LANE_WRITER", "FAST_LANE_WRITER_HOLD")
    article = CP._clean_article(obj.get("article", ""))
    if len((article or "").split()) < CP.WRITER_MIN_WORDS:
        raise CP.CompositionHold("FAST_LANE_WRITER", "FAST_LANE_WRITER_HOLD",
                                 ["writer reply has no real article body"])
    return article, negative_lineage_dict(obj.get("negative_lineage") or []), \
        packet, ident


def negative_lineage_dict(raw: list) -> dict:
    """composition.safety_audit() expects negative_lineage as {sentence_id:
    [fact_ids]} (it calls lineage.get(sid) directly) -- the Writer returns a list of
    {"sentence_id":..., "fact_ids":...} objects, the same shape WRITER_SYSTEM has
    always specified. TD Snap's list happened to be empty, so `[] or {}` silently
    fell back to a dict and masked the mismatch; the immigration article's non-empty
    list surfaced it. Fast Lane has no Continuity stage (draft text is always the
    final text), so this is a direct conversion, not composition.carry_negative_
    lineage()'s draft/final position remapping for an edited descendant."""
    return {item["sentence_id"]: item.get("fact_ids", [])
           for item in (raw or []) if item.get("sentence_id")}


# ══════════════════════════════════════════════════════════════════════════════
# CLAIM MAPPER -- a separate, READ-ONLY pass over the FROZEN article. It cannot
# rewrite, edit or judge prose; it only names which already-selected fact(s) each
# already-numbered sentence rests on, and that sentence's status. Sentence identity
# comes from composition.label_sentences() (the same S001.. numbering negative_
# lineage already uses), not from the model's own count -- removing exactly the
# self-numbering drift that caused the original defect.
# ══════════════════════════════════════════════════════════════════════════════
CLAIM_MAPPER_SYSTEM = (
    "You are a metadata annotator, not a writer. The article below is FINISHED and "
    "FROZEN -- you will never see it change, and nothing you say can change it. Your "
    "only task is bookkeeping: for each numbered sentence that makes a factual claim "
    "(names a product, person, action, date, version or number), report which "
    "fact_id(s) from FACTS AVAILABLE it actually rests on, and that sentence's "
    "status.\n"
    "\n"
    "You may not cite a fact_id that is not listed in FACTS AVAILABLE. You may not "
    "invent a fact, infer one, or add anything the sentence does not already say. A "
    "purely transitional sentence with no fact-specific claim may be omitted "
    "entirely.\n"
    "\n"
    "Each fact in FACTS AVAILABLE is already marked ESTABLISHED, ATTRIBUTED, DISPUTED "
    "or UNCERTAIN. Report the sentence's claim_status to MATCH its fact's status, "
    "honestly, from what the sentence actually says -- never report ESTABLISHED for a "
    "sentence whose fact is ATTRIBUTED, DISPUTED or UNCERTAIN, even if the sentence "
    "happens to read that way; report the true status of the fact instead, and if the "
    "sentence and the fact's status genuinely conflict, report the fact's status and "
    "leave a note by simply choosing the more conservative one.\n"
    "\n"
    "Reply with ONE JSON object:\n"
    '{"claim_map": [{"sentence_id": "S001", "fact_ids": ["F60"], '
    '"entity_owner": null, "claim_subject_label": "", "scope": null, '
    '"qualifiers": "", "claim_status": "ESTABLISHED", "attribution_to": null, '
    '"temporal_relation": "NONE"}]}\n'
    "  entity_owner: ONLY when the cited fact names exactly one entity and the "
    "sentence is about that one entity -- its exact name, verbatim. Otherwise null.\n"
    "  claim_subject_label: optional, freeform, ungraded description of the "
    "sentence's subject when entity_owner does not apply.\n"
    "  scope: the cited fact's own scope word, only when exactly one fact is cited.\n"
    "  qualifiers: any exact date/version/number the sentence states, verbatim.\n"
    "  attribution_to: the speaker actually named in the sentence, when claim_status "
    "is ATTRIBUTED or DISPUTED; null otherwise.\n"
    "  temporal_relation: 'BEFORE', 'AFTER' or 'NONE' -- BEFORE/AFTER only when a "
    "fact below explicitly licenses that ordering.\n"
    "No prose outside the JSON."
)


def render_claim_mapper_prompt(sentences: dict, ledger: dict, allowed_fact_ids,
                               fact_status: dict) -> str:
    fact_status = fact_status or {}

    def _n(fid: str) -> int:
        return int(fid[1:]) if fid[1:].isdigit() else 0

    L = ["THE FROZEN ARTICLE, BY SENTENCE"]
    for sid, s in sentences.items():
        L.append("  %s: %s" % (sid, s))
    L.append("")
    L.append("FACTS AVAILABLE")
    for fid in sorted(allowed_fact_ids, key=_n):
        fact = ledger.get(fid) or {}
        ann = fact_status.get(fid) or {}
        status = ann.get("claim_status", ESTABLISHED)
        who = ann.get("attribution_to")
        header = "  %s [%s%s]" % (fid, status, (" - %s" % who) if who else "")
        L.append("%s: %s" % (header, fact.get("proposition", "")))
        if fact.get("entities"):
            L.append("      entities: %s" % fact["entities"])
        if fact.get("scope"):
            L.append("      scope: %s" % fact["scope"])
    return "\n".join(L)


def claim_map_article(provider, article_text: str, ledger: dict, allowed_fact_ids,
                      fact_status: dict | None = None) -> tuple:
    """Returns (claim_map, errors, retries, identity). ONE normal call; if the
    result is mechanically invalid (fails validate_claim_map, not just malformed
    JSON -- fast_lane_ask already retries malformed JSON on its own), ONE further
    metadata-only retry naming the exact validation errors. Never touches the
    article, never calls the Writer."""
    fact_status = fact_status or {}
    sentences = CP.label_sentences(article_text)
    prompt = render_claim_mapper_prompt(sentences, ledger, allowed_fact_ids,
                                        fact_status)
    obj, ident = fast_lane_ask(provider, CLAIM_MAPPER_SYSTEM, prompt, 4_000,
                               "FAST_LANE_CLAIM_MAPPER", "FAST_LANE_CLAIM_MAPPER_HOLD")
    claim_map = obj.get("claim_map") or []
    errs = validate_claim_map(claim_map, allowed_fact_ids, ledger, fact_status)
    if not errs:
        return claim_map, errs, 0, ident

    retry_prompt = (
        prompt + "\n\nYOUR PREVIOUS ANSWER HAD THESE MECHANICAL ERRORS. Return a "
        "corrected claim_map only -- same sentence_ids, no new ones, no article "
        "change (you were never shown one to change):\n"
        + "\n".join("  - %s" % e for e in errs))
    obj2, ident2 = fast_lane_ask(provider, CLAIM_MAPPER_SYSTEM, retry_prompt, 4_000,
                                 "FAST_LANE_CLAIM_MAPPER", "FAST_LANE_CLAIM_MAPPER_HOLD")
    claim_map = obj2.get("claim_map") or []
    errs = validate_claim_map(claim_map, allowed_fact_ids, ledger, fact_status)
    return claim_map, errs, 1, ident2


# ══════════════════════════════════════════════════════════════════════════════
# CLAIM_MAP -- mechanical validation only, never a semantic judge (that is
# Grounding's job). entity_owner is OPTIONAL: a fact with no named entities (a
# general/absence-of-data fact) or with several (a relational/multi-party fact) has
# no single canonical owner to check against, and the Writer is not required to
# invent one. When entity_owner IS given, it is checked by EXACT set membership only
# -- a descriptive phrase that is not itself one of the cited fact(s)' Ledger
# `entities` is refused, never treated as a new canonical entity by fuzzy or partial
# match. Descriptive labeling belongs in the separate, unvalidated
# `claim_subject_label` field, which grants zero factual permission.
#
# claim_status/attribution_to/temporal_relation, when `fact_status` is supplied,
# add ONE more deterministic check: the Writer's own SELF-REPORTED status for a
# sentence may never be stronger than the packet declared for the fact(s) it cites
# (ATTRIBUTED/DISPUTED/UNCERTAIN may never self-report as ESTABLISHED), and an
# explicit BEFORE/AFTER may never be self-reported for facts the packet marked
# temporal_permission NONE. This is still comparing metadata to metadata, not prose
# to evidence -- it catches the Writer's own declared status disagreeing with what
# it was given, not whether the actual sentence text honours that status. Grounding
# is what catches the sentence itself, exactly as it did on the real regression this
# guards against (see fast_lane_v1_attribution_test.py).
# ══════════════════════════════════════════════════════════════════════════════
def validate_claim_map(claim_map: list, allowed_fact_ids: set, ledger: dict,
                       fact_status: dict | None = None) -> list:
    fact_status = fact_status or {}
    errs = []
    for c in claim_map:
        sid = c.get("sentence_id", "?")
        fids = c.get("fact_ids") or []
        if not fids:
            errs.append("%s: claim_map entry names no fact_ids" % sid)
            continue
        cited_facts = []
        for fid in fids:
            if fid not in allowed_fact_ids:
                errs.append("%s: fact_id %r is not in the ARTICLE_PACKET's selected "
                            "evidence" % (sid, fid))
                continue
            fact = ledger.get(fid)
            if not fact:
                errs.append("%s: fact_id %r does not exist in the Ledger" % (sid, fid))
                continue
            cited_facts.append(fact)
        if not cited_facts:
            continue

        if fact_status:
            declared = [fact_status[fid]["claim_status"] for fid in fids
                       if fid in fact_status and "claim_status" in fact_status[fid]]
            reported = c.get("claim_status")
            if declared and reported == ESTABLISHED and any(
                    d in QUALIFIED_STATUSES for d in declared):
                errs.append(
                    "%s: claim_status ESTABLISHED is stronger than the packet's "
                    "declared status %s for %s -- ATTRIBUTED/DISPUTED/UNCERTAIN may "
                    "never self-report as ESTABLISHED" % (sid, declared, fids))
            temporal = c.get("temporal_relation")
            if temporal in ("BEFORE", "AFTER"):
                no_permission = [fid for fid in fids
                                 if fact_status.get(fid, {}).get(
                                     "temporal_permission", "NONE") == "NONE"]
                if no_permission:
                    errs.append(
                        "%s: temporal_relation %r is not licensed -- %s carry no "
                        "temporal_permission for it, and two separately dated facts "
                        "do not by themselves create a chronology"
                        % (sid, temporal, no_permission))

        entities = set()
        for f in cited_facts:
            entities |= set(f.get("entities") or [])

        owner = c.get("entity_owner")
        if owner:
            if not entities:
                errs.append(
                    "%s: entity_owner %r given, but the cited fact(s) carry no "
                    "canonical Ledger entities -- use null (a descriptive phrase "
                    "belongs in claim_subject_label, not entity_owner)" % (sid, owner))
            elif len(entities) == 1:
                canonical = next(iter(entities))
                if owner != canonical:
                    errs.append(
                        "%s: entity_owner %r is not the cited fact's exact canonical "
                        "entity %r -- a descriptive phrase is never silently treated "
                        "as a canonical entity_owner" % (sid, owner, canonical))
            elif owner not in entities:
                errs.append(
                    "%s: entity_owner %r is not one of the cited facts' several "
                    "canonical entities %s -- a multi-entity/relational claim must "
                    "not invent a single synthetic owner (use null)"
                    % (sid, owner, sorted(entities)))

        # scope is checked by exact match only when the cited fact(s) name exactly one
        # entity -- the same threshold as entity_owner above. A zero- or multi-entity
        # claim may use a descriptive scope label ("general", "joint", "relational")
        # that isn't the ledger's own WORLD/AUDITED_CORPUS word, so it is not checked.
        scope = c.get("scope")
        if scope and len(entities) == 1 and len(cited_facts) == 1:
            fact_scope = cited_facts[0].get("scope")
            if fact_scope and scope != fact_scope:
                errs.append("%s: scope %r does not match the Ledger's %r for %s"
                            % (sid, scope, fact_scope, fids[0]))

        quals = str(c.get("qualifiers") or "")
        if quals:
            hay = " ".join(((f.get("proposition") or "") + " "
                           + (f.get("support_span") or "")) for f in cited_facts).lower()
            for token in quals.replace(",", " ").split():
                t = token.strip(".:;()").lower()
                if len(t) >= 3 and any(ch.isdigit() for ch in t) and t not in hay:
                    errs.append(
                        "%s: qualifier %r is not a verbatim date/version/number the "
                        "cited fact(s) state" % (sid, token))
    return errs


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════
def load_run(run_dir: pathlib.Path) -> dict:
    def j(name):
        return json.loads((run_dir / name).read_text(encoding="utf-8"))
    ledger = j("LEDGER.json")
    worth = j("WORTH_AND_CANDIDATE.json")
    source_snapshot = j("SOURCE_SNAPSHOT.json")
    pack = j("RESEARCH_PACK.json")
    src_payload = source_snapshot.get("payload", source_snapshot)
    # RESEARCH_PACK.json is a persisted Artifact: {"stage", "payload": {...}, ...}, the
    # same shape as SOURCE_SNAPSHOT.json above. Passing the wrapper itself to
    # pack_material_block() (via ground_candidate) starves Grounding of everything but
    # the anchor -- ~102 chars of material instead of the ~20,370-char retained research
    # corpus -- because the wrapper has no top-level "sources" list for it to read.
    pack = pack.get("payload", pack)
    article_type = ((worth.get("story_candidate") or {}).get("article_type")
                    or "SHORT_NARRATIVE")
    return {
        "ledger": ledger,
        "source_text": src_payload.get("source_text", ""),
        "source_sha": src_payload.get("source_sha256", ""),
        "pack": pack,
        "article_type": article_type,
    }


def run_replay(run_dir: str, out_dir: str, model: str = DEFAULT_MODEL) -> dict:
    run_dir = pathlib.Path(run_dir)
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    retained = load_run(run_dir)
    ledger = retained["ledger"]
    provider = Provider(model=model)

    packet = build_article_packet()
    allowed = set(packet["load_bearing_facts"]) | set(packet["supporting_facts"])
    arch = build_synthetic_arch(packet, retained["article_type"])
    (out_dir / "ARTICLE_PACKET.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "ARCH.json").write_text(
        json.dumps(arch, indent=2, sort_keys=True), encoding="utf-8")

    report = {"stage_reached": "WRITER", "status": "HOLD"}

    article_text, negative_lineage, writer_packet_obj, ident = \
        fast_lane_write(provider, arch, ledger)
    (out_dir / "WRITER_OUTPUT.json").write_text(
        json.dumps({"article_text": article_text,
                   "negative_lineage": negative_lineage, "provider": ident},
                  indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "article.md").write_text(article_text, encoding="utf-8")
    report["word_count"] = len(article_text.split())

    claim_map, claim_errs, claim_retries, claim_ident = claim_map_article(
        provider, article_text, ledger, allowed)
    (out_dir / "CLAIM_MAP_VALIDATION.json").write_text(
        json.dumps({"errors": claim_errs, "claim_map": claim_map,
                   "retries": claim_retries}, indent=2), encoding="utf-8")
    if claim_errs:
        report.update(stage_reached="CLAIM_MAP", status="HOLD", errors=claim_errs,
                      claim_mapper_retries=claim_retries)
        return report

    draft_text = final_text = article_text
    cut_terms = CP.derive_cut_watch_terms(arch, ledger)
    safety = CP.safety_audit(draft_text, final_text, writer_packet_obj, arch, ledger,
                             cut_terms, negative_lineage=negative_lineage)
    (out_dir / "SAFETY_AUDIT.json").write_text(
        json.dumps(safety, indent=2, sort_keys=True, default=str), encoding="utf-8")
    if safety.get("status") != CP.PASS:
        report.update(stage_reached="SAFETY", status="HOLD",
                      blocking=safety.get("blocking"))
        return report

    grounding = CP.ground_candidate(provider, final_text, retained["source_text"],
                                    retained["source_sha"], retained["pack"],
                                    arch=arch, packet=writer_packet_obj)
    (out_dir / "GROUNDING_AUDIT.json").write_text(
        json.dumps(grounding, indent=2, sort_keys=True, default=str), encoding="utf-8")
    if grounding.get("status") != CP.PASS:
        report.update(stage_reached="GROUNDING", status="HOLD",
                      blocking=grounding.get("blocking"))
        return report

    fact_check = FCB.fact_check(final_text)
    (out_dir / "FACT_CHECK.json").write_text(
        json.dumps(fact_check, indent=2, sort_keys=True, default=str), encoding="utf-8")
    if fact_check.get("status") != "PASS":
        report.update(stage_reached="FACT_CHECK", status="HOLD",
                      blocking=fact_check.get("blocking_contradictions"))
        return report

    reader = CP.reader_gate(provider, final_text)
    (out_dir / "READER_AUDIT.json").write_text(
        json.dumps(reader, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report.update(stage_reached="READER", status=reader.get("status"),
                 dimensions=reader.get("dimensions"), held=reader.get("held"),
                 one_line=reader.get("one_line"))
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("out_dir")
    args = ap.parse_args()
    result = run_replay(args.run_dir, args.out_dir)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
