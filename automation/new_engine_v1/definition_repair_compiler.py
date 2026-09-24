"""definition_repair_compiler.py -- change ONE unsupported factual commitment inside a
definition without recompiling the material around it.

ZERO AUTHORITY. Not wired into composition. Cannot reach the Writer, Grounding, Fact Check,
Reader, the package or publication, and is not imported by any production module. It reads a
frozen architecture plus a frozen Claim Support Shadow artifact, asks one bounded question,
and returns a repaired gloss with a preservation proof. If anything is off it returns a
refusal, never a degraded gloss.

WHY IT EXISTS. On 2026-09-23 the whole-architecture repair channel was pointed at one
NOT_ESTABLISHED commitment twice. Once it worked ("minutes away" -> "imminent"). Once it
destroyed the article.

    definitions['cutoff wavelength']
      "the long-wavelength edge of what the detector material will register, set by the
       bandgap energy engineered in the mercury cadmium telluride mixture -- for Roman,
       approximately 2.5 microns, with the WFI sensitive from 0.48 to 2.3 microns."

The flagged commitment was "set by the bandgap energy". The repair removed it AND removed
"the long-wavelength edge of what the detector material will register" -- which the same
shadow had already classified NON_FACTUAL_OR_NOT_CHECKABLE, i.e. explicitly NOT the defect.
The published definition became "a wavelength specified for the instrument", which tells a
reader nothing. Factually clean, editorially empty.

The repair prompt had said, in as many words, "Preserve the explanatory purpose of the
definition." It was not enough, and the reason is structural rather than a wording miss:

  * the reply schema asked for the ENTIRE architecture -- spine, beats, use_facts,
    final_lens, definitions -- so the definition was regenerated from nothing, as one field
    among thirty, by a model that had been given no representation of which of its own words
    were already load-bearing;
  * "the long-wavelength edge ..." and "set by the bandgap energy" read as one grammatical
    construction, and a model rewriting the construction rewrites both halves;
  * preservation existed only as a SENTENCE IN A PROMPT. Nothing checked it, so nothing
    enforced it.

THE INVERSION THIS MODULE MAKES. The repair model does not decide what is protected. The
partition is computed HERE, deterministically, from the detector's own per-span statuses --
which already say, for every span of the gloss, whether it is supported, explanatory, or
unsupported. The model is handed one span and one question about it. Protected text is then
COPIED OUT OF THE ORIGINAL STRING by the compiler and never passes through the model at all.

That is the difference from the literature this borrows from. RARR measures preservation
afterwards (a Levenshtein-based score) but its editor still regenerates a whole claim, and
its reference implementation has no mechanical rejection of an over-large edit. FactEditor
represents retention explicitly as Keep/Drop/Gen actions, which is the idea worth taking, but
the actions come from a learned policy with no guarantee that a supported token survives.
VENCE makes minimality a penalty term in an energy function and then needs iterative sampling
to satisfy it. Measured, learned, penalised. Here preservation is none of those: it is not
achievable for the model to violate it, because the protected text is never regenerated.

NARROW BY CONSTRUCTION, same discipline as the detector it consumes:
  * definitions only -- not beats, not the lens fields, not spine, ending or crip_turn;
  * ONE flagged commitment per call, no loops, no retries, no second opinion;
  * generated replacement text may use ONLY the evidence that definition declared, never
    the whole ledger -- widening that is the error the 114-run relation audit measured;
  * every failure is a refusal. A repair that cannot be proven is not applied.
"""
from __future__ import annotations

import json
import os
import re
import time
import unicodedata

from . import provenance as PV

SCHEMA_VERSION = "definition-repair-compiler-v1"
ENV_FLAG = "CRIPMINDS_DEFINITION_REPAIR_COMPILER"

SUPPORTED = "SUPPORTED"
NOT_ESTABLISHED = "NOT_ESTABLISHED"
CONTRADICTED = "CONTRADICTED"
NON_FACTUAL = "NON_FACTUAL_OR_NOT_CHECKABLE"

REPAIRABLE_STATUSES = (NOT_ESTABLISHED, CONTRADICTED)
PROTECTED_STATUSES = (SUPPORTED, NON_FACTUAL)

