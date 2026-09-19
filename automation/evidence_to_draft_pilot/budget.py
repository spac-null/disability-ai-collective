"""
budget.py -- the pilot's call ledger, budget caps and resumable checkpoint.

Three jobs, deliberately in one place so they cannot disagree:

  1. RECORD EVERY CALL. Section 5 lists what must be on each row: access method,
     requested model, resolved model (UNKNOWN where the provider does not disclose it),
     effort, prompt version, input hash, usage, elapsed time and any transport failure.
     Nothing writes a model result anywhere else without passing through `record()`.

  2. ENFORCE THE CAPS. 90 subscription invocations for the whole pilot, including nested
     stage calls, judges and smoke tests; $2 aggregate OpenRouter cash. `reserve()` is
     called BEFORE a call is issued and raises rather than letting a cell start work the
     budget cannot pay for. Ambiguous timeouts and retries count, per section 7.

  3. MAKE CELLS RESUMABLE. A completed cell is written to disk the moment it finishes.
     `done()` answers whether a cell already has a result, so resuming never regenerates
     -- and never re-pays for -- work that is already on disk.

WHAT THIS DOES NOT DO. It does not decide that a cell should be re-run. There is no
selective rerun after an unattractive answer (section 7); the only retry this module
permits is ONE documented transport retry where no model result was received at all, and
it is recorded as its own row with `retry_of` set so the count stays honest.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time

SUBSCRIPTION_CALL_CAP = 90
OPENROUTER_CASH_CAP_USD = 2.00

SUBSCRIPTION_PROVIDERS = ("claude-cli-subscription", "codex-cli-subscription")


class BudgetExceeded(Exception):
    """A cap would be breached. Raised BEFORE the call, never after."""


def sha256_text(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


class Ledger:
    """Append-only call log plus the checkpoint the next session resumes from."""

    def __init__(self, root, *, subscription_cap: int = SUBSCRIPTION_CALL_CAP,
                 cash_cap_usd: float = OPENROUTER_CASH_CAP_USD):
        self.root = pathlib.Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.calls_path = self.root / "CALLS.jsonl"
        self.cells_dir = self.root / "cells"
        self.cells_dir.mkdir(exist_ok=True)
        self.checkpoint_path = self.root / "CHECKPOINT.json"
        self.subscription_cap = subscription_cap
        self.cash_cap_usd = cash_cap_usd
        self._rows = self._load_rows()

    # ── reading state ────────────────────────────────────────────────────────
    def _load_rows(self) -> list:
        if not self.calls_path.exists():
            return []
        rows = []
        for line in self.calls_path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:                                  # noqa: BLE001
                    pass
        return rows

    @property
    def subscription_calls(self) -> int:
        """Every subscription invocation, successful or not.

        A FAILED call still spent quota, so counting only successes would understate the
        budget -- which is why `calls_issued` defaults to 1 rather than to whether the
        cell produced a usable result. The one case it is 0 is a cell that provably made
        no request at all: a plan refused on the frozen beat layout before the planner
        was called, and the arm C that plan never reached. Charging those would overstate
        the budget just as badly in the other direction.
        """
        return sum(int(r.get("calls_issued", 1)) for r in self._rows
                   if r.get("provider") in SUBSCRIPTION_PROVIDERS)

    @property
    def openrouter_spend_usd(self) -> float:
        return round(sum(float(r.get("cash_cost_usd") or 0.0)
                         for r in self._rows if r.get("openrouter_used")), 6)

    @property
    def openrouter_requests(self) -> int:
        return sum(1 for r in self._rows if r.get("openrouter_used"))

    def summary(self) -> dict:
        by = {}
        for r in self._rows:
            by[r.get("provider") or "?"] = by.get(r.get("provider") or "?", 0) + 1
        return {
            "subscription_calls": self.subscription_calls,
            "subscription_cap": self.subscription_cap,
            "subscription_remaining": self.subscription_cap - self.subscription_calls,
            "openrouter_requests": self.openrouter_requests,
            "openrouter_spend_usd": self.openrouter_spend_usd,
            "openrouter_cap_usd": self.cash_cap_usd,
            "calls_by_provider": by,
            "transport_failures": sum(1 for r in self._rows if r.get("error_code")),
        }

    # ── caps ─────────────────────────────────────────────────────────────────
    def reserve(self, *, provider: str, cash_estimate_usd: float = 0.0) -> None:
        """Raise if issuing one more call of this kind would breach a cap."""
        if provider in SUBSCRIPTION_PROVIDERS:
            if self.subscription_calls + 1 > self.subscription_cap:
                raise BudgetExceeded(
                    "subscription call cap reached: %d of %d already spent"
                    % (self.subscription_calls, self.subscription_cap))
        if cash_estimate_usd:
            if self.openrouter_spend_usd + cash_estimate_usd > self.cash_cap_usd:
                raise BudgetExceeded(
                    "OpenRouter cash cap would be breached: $%.4f spent, $%.4f more "
                    "requested, cap $%.2f" % (self.openrouter_spend_usd,
                                              cash_estimate_usd, self.cash_cap_usd))

    # ── recording ────────────────────────────────────────────────────────────
    def record(self, *, cell: str, role: str, provider: str, requested_model: str,
               resolved_model: str, prompt_version: str, input_text: str,
               effort=None, usage=None, duration_ms=None, cash_cost_usd: float = 0.0,
               openrouter_used: bool = False, error_code=None, error_text=None,
               retry_of=None, extra=None) -> dict:
        row = {
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cell": cell,
            "role": role,
            "provider": provider,
            "access_method": ("subscription CLI"
                              if provider in SUBSCRIPTION_PROVIDERS else "paid HTTP"),
            "requested_model": requested_model,
            "resolved_model": resolved_model,
            "effort": effort,
            "prompt_version": prompt_version,
            "input_sha256": sha256_text(input_text),
            "input_chars": len(input_text or ""),
            "usage": usage or {},
            "duration_ms": duration_ms,
            "cash_cost_usd": round(float(cash_cost_usd or 0.0), 6),
            "openrouter_used": bool(openrouter_used),
            "error_code": error_code,
            "error_text": (error_text or "")[:400] or None,
            "retry_of": retry_of,
        }
        if extra:
            row.update(extra)
        with self.calls_path.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
        self._rows.append(row)
        return row

    # ── cells ────────────────────────────────────────────────────────────────
    def cell_path(self, cell: str) -> pathlib.Path:
        safe = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in cell)
        return self.cells_dir / ("%s.json" % safe)

    def done(self, cell: str) -> bool:
        return self.cell_path(cell).exists()

    def load_cell(self, cell: str):
        p = self.cell_path(cell)
        return json.loads(p.read_text()) if p.exists() else None

    def save_cell(self, cell: str, payload: dict) -> pathlib.Path:
        """Persist a completed cell BEFORE the next one starts (section 7)."""
        p = self.cell_path(cell)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        os.replace(tmp, p)
        return p

    # ── checkpoint ───────────────────────────────────────────────────────────
    def write_checkpoint(self, *, worktree: str, branch: str, commit: str,
                         models: dict, planned_cells: list, resume_command: str,
                         notes: str = "") -> pathlib.Path:
        completed = sorted(p.stem for p in self.cells_dir.glob("*.json"))
        done = set(completed)
        payload = {
            "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "worktree": worktree,
            "branch": branch,
            "commit": commit,
            "frozen_model_configurations": models,
            "completed_cells": completed,
            "remaining_cells": [c for c in planned_cells if c not in done],
            "budget": self.summary(),
            "resume_command": resume_command,
            "notes": notes,
        }
        tmp = self.checkpoint_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=1))
        os.replace(tmp, self.checkpoint_path)
        return self.checkpoint_path
