#!/usr/bin/env python3
"""yield_report.py -- what did the engine actually do, from the artifacts it already writes.

Not a dashboard and not a database. Every number below is read out of the
COMPOSITION_RESULT.json files a run already persists, so this file can be deleted and
nothing is lost. It exists because "57 candidates were consumed before one article
published" took a forensic campaign to establish, and that question should cost a second.

    python3 yield_report.py [RUN_ROOT] [--since 2026-09-01] [--last 20]

RUN_ROOT defaults to /srv/data/cripminds-new-engine-v1.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

DEFAULT_ROOT = "/srv/data/cripminds-new-engine-v1"
STAGES = ("LEDGER", "WORTH", "ARCHITECTURE", "CUT_TERMS", "WRITER", "CONTINUITY",
          "PROSE_FINISH", "PACKAGE", "SAFETY", "GROUNDING", "FACT_CHECK", "READER")
# A run that stopped here stopped for a reason that is not about the article.
TECHNICAL = ("CLAUDE_SUBSCRIPTION_LIMIT", "PROVIDER", "TRANSPORT")


def load(root: pathlib.Path, since: str = "", last: int = 0) -> list:
    rows = []
    for p in sorted(root.glob("*/COMPOSITION_RESULT.json")):
        if since and p.parent.name[len("production-"):len("production-") + 8] \
                < since.replace("-", ""):
            continue
        try:
            rows.append((p.parent.name, json.loads(p.read_text())))
        except Exception as e:                                        # noqa: BLE001
            rows.append((p.parent.name, {"status": "UNREADABLE", "reason_code": str(e)}))
    return rows[-last:] if last else rows


def report(rows: list) -> None:
    n = len(rows)
    stages = collections.Counter(r.get("failure_stage") or "PUBLISHED_CANDIDATE"
                                 for _, r in rows)
    codes = collections.Counter(r.get("reason_code") or "" for _, r in rows)
    print("CONSIDERED (full compositions started)  %d" % n)
    if not n:
        return
    reached = lambda s: sum(1 for _, r in rows                       # noqa: E731
                           if (r.get("stages") or {}).get(s) in ("PASS", "REPLAYED"))
    print("WORTH        proceed %-4d hold %d"
          % (reached("WORTH"), stages.get("WORTH", 0)))
    print("ARCHITECTURE proceed %-4d hold %d"
          % (reached("ARCHITECTURE"), stages.get("ARCHITECTURE", 0)))
    polished = sum(1 for _, r in rows
                   if ((r.get("detail") or {}).get("PROSE_FINISH") or {}).get("applied"))
    fell_back = sum(1 for _, r in rows
                    if r.get("article_surface") == "PRE_POLISH_FALLBACK")
    print("PROSE FINISH applied %-4d pre-polish fallback %d" % (polished, fell_back))
    pkg = collections.Counter(r.get("package_status") or "NOT_RUN" for _, r in rows)
    print("PACKAGE      %s" % ", ".join("%s %d" % kv for kv in sorted(pkg.items())))
    for s in ("SAFETY", "GROUNDING", "FACT_CHECK", "READER"):
        print("%-12s pass %-4d hold %d" % (s, reached(s), stages.get(s, 0)))
    print("PUBLICATION  ready %-4d owner review %d"
          % (sum(1 for _, r in rows if r.get("publication_ready")),
             sum(1 for _, r in rows if r.get("owner_review"))))
    tech = [name for name, r in rows
            if any(t in (r.get("reason_code") or "") for t in TECHNICAL)]
    print("TECHNICAL    %d (%s)" % (len(tech), ", ".join(sorted(
        {(r.get("reason_code") or "") for name, r in rows if name in tech})) or "-"))
    print("\nWHERE THE RUNS STOPPED")
    for stage, c in stages.most_common():
        print("  %-22s %d" % (stage, c))
    print("\nREASON CODES")
    for code, c in codes.most_common(8):
        print("  %-26s %d" % (code or "(none)", c))


def main(argv: list) -> int:
    args = [a for a in argv if not a.startswith("--")]
    root = pathlib.Path(args[0] if args else DEFAULT_ROOT)
    since = next((a.split("=", 1)[-1] for a in argv if a.startswith("--since")), "")
    last = int(next((a.split("=", 1)[-1] for a in argv if a.startswith("--last")), 0) or 0)
    if not root.is_dir():
        print("no run root at %s" % root)
        return 1
    rows = load(root, since, last)
    print("RUN ROOT %s%s" % (root, (" since %s" % since) if since else ""))
    report(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
