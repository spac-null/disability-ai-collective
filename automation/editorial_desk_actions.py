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


# ── reading and reacting ────────────────────────────────────────────────────────────

def react(*, session_id: str, run_id: str, version_sha: str, event_type: str,
          user_id, chat_id, message_id=None, block: dict | None = None,
          raw_feedback: str | None = None, dedupe_key: str = "",
          reply_to_message_id=None,
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
        raw_feedback=raw_feedback,
        derived_signals=DESK.derived_signals(event_type),
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
                    chat_id, rewrite_fn, root=None) -> dict:
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
    STORE.record_version(
        session=session_id, run_id=run_id, text=new_text,
        version_id="v%d" % (len(done) + 1), reason=STORE.REASON_EDITORIAL_REWRITE,
        parent_version_id=parent.get("version_id"), parent_sha256=version_sha,
        gate_status={"revalidated": False,
                     "note": "produced by the editorial desk; no gate has seen it"},
        root=root)
    STORE.record_rewrite(session=session_id, run_id=run_id, from_sha=version_sha,
                         brief=brief, status=REWRITE_DONE, to_sha=new_sha, root=root)
    return {"status": REWRITE_DONE, "version_sha256": new_sha, "text": new_text,
            "brief": brief}


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
