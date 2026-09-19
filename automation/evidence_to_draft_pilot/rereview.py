#!/usr/bin/env python3
"""
rereview.py -- diagnostic re-evaluation v2 with COMPLETE frozen evidence.

    python3 evidence_to_draft_pilot/rereview.py --split development
    python3 evidence_to_draft_pilot/rereview.py --split held_out

Bounded to 12 calls total: one fresh Claude and one fresh Codex review per subject.

WHAT IS DIFFERENT FROM V1, and only this:
  * the reviewer receives the WHOLE retained source set, not a 5,000-character prefix
    of each source;
  * the rubric adds EVIDENCE_NOT_VISIBLE as an explicit answer, so a reviewer is never
    forced to call something unsupported when it might sit in material it cannot see;
  * the actual request text is persisted, not just its hash.

WHAT IS DELIBERATELY UNCHANGED: the same articles, the same frozen shuffle map, the same
models and settings, the same two reviewers, the same core rubric, blind to arm identity.
No article, plan or extraction is regenerated.

THIS IS NOT A CONFIRMATORY RERUN. It is diagnostic re-evaluation after exposure: the
v1 results have been read, and the defect that motivated it is known. It is recorded as
evaluation version 2 alongside v1, never replacing it. The original A/B preference
result stands as the v1 record.

NO RERUN UNTIL AGREEMENT. One call per reviewer per subject. Disagreements are persisted,
not resolved, and there is no tie-breaker model.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from evidence_to_draft_pilot import budget as BU                   # noqa: E402
from evidence_to_draft_pilot import evidence_delivery as ED        # noqa: E402
from evidence_to_draft_pilot import judge as JG                    # noqa: E402
import claude_cli_provider as CC                                   # noqa: E402
import codex_cli_provider as CX                                    # noqa: E402

V1 = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                  "evidence-to-draft-pilot")
OUT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                   "evidence-to-draft-pilot-audit-v2")

CLAUDE_MODEL = "claude-opus-5"
CODEX_MODEL = "gpt-5.6-luna"
CODEX_EFFORT = "medium"

PROMPT_VERSION = "blind-review-v2-full-evidence"

# The v1 rubric, plus the one answer v1 could not express.
EXTRA_RULE = """

EVIDENCE VISIBILITY. You are being shown the COMPLETE retained source set for this
article. If a source is marked as truncated, material may exist beyond what you can see.

For any factual objection, you must choose one of:
  - "UNSUPPORTED" -- you read the sources and they do not carry this claim;
  - "CONTRADICTED" -- the sources assert something incompatible with it;
  - "EVIDENCE_NOT_VISIBLE" -- you could not check because the relevant source text was
    not delivered to you.

