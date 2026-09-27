#!/usr/bin/env python3
"""cripminds_bot -- Jascha's editorial desk. A Telegram adapter and nothing else.

Follows the trident bot pattern already proven by sentinel-bot, reef-bot, compass-bot
and inbox-bot: stdlib only, long-poll getUpdates, a lock file, an offset file, an
explicit allowlist, systemd Restart=always. It runs under its OWN token -- reef-bot is
already polling REEF_BOT_TOKEN, and two pollers on one token steal each other's updates.

WHAT IT DOES AND DOES NOT DECIDE. Every editorial and publication decision lives in
editorial_desk_actions.py; this file turns Telegram events into calls on that and
formats the replies. It holds no state of its own: the reading position is derived from
the blocks already sent, so a restart mid-article resumes exactly where the owner was.

ARTICLE IDENTITY IS CARRIED BY THE BUTTON, AND NOTHING ELSE RESOLVES IT. Every inline
button embeds the session id, which is sha256(run_id, article bytes) -- an immutable
binding to one run and one exact version. A handler uses the session the button names,
verifies the stored bytes still hash to the version that card was built from, and sends
blocks from those bytes only. It may never re-resolve an article from queue order, card
position, the latest delivery, a title, or any notion of "current". A card whose session
cannot be found refuses and says so; it never falls back to another article.

That paragraph exists because the opposite was shipped on 2026-09-26. Five cards went
out at 17:00:17 and every READ, whichever card it sat under, opened card five -- the
handler resolved the right session from the button and then discarded it for "the most
recently delivered". A second press on a different card advanced the same wrong article
rather than opening the right one. See test_multi_card_identity in
editorial_desk_bot_test.py, which is the regression that must never go green by
accident.

THE NORMAL VIEW IS PLAIN LANGUAGE. Draft ready, readable now, blocked at Safety, ready
to publish, published. No SHAs, no stage taxonomy, no prompt hashes, no provider names,
no model-call counts. /debug shows all of it on request. The machine's problems must not
become the owner's working interface.

  /today      what is waiting, and deliver anything new
  /backlog    finished articles from earlier days that were never read
  /read       start (or resume) reading the current article
  /brief      what your reading adds up to so far
  /rewrite    one editorial rewrite from your reading
  /publish    approve and publish the exact version you read
  /hold       stop for now
  /status     where you are
  /debug      the engineering view of the current run
"""
from __future__ import annotations

import fcntl
import json
import os
import pathlib
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import editorial_desk as DESK                      # noqa: E402
import editorial_desk_actions as ACT               # noqa: E402
import editorial_desk_store as STORE               # noqa: E402

SECRETS_FILE = os.environ.get("CRIPMINDS_DESK_ENV",
                              "/srv/secrets/cripminds/desk-bot.env")
STATE_DIR = pathlib.Path(os.environ.get("CRIPMINDS_DESK_DIR",
                                        "/srv/data/cripminds-editorial-desk"))
OFFSET_FILE = STATE_DIR / "desk-bot.offset"
LOCK_FILE = STATE_DIR / "desk-bot.lock"

POLL_TIMEOUT = 30
HTTP_TIMEOUT = 20
BACKLOG_DAYS = 14

BOT_TOKEN = ""
CHAT_ID = ""
running = True

# NAVIGATION AND FEEDBACK ARE DIFFERENT ACTS, and until 2026-09-27 this keyboard
# conflated them: every reaction also advanced the reader, so "Continue" meant both
# "no objection" and "next page", and a reaction could not be given without moving.
# Now the top row carries the reader and nothing else; the rows below carry judgement
# and leave the reader where they are.
NAV_BUTTONS = [("< Back", "BACK"), ("Next >", "NEXT")]

# The labels are the owner's vocabulary, not the pipeline's: nothing here mentions a
# stage, a gate or a finding. "Too fast" is deliberately absent -- see BUTTON_SIGNALS.
BLOCK_BUTTONS = [
    [("Strong", "STRONG"), ("Too dense", "TOO_DENSE")],
    [("Sounds like a report", "SOUNDS_LIKE_REPORT")],
    [("I am lost", "READER_LOST"), ("Why now?", "WHY_NOW"), ("Want more", "WANT_MORE")],
]

