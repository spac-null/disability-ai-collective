"""
codex_cli_provider.py -- the Codex-subscription transport for the evidence-to-draft pilot.

WHY THIS EXISTS. The pilot needs a second reasoning model that is NOT Claude, for the
Experiment B/C planning role and for the second blind reviewer. The owner's brief is
explicit that it must come off the existing ChatGPT subscription through the local Codex
CLI, not through a paid API and not through OpenRouter. `claude_cli_provider` already
proved the shape for the Claude half; this is the same contract for `codex exec`.

It deliberately mirrors `claude_cli_provider`:
  * one subprocess per call, no session reuse;
  * a typed error per failure class, none of which licenses a paid fallback;
  * `requested_model` and `actual_model` kept apart and never collapsed;
  * `assert_subscription` reads the CLI's own auth state rather than inferring it.

WHAT CODEX DOES NOT EXPOSE. `codex exec --json` reports usage and a thread id but does
NOT disclose which model actually served the turn. Section 5 of the brief covers exactly
this case: record UNKNOWN rather than guess, and never ask the model to identify itself
as verification. `actual_model` is therefore RESOLVED_MODEL_UNDISCLOSED on every call,
and that string is a fact about the transport, not a placeholder to be tidied away.

ISOLATION. Every call runs with:
    --ephemeral            no session files on disk
    --ignore-user-config   ~/.codex/config.toml is not read, so the owner's interactive
                           model/effort defaults cannot leak into an experimental cell
                           and this module's explicit -m/-c settings are the only ones
    --ignore-rules         no user or project execpolicy .rules
    -s read-only           the model-run shell cannot write
    --skip-git-repo-check  the scratch cwd is not a repo, on purpose
    -C <scratch>           a per-call empty directory, so no repository material,
                           gold label or other cell's output is visible
Auth still resolves through CODEX_HOME, which is what --ignore-user-config leaves alone.

NO PAID FALLBACK. `auth.json` on this host carries auth_mode=chatgpt and a null
OPENAI_API_KEY, so there is no key for the CLI to silently bill. `assert_subscription`
re-checks that on every provider construction rather than trusting the file once.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import time

CODEX_SUBSCRIPTION = "CODEX_SUBSCRIPTION"

# Codex does not report the serving model. Recorded, never guessed. See module docstring.
RESOLVED_MODEL_UNDISCLOSED = "RESOLVED_MODEL_UNDISCLOSED"

DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_EFFORT = "medium"
DEFAULT_TIMEOUT = 900

CODEX_SUBSCRIPTION_LIMIT = "CODEX_SUBSCRIPTION_LIMIT"
CODEX_SUBSCRIPTION_AUTH_FAILURE = "CODEX_SUBSCRIPTION_AUTH_FAILURE"
CODEX_SUBSCRIPTION_TIMEOUT = "CODEX_SUBSCRIPTION_TIMEOUT"
CODEX_SUBSCRIPTION_OUTPUT_ERROR = "CODEX_SUBSCRIPTION_OUTPUT_ERROR"

# Same owner policy as the Claude half. A Codex-family request the subscription cannot
# serve is an explicit failure, never re-issued to a paid provider.
NO_PAID_CODEX_FALLBACK = True

# The variable that would redirect Codex off the ChatGPT login onto a billed key.
OVERRIDE_VARS = ("OPENAI_API_KEY", "OPENAI_BASE_URL")

_LIMIT_PATTERNS = (
    r"usage limit", r"rate limit", r"limit reached", r"quota (?:exceeded|exhausted)",
    r"out of (?:credit|usage)", r"you'?ve (?:hit|reached) your", r"resets? at",
    r"insufficient .{0,20}quota", r"upgrade to (?:plus|pro)",
)


class CodexCLIError(Exception):
    """Transport or response-shape failure. Never swallowed into a fake completion."""
    code = "CODEX_SUBSCRIPTION_ERROR"


class CodexSubscriptionLimit(CodexCLIError):
    code = CODEX_SUBSCRIPTION_LIMIT


class CodexAuthFailure(CodexCLIError):
    code = CODEX_SUBSCRIPTION_AUTH_FAILURE


class CodexTimeout(CodexCLIError):
    code = CODEX_SUBSCRIPTION_TIMEOUT


class CodexOutputError(CodexCLIError):
    code = CODEX_SUBSCRIPTION_OUTPUT_ERROR


# WHERE THE BINARY ACTUALLY IS. `codex` is installed under ~/.local/bin, which a login
# shell has on PATH and a non-interactive `ssh host command` does not. Resolving through
# `shutil.which` alone therefore worked interactively and failed under automation -- the
# exact shape of failure that only shows up once something is scheduled. Searched rather
# than assumed, and still overridable by passing an explicit binary path.
_FALLBACK_BINS = (
    os.path.expanduser("~/.local/bin/codex"),
    "/usr/local/bin/codex",
    "/usr/bin/codex",
)


def resolve_binary(binary: str = "codex") -> str:
    if os.path.sep in binary:
        return binary
    found = shutil.which(binary)
    if found:
        return found
    for cand in _FALLBACK_BINS:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return binary


def scrubbed_env(extra: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in OVERRIDE_VARS}
    if extra:
        env.update(extra)
    return env


def _codex_home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("CODEX_HOME")
                        or (pathlib.Path.home() / ".codex"))


def auth_status() -> dict:
    """What Codex's own auth store says. Read, never inferred.

    `codex login status` prints a human line, not JSON, so the structured facts come
    from auth.json -- which is the file the CLI itself authenticates from.
    """
    p = _codex_home() / "auth.json"
    if not p.exists():
        raise CodexAuthFailure("no Codex auth store at %s" % p)
    try:
        d = json.loads(p.read_text())
    except Exception as exc:                                       # noqa: BLE001
        raise CodexAuthFailure("could not read Codex auth store: %s" % exc)
    return {
        "auth_mode": d.get("auth_mode"),
        "has_api_key": bool(d.get("OPENAI_API_KEY")),
        "has_tokens": bool(d.get("tokens")),
        "last_refresh": d.get("last_refresh"),
    }


def assert_subscription(binary: str = "codex") -> dict:
    """Fail closed unless this is really the ChatGPT-subscription login.

    Checked rather than assumed for the same reason the Claude half checks: a stored API
    key still produces successful completions, just billed to an API account, and nothing
    in the transcript would say so.
    """
    # THE ENVIRONMENT IS CHECKED FIRST, BEFORE THE BINARY. A stored or inherited API key
    # is a billing error whether or not the CLI happens to be on this PATH, and checking
    # the binary first would report "codex not found" for a host that is really
    # misconfigured to bill an API account -- the quieter and more expensive of the two
    # failures. Found by the static suite, which runs where `codex` is not on PATH.
    for v in OVERRIDE_VARS:
        if os.environ.get(v):
            raise CodexAuthFailure("%s is set in the environment and would override the "
                                   "subscription login" % v)
    exe = resolve_binary(binary)
    if not (os.path.isfile(exe) and os.access(exe, os.X_OK)):
        raise CodexAuthFailure("codex CLI not found at %r" % exe)
    st = auth_status()
    if st["auth_mode"] != "chatgpt":
        raise CodexAuthFailure("auth_mode is %r, not 'chatgpt' -- this is not the "
                               "subscription path" % st["auth_mode"])
    if st["has_api_key"]:
        raise CodexAuthFailure("an OPENAI_API_KEY is stored in the Codex auth store; a "
                               "call could be billed to an API account instead of the "
                               "subscription")
    if not st["has_tokens"]:
        raise CodexAuthFailure("no OAuth tokens in the Codex auth store")
    return st


def _looks_like_a_limit(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in _LIMIT_PATTERNS)


class Completion:
    """Duck-types claude_cli_provider.Completion so callers can hold either."""

    def __init__(self, text, requested_model, actual_model, usage, duration_ms,
                 thread_id, effort):
        self.text = text
        self.requested_model = requested_model
        self.actual_model = actual_model
        self.provider_label = "codex-cli-subscription"
        self.usage = usage or {}
        self.cost_usd = None          # a subscription call has no per-call cash cost
        self.duration_ms = duration_ms
        self.session_id = thread_id
        self.effort = effort

    def identity(self) -> dict:
        return {
            "requested_model": self.requested_model,
            "actual_model": self.actual_model,
            "provider": self.provider_label,
            "transport": CODEX_SUBSCRIPTION,
            "auth": "chatgpt subscription OAuth",
            "reasoning_effort": self.effort,
            "fallback_used": False,
            "openrouter_used": False,
            "paid_api_used": False,
            "usage": self.usage,
            "cash_cost_usd": 0.0,
            "duration_ms": self.duration_ms,
            "session_id": self.session_id,
        }


class CodexCLIProvider:
    """One subprocess per call. Same `complete()` shape as ClaudeCLIProvider."""

    def __init__(self, model: str = DEFAULT_MODEL, binary: str = "codex",
                 effort: str = DEFAULT_EFFORT, timeout: int = DEFAULT_TIMEOUT,
                 verify_auth: bool = True):
        self.model = model
        self.effort = effort
        self.binary = resolve_binary(binary)
        self.timeout = timeout
        self.calls = 0
        self.auth = assert_subscription(binary) if verify_auth else {}

    def _argv(self, workdir: str, last_file: str, schema_file: str | None) -> list:
        argv = [
            self.binary, "exec",
            "--ephemeral",              # no session files
            "--ignore-user-config",     # the owner's interactive defaults stay out
            "--ignore-rules",           # no execpolicy rules
            "--skip-git-repo-check",
            "-s", "read-only",          # a model-run shell cannot write
            "-C", workdir,              # empty scratch: no repo, no labels, no siblings
            "-m", self.model,
            "-c", "model_reasoning_effort=%r" % self.effort,
            "--json",
            "-o", last_file,
        ]
        if schema_file:
            argv += ["--output-schema", schema_file]
        return argv

    def complete(self, system: str, user: str, max_tokens: int = 0,
                 timeout: int | None = None, temperature: float | None = None,
                 schema: dict | None = None) -> Completion:
        """`system` is prepended to the prompt: `codex exec` has no separate system
        channel, and silently dropping it would be worse than saying where it went.
        `max_tokens` and `temperature` are accepted for interface compatibility and are
        NOT forwarded -- the CLI exposes neither.
        """
        workdir = tempfile.mkdtemp(prefix="codex-cell-")
        last_file = os.path.join(workdir, "_last_message.txt")
        schema_file = None
        if schema:
            schema_file = os.path.join(workdir, "_schema.json")
            pathlib.Path(schema_file).write_text(json.dumps(schema))
        prompt = (system.rstrip() + "\n\n" + user) if system else user
        t0 = time.monotonic()
        try:
            p = subprocess.run(
                self._argv(workdir, last_file, schema_file),
                input=prompt, capture_output=True, text=True,
                env=scrubbed_env(), timeout=timeout or self.timeout, cwd=workdir)
        except subprocess.TimeoutExpired:
            raise CodexTimeout("codex CLI timed out after %ss"
                               % (timeout or self.timeout))
        except FileNotFoundError:
            raise CodexCLIError("codex CLI not found at %r" % self.binary)

        stderr = (p.stderr or "")[:600]
        if _looks_like_a_limit(stderr):
            raise CodexSubscriptionLimit(stderr)

        usage, thread_id = {}, ""
        for line in (p.stdout or "").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except Exception:                                      # noqa: BLE001
                continue
            if ev.get("type") == "thread.started":
                thread_id = ev.get("thread_id") or ""
            elif ev.get("type") == "turn.completed":
                usage = ev.get("usage") or {}
            elif ev.get("type") == "turn.failed":
                blob = json.dumps(ev)[:500]
                if _looks_like_a_limit(blob):
                    raise CodexSubscriptionLimit(blob)
                raise CodexCLIError("codex reported turn.failed: %s" % blob)

        text = ""
        if os.path.exists(last_file):
            text = pathlib.Path(last_file).read_text()
        if not text.strip():
            if p.returncode != 0:
                raise CodexCLIError("codex exited %s: %s" % (p.returncode, stderr))
            raise CodexOutputError("codex produced no final message")
        if _looks_like_a_limit(text) and len(text) < 400:
            raise CodexSubscriptionLimit(text[:400])

        self.calls += 1
        return Completion(
            text=text, requested_model=self.model,
            actual_model=RESOLVED_MODEL_UNDISCLOSED,
            usage=usage, duration_ms=int((time.monotonic() - t0) * 1000),
            thread_id=thread_id, effort=self.effort)


_PROVIDERS: dict = {}


def get_provider(model: str = DEFAULT_MODEL, binary: str = "codex",
                 effort: str = DEFAULT_EFFORT, timeout: int = DEFAULT_TIMEOUT):
    key = (model, binary, effort)
    if key not in _PROVIDERS:
        _PROVIDERS[key] = CodexCLIProvider(model=model, binary=binary, effort=effort,
                                           timeout=timeout)
    return _PROVIDERS[key]


def reset_providers() -> None:
    _PROVIDERS.clear()
