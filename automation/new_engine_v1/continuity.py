"""
continuity.py -- make an already-correct story read like continuous prose.

WHY THIS EXISTS. The owner read the ledger-bound Jia final and found the story, the
evidence containment and the Crip turn all sound, but said the Story Architect was still
visible through the prose. Paragraphs kept behaving as: rhetorical opener -> beat ->
little punchline.

Two mechanisms were measured, and the second is the one that matters.

1. TRANSCRIPTION. The Story Architect's prose fields contained the rhetorical staging
   itself, and the Writer copied it. Similarity between architect field and finished
   sentence:

     crip_turn   "Go back to the sand."                       -> "So go back to the sand."      0.93
     ending_move "Return to the salt walls: a surface someone -> "The salt was a surface someone
                  could have put a tongue to..."                  could have put a tongue to..." 0.90

   The architect was writing the performance, not the meaning.

2. SENTENCES THAT ANNOUNCE THEIR OWN STRUCTURAL JOB. The flagged sentences were
   "The answer was mostly things you cannot look at.", "So go back to the sand.",
   "Read that list again and notice what kind of description it is.", "That is an odd
   building to make." Each tells the reader what it is doing in the article rather than
   telling them about the world.

   CORRECTED 2026-09-04 (craft-research-v2 calibration). This module originally blamed the
   ONE-SENTENCE PARAGRAPH -- 5 of 15, 33% -- calling it "a slot that FORCES its sentence to
   perform". Measured against published prose, that diagnosis does not hold. Running
   writtenness() unmodified over 1,181 paragraphs of published nonfiction gives a solo_ratio
   range of 0.00-0.37, and Jia's 0.33 sits inside it: two Bregman texts (0.33, 0.37) and a
   ProPublica investigation (0.32) equal or exceed it. A measure on which excellent published
   work and the flagged draft are indistinguishable cannot be the diagnosis.

   The signpost-opener rate does separate them, by a wide margin:

       narrative exemplars (n=12)   mean 0.005/paragraph   max 0.025
       Bregman (n=18)               mean 0.046/paragraph   max 0.125
       jia.NEW.final.pre-audit      0.333/paragraph        (2.7x the published maximum)

   So one-sentence paragraphs are a normal pacing device -- pivot, question, verdict, breath,
   emphasis -- and carry no defect information on their own. What was wrong with the draft is
   that too many of its paragraphs opened by announcing their structural job.

   Note what was NOT the cause: the beat-to-paragraph ratio was 3.0, so beats were not
   being turned into paragraphs one for one. That earlier hypothesis was wrong too.

So paragraph ownership moves here, to the last stage, and the architect stops writing
rhetoric. This stage has LINGUISTIC freedom and ZERO factual freedom: it may merge,
split, re-paragraph and rephrase, and it may not introduce a proposition. Lineage is
necessary but not sufficient -- an editor can invent a claim while truthfully naming a
parent -- so lineage is paired with a semantic delta gate.
"""
from __future__ import annotations

import re

from .story import (SCENE_RISK, SENSORY_RISK, SPATIAL_RISK, _content_words, _entities,
                    _numbers, _stem, _FUNCTION_WORDS)

# ── operations the editor may declare ─────────────────────────────────────────
NO_CHANGE = "NO_CHANGE"          # a valid edit: good prose is left alone
REPHRASE = "REPHRASE"
MERGE = "MERGE_REPHRASE"
SPLIT = "SPLIT_REPHRASE"
DELETE = "DELETE"                # signposting removed; no output sentence
OPERATIONS = (NO_CHANGE, REPHRASE, MERGE, SPLIT, DELETE)


def sentences(text: str) -> list:
    body = text.split("---", 2)[2] if text.startswith("---") else text
    body = re.sub(r"^#\s+.*\n", "", body.strip(), count=1)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", body.strip()) if s.strip()]


def paragraphs(text: str) -> list:
    body = text.split("---", 2)[2] if text.startswith("---") else text
    body = re.sub(r"^#\s+.*\n", "", body.strip(), count=1)
    return [p.strip() for p in body.split("\n\n") if p.strip()]


def label_draft(text: str) -> dict:
    """D001.. over the Writer draft. Stable input identity for lineage."""
    return {"D%03d" % (i + 1): s for i, s in enumerate(sentences(text))}


