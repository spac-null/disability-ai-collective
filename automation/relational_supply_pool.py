"""Produce and freeze the candidate pool for the relational-supply acquisition batch.

READ ONLY against the production discovery database -- opened with mode=ro, so this cannot
mark a seed used, write an assessment, or run the schema DDL that the selector's own shadow
path performs. Nothing here consumes a candidate; consumption is the batch runner's job, and
it takes candidates strictly in the order frozen here.

NO MODEL CALLS. The ranking is production's own and is entirely deterministic: selector_v2's
`eligible_pool` (production's eligibility rules -- unused, not terminally failed, past its
per-material-class recency cutoff) followed by `select_candidates` (production's three
exposure streams: theme signal, urgency, deterministic exploration, then theme fill).

ONE DEVIATION FROM A PRODUCTION DAY, AND ONLY ONE. `select_candidates` exposes
DAILY_CANDIDATES = 12 per day, because a day commissions one article. A batch of eighteen
runs is not a day. So the same function is called repeatedly with `already_assessed`
accumulating -- which is exactly the mechanism the commissioning desk itself uses to stop
re-ranking a seed it has already spent -- until the requested depth is reached. Every layer
therefore has production's own stream mix; only the number of layers differs. The ranking
function is untouched, and the layer each candidate came from is recorded so the structure
stays visible.

Usage: relational_supply_pool.py <out_dir> [--depth N] [--now ISO]
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import sqlite3
import sys

WORKSPACE = pathlib.Path("/srv/data/hermes/workspace/disability-ai-collective")
sys.path.insert(0, str(WORKSPACE / "automation"))
sys.path.insert(0, str(WORKSPACE / "automation" / "orchestrator"))

import selector_v2 as SV                    # noqa: E402
import news_fetcher as NF                   # noqa: E402

EXCLUSIONS = pathlib.Path(__file__).resolve().parent.parent / ".claude" / "experiments" \
    / "relational-supply-acquisition-2026-09-24" / "EXCLUSIONS.json"


def _norm_url(u: str) -> str:
    u = (u or "").strip().rstrip("/.,);")
    for p in ("https://", "http://"):
        if u.startswith(p):
            u = u[len(p):]
    return u.lower()[4:] if u.lower().startswith("www.") else u.lower()


def build(out_dir: pathlib.Path, depth: int, now: datetime.datetime) -> dict:
    exc = json.loads(EXCLUSIONS.read_text(encoding="utf-8"))
    bad_urls = {_norm_url(u) for p in exc["plans"] for u in p["source_urls"]}
    bad_seeds = {s for p in exc["plans"] for s in p["seed_ids"]}

    uri = "file:%s?mode=ro" % (WORKSPACE / "disability_findings.db")
    conn = sqlite3.connect(uri, uri=True)
    try:
        pool = SV.eligible_pool(conn, now)
        eligible_n = len(pool)
        picked, assessed, layer = [], set(), 0
        while len(picked) < depth:
            layer += 1
            batch = SV.select_candidates(
                pool, now=now, score_item=NF.score_item,
                boosters=NF.DISABILITY_BOOSTERS, keyword_matches=NF._keyword_matches,
                already_assessed=frozenset(assessed))
            if not batch:
                break
            for c in batch:
                r = c["row"]
                picked.append({"layer": layer, "exposed_via": c["exposed_via"],
                               "theme_signal": c["theme_signal"],
                               "seed_id": r["id"], "url": r["url"], "title": r["title"],
                               "source_name": r["source_name"],
                               "pub_date": r["pub_date"],
                               "material_class": r["material_class"]})
                assessed.add(r["id"])
    finally:
        conn.close()

    kept, dropped = [], []
    for c in picked:
        why = ""
        if str(c["seed_id"]) in bad_seeds:
            why = "seed_id is an excluded plan's seed"
        elif _norm_url(c["url"]) in bad_urls:
            why = "url is a document an excluded plan already cites"
        (dropped if why else kept).append(dict(c, excluded_because=why) if why else c)
    for i, c in enumerate(kept, 1):
        c["rank"] = i

    doc = {"schema": "relational-supply-pool-v1",
           "frozen_at": now.isoformat(),
           "ranking": "selector_v2.eligible_pool + selector_v2.select_candidates, "
                      "production code unmodified, no model calls",
           "layers_note": "select_candidates exposes %d/day; layers accumulate "
                          "already_assessed to reach depth" % SV.DAILY_CANDIDATES,
           "exclusions_applied": {
               "source": "EXCLUSIONS.json",
               "sha256": hashlib.sha256(EXCLUSIONS.read_bytes()).hexdigest(),
               "keys": ["seed_id", "exact source url"],
               "note": "definition-term and question-id keys cannot apply before a plan "
                       "exists; they are enforced by the batch runner after ARCHITECTURE, "
                       "and the subject check is a human gate before admission"},
           "eligible_pool_size": eligible_n,
           "considered": len(picked), "excluded": len(dropped), "pool_size": len(kept),
           "excluded_candidates": dropped,
           "candidates": kept}
    out_dir.mkdir(parents=True, exist_ok=True)
    body = json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=False)
    (out_dir / "POOL.json").write_text(body, encoding="utf-8")
    (out_dir / "POOL.sha256").write_text(
        "%s  POOL.json\n" % hashlib.sha256(body.encode("utf-8")).hexdigest(),
        encoding="utf-8")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--depth", type=int, default=60)
    ap.add_argument("--now", default="")
    a = ap.parse_args()
    now = (datetime.datetime.fromisoformat(a.now) if a.now
           else datetime.datetime.now().replace(microsecond=0))
    doc = build(pathlib.Path(a.out_dir), a.depth, now)
    print("eligible pool      : %d" % doc["eligible_pool_size"])
    print("considered         : %d" % doc["considered"])
    print("excluded           : %d" % doc["excluded"])
    print("FROZEN POOL        : %d" % doc["pool_size"])
    print("sha256             : %s"
          % pathlib.Path(a.out_dir, "POOL.sha256").read_text().split()[0])
    for c in doc["candidates"][:12]:
        print("  %2d  L%d %-11s %-22s %s" % (c["rank"], c["layer"], c["exposed_via"],
                                             (c["source_name"] or "")[:22],
                                             (c["title"] or "")[:60]))
    for d in doc["excluded_candidates"]:
        print("  EXCLUDED  %s -- %s" % ((d["title"] or "")[:60], d["excluded_because"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
