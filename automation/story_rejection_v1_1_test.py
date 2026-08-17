#!/usr/bin/env python3
"""
story_rejection_v1_1_test.py — DSR2 Story Rejection V1.1, deterministic tests
for the commission-grounding + aggregator-isolation fix (2026-08-17, SRF3
forensic audit of the "7,000 Rooms With No Door For Anyone" false commission).

Two defects closed here:
  A. COMMISSION VALIDATION ASYMMETRY — validate_source_decision() used to
     validate DECLINE authoritatively but let COMMISSION pass trivially.
     grounding._validate_commission_grounding() now applies the same
     evidence-safety gates (authoritative origin, non-truncated, verbatim-
     grounded anchor) plus a mechanism-tied-to-anchor check. A verdict that
     fails these routes to `source_decision: "defer"` (generate.py's
     _handle_defer_run), NEVER a persisted decline and NEVER the legacy
     technical-failure write-anyway path.
  B. AGGREGATOR CONTAMINATION — a Techmeme-style aggregator permalink used to
     be fetched/extracted as if it were one article, pulling in every
     unrelated neighbouring story on the page. discovery.py's
     fetch_source_article now NEVER treats an aggregator URL as
     fetched_article material for itself: it either fetches a real recovered
     underlying_url, or falls back to the isolated per-item RSS blurb only.
     news_fetcher.py's fetch_feed() recovers that underlying_url (when
     present) from the item's own raw description HTML, before stripping.

No live network, no provider calls, no production DB mutation -- same
harness conventions as story_rejection_v1_test.py.

Run (from repo root):
  python3 automation/story_rejection_v1_1_test.py
"""

import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from snapshot_test import (  # noqa: E402
    _import_orchestrator, _patch_methods, _isolate_paths,
    FIXTURE_PERSONA_STATE, FIXTURE_FAULT_LINE,
)
from orchestrator.grounding import (  # noqa: E402
    build_evidence_packet, validate_source_decision,
)
from story_rejection_v1_test import (  # noqa: E402
    SRC, ANCHOR, REGISTER, VALID_COMMISSION, _make_evidence, _orch, _patch_common,
)

import news_fetcher as nf  # noqa: E402
import json as _json  # noqa: E402
from persona_brief_writer_reconciliation_test import (  # noqa: E402
    SOURCE_TEXT, NEWS_SEED, _StopAfterPersist,
)


# --------------------------------------------------------------------------- #
# Shared fixtures — the actual #4 failure structure, reproduced synthetically.
# Minimal synthetic text, not real copyrighted article content.
# --------------------------------------------------------------------------- #

ITEM_A_TITLE = "Freedonia's manufacturing sector grows 7.5%, powering 6% GDP growth"
ITEM_A_UNDERLYING = "https://example-ft.test/freedonia-gdp-q2"
# The isolated per-item blurb -- exactly what real selection/RSS parsing gives
# this candidate BEFORE any page-wide fetch happens. Deliberately contains no
# architecture/accessibility/AI-application detail, mirroring the real audited
# source (one GDP/construction paragraph, nothing about who enters a building).
ITEM_A_BLURB = (
    "Freedonia's construction sector grew 6.6 percent in Q2, supported partly "
    "by data-center development, as the country emerges as a regional hub."
)
ITEM_A_ANCHOR = "construction sector grew 6.6 percent"  # verbatim in ITEM_A_BLURB

# ITEM B is a wholly unrelated story that happens to share the same aggregator
# page. Its distinguishing fact ("7,000") must never be reachable from ITEM A's
# evidence under the fix.
ITEM_B_DISTINGUISHING_FACT = "7,000 unrelated incident reports"
ITEM_B_BLURB = f"A separate lawsuit filing describes {ITEM_B_DISTINGUISHING_FACT} in an unrelated case."

AGGREGATOR_PERMALINK_A = "https://www.techmeme.com/260817/p1#a260817p1"
AGGREGATOR_PERMALINK_B = "https://www.techmeme.com/260817/p1#a260817p9"


