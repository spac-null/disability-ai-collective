#!/usr/bin/env python3
"""knowledge_first.py -- the PRIMARY commissioning lane.

WHY THIS LANE EXISTS. The existing lane can only collide Crip Minds thinking with whatever
general news happens to arrive that morning. Checked against 69 retained candidates, it is
NOT biased toward access/architecture subjects -- those pass Worth at 29-44% against 69-70%
for transferred-knowledge carriers, and Worth refuses access-classifying readings on its
own. So the front door is not broken and is not being replaced. What it cannot do is
DELIBERATELY SEEK the intellectual territory the publication is about: signed language and
mediation, nonvisual knowledge, disabled authorship, disability aesthetics, care and
interdependence as knowledge, classification changing culture, technologies disability
helped produce.

So this lane inverts the order:

    APPROVED INTELLECTUAL QUESTION  (perspective material)
      -> REAL STORY THAT CAN CARRY OR TEST IT   (one model call, names only)
      -> REAL ANCHOR SOURCE                     (search + fetch, as normal)
      -> the EXISTING pipeline, unchanged: Research, Ledger, Worth, Architecture,
         Safety, Grounding, Fact Check, Reader, publication bridge.

THE HARD BOUNDARY IS THE ONE ALREADY IN DOCTRINE. Perspective material licenses only a
QUESTION. It licenses no fact, and nothing from it may be quoted in an article. Every
factual permission still comes from targeted research and the frozen Ledger, and no
downstream standard moves. This module therefore produces exactly one thing: an anchor
seed of the same shape the selector already returns.
"""
from __future__ import annotations

import json
import os
import pathlib
import random
import re

HERE = pathlib.Path(__file__).resolve().parent
PERSPECTIVE_DIR = HERE.parent / ".claude" / "perspective-research"

LANE = "KNOWLEDGE_FIRST"
LANE_SECONDARY = "ORDINARY_WORLD_COLLISION"

# The active cluster is preferred but not exclusive: the owner's desired first territory is
# art / disability / aesthetic knowledge / institutions, which is PR004.
PREFERRED_CLUSTER = "PR004"
MAX_STORIES = 4
MAX_QUERIES_PER_STORY = 2
MAX_URLS_PER_QUERY = 4
MIN_ANCHOR_CHARS = 1200

_ENTRY = re.compile(r"^### (PR\d{3}-\d{2}) — (.+?)$", re.M)
_QUESTION = re.compile(r"^\*\*QUESTION\.\*\*\s*(.+?)(?=\n\n|\n\*\*)", re.M | re.S)
_SKIP = {"INDEX.md", "README.md"}


def load_questions(directory: pathlib.Path | None = None) -> list:
    """The owner-approved questions, read from perspective material. Never authored here.

    Each entry in that directory already states its own QUESTION, reviewed by the owner.
    Inventing a question in code would be exactly the fabrication the perspective boundary
    forbids, so this only reads.
    """
    d = pathlib.Path(directory or PERSPECTIVE_DIR)
    out = []
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.md")):
        if f.name in _SKIP:
            continue
        text = f.read_text(encoding="utf-8")
        ents = list(_ENTRY.finditer(text))
        for i, m in enumerate(ents):
            end = ents[i + 1].start() if i + 1 < len(ents) else len(text)
            q = _QUESTION.search(text[m.end():end])
            if not q:
                continue
            out.append({"id": m.group(1), "cluster": m.group(1).split("-")[0],
                        "title": m.group(2).strip(),
                        "question": re.sub(r"\s+", " ", q.group(1)).strip(),
                        "doc": f.name})
    return out


def select_question(questions: list, *, exclude: set | None = None, rng=None) -> dict | None:
    """One question, preferring the active cluster, excluding ones already commissioned."""
    seen = set(exclude or ())
    pool = [q for q in questions if q["id"] not in seen]
    if not pool:
        return None
    preferred = [q for q in pool if q["cluster"] == PREFERRED_CLUSTER]
    r = rng or random
    return r.choice(preferred or pool)


