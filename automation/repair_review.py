"""Human-routed repair. The editor decides the type; the machine only does the work.

The automatic dispatcher is frozen and not trusted (CONCEPT_ANCHOR_CLASSIFIER_NEEDS_REDESIGN:
on the first genuinely out-of-sample cases it produced two relational dispatches and both
were wrong). Everything either side of that choice is proven and is used unchanged:

  detector          definition_claim_shadow            80554bd, zero authority
  LOCAL repair      definition_repair_compiler         span-level, protected text copied
  RELATIONAL repair commitment_slice_repair            slice + obligations + prohibition
  obligations       obligation_policy                  d4bd9ea, fixed in advance

So the editor supplies the one judgement no rule has earned yet, and nothing else changes.

WHAT THIS TOOL WILL NOT DO

  * It will not show the frozen classifier's opinion. It is recorded at sweep time and
    revealed to nobody, so the labels this collects stay independent of it and can be used
    to score it later. `show` prints the evidence and the claim; that is the material the
    decision should rest on.
  * It will not change a published article, a draft, Writer input, or any plan in place.
    `accept` writes a repaired architecture beside the finding and records the approval.
    Putting it to work is a separate, explicitly human act.
  * It will not hold publication. Nothing here is read by the publisher.

Commands
  list                       open findings, oldest first
  show <id>                  the claim, the gloss, the declared evidence
  route <id> LOCAL|RELATIONAL|IGNORE [--note ...]
                             records the human label. LOCAL and RELATIONAL then spend ONE
                             model call to build the repair; IGNORE spends none.
  accept <id> [--note ...]   approve the proposed repair
  reject <id> [--note ...]   refuse it, with the reason
  labels                     the ground truth collected so far
  score                      how the frozen classifier would have done, against labels it
                             never saw. Read this, do not act on it.
"""
import argparse
import datetime
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "orchestrator"))

from new_engine_v1 import definition_repair_compiler as DRC    # noqa: E402
from new_engine_v1 import commitment_slice_repair as CSR       # noqa: E402
from new_engine_v1 import obligation_policy as OP              # noqa: E402
from new_engine_v1.provider import parse_json_object           # noqa: E402
import repair_review_store as STORE                            # noqa: E402

W = 96


def _editor() -> str:
    return (os.environ.get("CRIPMINDS_EDITOR")
            or os.environ.get("USER") or "unknown")


def _find(fid: str):
    for f in STORE.findings():
        if f["finding_id"] == fid or f["finding_id"].startswith(fid):
            return f
    return None


def _load_plan(f: dict):
    d = pathlib.Path(f["plan_dir"])
    arch = json.loads((d / "ARCHITECTURE.json").read_text(encoding="utf-8"))
    ledger = None
    for name in ("FINAL_EVIDENCE_MANIFEST.json", "LEDGER.json"):
        p = d / name
        if p.exists():
            j = json.loads(p.read_text(encoding="utf-8"))
            j = j.get("facts", j) if isinstance(j, dict) else j
            ledger = j if isinstance(j, dict) else {x["fact_id"]: x for x in j}
            break
    shadow = json.loads((d / "DEFINITION_CLAIM_SHADOW.json").read_text(encoding="utf-8"))
    return d, arch, ledger, shadow


def cmd_list(a) -> int:
    rows = STORE.open_findings()
    if not rows:
        print("queue empty")
        return 0
    print("%-10s %-26s %-28s %s" % ("id", "term", "run", "flagged span"))
    print("-" * W)
    for f in rows:
        print("%-10s %-26s %-28s %s"
              % (f["finding_id"][:10], (f["term"] or "")[:26],
                 (f["run_id"] or "")[:28], repr(f["span"])[:40]))
    print("\n%d open. `show <id>` for the evidence." % len(rows))
    return 0