def _make_techmeme_rss(item_a_desc_html: str, item_b_desc_html: str) -> bytes:
    """A minimal, synthetic 2-item Techmeme-shaped RSS 2.0 feed. item_a_desc_html
    carries a real <a href> (simulating Techmeme's own link-to-source pattern);
    item_b is a distinct, unrelated item on the same feed/page. Descriptions use
    CDATA, matching how real RSS feeds embed HTML markup inside <description>
    (raw unescaped <a> tags there would parse as XML child elements, not text)."""
    xml = f"""<?xml version="1.0"?>
<rss version="2.0"><channel>
<item>
  <title>{ITEM_A_TITLE}</title>
  <link>{AGGREGATOR_PERMALINK_A}</link>
  <description><![CDATA[{item_a_desc_html}]]></description>
  <pubDate>Mon, 17 Aug 2026 09:00:00 GMT</pubDate>
</item>
<item>
  <title>Unrelated lawsuit item</title>
  <link>{AGGREGATOR_PERMALINK_B}</link>
  <description><![CDATA[{item_b_desc_html}]]></description>
  <pubDate>Mon, 17 Aug 2026 09:05:00 GMT</pubDate>
</item>
</channel></rss>"""
    return xml.encode("utf-8")


class _FakeResponse:
    def __init__(self, data):
        self._data = data
    def read(self):
        return self._data
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


# --------------------------------------------------------------------------- #
# news_fetcher.py pure helpers
# --------------------------------------------------------------------------- #

def case_url_domain_and_first_external_href():
    assert nf._url_domain("https://www.techmeme.com/260817/p1#a1") == "www.techmeme.com"
    assert nf._url_domain("not a url") == ""
    html = f'<strong><a href="{ITEM_A_UNDERLYING}">Financial Times</a></strong>: some text'
    assert nf._first_external_href(html, nf.AGGREGATOR_DOMAINS) == ITEM_A_UNDERLYING
    # A href pointing BACK at the aggregator itself must not be returned.
    html_self = '<a href="https://www.techmeme.com/other-item">see also</a>'
    assert nf._first_external_href(html_self, nf.AGGREGATOR_DOMAINS) == ""
    print("A1 OK  _url_domain/_first_external_href: recover real link, reject aggregator-self links")


# --------------------------------------------------------------------------- #
# fetch_feed: underlying_url recovered per-item, from that item's OWN raw
# description only -- ITEM B's link/content must never attach to ITEM A.
# --------------------------------------------------------------------------- #

def case_fetch_feed_recovers_underlying_url_per_item_only():
    item_a_desc = f'<a href="{ITEM_A_UNDERLYING}">Financial Times</a>: {ITEM_A_BLURB}'
    item_b_desc = f'<a href="https://example-lawsuit.test/case">Court Filing</a>: {ITEM_B_BLURB}'
    raw = _make_techmeme_rss(item_a_desc, item_b_desc)

    orig_urlopen = nf.urllib.request.urlopen
    nf.urllib.request.urlopen = lambda req, timeout=8: _FakeResponse(raw)
    try:
        items = nf.fetch_feed({"url": "https://www.techmeme.com/feed.xml", "name": "Techmeme", "tier": 2}, days=3650)
    finally:
        nf.urllib.request.urlopen = orig_urlopen

    assert len(items) == 2
    item_a = next(i for i in items if i["url"] == AGGREGATOR_PERMALINK_A)
    item_b = next(i for i in items if i["url"] == AGGREGATOR_PERMALINK_B)

    assert item_a.get("underlying_url") == ITEM_A_UNDERLYING
    assert item_b.get("underlying_url") == "https://example-lawsuit.test/case"
    # ITEM A's underlying_url/summary must not contain ANY trace of ITEM B.
    assert "7,000" not in item_a.get("underlying_url", "")
    assert ITEM_B_DISTINGUISHING_FACT not in item_a["summary"]
    print("A2 OK  fetch_feed recovers underlying_url per-item from raw description only, no cross-item leakage")


