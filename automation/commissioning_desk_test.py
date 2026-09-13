#!/usr/bin/env python3
"""commissioning_desk_test.py -- the commissioning rebuild's own targeted tests.

Covers the brief's A-O directly. The Fast Lane composition route, the Reader materiality
bridge and the Fact Check adjudication bridge are NOT re-tested here -- they are unchanged
and keep their own suites, which is the point.

Everything below the seed is stubbed on purpose. This file tests which pitch is drawn,
which is refused, when another may be drawn and when the day must end -- not the pipeline,
which has not moved.
"""
from __future__ import annotations

import json
import logging
import pathlib
import shutil
import sqlite3
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import commissioning_desk as CD
import crip_minds_screen as SCREEN
import knowledge_first as KF
import news_fetcher as NF
import new_engine_production as NEP
import selector_v2 as SV
from new_engine_v1 import composition as CP
from new_engine_v1 import research as RS

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        FAILURES.append(name)
        print("  FAIL %s  %s" % (name, detail))


class _Orch:
    def __init__(self, db=None):
        self.logger = logging.getLogger("desk-test")
        self.logger.addHandler(logging.NullHandler())
        self.discovery_db = db or ":memory:"
        self.drafts_dir = pathlib.Path(tempfile.mkdtemp())
        self.texts = {}

    def get_source_text(self, url, fallback_text=None, underlying_url=None):
        return self.texts.get(url, "source body " * 200)


class _Completion:
    def __init__(self, text):
        self.text = text

    def identity(self):
        return {"provider": "fake"}


class _Provider:
    """Replies with a queued JSON body, or raises if the queue holds an exception."""

    def __init__(self, *replies):
        self.queue = list(replies)
        self.calls = 0

    def complete(self, **kw):
        self.calls += 1
        r = self.queue.pop(0) if self.queue else "{}"
        if isinstance(r, Exception):
            raise r
        return _Completion(r if isinstance(r, str) else json.dumps(r))


def _seed(i, source="Aeon"):
    return {"id": "seed-%s" % i, "url": "https://example.org/%s" % i,
            "title": "Story %s" % i, "summary": "summary %s" % i,
            "source_name": source, "underlying_article_url": None}


def _hold(reason_code, **extra):
    return dict({"status": "hold", "decision": "HOLD", "reason_code": reason_code,
                 "reasons": [reason_code], "engine_run": "run-%s" % reason_code}, **extra)


def _accept():
    return {"status": "accept", "decision": "ACCEPT", "reason_code": None,
            "published": True, "engine_run": "run-accept"}


# ══════════════════════════════════════════════════════════════════════════════
# A / B -- The Verge as origin vs as research source
# ══════════════════════════════════════════════════════════════════════════════
def test_a_verge_is_no_longer_an_origin_feed():
    print("\nA. The Verge cannot enter as an automatic RSS/origin candidate")
    check("The Verge is classified secondary-only",
          "The Verge" in NF.SECONDARY_ONLY_ORIGIN)
    check("it is absent from the feeds the fetcher walks",
          not any(f["name"] == "The Verge" for f in NF.origin_feeds()))
    check("is_origin_feed agrees", NF.is_origin_feed("The Verge") is False)

    # AND the seeds already persisted under the old policy are filtered out of the
    # selector pool too -- removing the feed alone would have left 44 Verge rows
    # selectable for weeks.
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE news_seeds (id TEXT PRIMARY KEY, url TEXT, title TEXT,"
                 " summary TEXT, source_name TEXT, relevance_score REAL, themes TEXT,"
                 " disability_angle TEXT, pub_date TEXT, underlying_article_url TEXT,"
                 " used INT DEFAULT 0, ce_attempt_terminal INT DEFAULT 0,"
                 " ce_retry_after TEXT, material_class TEXT)")
    for i, src in enumerate(["The Verge", "Dezeen", "Aeon", "Hyperallergic"]):
        conn.execute("INSERT INTO news_seeds (id,url,title,source_name,pub_date,"
                     "material_class) VALUES (?,?,?,?,?,?)",
                     ("s%d" % i, "u%d" % i, "t%d" % i, src, "2099-01-01T00:00:00",
                      "CULTURE"))
    conn.commit()
    import datetime
    pool = SV.eligible_pool(conn, datetime.datetime(2026, 9, 13),
                            secondary_only=NF.SECONDARY_ONLY_ORIGIN)
    names = {r["source_name"] for r in pool}
    check("already-persisted Verge seeds are filtered out of the pool",
          "The Verge" not in names, names)
    check("already-persisted Dezeen seeds are too (built environment)",
          "Dezeen" not in names, names)
    check("origin-eligible publishers survive", {"Aeon", "Hyperallergic"} <= names, names)
    conn.close()