HELP = (
    "You read. I do the rest.\n\n"
    "/today     what's waiting\n"
    "/read      start or continue reading\n"
    "/brief     what your reading adds up to\n"
    "/rewrite   one rewrite from your reading\n"
    "/publish   approve and publish what you read\n"
    "/hold      stop for now\n"
    "/backlog   articles from earlier days\n"
    "/status    where you are\n"
    "/debug     the engineering view\n\n"
    "Under each block, top row moves you: < Back and Next >.\n"
    "The rows under it are what you think, and they do not move you:\n"
    "  Strong · Too dense · Sounds like a report · I am lost · Why now? · Want more\n"
    "Too dense and Sounds like a report will ask which kind. Skipping that is fine — "
    "the press is already saved.\n\n"
    "Or just type what you think. Reply to a block and it lands on that exact "
    "passage. You never have to say how to fix it.")


def log(line):
    print("[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), line), flush=True)


# ── secrets and transport ───────────────────────────────────────────────────────────

def parse_env(path: str) -> dict:
    out = {}
    try:
        for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def load_secrets():
    """Environment first (systemd EnvironmentFile), then the file, and never a default.

    A desk that can publish must not start with an empty allowlist believing it means
    "everyone". No allowlist is a fatal misconfiguration, not a permissive one.
    """
    global BOT_TOKEN, CHAT_ID
    env = parse_env(SECRETS_FILE)
    BOT_TOKEN = os.environ.get("CRIPMINDS_DESK_BOT_TOKEN") or env.get(
        "CRIPMINDS_DESK_BOT_TOKEN", "")
    CHAT_ID = os.environ.get("CRIPMINDS_DESK_CHAT_ID") or env.get(
        "CRIPMINDS_DESK_CHAT_ID", "")
    if not os.environ.get(ACT.ALLOWED_USERS_ENV) and env.get(ACT.ALLOWED_USERS_ENV):
        os.environ[ACT.ALLOWED_USERS_ENV] = env[ACT.ALLOWED_USERS_ENV]
    if not BOT_TOKEN:
        log("FATAL: no CRIPMINDS_DESK_BOT_TOKEN")
        sys.exit(1)
    if not CHAT_ID:
        log("FATAL: no CRIPMINDS_DESK_CHAT_ID")
        sys.exit(1)
    if not ACT.allowed_users():
        log("FATAL: no %s -- refusing to run a publishing bot with no allowlist"
            % ACT.ALLOWED_USERS_ENV)
        sys.exit(1)
    log("secrets loaded, %d allowed user(s)" % len(ACT.allowed_users()))


def tg(method: str, payload: dict | None = None, timeout=None):
    url = "https://api.telegram.org/bot%s/%s" % (BOT_TOKEN, method)
    data = json.dumps(payload).encode() if payload else None
    headers = {"Content-Type": "application/json"} if data else {}
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout or HTTP_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if e.fp else ""
        log("TG %s HTTP %s: %s" % (method, e.code, body[:200]))
    except Exception as e:                                            # noqa: BLE001
        # Never echo the URL: it carries the token.
        log("TG %s failed: %s" % (method, type(e).__name__))
    return None


def block_keyboard(sid, block_id) -> list:
    """Navigation on top, judgement underneath. A reaction never moves the reader."""
    rows = [[(t, "%s:%s" % (code, sid)) for t, code in NAV_BUTTONS]]
    rows += [[(t, "%s:%s:%s" % (code, sid, block_id)) for t, code in row]
             for row in BLOCK_BUTTONS]
    return rows


def detail_keyboard(action, sid, block_id) -> list:
    """The optional second press. `d` keeps the payload well inside Telegram's 64-byte
    callback limit; `D`/`R` name which action is being refined."""
    tag = {"TOO_DENSE": "D", "SOUNDS_LIKE_REPORT": "R"}[action]
    opts = DESK.DETAIL_OPTIONS[action]
    rows = [[(label, "d:%s:%s:%s:%s" % (sid, block_id, tag, code))]
            for label, code in opts]
    # Navigation stays reachable: saying nothing about which kind is a complete answer,
    # and the reader must never be trapped in a sub-menu to get to the next block.
    rows.append([(t, "%s:%s" % (code, sid)) for t, code in NAV_BUTTONS])
    return rows


def edit_markup(chat, message_id, rows) -> None:
    """Swap the keyboard under a message that is already on screen, rather than sending
    a new one. The chat should be the article, not a log of what the reader pressed."""
    tg("editMessageReplyMarkup", {"chat_id": str(chat), "message_id": message_id,
                                  "reply_markup": keyboard(rows)})


def keyboard(rows) -> dict:
    return {"inline_keyboard": [
        [{"text": t, "callback_data": d} for t, d in row] for row in rows]}


def send(text: str, *, chat=None, buttons=None):
    """One message, one id. Returns the message id, which is what a block is addressed by.

    Text is never split here: a block that needed splitting would break the mapping
    between one message and one paragraph range, and DESK.split_blocks already keeps
    blocks inside Telegram's limit.
    """
    msg = {"chat_id": str(chat or CHAT_ID), "text": text[:4090],
           "disable_web_page_preview": True}
    if buttons:
        msg["reply_markup"] = keyboard(buttons)
    r = tg("sendMessage", msg)
    if r and r.get("ok"):
        return r["result"]["message_id"]
    return None


def answer_callback(cb_id, text=""):
    tg("answerCallbackQuery", {"callback_query_id": cb_id, "text": text[:190]})


# ── reading position, derived rather than stored ────────────────────────────────────

def closed_sessions() -> set:
    return {e["session_id"] for e in STORE.events()
            if e["event_type"] in ("ARTICLE_FINISHED", "HOLD")}


def reading_session():
    """The article the owner actually OPENED and has not closed. Never "the newest".

    THE BUG THIS REPLACES, 2026-09-26. The previous version returned the most recently
    DELIVERED session. Five cards were sent at 17:00:17; every READ button, whichever
    card it sat under, resolved to card five (`a5b9041f3730a0b5`,
    production-20260922) because that session was appended last. Pressing READ on a
    second card did not open that article either -- it advanced the same wrong one.

    "Current" can only ever mean the article the owner opened, so it is derived from
    READ_STARTED, which only a button carrying an explicit session id can produce. A
    typed /read with nothing open resolves to nothing, and says so, rather than
    guessing at an article.
    """
    closed = closed_sessions()
    for e in reversed(STORE.events()):
        if e["event_type"] == "READ_STARTED" and e["session_id"] not in closed:
            return STORE.session(e["session_id"])
    return None


def open_article(session_row) -> tuple:
    """(text, sha) for exactly the bytes this card was delivered as, or (None, reason).

    The identity check that must run before a single block is sent: the session names a
    version hash, the stored bytes must still hash to it, and the blocks must come from
    those bytes and no other source. Fails closed -- a mismatch sends nothing.
    """
    sha = (session_row or {}).get("origin_version_sha256") or ""
    if not sha:
        return None, "this card carries no version identity"
    text = STORE.read_version_bytes(sha)
    if not text:
        return None, "the stored bytes for this version are missing"
    if STORE.sha256_text(text) != sha:
        return None, "the stored bytes no longer match the version this card was for"
    return text, sha


def sent_blocks(session_id, version_sha):
    return sorted(STORE.session_blocks(session_id, version_sha),
                  key=lambda b: b.get("index", 0))


def cursor(session_id, version_sha) -> int:
    """Where the reader is: the index of the block most recently SENT.

    Derived from the block rows in the order they were sent, not from how many exist,
    because Back re-sends a block the reader has already seen. Counting rows would
    make Back move the reader forward, which is the opposite of the button.
    """
    rows = STORE.session_blocks(session_id, version_sha)
    if not rows:
        return 0
    return sorted(rows, key=lambda b: b.get("sent_at", ""))[-1].get("index", 0)


def run_dir_of(session_row) -> pathlib.Path:
    return pathlib.Path(DESK.EVIDENCE_ROOT) / session_row["run_id"]


def title_of(run_dir: pathlib.Path, text: str) -> str:
    pkg = DESK.artifact(run_dir, "EDITORIAL_PACKAGE.json")
    t = (pkg.get("title") or "").strip()
    if t:
        return t
    for line in (text or "").splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:90]
    return "Untitled"


