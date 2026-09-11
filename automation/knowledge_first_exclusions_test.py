#!/usr/bin/env python3
"""knowledge_first_exclusions_test.py -- persisted question/story exclusions, NO_ACCESS_ORIGIN.

What these hold, on top of knowledge_first_test.py: a question already attempted by an
earlier, separate process is not selected again; a story already commissioned is not
recommissioned under a different question or a different source URL, once its identity is
known by a quoted title; a failed or held attempt still consumes the identity it claimed; a
question whose own proposition originates in access provision/intervention is never selected,
while a mediation/authorship/translation question is; and accessibility facts may still exist
inside the evidence of an allowed commission.

Offline: real module, deterministic fakes, a real sqlite file (tempfile), no provider, no
network, no model calls. A file-backed connection (not :memory:) is used deliberately, and
reopened between steps, so "a later process" is not a metaphor -- it is a second connection
that never saw the first one's in-memory state.
"""
from __future__ import annotations

import json
import pathlib
import random
import sqlite3
import sys
import tempfile

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
    def __init__(self, payload): self.payload = payload; self.calls = []
    def complete(self, system, user, max_tokens=2000, **kw):
        self.calls.append({"system": system, "user": user})
        return Reply(json.dumps(self.payload))


class Boom:
    def complete(self, **kw): raise RuntimeError("provider down")


def _q(qid, title="T", question="Q?", cluster=None):
    return {"id": qid, "cluster": cluster or qid.split("-")[0], "title": title,
            "question": question, "doc": "synthetic.md"}


def _cand(subject, queries):
    return {"subject": subject, "why_now": "now", "carrier": "carrier",
            "tests_the_question": "tests it", "names_to_research": ["Some Name"],
            "search_queries": queries,
            "access_deficit_self_check": "not about access"}


def _fetch_ok(u):
    return "x" * (KF.MIN_ANCHOR_CHARS + 10)


def test_a_claimed_question_is_excluded_by_a_later_process():
    """Two processes, two connections to the same file -- the second must see the first's
    claim without ever sharing memory with it."""
    with tempfile.TemporaryDirectory() as d:
        dbpath = str(pathlib.Path(d) / "state.db")
        q1, q2 = _q("ZZ001-01"), _q("ZZ001-02")

        conn1 = sqlite3.connect(dbpath)
        rec1 = KF.commission(
            FakeProvider({"candidates": [_cand("Story One", ["query one"])]}),
            search_fn=lambda q, api_key="": ["https://example.org/one"],
            fetch_fn=_fetch_ok, questions=[q1, q2], state_conn=conn1, run_id="proc-1",
            rng=random.Random(0))
        conn1.close()
        check("process 1 commissions successfully", rec1["status"] == "COMMISSIONED",
              rec1.get("status"))
        check("process 1 picked one of the two synthetic questions",
              rec1["question"]["id"] in ("ZZ001-01", "ZZ001-02"), rec1["question"])
        used_id = rec1["question"]["id"]
        other_id = "ZZ001-02" if used_id == "ZZ001-01" else "ZZ001-01"

        conn2 = sqlite3.connect(dbpath)
        claimed = KF.load_claimed_question_ids(conn2)
        check("a fresh connection sees the first process's claim", used_id in claimed,
              claimed)
        picked = KF.select_question([q1, q2], exclude=claimed, rng=random.Random(0))
        check("only the unused question remains selectable",
              picked is not None and picked["id"] == other_id, picked)
        conn2.close()


