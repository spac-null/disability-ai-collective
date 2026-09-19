"""
planner.py -- Experiment C: evidence-grounded REPLANNING over the frozen Ledger.

See PROTOCOL_AMENDMENT_01.md in the experiment root for why this module was rewritten.
In short: the first version held the retained beat structure fixed and let Codex only
rank the facts inside it. That made Arm C a hierarchy retrofit rather than the replanning
treatment section 13 commissions, and it caused a real conflation -- "these historical
beats cannot host the current hierarchy" was reported as though it were "this evidence
cannot support a valid plan". The first is a property of one past planning choice. The
second is a claim about the evidence, and the old adapter could not test it.

WHAT IS FROZEN, and enforced here rather than merely requested:
  * the subject and commissioning question;
  * the source set;
  * the approved Ledger -- every fact id in the plan must exist in it, and nothing else
    may enter. No fact from model memory, no unapproved source text promoted into Ledger
    permission, no new research;
  * the qualifications, attribution, chronology and event boundaries those facts carry;
  * the production validators, which are imported and called unmodified.

WHAT ARM C MAY CHANGE, within that same approved factual universe: which eligible facts
it selects, which are load-bearing and which merely supporting, what it omits, how the
beats are ordered, combined or split, which eligible fact ids sit in which beat, the
opening, the ending, how narrow the supported interpretation is, and which fact carries
it.

THE ADAPTER DOES NOT REPAIR THE PLAN. The previous version promoted facts to
load-bearing, re-pointed `supports` and substituted the carrier when the planner's own
choices did not validate. Every one of those was the adapter quietly doing the planning
it was supposed to be measuring. Now the planner owns plan validity: the adapter
assembles what it returns, carries forward only the fields it does not supply, runs
`composition.check_architecture` unmodified, and reports the result.

ONE ATTEMPT PER SUBJECT. No retry until a supported plan appears.

THE FOUR OUTCOMES, kept distinct:
    PASS                            a valid plan over the frozen evidence
    NO_SUPPORTED_PLAN               the planner replanned and reports that the evidence
                                    supports no valid article
    PLAN_VALIDATION_FAILED          a returned plan violates the contract
    TECHNICAL_FAILURE               transport, parsing or adapter failure
`HISTORICAL_PLAN_INCOMPATIBLE` is recorded as a DESCRIPTIVE property of the retained
architecture, never as a reason to skip replanning.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from new_engine_v1 import composition as CP                        # noqa: E402
from new_engine_v1 import story as ST                              # noqa: E402

PROMPT_VERSION = "codex-replanner-v2"
C_CONTRACT = "C2-replanning"

LOAD_BEARING = "LOAD_BEARING"
SUPPORTING = "SUPPORTING"

RESEARCH_NEEDED = "RESEARCH_NEEDED_BEFORE_DRAFTING"

# Outcomes. Distinct on purpose; see the module docstring and the amendment.
PASS = "PASS"
NO_SUPPORTED_PLAN = "NO_SUPPORTED_PLAN"
PLAN_VALIDATION_FAILED = "PLAN_VALIDATION_FAILED"
TECHNICAL_FAILURE = "TECHNICAL_FAILURE"
HISTORICAL_PLAN_INCOMPATIBLE = "HISTORICAL_PLAN_INCOMPATIBLE"

# Fields the planner may not touch unless it supplies its own: these carry claim-bearing
# prose whose support is checked against the ledger. Carried forward from the retained
# architecture when the planner does not replace them.
CARRIED_FORWARD = ("article_type", "crip_turn", "final_lens", "lens_realization",
                   "reader_initial_state", "crip_turn_rereads", "definitions",
                   "prohibitions")


REPLANNER_SYSTEM = """You are replanning one commissioned article from its evidence.

You are given the commissioning subject, the frozen source material, and a frozen Ledger
of numbered facts extracted from that material. THE LEDGER IS THE WHOLE OF WHAT YOU MAY
SAY. Every fact id you name must come from it. You may not introduce a fact, number,
name, date, place or relationship the Ledger does not carry, you may not reach into the
source text for something the Ledger did not approve, and you may not use anything you
happen to know about this subject from elsewhere.

You are also shown the article's PREVIOUS plan. It is context, not a constraint. You may
keep none of it. You may select different facts, order the story differently, use fewer
or more beats, put different facts in different beats, open somewhere else and end
somewhere else.

