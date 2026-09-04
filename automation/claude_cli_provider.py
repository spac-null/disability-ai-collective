"""
claude_cli_provider.py -- Claude-family composition on the owner's Claude subscription.

WHY THIS EXISTS. Composition used to reach Claude over HTTP through OpenRouter, because
CLIProxy holds no Claude auth. That worked and then stopped working for a reason that has
nothing to do with the engine: the OpenRouter balance ran out mid-run, at $268.12 of $269,
and an architecture stage died on a 402. Paying per token for generation the owner's
subscription already covers was the wrong arrangement.

So the Claude-family stages now run through the locally installed Claude Code CLI, which
authenticates with the subscription. OpenRouter keeps exactly one job: the authoritative
Perplexity/Sonar fact check, which is not a Claude model and cannot come from a Claude
subscription.

WHY IT IS HERE AND NOT IN new_engine_v1/. `test_package_purity_static` bans `subprocess`
inside that package, along with the legacy orchestrator. A provider that shells out cannot
live there. It is injected instead, the same way `research_fn` and the fact-check bridge
already are, and it duck-types the `Provider.complete` interface so nothing in the
composition path needs to know which transport served it.

WHAT IT DELIBERATELY IS NOT
  Not a proxy, not a daemon, not a queue, not a new provider framework. One subprocess per
  stage call. CLIProxy is untouched and keeps whatever other workloads already use it.

THE THREE VARIABLES THAT MUST NOT BE INHERITED
  /srv/secrets/openclaw.env carries ANTHROPIC_API_KEY (CLIProxy's own key, not an Anthropic
  one) and ANTHROPIC_BASE_URL (CLIProxy on the Docker bridge). The cripminds cron sources
  that file wholesale with `set -a`, so any child inherits both. Claude Code honours them
  over the claude.ai login -- measured on the host:

      with them set   {"authMethod":"claude.ai","apiKeySource":"ANTHROPIC_API_KEY",
                       "email":null,"orgName":null,"subscriptionType":null}
                      + "connectors are disabled because ANTHROPIC_API_KEY ... takes
                         precedence over your claude.ai login"
      scrubbed        {"authMethod":"claude.ai","apiProvider":"firstParty",
                       "email":"...","orgName":"Altro Spazio","subscriptionType":"team"}

  So the subscription is only reached if they are removed from the child environment. They
  are NOT deleted from the file: other services legitimately use them to reach CLIProxy.
  They are scoped out here, per process, which is the only place that can be done safely.

SUBSCRIPTION LIMITS. Exhaustion is a first-class outcome, not a retry and not a reason to
start spending OpenRouter money. It raises SubscriptionLimit, which the orchestration turns
into CLAUDE_SUBSCRIPTION_LIMIT and stops on.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time

# The three the pipeline's own environment would otherwise inject. See module docstring.
OVERRIDE_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN")

# Pinned to an explicit id rather than left to the CLI's own default. The default
# currently resolves to claude-opus-5[1m], the 1M-context variant, and a moving default
# is the reproducibility hazard provider.py already separates requested_model from
# actual_model to expose. Both are still recorded on every call.
DEFAULT_MODEL = "claude-opus-5"
DEFAULT_TIMEOUT = 600

CLAUDE_SUBSCRIPTION_LIMIT = "CLAUDE_SUBSCRIPTION_LIMIT"

# What exhaustion looks like in the CLI's own words. Matched against the result text and
# the error status, never against an exit code alone -- the CLI exits 0 on a refusal it
# reports in JSON, so an exit-code-only check would read a limit as a successful stage.
_LIMIT_PATTERNS = (
    r"usage limit",
    r"rate limit",
    r"limit reached",
    r"out of (?:credit|usage)",
    r"quota (?:exceeded|exhausted)",
    r"upgrade to (?:pro|max)",
    r"you'?ve (?:hit|reached) your",
    r"resets? at",
    r"insufficient .{0,20}quota",
)


class ClaudeCLIError(Exception):
    """Transport or response-shape failure. Never swallowed into a fake completion."""


class SubscriptionLimit(ClaudeCLIError):
    """The subscription cannot serve this call. Stop; do not retry, do not fall back."""


class Completion:
    """Duck-types new_engine_v1.provider.Completion."""

    def __init__(self, text: str, requested_model: str, actual_model: str,
                 usage: dict, cost_usd, duration_ms, session_id: str):
        self.text = text
        self.requested_model = requested_model
        self.actual_model = actual_model
        self.provider_label = "claude-cli-subscription"
        self.usage = usage or {}
        self.cost_usd = cost_usd
        self.duration_ms = duration_ms
        self.session_id = session_id

    def identity(self) -> dict:
        return {
            "requested_model": self.requested_model,
            "actual_model": self.actual_model,
            "provider": self.provider_label,
            "auth": "claude.ai subscription OAuth",
            "fallback_used": False,
            "openrouter_used": False,
            "usage": self.usage,
            "subscription_cost_equivalent_usd": self.cost_usd,
            "duration_ms": self.duration_ms,
            "session_id": self.session_id,
        }


def scrubbed_env(extra: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in OVERRIDE_VARS}
    if extra:
        env.update(extra)
    return env


def auth_status(binary: str = "claude") -> dict:
    """What the CLI says about its own authentication. Read, never inferred."""
    exe = shutil.which(binary) or binary
    p = subprocess.run([exe, "auth", "status"], capture_output=True, text=True,
                       env=scrubbed_env(), timeout=60, cwd="/tmp")
    try:
        return json.loads(p.stdout)
    except Exception:                                             # noqa: BLE001
        raise ClaudeCLIError("could not read auth status: %s"
                             % (p.stdout or p.stderr)[:300])


def assert_subscription(binary: str = "claude") -> dict:
    """Fail closed unless this is really a first-party subscription login.

    Checked rather than assumed, because every failure mode here is silent: an API key
    in the environment still produces successful completions, just billed to a Console
    account instead of the subscription, and reported as authMethod claude.ai either way.
    The tell is `apiKeySource`, which only appears when a key is overriding the login.
    """
    st = auth_status(binary)
    if not st.get("loggedIn"):
        raise ClaudeCLIError("claude CLI is not logged in")
    if st.get("apiProvider") != "firstParty":
        raise ClaudeCLIError("apiProvider is %r, not firstParty -- this is not the "
                             "subscription path" % st.get("apiProvider"))
    if st.get("authMethod") != "claude.ai":
        raise ClaudeCLIError("authMethod is %r, not claude.ai" % st.get("authMethod"))
    if st.get("apiKeySource"):
        raise ClaudeCLIError(
            "an API key from %r is overriding the subscription login; the composition "
            "environment must not carry %s"
            % (st["apiKeySource"], ", ".join(OVERRIDE_VARS)))
    if not st.get("subscriptionType"):
        raise ClaudeCLIError("no subscriptionType reported; the login is not resolving "
                             "to a subscription")
    return st


def _looks_like_a_limit(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in _LIMIT_PATTERNS)


class ClaudeCLIProvider:
    """One subprocess per stage call. Same `complete()` signature the engine already uses."""

    def __init__(self, model: str = DEFAULT_MODEL, binary: str = "claude",
                 timeout: int = DEFAULT_TIMEOUT, cwd: str = "/tmp",
                 verify_auth: bool = True):
        self.model = model
        self.binary = shutil.which(binary) or binary
        self.timeout = timeout
        # A neutral cwd on purpose: the CLI reads CLAUDE.md and .claude/settings.json from
        # the directory it starts in, and the composition prompts are the whole contract.
        # Running inside the repo would silently prepend the project's own instructions to
        # every stage.
        self.cwd = cwd
        self.calls = 0
        self.cost_usd = 0.0
        if verify_auth:
            self.auth = assert_subscription(self.binary)
        else:
            self.auth = {}

    def _argv(self, system: str, model: str) -> list:
        return [
            self.binary, "-p",
            "--system-prompt", system,          # REPLACES the agent preamble
            "--model", model,
            "--output-format", "json",
            "--tools",                          # no tools: this is generation, not agency
            "--strict-mcp-config",              # no MCP servers from any settings file
            "--no-session-persistence",
        ]

    def complete(self, system: str, user: str, max_tokens: int = 3000,
                 timeout: int | None = None, temperature: float | None = None,
                 deadline: float | None = None) -> Completion:
        """`max_tokens` and `temperature` are accepted for interface compatibility and
        are not forwarded: the CLI exposes neither, and silently pretending otherwise
        would be worse than saying so. Stage output length is governed by the prompts."""
        model = self.model
        t0 = time.monotonic()
        try:
            p = subprocess.run(
                self._argv(system, model), input=user, capture_output=True, text=True,
                env=scrubbed_env(), timeout=timeout or self.timeout, cwd=self.cwd)
        except subprocess.TimeoutExpired:
            raise ClaudeCLIError("claude CLI timed out after %ss"
                                 % (timeout or self.timeout))
        except FileNotFoundError:
            raise ClaudeCLIError("claude CLI not found at %r" % self.binary)

        raw = (p.stdout or "").strip()
        if p.returncode != 0 and not raw:
            err = (p.stderr or "")[:400]
            if _looks_like_a_limit(err):
                raise SubscriptionLimit(err)
            raise ClaudeCLIError("claude CLI exited %s: %s" % (p.returncode, err))
        try:
            d = json.loads(raw)
        except Exception:                                         # noqa: BLE001
            raise ClaudeCLIError("claude CLI did not return JSON: %s" % raw[:300])

        result = d.get("result") or ""
        # The CLI exits 0 on a refusal it reports inside the JSON, so the error state
        # lives in the payload and not in the exit code.
        if d.get("is_error") or d.get("subtype") not in (None, "success"):
            blob = "%s %s" % (result, d.get("api_error_status") or "")
            if _looks_like_a_limit(blob):
                raise SubscriptionLimit(blob[:400])
            raise ClaudeCLIError("claude CLI reported %s: %s"
                                 % (d.get("subtype"), blob[:300]))
        if _looks_like_a_limit(result) and len(result) < 400:
            # A short reply that reads as a limit notice rather than stage output.
            raise SubscriptionLimit(result[:400])
        if not result.strip():
            raise ClaudeCLIError("claude CLI returned an empty result")

        used = list((d.get("modelUsage") or {}).keys())
        actual = next((m for m in used if "haiku" not in m), model)
        self.calls += 1
        self.cost_usd += float(d.get("total_cost_usd") or 0.0)
        return Completion(
            text=result, requested_model=model, actual_model=actual,
            usage=d.get("usage") or {}, cost_usd=d.get("total_cost_usd"),
            duration_ms=d.get("duration_ms") or int((time.monotonic() - t0) * 1000),
            session_id=d.get("session_id") or "")
