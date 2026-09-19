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


def main():
    for fn in [test_ok_run_status_is_not_a_warning,
               test_ok_in_dict_shape_is_also_silent,
               test_provider_failure_string_is_reported,
               test_provider_failure_dict_is_reported,
               test_absent_run_status_is_silent]:
        print("\n" + fn.__name__)
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
