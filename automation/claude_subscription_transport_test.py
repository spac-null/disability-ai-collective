#!/usr/bin/env python3
"""claude_subscription_transport_test.py -- Phase 2B: Claude-family work is subscription work.

WHAT THIS PROTECTS. Phase 2A proved that a transport can fail for months without changing
a single log line, because the only provenance recorded was `fallback_used`, which
describes MODEL substitution and is blind to where the bytes went. Phase 2B moves every
live Claude-family call onto the owner's claude.ai subscription. The failure this test
exists to catch is the mirror image of the CLIProxy one: a subscription call that quietly
becomes a paid OpenRouter call again, either by a handler "helpfully" falling back or by a
new call site being written against the old HTTP path.

So the assertions come in two kinds:

  BEHAVIOURAL -- a fake `claude` binary is put on the adapter's path and driven through
  success, absence, bad auth, malformed output, timeout and limit. In every failure case
  `urllib.request.urlopen` is booby-trapped to raise, so any code that answered a
  subscription failure with an HTTP call fails the test rather than passing it quietly.

  STRUCTURAL -- the live import closure is walked (the same machinery
  cliproxy_removal_test.py uses) and every Claude-family model literal in it is required
  to sit on a subscription-routed path. A grep proves today; a closure proves every day.

Stdlib only, no network, matching every other test in this directory.
"""
import ast
import json
import os
import re
import stat
import sys
import tempfile
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claude_cli_provider as ccp
from orchestrator import transport

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    if cond:
        print("  PASS  %s" % label)
    else:
        print("  FAIL  %s%s" % (label, (" -- " + detail) if detail else ""))
        FAILURES.append(label)


AUTOMATION = os.path.dirname(os.path.abspath(__file__))

GOOD_AUTH = {
    "loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty",
    "email": "jascha@altrospazio.org", "orgName": "Altro Spazio",
    "subscriptionType": "team",
}

# A fake `claude` binary. `MODE` selects which real-world outcome it reproduces; each one
# was observed on the host rather than invented, which is why the shapes are odd -- notably
# that the CLI exits 0 on a refusal it reports inside the JSON payload.
FAKE = r'''#!/usr/bin/env python3
import json, os, sys, time
mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
auth = json.loads(os.environ.get("FAKE_CLAUDE_AUTH", "{}"))
if "auth" in sys.argv and "status" in sys.argv:
    if mode == "auth_unreadable":
        sys.stdout.write("not json at all"); sys.exit(1)
    sys.stdout.write(json.dumps(auth)); sys.exit(0)
model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "?"
sys.stdin.read()
if mode == "hang":
    time.sleep(30); sys.exit(0)
if mode == "not_json":
    sys.stdout.write("I am afraid that is not JSON"); sys.exit(0)
if mode == "limit":
    # Exit 0, error in the payload -- the real CLI's shape for an exhausted plan.
    sys.stdout.write(json.dumps({"is_error": True, "subtype": "error_during_execution",
                                 "result": "You've reached your usage limit. Resets at 4pm.",
                                 "session_id": "s"})); sys.exit(0)
if mode == "empty":
    sys.stdout.write(json.dumps({"is_error": False, "subtype": "success", "result": "  ",
                                 "session_id": "s"})); sys.exit(0)
if mode == "malformed_json_payload":
    body = "here you go: ```json\n{\"verdict\": \"ok\", \"n\": 2}\n``` hope that helps"
else:
    body = os.environ.get("FAKE_CLAUDE_RESULT", "SUBSCRIPTION-OK")
sys.stdout.write(json.dumps({
    "is_error": False, "subtype": "success", "result": body,
    "session_id": "s", "total_cost_usd": 0.0009, "duration_ms": 1200,
    "usage": {"input_tokens": 10, "output_tokens": 4},
    "modelUsage": {model: {"inputTokens": 10}}}))
'''


def fake_binary(tmpdir):
    path = os.path.join(tmpdir, "claude")
    with open(path, "w") as fh:
        fh.write(FAKE)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


