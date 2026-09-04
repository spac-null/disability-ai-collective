"""
claude_cli_provider.py -- the ONE Claude-subscription transport for Cripminds.

WHY THIS EXISTS. Claude-family work used to reach Claude over HTTP through OpenRouter,
paying per token for generation the owner's claude.ai subscription already covers. That
arrangement also failed in a way that had nothing to do with the engine: the OpenRouter
balance ran out mid-run, at $268.12 of $269, and an architecture stage died on a 402.

Phase 2A (PR #64) removed the CLIProxyAPI hop and added transport.py, which says where a
call actually WENT rather than which model name it asked for. Phase 2B uses that visibility
to move every live Claude-family call off OpenRouter and onto the subscription. OpenRouter
keeps exactly two jobs: the authoritative Perplexity/Sonar fact check and Recraft images,
neither of which is a Claude model and neither of which a Claude subscription can serve.

This module is the single transport all of them share. Story Architecture proved the shape
(PR #63); it is ported here so the orchestrator, news_fetcher, new_engine_v1 and the
Bluesky outreach writer all call the same implementation instead of six subprocess
re-inventions.

WHY IT IS HERE AND NOT IN new_engine_v1/. `test_package_purity_static` bans `subprocess`
inside that package. A provider that shells out cannot live there, so it lives at
automation/ level and is imported lazily at the one call boundary that needs it.

THE THREE VARIABLES THAT MUST NOT BE INHERITED
  ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN are honoured by Claude
  Code OVER the claude.ai login. Measured on the host:

      with them set   {"authMethod":"claude.ai","apiKeySource":"ANTHROPIC_API_KEY",
                       "email":null,"orgName":null,"subscriptionType":null}
                      + "connectors are disabled because ANTHROPIC_API_KEY ... takes
                         precedence over your claude.ai login"
      scrubbed        {"authMethod":"claude.ai","apiProvider":"firstParty",
                       "email":"...","orgName":"Altro Spazio","subscriptionType":"team"}

  Phase 2A removed CLIProxy's values from /srv/secrets/openclaw.env, so nothing sets them
  today. The scrubbing STAYS anyway. openclaw.env is sourced wholesale with `set -a` by
  several crons, config.py copies every key it contains into os.environ, and the defence
  costs one dict comprehension. A clean file today is not a guarantee about tomorrow's,
  and the failure it prevents is silent: a key does not break the call, it just bills a
  Console account instead of the subscription and reports authMethod claude.ai either way.

SUBSCRIPTION LIMITS AND OTHER FAILURES ARE TERMINAL. Exhaustion is a first-class outcome,
not a retry and not a reason to start spending OpenRouter money. Every failure here raises
a typed error carrying an explicit `code`; no caller may answer one by re-issuing the same
Claude-family request to a paid HTTP provider. See NO_PAID_CLAUDE_FALLBACK below.
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
CLAUDE_SUBSCRIPTION_AUTH_FAILURE = "CLAUDE_SUBSCRIPTION_AUTH_FAILURE"
CLAUDE_SUBSCRIPTION_TIMEOUT = "CLAUDE_SUBSCRIPTION_TIMEOUT"
CLAUDE_SUBSCRIPTION_OUTPUT_ERROR = "CLAUDE_SUBSCRIPTION_OUTPUT_ERROR"

# The transport label this module reports. Matches orchestrator.transport.CLAUDE_SUBSCRIPTION
# but is duplicated deliberately: new_engine_v1 may not import `orchestrator`, and a shared
# transport that drags a banned package in behind it is not shared, it is contagious.
CLAUDE_SUBSCRIPTION = "CLAUDE_SUBSCRIPTION"

# Owner policy, Phase 2B. A Claude-family request that the subscription cannot serve is an
# explicit failure. It is never answered by re-issuing the same request to a paid HTTP
# provider -- not OpenRouter, not Nous, not a first-party Anthropic API key. A future paid
# fallback may be added only by an explicit policy change, never as an error handler.
NO_PAID_CLAUDE_FALLBACK = True


# ---------------------------------------------------------------------------
# MODEL POLICY. Explicit, never a silent rename.
#
# The subscription does not serve the OpenRouter-era model ids. `anthropic/claude-opus-4.8`
# has no subscription equivalent; `claude-opus-5` is the current proven subscription
# Opus-class model, the one Story Architecture already runs on. That is a deliberate
# TIER-PRESERVING SUBSTITUTION and it is recorded as one: requested_model keeps the id the
# caller asked for, actual_model carries what the CLI reports it actually ran, and the two
# are never collapsed. `fallback_used` continues to mean MODEL substitution only -- it says
# nothing about transport, which has had its own field since Phase 2A.
#
# Verified live on trident 2026-09-05, each id returning is_error=false through
# `claude -p --model <id> --output-format json`.
# ---------------------------------------------------------------------------

# Tier keyword -> the subscription model id that preserves that tier.
SUBSCRIPTION_TIER_MODELS = {
    "opus":   "claude-opus-5",
    "sonnet": "claude-sonnet-5",
    "fable":  "claude-fable-5",
    "haiku":  "claude-haiku-4-5-20251001",
}

# A Claude-family model id in any of the shapes this codebase carries:
#   anthropic/claude-opus-4.8   openrouter/claude-fable-5   claude-sonnet-5
_CLAUDE_FAMILY = re.compile(r"(?:^|/)claude[-.]", re.IGNORECASE)
_TIER = re.compile(r"claude[-.](opus|sonnet|fable|haiku)", re.IGNORECASE)


def is_claude_family(model) -> bool:
    """Whether a model id names a Claude model, in any prefix shape."""
    return bool(model) and isinstance(model, str) and bool(_CLAUDE_FAMILY.search(model))


def subscription_model_for(model: str) -> str:
    """The subscription model id that preserves `model`'s tier.

    Raises on a Claude-family id whose tier is unrecognised rather than guessing. A wrong
    guess here is the exact failure mode section 6 forbids: a silent claim that some other
    model is the one that was asked for.
    """
    if not is_claude_family(model):
        raise ValueError("not a Claude-family model: %r" % (model,))
    # Already a subscription id (no vendor prefix, and a known subscription value).
    if model in SUBSCRIPTION_TIER_MODELS.values():
        return model
    m = _TIER.search(model)
    if not m:
        raise ClaudeCLIError(
            "no subscription tier is known for Claude-family model %r; add it to "
            "SUBSCRIPTION_TIER_MODELS deliberately rather than letting a call guess" % model)
    return SUBSCRIPTION_TIER_MODELS[m.group(1).lower()]



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
    """Transport or response-shape failure. Never swallowed into a fake completion.

    Every subclass carries an explicit `code` so a caller can log WHY the subscription
    could not serve a call without parsing an error string. None of them is a licence to
    re-issue the request to a paid HTTP provider -- see NO_PAID_CLAUDE_FALLBACK.
    """
    code = "CLAUDE_SUBSCRIPTION_ERROR"


class SubscriptionLimit(ClaudeCLIError):
    """The subscription cannot serve this call. Stop; do not retry, do not fall back."""
    code = CLAUDE_SUBSCRIPTION_LIMIT


class SubscriptionAuthFailure(ClaudeCLIError):
    """The CLI is not logged in, or a key is overriding the subscription login."""
    code = CLAUDE_SUBSCRIPTION_AUTH_FAILURE


class SubscriptionTimeout(ClaudeCLIError):
    """The CLI did not finish inside the caller's budget."""
    code = CLAUDE_SUBSCRIPTION_TIMEOUT


