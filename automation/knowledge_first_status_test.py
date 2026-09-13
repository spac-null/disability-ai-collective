#!/usr/bin/env python3
"""Focused regression tests for the entry-local Perspective Library status gate."""
from __future__ import annotations

import pathlib
import re
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


#: The sixteen instruments approved across PR001-PR004, before the 2026-09-13 owner
#: directive that added PR005-PR008. Asserted as a SUBSET from here on, never as equality:
#: the pool is expected to grow, and pinning it to a snapshot turns every authorised
#: addition into a test failure that says nothing about correctness. What must never happen
#: is one of these quietly disappearing, and that is what a subset check catches.
FOUNDATION_SIXTEEN = {
    "PR001-02", "PR001-03", "PR001-05", "PR001-07", "PR001-09",
    "PR002-01", "PR002-02", "PR002-03", "PR002-05", "PR002-07",
    "PR003-03", "PR003-06", "PR003-08",
    "PR004-01", "PR004-02", "PR004-05",
}


def test_real_library_preserves_the_foundation_approved_durable_ids():
    loaded = KF.load_questions()
    ids = {q["id"] for q in loaded}
    missing = FOUNDATION_SIXTEEN - ids
    assert not missing, "foundation instruments vanished from the library: %s" % sorted(missing)
    assert all(q["status"] == "APPROVED_DURABLE" for q in loaded)
    # The status filter is the only gate on loading, so it is checked against the FILES
    # rather than against a list anyone has to remember to update.
    approved_in_files = set()
    for f in sorted(KF.PERSPECTIVE_DIR.glob("*.md")):
        if f.name in ("INDEX.md", "README.md"):
            continue
        text = f.read_text(encoding="utf-8")
        entries = list(re.finditer(r"^### (PR\d{3}-\d{2}) — ", text, re.M))
        for i, m in enumerate(entries):
            end = entries[i + 1].start() if i + 1 < len(entries) else len(text)
            body = text[m.end():end]
            status = re.search(r"^\*\*STATUS:\*\*\s*\**(\w+)", body, re.M)
            has_q = re.search(r"^\*\*QUESTION\.\*\*", body, re.M)
            if status and status.group(1) == "APPROVED_DURABLE" and has_q:
                approved_in_files.add(m.group(1))
    assert ids == approved_in_files, (
        "loaded set differs from the files' own APPROVED_DURABLE entries: "
        "only-loaded=%s only-in-files=%s"
        % (sorted(ids - approved_in_files), sorted(approved_in_files - ids)))


if __name__ == "__main__":
    test_only_exact_approved_status_loads_from_each_entry()
    test_real_library_preserves_the_foundation_approved_durable_ids()
    print("ALL KNOWLEDGE-FIRST STATUS TESTS PASSED")