PROTECTED = "PROTECTED"
REPAIRABLE = "REPAIRABLE"
GLUE = "GLUE"

DROP = "DROP"
REPLACE = "REPLACE"
OPERATIONS = (DROP, REPLACE)

# Keys the tool owns. A model reply must not be able to restate its own authority, declare
# its own edit proven, or name the unit it was allowed to touch. Same rule and same reason as
# definition_claim_shadow.TOOL_OWNED.
TOOL_OWNED = ("schema_version", "authority", "status", "validation_errors", "preservation",
              "execution", "physical_model_calls", "tool_fields_ignored", "error",
              "repairable_unit_id", "units", "original_gloss", "repaired_gloss", "ir")

# -- the glue rule (see module docstring on why this is a closed list and not a judgement) --
#
# Glue exists to repair a JUNCTURE, not to say anything. A juncture needs punctuation, an
# article, a preposition or a coordinator; it never needs a noun, a verb, an adjective, an
# adverb or a number. Anything outside this list -- including a word that is merely harmless
# in context -- fails closed, because "harmless in context" is the judgement the whole module
# exists to avoid making. Relativisers ("which", "that", "where") are deliberately ABSENT:
# they are the cheapest way to start a clause, and a clause is where a new commitment hides.
GLUE_WORDS = frozenset("""
a an the this that these those its their his her our your
of in on at to for from with by into within through over under across about between as
and or but nor
""".split())

GLUE_PUNCT = frozenset(",;:.!?—–-()[]'\"… ")
MAX_GLUE_CHARS = 24

# A replacement may not grow the span it replaces without bound; a "replacement" three times
# the length of what it replaces is a rewrite wearing a smaller name.
REPLACEMENT_SLACK_CHARS = 24

# Function words are always licensed inside a replacement: they carry no factual commitment.
# Content words are not, and must be traceable to the declared evidence or to the gloss's own
# protected text.
FUNCTION_WORDS = GLUE_WORDS | frozenset("""
is are was were be been being am
it they them he she we you i
not no nor so than then there here when where while if unless until
what which who whom whose why how
each every both all any some few many most other another same such
can could may might must shall should will would do does did done have has had
up out off down away back again more less very just only also even still yet
""".split())


def enabled(env=None) -> bool:
    """OFF unless explicitly switched on, like every other experiment in this engine."""
    v = (env if env is not None else os.environ).get(ENV_FLAG, "").strip().lower()
    return v in ("1", "on", "true", "yes")


# --------------------------------------------------------------------------- anchoring --

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    return re.sub(r"\s+", " ", s).strip()


def anchor(gloss: str, commitment: str):
    """(start, end) of `commitment` in `gloss`, or None when it is not a safe edit offset.

    The detector is INSTRUCTED to quote the shortest span of the gloss carrying each
    commitment, but definition_claim_shadow.validate() checks only that the text is
    non-empty -- it never checks that the quote is a substring. So the guarantee does not
    exist in code and is not assumed here. Measured over every frozen artifact available on
    2026-09-24 -- 54 claims across 12 definitions from all three calibration datasets -- the
    quote was an exact and UNIQUE substring 54 times out of 54. That is a good instrument,
    not a contract, so an unanchorable or ambiguous quote refuses the repair rather than
    guessing an offset.
    """
    if not gloss or not commitment:
        return None
    n = gloss.count(commitment)
    if n == 1:
        i = gloss.find(commitment)
        return (i, i + len(commitment))
    if n > 1:
        return None                      # AMBIGUOUS -- a real span, but not one offset
    return None                          # UNANCHORED -- not a span of this gloss at all


