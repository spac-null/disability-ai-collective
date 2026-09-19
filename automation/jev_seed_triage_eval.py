#!/usr/bin/env python3
"""jev_seed_triage_eval.py -- can a cheap model recognise useful early seed properties?

EXPERIMENTAL / SHADOW ONLY. Jev has ZERO authority over discovery, inclusion,
rejection, commissioning, Research, the Ledger, Worth or publication. This
harness imports no production stage, calls none, and changes nothing. It reads
retained artifacts read-only, asks a pinned model several small questions about
information visible BEFORE Research, and writes results outside the repository.

  python3 automation/jev_seed_triage_eval.py --audit
  python3 automation/jev_seed_triage_eval.py --cohort b --dry-run
  python3 automation/jev_seed_triage_eval.py --cohort b --live
  python3 automation/jev_seed_triage_eval.py --cohort a --live
  python3 automation/jev_seed_triage_eval.py --report <results.json>

The score is fixed before any result is seen: eight equally weighted components,
no threshold, ranking only. Nothing here is tuned after looking at outcomes.

WHAT THE FIRST LIVE RUN (2026-09-19, 165 seeds, 88 pool candidates) EXPOSED.

  1. THE COMPOSITE SCORE DOES NOT ORDER CANDIDATES BY WORTH. AUC 0.528 over 143
     Worth-evaluable seeds, permutation p=0.57; within the news-seed stratum
     alone 0.486, p=0.78. The small apparent lift is an artifact of how much
     text the retained snapshot carries: triage_score correlates 0.79 with
     title length, and a title-length baseline reproduces the score's ranking
     on simulated triples. Knowledge-first seeds kept a 300-character summary
     as their title and scored 0.83; news seeds kept a headline and scored
     0.52. That is a property of the archive, not of the seeds.

  2. ONE QUESTION CARRIED REAL SIGNAL, AND IT WAS NOT THE ONE NAMED AFTER
     RESEARCH. concrete_human_or_material_stakes reached AUC 0.728 against
     RESEARCH_PASS within the news stratum (p=0.0008) and 0.670 against Worth
     there (p=0.0008). researchable_mechanism ran the wrong way (0.41 against
     research, 0.27 against the Ledger), and generic_commentary_risk also ran
     the wrong way, so the fixed score subtracts a component that should have
     been added. The composite dilutes the one signal that worked.

  3. WITHIN A POOL OF LIKE-SHAPED CANDIDATES THE RANKING AGREES WITH THE DESK.
     On the 22 retained four-candidate pools the top-ranked candidate was the
     one the desk chose 11 times (random 0.25, P(X>=11)=0.010), mean rank of
     the chosen candidate 1.64 of 4. Agreement with a human-designed selector,
     not accuracy against an outcome.

Read these as a reason to test one signal against one gate next, not as a
reason to let anything here order production candidates.
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import os
import stat
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jev_seed_triage_cases as cases  # noqa: E402

JEV_MODEL = "typesafe/jev-1.13"
JEV_ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
RESULT_ROOT = os.environ.get(
    "JEV_SEED_TRIAGE_RESULT_ROOT",
    "/srv/data/cripminds-new-engine-v1/experiments/jev-seed-triage",
)

PREAMBLE = (
    "The state describes a story seed exactly as it looked before any research "
    "was done: what was discovered, where it came from, and when. Answer each "
    "question about the seed alone. Do not judge whether the seed should be "
    "published, whether it is a good story, or whether any claim in it is true."
)

NOUL_QUESTIONS = {
    "concrete_carrier": (
        "Does the seed contain a specific person, object, institution, place, "
        "document, event, work, system, or other concrete thing capable of "
        "carrying a reported story? TRUE if a reader could follow something "
        "specific through the piece. FALSE if the seed is primarily an "
        "abstract topic, a broad theme or a generalised issue."
    ),
    "specific_event_or_change": (
        "Does the seed identify a specific action, change, decision, event, "
        "discovery, conflict, release, ruling, opening, closure, policy "
        "implementation or object, rather than merely a standing topic?"
    ),
    "researchable_mechanism": (
        "Does the seed point toward a concrete mechanism or process that can "
        "be investigated -- how an institution decides, how a system "
        "classifies, how infrastructure works, how participation is "
        "structured, how a policy is implemented, how an object or practice "
        "produces an effect? FALSE if only a broad topic or opinion is visible."
    ),
    "specific_tension_or_contradiction": (
        "Does the seed contain a concrete mismatch, tension, contradiction, "
        "dependency, tradeoff or surprising relationship that could plausibly "
        "carry reader momentum? This does not require conflict between people."
    ),
    "evidence_path_visible": (
        "Does the seed itself suggest a plausible path toward sourceable "
        "evidence -- a named institution, report, paper, artwork, court "
        "ruling, policy, document, a named person with an attributable record, "
        "or a specific event with traceable reporting? This is not asking "
        "whether evidence ultimately exists, only whether the seed exposes a "
        "concrete research path."
    ),
    "generic_commentary_risk": (
        "Is this primarily generic commentary, awareness language, broad trend "
        "description, opinion, promotional framing or abstract discussion, "
        "without enough specificity for a concrete story?"
    ),
    "ordinary_world_question_present": (
        "Does the seed contain a question about culture, science, technology, "
        "institutions or ordinary life whose interest survives beyond simply "
        "saying that this concerns disability? TRUE if there is a mechanism, "
        "assumption or world question to investigate. FALSE if the apparent "
        "editorial value is mainly that disability is mentioned. Disability "
        "does not have to be absent for this to be TRUE."
    ),
    "concrete_human_or_material_stakes": (
        "Does the seed make visible a concrete consequence for people, bodies, "
        "participation, access, perception, communication, time, money, space, "
        "infrastructure or institutional treatment? Do not ask whether the "
        "consequence is morally important -- only whether it is concrete."
    ),
    "local_language_search_may_help": (
        "EXPLORATORY ROUTING SUGGESTION ONLY. Would investigating this subject "
        "plausibly benefit from searching in a language associated with the "
        "subject, institution or place, rather than relying only on "
        "English-language material?"
    ),
}

LANE_CRITERIA = {
    "KNOWLEDGE_FIRST": (
        "The interesting starting point appears to require specialist or "
        "disability-rooted knowledge to formulate a sharper question."
    ),
    "ORDINARY_WORLD_COLLISION": (
        "The seed begins with a concrete ordinary-world event, object, "
        "institution or process where a disability-rooted question may expose "
        "an assumption."
    ),
    "UNCLEAR": "The seed does not cleanly suggest one initial route.",
}

SCORED_NOUL = tuple(cases.POSITIVE_SIGNALS) + tuple(cases.NEGATIVE_SIGNALS)
ALL_NOUL = SCORED_NOUL + tuple(cases.EXPLORATORY_NOUL)


# --------------------------------------------------------------- transport


def load_api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    try:
        from orchestrator.config import OPENROUTER_API_KEY as key  # noqa: N813
    except Exception:  # noqa: BLE001
        return ""
    return key or ""


def build_request(case):
    state = dict(case["state"])
    cases.assert_no_leakage(state)
    state["preamble"] = PREAMBLE
    questions = {
        name: {"type": "noul", "instructions": text}
        for name, text in NOUL_QUESTIONS.items()
    }
    questions["initial_lane"] = {
        "type": "choice",
        "instructions": (
            "EXPLORATORY ROUTING SUGGESTION ONLY, with no authority over "
            "perspective or lane. Which initial route does the seed suggest?"
        ),
        "criteria": dict(LANE_CRITERIA),
    }
    return {"model": JEV_MODEL, "state": state, "questions": questions}


def _scrub(text, api_key):
    if api_key and api_key in text:
        text = text.replace(api_key, "<redacted>")
    return text


def call_jev(payload, api_key, timeout=120):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        JEV_ENDPOINT,
        data=body,
        headers={
            "Authorization": "Bearer %s" % api_key,
            "Content-Type": "application/json",
        },
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return raw, int((time.time() - started) * 1000), None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        return None, int((time.time() - started) * 1000), "HTTP_%s: %s" % (
            exc.code,
            _scrub(detail, api_key),
        )
    except Exception as exc:  # noqa: BLE001
        return None, int((time.time() - started) * 1000), "%s: %s" % (
            type(exc).__name__,
            _scrub(str(exc)[:300], api_key),
        )


# -------------------------------------------------------------- validation


class ValidationError(ValueError):
    pass


def _num_0_1(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("%s is not numeric: %r" % (label, value))
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValidationError("%s out of range 0..1: %r" % (label, value))
    return value


def validate_response(raw):
    if not isinstance(raw, dict):
        raise ValidationError("response is not an object")
    answers = raw.get("answers")
    if not isinstance(answers, dict):
        raise ValidationError("missing answers object")
    missing = [q for q in list(ALL_NOUL) + ["initial_lane"] if q not in answers]
    if missing:
        raise ValidationError("missing answers: %s" % ",".join(sorted(missing)))

    probabilities = {}
    for name in ALL_NOUL:
        answer = answers[name]
        if not isinstance(answer, dict) or answer.get("type") != "noul":
            raise ValidationError("%s is not a noul answer" % name)
        probabilities[name] = _num_0_1(answer.get("noul"), name)

    lane = answers["initial_lane"]
    if not isinstance(lane, dict) or lane.get("type") != "choice":
        raise ValidationError("initial_lane is not a choice answer")
    if lane.get("choice") not in cases.LANE_OPTIONS:
        raise ValidationError("initial_lane %r outside options" % lane.get("choice"))
    confidence = lane.get("confidence")
    if confidence is not None:
        confidence = _num_0_1(confidence, "initial_lane confidence")

    usage = raw.get("usage") or {}
    return {
        "probabilities": probabilities,
        "initial_lane": lane.get("choice"),
        "initial_lane_confidence": confidence,
        "resolved_model": raw.get("model"),
        "provider": raw.get("provider"),
        "generation_id": raw.get("id"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "reported_cost_usd": usage.get("cost"),
    }


# ------------------------------------------------------------------ runner


def evaluate(case_list, live, api_key, timeout=120):
    results = []
    for case in case_list:
        record = {
            "case_id": case["case_id"],
            "cohort": case["cohort"],
            "date": case.get("date"),
            "state": case["state"],
            "state_fingerprint": case["state_fingerprint"],
            "requested_model": JEV_MODEL,
            "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        }
        if case["cohort"] == "B":
            record["seed_id"] = case["seed_id"]
            record["outcome"] = case["outcome"]
            record["source_name"] = case["source_name"]
            record["source_domain"] = case["source_domain"]
        else:
            record["pool"] = case["pool"]
            record["selected"] = case["selected"]
            record["source_language"] = case.get("source_language")
            record["subject_country"] = case.get("subject_country")
            record["world_region"] = case.get("world_region")
            record["historical_lane"] = case.get("lane")

        payload = build_request(case)
        if not live:
            record["status"] = "DRY_RUN"
            record["request_bytes"] = len(json.dumps(payload).encode("utf-8"))
            results.append(record)
            continue

        raw, latency_ms, error = call_jev(payload, api_key, timeout)
        record["latency_ms"] = latency_ms
        if error:
            record["status"] = "TRANSPORT_ERROR"
            record["error"] = error
            results.append(record)
            continue
        try:
            parsed = validate_response(raw)
        except ValidationError as exc:
            record["status"] = "SCHEMA_ERROR"
            record["error"] = str(exc)
            results.append(record)
            continue
        record["status"] = "OK"
        record.update(parsed)
        record["positive_mean"] = cases.positive_mean(parsed["probabilities"])
        record["triage_score"] = cases.triage_score(parsed["probabilities"])
        results.append(record)
    return results


# ------------------------------------------------------------------ report


def _scored(results):
    return [r for r in results if r.get("status") == "OK"]


def analyse_cohort_b(results):
    ok = [r for r in _scored(results) if r["cohort"] == "B"]
    evaluable = [r for r in ok if r["outcome"]["worth_evaluable"]
                 and not r["outcome"]["all_provider_failure"]]
    report = {
        "scored": len(ok),
        "worth_evaluable": len(evaluable),
    }

    def gate(name, subset_key):
        subset = [r for r in ok if r["outcome"].get(subset_key)
                  and not r["outcome"]["all_provider_failure"]]
        scores = [r["triage_score"] for r in subset]
        labels = [bool(r["outcome"][name]) for r in subset]
        yes = [s for s, y in zip(scores, labels) if y]
        no = [s for s, y in zip(scores, labels) if not y]
        return {
            "n": len(subset),
            "pass": len(yes),
            "non_pass": len(no),
            "auc": cases.auc(scores, labels),
            "pass_stats": cases.describe(yes),
            "non_pass_stats": cases.describe(no),
            "overlap": cases.overlap_description(yes, no),
        }

    report["worth"] = gate("worth_pass", "worth_evaluable")
    report["research"] = gate("research_pass", "research_evaluable")
    report["ledger"] = gate("ledger_pass", "ledger_evaluable")

    signals = {}
    scores = [r["triage_score"] for r in evaluable]
    labels = [bool(r["outcome"]["worth_pass"]) for r in evaluable]
    for name in ALL_NOUL:
        values = [r["probabilities"][name] for r in evaluable]
        signals[name] = {
            "auc_vs_worth": cases.auc(values, labels),
            "mean_pass": cases.describe(
                [v for v, y in zip(values, labels) if y]
            ).get("mean"),
            "mean_non_pass": cases.describe(
                [v for v, y in zip(values, labels) if not y]
            ).get("mean"),
        }
    report["signals"] = signals
    report["triage_score_auc_check"] = cases.auc(scores, labels)
    report["lane_distribution"] = collections.Counter(
        r["initial_lane"] for r in ok
    )
    report["local_language_true_rate"] = (
        sum(1 for r in ok if r["probabilities"]["local_language_search_may_help"] >= 0.5)
        / float(len(ok))
        if ok
        else None
    )
    return report


def daily_analysis(results, engine_root=None):
    ok = {r["seed_id"]: r for r in _scored(results) if r["cohort"] == "B"}
    out = {}

    desk = cases.desk_days(engine_root)
    desk_groups = []
    desk_actual = []
    desk_jev = []
    for day in desk:
        members = []
        for attempt in day["attempts"]:
            record = ok.get(attempt["seed_id"])
            if record is None:
                continue
            members.append((record["triage_score"], attempt["worth_pass"], attempt))
        if len(members) < 2:
            continue
        desk_groups.append([(m[0], m[1]) for m in members])
        actual_order = [m[1] for m in members]
        jev_order = [m[1] for m in sorted(members, key=lambda m: -m[0])]
        if any(actual_order):
            desk_actual.append(cases.attempts_to_first_pass(actual_order))
            desk_jev.append(cases.attempts_to_first_pass(jev_order))
    out["desk_days_total"] = len(desk)
    out["desk_days_multi_pitch"] = len(desk_groups)
    out["desk_rank"] = cases.rank_metrics(desk_groups)
    out["desk_actual_attempts_to_first_pass"] = (
        sum(desk_actual) / float(len(desk_actual)) if desk_actual else None
    )
    out["desk_jev_attempts_to_first_pass"] = (
        sum(desk_jev) / float(len(desk_jev)) if desk_jev else None
    )

    cohort = [r for r in _scored(results) if r["cohort"] == "B"
              and r["outcome"]["worth_evaluable"]
              and not r["outcome"]["all_provider_failure"]]
    by_date = collections.defaultdict(list)
    for record in cohort:
        by_date[record["date"]].append(record)
    proxy_groups = []
    proxy_actual = []
    proxy_jev = []
    for date in sorted(by_date):
        members = sorted(by_date[date], key=lambda r: r["case_id"])
        if not 2 <= len(members) <= 8:
            continue
        pairs = [(m["triage_score"], bool(m["outcome"]["worth_pass"])) for m in members]
        proxy_groups.append(pairs)
        actual_order = [y for _, y in pairs]
        jev_order = [y for _, y in sorted(pairs, key=lambda p: -p[0])]
        if any(actual_order):
            proxy_actual.append(cases.attempts_to_first_pass(actual_order))
            proxy_jev.append(cases.attempts_to_first_pass(jev_order))
    out["proxy_days"] = len(proxy_groups)
    out["proxy_rank"] = cases.rank_metrics(proxy_groups)
    out["proxy_actual_attempts_to_first_pass"] = (
        sum(proxy_actual) / float(len(proxy_actual)) if proxy_actual else None
    )
    out["proxy_jev_attempts_to_first_pass"] = (
        sum(proxy_jev) / float(len(proxy_jev)) if proxy_jev else None
    )

    simulated = cases.simulated_groups(cohort, size=3)
    sim_groups = [
        [(m["triage_score"], bool(m["outcome"]["worth_pass"])) for m in group["members"]]
        for group in simulated
    ]
    out["simulated_triples"] = len(sim_groups)
    out["simulated_rank"] = cases.rank_metrics(sim_groups)

    length_groups = [
        [(float(len(m["state"].get("title", ""))), bool(m["outcome"]["worth_pass"]))
         for m in group["members"]]
        for group in simulated
    ]
    out["simulated_rank_title_length_baseline"] = cases.rank_metrics(length_groups)
    scores = [float(len(r["state"].get("title", ""))) for r in cohort]
    labels = [bool(r["outcome"]["worth_pass"]) for r in cohort]
    out["title_length_auc_vs_worth"] = cases.auc(scores, labels)
    return out


def diversity_check(results, top_fraction=0.25):
    ok = [r for r in _scored(results) if r["cohort"] == "B"]
    if not ok:
        return {}
    ordered = sorted(ok, key=lambda r: -r["triage_score"])
    cut = max(1, int(len(ordered) * top_fraction))
    top = ordered[:cut]

    def distribution(records, key):
        counter = collections.Counter(records_key(r, key) for r in records)
        total = float(len(records))
        return {k: (v, v / total) for k, v in counter.most_common(8)}

    def records_key(record, key):
        if key == "lane":
            return record.get("initial_lane")
        return record.get(key) or "unknown"

    return {
        "top_n": len(top),
        "overall_n": len(ordered),
        "top_source": distribution(top, "source_name"),
        "overall_source": distribution(ordered, "source_name"),
        "top_domain_tld": collections.Counter(
            (r.get("source_domain") or "").rsplit(".", 1)[-1] for r in top
        ).most_common(8),
        "overall_domain_tld": collections.Counter(
            (r.get("source_domain") or "").rsplit(".", 1)[-1] for r in ordered
        ).most_common(8),
        "top_lane": distribution(top, "lane"),
        "overall_lane": distribution(ordered, "lane"),
        "top_local_language_rate": sum(
            1 for r in top if r["probabilities"]["local_language_search_may_help"] >= 0.5
        ) / float(len(top)),
        "overall_local_language_rate": sum(
            1 for r in ordered
            if r["probabilities"]["local_language_search_may_help"] >= 0.5
        ) / float(len(ordered)),
    }


def analyse_cohort_a(results):
    ok = [r for r in _scored(results) if r["cohort"] == "A"]
    if not ok:
        return {}
    selected = [r["triage_score"] for r in ok if r["selected"]]
    unselected = [r["triage_score"] for r in ok if not r["selected"]]
    by_pool = collections.defaultdict(list)
    for record in ok:
        by_pool[record["pool"]].append(record)
    agreement = 0
    pools = 0
    for pool, members in by_pool.items():
        if not any(m["selected"] for m in members) or len(members) < 2:
            continue
        pools += 1
        best = max(members, key=lambda m: m["triage_score"])
        if best["selected"]:
            agreement += 1
    return {
        "scored": len(ok),
        "pools": pools,
        "selected_stats": cases.describe(selected),
        "unselected_stats": cases.describe(unselected),
        "selection_agreement_top1": (agreement / float(pools)) if pools else None,
        "selection_agreement_random": (
            sum(1.0 / len(m) for m in by_pool.values() if len(m) >= 2
                and any(x["selected"] for x in m)) / pools
            if pools
            else None
        ),
        "lane_distribution": collections.Counter(r["initial_lane"] for r in ok),
        "language_top_quartile": collections.Counter(
            (r.get("source_language") or "unknown")
            for r in sorted(ok, key=lambda r: -r["triage_score"])[: max(1, len(ok) // 4)]
        ).most_common(8),
        "language_overall": collections.Counter(
            (r.get("source_language") or "unknown") for r in ok
        ).most_common(8),
    }


# -------------------------------------------------------------------- audit


def audit(engine_root=None):
    cohort_b = cases.build_cohort_b(engine_root)
    pools = cases.build_cohort_a(engine_root)
    evaluable = cases.worth_evaluable(cohort_b)
    dates = sorted(r["date"] for r in cohort_b if r["date"])
    counts = collections.Counter(r["outcome"]["terminal_stage"] for r in cohort_b)
    return {
        "raw_discovery_candidates": None,
        "raw_discovery_note": (
            "pre-commissioning discovery pools were not retained; only "
            "commissioning-desk candidate pools survive"
        ),
        "commissioned_candidates": len(cohort_b),
        "with_seed_snapshot": len(cohort_b),
        "date_range": [dates[0], dates[-1]] if dates else None,
        "distinct_dates": len({r["date"] for r in cohort_b}),
        "desk_days": len(cases.desk_days(engine_root)),
        "worth_evaluable": len(evaluable),
        "worth_pass": sum(1 for r in evaluable if r["outcome"]["worth_pass"]),
        "worth_non_pass": sum(1 for r in evaluable if not r["outcome"]["worth_pass"]),
        "research_evaluable": sum(
            1 for r in cohort_b if r["outcome"]["research_evaluable"]
        ),
        "research_pass": sum(
            1 for r in cohort_b
            if r["outcome"]["research_evaluable"] and r["outcome"]["research_pass"]
        ),
        "ledger_evaluable": sum(
            1 for r in cohort_b if r["outcome"]["ledger_evaluable"]
        ),
        "ledger_pass": sum(
            1 for r in cohort_b
            if r["outcome"]["ledger_evaluable"] and r["outcome"]["ledger_pass"]
        ),
        "terminal_stages": dict(counts),
        "cohort_a_pools": len(pools),
        "cohort_a_candidates": sum(len(p["candidates"]) for p in pools),
        "mean_state_bytes": (
            sum(len(json.dumps(r["state"]).encode("utf-8")) for r in cohort_b)
            / float(len(cohort_b))
            if cohort_b
            else 0
        ),
        "sufficiency_pass": (
            len(evaluable) >= 30
            and any(r["outcome"]["worth_pass"] for r in evaluable)
            and any(not r["outcome"]["worth_pass"] for r in evaluable)
        ),
    }


# --------------------------------------------------------------------- cli


def write_results(payload, name):
    os.makedirs(RESULT_ROOT, exist_ok=True)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(RESULT_ROOT, "%s-%s.json" % (name, stamp))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, ensure_ascii=False, default=str)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--cohort", choices=["a", "b"], default="b")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--report", default="")
    parser.add_argument("--engine-root", default=None)
    args = parser.parse_args(argv)

    if args.report:
        with open(args.report, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        results = payload["results"]
        summary = {
            "cohort_b": analyse_cohort_b(results),
            "daily": daily_analysis(results, args.engine_root),
            "diversity": diversity_check(results),
            "cohort_a": analyse_cohort_a(results),
        }
        print(json.dumps(summary, indent=1, default=str))
        return 0

    if args.audit:
        print(json.dumps(audit(args.engine_root), indent=1, default=str))
        return 0

    if args.cohort == "b":
        case_list = cases.build_cohort_b(args.engine_root)
    else:
        case_list = [
            candidate
            for pool in cases.build_cohort_a(args.engine_root)
            for candidate in pool["candidates"]
        ]
    if args.limit:
        case_list = case_list[: args.limit]

    if not args.live and not args.dry_run:
        parser.error("choose --live or --dry-run")

    api_key = load_api_key() if args.live else ""
    if args.live and not api_key:
        print("no OPENROUTER_API_KEY", file=sys.stderr)
        return 2

    started = time.time()
    results = evaluate(case_list, args.live, api_key)
    elapsed = time.time() - started

    ok = _scored(results)
    payload = {
        "experiment": "jev-seed-triage",
        "cohort": args.cohort.upper(),
        "requested_model": JEV_MODEL,
        "resolved_models": sorted(
            {r.get("resolved_model") for r in ok if r.get("resolved_model")}
        ),
        "live": args.live,
        "cases": len(case_list),
        "calls": sum(1 for r in results if r.get("status") != "DRY_RUN"),
        "ok": len(ok),
        "schema_errors": sum(1 for r in results if r.get("status") == "SCHEMA_ERROR"),
        "transport_errors": sum(
            1 for r in results if r.get("status") == "TRANSPORT_ERROR"
        ),
        "reported_cost_usd": sum(
            float(r.get("reported_cost_usd") or 0.0) for r in results
        ),
        "mean_latency_ms": (
            sum(r.get("latency_ms", 0) for r in results if r.get("latency_ms"))
            / float(max(1, sum(1 for r in results if r.get("latency_ms"))))
        ),
        "wall_seconds": round(elapsed, 1),
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "results": results,
    }
    if args.cohort == "b":
        payload["summary"] = {
            "cohort_b": analyse_cohort_b(results),
            "daily": daily_analysis(results, args.engine_root),
            "diversity": diversity_check(results),
        }
    else:
        payload["summary"] = {"cohort_a": analyse_cohort_a(results)}

    path = write_results(payload, "cohort-%s" % args.cohort)
    print(json.dumps(
        {k: v for k, v in payload.items() if k not in ("results", "summary")},
        indent=1,
        default=str,
    ))
    print(json.dumps(payload["summary"], indent=1, default=str))
    print("results: %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
