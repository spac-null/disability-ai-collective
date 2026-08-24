#!/usr/bin/env python3
"""
engine_switch.py -- the ONE engine-selection boundary for article generation.

    CRIPMINDS_ENGINE=legacy          (default)
    CRIPMINDS_ENGINE=new_engine_v1

Follows the project's existing convention: an explicit environment variable supplied by
the cron line, exactly like SHADOW_CAPTURE=1 and NEW_ENGINE_V1_MODE.

RULES
  * Default is legacy. An unset variable changes nothing about today's behaviour.
  * An UNKNOWN value FAILS CLOSED -- it raises rather than guessing, because a typo in a
    cron line must not silently pick an engine.
  * There is no post-start fallback. Once NEW_ENGINE_V1 has begun an editorial run it
    owns that run: a HOLD is a result, not a reason to re-run on legacy. Provider-level
    fallback INSIDE the approved provider adapter is unaffected.

ROLLBACK is this file's whole point: switching back is removing `CRIPMINDS_ENGINE=
new_engine_v1` from the cron line (or setting it to `legacy`). No database restore, no
migration, no history rewrite, no source-state repair.
"""
from __future__ import annotations

import os

ENV_VAR = "CRIPMINDS_ENGINE"
LEGACY = "legacy"
NEW_ENGINE_V1 = "new_engine_v1"
KNOWN = (LEGACY, NEW_ENGINE_V1)
DEFAULT = LEGACY


class UnknownEngine(Exception):
    """Raised on an unrecognised CRIPMINDS_ENGINE value. Never defaulted away."""


def resolve_engine(value: str | None = None) -> str:
    """The selected engine. Fail-closed on anything unrecognised."""
    raw = os.environ.get(ENV_VAR, "") if value is None else value
    name = (raw or "").strip().lower()
    if not name:
        return DEFAULT
    if name not in KNOWN:
        raise UnknownEngine(
            "%s=%r is not a known engine. Known: %s. Refusing to guess -- set it "
            "explicitly or unset it to use %s."
            % (ENV_VAR, raw, ", ".join(KNOWN), DEFAULT))
    return name


def is_new_engine(value: str | None = None) -> bool:
    return resolve_engine(value) == NEW_ENGINE_V1
