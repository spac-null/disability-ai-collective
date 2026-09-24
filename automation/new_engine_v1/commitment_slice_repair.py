"""commitment_slice_repair.py -- repair every plan surface that AFFORDS one unsupported
commitment, and leave the rest of the plan byte for byte alone.

ZERO AUTHORITY. Not wired into composition, not imported by any production module, flag off.
Reads a frozen architecture, a frozen ledger and a frozen Claim Support Shadow artifact, asks
one bounded question, and returns a repaired architecture with a proof. Every exit that is not
a proven repair is a refusal.

WHY THIS EXISTS, AND WHY IT IS NOT THE PREVIOUS MODULE.

definition_repair_compiler did exactly what it promised on the bandgap case: it removed
"set by the bandgap energy" from the gloss, kept "the long-wavelength edge of what the
detector material will register" byte for byte, changed 10.6% of the string, passed the
detector re-check and passed validate_definition_support. Then the Writer put the bridge back:

    "Varying the fraction of cadmium engineers a specific bandgap energy, WHICH SETS THE
     CUTOFF WAVELENGTH, the long-wavelength edge of what the material will register."

The controls were exact -- baseline, free rewrite and constrained repair all had BYTE-IDENTICAL
beats and use_facts, so the gloss was the only variable -- and the result was:

    gloss had explanation + bridge  ->  article had both
    gloss had neither (circular)    ->  article had neither
    gloss had explanation, no bridge->  article had BOTH

The definition was never the only place the claim could come from. Beat B3 says "The fraction
of cadmium in the mixture can be varied to engineer a specific bandgap energy; for Roman, with
a desired cutoff wavelength of approximately 2.5 microns, it was tuned to 0.445". That asserts
no bridge and is faithful to F86 and F87 -- but it puts the two concepts either side of a
semicolon, carries both facts in facts_allowed, and is the beat that must "explain plainly,
once, here: cutoff wavelength". The Writer closed the gap.

So the repair unit is wrong, not the repair mechanism. The unit is not a span inside one
field. It is a COMMITMENT, and a commitment is licensed by the plan as a whole.

WHAT IS KEPT FROM THE MODULE THAT WORKED, unchanged in spirit and mostly in code:
  * the detector is not modified and not re-run to find targets;
  * commitments are anchored exactly or the repair refuses;
  * protected text is COPIED OUT OF THE ORIGINAL, never regenerated;
  * one model call, no loop, no retry;
  * every failure closes;
  * zero authority.

WHAT IS NEW:
  * the slice: the set of plan surfaces that can AFFORD this commitment, found mechanically;
  * the affordance closure check, which is the invariant the last experiment was missing --
    after repair, no surface may still put both ends of the commitment within the Writer's
    reach at once. Run backwards over the three frozen branches, this check flags the beat in
    ALL of them, including the constrained-repair branch whose article failed. It would have
    predicted that failure before the replay was paid for.

AFFORDANCE IS AN OVER-APPROXIMATION, DELIBERATELY. The free-rewrite branch afforded the bridge
too and its Writer did not take it -- because that branch had destroyed the explanatory
apposition the bridge attaches to. So affordance present does not mean the claim will be
written; affordance closed means the route is gone. A conservative check is the right shape
here: it can cost an unnecessary repair, it cannot miss the carrier.
"""
from __future__ import annotations

import copy
import json
import os
import re
import time

from . import provenance as PV
from . import definition_repair_compiler as DRC

SCHEMA_VERSION = "commitment-slice-repair-v1"
ENV_FLAG = "CRIPMINDS_COMMITMENT_SLICE_REPAIR"

PROTECTED = "PROTECTED"
AFFORDING = "AFFORDING"

DROP = "DROP"
REPLACE = "REPLACE"
KEEP = "KEEP"

TOOL_OWNED = ("schema_version", "authority", "status", "validation_errors", "preservation",
              "affordance", "execution", "physical_model_calls", "tool_fields_ignored",
              "error", "slice", "repaired_architecture", "original_architecture")

_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def enabled(env=None) -> bool:
    v = (env if env is not None else os.environ).get(ENV_FLAG, "").strip().lower()
    return v in ("1", "on", "true", "yes")


# ------------------------------------------------------------------------- endpoints --

def _content(s: str) -> set:
    return {w.lower() for w in _WORD.findall(s or "")
            if w.lower() not in DRC.FUNCTION_WORDS and len(w) > 2}


def _ledger_df(ledger: dict, word: str) -> int:
    n = 0
    for f in (ledger or {}).values():
        if word in str((f or {}).get("proposition", "")).lower():
            n += 1
    return n


