#!/usr/bin/env python3
"""A join is evidence or it does not exist, and it reaches the Writer as a permission.

WHY THE MECHANISM EXISTS. An essay is asserted relations between facts; a report is the
same facts with the joins removed. This engine froze propositions and licensed nothing
else, so the Writer could state a fact and never connect two -- and the only thing
structurally available to it was a report. The owner's most-pressed reaction across ten
reading sessions is SOUNDS_LIKE_REPORT, seven times. On 2026-09-29 the same unlicensed
join returned through five independent controls, because the Writer was reaching for an
argument the evidence was never allowed to carry.

So a relation now gets exactly the guarantee a fact gets -- a verbatim span from a source
it cites -- and nothing more. Every refusal below is deterministic. Whether the span
genuinely asserts THAT join is the freezing model's judgement, the same as the
faithfulness of a proposition to its span; this suite does not pretend otherwise.

Run: python3 automation/ledger_relations_test.py
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as C      # noqa: E402
from new_engine_v1 import relations as REL      # noqa: E402
from new_engine_v1 import story as ST           # noqa: E402
import definition_support_test as DS            # noqa: E402

SRC = ("Roeske said the works most people remember are Emma Hauck's letters. "
       "Prinzhorn reproduced one of those sheets in his book upside down, merely as an "
       "example of scribbling with a first tendency to order.")
SRCS = {"S5": SRC, "S1": "An unrelated page about opening hours and ticket prices."}
LEDGER = {"F01": {"proposition": "The remembered works are Emma Hauck's letters."},
          "F02": {"proposition": "Prinzhorn reproduced a sheet upside down."}}
GOOD = {"relation_id": "R01", "subject": "F01", "object": "F02", "kind": "TEMPORAL",
        "evidence_ids": ["S5"],
        "support_span": "Prinzhorn reproduced one of those sheets in his book upside down"}

FAILED: list = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILED.append(name)


def main() -> int:
    check("a relation with a real span from the source it cites is accepted",
          REL.validate_relations([GOOD], LEDGER, SRCS) == {},
          str(REL.validate_relations([GOOD], LEDGER, SRCS)))

    # ── every refusal, and each is a way a join could be invented ─────────────
    for name, mutate in (
        ("a span from a source it does not cite", {"evidence_ids": ["S1"]}),
        ("a span in NO source -- the join itself invented",
         {"support_span": "Prinzhorn disliked the letters and said so plainly"}),
        ("an endpoint that is not a fact", {"object": "F99"}),
        ("a fact joined to itself", {"object": "F01"}),
        ("a relation kind outside the closed vocabulary", {"kind": "BECAUSE_I_SAY_SO"}),
        ("a span too short to carry a join", {"support_span": "upside down"}),
        ("no cited source at all", {"evidence_ids": []}),
    ):
        bad = REL.validate_relations([dict(GOOD, **mutate)], LEDGER, SRCS)
        check("refused: " + name, bad != {},
              "accepted something it should not have")

    # THE SPAN MUST BE IN THE CITED SOURCE, NOT MERELY IN THE CORPUS. A span quoted from
    # S5 and attributed to S1 is a provenance error, and check_ledger learned that lesson
    # for facts before relations existed.
    cross = REL.validate_relations([dict(GOOD, evidence_ids=["S1"])], LEDGER, SRCS)
    check("a cross-cited span says where it actually appears",
          any("appears in" in m for ms in cross.values() for m in ms),
          str(cross))

    check("usable() drops the bad and keeps the good",
          [r["relation_id"] for r in
           REL.usable([GOOD, dict(GOOD, relation_id="R02", object="F99")],
                      LEDGER, SRCS)] == ["R01"])

    # ── reaching the Writer ───────────────────────────────────────────────────
    ledger, arch = DS.LEDGER, DS.arch()
    use = arch.get("use_facts") or []
    rels = [{"relation_id": "R01", "subject": use[0], "object": use[1], "kind": "CAUSE",
             "evidence_ids": ["S0"], "support_span": "x" * 40}]
    packet, prompt = C.writer_packet(arch, ledger, None, rels)
    check("the packet carries the join", len(packet.get("relations") or []) == 1)
    check("the Writer is shown it", "JOINS YOU MAY ASSERT" in prompt)
    check("as a permission, not an instruction", "leave one unused" in prompt,
          "instruction accumulation is this engine's measured failure mode")
    check("and every OTHER join is still barred", "never to assert" in prompt)
    check("the packet still validates", ST.validate_packet(packet) == [],
          str(ST.validate_packet(packet)))

    # The block shows PROPOSITIONS. Fact ids are machine identity and the packet carries
    # none of them; a join the Writer cannot read is a join it cannot use.
    check("the block shows propositions, never fact ids",
          not any(fid in prompt.split("JOINS YOU MAY ASSERT")[-1].split("END ON")[0]
                  for fid in use))

    _, no_rel = C.writer_packet(arch, ledger, None, None)
    check("no joins means no block at all", "JOINS YOU MAY ASSERT" not in no_rel)

    # BOTH endpoints must be selected. A join to a fact the Writer was never given is an
    # invitation to reach outside the packet.
    outside = [{"relation_id": "R09", "subject": use[0], "object": "F9999",
                "kind": "CAUSE", "evidence_ids": ["S0"], "support_span": "y" * 40}]
    _, pr = C.writer_packet(arch, ledger, None, outside)
    check("a join to an unselected fact never reaches the Writer",
          "JOINS YOU MAY ASSERT" not in pr)

    # ── the joins are evidence, so they are not leak-scanned as generated prose ──
    scanned = [f for f, _ in ST.generated_packet_text(packet)]
    check("relation text is not scanned as generated prose",
          not any(f.startswith("relations") for f in scanned),
          "it is frozen propositions; only the `kind` word is model-chosen, from a "
          "closed vocabulary")

    print("-" * 62)
    if FAILED:
        print("FAILED: %d" % len(FAILED))
        for f in FAILED:
            print("   - " + f)
        return 1
    print("all ledger-relation checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
