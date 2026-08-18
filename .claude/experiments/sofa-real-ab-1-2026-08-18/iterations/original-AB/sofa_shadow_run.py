#!/usr/bin/env python3
"""
sofa_shadow_run.py — TEMP-WORKTREE-ONLY. Produces the SOFA SHADOW article
for Sofa Real Article Test 1's A/B, using the frozen commission from this
same experiment, run through the existing (already-built, already-tested)
orchestrator.sofa_discovery_shadow pipeline: Discovery -> generic writer
-> grounding audit.

Does NOT call Fable again for the commission itself (the frozen brief is
loaded from disk, never regenerated). Discovery and grounding-audit roles
use the real _call_editorial_model (Fable-first, Opus-fallback -- the same
chain production's own _fable_editorial_review uses). The WRITER role is
pinned to the EXACT same model/params Legacy's real writer call used
(openrouter/claude-opus-4.8 via CLIProxy, max_tokens=5000, timeout=180,
no_think=False, no temperature override) -- verified against
legacy-shadow.json's own recorded actual_model, per the task's explicit
"CRITICAL MODEL CONTROL" requirement.
"""
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT_REAL = Path("/tmp/cripminds-sofa-real-test-1")
sys.path.insert(0, str(REPO_ROOT_REAL / "automation"))

CASE_DIR = REPO_ROOT_REAL / ".claude/experiments/sofa-real-ab-1-2026-08-18"

WRITER_MODEL = "openrouter/claude-opus-4.8"
WRITER_MAX_TOKENS = 5000
WRITER_TIMEOUT = 180


def main():
    from production_orchestrator import ProductionOrchestrator
    from orchestrator.config import CLIPROXY_URL, CLIPROXY_KEY
    from orchestrator.sofa_discovery_shadow import (
        SofaShadowError, run_shadow_discovery, to_writer_context, run_shadow_writer,
        validate_discovery_packet,
    )

    commission_brief = json.loads((CASE_DIR / "commission-brief.json").read_text())
    evidence_packet = json.loads((CASE_DIR / "evidence-packet.json").read_text())
    source_text = (CASE_DIR / "source-snapshot.txt").read_text()

    with tempfile.TemporaryDirectory() as tmp:
        orch = ProductionOrchestrator()
        orch.repo_root = Path(tmp)
        orch.posts_dir = orch.repo_root / "_posts"
        orch.drafts_dir = orch.repo_root / "_drafts"
        orch.assets_dir = orch.repo_root / "assets"
        orch.discovery_db = orch.repo_root / "disability_findings.db"
        orch.posts_dir.mkdir(parents=True, exist_ok=True)
        orch.drafts_dir.mkdir(parents=True, exist_ok=True)
        orch.assets_dir.mkdir(parents=True, exist_ok=True)

        resolved_models = {}

        def _discovery_call(system, user):
            resolved_models["discovery_requested"] = "openrouter/claude-fable-5 (Fable-first chain, _call_editorial_model default)"
            return orch._call_editorial_model(system, user, max_tokens=3200, timeout=90)

        def _writer_call(system, user):
            text, actual_model = orch._call_openai_compat_api(
                CLIPROXY_URL, CLIPROXY_KEY, system, user,
                model=WRITER_MODEL, max_tokens=WRITER_MAX_TOKENS, timeout=WRITER_TIMEOUT,
                no_think=False, return_model=True,
            )
            resolved_models["writer_requested"] = WRITER_MODEL
            resolved_models["writer_actual"] = actual_model
            return text

        def _audit_call(system, user):
            resolved_models["audit_requested"] = "openrouter/claude-fable-5 (Fable-first chain, _call_editorial_model default)"
            return orch._call_editorial_model(system, user, max_tokens=3200, timeout=90)

        packet = run_shadow_discovery(commission_brief, evidence_packet, _discovery_call,
                                       discovery_lens=None)
        ok, errors = validate_discovery_packet(packet)
        if not ok:
            print(json.dumps({"ok": False, "stage": "discovery_packet_validation", "errors": errors}))
            return 1

        writer_context = to_writer_context(packet, source_text)
        article_text = run_shadow_writer(writer_context, _writer_call)

        (CASE_DIR / "discovery-packet.json").write_text(json.dumps(packet, indent=2))
        (CASE_DIR / "sofa-shadow.md").write_text(article_text)

        print(json.dumps({
            "ok": True,
            "resolved_models": resolved_models,
            "word_count": len(article_text.split()),
            "content_len": len(article_text),
        }, indent=2))
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(json.dumps({"ok": False, "reason": f"{type(e).__name__}: {e}"}))
        sys.exit(1)