class NoHTTP:
    """Booby-trap urlopen. Any OpenRouter fallback becomes a loud failure, not a pass."""

    def __init__(self):
        self.attempts = []

    def __enter__(self):
        import urllib.request
        self._real = urllib.request.urlopen

        def boom(req, *a, **kw):
            url = getattr(req, "full_url", req)
            self.attempts.append(str(url))
            raise AssertionError("HTTP call attempted during a subscription failure: %s" % url)

        urllib.request.urlopen = boom
        return self

    def __exit__(self, *exc):
        import urllib.request
        urllib.request.urlopen = self._real
        return False


def run_mode(binary, mode, auth=None, timeout=30, model="anthropic/claude-sonnet-4.6"):
    ccp.reset_providers()
    os.environ["FAKE_CLAUDE_MODE"] = mode
    os.environ["FAKE_CLAUDE_AUTH"] = json.dumps(auth if auth is not None else GOOD_AUTH)
    return ccp.complete_via_subscription("sys", "user", model,
                                         timeout=timeout, binary=binary)


TMP = tempfile.mkdtemp(prefix="phase2b-")
BIN = fake_binary(TMP)


# ---------------------------------------------------------------------------
print("test_model_policy_is_explicit_never_a_guess")
check("Claude-family recognised in every prefix shape this repo carries",
      all(ccp.is_claude_family(m) for m in (
          "anthropic/claude-opus-4.8", "openrouter/claude-fable-5", "claude-sonnet-5",
          "anthropic/claude-haiku-4.5")))
check("non-Claude models are not Claude-family",
      not any(ccp.is_claude_family(m) for m in (
          "perplexity/sonar", "recraft/recraft-v4.1", "qwen3.5:9b",
          "google/gemini-2.5-pro", "")))
check("Opus-class preserves tier onto the proven subscription Opus",
      ccp.subscription_model_for("anthropic/claude-opus-4.8") == "claude-opus-5")
check("Sonnet-class preserves tier",
      ccp.subscription_model_for("anthropic/claude-sonnet-4.6") == "claude-sonnet-5")
check("Fable preserves tier",
      ccp.subscription_model_for("anthropic/claude-fable-5") == "claude-fable-5")
check("Haiku preserves tier",
      ccp.subscription_model_for("anthropic/claude-haiku-4.5")
      == "claude-haiku-4-5-20251001")
check("a subscription id maps to itself, so routing is idempotent",
      ccp.subscription_model_for("claude-opus-5") == "claude-opus-5")
try:
    ccp.subscription_model_for("anthropic/claude-quartz-9")
    _guessed = True
except ccp.ClaudeCLIError:
    _guessed = False
check("an unknown Claude tier RAISES instead of guessing a substitute", not _guessed,
      "a silent guess is exactly the 'claim it is the same model' failure section 6 bans")


# ---------------------------------------------------------------------------
print("\ntest_A_subscription_success")
c = run_mode(BIN, "ok")
check("a completion comes back", c.text == "SUBSCRIPTION-OK", c.text)
check("provider label names the subscription",
      c.provider_label == "claude-cli-subscription", c.provider_label)
rec = ccp.provenance(c.requested_model, c.actual_model, ok=True)
check("transport is CLAUDE_SUBSCRIPTION", rec["transport"] == transport.CLAUDE_SUBSCRIPTION)
check("credential_source names the auth method, never a secret",
      rec["credential_source"] == "claude.ai subscription OAuth")
check("requested_model is what the CALLER asked for",
      c.requested_model == "anthropic/claude-sonnet-4.6", c.requested_model)
check("actual_model is what the CLI reports it ran",
      c.actual_model == "claude-sonnet-5", c.actual_model)
check("the tier substitution is visible as MODEL fallback, not hidden",
      rec["fallback_used"] is True)
check("identity() reports subscription auth and no OpenRouter use",
      c.identity()["auth"] == "claude.ai subscription OAuth"
      and c.identity()["openrouter_used"] is False)
