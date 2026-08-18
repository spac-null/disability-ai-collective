#!/usr/bin/env python3
"""
sofa_real_ab_1_harness.py — TEMPORARY, worktree-only harness for
"Sofa Real Article Test 1". Lives ONLY in /tmp/cripminds-sofa-real-test-1
(a detached git worktree of the production repo). NEVER copied into the
live production checkout. Does not commit, push, publish, mark any seed
used, or touch the real database — every filesystem path the real
ProductionOrchestrator would use is redirected to a throwaway tmpdir
before any method is called (same _isolate_paths discipline this repo's
own test suite already uses in snapshot_test.py / story_rejection_v1_test.py).

Usage:
  python3 sofa_real_ab_1_harness.py fetch <url> <out_dir>
      Fetches source fresh (read-only network), builds an evidence
      packet, writes source-snapshot.txt + evidence_packet.json.

  python3 sofa_real_ab_1_harness.py commission <evidence_packet.json> <news_title> <out_dir>
      Calls the REAL, current _fable_editorial_brief (Layer 1 + Layer 2)
      fresh against the supplied evidence packet. Writes
      commission-brief.json. No DB writes (isolated paths), no seed
      marked used (this never touches news_seeds/discovery_db at all).

  python3 sofa_real_ab_1_harness.py legacy-prompt <commission-brief.json> <evidence_packet.json> <out_dir>
      Reconstructs the EXACT legacy writer prompt (the persona-voice
      prompt generate.py builds) by calling the real prompt-construction
      code path with every side-effecting method monkeypatched to a safe
      no-op or a pure recorder. Writes legacy-prompt-system.txt,
      legacy-prompt-user.txt (or, if extraction isn't cleanly separable,
      writes a note explaining why and falls back to a byte-faithful
      hand-copy of the real branch, clearly marked).
"""
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent  # worktree root (harness lives directly here)
sys.path.insert(0, str(REPO_ROOT / "automation"))


def _fresh_orch(tmpdir):
    import production_orchestrator as po
    orch = po.ProductionOrchestrator()
    orch.repo_root = Path(tmpdir)
    orch.posts_dir = orch.repo_root / "_posts"
    orch.drafts_dir = orch.repo_root / "_drafts"
    orch.assets_dir = orch.repo_root / "assets"
    orch.discovery_db = orch.repo_root / "disability_findings.db"
    orch.posts_dir.mkdir(parents=True, exist_ok=True)
    orch.drafts_dir.mkdir(parents=True, exist_ok=True)
    orch.assets_dir.mkdir(parents=True, exist_ok=True)
    return orch


def cmd_fetch(url, out_dir):
    from orchestrator.grounding import build_evidence_packet
    _SOURCE_TEXT_MAX_CHARS = 20000  # matches generate.py's real constant exactly
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        orch = _fresh_orch(tmp)
        source_text = orch.get_source_text(url)
        origin = orch.get_source_origin(url)
        original_length = orch.get_source_original_length(url)
    if not source_text:
        print(json.dumps({"ok": False, "reason": "fetch returned no text", "origin": origin}))
        return 1
    packet = build_evidence_packet(
        source_text, source_max_chars=_SOURCE_TEXT_MAX_CHARS, source_origin=origin,
        source_original_length_chars=original_length,
    )
    (out_dir / "source-snapshot.txt").write_text(source_text)
    (out_dir / "evidence_packet.json").write_text(json.dumps(packet, indent=2))
    print(json.dumps({
        "ok": True, "origin": origin, "length": len(source_text),
        "original_length": original_length, "source_hash": packet.get("source_hash"),
    }, indent=2))
    return 0


def cmd_commission(evidence_packet_path, inputs_json_path, out_dir):
    """REVISED (faithfulness fix): inputs_json_path points to a JSON file
    with the REAL production input shape recovered read-only from
    news_seeds + the real rotation-eligible-agents computation, i.e.:
      {"news_title": ..., "news_summary": ..., "disability_angle": ...,
       "current_agent": ..., "eligible_agents": [...]}
    This replaces the earlier version's ("", "", "", None, eligible_agents=None)
    call shape, which did NOT match generate.py's real call site and
    silently omitted the "ELIGIBLE PERSONAS FOR THIS CYCLE ONLY" prompt
    block entirely (that block is only emitted when eligible_agents is not
    None -- see _fable_editorial_brief in llm.py).

    Also captures every RAW model response text seen during this call
    (via a monkeypatch of _call_editorial_model that records-then-
    delegates to the real implementation, unchanged) into
    fable-raw-responses.json -- so the exact pre-validation model output
    is inspectable, distinguishing HARNESS INPUT MISMATCH / MODEL OUTPUT
    SCHEMA FAILURE / MODEL SEMANTICALLY UNSUPPORTED from each other."""
    evidence_packet = json.loads(Path(evidence_packet_path).read_text())
    inputs = json.loads(Path(inputs_json_path).read_text())
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    captured = []
    with tempfile.TemporaryDirectory() as tmp:
        orch = _fresh_orch(tmp)
        _real_call = orch._call_editorial_model

        def _capturing_call(system, user, *a, **kw):
            raw = _real_call(system, user, *a, **kw)
            captured.append({"system_head": system[:200], "user_len": len(user), "raw_response": raw})
            return raw

        orch._call_editorial_model = _capturing_call
        brief = orch._fable_editorial_brief(
            inputs["news_title"], inputs.get("news_summary", ""), inputs.get("disability_angle", ""),
            inputs.get("current_agent"),
            evidence_packet=evidence_packet, eligible_agents=inputs.get("eligible_agents"),
        )
    (out_dir / "fable-raw-responses.json").write_text(json.dumps(captured, indent=2))
    if brief is None:
        print(json.dumps({"ok": False, "reason": "technical failure — Fable call returned None"}))
        return 1
    (out_dir / "commission-brief.json").write_text(json.dumps(brief, indent=2))
    print(json.dumps({
        "ok": True,
        "source_decision": brief.get("source_decision"),
        "has_anchor": bool(brief.get("source_anchor_examined")),
        "has_mechanism": bool(brief.get("hidden_mechanism")),
        "persona": brief.get("persona"),
        "defer_reason_code": brief.get("defer_reason_code"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "fetch":
        sys.exit(cmd_fetch(sys.argv[2], sys.argv[3]))
    elif action == "commission":
        sys.exit(cmd_commission(sys.argv[2], sys.argv[3], sys.argv[4]))
    else:
        print(f"unknown action: {action}", file=sys.stderr)
        sys.exit(2)
