"""Run the Definition Claim Support detector over finished production runs.

AFTER the run, never inside it. The daily pipeline is not touched by a single line: this
reads the frozen ARCHITECTURE and ledger a completed run left on disk, spends one detector
call per plan, and appends whatever it flags to the review queue.

That is a deliberate choice and not laziness. Hooking into composition would put a new model
call on the critical path of the job that publishes the site, inside an 8,979-line module,
to obtain findings that -- by policy -- are not allowed to hold publication anyway. A sweep
gets the same findings minutes later and cannot break the thing it is watching. If the sweep
dies, the queue is short and the site is unaffected.

NO PUBLICATION AUTHORITY. Nothing here reads or writes publication state, touches _drafts,
_posts, the discovery database, or git. It appends to a queue an editor reads.

Usage: repair_detector_sweep.py [--runs-root DIR] [--since ISO] [--limit N] [--dry-run]
"""
import argparse
import datetime
import json
import os
import pathlib
import sys
import traceback

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "orchestrator"))

from new_engine_v1 import definition_claim_shadow as D      # noqa: E402
from new_engine_v1 import commitment_slice_repair as CSR    # noqa: E402
from new_engine_v1.provider import parse_json_object        # noqa: E402
import repair_review_store as STORE                         # noqa: E402

RUNS_ROOT = pathlib.Path("/srv/data/cripminds-new-engine-v1")
FLAGGED = ("NOT_ESTABLISHED", "CONTRADICTED")
MARKER = "DEFINITION_CLAIM_SHADOW.json"


def load_ledger(d: pathlib.Path):
    for name in ("FINAL_EVIDENCE_MANIFEST.json", "LEDGER.json"):
        p = d / name
        if not p.exists():
            continue
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except Exception:                                         # noqa: BLE001
            continue
        j = j.get("facts", j) if isinstance(j, dict) else j
        if isinstance(j, dict):
            return j
        if isinstance(j, list):
            return {f["fact_id"]: f for f in j}
    return None


def candidate_runs(root: pathlib.Path, since: str, limit: int) -> list:
    already = STORE.swept()
    out = []
    for d in sorted(root.glob("production-*"), key=lambda p: p.name, reverse=True):
        if since and d.name[len("production-"):len("production-") + 8] < since:
            continue
        if not (d / "ARCHITECTURE.json").exists():
            continue
        if d.name in already or (d / MARKER).exists():
            continue                              # one detector call per plan, ever
        out.append(d)
        if limit and len(out) >= limit:
            break
    return out


def sweep_one(d: pathlib.Path, ask, dry_run: bool) -> dict:
    arch = json.loads((d / "ARCHITECTURE.json").read_text(encoding="utf-8"))
    ledger = load_ledger(d)
    res = {"run": d.name, "definitions": len(arch.get("definitions") or {}),
           "flagged": 0, "queued": 0, "status": ""}
    if not ledger:
        res["status"] = "NO_LEDGER"
        STORE.record_sweep(d.name, "NO_LEDGER", len(arch.get("definitions") or {}), 0)
        return res
    if not (arch.get("definitions") or {}):
        res["status"] = "NO_DEFINITIONS"
        STORE.record_sweep(d.name, "NO_DEFINITIONS", len(arch.get("definitions") or {}), 0)
        return res
    if not (arch.get("definition_evidence") or {}):
        # the detector's contract needs it; plans older than PR #106 cannot be judged
        res["status"] = "NO_DEFINITION_EVIDENCE"
        STORE.record_sweep(d.name, "NO_DEFINITION_EVIDENCE", len(arch.get("definitions") or {}), 0)
        return res
    if dry_run:
        res["status"] = "WOULD_SWEEP"
        return res

    shadow = D.run(ask, arch, ledger, execution_id="sweep-%s" % d.name)
    # recorded BEFORE the artifact write, so a failed write cannot buy a second call
    STORE.record_sweep(d.name, str(shadow.get("status")),
                       len(arch.get("definitions") or {}), 0)
    (d / MARKER).write_text(json.dumps(shadow, indent=1, ensure_ascii=False, default=str),
                            encoding="utf-8")
    res["status"] = shadow.get("status")

    for dd in (shadow.get("definitions") or []):
        term = dd.get("term")
        gloss = (arch.get("definitions") or {}).get(term) or ""
        ev_ids = (arch.get("definition_evidence") or {}).get(term)
        if isinstance(ev_ids, str):
            ev_ids = [ev_ids]
        ev = [{"fact_id": str(i),
               "proposition": str((ledger.get(str(i)) or {}).get("proposition", "")),
               "support_span": str((ledger.get(str(i)) or {}).get("support_span", ""))}
              for i in (ev_ids or [])]
        for c in (dd.get("claims") or []):
            if c.get("status") not in FLAGGED:
                continue
            res["flagged"] += 1
            span = c.get("commitment") or ""
            # the frozen dispatcher's opinion, recorded now and shown to nobody
            try:
                pred = CSR.classify(term, span, arch, ledger)
                pred = {"dispatch": pred["dispatch"], "reason": pred["reason"][:300],
                        "E1": pred["E1"], "E2": pred["E2"],
                        "qualified_endpoints": pred.get("qualified_endpoints"),
                        "classifier_state": "FROZEN -- NEEDS_REDESIGN, advisory to nobody"}
            except Exception as e:                                # noqa: BLE001
                pred = {"error": "%s: %s" % (type(e).__name__, str(e)[:120])}
            row = {"finding_id": STORE.finding_id(d.name, term, span),
                   "run_id": d.name, "plan_dir": str(d),
                   "term": term, "span": span, "status": c.get("status"),
                   "detector_reason": (c.get("reason") or "")[:500],
                   "gloss": gloss, "declared_evidence": ev,
                   "all_claims": [{"commitment": x.get("commitment"),
                                   "status": x.get("status")}
                                  for x in (dd.get("claims") or [])],
                   "detector_code_identity": "80554bd",
                   "classifier_prediction": pred}
            if STORE.record_finding(row) is not None:
                res["queued"] += 1
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", default=str(RUNS_ROOT))
    ap.add_argument("--since", default="", help="YYYYMMDD; skip runs older than this")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    os.environ[D.ENV_FLAG] = "1"          # the detector is opt-in; this is the opt-in
    runs = candidate_runs(pathlib.Path(a.runs_root), a.since, a.limit)
    if not runs:
        print("nothing to sweep")
        return 0

    prov, calls = None, {"n": 0}
    if not a.dry_run:
        import claude_cli_provider as CCP
        prov = CCP.ClaudeCLIProvider()

    def ask(system, user):
        calls["n"] += 1
        return parse_json_object(prov.complete(system=system, user=user,
                                               max_tokens=3000).text)

    print("sweeping %d run(s)%s" % (len(runs), "  [DRY RUN]" if a.dry_run else ""))
    for d in runs:
        try:
            r = sweep_one(d, ask, a.dry_run)
            print("  %-46s %-22s defs=%-2d flagged=%-2d queued=%d"
                  % (r["run"][:46], r["status"], r["definitions"], r["flagged"],
                     r["queued"]))
        except Exception as e:                                    # noqa: BLE001
            # a sweep failure is a sweep failure. It must never look like a clean day.
            print("  %-46s SWEEP_ERROR %s: %s" % (d.name[:46], type(e).__name__,
                                                  str(e)[:160]), file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    print("detector calls: %d" % calls["n"])
    print("queue: %s" % json.dumps(STORE.summary()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
