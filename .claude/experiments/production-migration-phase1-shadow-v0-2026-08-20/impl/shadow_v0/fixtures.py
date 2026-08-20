"""
fixtures.py -- adapters that let the runner ingest FROZEN stage outputs.

No model is called. Every payload below is read from an already-committed evidence
root; nothing is invented. Where a fixture predates a stage contract (FORM-1.3 has no
standalone Discovery document), the payload is derived from that experiment's own
frozen Form specification and marked with `provenance: derived_from_frozen_*` so the
artifact never claims more than the evidence supports.
"""
from __future__ import annotations

import json
import pathlib

from . import contracts as C

REPO = pathlib.Path(__file__).resolve().parents[5]   # -> repo root
assert (REPO / ".claude").is_dir(), "repo root resolution failed: %s" % REPO
T2 = REPO / ".claude/experiments/real-article-test-2-2026-08-20"
F13 = REPO / ".claude/experiments/sofa-real-ab-1-2026-08-18/iterations/FORM-1.3"

# Replay uses a fixed timestamp so artifact hashes are reproducible run to run.
REPLAY_AT = "2026-08-20T00:00:00Z"


def _read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


class Test2Fixture:
    """Real Article Test 2 -- RAIB Report 10/2026, Staniforth Road. TRANSFER_PASS."""
    name = "test2-staniforth-road"
    created_at = REPLAY_AT

    def source_snapshot(self):
        text = _read(T2 / "source/source-snapshot.txt")
        return {
            "source_text": text,
            "source_sha256": C.sha256_text(text),
            "provenance": {
                "origin": "frozen_evidence",
                "title": "RAIB Report 10/2026 -- Collision between a tram and two pedestrians "
                         "at Staniforth Road, Sheffield, 22 June 2025",
                "publisher": "Rail Accident Investigation Branch",
                "url": "https://assets.publishing.service.gov.uk/media/"
                       "6a67566bb9e28a4788aa3f61/R102026_260728_Staniforth_Road.pdf",
                "upstream_pdf_sha256": "7b27f78f3a70355126b332aa6dba3b316facc638e842f1761666c50ce8e5603f",
                "retrieved": "2026-08-20",
                "frozen_at": str(T2 / "source/source-snapshot.txt"),
                "frozen_commit": "2dd9a86",
            },
            "words": len(text.split()),
        }

    def discovery(self):
        return {
            "dominant_reading": "Two teenagers ran into the path of a tram without looking; the "
                                "driver probably did not sound the bell; the signage was not effective.",
            "disturbance": "The report states safety rests on 'observing or hearing approaching "
                           "trams', then documents that hearing there is a discretionary act.",
            "perceptual_instrument": "A deafness-derived way of perceiving treats hearing as a "
                                     "channel, not an ambient guarantee: not hearing something is "
                                     "not evidence that it is not there.",
            "what_becomes_knowable": "The crossing's safety rests on a channel whose silence carries "
                                     "no information, and every remedy in twenty years has been "
                                     "addressed to the act rather than to the channel.",
            "grounding_boundaries": _read(T2 / "GROUNDING-BOUNDARIES.md"),
            "provenance": {"document": "DISCOVERY.md", "frozen_commit": "2dd9a86",
                           "document_sha256": C.sha256_text(_read(T2 / "DISCOVERY.md"))},
        }

    def article_form(self):
        return {
            "route": [
                "The premise: the crossing as the report describes it, closing on the two channels named.",
                "Take the second channel apart using only the report's facts. Let the facts narrow.",
                "The accident, plainly and chronologically, in seconds; then the two recorder findings.",
                "Resistance then accumulation: the prior cases where a warning WAS given; then the rest; then the twenty-year remedy line.",
                "Arrive, and stop there.",
            ],
            "arrival": "Looking is a property of the crossing; hearing is a message with a sender. "
                       "A channel almost always silent, and almost always silent truthfully, teaches "
                       "the people who use it that silence is information.",
            "burden": "The argument is carried by the report's facts in sequence. No remedy, no second "
                      "arrival, no disability example, no persona voice, third person.",
            "motion": "narrows -> accumulates -> recurs",
            "target_words": [900, 1200],
            "provenance": {"document": "ARTICLE-FORM.md", "frozen_commit": "2dd9a86",
                           "document_sha256": C.sha256_text(_read(T2 / "ARTICLE-FORM.md"))},
        }

    def writer_input(self):
        text = _read(T2 / "writer-prompt.txt")
        return {"prompt_text": text, "prompt_sha256": C.sha256_text(text),
                "renderer": "render_writer_prompt.py (deterministic)",
                "instruction_surface_chars": len(text) - len(_read(T2 / "source/source-snapshot.txt"))}

    def writer_output(self):
        text = _read(T2 / "run/article.md")
        return {"article_text": text, "article_sha256": C.sha256_text(text),
                "provider_status": "ok",
                "model": "claude-opus-5[1m]",
                "route": "LOCAL_CLAUDE_SUBSCRIPTION",
                "writer_calls": 1, "words": len(text.split())}

    def grounding_findings(self):
        return {
            "status": "settled",
            "findings": [
                {"id": "F1", "classification": "TRUE_UNSUPPORTED",
                 "summary": "'Nine years later' -- writer-computed elapsed interval absent from the source "
                            "and wrong against its own 2016 anchor."},
                {"id": "F2", "classification": "TRUE_UNSUPPORTED",
                 "summary": "'none with a tram on the track' -- widens the source's narrower "
                            "'never encountered a tram while crossing'."},
                {"id": "F3", "classification": "TRUE_UNCERTAIN",
                 "summary": "'the operator' -- the 2017 recommendation was addressed to Stagecoach Supertram."},
                {"id": "F4", "classification": "LEGITIMATE_INTERPRETATION", "summary": "'Its ordinary state is silence.'"},
                {"id": "F5", "classification": "LEGITIMATE_INTERPRETATION", "summary": "looking as a property of the crossing"},
                {"id": "F6", "classification": "LEGITIMATE_INTERPRETATION", "summary": "'the silence had been true'"},
                {"id": "F7", "classification": "LEGITIMATE_INTERPRETATION", "summary": "the closing claim about what such a channel teaches"},
            ],
            "uncertain_adjudicated": True,
            "uncertain_adjudication_note": "F3 was explicitly adjudicated no-patch: repairing it would "
                                           "require naming entities the article deliberately does not name.",
            "qualifiers_preserved": True,
            "gold_v2_1_used_as_detector_input": False,
            "provenance": {"document": "run/GROUNDING-AUDIT.md", "frozen_commit": "8741804",
                           "document_sha256": C.sha256_text(_read(T2 / "run/GROUNDING-AUDIT.md"))},
        }

    def grounding_repair(self):
        patches = json.loads(_read(T2 / "run/patches.json"))
        text = _read(T2 / "run/article-patched.md")
        return {
            "mode": "patch_only",
            "patches": [{"finding_id": p["finding"], "id": p["id"], "rationale": p["rationale"]}
                        for p in patches["patches"]],
            "article_text": text,
            "article_sha256": C.sha256_text(text),
            "verification": {"residual": 0, "introduced": 0, "unrelated_edits": 0,
                             "paragraphs_touched": 2, "paragraphs_total": 16,
                             "movement_preserved": True, "voice_preserved": True,
                             "arrival_preserved": True},
            "provenance": {"document": "run/patches.json", "frozen_commit": "8741804"},
        }