def endpoints(term: str, span: str, arch: dict, ledger: dict) -> tuple:
    """The two ends of the unsupported relation, as words the plan can be searched for.

    E1 is the term being defined. E2 is what the flagged span brings to it.

    RARITY IS HOW THE ANCHOR IS CHOSEN, NOT WHAT AFFORDANCE MEANS. Un-filtered, "set by the
    bandgap energy" yields {bandgap, energy}, and "energy" matches F09 -- dark energy -- in a
    beat with nothing to do with detector physics. bandgap has df=1 in that 117-fact ledger and
    energy df=4, so taking the rarest tier gives {bandgap} and the false positive disappears.
    That is a search heuristic for locating the concept in the plan text. It is NOT the truth
    condition: a future unsupported relation may join two common concepts, and then this
    selection degrades to keeping several anchors and repairing more conservatively -- which is
    the safe direction -- rather than to being wrong about what affordance is. Affordance is
    defined in affording_surfaces(), in terms of reach and duty, and never in terms of rarity.
    """
    e1 = _content(term)
    ids = ((arch or {}).get("definition_evidence") or {}).get(term)
    if isinstance(ids, str):
        ids = [ids]
    ev = " ".join(str(((ledger or {}).get(str(i)) or {}).get("proposition", ""))
                  for i in (ids or [])).lower()
    cand = {w for w in _content(span) if w in ev} - e1
    if not cand:
        return e1, set()
    dfs = {w: _ledger_df(ledger, w) for w in cand}
    lo = min(dfs.values())
    return e1, {w for w, d in dfs.items() if d == lo}


def anchor_report(term: str, span: str, arch: dict, ledger: dict) -> dict:
    """What was considered and what was selected -- so the heuristic is inspectable."""
    e1 = _content(term)
    ids = ((arch or {}).get("definition_evidence") or {}).get(term)
    if isinstance(ids, str):
        ids = [ids]
    ev = " ".join(str(((ledger or {}).get(str(i)) or {}).get("proposition", ""))
                  for i in (ids or [])).lower()
    cand = {w for w in _content(span) if w in ev} - e1
    return {"candidates": {w: _ledger_df(ledger, w) for w in sorted(cand)},
            "selected_by": "rarest document frequency in the ledger (a search heuristic for "
                           "locating the concept, not the definition of affordance)"}


# -------------------------------------------------------------------------- surfaces --

def beat_visible_text(beat: dict, ledger: dict) -> str:
    """Everything about this beat the Writer can see. The fact PROPOSITIONS belong here: the
    Writer Packet prints them under the beat, so a fact left in facts_allowed is on the page
    whether or not the beat's own prose mentions it."""
    parts = [beat.get("happens", ""), beat.get("concrete_carrier", ""),
             beat.get("concept_introduced", "")]
    for fid in (beat.get("facts_allowed") or []):
        parts.append(str(((ledger or {}).get(str(fid)) or {}).get("proposition", "")))
    return " ".join(parts)


def affording_surfaces(arch: dict, ledger: dict, term: str, e1: set, e2: set,
                       full_only: bool = False) -> list:
    """Surfaces that can reconstruct the commitment, classified by HOW dangerous they are.

    The invariant this serves is not "the two concepts never appear in the same field". That
    condition can only be met by deleting one of them, which prevents regeneration by removing
    half the article rather than by repairing the plan.

    It is: NO SINGLE WRITER INSTRUCTION CONTEXT MAY COMBINE THE INGREDIENTS WITH THE RHETORICAL
    DUTY THAT MAKES THE UNSUPPORTED CLAIM THE NATURAL COMPLETION. A beat that offers both ends
    of the relation AND carries the obligation to explain the term at first use is a beat where
    a writer, reaching for a way to introduce the term, finds the link already half-built. That
    is what happened in branch C.

      FULL              both ends reachable AND the first-use duty for the term. Must be closed.
      INGREDIENTS_ONLY  both ends reachable, no duty. Reported, not required to close -- this
                        is where legitimate material about the second concept may legitimately
                        continue to live.
    """
    out = []
    if not e2:
        return out
    gloss = ((arch or {}).get("definitions") or {}).get(term) or ""
    if e2 & _content(gloss):
        # the gloss IS the first-use explanation of the term, so it always carries the duty
        out.append({"surface_id": "definition:%s" % term, "kind": "DEFINITION",
                    "where": ["gloss"], "affordance": "FULL"})
    for b in (arch or {}).get("beats") or []:
        c = _content(beat_visible_text(b, ledger))
        if (e1 & c) and (e2 & c):
            where, facts = [], []
            if e2 & _content(b.get("happens", "")):
                where.append("happens")
            for fid in (b.get("facts_allowed") or []):
                p = str(((ledger or {}).get(str(fid)) or {}).get("proposition", ""))
                if e2 & _content(p):
                    facts.append(str(fid))
            if facts:
                where.append("facts_allowed")
            duty = (b.get("concept_introduced") or "").strip().lower() == term.strip().lower()
            if duty:
                where.append("FIRST_USE_SITE")
            out.append({"surface_id": "beat:%s" % b.get("beat_id"), "kind": "BEAT",
                        "beat_id": b.get("beat_id"), "where": where, "e2_facts": facts,
                        "affordance": "FULL" if duty else "INGREDIENTS_ONLY"})
    if full_only:
        out = [a for a in out if a.get("affordance") == "FULL"]
    return out


