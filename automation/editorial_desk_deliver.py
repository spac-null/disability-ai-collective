#!/usr/bin/env python3
"""Put the day's article on the desk, by itself, as soon as the run has finished.

WHY THIS EXISTS. Until now an article reached the owner only if he typed /today, so
"no finished Crip Minds article dies unseen" depended on him remembering to ask. The
2026-09-27 run finished at 09:26 and reached nobody; the desk found out about it hours
later, in a list, between articles from two weeks earlier.

WHAT IT SENDS. One card per article WRITTEN TODAY that has not been delivered yet, and
nothing else -- no inbox, no backlog, no older drafts. A new article should arrive as
itself, not as row four of six.

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


def todays_undelivered(now=None, root=None) -> list:
    """Runs written today, carrying a coherent article, not yet on the desk."""
    import datetime
    now = now or datetime.datetime.now(datetime.timezone.utc)
    known = {s["run_id"] for s in STORE.sessions(root)}
    out = []
    for d in DESK.scan(limit=12):
        if d.name in known:
            continue
        written = ACT.run_date(d.name)
        if written is None or written.date() != now.date():
            continue
        run = DESK.read_run(d)
        if run["state"] == DESK.REVIEWABLE_DRAFT:
            out.append(run)
    return out[:MAX_PER_RUN]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not a.dry_run:
        BOT.load_secrets()
    runs = todays_undelivered()
    if not runs:
        BOT.log("nothing written today is waiting to be delivered")
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
