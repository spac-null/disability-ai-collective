"""Classify the closed acquisition batch with the UNCHANGED detector and classifier.

Runs only after the batch is closed. One detector call per plan -- the module's own design --
and zero calls for the dispatch classifier, which is deterministic. Repairs nothing.

  detector    new_engine_v1.definition_claim_shadow, blob 3384f8bb..., code identity 80554bd
  classifier  new_engine_v1.commitment_slice_repair.classify, committed at 1ee91de

Both are asserted by blob hash before a single call is spent, because "the frozen detector"
is a claim, and a claim about which code ran is exactly the kind that should be checked by
the thing that runs it.

Every row carries its clustering metadata. Definitions from one plan share a source, a
ledger and one author call, and are not independent trials.

Usage: relational_supply_classify.py <batch_dir>
"""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

BATCH = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
TREE = BATCH / "tree"
sys.path.insert(0, str(TREE / "automation"))
sys.path.insert(0, str(TREE / "automation" / "orchestrator"))

from new_engine_v1 import definition_claim_shadow as D      # noqa: E402
from new_engine_v1 import commitment_slice_repair as CSR    # noqa: E402
from new_engine_v1.provider import parse_json_object        # noqa: E402
import claude_cli_provider as CCP                           # noqa: E402

EXPECT = {"automation/new_engine_v1/definition_claim_shadow.py":
          "3384f8bbc8d96e04437131eae6f7de83ca8e9226",
          "automation/new_engine_v1/commitment_slice_repair.py":
          "4666b84c6c08489a50e13759c019f9492e9e7017"}

FLAGGED = ("NOT_ESTABLISHED", "CONTRADICTED")


def assert_identity():
    for rel, want in EXPECT.items():
        got = subprocess.run(["git", "hash-object", rel], cwd=str(TREE),
                             capture_output=True, text=True).stdout.strip()
        if got != want:
            raise SystemExit("REFUSING TO RUN: %s is %s, expected %s" % (rel, got, want))
        print("  %-52s %s OK" % (rel.split("/")[-1], got[:12]))


def load_ledger(d: pathlib.Path):
    for name in ("FINAL_EVIDENCE_MANIFEST.json", "LEDGER.json"):
        p = d / name
        if not p.exists():
            continue
        j = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(j, dict) and "facts" in j:
            j = j["facts"]
        if isinstance(j, dict):
            return j, name
        if isinstance(j, list):
            return {f["fact_id"]: f for f in j}, name
    return None, ""


def main() -> int:
    st = json.loads((BATCH / "BATCH.json").read_text(encoding="utf-8"))
    if not st.get("closed"):
        raise SystemExit("the batch is not closed -- classification does not run early")
    print("batch closed: %s" % st["close_reason"])
    print("identity check:")
    assert_identity()

    os.environ[D.ENV_FLAG] = "1"
    prov = CCP.ClaudeCLIProvider()
    calls = {"n": 0}

    def ask(system, user):
        calls["n"] += 1
        return parse_json_object(prov.complete(system=system, user=user,
                                               max_tokens=3000).text)

    out = {"schema": "relational-supply-classification-v1",
           "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "detector_blob": EXPECT["automation/new_engine_v1/definition_claim_shadow.py"],
           "classifier_blob": EXPECT["automation/new_engine_v1/commitment_slice_repair.py"],
           "detector_code_identity": "80554bd", "classifier_commit": "1ee91de",
           "plans": [], "definitions": [], "warnings": []}

    plans = [a for a in st["attempts"] if a["outcome"] == "ARCHITECTURE"]
    print("\n%d plans reached ARCHITECTURE; one detector call each\n" % len(plans))
    for a in plans:
        d = pathlib.Path(a["plan_dir"])
        arch = json.loads((d / "ARCHITECTURE.json").read_text(encoding="utf-8"))
        ledger, lname = load_ledger(d)
        prec = {"run_id": a["run_id"], "seed_id": a["seed_id"], "rank": a["rank"],
                "source_name": a["source_name"], "url": a["url"],
                "ledger_file": lname, "ledger_facts": len(ledger or {}),
                "definitions": sorted(arch.get("definitions") or {})}
        if not ledger:
            prec["shadow_status"] = "NO_LEDGER"
            out["plans"].append(prec)
            continue
        shadow = D.run(ask, arch, ledger, execution_id="supply-%s" % a["run_id"])
        (d / "DEFINITION_CLAIM_SHADOW.json").write_text(
            json.dumps(shadow, indent=1, ensure_ascii=False, default=str),
            encoding="utf-8")
        prec["shadow_status"] = shadow.get("status")
        prec["shadow_calls"] = shadow.get("physical_model_calls")
        out["plans"].append(prec)
        print("  %-16s %-30s %s" % (a["run_id"], (a["source_name"] or "")[:30],
                                    shadow.get("status")))

        for dd in (shadow.get("definitions") or []):
            term = dd.get("term")
            claims = dd.get("claims") or []
            flags = [c for c in claims if c.get("status") in FLAGGED]
            base = {"run_id": a["run_id"], "seed_id": a["seed_id"], "rank": a["rank"],
                    "source_name": a["source_name"], "plan_dir": str(d),
                    "term": term, "claims": len(claims), "flagged": len(flags),
                    "has_definition_evidence":
                        bool((arch.get("definition_evidence") or {}).get(term)),
                    "dispatches": []}
            for c in flags:
                span = c.get("commitment") or ""
                r = CSR.classify(term, span, arch, ledger)
                base["dispatches"].append({
                    "span": span, "status": c.get("status"),
                    "detector_reason": (c.get("reason") or "")[:300],
                    "dispatch": r["dispatch"], "reason": r["reason"][:300],
                    "E1": r["E1"], "E2": r["E2"],
                    "qualified_endpoints": r.get("qualified_endpoints"),
                    "blocked_only_by_distinctiveness":
                        r.get("blocked_only_by_distinctiveness"),
                    "candidates": r["candidates"]})
                print("      %-34s %-16s %s" % (repr(span)[:34], c.get("status"),
                                                r["dispatch"]))
            out["definitions"].append(base)

    out["detector_calls"] = calls["n"]
    n_def = len(out["definitions"])
    n_flag = sum(d["flagged"] for d in out["definitions"])
    disp = {}
    for d in out["definitions"]:
        for x in d["dispatches"]:
            disp[x["dispatch"]] = disp.get(x["dispatch"], 0) + 1
    out["totals"] = {"plans_probed": len([p for p in out["plans"]
                                          if p.get("shadow_status") == "OK"]),
                     "definitions": n_def, "flagged_commitments": n_flag,
                     "dispatch": disp,
                     "distinct_plans": len({d["run_id"] for d in out["definitions"]})}
    out["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    body = json.dumps(out, indent=1, ensure_ascii=False, default=str)
    (BATCH / "CLASSIFICATION.json").write_text(body, encoding="utf-8")
    (BATCH / "CLASSIFICATION.sha256").write_text(
        "%s  CLASSIFICATION.json\n" % hashlib.sha256(body.encode()).hexdigest(),
        encoding="utf-8")
    print("\nTOTALS: %s" % json.dumps(out["totals"]))
    print("detector calls: %d" % calls["n"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
