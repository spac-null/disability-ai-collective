#!/usr/bin/env python3
"""
snapshot_test.py — regression harness for production_orchestrator.py's pre-commit
gate / post-publish review pipeline.

WHY THIS EXISTS: a planned module split (2026-08-09 design discussion — see this
repo's git log around this date) moves ~95 methods out of one 6,101-line class into
per-concern files. "The method body didn't change" is currently an eyeball claim on
a live, unattended, daily-publishing pipeline with zero test coverage. This tool
makes it a verified one, for the three risk classes that actually matter here:

  1. DETERMINISTIC CHECKS — _readability_score, _check_buried_clause_sentences,
     _check_argument_word_overuse, _check_sentence_length_distribution,
     _parse_rule_verdicts. Pure functions (none read self), real published articles
     as input, exact-value snapshots. One misplaced character during a move changes
     the fixture diff.

  2. LLM CALL CONSTRUCTION (gate.py/review.py) — _pre_commit_gate's GATE_SYSTEM
     prompt, validate_article's RULES_SYSTEM/CITATION_SYSTEM prompts, and their
     model/max_tokens/timeout. These are 100+ line string literals embedded in
     methods — exactly the kind of thing that drifted across 12 hand-copied
     locations before (see check_rule_drift.py). This harness NEVER calls the
     network: it monkeypatches _call_openai_compat_api, _web_verify_quote, and
     _web_verify_claim to safe recorders/stubs, so a byte-for-byte diff of what
     WOULD have been sent (not the LLM's non-deterministic response) survives any
     refactor. All file writes are redirected into a throwaway temp directory
     via _isolate_paths (orch.repo_root and every path config.py derives from it
     at __init__ time) — this never touches _posts/, _reviews/, _drafts/, or any
     other repo-tracked file. One exception, not worth engineering around: the
     logging.FileHandler production_orchestrator.py's __init__ binds to
     automation.log is set up before any override is possible, so running this
     harness does append a few log lines to that file — it's gitignored, not a
     real content file, and the alternative (patching logging setup itself) adds
     more risk than the append-only side effect it would avoid.

  3. LLM CALL CONSTRUCTION (generate.py's plan/writer prompts) — added 2026-08-09
     continuation, closing a gap flagged during the anchor-architecture blueprint
     audit (.claude/bregman-anchor-corpus.md Section 7, blocker #3): this harness
     previously covered gate.py/review.py only and never imported anything from
     generate.py, meaning Stage D (adding anchor/refrain fields to
     _fable_editorial_brief) would have been the first writer-prompt-adjacent
     change ever shipped with zero regression protection. _snapshot_generate_calls
     below covers _fable_editorial_brief's system/user prompt construction and
     call parameters the same way #2 covers gate/review — deliberately scoped to
     just this one function for now, not the full ~700-line
     _run_production_automation_locked (which depends on live discovery-DB state,
     random topic selection, and network image generation that would need much
     heavier mocking to snapshot safely; _fable_editorial_brief is the specific
     function future Stage D/E work will touch first).

USAGE:
    python3 automation/snapshot_test.py --record   # (re)generate fixtures. Run this
                                                     # once now, before any extraction,
                                                     # and again ONLY when you deliberately
                                                     # change what a rule/prompt should say.
    python3 automation/snapshot_test.py --check     # diff current behavior against
                                                     # recorded fixtures. Run after every
                                                     # mixin-extraction commit.

Exit code 0 = match (or fixtures written). Exit code 1 = drift detected, or no
fixtures recorded yet.
"""
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
AUTOMATION_DIR = Path(__file__).parent
FIXTURES_DIR = AUTOMATION_DIR / ".snapshot_fixtures"

# A small, deliberately diverse set of real published articles — different personas,
# lengths, and ages, so the deterministic checks exercise real variation rather than
# one narrow style. Update this list only if one of these files is deleted/renamed;
# adding more is fine and only strengthens coverage.
FIXTURE_ARTICLES = [
    "_posts/2026-08-07-one-in-twelve-and-no-surprises.md",
    "_posts/2026-07-31-injected-since-birth.md",
    "_posts/2026-07-26-vally-wieselthier-fired-her-kiln-while-josef-hoffmann.md",
    "_posts/2026-07-22-fourteen-nodes-on-nicholson-street.md",
    "_posts/2026-07-29-weegee-heard-the-body-first.md",
    "_posts/2026-08-07-a-stack-of-colours-has-not-made-a-single-sound-yet.md",
]

