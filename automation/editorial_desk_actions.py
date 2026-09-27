"""The desk's state machine. Every write the editorial desk performs lives here.

Separated from the Telegram adapter on purpose: sending is injected, so the whole
lifecycle -- deliver, read, react, rewrite, approve, publish -- is exercisable offline
with no bot, no token and no network. The adapter above it does Telegram and nothing
else.

WHERE AUTHORITY LIVES, since this is the file that could quietly take some:

  visibility      here, and unconditional. A coherent article is delivered.
  editorial voice the owner's, expressed as reactions this file records verbatim.
  factual verdict NOT here. Quoted from the run's artifacts, never formed.
  publication     NOT here. publish_retained_fast_lane and the publication-safety
                  bridge decide; this file may only refuse further, never permit.

Four guards stand between a button press and a published article, and all four must
pass: the presser is on the allowlist, an explicit OWNER_APPROVED decision exists for
these exact bytes, the retained run still holds those exact bytes, and the existing
publisher independently grants eligibility at the moment of publication. No historical
preference, no learned profile and no model verdict can substitute for any of them.
"""
from __future__ import annotations

import os
import pathlib

import editorial_desk as DESK
import editorial_desk_store as STORE

ALLOWED_USERS_ENV = "CRIPMINDS_DESK_ALLOWED_USERS"

VERSION_ORIGIN = "v0"


def allowed_users(env: dict | None = None) -> set:
    """The allowlist, from configuration. Empty means nobody -- fail closed.

    A desk that publishes must not treat an unset variable as "allow everyone", and
    must not carry a hardcoded identifier in a public repository.
    """
    raw = (env if env is not None else os.environ).get(ALLOWED_USERS_ENV, "") or ""
    out = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part:
            out.add(part)
    return out


def authorized(user_id, env: dict | None = None) -> bool:
    return str(user_id) in allowed_users(env)


def actor_of(user_id) -> str:
    return "owner:%s" % user_id


# ── delivery ────────────────────────────────────────────────────────────────────────

def deliver(run: dict, *, chat_id, root=None) -> dict:
    """Open (or find) the session for a run and record that it was offered.

    Idempotent on (run_id, article bytes). A Telegram send that timed out after the
    message actually landed must not, on the next scan, deliver the same article twice.
    Returns the session row plus `created`, so the caller knows whether to send.
    """
    if run["state"] != DESK.REVIEWABLE_DRAFT:
        raise ValueError("only a REVIEWABLE_DRAFT is delivered for reading")
    sha = STORE.sha256_text(run["article_text"])
    row, created = STORE.ensure_session(
        run_id=run["run_id"], version_sha=sha, state=run["state"],
        publish_state=run["publish_state"], root=root)
    sid = row["session_id"]
    STORE.record_version(
        session=sid, run_id=run["run_id"], text=run["article_text"],
        version_id=VERSION_ORIGIN, reason=STORE.REASON_RETAINED_RUN,
        gate_status=run["gates"], root=root)
    STORE.record_event(
        session=sid, run_id=run["run_id"], event_type="DESK_DELIVERED",
        actor="system", version_sha=sha, version_id=VERSION_ORIGIN,
        chat_id=chat_id, dedupe_key="delivered:%s" % sid,
        metadata={"publish_state": run["publish_state"],
                  "publish_reason": run["publish_reason"],
                  "words": run["words"]},
        root=root)
    return {"session": row, "created": created, "version_sha256": sha,
            "session_id": sid}


def record_block_sent(*, session_id: str, run_id: str, version_sha: str, block: dict,
                      chat_id, message_id, root=None) -> dict:
    return STORE.record_block(
        session=session_id, version_sha=version_sha, block_id=block["block_id"],
        index=block["index"], total=block["of"],
        paragraph_start=block["paragraph_start"], paragraph_end=block["paragraph_end"],
        text=block["text"], chat_id=chat_id, message_id=message_id, root=root)


# ── one state, and it belongs to a VERSION ──────────────────────────────────────────
#
# Not to an article and not loosely to a session. On 2026-09-27 /today reported
# "Nothing new. You are part-way through Ten-minute acts" while an unread article sat
# on the desk, because four different notions -- undelivered, newly delivered, active
# session, reading session -- each answered a different question and none answered the
# reader's. There is now one question ("what is the state of THIS version?") and one
# place that answers it.

