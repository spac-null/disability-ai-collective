#!/usr/bin/env python3
"""Fresh natural Fast Lane candidate: 'the signature and the record' -- Article Packet
and synthetic arch, built from the frozen immigration Ledger. Reuses fast_lane_v1's
generic ONE_WRITER (with CLAIM_MAP + IMPLEMENTATION_DETAILS_REQUIRE_DIRECT_LICENSE),
validate_claim_map, and the unmodified canonical Safety/Grounding/Fact-Check/Reader
functions -- exactly the same tail as the TD Snap replay."""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import composition_factual_bridge as FCB                 # noqa: E402
from new_engine_v1 import composition as CP               # noqa: E402
from new_engine_v1.provider import Provider, DEFAULT_MODEL  # noqa: E402

import fast_lane_v1 as FL                                 # noqa: E402


def build_article_packet() -> dict:
    return {
        "question": (
            "What does it mean for consent and comprehension to be recorded as "
            "complete in a system that cannot detect when neither one actually "
            "happened?"
        ),
        "primary_carrier": {
            "carrier": "the document Lesly Rodriguez Gutierrez signed at the San "
                      "Francisco check-in",
            "evidence_ids": ["F47", "F54"],
        },
        "story_bearing_facts": ["F30", "F31", "F32", "F33", "F45", "F46", "F47",
                                "F54", "F41", "F42", "F49", "F55", "F35", "F36"],
        "load_bearing_facts": ["F04", "F15", "F16", "F19", "F20", "F13"],
        "supporting_facts": ["F01", "F08", "F10", "F11", "F58", "F59", "F17", "F38",
                            "F37", "F48"],
        "forbidden_claims": [
            "claim DHS or ICE acted in bad faith or intended to harm Joseph beyond "
            "what the Ledger records as their own stated position -- present the "
            "dispute between DHS's account and the attorney's account, do not "
            "adjudicate it",
            "claim any specific interpreter's performance was incompetent -- the "
            "Ledger licenses only that no certification process exists for "
            "non-ASL sign languages, not that a specific interpretation failed",
            "state or imply any specific medical harm to Joseph (infection, "
            "meningitis, permanent hearing loss) -- the Ledger does not license "
            "a medical-risk claim",
            "connect Emilio's case and the Rodriguez Gutierrez/Joseph case as "
            "legally or procedurally linked -- they are two separate documented "
            "instances of the same pattern, not one event",
            "speculate about any official's political motivations, including any "
            "campaign for office",
            "state a precise number of deaf people affected beyond 'more than "
            "100', which is the figure the Ledger licenses",
            "begin with 'Mother Jones reported', 'the article says', 'reporting "
            "found', or similar source-first framing",
            "turn this into a general immigration-policy or ICE-enforcement "
            "story that is not centered on communication/comprehension access",
        ],
        "ending_return": (
            "Return to the signed document and what it recorded as complete -- "
            "not a conclusion about intent, the concrete fact that the file was "
            "closed before the record and the event agreed."
        ),
    }


def build_synthetic_arch(packet: dict, article_type: str) -> dict:
    load = packet["load_bearing_facts"]
    story = packet["story_bearing_facts"]
    support = packet["supporting_facts"]
    beats = [
        {"beat_id": "B1",
         "happens": "Lesly Rodriguez Gutierrez and her two children go to a "
                    "routine immigration check-in in San Francisco. She had "
                    "been under a supervisory order and had a removal order "
                    "from 2024; she believed this was a periodic check-in",
         "concrete_carrier": "the routine check-in",
         "facts_allowed": ["F30", "F31", "F32", "F33"],
         "concept_introduced": "", "why_reader_wants_next":
             "what happens at the check-in is not yet known",
         "must_not_say_yet": "the deportation itself"},
        {"beat_id": "B2",
         "happens": "The family is deported to Colombia; her son Joseph, who is "
                    "deaf, is separated from his hearing devices, and her lawyer "
                    "says she was pressured to sign a document in a language "
                    "she did not understand",
         "concrete_carrier": "the document she signed",
         "facts_allowed": ["F45", "F46", "F47", "F54"],
         "concept_introduced": "", "why_reader_wants_next":
             "what the government's own account of this says is not yet known",
         "must_not_say_yet": "DHS's account"},
        {"beat_id": "B3",
         "happens": "DHS states she chose to be removed with her children; her "
                    "attorney disputes that account. Superintendent Tony "
                    "Thurmond and Rep. Eric Swalwell take up the case publicly",
         "concrete_carrier": "the dispute over what the signature meant",
         "facts_allowed": ["F41", "F42", "F35", "F36"],
         "concept_introduced": "", "why_reader_wants_next":
             "why this could happen at all is not yet known",
         "must_not_say_yet": "the systemic facts"},
        {"beat_id": "B4",
         "happens": "Federal law requires an interpreter on request, but the "
                    "United States certifies interpreter competence only for "
                    "American Sign Language, not the languages Joseph's family "
                    "or Emilio -- a Venezuelan deaf migrant deported without an "
                    "interpreter under a similar pattern -- would need; the "
                    "office meant to handle complaints about this has been cut "
                    "from about 150 staff to two, and there is no public count "
                    "of how often this happens",
         "concrete_carrier": "the office with two employees left",
         "facts_allowed": ["F04", "F15", "F16", "F19", "F20", "F13", "F01",
                          "F08", "F10", "F11", "F58", "F59", "F17"],
         "concept_introduced": "", "why_reader_wants_next": "",
         "must_not_say_yet": ""},
        {"beat_id": "B5",
         "happens": "Swalwell's staff fly to Colombia and return Joseph's "
                    "hearing devices; he says of it that the child's sound "
                    "was returned, and asks what has happened to the country's "
                    "soul",
         "concrete_carrier": "the hearing devices, returned",
         "facts_allowed": ["F49", "F55", "F38", "F37", "F48"],
         "concept_introduced": "", "why_reader_wants_next": "",
         "must_not_say_yet": ""},
        {"beat_id": "B6",
         "happens": "The signed document remains what the federal record calls "
                    "a completed, lawful process",
         "concrete_carrier": "the signed document",
         "facts_allowed": ["F47", "F54"],
         "concept_introduced": "", "why_reader_wants_next": "",
         "must_not_say_yet": ""},
    ]
    prohibitions = []
    for claim in packet["forbidden_claims"]:
        prohibitions.append("Do not " + claim + ".")
    prohibitions += FL.GENERAL_CONTRACT_PROHIBITIONS
    return {
        "article_type": article_type,
        "story_spine": "A signature on an immigration document is recorded as "
                       "consent and comprehension in a system with no way to "
                       "detect that neither one occurred.",
        "opening_object_or_event": "The document Lesly Rodriguez Gutierrez "
                                   "signed at a routine immigration check-in in "
                                   "San Francisco.",
        "reader_initial_state": "",
        "beats": beats,
        "turn": "",
        "crip_turn": packet["question"],
        "ending_move": packet["ending_return"],
        "use_facts": list(load) + list(story) + list(support),
        "use_quotes": [],
        "definitions": {},
        "prohibitions": prohibitions,
        "cut_evidence": [],
        "final_lens": {},
    }


