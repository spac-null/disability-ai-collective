#!/usr/bin/env python3
"""Which held runs are held only by a gloss the engine itself asked for.

ZERO MODEL CALLS. Reads retained artifacts.

THE CHAIN, MEASURED 2026-09-29

  Nothing has published since 4 September. Zero ACCEPTs in the last 60 production runs,
  so publication is not blocked at the publisher -- nothing reaches it.

  Of 71 runs with a grounding record:
      19  no blocking finding at all
      20  held ONLY by TRUE_UNCERTAIN          <- this file is about these
      32  carry at least one TRUE_UNSUPPORTED

  TRUE_UNSUPPORTED always blocks. TRUE_UNCERTAIN blocks unless adjudicated, and
  composition.ground_candidate already has ONE adjudication hatch: a definitional gloss,
  allowed when the flagged sentence names a term the ARCHITECTURE declared in
  `definitions` and adds no factual surface the packet does not carry.

  Of the 20, twelve have a readable packet, and ALL TWELVE pass that second test: every
  uncertain finding in them adds no unapproved number and no unapproved entity.

  AND THAT IS NOT ENOUGH, WHICH THE OUTPUT ITSELF SHOWS. Passing the surface test is not
  the same as being a gloss. Among the twelve:

      "an articulation route: an arrangement by which students entering from a partner
       college can secure a place on a named university degree"          <- a gloss
      "the sedges growing from the mud of the Pactolus -- the river in
       the story -- whispered out his infamy"                            <- a gloss
      "The dial the veto is mapped onto measures the arrangement: it
       records that redistributive authority can now be overridden"      <- an inference
      "In a separate experiment with 27 German-speaking participants"    <- a detail
      "All of those figures come from survey data collected in 2022 and
       2023 -- a household survey, a count taken by reaching people"     <- methodology

  Only some are explanations of a word. The rest are interpretive, attributive or
  methodological claims that add no NEW surface because their terms are already approved,
  and those should keep blocking. So the 44% below is the size of the population, not the
  size of a safe gain.

AND THE ENGINE ASKED FOR THE GLOSS. The writer system instructs: "On first use, briefly
expand a country-specific acronym, agency, benefit, institution, legal mechanism or
cultural shorthand when its meaning is necessary to understand the story." So the Writer
is told to explain a term, does, and the run is held for explaining it. The flagged
sentences are what that instruction produces:

    "SEVP -- the Student and Exchange Visitor Program, the DHS office that runs the
     student visa system"
    "programs that estimate, from the text itself, whether a passage was produced by a
     language model"
    "the playa, the flat dry lakebed the city is built on"
    "rule weighted toward those judged more knowledgeable, rather than equal votes"

The Grounder is right every time: the sources use these terms and do not define them. It
is the only stage that cannot see the architecture, by design.

WHY THIS FILE REPORTS AND DOES NOT DECIDE

Widening the hatch from "a term the architect declared" to "anything adding no factual
surface" would unblock about a quarter of the backlog -- and it would also adjudicate
findings that are not glosses at all. "a record that predates the pavilion and may not
reflect it" adds no surface either, and it is an inference about evidence rather than an
explanation of a word. A rule that cannot tell those apart is not ready to be a gate, and
a rule calibrated on the sample that produced it has been falsified in this project
before.

So this names the population and leaves the decision where it belongs. Nothing here is
imported by the engine and nothing blocks.

Run:  python3 automation/grounding_adjudicable_scan.py --root /srv/data/cripminds-new-engine-v1
"""

from __future__ import annotations

import argparse
import glob
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import story as ST                      # noqa: E402

UNSUPPORTED = "TRUE_UNSUPPORTED"
UNCERTAIN = "TRUE_UNCERTAIN"


def _payload(obj: dict) -> dict:
    """Retained artifacts are written as {stage, payload, ...} envelopes."""
    inner = obj.get("payload")
    return inner if isinstance(inner, dict) else obj