UNREAD = "UNREAD"
READING = "READING"
FINISHED = "FINISHED"
HELD = "HELD"

# The order the inbox lists them in: what is waiting, then what was left open, then
# what is done, then what was set aside.
STATE_ORDER = (UNREAD, READING, FINISHED, HELD)


def blocks_total(version_sha: str, root=None) -> int:
    text = STORE.read_version_bytes(version_sha, root)
    return len(DESK.split_blocks(text)) if text else 0


def blocks_read(session_id: str, version_sha: str, root=None) -> int:
    """How far the reader got: the index of the block most recently SENT, because Back
    re-sends one already seen and counting rows would read that as progress."""
    rows = STORE.session_blocks(session_id, version_sha, root)
    if not rows:
        return 0
    return sorted(rows, key=lambda b: b.get("sent_at", ""))[-1].get("index", 0)


def version_state(session_id: str, version_sha: str, root=None) -> dict:
    """UNREAD / READING n/m / FINISHED / HELD for exactly these bytes."""
    evs = [e for e in STORE.session_events(session_id, root)
           if not e.get("version_sha256") or e["version_sha256"] == version_sha]
    kinds = {e["event_type"] for e in evs}
    at, total = blocks_read(session_id, version_sha, root), blocks_total(version_sha, root)
    if "HOLD" in kinds:
        status = HELD
    elif "ARTICLE_FINISHED" in kinds:
        status = FINISHED
    elif at:
        status = READING
    else:
        status = UNREAD
    return {"status": status, "at": at, "of": total,
            "label": ("READING %d/%d" % (at, total)) if status == READING else status}


# Human labels for the feedback summary. Derived from the same tables the buttons are
# built from, so a new button cannot appear in the desk and be missing from a summary.
# Buttons whose human label is not a mechanical de-underscoring of their code.
LABEL_OVERRIDES = {"SOUNDS_LIKE_REPORT": "Sounds like a report",
                   "READER_LOST": "I am lost",
                   "WHY_NOW": "Why now?"}


def _labels() -> dict:
    out = {a: LABEL_OVERRIDES.get(a, a.replace("_", " ").capitalize())
           for a in DESK.BUTTON_SIGNALS}
    for opts in DESK.DETAIL_OPTIONS.values():
        for label, code in opts:
            out[code] = label
    return out


def feedback_summary(session_id: str, version_sha: str, root=None) -> list:
    """[(label, count)] for one version, most-pressed first. A detail press is counted
    under its own name, not under the action it refines: "No story x3" is what the
    reader said, and it is more use than "Sounds like a report x3"."""
    labels = _labels()
    counts: dict = {}
    for e in STORE.clean_events(STORE.session_events(session_id, root), root):
        if e.get("version_sha256") != version_sha:
            continue
        if e["event_type"] == "FEEDBACK_DETAIL":
            key = e.get("detail") or ""
        elif e["event_type"] in DESK.BUTTON_SIGNALS:
            key = e["event_type"]
        else:
            continue
        if key:
            counts[key] = counts.get(key, 0) + 1
    # A primary press that was then refined is not also counted: the detail is the
    # sharper statement of the same reaction.
    for e in STORE.session_events(session_id, root):
        if e["event_type"] == "FEEDBACK_DETAIL":
            parent = (e.get("metadata") or {}).get("of_action")
            if parent in counts:
                counts[parent] -= 1
                if counts[parent] <= 0:
                    counts.pop(parent, None)
    return sorted(((labels.get(k, k), n) for k, n in counts.items()),
                  key=lambda kv: (-kv[1], kv[0]))


# How long an article stays in the default view, measured from WHEN IT WAS WRITTEN.
#
# Not from when the desk delivered it. The first version of this aged by delivery time
# and therefore aged nothing: the entire three-week backlog was delivered in one
# evening, so every row was "recent" and /today still opened with twenty articles. An
# article written on 10 September is old on 27 September however long it sat unseen.
RECENT_DAYS = 2


