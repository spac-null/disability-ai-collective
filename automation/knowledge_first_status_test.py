#!/usr/bin/env python3
"""Focused regression tests for the entry-local Perspective Library status gate."""
from __future__ import annotations

import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import knowledge_first as KF  # noqa: E402


def _entry(qid: str, status: str | None, question: str = "What does this reveal?") -> str:
    status_line = "" if status is None else "**STATUS:** %s\n" % status
    return "### %s — Synthetic question\n\n%s\n**QUESTION.** %s\n\n" % (
        qid, status_line, question)


def test_only_exact_approved_status_loads_from_each_entry():
    body = "".join([
        _entry("PR900-01", "**APPROVED_DURABLE**"),
        _entry("PR900-02", "**REJECTED**"),
        _entry("PR900-03", "CANDIDATE"),
        _entry("PR900-04", "**NEEDS_RESEARCH**"),
        _entry("PR900-05", "**RETIRED**"),
        _entry("PR900-06", None),
        _entry("PR900-07", "**APPROVED_DURABLEISH**"),
        _entry("PR900-08", "APPROVED-DURABLE"),
    ])
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "synthetic.md"
        path.write_text(body, encoding="utf-8")
        loaded = KF.load_questions(path.parent)

    assert [q["id"] for q in loaded] == ["PR900-01"]
    assert loaded[0]["status"] == "APPROVED_DURABLE"


def test_real_library_preserves_the_sixteen_approved_durable_ids():
    expected = {
        "PR001-02", "PR001-03", "PR001-05", "PR001-07", "PR001-09",
        "PR002-01", "PR002-02", "PR002-03", "PR002-05", "PR002-07",
        "PR003-03", "PR003-06", "PR003-08",
        "PR004-01", "PR004-02", "PR004-05",
    }
    loaded = KF.load_questions()
    assert {q["id"] for q in loaded} == expected
    assert all(q["status"] == "APPROVED_DURABLE" for q in loaded)


if __name__ == "__main__":
    test_only_exact_approved_status_loads_from_each_entry()
    test_real_library_preserves_the_sixteen_approved_durable_ids()
    print("ALL KNOWLEDGE-FIRST STATUS TESTS PASSED")
