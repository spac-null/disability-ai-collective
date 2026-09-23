"""provenance.py -- which code, and which system prompt, produced a call.

WHAT WAS ALREADY THERE, and is not re-done here. The engine's lineage is better than it
is usually given credit for: `MANIFEST.json` carries a `stage_hashes` map of every stage
artifact's `content_hash()`, which is a real Ledger -> Worth -> Architecture -> Writer
chain; the source snapshot is hashed; and `write_article` already retains the exact
rendered user prompt AND its sha256. None of that is touched.

WHAT WAS MISSING, exactly two things:

  1. NO CODE IDENTITY ANYWHERE. `grep -rn "rev-parse\\|git_sha\\|code_sha"` across the
     engine returned nothing. A retained run could not be attributed to the code that
     produced it, which is what turns a longitudinal comparison into an argument.
  2. NO SYSTEM-PROMPT IDENTITY. Only `compose_mode` was recorded. The system text is
     recoverable from the mode ONLY if you know the code version -- which was the thing
     not recorded. The two gaps closed each other's escape route.

So this module exists to make one sentence provable after the fact:

    this exact code + this exact system prompt + this exact rendered user prompt
    produced this Writer call.

It is deliberately small. It does not define a provenance framework, it does not touch
`contracts.py` -- which says of itself "Do not 'improve' this file. It is the frozen
contract" -- and it adds no stage, no artifact type and no schema version.

NO SUBPROCESS. The git sha is read off the filesystem rather than shelled out for: the
engine runs unattended under cron and a subprocess that hangs on a lock is a worse failure
than an empty string. Every accessor fails soft and returns "" -- provenance that can end
a publication day is not provenance.

TWO IDENTITIES, NOT ONE, because they answer different questions. `git_sha` says which
commit; `engine_source_sha256` says what the files actually contained, which is the honest
answer when a worktree is dirty, when a deploy is mid-pull, or when .git is absent
entirely. A run whose two identities disagree with another run's is a run you cannot
compare, and that is worth knowing.
"""
from __future__ import annotations

import functools
import hashlib
import os
import pathlib
import re

ENV_CODE_SHA = "CRIPMINDS_CODE_SHA"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _git_dir(start: pathlib.Path):
    """The .git directory for `start`, following a worktree's `gitdir:` pointer."""
    for p in [start] + list(start.parents):
        g = p / ".git"
        if g.is_dir():
            return g
        if g.is_file():
            txt = g.read_text(encoding="utf-8").strip()
            if txt.startswith("gitdir:"):
                d = pathlib.Path(txt.split(":", 1)[1].strip())
                return d if d.is_absolute() else (p / d).resolve()
    return None


def _common_dir(gd: pathlib.Path) -> pathlib.Path:
    """A linked worktree keeps HEAD locally and refs in the main repository."""
    c = gd / "commondir"
    if c.exists():
        d = pathlib.Path(c.read_text(encoding="utf-8").strip())
        return d if d.is_absolute() else (gd / d).resolve()
    return gd


@functools.lru_cache(maxsize=1)
def git_sha() -> str:
    """The commit this code was checked out at, or "" if that cannot be established."""
    env = (os.environ.get(ENV_CODE_SHA) or "").strip().lower()
    if _SHA40.match(env):
        return env
    try:
        gd = _git_dir(pathlib.Path(__file__).resolve())
        if gd is None:
            return ""
        head = (gd / "HEAD").read_text(encoding="utf-8").strip()
        if not head.startswith("ref:"):
            return head.lower() if _SHA40.match(head.lower()) else ""
        ref = head.split(":", 1)[1].strip()
        common = _common_dir(gd)
        for base in (gd, common):
            f = base / ref
            if f.is_file():
                v = f.read_text(encoding="utf-8").strip().lower()
                if _SHA40.match(v):
                    return v
        packed = common / "packed-refs"
        if packed.is_file():
            for line in packed.read_text(encoding="utf-8").splitlines():
                if line.startswith("#") or line.startswith("^") or not line.strip():
                    continue
                parts = line.split()
                if len(parts) == 2 and parts[1] == ref and _SHA40.match(parts[0].lower()):
                    return parts[0].lower()
        return ""
    except Exception:                                             # noqa: BLE001
        return ""


@functools.lru_cache(maxsize=1)
def engine_source_sha256() -> str:
    """sha256 over the engine package's own sources, by name then bytes.

    This is the identity that survives a dirty worktree, a missing .git and a half-applied
    deploy -- the three situations in which a commit sha is most confidently wrong.
    """
    try:
        d = pathlib.Path(__file__).resolve().parent
        h = hashlib.sha256()
        for p in sorted(d.glob("*.py"), key=lambda q: q.name):
            h.update(p.name.encode("utf-8"))
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
        return h.hexdigest()
    except Exception:                                             # noqa: BLE001
        return ""


def code_identity() -> dict:
    return {"git_sha": git_sha(), "engine_source_sha256": engine_source_sha256()}


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def call_identity(system: str, user: str, mode: str = "") -> dict:
    """The provable sentence, as a dict: this code, this system prompt, this user prompt."""
    return {"code": code_identity(),
            "compose_mode": mode,
            "system_sha256": sha256_text(system),
            "prompt_sha256": sha256_text(user)}
