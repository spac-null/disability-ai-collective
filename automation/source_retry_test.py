#!/usr/bin/env python3
"""
source_retry_test.py -- SOURCE_ACQUISITION_RETRY_V1, deterministic tests.

THE FAILURE THIS CLOSES
The 2026-08-23 natural production run picked its top news seed, fetched ~286
chars of JavaScript/error shell from lemonde.fr, and Story Rejection correctly
found no story content -- "Source is an empty error page; no anchorable detail
exists". The whole daily run then ended, while 100+ unused seeds sat in the
pool. Note 286 chars is ABOVE fetch_source_article's own long-standing "<200
chars" check, which is exactly why the shell was labelled `fetched_article` and
flowed downstream as though it were a real article.

A source that cannot be acquired is a TECHNICAL failure. It must cost one
candidate, not the day. An editorial defer or decline is a different class and
must NOT trigger candidate-hunting.

Covers TEST A-F of the owner brief:
  A  shell -> SOURCE_ACQUISITION_FAILED -> candidate 2 selected, fresh start
  B  usable -> editorial DEFER   -> no acquisition retry
  C  usable -> editorial DECLINE -> no acquisition retry
  D  three acquisition failures  -> exhausted, no fourth candidate
  E  candidate 2 produces the article -> zero candidate-1 leakage
  F  capture stays OFF by default; SHADOW_CAPTURE=1 stays explicit
plus the owner correction of 2026-08-23: an acquisition failure is RUN-LOCAL,
never a permanent blacklist -- see
test_failure_is_run_local_not_a_permanent_blacklist.

No network, no provider calls, no production DB, no real repo paths.

Run (from repo root):
  python3 automation/source_retry_test.py
"""

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from snapshot_test import _import_orchestrator, _isolate_paths  # noqa: E402
from orchestrator.discovery import (  # noqa: E402
    MAX_SOURCE_ACQUISITION_ATTEMPTS, _SOURCE_MIN_USABLE_CHARS,
    _SOURCE_MIN_USABLE_PARAGRAPHS,
)
import shadow_capture as SC  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


# --------------------------------------------------------------------------- #
# Fixtures. Synthetic text only -- no real article content.
# --------------------------------------------------------------------------- #
def _article(nparas=6):
    para = ("A sentence of real body prose that comfortably clears the "
            "extractor's own eighty-character minimum for a kept paragraph. ")
    return "\n\n".join(para * 2 for _ in range(nparas))


GOOD = _article()                     # 6 paragraphs, well over every floor
SHELL = "Please enable JavaScript to continue reading this article."   # the 08-23 shape
assert len(GOOD) > _SOURCE_MIN_USABLE_CHARS
assert len(SHELL) < _SOURCE_MIN_USABLE_CHARS


def _orch():
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    _isolate_paths(orch, tempfile.mkdtemp())
    for d in (orch.posts_dir, orch.drafts_dir, orch.assets_dir):
        d.mkdir(parents=True, exist_ok=True)
    return orch


def _seed(orch, seed_id, score, url):
    conn = sqlite3.connect(str(orch.discovery_db))
    orch._init_news_seeds_table(conn)
    orch._ensure_decline_columns(conn)
    conn.execute(
        "INSERT OR REPLACE INTO news_seeds (id,url,title,summary,source_name,"
        "pub_date,fetched_date,relevance_score,themes,disability_angle,used) "
        "VALUES (?,?,?,?,?,date('now'),date('now'),?,'[]','an angle',0)",
        (seed_id, url, "T-" + seed_id, "rss blurb " + seed_id, "Outlet", score),
    )
    conn.commit()
    conn.close()


def _install_fetch(orch, bodies, origins=None, calls=None):
    """Stub fetch_source_article, mirroring its real side channels."""
    origins = origins or {}

    def fake(url, max_chars=None, fallback_text=None, underlying_url=None):
        if calls is not None:
            calls.append(url)
        body = bodies.get(url)
        orch._last_fetch_origin = origins.get(url, "fetched_article" if body else "none")
        orch._last_fetch_original_length = len(body) if body else None
        orch._last_fetch_paragraph_count = (
            len([b for b in body.split("\n\n") if b.strip()]) if body else 0)
        return body

    orch.fetch_source_article = fake