Judge the evidence, not the ambition. If the strongest supported reading is narrower than
the commissioning subject, plan the narrower article. If the evidence supports no article
at all, set "no_supported_plan": true and say why -- that is a valid and useful answer,
and a forced thesis is not.

Reply with ONE JSON object and nothing else:

{
 "source_baseline": "what the strongest existing coverage already explains",
 "distinct_reading": "what additional understanding this article could support",
 "central_dependencies": ["the factual relationships that must hold for that reading"],
 "support": [{"dependency": "...", "fact_ids": ["F03"], "passage": "exact quoted span"}],
 "missing_or_disputed": ["what is not established, ambiguous or contradicted"],
 "alternative_reading": "what would undermine or materially narrow the argument",
 "article_plan": "what changes for the reader from opening to ending",

 "story_spine": "ONE sentence naming the path through the story",
 "opening_object_or_event": "the concrete thing the article opens on",
 "ending_move": "what the ending does",

 "beats": [
   {"beat_id": "B1",
    "concrete_carrier": "the concrete thing this beat is about -- a NOUN PHRASE, not a
                         narrated event",
    "why_reader_wants_next": "why the reader reads on (every beat but the last)",
    "facts_allowed": ["F03", "F07"],
    "beat_function": "REVEAL"}],

 "use_facts": ["F03", "F07"],
 "evidence_roles": {"F07": "LOAD_BEARING", "F03": "SUPPORTING"},
 "supports": {"F03": ["F07"]},
 "primary_carrier": "F07",
 "cut_evidence": [{"evidence_id": "F44", "reason": "BACKGROUND_NOT_NEEDED"}],

 "international_reader_context": [
   {"term": "an institution, acronym or local term an international reader needs",
    "explanation": "the short explanation, IF the evidence carries it",
    "fact_ids": ["F09"],
    "status": "SUPPORTED_BY_EVIDENCE or RESEARCH_NEEDED_BEFORE_DRAFTING",
    "bounded_query": "the research question a future live workflow should ask"}],

 "no_supported_plan": false,
 "no_supported_plan_reason": ""
}

