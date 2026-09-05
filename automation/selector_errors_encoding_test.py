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
# The guard coerces every item to a BOUNDED string on purpose: an error list holds error
# text, and letting arbitrary structures through is how an unbounded value gets in.
check("a non-list decoded value is wrapped once, as bounded text",
      json.loads(SV._errors_json(json.dumps({"a": 1}))) == ['{"a": 1}'],
      SV._errors_json(json.dumps({"a": 1})))
# 20 layers, not 200: each layer roughly doubles, so this is already ~1 MB and 200 would
# be 2**200 characters. Building that is how the production bug killed the database, and
# an earlier draft of this test OOM-killed itself proving the point.
deep = "[]"
for _ in range(20):
    deep = json.dumps(deep)
check("the deep reconstruction is genuinely large", len(deep) > 100_000, str(len(deep)))
out = SV._errors_json(deep)
check("a pathologically deep value terminates and stays small", len(out) < 600, str(len(out)))


print("\ntest_D_an_oversized_errors_value_fails_explicitly_BEFORE_sqlite")
try:
    SV._errors_json(["x" * 900] * 200)
    raised = None
except SV.SelectorCacheError as e:
    raised = str(e)
check("an error list far over the bound raises SelectorCacheError", raised is not None)
check("the error names the size and the bound",
      raised and "bytes" in raised and str(SV.MAX_ERRORS_JSON_BYTES) in raised,
      (raised or "")[:160])
check("the bound is generous for real error lists",
      len(SV._errors_json(["ValueError: bad reply from provider"] * 20)) < SV.MAX_ERRORS_JSON_BYTES)
check("a doubling loop trips the bound early, not at half a gigabyte",
      SV.MAX_ERRORS_JSON_BYTES < 100_000, str(SV.MAX_ERRORS_JSON_BYTES))
check("individual items are truncated rather than stored whole",
      len(json.loads(SV._errors_json(["y" * 9000]))[0]) <= 1000)


print("\ntest_F_the_driver_cannot_attribute_a_stale_run_to_a_failed_attempt")
import campaign_driver as CD
import tempfile, pathlib as _pl
tmp = _pl.Path(tempfile.mkdtemp(prefix="drv-"))
# Attempt A: a real run that produced a directory and a Grounding HOLD.
runA = "production-20260905T010101Z-aaaa1111"
(tmp / runA).mkdir()
(tmp / runA / "COMPOSITION_RESULT.json").write_text(json.dumps({
    "subject": "Candidate A", "failure_stage": "GROUNDING", "reason_code": "GROUNDING_HOLD",
    "failure_reason": "1 blocking finding after one factual repair",
    "stages": {"GROUNDING": "HOLD", "WORTH": "PASS"}}))
stdout_A = ('noise\n{"status": "hold", "engine_run": "%s", '
            '"reason_code": "GROUNDING_HOLD"}\n' % runA)
oA = CD.outcome(stdout_A, str(tmp))
check("attempt A is attributed to its own run", oA["run"] == runA and oA["attributed"])
check("attempt A reports its Grounding HOLD", oA["stage"] == "GROUNDING")

# Attempt B: selector died before any run directory existed. THE REGRESSION.
stdout_B = ('CURRENT_ENGINE PROVIDER_FAILURE at stage SELECTOR\n'
            '{"status": "hold", "reason_code": "SELECTOR_FAILURE", '
            '"run_status": {"status": "PROVIDER_FAILURE", "stage": "SELECTOR", '
            '"detail": "DataError: string or blob too big"}}\n')
oB = CD.outcome(stdout_B, str(tmp))
check("attempt B is NOT attributed to any run", oB["attributed"] is False)
check("attempt B has no run id", oB["run"] is None)
check("attempt B has no run directory", oB["run_dir"] is None)
check("attempt B reports SELECTOR, not GROUNDING", oB["stage"] == "SELECTOR", oB["stage"])
check("attempt B reports the real reason", oB["reason_code"] == "SELECTOR_FAILURE",
      oB["reason_code"])
check("attempt B surfaces the underlying error",
      "string or blob too big" in oB["detail"], oB["detail"][:120])
check("attempt B did NOT inherit A's subject", "Candidate A" not in (oB["subject"] or ""))
check("attempt B did NOT inherit A's finding",
      "blocking finding" not in (oB["detail"] or ""))
# Check the EXECUTABLE code, not the module docstring -- which quotes the old broken
# `ls -td ... | head -1` on purpose, to record what went wrong.
import ast as _ast
_drv = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "campaign_driver.py")).read()
_tree = _ast.parse(_drv)
# RAW docstring constants, not ast.get_docstring() -- that returns a CLEANED, dedented
# string which never equals the raw Constant value, so filtering on it silently keeps the
# docstring in. The repo's own package-purity test records this same trap.
_docs = set()
for _n in _ast.walk(_tree):
    _body = getattr(_n, "body", None)
    if isinstance(_n, (_ast.Module, _ast.FunctionDef, _ast.ClassDef)) and _body \
            and isinstance(_body[0], _ast.Expr) \
            and isinstance(_body[0].value, _ast.Constant) \
            and isinstance(_body[0].value.value, str):
        _docs.add(_body[0].value.value)
_code_strings = [n.value for n in _ast.walk(_tree)
                 if isinstance(n, _ast.Constant) and isinstance(n.value, str)
                 and n.value not in _docs]
check("no executable string reaches for the newest directory",
      not any("ls -td" in v or "head -1" in v for v in _code_strings),
      str([v[:60] for v in _code_strings if "ls -td" in v or "head -1" in v]))
check("the driver selects the evidence dir by the run id it was given",
      'pathlib.Path(evidence_root) / run' in _drv)

# A limit stops the campaign rather than substituting a model.
oL = CD.outcome('{"status":"hold","run_status":{"stage":"RESEARCH_PACK",'
                '"error":"CLAUDE_SUBSCRIPTION_LIMIT: session limit"}}', str(tmp))
check("a subscription limit is detected as a stop condition", oL["limit"] is True)


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