def main(run_dir: str, model: str = DEFAULT_MODEL) -> dict:
    run_dir = pathlib.Path(run_dir)
    ledger_wrapper = json.loads((run_dir / "LEDGER.json").read_text(encoding="utf-8"))
    ledger = ledger_wrapper["ledger"]
    pack = json.loads((run_dir / "RESEARCH_PACK.json").read_text(encoding="utf-8"))
    worth = json.loads((run_dir / "WORTH.json").read_text(encoding="utf-8"))

    provider = Provider(model=model)
    packet = build_article_packet()
    allowed = (set(packet["load_bearing_facts"]) | set(packet["story_bearing_facts"])
              | set(packet["supporting_facts"]))
    arch = build_synthetic_arch(packet, "SHORT_NARRATIVE")
    (run_dir / "ARTICLE_PACKET.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "ARCH.json").write_text(
        json.dumps(arch, indent=2, sort_keys=True), encoding="utf-8")

    report = {"stage_reached": "WRITER", "status": "HOLD"}

    article_text, claim_map, negative_lineage, writer_packet_obj, ident = \
        FL.fast_lane_write(provider, arch, ledger)
    (run_dir / "WRITER_OUTPUT.json").write_text(
        json.dumps({"article_text": article_text, "claim_map": claim_map,
                   "negative_lineage": negative_lineage, "provider": ident},
                  indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "article.md").write_text(article_text, encoding="utf-8")
    report["word_count"] = len(article_text.split())

    claim_errs = FL.validate_claim_map(claim_map, allowed, ledger)
    (run_dir / "CLAIM_MAP_VALIDATION.json").write_text(
        json.dumps({"errors": claim_errs, "claim_map": claim_map}, indent=2),
        encoding="utf-8")
    if claim_errs:
        report.update(stage_reached="CLAIM_MAP", status="HOLD", errors=claim_errs)
        return report

    draft_text = final_text = article_text
    cut_terms = CP.derive_cut_watch_terms(arch, ledger)
    safety = CP.safety_audit(draft_text, final_text, writer_packet_obj, arch, ledger,
                             cut_terms, negative_lineage=negative_lineage)
    (run_dir / "SAFETY_AUDIT.json").write_text(
        json.dumps(safety, indent=2, sort_keys=True, default=str), encoding="utf-8")
    if safety.get("status") != CP.PASS:
        report.update(stage_reached="SAFETY", status="HOLD",
                      blocking=safety.get("blocking"))
        return report

    source_text = "\n\n".join("[%s] %s" % (s["source_id"], s["text"])
                              for s in pack["sources"])
    source_sha = __import__("hashlib").sha256(source_text.encode("utf-8")).hexdigest()
    grounding = CP.ground_candidate(provider, final_text, source_text, source_sha,
                                    pack, arch=arch, packet=writer_packet_obj)
    (run_dir / "GROUNDING_AUDIT.json").write_text(
        json.dumps(grounding, indent=2, sort_keys=True, default=str), encoding="utf-8")
    if grounding.get("status") != CP.PASS:
        report.update(stage_reached="GROUNDING", status="HOLD",
                      blocking=grounding.get("blocking"))
        return report

    fact_check = FCB.fact_check(final_text)
    (run_dir / "FACT_CHECK.json").write_text(
        json.dumps(fact_check, indent=2, sort_keys=True, default=str), encoding="utf-8")
    if fact_check.get("status") != "PASS":
        report.update(stage_reached="FACT_CHECK", status="HOLD",
                      blocking=fact_check.get("blocking_contradictions"))
        return report

    reader = CP.reader_gate(provider, final_text)
    (run_dir / "READER_AUDIT.json").write_text(
        json.dumps(reader, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report.update(stage_reached="READER", status=reader.get("status"),
                 dimensions=reader.get("dimensions"), held=reader.get("held"),
                 one_line=reader.get("one_line"))
    return report


if __name__ == "__main__":
    result = main(sys.argv[1])
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
