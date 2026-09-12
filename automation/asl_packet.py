#!/usr/bin/env python3
"""ASL/White House lawsuit candidate: Article Packet, synthetic arch, and
fact_status, built with explicit CARRIER_COHESION -- every selected fact traces to
ONE case (NAD v. White House), no stapled secondary thread."""
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


def build_article_packet() -> dict:
    return {
        "question": (
            "What does it mean when a government's own defense against providing "
            "an interpreter is that the interpreter would be seen?"
        ),
        "primary_carrier": {
            "carrier": "the Justice Department's argument that a visible ASL "
                      "interpreter would intrude on the president's image",
            "evidence_ids": ["F72", "F53"],
        },
        # CARRIER_COHESION: every fact below is either (a) part of the single
        # lawsuit/injunction record itself, or (b) explicitly cited BY these same
        # sources as this dispute's own history (NAD's prior suit against the same
        # defendant over the same issue) -- not a separately-reported, merely
        # thematically-similar thread.
        "story_bearing_facts": [
            "F45", "F32", "F46", "F41", "F53", "F72", "F79", "F80", "F81",
            "F87", "F37", "F38", "F49", "F36", "F88", "F55", "F42", "F43", "F82",
            "F70", "F34", "F44", "F69",
        ],
        "load_bearing_facts": ["F09", "F89", "F04", "F63"],
        "supporting_facts": [
            "F01", "F15", "F16", "F17", "F19", "F21", "F22",
            "F28", "F83", "F84", "F85", "F86", "F91", "F92",
        ],
        "forbidden_claims": [
            "state or imply that the appeal has been decided or that the D.C. "
            "Circuit has ruled -- the Ledger licenses only that DOJ appealed and "
            "the case is ongoing",
            "claim the White House has fully complied or fully defied the "
            "injunction -- the Ledger licenses only that it has 'started "
            "including ASL interpreters at some events' while disputing the "
            "injunction's scope",
            "assert a motive for the original January 2025 removal beyond what "
            "the Ledger states (the DEIA executive order and the removal are "
            "chronologically adjacent, not stated as cause and effect by any "
            "source)",
            "state a precise number of ASL users beyond the ranges the Ledger "
            "gives ('several hundred thousand' primary users, 'more than 48 "
            "million' deaf or hard of hearing people overall) -- do not merge "
            "or round these two different figures into one",
            "treat the plaintiffs' personal circumstances (Ford's and Bonn's "
            "stated concerns) as anything but what the complaint itself alleges",
            "begin with 'the lawsuit says', 'NPR reported', or similar "
            "source-first framing",
            "editorialize about whether the administration's image-control "
            "argument was made in good or bad faith -- report the argument and "
            "the judge's rejection of it, not a motive behind either",
        ],
        "ending_return": (
            "Return to the interpreter's place beside the podium -- required to "
            "be visible under the order, proposed to be moved to a separate "
            "channel by the government -- without resolving whether that "
            "argument succeeds; the appeal is still open."
        ),
    }


