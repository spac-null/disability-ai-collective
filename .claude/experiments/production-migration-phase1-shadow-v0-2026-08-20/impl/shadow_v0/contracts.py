"""
contracts.py -- stage artifact contracts for the target-architecture shadow V0.

The smallest schema sufficient for this migration. Every stage emits one Artifact;
the pipeline is reconstructable from the artifacts alone.

DESIGN NOTES

- `created_at` is INJECTED, never read from the clock. Replay must be deterministic:
  the same fixtures must produce the same artifact hashes on every run.
- `input_hashes` chains the stages. Each artifact records the content hashes of the
  artifacts it consumed, so a lineage break is detectable without re-running anything.
- Validation is FAIL-CLOSED. A missing required field, a wrong stage name, or a
  declared input hash that does not match the artifact actually supplied raises
  ContractViolation. Nothing silently degrades.
- SOURCE_SNAPSHOT carries the source TEXT, not just its hash. This is the fix for the
  Phase-0 finding that production persists `source_hash` but never the bytes, which
  would make Phase-2 live-vs-shadow comparison unprovable.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict

SCHEMA_VERSION = "shadow-v0.1"

# Stage identities, in pipeline order.
SOURCE_SNAPSHOT = "SOURCE_SNAPSHOT"
DISCOVERY = "DISCOVERY"
ARTICLE_FORM = "ARTICLE_FORM"
WRITER_INPUT = "WRITER_INPUT"
WRITER_OUTPUT = "WRITER_OUTPUT"
GROUNDING_FINDINGS = "GROUNDING_FINDINGS"
GROUNDING_REPAIR = "GROUNDING_REPAIR"
SHADOW_DECISION = "SHADOW_DECISION"

STAGE_ORDER = [
    SOURCE_SNAPSHOT, DISCOVERY, ARTICLE_FORM, WRITER_INPUT,
    WRITER_OUTPUT, GROUNDING_FINDINGS, GROUNDING_REPAIR, SHADOW_DECISION,
]

# Stages whose absence is fatal. GROUNDING_REPAIR is optional: a draft with no
# unsupported findings legitimately has nothing to repair.
REQUIRED_STAGES = [s for s in STAGE_ORDER if s != GROUNDING_REPAIR]

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