def _facts(ledger: dict) -> dict:
    return {k: v for k, v in (ledger or {}).items() if isinstance(v, dict)}


def classify_run(run: pathlib.Path) -> dict | None:
    """One run's grounding posture, or None if it has no grounding record."""
    gp = run / "GROUNDING_FINDINGS.json"
    if not gp.is_file():
        return None
    try:
        findings = _payload(json.loads(gp.read_text())).get("findings") or []
    except Exception:                                              # noqa: BLE001
        return None

    unsupported = [f for f in findings if f.get("classification") == UNSUPPORTED]
    uncertain = [f for f in findings if f.get("classification") == UNCERTAIN]
    out = {"run": run.name, "unsupported": len(unsupported),
           "uncertain": len(uncertain), "adds_surface": None, "quotes": []}
    if unsupported or not uncertain:
        return out

    pp, lp = run / "WRITER_PACKET.json", run / "LEDGER.json"
    if not pp.is_file():
        out["adds_surface"] = "unknown: no retained packet"
        return out
    try:
        packet = _payload(json.loads(pp.read_text()))
        ledger = _facts(json.loads(lp.read_text())) if lp.is_file() else {}
    except Exception:                                              # noqa: BLE001
        out["adds_surface"] = "unknown: packet unreadable"
        return out

    # THE EXISTING HATCH'S OWN SECOND TEST, applied unchanged: does the flagged sentence
    # add factual surface the approved material does not carry?
    adds = False
    for f in uncertain:
        quote = str(f.get("quote") or "")
        if not quote.strip():
            adds = True
            break
        audit = ST.factual_surface_audit(quote, packet, ledger)
        if audit.get("unapproved_numbers") or audit.get("unapproved_entities"):
            adds = True
            break
        out["quotes"].append(quote[:150])
    out["adds_surface"] = adds
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", required=True, type=pathlib.Path)
    p.add_argument("--out", type=pathlib.Path)
    args = p.parse_args()

    rows = [r for r in (classify_run(pathlib.Path(d).parent)
                        for d in sorted(glob.glob(str(args.root / "*" /
                                                      "GROUNDING_FINDINGS.json"))))
            if r]
    clean = [r for r in rows if not r["unsupported"] and not r["uncertain"]]
    unc_only = [r for r in rows if not r["unsupported"] and r["uncertain"]]
    has_uns = [r for r in rows if r["unsupported"]]
    gloss = [r for r in unc_only if r["adds_surface"] is False]
    surface = [r for r in unc_only if r["adds_surface"] is True]
    unknown = [r for r in unc_only if isinstance(r["adds_surface"], str)]

    print("runs with a grounding record          %d" % len(rows))
    print("  no blocking finding                 %d" % len(clean))
    print("  held ONLY by TRUE_UNCERTAIN         %d" % len(unc_only))
    print("      passes the surface test         %d   <- NOT the same as being a gloss"
          % len(gloss))
    print("      at least one adds surface       %d" % len(surface))
    print("      undecidable (no packet)         %d" % len(unknown))
    print("  carries a TRUE_UNSUPPORTED          %d" % len(has_uns))
    if rows:
        print()
        print("  clearing grounding today            %d of %d  (%.0f%%)"
              % (len(clean), len(rows), 100.0 * len(clean) / len(rows)))
        print("  population if all were adjudicable   %d of %d  (%.0f%%)"
              % (len(clean) + len(gloss), len(rows),
                 100.0 * (len(clean) + len(gloss)) / len(rows)))
    print()
    print("what is being held, verbatim -- read these before treating the number as a")
    print("gain; only some of them are explanations of a word:")
    for r in gloss[:8]:
        print("  %s" % r["run"])
        for q in r["quotes"][:2]:
            print("     %r" % q)
    if args.out:
        args.out.write_text(json.dumps(rows, indent=1, ensure_ascii=False))
        print("\nfull table -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
