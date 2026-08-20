"""
runner.py -- the shadow vertical-slice runner.

SAFETY, stated as code and enforced by safety_tests.py:
  * OFF by default. `SHADOW_V0_MODE` unset -> run() refuses to do anything.
  * REPLAY is the only executable mode in Phase 1. LIVE_SHADOW is scaffolded and
    raises; it must not be executed in this task.
  * Writes ONLY under the run root passed in. Never _posts/, never _drafts/, never a
    production database. There is no database code in this package at all.
  * Nothing here is imported by production. This package lives under
    .claude/experiments/ and no automation/ module references it.
"""
from __future__ import annotations

import json
import os
import pathlib

from . import contracts as C
from .decision import decide

MODE_OFF = "OFF"
MODE_REPLAY = "REPLAY"
MODE_LIVE_SHADOW = "LIVE_SHADOW"


def current_mode() -> str:
    return os.environ.get("SHADOW_V0_MODE", MODE_OFF).strip().upper()


class ShadowDisabled(Exception):
    """Raised when run() is called while the shadow is OFF."""


def _emit(stage, created_at, payload, inputs: dict) -> C.Artifact:
    """Build, lineage-stamp and validate one artifact. Fail-closed."""
    art = C.Artifact(
        stage=stage,
        created_at=created_at,
        payload=payload,
        input_hashes={name: a.content_hash() for name, a in inputs.items()},
    )
    C.validate(art)
    C.verify_lineage(art, inputs)
    return art


def run(fixture, run_root: pathlib.Path, mode: str | None = None) -> dict:
    """Execute the vertical slice. `fixture` supplies each stage's payload.

    Returns {"artifacts": {stage: Artifact}, "decision": str, "reasons": [...]}.
    """
    mode = (mode or current_mode()).upper()
    if mode == MODE_OFF:
        raise ShadowDisabled(
            "shadow v0 is OFF. Set SHADOW_V0_MODE=REPLAY explicitly to run it.")
    if mode == MODE_LIVE_SHADOW:
        raise NotImplementedError(
            "LIVE_SHADOW is scaffolded but not implemented in Phase 1 and must not run. "
            "Phase 1 is plumbing validation only -- no model calls.")
    if mode != MODE_REPLAY:
        raise ShadowDisabled("unknown SHADOW_V0_MODE: %r" % mode)

    at = fixture.created_at
    A: dict[str, C.Artifact] = {}

    # --- WORLD / SOURCE -------------------------------------------------------
    A[C.SOURCE_SNAPSHOT] = _emit(C.SOURCE_SNAPSHOT, at, fixture.source_snapshot(), {})

    # --- DISCOVERY: what the evidence reveals. Consumes source only. ----------
    A[C.DISCOVERY] = _emit(C.DISCOVERY, at, fixture.discovery(),
                           {"source": A[C.SOURCE_SNAPSHOT]})

    # --- ARTICLE FORM: selection, relationships, burden, route, arrival. ------
    # Consumes discovery + source. Owns sequence; the writer does not.
    A[C.ARTICLE_FORM] = _emit(C.ARTICLE_FORM, at, fixture.article_form(),
                              {"discovery": A[C.DISCOVERY], "source": A[C.SOURCE_SNAPSHOT]})

    # --- WRITER INPUT: prose instruction derived from the Form. ---------------
    A[C.WRITER_INPUT] = _emit(C.WRITER_INPUT, at, fixture.writer_input(),
                              {"article_form": A[C.ARTICLE_FORM], "source": A[C.SOURCE_SNAPSHOT]})

    # --- WRITER: prose only. --------------------------------------------------
    A[C.WRITER_OUTPUT] = _emit(C.WRITER_OUTPUT, at, fixture.writer_output(),
                               {"writer_input": A[C.WRITER_INPUT]})

    # --- WRITER GROUNDING: receives WRITER OUTPUT + SOURCE SNAPSHOT only. -----
    # It must NOT receive ARTICLE_FORM: grounding does not change the Form.
    A[C.GROUNDING_FINDINGS] = _emit(
        C.GROUNDING_FINDINGS, at, fixture.grounding_findings(),
        {"writer_output": A[C.WRITER_OUTPUT], "source": A[C.SOURCE_SNAPSHOT]})

    repair = fixture.grounding_repair()
    if repair is not None:
        A[C.GROUNDING_REPAIR] = _emit(
            C.GROUNDING_REPAIR, at, repair,
            {"findings": A[C.GROUNDING_FINDINGS], "writer_output": A[C.WRITER_OUTPUT]})

    # --- SHADOW ACCEPT / HOLD -------------------------------------------------
    decision, reasons = decide(A)
    dec_inputs = {"findings": A[C.GROUNDING_FINDINGS], "writer_output": A[C.WRITER_OUTPUT]}
    if C.GROUNDING_REPAIR in A:
        dec_inputs["repair"] = A[C.GROUNDING_REPAIR]
    A[C.SHADOW_DECISION] = _emit(C.SHADOW_DECISION, at,
                                 {"decision": decision, "reasons": reasons,
                                  "policy": "shadow-v0 positive acceptance; not connected to publication"},
                                 dec_inputs)

    _persist(A, run_root, fixture.name, mode)
    return {"artifacts": A, "decision": decision, "reasons": reasons}


def _persist(A: dict, run_root: pathlib.Path, name: str, mode: str) -> None:
    """Write artifacts to the shadow run root. This is the ONLY filesystem write."""
    out = run_root / name
    out.mkdir(parents=True, exist_ok=True)
    for stage, art in A.items():
        (out / ("%s.json" % stage)).write_text(
            json.dumps(art.to_dict(), indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8")
    # Source text is persisted as its own file too -- the Phase-0 blocker fix, so a
    # later comparison can prove production and shadow saw identical bytes.
    (out / "source-snapshot.txt").write_text(
        A[C.SOURCE_SNAPSHOT].payload["source_text"], encoding="utf-8")
    manifest = {
        "shadow_v0_mode": mode,
        "fixture": name,
        "schema_version": C.SCHEMA_VERSION,
        "stage_hashes": {s: a.content_hash() for s, a in A.items()},
        "decision": A[C.SHADOW_DECISION].payload["decision"],
        "source_sha256": A[C.SOURCE_SNAPSHOT].payload["source_sha256"],
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