# ── delivery ────────────────────────────────────────────────────────────────────────

def undelivered(limit=BACKLOG_DAYS):
    """Runs holding a coherent article that no session has been opened for."""
    known = {s["run_id"] for s in STORE.sessions()}
    out = []
    for d in DESK.scan(limit=limit * 3):
        if d.name in known:
            continue
        run = DESK.read_run(d)
        if run["state"] == DESK.REVIEWABLE_DRAFT:
            out.append(run)
        if len(out) >= limit:
            break
    return out


def offer(run: dict, chat=None):
    """The card. One article, its plain-language status, and two buttons.

    The session is created BEFORE the card is sent, because its id is what the buttons
    carry: a card is addressed by the immutable (run, bytes) identity it was built
    from, never by its position in the queue.
    """
    d = ACT.deliver(run, chat_id=chat or CHAT_ID)
    text = run["article_text"]
    title = title_of(pathlib.Path(run["run_dir"]), text)
    lines = ["New Crip Minds draft",
             "",
             title,
             "%d words" % run["words"],
             DESK.status_line(run)]
    if run["publish_state"] == DESK.PUBLISH_BLOCKED and run["gates"]["safety_blocking"]:
        lines.append("")
        lines.append("What the checks flagged:")
        for b in run["gates"]["safety_blocking"][:3]:
            lines.append("  - " + str(b)[:180])
    mid = send("\n".join(lines), chat=chat,
               buttons=[[("READ", "read:%s" % d["session_id"]),
                         ("HOLD", "hold:%s" % d["session_id"])]])
    # Which Telegram message this card became. Recorded so a click can be audited back
    # to the card the owner was actually looking at -- the fact the 2026-09-26 incident
    # investigation could not establish from the log alone.
    STORE.record_event(session=d["session_id"], run_id=run["run_id"],
                       event_type="CARD_SENT", actor="system",
                       version_sha=d["version_sha256"], chat_id=chat or CHAT_ID,
                       message_id=mid, dedupe_key="card:%s" % d["session_id"],
                       metadata={"title": title})
    return d