check("no secret value appears anywhere in the record",
      not any("sk-" in str(v) for v in rec.values()))
check("provenance shape matches orchestrator.transport.record exactly",
      sorted(rec) == sorted(transport.record("https://openrouter.ai/api/v1")),
      "the two must not drift: llm.py greps one format")

print("\ntest_override_vars_are_scrubbed_from_the_child_environment")
os.environ["ANTHROPIC_API_KEY"] = "should-not-survive"
os.environ["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:8317"
try:
    env = ccp.scrubbed_env()
    check("ANTHROPIC_API_KEY never reaches the child", "ANTHROPIC_API_KEY" not in env)
    check("ANTHROPIC_BASE_URL never reaches the child", "ANTHROPIC_BASE_URL" not in env)
    check("ANTHROPIC_AUTH_TOKEN is scrubbed too",
          "ANTHROPIC_AUTH_TOKEN" in ccp.OVERRIDE_VARS)
    check("the defence survives a clean openclaw.env",
          len(ccp.OVERRIDE_VARS) == 3,
          "Phase 2A emptied the file; the guard is kept for the next one")
finally:
    os.environ.pop("ANTHROPIC_API_KEY", None)
    os.environ.pop("ANTHROPIC_BASE_URL", None)


# ---------------------------------------------------------------------------
print("\ntest_B_claude_cli_unavailable_fails_explicitly_and_buys_nothing")
with NoHTTP() as http:
    try:
        run_mode(os.path.join(TMP, "no-such-claude-binary"), "ok")
        outcome = "returned"
    except ccp.ClaudeCLIError as e:
        outcome = getattr(e, "code", "?")
    except AssertionError as e:
        outcome = "HTTP: %s" % e
check("a missing CLI raises an explicit subscription error",
      outcome.startswith("CLAUDE_SUBSCRIPTION"), str(outcome))
check("no OpenRouter call was attempted", not http.attempts, str(http.attempts))


# ---------------------------------------------------------------------------
print("\ntest_C_auth_unavailable_or_invalid_fails_explicitly_and_buys_nothing")
cases = [
    ("logged out", dict(GOOD_AUTH, loggedIn=False)),
    ("a Console API key overriding the login",
     dict(GOOD_AUTH, apiKeySource="ANTHROPIC_API_KEY")),
    ("a non-firstParty provider", dict(GOOD_AUTH, apiProvider="bedrock")),
    ("no subscriptionType", dict(GOOD_AUTH, subscriptionType=None)),
]
for label, auth in cases:
    with NoHTTP() as http:
        try:
            run_mode(BIN, "ok", auth=auth)
            code = "returned"
        except ccp.SubscriptionAuthFailure as e:
            code = e.code
        except ccp.ClaudeCLIError as e:
            code = getattr(e, "code", "?")
        except AssertionError as e:
            code = "HTTP: %s" % e
    check("%s -> CLAUDE_SUBSCRIPTION_AUTH_FAILURE" % label,
          code == ccp.CLAUDE_SUBSCRIPTION_AUTH_FAILURE, str(code))
    check("%s -> no OpenRouter call" % label, not http.attempts, str(http.attempts))
with NoHTTP() as http:
    try:
        run_mode(BIN, "auth_unreadable")
        code = "returned"
    except ccp.ClaudeCLIError as e:
        code = getattr(e, "code", "?")
check("an unreadable auth status is an auth failure, not a silent success",
      code == ccp.CLAUDE_SUBSCRIPTION_AUTH_FAILURE, str(code))


# ---------------------------------------------------------------------------
print("\ntest_D_malformed_structured_output_is_bounded_mechanical_handling_only")
c = run_mode(BIN, "malformed_json_payload")
from new_engine_v1.provider import parse_json_object, ProviderError
obj = parse_json_object(c.text)
check("a fenced JSON object inside prose is recovered mechanically",
      obj == {"verdict": "ok", "n": 2}, str(obj))
try:
    parse_json_object("no object here at all")
    raised = False
except ProviderError:
    raised = True
check("unrecoverable output raises rather than yielding a partial payload", raised)
with NoHTTP() as http:
    try:
        run_mode(BIN, "not_json")
        code = "returned"
    except ccp.ClaudeCLIError as e:
        code = getattr(e, "code", "?")
check("a non-JSON CLI reply is CLAUDE_SUBSCRIPTION_OUTPUT_ERROR",
      code == ccp.CLAUDE_SUBSCRIPTION_OUTPUT_ERROR, str(code))
check("no regeneration loop was entered and nothing was bought",
      not http.attempts, str(http.attempts))
with NoHTTP():
    try:
        run_mode(BIN, "empty")
        code = "returned"
    except ccp.ClaudeCLIError as e:
        code = getattr(e, "code", "?")
check("an empty result is an output error, never an empty article",
      code == ccp.CLAUDE_SUBSCRIPTION_OUTPUT_ERROR, str(code))


# ---------------------------------------------------------------------------
print("\ntest_E_timeout_and_limit_fail_explicitly_with_no_openrouter_fallback")
with NoHTTP() as http:
    try:
        run_mode(BIN, "hang", timeout=2)
        code = "returned"
    except ccp.ClaudeCLIError as e:
        code = getattr(e, "code", "?")
check("a hung CLI is CLAUDE_SUBSCRIPTION_TIMEOUT",
      code == ccp.CLAUDE_SUBSCRIPTION_TIMEOUT, str(code))
check("a timeout does not fall back to OpenRouter", not http.attempts, str(http.attempts))
with NoHTTP() as http:
    try:
        run_mode(BIN, "limit")
        code = "returned"
    except ccp.SubscriptionLimit as e:
        code = e.code
    except ccp.ClaudeCLIError as e:
        code = getattr(e, "code", "?")
check("an exhausted plan is CLAUDE_SUBSCRIPTION_LIMIT",
      code == ccp.CLAUDE_SUBSCRIPTION_LIMIT, str(code))
check("exhaustion does not start spending OpenRouter money",
      not http.attempts, str(http.attempts))
check("a limit reported with exit code 0 is still caught",
      code == ccp.CLAUDE_SUBSCRIPTION_LIMIT,
      "the CLI exits 0 on a refusal it reports in JSON")
check("the no-paid-fallback policy is declared, not merely implied",
      ccp.NO_PAID_CLAUDE_FALLBACK is True)

print("\ntest_temperature_is_rejected_not_silently_dropped")
try:
    ccp.complete_via_subscription("s", "u", "anthropic/claude-opus-4.8",
                                  temperature=0.0, binary=BIN)
    rejected = False
except ccp.ClaudeCLIError:
    rejected = True
check("a pinned temperature raises rather than becoming an uncontrolled comparison",
      rejected, "phase_probe's before/after validity rests on the pin being real")


# ---------------------------------------------------------------------------
print("\ntest_F_and_G_non_claude_transports_are_untouched")
check("Sonar stays OPENROUTER_DIRECT",
      transport.classify("https://openrouter.ai/api/v1") == transport.OPENROUTER_DIRECT)
check("perplexity/sonar is not Claude-family, so the boundary never routes it",
      not ccp.is_claude_family("perplexity/sonar"))
check("recraft is not Claude-family, so images keep their OpenRouter route",
      not ccp.is_claude_family("recraft/recraft-v4.1"))
fact_src = open(os.path.join(AUTOMATION, "orchestrator", "fact_check.py")).read()
check("the authoritative fact check still names perplexity/sonar",
      'model="perplexity/sonar"' in fact_src)
img_src = open(os.path.join(AUTOMATION, "orchestrator", "images.py")).read()
check("image generation still reads OPENROUTER_API_KEY", "OPENROUTER_API_KEY" in img_src)
check("image generation still names the Recraft model", "recraft/recraft-v4.1" in img_src)
check("the local Qwen gateway is not swept into the subscription",
      transport.classify("http://vision-gateway:8080/v1") != transport.OPENROUTER_DIRECT)
check("the Nous endpoint is not OpenRouter, so the OpenRouter rule leaves it alone",
      transport.classify("https://inference-api.nousresearch.com/v1")
      != transport.OPENROUTER_DIRECT)
check("CLIProxy remains classifiable so it can never return unnoticed",
      transport.classify("http://127.0.0.1:8317/v1") == transport.CLIPROXY)


# ---------------------------------------------------------------------------
# STRUCTURAL: the live import closure may hold no Claude-family OpenRouter caller.
# Same machinery as cliproxy_removal_test.py -- import edges, not a flat grep, because
# the repo keeps frozen probe harnesses that must go on naming what they measured.
LIVE_ENTRYPOINTS = [
    "news_fetcher", "production_orchestrator", "bsky_outreach_auto", "publish_best",
    "engagement_fetch", "link_pool_crawler", "backup_state_dbs", "selector_v2_shadow_test",
]


def _module_map():
    mods = {}
    for dirpath, dirnames, filenames in os.walk(AUTOMATION):
        dirnames[:] = [d for d in dirnames
                       if d not in ("__pycache__", "probe_out", ".probe_fixtures")]
        for fn in filenames:
            if fn.endswith(".py"):
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, AUTOMATION)[:-3].replace(os.sep, ".")
                mods[rel] = path
    return mods