class Form13Fixture:
    """Edinburgh FORM-1.3. Grounding audit status FAIL, 2 unsupported, no repair
    performed -- exercises the HOLD path."""
    name = "form1-3-edinburgh"
    created_at = REPLAY_AT

    def __init__(self):
        self._audit = json.loads(_read(F13 / "form1-3-grounding-audit.json"))

    def source_snapshot(self):
        text = _read(F13 / "form1-3-source-snapshot.txt")
        return {
            "source_text": text,
            "source_sha256": C.sha256_text(text),
            "provenance": {
                "origin": "frozen_evidence",
                "title": "Guardian -- Edinburgh art festival review, 2026-08-14",
                "frozen_at": str(F13 / "form1-3-source-snapshot.txt"),
                "frozen_commit": "7248c61",
                "note": "This source hash is byte-identical to production draft "
                        "'sniff-it-out-follow-your-nose-whatever-your-legs-can' "
                        "(article_plans.source_hash), per the Phase-0 fixture analysis.",
            },
            "words": len(text.split()),
        }

    def discovery(self):
        return {
            "dominant_reading": "A festival review celebrating hidden stories and undiscovered artists.",
            "disturbance": "The review's language of discovery describes the visitor's present encounter, "
                           "while some of the work discussed had remained unshown in its maker's lifetime.",
            "perceptual_instrument": "A disability-derived reading of visibility and who gets seen when.",
            "what_becomes_knowable": "Discovery names the visitor's encounter, not the work's history.",
            "grounding_boundaries": "The source does not say why George or Walter went unseen, how their "
                                    "work came to be shown, or their wishes/capacity regarding exhibition.",
            "provenance": {"origin": "derived_from_frozen_form_spec",
                           "document": "form1-3-writer-system.txt",
                           "note": "FORM-1.3 predates the standalone DISCOVERY artifact contract; this "
                                   "payload is derived from that experiment's own frozen Form "
                                   "specification and its stated grounding boundaries, not invented.",
                           "document_sha256": C.sha256_text(_read(F13 / "form1-3-writer-system.txt"))},
        }

    def article_form(self):
        return {
            "route": [
                "Begin with the reviewer's description of moving through the festival.",
                "Then the facts about the two artists, together, with a plain neutral transition.",
                "Then the reviewer's stated conviction, pressing while the reading is still forming.",
                "Then return to the reviewer's language of discovery and set it beside those facts.",
                "Arrive at the distinction, and stop there.",
            ],
            "arrival": "The review uses discovery for the visitor's present encounter with previously "
                       "unknown work, while some of that work had remained unshown during its maker's lifetime.",
            "burden": "550-700 words, third person, no invented scenes or biography, arrival is terminal.",
            "motion": "encounter -> facts -> countervoice -> semantic narrowing -> distinction",
            "target_words": [550, 700],
            "provenance": {"document": "form1-3-writer-system.txt", "frozen_commit": "7248c61",
                           "document_sha256": C.sha256_text(_read(F13 / "form1-3-writer-system.txt"))},
        }

    def writer_input(self):
        text = _read(F13 / "form1-3-writer-prompt.txt")
        return {"prompt_text": text, "prompt_sha256": C.sha256_text(text),
                "renderer": "sofa_form1_3_run.py (frozen)"}

    def writer_output(self):
        text = _read(F13 / "form1-3-article.md")
        return {"article_text": text, "article_sha256": C.sha256_text(text),
                "provider_status": "ok", "words": self._audit.get("word_count")}

    def grounding_findings(self):
        findings = []
        for i, c in enumerate(self._audit.get("claims", []), start=1):
            cls = {"UNSUPPORTED": "TRUE_UNSUPPORTED",
                   "UNCERTAIN": "TRUE_UNCERTAIN"}.get(c["verdict"], "LEGITIMATE_INTERPRETATION")
            findings.append({"id": "C%d" % i, "classification": cls,
                             "summary": c["claim"][:160], "source_verdict": c["verdict"]})
        return {
            "status": "settled",
            "findings": findings,
            "upstream_status": self._audit.get("status"),
            "upstream_unsupported_count": self._audit.get("unsupported_count"),
            "gold_v2_1_used_as_detector_input": False,
            "provenance": {"document": "form1-3-grounding-audit.json", "frozen_commit": "7248c61",
                           "document_sha256": C.sha256_text(_read(F13 / "form1-3-grounding-audit.json"))},
        }

    def grounding_repair(self):
        # No repair was performed for FORM-1.3. Returning None is honest: the
        # unsupported findings therefore remain unresolved and the decision must HOLD.
        return None
