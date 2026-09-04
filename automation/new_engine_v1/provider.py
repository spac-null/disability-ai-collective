"""
provider.py -- the model transport for NEW_ENGINE_V1.

PRODUCTION FIDELITY, deliberately
Same transport, same auth and the same model identifiers the legacy editorial path uses.
That target has moved twice. Until 2026-09-04 both paths went through the local
CLIProxyAPI first; a live probe showed that hop returned 500 "unknown provider" for this
module's own DEFAULT_MODEL, so the rung could never succeed and every call paid for it
before falling through. Phase 2A removed it, leaving direct OpenRouter. Phase 2B
(2026-09-05) moved the CLAUDE-FAMILY half onto the owner's claude.ai subscription, which
is where the legacy path now goes too -- so fidelity is preserved by following it.

The split is by MODEL FAMILY, not by call site. A Claude-family model goes to the shared
subscription adapter; anything else keeps the direct OpenRouter POST below. That matters
because this package is also how a non-Claude model would be reached if one were ever
configured here, and a blanket cutover would have quietly turned it into a Claude call.

The OpenRouter POST is still a ~40-line stdlib implementation rather than an import from
`orchestrator.llm`, for one reason only: this package must carry NO legacy prompt surface,
and a test asserts that by scanning imports. `claude_cli_provider` is the single permitted
transport import -- it carries no prompt machinery, only a subprocess. It is imported
LAZILY inside complete(), because the package may not import `subprocess` itself and a
module-level import would put a shelling-out dependency in the package's import graph for
every consumer, including the ones that never make a call.

It sends exactly the system and user strings it is given. There is no prompt assembly
here, no persona canon, no style-rule pile, no register selector -- those live in the
legacy path and are not reachable from this module.

Every call records what actually served it. `requested_model` and `actual_model` are
kept apart on purpose: production has been silently falling back Fable -> Opus for
days, and a candidate architecture that cannot see that is not observable.

Stdlib only. No `requests`.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

import bounded_http

# Production's own value (orchestrator/config.py). Read at call time, not import
# time, so a test can point it somewhere harmless.
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# The model the migration targets for editorial reasoning and prose. Same family the
# legacy path lands on today after its Fable fallback. Kept in its OpenRouter-era spelling
# because it is what this module ASKS for; claude_cli_provider derives the tier-preserving
# subscription id (claude-opus-5) and Completion keeps requested_model and actual_model
# apart, so the substitution is recorded rather than assumed.
DEFAULT_MODEL = "anthropic/claude-opus-4.8"


class ProviderError(Exception):
    """Transport or response-shape failure. Never swallowed into a fake completion."""


@dataclass
class Completion:
    text: str
    requested_model: str
    actual_model: str
    provider_label: str
    usage: dict = field(default_factory=dict)

    def identity(self) -> dict:
        return {
            "requested_model": self.requested_model,
            "actual_model": self.actual_model,
            "provider": self.provider_label,
            "fallback_used": self.actual_model != self.requested_model,
            "usage": self.usage,
        }


def _post(url: str, key: str, payload: dict, timeout: int,
          deadline: float | None = None) -> dict:
    req = urllib.request.Request(
        url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer %s" % key},
        method="POST",
    )
    try:
        if deadline is None:
            response = urllib.request.urlopen(req, timeout=timeout)
        else:
            # urlopen's timeout bounds one socket operation, not the transfer, so a
            # trickling response is unbounded. Callers that must finish by a wall clock
            # -- the Selector V2 shadow, which runs before the real article pipeline --
            # pass a deadline and get a real one. Every read below is budgeted against
            # it, so read() cannot outlive it either. See bounded_http.
            response = bounded_http.bounded_opener(
                deadline, op_timeout=timeout, max_redirects=3).open(req, timeout=timeout)
        with response as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ProviderError("HTTP %s from %s: %s"
                            % (e.code, url, e.read()[:300].decode("utf-8", "replace")))
    except Exception as e:                                   # timeout, DNS, refused
        raise ProviderError("%s: %s" % (type(e).__name__, e))


def _extract(body: dict) -> tuple[str, str, dict]:
    choices = body.get("choices")
    if not choices:
        raise ProviderError("no choices in response: keys=%s" % sorted(body))
    msg = choices[0].get("message") or {}
    text = (msg.get("content") or "").strip()
    if not text:
        raise ProviderError("empty completion content")
    return text, body.get("model") or "", body.get("usage") or {}


class Provider:
    """Claude subscription for Claude-family models, direct OpenRouter otherwise.
    Raises rather than degrading."""

    def __init__(self, model: str = DEFAULT_MODEL, url: str | None = None):
        self.model = model
        self.url = url or os.environ.get("NEW_ENGINE_PROVIDER_URL", OPENROUTER_URL)

    def complete(self, system: str, user: str, max_tokens: int = 3000,
                 timeout: int = 180, temperature: float | None = None,
                 deadline: float | None = None) -> Completion:
        """`deadline` is an absolute time.monotonic() value, optional and off by
        default so the authoritative pipeline is untouched.

        It was introduced when this method had two rungs (CLIProxy, then OpenRouter),
        each of which got its own fresh `timeout`, so one call could cost twice what its
        argument suggested. Only the OpenRouter rung remains, but the deadline is kept:
        it is the caller's own upper bound on a complete(), independent of how many rungs
        happen to exist, and dropping it would silently loosen every caller that passes it.
        """
        # PHASE 2B. Claude-family work runs on the subscription; everything else keeps the
        # direct OpenRouter POST below. A subscription refusal is TERMINAL -- it raises a
        # ProviderError carrying the explicit subscription code, and is never answered by
        # buying the same completion from OpenRouter.
        import claude_cli_provider                                   # lazy: see docstring
        if claude_cli_provider.is_claude_family(self.model):
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProviderError("deadline reached before the attempt")
                timeout = max(1, int(min(timeout, remaining)))
            try:
                return claude_cli_provider.complete_via_subscription(
                    system, user, self.model, timeout=timeout, temperature=temperature)
            except claude_cli_provider.ClaudeCLIError as e:
                raise ProviderError("%s: %s" % (getattr(e, "code", "CLAUDE_SUBSCRIPTION_ERROR"), e))

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature

        attempts = []
        for label, url, key in (
            ("OpenRouter", self.url, os.environ.get("OPENROUTER_API_KEY", "")),
        ):
            if not url:
                continue
            try:
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        attempts.append("%s: deadline reached before the attempt" % label)
                        continue
                    leg_timeout = max(1, int(min(timeout, remaining)))
                else:
                    leg_timeout = timeout
                body = _post(url, key, payload, leg_timeout, deadline)
                text, actual, usage = _extract(body)
                return Completion(text=text, requested_model=self.model,
                                  actual_model=actual or self.model,
                                  provider_label=label, usage=usage)
            except ProviderError as e:
                attempts.append("%s: %s" % (label, e))
        raise ProviderError("all providers failed -- " + " | ".join(attempts))


def parse_json_object(text: str) -> dict:
    """Parse a model reply expected to be one JSON object.

    Tolerates a ```json fence and leading/trailing prose, because that is a formatting
    habit rather than a semantic failure -- the same lesson as the legacy eligible-flag
    contract mismatch. Anything that is not recoverably one object raises: a stage that
    cannot be parsed must fail, never silently produce a partial payload.
    """
    s = text.strip()
    if s.startswith("```"):
        s = s.split("```")[1] if "```" in s[3:] else s[3:]
        s = s.lstrip()
        if s.lower().startswith("json"):
            s = s[4:].lstrip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end <= start:
        raise ProviderError("reply contains no JSON object: %r" % text[:200])
    try:
        obj = json.loads(s[start:end + 1])
    except json.JSONDecodeError as e:
        raise ProviderError("reply is not valid JSON (%s): %r" % (e, text[:200]))
    if not isinstance(obj, dict):
        raise ProviderError("reply JSON is %s, expected object" % type(obj).__name__)
    return obj
