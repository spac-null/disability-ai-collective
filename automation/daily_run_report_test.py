#!/usr/bin/env python3
"""
daily_run_report_test.py -- what the morning message is allowed to say.

The reporter reads artifacts written by several stages, and those artifacts disagree
about shape. Two live defects came out of that in two days:

  2026-09-18  MANIFEST.json records run_status as the STRING "PROVIDER_FAILURE"; the
              reporter read only the dict shape, so the one morning the field mattered
              it printed nothing and an infrastructure failure read as a quiet HOLD.
  2026-09-19  the fix printed any non-empty string, and a healthy run records
              run_status "OK" -- so a normal editorial HOLD carried a bare "⚠️ OK"
              beneath it: a warning glyph attached to the word for nothing being wrong.

Both shapes are pinned here. Infrastructure earns a line only when it is abnormal;
silence means the pipeline ran fine.

No model calls, no network, no Telegram, no evidence root -- every case is a temporary
directory built in the test.

Run (from repo root):
  python3 automation/daily_run_report_test.py
"""

import datetime
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import daily_run_report as RPT                                   # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


def build(tmp, manifest, comp=None, run_status=None, article="# A title\n\nA paragraph.\n"):
    """One run directory, as the pipeline would leave it."""
    day = datetime.date(2026, 9, 19)
    d = pathlib.Path(tmp) / ("production-%sT070000Z-deadbeef" % day.strftime("%Y%m%d"))
    d.mkdir(parents=True)
    (d / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    if comp is not None:
        (d / "COMPOSITION_RESULT.json").write_text(json.dumps(comp), encoding="utf-8")
    if run_status is not None:
        (d / "RUN_STATUS.json").write_text(json.dumps(run_status), encoding="utf-8")
    (d / "ARTICLE_FINAL.md").write_text(article, encoding="utf-8")
    return day, d


def message_for(manifest, comp=None, run_status=None):
    with tempfile.TemporaryDirectory() as tmp:
        day, _ = build(tmp, manifest, comp, run_status)
        old = RPT.EVIDENCE_ROOT
        RPT.EVIDENCE_ROOT = pathlib.Path(tmp)
        try:
            return RPT.build_message(day)
        finally:
            RPT.EVIDENCE_ROOT = old


HOLD_COMP = {"status": "HOLD", "failure_stage": "SAFETY", "reason_code": "SAFETY_HOLD",
             "words": 1068, "compose_mode": "FAST_LANE", "runtime_seconds": 850,
             "failure_reason": "UNSUPPORTED_NEGATIVES: 2 negative-shaped sentence(s)",
             "stages": {"WRITER": "PASS", "SAFETY": "HOLD"}}


def test_ok_run_status_is_not_a_warning():
    """The 19 September defect."""
    msg = message_for({"decision": "HOLD", "run_status": "OK"}, HOLD_COMP)
    check("a healthy run_status prints no warning line", "⚠️" not in msg, msg)
    check("...and 'OK' does not appear at all", "OK" not in msg, msg)
    check("the editorial verdict is still reported", "HOLD at SAFETY" in msg, msg)


def test_ok_in_dict_shape_is_also_silent():
    msg = message_for({"decision": "HOLD", "run_status": {"status": "OK", "stage": ""}},
                      HOLD_COMP)
    check("a healthy dict run_status is also silent", "⚠️" not in msg, msg)


def test_provider_failure_string_is_reported():
    """The 18 September defect, from the other side."""
    msg = message_for({"decision": "HOLD", "run_status": "PROVIDER_FAILURE"}, None,
                      {"stage": "RESEARCH_PACK", "status": "PROVIDER_FAILURE",
                       "error": "reply is not valid JSON (Expecting ',' delimiter)"})
    check("an abnormal string run_status IS reported", "⚠️" in msg, msg)
    check("...naming the stage", "RESEARCH_PACK" in msg, msg)
    check("...and the actual error, not just a code", "not valid JSON" in msg, msg)


def test_provider_failure_dict_is_reported():
    msg = message_for({"decision": "HOLD",
                       "run_status": {"status": "PROVIDER_FAILURE", "stage": "WRITER"}},
                      HOLD_COMP)
    check("an abnormal dict run_status IS reported", "⚠️" in msg and "WRITER" in msg, msg)


def test_absent_run_status_is_silent():
    msg = message_for({"decision": "HOLD"}, HOLD_COMP)
    check("no run_status at all prints no warning", "⚠️" not in msg, msg)


# ── the alert that pointed at the wrong thing ────────────────────────────────
# On 2026-09-30 the orchestrator died at the Ledger freeze on a provider timeout, before
# any run_status was written. One second after the wrapper logged "ERROR: orchestrator
# failed" with a full traceback above it, the alert said: "No production run directory
# for today, and no orchestrator failure recorded in automation.log. The 09:00 job may
# not have started." Both halves of that sentence were false, and it sent the reader to
# cron while the provider was the cause.

# The shape of the real log, reduced: the wrapper's ERROR line with a traceback above it
# and NO run_status block anywhere before it.
CRASH_LOG = """\
[2026-09-30 21:33:41] === cripminds orchestrator ===
[2026-09-30 21:33:42] CODE_SHA=53d27df EXPECTED_CODE_SHA=53d27df DEPLOY_STATUS=PASS
2026-09-30 21:36:18,752 - INFO - CURRENT_ENGINE run production-20260930T193618Z-80ed601b
Traceback (most recent call last):
  File "automation/new_engine_v1/runner.py", line 504, in _run_story_architecture
    result = FC.run_free_argumentative_composition(
  File "automation/claude_cli_provider.py", line 345, in complete
    raise SubscriptionTimeout("claude CLI timed out after %ss"
claude_cli_provider.SubscriptionTimeout: claude CLI timed out after 600s
[2026-09-30 21:50:55] ERROR: orchestrator failed
"""


def _with_log(text):
    """Point the reporter at a log we control, restoring the real binding after."""
    tmp = tempfile.mkdtemp(prefix="drr-log-")
    p = pathlib.Path(tmp) / "automation.log"
    p.write_text(text, encoding="utf-8")
    return p


def test_a_crash_with_no_run_status_is_not_called_silence():
    day = datetime.date(2026, 9, 30)
    old = RPT.LOG
    RPT.LOG = _with_log(CRASH_LOG)
    try:
        lines = RPT.failure_lines(day)
        blob = " ".join(lines)
        check("it does not claim no failure was recorded",
              "no orchestrator failure" not in blob, blob[:160])
        check("it does not send the reader to cron",
              "may not have started" not in blob, blob[:160])
        check("it names the cause the traceback carries",
              "timeout" in blob.lower() or "timed out" in blob.lower(), blob[:200])
        check("and it says what to do about it",
              "latency" in blob or "retries once" in blob, blob[:240])
    finally:
        RPT.LOG = old


def test_a_day_with_no_error_line_still_says_the_job_may_not_have_run():
    """The fallback is still right for the case it was written for."""
    old = RPT.LOG
    RPT.LOG = _with_log("[2026-09-30 09:00:01] === cripminds orchestrator ===\n")
    try:
        lines = RPT.failure_lines(datetime.date(2026, 9, 30))
        check("a genuinely absent failure still reads as one",
              any("may not have started" in ln for ln in lines), lines)
    finally:
        RPT.LOG = old


def test_yesterdays_traceback_is_never_todays_cause():
    """THE BLOCKER an adversary found in the first version of this fix.

    `head` ran from the start of the log, so a crash today with no traceback of its own
    was explained with yesterday's exception -- confidently, and wrongly. Both ends are
    now anchored to the day.
    """
    log = (
        "[2026-09-29 21:00:00] === cripminds orchestrator ===\n"
        "Traceback (most recent call last):\n"
        "claude_cli_provider.SubscriptionLimit: you have reached your usage limit\n"
        "[2026-09-29 21:10:00] ERROR: orchestrator failed\n"
        "[2026-09-30 09:00:00] === cripminds orchestrator ===\n"
        "[2026-09-30 09:40:00] ERROR: orchestrator failed\n")
    old = RPT.LOG
    RPT.LOG = _with_log(log)
    try:
        blob = " ".join(RPT.failure_lines(datetime.date(2026, 9, 30)))
        check("yesterday's exception is not reported as today's cause",
              "usage limit" not in blob and "SubscriptionLimit" not in blob, blob[:200])
        check("today's crash is still reported as unexplained rather than as silence",
              "no run_status" in blob, blob[:200])
    finally:
        RPT.LOG = old


def test_a_recovered_failure_is_not_mistaken_for_the_crash():
    """A column-zero `SomethingTimeout: ...` is only a cause if a traceback began above it."""
    log = (
        "[2026-09-30 09:00:00] === cripminds orchestrator ===\n"
        "SubscriptionTimeout: a line of prose that is not a traceback at all\n"
        "[2026-09-30 09:40:00] ERROR: orchestrator failed\n")
    old = RPT.LOG
    RPT.LOG = _with_log(log)
    try:
        blob = " ".join(RPT.failure_lines(datetime.date(2026, 9, 30)))
        check("a bare matching line with no traceback above it is not read as the cause",
              "latency" not in blob, blob[:200])
    finally:
        RPT.LOG = old


def test_an_exception_with_no_message_does_not_swallow_the_next_line():
    """`\\s*` crosses newlines; `KeyError:` would have taken the ERROR line as its message."""
    log = (
        "[2026-09-30 09:00:00] === cripminds orchestrator ===\n"
        "Traceback (most recent call last):\n"
        "KeyError:\n"
        "[2026-09-30 09:40:00] ERROR: orchestrator failed\n")
    old = RPT.LOG
    RPT.LOG = _with_log(log)
    try:
        blob = " ".join(RPT.failure_lines(datetime.date(2026, 9, 30)))
        # Asserted on the attribution, not on the words: the honest "no traceback" fallback
        # legitimately contains the phrase "orchestrator failed", so the first version of
        # this check failed on its own correct output.
        check("the wrapper's own ERROR line is not attributed to the exception",
              "KeyError: [2026" not in blob and "KeyError: [" not in blob, blob[:200])
    finally:
        RPT.LOG = old


def test_help_is_chosen_by_the_class_not_by_a_substring():
    """"PermissionError: failed while handling SubscriptionTimeout" is a permission error."""
    log = (
        "[2026-09-30 09:00:00] === cripminds orchestrator ===\n"
        "Traceback (most recent call last):\n"
        "PermissionError: failed while handling SubscriptionTimeout\n"
        "[2026-09-30 09:40:00] ERROR: orchestrator failed\n")
    old = RPT.LOG
    RPT.LOG = _with_log(log)
    try:
        blob = " ".join(RPT.failure_lines(datetime.date(2026, 9, 30)))
        check("timeout advice is not offered for a permission error",
              "latency" not in blob, blob[:200])
        check("and the real exception is still named",
              "PermissionError" in blob, blob[:200])
    finally:
        RPT.LOG = old


def test_the_exception_class_is_enough_to_find_help():
    """A traceback says `SubscriptionTimeout`, never CLAUDE_SUBSCRIPTION_TIMEOUT.

    Without the alias the alert named the cause and then offered no help for it, which is
    how the original message managed to be useless in two different ways at once.
    """
    for cls in ("SubscriptionTimeout", "SubscriptionLimit", "SubscriptionAuthFailure"):
        check("help is reachable by the class name %r" % cls, cls in RPT.FAILURE_HELP)
    check("and the engine's own codes still reach the same help",
          RPT.FAILURE_HELP["SubscriptionLimit"]
          == RPT.FAILURE_HELP["CLAUDE_SUBSCRIPTION_LIMIT"])


def test_a_crash_with_neither_run_status_nor_traceback_says_so():
    old = RPT.LOG
    RPT.LOG = _with_log("[2026-09-30 21:50:55] ERROR: orchestrator failed\n")
    try:
        blob = " ".join(RPT.failure_lines(datetime.date(2026, 9, 30)))
        check("an unexplained crash is reported as unexplained, not as silence",
              "no run_status" in blob and "automation.log" in blob, blob[:200])
        check("and it is still not blamed on cron",
              "may not have started" not in blob, blob[:200])
    finally:
        RPT.LOG = old


def main():
    # DISCOVERED, NOT LISTED. The list this replaces named five tests by hand, so a test
    # added to this file and forgotten in that list ran never and said nothing -- which is
    # the same silent-omission shape as the alert these tests are about. Four new tests
    # were written against that list before this was noticed.
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        print("\n" + name)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL DAILY REPORT TESTS PASSED")


if __name__ == "__main__":
    main()
