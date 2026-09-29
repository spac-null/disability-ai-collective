#!/usr/bin/env python3
"""A span that opens on a demonstrative nothing establishes is reported, and blocks nothing.

The fixture is the real failure, reduced: a source whose second sentence refers back to its
first, with a ledger that extracted only the second. That is
production-20260928T070709Z-9b443d22's F48 -- "Prinzhorn bildet eines dieser Blaetter..."
retained while the sentence saying what the sheets are was never cited.

Both directions are asserted, because a detector that only ever fires is not a detector:
adding the antecedent fact must clear it, and that is the case the first implementation of
this got wrong. It matched the demonstrative's head noun against the other propositions,
which cannot work when spans are the source's own language and propositions are English --
"Blaetter" never matches "letters" -- so it flagged the REPAIRED ledger too.

Run: python3 automation/ledger_anaphora_test.py
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import anaphora as AN   # noqa: E402

# Padded on purpose. The lookback is 400 characters, so an unpadded fixture puts every
# sentence inside it and "a fact from elsewhere does not count" cannot be tested at all --
# which is how the first version of this file failed: the assertion was right and the
# fixture was too short to exercise it.
_FILLER = ("Die Sammlung waechst bestaendig und umfasst Werke aus mehr als hundert "
           "Jahren, darunter Zeichnungen, Texte und Musikstuecke aus vielen Anstalten "
           "des deutschsprachigen Raumes, die zu ganz unterschiedlichen Zeiten nach "
           "Heidelberg gelangt sind und dort seither verwahrt werden. ") * 3
SOURCE = (
    "Werke, die die meisten Leute heute im Kopf behalten, sind die Briefe von Emma Hauck. "
    + _FILLER +
    "Sie wiederholt in diesen so oft das bittende Herzensschatzi komm, dass sich eine "
    "Grauschwaerzung der Flaeche ergibt. "
    "Prinzhorn bildet eines dieser Blaetter in seinem Buch ab, allerdings auf dem Kopf "
    "stehend, mit einer falschen Autorenzuweisung."
)
PACK = {"sources": [{"source_id": "S5", "text": SOURCE}]}

SPAN_DEPENDENT = ("Prinzhorn bildet eines dieser Blaetter in seinem Buch ab, allerdings "
                  "auf dem Kopf stehend, mit einer falschen Autorenzuweisung.")
SPAN_ANTECEDENT = ("Sie wiederholt in diesen so oft das bittende Herzensschatzi komm, "
                   "dass sich eine Grauschwaerzung der Flaeche ergibt.")
SPAN_UNRELATED = "Werke, die die meisten Leute heute im Kopf behalten, sind die Briefe"

BROKEN = {"F48": {"proposition": "Prinzhorn reproduced one of the sheets upside down.",
                  "support_span": SPAN_DEPENDENT, "evidence_ids": ["S5"]}}
REPAIRED = dict(BROKEN, F57={
    "proposition": "Roeske described the letters as repeating one plea until the surface "
                   "greys.",
    "support_span": SPAN_ANTECEDENT, "evidence_ids": ["S5"]})

FAILED: list = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILED.append(name)


def main() -> int:
    broken = AN.orphaned_spans(BROKEN, PACK, selected=["F48"])
    check("a span opening on a demonstrative with no antecedent is reported",
          [h["fact_id"] for h in broken] == ["F48"], str(broken))
    if broken:
        check("and it says what the ledger failed to cite",
              "Grauschwaerzung" in broken[0]["uncited_before_it"],
              broken[0]["uncited_before_it"][-90:])
        check("and it records that the fact was selected", broken[0]["selected"] is True)

    repaired = AN.orphaned_spans(REPAIRED, PACK, selected=["F48"])
    check("adding the antecedent clears it", repaired == [], str(repaired))

    # The first implementation matched head nouns across languages and failed exactly here:
    # the antecedent fact says "letters" where the span says "Blaetter".
    check("cleared even though the antecedent's proposition shares no noun with the span",
          "Blaetter" not in REPAIRED["F57"]["proposition"] and repaired == [])

    far = dict(BROKEN, F99={"proposition": "An unrelated line from the top of the page.",
                            "support_span": SPAN_UNRELATED, "evidence_ids": ["S5"]})
    check("a fact from elsewhere in the source does not count as the antecedent",
          [h["fact_id"] for h in AN.orphaned_spans(far, PACK)] == ["F48"],
          "only material within LOOKBACK_CHARS before the span may clear it")

    check("a span with no demonstrative is never reported",
          AN.orphaned_spans({"F1": {"proposition": "x", "support_span": SPAN_UNRELATED}},
                            PACK) == [])
    check("a ledger carrying scalar metadata beside its facts does not crash",
          AN.orphaned_spans(dict(BROKEN, facts=55, span_verified=True), PACK) != [])
    check("no pack means no claim either way", AN.orphaned_spans(BROKEN, {}) == [])

    # TELEMETRY, NOT A GATE. The stage returns it; nothing raises on it.
    import inspect
    from new_engine_v1 import composition as C
    src = inspect.getsource(C.freeze_ledger)
    check("freeze_ledger reports it", "anaphora" in src)
    check("and does not raise on it",
          not any("anaphora" in ln and "raise" in ln for ln in src.splitlines()),
          "a detector calibrated on its own sample must not block a run")

    print("-" * 60)
    if FAILED:
        print("FAILED: %d" % len(FAILED))
        for f in FAILED:
            print("   - " + f)
        return 1
    print("all ledger-anaphora checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