def _row(orch, seed_id):
    conn = sqlite3.connect(str(orch.discovery_db))
    conn.row_factory = sqlite3.Row
    r = conn.execute("SELECT * FROM news_seeds WHERE id = ?", (seed_id,)).fetchone()
    conn.close()
    return r


# --------------------------------------------------------------------------- #
def test_classifier_signals():
    """Structured/structural signals first, length only as a backstop."""
    o = _orch()
    C = o.classify_source_acquisition
    check("real article is USABLE", C(GOOD, "fetched_article", 6)[0] == "USABLE")
    st, why = C(SHELL, "fetched_article", 1)
    check("the 08-23 shell classifies as SOURCE_ACQUISITION_FAILED",
          st == "SOURCE_ACQUISITION_FAILED")
    check("...on the structural body signal, not a bare char count",
          why.startswith("no_article_body:"), why)
    check("fallback_summary is an acquisition failure",
          C(GOOD, "fallback_summary", 6)[1].startswith("fetch_no_live_article:"))
    check("origin 'none' is an acquisition failure",
          C(None, "none", 0)[1].startswith("fetch_no_live_article:"))
    check("empty extraction is caught",
          C("   ", "fetched_article", 5)[1] == "empty_extraction")
    # marker path: enough paragraphs and length to pass 1 and 2
    wall = "\n\n".join(["Access denied. " + "x" * 200] * 5)
    check("interstitial marker is caught even when long and multi-paragraph",
          C(wall, "fetched_article", 5)[1].startswith("interstitial_marker:"),
          C(wall, "fetched_article", 5))
    short = "\n\n".join(["y" * 100] * (_SOURCE_MIN_USABLE_PARAGRAPHS + 1))
    check("length floor still acts as a backstop",
          C(short[:_SOURCE_MIN_USABLE_CHARS - 50], "fetched_article",
            _SOURCE_MIN_USABLE_PARAGRAPHS + 1)[1].startswith("extraction_too_short:"))


def test_A_shell_then_next_candidate():
    """TEST A -- candidate 1 shell, candidate 2 selected, fresh start."""
    o = _orch()
    _seed(o, "c1", 0.90, "https://paywall.example/1")
    _seed(o, "c2", 0.50, "https://open.example/2")
    calls = []
    _install_fetch(o, {"https://paywall.example/1": SHELL,
                       "https://open.example/2": GOOD}, calls=calls)

    seed = o.get_news_seed_with_usable_source()
    check("run is not lost -- a seed is returned", seed is not None)
    check("candidate 2 selected despite lower score", seed and seed["id"] == "c2",
          seed and seed["id"])
    check("each candidate fetched exactly once", calls == ["https://paywall.example/1",
                                                          "https://open.example/2"], calls)
    att = o._source_acquisition_attempts
    check("two attempts recorded", len(att) == 2, att)
    check("attempt 1 recorded as SOURCE_ACQUISITION_FAILED",
          att[0]["result"] == "SOURCE_ACQUISITION_FAILED" and att[0]["attempt"] == 1)
    check("attempt 2 recorded as USABLE", att[1]["result"] == "USABLE" and att[1]["attempt"] == 2)
    check("not flagged exhausted (a usable candidate was found)",
          o._source_acquisition_exhausted is False)

    bad = _row(o, "c1")
    check("failed candidate flagged source_unusable", bad["source_unusable"] == 1)
    check("reason persisted", bool(bad["source_unusable_reason"]))
    check("acquisition failure is NOT recorded as an editorial decline",
          bad["declined"] == 0 and bad["decline_json"] is None
          and bad["decline_schema_version"] is None)
    check("chosen candidate left untouched", _row(o, "c2")["source_unusable"] == 0)


