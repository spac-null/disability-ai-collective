#!/usr/bin/env python3
"""cliproxy_removal_test.py -- no live path may reach CLIProxyAPI again.

WHY A TEST AND NOT A ONE-OFF GREP. The CLIProxy hop survived for months because nothing
could see it: the model name was identical whether a call went through the proxy or
straight to OpenRouter, so its credential could expire and every log line stayed the
same. A grep proves today; a test proves every day. The reachability check below is
deliberately import-graph based rather than a flat grep over automation/*.py, because
the repo also holds frozen probe harnesses and archived experiment fixtures that name
the proxy for historical reasons and must keep naming it.

Stdlib only, matching every other test in this directory. No network.
"""
import ast
import os
import re
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    if cond:
        print("  PASS  %s" % label)
    else:
        print("  FAIL  %s%s" % (label, (" -- " + detail) if detail else ""))
        FAILURES.append(label)


AUTOMATION = os.path.dirname(os.path.abspath(__file__))

# The scheduled entry points. Anything importable from one of these can run in
# production; anything else cannot, whatever it mentions.
LIVE_ENTRYPOINTS = [
    "news_fetcher",              # cron 06:05
    "production_orchestrator",   # cron 09:00
    "bsky_outreach_auto",        # cron Sat 10:15
    "publish_best",              # cron 08:00 every other day
    "engagement_fetch",          # cron 11:00
    "link_pool_crawler",         # cron Sun 03:00
    "backup_state_dbs",          # cron 03:30
    "selector_v2_shadow_test",   # enabled by the 09:00 cron's own environment
]

PROXY_TOKENS = ("8317", "CLIPROXY_URL", "CLIPROXY_KEY", "NEW_ENGINE_CLIPROXY_URL")


def _module_map():
    mods = {}
    for dirpath, dirnames, filenames in os.walk(AUTOMATION):
        dirnames[:] = [d for d in dirnames
                       if d not in ("__pycache__", "probe_out", ".probe_fixtures")]
        for fn in filenames:
            if fn.endswith(".py"):
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, AUTOMATION)[:-3].replace(os.sep, ".")
                mods[rel] = path
    return mods


def _imports(path):
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError):
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def live_modules():
    """Transitive closure of the scheduled entry points, by real import edges."""
    mods = _module_map()
    seen, queue = set(), deque()
    for entry in LIVE_ENTRYPOINTS:
        if entry in mods:
            seen.add(entry)
            queue.append(entry)
    while queue:
        for dep in _imports(mods[queue.popleft()]):
            for candidate in (dep, dep.split(".")[0]):
                if candidate in mods and candidate not in seen:
                    seen.add(candidate)
                    queue.append(candidate)
    return {m: mods[m] for m in seen}


print("\ntest_no_live_module_reaches_cliproxy")
LIVE = live_modules()
check("the live import closure is non-trivial", len(LIVE) > 20,
      "found only %d modules -- the walk is probably broken" % len(LIVE))
for entry in LIVE_ENTRYPOINTS:
    check("entry point %s resolved" % entry, entry in LIVE)

offenders = []
for name, path in sorted(LIVE.items()):
    text = open(path, encoding="utf-8").read()
    # Comments may name the proxy: the removal is worth explaining where it happened.
    code_lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    code = "\n".join(code_lines)
    hits = [t for t in PROXY_TOKENS if t in code]
    # transport.py must name the port -- classifying the proxy is its whole job.
    if name == "orchestrator.transport":
        continue
    if hits:
        offenders.append("%s: %s" % (name, ",".join(hits)))
check("LIVE CLIPROXY CONSUMERS = 0", not offenders, "; ".join(offenders))


print("\ntest_transport_is_derived_from_url_not_model")
from orchestrator import transport  # noqa: E402

check("loopback :8317 is CLIPROXY",
      transport.classify("http://127.0.0.1:8317/v1") == transport.CLIPROXY)
check("docker bridge :8317 is CLIPROXY too",
      transport.classify("http://172.19.0.1:8317/v1") == transport.CLIPROXY)
check("openrouter.ai is OPENROUTER_DIRECT",
      transport.classify("https://openrouter.ai/api/v1") == transport.OPENROUTER_DIRECT)
check("an anthropic-named model over the proxy is still CLIPROXY",
      transport.classify("http://127.0.0.1:8317/v1") == transport.CLIPROXY)
check("empty url is UNKNOWN_TRANSPORT",
      transport.classify("") == transport.UNKNOWN_TRANSPORT)
check("uses_cliproxy agrees with classify",
      transport.uses_cliproxy("http://127.0.0.1:8317/v1")
      and not transport.uses_cliproxy("https://openrouter.ai/api/v1"))

rec = transport.record("https://openrouter.ai/api/v1",
                       requested_model="anthropic/claude-opus-4.8",
                       actual_model="anthropic/claude-opus-4.8",
                       credential_env="OPENROUTER_API_KEY", ok=True)
