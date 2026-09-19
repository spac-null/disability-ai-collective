#!/usr/bin/env python3
"""
freeze_prompts.py -- record the exact prompts before the held-out cases are generated.

Section 16: "Evaluate the development cases to test the harness. Then freeze prompts
before generating/evaluating the held-out cases." This writes a hash of every prompt
surface the pilot uses, so a later claim that the held-out cases ran on the same prompts
as the development cases can be checked rather than asserted -- and so that any change
made after this point is visible as a hash mismatch instead of a memory.

Run AFTER the development split is complete and BEFORE the held-out split starts.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from evidence_to_draft_pilot import guarded_editor as GE           # noqa: E402
from evidence_to_draft_pilot import judge as JG                    # noqa: E402
from evidence_to_draft_pilot import planner as PL                  # noqa: E402
from evidence_to_draft_pilot import source_reading as SR           # noqa: E402

ROOT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                    "evidence-to-draft-pilot")


def h(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def main():
    payload = {
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "why": "Section 16: prompts are frozen after the development split and before "
               "any held-out case is generated or evaluated.",
        "prompts": {
            "guarded_editor": {"version": GE.PROMPT_VERSION,
                               "system_sha256": h(GE.EDITOR_SYSTEM),
                               "max_patches": GE.MAX_PATCHES,
                               "delete_budget_chars": GE.DELETE_BUDGET_CHARS},
            "codex_replanner": {"version": PL.PROMPT_VERSION,
                                "c_contract": PL.C_CONTRACT,
                                "system_sha256": h(PL.REPLANNER_SYSTEM)},
            "blind_review": {"version": JG.PROMPT_VERSION,
                             "system_sha256": h(JG.REVIEW_SYSTEM),
                             "neutral_labels": list(JG.NEUTRAL_LABELS)},
            "source_reading": {"version": SR.PROMPT_VERSION,
                               "system_sha256": h(SR.EXTRACTION_SYSTEM),
                               "per_source_chars": SR.PER_SOURCE_CHARS},
        },
        "writer": "production composition.write_article, unmodified; its prompt is "
                  "derived from the frozen architecture and ledger by "
                  "composition.writer_packet",
        "models": {
            "claude": {"requested": "claude-opus-5",
                       "transport": "claude CLI subscription"},
            "codex": {"requested": "gpt-5.6-luna", "effort": "medium",
                      "transport": "codex CLI subscription",
                      "resolved": "RESOLVED_MODEL_UNDISCLOSED"},
            "gemini": {"requested": SR.GEMINI_MODEL,
                       "transport": "OpenRouter paid credits, subtest only"},
        },
    }
    p = ROOT / "PROMPTS_FROZEN.json"
    p.write_text(json.dumps(payload, indent=1))
    print(json.dumps(payload, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