def build_ir(term: str, gloss: str, claims: list) -> dict:
    """The repair IR: an ordered, gap-free, non-overlapping partition of the gloss.

    Every character of the gloss lands in exactly one unit -- PROTECTED, REPAIRABLE or GLUE.
    Coverage is total BY CONSTRUCTION, because glue is defined as the residue between
    anchored spans rather than as something anyone has to remember to account for. That is
    the "no silent deletion" property: there is no part of the original the compiler can lose
    track of, because there is no part of it that is not a unit.
    """
    ir = {"term": term, "gloss": gloss, "gloss_sha256": PV.sha256_text(gloss),
          "units": [], "repairable_unit_id": None, "anchoring": "OK", "refusals": []}

    spans = []
    for c in (claims or []):
        com = str((c or {}).get("commitment") or "")
        st = (c or {}).get("status")
        a = anchor(gloss, com)
        if a is None:
            ir["anchoring"] = "UNANCHORED"
            ir["refusals"].append("commitment %r is not a unique substring of the gloss" % com[:80])
            continue
        spans.append((a[0], a[1], st, com, (c or {}).get("reason", "")))

    if ir["anchoring"] != "OK":
        return ir

    spans.sort()
    for i in range(1, len(spans)):
        if spans[i][0] < spans[i - 1][1]:
            ir["anchoring"] = "OVERLAP"
            ir["refusals"].append(
                "commitments overlap in the gloss: %r and %r" % (spans[i - 1][3][:60], spans[i][3][:60]))
            return ir

    units = []
    cursor = 0
    ci = 0
    for s, e, st, com, reason in spans:
        if s > cursor:
            units.append({"unit_id": "G%d" % (len(units) + 1), "role": GLUE, "status": None,
                          "start": cursor, "end": s, "text": gloss[cursor:s]})
        ci += 1
        role = REPAIRABLE if st in REPAIRABLE_STATUSES else PROTECTED
        units.append({"unit_id": "U%d" % ci, "role": role, "status": st,
                      "start": s, "end": e, "text": gloss[s:e], "reason": reason})
        cursor = e
    if cursor < len(gloss):
        units.append({"unit_id": "G%d" % (len(units) + 1), "role": GLUE, "status": None,
                      "start": cursor, "end": len(gloss), "text": gloss[cursor:]})

    # total-coverage invariant, asserted rather than assumed
    if "".join(u["text"] for u in units) != gloss:
        ir["anchoring"] = "PARTITION_BROKEN"
        ir["refusals"].append("units do not reassemble to the original gloss")
        return ir

    ir["units"] = units
    reps = [u for u in units if u["role"] == REPAIRABLE]
    if not reps:
        ir["anchoring"] = "NO_REPAIRABLE_UNIT"
    elif len(reps) > 1:
        ir["repairable_candidates"] = [u["unit_id"] for u in reps]
    ir["claim_coverage"] = round(
        sum(u["end"] - u["start"] for u in units if u["role"] != GLUE) / float(len(gloss) or 1), 4)
    return ir


def select_target(ir: dict, unit_id: str = "") -> dict | None:
    """The ONE repairable unit this call is about. One warning at a time, by contract."""
    reps = [u for u in ir.get("units", []) if u["role"] == REPAIRABLE]
    if not reps:
        return None
    if unit_id:
        for u in reps:
            if u["unit_id"] == unit_id:
                return u
        return None
    return reps[0] if len(reps) == 1 else None


def edit_window(ir: dict, target: dict) -> dict:
    """The only region of the gloss this repair may touch.

    [a, b) spans the glue immediately before the target, the target, and the glue immediately
    after it. gloss[:a] ends exactly where the preceding PROTECTED unit ends and gloss[b:]
    begins exactly where the following one begins, so the compiler can copy both sides
    verbatim out of the original string.
    """
    units = ir["units"]
    i = units.index(target)
    a, b = target["start"], target["end"]
    left_glue = right_glue = ""
    if i > 0 and units[i - 1]["role"] == GLUE:
        left_glue = units[i - 1]["text"]
        a = units[i - 1]["start"]
    if i + 1 < len(units) and units[i + 1]["role"] == GLUE:
        right_glue = units[i + 1]["text"]
        b = units[i + 1]["end"]
    return {"start": a, "end": b, "left_glue": left_glue, "right_glue": right_glue,
            "prefix": ir["gloss"][:a], "suffix": ir["gloss"][b:]}


# ------------------------------------------------------------------ the repair contract --

