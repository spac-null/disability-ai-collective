#!/usr/bin/env python3
"""jev_seed_triage_static_tests.py -- offline tests for the seed triage harness.

NO API KEY. NO NETWORK. NO MODEL CALL. Every test builds its own fixture tree in
a temporary directory, so nothing here reads production data either.

    python3 automation/jev_seed_triage_static_tests.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jev_seed_triage_cases as cases  # noqa: E402
import jev_seed_triage_eval as ev  # noqa: E402


def write(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def make_run(root, run_id, seed_id, title, date, source="Example Wire",
             url="https://example.org/a", research=None, worth=None,
             ledger_facts=0, composition=False, article_final=False,
             run_status="OK", decision="HOLD", provenance_as_string=False):
    run_dir = os.path.join(root, run_id)
    os.makedirs(run_dir, exist_ok=True)
    provenance = {
        "seed_id": seed_id,
        "title": title,
        "url": url,
        "source_name": source,
        "origin": "fetched_article",
    }
    write(
        os.path.join(run_dir, "SOURCE_SNAPSHOT.json"),
        {
            "payload": {
                "provenance": str(provenance) if provenance_as_string else provenance,
                "source_text": "SECRET BODY TEXT THAT MUST NEVER REACH THE MODEL",
                "source_sha256": "deadbeef",
            }
        },
    )
    write(
        os.path.join(run_dir, "MANIFEST.json"),
        {"decision": decision, "run_status": run_status, "reasons": []},
    )
    if research is not None:
        write(
            os.path.join(run_dir, "RESEARCH_PACK.json"),
            {"payload": {"sufficiency": {"verdict": research}, "subject": "narrowed"}},
        )
    if worth is not None:
        write(
            os.path.join(run_dir, "WORTH_AND_CANDIDATE.json"),
            {"worth_gate": {"verdict": worth}, "narrative_yield": {}, "story_candidate": {}},
        )
    if ledger_facts:
        write(
            os.path.join(run_dir, "LEDGER.json"),
            {"F%02d" % i: {"proposition": "x"} for i in range(1, ledger_facts + 1)},
        )
    if composition:
        write(os.path.join(run_dir, "COMPOSITION_RESULT.json"), {"ok": True})
    if article_final:
        with open(os.path.join(run_dir, "ARTICLE_FINAL.md"), "w") as handle:
            handle.write("# final\n")
    return run_dir


class Fixture(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jev-triage-test-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)


# --------------------------------------------------- as-of-seed extraction


class TestExtraction(Fixture):
    def test_builds_one_record_per_distinct_seed(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "A first seed",
                 "20260910", research="NARROW", worth="STRONG_DIRECT_LENS")
        make_run(self.root, "production-20260911T070000Z-b", "seed-1", "A first seed",
                 "20260911", research="NARROW")
        make_run(self.root, "production-20260912T070000Z-c", "seed-2", "A second seed",
                 "20260912", research="HOLD_INSUFFICIENT_RESEARCH")
        cohort = cases.build_cohort_b(self.root)
        self.assertEqual([r["seed_id"] for r in cohort], ["seed-1", "seed-2"])
        self.assertEqual(cohort[0]["outcome"]["runs"], 2)
        self.assertEqual(cohort[0]["first_run"], "production-20260910T070000Z-a")

    def test_reads_provenance_written_as_a_python_literal(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Stringy",
                 "20260910", research="NARROW", provenance_as_string=True)
        cohort = cases.build_cohort_b(self.root)
        self.assertEqual(cohort[0]["title"], "Stringy")

    def test_run_without_provenance_title_is_skipped(self):
        run_dir = make_run(self.root, "production-20260910T070000Z-a", "seed-1", "",
                           "20260910")
        write(os.path.join(run_dir, "SOURCE_SNAPSHOT.json"),
              {"payload": {"provenance": {"seed_id": "seed-1"}}})
        self.assertEqual(cases.build_cohort_b(self.root), [])

    def test_domain_and_date_are_derived(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Seed",
                 "20260910", url="https://www.bbc.co.uk/news/x", research="NARROW")
        record = cases.build_cohort_b(self.root)[0]
        self.assertEqual(record["source_domain"], "bbc.co.uk")
        self.assertEqual(record["state"]["discovery_date"], "2026-09-10")


# ------------------------------------------------------------- no leakage


class TestLeakage(Fixture):
    def test_state_holds_only_allowed_keys(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Seed",
                 "20260910", research="NARROW", worth="STRONG_DIRECT_LENS",
                 ledger_facts=3, composition=True, article_final=True)
        record = cases.build_cohort_b(self.root)[0]
        for key in record["state"]:
            self.assertIn(key, cases.ALLOWED_STATE_KEYS)
        blob = json.dumps(record["state"]).lower()
        for needle in ("strong_direct_lens", "narrow", "worth", "ledger",
                       "publish", "secret body text", "f01"):
            self.assertNotIn(needle, blob)

    def test_outcome_is_held_outside_the_state(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Seed",
                 "20260910", research="NARROW", worth="STRONG_INTERPRETIVE_LENS")
        record = cases.build_cohort_b(self.root)[0]
        self.assertTrue(record["outcome"]["worth_pass"])
        self.assertNotIn("worth_pass", record["state"])

    def test_seed_state_rejects_post_seed_keys(self):
        for bad in ("worth_status", "research_status", "publication_eligible",
                    "engine_decision", "article", "seed_id", "run_id"):
            with self.assertRaises(cases.StateError):
                cases.seed_state({"title": "t", bad: "x"})

    def test_seed_state_rejects_an_unknown_key(self):
        with self.assertRaises(cases.StateError):
            cases.seed_state({"title": "t", "vibes": "good"})

    def test_state_requires_title_or_snippet(self):
        with self.assertRaises(cases.StateError):
            cases.seed_state({"source": "Wire"})

    def test_state_is_bounded(self):
        state = cases.seed_state({"title": "x" * 5000})
        self.assertLessEqual(len(state["title"]), cases.MAX_TITLE_CHARS)
        with self.assertRaises(cases.StateError):
            cases.seed_state({"title": "t", "snippet": "y" * 900,
                              "discovery_context": "z" * 900,
                              "source": "s" * 3000})

    def test_no_filesystem_paths_in_state(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Seed",
                 "20260910", research="NARROW")
        record = cases.build_cohort_b(self.root)[0]
        self.assertNotIn("/srv/", json.dumps(record["state"]))

    def test_request_carries_only_state_and_preamble(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Seed",
                 "20260910", research="NARROW", worth="STRONG_DIRECT_LENS")
        case = cases.build_cohort_b(self.root)[0]
        payload = ev.build_request(case)
        self.assertEqual(payload["model"], "typesafe/jev-1.13")
        extra = set(payload["state"]) - set(cases.ALLOWED_STATE_KEYS) - {"preamble"}
        self.assertEqual(extra, set())
        blob = json.dumps(payload).lower()
        self.assertNotIn("strong_direct_lens", blob)
        self.assertNotIn("seed-1", blob)

    def test_request_never_carries_the_api_key(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Seed",
                 "20260910", research="NARROW")
        case = cases.build_cohort_b(self.root)[0]
        self.assertNotIn("sk-", json.dumps(ev.build_request(case)))
        self.assertEqual(ev._scrub("token sk-abc leaked", "sk-abc"),
                         "token <redacted> leaked")


# ------------------------------------------------------------ question set


class TestQuestions(unittest.TestCase):
    def test_every_scored_signal_has_a_question(self):
        for name in cases.POSITIVE_SIGNALS + cases.NEGATIVE_SIGNALS:
            self.assertIn(name, ev.NOUL_QUESTIONS)
        self.assertIn("local_language_search_may_help", ev.NOUL_QUESTIONS)

    def test_lane_question_is_a_choice_with_three_options(self):
        payload = ev.build_request(
            {"state": cases.seed_state({"title": "t"}), "cohort": "B"}
        )
        lane = payload["questions"]["initial_lane"]
        self.assertEqual(lane["type"], "choice")
        self.assertEqual(set(lane["criteria"]), set(cases.LANE_OPTIONS))

    def test_no_verdict_question_is_asked(self):
        text = json.dumps(ev.NOUL_QUESTIONS).lower() + json.dumps(ev.LANE_CRITERIA).lower()
        for banned in ("worth publishing", "pass worth", "should this candidate be "
                       "rejected", "is the claim true", "good crip minds story"):
            self.assertNotIn(banned, text)

    def test_every_question_has_explicit_instructions(self):
        payload = ev.build_request(
            {"state": cases.seed_state({"title": "t"}), "cohort": "B"}
        )
        for name, question in payload["questions"].items():
            self.assertTrue(question["instructions"].strip(), name)


# ----------------------------------------------------------------- scoring


class TestScoring(unittest.TestCase):
    def probabilities(self, value, negative=None):
        out = {name: value for name in cases.POSITIVE_SIGNALS}
        out["generic_commentary_risk"] = value if negative is None else negative
        out["local_language_search_may_help"] = 0.9
        return out

    def test_all_components_have_equal_weight(self):
        base = self.probabilities(0.5, negative=0.5)
        baseline = cases.triage_score(base)
        for name in cases.POSITIVE_SIGNALS:
            bumped = dict(base)
            bumped[name] = 1.0
            self.assertAlmostEqual(cases.triage_score(bumped) - baseline, 0.5 / 8)
        bumped = dict(base)
        bumped["generic_commentary_risk"] = 0.0
        self.assertAlmostEqual(cases.triage_score(bumped) - baseline, 0.5 / 8)

    def test_negative_signal_is_inverted(self):
        high_risk = cases.triage_score(self.probabilities(0.8, negative=1.0))
        low_risk = cases.triage_score(self.probabilities(0.8, negative=0.0))
        self.assertGreater(low_risk, high_risk)

    def test_positive_mean_ignores_the_negative_signal(self):
        self.assertAlmostEqual(
            cases.positive_mean(self.probabilities(0.4, negative=1.0)), 0.4
        )

    def test_exploratory_signal_does_not_enter_the_score(self):
        a = self.probabilities(0.6)
        b = dict(a)
        b["local_language_search_may_help"] = 0.0
        self.assertEqual(cases.triage_score(a), cases.triage_score(b))

    def test_score_bounds(self):
        self.assertAlmostEqual(cases.triage_score(self.probabilities(1.0, 0.0)), 1.0)
        self.assertAlmostEqual(cases.triage_score(self.probabilities(0.0, 1.0)), 0.0)

    def test_ranking_is_deterministic(self):
        records = [
            {"case_id": "c%d" % i, "triage_score": s}
            for i, s in enumerate([0.4, 0.9, 0.4, 0.1])
        ]
        first = [r["case_id"] for r in sorted(records, key=lambda r: -r["triage_score"])]
        second = [r["case_id"] for r in sorted(records, key=lambda r: -r["triage_score"])]
        self.assertEqual(first, second)

    def test_simulated_groups_are_reproducible(self):
        cohort = [{"case_id": "c%02d" % i} for i in range(12)]
        a = cases.simulated_groups(cohort)
        b = cases.simulated_groups(cohort)
        self.assertEqual(
            [[m["case_id"] for m in g["members"]] for g in a],
            [[m["case_id"] for m in g["members"]] for g in b],
        )


# ---------------------------------------------------------------- outcomes


class TestOutcomes(Fixture):
    def test_worth_research_and_ledger_extraction(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Seed one",
                 "20260910", research="NARROW", worth="STRONG_INTERPRETIVE_LENS",
                 ledger_facts=40, composition=True)
        make_run(self.root, "production-20260910T080000Z-b", "seed-2", "Seed two",
                 "20260910", research="HOLD_INSUFFICIENT_RESEARCH")
        cohort = {r["seed_id"]: r["outcome"] for r in cases.build_cohort_b(self.root)}
        self.assertTrue(cohort["seed-1"]["worth_pass"])
        self.assertTrue(cohort["seed-1"]["research_pass"])
        self.assertTrue(cohort["seed-1"]["ledger_pass"])
        self.assertEqual(cohort["seed-1"]["terminal_stage"], "COMPOSITION")
        self.assertFalse(cohort["seed-2"]["worth_pass"])
        self.assertFalse(cohort["seed-2"]["research_pass"])
        self.assertEqual(cohort["seed-2"]["terminal_stage"], "RESEARCH_HOLD")

    def test_research_hold_still_counts_as_worth_non_pass_with_stage_kept(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Seed",
                 "20260910", research="HOLD_INSUFFICIENT_RESEARCH")
        outcome = cases.build_cohort_b(self.root)[0]["outcome"]
        self.assertFalse(outcome["worth_pass"])
        self.assertEqual(outcome["terminal_stage"], "RESEARCH_HOLD")

    def test_stage_that_did_not_exist_yet_is_unevaluable_not_a_failure(self):
        make_run(self.root, "production-20260826T070000Z-a", "seed-old", "Old seed",
                 "20260826", decision="ACCEPT")
        outcome = cases.build_cohort_b(self.root)[0]["outcome"]
        self.assertFalse(outcome["worth_evaluable"])
        self.assertFalse(outcome["research_evaluable"])
        self.assertFalse(outcome["ledger_evaluable"])
        self.assertEqual(cases.worth_evaluable(cases.build_cohort_b(self.root)), [])

    def test_provider_failure_only_seeds_are_excluded(self):
        make_run(self.root, "production-20260918T070000Z-a", "seed-x", "Seed",
                 "20260918", run_status="PROVIDER_FAILURE")
        cohort = cases.build_cohort_b(self.root)
        self.assertTrue(cohort[0]["outcome"]["all_provider_failure"])
        self.assertEqual(cases.worth_evaluable(cohort), [])

    def test_outcome_is_the_best_reached_across_reruns(self):
        make_run(self.root, "production-20260910T070000Z-a", "seed-1", "Seed",
                 "20260910", research="HOLD_INSUFFICIENT_RESEARCH")
        make_run(self.root, "production-20260911T070000Z-b", "seed-1", "Seed",
                 "20260911", research="NARROW", worth="STRONG_DIRECT_LENS")
        outcome = cases.build_cohort_b(self.root)[0]["outcome"]
        self.assertTrue(outcome["worth_pass"])
        self.assertEqual(outcome["runs"], 2)


# ------------------------------------------------------------ desk / daily


class TestDaily(Fixture):
    def day_file(self, name, attempts):
        write(
            os.path.join(self.root, name, "COMMISSIONING_DAY.json"),
            {"attempts": attempts},
        )

    def test_desk_day_attempt_order_is_preserved(self):
        self.day_file(
            "commissioning-20260916T070004Z",
            [
                {"attempt": 2, "seed_id": "s2", "worth_verdict": "PASS"},
                {"attempt": 1, "seed_id": "s1", "worth_verdict": ""},
            ],
        )
        days = cases.desk_days(self.root)
        self.assertEqual([a["seed_id"] for a in days[0]["attempts"]], ["s1", "s2"])
        self.assertEqual([a["worth_pass"] for a in days[0]["attempts"]], [False, True])

    def test_attempt_without_seed_id_is_dropped(self):
        self.day_file("commissioning-20260915T070004Z",
                      [{"attempt": 1, "seed_id": None, "worth_verdict": ""}])
        self.assertEqual(cases.desk_days(self.root), [])

    def test_calendar_days_group_and_bound(self):
        for i in range(3):
            make_run(self.root, "production-20260910T07000%dZ-%d" % (i, i),
                     "seed-%d" % i, "Seed %d" % i, "20260910", research="NARROW")
        make_run(self.root, "production-20260911T070000Z-x", "seed-x", "Seed x",
                 "20260911", research="NARROW")
        cohort = cases.build_cohort_b(self.root)
        days = cases.calendar_days(cohort)
        self.assertEqual([d["day"] for d in days], ["20260910"])
        self.assertEqual(len(days[0]["members"]), 3)
        self.assertEqual(cases.calendar_days(cohort, min_size=2, max_size=2), [])

    def test_top1_and_top2_metrics(self):
        groups = [
            [(0.9, True), (0.5, False), (0.1, False)],
            [(0.9, False), (0.5, True), (0.1, False)],
            [(0.9, False), (0.5, False), (0.1, True)],
            [(0.9, False), (0.5, False), (0.1, False)],
        ]
        metrics = cases.rank_metrics(groups)
        self.assertEqual(metrics["days"], 3)
        self.assertEqual(metrics["top1_hits"], 1)
        self.assertEqual(metrics["top2_hits"], 2)
        self.assertAlmostEqual(metrics["mean_rank_first_pass"], 2.0)
        self.assertAlmostEqual(metrics["random_top1_rate"], 1.0 / 3)
        self.assertAlmostEqual(metrics["random_mean_rank_first_pass"], 2.0)

    def test_counterfactual_attempt_order(self):
        self.assertEqual(cases.attempts_to_first_pass([False, True, False]), 2)
        self.assertEqual(cases.attempts_to_first_pass([True]), 1)
        self.assertIsNone(cases.attempts_to_first_pass([False, False]))

    def test_auc_matches_hand_computation(self):
        self.assertEqual(cases.auc([0.9, 0.8, 0.2], [True, False, False]), 1.0)
        self.assertEqual(cases.auc([0.2, 0.8, 0.9], [True, False, False]), 0.0)
        self.assertEqual(cases.auc([0.5, 0.5], [True, False]), 0.5)
        self.assertIsNone(cases.auc([0.5, 0.6], [True, True]))

    def test_describe_and_overlap(self):
        stats = cases.describe([0.2, 0.4, 0.6])
        self.assertAlmostEqual(stats["median"], 0.4)
        self.assertEqual(stats["n"], 3)
        self.assertIn("disjoint", cases.overlap_description([0.9], [0.1]))
        self.assertIn("shared band", cases.overlap_description([0.9, 0.2], [0.5]))


# ---------------------------------------------------------------- cohort A


class TestCohortA(Fixture):
    def pool(self, run_id, chosen_index=0, n=4):
        candidates = []
        for i in range(n):
            candidates.append(
                {
                    "subject": "Candidate subject number %d about a specific thing" % i,
                    "why_now": "because something happened %d" % i,
                    "carrier": "DESK REASONING THAT MUST NOT REACH THE MODEL",
                    "tests_the_question": "DESK REASONING",
                    "search_queries": ["DESK QUERY"],
                    "names_to_research": ["DESK NAME"],
                    "source_language": "German" if i == 1 else "English",
                    "country": "Germany" if i == 1 else "United States",
                }
            )
        write(
            os.path.join(self.root, run_id, "COMMISSION.json"),
            {
                "candidates": candidates,
                "chosen": {"subject": candidates[chosen_index]["subject"]},
                "lane": "KNOWLEDGE_FIRST",
                "status": "COMMISSIONED",
                "seed": {"title": candidates[chosen_index]["subject"]},
            },
        )

    def test_pool_has_exactly_one_selected_candidate(self):
        self.pool("production-20260916T070000Z-a", chosen_index=2)
        pools = cases.build_cohort_a(self.root)
        selected = [c for c in pools[0]["candidates"] if c["selected"]]
        self.assertEqual(len(selected), 1)
        self.assertEqual(len(pools[0]["candidates"]), 4)

    def test_unselected_candidates_are_not_labelled_failures(self):
        self.pool("production-20260916T070000Z-a")
        for candidate in cases.build_cohort_a(self.root)[0]["candidates"]:
            self.assertNotIn("worth_pass", candidate)
            self.assertNotIn("failed", json.dumps(candidate).lower())
            self.assertIn("selected", candidate)

    def test_desk_reasoning_is_stripped_from_the_state(self):
        self.pool("production-20260916T070000Z-a")
        for candidate in cases.build_cohort_a(self.root)[0]["candidates"]:
            blob = json.dumps(candidate["state"])
            self.assertNotIn("DESK REASONING", blob)
            self.assertNotIn("DESK QUERY", blob)
            self.assertNotIn("DESK NAME", blob)
            for key in candidate["state"]:
                self.assertIn(key, cases.ALLOWED_STATE_KEYS)

    def test_selection_agreement_is_not_called_accuracy(self):
        self.pool("production-20260916T070000Z-a", chosen_index=0)
        candidates = cases.build_cohort_a(self.root)[0]["candidates"]
        results = []
        for index, candidate in enumerate(candidates):
            record = dict(candidate)
            record.update(
                {
                    "status": "OK",
                    "triage_score": 1.0 - index * 0.1,
                    "initial_lane": "KNOWLEDGE_FIRST",
                    "probabilities": {"local_language_search_may_help": 0.1},
                }
            )
            results.append(record)
        summary = ev.analyse_cohort_a(results)
        self.assertEqual(summary["selection_agreement_top1"], 1.0)
        self.assertNotIn("accuracy", json.dumps(summary).lower())
        self.assertAlmostEqual(summary["selection_agreement_random"], 0.25)


# ------------------------------------------------- responses and hardening


class TestResponses(unittest.TestCase):
    def good(self):
        answers = {
            name: {"type": "noul", "noul": 0.5} for name in ev.ALL_NOUL
        }
        answers["initial_lane"] = {
            "type": "choice",
            "choice": "KNOWLEDGE_FIRST",
            "confidence": 0.7,
        }
        return {"model": "typesafe/jev-1.13", "answers": answers, "usage": {"cost": 0.0001}}

    def test_valid_response_parses(self):
        parsed = ev.validate_response(self.good())
        self.assertEqual(parsed["initial_lane"], "KNOWLEDGE_FIRST")
        self.assertAlmostEqual(cases.triage_score(parsed["probabilities"]), 0.5)

    def test_malformed_responses_raise(self):
        self.assertRaises(ev.ValidationError, ev.validate_response, None)
        self.assertRaises(ev.ValidationError, ev.validate_response, {"answers": []})
        missing = self.good()
        del missing["answers"]["concrete_carrier"]
        self.assertRaises(ev.ValidationError, ev.validate_response, missing)
        out_of_range = self.good()
        out_of_range["answers"]["concrete_carrier"]["noul"] = 1.4
        self.assertRaises(ev.ValidationError, ev.validate_response, out_of_range)
        wrong_type = self.good()
        wrong_type["answers"]["concrete_carrier"] = {"type": "choice", "choice": "x"}
        self.assertRaises(ev.ValidationError, ev.validate_response, wrong_type)
        bad_lane = self.good()
        bad_lane["answers"]["initial_lane"]["choice"] = "PINA"
        self.assertRaises(ev.ValidationError, ev.validate_response, bad_lane)
        boolean = self.good()
        boolean["answers"]["concrete_carrier"]["noul"] = True
        self.assertRaises(ev.ValidationError, ev.validate_response, boolean)

    def test_a_schema_error_does_not_stop_the_run(self):
        case = {
            "case_id": "B:x",
            "cohort": "B",
            "seed_id": "x",
            "date": "20260910",
            "state": cases.seed_state({"title": "t"}),
            "state_fingerprint": "abc",
            "outcome": {"worth_pass": False, "worth_evaluable": True,
                        "all_provider_failure": False},
            "source_name": "Wire",
            "source_domain": "example.org",
        }
        results = ev.evaluate([case], live=False, api_key="")
        self.assertEqual(results[0]["status"], "DRY_RUN")
        self.assertGreater(results[0]["request_bytes"], 0)


class TestResultStorage(unittest.TestCase):
    def test_result_root_is_outside_the_repository(self):
        repo = os.path.dirname(os.path.dirname(os.path.abspath(ev.__file__)))
        self.assertFalse(os.path.abspath(ev.RESULT_ROOT).startswith(repo + os.sep))
        self.assertTrue(ev.RESULT_ROOT.startswith("/srv/data/"))

    def test_results_are_written_private(self):
        tmp = tempfile.mkdtemp(prefix="jev-triage-out-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        original = ev.RESULT_ROOT
        ev.RESULT_ROOT = tmp
        try:
            path = ev.write_results({"results": []}, "unit")
        finally:
            ev.RESULT_ROOT = original
        self.assertEqual(oct(os.stat(path).st_mode)[-3:], "600")

    def test_model_is_pinned_and_not_latest(self):
        self.assertEqual(ev.JEV_MODEL, "typesafe/jev-1.13")
        self.assertNotIn("latest", ev.JEV_MODEL)


class TestNoProductionContact(unittest.TestCase):
    def test_harness_imports_no_production_stage(self):
        here = os.path.dirname(os.path.abspath(__file__))
        for name in ("jev_seed_triage_cases.py", "jev_seed_triage_eval.py"):
            with open(os.path.join(here, name), "r", encoding="utf-8") as handle:
                text = handle.read()
            for banned in ("import new_engine_v1", "from new_engine_v1",
                           "import commissioning_desk", "import selector_v2",
                           "import knowledge_first", "import crip_minds_screen",
                           "import news_fetcher"):
                self.assertNotIn(banned, text, "%s: %s" % (name, banned))

    def test_no_perspective_metadata_is_produced(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "jev_seed_triage_eval.py"), "r",
                  encoding="utf-8") as handle:
            text = handle.read().upper()
        for banned in ("PINA", "MIRA", "SIIRI", "ZENO"):
            self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
