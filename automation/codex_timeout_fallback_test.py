#!/usr/bin/env python3
"""Claude timeout can use ChatGPT subscription without touching a paid endpoint."""
import os
from unittest.mock import patch

import claude_cli_provider as CCP
import codex_subscription_provider as CDP
from new_engine_v1 import provider as NEP


class FakeCompletion:
    def __init__(self):
        self.text = '{"ok": true}'
        self.metadata = {"provider": "codex-cli-chatgpt-subscription",
                         "requested_model": "gpt-6-astra", "actual_model": None}

    def identity(self):
        return dict(self.metadata)


class FakeCodex:
    calls = []

    def __init__(self, **kwargs):
        self.calls.append(("init", kwargs))

    def complete(self, system, user, **kwargs):
        self.calls.append(("complete", system, user, kwargs))
        return FakeCompletion()


def timeout(*args, **kwargs):
    raise CCP.SubscriptionTimeout("Claude exceeded its call budget")


def paid_endpoint(*args, **kwargs):
    raise AssertionError("a paid HTTP endpoint was reached")


def run():
    with patch.object(CCP, "complete_via_subscription", timeout), \
         patch.object(CDP, "CodexSubscriptionProvider", FakeCodex), \
         patch.object(NEP, "_post", paid_endpoint), \
         patch.dict(os.environ, {"CRIPMINDS_CODEX_TIMEOUT_FALLBACK": "1"}):
        result = NEP.Provider().complete("system", "user", max_tokens=2000)
    assert result.text == '{"ok": true}'
    assert result.identity()["fallback_from"] == CCP.CLAUDE_SUBSCRIPTION_TIMEOUT
    assert result.identity()["original_requested_model"] == NEP.DEFAULT_MODEL
    assert result.identity()["actual_model"] is None
    assert [call[0] for call in FakeCodex.calls] == ["init", "complete"]

    FakeCodex.calls.clear()
    with patch.object(CCP, "complete_via_subscription", timeout), \
         patch.object(CDP, "CodexSubscriptionProvider", FakeCodex), \
         patch.dict(os.environ, {"CRIPMINDS_CODEX_TIMEOUT_FALLBACK": "0"}):
        try:
            NEP.Provider().complete("system", "user")
        except NEP.ProviderError as error:
            assert CCP.CLAUDE_SUBSCRIPTION_TIMEOUT in str(error)
        else:
            raise AssertionError("a disabled fallback hid the Claude timeout")
    assert not FakeCodex.calls

    print("Codex subscription fallback on Claude timeout: PASS")


if __name__ == "__main__":
    run()
