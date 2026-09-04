"""
provider_policy.py -- what a LIVE Cripminds run may do when Claude cannot answer.

OWNER POLICY, 2026-09-05. For live Claude-family workloads:

    subscription success  ->  use the result
    subscription failure  ->  explicit provider failure / HOLD

and NOT: Claude on Nous, Claude on OpenRouter, local Qwen, Gemini, or any other model.

THE REASON IS PROVENANCE AND EDITORIAL CONSISTENCY, NOT ONLY COST. A production run must
not silently change model family or tier because the preferred provider failed. Phase 2B
closed the paid-Claude half of that: a subscription refusal stops the Claude rungs instead
of buying the same completion from Nous or OpenRouter. It left two substitutions open, and
both were reachable in LIVE:

  1. THE LOCAL QWEN RUNG. Not Claude-family, so the Phase 2B skip did not apply to it. A
     refused Claude request fell straight through to a 9B local model, and the run
     continued and published under the same persona byline. Nothing downstream could tell:
     the article had an author, a length and a provider label, and provider label is not
     something the editorial gates read.

  2. generate_fallback_article. Worse, and quieter. When every provider failed, the legacy
     path substituted a canned Mad-Libs template -- four rotating openings selected by a
     hash of the title, fixed section pairs, `##` headers that the writer system prompt
     explicitly forbids -- attributed to the persona and carried on through the pipeline
     as `provider="fallback"`. That is not a degraded article. It is not an article.

Both are preserved, because both are genuinely useful for DEV, TEST, manual recovery and
explicit probes. Neither runs automatically in LIVE any more. They are gated on one
explicit opt-in, and the gate is opt-IN rather than opt-out on purpose: the failure mode
being prevented is silence, and a default that has to be remembered is not a default.
"""
from __future__ import annotations

import os

# One switch, covering every non-Claude automatic substitution in the legacy composition
# path -- the local model rung and the canned template alike. They are the same policy
# question ("may something other than Claude answer this?") and splitting them into two
# flags would only create a state where one is set and the other is not.
LOCAL_FALLBACK_ENV = "CRIPMINDS_ALLOW_LOCAL_FALLBACK"

_TRUE = ("1", "true", "yes", "on")

# The status a run reports when Claude could not answer and nothing else is permitted to.
# Distinct from an editorial HOLD: no editorial judgement was reached, because no article
# was written. Callers that need to tell an infrastructure failure from an editorial one
# read `run_status.status` -- see production_orchestrator._is_infra_or_contract_failure.
PROVIDER_HOLD_STATUS = "no_article_provider_failure"
PROVIDER_HOLD_RUN_STATUS = "PROVIDER_FAILURE"


def local_fallback_allowed(env=None) -> bool:
    """Whether a non-Claude model or the canned template may answer automatically.

    False in production. Set CRIPMINDS_ALLOW_LOCAL_FALLBACK=1 for a dev run, a test, or a
    deliberate manual recovery -- never in the scheduled environment.
    """
    env = os.environ if env is None else env
    return str(env.get(LOCAL_FALLBACK_ENV, "")).strip().lower() in _TRUE


def provider_hold(detail: str, attempted=None) -> dict:
    """The result a live run returns when Claude could not answer.

    Shaped like every other early return in _run_single_candidate_attempt, so no caller
    needs to learn a new convention to handle it.
    """
    return {
        "status": PROVIDER_HOLD_STATUS,
        "run_status": {"status": PROVIDER_HOLD_RUN_STATUS, "detail": detail},
        "provider_attempts": list(attempted or []),
        "message": (
            "Claude subscription could not serve this run and no automatic substitution "
            "is permitted in LIVE (%s). %s" % (LOCAL_FALLBACK_ENV, detail)
        ),
    }
