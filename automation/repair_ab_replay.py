"""Replay one plan from a PROPOSED repair, so the A/B is judged on the prose a reader gets.

Read-only against the original run. Writes only into a fresh output directory. Publishes
nothing, accepts nothing, and replaces no production architecture.

The B side reuses the frozen RESEARCH_PACK, ledger and worth of the original run and
substitutes ONLY the repaired architecture, so the Writer path is the sole variable. Same
FAST_LANE compose mode the scheduled run uses. One pass, no retries to improve prose --
a second attempt would be choosing the nicer of two drafts, which is not what is being
measured.

Usage: repair_ab_replay.py <finding_id> <out_dir>
"""
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "orchestrator"))

from new_engine_v1 import composition as CP          # noqa: E402
import composition_factual_bridge as FCB             # noqa: E402
import claude_cli_provider as CCP                    # noqa: E402
import repair_review_store as STORE                  # noqa: E402


def main() -> int:
    fid, out = sys.argv[1], pathlib.Path(sys.argv[2])
    f = next((x for x in STORE.findings() if x["finding_id"].startswith(fid)), None)
    if f is None:
        raise SystemExit("no such finding: %s" % fid)
    d = pathlib.Path(f["plan_dir"])
    prop = json.loads((d / "repair-review" / f["finding_id"] / "PROPOSED.json")
                      .read_text(encoding="utf-8"))
    repaired = prop["repaired_architecture"]
    if not (repaired.get("definitions") or {}).get(f["term"], "").strip():
        raise SystemExit("the proposal carries no repaired definition; refusing to replay")

    pack = json.loads((d / "RESEARCH_PACK.json").read_text(encoding="utf-8"))
    led = json.loads((d / "FINAL_EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
    led = led.get("facts", led)
    frozen = {"ledger": led, "architecture": repaired}
    w = d / "WORTH_AND_CANDIDATE.json"
    if w.exists():
        frozen["worth"] = json.loads(w.read_text(encoding="utf-8"))

    anchor = next(s for s in pack["sources"] if s.get("role") == "ANCHOR")
    out.mkdir(parents=True, exist_ok=True)
    (out / "REPAIRED_ARCHITECTURE.json").write_text(
        json.dumps(repaired, indent=1, ensure_ascii=False), encoding="utf-8")

    prov = CCP.ClaudeCLIProvider()
    print("finding  %s   term %r" % (f["finding_id"][:10], f["term"]))
    print("before   %s" % prop["before_gloss"])
    print("after    %s" % prop["after_gloss"])
    print("compose  %s | model %s" % (CP.scheduled_compose_mode(), prov.model))
    print("\nreplaying from the repaired architecture, one pass ...")
    res = CP.run_story_architecture_composition(
        prov, pack=pack, source_text=anchor["text"], source_sha=anchor["sha256"],
        subject=pack["subject"], fact_check=True, fact_check_fn=FCB.fact_check,
        out_dir=out, frozen=frozen, stop_after="",
        compose_mode=CP.scheduled_compose_mode())
    print("  status %s | failure %s | words %s"
          % (res.get("status"), res.get("failure_stage"), res.get("words")))
    print("  artifacts: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