def build_synthetic_arch(packet: dict, article_type: str) -> dict:
    load = packet["load_bearing_facts"]
    story = packet["story_bearing_facts"]
    support = packet["supporting_facts"]
    beats = [
        {"beat_id": "B1",
         "happens": "The White House stopped using live ASL interpreters at "
                    "briefings and other public events when the president began "
                    "his second term in January 2025, the same day he signed an "
                    "executive order eliminating federal DEIA programs",
         "concrete_carrier": "the interpreter, no longer at the podium",
         "facts_allowed": ["F45", "F32"],
         "concept_introduced": "", "why_reader_wants_next":
             "who objects to this, and on what ground, is not yet known",
         "must_not_say_yet": "the lawsuit"},
        {"beat_id": "B2",
         "happens": "The National Association of the Deaf and two deaf men sue "
                    "in May, saying the White House is violating disability-"
                    "rights law by broadcasting briefings deaf Americans "
                    "cannot follow",
         "concrete_carrier": "the lawsuit",
         "facts_allowed": ["F46", "F01", "F09", "F89", "F04", "F63", "F15", "F16", "F17",
                          "F19", "F21", "F22"],
         "concept_introduced": "", "why_reader_wants_next":
             "what a court does with this is not yet known",
         "must_not_say_yet": "the ruling"},
        {"beat_id": "B3",
         "happens": "In November, Judge Amir Ali orders the White House to "
                    "provide a qualified, visible ASL interpreter at every "
                    "publicly announced presidential or press-secretary "
                    "briefing, rejecting closed captioning as an adequate "
                    "substitute, and sets Nov. 7 as the deadline for a "
                    "compliance status report",
         "concrete_carrier": "the judge's order that interpretation be visible",
         "facts_allowed": ["F41", "F53", "F55", "F42", "F43"],
         "concept_introduced": "", "why_reader_wants_next":
             "how the government defends its prior refusal is not yet known",
         "must_not_say_yet": "the government's own stated reason"},
        {"beat_id": "B4",
         "happens": "In its own June filing, the Justice Department had argued "
                    "that a visible interpreter would intrude on the president's "
                    "control of his own image; Ali's order rejects that "
                    "reasoning directly, writing that an interest in an image "
                    "free of accessibility is not a defense the law allows",
         "concrete_carrier": "the president's image, argued over in court",
         "facts_allowed": ["F72", "F79", "F80", "F81"],
         "concept_introduced": "", "why_reader_wants_next":
             "what happens after the order is not yet known",
         "must_not_say_yet": "the appeal and the workaround"},
        {"beat_id": "B5",
         "happens": "The Justice Department appeals, disputes which events "
                    "count as a 'press briefing,' cites its vendor's 24-hour "
                    "notice requirement, and proposes routing interpretation "
                    "through a separate channel instead of the main broadcast; "
                    "the White House has begun including interpreters at some "
                    "events while the case continues",
         "concrete_carrier": "the separate channel, proposed",
         "facts_allowed": ["F87", "F37", "F38", "F49", "F36", "F88", "F82", "F70",
                          "F34", "F44", "F69"],
         "concept_introduced": "", "why_reader_wants_next": "",
         "must_not_say_yet": ""},
        {"beat_id": "B6",
         "happens": "This is not the first time the same organization has taken "
                    "the same White House to court over this exact question -- "
                    "a 2020 order produced interpreters through the end of the "
                    "pandemic, and the Biden administration made the arrangement "
                    "permanent in 2021, before it was removed again in January "
                    "2025",
         "concrete_carrier": "the arrangement, made and unmade twice",
         "facts_allowed": ["F28", "F83", "F84", "F85", "F86", "F91", "F92"],
         "concept_introduced": "", "why_reader_wants_next": "",
         "must_not_say_yet": ""},
    ]
    prohibitions = []
    for claim in packet["forbidden_claims"]:
        prohibitions.append("Do not " + claim + ".")
    prohibitions += FL.GENERAL_CONTRACT_PROHIBITIONS
    return {
        "article_type": article_type,
        "story_spine": "The government's own legal defense treats a visible ASL "
                       "interpreter as an intrusion on the president's image, "
                       "not a service that could simply be provided elsewhere.",
        "opening_object_or_event": "The interpreter who is no longer standing at "
                                   "White House briefings.",
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


FACT_STATUS = {
    # B1
    "F45": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "REMOVAL_JAN2025"},
    "F32": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "REMOVAL_JAN2025", "temporal_permission": "NONE"},
    # B2
    "F46": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "LAWSUIT_MAY2025"},
    "F01": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "LAWSUIT_MAY2025"},
    "F09": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "LAWSUIT_MAY2025"},
    "F89": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F04": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F63": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the plaintiffs"},
    # F15/F19 corrected 2026-09-12 (copy-desk pass): NPR (S0) states Ford's and
    # Bonn's basic identity (age, residence) in its own narration, not as "the
    # complaint says" -- ESTABLISHED matches the source's own framing, and the
    # article already states these plainly with no attribution, which is
    # therefore accurate rather than a dropped-attribution defect.
    "F15": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F16": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the complaint"},
    "F17": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the complaint"},
    "F19": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F21": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the complaint"},
    "F22": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the complaint"},
    # B3
    # F41's compliance deadline: mechanically resolving "last Friday" against S1's
    # own 2025-11-05 publication date gives 2025-10-31 -- but that PRECEDES the
    # Nov. 4 injunction it supposedly reports compliance on, an impossible order.
    # Verified instead directly against the primary court order (S4, Document 29,
    # fetched from CourtListener/RECAP and read in full): "These defendants shall
    # file a status report by November 7, 2025, that apprises the court of their
    # compliance with this order." That is the actual, authoritative deadline;
    # NPR's "last Friday" phrasing (S1) is not the source of resolution here --
    # this is why RELATIVE_DATE_RESOLUTION's own weekday arithmetic is NOT used
    # for this fact: the correct answer required primary-document verification,
    # which is more authoritative than any relative-phrase computation.
    "F41": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "INJUNCTION_NOV2025", "event_date": "Nov. 4",
           "temporal_permission": "NONE",
           "source_relative_phrase": "last Friday", "source_context_date": None,
           "resolved_absolute_date": "2025-11-07", "resolution_status": "EXACT",
           "resolution_method": "verified directly against primary court order "
                                "S4 (Document 29), not NPR's relative phrasing"},
    "F53": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "INJUNCTION_NOV2025"},
    # F55/F42/F43 corrected 2026-09-12 against the primary court order (S4,
    # Document 29, verified in full): F55's first clause is "reasonable
    # accommodations" (plural), not "accommodation" -- the second, "hardly be
    # called an accommodation at all", is correctly singular in the primary text
    # and unchanged. F42/F43 needed only a comma restored ("and, in recent
    # years," not "and in recent years").
    "F55": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Judge Amir Ali",
           "quote_permission": "DIRECT_VERBATIM",
           "quote_text": "The defendants correctly note that the plaintiffs are "
                         "entitled only to reasonable accommodations. But it is "
                         "not reasonable -- indeed it can hardly be called an "
                         "accommodation at all -- to transcribe press briefings "
                         "into a language that Ford and many NAD members do not "
                         "know",
           "quote_attribution": "Judge Amir Ali"},
    "F42": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Judge Amir Ali",
           "quote_permission": "DIRECT_VERBATIM",
           "quote_text": "White House press briefings engage the American "
                         "people on important issues affecting their daily "
                         "lives -- in recent months, war, the economy, and "
                         "healthcare, and, in recent years, a global pandemic",
           "quote_attribution": "Judge Amir Ali"},
    "F43": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Judge Amir Ali",
           "quote_permission": "DIRECT_VERBATIM",
           "quote_text": "The exclusion of deaf Americans from that "
                         "programming, in addition to likely violating the "
                         "Rehabilitation Act, is clear and present harm that "
                         "the court cannot meaningfully remedy after the fact",
           "quote_attribution": "Judge Amir Ali"},
    # B4
    "F72": {"claim_status": FL.ATTRIBUTED,
           "attribution_to": "U.S. Department of Justice attorneys",
           "event_id": "DOJ_JUNE_FILING",
           "quote_permission": "DIRECT_VERBATIM",
           "quote_text": "would severely intrude on the President's "
                         "prerogative to control the image he presents to the "
                         "public",
           "quote_attribution": "U.S. Department of Justice attorneys"},
    "F79": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "INJUNCTION_NOV2025"},
    "F80": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Judge Amir Ali",
           "quote_permission": "DIRECT_VERBATIM",
           "quote_text": "To the extent the defendants argue that they prefer "
                         "to act free from association with accessibility for "
                         "people with disabilities, their gripe is with "
                         "Congress and the Rehabilitation Act itself",
           "quote_attribution": "Judge Amir Ali"},
    "F81": {"claim_status": FL.ATTRIBUTED, "attribution_to": "Judge Amir Ali",
           "quote_permission": "DIRECT_VERBATIM",
           # Corrected against the primary court opinion (National Association
           # of the Deaf v. Trump, D.D.C., Document 29, filed 2025-11-04): the
           # Disability Scoop rendering this was originally drawn from dropped
           # "For the purposes of this action," and singularized "reasonable
           # accommodations". S4 in RESEARCH_PACK.json carries the verified span.
           "quote_text": "For the purposes of this action, the defendants "
                         "concede that section 504(a) applies to them, and "
                         "wanting to have an 'image' free from its "
                         "requirements is not a sound basis for declining to "
                         "provide reasonable accommodations",
           "quote_attribution": "Judge Amir Ali"},
    # B5
    "F87": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the department",
           "event_id": "DOJ_NOV_FILING"},
    "F37": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the DOJ",
           "event_id": "DOJ_NOV_FILING"},
    "F38": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the DOJ",
           "event_id": "DOJ_NOV_FILING"},
    "F49": {"claim_status": FL.DISPUTED, "attribution_to": "the NAD",
           "event_id": "NAD_DEC_FILING"},
    "F36": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the DOJ",
           "event_id": "DOJ_NOV_FILING"},
    "F88": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the department",
           "event_id": "DOJ_NOV_FILING"},
    "F82": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F70": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F34": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F44": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F69": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    # B6 -- 2020/2021 history
    "F28": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "SUIT_2020"},
    "F83": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "SUIT_2020"},
    "F84": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "SUIT_2020"},
    "F85": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "SUIT_2020"},
    "F86": {"claim_status": FL.ESTABLISHED, "attribution_to": None,
           "event_id": "REINSTATEMENT_2021"},
    "F91": {"claim_status": FL.ESTABLISHED, "attribution_to": None},
    "F92": {"claim_status": FL.ATTRIBUTED, "attribution_to": "the NAD",
           "event_id": "REINSTATEMENT_2021"},
}
for _ann in FACT_STATUS.values():
    _ann.setdefault("temporal_permission", "NONE")