def send_block(session_row, version_sha, index, chat=None):
    """Send block `index` (1-based) from the exact bytes this session was delivered as.

    `version_sha` is not trusted as an argument: it must equal the session's own
    recorded version, and the stored bytes must still hash to it. Blocks are derived
    from those bytes and from no other source.
    """
    text, sha = open_article(session_row)
    if text is None:
        send("I can't open that article safely: %s. Nothing sent." % sha, chat=chat)
        return None
    if version_sha and version_sha != sha:
        send("I can't open that article safely: the button and the stored version "
             "disagree. Nothing sent.", chat=chat)
        return None
    blocks = DESK.split_blocks(text)
    if index > len(blocks):
        return finish(session_row, sha, chat=chat)
    b = blocks[index - 1]
    header = "%d/%d" % (b["index"], b["of"])
    mid = send("%s\n\n%s" % (header, b["text"]), chat=chat,
               buttons=block_keyboard(session_row["session_id"], b["block_id"]))
    if mid:
        ACT.record_block_sent(session_id=session_row["session_id"],
                              run_id=session_row["run_id"], version_sha=sha,
                              block=b, chat_id=chat or CHAT_ID, message_id=mid)
    return mid


def finish(session_row, version_sha, chat=None):
    """What the reader gets for finishing: their own reading back, and what to do next.

    NOT the publisher's refusal text. "Cannot publish yet: missing required artifact:
    article.md" is the retained-run validator's Fast-Lane contract failing on a
    story-architecture directory -- plumbing, never an editorial judgement, and it has
    no business in front of a reader. Publish appears only when it is genuinely
    available; otherwise it is simply absent.
    """
    sid = session_row["session_id"]
    STORE.record_event(session=sid, run_id=session_row["run_id"],
                       event_type="ARTICLE_FINISHED", actor="owner",
                       version_sha=version_sha, chat_id=chat or CHAT_ID,
                       dedupe_key="finished:%s:%s" % (sid, version_sha))

    lines = ["Finished.", ""]
    summary = ACT.feedback_summary(sid, version_sha)
    if summary:
        lines += ["%s x%d" % (label, n) for label, n in summary]
    else:
        lines.append("No reactions recorded.")

    rows = [[("Rewrite", "rewrite:%s" % sid)],
            [("Hold", "hold:%s" % sid), ("Back to drafts", "inbox:%s" % sid)]]

    run_dir = run_dir_of(session_row)
    state, _reason = DESK.publish_state(run_dir)
    if state == DESK.PUBLISH_ELIGIBLE and version_sha == STORE.sha256_text(
            DESK.article_text(run_dir)[0]):
        rows.insert(0, [("PUBLISH", "publish:%s" % sid)])
    send("\n".join(lines), chat=chat, buttons=rows)


# ── command handling ────────────────────────────────────────────────────────────────

def unopened_sessions() -> list:
    """Cards sent but never opened. A card the owner has not pressed READ on is still
    waiting for them, and /today must not report it as nothing."""
    opened = {e["session_id"] for e in STORE.events()
              if e["event_type"] == "READ_STARTED"}
    closed = closed_sessions()
    return [s for s in STORE.sessions()
            if s["session_id"] not in opened and s["session_id"] not in closed]


