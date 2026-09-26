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
        check("and points at the unopened card rather than claiming nothing waits",
              any("haven't opened" in t for t in h.texts()[before:]),
              h.texts()[before:])


def test_upstream_failure_is_not_offered_as_a_draft():
    with Harness() as h:
        h.make_run("production-empty", body="")
        BOT.cmd_today(CHAT)
        check("a run with no article opens no session", STORE.sessions() == [])
        check("and is reported as nothing waiting",
              any("Nothing waiting" in t for t in h.texts()), h.texts())


# ── reading ─────────────────────────────────────────────────────────────────────────

def _open_and_read(h):
    """Deliver one article and open it THROUGH ITS OWN BUTTON, as a reader does."""
    h.make_run()
    BOT.cmd_today(CHAT)
    s = STORE.sessions()[0]
    BOT.handle_callback(cb("read:%s" % s["session_id"], cid="open-%s" % s["session_id"]))
    return s


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
        BOT.cmd_read(CHAT, BOT.reading_session())
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
        BOT.cmd_publish(CHAT, STRANGER, s)
        check("publish refuses an unlisted user",
              any("Not authorized" in t for t in h.texts()), h.texts()[-1])
        check("no approval was recorded",
              STORE.approved_version(s["origin_version_sha256"]) is None)


def test_publish_reports_the_publishers_refusal():
    with Harness() as h:
        s = _open_and_read(h)
        BOT.cmd_publish(CHAT, OWNER, s)
        last = h.texts()[-1]
        check("publish refuses and says why", last.startswith("Not published:"), last)
        check("the reason is the validator's, not the desk's",
              "missing required artifact" in last.lower() or "bridge" in last.lower(),
              last)
        check("nothing was published",
              STORE.published_version(s["origin_version_sha256"]) is None)


# ── article identity: the 2026-09-26 incident and its perimeter ─────────────────────
#
# On 2026-09-26 five cards were delivered at 17:00:17 and every READ button opened the
# fifth. These tests fix the shape of that failure, not one instance of it: each asserts
# that a button resolves to the article it was built for under conditions that would let
# a positional, latest-wins or title-based resolver look correct.

def _five_cards(h):
    """Five distinct articles, delivered in one /today, oldest last -- the exact shape
    of the failed smoke."""
    bodies = {}
    for i, day in enumerate(("26", "25", "24", "23", "22"), start=1):
        body = "\n\n".join(
            "Article %s paragraph %d. %s" % (day, n, "word " * 40) for n in range(1, 10))
        bodies[day] = body
        T.make_run(h.ev.name, "production-202609%sT070000Z-aaaaaaa%d" % (day, i),
                   body=body)
    BOT.cmd_today(CHAT)
    return bodies


def test_multi_card_identity():
    """A: five cards on screen at once; READ on each opens its own article."""
    with Harness() as h:
        bodies = _five_cards(h)
        sessions = STORE.sessions()
        check("A: five sessions were created", len(sessions) == 5, len(sessions))
        for s in sessions:
            before = len(h.messages())
            BOT.handle_callback(cb("read:%s" % s["session_id"],
                                   cid="read-%s" % s["session_id"]))
            sent = "\n".join(h.texts()[before:])
            day = s["run_id"][17:19]
            check("A: READ on the %s card opens the %s article" % (day, day),
                  ("Article %s paragraph 1." % day) in sent,
                  sent[:160])
            check("A: and opens no other article's text",
                  sum(("Article %s paragraph 1." % d) in sent for d in bodies) == 1,
                  sent[:160])
        starts = [e for e in STORE.events() if e["event_type"] == "READ_STARTED"]
        check("A: each article recorded its own READ_STARTED",
              len({e["session_id"] for e in starts}) == 5, len(starts))


def test_reordering_does_not_move_a_button():
    """B: the queue changes after the cards were sent; old buttons still resolve."""
    with Harness() as h:
        _five_cards(h)
        first = STORE.sessions()[0]
        # A newer run arrives and would sort to the top of any positional resolver.
        T.make_run(h.ev.name, "production-20260927T070000Z-ffffffff",
                   body="\n\n".join("Interloper paragraph %d. %s" % (n, "word " * 40)
                                    for n in range(1, 8)))
        BOT.cmd_today(CHAT)
        before = len(h.messages())
        BOT.handle_callback(cb("read:%s" % first["session_id"], cid="reorder"))
        sent = "\n".join(h.texts()[before:])
        check("B: the old button still opens its own article",
              "Article 26 paragraph 1." in sent, sent[:160])
        check("B: and not the newly arrived one", "Interloper" not in sent, sent[:160])


