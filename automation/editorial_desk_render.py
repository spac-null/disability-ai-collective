#!/usr/bin/env python3
"""Render every desk route against REAL data and print what Telegram would receive.

WHY THIS EXISTS. The desk's defects have all been things that only appear in the
rendering: a title that was a run id, an inbox that opened with twenty rows, a
publisher's artifact mismatch in front of a reader, `Noted.` after every press. Unit
tests asserted the behaviour and missed the output. This runs the real handlers over
the real store and prints the actual message text and keyboards, so the output itself
can be read and judged.

IT TOUCHES NOTHING. The live store is copied to a temporary directory and the copy is
what gets written; `tg` is replaced by a recorder, so no message is sent and no state
on disk changes. Run it as often as you like.

  python3 automation/editorial_desk_render.py            # every route
  python3 automation/editorial_desk_render.py --route today
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import editorial_desk as DESK                      # noqa: E402
import editorial_desk_actions as ACT               # noqa: E402
import editorial_desk_bot as BOT                   # noqa: E402
import editorial_desk_store as STORE               # noqa: E402

OWNER = None          # filled from the allowlist
CHAT = 999999
WIDTH = 78


class Capture:
    """A fake Telegram that records instead of sending."""

    def __init__(self):
        self.sent = []
        self.next_id = [50000]

    def __call__(self, method, payload=None, timeout=None):
        self.sent.append((method, payload))
        if method == "sendMessage":
            self.next_id[0] += 1
            return {"ok": True, "result": {"message_id": self.next_id[0]}}
        return {"ok": True, "result": []}

    def drain(self):
        out, self.sent = self.sent, []
        return out


def show(label, events):
    print()
    print("=" * WIDTH)
    print("ROUTE: %s" % label)
    print("=" * WIDTH)
    if not events:
        print("  (nothing sent)")
        return
    for method, p in events:
        if method == "sendMessage":
            text = p.get("text", "")
            print("  --- message (%d chars) ---" % len(text))
            for line in text.splitlines() or [""]:
                print("  | " + line)
            _keyboard(p.get("reply_markup"))
        elif method == "answerCallbackQuery":
            print("  [toast] %r" % p.get("text", ""))
        elif method == "editMessageReplyMarkup":
            print("  --- keyboard replaced on message %s ---" % p.get("message_id"))
            _keyboard(p.get("reply_markup"))
        else:
            print("  [%s] %s" % (method, json.dumps(p)[:120]))


def _keyboard(markup):
    if not markup:
        return
    for row in markup.get("inline_keyboard", []):
        cells = []
        for b in row:
            n = len(b["callback_data"].encode("utf-8"))
            flag = "  !!OVER 64 BYTES!!" if n > 64 else ""
            cells.append("[ %s ]%s" % (b["text"], flag))
        print("  " + "  ".join(cells))
    longest = max((len(b["callback_data"].encode("utf-8"))
                   for row in markup.get("inline_keyboard", []) for b in row),
                  default=0)
    n_buttons = sum(len(r) for r in markup.get("inline_keyboard", []))
    print("  (%d buttons, longest payload %d bytes)" % (n_buttons, longest))


def msg(text, mid=1, reply_to=None):
    m = {"message_id": mid, "from": {"id": OWNER}, "chat": {"id": CHAT}, "text": text}
    if reply_to:
        m["reply_to_message"] = {"message_id": reply_to}
    return m


def cbq(data, cid, message_id=4242):
    return {"id": cid, "from": {"id": OWNER}, "data": data,
            "message": {"chat": {"id": CHAT}, "message_id": message_id}}


def main():
    global OWNER
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", help="render only routes whose label contains this")
    args = ap.parse_args()

    BOT.parse_env(BOT.SECRETS_FILE)
    env = BOT.parse_env(BOT.SECRETS_FILE)
    allowed = env.get(ACT.ALLOWED_USERS_ENV, "") or "1"
    OWNER = int(allowed.split(",")[0].strip())
    import os
    os.environ[ACT.ALLOWED_USERS_ENV] = str(OWNER)

    live = pathlib.Path(STORE.ROOT)
    tmp = tempfile.mkdtemp(prefix="desk-render-")
    if live.is_dir():
        shutil.copytree(live, tmp, dirs_exist_ok=True)
    STORE.ROOT = pathlib.Path(tmp)
    BOT.STATE_DIR = pathlib.Path(tmp)

    cap = Capture()
    BOT.tg = cap
    BOT.CHAT_ID = str(CHAT)

    def render(label, fn):
        if args.route and args.route.lower() not in label.lower():
            return cap.drain() and None
        cap.drain()
        try:
            fn()
        except Exception as e:                                        # noqa: BLE001
            print()
            print("ROUTE %s RAISED %s: %s" % (label, type(e).__name__, e))
            return
        show(label, cap.drain())

    render("/today", lambda: BOT.cmd_today(CHAT))
    render("/backlog", lambda: BOT.cmd_backlog(CHAT))
    render("/help", lambda: BOT.handle_message(msg("/help", 2)))

    rows = ACT.inbox()
    unread = next((r for r in rows if r["status"] == ACT.UNREAD), None)
    reading = next((r for r in rows if r["status"] == ACT.READING), None)
    finished = next((r for r in rows if r["status"] == ACT.FINISHED), None)

    if unread:
        sid = unread["session_id"]
        render("READ (an unread article)",
               lambda: BOT.handle_callback(cbq("read:%s" % sid, "r1")))
        blocks = BOT.sent_blocks(sid, unread["version_sha256"])
        if blocks:
            b = blocks[-1]
            render("Next >", lambda: BOT.handle_callback(cbq("NEXT:%s" % sid, "r2")))
            render("< Back", lambda: BOT.handle_callback(cbq("BACK:%s" % sid, "r3")))
            render("feedback: Strong",
                   lambda: BOT.handle_callback(
                       cbq("STRONG:%s:%s" % (sid, b["block_id"]), "r4",
                           b["telegram_message_id"])))
            render("feedback: Too dense (opens sub-menu)",
                   lambda: BOT.handle_callback(
                       cbq("TOO_DENSE:%s:%s" % (sid, b["block_id"]), "r5",
                           b["telegram_message_id"])))
            render("detail: Too many names",
                   lambda: BOT.handle_callback(
                       cbq("d:%s:%s:D:TOO_MANY_NAMES" % (sid, b["block_id"]), "r6",
                           b["telegram_message_id"])))
            render("feedback: Sounds like a report",
                   lambda: BOT.handle_callback(
                       cbq("SOUNDS_LIKE_REPORT:%s:%s" % (sid, b["block_id"]), "r7",
                           b["telegram_message_id"])))
            render("feedback: I am lost",
                   lambda: BOT.handle_callback(
                       cbq("READER_LOST:%s:%s" % (sid, b["block_id"]), "r8",
                           b["telegram_message_id"])))
            render("free text (reply to a block)",
                   lambda: BOT.handle_message(
                       msg("this is where you lost me", 9,
                           reply_to=b["telegram_message_id"])))
            render("free text (plain, no reply)",
                   lambda: BOT.handle_message(msg("still too dense", 10)))
        render("/status", lambda: BOT.handle_message(msg("/status", 11)))
        render("/debug", lambda: BOT.handle_message(msg("/debug", 12)))
        render("reading to the end",
               lambda: [BOT.handle_callback(cbq("NEXT:%s" % sid, "end%d" % i))
                        for i in range(12)])
        render("/publish (should refuse, in plain language)",
               lambda: BOT.handle_message(msg("/publish", 13)))

    if reading:
        rid = reading["session_id"]
        render("RESUME (a part-read article)",
               lambda: BOT.handle_callback(cbq("read:%s" % rid, "s1")))
        render("Hold", lambda: BOT.handle_callback(cbq("hold:%s" % rid, "s2")))

    if finished:
        fid = finished["session_id"]
        render("Back to drafts",
               lambda: BOT.handle_callback(cbq("inbox:%s" % fid, "f1")))

    render("unknown card (must refuse, send nothing)",
           lambda: BOT.handle_callback(cbq("read:deadbeefdeadbeef", "x1")))
    render("malformed callback",
           lambda: BOT.handle_callback(cbq("::::", "x2")))
    render("unknown command",
           lambda: BOT.handle_message(msg("/nonsense", 20)))
    render("free text with nothing open",
           lambda: BOT.handle_message(msg("a stray thought", 21)))

    print()
    print("=" * WIDTH)
    print("store copy: %s  (live store untouched)" % tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
