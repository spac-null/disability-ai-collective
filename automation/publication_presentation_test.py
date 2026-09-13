#!/usr/bin/env python3
"""Focused publication-layer checks for art direction and public sources."""
import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import new_engine_candidate as C  # noqa: E402
import art_director as AD  # noqa: E402


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print("PASS", label)


def main():
    ledger = {"F1": {"evidence_ids": ["S0"]}, "F2": {"evidence_ids": ["S1"]}}
    claims = {"claim_map": [{"fact_ids": ["F1"]}, {"fact_ids": ["F1", "F2"]}]}
    pack = {"sources": [
        {"source_id": "S0", "title": "Used", "publisher": "one", "url": "https://one.test/a"},
        {"source_id": "S1", "title": "Used too", "publisher": "two", "url": "https://two.test/b"},
        {"source_id": "S9", "title": "Unused", "publisher": "nine", "url": "https://nine.test/c"},
        {"source_id": "S0", "title": "Duplicate", "publisher": "one", "url": "https://one.test/a"},
    ]}
    sources = C.public_sources(pack, ledger, claims)
    check("final-used sources only", [s["title"] for s in sources] == ["Used", "Used too"])
    check("duplicate source emitted once", len(sources) == 2)
    check("source URL and title preserved", sources[0]["url"] == "https://one.test/a")
    check("no internal metadata leaks", not any("F1" in str(s) or "ledger" in str(s) for s in sources))
    check("missing provenance fails safely", C.public_sources(pack, {}, claims) == [])

    arch = {"article_type": "essay", "beats": [
        {"beat_id": "b1", "concrete_carrier": "a red door and a paper notice"},
        {"beat_id": "b2", "concrete_carrier": "a hand sorting marked envelopes"},
        {"beat_id": "b3", "concrete_carrier": "a room with a long table"},
    ], "story_spine": "The notice changes who can enter."}
    digest = AD.architecture_digest(arch)
    check("art brief receives architecture carriers", len(digest["beats"]) == 3)
    brief = {"images": [
        {"function": "ESTABLISH_PLACE", "register": "MATERIAL_EDITORIAL",
         "placement": "HERO", "editorial_purpose": "establish the entry",
         "factual_anchors": ["red door"], "composition_note": "door at left",
         "alt_text": "A red door beside a paper notice"},
        {"function": "SHOW_MECHANISM", "register": "SPATIAL_DIAGRAMMATIC",
         "placement": "END", "editorial_purpose": "show the sorting action",
         "factual_anchors": ["marked envelopes"], "composition_note": "hands over table",
         "alt_text": "Marked envelopes arranged on a table"},
        {"function": "DIAGRAM", "register": "CONCEPTUAL_SYSTEMIC",
         "placement": "BREATHING", "editorial_purpose": "clarify the room relation",
         "factual_anchors": ["long table"], "composition_note": "table anchors the room",
         "alt_text": "A long table dividing a quiet room"},
    ]}
    prompts = [AD.build_image_prompt(x, "Maya Flux") for x in brief["images"]]
    check("three image roles stay distinct", len(set(prompts)) == 3)

    pub = (HERE / "publish_best.py").read_text()
    resume = (HERE / "publish_retained_fast_lane.py").read_text()
    check("normal and retained routes share publish_candidate", "publish_candidate(path)" in resume and "def publish_candidate" in pub)
    check("art-directed boundary is canonical", "art_direct_for(dest)" in pub and "illustrate_post(dest, brief=ad_brief, arch=ad_arch)" in pub)
    ast.parse(pub)
    ast.parse(resume)
    print("ALL PUBLICATION PRESENTATION TESTS PASS")


if __name__ == "__main__":
    main()