def _imports(path):
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError):
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def live_modules():
    mods = _module_map()
    seen, queue = set(), deque()
    for entry in LIVE_ENTRYPOINTS:
        if entry in mods:
            seen.add(entry)
            queue.append(entry)
    while queue:
        for dep in _imports(mods[queue.popleft()]):
            for candidate in (dep, dep.split(".")[0]):
                if candidate in mods and candidate not in seen:
                    seen.add(candidate)
                    queue.append(candidate)
    return {n: mods[n] for n in seen}


print("\ntest_zero_live_claude_family_openrouter_callers")
LIVE = live_modules()
check("the live closure resolved", len(LIVE) > 10, str(len(LIVE)))
check("the shared adapter is reachable from the live entry points",
      "claude_cli_provider" in LIVE, sorted(LIVE)[:5])

# WHAT ACTUALLY REACHES OPENROUTER is a `/chat/completions` POST. Naming a Claude model
# does not: almost every orchestrator module names one and hands it to the shared boundary,
# which is the whole point of routing centrally. And `urlopen` alone does not either --
# news_fetcher reads RSS with it, bsky_outreach_auto talks to Bluesky with it, social.py
# uses it a dozen times for posting. So the ban is on the request BUILDERS, and there must
# be exactly three of them, each accounted for.
CLAUDE_LITERAL = re.compile(r"""["'](?:anthropic|openrouter)/claude[-.][\w.\-]*["']""")
builders = []
for name, path in sorted(LIVE.items()):
    src = open(path, encoding="utf-8").read()
    code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
    if "chat/completions" in code:
        builders.append(name)
