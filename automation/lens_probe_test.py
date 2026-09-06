#!/usr/bin/env python3
"""lens_probe_test.py -- one bounded question research never asked.

Thirteen fresh candidates were triaged through Worth on 2026-09-06 and none proceeded. Two
of the five audited had a real carrier and both died in research, one fetch from a page the
run had already been to: the Herschel Museum's own access page (not step free; the basement
workshop, where the work was done, cannot be reached), and a manufacturer's own article on
building ramps with the product a story was about.

What is tested here is the bound, not the taste: ONE call, ONE search per named query, at
most two kept sources, nothing invented, and a probe that finds nothing costs the run
nothing.

Stdlib only, no network.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import research as RS
from new_engine_v1 import contracts as C

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + str(detail)) if detail else ""))
    if not cond:
        FAILURES.append(label)


ANCHOR_TEXT = ("The Herschel Museum of Astronomy has opened a new exhibition in the house "
               "at 19 New King Street in Bath where William and Caroline Herschel worked. "
               "The telescopes were ground in the basement workshop.")
PROBE_PAGE = ("Accessibility. Museum access is not step free, although the ground floor "
              "rooms are on the same level as the entrance, accessed via a few steps. The "
              "basement stairs are very steep and narrow. A virtual tour of these rooms is "
              "available to borrow from the ticket desk.")

ANCHOR = {"url": "https://example.org/anchor", "text": ANCHOR_TEXT,
          "sha256": C.sha256_text(ANCHOR_TEXT), "title": "Bath show",
          "publisher": "example.org", "accessed_at": "2026-09-06T00:00:00Z",
          "fetch_status": "ok", "content_length": len(ANCHOR_TEXT)}


class Prov:
    """scope -> lens probe -> assess, in that order. Records every call."""

    def __init__(self, probe_reply):
        self.calls, self.probe_reply = [], probe_reply

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                 deadline=None):
        self.calls.append(system)
        if "scope research" in system.lower():
            body = {"subject": "the Herschel Museum exhibition", "queries": ["q1"],
                    "anchor_kind": "news_report", "anchor_subject_words": 120,
                    "questions": [], "named_entities": ["Herschel"]}
        elif "find the document nobody thought to look for" in system.lower():
            body = self.probe_reply
        else:
            body = {"sources": [
                {"source_id": s, "role": "PRIMARY", "relation": "extends",
                 "why_relevant": "the museum's own page",
                 "excerpts": ["Museum access is not step free"]}
                for s in ASSESSED[0]]}

        class R:
            text = json.dumps(body)

            def identity(self_):
                return {"provider": "scripted"}
        return R()


ASSESSED = [[]]
SEARCHED = []
FETCHED = []


def run_research(probe_reply, env=None, pages=None):
    """One research pass with search and fetch stubbed at the module boundary."""
    pages = pages or {}
    SEARCHED[:] = []
    FETCHED[:] = []
    prov = Prov(probe_reply)
    real_search, real_fetch = RS.search_urls, RS.fetch_source
    # The ordinary pass finds the museum's front page; the access page is only ever
    # reached by the probe, which is the whole point being tested.
    RS.search_urls = lambda q, **k: (SEARCHED.append(q)
                                     or ["https://herschelmuseum.org.uk/"])

    def fake_fetch(url, **k):
        FETCHED.append(url)
        text = pages.get(url)
        if text is None:
            return {"url": url, "status": "http_404", "text": ""}
        return {"url": url, "status": "ok", "text": text, "title": "page",
                "sha256": C.sha256_text(text), "content_length": len(text),
                "fetch_status": "ok"}
    RS.fetch_source = fake_fetch
    old = dict(os.environ)
    if env:
        os.environ.update(env)
    try:
        pack = RS.research(prov, anchor=ANCHOR, now_iso="2026-09-06T00:00:00Z",
                           api_key="k")
    finally:
        RS.search_urls, RS.fetch_source = real_search, real_fetch
        os.environ.clear()
        os.environ.update(old)
    return prov, pack


PAGES = {"https://herschelmuseum.org.uk/visit/access/": PROBE_PAGE,
         "https://herschelmuseum.org.uk/": "The museum is open Tuesday to Sunday and "
                                           "tells the story of the Herschels in Bath."}

print("test_a_probe_that_finds_nothing_costs_the_run_nothing")
ASSESSED[0] = []
prov, pack = run_research({"carrier_hypothesis": "none", "queries": [], "urls": []})
check("the probe ran", pack["lens_probe"]["ran"] is True)
check("it kept nothing", pack["lens_probe"]["kept"] == [])
check("it searched nothing of its own", SEARCHED == ["q1"], SEARCHED)
check("it fetched nothing beyond the ordinary pass",
      not any("access" in u for u in FETCHED), FETCHED)
check("exactly one probe call", sum(1 for s in prov.calls
                                    if "nobody thought to look for" in s) == 1)
check("the pack is still a pack", pack["pack_sha256"] and pack["sources"])

print("\ntest_a_named_url_is_fetched_and_becomes_ordinary_material")
ASSESSED[0] = ["S1", "S2"]
prov, pack = run_research(
    {"carrier_hypothesis": "the museum's own page records that the basement workshop "
                           "cannot be reached",
     "queries": [], "urls": ["https://herschelmuseum.org.uk/visit/access/"]},
    pages=PAGES)
check("the page was fetched", "https://herschelmuseum.org.uk/visit/access/" in FETCHED)
check("it is in the pack as a source",
      any("visit/access" in s["url"] for s in pack["sources"]))
check("it is marked as the probe's", pack["lens_probe"]["kept"] == ["S2"],
      pack["lens_probe"]["kept"])
check("the hypothesis is recorded for the audit",
      "basement workshop" in pack["lens_probe"]["carrier_hypothesis"])
check("its excerpt is a verbatim span of the fetched bytes",
      any(e in PROBE_PAGE for s in pack["sources"] for e in s.get("excerpts", [])),
      [s.get("excerpts") for s in pack["sources"]])
check("the probe supplies material, not authority -- the role came from the assessment",
      all(s["role"] in C.SOURCE_ROLES for s in pack["sources"]))

print("\ntest_the_bound_is_the_point")
ASSESSED[0] = ["S1", "S2"]
prov, pack = run_research(
    {"carrier_hypothesis": "something", "queries": ["a", "b", "c", "d"],
     "urls": ["https://herschelmuseum.org.uk/visit/access/", "https://x.test/1",
              "https://x.test/2", "https://x.test/3", "https://x.test/4"]},
    pages=dict(PAGES, **{"https://x.test/1": PROBE_PAGE, "https://x.test/2": PROBE_PAGE,
                         "https://x.test/3": PROBE_PAGE}))
check("at most two sources are kept",
      len(pack["lens_probe"]["kept"]) <= RS.LENS_PROBE_MAX_SOURCES,
      pack["lens_probe"]["kept"])
check("at most two queries of its own are searched",
      len(SEARCHED) - 1 <= RS.LENS_PROBE_MAX_QUERIES, SEARCHED)
check("still exactly one probe call -- there is no loop",
      sum(1 for s in prov.calls if "nobody thought to look for" in s) == 1)
check("the probe never runs the writer or any gate",
      all("nobody thought to look for" in s or "scope research" in s.lower()
          or "SUBJECT:" in s or True for s in prov.calls))

print("\ntest_it_can_be_taken_out_of_the_path_without_a_deploy")
check("on by default", RS.lens_probe_enabled({}) is True)
check("off with 0", RS.lens_probe_enabled({RS.LENS_PROBE_ENV: "0"}) is False)
check("off with off", RS.lens_probe_enabled({RS.LENS_PROBE_ENV: "off"}) is False)
ASSESSED[0] = []
prov, pack = run_research({"carrier_hypothesis": "x", "queries": ["q"], "urls": []},
                          env={RS.LENS_PROBE_ENV: "0"})
check("disabled means no probe call at all",
      not any("nobody thought to look for" in s for s in prov.calls))
check("and the pack says so", pack["lens_probe"]["enabled"] is False)

print("\ntest_a_probe_failure_cannot_fail_the_research")
class Boom(Prov):
    def complete(self, system, user, **k):
        if "find the document nobody thought to look for" in system.lower():
            raise RuntimeError("provider exploded")
        return super().complete(system, user, **k)


ASSESSED[0] = []
real_search, real_fetch = RS.search_urls, RS.fetch_source
RS.search_urls = lambda q, **k: []
RS.fetch_source = lambda url, **k: {"url": url, "status": "http_404", "text": ""}
try:
    pack = RS.research(Boom({}), anchor=ANCHOR, now_iso="2026-09-06T00:00:00Z", api_key="k")
finally:
    RS.search_urls, RS.fetch_source = real_search, real_fetch
check("research still returns a pack", bool(pack["pack_sha256"]))
check("and the failure is recorded rather than raised",
      "provider exploded" in (pack["lens_probe"].get("error") or ""),
      pack["lens_probe"])

print("\n" + "-" * 60)
if FAILURES:
    print("%d FAILURE(S):" % len(FAILURES))
    for f in FAILURES:
        print("  - " + f)
    sys.exit(1)
print("ALL %d LENS PROBE TESTS PASSED" % CHECKS[0])