# ------------------------------------------------------------------ clause partition --

_SPLIT = re.compile(r"(?<=[.;])\s+")


def clause_units(text: str, e2: set, prefix: str) -> list:
    """Split beat prose into clauses and mark the ones carrying E2.

    Splitting only on sentence and semicolon boundaries, never on commas: a comma inside
    "for Roman, with a desired cutoff wavelength of approximately 2.5 microns, it was tuned to
    0.445" does not bound a removable clause, and cutting there would leave debris. The units
    concatenate back to the input exactly -- asserted by the caller.
    """
    units, pos, n = [], 0, 0
    for piece in _SPLIT.split(text or ""):
        if not piece:
            continue
        i = (text or "").find(piece, pos)
        if i < 0:
            return []
        if i > pos:                                   # the whitespace between clauses
            units.append({"unit_id": "%sW%d" % (prefix, n), "role": PROTECTED,
                          "start": pos, "end": i, "text": text[pos:i], "separator": True})
        n += 1
        role = AFFORDING if (e2 & _content(piece)) else PROTECTED
        units.append({"unit_id": "%sC%d" % (prefix, n), "role": role,
                      "start": i, "end": i + len(piece), "text": piece})
        pos = i + len(piece)
    if pos < len(text or ""):
        units.append({"unit_id": "%sW%d" % (prefix, n + 1), "role": PROTECTED,
                      "start": pos, "end": len(text), "text": text[pos:], "separator": True})
    return units


# ----------------------------------------------------------------------- build slice --

def build_slice(arch: dict, ledger: dict, shadow: dict, term: str, unit_id: str = "") -> dict:
    """The commitment and the surfaces that afford it. Deterministic; no model involved."""
    sl = {"term": term, "refusals": [], "surfaces": []}

    claims = None
    for d in (shadow or {}).get("definitions") or []:
        if d.get("term") == term:
            claims = d.get("claims") or []
    if claims is None:
        sl["refusals"].append("the shadow reports nothing for %r" % term)
        return sl

    gloss = ((arch or {}).get("definitions") or {}).get(term)
    if gloss is None:
        sl["refusals"].append("the architecture defines no term %r" % term)
        return sl

    ir = DRC.build_ir(term, gloss, claims)
    if ir["anchoring"] != "OK":
        sl["refusals"].append("cannot anchor a safe edit over the gloss: %s" % ir["anchoring"])
        return sl
    target = DRC.select_target(ir, unit_id)
    if target is None:
        sl["refusals"].append("no single repairable unit selected (candidates=%s)"
                              % ir.get("repairable_candidates"))
        return sl

    e1, e2 = endpoints(term, target["text"], arch, ledger)
    if not e2:
        sl["refusals"].append("the flagged span shares no distinctive word with the declared "
                              "evidence, so its other end cannot be located in the plan")
        return sl

    sl.update({"commitment": {"span": target["text"], "status": target["status"],
                              "reason": target.get("reason", ""), "unit_id": target["unit_id"]},
               "endpoints": {"E1": sorted(e1), "E2": sorted(e2)},
               "definition_ir": ir, "definition_target": target["unit_id"],
               "anchor_report": anchor_report(term, target["text"], arch, ledger),
               "_arch_beats": [{"beat_id": b.get("beat_id"), "happens": b.get("happens"),
                                "facts_allowed": list(b.get("facts_allowed") or [])}
                               for b in (arch.get("beats") or [])],
               "affording": affording_surfaces(arch, ledger, term, e1, e2)})

    # definition surface -- reuse the proven partition and edit window
    win = DRC.edit_window(ir, target)
    sl["definition_window"] = win
    sl["surfaces"].append({"surface_id": "definition:%s" % term, "kind": "DEFINITION",
                           "units": ir["units"], "target_unit": target["unit_id"]})

    # beat surfaces
    for a in sl["affording"]:
        if a["kind"] != "BEAT":
            continue
        b = next((x for x in arch.get("beats") or [] if x.get("beat_id") == a["beat_id"]), None)
        if b is None:
            continue
        happens = b.get("happens") or ""
        units = clause_units(happens, e2, "%s." % a["beat_id"])
        if not units or "".join(u["text"] for u in units) != happens:
            sl["refusals"].append("cannot partition beat %s prose safely" % a["beat_id"])
            return sl
        sl["surfaces"].append({
            "surface_id": a["surface_id"], "kind": "BEAT", "beat_id": a["beat_id"],
            "units": units, "e2_facts": a.get("e2_facts") or [],
            "first_use_site": "FIRST_USE_SITE" in (a.get("where") or []),
            "facts_allowed": list(b.get("facts_allowed") or [])})
    return sl


# ------------------------------------------------------------------------- contract --

