#!/usr/bin/env python3
"""knowledge_first_test.py -- the PRIMARY commissioning lane.

What these hold: the lane licenses only a QUESTION, never a fact; it produces the SAME
seed shape the selector produces so no downstream stage is forked; it refuses rather than
invents when it cannot find a real story; and the ordinary-world lane stays the default.

Offline: real module, deterministic fakes, no provider, no network, no model calls.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import knowledge_first as KF                                           # noqa: E402

FAILURES: list = []


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %s" % (detail,)))
    if not ok:
        FAILURES.append(label)


class Reply:
    def __init__(self, text): self.text = text
    def identity(self): return {"provider": "fake"}


class FakeProvider:
    """Records what it was ASKED, so the test can prove no fact was supplied to it."""
    def __init__(self, payload): self.payload = payload; self.calls = []
    def complete(self, system, user, max_tokens=2000, **kw):
        self.calls.append({"system": system, "user": user})
        return Reply(json.dumps(self.payload))


CAND = {"subject": "A named artist's 2025 retrospective reorganised its galleries around "
                   "the artist's own captioning practice",
        "why_now": "the retrospective is touring now",
        "carrier": "the retrospective and its installation decisions",
        "tests_the_question": "it could show the practice migrated, or that it stayed",
        "names_to_research": ["Some Artist", "Some Museum"],
        "search_queries": ["some artist retrospective captioning", "some museum 2025"],
        "access_deficit_self_check": "the subject is authorship of translation, not "
                                     "whether the museum is accessible"}


APPROVED_IDS = frozenset({
    "PR001-02", "PR001-03", "PR001-05", "PR001-07", "PR001-09",
    "PR002-01", "PR002-02", "PR002-03", "PR002-05", "PR002-07",
    "PR003-03", "PR003-06", "PR003-08",
    "PR004-01", "PR004-02", "PR004-05",
})


def test_questions_are_read_from_approved_material_never_authored():
    """The perspective boundary: this module may not mint a question. It reads entries the
    owner already reviewed, each of which states its own QUESTION."""
    qs = KF.load_questions()
    check("only owner-approved durable questions load",
          {q["id"] for q in qs} == APPROVED_IDS, sorted({q["id"] for q in qs}))
    check("all loaded questions carry the approved status",
          all(q.get("status") == "APPROVED_DURABLE" for q in qs), "")
    check("each approved question is selectable in isolation",
          all(KF.select_question([q], rng=random.Random(0)) == q for q in qs), "")
    check("every question carries its provenance",
          all(q["id"] and q["doc"] and q["question"] for q in qs), "")
    check("all four approved clusters are present",
          {q["cluster"] for q in qs} >= {"PR001", "PR002", "PR003", "PR004"},
          sorted({q["cluster"] for q in qs}))
    src = (HERE / "knowledge_first.py").read_text()
    body = src.split("def load_questions")[1].split("\ndef ")[0]
    check("load_questions only reads -- no hardcoded question text",
          "?" not in body.replace('r"^\\*\\*QUESTION', ""), "")
    check("an empty directory yields no questions rather than a default",
          KF.load_questions(HERE / "does-not-exist") == [], "")


def test_the_active_cluster_is_preferred_and_exclusions_hold():
    qs = KF.load_questions()
    picks = {KF.select_question(qs, rng=random.Random(n))["cluster"] for n in range(12)}
    check("selection prefers the active cluster", picks == {"PR004"}, picks)
    pr004 = {q["id"] for q in qs if q["cluster"] == "PR004"}
    q = KF.select_question(qs, exclude=pr004, rng=random.Random(3))
    check("excluding the active cluster falls through to the others",
          q is not None and q["cluster"] != "PR004", q and q["cluster"])
    check("excluding everything returns None rather than repeating",
          KF.select_question(qs, exclude={q["id"] for q in qs}) is None, "")


def test_the_commissioning_call_is_given_a_question_and_no_facts():
    prov = FakeProvider({"candidates": [CAND]})
    q = {"id": "PR004-04", "cluster": "PR004", "title": "T", "question": "Did it migrate?",
         "doc": "d.md"}
    out = KF.propose_stories(prov, q)
    check("exactly one model call", out["model_calls"] == 1 and len(prov.calls) == 1, "")
    user = prov.calls[0]["user"]
    check("the question is handed over", "Did it migrate?" in user, "")
    check("and it is labelled as licensing NO fact",
          "licenses this question and NO fact" in user, user[:120])
    sysp = prov.calls[0]["system"]
    check("the prompt forbids access-deficit stories",
          "NO ACCESS-DEFICIT STORIES" in sysp, "")
    check("it states the removal test rather than banning words",
          "remove the accessibility language" in sysp.lower(), "")
    check("it forbids inventing a movement",
          "Do not invent a movement" in sysp, "")
    check("it forbids disability profiles-as-subject",
          "because they are disabled" in sysp, "")
    check("an empty candidate list is accepted as a correct answer",
          KF.propose_stories(FakeProvider({"candidates": []}), q)["candidates"] == [], "")


def test_the_seed_is_the_shape_the_selector_already_returns():
    """The whole point: no downstream fork. The lane's output is a seed, and acquisition,
    Research, Ledger, Worth, composition and every gate consume it unchanged."""
    fetched = {"u": 0}

    def fetch(url):
        fetched["u"] += 1
        return "x" * (KF.MIN_ANCHOR_CHARS + 10)

    rec = KF.commission(FakeProvider({"candidates": [CAND]}),
                        search_fn=lambda q, api_key="": ["https://example.org/a"],
                        fetch_fn=fetch,
                        questions=KF.load_questions(), rng=random.Random(1))
    check("it commissions", rec["status"] == "COMMISSIONED", rec.get("status"))
    seed = rec["seed"] or {}
    for k in ("id", "url", "title", "summary", "source_name",
              "underlying_article_url"):
        check("the seed carries %s, as the selector's does" % k, k in seed, sorted(seed))
    check("the anchor is a real fetched URL", seed.get("url") == "https://example.org/a", "")
    check("the record keeps the question it came from",
          (rec.get("question") or {}).get("id", "").startswith("PR"), "")
    check("and the chosen story's own access-deficit self-check",
          "access_deficit_self_check" in (rec.get("chosen") or {}), "")
    check("the seed carries no factual claim of its own",
          not any(k in seed for k in ("facts", "ledger", "claims", "evidence")), "")


def test_it_refuses_rather_than_inventing_when_there_is_no_real_anchor():
    thin = KF.commission(FakeProvider({"candidates": [CAND]}),
                         search_fn=lambda q, api_key="": ["https://example.org/thin"],
                         fetch_fn=lambda u: "too short",
                         questions=KF.load_questions(), rng=random.Random(1))
    check("an anchor below the floor is refused, not padded",
          thin["status"] == "NO_FETCHABLE_ANCHOR" and thin["seed"] is None, thin["status"])
    none = KF.commission(FakeProvider({"candidates": []}),
                         search_fn=lambda q, api_key="": ["https://example.org/a"],
                         fetch_fn=lambda u: "x" * 9999,
                         questions=KF.load_questions(), rng=random.Random(1))
    check("no story for the question is a clean refusal",
          none["status"] == "NO_STORY_FOR_QUESTION" and none["seed"] is None, none["status"])
    nosearch = KF.commission(FakeProvider({"candidates": [CAND]}),
                             search_fn=lambda q, api_key="": [],
                             fetch_fn=lambda u: "x" * 9999,
                             questions=KF.load_questions(), rng=random.Random(1))
    check("no search result is a clean refusal",
          nosearch["seed"] is None, nosearch["status"])

    class Boom:
        def complete(self, **kw): raise RuntimeError("provider down")
    broke = KF.commission(Boom(), search_fn=lambda q, api_key="": [],
                          fetch_fn=lambda u: "", questions=KF.load_questions(),
                          rng=random.Random(1))
    check("a provider failure is reported, not swallowed into a fake seed",
          broke["status"] == "COMMISSION_CALL_FAILED" and broke["seed"] is None, broke)
    check("no questions available is refused rather than defaulted",
          KF.commission(FakeProvider({"candidates": [CAND]}),
                        search_fn=lambda q, api_key="": [], fetch_fn=lambda u: "",
                        questions=[])["status"] == "NO_QUESTION_AVAILABLE", "")


def test_a_search_provider_failure_is_technical_not_editorial_scarcity():
    """THE DEFECT THIS CLOSES. A 403, an expired key or a network partition used to be
    swallowed into an empty URL list, so it arrived as a plain no-anchor refusal --
    indistinguishable from "the web has nothing about this story". That is how a real
    production blocker hid: OpenRouter began returning
    `{"error":{"message":"Key limit exceeded (monthly limit)","code":403}}` and the lane
    reported NO_FETCHABLE_ANCHOR, which reads as editorial scarcity."""
    class Boom(Exception): pass

    def dead_search(q, api_key=""):
        raise Boom("HTTP Error 403: Forbidden")

    rec = KF.commission(FakeProvider({"candidates": [CAND]}),
                        search_fn=dead_search, fetch_fn=lambda u: "x" * 9999,
                        questions=KF.load_questions(), rng=random.Random(1))
    check("the status is SEARCH_UNAVAILABLE, not a no-anchor refusal",
          rec["status"] == "SEARCH_UNAVAILABLE", rec["status"])
    check("it is flagged as a technical failure",
          rec.get("technical_failure") is True, rec.get("technical_failure"))
    check("it carries an operator-visible run_status",
          (rec.get("run_status") or {}).get("status") == "PROVIDER_FAILURE",
          rec.get("run_status"))
    check("the run_status names the stage that failed",
          (rec.get("run_status") or {}).get("stage") == "KF_SEARCH", rec.get("run_status"))
    check("the provider's own error survives for diagnosis",
          "403" in str(rec.get("error")), rec.get("error"))
    check("no seed is produced", rec.get("seed") is None, "")

    # AND THE CONVERSE, which must stay an ordinary refusal.
    ok = KF.commission(FakeProvider({"candidates": [CAND]}),
                       search_fn=lambda q, api_key="": [],
                       fetch_fn=lambda u: "x" * 9999,
                       questions=KF.load_questions(), rng=random.Random(1))
    check("a search that RAN and found nothing is NOT a technical failure",
          ok["status"] == "NO_FETCHABLE_ANCHOR"
          and not ok.get("technical_failure"), ok["status"])
    check("and it carries no run_status", ok.get("run_status") is None, "")

    # One query failing while another succeeds is ordinary, not an outage.
    calls = {"n": 0}

    def flaky(q, api_key=""):
        calls["n"] += 1
        if calls["n"] == 1:
            raise Boom("transient")
        return ["https://example.org/a"]

    half = KF.commission(FakeProvider({"candidates": [CAND]}), search_fn=flaky,
                         fetch_fn=lambda u: "x" * 9999,
                         questions=KF.load_questions(), rng=random.Random(1))
    check("a partial search failure still commissions rather than escalating",
          half["status"] == "COMMISSIONED", half["status"])


def test_a_commissioning_call_failure_is_also_technical():
    class Dead:
        def complete(self, **kw): raise RuntimeError("provider down")
    rec = KF.commission(Dead(), search_fn=lambda q, api_key="": [],
                        fetch_fn=lambda u: "", questions=KF.load_questions(),
                        rng=random.Random(1))
    check("a dead commissioning provider is technical",
          rec["status"] == "COMMISSION_CALL_FAILED"
          and rec.get("technical_failure") is True, rec["status"])
    check("with its own stage on the run_status",
          (rec.get("run_status") or {}).get("stage") == "KF_COMMISSION",
          rec.get("run_status"))


def test_a_refused_commission_persists_its_own_record():
    """A refused commission returns before any run directory exists, so the record lived
    only in the returned dict and an operational driver reading COMMISSION.json off disk
    logged nulls. The question, the proposed stories and the exact refusal reason are the
    only evidence a refused run leaves."""
    import json as _json
    import tempfile
    import new_engine_production as NEP
    with tempfile.TemporaryDirectory() as d:
        NEP._persist_commission(d, {"status": "SEARCH_UNAVAILABLE",
                                    "technical_failure": True,
                                    "question": {"id": "PR004-06", "title": "T"},
                                    "error": "HTTP Error 403: Forbidden"}, KF.LANE)
        found = list(pathlib.Path(d).glob("commission-refused-*/COMMISSION.json"))
        check("the refusal record reaches disk", len(found) == 1,
              [str(x) for x in pathlib.Path(d).iterdir()])
        if not found:
            return
        rec = _json.loads(found[0].read_text())
        check("it names the question it came from",
              rec["question"]["id"] == "PR004-06", rec.get("question"))
        check("it keeps the exact refusal reason", "403" in rec["error"], rec.get("error"))
        check("and the lane", rec["lane"] == KF.LANE, rec.get("lane"))
    check("an empty record writes nothing rather than an empty directory",
          NEP._persist_commission(tempfile.mkdtemp(), {}, KF.LANE) is None, "")


def test_the_caller_surfaces_a_technical_commission_failure_as_infra():
    src = (HERE / "new_engine_production.py").read_text()
    seg = src.split("if lane == KF.LANE:")[1].split("else:")[0]
    check("a technical commissioning failure holds rather than reporting no source",
          'commission.get("technical_failure")' in seg, "")
    check("and passes the lane's own run_status through to the operator",
          'out["run_status"] = commission["run_status"]' in seg, "")
    check("an honest refusal still reports no_usable_source",
          '"no_usable_source"' in seg, "")
    check("and every refusal persists its record",
          "_persist_commission(evidence_root, commission, lane)" in seg, "")


def test_the_ordinary_world_lane_is_untouched_and_still_the_default():
    src = (HERE / "new_engine_production.py").read_text()
    check("the default lane is the ordinary-world collision lane",
          "LANE_DEFAULT = KF.LANE_SECONDARY" in src, "")
    check("the knowledge-first lane must be requested explicitly",
          "lane: str = LANE_DEFAULT" in src, "")
    check("the selector path still exists, unchanged",
          "_select_seed(orch, model)" in src, "")
    check("both lanes converge on the same R.run call",
          src.count("out = R.run(payload") == 1, src.count("out = R.run(payload"))
    check("the lane is recorded on the run's acquisition artifact",
          '"lane": lane' in src, "")
    check("the commissioning record is persisted for audit",
          'COMMISSION.json' in src, "")


def test_no_downstream_factual_standard_is_touched_by_this_lane():
    src = (HERE / "knowledge_first.py").read_text()
    for banned in ("freeze_ledger", "worth_gate", "ground_candidate", "safety_audit",
                   "fact_check", "TRUE_UNCERTAIN", "publication_eligible",
                   "run_story_architecture_composition"):
        check("the lane does not touch %s" % banned, banned not in src, "")
    check("it states the perspective boundary in its own docstring",
          "licenses only a\nQUESTION" in src or "licenses only a QUESTION" in src, "")


def main() -> int:
    for fn in (test_questions_are_read_from_approved_material_never_authored,
               test_the_active_cluster_is_preferred_and_exclusions_hold,
               test_the_commissioning_call_is_given_a_question_and_no_facts,
               test_the_seed_is_the_shape_the_selector_already_returns,
               test_it_refuses_rather_than_inventing_when_there_is_no_real_anchor,
               test_a_search_provider_failure_is_technical_not_editorial_scarcity,
               test_a_commissioning_call_failure_is_also_technical,
               test_a_refused_commission_persists_its_own_record,
               test_the_caller_surfaces_a_technical_commission_failure_as_infra,
               test_the_ordinary_world_lane_is_untouched_and_still_the_default,
               test_no_downstream_factual_standard_is_touched_by_this_lane):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL KNOWLEDGE-FIRST LANE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
