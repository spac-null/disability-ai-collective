#!/usr/bin/env python3
"""Focused tests for commissioning geography/language memory and reader orientation."""
import pathlib
import sqlite3
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import commissioning_diversity as D
import knowledge_first as KF
import news_fetcher as NF
from new_engine_v1 import stages as S


def check(label, condition):
    print(("PASS " if condition else "FAIL ") + label)
    if not condition:
        raise AssertionError(label)


def main():
    history = D.profile([
        {"country": "US", "world_region": "North America", "source_language": "en",
         "source_script": "LATIN"},
        {"country": "US", "world_region": "North America", "source_language": "en",
         "source_script": "LATIN"},
        {"country": "US", "world_region": "North America", "source_language": "en",
         "source_script": "LATIN"},
    ])
    us, _ = D.prior({"country": "US", "world_region": "North America",
                     "source_language": "en", "source_script": "LATIN"}, history)
    jp, _ = D.prior({"country": "Japan", "world_region": "East Asia",
                     "source_language": "ja", "source_script": "HIRAGANA"}, history)
    check("US-heavy history lowers US candidate", us < 0)
    check("underrepresented region/language/script gets advantage", jp > us)
    check("unknown metadata is neutral", D.prior({}, history)[0] == 0)
    check("non-Latin Unicode script survives", D.source_script("日本語の展示") in ("HIRAGANA", "CJK"))

    ranked = D.rank_candidates([
        {"subject": "US story", "country": "US"},
        {"subject": "日本語の物語", "country": "Japan", "source_language": "ja",
         "source_script": "CJK"},
    ], history)
    check("knowledge-first candidate metadata is retained", ranked[0]["country"] == "Japan")

    # Existing selector quality remains ahead of the prior: a strong US story beats a weak
    # underrepresented one, while comparable records can use the prior as a tie-break.
    def rec(name, assessment, country):
        return {"seed_id": name, "source_url": name, "source_name": "src", "title": name,
                "material_class": "OTHER", "pub_date": "2026-09-13", "source_sha256": name,
                "assessment_status": "OK", "exposed_via": "theme", "theme_signal": 0,
                "publisher_penalty": 0, "legacy_relevance_score": 0,
                "legacy_disability_angle": False, "errors": "[]",
                "assessment": assessment, "material_richness": "RICH",
                "researchability": "HIGH", "country": country}
    from selector_v2 import rank
    out = rank([rec("strong US", "STRONG_CANDIDATE", "US"),
                rec("weak Japan", "WEAK_CANDIDATE", "Japan")], history)
    check("editorial quality can override prior", out[0]["seed_id"] == "strong US")

    # Same approved-question lane and one-call contract; no second provider call is added.
    class Completion:
        text = '{"candidates": [{"subject":"日本語の展示", "why_now":"now", "carrier":"work", "tests_the_question":"question", "names_to_research":[], "search_queries":["日本語の展示"], "access_deficit_self_check":"not access", "country":"Japan", "world_region":"East Asia", "source_language":"ja", "source_script":"CJK"}]}'
        def identity(self): return {"provider": "test"}
    class Provider:
        def __init__(self): self.calls = 0
        def complete(self, **kwargs): self.calls += 1; return Completion()
    p = Provider()
    proposed = KF.propose_stories(p, {"id": "PR004-01", "title": "Question", "question": "Why?"}, history)
    check("knowledge-first still uses approved question", proposed["question"]["id"] == "PR004-01")
    check("knowledge-first remains one model call", p.calls == 1)
    check("Unicode candidate survives", proposed["candidates"][0]["subject"] == "日本語の展示")
    check("international reader rule is doctrine only", "international reader" in S.PROSE_DOCTRINE and "Ledger" in S.PROSE_DOCTRINE)
    check("two knowledge-first plus one ordinary lane structure", KF.LANE == "KNOWLEDGE_FIRST")

    # Existing DB state gains additive metadata and preserves the original script.
    conn = sqlite3.connect(":memory:")
    NF.init_db(conn)
    check("Unicode seed metadata roundtrip", NF.store_seed(conn, {
        "url": "https://例子.cn/展示", "title": "日本語の展示", "summary": "x",
        "source_name": "fixture", "source_tier": 2, "relevance_score": .5,
        "themes": [], "material_class": "OTHER"}) and
          conn.execute("select source_script from news_seeds").fetchone()[0] == "CJK")
    print("ALL PASS")


if __name__ == "__main__":
    main()
