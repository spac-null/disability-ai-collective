"""
transport.py -- say where a provider call actually went.

WHY THIS EXISTS. The only provenance the pipeline recorded was

    fallback_used = actual_model != requested_model

which describes MODEL SUBSTITUTION and says nothing about TRANSPORT. It cannot tell a
CLIProxy call from a direct OpenRouter call from a Claude subscription call, and that
blindness is exactly why a guaranteed-failing CLIProxy attempt ran unnoticed on every
editorial call for weeks: the model name was the same either way, so nothing in the logs
changed when the proxy stopped working.

Measured on the host, 2026-09-04:

    sonnet-4-6                    CLIProxy -> 401, OAuth access token expired
    haiku-4-5                     CLIProxy -> 401, expired
    anthropic/claude-opus-4.8     CLIProxy -> 500, unknown provider
    openrouter/claude-sonnet-4.6  CLIProxy -> 200, but only as OpenRouter passthrough

So a model name beginning "anthropic/" proved nothing about where the bytes went, and a
model name beginning "openrouter/" proved only that a proxy was translating it.

TRANSPORT IS DERIVED FROM THE URL, NEVER FROM THE MODEL. That is the whole point: the
model string is what we ASKED for and the URL is where we WENT.

No secret ever enters a record here -- `credential_source` names the environment variable
a call read, not its value.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

# Transport classes. What kind of pipe the bytes went down.
CLAUDE_SUBSCRIPTION = "CLAUDE_SUBSCRIPTION"   # host-wide claude CLI on the claude.ai plan
OPENROUTER_DIRECT = "OPENROUTER_DIRECT"       # openrouter.ai over the public internet
CLIPROXY = "CLIPROXY"                          # the local CLIProxyAPI, on :8317
DIRECT_PROVIDER = "DIRECT_PROVIDER"            # some other first-party provider endpoint
UNKNOWN_TRANSPORT = "UNKNOWN_TRANSPORT"

CLIPROXY_PORT = 8317


def classify(url: str) -> str:
    """Which transport a URL represents. Structural, not a guess about intent."""
    if not url:
        return UNKNOWN_TRANSPORT
    p = urlparse(url if "//" in url else "//" + url)
    host = (p.hostname or "").lower()
    port = p.port
    # CLIProxy is identified by its port wherever it is reached -- loopback from the host,
    # or the Docker bridge address from inside a container. Both are the same process.
    if port == CLIPROXY_PORT:
        return CLIPROXY
    if host.endswith("openrouter.ai"):
        return OPENROUTER_DIRECT
    if host.endswith("anthropic.com") or host.endswith("perplexity.ai") \
            or host.endswith("api.recraft.ai") or host:
        return DIRECT_PROVIDER
    return UNKNOWN_TRANSPORT


def record(url: str, requested_model: str = "", actual_model: str = "",
           credential_env: str = "", provider: str = "",
           ok: bool | None = None, detail: str = "") -> dict:
    """One structured provenance record. Safe to log verbatim.

    `credential_env` is the NAME of the variable a call read, never its value, and the
    record notes only whether that variable was populated.
    """
    transport = classify(url)
    p = urlparse(url if "//" in (url or "") else "//" + (url or ""))
    return {
        "transport": transport,
        "provider": provider or (p.hostname or "") or "unknown",
        "endpoint_host": p.hostname or "",
        "credential_source": credential_env or "",
        "credential_present": bool(os.environ.get(credential_env)) if credential_env
                              else None,
        "requested_model": requested_model or "",
        "actual_model": actual_model or "",
        # Kept for MODEL substitution only. Transport has its own field now and must not
        # be inferred from this one.
        "fallback_used": bool(actual_model and requested_model
                              and actual_model != requested_model),
        "ok": ok,
        "detail": detail[:200] if detail else "",
    }


def line(rec: dict) -> str:
    """A greppable one-liner for the run log."""
    return ("PROVENANCE transport=%s provider=%s credential=%s requested_model=%s "
            "actual_model=%s fallback_used=%s ok=%s"
            % (rec.get("transport"), rec.get("provider"), rec.get("credential_source"),
               rec.get("requested_model"), rec.get("actual_model"),
               rec.get("fallback_used"), rec.get("ok")))


def uses_cliproxy(url: str) -> bool:
    return classify(url) == CLIPROXY
