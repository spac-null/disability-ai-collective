#!/usr/bin/env python3
"""campaign_driver.py -- run production candidates back to back, and never mis-attribute.

WHY THIS IS COMMITTED CODE. The publication campaign was driven by a shell loop that
identified each attempt's result with

    ls -td /srv/data/cripminds-new-engine-v1/*/ | head -1

That is correct exactly while every invocation creates a run directory. On 2026-09-05 the
selector began failing before any directory existed -- `DataError: string or blob too big`
-- and six consecutive attempts were reported as the SAME Grounding HOLD, quoting a
finding from an earlier candidate, because the newest directory was the previous
attempt's. The real failure was invisible for six runs and the funnel numbers were wrong.

THE RULE HERE. A result is attributed to an attempt ONLY through the run id that
attempt's own invocation printed. The orchestrator emits its result as JSON on stdout,
carrying `engine_run`, and that id -- not the filesystem's idea of "newest" -- selects the
evidence directory. When an invocation exits before producing a run id, the driver reports
that invocation's real upstream failure and never reaches for a directory at all.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time

WORKSPACE = "/srv/data/hermes/workspace/disability-ai-collective"
EVIDENCE = "/srv/data/cripminds-new-engine-v1"
SUBSCRIPTION_LIMIT = "CLAUDE_SUBSCRIPTION_LIMIT"


def parse_result(stdout: str) -> dict:
    """The orchestrator's own result object, which is the last JSON object it prints."""
    depth = start = None
    best = None
    for i, ch in enumerate(stdout):
        if ch == "{":
            if depth is None:
                depth, start = 0, i
            depth += 1
        elif ch == "}" and depth is not None:
            depth -= 1
            if depth == 0:
                try:
                    best = json.loads(stdout[start:i + 1])
                except ValueError:
                    pass
                depth = start = None
    return best or {}


def outcome(stdout: str, evidence_root: str = EVIDENCE) -> dict:
    """What one invocation actually did.

    `run` is taken from the invocation's own output. If it has none, this returns the
    upstream failure and `run_dir` is None -- there is no directory to attribute.
    """
    res = parse_result(stdout)
    run = res.get("engine_run")
    rs = res.get("run_status") or {}
    if not run:
        return {
            "attributed": False,
            "run": None,
            "run_dir": None,
            "stage": rs.get("stage") or "UPSTREAM",
            "reason_code": res.get("reason_code") or rs.get("status") or "NO_RESULT",
            "detail": (rs.get("detail") or rs.get("error")
                       or "; ".join(res.get("reasons") or []) or "")[:400],
            "subject": res.get("source_url") or "",
            "limit": SUBSCRIPTION_LIMIT in stdout,
        }
    d = pathlib.Path(evidence_root) / run
    cr = d / "COMPOSITION_RESULT.json"
    comp = json.loads(cr.read_text()) if cr.exists() else {}
    return {
        "attributed": True,
        "run": run,
        "run_dir": str(d),
        "stage": comp.get("failure_stage") or rs.get("stage") or (
            "ACCEPT" if res.get("status") == "accept" else "UPSTREAM"),
        "reason_code": comp.get("reason_code") or res.get("reason_code") or "",
        "detail": (comp.get("failure_reason") or rs.get("detail") or "")[:400],
        "subject": (comp.get("subject") or res.get("source_url") or "")[:220],
        "stages": comp.get("stages") or {},
        "accepted": res.get("status") == "accept",
        "limit": SUBSCRIPTION_LIMIT in stdout,
    }


def run_once(env_extra: dict | None = None) -> str:
    env = dict(os.environ)
    env.update({"CRIPMINDS_ENGINE": "new_engine_v1", "NEW_ENGINE_V1_MODE": "LIVE",
                "CRIPMINDS_SELECTOR_V2_SHADOW": "1"})
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, "automation/production_orchestrator.py"],
                       cwd=WORKSPACE, env=env, capture_output=True, text=True)
    return (p.stdout or "") + "\n" + (p.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=10, help="maximum candidates to attempt")
    args = ap.parse_args()
    for i in range(1, args.n + 1):
        print("=== ATTEMPT %d  %s ===" % (i, time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                           time.gmtime())), flush=True)
        out = run_once()
        o = outcome(out)
        print("  attributed : %s" % o["attributed"])
        print("  run        : %s" % o["run"])
        print("  stage      : %s" % o["stage"])
        print("  reason     : %s" % o["reason_code"])
        print("  subject    : %s" % o["subject"])
        print("  detail     : %s" % o["detail"])
        if o.get("stages"):
            print("  stages     : %s" % json.dumps(o["stages"], sort_keys=True))
        sys.stdout.flush()
        if o["limit"]:
            print("### SUBSCRIPTION LIMIT -- stopping; no model substitution permitted ###")
            return 2
        if o.get("accepted"):
            print("### ACCEPTED ON ATTEMPT %d ###" % i)
            return 0
        print(flush=True)
    print("=== CASCADE END %s ===" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