# Synthetic raw LLM-verdict text for _parse_rule_verdicts — this one isn't
# article-dependent, so real published text doesn't exercise its actual edge cases.
# "reversal_bug_case" reproduces the exact failure fixed 2026-08-02..06 (see the
# method's own docstring): a [FAIL] line followed by a [PASS] reversal for the same
# rule id must resolve to PASS, not count as a violation.
SYNTHETIC_VERDICT_RAWS = {
    "normal_mixed": (
        '[PASS] R1\n[FAIL] R2 — "some quoted phrase here"\n[N/A] R9\n'
        '[FAIL] R14 — "another one"'
    ),
    "reversal_bug_case": (
        "[FAIL] R3 — reasoning text, none found with certainty\n[PASS] R3"
    ),
    "all_pass": "\n".join(f"[PASS] R{i}" for i in range(1, 18)),
    "malformed_noise": (
        "some preamble text\n[FAIL]R5 no space before rule\n"
        "[FAIL] R6 — real one\nnot a verdict line at all"
    ),
}

# Synthetic inputs for _fable_editorial_brief (generate.py coverage, added
# 2026-08-09 continuation). Hand-written, not real news items — this is
# testing prompt CONSTRUCTION, not real editorial judgment.
# source_text (added Phase 1.6, .claude/phase-1.6-source-grounding.md):
# _fable_editorial_brief now takes an evidence_packet built from this text
# (see _snapshot_generate_calls), and _make_editorial_brief_fake's mocked
# correction_moment/resisting_example excerpts below are written as literal
# verbatim substrings of it, so the real validate_brief() call inside
# _fable_editorial_brief accepts them as status="found" rather than
# rejecting them for a source that doesn't exist -- exercising the
# validated-clean path, not just the rejection path.
FIXTURE_BRIEF_INPUTS = [
    {
        "news_title": "City council votes to remove three accessible parking bays downtown",
        "news_summary": "The bays are being replaced with a bike lane after a resident petition.",
        "disability_angle": "Wheelchair users say the replacement bays are 400m further from transit.",
        "source_text": (
            "City council votes to remove three accessible parking bays downtown\n\n"
            "The city council voted 6-3 on Tuesday to remove three accessible parking "
            "bays and replace them with a protected bike lane. 'This was a genuinely "
            "difficult trade-off,' said council transport lead Dana Ruiz. Wheelchair "
            "user Priya Nathan told the council the new route adds a 400-metre "
            "detour with no dropped kerb for two of the three blocks."
        ),
    },
    {
        "news_title": "New AI hiring-screening tool adopted by regional employer network",
        "news_summary": "The tool scores video interviews for 'engagement' and 'clarity of speech'.",
        "disability_angle": "",
        "source_text": (
            "New AI hiring-screening tool adopted by regional employer network\n\n"
            "A consortium of 40 regional employers has adopted an AI-driven video "
            "interview screening tool. 'We're not replacing human judgment, we're "
            "focusing it,' said HR director Owen Marsh. Autism self-advocate Lena "
            "Vogt said the scoring model penalizes atypical eye contact and pacing "
            "regardless of what a candidate actually says."
        ),
    },
]

# Synthetic prior posts written into the isolated tmpdir's _posts/ before each
# _snapshot_generate_calls run, so _get_recent_title_patterns/_get_recent_openings
# (both read self.posts_dir) exercise their real "here's what to avoid repeating"
# branch instead of the always-empty one a bare tmpdir would produce.
FIXTURE_RECENT_POSTS = [
    ("2026-08-05-a-ramp-is-not-a-favor.md",
     "A Ramp Is Not a Favor",
     "The building inspector signed off on the ramp without ever using it himself, "
     "and that gap between approval and use is where most access failures live."),
    ("2026-08-06-the-elevator-that-only-works-on-tuesdays.md",
     "The Elevator That Only Works on Tuesdays",
     "For three months the maintenance log listed the elevator as fully operational "
     "while the residents who depended on it took the stairs or stayed home."),
]