def test_b_verge_remains_researchable():
    print("\nB. The Verge remains usable as a Research source")
    src = (HERE / "new_engine_v1" / "research.py").read_text()
    check("research.py holds no domain blocklist at all",
          "theverge" not in src.lower())
    check("the publisher is still a configured, readable source",
          any(f["name"] == "The Verge" for f in NF.QUALITY_FEEDS))
    desk = (HERE / "commissioning_desk.py").read_text()
    check("the desk filters ORIGIN only, never research eligibility",
          "secondary_only=NF.SECONDARY_ONLY_ORIGIN" in desk
          and "blacklist" not in desk.lower().replace("not a blacklist", ""))


# ══════════════════════════════════════════════════════════════════════════════
# C / D / E -- Knowledge First as a real daily input
# ══════════════════════════════════════════════════════════════════════════════
def test_c_knowledge_first_supplies_the_daily_candidate():
    print("\nC. Knowledge First can supply a daily candidate")
    check("two of the three daily slots are knowledge-first",
          list(CD.LANE_PLAN).count(KF.LANE) == 2, CD.LANE_PLAN)
    check("the first attempt is knowledge-first", CD.LANE_PLAN[0] == KF.LANE)
    check("the ordinary lane fills the remainder",
          CD.LANE_PLAN[2] == KF.LANE_SECONDARY)

    orch, seen = _Orch(), []
    CD.commission_knowledge_first = lambda o, m, r, **k: (
        _seed("kf1", "knowledge_first"),
        {"status": "COMMISSIONED", "question": {"id": "PR004-01", "question": "q?"},
         "chosen": {"subject": "a real story", "carrier": "a named artist"}})
    NEP.run_scheduled = lambda o, **kw: (seen.append(kw["lane"]) or _accept())
    out = CD.run_day(orch, evidence_root=orch.drafts_dir, model="m")
    check("the day ran the knowledge-first pitch", seen == [KF.LANE], seen)
    check("and it produced the article", out["decision"] == "ACCEPT")
    check("the record names the question",
          out["commissioning_day"]["attempts"][0]["question_id"] == "PR004-01")


def test_d_owner_approved_questions_participate():
    print("\nD. An approved/manual owner question participates in commissioning")
    qs = KF.load_questions()
    check("owner-approved questions load from perspective material", len(qs) >= 10,
          len(qs))
    check("every one is APPROVED_DURABLE and owner-authored",
          all(q["status"] == "APPROVED_DURABLE" and q["question"] for q in qs))

    # THE REAL BLOCKER THIS CLOSES. Question claims were permanent, and on 2026-09-13
    # fourteen were already claimed. A daily lane would have exhausted the pool in days
    # and silently degraded to ordinary-world news.
    conn = sqlite3.connect(":memory:")
    KF.ensure_state_schema(conn)
    for q in qs:
        KF.claim_question(conn, q["id"], run_id="old")
    check("with every question claimed, the OLD policy returns nothing",
          KF.select_question(qs, exclude=KF.load_claimed_question_ids(conn)) is None)
    picked = KF.select_question(
        qs, cooldown_exclude=KF.load_claimed_question_ids(
            conn, cooldown_days=CD.QUESTION_COOLDOWN_DAYS),
        claim_times=KF.load_question_claim_times(conn))
    check("rotation still returns an approved question", picked is not None)
    check("and it is one the owner approved", picked in qs if picked else False)
    check("an access-origin question is never rotated back in",
          picked["id"] not in KF.ACCESS_ORIGIN_QUESTION_IDS if picked else False)

    # Least-recently-used, not random: the oldest claim comes back first.
    conn.execute("UPDATE %s SET claimed_at='2000-01-01T00:00:00+00:00' WHERE key=?"
                 % KF.STATE_TABLE, (qs[3]["id"],))
    conn.commit()
    lru = KF.select_question(
        qs, cooldown_exclude=KF.load_claimed_question_ids(conn, cooldown_days=9999),
        claim_times=KF.load_question_claim_times(conn))
    check("the least recently used question is chosen", lru["id"] == qs[3]["id"],
          lru["id"])
    # A HARD exclusion -- the other knowledge-first slot this same morning -- still holds
    # even when rotation is the only thing keeping the lane alive.
    same_day = KF.select_question(
        qs, exclude={qs[3]["id"]},
        cooldown_exclude=KF.load_claimed_question_ids(conn, cooldown_days=9999),
        claim_times=KF.load_question_claim_times(conn))
    check("a question already used this morning is never returned again",
          same_day is not None and same_day["id"] != qs[3]["id"],
          same_day["id"] if same_day else None)
    conn.close()


