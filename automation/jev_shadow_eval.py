#!/usr/bin/env python3
"""Jev shadow benchmark for materiality and output repair routing.

EXPERIMENTAL / SHADOW ONLY.

Jev has zero publication authority. This harness does not import, modify or
call any production stage. It reads retained run artifacts read-only, asks a
pinned decision model a bounded editorial question per finding, and writes
results OUTSIDE the repository because they may contain unpublished prose.

  python3 automation/jev_shadow_eval.py --gold --dry-run
  python3 automation/jev_shadow_eval.py --gold --live
  python3 automation/jev_shadow_eval.py --recent 20 --live
  python3 automation/jev_shadow_eval.py --run-id <run> --live
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jev_shadow_cases as cases  # noqa: E402

JEV_MODEL = "typesafe/jev-1.13"
JEV_ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
RESULT_ROOT = os.environ.get(
    "JEV_SHADOW_RESULT_ROOT",
    "/srv/data/cripminds-new-engine-v1/experiments/jev-shadow",
)
HIGH_CONFIDENCE = 0.80

MATERIALITY_OPTIONS = {
    "MINOR": (
        "Correcting or removing the disputed unsupported element leaves the "
        "primary carrier, the chronology, the causality, any allegation, the "
        "argument, the conclusion and the substantive reader understanding "
        "unchanged."
    ),
    "MATERIAL": (
        "Correcting or removing the disputed element changes one or more of "
        "the primary carrier, the chronology, the causality, an allegation, "
        "the argument, the conclusion or the substantive reader "
        "understanding; or the article depends on the disputed element."
    ),
}

REPAIR_OPTIONS = {
    "PASS_THROUGH": "No editorial repair is warranted by this finding.",
    "DELETE_PERIPHERAL_SURFACE": (
        "The disputed unsupported wording can be removed without changing "
        "substantive reader understanding."
    ),
    "TARGETED_SUPPORTED_REPAIR": (
        "The idea can remain, but the wording must be rebuilt only from "
        "already-approved material; no new research and no new facts."
    ),
    "HOLD": (
        "The finding is material, central, ambiguous, or cannot be safely "
        "repaired from already-approved material."
    ),
}

DIMENSION_QUESTIONS = {
    "affects_carrier": (
        "Would correcting or removing the disputed element change the story's "
        "primary carrier -- the thing the article is actually carried by?"
    ),
    "affects_chronology": (
        "Would correcting or removing the disputed element change the order "
        "or the dating of events as the reader would reconstruct them?"
    ),
    "affects_causality": (
        "Would correcting or removing the disputed element change any claim "
        "that one thing caused, enabled or prevented another?"
    ),
    "affects_allegation": (
        "Would correcting or removing the disputed element change any "
        "allegation, attribution of responsibility or claim about what an "
        "institution or person did?"
    ),
    "affects_argument": (
        "Would correcting or removing the disputed element change the "
        "article's argument -- the case it makes?"
    ),
    "affects_conclusion": (
        "Would correcting or removing the disputed element change the "
        "article's conclusion -- where it lands?"
    ),
}

READER_UNDERSTANDING_QUESTION = (
    "If the disputed unsupported element were removed or corrected without "
    "adding any new facts, would the reader understand the story materially "
    "differently?"
)

DOCTRINE = (
    "Editorial doctrine: MATERIALITY > PERFECTION. The counterfactual test is "
    "'if corrected, would the reader understand the story differently?' -- no "
    "means MINOR, yes means MATERIAL. Materiality decides only whether a "
    "finding is serious enough to stop publication. Materiality must NEVER "
    "turn an unsupported claim into a supported one: the disputed element is "
    "unsupported either way."
)


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
    """One request per case carrying several independent questions."""
    state = dict(case["state"])
    state["doctrine"] = DOCTRINE
    questions = {
        "materiality": {
            "type": "choice",
            "instructions": (
                "Classify the materiality of this single finding under the "
                "doctrine in the state. Judge only this finding."
            ),
            "criteria": dict(MATERIALITY_OPTIONS),
        },
        "changes_reader_understanding": {
            "type": "noul",
            "instructions": READER_UNDERSTANDING_QUESTION,
        },
        "repair_route": {
            "type": "choice",
            "instructions": (
                "EXPERIMENTAL. Which repair route would this finding warrant, "
                "assuming no new research and no new facts may be introduced?"
            ),
            "criteria": dict(REPAIR_OPTIONS),
        },
    }
    for name, text in DIMENSION_QUESTIONS.items():
        questions[name] = {"type": "noul", "instructions": text}
    return {"model": JEV_MODEL, "state": state, "questions": questions}


def call_jev(payload, api_key, timeout=180):
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
    except urllib.error.HTTPError as exc:  # noqa: PERF203
        detail = exc.read().decode("utf-8", "replace")[:500]
        return None, int((time.time() - started) * 1000), "HTTP_%s: %s" % (
            exc.code,
            _scrub(detail, api_key),
        )
    except Exception as exc:  # noqa: BLE001
        return None, int((time.time() - started) * 1000), "%s: %s" % (
            type(exc).__name__,
            _scrub(str(exc)[:300], api_key),
        )


def _scrub(text, api_key):
    if api_key and api_key in text:
        text = text.replace(api_key, "<redacted>")
    return text


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


def _probabilities(raw, options, label):
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValidationError("%s probabilities not an object" % label)
    out = {}
    for key, value in raw.items():
        if key not in options:
            raise ValidationError("%s probability for unknown option %r" % (label, key))
        out[key] = _num_0_1(value, "%s probability[%s]" % (label, key))
    return out


def validate_response(raw):
    """Strict validation. Raises ValidationError; callers record MODEL_ERROR."""
    if not isinstance(raw, dict):
        raise ValidationError("response is not an object")
    answers = raw.get("answers")
    if not isinstance(answers, dict):
        raise ValidationError("missing answers object")

    expected_noul = ["changes_reader_understanding"] + list(DIMENSION_QUESTIONS)
    expected_choice = {
        "materiality": MATERIALITY_OPTIONS,
        "repair_route": REPAIR_OPTIONS,
    }
    missing = [
        q for q in expected_noul + list(expected_choice) if q not in answers
    ]
    if missing:
        raise ValidationError("missing answers: %s" % ",".join(sorted(missing)))

    out = {}
    for name in expected_noul:
        answer = answers[name]
        if not isinstance(answer, dict) or answer.get("type") != "noul":
            raise ValidationError("%s is not a noul answer" % name)
        out[name] = {"probability": _num_0_1(answer.get("noul"), name)}

    for name, options in expected_choice.items():
        answer = answers[name]
        if not isinstance(answer, dict) or answer.get("type") != "choice":
            raise ValidationError("%s is not a choice answer" % name)
        choice = answer.get("choice")
        if choice not in options:
            raise ValidationError("%s choice %r outside defined options" % (name, choice))
        confidence = answer.get("confidence")
        if confidence is not None:
            confidence = _num_0_1(confidence, "%s confidence" % name)
        out[name] = {
            "choice": choice,
            "confidence": confidence,
            "probabilities": _probabilities(
                answer.get("probabilities"), options, name
            ),
        }

    usage = raw.get("usage") or {}
    return {
        "answers": out,
        "resolved_model": raw.get("model"),
        "provider": raw.get("provider"),
        "generation_id": raw.get("id"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "reported_cost_usd": usage.get("cost"),
    }


# ------------------------------------------------------------------ runner


def evaluate(case_list, live, api_key, timeout=180):
    results = []
    for case in case_list:
        record = {
            "case_id": case["case_id"],
            "run_id": case["run_id"],
            "date": case["date"],
            "stage": case["stage"],
            "finding_type": case["finding_type"],
            "expected_route": case["expected_route"],
            "expected_materiality": case["expected_materiality"],
            "expected_repair_route": case.get("expected_repair_route"),
            "label_authority": case["label_authority"],
            "independence_key": case.get("independence_key"),
            "trusted": case.get("trusted", False),
            "scored_for_materiality": case.get("scored_for_materiality", False),
            "scored_for_repair": case.get("scored_for_repair", False),
            "source_artifacts": case["source_artifacts"],
            "input_hash": case["input_hash"],
            "hard_conditions": case["hard_conditions"],
            "route": case["computed_route"],
            "route_reason": case["route_reason"],
            "jev_called": False,
            "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "requested_model": JEV_MODEL,
            "state": case["state"],
        }
        record["route_match"] = case["computed_route"] == case["expected_route"] or (
            case["expected_route"] == "UNLABELED_EXPLORATORY"
        )

        if case["computed_route"] != "ADJUDICATE":
            results.append(record)
            continue
        if not live:
            record["status"] = "DRY_RUN"
            record["request_preview_bytes"] = len(
                json.dumps(build_request(case)).encode("utf-8")
            )
            results.append(record)
            continue

        raw, latency_ms, error = call_jev(build_request(case), api_key, timeout)
        record["jev_called"] = True
        record["latency_ms"] = latency_ms
        if error:
            record["status"] = "MODEL_ERROR"
            record["error"] = error
            results.append(record)
            continue
        try:
            validated = validate_response(raw)
        except ValidationError as exc:
            record["status"] = "MODEL_ERROR"
            record["error"] = "SCHEMA: %s" % exc
            results.append(record)
            continue

        record["status"] = "OK"
        record.update(
            {
                "resolved_model": validated["resolved_model"],
                "provider": validated["provider"],
                "generation_id": validated["generation_id"],
                "input_tokens": validated["input_tokens"],
                "output_tokens": validated["output_tokens"],
                "reported_cost_usd": validated["reported_cost_usd"],
                "materiality": validated["answers"]["materiality"],
                "repair_route": validated["answers"]["repair_route"],
                "changes_reader_understanding": validated["answers"][
                    "changes_reader_understanding"
                ],
                "dimensions": {
                    name: validated["answers"][name] for name in DIMENSION_QUESTIONS
                },
            }
        )
        # Only a trusted label scores. An UNRESOLVED case, a detector false
        # positive and an unlabelled exploratory finding all answer `None`, and
        # `metrics` never counts them.
        if case.get("scored_for_materiality"):
            record["materiality_match"] = (
                validated["answers"]["materiality"]["choice"]
                == case["expected_materiality"]
            )
        else:
            record["materiality_match"] = None
        if case.get("scored_for_repair"):
            record["repair_route_match"] = (
                validated["answers"]["repair_route"]["choice"]
                == case["expected_repair_route"]
            )
        else:
            record["repair_route_match"] = None
        results.append(record)
    return results


# ----------------------------------------------------------------- metrics


def _material_confidence(record):
    """Confidence attached to the chosen materiality label."""
    materiality = record.get("materiality") or {}
    probabilities = materiality.get("probabilities") or {}
    choice = materiality.get("choice")
    if choice in probabilities:
        return probabilities[choice]
    return materiality.get("confidence")


def metrics(results):
    scored = [
        r
        for r in results
        if r.get("status") == "OK" and r.get("materiality_match") is not None
    ]
    correct = [r for r in scored if r["materiality_match"]]
    wrong = [r for r in scored if not r["materiality_match"]]

    false_minor = [
        r
        for r in wrong
        if r["expected_materiality"] == "MATERIAL"
        and r["materiality"]["choice"] == "MINOR"
    ]
    false_material = [
        r
        for r in wrong
        if r["expected_materiality"] == "MINOR"
        and r["materiality"]["choice"] == "MATERIAL"
    ]

    def _high(subset):
        out = []
        for r in subset:
            conf = _material_confidence(r)
            if conf is not None and conf >= HIGH_CONFIDENCE:
                out.append(r["case_id"])
        return out

    def _mean(values):
        values = [v for v in values if v is not None]
        return round(sum(values) / len(values), 4) if values else None

    called = [r for r in results if r.get("jev_called")]
    ok = [r for r in results if r.get("status") == "OK"]

    repair_counts = {option: 0 for option in REPAIR_OPTIONS}
    for r in ok:
        repair_counts[r["repair_route"]["choice"]] += 1

    reported_costs = [
        r.get("reported_cost_usd") for r in ok if r.get("reported_cost_usd") is not None
    ]

    # Baselines. The first benchmark's 10/12 was the MINOR base rate, not
    # accuracy: a model that answered MINOR to everything would have scored the
    # same. Both constant answers are reported so that cannot recur unnoticed.
    expected_minor = len(
        [r for r in scored if r["expected_materiality"] == "MINOR"]
    )
    expected_material = len(scored) - expected_minor
    constant_minor = (
        round(expected_minor / len(scored), 4) if scored else None
    )
    constant_material = (
        round(expected_material / len(scored), 4) if scored else None
    )
    accuracy = round(len(correct) / len(scored), 4) if scored else None

    repair_scored = [
        r
        for r in results
        if r.get("status") == "OK" and r.get("repair_route_match") is not None
    ]
    repair_correct = [r for r in repair_scored if r["repair_route_match"]]
    repair_expected = {option: 0 for option in REPAIR_OPTIONS}
    for r in repair_scored:
        repair_expected[r["expected_repair_route"]] += 1
    constant_repair = (
        round(max(repair_expected.values()) / len(repair_scored), 4)
        if repair_scored
        else None
    )
    repair_accuracy = (
        round(len(repair_correct) / len(repair_scored), 4) if repair_scored else None
    )

    # The two labels are independent questions. A model that collapses them --
    # every MATERIAL answered HOLD, every MINOR answered DELETE -- is not
    # judging repairability, and the gold set contains the counterexamples
    # (17 Sep F4 is MATERIAL and repairable).
    collapsed = [
        r["case_id"]
        for r in repair_scored
        if (
            r["materiality"]["choice"] == "MATERIAL"
            and r["repair_route"]["choice"] == "HOLD"
        )
        or (
            r["materiality"]["choice"] == "MINOR"
            and r["repair_route"]["choice"] == "DELETE_PERIPHERAL_SURFACE"
        )
    ]

    return {
        "cases_total": len(results),
        "jev_called": len(called),
        "model_error": len([r for r in results if r.get("status") == "MODEL_ERROR"]),
        "scored_cases": len(scored),
        "materiality_correct": len(correct),
        "materiality_accuracy": accuracy,
        "expected_minor": expected_minor,
        "expected_material": expected_material,
        "constant_minor_baseline": constant_minor,
        "constant_material_baseline": constant_material,
        "beats_both_constant_baselines": (
            None
            if accuracy is None
            else accuracy > max(constant_minor, constant_material)
        ),
        "repair_route_scored": len(repair_scored),
        "repair_route_correct": len(repair_correct),
        "repair_route_accuracy": repair_accuracy,
        "repair_route_expected_distribution": repair_expected,
        "constant_repair_route_baseline": constant_repair,
        "repair_beats_constant_baseline": (
            None
            if repair_accuracy is None
            else repair_accuracy > constant_repair
        ),
        "repair_collapsed_onto_materiality": collapsed,
        "excluded_from_materiality_accuracy": {
            "detector_false_positive": [
                r["case_id"]
                for r in results
                if r["route"] == "DETECTOR_FALSE_POSITIVE"
            ],
            "hard_bypass": [
                r["case_id"] for r in results if r["route"] == "HARD_BYPASS"
            ],
            "untrusted_label": [
                r["case_id"] for r in results if not r.get("trusted")
            ],
        },
        "false_minor": [r["case_id"] for r in false_minor],
        "high_confidence_false_minor": _high(false_minor),
        "false_material": [r["case_id"] for r in false_material],
        "high_confidence_false_material": _high(false_material),
        "mean_confidence_correct": _mean([_material_confidence(r) for r in correct]),
        "mean_confidence_incorrect": _mean([_material_confidence(r) for r in wrong]),
        "mean_latency_ms": _mean([r.get("latency_ms") for r in called]),
        "total_input_tokens": sum(r.get("input_tokens") or 0 for r in ok),
        "total_output_tokens": sum(r.get("output_tokens") or 0 for r in ok),
        "cost_usd": round(sum(reported_costs), 6) if reported_costs else None,
        "cost_basis": (
            "PROVIDER_REPORTED" if reported_costs else "UNAVAILABLE"
        ),
        "repair_route_distribution": repair_counts,
        "route_discipline": {
            "hard_bypass": [r["case_id"] for r in results if r["route"] == "HARD_BYPASS"],
            "detector_false_positive": [
                r["case_id"]
                for r in results
                if r["route"] == "DETECTOR_FALSE_POSITIVE"
            ],
            "bypassed_and_never_called": all(
                not r["jev_called"]
                for r in results
                if r["route"] in ("HARD_BYPASS", "DETECTOR_FALSE_POSITIVE")
            ),
            "route_mismatches": [
                r["case_id"] for r in results if not r.get("route_match")
            ],
        },
    }


def counterfactual(results):
    """Pipeline opportunity, NOT publication outcome.

    A case 'could have continued to the next gate' only if the trusted label
    was MINOR, no deterministic hard condition existed, and Jev agreed. It says
    nothing about whether downstream gates would have passed -- they never ran.
    """
    could_continue = []
    correctly_held = []
    for r in results:
        if r.get("status") != "OK":
            continue
        if r["expected_materiality"] == "MINOR" and not r["hard_conditions"]:
            if r["materiality"]["choice"] == "MINOR":
                could_continue.append(r["case_id"])
        if r["expected_materiality"] == "MATERIAL":
            if r["materiality"]["choice"] == "MATERIAL":
                correctly_held.append(r["case_id"])
    return {
        "could_have_continued_to_next_gate": could_continue,
        "correctly_left_held": correctly_held,
        "caveat": (
            "Pipeline opportunity only. Downstream gates never ran on these "
            "runs; this is not a publication outcome and must not be reported "
            "as articles that would have published."
        ),
    }


# --------------------------------------------------------------------- io


def write_results(payload, label):
    os.makedirs(RESULT_ROOT, exist_ok=True)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(RESULT_ROOT, "jev-shadow-%s-%s.json" % (label, stamp))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
    os.chmod(path, 0o600)
    return path


def assert_result_path_outside_repo(path, repo_root=None):
    repo_root = os.path.abspath(
        repo_root
        or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if os.path.abspath(path).startswith(repo_root + os.sep):
        raise RuntimeError(
            "refusing to write experiment results inside the repository: %s" % path
        )
    return True


# -------------------------------------------------------------------- cli


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", action="store_true", help="run the gold caseset")
    parser.add_argument("--recent", type=int, default=0, help="N recent runs, exploratory")
    parser.add_argument("--run-id", help="single historical run, exploratory")
    parser.add_argument("--live", action="store_true", help="call Jev")
    parser.add_argument("--dry-run", action="store_true", help="no network at all")
    parser.add_argument(
        "--balance",
        action="store_true",
        help="print the gold caseset's label balance and baselines, then exit",
    )
    parser.add_argument(
        "--review-queue",
        action="store_true",
        help="print the unresolved owner-review cases, then exit",
    )
    parser.add_argument("--engine-root", default=None)
    args = parser.parse_args(argv)

    if args.balance:
        gold = cases.gold_cases(root=args.engine_root)
        print(json.dumps(cases.balance_report(gold), indent=1, sort_keys=True))
        return 0
    if args.review_queue:
        queue = cases.review_queue_cases(root=args.engine_root)
        for case in queue:
            print("%s  %s  %s" % (case["case_id"], case["stage"], case["run_id"]))
            print("   owner must decide: %s" % case["owner_must_decide"])
        print("\n%d unresolved; none are scored." % len(queue))
        return 0

    if args.live and args.dry_run:
        parser.error("--live and --dry-run are mutually exclusive")
    if not (args.gold or args.recent or args.run_id):
        parser.error("choose --gold, --recent N or --run-id")

    root = args.engine_root
    label = "gold" if args.gold else ("recent" if args.recent else "run")

    case_list = []
    if args.gold:
        case_list.extend(cases.gold_cases(root=root))
    if args.recent:
        case_list.extend(
            cases.exploratory_cases(cases.recent_run_ids(args.recent, root=root), root=root)
        )
    if args.run_id:
        case_list.extend(cases.exploratory_cases([args.run_id], root=root))

    api_key = ""
    if args.live:
        api_key = load_api_key()
        if not api_key:
            print("LIVE BENCHMARK BLOCKED: NO KEY")
            return 2

    results = evaluate(case_list, live=args.live, api_key=api_key)
    payload = {
        "experiment": "jev-shadow",
        "authority": "NONE -- shadow only, no publication authority",
        "requested_model": JEV_MODEL,
        "endpoint": JEV_ENDPOINT,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "mode": "LIVE" if args.live else "DRY_RUN",
        "results": results,
        "caseset_balance": cases.balance_report(case_list),
        "metrics": metrics(results),
        "counterfactual": counterfactual(results),
    }

    summary = {
        k: v for k, v in payload.items() if k not in ("results",)
    }
    print(json.dumps(summary, indent=1, sort_keys=True))

    if args.live:
        assert_result_path_outside_repo(RESULT_ROOT)
        path = write_results(payload, label)
        print("\nRESULTS: %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
