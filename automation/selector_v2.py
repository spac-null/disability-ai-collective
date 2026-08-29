"""
selector_v2.py -- SELECTOR V2, SHADOW ONLY, OFF BY DEFAULT.

    eligible pool (PR #48)
      -> three bounded deterministic exposure streams, unioned to ~12/day
      -> production source acquisition (the real one, curl_cffi and all)
      -> cheap deterministic source features
      -> MATERIAL_ASSESSMENT: is there enough concrete reality here to research?
      -> transparent ordering, every component inspectable

WHY
The authoritative selector spends its whole daily budget asking a model to invent a
disability angle from a headline and an RSS summary, then treats that invention as the
ticket into Priority 1. Measured on 24 read sources: the angle came back YES about 90%
of the time historically and approved weak material in 5 of 8 cases here; the
relevance_score that orders everything was uncorrelated with material quality (47%
strong above 0.55, 43% below 0.4); and the two highest-scoring candidates in the set
were an award announcement and a page of navigation markup. Meanwhile a Nautilus piece
about a blind cave fish scored 0.150 and read RICH.

So this stage stops guessing from headlines. It reads the source and asks one question:
is there enough here to justify researching it?

WHAT IT IS NOT
Not authoritative. It writes its own tables and its own report; it cannot change which
seed CURRENT_ENGINE receives, cannot touch disability_angle, cannot invoke Research Pack,
Discovery, Form or the Writer, and does not run at all unless CRIPMINDS_SELECTOR_V2_SHADOW
is explicitly set. The old selector stays exactly as it is until a cutover is separately
decided.

WHERE IT RUNS
new_engine_production._selector_v2_shadow, at the very end of a scheduled run -- after
the authoritative seed has been selected, fetched, carried through the whole engine and
written back. One comparison per run lands in 'selector_v2_shadow_runs': what the
authoritative selector chose, what this one would have chosen, whether they agreed.
Any failure inside it is logged as a SELECTOR_V2 warning and goes no further; a run that has already finished its real
work cannot be broken by an experiment.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta

import material_policy as MP
from new_engine_v1.provider import parse_json_object

SHADOW_ENV = "CRIPMINDS_SELECTOR_V2_SHADOW"
TABLE = "seed_material_assessments"
RUNS_TABLE = "selector_v2_shadow_runs"

# ── bounds, all reported ──────────────────────────────────────────────────────
STREAM_THEME = 6                 # A: legacy theme signal, booster removed
STREAM_URGENCY = 4               # B: least eligibility time remaining
STREAM_EXPLORE = 2               # C: deterministic day-stable exploration
DAILY_CANDIDATES = 12
BATCH_SIZE = 3                   # candidates per assessment call
BATCH_MAX_CHARS = 22_000
BATCH_MAX_TOKENS = 1_800
MAX_CALLS_PER_RUN = 10           # absolute ceiling
BODY_WORDS_TO_MODEL = 1_100
PUBLISHER_PENALTY_DAYS = 7       # decays to zero across a week
PUBLISHER_PENALTY_MAX = 0.30

OK = "OK"
ACQUISITION_FAILED = "SOURCE_ACQUISITION_FAILED"
ASSESSMENT_INVALID = "ASSESSMENT_INVALID"
ASSESSMENT_ERROR = "ASSESSMENT_ERROR"

RICHNESS = ("RICH", "MODERATE", "THIN")
LEVELS = ("HIGH", "MEDIUM", "LOW")
SHAPES = ("SINGLE_SUBJECT", "ROUNDUP", "LIST", "INTERVIEW", "REPORT", "PROMOTIONAL", "OTHER")
VERDICTS = ("STRONG_CANDIDATE", "POSSIBLE_CANDIDATE", "WEAK_CANDIDATE")


def enabled() -> bool:
    return str(os.environ.get(SHADOW_ENV, "")).strip().lower() in ("1", "true", "on", "yes")


# ── persistence: its own table, never news_seeds ──────────────────────────────
def ensure_schema(conn) -> None:
    """A separate table on purpose. news_seeds carries production selection state; an
    experiment must not add a dozen columns to it, and historical disability_angle must
    stay exactly as it is."""
    conn.execute("""CREATE TABLE IF NOT EXISTS %s (
        seed_id TEXT NOT NULL,
        source_url TEXT,
        source_sha256 TEXT NOT NULL,
        assessed_at TEXT,
        assessment_status TEXT,
        concrete_subject TEXT,
        subject_anchor_quote TEXT,
        investigable_question TEXT,
        question_basis_quote TEXT,
        material_richness TEXT,
        researchability TEXT,
        narrative_material TEXT,
        source_shape TEXT,
        specificity TEXT,
        assessment TEXT,
        reason TEXT,
        body_words INTEGER,
        paragraph_count INTEGER,
        det_roundup INTEGER,
        det_promotional INTEGER,
        exposed_via TEXT,
        theme_signal REAL,
        publisher_penalty REAL,
        shadow_rank INTEGER,
        errors TEXT,
        PRIMARY KEY (seed_id, source_sha256)
    )""" % TABLE)
    conn.commit()


def ensure_runs_schema(conn) -> None:
    """One row per natural run: what the authoritative selector chose, what the shadow
    would have chosen, and why. Accumulating these as they happen is the whole point --
    reconstructing old-vs-new pairs after the fact is not possible once the pool moves."""
    conn.execute("""CREATE TABLE IF NOT EXISTS %s (
        run_id TEXT PRIMARY KEY,
        run_at TEXT,
        old_seed_id TEXT,
        old_title TEXT,
        old_source_name TEXT,
        old_relevance_score REAL,
        shadow_seed_id TEXT,
        shadow_title TEXT,
        shadow_source_name TEXT,
        shadow_assessment TEXT,
        shadow_richness TEXT,
        shadow_researchability TEXT,
        shadow_exposed_via TEXT,
        shadow_rank INTEGER,
        shadow_explanation TEXT,
        same_winner INTEGER,
        candidates INTEGER,
        fetched INTEGER,
        acquisition_failed INTEGER,
        model_calls INTEGER,
        status TEXT
    )""" % RUNS_TABLE)
    conn.commit()


def record_comparison(conn, run_id: str, report: dict) -> None:
    """Persist one side-by-side result in the shadow's own table. Never news_seeds."""
    ensure_runs_schema(conn)
    old = report.get("old_authoritative_winner") or {}
    w = report.get("shadow_winner") or {}
    m = report.get("metrics", {})
    conn.execute(
        "INSERT OR REPLACE INTO %s VALUES (%s)" % (RUNS_TABLE, ",".join("?" * 21)),
        (run_id, report.get("run_at"), old.get("id"), old.get("title"),
         old.get("source_name"), old.get("relevance_score"),
         w.get("seed_id"), w.get("title"), w.get("source_name"), w.get("assessment"),
         w.get("material_richness"), w.get("researchability"), w.get("exposed_via"),
         w.get("shadow_rank"),
         json.dumps({k: w.get(k) for k in
                     ("concrete_subject", "investigable_question", "reason",
                      "theme_signal", "publisher_penalty", "publisher_penalty_detail",
                      "legacy_relevance_score", "legacy_disability_angle",
                      "body_words", "det_roundup", "det_promotional")},
                    ensure_ascii=False),
         1 if report.get("same_winner") else 0, m.get("candidates"), m.get("fetched"),
         m.get("acquisition_failed"), m.get("model_calls"),
         "OK" if w else "NO_SHADOW_WINNER"))
    conn.commit()


