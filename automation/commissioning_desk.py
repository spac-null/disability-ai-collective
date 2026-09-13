#!/usr/bin/env python3
"""commissioning_desk.py -- what the 09:00 run does BEFORE the pipeline runs.

WHAT THE 2026-09-13 RUN ACTUALLY EXPOSED. Candidate: The Verge, "Schools are catching on
to Big Tech's playbook". Research PASS, NARROW, six retained sources. Ledger PASS, 92
facts. Worth: GREAT_GENERAL_STORY_WRONG_PUBLICATION. Production stopped, correctly.

Nothing downstream failed. Two things upstream did, and they are separate problems:

  1. THE WRONG KIND OF PITCH. The selector optimises for whether a story is WRITEABLE --
     concrete subject, narrative material, source shape, specificity, richness,
     researchability, freshness. Every one of those readings was right. None of them is
     the question "has disability already taught, invented, noticed or made visible
     something about this?", and nothing asked that before a full Research pass and a
     92-fact Ledger had been spent discovering the answer was no.

  2. ONE PITCH WAS THE WHOLE DAY. Candidate A held at Worth and the day ended. A
     publication that can only make one commissioning guess per morning publishes
     whatever its first guess happens to be, or nothing.

This module owns both, and nothing else. It does not compose, does not judge prose, and
does not touch a single gate. Everything from architect() onward is exactly as it was.

    THE DESK                          UNCHANGED, BELOW THE LINE
    ────────────────────────────      ─────────────────────────────────────────
    lane plan: KF, KF, ORDINARY       Research -> Ledger -> Worth -> architect()
    commission or select              -> writer_packet -> Fast Lane Writer
    light Crip Minds screen           -> Writer -> Continuity -> Prose Finish
    (ordinary lane only)              -> Claim Mapper -> editorial_package
    up to 3 DISTINCT candidates       -> Safety -> Grounding -> Fact Check -> Reader
    attempt provenance                -> publication bridge -> images -> social -> NL

KNOWLEDGE FIRST IS THE DEFAULT, NOT THE EXCEPTION. Two of the three slots are the lane
that starts from an approved intellectual question and seeks a story for it, rather than
taking whatever general news arrived at 06:05 and looking for a reading of it. The
ordinary-world lane keeps the third slot and keeps Selector V2's real strengths; it just
stops being the entire commissioning intelligence.

THE RETRY BOUNDARY IS THE ONE RULE THAT MATTERS MOST HERE. A candidate may be replaced
only while the publication has not yet committed to it -- that is, while the rejection is
a COMMISSIONING answer: research could not find enough, the Ledger could not grant
permission, or Worth said this is not our story. The moment Worth PASSES and architect()
begins, the day is committed to that candidate. A hold at Architecture, Writer, Claim
Mapper, Safety, Grounding, Fact Check or Reader ENDS THE DAY. Trying another story
because a late gate objected is gate shopping: it would let a run keep drawing candidates
until one slipped past the gates that exist to catch exactly that, and it would quietly
convert every quality gate into a suggestion. Publishing nothing is a correct outcome and
this module is willing to reach it.

And a candidate is never reconsidered. Worth is not deterministic; re-running the same
seed hoping for a different verdict is the same gate shopping wearing a different hat.
Each attempt's verdict is retained and the seed is spent.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import sqlite3
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import crip_minds_screen as SCREEN                          # noqa: E402
import knowledge_first as KF                                # noqa: E402
import news_fetcher as NF                                   # noqa: E402
import selector_v2 as SV                                    # noqa: E402
from new_engine_v1 import composition as CP                 # noqa: E402
from new_engine_v1 import research as RS                    # noqa: E402
from new_engine_v1.provider import Provider                 # noqa: E402

DESK_ENV = "CRIPMINDS_COMMISSIONING_DESK"

# THE LANE PLAN. Knowledge first, twice, then ordinary world. Not a ratio to tune: it is
# the editorial statement that this publication commissions from its own questions and
# falls back to the news, rather than the other way round.
LANE_PLAN = (KF.LANE, KF.LANE, KF.LANE_SECONDARY)
MAX_DISTINCT_CANDIDATES = 3

# A question is not re-commissioned inside this window. Long enough that the desk does not
# circle a handful of questions, short enough that the pool cannot run dry -- which, with
# 16 approved questions, permanent claims and two knowledge-first slots a day, it otherwise
# does within the week. See knowledge_first.load_claimed_question_ids.
QUESTION_COOLDOWN_DAYS = 21

# ══════════════════════════════════════════════════════════════════════════════
# WHERE A REJECTION HAPPENED, AND THEREFORE WHETHER ANOTHER PITCH MAY BE DRAWN
# ══════════════════════════════════════════════════════════════════════════════
# Everything in this set is a rejection of the PITCH, decided before the publication has
# committed to composing it. Everything NOT in it -- every later gate, and every technical
# failure -- ends the day.
#
# Listed explicitly rather than derived from stage order, because the rule is editorial,
# not structural: a future stage inserted between Worth and architect() must be a
# deliberate decision to add here, never something that silently inherits retry rights.
PRE_COMPOSITION_REJECTIONS = frozenset({
    RS.HOLD,              # research could not find enough to write from
    CP.LEDGER_HOLD,       # the facts could not be granted
    CP.WORTH_HOLD,        # a real story; not this publication's
})

# Terminal reasons the desk itself produces, before any run starts.
SCREEN_REJECTED = "SCREEN_REJECTED"
NO_CANDIDATE = "NO_CANDIDATE"
COMMISSION_REFUSED = "COMMISSION_REFUSED"


def desk_enabled(env=None) -> bool:
    """On by default. `CRIPMINDS_COMMISSIONING_DESK=0` on the cron line restores the exact
    previous behaviour -- one ordinary-world candidate, no screen, no retry -- the same
    rollback shape CRIPMINDS_SELECTOR=legacy already has."""
    v = (env if env is not None else os.environ).get(DESK_ENV, "").strip().lower()
    return v not in ("0", "off", "false", "no")


def is_pre_composition_rejection(result: dict) -> bool:
    """True when the day may draw a DIFFERENT pitch.

    Deliberately narrow and fail-closed: an ACCEPT is not a rejection, a technical failure
    is not an editorial answer about a story, and anything whose reason code this does not
    recognise is treated as a commitment already made. Unrecognised means STOP.
    """
    if (result or {}).get("decision") == "ACCEPT":
        return False
    if (result or {}).get("run_status"):
        # PROVIDER_FAILURE / CONTRACT_FAILURE. The pitch was never judged; the
        # infrastructure was. Drawing another candidate would burn the day's remaining
        # slots on the same outage and report it as editorial scarcity.
        return False
    return (result or {}).get("reason_code") in PRE_COMPOSITION_REJECTIONS


# ══════════════════════════════════════════════════════════════════════════════
# LANE: KNOWLEDGE FIRST
# ══════════════════════════════════════════════════════════════════════════════
def commission_knowledge_first(orch, model: str, evidence_root, *,
                               exclude_question_ids=None) -> tuple:
    """(seed | None, record). The approved-question lane, with a per-day exclusion so two
    knowledge-first slots in one morning cannot land on the same question."""
    from new_engine_v1.research import search_urls
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("kf-%Y%m%dT%H%M%SZ")
    conn = sqlite3.connect(str(orch.discovery_db))
    try:
        rec = KF.commission(Provider(model=model), search_fn=search_urls,
                            fetch_fn=lambda u: orch.get_source_text(u) or "",
                            api_key=KF.search_key(), state_conn=conn, run_id=run_id,
                            evidence_root=evidence_root,
                            exclude=set(exclude_question_ids or ()),
                            question_cooldown_days=QUESTION_COOLDOWN_DAYS)
    finally:
        conn.close()
    q = rec.get("question") or {}
    orch.logger.info("DESK/KNOWLEDGE_FIRST %s: question=%s (%s) -> %s",
                     rec.get("status"), q.get("id"), q.get("title"),
                     (rec.get("chosen") or {}).get("subject", "no story")[:110])
    return rec.get("seed"), rec


# ══════════════════════════════════════════════════════════════════════════════
# LANE: ORDINARY WORLD COLLISION
# ══════════════════════════════════════════════════════════════════════════════
def select_ordinary_world(orch, model: str, *, exclude_seed_ids=None) -> tuple:
    """(seed | None, selection_report | None). Selector V2, unchanged in what it measures.

    Two filters are new and neither touches its ranking: origin-ineligible publishers are
    removed from the pool (news_fetcher.SECONDARY_ONLY_ORIGIN), and seeds this day has
    already spent are removed. What V2 is good at -- richness, specificity, source quality,
    researchability -- is exactly what it still does, over a pool that no longer offers it
    stories this publication was never going to commission.
    """
    import new_engine_production as NEP
    conn = sqlite3.connect(str(orch.discovery_db))
    try:
        report = SV.run_selection(
            conn, Provider(model=model), acquire=NEP._acquire_for_selector(orch),
            score_item=NF.score_item, boosters=NF.DISABILITY_BOOSTERS,
            keyword_matches=NF._keyword_matches, old_winner=None,
            secondary_only=NF.SECONDARY_ONLY_ORIGIN,
            exclude_seed_ids=set(exclude_seed_ids or ()))
    except Exception as e:
        raise SV.SelectorFailure("%s: %s" % (type(e).__name__, str(e)[:300])) from e
    finally:
        conn.close()
    winner = report.get("shadow_winner")
    m = report["metrics"]
    if not winner:
        if m["fetched"] > 0:
            # Acquired material and could not judge any of it: an outage, not a quiet day.
            raise SV.SelectorFailure(
                "acquired %d source(s) and produced no valid assessment "
                "(invalid=%d errored=%d): the pool could not be judged"
                % (m["fetched"], m["invalid"], m["errored"]))
        return None, report
    seed = NEP._seed_dict(orch, winner["seed_id"])
    if seed is None:
        raise SV.SelectorFailure("selected seed %s vanished from news_seeds"
                                 % winner["seed_id"])
    return seed, report


def screen_ordinary_world(orch, seed: dict, model: str) -> dict:
    """The light Crip Minds potential screen. Hypothesis generation ONLY.

    The source text it reads has already been acquired by the selector -- `get_source_text`
    memoises per url -- so this costs one bounded model call and no network.

    IT GRANTS NOTHING. Its output is recorded as commissioning provenance and is never
    passed to the Writer, never merged into a pack, and never treated as established. The
    question it names is a question; Research decides whether it is true, the Ledger
    decides what may be asserted, and Worth still decides whether the article was earned.
    """
    text = orch.get_source_text(seed["url"], fallback_text=seed.get("summary"),
                                underlying_url=seed.get("underlying_article_url")) or ""
    rec = SCREEN.screen(Provider(model=model), title=seed.get("title") or "",
                        summary=seed.get("summary") or "",
                        source_name=seed.get("source_name") or "",
                        source_text=text)
    orch.logger.info(
        "DESK/SCREEN %s: %s | carrier=%s | access_origin=%s | %s",
        (seed.get("title") or "")[:60], rec["verdict"], (rec["carrier"] or "none")[:60],
        rec["access_origin"], (rec["reject_reason"] or rec["question"] or "")[:120])
    return rec


# ══════════════════════════════════════════════════════════════════════════════
# ATTEMPT PROVENANCE
# ══════════════════════════════════════════════════════════════════════════════
def record_screen_rejection(orch, seed: dict, screen: dict, run: str) -> None:
    """Tell the seed pool that the commissioning screen refused this candidate.

    WHY THIS EXISTS. Measured on the 2026-09-13 three-day sample: the ordinary-world slot
    proposed the SAME candidate on all three days. Within a day the desk excludes a spent
    seed, but that set is per-day, and a screen rejection never reached the pool at all --
    the write-back lives in run_scheduled, which a screen-rejected candidate never gets to.
    So the selector re-ranked the identical pool each morning, picked the identical winner,
    and paid for the identical screen call to reach the identical refusal. A rejected pitch
    that comes back tomorrow is the reconsideration the desk's own doctrine forbids.

    RESTED, NOT RETIRED, and deliberately so. `classify_current_engine_attempt` states the
    rule this follows: a named code not yet proven deterministic is rested rather than
    retired, because "wrongly retrying a seed costs one run; wrongly consuming one loses a
    story permanently". The screen is ONE cheap model call and much weaker evidence than
    Worth; retiring a story forever on it would be exactly the over-consumption that
    classifier was written to prevent. The cooldown is enough to stop the daily repeat,
    which is the actual defect.

    Never allowed to affect the day: a pool write-back failure is logged, not raised.
    """
    try:
        klass = getattr(orch, "CE_REVIEWABLE", "NONDETERMINISTIC_OR_REVIEWABLE_HOLD")
        orch.mark_news_seed_current_engine_attempt(
            seed["id"], run=run, klass=klass,
            outcome="%s:%s:%s" % (klass, SCREEN_REJECTED,
                                  screen.get("reject_reason") or "unspecified"))
    except Exception as e:                                    # never reaches the caller
        orch.logger.warning("DESK: screen-rejection write-back failed on seed %s "
                            "(ignored): %s: %s", seed.get("id"), type(e).__name__,
                            str(e)[:200])


def _attempt_record(n: int, lane: str, seed, commission, screen, result, terminal) -> dict:
    """One pitch, whatever became of it. NO DISAPPEARING REJECTED PITCHES: a candidate the
    desk refused before Research leaves exactly as much record as one that reached Worth.

    Diagnostic only, and written into the existing run-artifact tree rather than a new
    table -- the brief's instruction, and the right call: a rejected pitch is evidence
    about one morning, not production state that anything reads back.
    """
    q = (commission or {}).get("question") or {}
    chosen = (commission or {}).get("chosen") or {}
    return {
        "attempt": n,
        "lane": lane,
        "seed_id": (seed or {}).get("id"),
        "source": (seed or {}).get("source_name"),
        "url": (seed or {}).get("url"),
        "subject": (seed or {}).get("title"),
        "question_id": q.get("id"),
        "question": q.get("question"),
        "commission_status": (commission or {}).get("status"),
        "carrier": (screen or {}).get("carrier") or chosen.get("carrier"),
        "crip_minds_question": (screen or {}).get("question") or q.get("question"),
        "perspective_or_axis": (screen or {}).get("perspective_or_axis"),
        "why_this_might_matter": ((screen or {}).get("why_this_might_matter")
                                  or chosen.get("tests_the_question")),
        "access_origin": (screen or {}).get("access_origin"),
        "screen_verdict": (screen or {}).get("verdict"),
        "screen_reject_reason": (screen or {}).get("reject_reason"),
        "research_status": _research_status(result),
        "ledger_status": _stage_status(result, CP.LEDGER),
        "worth_verdict": _stage_status(result, CP.WORTH),
        "decision": (result or {}).get("decision"),
        "reason_code": (result or {}).get("reason_code"),
        "engine_run": (result or {}).get("engine_run"),
        "evidence": (result or {}).get("evidence"),
        "terminal_reason": terminal,
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def _research_status(result) -> str:
    """PASS is only claimed when the run demonstrably got past Research.

    Inferring it from "decision is set and the reason code is not research's" would
    report PASS for a run that never reached Research at all -- a selector failure, a
    stubbed pipeline -- which is the record quietly asserting something it does not know.
    Reaching the composition ladder is the observable that actually means it.
    """
    if not result:
        return ""
    if result.get("reason_code") == RS.HOLD:
        return RS.HOLD
    if ((result.get("composition") or {}).get("stages")):
        return "PASS"
    return ""


def _stage_status(result, stage: str) -> str:
    """The stage's own recorded outcome, when the run reached the composition ladder."""
    stages = ((result or {}).get("composition") or {}).get("stages") or {}
    return str(stages.get(stage) or "")