def test_identity_survives_a_restart():
    """C: nothing in the process carries identity, so a restart changes nothing."""
    with Harness() as h:
        _five_cards(h)
        target = STORE.sessions()[1]
        # A restart is exactly this: no in-process state, everything re-read from the
        # store. Re-importing would be theatre; the assertion is that the handler reads
        # identity from the button and the store, which a fresh process also does.
        BOT.handle_callback(cb("read:%s" % target["session_id"], cid="restart-1"))
        first_open = "\n".join(h.texts()[-2:])
        before = len(h.messages())
        BOT.handle_callback(cb("read:%s" % target["session_id"], cid="restart-2"))
        check("C: the button resolves the same article before and after",
              "Article 25 paragraph 1." in first_open, first_open[:160])
        check("C: a second press continues that same article",
              h.texts()[-1].startswith("2/"), h.texts()[-1][:20])
        check("C: it did not jump to another article",
              "Article 25" in h.texts()[-1], h.texts()[-1][:80])
        _ = before


def test_identical_titles_cannot_collide():
    """D: two articles that look the same to a human still have different identities."""
    with Harness() as h:
        same = "# The Same Headline\n\n"
        a = same + "\n\n".join("Alpha paragraph %d. %s" % (n, "word " * 40)
                               for n in range(1, 8))
        b = same + "\n\n".join("Beta paragraph %d. %s" % (n, "word " * 40)
                               for n in range(1, 8))
        T.make_run(h.ev.name, "production-20260926T070000Z-aaaa1111", body=a)
        T.make_run(h.ev.name, "production-20260925T070000Z-bbbb2222", body=b)
        BOT.cmd_today(CHAT)
        s_a, s_b = STORE.sessions()[0], STORE.sessions()[1]
        check("D: same title, different session ids",
              s_a["session_id"] != s_b["session_id"])
        check("D: same title, different version hashes",
              s_a["origin_version_sha256"] != s_b["origin_version_sha256"])
        before = len(h.messages())
        BOT.handle_callback(cb("read:%s" % s_b["session_id"], cid="dup-title"))
        sent = "\n".join(h.texts()[before:])
        check("D: the button opens the right one of the two",
              "Beta paragraph 1." in sent and "Alpha paragraph" not in sent, sent[:160])


def test_duplicate_callback_opens_the_same_article():
    """E: a redelivered press is the same press, not a different article."""
    with Harness() as h:
        _five_cards(h)
        target = STORE.sessions()[2]
        c = cb("read:%s" % target["session_id"], cid="dedupe-same")
        BOT.handle_callback(c)
        first = "\n".join(h.texts()[-2:])
        BOT.handle_callback(c)
        check("E: both presses concern the same article",
              "Article 24" in first and "Article 24" in h.texts()[-1],
              (first[:80], h.texts()[-1][:80]))
        starts = [e for e in STORE.events()
                  if e["event_type"] == "READ_STARTED"
                  and e["session_id"] == target["session_id"]]
        check("E: READ_STARTED was recorded once", len(starts) == 1, len(starts))


def test_version_mismatch_fails_closed():
    """F: if the stored bytes no longer match the version, nothing is sent."""
    with Harness() as h:
        _five_cards(h)
        target = STORE.sessions()[0]
        sha = target["origin_version_sha256"]
        # Corrupt the stored bytes the way a damaged store would.
        (pathlib.Path(h.st.name) / "versions" / ("%s.md" % sha)).write_text(
            "something else entirely", encoding="utf-8")
        before = len(h.messages())
        BOT.handle_callback(cb("read:%s" % target["session_id"], cid="mismatch"))
        sent = "\n".join(h.texts()[before:])
        check("F: a version mismatch refuses", "can't open that article safely" in sent,
              sent[:200])
        check("F: and sends no article text", "paragraph 1." not in sent, sent[:200])
        check("F: and no block was recorded",
              STORE.session_blocks(target["session_id"], sha) == [])


def test_unknown_card_refuses_rather_than_substituting():
    with Harness() as h:
        _five_cards(h)
        before = len(h.messages())
        BOT.handle_callback(cb("read:deadbeefdeadbeef", cid="unknown"))
        check("an unidentifiable card sends nothing at all",
              len(h.messages()) == before, h.texts()[before:])
        check("and starts no reading",
              [e for e in STORE.events() if e["event_type"] == "READ_STARTED"] == [])


