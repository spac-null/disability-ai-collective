#!/usr/bin/env python3
"""
engine_switch.py -- the ONE engine-selection boundary for article generation.

    CRIPMINDS_ENGINE=new_engine_v1   (default)
    CRIPMINDS_ENGINE=legacy

Follows the project's existing convention: an explicit environment variable supplied by
the cron line, exactly like SHADOW_CAPTURE=1 and NEW_ENGINE_V1_MODE.

RULES
  * Default is new_engine_v1 (formal cutover, 2026-08-27). An unset variable selects the
    new engine. Before the cutover the default was legacy and new_engine_v1 was opt-in;
    the scheduler had already been running it explicitly, and the 2026-08-27 natural
    production run demonstrated the strict publication-safety bridge failing closed on a
    real ACCEPT, which is what the cutover waited for.
  * An UNKNOWN value FAILS CLOSED -- it raises rather than guessing, because a typo in a
    cron line must not silently pick an engine.
  * There is no post-start fallback. Once NEW_ENGINE_V1 has begun an editorial run it
    owns that run: a HOLD is a result, not a reason to re-run on legacy. Provider-level
    fallback INSIDE the approved provider adapter is unaffected.

ROLLBACK is this file's whole point: set `CRIPMINDS_ENGINE=legacy` on the cron line. The
legacy engine is untouched and that value still dispatches to it. No database restore, no
migration, no history rewrite, no source-state repair. Note the one thing the cutover
changed about rollback: UNSETTING the variable no longer means legacy, so a rollback is
now an explicit value rather than a deletion.
"""
from __future__ import annotations

import os

ENV_VAR = "CRIPMINDS_ENGINE"
LEGACY = "legacy"
NEW_ENGINE_V1 = "new_engine_v1"
KNOWN = (LEGACY, NEW_ENGINE_V1)
DEFAULT = NEW_ENGINE_V1


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