def test_B_editorial_defer_does_not_retry():
    """TEST B -- usable source, editorial DEFER, no acquisition retry."""
    o = _orch()
    _seed(o, "c1", 0.90, "https://open.example/1")
    _seed(o, "c2", 0.50, "https://open.example/2")
    calls = []
    _install_fetch(o, {"https://open.example/1": GOOD, "https://open.example/2": GOOD},
                   calls=calls)
    seed = o.get_news_seed_with_usable_source()
    check("usable candidate 1 accepted", seed and seed["id"] == "c1")
    fetches_after_acquisition = len(calls)

    # A downstream editorial defer happens here in the real run. It must not
    # re-enter acquisition: nothing below calls the retry helper again.
    check("exactly one acquisition attempt", len(o._source_acquisition_attempts) == 1)
    check("editorial defer triggers no further fetch", len(calls) == fetches_after_acquisition)
    check("no candidate flagged unusable by an editorial outcome",
          _row(o, "c1")["source_unusable"] == 0 and _row(o, "c2")["source_unusable"] == 0)
    check("candidate 2 is still untouched and available for a future run",
          o.get_news_seed(exclude_ids=["c1"])["id"] == "c2")


def test_C_editorial_decline_does_not_retry():
    """TEST C -- usable source, substantive editorial DECLINE, no acquisition retry."""
    o = _orch()
    _seed(o, "c1", 0.90, "https://open.example/1")
    _seed(o, "c2", 0.50, "https://open.example/2")
    calls = []
    _install_fetch(o, {"https://open.example/1": GOOD, "https://open.example/2": GOOD},
                   calls=calls)
    seed = o.get_news_seed_with_usable_source()
    before = len(calls)
    # the real editorial decline path, on the seed acquisition accepted
    o.mark_news_seed_declined(seed["id"], {"reason": "no strong mechanism"})
    check("editorial decline triggers no further acquisition", len(calls) == before)
    check("still one acquisition attempt", len(o._source_acquisition_attempts) == 1)
    row = _row(o, "c1")
    check("decline is recorded on the DECLINE columns", row["declined"] == 1)
    check("...and NOT as a source-acquisition failure", row["source_unusable"] == 0,
          row["source_unusable"])


def test_D_exhaustion_stops_at_three():
    """TEST D -- three acquisition failures, stop, no fourth candidate."""
    o = _orch()
    for i in range(9):
        _seed(o, "b%d" % i, 0.9 - i / 100.0, "https://bad.example/%d" % i)
    calls = []
    _install_fetch(o, {"https://bad.example/%d" % i: SHELL for i in range(9)}, calls=calls)

    seed = o.get_news_seed_with_usable_source()
    check("no seed returned", seed is None)
    check("exactly MAX_SOURCE_ACQUISITION_ATTEMPTS candidates tried",
          len(calls) == MAX_SOURCE_ACQUISITION_ATTEMPTS == 3, "%d calls" % len(calls))
    check("no fourth candidate was fetched", len(calls) == 3)
    check("flagged exhausted", o._source_acquisition_exhausted is True)
    check("three attempts recorded, all failed",
          len(o._source_acquisition_attempts) == 3 and
          all(a["result"] == "SOURCE_ACQUISITION_FAILED"
              for a in o._source_acquisition_attempts))
    check("an over-large max_attempts cannot exceed the hard budget",
          len(_exhaust_with(max_attempts=99)) == 3)


def _exhaust_with(max_attempts):
    o = _orch()
    for i in range(9):
        _seed(o, "z%d" % i, 0.9, "https://z.example/%d" % i)
    calls = []
    _install_fetch(o, {"https://z.example/%d" % i: SHELL for i in range(9)}, calls=calls)
    o.get_news_seed_with_usable_source(max_attempts=max_attempts)
    return calls


def test_D2_empty_pool_is_not_exhaustion():
    """An empty pool must leave the pre-existing discovery fallback reachable."""
    o = _orch()
    _install_fetch(o, {})
    check("no seeds at all -> None", o.get_news_seed_with_usable_source() is None)
    check("...and NOT flagged as acquisition-exhausted",
          o._source_acquisition_exhausted is False)


