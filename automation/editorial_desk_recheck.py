"""Factual re-check of an editorial rewrite. Two gates, in order, both required.

THE ONE MODULE IN THE DESK THAT MAY IMPORT THE COMPOSITION STAGES, and it imports them
only to CALL them. It defines no prompt, copies no rule text, and changes no stage. The
other desk modules are asserted never to import composition at all; this one is the
single, named exception, so the boundary stays visible.

WHY TWO GATES AND NOT ONE.

  A. SEMANTIC DELTA -- continuity.validate_semantic_delta(parent, child)
     Deterministic, offline, free. Answers "did editing ADD factual surface?" across
     numbers, entities, sensory, spatial, scene, and relation classes. This is what
     catches "No door opening at two in the morning. No torch." and "on the same wall".

  B. GROUNDING -- composition.ground_candidate over the frozen evidence
     One model call. Answers "are the resulting claims SUPPORTED?" -- a different
     question, and the reason A alone is not enough.

A rewrite can create a new unsupported meaning using only words already on the page.
The 2026-09-27 article is the proof: "Before it was a number, it was that" introduces
no entity, no number and no scene, and quietly rebuilds the very join -- this woman's
refusal being what the 42% is made of -- that had been removed from three surfaces that
same morning. Semantic delta would pass it. Grounding is what asks whether it is true.

So B runs even when A is clean, and either failing blocks.

FAIL CLOSED EVERYWHERE. A missing artifact, an unreadable ledger, an unavailable
provider, any exception at all: the version is NOT_CHECKED, which is a block. Nothing
here can clear a rewrite by being unable to test it.
"""
from __future__ import annotations

import pathlib

import editorial_desk as DESK

CLEARED = "CLEARED"
BLOCKED_ADDED_MATERIAL = "BLOCKED_ADDED_MATERIAL"
BLOCKED_UNSUPPORTED = "BLOCKED_UNSUPPORTED"
NOT_CHECKED = "NOT_CHECKED"

# Everything ground_candidate needs from the retained run. Absent any of them, the
# rewrite cannot be grounded and therefore cannot be cleared.
GROUNDING_ARTIFACTS = ("SOURCE_SNAPSHOT.json", "RESEARCH_PACK.json",
                       "ARCHITECTURE.json", "WRITER_PACKET.json")


def semantic_delta_errors(parent_text: str, child_text: str) -> list:
    """Gate A, on its own, so it is testable without a provider or a run directory."""
    from new_engine_v1 import continuity as CE
    return CE.validate_semantic_delta(parent_text or "", child_text or "")


def check(run_dir, parent_text: str, child_text: str, *, package: dict | None = None,
          provider=None) -> dict:
    """Both gates over the exact rewritten bytes. Returns a verdict, never raises."""
    out = {"status": NOT_CHECKED, "cleared": False, "delta_errors": [],
           "grounding_status": "", "grounding_blocking": [], "reason": ""}

    try:
        out["delta_errors"] = semantic_delta_errors(parent_text, child_text)
    except Exception as e:                                            # noqa: BLE001
        out["reason"] = "semantic delta failed (%s)" % type(e).__name__
        return out
    if out["delta_errors"]:
        out["status"] = BLOCKED_ADDED_MATERIAL
        out["reason"] = "; ".join(out["delta_errors"])[:400]
        return out

    run_dir = pathlib.Path(run_dir)
    missing = [n for n in GROUNDING_ARTIFACTS if not (run_dir / n).is_file()]
    if missing:
        out["reason"] = ("the evidence this article was written from was not retained "
                         "(%s), so the rewrite cannot be grounded" % ", ".join(missing))
        return out

    try:
        from new_engine_v1 import composition as CP
        import claude_cli_provider as CCP
        snap = DESK.artifact(run_dir, "SOURCE_SNAPSHOT.json")
        pack = DESK.artifact(run_dir, "RESEARCH_PACK.json")
        arch = DESK.artifact(run_dir, "ARCHITECTURE.json")
        packet = DESK.artifact(run_dir, "WRITER_PACKET.json")
        P = CP.composition_provider(provider or CCP.ClaudeCLIProvider())
        bundle = CP.bundle_text(child_text, package)
        g = CP.ground_candidate(P, bundle, snap.get("source_text", ""),
                                snap.get("source_sha256", ""), pack, arch, packet)
    except Exception as e:                                            # noqa: BLE001
        out["reason"] = "grounding unavailable (%s: %s)" % (type(e).__name__,
                                                            str(e)[:160])
        return out

    out["grounding_status"] = g.get("status", "")
    blocking = g.get("blocking") or []
    out["grounding_blocking"] = [
        (b.get("quote") if isinstance(b, dict) else str(b)) for b in blocking][:6]
    if out["grounding_status"] == "PASS" and not blocking:
        out["status"] = CLEARED
        out["cleared"] = True
        out["reason"] = "semantic delta clean; grounding PASS"
    else:
        out["status"] = BLOCKED_UNSUPPORTED
        out["reason"] = ("grounding %s with %d blocking finding(s)"
                         % (out["grounding_status"] or "unavailable", len(blocking)))
    return out