Put that word in the "status" field of each objection. Do not report UNSUPPORTED for
something you simply could not see. Searching the sources properly before objecting is
part of the task: these documents are long, and a claim is often supported far from the
start of a source."""


def review_system() -> str:
    return JG.REVIEW_SYSTEM.replace(
        '   "material_unsupported_claims": [\n'
        '     {"article_span": "exact quote from the article",\n'
        '      "why": "what the sources do not carry",\n'
        '      "source_passage": "the passage that fails to carry it, or NONE_FOUND"}],',
        '   "material_unsupported_claims": [\n'
        '     {"article_span": "exact quote from the article",\n'
        '      "why": "what the sources do not carry",\n'
        '      "status": "UNSUPPORTED|CONTRADICTED|EVIDENCE_NOT_VISIBLE",\n'
        '      "source_passage": "the passage that fails to carry it, or NONE_FOUND"}],'
    ) + EXTRA_RULE


def build_prompt(subject: dict, view: dict, labelled: dict) -> str:
    parts = ["THE COMMISSIONING SUBJECT\n%s" % subject["subject"],
             "THE SOURCE MATERIAL (complete retained set)\n%s" % view["sources_block"]]
    for label in sorted(labelled):
        parts.append("=== %s ===\n%s" % (label, labelled[label]))
    parts.append("Review every candidate above. Reply with one JSON object.")
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["development", "held_out"], required=True)
    args = ap.parse_args()

    man = json.loads((V1 / "EXPERIMENT_MANIFEST.json").read_text())
    runs = man["development_subjects" if args.split == "development"
               else "held_out_subjects"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "requests").mkdir(exist_ok=True)
    ledger = BU.Ledger(OUT / "ledger", subscription_cap=12)

    claude = CC.get_provider(CLAUDE_MODEL)
    codex = CX.get_provider(CODEX_MODEL, effort=CODEX_EFFORT)
    print("budget before: %s" % json.dumps(ledger.summary()))

    manifest_entries = []
    for run in runs:
        subj = json.loads((V1 / "subjects" / run / "SUBJECT.json").read_text())
        view = ED.evidence_view(subj)
        # The SAME articles and the SAME frozen shuffle map as v1.
        variants = {}
        for arm in ("A", "B"):
            p = V1 / "variants" / run / ("%s.md" % arm)
            if p.exists():
                t = p.read_text()
                variants[arm] = t.split("-->\n\n", 1)[-1]
        if len(variants) < 2:
            print("  %s: only %d variant(s)" % (run[-8:], len(variants)))
            continue
        smap = JG.shuffle_map(run, sorted(variants))
        labelled = {label: variants[arm] for label, arm in smap.items()}
        prompt = build_prompt(subj, view, labelled)
        system = review_system()

        entry = dict(view)
        entry.pop("sources_block")
        entry["request_sha256"] = BU.sha256_text(system + prompt)
        entry["request_chars"] = len(system) + len(prompt)
        entry["shuffle_map"] = smap
        manifest_entries.append(entry)
        # The sanitised request, retained so it can be INSPECTED, not only hashed.
        (OUT / "requests" / ("%s.txt" % run)).write_text(
            "=== SYSTEM ===\n%s\n\n=== USER ===\n%s" % (system, prompt))

        print("  %s  evidence %s: retained %d, delivered %d (v1 delivered %d)"
              % (run[-8:], view["evidence_view_status"],
                 view["retained_total_chars"], view["delivered_total_chars"],
                 view["v1_would_have_delivered_chars"]))

        reviews = {}
        for who, prov, model, eff in (("claude", claude, CLAUDE_MODEL, None),
                                      ("codex", codex, CODEX_MODEL, CODEX_EFFORT)):
            cell = "rereview:%s:%s" % (who, run)
            if ledger.done(cell):
                reviews[who] = ledger.load_cell(cell)["result"]
                print("     %-6s cached" % who)
                continue
            ledger.reserve(provider="%s-cli-subscription"
                           % ("claude" if who == "claude" else "codex"))
            t0 = time.time()
            try:
                comp = prov.complete(system, prompt)
                obj, errs = JG.parse_review(comp.text)
                r = {"status": "OK" if obj else "REVIEW_REPLY_UNUSABLE",
                     "parse_errors": errs, "review": obj, "shuffle_map": smap,
                     "provider": comp.identity(),
                     "evaluation_version": 2,
                     "assessment_not_owner_judgement": True,
                     "not_independent_fact_checking": True}
                if obj:
                    r["by_label"] = JG.usable_objections(obj)
                    r["by_arm"] = {smap[k]: v for k, v in r["by_label"].items()
                                   if k in smap}
                    pref = obj.get("preference") or {}
                    r["preference_by_arm"] = {
                        "best": smap.get(pref.get("best")),
                        "worst": smap.get(pref.get("worst")),
                        "reason": pref.get("reason"),
                        "confidence": pref.get("confidence")}
                err = None
            except Exception as exc:                               # noqa: BLE001
                r, err = {"status": "ERROR"}, str(exc)[:300]
            ledger.record(cell=cell, role="rereview-%s" % who,
                          provider="%s-cli-subscription"
                                   % ("claude" if who == "claude" else "codex"),
                          requested_model=model,
                          resolved_model=(model if who == "claude"
                                          else CX.RESOLVED_MODEL_UNDISCLOSED),
                          prompt_version=PROMPT_VERSION,
                          # THE ACTUAL REQUEST, not a placeholder. v1 logged
                          # input_chars=10 because it hashed the variant-name list.
                          input_text=system + prompt, effort=eff,
                          duration_ms=int((time.time() - t0) * 1000),
                          error_code=("ERROR" if err else None), error_text=err,
                          extra={"calls_issued": 1})
            ledger.save_cell(cell, {"cell": cell, "status": "ERROR" if err else "OK",
                                    "result": r, "error_text": err})
            reviews[who] = r
            print("     %-6s %s" % (who, r.get("status")))

        if all(reviews.get(w, {}).get("status") == "OK" for w in ("claude", "codex")):
            (OUT / ("REVIEW_V2_%s.json" % run)).write_text(json.dumps(
                {"subject_id": run, "evaluation_version": 2,
                 "claude": reviews["claude"], "codex": reviews["codex"]},
                indent=1, ensure_ascii=False))

    ED.write_manifest(OUT, manifest_entries)
    print("\nbudget after: %s" % json.dumps(ledger.summary()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
