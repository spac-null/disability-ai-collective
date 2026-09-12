#!/usr/bin/env python3
"""Immigration candidate, replay 2: same Research/Ledger/Worth/Article Packet
evidence selection, regenerated ONLY from ARTICLE_PACKET -> ONE_WRITER, now with
explicit per-fact claim_status/attribution_to/temporal_permission so the Writer
contract fix (ATTRIBUTION_AND_STATUS_MUST_SURVIVE) actually has data to enforce."""
from __future__ import annotations

import hashlib
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
import immigration_packet as IP                            # noqa: E402

NONE_TEMPORAL = "NONE"

# One-time editorial judgment, made by hand while compiling this packet -- not an
# automated inference, and NOT derived from claim_type (2026-09-12 correction). Real
# Grounding findings on F13 and F16 showed the ORIGINAL version of this comment was
# wrong: it treated NEGATIVE_EXISTENCE as proof of ESTABLISHED, on the theory that a
# negative fact had already cleared the Ledger's strict evidentiary bar for negatives.
# claim_type is the FORM of a proposition; evidence status is a SEPARATE question of
# how the publication may narrate it, and both F13 ("there's no public information on
# how often deaf people are given interpreters") and F16 (interpreters "taken at their
# word", certification) are NEGATIVE_EXISTENCE in form but, in substance, Julia
# Métraux's own statement in an interview transcript -- exactly as attributable as any
# other ATTRIBUTION-typed fact from the same interview. Both are ATTRIBUTED below.
#
# DISPUTED marks a fact as one side of an ACTIVE two-sided disagreement (F41/F42 DHS's
# account vs F47/F54 the attorney's account). ESTABLISHED is reserved for facts whose
# evidentiary basis is the event itself, independently reported as fact (the
# deportation happening, a press conference occurring) -- not a source's spoken
# statement, whatever claim_type the Ledger gave it. Every temporal_permission is
# NONE: no selected fact states an explicit before/after relation to another, so none
# is licensed. required_qualifiers marks a fact whose Ledger support_span carries a
# hedge or disjunction the frozen `proposition` compressed away (F16's own proposition
# dropped "sometimes"; F01's kept its disjunction, but the Writer dropped it in prose)
# -- named here from the support_span, since the proposition alone no longer states it
# for F16.
FACT_STATUS = {
    "F30": {"claim_status": FL.ATTRIBUTED,
           "attribution_to": "a DHS spokesperson"},
    "F31": {"claim_status": FL.ATTRIBUTED,
           "attribution_to": "a DHS spokesperson"},
    "F32": {"claim_status": FL.ATTRIBUTED,
           "attribution_to": "Nikolas De Bremaeker"},
    "F33": {"claim_status": FL.ATTRIBUTED,
           "attribution_to": "Nikolas De Bremaeker"},
    "F45": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F46": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F47": {"claim_status": FL.ATTRIBUTED,
           "attribution_to": "Nikolas De Bremaeker"},
    "F54": {"claim_status": FL.DISPUTED,
           "attribution_to": "Nikolas De Bremaeker"},
    "F41": {"claim_status": FL.DISPUTED,
           "attribution_to": "a DHS spokesperson"},
    "F42": {"claim_status": FL.DISPUTED,
           "attribution_to": "a DHS spokesperson"},
    "F49": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Eric Swalwell"},
    "F55": {"claim_status": FL.ATTRIBUTED,
           "attribution_to": "Nikolas De Bremaeker"},
    "F35": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "EVENT_LA_FRIDAY", "event_date": "Friday",
           "event_location": "Los Angeles"},
    "F36": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Tony Thurmond",
           "event_id": "EVENT_LA_FRIDAY", "event_date": "Friday",
           "event_location": "Los Angeles"},
    "F04": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux"},
    "F15": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Hands United"},
    "F16": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux",
           "required_qualifiers": ["sometimes (support_span: 'leads to people "
                                   "sometimes getting very poor-quality "
                                   "interpreters')"]},
    "F19": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux"},
    "F20": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux"},
    "F13": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux"},
    "F01": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux",
           "required_qualifiers": ["disjunction: 'had no interpreters, or "
                                   "interpretation inadequate to their needs' -- "
                                   "keep both branches, do not narrow to one"]},
    "F08": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F10": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F11": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F58": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F59": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Julia Métraux"},
    "F17": {"claim_status": FL.ATTRIBUTED,
           "attribution_to": "the president of the National Hispanic Latino "
                             "Association of the Deaf"},
    "F38": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Eric Swalwell",
           "event_id": "EVENT_HAYWARD_MONDAY", "event_date": "Monday",
           "event_location": "Hayward"},
    "F37": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "EVENT_HAYWARD_MONDAY", "event_date": "Monday",
           "event_location": "Hayward"},
    "F48": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "EVENT_HAYWARD_MONDAY", "event_date": "Monday",
           "event_location": "Hayward"},
}
for ann in FACT_STATUS.values():
    ann.setdefault("temporal_permission", NONE_TEMPORAL)


