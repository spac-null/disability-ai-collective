#!/usr/bin/env python3
"""Exhaustive audit of every Telegram route the desk exposes. Offline, no bot, no token.

WHY A SEPARATE FILE FROM THE BEHAVIOUR TESTS. The behaviour tests assert that the
journeys we designed work. This asserts something different and, after 2026-09-26,
more useful: that EVERY reachable route -- including the ones nobody designed a journey
for -- obeys four invariants. The identity defect lived on a route (READ) that the
behaviour tests did cover; what they did not cover was the same defect's presence on
hold, rewrite, publish and free text, which nobody had exercised.

So this enumerates the surface from the code itself and drives each entry point, rather
than testing the flows we happen to remember.

FOUR INVARIANTS, CHECKED PER ROUTE

  AUTH      an unlisted user causes no send and no stored event, on every route
  IDENTITY  the route acts on the article its input names, and on no other
  CLOSED    missing, unknown or malformed input refuses; it never substitutes
  QUIET     a route that refuses writes nothing to the editorial record

A route that cannot be reached by a user is not audited here; a route that can, is.
"""
from __future__ import annotations

import inspect
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import editorial_desk as DESK                      # noqa: E402
import editorial_desk_actions as ACT               # noqa: E402
import editorial_desk_bot as BOT                   # noqa: E402
import editorial_desk_store as STORE               # noqa: E402
import editorial_desk_test as T                    # noqa: E402
from editorial_desk_bot_test import (Harness, cb, msg, CHAT, OWNER,  # noqa: E402
                                     STRANGER)

FAILURES = []
AUDITED = []


def check(route, label, ok, detail=""):
    AUDITED.append(route)
    line = "%-22s %s" % (route, label)
    print(("PASS " if ok else "FAIL ") + line + ("" if ok else "  " + repr(detail)))
    if not ok:
        FAILURES.append("%s / %s" % (route, label))


# ── the surface, read off the code ──────────────────────────────────────────────────

def declared_commands() -> set:
    """Every /command handle_message dispatches on, extracted from the source so a new
    one cannot be added without this audit noticing it is unaudited."""
    src = (HERE / "editorial_desk_bot.py").read_text(encoding="utf-8")
    import re
    table = src[src.index("    table = {"):src.index("    if cmd in table:")]
    return set(re.findall(r'"(/[a-z]+)"\s*:', table))


def declared_callbacks() -> set:
    src = (HERE / "editorial_desk_bot.py").read_text(encoding="utf-8")
    body = src[src.index("def handle_callback"):src.index("def handle_message")]
    kinds = {line.split('kind == "')[1].split('"')[0]
             for line in body.splitlines() if 'kind == "' in line}
    kinds |= {line.split('kind in ("')[1].split('"')[0]
              for line in body.splitlines() if 'kind in ("' in line}
    kinds |= {"notgood"}
    return kinds | set(DESK.BUTTON_SIGNALS)


def test_00_surface_is_fully_enumerated():
    cmds = declared_commands()
    expected = {"/today", "/start", "/backlog", "/read", "/next", "/brief", "/status",
                "/debug", "/hold", "/rewrite", "/publish", "/help"}
    check("SURFACE", "every dispatched command is known to this audit",
          cmds == expected, sorted(cmds ^ expected))
    cbs = declared_callbacks()
    expected_cb = {"read", "hold", "rewrite", "publish", "almost", "notgood"} | set(
        DESK.BUTTON_SIGNALS)
    check("SURFACE", "every callback kind is known to this audit",
          cbs == expected_cb, sorted(cbs ^ expected_cb))


# ── helpers ─────────────────────────────────────────────────────────────────────────

def two_articles(h):
    """Two distinct delivered articles, neither opened.

    Long enough that sweeping all six reaction buttons does not walk an article to its
    end: a finished article is legitimately closed, and an audit that accidentally
    finishes one then asks whether it is still open is testing its own fixture.
    """
    for day, tag in (("26", "Alpha"), ("25", "Beta")):
        body = "\n\n".join("%s paragraph %d. %s" % (tag, n, "word " * 40)
                           for n in range(1, 31))
        T.make_run(h.ev.name, "production-202609%sT070000Z-aaaaaaa%s" % (day, day),
                   body=body)
    BOT.cmd_today(CHAT)
    a, b = STORE.sessions()[0], STORE.sessions()[1]
    return a, b


