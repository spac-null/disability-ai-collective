#!/usr/bin/env python3
"""
new_engine_v1_acceptance.py -- ONE controlled NEW_ENGINE_V1 run on real material.

NOT_PUBLICATION. NOT_P2_SAMPLE. Nothing here publishes, commits, marks a seed used, or
touches the legacy scheduled path.

Deliberately OUTSIDE the `new_engine_v1` package. Source acquisition is upstream
production's job, so this script imports the production orchestrator to get a real
source through the normal mechanism -- and keeping that import here is what lets the
package itself stay provably free of legacy imports (asserted in
new_engine_v1_test.py::test_package_purity_static).

The source is NOT hand-picked: it comes from the same ranking + SOURCE_ACQUISITION_
RETRY_V1 path the scheduled run uses. Whatever that returns is what gets tested.

Usage (trident):
  NEW_ENGINE_V1_MODE=LIVE python3 automation/new_engine_v1_acceptance.py --out <dir>
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import contracts as C          # noqa: E402
from new_engine_v1 import runner as R             # noqa: E402
from new_engine_v1.provider import Provider, DEFAULT_MODEL  # noqa: E402


def acquire_real_source():
    """One real current source through the normal upstream production mechanism."""
    import production_orchestrator as po           # legacy import, intentionally here
    orch = po.ProductionOrchestrator()
    seed = orch.get_news_seed_with_usable_source()
    if not seed:
        return None, None, getattr(orch, "_source_acquisition_attempts", [])
    text = orch.get_source_text(
        seed["url"], fallback_text=seed.get("summary"),
        underlying_url=seed.get("underlying_article_url"))
    payload = {
        "source_text": text,
        "source_sha256": C.sha256_text(text),
        "provenance": {
            "origin": orch.get_source_origin(seed["url"]),
            "url": seed["url"],
            "seed_id": seed["id"],
            "source_name": seed.get("source_name"),
            "title": seed.get("title"),
            "original_length_chars": orch.get_source_original_length(seed["url"]),
            "paragraph_count": orch.get_source_paragraph_count(seed["url"]),
            "acquired_via": "SOURCE_ACQUISITION_RETRY_V1 (normal upstream mechanism)",
        },
    }
    return seed, payload, getattr(orch, "_source_acquisition_attempts", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="isolated candidate/evidence root")
    ap.add_argument("--name", default=None)
    ap.add_argument("--byline", default=R.DEFAULT_BYLINE)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    if R.current_mode() != R.MODE_LIVE:
        print("NEW_ENGINE_V1_MODE is %r, not LIVE. Refusing." % R.current_mode())
        return 2

    seed, payload, attempts = acquire_real_source()
    if payload is None:
        print(json.dumps({"status": "no_usable_source", "attempts": attempts}, indent=2))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc)
    name = args.name or ("acceptance-%s-%s"
                         % (now.strftime("%Y%m%dT%H%M%SZ"), payload["source_sha256"][:8]))
    print("source : %s" % payload["provenance"]["url"])
    print("origin : %s  chars=%s  paragraphs=%s"
          % (payload["provenance"]["origin"],
             payload["provenance"]["original_length_chars"],
             payload["provenance"]["paragraph_count"]))
    print("acquisition attempts: %d" % len(attempts))
    print("model  : %s" % args.model)
    print("run    : %s\n" % name)

    out = R.run(payload, pathlib.Path(args.out), Provider(model=args.model),
                name, now.isoformat(), byline=args.byline)

    print("DECISION: %s" % out["decision"])
    for r in out["reasons"]:
        print("  - %s" % r)
    print("\nstages: %s" % ", ".join(sorted(out["artifacts"])))
    (pathlib.Path(args.out) / name / "ACQUISITION.json").write_text(
        json.dumps({"attempts": attempts, "seed_id": payload["provenance"]["seed_id"]},
                   indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