def test_a_claimed_anchor_is_not_recommissioned_by_a_different_question():
    with tempfile.TemporaryDirectory() as d:
        dbpath = str(pathlib.Path(d) / "state.db")
        qa, qb = _q("ZZ002-01"), _q("ZZ002-02")

        conn1 = sqlite3.connect(dbpath)
        rec1 = KF.commission(
            FakeProvider({"candidates": [_cand("A retrospective opens", ["q"])]}),
            search_fn=lambda q, api_key="": ["https://example.org/shared-anchor"],
            fetch_fn=_fetch_ok, questions=[qa], state_conn=conn1, run_id="proc-1")
        conn1.close()
        check("the first question commissions the shared anchor",
              rec1["status"] == "COMMISSIONED" and
              rec1["seed"]["url"] == "https://example.org/shared-anchor", rec1)

        conn2 = sqlite3.connect(dbpath)
        rec2 = KF.commission(
            FakeProvider({"candidates": [_cand("A different framing of the same show",
                                               ["q2"])]}),
            search_fn=lambda q, api_key="": ["https://example.org/shared-anchor"],
            fetch_fn=_fetch_ok, questions=[qb], state_conn=conn2, run_id="proc-2")
        conn2.close()
        check("a different question cannot recommission the same anchor URL",
              rec2["status"] == "NO_FETCHABLE_ANCHOR" and rec2["seed"] is None, rec2)
        check("the rejected attempt is recorded as an identity collision, not a fetch error",
              any("already commissioned" in (t.get("reason") or "")
                  for t in rec2["tried"]), rec2["tried"])


def test_the_same_quoted_title_is_excluded_even_via_a_different_url():
    with tempfile.TemporaryDirectory() as d:
        dbpath = str(pathlib.Path(d) / "state.db")
        qa, qb = _q("ZZ003-01"), _q("ZZ003-02")
        subject_1 = ("An artist's retrospective 'All Day All Night' gathers two decades "
                    "of work")
        subject_2 = ("A touring survey 'All Day All Night' reframes the same body of work")

        conn1 = sqlite3.connect(dbpath)
        rec1 = KF.commission(
            FakeProvider({"candidates": [_cand(subject_1, ["q"])]}),
            search_fn=lambda q, api_key="": ["https://whitney.example/show"],
            fetch_fn=_fetch_ok, questions=[qa], state_conn=conn1, run_id="proc-1")
        conn1.close()
        check("the first commissioning succeeds", rec1["status"] == "COMMISSIONED", rec1)

        conn2 = sqlite3.connect(dbpath)
        rec2 = KF.commission(
            FakeProvider({"candidates": [_cand(subject_2, ["q2"])]}),
            search_fn=lambda q, api_key="": ["https://walker.example/different-url"],
            fetch_fn=_fetch_ok, questions=[qb], state_conn=conn2, run_id="proc-2")
        conn2.close()
        check("the same quoted title is refused even from a wholly different URL/question",
              rec2["status"] == "NO_FETCHABLE_ANCHOR" and rec2["seed"] is None, rec2)


def test_a_failed_commission_still_consumes_its_claimed_question():
    with tempfile.TemporaryDirectory() as d:
        dbpath = str(pathlib.Path(d) / "state.db")
        q1 = _q("ZZ004-01")
        conn = sqlite3.connect(dbpath)
        rec = KF.commission(Boom(), search_fn=lambda q, api_key="": [], fetch_fn=_fetch_ok,
                            questions=[q1], state_conn=conn, run_id="proc-1")
        check("the commissioning call fails, technically",
              rec["status"] == "COMMISSION_CALL_FAILED", rec.get("status"))
        claimed = KF.load_claimed_question_ids(conn)
        conn.close()
        check("the failed attempt still claimed its question",
              "ZZ004-01" in claimed, claimed)


def test_a_fresh_question_and_a_fresh_story_remain_allowed():
    with tempfile.TemporaryDirectory() as d:
        dbpath = str(pathlib.Path(d) / "state.db")
        conn = sqlite3.connect(dbpath)
        rec = KF.commission(
            FakeProvider({"candidates": [_cand("A wholly new, never-seen story", ["q"])]}),
            search_fn=lambda q, api_key="": ["https://example.org/brand-new"],
            fetch_fn=_fetch_ok, questions=[_q("ZZ005-01")], state_conn=conn, run_id="proc-1")
        conn.close()
        check("a genuinely fresh question and story commissions normally",
              rec["status"] == "COMMISSIONED", rec)


def test_access_origin_question_is_never_selected():
    real_qs = KF.load_questions()
    # PR004-04/06 are held at candidate (never APPROVED_DURABLE), so load_questions() now
    # filters them out on status alone. Keep this direct selector test against synthetic
    # entries so the unconditional access-origin guard stays covered even though its own
    # ids never reach the loadable pool anymore.
    pool = [_q("PR004-04"), _q("PR004-06")]
    check("a pool of ONLY access-origin questions selects nothing",
          KF.select_question(pool, rng=random.Random(1)) is None, pool)
    combined = pool + [q for q in real_qs if q["id"] == "PR004-01"]
    for qid in ("PR004-04", "PR004-06"):
        check("%s is never returned even alongside other questions" % qid,
              all(KF.select_question(combined, rng=random.Random(n))["id"] != qid
                  for n in range(30)), qid)


