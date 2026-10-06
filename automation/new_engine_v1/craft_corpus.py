"""The craft corpus the house style was derived from, read rather than remembered.

NOTHING HAD EVER READ IT. 43KB of Bregman craft analysis sits in `.claude/`, and every
reference to it anywhere in this engine is a COMMENT citing it. `style_rules.py` and
`composition.WRITER_CRAFT_DELTA` were derived from that corpus once, by hand, in August
2026; the derived rules are what ships. The corpus itself has never been an input to a
prompt, so the rules have drifted from their source and nothing notices.

The 2026-09-29 offline probe read it for the first time, on the same frozen evidence a
scheduled run had just produced, and the difference was not marginal -- see
free_composition.py for the measurement. This module is what makes that repeatable.

IT IS QUOTED, NOT SUMMARISED, for the same reason `editorial_lens.py` is: a paraphrase
drifts silently and a quotation cannot, and an owner who edits the corpus reaches the next
run without touching code.

IT IS A CRAFT REFERENCE, NOT A STYLE TO COPY. The framing that carries it into the prompt
says so in as many words, and the reader contract repeats it: learn how the writing MOVES
-- pacing, argument, concretion, explanation, surprise, economy -- never its sentences and
never its subjects.

IT LICENSES NO FACT. The corpus is about writing. It names no subject, number or source
belonging to any story this engine will ever run, and nothing in it may be asserted.
"""

from __future__ import annotations

import pathlib

# In the order the probe read them, because that is the order that was measured. The
# anchor corpus is the bulk of it; the two analyses are the reasoning about it.
CORPUS_FILES = (
    (".claude/bregman-anchor-corpus.md", "BREGMAN ANCHOR CORPUS"),
    (".claude/bregman-architecture-analysis.md", "BREGMAN ARCHITECTURE ANALYSIS"),
    (".claude/bregman-write-economy-analysis.md", "BREGMAN WRITE ECONOMY ANALYSIS"),
)

# NINE TENTHS OF THE ANCHOR CORPUS IS NOT CRAFT MATERIAL (2026-10-06). The file is 26,472
# characters and the Writer was being handed all of it. Measured by section:
#
#     Section 1  ESSAY/REPORTAGE register      2,540   the ONLY part marked "use these"
#     Section 2  ORATORY/LECTURE register      1,508   marked "do NOT use for calibration"
#     Section 3  how to use this file            869   says it is a JUDGE reference
#     Section 4  a rejected 10-section template 5,200   described in followable detail
#     Sections 5-7  session notes, audits, blueprints  15,849
#
# Section 3 states the point in its own words: this file's value is "as a fixed, reusable
# judge reference ... not as a magic ingredient that fixes generation on its own if fed to
# a writer or fixer model." It was being fed to a writer model on every run.
#
# Three of those sections are worse than noise. Section 2 is a register the file itself
# says calibrates toward "different, sometimes contradictory targets". Section 4 sets out
# a fixed 10-section essay template -- Opening Scene 200-300w, Surprise, Zoom Out ... --
# that was CONSIDERED AND REJECTED for this pipeline, in enough detail to be followed by a
# model that does not reach the paragraph explaining it was rejected. Sections 5-7 are
# minutes.
#
# So the anchor corpus is cut at the first heading after Section 1, and the other two
# files are sent whole because they ARE craft documents end to end -- the seven-technique
# architecture analysis and the write-economy substitution table.
ANCHOR_STOP = "## Section 2"


def _root(start: pathlib.Path | None = None) -> pathlib.Path | None:
    """The repository root, found by walking up to the directory holding `.claude/`.

    Searched rather than hardcoded for the same reason `editorial_lens._find` searches:
    this package sits two directories below the root and is imported from several
    working trees, worktrees and probe checkouts.
    """
    here = (start or pathlib.Path(__file__)).resolve()
    for parent in [here] + list(here.parents):
        if (parent / ".claude").is_dir():
            return parent
    return None


def load(start: pathlib.Path | None = None) -> str:
    """The corpus as the owner wrote it, or "" when none of it can be read.

    A file that is missing is SKIPPED rather than substituted: this returns the parts that
    exist, and returns "" only when nothing does. Absent means absent -- no remembered
    version of the corpus is ever synthesised here, because a summary of the corpus is
    exactly the thing that already shipped and already drifted.
    """
    root = _root(start)
    if root is None:
        return ""
    parts = []
    for rel, heading in CORPUS_FILES:
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if rel.endswith("bregman-anchor-corpus.md") and ANCHOR_STOP in text:
            text = text.split(ANCHOR_STOP, 1)[0].strip()
        if text:
            parts.append("=== %s ===\n%s" % (heading, text))
    return "\n\n".join(parts)


def block(start: pathlib.Path | None = None) -> str:
    """The corpus, framed for a writer system. Empty when there is nothing to read.

    The framing is the probe's own, kept verbatim: it is the sentence that made the
    difference between a model imitating Bregman's sentences and a model learning how his
    paragraphs move.
    """
    corpus = load(start)
    if not corpus:
        return ""
    return "\n\n".join([
        "THE CRAFT CORPUS THIS PUBLICATION'S HOUSE STYLE WAS DERIVED FROM. It is a "
        "reference for HOW WRITING MOVES, not a style to imitate and not a source of "
        "facts. Learn its pacing, its argument movement, its concreteness, the way it "
        "explains a hard idea, its surprises and its economy. Never reuse its wording, "
        "its distinctive phrases, its subjects or its sentences. It licenses no fact: "
        "nothing in it may be asserted about the story you are writing.",
        corpus,
    ])