# Fixed non-empty persona state and fault-line data for _snapshot_generate_calls
# (added after a review flagged that an all-empty/neutral stub only exercises
# _fable_editorial_brief's "nothing to show" branches — exactly the ones NOT at
# risk from a Stage D/E edit. A real value here can go stale if agent names in
# config.py ever change; that's an acceptable, self-correcting cost — the
# fixture would then need obvious agent-name updates, not a silent bad snapshot).
FIXTURE_PERSONA_STATE = {
    "obsessions": ["how compliance paperwork substitutes for actual use-testing"],
    "unresolved_questions": [],
    "ongoing_arguments": ["a signed inspection is not evidence anything works"],
    "claims_on_record": [],
    "recent_mood": "wary",
    "last_updated": "2026-08-01",
}
FIXTURE_FAULT_LINE = {
    "personas": ["Maya Flux", "Zen Circuit"],
    "tension": "whether a compliant retrofit counts as access at all",
    "cross_cite": "a ramp that passes inspection but nobody who needs it can reach",
}


def _import_orchestrator():
    sys.path.insert(0, str(AUTOMATION_DIR))
    import production_orchestrator as po
    return po


def _patch_methods(cls, **replacements):
    """Monkeypatch multiple class attributes at once; returns a restore()
    callable. Restoring removes an attribute entirely if the class didn't
    define it directly before patching, rather than assigning back a value
    that only existed via inheritance from a mixin. Every name this harness
    patches (_call_openai_compat_api, _load_persona_state, etc.) is actually
    defined on a mixin (llm.py), not on ProductionOrchestrator itself — a
    naive setattr/setattr-back leaves a permanent same-function shadow on
    the subclass. Harmless today since it's the same function object either
    way, but it would silently win over any future MRO reorder that adds a
    real override on ProductionOrchestrator."""
    originals = {name: (name in cls.__dict__, cls.__dict__.get(name)) for name in replacements}
    for name, fn in replacements.items():
        setattr(cls, name, fn)

    def restore():
        for name, (had_own, old) in originals.items():
            if had_own:
                setattr(cls, name, old)
            else:
                delattr(cls, name)

    return restore


def _isolate_paths(orch, tmpdir):
    """Redirect every filesystem path production_orchestrator.py's __init__
    derives from self.repo_root — posts_dir, drafts_dir, assets_dir,
    discovery_db — into the throwaway tmpdir. All four are computed once at
    __init__ time (production_orchestrator.py:44-48), before orch.repo_root
    can be overridden, so setting repo_root alone does NOT isolate them —
    confirmed via a 2026-08-09 review after this harness's original
    orch.repo_root-only redirect turned out to leave self.posts_dir pointed
    at the real repo. Call this immediately after constructing orch and
    before calling anything that might read/write through these paths."""
    orch.repo_root = Path(tmpdir)
    orch.posts_dir = orch.repo_root / "_posts"
    orch.drafts_dir = orch.repo_root / "_drafts"
    orch.assets_dir = orch.repo_root / "assets"
    orch.discovery_db = orch.repo_root / "disability_findings.db"


def _load_fixture_texts():
    texts = {}
    for rel in FIXTURE_ARTICLES:
        path = REPO_ROOT / rel
        if not path.exists():
            print(f"WARNING: fixture article missing, skipping: {rel}", file=sys.stderr)
            continue
        texts[rel] = path.read_text(encoding="utf-8")
    return texts