SYSTEM = (
    "A plan for an article states one thing its evidence does not establish. You are closing "
    "every route by which that statement could reach the finished article. Nothing you say "
    "changes anything else: the plan is frozen, no article exists yet, and every part of the "
    "plan you are not shown is already fixed and will be copied back around your answer "
    "exactly as it stands.\n"
    "\n"
    "THE PROBLEM IS NOT ONLY THE WORDING. A writer who is shown two facts side by side, and "
    "told to explain a term in that same breath, will join them up. Removing the sentence that "
    "states the unsupported link is not enough if the plan still sets the two ideas next to "
    "each other with both facts in hand. That has already happened once: the definition was "
    "repaired, the plan still placed both ideas in one beat, and the writer wrote the link "
    "back in. Your job is to leave the plan unable to suggest it.\n"
    "\n"
    "You are shown the parts of the plan that can still do this, broken into numbered pieces. "
    "Pieces marked KEEP are staying and you cannot change them. Pieces marked AFFORDS carry "
    "the second idea, and those are yours. For each one choose:\n"
    "\n"
    "  DROP -- remove it. Usually right: the surrounding material was complete without it.\n"
    "\n"
    "  REPLACE -- put different words in its place, using ONLY what the facts listed for that "
    "piece state. Choose it when dropping would leave the surrounding text broken. Do not "
    "introduce a number, name, place, date, mechanism, cause or comparison those facts do not "
    "state.\n"
    "\n"
    "  KEEP -- leave it exactly as it is.\n"
    "\n"
    "You are also shown facts that carry the second idea into a beat. A fact left in place is "
    "printed for the writer whether or not the prose mentions it, so leaving one there leaves "
    "the route open. For each, choose:\n"
    "\n"
    "  MOVE -- offer it in a DIFFERENT existing beat instead, named from the list given. "
    "PREFER THIS when the fact is worth keeping and some other beat is a plausible home for "
    "it: the point is to separate the two ideas, not to delete one of them.\n"
    "\n"
    "  REMOVE -- stop offering it anywhere. Honest when no other beat is a plausible home, but "
    "say so in your reason, because it means the article loses that material.\n"
    "\n"
    "  KEEP -- leave it where it is.\n"
    "\n"
    "Do not invent a new beat. If nothing in the plan is a natural home for a fact, REMOVE it "
    "and say that no location existed -- that is a real answer, not a failure.\n"
    "\n"
    "You may adjust the small connecting text around a piece you changed -- punctuation, an "
    "article, a preposition, a conjunction -- and nothing else: no nouns, verbs, adjectives or "
    "numbers.\n"
    "\n"
    "Change as little as will close the route. Do not rewrite anything marked KEEP, do not "
    "improve the plan, do not reorder it, and do not say whether it should proceed."
)

SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"edits": [{"unit_id": "the id exactly as shown",\n'
    '            "operation": "DROP" | "REPLACE" | "KEEP",\n'
    '            "replacement": "...",        REPLACE only\n'
    '            "left_glue": "...",          optional\n'
    '            "right_glue": "..."}],       optional\n'
    ' "facts": [{"fact_id": "F..", "operation": "MOVE" | "REMOVE" | "KEEP",\n'
    '             "to_beat": "B.."}],        MOVE only; an EXISTING beat id\n'
    ' "reason": "one clause: how the route is now closed"}\n'
    "No prose outside the JSON."
)


def build_user(sl: dict, ledger: dict) -> str:
    L = ["THE STATEMENT THE EVIDENCE DOES NOT ESTABLISH",
         "   %r" % sl["commitment"]["span"],
         "   in the definition of: %s" % sl["term"],
         "   why: %s" % sl["commitment"].get("reason", ""),
         "   the two ideas it joins: %s  <->  %s"
         % (" ".join(sl["endpoints"]["E1"]), " ".join(sl["endpoints"]["E2"])),
         ""]
    for s in sl["surfaces"]:
        if s["kind"] == "DEFINITION":
            L.append("SURFACE %s -- the definition, in parts:" % s["surface_id"])
            for u in s["units"]:
                if u["role"] == DRC.GLUE:
                    L.append("   (connecting text)             %r" % u["text"])
                elif u["unit_id"] == s["target_unit"]:
                    L.append("   AFFORDS [%s]  %r" % (u["unit_id"], u["text"]))
                else:
                    L.append("   KEEP    [%s]  %r" % (u["unit_id"], u["text"]))
        else:
            L.append("SURFACE %s -- a beat of the plan%s, in parts:"
                     % (s["surface_id"],
                        "; this beat is where the term must be explained at first use"
                        if s.get("first_use_site") else ""))
            for u in s["units"]:
                if u.get("separator"):
                    continue
                L.append("   %-7s [%s]  %r"
                         % ("AFFORDS" if u["role"] == AFFORDING else "KEEP",
                            u["unit_id"], u["text"]))
            if s.get("e2_facts"):
                L.append("   facts this beat offers that carry %s:"
                         % " ".join(sl["endpoints"]["E2"]))
                for fid in s["e2_facts"]:
                    L.append("      %s  %s"
                             % (fid, str(((ledger or {}).get(fid) or {}).get("proposition", ""))))
        L.append("")
    L.append("THE EVIDENCE AVAILABLE TO THE PIECES YOU MAY CHANGE:")
    seen = set()
    for s in sl["surfaces"]:
        for fid in (s.get("facts_allowed") or []):
            if fid in seen:
                continue
            seen.add(fid)
            L.append("   %s  %s"
                     % (fid, str(((ledger or {}).get(str(fid)) or {}).get("proposition", ""))))
    others = [b.get("beat_id") for b in ((sl.get("_arch_beats")) or [])
              if b.get("beat_id") not in {x.get("beat_id") for x in sl["surfaces"]
                                          if x["kind"] == "BEAT"}]
    if others:
        L += ["", "OTHER BEATS OF THE PLAN, if a fact belongs in one of them instead:"]
        for b in (sl.get("_arch_beats") or []):
            if b.get("beat_id") in others:
                L.append("   %-4s %s" % (b.get("beat_id"), (b.get("happens") or "")[:150]))
    L += ["", SCHEMA]
    return "\n".join(L)


# ------------------------------------------------------------------------ validation --

def _licensed(sl: dict, ledger: dict, surface: dict) -> str:
    parts = []
    for fid in (surface.get("facts_allowed") or []):
        f = (ledger or {}).get(str(fid)) or {}
        parts += [str(f.get("proposition", "")), str(f.get("support_span", ""))]
    parts += [u["text"] for u in surface.get("units", []) if u["role"] != AFFORDING]
    return re.sub(r"\s+", " ", " ".join(parts)).strip().lower()


def validate(reply, sl: dict, ledger: dict) -> list:
    errs = []
    if not isinstance(reply, dict):
        return ["reply is not an object"]
    edits = reply.get("edits")
    if not isinstance(edits, list) or not edits:
        return ["edits is empty or not a list"]

    by_id, surface_of = {}, {}
    for s in sl["surfaces"]:
        for u in s["units"]:
            by_id[u["unit_id"]] = u
            surface_of[u["unit_id"]] = s
    afford_ids = {u["unit_id"] for s in sl["surfaces"] for u in s["units"]
                  if u["role"] == AFFORDING
                  or (s["kind"] == "DEFINITION" and u["unit_id"] == s["target_unit"])}

    seen = set()
    for e in edits:
        if not isinstance(e, dict):
            errs.append("an edit is not an object")
            continue
        uid = e.get("unit_id")
        if uid not in by_id:
            errs.append("edit names %r, which is not a piece of this slice" % uid)
            continue
        if uid not in afford_ids:
            errs.append("edit touches %r, which is marked KEEP and may not be changed" % uid)
            continue
        if uid in seen:
            errs.append("%r is edited twice" % uid)
        seen.add(uid)
        op = e.get("operation")
        if op not in (DROP, REPLACE, KEEP):
            errs.append("%s: operation %r is not DROP, REPLACE or KEEP" % (uid, op))
            continue
        for side in ("left_glue", "right_glue"):
            if e.get(side) is not None:
                errs += ["%s %s: %s" % (uid, side, x) for x in DRC.check_glue(e.get(side) or "")]
        if op == REPLACE:
            rep = str(e.get("replacement") or "")
            if not rep.strip():
                errs.append("%s: REPLACE with no replacement text" % uid)
                continue
            orig = by_id[uid]["text"]
            cap = len(orig) + DRC.REPLACEMENT_SLACK_CHARS
            if len(rep) > cap:
                errs.append("%s: replacement is %d chars, over the %d allowed"
                            % (uid, len(rep), cap))
            corpus = _licensed(sl, ledger, surface_of[uid])
            bad = DRC._unlicensed_words(rep, corpus)
            if bad:
                errs.append("%s: replacement introduces word(s) the facts for this piece do "
                            "not license: %s" % (uid, ", ".join(repr(b) for b in bad[:6])))
            for num in re.findall(r"\d[\d.,]*", rep):
                if num.rstrip(".,") not in corpus:
                    errs.append("%s: replacement introduces the number %r" % (uid, num))
        elif op == DROP and str(e.get("replacement") or "").strip():
            errs.append("%s: DROP carrying replacement text" % uid)

    known = {f for s in sl["surfaces"] for f in (s.get("e2_facts") or [])}
    for f in (reply.get("facts") or []):
        if not isinstance(f, dict):
            errs.append("a facts entry is not an object")
            continue
        if str(f.get("fact_id")) not in known:
            errs.append("facts names %r, which this slice does not offer" % f.get("fact_id"))
        op = f.get("operation")
        if op not in ("REMOVE", "KEEP", "MOVE"):
            errs.append("facts %s: operation %r is not MOVE, REMOVE or KEEP"
                        % (f.get("fact_id"), op))
        if op == "MOVE":
            dest = str(f.get("to_beat") or "")
            if dest not in {str(b.get("beat_id")) for b in (sl.get("_arch_beats") or [])}:
                errs.append("facts %s: MOVE names beat %r, which does not exist in this plan "
                            "-- a new beat may not be invented" % (f.get("fact_id"), dest))
            if dest in {s2["beat_id"] for s2 in sl["surfaces"] if s2["kind"] == "BEAT"}:
                errs.append("facts %s: MOVE targets %r, which is itself a surface being "
                            "repaired" % (f.get("fact_id"), dest))
    return errs


# -------------------------------------------------------------------------- assembly --

def _tidy_prose(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+([,;:.!?])", r"\1", s)
    s = re.sub(r"([.;])\s*([.;])", r"\1", s)
    s = s.strip()
    # a dropped opening clause can leave a sentence starting lower-case; purely orthographic
    s = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), s)
    return s


