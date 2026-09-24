"""Run the pre-registered relational-supply acquisition batch.

Consumes the FROZEN pool in rank order and runs the ordinary production path on each
candidate: production acquisition -> production research -> story-architecture composition,
unmodified, in the compose mode the scheduled run uses. It publishes nothing, writes nothing
to the discovery database, and repairs nothing.

THE STOP RULE IS THE DENOMINATOR. Stop when fresh definitions reach TARGET, or when attempts
reach MAX_ATTEMPTS, whichever comes first. Never on the number of relational hits -- that
would bias the one quantity this batch exists to measure.

An attempt is any candidate CONSUMED, including one that holds at research. That is the
strict reading of "18 pipeline runs": counting only the candidates that got as far as
composition would make the cap elastic, and a research hold is itself a supply finding.

THE CROSSING RUN IS NOT TRUNCATED. A run yields several definitions at once, so the target
is reached by overshooting it. Dropping the surplus would mean choosing which definitions to
keep, which is selection. Every definition of the run that crosses the line is kept and the
final count is reported as it falls.

CLUSTERING METADATA IS ATTACHED TO EVERY DEFINITION. Definitions from one plan share a
source, a ledger and an author call, so they are not independent trials. run_id, plan_dir,
seed_id, rank and source_name travel with each one so the batch can never later be counted
as N independent Bernoulli draws.

No detector call happens here. Classification is a separate step over the frozen batch.

Usage: relational_supply_batch.py <batch_dir>   (resumable; re-reads its own BATCH.json)
"""
import datetime
import hashlib
import json
import os
import pathlib
import sys
import time
import traceback

WORKSPACE = pathlib.Path("/srv/data/hermes/workspace/disability-ai-collective")
sys.path.insert(0, str(WORKSPACE / "automation"))
sys.path.insert(0, str(WORKSPACE / "automation" / "orchestrator"))

from new_engine_v1 import composition as CP          # noqa: E402
from new_engine_v1 import contracts as C             # noqa: E402
from new_engine_v1 import research as RS             # noqa: E402
import composition_factual_bridge as FCB             # noqa: E402
import claude_cli_provider as CCP                    # noqa: E402

TARGET_DEFINITIONS = 24
MAX_ATTEMPTS = 18

_ORCH = []


def _production_fetch(url: str) -> str:
    """The acquisition production actually uses, borrowed rather than reimplemented --
    a plain urllib GET is refused by several publishers this corpus reads most.
    Copied from the frozen rehearsal driver; nothing here writes to the database."""
    if not _ORCH:
        from production_orchestrator import ProductionOrchestrator
        _ORCH.append(ProductionOrchestrator())
    return _ORCH[0].get_source_text(url) or ""


def fetch(url: str) -> tuple:
    import urllib.request
    try:
        text = _production_fetch(url)
        if len(text.split()) >= 80:
            return text, ""
    except Exception as e:                                        # noqa: BLE001
        pass
    ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": ua})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
    except Exception as e:                                        # noqa: BLE001
        return "", "%s: %s" % (type(e).__name__, str(e)[:120])
    text = RS.strip_html(raw) if "<" in raw[:2000] else raw
    return text, "" if text.strip() else "empty after markup strip"


def anchor_pack(subject: str, url: str, now: str) -> tuple:
    text, err = fetch(url)
    if err or len(text.split()) < 80:
        return None, (err or "%d words" % len(text.split()))
    s = {"source_id": "S0", "role": "ANCHOR", "url": url, "accessed_at": now,
         "fetch_status": "ok", "text": text[:CP.FREEZE_SOURCE_CHARS]}
    s["sha256"] = C.sha256_text(s["text"])
    s["content_length"] = len(s["text"])
    return s, ""


def load_state(bd: pathlib.Path) -> dict:
    p = bd / "BATCH.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"schema": "relational-supply-batch-v1",
            "target_definitions": TARGET_DEFINITIONS, "max_attempts": MAX_ATTEMPTS,
            "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "attempts": [], "definitions": [], "closed": False, "close_reason": ""}


