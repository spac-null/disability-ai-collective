"""freeze_run.py -- freeze the pilot's six subjects and write the experiment manifest.

Run once. Section 10: the split is fixed BEFORE any new output exists, so no evaluation
subject can be chosen after seeing how it performed.
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from evidence_to_draft_pilot import subjects as S                  # noqa: E402

E = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/evidence-to-draft-pilot")

# THE SPLIT, chosen on source and stage availability only (section 10).
#
# development -- prompts are developed and the harness is debugged on these two:
#   9381ae93  moral-philosopher obituary; a READER-stage hold, i.e. the most advanced
#             retained draft class, which is section 10's "initially usable draft"
#   09d602f1  131-fact trend piece; the fact-dense end of the difficulty range
#
# held_out -- prompts are frozen before these are generated or evaluated:
#   d41d6fbc  art theft, Italian + English sources, many actors
#   40294a3a  Italian education policy, Italian + English sources, and the ONE subject
#             whose retained plan was written against the CURRENT evidence-hierarchy
#             contract rather than the pre-2026-09-11 one
#   8a0dab48  wheelchair duet; 126 facts compressed into a 431-word historical draft,
#             the hardest narrative structure in the pool, and a second READER-stage case
#   8556915b  speech-BCI preprint; technical/scientific register
DEV = ["production-20260909T073451Z-9381ae93",
       "production-20260910T084202Z-09d602f1"]
HELD = ["production-20260909T112754Z-d41d6fbc",
        "production-20260915T072045Z-40294a3a",
        "production-20260910T190530Z-8a0dab48",
        "production-20260907T154937Z-8556915b"]


def main():
    rows = S.scan()
    el = S.eligible_v2(rows)
    by = {r["run"]: r for r in el}
    for run in DEV + HELD:
        if not by[run]["eligible"]:
            raise SystemExit("%s is not eligible: %s"
                             % (run, by[run]["ineligible_reason"]))

    man = {
        "pilot": "evidence-to-draft-pilot",
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "not_publishable": "NOT_PUBLISHABLE_EXPERIMENT",
        "development_subjects": DEV,
        "held_out_subjects": HELD,
        "subjects": {},
    }
    for split, runs in (("development", DEV), ("held_out", HELD)):
        for run in runs:
            f = S.freeze_subject(run, split=split)
            f["plan_contract"] = by[run]["plan_contract"]
            d = E / "subjects" / run
            d.mkdir(parents=True, exist_ok=True)
            gen = dict(f)
            ev = gen.pop("evaluation_only")
            ev["historical_failure_stage"] = by[run]["historical_failure_stage"]
            (d / "SUBJECT.json").write_text(
                json.dumps(gen, indent=1, ensure_ascii=False))
            (d / "EVALUATION_ONLY.json").write_text(
                json.dumps(ev, indent=1, ensure_ascii=False))
            man["subjects"][run] = {k: f[k] for k in (
                "split", "subject", "source_set_hash", "ledger_sha256", "plan_sha256",
                "ledger_facts", "languages", "plan_contract")}
            print("%-11s %s facts=%3d langs=%-8s %s"
                  % (split, run, f["ledger_facts"], ",".join(f["languages"]),
                     f["subject"][:46]))

    man["excluded"] = [{"run": r["run"], "reason": r["ineligible_reason"]}
                       for r in el if not r["eligible"]]
    man["eligible_pool_size"] = sum(1 for r in el if r["eligible"])
    man["scanned_runs"] = len(rows)
    (E / "EXPERIMENT_MANIFEST.json").write_text(
        json.dumps(man, indent=1, ensure_ascii=False))
    print("\nfrozen %d subjects | excluded %d | eligible pool %d of %d scanned"
          % (len(man["subjects"]), len(man["excluded"]),
             man["eligible_pool_size"], len(rows)))


if __name__ == "__main__":
    main()