class SubscriptionOutputError(ClaudeCLIError):
    """The CLI ran but produced nothing usable: no JSON, no result, or an empty result."""
    code = CLAUDE_SUBSCRIPTION_OUTPUT_ERROR


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
    try:
        p = subprocess.run([exe, "auth", "status"], capture_output=True, text=True,
                           env=scrubbed_env(), timeout=60, cwd="/tmp")
    except FileNotFoundError:
        # A missing binary must be a TYPED subscription failure, not a bare OSError. The
        # ladders in orchestrator/llm.py distinguish ClaudeCLIError (stop, buy nothing)
        # from a generic Exception (try the next rung) -- so an unwrapped FileNotFoundError
        # would read as an ordinary provider hiccup and fall straight through to the paid
        # Nous rung. Caught by claude_subscription_transport_test's case B.
        raise SubscriptionAuthFailure("claude CLI not found at %r" % exe)
    except subprocess.TimeoutExpired:
        raise SubscriptionAuthFailure("claude CLI auth status timed out")
    except OSError as exc:
        raise SubscriptionAuthFailure("could not run the claude CLI at %r: %s" % (exe, exc))
    try:
        return json.loads(p.stdout)
    except Exception:                                             # noqa: BLE001
        raise SubscriptionAuthFailure("could not read auth status: %s"
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
        raise SubscriptionAuthFailure("claude CLI is not logged in")
    if st.get("apiProvider") != "firstParty":
        raise SubscriptionAuthFailure("apiProvider is %r, not firstParty -- this is not "
                                      "the subscription path" % st.get("apiProvider"))
    if st.get("authMethod") != "claude.ai":
        raise SubscriptionAuthFailure("authMethod is %r, not claude.ai"
                                      % st.get("authMethod"))
    if st.get("apiKeySource"):
        raise SubscriptionAuthFailure(
            "an API key from %r is overriding the subscription login; the composition "
            "environment must not carry %s"
            % (st["apiKeySource"], ", ".join(OVERRIDE_VARS)))
    if not st.get("subscriptionType"):
        raise SubscriptionAuthFailure("no subscriptionType reported; the login is not "
                                      "resolving to a subscription")
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
            raise SubscriptionTimeout("claude CLI timed out after %ss"
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
            raise SubscriptionOutputError("claude CLI did not return JSON: %s" % raw[:300])

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
            raise SubscriptionOutputError("claude CLI returned an empty result")

        used = list((d.get("modelUsage") or {}).keys())
        actual = next((m for m in used if "haiku" not in m), model)
        self.calls += 1
        self.cost_usd += float(d.get("total_cost_usd") or 0.0)
        return Completion(
            text=result, requested_model=model, actual_model=actual,
            usage=d.get("usage") or {}, cost_usd=d.get("total_cost_usd"),
            duration_ms=d.get("duration_ms") or int((time.monotonic() - t0) * 1000),
            session_id=d.get("session_id") or "")


# ---------------------------------------------------------------------------
# THE SHARED ENTRY POINT.
#
# Every live Cripminds Claude-family call goes through this one function, so there is
# exactly one place where the subscription is reached, one place that decides the tier
# substitution, and one place that emits provenance. Section 3 of the Phase 2B brief:
# "all live Claude-family callers eventually call the same transport implementation."
# ---------------------------------------------------------------------------

_PROVIDERS: dict = {}


def get_provider(subscription_model: str, binary: str = "claude",
                 timeout: int = DEFAULT_TIMEOUT):
    """One verified provider per subscription model, reused for the process's lifetime.

    `assert_subscription` shells out, so verifying on every call would add a subprocess
    round trip to each stage of a pipeline that makes dozens. It is verified once per
    model per process instead: the auth state cannot change mid-run in a way a re-check
    would catch earlier than the call itself failing.
    """
    key = (subscription_model, binary)
    if key not in _PROVIDERS:
        _PROVIDERS[key] = ClaudeCLIProvider(model=subscription_model, binary=binary,
                                            timeout=timeout)
    return _PROVIDERS[key]


def reset_providers() -> None:
    """Drop the cache. For tests, which swap binaries and environments between cases."""
    _PROVIDERS.clear()


def complete_via_subscription(system: str, user: str, requested_model: str,
                              timeout: int = DEFAULT_TIMEOUT, binary: str = "claude",
                              temperature: float | None = None):
    """Serve one Claude-family request on the subscription.

    `requested_model` is the id the CALLER asked for, in whatever prefix shape that call
    site carries. The tier-preserving subscription id is derived from it here, and the
    returned Completion keeps both apart.

    `temperature` is REJECTED rather than ignored. The CLI cannot pin it, and only
    phase_probe.py ever sets it -- for controlled before/after comparisons whose entire
    validity rests on the temperature actually being pinned. Silently dropping it would
    turn a probe result into a number that looks controlled and is not. A loud failure in
    a dev harness beats invalid evidence.
    """
    if temperature is not None:
        raise ClaudeCLIError(
            "the Claude subscription CLI cannot pin temperature=%r; this call would be an "
            "uncontrolled comparison. Run it against a provider that accepts temperature, "
            "or drop the pin deliberately." % (temperature,))
    model = subscription_model_for(requested_model)
    provider = get_provider(model, binary=binary, timeout=timeout)
    completion = provider.complete(system, user, timeout=timeout)
    # requested_model on the Completion is the SUBSCRIPTION id the CLI was given. The
    # caller's original id is what the substitution is measured against, so restore it
    # here: `fallback_used` in the provenance record then means "a different model
    # answered than the one asked for", which after a tier substitution is true and
    # should be visible.
    completion.requested_model = requested_model
    return completion


def provenance(requested_model: str, actual_model: str, ok: bool,
               detail: str = "") -> dict:
    """A provenance record in the same shape orchestrator.transport.record() produces.

    Duplicated rather than imported for the reason given in the module docstring:
    new_engine_v1 may not import `orchestrator`. The two shapes are asserted equal by
    claude_subscription_transport_test.py so they cannot drift apart unnoticed.
    """
    return {
        "transport": CLAUDE_SUBSCRIPTION,
        "provider": "claude-cli-subscription",
        "endpoint_host": "",
        "credential_source": "claude.ai subscription OAuth",
        "credential_present": True,
        "requested_model": requested_model or "",
        "actual_model": actual_model or "",
        "fallback_used": bool(actual_model and requested_model
                              and actual_model != requested_model),
        "ok": ok,
        "detail": detail[:200] if detail else "",
    }


def provenance_line(rec: dict) -> str:
    """The same greppable one-liner orchestrator.transport.line() emits."""
    return ("PROVENANCE transport=%s provider=%s credential=%s requested_model=%s "
            "actual_model=%s fallback_used=%s ok=%s"
            % (rec.get("transport"), rec.get("provider"), rec.get("credential_source"),
               rec.get("requested_model"), rec.get("actual_model"),
               rec.get("fallback_used"), rec.get("ok")))
