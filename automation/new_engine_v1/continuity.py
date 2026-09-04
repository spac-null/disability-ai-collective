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

2. PERFORMANCE SLOTS. 5 of 15 paragraphs were a single sentence -- 33% -- and they were
   almost exactly the sentences the owner flagged: "The answer was mostly things you
   cannot look at.", "So go back to the sand.", "The account has it as brick." A
   one-sentence paragraph is a slot that FORCES its sentence to perform. That is a
   paragraphing decision, not a wording decision, which is why rewriting the sentences
   never fixed it.

   Note what was NOT the cause: the beat-to-paragraph ratio was 3.0, so beats were not
   being turned into paragraphs one for one. The earlier hypothesis was wrong.

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
# Diagnostics, never a rule. Section 31 is explicit that banning sentence starters is not
# the fix; these numbers say WHERE to read.
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


def writtenness(text: str) -> dict:
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
    return {"paragraphs": len(paras),
            "solo_paragraphs": len(solo),
            "solo_ratio": round(len(solo) / max(1, len(paras)), 2),
            "solo_texts": [s for p in solo for s in sentences(p)],
            "signpost_openers": signposts,
            "sentences_per_paragraph": L,
            "sentence_len_median": sorted(sl)[len(sl) // 2] if sl else 0,
            "sentence_len_spread": (max(sl) - min(sl)) if sl else 0}


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
