"""definition_claim_shadow.py -- does each factual commitment in a definition actually
follow from the evidence that definition declared?

ZERO AUTHORITY. This module cannot change the architecture, invoke a repair, touch the
Writer Packet, reach the Writer, influence Grounding, Fact Check, Reader or publication, or
affect candidate selection. It reads a frozen architecture, asks one bounded question, and
writes a file. If it fails in any way the composition continues exactly as if it had never
run.

WHY IT EXISTS. PR #106 made every used definition declare the fact ids that license it. On
2026-09-23, run 1 of the rehearsal cohort showed what that does and does not buy:

    definitions['Dressing for Evacuation']
      "...people were asked to put on what they would wear if told a large-scale evacuation
       were MINUTES AWAY..."
    definition_evidence = [F46, F47, F48]
      F46 "...asked to dress as if alerted to an IMMINENT large-scale evacuation..."

All three ids exist, are in use_facts, are uncut, and are genuinely about that project. The
ATTRIBUTION is correct. The ENTAILMENT is not: no fact in that run's ledger contains the word
"minutes". render() put the gloss in front of the Writer under EXPLAIN AT FIRST USE, the
Writer transcribed it, and three of six blocking Grounding findings were that phrase. The
defect was fixed in the plan the moment Architecture emitted the gloss; the 7 model calls and
239 seconds spent after that were spent discovering something already decided.

validate_definition_support cannot catch it and does not claim to -- it checks numbers,
entities and relation classes, and "minutes away" has no digit, no capital and no relation
cue. Its own docstring says it is not a general entailment gate. This module asks the
entailment question instead, at the level the failure actually lives: the individual factual
commitment.

WHAT IT IS NOT. Not a gate. Not a score. Not a repair. There is no PASS, no HOLD and no
verdict field in the schema, on purpose. Whether a checker of this kind can identify
unsupported added specificity WITHOUT becoming another false-positive machine is an open
question, and the 114-run relation audit is the standing reminder of how that goes wrong: a
plausible mechanism, applied to the wrong unit, newly failed 91 of 114 real plans.

NARROW BY CONSTRUCTION. Definitions only, and each definition sees ONLY its own declared
evidence. Not the whole ledger -- that is what lets an unrelated fact rescue an unsupported
commitment, which is precisely the error the relation audit measured. Not crip_turn, not the
lens fields, not beats, spine or ending: the evidence that would have justified reaching
those was a misreading of a truncated proposition, corrected in
.claude/experiments/pr106-rehearsal-cohort-2026-09-23/.
"""
from __future__ import annotations

import json
import os
import time

from . import provenance as PV

SCHEMA_VERSION = "definition-claim-shadow-v1"
ENV_FLAG = "CRIPMINDS_DEFINITION_CLAIM_SHADOW"

SUPPORTED = "SUPPORTED"
NOT_ESTABLISHED = "NOT_ESTABLISHED"
CONTRADICTED = "CONTRADICTED"
NON_FACTUAL = "NON_FACTUAL_OR_NOT_CHECKABLE"
STATUSES = (SUPPORTED, NOT_ESTABLISHED, CONTRADICTED, NON_FACTUAL)

# Keys this module owns. The artifact is merged with a MODEL REPLY, and a reply must not be
# able to restate what authority this observation has or whether it validated. Same rule and
# same reason as prewrite_story_shadow.TOOL_OWNED.
TOOL_OWNED = ("schema_version", "authority", "article_not_written_yet", "status",
              "validation_errors", "wall_seconds", "execution", "physical_model_calls",
              "tool_fields_ignored", "error", "definitions_observed")


def enabled(env=None) -> bool:
    """OFF unless explicitly switched on, like every other shadow in this engine."""
    v = (env if env is not None else os.environ).get(ENV_FLAG, "").strip().lower()
    return v in ("1", "on", "true", "yes")


