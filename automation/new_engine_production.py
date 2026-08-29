#!/usr/bin/env python3
"""
new_engine_production.py -- the scheduled CURRENT_ENGINE generation path.

Called by production_orchestrator when CRIPMINDS_ENGINE=new_engine_v1. This is a REAL
production run, not a rehearsal:

    normal upstream source selection/acquisition   (stabilised legacy infrastructure)
      -> NEW_ENGINE_V1 Discovery -> Article Form -> Writer -> Writer Grounding
      -> ACCEPT / HOLD
      -> on ACCEPT: CURRENT_ENGINE publication-safety bridge
      -> on bridge pass: candidate with publication_eligible: true
      -> ordinary candidate pool -> existing periodic selector

ACCEPT != PUBLISH. Nothing here publishes; the selector remains the publication owner and
runs on its own unchanged cadence.

ONE usable story -> ONE editorial run -> ACCEPT or HOLD -> stop. No candidate rotation:
a HOLD is a normal production outcome, not a reason to try another story.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import sqlite3
import re
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import new_engine_candidate as CAND                      # noqa: E402
import news_fetcher as NF                                # noqa: E402
import selector_v2 as SV                                 # noqa: E402
import publication_safety_bridge as BRIDGE               # noqa: E402
import title_coherence as TC                             # noqa: E402
from new_engine_v1 import contracts as C                 # noqa: E402
from new_engine_v1 import runner as R                    # noqa: E402
from new_engine_v1.provider import Provider, DEFAULT_MODEL  # noqa: E402

# Private evidence root. Never inside the repo: raw runs stay out of the public tree.
DEFAULT_EVIDENCE_ROOT = os.environ.get(
    "NEW_ENGINE_EVIDENCE_ROOT", "/srv/data/cripminds-new-engine-v1")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "candidate").lower()).strip("-")[:70]


def _title_from(body: str, fallback: str, writer_title: str = "") -> str:
    """The candidate's headline.

    Order: the writer's own TITLE line; then a short heading the body opens with; then
    the source headline, but ONLY if it actually describes this article; then nothing.

    The coherence gate exists because of production-20260827T070010Z-fd846f06, where a
    roundup source was headlined for one project, Discovery selected a different project
    from the same roundup, and the candidate inherited the source headline unchecked --
    shipping an article about a tactile exhibition system titled for a mountain trike it
    never mentions. An honestly untitled candidate is better than a confidently wrong
    headline, and a candidate is not published from here anyway.
    """
    t = (writer_title or "").strip()
    if t:
        return t[:110]
    for line in (body or "").strip().splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            if len(line.split()) <= 18 and TC.is_coherent(line, body):
                return line[:110]
            break
    fb = (fallback or "").strip()
    if fb and fb != "Untitled" and TC.is_coherent(fb, body):
        return fb[:110]
    return "Untitled"


def _record_seed_attempt(orch, seed: dict, run: str, out: dict, result: dict) -> None:
    """Tell the seed pool that CURRENT_ENGINE tried this anchor, and how it went.

    Without this the pool never learned: `used` is set only by the legacy path on
    commit_success, which this engine never reaches, so the 09:00 selector kept
    re-choosing the same top-scoring seed. Live evidence: 25+26 August ran one MIT
    Tech Review seed, 27+28 August one Dezeen roundup -- four runs, two anchors.

    Terminal/retryable is decided by the orchestrator's own classifier from structured
    run fields, and the Research Pack's verdict is recorded where the run reached it.
    Recorded, not yet ranked on: how a verdict should influence future selection is a
    NEWS/POOL V2 decision, not this one. A failure to write this back must never fail a
    run that has otherwise completed.
    """
    try:
        pack = (out.get("artifacts") or {}).get(C.RESEARCH_PACK)
        payload = pack.payload if pack is not None else {}
        klass, outcome = orch.classify_current_engine_attempt(result)
        orch.mark_news_seed_current_engine_attempt(
            seed["id"], run=run, klass=klass, outcome=outcome,
            pack_verdict=(payload.get("sufficiency") or {}).get("verdict"),
            pack_subject_words=payload.get("anchor_subject_words"))
    except Exception as e:                                  # never reaches the caller
        orch.logger.warning("CURRENT_ENGINE %s: seed attempt write-back failed: %s",
                            run, e)


def _selector_v2_shadow(orch, seed: dict, run: str, model: str) -> None:
    """SELECTOR V2, shadow only. OFF unless CRIPMINDS_SELECTOR_V2_SHADOW is set.

    Runs ONCE per run, at one point only: after the authoritative selector has chosen
    its anchor and that anchor's source has been acquired, and before the engine, the
    Research Pack, or any seed write-back has touched anything.

    That position is the whole comparison. _record_seed_attempt retires or rests the
    seed it is given -- ce_attempt_terminal on a terminal outcome, ce_retry_after on a
    retryable one -- and both are eligibility filters in the pool this reads. Run the
    shadow after that write-back and the authoritative winner may already have been
    removed from the universe the shadow ranks, which does not merely bias the result:
    it makes agreement unreachable, so every comparison would report a disagreement
    that never happened. The two selectors must see one pool.

    Running here costs the acquisition of up to a day's candidates before the article
    work starts. That is the price of a comparison that means anything, and it is only
    ever paid when the flag is set.

    It reuses the PRODUCTION acquisition path (`get_source_text` plus the orchestrator's
    own classification), because a second weaker fetcher would mark whole publishers
    unreadable and make the comparison a lie.

    Every failure is contained. An experiment must never be able to break a run -- not by
    raising, not by leaving a connection open on the seed database that production is
    about to write to. The exception is logged as a SELECTOR_V2 warning rather than
    swallowed silently: an experiment that quietly stops running is worse than one that
    visibly fails.
    """
    if not SV.enabled():
        return
    conn = None
    try:
        conn = sqlite3.connect(str(orch.discovery_db))

        def acquire(url):
            text = orch.get_source_text(url)
            status, _reason = orch.classify_source_acquisition(
                text or "", orch.get_source_origin(url),
                orch.get_source_paragraph_count(url))
            return (text or ""), status

        report = SV.run_shadow(
            conn, Provider(model=model), acquire=acquire,
            score_item=NF.score_item, boosters=NF.DISABILITY_BOOSTERS,
            keyword_matches=NF._keyword_matches,
            old_winner={"id": seed["id"], "title": seed.get("title"),
                        "source_name": seed.get("source_name"),
                        "relevance_score": seed.get("relevance_score")})
        SV.record_comparison(conn, run, report)
        w = report.get("shadow_winner") or {}
        orch.logger.info(
            "SELECTOR_V2 shadow %s: old=%s | shadow=%s (%s) | same=%s | "
            "candidates=%d fetched=%d calls=%d",
            run, (seed.get("title") or "")[:60], (w.get("title") or "none")[:60],
            w.get("assessment"), report.get("same_winner"),
            report["metrics"]["candidates"], report["metrics"]["fetched"],
            report["metrics"]["model_calls"])
    except Exception as e:                                # never reaches the caller
        orch.logger.warning("SELECTOR_V2 shadow failed (ignored, run unaffected): %s: %s",
                            type(e).__name__, str(e)[:300])
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def run_scheduled(orch, *, rehearsal: bool = False,
                  evidence_root: str | None = None,
                  model: str = DEFAULT_MODEL, research_fn=None) -> dict:
    """One scheduled CURRENT_ENGINE run. `orch` is the production orchestrator.

    Source acquisition reuses the stabilised upstream path; no legacy commission or Fable
    interpretation is produced or consumed. NEW_ENGINE_V1 owns everything after the
    source.
    """
    if R.current_mode() != R.MODE_LIVE:
        # The engine's own switch must be on too. Two explicit switches, no implicit run.
        return {"status": "skipped",
                "message": "CRIPMINDS_ENGINE=new_engine_v1 but NEW_ENGINE_V1_MODE=%r; "
                           "refusing to run implicitly" % R.current_mode()}

    seed = orch.get_news_seed_with_usable_source()
    if not seed:
        attempts = getattr(orch, "_source_acquisition_attempts", [])
        exhausted = getattr(orch, "_source_acquisition_exhausted", False)
        return {"status": ("no_article_source_acquisition_exhausted" if exhausted
                           else "no_usable_source"),
                "engine": "new_engine_v1", "attempts": attempts,
                "message": "no usable source; NEW_ENGINE_V1 not run"}

    text = orch.get_source_text(seed["url"], fallback_text=seed.get("summary"),
                               underlying_url=seed.get("underlying_article_url"))
    payload = {
        "source_text": text,
        "source_sha256": C.sha256_text(text),
        "provenance": {
            "origin": orch.get_source_origin(seed["url"]),
            "url": seed["url"], "seed_id": seed["id"],
            "source_name": seed.get("source_name"), "title": seed.get("title"),
            "original_length_chars": orch.get_source_original_length(seed["url"]),
            "paragraph_count": orch.get_source_paragraph_count(seed["url"]),
            "acquired_via": "SOURCE_ACQUISITION_RETRY_V1 (normal upstream mechanism)",
            "legacy_commission_used": False,
        },
    }

    now = datetime.datetime.now(datetime.timezone.utc)
    run = "%s-%s-%s" % ("rehearsal" if rehearsal else "production",
                        now.strftime("%Y%m%dT%H%M%SZ"), payload["source_sha256"][:8])
    root = pathlib.Path(evidence_root or DEFAULT_EVIDENCE_ROOT)
    orch.logger.info("CURRENT_ENGINE run %s — source %s (%s chars)",
                     run, payload["provenance"]["url"],
                     payload["provenance"]["original_length_chars"])

    # The anchor is now fixed and its source is in hand, and nothing has yet written
    # back to the seed pool. This is the only moment at which the two selectors can be
    # compared honestly -- see _selector_v2_shadow.
    _selector_v2_shadow(orch, seed, run, model)

    out = R.run(payload, root, Provider(model=model), run, now.isoformat(),
                research_fn=research_fn)
    (root / run / "ACQUISITION.json").write_text(json.dumps(
        {"seed_id": seed["id"],
         "attempts": getattr(orch, "_source_acquisition_attempts", []),
         "engine": "new_engine_v1"}, indent=2, sort_keys=True), encoding="utf-8")

    result = {"status": "hold" if out["decision"] != "ACCEPT" else "accept",
              "engine": "new_engine_v1", "engine_generation": CAND.ENGINE_GENERATION,
              "engine_run": run, "decision": out["decision"],
              "reasons": out["reasons"], "reason_code": out.get("reason_code"),
              # Propagated so a caller (production_orchestrator.py's __main__) can
              # tell an infrastructure/contract failure apart from an ordinary
              # editorial HOLD -- both HOLD here, but only one needs an operator
              # signal. Absent (None) for an ordinary editorial HOLD.
              "run_status": out.get("run_status"),
              "evidence": str(root / run), "commit_success": False,
              "source_url": payload["provenance"]["url"]}

    if out["decision"] != "ACCEPT":
        orch.logger.warning("CURRENT_ENGINE %s: HOLD — %s", run, "; ".join(out["reasons"])[:300])
        _record_seed_attempt(orch, seed, run, out, result)
        return result

    # ── ACCEPT: run the publication-safety bridge ────────────────────────────
    # CURRENT_ENGINE uses the STRICT fact-check contract (strict=True): an extraction
    # failure or a zero-claim result must reach the bridge as an explicit failure state,
    # not as an empty-and-therefore-clean result. Legacy callers keep strict=False.
    _fc = getattr(orch, "_run_web_fact_check", None)
    _strict_fc = (lambda text: _fc(text, strict=True)) if _fc else None
    bridge = BRIDGE.evaluate(out, fact_check_fn=_strict_fc)
    (root / run / "SAFETY_BRIDGE.json").write_text(
        json.dumps(bridge.summary(), indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8")
    result["safety_bridge"] = bridge.summary()
    for c in bridge.checks:
        orch.logger.info("CURRENT_ENGINE safety %-32s %s  %s",
                         c["check"], "PASS" if c["ok"] else "FAIL", c["detail"][:120])

    body = CAND.final_body(out)
    meta = CAND.engine_meta_from_run(out, run=run, generated_at=now.isoformat(),
                                     source_url=payload["provenance"]["url"],
                                     provider_model=model)
    _wo = out["artifacts"][C.WRITER_OUTPUT].payload if C.WRITER_OUTPUT in out["artifacts"] else {}
    _src_headline = payload["provenance"].get("title") or "Untitled"
    title = _title_from(body, _src_headline, writer_title=_wo.get("title", ""))
    if title == "Untitled":
        orch.logger.warning(
            "CURRENT_ENGINE %s: no usable headline -- writer supplied none and the source "
            "headline does not describe this article (%s)",
            run, TC.describe(_src_headline, body))
    path = CAND.persist_candidate(
        drafts_dir=orch.drafts_dir, slug=_slug(title), body=body, title=title,
        author=R.DEFAULT_BYLINE, engine_meta=meta, rehearsal=rehearsal,
        safety=BRIDGE.stamp_fields(bridge))
    result["candidate"] = str(path)
    result["publication_eligible"] = bool(bridge.eligible and not rehearsal)
    (root / run / "CANDIDATE.json").write_text(json.dumps(
        {"path": str(path), "engine_meta": meta, "body_sha256": C.sha256_text(body),
         "publication_eligible": result["publication_eligible"]},
        indent=2, sort_keys=True), encoding="utf-8")
    _record_seed_attempt(orch, seed, run, out, result)
    orch.logger.info("CURRENT_ENGINE %s: ACCEPT — candidate %s (publication_eligible=%s)",
                     run, path.name, result["publication_eligible"])
    return result
