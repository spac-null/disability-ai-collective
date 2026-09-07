#!/usr/bin/env python3
"""
architecture_writer_boundary_test.py -- Architecture owns ORDER; the ledger owns FACTUAL
PERMISSION.

THE PRODUCTION FAILURE. In production-20260907T160137Z-831b0d44 -- a Guardian piece on a
documentary shot by blind students, the strongest candidate the engine has surfaced --
Grounding blocked five findings that are all one word: "teenagers".

    RESEARCH_PACK.json   0 occurrences      "kids"  31
    LEDGER.json          0 occurrences      "kids"  26
    ARCHITECTURE.json    2 occurrences   <- first appearance
    WRITER_PACKET.json   1 occurrence
    ARTICLE_FINAL.md     1 occurrence
    EDITORIAL_PACKAGE    4 occurrences

The sources say "kids" throughout; the anchor has competitors running "from first grade
through high school" and one of the three chosen filmmakers aged ten. Of the architect's
two occurrences only one crossed into the packet -- `reader_initial_state` -- and
`render()` handed it to the Writer as "The reader should first understand only this: ...".

That made generated prose into permission. The approved surface every later screen
measures the article against IS the render, so a sentence the architect invented arrives
pre-licensed. `continuity.architect_rhetoric` has separately measured the Writer
transcribing these fields at 0.90-0.93 similarity, so the route from architect sentence to
published sentence is short and known.

WHAT THESE TESTS HOLD. The unsupported architect phrase no longer reaches the Writer as
permission; the supported material still does; and the ordering apparatus Story
Architecture exists for -- opening, beat sequence, withheld information, turn, ending --
is all still there. No gate was added and no word was blacklisted.

Offline: the real retained architecture is reconstructed from the run's own values. No
provider, no network, no article regenerated.

USAGE: python3 automation/architecture_writer_boundary_test.py
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import story as ST                                # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:240]))
    if not ok:
        FAILURES.append(label)


# The architecture as the run actually produced it, including the unsupported noun. It is
# reproduced here on purpose: the historical artefact is the regression case.
GUARDIAN_ARCH = {
    "article_type": "NARRATIVE_ARTICLE",
    "story_spine": "A documentary about a braille competition was shot by the blind kids "
                   "attending it, and the crew cut it from what they brought back.",
    "opening_object_or_event": "The drives of footage coming back each evening from "
                               "cameras the crew had handed out that morning",
    "reader_initial_state": "That the material of this film arrived every evening as "
                            "drives of footage from nine blind teenagers whom the crew "
                            "had equipped in the morning and then left alone",
    "beats": [
        {"beat_id": "B1", "happens": "the crew hands out the cameras at the start of "
                                     "the day", "concrete_carrier": "the cameras",
         "facts_allowed": ["F59", "F61"], "concept_introduced": "",
         "must_not_say_yet": "that only three of the nine end up in the film"},
        {"beat_id": "B2", "happens": "the footage comes back and is copied to drives",
         "concrete_carrier": "the drives", "facts_allowed": ["F61"],
         "concept_introduced": "", "must_not_say_yet": ""},
    ],
    "turn": "The film's authorship sits with the kids who carried the cameras.",
    "crip_turn": "What the crew edited was not their own footage.",
    "ending_move": "The finished cut, narrowed to three of the nine.",
    "use_facts": ["F59", "F61"],
    "use_quotes": [],
    "definitions": {},
    "prohibitions": [],
    "cut_evidence": [],
}
# The ledger facts the grounder cited as carrying the routine and the headcount.
FACTS = {
    "F59": "Grabias said nine of the kids agreed to be filmmakers, to document their "
           "experiences and to carry cameras for the weekend.",
    "F61": "Grabias said the crew met the kids each morning to set up cameras, charge "
           "batteries and ready memory cards, then let them loose, and collected the "
           "cameras and copied the footage to drives at day's end.",
}
LENS = {"verdict": "PUBLISHABLE", "lens_claim": "authorship of the footage"}


def _packet():
    return ST.build_packet(GUARDIAN_ARCH, LENS, FACTS)


def _render():
    return ST.render(_packet())


# ── 1 + 2: the architecture keeps it; the Writer is not given it ────────────────────
def test_the_architecture_still_carries_the_historical_phrase():
    check("the retained architecture still contains the unsupported phrase",
          "nine blind teenagers" in GUARDIAN_ARCH["reader_initial_state"])
    check("and the packet still carries the field for audit and diagnostics",
          "teenagers" in _packet()["reader_initial_state"])
    check("so the leak scanners and architect audits still see it",
          any(f == "reader_initial_state" and "teenagers" in t
              for f, t in ST.generated_packet_text(_packet())))


def test_the_writer_facing_render_does_not_license_it():
    r = _render()
    check("the Writer is not shown 'teenagers'", "teenager" not in r.lower(), r[:400])
    check("nor the architect's sentence in any form",
          "arrived every evening as drives" not in r)
    check("and the old licensing frame is gone",
          "The reader should first understand only this" not in r)


# ── 3: everything the evidence does support is still there ──────────────────────────
def test_the_supported_material_still_reaches_the_writer():
    r = _render()
    for phrase, why in (("kids", "the word the sources actually use"),
                        ("nine of the kids", "the supported headcount"),
                        ("each morning", "the supported routine"),
                        ("charge batteries", "the supported action"),
                        ("ready memory cards", "the supported action"),
                        ("cameras", "the supported object"),
                        ("weekend", "the supported span"),
                        ("copied the footage to drives", "the supported sequence")):
        check("still licensed: %s (%s)" % (phrase, why), phrase in r, r[:300])
    check("the licensed facts arrive as facts, under their beats",
          r.count("     - Grabias said") == 3, r)


# ── 4: the ordering apparatus is intact ─────────────────────────────────────────────
def test_story_architecture_still_orders_the_article():
    r = _render()
    for section in ("WHAT THE STORY IS", "OPEN ON", "THE PATH, IN ORDER", "THE TURN",
                    "WHAT THE READER SHOULD UNDERSTAND DIFFERENTLY BY THE END",
                    "END ON"):
        check("the render still has %s" % section, section in r, r[:200])
    check("the opening anchor is still given",
          "drives of footage coming back each evening" in r)
    check("the beats are still numbered in order",
          r.index("1. the crew hands out the cameras") < r.index(
              "2. the footage comes back"), r)
    check("each beat still names its carrier",
          "carried by: the cameras" in r and "carried by: the drives" in r)
    check("DELAYED INFORMATION SURVIVES -- the real order mechanism",
          "not yet: that only three of the nine end up in the film" in r, r)
    check("the turn and the ending are still given",
          "authorship sits with the kids" in r and "narrowed to three" in r)
    check("and the reader still starts from nothing, stated without asserting a fact",
          "The reader begins knowing nothing beyond what this opening puts" in r, r)


# ── 5: nothing supported was stripped as collateral ─────────────────────────────────
def test_no_supported_texture_was_stripped_as_collateral():
    r = _render()
    check("the other architect fields are untouched",
          GUARDIAN_ARCH["story_spine"] in r
          and GUARDIAN_ARCH["opening_object_or_event"] in r
          and GUARDIAN_ARCH["turn"] in r
          and GUARDIAN_ARCH["crip_turn"] in r
          and GUARDIAN_ARCH["ending_move"] in r)
    check("every beat's own prose still reaches the Writer",
          all(b["happens"] in r for b in GUARDIAN_ARCH["beats"]))
    # An architecture with a supported reader_initial_state loses nothing it was
    # carrying either: the field was a restatement, not a fact source.
    ok_arch = dict(GUARDIAN_ARCH,
                   reader_initial_state="That the kids carried the cameras themselves")
    r2 = ST.render(ST.build_packet(ok_arch, LENS, FACTS))
    check("a supported initial state is treated the same way -- no special case",
          "That the kids carried the cameras themselves" not in r2
          and "The reader begins knowing nothing" in r2)


def test_no_new_gate_and_no_word_list():
    src = (HERE / "new_engine_v1" / "story.py").read_text()
    check("no age word was blacklisted", "teenager" not in src.lower().replace(
        "teenagers\" into reader_initial_state", "").replace(
        "nine blind teenagers", ""))
    check("render still takes only the packet, with no new validator",
          "def render(packet: dict) -> str:" in src)
    check("build_packet still carries the field",
          '"reader_initial_state": arch.get("reader_initial_state", "")' in src)
    check("the field is still leak-scanned",
          '"reader_initial_state"' in src.split("_GENERATED_PACKET_FIELDS")[1][:200])


def main():
    for fn in (test_the_architecture_still_carries_the_historical_phrase,
               test_the_writer_facing_render_does_not_license_it,
               test_the_supported_material_still_reaches_the_writer,
               test_story_architecture_still_orders_the_article,
               test_no_supported_texture_was_stripped_as_collateral,
               test_no_new_gate_and_no_word_list):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL ARCHITECTURE/WRITER BOUNDARY TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
