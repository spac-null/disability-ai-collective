#!/usr/bin/env python3
"""Continue an existing Fast Lane V1 replay from Safety onward, on the EXACT SAME
article -- no new Writer call, no repair loop. Used after a Safety/Grounding engine
fix to re-check a retained article without regenerating it."""
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


def main(run_dir: str, out_dir: str) -> dict:
    run_dir = pathlib.Path(run_dir)
    out_dir = pathlib.Path(out_dir)
    retained = FL.load_run(run_dir)
    ledger = retained["ledger"]
    provider = Provider(model=DEFAULT_MODEL)

    article_text = (out_dir / "article.md").read_text(encoding="utf-8")
    writer_output = json.loads((out_dir / "WRITER_OUTPUT.json").read_text(encoding="utf-8"))
    assert writer_output["article_text"] == article_text, \
        "article.md and WRITER_OUTPUT.json have diverged -- refusing to continue"
    sha = hashlib.sha256(article_text.encode("utf-8")).hexdigest()

    arch = json.loads((out_dir / "ARCH.json").read_text(encoding="utf-8"))
    packet = json.loads((out_dir / "ARTICLE_PACKET.json").read_text(encoding="utf-8"))
    negative_lineage = writer_output.get("negative_lineage") or []

    # Rebuild the SAME writer_packet (deterministic, no model call) rather than trust a
    # persisted copy, since safety_audit needs the exact object story.render() produced.
    writer_packet_obj, _ = CP.writer_packet(arch, ledger, cut_prohibitions=None)

    report = {"article_sha256": sha, "word_count": len(article_text.split())}

    draft_text = final_text = article_text
    cut_terms = CP.derive_cut_watch_terms(arch, ledger)
    safety = CP.safety_audit(draft_text, final_text, writer_packet_obj, arch, ledger,
                             cut_terms, negative_lineage=negative_lineage)
    (out_dir / "SAFETY_AUDIT.json").write_text(
        json.dumps(safety, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["safety"] = safety.get("status")
    if safety.get("status") != CP.PASS:
        report.update(stage_reached="SAFETY", status="HOLD",
                      blocking=safety.get("blocking"))
        return report

    grounding = CP.ground_candidate(provider, final_text, retained["source_text"],
                                    retained["source_sha"], retained["pack"],
                                    arch=arch, packet=writer_packet_obj)
    (out_dir / "GROUNDING_AUDIT.json").write_text(
        json.dumps(grounding, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["grounding"] = grounding.get("status")
    if grounding.get("status") != CP.PASS:
        report.update(stage_reached="GROUNDING", status="HOLD",
                      blocking=grounding.get("blocking"))
        return report

    fact_check = FCB.fact_check(final_text)
    (out_dir / "FACT_CHECK.json").write_text(
        json.dumps(fact_check, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["fact_check"] = fact_check.get("status")
    if fact_check.get("status") != "PASS":
        report.update(stage_reached="FACT_CHECK", status="HOLD",
                      blocking=fact_check.get("blocking_contradictions"))
        return report

    reader = CP.reader_gate(provider, final_text)
    (out_dir / "READER_AUDIT.json").write_text(
        json.dumps(reader, indent=2, sort_keys=True, default=str), encoding="utf-8")
    report["reader"] = reader.get("status")
    report.update(stage_reached="READER", status=reader.get("status"),
                 dimensions=reader.get("dimensions"), held=reader.get("held"),
                 one_line=reader.get("one_line"))
    return report


if __name__ == "__main__":
    result = main(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
