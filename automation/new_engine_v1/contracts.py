"""VERBATIM PORT of the frozen Phase-1 shadow_v0 module of the same name.

Source: .claude/experiments/production-migration-phase1-shadow-v0-2026-08-20/impl/shadow_v0/
on the research line (backup/research-main-2026-08-20). Copied rather than imported so this
production-candidate package has no dependency on an experiment directory, and copied
VERBATIM rather than adapted so NEW_ENGINE_V1 artifacts stay directly comparable with the
frozen shadow runs (same SCHEMA_VERSION, same hashes for the same payloads).

Do not "improve" this file. It is the frozen contract. If it must change, that is a
schema-version decision, not an edit.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict

SCHEMA_VERSION = "shadow-v0.1"

# Stage identities, in pipeline order.
SOURCE_SNAPSHOT = "SOURCE_SNAPSHOT"
# ADDITIVE EXTENSION (2026-08-28), deliberately not a schema-version bump. The eight
# frozen stages keep their payload shapes, their validation and therefore their hashes,
# so a frozen shadow run still validates and still compares byte-for-byte. RESEARCH_PACK
# is OPTIONAL in REQUIRED_STAGES for exactly that reason: a run recorded before this
# stage existed is not retroactively invalid. What is NOT optional is its content --
# where a pack is present, every source in it must carry provenance and every excerpt
# must be a verbatim span of fetched bytes, checked below.
RESEARCH_PACK = "RESEARCH_PACK"
DISCOVERY = "DISCOVERY"
ARTICLE_FORM = "ARTICLE_FORM"
WRITER_INPUT = "WRITER_INPUT"
WRITER_OUTPUT = "WRITER_OUTPUT"
GROUNDING_FINDINGS = "GROUNDING_FINDINGS"
GROUNDING_REPAIR = "GROUNDING_REPAIR"
SHADOW_DECISION = "SHADOW_DECISION"

STAGE_ORDER = [
    SOURCE_SNAPSHOT, RESEARCH_PACK, DISCOVERY, ARTICLE_FORM, WRITER_INPUT,
    WRITER_OUTPUT, GROUNDING_FINDINGS, GROUNDING_REPAIR, SHADOW_DECISION,
]

# Stages whose absence is fatal. GROUNDING_REPAIR is optional: a draft with no
# unsupported findings legitimately has nothing to repair. RESEARCH_PACK is optional
# for the compatibility reason stated at its definition, not because a production run
# may skip research -- the runner decides that, and fails closed when it cannot.
OPTIONAL_STAGES = (GROUNDING_REPAIR, RESEARCH_PACK)
REQUIRED_STAGES = [s for s in STAGE_ORDER if s not in OPTIONAL_STAGES]

# Roles a pack source may carry. ANCHOR is the source that caused the subject to be
# discovered; everything else had to be found, fetched and hashed to exist here.
SOURCE_ROLES = ("ANCHOR", "PRIMARY", "INDEPENDENT", "TERTIARY", "CONTEXT",
                "COUNTERWEIGHT")
SUFFICIENCY_VERDICTS = ("ARTICLE", "SHORT_ARTICLE", "NARROW", "HOLD_INSUFFICIENT_RESEARCH")

# Markers from the legacy production prompt surface. WRITER_INPUT is checked against
# these so a legacy prompt cannot enter the new architecture unnoticed. Sourced from
# the Legacy Prompt / Rule Inventory (commit 38c47b8).
LEGACY_PROMPT_MARKERS = (
    "YOU ARE MAYA FLUX", "YOU ARE PIXEL NOVA", "YOU ARE SIRI SAGE", "YOU ARE ZEN CIRCUIT",
    "WRITE LIKE THIS PERSON", "YOUR WOUND", "AUTHORIZED PERSONAL HISTORY",
    "YOUR CANON (WHO YOU ARE, IMMUTABLY)", "FORBIDDEN ACADEMIC JARGON",
    "FORBIDDEN CORPORATE/JOURNALESE", "FORBIDDEN DEFAULTS", "SOMEONE ELSE MUST SPEAK",
    "NAMED VOICES", "CRAFTED RHETORIC", "BLOCKED THEORISTS", "ANTI-SYSTEMIC TEST",
    "RUTGER BREGMAN", "TITLE RULES", "BEAT NOTE", "HUMAN THREAD", "AUTHOR RULE",
    "STARTING REGISTER", "ARRIVAL PARAGRAPH", "DISCOVERY VOICE", "SIGNPOST PHRASES",
    "US-AVOIDANCE", "UK-PREFERENCE", "ONE APHORISM", "NO EMPTY GRANDEUR",
)


class ContractViolation(Exception):
    """Raised on any contract breach. Callers must not catch-and-continue."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass
