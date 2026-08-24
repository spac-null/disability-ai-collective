"""
runner.py -- NEW_ENGINE_V1 live orchestration.

    WORLD / SOURCE -> DISCOVERY -> ARTICLE FORM -> WRITER -> WRITER GROUNDING
                   -> ACCEPT / HOLD -> (accepted candidate pool)

This is the production CANDIDATE. It is not wired to any cron, any selector, or any
publication path, and it cannot publish: there is no `_posts`/`_drafts` write, no git
call and no database code in this package.

SAFETY, enforced by engine_test.py rather than asserted here:
  * OFF by default. `NEW_ENGINE_V1_MODE` unset -> run() refuses.
  * Writes only under the run root it is given.
  * No legacy prompt surface reaches WRITER_INPUT -- the frozen contract rejects 29
    markers and validation is fail-closed.
  * ACCEPT means "eligible to enter the candidate pool". It does NOT mean publish, and
    nothing here connects it to publication.

The stage graph, the artifact hashing and the ACCEPT/HOLD policy are the frozen
Phase-1 contracts, ported verbatim. What is new here is only that the stages are
executed against real material by a real provider instead of replayed from fixtures.
"""
from __future__ import annotations

import json
import os
import pathlib

from . import contracts as C
from . import stages as S
from .decision import decide

ENGINE = "NEW_ENGINE_V1"
MODE_OFF = "OFF"
MODE_LIVE = "LIVE"

DEFAULT_BYLINE = "Maya Flux"


class EngineDisabled(Exception):
    """Raised when run() is called while the engine is OFF."""


def current_mode() -> str:
    return os.environ.get("NEW_ENGINE_V1_MODE", MODE_OFF).strip().upper()


def _emit(stage, created_at, payload, inputs: dict) -> C.Artifact:
    art = C.Artifact(stage=stage, created_at=created_at, payload=payload,
                     input_hashes={n: a.content_hash() for n, a in inputs.items()})
    C.validate(art)
    C.verify_lineage(art, inputs)
    return art


def _strip_provider(payload: dict) -> dict:
    """Provider identity is recorded in the manifest, not inside the stage payload.

    Keeping it out of the payload keeps artifact hashes stable for the same material,
    which is what makes a later legacy-vs-new comparison meaningful.
    """
    return {k: v for k, v in payload.items() if k != "_provider"}


