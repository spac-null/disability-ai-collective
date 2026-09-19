"""
planner.py -- Experiment C's evidence/argument review and improved plan (section 13).

WHAT CODEX IS ASKED FOR, and what it is NOT.

Codex receives the frozen source evidence, the frozen Ledger and the commissioning
subject. It does NOT receive the final article, the historical findings, the reason codes
or any owner label -- those live in the subject manifest's `evaluation_only` block, which
nothing here reads.

It returns the compact planning output section 13 specifies: SOURCE BASELINE, DISTINCT
READING, CENTRAL DEPENDENCIES, SUPPORT, MISSING OR DISPUTED, NARRATIVE HIERARCHY,
ALTERNATIVE READING, ARTICLE PLAN -- plus the international-reader pass of section 15.

WHY THE PLAN IS DERIVED DETERMINISTICALLY RATHER THAN WRITTEN BY THE MODEL.

The incumbent Writer takes a story architecture that must satisfy `check_architecture`:
minted-fact refusal, USE/CUT honesty, carrier-occurrence support, turn-relation support,
the evidence hierarchy, final-lens and lens-embodiment validation, the architect-prose
audit and the packet gate. Asking a second model to emit that object from scratch would
mostly measure its ability to guess a schema, and every failure would be a schema failure
wearing an editorial costume.

So Codex supplies EDITORIAL JUDGEMENT ONLY -- which fact carries the article, which facts
are load-bearing, which merely ride along, which are deliberately omitted, and what
narrative work each beat does -- and this module applies that judgement to the frozen
architecture by MUTATING ONLY THE HIERARCHY AND SELECTION FIELDS. The architect's prose
fields (`crip_turn`, `final_lens`, `opening_object_or_event`, `lens_realization`) are
carried through untouched, because those are exactly the fields whose rewriting produces
MINTED_FACT and TURN_RELATION_NOT_SUPPORTED failures. No new factual permission can arise
from a review, which is section 13's own requirement, and here it is structural rather
than merely instructed: a fact Codex does not name cannot enter `use_facts`, and a fact
outside the frozen ledger cannot enter it either.

NO_SUPPORTED_PLAN is a valid answer and is recorded as one. Section 13: the original
thesis is not forced to survive. It is NOT a software failure, and it is NOT a successful
article -- it is reported in the completion denominator (section 18).
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

PROMPT_VERSION = "codex-planner-v1"

LOAD_BEARING = "LOAD_BEARING"
SUPPORTING = "SUPPORTING"

# Section 15. When the plan needs an explanation the evidence does not carry, it says so
# in this exact word rather than inventing one.
RESEARCH_NEEDED = "RESEARCH_NEEDED_BEFORE_DRAFTING"

PLANNER_SYSTEM = """You are an editor reviewing the evidence behind one commissioned
article before it is written. You are not writing the article.

You have the frozen source material and a frozen Ledger of numbered facts extracted from
it. Every fact id you name must come from that Ledger. You may not introduce a fact,
a number, a name, a date or a relationship that the Ledger does not carry. A review
creates no new factual permission.

Your job is to decide what this article can honestly be ABOUT, and what carries it.

Judge the evidence, not the ambition. If the strongest supported reading is narrower than
the commissioning subject, say so and plan the narrower article. If the evidence does not
support an article at all, set "no_supported_plan": true and explain why. That is a valid
and useful answer; a forced thesis is not.

Reply with ONE JSON object and nothing else:

{
 "source_baseline": "what the strongest existing coverage already explains",
 "distinct_reading": "what additional understanding this article could support",
 "central_dependencies": ["the factual relationships that must hold for that reading"],
 "support": [{"dependency": "...", "fact_ids": ["F03"], "passage": "exact quoted span"}],
 "missing_or_disputed": ["what is not established, ambiguous or contradicted"],
 "alternative_reading": "what would undermine or materially narrow the argument",
 "article_plan": "what changes for the reader from opening to ending",
 "narrative_hierarchy": {
   "primary_carrier": "F07",
   "load_bearing": ["F07", "F12"],
   "supporting": {"F03": ["F07"]},
   "deliberate_omissions": [{"fact_id": "F44", "reason": "true but does not advance"}]
 },
 "beat_functions": {"B1": "REVEAL", "B2": "COMPLICATE"},
 "international_reader_context": [
   {"term": "an institution, acronym or local term an international reader needs",
    "explanation": "the short explanation, IF the evidence carries it",
    "fact_ids": ["F09"],
    "status": "SUPPORTED_BY_EVIDENCE or RESEARCH_NEEDED_BEFORE_DRAFTING",
    "bounded_query": "the research question a future live workflow should ask"}],
 "no_supported_plan": false,
 "no_supported_plan_reason": ""
}

