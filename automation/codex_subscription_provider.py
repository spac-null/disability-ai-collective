"""Isolated text completion through a ChatGPT-authenticated Codex CLI session.

Codex CLI is an agent surface, so its instructions are not byte-equivalent to a direct
Responses API call. The CLI is run outside the repository, read-only, with no persisted
session. Any tool use fails the completion. The requested model is recorded separately
from the unresolved server model reported by the CLI.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass


class CodexSubscriptionError(RuntimeError):
    pass


@dataclass
class CodexCompletion:
    text: str
    metadata: dict

    def identity(self) -> dict:
        return dict(self.metadata)


class CodexSubscriptionProvider:
    def __init__(self, *, model: str = "gpt-6-astra",
                 reasoning_effort: str = "medium", executable: str = "codex",
                 timeout_seconds: int = 900, runner=None):
        if model != "gpt-6-astra":
            raise CodexSubscriptionError("the shadow subscription route is pinned to gpt-6-astra")
        if reasoning_effort not in ("low", "medium", "high", "xhigh", "max"):
            raise CodexSubscriptionError("unsupported reasoning effort")
        resolved = shutil.which(executable)
        if not resolved:
            raise CodexSubscriptionError("Codex CLI is not installed")
        self.executable = resolved
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self._run = runner or subprocess.run
        self._env = dict(os.environ)
        # A key in the parent process must not silently replace ChatGPT subscription
        # auth for this route. No key is passed to any Codex subprocess.
        self._env.pop("OPENAI_API_KEY", None)
        self._env.pop("CODEX_API_KEY", None)
        status = self._run([self.executable, "login", "status"],
                           capture_output=True, text=True, timeout=15, env=self._env)
        if status.returncode != 0 or "Logged in using ChatGPT" not in (
                status.stdout + status.stderr):
            raise CodexSubscriptionError(
                "Codex CLI must be signed in using ChatGPT subscription")
        version = self._run([self.executable, "--version"],
                            capture_output=True, text=True, timeout=15, env=self._env)
        self.cli_version = (version.stdout + version.stderr).strip() if version.returncode == 0 else "unknown"
        self.last_events = ""

    def complete(self, system: str, user: str, max_tokens: int = 8000,
                 temperature=None) -> CodexCompletion:
        # The CLI accepts one user prompt, not separate system and user roles. Preserve
        # both original strings verbatim inside explicit boundaries for auditability.
        prompt = (
            "Complete this single editorial writing task using only the text below. "
            "Do not use tools, read files, browse, or inspect the environment. "
            "Return only the requested completion.\n\n"
            "<EDITORIAL_INSTRUCTIONS>\n" + system +
            "\n</EDITORIAL_INSTRUCTIONS>\n\n<COMMISSION_AND_EVIDENCE>\n" + user +
            "\n</COMMISSION_AND_EVIDENCE>\n"
        )
        with tempfile.TemporaryDirectory(prefix="cripminds-codex-subscription-") as tmp:
            last = pathlib.Path(tmp) / "last-message.txt"
            cmd = [
                self.executable, "--ask-for-approval", "never", "exec",
                "--ephemeral", "--ignore-user-config", "--ignore-rules",
                "--skip-git-repo-check", "--sandbox", "read-only",
                "--model", self.model, "-c",
                'model_reasoning_effort="%s"' % self.reasoning_effort,
                "--cd", tmp, "--output-last-message", str(last), "--json", "-",
            ]
            try:
                proc = self._run(cmd, input=prompt, capture_output=True, text=True,
                                 cwd=tmp, timeout=self.timeout_seconds, env=self._env)
            except subprocess.TimeoutExpired as error:
                raise CodexSubscriptionError("Codex CLI timed out") from error
            if proc.returncode != 0:
                raise CodexSubscriptionError(
                    "Codex CLI failed: %s" % (proc.stderr or proc.stdout)[-500:])
            self.last_events = proc.stdout
            events = []
            for line in proc.stdout.splitlines():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise CodexSubscriptionError("Codex emitted non-JSON event data") from error
            if not events or not any(e.get("type") == "turn.completed" for e in events):
                raise CodexSubscriptionError("Codex did not report a completed turn")
            items = [e.get("item") or {} for e in events
                     if e.get("type") in ("item.started", "item.completed")]
            tool_types = sorted({str(item.get("type")) for item in items
                                 if item.get("type") not in ("agent_message", "reasoning")})
            if tool_types:
                raise CodexSubscriptionError(
                    "isolated writing call attempted tools: %s" % tool_types)
            if not last.exists():
                raise CodexSubscriptionError("Codex did not write its final message")
            answer = last.read_text(encoding="utf-8").strip()
            if not answer:
                raise CodexSubscriptionError("Codex returned an empty final message")
            thread = next((e.get("thread_id") for e in events
                           if e.get("type") == "thread.started"), None)
            usage = next((e.get("usage") for e in reversed(events)
                          if e.get("type") == "turn.completed"), {}) or {}
        return CodexCompletion(answer, {
            "requested_model": self.model,
            "actual_model": None,  # JSONL does not expose the server's resolved model.
            "model_resolution": "Codex CLI accepted explicit --model; actual model not in JSONL",
            "reasoning_effort_requested": self.reasoning_effort,
            "provider": "codex-cli-chatgpt-subscription",
            "auth": "ChatGPT subscription",
            "cli_version": self.cli_version,
            "thread_id": thread,
            "usage": usage,
            "tool_calls": 0,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "event_log_sha256": hashlib.sha256(self.last_events.encode("utf-8")).hexdigest(),
            "max_tokens_requested": max_tokens,
            "max_tokens_honored": False,
            "temperature_requested": temperature,
            "temperature_honored": False,
        })
