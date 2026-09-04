#!/usr/bin/env python3
"""
rq1_reader_state.py -- EXPERIMENTAL. Not imported by any authoritative path.

RQ-1 asks one question: does modelling the reader's actual information state produce
better nonfiction order than asking the architect to justify why the reader "wants the
next beat"?

The field under test in PR #62 is `why_reader_wants_next`. Its weakness is that it can be
satisfied by a plausible sentence about the architect's own outline -- "the reader wants to
know what the room was for, because this raises the question of the record" -- which is not
independently checkable against anything.

The alternative modelled here splits that single justification into four parts, three of
which can be checked against something outside the architect's own intention:

    reader_knows        reconstructable ONLY from material already delivered
    reader_now_wonders  the information pressure the delivered material created -- or NONE
    next_material       the approved material the article gives next
    next_move_relation  what the next material does to that state

WHAT THIS IS NOT. `reader_now_wonders` is an internal ordering model, never prose. If it
reaches the page as a rhetorical question, a "you may wonder", a "but first" or a "now
consider", the experiment has failed rather than succeeded: the point is better ORDER, not
more questions.

NONE is a first-class value. Scene continues, chronology carries itself, a description is
still unfolding -- in all of those the honest answer is that the reader has no new
information pressure, and forcing a question there is the failure mode being guarded
against.
"""
from __future__ import annotations

import re

# ── what the next material does to the reader's state ────────────────────────
ANSWERS = "ANSWERS"                # resolves the current uncertainty
DEEPENS = "DEEPENS"                # answers, and the answer raises a sharper question
COMPLICATES = "COMPLICATES"        # undermines an easy answer the reader had formed
DEFERS = "DEFERS"                  # knowingly delays, giving needed material meanwhile
CONTINUES = "CONTINUES"            # no active question; action or time simply proceeds
CHANGES_SCALE = "CHANGES_SCALE"    # moves from object/person/event to a wider context
NONE_REL = "NONE"                  # no intelligible relation -- a defect if asserted
RELATIONS = (ANSWERS, DEEPENS, COMPLICATES, DEFERS, CONTINUES, CHANGES_SCALE, NONE_REL)

# Relations that are legitimate with no active reader question. Their existence is the
# guard against turning every transition into question-and-answer.
QUESTIONLESS_OK = (CONTINUES, CHANGES_SCALE, DEFERS)

NO_QUESTION = "NONE"

_STOP = set("""that this these those with from into about only just also been were
have hass been being which what when where were than then they them their there
some more most much many such very same other another does doing done""".split())

# ── the leak set: reader-state language that must never reach prose ───────────
# Checked on the ARTICLE, not on the architecture. Section 6 and 21 of the brief.
QUESTION_SERIALIZATION = [
    (r"\byou (?:might|may|could) (?:wonder|ask|be wondering)\b", "reader address"),
    (r"\bthe question is\b", "question announcement"),
    (r"\bwhich raises the question\b", "question announcement"),
    (r"\bso why\b", "rhetorical why"),
    (r"\bso what\b", "rhetorical so-what"),
    (r"\bbut first\b", "outline signpost"),
    (r"\bnow consider\b", "outline signpost"),
    (r"\bthis brings us\b", "outline signpost"),
    (r"\bwhich brings us\b", "outline signpost"),
    (r"\bgo back to\b", "reader instruction"),
    (r"\bread (?:that|this) again\b", "reader instruction"),
    (r"\bconsider (?:this|for a moment)\b", "reader instruction"),
    (r"\bwhat (?:exactly )?(?:was|is) it for\?", "planted question"),
    (r"\bone might ask\b", "reader address"),
]


def question_serialization(article: str) -> list:
    """Every place the internal model has become visible prose. Zero is required."""
    out = []
    for pat, kind in QUESTION_SERIALIZATION:
        for m in re.finditer(pat, article, re.I):
            s = max(0, m.start() - 60)
            out.append({"kind": kind, "match": m.group(0),
                        "context": article[s:m.end() + 60].replace("\n", " ")})
    return out