def cached_assessment(conn, seed_id: str, source_sha256: str):
    """Cache key is (seed_id, source_sha256): the same seed AND the same bytes. A source
    that materially changed hashes differently and is reassessed; a failed or invalid
    assessment is never cached as a judgment."""
    row = conn.execute(
        "SELECT * FROM %s WHERE seed_id = ? AND source_sha256 = ? "
        "AND assessment_status = ?" % TABLE, (seed_id, source_sha256, OK)).fetchone()
    return dict(row) if row else None


# ── exposure: three bounded deterministic streams ─────────────────────────────
# The disability booster's value inside the production scorer. Named here so the
# subtraction below is explicit rather than a magic number; a test asserts it still
# matches what score_item actually adds, so a change there fails loudly instead of
# silently skewing the shadow signal.
BOOSTER_CONTRIBUTION = 0.15


def theme_signal(title, summary, score_item, boosters, keyword_matches) -> float:
    """Legacy theme relevance MINUS the disability-booster contribution. Pure.

    Earlier this cleared the production booster list around a score_item() call and
    restored it in a finally block. That worked and was still wrong: a shadow that
    mutates production-global state, however briefly, is not observationally isolated,
    and a raise or a concurrent caller between the two lines would have been a real
    production bug caused by an experiment. So nothing is mutated. The production score
    is computed exactly as production computes it, and the booster is subtracted
    arithmetically.

    Exact, not approximate: score_item's base term is capped at 0.7 before the 0.15
    booster is added, so the sum can never reach the 1.0 clamp and the subtraction
    always recovers the unboosted value.

    Why subtract at all: the booster fires on ~2.5% of the eligible pool and moved one
    slot in a top-10 counterfactual, so it buys nothing -- and carrying a disability
    keyword advantage into the replacement's own ranking is precisely what the doctrine
    retired. The production scorer is not touched here or anywhere in this module.
    """
    item = {"title": title or "", "summary": summary or ""}
    score, _themes = score_item(item)
    text = ("%s %s" % (item["title"], item["summary"])).lower()
    words = set(re.findall(r"\b\w+\b", text))
    boosted = any(keyword_matches(text, words, kw) for kw in boosters)
    return round(max(0.0, score - (BOOSTER_CONTRIBUTION if boosted else 0.0)), 3)


