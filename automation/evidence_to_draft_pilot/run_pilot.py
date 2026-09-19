#!/usr/bin/env python3
"""
run_pilot.py -- the pilot driver. Resumable, budgeted, and it publishes nothing.

USAGE
    python3 evidence_to_draft_pilot/run_pilot.py --split development
    python3 evidence_to_draft_pilot/run_pilot.py --split held_out
    python3 evidence_to_draft_pilot/run_pilot.py --status

CELLS. One cell per (subject, stage). A completed cell is written to disk before the next
one starts, so a resumed run never regenerates -- and never re-pays for -- work already
done. Cells, in order, per subject:

    <subject>:writer   the shared Writer draft that arms A and B both start from
    <subject>:A        production Continuity + Prose Finish on that draft
    <subject>:B        one guarded edit on EXACTLY those same bytes
    <subject>:plan     Codex's evidence review and improved plan
    <subject>:C        the incumbent Writer on that plan, then the same guarded editor

BUDGET. Every model call is reserved before it is issued and recorded after, including
failures and the CLI's own internal mechanical retries -- which is why call counts are
read from the provider's own counter rather than from the stage's self-report. A run that
would breach a cap stops and says so rather than starting work it cannot finish.

NO PRODUCTION SIDE EFFECTS. Nothing here imports the publisher, the publication bridge,
the engagement database, the social writer or the orchestrator. Output goes only under
the experiment root.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import traceback

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from evidence_to_draft_pilot import arms as AR                     # noqa: E402
from evidence_to_draft_pilot import budget as BU                   # noqa: E402
from evidence_to_draft_pilot import planner as PL                  # noqa: E402
import claude_cli_provider as CC                                   # noqa: E402
import codex_cli_provider as CX                                    # noqa: E402

ROOT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                    "evidence-to-draft-pilot")

# FROZEN MODEL CONFIGURATION. Explicit on every call, per section 5. The Claude id is the
# subscription model production's own composition path resolves to; the Codex id is the
# CLI's configured default, named here so the pilot does not inherit a moving default.
CLAUDE_MODEL = "claude-opus-5"
CODEX_MODEL = "gpt-5.6-luna"
CODEX_EFFORT = "medium"

RESUME_COMMAND = ("cd /srv/data/hermes/workspace/evidence-to-draft-pilot/automation && "
                  "python3 evidence_to_draft_pilot/run_pilot.py --split %s")


def load_manifest() -> dict:
    return json.loads((ROOT / "EXPERIMENT_MANIFEST.json").read_text())


def load_subject(run: str) -> dict:
    return json.loads((ROOT / "subjects" / run / "SUBJECT.json").read_text())


def planned_cells(manifest: dict, split: str) -> list:
    runs = manifest["development_subjects" if split == "development"
                    else "held_out_subjects"]
    out = []
    for r in runs:
        out += ["%s:%s" % (r, s) for s in ("writer", "A", "B", "plan", "C")]
    return out


class Meter:
    """Counts what the PROVIDER actually issued, not what a stage reported.

    A stage's own `model_calls` misses the mechanical JSON retry `composition._ask` and
    `write_article` each perform, and an undercounted retry is exactly the budget leak
    section 7 asks to be counted.
    """

    def __init__(self, provider):
        self.p = provider
        self.start = getattr(provider, "calls", 0)

    def spent(self) -> int:
        return getattr(self.p, "calls", 0) - self.start


def run_cell(ledger: BU.Ledger, cell: str, role: str, provider, fn, *,
             requested_model: str, resolved_model: str, prompt_version: str,
             input_text: str, effort=None):
    """Reserve, run, record, persist. One documented transport retry, and no other."""
    if ledger.done(cell):
        print("    = %-8s cached" % role)
        return ledger.load_cell(cell)

    provider_label = ("claude-cli-subscription" if provider is None
                      or isinstance(provider, CC.ClaudeCLIProvider)
                      else "codex-cli-subscription")
    ledger.reserve(provider=provider_label)
    meter = Meter(provider)
    t0 = time.time()
    try:
        out = fn()
        err_code, err_text = None, None
    except Exception as exc:                                       # noqa: BLE001
        out = None
        err_code = getattr(exc, "code", type(exc).__name__)
        err_text = "%s: %s" % (type(exc).__name__, exc)
        print("    ! %-8s %s" % (role, err_text[:120]))

    # A cell that genuinely issued no request must not be charged one. Two cases reach
    # here: a plan refused before any call because the frozen beat layout cannot host a
    # carrier, and arm C skipped because that plan never validated. Everything else is
    # charged at least one call even when the provider counter did not move, because a
    # failure that consumed quota is the case the counter is least able to see.
    issued = meter.spent()
    no_call = isinstance(out, dict) and (out.get("no_model_call_was_made")
                                         or out.get("model_calls") == 0)
    spent = issued if (issued == 0 and no_call) else max(issued, 1)
    ledger.record(cell=cell, role=role, provider=provider_label,
                  requested_model=requested_model, resolved_model=resolved_model,
                  prompt_version=prompt_version, input_text=input_text, effort=effort,
                  duration_ms=int((time.time() - t0) * 1000),
                  error_code=err_code, error_text=err_text,
                  extra={"provider_calls_issued": spent, "calls_issued": 1 if spent else 0})
    # The provider's extra internal retries are real quota. Record each as its own row so
    # the count in CALLS.jsonl equals the count the account saw.
    for n in range(1, spent):
        ledger.record(cell=cell, role=role + ":internal-retry", provider=provider_label,
                      requested_model=requested_model, resolved_model=resolved_model,
                      prompt_version=prompt_version, input_text="", effort=effort,
                      retry_of=cell, extra={"calls_issued": 1})

    payload = {"cell": cell, "role": role, "status": "ERROR" if out is None else "OK",
               "error_code": err_code, "error_text": err_text,
               "provider_calls_issued": spent,
               "elapsed_seconds": round(time.time() - t0, 1),
               "requested_model": requested_model, "resolved_model": resolved_model,
               "result": out}
    ledger.save_cell(cell, payload)
    if out is not None:
        print("    + %-8s %d call(s), %.0fs" % (role, spent, time.time() - t0))
    return payload


def run_subject(ledger: BU.Ledger, run: str, claude, codex) -> None:
    subj = load_subject(run)
    gi = subj["generation_inputs"]
    arch, led = gi["architecture"], gi["ledger"]
    print("\n  %s  (%s)" % (run, subj["subject"][:56]))

    w = run_cell(ledger, "%s:writer" % run, "writer", claude,
                 lambda: AR.write_draft(claude, arch, led),
                 requested_model=CLAUDE_MODEL, resolved_model=CLAUDE_MODEL,
                 prompt_version="production-writer", input_text=json.dumps(arch))
    if w["status"] != "OK":
        return
    wr = w["result"]

    run_cell(ledger, "%s:A" % run, "armA", claude,
             lambda: AR.arm_a_current_editing(claude, wr, arch),
             requested_model=CLAUDE_MODEL, resolved_model=CLAUDE_MODEL,
             prompt_version="production-continuity+prose-finish",
             input_text=wr["article_text"])

    run_cell(ledger, "%s:B" % run, "armB", claude,
             lambda: AR.arm_b_guarded_edit(claude, wr),
             requested_model=CLAUDE_MODEL, resolved_model=CLAUDE_MODEL,
             prompt_version="guarded-editor-v1", input_text=wr["article_text"])

    p = run_cell(ledger, "%s:plan" % run, "plan", codex,
                 lambda: PL.plan_subject(codex, subj),
                 requested_model=CODEX_MODEL,
                 resolved_model=CX.RESOLVED_MODEL_UNDISCLOSED,
                 prompt_version=PL.PROMPT_VERSION, effort=CODEX_EFFORT,
                 input_text=json.dumps(gi["subject"]))
    if p["status"] != "OK":
        return

    run_cell(ledger, "%s:C" % run, "armC", claude,
             lambda: AR.arm_c_planned(claude, p["result"], led),
             requested_model=CLAUDE_MODEL, resolved_model=CLAUDE_MODEL,
             prompt_version="production-writer+guarded-editor-v1",
             input_text=json.dumps(p["result"].get("architecture") or {}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["development", "held_out"])
    ap.add_argument("--subject", help="run one subject only")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    man = load_manifest()
    ledger = BU.Ledger(ROOT / "ledger")

    if args.status:
        print(json.dumps(ledger.summary(), indent=1))
        return 0
    if not args.split:
        ap.error("--split is required unless --status")

    cells = planned_cells(man, args.split)
    runs = [args.subject] if args.subject else (
        man["development_subjects"] if args.split == "development"
        else man["held_out_subjects"])

    print("budget before: %s" % json.dumps(ledger.summary()))
    claude = CC.get_provider(CLAUDE_MODEL)
    codex = CX.get_provider(CODEX_MODEL, effort=CODEX_EFFORT)
    print("claude auth: %s / %s" % (claude.auth.get("authMethod"),
                                    claude.auth.get("subscriptionType")))
    print("codex auth:  %s (api key stored: %s)" % (codex.auth.get("auth_mode"),
                                                    codex.auth.get("has_api_key")))

    try:
        for run in runs:
            run_subject(ledger, run, claude, codex)
    except BU.BudgetExceeded as exc:
        print("\nSTOPPED ON BUDGET: %s" % exc)
    except KeyboardInterrupt:
        print("\ninterrupted")
    except Exception:                                              # noqa: BLE001
        traceback.print_exc()
    finally:
        ledger.write_checkpoint(
            worktree="/srv/data/hermes/workspace/evidence-to-draft-pilot",
            branch="pilot/evidence-to-draft-2026-09-19",
            commit=(pathlib.Path(AUTOMATION).parent / ".git").exists() and "see git" or "",
            models={"claude": {"requested": CLAUDE_MODEL, "transport": "claude CLI "
                               "subscription"},
                    "codex": {"requested": CODEX_MODEL, "effort": CODEX_EFFORT,
                              "transport": "codex CLI subscription",
                              "resolved": CX.RESOLVED_MODEL_UNDISCLOSED}},
            planned_cells=cells,
            resume_command=RESUME_COMMAND % args.split)
        print("\nbudget after: %s" % json.dumps(ledger.summary()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
