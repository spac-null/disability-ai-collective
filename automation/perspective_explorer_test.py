#!/usr/bin/env python3
"""perspective_explorer_test.py -- the bounded fallback, and only the fallback.

What is tested here is the trigger, not the taste: the Explorer must never run when
the Lens Probe already found a carrier, must run AT MOST once when it did not, and a
clean "nothing" from the Explorer must leave research() exactly where it already was.

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


ANCHOR_TEXT = ("A municipal water utility replaced its analogue meters with smart "
               "meters that report usage every fifteen minutes.")
ANCHOR = {"url": "https://example.org/anchor", "text": ANCHOR_TEXT,
          "sha256": C.sha256_text(ANCHOR_TEXT), "title": "Utility upgrade",
          "publisher": "example.org", "accessed_at": "2026-09-08T00:00:00Z",
          "fetch_status": "ok", "content_length": len(ANCHOR_TEXT)}

EXPLORER_PAGE = ("Billing dispute policy: a customer may challenge a reading within "
                 "30 days. Automated readings are provisional until a technician "
                 "confirms them on the next scheduled visit.")


class Prov:
    """scope -> lens probe -> [perspective explorer] -> assess, in that order."""

    def __init__(self, probe_reply, explorer_reply=None):
        self.calls = []
        self.probe_reply = probe_reply
        self.explorer_reply = explorer_reply or {"convergence": True}

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                 deadline=None):
        self.calls.append(system)
        low = system.lower()
        if "scope research" in low:
            body = {"subject": "the smart meter rollout", "queries": ["q1"],
                    "anchor_kind": "news_report", "anchor_subject_words": 80,
                    "questions": [], "named_entities": ["utility"]}
        elif "epistemic methods" in low:
            body = self.explorer_reply
        elif "what does this subject assume about" in low:
            body = self.probe_reply
        else:
            body = {"sources": [
                {"source_id": s, "role": "PRIMARY", "relation": "extends",
                 "why_relevant": "the utility's own policy page",
                 "excerpts": ["Automated readings are provisional until a technician "
                             "confirms them on the next scheduled visit."]}
                for s in ASSESSED[0]]}

        class R:
            text = json.dumps(body)

            def identity(self_):
                return {"provider": "scripted"}
        return R()


ASSESSED = [[]]
SEARCHED = []
FETCHED = []


def run_research(probe_reply, explorer_reply=None, env=None, pages=None):
    pages = pages or {}
    SEARCHED[:] = []
    FETCHED[:] = []
    prov = Prov(probe_reply, explorer_reply)
    real_search, real_fetch = RS.search_urls, RS.fetch_source
    RS.search_urls = lambda q, **k: (SEARCHED.append(q)
                                     or ["https://utility.example/"])

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
        pack = RS.research(prov, anchor=ANCHOR, now_iso="2026-09-08T00:00:00Z",
                           api_key="k")
    finally:
        RS.search_urls, RS.fetch_source = real_search, real_fetch
        os.environ.clear()
        os.environ.update(old)
    return prov, pack


def explorer_calls(prov):
    return [s for s in prov.calls if "epistemic methods" in s.lower()]


print("test_lens_hypothesis_present_explorer_not_called")
ASSESSED[0] = ["S1"]
prov, pack = run_research(
    {"assumption": "that all customers read a bill the same way",
     "carrier_hypothesis": "the utility's own billing FAQ",
     "queries": [], "urls": []})
check("the lens probe found a carrier", pack["lens_probe"]["carrier_hypothesis"] != "")
check("the explorer was never called", explorer_calls(prov) == [], prov.calls)
check("the pack says the explorer did not run", pack["perspective_explorer"]["ran"] is False)

print("\ntest_lens_nothing_explorer_called_at_most_once")
ASSESSED[0] = ["S1"]
prov, pack = run_research(
    {"carrier_hypothesis": "none", "queries": [], "urls": []},
    explorer_reply={
        "convergence": False,
        "methods_selected": [{"method": "billing operations", "native": True},
                             {"method": "behavioural decision science", "native": False}],
        "collision": "billing treats a reading as settled on receipt; decision "
                     "science predicts a disputed reading is not fully revised in "
                     "the customer's own belief even after correction",
        "person_assumption_check": "about the customer's own understanding of a "
                                   "bill, not only the utility's process",
        "assumption": "that a customer treats an automated reading as final the "
                      "moment it appears on a bill",
        "carrier_hypothesis": "the utility's own dispute policy, which calls "
                              "automated readings provisional until a technician "
                              "confirms them",
        "seed_or_instrument_used": "none",
        "why_question_survived": "billing operations alone would not have asked "
                                 "whether the customer's belief lags a correction",
        "queries": [],
        "urls": ["https://utility.example/billing-policy"]},
    pages={"https://utility.example/billing-policy": EXPLORER_PAGE})
check("the lens probe found nothing", pack["lens_probe"]["carrier_hypothesis"] == "")
check("exactly one explorer call", len(explorer_calls(prov)) == 1, prov.calls)
check("the named url was fetched", "https://utility.example/billing-policy" in FETCHED)
check("it is in the pack as ordinary material",
      any("billing-policy" in s["url"] for s in pack["sources"]))
check("it is marked as the explorer's",
      pack["perspective_explorer"]["kept"] == ["S1"], pack["perspective_explorer"])
check("the hypothesis is recorded for audit only",
      "provisional" in pack["perspective_explorer"]["carrier_hypothesis"])
check("collision reasoning is retained for audit",
      "decision science" in pack["perspective_explorer"]["collision"])
check("audit metadata never enters the source material",
      all("collision" not in json.dumps(s) for s in pack["sources"]))

print("\ntest_explorer_nothing_leaves_the_clean_no_reading_path")
ASSESSED[0] = []
prov, pack = run_research(
    {"carrier_hypothesis": "none", "queries": [], "urls": []},
    explorer_reply={"convergence": True})
check("the lens probe found nothing", pack["lens_probe"]["carrier_hypothesis"] == "")
check("the explorer ran exactly once", len(explorer_calls(prov)) == 1)
check("the explorer found nothing", pack["perspective_explorer"]["carrier_hypothesis"] == "")
check("it kept no sources", pack["perspective_explorer"]["kept"] == [])
check("it searched nothing of its own beyond the ordinary pass",
      SEARCHED == ["q1"], SEARCHED)
check("the pack is still a clean, ordinary pack",
      pack["pack_sha256"] and isinstance(pack["sources"], list))

print("\n" + "-" * 60)
if FAILURES:
    print("%d FAILURE(S):" % len(FAILURES))
    for f in FAILURES:
        print("  - " + f)
    sys.exit(1)
print("ALL %d PERSPECTIVE EXPLORER TESTS PASSED" % CHECKS[0])
