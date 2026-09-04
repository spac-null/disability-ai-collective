"""
composition_factual_bridge.py -- the authoritative Fact Check, for the composition path.

WHY THIS FILE EXISTS AND WHY IT IS HERE, not in `new_engine_v1/`.
The authoritative external Fact Check is `orchestrator.fact_check.FactCheckMixin`, and
`new_engine_v1` is asserted by test to import no part of the legacy orchestrator -- an
AST scan that sees a function-local import exactly as it sees a top-level one. That
constraint is worth keeping, so the bridge lives on this side of the boundary and is
INJECTED into the composition run, the same way `runner.run` already takes a
`research_fn`.

WHAT IT IS NOT. It is not a second Fact Check. `_run_web_fact_check` is called unmodified,
with the same `strict=True` the current engine uses, and its verdicts are not
reinterpreted -- only summarised into the fields the composition result reports.

`heldout_factual_bridge.py` was the reference for this and is deliberately not imported:
it carries the held-out article's own paths, its hardcoded source ids and a hand-written
per-component fallback for one specific fact.

PROVIDER NOTE. This is the one composition stage that legitimately reaches OpenRouter:
the Perplexity Sonar checks live there and always have. Composition generation does not
(see `composition.composition_provider`).
"""
from __future__ import annotations

import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

NOT_RUN = "NOT_RUN"
PASS = "PASS"
HOLD = "HOLD"

DEFAULT_CLAIM_CAP = 8


class _Log:
    """The mixins log through self.logger; nothing here needs the output."""

    def _p(self, m, *a):
        pass

    info = debug = warning = error = _p


def credentials_missing() -> list:
    """What is absent that the authoritative check needs. Reported, never worked around.

    Rewritten 2026-09-05. This used to require the old local proxy's key and probe its
    /models endpoint. Both are gone: Phase 2A removed that hop from every live path and
    the service is stopped and disabled, so the probe could only ever add a false NOT RUN
    on a host where the stage runs perfectly well. The env-var names are deliberately not
    written out here -- cliproxy_removal_test scans live modules for them.

    What STAGE 9 actually needs now is two different things, because the fact check is
    two different kinds of call:

      OPENROUTER_API_KEY   the authoritative Perplexity/Sonar web verification, which is
                           not a Claude model and cannot come from a Claude subscription.
      Claude subscription  the claim-extraction reasoning, which Phase 2B moved onto the
                           owner's plan.

    The subscription is READ from the CLI rather than assumed from a successful call --
    an API key in the environment still produces completions, just billed elsewhere.
    """
    missing = []
    if not os.environ.get("OPENROUTER_API_KEY"):
        try:
            from orchestrator.config import OPENROUTER_API_KEY
        except Exception:                                         # noqa: BLE001
            OPENROUTER_API_KEY = ""
        if not OPENROUTER_API_KEY:
            missing.append("OPENROUTER_API_KEY (Perplexity/Sonar web verification)")
    try:
        import claude_cli_provider
        claude_cli_provider.assert_subscription()
    except Exception as e:                                        # noqa: BLE001
        missing.append("Claude subscription (%s: %s)" % (type(e).__name__, str(e)[:120]))
    return missing


def fact_check(article_text: str, claim_cap: int = DEFAULT_CLAIM_CAP) -> dict:
    """The composition path's STAGE 9. Signature: one article in, one result out."""
    t0 = time.time()
    try:
        from orchestrator.fact_check import FactCheckMixin
        from orchestrator.llm import LLMMixin
    except ImportError as e:
        return {"status": NOT_RUN, "missing": ["orchestrator: %s" % e],
                "runtime_seconds": 0.0}

    missing = credentials_missing()
    if missing:
        return {"status": NOT_RUN, "missing": missing,
                "runtime_seconds": round(time.time() - t0, 1)}

    class _Runner(LLMMixin, FactCheckMixin):
        def __init__(self):
            self.logger = _Log()

    try:
        r = _Runner()._run_web_fact_check(article_text, claim_cap=claim_cap, strict=True)
    except Exception as e:                                        # noqa: BLE001
        # A transport or provider failure is NOT_RUN, not PASS. The distinction matters:
        # "we could not check" and "we checked and found nothing" are different answers
        # and only one of them is permission.
        return {"status": NOT_RUN,
                "missing": ["%s: %s" % (type(e).__name__, str(e)[:200])],
                "runtime_seconds": round(time.time() - t0, 1)}

    r["runtime_seconds"] = round(time.time() - t0, 1)
    r["blocking_contradictions"] = list(r.get("contradicted") or [])
    r["soft_findings"] = list(r.get("advisory") or [])
    r["unverifiable"] = r.get("unverifiable_count")
    r["claims_checked"] = r.get("claims_extracted")
    r["provider_calls"] = r.get("provider_calls")
    r["completed"] = bool(r.get("fact_check_completed"))
    r["status"] = (HOLD if (r["blocking_contradictions"]
                            or r.get("extraction_status") == "error"
                            or not r["completed"]) else PASS)
    return r
