"""Deterministic case extraction for the Jev shadow benchmark.

EXPERIMENTAL / SHADOW ONLY. Nothing here is imported by production code, and
nothing here grants any model publication authority. The module reads retained
run artifacts read-only and builds a bounded editorial-decision state per
finding. It never copies whole drafts, research packs or ledgers.

TWO INDEPENDENT GOLD LABELS PER CASE.

  expected_materiality   MINOR | MATERIAL -- CONSEQUENCE. If the disputed
                         element were corrected or removed, would the reader
                         understand the story materially differently?

  expected_repair_route  PASS_THROUGH | DELETE_PERIPHERAL_SURFACE |
                         TARGETED_SUPPORTED_REPAIR | HOLD -- MECHANISM. What
                         would it take to put the article right, given that no
                         new research and no new facts may be introduced?

They are not the same question and they do not track each other. A MATERIAL
finding can still be repairable from already-approved material (17 Sep F4: the
weather belongs to the arrival day, and the source says so). A MINOR finding
can still be best deleted rather than passed through (14 Sep "in Italian").

NO PROSE LIVES IN THIS FILE. Registry entries carry artifact references,
locators and labels. Every disputed span and every sentence of context is read
from the retained artifact at resolve time and clipped. `validate_registry`
enforces that, so an unpublished draft cannot enter the repository through a
fixture.
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
REPAIR_ROUTES = (
    "PASS_THROUGH",
    "DELETE_PERIPHERAL_SURFACE",
    "TARGETED_SUPPORTED_REPAIR",
    "HOLD",
)
LABEL_AUTHORITIES = (
    "OWNER",
    "POSTMORTEM_CONFIRMED",
    "DOCTRINE_DIRECT",
    "UNRESOLVED",
    "NONE",
)
# Only these may enter the trusted gold set and be scored.
TRUSTED_AUTHORITIES = ("OWNER", "POSTMORTEM_CONFIRMED", "DOCTRINE_DIRECT")

STAGES = ("SAFETY", "GROUNDING", "READER", "OWNER_REPAIR", "FACT_CHECK")

# The 13 Sep publication. Named because it is the article the first benchmark
# was accidentally built out of, and the one the per-article cap exists for.
SFMOMA_RUN_ID = "production-20260913T083824Z-f83f4b8a"

# No single article may dominate the gold set the way the 13 Sep SFMOMA run
# dominated the first benchmark (9 of 12 scored cases from one publication).
ARTICLE_CAP = 3

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


class RegistryError(RuntimeError):
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
                    publication_decision=None, finding=None,
                    owner_repair=None, fact_check_adjudication=None):
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
    elif stage == "OWNER_REPAIR":
        # An owner copy-desk repair is itself the record that the factual gates
        # were settled by a human with authority. Without that artifact there
        # is nothing to adjudicate against.
        if owner_repair is None:
            conds.append("NO_OWNER_REPAIR_RECORD")
        elif not owner_repair.get("owner_authorized"):
            conds.append("OWNER_REPAIR_NOT_AUTHORIZED")
    elif stage == "FACT_CHECK":
        if fact_check_adjudication is None:
            conds.append("NO_FACT_CHECK_ADJUDICATION")
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


def _article_text(artifacts):
    for key in ("CONTINUITY_FINAL", "ARTICLE_FINAL"):
        text = artifacts.get(key)
        if text:
            return text
    return ""


def build_state(case, artifacts):
    """Bounded editorial state for one finding. No whole drafts, no packs."""
    stage = case["stage"]
    locator = case["locator"]
    safety_audit = artifacts.get("SAFETY_AUDIT")
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
        prose = _article_text(artifacts)
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
        entry = (decision.get("reader_findings") or {}).get(dimension)
        if isinstance(entry, str):
            entry = {"note": entry, "passages": [], "verdict": "HOLD"}
        entry = entry or {}
        passages = entry.get("passages") or []
        state["disputed_span"] = _clip(" / ".join(passages), 900)
        state["containing_sentence"] = _clip(passages[0] if passages else "", 600)
        state["finding_detail"] = _clip(entry.get("note") or "", 600)
        state["reader_dimension"] = dimension
        state["reader_verdict"] = entry.get("verdict")
    elif stage == "OWNER_REPAIR":
        finding_id = locator["finding_id"]
        repair = artifacts.get("OWNER_COPYDESK_REPAIR") or {}
        before = (repair.get("exact_before") or {}).get(finding_id, "")
        after = (repair.get("exact_after") or {}).get(finding_id, "")
        if not before:
            for extra in repair.get("additional_owner_authorized_repairs") or []:
                if extra.get("finding_id") == finding_id:
                    before = extra.get("exact_before") or ""
                    after = extra.get("exact_after") or ""
                    break
        if not before:
            raise CaseError(
                "owner repair %s absent from %s" % (finding_id, case["run_id"])
            )
        state["disputed_span"] = _clip(before, 600)
        state["containing_sentence"] = _clip(before, 600)
        state["finding_detail"] = _clip(repair.get("reason") or "", 600)
        state["repair_available_from_approved_material"] = bool(after)
        state["suggested_patch_from_approved_material"] = _clip(after, 400)
    elif stage == "FACT_CHECK":
        finding_id = locator["finding_id"]
        adj = artifacts.get("FACT_CHECK_ADJUDICATION") or {}
        entry = None
        for item in adj.get("findings") or []:
            if item.get("finding_id") == finding_id:
                entry = item
                break
        if entry is None:
            raise CaseError(
                "fact check finding %s absent from %s"
                % (finding_id, case["run_id"])
            )
        state["disputed_span"] = _clip(entry.get("article_span") or "", 600)
        state["containing_sentence"] = _clip(entry.get("article_span") or "", 600)
        state["finding_detail"] = _clip(entry.get("reason") or "", 1200)
        state["fact_check_raw_status"] = entry.get("raw_status")
        state["fact_check_adjudication"] = entry.get("adjudication")
        state["primary_source_identity"] = _clip(
            entry.get("document_identity") or "", 300
        )
    else:
        raise CaseError("unknown stage %r" % (stage,))

    state["deterministic_hard_conditions"] = case["hard_conditions"]
    state["deterministic_hard_conditions_present"] = bool(case["hard_conditions"])
    return state


def state_hash(state):
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ------------------------------------------------------------ gold registry
#
# `note` records WHY the label is what it is, and `label_authority` records WHO
# it rests on:
#
#   OWNER                a human with publication authority recorded the label
#                        in a retained artifact (PUBLICATION_DECISION,
#                        OWNER_COPYDESK_REPAIR, FACT_CHECK_ADJUDICATION)
#   POSTMORTEM_CONFIRMED a committed postmortem adjudicated this exact finding
#   DOCTRINE_DIRECT      the doctrine in new_engine_v1/materiality.py decides it
#                        without residue: the disputed element is or is not one
#                        of the hard-list categories, and the counterfactual is
#                        not arguable
#
# `independence_key` is the ARTICLE, not the run. Two runs on the same subject
# share a key so the per-article cap is not defeated by a re-run.

GOLD_REGISTRY = [
    # ---------------------------------------------------------------- MINOR
    {
        "case_id": "20260905-grounding-F2-ada-gloss",
        "run_id": "production-20260905T073611Z-8f73c769",
        "date": "2026-09-05",
        "independence_key": "chinati-specification",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F2"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "DELETE_PERIPHERAL_SURFACE",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "An explanatory appositive on 'an ADA-compliant walking path', "
                "which the anchor does grant. Strike the appositive and the "
                "sentence still says a compliant path is being built: no "
                "carrier, chronology, causality, allegation, argument or "
                "conclusion moves.",
    },
    {
        "case_id": "20260905-grounding-F4-museum-standard-gloss",
        "run_id": "production-20260905T073611Z-8f73c769",
        "date": "2026-09-05",
        "independence_key": "chinati-specification",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F4"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "A gloss on the sources' own phrase 'a static, museum-standard "
                "environment'. The gloss cannot simply vanish -- it is the "
                "object of 'rather than chasing' -- but the sources supply the "
                "phrase that replaces it.",
    },
    {
        "case_id": "20260905-grounding-F3-constraint-particulars",
        "run_id": "production-20260905T150712Z-94a83312",
        "date": "2026-09-05",
        "independence_key": "laiout-test-fit",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F3"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "DELETE_PERIPHERAL_SURFACE",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "Invented regulatory particulars in a sentence whose point -- "
                "compliance is settled before design -- is already carried by "
                "Carpinteiro's quoted list in the sentence before it. The "
                "particulars can be struck and the paragraph still reads.",
    },
    {
        "case_id": "20260905-grounding-F5-call-to-action-addressee",
        "run_id": "production-20260905T155110Z-3ab05fcf",
        "date": "2026-09-05",
        "independence_key": "eight-resumes",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F5"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "DELETE_PERIPHERAL_SURFACE",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "An added attribute of a document ('addressed to business'). "
                "Remove it and Call to Action No. 92 on economic "
                "reconciliation is still the document the article cites.",
    },
    {
        "case_id": "20260905-grounding-F1-acrossrca-scope",
        "run_id": "production-20260905T213559Z-8d2d1a38",
        "date": "2026-09-05",
        "independence_key": "rca-schools",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "The draft widens 'all students across our MA programmes' to "
                "'students across the whole College'. The article's subject is "
                "the school merger; who takes AcrossRCA is a subsidiary fact, "
                "and the source states the correct scope verbatim.",
    },
    {
        "case_id": "20260907-grounding-F1-grade-one-gloss",
        "run_id": "production-20260907T173433Z-ab65bb22",
        "date": "2026-09-07",
        "independence_key": "finsbury-health-centre",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "'Exceptional interest' is an outside-knowledge gloss on the "
                "listing grade; the list entry's own words are 'special "
                "architectural or historic interest'. The carrier is the ramp "
                "at Pine Street, not the grading vocabulary.",
    },
    {
        "case_id": "20260909-grounding-F6-current-locations-field",
        "run_id": "production-20260909T070025Z-8d2d1a38",
        "date": "2026-09-09",
        "independence_key": "rca-schools",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F6"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "A form-field label ('current locations' for 'Current "
                "Location') and its position on the page. Copy-desk factual "
                "imprecision: the three campuses it lists are unchanged.",
    },
    {
        "case_id": "20260909-grounding-F1-ngss-gloss",
        "run_id": "production-20260909T232121Z-431ceea4",
        "date": "2026-09-09",
        "independence_key": "plastic-expelled",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "DELETE_PERIPHERAL_SURFACE",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "The sources grant 'aligned with NGSS standards' and the "
                "expansion of the acronym. Only the appended world-claim about "
                "state adoption is unsupported, and it can simply disappear. "
                "Structurally the same case as 14 Sep 'in Italian'.",
    },
    {
        "case_id": "20260910-grounding-F1-memorial-notice-venue",
        "run_id": "production-20260910T000254Z-4314d310",
        "date": "2026-09-10",
        "independence_key": "cain-todd",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "DELETE_PERIPHERAL_SURFACE",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "Publisher and date of a memorial notice, inside a "
                "biographical paragraph of posts and awards. The article is "
                "about one word in Todd's last paper; strike the venue and the "
                "date and the attribution to Teroni, which the anchor does "
                "grant, still stands.",
    },
    {
        "case_id": "20260914-safety-entity-italian",
        "run_id": "production-20260914T070213Z-d20b3807",
        "date": "2026-09-14",
        "independence_key": "trieste-csm",
        "stage": "SAFETY",
        "finding_type": "NEW_UNSUPPORTED_FACTS:entity",
        "locator": {"kind": "safety_entity", "entity": "Italian"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "DELETE_PERIPHERAL_SURFACE",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "The canonical MINOR case, named in the doctrine module "
                "itself: removing 'in Italian' leaves carrier, chronology, "
                "causality, allegation, argument and conclusion intact.",
    },
    {
        "case_id": "20260913-reader-opening",
        "run_id": "production-20260913T083824Z-f83f4b8a",
        "date": "2026-09-13",
        "independence_key": "sfmoma-creative-growth",
        "stage": "READER",
        "finding_type": "READER_OPENING",
        "locator": {"kind": "reader_dimension", "dimension": "OPENING"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "OWNER",
        "verify_against_publication_decision": True,
        "note": "Owner-adjudicated MINOR at publication. Showing the drawing "
                "more directly is a rewrite from material already approved; "
                "the opening cannot simply be deleted.",
    },
    {
        "case_id": "20260913-owner-repair-F1-attribution",
        "run_id": "production-20260913T083824Z-f83f4b8a",
        "date": "2026-09-13",
        "independence_key": "sfmoma-creative-growth",
        "stage": "OWNER_REPAIR",
        "finding_type": "OWNER_COPYDESK_REPAIR",
        "locator": {"kind": "owner_repair_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MINOR",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "OWNER",
        "note": "OWNER_COPYDESK_REPAIR records the owner's own reason: "
                "'nonmaterial factual-scope/attribution imprecisions with "
                "exact source-supported Grounder patches'. Both labels are "
                "the owner's, not this file's.",
    },
    # ------------------------------------------------------------- MATERIAL
    {
        "case_id": "20260903-grounding-F2-derived-litres",
        "run_id": "production-20260903T135702Z-3ea6156a",
        "date": "2026-09-03",
        "independence_key": "river-water-treatment",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F2"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "A material number the sources never state, reached by "
                "subtraction, and asserting as exact what the source calls "
                "'most'. Unapproved numbers are on the doctrine's hard list "
                "without residue. The source's own word supplies the repair.",
    },
    {
        "case_id": "20260905-grounding-F1-warning-framing",
        "run_id": "production-20260905T065626Z-5522ac42",
        "date": "2026-09-05",
        "independence_key": "sauna-theatre",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "HOLD",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "The sentence IS the crip turn: access fields describe getting "
                "in, while participation requirements 'are printed as a "
                "warning'. The listing's Warnings field carries no such text. "
                "Corrected to 'Additional Information' the contrast collapses "
                "and the paragraph has to be rethought, not patched.",
    },
    {
        "case_id": "20260905-grounding-F1-aquinas-quotation",
        "run_id": "production-20260905T094701Z-e7b61df1",
        "date": "2026-09-05",
        "independence_key": "aquinas-syllabus",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "Authorial paraphrase reformulated into quoted clauses, "
                "attributing a verbal form to Aquinas that no source contains. "
                "A central quotation is on the doctrine's hard list. The sense "
                "survives once the quotation marks come off.",
    },
    {
        "case_id": "20260905-grounding-F2-single-line-contradiction",
        "run_id": "production-20260905T155110Z-3ab05fcf",
        "date": "2026-09-05",
        "independence_key": "eight-resumes",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F2"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "HOLD",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "The source says the resumes differed in MULTIPLE identity "
                "signals; the draft says one line. The title 'Eight resumes, "
                "one line' is built on the error and the draft's own next "
                "paragraph contradicts it. Thesis surface: not a span repair.",
    },
    {
        "case_id": "20260905-grounding-F1-study-misattribution",
        "run_id": "production-20260905T221120Z-628ef133",
        "date": "2026-09-05",
        "independence_key": "freelance-ai-losses",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "Named authors, a publication year and two statistics from a "
                "2025 Brookings piece presented as the findings of a different, "
                "unnamed 2026 study. Wrong central attribution plus material "
                "numbers. Both sources are in the pack, so it can be split.",
    },
    {
        "case_id": "20260907-grounding-F2-teenagers-identity",
        "run_id": "production-20260907T160137Z-831b0d44",
        "date": "2026-09-07",
        "independence_key": "brailled-it",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F2"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "One unsupported word, and it is MATERIAL: the sources say "
                "'kids' and the anchor names a 10-year-old among the "
                "filmmakers. It states the identity of the central persons and "
                "the source record contradicts it. The paired opposite of "
                "14 Sep 'in Italian'.",
    },
    {
        "case_id": "20260907-grounding-F4-finished-cut-overstated",
        "run_id": "production-20260907T160137Z-831b0d44",
        "date": "2026-09-07",
        "independence_key": "brailled-it",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F4"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "Beyond the age category, this asserts that nine filmed the "
                "released film when the source says nine shot footage and the "
                "cut was narrowed to three. What the reader believes the film "
                "is changes.",
    },
    {
        "case_id": "20260909-grounding-F1-index-conflation",
        "run_id": "production-20260909T223331Z-83161dd1",
        "date": "2026-09-09",
        "independence_key": "heat-index-somerstown",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "Two distinct indices fused into one. The article's carrier is "
                "the number on a 30-metre square and its crip turn is what "
                "that number measures, so the conflation invents the meaning "
                "of the central object. Both indices are described separately "
                "in approved material.",
    },
    {
        "case_id": "20260910-grounding-F1-review-route-invented",
        "run_id": "production-20260910T075720Z-90687a49",
        "date": "2026-09-10",
        "independence_key": "ppa-ai-authorship",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "The dek asserts a procedural event about this manuscript -- "
                "acceptance through triple-anonymous review -- that no source "
                "states about it. Thesis surface, and an invented event. "
                "'Published' is granted and carries the dek.",
    },
    {
        "case_id": "20260910-grounding-F1-june-and-attendance",
        "run_id": "production-20260910T110024Z-1906b00c",
        "date": "2026-09-10",
        "independence_key": "three-mayors-heat",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "DOCTRINE_DIRECT",
        "note": "An invented month, and an attendance claim the anchor cuts "
                "against by placing Paris's mayor on his own crisis response "
                "at the same time. Chronology and who was in the room. The "
                "anchor's 'this summer' and hedged attendance repair it.",
    },
    {
        "case_id": "20260917-grounding-F2-macaulay-linkage",
        "run_id": "production-20260917T070213Z-67554ae5",
        "date": "2026-09-17",
        "independence_key": "elephant-seal",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F2"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "HOLD",
        "label_authority": "POSTMORTEM_CONFIRMED",
        "note": "Commit f52a66c: 'The title is the claim, the opening sentence "
                "is the claim... Removing them removes the article. MATERIAL.' "
                "No source places the recording in the archive, so there is "
                "nothing in approved material to rebuild it from.",
    },
    {
        "case_id": "20260917-grounding-F4-weather-conflation",
        "run_id": "production-20260917T070213Z-67554ae5",
        "date": "2026-09-17",
        "independence_key": "elephant-seal",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F4"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": "MATERIAL",
        "expected_repair_route": "TARGETED_SUPPORTED_REPAIR",
        "label_authority": "POSTMORTEM_CONFIRMED",
        "note": "MATERIAL by the same postmortem: 70 km/h and -25C belong to "
                "arrival at base Artigas, not the ten-kilometre walk. But the "
                "repair route differs from F2 -- S3 describes the walks and "
                "the trip, so the passage can be rebuilt without the "
                "conflation. MATERIAL does not imply HOLD.",
    },
    # --------------------------------------- route discipline, not materiality
    {
        "case_id": "20260915-safety-entity-italian",
        "run_id": "production-20260915T072045Z-40294a3a",
        "date": "2026-09-15",
        "independence_key": "lombardy-comune",
        "stage": "SAFETY",
        "finding_type": "NEW_UNSUPPORTED_FACTS:entity",
        "locator": {"kind": "safety_entity", "entity": "Italian"},
        "expected_route": "HARD_BYPASS",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "DOCTRINE_DIRECT",
        "note": "Same unsupported entity as 14 Sep, but the run also discarded "
                "continuity and editing added a CAUSAL relation. Not a "
                "materiality rescue; never reaches a model.",
    },
    {
        "case_id": "20260919-safety-unsupported-negatives",
        "run_id": "production-20260919T070300Z-faa849c8",
        "date": "2026-09-19",
        "independence_key": "malnutrition-negatives",
        "stage": "SAFETY",
        "finding_type": "UNSUPPORTED_NEGATIVES",
        "locator": {"kind": "safety_entity", "entity": "malnutrition"},
        "expected_route": "HARD_BYPASS",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "DOCTRINE_DIRECT",
        "note": "Sensory hard finding, editing-added NEGATION relation, "
                "discarded continuity and unsupported negatives. The run stays "
                "HOLD and nothing is asked of any model.",
    },
    {
        "case_id": "20260916-continuity-added-entity-cem",
        "run_id": "production-20260916T070723Z-5a4e7891",
        "date": "2026-09-16",
        "independence_key": "cem-behar",
        "stage": "SAFETY",
        "finding_type": "CONTINUITY_ADDED_MATERIAL:entity",
        "locator": {"kind": "safety_entity", "entity": "Cem"},
        "expected_route": "DETECTOR_FALSE_POSITIVE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "POSTMORTEM_CONFIRMED",
        "forced_route": "DETECTOR_FALSE_POSITIVE",
        "note": "Commit f52a66c proved a deterministic semantic_delta defect: "
                "Cem Behar was supported throughout and Prose Finish only "
                "moved the name off the front of its sentence. Detector "
                "repair, never model materiality.",
    },
    {
        "case_id": "20260913-safety-entity-museum",
        "run_id": "production-20260913T083824Z-f83f4b8a",
        "date": "2026-09-13",
        "independence_key": "sfmoma-creative-growth",
        "stage": "SAFETY",
        "finding_type": "NEW_UNSUPPORTED_FACTS:entity",
        "locator": {"kind": "safety_entity", "entity": "Museum"},
        "expected_route": "DETECTOR_FALSE_POSITIVE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "POSTMORTEM_CONFIRMED",
        "forced_route": "DETECTOR_FALSE_POSITIVE",
        "note": "Commit 3802565: 'San Francisco Museum of Modern Art' appears "
                "verbatim in three frozen Ledger facts; the audit compared "
                "prose against the packet render alone. The token was never an "
                "unsupported fact, so it is not a materiality question.",
    },
    {
        "case_id": "20260912-factcheck-C04-primary-verified",
        "run_id": "fast-lane-v1-fresh-asl-whitehouse-20260912",
        "date": "2026-09-12",
        "independence_key": "asl-whitehouse",
        "stage": "FACT_CHECK",
        "finding_type": "CONTRADICTED",
        "locator": {"kind": "fact_check_finding", "finding_id": "C04"},
        "expected_route": "DETECTOR_FALSE_POSITIVE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "OWNER",
        "forced_route": "DETECTOR_FALSE_POSITIVE",
        "note": "Fact Check reported CONTRADICTED against a secondary "
                "paraphrase. FACT_CHECK_ADJUDICATION records a byte-level "
                "normalized match against the primary court document, with "
                "source hash retained. The quote was right; the comparison was "
                "wrong.",
    },
]


# Cases the retained evidence does NOT settle. They are never scored, never
# counted in balance, and never sent to a model as gold. They exist so the
# owner can decide them, and so the reason each is open is written down.
REVIEW_QUEUE = [
    {
        "case_id": "20260903-grounding-F1-gough-quote-graft",
        "run_id": "production-20260903T070032Z-ec372f9c",
        "date": "2026-09-03",
        "independence_key": "gough-theory",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "UNRESOLVED",
        "owner_must_decide": "Quotation integrity against consequence. The "
                             "draft grafts 'had' onto a verbatim 'hasn't', "
                             "which is a corrupted quotation -- a hard-list "
                             "category -- but the corrupted and correct "
                             "renderings mean the same thing to a reader. "
                             "Does quote corruption make a finding MATERIAL "
                             "even when meaning is preserved?",
    },
    {
        "case_id": "20260910-grounding-F1-quoted-string-not-verbatim",
        "run_id": "production-20260910T102814Z-ab65bb22",
        "date": "2026-09-10",
        "independence_key": "finsbury-health-centre",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "UNRESOLVED",
        "owner_must_decide": "The same question in its cleanest form: the "
                             "Grounder itself says the sense is a fair "
                             "reading and only the quoted string is absent "
                             "from the statutory entry. Same shape as the "
                             "Gough case; they should be decided together.",
    },
    {
        "case_id": "20260910-grounding-F1-invented-publisher",
        "run_id": "production-20260910T084202Z-09d602f1",
        "date": "2026-09-10",
        "independence_key": "mint-tin-plein-air",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "UNRESOLVED",
        "owner_must_decide": "Is a fabricated attribution to a real, named "
                             "publication MINOR when the observation it "
                             "carries is peripheral? Consequence doctrine "
                             "says MINOR; an invented named source may be a "
                             "category the publication refuses to downgrade "
                             "regardless of consequence.",
    },
    {
        "case_id": "20260830-grounding-F1-citation-grouping",
        "run_id": "production-20260830T070004Z-c3f0148f",
        "date": "2026-08-30",
        "independence_key": "durham-light-art",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "UNRESOLVED",
        "owner_must_decide": "A citation-mechanics defect: every name is "
                             "supported, but one is grouped under a citation "
                             "that does not cover it. Is a wrong citation "
                             "boundary a materiality question at all, or a "
                             "third category alongside detector defects?",
    },
    {
        "case_id": "20260905-grounding-F1-one-signal-per-resume",
        "run_id": "production-20260905T155110Z-3ab05fcf",
        "date": "2026-09-05",
        "independence_key": "eight-resumes",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F1"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "UNRESOLVED",
        "owner_must_decide": "Held out of gold only by the per-article cap, "
                             "not by doubt: invented study construction (one "
                             "identity signal per resume) reads MATERIAL. "
                             "Confirm, and it can replace a weaker case from "
                             "the same article.",
    },
    {
        "case_id": "20260909-grounding-F2-conflation-in-social-hook",
        "run_id": "production-20260909T223331Z-83161dd1",
        "date": "2026-09-09",
        "independence_key": "heat-index-somerstown",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F2"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "UNRESOLVED",
        "owner_must_decide": "The same index conflation, but in the social "
                             "hook rather than the article body. Does surface "
                             "that never reaches the article carry the same "
                             "materiality as surface inside it?",
    },
    {
        "case_id": "20260909-grounding-F3-page-attribution",
        "run_id": "production-20260909T070025Z-8d2d1a38",
        "date": "2026-09-09",
        "independence_key": "rca-schools",
        "stage": "GROUNDING",
        "finding_type": "TRUE_UNSUPPORTED",
        "locator": {"kind": "grounding_finding", "finding_id": "F3"},
        "expected_route": "ADJUDICATE",
        "expected_materiality": None,
        "expected_repair_route": None,
        "label_authority": "UNRESOLVED",
        "owner_must_decide": "Two institutional pages conflated, and a "
                             "last-updated date moved onto the wrong one. The "
                             "assurance to offer holders is real either way. "
                             "Is misattributing WHERE an institution said "
                             "something MINOR when WHAT it said is intact?",
    },
]


# --------------------------------------------------------------- assembly


_ARTIFACT_MAP = {
    "SAFETY_AUDIT": ("SAFETY_AUDIT.json", False),
    "MANIFEST": ("MANIFEST.json", False),
    "WRITER_PACKET": ("WRITER_PACKET.json", False),
    "GROUNDING_FINDINGS": ("GROUNDING_FINDINGS.json", False),
    "PUBLICATION_DECISION": ("PUBLICATION_DECISION.json", False),
    "OWNER_COPYDESK_REPAIR": ("OWNER_COPYDESK_REPAIR.json", False),
    "FACT_CHECK_ADJUDICATION": ("FACT_CHECK_ADJUDICATION.json", False),
    "CONTINUITY_FINAL": ("CONTINUITY_FINAL.md", False),
    "ARTICLE_FINAL": ("ARTICLE_FINAL.md", False),
}

# What each stage cannot be adjudicated without. A Grounding finding is
# produced before Safety ever runs, so an absent SAFETY_AUDIT is not a defect
# in a Grounding case -- it is the normal shape of a run that never got there.
_STAGE_REQUIRES = {
    "SAFETY": ("SAFETY_AUDIT",),
    "GROUNDING": ("GROUNDING_FINDINGS",),
    "READER": ("PUBLICATION_DECISION",),
    "OWNER_REPAIR": ("OWNER_COPYDESK_REPAIR",),
    "FACT_CHECK": ("FACT_CHECK_ADJUDICATION",),
}


def load_run_artifacts(run_id, root=None):
    out = {}
    for key, (name, required) in _ARTIFACT_MAP.items():
        out[key] = load_artifact(run_id, name, root=root, required=required)
    return out


def _verify_owner_label(case, artifacts):
    """An OWNER label must match the retained artifact, or the case is dropped.

    This is the guard against a gold label drifting away from the human
    decision it claims to record.
    """
    if not case.get("verify_against_publication_decision"):
        return
    decision = artifacts.get("PUBLICATION_DECISION") or {}
    labels = decision.get("reader_materiality_classification") or {}
    dimension = case["locator"].get("dimension")
    retained = labels.get(dimension)
    if retained != case["expected_materiality"]:
        raise CaseError(
            "owner label drift for %s: registry says %r, "
            "PUBLICATION_DECISION says %r"
            % (case["case_id"], case["expected_materiality"], retained)
        )


def resolve_case(spec, root=None, artifacts=None):
    """Attach artifacts, hard conditions, computed route and bounded state."""
    case = dict(spec)
    case.setdefault("expected_repair_route", None)
    case.setdefault("independence_key", case["run_id"])
    artifacts = artifacts if artifacts is not None else load_run_artifacts(
        case["run_id"], root=root
    )
    for key in _STAGE_REQUIRES.get(case["stage"], ()):
        if artifacts.get(key) is None:
            raise CaseError(
                "%s needs %s for a %s case" % (case["run_id"], key, case["stage"])
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
    _verify_owner_label(case, artifacts)
    case["hard_conditions"] = hard_conditions(
        case["stage"],
        artifacts.get("SAFETY_AUDIT"),
        artifacts.get("MANIFEST"),
        grounding=artifacts.get("GROUNDING_FINDINGS"),
        publication_decision=artifacts.get("PUBLICATION_DECISION"),
        finding=finding,
        owner_repair=artifacts.get("OWNER_COPYDESK_REPAIR"),
        fact_check_adjudication=artifacts.get("FACT_CHECK_ADJUDICATION"),
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
    case["trusted"] = case["label_authority"] in TRUSTED_AUTHORITIES
    case["scored_for_materiality"] = bool(
        case["trusted"]
        and case["expected_materiality"] in MATERIALITY_LABELS
        and case["computed_route"] == "ADJUDICATE"
    )
    case["scored_for_repair"] = bool(
        case["trusted"]
        and case["expected_repair_route"] in REPAIR_ROUTES
        and case["computed_route"] == "ADJUDICATE"
    )
    case["source_artifacts"] = sorted(
        name for key, (name, _r) in _ARTIFACT_MAP.items() if artifacts.get(key)
    )
    case["state"] = build_state(case, artifacts)
    case["input_hash"] = state_hash(case["state"])
    case["locator"] = {k: v for k, v in locator.items() if not k.startswith("_")}
    return case


# ------------------------------------------------------------- validation


_PROSE_FIELDS = ("note", "owner_must_decide")
# A registry entry is a reference, not a fixture. Anything that looks like a
# retained span belongs in the artifact, not here.
_MAX_REGISTRY_FIELD = 700


def validate_registry(registry=None, queue=None, cap=ARTICLE_CAP):
    """Offline structural validation. Raises RegistryError on the first fault.

    Checks the things that silently ruin a benchmark: an invalid label, a label
    without authority, an untrusted case smuggled into gold, one article
    dominating the set, and unpublished prose committed as fixture text.
    """
    registry = GOLD_REGISTRY if registry is None else registry
    queue = REVIEW_QUEUE if queue is None else queue

    seen = set()
    per_article = {}
    for spec in list(registry) + list(queue):
        case_id = spec.get("case_id")
        if not case_id:
            raise RegistryError("registry entry without case_id")
        if case_id in seen:
            raise RegistryError("duplicate case_id %s" % case_id)
        seen.add(case_id)

        if spec.get("stage") not in STAGES:
            raise RegistryError("%s: unknown stage %r" % (case_id, spec.get("stage")))
        if spec.get("expected_route") not in ROUTES:
            raise RegistryError(
                "%s: unknown expected_route %r" % (case_id, spec.get("expected_route"))
            )
        authority = spec.get("label_authority")
        if authority not in LABEL_AUTHORITIES:
            raise RegistryError(
                "%s: unknown label_authority %r" % (case_id, authority)
            )

        materiality = spec.get("expected_materiality")
        if materiality is not None and materiality not in MATERIALITY_LABELS:
            raise RegistryError(
                "%s: invalid expected_materiality %r" % (case_id, materiality)
            )
        repair = spec.get("expected_repair_route")
        if repair is not None and repair not in REPAIR_ROUTES:
            raise RegistryError(
                "%s: invalid expected_repair_route %r" % (case_id, repair)
            )

        if authority == "UNRESOLVED":
            if materiality is not None or repair is not None:
                raise RegistryError(
                    "%s: an UNRESOLVED case may not carry a label" % case_id
                )
            if not spec.get("owner_must_decide"):
                raise RegistryError(
                    "%s: UNRESOLVED without owner_must_decide" % case_id
                )
        if materiality is not None and authority not in TRUSTED_AUTHORITIES:
            raise RegistryError(
                "%s: materiality label with authority %r" % (case_id, authority)
            )
        if repair is not None and materiality is None:
            raise RegistryError(
                "%s: repair route without a materiality label" % case_id
            )
        if spec.get("expected_route") != "ADJUDICATE" and (
            materiality is not None or repair is not None
        ):
            raise RegistryError(
                "%s: a bypassed case cannot carry adjudication labels" % case_id
            )

        for field in _PROSE_FIELDS:
            value = spec.get(field)
            if value and len(value) > _MAX_REGISTRY_FIELD:
                raise RegistryError(
                    "%s: %s is %d chars -- registry entries are references, "
                    "not fixtures" % (case_id, field, len(value))
                )
        for key, value in spec.items():
            if key in _PROSE_FIELDS or not isinstance(value, str):
                continue
            if len(value) > 200:
                raise RegistryError(
                    "%s: field %s looks like retained prose" % (case_id, key)
                )

    for spec in registry:
        if spec.get("label_authority") == "UNRESOLVED":
            raise RegistryError(
                "%s: UNRESOLVED cases belong in REVIEW_QUEUE" % spec["case_id"]
            )
        key = spec.get("independence_key") or spec["run_id"]
        per_article.setdefault(key, []).append(spec["case_id"])

    for key, ids in sorted(per_article.items()):
        if len(ids) > cap:
            raise RegistryError(
                "article %s contributes %d gold cases, cap is %d: %s"
                % (key, len(ids), cap, ", ".join(sorted(ids)))
            )
    return True


# --------------------------------------------------------------- reporting


def balance_report(case_list):
    """Label balance and the constant-answer baselines a model must beat."""
    scored = [c for c in case_list if c.get("scored_for_materiality")]
    minor = [c for c in scored if c["expected_materiality"] == "MINOR"]
    material = [c for c in scored if c["expected_materiality"] == "MATERIAL"]

    repair_scored = [c for c in case_list if c.get("scored_for_repair")]
    repair_counts = {route: 0 for route in REPAIR_ROUTES}
    for case in repair_scored:
        repair_counts[case["expected_repair_route"]] += 1

    per_article = {}
    for case in case_list:
        per_article.setdefault(case.get("independence_key") or case["run_id"], 0)
        per_article[case.get("independence_key") or case["run_id"]] += 1

    total = len(scored)
    constant_minor = round(len(minor) / total, 4) if total else None
    constant_material = round(len(material) / total, 4) if total else None
    repair_total = len(repair_scored)
    constant_repair = (
        round(max(repair_counts.values()) / repair_total, 4) if repair_total else None
    )

    return {
        "cases_total": len(case_list),
        "materiality_scored": total,
        "minor": len(minor),
        "material": len(material),
        "minor_material_ratio": "%d:%d" % (len(minor), len(material)),
        "repair_scored": repair_total,
        "repair_route_counts": repair_counts,
        "by_authority": _count(case_list, "label_authority"),
        "by_stage": _count(case_list, "stage"),
        "by_expected_route": _count(case_list, "expected_route"),
        "max_cases_from_one_article": max(per_article.values()) if per_article else 0,
        "articles": len(per_article),
        "constant_minor_baseline": constant_minor,
        "constant_material_baseline": constant_material,
        "constant_repair_route_baseline": constant_repair,
        "trivially_solvable_by_constant_materiality": bool(
            constant_minor is not None
            and max(constant_minor, constant_material) >= 0.70
        ),
    }


def registry_balance(registry=None):
    """Balance from the registry alone -- no artifacts, no filesystem.

    What the caseset claims about itself, independent of which runs happen to
    be retained on this host.
    """
    registry = GOLD_REGISTRY if registry is None else registry
    synthetic = []
    for spec in registry:
        adjudicated = spec.get("expected_route") == "ADJUDICATE"
        trusted = spec.get("label_authority") in TRUSTED_AUTHORITIES
        synthetic.append(
            {
                "run_id": spec["run_id"],
                "independence_key": spec.get("independence_key") or spec["run_id"],
                "stage": spec.get("stage"),
                "label_authority": spec.get("label_authority"),
                "expected_route": spec.get("expected_route"),
                "expected_materiality": spec.get("expected_materiality"),
                "expected_repair_route": spec.get("expected_repair_route"),
                "scored_for_materiality": bool(
                    trusted
                    and adjudicated
                    and spec.get("expected_materiality") in MATERIALITY_LABELS
                ),
                "scored_for_repair": bool(
                    trusted
                    and adjudicated
                    and spec.get("expected_repair_route") in REPAIR_ROUTES
                ),
            }
        )
    return balance_report(synthetic)


def _count(case_list, field):
    out = {}
    for case in case_list:
        out[case.get(field)] = out.get(case.get(field), 0) + 1
    return {k: out[k] for k in sorted(out, key=str)}


# ------------------------------------------------------------- assembly


def gold_cases(root=None, strict=False):
    """The trusted caseset. Unresolved cases are never included.

    A case whose run is not retained on this host is skipped, not fatal, unless
    `strict` -- the benchmark must stay runnable on a host with a partial
    archive, but the tests run it strict.
    """
    validate_registry()
    out = []
    for spec in GOLD_REGISTRY:
        try:
            out.append(resolve_case(spec, root=root))
        except CaseError:
            if strict:
                raise
    return out


def review_queue_cases(root=None, strict=False):
    """Unresolved cases, resolved only far enough to show the owner the span."""
    validate_registry()
    out = []
    for spec in REVIEW_QUEUE:
        try:
            out.append(resolve_case(spec, root=root))
        except CaseError:
            if strict:
                raise
    return out


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
                    "expected_repair_route": None,
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
                    "expected_repair_route": None,
                    "label_authority": "NONE",
                }
            )
        for spec in specs:
            try:
                cases.append(resolve_case(spec, root=root, artifacts=artifacts))
            except CaseError:
                continue
    known = {
        (spec["run_id"], json.dumps(spec["locator"], sort_keys=True))
        for spec in list(GOLD_REGISTRY) + list(REVIEW_QUEUE)
    }
    return [
        c
        for c in cases
        if (c["run_id"], json.dumps(c["locator"], sort_keys=True)) not in known
    ]
