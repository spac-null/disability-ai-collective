#!/usr/bin/env python3
"""
new_engine_v1_rehearsal.py -- ONE controlled NEW_ENGINE_V1 cutover rehearsal.

    normal upstream source selection/acquisition   (legacy infrastructure, reused)
      -> NEW_ENGINE_V1: Discovery -> Article Form -> Writer -> Writer Grounding
      -> ACCEPT / HOLD
      -> production adapter: HOLD = evidence only | ACCEPT = candidate + interlock

NOT public publication. NOT a P2 sample. The candidate is written with the publication
interlock ON, so the selector deterministically ignores it.

Requires BOTH switches, explicitly:
    CRIPMINDS_ENGINE=new_engine_v1
    NEW_ENGINE_V1_MODE=LIVE

ONE usable chosen story -> ONE new-engine editorial run -> ACCEPT or HOLD -> stop.
There is no candidate rotation here: the legacy PREWRITER loop must not become a
wrapper that retries the new engine because a HOLD is inconvenient.

Usage (trident):
  CRIPMINDS_ENGINE=new_engine_v1 NEW_ENGINE_V1_MODE=LIVE \
    python3 automation/new_engine_v1_rehearsal.py --out <private-dir>
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import engine_switch as ES                          # noqa: E402
import new_engine_candidate as CAND                 # noqa: E402
from new_engine_v1 import contracts as C            # noqa: E402
from new_engine_v1 import runner as R               # noqa: E402
from new_engine_v1.provider import Provider, DEFAULT_MODEL  # noqa: E402


def acquire_real_source():
    """One real source through the NORMAL upstream mechanism.

    Reuses the stabilised legacy infrastructure -- candidate selection,
    SOURCE_ACQUISITION_RETRY_V1, provenance, snapshot. It does NOT touch legacy
    commissioning: no Fable brief, no legacy editorial interpretation is produced or
    consumed. Once usable source material exists, NEW_ENGINE_V1 owns everything after it.
    """
    import production_orchestrator as po
    orch = po.ProductionOrchestrator()
    seed = orch.get_news_seed_with_usable_source()
    if not seed:
        return None, None, getattr(orch, "_source_acquisition_attempts", []), None
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
            "legacy_commission_used": False,
        },
    }
    return seed, payload, getattr(orch, "_source_acquisition_attempts", []), orch.drafts_dir


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "candidate").lower()).strip("-")[:70]


def _title_from(body: str, fallback: str) -> str:
    for line in body.strip().splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:110] if len(line.split()) <= 18 else fallback
    return fallback


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="private run-evidence root")
    ap.add_argument("--drafts", default=None,
                    help="candidate destination (defaults to the repo's _drafts/)")
    ap.add_argument("--byline", default=R.DEFAULT_BYLINE)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    engine = ES.resolve_engine()                     # fail-closed on an unknown value
    if engine != ES.NEW_ENGINE_V1:
        print("CRIPMINDS_ENGINE=%r, not %s. Refusing." % (engine, ES.NEW_ENGINE_V1))
        return 2
    if R.current_mode() != R.MODE_LIVE:
        print("NEW_ENGINE_V1_MODE=%r, not LIVE. Refusing." % R.current_mode())
        return 2

    seed, payload, attempts, drafts_default = acquire_real_source()
    if payload is None:
        print(json.dumps({"status": "no_usable_source", "attempts": attempts}, indent=2))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc)
    run = "rehearsal-%s-%s" % (now.strftime("%Y%m%dT%H%M%SZ"), payload["source_sha256"][:8])
    print("engine : %s   mode: %s" % (engine, R.current_mode()))
    print("source : %s" % payload["provenance"]["url"])
    print("origin : %s  chars=%s  paragraphs=%s  attempts=%d"
          % (payload["provenance"]["origin"],
             payload["provenance"]["original_length_chars"],
             payload["provenance"]["paragraph_count"], len(attempts)))
    print("model  : %s\nrun    : %s\n" % (args.model, run))

    out = R.run(payload, pathlib.Path(args.out), Provider(model=args.model),
                run, now.isoformat(), byline=args.byline)

    print("DECISION: %s" % out["decision"])
    for r in out["reasons"]:
        print("  - %s" % r)
    if out.get("reason_code"):
        print("  reason_code: %s" % out["reason_code"])

    (pathlib.Path(args.out) / run / "ACQUISITION.json").write_text(
        json.dumps({"attempts": attempts, "seed_id": payload["provenance"]["seed_id"],
                    "engine": engine}, indent=2, sort_keys=True), encoding="utf-8")

    # ── production adapter ────────────────────────────────────────────────────
    if out["decision"] != "ACCEPT":
        print("\nHOLD -> evidence preserved privately; NO candidate created, nothing "
              "published.")
        return 0

    body = CAND.final_body(out)
    meta = CAND.engine_meta_from_run(
        out, run=run, generated_at=now.isoformat(),
        source_url=payload["provenance"]["url"], provider_model=args.model)
    title = _title_from(body, payload["provenance"].get("title") or "Untitled")
    drafts = pathlib.Path(args.drafts) if args.drafts else drafts_default
    path = CAND.persist_candidate(drafts_dir=drafts, slug=_slug(title), body=body,
                                  title=title, author=args.byline, engine_meta=meta,
                                  rehearsal=True)
    print("\nACCEPT -> candidate persisted (NOT published, interlock ON):")
    print("  %s" % path)
    print("  engine_generation=%s editorial_engine=%s cutover_rehearsal=true "
          "publication_eligible=false" % (CAND.ENGINE_GENERATION, CAND.EDITORIAL_ENGINE))
    (pathlib.Path(args.out) / run / "CANDIDATE.json").write_text(
        json.dumps({"path": str(path), "engine_meta": meta,
                    "body_sha256": C.sha256_text(body)}, indent=2, sort_keys=True),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