def _snapshot_deterministic(po, fixture_texts):
    out = {}
    for name, content in fixture_texts.items():
        out[name] = {
            "readability_score": po.ProductionOrchestrator._readability_score(
                po.ProductionOrchestrator.__new__(po.ProductionOrchestrator), content
            ),
            "buried_clause_hits": po.ProductionOrchestrator._check_buried_clause_sentences(content),
            "argument_hits": po.ProductionOrchestrator._check_argument_word_overuse(content),
            "length_dist_hits": po.ProductionOrchestrator._check_sentence_length_distribution(content),
            "shadow_bullet_hits": po.ProductionOrchestrator._check_bullet_points_shadow(content),
            "shadow_word_hits": po.ProductionOrchestrator._check_forbidden_word_lists_shadow(content),
            "shadow_truncated_ending": po.ProductionOrchestrator._check_truncated_ending_shadow(content),
            "shadow_seam_hits": po.ProductionOrchestrator._check_seam_shadow(content),
        }
    out["_parse_rule_verdicts"] = {
        key: po.ProductionOrchestrator._parse_rule_verdicts(raw)
        for key, raw in SYNTHETIC_VERDICT_RAWS.items()
    }
    return out


def _make_recorder():
    calls = []

    def fake_call_openai_compat_api(self, url, api_key, system_prompt, user_prompt,
                                     model, max_tokens=3500, timeout=120, no_think=False,
                                     return_model=False, reasoning_max_tokens=None):
        calls.append({
            "system_prompt": system_prompt,
            # user_prompt added 2026-08-09 continuation (review finding): this
            # is where the rendered R1..Rn rule checklist (style_rules.py)
            # actually lives — the exact drift class check_rule_drift.py
            # exists for was previously unprotected here.
            "user_prompt": user_prompt,
            "model": model,
            "max_tokens": max_tokens,
            "timeout": timeout,
        })
        # Safe dummy response: enough [PASS] Rn lines to satisfy any parser up through
        # R30 (current max in use is R17), plus CLEAN for citation-style checks, so
        # every calling method proceeds down its "nothing wrong" path instead of
        # crashing on the absence of a real network response.
        text = "CLEAN\n" + "\n".join(f"[PASS] R{i}" for i in range(1, 30))
        return (text, model) if return_model else text

    return calls, fake_call_openai_compat_api


def _fake_web_verify_quote(self, person, quote):
    return ("UNVERIFIABLE", "stubbed by snapshot_test.py — no live web calls in this harness")


def _fake_web_verify_claim(self, claim_type, subject, claim_text):
    return ("UNVERIFIABLE", "stubbed by snapshot_test.py — no live web calls in this harness")


def _evidence_field_fixture(editorial_need, source_excerpt, named_person="",
                             direct_quote="", dates_numbers=None, interpretation=""):
    """Phase 1.6 (.claude/phase-1.6-source-grounding.md): the structured
    evidence-candidate shape validate_brief() (grounding.py) expects, not the
    old flat string. named_person/direct_quote/dates_numbers here must each
    be an actual verbatim substring of source_excerpt, and source_excerpt
    itself must be a verbatim substring of whatever source_text the caller's
    evidence_packet was built from -- see FIXTURE_BRIEF_INPUTS's source_text
    fields, which these fixture excerpts are hand-matched against."""
    return {
        "editorial_need": editorial_need,
        "evidence_candidate": {
            "status": "found",
            "source_excerpt": source_excerpt,
            "named_person": named_person,
            "direct_quote": direct_quote,
            "dates_numbers": dates_numbers or [],
        },
        "interpretation": interpretation,
    }


