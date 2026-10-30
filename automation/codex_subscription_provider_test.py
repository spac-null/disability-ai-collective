"""Offline checks for the ChatGPT-authenticated Codex shadow transport."""
import json
import os
import pathlib
import subprocess
from unittest.mock import patch

from codex_subscription_provider import (CodexSubscriptionError,
                                         CodexSubscriptionProvider)


class FakeRunner:
    def __init__(self, *, auth="Logged in using ChatGPT", tool=False):
        self.auth = auth
        self.tool = tool
        self.command = None
        self.env = None

    def __call__(self, command, **kwargs):
        self.env = kwargs.get("env")
        if command[-2:] == ["login", "status"]:
            return subprocess.CompletedProcess(command, 0, "", self.auth)
        if command[-1] == "--version":
            return subprocess.CompletedProcess(command, 0, "codex-cli test", "")
        self.command = command
        pathlib.Path(command[command.index("--output-last-message") + 1]).write_text(
            "A finished essay.", encoding="utf-8")
        events = [{"type": "thread.started", "thread_id": "t1"}]
        if self.tool:
            events.append({"type": "item.completed", "item":
                           {"type": "command_execution"}})
        events.append({"type": "turn.completed", "usage": {"output_tokens": 4}})
        return subprocess.CompletedProcess(command, 0,
                                           "\n".join(json.dumps(e) for e in events), "")


def run():
    fake = FakeRunner()
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key",
                              "CODEX_API_KEY": "test-codex-key"}):
        provider = CodexSubscriptionProvider(executable="/bin/echo", runner=fake)
    result = provider.complete("System", "User", max_tokens=50)
    assert result.text == "A finished essay."
    assert result.identity()["provider"] == "codex-cli-chatgpt-subscription"
    assert result.identity()["actual_model"] is None
    assert "--sandbox" in fake.command and "read-only" in fake.command
    assert "--ephemeral" in fake.command
    assert fake.command[fake.command.index("--disable") + 1] == "apps"
    assert "gpt-6-astra" in fake.command
    assert result.identity()["tool_calls"] == 0
    assert "OPENAI_API_KEY" not in fake.env and "CODEX_API_KEY" not in fake.env

    try:
        CodexSubscriptionProvider(executable="/bin/echo",
                                  runner=FakeRunner(auth="Logged in using API key"))
    except CodexSubscriptionError:
        pass
    else:
        raise AssertionError("API-key authentication was accepted")

    try:
        CodexSubscriptionProvider(executable="/bin/echo",
                                  runner=FakeRunner(tool=True)).complete("S", "U")
    except CodexSubscriptionError:
        pass
    else:
        raise AssertionError("tool use was accepted")
    print("Codex subscription auth, model pin, isolation and tool refusal: PASS")


if __name__ == "__main__":
    run()
