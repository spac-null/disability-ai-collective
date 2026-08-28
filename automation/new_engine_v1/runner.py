"""
runner.py -- NEW_ENGINE_V1 live orchestration.

    WORLD / SOURCE -> RESEARCH PACK -> SUFFICIENCY -> DISCOVERY -> ARTICLE FORM
                   -> WRITER -> WRITER GROUNDING -> ACCEPT / HOLD
                   -> (accepted candidate pool)

RESEARCH runs BEFORE Discovery, on purpose: evidence is supposed to produce the idea,
not be recruited to defend one Discovery already had. Everything downstream reads the
frozen pack. The Writer still has no network of its own -- it writes from bytes that
were fetched, hashed and persisted before it was asked for a word.

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
from . import invariants as INV
from . import research as RS
from . import stages as S
from .decision import decide
from .provider import ProviderError

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


def _stage_failure(stage: str, category: str, exc: Exception, at: str, A: dict,
                   run_root: pathlib.Path, name: str, mode: str, prov: dict) -> dict:
    """A model-stage failure at DISCOVERY, ARTICLE_FORM or GROUNDING_FINDINGS is
    recorded exactly like the existing WRITER_OUTPUT provider-failure path: HOLD, no
    downstream stage runs, no artifact is fabricated for the failed stage, and a
    RUN_STATUS record identifies which stage and why -- distinguishable from an
    editorial HOLD (`decision.py`'s HOLDs always carry a full artifact set; this one
    never does).

    Two failure categories reach here, kept distinct in the record:
      * `ProviderError` -- transport failure or a reply that isn't recoverably one
        JSON object (`provider.py::parse_json_object`).
      * `contracts.ContractViolation` -- the reply parsed, but doesn't satisfy the
        stage's required shape (missing field, wrong type) -- caught where `_emit`
        calls `contracts.validate()`.
    """
    status = "PROVIDER_FAILURE" if isinstance(exc, ProviderError) else "CONTRACT_FAILURE"
    run_status = {
        "status": status,
        "stage": stage,
        "failure_category": category,
        "error": str(exc)[:500],
        "run": name,
        "created_at": at,
        "engine": ENGINE,
        "writer_output_emitted": False,
        "article_produced": False,
    }
    reasons = ["%s failed (%s); HOLD, no downstream stage runs" % (stage, category),
               "RUN_STATUS=%s recorded; no %s artifact emitted for this run" % (status, stage)]
    _persist(A, run_root, name, mode, prov, "HOLD", reasons, run_status=run_status)
    return {"artifacts": A, "decision": "HOLD", "reasons": reasons, "provider": prov,
            "run_status": run_status, "reason_code": "%s_%s" % (stage, category.upper())}


def run(source_payload: dict, run_root: pathlib.Path, provider,
        name: str, created_at: str, byline: str = DEFAULT_BYLINE,
        mode: str | None = None, research_fn=None) -> dict:
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

    # --- RESEARCH: bounded, before any idea exists ---------------------------
    # Injected so a test can supply a pack without a network, exactly as the safety
    # bridge injects its fact check. A research failure is a HOLD, never a thin pack:
    # "we could not read enough" and "there was not enough to read" are different
    # answers, and neither is permission to write anyway.
    prov_anchor = source_payload.get("provenance") or {}
    try:
        pack = (research_fn or RS.research)(
            provider,
            anchor={"url": prov_anchor.get("url", ""), "text": src,
                    "title": prov_anchor.get("title", ""),
                    "canonical_url": prov_anchor.get("canonical_url", ""),
                    "accessed_at": at},
            now_iso=at)
    except (RS.ResearchError, ProviderError, C.ContractViolation) as e:
        return _stage_failure(
            C.RESEARCH_PACK,
            "provider_error" if isinstance(e, (ProviderError, RS.ResearchError))
            else "invalid_response_shape",
            e, at, A, run_root, name, mode, prov)
    prov["research"] = pack.pop("_provider", {})
    A[C.RESEARCH_PACK] = _emit(C.RESEARCH_PACK, at, pack, {"source": A[C.SOURCE_SNAPSHOT]})
    verdict = pack["sufficiency"]["verdict"]

    if verdict == RS.HOLD:
        # A successful fail-closed outcome, not an engine error. The pack is persisted
        # with it, so "what did research actually find" is answerable afterwards.
        reasons = ["research: %s" % RS.HOLD,
                   "; ".join(pack["sufficiency"]["reasons"])[:300],
                   "; ".join(pack["sufficiency"]["what_is_missing"])[:200],
                   "HOLD before Discovery -- there is not enough material to write from"]
        A[C.SHADOW_DECISION] = _emit(
            C.SHADOW_DECISION, at,
            {"decision": "HOLD", "reasons": reasons, "engine": ENGINE,
             "reason_code": RS.HOLD,
             "policy": "ACCEPT = eligible for the candidate pool; never publication"},
            {"research_pack": A[C.RESEARCH_PACK]})
        _persist(A, run_root, name, mode, prov, "HOLD", reasons)
        return {"artifacts": A, "decision": "HOLD", "reasons": reasons,
                "provider": prov, "reason_code": RS.HOLD}

    # --- DISCOVERY: consumes the anchor and the frozen pack ------------------
    try:
        d = S.discover(provider, src, sha, pack)
        prov["discovery"] = d.get("_provider", {})
        if d.get("commissionable") is False:
            # A grounded refusal. Recorded as a first-class outcome, not an error: the
            # source carries no mechanism this reading can reach.
            disc = _emit(C.DISCOVERY, at, _strip_provider(d),
                         {"source": A[C.SOURCE_SNAPSHOT],
                          "research_pack": A[C.RESEARCH_PACK]})
            A[C.DISCOVERY] = disc
            _persist(A, run_root, name, mode, prov,
                     decision="HOLD", reasons=["discovery: source not commissionable"])
            return {"artifacts": A, "decision": "HOLD",
                    "reasons": ["discovery: source not commissionable -- %s"
                                % str(d.get("disturbance", ""))[:200]],
                    "provider": prov}
        # CONTRACT REVISION 2026-08-24 (Part A): the designated source anchor must be an
        # exact span of the snapshot. Enforced BEFORE Article Form and before the writer, so
        # an ungrounded Discovery can never reach prose. Only mechanically harmless
        # differences are normalised away -- a paraphrase still fails. See invariants.py.
        ok, code, detail = INV.check_anchor(d, src)
        anchor_note = detail
        if not ok:
            # ONE bounded repair, exactness only, changing only the anchor field. No loop.
            # (repair_anchor already catches its own provider call internally and
            # degrades to "repair failed" rather than raising -- not re-caught here.)
            repaired, rdetail = INV.repair_anchor(provider, d, src)
            prov["anchor_repair"] = {"attempted": True, "succeeded": repaired,
                                     "detail": rdetail}
            if not repaired:
                reasons = ["%s: %s" % (code, detail), "anchor repair: %s" % rdetail,
                           "HOLD before writer -- Discovery is not source-grounded"]
                A[C.DISCOVERY] = _emit(C.DISCOVERY, at, _strip_provider(d),
                                       {"source": A[C.SOURCE_SNAPSHOT],
                                        "research_pack": A[C.RESEARCH_PACK]})
                A[C.SHADOW_DECISION] = _emit(
                    C.SHADOW_DECISION, at,
                    {"decision": "HOLD", "reasons": reasons, "engine": ENGINE,
                     "reason_code": code,
                     "policy": "ACCEPT = eligible for the candidate pool; never publication"},
                    {"discovery": A[C.DISCOVERY]})
                _persist(A, run_root, name, mode, prov, "HOLD", reasons)
                return {"artifacts": A, "decision": "HOLD", "reasons": reasons,
                        "provider": prov, "reason_code": code}
            ok, code, anchor_note = INV.check_anchor(d, src)
        # SUBJECT SCOPE (2026-08-28). Discovery may read the whole anchor, but it may
        # not ground its reading in a part of it nobody researched. Offsets only, over
        # the text check_anchor already validated the quote against. A run that trips
        # this HOLDs; it does not re-research, and it does not quietly switch subject.
        ok_scope, scope_code, scope_detail = INV.check_subject_scope(
            d, pack.get("subject_span", ""), src)
        if not ok_scope:
            reasons = ["%s: %s" % (scope_code, scope_detail),
                       "research subject: %s" % str(pack.get("subject", ""))[:160],
                       "HOLD before Article Form -- the researched subject and the "
                       "written subject must be the same subject"]
            A[C.DISCOVERY] = _emit(C.DISCOVERY, at, _strip_provider(d),
                                   {"source": A[C.SOURCE_SNAPSHOT],
                                    "research_pack": A[C.RESEARCH_PACK]})
            A[C.SHADOW_DECISION] = _emit(
                C.SHADOW_DECISION, at,
                {"decision": "HOLD", "reasons": reasons, "engine": ENGINE,
                 "reason_code": scope_code,
                 "policy": "ACCEPT = eligible for the candidate pool; never publication"},
                {"discovery": A[C.DISCOVERY], "research_pack": A[C.RESEARCH_PACK]})
            _persist(A, run_root, name, mode, prov, "HOLD", reasons)
            return {"artifacts": A, "decision": "HOLD", "reasons": reasons,
                    "provider": prov, "reason_code": scope_code}
        d["subject_scope_verified"] = True
        d["source_anchor_verified"] = True
        A[C.DISCOVERY] = _emit(C.DISCOVERY, at, _strip_provider(d),
                               {"source": A[C.SOURCE_SNAPSHOT],
                                "research_pack": A[C.RESEARCH_PACK]})
    except (ProviderError, C.ContractViolation) as e:
        return _stage_failure(
            C.DISCOVERY,
            "provider_error" if isinstance(e, ProviderError) else "invalid_response_shape",
            e, at, A, run_root, name, mode, prov)

    # --- ARTICLE FORM: consumes discovery + source ---------------------------
    try:
        f = S.make_form(provider, d, src, sha, pack)
        prov["article_form"] = f.get("_provider", {})
        A[C.ARTICLE_FORM] = _emit(C.ARTICLE_FORM, at, _strip_provider(f),
                                  {"discovery": A[C.DISCOVERY],
                                   "source": A[C.SOURCE_SNAPSHOT],
                                   "research_pack": A[C.RESEARCH_PACK]})
    except (ProviderError, C.ContractViolation) as e:
        return _stage_failure(
            C.ARTICLE_FORM,
            "provider_error" if isinstance(e, ProviderError) else "invalid_response_shape",
            e, at, A, run_root, name, mode, prov)

    # --- WRITER INPUT: derived from the Form. Deterministic, no model. --------
    wi = S.build_writer_input(f, d, src, sha, byline, pack)
    A[C.WRITER_INPUT] = _emit(C.WRITER_INPUT, at, wi,
                              {"article_form": A[C.ARTICLE_FORM],
                               "source": A[C.SOURCE_SNAPSHOT],
                               "research_pack": A[C.RESEARCH_PACK]})

    # --- WRITER: prose only --------------------------------------------------
    wo = S.write(provider, wi)
    prov["writer"] = wo.get("_provider", {})

    if wo["provider_status"] != "ok":
        # PART B (2026-08-24). decision.py anticipates provider_status != "ok", but
        # contracts.validate() requires a NON-EMPTY article_text, so a failed writer
        # cannot be expressed as a valid WRITER_OUTPUT. Rather than edit a frozen
        # contract or fabricate placeholder prose, the failure gets its own first-class
        # record -- RUN_STATUS -- and the run HOLDs. No WRITER_OUTPUT artifact is
        # emitted, so nothing downstream can mistake a failure for a draft.
        run_status = {
            "status": "PROVIDER_FAILURE",
            "stage": C.WRITER_OUTPUT,
            "failure_category": "writer_provider_unavailable",
            "provider": (wo.get("_provider") or {}).get("provider", "unknown"),
            "requested_model": (wo.get("_provider") or {}).get(
                "requested_model", getattr(provider, "model", "unknown")),
            "actual_model": (wo.get("_provider") or {}).get("actual_model", ""),
            "error": wo.get("provider_error", "")[:500],
            "run": name,
            "created_at": at,
            "engine": ENGINE,
            "writer_output_emitted": False,
            "article_produced": False,
        }
        reasons = ["writer provider failed; HOLD, no template fallback",
                   "RUN_STATUS=PROVIDER_FAILURE recorded; no WRITER_OUTPUT artifact "
                   "emitted, so no empty or placeholder article exists"]
        A[C.SHADOW_DECISION] = _emit(
            C.SHADOW_DECISION, at,
            {"decision": "HOLD", "reasons": reasons, "engine": ENGINE,
             "reason_code": "WRITER_PROVIDER_FAILURE",
             "policy": "ACCEPT = eligible for the candidate pool; never publication"},
            {"writer_input": A[C.WRITER_INPUT]})
        _persist(A, run_root, name, mode, prov, "HOLD", reasons, run_status=run_status)
        return {"artifacts": A, "decision": "HOLD", "reasons": reasons,
                "provider": prov, "run_status": run_status,
                "reason_code": "WRITER_PROVIDER_FAILURE"}

    # write()'s success path (provider_status == "ok") is not model-parsed JSON --
    # article_sha256 is always computed from article_text in the same expression, and
    # provider_status is always the literal "ok" -- so contracts.validate() cannot
    # diverge on those two fields. article_text could in principle be empty (the one
    # field _require() treats as missing), but provider.py's real Provider already
    # raises ProviderError on an empty completion before write() ever reaches this
    # branch. Wrapped anyway, for the same reason the other three stages are: this
    # boundary should not depend on a guarantee living in a different module holding
    # forever, and a caller satisfying write()'s duck-typed provider interface
    # differently must still fail closed here, not raise uncaught.
    try:
        A[C.WRITER_OUTPUT] = _emit(C.WRITER_OUTPUT, at, _strip_provider(wo),
                                   {"writer_input": A[C.WRITER_INPUT]})
    except C.ContractViolation as e:
        return _stage_failure(C.WRITER_OUTPUT, "invalid_response_shape", e, at, A,
                              run_root, name, mode, prov)

    # --- WRITER GROUNDING: writer output + source ONLY (never the Form) -------
    try:
        gf = S.ground(provider, wo["article_text"], src, sha, pack)
        prov["grounding"] = gf.get("_provider", {})
    except (ProviderError, C.ContractViolation) as e:
        return _stage_failure(
            C.GROUNDING_FINDINGS,
            "provider_error" if isinstance(e, ProviderError) else "invalid_response_shape",
            e, at, A, run_root, name, mode, prov)

    # --- PATCH-ONLY REPAIR, then a real re-check of the affected findings -----
    findings_now = gf["findings"]
    current_text = wo["article_text"]
    rp = S.repair(wo["article_text"], gf["findings"])
    if rp is not None:
        try:
            recheck = S.ground(provider, rp["article_text"], src, sha, pack)
        except ProviderError as e:
            # The recheck's own parsed findings never reach a separate _emit -- only
            # `rp`'s deterministic shape does -- so ProviderError is the only risk here.
            return _stage_failure(C.GROUNDING_FINDINGS, "provider_error", e, at, A,
                                  run_root, name, mode, prov)
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
        current_text = rp["article_text"]
        findings_now = recheck["findings"]

    # --- UNCERTAINTY ADJUDICATION: one pass, pack-only, then one re-grounding --
    # decision.py's V0 rule is unchanged and still fail-closed: an uncertain finding
    # HOLDs unless the grounding payload says it was adjudicated. What is new is that
    # something can now do the adjudicating, because the writer no longer had one
    # source. The adjudicator sees the article and the frozen pack, may only keep,
    # weaken or remove a claim, and is believed about nothing: the re-grounding below
    # decides, and any uncertainty that survives it still HOLDs.
    uncertain = [f for f in findings_now
                 if f.get("classification") == "TRUE_UNCERTAIN"]
    if uncertain:
        try:
            raw = S.adjudicate(provider, current_text, src, sha, uncertain, pack)
            prov["uncertainty_adjudication"] = raw.get("_provider", {})
            adj = S.apply_adjudication(current_text, uncertain, raw, pack)
            after = S.ground(provider, adj["article_text"], src, sha, pack)
            prov["grounding_after_adjudication"] = after.get("_provider", {})
        except (ProviderError, C.ContractViolation) as e:
            return _stage_failure(
                C.GROUNDING_FINDINGS,
                "provider_error" if isinstance(e, ProviderError) else "invalid_response_shape",
                e, at, A, run_root, name, mode, prov)

        residual_uncertain = [f for f in after["findings"]
                              if f.get("classification") == "TRUE_UNCERTAIN"]
        residual_unsupported = [f for f in after["findings"]
                                if f.get("classification") == "TRUE_UNSUPPORTED"]
        def _n(s):
            return " ".join((s or "").split()).lower()

        still = [_n(f.get("quote")) for f in residual_uncertain]
        for rec in adj["records"]:
            if rec["action"] == "MATERIAL_UNRESOLVED":
                rec["verified_by_regrounding"] = False
                continue
            # Containment either way, not string equality: the second grounder quotes
            # the span it doubts, which is rarely the exact clause the adjudicator
            # touched. Equality made a record read "verified" while the run was HOLDing
            # on that very claim -- seen in the 28 August live run.
            now = _n(rec["replacement"] if rec["applied"] else rec["claim"])
            rec["verified_by_regrounding"] = not any(
                now and (now in s or s in now) for s in still)

        clean = not (residual_uncertain or residual_unsupported
                     or adj["material_unresolved"])
        # The flag decision.py reads. Set only when the SECOND grounding found nothing
        # unresolved -- never because the adjudicator said so.
        gf["uncertain_adjudicated"] = bool(clean)
        gf["uncertainty_adjudication"] = {
            "records": adj["records"],
            "material_unresolved": adj["material_unresolved"],
            "residual_uncertain": len(residual_uncertain),
            "residual_unsupported": len(residual_unsupported),
            "patches_applied": len(adj["patches"]),
            "regrounding_status": after.get("status"),
            # Persisted even when nothing was patched: without it, a HOLD caused by the
            # second grounding is unanswerable after the fact -- which is exactly what
            # happened on the first live run of this stage.
            "regrounding_findings": after.get("findings", []),
            "passes": 1,
        }
        if adj["patches"]:
            before_unsupported = {f_.get("quote") for f_ in gf["findings"]
                                  if f_.get("classification") == "TRUE_UNSUPPORTED"}
            if rp is None:
                rp = {"mode": "patch_only", "patches": [], "unpatched_finding_ids": [],
                      "verification": {"residual": 0, "introduced": 0,
                                       "unrelated_edits": 0}}
            rp["patches"] = list(rp["patches"]) + adj["patches"]
            rp["article_text"] = adj["article_text"]
            rp["article_sha256"] = adj["article_sha256"]
            rp["recheck_findings"] = after["findings"]
            rp["verification"]["residual"] = len(
                [f_ for f_ in residual_unsupported if f_.get("quote") in before_unsupported])
            rp["verification"]["introduced"] = len(
                [f_ for f_ in residual_unsupported
                 if f_.get("quote") not in before_unsupported])

    A[C.GROUNDING_FINDINGS] = _emit(C.GROUNDING_FINDINGS, at, _strip_provider(gf),
                                    {"writer_output": A[C.WRITER_OUTPUT],
                                     "source": A[C.SOURCE_SNAPSHOT],
                                     "research_pack": A[C.RESEARCH_PACK]})
    if rp is not None:
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
             prov: dict, decision: str, reasons: list,
             run_status: dict | None = None) -> None:
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
    if run_status is not None:
        (out / "RUN_STATUS.json").write_text(
            json.dumps(run_status, indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8")
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
        "run_status": (run_status or {"status": "OK"})["status"],
        "publication": "NONE -- candidate only, not connected to any selector or publish path",
    }, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