SYSTEM = (
    "You are checking whether a short explanatory gloss says more than its evidence "
    "establishes. Nothing you say changes anything: the plan is already frozen, no article "
    "exists yet, and your reply cannot alter, repair or stop any of it.\n"
    "\n"
    "For each term you are given a GLOSS and the EVIDENCE that gloss declared. Break the "
    "gloss into the smallest factual commitments that could be checked independently, and "
    "judge each one against THAT TERM'S EVIDENCE ONLY. Evidence listed under another term is "
    "not available to this one.\n"
    "\n"
    "STATUSES, and the distinctions between them matter more than the labels:\n"
    "\n"
    "  SUPPORTED -- the evidence establishes this commitment, at the specificity the gloss "
    "states it. Different wording is fine and expected. A gloss is a plain-language "
    "restatement, not a quotation; do not require overlapping words, and do not withhold "
    "SUPPORTED because the gloss is shorter, simpler or differently ordered than the "
    "evidence.\n"
    "\n"
    "  NOT_ESTABLISHED -- the commitment may well be true, but this term's evidence does not "
    "establish it AT THE SPECIFICITY STATED. This is the finding worth having. It is most "
    "often a quiet sharpening: a range narrowed to a value, a qualitative word replaced by a "
    "quantity, a superlative where the evidence gives only a description, a named part or "
    "place where the evidence names none, a general capability turned into a specific "
    "mechanism. Ask of each commitment: if the evidence is all I have, could I write this "
    "exact degree of precision? If the answer is no, it is NOT_ESTABLISHED even when the "
    "surrounding sentence is entirely supported.\n"
    "\n"
    "  CONTRADICTED -- the evidence states something incompatible with the commitment. "
    "Absence of support is NOT contradiction; if the evidence is merely silent, the status is "
    "NOT_ESTABLISHED.\n"
    "\n"
    "  NON_FACTUAL_OR_NOT_CHECKABLE -- the span is not a checkable claim about this subject. "
    "Ordinary explanatory framing belongs here and is entirely legitimate: saying what kind "
    "of thing a term is, what category it falls in, or what the word means in ordinary usage "
    "is what a gloss is FOR. 'a small motor', 'a printed list', 'the category the developers "
    "use' -- these are definitional framing, not assertions about this subject, and marking "
    "them NOT_ESTABLISHED because the evidence does not repeat them is a mistake. A gloss is "
    "allowed to explain a term in ordinary language without the evidence teaching the "
    "language.\n"
    "\n"
    "THE FAILURE MODE TO AVOID. It is easy, and useless, to flag everything by treating each "
    "ordinary phrase as an unsupported claim. A report in which most commitments are "
    "NOT_ESTABLISHED is a report that has not discriminated. Most commitments in a "
    "well-built gloss are SUPPORTED or NON_FACTUAL_OR_NOT_CHECKABLE, and that is the normal "
    "result. Report the specific commitment that reaches past the evidence, and leave the "
    "rest alone.\n"
    "\n"
    "Quote each commitment as the shortest span of the gloss that carries it. Give a reason "
    "of one clause. Do not rewrite the gloss, do not suggest a repair, do not rank or score "
    "anything, and do not say whether the plan should proceed -- that is not yours to give."
)

SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"definitions": [\n'
    '   {"term": "the term exactly as given",\n'
    '    "claims": [\n'
    '      {"commitment": "the shortest span of the gloss carrying this commitment",\n'
    '       "status": "%(st)s",\n'
    '       "evidence_ids": ["F.."],   the ids that establish it; [] unless SUPPORTED\n'
    '                                  or CONTRADICTED; only ids given for THIS term\n'
    '       "reason": "one clause"}]}]}\n'
    "No prose outside the JSON. No verdict, no score, no recommendation, no rewritten gloss."
) % {"st": "|".join(STATUSES)}


def definitions_of(arch: dict) -> dict:
    return (arch or {}).get("definitions") or {}


def build_user(arch: dict, ledger: dict) -> str:
    """Only the definitions and, per definition, ONLY its own declared evidence.

    The whole ledger is deliberately absent. Handing it over is what lets an unrelated fact
    license a commitment it has nothing to do with -- the exact widening the 114-run relation
    audit measured the cost of.
    """
    defs = definitions_of(arch)
    support = (arch or {}).get("definition_evidence") or {}
    L = []
    for term in sorted(defs):
        gloss = str(defs.get(term) or "").strip()
        ids = support.get(term)
        if isinstance(ids, str):
            ids = [ids]
        ids = [str(i) for i in (ids or [])]
        L.append("TERM: %s" % term)
        L.append("GLOSS: %s" % gloss)
        if not ids:
            L.append("EVIDENCE: none declared")
        else:
            L.append("EVIDENCE (this term's own, and nothing else):")
            for fid in ids:
                f = (ledger or {}).get(fid) or {}
                L.append("  %s  %s" % (fid, str(f.get("proposition", "")).strip()))
                span = str(f.get("support_span", "") or "").strip()
                if span:
                    L.append("      verbatim from source: %s" % span)
        L.append("")
    L.append(SCHEMA)
    return "\n".join(L)


def _evidence_inputs(arch: dict, ledger: dict) -> dict:
    """Exactly the evidence the question was asked about -- hashed as its own input."""
    support = (arch or {}).get("definition_evidence") or {}
    out = {}
    for term in sorted(definitions_of(arch)):
        ids = support.get(term)
        if isinstance(ids, str):
            ids = [ids]
        for fid in [str(i) for i in (ids or [])]:
            f = (ledger or {}).get(fid) or {}
            out[fid] = {"proposition": f.get("proposition", ""),
                        "support_span": f.get("support_span", "")}
    return out


