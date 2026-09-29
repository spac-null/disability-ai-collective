#!/usr/bin/env python3
"""Find Ledger facts whose cited span points at something the Ledger never establishes.

ZERO MODEL CALLS. Pure text over retained LEDGER.json files.

THE SIGNATURE, TAKEN FROM A CONFIRMED CASE.

production-20260928T070709Z-9b443d22 published an article whose subject was missing. Its
F48 read:

    proposition   "Roeske said Prinzhorn reproduced one of Emma Hauck's SHEETS in
                   Prinzhorn's book, but upside down, ... merely as an example of
                   scribbling with a first tendency to order."
    support_span  "Prinzhorn bildet eines DIESER BLAETTER in seinem Buch ab, ..."

The span opens on a demonstrative -- "one of THESE sheets" -- whose antecedent is the
preceding source sentence, which says the sheets are Emma Hauck's letters, covered with
one plea repeated until the surface greys. That sentence was never extracted. Nothing was
cut (CUT_REPORT: 0 hits) and nothing failed. The Ledger kept the fact ABOUT the thing and
dropped the fact SAYING WHAT THE THING IS, and every downstream gate passed, because they
all ask whether the prose is carried by the Ledger and none asks whether the Ledger covers
the source.

Re-freezing the same pack under the same code recovered it, so this is an omission, not an
incapacity.

TWO SIGNALS, BOTH DETERMINISTIC.

THE SIGNAL IS STRUCTURAL, NOT LEXICAL, AND THE FIRST VERSION OF THIS SCRIPT WAS WRONG.

It matched the demonstrative's head noun against the other propositions. That cannot work:
support spans are the source's own German, propositions are English, so the F48 span says
"Blaetter" while the fact that would establish it says "letters". Validated against the
one case with a known answer, it correctly flagged F48 in the retained ledger AND
incorrectly flagged F58 in the refrozen one, where F57 does supply the antecedent. It also
took "Dieser sollte" and "Diese werden" for noun phrases.

So the question is asked of the SOURCE instead, where it is language-independent and
exact:

    a span opens on a demonstrative
    -> locate that span in the source it cites
    -> is ANY other fact's span drawn from the sentences immediately before it?
    -> if not, the thing the demonstrative points at was never extracted

That is precisely the F48 shape: "Prinzhorn bildet eines dieser Blaetter..." is retained,
and the sentence in front of it -- the one saying the sheets are Hauck's letters -- is in
the source, cited by nothing.

WHAT A HIT IS AND IS NOT. This finds a fact whose own citation depends on material the
ledger does not carry. It does not prove the article was damaged -- an unused fact costs
nothing. So hits are reported separately for facts the ARCHITECTURE actually selected,
which is where the cost is real.

Run:  python3 automation/ledger_anaphora_scan.py --root /srv/data/cripminds-new-engine-v1
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# Demonstratives that point BACKWARD, in the two languages the corpus actually contains.
# Bare articles are excluded: German "das"/"die" are usually definite articles, and the
# false-positive cost of including them is total.
# ONE IMPLEMENTATION. The detector lives in the engine as `new_engine_v1.anaphora`, where
# the Ledger stage calls it; this file is the retrospective sweep over retained runs and
# must never drift from it. A second copy here would be a second answer.
from new_engine_v1 import anaphora as AN                    # noqa: E402

scan_ledger = AN.orphaned_spans


def pack_of(run: pathlib.Path) -> dict:
    path = run / "RESEARCH_PACK.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:                                              # noqa: BLE001
        return {}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", required=True, type=pathlib.Path)
    p.add_argument("--out", type=pathlib.Path)
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    runs = sorted(d for d in args.root.iterdir()
                  if d.is_dir() and (d / "LEDGER.json").exists())
    if args.limit:
        runs = runs[-args.limit:]

    report, totals = {}, Counter()
    for run in runs:
        try:
            ledger = json.loads((run / "LEDGER.json").read_text())
        except Exception as e:                                     # noqa: BLE001
            totals["unreadable"] += 1
            continue
        if not isinstance(ledger, dict) or not ledger:
            totals["empty"] += 1
            continue
        selected = set()
        arch_path = run / "ARCHITECTURE.json"
        if arch_path.exists():
            try:
                selected = set(json.loads(arch_path.read_text()).get("use_facts") or [])
            except Exception:                                      # noqa: BLE001
                pass
        pack = pack_of(run)
        if not AN.source_texts(pack):
            totals["no_pack"] += 1
            continue
        hits = scan_ledger(ledger, pack, selected)
        totals["runs"] += 1
        totals["facts"] += len(ledger)
        if hits:
            totals["runs_with_hits"] += 1
            totals["hits"] += len(hits)
            totals["hits_selected"] += sum(1 for h in hits if h["selected"])
            report[run.name] = hits

    print("runs scanned            %d" % totals["runs"])
    print("ledger facts read       %d" % totals["facts"])
    print("runs with an orphan     %d  (%.0f%%)"
          % (totals["runs_with_hits"],
             100.0 * totals["runs_with_hits"] / max(1, totals["runs"])))
    print("orphaned facts          %d" % totals["hits"])
    print("of those, SELECTED      %d   <- these reached an article"
          % totals["hits_selected"])
    if totals["unreadable"] or totals["empty"] or totals["no_pack"]:
        print("skipped                 %d unreadable, %d empty, %d without a pack"
              % (totals["unreadable"], totals["empty"], totals["no_pack"]))
    print()
    shown = 0
    for run, hits in sorted(report.items()):
        sel = [h for h in hits if h["selected"]]
        if not sel:
            continue
        print("%s" % run)
        for h in sel:
            print("   %-5s span opens: %r" % (h["fact_id"], h["span_opens_on"]))
            print("         nothing cites the source text before it:")
            print("           ...%s" % h["uncited_before_it"][-150:].replace("\n", " "))
        shown += 1
        if shown >= 12:
            print("   ... (%d more runs with selected orphans)"
                  % (sum(1 for r, hs in report.items()
                         if any(x["selected"] for x in hs)) - shown))
            break
    if args.out:
        args.out.write_text(json.dumps(report, indent=1, ensure_ascii=False))
        print("\nfull report -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
