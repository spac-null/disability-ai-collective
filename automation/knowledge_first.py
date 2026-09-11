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

import datetime
import json
import os
import pathlib
import random
import re
import sqlite3

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
_STATUS = re.compile(
    r"^\*\*STATUS:\*\*\s*\**"
    r"(APPROVED_DURABLE|CANDIDATE|NEEDS_RESEARCH|REJECTED|RETIRED)\b", re.M)
_QUESTION = re.compile(r"^\*\*QUESTION\.\*\*\s*(.+?)(?=\n\n|\n\*\*)", re.M | re.S)
_SKIP = {"INDEX.md", "README.md"}

# ══════════════════════════════════════════════════════════════════════════════
# NO_ACCESS_ORIGIN. Owner doctrine, stronger than the prompt-level NO ACCESS-DEFICIT rule
# above: accessibility may appear inside a commissioned story as EVIDENCE, but it may not
# be what the QUESTION ITSELF is about -- not the central proposition, not the carrier, not
# the reason the article exists. This is a judgement about each question's own proposition,
# made once per question by reading it (never a runtime keyword scan of story text), so it
# is recorded here as an explicit, reviewable set rather than inferred from wording.
#
# Reviewed against every question currently loadable from .claude/perspective-research/
# (entries without their own **QUESTION.** field, e.g. PR004-07/08, are never loadable and
# are not reviewed here):
#
#   PR004-04 -- "Did this remain an accommodation attached to one project, or did it change
#   how the place ordinarily works?" The mechanism, carriers and evidence are ALL about an
#   access practice/programme's institutional status (tours, staffing, a budget line staying
#   or ending). Access provision is not evidence here, it is the subject. REJECTED.
#
#   PR004-06 -- "Did the access intervention only change who could encounter the work, or did
#   it materially change what was installed, performed, interpreted or experienced?" The
#   question is literally about an access intervention's effect. REJECTED.
#
# Every other currently loadable question (PR004-01, 02, 03, 05, 09) asks about mediation,
# authorship, translation, historiographic method or a tool generating new artistic
# vocabulary -- accessibility facts may appear inside their evidence without being what the
# question is about, and none is rejected.
#
# A new question added to the Perspective Library must be read and, if its own proposition is
# about access provision/intervention/accommodation rather than mediation, authorship,
# translation or artistic material, added here. Defaulting an unreviewed id to allowed (rather
# than rejecting the whole cluster) keeps a missing review from silently blocking every future
# question; the prompt-level NO ACCESS-DEFICIT self-check downstream is the second line of
# defense either way.
ACCESS_ORIGIN_QUESTION_IDS = frozenset({
    "PR004-04",
    "PR004-06",
})


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
            entry = text[m.end():end]
            status = _STATUS.search(entry)
            if not status or status.group(1) != "APPROVED_DURABLE":
                continue
            q = _QUESTION.search(entry)
            if not q:
                continue
            out.append({"id": m.group(1), "cluster": m.group(1).split("-")[0],
                        "title": m.group(2).strip(),
                        "question": re.sub(r"\s+", " ", q.group(1)).strip(),
                        "doc": f.name, "status": status.group(1)})
    return out


def select_question(questions: list, *, exclude: set | None = None, rng=None) -> dict | None:
    """One question, preferring the active cluster, excluding ones already commissioned.

    ACCESS_ORIGIN_QUESTION_IDS is excluded unconditionally, not merely offered as a default:
    a caller cannot accidentally re-admit an access-origin question by passing a narrower
    `exclude` set.
    """
    seen = set(exclude or ()) | ACCESS_ORIGIN_QUESTION_IDS
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


class SearchUnavailable(Exception):
    """The search provider could not be reached or refused the request.

    A DISTINCT type on purpose. This was previously swallowed into an empty result list,
    so a 403, an expired key, a network partition and "the web genuinely has nothing about
    this story" all arrived at the caller as the same silent no-anchor refusal. That is the
    failure mode that hid a real production blocker: OpenRouter began returning
    `{"error":{"message":"Key limit exceeded (monthly limit)","code":403}}` and the lane
    reported NO_FETCHABLE_ANCHOR, which reads as editorial scarcity. A provider failure is
    an INFRASTRUCTURE failure and must reach an operator.
    """