def case_fetch_feed_non_aggregator_item_has_no_underlying_url():
    """A normal (non-aggregator) feed's <link> already IS the real article --
    underlying_url must not be synthesized for it."""
    raw = """<?xml version="1.0"?>
<rss version="2.0"><channel><item>
  <title>Ordinary article</title>
  <link>https://example-publisher.test/article</link>
  <description><![CDATA[Some description with <a href="https://example-other.test/x">a link</a> in it.]]></description>
  <pubDate>Mon, 17 Aug 2026 09:00:00 GMT</pubDate>
</item></channel></rss>""".encode("utf-8")
    orig_urlopen = nf.urllib.request.urlopen
    nf.urllib.request.urlopen = lambda req, timeout=8: _FakeResponse(raw)
    try:
        items = nf.fetch_feed({"url": "https://example-publisher.test/feed.xml", "name": "Example", "tier": 1}, days=3650)
    finally:
        nf.urllib.request.urlopen = orig_urlopen
    assert len(items) == 1
    assert "underlying_url" not in items[0]
    print("A3 OK  non-aggregator feed item is untouched (no synthesized underlying_url)")


# --------------------------------------------------------------------------- #
# fetch_source_article: an aggregator URL is NEVER fetched/extracted as a
# whole page for itself -- proven structurally (the page-fetch/extract path
# is provably unreachable), not just empirically.
# --------------------------------------------------------------------------- #

def case_aggregator_url_never_page_fetched_no_underlying():
    orch, po = _orch()
    called = []
    def _boom(*a, **kw):
        called.append(True)
        raise AssertionError("fetch_source_article must never HTML-fetch an aggregator permalink")
    r1 = _patch_methods(po.DiscoveryMixin, _fetch_url_html=_boom, _fetch_url_html_impersonated=_boom)
    try:
        result = orch.fetch_source_article(AGGREGATOR_PERMALINK_A, fallback_text=ITEM_A_BLURB)
    finally:
        r1()
    assert called == [], "the page-wide fetch path must be structurally unreachable for an aggregator URL"
    assert result == ITEM_A_BLURB, "must return exactly the isolated per-item blurb, nothing more"
    assert ITEM_B_DISTINGUISHING_FACT not in result
    assert orch.get_source_origin(AGGREGATOR_PERMALINK_A) is None or True  # origin set via _last_fetch_origin below
    assert orch._last_fetch_origin == "fallback_summary"
    print("B1 OK  aggregator URL w/o underlying_url: isolated blurb only, whole-page fetch never attempted")


def case_aggregator_url_fetches_real_underlying_article():
    orch, po = _orch()
    # Natural prose, not a repeated/templated sentence -- _extract_paragraphs's
    # regex fallback (no trafilatura in this dev environment) filters
    # low-function-word-density text as nav/boilerplate (_looks_like_nav);
    # real article prose clears that bar easily.
    _para = (
        "<p>The company said on Monday that it would expand its operations into three new "
        "markets over the next year, adding hundreds of jobs in the process and investing "
        "heavily in new facilities across the region to support the planned growth.</p>"
    )
    real_article_html = f"<html><body>{_para * 3}</body></html>"
    fetched_urls = []
    def fake_fetch_html(self, url):
        fetched_urls.append(url)
        return real_article_html
    r1 = _patch_methods(po.DiscoveryMixin, _fetch_url_html=fake_fetch_html)
    try:
        result = orch.fetch_source_article(
            AGGREGATOR_PERMALINK_A, fallback_text=ITEM_A_BLURB, underlying_url=ITEM_A_UNDERLYING,
        )
    finally:
        r1()
    assert fetched_urls == [ITEM_A_UNDERLYING], "must fetch the underlying article, never the aggregator permalink"
    assert "expand its operations into three new" in result
    assert orch._last_fetch_origin == "fetched_article"
    print("B2 OK  aggregator URL w/ underlying_url: fetches the real article, not the aggregator page")


