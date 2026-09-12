#!/usr/bin/env python3
"""Targeted regressions for RELATIVE_DATE_RESOLUTION, built from the real ASL
White House article's oscillating 'by Friday' / 'by the following Friday' hold. No
provider, no network."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import fast_lane_v1 as FL                                 # noqa: E402

FAILURES = []


def check(label, ok, detail=""):
    print(("PASS" if ok else "FAIL") + "  " + label + ("" if ok else " <- %r" % detail))
    if not ok:
        FAILURES.append(label)


# A. Known source date + "last Friday" resolves to one exact ISO date.
r = FL.resolve_relative_date("last Friday", "2025-11-05")
check("A: 'last Friday' from a known 2025-11-05 (Wednesday) publication resolves "
      "to the exact preceding Friday",
      r["resolution_status"] == "EXACT" and r["resolved_absolute_date"] == "2025-10-31",
      r)

# B. Source date unknown -> UNRESOLVED.
r = FL.resolve_relative_date("last Friday", None)
check("B: no source context date -- UNRESOLVED, no invented date",
      r["resolution_status"] == "UNRESOLVED" and r["resolved_absolute_date"] is None,
      r)

# C. A vague relative phrase outside the narrow resolvable set stays UNRESOLVED even
# with a known context date -- it may not become a precise date.
r = FL.resolve_relative_date("earlier that week", "2025-11-05")
check("C: a vague relative phrase ('earlier that week') stays UNRESOLVED even with "
      "a known context date -- never guessed into a precise date",
      r["resolution_status"] == "UNRESOLVED" and r["resolved_absolute_date"] is None,
      r)

# D. The exact resolved date, once computed, is exactly what a packet/fact_status
# entry would carry forward -- same dict shape, same value, no drift.
ann = {"claim_status": FL.ESTABLISHED, "attribution_to": None}
resolution = FL.resolve_relative_date("last Friday", "2025-11-05")
ann.update(resolution)
check("D: the resolved date survives into a fact_status-shaped annotation "
      "unchanged", ann["resolved_absolute_date"] == "2025-10-31"
      and ann["resolution_status"] == "EXACT", ann)

if FAILURES:
    raise SystemExit("FAILED: " + ", ".join(FAILURES))
print("\nALL PASS")
