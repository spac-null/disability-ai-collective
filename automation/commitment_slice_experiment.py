"""One frozen bandgap case, one commitment slice, one bounded cross-plan repair.

Reports five things separately, because four of them can be true while the fifth is false --
that is exactly what happened last time:

  TARGET_COMMITMENT_REMOVED
  AFFORDANCE_REMOVED
  PROTECTED_CONTENT_PRESERVED
  UNRELATED_FACT_PRESERVED_OR_EXPLICITLY_DROPPED
  WRITER_REGENERATION                (only the paired replay can answer this)

Usage: commitment_slice_experiment.py <out_dir>
"""
import json, os, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import commitment_slice_repair as C      # noqa: E402
from new_engine_v1 import definition_claim_shadow as D      # noqa: E402
from new_engine_v1.provider import parse_json_object        # noqa: E402
import claude_cli_provider as CCP                           # noqa: E402

EV = pathlib.Path("/srv/data/cripminds-evidence")
RUN = EV / "claim-shadow-batch2-2026-09-23" / "run2-20260923T212313Z"
SHADOW_FILE = EV / "claim-shadow-batch2-2026-09-23" / "shadow_run2.json"
TERM = "cutoff wavelength"


def main(out_dir):
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    arch = json.loads((RUN / "ARCHITECTURE.json").read_text())
    l = json.loads((RUN / "LEDGER.json").read_text())
    if isinstance(l, dict) and "facts" in l:
        l = l["facts"]
    led = l if isinstance(l, dict) else {f["fact_id"]: f for f in l}
    shadow = list(json.loads(SHADOW_FILE.read_text()).values())[0]

    sl = C.build_slice(arch, led, shadow, TERM)
    if sl.get("refusals"):
        print("SLICE REFUSED:", sl["refusals"]); return 1

    print("=" * 96)
    print("COMMITMENT: %r  (%s)" % (sl["commitment"]["span"], sl["commitment"]["status"]))
    print("  why: %s" % sl["commitment"]["reason"])
    print("  anchors: E1=%s  E2=%s" % (sl["endpoints"]["E1"], sl["endpoints"]["E2"]))
    print("  anchor candidates (word: ledger df): %s" % sl["anchor_report"]["candidates"])
    print("\nAFFORDING SURFACES (before):")
    for a in sl["affording"]:
        print("   %-17s %-28s %s" % (a.get("affordance"), a["surface_id"], a.get("where")))
    print("\nSLICE PARTITION:")
    for s in sl["surfaces"]:
        print("  %s" % s["surface_id"])
        for u in s["units"]:
            if u.get("separator"):
                continue
            role = u["role"]
            if s["kind"] == "DEFINITION" and u["unit_id"] == s["target_unit"]:
                role = "REPAIR"
            elif s["kind"] == "DEFINITION" and role == "GLUE":
                continue
            print("     %-9s [%-6s] %s" % (role, u["unit_id"], repr(u["text"])[:96]))
        if s.get("e2_facts"):
            print("     facts routing the second idea in: %s" % s["e2_facts"])

    prov = CCP.ClaudeCLIProvider()
    calls = {"n": 0}

    def ask(system, user):
        calls["n"] += 1
        (out / "REPAIR_PROMPT.txt").write_text(system + "\n\n=== USER ===\n\n" + user)
        return parse_json_object(prov.complete(system=system, user=user, max_tokens=2000).text)

    art = C.run(ask, arch, led, shadow, TERM,
                execution_id="commitment-slice-bandgap", out_dir=str(out))
    print("\n" + "=" * 96)
    print("STATUS: %s   model calls: %d" % (art["status"], calls["n"]))
    if art.get("error"):
        print("ERROR : %s" % art["error"])
    if art.get("validation_errors"):
        for e in art["validation_errors"]:
            print("   - %s" % e)
    if art.get("edit_plan"):
        print("\nEDIT PLAN  (%s)" % art["edit_plan"].get("reason"))
        for e in art["edit_plan"].get("edits") or []:
            print("   %-8s %-8s %s" % (e.get("operation"), e.get("unit_id"),
                                       repr(e.get("replacement"))[:70] if e.get("replacement") else ""))
        for f in art["edit_plan"].get("facts") or []:
            print("   FACT     %-8s %s %s" % (f.get("fact_id"), f.get("operation"),
                                              f.get("to_beat") or ""))
    p = art.get("preservation") or {}
    if art["status"] == "REPAIRED":
        rep = art["repaired_architecture"]
        print("\nDEFINITION")
        print("   before: %s" % arch["definitions"][TERM])
        print("   after : %s" % rep["definitions"][TERM])
        for s in sl["surfaces"]:
            if s["kind"] != "BEAT":
                continue
            b0 = next(b for b in arch["beats"] if b["beat_id"] == s["beat_id"])
            b1 = next(b for b in rep["beats"] if b["beat_id"] == s["beat_id"])
            print("\nBEAT %s" % s["beat_id"])
            print("   before: %s" % b0["happens"])
            print("   after : %s" % b1["happens"])
            print("   facts_allowed: %s  ->  %s" % (b0["facts_allowed"], b1["facts_allowed"]))
        print("\n   facts moved into other beats:")
        for b0, b1 in zip(arch["beats"], rep["beats"]):
            if (b0.get("facts_allowed") or []) != (b1.get("facts_allowed") or []) \
                    and b0["beat_id"] not in {x.get("beat_id") for x in sl["surfaces"]}:
                print("      %s: %s -> %s" % (b0["beat_id"], b0["facts_allowed"], b1["facts_allowed"]))
        (out / "REPAIRED_ARCHITECTURE.json").write_text(
            json.dumps(rep, indent=2, ensure_ascii=False))

    print("\nAFFORDING SURFACES (after): %s" % (p.get("affording_after") or "n/a"))
    print("second-concept facts: %s" % json.dumps(p.get("second_concept_facts") or {}, indent=1))
    print("orthographic adjustments: %s" % (p.get("orthographic_adjustments") or "none"))
    print("engine validators: %s" % art.get("engine_validation"))

    print("\n" + "=" * 96)
    for k in ("TARGET_COMMITMENT_REMOVED", "AFFORDANCE_REMOVED", "PROTECTED_CONTENT_PRESERVED",
              "UNRELATED_FACT_PRESERVED_OR_EXPLICITLY_DROPPED", "WRITER_REGENERATION"):
        print("  %-46s %s" % (k, p.get(k, "n/a")))

    (out / "REPORT.json").write_text(json.dumps(
        {"artifact": art, "calls": calls["n"]}, indent=2, ensure_ascii=False, default=str))
    return 0 if art["status"] == "REPAIRED" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/slice-exp"))