def _make_editorial_brief_fake(persona_name, register_name, correction_moment, resisting_example):
    """Unlike _make_recorder's generic '[PASS] Rn' stub (fine for gate/review,
    which only checks call construction), _fable_editorial_brief parses its
    response as JSON and validates persona/register against real config — a
    non-JSON stub would make every fixture call return None, hiding whether
    parsing/validation logic itself drifts. Returns a real, schema-valid
    brief using a persona/register pulled from the live orchestrator/config
    at record time, not hand-typed names that could go stale if personas are
    renamed.

    correction_moment/resisting_example (Phase 1.6): pre-built structured
    evidence-candidate dicts (see _evidence_field_fixture) rather than flat
    strings, so the mocked LLM response matches the schema
    _fable_editorial_brief's real validate_brief() call now expects — a flat
    string here would be rejected as a schema-shape violation before this
    fixture ever reaches the interesting parts of the pipeline."""
    calls = []

    def fake(self, url, api_key, system_prompt, user_prompt, model,
              max_tokens=3500, timeout=120, no_think=False,
              return_model=False, reasoning_max_tokens=None,
              check_truncation=False, temperature=None):
        # check_truncation/temperature (fixed alongside the Phase 1.6 schema
        # update): this fake's signature had drifted behind
        # _call_openai_compat_api's real one (llm.py) -- _call_editorial_model
        # calls it with check_truncation=True, which every prior version of
        # this fake rejected with a bare TypeError on argument binding
        # (before the function body, and therefore before `calls.append`,
        # ever ran). That silently made this whole fixture inert: brief was
        # always None and calls was always [] for BOTH personas, in the
        # committed pre-Phase-1.6 fixture too -- confirmed by diffing against
        # git HEAD's automation/.snapshot_fixtures/generate_calls.json before
        # this fix. Not a Phase 1.6 regression, but fixing it here is what
        # makes this fixture capable of catching prompt-construction drift
        # at all, which is the whole point of recording it.
        calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "model": model,
            "max_tokens": max_tokens,
            "timeout": timeout,
        })
        payload = json.dumps({
            "persona": persona_name,
            "angle": "Is the replacement bay closer or further for most riders who actually use it?",
            "register": register_name,
            "seed_sentence": "The new accessible bay is four hundred metres from the tram stop.",
            "opening_scene": "The new accessible bay is four hundred metres from the tram stop.",
            "opening_shape": "fact",
            "correction_moment": correction_moment,
            "resisting_example": resisting_example,
            "cross_cite": "",
        })
        return (payload, model) if return_model else payload

    return calls, fake


