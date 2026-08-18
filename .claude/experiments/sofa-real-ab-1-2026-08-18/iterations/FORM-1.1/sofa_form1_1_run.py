#!/usr/bin/env python3
"""
sofa_form1_1_run.py — TEMP-WORKTREE-ONLY. Generates ONE Sofa FORM-1.1
article from the frozen Edinburgh commission. Same writer model/params as
all prior Edinburgh runs: openrouter/claude-opus-4.8 via CLIProxy,
max_tokens=5000, timeout=180, no_think=False, no temperature override.
No new Fable call, no Discovery model call. Exactly one writer call.
"""
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT_REAL = Path("/tmp/cripminds-sofa-real-test-1")
sys.path.insert(0, str(REPO_ROOT_REAL / "automation"))

CASE_DIR = REPO_ROOT_REAL / ".claude/experiments/sofa-real-ab-1-2026-08-18"
FORM11_DIR = REPO_ROOT_REAL / ".claude/experiments/sofa-form1-1-2026-08-18"

WRITER_MODEL = "openrouter/claude-opus-4.8"
WRITER_MAX_TOKENS = 5000
WRITER_TIMEOUT = 180


def main():
    from production_orchestrator import ProductionOrchestrator
    from orchestrator.config import CLIPROXY_URL, CLIPROXY_KEY
    from orchestrator.sofa_discovery_shadow_form1_1 import build_form1_1_packet, run_form1_1_writer

    commission_brief = json.loads((CASE_DIR / "commission-brief.json").read_text())
    evidence_packet = json.loads((CASE_DIR / "evidence-packet.json").read_text())
    source_text = (CASE_DIR / "source-snapshot.txt").read_text()
    evidence_packet["source_text"] = source_text

    FORM11_DIR.mkdir(parents=True, exist_ok=True)

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

        packet = build_form1_1_packet(commission_brief, evidence_packet)

        resolved = {}

        def _writer_call(system, user):
            text, actual_model = orch._call_openai_compat_api(
                CLIPROXY_URL, CLIPROXY_KEY, system, user,
                model=WRITER_MODEL, max_tokens=WRITER_MAX_TOKENS, timeout=WRITER_TIMEOUT,
                no_think=False, return_model=True,
            )
            resolved["writer_requested"] = WRITER_MODEL
            resolved["writer_actual"] = actual_model
            return text

        article_text = run_form1_1_writer(packet, source_text, _writer_call)

        (FORM11_DIR / "form1-1-packet.json").write_text(json.dumps(packet, indent=2))
        (FORM11_DIR / "sofa-form1-1.md").write_text(article_text)

        print(json.dumps({
            "ok": True,
            "resolved_models": resolved,
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