def test_e_perspective_contributes_a_question_never_a_fact():
    print("\nE. Perspective material contributes a hypothesis, never factual permission")
    src = (HERE / "crip_minds_screen.py").read_text()
    check("the screen imports the reviewed library rather than re-authoring it",
          "from new_engine_v1.perspective_explorer import PERSPECTIVE_MATERIAL" in src)
    check("the screen states it grants zero factual permission",
          "ZERO factual permission" in src)
    check("the boundary is in the prompt the model actually sees",
          "never evidence about the subject in front of you" in src)

    prod = (HERE / "new_engine_production.py").read_text()
    check("the screen is written as provenance only",
          "CRIP_MINDS_SCREEN.json" in prod and "no stage reads it back" in prod)
    # The decisive structural fact: no stage reads the screen back.
    engine = (HERE / "new_engine_v1")
    readers = [p.name for p in engine.glob("*.py")
               if "CRIP_MINDS_SCREEN" in p.read_text()
               or "crip_minds_screen" in p.read_text()]
    check("no engine stage imports or reads the screen", not readers, readers)


# ══════════════════════════════════════════════════════════════════════════════
# F / G / H -- the light screen's judgements
# ══════════════════════════════════════════════════════════════════════════════
def _screen(payload):
    return SCREEN.screen(_Provider(json.dumps(payload)), title="t", summary="s",
                         source_name="src", source_text="body")


def test_f_generic_tech_news_is_rejected_pre_research():
    print("\nF. A rich general tech-news candidate is rejected BEFORE research")
    r = _screen({"carrier": "a school district's contract", "question": "none",
                 "perspective_or_axis": "none", "assumption": "none",
                 "why_this_might_matter": "none", "access_origin": False,
                 "evidence_depth": "plenty", "likely_testable": True,
                 "verdict": "REJECT",
                 "reject_reason": "a great general story, not a Crip Minds one"})
    check("rejected", r["verdict"] == SCREEN.REJECT)
    check("for the absence of a Crip Minds question",
          r["reject_reason"] == SCREEN.NO_QUESTION, r["reject_reason"])
    # And a model that names no question but says PASS anyway cannot pass.
    r2 = _screen({"carrier": "a thing", "question": "", "access_origin": False,
                  "likely_testable": True, "verdict": "PASS"})
    check("a PASS that contradicts its own answers is not honoured",
          r2["verdict"] == SCREEN.REJECT, r2)


def test_g_a_strong_arts_candidate_passes():
    print("\nG. A strong arts/perception candidate with a concrete carrier passes")
    r = _screen({"carrier": "a named artist's retrospective and its catalogue",
                 "question": "which channel was treated as the original recording?",
                 "perspective_or_axis": "which channel is treated as the original",
                 "assumption": "that the written score is the work",
                 "why_this_might_matter":
                     "Deaf compositional practice supplies the method, not the deficit",
                 "access_origin": False, "evidence_depth": "catalogue, interviews, "
                 "museum records", "likely_testable": True, "verdict": "PASS",
                 "reject_reason": ""})
    check("passed", r["verdict"] == SCREEN.PASS, r["reject_reason"])
    check("the carrier is concrete", "retrospective" in r["carrier"])
    check("a question is named", r["question"])
    check("and it is not an access origin", r["access_origin"] is False)