def cmd_today(chat):
    """The inbox. It lists; it never opens anything.

    Every row names one immutable version and carries its own button. There is no
    "current article" here and no resume-by-guess: if the desk cannot say which version
    an action is for, it shows this list instead.
    """
    for run in undelivered():
        offer(run, chat=chat)

    rows = ACT.inbox()
    if not rows:
        send("Nothing on the desk.", chat=chat)
        return

    lines, buttons, shown = ["Waiting for you", ""], [], 0
    for r in rows:
        if r["status"] == ACT.HELD and shown >= 6:
            continue
        if shown >= 8:
            break
        shown += 1
        lines.append(r["label"])
        lines.append("  %s" % r["title"])
        bits = []
        if r["words"]:
            bits.append("%d words" % r["words"])
        if r["reason"] == STORE.REASON_EDITORIAL_REWRITE:
            bits.append("rewrite")
        if r["summary"]:
            bits.append(" · ".join("%s x%d" % (lbl, n) for lbl, n in r["summary"][:3]))
        if bits:
            lines.append("  " + " · ".join(bits))
        lines.append("")
        if r["status"] == ACT.UNREAD:
            buttons.append([("READ: %s" % r["title"][:28], "read:%s" % r["session_id"])])
        elif r["status"] == ACT.READING:
            buttons.append([("RESUME: %s" % r["title"][:26],
                             "read:%s" % r["session_id"])])
        elif r["status"] == ACT.FINISHED:
            buttons.append([("Rewrite: %s" % r["title"][:24],
                             "rewrite:%s" % r["session_id"]),
                            ("Hold", "hold:%s" % r["session_id"])])
    more = len(rows) - shown
    if more > 0:
        lines.append("%d more" % more)
    send("\n".join(lines).rstrip(), chat=chat, buttons=buttons or None)


def cmd_backlog(chat):
    known = {s["run_id"] for s in STORE.sessions()}
    lines, n = ["Finished articles from earlier runs:"], 0
    for d in DESK.scan(limit=60):
        run = DESK.read_run(d)
        if run["state"] != DESK.REVIEWABLE_DRAFT:
            continue
        n += 1
        mark = "read" if d.name in known else "NEW"
        lines.append("  [%s] %s — %d words — %s"
                     % (mark, d.name[11:19], run["words"], DESK.status_line(run)))
        if n >= 20:
            break
    send("\n".join(lines) if n else "No finished articles retained.", chat=chat)


def short_title(session_row) -> str:
    """The title recorded when this card was sent. Read from the card's own event, not
    re-derived, so what the desk calls an article never drifts from what it showed."""
    for e in reversed(STORE.session_events(session_row["session_id"])):
        if e["event_type"] == "CARD_SENT" and (e.get("metadata") or {}).get("title"):
            return e["metadata"]["title"]
    text, _ = open_article(session_row)
    return title_of(run_dir_of(session_row), text or "")


def cmd_read(chat, session_row):
    """Read the article this button belongs to. Never 'the current one'."""
    if not session_row:
        # No explicit version means no article. Show the inbox rather than resolve
        # through newest/latest/current -- that heuristic is what made /today lie.
        cmd_today(chat)
        return
    text, sha = open_article(session_row)
    if text is None:
        send("I can't open that article safely: %s. Nothing sent." % sha, chat=chat)
        return
    at = cursor(session_row["session_id"], sha)
    if not at:
        STORE.record_event(session=session_row["session_id"],
                           run_id=session_row["run_id"], event_type="READ_STARTED",
                           actor="owner", version_sha=sha, chat_id=chat,
                           dedupe_key="read:%s:%s" % (session_row["session_id"], sha))
        # The article names itself before its first block. A silent mismatch between
        # the card pressed and the article delivered is what the 2026-09-26 incident
        # was, and a reader should be able to see it without reading the log.
        send("Reading: %s" % short_title(session_row), chat=chat)
    send_block(session_row, sha, at + 1, chat=chat)


def cmd_brief(chat, session_row):
    if not session_row:
        send("No article open.", chat=chat)
        return
    send(ACT.brief_for(session_row["session_id"],
                       session_row["origin_version_sha256"]), chat=chat)


def cmd_status(chat, session_row):
    if not session_row:
        send("No article open. /today to see what's waiting.", chat=chat)
        return
    text, sha = open_article(session_row)
    if text is None:
        send("That article cannot be opened: %s" % sha, chat=chat)
        return
    at = cursor(session_row["session_id"], sha)
    total = len(DESK.split_blocks(text))
    run = DESK.read_run(run_dir_of(session_row))
    send("Open: %s\nYou're at block %d of %d.\n%s"
         % (short_title(session_row), at, total, DESK.status_line(run)),
         chat=chat)


def cmd_debug(chat, session_row):
    if not session_row:
        send("No article open.", chat=chat)
        return
    run = DESK.read_run(run_dir_of(session_row))
    send(json.dumps({"run_id": run["run_id"],
                     "session_id": session_row["session_id"],
                     "version_sha256": session_row["origin_version_sha256"][:16],
                     "words": run["words"], "publish_state": run["publish_state"],
                     "publish_reason": run["publish_reason"],
                     "gates": run["gates"]}, indent=2, default=str)[:3800], chat=chat)