# ── LINEAGE: necessary, not sufficient ───────────────────────────────────────
def validate_lineage(edits: list, draft: dict) -> list:
    """Every reader-facing output sentence must have at least one semantic parent."""
    errs = []
    seen = set()
    for i, e in enumerate(edits, 1):
        eid = e.get("id") or "<%d>" % i
        if eid in seen:
            errs.append("%s: duplicate output id" % eid)
        seen.add(eid)
        op = e.get("operation")
        if op not in OPERATIONS:
            errs.append("%s: operation %r not declared" % (eid, op))
        parents = e.get("parents") or []
        unknown = [p for p in parents if p not in draft]
        if unknown:
            errs.append("%s: parents not in the draft: %s" % (eid, unknown))
        if op == DELETE:
            if e.get("text"):
                errs.append("%s: a DELETE may not carry output text" % eid)
            continue
        if not (e.get("text") or "").strip():
            errs.append("%s: no output text" % eid)
        if not parents:
            errs.append("%s: output sentence with ZERO semantic parents" % eid)
        if op == MERGE and len(parents) < 2:
            errs.append("%s: MERGE declares fewer than two parents" % eid)
    return errs


def apply_edits(edits: list) -> str:
    """Render the edited article. Paragraph breaks are the editor's to place."""
    out, cur = [], []
    for e in edits:
        if e.get("operation") == DELETE:
            continue
        cur.append(e["text"].strip())
        if e.get("paragraph_break"):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return "\n\n".join(out)


# ── SEMANTIC DELTA: relations are first-class ────────────────────────────────
# A sentence can add no number, name, colour or material and still invent a fact. These
# are the relation classes that carry that risk.
RELATION_SHAPES = [
    (r"\bbecause\b|\bsince\b|\bas a result\b|\btherefore\b|\bso that\b|\bwhich is why\b"
     r"|\bcaused\b|\bled to\b|\bmeant that\b|\bresulted in\b", "CAUSAL"),
    (r"\bno\b|\bnot\b|\bnever\b|\bnone\b|\bnothing\b|\bnobody\b|\bwithout\b"
     r"|\bfailed to\b|\blacks?\b", "NEGATION"),
    (r"\bonly\b|\bmerely\b|\bjust the\b|\bsolely\b|\balone\b|\bnothing but\b", "EXCLUSIVITY"),
    (r"\bfirst\b|\blast\b|\bnever before\b|\bunprecedented\b|\bearliest\b", "FIRST_LAST"),
    (r"\bwanted\b|\bintended\b|\bhoped\b|\bin order to\b|\bdecided\b|\bset out to\b"
     r"|\bmeant to\b|\bdesigned to\b|\baimed to\b", "INTENT"),
    (r"\bbefore\b|\bafter\b|\bthen\b|\bonce\b|\buntil\b|\bby the time\b", "TEMPORAL"),
    (r"\bunlike\b|\bwhereas\b|\bmore than\b|\bless than\b|\bbetter than\b"
     r"|\bworse than\b|\brather than\b", "COMPARISON"),
    (r"\balways\b|\bevery\b|\ball \w+ are\b|\bany\b|\bgenerally\b|\bin general\b", "GENERALIZATION"),
]


def relations(text: str) -> dict:
    out = {}
    for pat, kind in RELATION_SHAPES:
        n = len(re.findall(pat, text, re.I))
        if n:
            out[kind] = out.get(kind, 0) + n
    return out


def _surface(text: str) -> dict:
    words = _content_words(text)
    return {"numbers": _numbers(text),
            "entities": _entities(text),
            "sensory": {w for w in words if w in SENSORY_RISK},
            "spatial": {w for w in words if w in SPATIAL_RISK},
            "scene": {w for w in words if w in SCENE_RISK}}


def semantic_delta(before: str, after: str) -> dict:
    """What factual surface and what relation classes did editing ADD?

    Compared whole-article rather than sentence-to-sentence, because a MERGE legitimately
    moves material between sentences; what may not happen is the article as a whole
    acquiring a proposition it did not have.
    """
    b, a = _surface(before), _surface(after)
    b_words = _content_words(before, fold=True)
    added_surface = {k: sorted(a[k] - b[k]) for k in a}
    rb, ra = relations(before), relations(after)
    added_rel = {k: ra[k] - rb.get(k, 0) for k in ra if ra[k] > rb.get(k, 0)}
    new_content = sorted(w for w in _content_words(after)
                         if w not in b_words and _stem(w) not in b_words)
    hard = any(added_surface[k] for k in ("numbers", "entities", "sensory",
                                          "spatial", "scene"))
    return {"added_surface": added_surface,
            "added_relation_classes": added_rel,
            "new_content_words": new_content,
            "hard_ok": not hard,
            "relations_ok": not added_rel,
            "ok": not hard and not added_rel}