def _snapshot_generate_calls(po):
    """Covers _fable_editorial_brief (llm.py) — see the module docstring's
    item 3. Two things would otherwise make this fixture non-deterministic
    or hollow, both fixed here:

    Determinism: persona obsessions/mood (_load_persona_state) and fault-line
    detection (_active_fault_lines) both read from live files anchored to the
    script's own directory (PERSONA_STATE_DIR / _RELATIONSHIPS_FILE in
    config.py), NOT self.repo_root, so _isolate_paths below cannot isolate
    them — patched to fixed values instead, the same way
    _call_openai_compat_api is patched rather than left live.

    Coverage (fixed after a 2026-08-09 review found the original version of
    this function used all-EMPTY/neutral stubs — which made every
    conditional block in _fable_editorial_brief's prompt (state_block,
    fault_block, openings_block) render as "" and go completely
    unprotected, i.e. exactly the dynamic assembly code Stage D/E work is
    most likely to touch): FIXTURE_PERSONA_STATE and FIXTURE_FAULT_LINE are
    real non-empty values, and FIXTURE_RECENT_POSTS gets written into the
    isolated tmpdir's _posts/ before the call, so _get_recent_openings sees
    real prior posts instead of an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = po.ProductionOrchestrator()
        _isolate_paths(orch, tmpdir)
        orch.posts_dir.mkdir(parents=True, exist_ok=True)
        for filename, title, body_line in FIXTURE_RECENT_POSTS:
            (orch.posts_dir / filename).write_text(
                f"---\ntitle: {title}\n---\n\n{body_line}\n", encoding="utf-8"
            )

        from orchestrator.config import _REGISTERS  # AUTOMATION_DIR already on
        # sys.path via _import_orchestrator(); local import keeps this lazy so
        # module load order never depends on record()/check() having run first.
        from orchestrator.grounding import build_evidence_packet
        persona_name = sorted(orch.agents.keys())[0]
        register_name = sorted(r[0] for r in _REGISTERS)[0]

        # Phase 1.6: one evidence-candidate excerpt fixture per FIXTURE_BRIEF_INPUTS
        # entry, hand-matched to that entry's source_text -- see
        # _evidence_field_fixture's docstring for why these must be verbatim
        # substrings, not paraphrases.
        _EVIDENCE_FIXTURES = [
            (
                _evidence_field_fixture(
                    "A concrete moment where the council's own account complicates the persona's framing.",
                    "Wheelchair user Priya Nathan told the council the new route adds a "
                    "400-metre detour with no dropped kerb for two of the three blocks.",
                    named_person="Priya Nathan", dates_numbers=["400"],
                    interpretation="The distance gap is the material fact; the persona's argument turns on it.",
                ),
                _evidence_field_fixture(
                    "A real position, from inside the same access-advocacy value system, that resists the piece's argument.",
                    "'This was a genuinely difficult trade-off,' said council transport lead Dana Ruiz.",
                    named_person="Dana Ruiz", direct_quote="This was a genuinely difficult trade-off",
                    interpretation="Ruiz frames this as a hard trade-off between two accessible-transport goods, not neglect.",
                ),
            ),
            (
                _evidence_field_fixture(
                    "A specific, sourced claim about what the scoring model actually penalizes.",
                    "Autism self-advocate Lena Vogt said the scoring model penalizes atypical "
                    "eye contact and pacing regardless of what a candidate actually says.",
                    named_person="Lena Vogt",
                    interpretation="This is the mechanism, not just the outcome -- worth naming directly.",
                ),
                _evidence_field_fixture(
                    "The vendor/employer's own stated framing, which resists the piece's argument from inside the hiring-reform value system.",
                    "'We're not replacing human judgment, we're focusing it,' said HR director Owen Marsh.",
                    named_person="Owen Marsh", direct_quote="We're not replacing human judgment, we're focusing it",
                    interpretation="Marsh's framing assumes the tool only filters volume, not that the filter itself discriminates.",
                ),
            ),
        ]

        out = {}
        for i, brief_input in enumerate(FIXTURE_BRIEF_INPUTS):
            correction_fixture, resisting_fixture = _EVIDENCE_FIXTURES[i]
            calls, fake_call = _make_editorial_brief_fake(
                persona_name, register_name, correction_fixture, resisting_fixture,
            )
            restore = _patch_methods(
                po.ProductionOrchestrator,
                _call_openai_compat_api=fake_call,
                _load_persona_state=lambda self, agent_name: dict(FIXTURE_PERSONA_STATE),
                _active_fault_lines=lambda self, text: [dict(FIXTURE_FAULT_LINE)],
            )
            evidence_packet = build_evidence_packet(brief_input["source_text"])
            try:
                brief = orch._fable_editorial_brief(
                    brief_input["news_title"], brief_input["news_summary"],
                    brief_input["disability_angle"], persona_name, evidence_packet,
                )
                error = None
            except Exception as e:
                brief, error = None, f"{type(e).__name__}: {e}"
            finally:
                restore()
            out[f"brief_{i}"] = {
                "calls": [dict(c) for c in calls],
                "brief": brief,
                "error": error,
            }

    return out


def _snapshot_llm_calls(po, fixture_texts):
    calls, fake_call = _make_recorder()
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=fake_call,
        _web_verify_quote=_fake_web_verify_quote,
        _web_verify_claim=_fake_web_verify_claim,
    )

    out = {}
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            orch = po.ProductionOrchestrator()
            # Redirect ALL file writes (review files, article-file patches) into a
            # throwaway directory — see _isolate_paths's docstring for why
            # orch.repo_root alone is not enough (posts_dir/drafts_dir/assets_dir/
            # discovery_db are all cached before an override could take effect).
            _isolate_paths(orch, tmpdir)
            (orch.repo_root / "_reviews").mkdir(exist_ok=True)

            for name, content in fixture_texts.items():
                tmp_article = Path(tmpdir) / (Path(name).stem + ".md")
                tmp_article.write_text(content, encoding="utf-8")

                calls.clear()
                try:
                    gate_content, gate_changed = orch._pre_commit_gate(
                        content, tmp_article, article_type=None
                    )
                    gate_error = None
                except Exception as e:
                    gate_content, gate_changed, gate_error = None, None, f"{type(e).__name__}: {e}"
                gate_calls = [dict(c) for c in calls]

                calls.clear()
                try:
                    review_file, is_clean = orch.validate_article(
                        content, tmp_article, slug="snapshot-test"
                    )
                    review_error = None
                except Exception as e:
                    is_clean, review_error = None, f"{type(e).__name__}: {e}"
                review_calls = [dict(c) for c in calls]

                out[name] = {
                    "gate_calls": gate_calls,
                    "gate_changed": gate_changed,
                    "gate_error": gate_error,
                    "review_calls": review_calls,
                    "review_is_clean": is_clean,
                    "review_error": review_error,
                }
    finally:
        restore()

    return out


def _fixture_path(name):
    return FIXTURES_DIR / f"{name}.json"


def record():
    po = _import_orchestrator()
    fixture_texts = _load_fixture_texts()
    if not fixture_texts:
        print("ERROR: no fixture articles could be loaded — nothing to record.", file=sys.stderr)
        return 1
    FIXTURES_DIR.mkdir(exist_ok=True)

    deterministic = _snapshot_deterministic(po, fixture_texts)
    _fixture_path("deterministic").write_text(json.dumps(deterministic, indent=2, sort_keys=True))

    llm_calls = _snapshot_llm_calls(po, fixture_texts)
    _fixture_path("llm_calls").write_text(json.dumps(llm_calls, indent=2, sort_keys=True))

    generate_calls = _snapshot_generate_calls(po)
    _fixture_path("generate_calls").write_text(json.dumps(generate_calls, indent=2, sort_keys=True))

    print(f"Recorded fixtures for {len(fixture_texts)} article(s) to {FIXTURES_DIR}/")
    return 0


_FIXTURE_NAMES = ("deterministic", "llm_calls", "generate_calls")


def check():
    # Check every required fixture individually, not just "at least one .json
    # exists" — a partially-recorded fixtures dir (e.g. a checkout missing a
    # fixture added by a commit it doesn't have yet) previously crashed with
    # a raw FileNotFoundError instead of this message.
    missing = [n for n in _FIXTURE_NAMES if not _fixture_path(n).exists()]
    if missing:
        print(
            f"ERROR: fixture(s) not recorded yet: {', '.join(missing)}. "
            "Run with --record first.", file=sys.stderr,
        )
        return 1

    po = _import_orchestrator()
    fixture_texts = _load_fixture_texts()
    problems = []

    deterministic_expected = json.loads(_fixture_path("deterministic").read_text())
    deterministic_actual = _snapshot_deterministic(po, fixture_texts)
    if deterministic_actual != deterministic_expected:
        for key in set(deterministic_expected) | set(deterministic_actual):
            if deterministic_expected.get(key) != deterministic_actual.get(key):
                problems.append(f"[DRIFT] deterministic checks changed for: {key}")

    llm_expected = json.loads(_fixture_path("llm_calls").read_text())
    llm_actual = _snapshot_llm_calls(po, fixture_texts)
    if llm_actual != llm_expected:
        for key in set(llm_expected) | set(llm_actual):
            if llm_expected.get(key) != llm_actual.get(key):
                problems.append(f"[DRIFT] gate/review LLM-call construction changed for: {key}")

    generate_expected = json.loads(_fixture_path("generate_calls").read_text())
    generate_actual = _snapshot_generate_calls(po)
    if generate_actual != generate_expected:
        for key in set(generate_expected) | set(generate_actual):
            if generate_expected.get(key) != generate_actual.get(key):
                problems.append(f"[DRIFT] generate.py (_fable_editorial_brief) LLM-call construction changed for: {key}")

    if problems:
        print("Snapshot drift detected:\n")
        for p in problems:
            print(p)
        print(
            "\nRe-run with a diff tool against automation/.snapshot_fixtures/*.json to see "
            "exactly what changed. If the change was deliberate (a real rule-text or logic "
            "fix, not a refactor accident), re-run --record to update the baseline."
        )
        return 1

    print(f"No drift — {len(fixture_texts)} article(s) match recorded fixtures.")
    return 0


if __name__ == "__main__":
    if "--record" in sys.argv:
        sys.exit(record())
    elif "--check" in sys.argv:
        sys.exit(check())
    else:
        print(__doc__)
        sys.exit(1)
