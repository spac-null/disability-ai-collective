"""Run the constrained repair against FROZEN cases. One model call per case, no loop.

Cases, all from /srv/data/cripminds-evidence/ with checksums verified:

  A  cutoff wavelength     the hard case -- the free rewrite deleted the explanation
  B  Dressing for Evac.    the easy case that already worked -- must not break
  C  transfer-to-seat      correct warning the Writer removed on its own; diagnostic
  D  every clean definition in the same plans -- must produce NO call at all

Usage: definition_repair_experiment.py <out_dir>
"""
import json, os, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import definition_repair_compiler as R   # noqa: E402
from new_engine_v1.provider import parse_json_object        # noqa: E402
import claude_cli_provider as CCP                           # noqa: E402

EV = pathlib.Path("/srv/data/cripminds-evidence")
CAL = pathlib.Path("/srv/data/cripminds-dcs-calibration/calib.json")

B2 = EV / "claim-shadow-batch2-2026-09-23"
B3 = EV / "claim-shadow-batch3-2026-09-23"
PR = EV / "pr106-rehearsal-cohort-2026-09-23"


def load(run_dir):
    arch = json.loads((run_dir / "ARCHITECTURE.json").read_text())
    l = json.loads((run_dir / "LEDGER.json").read_text())
    if isinstance(l, dict) and "facts" in l:
        l = l["facts"]
    led = l if isinstance(l, dict) else {f["fact_id"]: f for f in l}
    return arch, led


def shadow_of(blob, runkey):
    return blob[runkey]


def main(out_dir):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    b2r1 = json.loads((B2 / "shadow_run1.json").read_text())
    b2r2 = json.loads((B2 / "shadow_run2.json").read_text())
    b3r1 = json.loads((B3 / "shadow_run1.json").read_text())
    b3r2 = json.loads((B3 / "shadow_run2.json").read_text())
    cal = json.loads(CAL.read_text())

    R1 = "run1-20260923T210336Z"; R2 = "run2-20260923T212313Z"
    B3R1 = "run1-20260923T220109Z"; B3R2 = "run2-20260923T221807Z"
    PRR1 = "run1-20260923T193833Z"

    plans = [
        ("A_bandgap",  B2 / R2,  shadow_of(b2r2, R2),  "cutoff wavelength"),
        ("B_minutes",  PR / PRR1, cal["A_run1"],       "Dressing for Evacuation"),
        ("C_seat",     B2 / R1,  shadow_of(b2r1, R1),  "transfer-to-seat"),
    ]
    controls = [
        ("D_b2r2", B2 / R2,  shadow_of(b2r2, R2)),
        ("D_b3r1", B3 / B3R1, shadow_of(b3r1, B3R1)),
        ("D_b3r2", B3 / B3R2, shadow_of(b3r2, B3R2)),
    ]

    report = {"cases": {}, "positive_control": {}, "total_model_calls": 0}

    # ---- D: positive control FIRST. If a clean definition asks for a call, stop. ----
    for label, run_dir, shadow in controls:
        arch, led = load(run_dir)
        targets = R.plan_targets(arch, shadow)
        flagged = {t["term"] for t in targets}
        allterms = set((arch.get("definitions") or {}).keys())
        report["positive_control"][label] = {
            "definitions_in_plan": sorted(allterms),
            "would_call_for": sorted(flagged),
            "clean_definitions_untouched": sorted(allterms - flagged),
        }
        print("[%s] %d definitions, %d flagged -> %s" % (label, len(allterms), len(flagged), sorted(flagged)))

    prov = CCP.ClaudeCLIProvider()
    calls = {"n": 0}

    def ask(system, user):
        calls["n"] += 1
        comp = prov.complete(system=system, user=user, max_tokens=1200)
        return parse_json_object(comp.text)

    for label, run_dir, shadow, term in plans:
        arch, led = load(run_dir)
        gloss = (arch.get("definitions") or {}).get(term)
        claims = None
        for d in shadow.get("definitions", []):
            if d.get("term") == term:
                claims = d["claims"]
        ir = R.build_ir(term, gloss, claims)
        reps = [u["unit_id"] for u in ir["units"] if u["role"] == R.REPAIRABLE]

        # One warning at a time. Where a gloss carries more than one, the experiment names
        # the one it is about rather than letting the module pick.
        unit_id = ""
        if label == "B_minutes":
            unit_id = [u["unit_id"] for u in ir["units"]
                       if u["role"] == R.REPAIRABLE and "minutes away" in u["text"]][0]
        before = calls["n"]
        art = R.run(ask, arch, led, shadow, term, unit_id=unit_id,
                    execution_id="repair-%s" % label, out_dir=str(out / label))
        art["_calls_made"] = calls["n"] - before
        art["_repairable_units_in_gloss"] = reps
        art["_source_run"] = str(run_dir)
        report["cases"][label] = art

        print("\n=== %s :: %s ===" % (label, term))
        print("  repairable units in gloss : %s" % reps)
        print("  status                    : %s" % art["status"])
        print("  model calls               : %d" % art["_calls_made"])
        if art["status"] == "REPAIRED":
            print("  operation                 : %s" % art["edit_plan"]["operation"])
            print("  replacement               : %r" % art["edit_plan"].get("replacement"))
            print("  reason                    : %s" % art["edit_plan"].get("reason"))
            print("  BEFORE: %s" % art["original_gloss"])
            print("  AFTER : %s" % art["repaired_gloss"])
            p = art["preservation"]
            print("  protected survived        : %s/%s  explanatory %s/%s  ordered=%s"
                  % (len(p["protected_survived_verbatim"]), len(p["protected_units"]),
                     len(p["explanatory_survived"]), len(p["explanatory_units"]),
                     p["protected_in_original_order"]))
            print("  chars changed             : %d of %d" % (p["chars_changed_outside_common_affixes"],
                                                              p["original_chars"]))
        else:
            print("  error                     : %s" % art.get("error"))

    report["total_model_calls"] = calls["n"]
    (out / "REPORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    print("\nTOTAL PHYSICAL MODEL CALLS: %d (expected 3: one per case, none for controls)" % calls["n"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/repair-exp")