def validate_semantic_delta(before: str, after: str, allow_relation_growth=()) -> list:
    """Fail closed. An unexplained delta HOLDS the article; it is never repaired with a
    caveat, because a caveat is how the research memo reached the prose originally."""
    d = semantic_delta(before, after)
    errs = []
    for k, v in d["added_surface"].items():
        if v:
            errs.append("editing added %s: %s" % (k, v))
    for k, n in d["added_relation_classes"].items():
        if k not in allow_relation_growth:
            errs.append("editing added %d %s relation(s) -- a relation is a factual "
                        "claim even with no new nouns" % (n, k))
    return errs


# ── WRITTENNESS: where the scaffolding shows ─────────────────────────────────
# Diagnostics, never a rule, and never a gate. Section 31 is explicit that banning sentence
# starters is not the fix; these numbers say WHERE to read.
#
# WHAT THIS TARGETS, precisely. Openers that point at the ARTICLE -- its structure, its
# argument's next move, or the reader's own reading process. It does NOT target the visible
# transition devices the craft literature teaches, because those point at the MATERIAL. That
# separation was verified rather than assumed: of six devices praised in The Open Notebook's
# "Good Transitions" -- head-to-tail echo ("If they begin."), the contrast turn, the "But
# wait" reversal ("Or so scientists thought."), a dated launch-pad sentence, a bridge clause,
# and a short declarative content opener ("Phages are viruses.") -- this list flags ZERO. Of
# the four sentences the owner flagged in the Jia draft, it flags four.
#
# It does flag legitimate reader instructions in argument and newsletter forms: Bregman's
# "Look at the first line of this graph." and "Remember: the models of today are the worst
# models we will ever have." are both caught. That is why the reading below is banded against
# published rates instead of thresholded at zero, and why it is form-sensitive.
#
# A leading connective must not hide the instruction: "So go back to the sand." is a
# reader instruction wearing a "So". An earlier version of this list missed it, which is
# how the sentence survived into the draft the owner then flagged.
_LEAD = r"(?:so|now|and so|and then|but)?\s*"
SIGNPOST_SHAPES = [
    (r"^(?:so|now|and so)\b[^.]{0,40}\.?$", "bare signpost"),
    (_LEAD + r"(?:read|look at|notice|consider|remember|go back|return)\b",
     "reader instruction"),
    (r"^(?:that is|this is|which)\b", "pointer opener"),
    (r"^(?:the answer|the point|the thing)\b", "answer announcement"),
    (r"^(?:then it was|and then)\b", "beat closer"),
]


# ── empirical calibration ────────────────────────────────────────────────────
# Measured by running the functions in this module, unmodified, over published nonfiction
# they were not built for. Provenance and per-text rows:
#   .claude/story-architecture/craft-research-v2/metrics/pr62_detector_calibration.json
#   .claude/story-architecture/craft-research-v2/reports/CRAFT_METRICS_V2.md
#
# These are the rates of ONE corpus, not a law. They exist so the signal can be read against
# something real instead of against zero. Widen them when the corpus widens; do not promote
# them to a threshold that holds an article.
WRITTENNESS_CALIBRATION = {
    "measured": "2026-09-04",
    "corpus": "18 Rutger Bregman public texts (43,115 w); 12 professionally annotated "
              "narrative/explanatory exemplars (50,033 w); 3-6 frozen Jia drafts",
    "signpost_per_paragraph": {
        "narrative_exemplars": {"n": 12, "mean": 0.005, "median": 0.000, "max": 0.025},
        "argument_essay_bregman": {"n": 18, "mean": 0.046, "median": 0.041, "max": 0.125},
        "jia_pre_audit": 0.333,
        "absolute_count_max": {"narrative_exemplars": 1, "argument_essay_bregman": 6,
                               "jia_flagged_draft_counts": [3, 4, 4, 5]},
    },
    "solo_ratio": {
        "narrative_exemplars": {"n": 12, "mean": 0.088, "min": 0.00, "max": 0.32},
        "argument_essay_bregman": {"n": 18, "mean": 0.127, "min": 0.00, "max": 0.37},
        "jia_pre_audit": 0.33,
        "verdict": "DESCRIPTIVE_ONLY -- the published range contains Jia's value, so this "
                   "measure carries no defect information.",
    },
    "not_calibrated_for": "Dutch or other non-English prose: SIGNPOST_SHAPES is English-only, "
                          "so a near-zero rate on non-English text is a language artefact, "
                          "not a finding.",
}

