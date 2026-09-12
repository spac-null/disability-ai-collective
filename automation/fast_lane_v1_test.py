#!/usr/bin/env python3
"""One targeted regression: load_run() must unwrap RESEARCH_PACK.json's payload, the
same way it already unwraps SOURCE_SNAPSHOT.json's, so Grounding receives the retained
research corpus instead of ~102 chars of nothing. No provider, no network."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import fast_lane_v1 as FL                                 # noqa: E402
from new_engine_v1 import composition as CP               # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                           "" if ok else " <- %r" % detail))
    if not ok:
        FAILURES.append(label)


def _fake_run_dir(tmp: pathlib.Path) -> pathlib.Path:
    (tmp / "LEDGER.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp / "WORTH_AND_CANDIDATE.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp / "SOURCE_SNAPSHOT.json").write_text(json.dumps(
        {"stage": "SOURCE_SNAPSHOT",
         "payload": {"source_text": "anchor text", "source_sha256": "abc"}}),
        encoding="utf-8")
    real_source = ("This is the retained research corpus text for a non-anchor "
                   "source. " * 50)
    (tmp / "RESEARCH_PACK.json").write_text(json.dumps({
        "stage": "RESEARCH_PACK",
        "payload": {
            "subject": "test subject",
            "sources": [
                {"source_id": "S0", "role": "ANCHOR", "url": "https://example.org/a",
                 "text": "anchor text"},
                {"source_id": "S1", "role": "PRIMARY", "url": "https://example.org/b",
                 "text": real_source},
            ],
        },
    }), encoding="utf-8")
    return tmp


def test_load_run_unwraps_research_pack_payload():
    with tempfile.TemporaryDirectory() as d:
        run_dir = _fake_run_dir(pathlib.Path(d))
        retained = FL.load_run(run_dir)
        pack = retained["pack"]
        check("load_run returns an unwrapped pack with a top-level 'sources' list",
              isinstance(pack.get("sources"), list) and len(pack["sources"]) == 2,
              pack)

        block = CP.S.pack_material_block(pack)
        check("pack_material_block on the unwrapped pack carries the real corpus",
              "retained research corpus" in block, len(block))

        wrapped = json.loads((run_dir / "RESEARCH_PACK.json").read_text())
        wrapped_block = CP.S.pack_material_block(wrapped)
        check("the bug this guards against: the WRAPPED dict starves the block "
              "(no top-level 'sources')",
              "retained research corpus" not in wrapped_block, len(wrapped_block))
        check("...and the unwrapped block is materially larger",
              len(block) > len(wrapped_block) * 5, (len(block), len(wrapped_block)))


def main() -> None:
    print("\ntest_load_run_unwraps_research_pack_payload")
    test_load_run_unwraps_research_pack_payload()
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("\nALL PASS")


if __name__ == "__main__":
    main()
