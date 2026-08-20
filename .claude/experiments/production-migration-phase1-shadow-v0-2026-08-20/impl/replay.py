#!/usr/bin/env python3
"""
replay.py -- Phase-1 golden replay entry point.

Runs the shadow V0 vertical slice in REPLAY mode over preserved fixtures. No model
call, no network, no production state. Writes only under ../runs/.

USAGE:  SHADOW_V0_MODE=REPLAY python3 replay.py [--fixture test2|form13|all]
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from shadow_v0 import contracts as C          # noqa: E402
from shadow_v0.runner import run  # noqa: E402
from shadow_v0.fixtures import Test2Fixture, Form13Fixture  # noqa: E402

RUN_ROOT = pathlib.Path(__file__).parent.parent / "runs"
FIXTURES = {"test2": Test2Fixture, "form13": Form13Fixture}


def replay(key):
    fx = FIXTURES[key]()
    result = run(fx, RUN_ROOT)      # mode comes from SHADOW_V0_MODE; OFF by default
    A = result["artifacts"]
    print("=" * 74)
    print("FIXTURE: %s" % fx.name)
    print("=" * 74)
    for stage in C.STAGE_ORDER:
        if stage in A:
            print("  %-20s %s" % (stage, A[stage].content_hash()))
        else:
            print("  %-20s (absent -- optional)" % stage)
    src = A[C.SOURCE_SNAPSHOT].payload
    print("  source words           %d" % src["words"])
    print("  source sha256          %s" % src["source_sha256"])
    print("  DECISION               %s" % result["decision"])
    for r in result["reasons"]:
        print("      - %s" % r)
    return fx, result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", default="test2", choices=["test2", "form13", "all"])
    args = ap.parse_args()
    keys = ["test2", "form13"] if args.fixture == "all" else [args.fixture]
    for k in keys:
        replay(k)
        print()


if __name__ == "__main__":
    main()
