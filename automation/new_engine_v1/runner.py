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

from . import anchors as AN
from . import contracts as C
from . import invariants as INV
from . import grounding_v2 as GV2
from . import repair_identity as RI
from . import research as RS
from . import stages as S
from .decision import decide
from .provider import ProviderError
from . import composition as CP

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
        mode: str | None = None, research_fn=None, fact_check_fn=None) -> dict:
    """Execute the target path once against real material.

    `source_payload` must already satisfy the SOURCE_SNAPSHOT contract -- acquisition is
    upstream production's job, not this engine's, and passing it in keeps this package
    free of any legacy import.

    `fact_check_fn` is injected for the same reason and used only by the
    story-architecture composition path: the authoritative Fact Check is part of the
    legacy orchestrator, which this package may not import. Production supplies
    `composition_factual_bridge.fact_check`; a test supplies its own, and an absent
    callable is reported NOT_RUN rather than passed.
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

    # --- COMPOSITION SELECTOR ------------------------------------------------
    # Two engines share everything up to here: acquisition, research and the sufficiency
    # verdict are the same work whichever path composes the article. They diverge on what
    # happens to approved material.
    #
    #   legacy             Discovery -> Article Form -> Writer Input -> Writer -> Ground
    #   story_architecture Ledger -> Worth -> Architect -> CUT -> Writer -> Continuity
    #                      -> safety -> Ground -> Fact Check -> Reader
    #
    # Default is legacy. The story-architecture path emits the three artifacts it really
    # produces -- WRITER_OUTPUT, GROUNDING_FINDINGS, SHADOW_DECISION -- and writes its own
    # stage artifacts beside them. It does NOT call decide(): that function requires the
    # legacy Discovery/Article Form/Writer Input lineage, which this path does not have,
    # and it is a frozen verbatim port that must not be adapted. The composition ladder is
    # this path's decision, and it is the stricter of the two.
    try:
        engine = CP.current_composition_engine()
    except CP.UnknownCompositionEngine as e:
        raise EngineDisabled(str(e))
    if engine == CP.COMPOSITION_STORY_ARCHITECTURE:
        return _run_story_architecture(
            provider, A, prov, pack, src, sha, at, run_root, name, mode, fact_check_fn)

    # --- DISCOVERY: consumes the anchor and the frozen pack ------------------
    # The anchor is SELECTED, not written (PR #61). Candidates are cut deterministically
    # from the anchor source -- narrowed to the researched subject when the pack recorded
    # one -- so the span Discovery picks is source bytes by construction and cannot come
    # from the research pack, which is where all four of the 3 September anchor holds
    # actually took their (verbatim, correctly copied) quotes from.
    anchor_cands = AN.candidates(src, pack.get("subject_span", ""))
    if not anchor_cands:
        reasons = ["%s: the anchor source yielded no bounded span of at least %d chars"
                   % (INV.NO_ANCHOR_CANDIDATES, INV.MIN_ANCHOR_CHARS),
                   "HOLD before Discovery -- there is nothing to anchor a reading in"]
        A[C.SHADOW_DECISION] = _emit(
            C.SHADOW_DECISION, at,
            {"decision": "HOLD", "reasons": reasons, "engine": ENGINE,
             "reason_code": INV.NO_ANCHOR_CANDIDATES,
             "policy": "ACCEPT = eligible for the candidate pool; never publication"},
            {"research_pack": A[C.RESEARCH_PACK]})
        _persist(A, run_root, name, mode, prov, "HOLD", reasons)
        return {"artifacts": A, "decision": "HOLD", "reasons": reasons,
                "provider": prov, "reason_code": INV.NO_ANCHOR_CANDIDATES}
    try:
        d = S.discover(provider, src, sha, pack, anchor_cands)
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
        # Selection outcome first: a missing, unknown or explicitly-NONE id is a HOLD,
        # never a fallback to model-written text. check_anchor then still runs as the
        # final guarantee -- with selection it should be unfailable, and if it ever does
        # fail the mapping is wrong and holding is the only safe answer.
        sel = d.get("_anchor") or {}
        ok, code, detail = INV.check_anchor(d, src)
        if not sel.get("ok"):
            ok, code, detail = False, sel.get("code") or INV.ANCHOR_ID_MISSING, \
                sel.get("detail") or "anchor selection did not resolve"
        anchor_note = detail
        prov["anchor_selection"] = {"candidates": sel.get("candidates", 0),
                                    "resolved": bool(sel.get("ok")),
                                    "detail": sel.get("detail", "")}
        if not ok:
            reasons = ["%s: %s" % (code, detail),
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
        A[C.GROUNDING_FINDINGS] = _emit(C.GROUNDING_FINDINGS, at, _strip_provider(gf),
                                        {"writer_output": A[C.WRITER_OUTPUT],
                                         "source": A[C.SOURCE_SNAPSHOT],
                                         "research_pack": A[C.RESEARCH_PACK]})
    except (ProviderError, C.ContractViolation) as e:
        return _stage_failure(
            C.GROUNDING_FINDINGS,
            "provider_error" if isinstance(e, ProviderError) else "invalid_response_shape",
            e, at, A, run_root, name, mode, prov)

    # --- PATCH-ONLY REPAIR, then a real re-check of the affected findings -----
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
        # Attribution comes from the ARTICLE, not from pass 1's classifications.
        #
        # This used to be a set difference over pass-1 TRUE_UNSUPPORTED quote strings,
        # which answered a question nobody asked: "was this exact string already called
        # unsupported?" A sentence the repair never touched, reclassified on the second
        # pass, came out labelled as a claim the repair created -- measured on
        # production-20260903T135702Z-3ea6156a, where one clause was patched and two
        # untouched sentences were blamed on it.
        #
        # The repair is a deterministic clause substitution, so its changed regions are
        # computable and each pass-2 finding either overlaps text the repair wrote or
        # does not. All four resulting states still HOLD; only the sentence the run
        # writes about itself changes.
        acct = RI.account(wo["article_text"], rp["article_text"], rp.get("patches"),
                          gf["findings"], recheck["findings"])
        rp["verification"].update(acct)
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
    _shadow_grounding_v2(provider, run_root / name, wo, src, pack)
    return {"artifacts": A, "decision": decision, "reasons": reasons, "provider": prov}


def _run_story_architecture(provider, A: dict, prov: dict, pack: dict, src: str,
                            sha: str, at: str, run_root: pathlib.Path, name: str,
                            mode: str, fact_check_fn=None) -> dict:
    """The story-architecture composition path, from the frozen research pack onwards."""
    out_dir = run_root / name
    result = CP.run_story_architecture_composition(
        provider, pack=pack, source_text=src, source_sha=sha,
        subject=pack.get("subject", ""), out_dir=out_dir,
        fact_check_fn=fact_check_fn)
    prov["composition"] = {s: (d or {}).get("provider", {})
                           for s, d in (result.get("detail") or {}).items()
                           if isinstance(d, dict) and d.get("provider")}
    prov["composition_engine"] = CP.COMPOSITION_STORY_ARCHITECTURE

    article = result.get("article_text") or ""
    det = result.get("detail") or {}
    passed = result["status"] == CP.PASS

    # A candidate that reached prose gets a real WRITER_OUTPUT, whether or not a later
    # gate held it. A run that never reached prose emits none, for the same reason the
    # legacy writer-failure path emits none: nothing downstream may mistake a failure for
    # a draft.
    if article.strip():
        wo = {"article_text": article,
              "article_sha256": C.sha256_text(article),
              "provider_status": "ok"}
        try:
            A[C.WRITER_OUTPUT] = _emit(C.WRITER_OUTPUT, at, wo,
                                       {"research_pack": A[C.RESEARCH_PACK]})
        except C.ContractViolation as e:
            return _stage_failure(C.WRITER_OUTPUT, "invalid_response_shape", e, at, A,
                                  run_root, name, mode, prov)
    gf = (det.get(CP.GROUNDING) or {}).get("grounding")
    if gf and C.WRITER_OUTPUT in A:
        try:
            A[C.GROUNDING_FINDINGS] = _emit(C.GROUNDING_FINDINGS, at, gf,
                                            {"writer_output": A[C.WRITER_OUTPUT],
                                             "source": A[C.SOURCE_SNAPSHOT],
                                             "research_pack": A[C.RESEARCH_PACK]})
        except C.ContractViolation as e:
            return _stage_failure(C.GROUNDING_FINDINGS, "invalid_response_shape", e, at,
                                  A, run_root, name, mode, prov)

    if passed:
        decision = "ACCEPT"
        reasons = ["story_architecture: all ten stages passed",
                   "stages: %s" % ", ".join("%s=%s" % (s, result["stages"][s])
                                            for s in CP.STAGES),
                   "ACCEPT = eligible for the candidate pool; never publication"]
    else:
        decision = "HOLD"
        reasons = ["story_architecture HOLD at %s (%s)"
                   % (result["failure_stage"], result["reason_code"]),
                   str(result["failure_reason"])[:400]]

    dec_inputs = {"research_pack": A[C.RESEARCH_PACK]}
    if C.WRITER_OUTPUT in A:
        dec_inputs["writer_output"] = A[C.WRITER_OUTPUT]
    if C.GROUNDING_FINDINGS in A:
        dec_inputs["findings"] = A[C.GROUNDING_FINDINGS]
    A[C.SHADOW_DECISION] = _emit(
        C.SHADOW_DECISION, at,
        {"decision": decision, "reasons": reasons, "engine": ENGINE,
         "composition_engine": CP.COMPOSITION_STORY_ARCHITECTURE,
         "reason_code": result.get("reason_code") or "",
         "policy": "ACCEPT = eligible for the candidate pool; never publication"},
        dec_inputs)

    _persist(A, run_root, name, mode, prov, decision, reasons)
    return {"artifacts": A, "decision": decision, "reasons": reasons,
            "provider": prov, "composition": result,
            "reason_code": result.get("reason_code")}


def _shadow_grounding_v2(provider, out_dir: pathlib.Path, wo: dict, src: str,
                         pack: dict) -> None:
    """GROUNDER V2, shadow only. OFF unless explicitly enabled.

    Called AFTER the decision is made and persisted, and its result is written to its
    own file -- never into the artifact map, so `decide()` and the safety bridge cannot
    see it even by accident. It cannot set GROUNDING_FINDINGS, cannot trigger repair,
    cannot reach the fact check, and cannot make a held article publishable. Any failure
    inside it is swallowed and recorded: a comparison experiment must never be able to
    change the outcome of a production run, including by raising.
    """
    if not GV2.enabled():
        return
    try:
        payload = GV2.run_shadow(provider, article_text=wo.get("article_text", ""),
                                 pack=pack)
    except Exception as e:                                    # never reaches the caller
        payload = {"shadow": True, "error": "%s: %s" % (type(e).__name__, str(e)[:300]),
                   "authority": "NONE"}
    try:
        (out_dir / ("%s.json" % GV2.ARTIFACT)).write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8")
    except Exception:
        pass


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