check("record names the credential variable, never a value",
      rec["credential_source"] == "OPENROUTER_API_KEY"
      and set(rec) >= {"transport", "provider", "credential_source", "credential_present",
                       "requested_model", "actual_model", "fallback_used"})
check("no record field carries a secret-looking value",
      all(not isinstance(v, str) or "sk-" not in v for v in rec.values()))
check("fallback_used is false when the model was not substituted",
      rec["fallback_used"] is False)
sub = transport.record("https://openrouter.ai/api/v1",
                       requested_model="anthropic/claude-fable-5",
                       actual_model="anthropic/claude-opus-4.8")
check("fallback_used tracks MODEL substitution only", sub["fallback_used"] is True)
check("transport is not inferred from the model name",
      sub["transport"] == transport.OPENROUTER_DIRECT)


print("\ntest_config_exposes_openrouter_not_a_proxy")
from orchestrator import config  # noqa: E402

check("OPENROUTER_URL points at openrouter.ai",
      transport.classify(config.OPENROUTER_URL) == transport.OPENROUTER_DIRECT,
      config.OPENROUTER_URL)
check("no CLIPROXY_URL name survives in config", not hasattr(config, "CLIPROXY_URL"))
check("no CLIPROXY_KEY name survives in config", not hasattr(config, "CLIPROXY_KEY"))
check("__all__ advertises the new names",
      "OPENROUTER_URL" in config.__all__ and "OPENROUTER_API_KEY" in config.__all__)
check("__all__ advertises no proxy name",
      not any("CLIPROXY" in n for n in config.__all__))


print("\ntest_new_engine_provider_has_one_direct_rung")
from new_engine_v1 import provider  # noqa: E402

check("provider has no DEFAULT_CLIPROXY_URL",
      not hasattr(provider, "DEFAULT_CLIPROXY_URL"))
check("provider OPENROUTER_URL is direct",
      transport.classify(provider.OPENROUTER_URL) == transport.OPENROUTER_DIRECT)
p = provider.Provider()
check("Provider carries no cliproxy_url attribute", not hasattr(p, "cliproxy_url"))
check("Provider's url is direct OpenRouter",
      transport.classify(p.url) == transport.OPENROUTER_DIRECT, p.url)
src = open(os.path.join(AUTOMATION, "new_engine_v1", "provider.py"),
           encoding="utf-8").read()
body = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
check("no CLIProxy attempt remains in provider.complete",
      '"CLIProxy"' not in body and "CLIPROXY_KEY" not in body)


print("\ntest_proxy_only_model_names_cannot_reach_a_direct_endpoint")
# `openrouter/claude-*` was CLIProxy's translation key. Direct OpenRouter answers such a
# name with a 500 "unknown provider", so the normaliser is what makes a stale call site
# harmless instead of an opaque failure far from its cause.
llm_src = open(os.path.join(AUTOMATION, "orchestrator", "llm.py"), encoding="utf-8").read()
check("the chokepoint normalises the proxy-only prefix",
      'wire_model = "anthropic/" + model[len("openrouter/"):]' in llm_src)
check("the request body sends the normalised name, not the raw one",
      '"model": wire_model,' in llm_src)
check("normalisation is gated on the transport, not on the model",
      "transport.classify(url) == transport.OPENROUTER_DIRECT" in llm_src)
check("the chokepoint emits a provenance line",
      "transport.line(transport.record(" in llm_src)
check("a prefix rewrite is not reported as a model fallback",
      "requested_model=wire_model," in llm_src,
      "requested_model must be the wire model, or normalisation fakes fallback_used")
check("the rewrite is still recorded, in detail",
      "normalised proxy-only model name" in llm_src)

live_model_names = []
for name, path in sorted(LIVE.items()):
    if name == "orchestrator.transport":
        continue
    text = open(path, encoding="utf-8").read()
    for i, ln in enumerate(text.splitlines(), 1):
        if ln.lstrip().startswith("#"):
            continue
        # A proxy-only MODEL NAME is the prefix followed by the model, e.g.
        # "openrouter/claude-opus-4.8". The bare prefix `"openrouter/"` is the
        # normaliser's own needle in llm.py and must stay exactly there.
        if re.search(r"""["']openrouter/\w""", ln):
            live_model_names.append("%s:%d" % (name, i))
check("no live module still names a proxy-only model", not live_model_names,
      ", ".join(live_model_names))


print("\ntest_gemini_rung_removed_and_not_replaced")
check("no Gemini endpoint in the live editorial ladder",
      "generativelanguage.googleapis.com" not in llm_src)
check("no GEMINI_API_KEY read in the live editorial ladder",
      "GEMINI_API_KEY" not in llm_src)
llm_code = "\n".join(ln for ln in llm_src.splitlines()
                      if not ln.lstrip().startswith("#"))
check("no substitute Gemini model id was introduced",
      "gemini-" not in llm_code.lower(),
      "prose recording the removal is fine; a model id is not")


print("\n" + "-" * 60)
if FAILURES:
    print("CLIPROXY REMOVAL: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d CLIPROXY REMOVAL TESTS PASSED" % CHECKS[0])