check("exactly the three known modules build an OpenRouter request",
      sorted(builders) == ["gen_images", "new_engine_v1.provider", "orchestrator.llm"],
      ", ".join(sorted(builders)))

# gen_images is the third builder and must stay non-Claude: Recraft has no Claude
# equivalent in this architecture, so images keep OpenRouter and are not proved by
# spending a generation.
img_gen = open(os.path.join(AUTOMATION, "gen_images.py"), encoding="utf-8").read()
img_code = "\n".join(ln for ln in img_gen.splitlines() if not ln.lstrip().startswith("#"))
check("the image builder names no Claude model", not CLAUDE_LITERAL.search(img_code))
check("the image builder is Recraft over OpenRouter", "recraft" in img_gen.lower())

# research.py: Sonar only. If a Claude literal ever appears here it would be a Claude call
# over HTTP with nothing routing it away.
res_src = open(os.path.join(AUTOMATION, "new_engine_v1", "research.py")).read()
res_code = "\n".join(ln for ln in res_src.splitlines() if not ln.lstrip().startswith("#"))
check("the research/search builder names no Claude model at all",
      not CLAUDE_LITERAL.search(res_code))
check("the research/search builder is Sonar, and stays OPENROUTER_DIRECT",
      'SEARCH_MODEL = "perplexity/sonar"' in res_src)