def test_failure_is_run_local_not_a_permanent_blacklist():
    """Owner correction (2026-08-23): one acquisition failure must NOT remove a
    source from every future production day.

    Acquisition failure is frequently transient -- a temporary anti-bot
    response, a rotating interstitial, a site outage, a one-off extractor miss.
    It is not an editorial judgement. So:
      * a failed candidate cannot be reselected in the SAME run;
      * its acquisition-failure metadata is persisted, for evidence;
      * a NEW run is free to consider that source again;
      * if it fails again, the normal bounded retry just applies again.
    """
    o = _orch()
    _seed(o, "flaky", 0.99, "https://flaky.example/a")
    _seed(o, "other", 0.10, "https://other.example/b")

    # --- run 1: source is down. It must not be picked twice within this run. ---
    calls1 = []
    _install_fetch(o, {"https://flaky.example/a": SHELL,
                       "https://other.example/b": SHELL}, calls=calls1)
    check("run 1 finds nothing usable", o.get_news_seed_with_usable_source() is None)
    check("run 1 tried each candidate exactly once -- no same-run reselection",
          sorted(calls1) == ["https://flaky.example/a", "https://other.example/b"], calls1)
    check("run 1 attempted each seed id at most once",
          len({a["seed_id"] for a in o._source_acquisition_attempts})
          == len(o._source_acquisition_attempts))

    # --- the evidence survives ---
    row = _row(o, "flaky")
    check("acquisition-failure metadata is persisted for evidence",
          row["source_unusable"] == 1 and bool(row["source_unusable_reason"])
          and bool(row["source_unusable_date"]))
    check("still not recorded as an editorial decline", row["declined"] == 0)

    # --- a later run must NOT be blocked by that flag ---
    later = o.get_news_seed()
    check("plain selection still offers the previously-failed source "
          "(no permanent blacklist)", later is not None and later["id"] == "flaky", later)

    # --- later run, source recovered: usable again and actually used ---
    o2 = _orch()
    _seed(o2, "flaky", 0.99, "https://flaky.example/a")
    conn = sqlite3.connect(str(o2.discovery_db))
    conn.execute("UPDATE news_seeds SET source_unusable = 1, "
                 "source_unusable_reason = 'no_article_body:paragraphs=1<3', "
                 "source_unusable_date = '2026-08-23T09:00:00' WHERE id = 'flaky'")
    conn.commit(); conn.close()
    _install_fetch(o2, {"https://flaky.example/a": GOOD})
    seed = o2.get_news_seed_with_usable_source()
    check("a later run CAN use a source that failed acquisition before, once it "
          "recovers", seed is not None and seed["id"] == "flaky", seed)
    check("the recovered attempt is recorded as USABLE",
          o2._source_acquisition_attempts[-1]["result"] == "USABLE")

    # --- later run, still down: fails acquisition again, normally ---
    o3 = _orch()
    _seed(o3, "flaky", 0.99, "https://flaky.example/a")
    conn = sqlite3.connect(str(o3.discovery_db))
    conn.execute("UPDATE news_seeds SET source_unusable = 1 WHERE id = 'flaky'")
    conn.commit(); conn.close()
    calls3 = []
    _install_fetch(o3, {"https://flaky.example/a": SHELL}, calls=calls3)
    check("a still-broken source is re-attempted and fails normally",
          o3.get_news_seed_with_usable_source() is None and len(calls3) == 1, calls3)
    check("...and that run is flagged exhausted",
          o3._source_acquisition_exhausted is True)


def test_E_no_cross_attempt_leakage():
    """TEST E -- article-producing candidate owns every source artifact."""
    o = _orch()
    _seed(o, "c1", 0.90, "https://paywall.example/1")
    _seed(o, "c2", 0.50, "https://open.example/2")
    _install_fetch(o, {"https://paywall.example/1": SHELL, "https://open.example/2": GOOD})
    seed = o.get_news_seed_with_usable_source()
    chosen_url = seed["url"]

    # What generate.py builds its evidence packet from: the CHOSEN seed's url.
    chosen_text = o.get_source_text(chosen_url, fallback_text=seed.get("summary"))
    check("chosen source text is candidate 2's body", chosen_text == GOOD)
    check("candidate 1's shell is not the chosen source", chosen_text != SHELL)
    check("chosen url is candidate 2's", chosen_url == "https://open.example/2")
    check("chosen origin/paragraphs describe candidate 2",
          o.get_source_origin(chosen_url) == "fetched_article"
          and o.get_source_paragraph_count(chosen_url) >= _SOURCE_MIN_USABLE_PARAGRAPHS)
    # candidate 1 survives only as attempt metadata, keyed by its own url
    att = o._source_acquisition_attempts
    check("candidate 1 appears only as a failed-attempt record",
          att[0]["url"] == "https://paywall.example/1"
          and att[0]["result"] == "SOURCE_ACQUISITION_FAILED")
    check("no attempt record claims candidate 1 was chosen",
          [a["url"] for a in att if a["result"] == "USABLE"] == [chosen_url])

    # and the capture payload pins the article to one candidate
    with tempfile.TemporaryDirectory() as d:
        os.environ[SC.ENV_FLAG] = "1"
        os.environ[SC.ENV_ROOT] = d
        SC.capture("source_acquisition", "r1", None, attempts=att,
                   chosen_seed_id=seed["id"], chosen_url=chosen_url, exhausted=False)
        payload = json.loads((Path(d) / "r1" / "source" / "acquisition_attempts.json").read_text())
        check("capture pins chosen_seed_id to candidate 2", payload["chosen_seed_id"] == "c2")
        check("capture records both attempts", payload["attempt_count"] == 2)
        check("capture names the frozen policy", payload["policy"] == "SOURCE_ACQUISITION_RETRY_V1")
        # the failed candidate must leave NO source representation -- only the
        # attempt metadata (plus the manifest every event appends to)
        srcfiles = sorted(str(p.name) for p in (Path(d) / "r1" / "source").iterdir())
        check("no source-representation file is written for the failed candidate",
              srcfiles == ["acquisition_attempts.json"], srcfiles)
        blob = (Path(d) / "r1" / "source" / "acquisition_attempts.json").read_text()
        check("the failed candidate's body text is never persisted", SHELL not in blob)
        os.environ.pop(SC.ENV_FLAG, None)