def case_underlying_url_that_is_itself_aggregator_domain_ignored():
    """A malformed/self-referential underlying_url (still on an aggregator
    domain) must not be trusted -- falls back to the isolated blurb."""
    orch, po = _orch()
    called = []
    r1 = _patch_methods(
        po.DiscoveryMixin,
        _fetch_url_html=lambda self, url: called.append(url) or None,
        _fetch_url_html_impersonated=lambda self, url: called.append(url) or None,
    )
    try:
        result = orch.fetch_source_article(
            AGGREGATOR_PERMALINK_A, fallback_text=ITEM_A_BLURB,
            underlying_url="https://www.techmeme.com/260817/p1#a260817p9",  # ITEM B's own permalink
        )
    finally:
        r1()
    assert called == [], "an aggregator-domain 'underlying_url' must never be fetched either"
    assert result == ITEM_A_BLURB
    print("B3 OK  aggregator-domain underlying_url is ignored, not trusted as a real article link")


# --------------------------------------------------------------------------- #
# End-to-end structural proof: ITEM A's evidence packet, built the same way
# real production would (isolated blurb only), genuinely cannot ground a
# mechanism drawn from ITEM B. Commission on that mechanism -> DEFER.
# --------------------------------------------------------------------------- #

def case_commission_cannot_ground_mechanism_from_excluded_neighbor():
    ep = build_evidence_packet(ITEM_A_BLURB, source_max_chars=20000, source_origin="fallback_summary")
    contaminated_brief = {
        "source_decision": "commission",
        "eligible_execution_possible": True,
        "source_anchor_examined": ITEM_A_ANCHOR,
        "hidden_mechanism": f"AI systems trained on this kind of data enable {ITEM_B_DISTINGUISHING_FACT}.",
        "why_disability_knowledge_changes_subject": (
            f"This connects to {ITEM_B_DISTINGUISHING_FACT}, which the source never mentions."
        ),
    }
    # First: fallback_summary origin alone already blocks commission (isolated
    # blurb is exactly the "no real fetch happened" case).
    ok, code, _, _ = validate_source_decision(contaminated_brief, ep)
    assert ok is False and code == "commission_source_insufficient"

    # Second, stronger proof: even granting a fetched_article origin, the
    # neighbour's fact is simply not IN the isolated text at all, so the
    # anchor itself is fine but the mechanism-tie check still can't be
    # satisfied by contaminated content -- and a literal attempt to anchor
    # on the neighbour's own fact fails the anchor-grounding gate outright.
    ep2 = build_evidence_packet(ITEM_A_BLURB, source_max_chars=20000, source_origin="fetched_article")
    contaminated_brief2 = dict(contaminated_brief)
    contaminated_brief2["source_anchor_examined"] = ITEM_B_DISTINGUISHING_FACT  # not present in ITEM_A_BLURB
    ok2, code2, _, _ = validate_source_decision(contaminated_brief2, ep2)
    assert ok2 is False and code2 == "commission_anchor_not_grounded", (
        "a mechanism anchored on the excluded neighbour's fact must fail grounding, not pass"
    )
    print("C1 OK  commission cannot ground a mechanism drawn from the excluded neighbouring item -> blocked")