# The other two builders DO name Claude models -- they are the split points. What makes
# them safe is ORDER: the Claude-family branch must return before the request is built.
# Asserting the branch merely exists would pass even if it sat below the POST.
for label, path, guard in (
    ("orchestrator.llm", os.path.join(AUTOMATION, "orchestrator", "llm.py"),
     "claude_cli_provider.is_claude_family(wire_model)"),
    ("new_engine_v1.provider", os.path.join(AUTOMATION, "new_engine_v1", "provider.py"),
     "claude_cli_provider.is_claude_family(self.model)"),
):
    src = open(path, encoding="utf-8").read()
    # Measured against the POST-ISSUING CALL, not the string "chat/completions" -- in
    # provider.py the URL lives in a module-level _post() helper defined ABOVE the method
    # that routes, so a plain file-offset comparison reads the order backwards.
    poster = "_post(url, key, payload" if "new_engine" in label else "urlopen(req"
    check("%s: Claude-family is routed away BEFORE the request is issued" % label,
          guard in src and poster in src and src.index(guard) < src.index(poster),
          "guard at %s, POST at %s" % (src.find(guard), src.find(poster)))

llm_src = open(os.path.join(AUTOMATION, "orchestrator", "llm.py")).read()
check("the shared boundary routes Claude-family away from OpenRouter",
      "claude_cli_provider.is_claude_family(wire_model)" in llm_src
      and "_call_claude_subscription" in llm_src)
check("the boundary tests the endpoint too, so non-OpenRouter rungs are left alone",
      "transport.classify(url) == transport.OPENROUTER_DIRECT" in llm_src)
check("no ladder answers a subscription refusal with a paid Claude rung",
      "no paid Claude fallback is permitted" in llm_src)
nf_src = open(os.path.join(AUTOMATION, "news_fetcher.py")).read()
check("news_fetcher no longer holds an OpenRouter chat endpoint",
      "chat/completions" not in nf_src)
check("news_fetcher calls the shared adapter",
      "claude_cli_provider.complete_via_subscription" in nf_src)
prov_src = open(os.path.join(AUTOMATION, "new_engine_v1", "provider.py")).read()
check("new_engine_v1 routes Claude-family to the subscription",
      "claude_cli_provider.is_claude_family(self.model)" in prov_src)
check("new_engine_v1 turns a subscription refusal into a ProviderError, not a retry",
      "raise ProviderError(\"%s: %s\" % (getattr(e, \"code\"" in prov_src)
bo_src = open(os.path.join(AUTOMATION, "bsky_outreach_auto.py")).read()
check("the weekly outreach cron no longer posts to OpenRouter",
      "chat/completions" not in bo_src)

print("\ntest_new_engine_v1_purity_boundary_is_intact")
pkg = os.path.join(AUTOMATION, "new_engine_v1")
for fn in sorted(os.listdir(pkg)):
    if not fn.endswith(".py"):
        continue
    tree = ast.parse(open(os.path.join(pkg, fn), encoding="utf-8").read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    banned = imported & {"subprocess", "sqlite3", "requests", "socket", "orchestrator",
                         "production_orchestrator", "news_fetcher"}
    check("new_engine_v1/%s imports nothing banned" % fn, not banned, str(sorted(banned)))
check("claude_cli_provider is the ONE permitted transport import, and it is lazy",
      "import claude_cli_provider" in prov_src
      and "        import claude_cli_provider" in prov_src,
      "a module-level import would put a shelling-out dependency in the import graph")


print("\n" + "-" * 60)
if FAILURES:
    print("PHASE 2B TRANSPORT: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d PHASE 2B TRANSPORT TESTS PASSED" % CHECKS[0])