def _remaining_eligibility_days(row, now) -> float:
    try:
        pub = datetime.strptime((row["pub_date"] or "")[:10], "%Y-%m-%d")
    except Exception:
        return 999.0
    return MP.eligibility_days(row["material_class"]) - (now - pub).days


def _explore_key(row, day: str) -> str:
    """Stable within a day, different across days, and free of model randomness."""
    return hashlib.sha256(("%s|%s" % (day, row["id"])).encode()).hexdigest()


def select_candidates(rows, *, now, score_item, boosters, keyword_matches,
                      already_assessed=frozenset()) -> list:
    """Union of three streams, deduplicated, ~12/day. Each candidate records which
    stream exposed it, so 'why was this even looked at?' is answerable afterwards."""
    pool = [r for r in rows if r["id"] not in already_assessed]
    day = now.strftime("%Y-%m-%d")
    signals = {r["id"]: theme_signal(r["title"], r["summary"], score_item, boosters,
                                     keyword_matches)
               for r in pool}
    picked, seen = [], set()

    def take(ordered, budget, via):
        n = 0
        for r in ordered:
            if n >= budget or len(picked) >= DAILY_CANDIDATES:
                break
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            picked.append({"row": r, "exposed_via": via, "theme_signal": signals[r["id"]]})
            n += 1

    # A: theme signal, booster excluded
    take(sorted(pool, key=lambda r: (-signals[r["id"]], r["pub_date"] or "")),
         STREAM_THEME, "theme")
    # B: about to age out -- a 3-day news item must not queue behind a 30-day essay
    take(sorted(pool, key=lambda r: (_remaining_eligibility_days(r, now),
                                     -signals[r["id"]])),
         STREAM_URGENCY, "urgency")
    # C: deterministic exploration, so low-vocabulary material has a real path in
    take(sorted(pool, key=lambda r: _explore_key(r, day)), STREAM_EXPLORE, "exploration")
    # unused budget falls back to the strongest theme signal
    take(sorted(pool, key=lambda r: (-signals[r["id"]], r["pub_date"] or "")),
         DAILY_CANDIDATES - len(picked), "theme_fill")
    return picked


