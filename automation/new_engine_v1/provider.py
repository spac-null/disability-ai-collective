"""
provider.py -- the model transport for NEW_ENGINE_V1.

PRODUCTION FIDELITY, deliberately
Same endpoint, same auth and the same model identifiers the legacy editorial path
uses: the local CLIProxy (`http://127.0.0.1:8317/v1`, production's own proxy in front
of OpenRouter) with a direct-OpenRouter fallback. Reimplemented here as a ~40-line
stdlib POST rather than imported from `orchestrator.llm`, for one reason only: this
package must carry NO legacy prompt surface, and a test asserts that by scanning
imports. The transport is identical; the prompt machinery is not inherited.

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

# Production's own values (orchestrator/config.py). Read at call time, not import
# time, so a test can point them somewhere harmless.
DEFAULT_CLIPROXY_URL = "http://127.0.0.1:8317/v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# The model the migration targets for editorial reasoning and prose. Same family the
# legacy path lands on today after its Fable fallback.
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
    """CLIProxy first, direct OpenRouter as fallback. Raises rather than degrading."""

    def __init__(self, model: str = DEFAULT_MODEL, cliproxy_url: str | None = None,
                 allow_fallback: bool = True):
        self.model = model
        self.cliproxy_url = cliproxy_url or os.environ.get(
            "NEW_ENGINE_CLIPROXY_URL", DEFAULT_CLIPROXY_URL)
        # The composition path is a subscription-path workload and sets this False, so a
        # Writer or Continuity call cannot silently land on OpenRouter -- which would
        # change both who wrote the article and what the run cost, invisibly. OpenRouter
        # stays where it already is: behind the authoritative external Fact Check.
        self.allow_fallback = allow_fallback

    def complete(self, system: str, user: str, max_tokens: int = 3000,
                 timeout: int = 180, temperature: float | None = None,
                 deadline: float | None = None) -> Completion:
        """`deadline` is an absolute time.monotonic() value, optional and off by
        default so the authoritative pipeline is untouched.

        It matters because of how the fallback works: CLIProxy and OpenRouter are tried
        in sequence and each would otherwise get its own fresh `timeout`, so one call
        can cost twice what its argument suggests. A deadline is SHARED by both legs --
        whatever the first spends, the second inherits what is left -- so the total for
        one complete() cannot outlive it however the legs divide the time between them.
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature

        attempts = []
        legs = [("CLIProxy", self.cliproxy_url, os.environ.get("CLIPROXY_KEY", ""))]
        if self.allow_fallback:
            legs.append(("OpenRouter", OPENROUTER_URL,
                         os.environ.get("OPENROUTER_API_KEY", "")))
        for label, url, key in legs:
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