def main(run_dir: str, model: str = DEFAULT_MODEL) -> dict:
    run_dir = pathlib.Path(run_dir)
    ledger_wrapper = json.loads((run_dir / "LEDGER.json").read_text(encoding="utf-8"))
    ledger = ledger_wrapper["ledger"]
    pack = json.loads((run_dir / "RESEARCH_PACK.json").read_text(encoding="utf-8"))

    provider = Provider(model=model)
    packet = IP.build_article_packet()
    allowed = (set(packet["load_bearing_facts"]) | set(packet["story_bearing_facts"])
              | set(packet["supporting_facts"]))
    assert allowed == set(FACT_STATUS), \
        "FACT_STATUS must annotate exactly the packet's selected facts: missing %s, extra %s" % (
            sorted(allowed - set(FACT_STATUS)), sorted(set(FACT_STATUS) - allowed))
    arch = IP.build_synthetic_arch(packet, "SHORT_NARRATIVE")
    (run_dir / "ARTICLE_PACKET.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "ARCH.json").write_text(
        json.dumps(arch, indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "FACT_STATUS.json").write_text(
        json.dumps(FACT_STATUS, indent=2, sort_keys=True), encoding="utf-8")

    report = {"stage_reached": "WRITER", "status": "HOLD"}

    article_text, claim_map, negative_lineage, writer_packet_obj, ident = \
        FL.fast_lane_write(provider, arch, ledger, fact_status=FACT_STATUS)
    (run_dir / "WRITER_OUTPUT.json").write_text(
        json.dumps({"article_text": article_text, "claim_map": claim_map,
                   "negative_lineage": negative_lineage, "provider": ident},
                  indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "article.md").write_text(article_text, encoding="utf-8")
    report["word_count"] = len(article_text.split())
    report["article_sha256"] = hashlib.sha256(article_text.encode("utf-8")).hexdigest()

    claim_errs = FL.validate_claim_map(claim_map, allowed, ledger,
                                       fact_status=FACT_STATUS)
    (run_dir / "CLAIM_MAP_VALIDATION.json").write_text(
        json.dumps({"errors": claim_errs, "claim_map": claim_map}, indent=2),
        encoding="utf-8")
    if claim_errs:
        report.update(stage_reached="CLAIM_MAP", status="HOLD", errors=claim_errs)
        return report
    report["claim_map"] = "PASS"

    draft_text = final_text = article_text
    cut_terms = CP.derive_cut_watch_terms(arch, ledger)
    safety = CP.safety_audit(draft_text, final_text, writer_packet_obj, arch, ledger,
                             cut_terms, negative_lineage=negative_lineage)
    (run_dir / "SAFETY_AUDIT.json").write_text(
        json.dumps(safety, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["safety"] = safety.get("status")
    if safety.get("status") != CP.PASS:
        report.update(stage_reached="SAFETY", status="HOLD",
                      blocking=safety.get("blocking"))
        return report

    source_text = "\n\n".join("[%s] %s" % (s["source_id"], s["text"])
                              for s in pack["sources"])
    source_sha = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    grounding = CP.ground_candidate(provider, final_text, source_text, source_sha,
                                    pack, arch=arch, packet=writer_packet_obj)
    (run_dir / "GROUNDING_AUDIT.json").write_text(
        json.dumps(grounding, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["grounding"] = grounding.get("status")
    if grounding.get("status") != CP.PASS:
        report.update(stage_reached="GROUNDING", status="HOLD",
                      blocking=grounding.get("blocking"))
        return report

    fact_check = FCB.fact_check(final_text)
    (run_dir / "FACT_CHECK.json").write_text(
        json.dumps(fact_check, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["fact_check"] = fact_check.get("status")
    if fact_check.get("status") != "PASS":
        report.update(stage_reached="FACT_CHECK", status="HOLD",
                      blocking=fact_check.get("blocking_contradictions"))
        return report

    reader = CP.reader_gate(provider, final_text)
    (run_dir / "READER_AUDIT.json").write_text(
        json.dumps(reader, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["reader"] = reader.get("status")
    report.update(stage_reached="READER", status=reader.get("status"),
                 dimensions=reader.get("dimensions"), held=reader.get("held"),
                 one_line=reader.get("one_line"))
    return report


if __name__ == "__main__":
    result = main(sys.argv[1])
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