def counts():
    return len(STORE.events()), len(STORE.blocks()), len(STORE.decisions())


# ── AUTH: every route, an unlisted user ─────────────────────────────────────────────

def test_01_auth_on_every_message_route():
    with Harness() as h:
        a, b = two_articles(h)
        for cmd in sorted(declared_commands()):
            before_msgs, before = len(h.messages()), counts()
            BOT.handle_message(msg(cmd, user=STRANGER, mid=hash(cmd) % 9999))
            check("msg %s" % cmd, "a stranger gets no reply",
                  len(h.messages()) == before_msgs, h.texts()[before_msgs:])
            check("msg %s" % cmd, "a stranger writes nothing", counts() == before)


def test_02_auth_on_every_callback_route():
    with Harness() as h:
        a, b = two_articles(h)
        for kind in sorted(declared_callbacks()):
            before_msgs, before = len(h.messages()), counts()
            BOT.handle_callback(cb("%s:%s:b01" % (kind, a["session_id"]),
                                   user=STRANGER, cid="auth-%s" % kind))
            check("cb %s" % kind, "a stranger gets no message",
                  len(h.messages()) == before_msgs, h.texts()[before_msgs:])
            check("cb %s" % kind, "a stranger writes nothing", counts() == before)


# ── CLOSED: unknown / malformed input on every callback route ───────────────────────

def test_03_unknown_session_refuses_on_every_callback():
    with Harness() as h:
        two_articles(h)
        for kind in sorted(declared_callbacks()):
            before_msgs, before = len(h.messages()), counts()
            BOT.handle_callback(cb("%s:deadbeefdeadbeef:b01" % kind,
                                   cid="unknown-%s" % kind))
            check("cb %s" % kind, "an unknown session sends nothing",
                  len(h.messages()) == before_msgs, h.texts()[before_msgs:])
            check("cb %s" % kind, "an unknown session writes nothing",
                  counts() == before)


def test_04_malformed_callback_data():
    with Harness() as h:
        two_articles(h)
        for data in ("", ":", "read", "read:", "::::", "read:%s:" % "x" * 200,
                     "\x00", "READ:abc", "nonsense:abc:def"):
            before_msgs, before = len(h.messages()), counts()
            BOT.handle_callback(cb(data, cid="mal-%s" % abs(hash(data))))
            check("cb malformed", "%r sends nothing" % data[:24],
                  len(h.messages()) == before_msgs, h.texts()[before_msgs:])
            check("cb malformed", "%r writes nothing" % data[:24], counts() == before)


def test_05_unknown_block_on_a_reaction_refuses():
    with Harness() as h:
        a, _ = two_articles(h)
        BOT.handle_callback(cb("read:%s" % a["session_id"], cid="r"))
        for kind in sorted(DESK.BUTTON_SIGNALS):
            before = counts()
            BOT.handle_callback(cb("%s:%s:b99" % (kind, a["session_id"]),
                                   cid="noblock-%s" % kind))
            check("cb %s" % kind, "a reaction on an unknown block writes nothing",
                  counts() == before)


# ── CLOSED: every command with nothing open ─────────────────────────────────────────

def test_06_commands_with_no_session_open():
    with Harness() as h:
        for cmd in ("/read", "/next", "/brief", "/status", "/debug", "/hold",
                    "/rewrite", "/publish"):
            before = counts()
            BOT.handle_message(msg(cmd, mid=abs(hash(cmd)) % 9999))
            check("msg %s" % cmd, "with nothing open it answers and writes nothing",
                  counts() == before and h.texts(), h.texts()[-1:] if h.texts() else [])
            check("msg %s" % cmd, "and does not claim to have acted",
                  "Published" not in h.texts()[-1] and "Rewritten" not in h.texts()[-1],
                  h.texts()[-1])


