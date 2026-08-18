#!/usr/bin/env python3
"""discovery_eval_b3.py — internal-only post-writer discovery evaluation for Sofa B.3."""
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT_REAL = Path("/tmp/cripminds-sofa-real-test-1")
sys.path.insert(0, str(REPO_ROOT_REAL / "automation"))

CASE_DIR = REPO_ROOT_REAL / ".claude/experiments/sofa-real-ab-1-2026-08-18"
B4_DIR = REPO_ROOT_REAL / ".claude/experiments/sofa-b4-2026-08-18"


def main():
    from production_orchestrator import ProductionOrchestrator
    from orchestrator.sofa_discovery_shadow_b3 import run_discovery_eval

    commission_brief = json.loads((CASE_DIR / "commission-brief.json").read_text())
    hidden_mechanism = commission_brief["hidden_mechanism"]
    source_text = (CASE_DIR / "source-snapshot.txt").read_text()
    article_text = (B4_DIR / "sofa-b4.md").read_text()

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

        def _eval_call(system, user):
            return orch._call_editorial_model(system, user, max_tokens=800, timeout=90)

        result = run_discovery_eval(hidden_mechanism, source_text, article_text, _eval_call)
        (B4_DIR / "b4-discovery-eval.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(json.dumps({"ok": False, "reason": f"{type(e).__name__}: {e}"}))
        sys.exit(1)