def compile_repair(arch: dict, sl: dict, reply: dict) -> dict:
    """Assemble a whole architecture. Everything not in the slice is deep-copied untouched;
    inside the slice, KEEP text is copied out of the original strings."""
    out = copy.deepcopy(arch)
    edits = {e["unit_id"]: e for e in (reply.get("edits") or []) if isinstance(e, dict)}

    for s in sl["surfaces"]:
        if s["kind"] == "DEFINITION":
            e = edits.get(s["target_unit"])
            if not e or e.get("operation") == KEEP:
                continue
            win = sl["definition_window"]
            mid = "" if e.get("operation") == DROP else str(e.get("replacement") or "")
            lg = e.get("left_glue"); rg = e.get("right_glue")
            lg = win["left_glue"] if lg is None else str(lg)
            rg = win["right_glue"] if rg is None else str(rg)
            out["definitions"][sl["term"]] = DRC._tidy(win["prefix"] + lg + mid + rg + win["suffix"])
        else:
            beat = next(b for b in out["beats"] if b.get("beat_id") == s["beat_id"])
            pieces = []
            for u in s["units"]:
                e = edits.get(u["unit_id"])
                if e is None or e.get("operation") == KEEP:
                    pieces.append(u["text"])
                    continue
                if e.get("left_glue") is not None:
                    pieces.append(str(e["left_glue"]))
                if e.get("operation") == REPLACE:
                    pieces.append(str(e.get("replacement") or ""))
                if e.get("right_glue") is not None:
                    pieces.append(str(e["right_glue"]))
            beat["happens"] = _tidy_prose("".join(pieces))
            gone = {str(f["fact_id"]) for f in (reply.get("facts") or [])
                    if isinstance(f, dict) and f.get("operation") in ("REMOVE", "MOVE")}
            if gone:
                beat["facts_allowed"] = [f for f in (beat.get("facts_allowed") or [])
                                         if str(f) not in gone]
    for f in (reply.get("facts") or []):
        if not isinstance(f, dict) or f.get("operation") != "MOVE":
            continue
        dest = next((b for b in out["beats"] if str(b.get("beat_id")) == str(f.get("to_beat"))), None)
        if dest is not None and str(f["fact_id"]) not in (dest.get("facts_allowed") or []):
            dest["facts_allowed"] = list(dest.get("facts_allowed") or []) + [str(f["fact_id"])]
    return out


# ----------------------------------------------------------------------------- proof --

