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
import re
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import new_engine_candidate as CAND                      # noqa: E402
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


def run_scheduled(orch, *, rehearsal: bool = False,
                  evidence_root: str | None = None,
                  model: str = DEFAULT_MODEL) -> dict:
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

    out = R.run(payload, root, Provider(model=model), run, now.isoformat())
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
    orch.logger.info("CURRENT_ENGINE %s: ACCEPT — candidate %s (publication_eligible=%s)",
                     run, path.name, result["publication_eligible"])
    return result
