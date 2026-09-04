"""
story_architecture_canary.py -- run a subject through the automated composition path.

WHY THIS IS A COMMITTED SCRIPT and not an ad-hoc session. The held-out Ground Truth
article was produced by a person driving the stages by hand, which is precisely why it
could not be repeated. A canary that proves autonomy has to be a thing anyone can run
again, so the harness is code and its output is written to disk.

WHAT IT DOES NOT DO. It builds no ledger, performs no Worth judgement, writes no
architecture, derives no CUT terms, composes no Writer prompt and makes no Continuity
edit. If any of that appears here, the canary is testing the author rather than the
engine. All it does is assemble the frozen source material into a RESEARCH_PACK and hand
it to `composition.run_story_architecture_composition`.

TWO MODES
  --ground-truth   The held-out subject, from the source URLs its frozen manifest
                   records. Same subject, same sources. NOT byte-identical prose: the
                   question is whether the autonomous stages reach a valid result
                   without a human touching an intermediate.
  --url URL        A fresh subject, fetched as the anchor and researched normally.

Needs CLIPROXY_KEY and a reachable CLIProxy for composition, and OPENROUTER_API_KEY for
the authoritative Fact Check. It reports what is missing rather than stubbing anything.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "orchestrator"))

from new_engine_v1 import composition as CP            # noqa: E402
from new_engine_v1 import contracts as C               # noqa: E402
from new_engine_v1 import research as RS               # noqa: E402
from new_engine_v1.provider import Provider            # noqa: E402
import composition_factual_bridge as FCB               # noqa: E402
import claude_cli_provider as CCP                      # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# The held-out article's own sources, as its frozen manifest records them. Roles and ids
# are copied from the manifest so the canary's pack is the same corpus, not a new one.
# S2 is a scanned PDF deck and S3/S4 answer 403 to every request shape tried; they are
# attempted and recorded as unfetched rather than quietly omitted.
GROUND_TRUTH_SUBJECT = ("Justin Blinder, Ground Truth: a device that converts census "
                        "rent-burden data into physical brake resistance on a Citi Bike")
GROUND_TRUTH_SOURCES = [
    ("S0", "ANCHOR", "https://groundtruth.justin.work/"),
    ("S1", "INDEPENDENT",
     "https://gothamist.com/news/nyc-artist-creates-device-that-slows-citi-bikes-"
     "passing-through-rent-burdened-areas"),
    ("S3", "TERTIARY",
     "https://www.huduser.gov/portal/pdredge/pdr_edge_featd_article_092214.html"),
    ("S6", "PRIMARY",
     "https://www.govinfo.gov/content/pkg/USCODE-2023-title42/html/"
     "USCODE-2023-title42-chap8-subchapI-sec1437a.htm"),
    ("S7", "PRIMARY",
     "https://www.federalregister.gov/documents/2024/01/17/2024-00849/"
     "annual-adjustment-factors-and-annual-adjustment-factor-percentage-"
     "increases-for-fiscal-year-2024"),
]


def fetch(url: str, timeout: int = 30) -> tuple:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
    except Exception as e:                                        # noqa: BLE001
        return "", "%s: %s" % (type(e).__name__, str(e)[:120])
    text = RS.strip_html(raw) if "<" in raw[:2000] else raw
    return text, "" if text.strip() else "empty after markup strip"


def build_pack(subject: str, sources: list, now: str) -> tuple:
    """A RESEARCH_PACK from already-known source URLs. Model-free."""
    out, failed = [], []
    for sid, role, url in sources:
        text, err = fetch(url)
        if err or len(text.split()) < 80:
            failed.append({"source_id": sid, "url": url,
                           "reason": err or "%d words" % len(text.split())})
            continue
        out.append({"source_id": sid, "role": role, "url": url,
                    "accessed_at": now, "sha256": C.sha256_text(text),
                    "fetch_status": "ok", "content_length": len(text),
                    # NOT RS.PER_SOURCE_CHARS. That is the research stage's per-source
                    # budget, and applying it here cut the last third off a 15,744-char
                    # anchor -- taking all four of the facts that carried the held-out
                    # article's lens with it, and turning a strong subject into
                    # NO_PLAUSIBLE_LENS. The freeze's own budget is the only one that
                    # belongs here.
                    "text": text[:CP.FREEZE_SOURCE_CHARS]})
    if not any(s["role"] == "ANCHOR" for s in out):
        raise SystemExit("the anchor source could not be fetched; nothing to run on: %s"
                         % failed)
    anchor = next(s for s in out if s["role"] == "ANCHOR")
    for s in out:
        s["sha256"] = C.sha256_text(s["text"])
        s["content_length"] = len(s["text"])
    pack = {"subject": subject,
            "sources": out,
            "coverage": {"fetched": len(out), "failed": failed},
            "sufficiency": {"verdict": RS.ARTICLE,
                            "reasons": ["canary: sources supplied from the frozen "
                                        "manifest, not searched"],
                            "what_is_missing": []},
            "pack_sha256": C.sha256_text(json.dumps(
                [s["sha256"] for s in out], sort_keys=True))}
    C.validate(C.Artifact(stage=C.RESEARCH_PACK, created_at=now, payload=pack))
    return pack, anchor, failed


def report(result: dict, out_dir: pathlib.Path) -> None:
    L = ["STORY ARCHITECTURE AUTOMATED CANARY", "",
         "subject : %s" % result["subject"],
         "status  : %s" % result["status"],
         "runtime : %ss" % result["runtime_seconds"],
         "words   : %s" % result["words"]]
    if result.get("replay"):
        L.append("REPLAY  : %s came from frozen artifacts -- not an autonomy proof"
                 % ", ".join(result["replayed_stages"]))
    L += ["", "STAGES"]
    rt = result.get("runtime_by_stage") or {}
    for s in CP.STAGES:
        L.append("  %-13s %-8s  calls=%-2s %7s%s"
                 % (s, result["stages"][s],
                    result["model_calls_by_stage"].get(s, 0),
                    ("%.1fs" % rt[s]) if s in rt else "-",
                    "  repairs=%s" % result["repairs_by_stage"][s]
                    if result["repairs_by_stage"].get(s) else ""))
    if rt:
        slow = sorted(rt.items(), key=lambda kv: -kv[1])[:3]
        L.append("  slowest: " + ", ".join("%s %.1fs" % (k, v) for k, v in slow))
    L += ["", "model calls total : %s" % result["model_calls_total"]]
    if result["failure_stage"]:
        L += ["", "FAILURE STAGE : %s" % result["failure_stage"],
              "REASON CODE   : %s" % result["reason_code"],
              "REASON        : %s" % result["failure_reason"]]
    det = result.get("detail") or {}
    if (det.get(CP.READER) or {}).get("one_line"):
        L += ["", "reader: %s" % det[CP.READER]["one_line"]]
    text = "\n".join(L)
    print("\n" + text)
    (out_dir / "CANARY_REPORT.txt").write_text(text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ground-truth", action="store_true")
    ap.add_argument("--url", default="")
    ap.add_argument("--subject", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--no-fact-check", action="store_true")
    # Claude-family composition runs on the owner's subscription. `http` is the old
    # OpenRouter path and is kept only so the two can be compared deliberately; it is
    # not a fallback and nothing selects it automatically.
    ap.add_argument("--transport", choices=("subscription", "http"),
                    default="subscription")
    # A fresh subject needs a real pack, not just its anchor: the ledger's whole job is
    # to select across sources. --research runs the production research stage
    # (new_engine_v1.research.research) unmodified, so the live canary composes from the
    # same shape of pack a scheduled run would hand it. Its Sonar search is OpenRouter,
    # which is correct policy: Sonar is not a Claude model.
    ap.add_argument("--research", action="store_true")
    # Replay a previous run's frozen LEDGER/WORTH/ARCHITECTURE so a change to a later
    # stage can be tested without paying for two stages that already validated. The
    # replayed stages report REPLAYED and the result is marked replay:True -- this is a
    # test cycle, never an autonomy proof.
    ap.add_argument("--replay-from", default="",
                    help="artifact directory of a previous run")
    # Resume at the grounder/factual-repair boundary on prose that already passed the
    # Writer, Continuity and the safety stack. Used to test the factual repair without
    # paying for research, ledger, architecture, Writer and Continuity again.
    ap.add_argument("--replay-article", action="store_true")
    a = ap.parse_args()

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tag = "ground-truth" if a.ground_truth else "fresh"
    out_dir = pathlib.Path(a.out or (
        HERE.parent / ".claude" / "story-architecture"
        / ("automated-canary-%s-%s" % (tag, now[:19].replace(":", "")))))
    out_dir.mkdir(parents=True, exist_ok=True)

    missing = FCB.credentials_missing() if not a.no_fact_check else []
    if missing:
        print("NOTE: fact check cannot run -- missing %s" % ", ".join(missing))

    if a.replay_from and (pathlib.Path(a.replay_from) / "RESEARCH_PACK.json").exists() \
            and not a.ground_truth:
        R = pathlib.Path(a.replay_from)
        pack = json.loads((R / "RESEARCH_PACK.json").read_text())
        anchor = next(s for s in pack["sources"] if s.get("role") == "ANCHOR")
        failed = (pack.get("coverage") or {}).get("failed") or []
        print("REPLAY: research pack reused from %s (%d sources) -- research NOT rerun"
              % (R.name, len(pack["sources"])))
    elif a.ground_truth:
        print("assembling the frozen Ground Truth corpus ...")
        pack, anchor, failed = build_pack(GROUND_TRUTH_SUBJECT, GROUND_TRUTH_SOURCES, now)
    elif a.research:
        if not a.url:
            raise SystemExit("--url is required with --research")
        print("fetching the anchor ...")
        seed, anchor, failed = build_pack(a.subject or a.url,
                                          [("S0", "ANCHOR", a.url)], now)
        print("running the PRODUCTION research stage (unmodified) ...")
        prov_for_research = (CCP.ClaudeCLIProvider(**({"model": a.model} if a.model else {}))
                             if a.transport == "subscription"
                             else Provider(**({"model": a.model} if a.model else {})))
        pack = RS.research(prov_for_research,
                           anchor={"url": a.url, "text": anchor["text"],
                                   "title": a.subject or "", "canonical_url": a.url,
                                   "accessed_at": now},
                           now_iso=now,
                           api_key=os.environ.get("OPENROUTER_API_KEY", ""))
        pack.pop("_provider", None)
        verdict = (pack.get("sufficiency") or {}).get("verdict")
        print("  research verdict: %s" % verdict)
        if verdict == RS.HOLD:
            print("  HOLD before composition -- not enough material to write from:")
            for r in (pack["sufficiency"].get("reasons") or [])[:4]:
                print("    - %s" % r)
            (out_dir / "RESEARCH_PACK.json").write_text(json.dumps(pack, indent=1))
            return 1
        anchor = next(s for s in pack["sources"] if s.get("role") == "ANCHOR")
        failed = (pack.get("coverage") or {}).get("failed") or []
    else:
        if not a.url:
            raise SystemExit("--url is required without --ground-truth")
        print("fetching the anchor ...")
        pack, anchor, failed = build_pack(
            a.subject or a.url, [("S0", "ANCHOR", a.url)], now)
    for s in pack["sources"]:
        print("  %-4s %-12s %6d words  %s" % (s["source_id"], s["role"],
                                              len(s["text"].split()), s["url"][:60]))
    for f in failed:
        print("  %-4s UNFETCHED    %s" % (f["source_id"], f["reason"]))
    for tr in CP.truncated_sources(pack):
        print("  %-4s TRUNCATED    %d chars, %d shown to the freeze, %d unseen"
              % (tr["source_id"], tr["chars"], tr["shown"], tr["lost"]))
    (out_dir / "RESEARCH_PACK.json").write_text(json.dumps(pack, indent=1))

    frozen = None
    if a.replay_from:
        R = pathlib.Path(a.replay_from)
        frozen = {
            "ledger": json.loads((R / "FINAL_EVIDENCE_MANIFEST.json").read_text())["facts"],
            "architecture": json.loads((R / "ARCHITECTURE.json").read_text()),
        }
        wj = R / "WORTH_AND_CANDIDATE.json"
        if wj.exists():
            frozen["worth"] = json.loads(wj.read_text())
        if a.replay_article:
            art = R / "CONTINUITY_FINAL.md"
            if not art.exists():
                art = R / "WRITER_DRAFT.md"
            frozen["article"] = art.read_text()
            print("        AND the finished article (%s, %d words) -- resuming at the "
                  "grounder/repair boundary"
                  % (art.name, len(frozen["article"].split())))
        print("\nREPLAY: ledger (%d facts), worth and architecture come from %s"
              % (len(frozen["ledger"]), R.name))
        print("        this is a Writer-onward test cycle, NOT an autonomy proof")

    if a.transport == "subscription":
        provider = CCP.ClaudeCLIProvider(**({"model": a.model} if a.model else {}))
        st = provider.auth
        print("\ntransport: Claude Code CLI on the %s subscription (%s, %s)"
              % (st.get("subscriptionType"), st.get("orgName"), st.get("apiProvider")))
        print("           model %s | OpenRouter: not used for composition"
              % provider.model)
    else:
        provider = Provider(**({"model": a.model} if a.model else {}))
        print("\ntransport: HTTP provider (CLIProxy then OpenRouter) -- PAID PATH")
    print("\nrunning the automated composition path (no manual stage construction) ...")
    result = CP.run_story_architecture_composition(
        provider, pack=pack, source_text=anchor["text"],
        source_sha=anchor["sha256"], subject=pack["subject"],
        fact_check=not a.no_fact_check,
        fact_check_fn=FCB.fact_check, out_dir=out_dir, frozen=frozen)
    report(result, out_dir)
    if isinstance(provider, CCP.ClaudeCLIProvider):
        print("\nsubscription calls: %d | cost equivalent (not billed): $%.4f"
              % (provider.calls, provider.cost_usd))
    print("\nartifacts: %s" % out_dir)
    return 0 if result["status"] == CP.PASS else 1


if __name__ == "__main__":
    sys.exit(main())
