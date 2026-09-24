"""BOUNDED_MULTI_CASE_OBLIGATION_TEST -- six frozen cases, one policy, no tuning between them.

The question is NOT whether the Writer produces good prose. It is whether the compiler can
derive PERMISSIONS / OBLIGATIONS / PROHIBITIONS from ordinary pipeline output without the
answer being hand-authored.

  permissions   facts_allowed, untouched
  obligations   obligation_policy.select() -- deterministic, no model, committed beforehand
  prohibitions  written by the same single repair call, validated mechanically

THE COHORT IS FIXED HERE AND NOT CHOSEN AFTER LOOKING. Two of the six are clean and must cost
nothing at all; one carries five supported commitments around a single flag, to see whether
the policy over-selects; one is a case where dropping is very likely the right move.

Usage: obligation_cohort.py <out_dir>
"""
import copy, hashlib, json, os, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import commitment_slice_repair as CSR    # noqa: E402
from new_engine_v1 import definition_repair_compiler as DRC  # noqa: E402
from new_engine_v1 import obligation_policy as OP            # noqa: E402
from new_engine_v1 import story as ST                        # noqa: E402
from new_engine_v1 import composition as CP                  # noqa: E402
from new_engine_v1.provider import parse_json_object         # noqa: E402
import claude_cli_provider as CCP                            # noqa: E402

EV = pathlib.Path("/srv/data/cripminds-evidence")
B2 = EV / "claim-shadow-batch2-2026-09-23"
PR = EV / "pr106-rehearsal-cohort-2026-09-23"
CAL = pathlib.Path("/srv/data/cripminds-dcs-calibration/calib.json")
R1, R2, PRR1 = "run1-20260923T210336Z", "run2-20260923T212313Z", "run1-20260923T193833Z"

# (label, run_dir, shadow_source, term, note)
COHORT = [
    ("C1_bandgap",  B2 / R2,   ("b2r2", R2),  "cutoff wavelength",
     "hard positive: the known bridge"),
    ("C2_minutes",  PR / PRR1, ("calib", "A_run1"), "Dressing for Evacuation",
     "two flags; the minutes-away one is targeted"),
    ("C3_seat",     B2 / R1,   ("b2r1", R1),  "transfer-to-seat",
     "correct warning the Writer removed on its own"),
    ("C4_aufguss",  B2 / R1,   ("b2r1", R1),  "Aufguss",
     "five supported commitments around one flag; dropping is likely right"),
    ("C5_dark",     B2 / R2,   ("b2r2", R2),  "dark current",
     "CLEAN -- must cost nothing"),
    ("C6_sca",      B2 / R2,   ("b2r2", R2),  "sensor chip assembly (SCA)",
     "CLEAN with five supported commitments -- over-selection control"),
]


def sha(x):
    return hashlib.sha256(x.encode("utf-8") if isinstance(x, str) else x).hexdigest()


def load_shadow(kind, key):
    if kind == "calib":
        return json.loads(CAL.read_text())[key]
    src = B2 / ("shadow_run1.json" if key == R1 else "shadow_run2.json")
    return json.loads(src.read_text())[key]


def load_run(d):
    arch = json.loads((d / "ARCHITECTURE.json").read_text())
    l = json.loads((d / "LEDGER.json").read_text())
    if isinstance(l, dict) and "facts" in l:
        l = l["facts"]
    return arch, (l if isinstance(l, dict) else {f["fact_id"]: f for f in l})