def run_date(run_id: str):
    """The date in a run id, or None. `production-20260927T070556Z-17cadeff` and
    `editorial-20260927-oxevision-v3` both answer; anything else does not, and an
    unparseable id is treated as current rather than silently buried."""
    import datetime
    import re
    m = re.search(r"(20\d{6})", run_id or "")
    if not m:
        return None
    try:
        return datetime.datetime.strptime(m.group(1), "%Y%m%d").replace(
            tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def _title_for(sess: dict, root=None) -> str:
    """What the owner was SHOWN, if that was recorded; otherwise the run's own title.

    The card title wins because it is the text that was actually on screen. Only the
    five cards delivered before card titles existed need the fallback, and falling back
    to the run id -- which is what happened -- puts a timestamp where a headline
    belongs.
    """
    for e in reversed(STORE.session_events(sess["session_id"], root)):
        if e["event_type"] == "CARD_SENT" and (e.get("metadata") or {}).get("title"):
            return e["metadata"]["title"]
    sha = sess["origin_version_sha256"]
    return (DESK.title_of(pathlib.Path(DESK.EVIDENCE_ROOT) / sess["run_id"],
                          STORE.read_version_bytes(sha, root))
            or sess["run_id"])


def last_touched(session_id: str, version_sha: str, root=None):
    """When the owner last did anything to this version, or None."""
    import datetime
    stamps = [e["ts"] for e in STORE.session_events(session_id, root)
              if e.get("version_sha256") == version_sha and e.get("ts")]
    if not stamps:
        return None
    try:
        return datetime.datetime.fromisoformat(max(stamps))
    except ValueError:
        return None


def inbox(root=None, now=None) -> list:
    """Everything on the desk, one row per immutable version. Chooses nothing.

    `recent` marks what belongs in the default view. An unopened article is judged on
    when it was WRITTEN; an opened one on when it was LAST TOUCHED, so a read you came
    back to this morning stays and one you left three weeks ago does not.

    A PART-READ ARTICLE USED TO STAY FOREVER, on the reasoning that open work is open
    work. In practice that turns the inbox into a guilt list: press READ on twenty
    articles and twenty permanent RESUME rows follow you around, which is the same
    accumulation problem as the unread backlog arriving by a different door. Progress
    is kept; RESUME brings it straight back.

    AGEING A ROW OUT OF VIEW IS HOUSEKEEPING, NOT A JUDGEMENT. Nothing is recorded,
    nothing is marked abandoned, and no editorial signal is derived from the fact that
    a reading stopped. Silence is not a signal here either -- the owner putting a phone
    down is not a verdict on an article, and the log will not pretend otherwise.
    """
    import datetime
    now = now or datetime.datetime.now(datetime.timezone.utc)
    rows = []
    for sess in STORE.sessions(root):
        sha = sess["origin_version_sha256"]
        st = version_state(sess["session_id"], sha, root)
        vrow = STORE.version_row(sha, root) or {}
        written = run_date(sess["run_id"])
        if written is None:
            try:
                written = datetime.datetime.fromisoformat(sess["created_at"])
            except Exception:
                written = now
        age = max(0.0, (now - written).total_seconds() / 86400.0)
        touched = last_touched(sess["session_id"], sha, root)
        idle = (max(0.0, (now - touched).total_seconds() / 86400.0)
                if touched else age)
        rows.append({"session_id": sess["session_id"], "version_sha256": sha,
                     "run_id": sess["run_id"], "title": _title_for(sess, root),
                     "words": vrow.get("words", 0),
                     "version_id": vrow.get("version_id", ""),
                     "reason": vrow.get("reason", ""),
                     "summary": feedback_summary(sess["session_id"], sha, root),
                     "age_days": age,
                     "idle_days": idle,
                     "recent": (idle <= RECENT_DAYS if st["status"] == READING
                                else age <= RECENT_DAYS),
                     **st})
    rows.sort(key=lambda r: (STATE_ORDER.index(r["status"]), r["age_days"]))
    return rows


def _created_ts(session_id: str, root=None) -> float:
    for sess in STORE.sessions(root):
        if sess["session_id"] == session_id:
            try:
                import datetime
                return datetime.datetime.fromisoformat(sess["created_at"]).timestamp()
            except Exception:
                return 0.0
    return 0.0


# ── reading and reacting ────────────────────────────────────────────────────────────

def react(*, session_id: str, run_id: str, version_sha: str, event_type: str,
          user_id, chat_id, message_id=None, block: dict | None = None,
          raw_feedback: str | None = None, dedupe_key: str = "",
          reply_to_message_id=None, detail: str = "",
          metadata: dict | None = None, root=None) -> dict | None:
    """One explicit reaction, bound to the exact block it was made against.

    `block` is the stored BLOCKS row the reaction refers to, which is how the desk knows
    the paragraph range without matching text: the owner replied to a Telegram message,
    and that message is the range.

    Returns None when `dedupe_key` was already recorded. Telegram redelivers callbacks
    on retry, and a redelivered press is the same press.
    """
    return STORE.record_event(
        session=session_id, run_id=run_id, event_type=event_type,
        actor=actor_of(user_id), version_sha=version_sha,
        version_id=VERSION_ORIGIN,
        block_id=(block or {}).get("block_id"),
        paragraph_start=(block or {}).get("paragraph_start"),
        paragraph_end=(block or {}).get("paragraph_end"),
        chat_id=chat_id, message_id=message_id,
        # THE MESSAGE THE OWNER ACTUALLY REPLIED TO, or None when they simply typed.
        # It used to be filled with the block's own message id, which made the field a
        # tautology -- it could never disagree with the block, so it could never
        # evidence anything. `metadata.binding` says how the block was arrived at;
        # this says what Telegram was told.
        reply_to_message_id=reply_to_message_id,
        raw_feedback=raw_feedback, detail=detail,
        derived_signals=DESK.derived_signals(event_type, detail),
        dedupe_key=dedupe_key, metadata=metadata, root=root)


def brief_for(session_id: str, version_sha: str, root=None) -> str:
    """The edit brief for ONE version's reading.

    Filtering by version matters more than it looks: after a rewrite the same session
    holds two readings, and feeding v0's complaints into a rewrite of v1 would ask the
    writer to fix things it has already fixed.
    """
    evs = [e for e in STORE.clean_events(STORE.session_events(session_id, root), root)
           if e.get("version_sha256") == version_sha]
    row = STORE.version_row(version_sha, root) or {}
    return DESK.edit_brief(evs, words=row.get("words", 0))


# ── the one bounded rewrite ─────────────────────────────────────────────────────────

REWRITE_REQUESTED = "REQUESTED"
REWRITE_DONE = "DONE"
REWRITE_FAILED = "FAILED"
REWRITE_REFUSED = "REFUSED"

MAX_REWRITES_PER_SESSION = 1


def request_rewrite(*, session_id: str, run_id: str, version_sha: str, user_id,
                    chat_id, rewrite_fn, run_dir=None, recheck_fn=None,
                    root=None) -> dict:
    """ONE editorial rewrite per session, from the owner's reading of this version.

    `rewrite_fn(article_text, brief) -> str` performs the single model call and is
    injected, so the state machine is testable without a provider. It may reorder, cut,
    compress and re-explain; the brief itself carries the factual boundary, and the
    result is treated as a PROPOSAL, not an accepted article.

    THE REWRITTEN VERSION IS NOT PUBLISHABLE, and this is not a gap to close later by
    relaxing something. The existing publisher republishes the RETAINED RUN's bytes; a
    version this desk produced has been through no Safety, Grounding, Fact Check or
    Reader pass, and nothing in the publication-safety bridge would know that. So v1 is
    stored, delivered and read, and `publish` refuses it by the bytes check until a real
    revalidation path exists. A rewrite that cannot be published is still worth having:
    it is how the owner finds out whether the article can be saved.
    """
    done = [r for r in STORE.session_rewrites(session_id, root)
            if r.get("status") == REWRITE_DONE]
    if len(done) >= MAX_REWRITES_PER_SESSION:
        return {"status": REWRITE_REFUSED,
                "detail": "one editorial rewrite per session; this one has had %d"
                          % len(done)}
    brief = brief_for(session_id, version_sha, root)
    STORE.record_event(
        session=session_id, run_id=run_id, event_type="REWRITE_REQUESTED",
        actor=actor_of(user_id), version_sha=version_sha,
        version_id=VERSION_ORIGIN, chat_id=chat_id,
        dedupe_key="rewrite-requested:%s:%s" % (session_id, version_sha), root=root)
    source = STORE.read_version_bytes(version_sha, root)
    try:
        new_text = (rewrite_fn(source, brief) or "").strip()
    except Exception as e:                                            # noqa: BLE001
        STORE.record_rewrite(session=session_id, run_id=run_id, from_sha=version_sha,
                             brief=brief, status=REWRITE_FAILED,
                             detail="%s: %s" % (type(e).__name__, str(e)[:200]),
                             root=root)
        return {"status": REWRITE_FAILED,
                "detail": "%s: %s" % (type(e).__name__, str(e)[:200])}
    if not new_text or new_text == source:
        STORE.record_rewrite(session=session_id, run_id=run_id, from_sha=version_sha,
                             brief=brief, status=REWRITE_FAILED,
                             detail="the rewrite returned nothing new", root=root)
        return {"status": REWRITE_FAILED, "detail": "the rewrite returned nothing new"}

    parent = STORE.version_row(version_sha, root) or {}
    new_sha = STORE.sha256_text(new_text)

    # THE REWRITE IS A PROPOSAL UNTIL IT HAS BEEN CHECKED, and it is checked on the
    # exact bytes produced -- semantic delta against the parent, then Grounding over
    # the frozen evidence. Both must pass. See editorial_desk_recheck for why one is
    # not enough.
    if recheck_fn is None:
        def recheck_fn(parent_text, child_text):
            import editorial_desk_recheck as RC
            return RC.check(run_dir or "", parent_text, child_text)
    try:
        verdict = recheck_fn(source, new_text)
    except Exception as e:                                            # noqa: BLE001
        verdict = {"status": "NOT_CHECKED", "cleared": False,
                   "reason": "recheck failed (%s)" % type(e).__name__,
                   "delta_errors": [], "grounding_blocking": []}

    STORE.record_version(
        session=session_id, run_id=run_id, text=new_text,
        version_id="v%d" % (len(done) + 1), reason=STORE.REASON_EDITORIAL_REWRITE,
        parent_version_id=parent.get("version_id"), parent_sha256=version_sha,
        gate_status={"revalidated": bool(verdict.get("cleared")),
                     "recheck_status": verdict.get("status"),
                     "recheck_reason": verdict.get("reason", ""),
                     "delta_errors": verdict.get("delta_errors") or [],
                     "grounding_blocking": verdict.get("grounding_blocking") or []},
        root=root)
    STORE.record_rewrite(session=session_id, run_id=run_id, from_sha=version_sha,
                         brief=brief, status=REWRITE_DONE, to_sha=new_sha,
                         detail=verdict.get("status", ""), root=root)

    # A rewritten version is its own thing to read, so it gets its own session and
    # therefore its own UNREAD/READING/FINISHED state. v0 and v1 sitting side by side
    # is exactly the case the per-version state model exists for.
    STORE.ensure_session(run_id=run_id, version_sha=new_sha,
                         state=DESK.REVIEWABLE_DRAFT,
                         publish_state=DESK.PUBLISH_BLOCKED, root=root)
    return {"status": REWRITE_DONE, "version_sha256": new_sha, "text": new_text,
            "brief": brief, "recheck": verdict}


# ── approval and publication ────────────────────────────────────────────────────────

def approve(*, session_id: str, run_id: str, version_sha: str, user_id, chat_id,
            env: dict | None = None, root=None) -> dict:
    """Record the owner's explicit approval of exactly these bytes.

    Approval is a separate, recorded act from publication so that the thing bound to
    the published article is a decision a person made about a specific version, not a
    button that happened to be pressed while some version was on screen.
    """
    if not authorized(user_id, env):
        return {"ok": False, "detail": "not authorized"}
    STORE.record_event(
        session=session_id, run_id=run_id, event_type="OWNER_APPROVED",
        actor=actor_of(user_id), version_sha=version_sha, chat_id=chat_id,
        dedupe_key="approved:%s" % version_sha, root=root)
    STORE.record_decision(
        session=session_id, run_id=run_id, version_sha=version_sha,
        action="OWNER_APPROVED", actor=actor_of(user_id), root=root)
    return {"ok": True}


def publish(*, session_id: str, run_id: str, run_dir, version_sha: str, user_id,
            chat_id, publish_fn=None, env: dict | None = None, root=None) -> dict:
    """The only path from a Telegram button to a published article. Four guards.

    1. AUTHORIZED. The presser is on the allowlist.
    2. EXPLICITLY APPROVED. An OWNER_APPROVED decision exists for these exact bytes. No
       model, and no profile learned from past approvals, may stand in for it.
    3. IDENTICAL BYTES. The retained run still holds the article the owner approved.
       This is what refuses to publish a desk rewrite: v1's hash is not the run's hash,
       so the guard fires without needing to know what a rewrite is.
    4. THE PUBLISHER AGREES, NOW. Eligibility is re-evaluated at publication time by
       the existing validator, not read from what the desk recorded at delivery.

    Publishing twice is not recoverable, so a completed publication of these bytes
    short-circuits before anything is called.
    """
    run_dir = pathlib.Path(run_dir)
    already = STORE.published_version(version_sha, root)
    if already:
        return {"ok": True, "idempotent": True,
                "detail": "already published at %s" % already.get("ts")}

    if not authorized(user_id, env):
        STORE.record_event(session=session_id, run_id=run_id,
                           event_type="PUBLISH_REFUSED", actor=actor_of(user_id),
                           version_sha=version_sha, chat_id=chat_id,
                           metadata={"reason": "not authorized"}, root=root)
        return {"ok": False, "detail": "not authorized"}

    if not STORE.approved_version(version_sha, root):
        return {"ok": False, "detail": "no explicit owner approval for this version"}

    text, _ = DESK.article_text(run_dir)
    if STORE.sha256_text(text) != version_sha:
        STORE.record_event(session=session_id, run_id=run_id,
                           event_type="PUBLISH_REFUSED", actor=actor_of(user_id),
                           version_sha=version_sha, chat_id=chat_id,
                           metadata={"reason": "bytes differ from the retained run"},
                           root=root)
        return {"ok": False,
                "detail": "the approved version is not the retained run's article -- a "
                          "desk rewrite has not been through Safety, Grounding, Fact "
                          "Check or Reader and cannot be published from here"}

    state, reason = DESK.publish_state(run_dir)
    if state != DESK.PUBLISH_ELIGIBLE:
        STORE.record_event(session=session_id, run_id=run_id,
                           event_type="PUBLISH_REFUSED", actor=actor_of(user_id),
                           version_sha=version_sha, chat_id=chat_id,
                           metadata={"reason": reason}, root=root)
        return {"ok": False, "detail": reason}

    STORE.record_event(session=session_id, run_id=run_id,
                       event_type="PUBLISH_REQUESTED", actor=actor_of(user_id),
                       version_sha=version_sha, chat_id=chat_id,
                       dedupe_key="publish-requested:%s" % version_sha, root=root)
    if publish_fn is None:
        def publish_fn(d):
            import publish_retained_fast_lane as PRFL
            return PRFL.resume(str(d), publish=True)
    try:
        result = publish_fn(run_dir)
    except Exception as e:                                            # noqa: BLE001
        detail = "%s: %s" % (type(e).__name__, str(e)[:200])
        STORE.record_event(session=session_id, run_id=run_id,
                           event_type="PUBLISH_FAILED", actor=actor_of(user_id),
                           version_sha=version_sha, chat_id=chat_id,
                           metadata={"reason": detail}, root=root)
        STORE.record_decision(session=session_id, run_id=run_id,
                              version_sha=version_sha, action="PUBLISH_FAILED",
                              actor=actor_of(user_id), detail=detail, root=root)
        return {"ok": False, "detail": detail}

    ok = bool(result.get("published")) if isinstance(result, dict) else False
    if ok:
        STORE.record_event(session=session_id, run_id=run_id, event_type="PUBLISHED",
                           actor=actor_of(user_id), version_sha=version_sha,
                           chat_id=chat_id, metadata={"result": result}, root=root)
        STORE.record_decision(session=session_id, run_id=run_id,
                              version_sha=version_sha, action="PUBLISHED",
                              actor=actor_of(user_id),
                              detail=str(result.get("candidate_path") or ""),
                              metadata={"result": result}, root=root)
        return {"ok": True, "result": result}
    detail = str((result or {}).get("blocker")
                 or (result or {}).get("status") or "publication failed")
    STORE.record_event(session=session_id, run_id=run_id, event_type="PUBLISH_FAILED",
                       actor=actor_of(user_id), version_sha=version_sha,
                       chat_id=chat_id, metadata={"reason": detail}, root=root)
    STORE.record_decision(session=session_id, run_id=run_id, version_sha=version_sha,
                          action="PUBLISH_FAILED", actor=actor_of(user_id),
                          detail=detail, root=root)
    return {"ok": False, "detail": detail}