def cmd_show(a) -> int:
    f = _find(a.id)
    if not f:
        print("no such finding: %s" % a.id)
        return 1
    print("=" * W)
    print("FINDING   %s" % f["finding_id"])
    print("RUN       %s" % f["run_id"])
    print("TERM      %s" % f["term"])
    print()
    print("THE DEFINITION AS WRITTEN")
    print("  %s" % f["gloss"])
    print()
    print("THE COMMITMENT THE EVIDENCE DOES NOT ESTABLISH  [%s]" % f["status"])
    print("  %r" % f["span"])
    print("  detector: %s" % f["detector_reason"])
    print()
    print("THE EVIDENCE THIS DEFINITION DECLARES")
    for e in (f.get("declared_evidence") or []):
        print("  %-6s %s" % (e["fact_id"], e["proposition"]))
        if e.get("support_span"):
            print("         quoted: %s" % e["support_span"][:300])
    print()
    print("EVERY COMMITMENT IN THIS DEFINITION")
    for c in (f.get("all_claims") or []):
        mark = ">>" if c.get("commitment") == f["span"] else "  "
        print("  %s %-30s %r" % (mark, c.get("status"), (c.get("commitment") or "")[:52]))
    print()
    print("-" * W)
    print("Is the unsupported part a RELATION between two things the evidence establishes")
    print("separately -- or a value, attribute, attribution or degree hanging off the term?")
    print()
    print("  route %s RELATIONAL   two licensed concepts, the link between them is not"
          % f["finding_id"][:10])
    print("  route %s LOCAL        one concept, with something unsupported attached"
          % f["finding_id"][:10])
    print("  route %s IGNORE       no repair warranted" % f["finding_id"][:10])
    return 0


def _ask(prov):
    def ask(system, user):
        return parse_json_object(prov.complete(system=system, user=user,
                                               max_tokens=2500).text)
    return ask