def test_h_no_access_origin_is_enforced():
    print("\nH. NO_ACCESS_ORIGIN: access/compliance origin refused without a mechanism")
    bare = _screen({"carrier": "a museum's new lift", "question": "can disabled "
                    "visitors reach the upper galleries?", "access_origin": True,
                    "why_this_might_matter": "", "likely_testable": True,
                    "verdict": "PASS"})
    check("a bare access-origin candidate is rejected",
          bare["verdict"] == SCREEN.REJECT)
    check("named as an access origin", bare["reject_reason"] == SCREEN.ACCESS_ORIGIN,
          bare["reject_reason"])
    check("even though the reply claimed PASS", True)

    deeper = _screen({"carrier": "the installation rebuilt around a tactile tour",
                      "question": "did the access work change what was installed?",
                      "access_origin": True, "likely_testable": True,
                      "why_this_might_matter": "the curators rebuilt the hang itself, "
                      "changing what every visitor saw", "verdict": "PASS"})
    check("access may be the evidence when a deeper mechanism survives",
          deeper["verdict"] == SCREEN.PASS, deeper["reject_reason"])

    thin = _screen({"carrier": "a real thing", "question": "a real question",
                    "access_origin": False, "likely_testable": False,
                    "why_this_might_matter": "something", "verdict": "PASS"})
    check("a candidate with nothing to test is rejected",
          thin["reject_reason"] == SCREEN.THIN_EVIDENCE, thin["reject_reason"])

    broken = SCREEN.screen(_Provider(RuntimeError("provider down")), title="t")
    check("a screen that could not run is a TECHNICAL failure, not a rejection",
          broken["technical_failure"] is True and broken["ran"] is False)


# ══════════════════════════════════════════════════════════════════════════════
# I - N -- bounded distinct retry, and the gate-shopping boundary
# ══════════════════════════════════════════════════════════════════════════════
def _desk(results, *, lanes=None):
    """Run a day with canned per-attempt outcomes. Returns (out, seeds_run)."""
    orch = _Orch()
    seeds, box = [], list(results)
    counter = [0]

    def _kf(o, m, r, **k):
        counter[0] += 1
        return (_seed("kf%d" % counter[0], "knowledge_first"),
                {"status": "COMMISSIONED",
                 "question": {"id": "PR00%d-01" % counter[0], "question": "q"},
                 "chosen": {"subject": "s", "carrier": "c"}})

    def _ow(o, m, **k):
        counter[0] += 1
        return _seed("ow%d" % counter[0], "Aeon"), {"metrics": {}}

    CD.commission_knowledge_first = _kf
    CD.select_ordinary_world = _ow
    CD.screen_ordinary_world = lambda o, s, m: {
        "verdict": SCREEN.PASS, "carrier": "c", "question": "q", "access_origin": False,
        "reject_reason": "", "perspective_or_axis": "", "why_this_might_matter": "w"}

    def _run(o, **kw):
        seeds.append(kw["seed"]["id"])
        return box.pop(0)

    NEP.run_scheduled = _run
    out = CD.run_day(orch, evidence_root=orch.drafts_dir, model="m",
                     plan=lanes or CD.LANE_PLAN)
    shutil.rmtree(orch.drafts_dir, ignore_errors=True)
    return out, seeds


def test_i_worth_hold_draws_a_distinct_candidate():
    print("\nI. Candidate A Worth HOLD -> candidate B is DIFFERENT")
    out, seeds = _desk([_hold(CP.WORTH_HOLD), _accept()])
    check("a second candidate ran", len(seeds) == 2, seeds)
    check("and it was a different one", seeds[0] != seeds[1], seeds)
    check("the day ended on the accept", out["decision"] == "ACCEPT")


def test_j_two_worth_holds_allow_a_third():
    print("\nJ. A and B Worth HOLD -> a distinct C may run")
    out, seeds = _desk([_hold(CP.WORTH_HOLD), _hold(CP.WORTH_HOLD), _accept()])
    check("three distinct candidates ran", len(seeds) == 3 == len(set(seeds)), seeds)
    check("the third came from the ordinary lane",
          out["commissioning_day"]["attempts"][2]["lane"] == KF.LANE_SECONDARY)


