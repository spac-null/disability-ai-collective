#!/usr/bin/env python3
"""pr63_integration_transport_test.py -- Story Architecture inherits the provider policy.

PR #63 was written before Phase 2A and 2B. It carried its own copy of the Claude CLI
provider, its own CLIProxy preflight, and a Provider signature that no longer exists. The
risk at integration is not that composition breaks loudly -- it is that it keeps working
while quietly reaching a provider the current policy forbids.

So this asserts the integration properties specifically, on top of #63's own suites:
one provider stack, subscription transport, no Claude fallback of any kind, Sonar and
Recraft untouched, and no CLIProxy anywhere in the composition path.

Stdlib only, no network.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claude_cli_provider as ccp
from orchestrator import provider_policy, transport
from new_engine_v1 import composition as CP

FAILURES = []
CHECKS = [0]
HERE = os.path.dirname(os.path.abspath(__file__))


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else (" -- " + detail)) if detail else ""))
    if not cond:
        FAILURES.append(label)


def src(*parts):
    return open(os.path.join(HERE, *parts), encoding="utf-8").read()


print("test_one_provider_stack_not_two")
stacks = []
for dirpath, dirnames, filenames in os.walk(HERE):
    dirnames[:] = [d for d in dirnames
                   if d not in ("__pycache__", "probe_out", ".probe_fixtures")]
    for fn in filenames:
        if fn.endswith(".py") and not fn.endswith("_test.py"):
            if "class ClaudeCLIProvider" in open(os.path.join(dirpath, fn),
                                                 encoding="utf-8").read():
                stacks.append(os.path.relpath(os.path.join(dirpath, fn), HERE))
check("exactly one Claude CLI provider implementation exists",
      stacks == ["claude_cli_provider.py"], str(stacks))
check("new_engine_production imports the shared one",
      "import claude_cli_provider" in src("new_engine_production.py"))
check("composition duck-types it rather than importing a second copy",
      "class ClaudeCLIProvider" not in src("new_engine_v1", "composition.py"))

print("\ntest_story_architecture_runs_on_the_subscription")
check("production constructs the shared subscription provider",
      "CCP.ClaudeCLIProvider()" in src("new_engine_production.py"))
check("its default model is a subscription id, not an OpenRouter one",
      ccp.DEFAULT_MODEL == "claude-opus-5", ccp.DEFAULT_MODEL)
check("that id needs no tier substitution",
      ccp.subscription_model_for(ccp.DEFAULT_MODEL) == ccp.DEFAULT_MODEL)
check("the provider reports the subscription transport",
      ccp.CLAUDE_SUBSCRIPTION == transport.CLAUDE_SUBSCRIPTION)

print("\ntest_no_claude_fallback_of_any_kind_in_composition")
comp = src("new_engine_v1", "composition.py")
check("a subscription limit is a HOLD, not a retry",
      "CLAUDE_SUBSCRIPTION_LIMIT" in comp and "CompositionHold" in comp)
check("composition names no OpenRouter Claude model",
      "anthropic/claude" not in "\n".join(
          ln for ln in comp.splitlines() if not ln.lstrip().startswith("#")))
check("composition names no Nous endpoint", "nousresearch" not in comp)
check("composition names no local Qwen rung", "qwen" not in comp.lower())
check("the no-paid-fallback policy is in force", ccp.NO_PAID_CLAUDE_FALLBACK is True)
check("the live fail-closed policy is off by default",
      not provider_policy.local_fallback_allowed({}))

print("\ntest_composition_path_holds_no_cliproxy")
for rel in ("new_engine_v1/composition.py", "composition_factual_bridge.py",
            "new_engine_production.py", "story_architecture_canary.py",
            "new_engine_v1/runner.py"):
    code = "\n".join(ln for ln in src(*rel.split("/")).splitlines()
                     if not ln.lstrip().startswith("#"))
    check("%s names no CLIProxy port or key" % rel,
          "8317" not in code and "CLIPROXY" not in code)

print("\ntest_the_removed_provider_parameter_is_gone_everywhere")
for rel in ("new_engine_v1/composition.py", "new_engine_v1/provider.py",
            "new_engine_v1/runner.py"):
    check("%s does not use the removed cliproxy_url parameter" % rel,
          "cliproxy_url" not in src(*rel.split("/")))
# It must also actually construct: the override path was live code, not just a test.
from new_engine_v1.provider import Provider
os.environ[CP.COMPOSITION_MODEL_ENV] = "claude-sonnet-5"
try:
    over = CP.composition_provider(Provider(model="claude-opus-5", url="http://x/v1"))
    check("COMPOSITION_MODEL override constructs a real Provider",
          over.model == "claude-sonnet-5" and over.url == "http://x/v1")
finally:
    del os.environ[CP.COMPOSITION_MODEL_ENV]

print("\ntest_sonar_and_recraft_are_untouched_by_the_cutover")
check("the fact-check bridge requires the OpenRouter key for Sonar",
      "OPENROUTER_API_KEY" in src("composition_factual_bridge.py"))
check("the bridge reads the subscription rather than assuming it",
      "assert_subscription" in src("composition_factual_bridge.py"))
check("Sonar stays OPENROUTER_DIRECT",
      transport.classify("https://openrouter.ai/api/v1") == transport.OPENROUTER_DIRECT)
check("Sonar is not Claude-family", not ccp.is_claude_family("perplexity/sonar"))
check("Recraft is not Claude-family", not ccp.is_claude_family("recraft/recraft-v4.1"))
check("the authoritative fact check still names Sonar",
      'model="perplexity/sonar"' in src("orchestrator", "fact_check.py"))

print("\ntest_the_dispatcher_can_reach_both_engines")
check("legacy is a valid engine", CP.COMPOSITION_LEGACY in CP.COMPOSITION_ENGINES)
check("story_architecture is a valid engine",
      CP.COMPOSITION_STORY_ARCHITECTURE in CP.COMPOSITION_ENGINES)
check("an unset environment resolves to the shipped default",
      CP.current_composition_engine({}) == CP.DEFAULT_COMPOSITION_ENGINE)
check("story_architecture resolves when asked for",
      CP.current_composition_engine({CP.COMPOSITION_ENGINE_ENV: "story_architecture"})
      == CP.COMPOSITION_STORY_ARCHITECTURE)
check("legacy resolves when asked for -- this is the rollback",
      CP.current_composition_engine({CP.COMPOSITION_ENGINE_ENV: "legacy"}) == CP.COMPOSITION_LEGACY)
try:
    CP.current_composition_engine({CP.COMPOSITION_ENGINE_ENV: "something_else"})
    rejected = False
except Exception:                                                 # noqa: BLE001
    rejected = True
check("an unknown engine name is rejected rather than silently defaulted", rejected)

print("\n" + "-" * 60)
if FAILURES:
    print("PR63 INTEGRATION: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d PR63 INTEGRATION TESTS PASSED" % CHECKS[0])
