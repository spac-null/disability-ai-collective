"""What this publication is, read from the document that says so.

NOTHING HAD EVER READ IT. `editorial-lens.md` is 23 lines at the repository root defining
what Crip Minds is and how its articles work. Before 2026-09-29 no prompt in this engine
loaded it. The only reference anywhere was `prose_audit.py` listing it as a file to audit
-- the document describing the prose was itself a subject of the audit, never an input to
the writing.

The same was true of the 43KB of Bregman craft analysis in `.claude/`: every mention of it
in code is a COMMENT citing it. The style rules were derived from that corpus once, by
hand, in August 2026, and the derived rules are what ship. The corpus has never been read
by a model.

AND THE LENS SAYS THE OPPOSITE OF WHAT THE ENGINE DOES:

    "Two kinds of knowledge. Experience is the argument. Scholarship is evidence.
     The ramp, the lag, the room full of eyes come first. Citations after, if at all."

The engine freezes scholarship first and then looks for an argument inside it, which is
why its most-pressed reader reaction is SOUNDS_LIKE_REPORT, seven times across ten
sessions.

IT IS QUOTED, NOT SUMMARISED. A paraphrase drifts and nobody notices; a quotation cannot.
This module reads the file and passes the bytes through. If the owner edits the lens, the
next run uses the edit -- which is the whole point of reading a document rather than
copying it into a constant.

IT LICENSES NO FACT. The lens describes how to write. It names no subject, no number and
no source, and nothing in it may be asserted as a fact about any story.
"""

from __future__ import annotations

import pathlib

LENS_FILE = "editorial-lens.md"


def _find(start: pathlib.Path | None = None) -> pathlib.Path | None:
    """The lens file, searched upward from this module.

    Searched rather than hardcoded because this package sits two directories below the
    repository root and is imported from several working trees.
    """
    here = (start or pathlib.Path(__file__)).resolve()
    for parent in [here] + list(here.parents):
        candidate = parent / LENS_FILE
        if candidate.is_file():
            return candidate
    return None


def _strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def load(start: pathlib.Path | None = None) -> str:
    """The lens as the owner wrote it, or "" if the file is absent.

    Absent means absent: a missing lens leaves every prompt byte-identical to what it was
    before this module existed, rather than substituting a remembered version of it.
    """
    path = _find(start)
    if path is None:
        return ""
    try:
        return _strip_front_matter(path.read_text(encoding="utf-8")).strip()
    except OSError:
        return ""


def block(start: pathlib.Path | None = None) -> str:
    """The lens, framed for a writer system. Empty when there is no lens to read."""
    lens = load(start)
    if not lens:
        return ""
    return "\n".join([
        "",
        "WHAT THIS PUBLICATION IS. Written by the person it belongs to. This is not a",
        "rule to satisfy and not a style to imitate: it is what the work is for, and the",
        "reason a reader is here at all.",
        "",
        lens,
        "",
        "It licenses no fact. Nothing in it may be asserted about any subject.",
    ])
