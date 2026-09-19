#!/usr/bin/env python3
"""
run_extras.py -- the source-reading subtest (section 14) and the blind reviews (16).

    python3 evidence_to_draft_pilot/run_extras.py --subtest
    python3 evidence_to_draft_pilot/run_extras.py --reviews --split development
    python3 evidence_to_draft_pilot/run_extras.py --reviews --split held_out

Both share the pilot Ledger, so subscription calls and OpenRouter cash are counted
against the same caps as generation, and both are resumable cell by cell.

THE SUBTEST IS SEPARATELY BUDGETED AND SEPARATELY REPORTED. Its extractions are never
fed into arms A, B or C -- section 14 -- so nothing in the article comparison can be
improved or damaged by it without that being an explicit, later decision.
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
from evidence_to_draft_pilot import judge as JG                    # noqa: E402
from evidence_to_draft_pilot import source_reading as SR           # noqa: E402
import claude_cli_provider as CC                                   # noqa: E402
import codex_cli_provider as CX                                    # noqa: E402

ROOT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                    "evidence-to-draft-pilot")
CLAUDE_MODEL = "claude-opus-5"
CODEX_MODEL = "gpt-5.6-luna"
CODEX_EFFORT = "medium"


def load_manifest():
    return json.loads((ROOT / "EXPERIMENT_MANIFEST.json").read_text())


def load_subject(run):
    return json.loads((ROOT / "subjects" / run / "SUBJECT.json").read_text())


# ── SECTION 14 ───────────────────────────────────────────────────────────────
def pick_passages(man: dict) -> list:
    """Six bounded passages, chosen for the failure classes section 14 names.

    One per subject, and the two Italian-source subjects contribute their ITALIAN
    source rather than their English one, so multilingual fidelity is actually
    exercised instead of merely being available.
    """
    out = []
    for run in man["development_subjects"] + man["held_out_subjects"]:
        subj = load_subject(run)
        srcs = subj["generation_inputs"]["sources"]
        meta = {s["source_id"]: s for s in subj["source_set"]}
        # Prefer a non-English source where the subject has one.
        non_en = [s for s in srcs
                  if meta.get(s["source_id"], {}).get("detected_language", "en") != "en"]
        pool = non_en or srcs
        # The longest of the preferred pool: a short stub cannot show coverage.
        s = max(pool, key=lambda x: len(x.get("text") or ""))
        out.append({
            "passage_id": "%s::%s" % (run, s.get("source_id")),
            "subject_id": run,
            "source_id": s.get("source_id"),
            "title": s.get("title"),
            "publisher": s.get("publisher"),
            "detected_language":
                meta.get(s["source_id"], {}).get("detected_language", "en"),
            "text": (s.get("text") or "")[:SR.PER_SOURCE_CHARS],
        })
    return out


def run_subtest(ledger: BU.Ledger) -> None:
    man = load_manifest()
    passages = pick_passages(man)
    outdir = ROOT / "extraction"
    outdir.mkdir(exist_ok=True)

    price = SR.verify_model()
    (outdir / "GEMINI_MODEL_VERIFICATION.json").write_text(json.dumps(price, indent=1))
    print("gemini verified: %s  in=$%.9f/tok out=$%.9f/tok  page images sent: %s"
          % (price["model"], price["price_per_input_token_usd"],
             price["price_per_output_token_usd"],
             price["receives_page_images_in_this_test"]))

    claude = CC.get_provider(CLAUDE_MODEL)
    for p in passages:
        doc = p["text"]
        prompt = SR.extraction_prompt(doc)

        # -- Claude, on the subscription -------------------------------------
        cell = "extract:claude:%s" % p["passage_id"]
        if not ledger.done(cell):
            ledger.reserve(provider="claude-cli-subscription")
            t0 = time.time()
            try:
                comp = claude.complete(SR.EXTRACTION_SYSTEM, prompt)
                props, errs = SR.parse_extraction(comp.text)
                res = {"status": "OK", "propositions": props, "parse_errors": errs,
                       "score": SR.score_extraction(props, doc),
                       "provider": comp.identity()}
                err = None
            except Exception as exc:                               # noqa: BLE001
                res, err = {"status": "ERROR"}, str(exc)[:300]
            ledger.record(cell=cell, role="extract-claude",
                          provider="claude-cli-subscription",
                          requested_model=CLAUDE_MODEL, resolved_model=CLAUDE_MODEL,
                          prompt_version=SR.PROMPT_VERSION, input_text=prompt,
                          duration_ms=int((time.time() - t0) * 1000),
                          error_code=("ERROR" if err else None), error_text=err)
            ledger.save_cell(cell, dict(res, passage=p["passage_id"]))
            print("  claude %-52s %s" % (p["passage_id"][-50:],
                                         res.get("score", {}).get("propositions", res["status"])))

        # -- Gemini, on OpenRouter credits -----------------------------------
        cell = "extract:gemini:%s" % p["passage_id"]
        if not ledger.done(cell):
            # Estimate generously so the cap cannot be crossed by a surprise.
            est = (len(prompt) / 3.5) * price["price_per_input_token_usd"] \
                + 8000 * price["price_per_output_token_usd"]
            ledger.reserve(provider="openrouter", cash_estimate_usd=est)
            t0 = time.time()
            try:
                r = SR.call_gemini(SR.EXTRACTION_SYSTEM, prompt)
                props, errs = SR.parse_extraction(r["text"])
                res = {"status": "OK", "propositions": props, "parse_errors": errs,
                       "score": SR.score_extraction(props, doc),
                       "requested_model": r["requested_model"],
                       "resolved_model": r["resolved_model"],
                       "usage": r["usage"], "cash_cost_usd": r["cash_cost_usd"]}
                err, cost, resolved = None, r["cash_cost_usd"], r["resolved_model"]
            except Exception as exc:                               # noqa: BLE001
                res, err, cost = {"status": "ERROR"}, str(exc)[:300], 0.0
                resolved = "UNKNOWN"
            ledger.record(cell=cell, role="extract-gemini", provider="openrouter",
                          requested_model=SR.GEMINI_MODEL, resolved_model=resolved,
                          prompt_version=SR.PROMPT_VERSION, input_text=prompt,
                          duration_ms=int((time.time() - t0) * 1000),
                          cash_cost_usd=cost, openrouter_used=True,
                          error_code=("ERROR" if err else None), error_text=err)
            ledger.save_cell(cell, dict(res, passage=p["passage_id"]))
            print("  gemini %-52s %s  $%.5f"
                  % (p["passage_id"][-50:],
                     res.get("score", {}).get("propositions", res["status"]), cost))

    (outdir / "PASSAGES.json").write_text(json.dumps(
        [{k: v for k, v in p.items() if k != "text"} for p in passages], indent=1))


# ── SECTION 16 ───────────────────────────────────────────────────────────────
def variants_of(ledger: BU.Ledger, run: str) -> dict:
    out = {}
    for arm in ("A", "B", "C"):
        c = ledger.load_cell("%s:%s" % (run, arm))
        if c and c.get("status") == "OK" and (c["result"] or {}).get("article_text"):
            out[arm] = c["result"]["article_text"]
    return out


def run_reviews(ledger: BU.Ledger, split: str) -> None:
    man = load_manifest()
    runs = man["development_subjects" if split == "development" else "held_out_subjects"]
    outdir = ROOT / "reviews"
    outdir.mkdir(exist_ok=True)
    claude = CC.get_provider(CLAUDE_MODEL)
    codex = CX.get_provider(CODEX_MODEL, effort=CODEX_EFFORT)

    for run in runs:
        variants = variants_of(ledger, run)
        if len(variants) < 2:
            print("  %s: only %d variant(s); nothing to compare"
                  % (run[-8:], len(variants)))
            continue
        subj = load_subject(run)
        srcs = subj["generation_inputs"]["sources"]
        reviews = {}
        for who, prov, model, eff in (
                ("claude", claude, CLAUDE_MODEL, None),
                ("codex", codex, CODEX_MODEL, CODEX_EFFORT)):
            cell = "review:%s:%s" % (who, run)
            if ledger.done(cell):
                reviews[who] = ledger.load_cell(cell)["result"]
                print("  %s %-6s cached" % (run[-8:], who))
                continue
            ledger.reserve(provider="%s-cli-subscription"
                           % ("claude" if who == "claude" else "codex"))
            t0 = time.time()
            try:
                r = JG.review_variants(prov, subject_id=run,
                                       subject=subj["subject"], sources=srcs,
                                       variants=variants)
                err = None
            except Exception as exc:                               # noqa: BLE001
                r, err = {"status": "ERROR"}, str(exc)[:300]
            ledger.record(cell=cell, role="review-%s" % who,
                          provider="%s-cli-subscription"
                                   % ("claude" if who == "claude" else "codex"),
                          requested_model=model,
                          resolved_model=(model if who == "claude"
                                          else CX.RESOLVED_MODEL_UNDISCLOSED),
                          prompt_version=JG.PROMPT_VERSION,
                          input_text=json.dumps(sorted(variants)), effort=eff,
                          duration_ms=int((time.time() - t0) * 1000),
                          error_code=("ERROR" if err else None), error_text=err)
            ledger.save_cell(cell, {"cell": cell, "status": "ERROR" if err else "OK",
                                    "result": r, "error_text": err})
            reviews[who] = r
            print("  %s %-6s %s" % (run[-8:], who, r.get("status")))

        if all(reviews.get(w, {}).get("status") == "OK" for w in ("claude", "codex")):
            rec = JG.reconcile(reviews["claude"], reviews["codex"])
            (outdir / ("%s.json" % run)).write_text(json.dumps(
                {"subject_id": run, "reconciliation": rec,
                 "claude": reviews["claude"], "codex": reviews["codex"]},
                indent=1, ensure_ascii=False))
            print("     preference: claude=%s codex=%s agree=%s | owner review: %d"
                  % (rec["preference"]["claude_best"], rec["preference"]["codex_best"],
                     rec["preference"]["agree"], len(rec["owner_review_needed"])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subtest", action="store_true")
    ap.add_argument("--reviews", action="store_true")
    ap.add_argument("--split", choices=["development", "held_out"])
    args = ap.parse_args()
    ledger = BU.Ledger(ROOT / "ledger")
    print("budget before: %s" % json.dumps(ledger.summary()))
    try:
        if args.subtest:
            run_subtest(ledger)
        if args.reviews:
            if not args.split:
                ap.error("--reviews needs --split")
            run_reviews(ledger, args.split)
    except BU.BudgetExceeded as exc:
        print("STOPPED ON BUDGET: %s" % exc)
    finally:
        print("budget after: %s" % json.dumps(ledger.summary()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