RULES FOR THE HIERARCHY.
 - "primary_carrier" is ONE fact id, and it must appear in "load_bearing".
 - Every fact you keep is either load_bearing or a key in "supporting".
 - Each "supporting" fact maps to the load-bearing fact(s) it makes intelligible.
 - A supporting fact must share a beat with a fact it supports; the beats and the facts
   each beat allows are given to you.
 - Omit aggressively. A plan that keeps every true fact is a plan that repeats.
 - "beat_functions" assigns each beat id EXACTLY ONE of these five, and no other word:
   REVEAL, COMPLICATE, EXPLAIN, REVERSE, RESOLVE.

RULES FOR INTERNATIONAL CONTEXT. If the evidence carries the explanation, cite the fact
ids. If it does not, set status to RESEARCH_NEEDED_BEFORE_DRAFTING and write the bounded
query. Never invent the explanation."""


def ledger_block(ledger: dict) -> str:
    lines = []
    for fid in sorted(ledger):
        f = ledger[fid]
        if isinstance(f, dict):
            prop = f.get("proposition") or f.get("text") or ""
            src = f.get("source_id") or ""
            lines.append("  %s  %s  [%s]" % (fid, prop, src))
        else:
            lines.append("  %s  %s" % (fid, f))
    return "\n".join(lines)


def beats_block(arch: dict) -> str:
    lines = []
    for b in arch.get("beats") or []:
        lines.append("  %s  facts_allowed=%s  %s"
                     % (b.get("beat_id"), b.get("facts_allowed"),
                        (b.get("beat_intent") or b.get("intent") or "")[:120]))
    return "\n".join(lines)


def sources_block(sources: list, per_source_chars: int = 6000) -> str:
    out = []
    for s in sources:
        out.append("--- SOURCE %s | %s | %s\n%s"
                   % (s.get("source_id"), s.get("publisher") or "",
                      s.get("title") or "", (s.get("text") or "")[:per_source_chars]))
    return "\n\n".join(out)


def planner_prompt(subject: str, ledger: dict, arch: dict, sources: list) -> str:
    return "\n\n".join([
        "THE COMMISSIONING SUBJECT\n%s" % subject,
        "THE FROZEN LEDGER -- the only facts you may name\n%s" % ledger_block(ledger),
        "THE BEATS ALREADY PLANNED, with the facts each allows\n%s" % beats_block(arch),
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


def derive_architecture(base_arch: dict, plan: dict, ledger: dict) -> tuple:
    """Apply Codex's hierarchy to the frozen architecture. Returns (arch, errors).

    Only selection and hierarchy fields move. Every prose field is carried through
    byte-identical, so this cannot mint a fact or a relation.
    """
    errs = []
    h = plan.get("narrative_hierarchy") or {}
    carrier = h.get("primary_carrier")
    load = [f for f in (h.get("load_bearing") or []) if isinstance(f, str)]
    sup_map = {k: [v for v in (vs or []) if isinstance(v, str)]
               for k, vs in (h.get("supporting") or {}).items()
               if isinstance(k, str)}

    known = set(ledger)
    base_use = set(base_arch.get("use_facts") or [])

    # A FACT MAY ONLY BE NARROWED, NEVER ADDED. Anything outside the original plan's own
    # use_facts is dropped here rather than argued with downstream: the pilot compares
    # planning strategies on identical evidence, and a plan that reaches for a fact the
    # incumbent never selected is not the comparison this experiment is running.
    def keep(fs):
        return [f for f in fs if f in known and f in base_use]

    load, dropped_load = keep(load), [f for f in load if f not in base_use or f not in known]
    sup_map = {k: keep(v) for k, v in sup_map.items() if k in known and k in base_use}
    sup_map = {k: v for k, v in sup_map.items() if v}
    if dropped_load:
        errs.append("planner named load-bearing facts outside the frozen plan's own "
                    "selection and they were dropped: %s" % sorted(dropped_load)[:8])

    use = sorted(set(load) | set(sup_map))
    if not use:
        return None, errs + ["the plan keeps no usable fact"]
    if carrier not in load:
        if load:
            errs.append("primary_carrier %r was not load-bearing; the first load-bearing "
                        "fact was used instead" % carrier)
            carrier = load[0]
        else:
            return None, errs + ["the plan declares no load-bearing fact"]

    roles = {f: LOAD_BEARING for f in load}
    roles.update({f: SUPPORTING for f in sup_map})

    arch = dict(base_arch)
    arch["use_facts"] = use
    arch["evidence_roles"] = roles
    arch["supports"] = sup_map
    arch["primary_carrier"] = carrier

    # BEATS: prune to the kept facts, drop beats left with nothing, assign the function.
    fns = plan.get("beat_functions") or {}
    beats = []
    for b in base_arch.get("beats") or []:
        allowed = [f for f in (b.get("facts_allowed") or []) if f in use]
        if not allowed:
            continue
        nb = dict(b, facts_allowed=allowed)
        fn = fns.get(b.get("beat_id"))
        if fn in ST.BEAT_FUNCTIONS:
            nb["beat_function"] = fn
        elif not nb.get("beat_function"):
            errs.append("beat %s has no valid beat_function from the planner"
                        % b.get("beat_id"))
        beats.append(nb)
    if not beats:
        return None, errs + ["no beat survived the plan's fact selection"]
    arch["beats"] = beats

    # CUT HONESTY. A fact the plan drops must be declared cut, with a reason.
    reasons = {o.get("fact_id"): o.get("reason")
               for o in (h.get("deliberate_omissions") or []) if isinstance(o, dict)}
    cut = list(base_arch.get("cut_evidence") or [])
    already = {c.get("fact_id") if isinstance(c, dict) else c for c in cut}
    for f in sorted(base_use - set(use)):
        if f in already:
            continue
        cut.append({"fact_id": f,
                    "reason": reasons.get(f)
                    or "omitted by the evidence review: true but not load-bearing "
                       "for the supported reading"})
    arch["cut_evidence"] = cut
    return arch, errs


def plan_subject(provider, subject_manifest: dict, *, repair_provider=None) -> dict:
    """One planner call, one optional repair call. Returns the cell payload."""
    gi = subject_manifest["generation_inputs"]
    ledger, base_arch = gi["ledger"], gi["architecture"]
    prompt = planner_prompt(gi["subject"], ledger, base_arch, gi["sources"])

    comp = provider.complete(PLANNER_SYSTEM, prompt)
    plan, perrs = parse_plan(comp.text)
    out = {
        "prompt_version": PROMPT_VERSION,
        "provider": comp.identity(),
        "model_calls": 1,
        "parse_errors": perrs,
        "plan": plan,
        "raw_reply_sha256": CP.C.sha256_text(comp.text),
        "prompt_sha256": CP.C.sha256_text(prompt),
    }
    if plan is None:
        out["status"] = "PLANNER_REPLY_UNUSABLE"
        return out
    if plan.get("no_supported_plan"):
        # Section 13/18: valid, not a software failure, and not a successful article.
        out["status"] = "NO_SUPPORTED_PLAN"
        out["reason"] = plan.get("no_supported_plan_reason") or ""
        return out

    arch, derr = derive_architecture(base_arch, plan, ledger)
    out["derivation_notes"] = derr
    if arch is None:
        out["status"] = "PLAN_DERIVATION_FAILED"
        return out

    verrs = CP.check_architecture(arch, ledger)
    out["architecture_errors"] = verrs
    if verrs:
        out["status"] = "DERIVED_PLAN_INVALID"
        out["architecture"] = arch
        return out

    out["status"] = "PASS"
    out["architecture"] = arch
    out["plan_sha256"] = CP.C.sha256_text(json.dumps(arch, sort_keys=True))
    out["facts_kept"] = len(arch["use_facts"])
    out["facts_in_base_plan"] = len(base_arch.get("use_facts") or [])
    return out
