#!/usr/bin/env python3
"""Put a finished article on the desk, by itself, as soon as the run has finished.

WHY THIS EXISTS. Until now an article reached the owner only if he typed /today, so
"no finished Crip Minds article dies unseen" depended on him remembering to ask. The
2026-09-27 run finished at 09:26 and reached nobody; the desk found out about it hours
later, in a list, between articles from two weeks earlier.

AND FOR ITS FIRST WEEK IT KEPT THAT PROMISE ONLY BEFORE 10:05 UTC. Selection compared
the run's UTC date against today's, and the cron fired once a day. An article finishing
in the evening was dated yesterday by the time the next fire came, so it was skipped --
permanently, at every hour, with nothing logged. On 2026-09-30 that swallowed three
articles including the only one to reach the Reader; all three were sent by hand.

WHAT IT SENDS. One card per undelivered article written inside the delivery window
(see DELIVERY_WINDOW_DAYS), and nothing else -- no inbox, no backlog, no older drafts.
A new article should arrive as itself, not as row four of six.

It is idempotent: sessions are keyed on (run, article bytes), so running it twice, or
running it after the owner has already pulled the article with /today, delivers
nothing a second time. Safe on the cron, safe by hand.

  python3 automation/editorial_desk_deliver.py             # deliver, if there is any
  python3 automation/editorial_desk_deliver.py --dry-run   # say what it would send
"""
from __future__ import annotations

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import editorial_desk as DESK                      # noqa: E402
import editorial_desk_actions as ACT               # noqa: E402
import editorial_desk_bot as BOT                   # noqa: E402
import editorial_desk_store as STORE               # noqa: E402

# A day's run can produce more than one candidate; beyond a few, something is wrong
# and flooding the chat is not the way to report it.
MAX_PER_RUN = 3

# HOW FAR BACK A RUN MAY BE AND STILL BE DELIVERED, in days, counted on the UTC date in
# the run id. 1 means today and yesterday.
#
# WHY IT IS NOT 0, WHICH IS WHAT IT WAS. The selection compared the run's UTC date against
# TODAY'S, and the cron fired once, at 10:05 UTC. A run finishing at 21:00 is dated the
# 30th; the only fire that could carry it is 10:05 on the 1st, by which time "today" is
# the 1st and the run no longer matches. It was not late. It was unreachable, and there
# was no hour of the day at which a second look would have found it.
#
# Measured: on 2026-09-30 that swallowed three of the day's articles, including the only
# one to reach the Reader. Every one was sent by hand. The docstring above says this
# module exists so that "no finished Crip Minds article dies unseen"; for any run
# finishing after 10:05 UTC, it could not deliver on that.
#
# One day of overlap is enough because the cron now fires through the day rather than
# once: the window exists to cover the boundary and a missed fire, not to resurrect a
# backlog. Delivery stays idempotent on (run, article bytes), so a wider window cannot
# re-send anything the owner has already seen -- which is what makes widening it safe.
DELIVERY_WINDOW_DAYS = 1

# HOW MANY RUN DIRECTORIES TO LOOK AT. `scan` takes the newest N directories BEFORE
# anything is filtered, so already-delivered runs consume the budget and can hide a
# deliverable one behind them. It was 12. Measured on 2026-10-01: the two days inside the
# delivery window held 15 run directories, so three were already unreachable -- a run
# could age out of the window without ever being considered. Sized to cover the window
# several times over; the loop opens no artifact until a run survives the date filter,
# so a larger number costs a directory listing and nothing else.
SCAN_LIMIT = 60

# ONE DELIVERY AT A TIME. The cron fires through the day rather than once, and `offer()`
# creates the session before the Telegram send returns, so two overlapping fires can both
# select the same run and send two cards for it. A lock is the narrow fix for the risk
# this change introduces; the deeper one -- that `offer()` ignores whether the session was
# newly created -- is recorded in the phase blueprint and is not this change to make.
LOCK_PATH = "/tmp/cripminds-desk-deliver.lock"


def recent_undelivered(now=None, root=None) -> list:
    """Runs written recently enough to still be news, carrying a coherent article,
    not yet on the desk.

    `run_date` resolves a run id to a DATE and not an instant, so the window is counted
    in whole UTC days. An hours-based window would be measuring against midnight of the
    run's own day and would drift with the hour the check happens to run.
    """
    import datetime
    now = now or datetime.datetime.now(datetime.timezone.utc)
    known = {s["run_id"] for s in STORE.sessions(root)}
    out = []
    for d in DESK.scan(limit=SCAN_LIMIT):
        if d.name in known:
            continue
        written = ACT.run_date(d.name)
        if written is None:
            continue
        age_days = (now.date() - written.date()).days
        # A run dated in the future is a clock problem, not a delivery candidate.
        if age_days < 0 or age_days > DELIVERY_WINDOW_DAYS:
            continue
        run = DESK.read_run(d)
        if run["state"] == DESK.REVIEWABLE_DRAFT:
            out.append(run)
    return out[:MAX_PER_RUN]


def _hold_lock():
    """An exclusive lock for the duration of this process, or None if another holds it.

    Advisory and non-blocking: a second fire that arrives while the first is still
    sending exits quietly rather than queueing, because the work it would do is the work
    already in flight. The file descriptor is returned and kept alive by the caller --
    the lock is released by the process ending, so a crash cannot strand it.
    """
    import fcntl
    fh = open(LOCK_PATH, "a+")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return None
    return fh


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    lock = None
    if not a.dry_run:
        lock = _hold_lock()
        if lock is None:
            BOT.log("another delivery is already running; leaving it to finish")
            return 0
        BOT.load_secrets()
    # `lock` is deliberately held in scope for the whole function: the lock lives as long
    # as its file descriptor, so releasing it early would reopen the window it closes.
    assert lock is not None or a.dry_run
    runs = recent_undelivered()
    if not runs:
        BOT.log("nothing recent is waiting to be delivered")
        return 0
    for run in runs:
        BOT.log("delivering %s (%d words, %s)"
                % (run["run_id"], run["words"], run["publish_state"]))
        if a.dry_run:
            print(DESK.status_line(run))
            continue
        BOT.offer(run, heading="Today's article")
    return 0


if __name__ == "__main__":
    sys.exit(main())