SYSTEM = (
    "You are making ONE small correction inside a short definition. Nothing you say changes "
    "anything else: the plan is frozen, no article exists yet, and every other word of the "
    "definition is already fixed and will be copied back around your answer exactly as it "
    "stands. You are not rewriting the definition. You cannot rewrite the definition.\n"
    "\n"
    "You are shown the definition broken into numbered parts. Parts marked KEEP have already "
    "been checked and are staying, whether they are supported facts or ordinary explanation "
    "of what the term means. You are not being asked about them and you cannot change them.\n"
    "\n"
    "Exactly ONE part is marked REPAIR. It states something the evidence for this definition "
    "does not establish. Your whole task is that one part.\n"
    "\n"
    "Choose ONE operation:\n"
    "\n"
    "  DROP -- remove the REPAIR part. Choose this whenever the definition still reads "
    "correctly without it. It is the safest repair and usually the right one: an unsupported "
    "clause is most often an addition to a sentence that was complete before it.\n"
    "\n"
    "  REPLACE -- put different words in its place. Choose this only when DROP would leave "
    "the sentence broken -- most often because a KEEP part on either side needs the words to "
    "hang together. Your replacement may say ONLY what the evidence below states. It may not "
    "introduce a number, a name, a place, a date, a mechanism, a cause, or a comparison that "
    "is not already in that evidence. If the evidence supports a weaker word than the one "
    "being removed, the weaker word is the repair.\n"
    "\n"
    "You may also adjust the small connecting text on either side of the REPAIR part -- "
    "punctuation, an article, a preposition, a conjunction -- so the sentence joins up. That "
    "connecting text may contain nothing else: no nouns, no verbs, no adjectives, no "
    "numbers. If joining the sentence seems to need more than that, the repair belongs in "
    "REPLACE instead.\n"
    "\n"
    "Do not restate the KEEP parts. Do not improve them. Do not reorder them. Do not comment "
    "on the definition as a whole, and do not say whether anything should proceed."
)

SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"operation": "DROP" | "REPLACE",\n'
    ' "replacement": "the words that take its place",   REPLACE only; omit for DROP\n'
    ' "left_glue": "the connecting text before it",     echo it unchanged if it is fine\n'
    ' "right_glue": "the connecting text after it",     echo it unchanged if it is fine\n'
    ' "reason": "one clause"}\n'
    "No prose outside the JSON."
)


def build_user(ir: dict, target: dict, win: dict, evidence: list) -> str:
    L = ["TERM: %s" % ir["term"], "",
         "THE DEFINITION, IN PARTS:"]
    for u in ir["units"]:
        if u["role"] == GLUE:
            L.append("   (connecting text)          %r" % u["text"])
        elif u["unit_id"] == target["unit_id"]:
            L.append("   REPAIR  [%s]  %r" % (u["unit_id"], u["text"]))
            L.append("           ^ not established by the evidence below: %s" % (u.get("reason") or ""))
        else:
            L.append("   KEEP    [%s]  %r" % (u["unit_id"], u["text"]))
    L += ["",
          "THE PART YOU ARE REPAIRING: %r" % target["text"],
          "THE CONNECTING TEXT BEFORE IT: %r" % win["left_glue"],
          "THE CONNECTING TEXT AFTER IT:  %r" % win["right_glue"],
          "",
          "THE EVIDENCE THIS DEFINITION DECLARED -- the only evidence available to you:"]
    if not evidence:
        L.append("   none declared")
    for fid, prop, span in evidence:
        L.append("   %s  %s" % (fid, prop))
        if span and span != prop:
            L.append("       verbatim from source: %s" % span)
    L += ["", SCHEMA]
    return "\n".join(L)


def evidence_rows(arch: dict, ledger: dict, term: str) -> list:
    ids = ((arch or {}).get("definition_evidence") or {}).get(term)
    if isinstance(ids, str):
        ids = [ids]
    rows = []
    for fid in [str(i) for i in (ids or [])]:
        f = (ledger or {}).get(fid) or {}
        rows.append((fid, str(f.get("proposition", "") or "").strip(),
                     str(f.get("support_span", "") or "").strip()))
    return rows


# ------------------------------------------------------------------------- the checking --