def main(run_dir: str, model: str = DEFAULT_MODEL) -> dict:
    run_dir = pathlib.Path(run_dir)
    ledger_wrapper = json.loads((run_dir / "LEDGER.json").read_text(encoding="utf-8"))
    ledger = ledger_wrapper["ledger"]
    pack = json.loads((run_dir / "RESEARCH_PACK.json").read_text(encoding="utf-8"))

    provider = Provider(model=model)
    packet = build_article_packet()
    allowed = (set(packet["load_bearing_facts"]) | set(packet["story_bearing_facts"])
              | set(packet["supporting_facts"]))
    missing = allowed - set(FACT_STATUS)
    extra = set(FACT_STATUS) - allowed
    assert not missing and not extra, ("FACT_STATUS/packet mismatch",
                                       sorted(missing), sorted(extra))
    arch = build_synthetic_arch(packet, "SHORT_NARRATIVE")
    (run_dir / "ARTICLE_PACKET.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "ARCH.json").write_text(
        json.dumps(arch, indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "FACT_STATUS.json").write_text(
        json.dumps(FACT_STATUS, indent=2, sort_keys=True), encoding="utf-8")

    report = {"stage_reached": "WRITER", "status": "HOLD"}

    article_text, negative_lineage, writer_packet_obj, ident = FL.fast_lane_write(
        provider, arch, ledger, fact_status=FACT_STATUS)
    (run_dir / "WRITER_OUTPUT.json").write_text(
        json.dumps({"article_text": article_text,
                   "negative_lineage": negative_lineage, "provider": ident},
                  indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    (run_dir / "article.md").write_text(article_text, encoding="utf-8")
    report["word_count"] = len(article_text.split())
    report["article_sha256"] = hashlib.sha256(article_text.encode("utf-8")).hexdigest()

    claim_map, claim_errs, retries, cident = FL.claim_map_article(
        provider, article_text, ledger, allowed, FACT_STATUS)
    (run_dir / "CLAIM_MAP_VALIDATION.json").write_text(
        json.dumps({"errors": claim_errs, "claim_map": claim_map,
                   "retries": retries}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    report["claim_mapper_retries"] = retries
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
