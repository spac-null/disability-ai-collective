#!/usr/bin/env python3
"""audit_b3.py — grounding audit for Sofa B.3, same discipline as B.1/B.2."""
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
    from orchestrator.sofa_discovery_shadow import run_shadow_grounding_audit, grounding_audit_status

    source_text = (CASE_DIR / "source-snapshot.txt").read_text()
    article_text = (B4_DIR / "sofa-b4.md").read_text()

    # B.3 has no packet with hidden_mechanism/known_gaps (by design, the
    # writer never sees those) -- pass a minimal stand-in with empty
    # known_gaps, matching the same adapter pattern used for B.1/B.2.
    packet_for_audit = {"hidden_mechanism": {"value": ""}, "known_gaps": []}

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

        audit = run_shadow_grounding_audit(source_text, packet_for_audit, article_text, _audit_call)
        status, reasons = grounding_audit_status(audit)
        unsupported = [c for c in audit["claims"] if c["verdict"] == "UNSUPPORTED"]
        uncertain = [c for c in audit["claims"] if c["verdict"] == "UNCERTAIN"]

        out = {
            "status": status, "status_reasons": reasons,
            "deterministic_flags": audit["deterministic_flags"],
            "claims": audit["claims"],
            "unsupported_count": len(unsupported), "uncertain_count": len(uncertain),
            "word_count": len(article_text.split()),
        }
        (B4_DIR / "sofa-b4-grounding-audit.json").write_text(json.dumps(out, indent=2))
        print(json.dumps({
            "status": status, "unsupported_count": len(unsupported),
            "uncertain_count": len(uncertain), "total_claims": len(audit["claims"]),
            "word_count": len(article_text.split()),
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