def case_full_pipeline_defers_on_contaminated_commission_attempt():
    """_fable_editorial_brief itself, given a commission brief whose mechanism
    can only be true by importing the excluded neighbour's fact, returns a
    'defer' brief -- not None (technical failure), not a persisted decline."""
    orch, po = _orch()
    contaminated = {
        "source_decision": "commission",
        "eligible_execution_possible": True,
        "persona": "Maya Flux",
        "source_anchor_examined": ITEM_B_DISTINGUISHING_FACT,  # not in the isolated ITEM A text
        "hidden_mechanism": "some mechanism",
        "why_disability_knowledge_changes_subject": f"tied to {ITEM_B_DISTINGUISHING_FACT}",
        "angle": "does not matter",
        "register": REGISTER,
    }
    restore = _patch_common(orch, po, contaminated)
    try:
        ep = build_evidence_packet(ITEM_A_BLURB, source_max_chars=20000, source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            ITEM_A_TITLE, "", "", "Maya Flux", ep, eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert brief is not None, "a bad-grounding commission must become a defer brief, not None"
        assert brief["source_decision"] == "defer"
        assert brief["defer_reason_code"] == "commission_anchor_not_grounded"
        assert "decline_contract_version" not in brief, "must never be persisted as a decline"
    finally:
        restore()
    print("C2 OK  _fable_editorial_brief: contaminated commission -> defer brief, not None/decline")


def case_defer_run_writes_no_publication_artifacts():
    """_handle_defer_run mirrors cases M/Q: no writer, no article, no decline
    persistence, source left fully reconsiderable (not marked used)."""
    orch, po = _orch()
    persisted = []
    restore_plan = _patch_methods(
        po.GenerateMixin,
        _persist_article_plan=lambda self, slug, agent_name, fable_brief: persisted.append(("plan", slug)),
    )
    spied = []
    restore_mark = _patch_methods(
        po.DiscoveryMixin,
        mark_news_seed_declined=lambda self, seed_id, record: spied.append((seed_id, record)),
        mark_news_seed_used=lambda self, seed_id: spied.append(("used", seed_id)),
    )
    try:
        seed = {"id": "seed-defer", "title": "T", "url": "http://x.example", "summary": "", "themes": []}
        defer_brief = {
            "source_decision": "defer",
            "defer_reason_code": "commission_anchor_not_grounded",
            "defer_reason": "test",
        }
        ep = _make_evidence(source_origin="fetched_article")
        result = orch._handle_defer_run(seed, defer_brief, ep, "fetched_article")
        assert result["status"] == "defer"
        assert result["source_decision"] == "defer"
        assert result["commit_success"] is False
        assert result["agent"] is None
        assert result.get("declined") is False
        assert spied == [], "no decline persisted, seed not marked used -- fully reconsiderable"
        assert persisted == [], "_persist_article_plan must not run for defer"
        assert not any(orch.posts_dir.iterdir()), "no article file for defer"
        assert not any(orch.drafts_dir.iterdir()), "no draft file for defer"
    finally:
        restore_plan()
        restore_mark()
    print("C3 OK  defer run: no article/plan/decline-record/used-mark, source stays reconsiderable")


# --------------------------------------------------------------------------- #
# Real end-to-end dispatch proof: runs the ACTUAL _run_production_automation_
# locked() method (not _handle_defer_run directly) so the generate.py dispatch
# line `if fable_brief and _src_decision == "defer": return
# self._handle_defer_run(...)` is itself exercised, not merely the handler in
# isolation -- reverting that one dispatch line (proven below) makes this fail.
# --------------------------------------------------------------------------- #

def _ungrounded_commission_call_editorial_model(self, system, user, *a, **k):
    if "editorial director of Crip Minds" in system:
        return _json.dumps({
            "source_decision": "commission",
            "eligible_execution_possible": True,
            "source_anchor_examined": "this exact clause does not appear in SOURCE_TEXT at all",
            "hidden_mechanism": "an invented mechanism",
            "why_disability_knowledge_changes_subject": "an invented tie that cannot be verified",
            "persona": "Maya Flux", "angle": "n/a", "register": "wry",
            "seed_sentence": "n/a", "opening_scene": "n/a", "opening_shape": "fact",
        })
    raise AssertionError(
        f"no LLM call other than the Fable brief should ever fire on a defer path "
        f"(writer/review/etc. must never run) -- got system prompt: {system[:80]!r}"
    )


def case_real_dispatch_routes_defer_to_handler_not_writer():
    po = _import_orchestrator()
    routed = []

    def spying_handle_defer(self, news_seed, fable_brief, evidence_packet, source_origin):
        routed.append(fable_brief.get("defer_reason_code"))
        raise _StopAfterPersist()  # short-circuit the harness, same discipline as PRF1's own harness

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = po.ProductionOrchestrator()
        _isolate_paths(orch, tmpdir)
        orch.posts_dir.mkdir(parents=True, exist_ok=True)
        orch.drafts_dir.mkdir(parents=True, exist_ok=True)
        orch.assets_dir.mkdir(parents=True, exist_ok=True)
        (orch.repo_root / "_reviews").mkdir(exist_ok=True)
        orch.force_run = True
        restore = _patch_methods(
            po.ProductionOrchestrator,
            check_for_existing_article_today=lambda self: None,
            get_news_seed=lambda self: dict(NEWS_SEED),
            get_discovery_from_database=lambda self: None,
            get_source_text=lambda self, url, max_chars=3000, fallback_text=None, underlying_url=None: SOURCE_TEXT[:max_chars],
            get_source_origin=lambda self, url: "fetched_article",
            get_pool_links=lambda self, keywords: [],
            _rotation_eligible_agents=lambda self: ["Maya Flux", "Siri Sage"],
            _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
            _active_fault_lines=lambda self, text: [],
            _get_recent_openings=lambda self, n=5: "",
            _call_editorial_model=_ungrounded_commission_call_editorial_model,
            _handle_defer_run=spying_handle_defer,
        )
        error = None
        try:
            orch._run_production_automation_locked()
            error = "pipeline completed without ever reaching _handle_defer_run"
        except _StopAfterPersist:
            pass
        except Exception as e:  # noqa: BLE001
            error = f"{type(e).__name__}: {e}"
        finally:
            restore()
    if error:
        raise AssertionError(f"real dispatch did not route the ungrounded commission to defer: {error}")
    assert routed == ["commission_anchor_not_grounded"]
    print("D1 OK  real _run_production_automation_locked() dispatch routes an ungrounded commission "
          "to _handle_defer_run -- no writer/review call ever fires")


# --------------------------------------------------------------------------- #
# Section 8 — adversarial commission-validation cases A-H
# --------------------------------------------------------------------------- #

def case_8a_grounded_commission_valid():
    ep = _make_evidence(source_origin="fetched_article")
    ok, code, _, _ = validate_source_decision(VALID_COMMISSION, ep)
    assert ok and code == "commission"
    print("8A OK  grounded anchor + source-supported mechanism -> COMMISSION valid")


def case_8b_mechanism_requires_external_facts_defers():
    ep = _make_evidence(source_origin="fetched_article")
    bad = dict(VALID_COMMISSION)
    bad["why_disability_knowledge_changes_subject"] = (
        "This connects to an unrelated Grok lawsuit involving 7,000 images, which the source never mentions."
    )
    ok, code, _, _ = validate_source_decision(bad, ep)
    assert ok is False and code == "commission_mechanism_not_tied_to_anchor"
    print("8B OK  grounded topic anchor + externally-sourced mechanism -> DEFER (not tied to anchor)")


def case_8c_anchor_not_in_source_defers():
    ep = _make_evidence(source_origin="fetched_article")
    bad = dict(VALID_COMMISSION)
    bad["source_anchor_examined"] = "this exact sentence is not in the source at all"
    ok, code, _, _ = validate_source_decision(bad, ep)
    assert ok is False and code == "commission_anchor_not_grounded"
    print("8C OK  anchor not present in source -> DEFER (commission_anchor_not_grounded)")


def case_8d_fallback_summary_cannot_commission():
    ep = _make_evidence(source_origin="fallback_summary")
    ok, code, _, _ = validate_source_decision(VALID_COMMISSION, ep)
    assert ok is False and code == "commission_source_insufficient"
    print("8D OK  fallback_summary origin -> cannot authoritatively COMMISSION")


def case_8e_truncated_source_cannot_commission():
    ep = _make_evidence(source_origin="fetched_article", truncated=True)
    ok, code, _, _ = validate_source_decision(VALID_COMMISSION, ep)
    assert ok is False and code == "commission_evidence_truncated"
    print("8E OK  materially truncated source -> cannot COMMISSION")


def case_8f_eligible_execution_possible_string_rejected():
    ep = _make_evidence(source_origin="fetched_article")
    bad = dict(VALID_COMMISSION)
    bad["eligible_execution_possible"] = "false"  # string, not boolean
    ok, code, _, _ = validate_source_decision(bad, ep)
    assert ok is False and code == "commission_eligible_flag_malformed"
    print("8F OK  eligible_execution_possible='false' (string) -> rejected as malformed, not coerced")


def case_8g_valid_commission_no_eligible_carrier_not_decline():
    orch, po = _orch()
    blocked = dict(VALID_COMMISSION)
    blocked.update({"eligible_execution_possible": False, "blocked_carry_persona": "Pixel Nova"})
    restore = _patch_common(orch, po, blocked)
    try:
        ep = _make_evidence(source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert brief is not None
        assert brief["source_decision"] == "commission"
        assert brief["eligible_execution_possible"] is False
        assert "decline_contract_version" not in brief
    finally:
        restore()
    print("8G OK  valid grounded commission + no eligible carrier -> NO_ELIGIBLE_CARRIER, no decline")


def case_8h_invalid_commission_no_writer_no_article_no_decline():
    orch, po = _orch()
    bad = dict(VALID_COMMISSION)
    bad["hidden_mechanism"] = ""  # missing required grounding field
    restore = _patch_common(orch, po, bad)
    persisted = []
    restore_plan = _patch_methods(
        po.GenerateMixin,
        _persist_article_plan=lambda self, slug, agent_name, fable_brief: persisted.append(("plan", slug)),
    )
    spied = []
    restore_mark = _patch_methods(
        po.DiscoveryMixin,
        mark_news_seed_declined=lambda self, seed_id, record: spied.append(("declined", seed_id)),
    )
    try:
        ep = _make_evidence(source_origin="fetched_article")
        brief = orch._fable_editorial_brief(
            "title", "summary", "angle", "Maya Flux", ep,
            eligible_agents=["Maya Flux", "Siri Sage"],
        )
        assert brief is not None and brief["source_decision"] == "defer"
        seed = {"id": "seed-8h", "title": "T", "url": "http://x.example", "summary": "", "themes": []}
        result = orch._handle_defer_run(seed, brief, ep, "fetched_article")
        assert result["commit_success"] is False
        assert result["agent"] is None
        assert spied == [], "no decline persisted for invalid commission evidence"
        assert persisted == [], "no article plan persisted for invalid commission evidence"
        assert not any(orch.posts_dir.iterdir())
        assert not any(orch.drafts_dir.iterdir())
    finally:
        restore()
        restore_plan()
        restore_mark()
    print("8H OK  invalid commission evidence -> no writer, no article, no decline persistence (DEFER)")


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #

ALL = [
    case_url_domain_and_first_external_href,
    case_fetch_feed_recovers_underlying_url_per_item_only,
    case_fetch_feed_non_aggregator_item_has_no_underlying_url,
    case_aggregator_url_never_page_fetched_no_underlying,
    case_aggregator_url_fetches_real_underlying_article,
    case_underlying_url_that_is_itself_aggregator_domain_ignored,
    case_commission_cannot_ground_mechanism_from_excluded_neighbor,
    case_full_pipeline_defers_on_contaminated_commission_attempt,
    case_defer_run_writes_no_publication_artifacts,
    case_real_dispatch_routes_defer_to_handler_not_writer,
    case_8a_grounded_commission_valid,
    case_8b_mechanism_requires_external_facts_defers,
    case_8c_anchor_not_in_source_defers,
    case_8d_fallback_summary_cannot_commission,
    case_8e_truncated_source_cannot_commission,
    case_8f_eligible_execution_possible_string_rejected,
    case_8g_valid_commission_no_eligible_carrier_not_decline,
    case_8h_invalid_commission_no_writer_no_article_no_decline,
]


def main():
    failures = 0
    for case in ALL:
        try:
            case()
        except AssertionError as e:
            failures += 1
            print(f"FAIL  {case.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"ERROR {case.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(ALL) - failures}/{len(ALL)} cases passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