_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def _licensed_corpus(ir: dict, evidence: list) -> str:
    """What generated words may be drawn from: the declared evidence, plus the gloss's own
    protected text. Nothing else -- not the ledger, not the beats, not the world."""
    parts = [p for _, p, s in evidence for p in (p, s)]
    parts += [u["text"] for u in ir["units"] if u["role"] == PROTECTED]
    return _norm(" ".join(parts)).lower()


def _unlicensed_words(text: str, corpus: str) -> list:
    out = []
    for w in _WORD.findall(text or ""):
        lw = w.lower()
        if lw in FUNCTION_WORDS or lw in corpus:
            continue
        stem = lw[:max(4, len(lw) - 3)]
        if len(lw) > 3 and stem in corpus:
            continue
        out.append(w)
    return out


def check_glue(s: str) -> list:
    errs = []
    if s is None:
        return ["glue is null"]
    if len(s) > MAX_GLUE_CHARS:
        errs.append("connecting text is %d chars, over the %d allowed" % (len(s), MAX_GLUE_CHARS))
    if re.search(r"\d", s):
        errs.append("connecting text contains a digit: %r" % s)
    for w in _WORD.findall(s):
        if w.lower() not in GLUE_WORDS:
            errs.append("connecting text uses %r, which is not punctuation, an article, a "
                        "preposition or a conjunction" % w)
    for ch in s:
        if not ch.isalnum() and ch not in GLUE_PUNCT and not ch.isspace():
            errs.append("connecting text contains %r" % ch)
    return errs


def validate(reply, ir: dict, target: dict, evidence: list) -> list:
    """Everything that must hold about the MODEL'S ANSWER before anything is assembled."""
    errs = []
    if not isinstance(reply, dict):
        return ["reply is not an object"]

    op = reply.get("operation")
    if op not in OPERATIONS:
        errs.append("operation %r is not one of %s" % (op, ", ".join(OPERATIONS)))

    for side in ("left_glue", "right_glue"):
        errs += ["%s: %s" % (side, e) for e in check_glue(reply.get(side) or "")]

    rep = reply.get("replacement")
    if op == DROP:
        if str(rep or "").strip():
            errs.append("operation is DROP but a replacement was supplied: %r" % str(rep)[:80])
    elif op == REPLACE:
        rep = str(rep or "")
        if not rep.strip():
            errs.append("operation is REPLACE but no replacement text was supplied")
        else:
            cap = len(target["text"]) + REPLACEMENT_SLACK_CHARS
            if len(rep) > cap:
                errs.append("replacement is %d chars, over the %d allowed for a %d-char span"
                            % (len(rep), cap, len(target["text"])))
            corpus = _licensed_corpus(ir, evidence)
            bad = _unlicensed_words(rep, corpus)
            if bad:
                errs.append("replacement introduces word(s) the declared evidence does not "
                            "license: %s" % ", ".join(repr(b) for b in bad[:6]))
            for num in re.findall(r"\d[\d.,]*", rep):
                if num.rstrip(".,") not in corpus:
                    errs.append("replacement introduces the number %r, which the declared "
                                "evidence does not state" % num)
            if target["text"].lower().strip() in rep.lower():
                errs.append("replacement still contains the unsupported span verbatim")
    return errs


def _tidy(s: str) -> str:
    """Whitespace and spacing only. Deterministic, content-free, and applied to the ASSEMBLED
    string so that a DROP does not leave a doubled space or a space before a comma."""
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+([,;:.!?])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    return s.strip()


def compile_repair(ir: dict, target: dict, win: dict, reply: dict) -> str:
    """Assemble. The protected text is COPIED OUT OF THE ORIGINAL GLOSS, never regenerated.

    This single line is the whole preservation guarantee. prefix and suffix are slices of
    ir["gloss"]; the model's answer only ever reaches the middle.
    """
    mid = "" if reply.get("operation") == DROP else str(reply.get("replacement") or "")
    return _tidy(win["prefix"] + str(reply.get("left_glue") or "") + mid
                 + str(reply.get("right_glue") or "") + win["suffix"])


