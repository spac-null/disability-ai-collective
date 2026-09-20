#!/usr/bin/env python3
"""production_window_guard.py -- keep the Claude subscription free while production runs.

WHY THIS EXISTS. The daily article run starts at 09:00 Europe/Rome and every Claude-family
stage in it is served by ONE claude.ai subscription (see automation/claude_cli_provider.py:
there is no paid fallback, by policy). Anything else on this host that spends the same
subscription at the same time is competing with the only job that publishes.

On 2026-09-20 the 09:00 run died at KF_COMMISSION on CLAUDE_SUBSCRIPTION_TIMEOUT after
180s, and a shadow-replay experiment was started against the same subscription at 09:35,
while the recovery was in progress. The replay did not cause the 09:00 failure -- it began
later -- and the recovery rerun succeeded alongside it, so this guard is not a fix for a
measured contention incident. It is the standing rule those two facts made worth writing
down: production has first call on the subscription, and an experiment should not have to
remember that.

WHAT IT DOES NOT DO. It never kills anything, never inspects other processes, and never
applies to a person working interactively. It is a voluntary check for Crip Minds
AUTOMATED jobs -- benchmarks, replays, shadow runs, calibration sweeps -- to call before
they start spending the subscription.

USE

    # python
    from production_window_guard import assert_outside_production_window
    assert_outside_production_window("relation-aware-correction replay")

    # shell, before a long experiment
    python3 automation/production_window_guard.py || exit 0

CRIPMINDS_IGNORE_PRODUCTION_WINDOW=1 overrides it, deliberately and visibly, for the case
where the owner means it.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, time as _time

try:                                             # stdlib since 3.9; no new dependency
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Rome")
except Exception:                                # pragma: no cover -- no tzdata on host
    _TZ = None

# The daily article cron fires at 09:00 Europe/Rome. The window opens early enough to
# cover a late start and closes after a normal run's worst observed length (2026-09-20:
# 09:39 -> 09:53 to a terminal decision; a publishing run is longer).
WINDOW_OPEN = _time(8, 45)
WINDOW_CLOSE = _time(10, 0)
OVERRIDE_ENV = "CRIPMINDS_IGNORE_PRODUCTION_WINDOW"


class ProductionWindowBusy(RuntimeError):
    """Raised when an automated job would spend the subscription during the run."""


def now_rome() -> datetime:
    return datetime.now(_TZ) if _TZ else datetime.now()


def in_production_window(when: datetime | None = None) -> bool:
    """Whether `when` (Europe/Rome) falls inside the daily article run's window."""
    t = (when or now_rome()).time()
    return WINDOW_OPEN <= t < WINDOW_CLOSE


def reason(when: datetime | None = None) -> str:
    return ("the Crip Minds daily article run owns the Claude subscription between "
            "%s and %s Europe/Rome; it is %s now"
            % (WINDOW_OPEN.strftime("%H:%M"), WINDOW_CLOSE.strftime("%H:%M"),
               (when or now_rome()).strftime("%H:%M")))


def assert_outside_production_window(job: str = "this job",
                                     when: datetime | None = None) -> None:
    """Raise unless the subscription is free for `job`. No-op outside the window."""
    if os.environ.get(OVERRIDE_ENV):
        return
    if in_production_window(when):
        raise ProductionWindowBusy("%s must not run now: %s" % (job, reason(when)))


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    job = argv[0] if argv else "this job"
    try:
        assert_outside_production_window(job)
    except ProductionWindowBusy as e:
        print("PRODUCTION_WINDOW_BUSY: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