def anchor_candidates(cand: dict, search_fn, *, api_key: str = "") -> list:
    """Real URLs for one proposed story. The searcher NAMES pages; it supplies no text.

    Raises SearchUnavailable if EVERY query failed technically. A single query failing
    while another returns results is ordinary and is not escalated -- what must never be
    silently absorbed is a search path that did not run at all.
    """
    urls: list = []
    errors: list = []
    queries = [str(q) for q in (cand.get("search_queries") or [])[:MAX_QUERIES_PER_STORY]
               if str(q or "").strip()]
    for q in queries:
        try:
            found = search_fn(q, api_key=api_key) or []
        except Exception as e:
            errors.append("%s: %s" % (type(e).__name__, str(e)[:200]))
            continue
        for u in found[:MAX_URLS_PER_QUERY]:
            if u not in urls:
                urls.append(u)
    if queries and len(errors) == len(queries):
        raise SearchUnavailable("; ".join(errors[:3]))
    return urls


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTED COMMISSIONING STATE
# ══════════════════════════════════════════════════════════════════════════════
# WHY THIS EXISTS. Each knowledge_first commissioning attempt is a separate process (a cron
# invocation of production_orchestrator.py). `select_question`'s `exclude` parameter has
# always existed, but nothing before this persisted a value INTO it across processes, so
# three separate runs the same day each started from an empty exclude set: two picked
# PR004-02 (the second by accident when memory of the first process was already gone), and
# all three, working from different questions, converged on naming the identical Whitney/Kim
# exhibition as their story -- because nothing recorded that it had already been used either.
#
# This reuses the project's existing state database (disability_findings.db, the same file
# production_orchestrator.py already opens for the ordinary-world seed pool) rather than a
# parallel store, adding one small table to it. A caller that does not pass `state_conn` gets
# exactly the previous in-memory behaviour -- this is additive, not a required dependency, so
# every existing offline test of `commission()` is unaffected.
STATE_TABLE = "kf_identity_claims"


def ensure_state_schema(conn) -> None:
    """Idempotent DDL for the claims table. Safe to call on every commissioning attempt."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS %s ("
        " kind TEXT NOT NULL,"          # 'question' or 'story'
        " key TEXT NOT NULL,"           # question id, or a normalized story-identity key
        " question_id TEXT,"
        " run_id TEXT,"
        " status TEXT,"
        " claimed_at TEXT NOT NULL,"
        " PRIMARY KEY (kind, key))" % STATE_TABLE)
    conn.commit()


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load_claimed_question_ids(conn) -> set:
    """Every question id already attempted (commissioned OR refused OR held) in a prior
    process. A failed attempt claims its question exactly like a successful one -- see
    `claim_question`."""
    ensure_state_schema(conn)
    rows = conn.execute(
        "SELECT key FROM %s WHERE kind = 'question'" % STATE_TABLE).fetchall()
    return {r[0] for r in rows}


def claim_question(conn, question_id: str, run_id: str | None = None) -> None:
    """Claim a question id BEFORE the model call that proposes stories for it -- the
    expensive work this is meant to guard. INSERT OR IGNORE: a question already claimed
    (by this run seeding itself, or a retained-artifact backfill) stays claimed under
    whichever record came first, and re-claiming is not an error."""
    ensure_state_schema(conn)
    conn.execute(
        "INSERT OR IGNORE INTO %s (kind, key, question_id, run_id, status, claimed_at) "
        "VALUES ('question', ?, ?, ?, 'attempted', ?)" % STATE_TABLE,
        (question_id, question_id, run_id, _utcnow()))
    conn.commit()


_URL_TRIM = re.compile(r"^www\.")
# A possessive or contraction apostrophe ("artist's") is not a quote delimiter: the opening
# delimiter must follow start-of-string, whitespace or an opening bracket, never a letter, or
# "artist's retrospective 'Title'" would extract "s retrospective" instead of "Title".
_QUOTED_TITLE = re.compile(
    r"(?:^|(?<=[\s(]))['\"‘“]([^'\"‘’“”]{3,80}?)['\"’”](?=$|[\s.,;:!?)])")
_WS = re.compile(r"\s+")


def normalize_anchor_url(url: str) -> str:
    """Scheme/host-case/www/query/fragment/trailing-slash differences are not different
    stories. Deliberately simple: this is a dedupe key, not a URL parser with edge-case
    ambitions."""
    u = str(url or "").strip()
    u = re.sub(r"^https?://", "", u, flags=re.I)
    u = _URL_TRIM.sub("", u, count=1) if u.lower().startswith("www.") else u
    u = u.split("?", 1)[0].split("#", 1)[0]
    u = u.rstrip("/")
    return u.lower()


def _extract_quoted_titles(text: str) -> set:
    """Quoted work/exhibition titles inside a candidate's own subject line, e.g. "'All Day
    All Night'". A structural extraction, not a content judgement: two candidates that name
    the same quoted title are the same story regardless of which URL or which question named
    it, exactly the case observed across PR004-02 and PR004-06 both landing on Kim's 'All Day
    All Night'."""
    out = set()
    for m in _QUOTED_TITLE.finditer(text or ""):
        t = _WS.sub(" ", m.group(1)).strip().lower()
        if len(t) >= 3:
            out.add(t)
    return out