def cmd_hold(chat, session_row):
    if not session_row:
        send("Nothing open.", chat=chat)
        return
    STORE.record_event(session=session_row["session_id"],
                       run_id=session_row["run_id"], event_type="HOLD", actor="owner",
                       version_sha=session_row["origin_version_sha256"], chat_id=chat)
    send("Held: %s. It stays on the desk — /backlog to find it again."
         % short_title(session_row), chat=chat)


def cmd_rewrite(chat, user_id, session_row):
    if not session_row:
        cmd_today(chat)
        return
    if not ACT.authorized(user_id):
        send("Not authorized.", chat=chat)
        return
    text, sha = open_article(session_row)
    if text is None:
        send("That article cannot be opened: %s" % sha, chat=chat)
        return
    run_dir = run_dir_of(session_row)
    evidence = DESK.licensed_evidence(run_dir)
    send("Working from your reading of %s. One rewrite, then the factual checks."
         % short_title(session_row), chat=chat)
    out = ACT.request_rewrite(
        session_id=session_row["session_id"], run_id=session_row["run_id"],
        version_sha=sha, user_id=user_id, chat_id=chat,
        rewrite_fn=lambda t, b: rewrite_once(t, b, evidence),
        run_dir=run_dir)
    if out["status"] != ACT.REWRITE_DONE:
        send("No rewrite: %s" % out.get("detail", out["status"]), chat=chat)
        return

    v = out.get("recheck") or {}
    if v.get("cleared"):
        head = "Rewritten, and it passed the factual checks."
    elif v.get("status") == "BLOCKED_ADDED_MATERIAL":
        head = ("Rewritten, but BLOCKED: the edit added material the evidence does not "
                "carry. You can read it; it is not factually cleared.")
    elif v.get("status") == "BLOCKED_UNSUPPORTED":
        head = ("Rewritten, but BLOCKED: some of it is not supported by the evidence. "
                "You can read it; it is not factually cleared.")
    else:
        head = ("Rewritten, but NOT CHECKED: %s. You can read it; it is not factually "
                "cleared." % (v.get("reason") or "the checks could not run"))
    send(head, chat=chat)
    for b in DESK.split_blocks(out["text"]):
        send("%d/%d\n\n%s" % (b["index"], b["of"], b["text"]), chat=chat)
    send("That version is on the desk as its own draft. /today to see it.", chat=chat)


def cmd_publish(chat, user_id, session_row):
    if not session_row:
        send("No article open.", chat=chat)
        return
    text, sha = open_article(session_row)
    if text is None:
        send("Refusing to publish: %s" % sha, chat=chat)
        return
    a = ACT.approve(session_id=session_row["session_id"], run_id=session_row["run_id"],
                    version_sha=sha, user_id=user_id, chat_id=chat)
    if not a["ok"]:
        send("Not authorized.", chat=chat)
        return
    r = ACT.publish(session_id=session_row["session_id"], run_id=session_row["run_id"],
                    run_dir=run_dir_of(session_row), version_sha=sha, user_id=user_id,
                    chat_id=chat)
    if r["ok"] and r.get("idempotent"):
        send("Already published.", chat=chat)
    elif r["ok"]:
        send("Published: %s" % short_title(session_row), chat=chat)
    else:
        send("Not published: %s" % r["detail"], chat=chat)


def rewrite_once(article_text: str, brief: str, evidence=None) -> str:
    """The single editorial rewrite call, on the existing provider abstraction.

    `evidence` is the run's own frozen Ledger propositions. Without it the model was
    asked to give a passage "more room" with nothing licensed to fill it, and filled it
    with invention. See editorial_desk.REWRITE_SYSTEM for the contract it is held to.

    Imported lazily so the bot starts, polls and delivers articles on a machine where
    no provider is reachable: reading must never depend on the rewriter.
    """
    from new_engine_v1.provider import Provider, DEFAULT_MODEL
    p = Provider(model=DEFAULT_MODEL)
    return p.complete(system=DESK.REWRITE_SYSTEM,
                      user=DESK.rewrite_user(article_text, brief, evidence or []),
                      max_tokens=6000).text


# ── update dispatch ─────────────────────────────────────────────────────────────────