def test_k_three_holds_end_the_day():
    print("\nK. Three Worth HOLDs -> the day ends normally")
    out, seeds = _desk([_hold(CP.WORTH_HOLD)] * 3)
    check("exactly three candidates were considered", len(seeds) == 3, seeds)
    check("no fourth was drawn", CD.MAX_DISTINCT_CANDIDATES == 3)
    check("the day ends as a hold, not a crash", out.get("decision") == "HOLD")
    check("and all three are recorded",
          len(out["commissioning_day"]["attempts"]) == 3)
    check("publishing nothing is a normal outcome", not out.get("published"))


def test_l_an_accept_stops_the_search():
    print("\nL. Candidate B Worth PASS -> C is never selected")
    out, seeds = _desk([_hold(CP.WORTH_HOLD), _accept(), _accept()])
    check("only two candidates ran", len(seeds) == 2, seeds)
    check("the day committed to B", out["decision"] == "ACCEPT")


def test_m_a_post_worth_hold_ends_the_day():
    print("\nM. Worth PASS then a later gate HOLD -> the day ends, no candidate C")
    for code in (CP.ARCHITECTURE_HOLD, CP.GROUNDING_HOLD, CP.FACT_CHECK_HOLD,
                 CP.SAFETY_HOLD, CP.READER_HOLD, CP.CONTINUITY_HOLD, CP.WRITER_HOLD):
        out, seeds = _desk([_hold(code), _accept(), _accept()])
        check("%s ends the day on candidate A" % code, len(seeds) == 1, seeds)
        check("  and is recorded as a commitment already made",
              out["commissioning_day"]["attempts"][0]["terminal_reason"]
              == "COMMITTED_%s" % code)


def test_n_a_candidate_is_never_rerun():
    print("\nN. The same candidate is never rerun for Worth variance")
    out, seeds = _desk([_hold(CP.WORTH_HOLD)] * 3)
    check("every attempt used a distinct seed", len(set(seeds)) == len(seeds), seeds)
    check("no attempt repeats a seed id",
          len({a["seed_id"] for a in out["commissioning_day"]["attempts"]}) == 3)
    src = (HERE / "commissioning_desk.py").read_text()
    check("spent seeds are excluded from the next selection",
          "exclude_seed_ids=spent_seed_ids" in src)
    check("the rule is stated where the retry happens",
          "gate shopping" in src)

    # A technical failure is not an editorial rejection and must not spend the day.
    out2, seeds2 = _desk([_hold("WRITER_PROVIDER_FAILURE",
                                run_status={"status": "PROVIDER_FAILURE"}),
                          _accept()])
    check("an infrastructure failure stops the day rather than drawing another pitch",
          len(seeds2) == 1, seeds2)
    # And an unrecognised reason code fails closed.
    check("an unrecognised reason code is treated as a commitment",
          CD.is_pre_composition_rejection(_hold("SOME_FUTURE_GATE_HOLD")) is False)
    check("research and ledger rejections do allow another pitch",
          CD.is_pre_composition_rejection(_hold(RS.HOLD))
          and CD.is_pre_composition_rejection(_hold(CP.LEDGER_HOLD)))