def story_identity_keys(subject: str, url: str) -> set:
    """Every key under which this candidate's story identity should be checked/claimed: its
    anchor URL, and any quoted title named in its own subject line. A collision on EITHER
    key is the same story; claiming writes both."""
    keys = {"url:%s" % normalize_anchor_url(url)}
    keys |= {"title:%s" % t for t in _extract_quoted_titles(subject or "")}
    return keys


def is_story_claimed(conn, keys: set) -> bool:
    if not keys:
        return False
    ensure_state_schema(conn)
    qmarks = ",".join("?" for _ in keys)
    row = conn.execute(
        "SELECT 1 FROM %s WHERE kind = 'story' AND key IN (%s) LIMIT 1"
        % (STATE_TABLE, qmarks), tuple(keys)).fetchone()
    return row is not None


def claim_story(conn, keys: set, question_id: str, run_id: str | None = None) -> None:
    """Claim every identity key for a story BEFORE it is returned as a seed -- before the
    expensive downstream engine (acquisition, Research, Ledger, Worth, Architecture, ...)
    ever sees it. A run that is later HELD or fails has still claimed it: retrying the exact
    same story until it happens to pass a gate is exactly the gate-shopping this prevents."""
    if not keys:
        return
    ensure_state_schema(conn)
    now = _utcnow()
    conn.executemany(
        "INSERT OR IGNORE INTO %s (kind, key, question_id, run_id, status, claimed_at) "
        "VALUES ('story', ?, ?, ?, 'attempted', ?)" % STATE_TABLE,
        [(k, question_id, run_id, now) for k in keys])
    conn.commit()


def seed_exclusions_from_retained(conn, evidence_root) -> int:
    """Backfill claims from COMMISSION.json records this lane already wrote to disk before
    this table existed (or from a process that crashed before it could persist). Idempotent
    (INSERT OR IGNORE) and safe to call at the start of every commissioning attempt: existing
    retained runs seed the exclusions exactly once, and re-reading them on a later run is a
    no-op. Corrupt or partial records are skipped, never fatal -- this is a backfill, not the
    source of truth for whether a run happened.

    Returns the number of COMMISSION.json files it read (not the number of new claims, most
    of which will already be present after the first call).
    """
    ensure_state_schema(conn)
    root = pathlib.Path(evidence_root) if evidence_root else None
    if not root or not root.is_dir():
        return 0
    seen = 0
    for f in root.glob("**/COMMISSION.json"):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        seen += 1
        q = rec.get("question") or {}
        qid = q.get("id")
        if qid:
            claim_question(conn, qid, run_id="retained:%s" % f.parent.name)
        chosen = rec.get("chosen") or {}
        seed = rec.get("seed") or {}
        subject = chosen.get("subject") or seed.get("title") or ""
        url = chosen.get("anchor_url") or seed.get("url") or ""
        if subject or url:
            claim_story(conn, story_identity_keys(subject, url), qid,
                        run_id="retained:%s" % f.parent.name)
    return seen


