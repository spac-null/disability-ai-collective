#!/usr/bin/env python3
"""temperature_pin_transport_test.py -- a pin the CLI cannot apply must be declared.

WHAT THIS PREVENTS, both directions.

Phase 2B made a pinned temperature a hard error, on the reasoning that silently dropping
one turns a controlled comparison into a number that only looks controlled. That is right
for an experiment and wrong for everything else, and "everything else" turned out to be
most of the live pipeline: selector_v2, grounding_v2, claims and fact_check all pin
temperature=0 to make a JSON reply stable. The result was a production failure that hid
behind a cache -- assessments recorded before the cutover kept answering, so the selector
looked healthy until the cached rows ran out, and then every fresh assessment errored at
once (measured: 45 OK rows from before, 10 ASSESSMENT_ERROR after).

So the rule is now declared at the call site and never inferred, and BOTH halves are
tested here: a determinism pin proceeds and is RECORDED as unhonoured, and an
experimental pin still fails loudly.

Stdlib only, no network.
"""
import json
import os
import stat
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claude_cli_provider as ccp

FAILURES = []
CHECKS = [0]
HERE = os.path.dirname(os.path.abspath(__file__))


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


AUTH = {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty",
        "email": "x@y", "orgName": "Altro Spazio", "subscriptionType": "team"}

FAKE = r'''#!/usr/bin/env python3
import json, os, sys
if "auth" in sys.argv and "status" in sys.argv:
    sys.stdout.write(os.environ["FAKE_AUTH"]); sys.exit(0)
model = sys.argv[sys.argv.index("--model") + 1]
sys.stdin.read()
# The CLI takes no temperature flag at all. If one is ever passed it is a bug.
if any(a.startswith("--temp") for a in sys.argv):
    sys.stdout.write(json.dumps({"is_error": True, "subtype": "error",
                                 "result": "unknown flag"})); sys.exit(0)
sys.stdout.write(json.dumps({"is_error": False, "subtype": "success",
    "result": '{"assessments": [{"id": "a1", "richness": "RICH"}]}',
    "session_id": "s", "usage": {}, "modelUsage": {model: {}}}))
'''

TMP = tempfile.mkdtemp(prefix="temppin-")
BIN = os.path.join(TMP, "claude")
open(BIN, "w").write(FAKE)
os.chmod(BIN, os.stat(BIN).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
os.environ["FAKE_AUTH"] = json.dumps(AUTH)


def call(**kw):
    ccp.reset_providers()
    return ccp.complete_via_subscription("sys", "user", "anthropic/claude-opus-4.8",
                                         binary=BIN, **kw)


print("test_an_experimental_pin_still_fails_loudly")
try:
    call(temperature=0.9)
    raised = False
except ccp.ClaudeCLIError as e:
    raised = True
    msg = str(e)
check("a pinned temperature raises by DEFAULT", raised)
check("the error says how to declare a determinism pin instead",
      raised and "temperature_required=False" in msg, locals().get("msg", "")[:120])
try:
    call(temperature=0.9, temperature_required=True)
    raised2 = False
except ccp.ClaudeCLIError:
    raised2 = True
check("an explicitly required pin raises", raised2)
check("phase_probe reaches Claude through the strict default",
      "temperature_required=True" in open(os.path.join(HERE, "orchestrator", "llm.py")).read(),
      "the shared boundary must default to strict")

print("\ntest_a_determinism_pin_proceeds_and_is_recorded")
c = call(temperature=0, temperature_required=False)
check("the call succeeds", c.text.startswith("{"), c.text[:40])
check("the requested pin is recorded", c.temperature_requested == 0)
check("it is recorded as NOT honoured", c.temperature_honoured is False)
check("identity() reports both, so nothing is silent",
      c.identity()["temperature_requested"] == 0
      and c.identity()["temperature_honoured"] is False)
check("no temperature flag was passed to the CLI", "unknown flag" not in c.text)

c2 = call(temperature_required=False)
check("with no pin at all, honoured is None rather than False",
      c2.temperature_requested is None and c2.temperature_honoured is None,
      "absence and refusal must not look the same")

print("\ntest_every_live_pin_site_declares_itself")
# The pins that broke production. Each must now reach a seam that declares tolerance.
prov = open(os.path.join(HERE, "new_engine_v1", "provider.py")).read()
check("the new_engine_v1 seam declares tolerance for its callers",
      "temperature_required=False" in prov)
check("...and it is the subscription branch that declares it",
      prov.index("temperature_required=False") > prov.index("is_claude_family(self.model)"))
fc = open(os.path.join(HERE, "orchestrator", "fact_check.py")).read()
check("fact_check's claim extraction declares tolerance",
      "temperature_required=False" in fc)
for mod, path in (("selector_v2", ("selector_v2.py",)),
                  ("grounding_v2", ("new_engine_v1", "grounding_v2.py")),
                  ("claims", ("new_engine_v1", "claims.py"))):
    src = open(os.path.join(HERE, *path)).read()
    check("%s pins temperature and goes through the declaring seam" % mod,
          "temperature=0" in src and "provider.complete(" in src,
          "if this module ever built its own request it would bypass the declaration")

print("\ntest_the_strict_default_is_not_quietly_global")
import inspect
sig = inspect.signature(ccp.complete_via_subscription)
check("the parameter exists and defaults to strict",
      sig.parameters["temperature_required"].default is True)

print("\n" + "-" * 60)
if FAILURES:
    print("TEMPERATURE PIN: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d TEMPERATURE PIN TESTS PASSED" % CHECKS[0])