def validate(obj, arch: dict) -> list:
    """Shape, vocabulary, term honesty and evidence-id honesty.

    A claim citing an id the term did not declare is the one thing that must never pass: an
    artifact asserting that F73 supports a commitment under a term that never declared F73
    would be worse than no artifact, because a later audit would count it as an observation.
    """
    errs = []
    if not isinstance(obj, dict):
        return ["reply is not an object"]
    defs = definitions_of(arch)
    support = (arch or {}).get("definition_evidence") or {}
    rows = obj.get("definitions")
    if not isinstance(rows, list) or not rows:
        return ["definitions is empty or not a list"]

    seen = []
    for i, d in enumerate(rows, 1):
        if not isinstance(d, dict):
            errs.append("definitions[%d] is not an object" % i)
            continue
        term = d.get("term")
        seen.append(term)
        if term not in defs:
            errs.append("definitions[%d] reports term %r, which the architecture does not "
                        "define" % (i, term))
            continue
        allowed = support.get(term)
        if isinstance(allowed, str):
            allowed = [allowed]
        allowed = {str(x) for x in (allowed or [])}
        claims = d.get("claims")
        if not isinstance(claims, list) or not claims:
            errs.append("%r carries no claims" % term)
            continue
        for k, c in enumerate(claims, 1):
            where = "%r claim %d" % (term, k)
            if not isinstance(c, dict):
                errs.append("%s is not an object" % where)
                continue
            if not str(c.get("commitment") or "").strip():
                errs.append("%s has no commitment text" % where)
            if c.get("status") not in STATUSES:
                errs.append("%s status %r is not one of %s"
                            % (where, c.get("status"), ", ".join(STATUSES)))
            for fid in (c.get("evidence_ids") or []):
                if str(fid) not in allowed:
                    errs.append("%s cites %r, which is not evidence this term declared (%s)"
                                % (where, fid, sorted(allowed) or "none"))
    missing = sorted(set(defs) - {t for t in seen if t in defs})
    if missing:
        errs.append("no report for defined term(s): %s" % missing)
    return errs


def run(ask, arch: dict, ledger: dict, out_dir=None, execution_id: str = "",
        call_meta: dict | None = None) -> dict | None:
    """The artifact, or None. Never raises, never blocks, never returns a verdict.

    `ask` is a callable taking (system, user) and returning a parsed object -- injected so
    the caller owns the transport and a test can supply its own without a network.

    ONE CALL PER PLAN, not one per definition. Every definition in the architecture goes into
    a single request; the corpus median is 3-4 definitions and the maximum seen is 11, so a
    per-definition call would cost more than the 7 calls late detection wastes.
    """
    if not enabled():
        return None
    if not definitions_of(arch):
        return None
    t0 = time.time()
    user = build_user(arch, ledger)
    art = {"schema_version": SCHEMA_VERSION, "authority": "ZERO",
           "article_not_written_yet": True,
           "definitions_observed": sorted(definitions_of(arch)),
           "execution": {"execution_id": execution_id or "",
                         "code": PV.code_identity(),
                         "architecture_sha256": _h(arch),
                         "evidence_sha256": _h(_evidence_inputs(arch, ledger)),
                         "system_sha256": PV.sha256_text(SYSTEM),
                         "user_prompt_sha256": PV.sha256_text(user)}}
    try:
        obj = ask(SYSTEM, user)
        errs = validate(obj, arch)
        if errs:
            art.update({"status": "INVALID", "validation_errors": errs[:10]})
        else:
            stolen = sorted(k for k in obj if k in TOOL_OWNED)
            art.update({k: v for k, v in obj.items() if k not in TOOL_OWNED})
            if stolen:
                art["tool_fields_ignored"] = stolen
            art["status"] = "OK"
    except Exception as e:                                        # noqa: BLE001
        # Deliberately bare. A shadow that can end a publication day is not a shadow.
        art.update({"status": "FAILED",
                    "error": "%s: %s" % (type(e).__name__, str(e)[:200])})
    art["wall_seconds"] = round(time.time() - t0, 1)
    art["physical_model_calls"] = (call_meta or {}).get("physical_model_calls")
    try:
        if out_dir is not None:
            import pathlib
            p = pathlib.Path(out_dir)
            p.mkdir(parents=True, exist_ok=True)
            (p / "DEFINITION_CLAIM_SHADOW.json").write_text(
                json.dumps(art, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8")
    except Exception:                                             # noqa: BLE001
        pass
    return art


def _h(obj) -> str:
    try:
        return PV.sha256_text(json.dumps(obj, sort_keys=True, default=str))
    except Exception:                                             # noqa: BLE001
        return ""