def commission(provider, *, search_fn, fetch_fn, questions=None, exclude=None,
               api_key: str = "", rng=None, state_conn=None, run_id: str | None = None,
               evidence_root=None) -> dict:
    """(seed | None, record). The seed is the SAME shape the selector returns, so the
    entire downstream engine is reached unchanged.

    `state_conn`, if given, is a sqlite3 connection used to persist question and story
    identity claims across process invocations (see PERSISTED COMMISSIONING STATE above).
    Omitting it reproduces the exact previous in-memory-only behaviour. `evidence_root`, if
    given alongside `state_conn`, backfills claims from retained COMMISSION.json records
    once per call -- cheap and idempotent, so callers need not manage a separate migration
    step.
    """
    qs = questions if questions is not None else load_questions()
    persisted_exclude = set()
    if state_conn is not None:
        if evidence_root is not None:
            seed_exclusions_from_retained(state_conn, evidence_root)
        persisted_exclude = load_claimed_question_ids(state_conn)
    q = select_question(qs, exclude=(set(exclude or ()) | persisted_exclude), rng=rng)
    rec = {"lane": LANE, "questions_available": len(qs), "question": q,
           "candidates": [], "tried": [], "seed": None, "model_calls": 0}
    if not q:
        rec["status"] = "NO_QUESTION_AVAILABLE"
        return rec
    if state_conn is not None:
        # Claimed BEFORE the model call below: the first expensive step this attempt takes.
        # A commission call failure, a search failure or a downstream HOLD all still leave
        # this question claimed, exactly as intended.
        claim_question(state_conn, q["id"], run_id=run_id)
    try:
        proposed = propose_stories(provider, q)
    except Exception as e:
        rec["status"] = "COMMISSION_CALL_FAILED"
        rec["technical_failure"] = True
        rec["run_status"] = {"status": "PROVIDER_FAILURE", "stage": "KF_COMMISSION",
                             "detail": "%s: %s" % (type(e).__name__, str(e)[:200])}
        rec["error"] = "%s: %s" % (type(e).__name__, str(e)[:200])
        return rec
    rec["model_calls"] = proposed.get("model_calls", 0)
    rec["provider"] = proposed.get("provider", {})
    rec["candidates"] = proposed["candidates"]
    if not proposed["candidates"]:
        rec["status"] = "NO_STORY_FOR_QUESTION"
        return rec

    for cand in proposed["candidates"]:
        try:
            urls = anchor_candidates(cand, search_fn, api_key=api_key)
        except SearchUnavailable as e:
            # OPERATOR-VISIBLE, and it stops here rather than trying the next candidate:
            # if search itself is down, every remaining candidate would fail identically
            # and the run would look like it had honestly looked and found nothing.
            rec["status"] = "SEARCH_UNAVAILABLE"
            rec["technical_failure"] = True
            rec["run_status"] = {"status": "PROVIDER_FAILURE", "stage": "KF_SEARCH",
                                 "detail": str(e)[:300]}
            rec["error"] = str(e)[:300]
            return rec
        for url in urls:
            if state_conn is not None and is_story_claimed(
                    state_conn, story_identity_keys(cand.get("subject") or "", url)):
                rec["tried"].append({"url": url,
                                     "reason": "story identity already commissioned"})
                continue
            try:
                text = fetch_fn(url) or ""
            except Exception as e:
                rec["tried"].append({"url": url, "error": str(e)[:120]})
                continue
            if len(text) < MIN_ANCHOR_CHARS:
                rec["tried"].append({"url": url, "chars": len(text),
                                     "reason": "below anchor floor"})
                continue
            if state_conn is not None:
                # Claimed BEFORE this is returned to the caller, who runs the real,
                # expensive engine (acquisition, Research, Ledger, Worth, Architecture,
                # Writer, ...) on it next.
                claim_story(state_conn, story_identity_keys(cand.get("subject") or "", url),
                           q["id"], run_id=run_id)
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
