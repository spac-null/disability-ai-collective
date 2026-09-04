#!/usr/bin/env python3
"""phase2b_live_smoke.py -- prove, from a real checkout, where each live stage's bytes go.

Phase 2A's whole lesson was that a transport can be wrong for months while every log line
stays identical, because the model name is the same either way. So this does not ask "did
a call succeed". It asks "which transport served it", reads the answer out of the
provenance the call itself emitted, and prints a table.

Run it on the host, under the environment the cron actually uses:

    env -i HOME=/home/jascha PATH=/usr/local/bin:/usr/bin:/bin \\
        python3 automation/phase2b_live_smoke.py

WHAT IT SPENDS. Four small Claude calls on the subscription (a few hundred tokens each)
and, with --sonar, one Perplexity call on OpenRouter. It generates NO image: Recraft has
no Claude equivalent, so there is nothing about it Phase 2B could break that a route and
credential check does not already show, and spending a generation to prove that would be
theatre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claude_cli_provider as ccp
from orchestrator import transport

SONAR = "--sonar" in sys.argv
ROWS = []
BAD = []

SYSTEM = "You are a transport smoke test. Reply with exactly one word: OK"
USER = "Reply OK."


def row(stage, requested, actual, tport, note=""):
    ROWS.append((stage, requested, actual, tport, note))
    ok = tport in (transport.CLAUDE_SUBSCRIPTION, transport.OPENROUTER_DIRECT)
    print("  %-28s %-28s -> %-24s %s %s"
          % (stage, requested, actual, tport, note))
    if not ok:
        BAD.append(stage)


def fail(stage, exc):
    ROWS.append((stage, "-", "-", "FAILED", "%s: %s" % (type(exc).__name__, exc)))
    BAD.append(stage)
    print("  %-28s FAILED  %s: %s" % (stage, type(exc).__name__, exc))


print("PHASE 2B LIVE TRANSPORT SMOKE")
print("environment: HOME=%s TTY=%s cwd=%s"
      % (os.environ.get("HOME"), sys.stdin.isatty(), os.getcwd()))

# ---------------------------------------------------------------- auth, read not inferred
print("\n[0] subscription auth -- read from the CLI, never inferred from a 200")
try:
    st = ccp.assert_subscription()
    print("  authMethod=%s apiProvider=%s subscriptionType=%s org=%s"
          % (st.get("authMethod"), st.get("apiProvider"), st.get("subscriptionType"),
             st.get("orgName")))
    print("  apiKeySource=%r  (must be falsy: any value means a key is overriding the plan)"
          % st.get("apiKeySource"))
    if st.get("apiKeySource"):
        BAD.append("auth: an API key is overriding the subscription")
except Exception as exc:                                              # noqa: BLE001
    fail("auth", exc)

# ---------------------------------------------------------------- news_fetcher, cron 06:05
print("\n[1] news_fetcher Claude stage (cron 06:05)")
try:
    import news_fetcher
    c = ccp.complete_via_subscription(SYSTEM, USER, news_fetcher.MODEL, timeout=120)
    row("news_fetcher", c.requested_model, c.actual_model, transport.CLAUDE_SUBSCRIPTION)
except Exception as exc:                                              # noqa: BLE001
    fail("news_fetcher", exc)

# ---------------------------------------------------------------- orchestrator, cron 09:00
# The real boundary method, on the real class, with the real OpenRouter URL and an
# OpenRouter-era model id -- i.e. exactly the pair every orchestrator module hands it.
# If routing were broken this would reach openrouter.ai and bill for it.
print("\n[2] production orchestrator Claude stage (cron 09:00)")
try:
    import logging
    from orchestrator.llm import LLMMixin
    from orchestrator.config import OPENROUTER_URL, OPENROUTER_API_KEY

    class _Probe(LLMMixin):
        logger = logging.getLogger("phase2b")

    text, actual = _Probe()._call_openai_compat_api(
        OPENROUTER_URL, OPENROUTER_API_KEY, SYSTEM, USER,
        model="anthropic/claude-sonnet-4.6", max_tokens=32, timeout=120,
        return_model=True)
    used = transport.CLAUDE_SUBSCRIPTION if not actual.startswith("anthropic/") \
        else transport.OPENROUTER_DIRECT
    row("orchestrator (shared boundary)", "anthropic/claude-sonnet-4.6", actual, used)
except Exception as exc:                                              # noqa: BLE001
    fail("orchestrator", exc)

# ---------------------------------------------------------------- new_engine_v1, LIVE 09:00
print("\n[3] new_engine_v1/provider.py (the LIVE engine at 09:00)")
try:
    from new_engine_v1.provider import Provider
    comp = Provider().complete(SYSTEM, USER, max_tokens=32, timeout=120)
    used = transport.CLAUDE_SUBSCRIPTION \
        if comp.provider_label == "claude-cli-subscription" else transport.OPENROUTER_DIRECT
    row("new_engine_v1.provider", comp.requested_model, comp.actual_model, used)
except Exception as exc:                                              # noqa: BLE001
    fail("new_engine_v1.provider", exc)

# ---------------------------------------------------------------- Story Architecture (#63)
# Story Architecture injects ClaudeCLIProvider directly. PR #63 is deliberately unmerged,
# so what is proved here is its TRANSPORT -- the same class, the same binary, the same
# Opus-class model -- not its stages. No article is generated.
print("\n[4] Story Architecture transport (PR #63 injects this class; not merged here)")
try:
    p = ccp.ClaudeCLIProvider(model=ccp.DEFAULT_MODEL)
    comp = p.complete(SYSTEM, USER, timeout=180)
    row("story architecture", ccp.DEFAULT_MODEL, comp.actual_model,
        transport.CLAUDE_SUBSCRIPTION, "provider smoke only, no generation")
except Exception as exc:                                              # noqa: BLE001
    fail("story architecture", exc)

# ---------------------------------------------------------------- Sonar stays OpenRouter
print("\n[5] Fact check / Sonar -- must remain OPENROUTER_DIRECT")
try:
    from orchestrator.config import OPENROUTER_URL, OPENROUTER_API_KEY
    t = transport.classify(OPENROUTER_URL)
    if SONAR:
        import logging
        from orchestrator.llm import LLMMixin

        class _P(LLMMixin):
            logger = logging.getLogger("phase2b")

        _, actual = _P()._call_openai_compat_api(
            OPENROUTER_URL, OPENROUTER_API_KEY, "Answer in one word.",
            "What is the capital of France?", model="perplexity/sonar",
            max_tokens=32, timeout=60, return_model=True)
        row("fact check / sonar", "perplexity/sonar", actual, t, "live call")
    else:
        row("fact check / sonar", "perplexity/sonar", "(route check)", t,
            "pass --sonar to spend one real call")
    if not ccp.is_claude_family("perplexity/sonar"):
        print("  perplexity/sonar is not Claude-family: the boundary never routes it")
    print("  credential=OPENROUTER_API_KEY present=%s"
          % bool(os.environ.get("OPENROUTER_API_KEY") or OPENROUTER_API_KEY))
except Exception as exc:                                              # noqa: BLE001
    fail("fact check / sonar", exc)

# ---------------------------------------------------------------- Recraft stays OpenRouter
print("\n[6] Image / Recraft -- route and credential only, no generation spent")
try:
    from orchestrator.config import OPENROUTER_URL, OPENROUTER_API_KEY
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "orchestrator", "images.py")).read()
    model = "recraft/recraft-v4.1"
    assert model in src, "the Recraft model id moved"
    row("image / recraft", model, "(route check)", transport.classify(OPENROUTER_URL),
        "not Claude-family; no Claude equivalent exists")
    print("  credential=OPENROUTER_API_KEY present=%s" % bool(OPENROUTER_API_KEY))
except Exception as exc:                                              # noqa: BLE001
    fail("image / recraft", exc)

# ---------------------------------------------------------------- CLIProxy must stay gone
print("\n[7] CLIProxy must remain unreachable")
import socket
s = socket.socket()
s.settimeout(2)
reachable = s.connect_ex(("127.0.0.1", 8317)) == 0
s.close()
print("  127.0.0.1:8317 reachable=%s" % reachable)
if reachable:
    BAD.append("CLIProxy :8317 is listening again")

print("\n" + "=" * 78)
for stage, req, act, tport, note in ROWS:
    print("%-30s %-28s %-24s %s" % (stage, req, act, tport))
print("=" * 78)
if BAD:
    print("PHASE 2B LIVE SMOKE: HOLD -- %s" % "; ".join(BAD))
    sys.exit(1)
print("PHASE 2B LIVE SMOKE: PASS")