def publisher_penalty(recent, publisher: str, now) -> tuple:
    """Soft, temporary, decaying. `recent` is [(publisher, iso_datetime)] of actual
    recent attempts/selections. A publisher chosen today is demoted most; the penalty
    decays linearly to zero across a week. No ban, no quota, and it never applies to a
    publisher because one of its stories was thin -- only because it was chosen."""
    worst = 0.0
    detail = ""
    for pub, when in recent:
        if pub != publisher or not when:
            continue
        try:
            days = (now - datetime.strptime(when[:10], "%Y-%m-%d")).days
        except Exception:
            continue
        if 0 <= days < PUBLISHER_PENALTY_DAYS:
            p = PUBLISHER_PENALTY_MAX * (1 - days / PUBLISHER_PENALTY_DAYS)
            if p > worst:
                worst, detail = p, "selected %dd ago" % days
    return round(worst, 3), detail


# ── cheap deterministic source features ───────────────────────────────────────
_ROUNDUP = re.compile(r"(?im)^\s*[^\n]{3,90}\s+by\s+[A-Z][\w'’-]+(\s+[A-Z][\w'’-]+)*\s*$")
_PROMO = ("partnership content", "press release", "for immediate release", "sponsored",
          "find out more about", "brand partnership")


def source_features(body: str) -> dict:
    """Features and warnings, NOT gates. The probe established correlation, not a safe
    rejection boundary -- a short anchor may still be one the Research Pack can expand,
    and the existing acquisition minimum is the only hard floor."""
    paras = [p for p in (body or "").split("\n") if p.strip()]
    low = (body or "").lower()
    return {"body_words": len((body or "").split()),
            "paragraph_count": len(paras),
            "det_roundup": len(_ROUNDUP.findall(body or "")) >= 3,
            "det_promotional": any(k in low for k in _PROMO)}


# ── material assessment ───────────────────────────────────────────────────────
ASSESSMENT_SYSTEM = (
    "You assess a source as MATERIAL FOR INVESTIGATION. You are not writing, pitching or "
    "deciding what anyone should argue, and you do not know what this publication is "
    "interested in.\n\n"
    "One question: is there enough concrete reality in this source to justify researching "
    "it? Concrete reality means named people, places, objects, works, institutions, dates, "
    "numbers, decisions, documents, mechanisms -- things a researcher can pull on. A source "
    "can be well written and still be thin: a roundup of unrelated items, a promotional "
    "blurb, a paragraph of comment on someone else's reporting.\n\n"
    "The investigable_question must be a question the SOURCE raises and does not settle -- "
    "\"the source establishes X and leaves Y open\". It must not be a conclusion waiting "
    "to be proved, and it must not contain a thesis about what the material means.\n\n"
    "Every concrete_subject and investigable_question comes from the body you are given, "
    "and both quotes must be copied CHARACTER-FOR-CHARACTER from it. They are checked "
    "programmatically and the assessment is discarded if they are not exact. Do not invent "
    "a finding, an argument, or a future article."
)

_SCHEMA = ('{"assessments": [{"id": "...", "concrete_subject": "...", '
           '"subject_anchor_quote": "verbatim from the body", "investigable_question": '
           '"...", "question_basis_quote": "verbatim from the body", "material_richness": '
           '"RICH|MODERATE|THIN", "researchability": "HIGH|MEDIUM|LOW", '
           '"narrative_material": "HIGH|MEDIUM|LOW", "source_shape": "SINGLE_SUBJECT|'
           'ROUNDUP|LIST|INTERVIEW|REPORT|PROMOTIONAL|OTHER", "specificity": '
           '"HIGH|MEDIUM|LOW", "assessment": "STRONG_CANDIDATE|POSSIBLE_CANDIDATE|'
           'WEAK_CANDIDATE", "reason": "one sentence, evidence-relative"}]}')


