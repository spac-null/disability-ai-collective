"""Current-production baseline: `validate_turn_support` run offline, read-only.

The production function is imported unmodified from the engine package. It answers one
question only: is every RELATION CLASS the turn asserts also present, lexically, in at
least one licensing fact's proposition? It is a coarse class licence, not a check that
the relation holds between these particular terms -- the docstring says so itself.

No model call, no network, no side effects.
"""
from __future__ import annotations

import os
import sys

ENGINE = "/srv/data/hermes/workspace/factuality-bakeoff/automation"
if ENGINE not in sys.path:
    sys.path.insert(0, ENGINE)

from new_engine_v1 import story as _story  # noqa: E402

QUESTION = ("Is every relation CLASS asserted by the turn lexically present in at least "
            "one cited fact's proposition? Coarse class availability, not term-level truth.")


def ledger_of(facts: dict) -> dict:
    """Shape the frozen manifest facts the way validate_turn_support expects."""
    return {fid: {"proposition": f.get("proposition") or ""} for fid, f in (facts or {}).items()}


def check(claim_text: str, fact_ids, facts: dict) -> dict:
    """Return the baseline decision for one claim against one basis."""
    ledger = ledger_of(facts)
    errs = _story.validate_turn_support(claim_text, list(fact_ids or []), ledger)
    relations = _story.turn_relations(claim_text or "")
    return {
        "decision": "UNSUPPORTED" if errs else "SUPPORTED",
        "n_errors": len(errs),
        "relations_asserted": {k: v for k, v in relations.items()},
        "errors": [
            {"code": e.get("code"), "relation": e.get("relation"), "carried_by": e.get("carried_by")}
            for e in errs
        ],
    }


def both_conditions(claim_text: str, cited_fact_ids, facts: dict) -> dict:
    """CITED_BASIS vs COMPLETE_FROZEN_EVIDENCE, reported separately (never combined)."""
    return {
        "CITED_BASIS": check(claim_text, cited_fact_ids, facts),
        "COMPLETE_FROZEN_EVIDENCE": check(claim_text, list((facts or {}).keys()), facts),
    }