THE CONTRACT YOUR PLAN MUST SATISFY. It is checked mechanically and a violation is
reported, not repaired.

 SELECTION
  - Every id in use_facts, in any beat's facts_allowed, and in cut_evidence must be a
    Ledger fact id.
  - use_facts must be EXACTLY the union of the beats' facts_allowed. A fact you use is a
    fact some beat allows.
  - cut_evidence must be non-empty and must not overlap use_facts. Selection that
    discards nothing is not selection. Cut aggressively: a plan that keeps every true
    fact is a plan that repeats.
  - Each cut reason must be EXACTLY ONE of these nine words:
    REDUNDANT_PROOF, BACKGROUND_NOT_NEEDED, SECOND_EXAMPLE_SAME_POINT, NAME_OVERLOAD,
    CONCEPT_OVERLOAD, BREAKS_STORY_MOMENTUM, PROVENANCE_ONLY, MACHINE_BOUNDARY_ONLY,
    INTERESTING_BUT_WRONG_STORY.

 SHAPE
  - At least two beats. Unique beat ids. Every beat needs a concrete_carrier; every beat
    but the last needs why_reader_wants_next.
  - beat_function is EXACTLY ONE of: REVEAL, COMPLICATE, EXPLAIN, REVERSE, RESOLVE.
  - story_spine is ONE sentence.

 HIERARCHY
  - evidence_roles assigns every used fact exactly one of LOAD_BEARING or SUPPORTING,
    and covers use_facts exactly.
  - Each SUPPORTING fact names in "supports" the LOAD_BEARING fact(s) it makes
    intelligible, and must SHARE A BEAT with one of them.
  - primary_carrier is one LOAD_BEARING used fact. At least two beats must allow it and
    the LAST beat must allow it: the ending returns to the carrier with changed
    understanding rather than merely stopping.
  - Choose a carrier the story genuinely returns to. DO NOT scatter a fact across beats
    just to satisfy the rule -- a beat may only allow a fact that beat is really about.

 CARRIERS AND CLAIMS
  - A concrete_carrier NAMES a thing. It must not narrate an event the Ledger holds only
    as a rule or a description. "the brake that does not move" is a carrier; "the bike
    that coasted through the junction" asserts a ride nobody reported.
  - Do not assert a relationship between two facts that the Ledger does not itself
    assert. Two true facts side by side are not a cause, a consequence, an equivalence,
    a comparison, a superlative or a generalisation.

 INTERNATIONAL CONTEXT
  - If the evidence carries the explanation, cite the fact ids. If it does not, set
    status to RESEARCH_NEEDED_BEFORE_DRAFTING and write the bounded query a future live
    workflow should ask. Never invent the explanation."""


def ledger_block(ledger: dict) -> str:
    lines = []
    for fid in sorted(ledger):
        f = ledger[fid]
        if isinstance(f, dict):
            prop = f.get("proposition") or f.get("text") or ""
            src = f.get("source_id") or ""
            q = f.get("qualifier") or ""
            lines.append("  %s  %s%s  [%s]"
                         % (fid, prop, (" (%s)" % q) if q else "", src))
        else:
            lines.append("  %s  %s" % (fid, f))
    return "\n".join(lines)


def previous_plan_block(arch: dict) -> str:
    """The retained plan, shown as CONTEXT. Explicitly not a constraint."""
    lines = ["  story_spine: %s" % (arch.get("story_spine") or ""),
             "  opening: %s" % (arch.get("opening_object_or_event") or ""),
             "  ending_move: %s" % (arch.get("ending_move") or ""),
             "  beats:"]
    for b in arch.get("beats") or []:
        lines.append("    %s  facts_allowed=%s  carrier=%r"
                     % (b.get("beat_id"), b.get("facts_allowed"),
                        (b.get("concrete_carrier") or "")[:80]))
    return "\n".join(lines)


def sources_block(sources: list, per_source_chars: int = 6000) -> str:
    return "\n\n".join(
        "--- SOURCE %s | %s | %s\n%s"
        % (s.get("source_id"), s.get("publisher") or "", s.get("title") or "",
           (s.get("text") or "")[:per_source_chars])
        for s in sources)


def planner_prompt(subject: str, ledger: dict, arch: dict, sources: list) -> str:
    return "\n\n".join([
        "THE COMMISSIONING SUBJECT\n%s" % subject,
        "THE FROZEN LEDGER -- the only facts you may name\n%s" % ledger_block(ledger),
        "THE PREVIOUS PLAN -- context only, keep none of it if the evidence suggests "
        "otherwise\n%s" % previous_plan_block(arch),
        "THE SOURCE MATERIAL\n%s" % sources_block(sources),
        "Reply with one JSON object.",
    ])


def parse_plan(reply: str) -> tuple:
    txt = (reply or "").strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\n?", "", txt)
        txt = re.sub(r"\n?```\s*$", "", txt)
    i, j = txt.find("{"), txt.rfind("}")
    if i < 0 or j <= i:
        return None, ["the planner reply carries no JSON object"]
    try:
        return json.loads(txt[i:j + 1]), []
    except Exception as exc:                                       # noqa: BLE001
        return None, ["the planner reply is not valid JSON: %s" % exc]


def historical_plan_compatible(arch: dict) -> tuple:
    """DESCRIPTIVE ONLY. Can the RETAINED beats host the current hierarchy unchanged?

    This was once a gate that skipped the planner, which is the conflation
    PROTOCOL_AMENDMENT_01 corrects. It is kept because the answer is a genuine finding
    about how far the pre-2026-09-11 architectures sit from the current contract -- but
    it never decides whether replanning runs.
    """
    beats = arch.get("beats") or []
    if not beats:
        return False, "the retained plan carries no beats"
    occ = {}
    for b in beats:
        for f in (b.get("facts_allowed") or []):
            occ[f] = occ.get(f, 0) + 1
    recurring = [f for f in (beats[-1].get("facts_allowed") or []) if occ.get(f, 0) >= 2]
    if recurring:
        return True, ""
    return False, ("the retained closing beat %s allows no fact that any earlier retained "
                   "beat also allows, so the retained beats cannot host a recurring "
                   "primary carrier unchanged" % beats[-1].get("beat_id"))


def unknown_ids(plan: dict, ledger: dict) -> list:
    """Every fact id the plan names that the frozen Ledger does not carry.

    THE ONE RESTRICTION THE ADAPTER STILL ENFORCES STRUCTURALLY, because it is the one
    that is a factual permission rather than a planning choice: a plan cannot reach
    outside the approved Ledger. Everything else is checked by the production validators
    and reported, not corrected.
    """
    known = set(ledger)
    named = set(plan.get("use_facts") or [])
    named |= {f for b in (plan.get("beats") or []) if isinstance(b, dict)
              for f in (b.get("facts_allowed") or [])}
    named |= set((plan.get("evidence_roles") or {}))
    named |= set((plan.get("supports") or {}))
    named |= {x for v in (plan.get("supports") or {}).values() for x in (v or [])}
    named |= {c.get("evidence_id") for c in (plan.get("cut_evidence") or [])
              if isinstance(c, dict)}
    if plan.get("primary_carrier"):
        named.add(plan["primary_carrier"])
    return sorted(x for x in named if isinstance(x, str) and x not in known)


def build_architecture(base_arch: dict, plan: dict) -> dict:
    """Assemble the planner's replan into an architecture object.

    Assembly only. Nothing here decides anything the planner was asked to decide: no
    fact is added or removed, no role is changed, no carrier is substituted, no beat is
    restored. Fields the planner did not supply are carried forward from the retained
    architecture so that claim-bearing prose it did not rewrite keeps the wording that
    already validated.
    """
    arch = {k: base_arch.get(k) for k in CARRIED_FORWARD if k in base_arch}
    for field in ("story_spine", "opening_object_or_event", "ending_move"):
        arch[field] = plan.get(field) or base_arch.get(field)
    arch["beats"] = [b for b in (plan.get("beats") or []) if isinstance(b, dict)]
    arch["use_facts"] = list(plan.get("use_facts") or [])
    arch["evidence_roles"] = dict(plan.get("evidence_roles") or {})
    arch["supports"] = dict(plan.get("supports") or {})
    arch["primary_carrier"] = plan.get("primary_carrier")
    arch["cut_evidence"] = [c for c in (plan.get("cut_evidence") or [])
                            if isinstance(c, dict)]
    return arch


def plan_subject(provider, subject_manifest: dict) -> dict:
    """One replanning attempt. Assemble, validate, report. No repair, no retry."""
    gi = subject_manifest["generation_inputs"]
    ledger, base_arch = gi["ledger"], gi["architecture"]

    compatible, why = historical_plan_compatible(base_arch)
    out = {
        "prompt_version": PROMPT_VERSION,
        "c_contract": C_CONTRACT,
        "model_calls": 1,
        # Descriptive, never a gate. See PROTOCOL_AMENDMENT_01.
        "historical_plan_compatible": compatible,
        "historical_plan_note": (HISTORICAL_PLAN_INCOMPATIBLE if not compatible else ""),
        "historical_plan_reason": why,
    }

    prompt = planner_prompt(gi["subject"], ledger, base_arch, gi["sources"])
    comp = provider.complete(REPLANNER_SYSTEM, prompt)
    out["provider"] = comp.identity()
    out["prompt_sha256"] = CP.C.sha256_text(prompt)
    out["raw_reply_sha256"] = CP.C.sha256_text(comp.text)

    plan, perrs = parse_plan(comp.text)
    out["parse_errors"] = perrs
    if plan is None:
        out["status"] = TECHNICAL_FAILURE
        out["reason"] = "; ".join(perrs)
        return out
    out["plan"] = plan

    if plan.get("no_supported_plan"):
        out["status"] = NO_SUPPORTED_PLAN
        out["reason"] = plan.get("no_supported_plan_reason") or ""
        return out

    outside = unknown_ids(plan, ledger)
    if outside:
        out["status"] = PLAN_VALIDATION_FAILED
        out["reason"] = ("the plan names fact ids that are not in the frozen Ledger: %s"
                         % outside[:10])
        out["unknown_fact_ids"] = outside
        return out

    arch = build_architecture(base_arch, plan)
    out["architecture"] = arch
    verrs = CP.check_architecture(arch, ledger)
    out["architecture_errors"] = verrs
    if verrs:
        out["status"] = PLAN_VALIDATION_FAILED
        out["reason"] = "; ".join(verrs[:4])
        return out

    out["status"] = PASS
    out["plan_sha256"] = CP.C.sha256_text(json.dumps(arch, sort_keys=True))
    out["facts_kept"] = len(arch["use_facts"])
    out["facts_in_ledger"] = len(ledger)
    out["facts_in_retained_plan"] = len(base_arch.get("use_facts") or [])
    out["beats"] = len(arch["beats"])
    out["beats_in_retained_plan"] = len(base_arch.get("beats") or [])
    return out