def save(bd: pathlib.Path, st: dict) -> None:
    (bd / "BATCH.json").write_text(
        json.dumps(st, indent=1, ensure_ascii=False, default=str), encoding="utf-8")


def main() -> int:
    bd = pathlib.Path(sys.argv[1])
    bd.mkdir(parents=True, exist_ok=True)

    pool_doc = json.loads((bd / "pool" / "POOL.json").read_text(encoding="utf-8"))
    body = (bd / "pool" / "POOL.json").read_bytes()
    want = (bd / "pool" / "POOL.sha256").read_text().split()[0]
    got = hashlib.sha256(body).hexdigest()
    if got != want:
        print("POOL HASH MISMATCH -- refusing to run.\n  frozen %s\n  now    %s"
              % (want, got))
        return 2
    print("pool verified: %s (%d candidates)" % (got[:16], pool_doc["pool_size"]))

    exc = json.loads((bd / ".claude" / "experiments"
                      / "relational-supply-acquisition-2026-09-24"
                      / "EXCLUSIONS.json").read_text(encoding="utf-8"))
    bad_terms = {t.strip().lower() for p in exc["plans"] for t in p["definition_terms"]}

    st = load_state(bd)
    done = {a["seed_id"] for a in st["attempts"]}
    if st["closed"]:
        print("batch already closed: %s" % st["close_reason"])
        return 0

    provider = CCP.ClaudeCLIProvider()
    print("transport: %s / %s / %s | model %s | compose %s"
          % (provider.auth.get("subscriptionType"), provider.auth.get("orgName"),
             provider.auth.get("apiProvider"), provider.model,
             CP.scheduled_compose_mode()))

    for cand in pool_doc["candidates"]:
        if st["closed"]:
            break
        if cand["seed_id"] in done:
            continue
        n_def = len(st["definitions"])
        n_att = len(st["attempts"])
        if n_def >= TARGET_DEFINITIONS:
            st["closed"], st["close_reason"] = True, (
                "reached %d fresh definitions (target %d)" % (n_def, TARGET_DEFINITIONS))
            break
        if n_att >= MAX_ATTEMPTS:
            st["closed"], st["close_reason"] = True, (
                "reached the %d-attempt cap with %d definitions -- CLOSED SHORT, no top-up"
                % (MAX_ATTEMPTS, n_def))
            break

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        run_id = "r%02d-seed%s" % (n_att + 1, cand["seed_id"])
        out_dir = bd / "runs" / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        rec = {"run_id": run_id, "rank": cand["rank"], "seed_id": cand["seed_id"],
               "url": cand["url"], "title": cand["title"],
               "source_name": cand["source_name"], "layer": cand["layer"],
               "exposed_via": cand["exposed_via"], "started_at": now,
               "outcome": "", "detail": "", "definitions": [], "model_calls": 0}
        print("\n%s rank %d  %s\n   %s" % ("=" * 78, cand["rank"],
                                           (cand["source_name"] or "")[:40],
                                           (cand["title"] or "")[:100]))
        t0 = time.time()
        calls0 = provider.calls
        try:
            anchor, err = anchor_pack(cand["title"] or cand["url"], cand["url"], now)
            if anchor is None:
                rec.update({"outcome": "UPSTREAM_FAIL_ACQUISITION", "detail": err})
                raise StopIteration
            print("   anchor fetched: %d words" % len(anchor["text"].split()))
            try:
                pack = RS.research(
                    provider,
                    anchor={"url": cand["url"], "text": anchor["text"],
                            "title": cand["title"] or "", "canonical_url": cand["url"],
                            "accessed_at": now},
                    now_iso=now, api_key=os.environ.get("OPENROUTER_API_KEY", ""))
            except Exception as e:                                # noqa: BLE001
                rec.update({"outcome": "UPSTREAM_FAIL_RESEARCH",
                            "detail": "%s: %s" % (type(e).__name__, str(e)[:200])})
                raise StopIteration
            pack.pop("_provider", None)
            (out_dir / "RESEARCH_PACK.json").write_text(
                json.dumps(pack, indent=1, ensure_ascii=False), encoding="utf-8")
            verdict = (pack.get("sufficiency") or {}).get("verdict")
            rec["research_verdict"] = verdict
            print("   research verdict: %s" % verdict)
            if verdict == RS.HOLD:
                rec.update({"outcome": "RESEARCH_HOLD",
                            "detail": "; ".join(
                                (pack["sufficiency"].get("reasons") or [])[:2])[:300]})
                raise StopIteration
            src = next(s for s in pack["sources"] if s.get("role") == "ANCHOR")
            result = CP.run_story_architecture_composition(
                provider, pack=pack, source_text=src["text"],
                source_sha=src["sha256"], subject=pack["subject"],
                fact_check=True, fact_check_fn=FCB.fact_check,
                out_dir=out_dir, frozen=None, stop_after="",
                compose_mode=CP.scheduled_compose_mode())
            rec["composition_status"] = result.get("status")
            rec["failure_stage"] = result.get("failure_stage")
            arch_p = out_dir / "ARCHITECTURE.json"
            if not arch_p.exists():
                rec.update({"outcome": "NO_ARCHITECTURE",
                            "detail": "composition %s at %s"
                                      % (result.get("status"),
                                         result.get("failure_stage"))})
                raise StopIteration
            arch = json.loads(arch_p.read_text(encoding="utf-8"))
            defs = arch.get("definitions") or {}
            devi = arch.get("definition_evidence") or {}
            if not defs:
                rec.update({"outcome": "NO_DEFINITIONS", "detail": "architecture "
                            "authored no definitions"})
                raise StopIteration
            fresh = []
            for term in sorted(defs):
                collision = term.strip().lower() in bad_terms
                d = {"term": term, "has_definition_evidence": bool(devi.get(term)),
                     "term_collides_with_consumed_plan": collision,
                     # clustering metadata -- these are NOT independent trials
                     "run_id": run_id, "plan_dir": str(out_dir), "seed_id": cand["seed_id"],
                     "rank": cand["rank"], "source_name": cand["source_name"],
                     "source_url": cand["url"]}
                rec["definitions"].append(d)
                if not collision:
                    fresh.append(d)
            st["definitions"].extend(fresh)
            rec.update({"outcome": "ARCHITECTURE",
                        "detail": "%d definitions (%d fresh), %d with definition_evidence"
                                  % (len(defs), len(fresh),
                                     sum(1 for t in defs if devi.get(t)))})
            print("   %s" % rec["detail"])
        except StopIteration:
            pass
        except Exception as e:                                    # noqa: BLE001
            rec.update({"outcome": "RUNNER_ERROR",
                        "detail": "%s: %s" % (type(e).__name__, str(e)[:300])})
            (out_dir / "TRACEBACK.txt").write_text(traceback.format_exc(),
                                                   encoding="utf-8")
        rec["seconds"] = round(time.time() - t0, 1)
        rec["model_calls"] = provider.calls - calls0
        st["attempts"].append(rec)
        save(bd, st)
        print("   -> %s  (%.0fs, %d calls)  running total: %d definitions / %d attempts"
              % (rec["outcome"], rec["seconds"], rec["model_calls"],
                 len(st["definitions"]), len(st["attempts"])))

    if not st["closed"]:
        n_def, n_att = len(st["definitions"]), len(st["attempts"])
        if n_def >= TARGET_DEFINITIONS:
            st["closed"], st["close_reason"] = True, (
                "reached %d fresh definitions (target %d)" % (n_def, TARGET_DEFINITIONS))
        elif n_att >= MAX_ATTEMPTS:
            st["closed"], st["close_reason"] = True, (
                "reached the %d-attempt cap with %d definitions -- CLOSED SHORT, no top-up"
                % (MAX_ATTEMPTS, n_def))
        else:
            st["closed"], st["close_reason"] = True, (
                "the frozen pool of %d candidates was exhausted at %d definitions "
                "-- CLOSED SHORT, no top-up" % (pool_doc["pool_size"], n_att))
    st["closed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(bd, st)
    print("\nBATCH CLOSED: %s" % st["close_reason"])
    print("  attempts    : %d" % len(st["attempts"]))
    print("  definitions : %d" % len(st["definitions"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
