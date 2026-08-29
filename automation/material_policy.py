"""
material_policy.py -- what KIND of material a feed supplies, and how long that kind
stays worth considering.

WHY THIS EXISTS
Everything upstream of the engine ran on one universal clock: ingest anything published
in the last 7 days, consider anything published in the last 3, delete anything unused
after 14. That is the right clock for a news wire and the wrong clock for everything
else. A paper, a report, a museum essay or an archival piece is not less interesting on
its fourth day, and under one 3-day window such a source can only ever be missed --
which is why the low-cadence feeds in the configuration produce nothing that ever
reaches selection.

WHAT THIS IS NOT
It is not a quota system, a ranking input, or a judgement about a publisher. A material
class answers one question -- "can this still be considered?" -- and never "should this
win?". Ranking stays `relevance_score DESC, pub_date DESC`, untouched. Disability-led
provenance is deliberately NOT a class and carries no weight in either direction: a
disability-led news feed is CURRENT_NEWS exactly as any other news feed is.
"""
from __future__ import annotations

CURRENT_NEWS = "CURRENT_NEWS"
ESSAY_OPINION = "ESSAY_OPINION"
RESEARCH_REPORT = "RESEARCH_REPORT"
CULTURE = "CULTURE"
EVERGREEN = "EVERGREEN"
OTHER = "OTHER"

CLASSES = (CURRENT_NEWS, ESSAY_OPINION, RESEARCH_REPORT, CULTURE, EVERGREEN, OTHER)

# ingest_lookback_days : how far back a feed fetch will look at all
# eligibility_days     : how long a stored seed may still be selected
# retention_days       : how long an unused seed is kept
#
# INVARIANT, asserted below and by test: retention > eligibility for every class. A seed
# must never be deleted while its own class still considers it selectable -- a
# RESEARCH_REPORT eligible for 90 days and pruned at 14 would be worse than the universal
# rule it replaces.
POLICY = {
    CURRENT_NEWS:    {"ingest_lookback_days": 7,   "eligibility_days": 3,   "retention_days": 14},
    ESSAY_OPINION:   {"ingest_lookback_days": 30,  "eligibility_days": 30,  "retention_days": 45},
    RESEARCH_REPORT: {"ingest_lookback_days": 90,  "eligibility_days": 90,  "retention_days": 120},
    CULTURE:         {"ingest_lookback_days": 30,  "eligibility_days": 30,  "retention_days": 45},
    EVERGREEN:       {"ingest_lookback_days": 180, "eligibility_days": 180, "retention_days": 210},
    # OTHER is the legacy clock exactly. An unclassified feed, and every historical row
    # written before this existed, behaves precisely as it did before.
    OTHER:           {"ingest_lookback_days": 7,   "eligibility_days": 3,   "retention_days": 14},
}

for _cls, _p in POLICY.items():
    assert _p["retention_days"] > _p["eligibility_days"], _cls

# A per-feed fetch cap. An evergreen feed with a 180-day lookback must not become a
# historical crawler: whatever the window, one fetch takes at most this many items from
# one feed, newest first, and a feed that offers more simply contributes its newest.
MAX_ITEMS_PER_FEED_PER_FETCH = 40


def normalise(material_class) -> str:
    """Anything unknown, missing or malformed is OTHER -- i.e. legacy behaviour."""
    c = (material_class or "").strip().upper()
    return c if c in CLASSES else OTHER


def policy_for(material_class) -> dict:
    return POLICY[normalise(material_class)]


def eligibility_days(material_class) -> int:
    return policy_for(material_class)["eligibility_days"]


def ingest_lookback_days(material_class) -> int:
    return policy_for(material_class)["ingest_lookback_days"]


def retention_days(material_class) -> int:
    return policy_for(material_class)["retention_days"]


def eligibility_cutoffs(now) -> dict:
    """{class: 'YYYY-MM-DD'} -- the oldest pub_date each class still accepts.

    Computed in Python and passed to SQL as parameters, so the eligibility rule is
    readable in one place instead of spread across CASE expressions.
    """
    from datetime import timedelta
    return {c: (now - timedelta(days=POLICY[c]["eligibility_days"])).strftime("%Y-%m-%d")
            for c in CLASSES}