# Read against the corpus above. Bands are the observed maxima, not opinions:
#   <= narrative max (0.025)   ordinary for narrative and explanatory prose
#   <= argument max  (0.125)   ordinary for argument, essay and newsletter forms
#   >  argument max            above every published text measured -- go and read it
_SIGNPOST_NARRATIVE_MAX = 0.025
_SIGNPOST_ARGUMENT_MAX = 0.125
# Below this, one paragraph moves the rate too far for a band to mean anything. Jia has 15
# paragraphs, so one signpost is 0.067; BR-15 has 8, where a single instruction reads as 0.125.
_MIN_PARAS_FOR_READING = 10
# A rate alone over-reads short texts: two openers in twelve paragraphs is 0.167, which the
# bands above would call abnormal, yet two legitimate transitions are not a defect. So the
# top band needs an absolute count too. Corpus: no narrative exemplar exceeds ONE opener in
# a whole article (max 1, in a 68-paragraph feature); every flagged Jia draft has three or
# more. Three is therefore the smallest count the corpus will not vouch for.
_MIN_SIGNPOSTS_FOR_TOP_BAND = 3

ARGUMENT_FORMS = ("ARGUMENTATIVE_ESSAY", "REPORTED_ESSAY", "POLEMIC", "ESSAY", "COMMENT")


def signpost_reading(rate: float, paragraphs_n: int, form: str | None = None,
                     count: int | None = None) -> dict:
    """Interpret a signpost rate against published prose. Editorial, never a gate.

    `form` widens the ordinary band for argument-shaped writing, because the corpus says
    argument legitimately signposts about nine times more often than narrative does.

    `count` guards the top band against small-n noise: a high rate over few paragraphs is
    not the same finding as a high rate sustained across an article.
    """
    if paragraphs_n < _MIN_PARAS_FOR_READING:
        return {"band": "INSUFFICIENT_PARAGRAPHS", "rate": round(rate, 4),
                "ordinary_max_for_form": None,
                "form_assumed": (form or "NARRATIVE_DEFAULT"),
                "note": "under %d paragraphs a single opener swings the rate; no reading given"
                        % _MIN_PARAS_FOR_READING}
    ordinary_max = (_SIGNPOST_ARGUMENT_MAX if (form or "").upper() in ARGUMENT_FORMS
                    else _SIGNPOST_NARRATIVE_MAX)
    if rate <= ordinary_max:
        band, note = "WITHIN_PUBLISHED_RANGE", "ordinary for this form"
    elif rate <= _SIGNPOST_ARGUMENT_MAX:
        band, note = ("ELEVATED_FOR_FORM",
                      "above published narrative prose but inside the published argument "
                      "range; read it, and check whether the form is actually argument")
    elif count is not None and count < _MIN_SIGNPOSTS_FOR_TOP_BAND:
        band, note = ("ELEVATED_FOR_FORM",
                      "the rate is high but rests on only %d opener(s), which is too few to "
                      "call the architecture visible; read them and move on" % count)
    else:
        band, note = ("ARCHITECTURE_VISIBLE",
                      "above every published text in the calibration corpus, argument "
                      "included, and sustained across enough paragraphs to mean it; the "
                      "paragraphs are announcing their structural job")
    return {"band": band, "rate": round(rate, 4), "ordinary_max_for_form": ordinary_max,
            "signpost_count": count, "note": note,
            "form_assumed": (form or "NARRATIVE_DEFAULT")}