def test_g_feedback_binds_to_the_article_displayed():
    """G: feedback lands on the version and block that were actually on screen."""
    with Harness() as h:
        _five_cards(h)
        third = STORE.sessions()[2]
        BOT.handle_callback(cb("read:%s" % third["session_id"], cid="g-read"))
        blk = STORE.session_blocks(third["session_id"],
                                   third["origin_version_sha256"])[0]
        # A newer card is opened afterwards: a resolver keyed on "current" would file
        # the reply that follows against this one instead.
        newest = STORE.sessions()[4]
        BOT.handle_callback(cb("read:%s" % newest["session_id"], cid="g-read2"))
        BOT.handle_message(msg("hier raak ik je kwijt", mid=4242,
                               reply_to=blk["telegram_message_id"]))
        ev = [e for e in STORE.events() if e["event_type"] == "FREE_TEXT_FEEDBACK"]
        check("G: one feedback event", len(ev) == 1, ev)
        check("G: filed against the article the passage belongs to",
              ev[0]["session_id"] == third["session_id"], ev[0]["session_id"])
        check("G: and against that article's version",
              ev[0]["version_sha256"] == third["origin_version_sha256"])
        check("G: and against the exact block replied to",
              ev[0]["block_id"] == blk["block_id"])
        check("G: recorded as a true reply", ev[0]["metadata"]["binding"] == "REPLY")


def test_callback_payloads_fit_telegram():
    """Telegram truncates callback_data over 64 bytes, and a truncated token would
    collide across cards. Assert the real payloads, not an estimate."""
    with Harness() as h:
        _five_cards(h)
        s = STORE.sessions()[0]
        BOT.handle_callback(cb("read:%s" % s["session_id"], cid="len"))
        payloads = []
        for m in h.messages():
            for row in (m.get("reply_markup") or {}).get("inline_keyboard", []):
                payloads += [b["callback_data"] for b in row]
        check("callback payloads were produced", len(payloads) >= 8, len(payloads))
        longest = max(payloads, key=len)
        check("every callback payload is within Telegram's 64-byte limit",
              all(len(p.encode("utf-8")) <= 64 for p in payloads),
              "%r (%d bytes)" % (longest, len(longest.encode("utf-8"))))
        check("every payload names a session id",
              all(len(p.split(":")) >= 2 and len(p.split(":")[1]) == 16
                  for p in payloads), payloads[:3])


def test_the_incident_conditions_are_reproduced():
    """Proof the fixture above really recreates 2026-09-26, so test A is not green by
    accident: the REMOVED resolver, run against exactly this state, picks card five for
    every card -- while the shipped handler picks each card's own article."""
    with Harness() as h:
        _five_cards(h)

        def latest_wins():
            """The deleted active_session(), behaviour preserved for this proof only."""
            closed = BOT.closed_sessions()
            for s in reversed(STORE.sessions()):
                if s["session_id"] not in closed:
                    return s
            return None

        wrong = latest_wins()
        check("the old resolver picks the last-delivered card for every button",
              wrong["run_id"].startswith("production-20260922"), wrong["run_id"])
        first = STORE.sessions()[0]
        check("which is NOT the first card", wrong["session_id"] != first["session_id"])
        before = len(h.messages())
        BOT.handle_callback(cb("read:%s" % first["session_id"], cid="proof"))
        sent = "\n".join(h.texts()[before:])
        check("the shipped handler picks the card that was pressed",
              "Article 26 paragraph 1." in sent and "Article 22" not in sent, sent[:160])


def test_no_latest_wins_resolver_remains():
    """Structural guard: identity must be a parameter, never something re-derived."""
    import inspect
    src = (HERE / "editorial_desk_bot.py").read_text()
    check("the latest-wins resolver is gone from the module",
          "def active_session" not in src)
    for name in ("cmd_read", "cmd_hold", "cmd_brief", "cmd_status", "cmd_debug",
                 "cmd_rewrite", "cmd_publish"):
        params = inspect.signature(getattr(BOT, name)).parameters
        check("%s takes an explicit session" % name, "session_row" in params,
              list(params))
    cbsrc = src[src.index("def handle_callback"):src.index("def handle_message")]
    check("the callback handler never falls back to another article",
          "reading_session()" not in cbsrc)
    check("and refuses an unknown card",
          "I can't identify that card" in cbsrc)


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