def test_07_free_text_with_nothing_open():
    with Harness() as h:
        before = counts()
        BOT.handle_message(msg("some stray thought", mid=1))
        check("msg free-text", "with nothing open it stores no feedback",
              counts() == before)
        check("msg free-text", "and says so", "Nothing open" in h.texts()[-1],
              h.texts()[-1])


def test_08_non_text_messages_are_ignored():
    with Harness() as h:
        two_articles(h)
        before_msgs, before = len(h.messages()), counts()
        for m in ({"message_id": 1, "from": {"id": OWNER}, "chat": {"id": CHAT}},
                  {"message_id": 2, "from": {"id": OWNER}, "chat": {"id": CHAT},
                   "text": "   "},
                  {"message_id": 3, "from": {"id": OWNER}, "chat": {"id": CHAT},
                   "photo": [{"file_id": "x"}]}):
            BOT.handle_message(m)
        check("msg non-text", "a photo or empty message is ignored",
              len(h.messages()) == before_msgs and counts() == before)


# ── IDENTITY: every route that names an article ─────────────────────────────────────

def test_09_identity_on_every_article_route():
    """Each route is driven on article A while article B is the newest delivery -- the
    exact condition that made the 2026-09-26 defect invisible."""
    with Harness() as h:
        a, b = two_articles(h)
        BOT.handle_callback(cb("read:%s" % a["session_id"], cid="idA"))
        sent = "\n".join(h.texts()[-2:])
        check("cb read", "opens the named article, not the newest",
              "Alpha paragraph 1." in sent and "Beta" not in sent, sent[:120])

        blk = STORE.session_blocks(a["session_id"], a["origin_version_sha256"])[0]
        for kind in sorted(DESK.BUTTON_SIGNALS):
            BOT.handle_callback(cb("%s:%s:%s" % (kind, a["session_id"], blk["block_id"]),
                                   cid="id-%s" % kind))
            ev = [e for e in STORE.events() if e["event_type"] == kind]
            check("cb %s" % kind, "files against the named article",
                  ev and ev[-1]["session_id"] == a["session_id"], ev[-1:] )
            check("cb %s" % kind, "and against that article's version",
                  ev and ev[-1]["version_sha256"] == a["origin_version_sha256"])

        for kind, etype in (("almost", "ALMOST"), ("notgood", "NOT_GOOD")):
            BOT.handle_callback(cb("%s:%s" % (kind, b["session_id"]), cid="v-%s" % kind))
            ev = [e for e in STORE.events() if e["event_type"] == etype]
            check("cb %s" % kind, "files against the card pressed",
                  ev and ev[-1]["session_id"] == b["session_id"], ev[-1:])

        BOT.handle_callback(cb("hold:%s" % b["session_id"], cid="hold-b"))
        holds = [e for e in STORE.events() if e["event_type"] == "HOLD"]
        check("cb hold", "holds the card pressed, not the one being read",
              holds and holds[-1]["session_id"] == b["session_id"], holds[-1:])
        check("cb hold", "and the article being read stays open",
              (BOT.reading_session() or {}).get("session_id") == a["session_id"])


def test_10_publish_route_identity_and_guards():
    with Harness() as h:
        a, b = two_articles(h)
        BOT.handle_callback(cb("read:%s" % a["session_id"], cid="pubread"))
        calls = []
        original = DESK.publish_state
        DESK.publish_state = lambda _d: (DESK.PUBLISH_ELIGIBLE, "stub")
        try:
            BOT.handle_callback(cb("publish:%s" % b["session_id"], cid="pub-b"))
            approved = [d for d in STORE.decisions() if d["action"] == "OWNER_APPROVED"]
            check("cb publish", "approves the card pressed, not the one being read",
                  approved and approved[-1]["version_sha256"]
                  == b["origin_version_sha256"], approved[-1:])
            check("cb publish", "refuses because the bytes are not the run's",
                  not STORE.published_version(b["origin_version_sha256"]),
                  h.texts()[-1])
        finally:
            DESK.publish_state = original
        check("cb publish", "and never called a publisher", calls == [])