def run(source_payload: dict, run_root: pathlib.Path, provider,
        name: str, created_at: str, byline: str = DEFAULT_BYLINE,
        mode: str | None = None) -> dict:
    """Execute the target path once against real material.

    `source_payload` must already satisfy the SOURCE_SNAPSHOT contract -- acquisition is
    upstream production's job, not this engine's, and passing it in keeps this package
    free of any legacy import.
    """
    mode = (mode or current_mode()).upper()
    if mode == MODE_OFF:
        raise EngineDisabled(
            "NEW_ENGINE_V1 is OFF. Set NEW_ENGINE_V1_MODE=LIVE explicitly to run it.")
    if mode != MODE_LIVE:
        raise EngineDisabled("unknown NEW_ENGINE_V1_MODE: %r" % mode)

    at = created_at
    A: dict[str, C.Artifact] = {}
    prov: dict[str, dict] = {}

    # --- WORLD / SOURCE -------------------------------------------------------
    A[C.SOURCE_SNAPSHOT] = _emit(C.SOURCE_SNAPSHOT, at, source_payload, {})
    src = source_payload["source_text"]
    sha = source_payload["source_sha256"]

    # --- DISCOVERY: consumes source only -------------------------------------
    d = S.discover(provider, src, sha)
    prov["discovery"] = d.get("_provider", {})
    if d.get("commissionable") is False:
        # A grounded refusal. Recorded as a first-class outcome, not an error: the
        # source carries no mechanism this reading can reach.
        disc = _emit(C.DISCOVERY, at, _strip_provider(d), {"source": A[C.SOURCE_SNAPSHOT]})
        A[C.DISCOVERY] = disc
        _persist(A, run_root, name, mode, prov,
                 decision="HOLD", reasons=["discovery: source not commissionable"])
        return {"artifacts": A, "decision": "HOLD",
                "reasons": ["discovery: source not commissionable -- %s"
                            % str(d.get("disturbance", ""))[:200]],
                "provider": prov}
    A[C.DISCOVERY] = _emit(C.DISCOVERY, at, _strip_provider(d),
                           {"source": A[C.SOURCE_SNAPSHOT]})

    # --- ARTICLE FORM: consumes discovery + source ---------------------------
    f = S.make_form(provider, d, src, sha)
    prov["article_form"] = f.get("_provider", {})
    A[C.ARTICLE_FORM] = _emit(C.ARTICLE_FORM, at, _strip_provider(f),
                              {"discovery": A[C.DISCOVERY], "source": A[C.SOURCE_SNAPSHOT]})

    # --- WRITER INPUT: derived from the Form. Deterministic, no model. --------
    wi = S.build_writer_input(f, d, src, sha, byline)
    A[C.WRITER_INPUT] = _emit(C.WRITER_INPUT, at, wi,
                              {"article_form": A[C.ARTICLE_FORM],
                               "source": A[C.SOURCE_SNAPSHOT]})

    # --- WRITER: prose only --------------------------------------------------
    wo = S.write(provider, wi)
    prov["writer"] = wo.get("_provider", {})

    if wo["provider_status"] != "ok":
        # A note on the frozen contract: decision.py anticipates
        # provider_status != "ok", but contracts.validate() requires a non-empty
        # article_text, so a FAILED writer output cannot be expressed as a valid
        # WRITER_OUTPUT artifact. Rather than edit a frozen contract or fabricate
        # placeholder prose, no WRITER_OUTPUT is emitted: the run HOLDs on an
        # explicit, recorded reason. Fail-closed either way, and the provider error
        # is preserved in the manifest. Flagged for the contract owner.
        reasons = ["writer provider failed (%s); HOLD, no template fallback"
                   % wo.get("provider_error", "unknown")[:160],
                   "no WRITER_OUTPUT artifact emitted: the frozen contract cannot "
                   "represent an empty article_text"]
        A[C.SHADOW_DECISION] = _emit(
            C.SHADOW_DECISION, at,
            {"decision": "HOLD", "reasons": reasons, "engine": ENGINE,
             "provider_error": wo.get("provider_error", ""),
             "policy": "ACCEPT = eligible for the candidate pool; never publication"},
            {"writer_input": A[C.WRITER_INPUT]})
        _persist(A, run_root, name, mode, prov, "HOLD", reasons)
        return {"artifacts": A, "decision": "HOLD", "reasons": reasons, "provider": prov}

    A[C.WRITER_OUTPUT] = _emit(C.WRITER_OUTPUT, at, _strip_provider(wo),
                               {"writer_input": A[C.WRITER_INPUT]})

    # --- WRITER GROUNDING: writer output + source ONLY (never the Form) -------
    gf = S.ground(provider, wo["article_text"], src, sha)
    prov["grounding"] = gf.get("_provider", {})
    A[C.GROUNDING_FINDINGS] = _emit(C.GROUNDING_FINDINGS, at, _strip_provider(gf),
                                    {"writer_output": A[C.WRITER_OUTPUT],
                                     "source": A[C.SOURCE_SNAPSHOT]})

    # --- PATCH-ONLY REPAIR, then a real re-check of the affected findings -----
    rp = S.repair(wo["article_text"], gf["findings"])
    if rp is not None:
        recheck = S.ground(provider, rp["article_text"], src, sha)
        prov["grounding_recheck"] = recheck.get("_provider", {})
        before = {f_.get("quote") for f_ in gf["findings"]
                  if f_.get("classification") == "TRUE_UNSUPPORTED"}
        after = [f_ for f_ in recheck["findings"]
                 if f_.get("classification") == "TRUE_UNSUPPORTED"]
        # residual: an unsupported claim that survived. introduced: one the repair
        # itself created. Measured, not assumed.
        rp["verification"]["residual"] = len([f_ for f_ in after
                                              if f_.get("quote") in before])
        rp["verification"]["introduced"] = len([f_ for f_ in after
                                                if f_.get("quote") not in before])
        rp["recheck_findings"] = recheck["findings"]
        A[C.GROUNDING_REPAIR] = _emit(C.GROUNDING_REPAIR, at, rp,
                                      {"findings": A[C.GROUNDING_FINDINGS],
                                       "writer_output": A[C.WRITER_OUTPUT]})

    # --- ACCEPT / HOLD -------------------------------------------------------
    decision, reasons = decide(A)
    dec_inputs = {"findings": A[C.GROUNDING_FINDINGS], "writer_output": A[C.WRITER_OUTPUT]}
    if C.GROUNDING_REPAIR in A:
        dec_inputs["repair"] = A[C.GROUNDING_REPAIR]
    A[C.SHADOW_DECISION] = _emit(
        C.SHADOW_DECISION, at,
        {"decision": decision, "reasons": reasons, "engine": ENGINE,
         "policy": "ACCEPT = eligible for the candidate pool; never publication"},
        dec_inputs)

    _persist(A, run_root, name, mode, prov, decision, reasons)
    return {"artifacts": A, "decision": decision, "reasons": reasons, "provider": prov}


def _persist(A: dict, run_root: pathlib.Path, name: str, mode: str,
             prov: dict, decision: str, reasons: list) -> None:
    """The ONLY filesystem write. Isolated candidate/evidence location."""
    out = run_root / name
    out.mkdir(parents=True, exist_ok=True)
    for stage, art in A.items():
        (out / ("%s.json" % stage)).write_text(
            json.dumps(art.to_dict(), indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8")
    (out / "source-snapshot.txt").write_text(
        A[C.SOURCE_SNAPSHOT].payload["source_text"], encoding="utf-8")
    if C.WRITER_OUTPUT in A:
        (out / "article.md").write_text(
            A[C.WRITER_OUTPUT].payload["article_text"], encoding="utf-8")
    if C.GROUNDING_REPAIR in A:
        (out / "article-repaired.md").write_text(
            A[C.GROUNDING_REPAIR].payload["article_text"], encoding="utf-8")
    (out / "MANIFEST.json").write_text(json.dumps({
        "engine": ENGINE,
        "mode": mode,
        "run": name,
        "schema_version": C.SCHEMA_VERSION,
        "stage_hashes": {s: a.content_hash() for s, a in A.items()},
        "decision": decision,
        "reasons": reasons,
        "source_sha256": A[C.SOURCE_SNAPSHOT].payload["source_sha256"],
        "provider_identity": prov,
        "publication": "NONE -- candidate only, not connected to any selector or publish path",
    }, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
