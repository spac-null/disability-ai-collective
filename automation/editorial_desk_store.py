"""The durable record behind the Telegram editorial desk: append-only, owner-authored.

Same shape and the same reasons as repair_review_store.py, which this deliberately
mirrors rather than improving on: JSONL, one row per fact, never rewritten. A reaction
the owner had on a Tuesday is not improved by being edited on a Thursday, and the whole
value of this store is that it can be replayed later to learn how Jascha actually edits.

  SESSIONS.jsonl     one row per (run, version) delivered to Telegram. Idempotent.
  VERSIONS.jsonl     one row per immutable article version. Bytes live beside it.
  BLOCKS.jsonl       one row per delivered block, carrying its Telegram message id.
  EVENTS.jsonl       the editorial event log: every explicit owner action.
  REWRITES.jsonl     one row per rewrite request and its outcome.
  DECISIONS.jsonl    one row per publication decision.
  versions/<sha>.md  the exact bytes of every version, written once, never overwritten.

THREE RULES THIS FILE ENFORCES, BECAUSE THEY ARE THE ONES EASY TO BREAK LATER.

1. RAW FEEDBACK IS AUTHORITATIVE AND IS NEVER REPLACED. `raw_feedback` holds exactly
   what the owner typed. `derived_signals` is the machine's reading of it, stored
   alongside and freely recomputable later. A derived signal may never be written into
   the raw field, and recomputing the taxonomy may never rewrite a historical row.

2. SILENCE IS NOT A SIGNAL. Nothing here records "did not respond", "read but did not
   press", or any latency-derived judgement. `received_at` exists as technical telemetry
   and carries no editorial meaning. Six hours between blocks means the owner was doing
   something else, and a store that cannot express boredom cannot accidentally infer it.

3. A VERSION IS ITS BYTES. Identity is sha256 of the exact article text, and
   `write_version_bytes` refuses to overwrite a differing file under an existing hash.
   Everything downstream -- approval, publication, the learning record -- binds to that
   hash rather than to a path or a run name.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib

ROOT = pathlib.Path(os.environ.get("CRIPMINDS_DESK_DIR",
                                   "/srv/data/cripminds-editorial-desk"))

SESSIONS = "SESSIONS.jsonl"
VERSIONS = "VERSIONS.jsonl"
BLOCKS = "BLOCKS.jsonl"
EVENTS = "EVENTS.jsonl"
REWRITES = "REWRITES.jsonl"
DECISIONS = "DECISIONS.jsonl"

# Explicit owner actions and the delivery facts around them. Anything not on this list
# is not an editorial event, and in particular no absence of action is one.
EVENT_TYPES = (
    "DESK_DELIVERED",
    "READ_STARTED",
    "CONTINUE",
    "TOO_FAST",
    "WHY_NOW",
    "STRONG",
    "READER_LOST",
    "WANT_MORE",
    "FREE_TEXT_FEEDBACK",
    "ARTICLE_FINISHED",
    "REWRITE_REQUESTED",
    "VERSION_DELIVERED",
    "ALMOST",
    "NOT_GOOD",
    "HOLD",
    "OWNER_APPROVED",
    "PUBLISH_REQUESTED",
    "PUBLISHED",
    "PUBLISH_FAILED",
    "PUBLISH_REFUSED",
)

# Reader reactions that arrive as a button press. Kept apart from the lifecycle events
# above because these -- and the free text -- are the editorial evidence; the rest is
# bookkeeping about delivery.
REACTION_EVENTS = ("CONTINUE", "TOO_FAST", "WHY_NOW", "STRONG",
                   "READER_LOST", "WANT_MORE")

REASON_RETAINED_RUN = "RETAINED_RUN"
REASON_EDITORIAL_REWRITE = "EDITORIAL_REWRITE"


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _root(root=None) -> pathlib.Path:
    p = pathlib.Path(root or ROOT)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _path(name: str, root=None) -> pathlib.Path:
    return _root(root) / name


def _read(name: str, root=None) -> list:
    p = _path(name, root)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            # A corrupt line is skipped rather than raised on: the desk must still be
            # able to show yesterday's work when one row was half-written by a kill.
            continue
    return rows


def _append(name: str, row: dict, root=None) -> dict:
    p = _path(name, root)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=False, default=str) + "\n")
    return row


# ── identity ────────────────────────────────────────────────────────────────────────

def session_id(run_id: str, version_sha: str) -> str:
    """Stable across restarts and re-scans, so re-delivering the same article cannot
    open a second session. The version hash is part of it deliberately: a rewritten
    article is the same run and a DIFFERENT thing to read."""
    return hashlib.sha256(("%s\x00%s" % (run_id, version_sha))
                          .encode("utf-8")).hexdigest()[:16]


def event_id(session: str, kind: str, marker: str) -> str:
    return hashlib.sha256(("%s\x00%s\x00%s" % (session, kind, marker))
                          .encode("utf-8")).hexdigest()[:16]


# ── versions ────────────────────────────────────────────────────────────────────────

def write_version_bytes(text: str, root=None) -> str:
    """Store the exact article bytes under their own hash. Write-once.

    Raises if a file already exists under this hash with different content, which can
    only mean a hash collision or a corrupted store -- either way, not something to
    paper over by overwriting the earlier bytes.
    """
    sha = sha256_text(text)
    d = _root(root) / "versions"
    d.mkdir(parents=True, exist_ok=True)
    p = d / ("%s.md" % sha)
    if p.exists():
        if p.read_text(encoding="utf-8") != text:
            raise ValueError("version bytes for %s already exist and differ" % sha[:12])
        return sha
    p.write_text(text, encoding="utf-8")
    return sha


def read_version_bytes(sha: str, root=None) -> str:
    p = _root(root) / "versions" / ("%s.md" % sha)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def versions(root=None) -> list:
    return _read(VERSIONS, root)


def version_row(version_sha: str, root=None) -> dict | None:
    for r in versions(root):
        if r.get("sha256") == version_sha:
            return r
    return None


def record_version(*, session: str, run_id: str, text: str, version_id: str,
                   reason: str, parent_version_id: str | None = None,
                   parent_sha256: str | None = None,
                   gate_status: dict | None = None, root=None) -> dict:
    """An immutable article version. Re-recording identical bytes is a no-op, so a
    restart mid-delivery cannot fork the version history."""
    sha = write_version_bytes(text, root)
    existing = version_row(sha, root)
    if existing:
        return existing
    return _append(VERSIONS, {
        "sha256": sha,
        "session_id": session,
        "run_id": run_id,
        "version_id": version_id,
        "parent_version_id": parent_version_id,
        "parent_sha256": parent_sha256,
        "reason": reason,
        "created_at": now(),
        "words": len((text or "").split()),
        # The gate verdicts this version was produced under, copied verbatim from the
        # run's own artifacts. Recorded so a later reader knows what was true when the
        # owner read it, not what the pipeline says today.
        "gate_status": gate_status or {},
    }, root)


# ── sessions ────────────────────────────────────────────────────────────────────────

def sessions(root=None) -> list:
    return _read(SESSIONS, root)


def session(session: str, root=None) -> dict | None:
    for r in sessions(root):
        if r.get("session_id") == session:
            return r
    return None


def ensure_session(*, run_id: str, version_sha: str, state: str,
                   publish_state: str, root=None) -> tuple:
    """(row, created). Idempotent on (run_id, version_sha).

    The whole reason delivery can be retried safely: a Telegram send that times out
    after the message actually landed must not, on the next scan, open a second session
    and deliver the article twice.
    """
    sid = session_id(run_id, version_sha)
    existing = session(sid, root)
    if existing:
        return existing, False
    return _append(SESSIONS, {
        "session_id": sid,
        "run_id": run_id,
        "origin_version_sha256": version_sha,
        "state": state,
        "publish_state_at_delivery": publish_state,
        "created_at": now(),
    }, root), True


# ── blocks ──────────────────────────────────────────────────────────────────────────

def blocks(root=None) -> list:
    return _read(BLOCKS, root)


def record_block(*, session: str, version_sha: str, block_id: str, index: int,
                 total: int, paragraph_start: int, paragraph_end: int, text: str,
                 chat_id, message_id, root=None) -> dict:
    return _append(BLOCKS, {
        "session_id": session,
        "version_sha256": version_sha,
        "block_id": block_id,
        "index": index,
        "of": total,
        "paragraph_start": paragraph_start,
        "paragraph_end": paragraph_end,
        "text_sha256": sha256_text(text),
        "telegram_chat_id": chat_id,
        "telegram_message_id": message_id,
        "sent_at": now(),
    }, root)


def block_for_message(chat_id, message_id, root=None) -> dict | None:
    """Which block a reply landed on. This is why the desk needs no span matching: the
    owner replies to a Telegram message, and that message IS the paragraph range."""
    for r in reversed(blocks(root)):
        if (str(r.get("telegram_chat_id")) == str(chat_id)
                and str(r.get("telegram_message_id")) == str(message_id)):
            return r
    return None


def session_blocks(session: str, version_sha: str, root=None) -> list:
    return [r for r in blocks(root)
            if r.get("session_id") == session
            and r.get("version_sha256") == version_sha]


# ── events ──────────────────────────────────────────────────────────────────────────

def events(root=None) -> list:
    return _read(EVENTS, root)


def session_events(session: str, root=None) -> list:
    return [r for r in events(root) if r.get("session_id") == session]


def has_event_key(dedupe_key: str, root=None) -> bool:
    if not dedupe_key:
        return False
    return any(r.get("dedupe_key") == dedupe_key for r in events(root))


def record_event(*, session: str, run_id: str, event_type: str, actor: str,
                 version_sha: str = "", version_id: str = "",
                 block_id: str | None = None,
                 paragraph_start: int | None = None,
                 paragraph_end: int | None = None,
                 chat_id=None, message_id=None, reply_to_message_id=None,
                 raw_feedback: str | None = None,
                 derived_signals: list | None = None,
                 dedupe_key: str = "", metadata: dict | None = None,
                 root=None) -> dict | None:
    """One explicit owner action, or one delivery fact. Returns None if `dedupe_key`
    has already been recorded -- Telegram redelivers callbacks, and a redelivered
    button press is the same press, not a second opinion.

    `raw_feedback` is stored exactly as typed. `derived_signals` is the machine's
    reading and is stored beside it, never in place of it.
    """
    if event_type not in EVENT_TYPES:
        raise ValueError("unknown event_type %r" % event_type)
    if dedupe_key and has_event_key(dedupe_key, root):
        return None
    return _append(EVENTS, {
        "event_id": event_id(session, event_type, dedupe_key or now()),
        "ts": now(),
        "session_id": session,
        "run_id": run_id,
        "version_id": version_id,
        "version_sha256": version_sha,
        "block_id": block_id,
        "paragraph_start": paragraph_start,
        "paragraph_end": paragraph_end,
        "telegram_chat_id": chat_id,
        "telegram_message_id": message_id,
        "reply_to_message_id": reply_to_message_id,
        "event_type": event_type,
        "raw_feedback": raw_feedback,
        "derived_signals": derived_signals or [],
        "actor": actor,
        "dedupe_key": dedupe_key,
        "metadata": metadata or {},
    }, root)


# ── rewrites ────────────────────────────────────────────────────────────────────────

def rewrites(root=None) -> list:
    return _read(REWRITES, root)


def session_rewrites(session: str, root=None) -> list:
    return [r for r in rewrites(root) if r.get("session_id") == session]


def record_rewrite(*, session: str, run_id: str, from_sha: str, brief: str,
                   status: str, to_sha: str = "", detail: str = "",
                   root=None) -> dict:
    return _append(REWRITES, {
        "rewrite_id": event_id(session, "REWRITE", from_sha + status + now()),
        "session_id": session,
        "run_id": run_id,
        "from_version_sha256": from_sha,
        "to_version_sha256": to_sha,
        "brief": brief,
        "status": status,
        "detail": detail,
        "ts": now(),
    }, root)


# ── publication decisions ───────────────────────────────────────────────────────────

def decisions(root=None) -> list:
    return _read(DECISIONS, root)


def session_decisions(session: str, root=None) -> list:
    return [r for r in decisions(root) if r.get("session_id") == session]


def published_version(version_sha: str, root=None) -> dict | None:
    """A completed publication of exactly these bytes, if one exists.

    The idempotency guard for the Publish button: Telegram will happily deliver the
    same callback twice, and publishing twice is not a recoverable mistake.
    """
    for r in decisions(root):
        if r.get("version_sha256") == version_sha and r.get("action") == "PUBLISHED":
            return r
    return None


def approved_version(version_sha: str, root=None) -> dict | None:
    for r in decisions(root):
        if r.get("version_sha256") == version_sha and r.get("action") == "OWNER_APPROVED":
            return r
    return None


def record_decision(*, session: str, run_id: str, version_sha: str, action: str,
                    actor: str, detail: str = "", metadata: dict | None = None,
                    root=None) -> dict:
    return _append(DECISIONS, {
        "decision_id": event_id(session, action, version_sha + now()),
        "session_id": session,
        "run_id": run_id,
        "version_sha256": version_sha,
        "action": action,
        "actor": actor,
        "detail": detail,
        "metadata": metadata or {},
        "ts": now(),
    }, root)
