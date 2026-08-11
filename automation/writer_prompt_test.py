#!/usr/bin/env python3
"""
writer_prompt_test.py — mocked capture of the ACTUAL writer prompt built by
_run_production_automation_locked() (generate.py), zero network cost.

WHY THIS EXISTS: snapshot_test.py's _snapshot_generate_calls only ever
covered _fable_editorial_brief's own prompt construction (see that module's
docstring, item 3) -- the WRITER prompt (what Opus/Fable actually receives
to write the article body) was never captured or asserted on at all. That's
the single most safety-critical text Phase 1.6 touches: it's where
writer_prompt_block's validated-evidence sections, the OPENING instruction,
and the SOURCE MATERIAL block all land, and where every laundering path
fixed this session (editorial_need/interpretation, opening_scene/
seed_sentence, angle/cross_cite, summary-as-authority) would actually show
up if any of those fixes ever regressed. Found on review, before the mocked
baseline was allowed to freeze: recording a "clean" snapshot of ONLY the
brief-construction call while leaving this boundary completely untested
would let the most important thing go unverified.

Reuses the same _import_orchestrator/_patch_methods/_isolate_paths harness
as snapshot_test.py/phase_probe.py (same frozen-input/stubbed-side-effect
discipline), but intercepts call_llm_via_openclaw_session itself to CAPTURE
the constructed prompt and immediately abort via a sentinel exception -- no
real network call, no image generation, no git, no downstream gate/review
pass. The mocked _fable_editorial_brief return value below is deliberately
"contaminated" with canary strings a real fabrication would look like
(a fabricated angle premise, a fabricated opening_scene/seed_sentence, a
canary inside editorial_need/interpretation) specifically so this test
fails loudly if any of those fields ever leak back into the writer prompt.

USAGE: python3 automation/writer_prompt_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
import tempfile
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from snapshot_test import (  # noqa: E402
    _import_orchestrator, _patch_methods, _isolate_paths,
    FIXTURE_RECENT_POSTS, FIXTURE_PERSONA_STATE, FIXTURE_FAULT_LINE,
)
from orchestrator.grounding import build_evidence_packet  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


class _StopAfterWriterPrompt(BaseException):
    """Raised the instant the writer's LLM call is reached, with the prompt
    already captured -- nothing downstream (real generation, rewrite, gate,
    commit) should ever run for this test.

    MUST subclass BaseException, not Exception: generate.py wraps the
    call_llm_via_openclaw_session call site in its own `except Exception`
    (to fall back to generate_fallback_article on a real LLM failure) --
    an Exception-based sentinel raised from inside the mocked call gets
    silently swallowed there and the run continues to completion on the
    fallback path instead of stopping, which defeats the whole point of
    this being a zero-cost, capture-and-abort harness (found by this test
    initially reporting "pipeline completed without ever reaching the
    writer call" despite the prompt having been captured moments earlier).
    BaseException is not caught by a bare `except Exception`, so it
    propagates cleanly up to this module's own try/except."""


SOURCE_TEXT = (
    "City council votes to remove three accessible parking bays downtown\n\n"
    "The city council voted 6-3 on Tuesday to remove three accessible parking "
    "bays and replace them with a protected bike lane. 'This was a genuinely "
    "difficult trade-off,' said council transport lead Dana Ruiz. Wheelchair "
    "user Priya Nathan told the council the new route adds a 400-metre "
    "detour with no dropped kerb for two of the three blocks."
)

NEWS_SEED = {
    "id": 1, "url": "https://example.com/probe-fixture",
    "title": "City council votes to remove three accessible parking bays downtown",
    "summary": "The bays are being replaced with a bike lane after a resident petition.",
    "source_name": "test", "source_tier": 1, "pub_date": "2026-08-11", "fetched_date": "2026-08-11",
    "relevance_score": 0.8, "themes": "urban_planning",
    "disability_angle": "Wheelchair users say the replacement bays are 400m further from transit.",
    "used": 0, "used_date": None, "angle_checked": 1,
}


def _canary_brief(persona_name, register_name):
    """A hand-built, schema-v2-shaped brief whose free-prose fields are
    DELIBERATELY fabricated canaries -- if any of them show up in the
    captured writer prompt, a laundering path has regressed."""
    packet = build_evidence_packet(SOURCE_TEXT)
    return {
        "persona": persona_name,
        # Smuggles an unsupported factual premise inside a grammatically
        # valid question (task #26's exact motivating example) -- must NOT
        # reach the writer at all now.
        "angle": "Why did Deborah Antwi support the compromise despite being hit there last year?",
        "register": register_name,
        # Fabricated opening_scene/seed_sentence -- must NOT reach the
        # writer; only opening_shape may.
        "seed_sentence": 'Marcus Reyes stood outside city hall holding a sign that read "9200 signatures."',
        "opening_scene": 'Marcus Reyes stood outside city hall holding a sign that read "9200 signatures."',
        "opening_shape": "fact",
        "cross_cite": "Whether a compliant retrofit counts as access at all -- Deborah Antwi's testimony proves it doesn't.",
        "correction_moment": {
            "editorial_need": "CANARY_EDITORIAL_NEED_SHOULD_NOT_REACH_WRITER",
            "evidence_candidate": {
                "status": "not_found", "source_excerpt": "", "named_person": "",
                "direct_quote": "", "dates_numbers": [],
            },
            "interpretation": "CANARY_INTERPRETATION_SHOULD_NOT_REACH_WRITER",
        },
        "resisting_example": {
            "editorial_need": "CANARY_EDITORIAL_NEED_SHOULD_NOT_REACH_WRITER",
            "evidence_candidate": {
                "status": "found",
                "source_excerpt": (
                    "Wheelchair user Priya Nathan told the council the new route adds a "
                    "400-metre detour with no dropped kerb for two of the three blocks."
                ),
                "named_person": "Priya Nathan", "direct_quote": "", "dates_numbers": ["400"],
            },
            "interpretation": "CANARY_INTERPRETATION_SHOULD_NOT_REACH_WRITER",
        },
        "brief_schema_version": 2,
        "grounding_status": "validated",
        "grounding_scope": "evidence_fields_only",
        "grounding_violations": [],
        "source_hash": packet["source_hash"],
        "evidence_packet_hash": packet["evidence_packet_hash"],
        "evidence_schema_version": packet["evidence_schema_version"],
        "source_truncated": packet["source_truncated"],
    }


def _capture_writer_prompt(source_origin="fetched_article"):
    """Runs the real pipeline (frozen inputs, stubbed side effects, same
    discipline as phase_probe.py) up to and including the writer's own LLM
    call, capturing the exact prompt string sent AND the evidence_packet
    the (mocked) planner was actually called with. Returns
    (prompt_or_None, evidence_packet_or_None, error_or_None).

    source_origin: simulates get_source_origin(url)'s Phase 1.6 return
    value -- "fetched_article" (default, a genuine fetch) or
    "fallback_summary" (the real-article fetch failed/was blocked and
    get_source_text fell back to returning the RSS summary instead, which
    generate.py must NOT grant source-snapshot authority to)."""
    po = _import_orchestrator()
    captured = {}

    def capturing_llm_call(self, prompt, model_priority=None):
        captured["prompt"] = prompt
        raise _StopAfterWriterPrompt()

    def capturing_brief(self, *a, **k):
        # _fable_editorial_brief(news_title, news_summary, disability_angle,
        # current_agent, evidence_packet=None) -- evidence_packet is
        # positional 5th arg in generate.py's real call.
        captured["evidence_packet"] = a[4] if len(a) > 4 else k.get("evidence_packet")
        return _canary_brief("Maya Flux", "wry")

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = po.ProductionOrchestrator()
        _isolate_paths(orch, tmpdir)
        orch.posts_dir.mkdir(parents=True, exist_ok=True)
        orch.drafts_dir.mkdir(parents=True, exist_ok=True)
        orch.assets_dir.mkdir(parents=True, exist_ok=True)
        (orch.repo_root / "_reviews").mkdir(exist_ok=True)
        for filename, title, body_line in FIXTURE_RECENT_POSTS:
            (orch.posts_dir / filename).write_text(
                f"---\ntitle: {title}\n---\n\n{body_line}\n", encoding="utf-8"
            )

        orch.override_agent = "Maya Flux"
        orch.force_run = True

        restore = _patch_methods(
            po.ProductionOrchestrator,
            check_for_existing_article_today=lambda self: None,
            get_news_seed=lambda self: dict(NEWS_SEED),
            get_discovery_from_database=lambda self: None,
            _get_overused_themes=lambda self: [],
            _get_recent_references=lambda self, days=14: [],
            get_source_text=lambda self, url, max_chars=3000, fallback_text=None: SOURCE_TEXT[:max_chars],
            get_source_origin=lambda self, url: source_origin,
            get_pool_links=lambda self, keywords: [],
            _balance_agent=lambda self, preferred: "Maya Flux",
            _pick_register=lambda self: ("wry", "Dry, observational. The joke is in the framing."),
            _pick_length=lambda self: 1000,
            _pick_article_type=lambda self: ("essay", ""),
            _get_calendar_event_nudge=lambda self: "",
            _fable_editorial_brief=capturing_brief,
            _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
            _active_fault_lines=lambda self, text: [dict(FIXTURE_FAULT_LINE)],
            call_llm_via_openclaw_session=capturing_llm_call,
        )
        error = None
        try:
            orch._run_production_automation_locked()
            error = "pipeline completed without ever reaching call_llm_via_openclaw_session"
        except _StopAfterWriterPrompt:
            pass
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        finally:
            restore()

    return captured.get("prompt"), captured.get("evidence_packet"), error


def test_writer_prompt_boundaries():
    prompt, packet, error = _capture_writer_prompt(source_origin="fetched_article")
    check("writer prompt was actually captured (pipeline reached the writer call)", prompt is not None and error is None)
    if not prompt:
        print(f"  (capture failed: {error})")
        return

    check("evidence_packet records source_origin=fetched_article for a genuine fetch", packet is not None and packet.get("source_origin") == "fetched_article")

    # POSITIVE: real, validated material DOES reach the writer.
    check(
        "writer prompt contains the validated resisting_example source excerpt",
        "Wheelchair user Priya Nathan told the council the new route adds a "
        "400-metre detour with no dropped kerb for two of the three blocks." in prompt,
    )
    check("writer prompt contains the real SOURCE MATERIAL block with real source content", "Dana Ruiz" in prompt and "6-3" in prompt)
    check("writer prompt still receives opening_shape as a structural category", "fact" in prompt)

    # NEGATIVE: every fabricated/free-prose canary must be absent.
    check(
        "writer prompt does NOT contain the fabricated angle premise about Deborah Antwi (task #26)",
        "Deborah Antwi" not in prompt,
    )
    check(
        "writer prompt does NOT contain the fabricated opening_scene/seed_sentence text (task #12)",
        "Marcus Reyes" not in prompt and "9200 signatures" not in prompt,
    )
    check(
        "writer prompt does NOT contain planner editorial_need/interpretation canary text (task #8)",
        "CANARY_EDITORIAL_NEED_SHOULD_NOT_REACH_WRITER" not in prompt
        and "CANARY_INTERPRETATION_SHOULD_NOT_REACH_WRITER" not in prompt,
    )
    check(
        "writer prompt does NOT carry an EDITOR BRIEF / literal angle heading at all (task #26)",
        "EDITOR BRIEF" not in prompt,
    )
    check(
        "writer prompt does NOT carry a literal cross_cite disagreement heading (task #26)",
        "Deborah Antwi's testimony proves it doesn't" not in prompt,
    )
    check(
        "writer prompt does NOT contain raw evidence_candidate/legacy-object JSON leaking through",
        "evidence_candidate" not in prompt and "source_excerpt\":" not in prompt,
    )
    check(
        "writer prompt's OPENING instruction does not point the writer at 'summary' as an authority (task #25)",
        "drawn only from the source/summary material" not in prompt,
    )


def test_fallback_summary_not_granted_source_authority():
    """Round 5 (found on review): get_source_text/fetch_source_article
    return a plain string whether a real fetch succeeded or it fell back to
    the RSS summary -- indistinguishable once returned as source_text.
    generate.py must check get_source_origin(url) and refuse to build an
    evidence_packet (or a writer SOURCE MATERIAL block) from a
    fallback_summary result, since that's the exact same unvetted short
    summary already shown separately as plain "Summary:" context."""
    prompt, packet, error = _capture_writer_prompt(source_origin="fallback_summary")
    check("pipeline still reaches the writer call under a fallback_summary origin", prompt is not None and error is None)
    if not prompt:
        print(f"  (capture failed: {error})")
        return

    check(
        "evidence_packet passed to the planner has NO source_text when origin is fallback_summary",
        packet is not None and packet.get("source_text") is None,
    )
    check(
        "evidence_packet STILL records source_origin=fallback_summary as explanatory provenance "
        "(distinguishable from a genuine 'none' -- both otherwise look identical once source_text is None)",
        packet is not None and packet.get("source_origin") == "fallback_summary",
    )
    check(
        "writer prompt does NOT contain a SOURCE MATERIAL block built from the fallback summary",
        "SOURCE MATERIAL" not in prompt,
    )
    check(
        "writer prompt does NOT contain the fetched-article-only content (Dana Ruiz/6-3) "
        "since source_text was correctly suppressed",
        "Dana Ruiz" not in prompt,
    )


if __name__ == "__main__":
    test_writer_prompt_boundaries()
    test_fallback_summary_not_granted_source_authority()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All writer-prompt boundary tests passed.")
