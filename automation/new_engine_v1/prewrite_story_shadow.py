"""prewrite_story_shadow.py -- what the plan looks like before a sentence exists.

ZERO AUTHORITY. This module cannot hold a candidate, change the architecture, change
what the Writer is given, cause a retry, or influence any verdict. It reads the frozen
pre-writing state, asks one bounded question about it, and writes a file. If it fails in
any way the composition continues exactly as if it had never run.

WHY IT EXISTS. Reader has been holding articles on ACCESSIBLE_READING, READABILITY,
MOMENTUM, RESEARCH_LOAD and ENDING -- after the whole article has been written, grounded,
safety-audited and fact-checked. A doomed composition costs seven to ten model calls and
thirteen to twenty-seven minutes AFTER Architecture. The open question is which of those
failures were already visible in the plan.

That question cannot be answered yet. The retained Reader-audited runs are almost all
from before 2026-09-11, when `beat_function` and `primary_carrier` did not exist, and
there is not one retained run that passed the Reader to serve as a control. So this
module does not decide anything: it collects the evidence that a future audit would need,
on natural runs, under the contract that actually ships.

WHAT IT MUST NEVER BECOME without that evidence: a gate. There is no PASS, no HOLD, no
score and no publishability verdict in the schema on purpose.
"""
from __future__ import annotations

import json
import os
import time

SCHEMA_VERSION = "prewrite-story-shadow-v1"
ENV_FLAG = "CRIPMINDS_PREWRITE_STORY_SHADOW"

MOVES = ("REVEALS", "DEEPENS_MECHANISM", "COMPLICATES", "REVERSES", "CONNECTS",
         "RESOLVES", "PROVENANCE_ONLY", "REPEATS_PREVIOUS_MOVE", "UNCLEAR")
CONCEPT_STATUS = ("READY", "EVIDENCE_GAP", "CIRCULAR_OR_UNCLEAR")
GROUNDING_STATUS = ("EVIDENCE_BACKED", "INTERPRETIVE_BUT_LICENSED",
                    "REQUIRED_BUT_UNSUPPORTED", "UNCLEAR")
LANDS = ("YES", "NO", "UNCLEAR")
ARGUMENT = ("ARGUMENT_READY", "SUMMARY_ONLY", "UNCLEAR")
STAGES = ("RESEARCH", "LEDGER", "WORTH", "ARCHITECTURE", "UNKNOWN")


def enabled(env=None) -> bool:
    """OFF unless explicitly switched on. An unset variable is OFF, like every other
    shadow in this engine -- see SHADOW_CAPTURE and CRIPMINDS_SEMANTIC_CLAIM_SHADOW."""
    v = (env if env is not None else os.environ).get(ENV_FLAG, "").strip().lower()
    return v in ("1", "on", "true", "yes")


SYSTEM = (
    "You are reading a plan for an article that has NOT been written. No prose exists "
    "yet. You are not judging quality and you are not deciding whether anything may "
    "proceed -- nothing you say changes what happens next.\n"
    "\n"
    "ONE QUESTION: does this plan already contain the ingredients a clear, grounded, "
    "reader-moving article needs, and where are the gaps?\n"
    "\n"
    "The evidence is FROZEN. You may not invent a fact, a definition, a scene, a person "
    "or a motive, and you may not cite a fact id that is not in the ledger you are "
    "given. Where the plan needs something the evidence does not carry, SAY SO -- that "
    "is the single most useful thing you can report, because it is knowable now and "
    "expensive to discover after the article has been written.\n"
    "\n"
    "CARRIER. The concrete thing a reader enters through: a person, object, action, "
    "decision, interaction, conflict, material process or observable mechanism. A "
    "research apparatus -- a search, a protocol, a database list -- is not automatically "
    "the carrier. It is the carrier only when the procedure acts on someone or "
    "materially produces the thing being examined.\n"
    "\n"
    "DISCOVERY ARC. For each beat, what does the reader understand before it, and what "
    "is new after it? The useful question is not which dramatic category it belongs to. "
    "It is whether the beat changes understanding at all, or is present because the "
    "material happened to be available. Say REPEATS_PREVIOUS_MOVE or PROVENANCE_ONLY "
    "plainly when that is what it is.\n"
    "\n"
    "LOAD-BEARING CONCEPTS. Only the terms a reader MUST understand for the mechanism or "
    "argument to work -- not every unusual word. For each, can it be explained in "
    "ordinary language FROM THE FROZEN EVIDENCE? A gloss that restates its own term "
    "explains nothing. If the evidence cannot license a plain explanation of something "
    "the article cannot do without, that is EVIDENCE_GAP, and it is the finding.\n"
    "\n"
    "THE CRIP MINDS TURN. What assumption about bodies, perception, communication, "
    "dependence, assistance, timing, navigation, cognition, sensory processing, "
    "endurance, participation, classification or normal functioning becomes visible "
    "through this concrete material? The disability perspective licenses the QUESTION; "
    "only the frozen evidence licenses the FACTS. Imperfection is not disability, "
    "friction is not accessibility, and another marginalised group is not a proxy. If "
    "the turn is forced or generic, say that.\n"
    "\n"
    "LANDING. What does the reader understand at the end that they did not at the start? "
    "An ending may legitimately return to the opening carrier -- returning is not "
    "repeating. The question is whether the MEANING has changed. If the planned ending "
    "only restates what the reader already had, say NO.\n"
    "\n"
    "Be concrete and brief. Do not write an essay. Do not praise the plan. Words like "
    "'strong', 'compelling' and 'excellent' carry no information unless a specific "
    "reason is attached, and a field that reads as praise is a field that was not "
    "thought about."
)

SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"theme_statement": "what this story shows the reader about the world, not what '
    'the source is about",\n'
    ' "central_question": "the question that pulls the reader through",\n'
    ' "concrete_entry": {"description": "...", "fact_ids": ["F.."]},\n'
    ' "reader_promise": "what the reader understands by continuing",\n'
    ' "discovery_arc": [{"beat_id": "B1", "before": "...", "after": "...",\n'
    '                    "move": "%(moves)s", "fact_ids": ["F.."]}],\n'
    ' "load_bearing_concepts": [{"concept": "...", "why_load_bearing": "...",\n'
    '                            "plain_language_meaning": "... or \\"\\" if the evidence '
    'cannot carry one",\n'
    '                            "evidence_fact_ids": ["F.."],\n'
    '                            "status": "%(cstat)s"}],\n'
    ' "grounding_readiness": [{"planned_element": "...", "status": "%(gstat)s",\n'
    '                          "fact_ids": ["F.."]}],\n'
    ' "crip_minds_turn": "... or \\"\\" if the material does not carry one",\n'
    ' "why_carrier_reveals_it": "...",\n'
    ' "research_budget": {"load_bearing": ["..."], "credibility_once": ["..."],\n'
    '                     "provenance_only": ["..."], "cuttable": ["..."]},\n'
    ' "landing": {"reader_at_start": "...", "reader_at_end": "...",\n'
    '             "changed_understanding": "...", "lands": "%(lands)s"},\n'
    ' "argument_readiness": "%(arg)s",\n'
    ' "cut_before_writing": [{"material": "...", "label": '
    '"INTERESTING_BUT_NOT_STORY|PROVENANCE_ONLY|POSSIBLY_CUTTABLE"}],\n'
    ' "risks": [{"type": "...", "description": "...",\n'
    '            "responsible_stage_if_real": "%(stages)s"}]}\n'
    "No prose outside the JSON. No verdict field, no score, no recommendation about "
    "whether to proceed -- that is not yours to give."
) % {"moves": "|".join(MOVES), "cstat": "|".join(CONCEPT_STATUS),
     "gstat": "|".join(GROUNDING_STATUS), "lands": "|".join(LANDS),
     "arg": "|".join(ARGUMENT), "stages": "|".join(STAGES)}


def build_user(pack: dict, ledger: dict, worth: dict, arch: dict,
               packet_text: str = "") -> str:
    """Only frozen pre-writing material. No prose, no Reader feedback, no outcome."""
    cand = (worth or {}).get("story_candidate") or {}
    lens = (worth or {}).get("worth_gate") or {}
    L = ["SUBJECT", "  " + str((pack or {}).get("subject", ""))[:400], "",
         "WHAT THIS PUBLICATION SAW IN IT",
         "  " + str(lens.get("lens_claim") or "")[:400], "",
         "THE PLAN",
         "  spine:   " + str((arch or {}).get("story_spine") or "")[:400],
         "  opens on: " + str((arch or {}).get("opening_object_or_event") or "")[:300],
         "  carrier:  " + str((arch or {}).get("primary_carrier") or ""),
         "  ends on:  " + str((arch or {}).get("ending_move") or "")[:300], ""]
    L.append("BEATS")
    for b in (arch or {}).get("beats") or []:
        L.append("  %s [%s] %s" % (b.get("beat_id"), b.get("beat_function") or "-",
                                   str(b.get("concrete_carrier") or "")[:120]))
        L.append("      %s" % str(b.get("happens") or "")[:300])
        if b.get("facts_allowed"):
            L.append("      facts: %s" % ", ".join(str(f) for f in b["facts_allowed"]))
    L.append("")
    if (arch or {}).get("definitions"):
        L.append("DEFINITIONS THE PLAN DECLARES")
        for k, v in (arch["definitions"] or {}).items():
            L.append("  %s -- %s" % (k, str(v)[:200]))
        L.append("")
    L.append("FROZEN FACTS")
    for fid, f in list((ledger or {}).items()):
        if isinstance(f, dict):
            L.append("  %s  %s" % (fid, str(f.get("proposition", ""))[:220]))
    L.append("")
    if packet_text:
        L.append("(the writer packet renders from exactly the above)")
        L.append("")
    L.append(SCHEMA)
    return "\n".join(L)