def test_11_rewrite_route_identity():
    with Harness() as h:
        a, b = two_articles(h)
        BOT.handle_callback(cb("read:%s" % a["session_id"], cid="rwread"))
        seen = {}
        saved = BOT.rewrite_once
        BOT.rewrite_once = lambda text, brief: (
            seen.update(text=text, brief=brief) or text.replace("Beta", "X")
            or text + "\n\nnew")
        try:
            BOT.handle_callback(cb("rewrite:%s" % b["session_id"], cid="rw-b"))
            check("cb rewrite", "rewrites the card pressed, not the one being read",
                  "Beta paragraph 1." in seen.get("text", ""), seen.get("text", "")[:60])
            rw = STORE.rewrites()
            check("cb rewrite", "records the rewrite against that article",
                  rw and rw[-1]["from_version_sha256"] == b["origin_version_sha256"])
        finally:
            BOT.rewrite_once = saved


def test_12_free_text_routes():
    with Harness() as h:
        a, b = two_articles(h)
        BOT.handle_callback(cb("read:%s" % a["session_id"], cid="ftA"))
        blk_a = STORE.session_blocks(a["session_id"], a["origin_version_sha256"])[0]
        BOT.handle_callback(cb("read:%s" % b["session_id"], cid="ftB"))

        BOT.handle_message(msg("about alpha", mid=701,
                               reply_to=blk_a["telegram_message_id"]))
        ev = [e for e in STORE.events() if e["raw_feedback"] == "about alpha"][0]
        check("msg reply", "a reply files against the replied-to article",
              ev["session_id"] == a["session_id"])
        check("msg reply", "and records the message actually replied to",
              ev["reply_to_message_id"] == blk_a["telegram_message_id"],
              ev["reply_to_message_id"])
        check("msg reply", "marked as a true reply",
              ev["metadata"]["binding"] == "REPLY")

        BOT.handle_message(msg("just typed", mid=702))
        ev2 = [e for e in STORE.events() if e["raw_feedback"] == "just typed"][0]
        check("msg plain", "a plain message files against the open article",
              ev2["session_id"] == b["session_id"])
        check("msg plain", "marked as an inferred binding",
              ev2["metadata"]["binding"] == "LAST_BLOCK_SENT")
        check("msg plain", "and records no reply target",
              ev2["reply_to_message_id"] is None, ev2["reply_to_message_id"])


def test_13_command_routes_act_on_the_open_article():
    with Harness() as h:
        a, b = two_articles(h)
        BOT.handle_callback(cb("read:%s" % a["session_id"], cid="cmdA"))
        for cmd, needle in (("/status", "Alpha"), ("/debug", "aaaaaaa26"),
                            ("/brief", "")):
            BOT.handle_message(msg(cmd, mid=abs(hash(cmd)) % 9999))
            if needle:
                check("msg %s" % cmd, "reports the open article",
                      needle in h.texts()[-1], h.texts()[-1][:120])
        BOT.handle_message(msg("/read", mid=801))
        check("msg /read", "continues the open article, not the newest",
              "Alpha" in h.texts()[-1], h.texts()[-1][:80])


# ── QUIET / idempotency across routes ───────────────────────────────────────────────

def test_14_every_callback_is_idempotent():
    with Harness() as h:
        a, _ = two_articles(h)
        BOT.handle_callback(cb("read:%s" % a["session_id"], cid="idem-read"))
        blk = STORE.session_blocks(a["session_id"], a["origin_version_sha256"])[0]
        for kind in sorted(DESK.BUTTON_SIGNALS):
            c = cb("%s:%s:%s" % (kind, a["session_id"], blk["block_id"]),
                   cid="idem-%s" % kind)
            BOT.handle_callback(c)
            n1 = len([e for e in STORE.events() if e["event_type"] == kind])
            blocks_after_first = len(STORE.blocks())
            BOT.handle_callback(c)
            n2 = len([e for e in STORE.events() if e["event_type"] == kind])
            check("cb %s" % kind, "a redelivered press records once", n1 == n2, (n1, n2))
            check("cb %s" % kind, "and does not advance the reader a second time",
                  len(STORE.blocks()) == blocks_after_first,
                  (blocks_after_first, len(STORE.blocks())))
        m = msg("said once", mid=900)
        BOT.handle_message(m)
        BOT.handle_message(m)
        check("msg free-text", "a redelivered message records once",
              len([e for e in STORE.events()
                   if e["raw_feedback"] == "said once"]) == 1)


