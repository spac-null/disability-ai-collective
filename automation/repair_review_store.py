"""The durable record behind human-routed repair: an open queue, and ground truth.

Two append-only JSONL files. Append-only because this is evidence: a decision an editor
made on a Tuesday is not improved by being rewritten on a Thursday, and the whole value of
the store is that it can be replayed later to design a classifier against real labels.

  FINDINGS.jsonl   one row per flagged commitment the sweep found. Written once.
  DECISIONS.jsonl  one row per human action. A finding may collect several -- routed, then
                   accepted or rejected -- and the last row for a finding_id is its state.

WHY THE CLASSIFIER'S PREDICTION IS STORED AND NEVER SHOWN.

Every finding carries what the frozen R1-R4 dispatcher WOULD have said. The editor is never
shown it, before or during the decision. Two reasons, and the second is the one that matters:

  1. An editor shown a machine suggestion agrees with it more often than an editor who is
     not. The labels would then measure the classifier's influence rather than the defect.
  2. Labels collected independently are a held-out evaluation set for free. Predictions made
     before the human decided, recorded at the same moment, never revealed -- that is exactly
     the data the redesign needs, and it only exists if nobody looks.

So `classifier_prediction` is written by the sweep and read only by an evaluation pass. The
review tool must not print it. A test asserts that.
"""
import datetime
import hashlib
import json
import os
import pathlib

ROOT = pathlib.Path(os.environ.get("CRIPMINDS_REPAIR_REVIEW_DIR",
                                   "/srv/data/cripminds-repair-review"))
FINDINGS = "FINDINGS.jsonl"
DECISIONS = "DECISIONS.jsonl"

# what an editor may choose. IGNORE is a first-class answer, not a failure to decide.
LOCAL = "LOCAL"
RELATIONAL = "RELATIONAL"
IGNORE = "IGNORE"
ROUTES = (LOCAL, RELATIONAL, IGNORE)

ACCEPT = "ACCEPT"
REJECT = "REJECT"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def finding_id(run_id: str, term: str, span: str) -> str:
    """Stable across sweeps, so re-sweeping a run cannot duplicate a finding."""
    return hashlib.sha256(("%s\x00%s\x00%s" % (run_id, term, span))
                          .encode("utf-8")).hexdigest()[:16]


def _path(name: str, root=None) -> pathlib.Path:
    p = pathlib.Path(root or ROOT)
    p.mkdir(parents=True, exist_ok=True)
    return p / name


def _read(name: str, root=None) -> list:
    p = _path(name, root)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _append(name: str, row: dict, root=None) -> dict:
    with _path(name, root).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")
    return row


SWEPT = "SWEPT.jsonl"


def swept(root=None) -> set:
    """Runs the sweep has already spent a detector call on.

    Held here rather than inferred from an artifact in the run directory. A run with no
    flagged commitment leaves no finding, so the queue cannot answer "was this swept?",
    and a marker file makes the guard depend on write access to a production directory.
    One plan must cost at most one detector call even if that write fails.
    """
    return {r["run_id"] for r in _read(SWEPT, root)}


def record_sweep(run_id: str, status: str, definitions: int, flagged: int, root=None):
    return _append(SWEPT, {"run_id": run_id, "status": status,
                           "definitions": definitions, "flagged": flagged,
                           "at": _now()}, root)


def findings(root=None) -> list:
    return _read(FINDINGS, root)


def decisions(root=None) -> list:
    return _read(DECISIONS, root)


def record_finding(row: dict, root=None):
    """Write a finding once. Returns None if this finding_id is already on file."""
    fid = row["finding_id"]
    if any(f["finding_id"] == fid for f in findings(root)):
        return None
    row = dict(row, recorded_at=_now())
    return _append(FINDINGS, row, root)


def record_decision(finding_id_: str, action: str, editor: str, **fields):
    root = fields.pop("root", None)
    row = {"finding_id": finding_id_, "action": action, "editor": editor,
           "at": _now()}
    row.update(fields)
    return _append(DECISIONS, row, root)


def state(root=None) -> dict:
    """finding_id -> the latest decision row, or None when still open."""
    st = {f["finding_id"]: None for f in findings(root)}
    for d in decisions(root):
        st[d["finding_id"]] = d
    return st


def open_findings(root=None) -> list:
    """Findings with no decision yet, oldest first -- a queue, not a ranking."""
    st = state(root)
    return [f for f in findings(root) if st.get(f["finding_id"]) is None]


def resolved(root=None) -> list:
    """(finding, last decision) for everything an editor has answered."""
    st = state(root)
    by = {f["finding_id"]: f for f in findings(root)}
    return [(by[k], v) for k, v in st.items() if v is not None and k in by]


def ground_truth(root=None) -> list:
    """The labelled set: one row per finding an editor ROUTED, with the route they chose,
    what the repair did if one was made, and whether they accepted it.

    This is the thing the classifier redesign is for. `classifier_prediction` travels with
    it so the frozen R1-R4 can be scored afterwards -- against labels it never influenced.
    """
    by_f = {f["finding_id"]: f for f in findings(root)}
    routed, latest = {}, {}
    for d in decisions(root):
        if d.get("action") in ROUTES:
            routed[d["finding_id"]] = d
        latest[d["finding_id"]] = d
    out = []
    for fid, r in routed.items():
        f = by_f.get(fid)
        if f is None:
            continue
        last = latest[fid]
        out.append({
            "finding_id": fid,
            "run_id": f.get("run_id"), "plan_dir": f.get("plan_dir"),
            "term": f.get("term"), "span": f.get("span"),
            "status": f.get("status"), "detector_reason": f.get("detector_reason"),
            "gloss": f.get("gloss"), "declared_evidence": f.get("declared_evidence"),
            "human_route": r["action"], "routed_by": r.get("editor"),
            "routed_at": r.get("at"), "route_note": r.get("note", ""),
            "repair_outcome": last.get("action") if last.get("action") in
                              (ACCEPT, REJECT) else None,
            "repair_note": last.get("note", "") if last is not r else "",
            "repaired_gloss": last.get("repaired_gloss"),
            # never shown to the editor; written before they chose
            "classifier_prediction": f.get("classifier_prediction"),
        })
    return sorted(out, key=lambda r: r["routed_at"] or "")


def summary(root=None) -> dict:
    gt = ground_truth(root)
    routes, agree, n_pred = {}, 0, 0
    for r in gt:
        routes[r["human_route"]] = routes.get(r["human_route"], 0) + 1
        p = (r.get("classifier_prediction") or {}).get("dispatch")
        if p:
            n_pred += 1
            # the classifier only ever claims RELATIONAL or not; IGNORE is a human answer
            # it does not model, so agreement is only defined on the other two.
            if r["human_route"] in (LOCAL, RELATIONAL):
                agree += int((p == RELATIONAL) == (r["human_route"] == RELATIONAL))
    return {"findings": len(findings(root)), "open": len(open_findings(root)),
            "resolved": len(resolved(root)), "labelled": len(gt),
            "routes": routes, "with_prediction": n_pred,
            "classifier_agreement_on_local_vs_relational": agree}