def rhetorical_question_count(article: str) -> int:
    """Question marks in the body. Reader-state planning must not raise this."""
    body = article.split("---", 2)[2] if article.startswith("---") else article
    body = re.sub(r"^#\s+.*$", "", body, flags=re.M)
    return body.count("?")


# ── validation of the experimental contract ──────────────────────────────────
def validate_reader_state(states: list, delivered_facts: list) -> list:
    """Check a reader-state plan. `states[i]` describes section i, with two DIFFERENT
    boundaries in one record -- a distinction that has to be explicit or the check is
    meaningless:

        reader_knows_entering   the state BEFORE section i, so it may only contain material
                                delivered by sections 0..i-1
        reader_now_wonders_leaving  the state AFTER section i, so it must be caused by
                                material delivered by sections 0..i inclusive

    `delivered_facts[i]` is the list of fact PROPOSITIONS section i delivers. Checking
    against propositions rather than against the architect's own one-line summaries matters:
    a summary saying "a five-day festival on a shoreline in Sanur" does not contain the words
    "13 to 17 August" or "Pengembak", but the fact it delivers does, so the reader really has
    been told. An earlier version of this function compared against the summaries and
    produced four false violations on the first plan it was given.
    """
    errs = []
    for i, st in enumerate(states):
        tag = st.get("boundary") or st.get("section_id") or "section %d" % i
        rel = st.get("next_move_relation")
        is_last = (i == len(states) - 1)
        if is_last and not rel:
            rel = None                      # a final section has nothing following it
        elif rel not in RELATIONS:
            errs.append("%s: next_move_relation %r not in %s" % (tag, rel, RELATIONS))

        knows = st.get("reader_knows_entering", st.get("reader_knows")) or []
        if not isinstance(knows, list):
            errs.append("%s: reader_knows_entering must be a list" % tag)
            knows = []
        before = " ".join(" ".join(f) for f in delivered_facts[:i]).lower()
        if i == 0 and knows:
            errs.append("%s: the first section cannot enter with the reader already "
                        "knowing anything" % tag)
        for k in knows:
            key = [w for w in re.findall(r"[a-z]{4,}", str(k).lower()) if w not in _STOP][:8]
            if not key or not before:
                continue
            hit = sum(1 for w in key if w in before)
            if hit / len(key) < 0.5:
                errs.append("%s: reader_knows_entering claims %r, and only %d of %d content "
                            "words appear in any fact delivered before this section"
                            % (tag, str(k)[:70], hit, len(key)))

        wonders = (st.get("reader_now_wonders_leaving",
                          st.get("reader_now_wonders")) or "").strip()
        has_q = bool(wonders) and wonders != NO_QUESTION
        if has_q and i == 0 and not (delivered_facts and delivered_facts[0]):
            errs.append("%s: a question here cannot have been caused by prior material, "
                        "because this section delivers nothing" % tag)
        if rel is not None:
            if not has_q and rel not in QUESTIONLESS_OK:
                errs.append("%s: no active question, so the relation must be one of %s, "
                            "not %r" % (tag, QUESTIONLESS_OK, rel))
            if has_q and rel == CONTINUES:
                errs.append("%s: an open question with relation CONTINUES leaves the "
                            "pressure unserved; use DEFERS if the delay is deliberate" % tag)
    return errs


def questionless_share(states: list) -> float:
    """How much of the article moves with no active reader question. Guards the formula."""
    if not states:
        return 0.0
    def _w(s):
        return (s.get("reader_now_wonders_leaving", s.get("reader_now_wonders")) or "").strip()
    n = sum(1 for s in states if not _w(s) or _w(s) == NO_QUESTION)
    return round(n / len(states), 3)


def relation_mix(states: list) -> dict:
    out = {}
    for s in states:
        r = s.get("next_move_relation")
        out[r] = out.get(r, 0) + 1
    return out
