"""Prove Telegram ACCEPTS the desk's real payloads, then remove them again.

The render harness shows what would be sent; only the API can say whether it is
valid -- keyboard size, label length, callback payload limits, markup shape. Each
message is sent silently (no notification) and deleted immediately afterwards.
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, "/srv/data/hermes/workspace/disability-ai-collective/automation")
import editorial_desk as DESK          # noqa: E402
import editorial_desk_actions as ACT   # noqa: E402
import editorial_desk_bot as BOT       # noqa: E402
import editorial_desk_store as STORE   # noqa: E402

BOT.load_secrets()
real_tg = BOT.tg
sent = []


def send_and_check(label, text, rows):
    payload = {"chat_id": BOT.CHAT_ID, "text": text[:4090],
               "disable_web_page_preview": True, "disable_notification": True}
    if rows:
        payload["reply_markup"] = BOT.keyboard(rows)
    r = real_tg("sendMessage", payload)
    ok = bool(r and r.get("ok"))
    if ok:
        sent.append(r["result"]["message_id"])
    n = sum(len(x) for x in rows) if rows else 0
    longest = max((len(b[1].encode()) for row in rows for b in row), default=0) if rows else 0
    print("%-34s %-8s %d buttons, longest payload %d bytes%s"
          % (label, "ACCEPTED" if ok else "REJECTED", n, longest,
             "" if ok else "  -> " + json.dumps(r)[:200]))
    return ok


rows = ACT.inbox()
target = next((r for r in rows if r["status"] in (ACT.UNREAD, ACT.READING)), None)
if target is None:
    print("no article on the desk to test with")
    raise SystemExit(1)

sha = target["version_sha256"]
sid = target["session_id"]
blocks = DESK.split_blocks(STORE.read_version_bytes(sha))

all_ok = True
all_ok &= send_and_check(
    "article card", "LIVE PAYLOAD CHECK - card\n\n%s\n%d words\nReadable now."
    % (target["title"], target["words"]),
    [[("READ", "read:%s" % sid), ("HOLD", "hold:%s" % sid)]])

all_ok &= send_and_check(
    "reading block + full keyboard",
    "LIVE PAYLOAD CHECK - block\n\n" + blocks[0]["text"],
    BOT.block_keyboard(sid, blocks[0]["block_id"]))

all_ok &= send_and_check(
    "density sub-menu",
    "LIVE PAYLOAD CHECK - detail keyboard",
    BOT.detail_keyboard("TOO_DENSE", sid, blocks[0]["block_id"]))

all_ok &= send_and_check(
    "report sub-menu (longest payloads)",
    "LIVE PAYLOAD CHECK - detail keyboard",
    BOT.detail_keyboard("SOUNDS_LIKE_REPORT", sid, blocks[0]["block_id"]))

# The inbox, exactly as /today would build it, with the most buttons it can carry.
inbox_buttons = []
for n, r in enumerate(rows[:6], start=1):
    b = BOT._row_buttons(r, n)
    if b:
        inbox_buttons.append(b)
all_ok &= send_and_check("inbox keyboard", "LIVE PAYLOAD CHECK - inbox",
                         BOT._pack(inbox_buttons))

longest_block = max(blocks, key=lambda b: len(b["text"]))
all_ok &= send_and_check("longest block in this article",
                         "LIVE PAYLOAD CHECK - longest block\n\n"
                         + longest_block["text"], None)

time.sleep(1)
removed = 0
for mid in sent:
    r = real_tg("deleteMessage", {"chat_id": BOT.CHAT_ID, "message_id": mid})
    if r and r.get("ok"):
        removed += 1
print()
print("sent %d, deleted %d" % (len(sent), removed))
print("RESULT:", "every payload accepted by Telegram" if all_ok else "SOMETHING WAS REJECTED")
