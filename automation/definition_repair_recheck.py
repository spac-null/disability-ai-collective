"""Re-run the UNCHANGED Claim Support Shadow over the repaired architectures.

The detector is not modified, not re-tuned and not told a repair happened. It sees a plan
like any other. A clean re-check is necessary and not sufficient -- the bandgap failure was
already clean by this measure -- so preservation is proven separately, in the compiler.

Usage: definition_repair_recheck.py <exp_dir>
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import definition_claim_shadow as D     # noqa: E402
from new_engine_v1 import definition_repair_compiler as R  # noqa: E402
from new_engine_v1.provider import parse_json_object       # noqa: E402
import claude_cli_provider as CCP                          # noqa: E402
import os                                                  # noqa: E402

os.environ[D.ENV_FLAG] = "1"

REP = {"A_bandgap": "cutoff wavelength",
       "B_minutes": "Dressing for Evacuation",
       "C_seat": "transfer-to-seat"}


def load(run_dir):
    run_dir = pathlib.Path(run_dir)
    arch = json.loads((run_dir / "ARCHITECTURE.json").read_text())
    l = json.loads((run_dir / "LEDGER.json").read_text())
    if isinstance(l, dict) and "facts" in l:
        l = l["facts"]
    return arch, (l if isinstance(l, dict) else {f["fact_id"]: f for f in l})


def main(exp_dir):
    exp = pathlib.Path(exp_dir)
    report = json.loads((exp / "REPORT.json").read_text())
    prov = CCP.ClaudeCLIProvider()
    calls = {"n": 0}

    def ask(system, user):
        calls["n"] += 1
        return parse_json_object(prov.complete(system=system, user=user, max_tokens=3000).text)

    out = {}
    for label, term in REP.items():
        case = report["cases"][label]
        if case["status"] != "REPAIRED":
            print("[%s] not repaired, skipping" % label)
            continue
        arch, led = load(case["_source_run"])
        before_gloss = arch["definitions"][term]
        assert before_gloss == case["original_gloss"], "baseline drift on %s" % label

        arch2 = json.loads(json.dumps(arch))
        arch2["definitions"][term] = case["repaired_gloss"]
        (exp / label / "REPAIRED_ARCHITECTURE.json").write_text(
            json.dumps(arch2, indent=2, ensure_ascii=False))

        art = D.run(ask, arch2, led, execution_id="recheck-%s" % label,
                    out_dir=str(exp / label))
        out[label] = art

        rep_unit = case["repairable_text"]
        rows = {d["term"]: d["claims"] for d in art.get("definitions", [])}
        claims = rows.get(term, [])
        bad = [c for c in claims if c["status"] in R.REPAIRABLE_STATUSES]

        # every commitment the BASELINE shadow called SUPPORTED, in this same definition
        base_sup = {u["text"] for u in case["ir"]["units"]
                    if u["role"] == R.PROTECTED and u["status"] == D.SUPPORTED}
        now_sup = {c["commitment"] for c in claims if c["status"] == D.SUPPORTED}

        print("\n=== recheck %s :: %s ===" % (label, term))
        print("  target commitment %r" % rep_unit)
        print("  still present in any claim : %s"
              % any(rep_unit in c["commitment"] for c in claims))
        print("  claims now                 : %d" % len(claims))
        for c in claims:
            print("     %-30s %r" % (c["status"], c["commitment"]))
        print("  still-flagged in this def  : %s" % [c["commitment"] for c in bad])
        print("  baseline SUPPORTED spans still SUPPORTED: %d/%d"
              % (len(base_sup & now_sup), len(base_sup)))
        missing = base_sup - now_sup
        if missing:
            print("    NOT reconfirmed: %s" % sorted(missing))
        others = {d["term"]: [c for c in d["claims"] if c["status"] in R.REPAIRABLE_STATUSES]
                  for d in art.get("definitions", []) if d["term"] != term}
        print("  other definitions in plan, still-flagged: %s"
              % {k: [c["commitment"] for c in v] for k, v in others.items() if v})

    (exp / "RECHECK.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    print("\nrecheck model calls: %d" % calls["n"])


if __name__ == "__main__":
    main(sys.argv[1])