def prove_preservation(ir: dict, target: dict, repaired: str) -> dict:
    """The mechanical proof, recomputed against the OUTPUT STRING rather than against the
    compiler's intentions -- so a bug in compile_repair() is caught here rather than shipped.
    """
    protected = [u for u in ir["units"] if u["role"] == PROTECTED]
    survived, lost, cursor, ordered = [], [], 0, True
    for u in protected:
        i = repaired.find(u["text"], cursor)
        if i < 0:
            if u["text"] in repaired:
                ordered = False
                survived.append(u["unit_id"])
            else:
                lost.append(u["unit_id"])
        else:
            survived.append(u["unit_id"])
            cursor = i + len(u["text"])
    explanatory = [u["unit_id"] for u in protected if u["status"] == NON_FACTUAL]
    supported = [u["unit_id"] for u in protected if u["status"] == SUPPORTED]
    changed = len(ir["gloss"]) - len(_common_prefix(ir["gloss"], repaired)) \
        - len(_common_suffix(ir["gloss"], repaired))
    return {
        "protected_units": [u["unit_id"] for u in protected],
        "protected_survived_verbatim": survived,
        "protected_lost": lost,
        "protected_in_original_order": ordered,
        "explanatory_units": explanatory,
        "explanatory_survived": [u for u in explanatory if u in survived and not lost],
        "supported_units": supported,
        "supported_survived": [u for u in supported if u in survived],
        "repairable_unit": target["unit_id"],
        "repairable_text_absent": target["text"] not in repaired,
        "original_chars": len(ir["gloss"]),
        "repaired_chars": len(repaired),
        "chars_changed_outside_common_affixes": max(0, changed),
        "all_protected_survived": (not lost) and ordered,
    }


def _common_prefix(a: str, b: str) -> str:
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return a[:n]


def _common_suffix(a: str, b: str) -> str:
    n = 0
    while n < min(len(a), len(b)) - 0 and a[len(a) - 1 - n] == b[len(b) - 1 - n]:
        n += 1
    return a[len(a) - n:] if n else ""


# ------------------------------------------------------------------------------- the run --

def plan_targets(arch: dict, shadow: dict) -> list:
    """Every (term, unit) this module could be pointed at, and why it would refuse.

    A definition whose every commitment is SUPPORTED or NON_FACTUAL produces NOTHING here --
    not a call, not a refusal, not an entry. A repair system that touches a clean definition
    is a repair system that can damage one.
    """
    defs = (arch or {}).get("definitions") or {}
    out = []
    for d in (shadow or {}).get("definitions") or []:
        term = d.get("term")
        gloss = defs.get(term)
        if gloss is None:
            continue
        ir = build_ir(term, gloss, d.get("claims") or [])
        reps = [u for u in ir.get("units", []) if u["role"] == REPAIRABLE]
        if ir["anchoring"] == "NO_REPAIRABLE_UNIT" or (ir["anchoring"] == "OK" and not reps):
            continue
        out.append({"term": term, "ir": ir,
                    "repairable": [u["unit_id"] for u in reps],
                    "refusal": None if ir["anchoring"] == "OK" else ir["anchoring"]})
    return out


