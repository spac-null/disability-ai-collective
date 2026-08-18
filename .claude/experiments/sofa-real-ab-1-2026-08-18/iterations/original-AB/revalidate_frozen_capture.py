#!/usr/bin/env python3
"""
revalidate_frozen_capture.py — TEMP-WORKTREE-ONLY, one-shot offline
revalidation of an already-captured real Fable response (Sofa Real Article
Test 1 continuation: "freeze an existing real commission").

Does NOT call Fable again. The captured raw_response text from
/tmp/sofa-real-1-out-faithful-replay2/fable-raw-responses.json is injected
verbatim in place of a real Fable call (by monkeypatching
_call_editorial_model to intercept ONLY calls whose system prompt matches
the Fable-editorial-brief's system prompt -- recognized by its literal
opening text -- and return the frozen text unmodified). Any OTHER call
made from inside _fable_editorial_brief (specifically
_verify_commission_mechanism_support, the V1.1 semantic entailment gate,
whose system prompt starts with "You are a CripMinds mechanism-support
verifier") is NOT intercepted and is allowed to proceed as a real, live,
narrow (max_tokens=20) call -- required by the task to prove the frozen
commission survives the CURRENT full validation pipeline, not just the
already-diagnosed deterministic anchor check.

No commission object is edited. No normalization beyond
recover_editorial_json's own already-tested logic (which won't even
trigger here, since the frozen text parses directly).
"""
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "automation"))

FROZEN_CAPTURE_DIR = "/tmp/sofa-real-1-out-faithful-replay2"
EVIDENCE_PACKET_PATH = "/tmp/sofa-real-1-out/evidence_packet.json"
INPUTS_PATH = "/tmp/sofa-real-1-out/faithful-inputs.json"

_FABLE_BRIEF_SYSTEM_MARKER = "You are the editorial director of Crip Minds"


def main():
    from production_orchestrator import ProductionOrchestrator

    frozen_raw = json.loads(
        Path(FROZEN_CAPTURE_DIR, "fable-raw-responses.json").read_text()
    )[0]["raw_response"]
    evidence_packet = json.loads(Path(EVIDENCE_PACKET_PATH).read_text())
    inputs = json.loads(Path(INPUTS_PATH).read_text())

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

        _real_call = orch._call_editorial_model
        call_log = []

        def _intercepting_call(system, user, *a, **kw):
            if system.startswith(_FABLE_BRIEF_SYSTEM_MARKER):
                call_log.append({"call": "fable_editorial_brief", "intercepted": True,
                                  "live_call_made": False})
                return frozen_raw
            # Any other call (the mechanism-support verifier) is real and live.
            result = _real_call(system, user, *a, **kw)
            call_log.append({"call": "other (e.g. mechanism-support verifier)",
                              "intercepted": False, "live_call_made": True,
                              "system_head": system[:80], "raw_result": result})
            return result

        orch._call_editorial_model = _intercepting_call
        brief = orch._fable_editorial_brief(
            inputs["news_title"], inputs.get("news_summary", ""), inputs.get("disability_angle", ""),
            inputs.get("current_agent"),
            evidence_packet=evidence_packet, eligible_agents=inputs.get("eligible_agents"),
        )
        log_path = Path(tmp) / "automation.log"
        log_text = log_path.read_text() if log_path.exists() else ""

    print(json.dumps({
        "capture_file": f"{FROZEN_CAPTURE_DIR}/fable-raw-responses.json",
        "call_log": call_log,
        "final_brief": brief,
        "automation_log": log_text,
    }, indent=2))


if __name__ == "__main__":
    main()