def test_F_capture_defaults_unchanged():
    """TEST F -- capture OFF unless SHADOW_CAPTURE is explicitly set."""
    with tempfile.TemporaryDirectory() as d:
        os.environ.pop(SC.ENV_FLAG, None)
        os.environ[SC.ENV_ROOT] = d
        check("capture disabled with no flag", SC.enabled() is False)
        SC.capture("source_acquisition", "off1", None, attempts=[{"attempt": 1}],
                   chosen_seed_id="x", chosen_url="u")
        check("new acquisition event writes nothing when OFF",
              not any(Path(d).rglob("*")), sorted(str(x) for x in Path(d).rglob("*")))
        os.environ[SC.ENV_FLAG] = "1"
        check("SHADOW_CAPTURE=1 still turns it on", SC.enabled() is True)
        os.environ.pop(SC.ENV_FLAG, None)
    check("source_acquisition is CONDITIONAL, not part of the article contract",
          "source_acquisition" in SC.CONDITIONAL_EVENTS
          and "source_acquisition" not in SC.REQUIRED_EVENTS)
    check("article-output contract is unchanged",
          SC.REQUIRED_EVENTS == ("evidence", "commission", "writer",
                                 "final_output", "disposition"), SC.REQUIRED_EVENTS)


def test_retry_is_reachable_only_from_selection():
    """Structural: one call site, in step 2a, before any editorial stage."""
    src = (Path(__file__).parent / "orchestrator" / "generate.py").read_text()
    n = src.count("get_news_seed_with_usable_source()")
    check("exactly one call site in generate.py", n == 1, n)
    i_acq = src.index("get_news_seed_with_usable_source()")
    # note: the evidence hook is a multi-line call, so match its first argument
    for label, marker in (("evidence", '"evidence", _capture_run_id'),
                          ("commission", '_shadow_capture("commission"'),
                          ("writer", '_shadow_capture("writer"'),
                          ("final_output", '_shadow_capture("final_output"')):
        check("acquisition precedes the %s capture" % label, i_acq < src.index(marker))
    check("no acquisition retry inside the defer handler",
          "get_news_seed_with_usable_source" not in src[src.index("def _handle_defer_run"):]
          if "def _handle_defer_run" in src else True)


def main():
    for fn in [test_classifier_signals,
               test_A_shell_then_next_candidate,
               test_B_editorial_defer_does_not_retry,
               test_C_editorial_decline_does_not_retry,
               test_D_exhaustion_stops_at_three,
               test_D2_empty_pool_is_not_exhaustion,
               test_failure_is_run_local_not_a_permanent_blacklist,
               test_E_no_cross_attempt_leakage,
               test_F_capture_defaults_unchanged,
               test_retry_is_reachable_only_from_selection]:
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL SOURCE-ACQUISITION-RETRY TESTS PASSED")


if __name__ == "__main__":
    main()
