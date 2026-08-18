#!/usr/bin/env python3
"""
legacy_shadow_run.py — TEMP-WORKTREE-ONLY. Produces the LEGACY SHADOW
article for Sofa Real Article Test 1's A/B, using the real, unmodified
production writer path (_run_production_automation_locked in generate.py)
against the FROZEN commission from this same experiment.

Does NOT call Fable again (the frozen commission-brief is injected in
place of a real _fable_editorial_brief call). Makes exactly ONE real
writer call (the production call_llm_via_openclaw_session, whose real
PROVIDERS[0] is Claude Opus 4.8 via CLIProxy, max_tokens=5000, timeout=180
-- unmodified, not reimplemented).

Isolation:
  - repo_root points at a throwaway tmpdir. _posts/_drafts/assets are
    copied (not symlinked) from the real worktree checkout so title-
    freshness/recent-opening/theme-diversity nudges see real history,
    but every write this run could make lands in the disposable copy.
  - Every DB/discovery/news-seed lookup is mocked to return the frozen
    commission's own real inputs -- no network fetch, no DB read/write.
  - _fable_editorial_brief is mocked to return the frozen commission
    verbatim -- no new Fable call.
  - _record_cited_theorists and _fable_update_state (persona state
    persistence) are short-circuited: the LATTER is where this run is
    deliberately stopped, immediately after the real draft is finalized
    and BEFORE gate/fact-check/revision/publish/social/images ever run --
    none of those stages execute at all in this run.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT_REAL = Path("/tmp/cripminds-sofa-real-test-1")
sys.path.insert(0, str(REPO_ROOT_REAL / "automation"))

CASE_DIR = REPO_ROOT_REAL / ".claude/experiments/sofa-real-ab-1-2026-08-18"


class _StopAfterDraft(Exception):
    def __init__(self, content, extracted_title, used_provider, actual_model):
        self.content = content
        self.extracted_title = extracted_title
        self.used_provider = used_provider
        self.actual_model = actual_model


def main():
    from production_orchestrator import ProductionOrchestrator

    commission_brief = json.loads((CASE_DIR / "commission-brief.json").read_text())
    faithful_inputs = json.loads((CASE_DIR / "faithful-inputs.json").read_text())
    source_text = (CASE_DIR / "source-snapshot.txt").read_text()
    evidence_packet = json.loads((CASE_DIR / "evidence-packet.json").read_text())

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for d in ("_posts", "_drafts", "assets"):
            src, dst = REPO_ROOT_REAL / d, tmp / d
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                dst.mkdir(parents=True, exist_ok=True)

        orch = ProductionOrchestrator()
        orch.repo_root = tmp
        orch.posts_dir = tmp / "_posts"
        orch.drafts_dir = tmp / "_drafts"
        orch.assets_dir = tmp / "assets"
        orch.discovery_db = tmp / "disability_findings.db"

        news_seed = {
            "relevance_score": 1.0,
            "source_name": "(original publication — name not preserved in this experiment's artifacts)",
            "title": faithful_inputs["news_title"],
            "url": "(source URL not preserved in this experiment's artifacts)",
            "disability_angle": faithful_inputs.get("disability_angle", ""),
            "summary": faithful_inputs.get("news_summary", ""),
            "underlying_article_url": None,
            "themes": ["art", "access"],
            "pub_date": "recently",
        }

        orch.check_for_existing_article_today = lambda: None
        orch.get_news_seed = lambda: dict(news_seed)
        orch.get_discovery_from_database = lambda: None
        orch.get_source_text = lambda *a, **kw: source_text
        orch.get_source_origin = lambda *a, **kw: evidence_packet.get("source_origin", "fetched_article")
        orch.get_source_original_length = lambda *a, **kw: evidence_packet.get("source_original_length_chars")
        orch.get_pool_links = lambda *a, **kw: []
        orch._balance_agent = lambda *a, **kw: "Zen Circuit"
        orch._rotation_eligible_agents = lambda: list(faithful_inputs.get("eligible_agents") or ["Zen Circuit"])
        orch._fable_editorial_brief = lambda *a, **kw: dict(commission_brief)
        orch._record_cited_theorists = lambda *a, **kw: None

        def _stop(agent_name, extracted_title, content):
            raise _StopAfterDraft(content, extracted_title, _captured.get("used_provider"), _captured.get("actual_model"))
        orch._fable_update_state = _stop

        _real_call_llm = orch.call_llm_via_openclaw_session
        _captured = {}

        def _capturing_call_llm(prompt, model_priority=None):
            raw_content, used_provider, actual_model = _real_call_llm(prompt)
            _captured["used_provider"] = used_provider
            _captured["actual_model"] = actual_model
            _captured["prompt_len"] = len(prompt)
            return raw_content, used_provider, actual_model

        orch.call_llm_via_openclaw_session = _capturing_call_llm

        try:
            result = orch._run_production_automation_locked()
            print(json.dumps({"ok": False, "reason": "run completed WITHOUT hitting the intended stop point",
                              "result": result}))
            return 1
        except _StopAfterDraft as stop:
            (CASE_DIR / "legacy-shadow.md").write_text(
                f"# {stop.extracted_title}\n\n{stop.content}\n"
            )
            print(json.dumps({
                "ok": True,
                "title": stop.extracted_title,
                "used_provider": stop.used_provider,
                "actual_model": stop.actual_model,
                "content_len": len(stop.content),
                "word_count": len(stop.content.split()),
                "prompt_len": _captured.get("prompt_len"),
            }, indent=2))
            return 0


if __name__ == "__main__":
    sys.exit(main())