# ══════════════════════════════════════════════════════════════════════════════
# FINDING A REAL STORY FOR THE QUESTION
# ══════════════════════════════════════════════════════════════════════════════
# This call NAMES candidate stories. It supplies no facts and its output is never evidence:
# everything it proposes must be independently researched afterwards, and anything the
# targeted research cannot establish simply is not in the article. That is why it is asked
# for search handles rather than for claims.
COMMISSION_SYSTEM = (
    "You are commissioning one article for Crip Minds, a disability-led publication that "
    "reads the world through disability as a way of KNOWING rather than as a subject to "
    "cover.\n"
    "\n"
    "You are given ONE intellectual question. Your job is to name REAL, CHECKABLE stories "
    "that could carry or test it -- and nothing else. You are not writing the article, not "
    "answering the question, and not supplying facts. Everything you name will be "
    "independently researched, and anything research cannot establish will be dropped.\n"
    "\n"
    "WHAT A GOOD CANDIDATE IS. A named artist, work, exhibition, retrospective, book, "
    "essay, interview, manifesto, collaboration, dispute, institutional change, or a "
    "documented historical transition. It must have people, events, objects, time, change, "
    "tension and consequence. An idea is not a story. A theme is not a story. Do not "
    "propose an abstract theory essay.\n"
    "\n"
    "WHY NOW. Each candidate needs a credible reason to exist now -- an exhibition open or "
    "touring, a retrospective, a new book or essay or interview that changed the "
    "conversation, an institutional decision, several practices showing a real emerging "
    "pattern, or an older work made newly relevant by a current shift. It does NOT need a "
    "breaking-news peg.\n"
    "\n"
    "THE ABSOLUTE EDITORIAL RULE -- NO ACCESS-DEFICIT STORIES. Crip Minds does not publish "
    "an article whose central proposition is that something is inaccessible, that disabled "
    "people cannot access it, that it creates barriers, that it should be made more "
    "accessible, or that there are accessibility problems at it. Ramps, captions, "
    "interpreters, lifts and toilets may appear inside research as evidence. They may never "
    "be the carrier, the thesis, the headline idea or the reason the article exists.\n"
    "  APPLY THIS TEST TO EVERY CANDIDATE: remove the accessibility language from your "
    "proposal. If the story disappears, DO NOT PROPOSE IT. The question is never \"why "
    "can't disabled people access X\"; it is \"what does X reveal about how the ordinary "
    "world imagines a body, a mind, a sense, a pace, a relation, a dependence or a form of "
    "participation\".\n"
    "\n"
    "DO NOT propose a profile of a disabled person because they are disabled. Do not "
    "propose 'representation' or 'awareness' stories. Do not invent a movement, a phase or "
    "a trend: if you name a broader development, name the several artists, institutions, "
    "critics or scholars that would have to be researched to establish it, so the claim can "
    "be tested and abandoned if it fails.\n"
    "\n"
    "Propose the strongest %(n)d candidates, best first. If you cannot honestly name a real "
    "story for this question, return an empty list -- that is a correct answer."
) % {"n": MAX_STORIES}

