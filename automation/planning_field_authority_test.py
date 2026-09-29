#!/usr/bin/env python3
"""Planning fields that reach the Writer may not launder a fact into approved surface.

THE DEFECT, MEASURED 2026-09-29 AND REPRODUCED HERE.

`factual_surface_audit` takes the RENDERED PACKET as its approved surface -- that is
deliberate and documented. `architect_prose_audit` is the screen that stops the plan from
putting something into that packet which no fact carries, and its field list was shorter
than the set of fields `render()` actually prints. Two were missing:

    beats[].must_not_say_yet   render() prints it as "not yet: ..."   (story.py:1324)
    prohibitions               render() prints them under RULES       (story.py:1393)

So an unsupported token placed in either passed `check_architecture`, reached the prompt,
and thereafter SILENCED the article-level screen for that same token -- the planning field
did not merely carry the invention, it licensed it.

Observed before the fix, on a fixture that is otherwise clean:

    baseline                  check_architecture []   audit(article) -> ['2027']   caught
    must_not_say_yet <- 2027  check_architecture []   audit(article) -> []         LAUNDERED
    prohibitions     <- 2027  check_architecture []   audit(article) -> []         LAUNDERED
    CONTROL: happens <- 2027  check_architecture REFUSES

The control is what makes it conclusive: the identical token in a field that WAS scanned
is refused, so the gap was the field list and nothing else.

A SECOND, QUIETER HALF. `composition._sentence_initial` decides which entity hits are
discarded as grammar capitals, and it reads its own hard-coded field list. That list was
short too, so a proper noun appearing only in `must_not_say_yet` would never be found
mid-sentence, `_sentence_initial` would return True, and the hit would be dropped at
composition.py:1565. Adding the field to the audit alone fixes numbers and leaves entities
laundered, which is why both lists are tested.

ONLY ONE OF THE TWO FIELDS IS FIXED HERE, AND THE OTHER IS ASSERTED AS A GAP.

`must_not_say_yet` is screened now. `prohibitions` deliberately are NOT, because the
obvious fix is refuted by a fixture already in the tree. roman's plan says:

    "Do not compare Roman's data release to Hubble's or Webb's release practices."

"Webb" is in no fact -- and that is exactly why it is forbidden, since the Writer knows
what Webb is without being told. Screening prohibitions for surface refuses well-formed
editorial guards. The laundering is real, but the fix belongs at the other end: exclude
prohibition lines from the approved surface `factual_surface_audit` builds out of the
rendered packet, so that naming a thing in order to forbid it does not license it. Until
that lands, the two `KNOWN GAP` cases below assert the CURRENT behaviour so the hole stays
visible and so that whoever closes it is told by a failing test to come and update this.

A THIRD THING, FOUND WHILE FIXING THE FIRST. The audit joined its fields with " ".
`_entities` exempts sentence-initial capitals, so a space join put every short field's
first word mid-sentence, where the exemption does not apply. That was the entire
pre-existing `roman` failure on "Naming", and adding fields reproduced it on `jia` with
"What". Joined on a sentence boundary now, and `story_architecture_test` is green for the
first time.

Run: python3 automation/planning_field_authority_test.py
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as C   # noqa: E402
from new_engine_v1 import story as ST        # noqa: E402
import definition_support_test as DS         # noqa: E402

# A year and a proper noun, neither in any fact of the fixture ledger.
UNSUPPORTED_YEAR = "2027"
UNSUPPORTED_NAME = "Zorbath"
ARTICLE_YEAR = ("The council published a ranking sheet in March. "
                "The catalogue is due again in 2027.")
ARTICLE_NAME = ("The council published a ranking sheet in March. "
                "It was compiled by Zorbath.")

FAILED: list = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILED.append(name)


def audited(arch: dict, ledger: dict, article: str) -> dict:
    packet, _ = C.writer_packet(arch, ledger)
    return ST.factual_surface_audit(article, packet, ledger)


def main() -> int:
    ledger = DS.LEDGER

    # ── the fixture is clean, and the screen works when nothing is hidden ──────
    base = DS.arch()
    check("fixture architecture validates before anything is injected",
          C.check_architecture(base, ledger) == [],
          str(C.check_architecture(base, ledger))[:120])
    a = audited(base, ledger, ARTICLE_YEAR)
    check("an unsupported year in the ARTICLE is reported when nothing hid it",
          a.get("unapproved_numbers") == [UNSUPPORTED_YEAR],
          str(a.get("unapproved_numbers")))

    # ── the control: a scanned field refuses the token ────────────────────────
    ctrl = DS.arch()
    ctrl["beats"][0]["happens"] += " in %s" % UNSUPPORTED_YEAR
    check("CONTROL: the same year in `happens` is refused by check_architecture",
          C.check_architecture(ctrl, ledger) != [])

    # ── must_not_say_yet: now screened ────────────────────────────────────────
    arch = DS.arch()
    arch["beats"][0]["must_not_say_yet"] = "the %s catalogue" % UNSUPPORTED_YEAR
    check("an unsupported NUMBER in must_not_say_yet is refused",
          C.check_architecture(arch, ledger) != [],
          "check_architecture returned [] -- the field is not screened")

    arch = DS.arch()
    arch["beats"][0]["must_not_say_yet"] = "anything about %s" % UNSUPPORTED_NAME
    check("an unsupported ENTITY in must_not_say_yet is refused",
          C.check_architecture(arch, ledger) != [],
          "check_architecture returned [] -- _sentence_initial may be dropping it")

    # ── prohibitions: the blind spot, asserted ON PURPOSE ─────────────────────
    #
    # This is a KNOWN OPEN DEFECT and the assertion below records it rather than hides
    # it. Prohibitions launder: a token named in one becomes approved surface for
    # factual_surface_audit. Screening them here is the wrong fix, and the roman fixture
    # is why -- "Do not compare Roman's data release to Hubble's or Webb's release
    # practices" names Webb, which is in no fact, and that is exactly why it is forbidden.
    # A prohibition must be free to name what it forbids.
    #
    # The fix belongs at the other end: exclude prohibition lines from the approved
    # surface factual_surface_audit builds from the rendered packet. Until that lands,
    # this test asserts the CURRENT behaviour so the gap stays visible and so that
    # whoever fixes it is told, by a failing test, to come here and update it.
    #
    # DO NOT DELETE THIS CASE TO MAKE THE SUITE LOOK BETTER.
    arch = DS.arch()
    arch["prohibitions"] = (list(arch.get("prohibitions") or [])
                            + ["Do not mention the %s edition." % UNSUPPORTED_YEAR])
    accepted = C.check_architecture(arch, ledger) == []
    check("KNOWN GAP: a prohibition may still name an unsupported number", accepted,
          "prohibitions are now screened -- if that is intended, update this test")
    if accepted:
        a = audited(arch, ledger, ARTICLE_YEAR)
        check("KNOWN GAP: and that silences the article screen for it",
              a.get("unapproved_numbers") == [],
              "the laundering appears to be fixed -- update this test and say where")

    # ── the field lists must not drift apart again ────────────────────────────
    import inspect
    audit_src = inspect.getsource(ST.architect_prose_audit)
    sentinit_src = inspect.getsource(C._sentence_initial)
    for field in ("must_not_say_yet", "why_reader_wants_next"):
        check("architect_prose_audit reads %r" % field, field in audit_src)
        check("_sentence_initial reads %r" % field, field in sentinit_src,
              "an entity seen only in this field would be dropped as a grammar capital")

    # ── the join that made the exemption fail ─────────────────────────────────
    # Fields are joined on a sentence boundary, not a space: _entities exempts
    # sentence-initial capitals, and " ".join put each short field's first word
    # mid-sentence. That was the whole of the pre-existing `roman` "Naming" failure.
    check("architect_prose_audit joins its fields on a sentence boundary",
          '". ".join' in audit_src,
          "a space join puts every field-initial capital mid-sentence")

    print("-" * 60)
    if FAILED:
        print("FAILED: %d" % len(FAILED))
        for f in FAILED:
            print("   - " + f)
        return 1
    print("all planning-field authority checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
