#!/usr/bin/env python3
"""
research_pack_fixture.py -- a valid RESEARCH_PACK for tests, and nothing else.

TEST SUPPORT ONLY. It is not imported by the engine, the orchestrator or any
scheduled path. Research is injected into runner.run() the way the safety bridge
injects its fact check, so contract tests can exercise the pipeline without a
network -- and the pack this returns still has to satisfy the real RESEARCH_PACK
contract, verbatim excerpts included, so a stub cannot smuggle through anything a
live pack could not.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import contracts as C                     # noqa: E402


def stub_pack(_provider, *, anchor, now_iso, **_kw):
    """A minimal ARTICLE-sufficient pack, injected instead of live research.

    Research is injected here for the same reason the safety bridge injects its fact
    check: the contract tests must exercise the pipeline without a network. The pack
    itself still has to satisfy the real RESEARCH_PACK contract -- verbatim excerpts
    included -- so a stub cannot smuggle through anything a live pack could not.
    """
    supporting = ("The 2019 inspection found the audible warning inoperative for eleven "
                  "weeks. The operator replaced the unit in March 2020.")
    return {
        "subject": "an accessible crossing", "questions": [], "queries": ["crossing audit"],
        "candidates_considered": ["https://audit.example/report"],
        "anchor_kind": "report", "anchor_subject_words": 40, "narrower_subject": "",
        "sources": [
            {"source_id": "S0", "role": "ANCHOR", "url": anchor["url"],
             "canonical_url": "", "publisher": "example.org", "title": "",
             "accessed_at": now_iso, "fetch_status": "ok",
             "sha256": C.sha256_text(anchor["text"]), "content_length": len(anchor["text"]),
             "relation": "anchor", "duplicate_cluster": 0, "why_relevant": "anchor source",
             "text": anchor["text"], "excerpts": [], "excerpts_dropped": []},
            {"source_id": "S1", "role": "PRIMARY", "url": "https://audit.example/report",
             "canonical_url": "", "publisher": "audit.example", "title": "Inspection",
             "accessed_at": now_iso, "fetch_status": "ok",
             "sha256": C.sha256_text(supporting), "content_length": len(supporting),
             "relation": "extends", "duplicate_cluster": 1,
             "why_relevant": "first-party inspection record",
             "text": supporting,
             "excerpts": ["The 2019 inspection found the audible warning inoperative for "
                          "eleven weeks."], "excerpts_dropped": []},
            {"source_id": "S2", "role": "INDEPENDENT", "url": "https://press.example/story",
             "canonical_url": "", "publisher": "press.example", "title": "Report",
             "accessed_at": now_iso, "fetch_status": "ok",
             "sha256": C.sha256_text("Residents told the paper the crossing had been "
                                     "unusable since the winter."),
             "content_length": 74, "relation": "corroborates", "duplicate_cluster": 2,
             "why_relevant": "independent reporting",
             "text": "Residents told the paper the crossing had been unusable since the winter.",
             "excerpts": ["Residents told the paper the crossing had been unusable since "
                          "the winter."], "excerpts_dropped": []},
        ],
        "coverage": {"fetched_ok": 2, "fetch_failures": [],
                     "roles_present": ["ANCHOR", "INDEPENDENT", "PRIMARY"],
                     "distinct_publishers": 3, "duplicate_clusters": 3,
                     "independent_clusters": 2, "subject_relevant_words": 500},
        "sufficiency": {"verdict": "ARTICLE", "reasons": ["stub"], "what_is_missing": []},
        "pack_sha256": "stub",
    }