def _persist_day(evidence_root, day: dict) -> pathlib.Path | None:
    try:
        root = pathlib.Path(evidence_root)
        d = root / ("commissioning-%s" % day["day_id"])
        d.mkdir(parents=True, exist_ok=True)
        p = d / "COMMISSIONING_DAY.json"
        p.write_text(json.dumps(day, indent=2, sort_keys=True, default=str),
                     encoding="utf-8")
        return p
    except Exception:
        # Provenance must never be able to change an outcome that is already decided.
        return None


# ══════════════════════════════════════════════════════════════════════════════
# THE DAY
# ══════════════════════════════════════════════════════════════════════════════
def run_day(orch, *, rehearsal: bool = False, evidence_root=None,
            model: str, research_fn=None, plan=LANE_PLAN) -> dict:
    """One morning. At most MAX_DISTINCT_CANDIDATES distinct pitches; exactly one article.

    Returns the DECIDING attempt's own result -- the same dict shape run_scheduled has
    always returned -- with the day's record attached, so production_orchestrator's
    infrastructure-failure classifier and every existing caller are unchanged.
    """
    import new_engine_production as NEP
    root = pathlib.Path(evidence_root or NEP.DEFAULT_EVIDENCE_ROOT)
    day_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    attempts: list = []
    spent_seed_ids: set = set()
    used_question_ids: set = set()
    last: dict | None = None

    for n, lane in enumerate(plan[:MAX_DISTINCT_CANDIDATES], 1):
        seed = commission = screen = selection = None
        terminal = ""

        # ── draw a pitch ────────────────────────────────────────────────────
        if lane == KF.LANE:
            seed, commission = commission_knowledge_first(
                orch, model, root, exclude_question_ids=used_question_ids)
            qid = ((commission or {}).get("question") or {}).get("id")
            if qid:
                used_question_ids.add(qid)
            if not seed:
                if commission.get("technical_failure"):
                    # Not scarcity. An operator is told, and the day stops rather than
                    # spending its remaining slots on the same broken provider.
                    attempts.append(_attempt_record(n, lane, seed, commission, screen,
                                                    None, commission["status"]))
                    return _finish(orch, root, day_id, attempts, {
                        "status": "hold", "engine": "new_engine_v1", "decision": "HOLD",
                        "lane": lane, "commit_success": False,
                        "reason_code": commission.get("status"),
                        "reasons": ["knowledge-first commissioning failed technically: %s"
                                    % commission.get("error")],
                        "run_status": commission["run_status"]})
                attempts.append(_attempt_record(n, lane, seed, commission, screen, None,
                                                COMMISSION_REFUSED))
                continue
        else:
            try:
                seed, selection = select_ordinary_world(
                    orch, model, exclude_seed_ids=spent_seed_ids)
            except (SV.SelectorFailure, SV.UnknownSelector) as e:
                orch.logger.error("DESK selector failed, day held: %s: %s",
                                  type(e).__name__, e)
                attempts.append(_attempt_record(n, lane, None, None, None, None,
                                                "SELECTOR_FAILURE"))
                return _finish(orch, root, day_id, attempts, {
                    "status": "hold", "engine": "new_engine_v1", "decision": "HOLD",
                    "lane": lane, "commit_success": False,
                    "reasons": ["selector failure: %s" % e],
                    "reason_code": "SELECTOR_FAILURE",
                    "run_status": {"status": "PROVIDER_FAILURE", "stage": "SELECTOR",
                                   "detail": str(e)[:300]}})
            if not seed:
                attempts.append(_attempt_record(n, lane, None, None, None, None,
                                                NO_CANDIDATE))
                continue
            spent_seed_ids.add(seed["id"])

            # ── the light screen, ordinary lane only ────────────────────────
            # Knowledge-first candidates are not screened: they were commissioned FROM an
            # approved question and already carry one, with their own access-deficit
            # self-check. Screening them would ask a question already answered and charge
            # a model call for it.
            if SCREEN.screen_enabled():
                screen = screen_ordinary_world(orch, seed, model)
                if screen.get("technical_failure"):
                    attempts.append(_attempt_record(n, lane, seed, None, screen, None,
                                                    SCREEN.SCREEN_UNAVAILABLE))
                    return _finish(orch, root, day_id, attempts, {
                        "status": "hold", "engine": "new_engine_v1", "decision": "HOLD",
                        "lane": lane, "commit_success": False,
                        "reason_code": SCREEN.SCREEN_UNAVAILABLE,
                        "reasons": ["commissioning screen failed technically: %s"
                                    % screen.get("error")],
                        "run_status": {"status": "PROVIDER_FAILURE",
                                       "stage": "COMMISSIONING_SCREEN",
                                       "detail": str(screen.get("error"))[:300]}})
                if screen["verdict"] == SCREEN.REJECT:
                    # REJECTED BEFORE RESEARCH. This is the saving: no targeted research
                    # pass, no Ledger, no Worth call spent on a story this publication was
                    # never going to commission.
                    #
                    # The refusal is written back to the pool so tomorrow does not
                    # rediscover it -- see record_screen_rejection.
                    record_screen_rejection(orch, seed, screen, day_id)
                    attempts.append(_attempt_record(n, lane, seed, None, screen, None,
                                                    SCREEN_REJECTED))
                    continue

        # ── run it: the pipeline, entirely unchanged ────────────────────────
        orch.logger.info("DESK attempt %d/%d lane=%s -> %s (%s)", n,
                         min(len(plan), MAX_DISTINCT_CANDIDATES), lane,
                         (seed.get("title") or "")[:70], seed.get("source_name"))
        last = NEP.run_scheduled(orch, rehearsal=rehearsal, evidence_root=str(root),
                                 model=model, research_fn=research_fn, lane=lane,
                                 seed=seed, selection=selection, commission=commission,
                                 screen=screen)
        if seed.get("id"):
            spent_seed_ids.add(seed["id"])

        if last.get("decision") == "ACCEPT":
            terminal = "ACCEPT"
        elif is_pre_composition_rejection(last):
            terminal = last.get("reason_code")
        else:
            terminal = "COMMITTED_%s" % (last.get("reason_code") or "HOLD")
        attempts.append(_attempt_record(n, lane, seed, commission, screen, last, terminal))

        if not is_pre_composition_rejection(last):
            # ACCEPT, a post-Worth hold, or a technical failure. Either the day has its
            # article or the day is over. No further candidate is drawn.
            if last.get("decision") != "ACCEPT":
                orch.logger.warning(
                    "DESK: attempt %d held at %s -- the publication had already committed "
                    "to this candidate; the day ends here rather than selecting another "
                    "article", n, last.get("reason_code") or "an unnamed stage")
            return _finish(orch, root, day_id, attempts, last)

        orch.logger.info("DESK: attempt %d rejected at %s -- drawing a distinct candidate",
                         n, last.get("reason_code"))

    # Every slot used, nothing commissioned. A correct outcome.
    orch.logger.info("DESK: %d pitch(es) considered, none earned an article -- the day "
                     "ends with no publication", len(attempts))
    return _finish(orch, root, day_id, attempts, last or {
        "status": "no_usable_source", "engine": "new_engine_v1",
        "message": "no pitch reached composition; %d candidate(s) considered"
                   % len(attempts)})


def _finish(orch, root, day_id: str, attempts: list, result: dict) -> dict:
    day = {
        "day_id": day_id,
        "lane_plan": list(LANE_PLAN),
        "max_distinct_candidates": MAX_DISTINCT_CANDIDATES,
        "candidates_considered": len(attempts),
        "attempts": attempts,
        "outcome": result.get("decision") or result.get("status"),
        "published": result.get("published"),
        "deciding_attempt": len(attempts) or None,
    }
    path = _persist_day(root, day)
    out = dict(result)
    out["commissioning_day"] = day
    if path:
        out["commissioning_record"] = str(path)
    for a in attempts:
        orch.logger.info("DESK attempt %s | %s | %s | %s | %s", a["attempt"], a["lane"],
                         (a["source"] or a["question_id"] or "?"),
                         (a["subject"] or "")[:60], a["terminal_reason"])
    return out