def validate(obj, ledger: dict) -> list:
    """Shape, vocabulary and fact-id honesty. Errors invalidate the ARTIFACT only.

    A fact id the ledger does not contain is the one thing that must never pass: an
    artifact citing invented evidence would be worse than no artifact, because a future
    audit would count it as a real observation.
    """
    errs = []
    if not isinstance(obj, dict):
        return ["shadow reply is not an object"]
    known = set(ledger or {})

    def ids(v, where):
        for f in (v or []):
            if str(f) not in known:
                errs.append("%s cites %r, which is not in the frozen ledger" % (where, f))

    for k in ("theme_statement", "central_question", "reader_promise",
              "why_carrier_reveals_it"):
        if not isinstance(obj.get(k), str):
            errs.append("%s missing or not a string" % k)
    ce = obj.get("concrete_entry")
    if not isinstance(ce, dict) or not str(ce.get("description") or "").strip():
        errs.append("concrete_entry missing a description")
    else:
        ids(ce.get("fact_ids"), "concrete_entry")
    arc = obj.get("discovery_arc")
    if not isinstance(arc, list) or not arc:
        errs.append("discovery_arc is empty")
    else:
        for i, b in enumerate(arc, 1):
            if not isinstance(b, dict):
                errs.append("discovery_arc[%d] is not an object" % i)
                continue
            if b.get("move") not in MOVES:
                errs.append("discovery_arc[%d] move %r is not one of the declared moves"
                            % (i, b.get("move")))
            ids(b.get("fact_ids"), "discovery_arc[%d]" % i)
    for i, c in enumerate(obj.get("load_bearing_concepts") or [], 1):
        if not isinstance(c, dict):
            errs.append("load_bearing_concepts[%d] is not an object" % i)
            continue
        if c.get("status") not in CONCEPT_STATUS:
            errs.append("load_bearing_concepts[%d] status %r is not declared"
                        % (i, c.get("status")))
        ids(c.get("evidence_fact_ids"), "load_bearing_concepts[%d]" % i)
    for i, g in enumerate(obj.get("grounding_readiness") or [], 1):
        if not isinstance(g, dict):
            errs.append("grounding_readiness[%d] is not an object" % i)
            continue
        if g.get("status") not in GROUNDING_STATUS:
            errs.append("grounding_readiness[%d] status %r is not declared"
                        % (i, g.get("status")))
        ids(g.get("fact_ids"), "grounding_readiness[%d]" % i)
    land = obj.get("landing")
    if not isinstance(land, dict) or land.get("lands") not in LANDS:
        errs.append("landing.lands missing or not one of %s" % (LANDS,))
    if obj.get("argument_readiness") not in ARGUMENT:
        errs.append("argument_readiness %r is not declared" % obj.get("argument_readiness"))
    for i, r in enumerate(obj.get("risks") or [], 1):
        if isinstance(r, dict) and r.get("responsible_stage_if_real") not in STAGES:
            errs.append("risks[%d] responsible_stage_if_real %r is not declared"
                        % (i, r.get("responsible_stage_if_real")))
    return errs


def run(ask, pack: dict, ledger: dict, worth: dict, arch: dict,
        out_dir=None, packet_text: str = "") -> dict | None:
    """The shadow artifact, or None. Never raises, never blocks, never returns a verdict.

    `ask` is a callable taking (system, user) and returning a parsed object -- injected
    so the caller owns the transport and a test can supply its own without a network.
    """
    if not enabled():
        return None
    t0 = time.time()
    art = {"schema_version": SCHEMA_VERSION, "authority": "ZERO",
           "article_not_written_yet": True}
    try:
        obj = ask(SYSTEM, build_user(pack, ledger, worth, arch, packet_text))
        errs = validate(obj, ledger)
        if errs:
            art.update({"status": "INVALID", "validation_errors": errs[:10]})
        else:
            art.update(obj)
            art["status"] = "OK"
    except Exception as e:                                        # noqa: BLE001
        # Deliberately bare, like run_semantic_claim_shadow. A shadow that can end a
        # publication day is not a shadow.
        art.update({"status": "FAILED",
                    "error": "%s: %s" % (type(e).__name__, str(e)[:200])})
    art["wall_seconds"] = round(time.time() - t0, 1)
    try:
        if out_dir is not None:
            import pathlib
            p = pathlib.Path(out_dir)
            p.mkdir(parents=True, exist_ok=True)
            (p / "PREWRITE_STORY_SHADOW.json").write_text(
                json.dumps(art, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8")
    except Exception:                                             # noqa: BLE001
        pass
    return art