def handle_callback(cb):
    """Every button carries the identity of the article it belongs to, and that
    identity is what gets used. There is no fallback to 'the current article'.

    The 2026-09-26 incident was exactly the missing half of this function: the session
    was resolved correctly from `callback_data` on the line below, and then thrown away
    by calling a command that re-derived it from the newest delivery. A card whose
    session cannot be found now refuses; it never resolves to a different article.
    """
    data = cb.get("data") or ""
    user_id = (cb.get("from") or {}).get("id")
    chat = ((cb.get("message") or {}).get("chat") or {}).get("id") or CHAT_ID
    if not ACT.authorized(user_id):
        answer_callback(cb["id"], "Not authorized")
        return
    parts = data.split(":")
    kind, sid = parts[0], (parts[1] if len(parts) > 1 else "")
    s = STORE.session(sid)
    if not s:
        answer_callback(cb["id"], "I can't identify that card — nothing sent")
        log("REFUSED callback %r: no session %r" % (kind, sid))
        return
    sha = s["origin_version_sha256"]
    answer_callback(cb["id"])

    if kind == "inbox":
        cmd_today(chat)
        return
    if kind == "read":
        cmd_read(chat, s)
        return
    if kind == "hold":
        cmd_hold(chat, s)
        return
    if kind == "rewrite":
        cmd_rewrite(chat, user_id, s)
        return
    if kind == "publish":
        cmd_publish(chat, user_id, s)
        return
    if kind in ("almost", "notgood"):
        STORE.record_event(session=sid, run_id=s["run_id"],
                           event_type="ALMOST" if kind == "almost" else "NOT_GOOD",
                           actor=ACT.actor_of(user_id), version_sha=sha, chat_id=chat,
                           dedupe_key="verdict:%s:%s" % (sid, kind))
        send("Noted. /rewrite to act on your reading, or /hold.", chat=chat)
        return
    # ── navigation: carries the reader, records no judgement ────────────────────
    if kind in DESK.NAVIGATION:
        at = cursor(sid, sha)
        target = at + 1 if kind == "NEXT" else max(1, at - 1)
        if kind == "BACK" and at <= 1:
            send("You are at the beginning.", chat=chat)
            return
        STORE.record_event(session=sid, run_id=s["run_id"], event_type=kind,
                           actor=ACT.actor_of(user_id), version_sha=sha, chat_id=chat,
                           dedupe_key="nav:%s" % cb["id"],
                           metadata={"from_index": at, "to_index": target})
        send_block(s, sha, target, chat=chat)
        return

    # ── the optional second press: which KIND ───────────────────────────────────
    if kind == "d":
        # d:<sid>:<block>:<D|R>:<DETAIL>
        if len(parts) < 5:
            return
        block_id, tag, detail = parts[2], parts[3], parts[4]
        action = {"D": "TOO_DENSE", "R": "SOUNDS_LIKE_REPORT"}.get(tag, "")
        if action not in DESK.DETAIL_OPTIONS or detail not in DESK.DETAIL_SIGNALS:
            return
        blk = next((b for b in sent_blocks(sid, sha) if b["block_id"] == block_id), None)
        if blk is None:
            answer_callback(cb["id"], "I can't place that passage")
            return
        ACT.react(session_id=sid, run_id=s["run_id"], version_sha=sha,
                  event_type="FEEDBACK_DETAIL", user_id=user_id, chat_id=chat,
                  block=blk, detail=detail, dedupe_key="cb:%s" % cb["id"],
                  metadata={"of_action": action})
        answer_callback(cb["id"], "Saved: %s" % detail.replace("_", " ").lower())
        msg_id = ((cb.get("message") or {}).get("message_id"))
        if msg_id:
            edit_markup(chat, msg_id, block_keyboard(sid, block_id))
        return

    # ── a reaction: recorded, and the reader stays where they are ───────────────
    if kind in DESK.BUTTON_SIGNALS:
        block_id = parts[2] if len(parts) > 2 else ""
        blk = next((b for b in sent_blocks(sid, sha) if b["block_id"] == block_id), None)
        if blk is None:
            # A reaction whose block cannot be located is not filed against a guess.
            answer_callback(cb["id"], "I can't place that passage")
            log("REFUSED reaction %r: no block %r in session %s" % (kind, block_id, sid))
            return
        recorded = ACT.react(session_id=sid, run_id=s["run_id"], version_sha=sha,
                             event_type=kind, user_id=user_id, chat_id=chat,
                             block=blk, dedupe_key="cb:%s" % cb["id"])
        if recorded is None:
            # A REDELIVERED PRESS IS THE SAME PRESS. Found by the route audit 2026-09-26.
            return
        # ACKNOWLEDGE ON THE BUTTON, NOT IN THE CHAT. A confirmation message after
        # every press turns the thing the reader is reading into an event log, and the
        # reading is what we are here to observe.
        label = kind.replace("_", " ").lower()
        if kind in DESK.DETAIL_OPTIONS:
            # The press is already stored; this only asks which kind, and saying
            # nothing is a complete answer. The keyboard is swapped in place.
            answer_callback(cb["id"], "Saved: %s - which part?" % label)
            msg_id = ((cb.get("message") or {}).get("message_id"))
            if msg_id:
                edit_markup(chat, msg_id, detail_keyboard(kind, sid, blk["block_id"]))
        elif kind == "READER_LOST":
            answer_callback(cb["id"], "Saved. Type what lost you, or press Next.")
        else:
            answer_callback(cb["id"], "Saved: %s" % label)


