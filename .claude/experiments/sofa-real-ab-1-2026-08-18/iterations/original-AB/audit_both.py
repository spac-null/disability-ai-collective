#!/usr/bin/env python3
"""
audit_both.py — TEMP-WORKTREE-ONLY. Runs the SAME post-writer grounding
audit (orchestrator.sofa_discovery_shadow.run_shadow_grounding_audit)
against BOTH the Legacy Shadow and Sofa Shadow articles, using the same
source snapshot, the same discovery packet as the shared reference frame
(hidden_mechanism / known_gaps), and the same audit model
(_call_editorial_model's default Fable-first/Opus-fallback chain --
production's own _fable_editorial_review model chain).
"""
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT_REAL = Path("/tmp/cripminds-sofa-real-test-1")
sys.path.insert(0, str(REPO_ROOT_REAL / "automation"))

CASE_DIR = REPO_ROOT_REAL / ".claude/experiments/sofa-real-ab-1-2026-08-18"


def main():
    from production_orchestrator import ProductionOrchestrator
    from orchestrator.sofa_discovery_shadow import (
        run_shadow_grounding_audit, grounding_audit_status,
    )

    packet = json.loads((CASE_DIR / "discovery-packet.json").read_text())
    source_text = (CASE_DIR / "source-snapshot.txt").read_text()
    legacy_text = (CASE_DIR / "legacy-shadow.md").read_text()
    sofa_text = (CASE_DIR / "sofa-shadow.md").read_text()

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

        def _audit_call(system, user):
            return orch._call_editorial_model(system, user, max_tokens=3200, timeout=90)

        results = {}
        for label, text, out_name in [
            ("legacy", legacy_text, "legacy-grounding-audit.json"),
            ("sofa", sofa_text, "sofa-grounding-audit.json"),
        ]:
            audit = run_shadow_grounding_audit(source_text, packet, text, _audit_call)
            status, reasons = grounding_audit_status(audit)
            unsupported = [c for c in audit["claims"] if c["verdict"] == "UNSUPPORTED"]
            uncertain = [c for c in audit["claims"] if c["verdict"] == "UNCERTAIN"]
            out = {
                "status": status,
                "status_reasons": reasons,
                "deterministic_flags": audit["deterministic_flags"],
                "claims": audit["claims"],
                "unsupported_count": len(unsupported),
                "uncertain_count": len(uncertain),
            }
            (CASE_DIR / out_name).write_text(json.dumps(out, indent=2))
            results[label] = {
                "status": status, "unsupported_count": len(unsupported),
                "uncertain_count": len(uncertain), "total_claims": len(audit["claims"]),
            }

        print(json.dumps(results, indent=2))
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(json.dumps({"ok": False, "reason": f"{type(e).__name__}: {e}"}))
        sys.exit(1)
