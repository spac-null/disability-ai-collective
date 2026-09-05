#!/usr/bin/env python3
"""selector_errors_encoding_test.py -- the errors field must be encoded exactly once.

WHAT HAPPENED. seed_material_assessments.errors is written as JSON text and read back as
JSON text, and the record is rebuilt from EITHER a fresh assessment (a real list) OR a
cached row (already-encoded text). json.dumps() was called on both, so every selector run
that re-read a cached row added another layer of escaping and roughly doubled the string.

Measured live on 2026-09-05, the lengths in that column were exact powers of two:

    512  1024  4096  8192  65536  33554432  67108864  134217728  536870912

and the content was nothing but escaped quotes and backslashes. The next doubling crossed
SQLite's SQLITE_MAX_LENGTH, and every production run then died at the SELECTOR stage with
"DataError: string or blob too big" -- which stops everything, because no candidate can be
chosen and nothing downstream runs. The database had reached 881 MB.

It grew from `[]`. An empty error list is still a string once encoded, so healthy rows
doubled exactly as fast as broken ones. The idempotence test below is the whole fix.

Stdlib only, no network.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import selector_v2 as SV

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


print("test_a_fresh_assessment_encodes_its_list_once")
check("an empty list becomes []", SV._errors_json([]) == "[]", SV._errors_json([]))
check("None becomes []", SV._errors_json(None) == "[]")
one = SV._errors_json(["ValueError: bad reply"])
check("a real error list round-trips", json.loads(one) == ["ValueError: bad reply"], one)


print("\ntest_re_encoding_a_cached_value_is_IDEMPOTENT")
# This is the exact loop that blew up: write, read back, rebuild the record, write again.
v = SV._errors_json([])
lengths = [len(v)]
for _ in range(40):
    v = SV._errors_json(v)          # as if read from the DB and re-recorded
    lengths.append(len(v))
check("forty round trips do not grow the value", len(set(lengths)) == 1,
      "lengths seen: %s" % sorted(set(lengths)))
check("the value is still []", v == "[]", v)

v = SV._errors_json(["ASSESSMENT_ERROR: timeout"])
first, lengths = v, []
for _ in range(40):
    v = SV._errors_json(v)
    lengths.append(len(v))
check("a non-empty list is stable across forty round trips", set(lengths) == {len(first)},
      "lengths seen: %s" % sorted(set(lengths)))
check("and still decodes to the original list",
      json.loads(v) == ["ASSESSMENT_ERROR: timeout"], v[:120])


print("\ntest_the_real_corrupted_shapes_are_recovered_not_re_wrapped")
# Rebuild the production corruption by hand: N layers of encoding over [].
poisoned = "[]"
for _ in range(12):
    poisoned = json.dumps(poisoned)
check("the reconstruction really is huge and escape-only", len(poisoned) > 4000,
      str(len(poisoned)))
fixed = SV._errors_json(poisoned)
check("twelve layers of escaping collapse back to []", fixed == "[]", fixed[:80])
check("the result is not larger than the input", len(fixed) < len(poisoned))

poisoned = json.dumps(json.dumps(json.dumps(["real: a message"])))
check("layered real errors are recovered",
      json.loads(SV._errors_json(poisoned)) == ["real: a message"],
      SV._errors_json(poisoned)[:120])


print("\ntest_it_never_throws_and_never_grows_without_bound")
check("undecodable text is captured, not re-wrapped forever",
      json.loads(SV._errors_json("not json at all")) == ["not json at all"])
check("an over-long undecodable string is truncated",
      len(json.loads(SV._errors_json("x" * 5000))[0]) <= 500)
check("a non-list decoded value is wrapped once",
      json.loads(SV._errors_json(json.dumps({"a": 1}))) == [{"a": 1}])
# 20 layers, not 200: each layer roughly doubles, so this is already ~1 MB and 200 would
# be 2**200 characters. Building that is how the production bug killed the database, and
# an earlier draft of this test OOM-killed itself proving the point.
deep = "[]"
for _ in range(20):
    deep = json.dumps(deep)
check("the deep reconstruction is genuinely large", len(deep) > 100_000, str(len(deep)))
out = SV._errors_json(deep)
check("a pathologically deep value terminates and stays small", len(out) < 600, str(len(out)))


print("\ntest_the_write_site_uses_it")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "selector_v2.py")).read()
check("the record builder calls the helper",
      '"errors": _errors_json(a.get("errors"))' in src)
check("the old double-encoding call is gone",
      '"errors": json.dumps(a.get("errors") or [])' not in src)


print("\n" + "-" * 60)
if FAILURES:
    print("SELECTOR ERRORS ENCODING: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d SELECTOR ERRORS ENCODING TESTS PASSED" % CHECKS[0])