def main(out_dir):
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    prov, calls = None, {"n": 0}

    def ask(system, user):
        calls["n"] += 1
        return parse_json_object(prov.complete(system=system, user=user, max_tokens=2500).text)

    report = {"policy": "obligation-policy-v1", "cases": {}, "model_calls": 0}

    for label, run_dir, (skind, skey), term, note in COHORT:
        arch, led = load_run(run_dir)
        shadow = load_shadow(skind, skey)
        claims = None
        for d in shadow.get("definitions", []):
            if d.get("term") == term:
                claims = d.get("claims") or []
        gloss = (arch.get("definitions") or {}).get(term)
        print("\n" + "=" * 98)
        print("%s  [%s]  %s" % (label, term, note))
        if gloss is None or claims is None:
            print("   SKIP -- not present in this plan"); continue

        ir = DRC.build_ir(term, gloss, claims)
        reps = [u for u in ir.get("units", []) if u["role"] == DRC.REPAIRABLE]
        rec = {"term": term, "note": note, "source": str(run_dir),
               "commitments": len(claims), "flagged": [u["text"] for u in reps],
               "anchoring": ir.get("anchoring")}

        if not reps:
            rec.update({"outcome": "NO_REPAIR", "model_calls": 0, "obligations": [],
                        "prohibition": None})
            print("   commitments=%d  flagged=0  ->  NO REPAIR, NO OBLIGATION, NO CALL"
                  % len(claims))
            report["cases"][label] = rec
            continue

        unit_id = ""
        if len(reps) > 1:
            pick = [u for u in reps if "minutes away" in u["text"]]
            unit_id = (pick or reps)[0]["unit_id"]
        target = DRC.select_target(ir, unit_id)

        # what the policy would oblige BEFORE the repair runs (displaced facts unknown yet)
        pre = OP.select(ir, target)
        print("   commitments=%d  flagged=%d  target=%r" % (len(claims), len(reps), target["text"]))
        print("   policy (pre-repair): %s  share=%.2f"
              % ([(o["id"], o["why"]) for o in pre["obligations"]], pre["obligation_share"]))

        if prov is None:
            prov = CCP.ClaudeCLIProvider()
        before = calls["n"]
        art = CSR.run(ask, arch, led, shadow, term, unit_id=unit_id,
                      execution_id="cohort-%s" % label, out_dir=str(out / label))
        made = calls["n"] - before
        rec["model_calls"] = made
        rec["repair_status"] = art["status"]

        if art["status"] != "REPAIRED":
            rec.update({"outcome": "REPAIR_REFUSED", "error": art.get("error"),
                        "validation_errors": art.get("validation_errors")})
            print("   REPAIR REFUSED (%d call): %s" % (made, art.get("error")))
            report["cases"][label] = rec
            continue

        plan = art["edit_plan"]
        sel = OP.select(ir, target, plan, led)
        field = OP.architecture_field(sel)
        rep_arch = copy.deepcopy(art["repaired_architecture"])
        rep_arch["prohibitions"] = list(rep_arch.get("prohibitions") or []) + [plan["prohibition"]]
        rep_arch["required_commitments"] = field

        os.environ[ST.REQUIRED_COMMITMENTS_FLAG] = "1"
        try:
            _, rendered = CP.writer_packet(rep_arch, led)
            packet_ok, packet_err = True, ""
        except Exception as e:                                    # noqa: BLE001
            rendered, packet_ok, packet_err = "", False, "%s: %s" % (type(e).__name__, e)
        os.environ.pop(ST.REQUIRED_COMMITMENTS_FLAG, None)

        ids = set(led.keys())
        verrs = (ST.validate_architecture(rep_arch, ids, led)
                 + ST.validate_definition_support(rep_arch, led)
                 + ST.validate_evidence_hierarchy(rep_arch, ids))

        rec.update({
            "outcome": "REPAIRED",
            "operation": [(e.get("unit_id"), e.get("operation")) for e in plan.get("edits") or []],
            "facts": [(f.get("fact_id"), f.get("operation"), f.get("to_beat"))
                      for f in plan.get("facts") or []],
            "prohibition": plan["prohibition"],
            "obligations": [{"id": o["id"], "why": o["why"], "text": o["must_realize"]}
                            for o in sel["obligations"]],
            "obligation_share": sel["obligation_share"],
            "over_obligation": sel["over_obligation"],
            "preservation": {k: art["preservation"].get(k) for k in
                             ("all_keep_survived", "affordance_closed",
                              "plan_outside_slice_byte_identical",
                              "flagged_span_absent_from_gloss")},
            "engine_validation": verrs or "CLEAN",
            "packet_renders": packet_ok, "packet_error": packet_err,
            "packet_sha256": sha(rendered) if rendered else None,
            "obligations_in_packet": all(o["must_realize"] in rendered for o in sel["obligations"])
                                      if rendered else False,
            "prohibition_in_packet": (plan["prohibition"] in rendered) if rendered else False,
        })
        (out / label).mkdir(parents=True, exist_ok=True)
        (out / label / "ARCHITECTURE.json").write_text(json.dumps(rep_arch, indent=2, ensure_ascii=False))
        if rendered:
            (out / label / "WRITER_PACKET_FROZEN.txt").write_text(rendered)

        print("   repair: %s   facts: %s   (%d call)" % (rec["operation"], rec["facts"], made))
        print("   PROHIBITION: %s" % plan["prohibition"])
        print("   OBLIGATIONS (%d of %d considered, share %.2f%s):"
              % (len(sel["obligations"]), sel["commitments_considered"], sel["obligation_share"],
                 "  ** OVER **" if sel["over_obligation"] else ""))
        for o in sel["obligations"]:
            print("      %-18s %s" % (o["why"], repr(o["must_realize"])[:82]))
        print("   validators: %s | packet: renders=%s obligations_in=%s prohibition_in=%s"
              % (rec["engine_validation"] if verrs else "CLEAN", packet_ok,
                 rec["obligations_in_packet"], rec["prohibition_in_packet"]))
        report["cases"][label] = rec

    report["model_calls"] = calls["n"]
    (out / "COHORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))

    print("\n" + "=" * 98)
    print("COHORT SUMMARY   policy=%s   total model calls=%d" % (report["policy"], calls["n"]))
    print("%-13s %-5s %-5s %-6s %-7s %-6s %s" % ("case", "cmts", "flag", "calls", "obligs", "share", "outcome"))
    for label, r in report["cases"].items():
        print("%-13s %-5s %-5s %-6s %-7s %-6s %s"
              % (label, r.get("commitments"), len(r.get("flagged") or []), r.get("model_calls"),
                 len(r.get("obligations") or []), r.get("obligation_share", "-"),
                 r.get("outcome") + (" **OVER**" if r.get("over_obligation") else "")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cohort"))