def prove(arch: dict, repaired: dict, sl: dict, ledger: dict, term: str,
          reply: dict | None = None) -> dict:
    """Preservation, scope, affordance closure and fact disposition -- all recomputed against
    the OUTPUT, so a bug in compile_repair() is caught here rather than shipped."""
    touched = {s["surface_id"] for s in sl["surfaces"]}
    touched_beats = {s["beat_id"] for s in sl["surfaces"] if s["kind"] == "BEAT"}
    moved_to = {str(f.get("to_beat")) for f in ((reply or {}).get("facts") or [])
                if isinstance(f, dict) and f.get("operation") == "MOVE"}

    # 1. everything outside the slice -- and outside any beat a fact was moved into -- is
    #    byte-identical. A MOVE destination is in scope only for its facts_allowed list.
    a2, r2 = copy.deepcopy(arch), copy.deepcopy(repaired)
    a2["definitions"] = {k: v for k, v in (a2.get("definitions") or {}).items() if k != term}
    r2["definitions"] = {k: v for k, v in (r2.get("definitions") or {}).items() if k != term}
    for d in (a2, r2):
        nb = []
        for b in (d.get("beats") or []):
            if b.get("beat_id") in touched_beats:
                nb.append({k: v for k, v in b.items() if k not in ("happens", "facts_allowed")})
            elif str(b.get("beat_id")) in moved_to:
                nb.append({k: v for k, v in b.items() if k != "facts_allowed"})
            else:
                nb.append(b)
        d["beats"] = nb
    outside_identical = json.dumps(a2, sort_keys=True) == json.dumps(r2, sort_keys=True)

    # 2. KEEP units survive verbatim, in order, in their own surface.
    #
    #    ONE orthographic exception, recorded rather than waved through: a clause that becomes
    #    sentence-initial because the clause before it was dropped gets its first letter
    #    capitalised by _tidy_prose. That is a change to protected text, however small, so it
    #    is matched explicitly and listed in orthographic_adjustments -- never folded silently
    #    into "survived". Nothing else about a protected unit may differ by one character.
    lost, kept, ortho = [], [], []
    for s in sl["surfaces"]:
        if s["kind"] == "DEFINITION":
            text = (repaired.get("definitions") or {}).get(term) or ""
            units = [u for u in s["units"]
                     if u["role"] == DRC.PROTECTED and u["unit_id"] != s["target_unit"]]
        else:
            beat = next((b for b in repaired.get("beats") or []
                         if b.get("beat_id") == s["beat_id"]), {})
            text = beat.get("happens") or ""
            units = [u for u in s["units"] if u["role"] == PROTECTED and not u.get("separator")]
        cur = 0
        for u in units:
            needle = u["text"].strip()
            i = text.find(needle, cur)
            if i < 0 and needle:
                swapped = (needle[0].upper() if needle[0].islower() else needle[0].lower()) + needle[1:]
                j = text.find(swapped, cur)
                if j >= 0:
                    ortho.append({"unit_id": u["unit_id"], "change": "first letter %r -> %r"
                                  % (needle[0], swapped[0])})
                    i, needle = j, swapped
            (kept if i >= 0 else lost).append(u["unit_id"])
            if i >= 0:
                cur = i + len(needle)

    # 3. affordance closure -- FULL only. "Both concepts never co-occur" would be satisfiable
    #    only by deleting one of them; what must go is the coincidence of ingredients with the
    #    first-use duty.
    e1 = set(sl["endpoints"]["E1"]); e2 = set(sl["endpoints"]["E2"])
    after_all = affording_surfaces(repaired, ledger, term, e1, e2)
    after_full = [a for a in after_all if a.get("affordance") == "FULL"]

    # 4. what happened to the second concept's facts -- preserved, relocated, or dropped, and
    #    whether that was an explicit decision rather than a silent loss
    declared = {str(f.get("fact_id")): f for f in ((reply or {}).get("facts") or [])
                if isinstance(f, dict)}
    use_after = set(str(x) for x in (repaired.get("use_facts") or []))
    disposition = {}
    for fid in sorted({f for s in sl["surfaces"] for f in (s.get("e2_facts") or [])}):
        homes = [b.get("beat_id") for b in (repaired.get("beats") or [])
                 if str(fid) in [str(x) for x in (b.get("facts_allowed") or [])]]
        d = (declared.get(fid) or {}).get("operation")
        if homes:
            state = "OFFERED_IN_%s" % ",".join(homes)
        elif fid in use_after:
            state = "IN_use_facts_BUT_NO_BEAT_OFFERS_IT"
        else:
            state = "DROPPED_FROM_PLAN"
        disposition[fid] = {"state": state, "declared_operation": d,
                            "explicit": d in ("MOVE", "REMOVE", "KEEP")}
    facts_accounted = all(v["explicit"] for v in disposition.values()) if disposition else True
    material_lost = [f for f, v in disposition.items()
                     if v["state"] != "DROPPED_FROM_PLAN" and not v["state"].startswith("OFFERED")]

    gone = sl["commitment"]["span"] not in ((repaired.get("definitions") or {}).get(term) or "")
    first_use_kept = any((b.get("concept_introduced") or "").strip().lower() == term.strip().lower()
                         for b in (repaired.get("beats") or []))

    return {"surfaces_in_slice": sorted(touched),
            "plan_outside_slice_byte_identical": outside_identical,
            "keep_units_survived": kept, "keep_units_lost": lost,
            "all_keep_survived": not lost,
            "orthographic_adjustments": ortho,
            "flagged_span_absent_from_gloss": gone,
            "first_use_duty_still_assigned": first_use_kept,
            "affording_before": [(a["surface_id"], a.get("affordance")) for a in sl["affording"]],
            "affording_after": [(a["surface_id"], a.get("affordance")) for a in after_all],
            "affordance_closed": not after_full,
            "second_concept_facts": disposition,
            "facts_explicitly_accounted": facts_accounted,
            "facts_in_limbo": material_lost,
            # ---- the five report lines ----
            "TARGET_COMMITMENT_REMOVED": gone,
            "AFFORDANCE_REMOVED": not after_full,
            "PROTECTED_CONTENT_PRESERVED": (not lost) and outside_identical and first_use_kept,
            "UNRELATED_FACT_PRESERVED_OR_EXPLICITLY_DROPPED": facts_accounted and not material_lost,
            "WRITER_REGENERATION": "NOT_MEASURED_STATICALLY -- requires the paired replay"}


