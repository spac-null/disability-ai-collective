#!/usr/bin/env python3
"""Offline regressions for the Telegram adapter. No token, no network, no bot running.

`tg()` is replaced by a recorder, so every assertion here is about what the desk WOULD
send and what it records while doing it.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import editorial_desk as DESK                      # noqa: E402
import editorial_desk_actions as ACT               # noqa: E402
import editorial_desk_bot as BOT                   # noqa: E402
import editorial_desk_store as STORE               # noqa: E402
import editorial_desk_test as T                    # noqa: E402

FAILURES = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else "  " + repr(detail)))
    if not ok:
        FAILURES.append(label)


OWNER = 4242
STRANGER = 9999
CHAT = 555


class Harness:
    """A temp evidence root, a temp store, and a fake Telegram."""

    def __enter__(self):
        self.ev = tempfile.TemporaryDirectory()
        self.st = tempfile.TemporaryDirectory()
        self._saved = (STORE.ROOT, DESK.EVIDENCE_ROOT, BOT.CHAT_ID, BOT.tg,
                       BOT.STATE_DIR)
        STORE.ROOT = pathlib.Path(self.st.name)
        DESK.EVIDENCE_ROOT = pathlib.Path(self.ev.name)
        BOT.CHAT_ID = str(CHAT)
        BOT.STATE_DIR = pathlib.Path(self.st.name)
        self.sent = []
        self.next_id = [900]

        def fake_tg(method, payload=None, timeout=None):
            self.sent.append((method, payload))
            if method == "sendMessage":
                self.next_id[0] += 1
                return {"ok": True, "result": {"message_id": self.next_id[0]}}
            return {"ok": True, "result": []}

        BOT.tg = fake_tg
        import os
        os.environ[ACT.ALLOWED_USERS_ENV] = str(OWNER)
        return self

    def __exit__(self, *a):
        (STORE.ROOT, DESK.EVIDENCE_ROOT, BOT.CHAT_ID, BOT.tg,
         BOT.STATE_DIR) = self._saved
        self.ev.cleanup()
        self.st.cleanup()

    def make_run(self, name="production-20260926T072441Z-66967ce4", **kw):
        return T.make_run(self.ev.name, name, **kw)

    def messages(self):
        return [p for m, p in self.sent if m == "sendMessage"]

    def texts(self):
        return [p["text"] for p in self.messages()]

    def last_markup(self):
        for p in reversed(self.messages()):
            if p.get("reply_markup"):
                return p["reply_markup"]
        return {}


def msg(text, *, user=OWNER, mid=1, reply_to=None):
    m = {"message_id": mid, "from": {"id": user}, "chat": {"id": CHAT}, "text": text}
    if reply_to:
        m["reply_to_message"] = {"message_id": reply_to}
    return m


def cb(data, *, user=OWNER, cid="cb-1"):
    return {"id": cid, "from": {"id": user}, "data": data,
            "message": {"chat": {"id": CHAT}}}


# ── delivery ────────────────────────────────────────────────────────────────────────

def test_today_offers_a_held_article():
    with Harness() as h:
        h.make_run()
        BOT.cmd_today(CHAT)
        txt = "\n".join(h.texts())
        check("today announces the waiting article", "1 article waiting" in txt, txt[:200])
        check("the card says it is readable",
              "Readable now" in txt, txt[:400])
        check("the card shows the flagged finding verbatim",
              "MACHINE_LANGUAGE" in txt, txt[:400])
        buttons = json.dumps(h.last_markup())
        check("the card offers READ and HOLD",
              "READ" in buttons and "HOLD" in buttons, buttons)
        check("one session was opened", len(STORE.sessions()) == 1)


def test_today_does_not_reoffer():
    with Harness() as h:
        h.make_run()
        BOT.cmd_today(CHAT)
        before = len(h.messages())
        BOT.cmd_today(CHAT)
        check("a delivered article is not offered again",
              len(STORE.sessions()) == 1, STORE.sessions())
        check("the second /today says nothing new",
              any("Nothing new" in t for t in h.texts()[before:]), h.texts()[before:])


def test_upstream_failure_is_not_offered_as_a_draft():
    with Harness() as h:
        h.make_run("production-empty", body="")
        BOT.cmd_today(CHAT)
        check("a run with no article opens no session", STORE.sessions() == [])
        check("and is reported as nothing waiting",
              any("Nothing waiting" in t for t in h.texts()), h.texts())


# ── reading ─────────────────────────────────────────────────────────────────────────

def _open_and_read(h):
    h.make_run()
    BOT.cmd_today(CHAT)
    BOT.cmd_read(CHAT)
    return STORE.sessions()[0]


def test_read_sends_one_block_with_buttons():
    with Harness() as h:
        s = _open_and_read(h)
        body = h.texts()[-1]
        check("the first block is numbered", body.startswith("1/"), body[:20])
        check("the first block is not the whole article",
              len(body) <= DESK.BLOCK_MAX_CHARS + 40, len(body))
        buttons = json.dumps(h.last_markup())
        for label in ("Continue", "Too fast", "Why now?", "Strong", "I'm lost",
                      "Want more"):
            check("block offers %r" % label, label in buttons)
        blocks = STORE.session_blocks(s["session_id"], s["origin_version_sha256"])
        check("the block was recorded with its message id",
              len(blocks) == 1 and blocks[0]["telegram_message_id"] == h.next_id[0],
              blocks)
        check("READ_STARTED was recorded once",
              len([e for e in STORE.events()
                   if e["event_type"] == "READ_STARTED"]) == 1)


def test_continue_advances_and_records():
    with Harness() as h:
        s = _open_and_read(h)
        sid = s["session_id"]
        blk = STORE.session_blocks(sid, s["origin_version_sha256"])[0]
        BOT.handle_callback(cb("CONTINUE:%s:%s" % (sid, blk["block_id"])))
        check("a second block was sent", h.texts()[-1].startswith("2/"), h.texts()[-1])
        ev = [e for e in STORE.events() if e["event_type"] == "CONTINUE"]
        check("the press was recorded once", len(ev) == 1)
        check("it is bound to the block it was made on",
              ev[0]["block_id"] == blk["block_id"])


def test_duplicate_callback_is_idempotent():
    with Harness() as h:
        s = _open_and_read(h)
        sid = s["session_id"]
        blk = STORE.session_blocks(sid, s["origin_version_sha256"])[0]
        c = cb("TOO_FAST:%s:%s" % (sid, blk["block_id"]), cid="same-id")
        BOT.handle_callback(c)
        BOT.handle_callback(c)
        check("a redelivered press is recorded once",
              len([e for e in STORE.events() if e["event_type"] == "TOO_FAST"]) == 1)


def test_reader_lost_stops_instead_of_advancing():
    with Harness() as h:
        s = _open_and_read(h)
        sid = s["session_id"]
        blk = STORE.session_blocks(sid, s["origin_version_sha256"])[0]
        before = len(STORE.session_blocks(sid, s["origin_version_sha256"]))
        BOT.handle_callback(cb("READER_LOST:%s:%s" % (sid, blk["block_id"])))
        after = len(STORE.session_blocks(sid, s["origin_version_sha256"]))
        check("'I'm lost' does not send the next block", after == before, (before, after))
        check("it asks what lost them", "What lost you" in h.texts()[-1], h.texts()[-1])


def test_reply_binds_to_the_exact_block():
    with Harness() as h:
        s = _open_and_read(h)
        sid = s["session_id"]
        blk = STORE.session_blocks(sid, s["origin_version_sha256"])[0]
        BOT.handle_message(msg("hier raak ik je kwijt", mid=77,
                               reply_to=blk["telegram_message_id"]))
        ev = [e for e in STORE.events() if e["event_type"] == "FREE_TEXT_FEEDBACK"]
        check("the reply was stored once", len(ev) == 1, ev)
        check("bound to the replied-to block", ev[0]["block_id"] == blk["block_id"])
        check("recorded as a true reply", ev[0]["metadata"]["binding"] == "REPLY")
        check("verbatim", ev[0]["raw_feedback"] == "hier raak ik je kwijt")


def test_plain_message_binds_to_the_last_block_and_says_so():
    with Harness() as h:
        s = _open_and_read(h)
        BOT.handle_message(msg("te veel namen ineens", mid=78))
        ev = [e for e in STORE.events() if e["event_type"] == "FREE_TEXT_FEEDBACK"][0]
        check("a plain message still lands on a block", ev["block_id"] is not None)
        check("and is marked as an inferred binding, not a reply",
              ev["metadata"]["binding"] == "LAST_BLOCK_SENT", ev["metadata"])


def test_reading_position_survives_a_restart():
    with Harness() as h:
        s = _open_and_read(h)
        sid = s["session_id"]
        blk = STORE.session_blocks(sid, s["origin_version_sha256"])[0]
        BOT.handle_callback(cb("CONTINUE:%s:%s" % (sid, blk["block_id"])))
        # Nothing in the bot process carries the cursor -- it is re-derived from the
        # blocks already sent, so simply calling /read again is the restart case.
        BOT.cmd_read(CHAT)
        check("reading resumes at the next unsent block",
              h.texts()[-1].startswith("3/"), h.texts()[-1][:20])


def test_finishing_offers_the_end_actions():
    with Harness() as h:
        s = _open_and_read(h)
        sid = s["session_id"]
        sha = s["origin_version_sha256"]
        total = len(DESK.split_blocks(STORE.read_version_bytes(sha)))
        for _ in range(total + 1):
            blocks = STORE.session_blocks(sid, sha)
            if not blocks:
                break
            BOT.handle_callback(cb("CONTINUE:%s:%s" % (sid, blocks[-1]["block_id"]),
                                   cid="c%d" % len(blocks)))
        check("the desk says the article is read",
              any("read it all" in t for t in h.texts()), h.texts()[-1][:120])
        check("ARTICLE_FINISHED was recorded",
              any(e["event_type"] == "ARTICLE_FINISHED" for e in STORE.events()))
        buttons = json.dumps(h.last_markup())
        check("a blocked article offers rewrite, not publish",
              "Rewrite from my feedback" in buttons and "PUBLISH" not in buttons,
              buttons)
        check("and says why it cannot publish",
              any("Cannot publish yet" in t for t in h.texts()), h.texts()[-1][:200])


# ── authorization ───────────────────────────────────────────────────────────────────

def test_a_stranger_gets_nothing():
    with Harness() as h:
        _open_and_read(h)
        before = len(h.messages()), len(STORE.events())
        BOT.handle_message(msg("give me the draft", user=STRANGER, mid=99))
        BOT.handle_callback(cb("CONTINUE:x:b01", user=STRANGER, cid="x"))
        check("no message was sent to a stranger", len(h.messages()) == before[0],
              h.texts()[before[0]:])
        check("nothing a stranger did was recorded",
              len(STORE.events()) == before[1])


def test_a_stranger_cannot_publish():
    with Harness() as h:
        s = _open_and_read(h)
        BOT.cmd_publish(CHAT, STRANGER)
        check("publish refuses an unlisted user",
              any("Not authorized" in t for t in h.texts()), h.texts()[-1])
        check("no approval was recorded",
              STORE.approved_version(s["origin_version_sha256"]) is None)


def test_publish_reports_the_publishers_refusal():
    with Harness() as h:
        s = _open_and_read(h)
        BOT.cmd_publish(CHAT, OWNER)
        last = h.texts()[-1]
        check("publish refuses and says why", last.startswith("Not published:"), last)
        check("the reason is the validator's, not the desk's",
              "missing required artifact" in last.lower() or "bridge" in last.lower(),
              last)
        check("nothing was published",
              STORE.published_version(s["origin_version_sha256"]) is None)


def main():
    for fn in sorted((f for n, f in globals().items() if n.startswith("test_")),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print()
    if FAILURES:
        print("%d FAILURE(S): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("all editorial-desk bot checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