def run(ask, arch: dict, ledger: dict, shadow: dict, term: str, unit_id: str = "",
        execution_id: str = "", out_dir=None, call_meta: dict | None = None) -> dict:
    """ONE repair, ONE model call, no loop. Returns an artifact; never raises.

    Every exit that is not a proven repair is a REFUSAL with a reason. There is deliberately
    no path that returns a gloss the proof did not cover.
    """
    t0 = time.time()
    art = {"schema_version": SCHEMA_VERSION, "authority": "ZERO",
           "term": term, "status": "REFUSED", "physical_model_calls": 0,
           "execution": {"execution_id": execution_id or "",
                         "code": PV.code_identity(),
                         "architecture_sha256": _h(arch),
                         "shadow_sha256": _h(shadow),
                         "system_sha256": PV.sha256_text(SYSTEM),
                         "schema_sha256": PV.sha256_text(SCHEMA)}}
    try:
        gloss = ((arch or {}).get("definitions") or {}).get(term)
        if gloss is None:
            art["error"] = "architecture defines no term %r" % term
            return _finish(art, t0, out_dir)

        claims = None
        for d in (shadow or {}).get("definitions") or []:
            if d.get("term") == term:
                claims = d.get("claims") or []
        if claims is None:
            art["error"] = "the shadow reports nothing for %r" % term
            return _finish(art, t0, out_dir)

        ir = build_ir(term, gloss, claims)
        art["ir"] = ir
        art["original_gloss"] = gloss
        art["execution"]["gloss_sha256"] = ir["gloss_sha256"]
        if ir["anchoring"] != "OK":
            art["error"] = "cannot build a safe edit over this gloss: %s (%s)" % (
                ir["anchoring"], "; ".join(ir["refusals"])[:200])
            return _finish(art, t0, out_dir)

        target = select_target(ir, unit_id)
        if target is None:
            art["error"] = ("no single repairable unit selected; candidates=%s"
                            % ir.get("repairable_candidates") or "none")
            return _finish(art, t0, out_dir)
        art["repairable_unit_id"] = target["unit_id"]
        art["repairable_text"] = target["text"]

        win = edit_window(ir, target)
        evidence = evidence_rows(arch, ledger, term)
        user = build_user(ir, target, win, evidence)
        art["execution"]["user_prompt_sha256"] = PV.sha256_text(user)
        art["execution"]["evidence_sha256"] = _h(
            [{"id": f, "proposition": p, "support_span": s} for f, p, s in evidence])

        reply = ask(SYSTEM, user)
        art["physical_model_calls"] = 1

        errs = validate(reply, ir, target, evidence)
        if errs:
            art["status"] = "REFUSED"
            art["validation_errors"] = errs[:10]
            art["error"] = "the proposed edit did not pass: %s" % errs[0]
            return _finish(art, t0, out_dir)

        stolen = sorted(k for k in reply if k in TOOL_OWNED)
        if stolen:
            art["tool_fields_ignored"] = stolen
        art["edit_plan"] = {k: reply.get(k) for k in
                            ("operation", "replacement", "left_glue", "right_glue", "reason")}
        art["execution"]["edit_plan_sha256"] = _h(art["edit_plan"])

        repaired = compile_repair(ir, target, win, reply)
        proof = prove_preservation(ir, target, repaired)
        art["preservation"] = proof

        hard = []
        if not proof["all_protected_survived"]:
            hard.append("protected unit(s) did not survive verbatim: %s" % proof["protected_lost"])
        if proof["explanatory_units"] and len(proof["explanatory_survived"]) != len(proof["explanatory_units"]):
            hard.append("explanatory unit(s) did not survive")
        if not proof["repairable_text_absent"]:
            hard.append("the unsupported span is still present in the repaired gloss")
        if not repaired.strip():
            hard.append("the repaired gloss is empty")
        if hard:
            art["status"] = "REFUSED"
            art["validation_errors"] = hard
            art["error"] = "the assembled repair failed its preservation proof: %s" % hard[0]
            art["rejected_gloss"] = repaired
            return _finish(art, t0, out_dir)

        art["repaired_gloss"] = repaired
        art["execution"]["repaired_gloss_sha256"] = PV.sha256_text(repaired)
        art["status"] = "REPAIRED"
    except Exception as e:                                        # noqa: BLE001
        art["status"] = "FAILED"
        art["error"] = "%s: %s" % (type(e).__name__, str(e)[:200])
    return _finish(art, t0, out_dir, call_meta)


def _finish(art, t0, out_dir, call_meta=None):
    art["wall_seconds"] = round(time.time() - t0, 1)
    if call_meta:
        art["physical_model_calls"] = call_meta.get("physical_model_calls",
                                                    art.get("physical_model_calls"))
    try:
        if out_dir is not None:
            import pathlib
            p = pathlib.Path(out_dir)
            p.mkdir(parents=True, exist_ok=True)
            (p / "DEFINITION_REPAIR.json").write_text(
                json.dumps(art, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    except Exception:                                             # noqa: BLE001
        pass
    return art


def _h(obj) -> str:
    try:
        return PV.sha256_text(json.dumps(obj, sort_keys=True, default=str))
    except Exception:                                             # noqa: BLE001
        return ""