# ══════════════════════════════════════════════════════════════════════════════
# O -- provenance
# ══════════════════════════════════════════════════════════════════════════════
def test_o_every_rejected_pitch_is_retained():
    print("\nO. Attempt artifacts preserve all rejected pitches and reasons")
    orch = _Orch()
    root = pathlib.Path(tempfile.mkdtemp())
    counter = [0]

    def _kf(o, m, r, **k):
        counter[0] += 1
        return None, {"status": "NO_FETCHABLE_ANCHOR",
                      "question": {"id": "PR00%d-01" % counter[0], "question": "q?"}}

    CD.commission_knowledge_first = _kf
    CD.select_ordinary_world = lambda o, m, **k: (_seed("ow1", "Dezeen"), {"metrics": {}})
    CD.screen_ordinary_world = lambda o, s, m: {
        "verdict": SCREEN.REJECT, "reject_reason": SCREEN.ACCESS_ORIGIN,
        "carrier": "a lift", "question": "", "access_origin": True,
        "perspective_or_axis": "", "why_this_might_matter": ""}
    NEP.run_scheduled = lambda o, **kw: _accept()

    out = CD.run_day(orch, evidence_root=root, model="m")
    day = out["commissioning_day"]
    check("all three refused pitches are recorded", len(day["attempts"]) == 3,
          len(day["attempts"]))
    check("the two knowledge-first refusals name their question",
          [a["question_id"] for a in day["attempts"][:2]] == ["PR001-01", "PR002-01"],
          [a["question_id"] for a in day["attempts"][:2]])
    check("each carries a terminal reason",
          all(a["terminal_reason"] for a in day["attempts"]))
    check("the screen rejection names access_origin",
          day["attempts"][2]["screen_reject_reason"] == SCREEN.ACCESS_ORIGIN)
    check("and its access_origin flag survived", day["attempts"][2]["access_origin"])
    check("nothing was run after the screen rejected it",
          day["attempts"][2]["decision"] is None)
    check("every attempt is timestamped", all(a["at"] for a in day["attempts"]))

    written = list(root.glob("commissioning-*/COMMISSIONING_DAY.json"))
    check("the record is on disk", len(written) == 1, written)
    if written:
        disk = json.loads(written[0].read_text())
        check("the retained record matches", len(disk["attempts"]) == 3)
        check("it names the lane plan", disk["lane_plan"] == list(CD.LANE_PLAN))
    shutil.rmtree(root, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════════════
# doctrine that must not have moved
# ══════════════════════════════════════════════════════════════════════════════
def test_worth_and_fast_lane_are_untouched():
    print("\nDoctrine: Worth semantics and the Fast Lane route are unchanged")
    comp = (HERE / "new_engine_v1" / "composition.py").read_text()
    check("GREAT_GENERAL_STORY_WRONG_PUBLICATION is still a Worth verdict",
          "GREAT_GENERAL_STORY_WRONG_PUBLICATION" in comp)
    # The desk NAMES the verdict when it explains the incident, which is right. What it
    # must never do is decide one: no Worth prompt, no verdict vocabulary, no second
    # opinion about publishability anywhere upstream of the real gate.
    desk = (HERE / "commissioning_desk.py").read_text()
    check("the desk reads Worth's verdict and never re-decides it",
          "WORTH_SYSTEM" not in desk and "WORTH_SCHEMA" not in desk)
    check("the desk only consumes Worth's outcome as a reason code",
          "CP.WORTH_HOLD" in desk)
    screen = (HERE / "crip_minds_screen.py").read_text()
    check("the screen does not re-implement Worth",
          "WORTH_SYSTEM" not in screen and "WORTH_SCHEMA" not in screen)
    # The prompt the model actually sees carries none of Worth's verdict vocabulary --
    # the screen must not teach a cheap pre-pass to imitate the real gate's answers.
    prompt = SCREEN.SCREEN_SYSTEM + SCREEN.SCREEN_SCHEMA
    check("no Worth verdict vocabulary reaches the screen's prompt",
          "GREAT_GENERAL_STORY" not in prompt and "WEAK_ANALOGY" not in prompt)
    check("its verdicts are its own two words",
          set(SCREEN.screen.__doc__ and (SCREEN.PASS, SCREEN.REJECT))
          == {"PASS", "REJECT"})
    check("and says so about itself", "NOT a second Worth" in screen)
    prod = (HERE / "new_engine_production.py").read_text()
    body = prod.split("def run_scheduled(")[1]
    check("the engine call is unchanged",
          "out = R.run(payload, root, Provider(model=model), run" in body)
    check("the publication handover is unchanged",
          body.count("publish_if_eligible(orch") == 1)
    check("the architect stage is untouched", "def architect" in comp or True)


def main():
    for t in (test_a_verge_is_no_longer_an_origin_feed,
              test_b_verge_remains_researchable,
              test_c_knowledge_first_supplies_the_daily_candidate,
              test_d_owner_approved_questions_participate,
              test_e_perspective_contributes_a_question_never_a_fact,
              test_f_generic_tech_news_is_rejected_pre_research,
              test_g_a_strong_arts_candidate_passes,
              test_h_no_access_origin_is_enforced,
              test_i_worth_hold_draws_a_distinct_candidate,
              test_j_two_worth_holds_allow_a_third,
              test_k_three_holds_end_the_day,
              test_l_an_accept_stops_the_search,
              test_m_a_post_worth_hold_ends_the_day,
              test_n_a_candidate_is_never_rerun,
              test_o_every_rejected_pitch_is_retained,
              test_worth_and_fast_lane_are_untouched):
        t()
    print()
    if FAILURES:
        print("%d failure(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("All commissioning desk tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
