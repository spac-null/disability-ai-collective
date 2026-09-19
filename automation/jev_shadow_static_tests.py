#!/usr/bin/env python3
"""Offline tests for the Jev shadow benchmark.

No API key, no network, no model calls. Synthetic fixtures mirror the shape of
retained run artifacts; Jev responses are mocked.

  python3 automation/jev_shadow_static_tests.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jev_shadow_cases as cases  # noqa: E402
import jev_shadow_eval as ev  # noqa: E402

FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)


# ------------------------------------------------------------- fixtures


def write_run(root, run_id, safety, manifest, packet=None, grounding=None,
              publication=None, continuity=None, owner_repair=None,
              fact_check=None):
    path = os.path.join(root, run_id)
    os.makedirs(path, exist_ok=True)

    def dump(name, obj):
        with open(os.path.join(path, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh)

    if safety is not None:
        dump("SAFETY_AUDIT.json", safety)
    dump("MANIFEST.json", manifest)
    if owner_repair is not None:
        dump("OWNER_COPYDESK_REPAIR.json", owner_repair)
    if fact_check is not None:
        dump("FACT_CHECK_ADJUDICATION.json", fact_check)
    if packet is not None:
        dump("WRITER_PACKET.json", packet)
    if grounding is not None:
        dump("GROUNDING_FINDINGS.json", grounding)
    if publication is not None:
        dump("PUBLICATION_DECISION.json", publication)
    if continuity is not None:
        with open(os.path.join(path, "CONTINUITY_FINAL.md"), "w", encoding="utf-8") as fh:
            fh.write(continuity)
    return path


def safety_audit(entities=(), blocking=(), discarded=False, relations=None,
                 hard_ok=True):
    return {
        "blocking": list(blocking),
        "continuity_discarded": discarded,
        "semantic_delta": {
            "added_relation_classes": relations or {},
            "added_surface": {"entities": [], "numbers": [], "sensory": []},
            "hard_ok": hard_ok,
        },
        "audits": {
            "continuity_final": {
                "hard_factual_ok": hard_ok,
                "factual_surface": {
                    "unapproved_entities": list(entities),
                    "unapproved_numbers": [],
                    "unapproved_sensory": [],
                },
            }
        },
    }


PACKET = {
    "primary_carrier": "F07",
    "evidence_roles": {"F07": "the transfer of patients out of the centre before 8pm"},
    "story_spine": "The centre resumes 24-hour operation with three or four night beds.",
    "crip_turn": "Night-time hospitality is listed among the centre's main activities.",
    "ending_move": "Lands on who does the moving.",
    "article_type": "NARRATIVE_ARTICLE",
    "beats": [{"carrier": "the transfer of patients"}],
}


def build_fixture_root():
    root = tempfile.mkdtemp(prefix="jev-shadow-test-")
    # 14 Sep analogue: adjudicable, single unsupported entity.
    write_run(
        root,
        "production-20260914T070213Z-d20b3807",
        safety_audit(
            entities=["Italian"],
            blocking=["NEW_UNSUPPORTED_FACTS: entities=['Italian']"],
            hard_ok=False,
        ),
        {"decision": "HOLD", "reasons": ["NEW_UNSUPPORTED_FACTS: entities=['Italian']"]},
        packet=PACKET,
        continuity=(
            "A Mental Health Centre, CSM in Italian, is a neighbourhood centre "
            "run by the health authority. Trieste has four."
        ),
    )
    # 15 Sep analogue: same entity plus discarded continuity and a CAUSAL relation.
    write_run(
        root,
        "production-20260915T072045Z-40294a3a",
        safety_audit(
            entities=["Italian"],
            blocking=["NEW_UNSUPPORTED_FACTS: entities=['Italian']"],
            discarded=True,
            hard_ok=False,
        ),
        {
            "decision": "HOLD",
            "reasons": [
                "continuity was discarded (editing added 1 CAUSAL relation(s))"
            ],
        },
        packet=PACKET,
        continuity="A Comune in Italian has ninety days from the request.",
    )
    # 16 Sep analogue: deterministic detector false positive.
    write_run(
        root,
        "production-20260916T070723Z-5a4e7891",
        safety_audit(blocking=["CONTINUITY_ADDED_MATERIAL: [\"editing added entities: ['Cem']\"]"]),
        {"decision": "HOLD", "reasons": ["CONTINUITY_ADDED_MATERIAL"]},
        packet=PACKET,
        continuity="Cem Behar wrote the history of the school.",
    )
    # 17 Sep analogue: grounding findings, settled, repairable.
    write_run(
        root,
        "production-20260917T070213Z-67554ae5",
        safety_audit(discarded=True),
        {"decision": "HOLD", "reasons": ["story_architecture HOLD at GROUNDING"]},
        packet=PACKET,
        grounding={
            "payload": {
                "status": "settled",
                "findings": [
                    {
                        "id": "F2",
                        "classification": "TRUE_UNSUPPORTED",
                        "repairable": True,
                        "quote": "The ten seconds of elephant seal are among them.",
                        "suggested_patch": "Which recordings are archived there he does not say.",
                        "why": "Nothing places the recording in the Macaulay Library.",
                    },
                    {
                        "id": "F4",
                        "classification": "TRUE_UNSUPPORTED",
                        "repairable": True,
                        "quote": "Culasso says it was worth the ten-kilometre round trip in winds of 70km/h at -25C.",
                        "suggested_patch": "Culasso says it was worth the ten-kilometre round trip to the colony.",
                        "why": "The weather belongs to arrival at base Artigas.",
                    },
                    {
                        "id": "F9",
                        "classification": "TRUE_UNSUPPORTED",
                        "repairable": False,
                        "quote": "A claim that cannot be repaired.",
                        "suggested_patch": "",
                        "why": "Not repairable from approved material.",
                    },
                ],
            }
        },
    )
    # 19 Sep analogue: negatives, machine language, discarded continuity.
    write_run(
        root,
        "production-20260919T070300Z-faa849c8",
        safety_audit(
            blocking=[
                "UNSUPPORTED_NEGATIVES: 2 negative-shaped sentence(s)",
                "MACHINE_LANGUAGE: provenance frames",
            ],
            discarded=True,
        ),
        {
            "decision": "HOLD",
            "reasons": ["continuity was discarded (editing added 1 NEGATION relation(s))"],
        },
        packet=PACKET,
        continuity="The admissions were unsuccessful in preventing malnutrition.",
    )
    # SFMOMA analogue: owner-adjudicated reader findings, decision retained.
    write_run(
        root,
        cases.SFMOMA_RUN_ID,
        safety_audit(blocking=["NEW_UNSUPPORTED_FACTS: entities=['Museum']"]),
        {"decision": "HOLD", "reasons": ["NEW_UNSUPPORTED_FACTS"]},
        packet=PACKET,
        publication={
            "publication_status": "PASS_WITH_MINOR_FINDINGS",
            "reader_findings": {
                "OPENING": {
                    "note": "The opening is secondhand.",
                    "passages": ["In one of her drawings, Camille Holvoet considers income."],
                    "verdict": "HOLD",
                },
                "ENDING": {
                    "note": "The ending restates the opening.",
                    "passages": ["Inside one of them hung a drawing."],
                    "verdict": "HOLD",
                },
            },
            "reader_materiality_classification": {"OPENING": "MINOR", "ENDING": "MINOR"},
        },
        owner_repair={
            "owner_authorized": True,
            "reason": "nonmaterial factual-scope/attribution imprecisions with "
                      "exact source-supported Grounder patches",
            "finding_ids": ["F1"],
            "exact_before": {"F1": "The drawing names a problem."},
            "exact_after": {"F1": "A reviewer noted the problem."},
        },
        continuity="It hung at the San Francisco Museum of Modern Art.",
    )
    # Fast Lane analogue: a Fact Check contradiction the owner adjudicated
    # against the primary document. No SAFETY_AUDIT at all -- the stage-scoped
    # artifact requirement must tolerate that.
    write_run(
        root,
        "fast-lane-v1-fresh-asl-whitehouse-20260912",
        None,
        {"decision": "PASS_WITH_MINOR_FINDINGS", "reasons": []},
        packet=PACKET,
        fact_check={
            "policy": "PRIMARY_SOURCE_EXACT_MATCH",
            "findings": [
                {
                    "finding_id": "C04",
                    "raw_status": "CONTRADICTED",
                    "adjudication": "VERIFIED_PRIMARY_SOURCE",
                    "article_span": "their gripe is with Congress",
                    "document_identity": "Document 29 (order, Judge Amir H. Ali)",
                    "reason": "byte-level normalized match against the primary PDF",
                }
            ],
        },
    )
    # A Grounding-only run: the article never reached Safety, so there is no
    # SAFETY_AUDIT and no CONTINUITY_FINAL. This must still resolve.
    write_run(
        root,
        "production-20260903T135702Z-3ea6156a",
        None,
        {"decision": "HOLD", "reasons": ["repair verification failed"]},
        grounding={
            "payload": {
                "status": "settled",
                "findings": [
                    {
                        "id": "F2",
                        "classification": "TRUE_UNSUPPORTED",
                        "repairable": True,
                        "quote": "The rest goes back into the river.",
                        "suggested_patch": "The rest -- most of it -- goes back.",
                        "why": "The figure is derived by subtraction.",
                    }
                ],
            }
        },
    )
    return root


# ----------------------------------------------------------------- mocks


def mock_response(materiality, repair, reader_prob, confidence=0.9, dims=0.1):
    answers = {
        "materiality": {
            "type": "choice",
            "choice": materiality,
            "confidence": confidence,
            "probabilities": {
                "MINOR": confidence if materiality == "MINOR" else 1 - confidence,
                "MATERIAL": confidence if materiality == "MATERIAL" else 1 - confidence,
            },
        },
        "repair_route": {
            "type": "choice",
            "choice": repair,
            "confidence": 0.7,
            "probabilities": {k: (0.7 if k == repair else 0.1) for k in ev.REPAIR_OPTIONS},
        },
        "changes_reader_understanding": {"type": "noul", "noul": reader_prob},
    }
    for name in ev.DIMENSION_QUESTIONS:
        answers[name] = {"type": "noul", "noul": dims}
    return {
        "model": "typesafe/jev-1.13-20260917",
        "provider": "TypeSafe",
        "id": "gen-dec-test",
        "answers": answers,
        "usage": {"input_tokens": 900, "output_tokens": 60, "cost": 0.00004},
    }


# ----------------------------------------------------------------- tests


def test_extraction(root):
    print("\n[case extraction]")
    gold = cases.gold_cases(root=root)
    by_id = {c["case_id"]: c for c in gold}
    check("gold set non-empty", len(gold) >= 7, str(len(gold)))

    c14 = by_id["20260914-safety-entity-italian"]
    check(
        "14 Sep containing sentence extracted",
        "CSM in Italian" in c14["state"]["containing_sentence"],
        c14["state"]["containing_sentence"],
    )
    check("14 Sep disputed span bounded", c14["state"]["disputed_span"] == "Italian")
    check("14 Sep carries packet spine", bool(c14["state"]["packet"]["story_spine"]))
    check("14 Sep input hash stable", c14["input_hash"] == cases.state_hash(c14["state"]))

    c17 = by_id["20260917-grounding-F4-weather-conflation"]
    check(
        "17 Sep grounding quote extracted",
        "70km/h" in c17["state"]["disputed_span"],
        c17["state"]["disputed_span"],
    )
    check(
        "17 Sep repair material flagged",
        c17["state"]["repair_available_from_approved_material"] is True,
    )

    reader = [c for c in gold if c["stage"] == "READER"]
    check("SFMOMA reader case extracted", len(reader) == 1, str(len(reader)))
    check(
        "SFMOMA labels are owner-authored",
        all(c["label_authority"] == "OWNER" for c in reader),
    )
    check(
        "SFMOMA label taken verbatim from the decision",
        [c["expected_materiality"] for c in reader] == ["MINOR"],
    )

    owner = by_id["20260913-owner-repair-F1-attribution"]
    check(
        "owner copy-desk span read from the artifact",
        owner["state"]["disputed_span"] == "The drawing names a problem.",
        owner["state"]["disputed_span"],
    )
    check(
        "owner copy-desk patch flagged as source-supported",
        owner["state"]["repair_available_from_approved_material"] is True,
    )

    fc = by_id["20260912-factcheck-C04-primary-verified"]
    check(
        "fact check case resolves with no SAFETY_AUDIT",
        fc["state"]["fact_check_adjudication"] == "VERIFIED_PRIMARY_SOURCE",
    )
    check(
        "grounding-only run resolves with no SAFETY_AUDIT",
        "20260903-grounding-F2-derived-litres" in by_id,
    )
    return gold


def test_labels(gold):
    """Both gold labels, their authority, and the bar for being scored."""
    print("\n[gold labels]")
    by_id = {c["case_id"]: c for c in gold}

    for case in gold:
        check(
            "%s materiality label is valid" % case["case_id"],
            case["expected_materiality"] is None
            or case["expected_materiality"] in cases.MATERIALITY_LABELS,
            str(case["expected_materiality"]),
        )
        check(
            "%s repair route is valid" % case["case_id"],
            case["expected_repair_route"] is None
            or case["expected_repair_route"] in cases.REPAIR_ROUTES,
            str(case["expected_repair_route"]),
        )

    f2 = by_id["20260917-grounding-F2-macaulay-linkage"]
    f4 = by_id["20260917-grounding-F4-weather-conflation"]
    check(
        "materiality and repairability are separate labels",
        f2["expected_materiality"] == f4["expected_materiality"] == "MATERIAL"
        and f2["expected_repair_route"] == "HOLD"
        and f4["expected_repair_route"] == "TARGETED_SUPPORTED_REPAIR",
        "%s / %s" % (f2["expected_repair_route"], f4["expected_repair_route"]),
    )
    c14 = by_id["20260914-safety-entity-italian"]
    check(
        "a MINOR finding can still be deleted rather than passed through",
        c14["expected_materiality"] == "MINOR"
        and c14["expected_repair_route"] == "DELETE_PERIPHERAL_SURFACE",
    )

    check(
        "every scored case has a trusted authority",
        all(
            c["label_authority"] in cases.TRUSTED_AUTHORITIES
            for c in gold
            if c["scored_for_materiality"]
        ),
    )
    check(
        "no UNRESOLVED case is in gold",
        all(c["label_authority"] != "UNRESOLVED" for c in gold),
    )
    check(
        "detector false positives are not scored for materiality",
        all(
            not c["scored_for_materiality"]
            for c in gold
            if c["computed_route"] == "DETECTOR_FALSE_POSITIVE"
        ),
    )
    check(
        "hard-bypassed cases are not scored for materiality",
        all(
            not c["scored_for_materiality"]
            for c in gold
            if c["computed_route"] == "HARD_BYPASS"
        ),
    )


def test_review_queue():
    """Unresolved cases are carried, described, and never scored."""
    print("\n[owner review queue]")
    check("review queue non-empty", len(cases.REVIEW_QUEUE) >= 5,
          str(len(cases.REVIEW_QUEUE)))
    check(
        "every unresolved case says what the owner must decide",
        all(spec.get("owner_must_decide") for spec in cases.REVIEW_QUEUE),
    )
    check(
        "no unresolved case carries a label",
        all(
            spec.get("expected_materiality") is None
            and spec.get("expected_repair_route") is None
            for spec in cases.REVIEW_QUEUE
        ),
    )
    gold_ids = {spec["case_id"] for spec in cases.GOLD_REGISTRY}
    queue_ids = {spec["case_id"] for spec in cases.REVIEW_QUEUE}
    check("gold and queue are disjoint", not (gold_ids & queue_ids))


def test_registry_validation():
    """The registry guards, each proved by a mutation that must be refused."""
    print("\n[registry validation]")
    check("the committed registry validates", cases.validate_registry() is True)

    def refuses(name, registry=None, queue=None, cap=cases.ARTICLE_CAP):
        try:
            cases.validate_registry(
                registry=registry if registry is not None else cases.GOLD_REGISTRY,
                queue=queue if queue is not None else [],
                cap=cap,
            )
        except cases.RegistryError:
            check(name, True)
            return
        check(name, False, "accepted")

    def mutate(**fields):
        spec = dict(cases.GOLD_REGISTRY[0])
        spec.update(fields)
        return [spec]

    refuses("invalid materiality label", mutate(expected_materiality="MAYBE"))
    refuses("invalid repair route", mutate(expected_repair_route="DELETE"))
    refuses("unknown stage", mutate(stage="COPYDESK"))
    refuses("unknown authority", mutate(label_authority="VIBES"))
    refuses(
        "materiality label without a trusted authority",
        mutate(label_authority="UNRESOLVED", owner_must_decide="x"),
    )
    refuses(
        "repair route with no materiality label",
        mutate(expected_materiality=None),
    )
    refuses(
        "a bypassed case carrying adjudication labels",
        mutate(expected_route="HARD_BYPASS"),
    )
    refuses(
        "an UNRESOLVED case inside gold",
        [
            dict(
                cases.REVIEW_QUEUE[0],
                label_authority="UNRESOLVED",
            )
        ],
    )
    refuses(
        "unpublished prose committed as a registry field",
        mutate(note="x" * (cases._MAX_REGISTRY_FIELD + 1)),
    )
    refuses(
        "a registry field long enough to be a retained span",
        mutate(finding_type="y" * 240),
    )

    over_cap = []
    for index in range(cases.ARTICLE_CAP + 1):
        spec = dict(cases.GOLD_REGISTRY[0])
        spec["case_id"] = "cap-%d" % index
        spec["independence_key"] = "one-article"
        over_cap.append(spec)
    refuses("one article above the per-article cap", over_cap)

    at_cap = over_cap[: cases.ARTICLE_CAP]
    try:
        ok = cases.validate_registry(registry=at_cap, queue=[])
    except cases.RegistryError as exc:  # noqa: BLE001
        ok = "raised: %s" % exc
    check("exactly at the cap is allowed", ok is True, str(ok))

    duplicates = [cases.GOLD_REGISTRY[0], dict(cases.GOLD_REGISTRY[0])]
    refuses("duplicate case_id", duplicates)


def test_balance(gold):
    """Balance reporting, and the baselines a model has to beat."""
    print("\n[balance reporting]")
    # From the registry alone: no artifacts, so this holds on any host.
    report = cases.registry_balance()
    check(
        "minor and material both present",
        report["minor"] >= 10 and report["material"] >= 10,
        report["minor_material_ratio"],
    )
    check(
        "not trivially solvable by a constant answer",
        report["trivially_solvable_by_constant_materiality"] is False,
        str(report["constant_minor_baseline"]),
    )
    check(
        "baselines are complementary",
        abs(
            report["constant_minor_baseline"]
            + report["constant_material_baseline"]
            - 1.0
        )
        < 1e-9,
    )
    check(
        "per-article cap holds in the resolved set",
        report["max_cases_from_one_article"] <= cases.ARTICLE_CAP,
        str(report["max_cases_from_one_article"]),
    )
    check(
        "cases drawn from many articles",
        report["articles"] >= 15,
        str(report["articles"]),
    )
    check(
        "repair routes are reported per option",
        set(report["repair_route_counts"]) == set(cases.REPAIR_ROUTES),
    )
    check(
        "unresolved cases are outside the balance",
        report["by_authority"].get("UNRESOLVED") is None,
    )
    check(
        "the fixture-backed subset also reports balance",
        cases.balance_report(gold)["cases_total"] == len(gold),
    )


def test_routing(gold):
    print("\n[routing discipline]")
    by_id = {c["case_id"]: c for c in gold}
    pins = {
        "20260914-safety-entity-italian": ("ADJUDICATE", "MINOR"),
        "20260915-safety-entity-italian": ("HARD_BYPASS", None),
        "20260916-continuity-added-entity-cem": ("DETECTOR_FALSE_POSITIVE", None),
        "20260917-grounding-F2-macaulay-linkage": ("ADJUDICATE", "MATERIAL"),
        "20260917-grounding-F4-weather-conflation": ("ADJUDICATE", "MATERIAL"),
        "20260919-safety-unsupported-negatives": ("HARD_BYPASS", None),
    }
    for case_id, (route, materiality) in pins.items():
        case = by_id[case_id]
        check(
            "%s routes %s" % (case_id, route),
            case["computed_route"] == route,
            case["computed_route"],
        )
        check(
            "%s expected materiality %s" % (case_id, materiality),
            case["expected_materiality"] == materiality,
        )
    check(
        "hard bypass carries a deterministic reason",
        all(
            c["hard_conditions"]
            for c in gold
            if c["computed_route"] == "HARD_BYPASS"
        ),
    )
    check(
        "bypassed cases are never called",
        all(
            not c["jev_called"]
            for c in gold
            if c["computed_route"] != "ADJUDICATE"
        ),
    )
    check(
        "Safety hard conditions do not leak into Grounding cases",
        cases.hard_conditions(
            "GROUNDING",
            {"continuity_discarded": True},
            {"reasons": ["editing added 1 CAUSAL relation(s)"]},
            grounding={"payload": {"status": "settled"}},
            finding={"repairable": True},
        )
        == [],
    )
    check(
        "unrepairable grounding finding is hard",
        "FINDING_NOT_REPAIRABLE"
        in cases.hard_conditions(
            "GROUNDING",
            {},
            {},
            grounding={"payload": {"status": "settled"}},
            finding={"repairable": False},
        ),
    )
    check(
        "unsettled grounding is hard",
        "GROUNDING_UNSETTLED"
        in cases.hard_conditions(
            "GROUNDING", {}, {}, grounding={"payload": {"status": "open"}},
            finding={"repairable": True},
        ),
    )
    check(
        "NEW_UNSUPPORTED_FACTS is not a hard condition",
        cases.hard_conditions(
            "SAFETY",
            {"blocking": ["NEW_UNSUPPORTED_FACTS: entities=['Italian']"]},
            {"reasons": []},
        )
        == [],
    )


def test_request_schema(gold):
    print("\n[request schema]")
    case = [c for c in gold if c["case_id"] == "20260914-safety-entity-italian"][0]
    payload = ev.build_request(case)
    check("model pinned", payload["model"] == "typesafe/jev-1.13")
    check("model is not latest", "latest" not in payload["model"])
    questions = payload["questions"]
    check("questions is a record", isinstance(questions, dict))
    check(
        "materiality is a choice with both options",
        questions["materiality"]["type"] == "choice"
        and set(questions["materiality"]["criteria"]) == {"MINOR", "MATERIAL"},
    )
    check(
        "repair_route carries four options",
        set(questions["repair_route"]["criteria"]) == set(ev.REPAIR_OPTIONS),
    )
    check(
        "reader-understanding question is a noul",
        questions["changes_reader_understanding"]["type"] == "noul",
    )
    check(
        "six independent dimension nouls",
        all(
            questions[name]["type"] == "noul" and questions[name]["instructions"]
            for name in ev.DIMENSION_QUESTIONS
        )
        and len(ev.DIMENSION_QUESTIONS) == 6,
    )
    blob = json.dumps(payload)
    check("no filesystem paths in state", "/srv/" not in blob)
    check("no research pack in state", "RESEARCH_PACK" not in blob)
    check("no ledger in state", "LEDGER" not in blob)
    check("bounded size", len(blob.encode()) < 20000, str(len(blob.encode())))
    check(
        "hard conditions declared to the model",
        payload["state"]["deterministic_hard_conditions_present"] is False,
    )


def test_validation():
    print("\n[response validation]")
    good = mock_response("MINOR", "DELETE_PERIPHERAL_SURFACE", 0.08)
    parsed = ev.validate_response(good)
    check("valid response parses", parsed["answers"]["materiality"]["choice"] == "MINOR")
    check(
        "probabilities parsed",
        parsed["answers"]["materiality"]["probabilities"]["MINOR"] == 0.9,
    )
    check("noul parsed", parsed["answers"]["changes_reader_understanding"]["probability"] == 0.08)
    check("resolved model captured", parsed["resolved_model"] == "typesafe/jev-1.13-20260917")
    check("usage captured", parsed["input_tokens"] == 900)

    def rejects(name, mutate):
        payload = json.loads(json.dumps(good))
        mutate(payload)
        try:
            ev.validate_response(payload)
        except ev.ValidationError:
            check(name, True)
        else:
            check(name, False, "accepted malformed response")

    rejects("rejects missing answers", lambda p: p.pop("answers"))
    rejects(
        "rejects missing question",
        lambda p: p["answers"].pop("affects_causality"),
    )
    rejects(
        "rejects choice outside options",
        lambda p: p["answers"]["materiality"].__setitem__("choice", "PROBABLY_FINE"),
    )
    rejects(
        "rejects wrong answer type",
        lambda p: p["answers"]["materiality"].__setitem__("type", "noul"),
    )
    rejects(
        "rejects noul out of range",
        lambda p: p["answers"]["changes_reader_understanding"].__setitem__("noul", 1.4),
    )
    rejects(
        "rejects non-numeric noul",
        lambda p: p["answers"]["affects_carrier"].__setitem__("noul", "high"),
    )
    rejects(
        "rejects unknown probability key",
        lambda p: p["answers"]["materiality"]["probabilities"].__setitem__("MAYBE", 0.2),
    )
    rejects(
        "rejects out-of-range confidence",
        lambda p: p["answers"]["materiality"].__setitem__("confidence", 2.0),
    )


def test_malformed_run(gold):
    print("\n[malformed response behaviour]")
    calls = {"n": 0}

    def fake_call(payload, api_key, timeout=180):
        calls["n"] += 1
        return {"answers": {"materiality": {"type": "choice", "choice": "NOPE"}}}, 12, None

    original = ev.call_jev
    ev.call_jev = fake_call
    try:
        results = ev.evaluate(gold, live=True, api_key="test-key-not-real")
    finally:
        ev.call_jev = original
    adjudicable = [c for c in gold if c["computed_route"] == "ADJUDICATE"]
    check("one call per adjudicable case, no retry", calls["n"] == len(adjudicable),
          "%s vs %s" % (calls["n"], len(adjudicable)))
    errored = [r for r in results if r.get("status") == "MODEL_ERROR"]
    check("malformed recorded as MODEL_ERROR", len(errored) == len(adjudicable))
    check(
        "no materiality recorded on error",
        all("materiality" not in r for r in errored),
    )


def test_metrics(gold):
    print("\n[metrics and false-MINOR accounting]")

    def fake_call(payload, api_key, timeout=180):
        # Deliberately wrong on one MATERIAL case, at high confidence.
        spine = payload["state"].get("disputed_span", "")
        if "70km/h" in spine:
            return mock_response("MINOR", "DELETE_PERIPHERAL_SURFACE", 0.1, 0.95), 100, None
        if payload["state"]["stage"] == "GROUNDING":
            return mock_response("MATERIAL", "HOLD", 0.9, 0.88), 100, None
        return mock_response("MINOR", "DELETE_PERIPHERAL_SURFACE", 0.05, 0.92), 100, None

    original = ev.call_jev
    ev.call_jev = fake_call
    try:
        results = ev.evaluate(gold, live=True, api_key="test-key-not-real")
    finally:
        ev.call_jev = original

    m = ev.metrics(results)
    check("false MINOR detected", m["false_minor"] == ["20260917-grounding-F4-weather-conflation"],
          str(m["false_minor"]))
    check(
        "high-confidence false MINOR flagged",
        m["high_confidence_false_minor"] == ["20260917-grounding-F4-weather-conflation"],
        str(m["high_confidence_false_minor"]),
    )
    check("no false MATERIAL here", m["false_material"] == [], str(m["false_material"]))
    check("accuracy computed", m["materiality_accuracy"] is not None)
    check("bypassed cases never called", m["route_discipline"]["bypassed_and_never_called"])
    check("no route mismatches", m["route_discipline"]["route_mismatches"] == [],
          str(m["route_discipline"]["route_mismatches"]))
    check("cost is provider reported", m["cost_basis"] == "PROVIDER_REPORTED")
    check("input tokens summed", m["total_input_tokens"] > 0)
    check("latency reported", m["mean_latency_ms"] == 100)
    check(
        "repair distribution covers all options",
        set(m["repair_route_distribution"]) == set(ev.REPAIR_OPTIONS),
    )

    cf = ev.counterfactual(results)
    check(
        "counterfactual excludes hard-condition cases",
        "20260915-safety-entity-italian" not in cf["could_have_continued_to_next_gate"],
    )
    check(
        "counterfactual includes the agreed MINOR case",
        "20260914-safety-entity-italian" in cf["could_have_continued_to_next_gate"],
    )
    check(
        "counterfactual carries the not-published caveat",
        "not a publication outcome" in cf["caveat"],
    )
    return results


def test_repair_scoring(gold):
    """Repair route is scored separately, and only where the label is trusted."""
    print("\n[repair route scoring]")

    scored = [c for c in gold if c["scored_for_repair"]]
    if not scored:
        check("fixture provides a repair-scored case", False)
        return

    # evaluate() walks the list in order and calls only the ADJUDICATE cases,
    # so the nth call is the nth adjudicable case.
    adjudicable = [c for c in gold if c["computed_route"] == "ADJUDICATE"]

    def run(choose):
        pending = list(adjudicable)

        def fake(payload, api_key, timeout=180):
            case = pending.pop(0)
            materiality, repair = choose(case)
            return mock_response(materiality, repair, 0.2), 40, None

        original = ev.call_jev
        ev.call_jev = fake
        try:
            return ev.evaluate(gold, live=True, api_key="k")
        finally:
            ev.call_jev = original

    # Every answer correct on both axes.
    perfect = run(
        lambda c: (
            c["expected_materiality"] or "MINOR",
            c["expected_repair_route"] or "HOLD",
        )
    )
    m = ev.metrics(perfect)
    check("repair accuracy computed", m["repair_route_accuracy"] == 1.0,
          str(m["repair_route_accuracy"]))
    check(
        "repair scoring counts only trusted adjudicated cases",
        m["repair_route_scored"] == len(scored),
        "%s vs %s" % (m["repair_route_scored"], len(scored)),
    )
    check(
        "materiality and repair are scored independently",
        m["scored_cases"] >= m["repair_route_scored"] - len(scored)
        and m["materiality_accuracy"] == 1.0,
    )

    # A model that always answers HOLD: right on the HOLD cases only.
    always_hold = run(lambda c: ("MATERIAL", "HOLD"))
    mh = ev.metrics(always_hold)
    check(
        "a constant repair answer does not score 1.0",
        mh["repair_route_accuracy"] is not None and mh["repair_route_accuracy"] < 1.0,
        str(mh["repair_route_accuracy"]),
    )
    check(
        "constant repair baseline reported",
        mh["constant_repair_route_baseline"] is not None,
    )
    check(
        "collapsing repair onto materiality is detected",
        bool(mh["repair_collapsed_onto_materiality"]),
    )
    check(
        "both constant materiality baselines reported",
        mh["constant_minor_baseline"] is not None
        and mh["constant_material_baseline"] is not None,
    )
    check(
        "a constant materiality answer is measured against its own baseline",
        mh["beats_both_constant_baselines"] is False,
        str(mh["materiality_accuracy"]),
    )
    check(
        "bypassed and untrusted cases are named as excluded",
        set(mh["excluded_from_materiality_accuracy"])
        == {"detector_false_positive", "hard_bypass", "untrusted_label"},
    )
    for record in always_hold:
        if record.get("route") != "ADJUDICATE":
            check(
                "%s never scored" % record["case_id"],
                record.get("materiality_match") is None
                and record.get("repair_route_match") is None,
            )
    return always_hold


def test_no_unpublished_prose():
    """Nothing in the registry is a retained span; the artifacts hold those."""
    print("\n[no unpublished prose committed]")
    for spec in list(cases.GOLD_REGISTRY) + list(cases.REVIEW_QUEUE):
        for key, value in spec.items():
            if not isinstance(value, str):
                continue
            limit = (
                cases._MAX_REGISTRY_FIELD
                if key in ("note", "owner_must_decide")
                else 200
            )
            check(
                "%s.%s within reference length" % (spec["case_id"], key),
                len(value) <= limit,
                "%d chars" % len(value),
            )
    source = open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "jev_shadow_cases.py"),
        encoding="utf-8",
    ).read()
    check("no article body committed", "\n\n## " not in source)
    check("registry validation enforces the limit", "_MAX_REGISTRY_FIELD" in source)


def test_secrets_and_paths(results):
    print("\n[result path and secret hygiene]")
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(ev.__file__)))
    try:
        ev.assert_result_path_outside_repo(os.path.join(repo_root, "automation", "x.json"))
    except RuntimeError:
        check("refuses to write results inside the repo", True)
    else:
        check("refuses to write results inside the repo", False)
    check(
        "default result root is outside the repo",
        ev.assert_result_path_outside_repo(ev.RESULT_ROOT) is True,
    )
    blob = json.dumps(results)
    check("no authorization header stored", "Authorization" not in blob)
    check("no bearer token stored", "Bearer " not in blob)
    check("no api key stored", "test-key-not-real" not in blob)
    check(
        "scrubber removes a key from error text",
        "secret" not in ev._scrub("failed with secret", "secret"),
    )


def test_no_production_imports():
    print("\n[production isolation]")
    source = ""
    for name in ("jev_shadow_eval.py", "jev_shadow_cases.py"):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name),
                  encoding="utf-8") as fh:
            source += fh.read()
    forbidden = [
        "new_engine_production",
        "publication_safety_bridge",
        "import materiality",
        "import continuity",
        "production_orchestrator",
    ]
    for token in forbidden:
        check("does not touch %s" % token, token not in source)
    check("no cron registration", "crontab" not in source)
    check("no telegram", "telegram" not in source.lower())
    check("no jev-latest anywhere", "jev-latest" not in source)
    check("no fallback model", "chat/completions" not in source)


def main():
    root = build_fixture_root()
    try:
        gold = test_extraction(root)
        test_labels(gold)
        test_routing(gold)
        test_review_queue()
        test_registry_validation()
        test_balance(gold)
        test_request_schema(gold)
        test_validation()
        test_malformed_run(gold)
        test_repair_scoring(gold)
        test_no_unpublished_prose()
        results = test_metrics(gold)
        test_secrets_and_paths(results)
        test_no_production_imports()
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("\n%s" % ("FAILED: " + ", ".join(FAILURES) if FAILURES else "ALL OFFLINE TESTS PASS"))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
