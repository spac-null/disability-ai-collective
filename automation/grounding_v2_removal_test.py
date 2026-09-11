#!/usr/bin/env python3
"""Regression test for removing the Grounding V2 runtime hook.

The V2 module and its historical tests remain available as research artifacts.  The
production runner must not import or execute them, and an existing shadow artifact must
survive a normal persist operation.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import new_engine_v1_test as T  # noqa: E402
from new_engine_v1 import composition as CP  # noqa: E402
from new_engine_v1 import runner as R  # noqa: E402


def main() -> None:
    old_shadow = os.environ.get("CRIPMINDS_GROUNDING_V2_SHADOW")
    old_engine = os.environ.get(CP.COMPOSITION_ENGINE_ENV)
    os.environ["CRIPMINDS_GROUNDING_V2_SHADOW"] = "1"
    os.environ[CP.COMPOSITION_ENGINE_ENV] = CP.COMPOSITION_LEGACY
    try:
        with tempfile.TemporaryDirectory() as d:
            run_dir = pathlib.Path(d) / "run"
            run_dir.mkdir()
            historical = run_dir / "GROUNDING_V2_SHADOW.json"
            historical.write_text('{"historical": true}\n', encoding="utf-8")

            out = R.run(T._source_payload(), pathlib.Path(d), T.StubProvider(), "run",
                        T.AT, mode=R.MODE_LIVE, research_fn=T.stub_pack)
            runner_source = (HERE / "new_engine_v1" / "runner.py").read_text()

            assert out["decision"] == "ACCEPT"
            assert historical.read_text(encoding="utf-8") == '{"historical": true}\n'
            assert "GROUNDING_V2_SHADOW.json" not in {
                p.name for p in run_dir.iterdir() if p.name != historical.name
            }
            assert "grounding_v2" not in runner_source.lower()
            assert "_shadow_grounding_v2" not in runner_source
    finally:
        if old_shadow is None:
            os.environ.pop("CRIPMINDS_GROUNDING_V2_SHADOW", None)
        else:
            os.environ["CRIPMINDS_GROUNDING_V2_SHADOW"] = old_shadow
        if old_engine is None:
            os.environ.pop(CP.COMPOSITION_ENGINE_ENV, None)
        else:
            os.environ[CP.COMPOSITION_ENGINE_ENV] = old_engine

    print("Grounding V2 removal regression passed.")


if __name__ == "__main__":
    main()
