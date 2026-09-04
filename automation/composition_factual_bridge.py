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
    """What is absent that the authoritative check needs. Reported, never worked around."""
    from orchestrator.config import CLIPROXY_URL, CLIPROXY_KEY

    missing = []
    if not CLIPROXY_KEY:
        missing.append("CLIPROXY_KEY")
    if not os.environ.get("OPENROUTER_API_KEY"):
        missing.append("OPENROUTER_API_KEY")
    # An HTTP reply -- 401 included -- means the proxy is up and asking for a key. Only a
    # transport failure means it is not there. An earlier version of this check treated
    # 401 as unreachable and reported the stage NOT RUN on a host where it could have run.
    try:
        req = urllib.request.Request(CLIPROXY_URL + "/models",
                                     headers={"Authorization": "Bearer " + CLIPROXY_KEY})
        urllib.request.urlopen(req, timeout=6)
    except urllib.error.HTTPError:
        pass
    except Exception as e:                                        # noqa: BLE001
        missing.append("CLIProxyAPI at %s (%s)" % (CLIPROXY_URL, type(e).__name__))
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
