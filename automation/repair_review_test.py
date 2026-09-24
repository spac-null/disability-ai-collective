"""Static tests for human-routed repair mode. No network, no provider, no model call.

The properties worth asserting are mostly about what this must NOT do: not leak the frozen
classifier's opinion to the editor, not hold publication, not touch a plan in place.
"""
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import repair_review_store as STORE          # noqa: E402

FAIL = []


def ok(cond, label):
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        FAIL.append(label)


TMP = pathlib.Path(tempfile.mkdtemp(prefix="repair-review-test-"))

FINDING = {
    "finding_id": STORE.finding_id("run-A", "cutoff wavelength",
                                   "set by the bandgap energy"),
    "run_id": "run-A", "plan_dir": str(TMP / "plan"),
    "term": "cutoff wavelength", "span": "set by the bandgap energy",
    "status": "NOT_ESTABLISHED", "detector_reason": "never stated",
    "gloss": "the long-wavelength edge, set by the bandgap energy",
    "declared_evidence": [{"fact_id": "F86", "proposition": "...bandgap energy.",
                           "support_span": "...bandgap energy."}],
    "all_claims": [{"commitment": "set by the bandgap energy",
                    "status": "NOT_ESTABLISHED"}],
    "classifier_prediction": {"dispatch": "RELATIONAL", "reason": "two ends",
                              "E1": ["cutoff"], "E2": ["bandgap"]},
}

print("\n== the store is append-only and idempotent ==")
ok(STORE.record_finding(FINDING, root=TMP) is not None, "a finding is recorded")
ok(STORE.record_finding(FINDING, root=TMP) is None,
   "re-sweeping the same run cannot duplicate it")
ok(len(STORE.findings(root=TMP)) == 1, "exactly one row on file")
ok(STORE.finding_id("run-A", "t", "s") == STORE.finding_id("run-A", "t", "s"),
   "finding_id is stable")
ok(STORE.finding_id("run-A", "t", "s") != STORE.finding_id("run-B", "t", "s"),
   "and distinguishes runs")

print("\n== the queue ==")
fid = FINDING["finding_id"]
ok([f["finding_id"] for f in STORE.open_findings(root=TMP)] == [fid],
   "a new finding is open")
STORE.record_decision(fid, STORE.LOCAL, "editor-1", note="attribute", root=TMP)
ok(STORE.open_findings(root=TMP) == [], "routing takes it off the open queue")
ok(len(STORE.resolved(root=TMP)) == 1, "and it shows as resolved")
STORE.record_decision(fid, STORE.ACCEPT, "editor-1", route=STORE.LOCAL,
                      repaired_gloss="the long-wavelength edge", root=TMP)
ok(len(STORE.decisions(root=TMP)) == 2,
   "a second decision appends rather than overwriting -- the route is still on file")

print("\n== ground truth ==")
gt = STORE.ground_truth(root=TMP)
ok(len(gt) == 1, "one labelled row")
r = gt[0]
ok(r["human_route"] == STORE.LOCAL, "the human's route is the label")
ok(r["repair_outcome"] == STORE.ACCEPT, "and the accept/reject outcome travels with it")
ok(r["repaired_gloss"] == "the long-wavelength edge", "as does what the repair produced")
ok(r["span"] == FINDING["span"] and r["gloss"] == FINDING["gloss"],
   "with the claim and the definition it came from")
ok(r["declared_evidence"] == FINDING["declared_evidence"],
   "and the evidence the decision was made against")
ok(r["classifier_prediction"]["dispatch"] == "RELATIONAL",
   "the frozen classifier's prediction is retained for scoring")

print("\n== the classifier's opinion is recorded and never displayed ==")
src = (pathlib.Path(__file__).resolve().parent / "repair_review.py").read_text()
shown = [ln.strip() for ln in src.splitlines()
         if "classifier_prediction" in ln and ln.strip().startswith("print")]
ok(shown == [], "repair_review.py never prints classifier_prediction: %s" % shown)
body = src.split("def cmd_score")[0]
ok("classifier_prediction" not in body,
   "and no command except `score` reads it at all")
ok("classifier_prediction" in src.split("def cmd_score")[1],
   "`score` does read it -- evaluation is the one place it is allowed")

print("\n== IGNORE is a first-class label and costs nothing ==")
f2 = dict(FINDING, finding_id=STORE.finding_id("run-B", "t2", "s2"), run_id="run-B",
          term="t2", span="s2")
STORE.record_finding(f2, root=TMP)
STORE.record_decision(f2["finding_id"], STORE.IGNORE, "editor-1", note="not worth it",
                      root=TMP)
gt = STORE.ground_truth(root=TMP)
ok(any(x["human_route"] == STORE.IGNORE for x in gt),
   "IGNORE is kept as a label, not discarded")
ok(next(x for x in gt if x["human_route"] == STORE.IGNORE)["repair_outcome"] is None,
   "and carries no repair outcome, because no repair was built")
rsrc = src.split("def cmd_route")[1].split("def ")[0]
ok("IGNORE" in rsrc and rsrc.index("return 0") < rsrc.index("ClaudeCLIProvider"),
   "route returns before constructing a provider when the editor chose IGNORE")

print("\n== summary counts what it says it counts ==")
s = STORE.summary(root=TMP)
ok(s["findings"] == 2 and s["labelled"] == 2, "two findings, two labels: %s" % s)
ok(s["routes"].get(STORE.LOCAL) == 1 and s["routes"].get(STORE.IGNORE) == 1,
   "routes tallied: %s" % s["routes"])

print("\n== no publication authority anywhere in this mode ==")


def code_only(path: pathlib.Path) -> str:
    """Executable source with docstrings and comments removed.

    Checking raw text made the first version of this test fail on its own docstring, which
    PROMISES not to touch _posts. A prose promise and a call are opposites, and a test that
    cannot tell them apart is checking the wrong thing.
    """
    import ast, io, tokenize
    src = path.read_text(encoding="utf-8")
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            continue
        out.append(tok.string if tok.type != tokenize.STRING else '""')
    stripped = " ".join(out)
    ast.parse(src)                       # the file must still be valid Python
    return stripped


for name in ("repair_review.py", "repair_detector_sweep.py", "repair_review_store.py"):
    t = code_only(pathlib.Path(__file__).resolve().parent / name)
    for forbidden in ("publish_best", "publish_candidate", "_posts", "publication_eligible",
                      "git"):
        ok(forbidden not in t, "%s calls nothing named %r" % (name, forbidden))

print("\n== the sweep cannot be confused for an in-pipeline hook ==")
t = (pathlib.Path(__file__).resolve().parent / "repair_detector_sweep.py").read_text()
ok("composition" not in t.replace("composition would put", ""),
   "the sweep does not import or call composition")
ok("DEFINITION_CLAIM_SHADOW.json" in t,
   "it marks a swept run so one plan costs at most one detector call, ever")

print("\n" + ("ALL PASS" if not FAIL else "FAILURES: %d\n  - %s"
                                          % (len(FAIL), "\n  - ".join(FAIL))))
sys.exit(1 if FAIL else 0)