def writtenness(text: str, form: str | None = None) -> dict:
    """Diagnostics for where the scaffolding shows. Nothing here fails or holds an article.

    Two of the returned numbers mean different things, and conflating them is what this
    module got wrong until 2026-09-04:

      signpost_openers / signpost_rate  -- a real signal. Separates the flagged Jia draft
                                           from every published text measured.
      solo_ratio / solo_paragraphs      -- DESCRIPTIVE TELEMETRY ONLY. Published prose spans
                                           0.00-0.37 and Jia sits inside that. A one-sentence
                                           paragraph is an ordinary pacing device.
    """
    paras = paragraphs(text)
    solo = [p for p in paras if len(sentences(p)) == 1]
    edges, signposts = [], []
    for p in paras:
        ss = sentences(p)
        edges.append((ss[0], ss[-1]))
        for pat, kind in SIGNPOST_SHAPES:
            if re.match(pat, ss[0].strip(), re.I):
                signposts.append({"sentence": ss[0], "kind": kind, "where": "opener"})
                break
    L = [len(sentences(p)) for p in paras]
    sl = [len(s.split()) for s in sentences(text)]
    n = max(1, len(paras))
    rate = len(signposts) / n
    reading = signpost_reading(rate, len(paras), form, count=len(signposts))
    return {"paragraphs": len(paras),
            # --- descriptive telemetry: NOT a defect signal (see docstring) --------------
            "solo_paragraphs": len(solo),
            "solo_ratio": round(len(solo) / n, 2),
            "solo_texts": [s for p in solo for s in sentences(p)],
            "solo_ratio_is_a_defect_signal": False,
            "solo_ratio_published_range": (
                WRITTENNESS_CALIBRATION["solo_ratio"]["narrative_exemplars"]["min"],
                WRITTENNESS_CALIBRATION["solo_ratio"]["argument_essay_bregman"]["max"]),
            "pivot_paragraph_candidates": pivot_paragraph_candidates(text),
            # --- the signal --------------------------------------------------------------
            "signpost_openers": signposts,
            "signpost_rate": round(rate, 4),
            "signpost_reading": reading,
            # --- shape -------------------------------------------------------------------
            "sentences_per_paragraph": L,
            "sentence_len_median": sorted(sl)[len(sl) // 2] if sl else 0,
            "sentence_len_spread": (max(sl) - min(sl)) if sl else 0,
            "interpretation": "signposting %s (%.3f/para, form=%s); solo_ratio %.2f is "
                              "descriptive only" % (reading["band"], rate,
                                                    reading["form_assumed"],
                                                    round(len(solo) / n, 2))}


# ── pivot paragraphs: research terminology, telemetry only ───────────────────
# craft-research-v2 named a device visible in the Bregman corpus: a short standalone
# paragraph carrying the reader's next question, a bare verdict, a turn in understanding, or
# a breath. It is 8-9% of his paragraphs and 0% of 31 Scientias articles, so it is one
# writer's habit rather than a requirement of accessible prose.
#
# COUNTED, NEVER REQUESTED. There is deliberately no generator rule, no Writer instruction
# and no target for this. The failure mode being avoided is obvious: told to produce pivot
# paragraphs, a model would manufacture Bregman-shaped one-liners on demand, which is the
# performance this module exists to detect.
PIVOT_MAX_WORDS = 15


def pivot_paragraph_candidates(text: str) -> list:
    """Short standalone paragraphs, with the shape they happen to have. Telemetry."""
    out = []
    for i, p in enumerate(paragraphs(text)):
        w = len(p.split())
        if w <= PIVOT_MAX_WORDS and len(sentences(p)) <= 2:
            out.append({"index": i, "words": w, "text": p,
                        "shape": "QUESTION" if "?" in p else "STATEMENT"})
    return out


# ── the architect must stop writing the performance ──────────────────────────
RHETORICAL_DIRECTION = [
    r"\breturn to\b", r"\bgo back to\b", r"\bask the reader\b", r"\bremind the reader\b",
    r"\bnotice\b", r"\bpivot\b", r"\bland (?:with|on)\b", r"\bend (?:beat )?on\b",
    r"\bclose (?:the )?paragraph\b", r"\bcallback\b", r"\bpunchline\b",
    r"\brhetorical question\b", r"\bsurprise sentence\b", r"\bread .* again\b",
    r"\bstate the paradox\b", r"\bopen with\b", r"\bfinish on\b",
]


def architect_rhetoric(arch: dict) -> list:
    """Rhetorical micro-direction in the architect's fields, which the Writer transcribes.

    Measured at 0.90-0.93 similarity between these fields and finished sentences, so this
    is the transcription channel, not a style preference.
    """
    hits = []
    fields = ["story_spine", "opening_object_or_event", "reader_initial_state", "turn",
              "crip_turn", "ending_move"]
    for f in fields:
        v = str(arch.get(f) or "")
        for pat in RHETORICAL_DIRECTION:
            if re.search(pat, v, re.I):
                hits.append({"field": f, "pattern": pat.replace(r"\b", ""),
                             "text": v[:90]})
    for b in (arch.get("beats") or []):
        for f in ("happens", "why_reader_wants_next", "concept_introduced"):
            v = str(b.get(f) or "")
            for pat in RHETORICAL_DIRECTION:
                if re.search(pat, v, re.I):
                    hits.append({"field": "%s.%s" % (b.get("beat_id"), f),
                                 "pattern": pat.replace(r"\b", ""), "text": v[:90]})
    return hits


def validate_architect_is_semantic(arch: dict) -> list:
    """Beat purpose, not beat staging."""
    return ["architect field %s carries rhetorical direction (%s): %r"
            % (h["field"], h["pattern"], h["text"]) for h in architect_rhetoric(arch)]