COMMISSION_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"candidates": [{\n'
    '   "subject": "the story in one concrete sentence: who or what, and what happened",\n'
    '   "why_now": "the credible current reason this is live",\n'
    '   "carrier": "the concrete person, work, event, object or decision it rests on",\n'
    '   "tests_the_question": "how this story could confirm OR fail the question",\n'
    '   "names_to_research": ["real proper names a researcher would look up"],\n'
    '   "search_queries": ["a query that would find primary material", "another"],\n'
    '   "access_deficit_self_check": "why this is NOT an access-deficit story"}]}\n'
    "No prose outside the JSON."
)


def _parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("commission reply was not one JSON object")
    return json.loads(m.group(0))


def propose_stories(provider, question: dict) -> dict:
    """ONE model call. Names stories; licenses nothing."""
    user = "\n".join([
        "THE QUESTION (from approved perspective material -- it licenses this question and "
        "NO fact):",
        "  %s" % question["question"],
        "  (mechanism: %s)" % question["title"],
        "",
        COMMISSION_SCHEMA,
    ])
    comp = provider.complete(system=COMMISSION_SYSTEM, user=user, max_tokens=2_000)
    obj = _parse(getattr(comp, "text", "") or "")
    cands = [c for c in (obj.get("candidates") or []) if isinstance(c, dict)
             and str(c.get("subject") or "").strip()]
    return {"question": question, "candidates": cands[:MAX_STORIES],
            "model_calls": 1,
            "provider": comp.identity() if hasattr(comp, "identity") else {}}


def anchor_candidates(cand: dict, search_fn, *, api_key: str = "") -> list:
    """Real URLs for one proposed story. The searcher NAMES pages; it supplies no text."""
    urls: list = []
    for q in (cand.get("search_queries") or [])[:MAX_QUERIES_PER_STORY]:
        if not str(q or "").strip():
            continue
        try:
            found = search_fn(str(q), api_key=api_key) or []
        except Exception:
            found = []
        for u in found[:MAX_URLS_PER_QUERY]:
            if u not in urls:
                urls.append(u)
    return urls


def commission(provider, *, search_fn, fetch_fn, questions=None, exclude=None,
               api_key: str = "", rng=None) -> dict:
    """(seed | None, record). The seed is the SAME shape the selector returns, so the
    entire downstream engine is reached unchanged."""
    qs = questions if questions is not None else load_questions()
    q = select_question(qs, exclude=exclude, rng=rng)
    rec = {"lane": LANE, "questions_available": len(qs), "question": q,
           "candidates": [], "tried": [], "seed": None, "model_calls": 0}
    if not q:
        rec["status"] = "NO_QUESTION_AVAILABLE"
        return rec
    try:
        proposed = propose_stories(provider, q)
    except Exception as e:
        rec["status"] = "COMMISSION_CALL_FAILED"
        rec["error"] = "%s: %s" % (type(e).__name__, str(e)[:200])
        return rec
    rec["model_calls"] = proposed.get("model_calls", 0)
    rec["provider"] = proposed.get("provider", {})
    rec["candidates"] = proposed["candidates"]
    if not proposed["candidates"]:
        rec["status"] = "NO_STORY_FOR_QUESTION"
        return rec

    for cand in proposed["candidates"]:
        for url in anchor_candidates(cand, search_fn, api_key=api_key):
            try:
                text = fetch_fn(url) or ""
            except Exception as e:
                rec["tried"].append({"url": url, "error": str(e)[:120]})
                continue
            if len(text) < MIN_ANCHOR_CHARS:
                rec["tried"].append({"url": url, "chars": len(text),
                                     "reason": "below anchor floor"})
                continue
            rec["seed"] = {
                "id": "kf-%s-%s" % (q["id"].lower(), abs(hash(url)) % 10_000_000),
                "url": url,
                "title": str(cand.get("subject") or "")[:300],
                "summary": str(cand.get("subject") or "")[:600],
                "source_name": "knowledge_first",
                "underlying_article_url": None,
            }
            rec["chosen"] = {"subject": cand.get("subject"),
                             "why_now": cand.get("why_now"),
                             "carrier": cand.get("carrier"),
                             "tests_the_question": cand.get("tests_the_question"),
                             "access_deficit_self_check":
                                 cand.get("access_deficit_self_check"),
                             "names_to_research": cand.get("names_to_research"),
                             "anchor_url": url, "anchor_chars": len(text)}
            rec["status"] = "COMMISSIONED"
            return rec
    rec["status"] = "NO_FETCHABLE_ANCHOR"
    return rec


def search_key() -> str:
    return os.environ.get("OPENROUTER_API_KEY", "")