def handle_message(msg):
    user_id = (msg.get("from") or {}).get("id")
    chat = (msg.get("chat") or {}).get("id")
    text = (msg.get("text") or "").strip()
    if not ACT.authorized(user_id):
        return
    if not text:
        return
    cmd = text.split()[0].lower().split("@")[0]
    # A typed command has no card behind it, so it acts on the article the owner
    # actually OPENED -- see reading_session(). With nothing open, each of these says
    # so rather than picking one.
    s = reading_session()
    table = {"/today": lambda: cmd_today(chat), "/start": lambda: cmd_today(chat),
             "/backlog": lambda: cmd_backlog(chat),
             "/read": lambda: cmd_read(chat, s), "/next": lambda: cmd_read(chat, s),
             "/brief": lambda: cmd_brief(chat, s),
             "/status": lambda: cmd_status(chat, s),
             "/debug": lambda: cmd_debug(chat, s),
             "/hold": lambda: cmd_hold(chat, s),
             "/rewrite": lambda: cmd_rewrite(chat, user_id, s),
             "/publish": lambda: cmd_publish(chat, user_id, s),
             "/help": lambda: send(HELP, chat=chat)}
    if cmd in table:
        table[cmd]()
        return

    # Anything else is editorial feedback. A REPLY carries its own identity: the block
    # row names the session and the version, so the article is read off the passage
    # replied to rather than from any notion of what is current. Only a plain message
    # falls back to the open article, and is marked as an inferred binding.
    reply_to = (msg.get("reply_to_message") or {}).get("message_id")
    blk = STORE.block_for_message(chat, reply_to) if reply_to else None
    if blk is not None:
        target = STORE.session(blk["session_id"])
        sha = blk["version_sha256"]
        binding = "REPLY"
    else:
        target, blk, binding = s, None, "NO_BLOCK"
        if target:
            sha = target["origin_version_sha256"]
            done = sent_blocks(target["session_id"], sha)
            if done:
                blk, binding = done[-1], "LAST_BLOCK_SENT"
    if not target:
        send("Nothing open to comment on. /today", chat=chat)
        return
    ACT.react(session_id=target["session_id"], run_id=target["run_id"],
              version_sha=sha, event_type="FREE_TEXT_FEEDBACK", user_id=user_id,
              chat_id=chat, message_id=msg.get("message_id"), block=blk,
              raw_feedback=text, reply_to_message_id=reply_to,
              dedupe_key="msg:%s:%s" % (chat, msg.get("message_id")),
              metadata={"binding": binding})
    send("Saved.", chat=chat)


def poll_once(offset: int) -> int:
    r = tg("getUpdates", {"offset": offset, "timeout": POLL_TIMEOUT,
                          "allowed_updates": ["message", "callback_query"]},
           timeout=POLL_TIMEOUT + 10)
    if not r or not r.get("ok"):
        return offset
    for u in r.get("result", []):
        offset = u["update_id"] + 1
        try:
            if "callback_query" in u:
                handle_callback(u["callback_query"])
            elif "message" in u:
                handle_message(u["message"])
        except Exception as e:                                        # noqa: BLE001
            # One bad update must never stop the desk. The offset has already advanced,
            # so a message that crashes the handler is not retried forever.
            log("update %s failed: %s: %s" % (u.get("update_id"), type(e).__name__,
                                              str(e)[:200]))
        _save_offset(offset)
    return offset


def _load_offset() -> int:
    try:
        return int(OFFSET_FILE.read_text().strip())
    except Exception:
        return 0


def _save_offset(offset: int):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        OFFSET_FILE.write_text(str(offset))
    except Exception as e:                                            # noqa: BLE001
        log("save_offset: %s" % e)


def _stop(*_):
    global running
    running = False


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lock = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("another desk bot is running; exiting")
        return 1
    load_secrets()
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    log("editorial desk online")
    offset = _load_offset()
    while running:
        try:
            offset = poll_once(offset)
        except Exception as e:                                        # noqa: BLE001
            log("poll failed: %s: %s" % (type(e).__name__, str(e)[:200]))
            time.sleep(5)
    log("editorial desk stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
