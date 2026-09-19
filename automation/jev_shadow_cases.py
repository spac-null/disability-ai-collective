"""Deterministic case extraction for the Jev shadow benchmark.

EXPERIMENTAL / SHADOW ONLY. Nothing here is imported by production code, and
nothing here grants any model publication authority. The module reads retained
run artifacts read-only and builds a bounded editorial-decision state per
finding. It never copies whole drafts, research packs or ledgers.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

ENGINE_ROOT = os.environ.get(
    "CRIPMINDS_ENGINE_ROOT", "/srv/data/cripminds-new-engine-v1"
)

ROUTES = (
    "ADJUDICATE",
    "HARD_BYPASS",
    "DETECTOR_FALSE_POSITIVE",
    "UNLABELED_EXPLORATORY",
)
MATERIALITY_LABELS = ("MINOR", "MATERIAL")
LABEL_AUTHORITIES = ("OWNER", "DOCTRINE_CONFIRMED", "POSTMORTEM_CONFIRMED", "NONE")

# Safety blocking tags that are deterministic hard conditions in their own
# right. NEW_UNSUPPORTED_FACTS is deliberately absent: that is exactly the
# category materiality is allowed to adjudicate.
HARD_SAFETY_BLOCKING_TAGS = frozenset(
    {
        "UNSUPPORTED_NEGATIVES",
        "MACHINE_LANGUAGE",
        "CONTINUITY_ADDED_MATERIAL",
        "SENSORY_ASSERTION",
        "UNAPPROVED_NUMBERS",
    }
)

_RELATION_RE = re.compile(r"editing added \d+ ([A-Z_]+) relation")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


class CaseError(RuntimeError):
    pass


# ---------------------------------------------------------------- artifacts


def run_dir(run_id, root=None):
    return os.path.join(root or ENGINE_ROOT, run_id)


def load_artifact(run_id, name, root=None, required=True):
    path = os.path.join(run_dir(run_id, root), name)
    if not os.path.exists(path):
        if required:
            raise CaseError("missing artifact %s for %s" % (name, run_id))
        return None
    with open(path, "r", encoding="utf-8") as fh:
        if name.endswith(".json"):
            return json.load(fh)
        return fh.read()


def containing_sentence(text, needle):
    """Return the single sentence carrying needle, or '' when absent."""
    if not text or not needle:
        return ""
    for sentence in _SENTENCE_RE.split(text):
        if needle in sentence:
            return " ".join(sentence.split())
    return ""


# ------------------------------------------------------- hard-condition gate


def hard_conditions(stage, safety_audit, manifest, grounding=None,
                    publication_decision=None, finding=None):
    """Deterministic hard conditions that forbid materiality adjudication.

    Scoped by the stage that produced the finding. A Safety-stage condition
    (discarded continuity, an editing-added relation) is not evidence about a
    Grounding-stage finding on the Writer output, which is produced before
    Safety ever runs.
    """
    conds = []
    safety_audit = safety_audit or {}
    manifest = manifest or {}

    def _safety_set():
        found = []
        if safety_audit.get("continuity_discarded"):
            found.append("CONTINUITY_DISCARDED")
        for block in safety_audit.get("blocking") or []:
            tag = str(block).split(":", 1)[0].strip()
            if tag in HARD_SAFETY_BLOCKING_TAGS:
                found.append(tag)
        relations = (safety_audit.get("semantic_delta") or {}).get(
            "added_relation_classes"
        ) or {}
        for name in relations:
            found.append("EDITING_ADDED_RELATION:%s" % name)
        for reason in manifest.get("reasons") or []:
            for match in _RELATION_RE.finditer(str(reason)):
                found.append("EDITING_ADDED_RELATION:%s" % match.group(1))
        return found

    if stage == "SAFETY":
        conds.extend(_safety_set())
    elif stage == "GROUNDING":
        payload = (grounding or {}).get("payload") or {}
        if payload.get("status") != "settled":
            conds.append("GROUNDING_UNSETTLED")
        if finding is not None and finding.get("repairable") is False:
            conds.append("FINDING_NOT_REPAIRABLE")
    elif stage == "READER":
        # Reader findings are adjudicable only once the factual gates have
        # already been settled for the run. A retained PUBLICATION_DECISION is
        # the artifact that records that settlement.
        if publication_decision is None:
            conds.extend(_safety_set())
    else:
        raise CaseError("unknown stage %r" % (stage,))
    return sorted(set(conds))


# ------------------------------------------------------------- bounded state


def _packet_summary(packet):
    packet = packet or {}
    carrier_id = packet.get("primary_carrier") or ""
    carrier_text = ""
    roles = packet.get("evidence_roles") or {}
    if isinstance(roles, dict):
        entry = roles.get(carrier_id)
        if isinstance(entry, str):
            carrier_text = entry
        elif isinstance(entry, dict):
            carrier_text = entry.get("text") or entry.get("role") or ""
    if not carrier_text:
        beats = packet.get("beats") or []
        if beats and isinstance(beats[0], dict):
            carrier_text = beats[0].get("carrier") or ""
    return {
        "primary_carrier_id": carrier_id,
        "primary_carrier": _clip(carrier_text, 400),
        "story_spine": _clip(packet.get("story_spine") or "", 900),
        "crip_turn": _clip(packet.get("crip_turn") or "", 700),
        "ending_move": _clip(packet.get("ending_move") or "", 500),
        "article_type": packet.get("article_type") or "",
    }


def _clip(value, limit):
    value = " ".join(str(value or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _approved_surface_summary(safety_audit, stage_key="continuity_final"):
    audits = (safety_audit or {}).get("audits") or {}
    surface = (audits.get(stage_key) or {}).get("factual_surface") or {}
    return {
        "unapproved_entities": surface.get("unapproved_entities") or [],
        "unapproved_numbers": surface.get("unapproved_numbers") or [],
        "unapproved_sensory": surface.get("unapproved_sensory") or [],
        "hard_factual_ok": (audits.get(stage_key) or {}).get("hard_factual_ok"),
    }


def build_state(case, artifacts):
    """Bounded editorial state for one finding. No whole drafts, no packs."""
    stage = case["stage"]
    locator = case["locator"]
    safety_audit = artifacts.get("SAFETY_AUDIT")
    manifest = artifacts.get("MANIFEST")
    packet = artifacts.get("WRITER_PACKET")

    state = {
        "run_id": case["run_id"],
        "date": case["date"],
        "stage": stage,
        "finding_type": case["finding_type"],
        "packet": _packet_summary(packet),
    }

    if stage == "SAFETY":
        entity = locator["entity"]
        prose = artifacts.get("CONTINUITY_FINAL") or ""
        state["disputed_span"] = entity
        state["containing_sentence"] = containing_sentence(prose, entity)
        state["finding_detail"] = (
            "Safety reports factual surface the frozen packet never granted: "
            "the entity %r appears in the edited prose." % entity
        )
        state["approved_factual_surface"] = _approved_surface_summary(safety_audit)
    elif stage == "GROUNDING":
        finding = locator["_finding"]
        state["disputed_span"] = _clip(finding.get("quote") or "", 600)
        state["containing_sentence"] = _clip(finding.get("quote") or "", 600)
        state["finding_detail"] = _clip(finding.get("why") or "", 1200)
        state["grounding_classification"] = finding.get("classification")
        state["repair_available_from_approved_material"] = bool(
            finding.get("suggested_patch")
        )
        state["suggested_patch_from_approved_material"] = _clip(
            finding.get("suggested_patch") or "", 400
        )
    elif stage == "READER":
        dimension = locator["dimension"]
        decision = artifacts.get("PUBLICATION_DECISION") or {}
        entry = (decision.get("reader_findings") or {}).get(dimension) or {}
        passages = entry.get("passages") or []
        state["disputed_span"] = _clip(" / ".join(passages), 900)
        state["containing_sentence"] = _clip(passages[0] if passages else "", 600)
        state["finding_detail"] = _clip(entry.get("note") or "", 600)
        state["reader_dimension"] = dimension
        state["reader_verdict"] = entry.get("verdict")
    else:
        raise CaseError("unknown stage %r" % (stage,))

    state["deterministic_hard_conditions"] = case["hard_conditions"]
    state["deterministic_hard_conditions_present"] = bool(case["hard_conditions"])
    return state


def state_hash(state):
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ------------------------------------------------------------ gold registry


GOLD_REGISTRY = [
    {
        "case_id": "20260914-safety-entity-italian",
        "run_id": "production-20260914T070213Z-d20b3807",
        "date": "2026-09-14",
        "stage": "SAFETY",
        "finding_type": "NEW_UNSUPPORTED_FACTS:entity",
        "locator": {"kind": "safety_entity", "entity": "Italian"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "label_authority": "DOCTRINE_CONFIRMED",
        "note": "Canonical MINOR case: removing 'in Italian' leaves carrier, "
                "chronology, causality, allegation, argument and conclusion intact.",
    },
    {
        "case_id": "20260915-safety-entity-italian",
        "run_id": "production-20260915T072045Z-40294a3a",
        "date": "2026-09-15",
        "stage": "SAFETY",
        "finding_type": "NEW_UNSUPPORTED_FACTS:entity",
        "locator": {"kind": "safety_entity", "entity": "Italian"},
        "expected_route": "HARD_BYPASS",
        "expected_materiality": None,
        "label_authority": "DOCTRINE_CONFIRMED",
        "note": "Same unsupported entity, but the run also discarded continuity "
                "and editing added a CAUSAL relation. Not a materiality rescue.",
    },
    {
        "case_id": "20260916-continuity-added-entity-cem",
        "run_id": "production-20260916T070723Z-5a4e7891",
        "date": "2026-09-16",
        "stage": "SAFETY",
        "finding_type": "CONTINUITY_ADDED_MATERIAL:entity",
        "locator": {"kind": "safety_entity", "entity": "Cem"},
        "expected_route": "DETECTOR_FALSE_POSITIVE",
        "expected_materiality": None,
        "label_authority": "POSTMORTEM_CONFIRMED",
        "forced_route": "DETECTOR_FALSE_POSITIVE",
        "note": "Audit proved a deterministic semantic_delta defect: Cem Behar was "
                "supported throughout; Prose Finish only moved the name from "
                "sentence-initial to sentence-medial position. The correct action "
                "is detector repair, never model materiality.",
    },
    {
        "case_id": "20260917-grounding-F2-macaulay-linkage",
        "run_id": "production-20260917T070213Z-67554ae5",
        "date": "2026-09-17",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F2"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "label_authority": "POSTMORTEM_CONFIRMED",
        "note": "No source places the recording in the Macaulay archive; title, "
                "opening and crip_turn depended on the linkage.",
    },
    {
        "case_id": "20260917-grounding-F4-weather-conflation",
        "run_id": "production-20260917T070213Z-67554ae5",
        "date": "2026-09-17",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F4"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "label_authority": "POSTMORTEM_CONFIRMED",
        "note": "70 km/h wind and -25C belong to arrival at base Artigas, not the "
                "ten-kilometre walk. Correction changes what the reader believes "
                "happened.",
    },
    {
        "case_id": "20260919-safety-unsupported-negatives",
        "run_id": "production-20260919T070300Z-faa849c8",
        "date": "2026-09-19",
        "stage": "SAFETY",
        "finding_type": "UNSUPPORTED_NEGATIVES",
        "locator": {"kind": "safety_entity", "entity": "malnutrition"},
        "expected_route": "HARD_BYPASS",
        "expected_materiality": None,
        "label_authority": "DOCTRINE_CONFIRMED",
        "note": "Sensory hard finding, editing-added NEGATION relation, discarded "
                "continuity and unsupported negatives. Overall run stays HOLD.",
    },
]

# Owner-adjudicated Reader findings from the published SFMOMA article. Labels
# are taken verbatim from the retained PUBLICATION_DECISION.json; none are
# invented here.
SFMOMA_RUN_ID = "production-20260913T083824Z-f83f4b8a"


def sfmoma_registry(root=None):
    decision = load_artifact(
        SFMOMA_RUN_ID, "PUBLICATION_DECISION.json", root=root, required=False
    )
    if not decision:
        return []
    labels = decision.get("reader_materiality_classification") or {}
    cases = []
    for dimension in sorted(labels):
        label = labels[dimension]
        if label not in MATERIALITY_LABELS:
            continue
        cases.append(
            {
                "case_id": "20260913-reader-%s" % dimension.lower(),
                "run_id": SFMOMA_RUN_ID,
                "date": "2026-09-13",
                "stage": "READER",
                "finding_type": "READER_%s" % dimension,
                "locator": {"kind": "reader_dimension", "dimension": dimension},
                "expected_route": "ADJUDICATE",
                "expected_materiality": label,
                "label_authority": "OWNER",
                "note": "Owner-adjudicated at publication "
                        "(%s)." % decision.get("publication_status", ""),
            }
        )
    return cases


# --------------------------------------------------------------- assembly


_ARTIFACT_MAP = {
    "SAFETY_AUDIT": ("SAFETY_AUDIT.json", True),
    "MANIFEST": ("MANIFEST.json", True),
    "WRITER_PACKET": ("WRITER_PACKET.json", False),
    "GROUNDING_FINDINGS": ("GROUNDING_FINDINGS.json", False),
    "PUBLICATION_DECISION": ("PUBLICATION_DECISION.json", False),
    "CONTINUITY_FINAL": ("CONTINUITY_FINAL.md", False),
}


def load_run_artifacts(run_id, root=None):
    out = {}
    for key, (name, required) in _ARTIFACT_MAP.items():
        out[key] = load_artifact(run_id, name, root=root, required=required)
    return out


def resolve_case(spec, root=None, artifacts=None):
    """Attach artifacts, hard conditions, computed route and bounded state."""
    case = dict(spec)
    artifacts = artifacts if artifacts is not None else load_run_artifacts(
        case["run_id"], root=root
    )
    locator = dict(case["locator"])

    finding = None
    if locator["kind"] == "grounding_finding":
        grounding = artifacts.get("GROUNDING_FINDINGS") or {}
        findings = (grounding.get("payload") or {}).get("findings") or []
        for item in findings:
            if item.get("id") == locator["finding_id"]:
                finding = item
                break
        if finding is None:
            raise CaseError(
                "grounding finding %s absent from %s"
                % (locator["finding_id"], case["run_id"])
            )
        locator["_finding"] = finding

    case["locator"] = locator
    case["hard_conditions"] = hard_conditions(
        case["stage"],
        artifacts.get("SAFETY_AUDIT"),
        artifacts.get("MANIFEST"),
        grounding=artifacts.get("GROUNDING_FINDINGS"),
        publication_decision=artifacts.get("PUBLICATION_DECISION"),
        finding=finding,
    )

    if case.get("forced_route") == "DETECTOR_FALSE_POSITIVE":
        case["computed_route"] = "DETECTOR_FALSE_POSITIVE"
        case["route_reason"] = [
            "postmortem-confirmed deterministic detector false positive"
        ]
    elif case["hard_conditions"]:
        case["computed_route"] = "HARD_BYPASS"
        case["route_reason"] = list(case["hard_conditions"])
    else:
        case["computed_route"] = "ADJUDICATE"
        case["route_reason"] = []

    case["jev_called"] = case["computed_route"] == "ADJUDICATE"
    case["source_artifacts"] = sorted(
        name for key, (name, _r) in _ARTIFACT_MAP.items() if artifacts.get(key)
    )
    case["state"] = build_state(case, artifacts)
    case["input_hash"] = state_hash(case["state"])
    case["locator"] = {k: v for k, v in locator.items() if not k.startswith("_")}
    return case


def gold_cases(root=None):
    specs = list(GOLD_REGISTRY) + sfmoma_registry(root=root)
    return [resolve_case(spec, root=root) for spec in specs]


# ------------------------------------------------------ exploratory cases


def recent_run_ids(limit, root=None):
    base = root or ENGINE_ROOT
    names = [
        n
        for n in os.listdir(base)
        if n.startswith("production-") and os.path.isdir(os.path.join(base, n))
    ]
    return sorted(names)[-limit:]


def exploratory_cases(run_ids, root=None):
    """Unlabelled findings from recent runs. Never scored against gold."""
    cases = []
    for run_id in run_ids:
        try:
            artifacts = load_run_artifacts(run_id, root=root)
        except CaseError:
            continue
        specs = []
        audits = (artifacts.get("SAFETY_AUDIT") or {}).get("audits") or {}
        surface = (audits.get("continuity_final") or {}).get("factual_surface") or {}
        for entity in surface.get("unapproved_entities") or []:
            specs.append(
                {
                    "case_id": "%s-safety-entity-%s" % (run_id[11:19], entity.lower()),
                    "run_id": run_id,
                    "date": "%s-%s-%s" % (run_id[11:15], run_id[15:17], run_id[17:19]),
                    "stage": "SAFETY",
                    "finding_type": "NEW_UNSUPPORTED_FACTS:entity",
                    "locator": {"kind": "safety_entity", "entity": entity},
                    "expected_route": "UNLABELED_EXPLORATORY",
                    "expected_materiality": None,
                    "label_authority": "NONE",
                }
            )
        grounding = artifacts.get("GROUNDING_FINDINGS") or {}
        for item in (grounding.get("payload") or {}).get("findings") or []:
            if item.get("classification") != "TRUE_UNSUPPORTED":
                continue
            specs.append(
                {
                    "case_id": "%s-grounding-%s" % (run_id[11:19], item.get("id")),
                    "run_id": run_id,
                    "date": "%s-%s-%s" % (run_id[11:15], run_id[15:17], run_id[17:19]),
                    "stage": "GROUNDING",
                    "finding_type": "TRUE_UNSUPPORTED",
                    "locator": {
                        "kind": "grounding_finding",
                        "finding_id": item.get("id"),
                    },
                    "expected_route": "UNLABELED_EXPLORATORY",
                    "expected_materiality": None,
                    "label_authority": "NONE",
                }
            )
        for spec in specs:
            try:
                cases.append(resolve_case(spec, root=root, artifacts=artifacts))
            except CaseError:
                continue
    gold_keys = {
        (spec["run_id"], json.dumps(spec["locator"], sort_keys=True))
        for spec in GOLD_REGISTRY
    }
    return [
        c
        for c in cases
        if (c["run_id"], json.dumps(c["locator"], sort_keys=True)) not in gold_keys
    ]
