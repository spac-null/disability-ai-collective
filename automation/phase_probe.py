#!/usr/bin/env python3
"""
phase_probe.py — controlled dry-run harness for the writer prompt itself.

WHY THIS EXISTS: the article-quality repair blueprint (2026-08-10, see
.claude/audience-engagement-tasklist.md's sibling docs / project memory)
requires "one layer at a time, against fixed test articles" -- comparing a
phase's effect against the phase before it. Two things make that invalid
without this harness:

  1. production_orchestrator.py --force IS NOT A DRY RUN. It generates paid
     images, writes to _drafts/, git add+commit+PUSHES, marks the news
     seed/discovery finding permanently used, and mutates persona state, the
     beat ledger, the citation ledger, and engagement.db. Running it
     repeatedly to validate a prompt change pushes junk to the live repo and
     burns real seeds.
  2. There is no temperature control anywhere in the generation call chain
     (confirmed 2026-08-10 -- see _call_openai_compat_api's temperature
     parameter, added the same day specifically for this harness). The
     provider default applies, so two calls with an IDENTICAL prompt produce
     materially different articles. A single before/after article comparison
     is not evidence of anything; only a distribution across several samples
     is.

This harness runs the REAL _run_production_automation_locked() -- not a
reimplementation of its logic, which would silently drift out of sync with
real pipeline changes -- with every variable input frozen to a fixed value
and every write/consume side effect stubbed to a no-op. See FROZEN vs
STUBBED below for the exact list.

FROZEN (deterministic inputs, same every run):
  topic/source text, persona, register, article length target, article type,
  Fable brief (loaded from a frozen fixture -- see --freeze-briefs), recent
  posts/persona-state/fault-lines (reused from snapshot_test.py's fixtures).
  Temperature is pinned via _call_openai_compat_api's temperature= kwarg,
  ONLY inside this harness -- production callers never pass it, so live
  generation behavior is completely unaffected by this file's existence.

STUBBED (no-op, zero side effects):
  generate_images (no paid image calls), commit_to_git (no git operations --
  returns False, which already correctly gates mark_finding_as_used /
  mark_news_seed_used / _store_pending_social off in the real function),
  _record_cited_theorists, _record_beat, _persist_article_plan,
  _save_persona_state (writes to a fixed path outside repo_root, NOT covered
  by path isolation), validate_article (the post-publish fact-check/citation/
  engagement-read pass -- expensive, hits Perplexity Sonar, and is a separate
  concern from the writer-prompt comparison this harness exists for; stubbed
  to (None, True) rather than run on every probe sample).

_pre_commit_gate DOES run for real (relatively cheap, one Sonnet call) --
its surgical-fix pass can modify the draft before it's written, and that's
real pipeline behavior worth capturing in the baseline.

Every filesystem write goes through _isolate_paths (snapshot_test.py) into a
throwaway tmpdir -- _posts/, _drafts/, _reviews/, and the discovery DB never
touch the real repo.

USAGE:
    python3 automation/phase_probe.py --freeze-briefs
        One-time (or per-phase, if a phase deliberately changes brief
        generation -- see the blueprint's Section T.3): makes ONE real,
        live _fable_editorial_brief call per topic and freezes the result
        to automation/.probe_fixtures/brief_<topic>.json. Costs real tokens;
        run it once, not per sample.

    python3 automation/phase_probe.py --run baseline --samples 3
        Runs all 3 topics x --samples real writer-generation calls (live
        network, real cost) through the actual pipeline and writes each
        result to automation/probe_out/<phase_name>/. Requires frozen
        briefs to already exist (run --freeze-briefs first).

    python3 automation/phase_probe.py --score baseline
        Prints mechanical metrics (word count, sentence-length stats, gate
        violations) for every article already written under
        automation/probe_out/<phase_name>/, plus a metrics.json summary.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
REPO_ROOT = AUTOMATION_DIR.parent
PROBE_FIXTURES_DIR = AUTOMATION_DIR / ".probe_fixtures"
PROBE_OUT_DIR = AUTOMATION_DIR / "probe_out"

sys.path.insert(0, str(AUTOMATION_DIR))
from snapshot_test import (  # noqa: E402
    _import_orchestrator, _patch_methods, _isolate_paths,
    FIXTURE_RECENT_POSTS, FIXTURE_PERSONA_STATE, FIXTURE_FAULT_LINE,
)

# Pinned inside this harness only -- see module docstring. 0.9 rather than the
# provider default (1.0) or something very low (0.3-0.5 would suppress the
# real register/voice variation the writer prompt is supposed to produce,
# making samples artificially similar to each other and hiding real
# phase-to-phase differences under an artificial floor).
PROBE_TEMPERATURE = 0.9

# 3 fixed topics, deliberately spanning 3 different personas so a persona-
# specific prompt change (e.g. Siri Sage's VOICE ANCHOR, Phase A2) is only
# exercised by its own topic, and a shared-prompt change (Phase 0/1) is
# exercised by all three. Source text is a real, representative excerpt --
# not fetched live, so it never changes between runs.
PROBE_TOPICS = [
    {
        "key": "sauna",
        "persona": "Siri Sage",
        "news_seed": {
            "id": 1,
            "url": "https://example.com/probe-fixture-sauna",
            "title": "Crystal-shaped sauna rises from former industrial site in Sweden",
            "summary": (
                "Stockholm-based artist duo Bigert & Bergstrom has created a pink "
                "crystal-shaped sauna on a remediated industrial site in Skelleftea, "
                "northern Sweden. Named Lithium Crystal Sauna, the structure is clad "
                "in mirrored, titanium-coated stainless steel facets."
            ),
            "source_name": "Dezeen",
            "source_tier": 1,
            "pub_date": "2026-08-09",
            "fetched_date": "2026-08-09",
            "relevance_score": 0.85,
            "themes": "architecture,design",
            "disability_angle": "",
            "used": 0,
            "used_date": None,
            "angle_checked": 1,
        },
        "source_text": (
            "Crystal-shaped sauna rises from former industrial site in Sweden\n\n"
            "Stockholm-based artist duo Bigert & Bergstrom has created a pink "
            "crystal-shaped sauna on a remediated industrial site in Skelleftea, "
            "northern Sweden. Named Lithium Crystal Sauna, it is the first permanent "
            "structure completed for WasteLand Climate Action Park, a project "
            "transforming one of Vasterbotten's most polluted industrial sites -- a "
            "former Scharin pulp mill -- after 17 years of soil remediation.\n\n"
            "The sauna is clad in roughly 280 mirrored, titanium-coated stainless "
            "steel facets, arranged so the whole structure leans back four degrees "
            "from vertical. 'The project is shaped around ambiguity,' studio founder "
            "Niko told Dezeen. Visitors enter through a single door into a small "
            "changing area before the main heat chamber, which seats up to eight "
            "people around a central stove.\n\n"
            "The remediation of the Scharin site involved removing contaminated "
            "topsoil down to bedrock in several sections and capping the rest with "
            "a sealed clay layer. Bigert & Bergstrom have previously built "
            "climate-themed installations including a solar-powered ice rink and a "
            "greenhouse that floods on a timer."
        ),
    },
    {
        "key": "hiring_tool",
        "persona": "Zen Circuit",
        "news_seed": {
            "id": 2,
            "url": "https://example.com/probe-fixture-hiring",
            "title": "New AI hiring-screening tool adopted by regional employer network",
            "summary": (
                "The tool scores recorded video interviews for 'engagement' and "
                "'clarity of speech', flagging candidates whose scores fall below a "
                "set threshold for manual review."
            ),
            "source_name": "regional business wire",
            "source_tier": 2,
            "pub_date": "2026-08-05",
            "fetched_date": "2026-08-05",
            "relevance_score": 0.7,
            "themes": "technology,employment",
            "disability_angle": "Autistic and disabled applicants score lower on 'engagement' metrics regardless of interview content.",
            "used": 0,
            "used_date": None,
            "angle_checked": 1,
        },
        "source_text": (
            "New AI hiring-screening tool adopted by regional employer network\n\n"
            "A consortium of 40 regional employers has adopted an AI-driven video "
            "interview screening tool, the companies announced this week. The "
            "system records a candidate's first-round interview, then scores it on "
            "dimensions including 'engagement', 'clarity of speech', and 'positive "
            "affect', producing a single composite score employers can use to "
            "triage applicants before a human ever watches the recording.\n\n"
            "'We're not replacing human judgment, we're focusing it,' said one HR "
            "director involved in the rollout, speaking on condition her company "
            "not be named. The vendor's own materials describe the underlying model "
            "as trained on 'tens of thousands of hours of successful interview "
            "footage', though the company has not published details of that "
            "training set or its demographic composition.\n\n"
            "Independent researchers who have studied similar tools in other "
            "markets have found that scoring models trained this way frequently "
            "penalize atypical eye contact, pacing, and vocal tone -- traits "
            "correlated with autism and some other disabilities -- regardless of "
            "what a candidate actually says. None of the consortium's public "
            "materials mention disability, accommodation, or an appeals process for "
            "a low composite score."
        ),
    },
    {
        "key": "curb_cuts",
        "persona": "Maya Flux",
        "news_seed": {
            "id": 3,
            "url": "https://example.com/probe-fixture-curbcuts",
            "title": "City council votes to remove three accessible parking bays downtown",
            "summary": (
                "The bays are being replaced with a protected bike lane after a "
                "resident petition; the nearest remaining accessible bay is roughly "
                "400 metres further from the transit interchange."
            ),
            "source_name": "local council minutes",
            "source_tier": 2,
            "pub_date": "2026-08-03",
            "fetched_date": "2026-08-03",
            "relevance_score": 0.65,
            "themes": "urban planning,transport",
            "disability_angle": "Wheelchair users say the replacement bays add a 400m detour with no dropped kerb for two of the three blocks.",
            "used": 0,
            "used_date": None,
            "angle_checked": 1,
        },
        "source_text": (
            "City council votes to remove three accessible parking bays downtown\n\n"
            "The city council voted 6-3 on Tuesday to remove three accessible "
            "parking bays on Exchange Street and replace them with a protected bike "
            "lane, following a two-year resident petition campaign. The nearest "
            "remaining accessible bay is now roughly 400 metres from the transit "
            "interchange, up from the removed bays' 40-metre distance.\n\n"
            "'This was a genuinely difficult trade-off between two forms of "
            "sustainable, accessible transport,' the council's transport lead said "
            "in a statement, adding that a new accessible bay would be added 'as "
            "part of a future phase' with no confirmed date. A council staff report "
            "noted that two of the three blocks between the new bay and the "
            "interchange currently have no dropped kerb, meaning the marked "
            "wheelchair route requires an additional 150-metre detour around them.\n\n"
            "The bike lane petition, organised by a local cycling advocacy group, "
            "collected 1,200 signatures over 18 months. No disability advocacy "
            "group was consulted during the petition process; the council's own "
            "accessibility liaison was on leave for the duration of the review "
            "period and the position has not been backfilled."
        ),
    },
]


# Supplemental, one-off validation topics -- deliberately NOT merged into
# PROBE_TOPICS. The canonical 3-topic/3-persona design (above) is what the
# existing frozen baseline/whywewrite-v1 runs used, and any future phase that
# calls run_phase()/freeze_briefs() without --topic must keep iterating
# exactly those 3 topics, unchanged, so it stays comparable to that history.
# This list exists so a specific persona not covered by PROBE_TOPICS (here:
# Pixel Nova, added 2026-08-10 to validate WHY WE WRITE against a 4th
# persona/territory -- information architecture/legibility/interfaces --
# without regenerating or renaming anything under the existing 3 topics)
# can be probed via --topic <key> without touching the default 3-topic path.
#
# NOTE on this fixture's provenance (2026-08-10): a first draft here used a
# fabricated transit-signage story (example.com, invented quotes, an
# invented "40 stations"/"2013 retrofit"/Braille-removal narrative). Caught
# and discarded before freezing or running anything against it -- it failed
# on two counts: (1) it violated the source-grounding principle this whole
# repair project is trying to strengthen (Fable/Opus reasoning from facts
# that never happened), and (2) the invented details were themselves
# essay-ready evidence (a "primary channel" audio-first framing, a
# conveniently untested app, no disability groups on the design panel) --
# effectively writing the test's own answer into the fixture. Replaced with
# a real, retrieved, verifiable story (The Art Newspaper, 2026-01-27) whose
# surface subject is curatorial/legibility, NOT disability -- it contains
# zero mentions of accessibility, Deaf visitors, or disability of any kind
# in the source itself, so any disability content in a generated essay has
# to come from Pixel's own persona/canon, not be pre-loaded by the source.
# `disability_angle` is deliberately left empty, same as the sauna topic's
# precedent -- Fable's brief-writing gets title+summary+persona only, no
# discovery-stage angle hint, for this one.
SUPPLEMENTAL_TOPICS = [
    {
        "key": "museum_labels",
        "persona": "Pixel Nova",
        "news_seed": {
            "id": 4,
            "url": "https://www.theartnewspaper.com/2026/01/27/museum-wall-texts-are-an-art-in-their-own-rightbut-will-they-survive-the-digital-age",
            "title": "Museum wall texts are an art in their own right — but will they survive the digital age?",
            "summary": (
                "Museums are rethinking the wall label as attention spans shrink: "
                "Calder Gardens in Philadelphia has dropped wall text entirely, "
                "branding itself 'open to interpretation', while the Frick Pittsburgh "
                "invites community members to write 'guest labels' and the Cleveland "
                "Museum of Art pushes context into a companion app instead."
            ),
            "source_name": "The Art Newspaper",
            "source_tier": 1,
            "pub_date": "2026-01-27",
            "fetched_date": "2026-08-10",
            "relevance_score": 0.7,
            "themes": "art_culture,design,museums",
            "disability_angle": "",
            "used": 0,
            "used_date": None,
            "angle_checked": 0,
        },
        "source_text": (
            "Museum wall texts are an art in their own right — but will they survive "
            "the digital age?\n\n"
            "As the average adult attention span is now measured at around 8.25 "
            "seconds, museums are rethinking what, if anything, a visitor should be "
            "asked to read next to an artwork. Calder Gardens, a new institution in "
            "Philadelphia, has dropped wall text altogether, branding itself 'open to "
            "interpretation' and leaving works entirely unlabelled. The Royal Ontario "
            "Museum in Toronto has gone the other way, keeping labels but shortening "
            "them into scannable fragments; assistant vice-president of interpretation "
            "Juline Chevalier said the museum now writes 'knowing that visitors are "
            "distracted as they read.'\n\n"
            "Other institutions are handing label-writing away from curators "
            "entirely. The Frick Pittsburgh invited community members to write "
            "'guest labels' for a recent Kara Walker exhibition, including a "
            "University of Pittsburgh professor, Shaun Myers, who used his label to "
            "reflect on his own family history. 'What is not being said in "
            "exhibition text is often just as revealing as what is being shared,' "
            "said the Frick's chief curator, Dawn Reid Brean. The Cleveland Museum "
            "of Art has pushed further context into a companion app called ArtLens "
            "instead of the wall; a museum representative described the printed "
            "label itself as 'the beginning of a relationship, not the end of an "
            "explanation.'\n\n"
            "A 2021 University of Vienna eye-tracking study conducted at Vienna's "
            "Belvedere Museum found that most visitors follow a fixed rhythm when "
            "encountering a labelled work: art, then label, then art again, "
            "confirming that the label is read as a distinct, separate object rather "
            "than absorbed alongside the image. Labels mounted at eye level were "
            "found to be read far more often than those placed above or below it."
        ),
    },
]

ALL_TOPICS_BY_KEY = {t["key"]: t for t in PROBE_TOPICS + SUPPLEMENTAL_TOPICS}


# Shape MUST match what discovery.py's real _pick_register/_pick_article_type
# return -- (name, prompt) 2-tuples, weight already consumed internally by
# random.choices and never part of the return value. These two constants used
# to be copy-pasted straight from _REGISTERS/_ARTICLE_TYPES's raw 3-tuple rows
# (name, weight, prompt), which meant the weight float rode along in the
# prompt-text slot. `_pick_register`'s stub lambda handed that 3-tuple back to
# generate.py's `register, register_prompt = self._pick_register()`, which
# blew up with "too many values to unpack (expected 2)" on every real
# `_run_one_sample()` call. Also restored the full "wry" prompt text (was
# truncated to one sentence) so the probe exercises the real register prompt.
PROBE_REGISTER = ("wry", "Dry, observational. The joke is in the framing, never announced. You find the absurdity in how things are organised and let it sit. The reader laughs a beat late.")
PROBE_LENGTH = 1000
PROBE_ARTICLE_TYPE = ("essay", "")


def _git_commit_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def _brief_fixture_path(topic_key):
    return PROBE_FIXTURES_DIR / f"brief_{topic_key}.json"


def freeze_briefs(force=False, topic_key=None):
    """Make ONE real, live _fable_editorial_brief call per topic and freeze the
    result. Real network cost -- run this deliberately, not per sample. See
    the blueprint's Section T.3: phases that change brief-generation logic
    itself should re-freeze; every other phase reuses the same frozen brief
    so the writer-prompt comparison isn't confounded by a differently-worded
    brief each time. topic_key: restrict to one topic (PROBE_TOPICS or
    SUPPLEMENTAL_TOPICS, e.g. 'signage') instead of the default 3 -- used for
    one-off supplemental-persona validation without re-freezing the rest."""
    po = _import_orchestrator()
    PROBE_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    topics = [ALL_TOPICS_BY_KEY[topic_key]] if topic_key else PROBE_TOPICS
    for topic in topics:
        path = _brief_fixture_path(topic["key"])
        if path.exists() and not force:
            print(f"  {topic['key']}: already frozen ({path.name}), skipping (--force to redo)")
            continue
        orch = po.ProductionOrchestrator()
        ns = topic["news_seed"]
        brief = orch._fable_editorial_brief(ns["title"], ns["summary"], ns["disability_angle"], topic["persona"])
        if not brief:
            print(f"  {topic['key']}: _fable_editorial_brief returned nothing -- try again", file=sys.stderr)
            continue
        path.write_text(json.dumps(brief, indent=2, sort_keys=True))
        print(f"  {topic['key']}: froze brief -> {path}")
    return 0


def _load_frozen_brief(topic_key):
    path = _brief_fixture_path(topic_key)
    if not path.exists():
        raise RuntimeError(
            f"No frozen brief for topic '{topic_key}' -- run "
            f"'python3 automation/phase_probe.py --freeze-briefs' first."
        )
    return json.loads(path.read_text())


def _run_one_sample(po, topic, sample_idx, temperature):
    """Run the real pipeline once for one topic, fully frozen/stubbed per the
    module docstring. Returns a dict: article_text, prompt_calls, error,
    degraded_stages, actual_models (every distinct model that actually
    answered, in call order -- the writer call may itself fall through
    several providers)."""
    frozen_brief = _load_frozen_brief(topic["key"])
    prompt_calls = []
    actual_models = []

    _orig_call = po.LLMMixin.__dict__["_call_openai_compat_api"]

    def capturing_call(self, url, api_key, system_prompt, user_prompt, model,
                        max_tokens=3500, timeout=120, no_think=False,
                        return_model=False, reasoning_max_tokens=None,
                        check_truncation=False, temperature=None, _orig=_orig_call):
        prompt_calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "model": model,
            "max_tokens": max_tokens,
        })
        result = _orig(
            self, url, api_key, system_prompt, user_prompt, model,
            max_tokens=max_tokens, timeout=timeout, no_think=no_think,
            return_model=return_model, reasoning_max_tokens=reasoning_max_tokens,
            check_truncation=check_truncation, temperature=PROBE_TEMPERATURE,
        )
        actual_models.append(result[1] if return_model and isinstance(result, tuple) else model)
        return result

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = po.ProductionOrchestrator()
        _isolate_paths(orch, tmpdir)
        orch.posts_dir.mkdir(parents=True, exist_ok=True)
        # drafts_dir isn't created by _isolate_paths itself (it only reassigns the
        # path); create_article_file does a bare open(filepath, 'w') with no parent
        # mkdir, so the first real sample to reach Step 6 would FileNotFoundError
        # inside the isolated tmpdir. Found by an independent isolation audit
        # (2026-08-10) before it had a chance to bite -- not a leak, just a crash
        # waiting to happen one step later than the one already being debugged.
        orch.drafts_dir.mkdir(parents=True, exist_ok=True)
        orch.assets_dir.mkdir(parents=True, exist_ok=True)
        (orch.repo_root / "_reviews").mkdir(exist_ok=True)
        for filename, title, body_line in FIXTURE_RECENT_POSTS:
            (orch.posts_dir / filename).write_text(
                f"---\ntitle: {title}\n---\n\n{body_line}\n", encoding="utf-8"
            )

        orch.override_agent = topic["persona"]
        orch.force_run = True

        ns = dict(topic["news_seed"])
        src_text = topic["source_text"]

        restore = _patch_methods(
            po.ProductionOrchestrator,
            # ── frozen inputs ──────────────────────────────────────────────
            check_for_existing_article_today=lambda self: None,
            get_news_seed=lambda self: dict(ns),
            get_discovery_from_database=lambda self: None,
            _get_overused_themes=lambda self: [],
            _get_recent_references=lambda self, days=14: [],
            get_source_text=lambda self, url, max_chars=3000, fallback_text=None: src_text[:max_chars],
            get_pool_links=lambda self, keywords: [],
            _balance_agent=lambda self, preferred: topic["persona"],
            _pick_register=lambda self: PROBE_REGISTER,
            _pick_length=lambda self: PROBE_LENGTH,
            _pick_article_type=lambda self: PROBE_ARTICLE_TYPE,
            _get_calendar_event_nudge=lambda self: "",
            _fable_editorial_brief=lambda self, *a, **k: dict(frozen_brief),
            _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
            _active_fault_lines=lambda self, text: [dict(FIXTURE_FAULT_LINE)],
            # ── stubbed side effects ───────────────────────────────────────
            _save_persona_state=lambda self, agent_name, state: None,
            _record_cited_theorists=lambda self, *a, **k: None,
            _record_beat=lambda self, *a, **k: None,
            _persist_article_plan=lambda self, *a, **k: None,
            generate_images=lambda self, *a, **k: ([], []),
            validate_article=lambda self, *a, **k: (None, True),
            commit_to_git=lambda self, *a, **k: False,
            # ── captured + temperature-pinned ───────────────────────────────
            _call_openai_compat_api=capturing_call,
        )
        # generate.py's degraded-run and fallback-mode alerts read
        # REEF_BOT_TOKEN/REEF_CHAT_ID from the environment directly (not via a
        # patchable method) and POST to the real Telegram API whenever
        # self._degraded_stages is non-empty -- a real possibility here, since
        # editorial-revision degradation depends on live LLM behavior, not
        # something this harness controls. Found by an independent isolation
        # audit (2026-08-10): on a host where these are already exported (e.g.
        # trident, where the real automation env lives), an unpatched probe
        # run could send a real message to the real ops channel about a
        # throwaway tmpdir path. Neutralize for the duration of this call only.
        import os as _os
        _saved_env = {k: _os.environ.pop(k, None) for k in ("REEF_BOT_TOKEN", "REEF_CHAT_ID")}
        try:
            result = orch._run_production_automation_locked()
            error = None
        except Exception as e:
            result, error = None, f"{type(e).__name__}: {e}"
        finally:
            restore()
            for k, v in _saved_env.items():
                if v is not None:
                    _os.environ[k] = v

        draft_files = list(orch.drafts_dir.glob("*.md")) if orch.drafts_dir.exists() else []
        article_text = draft_files[0].read_text(encoding="utf-8") if draft_files else None
        # Grab this before the tmpdir/orch instance goes out of scope -- see
        # production_orchestrator.py's __init__ for what populates it.
        degraded_stages = sorted(set(getattr(orch, "_degraded_stages", []) or []))

    return {
        "article_text": article_text,
        "prompt_calls": prompt_calls,
        "actual_models": actual_models,
        "error": error,
        "degraded_stages": degraded_stages,
    }


def _brief_hash(topic_key):
    import hashlib
    return hashlib.sha256(_brief_fixture_path(topic_key).read_bytes()).hexdigest()[:12]


def preflight(po=None):
    """Cheap check of the actual model-dependency paths the probe needs,
    BEFORE spending a full sample's ~13 calls to discover the environment is
    dead. Added 2026-08-10 after baseline attempt 1: 2/9 samples succeeded,
    then every subsequent call failed for the rest of the run (OpenRouter
    direct 402 Payment Required, CLIProxy 500, Nous 403) -- an external
    provider/account/proxy availability problem, not a phase_probe bug, but
    one that burned ~7 samples' worth of real calls before the harness's own
    per-sample rejection caught each one individually. This tests the
    dependency, not just whether a hostname responds -- two distinct minimal
    calls, since the writer path and the Fable-brief path share CLIProxy as
    their PRIMARY route but fall back to different services (OpenRouter-
    direct, Gemini, local Qwen) if CLIProxy itself is down.

    Returns True if healthy, False if not (with per-route detail printed).
    Deliberately probe-only -- does not touch or gate production behavior.
    """
    po = po or _import_orchestrator()
    orch = po.ProductionOrchestrator()
    from orchestrator.config import CLIPROXY_URL, CLIPROXY_KEY

    # Fable has mandatory extended thinking that counts against max_tokens
    # (see llm.py's _call_editorial_model docstring) -- give it real headroom
    # and cap its reasoning spend the same way production does, so a merely-
    # thoughtful reply doesn't get misread as an outage.
    routes = [
        ("writer path (Opus via CLIProxy)", "openrouter/claude-opus-4.8", None),
        ("Fable-brief path (Fable via CLIProxy)", "openrouter/claude-fable-5", 1024),
    ]
    all_ok = True
    for label, model, reasoning_cap in routes:
        try:
            raw = orch._call_openai_compat_api(
                url=CLIPROXY_URL, api_key=CLIPROXY_KEY,
                system_prompt="Reply with exactly one word.",
                user_prompt="Say OK.",
                model=model, max_tokens=2000, timeout=30,
                reasoning_max_tokens=reasoning_cap,
            )
            if raw and raw.strip():
                print(f"  PREFLIGHT OK   -- {label}")
            else:
                print(f"  PREFLIGHT FAIL -- {label}: empty response")
                all_ok = False
        except Exception as e:
            print(f"  PREFLIGHT FAIL -- {label}: {type(e).__name__}: {e}")
            all_ok = False

    if not all_ok:
        print("\nPREFLIGHT FAILED — model infrastructure unavailable. No baseline samples attempted.")
    else:
        print("\nPREFLIGHT OK — proceeding.")
    return all_ok


def _generate_one_sample_record(po, topic, i, out_dir, retried=False):
    """Generate one sample and write its files, returning the metrics.json
    entry for it. Shared by run_phase (fresh runs) and retry_failed (re-running
    specific failed/rejected slots) so both produce byte-identical record
    shapes and file-naming conventions."""
    import datetime
    label = f"{topic['key']}-{i}"
    print(f"generating {label} (persona={topic['persona']}){' [RETRY]' if retried else ''}...")
    run_result = _run_one_sample(po, topic, i, PROBE_TEMPERATURE)
    article_text = run_result["article_text"]
    degraded = run_result["degraded_stages"]

    sample_record = {
        "topic": topic["key"],
        "persona": topic["persona"],
        "sample": i,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "fable_brief_hash": _brief_hash(topic["key"]),
        "actual_models": run_result["actual_models"],
        "degraded_stages": degraded,
        "error": run_result["error"],
    }
    if retried:
        # Explicit per the recovery methodology: a retried slot must be visibly
        # marked as such in metrics.json, never silently indistinguishable from
        # a first-attempt success -- see .claude/current-work.md.
        sample_record["retried"] = True

    # A retry can overwrite a previous DEGRADED-<label>.md stub from the same
    # slot -- clean it up either way (success replaces it with the real file,
    # a repeat failure gets a fresh DEGRADED- write below) so stale stubs don't
    # accumulate across retries.
    degraded_stub = out_dir / f"DEGRADED-{label}.md"
    if retried and degraded_stub.exists():
        degraded_stub.unlink()

    if run_result["error"]:
        sample_record["status"] = "failed"
        print(f"  FAILED: {run_result['error']}", file=sys.stderr)
    elif degraded:
        # Healthy-path assertion: a sample generated during a degraded run
        # (failed brief/gate-LLM/editorial-revision -- see
        # production_orchestrator.py's __init__) is excluded from the
        # baseline set even though it produced an article. Comparing later
        # clean generations against a baseline partly made during a
        # simulated or real outage would be exactly the kind of
        # contaminated comparison this harness exists to prevent. Still
        # saved to disk (prefixed DEGRADED-) so it's inspectable, just not
        # counted as "ok".
        degraded_stub.write_text(article_text or "", encoding="utf-8")
        sample_record["status"] = "rejected_degraded"
        print(f"  REJECTED (degraded: {', '.join(degraded)}) -- saved as DEGRADED-{label}.md")
    elif article_text:
        (out_dir / f"{label}.md").write_text(article_text, encoding="utf-8")
        prompt_calls = run_result["prompt_calls"]
        if prompt_calls:
            writer_call = prompt_calls[0]
            (out_dir / f"{label}.prompt.txt").write_text(
                "=== SYSTEM ===\n" + writer_call["system_prompt"] +
                "\n\n=== USER ===\n" + writer_call["user_prompt"],
                encoding="utf-8",
            )
        (out_dir / f"{label}.all_calls.json").write_text(
            json.dumps(prompt_calls, indent=2), encoding="utf-8"
        )
        sample_record["word_count"] = len(re.findall(
            r"\S+", re.sub(r"^---\n.*?\n---\n", "", article_text, flags=re.DOTALL)
        ))
        sample_record["status"] = "ok"
    else:
        sample_record["status"] = "failed"
        print("  FAILED: no article text and no error captured", file=sys.stderr)

    return sample_record


def run_phase(phase_name, n_samples=3, topic_key=None):
    """topic_key: restrict this run to one topic (e.g. 'signage' for the
    Pixel Nova supplemental validation set) instead of the default 3-topic
    PROBE_TOPICS. Omitting it preserves the exact behavior every existing
    phase (baseline, whywewrite-v1, ...) already used -- do not default this
    to anything but None."""
    po = _import_orchestrator()
    print("Running preflight before spending any real sample calls...")
    if not preflight(po):
        return 1
    commit_hash = _git_commit_hash()
    out_dir = PROBE_OUT_DIR / phase_name
    out_dir.mkdir(parents=True, exist_ok=True)

    run_log = {
        "phase": phase_name,
        "commit": commit_hash,
        "temperature": PROBE_TEMPERATURE,
        "register": PROBE_REGISTER[0],
        "article_type": PROBE_ARTICLE_TYPE[0],
        "target_words": PROBE_LENGTH,
        "samples": [],
    }

    topics = [ALL_TOPICS_BY_KEY[topic_key]] if topic_key else PROBE_TOPICS
    for topic in topics:
        for i in range(n_samples):
            print(f"[{phase_name}] ", end="")
            run_log["samples"].append(_generate_one_sample_record(po, topic, i, out_dir))

    (out_dir / "metrics.json").write_text(json.dumps(run_log, indent=2), encoding="utf-8")
    ok = sum(1 for s in run_log["samples"] if s["status"] == "ok")
    rejected = sum(1 for s in run_log["samples"] if s["status"] == "rejected_degraded")
    print(f"\n[{phase_name}] {ok}/{len(run_log['samples'])} usable "
          f"({rejected} rejected as degraded) -> {out_dir}/")
    return 0 if ok == len(run_log["samples"]) else 1


def retry_failed(phase_name):
    """Re-run only the samples in an existing metrics.json that are not
    status=='ok' (i.e. 'failed' or 'rejected_degraded'), in place -- leaves
    already-clean samples completely untouched, never regenerates them.
    Each retried entry is marked retried=True (see _generate_one_sample_record)
    so a retry is always visible in the record, never indistinguishable from
    a first-attempt success. Requires the phase to have been run at least
    once already (metrics.json must exist)."""
    po = _import_orchestrator()
    out_dir = PROBE_OUT_DIR / phase_name
    metrics_path = out_dir / "metrics.json"
    if not metrics_path.exists():
        print(f"No metrics.json for phase '{phase_name}' -- run --run first.", file=sys.stderr)
        return 1

    run_log = json.loads(metrics_path.read_text())
    topics_by_key = ALL_TOPICS_BY_KEY
    to_retry = [(idx, s) for idx, s in enumerate(run_log["samples"]) if s["status"] != "ok"]

    if not to_retry:
        print(f"[{phase_name}] nothing to retry -- every sample is already status=ok.")
        return 0

    slot_labels = [f"{s['topic']}-{s['sample']}" for _, s in to_retry]
    print(f"[{phase_name}] retrying {len(to_retry)} non-ok sample(s): {slot_labels}")

    for idx, old_record in to_retry:
        topic = topics_by_key[old_record["topic"]]
        new_record = _generate_one_sample_record(po, topic, old_record["sample"], out_dir, retried=True)
        run_log["samples"][idx] = new_record

    metrics_path.write_text(json.dumps(run_log, indent=2), encoding="utf-8")
    ok = sum(1 for s in run_log["samples"] if s["status"] == "ok")
    rejected = sum(1 for s in run_log["samples"] if s["status"] == "rejected_degraded")
    still_bad = len(run_log["samples"]) - ok
    print(f"\n[{phase_name}] after retry: {ok}/{len(run_log['samples'])} usable "
          f"({rejected} rejected as degraded, {still_bad - rejected} still failed) -> {out_dir}/")
    return 0 if ok == len(run_log["samples"]) else 1


def score_phase(phase_name):
    """Print mechanical metrics for every article already written under
    probe_out/<phase_name>/ -- word count, sentence-length stats, and the
    deterministic gate checks (buried-clause, argument-word-overuse, length
    distribution) already used in production, applied here read-only."""
    po = _import_orchestrator()
    out_dir = PROBE_OUT_DIR / phase_name
    if not out_dir.exists():
        print(f"No probe_out directory for phase '{phase_name}' -- run --run first.", file=sys.stderr)
        return 1

    for md_path in sorted(out_dir.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
        word_count = len(re.findall(r"\S+", body))
        scores = po.ProductionOrchestrator._readability_score(
            po.ProductionOrchestrator.__new__(po.ProductionOrchestrator), body
        )
        buried = po.ProductionOrchestrator._check_buried_clause_sentences(body)
        argument_hits = po.ProductionOrchestrator._check_argument_word_overuse(body)
        length_dist = po.ProductionOrchestrator._check_sentence_length_distribution(body)
        print(f"{md_path.stem}: words={word_count} fre={scores.get('fre') if scores else 'n/a'} "
              f"buried_clause={len(buried)} argument_word={len(argument_hits)} length_dist={len(length_dist)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--freeze-briefs", action="store_true", help="Make one real call per topic, freeze the Fable brief")
    parser.add_argument("--force", action="store_true", help="With --freeze-briefs: overwrite existing frozen briefs")
    parser.add_argument("--run", metavar="PHASE_NAME", help="Run the probe for this phase name (e.g. 'baseline')")
    parser.add_argument("--samples", type=int, default=3, help="Samples per topic (default 3)")
    parser.add_argument("--score", metavar="PHASE_NAME", help="Print mechanical metrics for an already-run phase")
    parser.add_argument("--preflight", action="store_true", help="Standalone: check model dependency paths, don't run anything")
    parser.add_argument("--retry-failed", metavar="PHASE_NAME", help="Re-run only the non-ok samples in an existing phase's metrics.json, in place")
    parser.add_argument("--topic", metavar="TOPIC_KEY", help="Restrict --run/--freeze-briefs to one topic (e.g. 'signage' for the Pixel Nova supplemental set) instead of the default 3-topic PROBE_TOPICS. Omit for the standard 3-topic behavior.")
    args = parser.parse_args()

    if args.freeze_briefs:
        sys.exit(freeze_briefs(force=args.force, topic_key=args.topic))
    elif args.preflight:
        sys.exit(0 if preflight() else 1)
    elif args.retry_failed:
        sys.exit(retry_failed(args.retry_failed))
    elif args.run:
        sys.exit(run_phase(args.run, n_samples=args.samples, topic_key=args.topic))
    elif args.score:
        sys.exit(score_phase(args.score))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