def assessment_prompt(batch: list) -> str:
    blocks = []
    for c in batch:
        body = " ".join((c["body"] or "").split()[:BODY_WORDS_TO_MODEL])
        f = c["features"]
        blocks.append("ID: %s\nTITLE: %s\nMATERIAL CLASS: %s\nSOURCE FEATURES: "
                      "%d words, %d paragraphs%s%s\n<<<BODY\n%s\nBODY>>>"
                      % (c["key"], c["row"]["title"], c["row"]["material_class"],
                         f["body_words"], f["paragraph_count"],
                         ", list/roundup shape" if f["det_roundup"] else "",
                         ", promotional markers" if f["det_promotional"] else "",
                         body))
    return "\n\n".join(blocks) + "\n\nReply with JSON only:\n" + _SCHEMA


def _norm(s):
    return " ".join((s or "").split()).lower()


def validate(a: dict, body: str) -> list:
    """Deterministic. Never repairs, never downgrades to WEAK -- an invalid assessment
    is invalid, not a judgment about the material."""
    errs = []
    hay = _norm(body)
    for field in ("subject_anchor_quote", "question_basis_quote"):
        q = _norm(a.get(field))
        if not q:
            errs.append("%s missing" % field)
        elif q not in hay:
            errs.append("%s not verbatim in the source body" % field)
    for field, allowed in (("material_richness", RICHNESS), ("researchability", LEVELS),
                           ("narrative_material", LEVELS), ("source_shape", SHAPES),
                           ("specificity", LEVELS), ("assessment", VERDICTS)):
        if a.get(field) not in allowed:
            errs.append("%s=%r not in %s" % (field, a.get(field), "/".join(allowed)))
    for field in ("concrete_subject", "investigable_question", "reason"):
        if not (a.get(field) or "").strip():
            errs.append("%s empty" % field)
    return errs


def assess(provider, candidates: list) -> tuple:
    """Batched, temperature 0. Returns (results_by_key, calls). A batch that fails as a
    whole marks its candidates ASSESSMENT_ERROR; nothing is inferred from silence."""
    results, calls = {}, 0
    batches, cur, size = [], [], 0
    for c in candidates:
        chars = len(c["body"] or "")
        if cur and (len(cur) >= BATCH_SIZE or size + chars > BATCH_MAX_CHARS):
            batches.append(cur); cur, size = [], 0
        cur.append(c); size += chars
    if cur:
        batches.append(cur)
    for batch in batches[:MAX_CALLS_PER_RUN]:
        calls += 1
        try:
            c = provider.complete(ASSESSMENT_SYSTEM, assessment_prompt(batch),
                                  max_tokens=BATCH_MAX_TOKENS, temperature=0)
            payload = parse_json_object(c.text)
            got = {a.get("id"): a for a in (payload.get("assessments") or [])}
        except Exception as e:
            for cand in batch:
                results[cand["key"]] = {"status": ASSESSMENT_ERROR,
                                        "errors": ["%s: %s" % (type(e).__name__, str(e)[:140])]}
            continue
        for cand in batch:
            a = got.get(cand["key"])
            if not a:
                results[cand["key"]] = {"status": ASSESSMENT_ERROR,
                                        "errors": ["no assessment returned for this id"]}
                continue
            errs = validate(a, cand["body"])
            results[cand["key"]] = dict(a, status=ASSESSMENT_INVALID if errs else OK,
                                        errors=errs)
    return results, calls


# ── ordering ──────────────────────────────────────────────────────────────────
_ORDER = {"assessment": {"STRONG_CANDIDATE": 0, "POSSIBLE_CANDIDATE": 1, "WEAK_CANDIDATE": 2},
          "material_richness": {"RICH": 0, "MODERATE": 1, "THIN": 2},
          "researchability": {"HIGH": 0, "MEDIUM": 1, "LOW": 2}}