def test_mediation_authorship_question_is_allowed():
    real_qs = KF.load_questions()
    by_id = {q["id"]: q for q in real_qs}
    for qid in ("PR004-01", "PR004-02"):
        if qid not in by_id:
            check("%s present in the loadable corpus to test against" % qid, False, by_id)
            continue
        picked = KF.select_question([by_id[qid]], rng=random.Random(0))
        check("%s (mediation/authorship territory) is selectable on its own" % qid,
              picked is not None and picked["id"] == qid, picked)


def test_accessibility_evidence_may_exist_inside_an_allowed_commission():
    """The gate filters the QUESTION, never the story's own evidence. A mediation question
    may still surface a candidate whose research trail touches accessibility facts."""
    with tempfile.TemporaryDirectory() as d:
        dbpath = str(pathlib.Path(d) / "state.db")
        q = _q("PR004-02", title="THE MEDIATOR ASSIGNS A REGISTER TO THE MEDIATED",
              question="What qualities of the apparent speaker were actually supplied by "
                       "the mediator?")
        cand = _cand("An interpreter's register choices are compared against the ADA "
                     "accessibility notice for the same venue", ["q"])
        conn = sqlite3.connect(dbpath)
        rec = KF.commission(FakeProvider({"candidates": [cand]}),
                            search_fn=lambda q, api_key="": ["https://example.org/mediator"],
                            fetch_fn=_fetch_ok, questions=[q], state_conn=conn,
                            run_id="proc-1")
        conn.close()
        check("a mediation question with accessibility-flavoured evidence still commissions",
              rec["status"] == "COMMISSIONED", rec)
        check("the accessibility fact rode along as evidence, not as the question",
              "ADA accessibility" in (rec["chosen"]["subject"] or ""), rec.get("chosen"))


def test_retained_commission_artifacts_seed_the_exclusions():
    """A COMMISSION.json left on disk by a run before this table existed (or one this
    process itself never got to persist because it crashed) still claims its question and
    story on the next attempt."""
    with tempfile.TemporaryDirectory() as d:
        dbpath = str(pathlib.Path(d) / "state.db")
        evidence_root = pathlib.Path(d) / "evidence"
        run_dir = evidence_root / "production-retained-run"
        run_dir.mkdir(parents=True)
        (run_dir / "COMMISSION.json").write_text(json.dumps({
            "question": {"id": "ZZ006-01"},
            "chosen": {"subject": "A retained 'Old Story' from a prior process",
                      "anchor_url": "https://example.org/retained"},
        }), encoding="utf-8")

        conn = sqlite3.connect(dbpath)
        seen = KF.seed_exclusions_from_retained(conn, str(evidence_root))
        check("the backfill reads the one retained COMMISSION.json", seen == 1, seen)
        claimed = KF.load_claimed_question_ids(conn)
        check("the retained question id is claimed", "ZZ006-01" in claimed, claimed)
        check("the retained story identity (anchor URL) is claimed",
              KF.is_story_claimed(conn, {"url:%s" % KF.normalize_anchor_url(
                  "https://example.org/retained")}), "")
        check("the retained story identity (quoted title) is claimed",
              KF.is_story_claimed(conn, {"title:old story"}), "")
        conn.close()


def main() -> int:
    for fn in (test_a_claimed_question_is_excluded_by_a_later_process,
               test_a_claimed_anchor_is_not_recommissioned_by_a_different_question,
               test_the_same_quoted_title_is_excluded_even_via_a_different_url,
               test_a_failed_commission_still_consumes_its_claimed_question,
               test_a_fresh_question_and_a_fresh_story_remain_allowed,
               test_access_origin_question_is_never_selected,
               test_mediation_authorship_question_is_allowed,
               test_accessibility_evidence_may_exist_inside_an_allowed_commission,
               test_retained_commission_artifacts_seed_the_exclusions):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL KNOWLEDGE-FIRST EXCLUSION/ACCESS-ORIGIN TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
