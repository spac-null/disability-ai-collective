#!/usr/bin/env python3
"""Immigration candidate, continuation: discard ONLY the Writer-generated
(pre-separation) claim_map, keep the article byte-for-byte, run the new read-only
Claim Mapper against the frozen article, validate, and if clean continue Safety ->
Grounding -> Fact Check -> Reader. No Writer call. No article mutation."""
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
import immigration_packet_v2 as IP2                         # noqa: E402


def main(run_dir: str, model: str = DEFAULT_MODEL) -> dict:
    run_dir = pathlib.Path(run_dir)

    article_text = (run_dir / "article.md").read_text(encoding="utf-8")
    sha_before = hashlib.sha256(article_text.encode("utf-8")).hexdigest()

    packet = json.loads((run_dir / "ARTICLE_PACKET.json").read_text(encoding="utf-8"))
    allowed = (set(packet["load_bearing_facts"]) | set(packet["story_bearing_facts"])
              | set(packet["supporting_facts"]))
    ledger_wrapper = json.loads((run_dir / "LEDGER.json").read_text(encoding="utf-8"))
    ledger = ledger_wrapper["ledger"]
    arch = json.loads((run_dir / "ARCH.json").read_text(encoding="utf-8"))
    pack = json.loads((run_dir / "RESEARCH_PACK.json").read_text(encoding="utf-8"))
    fact_status = IP2.FACT_STATUS
    assert allowed == set(fact_status), "FACT_STATUS/packet selection mismatch"

    # Discard only the old (pre-separation) claim_map and negative_lineage carrier;
    # negative_lineage is still needed by safety_audit and was produced by the SAME
    # Writer call that produced this article, so it is kept from WRITER_OUTPUT.json.
    writer_output = json.loads((run_dir / "WRITER_OUTPUT.json").read_text(encoding="utf-8"))
    assert writer_output["article_text"] == article_text, \
        "article.md and WRITER_OUTPUT.json have diverged -- refusing to continue"
    # This run's WRITER_OUTPUT.json was persisted by the pre-fix fast_lane_write(),
    # which stored negative_lineage as the Writer's raw list; convert it the same way
    # fast_lane_write() now does internally (see FL.negative_lineage_dict).
    negative_lineage = FL.negative_lineage_dict(writer_output.get("negative_lineage")
                                                or [])

    provider = Provider(model=model)
    report = {"article_sha_before": sha_before}

    claim_map, claim_errs, retries, ident = FL.claim_map_article(
        provider, article_text, ledger, allowed, fact_status)
    (run_dir / "CLAIM_MAP_VALIDATION.json").write_text(
        json.dumps({"errors": claim_errs, "claim_map": claim_map, "retries": retries},
                  indent=2, ensure_ascii=False), encoding="utf-8")

    sha_after = hashlib.sha256(
        (run_dir / "article.md").read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    report["article_sha_after"] = sha_after
    report["article_sha_unchanged"] = (sha_before == sha_after)
    report["claim_mapper_retries"] = retries

    if claim_errs:
        report.update(stage_reached="CLAIM_MAP", status="HOLD", errors=claim_errs)
        print(json.dumps(report, indent=2, default=str))
        return report
    report["claim_map"] = "PASS"

    writer_packet_obj, _ = CP.writer_packet(arch, ledger, cut_prohibitions=None)
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
        print(json.dumps(report, indent=2, default=str))
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
        print(json.dumps(report, indent=2, default=str))
        return report

    fact_check = FCB.fact_check(final_text)
    (run_dir / "FACT_CHECK.json").write_text(
        json.dumps(fact_check, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["fact_check"] = fact_check.get("status")
    if fact_check.get("status") != "PASS":
        report.update(stage_reached="FACT_CHECK", status="HOLD",
                      blocking=fact_check.get("blocking_contradictions"))
        print(json.dumps(report, indent=2, default=str))
        return report

    reader = CP.reader_gate(provider, final_text)
    (run_dir / "READER_AUDIT.json").write_text(
        json.dumps(reader, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["reader"] = reader.get("status")
    report.update(stage_reached="READER", status=reader.get("status"),
                 dimensions=reader.get("dimensions"), held=reader.get("held"),
                 one_line=reader.get("one_line"))
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return report


if __name__ == "__main__":
    main(sys.argv[1])