def engine_validators(repaired: dict, ledger: dict) -> list:
    """The engine's own rules, run on the assembled plan. Imported lazily so this module can be
    tested without dragging in composition."""
    from . import story as S
    ids = set((ledger or {}).keys())
    errs = []
    try:
        errs += ["validate_architecture: %s" % e
                 for e in S.validate_architecture(repaired, ids, ledger)]
    except Exception as e:                                        # noqa: BLE001
        errs.append("validate_architecture raised %s: %s" % (type(e).__name__, e))
    try:
        errs += ["validate_definition_support: %s" % e
                 for e in S.validate_definition_support(repaired, ledger)]
    except Exception as e:                                        # noqa: BLE001
        errs.append("validate_definition_support raised %s: %s" % (type(e).__name__, e))
    try:
        errs += ["validate_evidence_hierarchy: %s" % e
                 for e in S.validate_evidence_hierarchy(repaired, ids)]
    except Exception as e:                                        # noqa: BLE001
        errs.append("validate_evidence_hierarchy raised %s: %s" % (type(e).__name__, e))
    return errs


# ------------------------------------------------------------------------------- run --

def run(ask, arch: dict, ledger: dict, shadow: dict, term: str, unit_id: str = "",
        execution_id: str = "", out_dir=None) -> dict:
    t0 = time.time()
    art = {"schema_version": SCHEMA_VERSION, "authority": "ZERO", "term": term,
           "status": "REFUSED", "physical_model_calls": 0,
           "execution": {"execution_id": execution_id or "", "code": PV.code_identity(),
                         "architecture_sha256": DRC._h(arch),
                         "shadow_sha256": DRC._h(shadow),
                         "system_sha256": PV.sha256_text(SYSTEM),
                         "schema_sha256": PV.sha256_text(SCHEMA)}}
    try:
        sl = build_slice(arch, ledger, shadow, term, unit_id)
        art["slice"] = sl
        if sl.get("refusals"):
            art["error"] = "; ".join(sl["refusals"])[:300]
            return _finish(art, t0, out_dir)
        art["execution"]["slice_sha256"] = DRC._h(sl.get("affording"))

        user = build_user(sl, ledger)
        art["execution"]["user_prompt_sha256"] = PV.sha256_text(user)

        reply = ask(SYSTEM, user)
        art["physical_model_calls"] = 1

        errs = validate(reply, sl, ledger)
        if errs:
            art["validation_errors"] = errs[:10]
            art["error"] = "the proposed edits did not pass: %s" % errs[0]
            return _finish(art, t0, out_dir)

        stolen = sorted(k for k in reply if k in TOOL_OWNED)
        if stolen:
            art["tool_fields_ignored"] = stolen
        art["edit_plan"] = {"edits": reply.get("edits"), "facts": reply.get("facts"),
                            "reason": reply.get("reason")}
        art["execution"]["edit_plan_sha256"] = DRC._h(art["edit_plan"])

        repaired = compile_repair(arch, sl, reply)
        proof = prove(arch, repaired, sl, ledger, term, reply)
        art["preservation"] = proof
        verrs = engine_validators(repaired, ledger)
        art["engine_validation"] = verrs or "CLEAN"

        hard = []
        if not proof["plan_outside_slice_byte_identical"]:
            hard.append("the plan outside the slice is not byte-identical")
        if not proof["all_keep_survived"]:
            hard.append("KEEP piece(s) did not survive: %s" % proof["keep_units_lost"])
        if not proof["flagged_span_absent_from_gloss"]:
            hard.append("the flagged span is still in the gloss")
        if not proof["affordance_closed"]:
            hard.append("a beat still combines both ideas with the first-use duty: %s"
                        % [a for a, k in proof["affording_after"] if k == "FULL"])
        if not proof["first_use_duty_still_assigned"]:
            hard.append("no beat explains the term at first use any more")
        if not proof["facts_explicitly_accounted"]:
            hard.append("a fact carrying the second idea changed state without being named")
        if verrs:
            hard.append("the repaired plan fails the engine's own rules: %s" % verrs[0])
        if hard:
            art["validation_errors"] = hard
            art["error"] = "the assembled repair failed its proof: %s" % hard[0]
            art["rejected_architecture"] = repaired
            return _finish(art, t0, out_dir)

        art["repaired_architecture"] = repaired
        art["execution"]["repaired_architecture_sha256"] = DRC._h(repaired)
        art["status"] = "REPAIRED"
    except Exception as e:                                        # noqa: BLE001
        art["status"] = "FAILED"
        art["error"] = "%s: %s" % (type(e).__name__, str(e)[:200])
    return _finish(art, t0, out_dir)


def _finish(art, t0, out_dir):
    art["wall_seconds"] = round(time.time() - t0, 1)
    try:
        if out_dir is not None:
            import pathlib
            p = pathlib.Path(out_dir)
            p.mkdir(parents=True, exist_ok=True)
            (p / "COMMITMENT_SLICE_REPAIR.json").write_text(
                json.dumps(art, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    except Exception:                                             # noqa: BLE001
        pass
    return art