def rank(records: list) -> list:
    """Transparent and arithmetic. The model classifies; the ordering is a readable sort
    over named fields, so any position can be explained without rerunning anything.
    Only assessments that actually validated can rank at all."""
    ok = [r for r in records if r["assessment_status"] == OK]
    ok.sort(key=lambda r: (
        _ORDER["assessment"].get(r["assessment"], 9),
        _ORDER["material_richness"].get(r["material_richness"], 9),
        _ORDER["researchability"].get(r["researchability"], 9),
        r["publisher_penalty"],                       # small, decaying, never a ban
        -(r["theme_signal"] or 0),                    # booster excluded
        # freshness as the final deterministic tie-break: later pub_date first
        [-ord(ch) for ch in (r["pub_date"] or "")],
    ))
    for i, r in enumerate(ok, 1):
        r["shadow_rank"] = i
    return ok + [r for r in records if r["assessment_status"] != OK]


# ── orchestration ─────────────────────────────────────────────────────────────
def eligible_pool(conn, now) -> list:
    """The PR #48 eligible pool, read-only, with the same attempt filters production
    uses. disability_angle and angle_checked are deliberately NOT consulted."""
    cut = MP.eligibility_cutoffs(now)
    args = tuple(cut[k] for k in (MP.CURRENT_NEWS, MP.ESSAY_OPINION, MP.RESEARCH_REPORT,
                                  MP.CULTURE, MP.EVERGREEN, MP.OTHER))
    conn.row_factory = sqlite3.Row
    return conn.execute("""
        SELECT * FROM news_seeds
        WHERE used = 0 AND ce_attempt_terminal IS NOT 1
          AND (ce_retry_after IS NULL OR ce_retry_after <= ?)
          AND pub_date >= CASE COALESCE(material_class,'OTHER')
                            WHEN 'CURRENT_NEWS' THEN ? WHEN 'ESSAY_OPINION' THEN ?
                            WHEN 'RESEARCH_REPORT' THEN ? WHEN 'CULTURE' THEN ?
                            WHEN 'EVERGREEN' THEN ? ELSE ? END
    """, (now.strftime("%Y-%m-%dT%H:%M:%S"), *args)).fetchall()


def recent_selections(conn, limit: int = 12) -> list:
    """Actual recent choices, for the publisher-repetition term. Attempts and uses only
    -- never Research Pack verdicts, which say nothing about a publisher."""
    rows = conn.execute(
        "SELECT source_name, COALESCE(ce_attempted_date, used_date) d FROM news_seeds "
        "WHERE COALESCE(ce_attempted_date, used_date) IS NOT NULL "
        "ORDER BY d DESC LIMIT ?", (limit,)).fetchall()
    return [(r[0], r[1]) for r in rows]


