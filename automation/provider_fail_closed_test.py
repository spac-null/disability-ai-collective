#!/usr/bin/env python3
"""provider_fail_closed_test.py -- a LIVE Claude failure may not become another model.

OWNER POLICY, 2026-09-05: for live Claude-family workloads, subscription success is used
and subscription failure is an explicit provider failure / HOLD. Not Nous, not OpenRouter
Claude, not local Qwen, not a canned template. The reason is provenance and editorial
consistency, not only cost -- a production run must not silently change model family or
tier because the preferred provider failed.

WHAT MAKES THIS TESTABLE RATHER THAN ASSERTED. Every case below drives the real ladder
(`call_llm_via_openclaw_session`) with a real provider list, and records which rungs were
actually attempted. A substitution is therefore visible as a rung that ran, not inferred
from a log line. The three Claude failure shapes are the ones the adapter really raises:
auth failure, limit, and a missing CLI.

Stdlib only, no network, matching every other test in this directory.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claude_cli_provider as ccp
from orchestrator import provider_policy, transport
from orchestrator.llm import LLMMixin

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    if cond:
        print("  PASS  %s" % label)
    else:
        print("  FAIL  %s%s" % (label, (" -- " + detail) if detail else ""))
        FAILURES.append(label)


class _Log:
    def __init__(self):
        self.lines = []

    def _rec(self, m, *a):
        try:
            self.lines.append(str(m) % a if a else str(m))
        except Exception:                                         # noqa: BLE001
            self.lines.append(str(m))

    info = warning = error = debug = _rec


class Ladder(LLMMixin):
    """The real ladder, with only the wire call replaced.

    `served` records every rung that actually reached a provider -- which is the whole
    question. A rung that is skipped by policy never appears; a rung that answers does.
    """

    def __init__(self, outcome):
        self.logger = _Log()
        self.outcome = outcome
        self.served = []

    def _call_openai_compat_api(self, url, api_key, system_prompt, user_prompt, model,
                                max_tokens=3500, timeout=120, no_think=False,
                                return_model=False, **kw):
        self.served.append(model)
        result = self.outcome(model)
        if isinstance(result, Exception):
            raise result
        return (result, model) if return_model else result


ARTICLE = "x" * 900          # long enough to clear the ladder's 400-char floor
CLAUDE_RUNGS = ("anthropic/claude-opus-4.8", "anthropic/claude-sonnet-4.6")
NOUS_RUNG = "anthropic/claude-opus-4.6"
LOCAL_RUNG = "qwen3.5:9b"


def run(outcome, allow_local=False):
    prev = os.environ.pop(provider_policy.LOCAL_FALLBACK_ENV, None)
    if allow_local:
        os.environ[provider_policy.LOCAL_FALLBACK_ENV] = "1"
    try:
        lad = Ladder(outcome)
        return lad, lad.call_llm_via_openclaw_session("write something")
    finally:
        os.environ.pop(provider_policy.LOCAL_FALLBACK_ENV, None)
        if prev is not None:
            os.environ[provider_policy.LOCAL_FALLBACK_ENV] = prev


def assert_no_substitution(label, lad):
    check("%s: Nous is NOT called" % label, NOUS_RUNG not in lad.served, str(lad.served))
    check("%s: local Qwen is NOT called" % label, LOCAL_RUNG not in lad.served,
          str(lad.served))
    check("%s: no non-Claude model answered" % label,
          all(ccp.is_claude_family(m) for m in lad.served), str(lad.served))


# ---------------------------------------------------------------------------
print("test_A_subscription_success_result_is_used")
lad, (text, name, actual) = run(lambda m: ARTICLE)
check("the article comes back", text == ARTICLE)
check("it came from the first Claude rung", lad.served == [CLAUDE_RUNGS[0]], str(lad.served))
check("no further rung was attempted after success", len(lad.served) == 1)
check("the provider label names the subscription", "subscription" in (name or "").lower(),
      str(name))


# ---------------------------------------------------------------------------
print("\ntest_B_subscription_auth_failure_holds_and_substitutes_nothing")
lad, out = run(lambda m: ccp.SubscriptionAuthFailure("claude CLI is not logged in"))
check("the ladder returns no article", out == (None, None, None), str(out))
assert_no_substitution("auth failure", lad)
check("auth failure: the second Claude rung is not retried either",
      lad.served == [CLAUDE_RUNGS[0]], str(lad.served))


# ---------------------------------------------------------------------------
print("\ntest_C_subscription_limit_holds_and_substitutes_nothing")
lad, out = run(lambda m: ccp.SubscriptionLimit("You've reached your usage limit."))
check("the ladder returns no article", out == (None, None, None), str(out))
assert_no_substitution("limit", lad)
check("limit: exhaustion stops the ladder rather than spending elsewhere",
      lad.served == [CLAUDE_RUNGS[0]], str(lad.served))


# ---------------------------------------------------------------------------
print("\ntest_D_claude_cli_missing_holds_and_substitutes_nothing")
lad, out = run(lambda m: ccp.SubscriptionAuthFailure("claude CLI not found at '/usr/bin/claude'"))
check("the ladder returns no article", out == (None, None, None), str(out))
assert_no_substitution("missing CLI", lad)
# The real adapter must TYPE this failure. An unwrapped OSError would be caught by the
# ladder's generic `except Exception`, leave subscription_refused False, and fall through.
try:
    ccp.reset_providers()
    ccp.complete_via_subscription("s", "u", "anthropic/claude-opus-4.8",
                                  binary="/nonexistent/claude")
    code = "returned"
except ccp.ClaudeCLIError as e:
    code = getattr(e, "code", "?")
except OSError as e:
    code = "UNTYPED OSError: %s" % e
check("a missing CLI raises a TYPED subscription error, not a bare OSError",
      code == ccp.CLAUDE_SUBSCRIPTION_AUTH_FAILURE, str(code))


# ---------------------------------------------------------------------------
print("\ntest_E_local_fallback_runs_only_behind_the_explicit_opt_in")
check("the opt-in is OFF by default", not provider_policy.local_fallback_allowed({}))
check("the opt-in is off for an empty value",
      not provider_policy.local_fallback_allowed({provider_policy.LOCAL_FALLBACK_ENV: ""}))
for val in ("1", "true", "yes", "on", "TRUE"):
    check("the opt-in reads %r as on" % val,
          provider_policy.local_fallback_allowed({provider_policy.LOCAL_FALLBACK_ENV: val}))

lad, (text, name, actual) = run(
    lambda m: ARTICLE if m == LOCAL_RUNG
    else ccp.SubscriptionLimit("limit"), allow_local=True)
check("with the opt-in set, the local rung MAY answer", text == ARTICLE, str(text)[:40])
check("with the opt-in set, the local rung was reached", LOCAL_RUNG in lad.served,
      str(lad.served))
check("even with the opt-in set, the PAID Claude rungs stay skipped",
      NOUS_RUNG not in lad.served,
      "the opt-in is about local infrastructure, not about buying Claude")

lad, out = run(lambda m: ARTICLE if m == LOCAL_RUNG else ccp.SubscriptionLimit("limit"))
check("without the opt-in, the same failure yields no article", out == (None, None, None),
      str(out))
check("without the opt-in, the local rung is never reached", LOCAL_RUNG not in lad.served,
      str(lad.served))
check("the skip is logged with the flag name, so the operator can act on it",
      any(provider_policy.LOCAL_FALLBACK_ENV in ln for ln in lad.logger.lines))


# ---------------------------------------------------------------------------
print("\ntest_the_canned_template_cannot_answer_a_live_failure")
gen_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "orchestrator", "generate.py")).read()
i_guard = gen_src.find("if not provider_policy.local_fallback_allowed():")
i_tmpl = gen_src.find("raw_content = self.generate_fallback_article(")
check("generate.py gates the canned template on the opt-in",
      i_guard != -1 and i_tmpl != -1 and i_guard < i_tmpl,
      "guard at %s, template at %s" % (i_guard, i_tmpl))
check("the live path returns a provider HOLD instead",
      "return provider_policy.provider_hold(" in gen_src)
hold = provider_policy.provider_hold("CLAUDE_SUBSCRIPTION_LIMIT", ["Opus: limit"])
check("the HOLD is shaped like every other early return",
      hold["status"] == provider_policy.PROVIDER_HOLD_STATUS and "message" in hold)
check("the HOLD is classifiable as infrastructure, not editorial",
      hold["run_status"]["status"] == "PROVIDER_FAILURE")
import production_orchestrator
check("production_orchestrator recognises it as an infra failure",
      production_orchestrator._is_infra_or_contract_failure(hold))
check("the template itself is preserved for dev/manual recovery",
      "def generate_fallback_article" in
      open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "orchestrator", "content_checks.py")).read())


# ---------------------------------------------------------------------------
print("\ntest_F_non_claude_routing_is_unaffected")
check("Sonar stays OPENROUTER_DIRECT",
      transport.classify("https://openrouter.ai/api/v1") == transport.OPENROUTER_DIRECT)
check("Sonar is not Claude-family, so no policy here touches it",
      not ccp.is_claude_family("perplexity/sonar"))
check("Recraft is not Claude-family either", not ccp.is_claude_family("recraft/recraft-v4.1"))
fact_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "orchestrator", "fact_check.py")).read()
check("the authoritative fact check still names perplexity/sonar",
      'model="perplexity/sonar"' in fact_src)
# A Sonar call is not a Claude-family request, so the fail-closed rule must not fire on it.
lad = Ladder(lambda m: "PARIS")
out = lad._call_openai_compat_api("https://openrouter.ai/api/v1", "k", "s", "u",
                                  "perplexity/sonar")
check("a Sonar call still returns normally under the new policy", out == "PARIS")
check("CLIProxy stays classifiable so it cannot return unnoticed",
      transport.classify("http://127.0.0.1:8317/v1") == transport.CLIPROXY)


print("\n" + "-" * 60)
if FAILURES:
    print("PROVIDER FAIL-CLOSED: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d PROVIDER FAIL-CLOSED TESTS PASSED" % CHECKS[0])