def cmd_route(a) -> int:
    f = _find(a.id)
    if not f:
        print("no such finding: %s" % a.id)
        return 1
    route = a.route.upper()
    if route not in STORE.ROUTES:
        print("route must be one of %s" % ", ".join(STORE.ROUTES))
        return 1

    STORE.record_decision(f["finding_id"], route, _editor(), note=a.note or "")
    print("recorded: %s routed %s by %s" % (f["finding_id"][:10], route, _editor()))

    if route == STORE.IGNORE:
        print("no repair, no model call. The label is kept.")
        return 0

    d, arch, ledger, shadow = _load_plan(f)
    os.environ[DRC.ENV_FLAG] = "1"
    os.environ[CSR.ENV_FLAG] = "1"
    import claude_cli_provider as CCP
    prov = CCP.ClaudeCLIProvider()
    ask = _ask(prov)
    out_dir = d / "repair-review" / f["finding_id"]
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\nbuilding the %s repair -- one call, no retry ..." % route)
    mod = DRC if route == STORE.LOCAL else CSR
    art = mod.run(ask, arch, ledger, shadow, f["term"], out_dir=out_dir)

    status = art.get("status")
    print("  status: %s" % status)
    if status != "REPAIRED":
        print("  reason: %s" % (art.get("error") or "")[:300])
        for e in (art.get("validation_errors") or [])[:5]:
            print("    - %s" % str(e)[:160])
        print("\nThe repair did not pass its own checks, so there is nothing to approve.")
        print("This is a refusal, not a crash, and the route you chose is already recorded.")
        return 0

    repaired = art.get("repaired_architecture") or {}
    new_gloss = (repaired.get("definitions") or {}).get(f["term"], "")
    print("\n  BEFORE  %s" % f["gloss"])
    print("  AFTER   %s" % new_gloss)
    if route == STORE.RELATIONAL:
        plan = art.get("edit_plan") or {}
        if plan.get("prohibition"):
            print("\n  house rule: %s" % plan["prohibition"])
        try:
            sl = art.get("slice") or {}
            ir = sl.get("definition_ir") or {}
            tgt = next((u for u in ir.get("units", [])
                        if u.get("unit_id") == sl.get("definition_target")), None)
            if tgt is not None:
                obs = OP.select(ir, tgt, plan, ledger)
                n = sum(len(v) for v in obs.values()) if isinstance(obs, dict) else len(obs)
                print("  obligations: %d selected by policy d4bd9ea (unchanged)" % n)
        except Exception as e:                                    # noqa: BLE001
            print("  obligations: not shown (%s)" % type(e).__name__)
    (out_dir / "PROPOSED.json").write_text(
        json.dumps({"finding_id": f["finding_id"], "route": route,
                    "repaired_architecture": repaired,
                    "before_gloss": f["gloss"], "after_gloss": new_gloss},
                   indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print("\n  proposal: %s" % (out_dir / "PROPOSED.json"))
    print("\n  accept %s   or   reject %s --note '...'"
          % (f["finding_id"][:10], f["finding_id"][:10]))
    return 0


def _proposal(f):
    p = pathlib.Path(f["plan_dir"]) / "repair-review" / f["finding_id"] / "PROPOSED.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def cmd_accept(a) -> int:
    f = _find(a.id)
    if not f:
        print("no such finding: %s" % a.id)
        return 1
    prop = _proposal(f)
    if prop is None:
        print("there is no proposed repair for %s -- route it first" % a.id)
        return 1
    STORE.record_decision(f["finding_id"], STORE.ACCEPT, _editor(),
                          note=a.note or "", route=prop["route"],
                          repaired_gloss=prop["after_gloss"])
    print("ACCEPTED %s by %s" % (f["finding_id"][:10], _editor()))
    print("  the repaired architecture is at %s"
          % (pathlib.Path(f["plan_dir"]) / "repair-review" / f["finding_id"]))
    print("  nothing downstream has changed. Putting it to work is a separate, human step.")
    return 0


def cmd_reject(a) -> int:
    f = _find(a.id)
    if not f:
        print("no such finding: %s" % a.id)
        return 1
    prop = _proposal(f) or {}
    STORE.record_decision(f["finding_id"], STORE.REJECT, _editor(),
                          note=a.note or "", route=prop.get("route"))
    print("REJECTED %s by %s%s" % (f["finding_id"][:10], _editor(),
                                   " -- %s" % a.note if a.note else ""))
    print("  the rejection is the valuable part: it says the repair was wrong, not the flag.")
    return 0


def cmd_labels(a) -> int:
    gt = STORE.ground_truth()
    if not gt:
        print("no labels yet")
        return 0
    print("%-10s %-24s %-12s %-8s %s" % ("id", "term", "route", "outcome", "span"))
    print("-" * W)
    for r in gt:
        print("%-10s %-24s %-12s %-8s %s"
              % (r["finding_id"][:10], (r["term"] or "")[:24], r["human_route"],
                 r["repair_outcome"] or "-", repr(r["span"])[:34]))
    print()
    print(json.dumps(STORE.summary(), indent=1))
    return 0


def cmd_score(a) -> int:
    """How the frozen classifier would have done, against labels it never influenced."""
    gt = [r for r in STORE.ground_truth()
          if r["human_route"] in (STORE.LOCAL, STORE.RELATIONAL)
          and (r.get("classifier_prediction") or {}).get("dispatch")]
    if not gt:
        print("no labelled cases with a recorded prediction yet")
        return 0
    tp = fp = tn = fn = 0
    for r in gt:
        pred_rel = (r["classifier_prediction"]["dispatch"] == STORE.RELATIONAL)
        true_rel = (r["human_route"] == STORE.RELATIONAL)
        tp += int(pred_rel and true_rel)
        fp += int(pred_rel and not true_rel)
        tn += int(not pred_rel and not true_rel)
        fn += int(not pred_rel and true_rel)
    print("frozen R1-R4 against %d independent human labels" % len(gt))
    print("  relational, and human agreed      %d" % tp)
    print("  relational, and human said local  %d   <- the dangerous direction" % fp)
    print("  refused,    and human said local  %d" % tn)
    print("  refused,    and human said rel.   %d" % fn)
    print("\nEvaluation only. The classifier is frozen and routes nothing.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("show"); p.add_argument("id"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("route"); p.add_argument("id"); p.add_argument("route")
    p.add_argument("--note", default=""); p.set_defaults(fn=cmd_route)
    p = sub.add_parser("accept"); p.add_argument("id"); p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_accept)
    p = sub.add_parser("reject"); p.add_argument("id"); p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_reject)
    sub.add_parser("labels").set_defaults(fn=cmd_labels)
    sub.add_parser("score").set_defaults(fn=cmd_score)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
