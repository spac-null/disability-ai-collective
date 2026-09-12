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
    + "\n\nADDITIONALLY, return one more field in the same JSON object:\n"
      '  "claim_map": [{"sentence_id": "S001", "fact_ids": ["F60"], '
      '"entity_owner": "TD Snap", "claim_subject_label": "", "scope": "WORLD", '
      '"qualifiers": "v1.40.2, 2026-08-17"}]\n'
      "For every factual sentence in the article (a sentence naming a specific "
      "product, action, date, version or number), give its sentence_id (matching the "
      "numbering you already assign for negative_lineage) and the fact_id(s) from the "
      "packet it rests on.\n"
      "  entity_owner is OPTIONAL. Give it ONLY when the cited fact names exactly one "
      "entity and the sentence is about that one entity -- and then it must be that "
      "entity's exact name, verbatim, not a paraphrase or a description of what the "
      "fact is about. If the cited fact names no entity, or several, or the sentence "
      "is relational, leave entity_owner null (do not invent a descriptive stand-in).\n"
      "  claim_subject_label is OPTIONAL, freeform, and never checked against the "
      "Ledger -- use it for a short descriptive label of what the sentence is about "
      "when entity_owner does not apply (e.g. 'US interpreter certification "
      "requirements'). It grants no factual permission.\n"
      "  scope: the scope word from the cited fact, when there is exactly one cited "
      "fact; omit it for a sentence resting on more than one fact.\n"
      "  qualifiers: any exact date/version/number the sentence states, verbatim.\n"
      "A purely transitional sentence asserting no fact-specific claim may be omitted "
      "from claim_map. Use no fact_id that was not given to you above."
)


def fast_lane_write(provider, arch: dict, ledger: dict) -> tuple:
    """Returns (article_text, claim_map, negative_lineage, packet, identity)."""
    packet, rendered = CP.writer_packet(arch, ledger, cut_prohibitions=None)
    obj, ident = CP._ask(provider, FAST_LANE_WRITER_SYSTEM, rendered, 6_000,
                         "FAST_LANE_WRITER", "FAST_LANE_WRITER_HOLD")
    article = CP._clean_article(obj.get("article", ""))
    if len((article or "").split()) < CP.WRITER_MIN_WORDS:
        raise CP.CompositionHold("FAST_LANE_WRITER", "FAST_LANE_WRITER_HOLD",
                                 ["writer reply has no real article body"])
    return article, obj.get("claim_map") or [], obj.get("negative_lineage") or [], \
        packet, ident


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
# ══════════════════════════════════════════════════════════════════════════════
def validate_claim_map(claim_map: list, allowed_fact_ids: set, ledger: dict) -> list:
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

    article_text, claim_map, negative_lineage, writer_packet_obj, ident = \
        fast_lane_write(provider, arch, ledger)
    (out_dir / "WRITER_OUTPUT.json").write_text(
        json.dumps({"article_text": article_text, "claim_map": claim_map,
                   "negative_lineage": negative_lineage, "provider": ident},
                  indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "article.md").write_text(article_text, encoding="utf-8")
    report["word_count"] = len(article_text.split())

    claim_errs = validate_claim_map(claim_map, allowed, ledger)
    (out_dir / "CLAIM_MAP_VALIDATION.json").write_text(
        json.dumps({"errors": claim_errs, "claim_map": claim_map}, indent=2),
        encoding="utf-8")
    if claim_errs:
        report.update(stage_reached="CLAIM_MAP", status="HOLD", errors=claim_errs)
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