class Artifact:
    stage: str
    created_at: str                       # injected, never clock-read
    payload: dict
    input_hashes: dict = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def content_hash(self) -> str:
        """Hash of everything that defines this artifact, including its lineage."""
        return sha256_text(canonical_json({
            "schema_version": self.schema_version,
            "stage": self.stage,
            "created_at": self.created_at,
            "input_hashes": self.input_hashes,
            "payload": self.payload,
        }))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["content_hash"] = self.content_hash()
        return d


def _require(payload: dict, keys, stage: str):
    missing = [k for k in keys if k not in payload or payload[k] in (None, "")]
    if missing:
        raise ContractViolation("%s: missing required payload field(s): %s" % (stage, ", ".join(missing)))


def validate(artifact: Artifact) -> None:
    """Fail-closed structural validation. Raises ContractViolation."""
    if artifact.stage not in STAGE_ORDER:
        raise ContractViolation("unknown stage: %r" % artifact.stage)
    if artifact.schema_version != SCHEMA_VERSION:
        raise ContractViolation("%s: schema_version %r != %r"
                                % (artifact.stage, artifact.schema_version, SCHEMA_VERSION))
    if not artifact.created_at:
        raise ContractViolation("%s: created_at is required" % artifact.stage)
    p = artifact.payload
    s = artifact.stage

    if s == SOURCE_SNAPSHOT:
        # The Phase-0 blocker fix: the TEXT must be here, not only a hash.
        _require(p, ["source_text", "source_sha256", "provenance"], s)
        if sha256_text(p["source_text"]) != p["source_sha256"]:
            raise ContractViolation("SOURCE_SNAPSHOT: source_sha256 does not match source_text")
        _require(p["provenance"], ["origin"], "SOURCE_SNAPSHOT.provenance")
    elif s == RESEARCH_PACK:
        _require(p, ["subject", "sources", "coverage", "sufficiency", "pack_sha256"], s)
        if not isinstance(p["sources"], list) or not p["sources"]:
            raise ContractViolation("RESEARCH_PACK: sources must be a non-empty list")
        if (p["sufficiency"] or {}).get("verdict") not in SUFFICIENCY_VERDICTS:
            raise ContractViolation("RESEARCH_PACK: sufficiency.verdict %r is not one of %s"
                                    % ((p["sufficiency"] or {}).get("verdict"),
                                       ", ".join(SUFFICIENCY_VERDICTS)))
        # A subject span, where one exists, must be a verbatim region of the anchor: it
        # is what binds Discovery to the subject that was actually researched, so a
        # paraphrase of it would bind nothing while looking as if it did.
        span = p.get("subject_span") or ""
        if span:
            anchor_src = next((x for x in p["sources"] if x.get("role") == "ANCHOR"), None)
            hay = " ".join((anchor_src or {}).get("text", "").split()).lower()
            if " ".join(str(span).split()).lower() not in hay:
                raise ContractViolation(
                    "RESEARCH_PACK: subject_span is not a verbatim region of the anchor: %r"
                    % str(span)[:80])
        anchors = [x for x in p["sources"] if x.get("role") == "ANCHOR"]
        if len(anchors) != 1:
            raise ContractViolation("RESEARCH_PACK: exactly one ANCHOR source required, got %d"
                                    % len(anchors))
        ids = set()
        for src in p["sources"]:
            _require(src, ["source_id", "role", "url", "accessed_at", "sha256",
                           "fetch_status", "content_length", "text"],
                     "RESEARCH_PACK.source")
            if src["source_id"] in ids:
                raise ContractViolation("RESEARCH_PACK: duplicate source_id %r" % src["source_id"])
            ids.add(src["source_id"])
            if src["role"] not in SOURCE_ROLES:
                raise ContractViolation("RESEARCH_PACK: %s has role %r, not one of %s"
                                        % (src["source_id"], src["role"], ", ".join(SOURCE_ROLES)))
            if src["fetch_status"] != "ok":
                raise ContractViolation(
                    "RESEARCH_PACK: %s has fetch_status %r -- a source that was not "
                    "successfully fetched supplies no material and may not be in the pack"
                    % (src["source_id"], src["fetch_status"]))
            if sha256_text(src["text"]) != src["sha256"]:
                raise ContractViolation("RESEARCH_PACK: %s sha256 does not match its text"
                                        % src["source_id"])
            # Every excerpt the pack offers downstream must really be in the bytes it
            # was taken from. This is the search-result-is-not-a-source rule made
            # structural: a model-written span that is not in the fetched text cannot
            # be carried, whatever produced it.
            hay = " ".join(src["text"].split()).lower()
            for ex in (src.get("excerpts") or []):
                if " ".join(str(ex).split()).lower() not in hay:
                    raise ContractViolation(
                        "RESEARCH_PACK: %s carries an excerpt that is not a verbatim span "
                        "of its own fetched text: %r" % (src["source_id"], str(ex)[:80]))
    elif s == DISCOVERY:
        _require(p, ["dominant_reading", "disturbance", "perceptual_instrument",
                     "what_becomes_knowable", "grounding_boundaries"], s)
    elif s == ARTICLE_FORM:
        _require(p, ["route", "arrival", "burden"], s)
        if not isinstance(p["route"], list) or not p["route"]:
            raise ContractViolation("ARTICLE_FORM: route must be a non-empty list of movements")
    elif s == WRITER_INPUT:
        _require(p, ["prompt_text", "prompt_sha256"], s)
        if sha256_text(p["prompt_text"]) != p["prompt_sha256"]:
            raise ContractViolation("WRITER_INPUT: prompt_sha256 does not match prompt_text")
        hits = [m for m in LEGACY_PROMPT_MARKERS if m in p["prompt_text"]]
        if hits:
            raise ContractViolation("WRITER_INPUT: legacy prompt surface present: %s" % ", ".join(hits[:5]))
    elif s == WRITER_OUTPUT:
        _require(p, ["article_text", "article_sha256", "provider_status"], s)
        if sha256_text(p["article_text"]) != p["article_sha256"]:
            raise ContractViolation("WRITER_OUTPUT: article_sha256 does not match article_text")
        if p["provider_status"] not in ("ok", "failed"):
            raise ContractViolation("WRITER_OUTPUT: provider_status must be 'ok' or 'failed'")
    elif s == GROUNDING_FINDINGS:
        _require(p, ["status", "findings"], s)
        if p["status"] not in ("settled", "unresolved"):
            raise ContractViolation("GROUNDING_FINDINGS: status must be 'settled' or 'unresolved'")
        for f in p["findings"]:
            if f.get("classification") not in ("TRUE_UNSUPPORTED", "TRUE_UNCERTAIN", "LEGITIMATE_INTERPRETATION"):
                raise ContractViolation("GROUNDING_FINDINGS: bad classification %r" % f.get("classification"))
    elif s == GROUNDING_REPAIR:
        _require(p, ["mode", "patches", "article_text", "article_sha256"], s)
        if p["mode"] != "patch_only":
            raise ContractViolation("GROUNDING_REPAIR: mode must be 'patch_only' (no rewrite)")
        if sha256_text(p["article_text"]) != p["article_sha256"]:
            raise ContractViolation("GROUNDING_REPAIR: article_sha256 does not match article_text")
    elif s == SHADOW_DECISION:
        _require(p, ["decision", "reasons"], s)
        if p["decision"] not in ("ACCEPT", "HOLD"):
            raise ContractViolation("SHADOW_DECISION: decision must be ACCEPT or HOLD")


def verify_lineage(artifact: Artifact, supplied: dict) -> None:
    """Every hash an artifact declares as an input must match the artifact actually
    supplied under that name. Fail-closed: a lineage break raises."""
    for name, declared in artifact.input_hashes.items():
        if name not in supplied:
            raise ContractViolation("%s: declares input %r that was not supplied" % (artifact.stage, name))
        actual = supplied[name].content_hash()
        if actual != declared:
            raise ContractViolation(
                "%s: lineage break on %r -- declared %s, actual %s"
                % (artifact.stage, name, declared[:16], actual[:16]))