def run_shadow(conn, provider, *, acquire, score_item, boosters, keyword_matches,
               now=None, old_winner=None) -> dict:
    """One shadow run. `acquire(url) -> (text, status)` MUST be the production
    acquisition path -- a second, weaker fetcher would mark whole publishers unreadable
    (the probe's stdlib fetch got HTTP 403 from Dezeen, NYT Arts and the Economist while
    production retrieves them).

    Writes its own table and returns its own report. Nothing here can change which seed
    CURRENT_ENGINE receives.
    """
    now = now or datetime.now()
    ensure_schema(conn)
    pool = eligible_pool(conn, now)
    recent = recent_selections(conn)
    candidates = select_candidates(pool, now=now, score_item=score_item,
                                   boosters=boosters, keyword_matches=keyword_matches)

    prepared, cached, failed = [], [], []
    for c in candidates:
        row = c["row"]
        text, status = acquire(row["url"])
        if status != "USABLE" or not text:
            failed.append({"seed_id": row["id"], "source_name": row["source_name"],
                           "url": row["url"], "assessment_status": ACQUISITION_FAILED,
                           "detail": status, "exposed_via": c["exposed_via"]})
            continue
        # Hash of the FULL acquired source, before any truncation for the model
        # prompt. If the source changes past the 1,100 words the assessor sees, the
        # cache must still know the source changed.
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        c.update(body=text, sha=sha, features=source_features(text),
                 key=row["id"][:8])
        hit = cached_assessment(conn, row["id"], sha)
        (cached if hit else prepared).append(c)
        if hit:
            c["cached"] = hit
    results, calls = assess(provider, prepared) if prepared else ({}, 0)

    records = []
    for c in cached + prepared:
        row = c["row"]
        a = c.get("cached") or results.get(c["key"], {"status": ASSESSMENT_ERROR,
                                                      "errors": ["no result"]})
        pen, pen_detail = publisher_penalty(recent, row["source_name"], now)
        rec = {"seed_id": row["id"], "source_url": row["url"],
               "source_name": row["source_name"], "title": row["title"],
               "material_class": row["material_class"], "pub_date": row["pub_date"],
               "source_sha256": c["sha"], "assessed_at": now.strftime("%Y-%m-%dT%H:%M:%S"),
               "assessment_status": a.get("status") or a.get("assessment_status"),
               "exposed_via": c["exposed_via"], "theme_signal": c["theme_signal"],
               "publisher_penalty": pen, "publisher_penalty_detail": pen_detail,
               "legacy_relevance_score": row["relevance_score"],
               "legacy_disability_angle": bool(row["disability_angle"]),
               "cached": bool(c.get("cached")),
               "errors": json.dumps(a.get("errors") or [])}
        rec.update({k: a.get(k) for k in
                    ("concrete_subject", "subject_anchor_quote", "investigable_question",
                     "question_basis_quote", "material_richness", "researchability",
                     "narrative_material", "source_shape", "specificity", "assessment",
                     "reason")})
        rec.update(c["features"])
        records.append(rec)

    ranked = rank(records)
    for rec in ranked:
        conn.execute(
            "INSERT OR REPLACE INTO %s (seed_id, source_url, source_sha256, assessed_at,"
            " assessment_status, concrete_subject, subject_anchor_quote,"
            " investigable_question, question_basis_quote, material_richness,"
            " researchability, narrative_material, source_shape, specificity, assessment,"
            " reason, body_words, paragraph_count, det_roundup, det_promotional,"
            " exposed_via, theme_signal, publisher_penalty, shadow_rank, errors)"
            " VALUES (%s)" % (TABLE, ",".join("?" * 25)),
            (rec["seed_id"], rec["source_url"], rec["source_sha256"], rec["assessed_at"],
             rec["assessment_status"], rec.get("concrete_subject"),
             rec.get("subject_anchor_quote"), rec.get("investigable_question"),
             rec.get("question_basis_quote"), rec.get("material_richness"),
             rec.get("researchability"), rec.get("narrative_material"),
             rec.get("source_shape"), rec.get("specificity"), rec.get("assessment"),
             rec.get("reason"), rec["body_words"], rec["paragraph_count"],
             int(rec["det_roundup"]), int(rec["det_promotional"]), rec["exposed_via"],
             rec["theme_signal"], rec["publisher_penalty"], rec.get("shadow_rank"),
             rec["errors"]))
    conn.commit()

    winner = next((r for r in ranked if r["assessment_status"] == OK), None)
    return {
        "shadow": True,
        "authority": "NONE -- comparison only; cannot change the anchor CURRENT_ENGINE "
                     "receives, and invokes no Research Pack, Discovery, Form or Writer",
        "run_at": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "eligible_pool": len(pool),
        "candidates": [{"seed_id": c["row"]["id"], "exposed_via": c["exposed_via"],
                        "source_name": c["row"]["source_name"]} for c in candidates],
        "acquisition_failures": failed,
        "records": ranked,
        "old_authoritative_winner": old_winner,
        "shadow_winner": winner,
        "same_winner": bool(old_winner and winner
                            and old_winner.get("id") == winner["seed_id"]),
        "metrics": {"candidates": len(candidates), "fetched": len(cached) + len(prepared),
                    "cached": len(cached), "assessed": len(prepared),
                    "acquisition_failed": len(failed), "model_calls": calls,
                    "valid": sum(1 for r in records if r["assessment_status"] == OK),
                    "invalid": sum(1 for r in records
                                   if r["assessment_status"] == ASSESSMENT_INVALID),
                    "errored": sum(1 for r in records
                                   if r["assessment_status"] == ASSESSMENT_ERROR),
                    "exposed_via": dict(collections.Counter(
                        c["exposed_via"] for c in candidates))},
    }