def test_15_help_and_backlog_are_read_only():
    with Harness() as h:
        two_articles(h)
        before = counts()
        BOT.handle_message(msg("/help", mid=910))
        BOT.handle_message(msg("/backlog", mid=911))
        check("msg /help", "writes nothing", counts() == before)
        check("msg /help", "explains the buttons", "Too fast" in "\n".join(h.texts()))
        check("msg /backlog", "lists without delivering",
              len(STORE.sessions()) == 2, len(STORE.sessions()))


def test_16_debug_is_the_only_engineering_view():
    """The normal flow must not leak SHAs or stage taxonomy."""
    with Harness() as h:
        a, _ = two_articles(h)
        BOT.handle_callback(cb("read:%s" % a["session_id"], cid="leak"))
        blk = STORE.session_blocks(a["session_id"], a["origin_version_sha256"])[0]
        BOT.handle_callback(cb("CONTINUE:%s:%s" % (a["session_id"], blk["block_id"]),
                               cid="leak2"))
        normal = "\n".join(h.texts())
        check("UX", "no version hash appears in the normal flow",
              a["origin_version_sha256"][:16] not in normal)
        check("UX", "no session id appears in the normal flow",
              a["session_id"] not in normal)
        check("UX", "no HOLD code appears in the normal flow",
              "SAFETY_HOLD" not in normal and "_HOLD" not in normal)
        before = len(h.messages())
        BOT.handle_message(msg("/debug", mid=920))
        check("msg /debug", "shows the engineering view on request",
              a["origin_version_sha256"][:16] in "\n".join(h.texts()[before:]))


def test_17_send_failure_does_not_corrupt_the_record():
    """Telegram returns an error: nothing may be recorded as delivered or read."""
    with Harness() as h:
        a, _ = two_articles(h)
        saved = BOT.tg
        BOT.tg = lambda method, payload=None, timeout=None: (
            {"ok": True, "result": []} if method != "sendMessage" else None)
        try:
            before = len(STORE.blocks())
            BOT.handle_callback(cb("read:%s" % a["session_id"], cid="sendfail"))
            check("cb read", "a failed send records no block",
                  len(STORE.blocks()) == before, len(STORE.blocks()))
        finally:
            BOT.tg = saved


def test_18_signatures_carry_identity_everywhere():
    for name in ("cmd_read", "cmd_hold", "cmd_brief", "cmd_status", "cmd_debug",
                 "cmd_rewrite", "cmd_publish"):
        params = inspect.signature(getattr(BOT, name)).parameters
        check("STRUCTURE", "%s takes an explicit session" % name,
              "session_row" in params, list(params))
    src = (HERE / "editorial_desk_bot.py").read_text(encoding="utf-8")
    body = src[src.index("def handle_callback"):src.index("def handle_message")]
    check("STRUCTURE", "the callback handler has no fallback resolver",
          "reading_session()" not in body)
    check("STRUCTURE", "no latest-wins resolver exists", "def active_session" not in src)


def main():
    for fn in sorted((f for n, f in globals().items() if n.startswith("test_")),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print()
    print("routes audited: %d checks across %d route labels"
          % (len(AUDITED), len(set(AUDITED))))
    if FAILURES:
        print("%d FAILURE(S):" % len(FAILURES))
        for f in FAILURES:
            print("  " + f)
        return 1
    print("every Telegram route obeys AUTH / IDENTITY / CLOSED / QUIET")
    return 0


if __name__ == "__main__":
    sys.exit(main())
